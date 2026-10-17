"""
src/agents/vision_team.py — Vision Specialist Team (DERMA-GUARD v4.0)

Runs 4 model families in parallel:
  1. DermLIP-PanDerm (VLM, HuggingFace)
  2. PanDerm Encoder (Foundation Vision, HuggingFace)
  3. Swin-Tiny ×2 (clinical + dermoscopy, separate weights, timm)
  4. ResNet152 (timm)

Also computes per-image quality scores via OpenCV.
"""
from __future__ import annotations

import concurrent.futures
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image


# ---------------------------------------------------------------------------
# Per-image quality scorer (MLP trained jointly)
# ---------------------------------------------------------------------------

class ImageQualityMLP(nn.Module):
    """Predicts a quality score in [0,1] from 5 hand-crafted image stats.

    Inputs:
        blur_score         – variance of Laplacian (higher = sharper)
        brightness         – mean pixel value (0-1 range)
        contrast           – std of pixel values
        resolution_ratio   – actual_resolution / expected_resolution
        occlusion_score    – fraction of pixels below saliency threshold
    """

    def __init__(self, input_dim: int = 5, hidden_dim: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, 5) → (B, 1) quality score in [0,1]."""
        return self.net(x)


def compute_image_stats(img_bgr: np.ndarray, expected_size: int = 224) -> Dict[str, float]:
    """Compute 5 image quality statistics from a BGR numpy image.

    Args:
        img_bgr: OpenCV BGR image (uint8)
        expected_size: expected shorter side in pixels

    Returns:
        dict with keys: blur_score, brightness, contrast, resolution_ratio, occlusion_score
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # 1. Blur score — variance of Laplacian
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    blur_score = float(lap.var())
    # Normalise: typical good images > 100, very blurry < 5
    blur_score_norm = min(1.0, blur_score / 200.0)

    # 2. Brightness — mean pixel value [0,1]
    brightness = float(gray.mean()) / 255.0

    # 3. Contrast — std of pixel values [0,1]
    contrast = float(gray.std()) / 128.0

    # 4. Resolution ratio
    actual_shorter = min(h, w)
    resolution_ratio = min(1.0, actual_shorter / expected_size)

    # 5. Occlusion — fraction of pixels below saliency threshold
    # Simple proxy: fraction of very dark pixels (< 10)
    dark_fraction = float(np.sum(gray < 10)) / (h * w)
    occlusion_score = dark_fraction  # lower is better; we want 1 - this

    return {
        "blur_score": blur_score_norm,
        "brightness": brightness,
        "contrast": contrast,
        "resolution_ratio": resolution_ratio,
        "occlusion_score": 1.0 - occlusion_score,  # invert: 1 = no occlusion
    }


def pil_to_bgr(pil_img: Image.Image) -> np.ndarray:
    """Convert PIL image to OpenCV BGR numpy array."""
    rgb = np.array(pil_img.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


# ---------------------------------------------------------------------------
# Individual model wrappers
# ---------------------------------------------------------------------------

class DermLIPPanDermModel(nn.Module):
    """DermLIP-PanDerm VLM wrapper.

    Loads from HuggingFace hub: redlessone/DermLIP_PanDerm-base-w-PubMed-256
    Provides zero-shot classification and 768-d embeddings.
    Falls back gracefully if the model is not available.
    """

    HF_REPO = "redlessone/DermLIP_PanDerm-base-w-PubMed-256"
    ZERO_SHOT_TEMPLATE = "This is a skin image of {class_name}"

    def __init__(self, num_classes: int = 7, device: torch.device | str = "cpu"):
        super().__init__()
        self.num_classes = num_classes
        self.device_str = str(device)
        self._model = None
        self._processor = None
        self._available = False

    def load(self, class_names: List[str]) -> bool:
        """Attempt to load from HuggingFace hub."""
        try:
            from transformers import CLIPModel, CLIPProcessor
            self._model = CLIPModel.from_pretrained(self.HF_REPO)
            self._processor = CLIPProcessor.from_pretrained(self.HF_REPO)
            self._class_names = class_names
            self._text_inputs_cache = None
            self._available = True
            print(f"[VisionTeam] DermLIP-PanDerm loaded from {self.HF_REPO}")
            return True
        except Exception as e:
            warnings.warn(
                f"[VisionTeam] DermLIP-PanDerm unavailable: {e}\n"
                "  Tip: run `huggingface-cli login` and accept the model license."
            )
            self._available = False
            return False

    @torch.no_grad()
    def forward(
        self,
        clinical_images: Optional[List[Image.Image]] = None,
        dermo_images: Optional[List[Image.Image]] = None,
    ) -> Dict:
        if not self._available or self._model is None:
            # Return zero tensors so pipeline can continue
            B = len(clinical_images or dermo_images or [1])
            return {
                "logits": torch.zeros(B, self.num_classes),
                "embedding": torch.zeros(B, 768),
                "quality_score": torch.zeros(B),
                "available": False,
            }

        images = clinical_images if clinical_images else dermo_images
        if not images:
            return {
                "logits": torch.zeros(1, self.num_classes),
                "embedding": torch.zeros(1, 768),
                "quality_score": torch.zeros(1),
                "available": False,
            }

        # Build text prompts
        texts = [self.ZERO_SHOT_TEMPLATE.format(class_name=cn) for cn in self._class_names]
        inputs = self._processor(text=texts, images=images, return_tensors="pt", padding=True)

        outputs = self._model(**inputs)
        logits = outputs.logits_per_image  # (B, num_classes)
        # Image embedding from vision model
        image_embeds = outputs.image_embeds  # (B, 768) — already normalized in CLIP
        quality = torch.ones(len(images))  # DermLIP manages its own quality internally

        return {
            "logits": logits,
            "embedding": image_embeds,
            "quality_score": quality,
            "available": True,
        }


class PanDermModel(nn.Module):
    """PanDerm Foundation Vision Encoder.

    Attempts to load from HuggingFace (SiyuanYan1/PanDerm).
    Falls back to a Swin-Base proxy if unavailable.
    Freezes early layers, fine-tunes last 2 stages.
    """

    HF_REPO = "SiyuanYan1/PanDerm"

    def __init__(self, num_classes: int = 7):
        super().__init__()
        self.num_classes = num_classes
        self._backbone: Optional[nn.Module] = None
        self._head: Optional[nn.Module] = None
        self._available = False
        self.embed_dim = 768

    def load(self) -> bool:
        """Load PanDerm encoder."""
        try:
            from transformers import AutoModel
            backbone = AutoModel.from_pretrained(self.HF_REPO, trust_remote_code=True)
            self._backbone = backbone
            # Freeze early layers (all but last 2 stages)
            self._freeze_early_layers()
            # Classification head
            self._head = nn.Linear(self.embed_dim, self.num_classes)
            self._available = True
            print(f"[VisionTeam] PanDerm loaded from {self.HF_REPO}")
            return True
        except Exception as e:
            warnings.warn(
                f"[VisionTeam] PanDerm unavailable ({e}). Using Swin-Base proxy."
            )
            self._load_proxy()
            return False

    def _load_proxy(self):
        """Use Swin-Base as a proxy encoder when PanDerm is unavailable."""
        try:
            import timm
            self._backbone = timm.create_model(
                "swin_base_patch4_window7_224", pretrained=True, num_classes=0
            )
            self.embed_dim = self._backbone.num_features
            self._head = nn.Linear(self.embed_dim, self.num_classes)
            self._available = True
            print("[VisionTeam] PanDerm proxy: using swin_base_patch4_window7_224")
        except Exception as e2:
            warnings.warn(f"[VisionTeam] PanDerm proxy also failed: {e2}")
            self._available = False

    def _freeze_early_layers(self):
        """Freeze backbone stages except the last 2."""
        if self._backbone is None:
            return
        params = list(self._backbone.parameters())
        # Freeze first 80% of parameters
        n_freeze = int(len(params) * 0.8)
        for i, p in enumerate(params):
            p.requires_grad = i >= n_freeze

    def forward(self, images: torch.Tensor) -> Dict:
        if not self._available or self._backbone is None:
            B = images.shape[0]
            return {
                "features": torch.zeros(B, 768),
                "logits": torch.zeros(B, self.num_classes),
                "available": False,
            }
        feats = self._backbone(images)  # (B, embed_dim)
        if feats.dim() > 2:
            feats = feats.mean(dim=[2, 3]) if feats.dim() == 4 else feats.mean(dim=1)
        logits = self._head(feats)
        return {"features": feats, "logits": logits, "available": True}


class SwinTinyModel(nn.Module):
    """Swin-Tiny backbone (timm).

    num_classes=0 → 768-d pre-head embedding (as specified).
    Two separate instances: clinical and dermoscopy (NOT shared weights).
    Training protocol: freeze 5 epochs → fine-tune last 2 stages at 0.1× LR.
    """

    def __init__(self, num_classes: int = 7, instance_name: str = "clinical"):
        super().__init__()
        self.num_classes = num_classes
        self.instance_name = instance_name  # "clinical" or "dermoscopy"
        self.embed_dim = 768
        self._load_backbone()

    def _load_backbone(self):
        import timm
        # num_classes=0 returns pre-head 768-d embedding
        self.backbone = timm.create_model(
            "swin_tiny_patch4_window7_224",
            pretrained=True,
            num_classes=0,  # CRITICAL: pre-head embeddings
        )
        self.head = nn.Sequential(
            nn.Linear(self.embed_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, self.num_classes),
        )

    def freeze_backbone(self):
        """Freeze backbone (call for first 5 epochs)."""
        for p in self.backbone.parameters():
            p.requires_grad = False

    def unfreeze_last_stages(self, n_stages: int = 2):
        """Unfreeze last n stages for fine-tuning at reduced LR."""
        # Swin-Tiny has 4 stages in backbone.layers
        total_stages = len(self.backbone.layers)
        for i, stage in enumerate(self.backbone.layers):
            for p in stage.parameters():
                p.requires_grad = i >= (total_stages - n_stages)
        # Always keep head trainable
        for p in self.head.parameters():
            p.requires_grad = True

    def forward(self, images: torch.Tensor) -> Dict:
        """
        Args:
            images: (B, 3, 224, 224)
        Returns:
            dict with 'embedding' (B, 768) and 'logits' (B, num_classes)
        """
        embedding = self.backbone(images)  # (B, 768) — num_classes=0 mode
        logits = self.head(embedding)
        return {"embedding": embedding, "logits": logits}


class ResNet152Model(nn.Module):
    """ResNet152 CNN backbone (timm).

    Provides 2048-d embedding and fine-tuned logits.
    Fine-tuning protocol: same as Swin-Tiny (freeze → partial unfreeze).
    """

    def __init__(self, num_classes: int = 7):
        super().__init__()
        self.num_classes = num_classes
        self.embed_dim = 2048
        import timm
        self.backbone = timm.create_model(
            "resnet152.a2_in1k", pretrained=True, num_classes=0
        )
        self.head = nn.Sequential(
            nn.Linear(self.embed_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, num_classes),
        )

    def freeze_backbone(self):
        for p in self.backbone.parameters():
            p.requires_grad = False

    def unfreeze_last_stages(self, n_stages: int = 2):
        """Unfreeze the last n layer groups of ResNet152."""
        layer_groups = [self.backbone.layer1, self.backbone.layer2,
                        self.backbone.layer3, self.backbone.layer4]
        n_total = len(layer_groups)
        for i, lg in enumerate(layer_groups):
            for p in lg.parameters():
                p.requires_grad = i >= (n_total - n_stages)
        for p in self.head.parameters():
            p.requires_grad = True

    def forward(self, images: torch.Tensor) -> Dict:
        embedding = self.backbone(images)  # (B, 2048)
        logits = self.head(embedding)
        return {"embedding": embedding, "logits": logits}


# ---------------------------------------------------------------------------
# VisionSpecialistTeam
# ---------------------------------------------------------------------------

@dataclass
class VisionReport:
    """Output from VisionSpecialistTeam.process_case()."""
    model_predictions: Dict[str, torch.Tensor]  # name → logits [K]
    model_embeddings: Dict[str, torch.Tensor]   # name → embedding
    model_confidences: Dict[str, float]          # name → max(softmax)
    uncertainty_estimates: Dict[str, float]      # name → predictive entropy
    quality_scores: Dict[str, float]             # name → per-image quality


class VisionSpecialistTeam(nn.Module):
    """Runs 4 model families in parallel and returns a VisionReport.

    Models (run in parallel via ThreadPoolExecutor):
        - DermLIP-PanDerm (VLM)
        - PanDerm Encoder (Foundation)
        - Swin-Tiny (clinical image)
        - Swin-Tiny (dermoscopy image)
        - ResNet152

    Also computes per-image quality scores using OpenCV.
    """

    def __init__(
        self,
        num_classes: int = 7,
        class_names: Optional[List[str]] = None,
        device: Optional[torch.device] = None,
        load_weights_dir: Optional[Path] = None,
    ):
        super().__init__()
        self.num_classes = num_classes
        self.class_names = class_names or [str(i) for i in range(num_classes)]
        self.device = device or (torch.device("cuda") if torch.cuda.is_available()
                                  else torch.device("cpu"))

        # Quality MLP (trained jointly — loaded if checkpoint exists)
        self.quality_mlp = ImageQualityMLP(input_dim=5)

        # Model instances
        self.dermlip = DermLIPPanDermModel(num_classes=num_classes, device=self.device)
        self.panderm = PanDermModel(num_classes=num_classes)
        self.swin_clinical = SwinTinyModel(num_classes=num_classes, instance_name="clinical")
        self.swin_dermo = SwinTinyModel(num_classes=num_classes, instance_name="dermoscopy")
        self.resnet = ResNet152Model(num_classes=num_classes)

        self._loaded = False

    def load(self) -> "VisionSpecialistTeam":
        """Load all model weights. Call once before inference."""
        self.dermlip.load(self.class_names)
        self.panderm.load()
        # Swin-Tiny and ResNet152 are loaded via timm (pretrained=True in __init__)
        self._loaded = True
        self.to(self.device)
        return self

    # ------------------------------------------------------------------
    # Quality scoring helpers
    # ------------------------------------------------------------------

    def _score_image_quality(self, image_tensor: torch.Tensor) -> float:
        """Compute quality score for a single image tensor (C,H,W) in [0,1]."""
        # Convert tensor to numpy uint8 for OpenCV
        np_img = (image_tensor.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
        bgr = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
        stats = compute_image_stats(bgr, expected_size=224)
        feat = torch.tensor([
            stats["blur_score"],
            stats["brightness"],
            stats["contrast"],
            stats["resolution_ratio"],
            stats["occlusion_score"],
        ], dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            score = self.quality_mlp(feat).item()
        return score

    def _predictive_entropy(self, logits: torch.Tensor) -> float:
        """Compute predictive entropy H[p] from logits."""
        probs = F.softmax(logits, dim=-1)
        log_probs = F.log_softmax(logits, dim=-1)
        entropy = -(probs * log_probs).sum(dim=-1).mean().item()
        return float(entropy)

    # ------------------------------------------------------------------
    # Per-model inference wrappers (run in parallel)
    # ------------------------------------------------------------------

    def _run_dermlip(
        self,
        clinical_pil: Optional[List[Image.Image]],
        dermo_pil: Optional[List[Image.Image]],
    ) -> Dict:
        with torch.no_grad():
            return self.dermlip(clinical_images=clinical_pil, dermo_images=dermo_pil)

    def _run_panderm(self, images: torch.Tensor) -> Dict:
        with torch.no_grad():
            return self.panderm(images.to(self.device))

    def _run_swin_clinical(self, images: torch.Tensor) -> Dict:
        with torch.no_grad():
            return self.swin_clinical(images.to(self.device))

    def _run_swin_dermo(self, images: torch.Tensor) -> Dict:
        with torch.no_grad():
            return self.swin_dermo(images.to(self.device))

    def _run_resnet(self, images: torch.Tensor) -> Dict:
        with torch.no_grad():
            return self.resnet(images.to(self.device))

    # ------------------------------------------------------------------
    # Main API
    # ------------------------------------------------------------------

    def process_case(
        self,
        clinical_images: Optional[torch.Tensor] = None,
        dermo_images: Optional[torch.Tensor] = None,
        clinical_pil: Optional[List[Image.Image]] = None,
        dermo_pil: Optional[List[Image.Image]] = None,
    ) -> VisionReport:
        """Run all vision models in parallel and return a VisionReport.

        Args:
            clinical_images:  (B, 3, 224, 224) tensor of clinical images
            dermo_images:     (B, 3, 224, 224) tensor of dermoscopy images
            clinical_pil:     list of PIL Images (for DermLIP CLIP processor)
            dermo_pil:        list of PIL Images (for DermLIP CLIP processor)

        Returns:
            VisionReport with per-model predictions, embeddings, confidences,
            uncertainties, and quality scores.
        """
        if not self._loaded:
            raise RuntimeError("Call VisionSpecialistTeam.load() before process_case()")

        B = (clinical_images.shape[0] if clinical_images is not None
             else (dermo_images.shape[0] if dermo_images is not None else 1))

        # Placeholder tensors for missing modalities
        zero_clinical = torch.zeros(B, 3, 224, 224, device=self.device)
        zero_dermo = torch.zeros(B, 3, 224, 224, device=self.device)
        clin = clinical_images.to(self.device) if clinical_images is not None else zero_clinical
        derm = dermo_images.to(self.device) if dermo_images is not None else zero_dermo

        # Run all models in parallel (IO-bound + model forward)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            f_dermlip = executor.submit(self._run_dermlip, clinical_pil, dermo_pil)
            f_panderm = executor.submit(self._run_panderm, clin)
            f_swin_c = executor.submit(self._run_swin_clinical, clin)
            f_swin_d = executor.submit(self._run_swin_dermo, derm)
            f_resnet = executor.submit(self._run_resnet, clin)

            res_dermlip = f_dermlip.result()
            res_panderm = f_panderm.result()
            res_swin_c = f_swin_c.result()
            res_swin_d = f_swin_d.result()
            res_resnet = f_resnet.result()

        # Collect predictions
        model_predictions = {
            "dermlip_panderm": res_dermlip["logits"].cpu(),
            "panderm": res_panderm["logits"].cpu(),
            "swin_tiny_clinical": res_swin_c["logits"].cpu(),
            "swin_tiny_dermoscopy": res_swin_d["logits"].cpu(),
            "resnet152": res_resnet["logits"].cpu(),
        }

        # Collect embeddings
        model_embeddings = {
            "dermlip_panderm": res_dermlip["embedding"].cpu(),
            "panderm": res_panderm["features"].cpu(),
            "swin_tiny_clinical": res_swin_c["embedding"].cpu(),
            "swin_tiny_dermoscopy": res_swin_d["embedding"].cpu(),
            "resnet152": res_resnet["embedding"].cpu(),
        }

        # Compute confidences (max softmax probability)
        model_confidences = {
            name: float(F.softmax(logits, dim=-1).max(dim=-1).values.mean().item())
            for name, logits in model_predictions.items()
        }

        # Compute uncertainty (predictive entropy)
        uncertainty_estimates = {
            name: self._predictive_entropy(logits)
            for name, logits in model_predictions.items()
        }

        # Per-image quality scores
        quality_scores: Dict[str, float] = {}
        if clinical_images is not None:
            quality_scores["clinical"] = float(np.mean([
                self._score_image_quality(clinical_images[i])
                for i in range(B)
            ]))
        if dermo_images is not None:
            quality_scores["dermoscopy"] = float(np.mean([
                self._score_image_quality(dermo_images[i])
                for i in range(B)
            ]))

        return VisionReport(
            model_predictions=model_predictions,
            model_embeddings=model_embeddings,
            model_confidences=model_confidences,
            uncertainty_estimates=uncertainty_estimates,
            quality_scores=quality_scores,
        )

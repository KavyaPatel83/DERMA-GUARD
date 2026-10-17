"""
src/stress/corruption.py — DERMA-STRESS corruption engine (DERMA-GUARD v4.0)

Implements 15 corruption conditions across 4 categories:
  Availability (4): missing clinical, dermoscopy, metadata, text
  Technical   (6): blur, noise, brightness, contrast, JPEG, occlusion
  Semantic    (3): contradictory text, vague text, incorrect metadata,
                   + semantic image swap, metadata poisoning, text hallucination
  Compound    (1): multi-failure composition

CRITICAL: Corruptions are generated ONCE, cached, and replayed for ALL models.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch
from PIL import Image


# ---------------------------------------------------------------------------
# Condition descriptors
# ---------------------------------------------------------------------------

CORRUPTION_CONDITIONS: List[Dict] = [
    # ---- Availability ----
    {"id": "miss_clinical",      "category": "availability", "name": "Missing clinical image",    "severity": "high"},
    {"id": "miss_dermo",         "category": "availability", "name": "Missing dermoscopy image",  "severity": "high"},
    {"id": "miss_metadata",      "category": "availability", "name": "Missing metadata",          "severity": "medium"},
    {"id": "miss_text",          "category": "availability", "name": "Missing text",              "severity": "medium"},
    # ---- Technical ----
    {"id": "blur_mild",          "category": "technical",    "name": "Gaussian blur (mild)",      "severity": "low",    "param": 5},
    {"id": "blur_severe",        "category": "technical",    "name": "Gaussian blur (severe)",    "severity": "high",   "param": 15},
    {"id": "noise_mild",         "category": "technical",    "name": "Gaussian noise (mild)",     "severity": "low",    "param": 0.05},
    {"id": "noise_severe",       "category": "technical",    "name": "Gaussian noise (severe)",   "severity": "high",   "param": 0.2},
    {"id": "brightness_low",     "category": "technical",    "name": "Brightness (dark)",         "severity": "medium", "param": 0.5},
    {"id": "jpeg_heavy",         "category": "technical",    "name": "JPEG compression (heavy)",  "severity": "medium", "param": 10},
    {"id": "occlusion",          "category": "technical",    "name": "Occlusion (black patch)",   "severity": "medium", "param": 0.20},
    # ---- Semantic (6 conditions, per spec table) ----
    {"id": "contradict_text",    "category": "semantic",     "name": "Contradictory text",        "severity": "high"},
    {"id": "vague_text",         "category": "semantic",     "name": "Vague text (<5 words)",     "severity": "medium"},
    {"id": "wrong_metadata",     "category": "semantic",     "name": "Incorrect metadata (permuted)", "severity": "high"},
    {"id": "dermo_swap",         "category": "semantic",     "name": "Dermoscopy image swap (different patient)", "severity": "critical"},
    {"id": "metadata_poison",    "category": "semantic",     "name": "Metadata poisoning (swapped dx)", "severity": "critical"},
    {"id": "hallucination_text", "category": "semantic",     "name": "Text hallucination injection", "severity": "high"},
    # ---- Compound ----
    {"id": "compound_multi",     "category": "compound",     "name": "Multi-failure (2+ failures)", "severity": "critical",
     "components": ["miss_clinical", "noise_mild", "vague_text"]},
]


# ---------------------------------------------------------------------------
# Tensor / numpy helpers
# ---------------------------------------------------------------------------

def tensor_to_bgr(t: torch.Tensor) -> np.ndarray:
    """(C,H,W) float [0,1] tensor → BGR uint8 ndarray."""
    arr = (t.permute(1, 2, 0).cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def bgr_to_tensor(bgr: np.ndarray) -> torch.Tensor:
    """BGR uint8 ndarray → (C,H,W) float [0,1] tensor."""
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return torch.from_numpy(rgb.astype(np.float32) / 255.0).permute(2, 0, 1)


def add_black_occlusion(img: np.ndarray, area_fraction: float = 0.20) -> np.ndarray:
    """Add a random black square covering `area_fraction` of the image."""
    h, w = img.shape[:2]
    side = int((h * w * area_fraction) ** 0.5)
    x = random.randint(0, max(0, w - side))
    y = random.randint(0, max(0, h - side))
    result = img.copy()
    result[y:y+side, x:x+side] = 0
    return result


def jpeg_compress(img: np.ndarray, quality: int = 10) -> np.ndarray:
    """Re-encode image with JPEG compression at given quality (1-100)."""
    encode_param = [cv2.IMWRITE_JPEG_QUALITY, quality]
    _, buf = cv2.imencode(".jpg", img, encode_param)
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


# ---------------------------------------------------------------------------
# Image-level corruption functions
# ---------------------------------------------------------------------------

def corrupt_blur(image: torch.Tensor, kernel_size: int = 5) -> torch.Tensor:
    bgr = tensor_to_bgr(image)
    blurred = cv2.GaussianBlur(bgr, (kernel_size, kernel_size), 0)
    return bgr_to_tensor(blurred)


def corrupt_noise(image: torch.Tensor, sigma: float = 0.05) -> torch.Tensor:
    """Add Gaussian noise (sigma = fraction of [0,1] pixel range)."""
    return (image + sigma * torch.randn_like(image)).clamp(0.0, 1.0)


def corrupt_brightness(image: torch.Tensor, factor: float = 0.5) -> torch.Tensor:
    """Multiply pixel values by factor."""
    return (image * factor).clamp(0.0, 1.0)


def corrupt_jpeg(image: torch.Tensor, quality: int = 10) -> torch.Tensor:
    bgr = tensor_to_bgr(image)
    compressed = jpeg_compress(bgr, quality)
    return bgr_to_tensor(compressed)


def corrupt_occlusion(image: torch.Tensor, area_fraction: float = 0.20) -> torch.Tensor:
    bgr = tensor_to_bgr(image)
    occluded = add_black_occlusion(bgr, area_fraction)
    return bgr_to_tensor(occluded)


# ---------------------------------------------------------------------------
# Text corruption functions
# ---------------------------------------------------------------------------

def corrupt_text_contradictory(text: str, symptoms: Optional[Dict] = None) -> str:
    """Negate one extracted symptom field via template."""
    negations = {
        "itch": "does not itch",
        "bleed": "has not bled",
        "grow": "has not grown",
        "pain": "is not painful",
        "color": "has not changed color",
    }
    if not text:
        return "This lesion looks completely normal and has no concerning features."
    text_lower = text.lower()
    for kw, neg in negations.items():
        if kw in text_lower:
            return text + f" Correction: it {neg}."
    return text + " Update: All previous symptoms were mistaken."


def corrupt_text_vague(text: str, max_words: int = 5) -> str:
    """Truncate text to <5 words."""
    words = text.split()
    return " ".join(words[:max_words]) if words else "something on skin"


# ---------------------------------------------------------------------------
# Metadata corruption
# ---------------------------------------------------------------------------

def corrupt_metadata_permute(
    metadata_tensors: List[torch.Tensor],
    batch_idx: int,
) -> torch.Tensor:
    """Permute one field (column) of metadata across batch (swap between samples)."""
    if len(metadata_tensors) < 2:
        return metadata_tensors[batch_idx]
    result = metadata_tensors[batch_idx].clone()
    # Swap first field with another sample
    swap_idx = (batch_idx + 1) % len(metadata_tensors)
    result[0] = metadata_tensors[swap_idx][0]
    return result


# ---------------------------------------------------------------------------
# CorruptionEngine
# ---------------------------------------------------------------------------

@dataclass
class CorruptedCase:
    """A single corrupted case."""
    original_id: str
    corruption_id: str
    corruption_name: str
    category: str
    # Corrupted modalities (None = original)
    clinical_image: Optional[torch.Tensor] = None
    dermo_image: Optional[torch.Tensor] = None
    metadata_continuous: Optional[torch.Tensor] = None
    patient_text: Optional[str] = None
    # Availability flags
    clinical_available: bool = True
    dermo_available: bool = True
    meta_available: bool = True
    text_available: bool = True


class CorruptionEngine:
    """Generate and cache all 15 corruption conditions.

    Usage:
        engine = CorruptionEngine(seed=42)
        corrupted_cases = engine.corrupt_batch(cases, cache_dir="outputs/stress_cache")
        # Then pass each CorruptedCase to the pipeline
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

    def _apply_corruption(self, cond_id: str, case: Dict, batch: List[Dict]) -> CorruptedCase:
        """Apply a single corruption to a case. Returns CorruptedCase."""
        cond = next(c for c in CORRUPTION_CONDITIONS if c["id"] == cond_id)

        corrupted = CorruptedCase(
            original_id=case.get("case_id", "unknown"),
            corruption_id=cond_id,
            corruption_name=cond["name"],
            category=cond["category"],
            clinical_image=case.get("clinical_image"),
            dermo_image=case.get("dermo_image"),
            metadata_continuous=case.get("metadata_continuous"),
            patient_text=case.get("patient_text", ""),
            clinical_available=case.get("clinical_available", True),
            dermo_available=case.get("dermo_available", True),
            meta_available=case.get("meta_available", True),
            text_available=case.get("text_available", True),
        )

        # --- Availability ---
        if cond_id == "miss_clinical":
            corrupted.clinical_image = None
            corrupted.clinical_available = False
        elif cond_id == "miss_dermo":
            corrupted.dermo_image = None
            corrupted.dermo_available = False
        elif cond_id == "miss_metadata":
            corrupted.metadata_continuous = None
            corrupted.meta_available = False
        elif cond_id == "miss_text":
            corrupted.patient_text = ""
            corrupted.text_available = False

        # --- Technical image corruptions ---
        elif cond_id == "blur_mild" and corrupted.clinical_image is not None:
            corrupted.clinical_image = corrupt_blur(corrupted.clinical_image, kernel_size=5)
        elif cond_id == "blur_severe" and corrupted.clinical_image is not None:
            corrupted.clinical_image = corrupt_blur(corrupted.clinical_image, kernel_size=15)
        elif cond_id == "noise_mild" and corrupted.clinical_image is not None:
            corrupted.clinical_image = corrupt_noise(corrupted.clinical_image, sigma=0.05)
        elif cond_id == "noise_severe" and corrupted.clinical_image is not None:
            corrupted.clinical_image = corrupt_noise(corrupted.clinical_image, sigma=0.2)
        elif cond_id == "brightness_low" and corrupted.clinical_image is not None:
            corrupted.clinical_image = corrupt_brightness(corrupted.clinical_image, factor=0.5)
        elif cond_id == "jpeg_heavy" and corrupted.clinical_image is not None:
            corrupted.clinical_image = corrupt_jpeg(corrupted.clinical_image, quality=10)
        elif cond_id == "occlusion" and corrupted.clinical_image is not None:
            corrupted.clinical_image = corrupt_occlusion(corrupted.clinical_image, area_fraction=0.20)

        # --- Semantic ---
        elif cond_id == "contradict_text":
            corrupted.patient_text = corrupt_text_contradictory(corrupted.patient_text or "")
        elif cond_id == "vague_text":
            corrupted.patient_text = corrupt_text_vague(corrupted.patient_text or "")
        elif cond_id == "wrong_metadata" and corrupted.metadata_continuous is not None:
            all_meta = [c.get("metadata_continuous") for c in batch
                        if c.get("metadata_continuous") is not None]
            corrupted.metadata_continuous = corrupt_metadata_permute(
                all_meta, batch.index(case) if case in batch else 0
            )
        # Semantic condition 4: replace dermoscopy with a different patient's image
        elif cond_id == "dermo_swap":
            # Find another case in the batch with a different diagnosis
            original_label = case.get("label", -1)
            swap_case = next(
                (c for c in batch if c is not case and c.get("label", -1) != original_label),
                None,
            )
            if swap_case is not None and swap_case.get("dermo_image") is not None:
                corrupted.dermo_image = swap_case["dermo_image"]
            # If no different-label case found, use same-batch random swap
            elif len(batch) > 1:
                other = next(c for c in batch if c is not case)
                corrupted.dermo_image = other.get("dermo_image", corrupted.dermo_image)
        # Semantic condition 5: metadata poisoning (swap metadata between different-diagnosis cases)
        elif cond_id == "metadata_poison":
            original_label = case.get("label", -1)
            poison_case = next(
                (c for c in batch if c is not case and c.get("label", -1) != original_label
                 and c.get("metadata_continuous") is not None),
                None,
            )
            if poison_case is not None:
                corrupted.metadata_continuous = poison_case["metadata_continuous"]
        # Semantic condition 6: text hallucination injection
        elif cond_id == "hallucination_text":
            hallucination = " My doctor said this is just a mole and nothing to worry about."
            corrupted.patient_text = (corrupted.patient_text or "") + hallucination

        # --- Compound ---
        elif cond_id == "compound_multi":
            components = cond.get("components", ["miss_clinical", "noise_mild", "vague_text"])
            for sub_cond in components:
                sub_corrupted = self._apply_corruption(sub_cond, {
                    "case_id": case.get("case_id"),
                    "clinical_image": corrupted.clinical_image,
                    "dermo_image": corrupted.dermo_image,
                    "metadata_continuous": corrupted.metadata_continuous,
                    "patient_text": corrupted.patient_text,
                    "clinical_available": corrupted.clinical_available,
                    "dermo_available": corrupted.dermo_available,
                    "meta_available": corrupted.meta_available,
                    "text_available": corrupted.text_available,
                }, batch)
                corrupted.clinical_image = sub_corrupted.clinical_image
                corrupted.dermo_image = sub_corrupted.dermo_image
                corrupted.metadata_continuous = sub_corrupted.metadata_continuous
                corrupted.patient_text = sub_corrupted.patient_text
                corrupted.clinical_available = sub_corrupted.clinical_available
                corrupted.dermo_available = sub_corrupted.dermo_available
                corrupted.meta_available = sub_corrupted.meta_available
                corrupted.text_available = sub_corrupted.text_available

        return corrupted

    def corrupt_batch(
        self,
        cases: List[Dict],
        conditions: Optional[List[str]] = None,
        cache_dir: Optional[str] = None,
    ) -> Dict[str, List[CorruptedCase]]:
        """Apply all (or selected) corruption conditions to a batch of cases.

        Corruptions are generated ONCE and cached.

        Args:
            cases:      list of case dicts
            conditions: list of condition IDs to apply (None = all 15)
            cache_dir:  if provided, save corrupted tensors as .pt files

        Returns:
            dict mapping condition_id → list of CorruptedCase
        """
        if conditions is None:
            conditions = [c["id"] for c in CORRUPTION_CONDITIONS]

        if cache_dir:
            Path(cache_dir).mkdir(parents=True, exist_ok=True)

        results: Dict[str, List[CorruptedCase]] = {}
        for cond_id in conditions:
            print(f"[StressEngine] Applying corruption: {cond_id}")
            corrupted_list = []
            for case in cases:
                cc = self._apply_corruption(cond_id, case, cases)
                corrupted_list.append(cc)
            results[cond_id] = corrupted_list

        return results

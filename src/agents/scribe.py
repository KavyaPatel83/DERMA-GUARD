"""
src/agents/scribe.py — Scribe Agent (DERMA-GUARD v4.0)

Uses Bio_ClinicalBERT (NOT bert-base-uncased) for text encoding.
Extracts structured symptoms via LLM (3 fixed prompts, temperature=0).
Computes PTIS (v1 heuristic + v2 ICC-validated regression).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer


# ---------------------------------------------------------------------------
# Bio_ClinicalBERT encoder — mean-pools last hidden state → 768-d embedding
# ---------------------------------------------------------------------------

CLINICALBERT_REPO = "emilyalsentzer/Bio_ClinicalBERT"


class ClinicalBERTEncoder(nn.Module):
    """Bio_ClinicalBERT text encoder.

    Mean-pools last hidden state → 768-d embedding.
    This is the required encoder per DERMA-GUARD spec (NOT bert-base-uncased).
    """

    def __init__(self, model_name: str = CLINICALBERT_REPO, max_length: int = 128):
        super().__init__()
        self.max_length = max_length
        self._tokenizer: Optional[AutoTokenizer] = None
        self._bert: Optional[AutoModel] = None
        self._loaded = False
        self._model_name = model_name

    def load(self) -> "ClinicalBERTEncoder":
        """Load tokenizer and model weights from HuggingFace."""
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
            self._bert = AutoModel.from_pretrained(self._model_name)
            self._loaded = True
            print(f"[Scribe] ClinicalBERT loaded: {self._model_name}")
        except Exception as e:
            import warnings
            warnings.warn(f"[Scribe] ClinicalBERT unavailable: {e}")
        return self

    @property
    def tokenizer(self):
        if not self._loaded:
            self.load()
        return self._tokenizer

    def encode(self, texts: List[str], device: torch.device | None = None) -> torch.Tensor:
        """Encode a list of texts → (N, 768) float tensor.

        Uses mean-pooling over last hidden state (attention mask aware).
        """
        if not self._loaded:
            self.load()
        if not self._loaded or self._tokenizer is None or self._bert is None:
            # Return zero embeddings as graceful fallback
            return torch.zeros(len(texts), 768)

        enc = self._tokenizer(
            texts,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        if device is not None:
            enc = {k: v.to(device) for k, v in enc.items()}
            self._bert = self._bert.to(device)

        with torch.no_grad():
            out = self._bert(**enc)

        # Mean-pool last hidden state (attention-mask aware)
        last_hidden = out.last_hidden_state  # (N, seq, 768)
        mask = enc["attention_mask"].unsqueeze(-1).float()
        embedding = (last_hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-8)
        return embedding.cpu()  # (N, 768)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Direct tensor forward pass (for training loop integration)."""
        if not self._loaded:
            self.load()
        if self._bert is None:
            return torch.zeros(input_ids.shape[0], 768)
        out = self._bert(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden = out.last_hidden_state
        mask = attention_mask.unsqueeze(-1).float()
        return (last_hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-8)


# ---------------------------------------------------------------------------
# PTIS — Patient Text Informativeness Score
# ---------------------------------------------------------------------------

class PTISv1:
    """PTIS v1: heuristic 7-feature scorer, min-max scaled.

    Features:
        1. word_count (normalised)
        2. symptom_keywords (count of medical keywords)
        3. temporal_info (mentions of duration, onset, ...)
        4. location_info (body location mentions)
        5. specificity_ratio (specific adjectives / total words)
        6. visual_descriptors (color/shape/size terms)
        7. vagueness_penalty (penalise "a bit", "kind of", ...)
    """

    SYMPTOM_KEYWORDS = {
        "pain", "itch", "bleed", "bleeding", "grow", "grew", "change", "changed",
        "bump", "lesion", "mole", "patch", "sore", "wound", "rash", "swollen",
        "raised", "flat", "ulcer", "nodule", "crust", "scale",
    }
    TEMPORAL_WORDS = {
        "month", "week", "year", "day", "since", "ago", "recently", "long",
        "duration", "onset", "started", "began", "for",
    }
    LOCATION_WORDS = {
        "back", "arm", "leg", "face", "chest", "neck", "shoulder", "foot",
        "hand", "abdomen", "scalp", "forehead", "cheek", "nose", "ear",
    }
    VISUAL_WORDS = {
        "black", "brown", "red", "pink", "white", "dark", "light", "color",
        "round", "oval", "irregular", "border", "edge", "size", "cm", "mm",
    }
    VAGUE_WORDS = {
        "a bit", "kind of", "sort of", "maybe", "probably", "not sure",
        "i think", "i don't know", "something", "thing",
    }

    def score(self, text: str) -> float:
        """Return PTIS v1 score ∈ [0, 1]."""
        if not text or not text.strip():
            return 0.0
        text_lower = text.lower()
        words = text_lower.split()
        n = max(len(words), 1)

        f1 = min(1.0, len(words) / 100.0)  # word count (cap at 100)
        f2 = min(1.0, sum(1 for w in words if w in self.SYMPTOM_KEYWORDS) / 5.0)
        f3 = min(1.0, sum(1 for w in words if w in self.TEMPORAL_WORDS) / 3.0)
        f4 = min(1.0, sum(1 for w in words if w in self.LOCATION_WORDS) / 2.0)
        f5 = sum(1 for w in words if len(w) > 6) / n  # specificity proxy
        f6 = min(1.0, sum(1 for w in words if w in self.VISUAL_WORDS) / 3.0)
        # Vagueness penalty
        vague_count = sum(1 for v in self.VAGUE_WORDS if v in text_lower)
        f7 = max(0.0, 1.0 - 0.2 * vague_count)

        # Weighted combination
        weights = [0.15, 0.25, 0.15, 0.15, 0.10, 0.10, 0.10]
        score = sum(w * f for w, f in zip(weights, [f1, f2, f3, f4, f5, f6, f7]))
        return float(np.clip(score, 0.0, 1.0))


class PTISv2Regressor(nn.Module):
    """PTIS v2: fit regression from heuristic features to mean human ICC score.

    Trained on 100+ samples rated 0–3 by 3 raters.
    ICC is computed externally; this model learns the mapping:
        heuristic_features (7) → mean human score (0–3, then normalized to 0–1)
    """

    def __init__(self, input_dim: int = 7):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid(),  # output in [0, 1]
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, 7) heuristic features → (B, 1) PTIS v2 score."""
        return self.net(x)


def compute_ptis_features(text: str) -> torch.Tensor:
    """Extract 7 PTIS heuristic features as a tensor (7,)."""
    scorer = PTISv1()
    text_lower = text.lower()
    words = text_lower.split()
    n = max(len(words), 1)

    features = [
        min(1.0, len(words) / 100.0),
        min(1.0, sum(1 for w in words if w in scorer.SYMPTOM_KEYWORDS) / 5.0),
        min(1.0, sum(1 for w in words if w in scorer.TEMPORAL_WORDS) / 3.0),
        min(1.0, sum(1 for w in words if w in scorer.LOCATION_WORDS) / 2.0),
        sum(1 for w in words if len(w) > 6) / n,
        min(1.0, sum(1 for w in words if w in scorer.VISUAL_WORDS) / 3.0),
        max(0.0, 1.0 - 0.2 * sum(1 for v in scorer.VAGUE_WORDS if v in text_lower)),
    ]
    return torch.tensor(features, dtype=torch.float32)


# ---------------------------------------------------------------------------
# Metadata encoder
# ---------------------------------------------------------------------------

class MetadataEncoder(nn.Module):
    """Encode metadata fields → 64-d embedding.

    Continuous fields: z-score normalized (train stats only).
    Categorical fields: learned embeddings dim = min(50, (n_cats+1)//2).
    Missing: binary indicator + zero imputation.
    """

    def __init__(self, continuous_dims: int = 10, categorical_sizes: Optional[List[int]] = None,
                 output_dim: int = 64):
        super().__init__()
        categorical_sizes = categorical_sizes or []

        # Categorical embeddings
        self.cat_embeddings = nn.ModuleList([
            nn.Embedding(n, min(50, (n + 1) // 2))
            for n in categorical_sizes
        ])
        cat_out_dim = sum(min(50, (n + 1) // 2) for n in categorical_sizes)

        # Total input = continuous + missing_indicators + categorical_embeddings
        in_dim = continuous_dims * 2 + cat_out_dim  # *2 for missingness indicators

        self.proj = nn.Sequential(
            nn.Linear(in_dim, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim),
        )

    def forward(
        self,
        continuous: torch.Tensor,         # (B, cont_dims) — zero-imputed
        missing_mask: torch.Tensor,        # (B, cont_dims) — binary 1=missing
        categorical: Optional[List[torch.Tensor]] = None,  # list of (B,) int tensors
    ) -> torch.Tensor:
        """Returns (B, 64) metadata embedding."""
        parts = [continuous, missing_mask.float()]
        if categorical and self.cat_embeddings:
            for i, (cat_tensor, emb_layer) in enumerate(
                zip(categorical, self.cat_embeddings)
            ):
                parts.append(emb_layer(cat_tensor))
        x = torch.cat(parts, dim=-1)
        return self.proj(x)


# ---------------------------------------------------------------------------
# ScribeAgent
# ---------------------------------------------------------------------------

@dataclass
class ScribeReport:
    """Output from ScribeAgent.process_case()."""
    symptoms: Dict[str, str]         # extracted symptoms {key: value/unknown}
    ptis: float                       # PTIS score ∈ [0,1]
    risk_factors: List[str]           # extracted risk factors
    summary: str                      # short text summary
    text_embedding: torch.Tensor      # (768,) ClinicalBERT embedding
    metadata_embedding: torch.Tensor  # (64,) metadata embedding
    metadata_quality: float           # 1 - fraction_missing


class ScribeAgent:
    """Processes free-text patient descriptions + metadata.

    Uses:
    - Bio_ClinicalBERT for text encoding (NOT bert-base-uncased)
    - LLM (Qwen2.5) for structured symptom extraction (3 fixed prompts, T=0)
    - PTIS v1 (heuristic, always available) + v2 (ICC regression, if trained)
    - MetadataEncoder for metadata → 64-d embedding
    """

    SYMPTOM_FIELDS = ["duration", "growth", "color_change", "itching", "pain", "bleeding"]

    def __init__(
        self,
        llm_client=None,
        ptis_v2_path: Optional[str] = None,
        metadata_encoder: Optional[MetadataEncoder] = None,
        device: Optional[torch.device] = None,
    ):
        self.llm = llm_client
        self.device = device or torch.device("cpu")
        self.bert = ClinicalBERTEncoder().load()
        self.ptis_v1 = PTISv1()
        self.ptis_v2: Optional[PTISv2Regressor] = None
        self.metadata_encoder = metadata_encoder

        # Load PTISv2 if checkpoint available
        if ptis_v2_path and __import__("pathlib").Path(ptis_v2_path).exists():
            self.ptis_v2 = PTISv2Regressor()
            self.ptis_v2.load_state_dict(
                torch.load(ptis_v2_path, map_location="cpu", weights_only=True)
            )
            self.ptis_v2.eval()
            print(f"[Scribe] PTIS v2 loaded from {ptis_v2_path}")

    def compute_ptis(self, text: str) -> float:
        """Compute PTIS using v2 if available, else v1."""
        if self.ptis_v2 is not None:
            feats = compute_ptis_features(text).unsqueeze(0)
            with torch.no_grad():
                score = self.ptis_v2(feats).item()
        else:
            score = self.ptis_v1.score(text)
        return float(np.clip(score, 0.0, 1.0))

    def extract_symptoms(self, text: str) -> Dict[str, str]:
        """Extract structured symptoms via LLM (temperature=0, JSON schema).

        System prompt: 'If a symptom is not mentioned, output unknown.
                        Never output false for something not stated.'
        Returns: {duration, growth, color_change, itching, pain, bleeding}
        Each value: 'true' | 'false' | 'unknown'
        """
        if not text or not text.strip():
            return {f: "unknown" for f in self.SYMPTOM_FIELDS}

        if self.llm is None:
            return self._heuristic_symptom_extract(text)

        prompt = self._extraction_prompt(text)
        try:
            raw = self.llm.generate(prompt, temperature=0.0, max_tokens=256)
            return self._parse_symptom_json(raw)
        except Exception as e:
            import warnings
            warnings.warn(f"[Scribe] LLM symptom extraction failed: {e}, using heuristics.")
            return self._heuristic_symptom_extract(text)

    def _extraction_prompt(self, text: str) -> str:
        return (
            "You are a clinical symptom extractor. Extract the following fields from the "
            "patient's description and return valid JSON only.\n\n"
            "Fields: duration, growth, color_change, itching, pain, bleeding\n"
            "Values: true | false | unknown\n\n"
            "RULES:\n"
            "- If a symptom is not mentioned, output 'unknown'.\n"
            "- Never output false for something not stated.\n"
            "- Output ONLY a JSON object, no prose.\n\n"
            f"Patient description:\n{text}\n\n"
            "JSON output:"
        )

    def _parse_symptom_json(self, raw: str) -> Dict[str, str]:
        """Parse LLM JSON output with fallback."""
        import json
        # Find JSON in response
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                result = {}
                for f in self.SYMPTOM_FIELDS:
                    val = str(data.get(f, "unknown")).lower()
                    if val not in ("true", "false", "unknown"):
                        val = "unknown"
                    result[f] = val
                return result
            except Exception:
                pass
        return {f: "unknown" for f in self.SYMPTOM_FIELDS}

    def _heuristic_symptom_extract(self, text: str) -> Dict[str, str]:
        """Rule-based fallback symptom extraction."""
        text_lower = text.lower()
        result = {}
        kw_map = {
            "duration":     ["month", "week", "year", "day", "since", "ago", "long"],
            "growth":       ["grow", "grew", "bigger", "larger", "expanding"],
            "color_change": ["color", "colour", "darker", "lighter", "changed color"],
            "itching":      ["itch", "itchy", "scratching"],
            "pain":         ["pain", "painful", "hurts", "sore", "tender"],
            "bleeding":     ["bleed", "bleeding", "blood"],
        }
        for field, keywords in kw_map.items():
            result[field] = "true" if any(k in text_lower for k in keywords) else "unknown"
        return result

    def generate_question(self, missing_field: str, expected_value: str = "") -> str:
        """Generate a natural language follow-up question for a missing field."""
        if self.llm is None:
            return self._default_question(missing_field)

        prompt = (
            f"Generate a single, clear, patient-friendly question to ask about the following "
            f"missing clinical information.\n\n"
            f"Missing field: {missing_field}\n"
            f"Expected type: {expected_value or 'yes/no or description'}\n\n"
            "Output only the question, nothing else."
        )
        try:
            return self.llm.generate(prompt, temperature=0.0, max_tokens=64).strip()
        except Exception:
            return self._default_question(missing_field)

    def _default_question(self, field: str) -> str:
        defaults = {
            "duration": "How long have you had this skin lesion?",
            "growth": "Has the lesion changed in size recently?",
            "color_change": "Has the color of the lesion changed?",
            "itching": "Does the lesion itch?",
            "pain": "Is the lesion painful or tender to the touch?",
            "bleeding": "Has the lesion bled or crusted?",
        }
        return defaults.get(field, f"Can you provide more details about: {field}?")

    def process_case(
        self,
        text: str,
        metadata_continuous: Optional[torch.Tensor] = None,
        metadata_missing_mask: Optional[torch.Tensor] = None,
        metadata_categorical: Optional[List[torch.Tensor]] = None,
    ) -> ScribeReport:
        """Full scribe pipeline for one case.

        Args:
            text:                    raw patient text description
            metadata_continuous:     (cont_dims,) tensor of continuous metadata
            metadata_missing_mask:   (cont_dims,) binary mask (1=missing)
            metadata_categorical:    list of int tensors for categorical fields

        Returns:
            ScribeReport
        """
        # 1. Text embedding
        text_embedding = self.bert.encode([text or ""], device=self.device)[0]  # (768,)

        # 2. PTIS score
        ptis_score = self.compute_ptis(text or "")

        # 3. Symptom extraction
        symptoms = self.extract_symptoms(text or "")

        # 4. Risk factors (simple keyword extraction)
        risk_factors = self._extract_risk_factors(text or "")

        # 5. Summary
        summary = self._make_summary(text or "", symptoms, ptis_score)

        # 6. Metadata embedding
        if (self.metadata_encoder is not None
                and metadata_continuous is not None
                and metadata_missing_mask is not None):
            with torch.no_grad():
                meta_emb = self.metadata_encoder(
                    metadata_continuous.unsqueeze(0),
                    metadata_missing_mask.unsqueeze(0),
                    [c.unsqueeze(0) for c in metadata_categorical] if metadata_categorical else None,
                )[0]  # (64,)
            n_missing = metadata_missing_mask.float().mean().item()
        else:
            meta_emb = torch.zeros(64)
            n_missing = 1.0 if metadata_continuous is None else 0.0

        metadata_quality = float(1.0 - (
            metadata_missing_mask.float().mean().item()
            if metadata_missing_mask is not None else 1.0
        ))

        return ScribeReport(
            symptoms=symptoms,
            ptis=ptis_score,
            risk_factors=risk_factors,
            summary=summary,
            text_embedding=text_embedding,
            metadata_embedding=meta_emb,
            metadata_quality=metadata_quality,
        )

    def _extract_risk_factors(self, text: str) -> List[str]:
        """Simple keyword-based risk factor extraction."""
        text_lower = text.lower()
        factors = []
        rf_map = {
            "sun_exposure": ["sun", "outdoor", "beach", "tanning"],
            "family_history": ["family", "father", "mother", "sibling", "relative"],
            "fair_skin": ["fair", "pale", "light skin", "freckles"],
            "immunosuppression": ["immunosuppressed", "transplant", "chemo", "steroid"],
            "prior_skin_cancer": ["previous", "before", "history of skin"],
        }
        for factor, keywords in rf_map.items():
            if any(k in text_lower for k in keywords):
                factors.append(factor)
        return factors

    def _make_summary(self, text: str, symptoms: Dict[str, str], ptis: float) -> str:
        """Create a brief text summary of the case."""
        present = [f for f, v in symptoms.items() if v == "true"]
        absent = [f for f, v in symptoms.items() if v == "false"]
        quality = "high" if ptis > 0.7 else ("moderate" if ptis > 0.3 else "low")
        summary = f"Text informativeness: {quality} (PTIS={ptis:.2f}). "
        if present:
            summary += f"Reported symptoms: {', '.join(present)}. "
        if absent:
            summary += f"Denied: {', '.join(absent)}."
        return summary.strip()

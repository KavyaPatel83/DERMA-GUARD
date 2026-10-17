"""src/agents/devils_advocate.py — Devil's Advocate / Evidence Profiler.

Computes the EvidenceProfile: Q, R, C, M, OOD score.
This is the safety layer of DERMA-GUARD v4.0.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F

from src.evidence.quality import compute_image_quality, compute_text_quality, compute_metadata_quality
from src.evidence.reliability import (
    ReliabilityMLP, compute_predictive_entropy,
    compute_tta_stability, compute_agreement_score, compute_reliability,
)
from src.evidence.consistency import compute_consistency
from src.evidence.missingness import compute_missingness, ALL_MODALITIES
from src.evidence.utility import approximate_utility_from_training


# ---------------------------------------------------------------------------
# OOD Detection — Mahalanobis distance (class-conditional)
# ---------------------------------------------------------------------------

class OODDetector:
    """Out-of-distribution detection using class-conditional Mahalanobis distance.

    ood_score = min_k (z_fused - mu_k)^T Sigma_k^-1 (z_fused - mu_k)

    Fitted on training embeddings. Threshold calibrated on validation set.
    """

    def __init__(self, threshold: float = 50.0):
        self.threshold = threshold
        self._class_means: Optional[Dict[int, np.ndarray]] = None
        self._class_covs: Optional[Dict[int, np.ndarray]] = None
        self._class_inv_covs: Optional[Dict[int, np.ndarray]] = None
        self._fitted = False

    def fit(
        self,
        embeddings: np.ndarray,  # (N, D)
        labels: np.ndarray,      # (N,)
    ) -> "OODDetector":
        """Fit class-conditional Gaussian parameters on training embeddings."""
        classes = np.unique(labels)
        self._class_means = {}
        self._class_covs = {}
        self._class_inv_covs = {}

        for c in classes:
            mask = labels == c
            emb_c = embeddings[mask]
            mu = emb_c.mean(axis=0)
            # Regularised covariance (add small identity for invertibility)
            cov = np.cov(emb_c.T) + 1e-6 * np.eye(emb_c.shape[1])
            self._class_means[int(c)] = mu
            self._class_covs[int(c)] = cov
            try:
                self._class_inv_covs[int(c)] = np.linalg.inv(cov)
            except np.linalg.LinAlgError:
                # Fallback to pseudo-inverse
                self._class_inv_covs[int(c)] = np.linalg.pinv(cov)

        self._fitted = True
        return self

    def score(self, z: np.ndarray) -> float:
        """Compute minimum Mahalanobis distance to any class centroid.

        Lower score = more in-distribution.
        Higher score = more OOD.
        """
        if not self._fitted or not self._class_means:
            return 0.0  # cannot detect OOD if not fitted

        if z.ndim > 1:
            z = z.flatten()

        min_dist = float("inf")
        for c, mu in self._class_means.items():
            inv_cov = self._class_inv_covs[c]
            diff = z - mu
            dist = float(diff @ inv_cov @ diff)
            if dist < min_dist:
                min_dist = dist

        return min_dist

    def is_ood(self, z: np.ndarray) -> bool:
        """Return True if the embedding is OOD (above threshold)."""
        return self.score(z) > self.threshold

    def calibrate_threshold(
        self,
        val_embeddings: np.ndarray,
        val_labels: np.ndarray,
        fpr_target: float = 0.05,
    ) -> float:
        """Calibrate OOD threshold on validation set.

        Uses the (1 - fpr_target)-quantile of in-distribution scores
        as the threshold.
        """
        scores = [self.score(val_embeddings[i]) for i in range(len(val_embeddings))]
        self.threshold = float(np.quantile(scores, 1.0 - fpr_target))
        return self.threshold


# ---------------------------------------------------------------------------
# EvidenceProfile output
# ---------------------------------------------------------------------------

@dataclass
class EvidenceProfile:
    """Complete evidence profile for a case."""
    quality: Dict[str, float]           # modality → Q_m ∈ [0,1]
    reliability: Dict[str, float]       # modality → R_m ∈ [0,1]
    utility: Dict[str, float]           # modality → U_m (approx from training stats)
    consistency: float                  # C(x) ∈ [0,1]
    conflict_flag: bool                 # True if C < 0.3
    conflict_details: Dict              # per-pair JSD details
    missing_modalities: List[str]       # list of missing modality names
    missing_mask: torch.Tensor          # binary tensor [4] (1=available)
    ood_score: float                    # Mahalanobis distance
    overall_risk: float                 # composite risk score ∈ [0,1]

    def to_dict(self) -> Dict:
        return {
            "quality": self.quality,
            "reliability": self.reliability,
            "utility": self.utility,
            "consistency": self.consistency,
            "conflict_flag": self.conflict_flag,
            "conflict_details": self.conflict_details,
            "missing_modalities": self.missing_modalities,
            "missing_mask": self.missing_mask.tolist(),
            "ood_score": self.ood_score,
            "overall_risk": self.overall_risk,
        }


# ---------------------------------------------------------------------------
# DevilsAdvocateAgent
# ---------------------------------------------------------------------------

class DevilsAdvocateAgent:
    """Computes EvidenceProfile: quality, reliability, utility, consistency, OOD.

    This is the safety layer of DERMA-GUARD v4.0.
    Works together with VisionSpecialistTeam and ScribeAgent outputs.
    """

    def __init__(
        self,
        reliability_mlp: Optional[ReliabilityMLP] = None,
        ood_detector: Optional[OODDetector] = None,
        training_utility_stats: Optional[Dict] = None,
        quality_mlp=None,
    ):
        self.reliability_mlp = reliability_mlp or ReliabilityMLP()
        self.ood_detector = ood_detector or OODDetector()
        self.training_utility_stats = training_utility_stats
        self.quality_mlp = quality_mlp

    def profile(
        self,
        # Vision report
        vision_report,  # VisionReport dataclass
        # Scribe report
        scribe_report,  # ScribeReport dataclass
        # Availability flags
        clinical_available: bool = True,
        dermo_available: bool = True,
        meta_available: bool = True,
        text_available: bool = True,
        # Fused embedding (for OOD) — can be None before fusion
        fused_embedding: Optional[torch.Tensor] = None,
        # Predicted diagnosis (for utility lookup)
        predicted_diagnosis: Optional[int] = None,
    ) -> EvidenceProfile:
        """Compute the full EvidenceProfile.

        Args:
            vision_report:     VisionReport from VisionSpecialistTeam
            scribe_report:     ScribeReport from ScribeAgent
            *_available:       modality availability flags
            fused_embedding:   (D,) fused embedding for OOD detection
            predicted_diagnosis: int class index for utility approximation

        Returns:
            EvidenceProfile
        """
        # ---- 1. Quality -------------------------------------------------------
        quality: Dict[str, float] = {}

        for model_name, q_score in vision_report.quality_scores.items():
            quality[model_name] = float(q_score)

        quality["text"] = compute_text_quality(scribe_report.ptis)
        quality["metadata"] = scribe_report.metadata_quality

        # ---- 2. Reliability --------------------------------------------------
        reliability: Dict[str, float] = {}

        model_preds = vision_report.model_predictions
        all_model_names = list(model_preds.keys())

        for name in all_model_names:
            logits = model_preds[name]
            H_m = compute_predictive_entropy(logits)
            # TTA stability: approximate (no augmentation fn here, returns 1.0 if not provided)
            S_m = 1.0  # placeholder; actual TTA done during training
            # Agreement: cosine similarity vs other modalities
            others = [model_preds[n] for n in all_model_names if n != name]
            A_m = compute_agreement_score(logits, others)
            # Quality for this modality
            q_key = "clinical" if "clinical" in name else "dermoscopy" if "dermo" in name else name
            Q_m = quality.get(q_key, quality.get(name, 0.5))

            reliability[name] = compute_reliability(Q_m, H_m, S_m, A_m, self.reliability_mlp)

        # ---- 3. Utility (approximated from training stats) -------------------
        utility = approximate_utility_from_training(
            self.training_utility_stats, predicted_diagnosis
        )

        # ---- 4. Consistency --------------------------------------------------
        consistency, conflict_flag, conflict_details = compute_consistency(model_preds)

        # ---- 5. Missingness --------------------------------------------------
        miss = compute_missingness(clinical_available, dermo_available, meta_available, text_available)

        # ---- 6. OOD ----------------------------------------------------------
        ood_score = 0.0
        if fused_embedding is not None:
            z_np = fused_embedding.detach().cpu().numpy().flatten()
            ood_score = self.ood_detector.score(z_np)

        # ---- 7. Overall risk -------------------------------------------------
        overall_risk = self._compute_overall_risk(
            quality=quality,
            reliability=reliability,
            consistency=consistency,
            conflict_flag=conflict_flag,
            missing_count=miss["missing_count"],
            ood_score=ood_score,
        )

        return EvidenceProfile(
            quality=quality,
            reliability=reliability,
            utility=utility,
            consistency=consistency,
            conflict_flag=conflict_flag,
            conflict_details=conflict_details,
            missing_modalities=miss["missing_list"],
            missing_mask=miss["missing_mask"],
            ood_score=ood_score,
            overall_risk=overall_risk,
        )

    def _compute_overall_risk(
        self,
        quality: Dict[str, float],
        reliability: Dict[str, float],
        consistency: float,
        conflict_flag: bool,
        missing_count: int,
        ood_score: float,
    ) -> float:
        """Composite risk score ∈ [0, 1] (1 = high risk / unsafe)."""
        # Low quality → high risk
        mean_quality = np.mean(list(quality.values())) if quality else 0.5
        # Low reliability → high risk
        mean_reliability = np.mean(list(reliability.values())) if reliability else 0.5
        # Low consistency → high risk
        # Missing modalities → higher risk
        missing_ratio = missing_count / len(ALL_MODALITIES)
        # OOD score → normalised (threshold 50 → risk=1)
        ood_risk = min(1.0, ood_score / max(self.ood_detector.threshold, 1e-8))
        # Conflict penalty
        conflict_penalty = 0.3 if conflict_flag else 0.0

        risk = (
            0.25 * (1.0 - mean_quality)
            + 0.25 * (1.0 - mean_reliability)
            + 0.20 * (1.0 - consistency)
            + 0.15 * missing_ratio
            + 0.10 * ood_risk
            + conflict_penalty
        )
        return float(np.clip(risk, 0.0, 1.0))

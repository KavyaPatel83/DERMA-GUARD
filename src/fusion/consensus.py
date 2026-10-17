"""
src/fusion/consensus.py — 4-Level Consensus Hierarchy (DERMA-GUARD v4.0)

Replaces conformal prediction with a safety-tiered decision framework.
Levels:
  1 → ACCEPT      (strong agreement, high confidence, good quality)
  2 → ARBITRATE   (moderate agreement, evidence-based arbitration)
  3 → ACQUIRE     (high uncertainty → request more data)
  4 → ESCALATE    (critical conflict or unresolvable → human expert)
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, Optional

import torch
import torch.nn.functional as F


@dataclass
class ConsensusResult:
    """Output of classify_consensus."""
    level: int           # 1, 2, 3, or 4
    action: str          # ACCEPT | ARBITRATE | ACQUIRE | ESCALATE
    diagnosis: Optional[int] = None       # class index (levels 1 & 2 only)
    confidence: Optional[float] = None   # fusion confidence (levels 1 & 2)
    reason: Optional[str] = None         # explanation (levels 3 & 4)

    def to_dict(self) -> Dict:
        return {
            "level": self.level,
            "action": self.action,
            "diagnosis": self.diagnosis,
            "confidence": self.confidence,
            "reason": self.reason,
        }


def classify_consensus(
    fused_prediction: Dict,    # output of DiagnosisAdaptiveFusion.fuse() or .to_dict()
    evidence_profile,          # EvidenceProfile dataclass (or .to_dict())
    vision_report,             # VisionReport dataclass
) -> ConsensusResult:
    """Apply the 4-level consensus hierarchy.

    Args:
        fused_prediction:   dict with keys 'prediction' (logits), 'confidence', 'diagnosis'
        evidence_profile:   EvidenceProfile (or dict) with quality, reliability, conflict_flag, consistency
        vision_report:      VisionReport with model_predictions, model_confidences

    Returns:
        ConsensusResult with level ∈ {1,2,3,4} and action.
    """
    # --- Unpack inputs ---
    if hasattr(fused_prediction, "confidence"):
        fusion_confidence = fused_prediction.confidence
    else:
        fusion_confidence = fused_prediction.get("confidence", 0.0)

    if hasattr(evidence_profile, "quality"):
        Q = evidence_profile.quality
        conflict_flag = evidence_profile.conflict_flag
        C = evidence_profile.consistency
        reliability = evidence_profile.reliability
    else:
        Q = evidence_profile.get("quality", {})
        conflict_flag = evidence_profile.get("conflict_flag", False)
        C = evidence_profile.get("consistency", 1.0)
        reliability = evidence_profile.get("reliability", {})

    if hasattr(vision_report, "model_predictions"):
        model_preds = vision_report.model_predictions
    else:
        model_preds = vision_report.get("model_predictions", {})

    # --- Count top-1 model agreements ---
    top1_predictions = {}
    for name, logits in model_preds.items():
        if logits is not None:
            pred_class = int(logits.argmax(dim=-1).flatten()[0].item())
            top1_predictions[name] = pred_class

    diag_counts = Counter(top1_predictions.values())
    if not diag_counts:
        return ConsensusResult(level=4, action="ESCALATE", reason="No model predictions available")

    max_agreement = max(diag_counts.values())
    majority_diag = diag_counts.most_common(1)[0][0]

    # Min quality across available modalities
    min_quality = min(Q.values()) if Q else 0.0

    # ---- Level 1: ACCEPT (strong consensus) ----------------------------------
    if (
        max_agreement >= 3
        and fusion_confidence >= 0.80
        and min_quality >= 0.30
        and not conflict_flag
    ):
        return ConsensusResult(
            level=1,
            action="ACCEPT",
            diagnosis=majority_diag,
            confidence=fusion_confidence,
        )

    # ---- Level 2: ARBITRATE (moderate consensus) -----------------------------
    if (
        max_agreement == 2
        and fusion_confidence >= 0.50
        and not conflict_flag
    ):
        # Evidence-based arbitration: weight votes by quality × reliability
        weighted_votes: Dict[int, float] = {}
        for name, diag in top1_predictions.items():
            q_key = "clinical" if "clinical" in name else "dermoscopy" if "dermo" in name else name
            score = Q.get(q_key, Q.get(name, 0.5)) * reliability.get(name, 0.5)
            weighted_votes[diag] = weighted_votes.get(diag, 0.0) + score

        best_diag = max(weighted_votes, key=weighted_votes.get)
        return ConsensusResult(
            level=2,
            action="ARBITRATE",
            diagnosis=best_diag,
            confidence=fusion_confidence,
        )

    # ---- Level 4: ESCALATE (critical conflict) — checked BEFORE Level 3 ------
    if conflict_flag and C < 0.3:
        return ConsensusResult(
            level=4,
            action="ESCALATE",
            reason="Critical cross-modal conflict detected (consistency < 0.3)",
        )

    # ---- Level 3: ACQUIRE (high uncertainty) ---------------------------------
    if (
        max_agreement <= 1
        or fusion_confidence < 0.50
        or min_quality < 0.30
    ):
        return ConsensusResult(
            level=3,
            action="ACQUIRE",
            reason=(
                f"High uncertainty (conf={fusion_confidence:.2f}, "
                f"agreement={max_agreement}/5, min_quality={min_quality:.2f})"
            ),
        )

    # ---- Level 4: ESCALATE (fallthrough — unresolvable) ---------------------
    return ConsensusResult(
        level=4,
        action="ESCALATE",
        reason="Unresolvable disagreement between models",
    )

"""
tests/test_consensus.py — Consensus hierarchy tests (DERMA-GUARD v4.0)

Tests:
  - Level 1-4 boundary cases
  - Empty evidence handling
  - Appropriate escalation under conflict
"""
import pytest
import torch
from unittest.mock import MagicMock

from src.fusion.consensus import classify_consensus, ConsensusResult


def make_vision_report(agreement=3, n_models=5, confidence=0.90):
    """Build a mock VisionReport with specified agreement level."""
    majority_class = 2
    # Assign majority_class to `agreement` models, others get different predictions
    predictions = {}
    model_names = [
        "dermlip_panderm", "panderm", "swin_tiny_clinical",
        "swin_tiny_dermoscopy", "resnet152"
    ][:n_models]
    for i, name in enumerate(model_names):
        if i < agreement:
            logits = torch.zeros(7)
            logits[majority_class] = 5.0  # high confidence in majority class
        else:
            logits = torch.zeros(7)
            logits[(majority_class + i + 1) % 7] = 5.0
        predictions[name] = logits

    report = MagicMock()
    report.model_predictions = predictions
    report.model_confidences = {k: confidence for k in predictions}
    return report


def make_evidence_profile(
    quality=None, conflict_flag=False, consistency=0.9,
    reliability=None, missing=None
):
    """Build a mock EvidenceProfile."""
    ep = MagicMock()
    ep.quality = quality or {"clinical": 0.8, "dermoscopy": 0.7, "text": 0.6, "metadata": 0.9}
    ep.conflict_flag = conflict_flag
    ep.consistency = consistency
    ep.reliability = reliability or {"dermlip_panderm": 0.8, "panderm": 0.8}
    ep.missing_modalities = missing or []
    return ep


def make_fusion_result(confidence=0.90, diagnosis=2):
    """Build a mock FusionResult."""
    fr = MagicMock()
    fr.confidence = confidence
    fr.diagnosis = diagnosis
    return fr


class TestLevel1Accept:
    def test_strong_consensus_returns_level1(self):
        """≥3 models agree, confidence ≥0.80, no conflict → Level 1 ACCEPT."""
        result = classify_consensus(
            fused_prediction=make_fusion_result(confidence=0.85),
            evidence_profile=make_evidence_profile(conflict_flag=False, consistency=0.9),
            vision_report=make_vision_report(agreement=4, confidence=0.85),
        )
        assert result.level == 1
        assert result.action == "ACCEPT"
        assert result.diagnosis is not None

    def test_low_confidence_does_not_level1(self):
        """Confidence < 0.80 → should not be Level 1."""
        result = classify_consensus(
            fused_prediction=make_fusion_result(confidence=0.60),
            evidence_profile=make_evidence_profile(conflict_flag=False),
            vision_report=make_vision_report(agreement=4, confidence=0.60),
        )
        assert result.level != 1 or result.action != "ACCEPT", \
            "Low confidence should not yield Level 1 ACCEPT"


class TestLevel2Arbitrate:
    def test_moderate_consensus_returns_level2(self):
        """Exactly 2 models agree, confidence ≥0.50, no conflict → Level 2 ARBITRATE."""
        result = classify_consensus(
            fused_prediction=make_fusion_result(confidence=0.65),
            evidence_profile=make_evidence_profile(conflict_flag=False, consistency=0.7),
            vision_report=make_vision_report(agreement=2, confidence=0.65),
        )
        assert result.level == 2
        assert result.action == "ARBITRATE"


class TestLevel3Acquire:
    def test_very_low_agreement_triggers_acquire(self):
        """Max agreement = 1 with no conflict → Level 3 ACQUIRE."""
        result = classify_consensus(
            fused_prediction=make_fusion_result(confidence=0.30),
            evidence_profile=make_evidence_profile(conflict_flag=False, consistency=0.8),
            vision_report=make_vision_report(agreement=1, confidence=0.30),
        )
        assert result.level == 3
        assert result.action == "ACQUIRE"

    def test_low_quality_triggers_acquire(self):
        """Very low quality (< 0.30) → Level 3 ACQUIRE."""
        low_q = {"clinical": 0.10, "dermoscopy": 0.15, "text": 0.20, "metadata": 0.25}
        result = classify_consensus(
            fused_prediction=make_fusion_result(confidence=0.70),
            evidence_profile=make_evidence_profile(quality=low_q, conflict_flag=False),
            vision_report=make_vision_report(agreement=3, confidence=0.70),
        )
        # min(quality) < 0.30 → should trigger acquire
        assert result.action in ("ACQUIRE", "ESCALATE")


class TestLevel4Escalate:
    def test_critical_conflict_escalates(self):
        """conflict_flag=True AND consistency < 0.3 → Level 4 ESCALATE."""
        result = classify_consensus(
            fused_prediction=make_fusion_result(confidence=0.50),
            evidence_profile=make_evidence_profile(conflict_flag=True, consistency=0.20),
            vision_report=make_vision_report(agreement=2, confidence=0.50),
        )
        assert result.level == 4
        assert result.action == "ESCALATE"

    def test_no_model_predictions_escalates(self):
        """Empty model predictions → escalation."""
        empty_report = MagicMock()
        empty_report.model_predictions = {}
        empty_report.model_confidences = {}

        result = classify_consensus(
            fused_prediction=make_fusion_result(confidence=0.0),
            evidence_profile=make_evidence_profile(),
            vision_report=empty_report,
        )
        assert result.action == "ESCALATE"

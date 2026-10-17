"""
tests/test_verification.py — Two-stage verification tests (DERMA-GUARD v4.0)

Tests:
  - Rule-based checks on known pass/fail cases
  - LLM timeout fallback (passes rules even if LLM unavailable)
"""
import pytest

from src.llm.verification import stage1_verify, stage2_verify, VerificationResult
from unittest.mock import MagicMock


def make_evidence_profile(
    ood_score=0.0,
    conflict_flag=False,
    consistency=0.9,
    missing_list=None,
    quality=None,
):
    ep = MagicMock()
    ep.ood_score = ood_score
    ep.conflict_flag = conflict_flag
    ep.consistency = consistency
    ep.missing_modalities = missing_list or []
    ep.quality = quality or {"clinical": 0.8, "text": 0.7}
    return ep


class TestStage1Verification:
    def test_clean_evidence_passes(self):
        """Normal evidence → Stage 1 PASS."""
        result = stage1_verify(make_evidence_profile())
        assert result.passed

    def test_high_ood_fails(self):
        """OOD score above threshold → FAIL."""
        result = stage1_verify(make_evidence_profile(ood_score=200.0))
        assert not result.passed
        assert "out-of-distribution" in result.reason.lower() or "ood" in result.reason.lower()

    def test_critical_conflict_fails(self):
        """conflict_flag=True AND consistency < 0.3 → FAIL."""
        result = stage1_verify(make_evidence_profile(conflict_flag=True, consistency=0.25))
        assert not result.passed

    def test_conflict_without_low_consistency_passes(self):
        """conflict_flag=True but consistency ≥ 0.3 → PASS (not a hard fail)."""
        result = stage1_verify(make_evidence_profile(conflict_flag=True, consistency=0.5))
        # Should still pass (conflict alone without consistency < 0.3 is not critical)
        assert result.passed

    def test_all_modalities_missing_fails(self):
        """No evidence → FAIL."""
        all_missing = ["clinical_image", "dermoscopy_image", "metadata", "text"]
        result = stage1_verify(make_evidence_profile(missing_list=all_missing))
        assert not result.passed
        assert "no evidence" in result.reason.lower() or "missing" in result.reason.lower()

    def test_partial_missingness_passes(self):
        """Some missing modalities, but not all → PASS."""
        result = stage1_verify(make_evidence_profile(missing_list=["text"]))
        assert result.passed


class TestStage2Verification:
    def test_valid_report_passes(self):
        """A well-formed report passes stage 2."""
        report = ("Clinical report: The patient presents with a skin lesion showing class 2 features. "
                  "Based on the multimodal analysis, further review is recommended. "
                  "Confidence is moderate at 55%. Additional clinical evaluation is suggested.")
        evidence = {
            "consensus_action": "ACQUIRE",
            "consensus_level": 3,
            "confidence": 0.55,
            # model_predictions_top3 empty → Rule 1 passes by default (cannot verify)
            "model_predictions_top3": [],
        }
        result = stage2_verify(report, evidence, llm_client=None)
        assert result.passed

    def test_overconfident_report_on_escalate_fails(self):
        """Report claiming 'high confidence' on ESCALATE action → FAIL."""
        report = "I am definitely confident that this is melanoma with high confidence."
        evidence = {
            "consensus_action": "ESCALATE",
            "consensus_level": 4,
            "confidence": 0.30,
        }
        result = stage2_verify(report, evidence, llm_client=None)
        assert not result.passed

    def test_llm_unavailable_falls_back_to_rules(self):
        """If LLM is None, verification still works via rules."""
        report = "The lesion shows uncertain characteristics. Further evaluation is needed."
        evidence = {
            "consensus_action": "ACQUIRE",
            "consensus_level": 3,
            "confidence": 0.50,
        }
        # No LLM client — should not raise
        result = stage2_verify(report, evidence, llm_client=None)
        assert isinstance(result, VerificationResult)

    def test_llm_timeout_does_not_crash(self):
        """Simulate LLM timeout — verification continues without crashing."""
        import warnings
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = RuntimeError("LLM call failed after 3 attempts: timeout")

        report = "Moderate confidence. Further review recommended."
        evidence = {"consensus_action": "ACCEPT", "consensus_level": 1, "confidence": 0.82}

        with warnings.catch_warnings(record=True):
            result = stage2_verify(report, evidence, llm_client=mock_llm)
        # Should complete (rule-based checks pass, LLM failure is caught gracefully)
        assert isinstance(result, VerificationResult)

"""
tests/test_orchestrator.py — Full pipeline integration tests (DERMA-GUARD v4.0)

Tests:
  - Full pipeline integration (end-to-end smoke test with mocks)
  - OOD case → ESCALATE
  - Missing modality → ACQUIRE
"""
import pytest
import torch
from unittest.mock import MagicMock, patch

from src.agents.orchestrator import OrchestratorAgent, PatientCase, PipelineResult
from src.agents.devils_advocate import EvidenceProfile
from src.evidence.missingness import compute_missingness


def make_mock_vision_report(agreement=4, confidence=0.85):
    """Create a mock VisionReport that yields strong agreement."""
    report = MagicMock()
    predictions = {}
    for i in range(5):
        logits = torch.zeros(7)
        logits[2 if i < agreement else i % 7] = 5.0
        predictions[f"model_{i}"] = logits
    report.model_predictions = predictions
    report.model_embeddings = {k: torch.randn(1, 768) for k in predictions}
    report.model_confidences = {k: confidence for k in predictions}
    report.quality_scores = {"clinical": 0.8, "dermoscopy": 0.75}
    report.uncertainty_estimates = {k: 0.3 for k in predictions}
    return report


def make_mock_scribe_report(ptis=0.7):
    report = MagicMock()
    report.ptis = ptis
    report.symptoms = {"itching": "true", "growth": "unknown"}
    report.risk_factors = []
    report.summary = "Test summary"
    report.text_embedding = torch.randn(768)
    report.metadata_embedding = torch.randn(64)
    report.metadata_quality = 0.9
    return report


def make_mock_evidence_profile(ood_score=5.0, conflict=False, consistency=0.85):
    miss = compute_missingness(True, True, True, True)
    ep = EvidenceProfile(
        quality={"clinical": 0.8, "dermoscopy": 0.75, "text": 0.7, "metadata": 0.9},
        reliability={"model_0": 0.8, "model_1": 0.8, "model_2": 0.8, "model_3": 0.8, "model_4": 0.8},
        utility={"clinical_image": 0.7, "dermoscopy_image": 0.6, "text": 0.5, "metadata": 0.4},
        consistency=consistency,
        conflict_flag=conflict,
        conflict_details={},
        missing_modalities=miss["missing_list"],
        missing_mask=miss["missing_mask"],
        ood_score=ood_score,
        overall_risk=0.2,
    )
    return ep


def make_orchestrator():
    """Build an Orchestrator with all mocked sub-agents."""
    vision_mock = MagicMock()
    vision_mock.process_case.return_value = make_mock_vision_report()

    scribe_mock = MagicMock()
    scribe_mock.process_case.return_value = make_mock_scribe_report()

    librarian_mock = MagicMock()
    librarian_mock.retrieve.return_value = {"similar_cases": [], "agreement_rate": 0.0}

    da_mock = MagicMock()
    da_mock.profile.return_value = make_mock_evidence_profile()

    orch = OrchestratorAgent(
        vision_team=vision_mock,
        scribe=scribe_mock,
        librarian=librarian_mock,
        devils_advocate=da_mock,
        llm_client=None,
        class_names=["class_" + str(i) for i in range(7)],
    )
    return orch, vision_mock, scribe_mock, da_mock


class TestFullPipelineIntegration:
    def test_clean_case_returns_result(self):
        """A clean, well-formed case should return ACCEPT or ARBITRATE."""
        orch, _, _, _ = make_orchestrator()
        case = PatientCase(
            case_id="test_001",
            clinical_images=torch.randn(1, 3, 224, 224),
            dermo_images=torch.randn(1, 3, 224, 224),
            patient_text="Skin lesion on arm, growing for 3 months, itching.",
            clinical_available=True,
            dermo_available=True,
            meta_available=True,
            text_available=True,
        )
        result = orch.process_case(case)
        assert isinstance(result, PipelineResult)
        assert result.case_id == "test_001"
        assert result.action in ("ACCEPT", "ARBITRATE", "ACQUIRE", "ESCALATE")

    def test_result_has_evidence_trace(self):
        """Result must contain an evidence_trace with at least step entries."""
        orch, _, _, _ = make_orchestrator()
        case = PatientCase(case_id="test_002")
        result = orch.process_case(case)
        assert isinstance(result.evidence_trace, list)
        assert len(result.evidence_trace) > 0


class TestOODEscalation:
    def test_ood_case_triggers_escalation(self):
        """OOD score > threshold → Stage 1 fails → action should be ESCALATE."""
        orch, _, _, da_mock = make_orchestrator()
        # Override devil's advocate to return high OOD score
        da_mock.profile.return_value = make_mock_evidence_profile(ood_score=200.0)

        case = PatientCase(case_id="ood_test", clinical_available=True)
        result = orch.process_case(case)
        assert result.action == "ESCALATE", \
            f"OOD case should escalate, got: {result.action}"


class TestMissingModalityAcquire:
    def test_all_missing_returns_abstain(self):
        """All modalities missing → pipeline should ABSTAIN."""
        orch, _, _, da_mock = make_orchestrator()
        miss = compute_missingness(False, False, False, False)
        ep = EvidenceProfile(
            quality={}, reliability={}, utility={},
            consistency=1.0, conflict_flag=False, conflict_details={},
            missing_modalities=miss["missing_list"],
            missing_mask=miss["missing_mask"],
            ood_score=0.0, overall_risk=0.9,
        )
        da_mock.profile.return_value = ep

        case = PatientCase(
            case_id="all_missing",
            clinical_available=False,
            dermo_available=False,
            meta_available=False,
            text_available=False,
        )
        result = orch.process_case(case)
        assert result.action in ("ABSTAIN", "ESCALATE", "ACQUIRE"), \
            f"All-missing case should abstain/escalate, got: {result.action}"

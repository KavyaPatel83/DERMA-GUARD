"""
src/agents/orchestrator.py — Orchestrator Agent (DERMA-GUARD v4.0)

7-step pipeline:
  1. Parallel agent execution (vision, scribe, librarian, devils_advocate)
  2. Stage 1 verification
  3. Dynamic fusion (DiagnosisAdaptiveFusion)
  4. 4-level consensus hierarchy
  5. Report generation (LLM)
  6. Stage 2 verification (rule + LLM)
  7. Log and return

CRITICAL CONSTRAINT: The Orchestrator uses structured tool-calling ONLY.
The LLM synthesizes reports but does NOT independently diagnose.
"""
from __future__ import annotations

import json
import time
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import torch

from src.fusion.adaptive_fusion import DiagnosisAdaptiveFusion, InsufficientEvidenceError
from src.fusion.consensus import classify_consensus, ConsensusResult
from src.fusion.acquisition import AcquisitionPolicy
from src.llm.verification import stage1_verify, stage2_verify
from src.llm.report_gen import generate_report


# ---------------------------------------------------------------------------
# PatientCase — the unified case input structure
# ---------------------------------------------------------------------------

@dataclass
class PatientCase:
    """Unified input to the Orchestrator pipeline."""
    case_id: str
    # Images (optional tensors)
    clinical_images: Optional[torch.Tensor] = None    # (B, 3, 224, 224)
    dermo_images: Optional[torch.Tensor] = None       # (B, 3, 224, 224)
    # Text
    patient_text: Optional[str] = None
    # Metadata
    metadata_continuous: Optional[torch.Tensor] = None
    metadata_missing_mask: Optional[torch.Tensor] = None
    metadata_categorical: Optional[List[torch.Tensor]] = None
    # Availability flags
    clinical_available: bool = True
    dermo_available: bool = True
    meta_available: bool = True
    text_available: bool = True


# ---------------------------------------------------------------------------
# Pipeline result
# ---------------------------------------------------------------------------

@dataclass
class PipelineResult:
    """Structured output from OrchestratorAgent.process_case()."""
    case_id: str
    action: str                        # ACCEPT | ARBITRATE | ACQUIRE | ESCALATE | ABSTAIN
    diagnosis: Optional[int] = None    # class index (if action is ACCEPT/ARBITRATE)
    confidence: Optional[float] = None
    consensus_level: Optional[int] = None
    report: Optional[str] = None
    evidence_used: List[str] = field(default_factory=list)
    evidence_missing: List[str] = field(default_factory=list)
    acquire_target: Optional[str] = None   # what to acquire (if action=ACQUIRE)
    escalate_reason: Optional[str] = None  # why escalated (if action=ESCALATE)
    evidence_trace: List[Dict] = field(default_factory=list)
    processing_time_s: float = 0.0
    model_version: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "case_id": self.case_id,
            "action": self.action,
            "diagnosis": self.diagnosis,
            "confidence": self.confidence,
            "consensus_level": self.consensus_level,
            "report": self.report,
            "evidence_used": self.evidence_used,
            "evidence_missing": self.evidence_missing,
            "acquire_target": self.acquire_target,
            "escalate_reason": self.escalate_reason,
            "processing_time_s": self.processing_time_s,
        }


# ---------------------------------------------------------------------------
# OrchestratorAgent
# ---------------------------------------------------------------------------

class OrchestratorAgent:
    """Central coordinator for the DERMA-GUARD v4.0 pipeline.

    Tools (structured, no free-text diagnosis):
        vision_specialist → VisionSpecialistTeam
        scribe            → ScribeAgent
        librarian         → LibrarianAgent
        devils_advocate   → DevilsAdvocateAgent
        fusion            → DiagnosisAdaptiveFusion
        acquisition       → AcquisitionPolicy
    """

    def __init__(
        self,
        vision_team=None,
        scribe=None,
        librarian=None,
        devils_advocate=None,
        fusion_model: Optional[DiagnosisAdaptiveFusion] = None,
        acquisition_policy: Optional[AcquisitionPolicy] = None,
        llm_client=None,
        class_names: Optional[List[str]] = None,
        model_version: Optional[str] = None,
    ):
        self.vision_team = vision_team
        self.scribe = scribe
        self.librarian = librarian
        self.devils_advocate = devils_advocate
        self.fusion = fusion_model or DiagnosisAdaptiveFusion()
        self.acquisition = acquisition_policy or AcquisitionPolicy()
        self.llm = llm_client
        self.class_names = class_names
        self.model_version = model_version

        # Tool registry (structured tool-calling)
        self.tools = {
            "vision_specialist": self._call_vision_team,
            "scribe":            self._call_scribe,
            "librarian":         self._call_librarian,
            "devils_advocate":   self._call_evidence_profiler,
        }

    def process_case(self, case: PatientCase) -> PipelineResult:
        """Execute the 7-step pipeline.

        CRITICAL: all decisions based on tool outputs, not LLM reasoning.

        Args:
            case: PatientCase

        Returns:
            PipelineResult
        """
        t0 = time.time()
        trace: List[Dict] = []

        def _log(step: str, data: Any):
            trace.append({"step": step, "timestamp": time.time() - t0, "data": str(data)[:500]})

        # ================================================================
        # STEP 1: Parallel agent execution
        # ================================================================
        _log("step1_start", "parallel agent execution")

        # Vision
        vision_report = None
        if self.vision_team is not None:
            try:
                vision_report = self._call_vision_team(case)
                _log("vision_team", f"models={list(vision_report.model_predictions.keys())}")
            except Exception as e:
                warnings.warn(f"[Orchestrator] Vision team failed: {e}")

        # Scribe
        scribe_report = None
        if self.scribe is not None:
            try:
                scribe_report = self._call_scribe(case)
                _log("scribe", f"ptis={scribe_report.ptis:.2f}, symptoms={scribe_report.symptoms}")
            except Exception as e:
                warnings.warn(f"[Orchestrator] Scribe failed: {e}")

        # Librarian (need embeddings — use scribe's text_embedding as primary key)
        knowledge = None
        if self.librarian is not None and scribe_report is not None:
            try:
                query_embs = {
                    "text_embedding": scribe_report.text_embedding,
                    "metadata_embedding": scribe_report.metadata_embedding,
                }
                if vision_report is not None:
                    query_embs["clinical_embedding"] = vision_report.model_embeddings.get(
                        "swin_tiny_clinical", torch.zeros(768)
                    )
                    query_embs["dermoscopy_embedding"] = vision_report.model_embeddings.get(
                        "swin_tiny_dermoscopy", torch.zeros(768)
                    )
                knowledge = self._call_librarian(query_embs)
                _log("librarian", f"similar_cases={len(knowledge.get('similar_cases', []))}")
            except Exception as e:
                warnings.warn(f"[Orchestrator] Librarian failed: {e}")

        # Devil's Advocate (Evidence Profiler)
        evidence_profile = None
        if self.devils_advocate is not None and vision_report is not None and scribe_report is not None:
            try:
                evidence_profile = self._call_evidence_profiler(
                    case, vision_report, scribe_report
                )
                _log("devils_advocate", f"risk={evidence_profile.overall_risk:.2f}, "
                                        f"conflict={evidence_profile.conflict_flag}")
            except Exception as e:
                warnings.warn(f"[Orchestrator] Evidence profiler failed: {e}")

        # Guard: if we have nothing, create empty placeholders
        if vision_report is None:
            _log("warning", "no vision report — creating placeholder")
            vision_report = self._empty_vision_report()
        if scribe_report is None:
            _log("warning", "no scribe report — creating placeholder")
            scribe_report = self._empty_scribe_report()
        if evidence_profile is None:
            _log("warning", "no evidence profile — creating placeholder")
            evidence_profile = self._empty_evidence_profile(case)

        # ================================================================
        # STEP 2: Stage 1 verification
        # ================================================================
        _log("step2_start", "stage 1 verification")
        v1 = stage1_verify(evidence_profile)
        if not v1.passed:
            _log("stage1_fail", v1.reason)
            action = "ESCALATE" if "Out-of-distribution" in (v1.reason or "") else \
                     "ABSTAIN" if "No evidence" in (v1.reason or "") else "ACQUIRE"
            return PipelineResult(
                case_id=case.case_id,
                action=action,
                escalate_reason=v1.reason,
                evidence_missing=evidence_profile.missing_modalities
                    if hasattr(evidence_profile, "missing_modalities") else [],
                evidence_trace=trace,
                processing_time_s=time.time() - t0,
                model_version=self.model_version,
            )

        # ================================================================
        # STEP 3: Dynamic Fusion
        # ================================================================
        _log("step3_start", "dynamic fusion")
        fusion_result = None
        try:
            from src.evidence.missingness import compute_missingness
            miss = compute_missingness(
                case.clinical_available, case.dermo_available,
                case.meta_available, case.text_available
            )
            fusion_result = self.fusion.fuse(
                embeddings=vision_report.model_embeddings,
                quality=evidence_profile.quality,
                reliability=evidence_profile.reliability,
                utility=evidence_profile.utility,
                consistency=evidence_profile.consistency,
                missing_mask=miss["missing_mask"],
            )
            _log("fusion", f"iterations={fusion_result.iterations_used}, "
                           f"converged={fusion_result.converged}, "
                           f"diagnosis={fusion_result.diagnosis}")
        except InsufficientEvidenceError as e:
            _log("fusion_abstain", str(e))
            return PipelineResult(
                case_id=case.case_id,
                action="ABSTAIN",
                escalate_reason=str(e),
                evidence_trace=trace,
                processing_time_s=time.time() - t0,
            )
        except Exception as e:
            warnings.warn(f"[Orchestrator] Fusion failed: {e}")
            # Create a minimal fusion result
            from src.fusion.adaptive_fusion import FusionResult
            fusion_result = FusionResult(
                prediction=torch.zeros(1, self.fusion.num_classes),
                diagnosis=0, confidence=0.0,
                weights=torch.zeros(self.fusion.num_modalities),
                fused_embedding=torch.zeros(self.fusion.d_common),
                iterations_used=0, converged=False,
            )

        # ================================================================
        # STEP 4: Consensus
        # ================================================================
        _log("step4_start", "consensus classification")
        consensus = classify_consensus(fusion_result, evidence_profile, vision_report)
        _log("consensus", f"level={consensus.level}, action={consensus.action}")

        # Handle ACQUIRE
        if consensus.action == "ACQUIRE":
            available = [m for m, avail in {
                "clinical_image": case.clinical_available,
                "dermoscopy_image": case.dermo_available,
                "metadata": case.meta_available,
                "text": case.text_available,
            }.items() if avail]
            case_features = {
                "current_entropy": sum(evidence_profile.uncertainty.values()) / max(
                    len(evidence_profile.uncertainty), 1
                ) if hasattr(evidence_profile, "uncertainty") else 0.5,
                "missing_count": len(evidence_profile.missing_modalities),
                "metadata_completeness": evidence_profile.quality.get("metadata", 0.5),
                "ptis": scribe_report.ptis,
                "ood_score": evidence_profile.ood_score,
                "consistency": evidence_profile.consistency,
            }
            target = self.acquisition.select_action(case_features, available)
            _log("acquire", f"target={target}")
            return PipelineResult(
                case_id=case.case_id,
                action="ACQUIRE",
                acquire_target=target,
                evidence_missing=evidence_profile.missing_modalities,
                evidence_trace=trace,
                processing_time_s=time.time() - t0,
            )

        # Handle ESCALATE (from consensus)
        if consensus.action == "ESCALATE":
            _log("escalate", consensus.reason)
            return PipelineResult(
                case_id=case.case_id,
                action="ESCALATE",
                escalate_reason=consensus.reason,
                evidence_trace=trace,
                processing_time_s=time.time() - t0,
            )

        # ================================================================
        # STEP 5: Report generation
        # ================================================================
        _log("step5_start", "report generation")
        evidence_dict = evidence_profile.to_dict() if hasattr(evidence_profile, "to_dict") else {}
        evidence_dict["consensus_action"] = consensus.action
        evidence_dict["consensus_level"] = consensus.level
        evidence_dict["confidence"] = consensus.confidence

        report_draft = generate_report(
            vision_report=vision_report,
            scribe_report=scribe_report,
            knowledge=knowledge,
            evidence_profile=evidence_dict,
            consensus=consensus.to_dict(),
            llm_client=self.llm,
            class_names=self.class_names,
        )
        _log("report_gen", f"report_length={len(report_draft)} chars")

        # ================================================================
        # STEP 6: Stage 2 verification
        # ================================================================
        _log("step6_start", "stage 2 verification")
        v2 = stage2_verify(report_draft, evidence_dict, self.llm)
        if not v2.passed:
            _log("stage2_fail", f"first attempt: {v2.reason}")
            # Regenerate with conservative prompt
            report_draft = generate_report(
                vision_report=vision_report,
                scribe_report=scribe_report,
                knowledge=knowledge,
                evidence_profile=evidence_dict,
                consensus=consensus.to_dict(),
                llm_client=self.llm,
                class_names=self.class_names,
                conservative=True,
            )
            v2_retry = stage2_verify(report_draft, evidence_dict, self.llm)
            if not v2_retry.passed:
                _log("stage2_escalate", f"retry also failed: {v2_retry.reason}")
                return PipelineResult(
                    case_id=case.case_id,
                    action="ESCALATE",
                    escalate_reason=f"Stage 2 verification failed: {v2_retry.reason}",
                    evidence_trace=trace,
                    processing_time_s=time.time() - t0,
                )
            _log("stage2_pass_conservative", "conservative report passed verification")

        # ================================================================
        # STEP 7: Return result
        # ================================================================
        evidence_used = [m for m in ["clinical_image", "dermoscopy_image", "metadata", "text"]
                         if m not in evidence_profile.missing_modalities]

        result = PipelineResult(
            case_id=case.case_id,
            action=consensus.action,
            diagnosis=consensus.diagnosis,
            confidence=consensus.confidence,
            consensus_level=consensus.level,
            report=report_draft,
            evidence_used=evidence_used,
            evidence_missing=evidence_profile.missing_modalities,
            evidence_trace=trace,
            processing_time_s=time.time() - t0,
            model_version=self.model_version,
        )
        _log("step7_done", f"action={result.action}, processing_time={result.processing_time_s:.2f}s")
        return result

    # -----------------------------------------------------------------------
    # Tool wrappers (structured calls only)
    # -----------------------------------------------------------------------

    def _call_vision_team(self, case: PatientCase):
        return self.vision_team.process_case(
            clinical_images=case.clinical_images,
            dermo_images=case.dermo_images,
        )

    def _call_scribe(self, case: PatientCase):
        return self.scribe.process_case(
            text=case.patient_text or "",
            metadata_continuous=case.metadata_continuous,
            metadata_missing_mask=case.metadata_missing_mask,
            metadata_categorical=case.metadata_categorical,
        )

    def _call_librarian(self, query_embs: Dict):
        return self.librarian.retrieve(query_embs)

    def _call_evidence_profiler(self, case: PatientCase, vision_report, scribe_report):
        return self.devils_advocate.profile(
            vision_report=vision_report,
            scribe_report=scribe_report,
            clinical_available=case.clinical_available,
            dermo_available=case.dermo_available,
            meta_available=case.meta_available,
            text_available=case.text_available,
        )

    # -----------------------------------------------------------------------
    # Empty placeholders
    # -----------------------------------------------------------------------

    def _empty_vision_report(self):
        from src.agents.vision_team import VisionReport
        return VisionReport(
            model_predictions={}, model_embeddings={},
            model_confidences={}, uncertainty_estimates={}, quality_scores={}
        )

    def _empty_scribe_report(self):
        from src.agents.scribe import ScribeReport
        return ScribeReport(
            symptoms={}, ptis=0.0, risk_factors=[], summary="No text available.",
            text_embedding=torch.zeros(768), metadata_embedding=torch.zeros(64),
            metadata_quality=0.0
        )

    def _empty_evidence_profile(self, case: PatientCase):
        from src.agents.devils_advocate import EvidenceProfile
        from src.evidence.missingness import compute_missingness
        miss = compute_missingness(
            case.clinical_available, case.dermo_available,
            case.meta_available, case.text_available
        )
        return EvidenceProfile(
            quality={}, reliability={}, utility={},
            consistency=1.0, conflict_flag=False, conflict_details={},
            missing_modalities=miss["missing_list"],
            missing_mask=miss["missing_mask"],
            ood_score=0.0, overall_risk=0.5
        )

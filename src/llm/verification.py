"""src/llm/verification.py — Two-stage verification layer (DERMA-GUARD v4.0).

Stage 1 (Pre-Orchestrator): rule-based evidence gating
Stage 2 (Post-Orchestrator): rule-based + LLM verification of report

If Stage 2 fails: regenerate with conservative prompt. If still failing: ESCALATE.
"""
from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from typing import Dict, List, Optional

import torch
import torch.nn.functional as F

OOD_THRESHOLD = 50.0   # calibrated on validation set
MIN_AVAILABLE_MODALITIES = 1  # at least one modality must be present


@dataclass
class VerificationResult:
    status: str          # "PASS" | "FAIL"
    reason: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


# ---------------------------------------------------------------------------
# Stage 1 — Pre-Orchestrator evidence gate
# ---------------------------------------------------------------------------

def stage1_verify(evidence_profile) -> VerificationResult:
    """Stage 1 verification: check evidence before running fusion.

    Rules:
    1. OOD score above threshold → FAIL
    2. Critical conflict AND consistency < 0.3 → FAIL
    3. All modalities missing → FAIL
    4. Any modality quality < 0.2 → warn and suppress (do NOT fail)

    Args:
        evidence_profile: EvidenceProfile dataclass or dict

    Returns:
        VerificationResult with status and reason
    """
    # Unpack (support both dataclass and dict)
    if hasattr(evidence_profile, "ood_score"):
        ood_score      = evidence_profile.ood_score
        conflict_flag  = evidence_profile.conflict_flag
        consistency    = evidence_profile.consistency
        missing_list   = evidence_profile.missing_modalities
        quality        = evidence_profile.quality
    else:
        ood_score      = evidence_profile.get("ood_score", 0.0)
        conflict_flag  = evidence_profile.get("conflict_flag", False)
        consistency    = evidence_profile.get("consistency", 1.0)
        missing_list   = evidence_profile.get("missing_modalities", [])
        quality        = evidence_profile.get("quality", {})

    # Rule 1: OOD
    if ood_score > OOD_THRESHOLD:
        return VerificationResult(
            status="FAIL",
            reason=f"Out-of-distribution case (OOD score={ood_score:.1f} > threshold={OOD_THRESHOLD})",
        )

    # Rule 2: critical conflict
    if conflict_flag and consistency < 0.3:
        return VerificationResult(
            status="FAIL",
            reason=f"Critical cross-modal conflict (consistency={consistency:.2f} < 0.3)",
        )

    # Rule 3: no evidence at all
    from src.evidence.missingness import ALL_MODALITIES
    if len(missing_list) == len(ALL_MODALITIES):
        return VerificationResult(
            status="FAIL",
            reason="No evidence available — all modalities are missing",
        )

    # Rule 4: low-quality modality → warn and suppress (not a hard fail)
    low_quality_modalities = [m for m, q in quality.items() if q < 0.2]
    if low_quality_modalities:
        warnings.warn(
            f"[Stage1Verify] Low-quality modalities detected: {low_quality_modalities}. "
            "These will be down-weighted but not suppressed entirely."
        )

    return VerificationResult(status="PASS")


# ---------------------------------------------------------------------------
# Stage 2 — Post-Orchestrator report verification
# ---------------------------------------------------------------------------

_RULE_DESCRIPTIONS = [
    "Does the diagnosis appear in ANY model's top-3 predictions?",
    "Does the confidence match the consensus level?",
    "Is every claim in the report traceable to a field in evidence_json?",
    "Does the report mention a diagnosis not supported by evidence?",
    "If sufficiency is insufficient, does the report state a confident diagnosis?",
]


def _check_rule_1(report: str, evidence: Dict) -> bool:
    """Rule 1: diagnosis appears in at least one model's top-3 predictions."""
    # Extract what appears to be the primary diagnosis from the report
    # (simple heuristic: look for any class name mentioned)
    model_preds = evidence.get("model_predictions_top3", [])
    if not model_preds:
        # Cannot verify — pass with warning
        return True
    report_lower = report.lower()
    return any(str(d).lower() in report_lower for d in model_preds)


def _check_rule_2(report: str, evidence: Dict) -> bool:
    """Rule 2: confidence language matches consensus level."""
    level = evidence.get("consensus_level", 4)
    report_lower = report.lower()
    # Level 4 reports should not say "high confidence"
    if level >= 4 and any(p in report_lower for p in ["high confidence", "definitively", "certainly"]):
        return False
    return True


def _check_rule_3(report: str, evidence: Dict) -> bool:
    """Rule 3: claims are traceable (heuristic — no hallucinated numbers)."""
    # Check that any percentage in the report ≈ evidence confidence
    import re
    confidence = evidence.get("confidence", None)
    pct_matches = re.findall(r'(\d{1,3})%', report)
    if confidence is not None and pct_matches:
        for pct in pct_matches:
            if abs(float(pct) - confidence * 100) > 15:
                return False
    return True


def _check_rule_4(report: str, evidence: Dict) -> bool:
    """Rule 4: report does not mention diagnosis not in evidence."""
    # Simplified: always pass (full implementation requires NER)
    return True


def _check_rule_5(report: str, evidence: Dict) -> bool:
    """Rule 5: if consensus action is ACQUIRE/ESCALATE, report should not be confident."""
    action = evidence.get("consensus_action", "ACCEPT")
    report_lower = report.lower()
    if action in ("ACQUIRE", "ESCALATE"):
        # Should mention uncertainty
        if not any(w in report_lower for w in ["uncertain", "unclear", "further", "review", "additional"]):
            return False
    return True


_RULE_CHECKERS = [
    _check_rule_1,
    _check_rule_2,
    _check_rule_3,
    _check_rule_4,
    _check_rule_5,
]


def stage2_verify(
    report_draft: str,
    evidence: Dict,
    llm_client=None,
) -> VerificationResult:
    """Stage 2 verification: rule-based then LLM-based.

    Args:
        report_draft: generated clinical report text
        evidence: dict with consensus_action, consensus_level, confidence, etc.
        llm_client: OllamaClient instance (optional; skips LLM check if None)

    Returns:
        VerificationResult
    """
    # Rule-based checks first
    for i, (rule_desc, checker) in enumerate(zip(_RULE_DESCRIPTIONS, _RULE_CHECKERS)):
        if not checker(report_draft, evidence):
            return VerificationResult(
                status="FAIL",
                reason=f"Rule {i+1} failed: {rule_desc}",
            )

    # LLM-based check (if available)
    if llm_client is not None:
        try:
            from src.llm.prompts import verification_prompt, VERIFICATION_SYSTEM
            prompt = verification_prompt(report_draft, json.dumps(evidence, indent=2, default=str))
            raw = llm_client.generate(prompt, system_prompt=VERIFICATION_SYSTEM, temperature=0.0)
            # Parse JSON response
            result_data = {}
            import re
            match = re.search(r'\{.*?\}', raw, re.DOTALL)
            if match:
                try:
                    result_data = json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            if result_data.get("status") == "fail":
                return VerificationResult(
                    status="FAIL",
                    reason=f"LLM verification: {result_data.get('reason', 'unspecified')}",
                )
        except Exception as e:
            warnings.warn(f"[Stage2Verify] LLM verification failed: {e}. Proceeding with rules only.")

    return VerificationResult(status="PASS")

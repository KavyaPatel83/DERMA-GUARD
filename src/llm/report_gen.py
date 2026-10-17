"""src/llm/report_gen.py — Clinical report generation from evidence bundle."""
from __future__ import annotations

import json
import warnings
from typing import Dict, List, Optional

from src.llm.prompts import (
    REPORT_GEN_SYSTEM, synthesis_prompt,
    CONSERVATIVE_REPORT_PROMPT, conservative_prompt,
)


def generate_report(
    vision_report: Dict,
    scribe_report: Dict,
    knowledge: Optional[Dict],
    evidence_profile: Dict,
    consensus: Dict,
    llm_client=None,
    class_names: Optional[List[str]] = None,
    conservative: bool = False,
) -> str:
    """Generate a clinical report from the evidence bundle.

    Args:
        vision_report:    VisionReport dict or dataclass
        scribe_report:    ScribeReport dict or dataclass
        knowledge:        RAG retrieval result dict
        evidence_profile: EvidenceProfile dict
        consensus:        ConsensusResult dict
        llm_client:       OllamaClient instance
        class_names:      list of class name strings
        conservative:     if True, use conservative prompt

    Returns:
        Report text string
    """
    # Convert dataclasses to dicts for prompt building
    def _to_dict(obj):
        if hasattr(obj, "__dataclass_fields__"):
            import dataclasses
            d = dataclasses.asdict(obj)
            # Convert tensors
            for k, v in d.items():
                if hasattr(v, "tolist"):
                    d[k] = v.tolist()
            return d
        return obj if isinstance(obj, dict) else {}

    vr = _to_dict(vision_report)
    sr = _to_dict(scribe_report)
    ep = _to_dict(evidence_profile)
    cr = _to_dict(consensus)

    if llm_client is None:
        return _fallback_report(cr, ep, sr)

    if conservative:
        evidence_json = json.dumps(ep, indent=2, default=str)
        try:
            return llm_client.generate(
                conservative_prompt(evidence_json),
                system_prompt=CONSERVATIVE_REPORT_PROMPT,
                temperature=0.0,
            )
        except Exception as e:
            warnings.warn(f"[ReportGen] Conservative report generation failed: {e}")
            return _fallback_report(cr, ep, sr)

    prompt = synthesis_prompt(vr, sr, knowledge, ep, cr, class_names=class_names)
    try:
        return llm_client.generate(prompt, system_prompt=REPORT_GEN_SYSTEM, temperature=0.0)
    except Exception as e:
        warnings.warn(f"[ReportGen] Report generation failed: {e}. Using fallback.")
        return _fallback_report(cr, ep, sr)


def _fallback_report(consensus: Dict, evidence: Dict, scribe: Dict) -> str:
    """Generate a minimal factual report without LLM."""
    action = consensus.get("action", "ESCALATE")
    diag = consensus.get("diagnosis", "unknown")
    conf = consensus.get("confidence", 0.0)
    missing = evidence.get("missing_modalities", [])

    lines = [
        f"DERMA-GUARD v4.0 — Automated Report",
        f"Consensus Action: {action}",
    ]
    if action in ("ACCEPT", "ARBITRATE"):
        lines.append(f"Predicted Diagnosis: Class {diag} (confidence: {conf:.1%})")
    if missing:
        lines.append(f"Missing Data: {', '.join(missing)}")
    lines.append("Note: LLM report generation was unavailable. Please review evidence manually.")
    return "\n".join(lines)

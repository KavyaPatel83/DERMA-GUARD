"""src/llm/prompts.py — All structured prompts for DERMA-GUARD v4.0."""
from __future__ import annotations

from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Symptom extraction
# ---------------------------------------------------------------------------

SYMPTOM_EXTRACTION_SYSTEM = (
    "You are a clinical symptom extractor. Extract structured information from "
    "patient descriptions. If a symptom is not mentioned, output 'unknown'. "
    "Never output 'false' for something not stated. Return valid JSON only."
)

def symptom_extraction_prompt(text: str) -> str:
    return (
        f"Extract the following clinical fields from the patient description.\n\n"
        f"Fields and allowed values:\n"
        f"  duration: 'short' | 'long' | 'unknown'  (short = <3 months, long = >=3 months)\n"
        f"  growth: 'true' | 'false' | 'unknown'\n"
        f"  color_change: 'true' | 'false' | 'unknown'\n"
        f"  itching: 'true' | 'false' | 'unknown'\n"
        f"  pain: 'true' | 'false' | 'unknown'\n"
        f"  bleeding: 'true' | 'false' | 'unknown'\n\n"
        f"Patient description:\n{text}\n\n"
        f"Output ONLY a JSON object with these six fields."
    )


# ---------------------------------------------------------------------------
# Follow-up question generation
# ---------------------------------------------------------------------------

QUESTION_GEN_SYSTEM = (
    "You are a clinical assistant. Generate a single, clear, patient-friendly question "
    "to gather missing clinical information. Output only the question, nothing else."
)

def question_generation_prompt(missing_field: str, expected_value: str = "") -> str:
    return (
        f"Generate a question to ask the patient about: {missing_field}\n"
        f"Expected response type: {expected_value or 'yes/no or brief description'}\n"
        f"Make it simple, friendly, and non-medical in language.\n"
        f"Output: ONLY the question."
    )


# ---------------------------------------------------------------------------
# Report synthesis
# ---------------------------------------------------------------------------

REPORT_GEN_SYSTEM = (
    "You are a clinical report writer for a dermatology AI system. "
    "Write a concise, factual report based ONLY on the provided evidence. "
    "Do NOT infer or speculate beyond the evidence. "
    "Always include uncertainty acknowledgement if evidence is incomplete."
)

def synthesis_prompt(
    vision: Dict,
    scribe: Dict,
    knowledge: Optional[Dict],
    evidence: Dict,
    consensus: Dict,
    class_names: Optional[List[str]] = None,
) -> str:
    diag_id = consensus.get("diagnosis")
    diag_name = class_names[diag_id] if class_names and diag_id is not None else str(diag_id)
    confidence = consensus.get("confidence", 0.0)
    level = consensus.get("level", 4)
    action = consensus.get("action", "ESCALATE")

    # Summarize evidence
    quality_str = ", ".join(f"{k}={v:.2f}" for k, v in evidence.get("quality", {}).items())
    missing = evidence.get("missing_modalities", [])
    consistency = evidence.get("consistency", 1.0)
    conflict = evidence.get("conflict_flag", False)

    symptoms = scribe.get("symptoms", {})
    symptom_str = "; ".join(f"{k}: {v}" for k, v in symptoms.items() if v != "unknown")
    ptis = scribe.get("ptis", 0.0)

    similar_cases = ""
    if knowledge and knowledge.get("similar_cases"):
        agreement = knowledge.get("agreement_rate", 0.0)
        similar_cases = f"Similar cases from database: agreement rate = {agreement:.2%}"

    return (
        f"Write a clinical report for a skin lesion case.\n\n"
        f"EVIDENCE:\n"
        f"  Predicted diagnosis: {diag_name}\n"
        f"  Fusion confidence: {confidence:.2%}\n"
        f"  Consensus level: {level} ({action})\n"
        f"  Evidence quality: {quality_str}\n"
        f"  Consistency across modalities: {consistency:.2f}\n"
        f"  Conflict detected: {conflict}\n"
        f"  Missing modalities: {', '.join(missing) or 'none'}\n"
        f"  Patient symptoms: {symptom_str or 'not reported'}\n"
        f"  Text informativeness (PTIS): {ptis:.2f}\n"
        f"  {similar_cases}\n\n"
        f"INSTRUCTIONS:\n"
        f"  - State the diagnosis and confidence level.\n"
        f"  - Note which evidence modalities were used.\n"
        f"  - Acknowledge any missing evidence.\n"
        f"  - If confidence is below 80%, explicitly state uncertainty.\n"
        f"  - Recommend next steps (follow-up, biopsy, monitor, etc.).\n"
        f"  - Keep the report under 200 words.\n\n"
        f"Report:"
    )


CONSERVATIVE_REPORT_PROMPT = (
    "Write a conservative, factual clinical report. "
    "State only what is directly supported by the evidence. "
    "Do not mention any diagnosis not supported by at least one model's top-3 predictions. "
    "Explicitly acknowledge uncertainty and recommend clinical review."
)

def conservative_prompt(evidence_json: str) -> str:
    return (
        f"{CONSERVATIVE_REPORT_PROMPT}\n\n"
        f"Evidence:\n{evidence_json}\n\n"
        f"Conservative Report:"
    )


# ---------------------------------------------------------------------------
# Stage 2 verification prompt
# ---------------------------------------------------------------------------

VERIFICATION_SYSTEM = (
    "You are a clinical AI safety checker. "
    "Verify whether a generated report is consistent with the provided evidence. "
    "Return valid JSON with keys: status ('pass'|'fail'), reason (string if fail)."
)

def verification_prompt(report_draft: str, evidence_json: str) -> str:
    return (
        f"Check this report against the evidence.\n\n"
        f"REPORT:\n{report_draft}\n\n"
        f"EVIDENCE:\n{evidence_json}\n\n"
        f"CHECK RULES:\n"
        f"1. Does the diagnosis appear in ANY model's top-3 predictions?\n"
        f"2. Does the confidence match the consensus level?\n"
        f"3. Is every claim in the report traceable to the evidence?\n"
        f"4. Does the report mention a diagnosis NOT supported by evidence?\n"
        f"5. If sufficiency is 'insufficient', does the report still claim confidence?\n\n"
        f"Return JSON: {{\"status\": \"pass\" or \"fail\", \"reason\": \"...\"}}"
    )

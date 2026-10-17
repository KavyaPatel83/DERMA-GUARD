"""src/llm/extraction.py — Structured symptom extraction pipeline."""
from __future__ import annotations

import warnings
from typing import Dict, Optional

from src.llm.prompts import SYMPTOM_EXTRACTION_SYSTEM, symptom_extraction_prompt


def extract_symptoms(text: str, llm_client=None) -> Dict[str, str]:
    """Extract structured symptoms from patient text.

    Args:
        text: raw patient description
        llm_client: OllamaClient (uses heuristics if None)

    Returns:
        dict with keys: duration, growth, color_change, itching, pain, bleeding
        values: 'true' | 'false' | 'unknown'
    """
    fields = ["duration", "growth", "color_change", "itching", "pain", "bleeding"]
    if not text or not text.strip():
        return {f: "unknown" for f in fields}

    if llm_client is None:
        return _heuristic_extract(text, fields)

    try:
        prompt = symptom_extraction_prompt(text)
        result = llm_client.generate_json(prompt, system_prompt=SYMPTOM_EXTRACTION_SYSTEM)
        # Validate fields
        out = {}
        for f in fields:
            val = str(result.get(f, "unknown")).lower()
            out[f] = val if val in ("true", "false", "unknown") else "unknown"
        return out
    except Exception as e:
        warnings.warn(f"[Extraction] LLM extraction failed: {e}. Using heuristics.")
        return _heuristic_extract(text, fields)


def _heuristic_extract(text: str, fields: list) -> Dict[str, str]:
    """Simple keyword-based extraction fallback."""
    text_lower = text.lower()
    kw = {
        "duration":     ["month", "week", "year", "day", "long", "since"],
        "growth":       ["grow", "grew", "bigger", "larger", "spread"],
        "color_change": ["color", "darker", "lighter", "changed"],
        "itching":      ["itch", "itchy", "scratch"],
        "pain":         ["pain", "painful", "hurt", "sore"],
        "bleeding":     ["bleed", "blood"],
    }
    return {f: ("true" if any(k in text_lower for k in kw[f]) else "unknown") for f in fields}

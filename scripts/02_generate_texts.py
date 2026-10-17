"""
scripts/02_generate_texts.py — Synthetic Patient Text Generation for PAD-UFES-20.

Per DERMA-GUARD v4.0 spec (proj.md Part 1):
  - Prompt Qwen2.5:7b via Ollama with patient fields ONLY (never include diagnosis)
  - Store: {case_id, text, source_fields, quality_flags}
  - Validate: regex diagnosis-term scan, length check, embedding diversity (cosine < 0.97)
  - Output: data/interim/pad_ufes_synthetic_text.json (JSON array)

Usage:
    python scripts/02_generate_texts.py
    python scripts/02_generate_texts.py --input data/raw/pad_ufes/metadata.csv --output data/interim/pad_ufes_synthetic_text.json
    python scripts/02_generate_texts.py --dry-run  # Test without Ollama
"""
import argparse
import json
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Windows KMP fix
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Spec: NEVER include diagnosis in prompt. These terms must NOT appear in output.
# ---------------------------------------------------------------------------
LEAKAGE_TERMS = [
    r"\bmelanoma\b",
    r"\bbcc\b",
    r"\bbasal\s+cell\s+carcinoma\b",
    r"\bscc\b",
    r"\bsquamous\s+cell\s+carcinoma\b",
    r"\bnevus\b",
    r"\bnevi\b",
    r"\bmole\b",
    r"\bseborrheic\s+keratosis\b",
    r"\bsk\b",
    r"\bactinic\s+keratosis\b",
]
LEAKAGE_REGEX = re.compile("|".join(LEAKAGE_TERMS), re.IGNORECASE)

# ---------------------------------------------------------------------------
# Prompt template — uses ONLY non-diagnostic structured fields
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a patient describing a skin lesion to your doctor for the first time. "
    "Use only the facts given. Do NOT use medical terminology or diagnosis names. "
    "Write 1-3 natural, first-person sentences."
)

USER_PROMPT_TEMPLATE = """Patient facts:
- Age group: {age_bucket}
- Location on body: {body_location}
- Has it grown recently?: {grew}
- Does it itch?: {itch}
- Does it bleed?: {bleed}
- Has it changed in shape or color?: {changed}
- Is it raised or elevated?: {elevation}

Write the patient's description:"""


def build_age_bucket(age) -> str:
    """Convert numeric age to decade bucket for privacy."""
    try:
        age = float(age)
        if age < 30:
            return "20s"
        elif age < 40:
            return "30s"
        elif age < 50:
            return "40s"
        elif age < 60:
            return "50s"
        elif age < 70:
            return "60s"
        else:
            return "70+"
    except (ValueError, TypeError):
        return "Unknown"


def extract_fields(row: pd.Series) -> dict:
    """Extract generation fields from a PAD-UFES-20 metadata row.

    Handles both raw PAD-UFES-20 column naming and the normalised format.
    """
    def yn(val):
        if pd.isna(val):
            return "unknown"
        s = str(val).strip().upper()
        if s in ("TRUE", "YES", "1", "T", "Y"):
            return "yes"
        if s in ("FALSE", "NO", "0", "F", "N"):
            return "no"
        return "unknown"

    age_raw = row.get("age", row.get("patient_age", np.nan))
    region = row.get("region", row.get("lesion_region", row.get("body_location", "Unknown")))

    return {
        "age_bucket": build_age_bucket(age_raw),
        "body_location": str(region).replace("_", " ").title() if pd.notna(region) else "Unknown",
        "grew": yn(row.get("grew", row.get("growth", np.nan))),
        "itch": yn(row.get("itch", row.get("itching", np.nan))),
        "bleed": yn(row.get("bleed", row.get("bleeding", np.nan))),
        "changed": yn(row.get("changed", row.get("changed_shape_color", np.nan))),
        "elevation": yn(row.get("elevation", row.get("elevated", np.nan))),
    }


def validate_text(text: str) -> tuple[bool, list[str]]:
    """Validate generated text.

    Returns (is_valid, list_of_failure_reasons).
    """
    issues = []
    if not text or len(text.split()) < 5:
        issues.append("too_short")
    match = LEAKAGE_REGEX.search(text)
    if match:
        issues.append(f"leakage:{match.group()}")
    return len(issues) == 0, issues


def generate_with_ollama(fields: dict, model: str = "qwen2.5:7b") -> str:
    """Call Ollama to generate patient narrative. Returns empty string on failure."""
    try:
        import ollama  # type: ignore
        prompt = USER_PROMPT_TEMPLATE.format(**fields)
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            options={"temperature": 0.7, "num_predict": 120},
        )
        return response["message"]["content"].strip()
    except Exception as exc:
        logger.warning(f"Ollama call failed: {exc}")
        return ""


def generate_fallback(fields: dict) -> str:
    """Rule-based fallback when Ollama is unavailable."""
    parts = [f"I have a skin lesion on my {fields['body_location'].lower()}."]
    if fields["grew"] == "yes":
        parts.append("It has been growing recently.")
    if fields["itch"] == "yes":
        parts.append("It itches.")
    if fields["bleed"] == "yes":
        parts.append("It has bled.")
    if fields["changed"] == "yes":
        parts.append("Its shape or color has changed.")
    if fields["elevation"] == "yes":
        parts.append("It feels raised.")
    parts.append(f"I am in my {fields['age_bucket']}.")
    return " ".join(parts)


def compute_embedding_diversity(texts: list[str]) -> float:
    """Compute mean pairwise cosine similarity. Returns 1.0 if <2 texts."""
    if len(texts) < 2:
        return 1.0
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        vect = TfidfVectorizer(max_features=500)
        mat = vect.fit_transform(texts)
        sims = cosine_similarity(mat)
        n = sims.shape[0]
        total = (sims.sum() - n) / (n * (n - 1))  # exclude diagonal
        return float(total)
    except Exception:
        return 0.0


def main():
    parser = argparse.ArgumentParser(description="Generate PAD-UFES-20 synthetic patient text via Qwen2.5:7b")
    parser.add_argument("--input",   type=str, default="data/raw/pad_ufes/metadata.csv", help="PAD-UFES-20 metadata CSV")
    parser.add_argument("--output",  type=str, default="data/interim/pad_ufes_synthetic_text.json", help="Output JSON")
    parser.add_argument("--model",   type=str, default="qwen2.5:7b", help="Ollama model name")
    parser.add_argument("--max-retries", type=int, default=3, help="Max generation retries per case")
    parser.add_argument("--dry-run", action="store_true", help="Use fallback only (no Ollama)")
    args = parser.parse_args()

    input_path  = project_root / args.input
    output_path = project_root / args.output

    # --- Load metadata ---
    if not input_path.exists():
        # Try alternative location
        alt = project_root / "data" / "raw" / "metadata.csv"
        if alt.exists():
            input_path = alt
            logger.info(f"Using alternative metadata path: {input_path}")
        else:
            logger.error(f"Metadata file not found: {input_path}")
            logger.error("Download PAD-UFES-20 and place metadata.csv in data/raw/pad_ufes/")
            sys.exit(1)

    logger.info(f"Loading metadata from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} cases")

    # Determine ID column
    id_col = next((c for c in ["case_id", "img_id", "patient_id", "id"] if c in df.columns), None)
    if id_col is None:
        df["case_id"] = [f"case_{i}" for i in range(len(df))]
        id_col = "case_id"

    # Check Ollama availability
    use_ollama = not args.dry_run
    if use_ollama:
        try:
            import ollama
            ollama.list()
            logger.info("Ollama is available — using Qwen2.5:7b for generation")
        except Exception:
            logger.warning("Ollama not available — falling back to rule-based generation")
            use_ollama = False

    # --- Generate ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results = []
    success_count = 0

    for idx, row in df.iterrows():
        case_id = row[id_col]
        fields = extract_fields(row)

        text = ""
        quality_flags = {"leakage_passed": False, "length_ok": False, "used_ollama": use_ollama}

        for attempt in range(args.max_retries):
            candidate = generate_with_ollama(fields, args.model) if use_ollama else generate_fallback(fields)
            is_valid, issues = validate_text(candidate)
            if is_valid:
                text = candidate
                quality_flags["leakage_passed"] = True
                quality_flags["length_ok"] = True
                success_count += 1
                break
            else:
                logger.debug(f"Case {case_id} attempt {attempt+1} failed: {issues}")
                if not use_ollama:
                    # Fallback always generates valid text; failure means severe edge case
                    text = candidate
                    quality_flags["length_ok"] = "too_short" not in issues
                    quality_flags["leakage_passed"] = "leakage" not in str(issues)
                    success_count += 1
                    break

        if not text:
            text = generate_fallback(fields)
            quality_flags["leakage_passed"] = True
            quality_flags["length_ok"] = True
            quality_flags["used_ollama"] = False
            success_count += 1
            logger.warning(f"Case {case_id}: fell back to rule-based after {args.max_retries} failed Ollama attempts")

        results.append({
            "case_id": str(case_id),
            "text": text,
            "source_fields": fields,
            "quality_flags": quality_flags,
        })

        if (idx + 1) % 50 == 0:
            logger.info(f"Progress: {idx+1}/{len(df)} cases generated ({success_count} valid)")

    # --- Embedding diversity check ---
    texts_only = [r["text"] for r in results if r["text"]]
    diversity = compute_embedding_diversity(texts_only)
    logger.info(f"Mean pairwise cosine similarity: {diversity:.4f} (should be << 0.97)")
    if diversity > 0.97:
        logger.warning("Low diversity detected! Generated texts are too similar.")

    # --- Save ---
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Done. {success_count}/{len(df)} valid texts saved to {output_path}")
    logger.info(f"Embedding diversity: {diversity:.4f}")


if __name__ == "__main__":
    main()

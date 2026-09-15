"""
================================================================================================
DERMA-GUARD: Comprehensive Multi-Class & Multi-Scenario Clinical Inference Engine
================================================================================================
Demonstrates:
  1. ALL 6 Diagnostic Classes (BCC, ACK, NEV, SEK, SCC, MEL)
  2. ALL Modality Input Types (Only Image, Only Metadata, Only Text, Image+Meta, Tri-Modal)
  3. ALL Confidence Levels (High Confidence Decisive, Moderate 2-Class, Low Ambiguity 3-4 Class)
  4. Conflict Detection & Devil's Advocate Scenarios
  5. Tailored, Evidence-Aware Clinical Advice according to scores & conformal sets

Usage:
  python clinical_case_tester.py             # Interactive scenario selector
  python clinical_case_tester.py --all       # Run all 8 clinical scenarios in sequence
  python clinical_case_tester.py --scenario 1# Run specific scenario (1 through 8)
  python clinical_case_tester.py --class MEL # Run scenario for specific lesion class
"""

import os
import sys
import argparse
import warnings

warnings.filterwarnings("ignore")

# Ensure UTF-8 output on Windows terminal
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import transformers
transformers.logging.set_verbosity_error()

from predict import DermaGuardPredictor, print_prediction_report


# ==============================================================================================
# CLINICAL SCENARIO CATALOG (PAD-UFES-20 DATASET)
# ==============================================================================================
def resolve_img(filename):
    candidates = [
        os.path.join(PROJECT_ROOT, "data", "images", filename),
        os.path.join(r"D:\VIT BOOKS\PROJECT 1\Dataset\images", filename)
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return candidates[0]

SCENARIOS = [
    {
        'id': 1,
        'title': "High-Confidence Benign Nevus (Model G - Tri-Modal)",
        'target_class': "NEV",
        'modality_type': "Full Tri-Modal (Image + Metadata + Text)",
        'model_code': "G",
        'confidence_tier': "HIGH CONFIDENCE (>90%, Set Size: 1)",
        'description': "8-year-old child with an asymptomatic, stable, flat 5mm brown macule on arm.",
        'image': resolve_img("PAT_1516_1765_530.png"),
        'metadata': {
            'age': 8, 'gender': 'MALE', 'region': 'ARM',
            'diameter_1': 5.0, 'diameter_2': 4.0, 'fitspatrick': 2,
            'itch': 'FALSE', 'grew': 'FALSE', 'hurt': 'FALSE', 'bleed': 'FALSE', 'elevation': 'FALSE'
        },
        'text': "8-year-old male with a stable, flat, non-pruritic 5mm brownish macule on the arm with no history of growth.",
        'expected_outcome': "Decisive single-class diagnosis (NEV), Conformal Set Size: 1, Low Uncertainty"
    },
    {
        'id': 2,
        'title': "High-Confidence Carcinoma (Model G - Tri-Modal)",
        'target_class': "BCC",
        'modality_type': "Full Tri-Modal (Image + Metadata + Text)",
        'model_code': "G",
        'confidence_tier': "HIGH CONFIDENCE (>80%, Set Size: 1-2)",
        'description': "55-year-old female with a 6mm bleeding, growing nodule on the neck.",
        'image': resolve_img("PAT_46_881_939.png"),
        'metadata': {
            'age': 55, 'gender': 'FEMALE', 'region': 'NECK',
            'diameter_1': 6.0, 'diameter_2': 5.0, 'fitspatrick': 3,
            'itch': 'TRUE', 'grew': 'TRUE', 'hurt': 'FALSE', 'bleed': 'TRUE', 'elevation': 'TRUE'
        },
        'text': "55-year-old female presenting with a 6mm bleeding, growing, raised nodule on the neck with positive personal cancer history.",
        'expected_outcome': "High probability of Basal Cell Carcinoma (BCC), surgical evaluation indicated"
    },
    {
        'id': 3,
        'title': "Actinic Sun-Damaged Keratosis (Model D - Image + Metadata)",
        'target_class': "ACK",
        'modality_type': "Dual-Modal (Image + Metadata)",
        'model_code': "D",
        'confidence_tier': "HIGH CONFIDENCE (>80%)",
        'description': "77-year-old patient with an itchy flat erythematous keratotic patch on the face.",
        'image': resolve_img("PAT_1545_1867_547.png"),
        'metadata': {
            'age': 77, 'gender': 'FEMALE', 'region': 'FACE',
            'diameter_1': 5.0, 'diameter_2': 4.0, 'fitspatrick': 2,
            'itch': 'TRUE', 'grew': 'FALSE', 'hurt': 'FALSE', 'bleed': 'FALSE', 'elevation': 'FALSE'
        },
        'text': None,
        'expected_outcome': "Actinic Keratosis (ACK) identification without text modality"
    },
    {
        'id': 4,
        'title': "Malignant Melanoma Alert (Model G - Tri-Modal)",
        'target_class': "MEL",
        'modality_type': "Full Tri-Modal (Image + Metadata + Text)",
        'model_code': "G",
        'confidence_tier': "HIGH PRIORITY MALIGNANCY ALERT",
        'description': "78-year-old male with a large 10mm evolving raised lesion on the back.",
        'image': resolve_img("PAT_680_1289_182.png"),
        'metadata': {
            'age': 78, 'gender': 'MALE', 'region': 'BACK',
            'diameter_1': 10.0, 'diameter_2': 10.0, 'fitspatrick': 2,
            'itch': 'FALSE', 'grew': 'TRUE', 'hurt': 'FALSE', 'bleed': 'FALSE', 'elevation': 'TRUE'
        },
        'text': "78-year-old male with a 10mm raised, growing pigmented lesion on the back with family skin cancer history.",
        'expected_outcome': "Melanoma (MEL) / High risk malignancy alert triggered"
    },
    {
        'id': 5,
        'title': "Moderate Confidence Differential Diagnosis (Model D - Image + Metadata)",
        'target_class': "SEK",
        'modality_type': "Dual-Modal (Image + Metadata)",
        'model_code': "D",
        'confidence_tier': "MODERATE CONFIDENCE (50-75%, 2 Differential Classes)",
        'description': "53-year-old patient with a 5mm raised stuck-on appearance lesion on chest.",
        'image': resolve_img("PAT_1549_1882_230.png"),
        'metadata': {
            'age': 53, 'gender': 'FEMALE', 'region': 'CHEST',
            'diameter_1': 5.0, 'diameter_2': 4.0, 'fitspatrick': 2,
            'itch': 'TRUE', 'grew': 'FALSE', 'hurt': 'FALSE', 'bleed': 'FALSE', 'elevation': 'TRUE'
        },
        'text': None,
        'expected_outcome': "Dual differential diagnosis set (e.g. SEK vs BCC)"
    },
    {
        'id': 6,
        'title': "Squamous Cell Carcinoma (Model F - Metadata + Text)",
        'target_class': "SCC",
        'modality_type': "Dual-Modal (Metadata + Text - No Image)",
        'model_code': "F",
        'confidence_tier': "MODERATE-HIGH CONFIDENCE (Non-Visual Modalities)",
        'description': "60-year-old male with an ulcerated lesion on nose with pesticide exposure history.",
        'image': None,
        'metadata': {
            'age': 60, 'gender': 'MALE', 'region': 'NOSE',
            'diameter_1': 3.0, 'diameter_2': 3.0, 'fitspatrick': 2,
            'itch': 'TRUE', 'grew': 'FALSE', 'hurt': 'FALSE', 'bleed': 'FALSE', 'elevation': 'FALSE'
        },
        'text': "60-year-old male with an itchy 3mm ulcerated nodule on the nose with occupational pesticide exposure.",
        'expected_outcome': "Squamous Cell Carcinoma (SCC) classified from metadata & narrative alone"
    },
    {
        'id': 7,
        'title': "Low Confidence & Multi-Class Ambiguity (Model A - Only Image)",
        'target_class': "Ambiguous",
        'modality_type': "Single Modality (Only Image, Missing Metadata & Text)",
        'model_code': "A",
        'confidence_tier': "LOW CONFIDENCE / HIGH UNCERTAINTY (3-4 Class Set)",
        'description': "Image provided in isolation without clinical history or patient metadata.",
        'image': resolve_img("PAT_380_1540_959.png"),
        'metadata': None,
        'text': None,
        'expected_outcome': "High Uncertainty warning, wide conformal set (>=3 classes), recommendation to ACQUIRE metadata"
    },
    {
        'id': 8,
        'title': "Conflicting Modality Evidence (Devil's Advocate Triggered)",
        'target_class': "Conflict Test",
        'modality_type': "Tri-Modal with Injected Diagnostic Conflict",
        'model_code': "G",
        'confidence_tier': "CRITICAL CONFLICT / ESCALATE GATE",
        'description': "Benign Nevus image paired intentionally with aggressive elderly Carcinoma metadata & text.",
        'image': resolve_img("PAT_1516_1765_530.png"), # Benign pediatric mole
        'metadata': {
            'age': 79, 'gender': 'MALE', 'region': 'NECK',
            'diameter_1': 14.0, 'diameter_2': 12.0, 'fitspatrick': 1,
            'itch': 'TRUE', 'grew': 'TRUE', 'hurt': 'TRUE', 'bleed': 'TRUE', 'elevation': 'TRUE'
        },
        'text': "79-year-old male with a rapidly expanding, 14mm painful, ulcerated bleeding tumor on the neck.",
        'expected_outcome': "Devil's Advocate activates: multi-class spread, Gate = ESCALATE / ACQUIRE"
    }
]


# ==============================================================================================
# ACTIONABLE EVIDENCE-BASED CLINICAL ADVICE GENERATOR
# ==============================================================================================
def generate_custom_clinical_advice(res: dict):
    pred = res['primary_prediction']
    conf = res['confidence'] * 100.0
    c_set = res['prediction_set_95']
    set_size = len(c_set)
    gate = res['evidence_manager']['decision_gate']
    active_mods = res['active_modalities']

    is_malignant = pred in ['MEL', 'BCC', 'SCC']
    
    advice_lines = []

    # 1. Action Gate Evaluation
    if gate in ['ESCALATE', 'ABSTAIN']:
        advice_lines.append("[!] CRITICAL SAFETY ALERT: Significant inter-modality conflict or low evidence sufficiency detected.")
        advice_lines.append("    -> Clinical Decision Gate: ESCALATE TO SENIOR DERMATOLOGIST.")
        advice_lines.append("    -> Action: Do NOT rely on automated top-1 prediction. Order urgent biopsy and clinical review.")
        return advice_lines

    # 2. Confidence Tier & Conformal Set Size
    if set_size == 1 and conf >= 80.0:
        advice_lines.append(f"[+] DECISIVE HIGH-CONFIDENCE DIAGNOSIS ({conf:.1f}% certainty):")
        advice_lines.append(f"    -> Definitive single-condition match: {pred}")
        if pred == 'NEV':
            advice_lines.append("    -> Clinical Advice: Benign melanocytic nevus. Recommend routine periodic observation (ABCDE self-check).")
        elif pred == 'BCC':
            advice_lines.append("    -> Clinical Advice: Non-melanoma carcinoma (BCC). Schedule surgical excision or Mohs micrographic surgery.")
        elif pred == 'ACK':
            advice_lines.append("    -> Clinical Advice: Pre-malignant actinic keratosis. Treat with cryotherapy (liquid nitrogen) or topical 5-FU.")
        elif pred == 'MEL':
            advice_lines.append("    -> URGENT ONCOLOGY ACTION: Malignant Melanoma. Schedule immediate narrow excisional biopsy (2mm margin).")
        elif pred == 'SEK':
            advice_lines.append("    -> Clinical Advice: Benign seborrheic keratosis. No therapeutic intervention required unless symptomatic.")
        elif pred == 'SCC':
            advice_lines.append("    -> Clinical Advice: Invasive Squamous Cell Carcinoma. Complete surgical excision with histological margin control.")
    
    elif set_size == 2 or (50.0 <= conf < 80.0):
        advice_lines.append(f"[?] MODERATE CONFIDENCE WITH DIFFERENTIAL DIAGNOSIS (Confidence: {conf:.1f}%):")
        advice_lines.append(f"    -> Primary Finding: {pred} ({conf:.1f}%) | Alternative Differential: {c_set[1] if len(c_set) > 1 else 'None'}")
        advice_lines.append(f"    -> 95% Conformal Set: {c_set}")
        if is_malignant:
            advice_lines.append("    -> Clinical Advice: Malignancy cannot be ruled out. High-magnification dermoscopy and short-term follow-up (3-4 weeks) or punch biopsy strongly advised.")
        else:
            advice_lines.append("    -> Clinical Advice: Dermoscopic inspection recommended to confirm border reticulation and vascular pattern before discharging.")

    else:
        advice_lines.append(f"[!] HIGH CLINICAL UNCERTAINTY / MULTI-CLASS AMBIGUITY ({set_size} Candidate Classes):")
        advice_lines.append(f"    -> Top-1 Guess: {pred} (Low Confidence: {conf:.1f}%)")
        advice_lines.append(f"    -> 95% Conformal Prediction Set: {c_set}")
        advice_lines.append("    -> Root Cause: Insufficient modality evidence (e.g. image-only without metadata) or ambiguous lesion morphology.")
        advice_lines.append("    -> Actionable Protocol:")
        if 'metadata' not in active_mods or 'text' not in active_mods:
            advice_lines.append("       1. ACQUIRE MISSING MODALITIES: Ingest patient age, anatomical location, growth history, and bleeding status.")
        advice_lines.append("       2. Secondary Review: Mandatory biopsy / histopathology before making therapeutic decisions.")

    return advice_lines


# ==============================================================================================
# EXECUTION HARNESS
# ==============================================================================================
def execute_scenario(scenario: dict, predictor: DermaGuardPredictor):
    print("\n" + "#" * 85)
    print(f"  SCENARIO #{scenario['id']}: {scenario['title'].upper()}")
    print(f"  Target Condition : {scenario['target_class']} | Modality Type: {scenario['modality_type']}")
    print(f"  Confidence Tier  : {scenario['confidence_tier']}")
    print(f"  Case Summary     : {scenario['description']}")
    print("#" * 85)

    res = predictor.predict(
        image_path_or_pil=scenario['image'],
        metadata_dict=scenario['metadata'],
        text_string=scenario['text'],
        target_model=scenario['model_code'],
        verbose=False
    )

    # Print clean formatted summary report
    print_prediction_report(res, title=f"CLINICAL REPORT: SCENARIO #{scenario['id']} ({scenario['title']})")

    # Generate and print tailored clinical advice
    advice = generate_custom_clinical_advice(res)
    print("\n" + "=" * 80)
    print("   EXPERT EVIDENCE-BASED CLINICAL ADVICE & DECISION PROTOCOL")
    print("=" * 80)
    for line in advice:
        print(line)
    print("=" * 80 + "\n")

    return res


def run_all(predictor: DermaGuardPredictor):
    summary_records = []
    for sc in SCENARIOS:
        res = execute_scenario(sc, predictor)
        summary_records.append({
            'id': sc['id'],
            'target': sc['target_class'],
            'model': res['selected_model'],
            'pred': res['primary_prediction'],
            'conf': f"{res['confidence']*100:.1f}%",
            'set': str(res['prediction_set_95']),
            'set_size': len(res['prediction_set_95']),
            'gate': res['evidence_manager']['decision_gate']
        })

    # Print Consolidated Scorecard
    print("\n" + "=" * 100)
    print("                         ALL CLINICAL SCENARIOS MASTER SUMMARY TABLE")
    print("=" * 100)
    header = f"{'ID':<4} | {'Target':<7} | {'Model':<10} | {'Prediction':<12} | {'Confidence':<10} | {'Set Size':<8} | {'Conformal Set':<25} | {'Decision Gate':<12}"
    print(header)
    print("-" * 100)
    for r in summary_records:
        row = f"{r['id']:<4} | {r['target']:<7} | {r['model']:<10} | {r['pred']:<12} | {r['conf']:<10} | {r['set_size']:<8} | {r['set']:<25} | {r['gate']:<12}"
        print(row)
    print("=" * 100 + "\n")


def main():
    parser = argparse.ArgumentParser(description="DERMA-GUARD Comprehensive Clinical Case & Multi-Class Scenario Tester")
    parser.add_argument("--all", action="store_true", help="Run all 8 clinical scenarios in sequence")
    parser.add_argument("--scenario", "-s", type=int, default=None, choices=range(1, 9), help="Scenario ID to execute (1 to 8)")
    parser.add_argument("--class", "-c", dest="cls", type=str, default=None, help="Target class to execute (BCC, ACK, NEV, SEK, SCC, MEL)")
    args = parser.parse_args()

    print("[*] Initializing DERMA-GUARD Predictor with Saved Checkpoints...", flush=True)
    predictor = DermaGuardPredictor()
    print("[+] Predictor Ready! Checkpoints loaded directly from saved_models/.\n")

    if args.all:
        run_all(predictor)
    elif args.scenario:
        matched = [sc for sc in SCENARIOS if sc['id'] == args.scenario]
        if matched:
            execute_scenario(matched[0], predictor)
        else:
            print(f"[!] Error: Scenario {args.scenario} not found.")
    elif args.cls:
        c_upper = args.cls.upper()
        matched = [sc for sc in SCENARIOS if sc['target_class'].upper() == c_upper]
        if matched:
            for m in matched:
                execute_scenario(m, predictor)
        else:
            print(f"[!] No direct preset scenario for class '{args.cls}'. Available: BCC, ACK, NEV, SEK, SCC, MEL")
    else:
        # Interactive Menu
        print("=" * 70)
        print("          DERMA-GUARD COMPREHENSIVE CLINICAL SCENARIOS")
        print("=" * 70)
        for sc in SCENARIOS:
            print(f"  [{sc['id']}] {sc['title']}")
            print(f"      Modality: {sc['modality_type']} | Tier: {sc['confidence_tier']}")
        print("  [A] Run ALL 8 scenarios in sequence")
        print("  [Q] Quit")
        print("=" * 70)
        
        try:
            choice = input("\nEnter choice [1-8, A, Q]: ").strip().upper()
        except EOFError:
            choice = "A"

        if choice == 'A':
            run_all(predictor)
        elif choice == 'Q':
            print("Exiting.")
            return
        elif choice.isdigit() and 1 <= int(choice) <= 8:
            matched = [sc for sc in SCENARIOS if sc['id'] == int(choice)]
            if matched:
                execute_scenario(matched[0], predictor)
        else:
            print("[INFO] Defaulting to running all scenarios:\n")
            run_all(predictor)


if __name__ == '__main__':
    main()

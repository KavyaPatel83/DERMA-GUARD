"""
====================================================================================================
DERMA-GUARD: Interactive Clinical Prediction Assistant (User-Guided Inputs)
====================================================================================================
Allows the user to:
  1. Select an image file (browse via Windows file dialog or type file path)
  2. Input custom patient metadata (age, gender, anatomical site, diameters, ABCDE symptoms)
  3. Enter custom clinical free text notes (or press Enter to auto-generate from metadata)
  4. Choose any model permutation (A through G, or default to Full Multimodal Model G)
  5. Run direct inference from saved models (no re-training needed)
  6. Review primary diagnosis, confidence, conformal prediction set, and tailored clinical advice

Usage:
  python interactive_predict.py
====================================================================================================
"""

import os
import sys
import json
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
from clinical_case_tester import generate_custom_clinical_advice


def prompt_image_selection():
    """Prompts user for image path, offering a file dialog or sample fallback."""
    print("\n" + "=" * 70)
    print(" [STEP 1/4] SELECT CUTANEOUS LESION IMAGE")
    print("=" * 70)
    print(" Options:")
    print("   [1] Open Windows File Dialog to select image from your computer")
    print("   [2] Enter file path manually")
    print("   [3] Use sample benign nevus image (PAT_1516_1765_530.png)")
    print("   [4] Use sample carcinoma image (PAT_46_881_939.png)")
    print("   [5] Skip image (Predict using Metadata and/or Free Text only)")
    
    choice = input("\nSelect option [1-5, default=1]: ").strip()
    if choice == '' or choice == '1':
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            file_path = filedialog.askopenfilename(
                title="Select Skin Lesion Image",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff"), ("All Files", "*.*")]
            )
            root.destroy()
            if file_path and os.path.isfile(file_path):
                print(f"[+] Selected Image: {file_path}")
                return file_path
            else:
                print("[!] No file selected via dialog. Falling back to manual input.")
        except Exception as e:
            print(f"[!] Dialog unavailable ({e}). Falling back to manual input.")

    if choice == '2' or choice == '1':
        while True:
            manual_path = input("Enter full image file path: ").strip().strip('"').strip("'")
            if os.path.isfile(manual_path):
                return manual_path
            print(f"[!] File not found: '{manual_path}'. Please check the path and retry.")

    elif choice == '3':
        sample_path = os.path.join(PROJECT_ROOT, "data", "images", "PAT_1516_1765_530.png")
        if os.path.isfile(sample_path):
            print(f"[+] Using sample nevus image: {sample_path}")
            return sample_path
        return r"D:\VIT BOOKS\PROJECT 1\Dataset\images\PAT_1516_1765_530.png"

    elif choice == '4':
        sample_path = os.path.join(PROJECT_ROOT, "data", "images", "PAT_46_881_939.png")
        if os.path.isfile(sample_path):
            print(f"[+] Using sample carcinoma image: {sample_path}")
            return sample_path
        return r"D:\VIT BOOKS\PROJECT 1\Dataset\images\PAT_46_881_939.png"

    elif choice == '5':
        print("[*] Image modality skipped.")
        return None

    return None


def prompt_yes_no(question, default="FALSE"):
    d_str = "[y/N]" if default == "FALSE" else "[Y/n]"
    ans = input(f"   - {question} {d_str}: ").strip().lower()
    if ans == '':
        return default
    if ans in ['y', 'yes', 'true', '1', 't']:
        return "TRUE"
    return "FALSE"


def prompt_metadata():
    """Prompts user step-by-step for patient demographics, anatomy, and ABCDE symptoms."""
    print("\n" + "=" * 70)
    print(" [STEP 2/4] ENTER PATIENT DEMOGRAPHICS & CLINICAL METADATA")
    print("=" * 70)
    print(" (Press Enter on any field to accept the default value)")

    skip = input("\nDo you want to enter metadata? [Y/n]: ").strip().lower()
    if skip in ['n', 'no']:
        print("[*] Metadata modality skipped.")
        return None

    # Age
    while True:
        age_str = input("   - Patient Age [default=50]: ").strip()
        if age_str == '':
            age = 50
            break
        try:
            age = int(age_str)
            if 0 <= age <= 120:
                break
            print("[!] Age must be between 0 and 120.")
        except ValueError:
            print("[!] Please enter a valid integer for age.")

    # Gender
    gender_in = input("   - Patient Gender [MALE / FEMALE / unknown, default=FEMALE]: ").strip().upper()
    if gender_in in ['M', 'MALE']:
        gender = 'MALE'
    elif gender_in in ['F', 'FEMALE']:
        gender = 'FEMALE'
    elif gender_in == '':
        gender = 'FEMALE'
    else:
        gender = gender_in

    # Anatomical Region
    print("   Common regions: FACE, NECK, CHEST, BACK, ABDOMEN, ARM, FOREARM, HAND, THIGH, LEG, FOOT, SCALP, NOSE, EAR")
    region_in = input("   - Anatomical Region [default=FACE]: ").strip().upper()
    region = region_in if region_in else "FACE"

    # Lesion Dimensions
    d1_str = input("   - Largest Diameter (diameter_1 in mm) [default=6.0]: ").strip()
    try:
        d1 = float(d1_str) if d1_str else 6.0
    except ValueError:
        d1 = 6.0

    d2_str = input("   - Perpendicular Diameter (diameter_2 in mm) [default=5.0]: ").strip()
    try:
        d2 = float(d2_str) if d2_str else 5.0
    except ValueError:
        d2 = 5.0

    # Fitzpatrick Phototype (1 to 6)
    fitz_str = input("   - Fitzpatrick Skin Phototype (1 to 6) [default=2]: ").strip()
    try:
        fitz = int(fitz_str) if fitz_str and 1 <= int(fitz_str) <= 6 else 2
    except ValueError:
        fitz = 2

    # ABCDE Symptoms
    print("\n   Clinical Symptoms & ABCDE History:")
    itch = prompt_yes_no("Does the lesion itch (pruritus)?", default="FALSE")
    grew = prompt_yes_no("Has the lesion grown in size recently?", default="FALSE")
    bleed = prompt_yes_no("Has the lesion bled or ulcerated?", default="FALSE")
    hurt = prompt_yes_no("Is the lesion tender or painful?", default="FALSE")
    elevation = prompt_yes_no("Is the lesion palpably raised / elevated?", default="FALSE")

    meta = {
        'age': age,
        'gender': gender,
        'region': region,
        'diameter_1': d1,
        'diameter_2': d2,
        'fitspatrick': fitz,
        'itch': itch,
        'grew': grew,
        'hurt': hurt,
        'bleed': bleed,
        'elevation': elevation
    }

    print("\n[+] Captured Patient Metadata Record:")
    print(f"    {json.dumps(meta, indent=2)}")
    return meta


def prompt_clinical_text(metadata_dict=None):
    """Prompts user for clinical narrative free text, with auto-generation option."""
    print("\n" + "=" * 70)
    print(" [STEP 3/4] CLINICAL FREE TEXT NARRATIVE")
    print("=" * 70)
    print(" Options:")
    print("   - Type your custom clinical notes / patient history description")
    print("   - Type 'AUTO' (or press Enter if metadata provided) to auto-synthesize text")
    print("   - Type 'SKIP' to run without textual modality")

    prompt_label = "\nEnter clinical narrative (or press Enter for AUTO): " if metadata_dict else "\nEnter clinical narrative (or press Enter to SKIP): "
    user_text = input(prompt_label).strip()

    if user_text.upper() == 'SKIP':
        print("[*] Text modality skipped.")
        return None, False

    if user_text == '' or user_text.upper() == 'AUTO':
        if metadata_dict:
            print("[+] Auto-generating clinical narrative text from metadata...")
            return None, True
        else:
            print("[*] No metadata provided for auto-generation. Text skipped.")
            return None, False

    print(f"[+] Custom Clinical Text Accepted: \"{user_text}\"")
    return user_text, False


def prompt_model_selection(has_img, has_meta, has_text):
    """Allows user to specify target model architecture or auto-select optimal model."""
    print("\n" + "=" * 70)
    print(" [STEP 4/4] SELECT TARGET MODEL ARCHITECTURE")
    print("=" * 70)
    print(" Available Architectures:")
    print("   [G] Model G: Full Tri-Modal (ViT + MetaBlock MLP + Bio_ClinicalBERT) [Recommended]")
    print("   [D] Model D: Dual-Stream Image + Metadata Adaptive Fusion")
    print("   [E] Model E: Dual-Stream Image + Free Text Adaptive Fusion")
    print("   [F] Model F: Dual-Stream Free Text + Metadata Adaptive Fusion")
    print("   [A] Model A: Vision-Only ResNet50 + MHSA ViT")
    print("   [B] Model B: Metadata-Only Residual MetaBlock MLP")
    print("   [C] Model C: Free Text-Only Bio_ClinicalBERT")
    print("   [AUTO] Automatically select best matching model for your active inputs")

    m_in = input("\nSelect model [G/D/E/F/A/B/C/AUTO, default=AUTO]: ").strip().upper()
    if m_in in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
        return m_in
    return None  # Auto-select based on active inputs


def run_interactive_session(predictor: DermaGuardPredictor):
    print("\n" + "#" * 80)
    print("     DERMA-GUARD INTERACTIVE MULTIMODAL CLINICAL PREDICTOR")
    print("     Load Checkpoints: Direct from saved_models/ (Zero Re-training)")
    print("#" * 80)

    while True:
        # Step 1: Image
        image_path = prompt_image_selection()

        # Step 2: Metadata
        metadata_dict = prompt_metadata()

        # Step 3: Text
        clinical_text, auto_text = prompt_clinical_text(metadata_dict)

        if image_path is None and metadata_dict is None and clinical_text is None and not auto_text:
            print("\n[!] Error: No modalities selected! You must provide at least one input.")
            retry = input("Try again? [Y/n]: ").strip().lower()
            if retry in ['n', 'no']:
                break
            continue

        # Step 4: Model Choice
        has_img = image_path is not None
        has_meta = metadata_dict is not None
        has_text = (clinical_text is not None) or auto_text
        target_model = prompt_model_selection(has_img, has_meta, has_text)

        print("\n[*] Executing Multimodal Clinical Inference Pipeline...")
        try:
            res = predictor.predict(
                image_path_or_pil=image_path,
                metadata_dict=metadata_dict,
                text_string=clinical_text,
                auto_generate_text=auto_text,
                target_model=target_model,
                verbose=True
            )

            # Print Standard Clinical Report
            print_prediction_report(res, title="DERMA-GUARD PATIENT DIAGNOSTIC REPORT")

            # Generate and Print Tailored Evidence-Based Clinical Advice
            advice = generate_custom_clinical_advice(res)
            print("\n" + "=" * 80)
            print("   TAILORED EVIDENCE-BASED MEDICAL ADVICE & DECISION PROTOCOL")
            print("=" * 80)
            for line in advice:
                print(line)
            print("=" * 80 + "\n")

        except Exception as e:
            print(f"\n[!] Error during inference: {e}")
            import traceback
            traceback.print_exc()

        # Loop Prompt
        print("-" * 80)
        again = input("Do you want to test another patient / image? [Y/n]: ").strip().lower()
        if again in ['n', 'no', 'q', 'quit']:
            print("\nThank you for using DERMA-GUARD. Clinical session ended.")
            break


def main():
    print("[*] Initializing DERMA-GUARD Inference Engine with Saved Checkpoints...", flush=True)
    predictor = DermaGuardPredictor()
    print("[+] Models successfully loaded into memory!\n")
    run_interactive_session(predictor)


if __name__ == '__main__':
    main()

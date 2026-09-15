"""
====================================================================================================
DERMA-GUARD: Desktop Graphical User Interface (GUI) for Clinical Diagnostics
====================================================================================================
A complete GUI application allowing the user to:
  - Browse and visually inspect cutaneous lesion images
  - Fill in patient demographics, anatomical location, and ABCDE clinical symptoms
  - Write custom clinical narratives or auto-generate them
  - Select model configuration (Models A through G)
  - Run direct multi-modal inference with saved models (no re-training)
  - View confidence scores, probability charts, 95% conformal prediction sets, and tailored clinical advice

Usage:
  python gui_predict.py
====================================================================================================
"""

import os
import sys
import threading
import warnings
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

warnings.filterwarnings("ignore")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import transformers
transformers.logging.set_verbosity_error()

from predict import DermaGuardPredictor
from clinical_case_tester import generate_custom_clinical_advice


class DermaGuardGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DERMA-GUARD: Clinical Multimodal Diagnostic System")
        self.root.geometry("1180x860")
        self.root.minsize(1000, 750)

        # Style
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.predictor = None
        self.selected_image_path = None
        self.tk_img = None

        self._build_ui()
        self._load_predictor_background()

    def _build_ui(self):
        # Header Banner
        header = tk.Frame(self.root, bg="#1e293b", height=70)
        header.pack(fill=tk.X, side=tk.TOP)

        title = tk.Label(
            header,
            text="DERMA-GUARD CLINICAL DIAGNOSTIC ASSISTANT",
            font=("Segoe UI", 16, "bold"),
            fg="#f8fafc",
            bg="#1e293b"
        )
        title.pack(anchor="w", padx=20, pady=(10, 2))

        subtitle = tk.Label(
            header,
            text="Multimodal Skin Lesion Classification (ResNet50 + MHSA ViT + Bio_ClinicalBERT + Residual MetaBlock MLP)",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#1e293b"
        )
        subtitle.pack(anchor="w", padx=20, pady=(0, 10))

        # Main Container (Paned)
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#f1f5f9", sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left Column: Inputs
        left_frame = tk.Frame(paned, bg="#ffffff", bd=1, relief=tk.SOLID)
        paned.add(left_frame, minsize=480)

        # Right Column: Results & Advice
        right_frame = tk.Frame(paned, bg="#ffffff", bd=1, relief=tk.SOLID)
        paned.add(right_frame, minsize=480)

        self._build_left_inputs(left_frame)
        self._build_right_results(right_frame)

    def _build_left_inputs(self, parent):
        canvas = tk.Canvas(parent, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg="#ffffff")

        scroll_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_content, anchor="nw")
        canvas.configure(xscrollcommand=None, yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        pad = 12

        # Section 1: Image Selection
        lbl_sec1 = tk.Label(scroll_content, text="1. Cutaneous Image Input", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_sec1.pack(anchor="w", padx=pad, pady=(pad, 4))

        img_ctrl_frame = tk.Frame(scroll_content, bg="#ffffff")
        img_ctrl_frame.pack(fill=tk.X, padx=pad, pady=4)

        btn_browse = tk.Button(img_ctrl_frame, text="Browse Image...", bg="#0284c7", fg="#ffffff", font=("Segoe UI", 9, "bold"),
                               relief=tk.FLAT, padx=12, pady=4, command=self._browse_image)
        btn_browse.pack(side=tk.LEFT)

        btn_sample = tk.Button(img_ctrl_frame, text="Load Sample Image", bg="#f8fafc", fg="#334155", font=("Segoe UI", 9),
                               relief=tk.GROOVE, padx=10, pady=4, command=self._load_sample_image)
        btn_sample.pack(side=tk.LEFT, padx=8)

        self.lbl_img_path = tk.Label(scroll_content, text="No image selected", font=("Segoe UI", 8, "italic"), bg="#ffffff", fg="#64748b", wraplength=420)
        self.lbl_img_path.pack(anchor="w", padx=pad, pady=(2, 4))

        self.canvas_img_preview = tk.Canvas(scroll_content, width=200, height=150, bg="#f8fafc", bd=1, relief=tk.RIDGE)
        self.canvas_img_preview.pack(anchor="w", padx=pad, pady=4)
        self.canvas_img_preview.create_text(100, 75, text="Image Preview", fill="#94a3b8", font=("Segoe UI", 9))

        ttk.Separator(scroll_content, orient='horizontal').pack(fill=tk.X, padx=pad, pady=10)

        # Section 2: Demographics & Metadata
        lbl_sec2 = tk.Label(scroll_content, text="2. Patient Demographics & Symptoms", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_sec2.pack(anchor="w", padx=pad, pady=(4, 4))

        grid_frame = tk.Frame(scroll_content, bg="#ffffff")
        grid_frame.pack(fill=tk.X, padx=pad, pady=4)

        # Age
        tk.Label(grid_frame, text="Age:", bg="#ffffff", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=3)
        self.ent_age = ttk.Entry(grid_frame, width=8)
        self.ent_age.insert(0, "55")
        self.ent_age.grid(row=0, column=1, sticky="w", pady=3)

        # Gender
        tk.Label(grid_frame, text="Gender:", bg="#ffffff", font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w", padx=(15, 0), pady=3)
        self.cmb_gender = ttk.Combobox(grid_frame, values=["FEMALE", "MALE", "unknown"], width=10, state="readonly")
        self.cmb_gender.set("FEMALE")
        self.cmb_gender.grid(row=0, column=3, sticky="w", pady=3)

        # Anatomical Region
        tk.Label(grid_frame, text="Region:", bg="#ffffff", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=3)
        self.cmb_region = ttk.Combobox(grid_frame, values=["FACE", "NECK", "CHEST", "BACK", "ARM", "FOREARM", "HAND", "ABDOMEN", "THIGH", "LEG", "FOOT", "NOSE", "EAR", "SCALP"], width=10)
        self.cmb_region.set("NECK")
        self.cmb_region.grid(row=1, column=1, sticky="w", pady=3)

        # Phototype
        tk.Label(grid_frame, text="Phototype (1-6):", bg="#ffffff", font=("Segoe UI", 9)).grid(row=1, column=2, sticky="w", padx=(15, 0), pady=3)
        self.ent_fitz = ttk.Entry(grid_frame, width=8)
        self.ent_fitz.insert(0, "3")
        self.ent_fitz.grid(row=1, column=3, sticky="w", pady=3)

        # Diameters
        tk.Label(grid_frame, text="Diam 1 (mm):", bg="#ffffff", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=3)
        self.ent_d1 = ttk.Entry(grid_frame, width=8)
        self.ent_d1.insert(0, "6.0")
        self.ent_d1.grid(row=2, column=1, sticky="w", pady=3)

        tk.Label(grid_frame, text="Diam 2 (mm):", bg="#ffffff", font=("Segoe UI", 9)).grid(row=2, column=2, sticky="w", padx=(15, 0), pady=3)
        self.ent_d2 = ttk.Entry(grid_frame, width=8)
        self.ent_d2.insert(0, "5.0")
        self.ent_d2.grid(row=2, column=3, sticky="w", pady=3)

        # Checkboxes for ABCDE symptoms
        tk.Label(scroll_content, text="Reported Symptoms & History:", bg="#ffffff", font=("Segoe UI", 9, "bold"), fg="#334155").pack(anchor="w", padx=pad, pady=(6, 2))

        symp_frame = tk.Frame(scroll_content, bg="#ffffff")
        symp_frame.pack(fill=tk.X, padx=pad, pady=2)

        self.var_itch = tk.BooleanVar(value=True)
        self.var_grew = tk.BooleanVar(value=True)
        self.var_bleed = tk.BooleanVar(value=True)
        self.var_hurt = tk.BooleanVar(value=False)
        self.var_elevation = tk.BooleanVar(value=True)

        tk.Checkbutton(symp_frame, text="Itching (Pruritus)", variable=self.var_itch, bg="#ffffff").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        tk.Checkbutton(symp_frame, text="Recent Growth", variable=self.var_grew, bg="#ffffff").grid(row=0, column=1, sticky="w", padx=4, pady=2)
        tk.Checkbutton(symp_frame, text="Bleeding / Ulcer", variable=self.var_bleed, bg="#ffffff").grid(row=0, column=2, sticky="w", padx=4, pady=2)
        tk.Checkbutton(symp_frame, text="Pain / Tenderness", variable=self.var_hurt, bg="#ffffff").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        tk.Checkbutton(symp_frame, text="Raised / Elevated", variable=self.var_elevation, bg="#ffffff").grid(row=1, column=1, sticky="w", padx=4, pady=2)

        ttk.Separator(scroll_content, orient='horizontal').pack(fill=tk.X, padx=pad, pady=10)

        # Section 3: Clinical Free Text Narrative
        lbl_sec3 = tk.Label(scroll_content, text="3. Clinical Free Text Narrative", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_sec3.pack(anchor="w", padx=pad, pady=(4, 2))

        self.txt_notes = scrolledtext.ScrolledText(scroll_content, height=4, width=50, font=("Segoe UI", 9))
        self.txt_notes.insert(tk.END, "55-year-old female presenting with a 6mm bleeding, growing, raised nodular lesion on the neck.")
        self.txt_notes.pack(fill=tk.X, padx=pad, pady=4)

        self.var_auto_text = tk.BooleanVar(value=False)
        tk.Checkbutton(scroll_content, text="Auto-generate clinical text narrative from metadata above", variable=self.var_auto_text, bg="#ffffff").pack(anchor="w", padx=pad, pady=2)

        ttk.Separator(scroll_content, orient='horizontal').pack(fill=tk.X, padx=pad, pady=10)

        # Section 4: Target Model Selection & Action
        lbl_sec4 = tk.Label(scroll_content, text="4. Target Architecture & Run", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_sec4.pack(anchor="w", padx=pad, pady=(4, 2))

        mod_frame = tk.Frame(scroll_content, bg="#ffffff")
        mod_frame.pack(fill=tk.X, padx=pad, pady=4)

        tk.Label(mod_frame, text="Model Architecture:", bg="#ffffff", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.cmb_model = ttk.Combobox(mod_frame, values=[
            "AUTO: Best Matching Architecture",
            "Model G: Full Tri-Modal (ViT + MetaBlock + Bio_ClinicalBERT)",
            "Model D: Image + Metadata Adaptive Fusion",
            "Model E: Image + Free Text Adaptive Fusion",
            "Model F: Metadata + Free Text Adaptive Fusion",
            "Model A: Vision-Only (ResNet50 + MHSA ViT)",
            "Model B: Metadata-Only (Residual MetaBlock MLP)",
            "Model C: Free Text-Only (Bio_ClinicalBERT)"
        ], width=42, state="readonly")
        self.cmb_model.set("AUTO: Best Matching Architecture")
        self.cmb_model.pack(side=tk.LEFT, padx=8)

        self.btn_predict = tk.Button(
            scroll_content,
            text="RUN DERMA-GUARD PREDICTION",
            bg="#16a34a",
            fg="#ffffff",
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self._on_predict_click
        )
        self.btn_predict.pack(fill=tk.X, padx=pad, pady=(15, 20))

    def _build_right_results(self, parent):
        pad = 14

        lbl_header = tk.Label(parent, text="DIAGNOSTIC FINDINGS & EVIDENCE REPORT", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_header.pack(anchor="w", padx=pad, pady=(pad, 8))

        # Big Badge Card
        self.card_result = tk.Frame(parent, bg="#f8fafc", bd=1, relief=tk.SOLID)
        self.card_result.pack(fill=tk.X, padx=pad, pady=4)

        self.lbl_diag_title = tk.Label(self.card_result, text="Primary Diagnosis: --", font=("Segoe UI", 16, "bold"), fg="#1e293b", bg="#f8fafc")
        self.lbl_diag_title.pack(anchor="w", padx=14, pady=(10, 2))

        self.lbl_confidence = tk.Label(self.card_result, text="Confidence Score: --", font=("Segoe UI", 11), fg="#475569", bg="#f8fafc")
        self.lbl_confidence.pack(anchor="w", padx=14, pady=2)

        self.lbl_conformal = tk.Label(self.card_result, text="95% Conformal Set: -- | Uncertainty: --", font=("Segoe UI", 10, "bold"), fg="#2563eb", bg="#f8fafc")
        self.lbl_conformal.pack(anchor="w", padx=14, pady=(2, 10))

        # Probability Distribution
        lbl_dist = tk.Label(parent, text="Class Probability Distribution:", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#334155")
        lbl_dist.pack(anchor="w", padx=pad, pady=(10, 4))

        self.prob_frame = tk.Frame(parent, bg="#ffffff")
        self.prob_frame.pack(fill=tk.X, padx=pad, pady=2)
        self.prob_bars = {}

        classes = ["BCC", "ACK", "NEV", "SEK", "SCC", "MEL"]
        for idx, c in enumerate(classes):
            row = tk.Frame(self.prob_frame, bg="#ffffff")
            row.pack(fill=tk.X, pady=2)
            lbl_name = tk.Label(row, text=f"{c}:", width=5, anchor="w", font=("Segoe UI", 9, "bold"), bg="#ffffff")
            lbl_name.pack(side=tk.LEFT)

            pbar = ttk.Progressbar(row, orient="horizontal", length=220, mode="determinate")
            pbar.pack(side=tk.LEFT, padx=6)

            lbl_val = tk.Label(row, text="0.0%", width=8, anchor="w", font=("Segoe UI", 9), bg="#ffffff")
            lbl_val.pack(side=tk.LEFT)

            self.prob_bars[c] = (pbar, lbl_val)

        # Clinical Advice Box
        lbl_adv = tk.Label(parent, text="Evidence-Based Medical Decision Protocol:", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#334155")
        lbl_adv.pack(anchor="w", padx=pad, pady=(12, 4))

        self.txt_advice = scrolledtext.ScrolledText(parent, height=11, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief=tk.SOLID)
        self.txt_advice.pack(fill=tk.BOTH, expand=True, padx=pad, pady=(2, pad))
        self.txt_advice.insert(tk.END, "Enter patient details on the left panel and click 'RUN DERMA-GUARD PREDICTION' to generate an auditable clinical report.")
        self.txt_advice.configure(state="disabled")

    def _browse_image(self):
        initial_dir = os.path.join(PROJECT_ROOT, "data", "images")
        if not os.path.isdir(initial_dir):
            initial_dir = PROJECT_ROOT

        f = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select Cutaneous Lesion Photograph",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.webp")]
        )
        if f and os.path.isfile(f):
            self.selected_image_path = f
            self.lbl_img_path.config(text=f, fg="#0284c7")
            self._render_preview(f)

    def _load_sample_image(self):
        candidates = [
            os.path.join(PROJECT_ROOT, "data", "images", "PAT_46_881_939.png"),
            os.path.join(PROJECT_ROOT, "data", "images", "PAT_1516_1765_530.png")
        ]
        for c in candidates:
            if os.path.isfile(c):
                self.selected_image_path = c
                self.lbl_img_path.config(text=c, fg="#0284c7")
                self._render_preview(c)
                return
        messagebox.showinfo("Sample", "Please browse to select an image from your dataset.")

    def _render_preview(self, path):
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((200, 150))
            self.tk_img = ImageTk.PhotoImage(img)
            self.canvas_img_preview.delete("all")
            self.canvas_img_preview.create_image(100, 75, image=self.tk_img)
        except Exception as e:
            print(f"[!] Preview failed: {e}")

    def _load_predictor_background(self):
        def worker():
            try:
                self.predictor = DermaGuardPredictor()
            except Exception as e:
                print(f"[!] Failed to initialize predictor: {e}")
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _on_predict_click(self):
        if self.predictor is None:
            messagebox.showinfo("Initializing", "Model checkpoints are currently loading from disk. Please wait a few seconds.")
            return

        # Parse Metadata
        meta = None
        try:
            age = int(self.ent_age.get().strip() or "50")
            gender = self.cmb_gender.get().strip() or "FEMALE"
            region = self.cmb_region.get().strip() or "FACE"
            d1 = float(self.ent_d1.get().strip() or "5.0")
            d2 = float(self.ent_d2.get().strip() or "4.0")
            fitz = int(self.ent_fitz.get().strip() or "2")

            meta = {
                'age': age,
                'gender': gender,
                'region': region,
                'diameter_1': d1,
                'diameter_2': d2,
                'fitspatrick': fitz,
                'itch': "TRUE" if self.var_itch.get() else "FALSE",
                'grew': "TRUE" if self.var_grew.get() else "FALSE",
                'bleed': "TRUE" if self.var_bleed.get() else "FALSE",
                'hurt': "TRUE" if self.var_hurt.get() else "FALSE",
                'elevation': "TRUE" if self.var_elevation.get() else "FALSE"
            }
        except Exception as e:
            messagebox.showerror("Input Error", f"Invalid metadata entry: {e}")
            return

        text = self.txt_notes.get("1.0", tk.END).strip()
        auto_text = self.var_auto_text.get()
        if not text and not auto_text:
            text = None

        img_path = self.selected_image_path

        # Model Code
        sel_mod = self.cmb_model.get()
        target_code = None
        if "Model " in sel_mod:
            target_code = sel_mod.split("Model ")[1][0]

        # Execute in background thread to keep GUI snappy
        self.btn_predict.config(state="disabled", text="Running Multimodal Diagnostic Inference...")
        
        def run_thread():
            try:
                res = self.predictor.predict(
                    image_path_or_pil=img_path,
                    metadata_dict=meta,
                    text_string=text,
                    auto_generate_text=auto_text,
                    target_model=target_code,
                    verbose=False
                )
                self.root.after(0, lambda: self._update_results(res))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Execution Error", str(e)))
            finally:
                self.root.after(0, lambda: self.btn_predict.config(state="normal", text="RUN DERMA-GUARD PREDICTION"))

        threading.Thread(target=run_thread, daemon=True).start()

    def _update_results(self, res):
        pred = res['primary_prediction']
        conf = res['confidence'] * 100.0
        c_set = res['prediction_set_95']
        unc = res['uncertainty_assessment'].get('uncertainty_level', 'LOW')

        # Color coding
        if pred in ['MEL', 'BCC', 'SCC']:
            badge_bg = "#fef2f2"
            title_fg = "#dc2626"
        else:
            badge_bg = "#f0fdf4"
            title_fg = "#16a34a"

        self.card_result.configure(bg=badge_bg)
        self.lbl_diag_title.configure(text=f"Primary Diagnosis: {pred}", fg=title_fg, bg=badge_bg)
        self.lbl_confidence.configure(text=f"Confidence Score: {conf:.2f}% | Model: {res['selected_model']}", bg=badge_bg)
        self.lbl_conformal.configure(text=f"95% Conformal Set: {c_set} | Uncertainty: {unc}", bg=badge_bg)

        # Update Progress Bars
        for c, p in res['class_probabilities'].items():
            if c in self.prob_bars:
                pbar, lbl_val = self.prob_bars[c]
                pbar['value'] = p * 100.0
                lbl_val.config(text=f"{p*100:.1f}%")

        # Update Clinical Advice
        advice_lines = generate_custom_clinical_advice(res)
        self.txt_advice.configure(state="normal")
        self.txt_advice.delete("1.0", tk.END)
        for line in advice_lines:
            self.txt_advice.insert(tk.END, line + "\n")
        self.txt_advice.configure(state="disabled")


def main():
    root = tk.Tk()
    app = DermaGuardGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()

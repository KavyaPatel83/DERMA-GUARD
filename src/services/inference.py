"""
website/engine.py — thin, thread-safe wrapper around the trained DERMA-GUARD
inference engine (Dummy/Project/predict.py) plus the helpers the website needs
(image quality check, triage logic, class metadata, benchmark loading).

The engine never fabricates predictions: if the trained models cannot be
loaded the API reports an error state instead of returning made-up output.
"""
from __future__ import annotations

import ast
import csv
import io
import math
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MODEL_PROJECT = ROOT / "Dummy" / "Project"
SAVED_MODELS = MODEL_PROJECT / "saved_models"
RAW_DATA = ROOT / "data" / "raw"

CLASS_INFO: Dict[str, Dict[str, Any]] = {
    "BCC": {
        "name": "Basal Cell Carcinoma", "group": "malignant", "severity": 3,
        "summary": "The most common skin cancer. Grows slowly and rarely spreads, "
                   "but needs treatment to prevent local tissue damage.",
        "features": "Pearly or waxy bump, visible blood vessels, a sore that bleeds and does not heal.",
    },
    "SCC": {
        "name": "Squamous Cell Carcinoma", "group": "malignant", "severity": 4,
        "summary": "A malignant tumour of the outer skin layer. Can spread if left "
                   "untreated, so early assessment matters.",
        "features": "Firm red nodule, scaly or crusted flat sore, often on sun-exposed skin.",
    },
    "MEL": {
        "name": "Melanoma", "group": "malignant", "severity": 5,
        "summary": "The most dangerous skin cancer. Highly treatable when found early, "
                   "which is why every suspected melanoma is escalated to a specialist.",
        "features": "Asymmetry, irregular border, several colours, diameter over 6 mm, evolving over time.",
    },
    "ACK": {
        "name": "Actinic Keratosis", "group": "pre-malignant", "severity": 2,
        "summary": "A rough, scaly patch caused by long-term sun exposure. "
                   "Some can progress to squamous cell carcinoma.",
        "features": "Rough, dry, scaly patch; may itch or sting; usually on face, scalp, hands.",
    },
    "NEV": {
        "name": "Melanocytic Nevus", "group": "benign", "severity": 1,
        "summary": "A common mole. Almost always harmless, but changes in size, "
                   "shape or colour should be checked.",
        "features": "Uniform colour, smooth round border, stable over time.",
    },
    "SEK": {
        "name": "Seborrheic Keratosis", "group": "benign", "severity": 1,
        "summary": "A harmless, wart-like growth that becomes more common with age.",
        "features": "Waxy, 'stuck-on' appearance, tan to dark brown, well-defined edge.",
    },
}

CLASS_ORDER = ["BCC", "ACK", "NEV", "SEK", "SCC", "MEL"]
MODALITY_LABEL = {"image": "Lesion image", "metadata": "Patient metadata", "text": "Clinical text"}

MODEL_REQUIRES = {
    "A": ("image",), "B": ("metadata",), "C": ("text",),
    "D": ("image", "metadata"), "E": ("image", "text"), "F": ("metadata", "text"),
    "G": ("image", "metadata", "text"),
}

METADATA_FIELDS = [
    "age", "gender", "region", "diameter_1", "diameter_2", "fitspatrick",
    "itch", "grew", "hurt", "changed", "bleed", "elevation",
    "smoke", "drink", "pesticide", "skin_cancer_history", "cancer_history",
]
BOOL_FIELDS = {"itch", "grew", "hurt", "changed", "bleed", "elevation",
               "smoke", "drink", "pesticide", "skin_cancer_history", "cancer_history"}


# --------------------------------------------------------------------------- #
# Inference engine
# --------------------------------------------------------------------------- #
class Engine:
    def __init__(self) -> None:
        self.state = "idle"            # idle | loading | ready | error
        self.error: Optional[str] = None
        self.load_seconds: Optional[float] = None
        self.device: Optional[str] = None
        self._predictor = None
        self.calib: Dict[str, Any] = {}
        self.measured: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

    # -- lifecycle ---------------------------------------------------------- #
    def start(self) -> None:
        """Begin loading the models in the background (idempotent)."""
        if self._thread is not None:
            return
        self.state = "loading"
        self._thread = threading.Thread(target=self._load, daemon=True, name="engine-loader")
        self._thread.start()

    def _load(self) -> None:
        t0 = time.time()
        try:
            if str(MODEL_PROJECT) not in sys.path:
                sys.path.insert(0, str(MODEL_PROJECT))
            from predict import DermaGuardPredictor  # noqa: WPS433 (deferred heavy import)

            self._predictor = DermaGuardPredictor(saved_models_dir=str(SAVED_MODELS))
            self.device = str(self._predictor.device)
            self._load_calibration()
            # Warm every candidate model so the first real request is fast.
            self._warmup()
            self.state = "ready"
        except Exception as exc:  # pragma: no cover - environment dependent
            self.state = "error"
            self.error = f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
        finally:
            self.load_seconds = round(time.time() - t0, 1)

    def _load_calibration(self) -> None:
        """Temperature scaling + conformal thresholds fitted on rows never used for training."""
        from src.services import honest_eval as evaluation
        res = evaluation.load()
        if res is None:
            res = evaluation.run(self._predictor)
        self.calib = res["live_calibration"]
        self.measured = {c: {"heldout_accuracy": m["heldout"]["accuracy"], "ci95": m["heldout"]["accuracy_ci95"],
                             "reported_accuracy": m["reported_accuracy"], "ece_before": m["eval_half_ece_before"],
                             "ece_after": m["eval_half_ece_after"], "text_dependent": m["text_dependent"]}
                         for c, m in res["models"].items()}
        self.calib_n = res["meta"]["n_heldout"]

    def _warmup(self) -> None:
        img = Image.new("RGB", (224, 224), (150, 110, 100))
        meta = {"age": 55, "gender": "FEMALE", "region": "NECK", "diameter_1": 6.0,
                "diameter_2": 5.0, "fitspatrick": 3}
        self._predictor.predict(image_path_or_pil=img, metadata_dict=meta,
                                text_string="55 year old female with a lesion on the neck.",
                                verbose=False)

    def status(self) -> Dict[str, Any]:
        return {"state": self.state, "error": self.error, "device": self.device,
                "load_seconds": self.load_seconds}

    # -- inference ---------------------------------------------------------- #
    def predict(self, image: Optional[Image.Image], metadata: Optional[Dict[str, Any]],
                text: Optional[str], auto_text: bool = False,
                target_model: Optional[str] = None) -> Dict[str, Any]:
        if self.state != "ready":
            raise RuntimeError(self.error or "Models are still loading.")
        t0 = time.time()
        with self._lock:  # the torch modules are shared; serialise requests
            raw = self._predictor.predict(
                image_path_or_pil=image,
                metadata_dict=metadata or None,
                text_string=text or None,
                auto_generate_text=auto_text,
                target_model=target_model or None,
                verbose=False,
            )
        result = enrich(raw, self.calib, self.measured)
        result["inference_seconds"] = round(time.time() - t0, 2)
        return result


# --------------------------------------------------------------------------- #
# Result post-processing
# --------------------------------------------------------------------------- #
def _gate_kind(gate: str) -> str:
    g = (gate or "").upper()
    if "INSUFFICIENT" in g:
        return "insufficient"
    if "ACQUIRE" in g:
        return "acquire"
    return "proceed"


def triage(raw: Dict[str, Any]) -> Dict[str, Any]:
    """4-level consensus hierarchy (ACCEPT / ARBITRATE / ACQUIRE / ESCALATE).

    Implemented at the website layer from the engine's own outputs: the evidence
    gate, cross-model agreement, calibrated confidence and the conformal set.
    """
    primary = raw["primary_prediction"]
    conf = float(raw["confidence"])
    gate = _gate_kind(raw["evidence_manager"]["decision_gate"])
    cand = raw.get("candidate_models", {})
    agree = sum(1 for c in cand.values() if c["predicted_class"] == primary)
    total = max(len(cand), 1)
    agreement = agree / total
    pset: List[str] = raw.get("prediction_set_95", [primary])
    hidden_malignant = (CLASS_INFO[primary]["group"] != "malignant"
                        and any(CLASS_INFO[c]["group"] == "malignant" for c in pset if c != primary))

    reasons: List[str] = []
    if gate == "insufficient":
        action, level = "ESCALATE", 4
        reasons.append("Evidence sufficiency fell below 0.30 — the inputs are not enough to decide safely.")
    elif hidden_malignant:
        action, level = "ESCALATE", 4
        reasons.append("A malignant class is inside the conformal set although the top prediction is benign.")
    elif gate == "acquire":
        action, level = "ACQUIRE", 3
        reasons.append("Evidence sufficiency is borderline (0.30–0.50) — more or better input is recommended.")
    elif conf >= 0.80 and agreement >= 0.75:
        action, level = "ACCEPT", 1
        reasons.append(f"{agree}/{total} candidate models agree with confidence ≥ 80%.")
    elif conf >= 0.50:
        action, level = "ARBITRATE", 2
        reasons.append("Models broadly agree but confidence is moderate — clinician arbitration advised.")
    else:
        action, level = "ACQUIRE", 3
        reasons.append("Confidence is below 50% — additional evidence is needed.")

    if CLASS_INFO[primary]["group"] == "malignant" and action == "ACCEPT":
        reasons.append("Predicted class is malignant — specialist confirmation is still required.")

    return {"action": action, "level": level, "agreement": agreement,
            "models_agree": agree, "models_total": total, "reasons": reasons,
            "malignant_in_set": any(CLASS_INFO[c]["group"] == "malignant" for c in pset)}


def suggestions(raw: Dict[str, Any], tri: Dict[str, Any]) -> List[str]:
    """Concrete, actionable follow-ups derived from the evidence profile."""
    ev = raw["evidence_manager"]
    active = set(raw["active_modalities"])
    out: List[str] = []
    for m in ("image", "metadata", "text"):
        if m not in active:
            out.append({
                "image": "Add a clear, well-lit close-up photograph of the lesion.",
                "metadata": "Add patient details (age, body site, size, symptoms) to enable the metadata models.",
                "text": "Add a short symptom description to enable the text models.",
            }[m])
    for m in active:
        q = ev["quality"].get(m, 1.0)
        if q < 0.5:
            out.append({
                "image": "Image quality is low — retake the photo in good light, in focus, filling the frame.",
                "metadata": "Many metadata fields are missing — completing them improves reliability.",
                "text": "The description is short or vague — mention location, duration, size and symptoms.",
            }[m])
    if tri["action"] in ("ESCALATE", "ARBITRATE"):
        out.append("Book a dermatology consultation; dermoscopy or biopsy is the definitive next step.")
    if not out:
        out.append("Evidence is sufficient. Keep monitoring the lesion and re-check if it changes.")
    return out


def _scale(probs: Dict[str, float], T: float) -> Dict[str, float]:
    v = np.array([probs[c] for c in CLASS_ORDER], dtype=float)
    z = np.log(np.clip(v, 1e-9, 1)) / max(T, 1e-3)
    z -= z.max()
    e = np.exp(z)
    e /= e.sum()
    return {c: float(x) for c, x in zip(CLASS_ORDER, e)}


def enrich(raw: Dict[str, Any], calib: Optional[Dict[str, Any]] = None,
           measured: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Post-process an engine result: temperature-scale probabilities, rebuild the conformal set
    from a threshold calibrated on held-out data, then derive triage from the calibrated numbers."""
    calib, measured = calib or {}, measured or {}
    primary_code = raw["selected_model"].replace("Model ", "")
    cal_note = None

    cand_raw = raw.get("candidate_models", {})
    cand_cal: Dict[str, Dict[str, Any]] = {}
    for code, v in cand_raw.items():
        T = calib.get(code, {}).get("temperature", 1.0)
        pr = _scale(v["probabilities"], T)
        top = max(pr, key=pr.get)
        ent = -sum(p * math.log(p + 1e-9) for p in pr.values()) / math.log(6.0)
        cand_cal[code] = {**v, "probabilities": pr, "predicted_class": top, "confidence": pr[top], "entropy": ent}

    T0 = calib.get(primary_code, {}).get("temperature", 1.0)
    probs = cand_cal[primary_code]["probabilities"] if primary_code in cand_cal else _scale(raw["class_probabilities"], T0)
    top = max(probs, key=probs.get)
    conf = probs[top]
    q = calib.get(primary_code, {}).get("qhat90")
    if q is not None:
        pset = [c for c in sorted(probs, key=lambda c: -probs[c]) if probs[c] >= 1 - q] or [top]
        if top not in pset:
            pset.insert(0, top)
        cal_note = {"temperature": T0, "coverage": "90%", "n_calibration": measured and None}
        coverage = "90%"
    else:
        pset = list(raw["prediction_set_95"]); coverage = raw["uncertainty_assessment"].get("coverage_guarantee", "95%")

    size = len(pset)
    uncertainty = ("LOW (single credible class)" if size == 1 else
                   f"MODERATE ({size} plausible classes)" if size <= 3 else f"HIGH ({size} of 6 classes remain plausible)")
    advice = (f"Calibrated model considers {', '.join(pset)} plausible at the {coverage} level. "
              + ("A clinician should assess this lesion." if size > 1 else "Single credible class, still requires clinical confirmation."))

    shim = dict(raw)
    shim["primary_prediction"] = top
    shim["confidence"] = conf
    shim["prediction_set_95"] = pset
    shim["candidate_models"] = {k: {**v, "predicted_class": v["predicted_class"]} for k, v in cand_cal.items()}
    tri = triage(shim)
    ranked = sorted(probs.items(), key=lambda kv: -kv[1])
    ev = raw["evidence_manager"]
    info = CLASS_INFO[top]
    shim_for_sugg = shim
    result = {
        "selected_model": raw["selected_model"],
        "active_modalities": raw["active_modalities"],
        "diagnosis": {"code": top, "name": info["name"], "group": info["group"], "summary": info["summary"],
                      "features": info["features"], "confidence": float(conf)},
        "ranking": [{"code": c, "name": CLASS_INFO[c]["name"], "group": CLASS_INFO[c]["group"], "probability": float(p)} for c, p in ranked],
        "conformal": {"set": pset, "size": size, "uncertainty": uncertainty, "advice": advice, "coverage": coverage},
        "calibration": {"temperature": T0, "applied": q is not None,
                        "heldout_accuracy": measured.get(primary_code, {}).get("heldout_accuracy"),
                        "heldout_ci95": measured.get(primary_code, {}).get("ci95"),
                        "reported_accuracy": measured.get(primary_code, {}).get("reported_accuracy")},
        "evidence": {"quality": ev["quality"], "reliability": ev["reliability"], "utility": ev["utility"],
                     "scores": ev["evidence_scores"], "weights": ev["dynamic_fusion_weights"],
                     "consistency": ev["consistency"], "sufficiency": ev["sufficiency"],
                     "gate": ev["decision_gate"], "action": ev["clinical_action"]},
        "candidates": [
            {"code": k, "name": v["name"], "modality": v["modality"], "predicted": v["predicted_class"],
             "confidence": v["confidence"], "evidence_score": v["evidence_score"], "entropy": v["entropy"],
             "probabilities": v["probabilities"],
             "heldout_accuracy": measured.get(k, {}).get("heldout_accuracy"),
             "text_dependent": measured.get(k, {}).get("text_dependent", False)}
            for k, v in cand_cal.items()],
        "triage": tri,
        "suggestions": suggestions(shim_for_sugg, tri),
        "generated_text": raw.get("text_generated"),
    }
    return result


# --------------------------------------------------------------------------- #
# Image quality pre-check (independent of the model; instant)
# --------------------------------------------------------------------------- #
def image_quality(img: Image.Image) -> Dict[str, Any]:
    arr = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean() / 255.0)
    contrast = float(gray.std() / 255.0)

    sharp_score = float(np.clip(blur / 150.0, 0, 1))
    light_score = float(np.clip(1.0 - 2.0 * abs(brightness - 0.5), 0, 1))
    contrast_score = float(np.clip(contrast / 0.20, 0, 1))
    res_score = float(np.clip(min(h, w) / 224.0, 0, 1))
    overall = 0.35 * sharp_score + 0.25 * light_score + 0.2 * contrast_score + 0.2 * res_score

    checks = [
        {"key": "sharpness", "label": "Sharpness", "score": sharp_score,
         "hint": "Blurry — hold the camera steady and tap to focus." if sharp_score < 0.45 else "In focus."},
        {"key": "lighting", "label": "Lighting", "score": light_score,
         "hint": ("Too dark — move to brighter, even light." if brightness < 0.3 else
                  "Too bright — avoid flash glare." if brightness > 0.75 else "Good exposure.")},
        {"key": "contrast", "label": "Contrast", "score": contrast_score,
         "hint": "Flat image — lesion may blend into the skin." if contrast_score < 0.4 else "Good contrast."},
        {"key": "resolution", "label": "Resolution", "score": res_score,
         "hint": f"{w}×{h}px — too small, move closer." if res_score < 1 else f"{w}×{h}px."},
    ]
    verdict = "good" if overall >= 0.65 else "fair" if overall >= 0.4 else "poor"
    return {"overall": float(overall), "verdict": verdict, "width": w, "height": h, "checks": checks}


# --------------------------------------------------------------------------- #
# Benchmarks (parsed from the artefacts the training script saved)
# --------------------------------------------------------------------------- #
def load_benchmarks() -> Dict[str, Any]:
    path = SAVED_MODELS / "models_benchmark_summary.csv"
    models = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            cm = ast.literal_eval(row["confusion_matrix"])
            models.append({
                "code": row["code"], "name": row["name"], "modality": row["modality"],
                "accuracy": float(row["accuracy"]),
                "precision": float(row["precision_macro"]),
                "sensitivity": float(row["sensitivity_macro"]),
                "specificity": float(row["specificity_macro"]),
                "f1": float(row["f1_macro"]),
                "auc": float(row["auc_macro"]),
                "auprc": float(row["auprc_macro"]),
                "confusion_matrix": cm,
                "test_size": int(row["dataset_test"]),
            })
    ds = models[0] if models else {}
    return {
        "models": models,
        "classes": CLASS_ORDER,
        "split": {"total": 2298, "train": 1953, "val": 229, "test": 459},
        "warning": ("Script-reported figures: the 'test' split is contained in the training set and probabilities were "
                    "adjusted to hit target accuracies. Use /api/evaluation for held-out measurements."),
    }


def load_dataset_stats() -> Dict[str, Any]:
    import pandas as pd
    df = pd.read_csv(RAW_DATA / "metadata.csv")
    def vc(col: str) -> Dict[str, int]:
        return {str(k): int(v) for k, v in df[col].dropna().value_counts().items()}
    ages = df["age"].dropna()
    bins = list(range(0, 100, 10))
    hist = np.histogram(ages, bins=bins + [120])[0]
    age_hist = {f"{b}-{b+9}": int(c) for b, c in zip(bins, hist)}
    return {
        "total": int(len(df)),
        "patients": int(df["patient_id"].nunique()),
        "classes": {c: int(df[df["diagnostic"] == c].shape[0]) for c in CLASS_ORDER},
        "region": vc("region"),
        "gender": vc("gender"),
        "fitzpatrick": {str(int(float(k))): v for k, v in vc("fitspatrick").items()},
        "age": age_hist,
        "age_mean": float(ages.mean()),
    }


# --------------------------------------------------------------------------- #
# Sample case library
# --------------------------------------------------------------------------- #
def _clean_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Build the metadata dict the model expects from a dataset row.

    Deliberately excludes the diagnosis, ids and the `biopsed` flag.
    """
    out: Dict[str, Any] = {}
    for k in METADATA_FIELDS:
        v = row.get(k)
        if v is None:
            continue
        if isinstance(v, float) and np.isnan(v):
            continue
        s = str(v).strip()
        if s in ("", "UNK", "nan", "None"):
            continue
        if k in BOOL_FIELDS:
            out[k] = "TRUE" if s.upper() in ("TRUE", "1", "1.0") else "FALSE"
        elif k in ("age", "diameter_1", "diameter_2"):
            out[k] = float(v)
        elif k == "fitspatrick":
            out[k] = int(float(v))
        else:
            out[k] = s.upper()
    return out


def build_samples(per_class: int = 4, seed: int = 7) -> List[Dict[str, Any]]:
    import pandas as pd
    df = pd.read_csv(RAW_DATA / "metadata.csv")
    img_dir = RAW_DATA / "images"
    samples: List[Dict[str, Any]] = []
    for code in CLASS_ORDER:
        sub = df[(df["diagnostic"] == code) & df["age"].notna() & df["region"].notna()]
        sub = sub[sub["img_id"].map(lambda f: (img_dir / f).exists())]
        for _, r in sub.sample(n=min(per_class, len(sub)), random_state=seed).iterrows():
            meta = _clean_row(r.to_dict())
            samples.append({
                "img_id": r["img_id"], "truth": code,
                "truth_name": CLASS_INFO[code]["name"], "group": CLASS_INFO[code]["group"],
                "metadata": meta,
                "label": f"{int(r['age'])}y · {str(r['gender']).title() if isinstance(r['gender'], str) else 'N/A'} · {str(r['region']).title()}",
            })
    return samples


def pil_from_bytes(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    img.load()
    return img.convert("RGB")


# --------------------------------------------------------------------------- #
# Lesion segmentation + morphology (classical, no extra model weights)
# --------------------------------------------------------------------------- #
def morphology(img: Image.Image, save_overlay: Optional[Path] = None, _return_mask: bool = False) -> Dict[str, Any]:
    """Segment the lesion by colour distance from the surrounding skin and measure its shape.

    Method: Lab colour distance to the median border-ring colour -> Gaussian blur -> Otsu ->
    morphological clean-up -> connected component closest to the centre. All geometric values are
    in pixels (no physical scale is available unless a reference object is present).
    Irregularity is a *descriptive* feature only; it must not be read as a malignancy rule.
    """
    arr = np.array(img.convert("RGB"))
    h0, w0 = arr.shape[:2]
    scale = min(1.0, 512.0 / max(h0, w0))
    small = cv2.resize(arr, (int(w0 * scale), int(h0 * scale)), interpolation=cv2.INTER_AREA) if scale < 1 else arr
    h, w = small.shape[:2]
    out: Dict[str, Any] = {"status": "failed", "model_version": "classical-seg-v1", "physical_scale_available": False,
                           "image_px": [w0, h0],
                           "note": "Geometric descriptors only; irregularity is not a diagnostic rule."}
    lab = cv2.cvtColor(small, cv2.COLOR_RGB2LAB).astype(np.float32)
    ring = np.zeros((h, w), bool)
    b = max(int(0.1 * min(h, w)), 4)
    ring[:b, :] = ring[-b:, :] = ring[:, :b] = ring[:, -b:] = True
    ref = np.median(lab[ring], axis=0)
    dist = np.sqrt(((lab - ref) ** 2).sum(2))
    dist = cv2.GaussianBlur(dist, (0, 0), max(h, w) / 160.0)
    d8 = np.clip(dist / max(dist.max(), 1e-6) * 255, 0, 255).astype(np.uint8)
    ks = max(3, int(min(h, w) / 60)) | 1
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks))
    bw = None
    try:   # GrabCut seeded from a central prior; border ring is definite background
        gs = 256.0 / max(h, w)
        gsm = cv2.resize(small, (max(int(w * gs), 32), max(int(h * gs), 32)), interpolation=cv2.INTER_AREA)
        gh, gw = gsm.shape[:2]
        gmask = np.full((gh, gw), cv2.GC_PR_BGD, np.uint8)
        yy, xx = np.ogrid[:gh, :gw]
        nrm = ((xx - gw / 2) / (0.34 * gw)) ** 2 + ((yy - gh / 2) / (0.34 * gh)) ** 2
        gmask[nrm <= 1.0] = cv2.GC_PR_FGD
        gmask[((xx - gw / 2) / (0.10 * gw)) ** 2 + ((yy - gh / 2) / (0.10 * gh)) ** 2 <= 1.0] = cv2.GC_FGD
        gb = max(int(0.06 * min(gh, gw)), 2)
        gmask[:gb, :] = gmask[-gb:, :] = gmask[:, :gb] = gmask[:, -gb:] = cv2.GC_BGD
        bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
        cv2.grabCut(cv2.cvtColor(gsm, cv2.COLOR_RGB2BGR), gmask, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
        fg = ((gmask == cv2.GC_FGD) | (gmask == cv2.GC_PR_FGD)).astype(np.uint8)
        bw = cv2.resize(fg, (w, h), interpolation=cv2.INTER_LINEAR_EXACT if hasattr(cv2, "INTER_LINEAR_EXACT") else cv2.INTER_LINEAR) * 255
        bw = (cv2.GaussianBlur(bw.astype(np.float32), (0, 0), max(h, w) / 90.0) > 127).astype(np.uint8) * 255
    except Exception:
        bw = None
    if bw is None or bw.sum() == 0:       # fallback: colour-distance Otsu
        _, bw = cv2.threshold(d8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bw = cv2.morphologyEx(cv2.morphologyEx(bw, cv2.MORPH_OPEN, k), cv2.MORPH_CLOSE, k)
    n, labels, stats, cents = cv2.connectedComponentsWithStats(bw)
    best, best_score = None, 0.0
    diag = math.hypot(h, w)
    for i in range(1, n):
        a = stats[i, cv2.CC_STAT_AREA]
        if a < 0.004 * h * w:
            continue
        d = math.hypot(cents[i][0] - w / 2, cents[i][1] - h / 2) / diag
        score = a * math.exp(-(d / 0.30) ** 2)
        if score > best_score:
            best, best_score = i, score
    if best is None:
        return out
    mask = (labels == best).astype(np.uint8)
    mask = (cv2.GaussianBlur(mask.astype(np.float32), (0, 0), max(h, w) / 140.0) > 0.5).astype(np.uint8)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cnt = max(cnts, key=cv2.contourArea)
    mask = np.zeros_like(mask)
    cv2.drawContours(mask, [cnt], -1, 1, -1)
    area = float(mask.sum())
    per = float(cv2.arcLength(cnt, True))
    hull = cv2.convexHull(cnt)
    hull_area, hull_per = float(cv2.contourArea(hull)), float(cv2.arcLength(hull, True))
    circ = float(min(1.0, 4 * math.pi * area / (per ** 2))) if per > 0 else 0.0
    (_cx, _cy), (rw, rh), _ang = cv2.minAreaRect(cnt)

    # asymmetry: IoU of the mask with its mirror image about both principal axes
    m = cv2.moments(mask, binaryImage=True)
    mu20, mu02, mu11 = m["mu20"] / m["m00"], m["mu02"] / m["m00"], m["mu11"] / m["m00"]
    theta = 0.5 * math.atan2(2 * mu11, mu20 - mu02)
    cx0, cy0 = m["m10"] / m["m00"], m["m01"] / m["m00"]
    S = int(2 * max(rw, rh)) + 8
    M = cv2.getRotationMatrix2D((cx0, cy0), math.degrees(theta), 1.0)
    M[0, 2] += S / 2 - cx0
    M[1, 2] += S / 2 - cy0
    aligned = cv2.warpAffine(mask, M, (S, S), flags=cv2.INTER_NEAREST) > 0

    def iou(a, b2):
        u = (a | b2).sum()
        return float((a & b2).sum() / u) if u else 1.0
    asym = 1.0 - 0.5 * (iou(aligned, aligned[:, ::-1]) + iou(aligned, aligned[::-1, :]))

    inside = lab[mask > 0]
    col_std = inside.std(0)
    dom: List[Dict[str, Any]] = []
    try:
        data = small[mask > 0].astype(np.float32)
        if len(data) > 50:
            crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 15, 1.0)
            _, lab_k, centers = cv2.kmeans(data, 3, None, crit, 3, cv2.KMEANS_PP_CENTERS)
            share = np.bincount(lab_k.ravel(), minlength=3) / len(lab_k)
            for j in np.argsort(-share):
                r, g, bb = centers[j].astype(int)
                dom.append({"hex": f"#{r:02x}{g:02x}{bb:02x}", "share": float(share[j])})
    except Exception:
        pass

    ring_out = cv2.dilate(mask, k, iterations=3) - mask
    contrast = float(dist[mask > 0].mean() - (dist[ring_out > 0].mean() if ring_out.any() else 0.0))
    touches = float(mask[0, :].any() or mask[-1, :].any() or mask[:, 0].any() or mask[:, -1].any())
    frac = area / (h * w)
    quality = float(np.clip(0.5 * np.clip(contrast / 12.0, 0, 1) + 0.3 * (1 - touches)
                            + 0.2 * (1.0 if 0.01 < frac < 0.7 else 0.3), 0, 1))
    inv = 1.0 / (scale * scale)
    out.update({
        "status": "success" if quality >= 0.5 else "low_quality",
        "area_px": round(area * inv), "area_fraction": round(frac, 4), "perimeter_px": round(per / scale, 1),
        "diameter_px": round(max(rw, rh) / scale, 1), "circularity": round(circ, 3),
        "convexity": round(hull_per / per, 3) if per else None,
        "solidity": round(area / hull_area, 3) if hull_area else None,
        "asymmetry": round(asym, 3), "colour_variation": round(float(col_std.mean()), 2),
        "dominant_colours": dom, "segmentation_quality": round(quality, 3), "touches_border": bool(touches),
    })
    if _return_mask:
        out["_mask"] = mask.astype(bool)
    if save_overlay is not None:
        ov = arr.copy()
        c_full = (cnt.astype(np.float32) / scale).astype(np.int32)
        cv2.drawContours(ov, [c_full], -1, (13, 148, 136), max(2, int(max(h0, w0) / 160)))
        Image.fromarray(ov).save(save_overlay)
        out["overlay"] = True
    return out


# --------------------------------------------------------------------------- #
# Cost-aware evidence acquisition (greedy utility-minus-cost ranking)
# --------------------------------------------------------------------------- #
ACQ_LAMBDA = 0.015   # penalty per cost unit
ACQ_MU = 0.008       # penalty per day of delay
ACQ_COST = {  # (cost units, delay days)
    "retake_photo": (1, 0.0), "add_details": (1, 0.0), "add_description": (1, 0.0),
    "clinician_review": (3, 2.0), "dermoscopy": (5, 3.0), "biopsy": (10, 7.0),
}


def acquisition_plan(result: Dict[str, Any], morph: Optional[Dict[str, Any]], measured: Dict[str, Any]) -> Dict[str, Any]:
    """Rank follow-up actions by  E[dV] - lambda*cost - mu*delay.

    E[dV] for adding a modality is the *measured* held-out accuracy difference between the matching
    model configurations (text-dependent configs are excluded: that pipeline is unvalidated).
    Other actions use transparent heuristics proportional to current uncertainty (flagged 'heuristic').
    This is the greedy baseline of the acquisition ladder, not a learned policy.
    """
    active = set(result["active_modalities"])
    unc = 1.0 - result["diagnosis"]["confidence"]
    acc = {c: v.get("heldout_accuracy") for c, v in measured.items() if not v.get("text_dependent")}
    code_for = {frozenset(["image"]): "A", frozenset(["metadata"]): "B", frozenset(["image", "metadata"]): "D"}
    cur = acc.get(code_for.get(frozenset(active & {"image", "metadata"})), None)

    def gain(add_m: str) -> Optional[float]:
        new = code_for.get(frozenset((active & {"image", "metadata"}) | {add_m}))
        if cur is None or new is None or acc.get(new) is None:
            return None
        return acc[new] - cur

    q_img = result["evidence"]["quality"].get("image", 1.0) if "image" in active else None
    seg_q = (morph or {}).get("segmentation_quality")
    actions: List[Dict[str, Any]] = []

    def add(key, label, dv, basis, why, applicable=True):
        cost, delay = ACQ_COST[key]
        actions.append({"action": key, "label": label, "delta_v": round(float(dv), 4), "cost": cost,
                        "delay_days": delay, "basis": basis, "rationale": why, "applicable": applicable,
                        "score": round(float(dv) - ACQ_LAMBDA * cost - ACQ_MU * delay, 4)})

    if "image" not in active:
        g = gain("image")
        add("retake_photo", "Add a lesion photograph", g if g is not None else 0.0,
            "measured held-out gain" if g is not None else "unavailable",
            "Measured accuracy change from adding the image modality to the current inputs.")
    elif (q_img is not None and q_img < 0.8) or (seg_q is not None and seg_q < 0.6):
        poor = max(1 - (q_img or 1), 1 - (seg_q or 1))
        add("retake_photo", "Retake a sharper, evenly lit photo", 0.5 * poor * unc, "heuristic",
            "Image quality / segmentation confidence is below target; improving it shrinks uncertainty roughly in proportion.")
    if "metadata" not in active:
        g = gain("metadata")
        add("add_details", "Add patient details (age, site, size, symptoms)", g if g is not None else 0.0,
            "measured held-out gain" if g is not None else "unavailable",
            "Measured accuracy change from adding the metadata modality.")
    if "text" not in active:
        add("add_description", "Add a written description", 0.0, "unvalidated",
            "The text pipeline could not be validated against saved weights, so no gain is claimed.")
    add("clinician_review", "Doctor review in the portal", 0.4 * unc, "heuristic",
        "A human reviewer resolves part of the model's uncertainty.")
    add("dermoscopy", "Dermoscopy at clinic", 0.55 * unc, "heuristic",
        "Magnified pigment and vessel patterns reduce ambiguity between look-alike classes.")
    add("biopsy", "Biopsy and histopathology", 0.95 * unc, "heuristic",
        "Definitive diagnosis; resolves almost all remaining uncertainty at highest cost and delay.")
    actions.sort(key=lambda a: -a["score"])
    top = next((a for a in actions if a["score"] > 0), None)
    return {"policy": "greedy utility-minus-cost (ladder rung 2)", "lambda": ACQ_LAMBDA, "mu": ACQ_MU,
            "current_uncertainty": round(unc, 3), "ranked": actions,
            "recommended": top["action"] if top else None,
            "recommended_label": top["label"] if top else "No additional evidence is worth its cost",
            "note": "Gains marked 'heuristic' are proportional assumptions, not measured effects."}


def lesion_mask(img: Image.Image) -> Optional[np.ndarray]:
    """Boolean lesion mask at the image's own resolution (None when segmentation fails)."""
    import tempfile
    arr = np.array(img.convert("RGB"))
    h0, w0 = arr.shape[:2]
    out = morphology(img, None, _return_mask=True)
    m = out.pop("_mask", None)
    if m is None:
        return None
    return cv2.resize(m.astype(np.uint8), (w0, h0), interpolation=cv2.INTER_NEAREST) > 0


def simulate_growth(img: Image.Image, mask: Optional[np.ndarray], growth: float) -> Image.Image:
    """SIMULATED follow-up: magnify the image about the lesion centroid so lesion area changes by `growth`.

    This is a synthetic transformation (background is magnified too) used only to exercise the
    longitudinal pipeline; it is not a model of real lesion growth.
    """
    arr = np.array(img.convert("RGB"))
    h, w = arr.shape[:2]
    if mask is not None and mask.any():
        ys, xs = np.nonzero(mask)
        cx, cy = float(xs.mean()), float(ys.mean())
    else:
        cx, cy = w / 2.0, h / 2.0
    s = math.sqrt(max(1.0 + growth, 0.05))            # linear scale from area ratio
    M = np.array([[s, 0, cx - s * cx], [0, s, cy - s * cy]], dtype=np.float32)
    warped = cv2.warpAffine(arr, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return Image.fromarray(warped)

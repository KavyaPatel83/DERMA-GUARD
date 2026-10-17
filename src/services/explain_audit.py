"""
src/services/explain_audit.py — explanation consistency auditor (v5.0 module 5).

Occlusion-sensitivity audit of the image-only model (Model A) for one case:
  1. mask each cell of a 4x4 grid with the image's mean colour and measure the drop in the
     probability of the case's predicted class  -> attribution map;
  2. compare where the attribution mass falls against the segmented lesion mask;
  3. test stability of the prediction under benign transforms (flip, +/-10% brightness).

A heat-map is evidence about *this model's* sensitivity, not proof of clinical reasoning;
thresholds below are provisional and have not been calibrated against known shortcut artefacts.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps

GRID = 4


def _prob(engine, img: Image.Image, code: str) -> float:
    r = engine.predict(img, None, None, auto_text=False, target_model="A")
    return next(x["probability"] for x in r["ranking"] if x["code"] == code)


def audit_image(engine, thumb_path: Path, predicted_code: str, mask: np.ndarray | None,
                overlay_path: Path | None = None) -> Dict[str, Any]:
    img = Image.open(thumb_path).convert("RGB")
    w, h = img.size
    base_res = engine.predict(img, None, None, auto_text=False, target_model="A")
    base_top = base_res["diagnosis"]["code"]            # the image model's OWN top class
    base = next(x["probability"] for x in base_res["ranking"] if x["code"] == predicted_code)
    arr = np.array(img)
    mean_col = tuple(int(v) for v in arr.reshape(-1, 3).mean(0))

    drops = np.zeros((GRID, GRID))
    for gy in range(GRID):
        for gx in range(GRID):
            occ = img.copy()
            box = (gx * w // GRID, gy * h // GRID, (gx + 1) * w // GRID, (gy + 1) * h // GRID)
            occ.paste(mean_col, box)
            drops[gy, gx] = max(0.0, base - _prob(engine, occ, predicted_code))

    total = float(drops.sum())
    overlap = None
    if mask is not None and total > 1e-6:
        m = cv2.resize(mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) > 0
        inside = 0.0
        for gy in range(GRID):
            for gx in range(GRID):
                cell = m[gy * h // GRID:(gy + 1) * h // GRID, gx * w // GRID:(gx + 1) * w // GRID]
                if cell.size and cell.mean() >= 0.25:        # cell substantially covers lesion
                    inside += drops[gy, gx]
        overlap = inside / total

    variants = {"horizontal flip": ImageOps.mirror(img), "vertical flip": ImageOps.flip(img),
                "brightness -10%": ImageEnhance.Brightness(img).enhance(0.9),
                "brightness +10%": ImageEnhance.Brightness(img).enhance(1.1)}
    shifts, same = [], 0
    for name, v in variants.items():
        r = engine.predict(v, None, None, auto_text=False, target_model="A")
        top = r["diagnosis"]["code"]
        same += int(top == base_top)
        shifts.append(abs(next(x["probability"] for x in r["ranking"] if x["code"] == predicted_code) - base))
    stability = same / len(variants)

    flags = []
    max_drop = float(drops.max())
    if max_drop < 0.03:
        flags.append("diffuse_attribution")
    if overlap is not None and total > 0.05 and overlap < 0.40:
        flags.append("background_reliance")
    if stability < 0.75:
        flags.append("unstable_under_benign_transforms")

    if overlay_path is not None:
        hm = drops / (drops.max() + 1e-9)
        hm = cv2.resize((hm * 255).astype(np.uint8), (w, h), interpolation=cv2.INTER_CUBIC)
        hm = cv2.applyColorMap(hm, cv2.COLORMAP_INFERNO)[:, :, ::-1]
        Image.fromarray((0.55 * arr + 0.45 * hm).astype(np.uint8)).save(overlay_path)

    return {
        "audit_version": "occlusion-v1", "audited_model": "Model A (image-only)", "predicted_class": predicted_code, "image_model_top_class": base_top,
        "baseline_probability": round(base, 3), "grid": GRID,
        "attribution": [[round(float(x), 3) for x in row] for row in drops],
        "max_drop": round(max_drop, 3), "lesion_region_overlap": None if overlap is None else round(overlap, 3),
        "background_reliance": None if overlap is None else round(1 - overlap, 3),
        "stability": round(stability, 2), "mean_probability_shift": round(float(np.mean(shifts)), 3),
        "status": "review_required" if flags else "ok", "flags": flags,
        "caveat": "Occlusion sensitivity of the image-only model; thresholds are provisional and uncalibrated.",
    }

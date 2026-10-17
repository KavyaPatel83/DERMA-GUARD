"""
src/services/stress_runner.py — DERMA-STRESS against the live models.

Re-uses the project's own corruption functions (src/stress/corruption.py). Cases are drawn from
the patient-disjoint held-out rows only (never used to train), so degradation numbers are not
polluted by memorisation.

Scope notes (kept in the output):
  * the live system has one image modality, so `miss_dermo` is not applicable;
  * the text pipeline is unvalidated, so text corruptions are reported as not applicable;
  * `compound_multi` is run as blur_severe + noise_mild + missing metadata (the original listed
    components include text).
"""
from __future__ import annotations

import random
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

import numpy as np
from PIL import Image

from src.services import db, honest_eval
from src.services import inference as eng

NOT_APPLICABLE = {
    "miss_dermo": "single image modality in the live system",
    "miss_text": "text modality is not used in the stress baseline (unvalidated pipeline)",
    "contradict_text": "text pipeline unvalidated",
    "vague_text": "text pipeline unvalidated",
    "hallucination_text": "text pipeline unvalidated",
}


def _tensor(img: Image.Image):
    import torchvision.transforms.functional as TF
    return TF.to_tensor(img)


def _pil(t):
    import torchvision.transforms.functional as TF
    return TF.to_pil_image(t.clamp(0, 1))


def _select_cases(n: int, seed: int = 13) -> List[Dict[str, Any]]:
    import pandas as pd
    y, df, _tr, _te, _va, _held, held_pd = honest_eval.splits()
    rng = random.Random(seed)
    rows = []
    by_class: Dict[int, List[int]] = {}
    for i in held_pd:
        r = df.iloc[int(i)]
        if not (eng.RAW_DATA / "images" / r["img_id"]).exists() or pd.isna(r["age"]) or pd.isna(r["region"]):
            continue
        by_class.setdefault(int(y[i]), []).append(int(i))
    per = max(1, n // max(len(by_class), 1))
    for cls, idxs in by_class.items():
        rng.shuffle(idxs)
        rows += idxs[:per]
    rng.shuffle(rows)
    cases = []
    for i in rows[:n]:
        r = df.iloc[i].to_dict()
        cases.append({"index": i, "img_id": r["img_id"], "truth": honest_eval.NAMES[int(y[i])],
                      "metadata": eng._clean_row(r)})
    return cases


def _apply(cond: str, case: Dict[str, Any], pool: List[Dict[str, Any]], rng: random.Random):
    """Return (image, metadata, applicable_note)."""
    from src.stress import corruption as C
    img = Image.open(eng.RAW_DATA / "images" / case["img_id"]).convert("RGB")
    img.thumbnail((640, 640))
    meta = dict(case["metadata"])
    others = [c for c in pool if c["img_id"] != case["img_id"]]
    if cond == "clean":
        return img, meta
    if cond == "miss_clinical":
        return None, meta
    if cond == "miss_metadata":
        return img, None
    if cond in ("blur_mild", "blur_severe"):
        return _pil(C.corrupt_blur(_tensor(img), 5 if cond == "blur_mild" else 15)), meta
    if cond in ("noise_mild", "noise_severe"):
        import torch
        torch.manual_seed(1)
        return _pil(C.corrupt_noise(_tensor(img), 0.05 if cond == "noise_mild" else 0.2)), meta
    if cond == "brightness_low":
        return _pil(C.corrupt_brightness(_tensor(img), 0.5)), meta
    if cond == "jpeg_heavy":
        return _pil(C.corrupt_jpeg(_tensor(img), 10)), meta
    if cond == "occlusion":
        return _pil(C.corrupt_occlusion(_tensor(img), 0.20)), meta
    if cond == "wrong_metadata":
        o = rng.choice(others)
        return img, dict(o["metadata"])
    if cond == "dermo_swap":
        o = rng.choice(others)
        im2 = Image.open(eng.RAW_DATA / "images" / o["img_id"]).convert("RGB")
        im2.thumbnail((640, 640))
        return im2, meta
    if cond == "metadata_poison":
        diff = [c for c in others if c["truth"] != case["truth"]] or others
        return img, dict(rng.choice(diff)["metadata"])
    if cond == "compound_multi":
        import torch
        torch.manual_seed(1)
        t = C.corrupt_noise(C.corrupt_blur(_tensor(img), 15), 0.05)
        return _pil(t), None
    raise KeyError(cond)


def _run(job_id: str, engine, n_cases: int, conditions: Optional[List[str]]) -> None:
    from src.stress.corruption import CORRUPTION_CONDITIONS
    try:
        cases = _select_cases(n_cases)
        all_conds = [c["id"] for c in CORRUPTION_CONDITIONS]
        wanted = [c for c in (conditions or all_conds) if c in all_conds]
        order = ["clean"] + [c for c in wanted if c != "clean"]
        total = len(order) * len(cases)
        done = 0
        rng = random.Random(5)
        results: Dict[str, Any] = {}
        meta_by_id = {c["id"]: c for c in CORRUPTION_CONDITIONS}
        malignant = {"BCC", "SCC", "MEL"}
        clean_pred: Dict[str, str] = {}
        for cond in order:
            if cond in NOT_APPLICABLE:
                results[cond] = {"id": cond, "name": meta_by_id[cond]["name"], "category": meta_by_id[cond]["category"],
                                 "applicable": False, "reason": NOT_APPLICABLE[cond]}
                done += len(cases)
                continue
            rows = []
            for case in cases:
                img, meta = _apply(cond, case, cases, rng)
                if img is None and not meta:
                    continue
                r = engine.predict(img, meta or None, None, auto_text=False, target_model=None)
                d, t = r["diagnosis"], r["triage"]
                rows.append({"img_id": case["img_id"], "truth": case["truth"], "pred": d["code"], "conf": d["confidence"],
                             "action": t["action"], "sufficiency": r["evidence"]["sufficiency"], "set": r["conformal"]["set"],
                             "model": r["selected_model"]})
                if cond == "clean":
                    clean_pred[case["img_id"]] = d["code"]
                done += 1
                db.run("UPDATE stress_runs SET progress=? WHERE id=?", (done / total, job_id))
            n = len(rows)
            if n == 0:
                results[cond] = {"id": cond, "applicable": False, "reason": "no valid cases"}
                continue
            correct = [x["pred"] == x["truth"] for x in rows]
            decided = [x for x in rows if x["action"] in ("ACCEPT", "ARBITRATE")]
            unsafe = [x for x in rows if x["truth"] in malignant and x["pred"] not in malignant and x["action"] == "ACCEPT"]
            results[cond] = {
                "id": cond, "name": meta_by_id.get(cond, {"name": "Clean"})["name"] if cond != "clean" else "Clean (no corruption)",
                "category": meta_by_id.get(cond, {"category": "baseline"})["category"] if cond != "clean" else "baseline",
                "applicable": True, "n": n, "accuracy": float(np.mean(correct)),
                "mean_confidence": float(np.mean([x["conf"] for x in rows])),
                "mean_sufficiency": float(np.mean([x["sufficiency"] for x in rows])),
                "abstention_rate": float(np.mean([x["action"] in ("ACQUIRE", "ESCALATE") for x in rows])),
                "accepted_rate": float(len(decided) / n),
                "selective_risk": float(np.mean([x["pred"] != x["truth"] for x in decided])) if decided else None,
                "unsafe_acceptance": int(len(unsafe)),
                "prediction_changed": float(np.mean([clean_pred.get(x["img_id"]) != x["pred"] for x in rows])) if cond != "clean" else 0.0,
                "mean_set_size": float(np.mean([len(x["set"]) for x in rows])),
            }
        db.run("UPDATE stress_runs SET status='complete', progress=1, results=? WHERE id=?",
               (db.jdump({"cases": len(cases), "results": results,
                          "notes": ["Cases are patient-disjoint held-out rows (n small; CIs are wide).",
                                    "Single image modality: miss_dermo not applicable.",
                                    "Text corruptions not applicable: text pipeline unvalidated.",
                                    "compound_multi = blur_severe + noise_mild + missing metadata."]}), job_id))
    except Exception as exc:  # report, never crash the server
        db.run("UPDATE stress_runs SET status='error', error=? WHERE id=?", (f"{type(exc).__name__}: {exc}", job_id))


def start(engine, user_id: int, n_cases: int = 24, conditions: Optional[List[str]] = None) -> str:
    job_id = uuid.uuid4().hex[:10]
    db.run("INSERT INTO stress_runs(id,created,user_id,status,progress,params) VALUES (?,?,?,?,?,?)",
           (job_id, time.time(), user_id, "running", 0.0, db.jdump({"n_cases": n_cases, "conditions": conditions or "all"})))
    threading.Thread(target=_run, args=(job_id, engine, n_cases, conditions), daemon=True, name=f"stress-{job_id}").start()
    return job_id

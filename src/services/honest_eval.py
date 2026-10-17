"""
website/evaluation.py — honest re-evaluation of the trained models.

Why this exists
---------------
The benchmark numbers produced by Dummy/Project/train_all.py are NOT measurements:
  * the "test" index set is drawn with the same seed as, and is entirely contained in,
    the training set (459/459 rows), and
  * evaluate_and_report_model() rewrites predicted probabilities until accuracy equals a
    hard-coded target per model (MODEL_TARGET_ACC).
This module recomputes everything from the saved weights on rows that were never used for
gradient updates ("held-out", n=345; patient-disjoint subset n=132), and derives temperature
scaling, split-conformal thresholds, risk-coverage and subgroup metrics from them.

Limitations (kept visible in the output):
  * the held-out set is small (MEL n=8); intervals are wide;
  * rows from the same patient may sit in both train and held-out (patient-disjoint subset
    reported separately);
  * the saved text pipeline could not be reproduced from cached features (model C scores
    ~chance even on training rows), so text-dependent results are marked unvalidated.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJ = ROOT / "Dummy" / "Project"
OUT = ROOT / "outputs" / "portal" / "honest_eval.json"
NAMES = ["BCC", "ACK", "NEV", "SEK", "SCC", "MEL"]
MALIGNANT = {0, 4, 5}
REPORTED = {"A": .8562, "B": .8410, "C": .8344, "D": .8845, "E": .8802, "F": .8736, "G": .8976}
FEATS = {"A": ("img",), "B": ("meta",), "C": ("txt",), "D": ("img", "meta"), "E": ("img", "txt"),
         "F": ("txt", "meta"), "G": ("img", "txt", "meta")}


# --------------------------------------------------------------------------- #
# metrics
# --------------------------------------------------------------------------- #
def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    conf, pred = p.max(1), p.argmax(1)
    e = 0.0
    for lo in np.linspace(0, 1, bins, endpoint=False):
        m = (conf > lo) & (conf <= lo + 1 / bins)
        if m.any():
            e += m.mean() * abs((pred[m] == y[m]).mean() - conf[m].mean())
    return float(e)


def brier(p: np.ndarray, y: np.ndarray) -> float:
    oh = np.eye(p.shape[1])[y]
    return float(((p - oh) ** 2).sum(1).mean())


def temperature_scale(p: np.ndarray, T: float) -> np.ndarray:
    z = np.log(np.clip(p, 1e-9, 1)) / T
    z -= z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def fit_temperature(p: np.ndarray, y: np.ndarray) -> float:
    best, best_nll = 1.0, 1e9
    for T in np.exp(np.linspace(np.log(0.5), np.log(8.0), 60)):
        q = temperature_scale(p, T)
        nll = -np.log(np.clip(q[np.arange(len(y)), y], 1e-9, 1)).mean()
        if nll < best_nll:
            best, best_nll = float(T), nll
    return best


def conformal_q(p: np.ndarray, y: np.ndarray, alpha: float) -> float:
    n = len(y)
    s = 1.0 - p[np.arange(n), y]
    level = min(1.0, math.ceil((n + 1) * (1 - alpha)) / n)
    return float(np.quantile(s, level, method="higher"))


def basic(p: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score
    pred = p.argmax(1)
    out: Dict[str, Any] = {"n": int(len(y)), "accuracy": float((pred == y).mean()),
                           "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
                           "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
                           "ece": ece(p, y), "brier": brier(p, y)}
    try:
        if len(set(y)) == p.shape[1] and min(np.bincount(y)) >= 2:
            out["auroc_macro"] = float(roc_auc_score(y, p, multi_class="ovr", average="macro"))
        else:
            out["auroc_macro"] = None
    except ValueError:
        out["auroc_macro"] = None
    mal_true = np.isin(y, list(MALIGNANT))
    mal_pred = np.isin(pred, list(MALIGNANT))
    out["malignant_sensitivity"] = float((mal_pred & mal_true).sum() / max(mal_true.sum(), 1))
    out["n_malignant"] = int(mal_true.sum())
    return out


def cluster_bootstrap_ci(stat, groups: np.ndarray, reps: int = 400, seed: int = 0) -> List[float]:
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    idx_by = {g: np.where(groups == g)[0] for g in uniq}
    vals = []
    for _ in range(reps):
        pick = rng.choice(uniq, len(uniq), replace=True)
        ix = np.concatenate([idx_by[g] for g in pick])
        vals.append(stat(ix))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


# --------------------------------------------------------------------------- #
# probabilities from saved weights
# --------------------------------------------------------------------------- #
def compute_probs(predictor) -> Dict[str, Dict[str, np.ndarray]]:
    """Forward all 2,298 cached feature rows through each saved model (raw + live stacked path)."""
    import torch
    import torch.nn.functional as F
    c = torch.load(PROJ / "saved_models" / "cached_multimodal_features.pt", map_location="cpu", weights_only=False)
    dev = predictor.device
    img, meta, text = c["img_feats"].to(dev), c["meta_feats"].to(dev), c["text_feats"].to(dev)
    qi, qm, qt = c["q_img"].to(dev), c["q_meta"].to(dev), c["q_text"].to(dev)
    out: Dict[str, Dict[str, np.ndarray]] = {}
    with torch.no_grad():
        ie, te = predictor.img_proj(img), predictor.text_proj(text)
        emb = {"img": ie.cpu().numpy(), "txt": te.cpu().numpy(), "meta": meta.cpu().numpy()}
        for code in "ABCDEFG":
            m = predictor._get_model(code)
            if code == "A": lg, _ = m(img_embed=ie)
            elif code == "B": lg, _ = m(meta_embed=meta)
            elif code == "C": lg, _ = m(text_embed=te)
            elif code == "D": lg, _, _ = m(img_embed=ie, meta_embed=meta, ev_img=qi, ev_meta=qm)
            elif code == "E": lg, _, _ = m(img_embed=ie, text_embed=te, ev_img=qi, ev_text=qt)
            elif code == "F": lg, _, _ = m(meta_embed=meta, text_embed=te, ev_meta=qm, ev_text=qt)
            else: lg, _, _ = m(img_embed=ie, meta_embed=meta, text_embed=te, ev_img=qi, ev_meta=qm, ev_text=qt)
            raw = F.softmax(lg, -1).cpu().numpy()
            stacked = raw.copy()
            sm = predictor._get_stacking_model(code)
            if sm is not None:
                X = np.hstack([emb[k] for k in FEATS[code]])
                try:
                    stacked = sm.predict_proba(X, p_neural=raw)
                    stacked = stacked / stacked.sum(1, keepdims=True)
                except Exception:
                    stacked = raw
            out[code] = {"raw": raw, "stacked": stacked}
    return out


def splits():
    import pandas as pd
    import torch
    from sklearn.model_selection import train_test_split
    c = torch.load(PROJ / "saved_models" / "cached_multimodal_features.pt", map_location="cpu", weights_only=False)
    y = c["labels"].numpy()
    n = len(y)
    df = pd.read_csv(PROJ / "data" / "metadata.csv")
    # identical calls to train_all.py
    idx_train, _ = train_test_split(np.arange(n), train_size=0.85, random_state=42, stratify=y)
    idx_test, _ = train_test_split(np.arange(n), train_size=0.20, random_state=42, stratify=y)
    idx_val, _ = train_test_split(np.arange(n), train_size=0.10, random_state=123, stratify=y)
    held = np.array(sorted(set(range(n)) - set(idx_train)))
    pat = df["patient_id"].values
    tr_pat = set(pat[idx_train])
    held_pd = np.array([i for i in held if pat[i] not in tr_pat])
    return y, df, idx_train, idx_test, idx_val, held, held_pd


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def run(predictor) -> Dict[str, Any]:
    y, df, idx_train, idx_test, idx_val, held, held_pd = splits()
    probs = compute_probs(predictor)
    pat = df["patient_id"].values
    n = len(y)
    tr, te, va = set(idx_train.tolist()), set(idx_test.tolist()), set(idx_val.tolist())

    meta: Dict[str, Any] = {
        "created": time.time(), "n_total": int(n), "n_train": len(tr), "n_reported_test": len(te), "n_reported_val": len(va),
        "reported_test_in_train": len(te & tr), "reported_val_in_train": len(va & tr),
        "reported_partition_sum": len(tr) + len(te) + len(va),
        "n_heldout": int(len(held)), "n_patient_disjoint": int(len(held_pd)),
        "heldout_classes": np.bincount(y[held], minlength=6).tolist(),
        "text_path_validated": False,
        "probability_source": "live path: raw neural softmax blended with stacking ensemble (alpha<=0.25)",
    }
    # patient-grouped 50/50 split of the held-out set: calibration vs evaluation
    rng = np.random.default_rng(7)
    hp = np.unique(pat[held])
    cal_p = set(rng.choice(hp, len(hp) // 2, replace=False).tolist())
    cal_ix = np.array([i for i in held if pat[i] in cal_p])
    ev_ix = np.array([i for i in held if pat[i] not in cal_p])
    meta["calibration_n"], meta["evaluation_n"] = int(len(cal_ix)), int(len(ev_ix))

    models: Dict[str, Any] = {}
    rc: Dict[str, Any] = {}
    reliab: Dict[str, Any] = {}
    conf: Dict[str, Any] = {}
    for code in "ABCDEFG":
        P = probs[code]["stacked"]
        raw = probs[code]["raw"]
        T = fit_temperature(P[cal_ix], y[cal_ix])
        Pc = temperature_scale(P, T)
        m: Dict[str, Any] = {
            "reported_accuracy": REPORTED[code],
            "train_rows_accuracy": float((P[idx_train].argmax(1) == y[idx_train]).mean()),
            "reported_test_rows_accuracy_raw": float((P[idx_test].argmax(1) == y[idx_test]).mean()),
            "heldout": basic(P, y)  if False else basic(P[held], y[held]),
            "heldout_calibrated": basic(Pc[held], y[held]),
            "patient_disjoint": basic(P[held_pd], y[held_pd]),
            "temperature": T,
            "eval_half_ece_before": ece(P[ev_ix], y[ev_ix]), "eval_half_ece_after": ece(Pc[ev_ix], y[ev_ix]),
            "text_dependent": "txt" in FEATS[code],
        }
        from sklearn.metrics import confusion_matrix
        cm = confusion_matrix(y[held], P[held].argmax(1), labels=list(range(6)))
        m["heldout"]["confusion_matrix"] = cm.tolist()
        m["heldout"]["per_class"] = [{"class": NAMES[i], "support": int(cm[i].sum()),
                                      "recall": float(cm[i, i] / max(cm[i].sum(), 1)),
                                      "precision": float(cm[i, i] / max(cm[:, i].sum(), 1))} for i in range(6)]
        m["heldout"]["accuracy_ci95"] = cluster_bootstrap_ci(lambda ix: float((P[held][ix].argmax(1) == y[held][ix]).mean()), pat[held])
        models[code] = m

        # risk-coverage on held-out, calibrated confidence
        pc = Pc[held]; yh = y[held]
        order = np.argsort(-pc.max(1))
        correct = (pc.argmax(1) == yh)[order]
        cum_err = np.cumsum(~correct)
        k = np.arange(1, len(yh) + 1)
        step = max(len(yh) // 40, 1)
        rc[code] = {"curve": [[float(k[i] / len(yh)), float(cum_err[i] / k[i]), float(pc.max(1)[order][i])] for i in range(step - 1, len(yh), step)],
                    "aurc": float(np.mean(cum_err / k))}
        # reliability diagram (calibrated vs raw) on held-out
        def bins(Pm):
            cf, pr = Pm[held].max(1), Pm[held].argmax(1)
            out = []
            for lo in np.linspace(0, 1, 10, endpoint=False):
                mm = (cf > lo) & (cf <= lo + .1)
                if mm.sum():
                    out.append([float(cf[mm].mean()), float((pr[mm] == y[held][mm]).mean()), int(mm.sum())])
            return out
        reliab[code] = {"before": bins(P), "after": bins(Pc)}
        # split-conformal: repeated patient-grouped cal/eval splits of held-out
        res = {}
        for alpha in (0.10, 0.05):
            covs, sizes, singles = [], [], []
            r = np.random.default_rng(11)
            for _ in range(200):
                cp = set(r.choice(hp, len(hp) // 2, replace=False).tolist())
                ci = np.array([i for i in held if pat[i] in cp]); ei = np.array([i for i in held if pat[i] not in cp])
                if len(ci) < 20 or len(ei) < 20:
                    continue
                q = conformal_q(Pc[ci], y[ci], alpha)
                sets = Pc[ei] >= (1 - q)
                sets[np.arange(len(ei)), Pc[ei].argmax(1)] = True
                covs.append(sets[np.arange(len(ei)), y[ei]].mean()); sizes.append(sets.sum(1).mean()); singles.append((sets.sum(1) == 1).mean())
            res[f"{int((1-alpha)*100)}"] = {"target": 1 - alpha, "coverage_mean": float(np.mean(covs)), "coverage_sd": float(np.std(covs)),
                                          "set_size_mean": float(np.mean(sizes)), "singleton_rate": float(np.mean(singles)),
                                          "qhat_live": conformal_q(Pc[held], y[held], alpha)}
        conf[code] = res

    # fairness on model G (calibrated), held-out rows
    def groups_for(df_):
        age = df_["age"].values.astype(float)
        region = df_["region"].astype(str).str.upper().values
        head = {"FACE", "NOSE", "EAR", "LIP", "SCALP", "NECK"}; trunk = {"CHEST", "BACK", "ABDOMEN"}
        fitz = df_["fitspatrick"].values.astype(float)
        return {
            "age": {"<40": age < 40, "40-59": (age >= 40) & (age < 60), "60-74": (age >= 60) & (age < 75), "75+": age >= 75},
            "sex": {"Female": (df_["gender"] == "FEMALE").values, "Male": (df_["gender"] == "MALE").values},
            "body site": {"Head & neck": np.isin(region, list(head)), "Trunk": np.isin(region, list(trunk)),
                          "Limbs": ~np.isin(region, list(head | trunk))},
            "Fitzpatrick type": {"I-II": fitz <= 2, "III+": fitz >= 3},
        }
    fair: Dict[str, Any] = {}
    for code in ("G", "A", "B"):
        Pc = temperature_scale(probs[code]["stacked"], models[code]["temperature"])
        q90 = conf[code]["90"]["qhat_live"]
        dfh = df.iloc[held].reset_index(drop=True)
        yh, ph, gh = y[held], Pc[held], pat[held]
        rows = []
        for gname, grp in groups_for(dfh).items():
            for lab, mask in grp.items():
                ix = np.where(mask)[0]
                if len(ix) == 0:
                    continue
                b = basic(ph[ix], yh[ix])
                sets = ph[ix] >= (1 - q90)
                sets[np.arange(len(ix)), ph[ix].argmax(1)] = True
                rows.append({"attribute": gname, "group": lab, "n": int(len(ix)), "accuracy": b["accuracy"],
                             "accuracy_ci95": cluster_bootstrap_ci(lambda s, ix=ix: float((ph[ix][s].argmax(1) == yh[ix][s]).mean()), gh[ix], reps=200),
                             "malignant_sensitivity": b["malignant_sensitivity"], "n_malignant": b["n_malignant"],
                             "mean_confidence": float(ph[ix].max(1).mean()), "low_confidence_rate": float((ph[ix].max(1) < 0.5).mean()),
                             "conformal_coverage_90": float(sets[np.arange(len(ix)), yh[ix]].mean()),
                             "conformal_set_size": float(sets.sum(1).mean()),
                             "reliable": bool(len(ix) >= 30)})
        fair[code] = rows

    result = {"meta": meta, "models": models, "risk_coverage": rc, "reliability": reliab, "conformal": conf, "fairness": fair,
              "live_calibration": {c: {"temperature": models[c]["temperature"], "qhat90": conf[c]["90"]["qhat_live"],
                                        "qhat95": conf[c]["95"]["qhat_live"]} for c in "ABCDEFG"}}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


def load() -> Dict[str, Any] | None:
    if OUT.exists():
        try:
            return json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(PROJ))
    from predict import DermaGuardPredictor
    r = run(DermaGuardPredictor(saved_models_dir=str(PROJ / "saved_models")))
    m = r["meta"]
    print(f"held-out n={m['n_heldout']} (patient-disjoint {m['n_patient_disjoint']}); wrote {OUT}")
    for c, v in r["models"].items():
        print(c, f"reported {v['reported_accuracy']:.3f} | held-out {v['heldout']['accuracy']:.3f} "
                 f"[{v['heldout']['accuracy_ci95'][0]:.2f},{v['heldout']['accuracy_ci95'][1]:.2f}] | T={v['temperature']:.2f} "
                 f"ECE {v['eval_half_ece_before']:.3f}->{v['eval_half_ece_after']:.3f} | 90%-set cov "
                 f"{r['conformal'][c]['90']['coverage_mean']:.3f} size {r['conformal'][c]['90']['set_size_mean']:.2f}")

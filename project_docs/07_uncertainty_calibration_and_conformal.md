# 07 — Uncertainty, Calibration, Conformal Prediction and Safety Logic

Code: `src/services/honest_eval.py`, `src/services/inference.py` (`enrich`, `triage`, `acquisition_plan`,
`morphology`), `Dummy/Project/models/conformal_prediction.py`.

## 1. Why uncertainty needs three layers

| Problem | Tool | Output |
|---------|------|--------|
| Softmax probabilities are over-confident | **Temperature scaling** | Calibrated probabilities |
| A single class label hides ambiguity | **Split conformal prediction** | A *set* of plausible classes with a coverage target |
| Numbers alone are not actionable | **Triage rules** | ACCEPT / ARBITRATE / ACQUIRE / ESCALATE |

## 2. Temperature scaling

```
p_cal = softmax( log(p) / T )
```
* One temperature `T` per model (A–G), fitted by grid search (60 values in [0.5, 8]) minimising negative log-likelihood
  on a **patient-grouped half** of the held-out rows.
* Evaluated on the *other* half to avoid optimistic bias.
* Measured effect (model G): **ECE 0.22 → 0.07**; for model A, `T ≈ 1.86` and ECE 0.23 → 0.057 on the evaluation half.
* Ranking is unchanged — only confidence is rescaled — so accuracy is not affected.

## 3. Split conformal prediction

Goal: a set `C(x)` such that `P(y ∈ C(x)) ≥ 1 − α` under exchangeability.

Algorithm (portal, α = 0.10):

1. Nonconformity score on calibration rows: `s_i = 1 − p̂(y_i | x_i)`.
2. Finite-sample quantile: `level = ⌈(n+1)(1−α)⌉ / n`, `q̂ = quantile(s, level, "higher")`.
3. Prediction set: all classes with `p̂(c | x) ≥ 1 − q̂`; the top class is always included.

Properties:
* Distribution-free, model-agnostic, cheap.
* Marginal (not per-class) guarantee; relies on exchangeability between calibration and future data.
* **Measured coverage:** ≈ 91 % empirical coverage at a 90 % target, averaged over 200 patient-grouped splits.
* **Set sizes:** because the models are only moderately accurate, sets are large (≈ 4 of 6 classes for image models,
  ≈ 1.7 for metadata-only) — the honest consequence of weak underlying models.

The original prototype used `ConformalPredictor` with α = 0.05 calibrated on the (contaminated) validation set; the
portal **replaces** it with the held-out calibration above (`conformal_calibrator.pt` is superseded).

## 4. Uncertainty categories shown to users

| Set size | Label |
|:--------:|-------|
| 1 | LOW (single credible class) |
| 2–3 | MODERATE (n plausible classes) |
| ≥ 4 | HIGH (n of 6 classes remain plausible) |

## 5. Triage — turning numbers into a safe action

See `06_...` §5.2 for the exact rule order. Design reasoning:

* **Safety rules come first.** Insufficient evidence and "hidden malignant in the set" escalate regardless of confidence.
* **ACCEPT is deliberately rare** (confidence ≥ 0.80 on the *calibrated* scale **and** ≥ 75 % candidate agreement).
* **Malignant predictions are never fully auto-accepted** — the reasons always add specialist confirmation.
* **Every ESCALATE / suspected-malignancy case** is flagged by the SafetyAgent and routed by the ReferralAgent.

## 6. Risk–coverage, subgroup and robustness metrics

`honest_eval.py` also produces (shown on the **Evidence & performance** page):

| Metric | Meaning |
|--------|---------|
| Accuracy, balanced accuracy, macro-F1 | Overall and class-balanced performance |
| Per-class recall / precision, confusion matrix | Especially SCC, MEL |
| Malignant sensitivity | Share of cancers called a malignant class |
| AUROC (macro) | Ranking quality |
| ECE, Brier | Calibration quality |
| Patient-level cluster bootstrap 95 % CI | Uncertainty of each number (cluster = patient) |
| Patient-disjoint subset (n = 132) | Stricter estimate without patient leakage |
| Risk–coverage curve | Error rate vs. fraction of cases answered when abstaining on least-confident ones |
| Subgroups | Age, sex, body site, Fitzpatrick type (groups < 30 flagged; skin tone is never inferred from images) |

## 7. Acquisition planning (what to do next)

Ranking rule:

```
score(action) = ΔV(action)  −  λ·cost(action)  −  μ·delay_days(action)
```

| Action | ΔV basis |
|--------|----------|
| Add photograph / add patient details | **Measured** held-out accuracy difference between the matching model configurations (A vs. B vs. D) |
| Retake sharper photo | Heuristic: `0.5 · poor_quality · uncertainty` |
| Written description | 0 — text pipeline unvalidated, so no gain is claimed |
| Doctor review in portal | Heuristic `0.4 · uncertainty` |
| Dermoscopy | Heuristic `0.55 · uncertainty` |
| Biopsy | Heuristic `0.95 · uncertainty` |

The output labels every ΔV as "measured held-out gain", "heuristic" or "unvalidated" so users can see which numbers are
real. It is a *greedy* rung of an acquisition ladder, not a learned policy.

## 8. Lesion morphology (classical image analysis)

`inference.morphology()` uses OpenCV **GrabCut** seeded from a central prior, then smooths the mask and measures:
area, perimeter, circularity, convexity, **asymmetry** (mirror IoU), colour variation, dominant colours and a
segmentation-quality score. Units are pixels. There is no learned U-Net, so no Dice/IoU claim is made. These are
ABCDE-style descriptors shown to the doctor and used to modulate the acquisition plan.

## 9. Longitudinal tracking (`/api/lesions/*`)

* Cases can be attached to a named **lesion** with an observation time.
* Follow-ups can be **simulated** (magnification about the lesion centroid) and are labelled as simulated.
* Change alerts use a 25 % area-growth threshold because a simulated +60 % growth was recovered as a median ×1.42
  (IQR 1.20–1.55); large lesions touching the frame are under-measured. No image registration is performed.

## 10. Explanation audit (`explain_audit.py`)

For image model A: 4×4 **occlusion sensitivity** (mask each cell with the mean colour and measure the drop in the
predicted class's probability), overlap of attribution mass with the segmented lesion, and stability under flips and
±10 % brightness. Thresholds are provisional; heat-maps show the *model's* sensitivity, not clinical reasoning.

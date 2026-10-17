# 11 — Evaluation, the Audit, and the Results (honest version)

Sources: `docs/evaluation_audit.md`, `outputs/portal/honest_eval.json`, `src/services/honest_eval.py`,
`Dummy/Project/train_all.py`.

> **One-sentence summary.** The first training script printed 84–90 % accuracy; the project's own audit showed those
> numbers were invalid and replaced them with measured held-out figures of ≈ 61–65 % (image models) and ≈ 78 %
> (metadata only). The website shows the measured numbers.

## 1. What was originally reported

| Model | Inputs | Reported accuracy |
|:----:|--------|------------------:|
| A | image | 85.6 % |
| B | metadata | 84.1 % |
| C | text | 83.4 % |
| D | image + metadata | 88.5 % |
| E | image + text | 88.0 % |
| F | text + metadata | 87.4 % |
| G | all three | 89.8 % (AUC ≈ 0.999) |

## 2. What the audit found

| # | Finding | Evidence |
|---|---------|----------|
| 1 | **Test set ⊂ training set** — train/test/val indices were drawn independently with the same seed and stratification | 459 / 459 "test" rows also in training; 195 / 229 "validation" rows in training; partitions sum to 2,641 for a dataset of 2,298 |
| 2 | **Accuracy forced to a target** — `evaluate_and_report_model()` swaps probabilities of borderline cases until accuracy equals a per-model constant (`MODEL_TARGET_ACC`) and per-epoch validation accuracy is clipped | Reported values equal the constants to six digits (e.g. 0.897603) |
| 3 | **Patient leakage** — several lesions per patient across splits | All 459 test rows belong to patients seen in training |

Consequence: saved weights score ≈ 99 % on the "test" rows (they were trained on them); the script then *lowered* that to
the preset target.

## 3. What the models really score

Held-out set: **n = 345** rows never used for gradient updates (BCC 127, ACK 109, NEV 37, SEK 35, SCC 29, MEL 8);
**132** from patients absent from training (patient-disjoint). Intervals: 95 % patient-level cluster bootstrap.

| Model | Reported | Train rows | **Held-out acc.** [95 % CI] | Patient-disjoint | Malignant sensitivity |
|:----:|---------:|-----------:|----------------------------:|-----------------:|----------------------:|
| A image | 85.6 % | 99.2 % | **61.4 %** [57–67] | 59.8 % | 0.77 |
| B metadata | 84.1 % | 95.3 % | **77.7 %** [73–82] | 74.2 % | 0.95 |
| C text | 83.4 % | 17.6 % ⚠ | 19.4 % ⚠ | 16.7 % | 0.09 |
| D image + meta | 88.5 % | 99.6 % | **64.6 %** [60–70] | 62.1 % | 0.80 |
| E image + text | 88.0 % | 99.1 % | 62.9 % ⚠ | 61.4 % | 0.78 |
| F meta + text | 87.4 % | 87.8 % | 73.3 % ⚠ | 69.7 % | 0.91 |
| G all | 89.8 % | 99.7 % | **64.3 %** [59–70] | 63.6 % | 0.79 |

(⚠ = depends on the text pipeline, which could not be validated.)

### Model A (image only) details, from `honest_eval.json`
accuracy 0.614, balanced accuracy 0.536, macro-F1 0.552, ECE 0.237 (raw) → 0.067 (calibrated), AUROC (macro) 0.823,
malignant sensitivity 0.768 (n = 164). Class recall: BCC 0.73, ACK 0.61, NEV 0.65, SEK 0.63, **SCC 0.10**, MEL 0.50 (n = 8).

## 4. How to read these numbers

* **Overfitting:** ≈ 99 % on training rows vs. ≈ 61–65 % held-out → the image branch memorises ≈ 35 points' worth.
* **Metadata beats the "full" model:** adding the image *currently hurts* on unseen rows (B 78 % vs. G 64 %).
* **Aggregate accuracy hides the dangerous classes:** SCC recall ≈ 7–10 %, MEL ≈ 50 % on 8 cases.
* **Text path unvalidated:** model C scores at/below chance even on its own training rows — the inference-time
  Bio_ClinicalBERT → projector path does not reproduce the features the model trained on.

## 5. What the website does about it

| Mitigation | Where |
|------------|-------|
| Shows measured next to originally-reported accuracy and labels the latter | `/api/evaluation`, **Evidence** page |
| Temperature-scaled live probabilities (ECE 0.22 → 0.07 for G) | `inference.enrich` |
| Conformal sets rebuilt from held-out threshold (≈ 91 % coverage at 90 % target) | `honest_eval` → `qhat90` |
| ACCEPT only at *calibrated* confidence ≥ 0.80 and agreement ≥ 75 % | `inference.triage` |
| Text-dependent models flagged unvalidated; text gain not claimed in acquisition | `acquisition_plan` |
| Agent "model score" uses held-out, not reported, accuracy | `score_agents` |

## 6. Limitations of the audit itself (stated by the project)

* Held-out set is small (345 rows, 8 melanomas) — intervals wide, subgroup results unstable.
* `idx_val` (used for best-epoch selection) overlaps ~34 held-out rows → small optimistic bias.
* 213 of the 345 held-out rows still share a patient with training; the 132-row patient-disjoint column is the stricter
  estimate.
* The conformal guarantee is marginal and assumes exchangeability with calibration rows.

## 7. Recommended fixes (documented, not applied to the training code)

1. One patient-grouped split (`GroupShuffleSplit` on `patient_id`), saved once, used for train/val/test.
2. Delete the target-accuracy adjustment and validation clamp; report raw outputs with CIs.
3. Re-derive text features with the *same* encoder as inference; require model C to beat the majority-class baseline.
4. Regularise / fine-tune the image branch or default to metadata-led fusion.
5. Re-run `python -m src.services.honest_eval` after retraining.

## 8. Second-generation results (final IEEE paper; MILK10k)

Reported in `docs/DERMA-GUARD_final_paper/main.tex` (not reproducible from this repository's data):

| Quantity | Value |
|----------|-------|
| Test set | 787 held-out MILK10k lesions (11 diagnoses), split by lesion, fusion/calibration fitted on validation only |
| Answered | 89.1 % of patients receive an answer; 57.1 % receive a **high-confidence** answer |
| High-confidence accuracy | 77.1 % over 11 diagnoses; **missed-cancer rate 3.1 %** |
| Baselines at equal coverage | learned rejector 4.9 % (p = 0.011), confidence thresholding 3.8 % |
| Stability across 4 fusion back-ends | policy 3.0–3.5 % vs. thresholding 3.5–9.3 % |
| External tests (no retraining) | safety target holds on PAD-UFES-20 and Derm7pt; fine-grained diagnosis does not transfer |
| Prototype re-scored on unseen patients | 57–75 % (vs. 84–90 % originally reported) |

## 9. Other evaluation material in the repository

| Item | Location |
|------|----------|
| Original benchmark figures (confusion matrices, curves, scorecard) | `Dummy/Project/saved_models/*.png`, `app/static/img/benchmark_*.png` |
| Statistics tooling (bootstrap CI, McNemar, Cohen's d, FDR) | `src/eval/stats.py` |
| Ablations (linear chain; 2⁴ factorial over Q,R,C,M) | `src/eval/ablation.py` |
| Metrics | `src/eval/metrics.py` |
| TensorBoard training curves | `outputs/logs/model_A … model_E` |

# Evaluation audit

*Scope: the benchmark numbers written by `Dummy/Project/train_all.py` (README table, `performance_metrics.txt`, `models_benchmark_summary.csv`).*
*Re-evaluation code: `src/services/honest_eval.py` · results: `outputs/portal/honest_eval.json` · shown live on the **Evidence** page.*

## Summary

The reported benchmark figures (85.6 % for the image model up to 89.8 % for the full multimodal model) are **not measurements of generalisation performance**. Two independent problems were found in the training script and one in the data handling:

| # | Finding | Where | Evidence |
|---|---------|-------|----------|
| 1 | The "test" set is contained in the training set | `train_all.py`, lines ~674-682 | `idx_train` (85 %) and `idx_test` (20 %) are drawn with the same seed and the same stratification, so the test indices are a subset of the training indices: **459 / 459 test rows are also training rows**. The 229 "validation" rows overlap training by 195 / 229. The three partitions sum to 2,641 for a dataset of 2,298 images. |
| 2 | Accuracy is forced to a hard-coded target | `evaluate_and_report_model()`, lines ~456-518 | `MODEL_TARGET_ACC = {G: 0.897603, D: 0.884532, ...}`; probabilities of the "most borderline" cases are swapped (`p_true*1.05`, `p_pred*0.95`) until accuracy equals the target. Validation accuracy per epoch is also clipped to a per-model ceiling (lines ~373-388). Reported figures equal the constants to six digits. |
| 3 | Patients appear in both train and test | `data/metadata.csv` has several lesions per patient | All 459 "test" rows belong to patients that also occur in training. |

Consequences: the saved weights score ~99 % on the "test" rows (they were trained on them); the script then lowers that to the target. The reported AUC ≈ 0.999 is likewise an artefact.

## What the models actually score

Rows **never used for gradient updates**: *n* = 345 (class counts BCC 127, ACK 109, NEV 37, SEK 35, SCC 29, MEL 8). Of these, 132 are from patients absent from training ("patient-disjoint").
Intervals are 95 % patient-level cluster bootstrap.

| Model | Inputs | Script-reported | Train rows | **Held-out** [95 % CI] | Patient-disjoint | Malignant sensitivity |
|-------|--------|----------------:|-----------:|------------------------:|-----------------:|----------------------:|
| A | image | 85.6 % | 99.2 % | **61.4 %** [57–67] | 59.8 % | 0.77 |
| B | metadata | 84.1 % | 95.3 % | **77.7 %** [73–82] | 74.2 % | 0.95 |
| C | text | 83.4 % | 17.6 % ⚠ | 19.4 % ⚠ | 16.7 % | 0.09 |
| D | image + metadata | 88.5 % | 99.6 % | **64.6 %** [60–70] | 62.1 % | 0.80 |
| E | image + text | 88.0 % | 99.1 % | 62.9 % ⚠ | 61.4 % | 0.78 |
| F | metadata + text | 87.4 % | 87.8 % | 73.3 % ⚠ | 69.7 % | 0.91 |
| G | all three | 89.8 % | 99.7 % | **64.3 %** [59–70] | 63.6 % | 0.79 |

Reading the table:

* The image-based models memorise the training set (≈ 99 %) and generalise at ≈ 61-65 %.
* **Metadata-only (B) generalises best** (≈ 78 %) and is *better* than the "full multimodal" model G (≈ 64 %). Adding the image currently *hurts* on unseen rows.
* SCC recall is ≈ 7 % and MEL recall ≈ 50 % (8 cases) for model G: aggregate accuracy hides weak performance on the dangerous classes.
* ⚠ **Text pipeline unvalidated.** Model C scores at or below chance even on its own training rows, so the text path used at inference (Bio_ClinicalBERT [CLS] → projector) does not reproduce the features the model was trained on, or the cached text features were produced differently. Any result involving text (C, E, F, G) should be treated as unvalidated until this is resolved.

## What the website does about it

* `/api/evaluation` and the **Evidence** page show measured numbers next to the script-reported ones and label the latter as such.
* Live predictions are **temperature-scaled** (T fitted on a patient-grouped half of the held-out rows; ECE 0.22 → 0.07 for model G) and conformal sets are rebuilt from a held-out threshold (≈ 91 % empirical coverage at a 90 % target, averaged over 200 patient-grouped splits). Because the models are weak, sets are large (≈ 4 of 6 classes for image models; ≈ 1.7 for metadata-only).
* Triage thresholds (ACCEPT ≥ 0.80 confidence) are applied to *calibrated* confidence, so ACCEPT is correctly rare.

## Limitations of this audit

* The held-out set is small (345 rows, 8 melanomas); intervals are wide and subgroup results are unstable.
* "Held-out" rows were excluded from gradient updates, but `idx_val` (used for best-epoch selection) overlaps them in ~34 rows; this is a minor optimistic bias.
* Patient-level leakage remains for 213 of the 345 held-out rows (their patient also appears in training); the 132-row patient-disjoint column is the stricter estimate.
* The conformal guarantee is marginal and assumes exchangeability with the calibration rows.

## Recommended fixes (not applied to your training code)

1. Create one **patient-grouped** split once (e.g. `GroupShuffleSplit` on `patient_id`), save it, and train/validate/test on disjoint partitions.
2. Delete the target-accuracy adjustment and the validation-accuracy clamp; report raw outputs with confidence intervals.
3. Re-derive text features with the same encoder used at inference and verify that model C beats the majority-class baseline on its own training data before using it.
4. Add regularisation / fine-tuning for the image branch (it currently overfits ≈ 35 points), or default to metadata-led fusion.
5. Re-run `python -m src.services.honest_eval` after retraining.

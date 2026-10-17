# 04 — Dataset and Data Pipeline

## 1. Datasets

### 1.1 PAD-UFES-20 (the dataset actually used by the live system)

| Property | Value |
|----------|-------|
| Origin | Federal University of Espírito Santo (UFES), Brazil — smartphone photos collected via the PAD programme |
| Licence | CC BY 4.0 (free, matches the "$0 cost" constraint) |
| Images | **2,298** clinical (smartphone) lesion photos, PNG, in `data/raw/images/` (copies also in `imgs_part_1..3`) |
| Metadata | `data/raw/metadata.csv`, **26 columns** per image |
| Task | 6-class diagnosis; also malignant vs. benign grouping |
| Biopsy-confirmed | A large share (field `biopsed`) |

**Class distribution (full dataset):**

| Code | Name | Group | Count | Share |
|------|------|-------|------:|------:|
| BCC | Basal Cell Carcinoma | malignant | 845 | 36.8 % |
| ACK | Actinic Keratosis | pre-malignant | 730 | 31.8 % |
| NEV | Melanocytic Nevus | benign | 244 | 10.6 % |
| SEK | Seborrheic Keratosis | benign | 235 | 10.2 % |
| SCC | Squamous Cell Carcinoma | malignant | 192 | 8.4 % |
| MEL | Melanoma | malignant | 52 | 2.3 % |

The imbalance is severe (MEL is the most dangerous but rarest class) — this drives the use of class weights, focal loss
and macro-averaged metrics.

**Metadata columns** (from `metadata.csv`):
`patient_id, lesion_id, smoke, drink, background_father, background_mother, age, pesticide, gender,
skin_cancer_history, cancer_history, has_piped_water, has_sewage_system, fitspatrick, region, diameter_1, diameter_2,
diagnostic, itch, grew, hurt, changed, bleed, elevation, img_id, biopsed`.

The website's form exposes 17 of these as inputs (`METADATA_FIELDS` in `src/services/inference.py`):
`age, gender, region, diameter_1, diameter_2, fitspatrick, itch, grew, hurt, changed, bleed, elevation, smoke, drink,
pesticide, skin_cancer_history, cancer_history`. The label (`diagnostic`) and identifiers are never model inputs.

### 1.2 Derm7pt (research pipeline only)

1,011 cases with clinical + dermoscopic images and the 7-point checklist; official split 413 / 203 / 395. Loader in
`src/data/derm7pt.py`. Used by the v4.0 research code and the paper's external test, **not** by the live portal.

### 1.3 MILK10k (final IEEE paper only)

5,240 lesions, each with a clinical close-up **and** dermoscopic image, 11 diagnoses. Used by the second-generation
experiments reported in `docs/DERMA-GUARD_final_paper/` (see `12_...`). The data itself is not in this repository.

## 2. Why PAD-UFES-20 for the live system

| Need | Why PAD-UFES-20 fits |
|------|----------------------|
| Free and open | CC BY 4.0, no credentials |
| Smartphone photos | Matches the "patient takes a photo at home" scenario (not only dermoscopy) |
| Rich metadata | Age, site, size, symptoms, risk factors → enables tabular and text modalities |
| Realistic imbalance | Includes the rare/dangerous classes (SCC, MEL) |
| Manageable size | 2,298 images train on a laptop; frozen backbone features can be cached |

## 3. Data pipeline step by step

```
data/raw/images/*.png ─┐
data/raw/metadata.csv ─┴─► scripts / train_all.py
                              │
         ┌────────────────────┼──────────────────────────────┐
         ▼                    ▼                              ▼
   IMAGE branch         METADATA branch                 TEXT branch
   resize/normalise     MetadataPreprocessor            text_generator.py
   ResNet50 → 2048-d    → 116 engineered features       synthetic narrative (≈137 words)
   (cached)             (cached)                        Bio_ClinicalBERT [CLS] 768-d (cached)
         └────────────────────┬──────────────────────────────┘
                              ▼
              cached_multimodal_features.pt  →  train projection heads + models A–G
```

### 3.1 Image preprocessing
* Train: resize/crop to 224×224, flips, rotation, colour jitter, ImageNet mean/std normalisation.
* Eval / inference: resize → centre-crop 224, ImageNet normalisation.
* Backbone: ImageNet ResNet50 (frozen) produces **2,048-d** features, cached to disk so experiments are fast.

### 3.2 Metadata preprocessing (`Dummy/Project/data/preprocessing.py`, `MetadataPreprocessor`)
Produces a **116-dimensional** engineered vector:

| Block | Examples |
|-------|----------|
| Demographics | standardised age, gender, Fitzpatrick phototype |
| Lesion geometry | d1, d2, log(area), aspect ratio d1/d2 |
| Symptoms (ABCDE-style) | itch, bleed, grew, hurt, changed, elevation |
| Interactions | `bleed_grew_interaction`, `hurt_bleed_interaction`, `sun_age_interaction`, `risk_ratio` |
| Anatomical region | one-hot over body regions |
| Risk heuristics | `melanoma_high_risk_flag`, `carcinoma_high_risk_flag`, per-class likelihood indices |
| Missingness | NaN-aware imputation; missing fraction feeds Q_meta |

The fitted preprocessor is saved as `saved_models/preprocessor.pkl` so inference applies identical statistics.

### 3.3 Synthetic clinical text (`Dummy/Project/data/text_generator.py`)
PAD-UFES-20 contains **no real clinical notes**. Text is synthesised from structured fields:

* `generate_synthetic_patient_narrative(row)` — first-person patient account;
* `generate_clinical_text(row, include_morphology)` — clinical-assertion style paragraph;
* `data/synthetic_texts.csv` stores the generated text (≈137 words per case in the prototype);
* `data/templates/text_templates.json` holds templates for the research text generator
  (`scripts/02_generate_texts.py`, which can also paraphrase via a local Ollama model).

**Leakage guard:** the diagnosis must never appear in the text. The research pipeline validates with a regex scan for
diagnosis terms and an embedding-diversity check.

**Caveat (important):** because the text is derived from the same metadata, text experiments are *optimistic* and
partly redundant with metadata. The honest audit also found the saved text path could not be reproduced (model C scores
below chance), so text-dependent results are flagged **unvalidated** on the website.

### 3.4 PTIS — Patient Text Information Score
`compute_ptis(text)` returns Q_text ∈ [0.1, 1]:

```
length_score  = min(words / 120, 1)
entity_score  = min(keyword_hits / 9, 1)      # 15 clinical keywords: lesion, phototype, bleeding, biopsy…
PTIS = 0.35 · length_score + 0.65 · entity_score
```
It measures *how informative* a description is, so vague text is down-weighted.

## 4. Splits (and the problem found in them)

| Item | Detail |
|------|--------|
| Prototype split (`train_all.py`) | 85 % train (1,953) / 20 % "test" (459) / 10 % "val" (229) drawn **independently** with the same seed from the same pool → sets overlap (459/459 test rows are in train) |
| Honest held-out set | 345 rows never used for gradient updates; 132 of them from patients absent from training ("patient-disjoint") |
| Frozen splits for research code | `data/processed/splits.json`, and `scripts/01_prepare_data.py` creates patient-grouped (`GroupShuffleSplit` by `patient_id`, seed 42) 70/15/15 splits |
| Recommended | One patient-grouped split created once, saved, and reused (documented in `docs/evaluation_audit.md`) |

Why *patient-grouped*? One patient can have several lesions/photos. If images of the same patient appear on both sides
of the split, the model can recognise the patient/skin context and the test score is inflated.

## 5. Data integrity tooling
* `scripts/dataset_audit.py` — SHA-256 and perceptual-hash (`imagehash.phash`) collision checks, class/missingness plots.
* `src/data/splits.py` and `tests/test_data_pipeline.py` — verify no patient appears in two splits.
* `src/services/honest_eval.py::audit_splits` (tested by `test_splits_audit_finds_the_leak`) — reproduces the overlap finding.

## 6. Data folders at a glance

| Path | Contents |
|------|----------|
| `data/raw/` | images + `metadata.csv` (original data, untouched) |
| `data/processed/splits.json` | saved split indices |
| `data/synthetic_texts.csv` | generated narratives |
| `data/templates/text_templates.json` | text-generation templates |
| `Dummy/Project/data/` | prototype copy of images/metadata, `metadata_with_clinical_text.csv`, `generated_clinical_texts.csv` |
| `Dummy/Project/saved_models/cached_multimodal_features.pt` | cached ResNet50 / BERT / metadata features |

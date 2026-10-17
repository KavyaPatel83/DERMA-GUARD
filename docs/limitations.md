# Limitations of DERMA-GUARD v4.0

This document lists known limitations of the DERMA-GUARD v4.0 system. These must be understood before interpreting any results.

## 1. Synthetic Text ≠ Real Clinical Text (PAD-UFES-20)

PAD-UFES-20 does not include free-text clinical notes. We generate synthetic patient narratives using Qwen2.5:7B-Instruct prompted with structured metadata fields. This synthetic text:
- Is based solely on 7 structured fields (age_bucket, body_location, grew, itch, bleed, changed, elevation)
- Does **not** capture the nuance, ambiguity, or clinical vocabulary of real patient narratives
- May have lower lexical diversity than real text
- Passes a regex leakage check, but may still implicitly encode diagnosis-correlated patterns

**Implication**: Performance on text-inclusive experiments on PAD-UFES-20 is likely **overoptimistic** compared to deployment with real clinical text.

## 2. Acquisition Policy is Simulated Only

The AcquisitionPolicy (Section 7 / Part 7) selects which additional modality to request. In DERMA-GUARD v4.0:
- Acquisition is a **recommendation** only — no actual new data is collected
- The uncertainty-reduction estimates are derived from held-out validation set statistics, not from real-world follow-up outcomes
- The cost function (image > dermoscopy > question) is manually defined, not learned from clinician preferences

**Implication**: Real-world active information gathering would require a live clinical workflow integration.

## 3. Conformal Coverage Replaced by Consensus Hierarchy

Earlier versions of this system used conformal prediction to guarantee coverage at a specified error rate. In DERMA-GUARD v4.0, conformal prediction is **replaced** by the 4-level consensus hierarchy. This means:
- Population-level coverage guarantees (from conformal prediction theory) **no longer apply**
- The consensus thresholds (confidence ≥ 0.80 for ACCEPT, etc.) are heuristic and dataset-specific
- Threshold recalibration is required for deployment on a new patient population

## 4. Results are Retrospective, Not Clinically Validated

All results in this project are computed on held-out test splits of public research datasets (PAD-UFES-20, Derm7pt). The system has:
- **Not** been validated on prospective clinical data
- **Not** been reviewed by board-certified dermatologists for clinical appropriateness
- **Not** been tested on rare skin conditions, dark skin tones, or paediatric cases beyond what appears in the test sets

**Do NOT use this system for any clinical decision-making.**

## 5. Single-GPU Training Constraints

All experiments were run on a single GPU. This imposes:
- Batch size limited to 32 (may affect batch normalization stability)
- No multi-GPU synchronization — batch statistics reflect single-GPU distributions
- Training time for 5 models × 100 epochs may be prohibitive without a modern GPU (≥ 24GB VRAM)

## 6. OOD Detector Sensitivity

The OOD detector uses Mahalanobis distance on class-conditional training embeddings. Its performance depends on:
- The quality and coverage of training embeddings
- The covariance matrix inversion being numerically stable (requires pseudoinverse if rank-deficient)
- The threshold calibrated on validation set — may not generalize to different patient populations

## 7. TTA Stability (S_m) Variance Scaling

The TTA stability score S_m = 1 - var(predictions under 5 augmentations) uses a heuristic scaling factor. The raw variance is typically in [0.001, 0.01] range; the multiplier of 100 maps it to a more useful [0, 1] range but is not theoretically grounded.

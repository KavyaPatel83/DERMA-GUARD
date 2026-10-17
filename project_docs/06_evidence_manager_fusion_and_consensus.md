# 06 — Evidence Manager, Adaptive Fusion and Consensus (the Core Novelty)

Code: `Dummy/Project/models/evidence_manager.py`, `adaptive_fusion.py`, `predict.py` (live path) and
`src/evidence/*`, `src/fusion/*`, `src/agents/devils_advocate.py` (research pipeline).

## 1. The idea

Most fusion treats every input as equally trustworthy. DERMA-GUARD asks, **per case and per modality**:

| Symbol | Question | How it is computed (live prototype) |
|:------:|----------|--------------------------------------|
| **Q** | Is this input good enough to use? | Image: MLP on 5 statistics (blur = Laplacian variance, brightness, contrast, resolution, border occlusion). Text: **PTIS**. Metadata: `1 − missing_fraction` |
| **R** | Can the model's output for this input be trusted? | Small MLP on `[Q, 1−entropy, 1−TTA-variance, cross-model agreement]` → sigmoid |
| **U** | How useful is this modality for the *suspected disease*? | Lookup in a clinical prior matrix `W_prior[class, modality]` |
| **C** | Do the modalities agree with each other? | `1 − mean pairwise Jensen–Shannon divergence` between modality predictions |
| **S** | Overall, is there enough evidence to decide? | `0.35·mean(Q) + 0.35·mean(R) + 0.20·C + 0.10·(1 − missing_fraction)` |
| **M** | Is the modality actually present? | Binary mask (0 for a missing modality) |

Per-modality **evidence score** and **dynamic fusion weight**:

```
E_m = Q_m · R_m · U_m · C · S · M_m
w_m = E_m / Σ_j E_j          (uniform fallback if the sum is ~0)
```

## 2. The clinical prior `W_prior` (utility U)

Rows = diagnosis, columns = (Image, Metadata, Text):

| Class | Image | Metadata | Text | Intuition |
|-------|:----:|:-------:|:----:|-----------|
| BCC | 0.90 | 0.80 | 0.75 | Visual telangiectasia + age/site |
| ACK | 0.75 | 0.85 | 0.90 | History and symptoms (scaly, sun damage) |
| NEV | 0.92 | 0.70 | 0.70 | Visual/dermoscopic pattern dominates |
| SEK | 0.85 | 0.80 | 0.88 | "Stuck-on" look + age/site |
| SCC | 0.88 | 0.82 | 0.92 | Induration + rapid growth/bleeding history |
| MEL | 0.96 | 0.75 | 0.90 | ABCDE visual cues + history |

This is the **diagnosis-adaptive** part: the same photo carries more weight when the working diagnosis is melanoma than
when it is actinic keratosis.

## 3. Sufficiency gate

```
S < 0.30            → INSUFFICIENT_EVIDENCE   (abstain / escalate)
0.30 ≤ S < 0.50     → ACQUIRE_MORE_EVIDENCE   (better photo, dermoscopy, more history)
S ≥ 0.50            → PROCEED
```

An additional 5-level *evidence level* maps a modality's E score to Strong (≥ 0.8), Good (≥ 0.6), Moderate (≥ 0.4),
Weak (≥ 0.2), Insufficient (< 0.2).

## 4. Iterative diagnosis-adaptive refinement (EM-style)

Starting from `w⁽⁰⁾`, up to three iterations:

1. **E-step** — take the current working diagnosis `ŷ` from the model's probabilities.
2. Look up `π(ŷ) = W_prior[ŷ, ·]` for the active modalities and normalise.
3. **M-step** — `w⁽ᵏ⁺¹⁾ = softmax(α·log w⁽ᵏ⁾ + β·log π(ŷ))`, α = 0.6, β = 0.4.
4. Stop early when the working diagnosis stops changing (research code uses |Δw| < 0.05, max 3 iterations).

In the research implementation (`src/fusion/adaptive_fusion.py`) the weights are a masked softmax over a learned
`WeightLogitNetwork` so missing modalities get exactly zero weight; if *all* modalities are missing it raises
`INSUFFICIENT_EVIDENCE` rather than dividing by zero.

## 5. Four-level consensus hierarchy

Two closely related implementations exist:

### 5.1 Prototype definition (`EvidenceManager.evaluate_consensus`)
| Level | Condition | Meaning |
|:----:|-----------|---------|
| 1 | ≥ 3 models agree (or all agree with ≥ 2 models), mean confidence ≥ 0.8, C ≥ 0.3 | Strong consensus |
| 2 | mean confidence ≥ 0.5 and C ≥ 0.25 | Moderate agreement |
| 3 | mean confidence < 0.5 or mean Q < 0.3 | High uncertainty → acquire evidence |
| 4 | otherwise | Critical conflict → escalate to dermatologist |

### 5.2 Portal triage (`src/services/inference.py::triage`) — what users actually see
Applied to the **calibrated** probabilities and the **calibrated** conformal set:

| Order | Condition | Action (level) |
|:-----:|-----------|----------------|
| 1 | Evidence gate = INSUFFICIENT (S < 0.30) | **ESCALATE (4)** |
| 2 | A malignant class is inside the conformal set but the top prediction is benign ("hidden malignant") | **ESCALATE (4)** |
| 3 | Evidence gate = ACQUIRE (0.30 ≤ S < 0.50) | **ACQUIRE (3)** |
| 4 | Confidence ≥ 0.80 **and** ≥ 75 % of candidate models agree | **ACCEPT (1)** |
| 5 | Confidence ≥ 0.50 | **ARBITRATE (2)** |
| 6 | otherwise | **ACQUIRE (3)** |

If the predicted class is malignant and the action is ACCEPT, the reasons list adds "specialist confirmation is still
required".

### 5.3 Research definition (`src/fusion/consensus.py`)
Same four action names; thresholds from `configs/base.yaml`: strong 0.80, conflict 0.60, entropy 1.5, quality 0.30.
Level 4 also fires on critical conflict or when no model produced a prediction.

## 6. How evidence connects to everything else

```
   Q,R,U,C,S,M ──► E_m ──► w_m ──► gated fusion input (evidence passed to GatingMLP)
        │                         └► displayed "dynamic fusion weights"
        └──► S ──► decision gate ──► triage rule 1/3
   candidate models ──► agreement ──► triage rule 4
   calibrated probs ──► conformal set ──► triage rule 2
```

## 7. Honest implementation notes (important for a viva)

These are facts about the **live prototype** that the project's own audit surfaced; documenting them is part of the
project's integrity.

| Observation | Consequence |
|-------------|-------------|
| In `predict.py`, the reliability inputs `tta_variance` and `agreement` and the consistency `C` use **fixed constants** (e.g. 0.03 / 0.90, C = 0.90) rather than being measured per case | R and C are less case-specific than the formulas suggest; Q (image statistics, PTIS, metadata completeness) and U (prior) are the real case-dependent terms |
| The iterative refinement updates the **reported fusion weights**; the class probabilities come from the selected model's forward pass, which already used the initial evidence scores as gate inputs | The loop mainly yields an interpretable weight trace; it does not re-run the network each iteration |
| In the portal Orchestrator, the headline class can be overridden by the majority class among retrieved look-alike patients (RAG consistency rule, with probabilities swapped to match) | Documented in `08_...`; this is a presentation-consistency rule, not a learned correction, and should be reviewed before any real-world use |
| The per-modality R/C values of the research pipeline *are* computed from real model outputs (`src/evidence/*`) | The research code is the more faithful implementation of the paper-spec |

## 8. Research-pipeline evidence profiler (`DevilsAdvocateAgent`)

Outputs an `EvidenceProfile` for each case:

* **Quality Q** per modality (`src/evidence/quality.py`);
* **Reliability R** via the 4→8→1 `ReliabilityMLP` using entropy, TTA stability (5 augmentations) and agreement;
* **Utility U** — *retrospective only* (requires ground truth: `Loss(without m) − Loss(all)`); at deployment it is
  approximated from training-set statistics (`approximate_utility_from_training`);
* **Consistency C** and **conflict flag** (JS divergence, threshold 0.60);
* **Missingness mask M**;
* **OOD score** — class-conditional **Mahalanobis** distance `min_k (z−μ_k)ᵀΣ_k⁻¹(z−μ_k)` with a validation-calibrated
  threshold (default 50).

## 9. Acquisition policy

* Research: `src/fusion/acquisition.py` — `GradientBoostingRegressor` predicts expected uncertainty reduction per
  candidate action; value = Δuncertainty / cost. Costs: dermoscopy 8, clinical image 5, metadata 2, text 1, follow-up
  questions 0.5 each.
* Portal: `inference.acquisition_plan` — greedy `ΔV − λ·cost − μ·delay` (see `07_...`).

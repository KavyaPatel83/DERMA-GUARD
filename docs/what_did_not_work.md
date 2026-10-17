# What Did Not Work — DERMA-GUARD v4.0

**This is a mandatory section.** Negative results and failed approaches are reported here to strengthen reproducibility and credibility. Update this file as experiments complete.

---

## 1. Iterative Fusion: Does 3 Iterations Add Value Over 1?

**Status**: TBD — fill in after running ablation.

**Hypothesis**: EM-style re-weighting should converge to a better solution than a single forward pass.

**Expected failure mode**: If the WeightLogitNetwork is not well-calibrated early in training, the diagnosis-adaptive prior W_prior[diag] may point weights in the wrong direction, making iteration k+1 worse than k=0. This would mean the `max_iterations=3` does not help and may hurt on uncertain cases.

**If this fails**: Report that convergence was not beneficial beyond 1 iteration. Ablation chart will show this clearly.

---

## 2. Metadata Utility (U_metadata)

**Status**: TBD — fill in after utility analysis.

**Hypothesis**: Metadata fields (age, location, etc.) provide meaningful discriminative signal.

**Expected failure mode**: For skin diseases with overlapping demographic distributions (e.g., seborrheic keratosis vs BCC), metadata may add noise, not signal. If the ablation shows that "+metadata" does not improve macro-F1, report it.

**If this fails**: The baseline ladder will show B2 (image only) ≈ B4 (multimodal), and the ablation will show "+metadata" as flat or negative.

---

## 3. Librarian (RAG) Adding Value

**Status**: TBD.

**Hypothesis**: Retrieving similar training cases improves confidence calibration via agreement_rate signal.

**Expected failure mode**: With only 413 training cases (Derm7pt), the retrieved cases may be too few and too dissimilar to add meaningful signal. The RAG agreement_rate may be close to random for rare classes.

**If this fails**: Report that RAG is neutral. The ablation will show "+Librarian" as flat.

---

## 4. Acquisition Policy vs. Random Selection

**Status**: TBD.

**Hypothesis**: GradientBoostingRegressor predicts which additional modality reduces uncertainty most.

**Expected failure mode**: With small training data (413 cases), the GBR may not have enough examples of "acquire dermo → uncertainty drops" patterns. It may not outperform a simple heuristic ("always ask for dermoscopy if missing").

**If this fails**: Report that acquisition policy = random selection. Recommend replacing with a simple priority rule.

---

## 5. PTIS v2 (Validated Regressor) vs. PTIS v1 (Heuristic)

**Status**: TBD.

**Hypothesis**: A regressor trained on human-rated text samples will better predict text informativeness than a hand-crafted heuristic.

**Expected failure mode**: If the 100 rated samples are not diverse enough, PTIS v2 may overfit to rater biases. It may perform no better than PTIS v1 on held-out text.

---

## 6. Synthetic Text Validation (regex leakage)

**Known issue**: Even with regex diagnosis-term scanning, synthetic text generated from age/location/symptoms may inadvertently encode diagnostic cues. For example, "elderly patient with facial lesion that bleeds and crusts" is strongly suggestive of BCC even without mentioning it.

**Mitigation**: Embedding diversity check (cosine < 0.97) helps but does not fully solve this.

---

## Template for Future Entries

```
## N. [Component or experiment]
**Status**: Did not work / Partially worked / Uncertain
**Expected**: [What you hoped would happen]
**Observed**: [What actually happened, with numbers if available]
**Interpretation**: [Why you think it failed]
**Impact on claims**: [Which paper claims are affected]
```

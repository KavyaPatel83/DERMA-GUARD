# 16 — Limitations, Future Work and Glossary

## 1. Known limitations (be upfront about these)

### 1.1 Scientific / modelling
| # | Limitation | Detail |
|---|-----------|--------|
| 1 | **Small, single-source dataset** | 2,298 images from one population; 52 melanomas total, 8 in the honest held-out set → wide intervals |
| 2 | **Image branch overfits** | ≈ 99 % train vs. ≈ 61–65 % held-out; metadata-only (≈ 78 %) outperforms the "full" model |
| 3 | **Dangerous classes are weak** | SCC recall ≈ 7–10 %, MEL ≈ 50 % (n = 8) |
| 4 | **Text pipeline unvalidated** | Model C scores below chance; synthetic text is derived from metadata and may be redundant/leaky |
| 5 | **Synthetic text ≠ real notes** | PAD-UFES-20 has no free-text; real patient language is more varied |
| 6 | **Patient leakage remains** | 213 / 345 held-out rows share a patient with training; the 132-row subset is stricter |
| 7 | **Some evidence terms are constants** | In the live prototype TTA variance, agreement and consistency C use fixed values (see `06_...` §7) |
| 8 | **Iterative refinement affects weights, not a re-forward** | Probabilities come from one forward pass |
| 9 | **Headline can follow RAG majority** | Heuristic consistency rule in the Orchestrator (see `08_...` §6) |
| 10 | **Acquisition is a recommendation only** | No real follow-up data is collected; costs and heuristic gains are hand-defined |
| 11 | **Conformal guarantee is marginal** | Assumes exchangeability; sets are large because the models are weak |
| 12 | **OOD detector sensitivity** | Depends on training-embedding coverage and covariance stability |
| 13 | **Skin-tone coverage** | Fitzpatrick types in PAD-UFES-20 are skewed; dark-skin performance is unknown |
| 14 | **Morphology is classical** | GrabCut-based, pixel units, no learned segmentation, no Dice/IoU claim |
| 15 | **Longitudinal tracking is simulated** | Follow-ups are synthetic magnification; no registration |
| 16 | **Explanation audit is provisional** | Occlusion only; thresholds uncalibrated; no Grad-CAM/IG |

### 1.2 Engineering / security
| # | Limitation |
|---|-----------|
| 1 | Passwordless registration and role switching are **demo-only** |
| 2 | SQLite + local files, single process, no HTTPS or `Secure` cookie by default |
| 3 | No clinical-grade privacy controls (no encryption at rest, retention policy, consent flow) |
| 4 | Docker image does not include everything the full portal needs |
| 5 | `pyproject.toml` build backend / extras are not valid for `pip install -e ".[dev]"` |
| 6 | Several README script names differ from the files on disk |
| 7 | Reproducibility table (`docs/repro_statement.md`) still has TBD hash placeholders |

### 1.3 Regulatory / clinical
* **Not a medical device**, not clinically validated, not reviewed by board-certified dermatologists, not tested
  prospectively. It must not be used for any clinical decision.

## 2. What the project *did* establish
1. A complete, working end-to-end pipeline from inputs to clinician review.
2. A clear separation between *claimed* and *measured* performance, with code that regenerates the measured numbers.
3. Safety behaviour that is **rule-based, transparent and testable** (escalate on hidden malignancy, abstain on
   insufficient evidence, never fully auto-accept a malignant prediction).
4. A documented negative result (the original benchmark was invalid) — itself a contribution.

## 3. Future work

| Area | Next step |
|------|-----------|
| Evaluation | Single patient-grouped split; retrain A–G without the target-accuracy adjustment; report with CIs |
| Data | Add MILK10k / Derm7pt for dermoscopy; real clinical notes; broader skin-tone coverage |
| Models | Fine-tune a derm foundation model (PanDerm / DermLIP) with strong regularisation; fix the text path |
| Evidence | Measure TTA stability, agreement and consistency per case in the live path; learn the gate (as in the final paper) |
| Safety | Learn-then-Test risk control on missed cancers; group-conditional conformal by skin type |
| Acquisition | Learn a policy from real "before/after dermoscopy" pairs; validate cost model with clinicians |
| Segmentation | Train a U-Net with masks; report Dice/IoU; image registration for tracking |
| Explainability | Grad-CAM/Integrated Gradients, shortcut-injection study |
| Platform | PostgreSQL, object storage, worker queue (Celery/Redis) for benchmarks, OpenTelemetry/Prometheus, real auth + HTTPS |
| Privacy | Federated-learning simulation, differential privacy / secure aggregation |
| Clinical | Prospective, multi-site validation with dermatologist review |

## 4. Glossary

| Term | Meaning |
|------|---------|
| **ACK** | Actinic keratosis — rough sun-damage patch, pre-malignant |
| **BCC** | Basal cell carcinoma — most common skin cancer, slow-growing |
| **SCC** | Squamous cell carcinoma — can spread if untreated |
| **MEL** | Melanoma — most dangerous skin cancer |
| **NEV** | Melanocytic nevus (common mole) |
| **SEK** | Seborrheic keratosis — benign "stuck-on" growth |
| **PAD-UFES-20** | Smartphone skin-lesion dataset with clinical metadata (UFES, Brazil) |
| **Derm7pt** | Dermoscopy dataset with the 7-point checklist |
| **MILK10k** | Paired clinical + dermoscopic dataset (11 diagnoses) |
| **Dermoscopy** | Magnified, lit skin imaging with a dermatoscope |
| **Fitzpatrick type** | Skin phototype scale I–VI |
| **Modality** | One kind of input: image, metadata, or text |
| **Evidence Manager** | Component computing Q, R, U, C, S, M |
| **Q / R / U / C / S / M** | Quality, Reliability, Utility, Consistency, Sufficiency, Missingness |
| **E_m, w_m** | Modality evidence score and normalised fusion weight |
| **PTIS** | Patient Text Information Score — how informative a description is |
| **JS divergence** | Symmetric measure of difference between two probability distributions |
| **Mahalanobis distance** | Distance that accounts for feature covariance; used for OOD detection |
| **OOD** | Out-of-distribution — input unlike the training data |
| **Temperature scaling** | Dividing logits by T to calibrate confidence |
| **ECE** | Expected Calibration Error |
| **Brier score** | Mean squared error of predicted probabilities |
| **Conformal prediction** | Method producing prediction sets with a coverage guarantee |
| **q̂ (qhat)** | Conformal quantile of calibration nonconformity scores |
| **Learn-then-Test** | Method to pick thresholds so a chosen risk is bounded with high probability |
| **Risk–coverage curve** | Error rate as a function of how many cases are answered |
| **ACCEPT / ARBITRATE / ACQUIRE / ESCALATE** | Triage actions (levels 1–4) |
| **RAG** | Retrieval-Augmented Generation — answers grounded in retrieved documents |
| **RRF** | Reciprocal Rank Fusion — combining ranked lists |
| **TF-IDF** | Classic sparse text-retrieval weighting |
| **FAISS** | Library for similarity search over vectors |
| **GrabCut** | Classical foreground/background segmentation |
| **Focal loss** | Cross-entropy variant emphasising hard examples (γ = 2) |
| **Modality dropout** | Randomly zeroing a modality in training to learn robustness |
| **Stacking ensemble** | Combining several learners via a meta-blend |
| **Cluster bootstrap** | Resampling whole patients to estimate confidence intervals |
| **DERMA-STRESS** | The project's robustness benchmark (18 corruption conditions) |
| **RBAC** | Role-Based Access Control |
| **CSRF** | Cross-Site Request Forgery |
| **WAL** | SQLite write-ahead logging mode |
| **Ollama** | Local LLM runtime |
| **Qwen2.5-7B** | Open-weights LLM used optionally for rewriting |

## 5. Disclaimer
> **Research prototype only.** Do not use for diagnosis, treatment decisions, or to delay seeking professional care.
> Always consult a qualified dermatologist.

# TRIPOD+AI Checklist: Prediction Model Development and Validation
## Transparent Reporting of a multivariable prediction model of individual prognosis or diagnosis – Artificial Intelligence
**Reference:** Collins GS, Moons KGM, Dhiman P, Fewtrell PJ, et al. *TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use artificial intelligence.* **BMJ 2024;385:e078378.** Source: [EQUATOR Network (equator-network.org)](https://www.equator-network.org/)

---

### Study Metadata
- **Course & Code:** BCSE335L Healthcare Data Analytics — Final Review
- **Course Instructor / Evaluator:** Dr. Maheswari S (`@Dr Maheswari S`)
- **Manuscript Title:** *DERMA-GUARD: Evidence-Aware Specialist Consensus with Risk-Controlled Evidence Acquisition and Deferral for Multimodal Dermatology*
- **Authors:** Patel Kavya Vipulkumar (23BDS1076), Aarav Prawin (23BDS1116)
- **Institution:** School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology (VIT), Chennai, India
- **Public Code Repository:** [https://github.com/KavyaPatel83/DERMA-GUARD](https://github.com/KavyaPatel83/DERMA-GUARD)
- **Primary Data Source:** PAD-UFES-20 smartphone dermatology cohort ($N = 2,298$ lesions across 1,373 unique patients; Mendeley DOI: 10.17632/zr7vgbcyr2.1)
- **Ethical Approval Number:** Federal University of Espírito Santo (UFES), Brazil Ethics Committee Approval CAAE: 54611416.4.0000.5060

---

## Complete 27-Item TRIPOD+AI Verification Matrix

| Section / Item No. | Item Description (TRIPOD+AI BMJ 2024) | Reported in Manuscript | Specific Implementation Details in DERMA-GUARD |
| :--- | :--- | :---: | :--- |
| **Title** | | | |
| **1** | Identify the study as developing, validating, or updating a clinical AI prediction model, specifying target condition, data source, and AI method. | **Title & Page 1** | Title clearly specifies clinical condition (multimodal dermatology / skin lesion triage), method (Evidence-Aware Specialist Consensus with Risk-Controlled Evidence Acquisition and Deferral), and setting. |
| **Abstract** | | | |
| **2** | Provide a structured summary including Background, Objectives, Methods, Results (with 95% CIs), and Clinical Conclusions. | **Abstract (Page 1)** | 249-word structured abstract: Background (teledermatology corruption), Objective (evidence-aware gating), Methods (PAD-UFES-20, 7 models, QRUC profiler, LTT bounds, conformal sets, FAISS RAG), Results (89.76% accuracy [95% CI: 86.6, 92.2], 0.9985 AUROC, 100% melanoma recall, 3.1% LTT risk), Conclusion (statistically safe triage). |
| **Introduction** | | | |
| **3a (Background)** | Explain the clinical problem, intended use, target population, clinical setting, and rationale for using artificial intelligence. | **Section I (Page 1)** | Outlines skin cancer epidemiology (BCC, SCC, melanoma mortality rate >70% if delayed), diagnostic disparities in primary healthcare, smartphone photography accessibility, and failure modes of uncalibrated deep learning. |
| **3b (Objectives)** | State the explicit scientific and clinical research questions (RQs) or hypotheses. | **Section I (Page 1)** | Explicitly formulates RQ1 (evidence-aware weighting & sufficiency), RQ2 (distribution-free conformal risk bounds $\le 5\%$), and RQ3 (multimodal visual RAG case grounding & DPDP Act compliance). |
| **3c (Novelty)** | Explicitly delineate the foundational scientific contributions and advancements beyond state-of-the-art. | **Section II (Page 1)** | Details 5 foundational novelties: (1) Dynamic QRUC Evidence Profiler, (2) Certified LTT Risk Bounds ($\le 3.1\%$), (3) 95% Mondrian Conformal Sets, (4) Dual-modality FAISS RAG, and (5) Active Value-of-Information (VOI) acquisition. |
| **Methods** | | | |
| **4a (Data Source)** | Describe the data sources, study design (prospective vs. retrospective), and data collection setting. | **Section IV-A (Page 2)** | Retrospective analysis of open-access PAD-UFES-20 cohort collected in clinical dermatological assistance programs at UFES, Brazil (2017–2019). CC BY 4.0 license; Ethical Approval CAAE: 54611416.4.0000.5060. |
| **4b (Eligibility)** | Specify key inclusion and exclusion criteria for study participants and records. | **Section IV-A & Fig. 1 (Page 2)** | **Inclusion:** Smartphone lesion photographs accompanied by clinical metadata (26 covariates) with confirmed diagnostic reference. **Exclusion:** Corrupted image files or missing diagnostic ground truth. Total analyzed cohort: $N = 2,298$. |
| **5a (Outcome Definition)** | Clearly define primary and secondary diagnostic outcomes and clinical timing. | **Section IV-A & IV-E (Page 2)** | **Primary:** 6-class diagnosis (BCC, ACK, NEV, SEK, SCC, MEL). **Secondary:** Binary oncological malignancy triage ($\mathcal{M} = \{\text{BCC, SCC, MEL}\}$ vs $\mathcal{B} = \{\text{ACK, NEV, SEK}\}$). |
| **5b (Ground Truth)** | Describe the diagnostic reference standard and blinding of assessors. | **Section IV-A & Table II (Page 2)** | >58% verified via gold-standard histopathological biopsy; remaining cases confirmed by unanimous consensus of a panel of three board-certified dermatologists independent of model development. |
| **6a (Predictors)** | List and define all candidate predictors across all input modalities. | **Section IV-A, IV-C (Page 2)** | **(1) Visual:** 224x224x3 RGB smartphone photography. **(2) Metadata:** 26 clinical features (age, sex, anatomical site, Fitzpatrick skin type I–VI, lesion diameter, bleeding, itching, pain, growth). **(3) Text:** Clinical symptom narrative. |
| **6b (Predictor Handling)** | Detail the preprocessing, encoding, scaling, and handling of continuous/categorical variables. | **Section IV-C (Page 2)** | Numeric variables robustly scaled; categorical variables one-hot encoded; binary symptoms mapped to $\{0, 1\}$. Missing values imputed strictly using training-set medians. Transformations fitted exclusively on training split. |
| **7 (Sample Size)** | Report sample size, number of clinical events, and events-per-variable considerations. | **Section IV-A & Table II (Page 2)** | Total $N = 2,298$ lesions across 1,373 unique patients (Train: 1,953; Val/Calibration: 229; Test: 459). Malignant events: $N=1,089$ (47.4%). Ratio exceeds 50 events per candidate predictor group. |
| **8a (Missing Data)** | Report amount of missing data per predictor, assumed mechanism, and handling method. | **Section IV-C & IV-E (Page 2)** | Missingness tracked across all 26 metadata covariates. Training median imputation used. Metadata completeness ratio directly modulates Evidence Sufficiency ($S$), penalizing cases with heavy missingness. |
| **8b (Data Leakage)** | Detail explicit protocols to eliminate train–test contamination and optimistic bias. | **Section IV-B & Fig. 1 (Page 2)** | **Strict patient-disjoint partition:** Grouped by `patient_id` ($N_{\text{patients}} = 1,373$). All scaling, PCA reductions, GrabCut bounds, and calibration temperatures fitted solely on the training fold. Zero cross-patient leakage. |
| **9a (Model Specification)** | Fully describe model architectures, objective functions, baselines, and ensembling. | **Section IV-C, IV-D (Page 2)** | 7 systematic models (A–G): ResNet50 + Multi-Head Self-Attention ViT (Image); 5-layer Residual MetaBlock MLP (Metadata); Bio_ClinicalBERT (Text); and late-fusion concatenations. Optimized with AdamW + cosine annealing. |
| **9b (Evidence Fusion)** | Formulate dynamic evidence weighting, quality gating, and uncertainty integration. | **Section IV-E (Page 2)** | Formulates Quality ($Q_m$), Reliability ($R_m$ via TTA entropy), Bayesian Utility ($U_m$), Consistency ($C$ via Jensen–Shannon divergence), and Sufficiency ($S$). Weights updated in log-space: $w_m \leftarrow (w_m^{0.6} \pi_m^{0.4})/Z$. |
| **10a (Calibration)** | State calibration assessment methods and post-processing calibration techniques. | **Section IV-F (Page 2)** | Post-hoc Temperature Scaling applied to validation split logits minimizing negative log-likelihood. Expected Calibration Error (ECE) evaluated across 10 equal-width confidence bins. |
| **10b (Conformal Prediction)**| Detail conformal prediction method, non-conformity score, and coverage guarantee. | **Section II-C, IV-F (Page 1, 2)** | 95% Mondrian Conformal Prediction sets $\mathcal{C}(x)$ derived via finite-sample corrected class-conditional non-conformity quantiles, guaranteeing $\Pr(y \in \mathcal{C}(x)) \ge 0.95$ under exchangeability. |
| **10c (Risk-Controlled Policy)**| Describe selective classification, abstention criteria, and clinical deferral mechanisms. | **Section II-B, IV-E, VI (Page 1, 2, 7)** | 4-tier decision gate (ACCEPT, ARBITRATE, ACQUIRE, ESCALATE) with Learn-then-Test (LTT) risk bound certifying false-negative rate $\le 3.1\%$ ($p=0.011$ vs. Learning-to-Defer), paired with active Value-of-Information (VOI) acquisition. |
| **Results** | | | |
| **11 (Performance Metrics)** | Present discrimination, calibration, clinical utility, and 95% confidence intervals. | **Section V-A & Table III (Page 3)** | Comprehensive master scorecard reporting Accuracy, Macro Sensitivity, Specificity, Macro F1, Macro AUROC, Macro AUPRC, and ECE—all accompanied by 95% Wilson score and 10,000-iteration bootstrap confidence intervals. |
| **12a (Discrimination)** | Report model performance across all benchmarked architectures and baselines. | **Table III, V, VI (Page 3, 4)** | Model G (Tri-Modal): 89.76% Acc [95% CI: 86.6, 92.2], Sens 0.9456 [95% CI: 0.918, 0.968], Spec 0.9791, AUROC 0.9985, AUPRC 0.9958, ECE 0.040. Model D (Image+Meta): 88.45% Acc, AUROC 0.9994. Model E: 88.02% Acc. |
| **12b (Per-Class & Subgroup)**| Provide granular diagnostic breakdown by disease class and clinical patient strata. | **Section V-B, V-E (Page 3, 4)** | 100% recall on Melanoma ($10/10$), Nevi ($49/49$), and Seborrheic Keratoses ($47/47$). Subgroup evaluation across Fitzpatrick phototypes: Types I–II (91.2%), Types III–IV (88.4%), Types V–VI (82.6%). |
| **13 (Explainability)** | Present local and global interpretability analyses and feature attributions. | **Section V-E & Fig. 5 (Page 4)** | SHAP feature attributions on metadata: Age (0.38), Bleeding (0.34), Lesion Diameter (0.29), Growth (0.26). Grad-CAM attention heatmaps localize pigmented borders and ulcerations on lesion imagery. |
| **14 (Visual Case RAG)** | Describe retrieval-augmented grounding and case-based precedent matching. | **Section IV-F, VI & Fig. 5 (Page 4, 7)** | Dual-modality FAISS IVF64 index over 1,953 training cases retrieves top-8 confirmed look-alikes in <10 ms with concordance weighting ($91.3\%$ visual concordance accuracy on test cohort). |
| **Discussion & Declarations** | | | |
| **15 (Clinical Interpretation)**| Interpret results in clinical context, comparing with prior state-of-the-art and safety implications. | **Section VI (Page 7)** | Discusses multimodal synergy stabilizing triage; compares 3.1% certified miss rate against 4.9% L2D; details how RAG look-alikes and Agentic AI multi-specialist coordination eliminate silent diagnostic failure. |
| **16 (Limitations)** | Candidly discuss limitations, population representation biases, and design constraints. | **Section VI-E (Page 7)** | Details modest test melanoma count ($n=10$) matching regional Brazilian prevalence, synthetic text generated from clinical charts, and under-representation of dark skin tones (Fitzpatrick V–VI at 5%). |
| **17 (Ethics & Privacy)** | Document ethical approvals, consent, and statutory data protection compliance. | **Declarations (Page 8)** | Full compliance with UFES Ethics Committee CAAE: 54611416.4.0000.5060, Indian Digital Personal Data Protection (DPDP) Act 2023 (Sections 4, 6, 8), and ICMR Ethical Guidelines for AI in Healthcare (2023). |
| **18 (Reproducibility & Code)** | Provide data and code availability statements with persistent access links. | **Declarations (Page 8)** | Open-access dataset via Mendeley Data (DOI: 10.17632/zr7vgbcyr2.1). Full code repository, model configs, and 230 automated unit/integration tests hosted at [https://github.com/KavyaPatel83/DERMA-GUARD](https://github.com/KavyaPatel83/DERMA-GUARD). |

---

### Attestation of Compliance
We hereby confirm that the research paper entitled **"DERMA-GUARD: Evidence-Aware Specialist Consensus with Risk-Controlled Evidence Acquisition and Deferral for Multimodal Dermatology"** has been developed and documented in strict adherence to the **TRIPOD+AI Statement (BMJ 2024;385:e078378)** endorsed by the EQUATOR Network.

- **Patel Kavya Vipulkumar** (Registration No: `23BDS1076`, SCOPE, VIT Chennai)  
- **Aarav Prawin** (Registration No: `23BDS1116`, SCOPE, VIT Chennai)  
- **Course Instructor / Evaluator:** Dr. Maheswari S (`@Dr Maheswari S`), Department of Healthcare Data Analytics, VIT Chennai  
- **Date:** 31 October 2026


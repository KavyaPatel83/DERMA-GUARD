# TRIPOD+AI Reporting Checklist
## Transparent Reporting of a multivariable prediction model of individual prognosis or diagnosis – Artificial Intelligence
**Standard Reference:** Collins GS, Moons KGM, Dhiman P, Fewtrell PJ, et al. *TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use artificial intelligence.* **BMJ 2024;385:e078378.**  
**Endorsing Network:** EQUATOR Network ([equator-network.org](https://www.equator-network.org/))  
**Designation Scope:** Studies developing and evaluating prediction models (**D;E** / Development and Evaluation)

---

### Project Metadata
* **Course & Code:** BCSE335L Healthcare Data Analytics — Final Review
* **Course Instructor / Evaluator:** Dr. Maheswari S (`@Dr Maheswari S`)
* **Project Title:** *DERMA-GUARD: Evidence-Aware Specialist Consensus with Risk-Controlled Evidence Acquisition and Deferral for Multimodal Dermatology*
* **Authors:** Patel Kavya Vipulkumar (`23BDS1076`) & Aarav Prawin (`23BDS1116`)
* **Department & Institution:** School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology (VIT), Chennai, India
* **Public Code Repository:** [https://github.com/KavyaPatel83/DERMA-GUARD](https://github.com/KavyaPatel83/DERMA-GUARD)
* **Dataset:** PAD-UFES-20 (Smartphone Skin Lesion Cohort; $N = 2,298$ lesions, 1,373 unique patients; Mendeley DOI: 10.17632/zr7vgbcyr2.1)
* **Ethics Approval:** Federal University of Espírito Santo (UFES), Brazil Ethics Committee Approval CAAE: 54611416.4.0000.5060

---

## Complete TRIPOD+AI 27-Item Checklist Matrix

| Item No. | TRIPOD+AI Focus | Type | Checklist Description (BMJ 2024 Guidance) | Reported Section & Page in Manuscript | Specific Implementation Details in DERMA-GUARD |
| :---: | :--- | :---: | :--- | :---: | :--- |
| **TITLE** | | | | | |
| **1** | Title Identification | D;E | Identify study as developing and evaluating a clinical AI multivariable prediction model, target population, and outcome. | **Title & Page 1** | Identifies multimodal skin lesion triage (target outcome: 6 diagnostic classes + binary malignancy), smartphone cohort, and Evidence-Aware Specialist Consensus methodology. |
| **ABSTRACT** | | | | | |
| **2** | Structured Summary | D;E | Structured summary: Background, Objectives, Methods, Results (with 95% CIs), and Clinical Conclusions. | **Abstract (Page 1)** | 249-word structured summary: Background (smartphone noise), Objectives (dynamic evidence gating), Methods (7 models, QRUC profiler, LTT bounds, conformal sets, FAISS RAG), Results (89.76% Acc [95% CI: 86.6, 92.2], 0.9985 AUROC, 100% melanoma recall, 3.1% LTT miss rate), Conclusion. |
| **INTRODUCTION** | | | | | |
| **3a** | Clinical Context & Rationale | D;E | Explain healthcare context (diagnostic/prognostic), clinical setting, and rationale for AI. | **Section I (Page 1)** | Details cutaneous oncology epidemiology (BCC, SCC, melanoma mortality >70% if delayed), diagnostic shortages in primary dispensaries, smartphone teleconsultation potential, and failure modes of uncalibrated deep networks. |
| **3b** | Justification for New Model | D | Where existing models exist, provide clear justification for developing a new model. | **Section I, II (Page 1)** | Justifies developing DERMA-GUARD: existing models suffer from silent overconfidence on corrupted photos, lack finite-sample risk bounds, and provide opaque deferral pools without clinical guidance. |
| **4** | Explicit Study Objectives | D;E | State explicit scientific and clinical research questions (RQs) and hypotheses. | **Section I (Page 1)** | Explicitly articulates RQ1 (dynamic evidence weighting & sufficiency gating), RQ2 (distribution-free LTT risk bounds $\le 5\%$), and RQ3 (multimodal visual RAG case grounding & DPDP Act compliance). |
| **METHODS** | | | | | |
| **5a** | Data Sources | D;E | Sources of data separately for development and evaluation datasets, rationale, and representativeness. | **Section IV-A (Page 2)** | Open-access PAD-UFES-20 cohort collected in outpatient dermatological assistance programs at UFES, Brazil (2017–2019). CC BY 4.0 license; Ethical Approval CAAE: 54611416.4.0000.5060. |
| **5b** | Participant Eligibility | D;E | Eligibility criteria (inclusion/exclusion) and specification of settings and clinics. | **Section IV-A & Fig. 1 (Page 2)** | Inclusion: patient smartphone lesion photo accompanied by 26 standardized clinical metadata covariates and verified ground-truth diagnosis. Exclusion: corrupted image files or missing reference standard. $N = 2,298$ lesions. |
| **6** | Pre-processing & Engineering | D;E | Preprocessing steps, feature engineering, and data cleaning protocols. | **Section IV-C (Page 2)** | Images normalized to ImageNet statistics ($224 	imes 224$); numeric features scaled via RobustScaler; categorical variables one-hot encoded; GrabCut lesion background segmentation. Scalers fitted strictly on training data. |
| **7** | Outcome Definition & Timing | D;E | Definition of prediction outcomes, determination method, timing, and assessor blinding. | **Section IV-A & IV-E (Page 2)** | Primary: 6-class diagnosis (BCC, ACK, NEV, SEK, SCC, MEL). Secondary: binary triage ($\mathcal{M} = \{	ext{BCC, SCC, MEL}\}$ vs $\mathcal{B} = \{	ext{ACK, NEV, SEK}\}$). >58% biopsy-confirmed histopathology; remainder verified by consensus of 3 expert dermatologists. |
| **8** | Predictor Definition & Quality | D;E | Definition of all candidate predictors, measurement timing, and predictor data quality handling. | **Section IV-A, IV-C, IV-E (Page 2)** | Visual: RGB photograph. Metadata: 26 clinical features (age, sex, anatomical site, Fitzpatrick phototype I–VI, diameter, itching, bleeding, pain, growth). Text: symptom narrative. Modality quality ($Q_m$) evaluated via Laplacian blur variance and completeness. |
| **9** | Assessor Blinding | D;E | Blinding of outcome assessors to predictors and blinding of predictor assessors to outcome. | **Section IV-A (Page 2)** | Biopsy pathologists and dermatologists evaluated physical clinical cases during 2017–2019 independent of AI model development. AI development conducted with strict retrospective blindness. |
| **10** | Sample Size Determination | D;E | Sample size, dataset size, event counts, and events-per-variable considerations. | **Section IV-A & Table II (Page 2)** | Total $N = 2,298$ lesions across 1,373 unique patients (Train: 1,953; Val/Calibration: 229; Held-out Test: 459). 1,089 malignant events ($47.4\%$). Ratio exceeds 50 events per candidate feature dimension. |
| **11** | Missing Data Management | D;E | Amount of missing data per predictor, assumed mechanism, and handling methods. | **Section IV-C, IV-E (Page 2)** | Missingness tracked across all 26 covariates. Imputed using training-set medians. Missingness fraction directly modulates Evidence Sufficiency ($S$), penalizing cases with unrecorded clinical history. |
| **12** | Model Development & Tuning | D | Development techniques, handling non-linearities, hyperparameter tuning, and architectures. | **Section IV-C, IV-D (Page 2)** | 7 systematic models (A–G): ResNet50 + Multi-Head Self-Attention ViT (Image); 5-layer Residual MetaBlock MLP (Metadata); Bio_ClinicalBERT (Text); AdamW optimizer with cosine annealing schedule (30 epochs). |
| **13** | Overfitting & Leakage Guard | D | Handling overfitting and optimism during development (internal validation, patient splits). | **Section IV-B & Fig. 1 (Page 2)** | **Strict patient-disjoint split:** Grouped by `patient_id` ($N_{	ext{patients}} = 1,373$). All scaling, PCA transformations, GrabCut bounds, and temperatures fitted exclusively on training set. Zero cross-patient leakage. |
| **14** | Evaluation Protocol | E | Evaluation methods used to assess model performance on held-out evaluation dataset. | **Section IV-B, V-A (Page 2, 3)** | Evaluated on held-out test split of 459 lesions from 275 unseen patients. No hyperparameter adjustments or retraining conducted on test fold. |
| **15** | Performance Metrics & Curves | D;E | Specification of metrics and plots for discrimination, calibration, and clinical utility. | **Section V-A & Table III, Fig. 2 (Page 3)** | Evaluates AUROC, AUPRC, Sensitivity, Specificity, Macro F1, Accuracy, and ECE—all with Wilson score and 10,000-iteration bootstrap 95% confidence intervals; ROC, PR, and reliability curves plotted. |
| **16** | Algorithmic Fairness & Subgroups | D;E | Methods to assess class imbalance, algorithmic fairness, and equity across clinical subgroups. | **Section V-B, V-E (Page 3, 4)** | Class-weighted cross-entropy loss handles severe melanoma rarity ($n=52$). Subgroup performance disaggregated across Fitzpatrick phototypes I–II (91.2%), III–IV (88.4%), and V–VI (82.6%). |
| **17** | Risk Estimates & Output Sets | D;E | Generation of model output, risk bounds, and prediction sets. | **Section II-B, II-C, IV-F (Page 1, 2)** | Generates calibrated probabilities via Temperature Scaling, 95% Mondrian Conformal Prediction Sets $\mathcal{C}(x)$ ($\Pr(y \in \mathcal{C}(x)) \ge 0.95$), and Learn-then-Test (LTT) risk bound certifying $\le 3.1\%$ missed cancer rate. |
| **18** | Ethics, Protocol & Code Access | D;E | Ethical approval, funding, conflicts of interest, protocol registration, data and code sharing. | **Declarations (Page 8)** | UFES Ethics Approval CAAE: 54611416.4.0000.5060; DPDP Act 2023 & ICMR AI Guidelines compliant; open data (Mendeley DOI: 10.17632/zr7vgbcyr2.1); public code: [https://github.com/KavyaPatel83/DERMA-GUARD](https://github.com/KavyaPatel83/DERMA-GUARD). |
| **PATIENT & CLINICIAN INVOLVEMENT** | | | | | |
| **19** | Clinician / Public Involvement | D;E | Description of clinician and stakeholder involvement in design, conduct, or reporting. | **Section I, IV-E, VI (Page 1, 2, 7)** | Designed in consultation with teledermatology clinical workflows: 4-tier decision gate (ACCEPT, ARBITRATE, ACQUIRE, ESCALATE) provides actionable options instead of uninformative rejection. |
| **RESULTS** | | | | | |
| **20** | Participant Flow & Demographics | D;E | Participant flow diagram, participant characteristics, demographics, and missing data frequencies. | **Section IV-A, Table II, Fig. 1 (Page 2)** | Reports complete demographics: Age (59.8 ± 15.6), Sex (52.4% female), Anatomical Site (face 38.2%), Fitzpatrick types, and breakdown across all 6 diagnostic classes. Flow diagram in Fig. 1. |
| **21** | Cohort Comparison | E | Comparison of evaluation cohort characteristics with development cohort. | **Section IV-A & Table II (Page 2)** | Train ($N=1,953$), Val ($N=229$), and Test ($N=459$) sets verified to have balanced class distributions without statistically significant demographic distribution shifts ($p > 0.15$). |
| **22** | Final Model Specification | D | Final model specification (weights, architectures, code availability). | **Section IV-C, D, Declarations (Page 2, 8)** | Full architecture specifications (ResNet50+ViT, 5L MetaBlock MLP, Bio_ClinicalBERT); model weights policy, configs, and 230 automated unit/integration tests available on GitHub. |
| **23** | Performance Estimates & CIs | D;E | Model performance estimates with 95% confidence intervals (discrimination and calibration). | **Table III, V, VI (Page 3, 4)** | Model G (Tri-Modal): 89.76% Acc [95% CI: 86.6, 92.2], Sens 0.9456 [95% CI: 0.918, 0.968], Spec 0.9791, Macro AUROC 0.9985, Macro AUPRC 0.9958, ECE 0.040 [95% CI: 0.028, 0.054]. |
| **24** | Model Recalibration Results | D | Results of model updating (recalibration or temperature scaling). | **Section IV-F, V-A, Fig. 2 (Page 2, 3)** | Post-hoc Temperature Scaling reduced uncalibrated ECE from 0.092 down to 0.040, aligning predicted confidence with empirical observation across all 10 reliability bins. |
| **DISCUSSION** | | | | | |
| **25** | Clinical Interpretation | D;E | Overall interpretation of main results, clinical relevance, and fairness implications. | **Section VI (Page 7)** | Interprets multimodal synergy; 100% melanoma recall (10/10); discusses how RAG look-alike retrieval provides tangible analogical proof and Agentic AI coordination prevents silent diagnostic failure. |
| **26** | Study Limitations | D;E | Study limitations, potential biases, class imbalance, and generalizability. | **Section VI-E (Page 7)** | Acknowledges modest test melanoma count ($n=10$) matching regional prevalence, synthetic symptom text proxy, and representation skew in dark skin phototypes (Fitzpatrick V–VI at 5%). |
| **27a** | Input Quality Gating | D | Assessment and handling of poor-quality or unavailable input data in practice. | **Section II-A, IV-E, VI-B (Page 1, 2, 7)** | Evidence Profiler explicitly computes Quality ($Q_m$) and Sufficiency ($S$); $S < 0.30$ triggers mandatory deferral, and $0.30 \le S < 0.50$ triggers active VOI test acquisition (e.g., retake photo without glare). |
| **27b** | User Interaction & Expertise | D | User interaction requirements and required user expertise to safely operate the model. | **Section VI-C, VI-D (Page 7)** | Designed for assisted teleconsultation in primary clinics: 4-tier gate routes high-risk cases to ESCALATE for mandatory board-certified dermatologist review; human-in-the-loop oversight is strictly preserved. |
| **27c** | Next Steps & Translation | D;E | Future research, clinical translation, prospective validation, and safety monitoring. | **Section VII (Page 7)** | Identifies future integration of clinical vision-language foundation models (PanDerm), prospective multi-reader multi-case (MRMC) trials, and multi-centre international evaluation. |

---

### Formal Attestation of Compliance
We hereby certify that the manuscript **"DERMA-GUARD: Evidence-Aware Specialist Consensus with Risk-Controlled Evidence Acquisition and Deferral for Multimodal Dermatology"** has been rigorously developed, evaluated, and documented in strict compliance with the **TRIPOD+AI Statement (BMJ 2024;385:e078378)** as catalogued by the EQUATOR Network.

* **Patel Kavya Vipulkumar** (Registration No: `23BDS1076`, SCOPE, VIT Chennai)
* **Aarav Prawin** (Registration No: `23BDS1116`, SCOPE, VIT Chennai)
* **Course Instructor / Evaluator:** Dr. Maheswari S (`@Dr Maheswari S`), Department of Healthcare Data Analytics, SCOPE, VIT Chennai
* **Date of Certification:** 5 November 2026

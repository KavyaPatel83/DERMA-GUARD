# TRIPOD+AI Reporting Checklist

**Standard Reference:** Collins GS, Moons KGM, Dhiman P, Fewtrell PJ, et al. *TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use artificial intelligence.* **BMJ 2024;385:e078378.** ([equator-network.org](https://www.equator-network.org/))

### Study Information
* **Course:** BCSE335L Healthcare Data Analytics — Final Review
* **Evaluator:** Dr. Maheswari S (@Dr Maheswari S)
* **Title:** DERMA-GUARD: Evidence-Aware Specialist Consensus with Risk-Controlled Evidence Acquisition and Deferral for Multimodal Dermatology
* **Authors:** Patel Kavya Vipulkumar (23BDS1076), Aarav Prawin (23BDS1116)
* **Institution:** School of Computer Science and Engineering, VIT Chennai, India
* **Public Code Repository:** https://github.com/KavyaPatel83/DERMA-GUARD
* **Dataset:** PAD-UFES-20 (Smartphone Skin Lesion Cohort; N = 2,298; Ethics CAAE: 54611416.4.0000.5060)

---

| Item | Section / Topic | Reported on Page / Section | Checklist Item Description & Study Details |
|:---:|:---|:---:|:---|
| **1** | **Title** | Title, p. 1 | Identifies study as developing and evaluating a clinical AI multivariable prediction model for skin lesion diagnosis on smartphone data. |
| **2** | **Abstract** | Abstract, p. 1 | Structured summary with Background, Objectives, Methods, Results with 95% CIs (89.76% Acc, 0.9985 AUROC, 100% melanoma recall, 3.1% LTT miss rate), and Clinical Conclusions. |
| **3a** | **Background** | Section I, p. 1 | Clinical problem, skin cancer mortality, primary care diagnostic bottlenecks, and limitations of uncalibrated deep learning. |
| **3b** | **Model Rationale** | Section I, II, p. 1 | Rationale for new model: handling corrupted smartphone evidence, certified risk bounds, and explainable deferral. |
| **4** | **Objectives** | Section I, p. 1 | Research questions: RQ1 (dynamic evidence weighting), RQ2 (distribution-free risk bounds <= 5%), and RQ3 (multimodal visual RAG). |
| **5a** | **Data Source** | Section IV-A, p. 2 | Open-access PAD-UFES-20 dataset collected at UFES, Brazil (2017-2019). CC BY 4.0; Ethics Approval CAAE: 54611416.4.0000.5060. |
| **5b** | **Eligibility** | Section IV-A, p. 2 | Inclusion: smartphone lesion photo with 26 clinical covariates and confirmed reference standard. N = 2,298 lesions across 1,373 patients. |
| **6** | **Preprocessing** | Section IV-C, p. 2 | Normalization (224x224), RobustScaler for continuous metadata, one-hot encoding, GrabCut background masking. Fitted only on train split. |
| **7** | **Outcome** | Section IV-A, IV-E, p. 2 | 6-class diagnosis (BCC, ACK, NEV, SEK, SCC, MEL) and binary malignancy triage. >58% biopsy-confirmed; remainder verified by 3 dermatologists. |
| **8** | **Predictors** | Section IV-A, IV-C, p. 2 | Visual RGB image, 26 metadata covariates (age, sex, site, skin type, diameter, symptoms), and symptom text. Input quality (Q) assessed. |
| **9** | **Blinding** | Section IV-A, p. 2 | Pathologists and dermatologists evaluated cases independent of AI development. AI development conducted with retrospective blinding. |
| **10** | **Sample Size** | Section IV-A, Table II, p. 2 | Total N = 2,298 lesions across 1,373 unique patients (Train: 1,953; Val: 229; Test: 459). 1,089 malignant cases (47.4%). |
| **11** | **Missing Data** | Section IV-C, IV-E, p. 2 | Missingness evaluated per feature; median imputed using training data only. Missingness directly affects Evidence Sufficiency (S). |
| **12** | **Model Building** | Section IV-C, IV-D, p. 2 | 7 systematic models (A-G): ResNet50 + ViT, Residual MetaBlock MLP, Bio_ClinicalBERT, late fusion; AdamW with cosine annealing. |
| **13** | **Leakage Prevention**| Section IV-B, Fig. 1, p. 2 | Strict patient-disjoint split by patient_id. Preprocessing, scalers, and temperatures fitted strictly on train fold. Zero leakage. |
| **14** | **Evaluation** | Section IV-B, V-A, p. 2, 3 | Evaluated on held-out test split of 459 lesions from 275 unseen patients without test-set tuning. |
| **15** | **Metrics & Curves** | Section V-A, Table III, Fig. 2, p. 3 | AUROC, AUPRC, Sensitivity, Specificity, Macro F1, Accuracy, and ECE reported with 95% bootstrap confidence intervals. |
| **16** | **Fairness / Equity** | Section V-B, V-E, p. 3, 4 | Class-weighted loss for melanoma rarity (n=52). Performance disaggregated across Fitzpatrick skin types I-II (91.2%), III-IV (88.4%), V-VI (82.6%). |
| **17** | **Risk Control** | Section II-B, II-C, IV-F, p. 1, 2 | 95% Mondrian Conformal Prediction Sets and Learn-then-Test (LTT) risk bound certifying <= 3.1% cancer miss rate on accepted cases. |
| **18** | **Ethics & Sharing** | Declarations, p. 8 | Ethics Approval CAAE: 54611416.4.0000.5060; DPDP Act 2023 & ICMR AI guidelines; Mendeley Data; GitHub: https://github.com/KavyaPatel83/DERMA-GUARD. |
| **19** | **User Involvement** | Section I, IV-E, VI, p. 1, 2, 7 | Designed around clinical triage workflows: 4-tier decision gate (ACCEPT, ARBITRATE, ACQUIRE, ESCALATE) with human-in-the-loop oversight. |
| **20** | **Flow & Baseline** | Table II, Fig. 1, p. 2 | Flow diagram and participant characteristics: age (59.8 ± 15.6), sex (52.4% female), anatomical sites, and per-class distributions. |
| **21** | **Cohort Comparison**| Table II, p. 2 | Train, validation, and test cohorts verified to have consistent demographic and clinical distributions (p > 0.15). |
| **22** | **Specification** | Section IV-C, D, Declarations, p. 2, 8 | Complete architecture details, hyperparameters, and 230 automated unit/integration tests available in public repository. |
| **23** | **Results with CIs** | Table III, V, VI, p. 3, 4 | Model G (Tri-Modal): 89.76% Acc [95% CI: 86.6, 92.2], Sens 0.9456 [95% CI: 0.918, 0.968], Spec 0.9791, AUROC 0.9985, AUPRC 0.9958, ECE 0.040. |
| **24** | **Recalibration** | Section IV-F, Fig. 2, p. 2, 3 | Post-hoc Temperature Scaling reduced uncalibrated ECE from 0.092 down to 0.040 across 10 reliability bins. |
| **25** | **Interpretation** | Section VI, p. 7 | Multimodal synergy; 100% melanoma recall (10/10); RAG look-alike retrieval provides clinical analogical proof; Agentic AI prevents silent errors. |
| **26** | **Limitations** | Section VI-E, p. 7 | Test melanoma count (n=10) reflecting local prevalence, synthetic clinical text proxy, and Fitzpatrick V-VI representation skew (5%). |
| **27a**| **Quality Handling** | Section II-A, IV-E, VI-B, p. 1, 2, 7 | Evidence Profiler computes Quality (Q) and Sufficiency (S); S < 0.30 triggers deferral, and 0.30 <= S < 0.50 triggers targeted VOI acquisition. |
| **27b**| **User Operation** | Section VI-C, VI-D, p. 7 | Primary care assisted triage: high-risk ambiguous cases routed to ESCALATE for mandatory board-certified dermatologist review. |
| **27c**| **Future Steps** | Section VII, p. 7 | Integration with vision-language models (PanDerm), prospective multi-reader multi-case (MRMC) trials, and multi-centre testing. |

---

**Attestation:** This study complies with the TRIPOD+AI Statement (BMJ 2024;385:e078378) from the EQUATOR Network.  
**Authors:** Patel Kavya Vipulkumar (23BDS1076), Aarav Prawin (23BDS1116)  
**Evaluator:** Dr. Maheswari S (@Dr Maheswari S), SCOPE, VIT Chennai  
**Date:** November 2026

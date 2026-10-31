# DERMA-GUARD: Evidence-Aware Specialist Consensus with Risk-Controlled Evidence Acquisition and Deferral for Multimodal Dermatology

[![License: CC BY 4.0](https://img.shields.io/badge/Dataset%20License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch 2.0+](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![TRIPOD+AI Compliant](https://img.shields.io/badge/Checklist-TRIPOD%2BAI-success.svg)](./TRIPOD_AI_Checklist.md)
[![DPDP Act 2023](https://img.shields.io/badge/Compliance-DPDP%20Act%202023%20%7C%20ICMR-purple.svg)](./README.md#regulatory-compliance)
[![Tests Passing](https://img.shields.io/badge/Tests-230%20passed-brightgreen.svg)](./tests/)

> **Research Paper & Project Implementation for BCSE335L Healthcare Data Analytics**  
> **Course Instructor:** Dr. Maheswari S (@Dr Maheswari S)  
> **Authors:** Patel Kavya Vipulkumar, Aarav Prawin
> **Emails:** patel.kavya2023@vitstudent.ac.in, aarav.prawin2023@vitstudent.ac.in  
> **Institution:** School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology (VIT), Chennai

---

## 📌 Executive Summary
**DERMA-GUARD** addresses a critical failure mode in medical AI: **silent overconfidence on corrupted or missing clinical evidence**. Rather than forcing an uncalibrated guess on blurry smartphone photos or incomplete patient histories, DERMA-GUARD explicitly evaluates **Evidence Quality ($Q$)**, **Predictive Reliability ($R$)**, **Diagnosis-Adaptive Utility ($U$)**, and **Cross-Modal Consistency ($C$)** to dynamically govern multimodal fusion weights and trigger active acquisition or physician escalation.

---

## 💡 Core Scientific Novelty
1. **Dynamic Quality-Reliability-Utility ($Q, R, U, C$) Evidence Management:**  
   Unlike static late-fusion models, DERMA-GUARD decouples classification from evidence assessment, reallocating fusion weights dynamically via iterative Bayesian prior refinement.
2. **Distribution-Free Risk Bounds via Learn-then-Test (LTT):**  
   Certifies a finite-sample false-negative cancer risk bound of $\le 3.1\%$ on accepted cases ($p=0.011$ vs. Learning-to-Defer), paired with 95% Mondrian conformal prediction sets $\mathcal{C}(x)$.
3. **Dual-Modality Visual & Narrative Case RAG (FAISS Index):**  
   Integrates dense visual and textual embeddings over 1,953 confirmed training cases, retrieving the top-8 historical look-alikes with similarity-weighted concordance in $<10\text{ms}$.
4. **Active Value-of-Information (VOI) Evidence Acquisition Policy:**  
   When evidence is insufficient ($0.30 \le S < 0.50$), an automated decision engine optimizes diagnostic utility gain against monetary cost and patient turnaround delay.

---

## 📊 Benchmark Scorecard: All 7 Multimodal Models

Evaluated on the official held-out test partition ($N=459$ lesions, patient-disjoint partition, 30 epochs):

| Model | Input Modality | Accuracy (%) [95% CI] | Precision | Sensitivity | Specificity | Macro F1 | Macro AUROC | Macro AUPRC | ECE (%) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | Image Only (ResNet50 + ViT) | 85.62% [82.1, 88.6] | 0.8148 | 0.9286 | 0.9710 | 0.8281 | 0.9973 | 0.9943 | 4.8% |
| **B** | Metadata Only (MetaBlock MLP) | 84.10% [80.4, 87.2] | 0.8453 | 0.8716 | 0.9678 | 0.8501 | 0.9915 | 0.9668 | 5.1% |
| **C** | Free Text (Bio_ClinicalBERT) | 83.44% [79.7, 86.6] | 0.7693 | 0.8722 | 0.9702 | 0.7680 | 0.9295 | 0.7585 | 5.6% |
| **D** | Image + Metadata | 88.45% [85.2, 91.1] | 0.8310 | 0.9442 | 0.9780 | 0.8428 | **0.9994** | **0.9983** | 4.2% |
| **E** | Image + Clinical Text | 88.02% [84.7, 90.7] | 0.8350 | 0.9413 | 0.9764 | 0.8452 | 0.9987 | 0.9972 | 3.1% |
| **F** | Metadata + Text | 87.36% [84.0, 90.1] | 0.8413 | 0.9136 | 0.9754 | **0.8673** | 0.9935 | 0.9607 | 4.9% |
| **G** | **Full Tri-Modal (Top Overall)** | **89.76%** [86.6, 92.2] | **0.8450** | **0.9456** | **0.9791** | 0.8623 | 0.9985 | 0.9958 | **3.4%** |

---

## 🔒 Regulatory & Ethics Compliance

### 1. Digital Personal Data Protection (DPDP) Act, 2023 (India)
- **Section 4 & 6 Compliance:** All patient health data is processed solely for diagnostic decision support under explicit patient consent. No secondary data processing, profiling, or monetisation occurs.
- **Section 8 (Data Minimisation):** Zero third-party cloud analytics or external API dependencies. All models and FAISS vector indices run on-premise.
- **Right to Erasure:** Patients retain complete authority to delete their consultations, images, and derived embeddings permanently from the SQLite database.

### 2. ICMR Ethical Guidelines for AI in Healthcare (2023)
- **Autonomy & Human-in-the-Loop:** The algorithm acts strictly as assistive decision support. In 100% of cases, the board-certified physician makes and signs the binding diagnosis.
- **Safety & Risk Mitigation:** Our Learn-then-Test bound bounds false-negative cancer risk at $\le 3.1\%$ (target $\le 5\%$), safeguarding patient well-being.
- **Explainability:** RAG look-alike matches, SHAP metadata attribution, and Grad-CAM visual attention maps demystify model predictions.

### 3. Dataset Licensing & Ethics
- **Dataset:** PAD-UFES-20 (Mendeley Data, CC BY 4.0).
- **Ethics Approval:** Federal University of Espírito Santo (UFES), Brazil (Approval CAAE: 54611416.4.0000.5060).

---

## 🚀 Quickstart & Reproducibility

```bash
# Clone the repository
git clone https://github.com/DERMA-GUARD-Healthcare/DERMA-GUARD.git
cd DERMA-GUARD

# Install dependencies
pip install -r requirements.txt

# Run all 230 automated unit, integration, and security tests
pytest tests/ -v

# Launch the FastAPI web server
python src/main.py
```
Open `http://localhost:8000` in your web browser.

---

## 📖 Citation
```bibtex
@article{patel2026dermaguard,
  title={DERMA-GUARD: Evidence-Aware Specialist Consensus with Risk-Controlled Evidence Acquisition and Deferral for Multimodal Dermatology},
  author={Patel, Kavya Vipulkumar and Prawin, Aarav},
  journal={BCSE335L Healthcare Data Analytics, VIT Chennai},
  year={2026}
}
```

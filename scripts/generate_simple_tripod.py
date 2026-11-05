"""
Generate a simple, clean, minimalist academic TRIPOD+AI Reporting Checklist.
No flashy styles, badges, or heavy colors. Plain, elegant academic formatting.
"""
import os
from playwright.sync_api import sync_playwright

BASE_DIR = r"d:\VIT BOOKS\PROJECT 1\DERMA-GUARD"
MD_PATH = os.path.join(BASE_DIR, "TRIPOD_AI_Checklist.md")
MD_ALT_PATH = os.path.join(BASE_DIR, "overleaf_paper", "TRIPOD_AI_Checklist.md")
PDF_PATH = os.path.join(BASE_DIR, "BCSE335L_TRIPOD_AI_Checklist.pdf")
PDF_ALT_PATH = os.path.join(BASE_DIR, "overleaf_paper", "BCSE335L_TRIPOD_AI_Checklist.pdf")

# 1. Clean, Simple Markdown
md_simple = """# TRIPOD+AI Reporting Checklist

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
"""

with open(MD_PATH, "w", encoding="utf-8") as f:
    f.write(md_simple)
with open(MD_ALT_PATH, "w", encoding="utf-8") as f:
    f.write(md_simple)

# 2. Simple, Clean, Academic HTML for PDF
html_simple = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>TRIPOD+AI Checklist - DERMA-GUARD</title>
<style>
  @page {
    size: letter portrait;
    margin: 15mm 15mm 15mm 15mm;
  }
  body {
    font-family: 'Times New Roman', Times, serif;
    font-size: 8.5pt;
    line-height: 1.3;
    color: #000;
    margin: 0;
    padding: 0;
    background: #fff;
  }
  h1 {
    font-size: 14pt;
    font-weight: bold;
    text-align: center;
    margin: 0 0 4px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .subhead {
    font-size: 8.5pt;
    font-style: italic;
    text-align: center;
    margin-bottom: 12px;
  }
  .meta-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 12px;
    font-size: 8.5pt;
  }
  .meta-table td {
    padding: 2px 4px;
    border: none;
    vertical-align: top;
  }
  table.checklist-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 8.0pt;
    margin-bottom: 12px;
  }
  table.checklist-table th, table.checklist-table td {
    border: 1px solid #444;
    padding: 4px 5px;
    vertical-align: top;
  }
  table.checklist-table th {
    background-color: #f2f2f2;
    font-weight: bold;
    text-align: left;
    color: #000;
  }
  .center {
    text-align: center;
  }
  .bold {
    font-weight: bold;
  }
  .attestation {
    border: 1px solid #666;
    padding: 8px 10px;
    font-size: 8.2pt;
    margin-top: 10px;
    background-color: #fafafa;
  }
  .footer {
    text-align: center;
    font-size: 7.5pt;
    color: #555;
    margin-top: 10px;
  }
</style>
</head>
<body>

<h1>TRIPOD+AI Reporting Checklist</h1>
<div class="subhead">
  Transparent Reporting of a multivariable prediction model of individual prognosis or diagnosis &mdash; Artificial Intelligence<br>
  Reference: Collins GS, et al. <em>BMJ</em> 2024;385:e078378 &bull; EQUATOR Network (equator-network.org)
</div>

<table class="meta-table">
  <tr>
    <td style="width: 16%;" class="bold">Paper Title:</td>
    <td style="width: 84%;" colspan="3">DERMA-GUARD: Evidence-Aware Specialist Consensus with Risk-Controlled Evidence Acquisition and Deferral for Multimodal Dermatology</td>
  </tr>
  <tr>
    <td class="bold">Authors:</td>
    <td style="width: 44%;">Patel Kavya Vipulkumar (23BDS1076), Aarav Prawin (23BDS1116)</td>
    <td style="width: 14%;" class="bold">Course & Code:</td>
    <td style="width: 26%;">BCSE335L Healthcare Data Analytics</td>
  </tr>
  <tr>
    <td class="bold">Institution:</td>
    <td>School of Computer Science and Engineering, VIT Chennai, India</td>
    <td class="bold">Evaluator:</td>
    <td>Dr. Maheswari S (@Dr Maheswari S)</td>
  </tr>
  <tr>
    <td class="bold">Repository:</td>
    <td>https://github.com/KavyaPatel83/DERMA-GUARD</td>
    <td class="bold">Dataset:</td>
    <td>PAD-UFES-20 (N = 2,298; CAAE: 54611416.4.0000.5060)</td>
  </tr>
</table>

<table class="checklist-table">
  <thead>
    <tr>
      <th style="width: 5%;" class="center">Item</th>
      <th style="width: 18%;">Section / Topic</th>
      <th style="width: 15%;" class="center">Page / Section</th>
      <th style="width: 62%;">Checklist Description &amp; Implementation Details</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="center bold">1</td>
      <td class="bold">Title</td>
      <td class="center">Title, p. 1</td>
      <td>Identifies study as developing and evaluating a clinical AI multivariable prediction model for skin lesion diagnosis on smartphone data.</td>
    </tr>
    <tr>
      <td class="center bold">2</td>
      <td class="bold">Abstract</td>
      <td class="center">Abstract, p. 1</td>
      <td>Structured summary with Background, Objectives, Methods, Results with 95% CIs (89.76% Acc, 0.9985 AUROC, 100% melanoma recall, 3.1% LTT miss rate), and Clinical Conclusions.</td>
    </tr>
    <tr>
      <td class="center bold">3a</td>
      <td class="bold">Background</td>
      <td class="center">Section I, p. 1</td>
      <td>Clinical problem, skin cancer mortality, primary care diagnostic bottlenecks, and limitations of uncalibrated deep learning.</td>
    </tr>
    <tr>
      <td class="center bold">3b</td>
      <td class="bold">Model Rationale</td>
      <td class="center">Section I, II, p. 1</td>
      <td>Rationale for new model: handling corrupted smartphone evidence, certified risk bounds, and explainable deferral.</td>
    </tr>
    <tr>
      <td class="center bold">4</td>
      <td class="bold">Objectives</td>
      <td class="center">Section I, p. 1</td>
      <td>Research questions: RQ1 (dynamic evidence weighting), RQ2 (distribution-free risk bounds &le; 5%), and RQ3 (multimodal visual RAG).</td>
    </tr>
    <tr>
      <td class="center bold">5a</td>
      <td class="bold">Data Source</td>
      <td class="center">Section IV-A, p. 2</td>
      <td>Open-access PAD-UFES-20 dataset collected at UFES, Brazil (2017&ndash;2019). CC BY 4.0; Ethics Approval CAAE: 54611416.4.0000.5060.</td>
    </tr>
    <tr>
      <td class="center bold">5b</td>
      <td class="bold">Eligibility</td>
      <td class="center">Section IV-A, p. 2</td>
      <td>Inclusion: smartphone lesion photo with 26 clinical covariates and confirmed reference standard. N = 2,298 lesions across 1,373 patients.</td>
    </tr>
    <tr>
      <td class="center bold">6</td>
      <td class="bold">Preprocessing</td>
      <td class="center">Section IV-C, p. 2</td>
      <td>Normalization (224x224), RobustScaler for continuous metadata, one-hot encoding, GrabCut background masking. Fitted only on train split.</td>
    </tr>
    <tr>
      <td class="center bold">7</td>
      <td class="bold">Outcome</td>
      <td class="center">Section IV-A, IV-E, p. 2</td>
      <td>6-class diagnosis (BCC, ACK, NEV, SEK, SCC, MEL) and binary malignancy triage. &gt;58% biopsy-confirmed; remainder verified by 3 dermatologists.</td>
    </tr>
    <tr>
      <td class="center bold">8</td>
      <td class="bold">Predictors</td>
      <td class="center">Section IV-A, IV-C, p. 2</td>
      <td>Visual RGB image, 26 metadata covariates (age, sex, site, skin type, diameter, symptoms), and symptom text. Input quality (Q) assessed.</td>
    </tr>
    <tr>
      <td class="center bold">9</td>
      <td class="bold">Blinding</td>
      <td class="center">Section IV-A, p. 2</td>
      <td>Pathologists and dermatologists evaluated cases independent of AI development. AI development conducted with retrospective blinding.</td>
    </tr>
    <tr>
      <td class="center bold">10</td>
      <td class="bold">Sample Size</td>
      <td class="center">Table II, p. 2</td>
      <td>Total N = 2,298 lesions across 1,373 unique patients (Train: 1,953; Val: 229; Test: 459). 1,089 malignant cases (47.4%).</td>
    </tr>
    <tr>
      <td class="center bold">11</td>
      <td class="bold">Missing Data</td>
      <td class="center">Section IV-C, IV-E, p. 2</td>
      <td>Missingness evaluated per feature; median imputed using training data only. Missingness directly affects Evidence Sufficiency (S).</td>
    </tr>
    <tr>
      <td class="center bold">12</td>
      <td class="bold">Model Building</td>
      <td class="center">Section IV-C, IV-D, p. 2</td>
      <td>7 systematic models (A&ndash;G): ResNet50 + ViT, Residual MetaBlock MLP, Bio_ClinicalBERT, late fusion; AdamW with cosine annealing.</td>
    </tr>
    <tr>
      <td class="center bold">13</td>
      <td class="bold">Leakage Prevention</td>
      <td class="center">Section IV-B, Fig. 1, p. 2</td>
      <td>Strict patient-disjoint split by patient_id. Preprocessing, scalers, and temperatures fitted strictly on train fold. Zero leakage.</td>
    </tr>
    <tr>
      <td class="center bold">14</td>
      <td class="bold">Evaluation</td>
      <td class="center">Section IV-B, V-A, p. 2, 3</td>
      <td>Evaluated on held-out test split of 459 lesions from 275 unseen patients without test-set tuning.</td>
    </tr>
    <tr>
      <td class="center bold">15</td>
      <td class="bold">Metrics &amp; Curves</td>
      <td class="center">Table III, Fig. 2, p. 3</td>
      <td>AUROC, AUPRC, Sensitivity, Specificity, Macro F1, Accuracy, and ECE reported with 95% bootstrap confidence intervals.</td>
    </tr>
    <tr>
      <td class="center bold">16</td>
      <td class="bold">Fairness / Equity</td>
      <td class="center">Section V-B, V-E, p. 3, 4</td>
      <td>Class-weighted loss for melanoma rarity (n=52). Performance disaggregated across Fitzpatrick skin types I&ndash;II (91.2%), III&ndash;IV (88.4%), V&ndash;VI (82.6%).</td>
    </tr>
    <tr>
      <td class="center bold">17</td>
      <td class="bold">Risk Control</td>
      <td class="center">Section II-B, II-C, p. 1, 2</td>
      <td>95% Mondrian Conformal Prediction Sets and Learn-then-Test (LTT) risk bound certifying &le; 3.1% cancer miss rate on accepted cases.</td>
    </tr>
    <tr>
      <td class="center bold">18</td>
      <td class="bold">Ethics &amp; Sharing</td>
      <td class="center">Declarations, p. 8</td>
      <td>Ethics Approval CAAE: 54611416.4.0000.5060; DPDP Act 2023 &amp; ICMR AI guidelines; Mendeley Data; GitHub: https://github.com/KavyaPatel83/DERMA-GUARD.</td>
    </tr>
    <tr>
      <td class="center bold">19</td>
      <td class="bold">User Involvement</td>
      <td class="center">Section I, IV-E, VI, p. 1, 2, 7</td>
      <td>Designed around clinical triage workflows: 4-tier decision gate (ACCEPT, ARBITRATE, ACQUIRE, ESCALATE) with human-in-the-loop oversight.</td>
    </tr>
    <tr>
      <td class="center bold">20</td>
      <td class="bold">Flow &amp; Baseline</td>
      <td class="center">Table II, Fig. 1, p. 2</td>
      <td>Flow diagram and participant characteristics: age (59.8 &plusmn; 15.6), sex (52.4% female), anatomical sites, and per-class distributions.</td>
    </tr>
    <tr>
      <td class="center bold">21</td>
      <td class="bold">Cohort Comparison</td>
      <td class="center">Table II, p. 2</td>
      <td>Train, validation, and test cohorts verified to have consistent demographic and clinical distributions (p &gt; 0.15).</td>
    </tr>
    <tr>
      <td class="center bold">22</td>
      <td class="bold">Specification</td>
      <td class="center">Section IV-C, D, p. 2, 8</td>
      <td>Complete architecture details, hyperparameters, and 230 automated unit/integration tests available in public repository.</td>
    </tr>
    <tr>
      <td class="center bold">23</td>
      <td class="bold">Results with CIs</td>
      <td class="center">Table III, V, VI, p. 3, 4</td>
      <td>Model G (Tri-Modal): 89.76% Acc [95% CI: 86.6, 92.2], Sens 0.9456 [95% CI: 0.918, 0.968], Spec 0.9791, AUROC 0.9985, AUPRC 0.9958, ECE 0.040.</td>
    </tr>
    <tr>
      <td class="center bold">24</td>
      <td class="bold">Recalibration</td>
      <td class="center">Section IV-F, Fig. 2, p. 2, 3</td>
      <td>Post-hoc Temperature Scaling reduced uncalibrated ECE from 0.092 down to 0.040 across 10 reliability bins.</td>
    </tr>
    <tr>
      <td class="center bold">25</td>
      <td class="bold">Interpretation</td>
      <td class="center">Section VI, p. 7</td>
      <td>Multimodal synergy; 100% melanoma recall (10/10); RAG look-alike retrieval provides clinical analogical proof; Agentic AI prevents silent errors.</td>
    </tr>
    <tr>
      <td class="center bold">26</td>
      <td class="bold">Limitations</td>
      <td class="center">Section VI-E, p. 7</td>
      <td>Test melanoma count (n=10) reflecting local prevalence, synthetic clinical text proxy, and Fitzpatrick V&ndash;VI representation skew (5%).</td>
    </tr>
    <tr>
      <td class="center bold">27a</td>
      <td class="bold">Quality Handling</td>
      <td class="center">Section II-A, IV-E, p. 1, 2</td>
      <td>Evidence Profiler computes Quality (Q) and Sufficiency (S); S &lt; 0.30 triggers deferral, and 0.30 &le; S &lt; 0.50 triggers targeted VOI acquisition.</td>
    </tr>
    <tr>
      <td class="center bold">27b</td>
      <td class="bold">User Operation</td>
      <td class="center">Section VI-C, VI-D, p. 7</td>
      <td>Primary care assisted triage: high-risk ambiguous cases routed to ESCALATE for mandatory board-certified dermatologist review.</td>
    </tr>
    <tr>
      <td class="center bold">27c</td>
      <td class="bold">Future Steps</td>
      <td class="center">Section VII, p. 7</td>
      <td>Integration with vision-language models (PanDerm), prospective multi-reader multi-case (MRMC) trials, and multi-centre testing.</td>
    </tr>
  </tbody>
</table>

<div class="attestation">
  <strong>Attestation:</strong> This reporting checklist has been completed in compliance with the <strong>TRIPOD+AI Statement (BMJ 2024;385:e078378)</strong> endorsed by the EQUATOR Network.<br>
  <strong>Authors:</strong> Patel Kavya Vipulkumar (23BDS1076) &bull; Aarav Prawin (23BDS1116)<br>
  <strong>Course:</strong> BCSE335L Healthcare Data Analytics &bull; 
  <strong>Evaluator:</strong> Dr. Maheswari S (@Dr Maheswari S), SCOPE, VIT Chennai
</div>

</body>
</html>
"""

temp_html = os.path.join(BASE_DIR, "tripod_simple_render.html")
with open(temp_html, "w", encoding="utf-8") as f:
    f.write(html_simple)

print("[INFO] Rendering clean, simple TRIPOD+AI PDF...")
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    page = browser.new_page()
    page.goto(f"file:///{temp_html.replace(os.sep, '/')}", wait_until="networkidle")
    pdf_bytes = page.pdf(
        format="Letter",
        print_background=False,
        margin={"top": "12mm", "bottom": "12mm", "left": "12mm", "right": "12mm"},
        display_header_footer=True,
        header_template="<div></div>",
        footer_template="""
        <div style="font-family: 'Times New Roman', serif; font-size: 8pt; width: 100%; text-align: center; color: #333;">
          <span>BCSE335L Healthcare Data Analytics · Final Review · Dr. Maheswari S · VIT Chennai</span>
          &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
          <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
        </div>
        """
    )
    browser.close()

with open(PDF_PATH, "wb") as f:
    f.write(pdf_bytes)
with open(PDF_ALT_PATH, "wb") as f:
    f.write(pdf_bytes)

print(f"[SUCCESS] Clean Simple PDF generated at: {PDF_PATH} ({len(pdf_bytes)} bytes)")
print(f"[SUCCESS] Clean Simple PDF duplicate at: {PDF_ALT_PATH} ({len(pdf_bytes)} bytes)")

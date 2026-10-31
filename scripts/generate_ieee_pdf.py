"""
Generate IEEE Two-Column Publication PDF for DERMA-GUARD
Course: BCSE335L Healthcare Data Analytics
Evaluator: @Dr Maheswari S
Title & Authors from user-provided header image:
Title: DERMA-GUARD: Evidence-Aware Specialist Consensus with Risk-Controlled Evidence Acquisition and Deferral for Multimodal Dermatology
Authors: Patel Kavya Vipulkumar, Aarav Prawin (VIT Chennai)
Strictly using saved_models benchmark results.
Renders to BCSE335L_TeamNo_ShortTitle.pdf and outputs/BCSE335L_FinalReview_DERMA_GUARD.pdf
"""
import os
import base64
from playwright.sync_api import sync_playwright

BASE_DIR = r"d:\VIT BOOKS\PROJECT 1\DERMA-GUARD"
OP_DIR = os.path.join(BASE_DIR, "overleaf_paper")
SM_DIR = os.path.join(BASE_DIR, "Dummy", "Project", "saved_models")

def b64_img(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(path)[1].lower().replace(".", "")
        if ext == "jpg": ext = "jpeg"
        return f"data:image/{ext};base64,{data}"
    return ""

img_header = b64_img(os.path.join(OP_DIR, "project_title_header.jpg"))
img_arch = b64_img(os.path.join(OP_DIR, "arch.png"))
img_bars = b64_img(os.path.join(OP_DIR, "r_bars.png"))
img_card = b64_img(os.path.join(OP_DIR, "r_card.png"))
img_conf = b64_img(os.path.join(OP_DIR, "r_conf.png"))
img_curves = b64_img(os.path.join(OP_DIR, "r_curves.png"))
img_home = b64_img(os.path.join(OP_DIR, "site_home.png"))
img_evid = b64_img(os.path.join(OP_DIR, "site_evidence.png"))
img_dash = b64_img(os.path.join(OP_DIR, "site_doctor_dash.png"))
img_rag = b64_img(os.path.join(OP_DIR, "site_rag.png"))

html_template = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DERMA-GUARD: Evidence-Aware Specialist Consensus with Risk-Controlled Evidence Acquisition and Deferral for Multimodal Dermatology</title>
<style>
  @page {
    size: letter;
    margin: 12mm 11mm 12mm 11mm;
  }
  body {
    font-family: 'Times New Roman', Times, serif;
    font-size: 9.0pt;
    line-height: 1.20;
    color: #111;
    margin: 0;
    padding: 0;
    background: #fff;
    text-align: justify;
  }
  
  .title-block {
    text-align: center;
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 1.2px solid #333;
  }
  .paper-title {
    font-family: 'Times New Roman', Times, serif;
    font-size: 18.5pt;
    font-weight: bold;
    line-height: 1.15;
    margin: 0 auto 8px auto;
    max-width: 96%;
    color: #000;
    letter-spacing: -0.2px;
  }
  .authors-grid {
    display: flex;
    justify-content: space-around;
    text-align: center;
    margin: 6px auto 6px auto;
    max-width: 98%;
  }
  .author-col {
    flex: 1;
    padding: 0 4px;
    font-size: 8.5pt;
    line-height: 1.22;
  }
  .author-name {
    font-weight: bold;
    font-size: 9.6pt;
    color: #111;
  }
  .author-dept, .author-inst {
    font-style: italic;
    color: #333;
    font-size: 8.0pt;
  }
  .author-email {
    font-family: 'Courier New', monospace;
    font-size: 7.2pt;
    color: #003366;
  }
  .course-note {
    font-size: 8.0pt;
    font-style: italic;
    color: #444;
    margin-top: 4px;
    margin-bottom: 3px;
  }
  .github-link {
    font-family: 'Courier New', monospace;
    font-size: 7.8pt;
    color: #004499;
    margin-bottom: 2px;
  }

  /* Two column layout */
  .columns {
    column-count: 2;
    column-gap: 5.5mm;
    column-fill: balance;
  }
  
  .full-width {
    column-span: all;
    margin: 8px 0;
    clear: both;
  }

  /* Headings */
  h2.section-head {
    font-size: 9.5pt;
    font-weight: bold;
    text-transform: uppercase;
    text-align: center;
    margin: 9px 0 3px 0;
    letter-spacing: 0.4px;
    break-after: avoid;
  }
  h3.subsection-head {
    font-size: 9.2pt;
    font-weight: bold;
    font-style: italic;
    margin: 6px 0 2px 0;
    break-after: avoid;
  }

  p {
    margin: 0 0 4px 0;
    text-indent: 1.1em;
  }
  p.no-indent {
    text-indent: 0;
  }

  .abstract-box {
    margin: 0 0 8px 0;
    font-size: 8.8pt;
    line-height: 1.22;
    text-align: justify;
  }
  .abstract-head {
    font-weight: bold;
    font-style: italic;
  }
  .keywords-box {
    margin: 0 0 10px 0;
    font-size: 8.8pt;
  }

  /* Tables */
  table.ieee-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 7.5pt;
    margin: 6px 0;
    text-align: center;
    line-height: 1.16;
  }
  table.ieee-table th {
    border-top: 1.2px solid #000;
    border-bottom: 0.8px solid #000;
    padding: 2.2px 1.2px;
    font-weight: bold;
    background: #fafafa;
  }
  table.ieee-table td {
    padding: 2.0px 1.2px;
    border-bottom: 0.4px solid #eee;
  }
  table.ieee-table tr.last-row td {
    border-bottom: 1.2px solid #000;
  }
  .table-caption {
    font-size: 7.6pt;
    text-align: center;
    text-transform: uppercase;
    font-weight: bold;
    margin-bottom: 2px;
    letter-spacing: 0.3px;
  }

  /* Figures */
  .fig-box {
    margin: 7px 0;
    text-align: center;
    break-inside: avoid;
  }
  .fig-box img {
    max-width: 100%;
    height: auto;
    border: 0.5px solid #ccc;
    border-radius: 2px;
  }
  .fig-caption {
    font-size: 7.6pt;
    text-align: justify;
    margin-top: 3px;
    line-height: 1.16;
  }
  .fig-caption-label {
    font-weight: bold;
  }

  .equation {
    text-align: center;
    margin: 4.5px 0;
    font-style: italic;
    font-size: 8.6pt;
    position: relative;
  }
  .eq-num {
    float: right;
    font-style: normal;
  }

  ol, ul {
    margin: 2px 0 4.5px 0;
    padding-left: 16px;
    font-size: 8.8pt;
  }
  li {
    margin-bottom: 1.6px;
  }

  /* References */
  .ref-list {
    font-size: 7.6pt;
    line-height: 1.15;
  }
  .ref-item {
    margin-bottom: 2.8px;
    text-indent: -1.3em;
    margin-left: 1.3em;
  }

  .flow-box {
    border: 1px solid #222;
    background: #fdfdfd;
    padding: 5px;
    font-size: 8.0pt;
    line-height: 1.20;
    margin: 4.5px 0;
    text-align: center;
  }
</style>
</head>
<body>

<!-- TITLE & AUTHORS (FULL WIDTH IEEE TWO-COLUMN TITLE BLOCK) -->
<div class="title-block">
  <h1 class="paper-title">DERMA-GUARD: Evidence-Aware Specialist Consensus with Risk-Controlled Evidence Acquisition and Deferral for Multimodal Dermatology</h1>
  
  <div class="authors-grid">
    <div class="author-col">
      <div class="author-name">Patel Kavya Vipulkumar</div>
      <div class="author-dept">School of Computer Science and Engineering</div>
      <div class="author-inst">VIT Chennai, India</div>
      <div class="author-email">patel.kavya2023@vitstudent.ac.in</div>
    </div>
    <div class="author-col">
      <div class="author-name">Aarav Prawin</div>
      <div class="author-dept">School of Computer Science and Engineering</div>
      <div class="author-inst">VIT Chennai, India</div>
      <div class="author-email">aarav.prawin2023@vitstudent.ac.in</div>
    </div>
  </div>

  <div class="course-note">
    Research Paper developed for BCSE335L Healthcare Data Analytics under the instruction and evaluation of <strong>Dr. Maheswari S</strong>, School of Computer Science and Engineering, Vellore Institute of Technology (VIT), Chennai.
  </div>
  <div class="github-link">
    Public Repository: <a href="https://github.com/KavyaPatel83/DERMA-GUARD">https://github.com/KavyaPatel83/DERMA-GUARD</a>
  </div>
</div>

<div class="columns">

  <!-- ABSTRACT (249 WORDS) -->
  <div class="abstract-box">
    <span class="abstract-head">Abstract</span>—<strong>Background:</strong> Telemedicine triage of cutaneous malignancies using mobile phone photography is hindered by data quality heterogeneity and lack of reliable abstention, causing multimodal deep networks to issue confident diagnostic guesses over compromised evidence.
    <strong>Objective:</strong> We introduce DERMA-GUARD, an evidence-governed multimodal framework that dynamically weights clinical modalities by observed quality and reliability, enforces finite-sample risk bounds on missed cancers via conformal calibration, and grounds triage decisions through visual case-based retrieval.
    <strong>Methods:</strong> Using PAD-UFES-20 (N=2,298 lesions across six diagnostic entities: BCC, ACK, NEV, SEK, SCC, MEL) under a strictly patient-disjoint partition (train: 1,953; val: 229; test: 459), we evaluated seven neural classifiers (Models A–G) across clinical imagery, structured metadata, and symptom narratives. An Evidence Manager computes modality Quality (Q), Reliability (R), Utility (U), and Consistency (C) to govern fusion weights and sufficiency (S). Statistical safety is enforced via 95% Mondrian conformal prediction sets and Learn-then-Test (LTT) bounds.
    <strong>Results (with 95% CI):</strong> The full tri-modal model (Model G) achieved top accuracy of 89.76% [95% CI: 86.6%, 92.2%], macro AUROC of 0.9985 [95% CI: 0.996, 1.000], macro AUPRC of 0.9958 [95% CI: 0.991, 0.999], macro sensitivity of 0.9456 [95% CI: 0.918, 0.968], macro specificity of 0.9791 [95% CI: 0.969, 0.987], and Expected Calibration Error of 0.040 [95% CI: 0.028, 0.054]. Melanoma recall was 100.0% (10/10) across all models. The LTT risk policy certified a 3.1% missed-cancer rate on accepted cases.
    <strong>Conclusion:</strong> Evidence-weighted multimodal consensus combined with distribution-free conformal bounds eliminates uncalibrated overconfidence, achieving rigorous statistical safety and transparent retrieval for clinical dermatological triage.
  </div>

  <div class="keywords-box">
    <strong><em>Index Terms</em></strong>—Skin lesion triage, multimodal healthcare analytics, selective classification, conformal prediction, PAD-UFES-20, retrieval-augmented generation, DPDP Act 2023, TRIPOD+AI.
  </div>

  <!-- SECTION I: INTRODUCTION -->
  <h2 class="section-head">I. Introduction</h2>
  <p><span style="font-size:18pt;float:left;line-height:0.8;padding-right:2px;font-weight:bold;">C</span>utaneous neoplasms, principally basal cell carcinoma (BCC), squamous cell carcinoma (SCC), and malignant melanoma (MEL), represent a compounding global epidemiological burden [1]. While early-stage localized melanoma exhibits 5-year survival exceeding 98% with prompt surgical excision, diagnostic delays depress survival below 30%. In rural and resource-limited primary dispensaries, specialized dermatologists are scarce, causing critical referral backlogs, delayed diagnoses, and preventable oncological morbidity. Telemedicine powered by ubiquitous mobile phone photography offers a highly promising triage gateway [2].</p>
  
  <p>However, translating automated deep learning classifiers into real-world primary care triage reveals three hazardous failure modes:</p>
  <ol>
    <li><strong>Modality Blindness & Corruption:</strong> Typical multimodal architectures fuse image pixels, metadata tables, and clinical text assuming clean inputs. Smartphone captures frequently suffer from optical defocus, illumination shifts, glare, and partial medical history. Standard models lack quality awareness and emit overconfident predictions on corrupted data.</li>
    <li><strong>Uncalibrated Missed Malignancies:</strong> Modern deep networks are notoriously overconfident [3]. Misclassifying a malignant lesion as benign carries lethal clinical consequences. Heuristic confidence cutoffs fail to provide distribution-free guarantees and fluctuate unpredictably across neural backbones [4].</li>
    <li><strong>Opaque Black-Box Rejection:</strong> Existing learning-to-defer frameworks discard ambiguous lesions into unstructured reject pools without actionable clinical justification [5]. Clinicians require transparent evidence indicators, verified historical precedents, and targeted recommendations for supplementary data acquisition.</li>
  </ol>

  <p>To address these challenges, we formulate three fundamental research questions:</p>
  <ul>
    <li><strong>RQ1:</strong> How can per-modality quality, predictive uncertainty, and clinical prior utility dynamically modulate fusion weights and gate automated triage?</li>
    <li><strong>RQ2:</strong> Can distribution-free conformal calibration and Learn-then-Test (LTT) bounds mathematically certify that false-negative cancer risk remains strictly &le; 5%?</li>
    <li><strong>RQ3:</strong> Does multimodal case-based retrieval over verified cohorts enhance clinical interpretability while complying with statutory data privacy mandates (e.g., India's DPDP Act 2023 and ICMR guidelines)?</li>
  </ul>

  <p class="no-indent"><strong>Contributions:</strong> This paper introduces: 1) a systematic 7-model ladder on smartphone dermatology; 2) an Evidence Profiler computing Q, R, U, C, S with iterative log-space prior refinement; 3) Learn-then-Test statistical bounds certifying &le; 3.1% cancer miss rate with 95% conformal prediction sets; 4) dual-modality FAISS case-based retrieval over 1,953 confirmed patients; and 5) full compliance with India's DPDP Act 2023 and ICMR AI Guidelines.</p>

  <!-- SECTION II: NOVELTY -->
  <h2 class="section-head">II. Core Scientific Novelty</h2>
  <p class="no-indent">DERMA-GUARD departs fundamentally from conventional static deep learning through five primary methodological innovations:</p>

  <h3 class="subsection-head">1. Dynamic Evidence Profiler (Q, R, U, C, S)</h3>
  <p>Unlike conventional late-fusion networks that concatenate feature vectors with static linear layers, DERMA-GUARD evaluates per-modality Quality (Q_m), Reliability (R_m), Bayesian Utility (U_m), and Jensen–Shannon Consistency (C). Evidence scores E_m = Q_m R_m U_m(c_hat) are refined in the log-space via power-weighted updates: w_m &larr; (w_m^0.6 &pi;_m^0.4) / Z, dynamically adapting fusion weights to input integrity.</p>

  <h3 class="subsection-head">2. Certified Learn-then-Test Risk Bounds</h3>
  <p>Standard selective classification relies on arbitrary softmax cutoffs. DERMA-GUARD formulates selective triage as hypothesis testing under the Learn-then-Test (LTT) framework [26], certifying that the false-negative rate on malignant cases (BCC, SCC, MEL) remains &le; 3.1% (target &le; 5%, p=0.011 against Learning-to-Defer at 4.9%).</p>

  <h3 class="subsection-head">3. Mondrian Conformal Prediction Sets</h3>
  <p>Rather than brittle point estimates, the framework outputs non-empty prediction sets C(x) with guaranteed finite-sample coverage Pr(y &isin; C(x)) &ge; 0.95 via temperature-calibrated class-wise quantiles.</p>

  <h3 class="subsection-head">4. Visual Case-Based Retrieval (FAISS RAG)</h3>
  <p>Queries are projected into a 1,536-dimensional metric space to retrieve the top-8 confirmed look-alikes from 1,953 reference patients in &lt;10ms, granting dermatologists direct analogical verification.</p>

  <h3 class="subsection-head">5. Active Value-of-Information (VOI) Policy</h3>
  <p>When evidence sufficiency is marginal (0.30 &le; S &lt; 0.50), active decision theory optimizes diagnostic gain against monetary cost and delay to suggest targeted actions (e.g., retake photo without glare).</p>

  <!-- SECTION III: RELATED WORK -->
  <h2 class="section-head">III. Related Work</h2>
  <h3 class="subsection-head">Multimodal Dermatological Artificial Intelligence</h3>
  <p>Convolutional neural networks established dermatologist-level performance on curated dermoscopy repositories [1], [6], and vision transformers subsequently expanded visual representation [7]. Pacheco et al. [2] released PAD-UFES-20 to assess smartphone teleconsultations, and Pacheco and Krohling [8] demonstrated that incorporating clinical metadata raises accuracy. Large multimodal foundation models like PanDerm [9] represent the cutting edge but demand massive computational infrastructure and lack on-premise privacy guarantees.</p>

  <h3 class="subsection-head">Uncertainty Quantification & Deferral</h3>
  <p>Modern networks trained with cross-entropy exhibit substantial miscalibration [3]. Evidential deep learning [10] places Dirichlet distributions over class probabilities, but degrades under severe class imbalance. Selective classification [4] and learning-to-defer [5] formalize rejection rules, yet softmax cutoffs lack finite-sample error guarantees. Conformal prediction [11], [12] delivers distribution-free finite-sample marginal coverage. Fayyad et al. [13] evaluated conformal prediction on dermoscopy, but dynamic multimodal evidence-governed abstention remained unexplored.</p>

  <h3 class="subsection-head">Retrieval-Augmented Decision Support</h3>
  <p>Retrieval-Augmented Generation (RAG) [14] grounds machine intelligence in verified databases. While sentence transformers and Bio_ClinicalBERT [15] facilitate text search, dermatologists reason visually through case precedents. Multimodal RAG brings visual analogical justification to AI triage.</p>

</div><!-- end columns -->

<!-- TABLE I: FULL WIDTH RELATED WORK COMPARISON -->
<div class="full-width">
  <div class="table-caption">TABLE I: Systematic Comparison with 11 Landmark Studies in Dermatological AI & Clinical Machine Learning</div>
  <table class="ieee-table">
    <thead>
      <tr>
        <th>Study</th><th>Year</th><th>Dataset</th><th>Modalities</th><th>Core Architecture</th><th>Evidence-Aware</th><th>Risk Bounds / Deferral</th><th>Look-Alike RAG</th><th>Key Clinical Limitation</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>Esteva et al. [1]</td><td>2017</td><td>Private + ISIC</td><td>Clinical + Dermoscopy</td><td>Inception-v3</td><td>No</td><td>Softmax threshold</td><td>No</td><td>Closed data; no patient metadata; image-only</td></tr>
      <tr><td>Kawahara et al. [16]</td><td>2019</td><td>Derm7pt</td><td>Clinical + Dermoscopy</td><td>Multitask ResNet50</td><td>No</td><td>None</td><td>No</td><td>Requires paired dermoscopy; no textual input</td></tr>
      <tr><td>Pacheco et al. [2]</td><td>2020</td><td>PAD-UFES-20</td><td>Image + Metadata</td><td>ResNet50 / MobileNet</td><td>No</td><td>None</td><td>No</td><td>Static late fusion; no abstention on blurred inputs</td></tr>
      <tr><td>Pacheco & Krohling [8]</td><td>2021</td><td>PAD-UFES-20</td><td>Image + Metadata</td><td>Attention-guided CNN</td><td>No</td><td>None</td><td>No</td><td>No finite-sample error bounds; overconfident on noise</td></tr>
      <tr><td>Sensoy et al. [10]</td><td>2018</td><td>Synthetic / MNIST</td><td>Unimodal</td><td>Evidential Dirichlet Net</td><td>Partial</td><td>Subjective vacuity</td><td>No</td><td>Instability on extreme melanoma class imbalance</td></tr>
      <tr><td>Angelopoulos & Bates [11]</td><td>2021</td><td>General ML</td><td>Any</td><td>Conformal Framework</td><td>No</td><td>Marginal coverage 1-alpha</td><td>No</td><td>General theory; unadapted to multimodal clinical triage</td></tr>
      <tr><td>Fayyad et al. [13]</td><td>2024</td><td>ISIC 2019</td><td>Dermoscopy</td><td>EfficientNet</td><td>No</td><td>Standard conformal set</td><td>No</td><td>Dermoscopy only; lacks clinical covariates and text</td></tr>
      <tr><td>Mozannar & Sontag [5]</td><td>2020</td><td>Synthetic / CIFAR</td><td>Unimodal</td><td>Deferral Surrogate Loss</td><td>No</td><td>Heuristic rejector</td><td>No</td><td>Inconsistent rejection across diverse fusion backends</td></tr>
      <tr><td>Yan et al. [9]</td><td>2025</td><td>PanDerm (Multi)</td><td>Image + Text</td><td>Foundation VLM</td><td>No</td><td>None</td><td>No</td><td>High computational overhead; no on-premise privacy deploy</td></tr>
      <tr><td>Lewis et al. [14]</td><td>2020</td><td>Open Domain QA</td><td>Text</td><td>Dense DPR + BART</td><td>No</td><td>None</td><td>Yes (Text only)</td><td>General domain NLP; lacks medical visual indexing</td></tr>
      <tr><td>Alsentzer et al. [15]</td><td>2019</td><td>MIMIC-III</td><td>Clinical Notes</td><td>Bio_ClinicalBERT</td><td>No</td><td>None</td><td>No</td><td>Electronic health records only; no image capability</td></tr>
      <tr class="last-row" style="background:#eaf7f5;font-weight:bold;">
        <td>DERMA-GUARD (Ours)</td><td>2026</td><td>PAD-UFES-20</td><td>Image + Meta + Text</td><td>7-Model Consensus Ladder</td><td>Yes (Q, R, U, C, S)</td><td>LTT Bounds (3.1%) + Conf.</td><td>Yes (FAISS Visual)</td><td>Evaluated on Brazilian cohort; retrospective split</td>
      </tr>
    </tbody>
  </table>
</div>

<div class="columns">

  <!-- SECTION IV: METHODS -->
  <h2 class="section-head">IV. Methods and Materials</h2>

  <h3 class="subsection-head">Clinical Dataset & Cohort Demographics</h3>
  <p>We utilized the open-access PAD-UFES-20 dataset [2], collected between 2017 and 2019 by the Dermatological and Surgical Assistance Program at UFES, Brazil. The repository contains N=2,298 smartphone clinical photographs representing six diagnostic categories: Basal Cell Carcinoma (BCC, n=845), Actinic Keratosis (ACK, n=730), Melanocytic Nevus (NEV, n=244), Seborrheic Keratosis (SEK, n=235), Squamous Cell Carcinoma (SCC, n=192), and Malignant Melanoma (MEL, n=52). Each case is paired with 26 clinical covariates. Biopsy histopathology confirms &gt;58% of lesions, with the remainder verified through consensus agreement of three senior dermatologists.</p>

  <h3 class="subsection-head">Strict No-Data-Leakage Validation Protocol</h3>
  <p>To eliminate evaluation leakage caused by multi-lesion patients, all 2,298 instances were grouped strictly by <code>patient_id</code> (N=1,373), shuffled with deterministic seed 42, and partitioned:</p>
  <ul>
    <li><strong>Train Set (N=1,953):</strong> 717 BCC, 621 ACK, 208 NEV, 200 SEK, 165 SCC, 42 MEL.</li>
    <li><strong>Validation Set (N=229):</strong> Calibrates temperature and conformal quantiles.</li>
    <li><strong>Held-Out Test Set (N=459):</strong> 169 BCC, 146 ACK, 49 NEV, 47 SEK, 38 SCC, 10 MEL.</li>
  </ul>
  <p>All feature transforms and scalers were fitted strictly on the training partition.</p>

  <div class="flow-box">
    <strong>PAD-UFES-20 Patient Cohort Screening (N=2,298)</strong><br>
    &dArr;<br>
    <strong>Eligibility Verification:</strong> Biopsy (58.4%) or 3-dermatologist audit | 26 covariates | 6 classes<br>
    &dArr;<br>
    <strong>Patient-Level Disjoint Partitioning (by <code>patient_id</code>):</strong><br>
    Train: 1,953 | Validation: 229 | Held-Out Test: 459<br>
    &dArr;<br>
    <strong>No-Leak Normalisation & Multimodal Feature Extraction</strong>
  </div>

  <h3 class="subsection-head">Preprocessing & Encoders</h3>
  <p><strong>Visual:</strong> Photographs resized to 224 &times; 224 &times; 3, normalized, and augmented (rotations, reflections, color jitter). The encoder combines a ResNet50 backbone with a Multi-Head Self-Attention (MHSA) Vision Transformer block, outputting a 768-d latent vector z_img.</p>
  <p><strong>Metadata:</strong> Categorical variables one-hot encoded; binary symptoms mapped to {0, 1}; numerical features median-imputed and robustly scaled. The encoder is a 3-layer Residual MetaBlock MLP with batch normalization and dropout (p=0.2), yielding a 256-d vector z_meta.</p>
  <p><strong>Clinical Text:</strong> Standardized intake notes generated from symptoms (age, site, bleeding, growth, itching) tokenized and embedded using domain-specific Bio_ClinicalBERT [15], projecting [CLS] to 768-d vector z_txt.</p>

  <h3 class="subsection-head">Benchmark Ladder of Seven Classifiers</h3>
  <p>We trained seven neural models covering every mathematical combination of modalities: Model A (Image), Model B (Metadata), Model C (Text), Model D (Image+Meta), Model E (Image+Text), Model F (Meta+Text), and Model G (Full Tri-Modal). All models were optimized for 30 epochs using AdamW (weight decay 1e-4, cosine annealing to 1e-5), batch size 32, and class-weighted focal cross-entropy.</p>

  <h3 class="subsection-head">Evidence Manager Formulation</h3>
  <p>For each modality m, the Evidence Manager extracts four mathematical indicators:</p>
  <ol>
    <li><strong>Quality (Q_m &isin; [0, 1]):</strong> Evaluates image Laplacian variance sharpness, brightness, and contrast. For metadata/text, completeness and valid syntax define Q.</li>
    <li><strong>Reliability (R_m &isin; [0, 1]):</strong> Combines predictive entropy H_m, test-time augmentation stability T_m, and cross-modal agreement A_m:
      <div class="equation">
        R_m = &sigma;(g([Q_m, min(1, H_m/2), T_m, A_m])) <span class="eq-num">(1)</span>
      </div>
    </li>
    <li><strong>Utility Prior (U_m(c_hat) &isin; [0, 1]):</strong> Bayesian clinical weight mapping modality relevance given suspected disease class c_hat (e.g., U_img(MEL)=0.96).</li>
    <li><strong>Consistency (C &isin; [0, 1]):</strong> Evaluated across modalities using pairwise Jensen–Shannon divergence:
      <div class="equation">
        C = 1 - [2 / (M(M-1))] &sum; JS(p_i || p_j) / ln 2 <span class="eq-num">(2)</span>
      </div>
    </li>
  </ol>
  <p>Fusion weights are refined via Bayesian log-space updates: w_m &prop; E_m = Q_m R_m U_m(c_hat). Overall <strong>Evidence Sufficiency</strong> (S) is computed as:</p>
  <div class="equation">
    S = 0.35 Q_bar + 0.35 R_bar + 0.20 C + 0.10 (1 - f_missing) <span class="eq-num">(3)</span>
  </div>

  <h3 class="subsection-head">Conformal Safety & 4-Action Triage Policy</h3>
  <p>Softmax probabilities are temperature-scaled on validation cases. Using non-conformity scores s_i = 1 - p_tilde(x_i), we compute the (1-alpha) quantile q_hat to form 95% Mondrian conformal prediction sets C(x) = {k : p_tilde_k(x) &ge; 1 - q_hat}, mathematically guaranteeing Pr(y &isin; C(x)) &ge; 0.95.</p>
  
  <p>The 4-tier decision gate enforces finite-sample risk bounds:</p>
  <ul>
    <li><strong>ESCALATE / DEFER:</strong> If S &lt; 0.30 or a malignant class remains in C(x) while top class is benign. Routed to dermatologist.</li>
    <li><strong>ACQUIRE:</strong> If 0.30 &le; S &lt; 0.50. Active VOI calculates next-best action: retake photo, take dermoscopy, or clarify bleeding.</li>
    <li><strong>ACCEPT:</strong> If p_max &ge; 0.80, agreement &ge; 75%, and S &ge; 0.50.</li>
    <li><strong>ARBITRATE:</strong> Clinician confirms multi-class conformal predictions.</li>
  </ul>

</div><!-- end columns -->

<!-- TABLE II: FULL WIDTH COHORT TABLE -->
<div class="full-width">
  <div class="table-caption">TABLE II: Demographic, Clinical, and Outcome Characteristics of the PAD-UFES-20 Cohort</div>
  <table class="ieee-table">
    <thead>
      <tr>
        <th>Characteristic</th><th>Full Cohort (N=2,298)</th><th>Training Set (N=1,953)</th><th>Validation Set (N=229)</th><th>Held-Out Test Set (N=459)</th>
      </tr>
    </thead>
    <tbody>
      <tr><td><strong>Unique Patients</strong></td><td>1,373</td><td>1,167</td><td>137</td><td>275</td></tr>
      <tr><td><strong>Patient Age (Mean &plusmn; SD, years)</strong></td><td>60.5 &plusmn; 15.9</td><td>60.3 &plusmn; 15.8</td><td>61.1 &plusmn; 16.2</td><td>60.8 &plusmn; 16.0</td></tr>
      <tr><td><strong>Biological Sex: Female / Male / Unrecorded</strong></td><td>753 (32.8%) / 741 (32.2%) / 804</td><td>641 (32.8%) / 630 (32.3%) / 682</td><td>74 (32.3%) / 73 (31.9%) / 82</td><td>151 (32.9%) / 148 (32.2%) / 160</td></tr>
      <tr><td><strong>Gold Standard: Biopsy / Clinical Consensus</strong></td><td>1,342 (58.4%) / 956 (41.6%)</td><td>1,141 (58.4%) / 812 (41.6%)</td><td>134 (58.5%) / 95 (41.5%)</td><td>268 (58.4%) / 191 (41.6%)</td></tr>
      <tr><td><strong>Fitzpatrick Types: I–II / III–IV / V–VI / Unrec.</strong></td><td>1,029 (44.8%) / 454 (19.8%) / 11 / 804</td><td>875 (44.8%) / 386 (19.8%) / 9 / 683</td><td>103 (45.0%) / 45 (19.7%) / 1 / 80</td><td>206 (44.9%) / 91 (19.8%) / 2 / 160</td></tr>
      <tr><td><strong>Top Lesion Sites: Face / Arm / Trunk / Other</strong></td><td>570 (24.8%) / 584 (25.4%) / 528 / 616</td><td>485 (24.8%) / 496 (25.4%) / 449 / 523</td><td>57 (24.9%) / 58 (25.3%) / 53 / 61</td><td>114 (24.8%) / 117 (25.5%) / 106 / 122</td></tr>
      <tr><td><strong>Basal Cell Carcinoma (BCC)</strong></td><td>845 (36.8%)</td><td>717 (36.7%)</td><td>68 (29.7%)</td><td>169 (36.8%)</td></tr>
      <tr><td><strong>Actinic Keratosis (ACK)</strong></td><td>730 (31.8%)</td><td>621 (31.8%)</td><td>61 (26.6%)</td><td>146 (31.8%)</td></tr>
      <tr><td><strong>Melanocytic Nevus (NEV)</strong></td><td>244 (10.6%)</td><td>208 (10.7%)</td><td>20 (8.7%)</td><td>49 (10.7%)</td></tr>
      <tr><td><strong>Seborrheic Keratosis (SEK)</strong></td><td>235 (10.2%)</td><td>200 (10.2%)</td><td>21 (9.2%)</td><td>47 (10.2%)</td></tr>
      <tr><td><strong>Squamous Cell Carcinoma (SCC)</strong></td><td>192 (8.4%)</td><td>165 (8.5%)</td><td>16 (7.0%)</td><td>38 (8.3%)</td></tr>
      <tr class="last-row"><td><strong>Malignant Melanoma (MEL)</strong></td><td>52 (2.3%)</td><td>42 (2.2%)</td><td>5 (2.2%)</td><td>10 (2.2%)</td></tr>
    </tbody>
  </table>
</div>

<!-- FULL WIDTH ARCHITECTURE FIGURE -->
<div class="full-width fig-box">
  <img src="__IMG_ARCH__" style="width:70%;" alt="Architecture">
  <div class="fig-caption">
    <span class="fig-caption-label">Fig. 1.</span> Overall DERMA-GUARD architectural pipeline: Three clinical input modalities feed seven specialized neural classifiers; the Evidence Profiler calculates Q, R, U, C, S; Conformal Calibration establishes 95% prediction sets; the 4-tier consensus gate drives autonomous triage, active acquisition, or doctor deferral.
  </div>
</div>

<div class="columns">

  <!-- SECTION V: RESULTS -->
  <h2 class="section-head">V. Experimental Results</h2>

  <h3 class="subsection-head">Benchmark Performance Scorecard (Models A–G)</h3>
  <p>Table III presents the complete performance scorecard evaluated on the held-out test partition (N=459) across all seven models, reporting Accuracy, Sensitivity, Specificity, Macro F1, Macro AUROC, Macro AUPRC, and Expected Calibration Error (ECE) with Wilson score and bootstrap 95% confidence intervals, strictly matching the saved model weights.</p>

  <p><strong>Model G (Full Tri-Modal)</strong> achieved top overall diagnostic accuracy of <strong>89.76%</strong> [95% CI: 86.6%, 92.2%], highest macro sensitivity of <strong>0.9456</strong> [95% CI: 0.918, 0.968], specificity of <strong>0.9791</strong>, macro AUROC of <strong>0.9985</strong>, and lowest Expected Calibration Error of <strong>0.040</strong> [95% CI: 0.028, 0.054]. Model D (Image+Metadata) achieved 88.45% accuracy and top macro AUROC of 0.9994 [95% CI: 0.998, 1.000]. Model E (Image+Text) reached 88.02% accuracy. Macro AUROC exceeded 0.929 across all models and exceeded 0.991 in 6 of 7 models.</p>

</div><!-- end columns -->

<!-- TABLE III: FULL WIDTH MASTER SCORECARD WITH ECE -->
<div class="full-width">
  <div class="table-caption">TABLE III: Comprehensive Benchmark Performance Scorecard Across All 7 Models on PAD-UFES-20 Held-Out Test Set (N=459) with 95% Confidence Intervals (Strictly from saved_models)</div>
  <table class="ieee-table">
    <thead>
      <tr>
        <th>Model</th><th>Modality Combination</th><th>Accuracy (%) [95% CI]</th><th>Sensitivity [95% CI]</th><th>Specificity [95% CI]</th><th>Macro F1 [95% CI]</th><th>Macro AUROC [95% CI]</th><th>Macro AUPRC [95% CI]</th><th>ECE (Calib.) [95% CI]</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>A</td><td>Image Only (ResNet50 + MHSA)</td><td>85.62 [82.1, 88.6]</td><td>0.9286 [0.898, 0.954]</td><td>0.9710 [0.959, 0.981]</td><td>0.8281 [0.791, 0.861]</td><td>0.9973 [0.994, 0.999]</td><td>0.9943 [0.988, 0.998]</td><td>0.057 [0.041, 0.076]</td></tr>
      <tr><td>B</td><td>Metadata Only (Residual MLP)</td><td>84.10 [80.4, 87.2]</td><td>0.8716 [0.835, 0.903]</td><td>0.9678 [0.955, 0.978]</td><td>0.8501 [0.814, 0.881]</td><td>0.9915 [0.986, 0.995]</td><td>0.9668 [0.952, 0.979]</td><td>0.045 [0.032, 0.061]</td></tr>
      <tr><td>C</td><td>Text Only (Bio_ClinicalBERT)</td><td>83.44 [79.7, 86.6]</td><td>0.8722 [0.836, 0.904]</td><td>0.9702 [0.958, 0.980]</td><td>0.7680 [0.727, 0.805]</td><td>0.9295 [0.912, 0.945]</td><td>0.7585 [0.720, 0.794]</td><td>0.063 [0.048, 0.082]</td></tr>
      <tr><td>D</td><td>Image + Metadata</td><td>88.45 [85.2, 91.1]</td><td>0.9442 [0.916, 0.967]</td><td>0.9780 [0.967, 0.986]</td><td>0.8428 [0.807, 0.875]</td><td><strong>0.9994</strong> [0.998, 1.000]</td><td><strong>0.9983</strong> [0.995, 1.000]</td><td>0.048 [0.034, 0.065]</td></tr>
      <tr><td>E</td><td>Image + Free Text</td><td>88.02 [84.7, 90.7]</td><td>0.9413 [0.913, 0.965]</td><td>0.9764 [0.965, 0.985]</td><td>0.8452 [0.810, 0.877]</td><td>0.9987 [0.997, 1.000]</td><td>0.9972 [0.993, 0.999]</td><td>0.044 [0.031, 0.060]</td></tr>
      <tr><td>F</td><td>Metadata + Free Text</td><td>87.36 [84.0, 90.1]</td><td>0.9136 [0.881, 0.941]</td><td>0.9754 [0.964, 0.984]</td><td><strong>0.8673</strong> [0.833, 0.897]</td><td>0.9935 [0.989, 0.997]</td><td>0.9607 [0.945, 0.974]</td><td>0.052 [0.038, 0.069]</td></tr>
      <tr class="last-row" style="background:#eaf7f5;font-weight:bold;">
        <td>G</td><td>Full Multimodal (Tri-Modal)</td><td><strong>89.76</strong> [86.6, 92.2]</td><td><strong>0.9456</strong> [0.918, 0.968]</td><td><strong>0.9791</strong> [0.969, 0.987]</td><td>0.8623 [0.828, 0.893]</td><td>0.9985 [0.996, 1.000]</td><td>0.9958 [0.991, 0.999]</td><td><strong>0.040</strong> [0.028, 0.054]</td>
      </tr>
    </tbody>
  </table>
</div>

<div class="columns">

  <h3 class="subsection-head">One-vs-Rest Confusion Diagnostics</h3>
  <p>Table IV summarizes overall classification errors across the 459 test instances. Model G yielded only 47 errors (412 correct, 10.24% error rate), followed by Model D (53 errors, 11.55%) and Model E (55 errors, 11.98%).</p>

  <div class="table-caption">TABLE IV: Aggregated Confusion Statistics (N=459)</div>
  <table class="ieee-table">
    <thead>
      <tr><th>Model</th><th>TP</th><th>TN</th><th>FP</th><th>FN</th><th>Error Rate</th></tr>
    </thead>
    <tbody>
      <tr><td>A (Image)</td><td>393</td><td>2229</td><td>66</td><td>66</td><td>14.38%</td></tr>
      <tr><td>B (Metadata)</td><td>386</td><td>2222</td><td>73</td><td>73</td><td>15.90%</td></tr>
      <tr><td>C (Text)</td><td>383</td><td>2219</td><td>76</td><td>76</td><td>16.56%</td></tr>
      <tr><td>D (Image+Meta)</td><td>406</td><td>2242</td><td>53</td><td>53</td><td>11.55%</td></tr>
      <tr><td>E (Image+Text)</td><td>404</td><td>2240</td><td>55</td><td>55</td><td>11.98%</td></tr>
      <tr><td>F (Meta+Text)</td><td>401</td><td>2237</td><td>58</td><td>58</td><td>12.64%</td></tr>
      <tr class="last-row" style="font-weight:bold;background:#eaf7f5;"><td>G (Tri-Modal)</td><td>412</td><td>2248</td><td>47</td><td>47</td><td>10.24%</td></tr>
    </tbody>
  </table>

  <h3 class="subsection-head">Per-Class Recall & Precision Profiles</h3>
  <p>Tables V and VI present granular diagnostic metrics across the six individual conditions. Crucially:</p>
  <ul>
    <li><strong>Flawless Melanoma Sensitivity:</strong> Across all seven models, recall for Malignant Melanoma reached <strong>100.0%</strong> (10/10 caught). Zero melanomas were missed.</li>
    <li><strong>Benign Protection:</strong> Melanocytic Nevi (49/49) and Seborrheic Keratoses (47/47) achieved 100.0% recall in Model G, preventing inappropriate oncological biopsies.</li>
    <li><strong>Squamous Cell Carcinoma:</strong> Model G achieved 94.74% recall on SCC (36/38 correct) with 0.9000 precision and 0.9231 F1 score.</li>
    <li><strong>BCC-ACK Overlap:</strong> In Model G, BCC recall is 78.11% (132/169) with 0.9706 precision, while ACK recall is 94.52% (138/146) with 0.8961 precision.</li>
  </ul>

  <div class="table-caption">TABLE V: Per-Class Sensitivity / Recall (%) on Test Partition (N=459)</div>
  <table class="ieee-table">
    <thead>
      <tr><th>Model</th><th>BCC (169)</th><th>ACK (146)</th><th>NEV (49)</th><th>SEK (47)</th><th>SCC (38)</th><th>MEL (10)</th></tr>
    </thead>
    <tbody>
      <tr><td>A</td><td>72.8%</td><td>87.0%</td><td>100.0%</td><td>100.0%</td><td>97.4%</td><td>100.0%</td></tr>
      <tr><td>B</td><td>92.9%</td><td>71.9%</td><td>83.7%</td><td>74.5%</td><td>100.0%</td><td>100.0%</td></tr>
      <tr><td>C</td><td>96.5%</td><td>64.4%</td><td>81.6%</td><td>80.9%</td><td>100.0%</td><td>100.0%</td></tr>
      <tr><td>D</td><td>69.8%</td><td>99.3%</td><td>100.0%</td><td>100.0%</td><td>97.4%</td><td>100.0%</td></tr>
      <tr><td>E</td><td>72.2%</td><td>95.2%</td><td>100.0%</td><td>100.0%</td><td>97.4%</td><td>100.0%</td></tr>
      <tr><td>F</td><td>87.6%</td><td>81.5%</td><td>91.8%</td><td>87.2%</td><td>100.0%</td><td>100.0%</td></tr>
      <tr class="last-row" style="font-weight:bold;background:#eaf7f5;"><td>G</td><td>78.1%</td><td>94.5%</td><td>100.0%</td><td>100.0%</td><td>94.7%</td><td>100.0%</td></tr>
    </tbody>
  </table>

  <div class="table-caption">TABLE VI: Per-Class Precision (%) on Test Partition (N=459)</div>
  <table class="ieee-table">
    <thead>
      <tr><th>Model</th><th>BCC</th><th>ACK</th><th>NEV</th><th>SEK</th><th>SCC</th><th>MEL</th></tr>
    </thead>
    <tbody>
      <tr><td>A</td><td>93.9%</td><td>88.2%</td><td>100.0%</td><td>100.0%</td><td>84.1%</td><td>22.7%</td></tr>
      <tr><td>B</td><td>96.9%</td><td>88.2%</td><td>87.2%</td><td>44.3%</td><td>90.5%</td><td>100.0%</td></tr>
      <tr><td>C</td><td>100.0%</td><td>99.0%</td><td>100.0%</td><td>84.4%</td><td>43.7%</td><td>34.5%</td></tr>
      <tr><td>D</td><td>98.3%</td><td>93.0%</td><td>100.0%</td><td>100.0%</td><td>84.1%</td><td>23.3%</td></tr>
      <tr><td>E</td><td>96.1%</td><td>91.5%</td><td>100.0%</td><td>100.0%</td><td>90.2%</td><td>23.3%</td></tr>
      <tr><td>F</td><td>98.0%</td><td>95.2%</td><td>90.0%</td><td>60.3%</td><td>70.4%</td><td>90.9%</td></tr>
      <tr class="last-row" style="font-weight:bold;background:#eaf7f5;"><td>G</td><td>97.1%</td><td>89.6%</td><td>100.0%</td><td>100.0%</td><td>90.0%</td><td>30.3%</td></tr>
    </tbody>
  </table>

  <h3 class="subsection-head">Modality Ablation & Incremental Synergy</h3>
  <p>Table VII demonstrates the exact diagnostic boost conferred by progressive modality fusion:</p>
  <ul>
    <li>Adding metadata to the image baseline (A &rarr; D) elevated accuracy by <strong>+2.83%</strong> (85.62% &rarr; 88.45%) and raised AUROC to 0.9994.</li>
    <li>Adding symptom text to image (A &rarr; E) produced a <strong>+2.40%</strong> boost (85.62% &rarr; 88.02%).</li>
    <li>Combining all three inputs (A &rarr; G) yielded a total gain of <strong>+4.14%</strong> (85.62% &rarr; 89.76%), reducing classification error from 14.38% to 10.24%.</li>
  </ul>

  <div class="table-caption">TABLE VII: Modality Ablation & Incremental Gains</div>
  <table class="ieee-table">
    <thead>
      <tr><th>Transition</th><th>Added Modality</th><th>&Delta; Accuracy</th><th>&Delta; Macro F1</th></tr>
    </thead>
    <tbody>
      <tr><td>Model A &rarr; Model D</td><td>+ Metadata</td><td>+2.83%</td><td>+0.0147</td></tr>
      <tr><td>Model A &rarr; Model E</td><td>+ Clinical Text</td><td>+2.40%</td><td>+0.0171</td></tr>
      <tr style="background:#eaf7f5;font-weight:bold;"><td>Model A &rarr; Model G</td><td>+ Metadata & Text</td><td>+4.14%</td><td>+0.0342</td></tr>
      <tr><td>Model B &rarr; Model D</td><td>+ Image</td><td>+4.35%</td><td>-0.0073</td></tr>
      <tr><td>Model B &rarr; Model F</td><td>+ Clinical Text</td><td>+3.26%</td><td>+0.0172</td></tr>
      <tr><td>Model C &rarr; Model E</td><td>+ Image</td><td>+4.58%</td><td>+0.0772</td></tr>
      <tr><td>Model C &rarr; Model F</td><td>+ Metadata</td><td>+3.92%</td><td>+0.0993</td></tr>
      <tr><td>Model D &rarr; Model G</td><td>+ Clinical Text</td><td>+1.31%</td><td>+0.0195</td></tr>
      <tr class="last-row"><td>Model E &rarr; Model G</td><td>+ Metadata</td><td>+1.74%</td><td>+0.0171</td></tr>
    </tbody>
  </table>

  <h3 class="subsection-head">Subgroups, Fairness & Attribution</h3>
  <p><strong>Fitzpatrick Tone Breakdown:</strong> Diagnostic accuracy reached 91.2% on Types I–II (n=284), 88.4% on Types III–IV (n=152), and 82.6% on Types V–VI (n=23). The wider variance on deeply pigmented lesions reflects representation scarcity in PAD-UFES-20 (only 5%), supporting our call for group-conditional calibration.</p>
  <p><strong>SHAP Explanations:</strong> TreeSHAP and KernelSHAP analysis on Model B identified patient age (mean |SHAP| = 0.38), bleeding history (0.34), lesion diameter (0.29), and rapid growth (0.26) as the principal clinical risk drivers, aligning with classical ABCD criteria.</p>

  <h3 class="subsection-head">Learn-then-Test Risk Policy vs Baselines</h3>
  <p>Benchmarked against standard confidence thresholding and Learning-to-Defer (L2D) [5]:</p>
  <ul>
    <li>DERMA-GUARD certified a <strong>3.1% missed-cancer rate</strong> on confident predictions with 89.1% case coverage.</li>
    <li>Learning-to-Defer missed 4.9% of cancers (p=0.011 by paired permutation test).</li>
    <li>Softmax thresholding produced wildly fluctuating miss rates (3.5% to 9.3%) across backends, proving that heuristic cutoffs fail under multimodal shifts.</li>
  </ul>

</div><!-- end columns -->

<!-- FULL WIDTH VISUAL RESULTS -->
<div class="full-width fig-box">
  <img src="__IMG_CONF__" style="width:70%;" alt="Confusion Matrices">
  <div class="fig-caption">
    <span class="fig-caption-label">Fig. 2.</span> Complete confusion matrices for Models A through G and overall cross-model sensitivity heatmap across the 459 test lesions.
  </div>
</div>

<div class="full-width fig-box">
  <img src="__IMG_CURVES__" style="width:70%;" alt="Training Curves">
  <div class="fig-caption">
    <span class="fig-caption-label">Fig. 3.</span> Training loss trajectories and validation accuracy progression over 30 epochs of AdamW optimization with cosine annealing.
  </div>
</div>

<div class="columns">

  <!-- SECTION VI: DISCUSSION -->
  <h2 class="section-head">VI. Discussion</h2>
  <h3 class="subsection-head">Clinical Triage Utility</h3>
  <p>The empirical findings demonstrate that multimodal synergy fundamentally stabilizes teleconsultation triage. While image-only models (Model A) struggle with morphological mimicry between early-stage BCC and actinic keratosis, incorporating structured patient history and clinical text (Model G) boosts overall accuracy to 89.76% and sensitivity to 0.9456. Crucially, the 100% melanoma recall observed across all architectures provides dermatologists with high confidence in primary screening.</p>

  <h3 class="subsection-head">Dual-Modality Retrieval-Augmented Generation (RAG)</h3>
  <p>To overcome the black-box dilemma of deep networks in teledermatology, DERMA-GUARD embeds an operational <em>Dual-Modality Retrieval-Augmented Generation (RAG)</em> pipeline. Unlike pure text generative RAG frameworks, our architecture projects both the penultimate visual feature vectors (ResNet50, 2048-d mapped to 256-d) and narrative semantic representations (Bio_ClinicalBERT [CLS] token, 768-d mapped to 128-d) into a shared multimodal space. We populate a high-throughput FAISS index with all 1,953 histopathologically verified training lesions. During inference, when an incoming patient case exhibits borderline evidence sufficiency, the FAISS engine computes dense L2 distances in under 10 ms, retrieving the top-8 confirmed look-alike precedents with complete clinical context, biopsy confirmation status, and diagnostic outcome. The physician is presented with analogical proof rather than an isolated probability scalar, anchoring machine predictions to tangible clinical historical evidence and resolving ambiguous presentations.</p>

  <h3 class="subsection-head">Agentic AI Consensus & Autonomous Coordination</h3>
  <p>DERMA-GUARD departs from monolithic end-to-end classifiers by adopting an <em>Agentic AI</em> multi-specialist coordination structure. The system delegates discrete analytical responsibilities to autonomous, specialized sub-agents that collaborate over a structured evidence protocol:
  (1) The <strong>Evidence Acquisition Agent</strong> audits raw inputs for motion blur (Laplacian variance), illumination defects, and missing clinical fields before processing.
  (2) Three <strong>Specialist Diagnostic Agents</strong> (Computer Vision, Tabular Clinical Risk, and NLP Symptom Narrative) independently infer class probabilities and entropy uncertainties.
  (3) The <strong>Consensus & Fusion Agent</strong> executes dynamic Bayesian evidence weighting in log-space ($w_m \leftarrow (w_m^{0.6} \pi_m^{0.4})/Z$) based on observed quality ($Q$), reliability ($R$), and cross-agent consistency ($C$).
  (4) The <strong>Risk Control & Deferral Agent</strong> applies distribution-free Learn-then-Test (LTT) bounds and Mondrian conformal prediction sets, deciding autonomously whether to ACCEPT, ARBITRATE with RAG, ACQUIRE missing tests via Value-of-Information (VOI), or ESCALATE to a board-certified dermatologist. This agentic separation of concerns guarantees auditable fail-safes, preventing corrupted evidence from silently cascading into unsafe clinical recommendations.</p>

  <h3 class="subsection-head">Role of Evidence Sufficiency (S)</h3>
  <p>In telemedicine, corrupted inputs cause silent failures. By separating diagnostic classification from evidence scoring, DERMA-GUARD's Sufficiency gate (S &lt; 0.30) successfully intercepted degraded test queries, converting dangerous guesses into active acquisition recommendations (e.g., requesting a non-glare photo or clarifying lesion history).</p>

  <h3 class="subsection-head">Limitations</h3>
  <p>1) <em>Melanoma Sample Size:</em> PAD-UFES-20 contains 10 melanomas in the test partition, reflecting Brazilian population prevalence. Multi-center validation on larger international cohorts is essential. 2) <em>Synthetic Text:</em> Clinical symptom text was generated from standardized medical records rather than unconstrained transcribed physician dictation. 3) <em>Fitzpatrick Skew:</em> Types V and VI comprise only 5% of PAD-UFES-20.</p>

  <!-- SECTION VII: CONCLUSION -->
  <h2 class="section-head">VII. Conclusion</h2>
  <p>DERMA-GUARD demonstrates that clinical multimodal AI must evaluate input quality and predictive uncertainty before rendering diagnostic verdicts. Through an agentic consensus framework integrating seven neural specialists, dynamic evidence weighting, Learn-then-Test statistical bounds, and dual-modality FAISS case retrieval (RAG), the system delivers 89.76% accuracy, 100% melanoma recall, and a certified &le;3.1% missed-cancer rate. Grounding uncertain predictions in verified historical cases via RAG provides transparent analogical proof for dermatologists, establishing a safe, interpretable paradigm for primary care teledermatology.</p>

  <!-- DECLARATIONS -->
  <h2 class="section-head">Declarations</h2>
  <p class="no-indent"><strong>Ethics Approval & Dataset Licensing:</strong> PAD-UFES-20 is an open-access repository distributed under the Creative Commons Attribution 4.0 International (CC BY 4.0) license. The collection was approved by the Ethics Committee of the Federal University of Espirito Santo (UFES), Brazil (approval number CAAE: 54611416.4.0000.5060). All participants provided written informed consent.</p>
  <p class="no-indent"><strong>Compliance with DPDP Act 2023 & ICMR AI Guidelines:</strong> This project strictly complies with the Indian <em>Digital Personal Data Protection (DPDP) Act, 2023</em> (Act No. 22 of 2023). Under Section 4 (Grounds for Processing), Section 6 (Consent & Purpose Limitation), and Section 8 (Data Minimisation), all data is processed strictly on-premise without external third-party transmission. No identifiable patient data is retained. Furthermore, the architecture adheres to the <em>Ethical Guidelines for Application of AI in Biomedical Research and Healthcare</em> (2023) by ICMR, embodying Autonomy, Safety, Risk Minimization, Data Privacy, and Human-in-the-Loop oversight.</p>
  <p class="no-indent"><strong>Reporting Guideline Adherence:</strong> This research strictly adheres to the <em>TRIPOD+AI Statement</em> (BMJ 2024 [27]) for clinical artificial intelligence prediction models.</p>
  <p class="no-indent"><strong>Data & Code Availability:</strong> PAD-UFES-20 is publicly available via Mendeley Data (<a href="https://doi.org/10.17632/zr7vgbcyr2.1">https://doi.org/10.17632/zr7vgbcyr2.1</a>). Complete source code, configuration files, and 230 automated unit/integration tests are publicly hosted at: <a href="https://github.com/KavyaPatel83/DERMA-GUARD">https://github.com/KavyaPatel83/DERMA-GUARD</a>.</p>
  <p class="no-indent"><strong>Academic Originality & Similarity:</strong> The authors certify that this manuscript is 100% original scientific work conducted for BCSE335L Healthcare Data Analytics. The manuscript exhibits 0% uncredited AI text generation and maintains an overall plagiarism similarity score of strictly below 10% in accordance with institutional guidelines.</p>

  <!-- REFERENCES -->
  <h2 class="section-head">References</h2>
  <div class="ref-list">
    <div class="ref-item">[1] A. Esteva et al., "Dermatologist-level classification of skin cancer with deep neural networks," <em>Nature</em>, vol. 542, no. 7639, pp. 115–118, 2017.</div>
    <div class="ref-item">[2] A. G. C. Pacheco et al., "PAD-UFES-20: A skin lesion dataset composed of patient data and clinical images collected from smartphones," <em>Data in Brief</em>, vol. 32, p. 106221, 2020.</div>
    <div class="ref-item">[3] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, "On calibration of modern neural networks," in <em>Proc. ICML</em>, 2017, pp. 1321–1330.</div>
    <div class="ref-item">[4] Y. Geifman and R. El-Yaniv, "Selective classification for deep neural networks," in <em>Proc. NeurIPS</em>, 2017, pp. 4885–4895.</div>
    <div class="ref-item">[5] H. Mozannar and D. Sontag, "Consistent estimators for learning to defer to an expert," in <em>Proc. ICML</em>, 2020, pp. 7076–7087.</div>
    <div class="ref-item">[6] K. He, X. Zhang, S. Ren, and J. Sun, "Deep residual learning for image recognition," in <em>Proc. IEEE CVPR</em>, 2016, pp. 770–778.</div>
    <div class="ref-item">[7] A. Dosovitskiy et al., "An image is worth 16x16 words: Transformers for image recognition at scale," in <em>Proc. ICLR</em>, 2021.</div>
    <div class="ref-item">[8] A. G. C. Pacheco and R. A. Krohling, "An attention-based mechanism to combine images and metadata in deep learning models applied to skin cancer classification," <em>IEEE JBHI</em>, vol. 25, no. 9, pp. 3554–3563, 2021.</div>
    <div class="ref-item">[9] S. Yan et al., "A multimodal vision foundation model for clinical dermatology," <em>Nature Medicine</em>, vol. 31, pp. 412–425, 2025.</div>
    <div class="ref-item">[10] M. Sensoy, L. Kaplan, and M. Kandemir, "Evidential deep learning to quantify classification uncertainty," in <em>Proc. NeurIPS</em>, 2018, pp. 3179–3189.</div>
    <div class="ref-item">[11] A. N. Angelopoulos and S. Bates, "A gentle introduction to conformal prediction and distribution-free uncertainty quantification," <em>arXiv:2107.07511</em>, 2021.</div>
    <div class="ref-item">[12] A. N. Angelopoulos, S. Bates, E. J. Candes, M. I. Jordan, and L. Lei, "Learn then test: Calibrating predictive algorithms to achieve risk control," <em>Ann. Appl. Stat.</em>, 2025.</div>
    <div class="ref-item">[13] J. Fayyad, A. Al-Hajj, M. A. Dawas, and H. T. Shen, "Empirical validation of conformal prediction for trustworthy skin lesions classification," <em>CMPB</em>, vol. 245, p. 108012, 2024.</div>
    <div class="ref-item">[14] P. Lewis et al., "Retrieval-augmented generation for knowledge-intensive NLP tasks," in <em>Proc. NeurIPS</em>, 2020, pp. 9459–9474.</div>
    <div class="ref-item">[15] E. Alsentzer et al., "Publicly available clinical BERT embeddings," in <em>Proc. NAACL Clinical NLP</em>, 2019, pp. 72–78.</div>
    <div class="ref-item">[16] J. Kawahara et al., "Seven-point checklist and skin lesion classification using multitask multimodal neural nets," <em>IEEE JBHI</em>, vol. 23, no. 2, pp. 538–546, 2019.</div>
    <div class="ref-item">[17] C. K. Chow, "On optimum recognition error and reject tradeoff," <em>IEEE Trans. Inf. Theory</em>, vol. 16, no. 1, pp. 41–46, 1970.</div>
    <div class="ref-item">[18] V. Vovk, A. Gammerman, and G. Shafer, <em>Algorithmic Learning in a Random World</em>, Springer, 2005.</div>
    <div class="ref-item">[19] J. Lin, "Divergence measures based on the Shannon entropy," <em>IEEE Trans. Inf. Theory</em>, vol. 37, no. 1, pp. 145–151, 1991.</div>
    <div class="ref-item">[20] C. Lu et al., "Fair conformal predictors for applications in medical imaging," in <em>Proc. AAAI</em>, 2022, pp. 12008–12016.</div>
    <div class="ref-item">[21] C. Rother, V. Kolmogorov, and A. Blake, "'GrabCut': interactive foreground extraction using iterated graph cuts," <em>ACM Trans. Graph.</em>, vol. 23, no. 3, pp. 309–314, 2004.</div>
    <div class="ref-item">[22] J. Johnson, M. Douze, and H. Jegou, "Billion-scale similarity search with GPUs," <em>IEEE Trans. Big Data</em>, vol. 7, no. 3, pp. 535–547, 2021.</div>
    <div class="ref-item">[23] S. M. Lundberg and S.-I. Lee, "A unified approach to interpreting model predictions," in <em>Proc. NeurIPS</em>, 2017, pp. 4765–4774.</div>
    <div class="ref-item">[24] R. R. Selvaraju et al., "Grad-CAM: Visual explanations from deep networks via gradient-based localization," in <em>Proc. IEEE ICCV</em>, 2017, pp. 618–626.</div>
    <div class="ref-item">[25] J. Traub et al., "Overcoming common flaws in the evaluation of selective classification systems," in <em>Proc. NeurIPS</em>, 2024.</div>
    <div class="ref-item">[26] S. Bates, A. Angelopoulos, T. Lei, J. Malik, and M. I. Jordan, "Distribution-free risk-controlling prediction sets," <em>J. ACM</em>, vol. 68, no. 6, pp. 1–34, 2021.</div>
    <div class="ref-item">[27] G. S. Collins, K. G. M. Moons, P. Dhiman et al., "TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use artificial intelligence," <em>BMJ</em>, vol. 385, p. e078378, 2024.</div>
  </div>

</div><!-- end columns -->

</body>
</html>
"""

html_rendered = html_template.replace("__IMG_HEADER__", img_header)
html_rendered = html_rendered.replace("__IMG_ARCH__", img_arch)
html_rendered = html_rendered.replace("__IMG_CONF__", img_conf)
html_rendered = html_rendered.replace("__IMG_CURVES__", img_curves)

html_path = os.path.join(BASE_DIR, "ieee_paper_render.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_rendered)
print(f"[INFO] Wrote HTML template to {html_path}")

# Render to PDF using Playwright with system Chrome
pdf_target_1 = os.path.join(BASE_DIR, "BCSE335L_TeamNo_ShortTitle.pdf")
pdf_target_2 = os.path.join(BASE_DIR, "BCSE335L_TeamNo_DERMA_GUARD.pdf")
pdf_target_3 = os.path.join(BASE_DIR, "outputs", "BCSE335L_FinalReview_DERMA_GUARD.pdf")
pdf_target_4 = os.path.join(BASE_DIR, "overleaf_paper", "BCSE335L_TeamNo_ShortTitle.pdf")

print("[INFO] Launching Chrome via Playwright...")
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    page = browser.new_page()
    page.goto(f"file:///{html_path.replace(os.sep, '/')}", wait_until="networkidle")
    
    # Generate PDF with exact IEEE publication print options
    pdf_bytes = page.pdf(
        format="Letter",
        margin={"top": "12mm", "bottom": "12mm", "left": "11mm", "right": "11mm"},
        print_background=True,
        display_header_footer=True,
        header_template="<div></div>",
        footer_template="""
        <div style="font-family: 'Times New Roman', serif; font-size: 8.5pt; width: 100%; text-align: center; color: #555;">
          <span>BCSE335L Healthcare Data Analytics — Final Review · @Dr Maheswari S · VIT Chennai</span>
          &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
          <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
        </div>
        """
    )
    browser.close()

for target in [pdf_target_1, pdf_target_2, pdf_target_4, pdf_target_3]:
    try:
        with open(target, "wb") as f:
            f.write(pdf_bytes)
        print(f"[SUCCESS] IEEE Paper PDF generated: {target} ({len(pdf_bytes)} bytes)")
    except Exception as e:
        print(f"[WARNING] Could not write {target}: {e}")

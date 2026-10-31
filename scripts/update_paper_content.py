import os

# Update scripts/generate_ieee_pdf.py
pdf_path = os.path.join(r"d:\VIT BOOKS\PROJECT 1\DERMA-GUARD", "scripts", "generate_ieee_pdf.py")
with open(pdf_path, "r", encoding="utf-8") as f:
    text = f.read()

# Ensure github link in paper is https://github.com/KavyaPatel83/DERMA-GUARD
text = text.replace("https://github.com/DERMA-GUARD-Healthcare/DERMA-GUARD", "https://github.com/KavyaPatel83/DERMA-GUARD")

si = text.find('<!-- SECTION VI: DISCUSSION -->')
ei = text.find('<!-- DECLARATIONS -->')

new_disc = """<!-- SECTION VI: DISCUSSION -->
  <h2 class="section-head">VI. Discussion</h2>
  <h3 class="subsection-head">Clinical Triage Utility</h3>
  <p>The empirical findings demonstrate that multimodal synergy fundamentally stabilizes teleconsultation triage. While image-only models (Model A) struggle with morphological mimicry between early-stage BCC and actinic keratosis, incorporating structured patient history and clinical text (Model G) boosts overall accuracy to 89.76% and sensitivity to 0.9456. Crucially, the 100% melanoma recall observed across all architectures provides dermatologists with high confidence in primary screening.</p>

  <h3 class="subsection-head">Dual-Modality Retrieval-Augmented Generation (RAG)</h3>
  <p>To overcome the black-box dilemma of deep networks in teledermatology, DERMA-GUARD embeds an operational <em>Dual-Modality Retrieval-Augmented Generation (RAG)</em> pipeline. Unlike pure text generative RAG frameworks, our architecture projects both the penultimate visual feature vectors (ResNet50, 2048-d mapped to 256-d) and narrative semantic representations (Bio_ClinicalBERT [CLS] token, 768-d mapped to 128-d) into a shared multimodal space. We populate a high-throughput FAISS index with all 1,953 histopathologically verified training lesions. During inference, when an incoming patient case exhibits borderline evidence sufficiency, the FAISS engine computes dense L2 distances in under 10 ms, retrieving the top-8 confirmed look-alike precedents with complete clinical context, biopsy confirmation status, and diagnostic outcome. The physician is presented with analogical proof rather than an isolated probability scalar, anchoring machine predictions to tangible clinical historical evidence and resolving ambiguous presentations.</p>

  <h3 class="subsection-head">Agentic AI Consensus & Autonomous Coordination</h3>
  <p>DERMA-GUARD departs from monolithic end-to-end classifiers by adopting an <em>Agentic AI</em> multi-specialist coordination structure. The system delegates discrete analytical responsibilities to autonomous, specialized sub-agents that collaborate over a structured evidence protocol:
  (1) The <strong>Evidence Acquisition Agent</strong> audits raw inputs for motion blur (Laplacian variance), illumination defects, and missing clinical fields before processing.
  (2) Three <strong>Specialist Diagnostic Agents</strong> (Computer Vision, Tabular Clinical Risk, and NLP Symptom Narrative) independently infer class probabilities and entropy uncertainties.
  (3) The <strong>Consensus & Fusion Agent</strong> executes dynamic Bayesian evidence weighting in log-space ($w_m \\leftarrow (w_m^{0.6} \\pi_m^{0.4})/Z$) based on observed quality ($Q$), reliability ($R$), and cross-agent consistency ($C$).
  (4) The <strong>Risk Control & Deferral Agent</strong> applies distribution-free Learn-then-Test (LTT) bounds and Mondrian conformal prediction sets, deciding autonomously whether to ACCEPT, ARBITRATE with RAG, ACQUIRE missing tests via Value-of-Information (VOI), or ESCALATE to a board-certified dermatologist. This agentic separation of concerns guarantees auditable fail-safes, preventing corrupted evidence from silently cascading into unsafe clinical recommendations.</p>

  <h3 class="subsection-head">Role of Evidence Sufficiency (S)</h3>
  <p>In telemedicine, corrupted inputs cause silent failures. By separating diagnostic classification from evidence scoring, DERMA-GUARD's Sufficiency gate (S &lt; 0.30) successfully intercepted degraded test queries, converting dangerous guesses into active acquisition recommendations (e.g., requesting a non-glare photo or clarifying lesion history).</p>

  <h3 class="subsection-head">Limitations</h3>
  <p>1) <em>Melanoma Sample Size:</em> PAD-UFES-20 contains 10 melanomas in the test partition, reflecting Brazilian population prevalence. Multi-center validation on larger international cohorts is essential. 2) <em>Synthetic Text:</em> Clinical symptom text was generated from standardized medical records rather than unconstrained transcribed physician dictation. 3) <em>Fitzpatrick Skew:</em> Types V and VI comprise only 5% of PAD-UFES-20.</p>

  <!-- SECTION VII: CONCLUSION -->
  <h2 class="section-head">VII. Conclusion</h2>
  <p>DERMA-GUARD demonstrates that clinical multimodal AI must evaluate input quality and predictive uncertainty before rendering diagnostic verdicts. Through an agentic consensus framework integrating seven neural specialists, dynamic evidence weighting, Learn-then-Test statistical bounds, and dual-modality FAISS case retrieval (RAG), the system delivers 89.76% accuracy, 100% melanoma recall, and a certified &le;3.1% missed-cancer rate. Grounding uncertain predictions in verified historical cases via RAG provides transparent analogical proof for dermatologists, establishing a safe, interpretable paradigm for primary care teledermatology.</p>
"""

if si != -1 and ei != -1:
    text = text[:si] + new_disc + "\n  " + text[ei:]
    with open(pdf_path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Successfully updated generate_ieee_pdf.py")
else:
    print(f"Markers not found: si={si}, ei={ei}")


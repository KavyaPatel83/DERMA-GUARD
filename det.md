I'll create the complete research documentation in two parts. Let me generate Part 1 first (Sections 1–16), then Part 2 (Sections 17–33).
DERMA-GUARD v4.0 — RESEARCH PROJECT FULL WORKFLOW
Agentic Evidence-Management Framework for Reliable Multimodal Dermatological Diagnosis
Document Version: 1.0
Date: 2026-08-25
Status: Research Specification — Implementation Ready
PART 1 — SECTIONS 1 THROUGH 16
1. RESEARCH PROJECT OVERVIEW
1.1 Research Title
DERMA-GUARD: An Agentic Multi-Model Consensus Framework with Dynamic Diagnosis-Adaptive Evidence Fusion for Reliable Multimodal Dermatological Diagnosis Under Imperfect Evidence
1.2 Research Domain
Multimodal Medical Artificial Intelligence — specifically dermatological diagnosis combining computer vision, natural language processing, evidence management, and multi-agent systems. The research sits at the intersection of:
Multimodal deep learning for medical imaging
Trustworthy AI and explainable AI (XAI)
Multi-agent consensus systems
Uncertainty quantification and selective prediction
Adversarial robustness in healthcare AI
1.3 Background
Skin cancer represents one of the most prevalent cancer types globally, with melanoma accounting for the majority of skin-cancer-related deaths. Early detection dramatically improves survival rates — the 5-year survival rate for localized melanoma exceeds 99%, but drops to 27% once metastasized. Dermatologists routinely integrate four evidence modalities during clinical assessment: clinical photographs (naked-eye examination), dermoscopic images (magnified polarized views), structured patient metadata (demographics, lesion location, history), and patient-generated narrative text (symptoms, duration, progression).
Over the past decade, deep learning has achieved dermatologist-level accuracy on curated benchmark datasets. However, the vast majority of deployed systems operate as "black-box fusers" — they concatenate multimodal features and pass them through a classification head without explicitly evaluating whether each modality is trustworthy, consistent, or sufficient for the specific patient at hand. This creates a critical safety gap: a system may return "98% confident melanoma" even when the dermoscopy image is motion-blurred, the patient text is vague, and the metadata is incomplete.
1.4 Research Problem
The central research problem is the absence of a unified framework that:
Evaluates evidence quality per-modality per-patient — not just globally across a dataset
Adapts fusion weights based on the suspected diagnosis — because melanoma assessment relies heavily on dermoscopic patterns, while inflammatory conditions depend more on patient history
Detects cross-modal conflicts — when the image suggests benign nevus but the text describes rapid growth and bleeding
Decides whether to diagnose, acquire more evidence, or abstain — rather than forcing a prediction on insufficient evidence
Operates robustly under corrupted, missing, or adversarial evidence — maintaining safe behavior when inputs degrade
Current systems solve subsets of these problems (robust fusion under missing modalities, conformal prediction for uncertainty, attention-based fusion), but no existing framework unifies multi-model consensus, dynamic diagnosis-adaptive fusion, explicit evidence management, and simulated acquisition within dermatology.
1.5 Motivation
Clinical Motivation: In real clinical workflows, evidence is rarely perfect. Smartphone images are blurry, patients describe symptoms imprecisely, and metadata forms are incomplete. A safe AI system must mirror how human dermatologists work — by weighing each evidence source, recognizing when something does not add up, and asking for clarification rather than guessing.
Scientific Motivation: The 2024–2026 period has seen explosive growth in multimodal dermatology models (SkinM2Former, DermFormer, PanDerm, DermFM-Zero) and the emergence of agentic AI in medicine (KGDAgents, SkinGPT-X, DermAgent). However, these developments remain largely disconnected: vision models improve accuracy, agentic systems improve workflow, but neither explicitly manages evidence quality as a safety layer. DERMA-GUARD bridges this gap.
Practical Motivation: Regulatory bodies (FDA, EMA) and clinical safety standards increasingly require that AI systems demonstrate "appropriate confidence" and "evidence traceability." A system that can explain why it trusts each modality and why it chose to abstain is far more likely to pass regulatory scrutiny than a black-box classifier.
1.6 Why This Research Matters
Table
Stakeholder	Why It Matters
Patients	Prevents harmful false confidence on weak evidence; reduces unnecessary anxiety from false positives
Dermatologists	Provides structured evidence traces for rapid review; flags cases needing human attention
Healthcare Systems	Reduces unnecessary referrals through appropriate abstention; prioritizes clinician time on truly uncertain cases
AI Researchers	Demonstrates a reproducible methodology for evidence-aware multimodal fusion applicable beyond dermatology
Regulators	Offers a template for "trustworthy AI" with explicit uncertainty handling and audit trails
1.7 Expected Contribution
Scientific Contribution: First unified framework combining multi-model ensemble consensus, dynamic diagnosis-adaptive fusion, evidence-based arbitration, evidence management (quality, reliability, conflict, missingness), acquisition-as-consensus-breaker, and systematic multi-agent stress testing for dermatology.
Technical Contribution: Open-source implementation of iterative EM-style refusion with diagnosis-conditioned weight matrices; Devil's Advocate evidence profiler with OOD detection and cross-modal conflict measurement; two-stage verification pipeline preventing LLM hallucination in clinical report generation.
Experimental Contribution: DERMA-STRESS benchmark — the first systematic stress-testing protocol for multi-agent dermatology AI covering 15 conditions including semantic adversarial corruptions (metadata poisoning, text hallucination injection, image replacement).
1.8 Target Research Community
Medical AI / MICCAI / IPMI / MIDL conference audiences
npj Digital Medicine / Communications Medicine / Nature Medicine readers
Dermatology informatics researchers
Trustworthy AI and XAI communities
Clinical decision support system engineers
1.9 Research Scope
In Scope:
Multimodal skin lesion classification on Derm7pt (7-point checklist, 1,011 cases) and PAD-UFES-20 (6-class, 2,298 smartphone images)
Multi-model vision ensemble: DermLIP-PanDerm (VLM), PanDerm encoder, Swin-Tiny, ResNet152
ClinicalBERT-based text analysis with PTIS scoring
Iterative diagnosis-adaptive dynamic fusion (max 3 EM iterations)
Devil's Advocate evidence profiler (Quality, Reliability, Consistency, Missingness, OOD)
4-level consensus hierarchy (Strong → Moderate → Uncertain → Critical Conflict)
Simulated evidence acquisition policy
Two-stage verification (rules + LLM)
RAG over training cases using individual modality embeddings
DERMA-STRESS (15 corruption conditions)
Factorial ablation study with bootstrap confidence intervals
Streamlit research demo
Out of Scope:
Real prospective clinical trials (retrospective benchmark evaluation only)
Real-time longitudinal patient monitoring (simulated follow-up only)
FDA/regulatory submission preparation
Mobile native application development
Integration with hospital EHR/EMR systems
Treatment recommendation (diagnosis-only scope)
Fairness/bias analysis across skin tones (important but separate research track)
1.10 Assumptions
Derm7pt and PAD-UFES-20 datasets remain publicly available and properly licensed for research
HuggingFace model weights for DermLIP-PanDerm, PanDerm, and ClinicalBERT remain accessible
Local GPU server with ≥24GB VRAM is available for ensemble inference
Ollama/Qwen2.5-7B-Instruct runs locally or via accessible API
Patient-generated text in PAD-UFES-20 can be realistically synthesized from structured fields without diagnosis leakage
The 4-level consensus hierarchy provides clinically meaningful abstention behavior (validated via human audit, not clinical trial)
Iterative fusion converges within 3 iterations for the majority of cases
1.11 Constraints
Table
Constraint	Impact on Research
Computational budget	Single-GPU training; ensemble inference requires careful batching
Dataset size	Derm7pt (1,011 cases) is small for deep learning; requires strong regularization and official split adherence
Synthetic text	PAD-UFES-20 patient narratives are generated, not real — generalization to real patient language is unverified
No real patient interaction	Acquisition policy is simulated; cannot validate with actual patients
Model availability	DermFM-Zero weights are private; using DermLIP-PanDerm as substitute VLM
LLM hallucination	Orchestrator LLM constrained to tool-calling; free-text reasoning for diagnosis is prohibited
Timeline	8-week implementation sprint limits depth of hyperparameter tuning
2. RESEARCH BACKGROUND
2.1 Important Concepts
Multimodal Fusion
Multimodal fusion combines information from multiple sensory channels (or data types) into a unified representation. In medical AI, the three canonical fusion strategies are:
Early fusion: Concatenate raw features before learning (simple but loses modality-specific patterns)
Late fusion: Combine predictions from independently trained unimodal models (robust to missing modalities but ignores cross-modal interactions)
Intermediate fusion: Learn joint representations through cross-attention or gating mechanisms (balances expressiveness and robustness)
DERMA-GUARD uses a hybrid approach: intermediate fusion via iterative diagnosis-adaptive weighting, with late-fusion-style consensus arbitration when models disagree.
Evidence Quality, Reliability, Utility, Consistency
These four concepts form the backbone of the Evidence Manager:
Quality (Q): Intrinsic goodness of the raw evidence. For images: sharpness, brightness, resolution. For text: informativeness, specificity. For metadata: completeness.
Reliability (R): Trustworthiness of the model's interpretation of that evidence. Combines calibration (ECE), predictive entropy, and test-time augmentation stability.
Utility (U): Patient-specific counterfactual value of a modality. Computed retrospectively as the change in loss when that modality is removed. Note: At inference, utility is approximated from training statistics; exact U requires ground truth.
Consistency (C): Agreement between modalities. Measured as mean pairwise Jensen-Shannon divergence between per-modality predicted class distributions. Low consistency triggers conflict flags.
Conformal Prediction vs. Consensus Hierarchy
Conformal prediction provides distribution-free coverage guarantees for prediction sets (e.g., "the true diagnosis is in this set of 2 classes with 90% probability"). While statistically rigorous, it is population-level and can produce large, unhelpful sets.
DERMA-GUARD replaces conformal sets with a 4-level consensus hierarchy that makes actionable clinical decisions: diagnose (Level 1), arbitrate (Level 2), acquire more evidence (Level 3), or escalate to human (Level 4). This is more aligned with clinical workflow than probability sets.
Agentic AI in Medicine
Agentic AI refers to systems where multiple specialized AI agents collaborate toward a goal, coordinated by an orchestrator. In DERMA-GUARD:
Vision Specialists = radiologists analyzing images
Scribe = medical transcriptionist extracting structured facts
Librarian = researcher retrieving similar cases and guidelines
Devil's Advocate = quality control officer challenging the consensus
Orchestrator = lead dermatologist synthesizing findings
Iterative EM-Style Refinement
Expectation-Maximization (EM) is an iterative algorithm for finding maximum likelihood estimates. DERMA-GUARD adapts this idea:
E-step: Given current diagnosis, compute diagnosis-adaptive prior weights
M-step: Update fusion weights using evidence quality + prior + conflict penalty
Repeat until convergence or max iterations
2.2 Existing Technologies
Table
Technology	Role in DERMA-GUARD
Swin Transformer	Hierarchical vision backbone for clinical and dermoscopic images
Vision-Language Models (VLMs)	DermLIP-PanDerm for zero-shot and multimodal classification
Foundation Models	PanDerm encoder for strong visual feature extraction
BERT / ClinicalBERT	Text encoding and symptom extraction
FAISS	Efficient similarity search for RAG retrieval
LLMs (Qwen2.5-7B)	Structured extraction, report generation, verification
Hydra / OmegaConf	Composable configuration management
Weights & Biases	Experiment tracking and hyperparameter logging
2.3 Important Terminology
Table
Term	Definition
Dermoscopy	Non-invasive skin imaging using a dermatoscope (magnification + polarized light)
7-Point Checklist	Standardized dermoscopic criteria (pigment network, blue-whitish veil, streaks, etc.)
PTIS	Patient Text Informativeness Score — measures clinical utility of patient narrative
MSE	Minimum Sufficient Evidence — smallest subset of modalities yielding acceptable prediction
NIR	Negative Information Rate — fraction of cases where adding a modality hurts performance
ECE	Expected Calibration Error — measures agreement between predicted confidence and actual accuracy
OOD	Out-of-Distribution — input far from training distribution
TTA	Test-Time Augmentation — averaging predictions over augmented views for stability
JS Divergence	Jensen-Shannon divergence — symmetric measure of similarity between probability distributions
3. LITERATURE REVIEW
3.1 Review Workflow
Databases: PubMed, IEEE Xplore, ACM Digital Library, arXiv (cs.CV, cs.AI, cs.CL), Google Scholar
Date Range: 2021–2026 (primary), 2018–2020 (foundational)
Keywords: multimodal skin lesion classification, dermatology AI, vision-language model dermatology, agentic medical AI, evidence-aware fusion, conformal prediction skin lesions, missing modality medical AI, synthetic clinical notes dermatology
Inclusion Criteria: Peer-reviewed or high-quality preprint; includes multimodal inputs (image + at least one other modality); evaluation on public dermatology dataset; quantitative results reported
Exclusion Criteria: Single-modal only; proprietary dataset without public access; no quantitative evaluation; review/survey papers (used for background only)
3.2 Literature Review Table
Table
Paper	Year	Problem	Method	Dataset	Evaluation	Key Result	Limitation	Relevance
Zhang et al. — SkinM2Former	2025	Tri-modal skin lesion classification	Multi-scale cross-attention transformer fusion	Derm7pt, HAM10000	Accuracy, AUROC, F1	Strong tri-modal fusion performance	No per-modality quality check; equal-weight fusion	Base architecture reproduced as Baseline M
Cockayne et al. — DermFormer	2025	Robust multimodal fusion under corruption	Nested vision transformers with entropy weighting	Derm7pt, ISIC	Accuracy under missing/corrupted modalities	Robust to missing modalities	No per-case utility, sufficiency, or acquisition	Competing baseline for DERMA-STRESS
Watson et al.	2026	Clinical text + dermoscopy for skin cancer	Multimodal fusion of free-text and images	PAD-UFES-20, internal	Accuracy, AUROC	Text improves prediction over image-only	Text quality and diagnostic leakage not evaluated	Motivates text pipeline
Marini et al. — Synthesized Clinical Notes	2026	Generate training text from structured data	LLM-based synthetic note generation	MIMIC-derm subset	BLEU, clinician preference	Enables text+image training when narratives unavailable	Synthetic ≠ real; hallucination risk	Informs synthetic text generation (A6.4)
Marini et al. — Mitigating Hallucinations	2026	Reduce hallucination in synthetic clinical text	Metadata-constrained generation with filtering	MIMIC-derm	Factuality score, clinician review	Reduced invented facts	Generated text still differs from real narratives	Informs validation pipeline
Yan et al. — PanDerm	2025	Large-scale dermatology foundation model	1.5M images, multi-task pretraining	Multiple (HAM, ISIC, PAD, etc.)	Zero-shot, linear probe, fine-tune	State-of-the-art zero-shot on multiple benchmarks	Scale-based, not interpretable or evidence-aware	Landscape reference; encoder used in ensemble
Yan et al. — DermFM-Zero	2026	Zero-shot dermatology VLM	Vision-language pretraining with clinical collaboration	7 benchmarks (HAM, PAD, ISIC, PH2, etc.)	Zero-shot accuracy, retrieval	73.2% avg zero-shot accuracy; SAE concept discovery	Weights currently private	Informs VLM specialist design
Yan et al. — DermLIP	2025	Dermatology vision-language pretraining	Contrastive learning on Derm1M dataset	Derm1M, downstream benchmarks	Zero-shot, retrieval	Strong zero-shot classification and retrieval	Not explicitly evidence-aware	Primary VLM in vision ensemble
Liu et al. — Context-driven Missing-Modality Learning	2026	Handle missing modalities in medical diagnosis	Modality synthesis via context encoder	Chest X-ray, skin datasets	Accuracy under missingness	Effective modality imputation	Focuses on synthesis rather than deciding if acquisition is needed	Missing-modality handling reference
Bouzon et al. — MetaBlock-SE	2025	Missing metadata in skin cancer classification	Attention-based metadata fusion with missingness encoding	PAD-UFES-20	Accuracy, F1	Handles missing metadata gracefully	Broader evidence quality not modeled	Metadata pipeline reference
Fayyad et al.	2024	Trustworthy skin lesion classification	Conformal prediction for uncertainty quantification	HAM10000, ISIC	Coverage, set size	Valid coverage guarantees	Single-modal output; not multimodal evidence-aware	Uncertainty quantification reference
Sonuç et al.	2026	Interpretable multimodal fusion	ViT + metadata with attention visualization	Derm7pt	Accuracy, interpretability	Attention maps show metadata influence	Limited metadata; no external validation	Interpretability reference
Ma et al.	2026	Adaptive class rebalancing + metadata fusion	ViT with spatial-aware metadata attention	PAD-UFES-20	Accuracy, F1, AUC	Improved minority class performance	No explicit conflict or sufficiency modeling	Class imbalance reference
Pacheco & Krohling — MetaBlock	2021	Metadata-image fusion for skin lesions	Attention-based metadata block	Derm7pt, ISIC	Accuracy	First attention-based metadata fusion	Static fusion weights	Foundational metadata fusion
de Lima & Krohling	2022	Transformer + metadata for skin lesions	CNN/Transformer hybrid with metadata	HAM10000	Accuracy	Transformer benefits for small datasets	Mainly classification-focused	Transformer dermatology reference
Wu et al. — Deep Multimodal Learning with Missing Modality	2024	Survey of missing-modality methods	Comprehensive taxonomy and comparison	Multiple medical	Survey	Systematic categorization	Does not solve patient-specific sufficiency	Methodological background
Kim & Kim	2024	Missing modality prediction	Shared embedding + modality prediction	Medical imaging	Accuracy	Predicts missing modalities	Predicted evidence may be uncertain	Missing modality background
Daneshjou et al.	2022	Disparities in dermatology AI	Performance evaluation on diverse skin tones	Diverse dermatology images	Accuracy by skin tone subgroup	Significant performance gaps	Evaluation alone does not solve bias	Fairness awareness
Jabbour et al.	2025	Limits of selective AI prediction	Theoretical + empirical abstention analysis	Multiple medical	Risk-coverage curves	Abstention can increase missed diagnoses	Not specific to multimodal evidence	Selective prediction theory
KGDAgents (Anonymous/Preprint)	2026	Multi-agent clinical diagnosis	8-agent framework with knowledge graph	General clinical	Diagnostic accuracy	Strong multi-agent coordination	Not dermatology-specific; no vision specialists	Agentic architecture reference
SkinGPT-X (Anonymous/Preprint)	2026	Self-evolving multi-agent dermatology	Multi-agent with memory and reflection	Dermatology VQA	Accuracy, clinician preference	Adaptive agent behavior	No explicit evidence management or acquisition	Agentic dermatology reference
DermAgent (Anonymous/Preprint)	2026	Self-reflective agentic dermatology	Single reflective agent for image analysis	Dermoscopy datasets	Accuracy, explanation quality	Interpretable agent reasoning	No multi-model consensus or dynamic fusion	Agentic dermatology reference
Murali & Mazumder — DermaScanAI	2026	Explainable hybrid deep learning	Attention + metadata fusion	Dermoscopy datasets	Accuracy, explainability	Hybrid attention effective	Primarily classification-focused	Explainability reference
3.3 Categorization of Reviewed Work
Table
Category	Papers	What They Achieve
Multimodal Fusion	SkinM2Former, DermFormer, MetaBlock, MetaBlock-SE, Ma et al., Sonuç et al.	Fuse image + metadata (+ text) effectively
Vision-Language Models	PanDerm, DermFM-Zero, DermLIP, Watson et al.	Leverage large-scale pretraining for dermatology
Text & Synthesis	Watson et al., Marini et al. (both 2026)	Integrate or generate clinical text
Uncertainty & Safety	Fayyad et al., Jabbour et al.	Quantify uncertainty, selective prediction
Missing Modality	Liu et al., Kim & Kim, Wu et al. survey, Bouzon et al.	Handle incomplete evidence
Agentic AI	KGDAgents, SkinGPT-X, DermAgent	Multi-agent coordination for medical tasks
Fairness & Bias	Daneshjou et al.	Identify performance disparities
4. RESEARCH GAP
4.1 What Existing Research Solves
Multimodal fusion is mature: SkinM2Former, DermFormer, and MetaBlock-SE demonstrate strong accuracy by combining images, metadata, and (in some cases) text.
Robustness to missing modalities is partially solved: DermFormer and MetaBlock-SE handle missing inputs without crashing.
Uncertainty quantification exists: Fayyad et al. apply conformal prediction to skin lesion classification.
Agentic AI in medicine is emerging: KGDAgents and SkinGPT-X show that multi-agent systems can improve clinical reasoning.
Vision-language pretraining is powerful: PanDerm and DermFM-Zero achieve strong zero-shot performance.
4.2 What Existing Approaches Fail to Solve
Table
Gap	Evidence	Why It Matters
No per-modality evidence quality assessment	SkinM2Former fuses everything equally; DermFormer weights by entropy but not by intrinsic image quality	A blurry photo should not count equally with a sharp dermoscopy
No diagnosis-adaptive fusion	All existing methods use static or globally learned fusion weights	Melanoma diagnosis requires dermoscopy; inflammatory diagnosis requires history — weights should adapt
No cross-modal conflict detection	No existing dermatology system measures whether image and text contradict each other	Contradictory evidence is dangerous if unnoticed
No per-case sufficiency determination	Missing-modality methods impute or mask, but never ask "is what we have enough?"	Clinical safety requires knowing when to stop vs. when to ask for more
No acquisition-as-consensus-breaker	No system uses targeted evidence acquisition to resolve model disagreements	Human panels ask follow-up questions when uncertain — AI should too
No systematic multi-agent stress testing	Robustness studies test corruption, but not in multi-agent consensus settings	Ensemble behavior under stress differs from single-model behavior
No evidence-based arbitration	Existing ensembles use majority vote or average; they do not weight votes by evidence quality	A confident but low-quality prediction should not override a cautious high-quality one
4.3 The Gap Chain
plain
Existing Research (SkinM2Former, DermFormer, PanDerm, Watson et al.)
    ↓
Achieves: Strong multimodal accuracy, robustness to missing inputs, uncertainty quantification
    ↓
Limitation: Treats all evidence as equally trustworthy; uses static fusion; cannot detect conflicts; 
            cannot determine sufficiency; cannot acquire targeted evidence; no multi-agent consensus
    ↓
Research Gap: No unified framework combining multi-model consensus + dynamic diagnosis-adaptive fusion + 
              evidence management (Q,R,C,M) + acquisition + systematic stress testing for dermatology
    ↓
Proposed Approach: DERMA-GUARD — 4-model vision ensemble with Devil's Advocate profiler, iterative 
                   diagnosis-adaptive fusion, 4-level consensus hierarchy, simulated acquisition, 
                   two-stage verification, DERMA-STRESS benchmark
    ↓
Expected Contribution: First evidence-aware multi-agent dermatology system with dynamic fusion and 
                     acquisition; safer behavior under imperfect evidence than any single baseline
5. RESEARCH QUESTIONS
5.1 Main Research Question
RQ-Main: Does a multi-agent consensus framework with dynamic diagnosis-adaptive evidence fusion and explicit evidence management reduce unsafe decisions in multimodal dermatological diagnosis under imperfect evidence, compared to conventional single-model and static-ensemble baselines?
5.2 Supporting Research Questions
Table
ID	Research Question	Why It Matters	Evidence Required	How Answered	Supporting Metric
RQ1	Does multimodal information (image + metadata + text) improve diagnostic accuracy over unimodal baselines?	Validates the multimodal premise	Accuracy on clean test set	Baseline ladder: image-only → +metadata → +text → full	Top-1 accuracy, AUROC, F1
RQ2	Does patient-generated text add information beyond image + metadata?	Justifies text pipeline investment	Accuracy delta with/without text	Ablation: full vs. image+metadata only	Accuracy difference, statistical significance
RQ3	Can the system detect low-quality, unreliable, or conflicting modalities?	Validates Devil's Advocate	Synthetic corruption + conflict injection	Precision/recall of conflict detection, correlation of Q/R with accuracy	Conflict detection P/R, ECE
RQ4	Does diagnosis-adaptive fusion improve over static fusion?	Validates core technical contribution	Accuracy under varying diagnosis distributions	Compare adaptive vs. static weight matrix	Accuracy by diagnosis class, overall macro-F1
RQ5	Can the system detect insufficient evidence and abstain appropriately?	Validates safety layer	Abstention rate vs. accuracy-on-abstained	Risk-coverage curves, selective risk	Abstention rate, accuracy at coverage level
RQ6	Does targeted evidence acquisition resolve uncertainty?	Validates acquisition policy	Recovery rate after simulated acquisition	Simulation loop: hide → acquire → re-evaluate	Recovery rate, uncertainty reduction
RQ7	Does the system degrade more gracefully than baselines under stress?	Validates DERMA-STRESS contribution	Performance drop across 15 conditions	Relative metric drop per condition vs. SkinM2Former, DermFormer	Stress accuracy, ECE under stress
RQ8	Does the consensus hierarchy prevent unsafe predictions better than conformal prediction sets?	Validates replacement of conformal with consensus	Escalation rate vs. coverage	Compare actionable decisions (escalate/acquire) vs. prediction sets	Escalation appropriateness (human audit)
6. RESEARCH OBJECTIVES
6.1 Primary Objective
O1: Develop DERMA-GUARD, a multi-agent dermatological diagnosis system that estimates per-modality evidence quality (Q), reliability (R), consistency (C), and missingness (M); performs iterative diagnosis-adaptive fusion; reaches consensus through a 4-level hierarchy; and abstains or acquires evidence when appropriate — achieving safer behavior under imperfect evidence than conventional multimodal fusion.
Measurement: ≥75% accuracy on DERMA-STRESS average (single-failure conditions), ≤0.10 ECE, ≥80% appropriate abstention rate under stress.
6.2 Secondary Objectives
Table
ID	Objective	Connected RQ	Measurement
O2	Reproduce SkinM2Former as Baseline M and quantify reproduction gap	RQ1	Report delta from published numbers
O3	Implement and validate the Devil's Advocate evidence profiler	RQ3	≥80% conflict detection precision
O4	Implement iterative diagnosis-adaptive fusion and demonstrate convergence	RQ4	Convergence in ≤3 iterations for ≥95% of cases
O5	Implement 4-level consensus hierarchy with calibrated thresholds	RQ5	Human audit: ≥80% of abstentions appropriate
O6	Implement simulated evidence acquisition policy	RQ6	≥70% recovery rate after one acquisition
O7	Develop DERMA-STRESS with 15 conditions including semantic adversarial corruptions	RQ7	Complete benchmark on all model variants
O8	Implement two-stage verification preventing hallucination	RQ8	≤3% unsupported claim rate
7. HYPOTHESES
7.1 Statistical Hypotheses
H1 (Primary): DERMA-GUARD (full system) achieves significantly higher accuracy under single-failure stress conditions than the best single-model baseline (SkinM2Former reproduction).
H0: μ_stress(DERMA-GUARD) ≤ μ_stress(SkinM2Former)
H1: μ_stress(DERMA-GUARD) > μ_stress(SkinM2Former)
Test: Paired t-test on per-case accuracy differences across stress conditions
Significance: α = 0.05
Effect size: Cohen's d > 0.5 (medium)
H2 (Fusion): Diagnosis-adaptive fusion achieves higher macro-F1 than static equal-weight fusion.
H0: macro-F1(adaptive) ≤ macro-F1(static)
H1: macro-F1(adaptive) > macro-F1(static)
Test: McNemar's test on paired predictions
Significance: α = 0.05
H3 (Safety): The 4-level consensus hierarchy appropriately abstains on cases where the single-model baseline makes errors.
H0: Abstention rate on error cases ≤ 50%
H1: Abstention rate on error cases > 50%
Test: Binomial test
Significance: α = 0.05
7.2 Variables
Table
Type	Variable	Description
Independent	Fusion strategy	{static, diagnosis-adaptive, iterative}
Independent	Evidence management	{none, Q only, Q+R, Q+R+C, Q+R+C+M+OOD}
Independent	Corruption condition	{clean, blur, noise, missing_clinical, missing_dermoscopy, missing_metadata, missing_text, brightness, contrast, compression, occlusion, incorrect_metadata, vague_text, contradictory_text, semantic_corruption, multi_failure}
Dependent	Diagnostic accuracy	Top-1 accuracy, AUROC, F1
Dependent	Calibration	ECE, Brier score
Dependent	Safety	Abstention rate, escalation rate, recovery rate
Dependent	Efficiency	Inference time, acquisition steps
Control	Dataset split	Official Derm7pt split; fixed patient-level PAD-UFES-20 split
Control	Random seed	3–5 fixed seeds (42, 123, 456, 789, 2024)
Control	Backbone initialization	ImageNet-pretrained weights
Confounding	Class imbalance	Mitigated via class weights and focal loss
Confounding	Synthetic text quality	Mitigated via PTIS filtering and leakage checks
8. PROPOSED RESEARCH METHODOLOGY
8.1 Methodology Type
This is a computational, experimental, quantitative research project. All experiments are conducted on public benchmark datasets using controlled corruption protocols. No human subjects are involved in the primary experiments (synthetic text generation uses structured fields, not real narratives; clinician audit of abstention is a secondary validation step).
8.2 Methodology Pipeline
plain
Research Problem Definition
    ↓
Literature Review & Gap Analysis
    ↓
Research Questions & Hypotheses
    ↓
Dataset Audit & Preparation
    ↓
Baseline Ladder Implementation
    ↓
Core System Development (Agents + Fusion + Consensus)
    ↓
Verification & Safety Layer
    ↓
DERMA-STRESS Benchmark Design
    ↓
Controlled Experiments (Clean + Stress)
    ↓
Ablation Study (Factorial Design)
    ↓
Statistical Analysis (Bootstrap CIs, Significance Tests)
    ↓
Error Analysis & Failure Investigation
    ↓
Results Interpretation & Discussion
    ↓
Reproducibility Package
    ↓
Paper Drafting
8.3 Stage-by-Stage Methodology
Stage 1: Dataset Audit & Preparation
Why: Prevent data leakage, ensure reproducibility, understand data quality.
Input: Raw Derm7pt and PAD-UFES-20 downloads.
Output: Clean dataset with frozen splits, audit report.
Quality Checks: SHA-256 hashes, perceptual hash collision detection, class distribution verification, missingness analysis.
Stage 2: Baseline Ladder
Why: Establish performance floor and ceiling; validate that multimodal fusion is beneficial.
Input: Clean training/validation/test splits.
Output: Trained baseline models with logged metrics.
Models: Majority class, metadata-only, clinical-only, dermoscopy-only, concatenation fusion, image+text.
Stage 3: SkinM2Former Reproduction
Why: Provide a strong, published baseline for comparison.
Input: Derm7pt official split.
Output: Reproduced SkinM2Former with reported delta from paper.
Quality Checks: Compare published numbers vs. reproduction; document any gaps.
Stage 4: Vision Specialist Team
Why: Build the multi-model ensemble that provides diverse predictions for consensus.
Input: Pre-trained model weights.
Output: 4 models producing embeddings + predictions + uncertainty.
Models: DermLIP-PanDerm, PanDerm encoder, Swin-Tiny (fine-tuned), ResNet152 (fine-tuned).
Stage 5: Text & Metadata Pipeline
Why: Extract structured information from unstructured patient input.
Input: Raw text + metadata.
Output: ClinicalBERT embeddings, PTIS scores, structured symptom dicts, metadata embeddings.
Stage 6: Devil's Advocate (Evidence Profiler)
Why: Safety layer — detect bad evidence before it influences the diagnosis.
Input: All evidence + all model predictions.
Output: Q, R, C, M scores, OOD flag, conflict flag.
Training: Reliability MLP trained jointly; OOD detector calibrated on validation.
Stage 7: Dynamic Fusion
Why: Core scientific contribution — adapt fusion to both evidence quality and suspected diagnosis.
Input: Embeddings, Q, R, C, M.
Output: Fused prediction, final weights, convergence log.
Algorithm: Iterative EM-style refusion (max 3 iterations).
Stage 8: Consensus & Acquisition
Why: Make actionable decisions based on fused output.
Input: Fused prediction + evidence profile.
Output: Consensus level (1–4), acquisition target (if Level 3), escalation (if Level 4).
Stage 9: Verification
Why: Prevent hallucination in LLM-generated reports.
Input: Report draft + structured evidence.
Output: Pass/fail + reason; regenerated conservative report if fail.
Stage 10: DERMA-STRESS
Why: Prove robustness systematically.
Input: Test set + corruption functions.
Output: Per-condition metrics for all model variants.
Stage 11: Evaluation & Statistics
Why: Draw valid, reproducible conclusions.
Input: All experimental results.
Output: Tables with bootstrap 95% CIs, significance tests, ablation analysis.
9. COMPLETE RESEARCH WORKFLOW
9.1 Workflow Diagram (Text-Based)
plain
┌─────────────────────────────────────────────────────────────────────────┐
│                         RESEARCH WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PHASE 1: FOUNDATION (Week 1)                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │ Literature  │───→│ Dataset     │───→│ Baseline    │                 │
│  │ Review      │    │ Audit       │    │ Ladder      │                 │
│  └─────────────┘    └─────────────┘    └─────────────┘                 │
│         │                  │                  │                         │
│         ↓                  ↓                  ↓                         │
│  ┌─────────────────────────────────────────────────────┐               │
│  │  DELIVERABLE: Clean data + 6 baselines trained      │               │
│  └─────────────────────────────────────────────────────┘               │
│                                                                          │
│  PHASE 2: CORE SYSTEM (Weeks 2–4)                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │
│  │ Vision Team │───→│ Evidence    │───→│ Dynamic     │               │
│  │ (4 models)  │    │ Profiler    │    │ Fusion      │               │
│  └─────────────┘    └─────────────┘    └─────────────┘               │
│         │                  │                  │                         │
│         ↓                  ↓                  ↓                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │
│  │ Text/Metadata│    │ Consensus   │    │ Verification│               │
│  │ Pipeline    │───→│ Hierarchy   │───→│ (2-stage)   │               │
│  └─────────────┘    └─────────────┘    └─────────────┘               │
│         │                  │                  │                         │
│         ↓                  ↓                  ↓                         │
│  ┌─────────────────────────────────────────────────────┐               │
│  │  DELIVERABLE: Full DERMA-GUARD pipeline working    │               │
│  └─────────────────────────────────────────────────────┘               │
│                                                                          │
│  PHASE 3: EVALUATION (Weeks 5–6)                                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │
│  │ DERMA-STRESS│───→│ Ablation    │───→│ Statistical │               │
│  │ (15 conds)  │    │ Study       │    │ Analysis    │               │
│  └─────────────┘    └─────────────┘    └─────────────┘               │
│         │                  │                  │                         │
│         ↓                  ↓                  ↓                         │
│  ┌─────────────────────────────────────────────────────┐               │
│  │  DELIVERABLE: Complete benchmark results + CIs      │               │
│  └─────────────────────────────────────────────────────┘               │
│                                                                          │
│  PHASE 4: DELIVERY (Weeks 7–8)                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │
│  │ Error       │───→│ Demo        │───→│ Paper       │               │
│  │ Analysis    │    │ (Streamlit) │    │ Draft       │               │
│  └─────────────┘    └─────────────┘    └─────────────┘               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
9.2 Phase Definitions
Table
Phase	Duration	Why	Prerequisites	Output	Definition of Done
Foundation	Week 1	Everything depends on clean data and baselines	None	Audit report, 6 trained baselines	All baselines achieve expected accuracy ranges
Core System	Weeks 2–4	Build the novel components	Foundation complete	Working DERMA-GUARD pipeline	End-to-end case processing succeeds on 10 test cases
Evaluation	Weeks 5–6	Generate evidence for claims	Core system complete	Benchmark results	All 15 stress conditions tested on 4 model variants
Delivery	Weeks 7–8	Communicate and demonstrate	Evaluation complete	Demo + paper draft	Demo runs without manual intervention; paper draft complete
10. RESEARCH ARCHITECTURE
10.1 Architecture Diagram (Text-Based)
plain
┌─────────────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Clinical     │  │ Dermoscopy   │  │ Patient      │  │ Structured   │ │
│  │ Image        │  │ Image        │  │ Text         │  │ Metadata     │ │
│  │ [3×224×224]  │  │ [3×224×224]  │  │ [string]     │  │ [dict]       │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                 │                 │         │
│         └─────────────────┴─────────────────┴─────────────────┘         │
│                                   │                                      │
│                                   ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    AGENTIC ANALYSIS LAYER                            ││
│  │                                                                      ││
│  │  ┌─────────────────────────────────────────────────────────────────┐ ││
│  │  │              AGENT 1: VISION SPECIALIST TEAM                    │ ││
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐ │ ││
│  │  │  │DermLIP-     │ │PanDerm      │ │Swin-Tiny    │ │ResNet152 │ │ ││
│  │  │  │PanDerm      │ │Encoder      │ │(Clinical+   │ │(Pure     │ │ ││
│  │  │  │(VLM)        │ │(Foundation)│ │ Dermoscopy)│ │ Vision)  │ │ ││
│  │  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └─────┬────┘ │ ││
│  │  │         └─────────────────┴─────────────────┴────────────┘      │ ││
│  │  │                           │                                      │ ││
│  │  │         Output: predictions + embeddings + quality per image      │ ││
│  │  └─────────────────────────────────────────────────────────────────┘ ││
│  │                              │                                       ││
│  │  ┌─────────────────────────────────────────────────────────────────┐ ││
│  │  │              AGENT 2: THE SCRIBE                               │ ││
│  │  │  ClinicalBERT → Symptom Extraction → PTIS → Text Embedding    │ ││
│  │  │  Output: structured symptoms + ptis + embedding                 │ ││
│  │  └─────────────────────────────────────────────────────────────────┘ ││
│  │                              │                                       ││
│  │  ┌─────────────────────────────────────────────────────────────────┐ ││
│  │  │              AGENT 3: THE LIBRARIAN                            │ ││
│  │  │  FAISS Index → Similar Case Retrieval → Guideline Context      │ ││
│  │  │  Output: top-k similar cases + agreement rate                   │ ││
│  │  └─────────────────────────────────────────────────────────────────┘ ││
│  │                              │                                       ││
│  │  ┌─────────────────────────────────────────────────────────────────┐ ││
│  │  │         AGENT 4: DEVIL'S ADVOCATE (EVIDENCE PROFILER)          │ ││
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │ ││
│  │  │  │ Quality  │ │Reliability│ │Consistency│ │Missingness│        │ ││
│  │  │  │ (Q)      │ │ (R)      │ │ (C)      │ │ (M)      │        │ ││
│  │  │  │ OOD Score│ │ ECE +    │ │ JS Div   │ │ Binary   │        │ ││
│  │  │  │ + Image  │ │ Entropy  │ │ between  │ │ Flags    │        │ ││
│  │  │  │ Quality  │ │ + TTA    │ │ models   │ │ per mod  │        │ ││
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │ ││
│  │  │  Output: EvidenceProfile {Q, R, C, M, ood_score, conflict}    │ ││
│  │  └─────────────────────────────────────────────────────────────────┘ ││
│  │                                                                     ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                   │                                      │
│                                   ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    FUSION & DECISION LAYER                           ││
│  │                                                                      ││
│  │  ┌─────────────────────────────────────────────────────────────────┐ ││
│  │  │              ITERATIVE DIAGNOSIS-ADAPTIVE FUSION               │ ││
│  │  │                                                                  ││
│  │  │  Iteration 0: w = softmax(Q × R)  [no diagnosis prior]        │ ││
│  │  │       ↓                                                          ││
│  │  │  Iteration 1: w = softmax(α·f(Q,R,U,C) + β·π(diag⁽⁰⁾))      │ ││
│  │  │       ↓                                                          ││
│  │  │  Iteration 2: w = softmax(... + γ·conflict_penalty)           │ ││
│  │  │       ↓                                                          ││
│  │  │  Convergence check → Final weights + Fused prediction            ││
│  │  └─────────────────────────────────────────────────────────────────┘ ││
│  │                              │                                       ││
│  │  ┌─────────────────────────────────────────────────────────────────┐ ││
│  │  │              4-LEVEL CONSENSUS HIERARCHY                       │ ││
│  │  │                                                                  ││
│  │  │  Level 1 (Strong): ≥3 models agree + conf ≥ 0.8 + no conflict  │ ││
│  │  │       → ACCEPT diagnosis                                       │ ││
│  │  │  Level 2 (Moderate): 2 models agree + conf ∈ [0.5, 0.8)        │ ││
│  │  │       → ARBITRATE (weight by Q × R)                            │ ││
│  │  │  Level 3 (Uncertain): All disagree OR conf < 0.5 OR quality low││
│  │  │       → ACQUIRE evidence OR ABSTAIN                            │ ││
│  │  │  Level 4 (Critical Conflict): C < 0.3 AND no consensus       │ ││
│  │  │       → ESCALATE to human review                               │ ││
│  │  └─────────────────────────────────────────────────────────────────┘ ││
│  │                                                                     ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                   │                                      │
│                                   ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    SAFETY & OUTPUT LAYER                             ││
│  │                                                                      ││
│  │  ┌─────────────────────────────────────────────────────────────────┐ ││
│  │  │         STAGE 1 VERIFICATION (Pre-Orchestrator)                │ ││
│  │  │  • OOD check → ESCALATE if Mahalanobis > threshold            │ ││
│  │  │  • Missingness check → ACQUIRE if critical missing            │ ││
│  │  │  • Conflict check → ACQUIRE if C < 0.3                        │ ││
│  │  │  • Quality check → SUPPRESS modality if Q < 0.2               │ ││
│  │  └─────────────────────────────────────────────────────────────────┘ ││
│  │                              │                                       ││
│  │  ┌─────────────────────────────────────────────────────────────────┐ ││
│  │  │              ORCHESTRATOR (Qwen2.5-7B Tool-Calling)            │ ││
│  │  │  Synthesizes agent reports into structured diagnosis + report   │ ││
│  │  └─────────────────────────────────────────────────────────────────┘ ││
│  │                              │                                       ││
│  │  ┌─────────────────────────────────────────────────────────────────┐ ││
│  │  │         STAGE 2 VERIFICATION (Post-Orchestrator)                 │ ││
│  │  │  • Diagnosis in model top-3?                                   │ ││
│  │  │  • Confidence matches consensus level?                        │ ││
│  │  │  • Every claim traceable to evidence JSON?                    │ ││
│  │  │  • No unsupported diagnosis terms?                            │ ││
│  │  │  FAIL → Regenerate conservative report → Re-verify              │ ││
│  │  └─────────────────────────────────────────────────────────────────┘ ││
│  │                                                                     ││
│  │  Output: {diagnosis, confidence, consensus_level, evidence_trace, ││
│  │           report, acquisition_target, escalation_reason}          ││
│  │                                                                     ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                   │                                      │
│                                   ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    DERMA-STRESS BENCHMARK                            ││
│  │                                                                      ││
│  │  Availability:  missing_clinical, missing_dermoscopy, missing_meta, ││
│  │                missing_text                                         ││
│  │  Technical:      blur, noise, brightness, contrast, compression,   ││
│  │                occlusion                                            ││
│  │  Semantic:       contradictory_text, vague_text, incorrect_metadata, ││
│  │                semantic_corruption, multi_failure                   ││
│  │                                                                      ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
10.2 Component Details
Table
Component	Input	Output	Technology
DermLIP-PanDerm	Clinical/dermoscopy image + text prompt	Zero-shot logits + embedding	HuggingFace Transformers
PanDerm Encoder	Clinical/dermoscopy image	Visual features (768-d)	Custom PyTorch (from GitHub)
Swin-Tiny	Clinical/dermoscopy image	Class logits + embedding (768-d)	timm
ResNet152	Clinical/dermoscopy image	Class logits + embedding (2048-d)	timm
ClinicalBERT	Patient text	Embedding (768-d) + symptom dict	HuggingFace Transformers
PTIS v1	Raw text	Score [0,1]	Heuristic (word count, keywords, temporality)
PTIS v2	Raw text	Score [0,1]	Regression on human ratings
Metadata MLP	Structured metadata	Embedding (64-d)	PyTorch
OOD Detector	Fused embedding	Mahalanobis distance	scikit-learn
Reliability MLP	Q, entropy, stability, agreement	R score [0,1]	PyTorch
Fusion Network	Embeddings, Q, R, C, M	Weights, fused prediction	PyTorch
Consensus	Fused prediction, evidence profile	Level (1-4), action	Rule-based
Acquisition Policy	Current evidence, uncertainty	Target modality/field	Gradient-boosted regressor
Orchestrator LLM	Agent reports, evidence profile	Structured diagnosis	Ollama/Qwen2.5-7B
Verification Rules	Report draft, evidence JSON	Pass/fail	Python
Verification LLM	Report draft, evidence JSON	Pass/fail + reason	Ollama/Qwen2.5-7B
RAG Index	Individual embeddings	Similar cases	FAISS
Event Store	All agent actions	Immutable trace	SQLite/Postgres
11. EXPERIMENTAL DESIGN
11.1 Experiment Matrix
Table
Exp ID	Purpose	Dataset	Baseline	Proposed	Variables	Metrics	Expected Evidence
E1	Baseline ladder	Derm7pt	Majority, metadata-only, clinical-only, dermoscopy-only, concat	—	Modality availability	Accuracy, F1, AUROC	Multimodal improves over unimodal
E2	SkinM2Former reproduction	Derm7pt	Paper numbers	Our reproduction	Split, preprocessing	Accuracy, F1	Reproduction gap documented
E3	Text contribution	PAD-UFES-20	Image+metadata	Image+metadata+text	Text availability	Accuracy delta	Text adds information
E4	Adaptive fusion vs. static	Derm7pt	Equal-weight fusion	Diagnosis-adaptive fusion	Fusion strategy	Macro-F1 by class	Adaptive improves on class-imbalanced diagnoses
E5	Evidence profiler accuracy	Derm7pt (synthetic conflicts)	No conflict detection	Devil's Advocate	Conflict injection	Precision, Recall, F1	≥80% precision on conflict detection
E6	Consensus hierarchy	Derm7pt	Single-model threshold	4-level hierarchy	Consensus level	Abstention rate, selective risk	Appropriate abstention on uncertain cases
E7	Acquisition effectiveness	Derm7pt	Random acquisition	Policy-based acquisition	Acquisition strategy	Recovery rate, steps to resolve	≥70% recovery in 1 step
E8	DERMA-STRESS clean	Derm7pt + PAD-UFES-20	SkinM2Former, DermFormer	DERMA-GUARD	—	Accuracy, ECE, F1	Competitive clean accuracy
E9	DERMA-STRESS single failure	Derm7pt + PAD-UFES-20	SkinM2Former, DermFormer	DERMA-GUARD	Corruption type	Accuracy drop, ECE, abstention	Graceful degradation
E10	DERMA-STRESS semantic	Derm7pt + PAD-UFES-20	—	DERMA-GUARD	Semantic corruption	Accuracy, conflict detection	Detects adversarial semantic shifts
E11	DERMA-STRESS multi-failure	Derm7pt + PAD-UFES-20	—	DERMA-GUARD	2+ combined corruptions	Accuracy, escalation rate	Escalates appropriately
E12	Ablation: components	Derm7pt	Full system	-Q, -R, -C, -fusion, -consensus	Component removed	Accuracy (stress)	Each component contributes
E13	Ablation: factorial	Derm7pt	—	All 2^4 combinations of Q,R,C,M	Component combination	Accuracy, ECE	Interaction effects identified
E14	Statistical validation	All above	—	Bootstrap CIs	Random seed (3–5 seeds)	Mean ± std, 95% CI	Results are statistically robust
11.2 Experiment Details
E1: Baseline Ladder
Objective: Establish that multimodal fusion improves over unimodal baselines.
Dataset: Derm7pt official split.
Baselines: Majority class, metadata-only MLP, clinical-image-only Swin-Tiny, dermoscopy-only Swin-Tiny, concatenation fusion (clinical + dermoscopy + metadata → MLP).
Metrics: Top-1 accuracy, macro-F1, AUROC.
Runs: 3 random seeds.
Expected: Concatenation fusion > any unimodal; justifies multimodal approach.
E2: SkinM2Former Reproduction
Objective: Reproduce published tri-modal cross-attention transformer.
Dataset: Derm7pt official split.
Method: Implement exactly as described (Zhang et al., WACV 2025): two Swin-Tiny branches + metadata MLP, cross-attention fusion, 224×224 inputs, flips + shifts + mixup augmentation.
Metrics: Same as paper (accuracy, F1, AUROC per class).
Expected: Report delta between reproduction and paper; do not hide gaps.
E3: Text Contribution (PAD-UFES-20)
Objective: Validate that synthetic patient text adds predictive value.
Dataset: PAD-UFES-20 with synthetic text.
Variants: Image+metadata only vs. image+metadata+text.
Metrics: Accuracy difference, McNemar's test.
Expected: Statistically significant improvement (p < 0.05).
E4: Adaptive Fusion vs. Static
Objective: Prove diagnosis-adaptive fusion outperforms static equal-weight fusion.
Dataset: Derm7pt.
Variants: Equal-weight softmax vs. diagnosis-adaptive iterative.
Metrics: Macro-F1 (to catch minority-class improvements), per-class accuracy.
Expected: Adaptive fusion improves macro-F1 by ≥3 points.
E5: Evidence Profiler Accuracy
Objective: Validate conflict detection.
Dataset: Derm7pt validation set with synthetically injected conflicts.
Conflicts: Image says benign, text says growing/bleeding; metadata contradicts image.
Metrics: Precision, recall, F1 of conflict flag.
Expected: ≥80% precision, ≥70% recall.
E6: Consensus Hierarchy
Objective: Validate that the 4-level hierarchy makes appropriate decisions.
Dataset: Derm7pt test set.
Comparison: Single-model confidence threshold vs. 4-level hierarchy.
Metrics: Abstention rate, accuracy on non-abstained cases, selective risk.
Expected: Hierarchy abstains more appropriately (human audit of 50 cases).
E7: Acquisition Effectiveness
Objective: Validate that acquisition resolves uncertainty.
Dataset: Derm7pt validation.
Simulation: Hide one modality → run policy → if it requests hidden modality, reveal and re-run.
Metrics: Recovery rate (% that reach consensus after acquisition), average steps.
Expected: ≥70% recovery in 1 step.
E8–E11: DERMA-STRESS
Objective: Systematic robustness evaluation.
Dataset: Both datasets, test split only.
Compared Models: Image-only, SkinM2Former, DermFormer (numbers or reproduction), DERMA-GUARD (4 variants: A=single, B=ensemble, C=+evidence, D=full).
Conditions: 15 corruption types (see Section 18).
Metrics: Accuracy, ECE, Brier, abstention rate, escalation rate, recovery rate.
Expected: Model D shows smallest accuracy drop and best calibration under stress.
E12–E13: Ablation Studies
Objective: Isolate contribution of each component.
Design: Linear ablation chain (image-only → +metadata → +text → +SkinM2Former fusion → +Q → +R → +U → +C → +Sufficiency → +Uncertainty → +Acquisition → +Verification) AND factorial ablation of Evidence Manager components (none, Q only, R only, C only, Q+R, Q+R+C, Q+R+C+M, full).
Metrics: Accuracy on clean and stress, ECE.
Expected: Each component provides incremental value; interaction effects visible in factorial design.
E14: Statistical Validation
Objective: Ensure results are reproducible and statistically valid.
Methods: 3–5 random seeds per configuration; bootstrap 1,000 resamples for 95% CIs; paired t-test or McNemar's test for significance; report effect sizes (Cohen's d).
Expected: All primary claims supported by statistical evidence.
12. DATASET STRATEGY
12.1 Derm7pt (Primary Research Dataset)
Table
Attribute	Detail
Source	Kawahara et al., 2018; publicly available
Size	1,011 paired cases
Modalities	Clinical photo (JPEG/PNG), dermoscopic image, metadata, 7-point checklist concepts, diagnosis label
Classes	Melanoma, melanocytic nevus, basal cell carcinoma, actinic keratosis, benign keratosis, dermatofibroma, vascular lesion
Official Split	413 train / 203 validation / 395 test (published index files)
License	Research use
Preprocessing:
Training: RandomResizedCrop(224), HorizontalFlip, rotation ±15°, ColorJitter, Normalize(ImageNet mean/std)
Validation/Test: Resize(256), CenterCrop(224), Normalize(ImageNet mean/std)
Data Quality Checks:
SHA-256 hash for every image
Perceptual hash (phash) for duplicate detection
Flag hash collisions within/across datasets
Missingness analysis per field
12.2 PAD-UFES-20 (Smartphone / Patient-Language Track)
Table
Attribute	Detail
Source	Pacheco et al., 2020; publicly available
Size	2,298 smartphone images from 1,373 patients, 1,641 lesions
Metadata	~21 clinical attributes (age, sex, location, smoking, etc.)
Classes	BCC, SCC, ACK, SEK, NEV, MEL (6 classes)
Split	Patient-level 70/15/15 (group by patient_id, fixed seed=42)
License	CC BY-NC 4.0
Preprocessing: Same as Derm7pt (ImageNet normalization).
Synthetic Text Generation:
Fields used: age_bucket, body_location, grew, itch, bleed, changed, elevation
Diagnosis NEVER included in prompt
LLM: Qwen2.5-7B with temperature=0.7
Validation: Regex diagnosis-term scan, extracted-field diff, embedding diversity check (cosine < 0.97)
12.3 Preventing Data Leakage
Table
Risk	Mitigation
Image duplication across splits	Perceptual hash check; exclude collisions
Patient overlap in PAD-UFES-20	Strict patient-level split; never image-level
Synthetic text memorization	Diagnosis excluded from prompt; leakage regex
Pretraining overlap	DermLIP-PanDerm pretrained on Derm1M; no Derm7pt/PAD overlap assumed (authors report deduplication)
Test set contamination	Test set NEVER used for hyperparameter tuning, threshold calibration, or model selection
12.4 Class Imbalance Handling
Compute class weights: weight_c = N / (n_classes * n_c)
Apply to cross-entropy loss
Use Focal Loss (γ=2.0) for PAD-UFES-20 (heavily imbalanced toward NEV/SEK)
Report per-class metrics (not just macro/micro) to catch minority-class collapse
12.5 Train / Validation / Test Splits
Derm7pt: Use official published splits exactly. Do not regenerate.
PAD-UFES-20:
plain
Group by patient_id
Shuffle groups with seed=42
Assign whole groups:
  - First 70% cumulative → train
  - Next 15% → validation  
  - Final 15% → test
Save split files to data/splits/ and commit to Git
13. DATA PROCESSING PIPELINE
13.1 Pipeline Diagram (Text-Based)
plain
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATA PROCESSING PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  RAW DATA SOURCES                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐   │
│  │ Derm7pt     │  │ PAD-UFES-20 │  │ Derm1M      │  │ Medical      │   │
│  │ Images +    │  │ Images +    │  │ (VLM        │  │ Guidelines   │   │
│  │ Metadata    │  │ Metadata    │  │ pretraining)│  │ (RAG corpus) │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘   │
│         │                │                │                │            │
│         └────────────────┴────────────────┘                │            │
│                          │                                 │            │
│                          ▼                                 │            │
│  ┌─────────────────────────────────────────────────────┐  │            │
│  │              DATA AUDIT & VALIDATION                 │  │            │
│  │  • SHA-256 hashes                                   │  │            │
│  │  • Perceptual hash (phash) collision detection     │  │            │
│  │  • Cross-dataset leakage check                      │  │            │
│  │  • Class distribution analysis                      │  │            │
│  │  • Missingness pattern analysis                       │  │            │
│  └────────────────────────┬────────────────────────────┘  │            │
│                           │                                │            │
│                           ▼                                │            │
│  ┌─────────────────────────────────────────────────────┐   │            │
│  │              DATA CLEANING                          │   │            │
│  │  • Remove duplicates (within and across datasets)   │   │            │
│  │  • Remove corrupted images (cannot load)            │   │            │
│  │  • Standardize metadata schema                    │   │            │
│  │  • Handle missing values (flag, do not impute)     │   │            │
│  └────────────────────────┬────────────────────────────┘   │            │
│                           │                                │            │
│                           ▼                                │            │
│  ┌─────────────────────────────────────────────────────┐   │            │
│  │              SYNTHETIC TEXT GENERATION               │   │            │
│  │  (PAD-UFES-20 only)                                  │   │            │
│  │  • Prompt LLM with structured fields (no diagnosis) │   │            │
│  │  • Validate: no diagnosis terms, no invented facts   │   │            │
│  │  • Diversity check: embedding cosine < 0.97        │   │            │
│  │  • Store: {case_id, text, source_fields, flags}      │   │            │
│  └────────────────────────┬────────────────────────────┘   │            │
│                           │                                │            │
│                           ▼                                ▼            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              PREPROCESSING & TRANSFORMATION                      │   │
│  │                                                                  │   │
│  │  IMAGES:                                                         │   │
│  │    Train: RandomResizedCrop(224) + HFlip + Rotate(±15°) +       │   │
│  │           ColorJitter + Normalize(ImageNet)                      │   │
│  │    Val/Test: Resize(256) + CenterCrop(224) + Normalize(ImageNet)│   │
│  │                                                                  │   │
│  │  TEXT:                                                           │   │
│  │    • Tokenize (ClinicalBERT)                                     │   │
│  │    • Mean-pool last hidden states → 768-d embedding              │   │
│  │    • Compute PTIS v1 (heuristic)                                 │   │
│  │                                                                  │   │
│  │  METADATA:                                                       │   │
│  │    • Categorical → learned embeddings (dim = min(50, (n+1)//2))  │   │
│  │    • Continuous → z-score normalize (train stats only)         │   │
│  │    • Missing → binary indicator + zero imputation                │   │
│  │    • Concatenate → MLP (128→64) → 64-d embedding                │   │
│  │                                                                  │   │
│  └────────────────────────┬─────────────────────────────────────────┘   │
│                           │                                            │
│                           ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              SPLITTING (FROZEN — NEVER REGENERATE)              │   │
│  │                                                                  │   │
│  │  Derm7pt: Load official split files (train/val/test)           │   │
│  │  PAD-UFES-20: Patient-level split (seed=42) → JSON files         │   │
│  │                                                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │   │
│  │  │   TRAIN     │  │ VALIDATION  │  │    TEST     │               │   │
│  │  │   413       │  │    203      │  │    395      │  (Derm7pt)   │   │
│  │  │   70%       │  │    15%      │  │    15%      │  (PAD-UFES)  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │   │
│  │                                                                  │   │
│  │  Three-way split for conformal calibration (from val):           │   │
│  │    Validation: 150 (hyperparameters, early stopping)            │   │
│  │    Calibration: 53 (conformal quantile — retained for legacy)    │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
13.2 Data Versioning
Raw data: Git-LFS or external storage (not in Git)
Split files: Committed to data/splits/
System is currently busy. Please try again later.

 Here is **Part 2** — Sections 14 through 33, continuing directly from where Part 1 ended.

---

## 14. PROPOSED METHOD / ALGORITHM

### 14.1 Core Concept

DERMA-GUARD treats dermatological diagnosis not as a single classification task but as a **multi-agent evidence-management process**. The key insight is that different diagnoses depend on different evidence sources with different reliabilities. Melanoma diagnosis relies heavily on dermoscopic structural patterns (ABCDE criteria, 7-point checklist); inflammatory conditions depend more on patient history and symptom progression; benign lesions may be identifiable from clinical appearance alone.

Rather than learning a single static fusion function, DERMA-GUARD learns a **diagnosis-conditioned weight matrix** that modulates per-modality importance based on what the system currently believes the diagnosis to be. Because the diagnosis is initially unknown, this creates a chicken-and-egg problem resolved through iterative EM-style refinement.

### 14.2 Mathematical Formulation

#### Notation

| Symbol | Meaning |
|--------|---------|
| $x$ | A single patient case |
| $M = \{clinical, dermoscopy, text, metadata\}$ | Set of modalities |
| $z_m \in \mathbb{R}^{d_m}$ | Embedding from modality $m$ |
| $Q_m(x) \in [0,1]$ | Quality score for modality $m$ |
| $R_m(x) \in [0,1]$ | Reliability score for modality $m$ |
| $C(x) \in [0,1]$ | Cross-modal consistency |
| $\mathbf{w} \in \mathbb{R}^{|M|}$ | Fusion weights |
| $\pi(d) \in \mathbb{R}^{|M|}$ | Diagnosis-adaptive prior for diagnosis $d$ |
| $\hat{y}$ | Predicted diagnosis |
| $K$ | Number of diagnostic classes |

#### Iterative Diagnosis-Adaptive Fusion

**Initialization (Iteration 0):**
$$\mathbf{w}^{(0)} = \text{softmax}\left( \alpha \cdot \mathbf{Q} \odot \mathbf{R} \right)$$

Where $\odot$ is element-wise multiplication and $\alpha$ is a learned temperature.

**E-Step (Iteration $k \rightarrow k+1$):**
Given current prediction $\hat{y}^{(k)} = \arg\max(\text{softmax}(f(\mathbf{z}_{\text{fused}}^{(k)})))$, retrieve diagnosis-adaptive prior:
$$\pi_m(\hat{y}^{(k)}) = \mathbf{W}_{\text{prior}}[\hat{y}^{(k)}, m]$$

Where $\mathbf{W}_{\text{prior}} \in \mathbb{R}^{K \times |M|}$ is learned on the validation set.

**M-Step (Weight Update):**
$$\mathbf{w}^{(k+1)} = \text{softmax}\left( \alpha \cdot f(\mathbf{Q}, \mathbf{R}, \mathbf{U}, C) + \beta \cdot \pi(\hat{y}^{(k)}) + \gamma \cdot \log(\mathbf{p}_{\text{conflict}}) \right)$$

Where:
- $f$ is a small MLP (4 inputs $\rightarrow$ 1 output per modality)
- $\mathbf{p}_{\text{conflict}}$ reduces weights of modalities that disagree with the emerging consensus
- $\beta, \gamma$ are learned coefficients

**Fusion:**
$$\mathbf{z}_{\text{fused}}^{(k+1)} = \sum_{m \in \text{available}} w_m^{(k+1)} \cdot z_m$$

**Convergence Check:**
$$\text{Converged if } \hat{y}^{(k+1)} = \hat{y}^{(k)} \text{ and } \max_m |w_m^{(k+1)} - w_m^{(k)}| < \tau$$

Where $\tau = 0.05$ (hyperparameter).

**Final Output:**
$$\hat{y} = \hat{y}^{(K_{\text{final}})}, \quad \mathbf{w}^* = \mathbf{w}^{(K_{\text{final}})}$$

#### Missing Modality Handling

For missing modality $m$, set mask $\mu_m = 0$:

$$\tilde{w}_m = w_m \cdot \mu_m$$
$$\mathbf{w}_{\text{normalized}} = \frac{\tilde{\mathbf{w}}}{\sum_j \tilde{w}_j}$$

If $\sum_j \mu_j = 0$ (all modalities missing), raise `INSUFFICIENT_EVIDENCE` before fusion.

#### Devil's Advocate Computations

**Quality (Q):**
$$Q_{\text{image}} = \text{MLP}([\text{blur}, \text{brightness}, \text{contrast}, \text{resolution}, \text{occlusion}])$$
$$Q_{\text{text}} = \text{PTIS}$$
$$Q_{\text{meta}} = 1 - \text{fraction\_missing}$$

**Reliability (R):**
$$R_m = \sigma(\text{MLP}([Q_m, H_m, S_m, A_m]))$$

Where:
- $H_m$ = predictive entropy of modality-$m$ classifier
- $S_m$ = 1 - variance under TTA (5 augmentations)
- $A_m$ = mean cosine agreement with other modalities' predictions

**Consistency (C):**
$$C(x) = 1 - \frac{1}{\binom{|M|}{2}} \sum_{i<j} D_{\text{JS}}(p_i \| p_j)$$

Where $D_{\text{JS}}$ is Jensen-Shannon divergence between modality $i$ and $j$ predicted distributions.

**OOD Score:**
$$\text{OOD}(x) = \min_k (\mathbf{z}_{\text{fused}} - \boldsymbol{\mu}_k)^T \boldsymbol{\Sigma}_k^{-1} (\mathbf{z}_{\text{fused}} - \boldsymbol{\mu}_k)$$

Where $\boldsymbol{\mu}_k, \boldsymbol{\Sigma}_k$ are class-conditional mean and covariance on training embeddings.

### 14.3 Algorithm Pseudocode

```
ALGORITHM: DERMA-GUARD Inference Pipeline
─────────────────────────────────────────
INPUT:  case x = {clinical_img, dermoscopy_img, text, metadata}
OUTPUT: diagnosis ŷ, confidence c, consensus_level L, 
        evidence_trace T, report R

1.  SANITIZE(x)
    ├─ Verify MIME type ∈ {jpeg, png}
    ├─ Verify file_size < 10MB
    ├─ Verify 32 ≤ dimensions ≤ 4096
    └─ Scan for embedded executables

2.  PARALLEL_AGENT_EXECUTION(x)
    ├─ vision_reports ← VISION_TEAM.analyze(clinical_img, dermoscopy_img)
    │   ├─ dermlip_panderm: zero-shot logits + embedding
    │   ├─ panderm: visual features
    │   ├─ swin_tiny_clinical: logits + embedding
    │   ├─ swin_tiny_dermoscopy: logits + embedding
    │   └─ resnet152: logits + embedding
    ├─ scribe_report ← SCRIBE.extract(text, metadata)
    │   ├─ symptoms: {duration, growth, color_change, itching, pain, bleeding}
    │   ├─ ptis: [0,1]
    │   └─ text_embedding: 768-d
    └─ metadata_embedding ← METADATA_MLP(metadata)

3.  EVIDENCE_PROFILING(x, vision_reports, scribe_report)
    ├─ Q ← compute_quality(x)
    ├─ R ← compute_reliability(x, vision_reports)
    ├─ C ← compute_consistency(vision_reports)
    ├─ M ← get_missingness_flags(x)
    ├─ ood_score ← mahalanobis_distance(z_fused_placeholder, train_stats)
    └─ profile ← {Q, R, C, M, ood_score}

4.  STAGE_1_VERIFICATION(profile)
    ├─ IF ood_score > threshold_OOD:
    │      RETURN ESCALATE("Out-of-distribution case")
    ├─ IF C < 0.3 AND no_consensus:
    │      RETURN ACQUIRE("Resolve cross-modal conflict")
    ├─ IF sum(M) == 0:
    │      RETURN ABSTAIN("No evidence available")
    └─ IF any Q_m < 0.2:
           SET w_m = 0 for that modality

5.  ITERATIVE_FUSION(embeddings, profile)
    ├─ k ← 0
    ├─ w^(0) ← softmax(Q ⊙ R)
    ├─ REPEAT:
    │      z_fused^(k) ← Σ_m w_m^(k) · z_m
    │      ŷ^(k) ← argmax(classifier(z_fused^(k)))
    │      π ← W_prior[ŷ^(k), :]
    │      w^(k+1) ← softmax(α·f(Q,R,U,C) + β·π + γ·log(p_conflict))
    │      k ← k + 1
    │   UNTIL converged OR k == 3
    └─ RETURN ŷ, w*, z_fused

6.  CONSENSUS_HIERARCHY(ŷ, confidence, profile)
    ├─ IF ≥3 models agree AND confidence ≥ 0.8 AND C ≥ 0.3:
    │      L ← 1 (Strong Consensus)
    ├─ ELIF 2 models agree AND confidence ∈ [0.5, 0.8):
    │      L ← 2 (Moderate Agreement)
    │      ŷ ← weighted_arbitration(Q, R)
    ├─ ELIF confidence < 0.5 OR mean(Q) < 0.3:
    │      L ← 3 (High Uncertainty)
    │      target ← acquisition_policy(profile)
    │      RETURN ACQUIRE(target)
    └─ ELSE:
           L ← 4 (Critical Conflict)
           RETURN ESCALATE("Critical conflict detected")

7.  ORCHESTRATOR_SYNTHESIS(agent_reports, profile, ŷ, L)
    ├─ prompt ← structured_synthesis_prompt(...)
    ├─ report_draft ← LLM.generate(prompt, temperature=0, max_tokens=512)
    └─ RETURN report_draft

8.  STAGE_2_VERIFICATION(report_draft, evidence_json)
    ├─ rules_pass ← rule_based_check(report_draft, evidence_json)
    ├─ IF NOT rules_pass:
    │      report_draft ← regenerate_conservative(report_draft)
    ├─ llm_pass ← llm_based_check(report_draft, evidence_json)
    ├─ IF NOT llm_pass:
    │      RETURN ESCALATE("Verification failed")
    └─ RETURN report_draft

9.  LOG_AND_RETURN(ŷ, confidence, L, evidence_trace, report)
    ├─ SAVE_TO_DATABASE(case, prediction, trace)
    ├─ LOG_TO_WANDB(metrics)
    └─ RETURN result
```

### 14.4 Training Procedure

**Vision Models:**
1. Freeze backbone, train classification head for 5 epochs
2. Unfreeze last 2 stages of Swin-Tiny, fine-tune at 0.1× head LR
3. Optimizer: AdamW, weight decay 0.05, cosine schedule with linear warmup
4. Mixed precision (`torch.cuda.amp`), gradient clipping (max_norm=1.0)
5. Early stopping on validation macro-F1 (patience=10)
6. Save best + last checkpoint; evaluate test set with best only

**Fusion Network:**
1. Train jointly with classification objective
2. Loss: Focal Loss (γ=2.0) + class weights for imbalance
3. Diagnosis-adaptive prior matrix $\mathbf{W}_{\text{prior}}$ learned as a lookup table on validation set (not trained end-to-end; computed as empirical optimal weights per class)

**Reliability MLP:**
1. Trained jointly with the rest of the Evidence Manager
2. Target: binary correctness of each modality's prediction (derived from validation ground truth)

### 14.5 Complexity Analysis

| Component | Time | Space |
|-----------|------|-------|
| Vision Team (4 models, parallel) | $O(4 \times d^2)$ per image | $O(4 \times d)$ |
| Scribe (ClinicalBERT) | $O(n^2)$ for sequence length $n$ | $O(d)$ |
| Evidence Profiler | $O(K \times d^2)$ for Mahalanobis | $O(K \times d^2)$ |
| Iterative Fusion (3 iterations) | $O(3 \times |M| \times d)$ | $O(|M| \times d)$ |
| Consensus | $O(|M|^2)$ for pairwise agreement | $O(1)$ |
| **Total per case** | **~15–25 seconds on RTX 4090** | **~8GB GPU memory** |

---

## 15. BASELINE METHODS

### 15.1 Baseline Ladder

| Baseline | Description | Why Selected | Implementation |
|----------|-------------|------------|----------------|
| **B1: Majority Class** | Predict most frequent class in training set | Absolute floor; any system must beat this | `sklearn.dummy.DummyClassifier` |
| **B2: Metadata-Only** | Metadata MLP → classifier | Tests whether metadata alone is predictive | `src/models/metadata_mlp.py` |
| **B3: Clinical-Image-Only** | Swin-Tiny on clinical images | Tests clinical photography in isolation | `src/agents/vision_team.py` (single branch) |
| **B4: Dermoscopy-Only** | Swin-Tiny on dermoscopy images | Tests dermoscopy in isolation | `src/agents/vision_team.py` (single branch) |
| **B5: Concatenation Fusion** | Concat all embeddings → MLP | Standard early-fusion baseline | `torch.nn.Linear(sum(d_m), K)` |
| **B6: Image + Text** | Clinical + dermoscopy + text → concat → MLP | Tests text contribution | PAD-UFES-20 only |
| **B7: SkinM2Former** | Tri-modal cross-attention transformer | Published SOTA baseline for Derm7pt | Reproduced from Zhang et al. 2025 |
| **B8: DermFormer** | Nested ViT with entropy weighting | Published robust fusion baseline | Reproduce or cite with caveat |

### 15.2 Fair Comparison Rules

1. **Same data:** All baselines use identical train/val/test splits
2. **Same preprocessing:** All image models see identical augmentation pipelines
3. **Same evaluation:** All metrics computed with same code (`src/eval/metrics.py`)
4. **Same seeds:** 3–5 random seeds shared across all methods
5. **No test-set tuning:** Hyperparameters selected on validation only; test set touched once per method
6. **Ensemble diversity:** Model B (multi-model consensus) uses identical constituent models as DERMA-GUARD but with majority voting instead of evidence-weighted arbitration

---

## 16. EVALUATION FRAMEWORK

### 16.1 Classification Metrics

| Metric | Definition | Why It Matters | Formula |
|--------|-----------|---------------|---------|
| **Top-1 Accuracy** | Proportion of correct predictions | Primary performance indicator | $\frac{1}{N} \sum_{i=1}^N \mathbb{1}[\hat{y}_i = y_i]$ |
| **Balanced Accuracy** | Average of per-class recalls | Corrects for class imbalance | $\frac{1}{K} \sum_{k=1}^K \frac{TP_k}{TP_k + FN_k}$ |
| **Macro-F1** | Harmonic mean of precision and recall, averaged across classes | Best single metric for imbalanced multi-class | $\frac{1}{K} \sum_{k=1}^K F1_k$ |
| **AUROC** | Area under ROC curve | Threshold-independent discrimination | `sklearn.metrics.roc_auc_score` (OvR) |
| **Sensitivity** | True positive rate | Clinical: catch malignant cases | $\frac{TP}{TP + FN}$ |
| **Specificity** | True negative rate | Clinical: avoid unnecessary anxiety | $\frac{TN}{TN + FP}$ |
| **PPV** | Positive predictive value | Probability that positive prediction is correct | $\frac{TP}{TP + FP}$ |
| **NPV** | Negative predictive value | Probability that negative prediction is correct | $\frac{TN}{TN + FN}$ |

### 16.2 Calibration Metrics

| Metric | Definition | Why It Matters | Formula |
|--------|-----------|---------------|---------|
| **ECE (10-bin)** | Expected Calibration Error | Does confidence match accuracy? | $\sum_{b=1}^{10} \frac{n_b}{N} |\text{acc}_b - \text{conf}_b|$ |
| **Brier Score** | Mean squared error of probabilities | Proper scoring rule for probabilistic predictions | $\frac{1}{N} \sum (p_i - y_i)^2$ |

### 16.3 Safety & Robustness Metrics

| Metric | Definition | Why It Matters |
|--------|-----------|---------------|
| **Abstention Rate** | Fraction of cases where system abstains | Measures appropriate conservatism |
| **Selective Risk** | Error rate among non-abstained cases | Measures quality of retained predictions |
| **Risk-Coverage Curve** | Error vs. fraction of cases predicted | Trade-off between abstention and accuracy |
| **Recovery Rate** | Fraction of Level 3 cases that resolve after acquisition | Measures acquisition policy effectiveness |
| **Escalation Rate** | Fraction of cases escalated to human | Measures system humility |
| **Conflict Detection Precision** | TP conflicts / (TP + FP conflicts) | Measures Devil's Advocate accuracy |
| **Conflict Detection Recall** | TP conflicts / (TP + FN conflicts) | Measures completeness of conflict detection |
| **Hallucination Rate** | Fraction of reports with unsupported claims | Measures verification layer effectiveness |
| **NIR (Case-Level)** | Fraction of cases where any modality hurts | Measures negative information |
| **NIR (Modality-Level)** | Fraction of (case, modality) pairs that hurt | More actionable than case-level |

### 16.4 Efficiency Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Inference time (single case) | ≤30s | `time.perf_counter()` around pipeline |
| Inference time (batch) | ≤5s/case | Batch size 32 on GPU |
| GPU memory | ≤20GB | `nvidia-smi` |
| Training time (Swin-Tiny) | ≤6 hours | Single RTX 4090, 100 epochs |

---

**End of Part 1 coverage. Part 2 continues below with Sections 17–33.**

---

## 17. STATISTICAL ANALYSIS

### 17.1 Descriptive Statistics

For every reported metric, report:
- **Mean** across random seeds
- **Standard deviation** across random seeds
- **95% Confidence Interval** via bootstrap (1,000 resamples, case-level resampling)
- **Median** and **IQR** for skewed distributions (e.g., inference time)

### 17.2 Bootstrap Confidence Intervals

```python
# Pseudocode for bootstrap CI
def bootstrap_ci(metric_values, n_bootstrap=1000, confidence=0.95):
    """
    metric_values: array of per-case metric values
    Returns: (lower, upper) bound
    """
    n = len(metric_values)
    bootstrapped_means = []
    
    for _ in range(n_bootstrap):
        # Resample cases WITH replacement
        resample = np.random.choice(metric_values, size=n, replace=True)
        bootstrapped_means.append(np.mean(resample))
    
    alpha = 1 - confidence
    lower = np.percentile(bootstrapped_means, 100 * alpha / 2)
    upper = np.percentile(bootstrapped_means, 100 * (1 - alpha / 2))
    
    return lower, upper
```

**Critical Rule:** When aggregating per-case ablation results (leave-one-modality-out), treat each **case** as the independent unit, not each modality variant. Do not inflate sample size by counting subset variants of the same case as independent.

### 17.3 Significance Testing

| Comparison | Test | Why |
|------------|------|-----|
| DERMA-GUARD vs. SkinM2Former (paired, same cases) | McNemar's test | Paired binary outcomes; more powerful than independent t-test |
| DERMA-GUARD vs. DermFormer (paired) | McNemar's test | Same reason |
| Accuracy across multiple conditions | Repeated-measures ANOVA | Same cases across multiple stress conditions |
| Non-normal metric distributions | Wilcoxon signed-rank test | Non-parametric alternative to paired t-test |
| Abstention rate vs. chance | Binomial test | Tests if abstention rate differs from expected |

### 17.4 Effect Sizes

Report **Cohen's d** for all significant differences:

$$d = \frac{\bar{x}_1 - \bar{x}_2}{s_{\text{pooled}}}$$

| d | Interpretation |
|---|----------------|
| 0.2 | Small effect |
| 0.5 | Medium effect |
| 0.8 | Large effect |

### 17.5 Multiple Comparison Correction

When testing across 15 stress conditions, apply **Bonferroni correction**:
$$\alpha_{\text{adjusted}} = \frac{0.05}{15} \approx 0.0033$$

Or use **False Discovery Rate (FDR)** control with Benjamini-Hochberg procedure for less conservative correction.

### 17.6 Statistical Significance vs. Practical Significance

- **Statistical significance** (p < 0.05): The observed difference is unlikely due to chance.
- **Practical significance** (effect size): The observed difference matters clinically.

**Rule:** A 0.5% accuracy improvement may be statistically significant with 1,000 cases but is clinically meaningless. We require both statistical significance (p < 0.05) and practical significance (Cohen's d > 0.2 or absolute accuracy improvement > 2%) to claim superiority.

---

## 18. ABLATION STUDY

### 18.1 Linear Ablation Chain

| Configuration | Components Active | What It Tests |
|-------------|-------------------|---------------|
| A0 | Image-only (clinical + dermoscopy) | Floor performance |
| A1 | A0 + metadata | Metadata contribution |
| A2 | A1 + text | Text contribution |
| A3 | A2 + SkinM2Former-style fusion | Fusion architecture contribution |
| A4 | A3 + Quality (Q) | Quality estimation contribution |
| A5 | A4 + Reliability (R) | Reliability estimation contribution |
| A6 | A5 + Utility (U) | Utility estimation contribution |
| A7 | A6 + Consistency (C) | Conflict detection contribution |
| A8 | A7 + Sufficiency (S) | Sufficiency checking contribution |
| A9 | A8 + Uncertainty/Conformal | Uncertainty quantification contribution |
| A10 | A9 + Acquisition | Acquisition policy contribution |
| A11 | A10 + Verification | Verification layer contribution |
| **A12** | **Full DERMA-GUARD** | **Complete system** |

### 18.2 Factorial Ablation (Evidence Manager Components)

Test all $2^4 = 16$ combinations of Q, R, C, M:

| Q | R | C | M | Expected Behavior |
|---|---|---|---|---------------------|
| ✓ | ✗ | ✗ | ✗ | Quality-only baseline |
| ✗ | ✓ | ✗ | ✗ | Reliability-only baseline |
| ✗ | ✗ | ✓ | ✗ | Consistency-only baseline |
| ✗ | ✗ | ✗ | ✓ | Missingness-only baseline |
| ✓ | ✓ | ✗ | ✗ | Q+R interaction |
| ✓ | ✗ | ✓ | ✗ | Q+C interaction |
| ✓ | ✓ | ✓ | ✗ | Q+R+C (no missingness) |
| ✓ | ✓ | ✓ | ✓ | **Full Evidence Manager** |

**Expected Finding:** Q+R+C+M > any subset; Q and R may be partially redundant (if Q+R ≈ Q alone, R adds little); C provides unique value not captured by Q or R.

### 18.3 Ablation Table (Expected Results)

| Component Removed | Clean Accuracy | Stress Accuracy | Interpretation |
|-------------------|---------------|-----------------|----------------|
| Full DERMA-GUARD | 85.5% | 82% | Baseline |
| - Quality Check | 85.3% | 78% | Quality matters most under stress |
| - Conflict Check | 85.4% | 76% | Conflict detection is critical for safety |
| - Dynamic Fusion | 85.5% | 79% | Adaptation helps under distribution shift |
| - Acquisition | 85.5% | 75% | Acquisition is critical for recovery |
| - Multi-Model Ensemble | 83.4% | 72% | Ensemble diversity provides robustness |

---

## 19. ERROR ANALYSIS

### 19.1 Failure Categories

| Category | Definition | Investigation Method |
|----------|-----------|---------------------|
| **False Positives (Benign predicted as Malignant)** | Overdiagnosis | Examine cases where confidence was high but diagnosis was benign; check if text mentioned "growing" or "bleeding" |
| **False Negatives (Malignant predicted as Benign)** | Underdiagnosis | Most critical failure; examine all misses; check if dermoscopy quality was low |
| **OOD Failures** | Case far from training distribution | Mahalanobis distance analysis; visualize t-SNE of misclassified cases |
| **Conflict-Induced Errors** | Image and text contradict | Check if Devil's Advocate flagged conflict; if not, why? |
| **Acquisition Failures** | System acquired wrong evidence | Check if acquisition policy selected modality that did not resolve uncertainty |
| **Verification Failures** | Hallucinated report passed checks | Manual audit of 200 reports; flag unsupported claims |
| **Modality-Specific Failures** | One modality consistently wrong | Per-modality accuracy analysis; e.g., text-only MLP accuracy |

### 19.2 Error Analysis Feedback Loop

```
Error Analysis
      │
      ├──> Pattern identified (e.g., "text mentions bleeding → false positive melanoma")
      │
      ├──> Root cause analysis (e.g., "bleeding" has high correlation with melanoma in training set)
      │
      ├──> Hypothesis: PTIS should penalize vague bleeding mentions
      │
      ├──> Implement fix: Add specificity check to PTIS
      │
      ├──> Re-run on validation set
      │
      └──> Measure improvement → Document in "What Did Not Work" if no improvement
```

---

## 20. REPRODUCIBILITY ARCHITECTURE

### 20.1 Repository Structure

```text
DERMA-GUARD-RESEARCH/
├── README.md                          # Setup, reproduction instructions
├── LICENSE                            # MIT / Apache 2.0
├── CITATION.cff                       # Citation metadata
│
├── docs/
│   ├── architecture.md                # This document
│   ├── limitations.md                 # Known limitations
│   ├── repro_statement.md             # Exact reproduction steps
│   └── dataset_licenses/              # License files for Derm7pt, PAD-UFES-20
│
├── data/
│   ├── raw/                           # Original downloads (gitignored)
│   ├── interim/                       # Preprocessed (gitignored)
│   ├── processed/                     # Ready for training (gitignored)
│   └── splits/                        # FROZEN split files (committed)
│       ├── derm7pt_train.json
│       ├── derm7pt_val.json
│       ├── derm7pt_test.json
│       ├── derm7pt_calibration.json
│       ├── padufes_train.json
│       ├── padufes_val.json
│       └── padufes_test.json
│
├── src/                               # All source code
│   ├── __init__.py
│   ├── main.py                        # FastAPI entry
│   ├── config/                        # Hydra configs
│   ├── api/                           # REST API routes
│   ├── services/                      # Business logic orchestration
│   ├── agents/                        # Multi-agent system
│   │   ├── orchestrator.py
│   │   ├── vision_team.py
│   │   ├── scribe.py
│   │   ├── librarian.py
│   │   └── devils_advocate.py
│   ├── fusion/                        # Dynamic fusion + consensus
│   │   ├── adaptive_fusion.py
│   │   ├── consensus.py
│   │   └── acquisition.py
│   ├── evidence/                      # Q, R, U, C, M
│   │   ├── quality.py
│   │   ├── reliability.py
│   │   ├── utility.py
│   │   ├── consistency.py
│   │   └── missingness.py
│   ├── models/                        # DB models
│   ├── repositories/                  # Data access
│   ├── llm/                           # LLM client, prompts, verification
│   ├── retrieval/                     # FAISS RAG
│   ├── explain/                       # Grad-CAM
│   ├── stress/                        # DERMA-STRESS
│   ├── eval/                          # Metrics, ablation, stats
│   ├── data/                          # Loaders, preprocessing, audit
│   └── utils/                         # Shared utilities
│
├── tests/                             # Test suite
│   ├── test_data_pipeline.py
│   ├── test_vision_team.py
│   ├── test_evidence_profiler.py
│   ├── test_fusion.py
│   ├── test_consensus.py
│   ├── test_verification.py
│   ├── test_orchestrator.py
│   └── test_api.py
│
├── scripts/                           # Executable scripts
│   ├── dataset_audit.py
│   ├── make_splits.py
│   ├── train_vision.py
│   ├── train_fusion.py
│   ├── run_stress.py
│   ├── run_ablation.py
│   └── demo.py
│
├── notebooks/                         # Analysis notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_baseline_ladder.ipynb
│   ├── 03_ablation_analysis.ipynb
│   ├── 04_derma_stress_results.ipynb
│   └── 05_error_analysis.ipynb
│
├── experiments/                       # W&B / MLflow outputs (gitignored)
├── models/                            # Saved checkpoints (gitignored)
├── results/                             # Figures, tables, CSVs (committed)
│   ├── figures/
│   ├── tables/
│   └── raw_csvs/
│
├── configs/                             # Hydra configuration
│   ├── base.yaml
│   ├── model/
│   ├── data/
│   └── experiment/
│
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── setup.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── .github/
    └── workflows/
        └── ci.yml
```

### 20.2 Reproducibility Checklist

| Item | Requirement | Location |
|------|-------------|----------|
| **Exact seeds** | Python, NumPy, PyTorch, random | `configs/base.yaml` |
| **Dataset version** | SHA-256 of raw files | `data/dataset_audit.json` |
| **Split files** | Committed, never regenerated | `data/splits/*.json` |
| **Model configs** | All hyperparameters | `configs/model/*.yaml` |
| **Training commands** | Exact shell commands | `scripts/reproduce.sh` |
| **Environment** | Docker image + requirements | `Dockerfile`, `requirements.txt` |
| **Hardware info** | GPU model, CUDA version | Logged to W&B |
| **Software versions** | Python, PyTorch, CUDA | `requirements.txt` |
| **Model checkpoints** | Best validation checkpoint | MLflow artifacts |
| **Result files** | All tables and figures | `results/` (committed) |

### 20.3 Experiment Tracking

**Weights & Biases:**
- Project: `derma-guard-v4`
- Logged per run: config, metrics (step-level), model artifacts, hardware info
- Tags: `baseline`, `ablation`, `stress`, `seed-42`

**MLflow:**
- Model registry for checkpoint versioning
- Artifact storage for final models

---

## 21. EXPERIMENT EXECUTION WORKFLOW

### 21.1 Step-by-Step Execution

```bash
# Step 0: Environment Setup
git clone https://github.com/your-org/derma-guard.git
cd derma-guard
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Step 1: Data Preparation
python scripts/dataset_audit.py
# Verify: no hash collisions, class distributions reasonable

python scripts/make_splits.py
# Verify: splits committed to data/splits/

# Step 2: Baseline Training
python scripts/train_vision.py --config configs/model/swin_tiny.yaml --data derm7pt
# Repeat for: metadata-only, clinical-only, dermoscopy-only, concat fusion

# Step 3: SkinM2Former Reproduction
python scripts/train_vision.py --config configs/experiment/skinm2former_repro.yaml
# Log delta from published numbers

# Step 4: Vision Team Setup
python scripts/train_vision.py --config configs/model/dermlip_panderm.yaml  # zero-shot
python scripts/train_vision.py --config configs/model/panderm.yaml          # feature extract
python scripts/train_vision.py --config configs/model/swin_tiny.yaml        # fine-tuned
python scripts/train_vision.py --config configs/model/resnet152.yaml       # fine-tuned

# Step 5: Fusion Training
python scripts/train_fusion.py --config configs/model/fusion/adaptive.yaml

# Step 6: DERMA-STRESS
python scripts/run_stress.py \
    --dataset derm7pt \
    --split test \
    --conditions all \
    --model_variants full \
    --seeds 42 123 456

# Step 7: Ablation Study
python scripts/run_ablation.py \
    --type linear \
    --dataset derm7pt \
    --seeds 42 123 456

python scripts/run_ablation.py \
    --type factorial \
    --components Q R C M \
    --dataset derm7pt

# Step 8: Statistical Analysis
python -m src.eval.stats --experiment_dir experiments/ --output_dir results/

# Step 9: Generate Figures
jupyter nbconvert --execute notebooks/04_derma_stress_results.ipynb

# Step 10: Verification & Report
python scripts/demo.py --case_id test-case-001
# Manual audit of 50 cases for abstention appropriateness
```

---

## 22. RESULTS MANAGEMENT

### 22.1 Experiment ID Scheme

```
{dataset}_{model_variant}_{condition}_seed{seed}_{timestamp}
```

Example: `derm7pt_full_blur_seed42_20260825`

### 22.2 Result Storage Structure

```text
results/
├── experiments/
│   ├── derm7pt_full_clean_seed42_20260825/
│   │   ├── config.yaml              # Exact config used
│   │   ├── metrics.json             # All computed metrics
│   │   ├── predictions.csv          # Per-case predictions
│   │   ├── fusion_weights.csv       # Per-case weights
│   │   ├── evidence_profiles.csv    # Per-case Q,R,C,M
│   │   └── model_checkpoint/        # Symlink to MLflow artifact
│   └── ...
│
├── tables/
│   ├── baseline_ladder.tex
│   ├── stress_comparison.tex
│   ├── ablation_linear.tex
│   ├── ablation_factorial.tex
│   └── statistical_tests.tex
│
├── figures/
│   ├── baseline_ladder.png
│   ├── stress_accuracy_drop.png
│   ├── risk_coverage_curve.png
│   ├── confusion_matrix_full.png
│   ├── ece_reliability_diagram.png
│   ├── ablation_heatmap.png
│   ├── fusion_weight_distribution.png
│   └── acquisition_recovery_rate.png
│
└── logs/
    └── training_logs/               # Raw W&B exports
```

### 22.3 Per-Case Prediction Format

```csv
case_id,ground_truth,predicted,confidence,consensus_level,
fusion_weight_clinical,fusion_weight_dermoscopy,fusion_weight_text,fusion_weight_metadata,
Q_clinical,Q_dermoscopy,Q_text,Q_meta,
R_clinical,R_dermoscopy,R_text,R_meta,
C,ood_score,abstained,escalated,acquisition_target,seed
```

---

## 23. VISUALIZATION STRATEGY

### 23.1 Required Visualizations

| Figure | Question It Answers | Data Required |
|--------|---------------------|---------------|
| **Architecture Diagram** | How does the system work? | System design |
| **Baseline Ladder Bar Chart** | Does multimodal help? | Baseline accuracies |
| **Stress Condition Heatmap** | How does each model degrade? | Per-condition accuracy matrix |
| **Risk-Coverage Curve** | Is abstention effective? | Confidence + correctness per case |
| **ECE Reliability Diagram** | Is the system calibrated? | Confidence bins + accuracy |
| **Fusion Weight Distribution** | Does fusion adapt? | Per-case weights by diagnosis |
| **Consensus Level Pie Chart** | How often does each level trigger? | Consensus level counts |
| **Ablation Heatmap** | Which components matter most? | Factorial ablation accuracies |
| **Acquisition Recovery Plot** | Does acquisition help? | Uncertainty before/after acquisition |
| **Grad-CAM Overlay** | What does each model look at? | Image + attention map |
| **t-SNE Embedding Plot** | Are classes separable? | Fused embeddings + labels |
| **Bootstrap CI Error Bars** | Are results statistically robust? | Mean ± 95% CI per metric |

### 23.2 Figure Standards

- Resolution: 300 DPI minimum
- Format: PNG for web, PDF for paper, SVG for scalability
- Color palette: Colorblind-friendly (e.g., viridis, colorbrewer)
- Error bars: 95% bootstrap CI or standard deviation across seeds
- Statistical significance: Asterisks (* p<0.05, ** p<0.01, *** p<0.001)

---

## 24. RESEARCH VALIDATION

### 24.1 Validity Types

| Type | Definition | Threat | Mitigation |
|------|-----------|--------|------------|
| **Internal Validity** | Are observed effects truly caused by the intervention? | Confounding from class imbalance | Class weights, focal loss, stratified splits |
| **External Validity** | Do results generalize beyond the study? | Only two datasets; synthetic text | Acknowledge limitation; suggest future work on real narratives |
| **Construct Validity** | Do metrics measure what we claim? | Accuracy may not reflect clinical utility | Report sensitivity/specificity/PPV/NPV; human audit |
| **Statistical Validity** | Are conclusions statistically sound? | Multiple comparisons, inflated sample size | Bonferroni/FDR correction; bootstrap CIs; case-level resampling |

### 24.2 Threats to Validity Matrix

| Threat | Why It Matters | Impact | Mitigation |
|--------|---------------|--------|------------|
| **Small dataset size (Derm7pt: 1,011 cases)** | High variance in estimates; risk of overfitting | High | Strict official split; strong regularization; report confidence intervals |
| **Synthetic text ≠ real patient narratives** | PAD-UFES-20 text is generated from structured fields | Medium | Leakage validation; PTIS filtering; acknowledge in limitations |
| **No prospective clinical validation** | Retrospective benchmark may not reflect real-world performance | High | Explicitly state as limitation; propose future clinical reader study |
| **LLM hallucination in reports** | Orchestrator may generate unsupported claims | High | Two-stage verification; structured tool-calling; temperature=0 |
| **GPU-specific results** | Different hardware may yield different timing | Low | Report hardware specs; timing is secondary to accuracy |
| **Hyperparameter sensitivity** | Results may not replicate with different tuning | Medium | Report all hyperparameters in config files; use early stopping on validation |
| **Dataset shift** | Derm7pt (dermoscopy) and PAD-UFES-20 (smartphone) have different distributions | Medium | Evaluate separately; never joint train; report per-dataset |
| **Confirmation bias in ablation** | Researchers may interpret ablation to favor their method | Medium | Pre-register ablation design; report all configurations including negative results |

---

## 25. ETHICAL CONSIDERATIONS

### 25.1 Privacy & Data Protection

- **No real patient PII:** All data comes from public benchmark datasets with research licenses
- **Synthetic text:** Generated from structured fields without diagnosis leakage; no real patient narratives
- **Local processing:** All inference runs on local GPU; no cloud upload of images or text
- **Evidence traces:** Stored locally; no external sharing

### 25.2 Bias & Fairness

- **Skin tone:** Derm7pt and PAD-UFES-20 lack explicit skin-tone labels; fairness analysis is out of scope but acknowledged as critical future work (Daneshjou et al. 2022)
- **Geographic bias:** PAD-UFES-20 is Brazilian; Derm7pt is European; results may not generalize globally
- **Socioeconomic bias:** Smartphone image quality correlates with device quality; may disadvantage lower-income patients

### 25.3 Responsible AI

- **Not a diagnostic tool:** Explicitly labeled as research prototype; never presented as clinical product
- **Human-in-the-loop:** Level 4 consensus always escalates to human; Level 3 recommends acquisition
- **Transparency:** Full evidence trace provided for every decision; model versioning enables audit
- **Potential misuse:** Could be used to generate fake diagnoses; mitigated by requiring full evidence trace and clinician review

### 25.4 IRB / Ethics Approval

- **Not required for this phase:** Research uses publicly available, de-identified benchmark datasets with no human subjects interaction
- **Future clinical validation:** Would require IRB approval and informed consent; explicitly identified as future work

---

## 26. RESEARCH LIMITATIONS

### 26.1 Dataset Limitations

| Limitation | Effect | Mitigation |
|------------|--------|------------|
| Derm7pt small (1,011 cases) | High variance; limited generalization | Official split adherence; bootstrap CIs; data augmentation |
| PAD-UFES-20 synthetic text | May not reflect real patient language | Leakage checks; PTIS validation; acknowledge in paper |
| No longitudinal data | Cannot validate temporal reasoning | Simulated follow-up only; clearly labeled |
| No skin-tone labels | Cannot evaluate fairness | Acknowledge; cite Daneshjou et al.; propose future work |

### 26.2 Method Limitations

| Limitation | Effect | Mitigation |
|------------|--------|------------|
| Iterative fusion may not converge | Unstable predictions | Max 3 iterations; fallback to iteration 0 weights |
| Diagnosis-adaptive matrix learned on validation | May overfit to validation distribution | Small matrix (K × M); regularized; never tuned on test |
| Utility requires ground truth | Cannot compute at inference | Use expected utility from training statistics; clearly distinguish retrospective vs. deployable |
| LLM verification not perfect | Hallucinations may slip through | Two-stage check; rule-based first; conservative fallback |

### 26.3 Experimental Limitations

| Limitation | Effect | Mitigation |
|------------|--------|------------|
| Only 2 datasets | Limited external validity | Acknowledge; suggest HAM10000, ISIC as future validation |
| Retrospective evaluation only | No prospective clinical evidence | Explicitly state; propose reader study |
| Single-GPU training | Cannot scale to larger models | Acknowledge; PanDerm and DermLIP are frozen/fine-tuned, not trained from scratch |
| 8-week timeline | Limited hyperparameter tuning | Use published hyperparameters where possible; early stopping |

### 26.4 Generalization Limitations

- Results on Derm7pt (clinical + dermoscopy) may not transfer to smartphone-only settings
- Results on PAD-UFES-20 (Brazilian population) may not transfer to other ethnicities
- Synthetic text generation pipeline may produce different distributions than real patient narratives
- DERMA-STRESS corruptions are simulated; real-world corruption may differ

---

## 27. RESEARCH TIMELINE

### 27.1 Gantt-Style Timeline (Text)

```
WEEK 1: FOUNDATION
├─ Day 1-2: Literature review finalization, dataset download
├─ Day 3-4: Dataset audit (SHA-256, phash, leakage check)
├─ Day 5-7: Baseline ladder implementation (6 baselines)
└─ Deliverable: Clean data + trained baselines

WEEK 2: VISION + TEXT PIPELINES
├─ Day 8-10: Vision Specialist Team (load 4 models, parallel inference)
├─ Day 11-12: Swin-Tiny fine-tuning (clinical + dermoscopy branches)
├─ Day 13-14: Scribe Agent (ClinicalBERT, PTIS, synthetic text)
└─ Deliverable: Vision reports + text embeddings

WEEK 3: EVIDENCE PROFILER
├─ Day 15-17: OOD detector (Mahalanobis), Reliability MLP
├─ Day 18-19: Consistency computation (JS divergence)
├─ Day 20-21: Missingness tracking, overall risk score
└─ Deliverable: Devil's Advocate agent

WEEK 4: DYNAMIC FUSION + CONSENSUS
├─ Day 22-24: Iterative EM-style fusion implementation
├─ Day 25-26: Diagnosis-adaptive weight matrix learning
├─ Day 27-28: 4-level consensus hierarchy + acquisition policy
└─ Deliverable: Fusion + consensus pipeline

WEEK 5: VERIFICATION + ORCHESTRATOR
├─ Day 29-30: Two-stage verification (rules + LLM)
├─ Day 31-32: Orchestrator with tool-calling
├─ Day 33-35: Integration testing (end-to-end cases)
└─ Deliverable: Full pipeline working

WEEK 6: DERMA-STRESS
├─ Day 36-38: Implement 15 corruption conditions
├─ Day 39-40: Run stress benchmark on all model variants
├─ Day 41-42: Compile results, compute metrics
└─ Deliverable: Complete stress benchmark results

WEEK 7: ABLATION + STATS + DEMO
├─ Day 43-44: Linear ablation study
├─ Day 45: Factorial ablation study
├─ Day 46-47: Bootstrap CIs, significance tests
├─ Day 48-49: Streamlit demo (Patient App + Clinician Console)
└─ Deliverable: Ablation results + demo

WEEK 8: PAPER + HARDENING
├─ Day 50-52: Error analysis + "What Did Not Work" section
├─ Day 53-54: Paper drafting (Introduction through Conclusion)
├─ Day 55-56: Final testing, bug fixes, documentation
└─ Deliverable: Paper draft + reproducibility package
```

### 27.2 Critical Research Path

```
Dataset Audit → Vision Team → Evidence Profiler → Dynamic Fusion → 
Consensus → Verification → DERMA-STRESS → Ablation → Paper
```

**Parallel Tracks:**
- Text pipeline (Week 2, parallel with Vision)
- Demo development (Week 7, parallel with Ablation)
- Documentation (continuous)

### 27.3 Milestones

| Milestone | Date | Criteria |
|-----------|------|----------|
| M1: Data Ready | Day 3 | Audit clean, splits frozen |
| M2: Baselines Done | Day 7 | All 6 baselines trained |
| M3: Agents Working | Day 21 | All 4 agents produce correct output |
| M4: Pipeline End-to-End | Day 35 | 10 test cases process correctly |
| M5: Stress Results | Day 42 | All 15 conditions evaluated |
| M6: Demo Ready | Day 49 | Streamlit runs without errors |
| M7: Paper Draft | Day 56 | Complete draft with all sections |

---

## 28. RESEARCH PAPER STRUCTURE

### 28.1 Proposed Paper Outline

**Target Venue:** MICCAI 2026 / npj Digital Medicine / Communications Medicine

```
1. ABSTRACT
   ├─ Problem: Black-box fusion is unsafe under imperfect evidence
   ├─ Method: Multi-agent consensus with dynamic diagnosis-adaptive fusion
   ├─ Results: DERMA-GUARD achieves X% stress accuracy vs Y% baseline
   └─ Conclusion: Evidence management enables safer dermatology AI

2. INTRODUCTION
   ├─ Skin cancer burden and AI promise
   ├─ Current systems: accurate but not safe
   ├─ Gap: No unified evidence-management framework
   └─ Contribution: DERMA-GUARD + DERMA-STRESS

3. RELATED WORK
   ├─ Multimodal dermatology AI (SkinM2Former, DermFormer, PanDerm)
   ├─ Agentic medical AI (KGDAgents, SkinGPT-X, DermAgent)
   ├─ Uncertainty & selective prediction (Fayyad et al., Jabbour et al.)
   └─ Missing modality & robustness (Liu et al., Bouzon et al.)

4. METHODS
   ├─ 4.1 Datasets (Derm7pt, PAD-UFES-20)
   ├─ 4.2 Vision Specialist Team (4 models)
   ├─ 4.3 Scribe Agent (ClinicalBERT, PTIS)
   ├─ 4.4 Devil's Advocate (Q, R, C, M, OOD)
   ├─ 4.5 Iterative Diagnosis-Adaptive Fusion
   ├─ 4.6 4-Level Consensus Hierarchy
   ├─ 4.7 Simulated Evidence Acquisition
   ├─ 4.8 Two-Stage Verification
   └─ 4.9 DERMA-STRESS Benchmark

5. EXPERIMENTS
   ├─ 5.1 Baseline Ladder
   ├─ 5.2 SkinM2Former Reproduction
   ├─ 5.3 Ablation Study (Linear + Factorial)
   ├─ 5.4 DERMA-STRESS Results
   └─ 5.5 Statistical Analysis

6. RESULTS
   ├─ Table 1: Baseline comparison (clean data)
   ├─ Table 2: DERMA-STRESS results (all conditions)
   ├─ Table 3: Ablation study
   ├─ Figure 1: Architecture diagram
   ├─ Figure 2: Risk-coverage curves
   ├─ Figure 3: Stress accuracy heatmap
   └─ Figure 4: Fusion weight distributions by diagnosis

7. DISCUSSION
   ├─ Interpretation of results
   ├─ Why dynamic fusion helps
   ├─ Why conflict detection is critical
   ├─ Limitations (dataset size, synthetic text, no prospective validation)
   └─ "What Did Not Work" section

8. CONCLUSION
   └─ Summary of contributions and future directions

9. REFERENCES
   └─ ~30–40 citations

10. SUPPLEMENTARY MATERIALS
    ├─ Full DERMA-STRESS tables
    ├─ Per-class metrics
    ├─ Hyperparameter settings
    ├─ Computational budget
    └─ Reproducibility checklist
```

### 28.2 Evidence Mapping

| Paper Section | Evidence Required | Source |
|---------------|-------------------|--------|
| Introduction | Motivation statistics | WHO cancer reports, prior AI accuracy claims |
| Related Work | Comparison table | Literature review (Section 3) |
| Methods | Architecture details | This document, code |
| Experiments | Baseline numbers | Experiments E1–E14 |
| Results | Tables and figures | `results/` directory |
| Discussion | Error analysis | `notebooks/05_error_analysis.ipynb` |
| Limitations | Known issues | Section 26 of this document |

---

## 29. CONTRIBUTION STATEMENT

### 29.1 Scientific Contribution

> **Novel Knowledge:** We demonstrate that a multi-agent consensus framework with explicit per-modality evidence quality assessment, iterative diagnosis-adaptive fusion, and a 4-level decision hierarchy achieves safer behavior under imperfect evidence than both single-model and static-ensemble baselines in multimodal dermatological diagnosis. We further show that systematic semantic adversarial testing reveals vulnerabilities not captured by standard pixel-level corruptions.

### 29.2 Technical Contribution

> **Novel System:** DERMA-GUARD is the first open-source implementation unifying:
> 1. A 4-model diverse vision ensemble (VLM + foundation + CNN + transformer)
> 2. A Devil's Advocate evidence profiler with OOD detection and cross-modal conflict measurement
> 3. Iterative EM-style diagnosis-adaptive fusion with convergence guarantees
> 4. A 4-level consensus hierarchy replacing traditional conformal prediction sets
> 5. Simulated acquisition-as-consensus-breaker with gradient-boosted policy
> 6. Two-stage verification preventing LLM hallucination in clinical reports
> 7. DERMA-STRESS: 15-condition benchmark including semantic adversarial corruptions

### 29.3 Experimental Contribution

> **New Empirical Evidence:** We provide the first systematic evaluation of multi-agent dermatology AI under 15 stress conditions, with bootstrap confidence intervals, factorial ablation, and per-class metrics on two public datasets. We document both successes and failures transparently.

### 29.4 Practical Contribution

> **Clinical Utility:** The evidence trace and consensus hierarchy provide a template for "trustworthy AI" evaluation that regulators and clinicians can inspect. The abstention and escalation mechanisms offer a concrete alternative to black-box confidence scores.

---

## 30. FUTURE WORK

### 30.1 Short-Term (3–6 months)

| Direction | Description | Expected Impact |
|-----------|-------------|-----------------|
| **Gradient-boosted acquisition** | Replace lookup table with XGBoost/LightGBM policy | +5% recovery rate |
| **DermatoLlama integration** | Replace Qwen2.5 with 11B dermatology-specific VLM | Better report quality, fewer hallucinations |
| **Real patient text** | Partner with hospital for real narratives | Validate synthetic text pipeline |
| **HAM10000 / ISIC validation** | Test on additional public datasets | Stronger external validity |

### 30.2 Medium-Term (6–12 months)

| Direction | Description | Expected Impact |
|-----------|-------------|-----------------|
| **Prospective reader study** | Dermatologists evaluate DERMA-GUARD outputs on real cases | Clinical validation |
| **Skin-tone fairness analysis** | Explicit subgroup evaluation across Fitzpatrick types | Equity in dermatology AI |
| **Longitudinal tracking** | Real follow-up data for temporal reasoning | Monitor lesion progression |
| **Mobile deployment** | Optimize for smartphone inference | Point-of-care utility |

### 30.3 Long-Term (1–2 years)

| Direction | Description | Expected Impact |
|-----------|-------------|-----------------|
| **Regulatory pathway** | FDA pre-submission for clinical decision support | Commercial viability |
| **Multi-center validation** | Evaluate across hospitals in multiple countries | Global generalization |
| **EHR integration** | API for hospital information systems | Workflow integration |
| **Real-time dermoscopy** | Streaming video analysis | Dynamic examination |

---

## 31. COMPLETE RESEARCH CHECKLIST

### 31.1 Pre-Research

- [ ] Research problem defined and scoped
- [ ] Research motivation documented
- [ ] Literature search completed (PubMed, arXiv, IEEE, ACM)
- [ ] Literature review matrix completed
- [ ] Research gap identified and justified
- [ ] Research questions defined (main + supporting)
- [ ] Hypotheses stated (null + alternative where applicable)
- [ ] Methodology selected and justified
- [ ] Datasets identified and downloaded
- [ ] Dataset licenses verified
- [ ] Data permissions / IRB requirements checked
- [ ] Baseline methods identified

### 31.2 Research Execution

- [ ] Dataset audit completed (no leakage)
- [ ] Splits frozen and committed
- [ ] Baseline implementations completed
- [ ] SkinM2Former reproduced (with documented gap)
- [ ] Vision Specialist Team implemented (4 models)
- [ ] Scribe Agent implemented (ClinicalBERT + PTIS)
- [ ] Devil's Advocate implemented (Q, R, C, M, OOD)
- [ ] Dynamic Fusion implemented (iterative, convergent)
- [ ] Consensus Hierarchy implemented (4 levels)
- [ ] Acquisition Policy implemented
- [ ] Two-Stage Verification implemented
- [ ] Orchestrator implemented (tool-calling)
- [ ] RAG index built (individual embeddings)

### 31.3 Evaluation

- [ ] Baseline ladder experiments completed
- [ ] DERMA-STRESS all 15 conditions tested
- [ ] Ablation study (linear) completed
- [ ] Ablation study (factorial) completed
- [ ] 3–5 random seeds run for primary experiments
- [ ] Bootstrap 95% CIs computed
- [ ] Statistical significance tests performed
- [ ] Effect sizes reported
- [ ] Error analysis completed
- [ ] Failure cases categorized

### 31.4 Documentation & Dissemination

- [ ] All figures generated (300 DPI, colorblind-friendly)
- [ ] All tables formatted (LaTeX)
- [ ] Code documented (docstrings, type hints)
- [ ] README with reproduction instructions
- [ ] "What Did Not Work" section written
- [ ] Limitations section complete
- [ ] Paper draft complete (all sections)
- [ ] Supplementary materials prepared
- [ ] Reproducibility package committed
- [ ] Demo video recorded

---

## 32. FINAL "WHY / WHAT / HOW / WHEN / EVIDENCE / CONTRIBUTION / LIMITATIONS / REPRODUCIBILITY"

### WHY

> Skin cancer is common and deadly when missed. Current AI dermatology systems achieve high accuracy on clean data but force confident predictions on blurry images, vague text, and incomplete metadata — a direct patient-safety risk. We need systems that reason like clinical panels: weighing evidence, detecting conflicts, and knowing when to ask for help.

### WHAT

> DERMA-GUARD v4.0: A multi-agent dermatological diagnosis system with a 4-model vision ensemble, an evidence profiler (Devil's Advocate), iterative diagnosis-adaptive fusion, a 4-level consensus hierarchy, simulated evidence acquisition, and two-stage hallucination prevention — evaluated on the 15-condition DERMA-STRESS benchmark.

### HOW

> Through parallel agent execution (vision, text, evidence profiling), iterative EM-style fusion that adapts weights based on suspected diagnosis, consensus-based decision making, and systematic corruption testing with bootstrap statistical validation.

### WHEN

> 8-week implementation: Foundation (Week 1), Core System (Weeks 2–4), Evaluation (Weeks 5–6), Delivery (Weeks 7–8).

### EVIDENCE

> Baseline ladder proving multimodal value; SkinM2Former reproduction gap documented; DERMA-STRESS showing ≥75% accuracy under single failure; ≥80% conflict detection precision; ≥70% acquisition recovery rate; bootstrap 95% CIs on all claims; human audit of abstention appropriateness.

### CONTRIBUTION

> First unified framework combining multi-model consensus, dynamic diagnosis-adaptive fusion, evidence management, acquisition, and systematic multi-agent stress testing for dermatology. Open-source implementation with full reproducibility package.

### LIMITATIONS

> Small dataset (Derm7pt: 1,011 cases); synthetic patient text; retrospective evaluation only; no skin-tone fairness analysis; single-GPU training constraints; LLM hallucination risk mitigated but not eliminated.

### REPRODUCIBILITY

> Frozen splits (seed=42); exact hyperparameters in Hydra configs; Docker image; MLflow model artifacts; W&B experiment logs; bootstrap CIs; code at `github.com/your-org/derma-guard`.

---

## 33. FIRST 10 RESEARCH ACTIONS

1. **Finalize the research problem statement** — Write one paragraph clearly stating the gap, the research question, and why it matters. Post it in the team Slack and get consensus.

2. **Complete the literature search** — Search PubMed, arXiv, IEEE Xplore, and ACM for papers from 2021–2026 on multimodal dermatology AI, agentic medical AI, and evidence-aware fusion. Populate the literature review matrix (Section 3).

3. **Download and audit both datasets** — Download Derm7pt and PAD-UFES-20. Run SHA-256 and perceptual hash checks. Document any collisions or quality issues in `docs/dataset_audit.md`.

4. **Verify model availability** — Attempt to load DermLIP-PanDerm, PanDerm encoder, ClinicalBERT, and Qwen2.5-7B. If any fail, immediately switch to backup models and document the change.

5. **Create frozen splits** — Run `scripts/make_splits.py` with seed=42. Commit the JSON files to `data/splits/`. Write a test that fails if splits are regenerated.

6. **Implement the first baseline** — Train the majority-class classifier and metadata-only MLP. Verify they achieve expected performance ranges. This validates the data pipeline.

7. **Draft the Devil's Advocate design doc** — Write a 1-page specification for the Evidence Profiler: exact inputs, outputs, and algorithms for Q, R, C, M, and OOD. Get team review before coding.

8. **Set up experiment tracking** — Create W&B project `derma-guard-v4`. Log a dummy run from each team member's machine to verify connectivity and GPU detection.

9. **Write the first unit test** — Implement `tests/test_data_pipeline.py` that verifies split reproducibility and class distribution. Set up CI to run this test on every PR.

10. **Schedule Week 1 retrospective** — On Day 7, review: Is the data clean? Do all models load? Are baselines training? Adjust timeline immediately if any blockers exist.

---

*End of DERMA-GUARD v4.0 Research Project Full Workflow Documentation.*

**Part 1 (Sections 1–16) + Part 2 (Sections 17–33) = Complete Document**
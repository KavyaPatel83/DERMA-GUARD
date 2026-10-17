 Here is your complete, self-contained implementation prompt for Claude. Copy-paste this entire block into Claude.

---

```
You are an expert AI/ML engineer and researcher specializing in multimodal medical AI, PyTorch, and multi-agent systems. I need you to implement a complete research project called DERMA-GUARD v4.0 from scratch, following this exact specification. Do not deviate from the architecture, algorithms, or design decisions described below unless explicitly told to improvise.

# PROJECT: DERMA-GUARD v4.0
## Agentic Evidence-Management Framework for Reliable Multimodal Dermatological Diagnosis

### CORE HYPOTHESIS
A multi-agent consensus framework with dynamic diagnosis-adaptive evidence fusion and explicit evidence management reduces unsafe decisions in multimodal dermatology under imperfect evidence, compared to conventional single-model and static-ensemble baselines.

---

## PART 0: FOUNDATION & SETUP

### Repository Structure (Create exactly this)
```
DERMA-GUARD/
├── configs/
│   ├── base.yaml
│   ├── model/
│   │   ├── vision/
│   │   │   ├── dermlip_panderm.yaml
│   │   │   ├── panderm.yaml
│   │   │   ├── swin_tiny.yaml
│   │   │   └── resnet152.yaml
│   │   ├── text/
│   │   │   └── clinicalbert.yaml
│   │   └── fusion/
│   │       └── adaptive.yaml
│   ├── data/
│   │   ├── derm7pt.yaml
│   │   └── pad_ufes.yaml
│   └── experiment/
│       ├── baseline_ladder/
│       ├── ablation/
│       └── stress/
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── splits/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   ├── api/
│   ├── services/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── vision_team.py
│   │   ├── scribe.py
│   │   ├── librarian.py
│   │   └── devils_advocate.py
│   ├── fusion/
│   │   ├── __init__.py
│   │   ├── adaptive_fusion.py
│   │   ├── consensus.py
│   │   └── acquisition.py
│   ├── evidence/
│   │   ├── __init__.py
│   │   ├── quality.py
│   │   ├── reliability.py
│   │   ├── utility.py
│   │   ├── consistency.py
│   │   └── missingness.py
│   ├── models/
│   ├── repositories/
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── prompts.py
│   │   ├── extraction.py
│   │   ├── report_gen.py
│   │   └── verification.py
│   ├── retrieval/
│   ├── explain/
│   ├── stress/
│   ├── eval/
│   ├── data/
│   └── utils/
├── tests/
├── scripts/
├── notebooks/
├── experiments/
├── app/
│   ├── patient_app.py
│   └── clinician_console.py
├── docs/
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── Dockerfile
└── README.md
```

### Technology Stack
- Python 3.10+
- PyTorch 2.0+ with CUDA
- timm (for Swin-Tiny, ResNet152)
- HuggingFace Transformers (for ClinicalBERT, DermLIP-PanDerm)
- FAISS-CPU (for RAG)
- Hydra + OmegaConf (for configs)
- Weights & Biases (for experiment tracking)
- MLflow (for model registry)
- Ollama with Qwen2.5:7B-Instruct (for LLM)
- FastAPI (for backend API)
- Streamlit (for demo)
- pytest + coverage (for testing)
- OpenCV + Albumentations (for image processing and stress testing)
- scikit-learn (for OOD detection, acquisition policy)
- structlog (for structured logging)

### requirements.txt
```
torch>=2.0.0
torchvision
timm
transformers
accelerate
huggingface_hub
faiss-cpu
hydra-core
omegaconf
wandb
mlflow
fastapi
uvicorn
streamlit
pillow
opencv-python
albumentations
scikit-learn
scipy
numpy
pandas
matplotlib
seaborn
plotly
pytest
pytest-cov
black
isort
flake8
mypy
structlog
python-multipart
httpx
requests
```

### Base Config (configs/base.yaml)
```yaml
defaults:
  - model/vision/dermlip_panderm
  - model/vision/panderm
  - model/vision/swin_tiny
  - model/vision/resnet152
  - model/text/clinicalbert
  - model/fusion/adaptive
  - data/derm7pt

project:
  name: derma-guard
  seed: 42

training:
  batch_size: 32
  epochs: 100
  lr: 1e-4
  weight_decay: 0.05
  gradient_clip: 1.0
  mixed_precision: true
  early_stopping:
    patience: 10
    monitor: val_macro_f1
    mode: max

fusion:
  max_iterations: 3
  convergence_threshold: 0.05
  diagnosis_adaptive: true

consensus:
  strong_threshold: 0.80
  conflict_threshold: 0.60
  entropy_threshold: 1.5
  quality_threshold: 0.30

llm:
  model: qwen2.5:7b
  max_tokens: 512
  timeout: 30
  temperature: 0.0
  max_retries: 2
```

---

## PART 1: DATA PIPELINE

### Datasets
1. **Derm7pt**: 1,011 cases. Official split: 413 train / 203 validation / 395 test. Use published index files. NEVER regenerate.
2. **PAD-UFES-20**: 2,298 smartphone images. Patient-level split 70/15/15 with seed=42. Group by patient_id, shuffle groups, assign cumulatively. Save to `data/splits/padufes_{train,val,test}.json` and commit.

### Dataset Audit (scripts/dataset_audit.py)
- Compute SHA-256 for every image
- Compute perceptual hash (imagehash.phash) for every image
- Flag collisions within/across datasets
- Output: `dataset_report.json`, `missingness.png`, `class_distribution.png`
- BLOCK training until clean

### Preprocessing
- Training: RandomResizedCrop(224), HorizontalFlip, rotation ±15°, ColorJitter, Normalize(ImageNet mean/std)
- Validation/Test: Resize(256), CenterCrop(224), Normalize(ImageNet mean/std)
- Metadata: z-score normalize continuous fields using train stats only. Categorical: learned embeddings (dim = min(50, (n_categories+1)//2)). Missing: binary indicator + zero imputation.

### Synthetic Text (PAD-UFES-20 only)
- Prompt Qwen2.5 with fields: age_bucket, body_location, grew, itch, bleed, changed, elevation
- NEVER include diagnosis in prompt
- Validation: regex diagnosis-term scan, extracted-field diff, embedding diversity (cosine < 0.97)
- Store: {case_id, text, source_fields, quality_flags}

---

## PART 2: VISION SPECIALIST TEAM (src/agents/vision_team.py)

Implement a class `VisionSpecialistTeam` that runs 4 models in parallel.

### Model 1: DermLIP-PanDerm (VLM)
- Source: `hf-hub:redlessone/DermLIP_PanDerm-base-w-PubMed-256`
- Role: Zero-shot + multimodal classification
- Output: logits (6 or 7 classes), embedding (768-d), quality score
- Use zero-shot template: "This is a skin image of {class_name}"

### Model 2: PanDerm Encoder (Foundation Vision)
- Source: github.com/SiyuanYan1/PanDerm (use the encoder only)
- Role: Strong visual feature extraction
- Output: visual features (768-d), fine-tuned logits
- Freeze early layers, fine-tune last 2 stages

### Model 3: Swin-Tiny (Pure Vision)
- Source: `timm.create_model('swin_tiny_patch4_window7_224', pretrained=True, num_classes=0)`
- Role: Fine-tuned pure vision backbone
- Two separate instances: one for clinical images, one for dermoscopy images (NOT shared weights)
- Training: Freeze backbone for 5 epochs, train head. Then unfreeze last 2 stages, fine-tune at 0.1x LR.
- Output: 768-d embedding, class logits
- CRITICAL FIX: Use `num_classes=0` to get pre-head embeddings. For Grad-CAM, target last attention block before head.

### Model 4: ResNet152 (Pure Vision)
- Source: `timm.create_model('resnet152.a2_in1k', pretrained=True)`
- Role: CNN inductive bias for diversity
- Output: 2048-d embedding, class logits
- Fine-tune similarly to Swin-Tiny

### VisionReport Output
```python
{
    "model_predictions": {
        "dermlip_panderm": Tensor[K],
        "panderm": Tensor[K],
        "swin_tiny_clinical": Tensor[K],
        "swin_tiny_dermoscopy": Tensor[K],
        "resnet152": Tensor[K]
    },
    "model_embeddings": {
        "dermlip_panderm": Tensor[768],
        "panderm": Tensor[768],
        "swin_tiny_clinical": Tensor[768],
        "swin_tiny_dermoscopy": Tensor[768],
        "resnet152": Tensor[2048]
    },
    "model_confidences": Dict[str, float],
    "uncertainty_estimates": Dict[str, float],  # entropy
    "quality_scores": Dict[str, float]  # per-image
}
```

### Per-Image Quality
- blur_score = variance of Laplacian (cv2.Laplacian)
- brightness, contrast = image statistics
- resolution_ratio = actual_res / expected_res
- occlusion_score = fraction below saliency threshold
- Q_image = MLP([blur, brightness, contrast, resolution_ratio, occlusion])

---

## PART 3: SCRIBE AGENT (src/agents/scribe.py)

### Model
- `emilyalsentzer/Bio_ClinicalBERT` (NOT bert-base-uncased)
- Mean-pool last hidden state → 768-d embedding

### Symptom Extraction
Three fixed structured-output prompts (JSON schema, temperature=0):
1. **Extraction**: raw text → {duration, growth, color_change, itching, pain, bleeding: true|false|unknown}
   - System prompt: "If a symptom is not mentioned, output unknown. Never output false for something not stated."
2. **Question generation**: {missing_field, expected_value} → natural language question
3. **Report generation**: {prediction, uncertainty, evidence_used, evidence_missing, conflicts, sufficiency_verdict} → short paragraph

### PTIS (Patient Text Informativeness Score)
- v1 (heuristic): weighted combination of word count, symptom keywords, temporal info, location info, specificity ratio. Min-max scaled on training set.
- v2 (validated): 100+ samples scored 0-3 by 3 raters. Compute ICC (not just Cohen's kappa). Fit regression (heuristic features → mean human score). Use output as final PTIS.

### ScribeReport Output
```python
{
    "symptoms": Dict[str, str],
    "ptis": float,  # [0,1]
    "risk_factors": List[str],
    "summary": str,
    "text_embedding": Tensor[768],
    "metadata_embedding": Tensor[64],
    "metadata_quality": float
}
```

---

## PART 4: DEVIL'S ADVOCATE / EVIDENCE PROFILER (src/agents/devils_advocate.py)

This is the safety layer. Implement `DevilsAdvocateAgent` with these exact computations:

### Quality (Q)
```python
Q_image = MLP([blur_score, brightness, contrast, resolution_ratio, occlusion_score])
Q_text = PTIS
Q_meta = 1 - fraction_of_fields_missing
```
Each Q_m ∈ [0,1]

### Reliability (R)
```python
R_m = sigmoid(MLP([Q_m, H_m, S_m, A_m]))
  H_m = predictive_entropy of single-modality branch
  S_m = 1 - variance_of_prediction_under_TTA(5_augmentations)
  A_m = mean_cosine_similarity_between_modality_m_prediction_and_all_others
```
MLP: 4 inputs → 8 hidden → 1 output. Trained jointly.

### Utility (U) — RETROSPECTIVE ONLY
```python
for each case x and modality m:
    pred_all = model(x, all_modalities)
    pred_without_m = model(x, all_modalities - {m})
    U_m(x) = Loss(pred_without_m, y) - Loss(pred_all, y)
```
CRITICAL: U requires ground truth y. It is ONLY for research analysis, NOT used in deployed inference. For deployment, approximate U from training-set statistics.

### Consistency (C)
```python
C(x) = 1 - mean_pairwise_JS_divergence(p_i, p_j) for all pairs of available modalities
Conflict_flag(x) = True if C(x) < 0.3
```

### Missingness (M)
```python
M = {clinical_avail, dermo_avail, meta_avail, text_avail}  # binary flags
```

### OOD Detection
```python
ood_score = min_k (z_fused - mu_k)^T Sigma_k^-1 (z_fused - mu_k)
```
Where mu_k, Sigma_k are class-conditional mean and covariance on TRAINING embeddings. Calibrate threshold on validation set.

### EvidenceProfile Output
```python
{
    "quality": Dict[str, float],
    "reliability": Dict[str, float],
    "utility": Dict[str, float],  # retrospective only
    "consistency": float,
    "conflict_flag": bool,
    "conflict_details": Dict,
    "missing_modalities": List[str],
    "ood_score": float,
    "overall_risk": float
}
```

---

## PART 5: DYNAMIC FUSION (src/fusion/adaptive_fusion.py)

### The Core Algorithm: Iterative EM-Style Refusion

```python
class DiagnosisAdaptiveFusion(nn.Module):
    def __init__(self, num_modalities, num_classes, d_embedding):
        self.f = MLP(4 inputs -> num_modalities)  # weight logit network
        self.W_prior = nn.Parameter(torch.randn(num_classes, num_modalities))
        self.alpha = nn.Parameter(torch.tensor(1.0))
        self.beta = nn.Parameter(torch.tensor(1.0))
        self.gamma = nn.Parameter(torch.tensor(0.5))
        self.classifier = nn.Linear(d_embedding, num_classes)
        
    def fuse(self, evidence, max_iterations=3, convergence_threshold=0.05):
        # evidence = {embeddings, quality, reliability, utility, consistency, missing_mask}
        
        # Iteration 0: No diagnosis prior
        w_logits = self.alpha * self.f(torch.stack([Q, R, U, C]))
        w = F.softmax(w_logits, dim=-1) * evidence["missing_mask"]
        w = w / w.sum(dim=-1, keepdim=True)  # renormalize
        z_fused = sum(w_m * z_m for m in available)
        pred = self.classifier(z_fused)
        diag = pred.argmax()
        
        # Iterations 1-3
        for k in range(max_iterations):
            # E-step: diagnosis-adaptive prior
            pi = self.W_prior[diag]  # [num_modalities]
            
            # M-step: update weights
            conflict_penalty = self.compute_conflict_penalty(evidence, diag)
            w_logits_new = (self.alpha * self.f(torch.stack([Q, R, U, C])) 
                           + self.beta * pi 
                           + self.gamma * torch.log(conflict_penalty + 1e-8))
            
            w_new = F.softmax(w_logits_new, dim=-1) * evidence["missing_mask"]
            w_new = w_new / w_new.sum(dim=-1, keepdim=True)
            
            z_fused_new = sum(w_new_m * z_m)
            pred_new = self.classifier(z_fused_new)
            diag_new = pred_new.argmax()
            
            # Convergence check
            if diag_new == diag and torch.max(torch.abs(w_new - w)) < convergence_threshold:
                break
                
            w, z_fused, pred, diag = w_new, z_fused_new, pred_new, diag_new
        
        return {
            "prediction": pred,
            "diagnosis": diag,
            "weights": w,
            "iterations_used": k + 1,
            "converged": k < max_iterations - 1 or (diag_new == diag and torch.max(torch.abs(w_new - w)) < convergence_threshold)
        }
```

### CRITICAL FIXES (from audit)
1. **Missing modality masking**: Always multiply softmax weights by binary mask, then renormalize. If all modalities missing, raise INSUFFICIENT_EVIDENCE before fusion (do not divide by zero).
2. **Class imbalance**: Use Focal Loss (gamma=2.0) + class weights: weight_c = N / (n_classes * n_c)
3. **Gradient clipping**: `torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)` — essential for transformer fine-tuning
4. **Mixed precision**: Use `torch.cuda.amp` autocast for all training
5. **Early stopping**: On validation macro-F1 (NOT loss), patience=10. Save best + last checkpoint. Load best for test evaluation.

---

## PART 6: CONSENSUS HIERARCHY (src/fusion/consensus.py)

Replace conformal prediction with this 4-level hierarchy:

```python
def classify_consensus(fused_prediction, evidence_profile, vision_reports):
    model_preds = vision_reports["model_predictions"]
    confidences = vision_reports["model_confidences"]
    fusion_confidence = fused_prediction["confidence"]  # max(softmax)
    C = evidence_profile["consistency"]
    Q = evidence_profile["quality"]
    
    # Count agreements
    top1_predictions = {name: logits.argmax().item() for name, logits in model_preds.items()}
    diag_counts = Counter(top1_predictions.values())
    max_agreement = max(diag_counts.values())
    majority_diag = diag_counts.most_common(1)[0][0]
    
    if (max_agreement >= 3 
        and fusion_confidence >= 0.80 
        and min(Q.values()) >= 0.30
        and not evidence_profile["conflict_flag"]):
        return {
            "level": 1,
            "action": "ACCEPT",
            "diagnosis": majority_diag,
            "confidence": fusion_confidence
        }
    
    elif (max_agreement == 2 
          and fusion_confidence >= 0.50
          and not evidence_profile["conflict_flag"]):
        # Evidence-based arbitration
        weighted_votes = {}
        for name, diag in top1_predictions.items():
            score = evidence_profile["quality"].get(name, 0.5) * evidence_profile["reliability"].get(name, 0.5)
            weighted_votes[diag] = weighted_votes.get(diag, 0) + score
        
        best_diag = max(weighted_votes, key=weighted_votes.get)
        return {
            "level": 2,
            "action": "ARBITRATE",
            "diagnosis": best_diag,
            "confidence": fusion_confidence
        }
    
    elif (max_agreement <= 1 
          or fusion_confidence < 0.50 
          or min(Q.values()) < 0.30):
        if evidence_profile["conflict_flag"] and C < 0.3:
            return {
                "level": 4,
                "action": "ESCALATE",
                "reason": "Critical conflict detected"
            }
        else:
            return {
                "level": 3,
                "action": "ACQUIRE",
                "reason": "High uncertainty"
            }
    
    else:
        return {
            "level": 4,
            "action": "ESCALATE",
            "reason": "Unresolvable disagreement"
        }
```

---

## PART 7: ACQUISITION POLICY (src/fusion/acquisition.py)

```python
class AcquisitionPolicy:
    def __init__(self):
        # Use gradient-boosted regression (XGBoost or LightGBM) instead of raw lookup table
        # Train on validation data to predict uncertainty reduction
        self.model = GradientBoostingRegressor()
        
    def select_action(self, case_features, available_modalities):
        # case_features: {current_entropy, missing_fields, metadata_completeness, ptis, ood_score}
        candidates = [m for m in ALL_MODALITIES if m not in available_modalities]
        candidates += ["ask_growth", "ask_bleeding", "ask_color_change", "ask_duration"]
        
        best_action = None
        best_value = -inf
        
        for action in candidates:
            expected_uncertainty_reduction = self.model.predict([
                self.encode_features(case_features, action)
            ])[0]
            cost = self.get_cost(action)  # image > dermoscopy > question
            value = expected_uncertainty_reduction / cost
            
            if value > best_value:
                best_value = value
                best_action = action
        
        return best_action
```

---

## PART 8: VERIFICATION LAYER (src/llm/verification.py)

### Two-Stage Verification

**Stage 1 (Pre-Orchestrator):**
```python
def stage1_verify(evidence_profile):
    if evidence_profile["ood_score"] > OOD_THRESHOLD:
        return FAIL("Out-of-distribution case")
    if evidence_profile["conflict_flag"] and evidence_profile["consistency"] < 0.3:
        return FAIL("Critical cross-modal conflict")
    if sum(evidence_profile["missing_modalities"]) == len(ALL_MODALITIES):
        return FAIL("No evidence available")
    if any(q < 0.2 for q in evidence_profile["quality"].values()):
        # Suppress low-quality modalities (do not fail, just warn)
        pass
    return PASS
```

**Stage 2 (Post-Orchestrator):**
```python
def stage2_verify(report_draft, evidence_json):
    rules = [
        "Does the diagnosis appear in ANY model's top-3 predictions?",
        "Does the confidence match the consensus level?",
        "Is every claim in the report traceable to a field in evidence_json?",
        "Does the report mention a diagnosis not supported by evidence?",
        "If sufficiency is insufficient, does the report state a confident diagnosis?"
    ]
    
    # Rule-based first
    for rule in rules:
        if not check_rule(report_draft, evidence_json, rule):
            return FAIL(rule)
    
    # LLM-based second (structured prompt, temperature=0)
    llm_result = llm_verify(report_draft, evidence_json)
    if llm_result["status"] == "fail":
        return FAIL(llm_result["reason"])
    
    return PASS
```

If Stage 2 fails: regenerate report with conservative prompt ("State only what is directly supported by the evidence below"). If still failing, ESCALATE.

---

## PART 9: ORCHESTRATOR (src/agents/orchestrator.py)

```python
class OrchestratorAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.tools = {
            "vision_specialist": self.call_vision_team,
            "scribe": self.call_scribe,
            "librarian": self.call_librarian,
            "devils_advocate": self.call_evidence_profiler
        }
    
    def process_case(self, case: PatientCase):
        # Step 1: Parallel agent execution
        vision_report = self.tools["vision_specialist"](case.images)
        scribe_report = self.tools["scribe"](case.text, case.metadata)
        knowledge = self.tools["librarian"](case.query_embedding)
        evidence_check = self.tools["devils_advocate"](case, vision_report, scribe_report)
        
        # Step 2: Stage 1 verification
        v1 = stage1_verify(evidence_check)
        if v1.status == "FAIL":
            if v1.reason == "Out-of-distribution":
                return ESCALATE(v1.reason)
            elif v1.reason == "Critical cross-modal conflict":
                return ACQUIRE("Resolve conflict")
            elif v1.reason == "No evidence available":
                return ABSTAIN(v1.reason)
        
        # Step 3: Dynamic fusion
        fusion_result = self.fusion.fuse(evidence_bundle)
        
        # Step 4: Consensus
        consensus = classify_consensus(fusion_result, evidence_check, vision_report)
        
        if consensus["action"] == "ACQUIRE":
            target = self.acquisition.select_action(case_features, case.available_modalities)
            return {"action": "ACQUIRE", "target": target, "evidence_trace": trace}
        
        if consensus["action"] == "ESCALATE":
            return {"action": "ESCALATE", "reason": consensus["reason"], "evidence_trace": trace}
        
        # Step 5: Report generation
        report_draft = self.llm.generate(
            synthesis_prompt(
                vision=vision_report,
                scribe=scribe_report,
                knowledge=knowledge,
                evidence=evidence_check,
                consensus=consensus
            ),
            temperature=0.0,
            max_tokens=512
        )
        
        # Step 6: Stage 2 verification
        v2 = stage2_verify(report_draft, evidence_json)
        if v2.status == "FAIL":
            report_draft = self.llm.generate(conservative_prompt, temperature=0.0, max_tokens=512)
            v2_retry = stage2_verify(report_draft, evidence_json)
            if v2_retry.status == "FAIL":
                return ESCALATE("Verification failed")
        
        # Step 7: Log and return
        result = {
            "diagnosis": consensus["diagnosis"],
            "confidence": consensus["confidence"],
            "consensus_level": consensus["level"],
            "evidence_used": [...],
            "evidence_missing": [...],
            "report": report_draft,
            "evidence_trace": trace
        }
        self.save_to_db(result)
        return result
```

**CRITICAL CONSTRAINT:** The Orchestrator MUST use structured tool-calling, NOT free-text reasoning for diagnosis. The LLM synthesizes reports but does not independently diagnose.

---

## PART 10: RAG / SIMILAR-CASE RETRIEVAL (src/retrieval/)

### CRITICAL FIX (from audit): No Chicken-and-Egg
- Index the **concatenation of individual modality embeddings** [z_clinical, z_dermo, z_meta] from training cases
- At inference, concatenate the test case's individual embeddings and search
- NEVER index fused embeddings (circular)

```python
class RAGIndex:
    def __init__(self):
        self.index = faiss.IndexFlatIP(total_dim)  # inner product = cosine if normalized
    
    def add_training_cases(self, cases):
        for case in cases:
            emb = torch.cat([
                case["clinical_embedding"],
                case["dermoscopy_embedding"],
                case["metadata_embedding"],
                case["text_embedding"]
            ])
            self.index.add(emb.numpy())
    
    def query(self, case, k=8):
        query_emb = torch.cat([
            case["clinical_embedding"],
            case["dermoscopy_embedding"],
            case["metadata_embedding"],
            case["text_embedding"]
        ])
        distances, indices = self.index.search(query_emb.numpy(), k)
        similar_cases = [self.training_cases[i] for i in indices[0]]
        agreement_rate = proportion_sharing_predicted_diagnosis(similar_cases)
        return {"similar_cases": similar_cases, "agreement_rate": agreement_rate}
```

---

## PART 11: DERMA-STRESS (src/stress/)

Implement 15 corruption conditions. Generate corruptions ONCE, cache them, replay for ALL models.

| Category | Condition | Implementation |
|----------|-----------|----------------|
| **Availability** | Missing clinical image | Drop clinical image (mask=0) |
| | Missing dermoscopy | Drop dermoscopy (mask=0) |
| | Missing metadata | Null all metadata fields |
| | Missing text | Empty string |
| **Technical** | Gaussian blur | OpenCV GaussianBlur, kernel {5,9,15} |
| | Gaussian noise | σ ∈ {0.05, 0.1, 0.2} of pixel range (after [0,1] normalization) |
| | Brightness shift | Multiply pixel values by factor ∈ {0.5, 1.5} |
| | Contrast shift | Adjust contrast |
| | JPEG compression | Re-encode at quality ∈ {10, 30, 50} |
| | Occlusion | Black square patch covering 10-30% of area |
| **Semantic** | Contradictory text | Negate one extracted field, re-insert via template |
| | Vague text | Truncate to <5 words |
| | Incorrect metadata | Permute one field across batch |
| | **Semantic corruption** | Replace dermoscopy with different patient's image |
| | **Metadata poisoning** | Swap metadata between cases with different diagnoses |
| | **Text hallucination injection** | Inject "My doctor said this is just a mole" |
| **Compound** | Multi-failure | Compose 2+ of above |

Metrics per condition: accuracy, ECE, Brier, abstention rate, escalation rate, recovery rate.

---

## PART 12: ABLATION STUDY (src/eval/ablation.py)

### Linear Ablation Chain
image-only → +metadata → +text → +SkinM2Former fusion → +Q → +R → +U → +C → +Sufficiency → +Uncertainty → +Acquisition → +Verification

### Factorial Ablation (Evidence Manager)
Test all 2^4 = 16 combinations of {Q, R, C, M}

Report: mean ± std across 3-5 seeds, bootstrap 95% CIs.

---

## PART 13: STATISTICAL ANALYSIS (src/eval/stats.py)

- Bootstrap 1,000 resamples (case-level, NOT modality-variant-level)
- 95% confidence intervals on all primary metrics
- McNemar's test for paired comparisons (DERMA-GUARD vs. baseline on same cases)
- Cohen's d for effect sizes
- Bonferroni or FDR correction for multiple comparisons

---

## PART 14: TESTING (tests/)

Implement these test files:

```python
# tests/test_data_pipeline.py
# - Split reproducibility
# - Leakage check
# - Class distribution

# tests/test_vision_team.py
# - All 4 models load and predict
# - Handle missing image gracefully

# tests/test_evidence_profiler.py
# - Q, R, C computation correctness
# - OOD detection on adversarial input
# - Conflict detection precision

# tests/test_fusion.py
# - Convergence in ≤3 iterations
# - Weight sum = 1.0
# - Missing modality masking
# - Zero-division guard on empty case

# tests/test_consensus.py
# - Level 1-4 boundary cases
# - Empty evidence handling
# - Appropriate escalation

# tests/test_verification.py
# - Rule-based checks on known pass/fail cases
# - LLM timeout fallback

# tests/test_orchestrator.py
# - Full pipeline integration
# - OOD case → escalation
# - Missing modality → acquisition
```

Coverage target: ≥70%

---

## PART 15: STREAMLIT DEMO (app/)

### Patient App (app/patient_app.py)
- Upload form: drag-and-drop images, text area, metadata form
- Status view: track case with evidence timeline
- Results view: final report (if not escalated)

### Clinician Console (app/clinician_console.py)
- Case queue: pending HUMAN_REVIEW cases
- Evidence trace viewer: expandable timeline of all agent actions
- Approve/Reject buttons + comment field

---

## PART 16: DOCUMENTATION REQUIREMENTS

Create these files in `docs/`:

1. `limitations.md` — Must include:
   - Synthetic text ≠ real text
   - Acquisition is simulated only
   - Conformal coverage replaced by consensus hierarchy (population-level guarantee no longer applies)
   - Results are retrospective, not clinically validated
   - Single-GPU training constraints

2. `repro_statement.md` — Exact seeds, config hashes, dataset hashes, hardware info

3. `what_did_not_work.md` — MANDATORY section. If metadata utility is near zero, if Librarian adds no value, if iterative fusion doesn't improve over 2 iterations, if acquisition policy is no better than random — REPORT IT. This strengthens credibility.

---

## PART 17: IMPLEMENTATION ORDER

Implement in THIS exact order:

1. **Week 1:** Data pipeline + audit + frozen splits + baseline ladder (6 baselines)
2. **Week 2:** Vision Team (load all 4 models, parallel inference) + Scribe (ClinicalBERT, PTIS v1)
3. **Week 3:** Devil's Advocate (Q, R, C, M, OOD) + synthetic text generation for PAD-UFES-20
4. **Week 4:** Dynamic Fusion (iterative EM) + 4-level consensus + acquisition policy
5. **Week 5:** Two-stage verification + Orchestrator + RAG (individual embeddings)
6. **Week 6:** DERMA-STRESS (all 15 conditions) + run on all model variants
7. **Week 7:** Ablation studies (linear + factorial) + bootstrap CIs + statistical tests
8. **Week 8:** Streamlit demo + error analysis + "What Did Not Work" + paper draft

---

## PART 18: CRITICAL RULES & CONSTRAINTS

1. NEVER use DermFM-Zero (weights are private). Use DermLIP-PanDerm instead.
2. NEVER regenerate Derm7pt splits. Use official files.
3. NEVER use fused embeddings for RAG. Use individual modality concatenation.
4. NEVER compute utility U at inference time. It requires ground truth. Use training statistics for deployment.
5. NEVER let the Orchestrator do free-text diagnosis. Tool-calling only.
6. ALWAYS mask missing modalities and renormalize. Guard against all-missing (division by zero).
7. ALWAYS use gradient clipping (max_norm=1.0) and mixed precision for training.
8. ALWAYS early stop on validation macro-F1, not loss.
9. ALWAYS report per-class metrics, not just macro.
10. ALWAYS include "What Did Not Work" in final documentation.
11. ALWAYS use Bio_ClinicalBERT, not bert-base-uncased.
12. ALWAYS use patient-level split for PAD-UFES-20.
13. ALWAYS validate synthetic text with regex leakage check.
14. ALWAYS log model version (git commit + config hash) with every prediction.
15. ALWAYS put a 30-second timeout, 2 retries, and conservative fallback on every LLM call.

---

## WHAT I NEED FROM YOU

Implement the complete DERMA-GUARD v4.0 system following the architecture, algorithms, and specifications above. Start with the repository structure and data pipeline, then build each component in the specified order. Provide complete, runnable Python code for every module. Include docstrings, type hints, and comments explaining non-obvious decisions. Make sure all the audit fixes are implemented correctly. The final system should be able to:
1. Process a multimodal case through the full pipeline
2. Run DERMA-STRESS benchmark
3. Produce ablation study results
4. Launch the Streamlit demo

Begin implementation now.
```

---

**This prompt is fully self-contained.** Claude will have everything needed: the architecture, the algorithms, the exact model names, the configuration, the file structure, the implementation order, the critical fixes, and the testing requirements.
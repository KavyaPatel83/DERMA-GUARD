# HealthSphere-Derm — Project Context Document
> **Last Updated**: 2026-07-27  
> **Status**: ✅ Completed & Verified  
> **Purpose**: Living reference document for all project context, decisions, and progress

---

## 1. Project Identity

| Field | Value |
|-------|-------|
| **Title** | HealthSphere-Derm: Quality-Gated Multimodal Fusion with Conformal Safety for Patient-Authored Skin Lesion Malignancy Detection |
| **Type** | B.Tech Capstone Research Project |
| **Target Venues** | IEEE JBHI, npj Digital Medicine, MICCAI Workshop |
| **Cost Constraint** | $0.00 — NO paid APIs, NO cloud costs, open dataset only |
| **Task** | Binary malignancy detection (Malignant vs Benign) |
| **Dataset** | PAD-UFES-20 (2,298 images, 26 metadata columns, CC BY 4.0) |

---

## 2. Implementation Status Summary

All 4 phases of the implementation plan have been completed and verified:

### Phase 1: Critical Bug Fixes & Spec Compliance
- ✅ Removed all paid xAI/Grok API keys from `configs/default.yaml` and source code.
- ✅ Replaced all `wandb` calls with local **TensorBoard** (`torch.utils.tensorboard.SummaryWriter`).
- ✅ Fixed method call bug in `src/reports/verifier.py` (`self._ask_ollama()` → `self._ask_llm()`).
- ✅ Fixed class import mismatch in `scripts/02_generate_texts.py` (`OllamaParaphraser`).
- ✅ Updated `requirements.txt` to remove `wandb` and include `tensorboard`, `flask`, `requests`.

### Phase 2: Backend Completion
- ✅ Implemented complete `create_dataloaders()` in `src/data/dataset.py` with image fallbacks, text merging, PTIS feature extraction, and custom collate logic.
- ✅ Overhauled `scripts/04_train_models.py` with TensorBoard logging, real dataloaders, mixed precision (`torch.amp`), and full checkpoint saving.
- ✅ Fully implemented `scripts/05_conformal_calibrate.py` for validation nonconformity scoring and test set coverage evaluation.
- ✅ Fully implemented `scripts/06_evaluate.py` for computing balanced accuracy, macro F1, AUROC, per-class sensitivity/specificity, and saving ROC curves.
- ✅ Fully implemented `scripts/07_generate_reports.py` integrating readability FKGL calculation, ReportGenerator, ReportVerifier, and ClarityAgent.
- ✅ Fully implemented `scripts/08_analysis.py` for generating 300 DPI publication plots (ROC curves, PTIS distribution, model comparison, conformal set sizes).

### Phase 3: Web Dashboard (Flask UI/UX)
- ✅ Enhanced `app.py` with `/api/ptis/score`, `/api/results`, and multimodal image+text analysis in `/api/analyze`.
- ✅ Redesigned `templates/analyze.html` with drag-and-drop image upload, patient text input for multimodal context, PTIS quality gate indicator, conformal prediction set visualization, FAISS evidence retrieval gallery, and adaptive patient report output.
- ✅ Updated `templates/pipeline.html` to integrate cleanly with style.css and main.js pipeline functions.
- ✅ Updated `templates/reports.html` with dynamic class support table, conformal metrics, benchmark table, and interactive Chart.js AUROC comparison chart.

### Phase 4: Verification & Directory Setup
- ✅ Created all output directories: `outputs/checkpoints`, `outputs/results`, `outputs/figures`, `outputs/reports`, `outputs/conformal`, `outputs/logs`.
- ✅ Updated `README.md` with TensorBoard instructions and Web Dashboard setup.

---

## 3. Architecture Overview

### Six Model Configurations

| Model | Modalities | Fusion | Purpose |
|-------|-----------|--------|---------|
| **A** | Image only | — | Vision baseline |
| **B** | Metadata only | MLP | Metadata baseline |
| **C** | Text only | BERT | Text baseline |
| **D** | Image + Metadata | MetaBlock (Pacheco 2021) | Literature SOTA baseline |
| **E** | Image + Text | **Quality-Gated (PTIS)** | **MAIN CONTRIBUTION** |
| **F** | Image + Meta + Text | MMF-Net Two-Stage | Full ablation |

### Model E Quality Gate (Main Innovation)
```
PTIS Score → Routing Decision:
├── PTIS < 0.3 (Low)    → Image-only pathway: z_fused = z_img
├── 0.3 ≤ PTIS ≤ 0.7    → Uncertainty-weighted: w_img*z_img + w_text*z_text
└── PTIS > 0.7 (High)   → Full cross-attention fusion (MMF-Net style)

Training: Soft gating (differentiable sigmoid blending)
Inference: Hard thresholds (discrete, interpretable routing)
```

---

## 4. Key Technical Guidelines & Rules Enforced

1. **$0.00 Cost Constraint**: All LLM functionality (paraphrasing, report generation, verification) uses local Ollama (`llama3`) HTTP endpoints with robust rule-based/template fallbacks. No external paid APIs are called.
2. **Local Experiment Tracking**: TensorBoard is used exclusively instead of `wandb`.
3. **Loss Function**: FocalLoss (γ=2.0) with inverse-frequency class weights.
4. **Data Splitting**: GroupShuffleSplit by `patient_id` to prevent patient-level data leakage across train/val/test splits.
5. **Reproducibility**: Global seed `42` set across Python `random`, `numpy`, and `torch`.

---

## 5. Change Log

### 2026-07-27 — Full Completion Audit
- Verified all 17 audit items from the implementation plan.
- All backend scripts 01–08 are end-to-end runnable.
- Dashboard endpoints and templates fully functional.
- Output directory tree generated and confirmed.

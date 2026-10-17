# DERMA-GUARD v4.0 — Complete Running Guide

## Quick Reference: Script Execution Order

```
01_prepare_data.py → 02_generate_texts.py → dataset_audit.py →
04_train_baselines.py → train_derma_guard.py → run_stress.py → 08_analysis.py
```

---

## 1. Environment Setup

### 1.1 Install Dependencies
```powershell
pip install -r requirements.txt
```

### 1.2 Configure Environment Variables
```powershell
# Copy the example env file
Copy-Item .env.example .env

# Edit .env and fill in:
# WANDB_API_KEY=your_key_here     (optional — only needed with --run-wandb)
# HF_HOME=models/pretrained       (cache HuggingFace weights locally)
```

### 1.3 Start Ollama with Qwen2.5:7b
```powershell
# Pull the model (one-time)
ollama pull qwen2.5:7b

# Verify it runs
ollama run qwen2.5:7b "Hello"
```

### 1.4 Windows-specific fix (already embedded in all scripts)
All scripts have `os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"` at the top.

---

## 2. Where to Put Datasets

### 2.1 Derm7pt Dataset
```
data/
└── raw/
    └── derm7pt/
        ├── images/            ← All Derm7pt images (clinical + dermoscopy)
        └── meta/              ← Official CSV/JSON split files (NEVER modify)
```

**Download**: https://derm.cs.sfu.ca/7point.html  
**Important**: Use the official train/val/test split. Never regenerate it.  
413 train / 203 val / 395 test (1,011 total cases)

### 2.2 PAD-UFES-20 Dataset
```
data/
└── raw/
    └── pad_ufes/
        ├── images/            ← 2,298 smartphone images
        └── metadata.csv       ← Official PAD-UFES-20 metadata
```

**Download**: https://data.mendeley.com/datasets/zr7vgbcyr2/1

### 2.3 Pretrained Model Weights
```
models/
└── pretrained/                ← Set HF_HOME=models/pretrained in .env
    ├── dermlip_panderm/       ← Auto-downloaded on first run
    ├── bio_clinicalbert/      ← Auto-downloaded on first run
    └── panderm/               ← Download from github.com/SiyuanYan1/PanDerm
```

---

## 3. Phase-by-Phase Execution

### Phase 1: Data Preparation (Run Once)

**Step 1.1 — Prepare PAD-UFES-20 splits**
```powershell
python scripts/01_prepare_data.py
# Creates: data/splits/padufes_{train,val,test}.json
# NEVER delete these splits — they must be reproducible (seed=42)
```

**Step 1.2 — Generate synthetic patient text (PAD-UFES-20 only)**
```powershell
# Full generation with Qwen2.5:7b (requires Ollama running)
python scripts/02_generate_texts.py

# With custom paths:
python scripts/02_generate_texts.py \
    --input data/raw/pad_ufes/metadata.csv \
    --output data/interim/pad_ufes_synthetic_text.json

# Dry run (no Ollama, uses rule-based fallback):
python scripts/02_generate_texts.py --dry-run
```
Output: `data/interim/pad_ufes_synthetic_text.json`  
Format: `[{"case_id": ..., "text": ..., "source_fields": {...}, "quality_flags": {...}}]`

**Step 1.3 — Dataset audit (MUST pass before training)**
```powershell
python scripts/dataset_audit.py
# Checks: SHA-256 hashes, perceptual hash collisions, class distribution
# Outputs: dataset_report.json, outputs/plots/missingness.png, class_distribution.png
# BLOCKS TRAINING if dirty data detected
```

---

### Phase 2: Baseline Ladder Training (B1–B6)

Train baselines in order. Each writes a checkpoint to `outputs/checkpoints/baselines/`.

```powershell
# B1: ResNet152 (image-only) on Derm7pt
python scripts/04_train_baselines.py --baseline B1 --dataset derm7pt --epochs 50

# B2: Swin-Tiny (image-only) on Derm7pt
python scripts/04_train_baselines.py --baseline B2 --dataset derm7pt --epochs 50

# B3: Late Fusion (requires Derm7pt paired loader)
python scripts/04_train_baselines.py --baseline B3 --dataset derm7pt --epochs 50

# B4: Multimodal Concat (requires text+meta features)
python scripts/04_train_baselines.py --baseline B4 --dataset derm7pt --epochs 50

# B5: PanDerm fine-tuned
python scripts/04_train_baselines.py --baseline B5 --dataset derm7pt --epochs 50

# B6: Ensemble Majority Vote (requires B1, B2, B5 trained first — no training needed)
python scripts/04_train_baselines.py --baseline B6 --dataset derm7pt

# Or train all at once:
python scripts/04_train_baselines.py --baseline all --dataset derm7pt
```

---

### Phase 3: DERMA-GUARD Full System Training

```powershell
# Train DiagnosisAdaptiveFusion, Evidence Profiler, PTIS v2, OOD detector, Acquisition Policy
python scripts/train_derma_guard.py --epochs 100 --batch-size 32 --lr 1e-4

# With W&B tracking:
python scripts/train_derma_guard.py --epochs 100 --run-wandb

# With ablation study after training:
python scripts/train_derma_guard.py --epochs 100 --run-ablation

# With DERMA-STRESS after training:
python scripts/train_derma_guard.py --epochs 100 --run-stress
```

Trained weights are saved to:
- `outputs/checkpoints/fusion_best.pt`
- `outputs/checkpoints/reliability_mlp.pt`
- `outputs/checkpoints/ptis_v2.pt`
- `models/ood/ood_detector.pkl`
- `models/acquisition/acquisition_policy.pkl`
- `models/rag/rag_index.index`

---

### Phase 4: Evaluation on Clean Test Set

```powershell
# Evaluate all models (baselines + full DERMA-GUARD)
python scripts/06_evaluate.py --split test

# Evaluate only baselines
python scripts/06_evaluate.py --split test --baselines-only

# Generate clinical reports for all test cases
python scripts/07_generate_reports.py --split test
```

---

### Phase 5: DERMA-STRESS Benchmark (15 Conditions)

```powershell
# Run all 15 conditions on full DERMA-GUARD
python scripts/run_stress.py --model-variant full --dataset derm7pt

# Run all 15 conditions on a specific baseline (for comparison)
python scripts/run_stress.py --model-variant b1 --dataset derm7pt

# Run a single condition:
python scripts/run_stress.py --condition missing_clinical

# Run all variants and all conditions:
for variant in full b1 b2 b5 b6:
    python scripts/run_stress.py --model-variant $variant
```

The 15 conditions:
| # | Category | Condition |
|---|----------|-----------|
| 1 | Availability | Missing clinical image |
| 2 | Availability | Missing dermoscopy |
| 3 | Availability | Missing metadata |
| 4 | Availability | Missing text |
| 5 | Technical | Gaussian blur (mild) |
| 6 | Technical | Gaussian blur (severe) |
| 7 | Technical | Gaussian noise |
| 8 | Technical | Brightness shift |
| 9 | Technical | JPEG compression |
| 10 | Technical | Occlusion patch |
| 11 | Semantic | Contradictory text |
| 12 | Semantic | Vague text |
| 13 | Semantic | Permuted metadata |
| 14 | Semantic | Dermoscopy image swap |
| 15 | Semantic | Metadata poisoning |
| 16 | Compound | Multi-failure combination |

---

### Phase 6: Ablation Study & Statistical Analysis

```powershell
# Linear ablation chain
python scripts/08_analysis.py --mode linear_ablation --seeds 42 43 44

# Factorial ablation 2^4 (Q, R, C, M)
python scripts/08_analysis.py --mode factorial_ablation

# Statistical tests (Bootstrap CIs, McNemar's, Cohen's d, FDR correction)
python scripts/08_analysis.py --mode stats --reference derma_guard

# Full analysis pipeline:
python scripts/08_analysis.py --mode all
```

---

### Phase 7: Application Launch

```powershell
# Terminal 1: FastAPI Backend API
python src/main.py
# → Available at http://localhost:8000
# → API docs at http://localhost:8000/docs

# Terminal 2: Patient Upload App
streamlit run app/patient_app.py --server.port 8501

# Terminal 3: Clinician Review Console
streamlit run app/clinician_console.py --server.port 8502
```

---

## 4. Paper Comparisons & Expected Results

### 4.1 Papers We Compare Against

| Paper | Year | Method | Dataset | Key Result |
|-------|------|--------|---------|------------|
| **SkinM2Former** (Zhang et al.) | 2025 | Tri-modal cross-attention ViT | Derm7pt, HAM10000 | ~83% acc, ~0.89 AUC — **Primary Baseline M** |
| **DermFormer** (Cockayne et al.) | 2025 | Nested ViT + entropy weighting | Derm7pt, ISIC | ~80% acc — Stress baseline |
| **PanDerm** (Yan et al.) | 2025 | 1.5M image foundation model | PAD-UFES, Derm7pt | Macro-F1 ~0.74 (PAD-UFES) — used as Model 2 in ensemble |
| **DermLIP** (Xin et al.) | 2025 | VLP on Derm1M | Multiple | ~0.89 AUC — used as Model 1 in ensemble |
| **MetaBlock-SE** (Bouzon et al.) | 2025 | Metadata attention fusion | PAD-UFES-20 | ~79% acc |
| **Watson et al.** | 2026 | Text + dermoscopy fusion | PAD-UFES-20 | Text adds ~3% over image-only |

### 4.2 Internal Baseline Ladder Expected Results

| Baseline | Architecture | Expected Val Macro-F1 |
|----------|-------------|----------------------|
| B1: ResNet152 (img-only) | ImageNet pretrained | ~0.65–0.70 |
| B2: Swin-Tiny (img-only) | ImageNet pretrained | ~0.70–0.74 |
| B3: Late Fusion | Dual ResNet152, avg logits | ~0.74–0.78 |
| B4: Multimodal Concat | Features + linear | ~0.76–0.80 |
| B5: PanDerm Fine-tuned | Foundation encoder | ~0.78–0.82 |
| B6: Ensemble Majority | Vote B1+B2+B5 | ~0.80–0.84 |
| **DERMA-GUARD (full)** | **Full system** | **≥0.80 clean, safer under stress** |

### 4.3 Primary Safety Claims We Must Demonstrate

| Metric | Clean Data Target | Under DERMA-STRESS |
|--------|------------------|-------------------|
| Unsafe-Decision Rate | ≤2% | ≤5% |
| Abstention Rate | 5–10% | 15–25% |
| Conflict Detection Precision | ≥85% | ≥80% |
| Acquisition Recovery Rate | ≥75% | ≥70% |
| Report Hallucination Rate | ≤2% | ≤3% |
| ECE (calibration) | ≤0.08 | ≤0.10 |

**The key claim**: DERMA-GUARD degrades *gracefully* under stress while baselines like SkinM2Former degrade sharply — because our Devil's Advocate detects bad evidence and abstains rather than forcing a wrong confident prediction.

---

## 5. Common Issues & Fixes

| Error | Fix |
|-------|-----|
| `OMP: Error #15` | Already fixed — all scripts set `KMP_DUPLICATE_LIB_OK=TRUE` |
| `Ollama not running` | Start Ollama service: `ollama serve` |
| `CUDA out of memory` | Reduce batch size: `--batch-size 8` |
| `Splits file not found` | Run `01_prepare_data.py` first |
| `timm not installed` | `pip install timm` |
| `faiss not installed` | `pip install faiss-cpu` |
| HuggingFace download fails | Set `HF_HOME=models/pretrained` and check internet |

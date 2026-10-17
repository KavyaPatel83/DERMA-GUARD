# Reproducibility Statement — DERMA-GUARD v4.0

## Random Seeds

| Component | Seed |
|-----------|------|
| Data splits (PAD-UFES-20 patient-level) | 42 |
| All model training | 42 |
| Bootstrap CI resampling | 42 |
| Ablation multi-seed runs | {42, 43, 44} |

## Dataset Integrity

Fill in after running `scripts/dataset_audit.py`:

| Dataset | SHA-256 Manifest | pHash Collision Count |
|---------|-----------------|----------------------|
| PAD-UFES-20 | TBD | TBD |
| Derm7pt | TBD | TBD |

Manifest saved to: `outputs/audit/dataset_report.json`

## Split Files (Committed)

| Split | File | SHA-256 |
|-------|------|---------|
| PAD-UFES train | `data/splits/padufes_train.json` | TBD |
| PAD-UFES val | `data/splits/padufes_val.json` | TBD |
| PAD-UFES test | `data/splits/padufes_test.json` | TBD |
| Derm7pt train | Official index file (not regenerated) | N/A |
| Derm7pt val | Official index file | N/A |
| Derm7pt test | Official index file | N/A |

## Config Hash

Fill in before each experiment run:
```bash
python -c "
import hashlib, json
with open('configs/base.yaml') as f:
    content = f.read()
print('Config SHA256:', hashlib.sha256(content.encode()).hexdigest()[:16])
"
```

## Git Commit
Every model prediction logs the git commit hash automatically:
```python
import subprocess
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
```

## Hardware

| Item | Value |
|------|-------|
| OS | Windows 11 / Linux TBD |
| GPU | TBD (e.g., NVIDIA RTX 4090 24GB) |
| CUDA | TBD |
| PyTorch | ≥2.0.0 |
| Python | 3.13.9 (Anaconda) |

## Environment Pinning

```bash
pip freeze > requirements-lock.txt
```
Committed as `requirements-lock.txt` for exact reproduction.

## Model Checkpoint Hashes

Fill in after training:
| Model | Filename | SHA-256 |
|-------|----------|---------|
| Swin-Tiny (clinical) | `models/finetuned/swin_tiny_clinical_best.pt` | TBD |
| Swin-Tiny (dermo) | `models/finetuned/swin_tiny_dermo_best.pt` | TBD |
| ResNet-152 | `models/finetuned/resnet152_best.pt` | TBD |
| PanDerm fine-tuned | `models/finetuned/panderm_finetuned_best.pt` | TBD |
| Fusion | `models/finetuned/fusion_best.pt` | TBD |

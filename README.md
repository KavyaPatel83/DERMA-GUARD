# DERMA-GUARD v4.0

> **Agentic Evidence-Management Framework for Reliable Multimodal Dermatological Diagnosis**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![Research Only](https://img.shields.io/badge/status-research%20only-red.svg)]()

> ⚠️ **This is a research prototype. NOT clinically validated. Do NOT use for medical diagnosis.**

---

## Web portal (DERMA-GUARD)

One command serves the API **and** the hospital website:

```bash
python src/main.py          # http://127.0.0.1:8000   (API docs: /api/docs)
```

First start creates `outputs/portal/hospital.db` and writes demo logins (random passwords) to
`outputs/portal/DEMO_CREDENTIALS.txt`. Models and the knowledge base load in the background (~40 s).

| Area | Code |
|------|------|
| Routes, `/api/v1` contract, legacy `/predict` `/case` `/metrics` | `src/main.py` |
| Auth (scrypt, HttpOnly sessions, lockout, CSRF header, RBAC), SQLite, scheduling | `src/services/auth.py`, `db.py`, `scheduling.py` |
| Inference wrapper, calibration, triage, morphology, acquisition | `src/services/inference.py` |
| Multi-agent layer (intake, safety, retrieval, referral, report, chat) | `src/services/care_agents.py` |
| RAG (MiniLM dense + TF-IDF, similar cases) over `docs/knowledge_base/` | `src/services/knowledge_base.py` |
| Honest held-out evaluation, conformal, risk-coverage, subgroups | `src/services/honest_eval.py` |
| Explanation audit, DERMA-STRESS runner | `src/services/explain_audit.py`, `stress_runner.py` |
| Front-end (white theme, vanilla JS) | `app/static/` |
| Tests | `tests/test_portal_services.py` |

Roles: **patient** (self-registers with name + email, no password), **doctor** and **admin** (seeded accounts).
The top bar has a **Patient / Doctor / Admin switch** for patient sessions, so one person can submit a case and then
review it as a doctor. Doctors see every case in the hospital and record the final decision; admins see accounts,
audit log and aggregate statistics, never clinical content. The password sign-in API (`/api/auth/login`) is kept
for scripts and the staff demo accounts, but the web UI has no sign-in page.

> **Demo-mode trade-off:** passwordless registration and role switching are deliberate conveniences for demonstrating
> the patient and doctor views. They are not suitable for real patient data; before real use, restore password
> sign-in and remove `/api/auth/join` and `/api/auth/switch`.

Each result also shows **AI-agent scores** (how well each of the six agents did its job) next to the **model scores**
(confidence and held-out accuracy), and the RAG panel shows the retrieved look-alike patients' images.

> **Read `docs/evaluation_audit.md`.** The benchmark figures produced by `Dummy/Project/train_all.py`
> (85-90 % accuracy) are not held-out measurements: the "test" set is contained in the training set and the
> evaluation routine adjusts probabilities to hit target accuracies. On rows never used for training the models
> score roughly 61-65 % (image-based) and 78 % (metadata-only). The portal reports the measured numbers.

## Architecture

```
OrchestratorAgent
├── VisionSpecialistTeam (DermLIP-PanDerm · PanDerm · Swin-Tiny × 2 · ResNet-152)
├── ScribeAgent          (Bio_ClinicalBERT · PTIS v1+v2)
├── LibrarianAgent       (FAISS RAG · modality-concat embeddings)
├── DevilsAdvocateAgent  (Q · R · U · C · M · OOD-Mahalanobis)
└── DiagnosisAdaptiveFusion (EM-style · 3 iterations)
    └── ConsensusHierarchy  (Level 1-4: ACCEPT / ARBITRATE / ACQUIRE / ESCALATE)
        ├── AcquisitionPolicy (GradientBoosting · value = Δuncertainty / cost)
        ├── Stage 1 Verification (pre-fusion gating)
        └── Stage 2 Verification (rule + LLM · conservative fallback)
```

## Setup

### Prerequisites
- Python 3.10+
- CUDA GPU (recommended, CPU fallback available)
- [Ollama](https://ollama.ai) with `qwen2.5:7b`

### Installation

```bash
# Clone / navigate to the project
cd HealthSphere

# Install dependencies
pip install -e ".[dev]"

# Pull the LLM model
ollama pull qwen2.5:7b
```

### Data Preparation

```bash
# 1. Audit datasets
python scripts/dataset_audit.py

# 2. Prepare PAD-UFES-20 / ISIC splits
python scripts/01_prepare_data.py

# 3. Train the full system
python scripts/train_derma_guard.py \
    --data-dir data \
    --output-dir outputs \
    --epochs 50 \
    --batch-size 32
```

## Running

### API Server

```bash
python src/main.py
# or
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Visit: `http://localhost:8000/api/docs`

### Streamlit Apps

```bash
# Patient portal (port 8501)
streamlit run app/patient_app.py

# Clinician dashboard (port 8502)
streamlit run app/clinician_app.py --server.port 8502
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## DERMA-STRESS Benchmark

```bash
python -c "
from src.stress.benchmark import StressBenchmark
# bench = StressBenchmark(pipeline=your_pipeline)
# bench.run(cases=test_cases)
print('DERMA-STRESS benchmark ready')
"
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Text encoder | Bio_ClinicalBERT | Clinical domain (NOT bert-base-uncased) |
| LLM | qwen2.5:7b via Ollama | Local inference, no external API |
| Foundation model | DermLIP-PanDerm | Per spec (NOT DermFM-Zero — private weights) |
| Fusion | EM-style iterative (3 iter) | Converges in ≤3 iterations per spec |
| Loss | FocalLoss γ=2.0 + class weights | Class imbalance in skin datasets |
| Gradient clip | max_norm=1.0 | Training stability |
| Early stopping | val macro-F1, patience=10 | NOT on loss |
| RAG index | Modality concat (NOT fused) | Avoids circular dependency |
| OOD detection | Mahalanobis distance | Class-conditional, calibrated |

## Pipeline Steps (7-step)

1. **Parallel agent execution** — Vision, Scribe, Librarian, Devil's Advocate run concurrently
2. **Stage 1 verification** — Pre-fusion gating (OOD, conflict, empty evidence)
3. **Dynamic fusion** — EM-style DiagnosisAdaptiveFusion with evidence weights
4. **Consensus classification** — 4-level hierarchy: ACCEPT → ARBITRATE → ACQUIRE → ESCALATE
5. **Report generation** — LLM synthesis (qwen2.5:7b, T=0)
6. **Stage 2 verification** — Rule + LLM check; conservative fallback if failed
7. **Return result** — Structured PipelineResult with evidence trace

## Directory Structure

```
HealthSphere/
├── src/
│   ├── agents/           # OrchestratorAgent, VisionTeam, Scribe, Librarian, DA
│   ├── fusion/           # DiagnosisAdaptiveFusion, consensus, acquisition
│   ├── evidence/         # Q, R, U, C, M computation
│   ├── llm/              # Ollama client, prompts, verification, report gen
│   ├── retrieval/        # FAISS RAG index
│   ├── data/             # Derm7pt loader
│   ├── stress/           # DERMA-STRESS: 15 corruption conditions
│   ├── eval/             # Metrics, stats, ablation
│   └── main.py           # FastAPI backend
├── app/
│   ├── patient_app.py    # Streamlit patient portal
│   └── clinician_app.py  # Streamlit clinician dashboard
├── tests/                # pytest test suite
├── scripts/              # Training, data prep, audit
├── configs/              # Hydra configs (base, model, data)
├── Dockerfile
├── pyproject.toml
└── requirements.txt
```

## Citation

If you use this work, please cite the original DERMA-GUARD specification.

---

**Research System Only** — Not for clinical use. Always consult a qualified dermatologist.

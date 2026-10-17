# 13 — Technology Stack and Why Each Was Chosen

Guiding constraints: **(1) $0 cost** — no paid APIs or cloud; **(2) runs on one laptop**; **(3) medical-AI honesty and
auditability**; **(4) reproducible**.

## 1. Stack at a glance

| Layer | Technology | Where |
|-------|-----------|-------|
| Language | Python 3.10+ | everywhere |
| Deep learning | PyTorch ≥ 2.0, torchvision, timm | `Dummy/Project/models`, `src/agents` |
| Language models | Hugging Face Transformers (Bio_ClinicalBERT, MiniLM), optional Ollama `qwen2.5:7b` | text encoder, RAG, LLM |
| Classical ML | scikit-learn, SciPy, NumPy, pandas | stacking, OOD, acquisition, stats |
| Retrieval | TF-IDF + MiniLM + Reciprocal Rank Fusion; FAISS (research) | `knowledge_base.py`, `rag_index.py` |
| Image processing | OpenCV, Pillow, albumentations, imagehash | quality, GrabCut, augmentation, dedupe |
| API / web | FastAPI, Uvicorn, Pydantic, python-multipart | `src/main.py` |
| Storage | SQLite (WAL) + local files | `db.py`, `outputs/portal` |
| Front-end | HTML, CSS, vanilla JS; Streamlit + Plotly (secondary) | `app/` |
| Config | Hydra + OmegaConf, YAML | `configs/` |
| Tracking | TensorBoard (final), W&B / MLflow (specified, removed from the active path) | `outputs/logs` |
| Testing / quality | pytest, pytest-cov, black, isort, flake8, mypy | `tests/`, `pyproject.toml` |
| Packaging | Dockerfile (python:3.10-slim), `pyproject.toml`, `requirements.txt` | root |
| Docs / papers | Markdown, LaTeX (IEEE), Overleaf bundles | `docs/` |

## 2. "Why this and not that" — decision table

### 2.1 Modelling

| Decision | Chosen | Alternatives considered | Why chosen |
|----------|--------|-------------------------|-----------|
| Image backbone (live) | **ResNet50**, frozen, + small attention head | EfficientNet, ViT-B/16, Swin, fine-tuning end-to-end | 2.3 k images → full fine-tuning overfits; frozen ImageNet features can be **cached once** so training seven models takes minutes on a laptop |
| Image backbone (research) | DermLIP-PanDerm, PanDerm, Swin-Tiny, ResNet152 | single model | Diversity (VLM + foundation + transformer + CNN) makes disagreement an informative safety signal |
| Text encoder | **Bio_ClinicalBERT** | bert-base-uncased, BioBERT, GPT embeddings | Pre-trained on clinical notes → better clinical phrasing; local, free; spec explicitly forbids bert-base-uncased |
| Metadata encoder | Residual MLP (MetaBlock-style) / TabTransformer | XGBoost only, plain MLP | Small tabular vector; residual MLP is stable; TabTransformer implemented as alternative; tree ensembles added in the stacking layer |
| Fusion | **Evidence-aware gated fusion** | Concatenation, simple average, cross-attention (SkinM2Former) | Needs per-case trust, graceful missing modalities, interpretability of weights |
| Fusion refinement | EM-style, diagnosis-adaptive (≤ 3 iterations) | Single pass | Lets the working diagnosis change which modality is trusted; converges quickly |
| Loss | **Focal loss (γ = 2) + class weights + label smoothing 0.02** | Plain cross-entropy | Strong class imbalance (MEL 2 %) |
| Ensemble | Calibrated stacking with residual blend (α ≥ 0) | Plain averaging | Cannot do worse than the neural anchor on validation |
| OOD | **Mahalanobis** (class-conditional) | Softmax-max, ODIN, energy | Cheap, no retraining, works on embeddings |
| Calibration | **Temperature scaling** | Platt, isotonic, none | One parameter → robust on small data; does not change ranking |
| Uncertainty sets | **Split conformal** | Bayesian NN, MC-dropout, ensembles | Distribution-free finite-sample coverage; trivial to implement and audit |
| Decision logic | Rule-based 4-level hierarchy | Learned policy | Transparent, clinically reviewable, no extra labels needed |
| Acquisition | Greedy utility − cost − delay (portal); GradientBoosting (research) | RL policy | Not enough data to learn an RL policy; honest labelling of heuristic vs. measured gains |
| Segmentation | **GrabCut** | U-Net | No pixel masks in the dataset; classical method needs no labels |

### 2.2 Retrieval and language

| Decision | Chosen | Why |
|----------|--------|-----|
| RAG retrieval | Hybrid MiniLM dense + TF-IDF with **RRF** | Dense catches paraphrase, sparse catches exact clinical terms; small corpus doesn't justify a vector DB |
| Vector DB | In-memory NumPy / FAISS-CPU | Corpus is tiny; no server needed |
| LLM | **Qwen2.5-7B via Ollama**, optional | Local, free, private (no patient text leaves the machine); system must work without it |
| LLM role | Rephrase grounded facts only | Prevents hallucinated diagnoses; verified in Stage-2 |

### 2.3 Engineering

| Decision | Chosen | Alternatives | Why |
|----------|--------|--------------|-----|
| Web framework | **FastAPI** | Flask, Django | Type-validated request models, auto OpenAPI docs, async friendly, easy to serve static files |
| Server | Uvicorn | Gunicorn | ASGI, one command, reload for dev |
| Database | **SQLite (WAL)** | PostgreSQL, MongoDB | Zero setup, single file, transactions, adequate for a demo; documented upgrade path |
| Password hashing | `hashlib.scrypt` | bcrypt/argon2 | Standard library, memory-hard, no extra dependency |
| Sessions | Random token, SHA-256 stored, HttpOnly cookie | JWT | Revocable server-side, nothing sensitive in the browser, simpler to reason about |
| CSRF | Custom header + SameSite=Lax | CSRF tokens | Simple, effective for a same-origin SPA-like site |
| Front-end | Vanilla JS | React/Vue | No build step, minimal surface, easy for reviewers to read |
| Streamlit | Secondary dashboards | — | Fast to build clinician/patient prototypes against the API |
| Config | Hydra/OmegaConf | argparse, JSON | Composable experiment configs (baseline ladder, ablations) |
| Experiment tracking | **TensorBoard** | W&B, MLflow | Local, free, no account; W&B was removed to honour the $0/no-cloud constraint |
| Containerisation | Docker | Conda env only | Reproducible deployment of the API |

### 2.4 Process

| Decision | Why |
|----------|-----|
| Patient-grouped splits (`GroupShuffleSplit`) | Prevents patient leakage — the main source of inflated skin-AI results |
| Global seed 42 | Reproducibility; multi-seed {42,43,44} for ablations |
| Bootstrap CIs with patient clustering | Small data → honest uncertainty |
| "What did not work" document | Negative results strengthen credibility |
| Honest re-evaluation module in the product | Trust is a product feature, not just a paper section |

## 3. Dependencies (`requirements.txt`)

`torch, torchvision, timm, transformers, accelerate, huggingface_hub, faiss-cpu, hydra-core, omegaconf, wandb, mlflow,
fastapi, uvicorn[standard], streamlit, pillow, opencv-python, albumentations, scikit-learn, scipy, numpy, pandas,
matplotlib, seaborn, plotly, pytest, pytest-cov, black, isort, flake8, mypy, structlog, python-multipart, httpx,
requests, imagehash, tensorboard`.

Notes: `wandb`/`mlflow` remain listed because the spec named them, but the active training path logs to TensorBoard.
The portal's RAG additionally needs `sentence-transformers/all-MiniLM-L6-v2` weights available locally (loaded with
`local_files_only=True`; otherwise it falls back to TF-IDF).

## 4. Pretrained assets and licences

| Asset | Source | Use |
|-------|--------|-----|
| ResNet50 / ResNet152 / Swin-Tiny | ImageNet (timm / torchvision) | Vision backbones |
| Bio_ClinicalBERT | `emilyalsentzer/Bio_ClinicalBERT` | Text |
| all-MiniLM-L6-v2 | `sentence-transformers` | RAG dense retrieval |
| DermLIP-PanDerm | `hf-hub:redlessone/DermLIP_PanDerm-base-w-PubMed-256` | Research vision team |
| PanDerm | github.com/SiyuanYan1/PanDerm | Research vision team |
| Qwen2.5-7B-Instruct | Ollama | Optional report/chat rewriting |
| PAD-UFES-20 | Mendeley Data, CC BY 4.0 | Data |

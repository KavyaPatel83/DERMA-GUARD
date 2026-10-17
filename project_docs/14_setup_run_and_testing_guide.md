# 14 — Setup, Running, Training and Testing Guide

## 1. Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python | 3.10 or newer |
| OS | Developed on Windows 11; Linux/macOS fine (set `KMP_DUPLICATE_LIB_OK=TRUE` on Anaconda/Windows if OpenMP errors appear) |
| GPU | Optional — CUDA GPU recommended for training; CPU works for the portal |
| Ollama | **Optional** — only for LLM-written summaries/chat (`ollama pull qwen2.5:7b`) |
| Disk | The repository contains the dataset images (~2.3 k PNG ×2–4 copies) and model weights |

## 2. Install

```bash
cd "Healthsphere_1"
python -m venv .venv
.venv\Scripts\activate            # Windows   (source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
```

> The README suggests `pip install -e ".[dev]"`. `pyproject.toml` declares no `dev` extra and a non-standard build
> backend string, so **use `requirements.txt`** (above) unless you fix `pyproject.toml`.

Environment variables (`.env`, copy of `.env.example`): `HF_HOME`, `OLLAMA_HOST`, `OLLAMA_MODEL`, `DATA_DIR`,
`OUTPUT_DIR`, `SEED`, `BATCH_SIZE`, `EPOCHS`, `LR`, `KMP_DUPLICATE_LIB_OK`. W&B/MLflow entries are placeholders and are
not required.

## 3. Run the website (the main way to use the project)

```bash
python src/main.py                 # → http://127.0.0.1:8000
# or
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

What happens on first start:
1. `outputs/portal/hospital.db` is created.
2. Demo accounts are seeded; random passwords are written to `outputs/portal/DEMO_CREDENTIALS.txt`.
3. Models load in the background (~40 s). Until `GET /api/status` shows `state: ready`, analysis returns 503.
4. The knowledge base and similar-case indexes build in the background.
5. If `outputs/portal/honest_eval.json` is missing, it is computed from the saved weights (takes a while).

Open `http://127.0.0.1:8000` → **Register** (name + email) → **Diagnose** → analyse a sample or upload your own.
Use the top-bar role switch to review your case as a doctor.

API documentation: `http://127.0.0.1:8000/api/docs`.

### Optional: local LLM
```bash
ollama serve
ollama pull qwen2.5:7b
```
The portal detects it automatically (status page shows `llm.available`).

## 4. Streamlit apps (against the legacy API)

```bash
streamlit run app/patient_app.py --server.port 8501
streamlit run app/clinician_console.py --server.port 8502
```

## 5. Data and training

### 5.1 Prototype models A–G (what the website uses)
```bash
cd Dummy/Project
python train_all.py              # caches features, trains projection heads + models A..G, writes saved_models/
python generate_all_confusion_matrices.py
python demo_predict.py           # sample inference
python predict.py                # command-line predictor
```
Then regenerate the honest evaluation and calibration:
```bash
python -m src.services.honest_eval        # from the repository root; rewrites outputs/portal/honest_eval.json
```

> Remember: the *printed* metrics of `train_all.py` are not valid held-out estimates (see `11_...`). Use the honest
> evaluation output.

### 5.2 Research pipeline (v4.0 spec)
```bash
python scripts/dataset_audit.py                      # hashes + perceptual-hash collisions + reports
python scripts/01_prepare_data.py                    # patient-level 70/15/15 splits (seed 42)
python scripts/02_generate_texts.py                  # synthetic text (Ollama paraphraser + templates)
python scripts/04_train_baselines.py --config configs/experiment/baseline_ladder/b1_resnet.yaml   # b1..b6
python scripts/train_derma_guard.py --data-dir data --output-dir outputs --epochs 50 --batch-size 32
python scripts/06_evaluate.py                        # metrics, ROC
python scripts/07_generate_reports.py                # reports + readability
python scripts/08_analysis.py                        # ablations, stats, figures
python scripts/run_stress.py --output-dir outputs/stress
```
Script names in some docs differ (`04_train_models.py`, `03_train_ptis.py`, `05_conformal_calibrate.py`); the files that
exist in `scripts/` are: `01_prepare_data.py`, `02_generate_texts.py`, `04_train_baselines.py`, `06_evaluate.py`,
`07_generate_reports.py`, `08_analysis.py`, `dataset_audit.py`, `run_stress.py`, `train_derma_guard.py`.

## 6. Tests

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
pytest tests/test_portal_services.py -v     # website services only
```
`.pytest_cache/` at the root contains the last-run state (including any previously failing tests listed in
`lastfailed`).

## 7. Docker

```bash
docker build -t derma-guard .
docker run -p 8000:8000 derma-guard
```
The `Dockerfile` copies only `src/`, `configs/` and `data/` and runs `uvicorn src.main:app`. Because the live engine
imports `Dummy/Project` and the portal reads `app/static`, `docs/` and `outputs/`, **extend the Dockerfile to copy
those directories** (and the saved weights) before expecting the full website to work in a container.

## 8. Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `503 Models are still loading` | Wait ~40 s; check `/api/status` |
| `state: error` in status | Missing weights in `Dummy/Project/saved_models` or missing ResNet/BERT downloads; read `error` text |
| RAG "keyword (TF-IDF); dense unavailable" | MiniLM weights not cached locally; download once with network access |
| OpenMP / MKL duplicate-lib crash on Windows | `set KMP_DUPLICATE_LIB_OK=TRUE` |
| 429 "Too many pending cases" | Limit is 5 pending reviews per user — have a doctor review or delete cases |
| Can't sign in with password for a self-registered patient | Passwordless accounts have no password by design |
| Ollama unavailable | System still works; summaries use templates |
| Port in use | Change the port in `src/main.py` or pass `--port` to uvicorn |

## 9. Demo walkthrough (for a presentation)

1. Open the site → **Register** as a patient.
2. **Diagnose** → pick a *sample* (e.g. a melanoma) or upload a photo; add age, site, symptoms.
3. Show the **image-quality check**, then **Analyse**.
4. Walk the result: diagnosis → triage banner → conformal set → evidence bars → candidate models → agents → RAG
   look-alikes → referral → report.
5. Click **Request review**, switch role to **Doctor**, open the case, record the final decision, switch back.
6. Open **Evidence & performance** to show *measured vs. reported* accuracy and calibration.
7. Open **DERMA-STRESS** to show robustness under blur/noise/missing inputs.
8. Open **Lesion tracking** and simulate a follow-up to show change alerts.

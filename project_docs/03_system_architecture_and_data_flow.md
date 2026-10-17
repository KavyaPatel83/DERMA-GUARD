# 03 — System Architecture and Data Flow

This file explains **how every part of the project connects**, from the browser click to the database row.

## 1. Layered view

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  PRESENTATION      app/static/*.html + js/common.js, diagnose.js, result.js + css          │
│                    (vanilla HTML/CSS/JS, white theme, role-aware navigation)                │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  API / WEB SERVER  src/main.py  (FastAPI + Uvicorn)                                         │
│                    /api/*  portal API   /api/v1/*  spec API   /predict /case  legacy         │
│                    security-headers middleware, input sanitisation, RBAC dependencies       │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  SERVICES          src/services/                                                             │
│   auth.py          scrypt, sessions, lockout, CSRF header, roles                            │
│   db.py            SQLite (users, sessions, cases, appointments, audit, lesions, chat…)     │
│   scheduling.py    appointment slot rules                                                   │
│   inference.py     Engine wrapper + calibration + triage + morphology + acquisition         │
│   care_agents.py   Orchestrator + Intake/Safety/Referral/Retrieval/Report/Chat agents       │
│   knowledge_base.py  RAG: hybrid MiniLM+TF-IDF over docs/knowledge_base + similar cases     │
│   honest_eval.py   Held-out re-evaluation, temperature, conformal, risk-coverage, subgroups │
│   explain_audit.py Occlusion-based explanation audit                                        │
│   stress_runner.py DERMA-STRESS against the live models                                     │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  MODEL ENGINE      Dummy/Project/predict.py  (DermaGuardPredictor)                           │
│   models/          encoders.py, evidence_manager.py, adaptive_fusion.py,                    │
│                    stacking_ensemble.py, conformal_prediction.py                            │
│   data/            preprocessing.py (116 features), text_generator.py (text + PTIS)         │
│   saved_models/    model_A … model_G weights, preprocessor.pkl, img_proj.pt, text_proj.pt,  │
│                    conformal_calibrator.pt, cached_multimodal_features.pt                   │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  STORAGE           outputs/portal/hospital.db, uploads/, thumbs/, kb_embeddings.npz,        │
│                    honest_eval.json     data/raw/images + metadata.csv                      │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Process view — one server, background loaders

`python src/main.py` starts **one** Uvicorn process. On start-up (`lifespan` in `src/main.py`):

1. `db.init()` creates/migrates the SQLite schema.
2. `auth.seed_demo()` creates demo doctor/admin/patient accounts and writes random passwords to
   `outputs/portal/DEMO_CREDENTIALS.txt` on first run only.
3. `engine.start()` loads the PyTorch models in a **background thread** (state: `loading → ready | error`).
4. A second background thread builds the RAG indexes (`kb.build()`, `similar.build(metadata.csv)`).

While loading, the API answers `503 Models are still loading`. The engine never fabricates predictions: if loading fails
it reports an error state.

## 3. End-to-end request flow (patient submits a case)

```
Browser (diagnose.html + diagnose.js)
   │  POST /api/analyze   multipart: image?, metadata JSON?, text?, auto_text?, model?
   ▼
src/main.py  analyze()  ──► _open_image()   size ≤10 MB, magic-byte check, decode, 32–4096 px
   │                    ──► _parse_metadata() keep only 17 allowed fields, clean values
   ▼
_run_case()  guards: engine ready? at least one input? ≤5 pending cases? model has needed inputs?
   ▼
care_agents.Orchestrator.analyze()
   ├─ IntakeAgent        free text → structured fields (regex NER), merged into metadata
   ├─ SafetyAgent        scan text for emergency wording
   ├─ Vision-Triage      Engine.predict()  ──► Dummy/Project/predict.py  DermaGuardPredictor.predict()
   │        │               1 ingest & choose model A–G    2 encode (ResNet50+MHSA / MetaBlock / ClinicalBERT)
   │        │               3 evidence Q,R,U,C,S,M         4 run all feasible candidate models
   │        │               5 gated fusion + prior refine  6 conformal set
   │        └─► inference.enrich()  temperature scaling → calibrated conformal set → 4-level triage
   ├─ SafetyAgent        guardrails on the model output
   ├─ RetrievalAgent     RAG chunks (knowledge base) + similar documented patients
   ├─ ReferralAgent      department / urgency / window
   ├─ ReportAgent        patient + clinician summary with citations (LLM only if reachable)
   └─ score_agents()     0–1 process-quality score per agent + combined assurance index
   ▼
main._run_case()  saves thumbnail, computes morphology (GrabCut), acquisition plan,
                  INSERT INTO cases(...), writes audit row
   ▼
JSON response ──► result.js renders: diagnosis, probabilities, conformal set, evidence bars,
                  agent trace + scores, RAG panel, referral, report, acquisition suggestions
```

## 4. How the components depend on each other

| Component | Depends on | Provides to |
|-----------|------------|-------------|
| `predict.py` (engine) | saved weights, `preprocessor.pkl`, ResNet50 weights, Bio_ClinicalBERT | `inference.Engine` |
| `inference.py` | engine, `honest_eval` results (temperature, q̂, measured accuracies) | `care_agents`, `main` |
| `honest_eval.py` | trained weights + cached features + `metadata.csv` | calibration for `inference`, **Evidence** page |
| `knowledge_base.py` | `docs/knowledge_base/*.md`, `docs/limitations.md`, `docs/what_did_not_work.md`, `metadata.csv` | RetrievalAgent, ChatAgent |
| `care_agents.py` | `inference`, `knowledge_base`, `db`, `scheduling`, optional Ollama | `main` |
| `auth.py` / `db.py` | SQLite | every protected route |
| Front-end | `/api/*` | the user |

## 5. Two ways the model layer can be reached

| Route | Pipeline | Notes |
|-------|----------|-------|
| `POST /api/analyze` (portal) | `care_agents.Orchestrator` → `inference.Engine` → `Dummy/Project/predict.py` | **The live website path.** Seven trained PAD-UFES-20 models, calibrated, with agents |
| `POST /predict`, `GET /case/{id}`, `GET /metrics` (legacy) | `src/agents/orchestrator.py` research pipeline | v4.0 specification pipeline (vision team + scribe + librarian + devil's advocate + EM fusion). Kept for the Streamlit apps and unit tests |
| `POST /api/v1/cases` etc. | Spec-style API contract wrappers | See `09_backend_api_database_and_security.md` |

## 6. The "research" v4.0 pipeline (for completeness)

```
OrchestratorAgent
├── VisionSpecialistTeam  (DermLIP-PanDerm · PanDerm · Swin-Tiny ×2 · ResNet-152)   [parallel]
├── ScribeAgent           (Bio_ClinicalBERT · PTIS v1/v2 · symptom extraction)
├── LibrarianAgent        (FAISS RAG over modality-concat embeddings)
├── DevilsAdvocateAgent   (Q · R · U · C · M · OOD-Mahalanobis → EvidenceProfile)
└── DiagnosisAdaptiveFusion (EM-style, ≤3 iterations, masked softmax)
    └── ConsensusHierarchy (L1 ACCEPT / L2 ARBITRATE / L3 ACQUIRE / L4 ESCALATE)
        ├── AcquisitionPolicy (GradientBoostingRegressor: Δuncertainty / cost)
        ├── Stage-1 verification (pre-fusion gate: OOD, conflict, empty evidence)
        └── Stage-2 verification (rule + LLM check of the report; conservative fallback)
```

Details in `12_research_pipeline_stress_and_paper.md`.

## 7. Design principles visible in the architecture

1. **Modular monolith.** One process, clear module boundaries; extraction into microservices is documented but not built
   (`docs/v5_extension_notes.md`).
2. **Fail soft.** Each agent runs inside `Trace.run()`; one agent failing does not take the case down — it scores 0 and
   shows in the trace.
3. **LLM optional.** Every agent has a deterministic path; the LLM only rewrites grounded evidence.
4. **Deterministic safety.** Emergency keywords, malignant-in-set rules, and triage thresholds are plain code, not model
   output.
5. **Measured, not claimed.** Calibration and displayed accuracies come from `honest_eval.json`, regenerated by code.

# 15 — Repository Map and File Guide

Root: `Healthsphere_1/`

```
Healthsphere_1/
├── README.md                    Project README (DERMA-GUARD v4.0, portal overview, architecture)
├── project_docs/                ← this documentation folder
├── project_context/PROJECT_CONTEXT.md   Earlier "HealthSphere-Derm" capstone status note (Flask/PTIS-era)
├── proj.md                      Original implementation specification prompt for DERMA-GUARD v4.0
├── det.md, detail.md            Long-form generated documentation drafts of the spec (2026-08-25)
├── requirements.txt, pyproject.toml, Dockerfile, .env, .env.example
│
├── src/                         Server + services + research framework
│   ├── main.py                  FastAPI app: portal API, /api/v1 contract, legacy endpoints, static site
│   ├── services/                (portal) auth, db, scheduling, inference, care_agents, knowledge_base,
│   │                            honest_eval, explain_audit, stress_runner
│   ├── agents/                  (research) orchestrator, vision_team, scribe, librarian, devils_advocate
│   ├── fusion/                  adaptive_fusion, consensus, acquisition
│   ├── evidence/                quality, reliability, utility, consistency, missingness
│   ├── llm/                     client, prompts, extraction, report_gen, verification
│   ├── retrieval/               rag_index (FAISS)
│   ├── data/                    dataset, derm7pt, preprocessing, splits, augmentation
│   ├── stress/                  corruption (18 conditions), benchmark
│   ├── eval/                    metrics, stats, ablation
│   ├── losses.py, utils.py
│   └── api/, config/, explain/, models/, repositories/   (package placeholders from the spec layout)
│
├── Dummy/Project/               The trained PAD-UFES-20 prototype engine (used live by the portal)
│   ├── train_all.py             Feature caching + training of models A–G (+ the flawed evaluator)
│   ├── predict.py               DermaGuardPredictor — the 6-step inference
│   ├── demo_predict.py, generate_all_confusion_matrices.py
│   ├── models/                  encoders, evidence_manager, adaptive_fusion, stacking_ensemble, conformal_prediction
│   ├── data/                    metadata.csv, images, preprocessing.py, text_generator.py, generated texts
│   ├── utils/                   metrics, plotting, terminal_display
│   ├── saved_models/            weights, projections, preprocessor, cached features, benchmark figures
│   ├── README.md, STEP_BY_STEP_GUIDE.md   Prototype documentation (note: contains the pre-audit numbers)
│   └── .git/                    Nested git repo of the prototype
│
├── app/
│   ├── static/                  Website: *.html, css/style.css, js/{common,diagnose,result}.js, img/benchmark_*.png
│   ├── patient_app.py           Streamlit patient app
│   └── clinician_console.py     Streamlit clinician dashboard
│
├── configs/                     Hydra YAML: base, default, data/, model/, experiment/baseline_ladder/
├── scripts/                     Data prep, training, evaluation, analysis, stress, audit
├── tests/                       pytest suite (7 files)
├── data/
│   ├── raw/                     images/, imgs_part_1..3/, metadata.csv   (PAD-UFES-20)
│   ├── processed/splits.json
│   ├── synthetic_texts.csv, templates/text_templates.json
│   └── interim/, splits/        (created by scripts)
├── models/                      ptis_scorer.pt, ptis_thresholds.json
├── outputs/
│   ├── checkpoints/best_model_A..E.pth
│   ├── logs/model_A..E/         TensorBoard event files
│   ├── portal/                  hospital.db, uploads/, thumbs/, kb_embeddings.npz, honest_eval.json, DEMO_CREDENTIALS.txt
│   └── conformal/, figures/, reports/, results/   (empty output folders)
├── docs/                        Knowledge base, audit, limitations, guides, papers (see 12_...)
├── experiments/, notebooks/     (empty placeholders)
└── .pytest_cache/
```

## Key files and their single responsibility

| File | Responsibility |
|------|----------------|
| `src/main.py` | Wire everything: routes, middleware, lifespan, RBAC dependencies, case workflow |
| `src/services/inference.py` | Engine wrapper, calibration (`enrich`), `triage`, `suggestions`, `image_quality`, `morphology`, `acquisition_plan`, sample building, growth simulation |
| `src/services/care_agents.py` | LLM client, Trace, Intake/Safety/Referral/Retrieval/Report agents, `score_agents`, Orchestrator, ChatAgent |
| `src/services/knowledge_base.py` | `KnowledgeBase` (hybrid RAG) and `SimilarCases` (k-NN) |
| `src/services/honest_eval.py` | Held-out evaluation, temperature, conformal, risk–coverage, subgroups, writes `honest_eval.json` |
| `src/services/auth.py` | Hashing, sessions, lockout, CSRF, role switching, demo seeding |
| `src/services/db.py` | SQLite connection helpers, schema, migration, audit |
| `src/services/scheduling.py` | Slot generation and validation |
| `src/services/explain_audit.py` | Occlusion explanation audit |
| `src/services/stress_runner.py` | Background DERMA-STRESS runs on live models |
| `Dummy/Project/predict.py` | End-to-end multimodal inference |
| `Dummy/Project/models/evidence_manager.py` | Q, R, U, C, S, M, E, weights, consensus level |
| `Dummy/Project/models/adaptive_fusion.py` | Gated fusion network + prior refinement |
| `Dummy/Project/models/stacking_ensemble.py` | Calibrated stacking |
| `Dummy/Project/models/conformal_prediction.py` | Original split conformal predictor |
| `Dummy/Project/data/text_generator.py` | Synthetic narratives and PTIS |
| `src/fusion/adaptive_fusion.py` | Research EM-style fusion with masking |
| `src/fusion/consensus.py` | Research 4-level hierarchy |
| `src/agents/orchestrator.py` | Research 7-step pipeline |
| `src/stress/corruption.py` | 18 DERMA-STRESS conditions |

## Which folder do I touch to…?

| Goal | Edit |
|------|------|
| Change what users see | `app/static/*.html`, `js/*.js`, `css/style.css` |
| Change triage thresholds | `src/services/inference.py::triage` |
| Add a new agent | `src/services/care_agents.py` (+ `score_agents`) |
| Add knowledge to RAG | Add `.md` to `docs/knowledge_base/` and delete `outputs/portal/kb_embeddings.npz` to rebuild |
| Change the clinical utility prior | `Dummy/Project/models/evidence_manager.py::DIAGNOSTIC_UTILITY_PRIOR` |
| Retrain models | `Dummy/Project/train_all.py` then `python -m src.services.honest_eval` |
| Add an API route | `src/main.py` |
| Add a stress condition | `src/stress/corruption.py` (+ `stress_runner.py`) |
| Change DB schema | `src/services/db.py::SCHEMA` / `_CASE_COLUMNS` |

## Naming caveat
The code base shows its history: *HealthSphere*, *HealthSphere-Derm*, *DERMA-GUARD v4.0*, *DERMA-GUARD v4.1/v5*. They
all refer to this same project; "DERMA-GUARD" is the current system name.

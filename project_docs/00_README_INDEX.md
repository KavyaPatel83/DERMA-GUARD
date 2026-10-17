# DERMA-GUARD / HealthSphere — Complete Project Documentation

> **Project name:** DERMA-GUARD (repository folder: `Healthsphere_1`, also called *HealthSphere-Derm*)
> **Full title:** *Agentic Evidence-Management Framework for Reliable Multimodal Dermatological Diagnosis*
> **Type:** B.Tech capstone / research prototype (VIT)
> **Status:** Research prototype — **not clinically validated, not for real medical use**

This folder is the single, organised explanation of the whole project: the idea, why it was chosen, what already exists,
how every part works, how the parts connect, which technologies were used and why, how to run it, and what is honestly
known to be weak. Each file has one purpose so you can read only what you need.

---

## 1. Reading order

| # | File | Purpose | Read it when you want to… |
|---|------|---------|---------------------------|
| 00 | `00_README_INDEX.md` | This index + 1-page summary | Get oriented |
| 01 | `01_project_overview_and_idea.md` | What the project is, the core idea, goals, contributions | Explain the project in a viva / presentation |
| 02 | `02_problem_existing_solutions_and_why_this_idea.md` | The problem, existing systems, gaps, why we chose this idea | Justify the topic selection |
| 03 | `03_system_architecture_and_data_flow.md` | Whole-system architecture and how every component connects | See the big picture and request flow |
| 04 | `04_dataset_and_data_pipeline.md` | PAD-UFES-20, metadata, synthetic text, splits, preprocessing | Understand the data |
| 05 | `05_machine_learning_models.md` | Models A–G, encoders, projection heads, training recipe | Understand the neural networks |
| 06 | `06_evidence_manager_fusion_and_consensus.md` | Q/R/U/C/S/M evidence, adaptive fusion, 4-level consensus | Understand the core novelty |
| 07 | `07_uncertainty_calibration_and_conformal.md` | Temperature scaling, conformal sets, triage, acquisition | Understand the safety maths |
| 08 | `08_multi_agent_layer_rag_and_llm.md` | The 6 care agents, RAG, chat, optional LLM | Understand the "agentic" part |
| 09 | `09_backend_api_database_and_security.md` | FastAPI, endpoints, SQLite schema, auth, RBAC | Understand the server |
| 10 | `10_frontend_web_portal.md` | The hospital website: pages, roles, UX flow | Understand the user interface |
| 11 | `11_evaluation_audit_and_results.md` | Reported vs. honest numbers, the audit, what was measured | Defend the results truthfully |
| 12 | `12_research_pipeline_stress_and_paper.md` | `src/` research code, DERMA-STRESS, ablations, the IEEE paper | Understand the research side |
| 13 | `13_technology_stack_and_why_chosen.md` | Every technology and why it was chosen over alternatives | Answer "why X instead of Y?" |
| 14 | `14_setup_run_and_testing_guide.md` | Install, run, train, test, Docker, troubleshooting | Run the project |
| 15 | `15_repository_map_and_file_guide.md` | Every folder/file and what it does | Find things in the code |
| 16 | `16_limitations_future_work_and_glossary.md` | Known problems, future work, glossary of terms | Be honest about limits, look up terms |

---

## 2. The project in one page

**Problem.** Most skin-lesion AI tools output a label with a confident-looking percentage whether the photo is sharp or
blurred, whether the patient history is complete or missing, and whether the image and the history contradict each other.
A confident wrong answer about a possible melanoma is dangerous.

**Idea.** Treat the AI like a careful *clinical panel* instead of a single classifier. For every case it:

1. Looks at **whatever evidence is available** — a lesion photo, patient details (age, body site, size, symptoms…),
   and/or a free-text description (any combination = 7 model configurations, **A–G**).
2. **Grades the evidence itself** — quality (Q), reliability (R), utility (U), cross-modal consistency (C),
   sufficiency (S) and missingness (M) — and uses those grades to weight each modality dynamically (*evidence-aware
   adaptive fusion*).
3. **Calibrates its uncertainty** — temperature scaling and split-conformal prediction sets give an honest
   "which classes remain plausible" answer.
4. **Chooses a safe action** with a 4-level consensus hierarchy: **ACCEPT → ARBITRATE → ACQUIRE → ESCALATE**
   (answer / ask a clinician to arbitrate / request more evidence / refer to a specialist).
5. **Wraps it in a care platform** — a hospital-style website with patient, doctor and admin roles, six cooperating
   "agents" (intake, safety, vision-triage, retrieval/RAG, referral, report), appointment booking, longitudinal lesion
   tracking, and an audit log.

**Dataset.** PAD-UFES-20 — 2,298 smartphone lesion photos with clinical metadata, 6 classes:
BCC, ACK, NEV, SEK, SCC, MEL (3 malignant, 1 pre-malignant, 2 benign).

**Honest headline result.** The original training script reported 84–90 % accuracy. The project's own audit
(`docs/evaluation_audit.md`) showed those numbers were **not** held-out measurements (the "test" set was inside the
training set and the evaluator adjusted probabilities toward target accuracies). Re-evaluated on rows never used for
training (n = 345), image-based models score ≈ 61–65 %, and the metadata-only model ≈ 78 %. The website shows the
*measured* numbers, not the original ones. This honesty is itself a design principle of the project.

**Run it.**

```bash
pip install -r requirements.txt
python src/main.py          # http://127.0.0.1:8000  (API docs at /api/docs)
```

---

## 3. Two "layers" of the repository (important to understand early)

The repository contains two cooperating code bases. Mixing them up is the most common source of confusion:

| Layer | Location | What it is | Used by the live website? |
|-------|----------|------------|---------------------------|
| **Trained prototype engine** | `Dummy/Project/` | The PAD-UFES-20 training script (`train_all.py`), the 7 trained models A–G, `predict.py`, evidence manager, adaptive fusion, conformal predictor, stacking ensemble, saved weights | **Yes** — `src/services/inference.py` imports `predict.py` from here |
| **Portal + services** | `src/main.py`, `src/services/`, `app/static/` | FastAPI server, auth, DB, RAG, agents, honest evaluation, calibration, triage, web UI | **Yes** — this *is* the website |
| **Research framework (v4.0 spec)** | `src/agents/`, `src/fusion/`, `src/evidence/`, `src/llm/`, `src/retrieval/`, `src/stress/`, `src/eval/`, `configs/`, `scripts/`, `tests/` | The full DERMA-GUARD v4.0 research architecture (vision team of DermLIP/PanDerm/Swin/ResNet152, Scribe, Librarian, Devil's Advocate, EM-style fusion, 4-level consensus, acquisition policy, 2-stage verification, DERMA-STRESS) with unit tests | **No** — a separately tested research pipeline (legacy `/predict` endpoints and Streamlit apps point at it) |

File `03_system_architecture_and_data_flow.md` explains exactly how these connect.

---

## 4. Safety statement

> This is a **research prototype**. It has **not** been clinically validated, has been tested only on a small public
> dataset, and must **never** be used to diagnose, treat, or delay seeking care for any real skin lesion. Always consult a
> qualified dermatologist.

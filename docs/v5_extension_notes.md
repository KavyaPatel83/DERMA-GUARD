# v5.0 extension notes

How the v5.0 blueprint maps onto the code in this repository, and what is deliberately **not** built.

## Implemented

| Blueprint module | Status | Where | Notes |
|------------------|--------|-------|-------|
| 1 · Lesion segmentation & morphology | Implemented (classical) | `src/services/inference.py::morphology` | GrabCut seeded from a central prior, smoothed boundary; area, perimeter, circularity, convexity, asymmetry (mirror IoU), colour variation, dominant colours, segmentation quality. Pixel units only. No learned U-Net yet, so no Dice/IoU figure exists. |
| 2 · Longitudinal tracking | Implemented on a **simulated** benchmark | `/api/lesions/*`, `app/static/lesions.html` | Real observations are user-linked cases; follow-ups can be *simulated* (magnification about the lesion centroid) and are labelled. No image registration; change alerts use a 25 % area threshold because a +60 % simulated change was recovered as median ×1.42 (IQR 1.20–1.55, range 0.80–1.86; large lesions that touch the frame are under-measured). |
| 3 · Clinical RAG | Implemented (small corpus) | `src/services/knowledge_base.py`, `docs/knowledge_base/` | Hybrid MiniLM dense + TF-IDF with reciprocal-rank fusion; separate similar-case retriever over the 2,298 documented records. No reranker, no external literature corpus; no claim-level verification beyond the source citation shown. |
| 4 · Conformal prediction + risk–coverage | Implemented | `src/services/honest_eval.py` | Split conformal on a patient-grouped half of the held-out rows; empirical coverage, set size, singleton rate, risk–coverage curves, ECE/Brier, temperature scaling. |
| 5 · Explanation auditor | Implemented (occlusion) | `src/services/explain_audit.py` | 4×4 occlusion sensitivity of the image-only model, lesion-overlap, stability under flips / brightness. Thresholds are provisional; no Grad-CAM or Integrated Gradients, no shortcut-injection study. |
| 6 · Cost-aware acquisition | Implemented (greedy rung) | `inference.py::acquisition_plan` | `ΔV − λ·cost − μ·delay`. ΔV for adding a modality is the *measured* held-out accuracy difference between model configurations; other actions use labelled heuristics. Not a learned policy. |
| 7 · Fairness / subgroups | Implemented (available labels) | Evidence page | Age, sex, body site, Fitzpatrick type; patient-level bootstrap CIs; groups under 30 flagged. Skin tone is never inferred from images. |
| 8 · DERMA-STRESS | Implemented against live models | `src/services/stress_runner.py`, `/api/v1/benchmarks/*` | Uses `src/stress/corruption.py`. 13 of the 18 listed conditions are applicable to the live system (single image modality; text pipeline unvalidated). |

## Documented only (not built)

### Module 9 — microservices & observability

Recommended path, in order, only when a concrete need appears:

1. Keep the **modular monolith** (`src/main.py` + `src/services/*`). It already isolates inference, retrieval, scheduling, auth and benchmarks behind module boundaries.
2. Move the benchmark runner to a worker (Celery + Redis) first — it is the only long-running job.
3. Extract the GPU inference engine into its own FastAPI service once more than one GPU or one concurrent user is required; version-pin models per case (already stored in each case's `selected_model`).
4. Add OpenTelemetry traces and Prometheus metrics; the per-agent timings stored in every case (`agents` column) are the natural span source.
5. Replace SQLite with PostgreSQL and the local `outputs/portal/uploads` directory with object storage; do not log images or free text.

### Module 10 — federated learning simulation

Suggested experiment (offline, on cached features, ~1 day of work once a **patient-grouped split exists**):

* Partition patients into 3–5 simulated sites with controlled label/skin-type skew.
* Compare local-only, centralised, FedAvg and FedProx on the metadata (B) and image-projection heads using `cached_multimodal_features.pt`.
* Report held-out accuracy, worst-site accuracy and communication rounds with patient-level CIs.
* State clearly that this is a *simulation*; it provides no privacy guarantee without secure aggregation / differential privacy.

It is intentionally not implemented here because the current splits are leaky (see `evaluation_audit.md`); a federated comparison on leaky splits would be uninterpretable.

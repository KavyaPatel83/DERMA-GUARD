# 12 — The Research Pipeline, DERMA-STRESS, Ablations and the Papers

This file covers everything that is *research-facing*: the v4.0 specification code under `src/`, the robustness
benchmark, the statistics tooling, and the paper drafts under `docs/`.

## 1. Origin: the specification (`proj.md`)

`proj.md` is the original long implementation prompt for "DERMA-GUARD v4.0". Its **core hypothesis**:

> A multi-agent consensus framework with dynamic diagnosis-adaptive evidence fusion and explicit evidence management
> reduces unsafe decisions in multimodal dermatology under imperfect evidence, compared to conventional single-model
> and static-ensemble baselines.

It prescribes the repository layout, technology stack, configs, agents, algorithms, benchmarks and tests. The code in
`src/` implements it; `det.md` and `detail.md` are long-form documentation drafts generated from the same
specification (dated 2026-08-25).

## 2. Module map of the research code

| Package | Files | Responsibility |
|---------|-------|----------------|
| `src/agents/` | `orchestrator.py`, `vision_team.py`, `scribe.py`, `librarian.py`, `devils_advocate.py` | The five agents and the 7-step pipeline |
| `src/evidence/` | `quality.py`, `reliability.py`, `utility.py`, `consistency.py`, `missingness.py` | Q, R, U, C, M computations |
| `src/fusion/` | `adaptive_fusion.py`, `consensus.py`, `acquisition.py` | EM-style fusion, 4-level hierarchy, acquisition policy |
| `src/llm/` | `client.py`, `prompts.py`, `extraction.py`, `report_gen.py`, `verification.py` | Ollama client, fixed prompts, symptom extraction, report, 2-stage verification |
| `src/retrieval/` | `rag_index.py` | FAISS index over modality-concatenated embeddings |
| `src/data/` | `dataset.py`, `derm7pt.py`, `preprocessing.py`, `splits.py`, `augmentation.py` | Loaders, patient-level splits, augmentation |
| `src/stress/` | `corruption.py`, `benchmark.py` | DERMA-STRESS conditions and runner |
| `src/eval/` | `metrics.py`, `stats.py`, `ablation.py` | Metrics, bootstrap/McNemar/FDR, ablations |
| `src/losses.py`, `src/utils.py` | | Focal loss, seeds, helpers |

## 3. The 7-step orchestrated pipeline

```
1. Parallel agents:   Vision team ‖ Scribe ‖ Librarian ‖ Devil's Advocate
2. Stage-1 verification (pre-fusion gate: OOD, critical conflict, empty evidence → ESCALATE/ABSTAIN)
3. Dynamic fusion     DiagnosisAdaptiveFusion (masked softmax weights, ≤3 EM iterations)
4. Consensus          Level 1..4 → ACCEPT / ARBITRATE / ACQUIRE / ESCALATE
5. Report             LLM synthesis (Qwen2.5-7B, T = 0) — structured tool calls only
6. Stage-2 verification  rule + LLM audit; failure → conservative regeneration → ESCALATE
7. Return             PipelineResult with full evidence trace + timings
```

Output type `PipelineResult`: `action`, `diagnosis`, `confidence`, `consensus_level`, `report`, `evidence_used`,
`evidence_missing`, `acquire_target`, `escalate_reason`, `evidence_trace`, `processing_time_s`, `model_version`.

### Fixes called out in the code ("critical fixes")
| Fix | Where |
|-----|-------|
| Missing modality: masked softmax then renormalise; all missing → `INSUFFICIENT_EVIDENCE` (never divide by zero) | `adaptive_fusion.py` |
| Class imbalance: focal loss γ = 2 + class weights `N / (K·n_c)` | `losses.py` |
| Gradient clipping `max_norm = 1.0`, mixed precision | training scripts |
| Early stopping on **validation macro-F1** (patience 10), not loss | `configs/base.yaml` |
| Swin-Tiny `num_classes=0` for pre-head embeddings; separate instances for clinical and dermoscopy | `vision_team.py` |
| RAG index built on **modality concatenation**, not the fused vector (avoids circularity) | `rag_index.py` |
| Utility U needs ground truth → *retrospective only*; deployment uses training-set approximation | `utility.py` |

## 4. Configuration (Hydra / OmegaConf, `configs/`)

| File | Role |
|------|------|
| `base.yaml` | Project name/seed 42, training (batch 32, 100 epochs, lr 1e-4, weight decay 0.05, clip 1.0, AMP, early stop), fusion (3 iterations, 0.05 convergence), consensus thresholds, LLM settings, data paths |
| `default.yaml` | Local-only defaults |
| `data/derm7pt.yaml`, `data/pad_ufes.yaml` | Dataset configs |
| `model/vision/*.yaml`, `model/text/clinicalbert.yaml`, `model/fusion/adaptive.yaml` | Per-model settings |
| `experiment/baseline_ladder/b1…b6.yaml` | The six internal baselines |

## 5. Baseline ladder (B1–B6) — "prove each component pays for itself"

| ID | Baseline | Adds |
|----|----------|------|
| B1 | ResNet152, clinical image only | CNN single model |
| B2 | Swin-Tiny, clinical image only | Transformer single model |
| B3 | Dual ResNet152 (clinical + dermoscopy) averaged logits | Late fusion |
| B4 | Concatenate `[z_clin, z_dermo, z_meta, z_text]` + linear head | Early fusion |
| B5 | PanDerm encoder + linear head fine-tuned | Foundation model |
| B6 | Majority vote of B1, B2, B5 | Static ensemble (no evidence profiling) |
| **DERMA-GUARD** | Evidence manager + adaptive fusion + consensus + acquisition + verification | Full system |

Literature baselines named in `docs/benchmarks_and_execution_guide.md`: SkinM2Former, DermFormer, PanDerm, DermLIP,
DermFM-Zero (replaced by DermLIP-PanDerm because weights are private), MetaBlock-SE.

## 6. Ablation studies (`src/eval/ablation.py`)

* **Linear chain:** image-only → +metadata → +text → +fusion → +Q → +R → +U → +C → +Sufficiency → +Uncertainty →
  +Acquisition → +Verification.
* **Factorial 2⁴:** all 16 combinations of {Q, R, C, M}.
* Reported as mean ± std over seeds {42, 43, 44}, with bootstrap 95 % CIs.

## 7. DERMA-STRESS — robustness benchmark

Question: *does the system stay safe when the evidence is damaged?* 18 conditions in four families
(`src/stress/corruption.py`):

| Family | Conditions |
|--------|-----------|
| **Availability** | missing clinical image; missing dermoscopy; missing metadata; missing text |
| **Technical** | Gaussian blur mild (k=5) / severe (k=15); Gaussian noise mild (σ=0.05) / severe (σ=0.2); low brightness (×0.5); heavy JPEG (q=10); black-patch occlusion (20 % area) |
| **Semantic** | contradictory text (e.g. "does not itch" for an itching lesion); vague text (< 5 words); permuted/incorrect metadata; dermoscopy swapped from another patient; metadata poisoning (swapped diagnosis); injected text hallucination |
| **Compound** | multi-failure (missing clinical image + mild noise + vague text) |

Targets from the execution guide (clean → under stress): accuracy ≥ 85 % → ≥ 75 %; macro-F1 ≥ 0.80 → ≥ 0.72;
ECE ≤ 0.08 → ≤ 0.10; unsafe-decision rate ≤ 2 % → ≤ 5 %; abstention 5–10 % → 15–25 %; conflict-detection precision
≥ 85 %; acquisition recovery ≥ 75 %; report hallucination ≤ 2 %.

> These are *targets*, not achieved results; the held-out numbers of the prototype are in `11_...`.

### Live-system version (`src/services/stress_runner.py`)
* Re-uses `corruption.py` on the **patient-disjoint held-out** rows only.
* 13 of 18 conditions are applicable (single image modality; text pipeline unvalidated → text conditions marked
  "not applicable"); `compound_multi` becomes blur-severe + noise-mild + missing metadata.
* Runs asynchronously (`POST /api/v1/benchmarks/stress` → 202; poll `/api/v1/benchmarks/{id}`); results stored in
  `stress_runs`.

## 8. Statistics (`src/eval/stats.py`)

Case-level **bootstrap** (1,000 resamples, 95 % CI), **McNemar's test** for paired model comparison, **Cohen's d**,
**Bonferroni / FDR** correction — chosen so claims of improvement are statistically defensible on small data.

## 9. Test suite (`tests/`)

| File | Covers |
|------|--------|
| `test_consensus.py` | Level 1–4 logic (strong, low-confidence, moderate, acquire, escalate, no-models) |
| `test_fusion.py` | Convergence within max iterations, weights sum to 1, missing-modality weight = 0, all-missing error |
| `test_evidence_profiler.py` | Quality bounds, PTIS, metadata completeness, JS consistency, conflict flag, OOD calibration |
| `test_verification.py` | Stage-1 gate cases |
| `test_orchestrator.py` | Clean case, evidence trace, OOD escalation, all-missing abstain |
| `test_data_pipeline.py` | Patient-level split leakage, ratios, class coverage |
| `test_portal_services.py` | Password hashing/policy, slot rules, ECE, temperature, conformal coverage, leak audit, morphology, growth simulation, acquisition behaviour, open accounts, agent scores |

## 10. Paper drafts in `docs/`

| Artefact | Content |
|----------|---------|
| `DERMA-GUARD_paper_v5.tex/.pdf` | Earlier v5 paper |
| `DERMA-GUARD_IEEE_milk10k_pad-ufes_results.*` | MILK10k + PAD-UFES results version |
| `DERMA-GUARD_IEEE_final_results.*`, `…_final_v2.*` | Later IEEE-format drafts |
| `DERMA-GUARD_final_paper/` | **Final** paper (`main.tex`, `DERMA-GUARD_paper.pdf`, figures `f_arch`, `f_policy`, `f_cf`, `f_trust`, portal screenshots) |
| `*_overleaf*` | Overleaf-ready bundles |
| `paper_src/` | HTML source and figures |

### The final paper in one paragraph
The second-generation DERMA-GUARD profiles **six specialists** (evidential heads for photo, dermoscopy and patient
details; the legacy PAD-UFES model; a nearest-neighbour vote; a class-balanced embedding classifier) with the evidence
manager, learns a gate over **ten signals** (selected among seven fusion rules by five-fold **cross-fitting**), and uses
a cost-aware, calibrated policy with a **Learn-then-Test** bound on missed cancers to choose among *answer with high
confidence*, *request dermoscopy/details*, *answer with low confidence (clinician confirms)* or *defer*. Base papers:
**HOT AI** (asks for dermoscopy) and **Learn-then-Test** (risk-controlling thresholds). It also documents the audit of
the first prototype (see `11_...`).

## 11. Other documentation in `docs/`

| File | Content |
|------|---------|
| `running_guide.md` | Run instructions |
| `benchmarks_and_execution_guide.md` | Paper comparisons, targets, phase-by-phase commands |
| `evaluation_audit.md` | The audit (see `11_...`) |
| `limitations.md` | Limitations v4.0 |
| `what_did_not_work.md` | Negative-results template with hypotheses and expected failure modes |
| `repro_statement.md` | Seeds, split files, hash tables (mostly TBD placeholders) |
| `v5_extension_notes.md` | v5 modules implemented vs. documented-only (microservices, federated simulation) |
| `knowledge_base/*.md` | The six RAG corpus documents |

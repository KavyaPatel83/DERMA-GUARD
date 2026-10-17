# 08 — The Multi-Agent Layer, RAG and the (Optional) LLM

Code: `src/services/care_agents.py`, `src/services/knowledge_base.py`.

## 1. What "agentic" means here

An *agent* is a small component with **one job**, deterministic inputs/outputs, and a trace entry. They are orchestrated
by `Orchestrator.analyze()`. There is no autonomous free-form LLM planning — the orchestration order is fixed and
auditable, which is a deliberate safety choice for a medical setting.

```
text ─► Intake ─► Safety(text) ─► Vision-Triage ─► Safety(result) ─► Retrieval(RAG) ─► Referral ─► Report ─► Scores
```

## 2. The agents

| Agent | Job | Method | Output |
|-------|-----|--------|--------|
| **IntakeAgent** | Convert free text into structured fields | Rule-based NER: regex for age, gender, size (mm/cm), body-region vocabulary, symptom patterns (itch, bleed, grew, changed, hurt, elevation) | Fields merged into metadata (explicit user input wins) |
| **SafetyAgent** | Guardrails | (a) emergency keyword patterns in text → "seek urgent care now"; (b) result checks: Escalated, malignant possibility not excluded, suspected malignancy, weak evidence | Flags with levels `emergency / high / info` |
| **Vision-Triage** | Run the trained models | `Engine.predict()` → temperature → conformal → triage (see `06`, `07`) | Diagnosis, ranking, conformal set, evidence, candidates, triage |
| **RetrievalAgent** | Ground the answer | Query = "{class name} features treatment {action} warning signs" → knowledge-base chunks; plus k = 8 **similar documented patients** from PAD-UFES-20 | Chunks with scores and citations; look-alike case list and class distribution |
| **ReferralAgent** | Where and how fast | Rule table: emergency symptoms → emergency care; MEL/SCC (or escalated with malignant in set) → Dermatologic Oncology, *urgent, within 1 week*; BCC → Dermatologic Surgery, *soon, 1–2 weeks*; ACQUIRE → General Dermatology, 2 weeks; ACK → routine 4–6 weeks; else routine | Department, urgency, window, reason |
| **ReportAgent** | Patient + clinician summaries | Deterministic template; if a local LLM is reachable, it *rewrites* the facts with citations `[1] [2]` | `patient_summary`, `clinician_summary`, `mode`, `citations` |
| **ChatAgent** | Conversational front-end | Intent routing: emergency → safety message; greeting; booking → scheduler tool; "my result / why escalated" → explain latest case; else RAG answer | Reply, sources, suggested actions |

### Trace and fault isolation
`Trace.run(agent, action, fn)` wraps every step, records `{agent, action, ok, ms, detail}` and **catches exceptions** so an
agent failure cannot crash the case; a failed agent scores 0 and the trace shows the error.

## 3. Agent scores (transparent, not probabilities)

`score_agents()` produces 0–1 **process-quality** scores:

| Agent | Weight | Score basis |
|-------|:-----:|-------------|
| Intake | 0.15 | Share of 9 key clinical fields available |
| Safety | 0.20 | `1 − 0.5·emergency − 0.15·high − 0.05·info` flags |
| Vision-Triage | 0.30 | `0.6·calibrated confidence + 0.4·model agreement` |
| Retrieval (RAG) | 0.20 | `0.5·mean chunk relevance + 0.5·share of look-alike patients with the predicted class` |
| Referral | 0.10 | `1 − 0.3·|urgency gap|` between recommended urgency and class/action risk |
| Report | 0.05 | `min(1, citations/3)` × (1.0 LLM, 0.9 template) |

Combined indices:
```
agent_score  = weighted mean of the six agent scores
model_score  = 0.5·calibrated confidence + 0.5·selected model's held-out accuracy
combined     = 0.5·model_score + 0.5·agent_score          → high ≥ 0.7, moderate ≥ 0.5, else low
```
The result page states that `combined` is a heuristic *assurance index*, **not** a probability of being correct.

## 4. Retrieval-Augmented Generation (RAG)

### 4.1 `KnowledgeBase` — text retrieval
| Step | Detail |
|------|--------|
| Corpus | `docs/knowledge_base/*.md` (skin conditions, diagnosis & treatment, prevention & self-checks, warning signs & urgency, hospital info, using DERMA-GUARD) + `docs/limitations.md` + `docs/what_did_not_work.md` |
| Chunking | Split by markdown headings, then sentence groups of ~110 words; each chunk keeps title, section, source file |
| Sparse index | TF-IDF (1–2-grams, sublinear TF, English stop-words) |
| Dense index | `sentence-transformers/all-MiniLM-L6-v2` loaded with Hugging Face `AutoModel` (local files only, so it works offline once cached); embeddings cached in `outputs/portal/kb_embeddings.npz` |
| Fusion | **Reciprocal Rank Fusion** of dense and sparse rankings (hybrid) |
| Degradation | If the dense model is unavailable it falls back to keyword (TF-IDF) and reports the mode |

### 4.2 `SimilarCases` — look-alike patient retrieval
Nearest neighbours among the 2,298 documented PAD-UFES-20 records using the structured patient features. Output includes
the class distribution of neighbours and thumbnails ("look-alike patients' images" in the RAG panel). The
`exclude_img` argument prevents a sample case from retrieving itself.

### 4.3 Why retrieval is "non-generative"
Nothing in retrieval creates new text; every chunk carries its source so the report and chat can **cite** it.

## 5. The optional LLM

| Item | Detail |
|------|--------|
| Server | **Ollama** at `http://127.0.0.1:11434` |
| Model | `qwen2.5:7b` (configurable) |
| Check | `LLM.available()` pings `/api/tags` (cached 30 s) |
| System prompt | "Use ONLY the facts supplied… Never state a definitive diagnosis. Cite sources as [1], [2]… recommend seeing a clinician." |
| Temperature | 0.2 in the portal; 0.0 in the research pipeline |
| Failure mode | Any error → deterministic template/extractive answer; status page shows `llm.available` |

**The LLM never diagnoses.** It only rephrases evidence that other agents produced. Without Ollama the system is fully
functional.

## 6. Headline/RAG consistency rule (known design quirk)

In `Orchestrator.analyze()`, if the most common class among retrieved look-alike patients differs from the model's top
class, the headline diagnosis is switched to the RAG class and the probability bars/conformal set are adjusted so the
page is internally consistent. Consequences to keep in mind:

* It improves visual consistency but means the headline can differ from the selected model's argmax.
* The change is not hidden (the candidate models panel still shows each model's own prediction), but it is a heuristic
  that has not been separately validated; remove or re-validate it before any real use.

## 7. Research-pipeline agents (v4.0 spec)

| Agent | File | Notes |
|-------|------|-------|
| `VisionSpecialistTeam` | `src/agents/vision_team.py` | Runs DermLIP-PanDerm, PanDerm, Swin-Tiny ×2, ResNet152 in parallel (`concurrent.futures`), per-image quality via OpenCV |
| `ScribeAgent` | `src/agents/scribe.py` | Bio_ClinicalBERT mean-pooled 768-d, structured symptom extraction with 3 fixed temperature-0 prompts, PTIS v1 (heuristic) and v2 (ICC-validated regressor) |
| `LibrarianAgent` | `src/agents/librarian.py` | FAISS RAG over **modality-concatenated** embeddings (deliberately *not* the fused vector, avoiding circular dependency) |
| `DevilsAdvocateAgent` | `src/agents/devils_advocate.py` | Evidence profile + OOD |
| `OrchestratorAgent` | `src/agents/orchestrator.py` | 7-step pipeline; "structured tool-calling only — the LLM synthesises reports but does NOT independently diagnose" |
| Verification | `src/llm/verification.py` | Stage 1 pre-fusion gate; Stage 2 rule + LLM report audit with conservative regeneration, else ESCALATE |

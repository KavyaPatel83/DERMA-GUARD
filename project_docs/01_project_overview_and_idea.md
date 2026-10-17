# 01 — Project Overview and the Core Idea

## 1. What is DERMA-GUARD?

**DERMA-GUARD** (repository name *HealthSphere*) is a **multimodal, evidence-aware, agent-based decision-support system
for skin-lesion triage**. A user can provide any combination of:

| Modality | Example | Notes |
|----------|---------|-------|
| **Image** | A smartphone photo of the lesion | JPEG/PNG, 32–4096 px, < 10 MB |
| **Metadata** | Age, sex, body region, lesion diameters, Fitzpatrick skin type, itch / grew / hurt / changed / bleed / elevation, smoking, drinking, pesticide exposure, cancer history | 17 structured fields |
| **Text** | "A 62-year-old man has a bleeding patch on his nose that has grown over 3 months" | Free-text description; can be auto-generated from metadata |

and receives:

* a **predicted class** among 6 skin-lesion types (BCC, ACK, NEV, SEK, SCC, MEL);
* a **calibrated confidence** and a **conformal prediction set** (the classes that remain plausible);
* an **evidence profile** (how good was each input and how much was it trusted);
* a **triage action** — ACCEPT / ARBITRATE / ACQUIRE / ESCALATE;
* a **referral recommendation** (department, urgency, time window);
* a **grounded explanation** with citations to a small knowledge base and to similar documented patients;
* a **clinician workflow** — a doctor can review the case and record a final decision.

It is delivered as a working website (one FastAPI process) with three roles: patient, doctor, admin.

## 2. The central idea in plain language

A normal classifier answers *"what is this lesion?"*.
DERMA-GUARD asks first: **"is the evidence good enough to answer, and how sure should we really be?"**

A careful dermatologist behaves this way:

* With clear evidence → names a diagnosis.
* With weak or incomplete evidence → asks for dermoscopy or more history before committing.
* When the photo and the history disagree → refers or arbitrates instead of guessing.
* For anything that could be melanoma → never "auto-accepts" without specialist confirmation.

DERMA-GUARD turns that behaviour into software with five building blocks:

```
   INPUTS            EVIDENCE GRADING          FUSION            SAFE DECISION        CARE WORKFLOW
 image / meta /  →   Q  R  U  C  S  M   →   adaptive,    →   calibrated prob.  →   agents, RAG,
 text (any mix)      per modality           per-case         + conformal set        referral, report,
                                            weights          + 4-level triage       doctor review
```

### The five key ideas

1. **Any-modality inference (Models A–G).** Seven trained models cover every non-empty combination of
   image / metadata / text. The right model is chosen automatically from what the user supplied.
2. **Evidence management.** Each modality gets scores for quality (Q), reliability (R), utility (U), plus a shared
   consistency (C), sufficiency (S) and a missingness mask (M). The product `E_m = Q·R·U·C·S·M` becomes the
   modality's *evidence score*, normalised into **dynamic fusion weights**.
3. **Diagnosis-adaptive fusion.** The weights are iteratively refined with a clinical prior: "for suspected melanoma
   the image matters more; for actinic keratosis the history/symptoms matter more".
4. **Honest uncertainty.** Temperature scaling + split-conformal prediction + a rule-based triage hierarchy, with the
   thresholds fitted on rows that were **not** used for training.
5. **Care platform.** Instead of stopping at a prediction, the project builds the surrounding workflow: safety
   guardrails, retrieval-augmented explanations, referral, appointments, longitudinal tracking, audit, stress testing.

## 3. Goals

| Goal | How the project addresses it |
|------|-------------------------------|
| Classify lesions from heterogeneous, possibly incomplete inputs | Models A–G, modality-dropout training, missingness handling |
| Avoid over-confident answers | Evidence gate, temperature scaling, conformal sets, triage |
| Make decisions explainable | Evidence profile, agent trace, per-agent scores, RAG citations, occlusion explanation audit |
| Be honest about performance | `honest_eval.py` re-evaluates on held-out rows; site shows measured vs. originally reported accuracy |
| Behave like a real service | Auth, RBAC, audit log, scheduling, doctor review loop, input sanitisation |
| Cost nothing to run | Local models only, SQLite, optional local LLM (Ollama), no paid APIs |

## 4. Main contributions

1. A unified framework that treats **evidence quality** as a first-class signal in multimodal skin-lesion triage.
2. **Evidence-aware adaptive gated fusion** with diagnosis-adaptive prior refinement.
3. A **calibrated safety layer** (temperature scaling + split conformal + 4-level triage) fitted on genuinely
   held-out data.
4. A **multi-agent care layer** (Intake, Safety, Vision-Triage, Retrieval/RAG, Referral, Report) with transparent
   0–1 scores for each agent.
5. A **hospital-style web portal** that connects patients, doctors and administrators to the model.
6. **DERMA-STRESS**, a robustness benchmark with 18 listed corruption conditions across availability, technical,
   semantic and compound failures (13 applicable to the live single-image system).
7. A **transparent evaluation audit** that found and documented data-leakage and target-accuracy problems in the first
   training script and replaced the reported figures with measured ones.

## 5. Who uses it

| Role | What they can do |
|------|-------------------|
| **Patient** | Register (name + email), upload photo / details / text, get AI result + evidence, ask the chat assistant, request doctor review, book appointments, track a lesion over time |
| **Doctor** | See *all* cases, review images / model opinions / retrieved similar patients / agent scores, record the final decision, manage appointments |
| **Admin** | Manage accounts, view audit log and aggregate statistics — never clinical content |

## 6. Where it sits academically

* Domain: multimodal medical AI, trustworthy AI, selective prediction, uncertainty quantification, multi-agent systems.
* Target venues named in the project notes: IEEE JBHI, npj Digital Medicine, MICCAI workshops.
* The repository contains several IEEE-format LaTeX drafts under `docs/` (see `12_research_pipeline_stress_and_paper.md`).

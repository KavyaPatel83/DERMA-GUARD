# 02 — The Problem, Existing Solutions, and Why This Idea

## 1. The real-world problem

* Skin cancer is among the most common cancers worldwide; **early detection of melanoma and carcinoma dramatically
  improves outcomes**, yet dermatologists are scarce, especially outside cities.
* Smartphones make lesion photos easy to capture, so **AI triage** is attractive: screen at home, escalate the
  suspicious ones.
* But clinical reality is messy:
  * photos are blurred, dark, partially covered or badly framed;
  * patient history is often incomplete or missing;
  * history and image can *contradict* each other;
  * classes are heavily imbalanced (in PAD-UFES-20, melanoma is only 52 of 2,298 cases);
  * the model may see something it was never trained on (out-of-distribution).

## 2. How existing solutions work (and where they fall short)

| Category | Typical examples | What they do well | Where they fall short for our goal |
|----------|------------------|-------------------|------------------------------------|
| **Single-image CNN/ViT classifiers** | ResNet, EfficientNet, Swin, dermatologist-level CNNs (Esteva et al.) | High accuracy on curated, clean images | Ignore patient context; always output a label; confidence often miscalibrated |
| **Metadata fusion models** | MetaBlock (Pacheco 2021), MetaBlock-SE | Add age/site/symptoms to the image | Fixed fusion; no per-case quality assessment; fail ungracefully when metadata is missing |
| **Tri-modal transformer fusion** | SkinM2Former (2025) | Cross-attention over image, text, metadata | Equal-weight treatment of modalities; no notion of "this modality is unreliable *for this case*" |
| **Robust fusion** | DermFormer (2025) | Entropy weighting, some robustness to missing data | Weights not diagnosis-aware; no abstention/acquisition logic |
| **Foundation / VLM models** | PanDerm, DermLIP, DermFM-Zero | Strong visual features, zero-shot | Image-centric, weights sometimes private; still just a classifier head |
| **Selective prediction / abstention** | Chow's rule, selective classification, learning-to-defer | Can withhold uncertain answers | Typically only a confidence threshold, safe only as the underlying fusion is |
| **Conformal prediction for derm** | Conformal sets, Mondrian/group conformal | Distribution-free coverage | Used alone, no workflow, no evidence acquisition |
| **"Ask for dermoscopy" systems** | HOT AI | Recommends dermoscopy when photo is insufficient | Models and data not public; no explicit cost model; no deferral for contradictory evidence |
| **Consumer apps** | Phone "mole scanner" apps | Convenient | Output a number with no uncertainty, no clinician loop, no audit trail |

## 3. The gaps this project targets

1. **No evidence grading.** Existing fusion treats a blurred photo and a sharp photo identically.
2. **No diagnosis-adaptive trust.** The importance of image vs. history *depends on the suspected disease* (dermoscopy
   is critical for melanoma; symptoms/history dominate for actinic keratosis), but fusion weights are usually global.
3. **Forced answers.** Few systems have a first-class *"acquire more evidence"* or *"escalate"* output.
4. **Weak uncertainty.** Raw softmax confidence is over-confident; few pipelines combine calibration + conformal
   sets + a human-readable decision rule.
5. **Prediction without a care workflow.** Research code typically ends at a metric; real use needs safety checks,
   explanations, referral, review, audit.
6. **Evaluation honesty.** Medical-AI papers frequently leak patients between train/test. A system that claims
   "reliability" must itself be evaluated reliably.

## 4. Why we chose this idea

| Reason | Explanation |
|--------|-------------|
| **Clinical relevance** | The most damaging failure of dermatology AI is *confident error*, not low accuracy on clean data. Targeting behaviour under imperfect evidence addresses a real safety problem. |
| **Genuine research novelty** | Individual ingredients exist (fusion, conformal, abstention, RAG). The combination — evidence manager + diagnosis-adaptive fusion + safe action hierarchy + care platform — is the contribution. |
| **Fits an open, zero-cost setting** | PAD-UFES-20 is free (CC BY 4.0); everything can run locally on a laptop CPU/GPU with no paid API. |
| **Natural multimodality** | PAD-UFES-20 provides images **and** 26 metadata columns, so tri-modal work is possible without private data. |
| **Demonstrable end-to-end** | A capstone benefits from something that can be *shown*: upload a photo, watch agents run, see a triage decision and a doctor review it. |
| **Scalable scope** | Core (models A–G + evidence + triage) is achievable; extras (RAG, agents, stress tests, lesion tracking) can be layered without breaking it. |
| **Teaches the right lesson** | The audit episode (reported 85–90 % vs. measured 61–78 %) turns into a research result about evaluation integrity. |

## 5. Why *this* design and not the obvious alternatives

| Alternative | Why it was not chosen |
|-------------|------------------------|
| "Just train a bigger image model" | Does not address missing/poor-quality evidence or abstention; also overfits badly with 2,298 images (the audit shows ≈ 99 % train vs. ≈ 61 % held-out). |
| "Concatenate all features and train one MLP" | Cannot cope with missing modalities, cannot explain which modality drove a decision, cannot adapt per case. |
| "Use an LLM to diagnose" | Unsafe, non-reproducible, hallucination risk. In this project the LLM may only *reword* evidence that other agents produced. |
| "Only report accuracy" | Hides the cases that matter (SCC/MEL recall) and ignores calibration and abstention. |
| "Conformal prediction only" | Gives a set but no action or workflow; large sets are not actionable by themselves. |
| "Build only the research pipeline, no website" | Hard to demonstrate the safety behaviour to non-experts; the portal makes triage, review and audit tangible. |

## 6. Positioning statement

> DERMA-GUARD is not trying to be a better classifier. It is trying to be a **more honest and safer decision process**
> around a classifier: grade the evidence, adapt the fusion, calibrate the uncertainty, choose a safe action, and keep
> a human in the loop — while being transparent about how well the underlying models really perform.

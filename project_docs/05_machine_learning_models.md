# 05 — Machine-Learning Models

All code for the live models is in `Dummy/Project/` (`models/encoders.py`, `models/adaptive_fusion.py`,
`models/stacking_ensemble.py`, `train_all.py`, `predict.py`).

## 1. The seven configurations (Models A–G)

Every non-empty subset of {image, metadata, text} gets its own trained model, so the system can always use whatever the
user provides.

| Model | Inputs | Encoder(s) | Needs |
|:----:|--------|------------|-------|
| **A** | Image only | ResNet50 → 8 patch tokens → 2-layer MHSA ViT block | image |
| **B** | Metadata only | Residual MetaBlock MLP (TabTransformer encoder also implemented) | metadata |
| **C** | Text only | Bio_ClinicalBERT [CLS] → projector | text |
| **D** | Image + Metadata | A + B → gated fusion | image, metadata |
| **E** | Image + Text | A + C → gated fusion | image, text |
| **F** | Text + Metadata | C + B → gated fusion | text, metadata |
| **G** | Image + Text + Metadata | A + B + C → gated fusion | all three |

`MODALITY_MODEL_MAP` in `predict.py` picks the model from the active inputs (default **G**). The user can also force a
model (`model=A..G`); the API rejects it if required inputs are missing. At inference **all feasible candidate models are
run** and their predictions are shown as the "model panel"; the selected one is the headline.

## 2. Encoders

### 2.1 Image: `VisionTransformerImageEncoder`
```
photo 224×224 ──► ResNet50 (ImageNet, frozen) ──► 2048-d feature map
              ──► DermatologicalChannelAttention (squeeze-and-excite: a = σ(W2·GELU(W1·GAP(F))))
              ──► split into 8 tokens + learnable [CLS] + 1-D positional embedding
              ──► 2 × Pre-LN Multi-Head Self-Attention blocks (8 heads, GELU FFN)
              ──► 256-d image embedding
```
In deployment a lightweight **projection head** (`img_proj.pt`) maps the cached 2048-d ResNet feature to 256-d.

### 2.2 Metadata: `MetaBlockMLPEncoder` / `TabTransformerEncoder`
* Input: 116 engineered features.
* `MetaBlockMLPEncoder`: LayerNorm + GELU, a residual MetaBlock MLP (hidden 512, dropout 0.15) → 256-d.
* `TabTransformerEncoder` (Huang et al.): column embeddings (d = 64), 4-head self-attention blocks, numeric projection
  → 256-d. Both are in `encoders.py`; the documentation for the prototype names the Residual MetaBlock MLP as the
  production metadata encoder and prints "TabTransformer" in the verbose inference trace.

### 2.3 Text: `LanguageEncoder`
* `emilyalsentzer/Bio_ClinicalBERT` (pre-trained on MIMIC-III clinical notes), WordPiece max length 128.
* [CLS] token (768-d) → deep residual **text projector** (`text_proj.pt`) → 256-d.

## 3. Fusion: `AdaptiveGatedFusion` (`models/adaptive_fusion.py`)

```
for each active modality m:
    e_m   = L2-normalise(embedding_m)                       # 256-d
    g_m   = GatingMLP([e_m ; evidence_score_m])             # scalar logit
w_raw   = softmax(g / 2.0)                                  # temperature 2 prevents winner-take-all
w_prior = evidence_score / Σ evidence_score
w       = 0.60·w_raw + 0.40·w_prior   (renormalised)
fused   = Σ w_m · e_m
rep     = GELU(fused + Projection(fused))                   # residual projection, LayerNorm
logits  = Classifier(rep)                                    # 256→128→6
```

Training-time features:
* **Stochastic modality dropout** (p = 0.15 when >1 modality) — teaches the model to cope with a missing input.
* **Gating takes evidence as an input** — the evidence manager's score for each modality is concatenated to its
  embedding, so the learned fusion is explicitly *evidence-aware*.
* `refine_weights_with_prior()` implements the diagnosis-adaptive update
  `w⁽ᵏ⁺¹⁾ = softmax(α·log w⁽ᵏ⁾ + β·log π(ŷ))` with α = 0.6, β = 0.4.

## 4. Calibrated stacking ensemble (`models/stacking_ensemble.py`)

A neural network trained on ~2k rows is brittle, so each model optionally gets a *residual* tree-ensemble layer:

* Auxiliary learners on power-L2-normalised features: **ExtraTrees**, **RandomForest**, **HistGradientBoosting**,
  calibrated **Logistic Regression**.
* Meta-blend: `p = (1 − α)·p_neural + α·p_aux`, with α chosen on validation. If the auxiliary learners do not help,
  `α = 0` — the ensemble can never score below the neural anchor on validation.
* In the live path α ≤ 0.25 ("raw neural softmax blended with stacking ensemble").

## 5. Training recipe (`train_all.py`)

| Item | Setting |
|------|---------|
| Strategy | Cache frozen ResNet50 / BERT / metadata features once, then train light heads → fast on a laptop |
| Optimiser | AdamW, weight decay 1e-4 |
| LR schedule | Cosine annealing (η_min 1e-5); projection heads lr 5e-4, models lr 2e-3 (varies) |
| Epochs | 30–35 per model; projection pre-training 15 epochs |
| Loss | Focal loss γ = 2, label smoothing 0.02, inverse-frequency class weights |
| Batch | 32 |
| Selection | Best validation accuracy checkpoint (`outputs/checkpoints/best_model_*.pth`) |
| Tracking | TensorBoard logs in `outputs/logs/model_A…E` |
| Seed | 42 |

> ⚠ The same script also contains the *evaluation* code that the audit later found to be invalid (see
> `11_evaluation_audit_and_results.md`). The **models and weights are real**; the originally printed accuracies are not.

## 6. Why these model choices (short version; full table in `13_...`)

| Choice | Reason |
|--------|--------|
| ResNet50 backbone, frozen | Strong, small, ImageNet-pretrained; with 2.3k images a frozen backbone limits overfitting and allows caching |
| Self-attention head over patch tokens | Cheap way to give the head a ViT-like inductive step on top of CNN features |
| Residual MLP for tabular data | Small tabular vector; deep tabular transformers are overkill and overfit |
| Bio_ClinicalBERT | Clinical-domain language model — better than generic BERT for medical phrasing |
| Gated fusion with evidence input | Lets the network learn *how much to trust each modality per case* |
| Modality dropout | Real inputs are often incomplete |
| Tree-ensemble stacking | Robust on small tabular-like feature sets; guaranteed not worse than anchor on validation |
| Focal loss + class weights | Rare, dangerous classes (MEL, SCC) should not be ignored |

## 7. Other model families in the research code (`src/agents/vision_team.py`, `configs/model/`)

| Config | Backbone | Role |
|--------|----------|------|
| `dermlip_panderm.yaml` | `hf-hub:redlessone/DermLIP_PanDerm-base-w-PubMed-256` | Vision-language foundation model, zero-shot + embeddings |
| `panderm.yaml` | PanDerm encoder (1.5 M-image derm foundation model) | Strong visual features |
| `swin_tiny.yaml` | `swin_tiny_patch4_window7_224` (timm), two instances (clinical, dermoscopy) | Fine-tuned vision |
| `resnet152.yaml` | `resnet152.a2_in1k` (timm) | CNN diversity |
| `clinicalbert.yaml` | Bio_ClinicalBERT | Text |
| `adaptive.yaml` | `DiagnosisAdaptiveFusion` | Fusion |

These implement the paper-spec "vision specialist team" and are exercised by unit tests; they are not what the live
website runs (see `03_...` and `12_...`).

## 8. Saved artefacts

| File | Meaning |
|------|---------|
| `Dummy/Project/saved_models/model_{A..G}/` | Trained neural weights + stacking ensembles per model |
| `img_proj.pt`, `text_proj.pt` | Projection heads from 2048-d / 768-d to 256-d |
| `preprocessor.pkl` | Fitted metadata preprocessor |
| `conformal_calibrator.pt` | Original conformal calibration (superseded by the portal's held-out calibration) |
| `cached_multimodal_features.pt` | Cached features used for training and honest evaluation |
| `outputs/checkpoints/best_model_A..E.pth` | Best-epoch checkpoints from the capstone training run |
| `models/ptis_scorer.pt`, `models/ptis_thresholds.json` | PTIS v2 regressor and thresholds (research pipeline) |

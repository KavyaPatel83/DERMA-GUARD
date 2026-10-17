"""
scripts/train_derma_guard.py — End-to-end training script for DERMA-GUARD v4.0.

Training workflow:
  1. Build RAG index from training embeddings
  2. Train DiagnosisAdaptiveFusion (focal loss, gradient clipping, AMP)
  3. Train PTISv2Regressor
  4. Calibrate OOD detector threshold
  5. Train AcquisitionPolicy
  6. Run ablation study
  7. Run evaluation on test set
"""
import argparse
import json
import os
from pathlib import Path

# Windows KMP fix
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import wandb

from src.fusion.adaptive_fusion import DiagnosisAdaptiveFusion, FocalLossWithWeights


def parse_args():
    parser = argparse.ArgumentParser(description="Train DERMA-GUARD v4.0")
    parser.add_argument("--data-dir",      type=str, default="data",           help="Data root directory")
    parser.add_argument("--output-dir",    type=str, default="outputs",        help="Output directory")
    parser.add_argument("--epochs",        type=int, default=50,               help="Max training epochs")
    parser.add_argument("--batch-size",    type=int, default=32,               help="Batch size")
    parser.add_argument("--lr",            type=float, default=1e-4,           help="Learning rate")
    parser.add_argument("--patience",      type=int, default=10,               help="Early stop patience")
    parser.add_argument("--seed",          type=int, default=42,               help="Random seed")
    parser.add_argument("--num-classes",   type=int, default=7,                help="Number of classes")
    parser.add_argument("--no-amp",        action="store_true",                help="Disable mixed precision")
    parser.add_argument("--run-ablation",  action="store_true",                help="Run ablation study")
    parser.add_argument("--run-stress",    action="store_true",                help="Run DERMA-STRESS")
    parser.add_argument("--run-wandb",     action="store_true",                help="Enable W&B logging")
    return parser.parse_args()


def set_seeds(seed: int):
    import random, numpy as np
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def train_fusion(args, train_loader, val_loader, device):
    """Train DiagnosisAdaptiveFusion with focal loss, gradient clipping, AMP.

    Critical training rules:
    - Focal loss (gamma=2.0) + inverse-frequency class weights
    - Gradient clipping max_norm=1.0
    - Early stopping on val macro-F1, patience=10 (NOT on loss)
    - AMP (torch.cuda.amp) unless --no-amp
    """
    from sklearn.metrics import f1_score
    from src.fusion.adaptive_fusion import InsufficientEvidenceError

    fusion = DiagnosisAdaptiveFusion(
        num_classes=args.num_classes,
        d_common=768,
        max_iterations=3,
    ).to(device)

    optimizer = torch.optim.AdamW(fusion.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)
    scaler = GradScaler(enabled=not args.no_amp and torch.cuda.is_available())

    # Compute class weights from train labels
    all_labels = []
    for batch in train_loader:
        all_labels.extend(batch["label"].tolist())
    label_tensor = torch.tensor(all_labels, dtype=torch.long)
    class_weights = FocalLossWithWeights.compute_class_weights(label_tensor, args.num_classes).to(device)
    criterion = FocalLossWithWeights(gamma=2.0, weight=class_weights)

    best_f1 = 0.0
    patience_counter = 0
    best_state = None
    output_dir = Path(args.output_dir) / "checkpoints"
    output_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(args.epochs):
        fusion.train()
        train_loss = 0.0

        for batch in train_loader:
            optimizer.zero_grad()
            labels = batch["label"].to(device)

            embeddings = {k: v.to(device) for k, v in batch.get("embeddings", {}).items()}
            quality = batch.get("quality", {"clinical": 0.7})
            reliability = batch.get("reliability", {"model_0": 0.8})
            utility = batch.get("utility", {"clinical_image": 0.5})
            consistency = float(batch.get("consistency", torch.tensor(0.9)))
            missing_mask = batch.get("missing_mask", torch.ones(5)).to(device)

            try:
                with autocast(enabled=not args.no_amp and torch.cuda.is_available()):
                    out = fusion(embeddings, quality, reliability, utility, consistency, missing_mask)
                    logits = out["logits"]  # (B, K)
                    loss = criterion(logits, labels)

                scaler.scale(loss).backward()
                # Gradient clipping: max_norm=1.0 (CRITICAL)
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_(fusion.parameters(), max_norm=1.0)
                scaler.step(optimizer)
                scaler.update()
                train_loss += loss.item()
            except InsufficientEvidenceError:
                continue  # skip all-missing batches

        scheduler.step()
        avg_loss = train_loss / max(len(train_loader), 1)

        # Validation: early stop on macro-F1 (NOT loss)
        fusion.eval()
        val_preds, val_true = [], []
        for batch in val_loader:
            labels = batch["label"].tolist()
            embeddings = {k: v.to(device) for k, v in batch.get("embeddings", {}).items()}
            missing_mask = batch.get("missing_mask", torch.ones(5)).to(device)
            try:
                with torch.no_grad():
                    out = fusion(
                        embeddings,
                        batch.get("quality", {}),
                        batch.get("reliability", {}),
                        batch.get("utility", {}),
                        float(batch.get("consistency", 0.9)),
                        missing_mask,
                    )
                preds = out["logits"].argmax(dim=-1).tolist()
                val_preds.extend(preds)
                val_true.extend(labels)
            except InsufficientEvidenceError:
                continue

        if val_true:
            val_f1 = f1_score(val_true, val_preds, average="macro", zero_division=0)
        else:
            val_f1 = 0.0

        print(f"Epoch {epoch+1}/{args.epochs} | Loss={avg_loss:.4f} | Val F1={val_f1:.4f}")

        if val_f1 > best_f1:
            best_f1 = val_f1
            patience_counter = 0
            best_state = {k: v.cpu().clone() for k, v in fusion.state_dict().items()}
            torch.save(best_state, output_dir / "fusion_best.pt")
            print(f"  ✓ New best F1={val_f1:.4f}")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"Early stopping at epoch {epoch+1} (patience={args.patience})")
                break
        
        if args.run_wandb:
            wandb.log({
                "train_loss": avg_loss,
                "val_f1": val_f1,
                "epoch": epoch + 1
            })

    if best_state:
        fusion.load_state_dict(best_state)
    return fusion, best_f1


def main():
    args = parse_args()
    set_seeds(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Train] Using device: {device}")
    
    if args.run_wandb:
        wandb.init(
            project=os.getenv("WANDB_PROJECT", "derma-guard-v4"),
            config=vars(args),
            name="train_fusion"
        )

    print(f"[Train] Output: {args.output_dir}")

    # In practice, replace these with your real DataLoader implementations:
    print("[Train] Note: Placeholder DataLoaders — replace with src.data.derm7pt loaders")

    output_dir = Path(args.output_dir)
    (output_dir / "logs").mkdir(parents=True, exist_ok=True)

    training_summary = {
        "seed": args.seed,
        "device": str(device),
        "epochs_max": args.epochs,
        "lr": args.lr,
        "batch_size": args.batch_size,
        "early_stopping_on": "val_macro_f1",
        "patience": args.patience,
        "loss": "FocalLoss(gamma=2.0) + class_weights",
        "gradient_clip": "max_norm=1.0",
        "amp": not args.no_amp,
    }

    with open(output_dir / "logs" / "training_config.json", "w") as f:
        json.dump(training_summary, f, indent=2)

    print("[Train] Training configuration saved.")
    print("[Train] To run full training, provide DataLoaders from src.data.derm7pt")


if __name__ == "__main__":
    main()

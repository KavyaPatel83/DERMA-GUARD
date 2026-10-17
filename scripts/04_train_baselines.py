"""
scripts/04_train_baselines.py — Train B1–B6 baseline models for DERMA-GUARD v4.0.

Baseline Ladder (per proj.md Part 2 & det.md Section 3.2):
  B1: ResNet152 — clinical image only, standard CE
  B2: Swin-Tiny — clinical image only, standard CE
  B3: Late Fusion — ResNet152(clinical) + ResNet152(dermoscopy), average logits
  B4: Multimodal Concat — [z_clinical, z_dermo, z_meta, z_text] → linear head
  B5: PanDerm Fine-tuned — PanDerm encoder + linear head
  B6: Ensemble Majority Vote — majority vote over B1+B2+B5

Usage:
    python scripts/04_train_baselines.py --baseline B1 --dataset derm7pt
    python scripts/04_train_baselines.py --baseline all --dataset pad_ufes
    python scripts/04_train_baselines.py --baseline B6  # Requires B1,B2,B5 trained first
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Windows KMP fix
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from sklearn.metrics import f1_score, balanced_accuracy_score

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    import timm
    TIMM_AVAILABLE = True
except ImportError:
    TIMM_AVAILABLE = False
    print("WARNING: timm not installed. Install with: pip install timm")


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------
def set_seed(seed: int = 42):
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ---------------------------------------------------------------------------
# Focal Loss (per spec: gamma=2.0, inverse-frequency class weights)
# ---------------------------------------------------------------------------
class FocalLoss(nn.Module):
    def __init__(self, gamma: float = 2.0, weight: torch.Tensor | None = None):
        super().__init__()
        self.gamma = gamma
        self.weight = weight

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        ce = F.cross_entropy(logits, targets, weight=self.weight, reduction="none")
        pt = torch.exp(-ce)
        loss = ((1 - pt) ** self.gamma) * ce
        return loss.mean()


def compute_class_weights(labels: list[int], num_classes: int) -> torch.Tensor:
    """Inverse-frequency class weights: weight_c = N / (n_classes * n_c)."""
    counts = torch.zeros(num_classes)
    for lbl in labels:
        counts[lbl] += 1
    counts = counts.clamp(min=1)
    N = len(labels)
    return N / (num_classes * counts)


# ---------------------------------------------------------------------------
# Simple image dataset wrapper for baselines
# ---------------------------------------------------------------------------
class ImageDataset(Dataset):
    """Minimal dataset — loads PIL images and applies transforms."""

    def __init__(self, file_list: list[dict], transform=None):
        self.items = file_list  # [{"path": str, "label": int}]
        self.transform = transform

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        from PIL import Image
        item = self.items[idx]
        img = Image.open(item["path"]).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return {"image": img, "label": item["label"]}


# ---------------------------------------------------------------------------
# Model builders
# ---------------------------------------------------------------------------
def build_resnet152(num_classes: int, pretrained: bool = True) -> nn.Module:
    if not TIMM_AVAILABLE:
        raise ImportError("timm required. pip install timm")
    model = timm.create_model("resnet152.a2_in1k", pretrained=pretrained, num_classes=num_classes)
    return model


def build_swin_tiny(num_classes: int, pretrained: bool = True) -> nn.Module:
    if not TIMM_AVAILABLE:
        raise ImportError("timm required. pip install timm")
    model = timm.create_model("swin_tiny_patch4_window7_224", pretrained=pretrained, num_classes=num_classes)
    return model


class LateFusionModel(nn.Module):
    """B3: ResNet152(clinical) + ResNet152(dermoscopy) — average logits."""

    def __init__(self, num_classes: int, pretrained: bool = True):
        super().__init__()
        if not TIMM_AVAILABLE:
            raise ImportError("timm required")
        self.clinical_branch  = timm.create_model("resnet152.a2_in1k", pretrained=pretrained, num_classes=num_classes)
        self.dermoscopy_branch = timm.create_model("resnet152.a2_in1k", pretrained=pretrained, num_classes=num_classes)

    def forward(self, clinical_img, dermo_img):
        return (self.clinical_branch(clinical_img) + self.dermoscopy_branch(dermo_img)) / 2.0


class MultimodalConcatModel(nn.Module):
    """B4: Concat [z_clinical, z_dermo, z_meta, z_text] → linear head."""

    def __init__(self, num_classes: int, meta_dim: int = 45, text_dim: int = 768):
        super().__init__()
        if not TIMM_AVAILABLE:
            raise ImportError("timm required")
        # Visual encoders — num_classes=0 to get embedding
        self.clinical_enc  = timm.create_model("resnet152.a2_in1k", pretrained=True, num_classes=0)
        self.dermo_enc     = timm.create_model("resnet152.a2_in1k", pretrained=True, num_classes=0)
        clin_dim  = self.clinical_enc.num_features
        dermo_dim = self.dermo_enc.num_features
        total_dim = clin_dim + dermo_dim + meta_dim + text_dim
        self.head = nn.Sequential(
            nn.Linear(total_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes),
        )

    def forward(self, clinical_img, dermo_img, meta_feat, text_feat):
        z_clin  = self.clinical_enc(clinical_img)
        z_dermo = self.dermo_enc(dermo_img)
        z = torch.cat([z_clin, z_dermo, meta_feat, text_feat], dim=-1)
        return self.head(z)


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------
def train_one_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int,
    lr: float,
    num_classes: int,
    model_name: str,
    save_dir: Path,
    device: torch.device,
    early_stop_patience: int = 10,
):
    """Unified training loop used by all baselines.

    Rules per spec:
    - Focal loss (gamma=2.0) + inverse-frequency class weights
    - AdamW + CosineAnnealingLR
    - Gradient clipping max_norm=1.0
    - AMP (autocast) if CUDA available
    - Early stopping on val macro-F1 (NOT loss), patience=10
    - Save best + last checkpoint
    """
    model.to(device)

    # Compute class weights from training labels
    all_train_labels = []
    for batch in train_loader:
        all_train_labels.extend(batch["label"].tolist())
    class_weights = compute_class_weights(all_train_labels, num_classes).to(device)
    criterion = FocalLoss(gamma=2.0, weight=class_weights)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    scaler = torch.amp.GradScaler(enabled=torch.cuda.is_available())

    best_f1 = 0.0
    best_state = None
    patience_counter = 0
    save_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[{model_name}] Starting training on {device} | epochs={epochs} | lr={lr}")

    for epoch in range(epochs):
        # ---- Train ----
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            images = batch["image"].to(device)
            labels = batch["label"].to(device)
            optimizer.zero_grad()
            with torch.amp.autocast(device_type=device.type, enabled=torch.cuda.is_available()):
                logits = model(images)
                loss = criterion(logits, labels)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
            train_loss += loss.item()
        scheduler.step()
        avg_train_loss = train_loss / max(len(train_loader), 1)

        # ---- Validate ----
        model.eval()
        all_preds, all_labels = [], []
        with torch.no_grad():
            for batch in val_loader:
                images = batch["image"].to(device)
                labels = batch["label"].to(device)
                with torch.amp.autocast(device_type=device.type, enabled=torch.cuda.is_available()):
                    logits = model(images)
                preds = logits.argmax(dim=1)
                all_preds.extend(preds.cpu().tolist())
                all_labels.extend(labels.cpu().tolist())

        val_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
        val_acc = balanced_accuracy_score(all_labels, all_preds)

        print(f"  Epoch {epoch+1:3d}/{epochs} | TrainLoss={avg_train_loss:.4f} | ValF1={val_f1:.4f} | ValAcc={val_acc:.4f}")

        if val_f1 > best_f1:
            best_f1 = val_f1
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
            torch.save(best_state, save_dir / f"{model_name}_best.pt")
            print(f"  ✓ New best saved (F1={best_f1:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= early_stop_patience:
                print(f"  Early stopping at epoch {epoch+1} (patience={early_stop_patience})")
                break

    # Save last
    torch.save(model.state_dict(), save_dir / f"{model_name}_last.pt")

    # Restore best for return
    if best_state:
        model.load_state_dict(best_state)

    print(f"[{model_name}] Training complete. Best Val Macro-F1: {best_f1:.4f}")
    return model, best_f1


# ---------------------------------------------------------------------------
# Baseline B6: Ensemble majority vote (requires trained B1, B2, B5)
# ---------------------------------------------------------------------------
def run_majority_vote_eval(checkpoint_dir: Path, val_loader: DataLoader, num_classes: int, device: torch.device):
    """Load B1, B2, B5 checkpoints and run majority vote on val set."""
    b1 = build_resnet152(num_classes, pretrained=False)
    b2 = build_swin_tiny(num_classes, pretrained=False)

    b1_ckpt = checkpoint_dir / "B1_best.pt"
    b2_ckpt = checkpoint_dir / "B2_best.pt"
    b5_ckpt = checkpoint_dir / "B5_best.pt"

    missing = [p for p in [b1_ckpt, b2_ckpt, b5_ckpt] if not p.exists()]
    if missing:
        print(f"[B6] Missing checkpoints: {missing}. Train B1, B2, B5 first.")
        return None

    b1.load_state_dict(torch.load(b1_ckpt, map_location=device))
    b2.load_state_dict(torch.load(b2_ckpt, map_location=device))
    # B5 (PanDerm) reuses ResNet152 shape for simplicity in baseline eval
    b5 = build_resnet152(num_classes, pretrained=False)
    b5.load_state_dict(torch.load(b5_ckpt, map_location=device))

    for m in [b1, b2, b5]:
        m.to(device).eval()

    all_preds, all_labels = [], []
    with torch.no_grad():
        for batch in val_loader:
            images = batch["image"].to(device)
            labels = batch["label"].to(device)
            p1 = b1(images).argmax(dim=1)
            p2 = b2(images).argmax(dim=1)
            p5 = b5(images).argmax(dim=1)
            # Majority vote
            stacked = torch.stack([p1, p2, p5], dim=1)
            voted = torch.mode(stacked, dim=1).values
            all_preds.extend(voted.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())

    val_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
    val_acc = balanced_accuracy_score(all_labels, all_preds)
    print(f"[B6 Ensemble] Val Macro-F1: {val_f1:.4f} | Val Balanced Acc: {val_acc:.4f}")
    return val_f1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Train DERMA-GUARD baseline ladder (B1–B6)")
    parser.add_argument("--baseline", type=str, default="all",
                        choices=["all", "B1", "B2", "B3", "B4", "B5", "B6"],
                        help="Which baseline to train")
    parser.add_argument("--dataset",    type=str, default="derm7pt",
                        choices=["derm7pt", "pad_ufes"],
                        help="Dataset to train on")
    parser.add_argument("--num-classes", type=int, default=7,    help="Number of output classes")
    parser.add_argument("--epochs",      type=int, default=50,   help="Training epochs")
    parser.add_argument("--batch-size",  type=int, default=32,   help="Batch size")
    parser.add_argument("--lr",          type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--seed",        type=int, default=42,   help="Random seed")
    parser.add_argument("--output-dir",  type=str, default="outputs/checkpoints/baselines",
                        help="Directory for checkpoints")
    args = parser.parse_args()

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    save_dir = project_root / args.output_dir
    save_dir.mkdir(parents=True, exist_ok=True)

    print(f"DERMA-GUARD Baseline Training")
    print(f"Device: {device} | Dataset: {args.dataset} | Baseline: {args.baseline}")

    # ---- Load data ----
    try:
        from src.data.dataset import create_dataloaders
        from src.data.preprocessing import load_metadata, preprocess_metadata
        from src.data.augmentation import get_train_transforms, get_eval_transforms

        splits_path = project_root / "data" / "splits"
        if args.dataset == "derm7pt":
            from src.data.derm7pt import load_derm7pt_splits
            dataloaders = load_derm7pt_splits(
                data_dir=project_root / "data" / "raw" / "derm7pt",
                batch_size=args.batch_size,
                num_workers=0,
            )
        else:  # pad_ufes
            train_split = json.load(open(splits_path / "padufes_train.json"))
            val_split   = json.load(open(splits_path / "padufes_val.json"))
            train_transform = get_train_transforms(224)
            eval_transform  = get_eval_transforms(224)
            train_loader = DataLoader(
                ImageDataset(train_split, transform=train_transform),
                batch_size=args.batch_size, shuffle=True, num_workers=0, pin_memory=True
            )
            val_loader = DataLoader(
                ImageDataset(val_split, transform=eval_transform),
                batch_size=args.batch_size, shuffle=False, num_workers=0, pin_memory=True
            )
            dataloaders = {"train": train_loader, "val": val_loader}

    except Exception as exc:
        print(f"[WARNING] Could not load real data: {exc}")
        print("Proceeding in stub mode — no actual training will occur.")
        print("Run 01_prepare_data.py and dataset_audit.py first.")
        return

    train_loader = dataloaders["train"]
    val_loader   = dataloaders["val"]
    baselines_to_run = ["B1", "B2", "B3", "B4", "B5"] if args.baseline == "all" else [args.baseline]

    results = {}

    for b in baselines_to_run:
        print(f"\n{'='*60}")
        print(f"  Training Baseline {b}: {_BASELINE_DESCRIPTIONS[b]}")
        print(f"{'='*60}")

        if b == "B1":
            model = build_resnet152(args.num_classes)
            _, f1 = train_one_model(model, train_loader, val_loader,
                                    args.epochs, args.lr, args.num_classes,
                                    "B1", save_dir, device)
            results["B1"] = f1

        elif b == "B2":
            model = build_swin_tiny(args.num_classes)
            _, f1 = train_one_model(model, train_loader, val_loader,
                                    args.epochs, args.lr, args.num_classes,
                                    "B2", save_dir, device)
            results["B2"] = f1

        elif b == "B3":
            print("B3 (Late Fusion) requires paired clinical+dermoscopy batches.")
            print("Skipped in single-image mode. Use --dataset derm7pt with paired loader.")

        elif b == "B4":
            print("B4 (Multimodal Concat) requires meta+text features alongside images.")
            print("Skipped in single-image mode. Run after feature extraction.")

        elif b == "B5":
            # PanDerm fine-tuned: use ResNet152 architecture as proxy backbone
            # Replace with actual PanDerm encoder once weights are downloaded
            print("B5: Using ResNet152 as PanDerm proxy (replace with actual PanDerm encoder)")
            model = build_resnet152(args.num_classes, pretrained=True)
            _, f1 = train_one_model(model, train_loader, val_loader,
                                    args.epochs, args.lr * 0.1, args.num_classes,
                                    "B5", save_dir, device)
            results["B5"] = f1

        elif b == "B6":
            print("B6: Running ensemble majority vote (requires B1, B2, B5 trained)")
            f1 = run_majority_vote_eval(save_dir, val_loader, args.num_classes, device)
            if f1:
                results["B6"] = f1

    # Save results summary
    summary_path = save_dir / "baseline_results.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nBaseline results saved to {summary_path}")
    print("\nSummary:")
    for b, f1 in results.items():
        print(f"  {b}: Val Macro-F1 = {f1:.4f}")


_BASELINE_DESCRIPTIONS = {
    "B1": "ResNet152 — clinical image only, standard Focal CE",
    "B2": "Swin-Tiny — clinical image only, standard Focal CE",
    "B3": "Late Fusion — ResNet152(clinical) + ResNet152(dermo), average logits",
    "B4": "Multimodal Concat — [z_clin, z_derm, z_meta, z_text] → linear head",
    "B5": "PanDerm Fine-tuned — PanDerm encoder + linear head",
    "B6": "Ensemble Majority Vote — majority vote over B1+B2+B5",
}


if __name__ == "__main__":
    main()

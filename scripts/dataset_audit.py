"""Dataset Audit — DERMA-GUARD v4.0.

Computes SHA-256 and perceptual hash for every image, flags duplicates
across datasets, and produces audit artifacts.

Usage:
    python scripts/dataset_audit.py --config configs/base.yaml
    
BLOCKS training if collisions are detected (exit code 1).
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hex digest for a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def phash_file(path: Path) -> str:
    """Compute perceptual hash for an image file."""
    try:
        import imagehash
        from PIL import Image
        img = Image.open(path).convert("RGB")
        return str(imagehash.phash(img))
    except ImportError:
        raise ImportError("imagehash not installed. Run: pip install imagehash")


def audit_images(image_dirs: Dict[str, Path]) -> Tuple[List[dict], Dict]:
    """
    Audit all images in the given directories.

    Args:
        image_dirs: mapping of dataset_name → image directory path

    Returns:
        records: list of dicts {dataset, path, sha256, phash}
        report:  summary statistics dict
    """
    records = []
    for dataset_name, img_dir in image_dirs.items():
        if not img_dir.exists():
            print(f"Warning: image directory not found: {img_dir}")
            continue
        extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
        paths = [p for p in img_dir.rglob("*") if p.suffix.lower() in extensions]
        print(f"Auditing {dataset_name}: {len(paths)} images …")
        for i, p in enumerate(paths):
            if (i + 1) % 200 == 0:
                print(f"  {i+1}/{len(paths)}")
            try:
                records.append({
                    "dataset": dataset_name,
                    "path": str(p),
                    "sha256": sha256_file(p),
                    "phash": phash_file(p),
                })
            except Exception as e:
                print(f"  Warning: could not audit {p}: {e}")

    # Detect collisions
    sha256_map = defaultdict(list)
    phash_map = defaultdict(list)
    for r in records:
        sha256_map[r["sha256"]].append(r)
        phash_map[r["phash"]].append(r)

    sha256_collisions = {k: v for k, v in sha256_map.items() if len(v) > 1}
    phash_collisions = {k: v for k, v in phash_map.items() if len(v) > 1}

    report = {
        "total_images": len(records),
        "per_dataset": {ds: sum(1 for r in records if r["dataset"] == ds)
                        for ds in image_dirs},
        "sha256_collisions": len(sha256_collisions),
        "phash_collisions": len(phash_collisions),
        "collision_details": {
            "sha256": [[r["path"] for r in v] for v in sha256_collisions.values()],
            "phash":  [[r["path"] for r in v] for v in phash_collisions.values()],
        },
        "clean": len(sha256_collisions) == 0 and len(phash_collisions) == 0,
    }
    return records, report


def plot_missingness(metadata_df: pd.DataFrame, output_path: Path) -> None:
    """Plot missingness heatmap for metadata fields."""
    missing = metadata_df.isnull().mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(10, max(4, len(missing) * 0.3)))
    missing.plot(kind="barh", ax=ax, color="steelblue")
    ax.set_xlabel("Fraction Missing")
    ax.set_title("Metadata Field Missingness")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved missingness plot → {output_path}")


def plot_class_distribution(metadata_df: pd.DataFrame, label_col: str, output_path: Path) -> None:
    """Plot class distribution bar chart."""
    counts = metadata_df[label_col].value_counts()
    fig, ax = plt.subplots(figsize=(8, 4))
    counts.plot(kind="bar", ax=ax, color="teal")
    ax.set_ylabel("Count")
    ax.set_title("Class Distribution")
    ax.tick_params(axis="x", rotation=30)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved class distribution plot → {output_path}")


def main():
    parser = argparse.ArgumentParser(description="DERMA-GUARD Dataset Audit")
    parser.add_argument("--config", type=str, default="configs/base.yaml")
    parser.add_argument("--output_dir", type=str, default="outputs/audit")
    parser.add_argument("--skip_phash", action="store_true", help="Skip slow perceptual hash")
    args = parser.parse_args()

    output_dir = project_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Discover image directories
    image_dirs = {}
    pad_ufes_dir = project_root / "data" / "raw" / "images"
    if pad_ufes_dir.exists():
        image_dirs["pad_ufes"] = pad_ufes_dir
    derm7pt_clinical = project_root / "data" / "raw" / "derm7pt" / "images" / "derm"
    derm7pt_dermo = project_root / "data" / "raw" / "derm7pt" / "images" / "clinic"
    if derm7pt_clinical.exists():
        image_dirs["derm7pt_clinical"] = derm7pt_clinical
    if derm7pt_dermo.exists():
        image_dirs["derm7pt_dermoscopy"] = derm7pt_dermo

    if not image_dirs:
        print("No image directories found. Place data in data/raw/ first.")
        print("Expected: data/raw/images/ (PAD-UFES-20) and/or data/raw/derm7pt/")
        sys.exit(0)

    # Run audit
    records, report = audit_images(image_dirs)

    # Save JSON report
    report_path = output_dir / "dataset_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nAudit report saved → {report_path}")
    print(f"  Total images: {report['total_images']}")
    print(f"  SHA-256 collisions: {report['sha256_collisions']}")
    print(f"  Perceptual hash collisions: {report['phash_collisions']}")

    # Metadata missingness (PAD-UFES-20 only for now)
    meta_path = project_root / "data" / "raw" / "metadata.csv"
    if meta_path.exists():
        df = pd.read_csv(meta_path)
        plot_missingness(df, output_dir / "missingness.png")
        label_col = "diagnostic" if "diagnostic" in df.columns else df.columns[-1]
        plot_class_distribution(df, label_col, output_dir / "class_distribution.png")
    else:
        print("metadata.csv not found — skipping missingness/class plots.")

    # BLOCK training if not clean
    if not report["clean"]:
        print("\n[BLOCK] Dataset audit FAILED: duplicate images detected!")
        print("Resolve collisions before running training.")
        sys.exit(1)
    else:
        print("\n[PASS] Dataset is clean. Training may proceed.")
        sys.exit(0)


if __name__ == "__main__":
    main()

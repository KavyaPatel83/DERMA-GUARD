"""Derm7pt Dataset loader — DERMA-GUARD v4.0.

Supports the official Derm7pt split index files (413 train / 203 val / 395 test).
NEVER regenerates splits.

Expected data layout:
    data/raw/derm7pt/
        meta/
            derm7pt_core_df.csv          ← main metadata file from official download
        images/
            derm/                        ← dermoscopy images
            clinic/                      ← clinical images

Official split index files (if provided as separate CSVs/JSONs):
    data/raw/derm7pt/meta/train_indexes.csv
    data/raw/derm7pt/meta/val_indexes.csv
    data/raw/derm7pt/meta/test_indexes.csv
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset


DERM7PT_CLASSES = [
    "nevus",
    "melanoma",
    "basal_cell_carcinoma",
    "squamous_cell_carcinoma",
    "seborrheic_keratosis",
    "dermatofibroma",
    "vascular_lesion",
]

CLASS2IDX = {c: i for i, c in enumerate(DERM7PT_CLASSES)}

# Canonical column names in the official CSV
_LABEL_COL = "diagnosis"   # may vary — adapt to actual column name
_IMG_DERM_COL = "derm"     # relative path to dermoscopy image
_IMG_CLINIC_COL = "clinic" # relative path to clinical image


class Derm7ptDataset(Dataset):
    """PyTorch Dataset for Derm7pt.

    Args:
        root: path to data/raw/derm7pt/
        split: 'train' | 'val' | 'test'
        transform: torchvision/albumentations transform for images
        include_clinical: whether to load clinical images
        include_dermo: whether to load dermoscopy images
    """

    def __init__(
        self,
        root: str | Path,
        split: str = "train",
        transform=None,
        include_clinical: bool = True,
        include_dermo: bool = True,
        tokenizer=None,
        max_text_length: int = 128,
    ):
        self.root = Path(root)
        self.split = split
        self.transform = transform
        self.include_clinical = include_clinical
        self.include_dermo = include_dermo
        self.tokenizer = tokenizer
        self.max_text_length = max_text_length

        meta_dir = self.root / "meta"
        if not meta_dir.exists():
            raise FileNotFoundError(
                f"Derm7pt metadata dir not found: {meta_dir}\n"
                "Download the Derm7pt dataset and place it in data/raw/derm7pt/"
            )

        # Load official split index files
        self.df = self._load_official_split(meta_dir)
        print(f"Derm7pt {split}: {len(self.df)} cases loaded.")

    def _load_official_split(self, meta_dir: Path) -> pd.DataFrame:
        """Load the official Derm7pt split.

        Tries three strategies in order:
        1. Official {split}_indexes.csv with row indices
        2. Pre-split CSV files {split}.csv
        3. derm7pt_core_df.csv with a 'split' column
        """
        main_csv = meta_dir / "derm7pt_core_df.csv"
        if not main_csv.exists():
            raise FileNotFoundError(
                f"derm7pt_core_df.csv not found in {meta_dir}.\n"
                "Download from: https://derm.cs.sfu.ca/Download.html"
            )

        full_df = pd.read_csv(main_csv)

        # Strategy 1: official index files
        index_file = meta_dir / f"{self.split}_indexes.csv"
        if index_file.exists():
            idxs = pd.read_csv(index_file, header=None)[0].tolist()
            return full_df.iloc[idxs].reset_index(drop=True)

        # Strategy 2: pre-split CSVs
        split_csv = meta_dir / f"{self.split}.csv"
        if split_csv.exists():
            return pd.read_csv(split_csv).reset_index(drop=True)

        # Strategy 3: split column
        if "split" in full_df.columns:
            return full_df[full_df["split"] == self.split].reset_index(drop=True)

        raise FileNotFoundError(
            f"Could not find official Derm7pt split files for '{self.split}'.\n"
            f"Expected one of:\n"
            f"  {meta_dir}/{self.split}_indexes.csv\n"
            f"  {meta_dir}/{self.split}.csv\n"
            f"  or a 'split' column in derm7pt_core_df.csv\n"
            "NEVER regenerate splits manually. Use official files."
        )

    def _load_image(self, relative_path: str) -> Optional[torch.Tensor]:
        """Load an image by relative path from root/images/."""
        if not relative_path or pd.isna(relative_path):
            return None
        full_path = self.root / "images" / relative_path
        if not full_path.exists():
            return None
        try:
            img = Image.open(full_path).convert("RGB")
            if self.transform is not None:
                img = self.transform(img)
            return img
        except Exception as e:
            print(f"Warning: could not load image {full_path}: {e}")
            return None

    def _get_label(self, row: pd.Series) -> int:
        """Map diagnosis string to class index."""
        diag = str(row.get(_LABEL_COL, "nevus")).lower().replace(" ", "_")
        # Handle common aliases
        aliases = {
            "nv": "nevus", "mel": "melanoma", "bcc": "basal_cell_carcinoma",
            "bkl": "seborrheic_keratosis", "df": "dermatofibroma",
            "vasc": "vascular_lesion", "akiec": "squamous_cell_carcinoma",
        }
        diag = aliases.get(diag, diag)
        return CLASS2IDX.get(diag, 0)

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Dict:
        row = self.df.iloc[idx]
        sample: Dict = {
            "case_id": str(row.get("case_num", idx)),
            "label": self._get_label(row),
            "dataset": "derm7pt",
        }

        # Clinical image
        clinical_img = None
        if self.include_clinical:
            clinical_img = self._load_image(str(row.get(_IMG_CLINIC_COL, "")))
        sample["clinical_image"] = clinical_img if clinical_img is not None else torch.zeros(3, 224, 224)
        sample["clinical_available"] = clinical_img is not None

        # Dermoscopy image
        dermo_img = None
        if self.include_dermo:
            dermo_img = self._load_image(str(row.get(_IMG_DERM_COL, "")))
        sample["dermoscopy_image"] = dermo_img if dermo_img is not None else torch.zeros(3, 224, 224)
        sample["dermo_available"] = dermo_img is not None

        # Text tokenization (no synthetic text for Derm7pt — metadata only)
        notes = str(row.get("notes", ""))
        if self.tokenizer and notes.strip():
            enc = self.tokenizer(
                notes,
                max_length=self.max_text_length,
                padding="max_length",
                truncation=True,
                return_tensors="pt",
            )
            sample["text_input_ids"] = enc["input_ids"].squeeze(0)
            sample["text_attention_mask"] = enc["attention_mask"].squeeze(0)
            sample["text_available"] = True
        else:
            sample["text_input_ids"] = torch.zeros(self.max_text_length, dtype=torch.long)
            sample["text_attention_mask"] = torch.zeros(self.max_text_length, dtype=torch.long)
            sample["text_available"] = False

        # Metadata flags
        sample["metadata_available"] = True  # Derm7pt has structured metadata

        return sample

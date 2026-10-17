"""src/evidence/missingness.py — Missingness flags for DERMA-GUARD v4.0."""
from __future__ import annotations

from typing import Dict, List, Optional

import torch


ALL_MODALITIES = ["clinical_image", "dermoscopy_image", "metadata", "text"]


def compute_missingness(
    clinical_available: bool,
    dermo_available: bool,
    meta_available: bool,
    text_available: bool,
) -> Dict:
    """Compute missingness binary flags M.

    Returns:
        dict with:
            flags:             {modality: bool}  True = available
            missing_list:      List[str] of missing modality names
            missing_count:     int
            all_missing:       bool — if True, pipeline should ABSTAIN
            missing_mask:      torch.Tensor [4] binary (1=available, 0=missing)
                               order: [clinical, dermoscopy, metadata, text]
    """
    flags = {
        "clinical_image": clinical_available,
        "dermoscopy_image": dermo_available,
        "metadata": meta_available,
        "text": text_available,
    }
    missing_list = [m for m, avail in flags.items() if not avail]
    missing_count = len(missing_list)
    all_missing = missing_count == len(ALL_MODALITIES)

    missing_mask = torch.tensor(
        [float(flags[m]) for m in ALL_MODALITIES], dtype=torch.float32
    )  # 1 = available, 0 = missing

    return {
        "flags": flags,
        "missing_list": missing_list,
        "missing_count": missing_count,
        "all_missing": all_missing,
        "missing_mask": missing_mask,
    }

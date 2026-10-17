"""src/evidence/consistency.py — Consistency (C) and conflict detection."""
from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Tuple

import torch
import torch.nn.functional as F


def js_divergence(p: torch.Tensor, q: torch.Tensor) -> float:
    """Jensen-Shannon divergence between two probability vectors.
    
    JSD(P || Q) = 0.5 * KL(P || M) + 0.5 * KL(Q || M)  where M = 0.5*(P+Q)
    JSD ∈ [0, log(2)] ≈ [0, 0.693]
    Normalized to [0, 1] by dividing by log(2).
    """
    # Ensure probabilities
    p = F.softmax(p, dim=-1).float()
    q = F.softmax(q, dim=-1).float()
    m = 0.5 * (p + q)
    
    # KL divergences (add epsilon for numerical stability)
    eps = 1e-8
    kl_pm = (p * (p + eps).log() - p * (m + eps).log()).sum()
    kl_qm = (q * (q + eps).log() - q * (m + eps).log()).sum()
    jsd = 0.5 * (kl_pm + kl_qm)
    
    # Normalise to [0, 1]
    return float(jsd.clamp(0.0, 1.0).item())


def compute_consistency(
    predictions: Dict[str, torch.Tensor],
) -> Tuple[float, bool, Dict]:
    """Compute cross-modal consistency score C(x).

    C(x) = 1 - mean_pairwise_JS_divergence(p_i, p_j) for all pairs of available modalities.
    Conflict_flag(x) = True if C(x) < 0.3

    Args:
        predictions: dict of modality_name → logits tensor (K,) or (1, K)

    Returns:
        consistency:    float ∈ [0, 1]  (1 = perfectly consistent)
        conflict_flag:  bool
        conflict_details: dict with per-pair JSD values
    """
    names = list(predictions.keys())
    if len(names) < 2:
        return 1.0, False, {}

    pairs_jsd = {}
    for n1, n2 in combinations(names, 2):
        l1 = predictions[n1].flatten()[:predictions[n1].shape[-1]]
        l2 = predictions[n2].flatten()[:predictions[n2].shape[-1]]
        # Pad to same length if needed
        K = max(l1.shape[0], l2.shape[0])
        if l1.shape[0] < K:
            l1 = F.pad(l1, (0, K - l1.shape[0]))
        if l2.shape[0] < K:
            l2 = F.pad(l2, (0, K - l2.shape[0]))
        pairs_jsd[f"{n1}|{n2}"] = js_divergence(l1, l2)

    mean_jsd = sum(pairs_jsd.values()) / len(pairs_jsd)
    consistency = float(1.0 - mean_jsd)
    conflict_flag = consistency < 0.3

    return consistency, conflict_flag, {
        "mean_jsd": mean_jsd,
        "pair_jsds": pairs_jsd,
        "most_conflicting_pair": max(pairs_jsd, key=pairs_jsd.get) if pairs_jsd else None,
    }

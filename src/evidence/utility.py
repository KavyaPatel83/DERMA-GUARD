"""src/evidence/utility.py — Utility (U) computation for DERMA-GUARD v4.0.

CRITICAL: U requires ground truth y.
  - RETROSPECTIVE/RESEARCH ONLY. Never used at inference time.
  - For deployment, approximate U from training-set statistics.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

import torch
import torch.nn.functional as F


def compute_utility_retrospective(
    model_fn: Callable,
    case_input: Dict,
    ground_truth: torch.Tensor,
    loss_fn: Callable,
    all_modality_names: List[str],
) -> Dict[str, float]:
    """Compute U_m for each modality m (RESEARCH USE ONLY).

    U_m(x) = Loss(pred_without_m, y) - Loss(pred_all, y)

    A positive U_m means the modality reduces loss (is useful).
    A negative or zero U_m means the modality adds noise or is irrelevant.

    Args:
        model_fn: callable(case_input) → logits
        case_input: dict with all modality inputs
        ground_truth: (B,) labels
        loss_fn: loss function callable(logits, labels) → scalar
        all_modality_names: list of modality keys in case_input

    Returns:
        dict {modality_name: utility_score}

    WARNING: This function is ONLY for retrospective research analysis.
    It must NEVER be called during deployed inference (requires ground truth).
    """
    import warnings
    warnings.warn(
        "[Utility] compute_utility_retrospective is for research ONLY. "
        "Do NOT call during deployed inference — it requires ground truth labels.",
        stacklevel=2,
    )

    with torch.no_grad():
        # Baseline: all modalities
        logits_all = model_fn(case_input)
        loss_all = loss_fn(logits_all, ground_truth).item()

    utility_scores: Dict[str, float] = {}
    for modality in all_modality_names:
        # Create ablated input (zero out the modality)
        ablated = dict(case_input)
        ablated[modality] = torch.zeros_like(case_input[modality])
        with torch.no_grad():
            logits_without = model_fn(ablated)
            loss_without = loss_fn(logits_without, ground_truth).item()
        utility_scores[modality] = float(loss_without - loss_all)

    return utility_scores


def approximate_utility_from_training(
    training_utility_stats: Optional[Dict[str, Dict[str, float]]] = None,
    diagnosis: Optional[int] = None,
) -> Dict[str, float]:
    """Approximate U from training-set statistics for deployment.

    At training time, compute utility for all training cases and store
    per-diagnosis mean utility. At inference, look up by predicted diagnosis.

    Args:
        training_utility_stats: {modality: {diagnosis_id: mean_utility}}
        diagnosis: predicted diagnosis class index

    Returns:
        approximate utility dict {modality: float}
    """
    if training_utility_stats is None or diagnosis is None:
        # Uniform utility as fallback
        return {m: 0.5 for m in ["image", "dermoscopy", "metadata", "text"]}

    result = {}
    for modality, diag_stats in training_utility_stats.items():
        key = str(diagnosis)
        result[modality] = float(diag_stats.get(key, diag_stats.get("mean", 0.5)))
    return result

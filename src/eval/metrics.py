"""
src/eval/metrics.py — Per-class and aggregate evaluation metrics.

Implements: accuracy, macro-F1, per-class precision/recall/F1, ECE, Brier, abstention rate.
All metrics are computed on case-level (not modality-variant level).
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    f1_score,
    precision_recall_fscore_support,
)


def compute_macro_f1(y_true: List[int], y_pred: List[int]) -> float:
    """Macro-averaged F1 score."""
    return float(f1_score(y_true, y_pred, average="macro", zero_division=0))


def compute_per_class_metrics(
    y_true: List[int],
    y_pred: List[int],
    class_names: Optional[List[str]] = None,
    probs: Optional[np.ndarray] = None,
) -> Dict:
    """Compute per-class and aggregate metrics.

    Always reports per-class metrics (as required by spec).
    Also computes ECE and Brier if probs provided.

    Args:
        y_true:      ground truth labels (N,)
        y_pred:      predicted labels (N,)
        class_names: optional list of class name strings
        probs:       (N, K) softmax probabilities for calibration metrics

    Returns:
        dict with per_class, macro, weighted, balanced_accuracy, [ece, brier]
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    prec, rec, f1, support = precision_recall_fscore_support(
        y_true, y_pred, average=None, zero_division=0
    )

    n_classes = max(y_true.max(), y_pred.max()) + 1
    names = class_names or [str(i) for i in range(n_classes)]

    per_class = {}
    for i in range(min(len(prec), n_classes)):
        name = names[i] if i < len(names) else str(i)
        per_class[name] = {
            "precision": float(prec[i]),
            "recall": float(rec[i]),
            "f1": float(f1[i]),
            "support": int(support[i]),
        }

    result = {
        "per_class": per_class,
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "n_samples": int(len(y_true)),
    }

    if probs is not None:
        from src.stress.benchmark import compute_ece, compute_brier
        result["ece"] = compute_ece(probs, y_true)
        result["brier"] = compute_brier(probs, y_true)

    return result


def compute_abstention_metrics(
    results: List[Dict],
    y_true: List[int],
) -> Dict:
    """Compute abstention-aware metrics.

    Args:
        results:  list of PipelineResult dicts (with 'action', 'diagnosis')
        y_true:   ground truth labels

    Returns:
        dict with abstention_rate, coverage, accuracy_on_covered
    """
    n = len(results)
    abstained = sum(1 for r in results if r.get("action") in ("ABSTAIN", "ESCALATE"))
    covered_mask = [r.get("action") in ("ACCEPT", "ARBITRATE") for r in results]
    covered_preds = [r.get("diagnosis", -1) for r, m in zip(results, covered_mask) if m]
    covered_true = [y for y, m in zip(y_true, covered_mask) if m]

    accuracy_on_covered = float(
        accuracy_score(covered_true, covered_preds) if covered_true else 0.0
    )

    return {
        "abstention_rate": abstained / max(n, 1),
        "coverage": sum(covered_mask) / max(n, 1),
        "accuracy_on_covered": accuracy_on_covered,
        "n_abstained": abstained,
        "n_covered": sum(covered_mask),
    }

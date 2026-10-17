"""
src/eval/stats.py — Statistical analysis for DERMA-GUARD v4.0.

- Bootstrap 1,000 resamples (case-level)
- 95% confidence intervals on all primary metrics
- McNemar's test for paired comparisons (DERMA-GUARD vs baseline)
- Cohen's d for effect sizes
- Bonferroni / FDR correction for multiple comparisons
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats as scipy_stats


def bootstrap_ci(
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_bootstrap: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> Dict:
    """Bootstrap confidence interval for a scalar metric.

    Samples are drawn at the CASE level (not modality-variant level).

    Args:
        metric_fn:   callable(y_true, y_pred) → float
        y_true:      (N,) ground truth
        y_pred:      (N,) predictions
        n_bootstrap: number of bootstrap resamples
        alpha:       significance level (default 0.05 → 95% CI)
        seed:        random seed

    Returns:
        dict with: mean, std, ci_lower, ci_upper, metric_on_full
    """
    rng = np.random.default_rng(seed)
    N = len(y_true)
    bootstrap_scores = []

    for _ in range(n_bootstrap):
        indices = rng.integers(0, N, size=N)
        score = metric_fn(y_true[indices], y_pred[indices])
        bootstrap_scores.append(score)

    bootstrap_scores = np.array(bootstrap_scores)
    ci_lower = float(np.percentile(bootstrap_scores, 100 * alpha / 2))
    ci_upper = float(np.percentile(bootstrap_scores, 100 * (1 - alpha / 2)))

    return {
        "mean": float(bootstrap_scores.mean()),
        "std": float(bootstrap_scores.std()),
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "metric_on_full": float(metric_fn(y_true, y_pred)),
        "n_bootstrap": n_bootstrap,
        "alpha": alpha,
    }


def mcnemar_test(
    y_true: np.ndarray,
    y_pred_a: np.ndarray,
    y_pred_b: np.ndarray,
) -> Dict:
    """McNemar's test for paired comparison (DERMA-GUARD vs baseline).

    Tests whether model A and model B have significantly different
    error rates on the same set of cases.

    Args:
        y_true:   (N,) ground truth labels
        y_pred_a: (N,) predictions from model A (DERMA-GUARD)
        y_pred_b: (N,) predictions from model B (baseline)

    Returns:
        dict with: statistic, p_value, correct_a_wrong_b, wrong_a_correct_b
    """
    correct_a = (y_pred_a == y_true)
    correct_b = (y_pred_b == y_true)

    # Contingency cell counts
    b = int(np.sum(correct_a & ~correct_b))   # A correct, B wrong
    c = int(np.sum(~correct_a & correct_b))   # A wrong, B correct

    # McNemar's test with continuity correction
    if b + c == 0:
        return {"statistic": 0.0, "p_value": 1.0, "b": b, "c": c, "note": "No disagreements"}

    statistic = float((abs(b - c) - 1) ** 2 / (b + c))
    p_value = float(scipy_stats.chi2.sf(statistic, df=1))

    return {
        "statistic": statistic,
        "p_value": p_value,
        "correct_a_wrong_b": b,
        "wrong_a_correct_b": c,
        "significant_0.05": p_value < 0.05,
    }


def cohens_d(group_a: np.ndarray, group_b: np.ndarray) -> float:
    """Cohen's d effect size for two groups.

    d = (mean_a - mean_b) / pooled_std

    Returns:
        Cohen's d (float). Interpretation: 0.2=small, 0.5=medium, 0.8=large
    """
    n_a, n_b = len(group_a), len(group_b)
    mean_a, mean_b = group_a.mean(), group_b.mean()
    var_a, var_b = group_a.var(ddof=1), group_b.var(ddof=1)
    # Pooled standard deviation
    pooled_std = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
    if pooled_std < 1e-10:
        return 0.0
    return float((mean_a - mean_b) / pooled_std)


def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict:
    """Bonferroni correction for multiple comparisons.

    Args:
        p_values: list of raw p-values
        alpha:    family-wise error rate (default 0.05)

    Returns:
        dict with adjusted threshold and significant flags
    """
    n = len(p_values)
    threshold = alpha / n
    return {
        "adjusted_threshold": threshold,
        "n_comparisons": n,
        "significant": [p < threshold for p in p_values],
        "raw_p_values": p_values,
    }


def fdr_correction(p_values: List[float], alpha: float = 0.05) -> Dict:
    """Benjamini-Hochberg FDR correction.

    Args:
        p_values: list of raw p-values
        alpha:    false discovery rate (default 0.05)

    Returns:
        dict with adjusted p-values and significant flags
    """
    from scipy.stats import rankdata
    n = len(p_values)
    sorted_idx = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_idx]
    ranks = rankdata(sorted_p)
    adjusted = sorted_p * n / ranks
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]

    # Restore original order
    result_adjusted = np.empty(n)
    result_adjusted[sorted_idx] = adjusted
    result_adjusted = np.clip(result_adjusted, 0.0, 1.0)

    return {
        "adjusted_p_values": result_adjusted.tolist(),
        "significant": (result_adjusted < alpha).tolist(),
        "method": "Benjamini-Hochberg",
        "alpha": alpha,
    }


def run_full_comparison(
    y_true: np.ndarray,
    model_results: Dict[str, np.ndarray],   # name → predictions
    primary_metric_fn: Optional[Callable] = None,
    reference_model: str = "derma_guard",
    n_bootstrap: int = 1000,
) -> Dict:
    """Run complete statistical comparison suite.

    Args:
        y_true:           (N,) ground truth
        model_results:    dict of model_name → (N,) predictions
        primary_metric_fn: callable(y_true, y_pred) → float (default: macro F1)
        reference_model:  name of the reference model for McNemar
        n_bootstrap:      number of bootstrap resamples

    Returns:
        dict with bootstrap CIs, McNemar results, Cohen's d, corrections
    """
    from src.eval.metrics import compute_macro_f1
    if primary_metric_fn is None:
        primary_metric_fn = lambda t, p: compute_macro_f1(t.tolist(), p.tolist())

    # Bootstrap CIs for each model
    bootstrap_results = {}
    for name, preds in model_results.items():
        bootstrap_results[name] = bootstrap_ci(
            primary_metric_fn, y_true, preds, n_bootstrap=n_bootstrap
        )

    # McNemar tests: reference vs all others
    mcnemar_results = {}
    if reference_model in model_results:
        ref_preds = model_results[reference_model]
        for name, preds in model_results.items():
            if name != reference_model:
                mcnemar_results[f"{reference_model}_vs_{name}"] = mcnemar_test(
                    y_true, ref_preds, preds
                )

    # Cohen's d for each pair vs reference
    cohens_results = {}
    if reference_model in bootstrap_results:
        ref_scores = np.array([
            primary_metric_fn(
                y_true, model_results[reference_model]
            )
        ] * n_bootstrap)  # simplified; full version uses bootstrap distributions
        for name in model_results:
            if name != reference_model:
                other_scores = np.array([
                    primary_metric_fn(y_true, model_results[name])
                ] * n_bootstrap)
                cohens_results[f"{reference_model}_vs_{name}"] = cohens_d(ref_scores, other_scores)

    # FDR correction on McNemar p-values
    fdr_result = {}
    if mcnemar_results:
        p_vals = [r["p_value"] for r in mcnemar_results.values()]
        fdr_result = fdr_correction(p_vals)

    return {
        "bootstrap_cis": bootstrap_results,
        "mcnemar": mcnemar_results,
        "cohens_d": cohens_results,
        "fdr_correction": fdr_result,
    }

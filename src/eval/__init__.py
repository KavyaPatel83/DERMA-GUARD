"""src/eval/__init__.py — Evaluation package."""
from src.eval.metrics import compute_per_class_metrics, compute_macro_f1
from src.eval.stats import bootstrap_ci, mcnemar_test, cohens_d, bonferroni_correction

__all__ = [
    "compute_per_class_metrics", "compute_macro_f1",
    "bootstrap_ci", "mcnemar_test", "cohens_d", "bonferroni_correction",
]

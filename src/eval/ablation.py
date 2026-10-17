"""
src/eval/ablation.py — Ablation study runner for DERMA-GUARD v4.0.

Implements:
  1. Linear ablation chain:
     image-only → +metadata → +text → +SkinM2Former fusion →
     +Q → +R → +U → +C → +Sufficiency → +Uncertainty → +Acquisition → +Verification

  2. Factorial ablation (Evidence Manager):
     All 2^4 = 16 combinations of {Q, R, C, M}

Reports: mean ± std across 3-5 seeds, bootstrap 95% CIs.
"""
from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.eval.metrics import compute_macro_f1, compute_per_class_metrics
from src.eval.stats import bootstrap_ci


# ---------------------------------------------------------------------------
# Linear ablation chain definition
# ---------------------------------------------------------------------------

LINEAR_CHAIN = [
    {"id": "image_only",        "description": "Image-only baseline (ViT-B/16)"},
    {"id": "+metadata",         "description": "+ Metadata (MetaBlock)"},
    {"id": "+text",             "description": "+ Text (ClinicalBERT)"},
    {"id": "+fusion",           "description": "+ EM-style DiagnosisAdaptiveFusion"},
    {"id": "+quality_Q",        "description": "+ Quality (Q) evidence weighting"},
    {"id": "+reliability_R",    "description": "+ Reliability (R) evidence weighting"},
    {"id": "+utility_U",        "description": "+ Utility (U) approximation"},
    {"id": "+consistency_C",    "description": "+ Consistency (C) cross-modal check"},
    {"id": "+sufficiency",      "description": "+ Evidence sufficiency gating"},
    {"id": "+uncertainty",      "description": "+ Uncertainty-aware consensus"},
    {"id": "+acquisition",      "description": "+ Acquisition policy"},
    {"id": "+verification",     "description": "+ Two-stage report verification"},
]

# Factorial ablation: which components of the Evidence Manager
FACTORIAL_COMPONENTS = ["Q", "R", "C", "M"]


# ---------------------------------------------------------------------------
# Ablation result types
# ---------------------------------------------------------------------------

@dataclass
class AblationStep:
    """Result for one step in the linear ablation chain."""
    step_id: str
    description: str
    macro_f1_mean: float
    macro_f1_std: float
    macro_f1_ci_lower: float
    macro_f1_ci_upper: float
    accuracy_mean: float
    per_class: Dict = field(default_factory=dict)
    notes: str = ""


@dataclass
class FactorialResult:
    """Result for one 2^4 factorial combination."""
    components: Dict[str, bool]  # {Q: True, R: False, C: True, M: True}
    macro_f1: float
    accuracy: float
    abstention_rate: float = 0.0


@dataclass
class AblationReport:
    """Complete ablation study report."""
    linear_chain: List[AblationStep] = field(default_factory=list)
    factorial: List[FactorialResult] = field(default_factory=list)
    n_seeds: int = 3

    def to_dict(self) -> Dict:
        return {
            "n_seeds": self.n_seeds,
            "linear_chain": [
                {
                    "step_id": s.step_id,
                    "description": s.description,
                    "macro_f1_mean": s.macro_f1_mean,
                    "macro_f1_std": s.macro_f1_std,
                    "ci": [s.macro_f1_ci_lower, s.macro_f1_ci_upper],
                    "accuracy_mean": s.accuracy_mean,
                }
                for s in self.linear_chain
            ],
            "factorial_16": [
                {
                    "components": f.components,
                    "macro_f1": f.macro_f1,
                    "accuracy": f.accuracy,
                }
                for f in self.factorial
            ],
        }

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"[Ablation] Report saved → {path}")

    def print_linear_chain(self):
        print("\n=== Linear Ablation Chain ===")
        for s in self.linear_chain:
            print(f"  {s.description:<50} "
                  f"F1={s.macro_f1_mean:.3f}±{s.macro_f1_std:.3f} "
                  f"[{s.macro_f1_ci_lower:.3f}, {s.macro_f1_ci_upper:.3f}]")

    def print_factorial(self):
        print("\n=== Factorial Ablation (2^4 = 16 combinations) ===")
        print(f"{'Q':>3} {'R':>3} {'C':>3} {'M':>3} | {'Macro-F1':>10} {'Acc':>8}")
        print("-" * 40)
        for r in sorted(self.factorial, key=lambda x: -x.macro_f1):
            bits = "".join("✓" if r.components.get(c) else "✗"
                           for c in FACTORIAL_COMPONENTS)
            print(f"  {bits}    |  {r.macro_f1:>8.3f}  {r.accuracy:>8.3f}")


# ---------------------------------------------------------------------------
# Ablation runner
# ---------------------------------------------------------------------------

class AblationStudy:
    """Manages and runs both linear and factorial ablation experiments.

    In practice, each ablation step requires re-training or re-running
    with different evidence components enabled. This class provides the
    scaffolding for that process.

    Usage:
        ablation = AblationStudy(eval_fn=my_eval_function)
        report = ablation.run_linear_chain(test_cases, seeds=[42, 43, 44])
        report = ablation.run_factorial(test_cases)
        report.save("outputs/ablation/report.json")
    """

    def __init__(
        self,
        eval_fn=None,    # callable(config: Dict, cases: List) → (y_true, y_pred)
        output_dir: str = "outputs/ablation",
        n_bootstrap: int = 1000,
    ):
        """
        Args:
            eval_fn: callable that takes a config dict (which components are enabled)
                     and test cases, returns (y_true, y_pred) arrays.
                     If None, uses random predictions as placeholder.
            output_dir: where to save results
            n_bootstrap: bootstrap resamples for CIs
        """
        self.eval_fn = eval_fn or self._placeholder_eval
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.n_bootstrap = n_bootstrap

    def _placeholder_eval(
        self, config: Dict, cases: List
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Placeholder: returns random predictions. Replace with actual eval."""
        n = max(len(cases), 10)
        y_true = np.random.randint(0, 7, n)
        y_pred = np.random.randint(0, 7, n)
        return y_true, y_pred

    def _eval_with_seeds(
        self, config: Dict, cases: List, seeds: List[int]
    ) -> Tuple[float, float, float, float, float]:
        """Run eval across multiple seeds, return (mean_f1, std_f1, ci_lo, ci_hi, mean_acc)."""
        f1_scores = []
        acc_scores = []
        all_true, all_pred = [], []

        for seed in seeds:
            np.random.seed(seed)
            y_true, y_pred = self.eval_fn({**config, "seed": seed}, cases)
            f1 = compute_macro_f1(y_true.tolist(), y_pred.tolist())
            from sklearn.metrics import accuracy_score
            acc = float(accuracy_score(y_true, y_pred))
            f1_scores.append(f1)
            acc_scores.append(acc)
            all_true.extend(y_true.tolist())
            all_pred.extend(y_pred.tolist())

        all_true_arr = np.array(all_true)
        all_pred_arr = np.array(all_pred)
        ci = bootstrap_ci(
            lambda t, p: compute_macro_f1(t.tolist(), p.tolist()),
            all_true_arr, all_pred_arr,
            n_bootstrap=self.n_bootstrap,
        )
        return (
            float(np.mean(f1_scores)),
            float(np.std(f1_scores)),
            ci["ci_lower"],
            ci["ci_upper"],
            float(np.mean(acc_scores)),
        )

    def run_linear_chain(
        self,
        cases: List,
        seeds: Optional[List[int]] = None,
    ) -> AblationReport:
        """Run the linear ablation chain (image-only → full system).

        Each step progressively adds one component.
        """
        seeds = seeds or [42, 43, 44]
        report = AblationReport(n_seeds=len(seeds))

        # Track which components are enabled (cumulative)
        enabled = {
            "use_metadata": False,
            "use_text": False,
            "use_adaptive_fusion": False,
            "use_quality_Q": False,
            "use_reliability_R": False,
            "use_utility_U": False,
            "use_consistency_C": False,
            "use_sufficiency": False,
            "use_uncertainty": False,
            "use_acquisition": False,
            "use_verification": False,
        }

        step_toggles = [
            None,
            "use_metadata",
            "use_text",
            "use_adaptive_fusion",
            "use_quality_Q",
            "use_reliability_R",
            "use_utility_U",
            "use_consistency_C",
            "use_sufficiency",
            "use_uncertainty",
            "use_acquisition",
            "use_verification",
        ]

        for step_info, toggle in zip(LINEAR_CHAIN, step_toggles):
            if toggle is not None:
                enabled[toggle] = True

            print(f"[Ablation] Running step: {step_info['description']}")
            mean_f1, std_f1, ci_lo, ci_hi, mean_acc = self._eval_with_seeds(
                dict(enabled), cases, seeds
            )

            report.linear_chain.append(AblationStep(
                step_id=step_info["id"],
                description=step_info["description"],
                macro_f1_mean=mean_f1,
                macro_f1_std=std_f1,
                macro_f1_ci_lower=ci_lo,
                macro_f1_ci_upper=ci_hi,
                accuracy_mean=mean_acc,
            ))

        report.print_linear_chain()
        return report

    def run_factorial(
        self,
        cases: List,
        seeds: Optional[List[int]] = None,
    ) -> AblationReport:
        """Run factorial 2^4 ablation over evidence manager components {Q, R, C, M}.

        Tests all 16 combinations.
        """
        seeds = seeds or [42]
        report = AblationReport(n_seeds=len(seeds))

        component_keys = {
            "Q": "use_quality_Q",
            "R": "use_reliability_R",
            "C": "use_consistency_C",
            "M": "use_missingness_M",
        }

        for bits in itertools.product([False, True], repeat=4):
            combination = dict(zip(FACTORIAL_COMPONENTS, bits))
            config = {component_keys[k]: v for k, v in combination.items()}
            config["use_adaptive_fusion"] = True

            bit_str = "".join("1" if b else "0" for b in bits)
            print(f"[Ablation] Factorial {bit_str}: {combination}")

            f1_list, acc_list = [], []
            for seed in seeds:
                np.random.seed(seed)
                y_true, y_pred = self.eval_fn({**config, "seed": seed}, cases)
                f1_list.append(compute_macro_f1(y_true.tolist(), y_pred.tolist()))
                from sklearn.metrics import accuracy_score
                acc_list.append(float(accuracy_score(y_true, y_pred)))

            report.factorial.append(FactorialResult(
                components=combination,
                macro_f1=float(np.mean(f1_list)),
                accuracy=float(np.mean(acc_list)),
            ))

        report.print_factorial()
        return report

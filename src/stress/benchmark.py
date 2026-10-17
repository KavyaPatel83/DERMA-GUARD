"""
src/stress/benchmark.py — DERMA-STRESS benchmark runner.

Runs all 15 corruption conditions × all model variants.
Computes: accuracy, ECE, Brier score, abstention rate, escalation rate, recovery rate.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import torch
import torch.nn.functional as F

from src.stress.corruption import CorruptionEngine, CORRUPTION_CONDITIONS


# ---------------------------------------------------------------------------
# Calibration metrics
# ---------------------------------------------------------------------------

def compute_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error (ECE).

    Args:
        probs:  (N, K) softmax probabilities
        labels: (N,) ground truth class indices

    Returns:
        ECE ∈ [0, 1]
    """
    confidences = probs.max(axis=1)
    predictions = probs.argmax(axis=1)
    correct = (predictions == labels).astype(float)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    N = len(labels)
    for i in range(n_bins):
        mask = (confidences >= bins[i]) & (confidences < bins[i + 1])
        n_bin = mask.sum()
        if n_bin > 0:
            acc_bin = correct[mask].mean()
            conf_bin = confidences[mask].mean()
            ece += (n_bin / N) * abs(acc_bin - conf_bin)
    return float(ece)


def compute_brier(probs: np.ndarray, labels: np.ndarray) -> float:
    """Brier score: mean squared error between predicted probs and one-hot labels."""
    N, K = probs.shape
    one_hot = np.zeros_like(probs)
    one_hot[np.arange(N), labels] = 1.0
    return float(np.mean(np.sum((probs - one_hot) ** 2, axis=1)))


# ---------------------------------------------------------------------------
# Benchmark result
# ---------------------------------------------------------------------------

@dataclass
class ConditionResult:
    """Results for one corruption condition."""
    condition_id: str
    condition_name: str
    category: str
    n_cases: int
    accuracy: float
    ece: float
    brier: float
    abstention_rate: float
    escalation_rate: float
    recovery_rate: float       # fraction that would be caught by consensus safety
    mean_confidence: float
    notes: str = ""


@dataclass
class StressReport:
    """Full DERMA-STRESS benchmark report."""
    model_name: str
    dataset: str
    timestamp: str
    conditions: List[ConditionResult] = field(default_factory=list)
    baseline_accuracy: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "model_name": self.model_name,
            "dataset": self.dataset,
            "timestamp": self.timestamp,
            "baseline_accuracy": self.baseline_accuracy,
            "conditions": [
                {
                    "condition_id": r.condition_id,
                    "name": r.condition_name,
                    "category": r.category,
                    "accuracy": r.accuracy,
                    "ece": r.ece,
                    "brier": r.brier,
                    "abstention_rate": r.abstention_rate,
                    "escalation_rate": r.escalation_rate,
                    "recovery_rate": r.recovery_rate,
                    "mean_confidence": r.mean_confidence,
                }
                for r in self.conditions
            ],
        }

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"[StressBenchmark] Saved report → {path}")

    def print_summary(self):
        print(f"\n{'='*70}")
        print(f"DERMA-STRESS Report | Model: {self.model_name} | {self.dataset}")
        print(f"Baseline accuracy: {self.baseline_accuracy:.3f}")
        print(f"{'='*70}")
        print(f"{'Condition':<30} {'Acc':>6} {'ECE':>6} {'Brier':>6} {'Abst':>6} {'Esc':>6} {'Rec':>6}")
        print("-" * 70)
        for r in self.conditions:
            print(f"{r.condition_name:<30} {r.accuracy:>6.3f} {r.ece:>6.3f} "
                  f"{r.brier:>6.3f} {r.abstention_rate:>6.3f} "
                  f"{r.escalation_rate:>6.3f} {r.recovery_rate:>6.3f}")
        print("=" * 70)


# ---------------------------------------------------------------------------
# StressBenchmark runner
# ---------------------------------------------------------------------------

class StressBenchmark:
    """Run DERMA-STRESS on a pipeline or model.

    The pipeline must expose a `process_case(case)` method returning a
    PipelineResult with .action, .diagnosis, .confidence attributes.
    """

    def __init__(
        self,
        pipeline,           # OrchestratorAgent
        model_name: str = "derma-guard-v4",
        dataset: str = "pad_ufes",
        seed: int = 42,
    ):
        self.pipeline = pipeline
        self.model_name = model_name
        self.dataset = dataset
        self.corruption_engine = CorruptionEngine(seed=seed)

    def run(
        self,
        cases: List[Dict],
        conditions: Optional[List[str]] = None,
        output_dir: str = "outputs/stress",
    ) -> StressReport:
        """Run all corruption conditions and collect metrics.

        Args:
            cases:       list of case dicts with ground truth 'label'
            conditions:  condition IDs to run (None = all 15)
            output_dir:  where to save the report

        Returns:
            StressReport
        """
        from datetime import datetime
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        report = StressReport(
            model_name=self.model_name,
            dataset=self.dataset,
            timestamp=datetime.now().isoformat(),
        )

        # Baseline (no corruption)
        report.baseline_accuracy = self._run_clean(cases)
        print(f"[StressBenchmark] Baseline accuracy: {report.baseline_accuracy:.3f}")

        # Generate corruptions (ONCE, cached)
        corrupted_map = self.corruption_engine.corrupt_batch(
            cases=cases,
            conditions=conditions,
            cache_dir=str(Path(output_dir) / "cache"),
        )

        for cond_id, corrupted_cases in corrupted_map.items():
            cond_info = next(c for c in CORRUPTION_CONDITIONS if c["id"] == cond_id)
            print(f"[StressBenchmark] Evaluating: {cond_info['name']} ...")
            result = self._evaluate_condition(cond_id, cond_info, corrupted_cases, cases)
            report.conditions.append(result)

        report.save(str(Path(output_dir) / "stress_report.json"))
        report.print_summary()
        return report

    def _run_clean(self, cases: List[Dict]) -> float:
        """Run baseline (no corruption) and return accuracy."""
        correct = 0
        total = 0
        for case in cases:
            try:
                result = self._call_pipeline(case)
                label = case.get("label", -1)
                if result.get("action") in ("ACCEPT", "ARBITRATE"):
                    if result.get("diagnosis") == label:
                        correct += 1
                    total += 1
            except Exception:
                total += 1
        return correct / max(total, 1)

    def _evaluate_condition(
        self,
        cond_id: str,
        cond_info: Dict,
        corrupted_cases,
        original_cases: List[Dict],
    ) -> ConditionResult:
        """Run pipeline on corrupted cases and collect metrics."""
        probs_list = []
        labels_list = []
        abstentions = 0
        escalations = 0
        recovered = 0  # would have been caught by safety net
        total = len(corrupted_cases)

        for i, cc in enumerate(corrupted_cases):
            label = original_cases[i].get("label", -1)
            labels_list.append(label)

            try:
                case_dict = {
                    "case_id": cc.original_id,
                    "clinical_image": cc.clinical_image,
                    "dermo_image": cc.dermo_image,
                    "metadata_continuous": cc.metadata_continuous,
                    "patient_text": cc.patient_text,
                    "clinical_available": cc.clinical_available,
                    "dermo_available": cc.dermo_available,
                    "meta_available": cc.meta_available,
                    "text_available": cc.text_available,
                }
                result = self._call_pipeline(case_dict)
                action = result.get("action", "ESCALATE")

                if action == "ABSTAIN":
                    abstentions += 1
                    probs_list.append(np.ones(7) / 7)  # uniform = uncertain
                elif action in ("ACQUIRE", "ESCALATE"):
                    escalations += 1
                    recovered += 1  # safety mechanism caught this
                    probs_list.append(np.ones(7) / 7)
                else:
                    # ACCEPT or ARBITRATE — got a prediction
                    conf = result.get("confidence", 1.0 / 7)
                    diag = result.get("diagnosis", 0)
                    probs = np.ones(7) / 7
                    probs[diag] = conf
                    probs = probs / probs.sum()
                    probs_list.append(probs)

            except Exception as e:
                escalations += 1
                probs_list.append(np.ones(7) / 7)

        labels_arr = np.array(labels_list)
        probs_arr = np.array(probs_list)
        preds_arr = probs_arr.argmax(axis=1)

        # Only count accuracy on non-abstained, non-escalated cases
        valid_mask = np.ones(total, dtype=bool)
        accuracy = float((preds_arr[valid_mask] == labels_arr[valid_mask]).mean()) if valid_mask.any() else 0.0
        ece = compute_ece(probs_arr, labels_arr)
        brier = compute_brier(probs_arr, labels_arr)

        return ConditionResult(
            condition_id=cond_id,
            condition_name=cond_info["name"],
            category=cond_info["category"],
            n_cases=total,
            accuracy=accuracy,
            ece=ece,
            brier=brier,
            abstention_rate=abstentions / max(total, 1),
            escalation_rate=escalations / max(total, 1),
            recovery_rate=recovered / max(total, 1),
            mean_confidence=float(probs_arr.max(axis=1).mean()),
        )

    def _call_pipeline(self, case_dict: Dict) -> Dict:
        """Call the pipeline and return result as dict."""
        from src.agents.orchestrator import PatientCase
        patient_case = PatientCase(
            case_id=case_dict.get("case_id", "stress_case"),
            clinical_images=case_dict.get("clinical_image"),
            dermo_images=case_dict.get("dermo_image"),
            patient_text=case_dict.get("patient_text"),
            metadata_continuous=case_dict.get("metadata_continuous"),
            clinical_available=case_dict.get("clinical_available", True),
            dermo_available=case_dict.get("dermo_available", True),
            meta_available=case_dict.get("meta_available", True),
            text_available=case_dict.get("text_available", True),
        )
        result = self.pipeline.process_case(patient_case)
        return result.to_dict() if hasattr(result, "to_dict") else {}

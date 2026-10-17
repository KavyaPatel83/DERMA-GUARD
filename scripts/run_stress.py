"""
scripts/run_stress.py — DERMA-STRESS Benchmark Entry Point.

Runs all 15 corruption conditions (defined in src/stress/corruption.py)
against all model variants and writes results to outputs/stress/.

Per DERMA-GUARD v4.0 spec (proj.md Part 11):
  - Corruptions are generated ONCE, cached, replayed for ALL models
  - Metrics per condition: accuracy, ECE, Brier, abstention rate,
    escalation rate, recovery rate

Usage:
    python scripts/run_stress.py
    python scripts/run_stress.py --model-variant full --dataset derm7pt
    python scripts/run_stress.py --condition missing_clinical
"""
import argparse
import json
import os
import sys
from pathlib import Path

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.stress.benchmark import StressBenchmark
from src.stress.corruption import CORRUPTION_CONDITIONS


def main():
    parser = argparse.ArgumentParser(description="Run DERMA-STRESS benchmark")
    parser.add_argument("--output-dir",    type=str, default="outputs/stress",
                        help="Directory to save stress results")
    parser.add_argument("--dataset",       type=str, default="derm7pt",
                        choices=["derm7pt", "pad_ufes"],
                        help="Evaluation dataset")
    parser.add_argument("--model-variant", type=str, default="full",
                        choices=["full", "b1", "b2", "b3", "b4", "b5", "b6"],
                        help="Which model variant to stress test")
    parser.add_argument("--condition",     type=str, default="all",
                        help=f"Specific condition to run, or 'all'. Available: {list(CORRUPTION_CONDITIONS.keys())}")
    parser.add_argument("--batch-size",    type=int, default=16)
    parser.add_argument("--seed",          type=int, default=42)
    args = parser.parse_args()

    output_dir = project_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("DERMA-STRESS Benchmark")
    print(f"Dataset: {args.dataset} | Model: {args.model_variant}")
    print(f"Condition: {args.condition}")
    print(f"Available conditions: {len(CORRUPTION_CONDITIONS)}")
    print("=" * 60)

    benchmark = StressBenchmark(
        output_dir=output_dir,
        seed=args.seed,
    )

    if args.condition == "all":
        results = benchmark.run_all_conditions(
            dataset=args.dataset,
            model_variant=args.model_variant,
            batch_size=args.batch_size,
        )
    else:
        if args.condition not in CORRUPTION_CONDITIONS:
            print(f"Unknown condition '{args.condition}'. Available: {list(CORRUPTION_CONDITIONS.keys())}")
            sys.exit(1)
        results = benchmark.run_condition(
            condition_name=args.condition,
            dataset=args.dataset,
            model_variant=args.model_variant,
            batch_size=args.batch_size,
        )

    # Save summary
    summary_path = output_dir / f"stress_summary_{args.model_variant}_{args.dataset}.json"
    # Results may be dataclass — convert to dict for JSON
    if hasattr(results, "__dict__"):
        results_dict = results.__dict__
    elif isinstance(results, list):
        results_dict = [r.__dict__ if hasattr(r, "__dict__") else r for r in results]
    else:
        results_dict = results

    with open(summary_path, "w") as f:
        json.dump(results_dict, f, indent=2, default=str)

    print(f"\nResults saved to {summary_path}")


if __name__ == "__main__":
    main()

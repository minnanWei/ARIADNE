from __future__ import annotations

import argparse
import random

from evaluation.dataset_runner import DatasetRunConfig, run_dataset

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_path", type=str, default="apps/apps_selected150.jsonl")
    parser.add_argument("--num", type=int, default=10)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--expansion_budget", type=int, default=2)
    parser.add_argument("--output_dir", type=str, default="results")
    parser.add_argument("--run_name", type=str, default="")
    args = parser.parse_args()

    config = DatasetRunConfig(
        dataset_path=args.dataset_path,
        output_dir=args.output_dir,
        run_name=args.run_name or None,
        limit=args.num,
        iterations=args.iterations,
        expansion_budget=args.expansion_budget,
    )
    summary_path = run_dataset(config)
    print(f"Summary written to: {summary_path}")

if __name__ == "__main__":
    main()

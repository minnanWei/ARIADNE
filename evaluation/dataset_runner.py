from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from apps.loader import load_apps_dataset
from agents.llm_client import get_usage, reset_usage
from core.mcts import MCTS
from core.node import Node
from evaluation.summary import write_summary


@dataclass
class DatasetRunConfig:
    dataset_path: str
    output_dir: str = "results"
    run_name: Optional[str] = None
    limit: Optional[int] = None
    iterations: int = 10
    expansion_budget: int = 2
    c: float = 1.4
    tau: float = 1.0
    seed: int = 0


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path_obj, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")


def run_dataset(config: DatasetRunConfig) -> str:
    run_name = config.run_name or datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(config.output_dir) / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    problems = load_apps_dataset(config.dataset_path, limit=config.limit)
    results: List[Dict[str, Any]] = []
    total = len(problems)

    for idx, blackboard in enumerate(problems, start=1):
        problem_name = blackboard.problem.name
        print(f"[{idx}/{total}] start: {problem_name}", flush=True)
        reset_usage()
        start = time.perf_counter()

        root = Node(code="", blackboard=blackboard)
        mcts = MCTS(
            iterations=config.iterations,
            expansion_budget=config.expansion_budget,
            c=config.c,
            tau=config.tau,
            seed=config.seed,
        )
        mcts_result = mcts.run(root)

        elapsed = time.perf_counter() - start
        usage = get_usage()

        run_details = [
            {
                "prompt_tokens": usage["prompt_tokens"],
                "completion_tokens": usage["completion_tokens"],
                "taken_time": elapsed,
                "api_calls": usage["api_calls"],
                "llm_time_s": usage["llm_time_s"],
            }
        ]

        results.append(
            {
                "name": problem_name,
                "problem_id": idx,
                "is_solved": mcts_result.solved,
                "run_details": run_details,
                "best_code": mcts_result.best_code,
            }
        )
        print(
            f"[{idx}/{total}] done: solved={mcts_result.solved}, api_calls={usage['api_calls']}, elapsed={elapsed:.2f}s",
            flush=True,
        )

    results_path = str(run_dir / "Results.jsonl")
    summary_path = str(run_dir / "Summary.txt")
    _write_jsonl(results_path, results)
    write_summary(results, summary_path)
    return summary_path

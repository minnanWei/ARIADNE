from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Dict, Any

def write_summary(results: List[Dict[str, Any]], summary_path: str) -> None:
    total = len(results)
    solved = sum(1 for item in results if item.get("is_solved") is True)
    unsolved = total - solved
    accuracy = (solved / total) if total else 0.0

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_taken_time = 0.0
    total_api_calls = 0
    max_api_calls = 0
    min_api_calls = 0

    api_calls_per_item: List[int] = []

    for item in results:
        run_details = item.get("run_details") or []
        prompt_tokens = sum(run.get("prompt_tokens", 0) for run in run_details)
        completion_tokens = sum(run.get("completion_tokens", 0) for run in run_details)
        taken_time = sum(run.get("taken_time", 0.0) for run in run_details)
        api_calls = sum(run.get("api_calls", 0) for run in run_details)

        total_prompt_tokens += prompt_tokens
        total_completion_tokens += completion_tokens
        total_taken_time += taken_time
        total_api_calls += api_calls
        api_calls_per_item.append(api_calls)

    if api_calls_per_item:
        max_api_calls = max(api_calls_per_item)
        min_api_calls = min(api_calls_per_item)

    average_prompt_tokens = (total_prompt_tokens / total) if total else 0.0
    average_completion_tokens = (total_completion_tokens / total) if total else 0.0
    average_taken_time = (total_taken_time / total) if total else 0.0
    average_api_calls = (total_api_calls / total) if total else 0.0

    summary_path_obj = Path(summary_path)
    summary_path_obj.parent.mkdir(parents=True, exist_ok=True)

    name_width = 30
    value_width = 10
    with open(summary_path_obj, "w", encoding="utf-8") as summary_file:
        summary_file.write(f"{'Accuracy:':<{name_width}} {accuracy*100:>{value_width}.01f}\n")
        summary_file.write(f"{'Solved:':<{name_width}} {solved:>{value_width}}\n")
        summary_file.write(f"{'Unsolved:':<{name_width}} {unsolved:>{value_width}}\n")
        summary_file.write("\n\n")
        summary_file.write(f"{'Total Prompt Tokens:':<{name_width}} {total_prompt_tokens:>{value_width}}\n")
        summary_file.write(f"{'Average Prompt Tokens:':<{name_width}} {average_prompt_tokens:>{value_width}.0f}\n")
        summary_file.write("\n")
        summary_file.write(f"{'Total Completion Tokens:':<{name_width}} {total_completion_tokens:>{value_width}}\n")
        summary_file.write(f"{'Average Completion Tokens:':<{name_width}} {average_completion_tokens:>{value_width}.0f}\n")
        summary_file.write("\n")
        summary_file.write(f"{'Total Taken Time:':<{name_width}} {total_taken_time:>{value_width}.02f}s\n")
        summary_file.write(f"{'Average Taken Time:':<{name_width}} {average_taken_time:>{value_width}.02f}s\n")
        summary_file.write("\n")
        summary_file.write(f"{'Total Api Calls:':<{name_width}} {total_api_calls:>{value_width}.02f}\n")
        summary_file.write(f"{'Max Api Calls:':<{name_width}} {max_api_calls:>{value_width}}\n")
        summary_file.write(f"{'Min Api Calls:':<{name_width}} {min_api_calls:>{value_width}}\n")
        summary_file.write(f"{'Average Api Calls:':<{name_width}} {average_api_calls:>{value_width}.02}\n")

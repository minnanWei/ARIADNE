from __future__ import annotations

from typing import Optional

ALPHA = 0.6
BETA = 0.2
GAMMA = 0.2

def compute_reward(
    passed_count: int,
    total: int,
    timeouts: int,
    avg_runtime_s: Optional[float],
    code: str,
) -> float:
    r_corr = passed_count / total if total > 0 else 0.0

    timeout_rate = timeouts / total if total > 0 else 1.0
    r_perf = 1.0 - min(1.0, timeout_rate)

    if avg_runtime_s is not None and avg_runtime_s > 0:
        slow_factor = min(1.0, avg_runtime_s / 0.5)
        r_perf *= max(0.0, 1.0 - 0.5 * slow_factor)

    length_penalty = min(len(code) / 2000.0, 1.0)
    branch_count = sum(code.count(token) for token in ["if", "for", "while"])
    branch_penalty = min(branch_count / 50.0, 1.0)
    r_struct = max(0.0, 1.0 - 0.5 * length_penalty - 0.5 * branch_penalty)

    return ALPHA * r_corr + BETA * r_perf + GAMMA * r_struct

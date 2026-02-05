from __future__ import annotations

from dataclasses import dataclass
from typing import List

from blackboard.blackboard import Blackboard
from blackboard.schemas import Diagnostic, DiagnosticStatus
from evaluation.runner import run_python


@dataclass
class DeepEvalResult:
    passed: bool
    passed_count: int
    total: int
    timeouts: int
    avg_runtime_s: float
    diagnostics: List[Diagnostic]


def run_deep_evaluate(
    code: str,
    blackboard: Blackboard,
    timeout_s: float = 1.0,
) -> DeepEvalResult:
    tests = blackboard.problem.tests
    passed = 0
    timeouts = 0
    runtimes = []
    diagnostics: List[Diagnostic] = []

    for test in tests:
        result = run_python(code, test.input, timeout_s)
        runtimes.append(result.runtime_s)

        if result.timed_out:
            timeouts += 1
            diagnostics.append(
                Diagnostic(
                    stage="deepeval",
                    status=DiagnosticStatus.TLE,
                    test=test,
                    message="timeout",
                    runtime_s=result.runtime_s,
                )
            )
            continue

        if result.exit_code != 0:
            diagnostics.append(
                Diagnostic(
                    stage="deepeval",
                    status=DiagnosticStatus.RE,
                    test=test,
                    message=result.stderr.strip() or "runtime error",
                    runtime_s=result.runtime_s,
                )
            )
            continue

        if result.stdout.strip() != test.output.strip():
            diagnostics.append(
                Diagnostic(
                    stage="deepeval",
                    status=DiagnosticStatus.WA,
                    test=test,
                    message="wrong answer",
                    actual_output=result.stdout,
                    expected_output=test.output,
                    runtime_s=result.runtime_s,
                )
            )
            continue

        passed += 1

    total = len(tests)
    avg_runtime = sum(runtimes) / len(runtimes) if runtimes else 0.0
    return DeepEvalResult(
        passed=passed == total,
        passed_count=passed,
        total=total,
        timeouts=timeouts,
        avg_runtime_s=avg_runtime,
        diagnostics=diagnostics,
    )

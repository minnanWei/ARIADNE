from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from blackboard.blackboard import Blackboard
from blackboard.schemas import Diagnostic, DiagnosticStatus, TestCase
from evaluation.runner import run_python


@dataclass
class QuickScreenResult:
    passed: bool
    passed_count: int
    total: int
    timeouts: int
    avg_runtime_s: float
    diagnostic: Optional[Diagnostic]


def run_quickscreen(
    code: str,
    blackboard: Blackboard,
    timeout_s: float = 0.2,
) -> QuickScreenResult:
    tests = blackboard.get_quickscreen_tests()
    passed = 0
    timeouts = 0
    runtimes = []
    diagnostic: Optional[Diagnostic] = None

    for test in tests:
        result = run_python(code, test.input, timeout_s)
        runtimes.append(result.runtime_s)

        if result.timed_out:
            timeouts += 1
            diagnostic = Diagnostic(
                stage="quickscreen",
                status=DiagnosticStatus.TLE,
                test=test,
                message="timeout",
                runtime_s=result.runtime_s,
            )
            break

        if result.exit_code != 0:
            diagnostic = Diagnostic(
                stage="quickscreen",
                status=DiagnosticStatus.RE,
                test=test,
                message=result.stderr.strip() or "runtime error",
                runtime_s=result.runtime_s,
            )
            break

        if result.stdout.strip() != test.output.strip():
            diagnostic = Diagnostic(
                stage="quickscreen",
                status=DiagnosticStatus.WA,
                test=test,
                message="wrong answer",
                actual_output=result.stdout,
                expected_output=test.output,
                runtime_s=result.runtime_s,
            )
            break

        passed += 1

    total = len(tests)
    avg_runtime = sum(runtimes) / len(runtimes) if runtimes else 0.0
    passed_all = (passed == total) and diagnostic is None
    return QuickScreenResult(
        passed=passed_all,
        passed_count=passed,
        total=total,
        timeouts=timeouts,
        avg_runtime_s=avg_runtime,
        diagnostic=diagnostic,
    )

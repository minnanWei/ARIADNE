from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from blackboard.schemas import Diagnostic, FailureRecord, TestCase, TestOrigin

@dataclass
class CounterexampleTestsBlackboard:
    seed_tests: List[TestCase] = field(default_factory=list)
    generated_tests: List[TestCase] = field(default_factory=list)
    counterexamples: List[TestCase] = field(default_factory=list)
    minimized_counterexamples: List[TestCase] = field(default_factory=list)
    failure_metadata: List[FailureRecord] = field(default_factory=list)
    seed: int = 0

    def add_counterexample(self, testcase: TestCase, diag: Diagnostic) -> None:
        if not self._contains_input(self.counterexamples, testcase.input_data):
            self.counterexamples.append(testcase)

    def add_minimized_counterexample(self, testcase: TestCase, diag: Diagnostic) -> None:
        if not self._contains_input(self.minimized_counterexamples, testcase.input_data):
            self.minimized_counterexamples.append(testcase)

    def record_failure(self, diag: Diagnostic) -> None:
        test = diag.failing_tests[0].testcase if diag.failing_tests else None
        message = diag.notes.get("message", "")
        stage = diag.notes.get("stage", "unknown")
        self.failure_metadata.append(
            FailureRecord(
                status=diag.status,
                test=test,
                stage=stage,
                message=message,
                timestamp_s=float(len(self.failure_metadata)),
            )
        )

    def add_generated_tests(self, tests: List[TestCase]) -> None:
        for test in tests:
            if test.origin == TestOrigin.MINIMIZED:
                if not self._contains_input(self.minimized_counterexamples, test.input_data):
                    self.minimized_counterexamples.append(test)
            elif test.origin == TestOrigin.COUNTEREXAMPLE:
                if not self._contains_input(self.counterexamples, test.input_data):
                    self.counterexamples.append(test)
            else:
                if not self._contains_input(self.generated_tests, test.input_data):
                    self.generated_tests.append(test)

    def get_quickscreen_suite(self, max_n: int) -> List[TestCase]:
        rng = __import__("random").Random(self.seed)
        ordered_groups = [
            self.minimized_counterexamples,
            self.counterexamples,
            self.seed_tests,
            self.generated_tests,
        ]
        suite: List[TestCase] = []
        seen_inputs = set()
        remaining = max_n

        for group in ordered_groups:
            if remaining <= 0:
                break
            unique_group = [t for t in group if t.input_data not in seen_inputs]
            if len(unique_group) > remaining:
                rng.shuffle(unique_group)
                selected = unique_group[:remaining]
            else:
                selected = unique_group
            for test in selected:
                seen_inputs.add(test.input_data)
                suite.append(test)
            remaining = max_n - len(suite)
        return suite

    @staticmethod
    def _contains_input(tests: List[TestCase], input_data: str) -> bool:
        return any(test.input_data == input_data for test in tests)

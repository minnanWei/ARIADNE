from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, List

from blackboard.counterexamples import CounterexampleTestsBlackboard
from blackboard.patch_repair import PatchRepairBlackboard
from blackboard.problem_model import ProblemModelBlackboard
from blackboard.schemas import Diagnostic, DiagnosticStatus, Problem, TestCase, TestOrigin
from blackboard.strategy_hypothesis import StrategyHypothesisBlackboard


@dataclass
class Blackboard:
    problem_model: ProblemModelBlackboard
    tests: CounterexampleTestsBlackboard
    strategy: StrategyHypothesisBlackboard
    repair: PatchRepairBlackboard

    def clone(self) -> "Blackboard":
        return copy.deepcopy(self)

    def update_from_diagnostic(self, diagnostic: Diagnostic) -> None:
        self.tests.record_failure(diagnostic)
        if diagnostic.failing_tests:
            for result in diagnostic.failing_tests:
                if result.testcase:
                    self.tests.add_counterexample(result.testcase, diagnostic)
        elif diagnostic.test and diagnostic.status in {
            DiagnosticStatus.WA,
            DiagnosticStatus.RE,
            DiagnosticStatus.TLE,
        }:
            self.tests.add_counterexample(diagnostic.test, diagnostic)

    def get_quickscreen_tests(self, max_tests: int = 3) -> List[TestCase]:
        return self.tests.get_quickscreen_suite(max_tests)

    def get_starter_code(self) -> str:
        return str(self.problem_model.io_spec.get("starter_code", ""))

    @property
    def problem(self) -> Problem:
        examples = [t for t in self.tests.seed_tests if t.origin == TestOrigin.APPS_EXAMPLE]
        tests = [t for t in self.tests.seed_tests if t.origin == TestOrigin.APPS_TEST]
        if not tests:
            tests = list(self.tests.seed_tests)
        return Problem(
            name=self.problem_model.objective,
            question=self.problem_model.raw_statement,
            starter_code=str(self.problem_model.io_spec.get("starter_code", "")),
            examples=examples,
            tests=tests,
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "objective": self.problem_model.objective,
            "constraints": self.problem_model.constraints,
            "tags": self.problem_model.tags,
            "seed_tests": len(self.tests.seed_tests),
            "counterexamples": len(self.tests.counterexamples),
            "generated_tests": len(self.tests.generated_tests),
        }

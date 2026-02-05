from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import List

from agents.base import BaseAgent, State
from agents.prompts import TESTGEN_PROMPT_TEMPLATE
from blackboard.blackboard import Blackboard
from blackboard.schemas import TestCase, TestOrigin
from core.actions import Action, TestGenerationAction

@dataclass
class TestGenerationAgent(BaseAgent):
    seed: int = 0

    def propose(self, state: State, blackboard: Blackboard) -> List[Action]:
        rng = random.Random(self.seed)
        prompt = self._build_prompt(state, blackboard)
        response = self._call_llm(prompt, state, blackboard)
        tests = self._parse_response(response)

        if not tests:
            minimized = self._minimize_counterexample(blackboard)
            if minimized:
                tests.append(minimized)
            tests.extend(self._generate_extreme_tests(blackboard, rng))
            tests.extend(self._generate_random_tests(blackboard, rng))

        if not tests:
            return []

        return [
            TestGenerationAction(
                name="test_generation",
                tests=tests,
                confidence=0.3,
                cost=0.2,
                risk=0.1,
                metadata={"count": len(tests)},
            )
        ]

    def _minimize_counterexample(self, blackboard: Blackboard) -> TestCase | None:
        if not blackboard.tests.counterexamples:
            return None
        original = blackboard.tests.counterexamples[-1]
        tokens = original.input_data.strip().split()
        if len(tokens) <= 1:
            return None
        minimized_input = " ".join(tokens[: max(1, len(tokens) // 2)])
        return TestCase(
            input_data=minimized_input,
            expected_output=original.expected_output,
            origin=TestOrigin.MINIMIZED,
            weight=1.5,
        )

    def _generate_extreme_tests(
        self, blackboard: Blackboard, rng: random.Random
    ) -> List[TestCase]:
        extremes = [-10, -1, 0, 1, 10, 100]
        tests: List[TestCase] = []
        for a in extremes[:3]:
            for b in extremes[:3]:
                input_data = f"{a} {b}\n"
                expected = self._maybe_compute_expected(blackboard, input_data)
                tests.append(
                    TestCase(
                        input_data=input_data,
                        expected_output=expected,
                        origin=TestOrigin.GENERATED_EXTREME,
                        weight=0.8,
                    )
                )
        return tests

    def _generate_random_tests(
        self, blackboard: Blackboard, rng: random.Random
    ) -> List[TestCase]:
        tests: List[TestCase] = []
        for _ in range(3):
            a = rng.randint(-20, 20)
            b = rng.randint(-20, 20)
            input_data = f"{a} {b}\n"
            expected = self._maybe_compute_expected(blackboard, input_data)
            tests.append(
                TestCase(
                    input_data=input_data,
                    expected_output=expected,
                    origin=TestOrigin.GENERATED_RANDOM,
                    weight=0.6,
                )
            )
        return tests

    def _maybe_compute_expected(self, blackboard: Blackboard, input_data: str) -> str | None:
        statement = blackboard.problem_model.raw_statement.lower()
        if "sum" in statement or "add" in statement:
            nums = [int(tok) for tok in input_data.strip().split() if tok]
            return f"{sum(nums)}\n"
        return None

    def _build_prompt(self, state: State, blackboard: Blackboard) -> str:
        problem_statement = blackboard.problem_model.raw_statement or blackboard.problem_model.objective
        io_spec = blackboard.problem_model.io_spec
        constraints = blackboard.problem_model.constraints
        edge_cases = "\n".join(blackboard.problem_model.edge_case_checklist or [])
        counterexamples = "\n".join(t.input_data for t in blackboard.tests.counterexamples[-5:])
        return TESTGEN_PROMPT_TEMPLATE.format(
            problem_statement=problem_statement,
            io_spec=io_spec,
            constraints=constraints,
            edge_cases=edge_cases,
            counterexamples=counterexamples,
        )

    def _parse_response(self, text: str) -> List[TestCase]:
        try:
            data = json.loads(text or "{}")
        except json.JSONDecodeError:
            return []
        tests: List[TestCase] = []
        for item in data.get("tests", []):
            origin = self._safe_origin(item.get("origin"))
            tests.append(
                TestCase(
                    input_data=str(item.get("input", "")),
                    expected_output=item.get("expected_output"),
                    origin=origin,
                    weight=float(item.get("weight", 0.5)),
                )
            )
        return tests

    def _safe_origin(self, origin_value: object) -> TestOrigin:
        if isinstance(origin_value, TestOrigin):
            return origin_value
        try:
            return TestOrigin(str(origin_value))
        except ValueError:
            if str(origin_value) == "GENERATED_ENUM":
                return TestOrigin.GENERATED_RANDOM
            if str(origin_value) == "MINIMIZATION_HINT":
                return TestOrigin.MINIMIZED
            return TestOrigin.GENERATED_RANDOM

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from agents.base import BaseAgent, State
from agents.prompts import CODEGEN_PROMPT_TEMPLATE
from blackboard.blackboard import Blackboard
from core.actions import Action, GenerateCodeAction

@dataclass
class CodeGenerationAgent(BaseAgent):
    def propose(self, state: State, blackboard: Blackboard) -> List[Action]:
        prior = blackboard.strategy.compute_prior()
        if prior:
            strategy_id = max(prior.items(), key=lambda item: item[1])[0]
            confidence = prior[strategy_id]
        else:
            strategy_id = blackboard.strategy.get_active_hypothesis().id
            confidence = 0.4

        prompt = self._build_prompt(state, blackboard)
        response = self._call_llm(prompt, state, blackboard)
        actions = self._parse_response(response, strategy_id, confidence, blackboard)
        if actions:
            return actions

        hypothesis = blackboard.strategy.hypotheses.get(strategy_id)
        expected_complexity = hypothesis.complexity_upper_bound if hypothesis else None
        return [
            GenerateCodeAction(
                name="generate_code",
                variant="starter_or_baseline",
                strategy_id=strategy_id,
                expected_complexity=expected_complexity,
                confidence=confidence,
                cost=0.4,
                risk=0.3,
                metadata={"strategy": strategy_id},
            )
        ]

    def _build_prompt(self, state: State, blackboard: Blackboard) -> str:
        problem_statement = blackboard.problem_model.raw_statement or blackboard.problem_model.objective
        io_spec = blackboard.problem_model.io_spec
        constraints = blackboard.problem_model.constraints
        invariants = "\n".join(blackboard.problem_model.invariants or [])
        edge_cases = "\n".join(blackboard.problem_model.edge_case_checklist or [])
        counterexamples = "\n".join(t.input_data for t in blackboard.tests.counterexamples[-5:])
        return CODEGEN_PROMPT_TEMPLATE.format(
            problem_statement=problem_statement,
            io_spec=io_spec,
            constraints=constraints,
            invariants=invariants,
            edge_cases=edge_cases,
            counterexamples=counterexamples,
        )

    def _parse_response(
        self,
        text: str,
        strategy_id: str,
        confidence: float,
        blackboard: Blackboard,
    ) -> List[Action]:
        code = _extract_code(text)
        if not code:
            return []
        actions: List[Action] = []
        hypothesis = blackboard.strategy.hypotheses.get(strategy_id)
        expected_complexity = hypothesis.complexity_upper_bound if hypothesis else None
        actions.append(
            GenerateCodeAction(
                name="generate_code",
                variant="llm",
                strategy_id=strategy_id,
                expected_complexity=expected_complexity,
                code_override=code,
                confidence=confidence,
                cost=0.4,
                risk=0.3,
                metadata={"strategy": strategy_id},
            )
        )
        return actions

def _extract_code(text: str) -> str:
    if not text:
        return ""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if "\n" in cleaned:
            cleaned = cleaned.split("\n", 1)[1]
        if "```" in cleaned:
            cleaned = cleaned.split("```", 1)[0]
    return cleaned.strip()

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from agents.base import BaseAgent, State
from agents.prompts import REPAIR_PROMPT_TEMPLATE
from blackboard.blackboard import Blackboard
from core.actions import Action, ApplyPatchAction


@dataclass
class CodeRepairAgent(BaseAgent):
    budget: int = 2
    _last_patches: List = None

    def propose(self, state: State, blackboard: Blackboard) -> List[Action]:
        patches = blackboard.repair.select_patch_subset(self.budget)
        if not patches:
            return []
        self._last_patches = patches
        prompt = self._build_prompt(state, blackboard)
        response = self._call_llm(prompt, state, blackboard)
        actions = self._parse_response(response, patches)
        if actions:
            return actions
        return self._fallback_actions(patches)

    def _build_prompt(self, state: State, blackboard: Blackboard) -> str:
        code, _ = state
        last_failure = blackboard.tests.failure_metadata[-1] if blackboard.tests.failure_metadata else None
        status = last_failure.status.value if last_failure else "UNKNOWN"
        error_type = last_failure.message if last_failure else ""
        failing_tests = "\n".join(t.input_data for t in blackboard.tests.counterexamples[-3:])
        patches = self._last_patches or []
        patch_proposals = "\n".join(
            f"- [{patch.id}] {patch.description} (level={patch.level.value}, p={patch.success_prob:.2f}, cost={patch.cost:.2f}, risk={patch.risk:.2f})"
            for patch in patches
        )
        problem_statement = blackboard.problem_model.raw_statement or blackboard.problem_model.objective
        return REPAIR_PROMPT_TEMPLATE.format(
            problem_statement=problem_statement,
            current_code=code,
            status=status,
            error_type=error_type,
            failing_tests=failing_tests,
            patch_proposals=patch_proposals,
        )

    def _parse_response(self, text: str, patches) -> List[Action]:
        code = _extract_code(text)
        if not code:
            return []
        patch = patches[0]
        return [
            ApplyPatchAction(
                name="apply_patch",
                patch_id=patch.id,
                level=patch.level,
                confidence=patch.success_prob,
                cost=patch.cost,
                risk=patch.risk,
                code_override=code,
                metadata={"description": patch.description},
            )
        ]

    def _fallback_actions(self, patches) -> List[Action]:
        actions: List[Action] = []
        for patch in patches:
            actions.append(
                ApplyPatchAction(
                    name="apply_patch",
                    patch_id=patch.id,
                    level=patch.level,
                    confidence=patch.success_prob,
                    cost=patch.cost,
                    risk=patch.risk,
                    metadata={"description": patch.description},
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

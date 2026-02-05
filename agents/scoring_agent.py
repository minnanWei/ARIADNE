from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List

from blackboard.blackboard import Blackboard
from blackboard.schemas import Diagnostic, DiagnosticStatus, Patch, PatchLevel
from core.actions import Action
from agents.base import BaseAgent, State


@dataclass
class ScoringAgent(BaseAgent):
    def propose(self, state: State, blackboard: Blackboard) -> List[Action]:
        return []

    def handle_diagnostic(self, diag: Diagnostic, blackboard: Blackboard) -> None:
        blackboard.update_from_diagnostic(diag)
        prompt = self._build_prompt(diag)
        response = self._call_llm(prompt, ("", blackboard), blackboard)
        patches = self._parse_response(response)
        if not patches:
            patches = self._fallback_patches(diag)
        for patch in patches:
            blackboard.repair.propose_patch(patch)

    def _fallback_patches(self, diag: Diagnostic) -> List[Patch]:
        if diag.status == DiagnosticStatus.WA:
            return [
                Patch(
                    id="stub_off_by_one",
                    level=PatchLevel.L1_LOCAL,
                    description="Check off-by-one / logic conditions.",
                    diff_like=None,
                    preconditions=[],
                    dependencies=[],
                    conflicts=[],
                    success_prob=0.25,
                    cost=0.15,
                    risk=0.2,
                    tags=["stub", "logic"],
                )
            ]
        if diag.status == DiagnosticStatus.RE:
            return [
                Patch(
                    id="stub_input_guard",
                    level=PatchLevel.L1_LOCAL,
                    description="Add input validation / guards.",
                    diff_like=None,
                    preconditions=[],
                    dependencies=[],
                    conflicts=[],
                    success_prob=0.25,
                    cost=0.15,
                    risk=0.25,
                    tags=["stub", "input"],
                )
            ]
        if diag.status == DiagnosticStatus.TLE:
            return [
                Patch(
                    id="stub_optimize_loop",
                    level=PatchLevel.L2_STRUCTURAL,
                    description="Optimize loop or reduce complexity.",
                    diff_like=None,
                    preconditions=[],
                    dependencies=[],
                    conflicts=[],
                    success_prob=0.2,
                    cost=0.3,
                    risk=0.3,
                    tags=["stub", "performance"],
                )
            ]
        return []

    def _build_prompt(self, diag: Diagnostic) -> str:
        payload = {
            "status": diag.status.value,
            "notes": diag.notes,
            "failing_tests": [
                {
                    "input": result.testcase.input_data,
                    "expected_output": result.expected_output,
                    "actual_output": result.actual_output,
                }
                for result in diag.failing_tests
            ],
        }
        return (
            "Analyze this failure and propose up to 3 candidate patches as JSON. "
            "Return the format {\"patches\":[{\"id\":...,\"level\":...,\"description\":...,"
            "\"success_prob\":...,\"cost\":...,\"risk\":...,\"tags\":[...]}]}.\n"
            f"Failure payload:\n{json.dumps(payload, ensure_ascii=True)}"
        )

    def _parse_response(self, text: str) -> List[Patch]:
        try:
            data = json.loads(text or "{}")
        except json.JSONDecodeError:
            return []
        patches = []
        for item in data.get("patches", []):
            level = self._safe_patch_level(item.get("level"))
            patches.append(
                Patch(
                    id=str(item.get("id", "stub_llm_patch")),
                    level=level,
                    description=str(item.get("description", "")),
                    diff_like=None,
                    preconditions=[],
                    dependencies=[],
                    conflicts=[],
                    success_prob=float(item.get("success_prob", 0.2)),
                    cost=float(item.get("cost", 0.2)),
                    risk=float(item.get("risk", 0.2)),
                    tags=list(item.get("tags", [])),
                )
            )
        return patches

    def _safe_patch_level(self, level_value: object) -> PatchLevel:
        if isinstance(level_value, PatchLevel):
            return level_value
        try:
            return PatchLevel(str(level_value))
        except ValueError:
            return PatchLevel.L1_LOCAL

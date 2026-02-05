from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ProblemModelBlackboard:
    objective: str
    constraints: Dict[str, Any]
    invariants: List[str]
    edge_case_checklist: List[str]
    raw_statement: str
    io_spec: Dict[str, Any]
    tags: List[str] = field(default_factory=list)

    @staticmethod
    def from_apps_problem(problem_json: Dict[str, Any]) -> "ProblemModelBlackboard":
        name = problem_json.get("name", "unknown")
        question = problem_json.get("question", "")
        starter_code = problem_json.get("starter_code", "")
        constraints = problem_json.get("constraints", {})
        tags = problem_json.get("tags", [])

        io_spec = {
            "starter_code": starter_code,
            "input_description": problem_json.get("input_description"),
            "output_description": problem_json.get("output_description"),
        }

        return ProblemModelBlackboard(
            objective=f"Solve {name}",
            constraints=constraints,
            invariants=[],
            edge_case_checklist=[],
            raw_statement=question,
            io_spec=io_spec,
            tags=tags,
        )

    def summarize(self) -> str:
        summary = self.raw_statement.strip().splitlines()
        first_line = summary[0] if summary else self.objective
        return f"{self.objective}: {first_line}"

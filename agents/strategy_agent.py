from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List

from agents.base import BaseAgent, State
from agents.prompts import STRATEGY_PROMPT_TEMPLATE
from blackboard.blackboard import Blackboard
from blackboard.schemas import DiagnosticStatus, StrategyHypothesis
from core.actions import Action, StrategyProposalAction

@dataclass
class StrategyAnalysisAgent(BaseAgent):
    def propose(self, state: State, blackboard: Blackboard) -> List[Action]:
        prompt = self._build_prompt(state, blackboard)
        response = self._call_llm(prompt, state, blackboard)
        actions = self._parse_response(response)
        if actions:
            return actions
        return self._fallback_actions(blackboard)

    def _build_prompt(self, state: State, blackboard: Blackboard) -> str:
        recent_records = blackboard.tests.failure_metadata[-5:]
        recent_statuses = [record.status.value for record in recent_records]
        failure_patterns = [record.message for record in recent_records if record.message]
        counterexamples = [t.input_data for t in blackboard.tests.counterexamples[-3:]]
        return STRATEGY_PROMPT_TEMPLATE.format(
            problem_summary=blackboard.problem_model.summarize(),
            constraints=json.dumps(blackboard.problem_model.constraints),
            recent_statuses=recent_statuses,
            failure_patterns=failure_patterns,
            counterexamples="\n".join(counterexamples),
        )

    def _parse_response(self, text: str) -> List[Action]:
        try:
            data = json.loads(text or "{}")
        except json.JSONDecodeError:
            return []
        hypotheses: List[StrategyHypothesis] = []
        bids: Dict[str, tuple[float, float, float]] = {}
        strategies = data.get("strategies", [])
        if isinstance(strategies, dict):
            strategies = [strategies]
        if isinstance(strategies, str):
            return []
        recommended_active_id = str(data.get("recommended_active_id", "")).strip()
        for item in strategies:
            if not isinstance(item, dict):
                continue
            hypothesis = StrategyHypothesis(
                id=str(item.get("id", "")),
                name=str(item.get("name", "")),
                applicability_conditions=list(item.get("applicability_conditions", [])),
                complexity_upper_bound=str(item.get("complexity_upper_bound", "O(n)")),
                risk_flags=list(item.get("risk_flags", [])),
                minimal_evidence_set=list(item.get("minimal_evidence_set", [])),
                notes=str(item.get("notes", "")),
            )
            if hypothesis.id:
                hypotheses.append(hypothesis)
                bid = item.get("bid", {})
                bids[hypothesis.id] = (
                    float(bid.get("p", 0.5)),
                    float(bid.get("c", 0.5)),
                    float(bid.get("r", 0.5)),
                )
        if not hypotheses:
            return []
        return [
            StrategyProposalAction(
                name="strategy_proposal",
                hypotheses=hypotheses,
                bids=bids,
                confidence=0.3,
                cost=0.2,
                risk=0.2,
                metadata={"count": len(hypotheses), "recommended_active_id": recommended_active_id},
            )
        ]

    def _fallback_actions(self, blackboard: Blackboard) -> List[Action]:
        hypotheses: List[StrategyHypothesis] = []
        bids: Dict[str, tuple[float, float, float]] = {}

        if not blackboard.strategy.hypotheses:
            default = StrategyHypothesis(
                id="default",
                name="Baseline",
                applicability_conditions=["default"],
                complexity_upper_bound="O(n)",
                risk_flags=[],
                minimal_evidence_set=[],
                notes="Default baseline strategy.",
            )
            hypotheses.append(default)
            bids[default.id] = (0.5, 0.5, 0.5)

        statuses = [record.status for record in blackboard.tests.failure_metadata]
        if DiagnosticStatus.TLE in statuses and "optimize" not in blackboard.strategy.hypotheses:
            hyp = StrategyHypothesis(
                id="optimize",
                name="Optimize Complexity",
                applicability_conditions=["TLE seen"],
                complexity_upper_bound="O(n log n)",
                risk_flags=["refactor"],
                minimal_evidence_set=["timeout"],
                notes="Prefer more efficient loops or data structures.",
            )
            hypotheses.append(hyp)
            bids[hyp.id] = (0.4, 0.6, 0.5)

        if DiagnosticStatus.WA in statuses and "boundary_check" not in blackboard.strategy.hypotheses:
            hyp = StrategyHypothesis(
                id="boundary_check",
                name="Boundary Checks",
                applicability_conditions=["WA seen"],
                complexity_upper_bound="O(n)",
                risk_flags=[],
                minimal_evidence_set=["wrong answer"],
                notes="Re-check edge cases and bounds.",
            )
            hypotheses.append(hyp)
            bids[hyp.id] = (0.45, 0.4, 0.3)

        if DiagnosticStatus.RE in statuses and "robust_io" not in blackboard.strategy.hypotheses:
            hyp = StrategyHypothesis(
                id="robust_io",
                name="Robust IO",
                applicability_conditions=["RE seen"],
                complexity_upper_bound="O(n)",
                risk_flags=[],
                minimal_evidence_set=["runtime error"],
                notes="Guard against empty input or malformed tokens.",
            )
            hypotheses.append(hyp)
            bids[hyp.id] = (0.35, 0.3, 0.2)

        if not hypotheses:
            return []

        return [
            StrategyProposalAction(
                name="strategy_proposal",
                hypotheses=hypotheses,
                bids=bids,
                confidence=0.3,
                cost=0.2,
                risk=0.2,
                metadata={"count": len(hypotheses)},
            )
        ]

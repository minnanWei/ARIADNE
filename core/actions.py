from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from blackboard.blackboard import Blackboard
from blackboard.schemas import PatchLevel, StrategyHypothesis, TestCase

@dataclass
class Action:
    name: str
    confidence: Optional[float] = None
    cost: Optional[float] = None
    risk: Optional[float] = None
    metadata: Dict[str, object] = field(default_factory=dict)

    def apply(self, code: str, blackboard: Blackboard) -> str:
        raise NotImplementedError

@dataclass
class GenerateCodeAction(Action):
    variant: str = "starter_or_baseline"
    strategy_id: Optional[str] = None
    expected_complexity: Optional[str] = None
    code_override: Optional[str] = None

    def apply(self, code: str, blackboard: Blackboard) -> str:
        if self.strategy_id:
            blackboard.strategy.set_active_hypothesis(self.strategy_id)
        if self.code_override:
            return self.code_override
        starter_code = blackboard.get_starter_code()
        if starter_code.strip():
            return starter_code
        return ""

@dataclass
class EvaluateAction(Action):
    def apply(self, code: str, blackboard: Blackboard) -> str:
        return code

@dataclass
class TestGenerationAction(Action):
    tests: List[TestCase] = field(default_factory=list)

    def apply(self, code: str, blackboard: Blackboard) -> str:
        blackboard.tests.add_generated_tests(self.tests)
        return code

@dataclass
class StrategyProposalAction(Action):
    hypotheses: List[StrategyHypothesis] = field(default_factory=list)
    bids: Dict[str, tuple[float, float, float]] = field(default_factory=dict)

    def apply(self, code: str, blackboard: Blackboard) -> str:
        for hypothesis in self.hypotheses:
            blackboard.strategy.upsert_hypothesis(hypothesis)
            if hypothesis.id in self.bids:
                p, c, r = self.bids[hypothesis.id]
                blackboard.strategy.set_bid_components(hypothesis.id, p, c, r)
        recommended = self.metadata.get("recommended_active_id")
        if recommended:
            blackboard.strategy.set_active_hypothesis(str(recommended))
        elif not blackboard.strategy.active_hypothesis_id and self.hypotheses:
            blackboard.strategy.set_active_hypothesis(self.hypotheses[0].id)
        return code

@dataclass
class ApplyPatchAction(Action):
    patch_id: str = ""
    level: Optional[PatchLevel] = None
    code_override: Optional[str] = None

    def apply(self, code: str, blackboard: Blackboard) -> str:
        if self.code_override:
            return self.code_override
        return code

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from agents.codegen_agent import CodeGenerationAgent
from agents.repair_agent import CodeRepairAgent
from agents.scoring_agent import ScoringAgent
from agents.strategy_agent import StrategyAnalysisAgent
from agents.testgen_agent import TestGenerationAgent
from blackboard.blackboard import Blackboard
from core.actions import Action

State = Tuple[str, Blackboard]

@dataclass
class AgentCoordinator:
    scoring_agent: ScoringAgent = field(default_factory=lambda: ScoringAgent(name="scoring"))
    testgen_agent: TestGenerationAgent = field(default_factory=lambda: TestGenerationAgent(name="testgen", seed=0))
    codegen_agent: CodeGenerationAgent = field(default_factory=lambda: CodeGenerationAgent(name="codegen"))
    repair_agent: CodeRepairAgent = field(default_factory=lambda: CodeRepairAgent(name="repair"))
    strategy_agent: StrategyAnalysisAgent = field(default_factory=lambda: StrategyAnalysisAgent(name="strategy"))

    def handle_diagnostic(self, diag, blackboard: Blackboard) -> None:
        self.scoring_agent.handle_diagnostic(diag, blackboard)

    def enumerate_actions(self, state: State, blackboard: Blackboard) -> List[Action]:
        actions: List[Action] = []
        for agent in [
            self.scoring_agent,
            self.testgen_agent,
            self.codegen_agent,
            self.repair_agent,
            self.strategy_agent,
        ]:
            agent.reset_iteration()
        actions.extend(self.scoring_agent.propose(state, blackboard))
        actions.extend(self.testgen_agent.propose(state, blackboard))
        actions.extend(self.codegen_agent.propose(state, blackboard))
        actions.extend(self.repair_agent.propose(state, blackboard))
        actions.extend(self.strategy_agent.propose(state, blackboard))
        self._attach_priors(actions, blackboard)
        return actions

    def _attach_priors(self, actions: List[Action], blackboard: Blackboard) -> None:
        strategy_prior = blackboard.strategy.compute_prior()
        for action in actions:
            strategy_id = action.metadata.get("strategy")
            if strategy_id and strategy_id in strategy_prior:
                action.confidence = strategy_prior[strategy_id]
            if action.name == "apply_patch":
                patch_id = getattr(action, "patch_id", None)
                if patch_id and patch_id in blackboard.repair.patches:
                    action.confidence = blackboard.repair.patches[patch_id].success_prob

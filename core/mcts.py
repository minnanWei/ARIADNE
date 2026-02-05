from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Optional

from core.actions import Action
from core.coordinator import AgentCoordinator
from core.node import Node
from evaluation.deepeval import run_deep_evaluate
from evaluation.quickscreen import run_quickscreen
from evaluation.reward import compute_reward

@dataclass
class MCTSResult:
    best_code: str
    reward_trajectory: List[float]
    nodes_expanded: int
    solved: bool

class MCTS:
    def __init__(
        self,
        iterations: int = 20,
        expansion_budget: int = 2,
        c: float = 1.4,
        tau: float = 1.0,
        epsilon: float = 1e-6,
        seed: int = 0,
        coordinator: Optional[AgentCoordinator] = None,
    ) -> None:
        self.iterations = iterations
        self.expansion_budget = expansion_budget
        self.c = c
        self.tau = tau
        self.epsilon = epsilon
        self.rng = random.Random(seed)
        self.coordinator = coordinator or AgentCoordinator()

    def run(self, root: Node) -> MCTSResult:
        reward_trajectory: List[float] = []
        nodes_expanded = 0
        best_code = root.code
        best_reward = float("-inf")

        for _ in range(self.iterations):
            node = self._select(root)
            eval_result = self._simulate_and_evaluate(node)
            if eval_result.solved:
                return MCTSResult(
                    best_code=eval_result.code,
                    reward_trajectory=reward_trajectory,
                    nodes_expanded=nodes_expanded,
                    solved=True,
                )

            reward = eval_result.reward
            reward_trajectory.append(reward)
            if reward > best_reward:
                best_reward = reward
                best_code = node.code

            nodes_expanded += self._expand(node)
            self._backpropagate(node, reward)

        return MCTSResult(
            best_code=best_code,
            reward_trajectory=reward_trajectory,
            nodes_expanded=nodes_expanded,
            solved=False,
        )

    def _select(self, node: Node) -> Node:
        current = node
        while current.children:
            current = self._select_child(current)
        return current

    def _select_child(self, node: Node) -> Node:
        scores = [self._ucb(child, node.N) for child in node.children]
        return self._softmax_sample(node.children, scores)

    def _ucb(self, child: Node, parent_visits: int) -> float:
        return child.Xbar + self.c * math.sqrt(
            math.log(parent_visits + self.epsilon) / (child.N + self.epsilon)
        )

    def _softmax_sample(self, children: List[Node], scores: List[float]) -> Node:
        scaled = [s / self.tau for s in scores]
        max_score = max(scaled)
        exp_scores = [math.exp(s - max_score) for s in scaled]
        total = sum(exp_scores)
        probs = [s / total for s in exp_scores]
        r = self.rng.random()
        cumulative = 0.0
        for child, p in zip(children, probs):
            cumulative += p
            if r <= cumulative:
                return child
        return children[-1]

    def _simulate_and_evaluate(self, node: Node) -> "EvalOutcome":
        quick = run_quickscreen(node.code, node.blackboard)
        if not quick.passed:
            if quick.diagnostic is not None:
                self.coordinator.handle_diagnostic(quick.diagnostic, node.blackboard)
            reward = compute_reward(
                quick.passed_count,
                max(1, quick.total),
                quick.timeouts,
                quick.avg_runtime_s,
                node.code,
            )
            reward = min(reward, 0.6)
            return EvalOutcome(False, reward, node.code)

        deep = run_deep_evaluate(node.code, node.blackboard)
        if deep.passed:
            return EvalOutcome(True, 1.0, node.code)

        for diag in deep.diagnostics:
            self.coordinator.handle_diagnostic(diag, node.blackboard)
        reward = compute_reward(
            deep.passed_count,
            max(1, deep.total),
            deep.timeouts,
            deep.avg_runtime_s,
            node.code,
        )
        return EvalOutcome(False, reward, node.code)

    def _expand(self, node: Node) -> int:
        actions = self.coordinator.enumerate_actions((node.code, node.blackboard), node.blackboard)
        actions = self._select_subset(actions, self.expansion_budget)
        for action in actions:
            new_blackboard = node.blackboard.clone()
            new_code = action.apply(node.code, new_blackboard)
            child = Node(
                code=new_code,
                blackboard=new_blackboard,
                parent=node,
                action_taken=action.name,
            )
            node.add_child(child)
        return len(actions)

    def _select_subset(self, actions: List[Action], budget: int) -> List[Action]:
        if len(actions) <= budget:
            return actions
        return self.rng.sample(actions, budget)

    def _backpropagate(self, node: Node, reward: float) -> None:
        current: Optional[Node] = node
        while current is not None:
            current.N += 1
            current.Xbar = current.Xbar + (reward - current.Xbar) / current.N
            current = current.parent

@dataclass
class EvalOutcome:
    solved: bool
    reward: float
    code: str

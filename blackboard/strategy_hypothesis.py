from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, Optional

from blackboard.schemas import StrategyHypothesis

@dataclass
class StrategyHypothesisBlackboard:
    hypotheses: Dict[str, StrategyHypothesis] = field(default_factory=dict)
    bid_components: Dict[str, tuple[float, float, float]] = field(default_factory=dict)
    active_hypothesis_id: Optional[str] = None
    seed: int = 0

    def __post_init__(self) -> None:
        if not self.hypotheses:
            default = StrategyHypothesis(
                id="default",
                name="Baseline",
                applicability_conditions=["default"],
                complexity_upper_bound="O(n)",
                risk_flags=[],
                minimal_evidence_set=[],
                notes="Default baseline hypothesis.",
            )
            self.upsert_hypothesis(default)
            self.set_active_hypothesis(default.id)
            self.set_bid_components(default.id, p=0.5, c=0.5, r=0.5)

    def upsert_hypothesis(self, h: StrategyHypothesis) -> None:
        self.hypotheses[h.id] = h
        self.bid_components.setdefault(h.id, (0.5, 0.5, 0.5))

    def set_bid_components(self, h_id: str, p: float, c: float, r: float) -> None:
        self.bid_components[h_id] = (p, c, r)

    def compute_prior(
        self,
        alpha: float = 1.0,
        beta: float = 1.0,
        gamma: float = 1.0,
        temperature: float = 1.0,
    ) -> Dict[str, float]:
        ids = list(self.hypotheses.keys())
        if not ids:
            return {}
        comps = [self.bid_components.get(h_id, (0.5, 0.5, 0.5)) for h_id in ids]
        ps, cs, rs = zip(*comps)
        p_norm = _normalize(ps)
        c_norm = _normalize(cs)
        r_norm = _normalize(rs)

        scores = [
            alpha * p - beta * c - gamma * r
            for p, c, r in zip(p_norm, c_norm, r_norm)
        ]
        return _softmax(ids, scores, temperature)

    def sample_hypothesis(self) -> StrategyHypothesis:
        prior = self.compute_prior()
        ids = list(prior.keys())
        if not ids:
            return self.hypotheses["default"]
        rng = random.Random(self.seed)
        r = rng.random()
        cumulative = 0.0
        for h_id in ids:
            cumulative += prior[h_id]
            if r <= cumulative:
                return self.hypotheses[h_id]
        return self.hypotheses[ids[-1]]

    def get_active_hypothesis(self) -> StrategyHypothesis:
        if self.active_hypothesis_id and self.active_hypothesis_id in self.hypotheses:
            return self.hypotheses[self.active_hypothesis_id]
        return self.hypotheses["default"]

    def set_active_hypothesis(self, h_id: str) -> None:
        if h_id in self.hypotheses:
            self.active_hypothesis_id = h_id

def _normalize(values: tuple[float, ...]) -> list[float]:
    min_v = min(values)
    max_v = max(values)
    if max_v == min_v:
        return [0.5 for _ in values]
    return [(v - min_v) / (max_v - min_v) for v in values]

def _softmax(ids: list[str], scores: list[float], temperature: float) -> Dict[str, float]:
    scaled = [s / max(temperature, 1e-6) for s in scores]
    max_score = max(scaled)
    exp_scores = [math.exp(s - max_score) for s in scaled]
    total = sum(exp_scores)
    return {h_id: exp / total for h_id, exp in zip(ids, exp_scores)}

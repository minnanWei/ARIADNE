from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from blackboard.blackboard import Blackboard
from core.actions import Action
from agents.llm_client import call_llm

State = Tuple[str, Blackboard]


@dataclass
class BaseAgent:
    name: str
    temperature: float = 0.2
    max_tokens: int = 1024
    max_calls_per_iteration: int = 1
    use_cache: bool = True
    _cache: Dict[str, str] = field(default_factory=dict, init=False, repr=False)
    _calls_this_iteration: int = field(default=0, init=False, repr=False)

    def propose(self, state: State, blackboard: Blackboard) -> List[Action]:
        raise NotImplementedError

    def reset_iteration(self) -> None:
        self._calls_this_iteration = 0

    def _call_llm(self, prompt: str, state: State, blackboard: Blackboard) -> str:
        if self._calls_this_iteration >= self.max_calls_per_iteration:
            return ""
        cache_key = self._cache_key(state, blackboard)
        if self.use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        response = call_llm(prompt, temperature=self.temperature, max_tokens=self.max_tokens)
        self._calls_this_iteration += 1
        if self.use_cache:
            self._cache[cache_key] = response
        return response

    def _cache_key(self, state: State, blackboard: Blackboard) -> str:
        code, _ = state
        payload = {
            "agent": self.name,
            "code": code,
            "blackboard": blackboard.to_json(),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

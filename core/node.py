from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from blackboard.blackboard import Blackboard


@dataclass
class Node:
    code: str
    blackboard: Blackboard
    parent: Optional["Node"] = None
    children: List["Node"] = field(default_factory=list)
    action_taken: Optional[str] = None
    N: int = 0
    Xbar: float = 0.0

    def add_child(self, child: "Node") -> None:
        self.children.append(child)

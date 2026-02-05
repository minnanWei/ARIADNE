from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from blackboard.schemas import Diagnostic, Patch

@dataclass
class PatchRepairBlackboard:
    patches: Dict[str, Patch] = field(default_factory=dict)
    applied_patch_history: List[str] = field(default_factory=list)
    rejected_patches: Dict[str, str] = field(default_factory=dict)

    def propose_patch(self, patch: Patch) -> None:
        if patch.id not in self.patches:
            self.patches[patch.id] = patch

    def can_apply(self, patch_id: str, already_selected: Set[str]) -> Tuple[bool, str]:
        if patch_id not in self.patches:
            return False, "unknown patch"
        patch = self.patches[patch_id]
        for dep in patch.dependencies:
            if dep not in already_selected:
                return False, f"missing dependency {dep}"
        for conflict in patch.conflicts:
            if conflict in already_selected:
                return False, f"conflict with {conflict}"
        return True, "ok"

    def select_patch_subset(
        self,
        budget_k: int,
        w1: float = 1.0,
        w2: float = 1.0,
        w3: float = 1.0,
    ) -> List[Patch]:
        scored = []
        for patch in self.patches.values():
            score = w1 * patch.success_prob - w2 * patch.cost - w3 * patch.risk
            scored.append((score, patch))
        scored.sort(key=lambda x: x[0], reverse=True)
        selected: List[Patch] = []
        selected_ids: Set[str] = set()
        for _, patch in scored:
            if len(selected) >= budget_k:
                break
            ok, _ = self.can_apply(patch.id, selected_ids)
            if ok:
                selected.append(patch)
                selected_ids.add(patch.id)
        return selected

    def record_patch_outcome(self, patch_id: str, success: bool, diag: Diagnostic) -> None:
        if success:
            self.applied_patch_history.append(patch_id)
            return
        reason = diag.status.value
        self.rejected_patches[patch_id] = reason

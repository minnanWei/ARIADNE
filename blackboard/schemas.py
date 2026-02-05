from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DiagnosticStatus(str, Enum):
    WA = "WA"
    RE = "RE"
    TLE = "TLE"
    PASS = "PASS"
    UNKNOWN = "UNKNOWN"


class TestOrigin(str, Enum):
    APPS_EXAMPLE = "APPS_EXAMPLE"
    APPS_TEST = "APPS_TEST"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    MINIMIZED = "MINIMIZED"
    GENERATED_EXTREME = "GENERATED_EXTREME"
    GENERATED_RANDOM = "GENERATED_RANDOM"
    GENERATED_ENUM = "GENERATED_ENUM"
    MINIMIZATION_HINT = "MINIMIZATION_HINT"


class PatchLevel(str, Enum):
    L1_LOCAL = "L1_LOCAL"
    L2_STRUCTURAL = "L2_STRUCTURAL"
    L3_SYSTEM = "L3_SYSTEM"


@dataclass
class TestCase:
    input_data: str
    expected_output: Optional[str]
    origin: TestOrigin = TestOrigin.APPS_TEST
    weight: float = 1.0

    @property
    def input(self) -> str:
        return self.input_data

    @property
    def output(self) -> str:
        if self.expected_output is None:
            return ""
        return str(self.expected_output)


@dataclass
class Problem:
    name: str
    question: str
    starter_code: str
    examples: List[TestCase]
    tests: List[TestCase]


@dataclass
class TestCaseResult:
    testcase: TestCase
    actual_output: Optional[str]
    expected_output: Optional[str]


@dataclass
class Diagnostic:
    stage: str
    status: DiagnosticStatus | str
    test: Optional[TestCase]
    message: str
    actual_output: Optional[str] = None
    expected_output: Optional[str] = None
    runtime_s: Optional[float] = None
    notes: Dict[str, Any] = field(default_factory=dict)
    failing_tests: List[TestCaseResult] = field(default_factory=list)

    def __post_init__(self) -> None:
        if isinstance(self.status, str):
            try:
                self.status = DiagnosticStatus(self.status)
            except ValueError:
                self.status = DiagnosticStatus.UNKNOWN


@dataclass
class FailureRecord:
    status: DiagnosticStatus
    test: Optional[TestCase]
    stage: str
    message: str
    timestamp_s: float


@dataclass
class Patch:
    id: str
    level: PatchLevel
    description: str
    diff_like: Optional[str]
    preconditions: List[str]
    dependencies: List[str]
    conflicts: List[str]
    success_prob: float
    cost: float
    risk: float
    tags: List[str]


@dataclass
class StrategyHypothesis:
    id: str
    name: str
    applicability_conditions: List[str]
    complexity_upper_bound: str
    risk_flags: List[str]
    minimal_evidence_set: List[str]
    notes: str

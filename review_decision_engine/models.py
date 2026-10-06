from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Decision(str, Enum):
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    NOT_SELECTED_FOR_HUMAN_REVIEW = "NOT_SELECTED_FOR_HUMAN_REVIEW"


class MergeGateStatus(str, Enum):
    MERGE_ALLOWED = "MERGE_ALLOWED"
    MERGE_BLOCKED = "MERGE_BLOCKED"
    ANALYSIS_REQUIRED = "ANALYSIS_REQUIRED"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VerificationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    MISSING = "missing"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class Revision:
    base_sha: str
    head_sha: str

    def __post_init__(self) -> None:
        if not self.base_sha or not self.head_sha:
            raise ValueError("base_sha and head_sha are required")

    def matches_head(self, current_head_sha: str) -> bool:
        return self.head_sha == current_head_sha


@dataclass(frozen=True)
class ChangeFact:
    revision: Revision
    symbol: str
    change_type: str
    callee: str | None = None
    argument: str | None = None
    before_value: str | None = None
    after_value: str | None = None


@dataclass(frozen=True)
class RiskCase:
    revision: Revision
    code: str
    severity: Severity
    confidence: float
    fact: ChangeFact

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class Invariant:
    invariant_id: str
    description: str
    critical: bool = True


@dataclass(frozen=True)
class InvariantTouch:
    revision: Revision
    invariant: Invariant
    source_risk_code: str


@dataclass(frozen=True)
class VerificationEvidence:
    revision: Revision
    check_id: str
    status: VerificationStatus
    details: str = ""


@dataclass(frozen=True)
class AnalysisState:
    revision: Revision
    analysis_complete: bool
    facts: tuple[ChangeFact, ...] = field(default_factory=tuple)
    risks: tuple[RiskCase, ...] = field(default_factory=tuple)
    invariants: tuple[InvariantTouch, ...] = field(default_factory=tuple)
    verification: tuple[VerificationEvidence, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DecisionRecord:
    revision: Revision
    decision: Decision
    reason_codes: tuple[str, ...]

    def is_stale(self, current_head_sha: str) -> bool:
        return not self.revision.matches_head(current_head_sha)


@dataclass(frozen=True)
class HumanApproval:
    revision: Revision
    approved: bool


@dataclass(frozen=True)
class MergeGateResult:
    status: MergeGateStatus
    reason_codes: tuple[str, ...]

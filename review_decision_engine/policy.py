from __future__ import annotations

from collections.abc import Iterable

from .models import (
    AnalysisState,
    Decision,
    DecisionRecord,
    Severity,
    VerificationStatus,
)


def _append_once(reasons: list[str], code: str) -> None:
    if code not in reasons:
        reasons.append(code)


def _all_revisions(state: AnalysisState) -> Iterable[object]:
    yield from state.facts
    yield from state.risks
    yield from state.invariants
    yield from state.verification


def evaluate_review_decision(state: AnalysisState) -> DecisionRecord:
    """Fail closed: unknown, stale or unverified high-risk work stays with humans."""
    reasons: list[str] = []

    for item in _all_revisions(state):
        if item.revision != state.revision:
            _append_once(reasons, "STALE_EVIDENCE")

    if not state.analysis_complete:
        _append_once(reasons, "ANALYSIS_INCOMPLETE")

    if any(risk.severity is Severity.CRITICAL for risk in state.risks):
        _append_once(reasons, "CRITICAL_RISK")
    elif any(risk.severity is Severity.HIGH for risk in state.risks):
        _append_once(reasons, "HIGH_RISK")

    if any(touch.invariant.critical for touch in state.invariants):
        _append_once(reasons, "CRITICAL_INVARIANT_TOUCHED")

    statuses = {evidence.status for evidence in state.verification}
    if VerificationStatus.FAILED in statuses:
        _append_once(reasons, "VERIFICATION_FAILED")
    if statuses & {VerificationStatus.MISSING, VerificationStatus.UNAVAILABLE}:
        _append_once(reasons, "VERIFICATION_INCOMPLETE")

    decision = (
        Decision.HUMAN_REVIEW_REQUIRED
        if reasons
        else Decision.NOT_SELECTED_FOR_HUMAN_REVIEW
    )
    return DecisionRecord(
        revision=state.revision,
        decision=decision,
        reason_codes=tuple(reasons),
    )

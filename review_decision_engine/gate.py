from __future__ import annotations

from .models import (
    Decision,
    DecisionRecord,
    HumanApproval,
    MergeGateResult,
    MergeGateStatus,
)


def evaluate_merge_gate(
    decision: DecisionRecord,
    *,
    current_head_sha: str,
    approval: HumanApproval | None = None,
) -> MergeGateResult:
    if decision.is_stale(current_head_sha):
        return MergeGateResult(
            status=MergeGateStatus.ANALYSIS_REQUIRED,
            reason_codes=("STALE_DECISION",),
        )

    if decision.decision is Decision.NOT_SELECTED_FOR_HUMAN_REVIEW:
        return MergeGateResult(
            status=MergeGateStatus.MERGE_ALLOWED,
            reason_codes=(),
        )

    if approval is None:
        return MergeGateResult(
            status=MergeGateStatus.MERGE_BLOCKED,
            reason_codes=("HUMAN_APPROVAL_REQUIRED",),
        )

    if (
        approval.revision != decision.revision
        or not approval.revision.matches_head(current_head_sha)
    ):
        return MergeGateResult(
            status=MergeGateStatus.MERGE_BLOCKED,
            reason_codes=("STALE_APPROVAL",),
        )

    if not approval.approved:
        return MergeGateResult(
            status=MergeGateStatus.MERGE_BLOCKED,
            reason_codes=("HUMAN_APPROVAL_REQUIRED",),
        )

    return MergeGateResult(
        status=MergeGateStatus.MERGE_ALLOWED,
        reason_codes=(),
    )

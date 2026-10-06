from pathlib import Path

from review_decision_engine import (
    Decision,
    HumanApproval,
    MergeGateStatus,
    Revision,
    VerificationEvidence,
    VerificationStatus,
    analyze_python_change,
    evaluate_merge_gate,
)

FIXTURES = Path(__file__).parent / "fixtures" / "review_decision"


def _source(fixture: str, side: str) -> str:
    return (FIXTURES / fixture / f"{side}.py").read_text()


def test_vf_001_low_risk_change_is_not_selected_for_human_review() -> None:
    revision = Revision(base_sha="base-001", head_sha="head-001")

    result = analyze_python_change(
        _source("vf_001", "before"),
        _source("vf_001", "after"),
        revision=revision,
        symbol="greeting",
    )

    assert result.state.facts == ()
    assert result.decision.decision is Decision.NOT_SELECTED_FOR_HUMAN_REVIEW
    assert result.decision.reason_codes == ()


def test_vf_002_idempotency_mutation_requires_human_review() -> None:
    revision = Revision(base_sha="base-002", head_sha="head-002")
    verification = (
        VerificationEvidence(
            revision=revision,
            check_id="unit-charge-called",
            status=VerificationStatus.PASSED,
        ),
        VerificationEvidence(
            revision=revision,
            check_id="retry-same-request-id-single-charge",
            status=VerificationStatus.MISSING,
            details="No retry/idempotency integration test exists.",
        ),
    )

    result = analyze_python_change(
        _source("vf_002", "before"),
        _source("vf_002", "after"),
        revision=revision,
        symbol="PaymentWorker.handle",
        verification=verification,
    )

    assert len(result.state.facts) == 1
    fact = result.state.facts[0]
    assert fact.argument == "idempotency_key"
    assert fact.before_value == "command.request_id"
    assert fact.after_value == "f'{command.request_id}:{attempt}'"

    assert [risk.code for risk in result.state.risks] == [
        "PAYMENT_IDEMPOTENCY_KEY_MUTATION"
    ]
    assert [touch.invariant.invariant_id for touch in result.state.invariants] == [
        "PAYMENT-001"
    ]
    assert result.decision.decision is Decision.HUMAN_REVIEW_REQUIRED
    assert result.decision.reason_codes == (
        "CRITICAL_RISK",
        "CRITICAL_INVARIANT_TOUCHED",
        "VERIFICATION_INCOMPLETE",
    )


def test_vf_003_unknown_is_not_treated_as_safe() -> None:
    revision = Revision(base_sha="base-003", head_sha="head-003")

    result = analyze_python_change(
        _source("vf_003", "before"),
        _source("vf_003", "after"),
        revision=revision,
        symbol="update_profile",
        analysis_complete=False,
    )

    assert result.decision.decision is Decision.HUMAN_REVIEW_REQUIRED
    assert result.decision.reason_codes == ("ANALYSIS_INCOMPLETE",)


def test_stale_evidence_fails_closed() -> None:
    revision = Revision(base_sha="base-004", head_sha="head-004")
    stale_revision = Revision(base_sha="base-004", head_sha="older-head")
    verification = (
        VerificationEvidence(
            revision=stale_revision,
            check_id="integration",
            status=VerificationStatus.PASSED,
        ),
    )

    result = analyze_python_change(
        _source("vf_001", "before"),
        _source("vf_001", "after"),
        revision=revision,
        symbol="greeting",
        verification=verification,
    )

    assert result.decision.decision is Decision.HUMAN_REVIEW_REQUIRED
    assert result.decision.reason_codes == ("STALE_EVIDENCE",)


def test_new_commit_invalidates_previous_decision_and_approval() -> None:
    revision = Revision(base_sha="base-005", head_sha="head-005")
    verification = (
        VerificationEvidence(
            revision=revision,
            check_id="retry-same-request-id-single-charge",
            status=VerificationStatus.MISSING,
        ),
    )
    result = analyze_python_change(
        _source("vf_002", "before"),
        _source("vf_002", "after"),
        revision=revision,
        symbol="PaymentWorker.handle",
        verification=verification,
    )
    approval = HumanApproval(revision=revision, approved=True)

    gate = evaluate_merge_gate(
        result.decision,
        current_head_sha="head-006",
        approval=approval,
    )

    assert gate.status is MergeGateStatus.ANALYSIS_REQUIRED
    assert gate.reason_codes == ("STALE_DECISION",)


def test_current_human_approval_unblocks_required_review() -> None:
    revision = Revision(base_sha="base-006", head_sha="head-006")
    verification = (
        VerificationEvidence(
            revision=revision,
            check_id="retry-same-request-id-single-charge",
            status=VerificationStatus.MISSING,
        ),
    )
    result = analyze_python_change(
        _source("vf_002", "before"),
        _source("vf_002", "after"),
        revision=revision,
        symbol="PaymentWorker.handle",
        verification=verification,
    )

    blocked = evaluate_merge_gate(result.decision, current_head_sha=revision.head_sha)
    approved = evaluate_merge_gate(
        result.decision,
        current_head_sha=revision.head_sha,
        approval=HumanApproval(revision=revision, approved=True),
    )

    assert blocked.status is MergeGateStatus.MERGE_BLOCKED
    assert blocked.reason_codes == ("HUMAN_APPROVAL_REQUIRED",)
    assert approved.status is MergeGateStatus.MERGE_ALLOWED
    assert approved.reason_codes == ()

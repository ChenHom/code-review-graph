from __future__ import annotations

from .models import ChangeFact, Invariant, InvariantTouch, RiskCase, Severity

PAYMENT_IDEMPOTENCY_INVARIANT = Invariant(
    invariant_id="PAYMENT-001",
    description=(
        "Retrying the same logical payment must preserve the same idempotency identity."
    ),
    critical=True,
)


def detect_risks(facts: tuple[ChangeFact, ...]) -> tuple[RiskCase, ...]:
    risks: list[RiskCase] = []

    for fact in facts:
        argument = (fact.argument or "").replace("_", "").lower()
        if argument != "idempotencykey":
            continue

        risks.append(
            RiskCase(
                revision=fact.revision,
                code="PAYMENT_IDEMPOTENCY_KEY_MUTATION",
                severity=Severity.CRITICAL,
                confidence=0.99,
                fact=fact,
            )
        )

    return tuple(risks)


def map_invariants(risks: tuple[RiskCase, ...]) -> tuple[InvariantTouch, ...]:
    touches: list[InvariantTouch] = []

    for risk in risks:
        if risk.code != "PAYMENT_IDEMPOTENCY_KEY_MUTATION":
            continue
        touches.append(
            InvariantTouch(
                revision=risk.revision,
                invariant=PAYMENT_IDEMPOTENCY_INVARIANT,
                source_risk_code=risk.code,
            )
        )

    return tuple(touches)

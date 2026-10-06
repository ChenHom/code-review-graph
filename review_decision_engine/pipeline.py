from __future__ import annotations

from dataclasses import dataclass

from .models import AnalysisState, DecisionRecord, Revision, VerificationEvidence
from .normalizer import normalize_python_keyword_argument_changes
from .policy import evaluate_review_decision
from .rules import detect_risks, map_invariants


@dataclass(frozen=True)
class AnalysisResult:
    state: AnalysisState
    decision: DecisionRecord


def analyze_python_change(
    before_source: str,
    after_source: str,
    *,
    revision: Revision,
    symbol: str,
    verification: tuple[VerificationEvidence, ...] = (),
    analysis_complete: bool = True,
) -> AnalysisResult:
    facts = normalize_python_keyword_argument_changes(
        before_source,
        after_source,
        revision=revision,
        symbol=symbol,
    )
    risks = detect_risks(facts)
    invariants = map_invariants(risks)
    state = AnalysisState(
        revision=revision,
        analysis_complete=analysis_complete,
        facts=facts,
        risks=risks,
        invariants=invariants,
        verification=verification,
    )
    return AnalysisResult(state=state, decision=evaluate_review_decision(state))

from __future__ import annotations

import ast

from .models import ChangeFact, Revision


def _keyword_arguments(source: str) -> dict[tuple[str, str], str]:
    tree = ast.parse(source)
    arguments: dict[tuple[str, str], str] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = ast.unparse(node.func)
        for keyword in node.keywords:
            if keyword.arg is None:
                continue
            arguments[(callee, keyword.arg)] = ast.unparse(keyword.value)

    return arguments


def normalize_python_keyword_argument_changes(
    before_source: str,
    after_source: str,
    *,
    revision: Revision,
    symbol: str,
) -> tuple[ChangeFact, ...]:
    """Convert Python keyword-argument mutations into deterministic change facts.

    The first vertical slice intentionally handles only calls that exist on both sides
    of the change. Added/removed calls will be handled by later normalizers.
    """
    before = _keyword_arguments(before_source)
    after = _keyword_arguments(after_source)
    facts: list[ChangeFact] = []

    for key in sorted(before.keys() & after.keys()):
        before_value = before[key]
        after_value = after[key]
        if before_value == after_value:
            continue

        callee, argument = key
        facts.append(
            ChangeFact(
                revision=revision,
                symbol=symbol,
                change_type="argument_expression_changed",
                callee=callee,
                argument=argument,
                before_value=before_value,
                after_value=after_value,
            )
        )

    return tuple(facts)

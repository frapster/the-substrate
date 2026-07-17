"""
governed_version.py, RUN-TIME: one small, generic evaluator that resolves a
ticket's routing outcome by reading facts.py.

This is the "after" half of the AI:code ratio demo. It contains no knowledge of
plan tiers, severities, or queues, that meaning lives entirely in facts.py's data
rows. Growing the feature (new business cases) means adding fact rows; this file
never changes. That's the countable claim ratio_demo.py demonstrates: 90% AI
(governed, run-time, fact-driven), 10% mechanical (this fixed evaluator).

If no fact governs a ticket, the evaluator does NOT guess: it abstains and returns
`hitl_required`, fail-closed. Contrast with code_version.py's `else` branch, which
silently returns a default with no signal that it was guessing.

Standard library only.
"""

from __future__ import annotations

from typing import Optional

import facts as _facts_module


def _reasoning_step(ticket: dict, fact: dict) -> bool:
    """Mocked deterministic 'reasoning': does this ticket satisfy this fact's
    governing conditions? In a real governed run-time system this step is a
    bounded, evidence-checked model call; here it's a deterministic stand-in so
    the demo has no external dependency. The SHAPE is the same, though: every
    condition in the fact must be satisfied by evidence present on the ticket."""
    return all(ticket.get(key) == value for key, value in fact["conditions"].items())


def evaluate(ticket: dict, facts: Optional[list[dict]] = None) -> dict:
    """The one generic evaluator. Walks the fact table in order and returns the
    first fact whose conditions the ticket satisfies. This function has no
    per-case logic: it is the same code whether the table holds 9 facts or 900.

    No fact matches? FAIL-CLOSED: abstain rather than silently default. A human
    has to add the missing fact row before this ticket can be routed."""
    table = facts if facts is not None else _facts_module.FACTS
    for fact in table:
        if _reasoning_step(ticket, fact):
            return dict(fact["outcome"])
    return {
        "status": "hitl_required",
        "reason": "no governing fact matches this ticket, abstaining rather than guessing",
    }

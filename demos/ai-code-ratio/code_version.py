"""
code_version.py, WRITE-TIME: support-ticket routing as a hand-authored branch tree.

This is the "before" half of the AI:code ratio demo. The feature: given a ticket's
`plan_tier` and `severity`, decide which queue it lands in and what escalation tier
(if any) fires. Every business case a product owner asks for becomes one more
`elif`: the requirement is baked into control flow at write-time, and it can only
change by editing and redeploying this file.

`route_ticket()` here covers the BASE requirement only (9 cases: 3 plan tiers ×
3 severities). `code_version_v2.py` is this same feature after three new cases
(critical severity) are added. See that file's docstring for the diff.

Standard library only. `count_branches()`/`count_decision_loc()` measure this file's
own decision tree honestly, by parsing its own source with `ast`: no hand-typed
numbers, so the delta printed by ratio_demo.py is a real count, not an estimate.
"""

from __future__ import annotations

import ast
import inspect


def route_ticket(ticket: dict) -> dict:
    """Route a ticket by hand-authored if/elif chain. Each business case below is a
    branch a developer wrote and shipped; there is no data table backing this: the
    requirement IS the code."""
    plan_tier = ticket.get("plan_tier")
    severity = ticket.get("severity")

    if plan_tier == "free" and severity == "low":
        return {"queue": "standard", "escalation": None}
    elif plan_tier == "free" and severity == "medium":
        return {"queue": "standard", "escalation": None}
    elif plan_tier == "free" and severity == "high":
        return {"queue": "standard", "escalation": "tier1"}
    elif plan_tier == "pro" and severity == "low":
        return {"queue": "priority", "escalation": None}
    elif plan_tier == "pro" and severity == "medium":
        return {"queue": "priority", "escalation": None}
    elif plan_tier == "pro" and severity == "high":
        return {"queue": "priority", "escalation": "tier2"}
    elif plan_tier == "enterprise" and severity == "low":
        return {"queue": "white_glove", "escalation": None}
    elif plan_tier == "enterprise" and severity == "medium":
        return {"queue": "white_glove", "escalation": "tier2"}
    elif plan_tier == "enterprise" and severity == "high":
        return {"queue": "white_glove", "escalation": "tier3"}
    else:
        # No branch matches (e.g. severity == "critical" isn't handled yet). The
        # code silently falls through to a generic default. It does not know it's
        # guessing. This is the fail-open failure mode ratio_demo.py contrasts
        # against governed_version.py's fail-closed abstain.
        return {"queue": "standard", "escalation": None}


def count_branches() -> int:
    """Parse this module's own source and count the `if`/`elif` decision points in
    route_ticket(). An honest count via stdlib `ast`: in Python's
    AST an `elif` is a nested `If` in the parent's `orelse`, so walking for
    `ast.If` nodes counts every branch, including elifs."""
    source = inspect.getsource(route_ticket)
    tree = ast.parse(source)
    return sum(1 for node in ast.walk(tree) if isinstance(node, ast.If))


def count_decision_loc() -> int:
    """Count non-blank source lines of route_ticket(), the write-time cost in
    lines a developer had to author and a reviewer had to read for this feature."""
    source = inspect.getsource(route_ticket)
    return len([line for line in source.splitlines() if line.strip()])

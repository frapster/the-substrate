"""
code_version_v2.py — WRITE-TIME: the same routing feature, after three new business
cases (critical-severity tickets for each plan tier) were added.

This is a SEPARATE file rather than an in-place edit of code_version.py so
ratio_demo.py can honestly diff "before" and "after" by parsing two real files with
`ast`, instead of simulating an edit. The only change from code_version.py is the
three new `elif` branches marked below — everything else is identical.

Standard library only.
"""

from __future__ import annotations

import ast
import inspect


def route_ticket(ticket: dict) -> dict:
    """Same hand-authored if/elif chain as code_version.py, plus three new branches
    for severity == "critical" — a new business case that arrived after the base
    feature shipped. Each new case costs a new branch here."""
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
    # --- new business cases: critical severity (3 new branches) -------------------
    elif plan_tier == "free" and severity == "critical":
        return {"queue": "standard_urgent", "escalation": "tier1"}
    elif plan_tier == "pro" and severity == "critical":
        return {"queue": "priority_urgent", "escalation": "tier3"}
    elif plan_tier == "enterprise" and severity == "critical":
        return {"queue": "white_glove", "escalation": "tier4_incident"}
    else:
        return {"queue": "standard", "escalation": None}


def count_branches() -> int:
    """Same counting method as code_version.py — see that file for why `ast.If`
    walking is the honest measure."""
    source = inspect.getsource(route_ticket)
    tree = ast.parse(source)
    return sum(1 for node in ast.walk(tree) if isinstance(node, ast.If))


def count_decision_loc() -> int:
    """Same counting method as code_version.py."""
    source = inspect.getsource(route_ticket)
    return len([line for line in source.splitlines() if line.strip()])

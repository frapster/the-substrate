"""
facts.py — RUN-TIME: the fact table for ticket routing eligibility.

This is the data half of the "after" feature. Each fact maps a governing condition
(a set of ticket attributes) to an outcome (a queue and an escalation target).
governed_version.py's evaluator reads this table; it contains no knowledge of plan
tiers, severities, or queues itself — that meaning lives here, in facts, not in code.

Adding a business case means adding a fact ROW. The evaluator does not change.
Removing/reverting a fact row reverts the behavior — the "revert-the-fact litmus"
ratio_demo.py exercises: git-revert a data row and the system's decisions revert
with it, with zero code change.
"""

from __future__ import annotations

# BASE_FACTS: the original requirement — route by plan tier × severity, 9 cases.
# This is the exact same feature code_version.py hand-authors as 9 elif branches.
BASE_FACTS: list[dict] = [
    {"conditions": {"plan_tier": "free", "severity": "low"}, "outcome": {"queue": "standard", "escalation": None}},
    {"conditions": {"plan_tier": "free", "severity": "medium"}, "outcome": {"queue": "standard", "escalation": None}},
    {"conditions": {"plan_tier": "free", "severity": "high"}, "outcome": {"queue": "standard", "escalation": "tier1"}},
    {"conditions": {"plan_tier": "pro", "severity": "low"}, "outcome": {"queue": "priority", "escalation": None}},
    {"conditions": {"plan_tier": "pro", "severity": "medium"}, "outcome": {"queue": "priority", "escalation": None}},
    {"conditions": {"plan_tier": "pro", "severity": "high"}, "outcome": {"queue": "priority", "escalation": "tier2"}},
    {"conditions": {"plan_tier": "enterprise", "severity": "low"}, "outcome": {"queue": "white_glove", "escalation": None}},
    {"conditions": {"plan_tier": "enterprise", "severity": "medium"}, "outcome": {"queue": "white_glove", "escalation": "tier2"}},
    {"conditions": {"plan_tier": "enterprise", "severity": "high"}, "outcome": {"queue": "white_glove", "escalation": "tier3"}},
]

# NEW_FACTS: the three new business cases from the growth scenario — critical
# severity, which BASE_FACTS never covered. These are the governed-path equivalent
# of the three new elif branches added in code_version_v2.py. Adding them is a data
# change only; governed_version.py is untouched.
NEW_FACTS: list[dict] = [
    {"conditions": {"plan_tier": "free", "severity": "critical"}, "outcome": {"queue": "standard_urgent", "escalation": "tier1"}},
    {"conditions": {"plan_tier": "pro", "severity": "critical"}, "outcome": {"queue": "priority_urgent", "escalation": "tier3"}},
    {"conditions": {"plan_tier": "enterprise", "severity": "critical"}, "outcome": {"queue": "white_glove", "escalation": "tier4_incident"}},
]

# FACTS is the table the evaluator reads by default — the currently-governing set.
# ratio_demo.py starts with FACTS == BASE_FACTS, then shows growth by passing
# BASE_FACTS + NEW_FACTS explicitly, and reversion by passing BASE_FACTS again.
FACTS: list[dict] = list(BASE_FACTS)

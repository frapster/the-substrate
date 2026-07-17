"""
gate.py: a minimal, deny-by-default policy gate that refuses over-scoped actions
BEFORE they execute.

This is a clean-room, dependency-free implementation of the *mechanism* the-substrate
claims in its prose (README.md, BOSS-STANDARD.md: agents may only act within a
registered, bounded surface) and the rule set out in
docs/adr/ADR-0002-deny-by-default-roster.md ("omission is prohibition"). It is a
generic authorization primitive (a closed roster checked against blast-radius caps)
and contains none of the BOSNet.io engine, schema, or kernel. It exists to make a
published claim *runnable and checkable* by a stranger.

The idea in one line:

    propose(action, scope) → proceed | escalated | blocked: decided BEFORE execution

An action not on the roster cannot be proposed into existence by an agent; a registered
action whose scope exceeds its hard ceiling is blocked; a scope between the soft cap and
the hard ceiling is escalated to a human. Every failure mode here fails CLOSED: a missing
or unreadable policy blocks rather than lets the action pass.

Standard library only (dataclasses, typing). Runs on any Python 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# Risk tiers, lowest to highest blast radius. Purely descriptive: the tier does not
# itself gate anything; the caps below do. It exists so a human reviewing the roster
# can triage at a glance.
TIERS = ("yellow", "orange", "red", "purple")


@dataclass
class Policy:
    """The registered ceiling for one action. `soft_cap` triggers escalation;
    `hard_ceiling` is the absolute limit past which nothing proceeds, ever.
    Caps are keyed by scope dimension, e.g. {"max_rows": 100} or {"max_usd": 500}."""

    tier: str
    soft_cap: dict[str, float]
    hard_ceiling: dict[str, float]

    def __post_init__(self) -> None:
        if self.tier not in TIERS:
            raise ValueError(f"unknown risk tier {self.tier!r}; must be one of {TIERS}")


@dataclass
class Decision:
    """The outcome of one propose() call. `outcome` is the only thing a caller should
    branch on; `reason` is for a human (or an audit log) to read."""

    outcome: str  # "proceed" | "escalated" | "blocked"
    reason: str
    action: str
    scope: dict[str, Any] = field(default_factory=dict)

    def short(self) -> str:
        return f"{self.outcome}: {self.reason}"

    def __bool__(self) -> bool:  # so callers can write `if gate.propose(...):`
        return self.outcome == "proceed"


@dataclass
class Gate:
    """A closed roster of registered actions, each with a risk tier and blast-radius
    caps. `propose()` is the only entry point: there is deliberately no way to act
    without going through it first, and no way to register an action mid-flight from
    inside propose(); registration is a separate, auditable step (`register`)."""

    roster: dict[str, Policy] = field(default_factory=dict)

    def register(self, action: str, tier: str, soft_cap: dict[str, float], hard_ceiling: dict[str, float]) -> None:
        """Add an action to the closed roster. This is the ONLY way an action becomes
        proposable: anything not registered here is prohibited by omission."""
        self.roster[action] = Policy(tier=tier, soft_cap=soft_cap, hard_ceiling=hard_ceiling)

    def propose(self, action: str, scope: dict[str, float]) -> Decision:
        """Decide whether `action` may proceed with the given `scope`, BEFORE it runs.

        Fail-closed at every step:
          1. action not on the roster            → blocked ("omission is prohibition")
          2. policy missing/unreadable caps       → blocked (never guess a ceiling)
          3. scope exceeds the hard ceiling       → blocked
          4. scope exceeds the soft cap           → escalated (needs HITL)
          5. within caps                          → proceed
        """
        policy = self.roster.get(action)
        if policy is None:
            return Decision(
                outcome="blocked",
                reason=f"'{action}' is not on the roster, omission is prohibition",
                action=action,
                scope=scope,
            )

        if not policy.hard_ceiling:
            # A registered action with no readable hard ceiling is a policy failure,
            # not permission to proceed. Fail closed: block rather than allow past
            # a ceiling we cannot confirm.
            return Decision(
                outcome="blocked",
                reason=f"'{action}' has no readable hard ceiling, fail-closed",
                action=action,
                scope=scope,
            )

        for dimension, requested in scope.items():
            ceiling = policy.hard_ceiling.get(dimension)
            if ceiling is None:
                # Scope names a dimension the policy never capped, same fail-closed
                # logic: an uncapped dimension is an unreadable ceiling, not a green light.
                return Decision(
                    outcome="blocked",
                    reason=f"'{action}' has no hard ceiling for '{dimension}', fail-closed",
                    action=action,
                    scope=scope,
                )
            if requested > ceiling:
                return Decision(
                    outcome="blocked",
                    reason=(
                        f"'{action}' requested {dimension}={requested:,} exceeds hard ceiling "
                        f"{ceiling:,} (tier={policy.tier})"
                    ),
                    action=action,
                    scope=scope,
                )

        for dimension, requested in scope.items():
            soft = policy.soft_cap.get(dimension)
            if soft is not None and requested > soft:
                return Decision(
                    outcome="escalated",
                    reason=(
                        f"'{action}' requested {dimension}={requested:,} exceeds soft cap "
                        f"{soft:,} (tier={policy.tier}), needs human-in-the-loop"
                    ),
                    action=action,
                    scope=scope,
                )

        return Decision(
            outcome="proceed",
            reason=f"'{action}' within caps (tier={policy.tier})",
            action=action,
            scope=scope,
        )

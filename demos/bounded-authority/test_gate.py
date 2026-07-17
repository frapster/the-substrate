"""
test_gate.py — proof that the gate is deny-by-default and fails closed.

Run it:

    python demos/bounded-authority/test_gate.py
    # or:  python -m unittest discover -s demos/bounded-authority

Standard-library `unittest` only — no pytest, no install.

The important tests here are the NEGATIVE ones: they assert that propose() *refuses*,
and refuses for the RIGHT reason, when an action is unregistered, over its hard
ceiling, over its soft cap, or missing a readable policy. A deny-by-default claim you
can't see refuse under those conditions is worthless — so these tests exist to see it
refuse.
"""

from __future__ import annotations

import os
import sys
import unittest

# Make `gate` importable no matter which directory the tests are launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gate import Gate  # noqa: E402


def _seeded_gate() -> Gate:
    gate = Gate()
    gate.register(
        "send_email", tier="yellow",
        soft_cap={"max_recipients": 50}, hard_ceiling={"max_recipients": 200},
    )
    gate.register(
        "grant_refund", tier="orange",
        soft_cap={"max_usd": 100}, hard_ceiling={"max_usd": 1000},
    )
    gate.register(
        "delete_rows", tier="red",
        soft_cap={"max_rows": 20}, hard_ceiling={"max_rows": 100},
    )
    return gate


class HappyPath(unittest.TestCase):
    def test_within_budget_proceeds(self):
        gate = _seeded_gate()
        decision = gate.propose("grant_refund", {"max_usd": 40})
        self.assertEqual(decision.outcome, "proceed")
        self.assertTrue(decision)

    def test_within_hard_ceiling_but_over_soft_cap_escalates(self):
        gate = _seeded_gate()
        decision = gate.propose("grant_refund", {"max_usd": 500})
        self.assertEqual(decision.outcome, "escalated")
        self.assertIn("soft cap", decision.reason)
        self.assertIn("human-in-the-loop", decision.reason)

    def test_exactly_at_soft_cap_proceeds(self):
        # The boundary belongs to "proceed" — only strictly exceeding a cap triggers
        # escalation or blocking.
        gate = _seeded_gate()
        decision = gate.propose("grant_refund", {"max_usd": 100})
        self.assertEqual(decision.outcome, "proceed")

    def test_exactly_at_hard_ceiling_escalates_not_blocks(self):
        gate = _seeded_gate()
        decision = gate.propose("delete_rows", {"max_rows": 100})
        self.assertEqual(decision.outcome, "escalated")


class RefusalIsEnforced(unittest.TestCase):
    """Each test proposes an action that must NOT proceed, and asserts the gate
    refuses it for the right reason before anything runs."""

    def test_unregistered_action_is_blocked(self):
        gate = _seeded_gate()
        decision = gate.propose("rotate_prod_credentials", {"max_usd": 0})
        self.assertEqual(decision.outcome, "blocked")
        self.assertIn("omission is prohibition", decision.reason)
        self.assertFalse(decision)

    def test_over_hard_ceiling_is_blocked(self):
        gate = _seeded_gate()
        decision = gate.propose("delete_rows", {"max_rows": 10_000})
        self.assertEqual(decision.outcome, "blocked")
        self.assertIn("exceeds hard ceiling", decision.reason)

    def test_over_soft_cap_but_under_hard_ceiling_is_escalated_not_blocked(self):
        gate = _seeded_gate()
        decision = gate.propose("delete_rows", {"max_rows": 50})
        self.assertEqual(decision.outcome, "escalated")
        self.assertIn("soft cap", decision.reason)

    def test_missing_policy_is_blocked_fail_closed(self):
        # A registered action whose hard ceiling is empty (unreadable policy) must
        # never be allowed to pass — fail-closed, not fail-open.
        gate = Gate()
        gate.register("wipe_cache", tier="orange", soft_cap={}, hard_ceiling={})
        decision = gate.propose("wipe_cache", {"max_usd": 1})
        self.assertEqual(decision.outcome, "blocked")
        self.assertIn("no readable hard ceiling", decision.reason)

    def test_scope_dimension_without_a_ceiling_is_blocked_fail_closed(self):
        # The action IS registered and has a ceiling for one dimension, but the
        # proposal names a dimension the policy never capped. Still fail-closed.
        gate = _seeded_gate()
        decision = gate.propose("grant_refund", {"max_recipients": 5})
        self.assertEqual(decision.outcome, "blocked")
        self.assertIn("no hard ceiling", decision.reason)

    def test_unknown_tier_is_rejected_at_registration(self):
        gate = Gate()
        with self.assertRaises(ValueError):
            gate.register("do_thing", tier="ultraviolet", soft_cap={}, hard_ceiling={"max_usd": 1})


if __name__ == "__main__":
    unittest.main(verbosity=2)

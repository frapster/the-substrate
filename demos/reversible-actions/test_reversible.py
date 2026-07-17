"""
test_reversible.py — proof that the store is gated, append-only, and recoverable.

Run it:

    python demos/reversible-actions/test_reversible.py
    # or:  python -m unittest discover -s demos/reversible-actions

Standard-library `unittest` only — no pytest, no install.

The important tests here are the NEGATIVE ones: they assert that in-place mutation
FAILS CLOSED, that an ungated high-impact action is REFUSED, and that a tampered
version is caught by verify_chain(). A "reversible" claim you can't see hold under an
attempted rewrite is worthless — so these tests exist to see it hold.
"""

from __future__ import annotations

import os
import sys
import unittest

# Make `reversible` importable no matter which directory the tests are launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reversible import (  # noqa: E402
    AppendOnlyViolation,
    Store,
    UngatedHighImpactError,
    compute_state_hash,
)


def _seed() -> Store:
    store = Store()
    store.apply({"balance_usd": 100, "status": "active"}, gated=True)
    store.apply({"status": "verified"}, gated=True)
    store.apply({"tier": "gold"}, gated=True)
    return store


class HappyPath(unittest.TestCase):
    def test_genesis_state_is_empty(self):
        store = Store()
        self.assertEqual(store.state, {})
        self.assertEqual(store.head.index, 0)

    def test_apply_appends_new_version_and_preserves_predecessor(self):
        store = _seed()
        self.assertEqual(len(store.versions), 4)  # genesis + 3 applies
        # The predecessor's state is untouched by later applies.
        self.assertEqual(store.versions[1].state, {"balance_usd": 100, "status": "active"})
        self.assertEqual(store.state, {"balance_usd": 100, "status": "verified", "tier": "gold"})

    def test_state_hash_matches_recomputation(self):
        store = _seed()
        for v in store.versions:
            self.assertEqual(compute_state_hash(v.state), v.state_hash)

    def test_gated_high_impact_applies(self):
        store = Store()
        v = store.apply({"balance_usd": 0}, high_impact=True, gated=True, note="approved refund")
        self.assertEqual(v.state, {"balance_usd": 0})

    def test_version_chain_verifies(self):
        result = _seed().verify_chain()
        self.assertTrue(result.ok)
        self.assertEqual(result.checked, 4)
        self.assertIsNone(result.broken_index)

    def test_operator_destructive_writes_audit_note_and_new_version(self):
        store = _seed()
        pre_count = len(store.versions)
        v = store.operator_destructive(reason="compliance purge #4471")
        self.assertEqual(len(store.versions), pre_count + 1)  # appended, not overwritten
        self.assertTrue(v.operator_destructive)
        self.assertIn("compliance purge #4471", v.note)
        # The purge itself is recoverable, like any other version.
        self.assertEqual(store.versions[pre_count - 1].state, {"balance_usd": 100, "status": "verified", "tier": "gold"})


class GuardsEnforced(unittest.TestCase):
    """Each test attempts a rewrite of committed history or an ungated high-impact
    action, and asserts it is refused — for the right reason."""

    def test_in_place_update_fails_closed(self):
        store = _seed()
        with self.assertRaises(AppendOnlyViolation) as ctx:
            store._update_in_place(1, {"status": "banned"})
        self.assertIn("append-only", str(ctx.exception))
        # The targeted version is provably untouched.
        self.assertEqual(store.versions[1].state, {"balance_usd": 100, "status": "active"})

    def test_in_place_delete_fails_closed(self):
        store = _seed()
        pre_count = len(store.versions)
        with self.assertRaises(AppendOnlyViolation) as ctx:
            store._delete_in_place(0)
        self.assertIn("append-only", str(ctx.exception))
        self.assertEqual(len(store.versions), pre_count)  # nothing was removed

    def test_ungated_high_impact_refused(self):
        store = _seed()
        pre_count = len(store.versions)
        with self.assertRaises(UngatedHighImpactError) as ctx:
            store.apply({"balance_usd": 0}, high_impact=True)  # gated defaults to False
        self.assertIn("gated=True", str(ctx.exception))
        self.assertEqual(len(store.versions), pre_count)  # refused before it could apply

    def test_operator_destructive_requires_a_reason(self):
        store = _seed()
        with self.assertRaises(ValueError) as ctx:
            store.operator_destructive(reason="")
        self.assertIn("reason", str(ctx.exception))

    def test_restore_reproduces_exact_prior_state_hash(self):
        store = _seed()
        checkpoint = store.head.index  # version 3, tier=gold
        checkpoint_hash = store.head.state_hash
        store.apply({"tier": "platinum", "status": "flagged"}, gated=True)  # drift away
        self.assertNotEqual(store.state_hash, checkpoint_hash)
        restored = store.restore(checkpoint)
        self.assertEqual(restored.state_hash, checkpoint_hash)
        self.assertEqual(restored.state, store.versions[checkpoint].state)
        self.assertEqual(store.state_hash, checkpoint_hash)  # head now matches the snapshot

    def test_restore_is_supersede_forward_not_a_rewind(self):
        store = _seed()
        pre_count = len(store.versions)
        store.restore(0)
        # Recovery appends; it never truncates or rewrites history.
        self.assertEqual(len(store.versions), pre_count + 1)
        self.assertEqual(store.versions[pre_count - 1].state, {"balance_usd": 100, "status": "verified", "tier": "gold"})

    def test_tampered_version_is_caught_by_verify_chain(self):
        # Reach past the append-only guard the way an attacker with raw storage
        # access would — edit a stored version's state directly, without going
        # through apply()/restore(), so its state_hash goes stale.
        store = _seed()
        tampered = dict(store.versions[2].state)
        tampered["status"] = "compromised"
        store.versions[2].state = tampered  # hash left unrecomputed
        result = store.verify_chain()
        self.assertFalse(result.ok)
        self.assertEqual(result.broken_index, 2)
        self.assertIn("altered", result.reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)

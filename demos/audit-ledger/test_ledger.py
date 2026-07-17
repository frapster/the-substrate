"""
test_ledger.py — proof that the ledger is tamper-evident.

Run it:

    python demos/audit-ledger/test_ledger.py
    # or:  python -m unittest discover -s demos/audit-ledger

Standard-library `unittest` only — no pytest, no install.

The important tests here are the NEGATIVE ones: they assert that verify() *fails*,
and fails for the RIGHT reason, when history is altered three different ways
(body edit, deletion, reordering). A tamper-evidence claim you can't see fail
under tampering is worthless — so these tests exist to see it fail.
"""

from __future__ import annotations

import os
import sys
import unittest

# Make `ledger` importable no matter which directory the tests are launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ledger import GENESIS_PREV_HASH, Ledger, compute_hash  # noqa: E402


def _seed(n: int = 5) -> Ledger:
    ledger = Ledger()
    for i in range(n):
        ledger.append({"action": f"act_{i}", "model": "claude", "verdict": "allow"})
    return ledger


class HappyPath(unittest.TestCase):
    def test_empty_ledger_verifies(self):
        self.assertTrue(Ledger().verify().ok)

    def test_intact_chain_verifies(self):
        result = _seed(5).verify()
        self.assertTrue(result.ok)
        self.assertEqual(result.checked, 5)
        self.assertIsNone(result.broken_index)

    def test_genesis_anchor(self):
        self.assertEqual(_seed(1).rows[0].prev_hash, GENESIS_PREV_HASH)

    def test_each_row_links_to_previous(self):
        ledger = _seed(4)
        for i in range(1, len(ledger.rows)):
            self.assertEqual(ledger.rows[i].prev_hash, ledger.rows[i - 1].hash)

    def test_hashes_are_deterministic(self):
        # Same bodies in the same order → identical chain hashes across two ledgers.
        a, b = _seed(3), _seed(3)
        self.assertEqual([r.hash for r in a.rows], [r.hash for r in b.rows])


class TamperIsCaught(unittest.TestCase):
    """Each test alters committed history and asserts verify() catches it at the
    right row and for the right reason."""

    def test_body_edit_is_caught(self):
        ledger = _seed(5)
        edited = dict(ledger.rows[2].body)
        edited["verdict"] = "deny"
        ledger._tamper_body(2, edited)  # hash left stale
        result = ledger.verify()
        self.assertFalse(result.ok)
        self.assertEqual(result.broken_index, 2)
        self.assertIn("altered", result.reason)

    def test_deletion_is_caught(self):
        ledger = _seed(5)
        ledger._tamper_delete(2)  # excise a row; the splice breaks the link
        result = ledger.verify()
        self.assertFalse(result.ok)
        # Row formerly at 3 now sits at index 2 with a prev_hash that no longer links.
        self.assertEqual(result.broken_index, 2)
        self.assertIn("reordered or truncated", result.reason)

    def test_reorder_is_caught(self):
        ledger = _seed(5)
        ledger._tamper_swap(1, 3)
        result = ledger.verify()
        self.assertFalse(result.ok)
        self.assertIn("reordered or truncated", result.reason)

    def test_head_truncation_is_caught(self):
        # Drop row 0: row 1 becomes the head but still carries a non-genesis prev_hash.
        ledger = _seed(5)
        ledger._tamper_delete(0)
        result = ledger.verify()
        self.assertFalse(result.ok)
        self.assertEqual(result.broken_index, 0)

    def test_forged_hash_without_matching_body_is_caught(self):
        # Attacker edits the body AND recomputes THIS row's hash, but cannot fix the
        # downstream rows whose prev_hash still points at the original digest.
        ledger = _seed(5)
        forged_body = dict(ledger.rows[1].body)
        forged_body["verdict"] = "deny"
        ledger.rows[1].body = forged_body
        ledger.rows[1].hash = compute_hash(
            ledger.rows[1].prev_hash, ledger.rows[1].index, forged_body
        )
        result = ledger.verify()
        self.assertFalse(result.ok)
        # Row 1 now recomputes cleanly, but row 2's prev_hash no longer matches row 1.
        self.assertEqual(result.broken_index, 2)
        self.assertIn("reordered or truncated", result.reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)

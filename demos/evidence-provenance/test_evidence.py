"""
test_evidence.py: proof that claims are evidence-backed, tracing to a hashed source.

Run it:

    python demos/evidence-provenance/test_evidence.py
    # or:  python -m unittest discover -s demos/evidence-provenance

Standard-library `unittest` only, no pytest, no install.

The important tests here are the NEGATIVE ones: an unsourced claim must be refused,
and an edited source must detach every claim pinned to it. An evidence-backed claim
you can't see fail to verify under a source edit is worthless, so these tests exist
to see it fail.
"""

from __future__ import annotations

import os
import sys
import unittest

# Make `evidence` importable no matter which directory the tests are launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evidence import EvidenceStore, UnsourcedClaimError, content_hash  # noqa: E402


def _seeded_store() -> EvidenceStore:
    store = EvidenceStore()
    store.add_source("src_a", "Refunds under $50 are auto-approved.")
    store.add_source("src_b", "Account deletion requires manager review.")
    return store


class HappyPath(unittest.TestCase):
    def test_add_source_returns_content_hash(self):
        store = EvidenceStore()
        h = store.add_source("src_a", "some text")
        self.assertEqual(h, content_hash("some text"))

    def test_claim_pins_source_hash(self):
        store = _seeded_store()
        claim = store.assert_claim("A $40 refund may be auto-approved.", "src_a")
        self.assertEqual(claim.pinned_hash, store.sources["src_a"].current_hash)

    def test_claim_defaults_to_untrusted_trust_class(self):
        store = _seeded_store()
        claim = store.assert_claim("A $40 refund may be auto-approved.", "src_a")
        self.assertEqual(claim.trust_class, "untrusted")

    def test_intact_claim_verifies(self):
        store = _seeded_store()
        claim = store.assert_claim("Deleting an account needs sign-off.", "src_b")
        result = store.verify(claim)
        self.assertTrue(result.ok)
        self.assertIn("matches", result.reason)

    def test_hashes_are_deterministic(self):
        # Same source text -> identical content_hash, independent of the store.
        a = EvidenceStore()
        b = EvidenceStore()
        h1 = a.add_source("src_a", "identical text")
        h2 = b.add_source("src_a", "identical text")
        self.assertEqual(h1, h2)


class RefusalAndDetachment(unittest.TestCase):
    """Each test proves the fail-closed guarantee: no evidence, no claim; and once
    asserted, a claim's grounding is checked against the CURRENT source, not just
    trusted forever."""

    def test_unsourced_claim_is_refused(self):
        store = _seeded_store()
        with self.assertRaises(UnsourcedClaimError) as ctx:
            store.assert_claim("Refunds over $10,000 are auto-approved.", "src_ghost")
        self.assertIn("no evidence without a resolvable source", str(ctx.exception))

    def test_refused_claim_is_not_stored(self):
        store = _seeded_store()
        try:
            store.assert_claim("Refunds over $10,000 are auto-approved.", "src_ghost")
        except UnsourcedClaimError:
            pass
        self.assertEqual(len(store.claims), 0)

    def test_source_edit_detaches_its_claim(self):
        store = _seeded_store()
        claim = store.assert_claim("A $40 refund may be auto-approved.", "src_a")
        store._tamper_source("src_a", "Refunds under $50 require manager review.")
        result = store.verify(claim)
        self.assertFalse(result.ok)
        self.assertIn("source was edited after assert-time", result.reason)

    def test_shared_source_edit_detaches_both_claims(self):
        store = _seeded_store()
        claim_1 = store.assert_claim("A $40 refund may be auto-approved.", "src_a")
        claim_2 = store.assert_claim("A $45 refund may be auto-approved.", "src_a")
        store._tamper_source("src_a", "Refunds under $50 require manager review.")
        result_1 = store.verify(claim_1)
        result_2 = store.verify(claim_2)
        self.assertFalse(result_1.ok)
        self.assertFalse(result_2.ok)
        self.assertIn("source was edited after assert-time", result_1.reason)
        self.assertIn("source was edited after assert-time", result_2.reason)

    def test_untouched_source_claim_still_verifies(self):
        store = _seeded_store()
        claim_a = store.assert_claim("A $40 refund may be auto-approved.", "src_a")
        claim_b = store.assert_claim("Deleting an account needs sign-off.", "src_b")
        store._tamper_source("src_a", "Refunds under $50 require manager review.")
        result_a = store.verify(claim_a)
        result_b = store.verify(claim_b)
        self.assertFalse(result_a.ok)
        self.assertTrue(result_b.ok)
        self.assertIn("matches", result_b.reason)

    def test_claim_against_deregistered_source_is_detached(self):
        store = _seeded_store()
        claim = store.assert_claim("Deleting an account needs sign-off.", "src_b")
        del store.sources["src_b"]
        result = store.verify(claim)
        self.assertFalse(result.ok)
        self.assertIn("no longer registered", result.reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)

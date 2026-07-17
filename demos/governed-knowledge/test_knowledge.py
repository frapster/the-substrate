"""
test_knowledge.py: proof that governed retrieval wins on currency, using a fair,
unmodified similarity function.

Run it:

    python demos/governed-knowledge/test_knowledge.py
    # or:  python -m unittest discover -s demos/governed-knowledge

Standard-library `unittest` only, no pytest, no install.

The FAIRNESS test is the load-bearing one: it asserts that the superseded atom
genuinely scores higher on cosine similarity than the current atom, for a real,
unmodified cosine computation. If that assertion ever failed, this whole demo would
be a strawman: naive_retrieve would be losing only because someone nerfed its
scoring function, a bug that would have nothing to do with similarity and currency
being different things.
"""

from __future__ import annotations

import os
import sys
import unittest

# Make `knowledge` importable no matter which directory the tests are launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from knowledge import (  # noqa: E402
    AUTHORIZED_SCOPES,
    QUERY_REFUND_WINDOW,
    QUERY_WARRANTY_PERIOD,
    SUPERSESSION_QUERIES,
    KnowledgeBase,
    cosine,
    seed_knowledge_base,
)


class Fairness(unittest.TestCase):
    """The retriever fight has to be fair, or it proves nothing. For every
    supersession pair, the stale atom must genuinely outscore the current atom on
    cosine similarity, because deprecated phrasing is often textually closer to
    how a stale query was worded."""

    def test_stale_atom_scores_higher_than_current_for_every_pair(self):
        kb = seed_knowledge_base()
        by_id = {a.atom_id: a for a in kb.atoms}
        for stale_id, current_id, query, _scope in SUPERSESSION_QUERIES:
            stale, current = by_id[stale_id], by_id[current_id]
            sim_stale = cosine(query, stale.embedding)
            sim_current = cosine(query, current.embedding)
            self.assertGreater(
                sim_stale,
                sim_current,
                f"{stale_id} must legitimately outscore {current_id} for the "
                "fairness argument to hold",
            )

    def test_cosine_is_a_real_unmodified_computation(self):
        # Identical vectors cosine to 1.0; orthogonal vectors cosine to 0.0. If
        # this ever broke, every other assertion in this file would be meaningless.
        self.assertAlmostEqual(cosine((1.0, 0.0), (1.0, 0.0)), 1.0)
        self.assertAlmostEqual(cosine((1.0, 0.0), (0.0, 1.0)), 0.0)
        self.assertEqual(cosine((0.0, 0.0), (1.0, 0.0)), 0.0)  # no divide-by-zero


class NaiveRetrievalLosesOnCurrency(unittest.TestCase):
    def test_naive_returns_the_stale_atom(self):
        kb = seed_knowledge_base()
        result = kb.naive_retrieve(QUERY_REFUND_WINDOW)
        self.assertEqual(result.atom.atom_id, "atom_refund_v1")
        self.assertFalse(result.atom.is_current)
        self.assertFalse(result.degraded)

    def test_naive_score_matches_the_fairness_claim(self):
        kb = seed_knowledge_base()
        by_id = {a.atom_id: a for a in kb.atoms}
        result = kb.naive_retrieve(QUERY_REFUND_WINDOW)
        expected = cosine(QUERY_REFUND_WINDOW, by_id["atom_refund_v1"].embedding)
        self.assertAlmostEqual(result.score, expected)

    def test_naive_ignores_scope_entirely(self):
        # naive_retrieve has no scope parameter, so it searches the whole KB,
        # tenant-scoped atoms included. That's exactly the leakage governed
        # retrieval exists to prevent.
        kb = seed_knowledge_base()
        result = kb.naive_retrieve(QUERY_REFUND_WINDOW)
        self.assertIn(result.atom.scope, {"platform", "tenant_acme"})


class GovernedRetrievalWinsOnCurrency(unittest.TestCase):
    def test_governed_returns_the_current_atom(self):
        kb = seed_knowledge_base()
        result = kb.governed_retrieve(QUERY_REFUND_WINDOW, scope="platform")
        self.assertFalse(result.degraded)
        self.assertEqual(result.atom.atom_id, "atom_refund_v2")
        self.assertTrue(result.atom.is_current)

    def test_governed_correct_for_every_supersession_pair(self):
        kb = seed_knowledge_base()
        for stale_id, current_id, query, scope in SUPERSESSION_QUERIES:
            result = kb.governed_retrieve(query, scope=scope)
            self.assertFalse(result.degraded, f"unexpected abstain for {current_id}")
            self.assertEqual(result.atom.atom_id, current_id)
            self.assertNotEqual(result.atom.atom_id, stale_id)

    def test_governed_never_returns_a_superseded_atom(self):
        kb = seed_knowledge_base()
        for _stale_id, _current_id, query, scope in SUPERSESSION_QUERIES:
            result = kb.governed_retrieve(query, scope=scope)
            if result.atom is not None:
                self.assertTrue(result.atom.is_current)


class GovernedRetrievalAbstains(unittest.TestCase):
    def test_abstains_when_no_current_atom_clears_threshold(self):
        kb = seed_knowledge_base()
        result = kb.governed_retrieve(QUERY_WARRANTY_PERIOD, scope="platform")
        self.assertTrue(result.degraded)
        self.assertIsNone(result.atom)
        self.assertIn("threshold", result.reason)

    def test_abstains_when_scope_is_not_registered(self):
        kb = seed_knowledge_base()
        self.assertNotIn("tenant_zzz", AUTHORIZED_SCOPES)
        result = kb.governed_retrieve(QUERY_REFUND_WINDOW, scope="tenant_zzz")
        self.assertTrue(result.degraded)
        self.assertIsNone(result.atom)
        self.assertIn("not a registered", result.reason)

    def test_scope_check_precedes_similarity_ranking(self):
        # Even a query that would score very high against SOME atom must still be
        # refused if the requesting scope itself isn't authorized.
        kb = seed_knowledge_base()
        result = kb.governed_retrieve((0.2, 0.15, 0.1, 0.2, 0.15, 0.1) + (0.0,) * 10, scope="tenant_unknown")
        self.assertTrue(result.degraded)
        self.assertIn("scope", result.reason)

    def test_abstains_on_empty_knowledge_base(self):
        kb = KnowledgeBase()
        result = kb.governed_retrieve(QUERY_REFUND_WINDOW, scope="platform")
        self.assertTrue(result.degraded)
        self.assertIn("no current atom", result.reason)

    def test_naive_degrades_on_empty_knowledge_base(self):
        kb = KnowledgeBase()
        result = kb.naive_retrieve(QUERY_REFUND_WINDOW)
        self.assertTrue(result.degraded)
        self.assertIn("empty", result.reason)


class ScopeFiltering(unittest.TestCase):
    def test_tenant_scope_returns_tenant_atom(self):
        kb = seed_knowledge_base()
        tenant_query = (0.2, 0.15, 0.1, 0.2, 0.15, 0.1) + (0.0,) * 10
        result = kb.governed_retrieve(tenant_query, scope="tenant_acme")
        self.assertFalse(result.degraded)
        self.assertEqual(result.atom.atom_id, "atom_tenant_acme_refund_v1")

    def test_platform_scope_does_not_leak_tenant_atom(self):
        kb = seed_knowledge_base()
        tenant_query = (0.2, 0.15, 0.1, 0.2, 0.15, 0.1) + (0.0,) * 10
        result = kb.governed_retrieve(tenant_query, scope="platform")
        if result.atom is not None:
            self.assertNotEqual(result.atom.scope, "tenant_acme")


class Supersession(unittest.TestCase):
    def test_supersede_closes_old_atom_and_adds_new_one(self):
        kb = seed_knowledge_base()
        from knowledge import Atom

        new_atom = Atom(
            atom_id="atom_shipping_v2",
            atom_type="policy_fact",
            body="Standard shipping now takes 2-3 business days from purchase.",
            embedding=(0.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.95, 0.0) + (0.0,) * 8,
            scope="platform",
            provenance="policy-doc://shipping/v2#section-1",
            validity_start="2026-06-01",
        )
        kb.supersede("atom_shipping_v1", new_atom, at="2026-05-31")
        old = next(a for a in kb.atoms if a.atom_id == "atom_shipping_v1")
        self.assertEqual(old.validity_end, "2026-05-31")
        self.assertFalse(old.is_current)
        new = next(a for a in kb.atoms if a.atom_id == "atom_shipping_v2")
        self.assertTrue(new.is_current)


if __name__ == "__main__":
    unittest.main(verbosity=2)

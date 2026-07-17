"""
test_pipeline.py, proof that the governed loop commits only fully-governed intents,
and refuses a broken one at the stage that owns the broken check.

Run it:

    python demos/governed-decision/test_pipeline.py
    # or:  python -m unittest discover -s demos/governed-decision

Standard-library `unittest` only.

The NEGATIVE tests are the point: each asserts that an intent broken in exactly one way
is refused at exactly the right stage, and that nothing partial leaks into the ledger or
the versioned store when a refusal happens.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import (  # noqa: E402
    ActionPolicy,
    AuditLedger,
    BoundedGate,
    DeterministicValidator,
    EvidenceStore,
    Intent,
    ReversibleStore,
    Substrate,
)


def _substrate() -> Substrate:
    gate = BoundedGate(
        {
            "grant_refund": ActionPolicy(tier="yellow", soft_cap=100, hard_cap=500, dimension="usd"),
            "delete_rows": ActionPolicy(tier="red", soft_cap=50, hard_cap=100, dimension="rows"),
        }
    )
    evidence = EvidenceStore()
    evidence.add_source("policy-refunds-v3", "Refunds up to $500 are pre-authorized.")
    validator = DeterministicValidator(required_fields=("action", "amount_usd"), max_usd=500)
    return Substrate(gate, evidence, validator, AuditLedger(), ReversibleStore())


def _good() -> Intent:
    return Intent(
        action="grant_refund",
        scope={"usd": 40},
        claim="eligible $40 refund",
        source_id="policy-refunds-v3",
        proposed_value={"action": "grant_refund", "amount_usd": 40, "user": "u_8831"},
    )


class HappyPath(unittest.TestCase):
    def test_well_formed_intent_commits_through_all_stages(self):
        s = _substrate()
        d = s.decide(_good())
        self.assertTrue(d.committed)
        self.assertEqual(d.outcome, "proceed")
        self.assertIsNotNone(d.ledger_hash)
        self.assertEqual(d.version, 1)

    def test_commit_is_audited_and_reversible(self):
        s = _substrate()
        pre = s.store.state_hash_at(0)
        s.decide(_good())
        self.assertTrue(s.ledger.verify())          # audited
        restored = s.store.restore(0)               # reversible
        self.assertEqual(s.store.state_hash_at(restored), pre)  # exact prior state

    def test_soft_cap_escalates_rather_than_commits_autonomously(self):
        s = _substrate()
        intent = _good()
        intent.scope = {"usd": 250}  # over soft_cap 100, under hard_cap 500
        intent.proposed_value = {"action": "grant_refund", "amount_usd": 250}
        d = s.decide(intent)
        self.assertTrue(d.committed)
        self.assertEqual(d.outcome, "escalated")


class EachStageRefusesItsOwnFailure(unittest.TestCase):
    def test_over_scope_refused_at_bounded(self):
        s = _substrate()
        intent = _good()
        intent.action = "delete_rows"
        intent.scope = {"rows": 10_000}
        d = s.decide(intent)
        self.assertFalse(d.committed)
        self.assertEqual(d.refusal_stage, "bounded")
        self.assertIn("hard cap", d.refusal_reason)

    def test_unregistered_action_refused_at_bounded(self):
        s = _substrate()
        intent = _good()
        intent.action = "wire_transfer"
        d = s.decide(intent)
        self.assertFalse(d.committed)
        self.assertEqual(d.refusal_stage, "bounded")
        self.assertIn("roster", d.refusal_reason)

    def test_unsourced_claim_refused_at_evidence(self):
        s = _substrate()
        intent = _good()
        intent.source_id = None
        d = s.decide(intent)
        self.assertFalse(d.committed)
        self.assertEqual(d.refusal_stage, "evidence")
        self.assertIn("provenance", d.refusal_reason)

    def test_invalid_proposal_refused_at_validated(self):
        s = _substrate()
        intent = _good()
        intent.proposed_value = {"action": "grant_refund"}  # missing amount_usd
        d = s.decide(intent)
        self.assertFalse(d.committed)
        self.assertEqual(d.refusal_stage, "validated")
        self.assertIn("discarded, not patched", d.refusal_reason)

    def test_a_refusal_leaves_no_trace_in_the_ledger_or_store(self):
        s = _substrate()
        intent = _good()
        intent.source_id = None  # will be refused at evidence
        d = s.decide(intent)
        self.assertFalse(d.committed)
        self.assertEqual(len(s.ledger.rows), 0)     # nothing audited
        self.assertEqual(len(s.store.versions), 1)  # no new version, only genesis {}


if __name__ == "__main__":
    unittest.main(verbosity=2)

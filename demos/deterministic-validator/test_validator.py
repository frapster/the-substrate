"""
test_validator.py — proof that a rejected proposal is discarded, not patched.

Run it:

    python demos/deterministic-validator/test_validator.py
    # or:  python -m unittest discover -s demos/deterministic-validator

Standard-library `unittest` only — no pytest, no install.

The important tests here are the NEGATIVE ones: they assert that validate() *fails*, and
fails for the RIGHT reason, for a hallucinated citation, an out-of-bound amount, and a
missing field — and that a failing proposal never reaches commit_log, is never mutated
into a passing one, and cannot be forced into commit_log by an approving llm_judge alone.
A "the model is never trusted — it is checked" claim you can't see fail is worthless — so
these tests exist to see it fail.
"""

from __future__ import annotations

import os
import sys
import unittest

# Make `validator` importable no matter which directory the tests are launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validator import (  # noqa: E402
    MAX_AMOUNT_USD,
    Judgment,
    Validator,
    llm_judge,
    propose,
)


class HappyPath(unittest.TestCase):
    def test_valid_proposal_commits(self):
        validator = Validator()
        good = propose(intent="grant_refund", source_id="src_101", amount_usd=40)
        result = validator.submit(good)
        self.assertTrue(result.ok)
        self.assertIn(good, validator.commit_log)
        self.assertEqual(len(validator.rejected_log), 0)

    def test_committed_record_equals_proposal_verbatim(self):
        # No auto-repair: the row in commit_log must be identical to what was proposed.
        validator = Validator()
        good = propose(intent="grant_refund", source_id="src_102", amount_usd=200)
        validator.submit(good)
        committed = validator.commit_log[0]
        self.assertEqual(committed, good)
        self.assertIs(committed, good)  # same object — nothing copied-and-edited it

    def test_boundary_amount_is_allowed(self):
        validator = Validator()
        edge = propose(intent="grant_refund", source_id="src_101", amount_usd=MAX_AMOUNT_USD)
        result = validator.submit(edge)
        self.assertTrue(result.ok)

    def test_zero_amount_is_allowed(self):
        # Some intents (e.g. escalate_ticket) carry no dollar amount.
        validator = Validator()
        free = propose(intent="escalate_ticket", source_id="src_103", amount_usd=0)
        result = validator.submit(free)
        self.assertTrue(result.ok)


class RejectionIsClean(unittest.TestCase):
    """Each test submits a bad proposal and asserts it is discarded — absent from
    commit_log, present in rejected_log with the right reason, and never mutated."""

    def test_hallucinated_source_is_discarded(self):
        validator = Validator()
        bad = propose(intent="grant_refund", source_id="src_999", amount_usd=40)
        result = validator.submit(bad)
        self.assertFalse(result.ok)
        self.assertIn("does not exist", result.reason)
        self.assertNotIn(bad, validator.commit_log)
        self.assertEqual(validator.rejected_log[0].proposal, bad)
        self.assertIn("does not exist", validator.rejected_log[0].reason)

    def test_over_bound_amount_is_discarded(self):
        validator = Validator()
        bad = propose(intent="grant_refund", source_id="src_101", amount_usd=MAX_AMOUNT_USD + 1)
        result = validator.submit(bad)
        self.assertFalse(result.ok)
        self.assertIn("exceeds policy bound", result.reason)
        self.assertEqual(len(validator.commit_log), 0)

    def test_negative_amount_is_discarded(self):
        validator = Validator()
        bad = propose(intent="grant_refund", source_id="src_101", amount_usd=-10)
        result = validator.submit(bad)
        self.assertFalse(result.ok)
        self.assertIn("must not be negative", result.reason)

    def test_missing_intent_is_discarded(self):
        validator = Validator()
        bad = propose(intent="", source_id="src_101", amount_usd=40)
        result = validator.submit(bad)
        self.assertFalse(result.ok)
        self.assertIn("missing required field", result.reason)

    def test_discarded_proposal_is_not_mutated_into_a_passing_one(self):
        # The whole point of "discarded, not patched": the stored (rejected) record
        # still carries the bad source id — nothing quietly repaired it.
        validator = Validator()
        bad = propose(intent="grant_refund", source_id="src_999", amount_usd=40)
        validator.submit(bad)
        stored = validator.rejected_log[0].proposal
        self.assertEqual(stored.source_id, "src_999")
        self.assertNotIn(stored, validator.commit_log)

    def test_llm_judge_approval_alone_cannot_commit(self):
        # The judge only looks at the amount, so it approves this proposal even though
        # it cites a source that does not exist. Approval must not matter: validate() is
        # the only gate, so the proposal is still discarded.
        validator = Validator()
        bad = propose(intent="grant_refund", source_id="src_999", amount_usd=40)
        judgment = llm_judge(bad)
        self.assertTrue(judgment.approved)  # the judge is fooled
        result = validator.submit(bad, judgment)
        self.assertFalse(result.ok)  # but the deterministic gate is not
        self.assertNotIn(bad, validator.commit_log)
        self.assertIn(bad, [e.proposal for e in validator.rejected_log])

    def test_no_commit_method_reads_judgment_approval(self):
        # There is no code path from a Judgment straight into commit_log — submit()
        # only ever consults validate(). Simulate the tempting shortcut and confirm
        # it changes nothing: passing an approving Judgment for a bad proposal is
        # indistinguishable in outcome from passing no judgment at all.
        validator_a = Validator()
        validator_b = Validator()
        bad = propose(intent="grant_refund", source_id="src_999", amount_usd=40)
        approving = Judgment(approved=True, note="looks fine to me")
        result_a = validator_a.submit(bad)
        result_b = validator_b.submit(bad, approving)
        self.assertEqual(result_a.ok, result_b.ok)
        self.assertFalse(result_b.ok)
        self.assertEqual(len(validator_b.commit_log), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

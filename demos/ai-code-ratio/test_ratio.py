"""
test_ratio.py, proof that the AI:code ratio claim holds up under test.

Run it:

    python demos/ai-code-ratio/test_ratio.py
    # or:  python -m unittest discover -s demos/ai-code-ratio

Standard-library `unittest` only, no pytest, no install.

The interesting assertions here are the ones that would be false if the demo were
rigged: the branch-delta count comes from parsing with `ast`, an actual count rather
than a hardcoded number; the evaluator-LOC-delta-is-zero claim is checked by
construction (governed_version.py's evaluate() is literally the same function object
whether the fact table has 9 rows or 12); and the revert-the-fact litmus is checked
both directions.
"""

from __future__ import annotations

import os
import sys
import unittest

# Make the sibling modules importable no matter which directory the tests are
# launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import code_version  # noqa: E402
import code_version_v2  # noqa: E402
import facts  # noqa: E402
import governed_version  # noqa: E402

BASE_TICKETS = [
    {"plan_tier": tier, "severity": severity}
    for tier in ("free", "pro", "enterprise")
    for severity in ("low", "medium", "high")
]

NEW_TICKETS = [
    {"plan_tier": "free", "severity": "critical"},
    {"plan_tier": "pro", "severity": "critical"},
    {"plan_tier": "enterprise", "severity": "critical"},
]


class BaseEquivalence(unittest.TestCase):
    """Both implementations were built for the same base requirement; they must
    agree on every case of it before any growth claim means anything."""

    def test_all_base_tickets_agree(self):
        for ticket in BASE_TICKETS:
            with self.subTest(ticket=ticket):
                self.assertEqual(
                    code_version.route_ticket(ticket),
                    governed_version.evaluate(ticket),
                )

    def test_base_facts_cover_every_base_ticket(self):
        # Sanity check on facts.py itself: 9 tickets, 9 facts, one-to-one.
        self.assertEqual(len(facts.BASE_FACTS), len(BASE_TICKETS))


class GovernedAbstains(unittest.TestCase):
    """The fail-closed contract: no governing fact → hitl_required, never a guess."""

    def test_abstains_on_ungoverned_input(self):
        for ticket in NEW_TICKETS:
            with self.subTest(ticket=ticket):
                result = governed_version.evaluate(ticket, facts=facts.BASE_FACTS)
                self.assertEqual(result.get("status"), "hitl_required")

    def test_code_path_does_not_abstain_it_silently_guesses(self):
        # The contrast case: code_version.py (unmodified) has no branch for
        # critical severity, so it falls through to the generic else, silently,
        # with no signal that it was guessing.
        for ticket in NEW_TICKETS:
            with self.subTest(ticket=ticket):
                result = code_version.route_ticket(ticket)
                self.assertNotEqual(result.get("status"), "hitl_required")
                self.assertEqual(result, {"queue": "standard", "escalation": None})


class GrowthCost(unittest.TestCase):
    """The countable claim: growing the requirement costs the code path branches
    and the governed path facts, never the reverse."""

    def test_code_path_needs_new_branches(self):
        delta = code_version_v2.count_branches() - code_version.count_branches()
        self.assertGreater(delta, 0)
        self.assertEqual(delta, len(NEW_TICKETS))  # one new branch per new case, here

    def test_code_path_needs_new_loc(self):
        delta = code_version_v2.count_decision_loc() - code_version.count_decision_loc()
        self.assertGreater(delta, 0)

    def test_governed_evaluator_is_unchanged_by_growth(self):
        # governed_version.evaluate is the SAME function object regardless of how
        # many rows the fact table it's called with holds. There is no version of
        # this function that "has" 9 facts or 12 facts baked in. Zero LOC delta by
        # construction, not by omission.
        grown_facts = facts.BASE_FACTS + facts.NEW_FACTS
        for ticket in BASE_TICKETS:
            with self.subTest(ticket=ticket):
                self.assertEqual(
                    governed_version.evaluate(ticket, facts=facts.BASE_FACTS),
                    governed_version.evaluate(ticket, facts=grown_facts),
                )

    def test_growth_facts_match_growth_branches(self):
        # The grown governed table reproduces exactly what the grown code version
        # computes for the new cases: same behavior, reached by a data row instead
        # of a shipped branch.
        grown_facts = facts.BASE_FACTS + facts.NEW_FACTS
        for ticket in NEW_TICKETS:
            with self.subTest(ticket=ticket):
                self.assertEqual(
                    governed_version.evaluate(ticket, facts=grown_facts),
                    code_version_v2.route_ticket(ticket),
                )


class RevertTheFactLitmus(unittest.TestCase):
    """Revert one fact row and behavior reverts with it; the evaluator's source
    never changes between the two calls."""

    def test_reverting_a_fact_reverts_the_decision(self):
        probe = {"plan_tier": "pro", "severity": "critical"}
        grown_facts = facts.BASE_FACTS + facts.NEW_FACTS

        with_fact = governed_version.evaluate(probe, facts=grown_facts)
        self.assertNotEqual(with_fact.get("status"), "hitl_required")

        reverted = governed_version.evaluate(probe, facts=facts.BASE_FACTS)
        self.assertEqual(reverted.get("status"), "hitl_required")

    def test_adding_a_fact_row_changes_behavior(self):
        # The converse of the litmus: a fact row present changes the outcome from
        # abstain to a concrete routing decision. Data alone drives the change.
        probe = {"plan_tier": "enterprise", "severity": "critical"}
        before = governed_version.evaluate(probe, facts=facts.BASE_FACTS)
        after = governed_version.evaluate(probe, facts=facts.BASE_FACTS + facts.NEW_FACTS)
        self.assertNotEqual(before, after)
        self.assertEqual(before.get("status"), "hitl_required")
        self.assertEqual(after, {"queue": "white_glove", "escalation": "tier4_incident"})


if __name__ == "__main__":
    unittest.main(verbosity=2)

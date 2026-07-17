"""
ratio_demo.py, watch the AI:code ratio become a countable number.

Run it:

    python demos/ai-code-ratio/ratio_demo.py

No installation, no dependencies. Python 3 standard library only.

The story in four acts:
  1. Two implementations of the same ticket-routing feature (one a hand-authored
     if/elif tree in code_version.py, one a generic evaluator reading a fact table
     in governed_version.py) agree on every case of the base requirement.
  2. Three new business cases arrive. The code path needs new BRANCHES (counted for
     real, via ast, not estimated); the governed path needs new FACT ROWS and zero
     evaluator code change. The delta is printed as an actual number.
  3. The litmus: revert one fact row and governed behavior reverts with it. The
     evaluator file is byte-for-byte the same before and after.
  4. On a ticket no fact governs, the governed path abstains (hitl_required),
     fail-closed. The unmodified code path silently mis-defaults instead: it has
     no way to know it's guessing.

This is the runnable proof behind the "90% AI, 10% mechanical" / AI:code ratio claim
in README.md and THESIS.md: for THIS one small feature, where does new requirement
meaning cost you a rebuild (code) versus a data row (facts)?
"""

from __future__ import annotations

import sys

import code_version
import code_version_v2
import facts
import governed_version

_TTY = sys.stdout.isatty()
GREEN = "\033[32m" if _TTY else ""
RED = "\033[31m" if _TTY else ""
YELLOW = "\033[33m" if _TTY else ""
DIM = "\033[2m" if _TTY else ""
BOLD = "\033[1m" if _TTY else ""
RESET = "\033[0m" if _TTY else ""
CHECK = "✓"
CROSS = "✗"


def rule(char: str = "─", width: int = 64) -> str:
    return DIM + char * width + RESET


# The base requirement: 3 plan tiers × 3 severities, 9 tickets. Both implementations
# were written to satisfy exactly this; the equivalence check in Act 1 proves it.
BASE_TICKETS = [
    {"plan_tier": tier, "severity": severity}
    for tier in ("free", "pro", "enterprise")
    for severity in ("low", "medium", "high")
]

# Three new business cases that arrive after the base feature shipped: critical
# severity, for each plan tier. Neither implementation's base version handles these.
NEW_TICKETS = [
    {"plan_tier": "free", "severity": "critical"},
    {"plan_tier": "pro", "severity": "critical"},
    {"plan_tier": "enterprise", "severity": "critical"},
]


def main() -> int:
    print()
    print(BOLD + "the-substrate · AI:code ratio, made countable" + RESET)
    print(rule("═"))
    print(
        "One feature (support-ticket routing), built twice: a hand-authored\n"
        "if/elif tree, and a generic evaluator reading a fact table. Watch what\n"
        "three new business cases cost each one.\n"
    )

    # --- Act 1: equivalence on the base requirement ------------------------------
    print(BOLD + "1. Base requirement, do the two versions agree?" + RESET)
    for ticket in BASE_TICKETS:
        code_out = code_version.route_ticket(ticket)
        governed_out = governed_version.evaluate(ticket)
        if code_out != governed_out:
            print(
                f"  {RED}{CROSS} DISAGREEMENT on {ticket}: "
                f"code={code_out} governed={governed_out}{RESET}"
            )
            return 1
    print(
        f"  {GREEN}{CHECK} {len(BASE_TICKETS)}/{len(BASE_TICKETS)} base tickets: "
        f"code_version and governed_version agree{RESET}"
    )
    print()

    # --- Act 2: grow the requirement, count the real cost -------------------------
    print(BOLD + "2. Three new cases arrive (critical severity)" + RESET)

    v1_branches = code_version.count_branches()
    v2_branches = code_version_v2.count_branches()
    v1_loc = code_version.count_decision_loc()
    v2_loc = code_version_v2.count_decision_loc()
    branch_delta = v2_branches - v1_branches
    loc_delta = v2_loc - v1_loc

    print(
        f"  {DIM}code_version.py    (ast-counted): {v1_branches} branches, {v1_loc} decision LOC{RESET}"
    )
    print(
        f"  {DIM}code_version_v2.py (ast-counted): {v2_branches} branches, {v2_loc} decision LOC{RESET}"
    )
    print(
        f"  {YELLOW}code path: +{branch_delta} branches / +{loc_delta} LOC{RESET} "
        f"{DIM}(a developer wrote, reviewed, and shipped this){RESET}"
    )
    print()

    fact_delta = len(facts.NEW_FACTS)
    grown_facts = facts.BASE_FACTS + facts.NEW_FACTS
    for ticket in NEW_TICKETS:
        governed_out = governed_version.evaluate(ticket, facts=grown_facts)
        expected = code_version_v2.route_ticket(ticket)
        if governed_out != expected:
            print(f"  {RED}{CROSS} governed (grown facts) disagrees with code_version_v2 on {ticket}{RESET}")
            return 1
    print(
        f"  {GREEN}{CHECK} governed path: +0 evaluator LOC / +{fact_delta} fact rows{RESET} "
        f"{DIM}(governed_version.py is the same file, untouched){RESET}"
    )
    print()
    print(
        f"  {BOLD}Headline: {fact_delta} new cases → code +{branch_delta} branches / "
        f"+{loc_delta} LOC; governed +0 LOC / +{fact_delta} facts.{RESET}"
    )
    print(
        f"  {DIM}For this feature's growth: 100% of the governed path's new meaning "
        f"landed in data\n  (facts); 100% of the code path's new meaning landed in "
        f"hand-authored control flow (branches).{RESET}"
    )
    print()

    # --- Act 3: the revert-the-fact litmus ----------------------------------------
    print(BOLD + "3. The revert-the-fact litmus" + RESET)
    probe = {"plan_tier": "pro", "severity": "critical"}
    with_fact = governed_version.evaluate(probe, facts=grown_facts)
    print(f"  {DIM}facts = BASE_FACTS + NEW_FACTS{RESET}  evaluate({probe}) → {with_fact}")
    reverted = governed_version.evaluate(probe, facts=facts.BASE_FACTS)
    print(f"  {DIM}facts = BASE_FACTS  (NEW fact reverted){RESET}  evaluate({probe}) → {reverted}")
    if with_fact.get("status") == "hitl_required" or reverted.get("status") != "hitl_required":
        print(f"  {RED}{CROSS} litmus failed, behavior did not track the fact table{RESET}")
        return 1
    print(
        f"  {GREEN}{CHECK} reverting one fact row reverted the decision{RESET}, "
        f"governed_version.py's source is\n    identical in both calls above; only the "
        f"data argument changed."
    )
    print()

    # --- Act 4: fail-closed vs. silent mis-default --------------------------------
    print(BOLD + "4. An ungoverned ticket: abstain, or silently guess?" + RESET)
    ungoverned = {"plan_tier": "pro", "severity": "critical"}
    governed_abstain = governed_version.evaluate(ungoverned, facts=facts.BASE_FACTS)
    code_guess = code_version.route_ticket(ungoverned)  # unmodified v1, no branch for this case
    print(f"  {DIM}governed (BASE_FACTS only), no governing fact:{RESET}")
    print(f"    {GREEN}{CHECK} abstains → {governed_abstain}{RESET}")
    print(f"  {DIM}code (unmodified code_version.py), same ticket:{RESET}")
    print(f"    {RED}{CROSS} silently returns → {code_guess}{RESET}  {DIM}(no signal this was a guess){RESET}")
    if governed_abstain.get("status") != "hitl_required":
        print(f"  {RED}{CROSS} governed path failed to abstain, not fail-closed!{RESET}")
        return 1
    print()

    print(rule())
    print(
        f"{GREEN}{CHECK} Where new requirement meaning lives is countable.{RESET} "
        "Growth cost the governed\n  path facts (data); it cost the code path branches "
        f"(code). {DIM}(See demos/ai-code-ratio/README.md\n  for what this does and does "
        f"not prove.){RESET}"
    )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

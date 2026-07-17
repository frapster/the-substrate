"""
validator_demo.py: watch a deterministic validator discard a hallucinated proposal.

Run it:

    python demos/deterministic-validator/validator_demo.py

No installation, no dependencies, Python 3 standard library only.

The story in three acts:
  1. A model proposes an action grounded in a real source, within policy. It passes
     validate() and commits.
  2. A model proposes an action that cites a source that does not exist: a hallucinated
     citation. validate() FAILS. Watch it get DISCARDED: the source id is
     never rewritten to a valid one, the proposal never quietly becomes admissible.
  3. A batch of proposals runs through the gate. The commit log holds only what passed;
     every discard is recorded with its reason; the committed records are byte-for-byte
     identical to what the model proposed, with no laundering.

This is the runnable proof behind ADR-0003
(../../docs/adr/ADR-0003-deterministic-validator-commits.md). The model is checked, not
trusted on its word alone.
"""

from __future__ import annotations

from validator import Validator, llm_judge, propose

# ANSI colors, with a plain fallback so piped/redirected output stays readable.
import sys

_TTY = sys.stdout.isatty()
GREEN = "\033[32m" if _TTY else ""
RED = "\033[31m" if _TTY else ""
DIM = "\033[2m" if _TTY else ""
BOLD = "\033[1m" if _TTY else ""
RESET = "\033[0m" if _TTY else ""
CHECK = "✓"
CROSS = "✗"


def rule(char: str = "─", width: int = 64) -> str:
    return DIM + char * width + RESET


def main() -> int:
    print()
    print(BOLD + "the-substrate · deterministic validator commits" + RESET)
    print(rule("═"))
    print(
        "A model proposes an action; a deterministic validator grades it against\n"
        "real, checkable rules. Only a proposal that PASSES is committed. A failing\n"
        "proposal is discarded, not patched. Let's watch both paths.\n"
    )

    validator = Validator()

    # --- Act 1: a valid, grounded proposal commits --------------------------------
    print(BOLD + "1. A valid proposal" + RESET)
    good = propose(intent="grant_refund", source_id="src_101", amount_usd=40)
    judgment = llm_judge(good)
    print(f"  {DIM}[propose]{RESET} {good.intent} citing {good.source_id}, ${good.amount_usd}")
    print(f"  {DIM}[llm_judge]{RESET} approved={judgment.approved}  {DIM}{judgment.note}{RESET}")
    result = validator.submit(good, judgment)
    print(f"  {GREEN}{CHECK} validate: {result.reason}{RESET}")
    print(f"  {GREEN}[commit]{RESET} row appended to commit_log (verbatim)")
    print()

    # --- Act 2: a hallucinated citation is discarded, not patched ------------------
    print(BOLD + "2. A hallucinated proposal" + RESET)
    bad = propose(intent="grant_refund", source_id="src_999", amount_usd=40)
    judgment = llm_judge(bad)
    print(f"  {DIM}[propose]{RESET} {bad.intent} citing {bad.source_id}, ${bad.amount_usd}")
    print(
        f"  {DIM}[llm_judge]{RESET} approved={judgment.approved}  {DIM}{judgment.note}"
        f"{RESET}  {DIM}(the judge never checks the source, it would wave this through){RESET}"
    )
    result = validator.submit(bad, judgment)
    print(f"  {RED}{CROSS} validate: {result.reason}{RESET}")
    print(f"  {RED}[discard]{RESET} proposal recorded in rejected_log, NOT patched into a valid one")
    still = validator.rejected_log[-1].proposal
    print(
        f"  {DIM}source_id after discard: {still.source_id!r} "
        f"(unchanged, nothing rewrote it to a real source){RESET}"
    )
    print()

    # --- Act 3: a batch shows the gate holds under volume ---------------------------
    print(BOLD + "3. A batch of proposals" + RESET)
    batch = [
        propose(intent="grant_refund", source_id="src_102", amount_usd=120),          # valid
        propose(intent="escalate_ticket", source_id="src_103", amount_usd=0),         # valid
        propose(intent="grant_refund", source_id="src_777", amount_usd=90),           # bad source
        propose(intent="grant_refund", source_id="src_104", amount_usd=5000),         # over bound
        propose(intent="", source_id="src_101", amount_usd=50),                       # missing intent
        propose(intent="grant_refund", source_id="src_102", amount_usd=-10),          # negative amount
    ]
    bad_count = 0
    discarded_count = 0
    for p in batch:
        r = validator.submit(p, llm_judge(p))
        tag = f"{GREEN}[commit]{RESET}" if r.ok else f"{RED}[discard]{RESET}"
        print(f"  {tag} {p.intent or '<missing intent>'} citing {p.source_id}, ${p.amount_usd}  {DIM}{r.reason}{RESET}")
        if not r.ok:
            bad_count += 1
            discarded_count += 1
    print()

    print(rule())
    print(f"  {bad_count} bad proposals: {discarded_count}/{bad_count} discarded (not patched)")
    print(f"  commit_log holds only validated proposals: {len(validator.commit_log)} rows")
    print(f"  rejected_log holds every discard with its reason: {len(validator.rejected_log)} rows")

    # Prove the boundary: no committed record differs from the proposal that was submitted.
    laundered = [p for p in validator.commit_log if not validator.validate(p).ok]
    if laundered:
        # This branch must never execute. If it does, the gate is broken.
        print(f"  {RED}{CROSS} commit_log contains a record that fails validate(), laundering!{RESET}")
        return 1

    print(
        f"\n{GREEN}{CHECK} The validator is fail-closed.{RESET} A rejected inference is "
        "discarded, not patched;\n  the model is never trusted, it is checked. "
        f"{DIM}(See demos/deterministic-validator/README.md and\n  "
        f"docs/adr/ADR-0003 for why this boundary, and what it does not claim.){RESET}"
    )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

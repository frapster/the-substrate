"""
governed_decision_demo.py, watch one intent flow through all four guarantees, and
watch each stage refuse its own bad input in isolation.

Run it:

    python demos/governed-decision/governed_decision_demo.py

No installation, no dependencies. Python 3 standard library only.

The story:
  1. A well-formed intent passes the whole loop (bounded → evidence → validated →
     audited → reversible), commits, and is then rolled back to its exact prior state,
     with the audit chain still intact.
  2. Four more intents, each broken in exactly one way, are each refused at the
     matching stage: over-scope (bounded), unsourced claim (evidence), an invalid
     proposal (validated). The refusal names the stage that said no.

This is the flagship: it shows the substrate as a pipeline of deterministic
checkpoints around one probabilistic step.
"""

from __future__ import annotations

import sys

from pipeline import (
    ActionPolicy,
    AuditLedger,
    BoundedGate,
    DeterministicValidator,
    EvidenceStore,
    Intent,
    ReversibleStore,
    Substrate,
)

_TTY = sys.stdout.isatty()
GREEN = "\033[32m" if _TTY else ""
RED = "\033[31m" if _TTY else ""
DIM = "\033[2m" if _TTY else ""
BOLD = "\033[1m" if _TTY else ""
RESET = "\033[0m" if _TTY else ""
CHECK = "✓"
CROSS = "✗"


def rule(char: str = "─", width: int = 68) -> str:
    return DIM + char * width + RESET


def build_substrate() -> Substrate:
    gate = BoundedGate(
        {
            "grant_refund": ActionPolicy(tier="yellow", soft_cap=100, hard_cap=500, dimension="usd"),
            "delete_rows": ActionPolicy(tier="red", soft_cap=50, hard_cap=100, dimension="rows"),
        }
    )
    evidence = EvidenceStore()
    evidence.add_source("policy-refunds-v3", "Refunds up to $500 are pre-authorized for tier-1 accounts.")
    validator = DeterministicValidator(required_fields=("action", "amount_usd"), max_usd=500)
    return Substrate(gate, evidence, validator, AuditLedger(), ReversibleStore())


def main() -> int:
    print()
    print(BOLD + "the-substrate · one governed decision, end to end" + RESET)
    print(rule("═"))
    print(
        "One intent flows through all four guarantees, bounded, evidence-backed,\n"
        "audited, reversible. The model proposes; deterministic checkpoints wrap it\n"
        "on both sides. Watch the loop commit a good intent, then refuse bad ones.\n"
    )

    substrate = build_substrate()

    # --- Act 1: a well-formed intent passes the whole loop -----------------------------
    good = Intent(
        action="grant_refund",
        scope={"usd": 40},
        claim="account u_8831 is tier-1 and eligible for a $40 refund",
        source_id="policy-refunds-v3",
        proposed_value={"action": "grant_refund", "amount_usd": 40, "user": "u_8831"},
    )
    print(BOLD + "1. A well-formed intent runs the full loop" + RESET)
    decision = substrate.decide(good)
    if not decision.committed:
        print(f"  {RED}{CROSS} unexpected refusal at {decision.refusal_stage}: {decision.refusal_reason}{RESET}")
        return 1
    print(f"  {GREEN}{CHECK} bounded{RESET}     grant_refund $40 within cap → {decision.outcome}")
    print(f"  {GREEN}{CHECK} evidence{RESET}    claim resolves to hashed source policy-refunds-v3")
    print(f"  {GREEN}{CHECK} validated{RESET}   proposal passed the deterministic validator (committed verbatim)")
    print(f"  {GREEN}{CHECK} audited{RESET}     ledger row hash={decision.ledger_hash[:8]}…")
    print(f"  {GREEN}{CHECK} reversible{RESET}  applied as version {decision.version}")
    print()

    # --- Reversibility + audit integrity ----------------------------------------------
    pre_hash = substrate.store.state_hash_at(0)
    restored_version = substrate.store.restore(0)
    post_hash = substrate.store.state_hash_at(restored_version)
    reversible_ok = post_hash == pre_hash
    audit_ok = substrate.ledger.verify()
    print(BOLD + "   Recover and re-check" + RESET)
    tick = f"{GREEN}{CHECK}{RESET}" if reversible_ok else f"{RED}{CROSS}{RESET}"
    print(f"  {tick} restore(version=0) reproduces the pre-action state hash exactly ({post_hash[:8]}…)")
    tick = f"{GREEN}{CHECK}{RESET}" if audit_ok else f"{RED}{CROSS}{RESET}"
    print(f"  {tick} the audit chain still verifies after commit + restore")
    if not (reversible_ok and audit_ok):
        return 1
    print()

    # --- Act 2: each stage refuses its own bad input -----------------------------------
    print(BOLD + "2. Each stage refuses its own failure, in isolation" + RESET)
    broken = [
        (
            "over-scope",
            Intent(
                action="delete_rows",
                scope={"rows": 10_000},
                claim="cleanup of stale rows",
                source_id="policy-refunds-v3",
                proposed_value={"action": "delete_rows", "amount_usd": 0},
            ),
        ),
        (
            "unsourced claim",
            Intent(
                action="grant_refund",
                scope={"usd": 40},
                claim="account is eligible (no source cited)",
                source_id=None,
                proposed_value={"action": "grant_refund", "amount_usd": 40},
            ),
        ),
        (
            "invalid proposal",
            Intent(
                action="grant_refund",
                scope={"usd": 40},
                claim="eligible refund",
                source_id="policy-refunds-v3",
                proposed_value={"action": "grant_refund"},  # missing required amount_usd
            ),
        ),
        (
            "unregistered action",
            Intent(
                action="wire_transfer",
                scope={"usd": 10},
                claim="pay vendor",
                source_id="policy-refunds-v3",
                proposed_value={"action": "wire_transfer", "amount_usd": 10},
            ),
        ),
    ]
    ledger_before = len(substrate.ledger.rows)
    all_refused = True
    for label, intent in broken:
        d = substrate.decide(intent)
        if d.committed:
            print(f"  {RED}{CROSS} {label}: committed anyway, a stage that should have refused did not!{RESET}")
            all_refused = False
            continue
        print(f"  {RED}{CROSS} {label:<20}{RESET} refused at {BOLD}{d.refusal_stage}{RESET}  {DIM}{d.refusal_reason}{RESET}")

    # No refused intent may leave a trace in the ledger: nothing partial commits.
    nothing_leaked = len(substrate.ledger.rows) == ledger_before
    print()
    if not (all_refused and nothing_leaked):
        return 1

    print(rule())
    print(
        f"{GREEN}{CHECK} One intent, five governed stages.{RESET} A good decision commits, "
        f"is auditable,\n  and is reversible; a bad one is refused at the exact stage that owns "
        f"that check, \n  and nothing partial leaks into the record. "
        f"{DIM}The substrate is a pipeline, not a prompt.\n  (See each sibling demo under demos/ for "
        f"the fuller proof of each stage.){RESET}"
    )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

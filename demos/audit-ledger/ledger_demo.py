"""
ledger_demo.py — watch a tamper-evident audit ledger catch a corrupted row.

Run it:

    python demos/audit-ledger/ledger_demo.py

No installation, no dependencies — Python 3 standard library only.

The story in three acts:
  1. A governed system commits a few decision records to an append-only ledger.
  2. verify() recomputes the chain from genesis: every row is intact.
  3. An attacker edits one PAST row's verdict. verify() runs again and pinpoints
     the exact row where the chain breaks — the tampering is *evident*, not silent.

This is the runnable proof behind the claim in README.md and BOSS-STANDARD.md that
every decision writes a "hash-chained, tamper-evident ledger entry."
"""

from __future__ import annotations

from ledger import Ledger

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


def print_chain(ledger: Ledger) -> None:
    for row in ledger.rows:
        verdict = row.body.get("verdict", "")
        print(
            f"  row {row.index}  hash={row.short()}…  "
            f"{DIM}prev={row.prev_hash[:8]}…{RESET}  "
            f"{DIM}verdict={verdict}{RESET}"
        )


def main() -> int:
    print()
    print(BOLD + "the-substrate · tamper-evident audit ledger" + RESET)
    print(rule("═"))
    print(
        "A governance engine records every decision to an append-only, "
        "SHA-256\nhash-chained ledger. Each row folds in the previous row's hash, "
        "so\nany later edit to a past row is detectable. Let's watch that happen.\n"
    )

    # --- Act 1: a governed system commits decisions ------------------------------
    ledger = Ledger()
    decisions = [
        {"action": "grant_refund", "amount_usd": 40, "model": "claude", "verdict": "allow"},
        {"action": "escalate_ticket", "priority": "high", "model": "claude", "verdict": "allow"},
        {"action": "delete_account", "user": "u_8831", "model": "claude", "verdict": "deny"},
        {"action": "publish_post", "post": "p_552", "model": "claude", "verdict": "allow"},
    ]
    print(BOLD + "1. Committing governed decisions" + RESET)
    for d in decisions:
        row = ledger.append(d)
        print(f"  {GREEN}[append]{RESET} row {row.index}  hash={row.short()}…  {d['action']} → {d['verdict']}")
    print()

    # --- Act 2: verify the intact chain ------------------------------------------
    print(BOLD + "2. Verifying the chain" + RESET)
    result = ledger.verify()
    print(f"  {GREEN}{CHECK} chain verified: {result.checked}/{len(ledger.rows)} rows intact{RESET}")
    print()
    print_chain(ledger)
    print()

    # --- Act 3: an attacker rewrites history -------------------------------------
    target = 2  # the "deny delete_account" decision
    print(BOLD + "3. An attacker rewrites a past decision" + RESET)
    print(
        f"  Row {target} recorded {BOLD}deny{RESET} on 'delete_account'. "
        f"An attacker flips it to\n  {BOLD}allow{RESET} — editing the stored row "
        f"directly, reaching past the append-only API."
    )
    tampered = dict(ledger.rows[target].body)
    tampered["verdict"] = "allow"
    ledger._tamper_body(target, tampered)  # silent edit — hash NOT recomputed
    print(f"  {RED}[tamper]{RESET} row {target} verdict: deny → allow  {DIM}(hash left unchanged){RESET}")
    print()

    print(BOLD + "   Re-verifying…" + RESET)
    result = ledger.verify()
    if result.ok:
        # This branch must never execute — if it does, the mechanism is broken.
        print(f"  {RED}{CROSS} tampering went UNDETECTED — the ledger is not tamper-evident!{RESET}")
        return 1

    print(f"  {RED}{CROSS} CHAIN BROKEN at row {result.broken_index}{RESET}")
    print(f"    {DIM}{result.reason}{RESET}")
    print(
        f"    {DIM}row {result.broken_index} no longer matches its hash, so every row "
        f"after it is\n    untrustworthy — the forgery cannot hide.{RESET}"
    )
    print()
    print(rule())
    print(
        f"{GREEN}{CHECK} The ledger is tamper-evident.{RESET} "
        "Silent edits to history are impossible;\n  any alteration is caught by recomputation. "
        f"{DIM}(See demos/audit-ledger/README.md and\n  docs/adr/ADR-0001 for why this mechanism, and what it does not claim.){RESET}"
    )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

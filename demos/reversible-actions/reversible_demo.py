"""
reversible_demo.py — watch a versioned store gate, guard, and recover.

Run it:

    python demos/reversible-actions/reversible_demo.py

No installation, no dependencies — Python 3 standard library only.

The story in four acts:
  1. A governed system commits a few gated changes. Each is a NEW version;
     nothing already committed is ever touched.
  2. An ungated high-impact action is attempted. It is REFUSED before it can apply.
  3. Something reaches past the API to edit / delete a version in place. The durable
     append-only guard FAILS CLOSED — both attempts are refused.
  4. Recovery: restore(version=N) reconstructs a prior state by superseding forward,
     and its state_hash matches the original snapshot byte-for-byte.

This is the runnable proof behind the BOSS-STANDARD.md claim: "**Reversible** |
High-impact actions are gated, versioned, and recoverable."
"""

from __future__ import annotations

from reversible import AppendOnlyViolation, Store, UngatedHighImpactError

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
    print(BOLD + "the-substrate · reversible, gated, versioned state" + RESET)
    print(rule("═"))
    print(
        "A governance engine treats high-impact state changes as gated and\n"
        "recoverable. The only sanctioned mutation is a new version appended\n"
        "forward — never an edit to what's already committed. Let's watch that.\n"
    )

    guard_refusals = 0

    # --- Act 1: gated changes supersede forward -----------------------------------
    print(BOLD + "1. Committing gated changes" + RESET)
    store = Store()
    print(f"  {DIM}[genesis] version 0  hash={store.head.short()}…  state={{}}{RESET}")
    changes = [
        {"balance_usd": 100, "status": "active"},
        {"status": "verified"},
        {"tier": "gold"},
    ]
    for change in changes:
        v = store.apply(change, gated=True, note=f"apply {change!r}")
        print(f"  {GREEN}[apply]{RESET}  version {v.index}  hash={v.short()}…  state={v.state}")
    checkpoint_index = store.head.index  # the version we'll recover to, in Act 4
    checkpoint_hash = store.head.state_hash
    print()

    # --- Act 2: an ungated high-impact action is refused --------------------------
    print(BOLD + "2. An ungated high-impact action" + RESET)
    print(
        f"  Someone attempts {BOLD}{{'balance_usd': 0}}{RESET} as high-impact, with\n"
        "  no approval token attached."
    )
    try:
        store.apply({"balance_usd": 0}, high_impact=True)
        print(f"  {RED}{CROSS} the change applied — the gate did not hold!{RESET}")
        return 1
    except UngatedHighImpactError as exc:
        print(f"  {RED}[refused]{RESET}  {exc}")
    print()

    # --- Act 3: in-place mutation fails closed -------------------------------------
    print(BOLD + "3. An attempt to edit history in place" + RESET)
    print(f"  Something reaches past apply()/restore() to touch a stored version directly.")
    for label, action in (
        ("update", lambda: store._update_in_place(1, {"status": "banned"})),
        ("delete", lambda: store._delete_in_place(0)),
    ):
        try:
            action()
            print(f"  {RED}{CROSS} in-place {label} succeeded — the append-only guard failed!{RESET}")
            return 1
        except AppendOnlyViolation as exc:
            guard_refusals += 1
            print(f"  {RED}[fails closed]{RESET}  {exc}")
    print()

    # --- Act 4: recovery via restore(N) --------------------------------------------
    print(BOLD + "4. Recovering a prior state" + RESET)
    # Advance state further so there's something to recover *from*.
    store.apply({"tier": "platinum", "status": "flagged"}, gated=True, note="later drift")
    print(
        f"  {DIM}[apply]{RESET}  version {store.head.index}  hash={store.head.short()}…  "
        f"state={store.head.state}"
    )
    print(f"  Recovering to version {checkpoint_index} (hash={checkpoint_hash[:8]}…)…")
    restored = store.restore(checkpoint_index)
    print(
        f"  {GREEN}[restore]{RESET}  version {restored.index}  hash={restored.short()}…  "
        f"state={restored.state}"
    )
    if restored.state_hash != checkpoint_hash:
        print(f"  {RED}{CROSS} restored hash != original snapshot hash — recovery is not deterministic!{RESET}")
        return 1
    print(f"  {GREEN}{CHECK} restored state_hash matches version {checkpoint_index} exactly, byte-for-byte.{RESET}")
    print()

    chain = store.verify_chain()
    print(BOLD + "5. Verifying the version chain" + RESET)
    if not chain.ok:
        print(f"  {RED}{CROSS} chain broken at version {chain.broken_index}: {chain.reason}{RESET}")
        return 1
    print(f"  {GREEN}{CHECK} chain verified: {chain.checked}/{len(store.versions)} versions intact{RESET}")
    print()

    print(rule())
    print(
        f"{GREEN}{CHECK} {guard_refusals} in-place mutations refused (fail-closed); "
        f"restore({checkpoint_index}) reproduces prior state hash exactly (1/1).{RESET}"
    )
    print(
        f"  {DIM}(See demos/reversible-actions/README.md for why this mechanism, and "
        f"what it does not claim.){RESET}"
    )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

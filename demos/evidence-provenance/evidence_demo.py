"""
evidence_demo.py: watch a claim's evidence get pulled out from under it.

Run it:

    python demos/evidence-provenance/evidence_demo.py

No installation, no dependencies. Python 3 standard library only.

The story in three acts:
  1. Sources are registered and claims are asserted against them. Each claim pins
     its source's content_hash at assert-time.
  2. A claim tries to name a source that was never registered. It is REFUSED,
     fail-closed: no evidence without a resolvable source.
  3. An attacker edits a registered source's bytes. Re-verifying the claims that
     depended on it shows them go STALE automatically. No one has to notice and
     revoke them by hand; the pinned hash simply stops matching.

This is the runnable proof behind the claim in README.md and BOSS-STANDARD.md that
the substrate is "evidence-backed": facts trace to hashed sources and are superseded
when the ground truth moves (ADR-0005), rather than staying silently trusted.
"""

from __future__ import annotations

from evidence import EvidenceStore, UnsourcedClaimError

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
    print(BOLD + "the-substrate · evidence-backed claims" + RESET)
    print(rule("═"))
    print(
        "A governed system only asserts claims that trace to a registered source.\n"
        "Each claim pins the source's SHA-256 content_hash at assert-time. If the\n"
        "source's bytes ever move, the claim detaches automatically. Let's watch it.\n"
    )

    store = EvidenceStore()

    # --- Act 1: register sources, assert claims that resolve to them -------------
    print(BOLD + "1. Registering sources and asserting grounded claims" + RESET)
    h1 = store.add_source("policy_refund_v1", "Refunds under $50 are auto-approved.")
    print(f"  {GREEN}[source]{RESET} policy_refund_v1  hash={h1[:8]}…")
    h2 = store.add_source("policy_delete_v1", "Account deletion requires manager review.")
    print(f"  {GREEN}[source]{RESET} policy_delete_v1  hash={h2[:8]}…")

    claim_a = store.assert_claim("A $40 refund may be auto-approved.", "policy_refund_v1")
    print(f"  {GREEN}[claim]{RESET}  {claim_a.statement!r}  pinned={claim_a.short()}…  {DIM}({claim_a.trust_class}){RESET}")
    claim_b = store.assert_claim("Deleting u_8831 needs manager sign-off.", "policy_delete_v1")
    print(f"  {GREEN}[claim]{RESET}  {claim_b.statement!r}  pinned={claim_b.short()}…  {DIM}({claim_b.trust_class}){RESET}")
    claim_c = store.assert_claim("A $45 refund may be auto-approved.", "policy_refund_v1")
    print(f"  {GREEN}[claim]{RESET}  {claim_c.statement!r}  pinned={claim_c.short()}…  {DIM}({claim_c.trust_class}){RESET}")
    print()

    # --- Act 2: a claim with no resolvable source is refused ---------------------
    print(BOLD + "2. A claim names a source that was never registered" + RESET)
    try:
        store.assert_claim("Refunds over $10,000 are auto-approved.", "policy_refund_v9_ghost")
        print(f"  {RED}{CROSS} claim was accepted, this must never happen!{RESET}")
        return 1
    except UnsourcedClaimError as exc:
        print(f"  {RED}[refused]{RESET} {exc}")
    print()

    # --- Act 3: an attacker edits ground truth out from under two claims ---------
    print(BOLD + "3. An attacker edits a source after claims were asserted" + RESET)
    print(
        "  policy_refund_v1 backs TWO claims (A and C). An attacker rewrites its\n"
        "  text, reaching past the API to edit stored bytes directly."
    )
    store._tamper_source("policy_refund_v1", "Refunds under $50 require manager review.")
    print(f"  {RED}[tamper]{RESET} policy_refund_v1 text edited  {DIM}(claims' pinned hashes left unchanged){RESET}")
    print()

    print(BOLD + "   Re-verifying every claim…" + RESET)
    results = {
        "A (refund $40)": store.verify(claim_a),
        "B (delete review)": store.verify(claim_b),
        "C (refund $45)": store.verify(claim_c),
    }
    all_expected = True
    for label, result in results.items():
        if result.ok:
            print(f"  {GREEN}{CHECK} {label}: still grounded{RESET}")
        else:
            print(f"  {RED}{CROSS} {label}: STALE, {result.reason}{RESET}")

    if results["A (refund $40)"].ok or results["C (refund $45)"].ok:
        # These two claims share the tampered source. If either still verifies,
        # the detachment mechanism is broken. This branch must never execute.
        print(f"  {RED}{CROSS} a claim on the tampered source went UNDETECTED as stale!{RESET}")
        return 1
    if not results["B (delete review)"].ok:
        # B's source was never touched; it must still verify cleanly.
        print(f"  {RED}{CROSS} an untouched claim was wrongly marked stale!{RESET}")
        return 1
    print()

    print(rule())
    print(
        f"{GREEN}{CHECK} The store is evidence-backed.{RESET} Claims without a resolvable\n"
        "  source are refused before they exist; claims whose source drifts detach\n"
        f"  automatically. {DIM}(See demos/evidence-provenance/README.md and\n"
        f"  docs/adr/ADR-0005-rag-is-not-the-substrate.md for why this mechanism,\n"
        f"  and what it does not claim.){RESET}"
    )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

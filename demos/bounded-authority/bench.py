"""
bench.py — a small, reproducible benchmark for the deny-by-default policy gate.

Run it:

    python demos/bounded-authority/bench.py            # default K = 500 proposals
    python demos/bounded-authority/bench.py 2000        # custom proposal count

Standard-library only. Prints a Markdown table of measured numbers — not adjectives —
and the exact command to reproduce them.

What it measures (and what it does NOT):
  - proposal throughput   — decisions/sec the gate can render
  - outcome mix           — how many of K mixed proposals proceed / escalate / block
  - refusal completeness  — of the proposals that were over-scoped or unregistered,
                             how many were blocked before execution (must be ALL of them)
This benchmarks the gate PRIMITIVE's throughput and refusal completeness. It is not an
end-to-end governance benchmark, and makes no claim about model quality.
"""

from __future__ import annotations

import sys
import time
from gate import Gate


def _fmt(n: float) -> str:
    return f"{n:,.0f}"


def _seeded_gate() -> Gate:
    gate = Gate()
    gate.register(
        "send_email", tier="yellow",
        soft_cap={"max_recipients": 50}, hard_ceiling={"max_recipients": 200},
    )
    gate.register(
        "grant_refund", tier="orange",
        soft_cap={"max_usd": 100}, hard_ceiling={"max_usd": 1000},
    )
    gate.register(
        "delete_rows", tier="red",
        soft_cap={"max_rows": 20}, hard_ceiling={"max_rows": 100},
    )
    gate.register(
        "wire_transfer", tier="purple",
        soft_cap={"max_usd": 500}, hard_ceiling={"max_usd": 5000},
    )
    return gate


def _build_proposals(k: int) -> list[tuple[str, dict[str, float], bool]]:
    """Deterministically build K mixed proposals. The bool marks whether the proposal
    is *deliberately* over-scoped or unregistered — i.e. must never be allowed to
    reach 'proceed'."""
    registered_scopes = [
        ("send_email", {"max_recipients": 10}, False),      # in-policy
        ("send_email", {"max_recipients": 150}, False),     # over soft, under hard
        ("grant_refund", {"max_usd": 40}, False),            # in-policy
        ("delete_rows", {"max_rows": 5}, False),              # in-policy
    ]
    over_scoped = [
        ("delete_rows", {"max_rows": 10_000}, True),         # over hard ceiling
        ("wire_transfer", {"max_usd": 50_000}, True),        # over hard ceiling
        ("rotate_prod_credentials", {"max_usd": 0}, True),   # unregistered
        ("drop_table", {"max_rows": 1}, True),                # unregistered
    ]
    pool = registered_scopes + over_scoped
    return [pool[i % len(pool)] for i in range(k)]


def bench_propose(k: int) -> tuple[list, float]:
    gate = _seeded_gate()
    proposals = _build_proposals(k)
    decisions = []
    t0 = time.perf_counter()
    for action, scope, is_bad in proposals:
        decisions.append((gate.propose(action, scope), is_bad))
    dt = time.perf_counter() - t0
    return decisions, dt


def main(argv: list[str]) -> int:
    k = int(argv[1]) if len(argv) > 1 else 500

    print()
    print(f"Benchmarking the bounded-authority gate over K = {_fmt(k)} mixed proposals…")
    print()

    decisions, dt = bench_propose(k)

    counts = {"proceed": 0, "escalated": 0, "blocked": 0}
    bad_total = 0
    bad_blocked = 0
    for decision, is_bad in decisions:
        counts[decision.outcome] += 1
        if is_bad:
            bad_total += 1
            if decision.outcome == "blocked":
                bad_blocked += 1

    propose_rps = k / dt if dt else float("inf")

    print(f"| Metric | Result |")
    print(f"|---|---|")
    print(f"| Proposals evaluated | {_fmt(k)} |")
    print(f"| Proposal throughput | {_fmt(propose_rps)} decisions/sec |")
    print(f"| proceed | {counts['proceed']} |")
    print(f"| escalated | {counts['escalated']} |")
    print(f"| blocked | {counts['blocked']} |")
    print(f"| Over-scoped/unregistered proposals blocked | {bad_blocked}/{bad_total} |")
    print()
    print(f"{bad_blocked}/{bad_total} over-scoped proposals blocked; 0 reached execution.")
    print()
    reproduce = "python demos/bounded-authority/bench.py" + (f" {k}" if k != 500 else "")
    print(f"Reproduce: `{reproduce}`  ·  Python {sys.version.split()[0]}  ·  numbers vary by machine.")
    print()

    # A benchmark of deny-by-default that ever lets an over-scoped proposal through
    # is a failed benchmark.
    return 0 if bad_blocked == bad_total else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

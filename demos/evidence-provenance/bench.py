"""
bench.py: a small, reproducible benchmark for the evidence store.

Run it:

    python demos/evidence-provenance/bench.py            # default N = 50,000 sources/claims
    python demos/evidence-provenance/bench.py 200000     # custom count

Standard-library only. Prints a Markdown table of measured numbers, not adjectives,
and the exact command to reproduce them.

What it measures (and what it does NOT):
  - assert throughput: claims/sec pinned against registered sources
  - verify throughput: claims/sec re-checked against current source hashes
  - unsourced refusal: of K claims naming unregistered sources, how many are refused
  - tamper detection: of K source edits, how many detach the claim they backed
This benchmarks the evidence PRIMITIVE's provenance-pinning and refusal overhead. It
is a primitive-level benchmark, not an end-to-end governance benchmark, and makes no
claim about model quality.
"""

from __future__ import annotations

import sys
import time
from evidence import EvidenceStore, UnsourcedClaimError


def _fmt(n: float) -> str:
    return f"{n:,.0f}"


def bench_assert(n: int) -> tuple[EvidenceStore, list, float]:
    store = EvidenceStore()
    for i in range(n):
        store.add_source(f"src_{i}", f"fact text number {i}")
    t0 = time.perf_counter()
    claims = [store.assert_claim(f"claim about src_{i}", f"src_{i}") for i in range(n)]
    dt = time.perf_counter() - t0
    return store, claims, dt


def bench_verify(store: EvidenceStore, claims: list) -> tuple[bool, float]:
    t0 = time.perf_counter()
    all_ok = all(store.verify(c).ok for c in claims)
    dt = time.perf_counter() - t0
    return all_ok, dt


def bench_unsourced_refusal(k: int) -> tuple[int, int]:
    """Try k claims naming a source that was never registered; count how many
    are refused with UnsourcedClaimError."""
    store = EvidenceStore()
    refused = 0
    for j in range(k):
        try:
            store.assert_claim(f"ghost claim {j}", f"src_ghost_{j}")
        except UnsourcedClaimError:
            refused += 1
    return refused, k


def bench_tamper_detection(n: int, k: int) -> tuple[int, int]:
    """Edit k distinct sources (one at a time, each on a fresh store) and count how
    many detach the claim they backed. A deterministic spread of indices keeps this
    reproducible."""
    caught = 0
    for j in range(k):
        store = EvidenceStore()
        for i in range(n):
            store.add_source(f"src_{i}", f"fact text number {i}")
        target = (j * (n - 1)) // max(k - 1, 1) if k > 1 else n // 2
        claim = store.assert_claim(f"claim about src_{target}", f"src_{target}")
        store._tamper_source(f"src_{target}", f"tampered fact text number {target}")
        if not store.verify(claim).ok:
            caught += 1
    return caught, k


def main(argv: list[str]) -> int:
    n = int(argv[1]) if len(argv) > 1 else 50_000
    k = 200  # number of independent trials for refusal / tamper detection

    print()
    print(f"Benchmarking the evidence store over N = {_fmt(n)} sources/claims…")
    print()

    store, claims, assert_dt = bench_assert(n)
    all_ok, verify_dt = bench_verify(store, claims)
    assert all_ok, "seeded claims failed to verify, benchmark environment is broken"
    refused, refusal_trials = bench_unsourced_refusal(k)
    caught, tamper_trials = bench_tamper_detection(min(n, 2_000), k)

    assert_rps = n / assert_dt if assert_dt else float("inf")
    verify_rps = n / verify_dt if verify_dt else float("inf")
    refusal_pct = 100.0 * refused / refusal_trials
    detect_pct = 100.0 * caught / tamper_trials

    print(f"| Metric | Result |")
    print(f"|---|---|")
    print(f"| Sources / claims | {_fmt(n)} |")
    print(f"| Assert throughput | {_fmt(assert_rps)} claims/sec |")
    print(f"| Verify throughput | {_fmt(verify_rps)} claims/sec |")
    print(f"| Verify latency (all claims) | {verify_dt * 1000:,.1f} ms |")
    print(f"| Unsourced claim refusal | {refused}/{refusal_trials} refused ({refusal_pct:.1f}%) |")
    print(f"| Tamper detection (source edit → claim detach) | {caught}/{tamper_trials} detached ({detect_pct:.1f}%) |")
    print()
    reproduce = "python demos/evidence-provenance/bench.py" + (f" {n}" if n != 50_000 else "")
    print(f"Reproduce: `{reproduce}`  ·  Python {sys.version.split()[0]}  ·  numbers vary by machine.")
    print()

    # A benchmark of fail-closed refusal or detachment that ever misses one is a failed benchmark.
    ok = refused == refusal_trials and caught == tamper_trials
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

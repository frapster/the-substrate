"""
bench.py: a small, reproducible benchmark for the hash-chained ledger.

Run it:

    python demos/audit-ledger/bench.py            # default N = 50,000 rows
    python demos/audit-ledger/bench.py 200000     # custom row count

Standard-library only. Prints a Markdown table of measured numbers, and the exact
command to reproduce them.

What it measures (and what it does NOT):
  - append throughput      : rows/sec committed to the chain
  - verify throughput      : rows/sec recomputed by a full-chain verify()
  - tamper detection       : of K randomly corrupted rows, how many verify() catches
This benchmarks the ledger PRIMITIVE's integrity and overhead. It is not an
end-to-end governance benchmark, and makes no claim about model quality.
"""

from __future__ import annotations

import sys
import time
from ledger import Ledger


def _fmt(n: float) -> str:
    return f"{n:,.0f}"


def bench_append(n: int) -> tuple[Ledger, float]:
    ledger = Ledger()
    t0 = time.perf_counter()
    for i in range(n):
        ledger.append({"action": "decide", "seq": i, "model": "claude", "verdict": "allow"})
    dt = time.perf_counter() - t0
    return ledger, dt


def bench_verify(ledger: Ledger) -> tuple[bool, float]:
    t0 = time.perf_counter()
    result = ledger.verify()
    dt = time.perf_counter() - t0
    return result.ok, dt


def bench_tamper_detection(n: int, k: int) -> tuple[int, int]:
    """Corrupt k distinct rows (one at a time, each on a fresh chain) and count how
    many verify() catches. A deterministic spread of indices keeps this reproducible."""
    caught = 0
    for j in range(k):
        ledger = Ledger()
        for i in range(n):
            ledger.append({"action": "decide", "seq": i, "verdict": "allow"})
        target = (j * (n - 1)) // max(k - 1, 1) if k > 1 else n // 2
        edited = dict(ledger.rows[target].body)
        edited["verdict"] = "deny"  # flip the recorded decision
        ledger._tamper_body(target, edited)
        if not ledger.verify().ok:
            caught += 1
    return caught, k


def main(argv: list[str]) -> int:
    n = int(argv[1]) if len(argv) > 1 else 50_000
    k = 200  # number of independent tamper trials

    print()
    print(f"Benchmarking the hash-chained ledger over N = {_fmt(n)} rows…")
    print()

    ledger, append_dt = bench_append(n)
    ok, verify_dt = bench_verify(ledger)
    assert ok, "seeded chain failed to verify, benchmark environment is broken"
    caught, trials = bench_tamper_detection(min(n, 2_000), k)

    append_rps = n / append_dt if append_dt else float("inf")
    verify_rps = n / verify_dt if verify_dt else float("inf")
    detect_pct = 100.0 * caught / trials

    print(f"| Metric | Result |")
    print(f"|---|---|")
    print(f"| Rows in chain | {_fmt(n)} |")
    print(f"| Append throughput | {_fmt(append_rps)} rows/sec |")
    print(f"| Verify throughput (full chain) | {_fmt(verify_rps)} rows/sec |")
    print(f"| Verify latency (full chain) | {verify_dt * 1000:,.1f} ms |")
    print(f"| Tamper detection | {caught}/{trials} corrupted rows caught ({detect_pct:.1f}%) |")
    print()
    reproduce = "python demos/audit-ledger/bench.py" + (f" {n}" if n != 50_000 else "")
    print(f"Reproduce: `{reproduce}`  ·  Python {sys.version.split()[0]}  ·  numbers vary by machine.")
    print()

    # A benchmark of tamper-evidence that ever misses a tamper is a failed benchmark.
    return 0 if caught == trials else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

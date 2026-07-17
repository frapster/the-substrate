"""
bench.py — a small, reproducible benchmark for governed vs. naive knowledge retrieval.

Run it:

    python demos/governed-knowledge/bench.py            # default K = 3,000 trials
    python demos/governed-knowledge/bench.py 10000       # custom trial count

Standard-library only. Prints a Markdown table of measured numbers — not adjectives —
and the exact command to reproduce them.

What it measures (and what it does NOT):
  - across K supersession-query trials, how often naive_retrieve returns the STALE
    atom (expected: (near) all of them — that's the failure mode being demonstrated)
  - across the SAME K trials, how often governed_retrieve is correct-or-safe: it
    either returns the CURRENT atom, or ABSTAINS — it must never return a stale
    atom or an atom outside the requested scope
This benchmarks the retrieval-ranking PRIMITIVE's behavior under supersession. It is
not an end-to-end governance benchmark, and makes no claim about embedding quality —
these are hand-authored toy vectors (see README.md), not a real embedding model.
"""

from __future__ import annotations

import random
import sys
import time

from knowledge import SUPERSESSION_QUERIES, seed_knowledge_base


def _fmt(n: float) -> str:
    return f"{n:,.0f}"


def _jitter(query: tuple[float, ...], rng: random.Random, magnitude: float = 0.03) -> tuple[float, ...]:
    """Perturb a query embedding slightly so repeated trials aren't bit-identical,
    while staying close enough to the original query's intent to be a fair,
    reproducible restatement of the same question."""
    return tuple(max(0.0, x + rng.uniform(-magnitude, magnitude)) if x != 0.0 else 0.0 for x in query)


def bench(k: int) -> tuple[int, int, int, int, float]:
    """Run K trials, cycling through the seeded supersession pairs with small
    deterministic jitter. Returns:
        naive_stale_count    — trials where naive_retrieve returned the stale atom
        governed_correct     — trials where governed_retrieve returned the current atom
        governed_safe_abstain — trials where governed_retrieve abstained instead of erring
        governed_wrong       — trials where governed_retrieve returned anything else (bug)
        elapsed_seconds
    """
    rng = random.Random(1729)  # fixed seed: reproducible across machines
    kb = seed_knowledge_base()
    by_id = {a.atom_id: a for a in kb.atoms}

    naive_stale_count = 0
    governed_correct = 0
    governed_safe_abstain = 0
    governed_wrong = 0

    t0 = time.perf_counter()
    for i in range(k):
        stale_id, current_id, base_query, scope = SUPERSESSION_QUERIES[i % len(SUPERSESSION_QUERIES)]
        query = _jitter(base_query, rng)

        naive = kb.naive_retrieve(query)
        if naive.atom is not None and naive.atom.atom_id == stale_id:
            naive_stale_count += 1

        governed = kb.governed_retrieve(query, scope=scope)
        if governed.degraded:
            governed_safe_abstain += 1
        elif governed.atom is not None and governed.atom.atom_id == current_id:
            governed_correct += 1
        else:
            governed_wrong += 1  # returned the stale atom, or the wrong atom — a real failure
    dt = time.perf_counter() - t0

    return naive_stale_count, governed_correct, governed_safe_abstain, governed_wrong, dt


def main(argv: list[str]) -> int:
    k = int(argv[1]) if len(argv) > 1 else 3_000

    print()
    print(f"Benchmarking governed vs. naive knowledge retrieval over K = {_fmt(k)} trials…")
    print()

    naive_stale_count, governed_correct, governed_safe_abstain, governed_wrong, dt = bench(k)
    governed_safe_total = governed_correct + governed_safe_abstain
    rps = k / dt if dt else float("inf")

    print(f"| Metric | Result |")
    print(f"|---|---|")
    print(f"| Trials (K) | {_fmt(k)} |")
    print(f"| naive_retrieve returned the STALE atom | {naive_stale_count}/{k} ({100.0 * naive_stale_count / k:.1f}%) |")
    print(f"| governed_retrieve returned the CURRENT atom | {governed_correct}/{k} ({100.0 * governed_correct / k:.1f}%) |")
    print(f"| governed_retrieve abstained (degraded) | {governed_safe_abstain}/{k} ({100.0 * governed_safe_abstain / k:.1f}%) |")
    print(f"| governed_retrieve correct-or-safe (current ∪ abstain) | {governed_safe_total}/{k} ({100.0 * governed_safe_total / k:.1f}%) |")
    print(f"| governed_retrieve WRONG (stale or off-scope) | {governed_wrong}/{k} |")
    print(f"| Throughput (both retrievers, per trial pair) | {_fmt(rps)} trials/sec |")
    print()
    reproduce = "python demos/governed-knowledge/bench.py" + (f" {k}" if k != 3_000 else "")
    print(f"Reproduce: `{reproduce}`  ·  Python {sys.version.split()[0]}  ·  numbers vary by machine.")
    print()

    # A benchmark of governed retrieval that is ever WRONG (not just abstaining) has
    # failed. It's fine — expected — for naive_retrieve to keep losing to staleness;
    # that's the point being measured, not a pass/fail condition on its own.
    return 0 if governed_wrong == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

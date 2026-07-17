# demo — a runnable, evidence-backed claim store

A small, **zero-dependency** proof of one claim `the-substrate` makes in prose: that
the substrate is *evidence-backed* — an asserted fact traces to a hashed source and is
superseded (or detached) when that source changes, rather than merely being "the
nearest chunk by embedding distance" (see [`../../README.md`](../../README.md),
[`../../BOSS-STANDARD.md`](../../BOSS-STANDARD.md), and
[`../../docs/adr/ADR-0005-rag-is-not-the-substrate.md`](../../docs/adr/ADR-0005-rag-is-not-the-substrate.md)).

You should be able to clone the repo and see it work in under a minute. No `pip install`,
no build — Python 3 standard library only.

## Quickstart (30 seconds)

```bash
python demos/evidence-provenance/evidence_demo.py
```

You'll watch sources get registered, claims get pinned to their content_hash, an
unsourced claim get refused before it exists, and — after an attacker edits a source's
bytes — every claim pinned to it detach automatically:

```
3. An attacker edits a source after claims were asserted
  [tamper] policy_refund_v1 text edited  (claims' pinned hashes left unchanged)

   Re-verifying every claim…
  ✗ A (refund $40): STALE — source 'policy_refund_v1' current hash a4a85287… != pinned 436ef3cd…
  ✓ B (delete review): still grounded
  ✗ C (refund $45): STALE — source 'policy_refund_v1' current hash a4a85287… != pinned 436ef3cd…
```

That last moment — two claims sharing one source, both **detaching the instant the
source moves** — is the whole point.

## Run the tests

The negative tests are the interesting ones: they assert that an unsourced claim is
refused, and that a source edit detaches every claim pinned to it — including when two
claims share one source, and that an untouched source's claims are left alone.

```bash
python demos/evidence-provenance/test_evidence.py
# or:  python -m unittest discover -s demos/evidence-provenance
```

## Run the benchmark

Measured numbers, not adjectives. This benchmarks the evidence primitive's
provenance-pinning and refusal overhead — not end-to-end governance, and not model
quality.

```bash
python demos/evidence-provenance/bench.py            # default N = 50,000 sources/claims
python demos/evidence-provenance/bench.py 200000     # custom count
```

Sample run (Python 3.13, a 2020-class laptop — **your numbers will vary; regenerate
with the command above**):

| Metric | Result |
|---|---|
| Sources / claims | 50,000 |
| Assert throughput | 232,038 claims/sec |
| Verify throughput | 326,777 claims/sec |
| Verify latency (all claims) | 153.0 ms |
| Unsourced claim refusal | 200/200 refused (100.0%) |
| Tamper detection (source edit → claim detach) | 200/200 detached (100.0%) |

## How it works

```
claim.pinned_hash = SHA256( canonical bytes of source.text at assert-time )
```

A claim is only as good as the source it names. `assert_claim()` fails closed if the
source doesn't resolve — a claim with no evidence never gets stored. On success it pins
the source's `content_hash` at that instant. `verify()` recomputes the source's CURRENT
hash and compares it to what's pinned: if they diverge, the source moved out from under
the claim, and the claim is reported as detached rather than silently trusted.

- [`evidence.py`](./evidence.py) — the `EvidenceStore` class: `add_source()`,
  `assert_claim()`, `verify()`; no way to assert a claim without a resolvable source.
- [`evidence_demo.py`](./evidence_demo.py) — the narrative runner above.
- [`test_evidence.py`](./test_evidence.py) — `unittest` suite, including the refusal
  and detachment cases.
- [`bench.py`](./bench.py) — the reproducible benchmark.

## What this proves — and what it does NOT

**Proves:** claims that cannot resolve to a registered source are refused before they
exist, and claims whose source is edited after the fact detach automatically —
content-hash pinning is a real, checkable provenance mechanism, demonstrated by code
you can run.

**Does NOT prove / is NOT:** this is a **generic hashing/pinning primitive**, not the
BOSNet.io evidence model. It is not a full knowledge substrate — it does not do
retrieval, atomic fact extraction, versioning, or reconciliation across superseding
sources; those live in the (proprietary) reference implementation described in
[`../../BOSS-STANDARD.md`](../../BOSS-STANDARD.md) and reserved by
[`../../LICENSE.md`](../../LICENSE.md). Detecting that a source moved is not the same
as knowing *which* of two conflicting sources is now true — that's a reconciliation
problem this toy does not attempt (see
[`../../docs/adr/ADR-0005-rag-is-not-the-substrate.md`](../../docs/adr/ADR-0005-rag-is-not-the-substrate.md)).
The case-study "after" figures elsewhere in this repo remain **labeled estimates**,
except Relic Wars.

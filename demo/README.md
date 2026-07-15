# demo — a runnable, tamper-evident audit ledger

A small, **zero-dependency** proof of one claim `the-substrate` makes in prose: that a
governance engine records every decision to a *hash-chained, tamper-evident ledger*
(see [`../README.md`](../README.md), [`../BOSS-STANDARD.md`](../BOSS-STANDARD.md), and
[`../docs/adr/ADR-0001-hash-chained-audit-ledger.md`](../docs/adr/ADR-0001-hash-chained-audit-ledger.md)).

You should be able to clone the repo and see it work in under a minute. No `pip install`,
no build — Python 3 standard library only.

## Quickstart (30 seconds)

```bash
python demo/ledger_demo.py
```

You'll watch four governed decisions get committed to the chain, verify as intact, and
then — after an attacker silently edits one *past* decision — you'll watch `verify()`
pinpoint the exact broken row:

```
3. An attacker rewrites a past decision
  [tamper] row 2 verdict: deny → allow  (hash left unchanged)

   Re-verifying…
  ✗ CHAIN BROKEN at row 2
    row 2 recomputed hash 86d17a4f… != stored 813c6b22… (body was altered)
```

That last moment — the chain **detecting** tampering — is the whole point.

## Run the tests

The negative tests are the interesting ones: they assert `verify()` *fails*, for the
right reason, under a body edit, a deletion, a reordering, and a partial forgery.

```bash
python demo/test_ledger.py
# or:  python -m unittest discover -s demo
```

## Run the benchmark

Measured numbers, not adjectives. This benchmarks the ledger primitive's integrity and
overhead — not end-to-end governance, and not model quality.

```bash
python demo/bench.py            # default N = 50,000 rows
python demo/bench.py 200000     # custom row count
```

Sample run (Python 3.13, a 2020-class laptop — **your numbers will vary; regenerate with
the command above**):

| Metric | Result |
|---|---|
| Rows in chain | 50,000 |
| Append throughput | ~36,000 rows/sec |
| Verify throughput (full chain) | ~74,000 rows/sec |
| Verify latency (full chain) | ~675 ms |
| Tamper detection | 200/200 corrupted rows caught (100.0%) |

## How it works

```
row.hash = SHA256( prev_hash || row.index || canonical_json(row.body) )
```

Each row folds in the previous row's hash. Editing any past row changes its hash, which
no longer matches what the next row recorded as its `prev_hash` — so a single silent edit
invalidates the whole chain from that point on. `verify()` recomputes every row from the
genesis anchor and returns the first row where stored and recomputed disagree.

- [`ledger.py`](./ledger.py) — the `Ledger` class: `append()`, `verify()`, append-only (no update/delete API).
- [`ledger_demo.py`](./ledger_demo.py) — the narrative runner above.
- [`test_ledger.py`](./test_ledger.py) — `unittest` suite, including the tamper cases.
- [`bench.py`](./bench.py) — the reproducible benchmark.

## What this proves — and what it does NOT

**Proves:** an append-only ledger with SHA-256 hash chaining is *tamper-evident* — any
after-the-fact edit, deletion, or reordering of committed history is detectable by
recomputation. This is a real, checkable property, demonstrated by code you can run.

**Does NOT prove / is NOT:** this is a **generic cryptographic primitive**, not the
BOSNet.io engine. It is not a full governance runtime; it does not police what a model
may do, retrieve evidence, or enforce policy — those live in the (proprietary) reference
implementation described in [`../BOSS-STANDARD.md`](../BOSS-STANDARD.md). Tamper-*evidence*
is not tamper-*prevention*: a chain detects alteration, it does not stop someone with
write access from altering storage (append-only storage + off-site anchoring are the
operational complements). The case-study "after" figures elsewhere in this repo remain
**labeled estimates**, except Relic Wars.

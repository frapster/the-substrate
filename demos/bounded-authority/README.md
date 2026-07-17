# demo — a runnable, deny-by-default policy gate

A small, **zero-dependency** proof of one claim `the-substrate` makes in prose: that an
agent's authority is bounded to a registered, closed surface, and that an over-scoped
action is refused *before* it executes (see [`../../README.md`](../../README.md),
[`../../BOSS-STANDARD.md`](../../BOSS-STANDARD.md), and
[`../../docs/adr/ADR-0002-deny-by-default-roster.md`](../../docs/adr/ADR-0002-deny-by-default-roster.md)).

You should be able to clone the repo and see it work in under a minute. No `pip install`,
no build — Python 3 standard library only.

## Quickstart (30 seconds)

```bash
python demos/bounded-authority/gate_demo.py
```

You'll watch a governance directory register a closed roster of actions with blast-radius
caps, a within-budget action proceed, and then a proposal to delete 10,000 rows against
a policy capped at 100 get refused before a single row is touched:

```
3. A model proposes deleting 10,000 rows
  Policy caps 'delete_rows' at a hard ceiling of 100 rows.
  propose('delete_rows', {'max_rows': 10000})
  ✗ BLOCKED  'delete_rows' requested max_rows=10,000 exceeds hard ceiling 100 (tier=red)
  Zero rows were touched. The refusal happened before execution, not after.
```

That refusal — happening in code, before anything runs — is the whole point.

## Run the tests

The negative tests are the interesting ones: they assert `propose()` *refuses*, for the
right reason, when an action is unregistered, over its hard ceiling, over its soft cap,
or has no readable policy at all.

```bash
python demos/bounded-authority/test_gate.py
# or:  python -m unittest discover -s demos/bounded-authority
```

## Run the benchmark

Measured numbers, not adjectives. This benchmarks the gate primitive's throughput and
refusal completeness — not end-to-end governance, and not model quality.

```bash
python demos/bounded-authority/bench.py            # default K = 500 proposals
python demos/bounded-authority/bench.py 2000        # custom proposal count
```

Sample run (Python 3.13, a 2020-class laptop — **your numbers will vary; regenerate with
the command above**):

| Metric | Result |
|---|---|
| Proposals evaluated | 500 |
| Proposal throughput | ~155,000 decisions/sec |
| proceed | 189 |
| escalated | 63 |
| blocked | 248 |
| Over-scoped/unregistered proposals blocked | 248/248 |

## How it works

```
propose(action, scope) → proceed | escalated | blocked   — decided BEFORE execution
```

Every action must first be registered on a closed roster with a risk tier
(yellow → orange → red → purple) and blast-radius caps: a soft cap that triggers
escalation, and a hard ceiling nothing may exceed. `propose()` checks a candidate
action against that roster and fails closed at every step: not on the roster →
blocked ("omission is prohibition"); registered but no readable ceiling → blocked;
over the hard ceiling → blocked; over the soft cap → escalated for a human; within
caps → proceed.

- [`gate.py`](./gate.py) — the `Gate` class: `register()`, `propose()`, the `Decision` dataclass.
- [`gate_demo.py`](./gate_demo.py) — the narrative runner above.
- [`test_gate.py`](./test_gate.py) — `unittest` suite, including the refusal cases.
- [`bench.py`](./bench.py) — the reproducible benchmark.

## What this proves — and what it does NOT

**Proves:** a closed roster with hard/soft blast-radius caps is *deny-by-default* — an
action that was never registered, or a registered action requested past its ceiling, is
refused before execution, not after. This is a real, checkable property, demonstrated by
code you can run.

**Does NOT prove / is NOT:** this is a **generic authorization primitive**, not the
BOSNet.io engine. It is not a full governance runtime; it does not resolve identity,
retrieve evidence, or record decisions to a ledger — those live in the (proprietary,
patent-pending) reference implementation described in
[`../../BOSS-STANDARD.md`](../../BOSS-STANDARD.md) and reserved under
[`../../LICENSE.md`](../../LICENSE.md). A closed roster bounds *what* may be proposed;
it does not by itself prove *correctness* of a permitted action, and it is not the kernel
or spec. The case-study "after" figures elsewhere in this repo remain **labeled
estimates**, except Relic Wars.

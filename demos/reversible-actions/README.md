# demo: a runnable, gated and reversible versioned store

A small, **zero-dependency** proof of one claim `the-substrate` makes in prose: that a
governance engine treats high-impact actions as *gated, versioned, and recoverable* (see
[`../../BOSS-STANDARD.md`](../../BOSS-STANDARD.md), which lists **Reversible** (defined as
"High-impact actions are gated, versioned, and recoverable") as one of the four governance surfaces
alongside Bounded, Evidence-backed, and Audited).

You should be able to clone the repo and see it work in under a minute. No `pip install`,
no build. Python 3 standard library only.

## Quickstart (30 seconds)

```bash
python demos/reversible-actions/reversible_demo.py
```

You'll watch a few gated changes supersede forward as new versions, an ungated
high-impact action get refused outright, two attempts to edit history in place fail
closed, and a `restore()` recover a prior state whose hash matches the original
snapshot byte-for-byte:

```
4. Recovering a prior state
  [apply]  version 4  hash=fbf898a3…  state={'balance_usd': 100, 'status': 'flagged', 'tier': 'platinum'}
  Recovering to version 3 (hash=447b9580…)…
  [restore]  version 5  hash=447b9580…  state={'balance_usd': 100, 'status': 'verified', 'tier': 'gold'}
  ✓ restored state_hash matches version 3 exactly, byte-for-byte.
```

That last moment, recovery reproducing the *exact* prior state byte-for-byte,
is the whole point.

## Run the tests

The negative tests are the interesting ones: they assert that in-place mutation **fails
closed**, that an ungated high-impact action is **refused**, and that a version tampered
with directly (bypassing the guard) is caught by `verify_chain()`.

```bash
python demos/reversible-actions/test_reversible.py
# or:  python -m unittest discover -s demos/reversible-actions
```

## How it works

The faithful mechanism is **append-only + supersede-forward + a gated destructive path**:
this demo deliberately does **not** implement a literal stored-inverse "undo". Nothing
committed is ever edited or removed; the store only ever grows forward.

```
apply(change)      → appends a NEW version = current state merged with change
restore(version=N) → appends a NEW version equal to version N's state
```

- **`apply()`** is the only sanctioned mutation. It supersedes forward: the predecessor
  version is untouched, and its `state_hash = SHA256(canonical_json(state))` stays valid
  forever.
- **High-impact actions are gated.** `apply(change, high_impact=True)` without
  `gated=True` (an approval token, standing in for a HITL approval) raises
  `UngatedHighImpactError` and never touches the chain.
- **In-place mutation fails closed.** `_update_in_place()` and `_delete_in_place()` model
  the durable append-only guard: they exist only to prove that reaching past `apply()` /
  `restore()` is refused unconditionally, every time.
- **`restore(N)` is recovery, not rewind.** It reconstructs a prior state by appending a
  new version equal to it, so `store.state_hash == snapshot_at(N)` exactly. Reversibility
  here means the same restore call always reproduces the same state: it is deterministic.
- **`operator_destructive()`** is a reserved path for genuinely destructive recovery
  (e.g. a full purge). It is explicitly marked and writes its own audit note: even
  destructive action is recorded as a new version, never as a silent in-place erasure.
- **`verify_chain()`** recomputes every version's `state_hash` from its stored state and
  reports the first version where stored and recomputed disagree, the same shape as the
  audit ledger's `verify()`.

- [`reversible.py`](./reversible.py): the `Store` class: `apply()`, `restore()`,
  `operator_destructive()`, `verify_chain()`, append-only guard.
- [`reversible_demo.py`](./reversible_demo.py): the narrative runner above.
- [`test_reversible.py`](./test_reversible.py): `unittest` suite, including the guard
  and refusal cases.

## What this proves, and what it does not

**Proves:** an append-only, versioned store with supersede-forward mutation makes
recovery *deterministic*: `restore(N)` reproduces a prior state's hash exactly, and
that gating an ungated high-impact action, or an attempt to mutate history in place, is
refused every time. This is a real, checkable property, demonstrated
by code you can run.

**Does NOT prove / is NOT:** this is a **generic state-versioning primitive**, distinct
from the BOSNet.io engine, kernel, or spec (patent-pending, reserved). It does not implement HITL
approval flows, real authorization tokens, or the blast-radius policy that decides what
counts as "high-impact": those live in the (proprietary) reference implementation
described in [`../../BOSS-STANDARD.md`](../../BOSS-STANDARD.md). This demo does not
implement literal stored-inverse undo; recovery is restore-to-a-prior-version by
supersede-forward, which is the faithful shape of the real mechanism. Never implies an
open-source grant of BOSNet.io or BOSS: see [`../../LICENSE.md`](../../LICENSE.md). The
case-study "after" figures elsewhere in this repo remain **labeled estimates**, except
Relic Wars.

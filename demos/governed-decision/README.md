# governed-decision: the whole loop in one runnable file

> **Try it in your browser** (no install): [interactive governed-decision demo](../interactive/governed-decision.html). The interactive version mirrors this Python; it is the convenience, and the code here is the proof.

The flagship demo. One intent flows through **all four BOSS guarantees** end to end:
**bounded** gate → **evidence** check → deterministic **validator** → **audited**
hash-chained ledger → **reversible** commit, and each stage can refuse its own bad input
in isolation.

The other demos each prove one primitive. This one shows how they compose: the substrate
is a **pipeline of deterministic checkpoints wrapped around a single probabilistic step**.

## Quickstart (30 seconds)

```bash
python demos/governed-decision/governed_decision_demo.py
```

You'll watch a well-formed intent pass the full loop: commit, prove reversible (restored
to its exact prior state hash), with the audit chain still intact, and then watch four
broken intents each get refused at the stage that owns the broken check:

```
2. Each stage refuses its own failure, in isolation
  ✗ over-scope           refused at bounded   rows=10000 exceeds hard cap 100 …
  ✗ unsourced claim      refused at evidence  claim carries no resolvable source …
  ✗ invalid proposal     refused at validated proposal missing required field(s) …
  ✗ unregistered action  refused at bounded   action 'wire_transfer' is not on the roster …
```

Nothing partial leaks: a refused intent leaves no row in the ledger and no new version in
the store.

## Run the tests

```bash
python demos/governed-decision/test_pipeline.py
# or:  python -m unittest discover -s demos/governed-decision
```

The negative tests are the interesting ones: each asserts an intent broken in exactly one
way is refused at exactly the right stage, and that a refusal leaves the ledger and the
versioned store untouched.

## How it works

Five minimal, self-contained stages, composed by `Substrate.decide(intent)`:

| Stage | Guarantee | What it enforces | Fuller proof |
|---|---|---|---|
| `BoundedGate` | Bounded | closed roster + blast-radius caps; deny-by-default | [`../bounded-authority/`](../bounded-authority/) |
| `EvidenceStore` | Evidence-backed | a claim must resolve to a hashed source | [`../evidence-provenance/`](../evidence-provenance/) |
| `DeterministicValidator` | *(the recurring shape)* | commit only what passes; discard, don't patch | [`../deterministic-validator/`](../deterministic-validator/) |
| `AuditLedger` | Audited | hash-chained, tamper-evident record | [`../audit-ledger/`](../audit-ledger/) |
| `ReversibleStore` | Reversible | append-only, supersede-forward, exact restore | [`../reversible-actions/`](../reversible-actions/) |

Each stage here is a deliberately small reimplementation of the mechanism its sibling demo
proves in full, so this folder runs standalone with **no cross-folder imports**. Any stage
may raise a `GovernanceRefusal`; the loop stops and nothing commits.

## What this proves, and what it does not

**Proves:** the four guarantees compose into a single decision path where the one
probabilistic step (the model's proposed record) is wrapped, before and after, by
deterministic checkpoints, and a failure of any one guarantee refuses the whole decision
at a nameable stage, with no partial commit. It is the *shape* of a governed decision made
runnable.

**Does NOT prove / is NOT:** this is a **generic illustration**, distinct from the BOSNet.io engine.
Each stage is a toy: the real gate, evidence model, validator, ledger, and reversibility
machinery are the proprietary reference implementation described in
[`../../BOSS-STANDARD.md`](../../BOSS-STANDARD.md). The machine-checkable specification and
governance kernel are patent-pending and reserved (see [`../../LICENSE.md`](../../LICENSE.md)).
The five stages are simplified to compose in one readable file; the sibling demos are the
stronger single-property proofs (tamper-evidence benchmark, fair RAG contrast, append-only
guard, and so on).

# demos — a runnable proof per guarantee

`the-substrate` makes claims in prose. This folder makes them **runnable**. Each subfolder proves
**one** published claim with code a stranger can clone and run in under a minute — Python 3 standard
library only, no `pip install`, no build.

Every demo is built to the same five-part spec that made the original ledger demo work:

1. **Proves exactly one claim** — not the whole engine.
2. **Shows a failure being caught** — the drama is watching the system say *no* correctly.
3. **Zero dependencies, <60 seconds** — stdlib only, `git clone && run`.
4. **A headline number** — a measured or counted result, not an adjective.
5. **Honest about what it does not prove** — each README spells out the boundary.

The unifying genre is the **refusal**. A governed system is defined by what it declines to do: the
ledger refuses silent edits, the gate refuses over-scope, evidence refuses unsourced claims, the
validator refuses to patch a bad proposal. "Watch it say no correctly" is the whole point — it is
exactly what separates *governance* from *capability*.

## The suite

| Demo | Guarantee / claim | ADR | The refusal it dramatizes |
|---|---|---|---|
| [`audit-ledger/`](./audit-ledger/) | **Audited** | [0001](../docs/adr/ADR-0001-hash-chained-audit-ledger.md) | a silent edit to committed history is caught by recomputation |
| [`bounded-authority/`](./bounded-authority/) | **Bounded** | [0002](../docs/adr/ADR-0002-deny-by-default-roster.md) | an over-scoped or unregistered action is blocked before it runs |
| [`evidence-provenance/`](./evidence-provenance/) | **Evidence-backed** | [0005](../docs/adr/ADR-0005-rag-is-not-the-substrate.md) | an unsourced claim is refused; editing a source auto-detaches its claim |
| [`governed-knowledge/`](./governed-knowledge/) | **Knowledge** | [0005](../docs/adr/ADR-0005-rag-is-not-the-substrate.md) | naive cosine returns a stale atom; governed retrieval returns the current one — or abstains |
| [`reversible-actions/`](./reversible-actions/) | **Reversible** | — | an in-place mutation fails closed; `restore()` reproduces the exact prior state |
| [`deterministic-validator/`](./deterministic-validator/) | **Validated** | [0003](../docs/adr/ADR-0003-deterministic-validator-commits.md) | an invalid proposal is discarded, not patched into a passing one |
| [`ai-code-ratio/`](./ai-code-ratio/) | **90:10 AI\:code** | thesis | new requirements cost *facts*, not code branches — counted from source |
| [`governed-decision/`](./governed-decision/) | **the whole loop** | 0001–0005 | one intent through all four guarantees; each stage refuses its own failure |

## Run everything

Each demo runs on its own (`python demos/<name>/<name>_demo.py`). To run every test suite at once:

```bash
python demos/run_tests.py
```

## What these prove — and what they do NOT

**Prove:** individually checkable properties — tamper-evidence, deny-by-default bounding, evidence
provenance, governed-vs-similarity retrieval, deterministic reversibility, checked (never trusted)
model proposals — demonstrated by code you can run, including the negative cases where each one
correctly fails.

**Do NOT prove / are NOT:** these are **generic primitives and honest toys**, not the BOSNet.io
engine. Each is grounded in a real mechanism from the proprietary reference implementation, but
reproduces none of it: no real schema, no coordinate scheme, no kernel or compiler, no client data —
invented names throughout. The machine-checkable specification and governance kernel are
patent-pending and reserved. See [`../BOSS-STANDARD.md`](../BOSS-STANDARD.md) for the standard's
shape and [`../LICENSE.md`](../LICENSE.md) for the IP boundary. Each subfolder's README states its own
precise limits.

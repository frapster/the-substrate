# the-substrate

**AI as the governed operational substrate.**

> The logic layer of code is the traditional way of capturing and executing the reasoning
> process, highly constrained and deterministic. My approach unleashes *reasoning* as part of
> the logic layer in the codebase, using a **governance engine** that makes it safe to let AI do
> things we've traditionally only trusted code to do, until today. **This is AI as the operational substrate.**
>
> Robert J. Floyd

This repo is the public thesis showcase for that idea, and it ships a **small, runnable
proof** of its most concrete claim: a tamper-evident audit ledger you can watch catch a
forged decision, in under a minute, with no dependencies.

---

## Quickstart (30 seconds)

The thesis says every governed decision writes a *hash-chained, tamper-evident ledger
entry*. Here it is as running code. Python 3 standard library only, nothing to install:

```bash
git clone https://github.com/frapster/the-substrate && cd the-substrate
python demos/audit-ledger/ledger_demo.py
```

You'll watch decisions get committed to an append-only chain, verify as intact, and then,
after an attacker silently edits one *past* decision, watch `verify()` pinpoint the exact
broken row:

```
  ✗ CHAIN BROKEN at row 2
    row 2 recomputed hash 86d17a4f… != stored 813c6b22… (body was altered)
```

That's the whole point: silent edits to history are impossible. See [`demos/audit-ledger/`](./demos/audit-ledger/)
for the code, the tests (including the tamper cases), and a reproducible benchmark
(~74,000 rows/sec verify, 200/200 tampers caught). What it proves, and deliberately does
**not**, is spelled out in [`demos/audit-ledger/README.md`](./demos/audit-ledger/README.md) and the
[Limitations](#limitations-what-this-does-and-does-not-do) section below.

The ledger is one of a **suite** of runnable proofs, one per guarantee, each dramatizing a
governed *refusal* you can watch happen in code. See [Runnable proofs](#runnable-proofs) below.

---

## Runnable proofs

Each demo in [`demos/`](./demos/) proves **one** published claim, in under a minute, with no
dependencies (Python 3 standard library only). Every one is grounded in a real mechanism from the
proprietary engine but ships only a clean-room toy, and every one dramatizes a *refusal*: watch
it say **no** correctly, which is exactly what separates governance from capability.

Each also has an **interactive browser version** (no install) where you can drive the inputs and
watch the refusal happen live. The interactive version is the convenience; the Python you rerun is
the proof, and every interactive page shows you how to run and extend the real tests. Start at the
[interactive demos suite](./demos/interactive/index.html).

| Demo | Guarantee / claim | The refusal you watch | Try it |
|---|---|---|---|
| [`demos/audit-ledger/`](./demos/audit-ledger/) | **Audited** (ADR-0001) | a silent edit to committed history is caught by recomputation | [browser](./demos/interactive/audit-ledger.html) |
| [`demos/bounded-authority/`](./demos/bounded-authority/) | **Bounded** (ADR-0002) | an over-scoped or unregistered action is blocked *before* it runs | [browser](./demos/interactive/bounded-authority.html) |
| [`demos/evidence-provenance/`](./demos/evidence-provenance/) | **Evidence-backed** (ADR-0005) | an unsourced claim is refused; editing a source auto-detaches its claim | [browser](./demos/interactive/evidence-provenance.html) |
| [`demos/governed-knowledge/`](./demos/governed-knowledge/) | **Knowledge** (ADR-0005) | naive cosine returns a stale atom; governed retrieval returns the current one, or abstains | [browser](./demos/interactive/governed-knowledge.html) |
| [`demos/reversible-actions/`](./demos/reversible-actions/) | **Reversible** | an in-place mutation fails closed; `restore()` reproduces the exact prior state | [browser](./demos/interactive/reversible-actions.html) |
| [`demos/deterministic-validator/`](./demos/deterministic-validator/) | **Validated** (ADR-0003) | an invalid proposal is discarded, never patched into a passing one | [browser](./demos/interactive/deterministic-validator.html) |
| [`demos/ai-code-ratio/`](./demos/ai-code-ratio/) | **90:10 AI\:code** | new requirements cost *facts* rather than code branches, counted from source | [browser](./demos/interactive/ai-code-ratio.html) |
| [`demos/governed-decision/`](./demos/governed-decision/) | **the whole loop** | one intent through all four guarantees; each stage refuses its own failure | [browser](./demos/interactive/governed-decision.html) |

Run the whole suite's tests at once:

```bash
python demos/run_tests.py
```

_The interactive pages are static HTML with no dependencies; they run once the repo is served
(GitHub Pages, or any static host) and also open directly from a local file. They mirror the Python
byte-for-byte, but treat them as an illustration and prove the claims with the Python yourself._

What each proves, and deliberately does **not**, is stated in its own README and summarized in
[Limitations](#limitations-what-this-does-and-does-not-do) below.

---

## The idea, precisely

Code has always been a reasoning layer. It's just reasoning that's been *frozen at write-time*.
Every `if`, every validation rule, every branch is a human's reasoning, pre-committed into
deterministic control flow.

The work described in this repo moves some (or a lot) of that reasoning from **write-time to run-time**: letting AI reason inside
the logic layer where code used to sit. That's normally reckless, because probabilistic reasoning
is unbounded and unauditable. **The governance engine is what makes run-time reasoning safe enough
to be load-bearing**: bounded, evidence-backed, audited, reversible.

That is the difference between "we call an LLM somewhere" and **AI as the operational substrate**.

- **Bounded**: reasoning runs inside explicit policy, permissions, and blast-radius limits.
- **Evidence-backed**: facts trace to hashed source evidence; nothing is asserted without provenance.
- **Audited**: every decision writes a hash-chained, tamper-evident ledger entry.
- **Reversible**: high-impact actions are gated, versioned, and recoverable.

But governance is only half of it. The operational substrate of an LLM is **governance *plus* knowledge**,
not code: what the model may *do*, and what it correctly *knows*. A governed model fed the wrong or
missing context still fails, which is why retrieval-by-similarity (RAG) does not carry governed
knowledge on its own (see [`ENGINEERING.md`](./ENGINEERING.md)).

And it begins with people. Governing AI starts by governing intent and context, with **safe, governed
tools that free the operator** ("the builder becomes the architect of the
builder's constraints"). The argument is in [`THESIS.md`](./THESIS.md); the evidence, and its honest
limits, in [`ENGINEERING.md`](./ENGINEERING.md).

The measurable spine across projects is the **AI : code ratio**: how much governed run-time
reasoning carries operational behavior versus hand-authored code, and where that trade is (and isn't)
worth it. The **LLM-First** target is **90 : 10**. The full argument, including total cost of
ownership, the quality/security of LLM-authored code, and what it takes to govern a model inside a
harness you don't own, is in [`THESIS.md`](./THESIS.md) and [`ENGINEERING.md`](./ENGINEERING.md).

## The standard: BOSNet.io

**BOSNet.io** is the governance infrastructure that makes the above safe: a matrix-first,
evidence-and-audit-backed model with deterministic policy before and after every model call.
It is the named standard these case studies build on.

> BOSNet.io and the Bounded Open Safety Standard (BOSS) are proprietary. See
> [`LICENSE.md`](./LICENSE.md).

**BOSS**, the Bounded Open Safety Standard, is presented publicly at the level a technical evaluator
needs (principles, the four guarantees, and the *governance directory* a governed system publishes) in
[`BOSS-STANDARD.md`](./BOSS-STANDARD.md). The machine-checkable specification and kernel are
patent-pending and reserved.

## Case studies

Each is a **before → after** transformation of one system: what it is today, and what governed
conversion toward the LLM-First **90 : 10** target does to it. Relic Wars is the one conversion that has
actually shipped (factual); the others are planned, with figures shown as **labeled estimates**.

| Project | Transformation | AI : code (before → after) | Status |
|---|---|---|---|
| **[Relic Wars](./case-studies/relic-wars.md)** | A ~2,350-line rules engine retired for a fact matrix plus prompt plus deterministic auditor; the proof case (and the algorithmic contrast case) | ~0:100 → **~85:15** (adjudication) | **Converted · factual** |
| **[Today Series](./case-studies/today-series.md)** | Study-content platform; language-and-judgment work can go furthest toward LLM-First via blueprint-compiled reasoning | ~35:65 → **~85-90:10-15** | Planned · estimate |
| **[Zabble](./case-studies/zabble.md)** | Live social platform; reasoning expands at judgment seams while payments and real-time safety stay deterministic, the ceiling case | ~8:92 → **~30-40:60-70** | Planned · estimate |
| **[Eikon Digital](./case-studies/eikon-digital.md)** | ~350k-line web app rebuilt as a full BOSNet.io tenant, the operating model of a whole system, the largest delta | ~12:88 → **~80-85:15-20** | Planned · estimate |
| **app.bosnet.io** | The governance standard the conversions target: reasoning as the operational core, carried well past a single fenced seam | **~90:10** | Proprietary · no write-up |

The cross-cutting engineering threads these studies share, **total cost of ownership**, the
**quality and security of LLM-authored code**, **cooperative governance inside a third-party harness**,
and the **drift** the model fights against, are treated in [`ENGINEERING.md`](./ENGINEERING.md).

_Writeups are added deliberately and reviewed for IP safety before publishing._

## Also in this repo

Every root document has a **visual explainer** companion in [`visuals/`](./visuals/):

| Document | Visual explainer |
|---|---|
| [`THESIS.md`](./THESIS.md), the core argument | [`visuals/thesis.html`](./visuals/thesis.html) |
| [`ENGINEERING.md`](./ENGINEERING.md), TCO, LLM-code quality/security, harness governance, drift | [`visuals/engineering.html`](./visuals/engineering.html) |
| [`BOSS-STANDARD.md`](./BOSS-STANDARD.md), the Bounded Open Safety Standard plus governance directory | [`visuals/boss-standard.html`](./visuals/boss-standard.html) |
| [`GOVERNING-PEOPLE.md`](./GOVERNING-PEOPLE.md), governing AI begins with governing people | [`visuals/governing-people.html`](./visuals/governing-people.html) |
| _Architecture decisions_, cross-project architectural judgment (visual-only) | [`visuals/architecture-decisions.html`](./visuals/architecture-decisions.html) |
| [Résumé](./resume/robert-floyd.html), experience, skills, signature work | the résumé itself |

The four **case-study** before/after explainers live in [`case-studies/visuals/`](./case-studies/visuals/).

The engineering record, runnable proof, decisions, and changes:

| Artifact | What it is |
|---|---|
| [`demos/`](./demos/) | A suite of runnable, zero-dependency proofs, one per guarantee (see [Runnable proofs](#runnable-proofs)) |
| [`docs/adr/`](./docs/adr/) | Architecture Decision Records: why hash-chaining, deny-by-default, private engine, and what was rejected |
| [`CHANGELOG.md`](./CHANGELOG.md) | What has shipped, and the near-term roadmap |

## Limitations: what this does and does NOT do

Stating limits plainly is part of the point; a governance thesis that hid its own boundaries
would be self-refuting.

- **The runnable demos are primitives.** [`demos/`](./demos/) proves individual
  properties: tamper-evidence, deny-by-default bounding, evidence provenance, governed versus
  similarity retrieval, reversibility, deterministic validation, with code a stranger can run.
  Each is a generic building block or an honest toy. Together they are **not** BOSNet.io and not a
  full governance runtime; the real gate, evidence model, validator, ledger, and knowledge
  substrate live in the proprietary reference implementation ([`BOSS-STANDARD.md`](./BOSS-STANDARD.md)).
  Each demo's README states precisely what it does and does not prove.
- **Tamper-*evidence* detects alteration; it does not prevent it.** The chain catches any edit by
  recomputation. It does not stop someone with storage access from altering bytes. Append-only
  storage and off-site anchoring are the operational complements, out of scope for the demo.
- **Most case-study numbers are labeled estimates.** Only **Relic Wars** is a shipped,
  measured conversion. Today Series, Zabble, and Eikon Digital "after" figures are projections,
  marked as such. The **90:10** LLM-First target is a design aspiration; no shipped system has
  measured it yet (see [`ENGINEERING.md`](./ENGINEERING.md) §6, "Objections we take seriously").
- **BOSS is published as an overview.** The machine-checkable specification, conformance rule
  set, and kernel are patent-pending and reserved. This repo evaluates the *shape* of the
  standard, not its normative internals.

## Why not Microsoft's Agent Governance Toolkit / DeepEval?

Because they solve adjacent problems, and the honest posture is to **interoperate with them**.
Eval frameworks (DeepEval) measure *model output quality*; agent-governance
toolkits (Microsoft's, covering the OWASP Agentic Top 10) harden *what an agent is allowed to
do*. Both complement the contribution here rather than compete with it, which is a
**published governance directory plus a tamper-evident decision ledger**: a verifiable,
outside-readable record of *how* a system is governed and an audit trail that a regulator or
auditor can check without source access ([`BOSS-STANDARD.md`](./BOSS-STANDARD.md) §3). A
governed system can run DeepEval at its output-safety gate and register its evals as evidence
sources in its directory. The gap this fills is *auditable governance*, distinct from evaluation.

## Scope

- **What it is:** a public thesis and case-study showcase for technical evaluators: architecture, patterns,
  and results, framed around governed run-time reasoning.
- **What it stays out of:** the BOSNet.io source, and client IP. Anything proprietary or client-owned stays
  out by design.

---

*Author: Robert J. Floyd, founder/CEO, Eikon Digital Solutions · [robfloyd.me](https://robfloyd.me)*

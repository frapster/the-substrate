# the-substrate

**AI as the governed operational substrate.**

> The logic layer of code is the traditional way of capturing and executing the reasoning
> process — highly constrained and deterministic. My approach unleashes *reasoning* as part of
> the logic layer in the codebase, using a **governance engine** that makes it safe to let AI do
> things we've traditionally relied on code to do. **This is AI as the operational substrate.**
>
> — Robert J. Floyd

---

## The idea, precisely

Code has always been a reasoning layer — it's just reasoning that's been *frozen at write-time*.
Every `if`, every validation rule, every branch is a human's reasoning, pre-committed into
deterministic control flow.

This work moves some of that reasoning from **write-time to run-time**: letting AI reason inside
the logic layer where code used to sit. That's normally reckless, because probabilistic reasoning
is unbounded and unauditable. **The governance engine is what makes run-time reasoning safe enough
to be load-bearing** — bounded, evidence-backed, audited, reversible.

That is the difference between "we call an LLM somewhere" and **AI as the operational substrate**.

- **Bounded** — reasoning runs inside explicit policy, permissions, and blast-radius limits.
- **Evidence-backed** — facts trace to hashed source evidence; nothing is asserted without provenance.
- **Audited** — every decision writes a hash-chained, tamper-evident ledger entry.
- **Reversible** — high-impact actions are gated, versioned, and recoverable.

The measurable spine across projects is the **AI : code ratio** — how much governed run-time
reasoning carries operational behavior versus hand-authored code, and where that trade is (and isn't)
worth it. The **LLM-First** target is **90 : 10**. The full argument — including total cost of
ownership, the quality/security of LLM-authored code, and what it takes to govern a model inside a
harness you don't own — is in [`THESIS.md`](./THESIS.md) and [`ENGINEERING.md`](./ENGINEERING.md).

## The standard: BOSNet.io

**BOSNet.io** is the governance infrastructure that makes the above safe: a matrix-first,
evidence-and-audit-backed model with deterministic policy before and after every model call.
It is the named standard these case studies build on.

> BOSNet.io, BOSGov, and the Bounded Open Safety Standard (BOSS) are proprietary. See
> [`LICENSE.md`](./LICENSE.md).

## Case studies

Each is a **before → after** transformation of one system: what it is today, and what governed
conversion toward the LLM-First **90 : 10** target does to it. Relic Wars is the one conversion that has
actually shipped (factual); the others are planned, with figures shown as **labeled estimates**.

| Project | Transformation | AI : code (before → after) | Status |
|---|---|---|---|
| **[Relic Wars](./case-studies/relic-wars.md)** | A ~2,350-line rules engine retired for a fact matrix + prompt + deterministic auditor; the proof case (and the algorithmic contrast case) | ~0:100 → **~85:15** (adjudication) | **Converted · factual** |
| **[Today Series](./case-studies/today-series.md)** | Study-content platform; language-and-judgment work can go furthest toward LLM-First via blueprint-compiled reasoning | ~35:65 → **~85–90:10–15** | Planned · estimate |
| **[Zabble](./case-studies/zabble.md)** | Live social platform; reasoning expands at judgment seams but payments + real-time safety stay deterministic — the ceiling case | ~8:92 → **~30–40:60–70** | Planned · estimate |
| **[Eikon Digital](./case-studies/eikon-digital.md)** | ~350k-line web app rebuilt as a full BOSNet.io tenant — the operating model of a whole system, the largest delta | ~12:88 → **~80–85:15–20** | Planned · estimate |
| **app.bosnet.io** | The governance standard the conversions target — reasoning as the operational core, not a fenced seam | **~90:10** | Proprietary · no write-up |

The cross-cutting engineering threads these studies share — **total cost of ownership**, the
**quality and security of LLM-authored code**, **cooperative governance inside a third-party harness**,
and the **drift** the model fights against — are treated in [`ENGINEERING.md`](./ENGINEERING.md).

_Writeups are added deliberately and reviewed for IP safety before publishing._

## What this repo is (and isn't)

- **Is:** a public thesis + case-study showcase for technical evaluators — architecture, patterns,
  and results, framed around governed run-time reasoning.
- **Isn't:** the BOSNet.io source, and never client IP. Anything proprietary or client-owned stays
  out by design.

---

*Author: Robert J. Floyd — founder/CEO, Eikon Digital Solutions · [robfloyd.me](https://robfloyd.me)*

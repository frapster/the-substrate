# BOSS — the Bounded Open Safety Standard

**A governance standard for agentic AI, organized around a published *governance directory*.**

**Author: Robert J. Floyd** — founder/CEO, Eikon Digital Solutions · [robfloyd.me](https://robfloyd.me)

**Visual:** [visual explainer](./visuals/boss-standard.html) · **Related:** [Thesis](./THESIS.md) · [Engineering](./ENGINEERING.md) · [README](./README.md)
**Status:** Public overview. The machine-checkable specification, conformance rule set, and reference
kernel are **patent-pending and reserved** — see [Reserved material](#reserved-material) and
[`LICENSE.md`](./LICENSE.md).

> **Unbounded agents are ungoverned agents.** BOSS exists to make run-time AI reasoning safe enough to
> be *load-bearing* — bounded, evidence-backed, audited, and reversible.

---

## 1. What BOSS is

BOSS — the **Bounded Open Safety Standard** — is a governance specification for agentic AI. Its premise
is the thesis behind [`the-substrate`](./README.md): a model can reason inside the logic layer where
deterministic code used to sit, but *only* when that reasoning runs inside a governance engine that keeps
it bounded, evidence-backed, audited, and reversible. BOSS specifies the **governance surface** a system
must expose — not its transport, auth, deployment, or operations, which belong to the implementation
layer.

"Bounded" is used as a **formal property**, not a marketing word: bounded execution, bounded checking,
bounded authority. Every part of BOSS bounds something.

The standard is deliberately modeled on the shape of **Kubernetes, OAuth, and OpenTelemetry**: the
*specification* is commoditized and open to describe; the *implementation* is where value is captured.
The reference implementation and commercial engine is **BOSNet.io** (proprietary; see
[`THESIS.md`](./THESIS.md)).

## 2. The four guarantees

BOSS conformance rests on four properties that must hold **at the point where reasoning does real work**:

| Guarantee | What it requires | Failure mode it prevents |
|---|---|---|
| **Bounded** | Reasoning runs inside explicit policy, permissions, and blast-radius limits. | Unauthorized action; an agent doing something no one sanctioned. |
| **Evidence-backed** | Every fact traces to hashed source evidence; nothing is asserted without provenance. | Hallucinated facts entering the system of record. |
| **Audited** | Every decision writes a tamper-evident ledger entry — inputs, model, verdict. | "The AI did it and we can't say why." |
| **Reversible** | High-impact actions are gated, versioned, and recoverable. | Irreversible damage from a single bad inference. |

The recurring engineering shape: **deterministic code computes what *does* happen and grades the
reasoning; the model decides what *should* happen; a validator commits only what passes.** The model is
never trusted — it is *checked*; a rejected inference is discarded, not patched.

## 3. The governance directory

The heart of BOSS is a simple, auditable idea: **a governed system must publish *how* it is governed.**
That published, machine-readable record is its **governance directory** — the public face of its
governance surface, the artifact an outside party (an auditor, a regulator, a partner, a customer) can
read to discover, verify, and audit the system's governance without access to its source.

A BOSS governance directory enumerates seven things:

| # | Directory entry | Declares |
|---|---|---|
| 1 | **Policies & constraints** | The boundaries the system operates under — what is admissible, and the blast-radius limits on any single action. |
| 2 | **Controls & gates** | The enforcement checkpoints and human-in-the-loop approvals that must be passed before a high-impact action commits. |
| 3 | **Evidence sources** | The hashed, provenance-tracked sources that back every asserted fact — the basis of *evidence-backed*. |
| 4 | **Agent & tool roster** | Which agents and tools are registered, discoverable, and permitted. **Omission is prohibition** — nothing outside the roster may act. |
| 5 | **Audit surface** | Where the tamper-evident decision ledger lives and what each entry records (inputs, model, verdict). |
| 6 | **Reversibility guarantees** | Which actions are gated, versioned, and recoverable — and how they are rolled back. |
| 7 | **Conformance claim** | The BOSS conformance level the system asserts, and the evidence it offers for it (§4). |

The design principle is **discoverability over trust**: governance that lives only in prose, prompts, or
intentions cannot be verified. A governance directory turns "we govern our AI" into something an outside
party can *read and check* — the difference between a claim and a control.

Two rules give the directory its teeth:

- **Omission is prohibition.** If an agent, tool, evidence source, or action is not in the directory, it
  is not permitted. The directory is a closed roster, not a suggestion.
- **Declared, then enforced.** Every directory entry corresponds to an enforcement point in the running
  system. The directory is not documentation *about* governance — it is the *registration of* governance
  the engine enforces.

## 4. Conformance

BOSS conformance is a **ramp, not all-or-nothing** — an adoption path from minimum viable governance to
the full surface:

- **Level 1 — Foundation.** Phase discipline and mandatory human checkpoints. The system has a
  governance directory covering policies, a gate roster, and an audit surface.
- **Level 2 — Structured.** Adds deterministic, reproducible execution and machine-compiled governance —
  governance derived from a declared model rather than hand-written per feature.
- **Level 3 — Full.** The complete surface: an atomic, evidence-backed knowledge model; compiled
  governance; output-safety gates; and precise, checkable conformance.

Conformance is **demonstrated, not asserted.** A system proves it against criteria (and, where
applicable, test vectors) rather than self-certifying by checklist. The specific checkable rules are the
reserved part of the standard.

## 5. Scope & non-goals

**In scope:** the governance surface — phase discipline, human checkpoints, execution contracts, the
evidence-backed knowledge model, and the conformance criteria that make a governance directory
verifiable.

**Out of scope (by design):** transport, authentication, deployment, hosting, and operations. Like
OAuth or OpenTelemetry, BOSS governs a *surface*, not a stack. Those concerns belong to the
implementation layer (BOSNet.io) and to the host system.

## 6. Reserved material

The following are **patent-pending and proprietary to Robert J. Floyd / Eikon Digital Solutions, LLC**,
and are **not** disclosed or licensed by this overview:

- the machine-checkable **specification** (its phase/gate/execution/knowledge/output/conformance
  modules and their normative rules);
- the **conformance rule set** and test vectors;
- the **governance kernel / compiler** and its dimensional model, schema, and coordinate scheme; and
- the **reference implementation** (BOSNet.io).

This document publishes BOSS's *principles, guarantees, governance-directory structure, and conformance
intent* — enough to evaluate the standard and adopt its shape — without disclosing the reserved spec or
kernel. BOSNet.io and BOSS are proprietary; see [`LICENSE.md`](./LICENSE.md). Nothing here
grants a license to them.

---

*BOSS is presented here at the level a technical evaluator needs to judge the approach. The complete
specification is maintained privately and is available for evaluation under separate written agreement.*

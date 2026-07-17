# ADR-0005 — Retrieval-by-similarity is not the governed-knowledge substrate

- **Status:** Accepted
- **Date:** 2026-07-15
- **Deciders:** Robert J. Floyd
- **Runnable proof:** [`demos/governed-knowledge/`](../../demos/governed-knowledge/) — a fair-fight contrast where naive cosine similarity returns a stale atom and governed retrieval returns the current one, or abstains. See also [`demos/evidence-provenance/`](../../demos/evidence-provenance/).

## Context

Governance bounds what a model may *do*. But a governed model fed the wrong or missing context still
produces wrong outputs — safely authorized, faithfully audited, and incorrect. The operational
substrate of an LLM is therefore **governance *plus* knowledge**, not governance alone. The common
reflex is to equate "give the model knowledge" with "add vector-similarity RAG," and that reflex is
what this decision pushes back on. (Full argument in [`../../ENGINEERING.md`](../../ENGINEERING.md).)

## Decision

Naive retrieval-by-cosine-similarity is treated as a **useful retrieval tactic, not the substrate**
for governed knowledge. What a model correctly *knows* must rest on an evidence model where facts are
atomic, provenance-tracked (hashed to source), versioned, and reconciled — so that an asserted fact
can be traced to evidence and superseded when it changes, rather than merely being "the nearest
chunk by embedding distance." Retrieval feeds that model; it does not define it.

## Alternatives considered

- **Vector similarity as the knowledge layer.** Rejected as the substrate: nearest-neighbor chunks
  optimize for topical closeness, not truth, currency, or provenance; they surface plausible-adjacent
  passages and have documented faithfulness failures. Fine as *a* retriever, wrong as *the* source.
- **Fine-tuning knowledge into weights.** Rejected as the primary mechanism: it bakes facts in
  opaquely, can't be audited or cheaply superseded, and blurs the provenance the "evidence-backed"
  guarantee requires.
- **Hybrid retrieval (vector + full-text + graph) with no evidence model.** Better recall, but still
  not a substrate — it improves *finding* without giving facts identity, provenance, or versioning.

## Consequences

- **Positive:** keeps "evidence-backed" a real guarantee — facts trace to hashed sources and can be
  superseded, which is what makes the audit ledger's decisions meaningful rather than well-recorded
  guesses.
- **Cost:** building an evidence model is materially more work than dropping in a vector store; this
  is a deliberate trade of effort for auditability.
- **Boundary:** this ADR states the *principle*; the specific knowledge-model schema and coordinate
  scheme are reserved (see [ADR-0006](./ADR-0006-keep-reference-engine-private.md)).

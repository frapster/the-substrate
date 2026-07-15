# ADR-0003 — A deterministic validator commits only what passes

- **Status:** Accepted
- **Date:** 2026-07-15
- **Deciders:** Robert J. Floyd

## Context

Moving reasoning from write-time to run-time means a probabilistic model now proposes actions that
used to be fixed in code. A model's proposal cannot be trusted on its own — it can be wrong,
hallucinated, or out of policy. But we also don't want to give up the flexibility that made run-time
reasoning worth adopting. The question is where trust lives.

## Decision

The recurring shape is: **deterministic code computes what *does* happen and grades the reasoning;
the model decides what *should* happen; a deterministic validator commits only what passes.** The
model is never trusted — it is *checked*. A rejected inference is **discarded, not patched**: the
system does not silently repair a bad proposal into a passing one, because that would launder an
untrustworthy decision into the record.

## Alternatives considered

- **Trust the model's output directly.** Rejected: this is exactly the unbounded, unauditable
  behavior the thesis exists to prevent.
- **Model-checks-model (an LLM judge as the sole gate).** Useful as *evidence*, but rejected as the
  final commit gate: a probabilistic checker of a probabilistic proposer has no deterministic floor.
  An LLM judge can feed the validator; it cannot *be* the validator.
- **Auto-repair failing proposals.** Rejected: patching a rejected inference hides the failure and
  breaks the audit story ("what committed, and did it pass on its own?"). Discard and re-derive.

## Consequences

- **Positive:** the trust boundary is a deterministic, testable checkpoint. What commits is always
  something that passed an explicit check; what fails leaves a recorded, discarded trace.
- **Cost:** every judgment seam needs a real validator — writing good checks is the hard, honest
  work, and it bounds how far toward LLM-First a given system can go (see the Zabble case study).
- **Boundary:** the validator bounds *admissibility*, not *quality of intent*; garbage-in still
  requires the knowledge layer to be right (see [ADR-0005](./ADR-0005-rag-is-not-the-substrate.md)).

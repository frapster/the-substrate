# ADR-0004: Publish a governance directory (discoverability over trust)

- **Status:** Accepted
- **Date:** 2026-07-15
- **Deciders:** Robert J. Floyd

## Context

"We govern our AI" is a claim. An outside party (an auditor, a regulator, a partner, a customer)
cannot verify a claim that lives only in prose, prompts, or good intentions. Governance that cannot
be inspected is indistinguishable from governance that does not exist. The gap to close is between
*asserting* governance and offering something an outsider can *read and check* without source access.

## Decision

A governed system **publishes a governance directory**: a machine-readable record enumerating what
it is governed by: policies and constraints, controls and gates, evidence sources, the agent/tool
roster, the audit surface, reversibility guarantees, and its conformance claim. The design principle
is **discoverability over trust**. Two rules give the directory teeth: **omission is prohibition**
(see [ADR-0002](./ADR-0002-deny-by-default-roster.md)), and **declared, then enforced**, meaning every
directory entry corresponds to an enforcement point in the running system. The directory registers
governance rather than merely documenting it.

## Alternatives considered

- **Prose/policy docs describing governance.** Rejected as the interface: not machine-checkable, and
  free to drift from what actually runs. Docs explain; the directory is a control.
- **Full source disclosure for verification.** Rejected: it conflates *evaluating governance* with
  *exposing the engine*. The directory lets an outsider verify the governance surface without access
  to the reserved implementation (see [ADR-0006](./ADR-0006-keep-reference-engine-private.md)).
- **Self-certification by checklist.** Rejected: conformance is demonstrated against criteria and
  test vectors, not asserted. A checklist is a claim; a directory backed by enforcement is evidence.

## Consequences

- **Positive:** turns "we govern our AI" into an inspectable artifact; models the proven shape of
  Kubernetes / OAuth / OpenTelemetry (open, describable *surface*; proprietary *implementation*).
- **Cost:** the directory must stay synchronized with enforcement. That maintenance obligation is the
  reason "declared, then enforced" is a rule rather than a convention.
- **Boundary:** this ADR commits to *publishing* the directory's structure and intent; the normative
  conformance rule set and test vectors are reserved (see [`../../BOSS-STANDARD.md`](../../BOSS-STANDARD.md) §6).

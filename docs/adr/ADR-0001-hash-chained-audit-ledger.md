# ADR-0001: Append-only, hash-chained audit ledger

- **Status:** Accepted
- **Date:** 2026-07-15
- **Deciders:** Robert J. Floyd
- **Runnable proof:** [`demos/audit-ledger/`](../../demos/audit-ledger/): a clean-room implementation of this decision.

## Context

When a model reasons inside the logic layer where deterministic code used to sit, "the AI did
it and we can't say why" becomes an unacceptable failure mode. A governed system must be able to
answer, after the fact and to a skeptical outside party (an auditor, a regulator, a customer),
*what was decided, on what inputs, by which model, and whether the record has been altered since*.
That requires an audit trail whose integrity does not depend on trusting the operator, the
database admin, or the application code that wrote it.

## Decision

Every governed decision is written to an **append-only, SHA-256 hash-chained ledger**. Each entry
folds the previous entry's hash into its own digest
(`hash = SHA256(prev_hash ‖ index ‖ canonical_json(body))`), so the entries form a chain anchored
at a fixed genesis value. Verification recomputes the whole chain and reports the first entry where
the stored and recomputed hashes disagree. Facts are **versioned by supersede**, never updated or
deleted in place; there is no sanctioned mutate API.

## Alternatives considered

- **A conventional mutable audit table (rows with an `updated_at`).** Rejected: it records history
  but cannot *prove* history is unaltered. Anyone with write access can rewrite a past row silently.
- **Append-only storage alone (no chaining).** Better, but a truncation or a restore-from-an-edited-
  backup is invisible. Chaining makes any excision or reordering detectable, not just in-place edits.
- **External SIEM / log shipping only.** Useful as a complement, but it moves the trust boundary to
  another system rather than making the record self-verifying. We keep the chain as the source of
  truth and can also ship anchors off-site.
- **A full blockchain / distributed ledger.** Rejected as disproportionate: the requirement is
  tamper-*evidence* within a single system of record, not decentralized consensus. A hash chain
  delivers the needed property at a tiny fraction of the operational cost.

## Consequences

- **Positive:** tamper-evidence becomes a checkable property. The runnable
  [`demos/audit-ledger/`](../../demos/audit-ledger/) demonstrates it directly (verify catches body edits, deletions, reordering, and partial
  forgeries). Maps directly to the BOSS "Audited" guarantee and governance-directory entry #5.
- **Cost:** verification is O(n) over the chain; very long chains need periodic checkpoints/anchors
  rather than full re-verification on every read (a known, bounded follow-on).
- **Boundary:** tamper-*evidence* is not tamper-*prevention*. The chain detects alteration; it does
  not stop a party with storage access from altering bytes. Append-only storage and off-site
  anchoring are the operational complements, and are out of scope for the primitive itself.

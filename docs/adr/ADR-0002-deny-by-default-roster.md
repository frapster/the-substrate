# ADR-0002: Deny-by-default: omission is prohibition

- **Status:** Accepted
- **Date:** 2026-07-15
- **Deciders:** Robert J. Floyd
- **Runnable proof:** [`demos/bounded-authority/`](../../demos/bounded-authority/): a clean-room deny-by-default gate that refuses over-scoped and unregistered actions.

## Context

An agentic system's blast radius is the set of actions, tools, and data it *can* reach. If that set
is defined implicitly, as "whatever the code happens to wire up," then capability grows silently as
the system evolves, and no one can state with confidence what an agent is permitted to do. For a
governance surface that has to be *auditable*, the permitted set must be explicit and closed.

## Decision

Governance is **deny-by-default**. Agents, tools, evidence sources, and high-impact actions must be
registered in the system's governance directory to be permitted. **Omission is prohibition:** if
something is not on the roster, it may not act, full stop. The roster is a closed set enforced at
run time.

## Alternatives considered

- **Allow-by-default with a denylist.** Rejected: denylists are unbounded and always incomplete;
  the failure mode is a capability nobody remembered to forbid. Deny-by-default fails safe instead.
- **Policy expressed only in code/config.** Rejected as the primary control: it is neither
  discoverable by an outside party nor guaranteed to match what actually runs. The roster is
  declared *and* enforced (see [ADR-0004](./ADR-0004-publish-governance-directory.md)).
- **Per-feature ad hoc permission checks.** Rejected: they drift out of sync and can't be audited as
  a whole. A single closed roster is the unit of review.

## Consequences

- **Positive:** the permitted surface is always explicitly known and reviewable; new capability
  requires a deliberate registration, which is itself an auditable event.
- **Cost:** more friction to add a tool or action. That friction is intentional; it is the control.
- **Boundary:** this governs *authorization* (may it act?), not *correctness* of a permitted action;
  correctness is handled by the validator ([ADR-0003](./ADR-0003-deterministic-validator-commits.md)).

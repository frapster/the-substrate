# Architecture Decision Records

An **Architecture Decision Record (ADR)** captures one significant decision: its context, the
choice made, the alternatives weighed, and the consequences accepted. ADRs are dated and
immutable. When a decision changes, a new ADR supersedes the old one rather than editing it.

For a governance project this log is on-thesis: an ADR is *evidence-backed, audited reasoning*
applied to the project's own choices. These records describe **architectural judgment**, the
shape and rationale of the approach, not the reserved BOSNet.io / BOSS kernel, schema, or
conformance rule set, which remain proprietary (see [`../../LICENSE.md`](../../LICENSE.md)).

| ADR | Decision | Status |
|---|---|---|
| [0001](./ADR-0001-hash-chained-audit-ledger.md) | Append-only, hash-chained audit ledger | Accepted |
| [0002](./ADR-0002-deny-by-default-roster.md) | Deny-by-default: omission is prohibition | Accepted |
| [0003](./ADR-0003-deterministic-validator-commits.md) | A deterministic validator commits only what passes | Accepted |
| [0004](./ADR-0004-publish-governance-directory.md) | Publish a governance directory (discoverability over trust) | Accepted |
| [0005](./ADR-0005-rag-is-not-the-substrate.md) | Retrieval-by-similarity is not the governed-knowledge substrate | Accepted |
| [0006](./ADR-0006-keep-reference-engine-private.md) | Keep the reference engine private; publish spec + proofs | Accepted |

Format: a light [Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
template with four sections: Context, Decision, Alternatives considered, Consequences.

# ADR-0006 — Keep the reference engine private; publish spec + proofs

- **Status:** Accepted
- **Date:** 2026-07-15
- **Deciders:** Robert J. Floyd

## Context

The work spans two things of very different kinds: a *standard* (BOSS — the governance surface, its
guarantees, and its directory structure) and a *reference implementation* (BOSNet.io — the engine,
kernel, schema, coordinate scheme, and conformance rule set). Publishing everything would forfeit the
value captured in the implementation; publishing nothing would make the thesis unevaluable and read
as vaporware. The IP boundary is itself an architectural decision, and worth recording as one.

## Decision

Model the split on **Kubernetes, OAuth, and OpenTelemetry**: the *specification* is commoditized and
open to describe; the *implementation* is where value is captured. Concretely — **publish the spec's
shape and runnable proofs; keep the engine private.** This repo carries the thesis, the BOSS
principles/guarantees/directory structure, de-identified case studies, and *clean-room runnable
proofs of published claims* (e.g. the hash-chained ledger in [`demo/`](../../demo/)). It never carries
BOSNet.io source, client IP, the kernel/compiler, the dimensional schema/coordinate scheme, or the
normative conformance rule set — those are patent-pending and reserved
([`../../LICENSE.md`](../../LICENSE.md), [`../../BOSS-STANDARD.md`](../../BOSS-STANDARD.md) §6).

## Alternatives considered

- **Open-source the engine.** Rejected: forfeits the captured value and exposes client-adjacent IP;
  the standard, not the engine, is the part meant to be openly describable.
- **Keep everything private (pitch-only).** Rejected: a governance thesis with no inspectable surface
  and nothing runnable is precisely the "hype divorced from shipping" pattern it must avoid. Hence a
  public directory ([ADR-0004](./ADR-0004-publish-governance-directory.md)) and public proofs.
- **Publish redacted engine excerpts.** Rejected: high leak risk for low evaluative gain. A clean-room
  proof of a *published* claim demonstrates the mechanism with zero exposure of the actual engine.

## Consequences

- **Positive:** an evaluator can run real code and read the standard's shape; the reserved engine stays
  protected. The public/private line is explicit and defensible.
- **Cost:** every public artifact must pass an IP-safety review before it ships ("when in doubt, leave
  it out"); some compelling internal detail stays unpublished.
- **Boundary:** "runnable proof" means a clean-room primitive backing a stated claim — never a port of
  the engine. The demo proves *tamper-evidence*; it is not BOSNet.io.

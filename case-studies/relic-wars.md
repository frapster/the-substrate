# Case Study — Relic Wars

**Status: Converted — factual. This before/after shipped; it is measured, not estimated.**
**AI : code (adjudication) — before ~0 : 100 → after ~85 : 15.**

Relic Wars is the **proof case**: the one system here where the conversion to AI-as-governed-substrate
has actually shipped. Because its core is *algorithmic simulation*, it is also the honest **contrast
case** — it shows both that the pattern works and how far it does (and doesn't) travel. Every projected
conversion in the other studies is "the pattern Relic Wars already proves, applied to a new domain."

> The invariant the conversion turned on: **code computes what *does* happen, the substrate decides
> what *should* happen, and a deterministic auditor grades every decision.**

---

## Before — a monolithic rules engine

The original match logic lived in one hand-authored play engine: roughly **2,350 lines** of branchy
rules dispatch. Every capability was a new code path; outcome logic was entangled with control flow.

- **Adjudication ratio:** ~0% reasoning / 100% code.
- **Cost of change:** high — new mechanics rippled through the dispatch.
- **Explainability:** low — the "why" was implicit in the branches taken.

The wider codebase is ~19k lines of TypeScript — mostly a bespoke simulation engine and a Three.js UI —
with a comparatively small external surface (9 tables, 8 dependencies) and, notably, the **best test
coverage of the four systems** (30 test files, ~3,800 test lines, plus a 900-match balance tournament
harness).

## The conversion move

The engine was **retired** and replaced by three small parts the model drives at run-time:

1. a **capability fact table** (~120 lines) — one row per capability;
2. a **system prompt** (~70 lines) that adjudicates a contest; and
3. a **deterministic auditor** (~90 lines) that grades the model's answer against seeded ground truth.

Per contest the model classifies the degree of success, elects the winner, and **cites the exact facts
it used** — roughly eight such decisions per snap, in dependency order.

## After — governed run-time reasoning (today)

- **Adjudication ratio:** ~85% governed reasoning / ~15% code. A ~2,350-line engine became a ~280-line
  table + prompt + validator.
- **Cost of change:** a new rule is **one table row**, not a new branch.
- **Explainability:** every outcome ships with checkable citations against a hashed fact set.

**The boundary, stated honestly.** The model never computes the arithmetic. Seeded code pre-computes
ground truth and the model is *graded against* it. The conversion displaced **branchy rules-dispatch
code** — not the physics. "Math is law; code disposes."

## Total cost of ownership

A rules/simulation engine's dominant lifetime cost is *enhancement* — endless balancing and new content —
which lands squarely in the expensive 60% "enhancement" slice of the
[60/60 maintenance rule](https://www.oreilly.com/library/view/97-things-every/9780596805425/ch34.html).
The conversion attacks exactly that bucket: adding or tuning a mechanic is now editing a table row and a
prompt, not tracing and re-testing a 2,350-line dispatch. Build cost of the adjudication core fell ~88%
(≈2,350 → ≈280 lines); the larger, durable win is that the part that changes most often is now the part
that is cheapest to change.

## Code quality & security

Relic Wars is the cleanest illustration of the governance discipline because its safety model and its AI
model are the *same shape*. The category norm for a competitive game is
**[server-authoritative architecture](https://www.gabrielgambetta.com/client-server-game-architecture.html)**:
never trust the client; keep authoritative state and validation on the server. Relic Wars extends the
identical rule to the model — *never trust the model's answer; re-derive and check it* — via:

- a **deterministic auditor** that rejects any output inventing an entity, citing out-of-envelope facts,
  omitting citations, or contradicting the computed outcome (fail-closed; two-tier escalation, then a
  denial receipt);
- **server-authoritative resolve** that still runs fully in code if no model key is present; and
- an **auto-RLS database trigger** that enables row-level security on every new table, so a forgotten
  policy cannot ship.

That the code is LLM-authored is precisely why these gates exist: unreviewed model output is a draft
(see [`ENGINEERING.md`](../ENGINEERING.md) §3). Here the draft is graded by code before it can matter.

## The honest boundary

**Where it paid off:** rule extensibility (rows, not branches) and explainability (citations). **Where
code stayed, deliberately:** all arithmetic, seeded randomness, and geometry — the numeric core, where
certainty matters. Relic Wars is not "all code → all AI"; it is "branchy rules dispatch → prompt + table
+ validator." And because its bulk is algorithmic, it is the *least* blueprint-compilable of the four —
which is exactly why it is the honest anchor for the estimates that follow in the other studies.

---

> IP-safety reviewed before publishing. Describes Relic Wars' own governance pattern only — no
> proprietary BOSNet.io source, no secrets, no client IP.

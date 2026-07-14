# Case Study — Relic Wars

**code : AI ratio — AI-heavy.** Governed run-time reasoning carries the adjudication that a
traditional build hard-codes. A hand-authored rules engine was retired in favour of a fact matrix,
a prompt, and a deterministic auditor.

> The one-line invariant the whole design turns on: **code computes what *does* happen, the
> substrate decides what *should* happen, and the contest is the seam between them.**

---

## What it is

Relic Wars is a browser-based fantasy-sports strategy game — a *pre-snap simulation*. The player
drafts a warband, builds a fortress, and authors coaching doctrine; then the match resolves
deterministically and is played back. There is no twitch input, which is the point: every outcome
has to be *explainable after the fact*, so the system is built to produce an auditable account of
why each contest went the way it did.

- **Stack:** TypeScript, React + Zustand, a Three.js / React-Three-Fiber renderer, Vite/Vitest.
- **Backend:** Supabase (Postgres, Auth, row-level security, Deno edge functions).
- **Reasoning:** a two-tier model cascade — a small nano-class model as primary, escalating to a
  larger model only on rejection — called with strict structured-JSON output.

## The substrate move

The original design carried match logic in a single monolithic play engine — roughly **2,350 lines**
of branchy rules dispatch. That engine was **retired**. In its place, the adjudication "brain" is now
three small parts:

1. a **capability fact table** (~120 lines) — one row per game capability;
2. a **system prompt** (~70 lines) that asks a model to adjudicate a contest; and
3. a **deterministic auditor** (~90 lines) that grades the model's answer against ground truth.

Per contest, the model does the work that enumerated branches used to do: it classifies the
**degree of success** (critical-success / success / failure / critical-failure), elects which entity
prevails, and **cites exactly which facts it used**. A snap concentrates roughly eight such decisions —
reads, deception acts, counter-reads, capability elections — resolved in dependency order.

**The boundary, stated honestly.** The model never determines the *arithmetic* outcome. Seeded
deterministic code pre-computes ground truth for every contest; the model is *graded against* it.
So the substrate move is precise: it replaced **branchy rules-dispatch code** with a **fact table +
prompt + validator** — it did not move the physics. AI governs *election, adjudication-classification,
and narration*; seeded code governs the numbers. "Math is law; code disposes."

## Dimensional model

Contest state is compiled into a **coordinate-addressed matrix of facts** — an "envelope" of nodes
where every fact is path-addressed: `entity/{id}/aptitude`, `read/{contestId}/target-dc`,
`read/{contestId}/roll`, and so on. Each envelope is pinned by a deterministic **compile hash**, so
the exact fact-set a decision was made on is reproducible forever. Entity attributes are a fixed
seven-stat vector. The model only ever sees this closed, hashed fact table — never free-form game
state — which is what makes its citations checkable.

## Knowledge graph

Capabilities live in a **fact table read generically by the compiler**: each row maps an aptitude
stat → an opposed stat → a consequence type. Adding a new capability to the game means **adding a
row**, not writing a new branch anywhere. On top of that sit three relationship graphs the engine
walks at run-time:

- a **read / counter-read graph** that self-prunes — deep counter-reads only fire when the prior
  read wins;
- a **line-of-sight / line-of-effect geometry graph** that gates which contests are even legal; and
- a **per-snap dependency graph** of contests, topologically batched with cycle detection and a
  fail-closed default.

## Vectorized data

**None — by design.** There is no embedding store or retrieval step. The reasoning operates over a
*closed, hand-supplied fact set*, not an open corpus. That is a deliberate governance choice:
bounding the model to a hashed envelope is what lets a deterministic auditor verify every claim.
This is governance-by-envelope, not retrieval — and it is the right trade for a system that has to
be provably correct rather than broadly informed.

## Governance

This is where run-time reasoning is made load-bearing safely. The model is bounded on every axis:

- **The Auditor (commit gate).** A deterministic validator re-derives ground truth and **rejects**
  any model output that invents an entity, cites a fact outside the envelope, omits its citations,
  or contradicts the computed outcome. It fails closed and never "corrects" the model — a bad answer
  is thrown away, not patched.
- **Two-tier escalation.** On rejection the contest escalates from the small model to the larger one;
  on a second failure **nothing commits** and the system records a denial receipt instead of guessing.
- **Append-only evidence ledger.** Every resolved contest writes a row — compile hash, seed, model
  reference, pinned prompt reference, the causal chain, and the referee's verdict (clean / rejected).
  It is server-write-only; clients can read their own match but cannot write to the ledger.
- **Server-authoritative resolve.** Resolution runs once, server-side, as a resumable background job,
  idempotent per play. Crucially, **governance is additive**: with no model key configured the match
  still resolves fully in code — the AI layer changes the *narration and the evidence trail, never the
  score*.

## The ratio, measured

- **Displaced:** a ~2,350-line rules engine → a ~120-line fact table + ~70-line prompt + ~90-line
  auditor + a thin provider adapter. New rules become table rows, not code paths.
- **Retained in code, deliberately:** all arithmetic, seeded randomness, geometry, and dependency
  ordering — the deterministic half is still substantial, because that is where certainty matters.
- **Validated, not asserted:** an offline bake-off over 200 contests measured full accuracy on the
  outcome band and on citation-legality, with a blended governed cost on the order of cents per
  thousand contests. Concentrated agency — roughly eight decisions per snap — keeps that cost bounded.

**Where it paid off:** rule extensibility (rows, not branches) and explainability (every outcome
ships with checkable citations). **Where it didn't, and shouldn't:** the numeric core stayed in
code. The honest headline is *"branchy rules dispatch → prompt + table + validator,"* not
*"all code → all AI"* — and that precision is the case study.

---

> IP-safety reviewed before publishing. Describes Relic Wars' own governance pattern only — no
> proprietary BOSNet.io / BOSGov source, no secrets, no client IP.

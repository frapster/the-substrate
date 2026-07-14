# Case Study — Zabble

**code : AI ratio — code-heavy, with narrow governed-AI seams.** By volume the system is
overwhelmingly hand-authored governance, schema, and read-model plumbing. Run-time reasoning is
admitted at only a handful of high-leverage judgment seams — and the code that surrounds them *is*
the product.

> The lesson Zabble carries for the thesis: the substrate move isn't "replace the code with AI." It's
> building enough deterministic envelope — bounds, audit, budget caps, injection hygiene, fixed action
> spaces — that a few reasoning calls can safely displace scraper fleets, rules engines, and human
> moderators.

---

## What it is

Zabble is a consumer social platform for recurring local groups and their events — persistent group
identity, local discovery, trust-and-safety, and a non-extractive payment model, launching in a
single metro.

- **Stack:** Next.js (App Router) + React, TypeScript, on Vercel, with strict module boundaries.
- **Backend:** Supabase Postgres with row-level security everywhere, plus PostGIS, pgvector, cron,
  and queues.
- **Reasoning:** the Vercel AI SDK through an AI gateway — a small text model for all text tasks,
  an image model for hero art, and an embedding model — with model choice centralized in a single
  task→model catalog.

## The substrate move

Zabble uses run-time reasoning in four places where traditional code would need scrapers, parsers,
rules engines, or human labour:

1. **Open-world event extraction.** Instead of a fleet of per-site scrapers and date parsers, the app
   fetches an arbitrary web page and asks the model to emit a strict JSON event record — title, date,
   venue, category, performers, confidence — validated against a schema. **One prompt replaces N
   site-specific parsers.**
2. **Agentic moderation.** Grooming, scam, doxxing, and "creepy DM" judgment — work that would
   otherwise be human moderators or brittle keyword rules — is done by a model given sender context
   and a *bounded* action space.
3. **Grounded narrative generation.** Event recaps, analytics narratives, and group copy are generated
   from **real database counts**, never invented numbers.
4. **Semantic discovery.** Embedding-based "for you" matching replaces hand-tuned tag/keyword ranking.

The stated design principle: *deterministic where milliseconds and certainty matter, agentic where
judgment matters, batch where patterns matter.*

## Dimensional model

The spine is **event-sourced (CQRS-lite)**. An append-only `domain_events` table is the system of
record — every state change is written transactionally alongside the mutation it describes, and that
same stream doubles as the trust-and-safety audit log, the webhook replay source, and the fan-out
trigger for moderation, embeddings, and analytics. Read models and rollups are rebuilt from the
stream. AI spend is its own dimensional layer: per-tenant budgets, a usage ledger, and a wallet,
metered per feature.

## Knowledge graph

A real entity graph underpins the anchor category and solves cold-start. Performers and venues (with
1:1 enrichment profiles) are the nodes; a many-to-many performer↔event join and an event→canonical-
event back-reference are the edges, alongside a general relationship-edge primitive (follows,
co-attended). Entity resolution is **fuzzy** — trigram indexes on names, a confidence band separating
enriched from name-only records, and a "times seen" counter — so the graph dedups itself as new
sources arrive.

## Vectorized data

pgvector provides the semantic layer: 1536-dimension embeddings on groups and on member interest
profiles, HNSW-cosine indexed, write-protected behind security-definer functions. A discovery function
ranks non-private, active groups by cosine similarity, unconditionally excluding private and
already-joined groups. This is embedding-*ranked* discovery rather than a full retrieve-then-generate
loop — the generation paths are grounded on computed data, not vector recall.

## Governance

Governance is the largest part of the system, and the point of the case study. Reasoning runs inside
a hand-authored deterministic envelope built in three layers:

- **L1 — deterministic gate.** Pure in-database logic, *no model calls*, run in-transaction before a
  message is even written: rate limits, blocklists, link reputation, consent and membership checks.
  By construction it **cannot be prompt-injected**.
- **L2 — agentic, but fenced.** The model may judge, but its output is coerced into a **fixed action
  space**; the most consequential actions (bans, removals) are *always* routed to a human, and any
  unrecognized model action degrades safely to "flag for human."
- **L3 — batch pattern analysis** over the event stream.

Around those layers:

- **Immutable audit** — every model verdict (action, rationale, model version) is written to a
  moderation log; rejected messages are logged too.
- **Prompt-injection hygiene as policy** — user and third-party content is always passed as *data*,
  never instructions; system prompts stay server-side; message bodies are delimiter-wrapped.
- **No-hallucinated-facts rule** — recaps and narratives may use only real counts.
- **AI spend governance** — hard per-tenant monthly caps and a hard daily cap on the discovery cron,
  checked against a persistent ledger, behind authenticated, rate-limited endpoints.
- **Secret isolation** — provider keys live in a vault and are resolved only inside edge functions,
  never in user-content paths — plus row-level security as the standing perimeter.

## The ratio, measured

- **Scale of the envelope:** on the order of ~31,000 lines of application code and ~100+ SQL
  migrations defining a few hundred functions/RPCs — overwhelmingly hand-authored governance, schema,
  and read models.
- **AI footprint:** roughly **17 distinct reasoning call sites** in the entire application.
- **Displacement is qualitative, not volumetric.** Each seam replaces something large: the extraction
  prompts stand in for a fleet of per-venue scrapers; the single safety prompt stands in for a
  hand-maintained abuse classifier; one model catalog centralizes every model choice into a one-line
  change.
- **Position on the spine:** the **code-heavy** end — and deliberately so. The story is not that AI
  replaced most of the code; it is that most of the code exists *so that* a few reasoning calls can be
  trusted.

**Where it paid off:** open-world extraction and abuse judgment, which resist clean rule-based
solutions. **Where code stayed, hard:** anything fast, certain, or irreversible — payments, the L1
gate, the final say on bans. The boundary between the two is the product.

---

> IP-safety reviewed before publishing. No secrets or project identifiers, no verbatim safety prompts
> or thresholds, no third-party-sourced datasets, and no BOSNet.io / BOSGov internals.

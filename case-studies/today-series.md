# Case Study — Today Series

**Status: Planned conversion — the "after" is a projected target, not shipped. Figures are labeled
estimates.**
**AI : code — before ~35 : 65 → after (projected) ~85–90 : 10–15.**

Today Series is the case that can go **furthest** toward LLM-First. Unlike Relic Wars — which keeps a
large deterministic core for its physics — a study-content platform's "physics" is *language and
judgment*, exactly what governed reasoning does well. That makes it a candidate to approach the 90 : 10
target: closer to a governed tenant than to a hand-coded app, driven by a **blueprint compiler** rather
than enumerated routes.

> Target thesis: most of what the app *does* — decide what content to produce, how to structure a lesson,
> what to retrieve, what to publish — becomes governed reasoning compiled from declarative blueprints,
> with hand-authored code reduced to the irreducible plumbing.

---

## Before — current state (grounded)

Today Series already uses reasoning as a **knowledge-production substrate**: a thin AI layer (~390 lines
of glue) manufactures the knowledge product — extraction, taxonomy, semantic de-duplication, authoring.
But the *serving layer* is conventional hand-authored code.

- **Scale:** ~9,900 lines of TypeScript, 19 pages, 11 API routes, 16 migrations, 20 tables. The
  smallest and leanest of the four.
- **Ratio (today):** ~35% reasoning / ~65% code — high in ingestion, ordinary in delivery.
- **Substrate already present:** a four-facet knowledge base (`prose · facts · qa · taxonomy`), a
  cross-ref graph populated by an LLM judge, and pgvector + full-text hybrid retrieval.
- **Standout risk:** a **thin test surface** — 3 test files, ~162 lines. For a platform this is the
  maintenance liability the conversion must address, not inherit.

## The conversion move (roadmap)

Apply the **proven pattern from Relic Wars** — envelope compiler + blueprints + auditor — to the
*operational* layer, not just ingestion. **This is a plan; none of it has shipped.**

1. **Blueprint the content types.** Replace hand-coded page/lesson logic with declarative blueprints
   (what a lesson is, what a study article requires, what a valid publication looks like).
2. **Compile, don't branch.** A governed compiler turns a blueprint + retrieved evidence into a run-time
   plan — curation, sequencing, and metadata become compiled reasoning, not enumerated code.
3. **Auditor over authoring.** Extend grounding/citation checks into a deterministic auditor that rejects
   any artifact citing unretrieved sources or missing provenance — the Relic Wars commit-gate, applied
   to content.
4. **Raise the test floor as blueprints land.** Blueprint conformance + auditor checks become the
   regression net the current codebase lacks.
5. **Keep the transactional shell.** Auth, billing, and RLS stay deterministic.

## After — projected target (ESTIMATE)

- **Projected ratio:** ~85–90% reasoning / ~10–15% code _(estimate)_ — approaching the LLM-First 90 : 10
  target because so little of a content platform is irreducibly deterministic.
- **Projected displacement:** ~50–70% of the current hand-authored app/serving logic replaced by the
  compiler + blueprints _(estimate)_.
- **What stays code:** billing, auth, RLS, the publish gate, and the human review stamp.

## Total cost of ownership

For a content platform, lifetime cost is dominated by *enhancement* — new content types, new lesson
formats, retrieval tuning — the expensive slice of the
[60/60 rule](https://www.oreilly.com/library/view/97-things-every/9780596805425/ch34.html). Today those
changes mean editing routes and services and (ideally) tests that barely exist. After conversion they
mean editing a **blueprint**, with the compiler and auditor carrying the rest. The estimated ~50–70%
reduction in maintained operational code is the point — and it lands on exactly the code that changes
most and is currently least tested.

## Code quality & security

The category standard for a RAG publishing platform is the
**[OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/)** — prompt injection
(including *indirect* injection via poisoned source documents), vector/embedding isolation, and
misinformation — plus, for anything that publishes, content-provenance via
**[C2PA / Content Credentials](https://c2pa.org/)**. Grounding is not security: neither RAG nor
fine-tuning removes prompt injection, so the conversion's auditor and citation-provenance checks are
load-bearing controls, not nice-to-haves.

On the build side, Today Series already runs the governance discipline that makes LLM-authored code
safe: a full remediation cycle closed the security findings **F-01 through F-08** in a tracked batch,
and generation is gated by grounding/refusal prompts and input/output moderation. The conversion extends
that same gate-and-remediate loop from ingestion to the whole operational surface (see
[`ENGINEERING.md`](../ENGINEERING.md) §3).

## The honest boundary

**Where it should go LLM-First:** content decisions, lesson structure, curation, retrieval planning —
judgment work with reversible outputs and a human gate. **Where code must stay:** money, identity, and
access control. The estimate is a *range*, and it is theoretical until the conversion is built and
measured against these targets.

---

> IP-safety reviewed before publishing. No secrets, project identifiers, or third-party copyrighted
> text. "After" figures are projected estimates, clearly labeled. No BOSNet.io internals.

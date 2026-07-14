# Case Study — Today Series

**code : AI ratio — AI-substantial (governed knowledge-production substrate).** A thin reasoning
layer *manufactures* the knowledge product — extraction, taxonomy, de-duplication, authoring — which
a conventional, deterministic app then serves, reviews, and bills for.

> The interesting seam here isn't the chatbot. It's that four subsystems a traditional build would
> hand-code — a parser/ETL, a classifier, an entity-resolution engine, and a content generator — are
> collapsed into prompts and schemas, then fenced by grounding rules, moderation, and human review.

---

## What it is

Today Series is an AI-assisted study-content platform: a public library of long-form articles and
structured lesson plans, a retrieval-grounded study chatbot, subscription commerce, consent-gated
analytics, and generated voice/avatar media.

- **Stack:** Next.js (App Router) + React, TypeScript, Tailwind.
- **Backend:** Supabase (Postgres, Auth, Storage, pgvector).
- **Reasoning:** the Vercel AI SDK over a small model registry — a long-form authoring model, a fast
  chat/classification model, and a strict-JSON fallback — plus an embedding model for retrieval.

## The substrate move

Run-time reasoning replaces four subsystems that a traditional content pipeline would build by hand:

1. **Document → structured data.** Instead of parsers and regex ETL, LLM extractors turn raw source
   manuscripts into typed structures — prose, facts, Q&A, and taxonomy. The **code defines the target
   schema; the model performs** the sectioning, fact/date/person extraction, and Q&A generation.
2. **Entity resolution by judgment, not rules.** Facts and Q&As are clustered by vector similarity;
   for the ambiguous middle band, an **LLM judge decides "duplicate" vs. "nuance variant"** and writes
   a one-sentence rationale. Brittle heuristic matching is replaced by semantic adjudication.
3. **Authoring.** Article bodies and lesson plans are generated from retrieved context, and the
   publication metadata itself — title, excerpt, SEO fields, tags — is produced by a second structured
   generation call against a schema rather than hand-computed.
4. **Moderation** is delegated to a moderation model rather than keyword lists.

The whole AI core is roughly **390 lines** across six files. That thin layer stands in for what would
otherwise be a content-generation engine, a taxonomy classifier, an extraction pipeline, and a dedup
engine.

## Dimensional model

State is Postgres — relational plus JSONB plus vector. The knowledge base is one row type keyed by
**four facets** (`json_type ∈ prose | facts | qa | taxonomy`), each carrying its content JSON, a
provenance/metadata blob, an ordering key, and its own embedding. Source documents flow through an
explicit state machine (pending → processing → completed / failed) with content-hash de-duplication.
The four facets *are* the dimensions: every source is decomposed along them and each facet is
independently embedded and retrievable.

## Knowledge graph

A lightweight semantic graph sits over the knowledge base. A cross-reference table stores typed edges
between KB rows — `duplicate`, `nuance_variant`, `contradicts`, `extends` — each annotated with an
LLM-written note explaining the relationship. The edges are **discovered by the reasoning pass**, not
hand-curated: it is an emergent semantic graph, populated as the nuance judge works through the corpus.

## Vectorized data

Retrieval is central. pgvector stores a 1536-dimension embedding per KB facet, indexed with HNSW
cosine. Search is **hybrid** — vector similarity fused with Postgres full-text ranking via reciprocal
rank fusion — behind a security-definer function so application code never touches the RLS-locked KB
tables directly. Both the chatbot and the authoring path retrieve through the same wrapper, which
returns numbered, citable context blocks.

## Governance

The reasoning is wrapped in a deliberate guardrail layer:

- **Grounding + refusal prompts** that require citations, forbid fabricating source material, and
  keep the assistant from overstepping into authoritative counsel.
- **Input and output moderation** — user input is gated before it reaches the model, and generated
  drafts are moderated before they can be published.
- **Layered rate limiting and a site-wide circuit breaker** in front of the reasoning endpoints.
- **Row-level security everywhere**, role checks, and security-definer functions with pinned search
  paths.
- **Human-in-the-loop publishing.** Content moves draft → review → published, and the reviewer is
  stamped on publish. Reasoning *produces artifacts*; people and deterministic code decide what goes
  live. The project also carries a documented security-hardening pass, evidence that the governance
  layer is maintained rather than assumed.
- **Graceful degradation:** every external integration sits behind a capability check and no-ops
  cleanly when unconfigured.

## The ratio, measured

- **Displaced:** ~4 subsystems (extraction, classification/taxonomy, dedup/entity-resolution,
  authoring) collapsed into ~390 lines of prompts and schemas. The two most expensive pipeline stages
  — parse-and-embed, and LLM-judged de-duplication — are essentially *pure reasoning*.
- **Retained in code:** the serving and commerce layer — routing, RLS, subscription sync, webhooks,
  rate limiting, consent, media reconciliation. Conventional, deterministic engineering.
- **Position on the spine:** the ratio is *high in the knowledge-manufacturing pipeline* and
  *ordinary in the delivery layer*. Run-time reasoning is not the live control plane for user
  transactions; it is the **governed substrate that produces the knowledge product**, which a
  traditional app then serves.

**Where it paid off:** turning unstructured manuscripts into a queryable, cross-referenced knowledge
base without building four bespoke engines. **Where code rightly stayed:** anything touching money,
identity, or what a user is allowed to see.

---

> IP-safety reviewed before publishing. No secrets, project identifiers, or third-party copyrighted
> text. Scoped to Today Series only — no BOSNet.io / BOSGov internals, no shared-infrastructure detail.

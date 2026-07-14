# Case Study — Zabble

**Status: Planned conversion — the "after" is a projected target, not shipped. Figures are labeled
estimates.**
**AI : code — before ~8 : 92 → after (projected) ~30–40 : 60–70.**

Zabble is the case that shows the substrate has a **ceiling**. It is a live consumer platform with
payments, real-time messaging, and trust-and-safety — a lot of logic that must be fast, certain, and
irreversible. Its conversion is real but **bounded**: reasoning expands at the judgment seams while the
deterministic core stays exactly where it is. *Where the substrate stops* is the story.

> Target thesis: govern more of the judgment work (moderation, curation, extraction, ranking) and
> blueprint-compile the CRUD/read-model plumbing — but never move the deterministic safety gate,
> payments, or the real-time path off code.

---

## Before — current state (grounded)

Zabble is **code-heavy** by design: ~33,400 lines of TypeScript, 57 pages, and an unusually heavy data
layer — **108 migrations, 65 tables, 234 database functions/RPCs, 102 RLS policies**. Run-time reasoning
is fenced to a small number of seams; a three-layer safety architecture keeps the fast path
deterministic.

- **Ratio (today):** ~8% reasoning / ~92% code.
- **Where reasoning lives:** open-world event extraction, agentic (fenced) moderation, grounded copy,
  semantic discovery.
- **Where it can't:** the L1 deterministic safety gate (cannot be prompt-injected), payments, and the
  event-sourced write path.
- **Discipline in place:** CI runs typecheck / lint / unit / build plus a hard **service-role-key
  guard**, an ephemeral database runs **pgTAP**, and an **RLS-audit** skill checks tenant isolation.

## The conversion move (roadmap)

Apply the proven envelope/compiler/auditor pattern **only to the reversible, judgment-heavy surfaces.**
**This is a plan; none of it has shipped.**

1. **Blueprint the read models & discovery.** Replace hand-tuned ranking and read-model assembly with
   blueprint-compiled reasoning over the existing embeddings and graph.
2. **Widen the governed moderation seam.** Move more borderline moderation and pattern analysis into
   governed reasoning with the existing fixed action space and human escalation — but keep L1
   deterministic.
3. **Compile the extraction fleet.** Generalize event extraction into blueprint-driven, auditor-checked
   ingestion (one blueprint per source *shape*, not per site).
4. **Freeze the core.** Payments, the L1 safety gate, and the event-sourced spine stay deterministic by
   policy. This is the ceiling, and it is intentional.

## After — projected target (ESTIMATE)

- **Projected ratio:** ~30–40% reasoning / ~60–70% code _(estimate)_. A meaningful shift, not a rewrite —
  and deliberately short of the 90 : 10 target.
- **Projected displacement:** ~25–40% of the *non-safety-critical* hand-authored logic (ranking,
  curation, extraction plumbing, copy) replaced by governed reasoning _(estimate)_.
- **Explicitly unchanged:** the deterministic safety and transactional core — the largest part of the
  codebase.

> **Why this moves less than Today Series:** Zabble's product *is* its deterministic envelope. A few
> reasoning calls can be trusted *because* the code around them is rigid; governing the irreversible path
> would remove the very property that makes the seams safe.

## Total cost of ownership

Zabble's maintenance cost is concentrated in that heavy data layer — **234 RPCs and 65 tables**, a lot of
business logic pushed into Postgres functions that are hard to refactor. Blueprint-compiling the
CRUD/workflow surface targets that cost directly, while the fixed safety/payments floor
(~20–30% of the system) stays put. The estimated ~25–40% reduction in maintained operational logic is
modest *by design* — the honest read is that a payments-and-safety platform keeps most of its
[60/60 maintenance load](https://www.oreilly.com/library/view/97-things-every/9780596805425/ch34.html)
in code, and should.

## Code quality & security

Zabble sits under the strictest external bar of the four. The relevant standards are the
**[OWASP Top 10:2025](https://owasp.org/Top10/2025/)** — where **broken access control is still #1**,
the dominant multi-tenant risk that RLS exists to mitigate — the
**[OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/)** for the moderation and
extraction seams (prompt injection, excessive agency), and
**[PCI DSS 4.0](https://www.pcisecuritystandards.org/document_library/)** for anything touching payments.
This is exactly the category where the published weakness of ungoverned LLM code bites hardest —
[Veracode found models choose the insecure option ~45% of the time](https://www.veracode.com/blog/genai-code-security-report/),
concentrated in access-control and injection classes.

Zabble's answer is the gate-and-remediate loop: a **service-role-key guard** that fails the build if a
privileged secret escapes its sanctioned module, **pgTAP** and RLS audits on an ephemeral database, and
tracked security-finding remediation cycles — **F-01 through F-12** across three batches, plus a
self-heal pass on plan drift. That governed floor is *why* it is safe to widen the reasoning seams at
all (see [`ENGINEERING.md`](../ENGINEERING.md) §3).

## The honest boundary

**Where it should expand:** reversible judgment — ranking, curation, moderation triage, extraction.
**Where it must not:** anything fast, certain, or irreversible. The most credible thing Zabble can say
about the substrate is where it *chooses not to apply it* — and that boundary is the design. All "after"
figures are theoretical until built and measured.

---

> IP-safety reviewed before publishing. No secrets or project identifiers, no verbatim safety prompts or
> thresholds, no third-party-sourced datasets. "After" figures are projected estimates, clearly labeled.
> No BOSNet.io / BOSGov internals.

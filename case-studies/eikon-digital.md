# Case Study: Eikon Digital Solutions

**Status: Planned conversion, the "after" is a projected target, not shipped. Figures are labeled
estimates.**
**AI : code, before ~12 : 88 → after (projected) ~80-85 : 15-20.**

Eikon Digital is the most **radical** conversion on the list, because it is the one that becomes a
**full BOSNet.io tenant** rather than merely borrowing the pattern. Today it is a large, conventional web
application. The target is a site whose operational logic is largely *governed run-time reasoning
compiled from blueprints*: the endpoint the whole thesis points at, and the largest delta of the four.

> Target thesis: a company system where the CRM, campaigns, content, and assistant are not ~179
> hand-authored routes but blueprint-compiled, envelope-governed reasoning running as a governed tenant:
> NLUI-first, evidence-backed, auditable end to end.

---

## Before: current state (grounded)

The Eikon Digital site is far beyond brochureware: a production Next.js application combining a public
marketing frontend with an authenticated back-office (CRM, email/social campaigns, content management,
scheduling, a natural-language assistant, and digital business cards).

- **Scale:** **~350,000 lines of hand-authored TypeScript** (more than the other three systems combined),
  across ~178 pages and **~179 API routes**, with **158 migrations, 132 tables, and 354 RLS policies**
  and **71 production dependencies** spanning every integration group.
- **Ratio (today):** ~12% reasoning / ~88% code. An AI assistant exists, and an **early-stage governance
  foundation** is in place, but the envelope-governed, proof-carrying tiers are **not yet implemented**
  (documented honestly in the project's own notes).
- **Maintenance drivers:** integration sprawl (71 deps across email, social, campaigns, calendar, CRM,
  CMS, assistant, cron, webhooks) and bespoke assistant/orchestrator code in large single files. It is
  the highest-maintenance system of the four by a wide margin.

## The conversion move (roadmap)

Move the system onto a full governed tenant, replacing hand-authored operational code with
blueprint-compiled reasoning under end-to-end governance. **This is a plan; the governed tiers do not
exist yet.**

1. **Blueprint the back-office.** Express CRM objects, campaign flows, and content types as declarative
   blueprints instead of bespoke routes and services: the bulk of the ~179 route handlers.
2. **Compile to run-time plans.** A governed compiler turns a blueprint + evidence into an executable
   plan: the Relic Wars envelope pattern, generalized to business operations.
3. **NLUI-first surface.** Promote the natural-language assistant from a feature to the primary control
   surface, with deterministic policy before and after every action.
4. **Mature the governance to envelope-governed / proof-carrying tiers.** Raise the existing foundation
   to where every high-impact action is bounded, evidence-backed, audited, and reversible.
5. **Keep the deterministic shell.** Auth, billing, secrets, and access control stay code.

## After: projected target (ESTIMATE)

- **Projected ratio:** ~80-85% reasoning / ~15-20% code _(estimate)_. Most operational route/service
  logic collapses into blueprints + compiled reasoning; the plumbing floor remains.
- **Projected displacement:** ~55-75% of the current hand-authored app/route logic replaced _(estimate)_,
  the single largest delta of the four case studies.
- **What stays code:** authentication, billing, secret handling, and access control.

> **Why this is the most radical:** Relic Wars converted one subsystem; Eikon converts the *operating
> model of a whole application* onto a governed tenant. It is the clearest illustration of "AI as the
> operational substrate." Precisely because it is that ambitious, it is the most clearly labeled
> estimate here.

## Total cost of ownership

This is the flagship TCO argument. With ~350k hand-authored lines, ~179 routes, 132 tables, and 71
integrations, Eikon carries the heaviest lifetime-maintenance load of the four. The
[60/60 rule](https://www.oreilly.com/library/view/97-things-every/9780596805425/ch34.html) says the
build cost already visible is the smaller part of what this system will cost to own. An estimated
~55-75% of that operational surface is blueprint-compilable; moving it off hand-authored code changes
what must be maintained from hundreds of bespoke routes to a set of blueprints plus a governed compiler.
The wager is that a governed tenant costs **an order of magnitude less to *own* over its life** than
~350k lines of hand-authored operational code, even though the rebuild itself is not cheap. (Exact line counts
are methodology-sensitive and stated as measured ranges.)

## Code quality & security

Eikon is a multi-tenant SaaS with an agentic assistant: the highest-surface-area risk profile of the
four. The governing standards are the **[OWASP Top 10:2025](https://owasp.org/Top10/2025/)** (broken
access control is #1; RLS is the multi-tenant mitigation), the
**[OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/)** (especially **LLM06
Excessive Agency**, the specific risk when an assistant can act on CRM data), and PCI DSS where payments
are involved. This is the exact stack AI coding assistants target, and the exact place their published
weaknesses ([Veracode ~45% insecure choices](https://www.veracode.com/blog/genai-code-security-report/);
[GitClear duplication/churn](https://www.gitclear.com/the_ai_code_quality_maintainability_gap)) do the
most damage.

Because every line is LLM-authored, Eikon runs the heaviest gate stack of the four: a chained set of
**six pre-commit guards** (endpoint-lock, a no-stubs gate, blueprint-lint, a public-view protocol, a
legacy-chain guard, and a content-truth check), a security-fix series closing IDOR/authorization holes
and untracking committed secrets, and the largest test surface of the group (~22k test lines). The
conversion's aim is to make governance *native* rather than bolted on: moving from guards that catch
bad code to a compiler that emits governed behavior by construction (see
[`ENGINEERING.md`](../ENGINEERING.md) §3-§5).

## The honest boundary

**Where it should convert:** the operational logic (CRM, campaigns, content, assistant), which is
judgment and orchestration over a governed knowledge base. **Where code must stay:** auth, billing,
secrets, access control. This is the destination the thesis is calibrated against, and it is entirely
theoretical until the governed tiers are built and the system actually runs on them.

---

> IP-safety reviewed before publishing. No secrets, key names, project identifiers, or client names. The
> governance kernel and BOSNet.io internals are described at concept level only. "After" figures
> are projected estimates, clearly labeled.

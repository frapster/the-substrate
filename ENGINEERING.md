# The engineering thesis — building and governing an LLM-first system

**Author: Robert J. Floyd** — founder/CEO, Eikon Digital Solutions · [robfloyd.me](https://robfloyd.me)

This companion to [`THESIS.md`](./THESIS.md) covers the parts of "AI as the governed operational
substrate" that are about *engineering economics and discipline*, not just architecture: what it costs
to build and maintain, what it means that the code is LLM-authored, and what it takes to govern an LLM
you don't own. Each [case study](./README.md#case-studies) applies these threads to its own before/after.

Every external claim below is cited. Estimates about not-yet-built conversions are labeled as estimates.

---

## 1. LLM-First, not LLM-Heavy

The distinction is the whole game.

- **LLM-Heavy** — a codebase that *calls* an LLM in many places, but is still structured code-first:
  hand-authored routes, enumerated logic, the model bolted on. Lots of AI, no governed default.
- **LLM-First** — reasoning is the **default operational layer**; hand-authored code is the *exception*,
  reserved for the things a model should not do (irreversible actions, identity, money, secrets). And it
  is a **build posture** as much as a runtime one: you author **blueprints and intent**, a **governed
  compiler** turns them into run-time behavior, and a human orchestrator curates the result.

The target ratio is **90 : 10 (AI : code)** — 90% of operational behavior carried by governed run-time
reasoning, 10% deterministic code for what must stay certain. In BOSNet.io this began as an 80/20 split;
the working target is now 90/10.

The point of a *ratio* is that it is honest about where the line falls. Not every system can or should
reach 90/10 — a payments-and-safety platform has a hard deterministic floor. The discipline is choosing
that line deliberately, and the [Relic Wars case study](./case-studies/relic-wars.md) is the one place
here where the conversion has actually shipped and the line can be *measured* rather than estimated.

## 2. Total cost of ownership — the maintenance argument

Software is not paid for when it is written. It is paid for over its life.

The canonical framing is the **60/60 rule**: roughly 60% of a system's lifetime cost is maintenance, and
about 60% of *that* is enhancement, not bug-fixing ([O'Reilly, *97 Things Every Project Manager Should
Know*](https://www.oreilly.com/library/view/97-things-every/9780596805425/ch34.html)). Over a multi-year
horizon, maintenance and enhancement commonly dominate build cost several times over. (The exact split is
context-dependent — regulated domains trend higher, simple marketing sites lower — so treat specific
percentages as directional.)

That is where LLM-First changes the economics. A conventional application spends most of its life
maintaining **hand-authored operational logic** — routes, CRUD, workflow branches, enumerated rules. In
the systems profiled here, that operational logic is **~70–85% of the hand-authored surface**; only a
**~15–30% "plumbing floor"** (auth, billing, secrets, row-level security) is truly irreducible. When the
operational logic moves to **blueprints compiled to governed reasoning**, the thing you maintain changes
from thousands of branchy lines to a much smaller set of declarative blueprints plus a governed compiler
— and the enhancement tax (the expensive 60%) drops with it.

Concretely, the four systems span a wide surface to convert:

| System | Hand-authored scale | Operational logic (compile target) |
|---|---|---|
| Today Series | ~9.9k LOC, 19 pages / 11 routes | ~70–80% |
| Relic Wars | ~19k LOC (algorithmic engine) | ~80–90% — but *algorithmic*, the contrast case |
| Zabble | ~33k LOC, 65 tables, 234 RPCs | ~70–80% (ceilinged by safety/payments) |
| Eikon Digital | **~350k LOC**, 178 pages / 179 routes, 132 tables | ~75–85% — the largest delta |

The per-system before/after TCO estimates live in each case study. The through-line: **LLM-First's
payoff is not faster typing — it is a smaller thing to maintain for a decade.**

## 3. LLM-authored code — quality, security, and the HITL orchestrator

Every line in these systems was written by an LLM. Rob is the engineer acting as **human-in-the-loop
orchestrator**, not a typist. That is a strength only if it is governed, because the published evidence
on ungoverned LLM code is not flattering:

- **Maintainability is degrading in the wild.** GitClear's analysis of 211M changed lines (2020–2024)
  found duplicated code blocks rising sharply, "moved" (refactored) code falling from ~24% to ~9.5% of
  changes, and short-lived churn climbing from 3.1% to 5.7% as AI assistants were adopted ([GitClear
  2025](https://www.gitclear.com/the_ai_code_quality_maintainability_gap)) — vendor data, correlational,
  but the largest dataset available.
- **Security defaults are weak.** Veracode's 2025 GenAI code-security study found models chose the
  *insecure* implementation in roughly **45%** of security-relevant tasks, with cross-site-scripting and
  log-injection classes among the worst ([Veracode 2025](https://www.veracode.com/blog/genai-code-security-report/)).
- **Speed is often an illusion.** In a randomized trial, experienced open-source developers were **~19%
  slower** with AI tools while *believing* they were ~20% faster ([METR RCT,
  2025](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)); Google's DORA 2024
  report associated AI adoption with a **−7.2%** hit to delivery stability, attributed to larger batch
  sizes ([DORA 2024](https://dora.dev/research/2024/dora-report/)).

Against a defect baseline of **15–50 defects per KLOC** for typical development ([McConnell](https://stevemcconnell.com/articles/gauging-software-readiness-with-defect-tracking/)),
this says one thing clearly: **LLM output is a draft, not a deliverable, until something enforces
quality and security.** The answer in these systems is a layered gate stack, not vibes:

- **Pre-commit guards** — a chained set of static gates (endpoint-lock, a **no-stubs / no-mocks**
  gate, blueprint-lint, a public-view protocol, a legacy-chain guard, and a content-truth check), some
  wired to run on every lint.
- **CI enforcement** — typecheck → lint → unit tests → build, plus a hard **service-role-key guard**
  that fails the build if a privileged secret is referenced outside its one sanctioned module, an
  ephemeral database that runs **pgTAP** tests, and SQL linting.
- **Row-level-security discipline** — an RLS-audit skill, and in one system a database trigger that
  **auto-enables RLS on every new table** so a forgotten policy cannot ship.
- **Audit-style remediation cycles** — numbered security findings closed in tracked batches
  (**F-01…F-08** in one system, **F-01…F-12** in another), plus IDOR/authorization fixes and
  committed-secret cleanup — the pattern of an external audit, run continuously and closed by the HITL.
- **"If I reverted every file I just changed, would any production behavior change?"** — the literal
  test a post-implementation audit applies before work is accepted, so nothing ships stubbed or unwired.

The claim is not "LLMs write good code." It is: **governed LLM code, held to these gates by a
disciplined orchestrator, is a deliverable — and the governance is the product.**

## 4. Governing an LLM inside a harness you don't own

There is a structural fact people miss: when you build with Claude.ai Max — in the CLI, desktop app,
browser, or mobile — **you are governing a model inside someone else's harness.** You cannot modify the
runtime. Governance is therefore **cooperative and always-on**, or it does not exist.

This is why "prompt-only governance" fails, and these systems say so explicitly in their own rules:
instructions are not enforcement. What works is a **cooperative overlay** that re-asserts itself every
session because the substrate underneath is not yours:

1. **Session-start mandates** that assert an authority hierarchy and pre-edit reconciliation steps.
2. **Tool-call hooks** (adoption-check, ungoverned-reminder, governance-disable, context-enrichment)
   that wrap the model's actions rather than trusting its intentions.
3. **A pre-implementation architecture-fit check** and **a post-implementation drift audit**, with a
   **self-heal** loop bounded by a hard iteration cap before it fails loudly.

The reason this matters beyond craft is **compliance and regulation.** The moment governed reasoning
touches regulated data or decisions, "the AI did it and we can't say why" is not an acceptable answer.
The properties in [`THESIS.md`](./THESIS.md) — bounded, evidence-backed, audited, reversible — are
exactly what a compliance regime asks for, and the reason this work started: the problems that made
run-time reasoning unsafe to depend on a year ago are **still present in today's models.** Better models
have not removed the need for governance; they have raised the stakes of not having it. Category standards
make the bar concrete — [OWASP Top 10:2025](https://owasp.org/Top10/2025/) (broken access control is
still #1), the [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/) (prompt
injection, excessive agency, vector isolation), and [PCI DSS 4.0](https://www.pcisecuritystandards.org/document_library/)
for anything near payments.

## 5. Drift, and the harness-injection problem

Two failure modes recur, both rooted in the same cause: **the model was trained overwhelmingly on
traditional, code-first software,** so its instincts pull toward code-first even when the target is a
governed substrate.

**Code-first drift.** Left alone, the model expresses product meaning as TypeScript, enums, config maps,
route folders, and static rosters — the very anti-pattern LLM-First exists to avoid. The counter is a
dedicated, versioned drift-detection stack: a **code-first-drift agent** with a signal table that runs
before *and* after every change, an **architecture-fit agent** that checks work is matrix-first /
NLUI-first / evidence-backed / runtime-compiled *before* it is written, a documented drift taxonomy
(CFD-01…CFD-14), and a runtime scanner with an externalized rule set. Drift remediation shows up as a
recurring maintenance category in the commit history — it is a real, ongoing cost, not a one-time fix.

**Harness-injection — the sharper, less obvious one.** When the model builds the *local governance
harness itself* — the skills, agents, hooks, and instructions — it tries to smuggle that harness logic
into the **application's own schema and code**: authority-bearing classes named after agents, NLUI
"tools" that mirror human workflow tasks, harness behavior migrated into the database. The guardrails
name this exactly ("harness is not authority"; "local scripts are evidence sources, never authority";
a "tool-posture test" that stops you from creating an app tool that mirrors a task). The cleanest
public-safe evidence that it happens is a database migration whose name is, literally, a *purge of
harness drift that had reached the schema* — caught and reversed.

The lesson is not "the model is bad." It is that **governing an LLM-first build is an active,
adversarial-in-your-own-favor discipline**: the harness and the product must be kept separate, and the
tooling to enforce that separation is itself part of the substrate. That local harness — how it detects
drift, keeps itself out of the product, and closes findings — is where a year of this work actually
lives. Its internals are proprietary; its *shape* is described here, and it is the real reason the
case-study conversions are credible rather than aspirational.

---

## References

Primary, citable anchors used above:

- Software maintenance as majority lifetime cost — [O'Reilly, "The 60/60 Rule"](https://www.oreilly.com/library/view/97-things-every/9780596805425/ch34.html)
- Defect-density baselines — [Steve McConnell](https://stevemcconnell.com/articles/gauging-software-readiness-with-defect-tracking/)
- LLM code maintainability — [GitClear 2025 (AI code quality & maintainability)](https://www.gitclear.com/the_ai_code_quality_maintainability_gap) · [research PDF](https://gitclear-public.s3.us-west-2.amazonaws.com/GitClear-AI-Copilot-Code-Quality-2025.pdf)
- LLM code security — [Veracode 2025 GenAI Code Security Report](https://www.veracode.com/blog/genai-code-security-report/)
- Productivity RCT — [METR, 2025](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) · [paper](https://arxiv.org/abs/2507.09089)
- Delivery outcomes — [DORA 2024 State of DevOps](https://dora.dev/research/2024/dora-report/)
- Web app security — [OWASP Top 10:2025](https://owasp.org/Top10/2025/)
- LLM app security — [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/)
- Payments compliance — [PCI DSS 4.0](https://www.pcisecuritystandards.org/document_library/)
- Content provenance — [C2PA / Content Credentials](https://c2pa.org/)
- Server-authoritative game architecture — [Gambetta, Client-Server Game Architecture](https://www.gabrielgambetta.com/client-server-game-architecture.html)

*Codebase metrics (LOC, routes, migrations, tables, RLS policies, test surface) were measured directly
from the author's own repositories. Figures for not-yet-built conversions are labeled estimates
throughout. No proprietary BOSNet.io / BOSGov internals, secrets, project identifiers, or client names
appear in this document.*

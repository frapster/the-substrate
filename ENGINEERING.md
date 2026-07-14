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
  2025](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)) — a narrow result
  about AI-assisted *coding* rather than architecture, but a pointed one. And Google's **DORA** program
  associated AI adoption with a delivery-stability hit in 2024; in fairness, the *throughput* half of
  that finding **reversed in the 2025 report** (AI now correlates positively with throughput) while the
  **instability persisted** — DORA's own synthesis is that AI is an *amplifier* of a team's existing
  quality ([DORA 2024](https://dora.dev/research/2024/dora-report/), [DORA
  2025](https://dora.dev/dora-report-2025/)). That "amplifier" framing is the argument for governance,
  not against it: AI magnifies whatever discipline — or absence of it — is already there.

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

But be honest about the ceiling of this approach: **a governance overlay is only as good as two things
staying true** — that the harness beneath it *hasn't changed* (a third-party runtime you don't control
can shift under you between sessions, silently invalidating an assumption your governance rested on), and
that you *didn't forget to invoke it* (a rule not loaded into context, a hook not registered, a check
not called is simply not enforced — **omission is ungoverned**). **Managing drift dies here first** —
not in the code, but at the seams of the overlay itself: the un-invoked hook, the silently-changed
harness. Governance-by-invocation is fragile precisely because it depends on remembering, every time.

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

## 5. Drift — code, harness, and knowledge

Drift takes three forms here. The first two share a cause — **the model was trained overwhelmingly on
traditional, code-first software**, so its instincts pull toward code-first even when the target is a
governed substrate. The third has nothing to do with code at all, and it is the deepest.

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

**Knowledge drift — the deepest one.** Drift is not always about code. A model fails just as surely when
the *data it consumes* is wrong, stale, or missing — fed without the context a decision actually requires.
Prompts and hooks govern *what the model may do*; they do nothing about *what the model knows when it does
it*. The remedy is not more retrieval — it is feeding the model the right context from a
**governance-carrying dimensional matrix**: knowledge that is itself bounded, evidence-backed, and
versioned, so the context is correct *by construction* rather than by lucky recall.

Say this precisely, because it is easy to overstate. The problem is not *retrieval* — it is **naive
vector-similarity retrieval over an open corpus with no provenance.** Similarity returns what is *near*,
not what is *governed and true*, and the failure modes are documented: retrieved context does not
eliminate hallucination ([RAGTruth, ACL 2024](https://arxiv.org/abs/2401.00396)); retrieval has a whole
taxonomy of ways to surface the wrong or missing passage ([Seven Failure Points](https://arxiv.org/abs/2401.05856));
models degrade on facts buried mid-context *even when the right passage was retrieved* ([Lost in the
Middle, TACL 2024](https://arxiv.org/abs/2307.03172); [context length hurts despite perfect retrieval,
2025](https://arxiv.org/abs/2510.05381)); and every retrieved third-party document is an injection
surface ([indirect prompt injection](https://arxiv.org/abs/2302.12173); [OWASP
LLM08:2025](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/)).

The fix is a better *index*, not the absence of retrieval: structured, provenance-carrying knowledge
that supports auditable multi-hop traversal rather than black-box nearest-neighbor — the direction
Microsoft's [GraphRAG](https://arxiv.org/abs/2404.16130) validates for global and relational questions.
Two honest caveats keep this from being dogma: structured knowledge is *itself* a form of retrieval
under the field's taxonomy ([GraphRAG survey](https://arxiv.org/abs/2501.00309)), and it is not free —
it can *lose* to plain vector search on fine-grained factoid lookups and costs more to build and serve
([RAG vs. GraphRAG](https://arxiv.org/abs/2502.11371)), and graphs degrade under incomplete coverage
([What Breaks KG-RAG](https://arxiv.org/abs/2508.08344)). So the rule is *right index per query class*:
similarity search is fine for open factoid lookup; governed, structured knowledge is the substrate for
anything a decision must be **accountable** for.

This points at the real definition. **The operational substrate of an LLM is governance *plus* knowledge —
not code.** Code is what you write when you lack the other two. Governance bounds what the model may do;
the dimensional knowledge model determines what it correctly *knows*; together they *are* the substrate.
Drift is the erosion of either half — a rule left un-invoked, a harness that shifted beneath you, or
context fed wrong — and managing it means holding **both** halves continuously, not just guarding the code.

The lesson is not "the model is bad." It is that **governing an LLM-first build is an active,
adversarial-in-your-own-favor discipline**: the harness and the product must be kept separate, and the
tooling to enforce that separation is itself part of the substrate. That local harness — how it detects
drift, keeps itself out of the product, and closes findings — is where a year of this work actually
lives. Its internals are proprietary; its *shape* is described here, and it is the real reason the
case-study conversions are credible rather than aspirational.

## 6. Objections we take seriously

A thesis is only as strong as the objections it survives. These are the sharpest ones, stated fairly:

**"Compounding error dooms run-time reasoning."** If each step is less than perfectly reliable, chaining
steps decays fast — 99% per step is ~37% over 100 steps — and models *self-condition* on their own
earlier mistakes, so more reasoning hops means multiplicatively more failure ([agent-evaluation
survey](https://arxiv.org/abs/2507.21504); [where agents fail](https://arxiv.org/abs/2509.25370)). A
90:10 target looks like it *maximizes* those terms. **Our answer:** breaking that multiplication is the
envelope's entire job. A deterministic auditor re-derives ground truth and **discards** any step that
fails — per-step correctness is *enforced by code*, not left to the model to decay; agency is
**concentrated** (Relic Wars governs ~8 decisions per snap, not 100); and a rejected inference is thrown
away, never fed back to compound. Governance converts an exponentially decaying chain into gated,
independently verified steps. Where a step *cannot* be capped or checked, it belongs in code — which is
exactly why the ratio is a design decision, not a mandate to maximize AI.

**"'Governance + knowledge, not code' is a false trichotomy."** Governance rules and knowledge models are
themselves authored, versioned, executed artifacts — that is [policy-as-code](https://www.pulumi.com/what-is/what-is-policy-as-code/) —
and structured retrieval is still retrieval ([GraphRAG is a *variant* of
RAG](https://arxiv.org/abs/2501.00309)). So the dichotomy may be rhetorical. **Our answer:** we don't
claim code disappears. We claim two specific shifts: the *locus of authored truth* moves from imperative
business logic to **declarative, evidence-backed, governed artifacts**, and *decision execution* moves
from write-time to **run-time reasoning inside the envelope**. That is a real difference in *what you
maintain* and *when decisions are made* — even though blueprints and policies are authored. Declarative
config plus a policy engine plus a non-vector index is *part* of it; the run-time governed reasoning and
the evidence/audit spine are the rest. We'd rather say that precisely than oversell a slogan.

**"Structure doesn't always pay."** A systematic evaluation finds graph/structured knowledge can *lose*
to plain vector RAG on fine-grained factoid queries and costs more to build and serve ([RAG vs.
GraphRAG](https://arxiv.org/abs/2502.11371)); knowledge graphs degrade under incomplete coverage ([What
Breaks KG-RAG](https://arxiv.org/abs/2508.08344)). **Our answer:** agreed — that is the *right-index-per-
query-class* rule from §5. Governed structure is for what must be **accountable** (relational, multi-hop,
auditable, regulated); similarity search is fine for open factoid lookup. Paying graph cost for a factoid
lookup would be the mistake.

**On the 90:10 number.** It is a **design aspiration, not an empirical finding.** No study shows a
specific optimal AI:code ratio, and the reliability literature above argues the safe default is
"deterministic where correctness is load-bearing, reasoning where flexibility is." We present 90:10 as
the target BOSNet.io reaches for and each project approaches *honestly* — Zabble stays near 30–40,
Relic Wars' whole game stays low — a measured north star, not a claim of proven optimum.

## 7. Governance that frees, not fences

A claim runs through this work that sounds soft but is testable, and it is where the thesis starts:
**governing AI begins with governing people — and safe, governed tools *free* people to work rather than
constrain them.** It earns the same evidence-and-objection treatment as everything else.

**The support.** The strongest evidence comes from the DevOps research program itself: heavyweight,
external change-approval boards do *not* lower failure rates and *do* slow delivery, while lightweight
peer-review guardrails correlate with better throughput *and* stability — "responding to problems by
adding more process" makes things worse ([DORA, streamlining change
approval](https://dora.dev/capabilities/streamlining-change-approval/)). Platform engineering's "golden
paths" are the same idea made concrete: opinionated-but-*optional* defaults that cut cognitive load and
setup time so people spend their creativity on higher-value work ([Spotify Golden
Paths](https://engineering.atspotify.com/2020/08/how-we-use-golden-paths-to-solve-fragmentation-in-our-software-ecosystem)).
The motivation research explains *why*: autonomy is not the absence of structure but *ownership of one's
action*, so good constraints can raise felt autonomy rather than lower it ([Self-Determination Theory,
Ryan & Deci](https://selfdeterminationtheory.org/SDT/documents/2000_RyanDeci_SDT.pdf)), and a climate
that feels *safe* is the top predictor of team performance ([Edmondson, psychological
safety](https://journals.sagepub.com/doi/10.2307/2666999)). The AI-governance standards agree on where
governance *starts*: NIST's AI RMF makes **GOVERN** a culture-and-people function that enables the others
([NIST AI RMF](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)), and ISO/IEC 42001 implements
AI governance as a *human* management system ([ISO 42001](https://www.iso.org/standard/42001)).

**The honest challenge.** This is true only under conditions, and the same research names them. The 2024
DevOps report found that platform engineering, run badly, can *cost* throughput and stability — a
transition-phase "platform paradox" ([DORA 2024](https://dora.dev/research/2024/dora-report/)). Golden
paths free people only while they stay *optional*; the moment they are mandated they become railroads
that breed resentment and shadow IT. And "governance" branded as surveillance erodes trust and *reduces*
the productivity it claims to protect ([HBR, 2024](https://hbr.org/2024/02/surveilling-employees-erodes-trust-and-puts-managers-in-a-bind)).
The sharpest form of the objection is a motte-and-bailey: "good guardrails help" is nearly tautological,
and much of the supporting evidence is self-reported by the teams who built the platform. So the claim
must carry its conditions: **governed tools free people when the framework is *paved, not fenced*** —
product-managed, optional where it can be, safe-by-default, and built to remove friction rather than to
watch the worker. That is the bar this work holds itself to. It is not automatic, and saying so is part
of the discipline.

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
- Delivery outcomes, updated — [DORA 2025 State of DevOps](https://dora.dev/dora-report-2025/) (2024 throughput hit reversed; instability persists; AI as "amplifier")

*Knowledge & retrieval:* [RAGTruth (ACL 2024)](https://arxiv.org/abs/2401.00396) ·
[Seven Failure Points of RAG](https://arxiv.org/abs/2401.05856) ·
[Lost in the Middle (TACL 2024)](https://arxiv.org/abs/2307.03172) ·
[Context length hurts despite perfect retrieval (2025)](https://arxiv.org/abs/2510.05381) ·
[GraphRAG](https://arxiv.org/abs/2404.16130) · [GraphRAG survey](https://arxiv.org/abs/2501.00309) ·
[RAG vs. GraphRAG](https://arxiv.org/abs/2502.11371) · [What Breaks KG-RAG](https://arxiv.org/abs/2508.08344) ·
[Indirect prompt injection](https://arxiv.org/abs/2302.12173) ·
[OWASP LLM08:2025 Vector & Embedding Weaknesses](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/)

*Reliability & counter-evidence:* [Agent-evaluation survey](https://arxiv.org/abs/2507.21504) ·
[Where LLM agents fail](https://arxiv.org/abs/2509.25370) ·
[Policy-as-code](https://www.pulumi.com/what-is/what-is-policy-as-code/)

*People & process governance:* [DORA — streamlining change approval](https://dora.dev/capabilities/streamlining-change-approval/) ·
[Spotify Golden Paths](https://engineering.atspotify.com/2020/08/how-we-use-golden-paths-to-solve-fragmentation-in-our-software-ecosystem) ·
[Self-Determination Theory (Ryan & Deci)](https://selfdeterminationtheory.org/SDT/documents/2000_RyanDeci_SDT.pdf) ·
[Edmondson, psychological safety](https://journals.sagepub.com/doi/10.2307/2666999) ·
[NIST AI RMF (GOVERN)](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/) ·
[ISO/IEC 42001](https://www.iso.org/standard/42001) ·
[HBR — surveillance erodes trust](https://hbr.org/2024/02/surveilling-employees-erodes-trust-and-puts-managers-in-a-bind)

*Codebase metrics (LOC, routes, migrations, tables, RLS policies, test surface) were measured directly
from the author's own repositories. Figures for not-yet-built conversions are labeled estimates
throughout. No proprietary BOSNet.io / BOSGov internals, secrets, project identifiers, or client names
appear in this document.*

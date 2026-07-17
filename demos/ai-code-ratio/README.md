# demo — the AI:code ratio, made countable

A small, **zero-dependency** proof of the measurable spine `the-substrate` claims in prose:
the **AI : code ratio** — how much operational behavior is carried by governed, run-time
facts versus hand-authored, write-time code (see [`../../README.md`](../../README.md) and
[`../../THESIS.md`](./../../THESIS.md)).

One small feature — support-ticket routing — is built **twice**: once as a hand-authored
`if/elif` tree, once as a generic evaluator reading a fact table. Then the requirement
grows by three new cases, and the cost to each is **counted for real**, via Python's
stdlib `ast` module parsing the actual source — not estimated, not asserted.

You should be able to clone the repo and see it work in under a minute. No `pip install`,
no build — Python 3 standard library only.

## Quickstart (30 seconds)

```bash
python demos/ai-code-ratio/ratio_demo.py
```

You'll watch the two implementations agree on the base requirement (9 tickets), then watch
three new business cases cost the code path new branches and the governed path new fact
rows:

```
2. Three new cases arrive (critical severity)
  code_version.py    (ast-counted): 9 branches, 30 decision LOC
  code_version_v2.py (ast-counted): 12 branches, 33 decision LOC
  code path: +3 branches / +3 LOC (a developer wrote, reviewed, and shipped this)

  ✓ governed path: +0 evaluator LOC / +3 fact rows (governed_version.py is the same file, untouched)

  Headline: 3 new cases → code +3 branches / +3 LOC; governed +0 LOC / +3 facts.
```

Then it runs the **revert-the-fact litmus** — remove one fact row and the governed
decision reverts, with `governed_version.py`'s source unchanged — and shows the fail-closed
contrast: on a ticket no fact governs, the governed path abstains (`hitl_required`); the
unmodified code path silently returns a default with no signal it was guessing.

## Run the tests

```bash
python demos/ai-code-ratio/test_ratio.py
# or:  python -m unittest discover -s demos/ai-code-ratio
```

The assertions that matter: the branch-delta count comes from `ast`, not a hardcoded
number; the "governed evaluator LOC delta is zero" claim is checked by construction
(`evaluate()` is the same function object called against a 9-row and a 12-row table); and
the revert-the-fact litmus is checked in both directions.

## How it works

- [`code_version.py`](./code_version.py) — the base feature (9 cases: 3 plan tiers ×
  3 severities) as a hand-authored `if/elif` chain. Includes `count_branches()` and
  `count_decision_loc()`, which parse the file's own `route_ticket()` source with `ast`
  to produce an honest, non-fabricated count of its own decision tree.
- [`code_version_v2.py`](./code_version_v2.py) — the same feature after three new
  business cases (critical severity) were added as three new branches. A separate file,
  not an in-place edit, so `ratio_demo.py` diffs two real files instead of simulating a
  change.
- [`facts.py`](./facts.py) — the fact table: `BASE_FACTS` (9 rows, one per base case) and
  `NEW_FACTS` (3 rows, the growth scenario). This is where the feature's *meaning* lives —
  which tier+severity combination maps to which queue and escalation.
- [`governed_version.py`](./governed_version.py) — the one generic evaluator. It reads
  whatever fact table it's given and resolves a ticket's outcome; it has no per-case
  logic and does not change when facts are added, removed, or reverted. If no fact
  matches, it fails closed and returns `hitl_required` instead of guessing.
- [`ratio_demo.py`](./ratio_demo.py) — the narrative runner above.
- [`test_ratio.py`](./test_ratio.py) — `unittest` suite, including the litmus and
  fail-closed cases.

## What this proves — and what it does NOT

**Proves:** for *this one small feature*, growing the requirement by three cases costs the
hand-authored version new branches and new lines of code (counted via `ast`, not asserted),
while it costs the governed version new fact rows and zero evaluator code change. It also
proves the fail-closed contract holds — an ungoverned input makes the governed path abstain
(`hitl_required`) rather than silently guess — and that reverting a fact row reverts
behavior with the evaluator's source unchanged (the "revert-the-fact litmus"). These are
real, checkable properties, demonstrated by code you can run.

**Does NOT prove / is NOT:**

- **This is one small, illustrative feature, not a measurement of a whole system.** It is
  not a benchmark of BOSNet.io, not the matrix-first evaluator described in
  [`../../BOSS-STANDARD.md`](../../BOSS-STANDARD.md), and it contains none of that engine's
  schema, kernel, or reasoning pipeline. `governed_version.py`'s `_reasoning_step()` is a
  **mocked, deterministic stand-in** for the bounded, evidence-checked run-time reasoning a
  real governed system performs — there is no model call here.
- **The 90:10 LLM-First target is a design aspiration, not an empirical finding.** This demo
  does not claim any system achieves 90:10; it shows, for one feature's growth, where new
  requirement *meaning* landed — 100% in facts on the governed side, 100% in hand-authored
  branches on the code side. Extrapolating that ratio to a whole application is exactly the
  kind of claim [`../../ENGINEERING.md`](../../ENGINEERING.md) §6 ("Objections we take
  seriously") argues against making without evidence.
- **The branch/fact symmetry here (3 new cases → 3 new branches → 3 new facts) is a property
  of this toy feature, not a law.** Real features vary: some new requirements cost several
  branches per case (nested conditionals) or several facts (compound conditions); the point
  demonstrated is *where the cost lands* (code vs. data), not a fixed ratio.
- **Not a benchmark.** There is no `bench.py` here — this demo is about where meaning lives,
  not throughput. See [`../audit-ledger/`](../audit-ledger/) for the demo with a reproducible
  benchmark.

See [`../../BOSS-STANDARD.md`](../../BOSS-STANDARD.md), [`../../LICENSE.md`](../../LICENSE.md),
[`../../THESIS.md`](../../THESIS.md), and [`../../ENGINEERING.md`](../../ENGINEERING.md) for
the proprietary standard this toy is a public-safe, clean-room illustration of.

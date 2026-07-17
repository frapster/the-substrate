# demo: a deterministic validator that commits only what passes

A small, **zero-dependency** proof of the decision recorded in
[`../../docs/adr/ADR-0003-deterministic-validator-commits.md`](../../docs/adr/ADR-0003-deterministic-validator-commits.md):
**deterministic code computes what does happen and grades the reasoning; the model decides
what should happen; a deterministic validator commits only what passes.** A rejected
inference is **discarded, not patched**: the system never silently repairs a bad proposal
into a passing one.

You should be able to clone the repo and see it work in under a minute. No `pip install`,
no build. Python 3 standard library only.

## Quickstart (30 seconds)

```bash
python demos/deterministic-validator/validator_demo.py
```

You'll watch a valid, grounded proposal commit, then a proposal that cites a source that
doesn't exist get discarded: watch its source id stay exactly as hallucinated, because
nothing repairs it, and then a batch of six proposals run through the gate:

```
3. A batch of proposals
  [commit] grant_refund citing src_102, $120  passes all checks
  [commit] escalate_ticket citing src_103, $0  passes all checks
  [discard] grant_refund citing src_777, $90  cited source 'src_777' does not exist in known sources
  [discard] grant_refund citing src_104, $5000  amount_usd 5000 exceeds policy bound 500
  [discard] <missing intent> citing src_101, $50  missing required field: intent
  [discard] grant_refund citing src_102, $-10  amount_usd -10 must not be negative

  4 bad proposals: 4/4 discarded (not patched)
  commit_log holds only validated proposals: 3 rows
  rejected_log holds every discard with its reason: 5 rows
```

That last moment, the gate holding under a mixed batch with every discard recorded and
none repaired, is the whole point.

## Run the tests

The negative tests are the interesting ones: they assert `validate()` *fails*, for the
right reason, under a hallucinated citation, an out-of-bound amount, a negative amount,
and a missing field, and that an approving `llm_judge()` opinion cannot commit a proposal
on its own.

```bash
python demos/deterministic-validator/test_validator.py
# or:  python -m unittest discover -s demos/deterministic-validator
```

## How it works

```
model.propose(intent)  ->  Proposal
Validator.validate(Proposal)  ->  CheckResult(ok, reason)   # deterministic, no model call
  ok  -> commit_log.append(proposal)      # verbatim, no mutation, no repair
  !ok -> rejected_log.append(proposal, reason)   # discarded, not patched
```

`validate()` is plain, hand-written code: does the cited source exist in a known set, is
the amount within a policy bound, are required fields present. Nothing probabilistic sits
on the commit path. A mocked `llm_judge()` is included to model the tempting alternative:
using a second model as the gate, and a test proves it explicitly: an approving judgment
attached to a bad proposal still gets discarded, because `submit()` never reads `Judgment`
at all. The judge can feed evidence; it cannot be the validator.

- [`validator.py`](./validator.py): `Proposal`, `Validator.validate()`, `Validator.submit()`, the mocked `propose()` and `llm_judge()`.
- [`validator_demo.py`](./validator_demo.py): the narrative runner above.
- [`test_validator.py`](./test_validator.py): `unittest` suite, including the rejection and judge-boundary cases.

## What this proves, and what it does not

**Proves:** a deterministic gate (a small set of real, checkable rules with no model call
in the check itself) can sit between a model's proposal and a commit log, admit only what
passes, and leave a recorded (not hidden) trace of every discard. This is a real, checkable
property, demonstrated by code you can run.

**Does NOT prove / is NOT:** this is a **generic gate primitive**, distinct from the
BOSNet.io engine or kernel. It is not a full governance runtime; the rules here (`KNOWN_SOURCE_IDS`,
`MAX_AMOUNT_USD`) are invented toy policy, distinct from a real schema or spec. The proprietary
reference implementation (the actual validator seams, evidence sources, and policy) is
described in [`../../BOSS-STANDARD.md`](../../BOSS-STANDARD.md) and remains patent-pending
and reserved (see [`../../LICENSE.md`](../../LICENSE.md)). A deterministic gate bounds
*admissibility*; it does not guarantee *quality of intent*: a proposal can pass every check here and still be
a bad idea if the knowledge feeding the model was wrong: see
[`../../docs/adr/ADR-0003-deterministic-validator-commits.md`](../../docs/adr/ADR-0003-deterministic-validator-commits.md).

# demo: governed knowledge vs. naive similarity retrieval

A small, **zero-dependency** proof of one claim in [`../../docs/adr/ADR-0005-rag-is-not-the-substrate.md`](../../docs/adr/ADR-0005-rag-is-not-the-substrate.md):
that naive retrieval-by-cosine-similarity is a useful retrieval *tactic*, not the
governed-knowledge *substrate*. A governance engine can authorize an action correctly
and still be wrong, if it reasons over a fact that used to be true. See
[`../../ENGINEERING.md`](../../ENGINEERING.md) for the fuller argument.

You should be able to clone the repo and see it work in under a minute. No `pip install`,
no build. Python 3 standard library only.

## Quickstart (30 seconds)

```bash
python demos/governed-knowledge/knowledge_demo.py
```

You'll watch a naive cosine-similarity search confidently return a **superseded**
refund-policy fact, with a similarity score that really is the highest in the
knowledge base, and then watch a governed retriever, given the identical query,
return the **current** policy instead. A second query then shows the governed
retriever **abstain** rather than guess, when nothing current clears its confidence
threshold:

```
2. Naive similarity search: "What is the refund window after a purchase?"
  [naive_retrieve] returns atom_refund_v1 (cosine=0.858), superseded 2025-12-31
    "Refund window is 30 days after purchase, no exceptions."

3. Governed retrieval: the SAME query, scope="platform"
  [governed_retrieve] returns atom_refund_v2 (cosine=0.678), current
    "Refund window is 14 days after purchase; platinum-tier customers retain a 30-day exception window."

4. Governed retrieval: "What is the warranty period?" (scope="platform")
  [governed_retrieve] degraded=True
    reason: best current, in-scope match scored 0.000, below threshold 0.500, abstaining rather than guessing
```

## The fairness point (read this before you doubt the result)

**The similarity function is a correct, unmodified cosine.** `atom_refund_v1` (the
superseded atom) genuinely scores *higher* against the query than `atom_refund_v2`
(the current atom): 0.858 vs. 0.678. That is not a bug or a rigged retriever: a
deprecated fact is often phrased more simply and more closely to how an old query was
worded, while the current fact carries extra qualifying language (here, a platinum-tier
exception clause) that dilutes its lexical/embedding closeness to a plain-language
query. `test_knowledge.py`'s `Fairness` test class asserts this directly:
`sim(query, stale_atom) > sim(query, current_atom)`, for all three supersession pairs
in the knowledge base (refund window, password policy, data retention).

**Governed knowledge wins on currency and provenance, and not on a rigged retriever.**
`naive_retrieve` searches the entire knowledge base and returns whatever scores
highest, indifferent to whether that atom is still true or whether the caller is even
authorized to see it. `governed_retrieve` filters to atoms that are **current**
(`validity_end is None`) and in an **authorized scope** *before* it ever ranks by
similarity, so a superseded or out-of-scope atom cannot outrank a current, authorized
one, no matter how textually close it is to the query. And if nothing current and
authorized clears the similarity threshold, it **abstains** (`degraded=True`, with a
human-readable `reason`) instead of serving its best guess as if it were fact.

**A candid limitation:** the embeddings here are illustrative toy vectors:
16-dimensional, hand-authored tuples of plain floats, chosen to make the fairness
property hold and easy to inspect. They are *not* the output of a real embedding
model. The cosine math applied to them is real and unmodified; production knowledge
retrieval would use a real embedding model over real text, but the mechanism
demonstrated here (filter-then-rank, plus abstain-on-uncertainty) is unchanged by
that substitution.

## Run the tests

```bash
python demos/governed-knowledge/test_knowledge.py
# or:  python -m unittest discover -s demos/governed-knowledge
```

The `Fairness` class is the load-bearing test: if it ever failed, the whole demo would
be a strawman. The rest assert that `naive_retrieve` returns the stale atom, that
`governed_retrieve` returns the current atom for every supersession pair, that it
abstains when no current atom clears the threshold, and that it abstains when the
requested scope isn't a registered/authorized retrieval channel.

## Run the benchmark

```bash
python demos/governed-knowledge/bench.py            # default K = 3,000 trials
python demos/governed-knowledge/bench.py 10000       # custom trial count
```

Each trial restates one of the three seeded supersession queries with small random
jitter, so trials aren't bit-identical repeats. Sample run (Python 3.13, a 2020-class
laptop; **your numbers will vary, regenerate with the command above**):

| Metric | Result |
|---|---|
| Trials (K) | 3,000 |
| naive_retrieve returned the STALE atom | 3000/3000 (100.0%) |
| governed_retrieve returned the CURRENT atom | 3000/3000 (100.0%) |
| governed_retrieve abstained (degraded) | 0/3000 (0.0%) |
| governed_retrieve correct-or-safe (current ∪ abstain) | 3000/3000 (100.0%) |
| governed_retrieve WRONG (stale or off-scope) | 0/3000 |

## How it works

- An **Atom** is one versioned fact: `atom_id`, `body`, `embedding`, `scope`
  (`"platform"` or a tenant channel), `provenance`, and a validity window
  (`validity_start` / `validity_end`: `validity_end is None` means current).
- **`naive_retrieve(query_embedding)`**: correct cosine search over every atom in the
  knowledge base, blind to currency and scope.
- **`governed_retrieve(query_embedding, scope, threshold)`**: filters to current
  atoms in an authorized scope, ranks by cosine, and abstains (`degraded=True`) if
  nothing qualifies or nothing clears `threshold`.
- **Supersession** is expressed forward: `KnowledgeBase.supersede()` closes the old
  atom's `validity_end` and appends a new atom; the old atom's text is never edited
  in place, only its validity window is closed.

```
score = cosine(query_embedding, atom.embedding)
naive_retrieve    = argmax(score) over ALL atoms
governed_retrieve = argmax(score) over {atoms : current AND scope authorized}
                     (or degrade if that set is empty or its best score < threshold)
```

- [`knowledge.py`](./knowledge.py): `Atom`, `KnowledgeBase`, `cosine()`, `naive_retrieve()`, `governed_retrieve()`, seed KB.
- [`knowledge_demo.py`](./knowledge_demo.py): the narrative runner above.
- [`test_knowledge.py`](./test_knowledge.py): `unittest` suite, including the fairness assertion.
- [`bench.py`](./bench.py): the reproducible benchmark.

## What this proves, and what it does not

**Proves:** naive similarity search can, and here provably does, return a
superseded fact with a higher similarity score than the current fact, using a
correct, unrigged cosine computation. Filtering to current-and-authorized atoms
*before* ranking, plus abstaining below a confidence threshold, avoids that failure
mode. This is a real, checkable property, demonstrated by code you can run.

**Does NOT prove / is NOT:** this is a **generic retrieval-ranking primitive**, distinct
from BOSNet.io's knowledge model, evidence schema, or coordinate scheme; those are
proprietary and reserved (see [`../../BOSS-STANDARD.md`](../../BOSS-STANDARD.md) and
[`../../LICENSE.md`](../../LICENSE.md)). It is not a production embedding pipeline:
the vectors here are small, hand-authored toy floats chosen to make the fairness
property legible by construction, distinct from the output of a real embedding model. It is not a full
governance runtime: see [`../../docs/adr/ADR-0005-rag-is-not-the-substrate.md`](../../docs/adr/ADR-0005-rag-is-not-the-substrate.md)
for the principle this demo runs, and [`../../ENGINEERING.md`](../../ENGINEERING.md)
for the broader argument this is one piece of.

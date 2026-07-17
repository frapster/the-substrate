"""
knowledge.py — governed knowledge retrieval vs. naive similarity retrieval.

This is a clean-room, dependency-free implementation of the *mechanism* behind
ADR-0005 ("retrieval-by-similarity is not the governed-knowledge substrate", see
../../docs/adr/ADR-0005-rag-is-not-the-substrate.md): a governed model fed the wrong
or missing context still produces wrong outputs — safely authorized, faithfully
audited, and incorrect. What a model correctly *knows* has to rest on an evidence
model where facts are atomic, provenance-tracked, versioned, and reconciled — not
merely "the nearest chunk by embedding distance." It is a generic retrieval-ranking
primitive and contains none of the BOSNet.io knowledge-model schema or coordinate
scheme.

Vocabulary used here echoes the thesis prose without exposing any proprietary
schema: an **Atom** is one versioned fact with a **scope** (platform-wide or a
specific tenant channel), a **validity window** (`validity_start` / `validity_end` —
`validity_end is None` means still current; a set end date means superseded), and
**provenance** (where the fact traces back to). "Expressing supersession forward"
means: when a fact changes, you write a NEW atom with `validity_start` at the change
date and set the OLD atom's `validity_end` — you never silently mutate the old atom
in place.

Two retrievers are provided, and the contrast between them is the whole point:

  - `naive_retrieve`  — a correct cosine-similarity search over ALL atoms, ignoring
    currency and scope. This is what a bare vector-similarity RAG layer does. It is
    not a strawman: the cosine math is real and it is genuinely the best-scoring
    match — see README.md for why a superseded atom can legitimately outscore a
    current one.
  - `governed_retrieve` — filters to CURRENT atoms in an AUTHORIZED scope first,
    THEN ranks by similarity, and ABSTAINS (never guesses) when nothing qualifies.

Standard library only (math, dataclasses, typing). Runs on any Python 3.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

# Scopes registered as authorized retrieval channels. `governed_retrieve` refuses
# to serve an atom for a scope that isn't on this list — an unregistered channel is
# degraded immediately, before any similarity ranking happens. Modeled here as a
# fixed set; a real deployment would resolve this from a tenant registry.
AUTHORIZED_SCOPES = frozenset({"platform", "tenant_acme"})

# Below this cosine score, a current-and-in-scope atom is not considered a confident
# enough match to serve as fact. Below-threshold means "nothing qualifies" — the
# retriever abstains rather than serving its best guess.
DEFAULT_THRESHOLD = 0.5


def cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    """Standard cosine similarity. Returns 0.0 for a zero-magnitude vector rather
    than dividing by zero — an all-zero embedding has no direction to compare."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


@dataclass
class Atom:
    """One versioned fact. `embedding` is a small, hand-authored toy vector (see
    README.md — illustrative floats standing in for a real embedding model's
    output; the cosine math applied to them is real). `validity_end is None` means
    this atom is CURRENT; a set date means it has been SUPERSEDED and stays in the
    KB only as history — express supersession forward, never mutate in place."""

    atom_id: str
    atom_type: str
    body: str
    embedding: tuple[float, ...]
    scope: str
    provenance: str
    validity_start: str
    validity_end: Optional[str] = None

    @property
    def is_current(self) -> bool:
        return self.validity_end is None

    def status(self) -> str:
        return "current" if self.is_current else f"superseded {self.validity_end}"


@dataclass
class RetrievalResult:
    """Outcome of a retrieval call. `degraded=True` means the retriever refused to
    guess — `atom` may still be populated as the best-scoring candidate that failed
    to qualify, purely for display; callers must not treat it as authoritative."""

    atom: Optional[Atom]
    score: float
    degraded: bool = False
    reason: str = ""

    def __bool__(self) -> bool:  # so callers can write `if result:`
        return not self.degraded


@dataclass
class KnowledgeBase:
    """A small store of atoms. There is deliberately no in-place `update()` — the
    sanctioned way to change a fact is to append a new atom and set the old one's
    `validity_end` (supersession), mirroring the append-only discipline used by the
    audit ledger demo."""

    atoms: list[Atom] = field(default_factory=list)

    def add(self, atom: Atom) -> Atom:
        self.atoms.append(atom)
        return atom

    def supersede(self, old_atom_id: str, new_atom: Atom, at: str) -> Atom:
        """Close out `old_atom_id`'s validity window at `at` and add `new_atom` as
        its replacement. This is "expressing supersession forward": the old atom's
        text is never edited, only its validity window is closed."""
        for atom in self.atoms:
            if atom.atom_id == old_atom_id:
                atom.validity_end = at
                break
        return self.add(new_atom)

    # --- naive: correct cosine search, blind to currency and scope ----------------

    def naive_retrieve(self, query_embedding: tuple[float, ...]) -> RetrievalResult:
        """Return the single highest-cosine atom in the ENTIRE knowledge base,
        superseded or current, any scope. This is a legitimate, unmodified
        cosine-similarity search — exactly what a bare vector-similarity RAG layer
        does. It has no notion of currency or authorization to consult."""
        if not self.atoms:
            return RetrievalResult(atom=None, score=0.0, degraded=True, reason="knowledge base is empty")
        best_atom = max(self.atoms, key=lambda a: cosine(query_embedding, a.embedding))
        best_score = cosine(query_embedding, best_atom.embedding)
        return RetrievalResult(atom=best_atom, score=best_score, degraded=False, reason="highest cosine match")

    # --- governed: current + authorized scope first, THEN rank, THEN threshold ----

    def governed_retrieve(
        self,
        query_embedding: tuple[float, ...],
        scope: str,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> RetrievalResult:
        """Filter to CURRENT atoms in an AUTHORIZED scope, rank by cosine, and
        return the top one — UNLESS nothing clears `threshold`, in which case
        abstain (degraded=True) rather than serve a stale or off-topic atom as if
        it were fact."""
        if scope not in AUTHORIZED_SCOPES:
            return RetrievalResult(
                atom=None,
                score=0.0,
                degraded=True,
                reason=f"scope {scope!r} is not a registered/authorized retrieval channel",
            )

        candidates = [a for a in self.atoms if a.is_current and a.scope == scope]
        if not candidates:
            return RetrievalResult(
                atom=None,
                score=0.0,
                degraded=True,
                reason=f"no current atom is registered for scope {scope!r}",
            )

        best_atom = max(candidates, key=lambda a: cosine(query_embedding, a.embedding))
        best_score = cosine(query_embedding, best_atom.embedding)
        if best_score < threshold:
            return RetrievalResult(
                atom=None,
                score=best_score,
                degraded=True,
                reason=(
                    f"best current, in-scope match scored {best_score:.3f}, below "
                    f"threshold {threshold:.3f} — abstaining rather than guessing"
                ),
            )
        return RetrievalResult(
            atom=best_atom,
            score=best_score,
            degraded=False,
            reason="current, in-scope, above threshold",
        )


# --- seed knowledge base -----------------------------------------------------------
# Toy embeddings, 16 dims, hand-authored (NOT produced by a real embedding model —
# see README.md). Dims are organized as disjoint topic blocks so each fact pair only
# activates its own block; zeros elsewhere. Three supersession pairs (refund window,
# password policy, data retention) plus two atoms with no stale counterpart
# (shipping, a tenant-scoped fact) round out the KB.
#
# dims: 0 refund      1 window      2 days30    3 days14   4 purchase
#       5 platinum     6 shipping    7 warranty
#       8 password      9 minchars_low  10 minchars_high  11 mfa
#      12 retention    13 days90     14 days365 15 legal_hold


def seed_knowledge_base() -> KnowledgeBase:
    kb = KnowledgeBase()

    kb.add(
        Atom(
            atom_id="atom_refund_v1",
            atom_type="policy_fact",
            body="Refund window is 30 days after purchase, no exceptions.",
            embedding=(0.9, 0.9, 0.9, 0.0, 0.8, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0),
            scope="platform",
            provenance="policy-doc://refunds/v1#section-3",
            validity_start="2023-01-01",
            validity_end="2025-12-31",  # superseded
        )
    )
    kb.add(
        Atom(
            atom_id="atom_refund_v2",
            atom_type="policy_fact",
            body=(
                "Refund window is 14 days after purchase; platinum-tier customers "
                "retain a 30-day exception window."
            ),
            embedding=(0.55, 0.5, 0.3, 0.7, 0.5, 0.6, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0),
            scope="platform",
            provenance="policy-doc://refunds/v2#section-1",
            validity_start="2026-01-01",
            validity_end=None,  # current
        )
    )
    kb.add(
        Atom(
            atom_id="atom_password_v1",
            atom_type="policy_fact",
            body="Password policy requires a minimum of 6 characters, no complexity rules.",
            embedding=(0, 0, 0, 0, 0, 0, 0, 0, 0.9, 0.9, 0.9, 0.0, 0, 0, 0, 0),
            scope="platform",
            provenance="policy-doc://password/v1#section-1",
            validity_start="2021-01-01",
            validity_end="2024-06-30",  # superseded
        )
    )
    kb.add(
        Atom(
            atom_id="atom_password_v2",
            atom_type="policy_fact",
            body=(
                "Password policy requires a minimum of 12 characters plus multi-factor "
                "authentication for all accounts."
            ),
            embedding=(0, 0, 0, 0, 0, 0, 0, 0, 0.5, 0.4, 0.7, 0.7, 0, 0, 0, 0),
            scope="platform",
            provenance="policy-doc://password/v2#section-1",
            validity_start="2024-07-01",
            validity_end=None,  # current
        )
    )
    kb.add(
        Atom(
            atom_id="atom_retention_v1",
            atom_type="policy_fact",
            body="Data retention period is 90 days after account closure.",
            embedding=(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.9, 0.9, 0.0, 0.0),
            scope="platform",
            provenance="policy-doc://retention/v1#section-2",
            validity_start="2022-03-01",
            validity_end="2025-09-30",  # superseded
        )
    )
    kb.add(
        Atom(
            atom_id="atom_retention_v2",
            atom_type="policy_fact",
            body=(
                "Data retention period is 365 days after account closure, extended "
                "indefinitely under legal hold."
            ),
            embedding=(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.5, 0.35, 0.7, 0.65),
            scope="platform",
            provenance="policy-doc://retention/v2#section-1",
            validity_start="2025-10-01",
            validity_end=None,  # current
        )
    )
    kb.add(
        Atom(
            atom_id="atom_shipping_v1",
            atom_type="policy_fact",
            body=(
                "Standard shipping takes 5-7 business days from purchase; expedited "
                "shipping is available for an extra fee."
            ),
            embedding=(0.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.9, 0.0, 0, 0, 0, 0, 0, 0, 0, 0),
            scope="platform",
            provenance="policy-doc://shipping/v1#section-1",
            validity_start="2020-01-01",
            validity_end=None,  # current, no supersession — always was this way
        )
    )
    kb.add(
        Atom(
            atom_id="atom_tenant_acme_refund_v1",
            atom_type="policy_fact",
            body="Acme Corp's contract addendum grants a custom 45-day refund window.",
            embedding=(0.2, 0.15, 0.1, 0.2, 0.15, 0.1, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0),
            scope="tenant_acme",
            provenance="contract://acme/addendum-3",
            validity_start="2025-05-01",
            validity_end=None,  # current, tenant-scoped
        )
    )
    return kb


# --- example queries, hand-authored to echo old phrasing more than new -----------
# See README.md for the fairness argument: these are correct, unmodified cosine
# comparisons — the stale atom really does score higher, because its short,
# unqualified phrasing textually resembles the query more than the current atom's
# longer phrasing (which trades some lexical closeness for the added exception
# clause). Governed retrieval wins on currency and scope, not on a rigged retriever.

QUERY_REFUND_WINDOW = (0.9, 0.9, 0.0, 0.0, 0.8, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0)
QUERY_PASSWORD_MIN_LENGTH = (0, 0, 0, 0, 0, 0, 0, 0, 0.9, 0.9, 0.0, 0.0, 0, 0, 0, 0)
QUERY_RETENTION_PERIOD = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.85, 0.95, 0.0, 0.0)

# A query about a topic the KB has no current fact for at all — every atom scores
# near zero, so governed_retrieve abstains on threshold, not on scope.
QUERY_WARRANTY_PERIOD = (0, 0, 0, 0, 0, 0, 0, 0.9, 0, 0, 0, 0, 0, 0, 0, 0)

SUPERSESSION_QUERIES = (
    ("atom_refund_v1", "atom_refund_v2", QUERY_REFUND_WINDOW, "platform"),
    ("atom_password_v1", "atom_password_v2", QUERY_PASSWORD_MIN_LENGTH, "platform"),
    ("atom_retention_v1", "atom_retention_v2", QUERY_RETENTION_PERIOD, "platform"),
)

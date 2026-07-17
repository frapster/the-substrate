"""
evidence.py: a minimal evidence store that refuses unsourced claims.

This is a clean-room, dependency-free implementation of the *mechanism* the-substrate
claims in prose (README.md, BOSS-STANDARD.md: "evidence-backed", a claim traces to a
hashed source and can be superseded when the source changes; ADR-0005: facts are
"atomic, provenance-tracked (hashed to source), versioned, and reconciled"). It is a
generic hashing/pinning primitive (content-hash provenance is textbook technique) and
contains none of the BOSNet.io evidence-model schema or coordinate scheme. It exists to
make a published claim *runnable and checkable* by a stranger.

The idea in one line:

    claim.pinned_hash = SHA256(canonical bytes of source.text at assert-time)

A claim is only as good as the source it names. If the source doesn't resolve, the
claim is refused before it's ever stored: "no evidence without a resolvable source."
If the source's bytes change after the claim was asserted, the pinned hash and the
source's current hash disagree, and the claim is INVALIDATED, detached from ground
truth, automatically, without anyone having to notice and revoke it by hand.

Standard library only (hashlib, dataclasses, typing). Runs on any Python 3.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional


def _canonical_bytes(text: str) -> bytes:
    """Deterministic byte encoding so a given source text always hashes to the same
    value. UTF-8 is the one true encoding here, no ambiguity to hash around."""
    return text.encode("utf-8")


def content_hash(text: str) -> str:
    """The identity function for a source. Two sources with identical text hash
    identically; one character of drift changes the hash entirely."""
    return hashlib.sha256(_canonical_bytes(text)).hexdigest()


@dataclass
class Source:
    """One registered piece of evidence. `text` is the governed fact's grounding
    material (e.g. a document, a record, a policy clause). Its `content_hash` IS
    its identity: recomputed on demand, never cached as truth."""

    source_id: str
    text: str

    @property
    def current_hash(self) -> str:
        return content_hash(self.text)


@dataclass
class Claim:
    """One asserted claim, pinned to the content_hash of its source AT ASSERT-TIME.
    `trust_class` echoes real vocabulary: claims start untrusted and are only as
    good as the evidence backing them."""

    statement: str
    source_id: str
    pinned_hash: str
    trust_class: str = "untrusted"

    def short(self) -> str:
        return self.pinned_hash[:8]


@dataclass
class VerifyResult:
    """Outcome of re-checking a claim against its source's current bytes."""

    ok: bool
    reason: str = ""

    def __bool__(self) -> bool:  # so callers can write `if store.verify(claim):`
        return self.ok


class UnsourcedClaimError(Exception):
    """Raised when a claim names a source that does not resolve. Fail-closed:
    no evidence without a resolvable source."""


@dataclass
class EvidenceStore:
    """A store of sources and the claims pinned to them.

    There is deliberately no way to assert a claim without naming a registered
    source, and no way for a claim to silently "follow" an edited source. Pinning
    is captured once, at assert-time. The `_tamper_*` helper below is NOT part of
    that API; it exists purely so the demo and tests can simulate an attacker who
    reaches past the API to edit a stored source's bytes, and prove verify() catches it.
    """

    sources: dict[str, Source] = field(default_factory=dict)
    claims: list[Claim] = field(default_factory=list)

    def add_source(self, source_id: str, text: str) -> str:
        """Register a source and return its content_hash. The hash IS the
        source's identity: anyone can recompute it and get the same value."""
        source = Source(source_id=source_id, text=text)
        self.sources[source_id] = source
        return source.current_hash

    def assert_claim(self, statement: str, source_id: str) -> Claim:
        """Assert a claim grounded in a registered source. Pins the source's
        CURRENT content_hash into the claim. Fails closed if the source is not
        resolvable: a claim with no evidence is refused before it is stored."""
        source = self.sources.get(source_id)
        if source is None:
            raise UnsourcedClaimError(
                f"claim {statement!r} names source {source_id!r}, which is not "
                "registered, no evidence without a resolvable source"
            )
        claim = Claim(statement=statement, source_id=source_id, pinned_hash=source.current_hash)
        self.claims.append(claim)
        return claim

    def verify(self, claim: Claim) -> VerifyResult:
        """Recompute the claim's source's CURRENT content_hash and compare it to
        the hash pinned at assert-time. A mismatch means the source moved out from
        under the claim. The claim is stale and detached; it is never silently
        trusted."""
        source = self.sources.get(claim.source_id)
        if source is None:
            return VerifyResult(
                ok=False,
                reason=(
                    f"source {claim.source_id!r} no longer registered, "
                    "claim is detached (source missing)"
                ),
            )
        current = source.current_hash
        if current != claim.pinned_hash:
            return VerifyResult(
                ok=False,
                reason=(
                    f"source {claim.source_id!r} current hash {current[:8]}… != "
                    f"pinned {claim.pinned_hash[:8]}… (source was edited after assert-time)"
                ),
            )
        return VerifyResult(ok=True, reason="pinned hash matches current source")

    # --- attacker simulation helper (NOT part of the sanctioned API) ---------------
    # Reaches past add_source() to mutate an already-stored source's text in place,
    # exactly as a tamperer with storage access would. Lets the demo/tests show a
    # source edit detaching every claim pinned to it.

    def _tamper_source(self, source_id: str, new_text: str) -> None:
        """Edit a registered source's text WITHOUT touching any claim's pinned
        hash: a silent edit at the ground-truth layer."""
        self.sources[source_id].text = new_text

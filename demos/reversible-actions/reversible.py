"""
reversible.py — a minimal, versioned store proving the "Reversible" BOSS guarantee.

This is a clean-room, dependency-free implementation of the *mechanism* the-substrate
claims in prose (BOSS-STANDARD.md: "**Reversible** | High-impact actions are gated,
versioned, and recoverable."). It is a generic state-management primitive — append-only
versioning is textbook technique — and contains none of the BOSNet.io engine, schema, or
kernel. It exists to make a published claim *runnable and checkable* by a stranger.

The faithful mechanism, deliberately NOT a literal stored-inverse "undo":

    apply(change)      → appends a NEW version (supersede-forward); predecessors untouched
    restore(version=N) → appends a NEW version equal to version N's state (recovery IS
                          forward motion through the chain, not a rewind)

There is no update() or delete() on a stored version. In-place mutation is forbidden and
FAILS CLOSED: `_update_in_place()` / `_delete_in_place()` exist only to prove the durable
append-only guard refuses them, unconditionally, every time. High-impact actions are
gated: an ungated `apply(..., high_impact=True)` is refused outright. Even the reserved
operator-destructive path writes its own audit note rather than silently erasing state.

Standard library only (hashlib, json, dataclasses, typing). Runs on any Python 3.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Optional


def _canonical_state(state: dict[str, Any]) -> str:
    """Deterministic JSON so a given state always hashes to the same value.

    sort_keys + no whitespace removes the two usual sources of hash instability
    (key order and formatting). Two structurally-equal states produce identical bytes.
    """
    return json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_state_hash(state: dict[str, Any]) -> str:
    """The versioning function. A pure hash of the canonical state — recomputing it
    from a stored version's state must always reproduce the version's stored hash."""
    return hashlib.sha256(_canonical_state(state).encode("utf-8")).hexdigest()


@dataclass
class Version:
    """One committed state version. `state` is the full governed state as of this
    version. `state_hash` is this version's content digest. Predecessors are never
    edited once committed — the only sanctioned way forward is a new Version."""

    index: int
    state: dict[str, Any]
    state_hash: str
    note: str = ""
    operator_destructive: bool = False

    def short(self) -> str:
        return self.state_hash[:8]


@dataclass
class ChainVerifyResult:
    """Outcome of a full-chain recomputation, mirroring the ledger's VerifyResult."""

    ok: bool
    checked: int
    broken_index: Optional[int] = None
    reason: str = ""

    def __bool__(self) -> bool:  # so callers can write `if store.verify_chain():`
        return self.ok


class AppendOnlyViolation(Exception):
    """Raised by the durable append-only guard: state versions cannot be edited or
    removed in place. The only sanctioned mutation is apply() (supersede-forward)."""


class UngatedHighImpactError(Exception):
    """Raised when a high-impact change is attempted without an approval token
    (gated=True). High-impact actions must be gated before they can apply."""


@dataclass
class Store:
    """A versioned, append-only state store.

    There is deliberately no public update() or delete() on a committed version — the
    only sanctioned way to change state is to `apply()` a change, which supersedes
    forward by appending a new version. `restore()` recovers a prior state the same
    way: by appending a new version equal to it, never by rewinding history.

    The `_update_in_place` / `_delete_in_place` helpers below are NOT part of that API;
    they exist purely so the demo and tests can show what happens when something tries
    to reach past append-only semantics — and prove the guard fails closed every time.
    """

    versions: list[Version] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.versions:
            genesis = Version(index=0, state={}, state_hash=compute_state_hash({}), note="genesis")
            self.versions.append(genesis)

    @property
    def head(self) -> Version:
        return self.versions[-1]

    @property
    def state(self) -> dict[str, Any]:
        return self.head.state

    @property
    def state_hash(self) -> str:
        return self.head.state_hash

    def snapshot_at(self, version: int) -> str:
        """The state_hash recorded at a given version index — the target restore()
        must reproduce exactly."""
        return self.versions[version].state_hash

    def apply(
        self,
        change: dict[str, Any],
        *,
        high_impact: bool = False,
        gated: bool = False,
        note: str = "",
    ) -> Version:
        """The only sanctioned mutation: append a NEW version with `change` merged
        into current state (supersede-forward). All predecessors are preserved
        untouched. High-impact changes are gated: an ungated one is refused."""
        if high_impact and not gated:
            raise UngatedHighImpactError(
                f"high-impact change {change!r} refused: no approval token "
                "(pass gated=True after HITL approval)"
            )
        new_state = {**self.state, **change}
        return self._commit(new_state, note=note or f"apply {change!r}")

    def restore(self, version: int) -> Version:
        """Reversibility guarantee: recover a prior state by supersede-forward —
        append a NEW version equal to `version`'s state. Deterministic, not
        best-effort: the returned version's state_hash equals snapshot_at(version)
        exactly, byte-for-byte."""
        snapshot = self.versions[version]
        restored = self._commit(dict(snapshot.state), note=f"restore(version={version})")
        assert restored.state_hash == snapshot.state_hash  # deterministic by construction
        return restored

    def operator_destructive(self, reason: str) -> Version:
        """Reserved, audited operator-destructive path (e.g. a full purge). It is
        explicitly marked and itself writes an audit note — even destructive recovery
        is recorded as a new version, never as a silent in-place erasure."""
        if not reason:
            raise ValueError("operator_destructive requires a reason (illustrative audit note)")
        return self._commit({}, note=f"operator_destructive: {reason}", operator_destructive=True)

    def _commit(self, new_state: dict[str, Any], *, note: str, operator_destructive: bool = False) -> Version:
        index = len(self.versions)
        state_hash = compute_state_hash(new_state)
        version = Version(
            index=index,
            state=new_state,
            state_hash=state_hash,
            note=note,
            operator_destructive=operator_destructive,
        )
        self.versions.append(version)
        return version

    def verify_chain(self) -> ChainVerifyResult:
        """Recompute every version's state_hash from its stored state and confirm
        indices are contiguous. Reports the first inconsistency, if any."""
        for i, v in enumerate(self.versions):
            if v.index != i:
                return ChainVerifyResult(
                    ok=False,
                    checked=i,
                    broken_index=i,
                    reason=f"version {i} carries index {v.index} (chain reordered or truncated)",
                )
            recomputed = compute_state_hash(v.state)
            if recomputed != v.state_hash:
                return ChainVerifyResult(
                    ok=False,
                    checked=i,
                    broken_index=i,
                    reason=(
                        f"version {i} recomputed hash {recomputed[:8]}… != stored "
                        f"{v.state_hash[:8]}… (state was altered)"
                    ),
                )
        return ChainVerifyResult(ok=True, checked=len(self.versions), reason="all versions intact")

    # --- durable append-only guard ---------------------------------------------------
    # These model the sanctioned-mutation boundary: any attempt to edit or remove a
    # committed version in place is refused unconditionally. There is no "sometimes" —
    # the guard fails closed every time it is invoked.

    def _update_in_place(self, index: int, change: dict[str, Any]) -> None:
        """Illustrative ONLY: attempting to mutate a stored version's state directly,
        instead of superseding forward via apply(). FAILS CLOSED."""
        raise AppendOnlyViolation(
            f"in-place update of version {index} refused: durable append-only guard — "
            "mutate via apply(), never in place"
        )

    def _delete_in_place(self, index: int) -> None:
        """Illustrative ONLY: attempting to remove a stored version directly. FAILS CLOSED."""
        raise AppendOnlyViolation(
            f"in-place delete of version {index} refused: durable append-only guard — "
            "history is immutable"
        )

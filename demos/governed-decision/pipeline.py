"""
pipeline.py — the whole governed loop in one runnable file.

This is the flagship demo: one intent flows through all four BOSS guarantees end to
end — **bounded** gate → **evidence** check → deterministic validator (a mocked model's
reasoning is checked, never trusted) → **audited** hash-chained ledger → **reversible**
commit — and each stage can refuse its own failure input in isolation.

The point it makes that the four separate primitives do not: the substrate is a
*pipeline, not a prompt*. Governance is the sequence of deterministic checkpoints that
wrap the one probabilistic step in the middle.

Each stage here is a deliberately MINIMAL, self-contained reimplementation of the
mechanism proved more fully in its sibling demo — so this folder runs on its own with
no cross-folder imports:

  - Bounded        → demos/bounded-authority/
  - Evidence       → demos/evidence-provenance/
  - Validated      → demos/deterministic-validator/
  - Audited        → demos/audit-ledger/          (the hash chain, in miniature here)
  - Reversible     → demos/reversible-actions/

Standard library only (hashlib, json). Runs on any Python 3. This is a generic
illustration of the *shape* of a governed decision — not the BOSNet.io engine.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Optional


# --------------------------------------------------------------------------------------
# A tiny shared vocabulary. `Outcome` is the tri-state every gate speaks in the wider
# system: proceed (do it), escalated (a human must approve), blocked (refused outright).
# --------------------------------------------------------------------------------------

PROCEED = "proceed"
ESCALATED = "escalated"
BLOCKED = "blocked"


class GovernanceRefusal(Exception):
    """Raised when a stage refuses to let an intent proceed. Carries the stage name
    and a human-readable reason so the caller can report exactly where the loop said no."""

    def __init__(self, stage: str, reason: str) -> None:
        super().__init__(f"[{stage}] {reason}")
        self.stage = stage
        self.reason = reason


@dataclass
class Intent:
    """One thing an operator (via a model) wants the system to do."""

    action: str
    scope: dict[str, Any]              # e.g. {"rows": 40} or {"usd": 40}
    claim: str                        # the factual assertion the action rests on
    source_id: Optional[str]          # the evidence that backs the claim (None = unsourced)
    proposed_value: dict[str, Any]    # the model's proposed record to commit


# --------------------------------------------------------------------------------------
# Stage 1 — BOUNDED. A closed roster with blast-radius caps. Deny-by-default: an action
# not on the roster may not act ("omission is prohibition"). Fail-closed everywhere.
# --------------------------------------------------------------------------------------

@dataclass
class ActionPolicy:
    tier: str          # yellow < orange < red < purple
    soft_cap: int      # over this → escalate to a human
    hard_cap: int      # over this → blocked outright
    dimension: str     # which scope key the caps apply to (e.g. "rows", "usd")


class BoundedGate:
    def __init__(self, roster: dict[str, ActionPolicy]) -> None:
        self._roster = roster

    def check(self, intent: Intent) -> str:
        policy = self._roster.get(intent.action)
        if policy is None:
            # Deny-by-default. Not on the roster → not permitted, full stop.
            raise GovernanceRefusal(
                "bounded", f"action '{intent.action}' is not on the roster (omission is prohibition)"
            )
        magnitude = intent.scope.get(policy.dimension)
        if magnitude is None:
            # The cap could not be read against this scope → fail closed, never allow past.
            raise GovernanceRefusal(
                "bounded", f"no '{policy.dimension}' in scope to check against the blast-radius cap"
            )
        if magnitude > policy.hard_cap:
            raise GovernanceRefusal(
                "bounded",
                f"{policy.dimension}={magnitude} exceeds hard cap {policy.hard_cap} "
                f"(tier {policy.tier}) — blocked before execution",
            )
        if magnitude > policy.soft_cap:
            # Not a hard refusal, but not an autonomous proceed either.
            return ESCALATED
        return PROCEED


# --------------------------------------------------------------------------------------
# Stage 2 — EVIDENCE-BACKED. A claim must resolve to a hashed source. No provenance,
# no proceed. (The full auto-detach-on-source-edit story is in evidence-provenance/.)
# --------------------------------------------------------------------------------------

class EvidenceStore:
    def __init__(self) -> None:
        self._sources: dict[str, str] = {}  # source_id -> content_hash

    def add_source(self, source_id: str, text: str) -> str:
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self._sources[source_id] = content_hash
        return content_hash

    def require(self, intent: Intent) -> str:
        if not intent.source_id or intent.source_id not in self._sources:
            raise GovernanceRefusal(
                "evidence",
                f"claim {intent.claim!r} carries no resolvable source — "
                f"nothing is asserted without provenance",
            )
        return self._sources[intent.source_id]


# --------------------------------------------------------------------------------------
# Stage 3 — VALIDATED. The model proposes; a deterministic validator commits only what
# passes; a rejected proposal is discarded, not patched. (More in deterministic-validator/.)
# --------------------------------------------------------------------------------------

class DeterministicValidator:
    def __init__(self, required_fields: tuple[str, ...], max_usd: int) -> None:
        self._required = required_fields
        self._max_usd = max_usd

    def validate(self, intent: Intent) -> dict[str, Any]:
        proposal = intent.proposed_value
        missing = [f for f in self._required if f not in proposal]
        if missing:
            raise GovernanceRefusal(
                "validated", f"proposal missing required field(s) {missing} — discarded, not patched"
            )
        amount = proposal.get("amount_usd", 0)
        if amount > self._max_usd:
            raise GovernanceRefusal(
                "validated",
                f"proposed amount_usd={amount} exceeds validator bound {self._max_usd} "
                f"— discarded, not patched",
            )
        # Return the proposal VERBATIM. The validator never rewrites a proposal into a
        # passing one; it either passes the model's record through, or discards it.
        return dict(proposal)


# --------------------------------------------------------------------------------------
# Stage 4 — AUDITED. A miniature hash-chained ledger. Every committed decision folds in
# the previous entry's hash. (The full tamper-evidence proof + benchmark is in audit-ledger/.)
# --------------------------------------------------------------------------------------

GENESIS = "0" * 64


@dataclass
class AuditLedger:
    rows: list[dict[str, Any]] = field(default_factory=list)

    @property
    def head(self) -> str:
        return self.rows[-1]["hash"] if self.rows else GENESIS

    def append(self, body: dict[str, Any]) -> str:
        index = len(self.rows)
        prev = self.head
        payload = f"{prev}|{index}|{json.dumps(body, sort_keys=True, separators=(',', ':'))}"
        row_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.rows.append({"index": index, "prev": prev, "body": body, "hash": row_hash})
        return row_hash

    def verify(self) -> bool:
        expected_prev = GENESIS
        for i, row in enumerate(self.rows):
            if row["prev"] != expected_prev:
                return False
            payload = f"{row['prev']}|{i}|{json.dumps(row['body'], sort_keys=True, separators=(',', ':'))}"
            if hashlib.sha256(payload.encode("utf-8")).hexdigest() != row["hash"]:
                return False
            expected_prev = row["hash"]
        return True


# --------------------------------------------------------------------------------------
# Stage 5 — REVERSIBLE. Append-only, supersede-forward versioned state; restore()
# reconstructs a prior version exactly. (The append-only guard proof is in reversible-actions/.)
# --------------------------------------------------------------------------------------

def _state_hash(state: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(state, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass
class ReversibleStore:
    versions: list[dict[str, Any]] = field(default_factory=lambda: [{}])

    @property
    def state(self) -> dict[str, Any]:
        return dict(self.versions[-1])

    def state_hash_at(self, version: int) -> str:
        return _state_hash(self.versions[version])

    def apply(self, change: dict[str, Any]) -> int:
        # Supersede forward: the new state is a NEW version; predecessors are preserved.
        new_state = dict(self.versions[-1])
        new_state.update(change)
        self.versions.append(new_state)
        return len(self.versions) - 1

    def restore(self, version: int) -> int:
        # Recovery is itself a supersede-forward: append a version equal to `version`.
        restored = dict(self.versions[version])
        self.versions.append(restored)
        return len(self.versions) - 1


# --------------------------------------------------------------------------------------
# The pipeline: run one intent through all five stages. Any stage may refuse.
# --------------------------------------------------------------------------------------

@dataclass
class GovernedDecision:
    committed: bool
    outcome: str
    ledger_hash: Optional[str] = None
    version: Optional[int] = None
    refusal_stage: Optional[str] = None
    refusal_reason: Optional[str] = None


class Substrate:
    """Composes the five stages into one governed decision loop."""

    def __init__(
        self,
        gate: BoundedGate,
        evidence: EvidenceStore,
        validator: DeterministicValidator,
        ledger: AuditLedger,
        store: ReversibleStore,
    ) -> None:
        self.gate = gate
        self.evidence = evidence
        self.validator = validator
        self.ledger = ledger
        self.store = store

    def decide(self, intent: Intent) -> GovernedDecision:
        try:
            outcome = self.gate.check(intent)                       # 1. bounded
            source_hash = self.evidence.require(intent)             # 2. evidence-backed
            record = self.validator.validate(intent)                # 3. validated (model checked)
            ledger_hash = self.ledger.append(                        # 4. audited
                {
                    "action": intent.action,
                    "outcome": outcome,
                    "source_hash": source_hash[:12],
                    "record": record,
                }
            )
            version = self.store.apply({intent.action: record})     # 5. reversible
            return GovernedDecision(
                committed=True, outcome=outcome, ledger_hash=ledger_hash, version=version
            )
        except GovernanceRefusal as r:
            # A refusal at any stage stops the loop. Nothing partial commits.
            return GovernedDecision(
                committed=False,
                outcome=BLOCKED,
                refusal_stage=r.stage,
                refusal_reason=r.reason,
            )

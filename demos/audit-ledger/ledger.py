"""
ledger.py: a minimal, append-only, hash-chained audit ledger.

This is a clean-room, dependency-free implementation of the *mechanism* the-substrate
claims in its prose (README.md: "every decision writes a hash-chained, tamper-evident
ledger entry"; BOSS-STANDARD.md: "tamper-evident decision ledger"). It is a generic
cryptographic primitive (SHA-256 hash chaining is textbook technique) and contains
none of the BOSNet.io engine, schema, or kernel. It exists to make a published claim
*runnable and checkable* by a stranger.

The idea in one line:

    entry.hash = SHA256(prev_hash || canonical_json(entry_body))

Because each row's hash folds in the previous row's hash, editing any past row changes
its hash, which breaks every hash after it. `verify()` recomputes the whole chain and
reports the first row where the stored hash and the recomputed hash disagree, so
tampering is *evident*, not silent.

Standard library only (hashlib, json). Runs on any Python 3.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Optional

# The genesis row's predecessor. A fixed, well-known anchor so the whole chain is
# reproducible from row 0 with no hidden state.
GENESIS_PREV_HASH = "0" * 64


def _canonical_json(body: dict[str, Any]) -> str:
    """Deterministic JSON so a given body always hashes to the same value.

    sort_keys + no whitespace removes the two usual sources of hash instability
    (key order and formatting). Two structurally-equal bodies produce identical bytes.
    """
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_hash(prev_hash: str, index: int, body: dict[str, Any]) -> str:
    """The chaining function. Folds the predecessor hash, the row index, and the
    canonical body into one SHA-256 digest. `index` is included so that reordering
    two otherwise-identical rows is also detectable."""
    payload = f"{prev_hash}|{index}|{_canonical_json(body)}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass
class Row:
    """One committed ledger entry. `body` is the governed decision record
    (e.g. inputs, model, verdict). `hash` is this row's chained digest."""

    index: int
    prev_hash: str
    body: dict[str, Any]
    hash: str

    def short(self) -> str:
        return self.hash[:8]


@dataclass
class VerifyResult:
    """Outcome of a full-chain recomputation."""

    ok: bool
    checked: int
    broken_index: Optional[int] = None
    reason: str = ""

    def __bool__(self) -> bool:  # so callers can write `if ledger.verify():`
        return self.ok


class TamperError(Exception):
    """Raised by mutating helpers that would violate append-only semantics."""


@dataclass
class Ledger:
    """An append-only, hash-chained ledger.

    There is deliberately no public update() or delete(): the only sanctioned way
    to change the ledger is to `append` a new row. The `_tamper_*` helpers below are
    NOT part of that API; they exist purely so the demo and tests can simulate an
    attacker who reaches past the API to edit stored bytes, and prove verify() catches it.
    """

    rows: list[Row] = field(default_factory=list)

    @property
    def head_hash(self) -> str:
        return self.rows[-1].hash if self.rows else GENESIS_PREV_HASH

    def append(self, body: dict[str, Any]) -> Row:
        """Commit a new decision record and return the chained row."""
        index = len(self.rows)
        prev_hash = self.head_hash
        row_hash = compute_hash(prev_hash, index, body)
        row = Row(index=index, prev_hash=prev_hash, body=body, hash=row_hash)
        self.rows.append(row)
        return row

    def verify(self) -> VerifyResult:
        """Recompute the entire chain from genesis and report the first inconsistency.

        Three independent things must hold at every row:
          1. prev_hash must equal the previous row's stored hash   (link intact)
          2. the recomputed hash must equal the stored hash         (body untampered)
          3. row 0's prev_hash must be the genesis anchor           (no truncation of the head)
        """
        expected_prev = GENESIS_PREV_HASH
        for i, row in enumerate(self.rows):
            if row.prev_hash != expected_prev:
                return VerifyResult(
                    ok=False,
                    checked=i,
                    broken_index=i,
                    reason=(
                        f"row {i} prev_hash {row.prev_hash[:8]}… does not link to "
                        f"expected {expected_prev[:8]}… (chain reordered or truncated)"
                    ),
                )
            recomputed = compute_hash(row.prev_hash, row.index, row.body)
            if recomputed != row.hash:
                return VerifyResult(
                    ok=False,
                    checked=i,
                    broken_index=i,
                    reason=(
                        f"row {i} recomputed hash {recomputed[:8]}… != stored "
                        f"{row.hash[:8]}… (body was altered)"
                    ),
                )
            expected_prev = row.hash
        return VerifyResult(ok=True, checked=len(self.rows), reason="all rows intact")

    # --- attacker simulation helpers (NOT part of the append-only API) -------------
    # These reach past append() to mutate already-stored rows, exactly as a tamperer
    # with database access would. They let the demo/tests show verify() catching it.

    def _tamper_body(self, index: int, new_body: dict[str, Any]) -> None:
        """Edit a stored row's body WITHOUT recomputing its hash: a silent tamper."""
        self.rows[index].body = new_body

    def _tamper_delete(self, index: int) -> None:
        """Remove a stored row, splicing the chain: a truncation/excision tamper."""
        del self.rows[index]

    def _tamper_swap(self, i: int, j: int) -> None:
        """Swap two stored rows: a reordering tamper."""
        self.rows[i], self.rows[j] = self.rows[j], self.rows[i]

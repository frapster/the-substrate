"""
validator.py: a deterministic validator that commits only what passes.

This is a clean-room, dependency-free implementation of the *mechanism* behind
ADR-0003 (../../docs/adr/ADR-0003-deterministic-validator-commits.md): "deterministic code
computes what does happen and grades the reasoning; the model decides what should happen;
a deterministic validator commits only what passes." It is a generic gate primitive (a set
of hand-written checks over a plain proposal) and contains none of the BOSNet.io engine,
schema, or kernel. It exists to make that decision *runnable and checkable* by a stranger.

The shape in one line:

    model proposes -> deterministic validate() grades it -> only a PASS is committed

A proposal that fails is DISCARDED: nothing here ever rewrites a failing
proposal into a passing one, because that would launder an untrustworthy decision into
the record. The model is never trusted. It is checked.

An `llm_judge()` is included to model the tempting alternative ADR-0003 rejects: using a
second model as the commit gate. It can feed evidence into a proposal's review, but it has
no path to the commit log: only `Validator.validate()` does.

Standard library only. Runs on any Python 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# The fixed set of source ids the model is allowed to cite as evidence. Anything else is
# a hallucinated citation, a source that does not exist in this system of record.
KNOWN_SOURCE_IDS = frozenset({"src_101", "src_102", "src_103", "src_104"})

# The policy bound on any proposed refund amount, in USD. A deterministic, checkable rule.
MAX_AMOUNT_USD = 500


@dataclass(frozen=True)
class Proposal:
    """One model-proposed action. Frozen so nothing downstream can mutate it in place:
    the only way a Proposal changes is by not existing (discarded) or being copied into
    the commit log exactly as it arrived (committed)."""

    intent: str
    source_id: str
    amount_usd: int
    model: str = "claude"


@dataclass
class CheckResult:
    """Outcome of a single deterministic validation."""

    ok: bool
    reason: str

    def __bool__(self) -> bool:  # so callers can write `if validator.validate(p):`
        return self.ok


@dataclass
class Judgment:
    """A mocked LLM judge's opinion of a proposal. Evidence only: per ADR-0003, an LLM
    judge can feed the validator, it cannot BE the validator. Nothing in this module lets
    a Judgment reach the commit log directly; see Validator.submit()."""

    approved: bool
    note: str


def propose(intent: str, source_id: str, amount_usd: int, model: str = "claude") -> Proposal:
    """A mocked 'model' call. In a real system this would be an LLM completion; here it's
    a plain constructor: validate() is the function under test.
    Callers are free to construct proposals that hallucinate a source or exceed policy;
    that's the point: the model is not trusted to police itself."""
    return Proposal(intent=intent, source_id=source_id, amount_usd=amount_usd, model=model)


def llm_judge(proposal: Proposal) -> Judgment:
    """A mocked LLM judge: a second model's opinion of the first model's proposal.
    Deliberately naive: it only eyeballs whether the amount looks reasonable, and it does
    not check the source at all. That's realistic (a judge is still a probabilistic
    reader) and it's exactly why ADR-0003 keeps judges off the commit gate: a
    probabilistic checker of a probabilistic proposer has no deterministic floor."""
    if proposal.amount_usd <= MAX_AMOUNT_USD:
        return Judgment(approved=True, note=f"amount ${proposal.amount_usd} looks reasonable")
    return Judgment(approved=False, note=f"amount ${proposal.amount_usd} looks high")


@dataclass
class RejectedEntry:
    """A recorded discard: the untouched proposal, plus why it never committed."""

    proposal: Proposal
    reason: str


@dataclass
class Validator:
    """The deterministic gate. `commit_log` receives ONLY proposals that pass `validate()`;
    `rejected_log` records every discard with its reason, keeping every failure visible.
    There is deliberately no repair path: a proposal either commits verbatim or it
    doesn't commit at all.
    """

    commit_log: list[Proposal] = field(default_factory=list)
    rejected_log: list[RejectedEntry] = field(default_factory=list)

    def validate(self, proposal: Proposal) -> CheckResult:
        """The deterministic checks. Real, hand-written rules, no model call in here.

        1. required fields present
        2. the cited source must exist in the known set (catches hallucinated citations)
        3. the amount must be positive and within the policy bound
        """
        if not proposal.intent:
            return CheckResult(ok=False, reason="missing required field: intent")
        if proposal.source_id not in KNOWN_SOURCE_IDS:
            return CheckResult(
                ok=False,
                reason=f"cited source {proposal.source_id!r} does not exist in known sources",
            )
        if proposal.amount_usd < 0:
            return CheckResult(ok=False, reason=f"amount_usd {proposal.amount_usd} must not be negative")
        if proposal.amount_usd > MAX_AMOUNT_USD:
            return CheckResult(
                ok=False,
                reason=f"amount_usd {proposal.amount_usd} exceeds policy bound {MAX_AMOUNT_USD}",
            )
        return CheckResult(ok=True, reason="passes all checks")

    def submit(self, proposal: Proposal, judgment: Optional[Judgment] = None) -> CheckResult:
        """Submit a proposal for commit. `judgment` is optional evidence from `llm_judge()`,
        accepted here purely so callers can log it alongside the decision; it is
        NEVER read by the gate below. Only `validate()` decides what commits.

        A passing proposal is appended to `commit_log` exactly as constructed: no field is
        rewritten, no value is clamped into range. A failing proposal is appended to
        `rejected_log` with its reason and stays there unmodified.
        """
        result = self.validate(proposal)
        if result.ok:
            self.commit_log.append(proposal)  # verbatim: no mutation, no auto-repair
        else:
            self.rejected_log.append(RejectedEntry(proposal=proposal, reason=result.reason))
        return result

# Changelog

All notable changes to **the-substrate** are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This repo is a thesis and evidence
record rather than a versioned software package, so entries are dated milestones.

## [Unreleased]

_Nothing yet._

## 2026-07-16: A runnable proof per guarantee

The single ledger demo becomes a **suite**: one runnable, zero-dependency proof for each BOSS
guarantee, including the two originals (governed knowledge and the 90:10 ratio) that previously had no
runnable backing. Each demo is grounded in a real mechanism from the private engine but ships only a
clean-room toy, and each dramatizes a governed *refusal*.

### Added
- **`demos/`: a suite of runnable proofs**, each stdlib-only, with a narrative runner, `unittest`
  suite whose **negative** cases are the point, an honest "what this does NOT prove" note, and (where a
  number is honest) a reproducible benchmark:
  - `demos/bounded-authority/`: a deny-by-default gate that refuses over-scoped/unregistered actions
    before execution (`proceed`/`escalated`/`blocked`, fail-closed). Proves **Bounded** (ADR-0002).
  - `demos/evidence-provenance/`: a claim must resolve to a hashed source; editing a source
    auto-detaches its claim. Proves **Evidence-backed** (ADR-0005).
  - `demos/governed-knowledge/`: a *fair-fight* contrast. Naive cosine returns a stale atom that
    genuinely scores higher, while governed retrieval returns the current one or abstains. Proves the
    **RAG-is-not-the-substrate** claim (ADR-0005).
  - `demos/reversible-actions/`: in-place mutation fails closed; recovery is supersede-forward;
    `restore()` reproduces the exact prior state hash. Proves **Reversible**.
  - `demos/deterministic-validator/`: commits only what passes; a rejected proposal is discarded
    outright. Proves the validator decision (ADR-0003).
  - `demos/ai-code-ratio/`: the same feature built twice; new requirements cost facts, not code
    branches, with the delta **counted** from source. Makes the 90:10 spine concrete (honest that it is
    one illustrative feature, not a whole-system measurement).
  - `demos/governed-decision/`: the flagship. One intent through all four guarantees end to end, each
    stage refusing its own failure input.
- **README:** a **Runnable proofs** section indexing the suite; a suite index at `demos/README.md`.
- **ADRs:** `Runnable proof:` links added to ADR-0002, ADR-0003, and ADR-0005.

### Changed
- **`demo/` to `demos/audit-ledger/`.** The original tamper-evident ledger moved into the suite
  (history preserved via `git mv`); all cross-links updated (README, ADR-0001, ADR-0006, in-file text).

## 2026-07-15: Credibility floor

The repo gains its first **runnable, verifiable** artifacts, so a technical evaluator can check a
core claim instead of taking it on prose. Guided by the private repo assessment.

### Added
- **`demo/`: a runnable, zero-dependency tamper-evident audit ledger.** A clean-room Python 3
  (standard library only) implementation of the repo's hash-chained-ledger claim:
  - `ledger.py`: the `Ledger` primitive, append-only, SHA-256 hash chaining, full-chain `verify()`.
  - `ledger_demo.py`: a <1-minute narrative run that commits decisions, then catches a forged past row.
  - `test_ledger.py`: `unittest` suite whose negative cases prove `verify()` catches body edits,
    deletions, reordering, and partial forgeries.
  - `bench.py`: a reproducible benchmark (append/verify throughput; 200/200 tampers detected).
- **`docs/adr/`: six Architecture Decision Records** (hash-chained ledger, deny-by-default,
  deterministic validator, published governance directory, RAG-is-not-the-substrate, private engine)
  with an index.
- **README:** a 30-second **Quickstart**, a **Limitations: what this does and does NOT do** section,
  a **"Why not Microsoft's toolkit / DeepEval?"** section, and an engineering-record link table.
- **This CHANGELOG.**

### Changed
- `.gitignore` now publishes `docs/adr/` while keeping the private working area (`docs/*`) ignored.

## Roadmap (near-term, realistic)

- Extend the benchmark with a verify-with-checkpoints path for very long chains (per ADR-0001).
- ~~A second runnable proof for another published guarantee (evidence-backed provenance).~~ **Done
  (2026-07-16)**, and extended to a proof per guarantee (see `demos/`).
- Ship the remaining case-study "after" conversions as they move from estimate to measured, updating
  their status the moment real numbers exist (Relic Wars is the current measured baseline).
- Layer visual explainers (architecture diagram; an asciinema of the ledger catching tampering) on
  top of the runnable proofs, with polish amplifying evidence, in that order.

---

_Earlier history predates this changelog; see the git log for the thesis and case-study writeups._

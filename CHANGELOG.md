# Changelog

All notable changes to **the-substrate** are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This repo is a thesis + evidence
showcase rather than a versioned software package, so entries are dated milestones.

## [Unreleased]

_Nothing yet._

## 2026-07-15 — Credibility floor

The repo gains its first **runnable, verifiable** artifacts, so a technical evaluator can check a
core claim instead of taking it on prose. Guided by the private repo assessment.

### Added
- **`demo/` — a runnable, zero-dependency tamper-evident audit ledger.** A clean-room Python 3
  (standard library only) implementation of the repo's hash-chained-ledger claim:
  - `ledger.py` — the `Ledger` primitive: append-only, SHA-256 hash chaining, full-chain `verify()`.
  - `ledger_demo.py` — a <1-minute narrative run that commits decisions, then catches a forged past row.
  - `test_ledger.py` — `unittest` suite whose negative cases prove `verify()` catches body edits,
    deletions, reordering, and partial forgeries.
  - `bench.py` — a reproducible benchmark (append/verify throughput; 200/200 tampers detected).
- **`docs/adr/` — six Architecture Decision Records** (hash-chained ledger, deny-by-default,
  deterministic validator, published governance directory, RAG-is-not-the-substrate, private engine)
  with an index.
- **README:** a 30-second **Quickstart**, a **Limitations — what this does and does NOT do** section,
  a **"Why not Microsoft's toolkit / DeepEval?"** section, and an engineering-record link table.
- **This CHANGELOG.**

### Changed
- `.gitignore` now publishes `docs/adr/` while keeping the private working area (`docs/*`) ignored.

## Roadmap (near-term, realistic)

- Extend the benchmark with a verify-with-checkpoints path for very long chains (per ADR-0001).
- A second runnable proof for another published guarantee (evidence-backed provenance).
- Ship the remaining case-study "after" conversions as they move from estimate to measured, updating
  their status the moment real numbers exist (Relic Wars is the current measured baseline).
- Layer visual explainers (architecture diagram; an asciinema of the ledger catching tampering) on
  top of the runnable proofs — polish amplifying evidence, in that order.

---

_Earlier history predates this changelog; see the git log for the thesis and case-study writeups._

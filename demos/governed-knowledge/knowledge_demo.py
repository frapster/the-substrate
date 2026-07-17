"""
knowledge_demo.py: watch governed knowledge retrieval beat naive similarity search.

Run it:

    python demos/governed-knowledge/knowledge_demo.py

No installation, no dependencies. Python 3 standard library only.

The story in four acts:
  1. Show the knowledge base: current atoms and their superseded predecessors.
  2. A naive cosine-similarity retriever confidently returns a SUPERSEDED atom for
     a query about refund policy, and its similarity score really is the highest
     in the whole knowledge base. No cheating: it's a correct search.
  3. A governed retriever, given the SAME query, filters to current + authorized
     atoms first and returns the CURRENT policy instead.
  4. A second query has no current atom that clears the confidence threshold.
     The governed retriever ABSTAINS rather than guessing: no atom is returned.

This is the runnable proof behind ADR-0005 (../../docs/adr/ADR-0005-rag-is-not-the-substrate.md):
retrieval-by-similarity is a useful tactic, not the governed-knowledge substrate.
"""

from __future__ import annotations

from knowledge import (
    QUERY_REFUND_WINDOW,
    QUERY_WARRANTY_PERIOD,
    seed_knowledge_base,
)

# ANSI colors, with a plain fallback so piped/redirected output stays readable.
import sys

_TTY = sys.stdout.isatty()
GREEN = "\033[32m" if _TTY else ""
RED = "\033[31m" if _TTY else ""
DIM = "\033[2m" if _TTY else ""
BOLD = "\033[1m" if _TTY else ""
RESET = "\033[0m" if _TTY else ""
CHECK = "✓"
CROSS = "✗"


def rule(char: str = "─", width: int = 70) -> str:
    return DIM + char * width + RESET


def print_kb(kb) -> None:
    for atom in kb.atoms:
        tag = f"{GREEN}current{RESET}" if atom.is_current else f"{RED}{atom.status()}{RESET}"
        print(f"  {DIM}{atom.atom_id:<28}{RESET} [{tag}]  {DIM}scope={atom.scope}{RESET}")
        print(f"    {DIM}\"{atom.body}\"{RESET}")
        print(f"    {DIM}provenance={atom.provenance}{RESET}")


def main() -> int:
    print()
    print(BOLD + "the-substrate · governed knowledge vs. naive similarity retrieval" + RESET)
    print(rule("═"))
    print(
        "A governance engine can authorize an action correctly and still be WRONG,\n"
        "if it reasons over the wrong fact. Naive vector-similarity search returns\n"
        "the nearest-embedding atom, whether or not that atom is still true. Governed\n"
        "retrieval filters to CURRENT, AUTHORIZED atoms first, and abstains rather\n"
        "than guess when nothing qualifies. Let's watch the difference.\n"
    )

    kb = seed_knowledge_base()

    # --- Act 1: show the knowledge base -------------------------------------------
    print(BOLD + "1. The knowledge base" + RESET)
    print_kb(kb)
    print()

    # --- Act 2: naive retrieval confidently returns the stale atom ----------------
    print(BOLD + "2. Naive similarity search: \"What is the refund window after a purchase?\"" + RESET)
    naive = kb.naive_retrieve(QUERY_REFUND_WINDOW)
    print(
        f"  {RED}[naive_retrieve]{RESET} returns {BOLD}{naive.atom.atom_id}{RESET} "
        f"(cosine={naive.score:.3f}), {RED}{naive.atom.status()}{RESET}"
    )
    print(f"    {DIM}\"{naive.atom.body}\"{RESET}")
    print(
        f"    {DIM}This is not a rigged search: {naive.atom.atom_id} really does score\n"
        f"    highest in the whole knowledge base. The deprecated phrasing textually\n"
        f"    resembles the query more closely than the current policy's does.{RESET}"
    )
    print()

    # --- Act 3: governed retrieval returns the current atom ------------------------
    print(BOLD + "3. Governed retrieval: the SAME query, scope=\"platform\"" + RESET)
    governed = kb.governed_retrieve(QUERY_REFUND_WINDOW, scope="platform")
    print(
        f"  {GREEN}[governed_retrieve]{RESET} returns {BOLD}{governed.atom.atom_id}{RESET} "
        f"(cosine={governed.score:.3f}), {GREEN}{governed.atom.status()}{RESET}"
    )
    print(f"    {DIM}\"{governed.atom.body}\"{RESET}")
    print(
        f"    {DIM}governed_retrieve never even considered {naive.atom.atom_id} as a\n"
        f"    candidate, it filtered to current + authorized atoms BEFORE ranking\n"
        f"    by similarity, so a superseded fact cannot outrank a current one.{RESET}"
    )
    print()

    # --- Act 4: governed retrieval abstains rather than guess ----------------------
    print(BOLD + "4. Governed retrieval: \"What is the warranty period?\" (scope=\"platform\")" + RESET)
    print(f"  {DIM}The knowledge base has no atom about warranty at all.{RESET}")
    abstain = kb.governed_retrieve(QUERY_WARRANTY_PERIOD, scope="platform")
    if not abstain.degraded:
        # This branch must never execute. Abstaining on an off-topic query is the
        # whole point of the threshold.
        print(f"  {RED}{CROSS} governed_retrieve served a guess instead of abstaining!{RESET}")
        return 1
    print(f"  {RED}[governed_retrieve]{RESET} {BOLD}degraded=True{RESET}")
    print(f"    {DIM}reason: {abstain.reason}{RESET}")
    print(
        f"    {DIM}No atom is returned. A naive retriever would still hand back its\n"
        f"    single nearest-embedding atom here, confidently, on a topic it has\n"
        f"    zero real evidence for.{RESET}"
    )
    print()

    print(rule())
    print(
        f"{GREEN}{CHECK} Governed retrieval wins on currency, scope, and the discipline to\n"
        f"  abstain{RESET}, not on a rigged similarity function. {DIM}(See\n"
        f"  demos/governed-knowledge/README.md and docs/adr/ADR-0005-rag-is-not-the-substrate.md\n"
        f"  for why this mechanism, and what it does not claim.){RESET}"
    )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

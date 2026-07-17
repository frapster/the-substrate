"""
gate_demo.py: watch a deny-by-default policy gate refuse an over-scoped action
before it executes.

Run it:

    python demos/bounded-authority/gate_demo.py

No installation, no dependencies: Python 3 standard library only.

The story in four acts:
  1. A governance directory registers a closed roster of actions, each with a risk
     tier and blast-radius caps.
  2. A model proposes a within-budget action: it proceeds.
  3. A model proposes `delete_rows` for 10,000 rows against a policy capped at 100:
     it is BLOCKED before a single row is touched.
  4. A model proposes an action that was never registered: it doesn't exist on the
     roster, so it's blocked too.

This is the runnable proof behind the claim in README.md and BOSS-STANDARD.md that an
agent's authority is bounded to a registered, closed surface, and the rule in
docs/adr/ADR-0002-deny-by-default-roster.md: "omission is prohibition."
"""

from __future__ import annotations

from gate import Gate

# ANSI colors, with a plain fallback so piped/redirected output stays readable.
import sys

_TTY = sys.stdout.isatty()
GREEN = "\033[32m" if _TTY else ""
RED = "\033[31m" if _TTY else ""
YELLOW = "\033[33m" if _TTY else ""
DIM = "\033[2m" if _TTY else ""
BOLD = "\033[1m" if _TTY else ""
RESET = "\033[0m" if _TTY else ""
CHECK = "✓"
CROSS = "✗"


def rule(char: str = "─", width: int = 64) -> str:
    return DIM + char * width + RESET


def print_roster(gate: Gate) -> None:
    for action, policy in gate.roster.items():
        soft = ", ".join(f"{k}≤{v:,}" for k, v in policy.soft_cap.items()) or ","
        hard = ", ".join(f"{k}≤{v:,}" for k, v in policy.hard_ceiling.items()) or ","
        print(f"  {action:<16} tier={policy.tier:<7} soft_cap=[{soft}]  hard_ceiling=[{hard}]")


def print_decision(decision) -> None:
    color = {"proceed": GREEN, "escalated": YELLOW, "blocked": RED}[decision.outcome]
    symbol = {"proceed": CHECK, "escalated": "⚠", "blocked": CROSS}[decision.outcome]
    print(f"  {color}{symbol} {decision.outcome.upper()}{RESET}  {DIM}{decision.reason}{RESET}")


def main() -> int:
    print()
    print(BOLD + "the-substrate · bounded-authority policy gate" + RESET)
    print(rule("═"))
    print(
        "An agent's authority is bounded to a closed roster of registered actions,\n"
        "each capped by blast radius. Every proposal is checked against that roster\n"
        "BEFORE anything executes, fail-closed, deny-by-default. Let's watch it refuse.\n"
    )

    # --- Act 1: the governance directory registers a closed roster ---------------
    print(BOLD + "1. Registering the closed roster" + RESET)
    gate = Gate()
    gate.register(
        "send_email", tier="yellow",
        soft_cap={"max_recipients": 50}, hard_ceiling={"max_recipients": 200},
    )
    gate.register(
        "grant_refund", tier="orange",
        soft_cap={"max_usd": 100}, hard_ceiling={"max_usd": 1000},
    )
    gate.register(
        "delete_rows", tier="red",
        soft_cap={"max_rows": 20}, hard_ceiling={"max_rows": 100},
    )
    gate.register(
        "wire_transfer", tier="purple",
        soft_cap={"max_usd": 500}, hard_ceiling={"max_usd": 5000},
    )
    print_roster(gate)
    print(f"  {DIM}Anything not listed here does not exist as an action an agent can take.{RESET}")
    print()

    # --- Act 2: a within-budget action proceeds -----------------------------------
    print(BOLD + "2. A model proposes a within-budget action" + RESET)
    proposal = {"action": "grant_refund", "scope": {"max_usd": 40}}
    print(f"  {DIM}propose('{proposal['action']}', {proposal['scope']}){RESET}")
    decision = gate.propose(proposal["action"], proposal["scope"])
    print_decision(decision)
    if decision.outcome != "proceed":
        print(f"  {RED}{CROSS} expected proceed, the mechanism is broken.{RESET}")
        return 1
    print()

    # --- Act 3: an over-scoped registered action is blocked before execution -----
    print(BOLD + "3. A model proposes deleting 10,000 rows" + RESET)
    print(f"  {DIM}Policy caps 'delete_rows' at a hard ceiling of 100 rows.{RESET}")
    proposal = {"action": "delete_rows", "scope": {"max_rows": 10_000}}
    print(f"  {DIM}propose('{proposal['action']}', {proposal['scope']}){RESET}")
    decision = gate.propose(proposal["action"], proposal["scope"])
    print_decision(decision)
    if decision.outcome != "blocked":
        # This branch must never execute. If it does, the mechanism is broken.
        print(f"  {RED}{CROSS} over-scoped action was NOT blocked, the gate failed open!{RESET}")
        return 1
    print(f"  {DIM}Zero rows were touched. The refusal happened before execution, not after.{RESET}")
    print()

    # --- Act 4: an unregistered action is blocked, full stop ---------------------
    print(BOLD + "4. A model proposes an action that was never registered" + RESET)
    proposal = {"action": "rotate_prod_credentials", "scope": {"max_usd": 0}}
    print(f"  {DIM}propose('{proposal['action']}', {proposal['scope']}){RESET}")
    decision = gate.propose(proposal["action"], proposal["scope"])
    print_decision(decision)
    if decision.outcome != "blocked":
        print(f"  {RED}{CROSS} unregistered action was NOT blocked, omission was not prohibition!{RESET}")
        return 1
    print()

    print(rule())
    print(
        f"{GREEN}{CHECK} The gate is deny-by-default.{RESET} Over-scoped and unregistered\n"
        "  proposals are refused before a single side effect runs, the roster is\n"
        f"  closed, and the caps fail closed. {DIM}(See demos/bounded-authority/README.md and\n"
        f"  docs/adr/ADR-0002-deny-by-default-roster.md for why this mechanism, and\n  what it does not claim.){RESET}"
    )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

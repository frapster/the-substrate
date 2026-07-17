/*
  ai-code-ratio.js, an in-browser reimplementation of the four files in
  demos/ai-code-ratio/: code_version.py, code_version_v2.py, facts.py, and
  governed_version.py.

  Same feature (ticket routing by plan_tier x severity), same base 9 cases, same
  3 growth cases (critical severity), same fail-closed contract. The branch/LOC
  counts below are NOT recomputed live by this script; they are the real numbers
  code_version.py's ast-based count_branches()/count_decision_loc() produce when
  you run demos/ai-code-ratio/ratio_demo.py (9 -> 12 branches, 30 -> 33 LOC). This
  page just displays them as the code path grows, so the numbers you see here are
  literally what the Python counts, not an estimate.

  This is a convenience, not the proof. The proof is the Python you can run and
  change yourself.
*/

/* ---- BASE_FACTS: mirrors facts.py BASE_FACTS (9 rows, one per base case) ---- */
const BASE_FACTS = [
  { conditions: { plan_tier: 'free', severity: 'low' }, outcome: { queue: 'standard', escalation: null } },
  { conditions: { plan_tier: 'free', severity: 'medium' }, outcome: { queue: 'standard', escalation: null } },
  { conditions: { plan_tier: 'free', severity: 'high' }, outcome: { queue: 'standard', escalation: 'tier1' } },
  { conditions: { plan_tier: 'pro', severity: 'low' }, outcome: { queue: 'priority', escalation: null } },
  { conditions: { plan_tier: 'pro', severity: 'medium' }, outcome: { queue: 'priority', escalation: null } },
  { conditions: { plan_tier: 'pro', severity: 'high' }, outcome: { queue: 'priority', escalation: 'tier2' } },
  { conditions: { plan_tier: 'enterprise', severity: 'low' }, outcome: { queue: 'white_glove', escalation: null } },
  { conditions: { plan_tier: 'enterprise', severity: 'medium' }, outcome: { queue: 'white_glove', escalation: 'tier2' } },
  { conditions: { plan_tier: 'enterprise', severity: 'high' }, outcome: { queue: 'white_glove', escalation: 'tier3' } },
];

/* ---- NEW_FACTS: mirrors facts.py NEW_FACTS (3 rows, the growth scenario) ---- */
const NEW_FACTS = [
  { conditions: { plan_tier: 'free', severity: 'critical' }, outcome: { queue: 'standard_urgent', escalation: 'tier1' } },
  { conditions: { plan_tier: 'pro', severity: 'critical' }, outcome: { queue: 'priority_urgent', escalation: 'tier3' } },
  { conditions: { plan_tier: 'enterprise', severity: 'critical' }, outcome: { queue: 'white_glove', escalation: 'tier4_incident' } },
];

/* ---- routeCode: mirrors code_version.py's route_ticket(), plus the branches
   code_version_v2.py adds, gated by branchesAdded so the UI can grow it one
   case at a time. Each case added here is a real elif a developer would write. ---- */
function routeCode(ticket, branchesAdded) {
  const plan_tier = ticket.plan_tier;
  const severity = ticket.severity;

  if (plan_tier === 'free' && severity === 'low') return { queue: 'standard', escalation: null };
  else if (plan_tier === 'free' && severity === 'medium') return { queue: 'standard', escalation: null };
  else if (plan_tier === 'free' && severity === 'high') return { queue: 'standard', escalation: 'tier1' };
  else if (plan_tier === 'pro' && severity === 'low') return { queue: 'priority', escalation: null };
  else if (plan_tier === 'pro' && severity === 'medium') return { queue: 'priority', escalation: null };
  else if (plan_tier === 'pro' && severity === 'high') return { queue: 'priority', escalation: 'tier2' };
  else if (plan_tier === 'enterprise' && severity === 'low') return { queue: 'white_glove', escalation: null };
  else if (plan_tier === 'enterprise' && severity === 'medium') return { queue: 'white_glove', escalation: 'tier2' };
  else if (plan_tier === 'enterprise' && severity === 'high') return { queue: 'white_glove', escalation: 'tier3' };
  // --- new business cases: critical severity, added one elif at a time as
  // branchesAdded grows, exactly like code_version_v2.py's diff -------------
  else if (branchesAdded >= 1 && plan_tier === 'free' && severity === 'critical') return { queue: 'standard_urgent', escalation: 'tier1' };
  else if (branchesAdded >= 2 && plan_tier === 'pro' && severity === 'critical') return { queue: 'priority_urgent', escalation: 'tier3' };
  else if (branchesAdded >= 3 && plan_tier === 'enterprise' && severity === 'critical') return { queue: 'white_glove', escalation: 'tier4_incident' };
  else {
    // No branch matches. The code silently falls through to a generic default.
    // It does not know it's guessing. Fail-open, contrasted with evaluate()'s
    // fail-closed abstain below.
    return { queue: 'standard', escalation: null };
  }
}

/* ---- evaluate: mirrors governed_version.py's evaluate(). One generic function,
   no per-case logic. Walks the fact table in order; first match wins. No fact
   matches -> abstain, fail-closed, never guess. ---- */
function evaluate(ticket, facts) {
  for (const fact of facts) {
    const matches = Object.keys(fact.conditions).every(k => ticket[k] === fact.conditions[k]);
    if (matches) return Object.assign({}, fact.outcome);
  }
  return { status: 'hitl_required', reason: 'no governing fact matches this ticket, abstaining rather than guessing' };
}

/* ---- real, ast-counted numbers from code_version.py / code_version_v2.py.
   These are NOT recomputed here; they are what
   `python demos/ai-code-ratio/ratio_demo.py` actually prints. ---- */
const V1_BRANCHES = 9, V1_LOC = 30;
const V2_BRANCHES = 12, V2_LOC = 33;
const BRANCH_DELTA_PER_CASE = (V2_BRANCHES - V1_BRANCHES) / NEW_FACTS.length; // 1
const LOC_DELTA_PER_CASE = (V2_LOC - V1_LOC) / NEW_FACTS.length; // 1

const BASE_TICKETS = [];
for (const tier of ['free', 'pro', 'enterprise']) {
  for (const severity of ['low', 'medium', 'high']) {
    BASE_TICKETS.push({ plan_tier: tier, severity });
  }
}
const NEW_TICKETS = [
  { plan_tier: 'free', severity: 'critical' },
  { plan_tier: 'pro', severity: 'critical' },
  { plan_tier: 'enterprise', severity: 'critical' },
];
const UNGOVERNED_TICKET = { plan_tier: 'pro', severity: 'outage' }; // no branch, no fact, ever

/* ---- UI state ---- */
let branchesAdded = 0; // how many of the 3 new cases the code path has
let factsAdded = 0;    // how many of the 3 new cases the governed path has (moves with branchesAdded)

const $ = sel => document.querySelector(sel);

function fmt(v) { return v === null || v === undefined ? String(v) : (v.queue ? `${v.queue}${v.escalation ? ' / ' + v.escalation : ''}` : (v.status || JSON.stringify(v))); }

function renderCounters() {
  const codeBranches = V1_BRANCHES + branchesAdded * BRANCH_DELTA_PER_CASE;
  const codeLoc = V1_LOC + branchesAdded * LOC_DELTA_PER_CASE;
  $('#counters').innerHTML = `
    <div class="c"><div class="n">${codeBranches}</div><div class="l">code: branches (+${branchesAdded * BRANCH_DELTA_PER_CASE} from base)</div></div>
    <div class="c"><div class="n">+${branchesAdded * LOC_DELTA_PER_CASE}</div><div class="l">code: decision LOC added</div></div>
    <div class="c accent"><div class="n">+0</div><div class="l">governed: evaluator LOC changed</div></div>
    <div class="c accent"><div class="n">+${factsAdded}</div><div class="l">governed: fact rows added</div></div>
  `;
}

function renderTable() {
  const growingFacts = BASE_FACTS.concat(NEW_FACTS.slice(0, factsAdded));
  const allTickets = BASE_TICKETS.concat(NEW_TICKETS);
  const rows = allTickets.map((t, i) => {
    const isNew = i >= BASE_TICKETS.length;
    const newIdx = i - BASE_TICKETS.length;
    const codeOut = routeCode(t, branchesAdded);
    const governedOut = evaluate(t, growingFacts);
    const agree = fmt(codeOut) === fmt(governedOut) || (codeOut.queue === governedOut.queue && codeOut.escalation === governedOut.escalation);
    const pending = isNew && newIdx >= branchesAdded;
    const cls = pending ? ' class="stale"' : (isNew ? ' class="current"' : '');
    return `<tr${cls}>
      <td>${t.plan_tier}</td>
      <td>${t.severity}</td>
      <td>${fmt(codeOut)}</td>
      <td>${fmt(governedOut)}</td>
      <td>${agree ? '<span class="chip good">agree</span>' : '<span class="chip bad">differ</span>'}</td>
    </tr>`;
  }).join('');
  $('#table').innerHTML =
    `<table class="dtable"><thead><tr><th>plan_tier</th><th>severity</th><th>code_version</th><th>governed</th><th></th></tr></thead><tbody>${rows}</tbody></table>`;
}

function setVerdict(html) { $('#verdict').innerHTML = html; }

function render() {
  renderCounters();
  renderTable();
}

function init() {
  render();
  setVerdict(`<span class="chip blue">base requirement</span> <span class="dim">9/9 tickets agree; add a case to grow the requirement</span>`);
  $('#out').textContent = 'Base requirement: code_version.py (9 branches, 30 LOC) and governed_version.py (9 facts) agree on all 9 base tickets.';

  $('#addCaseBtn').addEventListener('click', () => {
    if (branchesAdded >= NEW_FACTS.length) {
      setVerdict('<span class="chip blue">all 3 new cases added</span> <span class="dim">code: 12 branches / 33 LOC · governed: +0 code / +3 facts</span>');
      return;
    }
    branchesAdded += 1;
    factsAdded += 1;
    const newCase = NEW_TICKETS[branchesAdded - 1];
    render();
    setVerdict(`<span class="chip blue">case added</span> <span class="dim">${newCase.plan_tier} / ${newCase.severity} now governed by both sides</span>`);
    $('#out').innerHTML =
      `<span class="acc">[code]</span> +1 elif branch (${branchesAdded}/${NEW_FACTS.length} added) → ${V1_BRANCHES + branchesAdded * BRANCH_DELTA_PER_CASE} branches, ${V1_LOC + branchesAdded * LOC_DELTA_PER_CASE} decision LOC  <span class="dim">(a developer wrote, reviewed, and shipped this)</span>\n` +
      `<span class="acc">[governed]</span> +1 fact row (${factsAdded}/${NEW_FACTS.length} added) → governed_version.py unchanged, 0 LOC delta`;
  });

  $('#ungovernedBtn').addEventListener('click', () => {
    const growingFacts = BASE_FACTS.concat(NEW_FACTS.slice(0, factsAdded));
    const governedOut = evaluate(UNGOVERNED_TICKET, growingFacts);
    const codeOut = routeCode(UNGOVERNED_TICKET, branchesAdded);
    setVerdict(`<span class="chip good">governed abstains</span> <span class="dim">code silently guesses instead, see below</span>`);
    $('#out').innerHTML =
      `ticket: ${JSON.stringify(UNGOVERNED_TICKET)}  <span class="dim">(severity "outage", no branch, no fact, ever)</span>\n` +
      `<span class="ok">[governed]</span> abstains → ${JSON.stringify(governedOut)}\n` +
      `<span class="no">[code]</span> silently returns → ${JSON.stringify(codeOut)}  <span class="dim">(falls through to else, no signal it was guessing)</span>`;
  });
}

document.addEventListener('DOMContentLoaded', init);

/*
  bounded-authority.js, a faithful, in-browser reimplementation of
  demos/bounded-authority/gate.py.

  Same closed-roster, fail-closed rules as the Python:
      propose(action, scope) -> proceed | escalated | blocked, decided BEFORE execution
        1. action not on the roster            -> blocked ("omission is prohibition")
        2. policy missing/unreadable caps       -> blocked (never guess a ceiling)
        3. scope exceeds the hard ceiling       -> blocked
        4. scope exceeds the soft cap           -> escalated (needs HITL)
        5. within caps                          -> proceed

  This is a convenience, not the proof. The proof is the Python you can run and
  change yourself. No dependencies, works from file://.
*/

const TIERS = ['yellow', 'orange', 'red', 'purple'];

/* ---- comma-formatted number, matches Python's f"{x:,}" for integers ---- */
function fmt(n) {
  return Number(n).toLocaleString('en-US');
}

/* ---- the Gate (mirrors gate.py) ---- */
class Gate {
  constructor() { this.roster = {}; }

  register(action, tier, softCap, hardCeiling) {
    if (!TIERS.includes(tier)) {
      throw new Error(`unknown risk tier '${tier}'; must be one of ${TIERS}`);
    }
    this.roster[action] = { tier, softCap, hardCeiling };
  }

  propose(action, scope) {
    const policy = this.roster[action];
    if (!policy) {
      return { outcome: 'blocked', reason: `'${action}' is not on the roster, omission is prohibition`, action, scope };
    }

    const hardKeys = Object.keys(policy.hardCeiling || {});
    if (hardKeys.length === 0) {
      // A registered action with no readable hard ceiling is a policy failure,
      // not permission to proceed. Fail closed: block rather than allow past
      // a ceiling we cannot confirm.
      return { outcome: 'blocked', reason: `'${action}' has no readable hard ceiling, fail-closed`, action, scope };
    }

    for (const dimension of Object.keys(scope)) {
      const requested = scope[dimension];
      const ceiling = policy.hardCeiling[dimension];
      if (ceiling === undefined) {
        // Scope names a dimension the policy never capped, same fail-closed
        // logic: an uncapped dimension is an unreadable ceiling, not a green light.
        return { outcome: 'blocked', reason: `'${action}' has no hard ceiling for '${dimension}', fail-closed`, action, scope };
      }
      if (requested > ceiling) {
        return {
          outcome: 'blocked',
          reason: `'${action}' requested ${dimension}=${fmt(requested)} exceeds hard ceiling ${fmt(ceiling)} (tier=${policy.tier})`,
          action, scope,
        };
      }
    }

    for (const dimension of Object.keys(scope)) {
      const requested = scope[dimension];
      const soft = policy.softCap[dimension];
      if (soft !== undefined && requested > soft) {
        return {
          outcome: 'escalated',
          reason: `'${action}' requested ${dimension}=${fmt(requested)} exceeds soft cap ${fmt(soft)} (tier=${policy.tier}), needs human-in-the-loop`,
          action, scope,
        };
      }
    }

    return { outcome: 'proceed', reason: `'${action}' within caps (tier=${policy.tier})`, action, scope };
  }
}

/* ---- the closed roster (mirrors _seeded_gate() in test_gate.py) ---- */
const gate = new Gate();
gate.register('send_email', 'yellow', { max_recipients: 50 }, { max_recipients: 200 });
gate.register('grant_refund', 'orange', { max_usd: 100 }, { max_usd: 1000 });
gate.register('delete_rows', 'red', { max_rows: 20 }, { max_rows: 100 });

/* wire_transfer is deliberately NOT registered here: it is the "unregistered
   action" option in the dropdown below, to show omission is prohibition. */
const DIMENSION = { send_email: 'max_recipients', grant_refund: 'max_usd', delete_rows: 'max_rows', wire_transfer: 'max_usd' };
const LABEL = { max_recipients: 'recipients', max_usd: 'usd', max_rows: 'rows' };

const $ = sel => document.querySelector(sel);

function renderRoster() {
  const rows = Object.keys(gate.roster).map(action => {
    const p = gate.roster[action];
    const dim = DIMENSION[action];
    const soft = p.softCap[dim] !== undefined ? fmt(p.softCap[dim]) : ',';
    const hard = p.hardCeiling[dim] !== undefined ? fmt(p.hardCeiling[dim]) : ',';
    return `<tr>
      <td>${action}</td>
      <td>${p.tier}</td>
      <td>${soft} ${LABEL[dim]}</td>
      <td>${hard} ${LABEL[dim]}</td>
    </tr>`;
  }).join('');
  const unregisteredRow = `<tr class="stale">
      <td>wire_transfer</td>
      <td class="dim">not registered</td>
      <td class="dim">n/a</td>
      <td class="dim">n/a</td>
    </tr>`;
  $('#roster').innerHTML =
    `<table class="dtable"><thead><tr><th>action</th><th>tier</th><th>soft cap</th><th>hard ceiling</th></tr></thead>` +
    `<tbody>${rows}${unregisteredRow}</tbody></table>`;
}

function renderActionSelect() {
  const opts = Object.keys(gate.roster).map(a => `<option value="${a}">${a}</option>`).join('');
  $('#actionSel').innerHTML = opts + `<option value="wire_transfer">wire_transfer (unregistered action)</option>`;
}

function setVerdict(html) { $('#verdict').innerHTML = html; }

function doPropose(action, magnitude) {
  const dim = DIMENSION[action];
  const scope = { [dim]: magnitude };
  const decision = gate.propose(action, scope);

  if (decision.outcome === 'proceed') {
    setVerdict(`<span class="chip good">proceed</span> <span class="dim">executes as proposed</span>`);
    $('#out').innerHTML = `<span class="ok">✓ PROCEED</span>\n  ${decision.reason}`;
  } else if (decision.outcome === 'escalated') {
    setVerdict(`<span class="chip blue">escalated</span> <span class="dim">needs human-in-the-loop</span>`);
    $('#out').innerHTML = `<span class="acc">⚠ ESCALATED</span>\n  ${decision.reason}\n  <span class="dim">nothing executes until a human approves this proposal.</span>`;
  } else {
    setVerdict(`<span class="chip bad">blocked</span> <span class="dim">refused before execution</span>`);
    $('#out').innerHTML = `<span class="no">✗ BLOCKED</span>\n  ${decision.reason}\n  <span class="dim">zero side effects ran. the refusal happened before execution, not after.</span>`;
  }
  return decision;
}

function init() {
  renderRoster();
  renderActionSelect();
  setVerdict('<span class="chip blue">not yet proposed</span> <span class="dim">pick an action and a magnitude, then propose</span>');

  $('#proposeBtn').addEventListener('click', () => {
    const action = $('#actionSel').value;
    const magnitude = Number($('#magInput').value) || 0;
    doPropose(action, magnitude);
  });

  $('#scenarioBtn').addEventListener('click', () => {
    $('#actionSel').value = 'delete_rows';
    $('#magInput').value = 10000;
    doPropose('delete_rows', 10000);
  });
}

document.addEventListener('DOMContentLoaded', init);

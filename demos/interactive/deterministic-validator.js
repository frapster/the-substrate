/*
  deterministic-validator.js, a faithful, in-browser reimplementation of
  demos/deterministic-validator/validator.py.

  Same shape as the Python: model proposes -> deterministic validate() grades it -> only
  a PASS is committed. A rejected proposal is DISCARDED, not patched: nothing here ever
  rewrites a failing proposal into a passing one. An llm_judge() can feed evidence into a
  proposal's review, but it has no path to the commit log: only Validator.validate() does.

  This is a convenience, not the proof. The proof is the Python you can run and change
  yourself.
*/

/* ---- constants (mirror validator.py) ---- */
const KNOWN_SOURCE_IDS = new Set(['src_101', 'src_102', 'src_103', 'src_104']);
const MAX_AMOUNT_USD = 500;

/* ---- Proposal: frozen-in-spirit (we never mutate one in place) ---- */
function makeProposal(intent, sourceId, amountUsd, model) {
  return Object.freeze({ intent, source_id: sourceId, amount_usd: amountUsd, model: model || 'claude' });
}

/* ---- llm_judge: a mocked second model. Deliberately naive: it only eyeballs the
   amount, and never checks the source. That is exactly why it cannot sit on the
   commit gate: a probabilistic checker of a probabilistic proposer has no
   deterministic floor. ---- */
function llmJudge(proposal) {
  if (proposal.amount_usd <= MAX_AMOUNT_USD) {
    return { approved: true, note: `amount $${proposal.amount_usd} looks reasonable` };
  }
  return { approved: false, note: `amount $${proposal.amount_usd} looks high` };
}

/* ---- Validator: the deterministic gate (mirrors Validator in validator.py) ---- */
class Validator {
  constructor() {
    this.commitLog = [];
    this.rejectedLog = [];
  }

  /* The deterministic checks. Real, hand-written rules, no model call in here.
     1. required fields present
     2. the cited source must exist in the known set (catches hallucinated citations)
     3. the amount must be positive and within the policy bound */
  validate(proposal) {
    if (!proposal.intent) {
      return { ok: false, reason: 'missing required field: intent' };
    }
    if (!KNOWN_SOURCE_IDS.has(proposal.source_id)) {
      return { ok: false, reason: `cited source '${proposal.source_id}' does not exist in known sources` };
    }
    if (proposal.amount_usd < 0) {
      return { ok: false, reason: `amount_usd ${proposal.amount_usd} must not be negative` };
    }
    if (proposal.amount_usd > MAX_AMOUNT_USD) {
      return { ok: false, reason: `amount_usd ${proposal.amount_usd} exceeds policy bound ${MAX_AMOUNT_USD}` };
    }
    return { ok: true, reason: 'passes all checks' };
  }

  /* Submit a proposal for commit. `judgment` is optional evidence from llmJudge(),
     accepted here purely so callers can log it alongside the decision; it is NEVER
     read by the gate below. Only validate() decides what commits.

     A passing proposal is appended to commitLog exactly as constructed: no field is
     rewritten, no value is clamped into range. A failing proposal is appended to
     rejectedLog with its reason and stays there unmodified. */
  submit(proposal, judgment) {
    const result = this.validate(proposal); // the gate consults ONLY validate(), judgment is never read here
    if (result.ok) {
      this.commitLog.push(proposal); // verbatim: no mutation, no auto-repair
    } else {
      this.rejectedLog.push({ proposal, reason: result.reason });
    }
    return result;
  }
}

/* ---- UI ---- */
const validator = new Validator();
let lastSubmission = null; // { proposal, judgment, result, judged }

const $ = sel => document.querySelector(sel);

function deepEqual(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function renderLogs() {
  const commitRows = validator.commitLog.map((p, i) => `<tr>
      <td>${i}</td>
      <td>${p.intent}</td>
      <td><span class="hash">${p.source_id}</span></td>
      <td>$${p.amount_usd}</td>
    </tr>`).join('');
  $('#commitTable').innerHTML =
    `<table class="dtable"><thead><tr><th>#</th><th>intent</th><th>source</th><th>amount</th></tr></thead>
     <tbody>${commitRows || '<tr><td colspan="4" class="dim">(empty)</td></tr>'}</tbody></table>`;

  const rejectRows = validator.rejectedLog.map((e, i) => `<tr class="broken">
      <td>${i}</td>
      <td>${e.proposal.intent || '(missing)'}</td>
      <td><span class="hash">${e.proposal.source_id}</span></td>
      <td>$${e.proposal.amount_usd}</td>
      <td>${e.reason}</td>
    </tr>`).join('');
  $('#rejectTable').innerHTML =
    `<table class="dtable"><thead><tr><th>#</th><th>intent</th><th>source</th><th>amount</th><th>reason</th></tr></thead>
     <tbody>${rejectRows || '<tr><td colspan="5" class="dim">(empty)</td></tr>'}</tbody></table>`;
}

function setVerdict(html) { $('#verdict').innerHTML = html; }

function currentProposal() {
  const intent = $('#intent').value.trim();
  const sourceId = $('#sourceId').value;
  const amountRaw = $('#amount').value;
  const amount = amountRaw === '' ? NaN : parseInt(amountRaw, 10);
  return makeProposal(intent, sourceId, amount, 'claude');
}

function doSubmit() {
  const useJudge = $('#judgeToggle').checked;
  const proposal = currentProposal();
  const judgment = useJudge ? llmJudge(proposal) : null;
  const result = validator.submit(proposal, judgment);
  lastSubmission = { proposal, judgment, result, judged: useJudge };
  renderLogs();

  const judgeLine = useJudge
    ? `<span class="dim">llm_judge: approved=${judgment.approved}, ${judgment.note}${judgment.approved && !result.ok ? '  <span class="no">(the judge is fooled; the deterministic gate is not)</span>' : ''}</span>\n  `
    : '';

  if (result.ok) {
    setVerdict('<span class="chip good">committed</span> <span class="dim">passed every deterministic check</span>');
    $('#out').innerHTML =
      `${judgeLine}<span class="ok">&#10003; COMMITTED</span>  <span class="dim">${result.reason}</span>\n` +
      `  <span class="dim">committed record equals the proposal verbatim: ${deepEqual(proposal, validator.commitLog[validator.commitLog.length - 1])}</span>`;
  } else {
    setVerdict('<span class="chip bad">discarded</span> <span class="dim">' + result.reason + '</span>');
    const stillBad = validator.rejectedLog[validator.rejectedLog.length - 1].proposal;
    $('#out').innerHTML =
      `${judgeLine}<span class="no">&#10007; DISCARDED</span>  <span class="dim">${result.reason}</span>\n` +
      (useJudge ? `  <span class="no">judge approval could not commit it, submit() never reads judgment</span>\n` : '') +
      `  <span class="dim">stored rejected record: source_id still '${stillBad.source_id}', amount_usd still ${stillBad.amount_usd}, nothing repaired it</span>`;
  }
}

function init() {
  renderLogs();
  setVerdict('<span class="chip blue">not yet submitted</span> <span class="dim">edit the proposal, then submit</span>');

  $('#submitBtn').addEventListener('click', doSubmit);

  $('#loadHallucination').addEventListener('click', () => {
    $('#intent').value = 'grant_refund';
    $('#sourceId').value = 'src_999';
    $('#amount').value = '40';
    setVerdict('<span class="chip blue">loaded</span> <span class="dim">src_999 does not exist in KNOWN_SOURCE_IDS, try submitting, with and without the judge</span>');
  });

  $('#loadValid').addEventListener('click', () => {
    $('#intent').value = 'grant_refund';
    $('#sourceId').value = 'src_101';
    $('#amount').value = '40';
    setVerdict('<span class="chip blue">loaded</span> <span class="dim">a grounded, in-policy proposal</span>');
  });
}

document.addEventListener('DOMContentLoaded', init);

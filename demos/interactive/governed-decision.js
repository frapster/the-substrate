/*
  governed-decision.js, in-browser reimplementation of demos/governed-decision/pipeline.py.

  One intent flows through five minimal stages: bounded gate, evidence check,
  deterministic validator, audited hash-chained ledger, reversible commit. Any stage
  can refuse, and nothing partial commits. Same reason strings as the Python.

  A convenience, not the proof. The proof is the Python you can run and change.
  Self-contained SHA-256 + canonical JSON (copied from audit-ledger.js) so hashes match.
*/

/* ---- SHA-256 (synchronous, matches hashlib.sha256().hexdigest()) ---- */
const sha256 = (function () {
  function rotr(n, x) { return (x >>> n) | (x << (32 - n)); }
  const K = [
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  function toBytes(str) {
    const utf8 = unescape(encodeURIComponent(str));
    const bytes = new Array(utf8.length);
    for (let i = 0; i < utf8.length; i++) bytes[i] = utf8.charCodeAt(i);
    return bytes;
  }
  return function (message) {
    let H = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    const bytes = toBytes(message);
    const l = bytes.length * 8;
    bytes.push(0x80);
    while (bytes.length % 64 !== 56) bytes.push(0);
    for (let i = 7; i >= 0; i--) bytes.push((l / Math.pow(2, i * 8)) & 0xff);
    const w = new Array(64);
    for (let j = 0; j < bytes.length; j += 64) {
      for (let i = 0; i < 16; i++)
        w[i] = (bytes[j+i*4]<<24)|(bytes[j+i*4+1]<<16)|(bytes[j+i*4+2]<<8)|(bytes[j+i*4+3]);
      for (let i = 16; i < 64; i++) {
        const s0 = rotr(7,w[i-15])^rotr(18,w[i-15])^(w[i-15]>>>3);
        const s1 = rotr(17,w[i-2])^rotr(19,w[i-2])^(w[i-2]>>>10);
        w[i] = (w[i-16]+s0+w[i-7]+s1)|0;
      }
      let [a,b,c,d,e,f,g,h] = H;
      for (let i = 0; i < 64; i++) {
        const S1 = rotr(6,e)^rotr(11,e)^rotr(25,e);
        const ch = (e&f)^(~e&g);
        const t1 = (h+S1+ch+K[i]+w[i])|0;
        const S0 = rotr(2,a)^rotr(13,a)^rotr(22,a);
        const maj = (a&b)^(a&c)^(b&c);
        const t2 = (S0+maj)|0;
        h=g; g=f; f=e; e=(d+t1)|0; d=c; c=b; b=a; a=(t1+t2)|0;
      }
      H = [ (H[0]+a)|0,(H[1]+b)|0,(H[2]+c)|0,(H[3]+d)|0,(H[4]+e)|0,(H[5]+f)|0,(H[6]+g)|0,(H[7]+h)|0 ];
    }
    return H.map(x => (x>>>0).toString(16).padStart(8,'0')).join('');
  };
})();
function canonicalJSON(obj) {
  if (obj === null || typeof obj !== 'object') return JSON.stringify(obj);
  if (Array.isArray(obj)) return '[' + obj.map(canonicalJSON).join(',') + ']';
  const keys = Object.keys(obj).sort();
  return '{' + keys.map(k => JSON.stringify(k) + ':' + canonicalJSON(obj[k])).join(',') + '}';
}

/* ---- the five stages (mirror pipeline.py) ---- */
class GovernanceRefusal extends Error {
  constructor(stage, reason) { super(`[${stage}] ${reason}`); this.stage = stage; this.reason = reason; }
}

const ROSTER = {
  grant_refund: { tier: 'yellow', soft: 100, hard: 500, dim: 'usd' },
  delete_rows:  { tier: 'red',    soft: 50,  hard: 100, dim: 'rows' },
};
function boundedCheck(intent) {
  const p = ROSTER[intent.action];
  if (!p) throw new GovernanceRefusal('bounded', `action '${intent.action}' is not on the roster (omission is prohibition)`);
  const mag = intent.scope[p.dim];
  if (mag === undefined) throw new GovernanceRefusal('bounded', `no '${p.dim}' in scope to check against the blast-radius cap`);
  if (mag > p.hard) throw new GovernanceRefusal('bounded', `${p.dim}=${mag} exceeds hard cap ${p.hard} (tier ${p.tier}), blocked before execution`);
  if (mag > p.soft) return 'escalated';
  return 'proceed';
}

const SOURCES = {};
function addSource(id, text) { SOURCES[id] = sha256(text); return SOURCES[id]; }
function evidenceRequire(intent) {
  if (!intent.source_id || !(intent.source_id in SOURCES))
    throw new GovernanceRefusal('evidence', `claim carries no resolvable source, nothing is asserted without provenance`);
  return SOURCES[intent.source_id];
}

const REQUIRED = ['action', 'amount_usd'];
const MAX_USD = 500;
function validate(intent) {
  const p = intent.proposed_value;
  const missing = REQUIRED.filter(f => !(f in p));
  if (missing.length) throw new GovernanceRefusal('validated', `proposal missing required field(s) ${JSON.stringify(missing)}, discarded, not patched`);
  if ((p.amount_usd || 0) > MAX_USD) throw new GovernanceRefusal('validated', `proposed amount_usd=${p.amount_usd} exceeds validator bound ${MAX_USD}, discarded, not patched`);
  return Object.assign({}, p); // verbatim
}

const GENESIS = '0'.repeat(64);
class AuditLedger {
  constructor() { this.rows = []; }
  get head() { return this.rows.length ? this.rows[this.rows.length - 1].hash : GENESIS; }
  append(body) {
    const index = this.rows.length, prev = this.head;
    const hash = sha256(prev + '|' + index + '|' + canonicalJSON(body));
    this.rows.push({ index, prev, body, hash });
    return hash;
  }
  verify() {
    let ep = GENESIS;
    for (let i = 0; i < this.rows.length; i++) {
      const r = this.rows[i];
      if (r.prev !== ep) return false;
      if (sha256(r.prev + '|' + i + '|' + canonicalJSON(r.body)) !== r.hash) return false;
      ep = r.hash;
    }
    return true;
  }
}
function stateHash(s) { return sha256(canonicalJSON(s)); }
class ReversibleStore {
  constructor() { this.versions = [{}]; }
  get state() { return Object.assign({}, this.versions[this.versions.length - 1]); }
  stateHashAt(v) { return stateHash(this.versions[v]); }
  apply(change) { const s = Object.assign({}, this.versions[this.versions.length - 1], change); this.versions.push(s); return this.versions.length - 1; }
  restore(v) { this.versions.push(Object.assign({}, this.versions[v])); return this.versions.length - 1; }
}

function decide(intent, ledger, store) {
  const trace = { bounded: null, evidence: null, validated: null, audited: null, reversible: null };
  try {
    const outcome = boundedCheck(intent);            trace.bounded = 'pass';
    const srcHash = evidenceRequire(intent);          trace.evidence = 'pass';
    const record = validate(intent);                  trace.validated = 'pass';
    const ledgerHash = ledger.append({ action: intent.action, outcome, source_hash: srcHash.slice(0, 12), record }); trace.audited = 'pass';
    const version = store.apply({ [intent.action]: record }); trace.reversible = 'pass';
    return { committed: true, outcome, ledgerHash, version, trace };
  } catch (r) {
    if (r instanceof GovernanceRefusal) { trace[r.stage] = 'fail'; return { committed: false, refusalStage: r.stage, refusalReason: r.reason, trace }; }
    throw r;
  }
}

/* ---- UI ---- */
const $ = s => document.querySelector(s);
const STAGES = ['bounded', 'evidence', 'validated', 'audited', 'reversible'];
const STAGE_LABEL = { bounded: 'Bounded', evidence: 'Evidence', validated: 'Validated', audited: 'Audited', reversible: 'Reversible' };

function renderStages(trace) {
  $('#stages').innerHTML = STAGES.map((s, i) => {
    const st = trace ? trace[s] : null;
    const cls = st === 'pass' ? ' pass' : (st === 'fail' ? ' fail' : '');
    return `<div class="stage${cls}"><div class="sn">stage ${i + 1}</div><div class="st">${STAGE_LABEL[s]}</div></div>`;
  }).join('');
}

const PRESETS = {
  good:    { label: 'well-formed intent', action: 'grant_refund', mag: 40, source: 'policy-refunds-v3', fields: 'action,amount_usd' },
  scope:   { label: 'over-scope', action: 'delete_rows', mag: 10000, source: 'policy-refunds-v3', fields: 'action,amount_usd' },
  unsourced: { label: 'unsourced claim', action: 'grant_refund', mag: 40, source: '', fields: 'action,amount_usd' },
  invalid: { label: 'invalid proposal', action: 'grant_refund', mag: 40, source: 'policy-refunds-v3', fields: 'action' },
  unreg:   { label: 'unregistered action', action: 'wire_transfer', mag: 10, source: 'policy-refunds-v3', fields: 'action,amount_usd' },
};

function runIntent(preset) {
  const ledger = new AuditLedger();
  const store = new ReversibleStore();
  for (const k in SOURCES) delete SOURCES[k];
  addSource('policy-refunds-v3', 'Refunds up to $500 are pre-authorized for tier-1 accounts.');

  const fields = preset.fields.split(',').filter(Boolean);
  const proposed = {};
  fields.forEach(f => { proposed[f] = f === 'amount_usd' ? (preset.action === 'delete_rows' ? 0 : preset.mag) : preset.action; });
  const scope = preset.action === 'delete_rows' ? { rows: preset.mag } : { usd: preset.mag };
  const intent = { action: preset.action, scope, source_id: preset.source || null, proposed_value: proposed };

  const d = decide(intent, ledger, store);
  renderStages(d.trace);

  if (d.committed) {
    const preHash = store.stateHashAt(0);
    const restored = store.restore(0);
    const reversibleOk = store.stateHashAt(restored) === preHash;
    const auditOk = ledger.verify();
    $('#verdict').innerHTML = `<span class="chip good">committed</span> <span class="dim">outcome: ${d.outcome} · ledger ${d.ledgerHash.slice(0, 8)}… · version ${d.version}</span>`;
    $('#out').innerHTML =
      `<span class="ok">✓ committed through all five stages</span>\n` +
      `  <span class="dim">bounded → evidence → validated → audited → reversible</span>\n` +
      `  ${auditOk ? '<span class="ok">✓</span>' : '<span class="no">✗</span>'} audit chain verifies after commit\n` +
      `  ${reversibleOk ? '<span class="ok">✓</span>' : '<span class="no">✗</span>'} restore(0) reproduces the exact prior state hash (${store.stateHashAt(restored).slice(0, 8)}…)`;
  } else {
    $('#verdict').innerHTML = `<span class="chip bad">refused</span> <span class="no">at ${d.refusalStage}</span>`;
    $('#out').innerHTML =
      `<span class="no">✗ refused at ${d.refusalStage}</span>\n  <span class="dim">${d.refusalReason}</span>\n` +
      `  <span class="dim">nothing partial committed: no ledger row, no new version.</span>`;
  }
}

function init() {
  renderStages(null);
  $('#verdict').innerHTML = '<span class="chip blue">ready</span> <span class="dim">run a well-formed intent, or break one stage</span>';
  document.querySelectorAll('[data-preset]').forEach(btn => {
    btn.addEventListener('click', () => runIntent(PRESETS[btn.dataset.preset]));
  });
  runIntent(PRESETS.good);
}
document.addEventListener('DOMContentLoaded', init);

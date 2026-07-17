/*
  audit-ledger.js, a faithful, in-browser reimplementation of demos/audit-ledger/ledger.py.

  Same chaining rule as the Python, so the hashes match byte-for-byte:
      row.hash = SHA256( prev_hash + "|" + index + "|" + canonical_json(body) )
  canonical_json = JSON with sorted keys and no whitespace (Python's
  json.dumps(sort_keys=True, separators=(",",":"))). Genesis prev-hash is 64 zeros.

  This is a convenience, not the proof. The proof is the Python you can run and
  change yourself. Self-contained SHA-256 (no dependencies, no build, works from file://).
*/

/* ---- SHA-256 (public-domain style, synchronous, matches hashlib.sha256().hexdigest()) ---- */
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
    // UTF-8 encode
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

/* ---- canonical JSON: sorted keys, no whitespace (matches Python json.dumps) ---- */
function canonicalJSON(obj) {
  if (obj === null || typeof obj !== 'object') return JSON.stringify(obj);
  if (Array.isArray(obj)) return '[' + obj.map(canonicalJSON).join(',') + ']';
  const keys = Object.keys(obj).sort();
  return '{' + keys.map(k => JSON.stringify(k) + ':' + canonicalJSON(obj[k])).join(',') + '}';
}

const GENESIS = '0'.repeat(64);
function computeHash(prevHash, index, body) {
  return sha256(prevHash + '|' + index + '|' + canonicalJSON(body));
}

/* ---- the Ledger (mirrors ledger.py) ---- */
class Ledger {
  constructor() { this.rows = []; }
  get head() { return this.rows.length ? this.rows[this.rows.length - 1].hash : GENESIS; }
  append(body) {
    const index = this.rows.length;
    const prev = this.head;
    const hash = computeHash(prev, index, body);
    this.rows.push({ index, prev, body, hash });
    return this.rows[index];
  }
  tamperBody(index, newBody) { this.rows[index].body = newBody; } // silent edit, hash left stale
  verify() {
    let expectedPrev = GENESIS;
    for (let i = 0; i < this.rows.length; i++) {
      const row = this.rows[i];
      if (row.prev !== expectedPrev)
        return { ok: false, brokenIndex: i, reason: `row ${i} prev_hash ${row.prev.slice(0,8)}… does not link to expected ${expectedPrev.slice(0,8)}… (chain reordered or truncated)` };
      const recomputed = computeHash(row.prev, row.index, row.body);
      if (recomputed !== row.hash)
        return { ok: false, brokenIndex: i, reason: `row ${i} recomputed hash ${recomputed.slice(0,8)}… != stored ${row.hash.slice(0,8)}… (body was altered)` };
      expectedPrev = row.hash;
    }
    return { ok: true, checked: this.rows.length, reason: 'all rows intact' };
  }
}

/* ---- UI ---- */
const ledger = new Ledger();
const seed = [
  { action: 'grant_refund', amount_usd: 40, model: 'claude', verdict: 'allow' },
  { action: 'escalate_ticket', priority: 'high', model: 'claude', verdict: 'allow' },
  { action: 'delete_account', user: 'u_8831', model: 'claude', verdict: 'deny' },
  { action: 'publish_post', post: 'p_552', model: 'claude', verdict: 'allow' },
];
seed.forEach(d => ledger.append(d));
let lastVerify = null;

const $ = sel => document.querySelector(sel);

function renderChain() {
  const broken = lastVerify && !lastVerify.ok ? lastVerify.brokenIndex : -1;
  const rows = ledger.rows.map(r => {
    const cls = r.index === broken ? ' class="broken"' : (r._tampered ? ' class="tampered"' : '');
    return `<tr${cls}>
      <td>${r.index}</td>
      <td>${r.body.action || '(decision)'}</td>
      <td>${r.body.verdict ?? ''}</td>
      <td><span class="hash">${r.hash.slice(0,12)}…</span></td>
      <td><span class="hash">${r.prev.slice(0,8)}…</span></td>
    </tr>`;
  }).join('');
  $('#chain').innerHTML =
    `<table class="dtable"><thead><tr><th>#</th><th>action</th><th>verdict</th><th>hash</th><th>prev</th></tr></thead><tbody>${rows}</tbody></table>`;
  // populate the tamper target selector
  const sel = $('#tamperRow');
  sel.innerHTML = ledger.rows.map(r => `<option value="${r.index}">row ${r.index}, ${r.body.action}</option>`).join('');
}

function setVerdict(html) { $('#verdict').innerHTML = html; }

function doVerify() {
  lastVerify = ledger.verify();
  renderChain();
  if (lastVerify.ok) {
    setVerdict(`<span class="chip good">chain intact</span> <span class="dim">${lastVerify.checked}/${ledger.rows.length} rows verified by recomputation</span>`);
  } else {
    setVerdict(`<span class="chip bad">chain broken</span> <span class="no">at row ${lastVerify.brokenIndex}</span>`);
    $('#out').innerHTML = `<span class="no">✗ CHAIN BROKEN at row ${lastVerify.brokenIndex}</span>\n  <span class="dim">${lastVerify.reason}</span>\n  <span class="dim">row ${lastVerify.brokenIndex} no longer matches its hash, so every row after it is untrustworthy, the forgery cannot hide.</span>`;
  }
}

function init() {
  renderChain();
  setVerdict('<span class="chip blue">not yet verified</span> <span class="dim">append or tamper, then verify</span>');

  $('#appendBtn').addEventListener('click', () => {
    const action = $('#newAction').value.trim() || 'decide';
    const verdict = $('#newVerdict').value;
    ledger.append({ action, model: 'claude', verdict });
    lastVerify = null;
    renderChain();
    setVerdict('<span class="chip blue">appended</span> <span class="dim">a new decision was committed to the chain; verify to confirm intact</span>');
    $('#out').textContent = `Committed row ${ledger.rows.length - 1}: ${action} → ${verdict}`;
  });

  $('#tamperBtn').addEventListener('click', () => {
    const idx = parseInt($('#tamperRow').value, 10);
    const row = ledger.rows[idx];
    const flipped = row.body.verdict === 'deny' ? 'allow' : 'deny';
    const edited = Object.assign({}, row.body, { verdict: flipped });
    ledger.tamperBody(idx, edited); // hash left unchanged, a silent edit
    row._tampered = true;
    lastVerify = null;
    renderChain();
    setVerdict('<span class="chip bad">tampered</span> <span class="dim">row ' + idx + ' verdict flipped to <b>' + flipped + '</b>, hash left unchanged, now verify</span>');
    $('#out').innerHTML = `<span class="no">[tamper]</span> row ${idx} verdict → ${flipped}  <span class="dim">(hash NOT recomputed, reaching past the append-only API)</span>`;
  });

  $('#verifyBtn').addEventListener('click', doVerify);
}

document.addEventListener('DOMContentLoaded', init);

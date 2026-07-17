/*
  reversible-actions.js, a faithful, in-browser reimplementation of
  demos/reversible-actions/reversible.py.

  Same versioning rule as the Python, so the hashes match byte-for-byte:
      version.state_hash = SHA256( canonical_json(state) )
  canonical_json = JSON with sorted keys and no whitespace (Python's
  json.dumps(sort_keys=True, separators=(",",":"))).

  apply(change)      appends a NEW version (supersede-forward); predecessors untouched
  restore(version=N) appends a NEW version equal to version N's state (recovery IS
                      forward motion through the chain, not a rewind)

  There is no update() or delete() on a stored version. In-place mutation is forbidden
  and FAILS CLOSED. High-impact actions are gated: an ungated apply(..., highImpact:
  true) is refused outright.

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

function computeStateHash(state) {
  return sha256(canonicalJSON(state));
}

/* ---- errors (mirror reversible.py) ---- */
class AppendOnlyViolation extends Error {}
class UngatedHighImpactError extends Error {}

/* ---- the Store (mirrors reversible.py) ---- */
class Store {
  constructor() {
    this.versions = [];
    const state = {};
    this.versions.push({ index: 0, state, stateHash: computeStateHash(state), note: 'genesis', operatorDestructive: false });
  }
  get head() { return this.versions[this.versions.length - 1]; }
  get state() { return this.head.state; }
  get stateHash() { return this.head.stateHash; }
  snapshotAt(index) { return this.versions[index].stateHash; }

  apply(change, { highImpact = false, gated = false, note = '' } = {}) {
    // The only sanctioned mutation: append a NEW version with `change` merged
    // into current state (supersede-forward). All predecessors are preserved
    // untouched. High-impact changes are gated: an ungated one is refused.
    if (highImpact && !gated) {
      throw new UngatedHighImpactError(
        `high-impact change ${JSON.stringify(change)} refused: no approval token ` +
        `(pass gated=true after HITL approval)`
      );
    }
    const newState = Object.assign({}, this.state, change);
    return this._commit(newState, note || `apply ${JSON.stringify(change)}`);
  }

  restore(index) {
    // Reversibility guarantee: recover a prior state by supersede-forward,
    // appending a NEW version equal to `index`'s state. Deterministic: the
    // returned version's state_hash equals snapshotAt(index) exactly, byte-for-byte.
    const snapshot = this.versions[index];
    const restored = this._commit(Object.assign({}, snapshot.state), `restore(version=${index})`);
    if (restored.stateHash !== snapshot.stateHash) throw new Error('restore is not deterministic'); // should never happen
    return restored;
  }

  operatorDestructive(reason) {
    // Reserved, audited operator-destructive path (e.g. a full purge). It is
    // explicitly marked and itself writes an audit note: even destructive recovery
    // is recorded as a new version, preserving full audit history.
    if (!reason) throw new Error('operatorDestructive requires a reason (illustrative audit note)');
    return this._commit({}, `operator_destructive: ${reason}`, true);
  }

  _commit(newState, note, operatorDestructive = false) {
    const index = this.versions.length;
    const stateHash = computeStateHash(newState);
    const version = { index, state: newState, stateHash, note, operatorDestructive };
    this.versions.push(version);
    return version;
  }

  verifyChain() {
    for (let i = 0; i < this.versions.length; i++) {
      const v = this.versions[i];
      if (v.index !== i)
        return { ok: false, checked: i, brokenIndex: i, reason: `version ${i} carries index ${v.index} (chain reordered or truncated)` };
      const recomputed = computeStateHash(v.state);
      if (recomputed !== v.stateHash)
        return { ok: false, checked: i, brokenIndex: i, reason: `version ${i} recomputed hash ${recomputed.slice(0,8)}… != stored ${v.stateHash.slice(0,8)}… (state was altered)` };
    }
    return { ok: true, checked: this.versions.length, brokenIndex: null, reason: 'all versions intact' };
  }

  // --- durable append-only guard ---------------------------------------------------
  // These model the sanctioned-mutation boundary: any attempt to edit or remove a
  // committed version in place is refused unconditionally. There is no "sometimes";
  // the guard fails closed every time it is invoked.

  updateInPlace(index, change) {
    // Illustrative ONLY: attempting to mutate a stored version's state directly,
    // instead of superseding forward via apply(). FAILS CLOSED.
    throw new AppendOnlyViolation(
      `in-place update of version ${index} refused: durable append-only guard, ` +
      `mutate via apply(), never in place`
    );
  }

  deleteInPlace(index) {
    // Illustrative ONLY: attempting to remove a stored version directly. FAILS CLOSED.
    throw new AppendOnlyViolation(
      `in-place delete of version ${index} refused: durable append-only guard, ` +
      `history is immutable`
    );
  }
}

/* ---- UI ---- */
const store = new Store();
store.apply({ balance_usd: 100, status: 'active' }, { gated: true });
store.apply({ status: 'verified' }, { gated: true });

const $ = sel => document.querySelector(sel);

function renderChain() {
  const rows = store.versions.map(v => {
    const cls = v.index === store.head.index ? ' class="current"' : '';
    const changeLabel = v.note.length > 40 ? v.note.slice(0, 37) + '…' : v.note;
    return `<tr${cls}>
      <td>${v.index}</td>
      <td>${changeLabel}</td>
      <td><span class="hash">${v.stateHash.slice(0,12)}…</span></td>
    </tr>`;
  }).join('');
  $('#chain').innerHTML =
    `<table class="dtable"><thead><tr><th>#</th><th>change</th><th>state_hash</th></tr></thead><tbody>${rows}</tbody></table>`;
  // populate the restore target selector
  const sel = $('#restoreTo');
  const prevVal = sel.value;
  sel.innerHTML = store.versions.map(v => `<option value="${v.index}">version ${v.index}, ${v.note}</option>`).join('');
  if (prevVal && store.versions[prevVal]) sel.value = prevVal;
}

function setVerdict(html) { $('#verdict').innerHTML = html; }

function init() {
  renderChain();
  setVerdict('<span class="chip blue">2 gated versions committed</span> <span class="dim">apply, refuse, guard, or restore below</span>');
  $('#out').textContent = `store head: version ${store.head.index}  state_hash=${store.stateHash.slice(0,12)}…  state=${JSON.stringify(store.state)}`;

  $('#applyBtn').addEventListener('click', () => {
    const key = $('#changeKey').value.trim() || 'field';
    let val = $('#changeVal').value.trim();
    if (val !== '' && !isNaN(Number(val))) val = Number(val);
    const change = { [key]: val };
    const v = store.apply(change, { gated: true, note: `apply ${JSON.stringify(change)}` });
    renderChain();
    setVerdict(`<span class="chip good">applied</span> <span class="dim">version ${v.index} committed forward; predecessors untouched</span>`);
    $('#out').innerHTML = `<span class="ok">[apply]</span> version ${v.index}  hash=${v.stateHash.slice(0,12)}…  state=${JSON.stringify(v.state)}`;
  });

  $('#ungatedBtn').addEventListener('click', () => {
    const preCount = store.versions.length;
    try {
      store.apply({ balance_usd: 0 }, { highImpact: true });
      setVerdict('<span class="chip bad">gate did not hold</span>');
      $('#out').textContent = 'the change applied, the gate did not hold!';
    } catch (e) {
      if (e instanceof UngatedHighImpactError) {
        renderChain();
        setVerdict(`<span class="chip bad">refused</span> <span class="dim">no approval token; versions unchanged (${store.versions.length} == ${preCount})</span>`);
        $('#out').innerHTML = `<span class="no">[refused]</span> ${e.message}`;
      } else throw e;
    }
  });

  $('#updateBtn').addEventListener('click', () => {
    const idx = store.head.index > 0 ? 1 : 0;
    try {
      store.updateInPlace(idx, { status: 'banned' });
      setVerdict('<span class="chip bad">guard failed</span>');
      $('#out').textContent = 'in-place update succeeded, the append-only guard failed!';
    } catch (e) {
      if (e instanceof AppendOnlyViolation) {
        renderChain();
        setVerdict('<span class="chip bad">fails closed</span> <span class="dim">durable append-only guard refused the in-place update</span>');
        $('#out').innerHTML = `<span class="no">[fails closed]</span> ${e.message}`;
      } else throw e;
    }
  });

  $('#deleteBtn').addEventListener('click', () => {
    try {
      store.deleteInPlace(0);
      setVerdict('<span class="chip bad">guard failed</span>');
      $('#out').textContent = 'in-place delete succeeded, the append-only guard failed!';
    } catch (e) {
      if (e instanceof AppendOnlyViolation) {
        renderChain();
        setVerdict('<span class="chip bad">fails closed</span> <span class="dim">durable append-only guard refused the in-place delete</span>');
        $('#out').innerHTML = `<span class="no">[fails closed]</span> ${e.message}`;
      } else throw e;
    }
  });

  $('#restoreBtn').addEventListener('click', () => {
    const idx = parseInt($('#restoreTo').value, 10);
    const targetHash = store.snapshotAt(idx);
    const restored = store.restore(idx);
    renderChain();
    const match = restored.stateHash === targetHash;
    setVerdict(match
      ? `<span class="chip good">restored</span> <span class="dim">version ${restored.index} reproduces version ${idx}'s state_hash exactly</span>`
      : `<span class="chip bad">mismatch</span> <span class="dim">restored hash != version ${idx} hash</span>`);
    $('#out').innerHTML = `<span class="ok">[restore]</span> version ${restored.index}  hash=${restored.stateHash.slice(0,12)}…  state=${JSON.stringify(restored.state)}\n  <span class="dim">target version ${idx} hash=${targetHash.slice(0,12)}…</span>\n  <span class="${match ? 'ok' : 'no'}">${match ? '✓ state_hash matches version ' + idx + ' exactly, byte-for-byte.' : '✗ hash does not match'}</span>`;
  });
}

document.addEventListener('DOMContentLoaded', init);

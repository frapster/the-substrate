/*
  evidence-provenance.js, a faithful, in-browser reimplementation of
  demos/evidence-provenance/evidence.py.

  Same pinning rule as the Python, so the hashes match byte-for-byte:
      claim.pinned_hash = SHA256(source.text at assert-time)
  A claim naming an unregistered source is REFUSED before it is ever stored:
  "no evidence without a resolvable source." verify() recomputes the source's
  CURRENT hash and compares it to the pinned hash; a mismatch detaches the claim.

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

/* ---- content_hash: the identity function for a source (matches evidence.py) ---- */
function contentHash(text) { return sha256(text); }

/* ---- the EvidenceStore (mirrors evidence.py) ---- */
class EvidenceStore {
  constructor() { this.sources = {}; this.claims = []; }

  addSource(sourceId, text) {
    this.sources[sourceId] = { sourceId, text };
    return contentHash(text);
  }

  currentHash(sourceId) {
    const source = this.sources[sourceId];
    return source ? contentHash(source.text) : null;
  }

  // Fails closed: no evidence without a resolvable source.
  assertClaim(statement, sourceId) {
    const source = this.sources[sourceId];
    if (!source) {
      return {
        ok: false,
        reason: `claim ${JSON.stringify(statement)} names source ${JSON.stringify(sourceId)}, which is not registered, no evidence without a resolvable source`,
      };
    }
    const claim = { statement, sourceId, pinnedHash: contentHash(source.text), trustClass: 'untrusted' };
    this.claims.push(claim);
    return { ok: true, claim };
  }

  verify(claim) {
    const source = this.sources[claim.sourceId];
    if (!source) {
      return { ok: false, reason: `source ${JSON.stringify(claim.sourceId)} no longer registered, claim is detached (source missing)` };
    }
    const current = contentHash(source.text);
    if (current !== claim.pinnedHash) {
      return {
        ok: false,
        reason: `source ${JSON.stringify(claim.sourceId)} current hash ${current.slice(0,8)}… != pinned ${claim.pinnedHash.slice(0,8)}… (source was edited after assert-time)`,
      };
    }
    return { ok: true, reason: 'pinned hash matches current source' };
  }

  // --- attacker simulation helper (NOT part of the sanctioned API) -------------
  // Reaches past addSource() to mutate an already-stored source's text in place.
  tamperSource(sourceId, newText) { this.sources[sourceId].text = newText; }
}

/* ---- UI ---- */
const store = new EvidenceStore();
store.addSource('policy_refund_v1', 'Refunds under $50 are auto-approved.');
store.addSource('policy_delete_v1', 'Account deletion requires manager review.');
store.assertClaim('A $40 refund may be auto-approved.', 'policy_refund_v1');
store.assertClaim('Deleting u_8831 needs manager sign-off.', 'policy_delete_v1');
store.assertClaim('A $45 refund may be auto-approved.', 'policy_refund_v1');

// pending textarea edits keyed by sourceId, applied only on "recompute"
const pendingEdits = {};

const $ = sel => document.querySelector(sel);

function renderSources() {
  const rows = Object.values(store.sources).map(s => {
    const pending = pendingEdits[s.sourceId] !== undefined ? pendingEdits[s.sourceId] : s.text;
    const dirty = pending !== s.text;
    return `<div class="pg-row" data-source="${s.sourceId}" style="align-items:flex-start">
      <div class="field" style="width:170px"><label>source id</label>
        <div class="mono small">${s.sourceId}</div>
        <div class="mono small muted">hash <span class="hash">${contentHash(s.text).slice(0,12)}…</span></div>
      </div>
      <div class="field" style="flex:1"><label>text</label>
        <textarea class="src-text" data-source="${s.sourceId}" rows="2">${escapeHtml(pending)}</textarea>
      </div>
      <button class="btn sm${dirty ? '' : ' ghost'}" data-recompute="${s.sourceId}">${dirty ? 'Recompute' : 'unchanged'}</button>
    </div>`;
  }).join('');
  $('#sources').innerHTML = rows;

  // wire textarea input -> pendingEdits
  document.querySelectorAll('.src-text').forEach(ta => {
    ta.addEventListener('input', () => {
      pendingEdits[ta.dataset.source] = ta.value;
      const btn = document.querySelector(`[data-recompute="${ta.dataset.source}"]`);
      const dirty = ta.value !== store.sources[ta.dataset.source].text;
      btn.textContent = dirty ? 'Recompute' : 'unchanged';
      btn.classList.toggle('ghost', !dirty);
    });
  });
  document.querySelectorAll('[data-recompute]').forEach(btn => {
    btn.addEventListener('click', () => {
      const sourceId = btn.dataset.recompute;
      const newText = pendingEdits[sourceId];
      if (newText === undefined || newText === store.sources[sourceId].text) return;
      store.tamperSource(sourceId, newText); // hash left un-pinned in every claim that named it
      delete pendingEdits[sourceId];
      renderSources();
      renderClaims();
      setVerdict(`<span class="chip bad">source edited</span> <span class="dim">${sourceId} text changed, claims pinned to it are now checked against the new hash</span>`);
      $('#out').innerHTML = `<span class="no">[tamper]</span> ${sourceId} text edited  <span class="dim">(claims' pinned hashes left unchanged, reaching past the add_source API)</span>`;
    });
  });

  // populate the "assert claim" source selector
  const sel = $('#newSourceRef');
  const prev = sel.value;
  sel.innerHTML = Object.keys(store.sources).map(id => `<option value="${id}">${id}</option>`).join('');
  if (Object.prototype.hasOwnProperty.call(store.sources, prev)) sel.value = prev;
}

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function renderClaims() {
  const rows = store.claims.map((c, i) => {
    const result = store.verify(c);
    const cls = result.ok ? ' class="current"' : ' class="stale"';
    const chip = result.ok ? '<span class="chip good">current</span>' : '<span class="chip bad">stale</span>';
    return `<tr${cls}>
      <td>${i}</td>
      <td>${c.statement}</td>
      <td>${c.sourceId}</td>
      <td><span class="hash">${c.pinnedHash.slice(0,12)}…</span></td>
      <td>${chip}</td>
    </tr>`;
  }).join('');
  $('#claims').innerHTML =
    `<table class="dtable"><thead><tr><th>#</th><th>statement</th><th>source</th><th>pinned hash</th><th>status</th></tr></thead><tbody>${rows || '<tr><td colspan="5" class="dim">no claims asserted yet</td></tr>'}</tbody></table>`;
}

function setVerdict(html) { $('#verdict').innerHTML = html; }

function init() {
  renderSources();
  renderClaims();
  setVerdict('<span class="chip blue">not yet verified</span> <span class="dim">assert a claim or edit a source, statuses update live</span>');

  $('#addSourceBtn').addEventListener('click', () => {
    const id = $('#newSourceId').value.trim();
    const text = $('#newSourceText').value;
    if (!id || !text) return;
    const hash = store.addSource(id, text);
    renderSources();
    renderClaims();
    setVerdict('<span class="chip blue">registered</span> <span class="dim">source ' + id + ' added</span>');
    $('#out').textContent = `Registered source ${id}  hash=${hash.slice(0,8)}…`;
  });

  $('#assertBtn').addEventListener('click', () => {
    const statement = $('#newStatement').value.trim() || 'A claim.';
    const sourceId = $('#newSourceRef').value;
    const result = store.assertClaim(statement, sourceId);
    renderClaims();
    if (result.ok) {
      setVerdict('<span class="chip good">grounded</span> <span class="dim">claim pinned to ' + sourceId + '</span>');
      $('#out').innerHTML = `<span class="ok">[claim]</span> ${statement}  <span class="dim">pinned=${result.claim.pinnedHash.slice(0,8)}… (${result.claim.trustClass})</span>`;
    } else {
      setVerdict('<span class="chip bad">refused</span> <span class="dim">no resolvable source</span>');
      $('#out').innerHTML = `<span class="no">[refused]</span> ${result.reason}`;
    }
  });

  $('#ghostBtn').addEventListener('click', () => {
    const statement = $('#ghostStatement').value.trim() || 'A claim.';
    const sourceId = $('#ghostSourceId').value.trim() || 'ghost_source';
    const result = store.assertClaim(statement, sourceId);
    renderClaims();
    if (result.ok) {
      // Only happens if the user typed an id that actually exists, not the point of this button.
      setVerdict('<span class="chip good">grounded</span> <span class="dim">that source id exists, try one that is not registered</span>');
      $('#out').innerHTML = `<span class="ok">[claim]</span> ${statement}  <span class="dim">pinned=${result.claim.pinnedHash.slice(0,8)}…</span>`;
    } else {
      setVerdict('<span class="chip bad">REFUSED</span> <span class="no">no evidence without a resolvable source</span>');
      $('#out').innerHTML = `<span class="no">✗ REFUSED</span>\n  <span class="dim">${result.reason}</span>\n  <span class="dim">the claim never entered the store, fail-closed, before it could be trusted.</span>`;
    }
  });
}

document.addEventListener('DOMContentLoaded', init);

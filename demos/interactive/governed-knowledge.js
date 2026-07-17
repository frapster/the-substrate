/*
  governed-knowledge.js, a faithful, in-browser reimplementation of
  demos/governed-knowledge/knowledge.py.

  Same atoms, same toy embeddings, same query vectors, same cosine math, so the
  scores match the Python to the decimal. This is a convenience, not the proof.
  The proof is the Python you can run and change yourself.
*/

/* ---- cosine similarity: real math, no cheating (matches knowledge.py's cosine()) ---- */
function cosine(a, b) {
  let dot = 0, magA = 0, magB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    magA += a[i] * a[i];
    magB += b[i] * b[i];
  }
  magA = Math.sqrt(magA);
  magB = Math.sqrt(magB);
  if (magA === 0 || magB === 0) return 0.0;
  return dot / (magA * magB);
}

/* ---- seed knowledge base (same atoms, embeddings, validity, scope as knowledge.py) ---- */
// dims: 0 refund  1 window  2 days30  3 days14  4 purchase  5 platinum  6 shipping
//       7 warranty  8 password  9 minchars_low  10 minchars_high  11 mfa
//      12 retention  13 days90  14 days365  15 legal_hold
const AUTHORIZED_SCOPES = new Set(["platform", "tenant_acme"]);
const DEFAULT_THRESHOLD = 0.5;

const ATOMS = [
  {
    atom_id: "atom_refund_v1", body: "Refund window is 30 days after purchase, no exceptions.",
    embedding: [0.9, 0.9, 0.9, 0.0, 0.8, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0],
    scope: "platform", provenance: "policy-doc://refunds/v1#section-3",
    validity_start: "2023-01-01", validity_end: "2025-12-31",
  },
  {
    atom_id: "atom_refund_v2",
    body: "Refund window is 14 days after purchase; platinum-tier customers retain a 30-day exception window.",
    embedding: [0.55, 0.5, 0.3, 0.7, 0.5, 0.6, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0],
    scope: "platform", provenance: "policy-doc://refunds/v2#section-1",
    validity_start: "2026-01-01", validity_end: null,
  },
  {
    atom_id: "atom_password_v1", body: "Password policy requires a minimum of 6 characters, no complexity rules.",
    embedding: [0, 0, 0, 0, 0, 0, 0, 0, 0.9, 0.9, 0.9, 0.0, 0, 0, 0, 0],
    scope: "platform", provenance: "policy-doc://password/v1#section-1",
    validity_start: "2021-01-01", validity_end: "2024-06-30",
  },
  {
    atom_id: "atom_password_v2",
    body: "Password policy requires a minimum of 12 characters plus multi-factor authentication for all accounts.",
    embedding: [0, 0, 0, 0, 0, 0, 0, 0, 0.5, 0.4, 0.7, 0.7, 0, 0, 0, 0],
    scope: "platform", provenance: "policy-doc://password/v2#section-1",
    validity_start: "2024-07-01", validity_end: null,
  },
  {
    atom_id: "atom_retention_v1", body: "Data retention period is 90 days after account closure.",
    embedding: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.9, 0.9, 0.0, 0.0],
    scope: "platform", provenance: "policy-doc://retention/v1#section-2",
    validity_start: "2022-03-01", validity_end: "2025-09-30",
  },
  {
    atom_id: "atom_retention_v2",
    body: "Data retention period is 365 days after account closure, extended indefinitely under legal hold.",
    embedding: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.5, 0.35, 0.7, 0.65],
    scope: "platform", provenance: "policy-doc://retention/v2#section-1",
    validity_start: "2025-10-01", validity_end: null,
  },
  {
    atom_id: "atom_shipping_v1",
    body: "Standard shipping takes 5-7 business days from purchase; expedited shipping is available for an extra fee.",
    embedding: [0.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.9, 0.0, 0, 0, 0, 0, 0, 0, 0, 0],
    scope: "platform", provenance: "policy-doc://shipping/v1#section-1",
    validity_start: "2020-01-01", validity_end: null,
  },
  {
    atom_id: "atom_tenant_acme_refund_v1", body: "Acme Corp's contract addendum grants a custom 45-day refund window.",
    embedding: [0.2, 0.15, 0.1, 0.2, 0.15, 0.1, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0],
    scope: "tenant_acme", provenance: "contract://acme/addendum-3",
    validity_start: "2025-05-01", validity_end: null,
  },
];

function isCurrent(atom) { return atom.validity_end === null; }
function status(atom) { return isCurrent(atom) ? "current" : `superseded ${atom.validity_end}`; }
function byId(id) { return ATOMS.find(a => a.atom_id === id); }

/* ---- the two retrievers (mirror knowledge.py's naive_retrieve / governed_retrieve) ---- */

function naiveRetrieve(queryEmbedding) {
  if (ATOMS.length === 0) return { atom: null, score: 0.0, degraded: true, reason: "knowledge base is empty" };
  let best = ATOMS[0], bestScore = cosine(queryEmbedding, best.embedding);
  for (const atom of ATOMS.slice(1)) {
    const s = cosine(queryEmbedding, atom.embedding);
    if (s > bestScore) { best = atom; bestScore = s; }
  }
  return { atom: best, score: bestScore, degraded: false, reason: "highest cosine match" };
}

function governedRetrieve(queryEmbedding, scope, threshold = DEFAULT_THRESHOLD) {
  if (!AUTHORIZED_SCOPES.has(scope)) {
    return { atom: null, score: 0.0, degraded: true,
      reason: `scope '${scope}' is not a registered/authorized retrieval channel` };
  }
  const candidates = ATOMS.filter(a => isCurrent(a) && a.scope === scope);
  if (candidates.length === 0) {
    return { atom: null, score: 0.0, degraded: true, reason: `no current atom is registered for scope '${scope}'` };
  }
  let best = candidates[0], bestScore = cosine(queryEmbedding, best.embedding);
  for (const atom of candidates.slice(1)) {
    const s = cosine(queryEmbedding, atom.embedding);
    if (s > bestScore) { best = atom; bestScore = s; }
  }
  if (bestScore < threshold) {
    return { atom: null, score: bestScore, degraded: true,
      reason: `best current, in-scope match scored ${bestScore.toFixed(3)}, below threshold ${threshold.toFixed(3)}, abstaining rather than guessing` };
  }
  return { atom: best, score: bestScore, degraded: false, reason: "current, in-scope, above threshold" };
}

/* ---- queries (same vectors as knowledge.py's SUPERSESSION_QUERIES + the abstain case) ---- */
const QUERIES = {
  refund: {
    label: "“What is the refund window after a purchase?”",
    vector: [0.9, 0.9, 0.0, 0.0, 0.8, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0],
    stale_id: "atom_refund_v1", current_id: "atom_refund_v2", scope: "platform",
  },
  password: {
    label: "“What is the minimum password length?”",
    vector: [0, 0, 0, 0, 0, 0, 0, 0, 0.9, 0.9, 0.0, 0.0, 0, 0, 0, 0],
    stale_id: "atom_password_v1", current_id: "atom_password_v2", scope: "platform",
  },
  retention: {
    label: "“How long is data retained after account closure?”",
    vector: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.85, 0.95, 0.0, 0.0],
    stale_id: "atom_retention_v1", current_id: "atom_retention_v2", scope: "platform",
  },
  warranty: {
    label: "“What is the warranty period?” (no current atom covers this topic)",
    vector: [0, 0, 0, 0, 0, 0, 0, 0.9, 0, 0, 0, 0, 0, 0, 0, 0],
    stale_id: null, current_id: null, scope: "platform",
  },
};

/* ---- UI ---- */
const $ = sel => document.querySelector(sel);
let lastResult = null; // { mode: 'naive'|'governed', queryKey, scope, result, otherScore }

function renderKB(pickedId) {
  const rows = ATOMS.map(atom => {
    const cur = isCurrent(atom);
    const cls = cur ? "current" : "stale";
    const picked = pickedId === atom.atom_id ? ' <span class="mono small acc">&larr; returned</span>' : "";
    return `<tr class="${cls}">
      <td>${atom.atom_id}${picked}</td>
      <td>${atom.body}</td>
      <td>${atom.scope}</td>
      <td>${atom.validity_start} &rarr; ${atom.validity_end ?? ","}</td>
      <td>${cur ? '<span class="chip good">current</span>' : `<span class="chip bad">superseded</span>`}</td>
    </tr>`;
  }).join("");
  $("#kb").innerHTML =
    `<table class="dtable"><thead><tr><th>atom</th><th>body</th><th>scope</th><th>validity</th><th>status</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function setVerdict(html) { $("#verdict").innerHTML = html; }

function currentQuery() { return QUERIES[$("#querySelect").value]; }

function runNaive() {
  const q = currentQuery();
  const result = naiveRetrieve(q.vector);
  lastResult = { mode: "naive", q, result };
  render();
}

function runGoverned() {
  const q = currentQuery();
  const scope = $("#scopeSelect").value;
  const result = governedRetrieve(q.vector, scope);
  lastResult = { mode: "governed", q, scope, result };
  render();
}

function render() {
  if (!lastResult) { renderKB(); return; }
  const { mode, q, result, scope } = lastResult;
  renderKB(result.atom ? result.atom.atom_id : null);

  if (mode === "naive") {
    const stale = q.stale_id ? byId(q.stale_id) : null;
    const current = q.current_id ? byId(q.current_id) : null;
    const staleScore = stale ? cosine(q.vector, stale.embedding) : null;
    const currentScore = current ? cosine(q.vector, current.embedding) : null;

    setVerdict(`<span class="chip bad">naive_retrieve</span> <span class="dim">returned ${result.atom.atom_id} (${status(result.atom)})</span>`);
    let cmp = "";
    if (stale && current) {
      cmp = `\n  <span class="dim">side by side, same query, both scored with the identical cosine():</span>\n` +
        `    ${stale.atom_id}   cosine=${staleScore.toFixed(3)}  ${stale === result.atom ? "<span class=\"no\">← naive picked this (stale)</span>" : ""}\n` +
        `    ${current.atom_id}   cosine=${currentScore.toFixed(3)}  <span class="dim">(current, higher-quality answer, but scores lower)</span>`;
    }
    $("#out").innerHTML =
      `<span class="no">[naive_retrieve]</span> returns <b>${result.atom.atom_id}</b> (cosine=${result.score.toFixed(3)}), <span class="no">${status(result.atom)}</span>\n` +
      `  "${result.atom.body}"${cmp}\n\n` +
      `  <span class="dim">This is not a rigged search: it really is the highest-cosine atom in the whole\n` +
      `  knowledge base. naive_retrieve has no notion of currency or scope.</span>`;
  } else {
    if (result.degraded) {
      setVerdict(`<span class="chip bad">degraded</span> <span class="dim">governed_retrieve abstained</span>`);
      $("#out").innerHTML =
        `<span class="no">[governed_retrieve]</span> <b>degraded=true</b>  <span class="dim">scope=${scope}</span>\n` +
        `  <span class="no">reason:</span> ${result.reason}\n\n` +
        `  <span class="dim">No atom is returned. A naive retriever would still hand back its single\n` +
        `  nearest-embedding atom here, confidently, with no real evidence behind it.</span>`;
    } else {
      const stale = q.stale_id ? byId(q.stale_id) : null;
      const staleScore = stale ? cosine(q.vector, stale.embedding) : null;
      let cmp = "";
      if (stale) {
        cmp = `\n\n  <span class="dim">side by side, same query:</span>\n` +
          `    ${stale.atom_id}   cosine=${staleScore.toFixed(3)}  <span class="dim">(scores higher, but superseded, never a candidate)</span>\n` +
          `    ${result.atom.atom_id}   cosine=${result.score.toFixed(3)}  <span class="ok">← governed picked this (current)</span>`;
      }
      setVerdict(`<span class="chip good">governed_retrieve</span> <span class="dim">returned ${result.atom.atom_id} (current)</span>`);
      $("#out").innerHTML =
        `<span class="ok">[governed_retrieve]</span> returns <b>${result.atom.atom_id}</b> (cosine=${result.score.toFixed(3)}), <span class="ok">current</span>  <span class="dim">scope=${scope}</span>\n` +
        `  "${result.atom.body}"${cmp}\n\n` +
        `  <span class="dim">governed_retrieve filtered to current + authorized atoms BEFORE ranking by\n` +
        `  similarity, so a superseded fact could not outrank a current one, no matter its score.</span>`;
    }
  }
}

function init() {
  renderKB();
  setVerdict('<span class="chip blue">not yet queried</span> <span class="dim">pick a query, then run naive or governed retrieval</span>');
  $("#out").textContent = "";

  $("#naiveBtn").addEventListener("click", runNaive);
  $("#governedBtn").addEventListener("click", runGoverned);
  $("#querySelect").addEventListener("change", () => { lastResult = null; renderKB(); setVerdict('<span class="chip blue">not yet queried</span> <span class="dim">pick a query, then run naive or governed retrieval</span>'); $("#out").textContent = ""; });
  $("#scopeSelect").addEventListener("change", () => { lastResult = null; renderKB(); setVerdict('<span class="chip blue">not yet queried</span> <span class="dim">pick a query, then run naive or governed retrieval</span>'); $("#out").textContent = ""; });
}

document.addEventListener("DOMContentLoaded", init);

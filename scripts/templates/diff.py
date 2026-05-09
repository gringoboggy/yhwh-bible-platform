"""HTML for /diff console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import DIFF_HTML` callers.

ψ.16 status-dashboard polish (2026-05-09): cross-link nav
substituted from `_design.HEADER_NAV_LINKS("/diff")` and
`BUYER_ARC_POLISH_CSS` inlined from `_design`.
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
)

DIFF_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>E-Bible · Edition Diff</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  .col-a { background: #eff6ff; border-left: 3px solid #2563eb; }
  .col-b { background: #fdf4ff; border-left: 3px solid #a21caf; }
  .col-shared { background: #f8fafc; border-left: 3px solid #94a3b8; }
  .a-tint { color: #1d4ed8; }
  .b-tint { color: #86198f; }
  .pill {
    display: inline-flex; align-items: center; gap: 0.35em;
    padding: 0.15em 0.5em; border-radius: 9999px;
    font-size: 0.7rem; font-weight: 600;
    background: #f1f5f9; border: 1px solid #cbd5e1;
  }
  .bar-track { background: #e2e8f0; height: 8px; border-radius: 9999px; overflow: hidden; }
  .bar-a { background: #2563eb; height: 100%; }
  .bar-b { background: #a21caf; height: 100%; }
</style>
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Edition Diff</h1>
    <p class="text-xs text-slate-500">side-by-side comparison · read-only sales / demo tool</p>
  </div>
  <div class="flex items-center gap-4 text-xs flex-wrap">
    <!-- HEADER_NAV_LINKS -->
    <span id="corpus-progress" class="ml-auto text-xs text-slate-500" title="corpus depth toward the 35,000-note Ethiopian Tewahedo target">·· loading ··</span>
  </div>
</header>
<script>
// Phase ψ.3 — corpus progress widget. Cheap fetch + DOM update;
// silently no-ops on failure so a stale browser tab never breaks
// because the API endpoint changed shape.
(function () {
  fetch('/api/corpus-progress').then(function (r) { return r.json(); })
    .then(function (d) {
      var el = document.getElementById('corpus-progress');
      if (!el) return;
      var cur = (d.current || 0).toLocaleString();
      var tgt = (d.target || 0).toLocaleString();
      var pct = (typeof d.percent === 'number') ? d.percent.toFixed(1) : '0.0';
      el.textContent = cur + ' / ' + tgt + ' · ' + pct + '%';
    })
    .catch(function () {});
})();
</script>


<main class="p-6 max-w-6xl mx-auto space-y-5">

  <!-- Picker -->
  <section class="bg-white border border-slate-200 rounded-lg p-4 flex items-center gap-3 flex-wrap">
    <label class="text-xs font-semibold text-slate-500 uppercase tracking-wide">Edition A</label>
    <select id="pick-a" class="border border-slate-300 rounded px-2 py-1.5 text-sm bg-white"></select>
    <button id="swap" title="Swap A and B"
            class="px-3 py-1.5 rounded border border-slate-300 bg-slate-50 hover:bg-slate-100
                   text-slate-700 text-sm">⇄ swap</button>
    <label class="text-xs font-semibold text-slate-500 uppercase tracking-wide">Edition B</label>
    <select id="pick-b" class="border border-slate-300 rounded px-2 py-1.5 text-sm bg-white"></select>
    <span class="ml-auto text-xs text-slate-400" id="loading-flag">loading…</span>
  </section>

  <!-- Headline -->
  <section id="headline-card"
           class="bg-gradient-to-r from-blue-50 to-fuchsia-50 border border-slate-200 rounded-lg p-5">
    <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">At a glance</p>
    <p id="headline" class="text-base text-slate-800 leading-relaxed">…</p>
  </section>

  <!-- Edition cards (A vs B) -->
  <section class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div id="card-a" class="col-a rounded-lg p-4"></div>
    <div id="card-b" class="col-b rounded-lg p-4"></div>
  </section>

  <!-- Books -->
  <section class="bg-white border border-slate-200 rounded-lg overflow-hidden">
    <header class="px-5 py-3 border-b border-slate-200 bg-slate-50">
      <h2 class="font-semibold text-slate-700">Books</h2>
      <p class="text-xs text-slate-500">canon-level differences — which books appear in each edition's bound volume</p>
    </header>
    <div class="grid grid-cols-1 md:grid-cols-3 divide-x divide-slate-200">
      <div class="p-4">
        <p class="text-xs font-semibold uppercase tracking-wide a-tint mb-2">
          Only in <span id="books-a-name">A</span>
          <span id="books-a-count" class="pill ml-1">0</span>
        </p>
        <ul id="books-only-a" class="text-sm space-y-1"></ul>
      </div>
      <div class="p-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">
          In Both <span id="books-both-count" class="pill ml-1">0</span>
        </p>
        <p class="text-xs text-slate-500" id="books-both-detail"></p>
      </div>
      <div class="p-4">
        <p class="text-xs font-semibold uppercase tracking-wide b-tint mb-2">
          Only in <span id="books-b-name">B</span>
          <span id="books-b-count" class="pill ml-1">0</span>
        </p>
        <ul id="books-only-b" class="text-sm space-y-1"></ul>
      </div>
    </div>
  </section>

  <!-- Note kinds -->
  <section class="bg-white border border-slate-200 rounded-lg overflow-hidden">
    <header class="px-5 py-3 border-b border-slate-200 bg-slate-50">
      <h2 class="font-semibold text-slate-700">Note Kinds</h2>
      <p class="text-xs text-slate-500">which families of annotations appear in each edition, with shipping note counts</p>
    </header>
    <div class="grid grid-cols-1 md:grid-cols-2 divide-x divide-slate-200">
      <div class="p-4">
        <p class="text-xs font-semibold uppercase tracking-wide a-tint mb-3">
          Exclusive to <span id="kinds-a-name">A</span>
          <span id="kinds-only-a-count" class="pill ml-1">0</span>
        </p>
        <ul id="kinds-only-a" class="text-sm space-y-1.5"></ul>
      </div>
      <div class="p-4">
        <p class="text-xs font-semibold uppercase tracking-wide b-tint mb-3">
          Exclusive to <span id="kinds-b-name">B</span>
          <span id="kinds-only-b-count" class="pill ml-1">0</span>
        </p>
        <ul id="kinds-only-b" class="text-sm space-y-1.5"></ul>
      </div>
    </div>
    <details class="border-t border-slate-200 bg-slate-50">
      <summary class="px-5 py-3 cursor-pointer text-xs font-semibold uppercase tracking-wide text-slate-500
                      hover:bg-slate-100">
        Shared kinds <span id="shared-kinds-count" class="pill ml-1">0</span>
        <span class="ml-2 text-slate-400 normal-case font-normal">(in both editions, with note-count delta)</span>
      </summary>
      <ul id="kinds-shared" class="px-5 py-3 text-sm space-y-1 bg-white"></ul>
    </details>
  </section>

  <!-- Categories -->
  <section class="bg-white border border-slate-200 rounded-lg overflow-hidden">
    <header class="px-5 py-3 border-b border-slate-200 bg-slate-50">
      <h2 class="font-semibold text-slate-700">By Category</h2>
      <p class="text-xs text-slate-500">notes per top-level category, A vs B</p>
    </header>
    <div id="cat-bars" class="p-4 space-y-3"></div>
  </section>

</main>

<script>
const $ = sel => document.querySelector(sel);
const esc = s => (s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

const STATE = {
  editions: [],
  a: 'catholic-study',
  b: 'evangelical-reformed',
  data: null,
};

async function fetchDiff() {
  $('#loading-flag').textContent = 'loading…';
  $('#loading-flag').classList.remove('text-rose-500');
  const url = `/api/diff?a=${encodeURIComponent(STATE.a)}&b=${encodeURIComponent(STATE.b)}`;
  const r = await fetch(url);
  const data = await r.json();
  if (data.error) {
    $('#loading-flag').textContent = 'error: ' + data.error;
    $('#loading-flag').classList.add('text-rose-500');
    return;
  }
  STATE.data = data;
  if (!STATE.editions.length) {
    STATE.editions = data.editions_index;
    populatePickers();
  }
  render();
  $('#loading-flag').textContent = '';
}

function populatePickers() {
  for (const sel of ['#pick-a', '#pick-b']) {
    const el = $(sel);
    el.innerHTML = STATE.editions.map(e =>
      `<option value="${esc(e.id)}">${esc(e.short_title || e.id)}</option>`
    ).join('');
  }
  $('#pick-a').value = STATE.a;
  $('#pick-b').value = STATE.b;
  $('#pick-a').addEventListener('change', () => { STATE.a = $('#pick-a').value; fetchDiff(); });
  $('#pick-b').addEventListener('change', () => { STATE.b = $('#pick-b').value; fetchDiff(); });
  $('#swap').addEventListener('click', () => {
    [STATE.a, STATE.b] = [STATE.b, STATE.a];
    $('#pick-a').value = STATE.a;
    $('#pick-b').value = STATE.b;
    fetchDiff();
  });
}

function render() {
  const d = STATE.data;
  $('#headline').textContent = d.headline;

  $('#card-a').innerHTML = editionCard(d.a, 'a-tint');
  $('#card-b').innerHTML = editionCard(d.b, 'b-tint');

  // Books section labels
  $('#books-a-name').textContent = d.a.short_title;
  $('#books-b-name').textContent = d.b.short_title;
  $('#books-a-count').textContent = d.books.only_a.length;
  $('#books-b-count').textContent = d.books.only_b.length;
  $('#books-both-count').textContent = d.books.both_count;
  $('#books-both-detail').textContent =
    d.books.both_count
      ? `Both editions share ${d.books.both_count} books from their respective canons.`
      : 'No books in common.';

  $('#books-only-a').innerHTML = d.books.only_a.length
    ? d.books.only_a.map(bookRow).join('')
    : `<li class="text-slate-400 italic">none</li>`;
  $('#books-only-b').innerHTML = d.books.only_b.length
    ? d.books.only_b.map(bookRow).join('')
    : `<li class="text-slate-400 italic">none</li>`;

  // Kinds section
  $('#kinds-a-name').textContent = d.a.short_title;
  $('#kinds-b-name').textContent = d.b.short_title;
  $('#kinds-only-a-count').textContent = d.kinds.only_a.length;
  $('#kinds-only-b-count').textContent = d.kinds.only_b.length;
  $('#shared-kinds-count').textContent = d.kinds.shared.length;

  $('#kinds-only-a').innerHTML = d.kinds.only_a.length
    ? d.kinds.only_a.map(r => kindRow(r, 'a')).join('')
    : `<li class="text-slate-400 italic">none</li>`;
  $('#kinds-only-b').innerHTML = d.kinds.only_b.length
    ? d.kinds.only_b.map(r => kindRow(r, 'b')).join('')
    : `<li class="text-slate-400 italic">none</li>`;
  $('#kinds-shared').innerHTML = d.kinds.shared.length
    ? d.kinds.shared.map(sharedKindRow).join('')
    : `<li class="text-slate-400 italic">none</li>`;

  // Category bars
  $('#cat-bars').innerHTML = catBars(d.categories);
}

function editionCard(e, tintClass) {
  const isbn = e.isbn && e.isbn !== '—' ? e.isbn : '<span class="text-slate-400">no ISBN set</span>';
  return `
    <p class="text-xs font-semibold uppercase tracking-wide ${tintClass} mb-1">${esc(e.short_title)}</p>
    <h3 class="text-lg font-bold text-slate-900 leading-tight mb-2">${esc(e.title)}</h3>
    <p class="text-xs text-slate-600 mb-3">${esc(e.canon_label)}</p>
    <p class="text-xs text-slate-500 italic mb-3 line-clamp-2">${esc(e.audience || '')}</p>
    <div class="grid grid-cols-3 gap-2 text-center">
      <div class="bg-white rounded p-2 border border-slate-200">
        <div class="text-xl font-bold ${tintClass}">${e.totals.books}</div>
        <div class="text-xs text-slate-500 uppercase tracking-wide">books</div>
      </div>
      <div class="bg-white rounded p-2 border border-slate-200">
        <div class="text-xl font-bold ${tintClass}">${e.totals.kinds}</div>
        <div class="text-xs text-slate-500 uppercase tracking-wide">kinds</div>
      </div>
      <div class="bg-white rounded p-2 border border-slate-200">
        <div class="text-xl font-bold ${tintClass}">${e.totals.notes.toLocaleString()}</div>
        <div class="text-xs text-slate-500 uppercase tracking-wide">notes</div>
      </div>
    </div>
    <p class="text-xs text-slate-500 mt-3 mono">${isbn}</p>
  `;
}

function bookRow(b) {
  return `<li class="flex items-baseline gap-2">
    <span class="mono text-xs text-slate-400 w-10">${esc(b.code)}</span>
    <span class="text-slate-700">${esc(b.title)}</span>
  </li>`;
}

function kindRow(r, side) {
  const count = side === 'a' ? r.a_count : r.b_count;
  const tint = side === 'a' ? 'a-tint' : 'b-tint';
  return `<li class="flex items-baseline gap-2">
    <span class="text-base w-5 text-center">${esc(r.symbol)}</span>
    <span class="flex-1">
      <span class="font-semibold">${esc(r.label)}</span>
      <span class="text-xs text-slate-400 ml-1">(${esc(r.category_label)})</span>
      <span class="block text-xs text-slate-400 mono">${esc(r.code)}</span>
    </span>
    <span class="${tint} font-semibold mono text-sm">${count}</span>
    <span class="text-xs text-slate-400">notes</span>
  </li>`;
}

function sharedKindRow(r) {
  const sign = r.delta > 0 ? '+' : '';
  const deltaClass = r.delta > 0 ? 'a-tint' : (r.delta < 0 ? 'b-tint' : 'text-slate-400');
  return `<li class="flex items-baseline gap-2 py-0.5">
    <span class="text-sm w-5 text-center">${esc(r.symbol)}</span>
    <span class="flex-1 truncate">
      <span class="text-slate-700">${esc(r.label)}</span>
      <span class="text-xs text-slate-400 mono ml-1">${esc(r.code)}</span>
    </span>
    <span class="a-tint mono text-xs">${r.a_count}</span>
    <span class="text-slate-400 text-xs">vs</span>
    <span class="b-tint mono text-xs">${r.b_count}</span>
    <span class="${deltaClass} mono text-xs w-12 text-right">Δ ${sign}${r.delta}</span>
  </li>`;
}

function catBars(cats) {
  if (!cats.length) return '<p class="text-slate-400 italic">no category data</p>';
  const max = Math.max(1, ...cats.flatMap(c => [c.a_count, c.b_count]));
  return cats.map(c => {
    const aPct = (c.a_count / max) * 100;
    const bPct = (c.b_count / max) * 100;
    return `
      <div class="grid grid-cols-12 items-center gap-3 text-sm">
        <div class="col-span-3 truncate">
          <span class="mr-1">${esc(c.symbol)}</span>
          <span class="text-slate-700">${esc(c.label)}</span>
        </div>
        <div class="col-span-9 grid grid-cols-2 gap-3">
          <div class="flex items-center gap-2">
            <div class="bar-track flex-1"><div class="bar-a" style="width:${aPct}%"></div></div>
            <span class="a-tint mono text-xs w-10 text-right">${c.a_count}</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="bar-track flex-1"><div class="bar-b" style="width:${bPct}%"></div></div>
            <span class="b-tint mono text-xs w-10 text-right">${c.b_count}</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

fetchDiff().catch(e => {
  $('#loading-flag').textContent = 'failed: ' + e.message;
  $('#loading-flag').classList.add('text-rose-500');
});
</script>

<!-- ω.0.6 — UI defense prelude — START -->
<!-- Re-injecting / refreshing this block uses
     scripts/bulk_inject.py replace --open-marker "ω.0.6 — UI defense prelude — START"
     ...                          --close-marker "ω.0.6 — UI defense prelude — END"
     The markers are stable contracts; do not change without a coordinated migration. -->
<script>
(function () {
  'use strict';

  // -------------------------------------------------------------------
  // Tier 4 — Global error backstop. Catches anything that escapes
  // the other tiers (null-pointer accesses, unhandled rejections,
  // syntax errors in inline scripts) and shows a soft red banner
  // instead of leaving the page frozen.
  // -------------------------------------------------------------------

  function ensureErrorBanner() {
    var banner = document.getElementById('ebible-error-banner');
    if (banner) return banner;
    banner = document.createElement('div');
    banner.id = 'ebible-error-banner';
    banner.setAttribute('role', 'alert');
    banner.setAttribute('aria-live', 'polite');
    banner.style.cssText =
      'position:fixed;top:0;left:0;right:0;z-index:9999;' +
      'background:#dc2626;color:#fff;padding:8px 16px;font-size:13px;' +
      'font-family:system-ui,sans-serif;display:none;' +
      'box-shadow:0 2px 4px rgba(0,0,0,0.1)';
    banner.innerHTML =
      '<div style="max-width:72rem;margin:0 auto;display:flex;' +
      'align-items:center;justify-content:space-between;gap:12px">' +
      '<span class="ebible-error-text" style="flex:1;min-width:0;' +
      'overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span>' +
      '<button type="button" class="ebible-error-dismiss" ' +
      'style="background:none;border:1px solid rgba(255,255,255,0.4);' +
      'color:#fff;padding:2px 10px;border-radius:4px;cursor:pointer;' +
      'font-size:12px">Dismiss</button></div>';
    if (document.body) {
      document.body.appendChild(banner);
    } else {
      document.addEventListener('DOMContentLoaded', function () {
        document.body.appendChild(banner);
      });
    }
    banner.querySelector('.ebible-error-dismiss')
      .addEventListener('click', function () { banner.style.display = 'none'; });
    return banner;
  }

  function showErrorBanner(message) {
    try {
      var banner = ensureErrorBanner();
      var text = banner.querySelector('.ebible-error-text');
      if (text) text.textContent = message;
      banner.style.display = 'block';
    } catch (e) {
      // If even the banner fails, log to console as last resort
      try { console.error('[ebible] error banner failed:', e, message); }
      catch (_) {}
    }
  }

  // Install global error handlers
  window.addEventListener('error', function (ev) {
    var msg = (ev && ev.message) ? ev.message : 'Script error';
    // Filter out "Script error." with no info — usually cross-origin
    // loaded resources, nothing actionable for us
    if (msg === 'Script error.') return;
    showErrorBanner('Something went wrong: ' + msg);
    try { console.error('[ebible global error]', ev.error || msg); }
    catch (_) {}
  });
  window.addEventListener('unhandledrejection', function (ev) {
    var reason = ev && ev.reason;
    var msg = (reason && reason.message) ? reason.message : String(reason);
    showErrorBanner('Background task failed: ' + msg);
    try { console.error('[ebible unhandled rejection]', reason); }
    catch (_) {}
  });

  // -------------------------------------------------------------------
  // Tier 2 — safeFetch wrapper. Standard helper for every API call.
  // Throws on non-OK status, parses JSON safely, surfaces failures
  // via the banner. Re-throws so callers can do feature-specific
  // handling on top.
  // -------------------------------------------------------------------

  async function safeFetch(url, opts) {
    opts = opts || {};
    let response;
    try {
      response = await fetch(url, opts);
    } catch (netErr) {
      // Network drop, DNS fail, fetch aborted, etc.
      const msg = (netErr && netErr.message) ? netErr.message : 'network error';
      showErrorBanner('Network error: ' + msg + ' (' + url + ')');
      throw netErr;
    }
    if (!response.ok) {
      let errMsg = response.status + ' ' + response.statusText;
      try {
        const text = await response.text();
        if (text) {
          try {
            const parsed = JSON.parse(text);
            if (parsed && parsed.error) errMsg = parsed.error;
          } catch (_) {
            // Not JSON; use text snippet
            errMsg = text.slice(0, 200);
          }
        }
      } catch (_) {}
      showErrorBanner('API ' + response.status + ': ' + errMsg);
      const err = new Error(errMsg);
      err.status = response.status;
      throw err;
    }
    // Parse response. If empty body, return null (DELETE often is).
    const text = await response.text();
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch (parseErr) {
      showErrorBanner('Server returned invalid JSON from ' + url);
      throw parseErr;
    }
  }

  // -------------------------------------------------------------------
  // Tier 3 — DOM null-safe helpers. querySelector / querySelectorAll
  // wrappers that don't throw on missing elements. Opt-in: existing
  // code keeps working; new code can adopt these.
  // -------------------------------------------------------------------

  function safe$(selector, parent) {
    try {
      return (parent || document).querySelector(selector);
    } catch (e) {
      // Invalid selector syntax → log and return null instead of crash
      try { console.warn('[safe$] invalid selector:', selector, e); }
      catch (_) {}
      return null;
    }
  }

  function safe$$(selector, parent) {
    try {
      return Array.from((parent || document).querySelectorAll(selector));
    } catch (e) {
      try { console.warn('[safe$$] invalid selector:', selector, e); }
      catch (_) {}
      return [];
    }
  }

  // -------------------------------------------------------------------
  // ω.0.7 — Shared escape helpers. Eleven separate definitions of
  // essentially the same HTML-escaping logic existed across the
  // consoles before this consolidation. New code should use
  // window.ebible.escapeHtml (or the bare alias). Existing call
  // sites can migrate incrementally.
  // -------------------------------------------------------------------

  var ESCAPE_HTML_MAP = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  };

  function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, function (c) {
      return ESCAPE_HTML_MAP[c] || c;
    });
  }

  // -------------------------------------------------------------------
  // Public surface — attach to window.ebible namespace
  // -------------------------------------------------------------------

  window.ebible = window.ebible || {};
  window.ebible.showErrorBanner = showErrorBanner;
  window.ebible.safeFetch = safeFetch;
  window.ebible.safe$ = safe$;
  window.ebible.safe$$ = safe$$;
  window.ebible.escapeHtml = escapeHtml;
  // Convenience aliases for less typing in inline scripts
  window.safeFetch = safeFetch;
  window.safe$ = safe$;
  window.safe$$ = safe$$;
  window.escapeHtml = escapeHtml;
})();
</script>
<!-- ω.0.6 — UI defense prelude — END -->

</body>
</html>
"""


# ψ.16: substitute the canonical nav link list from _design.CONSOLES.
DIFF_HTML = DIFF_HTML.replace(
    "    <!-- HEADER_NAV_LINKS -->",
    HEADER_NAV_LINKS("/diff"),
)
DIFF_HTML = DIFF_HTML.replace(
    "<!-- BUYER_ARC_POLISH_CSS -->",
    BUYER_ARC_POLISH_CSS,
)

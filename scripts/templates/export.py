"""HTML for /export console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import EXPORT_HTML` callers.

ψ.14 buyer-arc polish (2026-05-08): the cross-link nav is now
substituted from `_design.HEADER_NAV_LINKS("/export")` at module
load so adding a new console — or renaming a label — propagates
without hand-edits here. The wrapping `<div>` + corpus-progress
sibling stay in the template (console-specific).
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
    apply_design_system,
)

EXPORT_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>E-Bible · Export</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
  .symbol { font-size: 1.1em; line-height: 1; display: inline-block; width: 1.4em; text-align: center; }
  @keyframes pulse-soft { 0%, 100% { opacity: 1; } 50% { opacity: 0.45; } }
  .pulsing { animation: pulse-soft 1.4s ease-in-out infinite; }
</style>
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Export Your Bible</h1>
    <p class="text-xs text-slate-500">pre-flight summary, then one-click EPUB build</p>
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


<main class="p-6 max-w-5xl mx-auto">

  <section class="bg-white rounded-lg shadow-sm border border-slate-200 p-4 mb-6">
    <label class="block text-xs uppercase tracking-wide text-slate-500 mb-1">Pick an edition to export</label>
    <select id="edition-select" class="w-full md:w-96 border border-slate-300 rounded px-2 py-2 text-sm">
      <option value="">— loading —</option>
    </select>
  </section>

  <div id="preview" class="hidden">

    <!-- Header card: title + canon + audience -->
    <section class="bg-white rounded-lg shadow-sm border border-slate-200 p-5 mb-4">
      <h2 id="ed-title" class="text-2xl font-bold tracking-tight"></h2>
      <div id="ed-urn" class="text-xs text-slate-500 font-mono mt-0.5"></div>
      <p id="ed-audience" class="text-sm text-slate-600 mt-2"></p>
      <p id="ed-notes" class="text-xs text-slate-500 italic mt-1"></p>
    </section>

    <!-- Summary numbers -->
    <section class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
      <div class="bg-white rounded-lg border border-slate-200 p-3">
        <div class="text-xs uppercase tracking-wide text-slate-500">Books</div>
        <div id="sum-books" class="text-2xl font-bold"></div>
      </div>
      <div class="bg-white rounded-lg border border-slate-200 p-3">
        <div class="text-xs uppercase tracking-wide text-slate-500">Notes shipping</div>
        <div id="sum-notes" class="text-2xl font-bold text-emerald-700"></div>
      </div>
      <div class="bg-white rounded-lg border border-slate-200 p-3">
        <div class="text-xs uppercase tracking-wide text-slate-500">Kinds enabled</div>
        <div id="sum-kinds" class="text-2xl font-bold"></div>
      </div>
      <div class="bg-white rounded-lg border border-slate-200 p-3">
        <div class="text-xs uppercase tracking-wide text-slate-500">Canon</div>
        <div id="sum-canon" class="text-2xl font-bold capitalize"></div>
      </div>
    </section>

    <!-- Two-column lower area -->
    <div class="grid md:grid-cols-2 gap-4 mb-4">

      <section class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <h3 class="text-xs uppercase tracking-wide text-slate-500 mb-2">Category breakdown</h3>
        <div id="cat-breakdown" class="text-sm space-y-1.5"></div>
      </section>

      <section class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <h3 class="text-xs uppercase tracking-wide text-slate-500 mb-2">Filtered out by edition config</h3>
        <p class="text-xs text-slate-500 mb-2">these note kinds exist in the canon but won't ship — toggle them on at <a href="/matrix" class="text-blue-600 hover:underline">/matrix</a> if you want them in.</p>
        <div id="filtered" class="text-sm space-y-1"></div>
      </section>

    </div>

    <!-- Export action card -->
    <section class="bg-white rounded-lg shadow-sm border-2 border-emerald-500 p-5">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h3 class="font-bold text-lg">Ready to export</h3>
          <p class="text-xs text-slate-500">runs the same pipeline that produces the retail EPUBs · usually 10-30 seconds</p>
          <div id="last-build" class="text-xs text-slate-500 mt-1"></div>
        </div>
        <button id="export-btn" class="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-5 py-2.5 rounded text-base">
          Export EPUB
        </button>
      </div>
      <div id="export-status" class="mt-3 text-sm"></div>
    </section>

  </div>

  <div id="loading" class="text-center text-slate-400 py-20">loading editions …</div>

  <!-- Phase ω.2 — Build-all-editions one-click. Buyer-demo gold:
       click once, get every edition packaged. Per-edition errors
       don't abort the batch; partial-success is a real outcome
       and the UI surfaces which editions made it. -->
  <section class="bg-white rounded-lg border border-slate-200 p-4 mt-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="font-semibold text-slate-800">Build all editions</h2>
        <p class="text-xs text-slate-500">runs every edition through the build pipeline · packages outputs into a single zip · partial failures don't abort the batch</p>
      </div>
      <button id="build-all-btn" class="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-4 py-2 rounded">
        Build all 5 editions
      </button>
    </div>
    <div id="build-all-status" class="mt-3 text-sm"></div>
    <div id="build-all-results" class="mt-3 hidden"></div>
  </section>

  <!-- Phase ψ.5 — Sample-chapter HTML export form. Lets publishers
       generate a self-contained preview document for sharing on
       Substack / pitch decks, without committing to a full EPUB build. -->
  <section class="bg-white rounded-lg border border-slate-200 p-4 mt-6">
    <h2 class="font-semibold text-slate-800 mb-1">Sample preview export</h2>
    <p class="text-xs text-slate-500 mb-3">
      Generate a self-contained HTML preview for a single book + chapter range.
      Filtered by the selected edition's enabled note kinds. Opens in a new tab.
    </p>
    <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
      <div class="md:col-span-3">
        <label class="text-xs font-medium text-slate-600 block mb-1">Edition</label>
        <select id="sample-edition" class="w-full text-sm border border-slate-300 rounded px-2 py-1.5"></select>
      </div>
      <div class="md:col-span-3">
        <label class="text-xs font-medium text-slate-600 block mb-1">Book</label>
        <input id="sample-book" type="text" placeholder="gen" maxlength="6"
               class="w-full text-sm border border-slate-300 rounded px-2 py-1.5">
      </div>
      <div class="md:col-span-2">
        <label class="text-xs font-medium text-slate-600 block mb-1">From ch.</label>
        <input id="sample-from" type="number" min="1" max="150" maxlength="3" value="1"
               class="w-full text-sm border border-slate-300 rounded px-2 py-1.5">
      </div>
      <div class="md:col-span-2">
        <label class="text-xs font-medium text-slate-600 block mb-1">To ch.</label>
        <input id="sample-to" type="number" min="1" max="150" maxlength="3" value="1"
               class="w-full text-sm border border-slate-300 rounded px-2 py-1.5">
      </div>
      <div class="md:col-span-2">
        <button id="sample-go" type="button"
                class="w-full text-sm px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-700 text-white font-medium">
          Open sample
        </button>
      </div>
    </div>
    <p id="sample-status" class="text-xs mt-2 text-slate-500"></p>
  </section>

</main>

<script>
let CURRENT_ID = null;

async function init() {
  // Pull edition list via /api/matrix (which already returns it)
  const res = await fetch('/api/matrix');
  const data = await res.json();
  const sel = document.getElementById('edition-select');
  sel.innerHTML = '';
  for (const ed of data.editions) {
    const o = document.createElement('option');
    o.value = ed.id;
    o.textContent = ed.title;
    sel.appendChild(o);
  }
  sel.addEventListener('change', () => loadPreview(sel.value));
  if (data.editions.length) {
    sel.value = data.editions[0].id;
    await loadPreview(sel.value);
  }
  // Phase ψ.5 — populate the sample-export edition select with the
  // same list (separate <select> so the user can preview a different
  // edition than the one being built without losing context)
  const sampleSel = document.getElementById('sample-edition');
  if (sampleSel) {
    sampleSel.innerHTML = '';
    for (const ed of data.editions) {
      const o = document.createElement('option');
      o.value = ed.id;
      o.textContent = ed.title;
      sampleSel.appendChild(o);
    }
    if (data.editions.length) sampleSel.value = data.editions[0].id;
  }
  // Wire the Open sample button
  const sampleBtn = document.getElementById('sample-go');
  if (sampleBtn) sampleBtn.addEventListener('click', openSample);
  // Phase ω.2 — Build all editions
  const buildAllBtn = document.getElementById('build-all-btn');
  if (buildAllBtn) buildAllBtn.addEventListener('click', buildAllEditions);
  document.getElementById('loading').classList.add('hidden');
}

// Phase ω.2 — kick off "Build all editions" pipeline. Returns
// JSON; per-edition statuses populate the results panel and
// the combined zip download URL is offered if any builds
// succeeded. Partial success is a real outcome — never abort
// the batch on a per-edition failure.
async function buildAllEditions() {
  const btn = document.getElementById('build-all-btn');
  const status = document.getElementById('build-all-status');
  const results = document.getElementById('build-all-results');
  const escape = (window.ebible && window.ebible.escapeHtml)
    ? window.ebible.escapeHtml
    : (s) => String(s == null ? '' : s).replace(/[&<>"']/g,
        c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  btn.disabled = true;
  btn.classList.add('opacity-50', 'cursor-not-allowed');
  btn.textContent = 'Building…';
  status.innerHTML = '<span class="text-slate-500">building all editions; this can take 1–3 minutes total…</span>';
  results.classList.add('hidden');

  let data;
  try {
    const r = await fetch('/api/build-all', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({version: 'v28a'}),
    });
    data = await r.json();
    if (!r.ok && !data.per_edition) {
      status.innerHTML = `<span class="text-red-600">✗ ${escape(data.error || r.statusText)}</span>`;
      btn.disabled = false;
      btn.classList.remove('opacity-50', 'cursor-not-allowed');
      btn.textContent = 'Build all 5 editions';
      return;
    }
  } catch (e) {
    status.innerHTML = `<span class="text-red-600">✗ network error: ${escape(e.message)}</span>`;
    btn.disabled = false;
    btn.classList.remove('opacity-50', 'cursor-not-allowed');
    btn.textContent = 'Build all 5 editions';
    return;
  }

  const succ = data.success_count || 0;
  const fail = data.fail_count || 0;
  const tot = data.total_count || 0;
  let summary;
  if (fail === 0 && succ > 0) {
    summary = `<span class="text-emerald-700">✓ all ${succ}/${tot} editions built</span>`;
  } else if (succ > 0) {
    summary = `<span class="text-amber-700">⚠ partial: ${succ}/${tot} built · ${fail} failed</span>`;
  } else {
    summary = `<span class="text-red-600">✗ all ${tot} editions failed</span>`;
  }
  if (data.zip_filename) {
    summary += ` · <a href="${escape(data.download_url)}" class="text-blue-600 hover:underline font-semibold">download combined zip (${data.zip_size_mb} MB)</a>`;
  }
  status.innerHTML = summary;

  if (data.per_edition && data.per_edition.length) {
    const rowsHtml = data.per_edition.map(p => {
      if (p.ok) {
        return `<tr class="border-b border-slate-100">
          <td class="py-1.5 pr-3 font-mono text-xs">${escape(p.edition_id)}</td>
          <td class="py-1.5 pr-3 text-emerald-700">✓ built</td>
          <td class="py-1.5 pr-3 text-xs text-slate-500">${p.size_mb || 0} MB</td>
          <td class="py-1.5 text-xs text-slate-500">${escape(p.filename || '')}</td>
        </tr>`;
      }
      return `<tr class="border-b border-slate-100">
        <td class="py-1.5 pr-3 font-mono text-xs">${escape(p.edition_id)}</td>
        <td class="py-1.5 pr-3 text-red-600">✗ failed</td>
        <td class="py-1.5 pr-3"></td>
        <td class="py-1.5 text-xs text-slate-600">${escape(p.error || '')}</td>
      </tr>`;
    }).join('');
    results.innerHTML = `<table class="w-full text-sm">
      <thead><tr class="border-b text-xs uppercase text-slate-500">
        <th class="text-left py-1 pr-3">Edition</th>
        <th class="text-left py-1 pr-3">Status</th>
        <th class="text-left py-1 pr-3">Size</th>
        <th class="text-left py-1">Detail</th>
      </tr></thead>
      <tbody>${rowsHtml}</tbody>
    </table>`;
    results.classList.remove('hidden');
  }

  btn.disabled = false;
  btn.classList.remove('opacity-50', 'cursor-not-allowed');
  btn.textContent = 'Build all 5 editions';
}

// Phase ψ.5 — open a sample-chapter HTML preview in a new tab.
// The endpoint returns text/html on success or JSON error on
// failure; we open the URL directly (browser handles content-type),
// but pre-flight with a HEAD-style fetch first so we can show
// inline error messages instead of dumping JSON in a tab.
async function openSample() {
  const ed = document.getElementById('sample-edition').value;
  const book = (document.getElementById('sample-book').value || '').trim();
  const f = document.getElementById('sample-from').value;
  const t = document.getElementById('sample-to').value;
  const status = document.getElementById('sample-status');
  if (!ed) { status.textContent = 'Pick an edition.'; status.className = 'text-xs mt-2 text-amber-700'; return; }
  if (!book) { status.textContent = 'Enter a book code (e.g. gen, mat, rev).'; status.className = 'text-xs mt-2 text-amber-700'; return; }
  status.textContent = 'Generating preview…';
  status.className = 'text-xs mt-2 text-slate-500';
  const url = `/api/sample/${encodeURIComponent(ed)}` +
              `?book=${encodeURIComponent(book)}` +
              `&from=${encodeURIComponent(f)}` +
              `&to=${encodeURIComponent(t)}`;
  // Pre-flight to surface errors inline before opening a new tab
  try {
    const r = await fetch(url);
    if (!r.ok) {
      let msg = `${r.status} ${r.statusText}`;
      try { const j = await r.json(); if (j && j.message) msg = j.message; } catch (_) {}
      status.textContent = '✗ ' + msg;
      status.className = 'text-xs mt-2 text-red-600';
      return;
    }
  } catch (e) {
    status.textContent = '✗ ' + (e.message || 'request failed');
    status.className = 'text-xs mt-2 text-red-600';
    return;
  }
  status.textContent = '✓ opening in new tab…';
  status.className = 'text-xs mt-2 text-emerald-700';
  window.open(url, '_blank');
}

async function loadPreview(edition_id) {
  CURRENT_ID = edition_id;
  document.getElementById('preview').classList.add('hidden');
  document.getElementById('export-status').innerHTML = '';

  const res = await fetch(`/api/export/preview/${encodeURIComponent(edition_id)}`);
  const data = await res.json();
  if (data.error) {
    document.getElementById('loading').textContent = 'error: ' + data.error;
    document.getElementById('loading').classList.remove('hidden');
    return;
  }

  document.getElementById('ed-title').textContent = data.edition.title;
  document.getElementById('ed-urn').textContent = 'urn:yhwh:edition:' + (data.edition.id || '');
  document.getElementById('ed-audience').textContent = data.edition.target_audience;
  document.getElementById('ed-notes').textContent = data.edition.notes_field;
  document.getElementById('sum-books').textContent = data.summary.books;
  document.getElementById('sum-notes').textContent = data.summary.notes_shipping.toLocaleString();
  document.getElementById('sum-kinds').textContent = `${data.summary.kinds_enabled} / ${data.summary.kinds_total}`;
  document.getElementById('sum-canon').textContent = data.edition.canon || '—';

  // Category bar chart
  const total = data.summary.notes_shipping || 1;
  const cb = document.getElementById('cat-breakdown');
  if (!data.category_breakdown.length) {
    cb.innerHTML = '<div class="text-xs text-slate-400">no notes shipping</div>';
  } else {
    cb.innerHTML = data.category_breakdown.map(c => {
      const pct = (c.count / total * 100).toFixed(1);
      return `
        <div>
          <div class="flex justify-between text-xs">
            <span><span class="symbol text-slate-500">${c.symbol}</span> ${c.label}</span>
            <span class="font-mono text-slate-500">${c.count.toLocaleString()} <span class="text-slate-400">(${pct}%)</span></span>
          </div>
          <div class="h-1.5 bg-slate-100 rounded overflow-hidden">
            <div class="h-full bg-emerald-500" style="width:${pct}%"></div>
          </div>
        </div>`;
    }).join('');
  }

  // Filtered-out list
  const fo = document.getElementById('filtered');
  if (!data.filtered_out_kinds.length) {
    fo.innerHTML = '<div class="text-xs text-slate-400">nothing filtered out — every potential note will ship.</div>';
  } else {
    fo.innerHTML = data.filtered_out_kinds.map(k => `
      <div class="flex justify-between border-b border-slate-100 py-1 last:border-0">
        <span class="font-mono text-xs text-slate-600">${k.kind}</span>
        <span class="font-mono text-xs text-amber-600">+${k.count}</span>
      </div>
    `).join('');
  }

  // Last build info
  const lb = document.getElementById('last-build');
  if (data.last_build) {
    const dt = new Date(data.last_build.mtime * 1000);
    lb.innerHTML = `previous build: <a href="/api/export/download/${encodeURIComponent(data.last_build.filename)}" class="text-blue-600 hover:underline">${data.last_build.filename}</a> · ${data.last_build.size_kb} KB · ${dt.toLocaleString()}`;
  } else {
    lb.textContent = '';
  }

  document.getElementById('preview').classList.remove('hidden');
}

document.getElementById('export-btn').addEventListener('click', exportNow);

async function exportNow() {
  const btn = document.getElementById('export-btn');
  const status = document.getElementById('export-status');
  btn.disabled = true;
  btn.classList.add('opacity-60');
  status.innerHTML = '<span class="pulsing">building EPUB · ~10-30 seconds · please wait …</span>';
  try {
    const r = await fetch(`/api/export/build/${encodeURIComponent(CURRENT_ID)}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({version: 'v28a'}),
    });
    const data = await r.json();
    if (!r.ok || data.error) {
      status.innerHTML = `<div class="text-red-600 font-medium">✗ ${data.error || 'build failed'}</div>` +
        (data.stderr ? `<pre class="text-xs bg-slate-100 p-2 mt-2 overflow-auto max-h-40">${data.stderr.replace(/[<>]/g, c => ({'<':'&lt;','>':'&gt;'}[c]))}</pre>` : '');
      btn.disabled = false;
      btn.classList.remove('opacity-60');
      return;
    }
    status.innerHTML = `
      <div class="text-emerald-700 font-medium">✓ Build complete</div>
      <div class="mt-2 flex items-center gap-3">
        <a href="${data.download_url}" download
           class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium">
          ⬇ Download ${data.filename}
        </a>
        <span class="text-xs text-slate-500">${data.size_mb} MB</span>
      </div>`;
    // reload preview to update last_build
    loadPreview(CURRENT_ID);
    btn.disabled = false;
    btn.classList.remove('opacity-60');
  } catch (e) {
    status.innerHTML = `<div class="text-red-600">✗ ${e.message}</div>`;
    btn.disabled = false;
    btn.classList.remove('opacity-60');
  }
}

init().catch(e => {
  document.getElementById('loading').textContent = 'failed: ' + e.message;
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


# ψ.14: substitute the canonical nav link list from _design.CONSOLES.
# Single source of truth — adding a console or renaming a label flows
# through every consumer automatically.
# ψ.13.5: consolidated design-system substitution.
EXPORT_HTML = apply_design_system(EXPORT_HTML, "/export")

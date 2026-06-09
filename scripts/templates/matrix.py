"""HTML for /matrix console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import MATRIX_HTML` callers.

ψ.15 editor-console polish (2026-05-09): cross-link nav substituted
from `_design.HEADER_NAV_LINKS("/matrix")` and `BUYER_ARC_POLISH_CSS`
inlined from `_design`, mirroring the ψ.14 buyer-arc pattern.
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
    apply_design_system,
)

__all__ = ["MATRIX_HTML", "HEADER_NAV_LINKS", "BUYER_ARC_POLISH_CSS"]

MATRIX_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>YHWH Ya' Way · Symbol Toggle Matrix</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
  .symbol { font-size: 1.4em; line-height: 1; display: inline-block; width: 1.5em; text-align: center; }
  .cat-row { cursor: pointer; user-select: none; }
  .cat-row:hover { background: #f3f4f6; }
  .kind-row { padding-left: 2em; font-size: 0.9em; }
  .count-cell { font-variant-numeric: tabular-nums; text-align: right; padding: 0.25rem 0.5rem; min-width: 4.5rem; }
  .count-zero { color: #574532; }
  .count-disabled { color: #9A6E12; font-style: italic; }
  .count-ok { color: #1f2937; }
  .pill { display: inline-block; padding: 0.1em 0.6em; border-radius: 9999px; font-size: 0.75em; }
  /* ψ.12 — sticky column headers + first-column row labels.
     Without this, scrolling right (with many editions) loses the
     column headers and scrolling down loses the row labels. */
  .matrix-table thead th {
    position: sticky;
    top: 0;
    background: #f8fafc;
    z-index: 2;
  }
  .matrix-table tbody td:first-child,
  .matrix-table thead th:first-child {
    position: sticky;
    left: 0;
    background: white;
    z-index: 1;
  }
  .matrix-table thead th:first-child { background: #f8fafc; z-index: 3; }
  .matrix-table tbody tr.cat-row td:first-child { background: #fafafa; }
  .matrix-table-wrap { max-height: 75vh; overflow: auto; }
  details > summary { list-style: none; }
  details > summary::-webkit-details-marker { display: none; }
  details > summary::before { content: "▸"; display: inline-block; width: 1em; transition: transform 0.15s; color: #94a3b8; }
  details[open] > summary::before { transform: rotate(90deg); }
  /* ψ.18.1 — drilldown rows put the arrow inline as a flex item
     instead of relying on the ::before pseudo (which doesn't sit
     beside the row's flex layout). Suppress the pseudo for this
     class and rotate the inline span instead. */
  details.psi181-drilldown > summary::before { content: none; }
  details.psi181-drilldown > summary .psi181-arrow {
    display: inline-block; transition: transform 0.15s;
  }
  details.psi181-drilldown[open] > summary .psi181-arrow {
    transform: rotate(90deg);
  }
  /* ψ.18.2 — nested expand-all for the long tail of books beyond
     the top-5. Lazy-rendered on first toggle so kinds spanning
     60+ books don't balloon the sidebar at first paint. Same
     suppress-pseudo + inline-arrow pattern as psi181. */
  details.psi182-rest > summary::before { content: none; }
  details.psi182-rest > summary {
    cursor: pointer;
    list-style: none;
  }
  details.psi182-rest > summary .psi182-arrow {
    display: inline-block; transition: transform 0.15s;
  }
  details.psi182-rest[open] > summary .psi182-arrow {
    transform: rotate(90deg);
  }
  /* ψ.26 — bulk-op visual cues. When a drag-select is in progress,
     hovered kind rows get a subtle highlight so the operator can
     see which rows are about to be toggled. The cursor switches to
     row-resize during a drag. */
  body.psi26-dragging { cursor: ns-resize; }
  body.psi26-dragging .kind-row.psi26-drag-touched {
    background: #eff6ff;
  }
  /* "↗ all" inline button per kind row — small, low-emphasis. */
  .psi26-applyall-btn {
    font-size: 0.65rem;
    color: #2563eb;
    margin-left: 0.5em;
    cursor: pointer;
    background: none;
    border: none;
    padding: 0;
  }
  .psi26-applyall-btn:hover { text-decoration: underline; }
  /* ψ.20 — heat-map cells. Aspect-1 squares with smooth color
     transitions on toggle-driven re-renders. */
  .psi20-cell {
    aspect-ratio: 1 / 1;
    border-radius: 3px;
    cursor: default;
    font-size: 0.55rem;
    color: rgba(255, 255, 255, 0.85);
    text-align: center;
    font-family: ui-monospace, SFMono-Regular, monospace;
    line-height: 1;
    padding-top: 2px;
    overflow: hidden;
    transition: background 200ms ease;
    border: 1px solid rgba(0, 0, 0, 0.05);
  }
  .psi20-cell.empty {
    color: #94a3b8;
    background: #e2e8f0;
  }
  .psi20-legend-cell {
    width: 1em;
    height: 0.7em;
    border-radius: 2px;
    display: inline-block;
  }
  /* ψ.38 — matrix heatmap mode. Toggle in header switches every
     .count-cell from raw-number display to a color-intensity cell.
     5 buckets (1=lightest, 5=darkest). Cell text stays black-on-X
     for readability; we shade the BACKGROUND so the value remains
     selectable + copyable for keyboard users. */
  body.matrix-heatmap-on .matrix-heatmap-1 { background: #f0fdf4; }   /* emerald-50 */
  body.matrix-heatmap-on .matrix-heatmap-2 { background: #bbf7d0; }   /* emerald-200 */
  body.matrix-heatmap-on .matrix-heatmap-3 { background: #4ade80; color: #064e3b; }  /* emerald-400 + emerald-900 text */
  body.matrix-heatmap-on .matrix-heatmap-4 { background: #16a34a; color: #f0fdf4; }  /* emerald-600 + emerald-50 text */
  body.matrix-heatmap-on .matrix-heatmap-5 { background: #14532d; color: #f0fdf4; }  /* emerald-900 + emerald-50 text */
  /* When heatmap is on, hide the numeric content of the cells —
     keep the data accessible via screen readers (text stays in
     the DOM) but de-emphasize visually. The cell BACKGROUND
     carries the information. */
  body.matrix-heatmap-on .count-cell.matrix-heatmap-1,
  body.matrix-heatmap-on .count-cell.matrix-heatmap-2,
  body.matrix-heatmap-on .count-cell.matrix-heatmap-3,
  body.matrix-heatmap-on .count-cell.matrix-heatmap-4,
  body.matrix-heatmap-on .count-cell.matrix-heatmap-5 {
    /* Keep text visible; the contrast pairing on each bucket is
       chosen so the digit + background stays readable. */
    transition: background-color 200ms ease, color 200ms ease;
  }
  #psi38-heatmap-toggle {
    cursor: pointer;
    user-select: none;
    font-size: 0.7rem;
    padding: 0.2rem 0.5rem;
    border: 1px solid #D2BE90;
    border-radius: 4px;
    background: white;
    color: #475569;
  }
  #psi38-heatmap-toggle.psi38-active {
    background: #14532d;
    color: #f0fdf4;
    border-color: #14532d;
  }
  #psi38-heatmap-toggle:hover {
    border-color: #94a3b8;
  }
</style>
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Symbol Toggle Matrix</h1>
    <p class="text-xs text-slate-500">read-only · Phase μ.1</p>
  </div>
  <div class="flex items-center gap-4 text-xs flex-wrap">
    <!-- HEADER_NAV_LINKS -->
    <span id="corpus-progress" class="ml-auto text-xs text-slate-500" title="corpus depth toward the 35,000-note Ethiopian Tewahedo target">·· loading ··</span>
    <!-- ψ.38 — heatmap mode toggle. localStorage-persisted. -->
    <button type="button" id="psi38-heatmap-toggle"
      aria-pressed="false"
      title="Toggle heatmap mode (color intensity = note count)">Heatmap</button>
    <!-- ψ.29 — keyboard help affordance. Same modal opens via `?`. -->
    <button type="button" id="psi29-help-btn"
      class="w-6 h-6 rounded-full border border-slate-300 text-slate-500 hover:text-slate-800 hover:border-slate-400 flex items-center justify-center"
      aria-label="Keyboard shortcuts" title="Keyboard shortcuts (?)">?</button>
  </div>
</header>
<script>
// ψ.38 — matrix heatmap mode. Toggle in header switches every
// .count-cell from raw-number display to color-intensity buckets.
// 5 buckets via simple even-distribution of (count > 0) values.
// localStorage key `ebible_matrix_heatmap_mode` ('on' | 'off')
// persists the user's choice across reloads.
//
// Re-applies via MutationObserver when /matrix re-renders (after
// a save, kind-toggle, etc.) — no coupling to matrix_app.js's
// internal render lifecycle.
(function () {
  'use strict';
  var STORAGE_KEY = 'ebible_matrix_heatmap_mode';
  var BUCKET_CLASSES = [
    'matrix-heatmap-1',
    'matrix-heatmap-2',
    'matrix-heatmap-3',
    'matrix-heatmap-4',
    'matrix-heatmap-5'
  ];

  function loadMode() {
    try {
      return localStorage.getItem(STORAGE_KEY) === 'on';
    } catch (e) { return false; }
  }
  function saveMode(on) {
    try { localStorage.setItem(STORAGE_KEY, on ? 'on' : 'off'); } catch (e) {}
  }

  function clearHeatmap() {
    var cells = document.querySelectorAll('.count-cell');
    for (var i = 0; i < cells.length; i++) {
      for (var j = 0; j < BUCKET_CLASSES.length; j++) {
        cells[i].classList.remove(BUCKET_CLASSES[j]);
      }
    }
  }

  function applyHeatmap() {
    var cells = document.querySelectorAll('.count-cell');
    if (cells.length === 0) return;
    // Collect numeric values; ignore cells with no digit content
    // (e.g., header cells that are .count-cell for alignment).
    var values = [];
    var numeric = [];
    for (var i = 0; i < cells.length; i++) {
      var text = (cells[i].textContent || '').trim();
      var n = parseInt(text.replace(/[^\\d-]/g, ''), 10);
      if (isFinite(n) && n > 0 && /\\d/.test(text)) {
        values.push(n);
        numeric.push({ cell: cells[i], value: n });
      }
    }
    if (numeric.length === 0) return;
    var maxVal = Math.max.apply(null, values);
    if (maxVal === 0) return;
    // Bucket by even-thirds of the linear scale; tweak with log
    // for skewed distributions if needed. 5 buckets total.
    for (var k = 0; k < numeric.length; k++) {
      var ratio = numeric[k].value / maxVal;
      var idx;
      if (ratio < 0.05)      idx = 0;  // matrix-heatmap-1 (faint)
      else if (ratio < 0.20) idx = 1;
      else if (ratio < 0.50) idx = 2;
      else if (ratio < 0.80) idx = 3;
      else                   idx = 4;  // matrix-heatmap-5 (deepest)
      // Remove any prior bucket; apply current.
      for (var b = 0; b < BUCKET_CLASSES.length; b++) {
        numeric[k].cell.classList.remove(BUCKET_CLASSES[b]);
      }
      numeric[k].cell.classList.add(BUCKET_CLASSES[idx]);
    }
  }

  function syncButton(btn, on) {
    btn.classList.toggle('psi38-active', on);
    btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    btn.textContent = on ? 'Numbers' : 'Heatmap';
  }

  function setMode(on) {
    var btn = document.getElementById('psi38-heatmap-toggle');
    if (btn) syncButton(btn, on);
    document.body.classList.toggle('matrix-heatmap-on', on);
    if (on) {
      applyHeatmap();
    } else {
      clearHeatmap();
    }
    saveMode(on);
  }

  function init() {
    var btn = document.getElementById('psi38-heatmap-toggle');
    if (!btn) return;
    var initial = loadMode();
    syncButton(btn, initial);
    if (initial) {
      document.body.classList.add('matrix-heatmap-on');
      // Defer the initial application until after matrix_app.js
      // populates the table. Two strategies: MutationObserver on
      // the table body (catches the render), and an interval-
      // bounded retry for safety.
      var attempts = 0;
      var tryApply = function () {
        if (document.querySelectorAll('.count-cell').length > 0) {
          applyHeatmap();
        } else if (attempts++ < 30) {
          setTimeout(tryApply, 200);
        }
      };
      tryApply();
    }
    btn.addEventListener('click', function () {
      setMode(!document.body.classList.contains('matrix-heatmap-on'));
    });
    // Watch for re-renders so kind-toggle saves don't strand
    // the heatmap classes.
    var observer = new MutationObserver(function () {
      if (document.body.classList.contains('matrix-heatmap-on')) {
        applyHeatmap();
      }
    });
    var main = document.querySelector('main') || document.body;
    observer.observe(main, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
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


<main class="p-6 max-w-7xl mx-auto">
  <div id="loading" class="text-center text-slate-400 py-20">loading matrix …</div>
  <div id="content" class="hidden grid grid-cols-1 lg:grid-cols-[1fr_20rem] gap-6">

    <!-- LEFT: matrix -->
    <section class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      <div class="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
        <h2 class="font-semibold">Categories &times; Editions</h2>
        <div class="text-xs text-slate-500" id="legend">
          <span class="count-ok">●</span> enabled count &nbsp;
          <span class="count-disabled">●</span> potential (filtered out) &nbsp;
          <span class="count-zero">●</span> no notes
        </div>
      </div>
      <!-- ψ.12 — inline switch-confirm banner replaces a blocking
           confirm() that was easy to dismiss accidentally. -->
      <div id="switch-confirm" class="hidden mx-4 my-2 px-3 py-2 rounded border border-amber-300 bg-amber-50 text-sm text-amber-900 flex items-center justify-between gap-3">
        <span>You have unsaved changes. Switching editions will discard them.</span>
        <span class="flex items-center gap-2">
          <button type="button" id="switch-discard" class="text-xs px-3 py-1 rounded bg-amber-600 text-white hover:bg-amber-700">Discard &amp; switch</button>
          <button type="button" id="switch-cancel" class="text-xs px-3 py-1 rounded border border-slate-300 hover:bg-slate-50">Cancel</button>
        </span>
      </div>
      <!-- ψ.28 — kind search-and-filter. Type-ahead hides non-matching
           kind rows; matches kind code / label / category id, label,
           symbol. `/` focuses; Esc clears + blurs. -->
      <div class="px-4 py-2 border-b border-slate-200 flex items-center gap-2">
        <input id="psi28-kind-filter" type="search"
          placeholder="Filter kinds — code, label, category, symbol  (press / to focus)"
          class="flex-1 border border-slate-300 rounded px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-blue-200"
          autocomplete="off" spellcheck="false">
        <button type="button" id="psi28-clear-filter"
          class="hidden text-xs text-blue-600 hover:underline">clear</button>
        <span id="psi28-filter-status" class="text-[0.65rem] text-slate-400 tabular-nums whitespace-nowrap"></span>
      </div>
      <div class="matrix-table-wrap">
      <table class="w-full text-sm matrix-table">
        <thead class="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr id="header-row">
            <th class="text-left px-3 py-2 w-72">
              <span class="inline-block w-5"></span>Category / Kind
            </th>
            <!-- edition columns injected by JS -->
          </tr>
        </thead>
        <tbody id="body"></tbody>
      </table>
      </div>
    </section>

    <!-- RIGHT: active edition panel -->
    <aside class="space-y-4">
      <section class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <label class="block text-xs uppercase tracking-wide text-slate-500 mb-1">Edit Edition</label>
        <select id="edition-select" class="w-full border border-slate-300 rounded px-2 py-1.5 text-sm"></select>
        <div id="edition-info" class="mt-3 text-sm space-y-1.5"></div>
        <div id="save-controls" class="mt-4 hidden">
          <div id="dirty-banner" class="hidden text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1.5 mb-2">
            <span id="dirty-count"></span> unsaved change(s)
          </div>
          <div class="flex gap-2">
            <button id="save-btn" class="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-3 py-1.5 rounded disabled:opacity-50 disabled:cursor-not-allowed" disabled>Save</button>
            <button id="reset-btn" class="px-3 py-1.5 text-sm border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50" disabled>Reset</button>
          </div>
          <!-- ψ.29 — undo/redo affordance. Cmd/Ctrl+Z and
               Cmd+Shift+Z / Ctrl+Y also drive these. Stack
               clears on edition switch / reset / save. -->
          <div class="flex gap-2 mt-2">
            <button type="button" id="psi29-undo-btn"
              class="flex-1 px-3 py-1 text-xs border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
              title="Undo last toggle (Cmd/Ctrl + Z)" disabled>↶ Undo</button>
            <button type="button" id="psi29-redo-btn"
              class="flex-1 px-3 py-1 text-xs border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
              title="Redo (Cmd+Shift+Z / Ctrl+Y)" disabled>↷ Redo</button>
          </div>
          <button id="save-as-btn" class="w-full mt-2 px-3 py-1.5 text-sm border border-slate-300 rounded hover:bg-slate-50 text-slate-700">
            Save As Scenario…
          </button>
          <div id="save-status" class="text-xs text-slate-500 mt-2"></div>
        </div>
      </section>

      <section class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <div class="flex items-center justify-between mb-2 flex-wrap gap-1">
          <h3 class="text-xs uppercase tracking-wide text-slate-500">Saved scenarios</h3>
          <div class="flex items-center gap-2">
            <!-- ψ.27 — paste-textarea import for portability -->
            <button id="psi27-import-btn" class="text-xs text-blue-600 hover:underline">Import YAML…</button>
            <button id="refresh-scenarios" class="text-xs text-blue-600 hover:underline">refresh</button>
          </div>
        </div>
        <div id="scenarios-list" class="space-y-1.5 text-sm">
          <div class="text-xs text-slate-400">loading scenarios…</div>
        </div>
      </section>

      <section class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <h3 class="text-xs uppercase tracking-wide text-slate-500 mb-2">Categories breakdown</h3>
        <div id="breakdown"></div>
      </section>

      <!-- ψ.18 — per-symbol totals + per-book sparkline -->
      <section class="bg-white rounded-lg shadow-sm border border-slate-200 p-4" id="totals-section">
        <h3 class="text-xs uppercase tracking-wide text-slate-500 mb-2">Symbol totals</h3>
        <div id="totals-edition" class="text-xs text-slate-400 mb-2">whole edition</div>
        <div id="totals-list" class="space-y-2"></div>
        <div class="text-xs text-slate-400 mt-3 leading-relaxed">
          Sparkline shows note distribution across the edition's books in canonical order. Hover for per-book counts.
        </div>
      </section>

      <!-- ψ.20 — note-density heat-map. Per-book grid colored by
           note-count percentile. Reuses Matrix.per_book data;
           respects LOCAL_ENABLED so the visual updates as the
           operator toggles kinds. -->
      <section class="bg-white rounded-lg shadow-sm border border-slate-200 p-4" id="psi20-heatmap-section">
        <h3 class="text-xs uppercase tracking-wide text-slate-500 mb-2">Density heat-map</h3>
        <div class="text-xs text-slate-400 mb-3">
          Per-book note count for currently-enabled kinds. Greener = denser; redder = sparse. Hover for the exact count.
        </div>
        <div id="psi20-heatmap-grid" class="grid gap-1"
             style="grid-template-columns: repeat(auto-fill, minmax(2.4em, 1fr));">
          <!-- JS-populated cells -->
        </div>
        <div class="flex items-center justify-between text-[0.65rem] text-slate-500 mt-3 leading-tight gap-1">
          <span class="psi20-legend-cell" style="background:#dc2626"></span>
          <span class="flex-1 text-center">sparse</span>
          <span class="psi20-legend-cell" style="background:#f59e0b"></span>
          <span class="flex-1 text-center">mid</span>
          <span class="psi20-legend-cell" style="background:#16a34a"></span>
          <span class="flex-1 text-center">dense</span>
          <span class="psi20-legend-cell" style="background:#e2e8f0"></span>
          <span class="flex-1 text-center">empty</span>
        </div>
      </section>
    </aside>

  </div>
</main>

<!-- ψ.26 — Apply-to-all-editions confirmation modal. Triggered by
     the "↗ all" button on each kind row. Shows the current
     per-edition state for that kind so the operator knows what
     they're about to change. -->
<div id="psi26-applyall-overlay"
  class="hidden fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center"
  role="dialog" aria-modal="true" aria-labelledby="psi26-applyall-title"
  aria-hidden="true">
  <div class="bg-white rounded-lg shadow-lg max-w-md w-full mx-4 p-5">
    <div class="flex items-center justify-between mb-3">
      <h2 id="psi26-applyall-title" class="text-lg font-semibold">Apply to all editions</h2>
      <button type="button" id="psi26-applyall-close"
        class="text-slate-400 hover:text-slate-700 text-xl leading-none px-2"
        aria-label="Close">&times;</button>
    </div>
    <p class="text-sm text-slate-700 mb-1">Kind: <span id="psi26-applyall-kind" class="font-mono"></span></p>
    <p id="psi26-applyall-summary" class="text-xs text-slate-500 mb-3"></p>
    <div id="psi26-applyall-perlist" class="text-xs text-slate-500 mb-3 max-h-40 overflow-y-auto border border-slate-200 rounded p-2"></div>
    <div class="flex gap-2 flex-wrap">
      <button type="button" id="psi26-applyall-enable"
        class="px-3 py-1.5 text-sm rounded bg-emerald-600 text-white hover:bg-emerald-700">Enable in all</button>
      <button type="button" id="psi26-applyall-disable"
        class="px-3 py-1.5 text-sm rounded border border-rose-300 text-rose-700 hover:bg-rose-50">Disable in all</button>
      <button type="button" id="psi26-applyall-cancel"
        class="px-3 py-1.5 text-sm border border-slate-300 rounded hover:bg-slate-50 ml-auto">Cancel</button>
    </div>
    <p id="psi26-applyall-feedback" class="text-xs mt-3"></p>
    <p class="text-[0.65rem] text-slate-400 mt-2">Saves directly to editions.yaml — bypasses the per-edition Save button. Undo history is cleared.</p>
  </div>
</div>

<!-- ψ.27 — Export YAML modal. Surfaces the raw scenario YAML as a
     read-only textarea + Copy + Download buttons. Opens from the
     per-scenario "export" link. -->
<div id="psi27-export-overlay"
  class="hidden fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center"
  role="dialog" aria-modal="true" aria-labelledby="psi27-export-title"
  aria-hidden="true">
  <div class="bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4 p-5">
    <div class="flex items-center justify-between mb-3">
      <h2 id="psi27-export-title" class="text-lg font-semibold">Export scenario</h2>
      <button type="button" id="psi27-export-close"
        class="text-slate-400 hover:text-slate-700 text-xl leading-none px-2"
        aria-label="Close">&times;</button>
    </div>
    <p class="text-xs text-slate-500 mb-2"><span id="psi27-export-name" class="font-mono"></span> — copy the YAML below or download the file.</p>
    <textarea id="psi27-export-yaml" readonly
      class="w-full h-64 border border-slate-300 rounded p-2 text-xs font-mono bg-slate-50"
      spellcheck="false"></textarea>
    <div class="flex gap-2 mt-3 flex-wrap">
      <button type="button" id="psi27-export-copy"
        class="px-3 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700">Copy to clipboard</button>
      <a id="psi27-export-download" download class="hidden"></a>
      <button type="button" id="psi27-export-download-btn"
        class="px-3 py-1.5 text-sm border border-slate-300 rounded hover:bg-slate-50">Download .yaml</button>
      <span id="psi27-export-feedback" class="text-xs text-emerald-700 ml-auto self-center"></span>
    </div>
  </div>
</div>

<!-- ψ.27 — Import YAML modal. Paste-textarea + name input. Reports
     parse / unknown-kind / conflict errors inline. -->
<div id="psi27-import-overlay"
  class="hidden fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center"
  role="dialog" aria-modal="true" aria-labelledby="psi27-import-title"
  aria-hidden="true">
  <div class="bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4 p-5">
    <div class="flex items-center justify-between mb-3">
      <h2 id="psi27-import-title" class="text-lg font-semibold">Import scenario from YAML</h2>
      <button type="button" id="psi27-import-close"
        class="text-slate-400 hover:text-slate-700 text-xl leading-none px-2"
        aria-label="Close">&times;</button>
    </div>
    <label class="block text-xs uppercase tracking-wide text-slate-500 mb-1">Scenario name</label>
    <input type="text" id="psi27-import-name" maxlength="41"
      placeholder="lowercase a–z, 0–9, _ or -"
      class="w-full border border-slate-300 rounded px-2 py-1 text-sm mb-3">
    <label class="block text-xs uppercase tracking-wide text-slate-500 mb-1">YAML body</label>
    <textarea id="psi27-import-yaml"
      class="w-full h-56 border border-slate-300 rounded p-2 text-xs font-mono"
      spellcheck="false"
      placeholder="label: My Scenario&#10;based_on: null&#10;enabled_kinds:&#10;  - lang-hebrew&#10;  - xref-citation"></textarea>
    <label class="flex items-center gap-2 text-xs text-slate-600 mt-2">
      <input type="checkbox" id="psi27-import-overwrite"> overwrite if a scenario by that name already exists
    </label>
    <div class="flex gap-2 mt-3 flex-wrap items-center">
      <button type="button" id="psi27-import-submit"
        class="px-3 py-1.5 text-sm rounded bg-emerald-600 text-white hover:bg-emerald-700">Import</button>
      <button type="button" id="psi27-import-cancel"
        class="px-3 py-1.5 text-sm border border-slate-300 rounded hover:bg-slate-50">Cancel</button>
      <span id="psi27-import-feedback" class="text-xs ml-auto"></span>
    </div>
  </div>
</div>

<!-- ψ.29 — keyboard shortcuts help modal. Opens via `?` key or
     the header help button. Closes via Esc, click outside, or X. -->
<div id="psi29-help-overlay"
  class="hidden fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center"
  role="dialog" aria-modal="true" aria-labelledby="psi29-help-title"
  aria-hidden="true">
  <div class="bg-white rounded-lg shadow-lg max-w-md w-full mx-4 p-5">
    <div class="flex items-center justify-between mb-3">
      <h2 id="psi29-help-title" class="text-lg font-semibold">Keyboard shortcuts</h2>
      <button type="button" id="psi29-help-close"
        class="text-slate-400 hover:text-slate-700 text-xl leading-none px-2"
        aria-label="Close">&times;</button>
    </div>
    <dl class="text-sm">
      <div class="flex items-center justify-between py-1.5 border-b border-slate-100">
        <dt><kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">/</kbd></dt>
        <dd class="text-slate-600">Focus the kind filter</dd>
      </div>
      <div class="flex items-center justify-between py-1.5 border-b border-slate-100">
        <dt><kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">Esc</kbd></dt>
        <dd class="text-slate-600">Clear filter / close help</dd>
      </div>
      <div class="flex items-center justify-between py-1.5 border-b border-slate-100">
        <dt><kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">?</kbd></dt>
        <dd class="text-slate-600">Show this help</dd>
      </div>
      <div class="flex items-center justify-between py-1.5 border-b border-slate-100">
        <dt><kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">Tab</kbd></dt>
        <dd class="text-slate-600">Move focus to next checkbox</dd>
      </div>
      <div class="flex items-center justify-between py-1.5 border-b border-slate-100">
        <dt><kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">Space</kbd></dt>
        <dd class="text-slate-600">Toggle the focused checkbox</dd>
      </div>
      <div class="flex items-center justify-between py-1.5 border-b border-slate-100">
        <dt class="space-x-1">
          <kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">Cmd</kbd>/<kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">Ctrl</kbd>+<kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">Z</kbd>
        </dt>
        <dd class="text-slate-600">Undo last toggle</dd>
      </div>
      <div class="flex items-center justify-between py-1.5 border-b border-slate-100">
        <dt class="space-x-1">
          <kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">Cmd</kbd>+<kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">Shift</kbd>+<kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">Z</kbd>
          <span class="text-slate-400">/</span>
          <kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">Ctrl</kbd>+<kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">Y</kbd>
        </dt>
        <dd class="text-slate-600">Redo</dd>
      </div>
      <div class="flex items-center justify-between py-1.5">
        <dt class="space-x-1">
          <kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">Cmd</kbd>/<kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">Ctrl</kbd>+<kbd class="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 font-mono text-xs">S</kbd>
        </dt>
        <dd class="text-slate-600">Save the active edition</dd>
      </div>
    </dl>
    <p class="text-xs text-slate-400 mt-3">Undo history clears on edition switch, reset, and save.</p>
  </div>
</div>

<script src="/static/matrix.js" defer></script>

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


# ψ.13.5: consolidated design-system substitution.
MATRIX_HTML = apply_design_system(MATRIX_HTML, "/matrix")

"""HTML for /build-my-bible console — the Navigator Console (Phase C2).

The hierarchical-customization surface: a builder picks an edition and
navigates it "like a Bible" (Bible → book → chapter → verse), toggling
note-symbol families/kinds and translation-popup languages at every
level. This module is the static SHELL only (Phase C2-2): header +
edition picker + breadcrumb + left book rail + right level-panel, plus
a JS skeleton (fetch helpers stubbed, render functions placeholder).
The drill-down logic, the toggle controls, and the save flow ship in
later tasks (C2-3 / C2-4 / C2-5).

Reads (already shipped, Phase C2-1 — do not modify):
  - GET /api/customize                          → edition list for the picker
  - GET /api/build-my-bible/<edition>           → edition overview
  - GET /api/build-my-bible/<edition>/<book>    → per-chapter list
  - GET /api/build-my-bible/<edition>/<book>/<ch> → per-verse list

Cross-link nav + design-system markers are substituted at module load
via ``apply_design_system(..., "/build-my-bible")`` per the ψ.13.5
single-source-of-truth convention (same pattern as sources.py /
distribution.py / ops.py). Adding the route to ``_design.CONSOLES``
auto-propagates the cross-link into every console's HEADER_NAV.
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
    apply_design_system,
)

__all__ = ["BUILD_MY_BIBLE_HTML", "HEADER_NAV_LINKS", "BUYER_ARC_POLISH_CSS"]

BUILD_MY_BIBLE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>YHWH Ya' Way · Build My Bible</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
  .symbol { font-size: 1.1em; line-height: 1; display: inline-block; width: 1.4em; text-align: center; }
  .book-row { cursor: pointer; user-select: none; }
  .book-row:hover { background: #f1f5f9; }
  .book-row.active { background: #dbeafe; font-weight: 600; }
  .crumb-link { cursor: pointer; }  /* used by renderBreadcrumb() — clickable crumbs land in C2-3 */
  .crumb-link:hover { text-decoration: underline; }
  .verse-anchor { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
</style>
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Build My Bible</h1>
    <p class="text-xs text-slate-500">navigate an edition like a Bible — book → chapter → verse — and tune note symbols + popup languages at every level</p>
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

<!-- Edition picker + breadcrumb bar. The picker selects which edition
     we navigate; the breadcrumb shows the current drill-down level
     (Bible → book → chapter → verse) and lets the user step back up.
     Both are static here — wiring lands in C2-3. -->
<section class="max-w-7xl mx-auto px-6 pt-6">
  <div class="bg-white rounded-lg shadow-sm border border-slate-200 px-4 py-3 flex items-center gap-4 flex-wrap">
    <label class="text-sm text-slate-600 flex items-center gap-2">
      edition:
      <select id="edition-picker" class="text-sm border border-slate-300 rounded px-2 py-1"
        title="Pick an edition to navigate and customize.">
        <option value="">— choose an edition —</option>
      </select>
    </label>
    <nav id="breadcrumb" aria-label="Breadcrumb"
      class="text-sm text-slate-500 flex items-center gap-1 flex-wrap">
      <span class="text-slate-400">pick an edition to begin</span>
    </nav>
  </div>
</section>

<main class="grid grid-cols-1 lg:grid-cols-[20rem_1fr] gap-6 p-6 max-w-7xl mx-auto">

  <!-- LEFT: book rail — renders in books.yaml canonical order (§6.1).
       The API returns books_canonical already ordered; never client-sort. -->
  <aside class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden lg:max-h-[80vh] lg:overflow-y-auto">
    <div class="px-3 py-2 border-b border-slate-200 sticky top-0 bg-white z-10">
      <input id="book-filter" type="text" placeholder="filter books…" maxlength="200"
        class="w-full text-sm border border-slate-300 rounded px-2 py-1">
      <div class="text-xs text-slate-500 mt-1" id="book-count"></div>
    </div>
    <div id="book-list" class="text-sm">pick an edition above …</div>
  </aside>

  <!-- RIGHT: level panel — the active drill-down level renders here
       (edition overview / chapter grid / verse list). Toggle controls
       (symbol families + popup languages) populate this panel in
       C2-3 / C2-4. -->
  <section class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
    <div class="px-4 py-3 border-b border-slate-200 flex items-center justify-between flex-wrap gap-2">
      <div>
        <h2 id="level-title" class="font-semibold">No edition selected</h2>
        <div id="level-subtitle" class="text-xs text-slate-500"></div>
      </div>
    </div>
    <div id="level-panel" class="p-4 text-sm text-slate-500">
      Pick an edition above to start building.
    </div>
  </section>

</main>

<script>
// =====================================================================
// /build-my-bible navigator — Phase C2-2 JS skeleton.
//
// This is the SHELL wiring only: state vars, fetch helpers, and empty
// render placeholders. The drill-down logic, toggle controls, and save
// flow are filled in by tasks C2-3 / C2-4 / C2-5. Every render function
// below is a deliberate stub — present so later tasks have a stable
// surface to extend, but doing nothing user-visible beyond placeholders.
// =====================================================================

// ---- navigation state ------------------------------------------------
let CUR_EDITION = '';     // edition id, '' = none chosen
let CUR_BOOK = null;      // book code, null = edition (top) level
let CUR_CHAPTER = null;   // chapter number, null = book level
let OVERVIEW = null;      // cached /api/build-my-bible/<ed> payload
let BOOKS = [];           // books_canonical (already in §6.1 order — never sort)

// ---- fetch helpers ---------------------------------------------------
// Thin wrappers over the C2-1 read API. They use window.safeFetch (the
// ω.0.6 UI-defense prelude) when available so failures surface a banner
// instead of silently breaking; they fall back to bare fetch otherwise.
async function apiGet(url) {
  if (window.safeFetch) return window.safeFetch(url);
  const r = await fetch(url);
  if (!r.ok) throw new Error(r.status + ' ' + r.statusText);
  return r.json();
}

async function fetchEditionList() {
  // The edition <select> reuses /api/customize (same source the
  // /sources console uses) so the option set stays in lockstep.
  const data = await apiGet('/api/customize');
  return (data && data.editions) || [];
}

async function fetchOverview(edition) {
  return apiGet('/api/build-my-bible/' + encodeURIComponent(edition));
}

async function fetchBook(edition, book) {
  return apiGet('/api/build-my-bible/' + encodeURIComponent(edition) +
                '/' + encodeURIComponent(book));
}

async function fetchChapter(edition, book, chapter) {
  return apiGet('/api/build-my-bible/' + encodeURIComponent(edition) +
                '/' + encodeURIComponent(book) +
                '/' + encodeURIComponent(chapter));
}

// ---- render placeholders (filled in C2-3 / C2-4) ---------------------
// Each renderer targets a fixed DOM node so later tasks only fill the
// body. For now they paint neutral placeholders.

function renderBreadcrumb() {
  // C2-3: Bible → book → chapter → verse, each step clickable to pop up.
  const el = document.getElementById('breadcrumb');
  if (!el) return;
  if (!CUR_EDITION) {
    el.innerHTML = '<span class="text-slate-400">pick an edition to begin</span>';
  }
}

function renderBookList() {
  // C2-3: render BOOKS (canonical order) into #book-list; clicking a
  // book drills into the chapter grid.
  const el = document.getElementById('book-list');
  if (!el) return;
  if (!CUR_EDITION) {
    el.innerHTML = '<div class="text-slate-400 px-3 py-2">pick an edition above …</div>';
  }
}

function renderLevelPanel() {
  // C2-3 / C2-4: render the active level (edition overview / chapter
  // grid / verse list) plus its toggle controls into #level-panel.
  const el = document.getElementById('level-panel');
  if (!el) return;
  if (!CUR_EDITION) {
    el.innerHTML = '<div class="text-slate-400">Pick an edition above to start building.</div>';
  }
}

// ---- edition picker (the one live control in the shell) --------------
async function populateEditionPicker() {
  const sel = document.getElementById('edition-picker');
  if (!sel) return;
  let editions = [];
  try {
    editions = await fetchEditionList();
  } catch (e) { /* banner already shown by safeFetch */ }
  for (const e of editions) {
    const o = document.createElement('option');
    o.value = e.id;
    o.textContent = e.short_title || e.title || e.id;
    sel.appendChild(o);
  }
  sel.addEventListener('change', onEditionChange);
}

// C2-3 fills this in (load overview, reset book/chapter, re-render the
// three panels). The shell just records the selection + re-paints the
// placeholders so the surface is honest about "nothing loaded yet".
async function onEditionChange() {
  const sel = document.getElementById('edition-picker');
  CUR_EDITION = sel ? sel.value : '';
  CUR_BOOK = null;
  CUR_CHAPTER = null;
  OVERVIEW = null;
  BOOKS = [];
  renderBreadcrumb();
  renderBookList();
  renderLevelPanel();
}

// ---- boot ------------------------------------------------------------
async function init() {
  await populateEditionPicker();
  renderBreadcrumb();
  renderBookList();
  renderLevelPanel();
}

init().catch(e => {
  const el = document.getElementById('level-panel');
  if (el) el.innerHTML = '<div class="text-red-600 p-4">' +
    (window.escapeHtml ? window.escapeHtml(e.message) : e.message) + '</div>';
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


# ψ.13.5: consolidated design-system substitution.
BUILD_MY_BIBLE_HTML = apply_design_system(BUILD_MY_BIBLE_HTML, "/build-my-bible")

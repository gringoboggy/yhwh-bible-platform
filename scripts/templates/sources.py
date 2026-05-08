"""HTML for /sources console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import SOURCES_HTML` callers.
"""

SOURCES_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>E-Bible · Sources Navigator</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
  .symbol { font-size: 1.1em; line-height: 1; display: inline-block; width: 1.4em; text-align: center; }
  .book-row { cursor: pointer; user-select: none; }
  .book-row:hover { background: #f1f5f9; }
  .book-row.active { background: #dbeafe; font-weight: 600; }
  .verse-anchor { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
  mark { background: #fef08a; padding: 0 1px; border-radius: 2px; }
</style>
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Sources Navigator</h1>
    <p class="text-xs text-slate-500">browse every note by book/chapter — verify what each edition will claim, and where each claim is sourced</p>
  </div>
  <div class="flex items-center gap-4 text-xs">
    <a href="/" class="text-blue-600 hover:underline">note editor</a>
    <a href="/matrix" class="text-blue-600 hover:underline">symbol matrix</a>
    <a href="/sources" class="font-semibold">sources</a>
    <a href="/export" class="text-blue-600 hover:underline">export</a>
    <a href="/customize" class="text-blue-600 hover:underline">customize</a>
    <a href="/audit" class="text-blue-600 hover:underline">audit</a>
    <a href="/publisher" class="text-blue-600 hover:underline">publisher</a>
    <a href="/wizard" class="text-blue-600 hover:underline">wizard</a>
    <a href="/diff" class="text-blue-600 hover:underline">diff</a>
    <a href="/compare" class="text-blue-600 hover:underline">compare</a>
    <a href="/covers" class="text-blue-600 hover:underline">covers</a>
    <a href="/preflight" class="text-blue-600 hover:underline">preflight</a>

    <a href="/ops" class="text-blue-600 hover:underline">ops</a>
    <a href="/apihelp" class="text-blue-600 hover:underline">apihelp</a>
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


<main class="grid grid-cols-1 lg:grid-cols-[20rem_1fr] gap-6 p-6 max-w-7xl mx-auto">

  <!-- LEFT: book index -->
  <aside class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden lg:max-h-[80vh] lg:overflow-y-auto">
    <div class="px-3 py-2 border-b border-slate-200 sticky top-0 bg-white z-10">
      <input id="book-filter" type="text" placeholder="filter books…" maxlength="200"
        class="w-full text-sm border border-slate-300 rounded px-2 py-1">
      <div class="text-xs text-slate-500 mt-1" id="book-count"></div>
    </div>
    <div id="book-list" class="text-sm">loading …</div>
  </aside>

  <!-- RIGHT: notes for selected book -->
  <section class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
    <div class="px-4 py-3 border-b border-slate-200 flex items-center justify-between flex-wrap gap-2">
      <div>
        <h2 id="book-title" class="font-semibold">No book selected</h2>
        <div id="book-subtitle" class="text-xs text-slate-500"></div>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <input id="note-filter" type="text" placeholder="filter notes (title / body / source)…" maxlength="200"
          class="text-sm border border-slate-300 rounded px-2 py-1 w-72">
        <select id="kind-filter" class="text-sm border border-slate-300 rounded px-2 py-1">
          <option value="">all kinds</option>
        </select>
        <span class="text-xs text-slate-400 ml-2 border-l border-slate-300 pl-2">edition:</span>
        <select id="edition-picker" class="text-sm border border-slate-300 rounded px-2 py-1" title="Pick an edition to enable per-note toggles. Choose 'browse only' to read without editing.">
          <option value="">browse only</option>
        </select>
      </div>
    </div>
    <div id="notes-area" class="p-4 text-sm text-slate-500">Pick a book on the left.</div>
  </section>

</main>

<script>
let BOOKS = [];
let CUR_BOOK_CODE = null;
let CUR_NOTES = [];
let KIND_FILTER = '';
let TEXT_FILTER = '';
let CUR_EDITION = '';            // empty = browse-only mode (no toggles)
let DISABLED_NOTE_IDS = new Set(); // set of note_ids disabled in CUR_EDITION

async function init() {
  const r = await fetch('/api/sources');
  const data = await r.json();
  BOOKS = data.books;
  await populateKindFilter();
  await populateEditionPicker();
  renderBookList();
  document.getElementById('book-filter').addEventListener('input', renderBookList);
  document.getElementById('note-filter').addEventListener('input', () => {
    TEXT_FILTER = document.getElementById('note-filter').value.toLowerCase();
    renderNotes();
  });
  document.getElementById('kind-filter').addEventListener('change', () => {
    KIND_FILTER = document.getElementById('kind-filter').value;
    renderNotes();
  });
  document.getElementById('edition-picker').addEventListener('change', async () => {
    CUR_EDITION = document.getElementById('edition-picker').value;
    await reloadDisabledSet();
    renderNotes();
  });
}

async function populateEditionPicker() {
  try {
    const r = await fetch('/api/customize');
    const data = await r.json();
    const sel = document.getElementById('edition-picker');
    for (const e of (data.editions || [])) {
      const o = document.createElement('option');
      o.value = e.id;
      o.textContent = e.short_title || e.title || e.id;
      sel.appendChild(o);
    }
  } catch (e) { /* non-fatal */ }
}

async function reloadDisabledSet() {
  DISABLED_NOTE_IDS = new Set();
  if (!CUR_EDITION) return;
  try {
    const r = await fetch(`/api/edition/${encodeURIComponent(CUR_EDITION)}/disabled-notes`);
    const data = await r.json();
    if (data.disabled_note_ids) {
      DISABLED_NOTE_IDS = new Set(data.disabled_note_ids);
    }
  } catch (e) { /* non-fatal */ }
}

async function toggleNote(noteId, enabled) {
  if (!CUR_EDITION) return;
  const r = await fetch(`/api/edition/${encodeURIComponent(CUR_EDITION)}/note-toggle`, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({note_id: noteId, enabled: enabled}),
  });
  const data = await r.json();
  if (data.ok) {
    if (enabled) DISABLED_NOTE_IDS.delete(noteId);
    else DISABLED_NOTE_IDS.add(noteId);
    return true;
  } else {
    alert(`Toggle failed: ${data.error || 'unknown error'}`);
    return false;
  }
}

async function populateKindFilter() {
  // Use the matrix endpoint we already have to get the kind list
  try {
    const r = await fetch('/api/matrix');
    const data = await r.json();
    const sel = document.getElementById('kind-filter');
    const cats = data.categories.sort((a, b) => a.sort_order - b.sort_order);
    for (const c of cats) {
      const og = document.createElement('optgroup');
      og.label = `${c.symbol} ${c.label}`;
      for (const k of data.kinds.filter(k => k.category === c.id)) {
        const o = document.createElement('option');
        o.value = k.code;
        o.textContent = k.code;
        og.appendChild(o);
      }
      sel.appendChild(og);
    }
  } catch (e) { /* non-fatal */ }
}

function renderBookList() {
  const filterText = (document.getElementById('book-filter').value || '').toLowerCase();
  const list = document.getElementById('book-list');
  const filtered = BOOKS.filter(b =>
    !filterText ||
    b.title.toLowerCase().includes(filterText) ||
    b.code.includes(filterText) ||
    (b.abbrev || '').toLowerCase().includes(filterText)
  );
  document.getElementById('book-count').textContent =
    `${filtered.length} books · ${filtered.reduce((s, b) => s + b.note_count, 0)} notes`;

  // Group by section so the order matches canonical reading order
  const sections = [];
  const seen = new Set();
  for (const b of filtered) {
    if (!seen.has(b.section)) {
      seen.add(b.section);
      sections.push(b.section);
    }
  }
  list.innerHTML = sections.map(s => `
    <div class="border-t border-slate-100 first:border-t-0">
      <div class="px-3 py-1 text-xs uppercase tracking-wide text-slate-400 bg-slate-50">${s || 'misc'}</div>
      ${filtered.filter(b => b.section === s).map(b => `
        <div class="book-row px-3 py-1.5 flex justify-between items-center ${b.code === CUR_BOOK_CODE ? 'active' : ''}"
             data-book="${b.code}">
          <span>${b.title}</span>
          <span class="text-xs ${b.note_count === 0 ? 'text-slate-300' : 'text-slate-500'} font-mono">
            ${b.note_count}
          </span>
        </div>
      `).join('')}
    </div>
  `).join('');

  list.querySelectorAll('.book-row').forEach(el => {
    el.addEventListener('click', () => loadBook(el.dataset.book));
  });
}

async function loadBook(code) {
  CUR_BOOK_CODE = code;
  TEXT_FILTER = '';
  document.getElementById('note-filter').value = '';
  renderBookList();  // rerender so active highlight moves

  const area = document.getElementById('notes-area');
  area.innerHTML = '<div class="text-slate-400">loading …</div>';

  await reloadDisabledSet();

  const r = await fetch(`/api/sources/${encodeURIComponent(code)}`);
  const data = await r.json();
  if (data.error) {
    area.innerHTML = `<div class="text-red-600">${data.error}</div>`;
    return;
  }
  CUR_NOTES = data.notes;
  document.getElementById('book-title').textContent = data.title;
  document.getElementById('book-subtitle').textContent =
    `${data.notes.length} note(s) across ${data.ch_count} chapter(s) · listed in canonical order`;
  renderNotes();
}

function renderNotes() {
  const area = document.getElementById('notes-area');
  if (!CUR_NOTES.length) {
    area.innerHTML = `<div class="text-slate-400">no notes for this book yet — this book has 0 notes attributed.</div>`;
    return;
  }
  let filtered = CUR_NOTES;
  if (KIND_FILTER) filtered = filtered.filter(n => n.kind === KIND_FILTER);
  if (TEXT_FILTER) {
    filtered = filtered.filter(n =>
      (n.title || '').toLowerCase().includes(TEXT_FILTER) ||
      (n.body || '').toLowerCase().includes(TEXT_FILTER) ||
      (n.attribution || '').toLowerCase().includes(TEXT_FILTER) ||
      (n.kind || '').toLowerCase().includes(TEXT_FILTER)
    );
  }
  if (!filtered.length) {
    area.innerHTML = `<div class="text-slate-400">no notes match your filters.</div>`;
    return;
  }

  // Group by chapter for visual scan
  const byChapter = {};
  for (const n of filtered) {
    (byChapter[n.chapter] = byChapter[n.chapter] || []).push(n);
  }
  const chapters = Object.keys(byChapter).map(Number).sort((a, b) => a - b);

  // Banner if in edition-mode
  const editing = !!CUR_EDITION;
  const editBanner = editing
    ? `<div class="mb-3 px-3 py-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-900">
         <strong>Editing mode:</strong> tick / untick each note to include or exclude it from the
         <code class="font-mono">${escapeHTML(CUR_EDITION)}</code> edition. Changes save automatically.
         ${DISABLED_NOTE_IDS.size > 0 ? `<span class="ml-2 text-blue-700">${DISABLED_NOTE_IDS.size} note(s) currently disabled</span>` : ''}
       </div>`
    : `<div class="mb-3 px-3 py-2 bg-slate-50 border border-slate-200 rounded text-xs text-slate-600">
         <strong>Browse-only:</strong> pick an edition above to enable per-note toggles.
       </div>`;

  area.innerHTML = editBanner + chapters.map(ch => `
    <section class="mb-6">
      <h3 class="font-semibold text-slate-700 mb-2 sticky top-0 bg-white py-1 border-b border-slate-100">
        Chapter ${ch} <span class="text-xs text-slate-400 ml-2">${byChapter[ch].length} note(s)</span>
      </h3>
      <ul class="space-y-3">
        ${byChapter[ch].map(n => {
          const isDisabled = DISABLED_NOTE_IDS.has(n.note_id);
          const dimClass = isDisabled ? 'opacity-50 line-through' : '';
          const checkboxHTML = editing
            ? `<input type="checkbox" data-note-id="${escapeAttr(n.note_id)}" ${isDisabled ? '' : 'checked'} class="note-toggle mt-1 mr-2 cursor-pointer">`
            : '';
          return `
          <li class="border-l-4 border-slate-200 pl-3 py-1 flex items-start">
            ${checkboxHTML}
            <div class="flex-1 ${dimClass}">
              <div class="flex items-baseline justify-between gap-2 flex-wrap">
                <div class="flex items-baseline gap-2 flex-wrap">
                  <span class="verse-anchor text-xs text-slate-500">${n.chapter}:${n.verse}${n.suffix || ''}${n.anchor ? ` ${n.anchor}` : ''}</span>
                  <span class="symbol" title="${n.category_label}">${n.category_symbol}</span>
                  <span class="text-xs px-1.5 py-0.5 bg-slate-100 rounded font-mono">${n.kind}</span>
                  ${n.title && n.title !== 'Note' ? `<span class="text-sm font-medium">${escapeHTML(n.title)}</span>` : ''}
                </div>
              </div>
              <div class="text-sm text-slate-700 mt-1">${truncateHTML(n.body, 240)}</div>
              ${n.attribution ? `<div class="text-xs text-slate-500 mt-1"><span class="text-slate-400">source:</span> ${escapeHTML(n.attribution)}</div>` : '<div class="text-xs text-amber-600 mt-1">⚠ no attribution</div>'}
            </div>
          </li>
        `}).join('')}
      </ul>
    </section>
  `).join('');

  // Wire checkbox handlers for per-note toggle (Phase ρ.2)
  area.querySelectorAll('.note-toggle').forEach(cb => {
    cb.addEventListener('change', async (ev) => {
      const noteId = cb.dataset.noteId;
      const enabled = cb.checked;
      cb.disabled = true;
      const ok = await toggleNote(noteId, enabled);
      cb.disabled = false;
      if (!ok) {
        cb.checked = !enabled;  // revert
      } else {
        // Re-render so the strikethrough updates
        renderNotes();
      }
    });
  });
}

function escapeAttr(s) { return escapeHTML(s); }

function escapeHTML(s) {
  return (s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function truncateHTML(html, n) {
  // Strip tags for the preview length calc, but allow a few semantic tags
  const stripped = (html || '').replace(/<[^>]+>/g, '');
  if (stripped.length <= n) return html;
  return escapeHTML(stripped.slice(0, n)) + '<span class="text-slate-400">…</span>';
}

init().catch(e => {
  document.getElementById('book-list').innerHTML = `<div class="text-red-600 p-4">${e.message}</div>`;
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

"""HTML for /sources console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import SOURCES_HTML` callers.

ψ.15 editor-console polish (2026-05-09): cross-link nav substituted
from `_design.HEADER_NAV_LINKS("/sources")` and `BUYER_ARC_POLISH_CSS`
inlined from `_design`, mirroring the ψ.14 buyer-arc pattern.
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
    apply_design_system,
)

__all__ = ["SOURCES_HTML", "HEADER_NAV_LINKS", "BUYER_ARC_POLISH_CSS"]

SOURCES_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>YHWH Ya' Way · Sources Navigator</title>
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
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Sources Navigator</h1>
    <p class="text-xs text-slate-500">browse every note by book/chapter — verify what each edition will claim, and where each claim is sourced</p>
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


<!-- Phase υ.1 — Public-domain source cache management.
     Sits above the per-book navigator. Reads /api/sources/cache for
     status; uses POST/DELETE on the same path family to fetch / clear
     / upload pre-built JSON. Schema source-of-truth is
     content/sources/_fetchers.json (υ.7). -->
<section class="max-w-7xl mx-auto px-6 pt-6">
  <details id="pd-cache-section" class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden" open>
    <summary class="px-4 py-3 border-b border-slate-200 flex items-center justify-between cursor-pointer select-none">
      <div>
        <h2 class="font-semibold text-base">Public-domain source cache</h2>
        <div class="text-xs text-slate-500">files in <code>content/sources/</code> the detectors read from — fetch, upload, or clear them here</div>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <button id="pd-fetch-all" type="button"
          class="text-sm px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">
          Fetch all
        </button>
        <button id="pd-fetch-all-force" type="button"
          class="text-sm px-3 py-1.5 rounded border border-slate-300 hover:bg-slate-50 disabled:opacity-50"
          title="Re-fetch every source even if cached (use after upstream updates)">
          Force re-fetch all
        </button>
      </div>
    </summary>
    <div id="pd-cache-status" class="text-xs text-slate-500 px-4 py-2 border-b border-slate-100">loading…</div>
    <div id="pd-cache-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 p-4"></div>
  </details>
</section>

<!-- υ.3 — Cross-edition note search. Sits between the PD source
     cache and the per-book navigator. Composes /api/search-notes
     (which composes scripts.core.note_search.search_notes — itself
     a thin wrapper over notes_io.load_notes' mtime-cached reads). -->
<section class="max-w-7xl mx-auto px-6 pt-6">
  <details id="ups3-search-section" class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
    <summary class="px-4 py-3 border-b border-slate-200 flex items-center justify-between cursor-pointer select-none">
      <div>
        <h2 class="font-semibold text-base">Search across editions</h2>
        <div class="text-xs text-slate-500">grep every note's label / title / kind / body / attribution — replaces the on-disk grep workflow</div>
      </div>
      <span id="ups3-result-count" class="text-xs text-slate-500 tabular-nums whitespace-nowrap"></span>
    </summary>
    <div class="p-4 space-y-3">
      <div class="flex items-center gap-2 flex-wrap">
        <input id="ups3-query" type="search"
          placeholder="Search every note (label, title, kind, body, attribution)…"
          class="flex-1 min-w-[18rem] border border-slate-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
          autocomplete="off" spellcheck="false" maxlength="500">
        <select id="ups3-edition-filter" class="text-sm border border-slate-300 rounded px-2 py-1.5"
          title="Restrict matches to kinds enabled in this edition (and its canon books)">
          <option value="">all editions</option>
        </select>
        <select id="ups3-kind-filter" class="text-sm border border-slate-300 rounded px-2 py-1.5"
          title="Restrict to one kind code">
          <option value="">all kinds</option>
        </select>
        <select id="ups3-book-filter" class="text-sm border border-slate-300 rounded px-2 py-1.5"
          title="Restrict to one book">
          <option value="">all books</option>
        </select>
        <button type="button" id="ups3-clear" class="hidden text-xs text-blue-600 hover:underline">clear</button>
      </div>
      <div id="ups3-results" class="text-sm text-slate-500">
        Type a query above to search every note across the corpus. Results rank
        label / title matches above body matches.
      </div>
    </div>
  </details>
</section>

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
  setupCrossEditionSearch();  // υ.3
}

// υ.3 — Cross-edition note search. Debounced fetch on input;
// populates the filter dropdowns from /api/customize + /api/matrix
// + /api/sources. Empty query → empty results panel + "type to
// search" placeholder restored. Click a result → loads the book
// and scrolls into the per-book panel.
let UPS3_DEBOUNCE = null;
async function setupCrossEditionSearch() {
  const q = document.getElementById('ups3-query');
  const ed = document.getElementById('ups3-edition-filter');
  const kf = document.getElementById('ups3-kind-filter');
  const bf = document.getElementById('ups3-book-filter');
  const clearBtn = document.getElementById('ups3-clear');
  if (!q) return;
  // Populate filter dropdowns. Editions reuse /api/customize (already
  // fetched once for the per-book editor); kinds reuse the matrix
  // dropdown shape so codes match; books come from /api/sources we
  // already fetched in `init`.
  try {
    const cr = await fetch('/api/customize');
    const cd = await cr.json();
    for (const e of (cd.editions || [])) {
      const o = document.createElement('option');
      o.value = e.id;
      o.textContent = e.short_title || e.title || e.id;
      ed.appendChild(o);
    }
  } catch (e) { /* non-fatal */ }
  try {
    const mr = await fetch('/api/matrix');
    const md = await mr.json();
    const cats = (md.categories || []).slice().sort((a, b) => a.sort_order - b.sort_order);
    for (const c of cats) {
      const og = document.createElement('optgroup');
      og.label = `${c.symbol} ${c.label}`;
      for (const k of (md.kinds || []).filter(k => k.category === c.id)) {
        const o = document.createElement('option');
        o.value = k.code;
        o.textContent = k.code;
        og.appendChild(o);
      }
      kf.appendChild(og);
    }
  } catch (e) { /* non-fatal */ }
  for (const b of BOOKS) {
    const o = document.createElement('option');
    o.value = b.code;
    o.textContent = `${b.title} (${b.code})`;
    bf.appendChild(o);
  }

  const trigger = () => {
    if (UPS3_DEBOUNCE) clearTimeout(UPS3_DEBOUNCE);
    UPS3_DEBOUNCE = setTimeout(runCrossEditionSearch, 200);
  };
  q.addEventListener('input', trigger);
  q.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      q.value = '';
      runCrossEditionSearch();
      q.blur();
    }
  });
  ed.addEventListener('change', trigger);
  kf.addEventListener('change', trigger);
  bf.addEventListener('change', trigger);
  if (clearBtn) clearBtn.addEventListener('click', () => {
    q.value = '';
    ed.value = '';
    kf.value = '';
    bf.value = '';
    runCrossEditionSearch();
    q.focus();
  });
}

async function runCrossEditionSearch() {
  const q = document.getElementById('ups3-query');
  const ed = document.getElementById('ups3-edition-filter');
  const kf = document.getElementById('ups3-kind-filter');
  const bf = document.getElementById('ups3-book-filter');
  const out = document.getElementById('ups3-results');
  const count = document.getElementById('ups3-result-count');
  const clearBtn = document.getElementById('ups3-clear');
  const query = (q.value || '').trim();
  // Show clear button whenever any field has content.
  const hasAny = !!(query || ed.value || kf.value || bf.value);
  if (clearBtn) clearBtn.classList.toggle('hidden', !hasAny);
  if (!query) {
    if (count) count.textContent = '';
    out.innerHTML = `<div class="text-slate-400">Type a query above to search every note across the corpus. Results rank label / title matches above body matches.</div>`;
    return;
  }
  out.innerHTML = `<div class="text-slate-400">searching …</div>`;
  const params = new URLSearchParams();
  params.set('q', query);
  if (ed.value) params.set('edition_id', ed.value);
  if (kf.value) params.set('kind', kf.value);
  if (bf.value) params.set('book', bf.value);
  params.set('limit', '100');
  let data;
  try {
    const r = await fetch(`/api/search-notes?${params.toString()}`);
    data = await r.json();
  } catch (e) {
    out.innerHTML = `<div class="text-red-600">search failed: ${e.message}</div>`;
    return;
  }
  if (data.error) {
    out.innerHTML = `<div class="text-red-600">${escapeHTML(data.error)}: ${escapeHTML(data.message || '')}</div>`;
    return;
  }
  const hits = data.hits || [];
  if (count) count.textContent = `${hits.length}${hits.length >= (data.limit || 100) ? '+' : ''} match${hits.length === 1 ? '' : 'es'}`;
  if (hits.length === 0) {
    out.innerHTML = `<div class="text-slate-400">no matches.</div>`;
    return;
  }
  out.innerHTML = hits.map(h => `
    <div class="ups3-hit border-b border-slate-100 py-2 cursor-pointer hover:bg-slate-50 -mx-4 px-4"
         data-book="${escapeHTML(h.book_code)}" data-anchor="${escapeHTML(h.anchor || '')}">
      <div class="flex items-center justify-between gap-2 text-xs">
        <div class="flex items-center gap-2 min-w-0">
          <span class="symbol text-slate-500" title="${escapeHTML(h.category_label)}">${escapeHTML(h.category_symbol)}</span>
          <span class="font-mono text-slate-700">${escapeHTML(h.book_code)} ${h.chapter}:${h.verse}${escapeHTML(h.suffix || '')}</span>
          <span class="text-slate-400 font-mono">${escapeHTML(h.kind)}</span>
          <span class="text-slate-700 truncate">${escapeHTML(h.label || h.title || '')}</span>
        </div>
        <span class="text-slate-400 tabular-nums whitespace-nowrap">score ${h.score}</span>
      </div>
      <div class="text-xs text-slate-500 mt-1">${highlightExcerpt(h.excerpt, query)}</div>
    </div>
  `).join('');
  // Click a result → jump to the book in the per-book navigator.
  out.querySelectorAll('.ups3-hit').forEach(el => {
    el.addEventListener('click', () => {
      const code = el.dataset.book;
      if (code) {
        loadBook(code);
        // Scroll the per-book panel into view.
        const main = document.querySelector('main');
        if (main && main.scrollIntoView) main.scrollIntoView({behavior: 'smooth', block: 'start'});
      }
    });
  });
}

// υ.3 — highlight every (case-insensitive) occurrence of `query` in
// the excerpt without losing the original casing. Uses the existing
// module-level `escapeHTML` defined further below; the two `function`
// declarations are hoisted so order doesn't matter.
function highlightExcerpt(excerpt, query) {
  if (!excerpt) return '';
  const safe = escapeHTML(excerpt);
  if (!query) return safe;
  const q = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return safe.replace(new RegExp(q, 'gi'), m => `<mark>${m}</mark>`);
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

// =====================================================================
// Phase υ.1 — PD source cache management widget
// Self-contained IIFE so it shares no globals with the navigator init()
// above. Reads /api/sources/cache (status grid) and uses POST/DELETE
// against the same path family for actions.
// =====================================================================
(function () {
  const grid = document.getElementById('pd-cache-grid');
  const statusEl = document.getElementById('pd-cache-status');
  const fetchAllBtn = document.getElementById('pd-fetch-all');
  const fetchAllForceBtn = document.getElementById('pd-fetch-all-force');
  if (!grid || !statusEl) return;

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
    })[c]);
  }

  function setBusy(busy, msg) {
    fetchAllBtn.disabled = !!busy;
    fetchAllForceBtn.disabled = !!busy;
    statusEl.textContent = msg || (busy ? 'working…' : '');
    statusEl.className = busy
      ? 'text-xs text-blue-700 bg-blue-50 px-4 py-2 border-b border-slate-100'
      : 'text-xs text-slate-500 px-4 py-2 border-b border-slate-100';
  }

  function setError(msg) {
    statusEl.textContent = msg;
    statusEl.className = 'text-xs text-red-700 bg-red-50 px-4 py-2 border-b border-slate-100';
  }

  function setOk(msg) {
    statusEl.textContent = msg;
    statusEl.className = 'text-xs text-green-700 bg-green-50 px-4 py-2 border-b border-slate-100';
  }

  function cardHtml(s) {
    const badge = s.required
      ? '<span class="text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 ml-2">required</span>'
      : '<span class="text-xs px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 ml-2">optional</span>';
    const status = s.cached
      ? `<span class="text-green-700">✓ cached</span> <span class="text-slate-500">${s.size_kb} KB · ${(s.mtime_iso||'').replace('T',' ').slice(0,16)}</span>`
      : '<span class="text-amber-700">— not fetched</span>';
    const candList = s.candidates.map(c =>
      `<li class="text-xs text-slate-500 truncate" title="${escapeHtml(c.url)}">
         <span class="text-slate-400">[${escapeHtml(c.parser)}]</span>
         <span class="break-all">${escapeHtml(c.url)}</span>
       </li>`
    ).join('');
    return `
      <div class="border border-slate-200 rounded p-3 flex flex-col gap-2"
           data-source-id="${escapeHtml(s.id)}">
        <div class="flex items-baseline justify-between flex-wrap">
          <h3 class="font-medium text-sm">${escapeHtml(s.name)}${badge}</h3>
        </div>
        <div class="text-xs text-slate-600">${status}</div>
        <div class="text-xs text-slate-400 font-mono">${escapeHtml(s.cache_path)}</div>
        <details class="text-xs">
          <summary class="cursor-pointer text-slate-500 hover:text-slate-700">${s.candidates.length} candidate${s.candidates.length===1?'':'s'}</summary>
          <ul class="mt-1 ml-2 space-y-1">${candList}</ul>
        </details>
        <div class="flex flex-wrap gap-1 mt-1">
          <button type="button" data-action="fetch"
                  class="text-xs px-2 py-1 rounded border border-slate-300 hover:bg-slate-50">
            Fetch
          </button>
          <button type="button" data-action="force-fetch"
                  class="text-xs px-2 py-1 rounded border border-slate-300 hover:bg-slate-50"
                  title="Re-fetch even if cached">
            Force
          </button>
          <label class="text-xs px-2 py-1 rounded border border-slate-300 hover:bg-slate-50 cursor-pointer">
            Upload JSON
            <input type="file" accept=".json,application/json" class="hidden" data-action="upload">
          </label>
          ${s.cached
            ? '<button type="button" data-action="clear" class="text-xs px-2 py-1 rounded border border-slate-300 text-red-700 hover:bg-red-50">Clear</button>'
            : ''}
        </div>
        <div class="text-xs text-slate-500" data-role="row-status"></div>
      </div>
    `;
  }

  async function refresh() {
    try {
      const r = await fetch('/api/sources/cache');
      const data = await r.json();
      if (data.status !== 'ok') {
        setError(data.message || 'failed to load source-cache status');
        grid.innerHTML = '';
        return;
      }
      grid.innerHTML = data.sources.map(cardHtml).join('');
      const cached = data.sources.filter(s => s.cached).length;
      const total = data.sources.length;
      setOk(`${cached} of ${total} sources cached`);
      attachRowHandlers();
    } catch (e) {
      setError('network error: ' + e.message);
    }
  }

  function rowStatus(card, msg, kind) {
    const el = card.querySelector('[data-role="row-status"]');
    if (!el) return;
    el.textContent = msg;
    el.className = 'text-xs ' + (
      kind === 'error' ? 'text-red-700' :
      kind === 'ok'    ? 'text-green-700' :
                         'text-slate-500'
    );
  }

  async function doFetch(card, sourceId, force) {
    rowStatus(card, 'fetching…');
    try {
      const r = await fetch(`/api/sources/cache/${encodeURIComponent(sourceId)}/fetch`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({force}),
      });
      const data = await r.json();
      if (r.ok && data.ok) {
        rowStatus(card, data.message || 'fetched', 'ok');
      } else {
        rowStatus(card, data.message || data.error || 'fetch failed', 'error');
      }
    } catch (e) {
      rowStatus(card, 'network error: ' + e.message, 'error');
    }
    await refresh();
  }

  async function doUpload(card, sourceId, file) {
    if (!file) return;
    rowStatus(card, `uploading ${file.name}…`);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const r = await fetch(`/api/sources/cache/${encodeURIComponent(sourceId)}/upload`, {
        method: 'POST',
        body: fd,
      });
      const data = await r.json();
      if (r.ok && data.ok) {
        rowStatus(card, data.message || 'uploaded', 'ok');
      } else {
        rowStatus(card, data.message || data.error || 'upload failed', 'error');
      }
    } catch (e) {
      rowStatus(card, 'network error: ' + e.message, 'error');
    }
    await refresh();
  }

  async function doClear(card, sourceId) {
    if (!confirm('Clear cached file for this source? A backup is kept under .backups/.')) return;
    rowStatus(card, 'clearing…');
    try {
      const r = await fetch(`/api/sources/cache/${encodeURIComponent(sourceId)}`, {
        method: 'DELETE',
      });
      const data = await r.json();
      if (r.ok && data.ok) {
        rowStatus(card, data.message || 'cleared', 'ok');
      } else {
        rowStatus(card, data.message || data.error || 'clear failed', 'error');
      }
    } catch (e) {
      rowStatus(card, 'network error: ' + e.message, 'error');
    }
    await refresh();
  }

  function attachRowHandlers() {
    grid.querySelectorAll('[data-source-id]').forEach(card => {
      const sid = card.getAttribute('data-source-id');
      card.querySelectorAll('button[data-action]').forEach(btn => {
        const action = btn.getAttribute('data-action');
        btn.addEventListener('click', () => {
          if (action === 'fetch')        doFetch(card, sid, false);
          else if (action === 'force-fetch') doFetch(card, sid, true);
          else if (action === 'clear')   doClear(card, sid);
        });
      });
      const fileInput = card.querySelector('input[type="file"]');
      if (fileInput) {
        fileInput.addEventListener('change', e => {
          const file = e.target.files && e.target.files[0];
          if (file) doUpload(card, sid, file);
          e.target.value = '';
        });
      }
    });
  }

  async function fetchAll(force) {
    setBusy(true, force ? 're-fetching all sources…' : 'fetching missing sources…');
    try {
      const r = await fetch('/api/sources/cache/_all/fetch', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({force}),
      });
      const data = await r.json();
      if (r.ok && data.ok) {
        setOk(`fetched ${data.results.filter(x=>x.ok).length} of ${data.results.length} sources`);
      } else {
        const fails = (data.results||[]).filter(x=>!x.ok).map(x=>x.id).join(', ');
        setError(`some sources failed: ${fails || (data.message||'unknown')}`);
      }
    } catch (e) {
      setError('network error: ' + e.message);
    }
    setBusy(false);
    await refresh();
  }

  fetchAllBtn.addEventListener('click', () => fetchAll(false));
  fetchAllForceBtn.addEventListener('click', () => fetchAll(true));

  refresh();
})();
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
SOURCES_HTML = apply_design_system(SOURCES_HTML, "/sources")

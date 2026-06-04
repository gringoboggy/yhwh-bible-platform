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
let CUR_VERSE = null;     // verse number, null = no verse focused (chapter level)
let OVERVIEW = null;      // cached /api/build-my-bible/<ed> payload
let BOOKS = [];           // books_canonical (already in §6.1 order — never sort)

// ---- lazy per-level caches ------------------------------------------
// Fetched book / chapter payloads are cached so re-visiting a level
// never refetches. Cleared on edition change (see onEditionChange). The
// edition overview itself is cached in OVERVIEW. Keys: book code for the
// book cache; "<book>:<ch>" for the chapter cache.
let BOOK_CACHE = new Map();    // book code -> /api/build-my-bible/<ed>/<book>
let CHAPTER_CACHE = new Map(); // "<book>:<ch>" -> /…/<book>/<ch>

// Title-lookup helpers — resolve a book code to its display title from
// the cached overview, so breadcrumbs read "Bible ▸ Genesis" not a code.
function bookTitle(code) {
  const b = BOOKS.find(x => x.code === code);
  return b ? b.title : code;
}

// Convenience alias for the shared ω.0.7 escaper (always present from the
// UI-defense prelude; the fallback keeps a stale tab from crashing).
function esc(s) {
  return window.escapeHtml ? window.escapeHtml(s) : String(s == null ? '' : s);
}

// ---- category / popup-language label lookups ------------------------
// Built once per edition from OVERVIEW so the read-only SYMBOLS / POPUPS
// sections can show human labels + symbols beside resolved on/off state.
// C2-4 reuses these maps to drive the interactive tri-state controls.
function categoriesOrdered() {
  // OVERVIEW.categories already arrives sorted by sort_order — never re-sort.
  return (OVERVIEW && OVERVIEW.categories) || [];
}
function popupLangLabel(id) {
  const langs = (OVERVIEW && OVERVIEW.popup_languages) || [];
  const l = langs.find(x => x.id === id);
  return l ? l.label : id;
}

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

// ---- spinner / small UI affordances ---------------------------------
// Mirror sources.py's loading affordance — a neutral "loading …" line
// painted into a target node while a level is being fetched.
function spinnerInto(el, label) {
  if (!el) return;
  el.innerHTML = '<div class="text-slate-400 px-1 py-2">' + esc(label || 'loading …') + '</div>';
}

// On/off badge for a resolved symbol category. Read-only display.
function symbolBadge(state) {
  return state === 'on'
    ? '<span class="text-xs px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 font-medium">on</span>'
    : '<span class="text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-400">off</span>';
}

// ---- breadcrumb ------------------------------------------------------
// Bible ▸ Genesis ▸ Chapter 3 ▸ Verse 5 — every segment up to (but not
// including) the current level is a clickable .crumb-link that pops back
// up to that level. The active (deepest) segment is plain text.
function renderBreadcrumb() {
  const el = document.getElementById('breadcrumb');
  if (!el) return;
  if (!CUR_EDITION) {
    el.innerHTML = '<span class="text-slate-400">pick an edition to begin</span>';
    return;
  }
  // Build the segment list. Each entry: {label, level} where level is the
  // navigation target a click should restore.
  const segs = [];
  segs.push({ label: 'Bible', level: 'bible' });
  if (CUR_BOOK) segs.push({ label: bookTitle(CUR_BOOK), level: 'book' });
  if (CUR_CHAPTER != null) segs.push({ label: 'Chapter ' + CUR_CHAPTER, level: 'chapter' });
  if (CUR_VERSE != null) segs.push({ label: 'Verse ' + CUR_VERSE, level: 'verse' });

  const parts = [];
  segs.forEach((s, i) => {
    const isLast = i === segs.length - 1;
    if (i > 0) parts.push('<span class="text-slate-300 px-0.5">▸</span>');
    if (isLast) {
      parts.push('<span class="text-slate-700 font-medium">' + esc(s.label) + '</span>');
    } else {
      parts.push(
        '<span class="crumb-link text-blue-600" data-level="' + esc(s.level) + '">' +
        esc(s.label) + '</span>'
      );
    }
  });
  el.innerHTML = parts.join('');
  el.querySelectorAll('.crumb-link').forEach(seg => {
    seg.addEventListener('click', () => goToLevel(seg.dataset.level));
  });
}

// Pop back up to a named level (clicking a breadcrumb segment).
function goToLevel(level) {
  if (level === 'bible') {
    CUR_BOOK = null; CUR_CHAPTER = null; CUR_VERSE = null;
    renderBreadcrumb(); renderBookList(); renderLevelPanel();
  } else if (level === 'book') {
    CUR_CHAPTER = null; CUR_VERSE = null;
    navToBook(CUR_BOOK);
  } else if (level === 'chapter') {
    CUR_VERSE = null;
    navToChapter(CUR_CHAPTER);
  }
  // 'verse' is the deepest level — its crumb is never a link.
}

// ---- left book rail --------------------------------------------------
// Renders BOOKS in canonical order (§6.1 — never client-sort). The
// filter box narrows by title / code without reordering. Clicking a book
// drills into the book (chapter) level.
function renderBookList() {
  const el = document.getElementById('book-list');
  if (!el) return;
  if (!CUR_EDITION) {
    el.innerHTML = '<div class="text-slate-400 px-3 py-2">pick an edition above …</div>';
    document.getElementById('book-count').textContent = '';
    return;
  }
  const filterText = (document.getElementById('book-filter').value || '').toLowerCase();
  const filtered = BOOKS.filter(b =>
    !filterText ||
    (b.title || '').toLowerCase().includes(filterText) ||
    (b.code || '').toLowerCase().includes(filterText)
  );
  document.getElementById('book-count').textContent =
    filtered.length + ' of ' + BOOKS.length + ' books';

  // Canonical order preserved — BOOKS arrives ordered; .filter keeps it.
  el.innerHTML = filtered.map(b => `
    <div class="book-row px-3 py-1.5 flex justify-between items-center ${b.code === CUR_BOOK ? 'active' : ''}"
         data-book="${esc(b.code)}">
      <span>${esc(b.title)}</span>
      <span class="text-xs text-slate-400 font-mono">${b.ch_count} ch</span>
    </div>
  `).join('');
  el.querySelectorAll('.book-row').forEach(row => {
    row.addEventListener('click', () => navToBook(row.dataset.book));
  });
}

// ---- right level panel ----------------------------------------------
// Dispatches to the level-specific renderer based on the current
// drill-down depth. Each renderer paints read-only resolved state into
// fixed-id section containers so C2-4 / C2-5 can swap displays for
// interactive controls without restructuring.
function renderLevelPanel() {
  const el = document.getElementById('level-panel');
  if (!el) return;
  if (!CUR_EDITION) {
    setLevelHeader('No edition selected', '');
    el.innerHTML = '<div class="text-slate-400">Pick an edition above to start building.</div>';
    return;
  }
  if (CUR_BOOK == null) {
    renderBiblePanel(el);
  } else if (CUR_CHAPTER == null) {
    renderBookPanel(el);
  } else {
    renderChapterPanel(el);
  }
}

function setLevelHeader(title, subtitle) {
  const t = document.getElementById('level-title');
  const s = document.getElementById('level-subtitle');
  if (t) t.textContent = title;
  if (s) s.textContent = subtitle || '';
}

// ---- Bible-level panel ----------------------------------------------
// SYMBOLS section (resolved on/off per category) + POPUPS section
// (resolved popup-language list). Read-only — C2-4 makes these the
// interactive tri-state + checklist controls.
function renderBiblePanel(el) {
  const ed = (OVERVIEW && OVERVIEW.edition) || {};
  setLevelHeader(ed.title || CUR_EDITION,
    BOOKS.length + ' book(s) in this edition · pick a book on the left to drill in');
  const resolved = (OVERVIEW && OVERVIEW.resolved_bible) || { symbols: {}, popups: [] };
  el.innerHTML =
    renderSymbolsSection(resolved.symbols, 'Bible') +
    renderPopupsSection(resolved.popups, 'Bible');
}

// SYMBOLS section — one row per category with its symbol, label, and a
// resolved on/off badge. Stable ids/classes so C2-4 can upgrade in place.
/* C2-4 makes this interactive (tri-state inherit/on/off per category) */
function renderSymbolsSection(symbols, scopeLabel) {
  symbols = symbols || {};
  const rows = categoriesOrdered().map(c => {
    const state = symbols[c.id] || 'off';
    return `
      <div class="sym-row flex items-center justify-between gap-3 py-1.5 border-b border-slate-50"
           data-category="${esc(c.id)}" data-state="${esc(state)}">
        <div class="flex items-center gap-2 min-w-0">
          <span class="symbol text-slate-600" title="${esc(c.description || c.label)}">${esc(c.symbol)}</span>
          <span class="text-sm text-slate-700 truncate">${esc(c.label)}</span>
        </div>
        ${symbolBadge(state)}
      </div>`;
  }).join('');
  return `
    <section id="symbols-section" class="mb-6" data-scope="${esc(scopeLabel)}">
      <h3 class="font-semibold text-slate-700 mb-1">Note symbols</h3>
      <p class="text-xs text-slate-400 mb-2">resolved on/off per symbol family at the ${esc(scopeLabel)} level (read-only)</p>
      ${rows || '<div class="text-slate-400 text-sm">no categories</div>'}
    </section>`;
}

// POPUPS section — the resolved popup-language list as read-only chips.
/* C2-4 makes this interactive (per-language checklist) */
function renderPopupsSection(popups, scopeLabel) {
  popups = popups || [];
  const chips = popups.length
    ? popups.map(id => `
        <span class="popup-chip text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700"
              data-lang="${esc(id)}">${esc(popupLangLabel(id))}</span>`).join('')
    : '<span class="text-slate-400 text-sm">none</span>';
  return `
    <section id="popups-section" class="mb-2" data-scope="${esc(scopeLabel)}">
      <h3 class="font-semibold text-slate-700 mb-1">Popup languages</h3>
      <p class="text-xs text-slate-400 mb-2">translation-popup languages resolved at the ${esc(scopeLabel)} level (read-only)</p>
      <div class="flex flex-wrap gap-1.5">${chips}</div>
    </section>`;
}

// ---- Book-level panel -----------------------------------------------
// Book title + chapter list. Each chapter is clickable (drills to the
// chapter level), shows a "has notes" indicator + its resolved symbol /
// popup badges. Chapters render 1..ch_count ascending (never sort).
function renderBookPanel(el) {
  const payload = BOOK_CACHE.get(CUR_BOOK);
  if (!payload) { spinnerInto(el, 'loading book …'); return; }
  const book = payload.book || {};
  const chapters = payload.chapters || [];
  setLevelHeader(book.title || CUR_BOOK,
    book.ch_count + ' chapter(s) · pick a chapter to see its verses');

  const grid = chapters.map(ch => {
    const symsOn = countSymbolsOn(ch.resolved && ch.resolved.symbols);
    const popN = (ch.resolved && ch.resolved.popups ? ch.resolved.popups.length : 0);
    const dot = ch.has_notes
      ? '<span class="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500" title="has notes"></span>'
      : '<span class="inline-block w-1.5 h-1.5 rounded-full bg-slate-200" title="no notes"></span>';
    return `
      <button type="button"
        class="chapter-cell text-left border border-slate-200 rounded px-2.5 py-1.5 hover:bg-slate-50 flex flex-col gap-1"
        data-chapter="${ch.num}">
        <div class="flex items-center justify-between">
          <span class="font-medium text-sm">Ch ${ch.num}</span>
          ${dot}
        </div>
        <div class="text-xs text-slate-400 tabular-nums">${symsOn} sym · ${popN} popup</div>
      </button>`;
  }).join('');

  el.innerHTML = `
    <section class="mb-2">
      <p class="text-xs text-slate-400 mb-2">a filled dot marks chapters with notes; counts show resolved symbol families on + popup languages</p>
      <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2">${grid}</div>
    </section>`;
  el.querySelectorAll('.chapter-cell').forEach(cell => {
    cell.addEventListener('click', () => navToChapter(Number(cell.dataset.chapter)));
  });
}

function countSymbolsOn(symbols) {
  if (!symbols) return 0;
  return Object.values(symbols).filter(v => v === 'on').length;
}

// ---- Chapter-level panel --------------------------------------------
// Verse list (1..N ascending). Each verse shows its resolved symbols /
// popups summary and its notes as a read-only list (symbol + kind +
// title, with a faint marker if disabled / forced_on). Clicking a verse
// focuses it (the individual level) — its notes expand, breadcrumb adds
// "Verse N". No writable controls here (those land in C2-5).
function renderChapterPanel(el) {
  const key = CUR_BOOK + ':' + CUR_CHAPTER;
  const payload = CHAPTER_CACHE.get(key);
  if (!payload) { spinnerInto(el, 'loading chapter …'); return; }
  const verses = payload.verses || [];
  const noteTotal = verses.reduce((s, v) => s + (v.notes ? v.notes.length : 0), 0);
  setLevelHeader(bookTitle(CUR_BOOK) + ' ' + CUR_CHAPTER,
    verses.length + ' verse(s) · ' + noteTotal + ' note(s) · click a verse to focus its notes');

  el.innerHTML = `
    <section id="verse-list-section">
      <ul class="space-y-2">
        ${verses.map(v => renderVerseRow(v)).join('')}
      </ul>
    </section>`;
  el.querySelectorAll('.verse-row').forEach(row => {
    row.querySelector('.verse-head').addEventListener('click', () => {
      const vs = Number(row.dataset.verse);
      // Toggle focus: clicking the focused verse collapses it again.
      CUR_VERSE = (CUR_VERSE === vs) ? null : vs;
      renderBreadcrumb();
      renderChapterPanel(el);
    });
  });
}

// One verse row. When focused (CUR_VERSE === v.vs) its notes expand to
// the individual level; otherwise a compact summary line.
function renderVerseRow(v) {
  const focused = CUR_VERSE === v.vs;
  const resolved = v.resolved || { symbols: {}, popups: [] };
  const symsOn = countSymbolsOn(resolved.symbols);
  const popN = (resolved.popups || []).length;
  const notes = v.notes || [];
  const head = `
    <div class="verse-head cursor-pointer flex items-center justify-between gap-2 px-2 py-1 rounded hover:bg-slate-50 ${focused ? 'bg-slate-50' : ''}">
      <div class="flex items-center gap-2 min-w-0">
        <span class="verse-anchor text-xs ${focused ? 'text-blue-700 font-semibold' : 'text-slate-500'}">${CUR_CHAPTER}:${v.vs}</span>
        ${notes.length
          ? `<span class="text-xs px-1.5 py-0.5 bg-slate-100 rounded font-mono text-slate-600">${notes.length} note${notes.length === 1 ? '' : 's'}</span>`
          : '<span class="text-xs text-slate-300">no notes</span>'}
      </div>
      <span class="text-xs text-slate-400 tabular-nums whitespace-nowrap">${symsOn} sym · ${popN} popup</span>
    </div>`;

  // Notes list — read-only at the individual level. C2-5 adds the
  // per-note disable / force-on checkboxes here.
  /* C2-5 makes this interactive (per-note disable / force-on) */
  let body = '';
  if (focused) {
    body = notes.length
      ? `<ul class="mt-1 ml-4 space-y-1 border-l-2 border-slate-100 pl-3">
           ${notes.map(n => renderNoteLine(n)).join('')}
         </ul>`
      : '<div class="mt-1 ml-4 text-xs text-slate-400">no notes attributed to this verse.</div>';
  }
  return `<li class="verse-row" data-verse="${v.vs}">${head}${body}</li>`;
}

// One read-only note line: symbol + kind + title, faint marker if the
// note is disabled or forced-on in this edition. C2-5 swaps the marker
// area for the writable checkboxes.
function renderNoteLine(n) {
  const stateMark = n.disabled
    ? '<span class="text-xs text-amber-600 ml-1" title="disabled in this edition">(disabled)</span>'
    : (n.forced_on
        ? '<span class="text-xs text-emerald-600 ml-1" title="forced on in this edition">(forced on)</span>'
        : '');
  const dim = n.disabled ? 'opacity-50' : '';
  return `
    <li class="note-line flex items-start gap-2 ${dim}" data-note-id="${esc(n.note_id)}">
      <span class="symbol text-slate-500" title="${esc(n.category)}">${esc(n.symbol)}</span>
      <span class="text-xs px-1.5 py-0.5 bg-slate-100 rounded font-mono text-slate-600">${esc(n.kind)}</span>
      <span class="text-sm text-slate-700 flex-1 min-w-0">${esc(n.title || 'Note')}${stateMark}</span>
    </li>`;
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

// Edition select → load + cache the overview, reset the drill-down to
// the Bible level, clear the per-level caches, repaint all three panels.
async function onEditionChange() {
  const sel = document.getElementById('edition-picker');
  CUR_EDITION = sel ? sel.value : '';
  CUR_BOOK = null;
  CUR_CHAPTER = null;
  CUR_VERSE = null;
  OVERVIEW = null;
  BOOKS = [];
  BOOK_CACHE = new Map();
  CHAPTER_CACHE = new Map();

  if (!CUR_EDITION) {
    renderBreadcrumb();
    renderBookList();
    renderLevelPanel();
    return;
  }

  // Spinners while the overview loads.
  spinnerInto(document.getElementById('book-list'), 'loading books …');
  spinnerInto(document.getElementById('level-panel'), 'loading edition …');
  renderBreadcrumb();

  try {
    OVERVIEW = await fetchOverview(CUR_EDITION);
  } catch (e) {
    // banner already shown by safeFetch; reset to a clean empty state
    CUR_EDITION = '';
    OVERVIEW = null;
    renderBreadcrumb();
    renderBookList();
    renderLevelPanel();
    return;
  }
  BOOKS = (OVERVIEW && OVERVIEW.books_canonical) || [];  // already §6.1-ordered
  renderBreadcrumb();
  renderBookList();
  renderLevelPanel();
}

// ---- drill-down navigation (lazy + cached) ---------------------------

// Navigate to a book (the chapter list). Fetches + caches on first
// visit; re-visits read straight from BOOK_CACHE (no refetch).
async function navToBook(code) {
  if (!code) return;
  const snapEd = CUR_EDITION;  // snapshot before any await
  CUR_BOOK = code;
  CUR_CHAPTER = null;
  CUR_VERSE = null;
  renderBreadcrumb();
  renderBookList();  // move the active highlight

  if (!BOOK_CACHE.has(code)) {
    spinnerInto(document.getElementById('level-panel'), 'loading book …');
    setLevelHeader(bookTitle(code), 'loading …');
    let payload;
    try {
      payload = await fetchBook(snapEd, code);
    } catch (e) {
      renderLevelPanel();  // banner already shown; clear the spinner / restore state
      return;
    }
    // Guard against a stale response if the user clicked away (or switched
    // edition) meanwhile.
    if (CUR_EDITION !== snapEd || CUR_BOOK !== code) return;
    BOOK_CACHE.set(code, payload);
  }
  renderLevelPanel();
}

// Navigate to a chapter (the verse list). Lazy + cached by "book:ch".
async function navToChapter(num) {
  if (num == null) return;
  const snapEd = CUR_EDITION;  // snapshot before any await
  const snapBook = CUR_BOOK;   // so a same-numbered chapter in another book
                               // (clicked mid-fetch) can't clobber this one
  CUR_CHAPTER = num;
  CUR_VERSE = null;
  renderBreadcrumb();

  const key = snapBook + ':' + num;
  if (!CHAPTER_CACHE.has(key)) {
    spinnerInto(document.getElementById('level-panel'), 'loading chapter …');
    setLevelHeader(bookTitle(snapBook) + ' ' + num, 'loading …');
    let payload;
    try {
      payload = await fetchChapter(snapEd, snapBook, num);
    } catch (e) {
      renderLevelPanel();  // banner already shown; clear the spinner / restore state
      return;
    }
    // Guard against a stale response if the user navigated away (or switched
    // book/edition) meanwhile.
    if (CUR_EDITION !== snapEd || CUR_BOOK !== snapBook || CUR_CHAPTER !== num) return;
    CHAPTER_CACHE.set(key, payload);
  }
  renderLevelPanel();
}

// ---- boot ------------------------------------------------------------
async function init() {
  await populateEditionPicker();
  const bf = document.getElementById('book-filter');
  if (bf) bf.addEventListener('input', renderBookList);
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

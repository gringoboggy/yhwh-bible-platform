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
  .book-row:hover { background: #EFE6CE; }
  .book-row.active { background: #E3D4AE; font-weight: 600; }
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
      <!-- C2-4 — autosave status line for the interactive controls. -->
      <div id="bmb-save-status" class="text-xs" role="status" aria-live="polite"></div>
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

// ---- C2-4 working-copy override maps ---------------------------------
// The interactive controls (book/chapter symbol tri-state, book/chapter/
// verse popup checklists) write the EXISTING per-coordinate fields through
// POST/PUT /api/edition-meta/<id> — and that endpoint is ABSOLUTE-REPLACE
// per field: a field present in the payload replaces that ENTIRE map. So a
// single-scope edit must send the WHOLE current map for the touched field
// with one delta applied. We keep an authoritative working copy of every
// override map here (seeded from OVERVIEW.overrides on load / after each
// save), mutate it locally, and POST the full touched maps. On success we
// refetch OVERVIEW to re-seed (authoritative) + invalidate the caches.
//
// Shape per field: { "<key>": ["<value>", ...] } — the decoded dict the
// server validates + re-encodes. Keys: "<book>" / "<book>:<ch>" /
// "<book>:<ch>:<vs>"; symbol values = category-id|kind-code tokens; popup
// values = popup-language ids.
let WORK = null;  // { note_families_on_per_book: {...}, ... } — null = not seeded

// The seven override fields this console can write. The two book-level
// popup absolute-set + the four signed symbol maps + the per-chapter /
// per-verse popup maps. (disabled_note_ids / enabled_note_ids belong to
// C2-5 and are left untouched.)
const WORK_FIELDS = [
  'note_families_on_per_book',
  'note_families_off_per_book',
  'note_families_on_per_chapter',
  'note_families_off_per_chapter',
  'popup_languages_per_book',
  'popup_languages_per_chapter',
  'popup_languages_per_verse',
];

// (Re)build WORK as a deep clone of OVERVIEW.overrides so local edits never
// mutate the cached server payload. Called on edition load + after a save's
// refetch. Missing fields default to {} (a no-override edition).
function seedWorkFromOverview(preserve) {
  const ov = (OVERVIEW && OVERVIEW.overrides) || {};
  const prev = WORK || {};
  WORK = {};
  for (const f of WORK_FIELDS) {
    if (preserve && preserve.has && preserve.has(f) && prev[f]) {
      // A toggle landed in this field while a save was in flight — keep the
      // client mutation rather than clobbering it with the pre-toggle server state.
      WORK[f] = prev[f];
      continue;
    }
    const m = ov[f] || {};
    const clone = {};
    for (const k of Object.keys(m)) clone[k] = Array.isArray(m[k]) ? m[k].slice() : [];
    WORK[f] = clone;
  }
}

// kinds belonging to a category (so a category bulk-flip can clear its
// kinds' finer overrides + so the kind drill-down can render rows).
function kindsForCategory(catId) {
  return ((OVERVIEW && OVERVIEW.kinds) || []).filter(k => k.category === catId);
}

// Every valid symbol token for a category = the category id + all its kind
// codes (used by bulk-clears-finer to strip the whole family from finer
// scopes when the category is flipped).
function categoryTokenSet(catId) {
  const s = new Set([catId]);
  for (const k of kindsForCategory(catId)) s.add(k.code);
  return s;
}

// ---- C2-4 symbol tri-state helpers (on the WORK maps) ----------------
// Tri-state per spec §3.3/§3.4: a token is ON if present in the on-map for
// the scope key, OFF if in the off-map, else INHERIT (absent from both).
function symStateAt(onField, offField, key, token) {
  const on = (WORK[onField][key] || []);
  const off = (WORK[offField][key] || []);
  if (off.indexOf(token) !== -1) return 'off';
  if (on.indexOf(token) !== -1) return 'on';
  return 'inherit';
}

// Mutate one map's key-list (add or remove a token), pruning empty keys so
// the encoded YAML stays exceptions-only (byte-stable when nothing is set).
function _listAdd(map, key, token) {
  let arr = map[key];
  if (!arr) { arr = []; map[key] = arr; }
  if (arr.indexOf(token) === -1) arr.push(token);
}
function _listRemove(map, key, token) {
  const arr = map[key];
  if (!arr) return;
  const i = arr.indexOf(token);
  if (i !== -1) arr.splice(i, 1);
  if (arr.length === 0) delete map[key];
}

// Set a token's tri-state at a scope key. A token is never in both on+off
// for the same key (the invariant): toggling to one removes it from the
// other; inherit removes it from both.
function setSymState(onField, offField, key, token, state) {
  _listRemove(WORK[onField], key, token);
  _listRemove(WORK[offField], key, token);
  if (state === 'on') _listAdd(WORK[onField], key, token);
  else if (state === 'off') _listAdd(WORK[offField], key, token);
  // 'inherit' = absent from both (already removed above)
}

// ---- C2-4 popup-set helpers (on the WORK maps) -----------------------
// Popups are an ABSOLUTE set per scope: a scope key present in its map wins
// outright; absent → inherit the next-coarser resolved set.
function popupSetField(scope) {
  return scope === 'book' ? 'popup_languages_per_book'
       : scope === 'chapter' ? 'popup_languages_per_chapter'
       : 'popup_languages_per_verse';
}
function popupHasExplicit(scope, key) {
  return Object.prototype.hasOwnProperty.call(WORK[popupSetField(scope)], key);
}
function popupExplicitSet(scope, key) {
  return (WORK[popupSetField(scope)][key] || []).slice();
}
function popupSetExplicit(scope, key, langs) {
  // Store an explicit (possibly empty) set — an empty array is meaningful
  // here ("show no popups at this scope"), so we keep the key even when [].
  WORK[popupSetField(scope)][key] = langs.slice();
}
function popupRevertToInherit(scope, key) {
  delete WORK[popupSetField(scope)][key];
}

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

// A faint "inherits: on/off" hint shown beside an inherit-state tri-state,
// so the builder sees what the value would be if left unset.
function inheritHint(state) {
  return '<span class="text-[10px] text-slate-400 italic ml-1" title="inherited from the level above">inherits ' +
    (state === 'on' ? 'on' : 'off') + '</span>';
}

// =====================================================================
// C2-4 — SAVE flow. The interactive controls mutate the WORK maps, then
// call scheduleSave([...]) with the names of every field they touched. We
// POST/PUT the FULL current WORK map for each named field (absolute-replace
// per field — see the WORK comment) and, on success, refetch OVERVIEW to
// re-authoritative-seed WORK + resolved state, invalidate the per-level
// caches for correctness, and re-render the current level.
//
// The shipped endpoint is PUT /api/edition-meta/<id> (api_save_edition_meta);
// the body is the decoded {field: {key:[values]}} dict the server validates
// + re-encodes; it answers {ok:true} | {error:"..."}.
//
// Autosave coordinator (debounce + serialize). Controls call scheduleSave();
// a burst of toggles debounces into ONE PUT, and two saves never overlap — a
// save's post-success re-seed pulls server state into WORK, which would clobber
// a mutation made while the PUT was in flight. So: touched field names
// accumulate in _pendingFields until the save actually fires (the PUT always
// reflects the final WORK); the worker (saveFields) preserves still-pending
// fields across the re-seed; and any toggle that lands during a save re-arms a
// follow-up save afterward. Single-user local app, but C2-5 builds on this flow.
// =====================================================================
let _saveTimer = null;
let _pendingFields = new Set();
let _saveInFlight = false;

function scheduleSave(fields) {
  for (const f of (fields || [])) _pendingFields.add(f);
  if (_saveTimer) clearTimeout(_saveTimer);
  _saveTimer = setTimeout(runPendingSave, 250);
}

async function runPendingSave() {
  _saveTimer = null;
  if (_saveInFlight || _pendingFields.size === 0) return;  // an in-flight save re-arms this on finish
  _saveInFlight = true;
  const fields = Array.from(_pendingFields);
  _pendingFields = new Set();
  try {
    await saveFields(fields);
  } finally {
    _saveInFlight = false;
    if (_pendingFields.size > 0) scheduleSave([]);  // toggles arrived mid-save → save them next
  }
}

// A small status line painted into #bmb-save-status (added to each panel's
// header area). ok=true → green ✓, ok=false → red ✗, null → neutral.
function setSaveStatus(msg, ok) {
  const el = document.getElementById('bmb-save-status');
  if (!el) return;
  if (!msg) { el.textContent = ''; el.className = 'text-xs'; return; }
  el.textContent = msg;
  el.className = 'text-xs ' +
    (ok === false ? 'text-red-600' : ok === true ? 'text-emerald-700' : 'text-slate-500');
}

async function saveFields(fields) {
  if (!CUR_EDITION || !WORK) return;
  // Build the payload: only the touched fields, each as its full current map.
  // Snapshot (deep-copy) each map so a WORK mutation between here and the
  // fetch can't alter what we send (the PUT body is a point-in-time state).
  const payload = {};
  for (const f of fields) payload[f] = JSON.parse(JSON.stringify(WORK[f] || {}));
  setSaveStatus('saving…', null);
  let result;
  try {
    const r = await fetch('/api/edition-meta/' + encodeURIComponent(CUR_EDITION), {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    result = await r.json();
    if (!r.ok || (result && result.error)) {
      const msg = (result && result.error) ? result.error : (r.status + ' ' + r.statusText);
      setSaveStatus('✗ ' + msg, false);
      return;
    }
  } catch (e) {
    setSaveStatus('✗ ' + (e && e.message ? e.message : String(e)), false);
    return;
  }
  // Success — re-seed authoritatively from the server so the next edit
  // builds on the canonical state (and any validator normalization shows).
  const snapEd = CUR_EDITION;
  try {
    OVERVIEW = await fetchOverview(snapEd);
  } catch (e) {
    // The write landed; only the refetch failed. Keep the local WORK as-is
    // and surface a soft warning — a reload re-syncs.
    setSaveStatus('✓ saved (reload to refresh)', true);
    return;
  }
  if (CUR_EDITION !== snapEd) return;  // user switched edition mid-save
  BOOKS = (OVERVIEW && OVERVIEW.books_canonical) || BOOKS;
  seedWorkFromOverview(_pendingFields);  // keep any field toggled during this PUT
  // Invalidate per-level caches so re-rendered resolved badges reflect the
  // save (the book/chapter payloads carry resolved state computed server-side).
  BOOK_CACHE = new Map();
  CHAPTER_CACHE = new Map();
  setSaveStatus('✓ saved', true);
  // Re-render the current level + reload the level payload if we're deeper
  // than the Bible level (book/chapter panels read from the now-cleared caches).
  await reRenderCurrentLevel();
}

// Re-render the active level after a save: the Bible level renders straight
// from OVERVIEW; the book/chapter levels must refetch their (now-invalidated)
// payloads first so the resolved badges are current. A focused verse is
// preserved across the chapter re-render (navToChapter resets CUR_VERSE),
// so saving a per-verse popup set doesn't collapse the verse the builder
// is working in.
async function reRenderCurrentLevel() {
  if (CUR_BOOK == null) {
    renderLevelPanel();
  } else if (CUR_CHAPTER == null) {
    await navToBook(CUR_BOOK);
  } else {
    const keepVerse = CUR_VERSE;
    // Brief flash: navToChapter paints the unfocused chapter, then we restore
    // the focused verse below. Acceptable for a post-save refresh.
    await navToChapter(CUR_CHAPTER);  // refetches the cleared chapter payload; resets CUR_VERSE
    if (keepVerse != null && CUR_BOOK != null && CUR_CHAPTER != null) {
      CUR_VERSE = keepVerse;
      renderBreadcrumb();
      renderChapterPanel(document.getElementById('level-panel'));
    }
  }
}

// Dirty-check (§6.4) — collect every interactive input/select in the panel.
// The controls autosave on change (so "dirty" is transient), but the spec
// requires the dirty pattern be honored where the codebase expects it: this
// helper exists + is exercised so a future Save-button variant / test can
// rely on `querySelectorAll('input, select')` finding the controls.
function bmbDirtyControls(box) {
  if (!box) return [];
  return Array.from(box.querySelectorAll('input, select'));
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
// (resolved popup-language list). The Bible (edition) level stays
// READ-ONLY in this task (C2-4): edition-wide symbol defaults are edited
// on /matrix and edition-wide popup defaults on /customize, so we render
// the resolved state read-only here + cross-link to those editors. Book /
// chapter / verse levels get the interactive controls below. Edition-wide
// writes from this console are deferred to C3.
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
// resolved on/off badge. Read-only (Bible level only); drill into a book
// for the interactive tri-state controls.
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
      <p class="text-xs text-slate-400 mb-2">edition-wide resolved on/off per symbol family (read-only here) —
        <a href="/matrix" class="text-blue-600 hover:underline">edit edition-wide on /matrix</a>,
        or pick a book on the left to override per book / chapter.</p>
      ${rows || '<div class="text-slate-400 text-sm">no categories</div>'}
    </section>`;
}

// POPUPS section — the resolved popup-language list as read-only chips.
// Read-only at the Bible level; drill into a book / chapter / verse for the
// interactive language checklist.
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
      <p class="text-xs text-slate-400 mb-2">edition-wide resolved translation-popup languages (read-only here) —
        <a href="/customize" class="text-blue-600 hover:underline">edit edition-wide on /customize</a>,
        or pick a book / chapter / verse to override.</p>
      <div class="flex flex-wrap gap-1.5">${chips}</div>
    </section>`;
}

// =====================================================================
// C2-4 — interactive SYMBOL tri-state controls (book + chapter levels).
//
// One row per category: a tri-state select (inherit / on / off) seeded
// from the WORK maps for this scope key, with a faint "inherits on/off"
// hint = the resolved value it would take if left unset. Each category
// row expands (a <details>) to per-kind tri-state selects (same scope key,
// kind-code token). Tokens: category id at the category row, kind code at
// the kind rows. Saving autosaves the touched field(s) (absolute-replace).
//
// scope = 'book' | 'chapter'; key = "<book>" | "<book>:<ch>".
// inheritedSymbols = {cat_id: 'on'|'off'} the next-coarser resolved state
// (what each category inherits when its tri-state is "inherit").
// =====================================================================
function renderSymbolsControls(scope, key, inheritedSymbols) {
  inheritedSymbols = inheritedSymbols || {};
  const onField = 'note_families_on_per_' + scope;
  const offField = 'note_families_off_per_' + scope;

  function triSelect(token, curState, cls) {
    // curState ∈ inherit|on|off. Mark each <option> selected explicitly.
    const opt = (val, label) =>
      `<option value="${val}"${curState === val ? ' selected' : ''}>${label}</option>`;
    return `<select class="${cls} text-xs border border-slate-300 rounded px-1 py-0.5"
        data-token="${esc(token)}">
        ${opt('inherit', 'inherit')}${opt('on', 'on')}${opt('off', 'off')}
      </select>`;
  }

  const rows = categoriesOrdered().map(c => {
    const catState = symStateAt(onField, offField, key, c.id);
    const inh = inheritedSymbols[c.id] || 'off';
    const kindRows = kindsForCategory(c.id).map(k => {
      const kState = symStateAt(onField, offField, key, k.code);
      return `
        <div class="sym-kind-row flex items-center justify-between gap-3 py-1 pl-7 pr-1 border-b border-slate-50"
             data-token="${esc(k.code)}">
          <div class="flex items-center gap-2 min-w-0">
            <span class="text-xs px-1.5 py-0.5 bg-slate-100 rounded font-mono text-slate-600">${esc(k.code)}</span>
            <span class="text-xs text-slate-600 truncate">${esc(k.label)}</span>
          </div>
          ${triSelect(k.code, kState, 'sym-kind-tri')}
        </div>`;
    }).join('');
    return `
      <details class="sym-cat border-b border-slate-100" data-category="${esc(c.id)}">
        <summary class="sym-row flex items-center justify-between gap-3 py-1.5 cursor-pointer list-none">
          <div class="flex items-center gap-2 min-w-0">
            <span class="text-slate-300 text-xs">▸</span>
            <span class="symbol text-slate-600" title="${esc(c.description || c.label)}">${esc(c.symbol)}</span>
            <span class="text-sm text-slate-700 truncate">${esc(c.label)}</span>
            ${catState === 'inherit' ? inheritHint(inh) : ''}
          </div>
          ${triSelect(c.id, catState, 'sym-cat-tri')}
        </summary>
        <div class="sym-kinds pb-1">${kindRows || '<div class="text-xs text-slate-400 pl-7 py-1">no kinds in this family</div>'}</div>
      </details>`;
  }).join('');

  const scopeWord = scope === 'book' ? 'this book' : 'this chapter';
  return `
    <section id="symbols-section" class="mb-6" data-scope="${esc(scope)}" data-scope-key="${esc(key)}">
      <h3 class="font-semibold text-slate-700 mb-1">Note symbols</h3>
      <p class="text-xs text-slate-400 mb-2">tri-state per family for ${scopeWord}: <em>inherit</em> (use the level above),
        <em>on</em>, or <em>off</em>. Expand a family to override individual kinds.
        Flipping a family clears its finer overrides in scope.</p>
      ${rows || '<div class="text-slate-400 text-sm">no categories</div>'}
    </section>`;
}

// Wire the symbol tri-state selects within a freshly-rendered panel.
// scope/key identify the coordinate; bulk-clears-finer (§3.2) runs before
// applying a category or kind flip.
function wireSymbolsControls(box, scope, key) {
  if (!box) return;
  const onField = 'note_families_on_per_' + scope;
  const offField = 'note_families_off_per_' + scope;

  // Category-level tri-state: setting it also clears the category + its
  // kinds from any FINER scope (chapter keys "book:*", or for a chapter
  // scope, the verse map "book:ch:*") so the coarse decision wins cleanly.
  box.querySelectorAll('.sym-cat-tri').forEach(sel => {
    sel.addEventListener('change', () => {
      const catId = sel.dataset.token;
      const state = sel.value;
      const touched = clearFinerSymbols(scope, key, categoryTokenSet(catId));
      setSymState(onField, offField, key, catId, state);
      touched.add(onField); touched.add(offField);
      scheduleSave([...touched]);
    });
  });
  // Kind-level tri-state: a single token; clears the SAME kind from finer
  // scopes (a kind decision at book level supersedes per-chapter kind set).
  box.querySelectorAll('.sym-kind-tri').forEach(sel => {
    sel.addEventListener('change', () => {
      const token = sel.dataset.token;
      const state = sel.value;
      const touched = clearFinerSymbols(scope, key, new Set([token]));
      setSymState(onField, offField, key, token, state);
      touched.add(onField); touched.add(offField);
      scheduleSave([...touched]);
    });
  });
}

// Bulk-clears-finer for SYMBOLS (§3.2). Remove `tokens` from every FINER
// symbol scope that falls within `key`. Returns the set of WORK field names
// it mutated (so the caller folds them into the save payload — they too get
// absolute-replaced). book key "gen" → clears note_families_*_per_chapter
// keys "gen:*"; chapter key "gen:1" has no finer SYMBOL scope (verse-level
// symbols are C2-5's note force-on/off, not in these maps).
function clearFinerSymbols(scope, key, tokens) {
  const touched = new Set();
  if (scope !== 'book') return touched;  // only book → chapter is finer here
  const prefix = key + ':';
  for (const field of ['note_families_on_per_chapter', 'note_families_off_per_chapter']) {
    const map = WORK[field];
    for (const k of Object.keys(map)) {
      if (k.indexOf(prefix) !== 0) continue;
      const arr = map[k];
      const kept = arr.filter(t => !tokens.has(t));
      if (kept.length !== arr.length) {
        touched.add(field);
        if (kept.length === 0) delete map[k];
        else map[k] = kept;
      }
    }
  }
  return touched;
}

// =====================================================================
// C2-4 — interactive POPUP language checklist (book / chapter / verse).
//
// Popups are an ABSOLUTE set per scope. If the scope key is present in its
// override map → that explicit set is edited; if absent → the scope INHERITS
// the next-coarser resolved set (shown faint) and the first toggle CREATES
// an explicit set seeded from the inherited set. A "↻ inherit" link removes
// the key (revert to inherit). Flipping a coarser scope clears finer popup
// keys in scope (§3.2).
//
// scope = 'book'|'chapter'|'verse'; key = "<book>"|"<book>:<ch>"|"<book>:<ch>:<vs>".
// inheritedSet = the resolved popup list this scope would inherit (the
// level payload's resolved.popups, which for an unset scope IS the inherited
// value).
// =====================================================================
function renderPopupsControls(scope, key, inheritedSet) {
  inheritedSet = inheritedSet || [];
  const explicit = popupHasExplicit(scope, key);
  const activeSet = explicit ? new Set(popupExplicitSet(scope, key)) : new Set(inheritedSet);
  const langs = (OVERVIEW && OVERVIEW.popup_languages) || [];
  const scopeWord = scope === 'book' ? 'this book' : scope === 'chapter' ? 'this chapter' : 'this verse';

  const boxes = langs.length ? langs.map(L => {
    const checked = activeSet.has(L.id);
    const dim = L.has_data ? '' : 'opacity-50';
    const noData = L.has_data ? '' : ' <span class="text-[10px] italic text-slate-400">(no data)</span>';
    return `
      <label class="text-sm flex items-center gap-1.5 ${dim}"
             title="${L.has_data ? '' : 'no source data yet — selecting has no visible effect'}">
        <input type="checkbox" class="popup-lang-cb" data-lang="${esc(L.id)}" ${checked ? 'checked' : ''}>
        ${esc(L.label)}${noData}
      </label>`;
  }).join('') : '<span class="text-slate-400 text-sm">no popup languages registered</span>';

  const stateLine = explicit
    ? `<span class="text-emerald-700">explicit set for ${scopeWord}</span>
       <button type="button" class="popup-revert ml-2 text-blue-600 hover:underline" title="remove this scope's override — fall back to the inherited set">↻ inherit</button>`
    : `<span class="text-slate-400 italic">inheriting the set above — checking a box creates an override for ${scopeWord}</span>`;

  // The per-verse instance uses a distinct id to avoid colliding with the
  // chapter-level #popups-section when a verse is focused; wiring is always
  // box-scoped so either works.
  const sectionId = scope === 'verse' ? 'popups-section-verse' : 'popups-section';
  return `
    <section id="${sectionId}" class="popups-section mb-2" data-scope="${esc(scope)}" data-scope-key="${esc(key)}">
      <h3 class="font-semibold text-slate-700 mb-1">Popup languages</h3>
      <p class="text-xs text-slate-400 mb-2">${stateLine}</p>
      <div class="flex flex-wrap gap-3 p-2 bg-slate-50 border border-slate-200 rounded">${boxes}</div>
      ${scope !== 'verse'
        ? '<p class="text-[10px] text-slate-400 mt-1 italic">Setting this clears finer popup exceptions in scope.</p>'
        : ''}
    </section>`;
}

// Wire the popup checklist within a freshly-rendered panel. Scopes its
// queries to the matching .popups-section (by data-scope + data-scope-key)
// so a chapter-panel call doesn't also grab a focused verse's checkboxes
// nested inside it (both live under the same panel element).
function wirePopupsControls(box, scope, key, inheritedSet) {
  if (!box) return;
  const field = popupSetField(scope);
  // Find this scope's own section. CSS.escape guards keys with ':' so the
  // attribute selector parses (book:ch:vs keys contain colons).
  const escKey = (window.CSS && CSS.escape) ? CSS.escape(key) : key.replace(/[^a-zA-Z0-9_-]/g, '\\$&');
  let section = box.querySelector('.popups-section[data-scope="' + scope + '"][data-scope-key="' + escKey + '"]');
  if (!section && box.matches && box.matches('.popups-section')) section = box;
  if (!section) section = box;  // last-resort fallback

  section.querySelectorAll('.popup-lang-cb').forEach(cb => {
    cb.addEventListener('change', () => {
      // First toggle on an inheriting scope seeds an explicit set from the
      // inherited resolved set, then applies this box's change.
      let cur;
      if (popupHasExplicit(scope, key)) {
        cur = new Set(popupExplicitSet(scope, key));
      } else {
        cur = new Set(inheritedSet || []);
      }
      if (cb.checked) cur.add(cb.dataset.lang);
      else cur.delete(cb.dataset.lang);
      popupSetExplicit(scope, key, [...cur]);
      const touched = clearFinerPopups(scope, key);
      touched.add(field);
      scheduleSave([...touched]);
    });
  });

  const revert = section.querySelector('.popup-revert');
  if (revert) {
    revert.addEventListener('click', () => {
      popupRevertToInherit(scope, key);
      // Reverting a coarse scope to inherit does NOT need to touch finer
      // keys (the resolver falls through), but reverting still only changes
      // this one field — send it (absolute-replace).
      scheduleSave([field]);
    });
  }
}

// Bulk-clears-finer for POPUPS (§3.2). Setting an explicit popup set at a
// coarser scope strips the finer popup overrides within that scope (their
// presence would otherwise win over the new coarser set). Returns the WORK
// field names it mutated. book "gen" → clears popup_languages_per_chapter
// "gen:*" + popup_languages_per_verse "gen:*"; chapter "gen:1" → clears
// popup_languages_per_verse "gen:1:*"; verse → nothing finer.
function clearFinerPopups(scope, key) {
  const touched = new Set();
  const strip = (field, prefix) => {
    const map = WORK[field];
    for (const k of Object.keys(map)) {
      if (k.indexOf(prefix) === 0) { delete map[k]; touched.add(field); }
    }
  };
  if (scope === 'book') {
    strip('popup_languages_per_chapter', key + ':');
    strip('popup_languages_per_verse', key + ':');
  } else if (scope === 'chapter') {
    strip('popup_languages_per_verse', key + ':');
  }
  return touched;
}

// ---- Book-level panel -----------------------------------------------
// Interactive book-level SYMBOL tri-state + POPUP checklist (C2-4), then
// the chapter grid. Each chapter is clickable (drills to the chapter
// level), shows a "has notes" indicator + its resolved symbol / popup
// badges. Chapters render 1..ch_count ascending (never sort).
function renderBookPanel(el) {
  const payload = BOOK_CACHE.get(CUR_BOOK);
  if (!payload) { spinnerInto(el, 'loading book …'); return; }
  const book = payload.book || {};
  const chapters = payload.chapters || [];
  setLevelHeader(book.title || CUR_BOOK,
    book.ch_count + ' chapter(s) · set this book\'s symbols / popups, or pick a chapter');

  // Inherited baseline for the book level = the edition default (Bible
  // resolved). For an inherit-state token at book level there is no book
  // override, so its inherited value IS the edition default. The popup
  // inherited set is likewise the edition-default resolved popup list.
  const bibleResolved = (OVERVIEW && OVERVIEW.resolved_bible) || { symbols: {}, popups: [] };

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

  el.innerHTML =
    renderSymbolsControls('book', CUR_BOOK, bibleResolved.symbols) +
    renderPopupsControls('book', CUR_BOOK, bibleResolved.popups) +
    `<section class="mb-2 mt-4 border-t border-slate-200 pt-4">
      <p class="text-xs text-slate-400 mb-2">a filled dot marks chapters with notes; counts show resolved symbol families on + popup languages — pick a chapter to override deeper</p>
      <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2">${grid}</div>
    </section>`;

  wireSymbolsControls(el, 'book', CUR_BOOK);
  wirePopupsControls(el, 'book', CUR_BOOK, bibleResolved.popups);
  el.querySelectorAll('.chapter-cell').forEach(cell => {
    cell.addEventListener('click', () => navToChapter(Number(cell.dataset.chapter)));
  });
}

function countSymbolsOn(symbols) {
  if (!symbols) return 0;
  return Object.values(symbols).filter(v => v === 'on').length;
}

// ---- Chapter-level panel --------------------------------------------
// Interactive chapter-level SYMBOL tri-state + POPUP checklist (C2-4),
// then the verse list (1..N ascending). Each verse shows its resolved
// symbols / popups summary and its notes as a read-only list. Clicking a
// verse focuses it — its notes expand (read-only; C2-5 owns the per-note
// checkboxes) AND its per-verse popup checklist appears (C2-4).
function renderChapterPanel(el) {
  const key = CUR_BOOK + ':' + CUR_CHAPTER;
  const payload = CHAPTER_CACHE.get(key);
  if (!payload) { spinnerInto(el, 'loading chapter …'); return; }
  const verses = payload.verses || [];
  const noteTotal = verses.reduce((s, v) => s + (v.notes ? v.notes.length : 0), 0);
  setLevelHeader(bookTitle(CUR_BOOK) + ' ' + CUR_CHAPTER,
    verses.length + ' verse(s) · ' + noteTotal + ' note(s) · set this chapter, or click a verse');

  // Inherited baseline for the chapter level = the book's resolved state.
  // The chapter's own resolved symbols (computed per-verse server-side, all
  // identical for the chapter) give the inherit-state hint value; for the
  // popup inherited set we use the book payload's chapter-entry resolved
  // popups (== book-resolved when the chapter has no explicit override).
  const chSymbols = (verses[0] && verses[0].resolved && verses[0].resolved.symbols) || {};
  const bookPayload = BOOK_CACHE.get(CUR_BOOK);
  let chInheritedPopups = [];
  if (bookPayload && bookPayload.chapters) {
    const chEntry = bookPayload.chapters.find(c => c.num === CUR_CHAPTER);
    if (chEntry && chEntry.resolved && chEntry.resolved.popups) chInheritedPopups = chEntry.resolved.popups;
  }

  el.innerHTML =
    renderSymbolsControls('chapter', key, chSymbols) +
    renderPopupsControls('chapter', key, chInheritedPopups) +
    `<section id="verse-list-section" class="mt-4 border-t border-slate-200 pt-4">
      <p class="text-xs text-slate-400 mb-2">click a verse to focus its notes + set a per-verse popup set</p>
      <ul class="space-y-2">
        ${verses.map(v => renderVerseRow(v)).join('')}
      </ul>
    </section>`;

  wireSymbolsControls(el, 'chapter', key);
  wirePopupsControls(el, 'chapter', key, chInheritedPopups);
  el.querySelectorAll('.verse-row').forEach(row => {
    row.querySelector('.verse-head').addEventListener('click', () => {
      const vs = Number(row.dataset.verse);
      // Toggle focus: clicking the focused verse collapses it again.
      CUR_VERSE = (CUR_VERSE === vs) ? null : vs;
      renderBreadcrumb();
      renderChapterPanel(el);
    });
    // Wire the per-verse popup checklist (C2-4) + per-note ships? checkboxes
    // (C2-5) for the focused verse.
    const vsNum = Number(row.dataset.verse);
    if (CUR_VERSE === vsNum) {
      const vEntry = verses.find(v => v.vs === vsNum);
      const vInherited = (vEntry && vEntry.resolved && vEntry.resolved.popups) || [];
      const vKey = key + ':' + vsNum;
      wirePopupsControls(row, 'verse', vKey, vInherited);
      wireNoteShipsControls(row);
    }
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

  // Notes list — interactive at the individual level (C2-5): each note
  // carries a "ships?" checkbox (force-on / force-off). Checkboxes are wired
  // in renderChapterPanel (scoped to the focused verse row).
  let body = '';
  if (focused) {
    const notesBlock = notes.length
      ? `<ul class="mt-1 ml-4 space-y-1 border-l-2 border-slate-100 pl-3">
           ${notes.map(n => renderNoteLine(n)).join('')}
         </ul>`
      : '<div class="mt-1 ml-4 text-xs text-slate-400">no notes attributed to this verse.</div>';
    // C2-4 — interactive per-verse popup checklist (absolute set for this
    // verse). The inherited set = this verse's resolved popups (the chapter/
    // book/edition value it would take with no verse override). wirePopups-
    // Controls is attached in renderChapterPanel (scoped to this verse row).
    const vKey = CUR_BOOK + ':' + CUR_CHAPTER + ':' + v.vs;
    const popupBlock = `<div class="mt-2 ml-4">${renderPopupsControls('verse', vKey, resolved.popups)}</div>`;
    body = notesBlock + popupBlock;
  }
  return `<li class="verse-row" data-verse="${v.vs}">${head}${body}</li>`;
}

// One interactive note line (C2-5): symbol + kind + title + a "ships?"
// checkbox = whether this note ends up in the built EPUB. The checkbox
// reflects the note's RESOLVED state (family on/off ∧ individual override)
// via the server-computed `ships` flag; a faint label explains WHY it ships
// (forced on / off via family / off via override / family on). Toggling
// writes the right per-note override through PUT /api/edition/<ed>/note-override
// (see wireNoteShipsControls). The data-* attributes carry the server flags
// the wiring needs so the row stays the single source of per-note truth.
function noteShipsLabel(n) {
  // §3.4 precedence order: forced_on wins absolutely; then a per-note force-off
  // (more specific than the family); then family-off; else family-on.
  if (n.forced_on) return '<span class="text-xs text-emerald-600 ml-1" title="force-on override — ships even though its family is off">(forced on)</span>';
  if (n.disabled) return '<span class="text-xs text-amber-600 ml-1" title="force-off override on this note">(off: override)</span>';
  if (!n.kind_enabled) return '<span class="text-xs text-slate-400 ml-1" title="this note\'s family is off at this coordinate">(off: family)</span>';
  return '<span class="text-xs text-slate-400 ml-1" title="ships because its family is on">(family on)</span>';
}

function renderNoteLine(n) {
  const dim = n.ships ? '' : 'opacity-50';
  return `
    <li class="note-line flex items-start gap-2 ${dim}" data-note-id="${esc(n.note_id)}"
        data-ships="${n.ships ? '1' : '0'}" data-kind-enabled="${n.kind_enabled ? '1' : '0'}">
      <label class="note-ships-label flex items-center gap-1 cursor-pointer select-none mt-0.5"
             title="ships? — whether this note ends up in the built EPUB">
        <input type="checkbox" class="note-ships-cb" data-note-id="${esc(n.note_id)}" ${n.ships ? 'checked' : ''}>
      </label>
      <span class="symbol text-slate-500" title="${esc(n.category)}">${esc(n.symbol)}</span>
      <span class="text-xs px-1.5 py-0.5 bg-slate-100 rounded font-mono text-slate-600">${esc(n.kind)}</span>
      <span class="text-sm text-slate-700 flex-1 min-w-0">${esc(n.title || 'Note')}${noteShipsLabel(n)}</span>
    </li>`;
}

// Wire the per-note "ships?" checkboxes for the focused verse (C2-5). The
// row's data-* flags + the checkbox's desired value pick the three-state
// override to send (§3.4):
//   desired ON  + family on  → "default" (drop any force-off)
//   desired ON  + family off → "on"      (force-on the off-family note)
//   desired OFF + family on  → "off"     (force-off)
//   desired OFF + family off → "default" (drop any force-on)
// On success we invalidate this chapter's cache + refetch OVERVIEW (so the
// overrides maps are current) then re-render, preserving the focused verse.
function wireNoteShipsControls(row) {
  if (!row) return;
  row.querySelectorAll('.note-ships-cb').forEach(cb => {
    cb.addEventListener('change', () => {
      const line = cb.closest('.note-line');
      if (!line) return;
      const noteId = cb.dataset.noteId;
      const kindEnabled = line.dataset.kindEnabled === '1';
      const desired = cb.checked;  // new checkbox value = "should this ship?"
      let state;
      if (desired) state = kindEnabled ? 'default' : 'on';
      else state = kindEnabled ? 'off' : 'default';
      saveNoteOverride(noteId, state);
    });
  });
}

// PUT the per-note override + refresh (mirrors C2-4's fetch/error handling).
// Note-ship overrides write per-note state to a DISTINCT endpoint
// (/note-override) and never touch the WORK symbol/popup maps, so they
// deliberately bypass the scheduleSave debounce/in-flight coordinator. A
// rapid note-toggle concurrent with an in-flight symbol/popup save is safe:
// JS is single-threaded, each PUT body is built before any await, and the two
// writes target different fields — the only effect is a harmless double
// re-render. The re-seed below preserves any still-pending WORK fields.
async function saveNoteOverride(noteId, state) {
  if (!CUR_EDITION) return;
  const snapEd = CUR_EDITION;
  const snapBook = CUR_BOOK;
  const snapCh = CUR_CHAPTER;
  setSaveStatus('saving…', null);
  let result;
  try {
    const r = await fetch('/api/edition/' + encodeURIComponent(snapEd) + '/note-override', {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({note_id: noteId, state: state}),
    });
    result = await r.json();
    if (!r.ok || (result && result.error)) {
      const msg = (result && result.error) ? result.error : (r.status + ' ' + r.statusText);
      setSaveStatus('✗ ' + msg, false);
      return;
    }
  } catch (e) {
    setSaveStatus('✗ ' + (e && e.message ? e.message : String(e)), false);
    return;
  }
  // Success — refetch OVERVIEW so overrides.disabled_note_ids / enabled_note_ids
  // are current, then invalidate the chapter cache + re-render (the chapter
  // payload carries the server-computed ships/forced_on/disabled flags).
  try {
    OVERVIEW = await fetchOverview(snapEd);
  } catch (e) {
    setSaveStatus('✓ saved (reload to refresh)', true);
    return;
  }
  if (CUR_EDITION !== snapEd) return;  // user switched edition mid-save
  BOOKS = (OVERVIEW && OVERVIEW.books_canonical) || BOOKS;
  seedWorkFromOverview(_pendingFields);
  if (snapBook != null && snapCh != null) CHAPTER_CACHE.delete(snapBook + ':' + snapCh);
  setSaveStatus('✓ saved', true);
  await reRenderCurrentLevel();
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
  // Drop any autosave pending for the edition we're leaving — its field names
  // don't belong to the new edition's WORK maps.
  if (_saveTimer) { clearTimeout(_saveTimer); _saveTimer = null; }
  _pendingFields = new Set();

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
  seedWorkFromOverview();  // C2-4 — working copy of the override maps
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

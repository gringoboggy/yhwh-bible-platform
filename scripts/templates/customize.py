"""HTML for /customize console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import CUSTOMIZE_HTML` callers.

ψ.15 editor-console polish (2026-05-09): cross-link nav substituted
from `_design.HEADER_NAV_LINKS("/customize")` and `BUYER_ARC_POLISH_CSS`
inlined from `_design`, mirroring the ψ.14 buyer-arc pattern.
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
)

CUSTOMIZE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>E-Bible · Customize</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
  .symbol-input {
    font-size: 1.4em;
    text-align: center;
    width: 2.5em;
    border: 1px solid #cbd5e0;
    border-radius: 4px;
    padding: 4px 0;
  }
  .label-input {
    border: 1px solid #cbd5e0;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 0.95em;
  }
  .dirty { background: #fef3c7; }
  .saved { background: #d1fae5; transition: background 1s; }
</style>
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Customize Symbols & Labels</h1>
    <p class="text-xs text-slate-500">edit category glyphs · edit kind labels · changes propagate to /matrix and /sources immediately</p>
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

  <div class="bg-amber-50 border border-amber-200 rounded p-3 mb-4 text-sm">
    <strong>Heads up:</strong> changes here update <code class="font-mono">content/categories.yaml</code>,
    <code class="font-mono">content/kinds.yaml</code>, and <code class="font-mono">content/editions.yaml</code>
    directly (with backups). Every UI in the system reads from those files, so the change
    appears everywhere on the next page load.
  </div>

  <section class="bg-white rounded-lg shadow-sm border border-slate-200 mb-6">
    <div class="px-4 py-3 border-b border-slate-200">
      <h2 class="font-semibold">Editions <span class="text-xs text-slate-500 font-normal">(5)</span></h2>
      <p class="text-xs text-slate-500">title · audience · verse-popup behavior · custom verse marker</p>
    </div>
    <div id="ed-body" class="divide-y divide-slate-100"></div>
  </section>

  <section class="bg-white rounded-lg shadow-sm border border-slate-200 mb-6">
    <div class="px-4 py-3 border-b border-slate-200">
      <h2 class="font-semibold">Categories <span class="text-xs text-slate-500 font-normal">(14)</span></h2>
      <p class="text-xs text-slate-500">the inline glyph + family label for each category</p>
    </div>
    <table class="w-full text-sm">
      <thead class="text-xs uppercase tracking-wide text-slate-500 bg-slate-50">
        <tr>
          <th class="text-left px-3 py-2">id</th>
          <th class="text-left px-3 py-2">symbol</th>
          <th class="text-left px-3 py-2">label</th>
          <th class="px-3 py-2"></th>
        </tr>
      </thead>
      <tbody id="cat-body"></tbody>
    </table>
  </section>

  <section class="bg-white rounded-lg shadow-sm border border-slate-200 mb-6">
    <div class="px-4 py-3 border-b border-slate-200">
      <h2 class="font-semibold">Kinds <span class="text-xs text-slate-500 font-normal">(63 — grouped by category)</span></h2>
      <p class="text-xs text-slate-500">label-level customization per kind · symbol inherits from category by default</p>
    </div>
    <div id="kinds-body" class="p-2"></div>
  </section>

  <div id="loading" class="text-center text-slate-400 py-20">loading …</div>
</main>

<script>
let DATA = null;

async function init() {
  const r = await fetch('/api/customize');
  DATA = await r.json();
  document.getElementById('loading').classList.add('hidden');
  renderEditions();
  renderCategories();
  renderKinds();
}

function renderEditions() {
  const wrap = document.getElementById('ed-body');
  wrap.innerHTML = DATA.editions.map(e => `
    <div class="p-4" data-edition="${e.id}">
      <div class="flex items-baseline justify-between mb-2 flex-wrap gap-2">
        <div class="flex items-baseline gap-2">
          <span class="font-mono text-xs text-slate-400">${e.id}</span>
          <input class="label-input flex-1 min-w-72" data-field="title" value="${escapeAttr(e.title)}" maxlength="200" placeholder="title">
        </div>
        <div class="flex items-center gap-3 flex-wrap">
          <label class="text-xs flex items-center gap-1.5 cursor-pointer select-none">
            <input type="checkbox" data-field="verse_popups" ${e.verse_popups ? 'checked' : ''}>
            verse-popup translations
          </label>
          <label class="text-xs flex items-center gap-1.5">
            <span>show:</span>
            <select class="label-input" data-field="popup_translation" title="which translation appears in verse-number popups (Phase τ.1.5)">
              <option value="" ${!e.popup_translation ? 'selected' : ''}>(default)</option>
              ${(DATA.translations || []).map(t => `<option value="${t.id}" ${e.popup_translation === t.id ? 'selected' : ''} title="${escapeAttr(t.title)} — ${escapeAttr(t.license)}">${escapeAttr(t.short_title)}</option>`).join('')}
            </select>
          </label>
          <label class="text-xs flex items-center gap-1.5">
            <span>marker:</span>
            <input class="symbol-input" data-field="verse_marker_glyph" value="${escapeAttr(e.verse_marker_glyph)}" maxlength="4" placeholder="·" title="leave empty for default verse number">
          </label>
          <label class="text-xs flex items-center gap-1.5">
            <span>theme:</span>
            <select class="label-input" data-field="theme">
              ${(DATA.themes || []).map(t => `<option value="${t.id}" ${e.theme === t.id ? 'selected' : ''} title="${escapeAttr(t.description)}">${escapeAttr(t.name)}</option>`).join('')}
            </select>
          </label>
        </div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
        <input class="label-input" data-field="short_title" value="${escapeAttr(e.short_title)}" maxlength="100" placeholder="short title">
        <input class="label-input" data-field="isbn" value="${escapeAttr(e.isbn)}" maxlength="40" placeholder="ISBN">
        <input class="label-input md:col-span-2" data-field="target_audience" value="${escapeAttr(e.target_audience)}" maxlength="500" placeholder="target audience">
        <input class="label-input md:col-span-2" data-field="notes" value="${escapeAttr(e.notes)}" maxlength="500" placeholder="editorial notes">
      </div>

      <details class="popup-langs-section mt-3 border border-slate-200 rounded bg-slate-50">
        <summary class="px-3 py-2 cursor-pointer text-xs font-semibold uppercase tracking-wide text-slate-600 hover:bg-slate-100">
          Reader experience
          <span class="text-slate-400 normal-case font-normal ml-2">
            chapter heading style · reader's TOC display
          </span>
        </summary>
        <div class="px-3 pb-3 pt-1 space-y-3">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <label class="text-xs">
              <span class="block mb-1 font-medium text-slate-700">Chapter number format</span>
              <select class="label-input w-full" data-field="chapter_number_format" title="how the chapter number renders in body headings">
                <option value="digit"        ${(e.chapter_number_format||'digit') === 'digit' ? 'selected' : ''}>digit · 42</option>
                <option value="word"         ${e.chapter_number_format === 'word' ? 'selected' : ''}>word · Forty-Two</option>
                <option value="word_chapter" ${e.chapter_number_format === 'word_chapter' ? 'selected' : ''}>word + "Chapter" · Chapter Forty-Two</option>
              </select>
            </label>
            <label class="text-xs">
              <span class="block mb-1 font-medium text-slate-700">Chapter number decoration</span>
              <select class="label-input w-full" data-field="chapter_number_decoration" title="decorative wrappers around the chapter number">
                <option value="plain"        ${(e.chapter_number_decoration||'plain') === 'plain' ? 'selected' : ''}>plain · 1</option>
                <option value="dashes"       ${e.chapter_number_decoration === 'dashes' ? 'selected' : ''}>dashes · — 1 —</option>
                <option value="em_dashes"    ${e.chapter_number_decoration === 'em_dashes' ? 'selected' : ''}>em-dashes · ———— 1 ————</option>
                <option value="stars"        ${e.chapter_number_decoration === 'stars' ? 'selected' : ''}>stars · ✦ 1 ✦</option>
                <option value="asterisks"    ${e.chapter_number_decoration === 'asterisks' ? 'selected' : ''}>asterisks · **** 1 ****</option>
                <option value="bullets"      ${e.chapter_number_decoration === 'bullets' ? 'selected' : ''}>bullets · • • • 1 • • •</option>
                <option value="ornament"     ${e.chapter_number_decoration === 'ornament' ? 'selected' : ''}>ornament · ❦ 1 ❦</option>
                <option value="fleurons"     ${e.chapter_number_decoration === 'fleurons' ? 'selected' : ''}>fleurons · ❧ 1 ❧</option>
                <option value="wave"         ${e.chapter_number_decoration === 'wave' ? 'selected' : ''}>wave · ～ 1 ～</option>
                <option value="double_lines" ${e.chapter_number_decoration === 'double_lines' ? 'selected' : ''}>double lines · ══ 1 ══</option>
              </select>
            </label>
          </div>
          <div class="pt-2 border-t border-slate-200">
            <label class="text-xs">
              <span class="block mb-1 font-medium text-slate-700">Book ToC ornament</span>
              <select class="label-input w-full md:w-1/2" data-field="book_toc_ornament" title="small visual marker that precedes each book name in the in-book Table of Contents (Phase ν.6.1)">
                <option value="none"           ${(e.book_toc_ornament||'none') === 'none' ? 'selected' : ''}>none · Genesis</option>
                <option value="square"         ${e.book_toc_ornament === 'square' ? 'selected' : ''}>square · ▪ Genesis</option>
                <option value="cross_latin"    ${e.book_toc_ornament === 'cross_latin' ? 'selected' : ''}>Latin cross · ✝ Genesis  (Catholic / Reformed)</option>
                <option value="cross_lalibela" ${e.book_toc_ornament === 'cross_lalibela' ? 'selected' : ''}>Lalibela cross · ✛ Genesis  (Ethiopian Tewahedo)</option>
                <option value="star_david"     ${e.book_toc_ornament === 'star_david' ? 'selected' : ''}>Star of David · ✡ Bereshit  (Jewish / Hebrew)</option>
                <option value="fleur"          ${e.book_toc_ornament === 'fleur' ? 'selected' : ''}>fleur-de-lis · ⚜ Genesis  (decorative)</option>
              </select>
            </label>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-slate-200">
            <label class="text-xs flex items-center gap-2">
              <input type="checkbox" data-field="reader_toc_collapsible" ${e.reader_toc_collapsible !== false ? 'checked' : ''}>
              <span>Reader's TOC: collapsible (dropdown per book)</span>
            </label>
            <label class="text-xs flex items-center gap-2">
              <input type="checkbox" data-field="reader_toc_default_open" ${e.reader_toc_default_open ? 'checked' : ''}>
              <span>Books default to expanded</span>
            </label>
            <p class="text-xs text-slate-500 md:col-span-2 italic">
              Note: chapter heading changes apply on the next BUILD. Reader's
              TOC dropdown preference and book ToC ornament are recorded
              per-edition; per-edition application of these settings is queued
              for a follow-up phase.
            </p>
          </div>
        </div>
      </details>

      <details class="traditions-section mt-3 border border-slate-200 rounded bg-slate-50">
        <summary class="px-3 py-2 cursor-pointer text-xs font-semibold uppercase tracking-wide text-slate-600 hover:bg-slate-100">
          Traditions
          <span class="text-slate-400 normal-case font-normal ml-2">
            which denominational notes appear in popups (Phase ψ.8)
          </span>
        </summary>
        <div class="p-3 traditions-body" data-edition-id="${e.id}">
          <p class="text-xs text-slate-500 mb-2">
            Notes are tagged by tradition (Catholic, Protestant, Eastern
            Orthodox, Jewish, Ethiopian Tewahedo, plus the denominationally
            neutral <em>Cross-tradition</em> bucket for linguistic and
            cross-reference apparatus). Selecting traditions here filters
            which notes survive into this edition's EPUB; popups render
            them in canonical order.
          </p>

          <div class="text-xs text-slate-500 mb-2">
            <strong>Default for all books:</strong>
            <span class="text-slate-400">applies to every book in the canon unless overridden below</span>
          </div>
          <div class="traditions-default-row flex flex-wrap gap-3 mb-3 p-2 bg-white border border-slate-200 rounded">
            ${(DATA.traditions || []).map(T => `
              <label class="text-sm flex items-center gap-1.5">
                <input type="checkbox" class="tradition-cb-default" data-tradition="${T.id}">
                ${escapeAttr(T.label)}
              </label>
            `).join('')}
          </div>

          <div class="flex items-center justify-between mb-2">
            <div class="text-xs text-slate-500">
              <strong>Per-book overrides:</strong>
              <span class="traditions-overrides-count text-slate-400">0 customized</span>
            </div>
            <div class="flex items-center gap-2 text-xs">
              <button type="button" class="traditions-bulk-clear px-2 py-1 rounded border border-slate-300 bg-white hover:bg-slate-100" title="Remove all per-book tradition overrides; every book inherits the default">
                ↺ apply default to all
              </button>
            </div>
          </div>

          <div class="traditions-overrides-list space-y-1"></div>

          <div class="traditions-add-book-row mt-2 flex items-center gap-2">
            <select class="traditions-add-book-select label-input flex-1" style="max-width: 28em">
              <option value="">+ add a book to customize…</option>
            </select>
          </div>

          <p class="text-xs text-slate-400 mt-3 italic">
            Leaving every default box unchecked means "no tradition filter"
            for any book without an override — pre-ψ.8 behaviour preserved
            per §7.2. Books listed in canonical Book/Chapter order; only
            books in <span class="traditions-canon-name font-medium">this edition's canon</span>
            appear.
          </p>
        </div>
      </details>

      <details class="popup-langs-section mt-3 border border-slate-200 rounded bg-slate-50">
        <summary class="px-3 py-2 cursor-pointer text-xs font-semibold uppercase tracking-wide text-slate-600 hover:bg-slate-100">
          Per-book popup languages
          <span class="text-slate-400 normal-case font-normal ml-2">
            (default + per-book overrides; books listed in canonical order)
          </span>
        </summary>
        <div class="p-3 popup-langs-body" data-edition-id="${e.id}">
          <div class="text-xs text-slate-500 mb-2">
            <strong>Default for all books:</strong>
            <span class="text-slate-400">applies to every book in the canon unless overridden below</span>
          </div>
          <div class="default-row flex flex-wrap gap-3 mb-3 p-2 bg-white border border-slate-200 rounded">
            ${(DATA.popup_languages || []).map(L => `
              <label class="text-sm flex items-center gap-1.5 ${L.has_data ? '' : 'opacity-50'}" title="${L.has_data ? '' : 'no source data yet — selecting has no visible effect'}">
                <input type="checkbox" class="popup-lang-default" data-lang="${L.id}">
                ${escapeAttr(L.label)}${L.has_data ? '' : ' <span class=\"text-xs italic text-slate-400\">(no data)</span>'}
              </label>
            `).join('')}
          </div>

          <div class="flex items-center justify-between mb-2">
            <div class="text-xs text-slate-500">
              <strong>Per-book overrides:</strong>
              <span class="overrides-count text-slate-400">0 customized</span>
            </div>
            <div class="flex items-center gap-2 text-xs">
              <button type="button" class="bulk-clear px-2 py-1 rounded border border-slate-300 bg-white hover:bg-slate-100" title="Remove all per-book overrides; every book inherits the default">
                ↺ apply default to all
              </button>
            </div>
          </div>

          <div class="overrides-list space-y-1"></div>

          <div class="add-book-row mt-2 flex items-center gap-2">
            <select class="add-book-select label-input flex-1" style="max-width: 28em">
              <option value="">+ add a book to customize…</option>
            </select>
          </div>

          <p class="text-xs text-slate-400 mt-3 italic">
            Books listed strictly in canonical Book/Chapter order
            (Genesis → Apocrypha → New Testament → Ethiopian tail).
            Only books in <span class="canon-name font-medium">this edition's canon</span>
            appear; the others would never reach the reader.
          </p>
        </div>
      </details>

      <div class="mt-2 flex items-center gap-3">
        <button class="ed-save text-xs px-3 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white opacity-50 inline-flex items-center gap-1.5" disabled>
          <span>Save edition</span>
          <span class="ed-save-count hidden text-[10px] leading-none px-1.5 py-0.5 rounded-full bg-white/25 font-semibold tabular-nums" title="unsaved changes on this edition"></span>
        </button>
        <button class="ed-preview text-xs px-3 py-1 rounded border border-slate-300 hover:border-blue-500 hover:text-blue-700 text-slate-700 opacity-50 disabled:cursor-not-allowed" title="Preview exactly what will change before committing (Phase ν.5)" disabled>Preview changes</button>
        <button class="ed-history text-xs text-slate-500 hover:text-blue-700 hover:underline" title="View backup snapshots (Phase ω.1)">Version history</button>
        <span class="ed-status text-xs"></span>
      </div>
    </div>
  `).join('');
  wrap.querySelectorAll('[data-edition]').forEach(box => {
    const inputs = box.querySelectorAll('input, select');
    const btn = box.querySelector('.ed-save');
    const previewBtn = box.querySelector('.ed-preview');
    inputs.forEach(inp => {
      const original = inp.type === 'checkbox' ? String(inp.checked) : inp.value;
      inp.dataset.original = original;
      const handler = () => {
        // Count individual dirty inputs for the ν.2.9 save-pending
        // badge — knowing "N changes" at a glance is the affordance.
        let dirtyCount = 0;
        inputs.forEach(i => {
          const cur = i.type === 'checkbox' ? String(i.checked) : i.value;
          if (cur !== i.dataset.original) dirtyCount++;
        });
        // The popup-language section maintains its own dirty flag
        // (see wirePopupLanguageSection) — fold it into the overall
        // edition dirty state so the Save button reflects every kind
        // of change the publisher might have made. We count it as
        // one logical "change" for the badge.
        if (box.dataset.popupLangsDirty === '1') dirtyCount++;
        // ψ.8.3 — same fold-in for the Traditions section.
        if (box.dataset.traditionsDirty === '1') dirtyCount++;
        const dirty = dirtyCount > 0;
        btn.disabled = !dirty;
        btn.classList.toggle('opacity-50', !dirty);
        // ν.2.9 save-pending badge — chip on the Save button itself
        const badge = btn.querySelector('.ed-save-count');
        if (badge) {
          if (dirty) {
            badge.textContent = String(dirtyCount);
            badge.classList.remove('hidden');
          } else {
            badge.classList.add('hidden');
          }
        }
        // Phase ν.5 — preview button enables together with save
        if (previewBtn) {
          previewBtn.disabled = !dirty;
          previewBtn.classList.toggle('opacity-50', !dirty);
        }
        box.classList.toggle('dirty', dirty);
      };
      inp.addEventListener('input', handler);
      inp.addEventListener('change', handler);
    });
    // Phase ν.2.7-B — wire the per-book popup language section.
    const ed = DATA.editions.find(x => x.id === box.dataset.edition);
    wirePopupLanguageSection(box, ed, () => {
      // When the section reports a change, recompute dirty state
      // by triggering the standard input handler.
      const evt = new Event('change', {bubbles: true});
      const anyInput = box.querySelector('input, select');
      if (anyInput) anyInput.dispatchEvent(evt);
    });
    // Phase ψ.8.3 — wire the Traditions section the same way.
    wireTraditionsSection(box, ed, () => {
      const evt = new Event('change', {bubbles: true});
      const anyInput = box.querySelector('input, select');
      if (anyInput) anyInput.dispatchEvent(evt);
    });
    btn.addEventListener('click', () => saveEdition(box));
    // Phase ν.5 — preview button click handler
    if (previewBtn) {
      previewBtn.addEventListener('click', () => previewEdition(box));
    }
    // Phase ω.1 — version history button
    const historyBtn = box.querySelector('.ed-history');
    if (historyBtn) {
      historyBtn.addEventListener('click', () => openHistoryModal(box));
    }
  });
}

// =====================================================================
// Phase ν.2.7-B — per-book popup language section
//
// Renders + manages the collapsible "Per-book popup languages" matrix
// inside each edition card. Books are listed in the order they appear
// in DATA.books_canonical (which is sourced from books.yaml — the
// single canonical-order authority per CLAUDE_PROJECT_RULES.md §6.1).
// Books outside the edition's canon are filtered out.
//
// State management:
//   box.popupLangsState = {
//     default:  Set<lang_id>,
//     perBook:  Map<book_code, Set<lang_id>>,    only customized books
//     original: { default, perBook }              for dirty comparison
//   }
//   box.dataset.popupLangsDirty = '0' | '1'
// =====================================================================

function wirePopupLanguageSection(box, edition, onChange) {
  const body = box.querySelector('.popup-langs-body');
  if (!body) return;

  const canonBooks = (DATA.edition_canon_books || {})[edition.id] || [];
  const canonSet = new Set(canonBooks);
  const allLangs = (DATA.popup_languages || []).map(L => L.id);

  // Initialize state from the API payload. popup_languages_default
  // is a list; popup_languages_per_book is a decoded dict.
  const initialDefault = new Set(edition.popup_languages_default || []);
  const initialPerBook = new Map();
  for (const [code, langs] of Object.entries(edition.popup_languages_per_book || {})) {
    if (canonSet.has(code)) initialPerBook.set(code, new Set(langs));
  }

  const state = {
    default: new Set(initialDefault),
    perBook: new Map(initialPerBook),
    original: {
      default: new Set(initialDefault),
      perBook: new Map([...initialPerBook].map(([k, v]) => [k, new Set(v)])),
    },
  };
  box.popupLangsState = state;

  // Populate the canon name and filter the books list to canonical
  // order ∩ canon.
  const canonNameEl = body.querySelector('.canon-name');
  if (canonNameEl) {
    canonNameEl.textContent = edition.canon
      ? `${edition.canon} (${canonBooks.length} books)`
      : `(${canonBooks.length} books)`;
  }
  const booksInCanon = (DATA.books_canonical || []).filter(b => canonSet.has(b.code));

  // Default-row checkboxes
  body.querySelectorAll('.popup-lang-default').forEach(cb => {
    cb.checked = state.default.has(cb.dataset.lang);
    cb.addEventListener('change', () => {
      if (cb.checked) state.default.add(cb.dataset.lang);
      else state.default.delete(cb.dataset.lang);
      markPopupLangsDirty(box, state);
      onChange && onChange();
    });
  });

  // Render per-book overrides + the add-book picker
  function renderOverrides() {
    const list = body.querySelector('.overrides-list');
    list.innerHTML = '';
    const canonRank = new Map(booksInCanon.map((b, i) => [b.code, i]));
    const codes = [...state.perBook.keys()]
      .filter(c => canonSet.has(c))
      .sort((a, b) => canonRank.get(a) - canonRank.get(b));

    body.querySelector('.overrides-count').textContent =
      `${codes.length} customized of ${booksInCanon.length}`;

    if (codes.length === 0) {
      list.innerHTML = `<p class="text-xs text-slate-400 italic px-1">
        no per-book overrides yet — every book uses the default above.
        Use the dropdown to customize a specific book.
      </p>`;
    } else {
      for (const code of codes) {
        const title = booksInCanon.find(b => b.code === code)?.title || code;
        const langs = state.perBook.get(code) || new Set();
        const row = document.createElement('div');
        row.className = 'override-row flex flex-wrap items-center gap-3 p-2 bg-white border border-slate-200 rounded';
        row.dataset.book = code;
        row.innerHTML = `
          <div class="flex items-baseline gap-2 min-w-48">
            <span class="font-mono text-xs text-slate-400 w-12">${code}</span>
            <span class="text-sm font-medium truncate">${escapeAttr(title)}</span>
          </div>
          <div class="flex flex-wrap gap-3 flex-1">
            ${(DATA.popup_languages || []).map(L => `
              <label class="text-sm flex items-center gap-1 ${L.has_data ? '' : 'opacity-50'}">
                <input type="checkbox" class="popup-lang-book" data-lang="${L.id}"
                  ${langs.has(L.id) ? 'checked' : ''}>
                ${escapeAttr(L.label)}
              </label>
            `).join('')}
          </div>
          <button type="button" class="remove-override text-slate-400 hover:text-red-600 px-1" title="revert to default — remove this override">×</button>
        `;
        // Wire per-book checkboxes
        row.querySelectorAll('.popup-lang-book').forEach(cb => {
          cb.addEventListener('change', () => {
            const set = state.perBook.get(code);
            if (cb.checked) set.add(cb.dataset.lang);
            else set.delete(cb.dataset.lang);
            markPopupLangsDirty(box, state);
            onChange && onChange();
          });
        });
        // Wire remove
        row.querySelector('.remove-override').addEventListener('click', () => {
          state.perBook.delete(code);
          renderOverrides();
          renderAddBookSelect();
          markPopupLangsDirty(box, state);
          onChange && onChange();
        });
        list.appendChild(row);
      }
    }
  }

  function renderAddBookSelect() {
    const sel = body.querySelector('.add-book-select');
    const customized = new Set(state.perBook.keys());
    const options = booksInCanon
      .filter(b => !customized.has(b.code))
      .map(b => `<option value="${b.code}">${b.code} — ${escapeAttr(b.title)}</option>`)
      .join('');
    sel.innerHTML = `<option value="">+ add a book to customize…</option>${options}`;
  }

  body.querySelector('.add-book-select').addEventListener('change', (ev) => {
    const code = ev.target.value;
    if (!code) return;
    // Start the new override at whatever the default currently is —
    // matches the publisher's mental model: "customize this book
    // starting from where I'd be otherwise."
    state.perBook.set(code, new Set(state.default));
    renderOverrides();
    renderAddBookSelect();
    ev.target.value = '';
    markPopupLangsDirty(box, state);
    onChange && onChange();
  });

  body.querySelector('.bulk-clear').addEventListener('click', () => {
    if (state.perBook.size === 0) return;
    state.perBook.clear();
    renderOverrides();
    renderAddBookSelect();
    markPopupLangsDirty(box, state);
    onChange && onChange();
  });

  renderOverrides();
  renderAddBookSelect();
  markPopupLangsDirty(box, state);
}

function markPopupLangsDirty(box, state) {
  // Compare current to original; flag the box if any difference.
  const o = state.original;
  const sameSet = (a, b) => a.size === b.size && [...a].every(x => b.has(x));
  let dirty = false;
  if (!sameSet(state.default, o.default)) dirty = true;
  if (state.perBook.size !== o.perBook.size) dirty = true;
  if (!dirty) {
    for (const [code, langs] of state.perBook) {
      const orig = o.perBook.get(code);
      if (!orig || !sameSet(langs, orig)) { dirty = true; break; }
    }
  }
  box.dataset.popupLangsDirty = dirty ? '1' : '0';
}

// =====================================================================
// Phase ψ.8.3 + ψ.8.4 — Traditions section
//
// Mirror of wirePopupLanguageSection: per-edition default + per-book
// overrides. State on the edition card:
//   box.traditionsState = {
//     default:  Set<tradition_id>,
//     perBook:  Map<book_code, Set<tradition_id>>,    only customized
//     original: { default, perBook }                  for dirty diff
//   }
//   box.dataset.traditionsDirty = '0' | '1'
// =====================================================================

function wireTraditionsSection(box, edition, onChange) {
  const body = box.querySelector('.traditions-body');
  if (!body) return;

  const canonBooks = (DATA.edition_canon_books || {})[edition.id] || [];
  const canonSet = new Set(canonBooks);

  const initialDefault = new Set(edition.traditions_default || []);
  const initialPerBook = new Map();
  for (const [code, traditions] of Object.entries(edition.traditions_per_book || {})) {
    if (canonSet.has(code)) initialPerBook.set(code, new Set(traditions));
  }

  const state = {
    default: new Set(initialDefault),
    perBook: new Map(initialPerBook),
    original: {
      default: new Set(initialDefault),
      perBook: new Map([...initialPerBook].map(([k, v]) => [k, new Set(v)])),
    },
  };
  box.traditionsState = state;

  // Populate the canon name + filter book list to canonical order ∩ canon
  const canonNameEl = body.querySelector('.traditions-canon-name');
  if (canonNameEl) {
    canonNameEl.textContent = edition.canon
      ? `${edition.canon} (${canonBooks.length} books)`
      : `(${canonBooks.length} books)`;
  }
  const booksInCanon = (DATA.books_canonical || []).filter(b => canonSet.has(b.code));

  // Default-row checkboxes
  body.querySelectorAll('.tradition-cb-default').forEach(cb => {
    cb.checked = state.default.has(cb.dataset.tradition);
    cb.addEventListener('change', () => {
      if (cb.checked) state.default.add(cb.dataset.tradition);
      else state.default.delete(cb.dataset.tradition);
      markTraditionsDirty(box, state);
      onChange && onChange();
    });
  });

  function renderOverrides() {
    const list = body.querySelector('.traditions-overrides-list');
    list.innerHTML = '';
    const canonRank = new Map(booksInCanon.map((b, i) => [b.code, i]));
    const codes = [...state.perBook.keys()]
      .filter(c => canonSet.has(c))
      .sort((a, b) => canonRank.get(a) - canonRank.get(b));

    body.querySelector('.traditions-overrides-count').textContent =
      `${codes.length} customized of ${booksInCanon.length}`;

    if (codes.length === 0) {
      list.innerHTML = `<p class="text-xs text-slate-400 italic px-1">
        no per-book overrides yet — every book uses the default above.
        Use the dropdown to customize a specific book.
      </p>`;
    } else {
      for (const code of codes) {
        const title = booksInCanon.find(b => b.code === code)?.title || code;
        const traditions = state.perBook.get(code) || new Set();
        const row = document.createElement('div');
        row.className = 'traditions-override-row flex flex-wrap items-center gap-3 p-2 bg-white border border-slate-200 rounded';
        row.dataset.book = code;
        row.innerHTML = `
          <div class="flex items-baseline gap-2 min-w-48">
            <span class="font-mono text-xs text-slate-400 w-12">${code}</span>
            <span class="text-sm font-medium truncate">${escapeAttr(title)}</span>
          </div>
          <div class="flex flex-wrap gap-3 flex-1">
            ${(DATA.traditions || []).map(T => `
              <label class="text-sm flex items-center gap-1">
                <input type="checkbox" class="tradition-cb-book" data-tradition="${T.id}"
                  ${traditions.has(T.id) ? 'checked' : ''}>
                ${escapeAttr(T.label)}
              </label>
            `).join('')}
          </div>
          <button type="button" class="traditions-remove-override text-slate-400 hover:text-red-600 px-1" title="revert to default — remove this override">×</button>
        `;
        row.querySelectorAll('.tradition-cb-book').forEach(cb => {
          cb.addEventListener('change', () => {
            const set = state.perBook.get(code);
            if (cb.checked) set.add(cb.dataset.tradition);
            else set.delete(cb.dataset.tradition);
            markTraditionsDirty(box, state);
            onChange && onChange();
          });
        });
        row.querySelector('.traditions-remove-override').addEventListener('click', () => {
          state.perBook.delete(code);
          renderOverrides();
          renderAddBookSelect();
          markTraditionsDirty(box, state);
          onChange && onChange();
        });
        list.appendChild(row);
      }
    }
  }

  function renderAddBookSelect() {
    const sel = body.querySelector('.traditions-add-book-select');
    const customized = new Set(state.perBook.keys());
    const options = booksInCanon
      .filter(b => !customized.has(b.code))
      .map(b => `<option value="${b.code}">${b.code} — ${escapeAttr(b.title)}</option>`)
      .join('');
    sel.innerHTML = `<option value="">+ add a book to customize…</option>${options}`;
  }

  body.querySelector('.traditions-add-book-select').addEventListener('change', (ev) => {
    const code = ev.target.value;
    if (!code) return;
    state.perBook.set(code, new Set(state.default));
    renderOverrides();
    renderAddBookSelect();
    ev.target.value = '';
    markTraditionsDirty(box, state);
    onChange && onChange();
  });

  body.querySelector('.traditions-bulk-clear').addEventListener('click', () => {
    if (state.perBook.size === 0) return;
    state.perBook.clear();
    renderOverrides();
    renderAddBookSelect();
    markTraditionsDirty(box, state);
    onChange && onChange();
  });

  renderOverrides();
  renderAddBookSelect();
  markTraditionsDirty(box, state);
}

function markTraditionsDirty(box, state) {
  const o = state.original;
  const sameSet = (a, b) => a.size === b.size && [...a].every(x => b.has(x));
  let dirty = false;
  if (!sameSet(state.default, o.default)) dirty = true;
  if (state.perBook.size !== o.perBook.size) dirty = true;
  if (!dirty) {
    for (const [code, traditions] of state.perBook) {
      const orig = o.perBook.get(code);
      if (!orig || !sameSet(traditions, orig)) { dirty = true; break; }
    }
  }
  box.dataset.traditionsDirty = dirty ? '1' : '0';
}

// Phase ν.5 — shared payload builder. Used by both saveEdition()
// and previewEdition() so the two compute identical payloads by
// construction. Returns an object containing only fields that have
// changed from their original (data-field originals + popup-language
// dirty flag). Empty object means no changes.
function buildCustomizePayload(box) {
  const payload = {};
  box.querySelectorAll('input, select').forEach(i => {
    // Skip the popup-language section's checkboxes; those are
    // collected via box.popupLangsState below.
    if (!i.dataset.field) return;
    const cur = i.type === 'checkbox' ? i.checked : i.value;
    const orig = i.dataset.original;
    const curStr = i.type === 'checkbox' ? String(cur) : cur;
    if (curStr !== orig) {
      payload[i.dataset.field] = cur;
    }
  });
  // Phase ν.2.7-B — include popup-language state if it changed
  if (box.dataset.popupLangsDirty === '1' && box.popupLangsState) {
    const s = box.popupLangsState;
    payload.popup_languages_default = [...s.default];
    payload.popup_languages_per_book = Object.fromEntries(
      [...s.perBook].map(([k, v]) => [k, [...v]])
    );
  }
  // Phase ψ.8.3 + ψ.8.4 — include traditions state if the section changed
  if (box.dataset.traditionsDirty === '1' && box.traditionsState) {
    const s = box.traditionsState;
    payload.traditions_default = [...s.default];
    payload.traditions_per_book = Object.fromEntries(
      [...s.perBook].map(([k, v]) => [k, [...v]])
    );
  }
  return payload;
}

async function saveEdition(box) {
  const id = box.dataset.edition;
  const payload = buildCustomizePayload(box);
  if (Object.keys(payload).length === 0) return;
  const status = box.querySelector('.ed-status');
  const btn = box.querySelector('.ed-save');
  const previewBtn = box.querySelector('.ed-preview');
  status.innerHTML = '<span class="text-slate-500">saving…</span>';
  try {
    const r = await fetch(`/api/edition-meta/${encodeURIComponent(id)}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    const result = await r.json();
    if (!r.ok || result.error) {
      status.innerHTML = `<span class="text-red-600">✗ ${result.error}</span>`;
      return;
    }
    status.innerHTML = '<span class="text-emerald-700">✓ saved</span>';
    box.classList.remove('dirty');
    box.classList.add('saved');
    setTimeout(() => box.classList.remove('saved'), 1200);
    btn.disabled = true;
    btn.classList.add('opacity-50');
    // ν.2.9 — clear the save-pending badge after a successful save
    const badge = btn.querySelector('.ed-save-count');
    if (badge) badge.classList.add('hidden');
    // Phase ν.5 — also disable the preview button (no changes left)
    if (previewBtn) {
      previewBtn.disabled = true;
      previewBtn.classList.add('opacity-50');
    }
    box.querySelectorAll('input, select').forEach(i => {
      i.dataset.original = i.type === 'checkbox' ? String(i.checked) : i.value;
    });
    // Re-baseline popup-language original snapshot
    if (box.popupLangsState) {
      const s = box.popupLangsState;
      s.original = {
        default: new Set(s.default),
        perBook: new Map([...s.perBook].map(([k, v]) => [k, new Set(v)])),
      };
      box.dataset.popupLangsDirty = '0';
    }
    // Phase ψ.8.3 + ψ.8.4 — re-baseline traditions snapshot
    if (box.traditionsState) {
      const s = box.traditionsState;
      s.original = {
        default: new Set(s.default),
        perBook: new Map([...s.perBook].map(([k, v]) => [k, new Set(v)])),
      };
      box.dataset.traditionsDirty = '0';
    }
  } catch (e) {
    status.innerHTML = `<span class="text-red-600">✗ ${e.message}</span>`;
  }
}

// Phase ν.5 — change-impact preview. Build the same payload that
// saveEdition() would, ask the server for a structured diff via the
// (read-only) /api/edition-meta/<id>/preview endpoint, and render
// it in a modal. Confirm = call saveEdition; Cancel = close modal.
// Uses the ω.0.6 safeFetch wrapper for unified error surfacing.
async function previewEdition(box) {
  const id = box.dataset.edition;
  const payload = buildCustomizePayload(box);
  const status = box.querySelector('.ed-status');
  if (Object.keys(payload).length === 0) {
    status.innerHTML = '<span class="text-slate-500">no changes to preview</span>';
    return;
  }
  status.innerHTML = '<span class="text-slate-500">computing preview…</span>';
  try {
    // Prefer the ω.0.6 safeFetch wrapper if available; fall back to
    // raw fetch for resilience if the prelude failed to load.
    const url = `/api/edition-meta/${encodeURIComponent(id)}/preview`;
    let data;
    if (window.ebible && window.ebible.safeFetch) {
      data = await window.ebible.safeFetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload),
      });
    } else {
      const r = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload),
      });
      data = await r.json();
      if (!r.ok || (data && data.error)) {
        const msg = (data && data.error) ? data.error : `${r.status} ${r.statusText}`;
        status.innerHTML = `<span class="text-red-600">✗ ${msg}</span>`;
        return;
      }
    }
    status.textContent = '';
    showCustomizePreviewModal(box, data);
  } catch (e) {
    status.innerHTML = `<span class="text-red-600">✗ ${e.message}</span>`;
  }
}

// Render the preview modal. Same shape as the publisher console's
// modal: backdrop with a centered card, before/after table, Cancel
// + "Save these changes" buttons; backdrop click and × close.
// Naming distinguishes from publisher's showPreviewModal so the two
// can coexist if customize ever embeds publisher widgets.
// Phase ω.1 — Version history modal. Lists backup snapshots for
// editions.yaml and lets the publisher restore one. The /customize
// console reflects ALL editions, so this surface lists snapshots
// of editions.yaml itself rather than per-edition slices (which
// don't exist in the backup format).
async function openHistoryModal(box) {
  // Remove any existing modal so multiple clicks don't stack
  document.querySelectorAll('.ed-history-backdrop').forEach(el => el.remove());

  const escape = window.ebible && window.ebible.escapeHtml
    ? window.ebible.escapeHtml
    : (s) => String(s == null ? '' : s).replace(/[&<>"']/g,
        c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  // List snapshots for editions.yaml (the file driving this console)
  const file = 'editions.yaml';
  let data;
  try {
    const r = await fetch('/api/backups?file=' + encodeURIComponent(file));
    data = await r.json();
    if (!r.ok) {
      alert('Could not load history: ' + (data.message || r.status));
      return;
    }
  } catch (e) {
    alert('Network error loading history: ' + e.message);
    return;
  }

  const fmtBytes = (n) => {
    if (n < 1024) return n + ' B';
    if (n < 1048576) return (n / 1024).toFixed(1) + ' KB';
    return (n / 1048576).toFixed(2) + ' MB';
  };

  const snapshots = data.snapshots || [];
  const rowsHtml = snapshots.length === 0
    ? '<p class="text-slate-500 italic text-sm">No backups yet for this file.</p>'
    : `<table class="w-full text-sm">
        <thead><tr class="border-b text-xs uppercase text-slate-500">
          <th class="text-left py-1 pr-2">Timestamp (UTC)</th>
          <th class="text-right py-1 pr-2">Size</th>
          <th class="text-right py-1"></th>
        </tr></thead>
        <tbody>
        ${snapshots.map(s => `
          <tr class="border-b border-slate-100" data-snapshot-id="${escape(s.id)}">
            <td class="py-1.5 pr-2 font-mono text-xs">${escape(s.iso_time)}</td>
            <td class="py-1.5 pr-2 text-right text-slate-500">${escape(fmtBytes(s.size_bytes))}</td>
            <td class="py-1.5 text-right">
              <button class="ed-history-restore text-xs px-2 py-0.5 rounded border border-amber-400 hover:bg-amber-50 text-amber-700">Restore</button>
            </td>
          </tr>`).join('')}
        </tbody>
      </table>`;

  const backdrop = document.createElement('div');
  backdrop.className = 'ed-history-backdrop fixed inset-0 bg-black/40 flex items-center justify-center z-50';
  backdrop.innerHTML = `
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[85vh] overflow-hidden flex flex-col">
      <div class="px-5 py-3 border-b border-slate-200 flex items-center justify-between">
        <h3 class="font-semibold">Version history — ${escape(file)}</h3>
        <button class="ed-history-close text-slate-400 hover:text-slate-600 text-xl leading-none" type="button">×</button>
      </div>
      <div class="px-5 py-4 overflow-y-auto">
        <p class="text-xs text-slate-500 mb-3">
          ${snapshots.length} snapshot${snapshots.length === 1 ? '' : 's'} available · newest first
          · Restore creates a backup of the current state first (so the operation is reversible).
        </p>
        ${rowsHtml}
      </div>
      <div class="px-5 py-3 border-t border-slate-200 flex justify-end gap-2 bg-slate-50">
        <button class="ed-history-close text-sm px-4 py-1.5 rounded border border-slate-300 hover:border-slate-500" type="button">Close</button>
      </div>
    </div>
  `;
  document.body.appendChild(backdrop);

  // Close handlers
  backdrop.querySelectorAll('.ed-history-close').forEach(b => {
    b.addEventListener('click', () => backdrop.remove());
  });
  backdrop.addEventListener('click', ev => {
    if (ev.target === backdrop) backdrop.remove();
  });

  // Restore button handlers — confirm before doing anything
  backdrop.querySelectorAll('.ed-history-restore').forEach(b => {
    b.addEventListener('click', async () => {
      const row = b.closest('[data-snapshot-id]');
      const snapshotId = row && row.dataset.snapshotId;
      if (!snapshotId) return;
      const ok = confirm(
        'Restore this snapshot?\\n\\n' +
        'The current state of ' + file + ' will be backed up first ' +
        '(so this is reversible), then replaced with the snapshot from ' +
        (row.querySelector('.font-mono') ? row.querySelector('.font-mono').textContent : 'the selected timestamp') +
        '.\\n\\nAfter restore, reload the page to see the changes.'
      );
      if (!ok) return;
      b.disabled = true;
      b.textContent = 'restoring…';
      try {
        const r = await fetch('/api/backups/restore', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({file, snapshot_id: snapshotId}),
        });
        const result = await r.json();
        if (!r.ok || result.error) {
          b.disabled = false;
          b.textContent = 'Restore';
          alert('Restore failed: ' + (result.message || result.error || r.status));
          return;
        }
        b.textContent = '✓ restored';
        b.classList.remove('border-amber-400', 'text-amber-700');
        b.classList.add('border-emerald-400', 'text-emerald-700');
        // Quick fade then reload — the page state needs to refresh
        setTimeout(() => { window.location.reload(); }, 800);
      } catch (e) {
        b.disabled = false;
        b.textContent = 'Restore';
        alert('Network error: ' + e.message);
      }
    });
  });
}

function showCustomizePreviewModal(box, data) {
  // Remove any existing modal so multiple clicks don't stack
  document.querySelectorAll('.ed-preview-backdrop').forEach(el => el.remove());

  const escHtml = s => String(s || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  const fmtValue = v => {
    if (v === null || v === undefined || v === '') return '<span class="text-slate-400 italic">empty</span>';
    if (typeof v === 'boolean') return v
      ? '<span class="text-emerald-700 font-medium">yes</span>'
      : '<span class="text-slate-500">no</span>';
    if (Array.isArray(v)) return v.length === 0
      ? '<span class="text-slate-400 italic">empty list</span>'
      : `<code class="text-xs">${escHtml(JSON.stringify(v))}</code>`;
    if (typeof v === 'object') return `<code class="text-xs">${escHtml(JSON.stringify(v))}</code>`;
    return `<code>${escHtml(String(v))}</code>`;
  };

  const changes = data.changes || [];
  const changesHtml = changes.length === 0
    ? '<p class="text-slate-500 italic">No changes to commit. Save will be a no-op.</p>'
    : `<table class="w-full text-sm">
        <thead><tr class="border-b text-xs uppercase text-slate-500">
          <th class="text-left py-1 pr-2">Field</th>
          <th class="text-left py-1 pr-2">Current</th>
          <th class="text-left py-1">Proposed</th>
        </tr></thead>
        <tbody>
        ${changes.map(c => `
          <tr class="border-b border-slate-100">
            <td class="py-1.5 pr-2 font-mono text-xs">${escHtml(c.field)}</td>
            <td class="py-1.5 pr-2">${fmtValue(c.before)}</td>
            <td class="py-1.5 text-emerald-700">${fmtValue(c.after)}</td>
          </tr>`).join('')}
        </tbody>
      </table>`;

  const unknownHtml = (data.unknown_fields && data.unknown_fields.length > 0)
    ? `<div class="mt-3 p-2 bg-amber-50 border border-amber-200 rounded text-xs">
        <strong>Unknown fields (will be silently ignored on save):</strong>
        <code class="ml-1">${data.unknown_fields.map(escHtml).join(', ')}</code>
      </div>`
    : '';

  const backdrop = document.createElement('div');
  backdrop.className = 'ed-preview-backdrop fixed inset-0 bg-black/40 flex items-center justify-center z-50';
  backdrop.innerHTML = `
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[85vh] overflow-hidden flex flex-col">
      <div class="px-5 py-3 border-b border-slate-200 flex items-center justify-between">
        <h3 class="font-semibold">Preview save — ${escHtml(data.edition_id || box.dataset.edition)}</h3>
        <button class="ed-preview-close text-slate-400 hover:text-slate-600 text-xl leading-none" type="button">×</button>
      </div>
      <div class="px-5 py-4 overflow-y-auto">
        <p class="text-xs text-slate-500 mb-3">
          ${changes.length} change${changes.length === 1 ? '' : 's'} to commit
          · ${(data.unchanged || []).length} unchanged field${(data.unchanged || []).length === 1 ? '' : 's'}
        </p>
        ${changesHtml}
        ${unknownHtml}
      </div>
      <div class="px-5 py-3 border-t border-slate-200 flex justify-end gap-2 bg-slate-50">
        <button class="ed-preview-close text-sm px-4 py-1.5 rounded border border-slate-300 hover:border-slate-500" type="button">Cancel</button>
        <button class="ed-preview-confirm text-sm px-4 py-1.5 rounded bg-blue-600 hover:bg-blue-700 text-white ${data.no_changes ? 'opacity-50 cursor-not-allowed' : ''}" ${data.no_changes ? 'disabled' : ''} type="button">Save these changes</button>
      </div>
    </div>
  `;
  document.body.appendChild(backdrop);
  // Close handlers (× and Cancel buttons)
  backdrop.querySelectorAll('.ed-preview-close').forEach(b => {
    b.addEventListener('click', () => backdrop.remove());
  });
  // Backdrop click closes (but click inside the card doesn't)
  backdrop.addEventListener('click', ev => {
    if (ev.target === backdrop) backdrop.remove();
  });
  // Confirm = proceed with the actual save
  const confirmBtn = backdrop.querySelector('.ed-preview-confirm');
  if (confirmBtn && !data.no_changes) {
    confirmBtn.addEventListener('click', () => {
      backdrop.remove();
      saveEdition(box);
    });
  }
}

function renderCategories() {
  const tb = document.getElementById('cat-body');
  tb.innerHTML = DATA.categories.map(c => `
    <tr class="border-t border-slate-100" data-cat="${c.id}">
      <td class="px-3 py-2 font-mono text-xs text-slate-500">${c.id}</td>
      <td class="px-3 py-2">
        <input class="symbol-input" data-field="symbol" value="${escapeAttr(c.symbol)}" maxlength="4">
      </td>
      <td class="px-3 py-2">
        <input class="label-input w-72" data-field="label" value="${escapeAttr(c.label)}" maxlength="60">
      </td>
      <td class="px-3 py-2 text-right">
        <button class="cat-save text-xs px-2 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white opacity-50" disabled>Save</button>
        <span class="cat-status text-xs ml-2"></span>
      </td>
    </tr>
  `).join('');
  // Wire change listeners
  tb.querySelectorAll('tr[data-cat]').forEach(tr => {
    const inputs = tr.querySelectorAll('input');
    const btn = tr.querySelector('.cat-save');
    inputs.forEach(inp => {
      const original = inp.value;
      inp.dataset.original = original;
      inp.addEventListener('input', () => {
        let dirty = false;
        inputs.forEach(i => { if (i.value !== i.dataset.original) dirty = true; });
        btn.disabled = !dirty;
        btn.classList.toggle('opacity-50', !dirty);
        tr.classList.toggle('dirty', dirty);
      });
    });
    btn.addEventListener('click', () => saveCategory(tr));
  });
}

function renderKinds() {
  // Group kinds by category, in category sort order
  const catsById = Object.fromEntries(DATA.categories.map(c => [c.id, c]));
  const grouped = {};
  for (const k of DATA.kinds) {
    (grouped[k.category] = grouped[k.category] || []).push(k);
  }
  const ordered = DATA.categories.filter(c => grouped[c.id]);
  const wrap = document.getElementById('kinds-body');
  wrap.innerHTML = ordered.map(c => `
    <details class="mb-2 border border-slate-200 rounded">
      <summary class="cursor-pointer px-3 py-2 bg-slate-50 select-none">
        <span class="symbol mr-2">${c.symbol}</span>
        <span class="font-semibold">${escapeAttr(c.label)}</span>
        <span class="text-xs text-slate-500 ml-2">(${grouped[c.id].length} kinds)</span>
      </summary>
      <table class="w-full text-sm">
        <tbody>
          ${grouped[c.id].map(k => `
            <tr class="border-t border-slate-100" data-kind="${k.code}">
              <td class="px-3 py-1.5 font-mono text-xs text-slate-500 w-48">${k.code}</td>
              <td class="px-3 py-1.5">
                <input class="label-input w-96" data-field="label" value="${escapeAttr(k.label)}" maxlength="60">
              </td>
              <td class="px-3 py-1.5 text-right">
                <button class="kind-save text-xs px-2 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white opacity-50" disabled>Save</button>
                <span class="kind-status text-xs ml-2"></span>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </details>
  `).join('');
  // Wire change listeners
  wrap.querySelectorAll('tr[data-kind]').forEach(tr => {
    const inputs = tr.querySelectorAll('input');
    const btn = tr.querySelector('.kind-save');
    inputs.forEach(inp => {
      const original = inp.value;
      inp.dataset.original = original;
      inp.addEventListener('input', () => {
        let dirty = false;
        inputs.forEach(i => { if (i.value !== i.dataset.original) dirty = true; });
        btn.disabled = !dirty;
        btn.classList.toggle('opacity-50', !dirty);
        tr.classList.toggle('dirty', dirty);
      });
    });
    btn.addEventListener('click', () => saveKind(tr));
  });
}

async function saveCategory(tr) {
  const id = tr.dataset.cat;
  const payload = {};
  tr.querySelectorAll('input').forEach(i => {
    if (i.value !== i.dataset.original) payload[i.dataset.field] = i.value;
  });
  await postSave(`/api/category/${encodeURIComponent(id)}`, payload, tr, '.cat-status', '.cat-save', renderCategories);
}

async function saveKind(tr) {
  const code = tr.dataset.kind;
  const payload = {};
  tr.querySelectorAll('input').forEach(i => {
    if (i.value !== i.dataset.original) payload[i.dataset.field] = i.value;
  });
  await postSave(`/api/kind/${encodeURIComponent(code)}`, payload, tr, '.kind-status', '.kind-save', null);
}

async function postSave(url, payload, tr, statusSel, btnSel, refreshFn) {
  const status = tr.querySelector(statusSel);
  const btn = tr.querySelector(btnSel);
  status.innerHTML = '<span class="text-slate-500">saving…</span>';
  try {
    const r = await fetch(url, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    const result = await r.json();
    if (!r.ok || result.error) {
      status.innerHTML = `<span class="text-red-600">✗ ${result.error}</span>`;
      return;
    }
    status.innerHTML = '<span class="text-emerald-700">✓ saved</span>';
    tr.classList.remove('dirty');
    tr.classList.add('saved');
    setTimeout(() => tr.classList.remove('saved'), 1200);
    btn.disabled = true;
    btn.classList.add('opacity-50');
    // Update originals
    tr.querySelectorAll('input').forEach(i => i.dataset.original = i.value);
    // Re-fetch and re-render so dependent UI bits (symbol in category headers) update
    if (refreshFn) {
      const fresh = await fetch('/api/customize').then(r => r.json());
      DATA = fresh;
      refreshFn();
      renderKinds();
    }
  } catch (e) {
    status.innerHTML = `<span class="text-red-600">✗ ${e.message}</span>`;
  }
}

function escapeAttr(s) {
  return (s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
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


# ψ.15: substitute the canonical nav link list from _design.CONSOLES.
CUSTOMIZE_HTML = CUSTOMIZE_HTML.replace(
    "    <!-- HEADER_NAV_LINKS -->",
    HEADER_NAV_LINKS("/customize"),
)
CUSTOMIZE_HTML = CUSTOMIZE_HTML.replace(
    "<!-- BUYER_ARC_POLISH_CSS -->",
    BUYER_ARC_POLISH_CSS,
)

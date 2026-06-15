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
    apply_design_system,
)

__all__ = ["CUSTOMIZE_HTML", "HEADER_NAV_LINKS", "BUYER_ARC_POLISH_CSS"]

CUSTOMIZE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>YHWH Ya' Way · Customize</title>
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
  /* ν.2.8 — visual section boundaries within an edition card.
     Each <section class="ed-section"> gets a thin top border so the
     identity row, metadata row, and accordion zones read as
     distinct chunks instead of one undifferentiated grid. */
  .ed-section { padding-top: 0.75rem; padding-bottom: 0.5rem;
                border-top: 1px solid #e2e8f0; }
  .ed-section:first-of-type { border-top: 0; padding-top: 0; }
  .ed-section-label { display: block; font-size: 0.65rem;
                      text-transform: uppercase; letter-spacing: 0.05em;
                      color: #94a3b8; margin-bottom: 0.5rem;
                      font-weight: 600; }
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
      <h2 class="font-semibold">Editions <span id="editions-count" class="text-xs text-slate-500 font-normal"></span></h2>
      <p class="text-xs text-slate-500">title · audience · verse-popup behavior · custom verse marker</p>
    </div>
    <div id="ed-body" class="divide-y divide-slate-100"></div>
  </section>

  <section class="bg-white rounded-lg shadow-sm border border-slate-200 mb-6">
    <div class="px-4 py-3 border-b border-slate-200">
      <h2 class="font-semibold">Categories <span id="categories-count" class="text-xs text-slate-500 font-normal"></span></h2>
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
      <h2 class="font-semibold">Kinds <span id="kinds-count" class="text-xs text-slate-500 font-normal"></span></h2>
      <p class="text-xs text-slate-500">label-level customization per kind · symbol inherits from category by default</p>
    </div>
    <div id="kinds-body" class="p-2"></div>
  </section>

  <div id="loading" class="text-center text-slate-400 py-20">loading …</div>
</main>

<!-- ψ.1.1 — preview modal. Hidden by default; opened by per-
     edition Preview buttons in the identity section. Renders the
     ψ.1.0 api_preview output via iframe srcdoc=. -->
<div id="psi11-preview-modal" class="hidden fixed inset-0 z-50 bg-black/50 flex items-center justify-center px-4 py-6">
  <div class="bg-white rounded-lg shadow-2xl border border-slate-200 max-w-5xl w-full max-h-[95vh] flex flex-col">
    <div class="px-5 py-3 border-b border-slate-200 flex items-center gap-3 flex-wrap">
      <h3 class="text-lg font-bold flex-1">
        Preview: <span id="psi11-preview-title" class="text-slate-700"></span>
      </h3>
      <label class="text-xs flex items-center gap-1.5">
        <span>book:</span>
        <select id="psi11-preview-book" class="label-input"></select>
      </label>
      <label class="text-xs flex items-center gap-1.5">
        <span>chapter:</span>
        <input id="psi11-preview-chapter" type="number" min="1" value="1" class="symbol-input" style="width:4em;">
      </label>
      <button id="psi11-preview-refresh" type="button" class="px-2 py-1 rounded border border-slate-300 text-xs hover:bg-slate-50">↻ Refresh</button>
      <button id="psi11-preview-close" type="button" class="text-slate-400 hover:text-slate-700 text-2xl leading-none ml-2" aria-label="Close">×</button>
    </div>
    <div class="px-5 py-2 text-xs text-slate-500 bg-slate-50 border-b border-slate-200 flex items-center gap-3 flex-wrap">
      <span id="psi11-preview-status">loading…</span>
      <span class="text-slate-400">·</span>
      <span class="italic">Showing the persisted edition state. Save edits to see them in the preview.</span>
    </div>
    <iframe id="psi11-preview-iframe" class="flex-1 w-full bg-white" sandbox="allow-same-origin" style="border:0; min-height:60vh;"></iframe>
  </div>
</div>

<script>
let DATA = null;

async function init() {
  const r = await fetch('/api/customize');
  DATA = await r.json();
  document.getElementById('loading').classList.add('hidden');
  renderEditions();
  renderCategories();
  renderKinds();
  // ν.2.8 — update section counts dynamically (was hard-coded
  // (5) / (14) / (63) — broke after ψ.7-A added 4 editions)
  const setCount = (id, n, suffix) => {
    const el = document.getElementById(id);
    if (el) el.textContent = '(' + n + (suffix ? ' ' + suffix : '') + ')';
  };
  setCount('editions-count',   (DATA.editions   || []).length, '');
  setCount('categories-count', (DATA.categories || []).length, '');
  setCount('kinds-count',      (DATA.kinds      || []).length, '— grouped by category');
  // ψ.1.1 — wire Preview-modal handlers (one-time after first render)
  initPsi11Preview();
}

// ─── ψ.1.1 — preview modal ───────────────────────────────────
let PSI11_EDITION = null;  // currently-previewed edition id

function initPsi11Preview() {
  // Delegated click handler for the per-edition Preview buttons
  // (rebound on every renderEditions; idempotent via dataset flag).
  const wrap = document.getElementById('ed-body');
  if (wrap && !wrap.dataset.psi11Bound) {
    wrap.dataset.psi11Bound = '1';
    wrap.addEventListener('click', (ev) => {
      const btn = ev.target.closest('.psi11-preview-btn');
      if (!btn) return;
      ev.preventDefault();
      openPsi11Preview(btn.dataset.edition);
    });
  }
  const closeBtn = document.getElementById('psi11-preview-close');
  if (closeBtn && !closeBtn.dataset.bound) {
    closeBtn.dataset.bound = '1';
    closeBtn.addEventListener('click', closePsi11Preview);
  }
  const refreshBtn = document.getElementById('psi11-preview-refresh');
  if (refreshBtn && !refreshBtn.dataset.bound) {
    refreshBtn.dataset.bound = '1';
    refreshBtn.addEventListener('click', refreshPsi11Preview);
  }
  const bookSel = document.getElementById('psi11-preview-book');
  const chInp = document.getElementById('psi11-preview-chapter');
  if (bookSel && !bookSel.dataset.bound) {
    bookSel.dataset.bound = '1';
    bookSel.addEventListener('change', refreshPsi11Preview);
  }
  if (chInp && !chInp.dataset.bound) {
    chInp.dataset.bound = '1';
    let timer = null;
    chInp.addEventListener('input', () => {
      // Debounce 300ms — typing "12" shouldn't fetch ch 1 then ch 12.
      if (timer) clearTimeout(timer);
      timer = setTimeout(refreshPsi11Preview, 300);
    });
  }
  // ESC closes the modal
  document.addEventListener('keydown', (ev) => {
    if (ev.key !== 'Escape') return;
    const modal = document.getElementById('psi11-preview-modal');
    if (modal && !modal.classList.contains('hidden')) {
      closePsi11Preview();
    }
  });
}

function openPsi11Preview(edition_id) {
  if (!edition_id) return;
  PSI11_EDITION = edition_id;
  const ed = (DATA.editions || []).find(e => e.id === edition_id);
  if (!ed) return;
  // Update title
  const titleEl = document.getElementById('psi11-preview-title');
  if (titleEl) {
    titleEl.textContent = ed.title || edition_id;
  }
  // Populate book picker from the edition's canon (DATA.edition_canon_books)
  const bookSel = document.getElementById('psi11-preview-book');
  const canonBooks = (DATA.edition_canon_books || {})[edition_id] || [];
  const booksByCode = {};
  for (const b of (DATA.books_canonical || [])) booksByCode[b.code] = b;
  bookSel.innerHTML = canonBooks.map(code => {
    const b = booksByCode[code] || {code, title: code};
    return `<option value="${code}">${escapeAttr(b.title || code)}</option>`;
  }).join('');
  // Default: first canon book (Genesis if applicable, else first)
  // Or persisted last-used per edition via localStorage.
  const lastKey = 'psi11-last-' + edition_id;
  let lastVal;
  try { lastVal = localStorage.getItem(lastKey); } catch (_) { lastVal = null; }
  if (lastVal) {
    const [bc, ch] = lastVal.split(':');
    if (canonBooks.includes(bc)) {
      bookSel.value = bc;
      const chInp = document.getElementById('psi11-preview-chapter');
      if (chInp && ch) chInp.value = ch;
    }
  } else {
    // Default to "jhn" (Gospel of John ch 1) if available — short
    // chapters, recognizable opening, broad-translation coverage.
    if (canonBooks.includes('jhn')) bookSel.value = 'jhn';
    const chInp = document.getElementById('psi11-preview-chapter');
    if (chInp) chInp.value = 1;
  }
  document.getElementById('psi11-preview-modal').classList.remove('hidden');
  refreshPsi11Preview();
}

function closePsi11Preview() {
  PSI11_EDITION = null;
  document.getElementById('psi11-preview-modal').classList.add('hidden');
  const iframe = document.getElementById('psi11-preview-iframe');
  if (iframe) iframe.srcdoc = '';
  const status = document.getElementById('psi11-preview-status');
  if (status) status.textContent = '';
}

async function refreshPsi11Preview() {
  if (!PSI11_EDITION) return;
  const bookSel = document.getElementById('psi11-preview-book');
  const chInp = document.getElementById('psi11-preview-chapter');
  const status = document.getElementById('psi11-preview-status');
  const iframe = document.getElementById('psi11-preview-iframe');
  if (!bookSel || !chInp || !iframe) return;
  const bookCode = bookSel.value;
  const ch = parseInt(chInp.value, 10) || 1;
  if (!bookCode) {
    status.textContent = 'pick a book to preview';
    return;
  }
  // Persist last-used per edition
  try { localStorage.setItem('psi11-last-' + PSI11_EDITION, bookCode + ':' + ch); } catch (_) {}
  status.textContent = 'loading ' + bookCode + ' ' + ch + '…';
  try {
    const r = await fetch('/api/preview/' + encodeURIComponent(PSI11_EDITION)
                          + '/' + encodeURIComponent(bookCode)
                          + '/' + encodeURIComponent(ch));
    const data = await r.json();
    if (!r.ok || data.status !== 'ok') {
      const msg = (data.message || data.error || 'preview failed');
      status.innerHTML = '<span class="text-red-700">✗ ' + escapeAttr(msg) + '</span>';
      return;
    }
    iframe.srcdoc = data.html;
    status.textContent = bookCode + ' ' + ch + ' · '
      + data.verse_count + ' verses · '
      + data.notes_shown + ' notes shown';
  } catch (e) {
    status.innerHTML = '<span class="text-red-700">✗ network error: '
      + escapeAttr(String(e && e.message || e)) + '</span>';
  }
}

function renderEditions() {
  const wrap = document.getElementById('ed-body');
  wrap.innerHTML = DATA.editions.map(e => `
    <div class="p-4" data-edition="${e.id}">
      <section class="ed-section ed-identity">
        <span class="ed-section-label">Identity &amp; appearance</span>
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
            <button type="button" class="psi11-preview-btn px-2 py-1 rounded border border-blue-300 bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-medium" data-edition="${e.id}" title="ψ.1.1 — preview one chapter rendered per this edition's spec">
              👁 Preview
            </button>
          </div>
        </div>
      </section>
      <section class="ed-section ed-meta">
        <span class="ed-section-label">Metadata</span>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
          <input class="label-input" data-field="short_title" value="${escapeAttr(e.short_title)}" maxlength="100" placeholder="short title">
          <input class="label-input md:col-span-2" data-field="target_audience" value="${escapeAttr(e.target_audience)}" maxlength="500" placeholder="target audience">
          <input class="label-input md:col-span-2" data-field="notes" value="${escapeAttr(e.notes)}" maxlength="500" placeholder="editorial notes">
          <textarea class="label-input md:col-span-2" data-field="dedication" maxlength="4000" placeholder="Dedication text (optional front-matter page)" rows="2">${escapeAttr(e.dedication||'')}</textarea>
        </div>
      </section>

      <details class="ed-identity-card mt-3 border border-slate-200 rounded bg-slate-50" data-edition-id="${e.id}">
        <summary class="px-3 py-2 cursor-pointer text-xs font-semibold uppercase tracking-wide text-slate-600 hover:bg-slate-100">
          Your edition's name &amp; notes
          <span class="text-slate-400 normal-case font-normal ml-2">
            the subtitle on the cover &amp; the note on your "Your Edition" page
          </span>
        </summary>
        <div class="identity-body px-3 pb-3 pt-2 space-y-3">
          <div>
            <span class="block mb-1 text-xs font-medium text-slate-700">Edition name
              <span class="text-slate-400 font-normal">— shows as the subtitle under "HOLY BIBLE" on the cover (leave blank for a cover with no subtitle)</span>
            </span>
            <!-- UI-only controls (no data-field). wireIdentityCard() syncs the
                 chosen/typed value into the hidden display_name field below,
                 which is the single source the save payload reads. Per-card
                 CLASSES (not ids) so the markup stays valid across cards. -->
            <select class="label-input w-full md:w-2/3 display-name-pick"
                    title="pick a name suggested from what you built, or choose Custom to type your own"></select>
            <input class="label-input w-full md:w-2/3 mt-2 display-name-custom hidden"
                   maxlength="48" placeholder="type your edition's name (max 48 characters)">
            <input type="hidden" data-field="display_name" class="display-name-value" value="${escapeAttr(e.display_name||'')}">
          </div>
          <div>
            <span class="block mb-1 text-xs font-medium text-slate-700">Notes
              <span class="text-slate-400 font-normal">— a short note shown on your "Your Edition" page (optional)</span>
            </span>
            <textarea class="label-input w-full edition-notes" data-field="description" maxlength="4000" rows="3"
                      placeholder="e.g. why you built this edition, who it's for, what makes it yours">${escapeAttr(e.description||'')}</textarea>
          </div>
        </div>
      </details>

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
              <span class="block mb-1 font-medium text-slate-700">Book title page</span>
              <select class="label-input w-full" data-field="title_page_style" title="how each book's title-page art is rendered">
                <option value="framed"     ${(e.title_page_style||'framed') === 'framed' ? 'selected' : ''}>framed · art plate above the title</option>
                <option value="full-bleed" ${e.title_page_style === 'full-bleed' ? 'selected' : ''}>full-bleed · art fills the page</option>
              </select>
            </label>
            <label class="text-xs">
              <span class="block mb-1 font-medium text-slate-700">Verse-popup layout</span>
              <select class="label-input w-full" data-field="verse_popup_style" title="how the original-language witnesses render inside a verse popup">
                <option value="cards" ${(e.verse_popup_style||'cards') === 'cards' ? 'selected' : ''}>cards · each witness in a tinted card</option>
                <option value="stack" ${e.verse_popup_style === 'stack' ? 'selected' : ''}>stack · flat, label above text</option>
              </select>
            </label>
            <label class="text-xs">
              <span class="block mb-1 font-medium text-slate-700">Note-popup layout</span>
              <select class="label-input w-full" data-field="note_popup_style" title="how a study note renders inside its popup">
                <option value="chip"  ${(e.note_popup_style||'chip') === 'chip' ? 'selected' : ''}>chip · category label as a tinted chip</option>
                <option value="pills" ${e.note_popup_style === 'pills' ? 'selected' : ''}>pills · cross-references as tappable pills</option>
              </select>
            </label>
            <label class="text-xs">
              <span class="block mb-1 font-medium text-slate-700">Note marker style</span>
              <select class="label-input w-full" data-field="marker_style" title="how each verse's notes are flagged in the running text">
                <option value="badge"   ${(e.marker_style||'badge') === 'badge' ? 'selected' : ''}>badge · one count per verse, tap for the list</option>
                <option value="numbers" ${e.marker_style === 'numbers' ? 'selected' : ''}>numbers · a superscript number per note</option>
              </select>
            </label>
            <label class="text-xs badge-style-row ${(e.marker_style||'badge') === 'badge' ? '' : 'hidden'}">
              <span class="block mb-1 font-medium text-slate-700">Study-note badge style</span>
              <select class="label-input w-full badge-style-select" data-field="marker_badge_style" title="how each verse's study-note badge looks in the running text (badge marker style only)">
                <option value="chip"        ${e.marker_badge_style === 'chip' ? 'selected' : ''}>chip · count in a bordered box</option>
                <option value="dagger"      ${e.marker_badge_style === 'dagger' ? 'selected' : ''}>dagger · † symbol only</option>
                <option value="dagger+count" ${e.marker_badge_style === 'dagger+count' ? 'selected' : ''}>dagger+count · † then count (recommended on Kobo)</option>
                <option value="asterisk"    ${e.marker_badge_style === 'asterisk' ? 'selected' : ''}>asterisk · * symbol only</option>
                <option value="lozenge"     ${e.marker_badge_style === 'lozenge' ? 'selected' : ''}>lozenge · ◇ symbol only</option>
                <option value="lozenge+count" ${e.marker_badge_style === 'lozenge+count' ? 'selected' : ''}>lozenge+count · ◇ then count</option>
                <option value="dot"         ${e.marker_badge_style === 'dot' ? 'selected' : ''} data-eink-unsafe="1">dot · • symbol only (not for Kobo)</option>
                <option value="glyph+count" ${e.marker_badge_style === 'glyph+count' ? 'selected' : ''}>glyph+count · ◈ then count (Apple Books / tablet)</option>
              </select>
              <span class="block text-slate-400 mt-1 badge-style-hint">◈ never renders on Kobo — pick dagger or lozenge for e-ink.</span>
            </label>
            <label class="text-xs flex items-center gap-1.5 cursor-pointer select-none" title="Drop a note's repeated kind label (e.g. the 'Hebrew.' prefix on every word study) when it merely restates the category. Lossless. Badge marker style only.">
              <input type="checkbox" data-field="note_attribution_dedup" ${e.note_attribution_dedup ? 'checked' : ''}>
              de-duplicate note labels
            </label>
            <label class="text-xs flex items-center gap-1.5 cursor-pointer select-none" title="Group a verse's notes into a category → source → note cascade (one category header + one source byline each) instead of a flat list. Lossless. Badge marker style only.">
              <input type="checkbox" data-field="note_group_by_category" ${e.note_group_by_category ? 'checked' : ''}>
              group notes by category &amp; source
            </label>
            <label class="text-xs flex items-center gap-1.5 cursor-pointer select-none" title="Merge a verse's topical-index notes (Nave's + Torrey) into one Topics line, de-duplicating repeated terms. Lossless. Badge marker style only.">
              <input type="checkbox" data-field="note_topic_dedup" ${e.note_topic_dedup ? 'checked' : ''}>
              merge topical-index entries
            </label>
            <label class="text-xs">
              <span class="block mb-1 font-medium text-slate-700">Popup split cap (characters)</span>
              <input type="number" min="0" step="100" class="label-input w-full" data-field="note_popup_split_cap"
                     value="${e.note_popup_split_cap ?? ''}" placeholder="4400 (device-calibrated default)"
                     title="Kobo e-ink declines oversized note popups and jumps to the page top instead — verses whose merged popup strips to more chars than this split into several smaller popups (one ◈ badge each). Blank = the calibrated default (4,400); 0 = never split. Badge marker style only.">
            </label>
            <label class="text-xs">
              <span class="block mb-1 font-medium text-slate-700">Popup split cap (bytes)</span>
              <input type="number" min="0" step="500" class="label-input w-full" data-field="note_popup_split_byte_cap"
                     value="${e.note_popup_split_byte_cap ?? ''}" placeholder="8858 (device-calibrated default)"
                     title="Kobo measures a popup in serialized kepub bytes and refuses above ~8.9 KB — units whose estimated converted size exceeds this split further, even when the character cap passes (markup-dense notes inflate under Kobo's per-sentence wrapping). Blank = the calibrated default (8,858); 0 = off. Badge marker style only.">
            </label>
            <label class="text-xs">
              <span class="block mb-1 font-medium text-slate-700">Topical index source</span>
              <select class="label-input w-full" data-field="topical_index_source" title="which topical authority feeds the back-of-book Topical Index">
                <option value="both"   ${(e.topical_index_source||'both') === 'both' ? 'selected' : ''}>both · Nave's + Torrey, merged (N·T tags)</option>
                <option value="naves"  ${e.topical_index_source === 'naves' ? 'selected' : ''}>Nave's only</option>
                <option value="torrey" ${e.topical_index_source === 'torrey' ? 'selected' : ''}>Torrey only</option>
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
            <label class="text-xs">
              <span class="block mb-1 font-medium text-slate-700">Made for (reader target)</span>
              <select class="label-input w-full" data-field="target_reader" title="where the builder will read this edition — gates which optional reading features are offered (K-R2)">
                <option value="everywhere" ${(e.target_reader||'everywhere') === 'everywhere' ? 'selected' : ''}>🌍 Everywhere — safest build</option>
                <option value="eink"       ${e.target_reader === 'eink' ? 'selected' : ''}>📖 E-ink reader (Kobo — use the .kepub)</option>
                <option value="tablet"     ${e.target_reader === 'tablet' ? 'selected' : ''}>📱 Phone / tablet (Apple Books)</option><!-- term-ref-ok -->
                <option value="computer"   ${e.target_reader === 'computer' ? 'selected' : ''}>💻 Computer (Calibre, ADE)</option>
                <option value="kindle"     ${e.target_reader === 'kindle' ? 'selected' : ''}>📬 Kindle (Send to Kindle — visible endnotes)</option>
              </select>
            </label>
            <label class="text-xs">
              <span class="block mb-1 font-medium text-slate-700">Popup language cap</span>
              <select class="label-input w-full" data-field="max_popup_languages" title="K-KIN — most verse-popup languages this edition carries (Kindle's converter rejects the full 4-language apparatus, so kindle targets cap at 2 by default; other targets are uncapped). The value shown is what builds today.">
                <option value="">reader default (Kindle 2 · others uncapped)</option>
                <option value="1" ${String(e.max_popup_languages) === '1' ? 'selected' : ''}>1 language</option>
                <option value="2" ${String(e.max_popup_languages) === '2' ? 'selected' : ''}>2 languages</option>
                <option value="3" ${String(e.max_popup_languages) === '3' ? 'selected' : ''}>3 languages</option>
                <option value="4" ${String(e.max_popup_languages) === '4' ? 'selected' : ''}>4 languages (all)</option>
              </select>
            </label>
            <div class="text-xs md:col-span-2 cap-pick-row" data-max-cap="${e.max_popup_languages === null ? '' : e.max_popup_languages}">
              <span class="block mb-1 font-medium text-slate-700">Capped popup languages <span class="text-slate-400 font-normal">(bible-wide pick that fills the cap — used only when a cap applies; default Hebrew + Greek)</span></span>
              <input type="hidden" data-field="popup_languages_capped" class="cap-pick-value" value="${escapeAttr((e.popup_languages_capped||[]).join(','))}">
              <label class="inline-flex items-center gap-1 mr-3"><input type="checkbox" class="cap-pick-box" data-cap-group="hebrew" ${(e.popup_languages_capped||[]).includes('hebrew') ? 'checked' : ''}><span>Hebrew</span></label>
              <label class="inline-flex items-center gap-1 mr-3"><input type="checkbox" class="cap-pick-box" data-cap-group="greek" ${(e.popup_languages_capped||[]).includes('greek') ? 'checked' : ''}><span>Greek</span></label>
              <label class="inline-flex items-center gap-1 mr-3"><input type="checkbox" class="cap-pick-box" data-cap-group="latin" ${(e.popup_languages_capped||[]).includes('latin') ? 'checked' : ''}><span>Latin</span></label>
              <label class="inline-flex items-center gap-1 mr-3"><input type="checkbox" class="cap-pick-box" data-cap-group="arabic" ${(e.popup_languages_capped||[]).includes('arabic') ? 'checked' : ''}><span>Arabic</span></label>
            </div>
            <label class="text-xs flex items-center gap-2">
              <input type="checkbox" data-field="reader_toc_collapsible" ${e.reader_toc_collapsible === true ? 'checked' : ''}>
              <span>Expandable chapter lists in the Contents page <span class="text-slate-400">(capable readers only — e-ink/ADE render the pills always-visible instead)</span></span>
            </label>
            <label class="text-xs flex items-center gap-2">
              <input type="checkbox" data-field="reader_toc_default_open" ${e.reader_toc_default_open ? 'checked' : ''}>
              <span>Books default to expanded</span>
            </label>
            <label class="text-xs flex items-center gap-2">
              <input type="checkbox" data-field="closing_colophon" ${e.closing_colophon !== false ? 'checked' : ''}>
              <span>Closing colophon page (the traditional last page)</span>
            </label>
            <label class="text-xs flex items-center gap-2 eink-only-row ${e.target_reader === 'eink' ? '' : 'hidden'}" data-eink-only>
              <input type="checkbox" data-field="reader_eink_verse_lines" ${e.reader_eink_verse_lines ? 'checked' : ''}>
              <span>One verse per line <span class="text-slate-400">(Kobo — off = normal flowing paragraphs like other readers)</span></span>
            </label>
            <label class="text-xs flex flex-col gap-1 eink-only-row ${e.target_reader === 'eink' ? '' : 'hidden'}" data-eink-only>
              <span>Study notes layout <span class="text-slate-400">(Kobo — badge notes only; translation links always popup)</span></span>
              <select data-field="reader_eink_study_layout" class="text-xs border border-slate-300 rounded px-2 py-1 max-w-md">
                <option value="backmatter" ${(e.reader_eink_study_layout || 'backmatter') === 'backmatter' ? 'selected' : ''}>Glossary at back (recommended)</option>
                <option value="popup" ${e.reader_eink_study_layout === 'popup' ? 'selected' : ''}>Compact popups (legacy)</option>
                <option value="inline" ${e.reader_eink_study_layout === 'inline' || e.reader_eink_study_inline ? 'selected' : ''}>Full inline blocks</option>
              </select>
            </label>
            <p class="text-xs text-slate-500 md:col-span-2 italic">
              Chapter heading and Contents changes apply on the next BUILD.
            </p>
          </div>
        </div>
      </details>

      <details class="covers-section mt-3 border border-slate-200 rounded bg-slate-50">
        <summary class="px-3 py-2 cursor-pointer text-xs font-semibold uppercase tracking-wide text-slate-600 hover:bg-slate-100">
          Cover
          <span class="text-slate-400 normal-case font-normal ml-2">
            pick one of 25 designs · upload your own · per-book art
          </span>
        </summary>
        <div class="covers-body px-3 pb-3 pt-1 space-y-3">
          <div class="flex gap-4 items-start flex-wrap">
            <div class="shrink-0">
              <span class="block mb-1 text-xs font-medium text-slate-700">Current cover</span>
              <img class="covers-current w-24 h-36 object-contain border border-slate-300 rounded bg-white"
                   src="${e.cover_image ? '/content/' + escapeAttr(e.cover_image) : ''}"
                   alt="current cover for ${escapeAttr(e.title)}">
            </div>
            <div class="flex-1 min-w-72">
              <span class="block mb-1 text-xs font-medium text-slate-700">Pick a design
                <span class="text-slate-400 font-normal">— composes this edition's title onto the design (applies immediately)</span></span>
              <div class="covers-picker grid grid-cols-5 gap-1.5">
                ${(DATA.cover_templates||[]).map(t => `
                  <button type="button"
                          class="covers-template-thumb border rounded overflow-hidden hover:ring-2 hover:ring-blue-400 ${t.stem === (e.cover_template||'') ? 'ring-2 ring-blue-600 border-blue-600' : 'border-slate-300'}"
                          data-stem="${escapeAttr(t.stem)}" title="${escapeAttr(t.family_label)} · ${escapeAttr(t.color)}">
                    <img class="block w-full h-auto" loading="lazy" src="${escapeAttr(t.thumb)}"
                         alt="${escapeAttr(t.family_label)} ${escapeAttr(t.color)} cover design">
                  </button>`).join('')}
              </div>
            </div>
          </div>
          <div class="pt-2 border-t border-slate-200 grid grid-cols-1 md:grid-cols-2 gap-3">
            <label class="text-xs">
              <span class="block mb-1 font-medium text-slate-700">Upload a main cover
                <span class="text-slate-400 font-normal">(2:3 portrait, PNG/JPEG/WebP, ≤10 MB)</span></span>
              <input type="file" class="covers-upload-main text-xs" accept="image/png,image/jpeg,image/webp">
            </label>
            <label class="text-xs">
              <span class="block mb-1 font-medium text-slate-700">Upload per-book art</span>
              <span class="flex gap-1.5">
                <select class="label-input covers-book-select text-xs flex-1" title="which book this art is for">
                  ${((DATA.edition_canon_books||{})[e.id]||[]).map(code => {
                      const b = (DATA.books_canonical||[]).find(x => x.code === code);
                      return `<option value="${escapeAttr(code)}">${escapeAttr(b ? b.title : code)}</option>`;
                  }).join('')}
                </select>
                <input type="file" class="covers-upload-book text-xs" accept="image/png,image/jpeg,image/webp">
              </span>
            </label>
          </div>
          <p class="covers-status text-xs text-slate-500"></p>
        </div>
      </details>

      <details class="time-travel-section mt-3 border border-slate-200 rounded bg-slate-50">
        <summary class="px-3 py-2 cursor-pointer text-xs font-semibold uppercase tracking-wide text-slate-600 hover:bg-slate-100">
          Time-traveling commentary
          <span class="text-slate-400 normal-case font-normal ml-2">
            limit commentary to what a reader in year X would have had (Phase ψ.37)
          </span>
        </summary>
        <div class="px-3 pb-3 pt-1 space-y-2">
          <p class="text-xs text-slate-500">
            When set, the build filters out every note whose source
            was first published <em>after</em> the year you choose —
            and every contemporary note (User-original / paraphrase)
            since those weren't part of the historical record either.
            Pick "no limit" to ship the whole corpus.
          </p>
          <label class="text-xs flex items-center gap-2">
            <span class="font-medium text-slate-700">Year ceiling:</span>
            <select class="label-input w-auto" data-field="time_filter_ceiling" title="ψ.37 — drop notes whose source published after this year">
              <option value="null" ${e.time_filter_ceiling == null ? 'selected' : ''}>no limit (full corpus)</option>
              <option value="2000" ${e.time_filter_ceiling === 2000 ? 'selected' : ''}>by 2000 — modern PD (drops contemporary user notes)</option>
              <option value="1900" ${e.time_filter_ceiling === 1900 ? 'selected' : ''}>by 1900 — drops Kenyon (1903) + contemporary</option>
              <option value="1895" ${e.time_filter_ceiling === 1895 ? 'selected' : ''}>by 1895 — drops Nave's (1897) too</option>
              <option value="1885" ${e.time_filter_ceiling === 1885 ? 'selected' : ''}>by 1885 — drops Strong's (1890); only TSK remains</option>
              <option value="1850" ${e.time_filter_ceiling === 1850 ? 'selected' : ''}>by 1850 — TSK era only (≈6K notes)</option>
              <option value="1700" ${e.time_filter_ceiling === 1700 ? 'selected' : ''}>by 1700 — empty (no pre-1834 commentary yet)</option>
              <option value="1611" ${e.time_filter_ceiling === 1611 ? 'selected' : ''}>by 1611 — King James era (empty; awaits Calvin/Henry χ-cluster)</option>
            </select>
          </label>
          <p class="text-xs text-slate-500 italic">
            Applies on next BUILD. Today's corpus is 1834-1903 PD apparatus;
            pre-1700 positions render empty until a future χ-cluster phase
            adds Calvin (1556), Henry (1706), Wesley (1755) etc.
          </p>
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

      <!-- ψ.19 — reading plans card. ψ.19.1 wired the build-pipeline
           ToC integration; opting in now produces a Reading-Plans
           section in the EPUB output. -->
      <details class="reading-plans-section mt-3 border border-slate-200 rounded bg-slate-50" data-edition-id="${e.id}">
        <summary class="px-3 py-2 cursor-pointer text-xs font-semibold uppercase tracking-wide text-slate-600 hover:bg-slate-100">
          Reading plans
          <span class="text-slate-400 normal-case font-normal ml-2">
            (Phase ψ.19 / ψ.19.1 — opt your edition into daily reading schedules)
          </span>
        </summary>
        <div class="p-3 reading-plans-body">
          <p class="text-xs text-slate-500 mb-2">
            Pick the daily / monthly reading plans this edition's readers
            should see. Each plan ships as a YAML file in
            <code class="font-mono">content/reading_plans/</code>; opt-in
            here is per-edition. The build pipeline emits a
            Reading-plan section in the EPUB ToC for every enabled plan.
          </p>
          <div class="reading-plans-list flex flex-col gap-2">
            ${(DATA.reading_plans || []).map(rp => `
              <label class="flex items-start gap-2 p-2 bg-white border border-slate-200 rounded text-sm cursor-pointer hover:border-blue-300">
                <input type="checkbox" class="reading-plan-cb mt-0.5" data-plan-id="${escapeAttr(rp.id)}">
                <div class="flex-1 min-w-0">
                  <div class="flex items-baseline gap-2 flex-wrap">
                    <span class="font-medium">${escapeAttr(rp.label)}</span>
                    <span class="font-mono text-xs text-slate-400">${escapeAttr(rp.id)}</span>
                    <span class="text-xs text-slate-500">· ${rp.entry_count} entries</span>
                  </div>
                  ${rp.description ? `<div class="text-xs text-slate-500 mt-0.5">${escapeAttr(rp.description.split('\\n')[0])}</div>` : ''}
                </div>
              </label>
            `).join('') || '<div class="text-xs text-slate-400 italic">no reading plans on disk yet — drop YAML files into content/reading_plans/</div>'}
          </div>
          <p class="text-xs text-slate-400 mt-2 italic">
            Leaving every box unchecked means "no reading plan ToC section"
            for this edition — pre-ψ.19 build behaviour preserved.
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
          ${e.max_popup_languages !== null && e.max_popup_languages !== undefined ? `
          <div class="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2 mb-2 cap-bypass-note">
            ⚠ This edition's reader target caps popups at ${e.max_popup_languages} language${e.max_popup_languages === 1 ? '' : 's'}
            (bible-wide pick: ${(e.popup_languages_capped || []).join(' + ') || 'Hebrew + Greek'}).
            The build uses that pick everywhere — the per-book settings below are bypassed while the cap applies.
          </div>` : ''}
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
    const inputs = box.querySelectorAll('input, select, textarea');
    const btn = box.querySelector('.ed-save');
    // The psi11 "Preview" button also carries data-edition, so the selector
    // above matches it as well. Skip any box that isn't a full edition card
    // (no Save button) — otherwise the unguarded btn.addEventListener below
    // throws on null and aborts the forEach, leaving every edition AFTER the
    // first completely unwired (no save / popup-langs / traditions / covers).
    if (!btn) return;
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
    // ψ.19 — wire the Reading-plans toggle list. Same pattern as
    // popup-langs / traditions: state on the box, dirty flag on
    // box.dataset, change events bubble out via a synthetic event.
    wireReadingPlansSection(box, ed, () => {
      const evt = new Event('change', {bubbles: true});
      const anyInput = box.querySelector('input, select');
      if (anyInput) anyInput.dispatchEvent(evt);
    });
    // σ.4.2 — wire the "Your edition's name & notes" card: the smart-name
    // picker + Custom… input sync into the hidden display_name field (which
    // participates in the standard dirty-check / payload above).
    wireIdentityCard(box, ed);
    // K-KIN (C) — the capped popup-language checkboxes sync into the hidden
    // popup_languages_capped data-field input (standard dirty-check path).
    wireCapPickRow(box);
    wireEinkOnlyRows(box);
    wireBadgeStyleRow(box);
    // §4.6 — Cover picker + uploads. Immediate-action panel (pick →
    // server-side recompose; uploads → multipart), so it's wired
    // independently of the Save button / dirty-check.
    wireCoversSection(box, ed);
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
// σ.4.2 — "Your edition's name & notes" card
//
// The name picker is a <select> of suggestions DERIVED from what the
// builder actually built — never a hardcoded "Study Bible". It pairs the
// edition's canon label with the kind of edition we can infer:
//   • "<Canon> Study Bible"  — only when study-type note families are on
//   • "<Canon> Bible"        — the plain reading edition
//   • "<Canon> Reading Bible"— when few/no note families are enabled
//   • "Holy Bible"           — the bare option (empty subtitle → cover
//                              shows just the main title)
//   • "✏ Custom…"            — reveals a free-text input (capped at 48)
// The select + custom input are UI-only; wireIdentityCard syncs the
// resolved value into a hidden data-field="display_name" input so the
// standard dirty-check + buildCustomizePayload pick it up unchanged.
// =====================================================================

// Friendly canon labels for the suggestion text. Unknown canons fall back
// to a capitalised form of the raw id so a new canon still reads sanely.
const CANON_LABELS = {
  ethiopian: 'Ethiopian Tewahedo',
  catholic:  'Catholic',
  protestant:'Protestant',
  tanakh:    'Hebrew',
  orthodox:  'Eastern Orthodox',
};

// Note categories that signal a study/annotated edition (vs. a plain reading
// Bible). If an edition enables ANY of these, "Study Bible" is offered;
// otherwise it never is (the user's "never assume Study" requirement).
const STUDY_CATEGORIES = ['comm', 'hist', 'lit', 'text', 'lang', 'apol', 'compare'];

function canonLabel(canon) {
  if (!canon) return '';
  if (CANON_LABELS[canon]) return CANON_LABELS[canon];
  return String(canon).charAt(0).toUpperCase() + String(canon).slice(1);
}

// Compute the ordered list of suggested names for one edition record. Pure
// function of the edition's canon + enabled note families — so the list
// reflects what was actually built, not an assumption.
function nameSuggestions(edition) {
  const label = canonLabel(edition.canon);
  const cats = edition.enabled_categories || [];
  const hasStudy = cats.some(c => STUDY_CATEGORIES.indexOf(c) !== -1);
  const out = [];
  if (label) {
    if (hasStudy) {
      // Study families on → lead with the Study Bible suggestion.
      out.push(label + ' Study Bible');
      out.push(label + ' Bible');
    } else {
      // No study families → a plain reading edition; never offer "Study".
      out.push(label + ' Bible');
      out.push(label + ' Reading Bible');
    }
  }
  // Always offer the bare "Holy Bible" (= empty subtitle, cover shows only
  // the main title) so the builder can opt into a subtitle-free cover.
  out.push('Holy Bible');
  // De-dup while preserving order.
  return out.filter((v, i) => out.indexOf(v) === i);
}

const CUSTOM_NAME_SENTINEL = '✏ Custom…';  // "✏ Custom…"

// K-KIN (C) — sync the 4 capped-language checkboxes into the hidden
// popup_languages_capped input (comma-joined, fixed hebrew/greek/latin/arabic
// order for determinism) and fire the events the standard dirty-check
// listens for. The cap itself is a plain data-field select; the build
// enforces pick<=cap, and the API refuses an over-cap save.
function wireCapPickRow(box) {
  const row = box.querySelector('.cap-pick-row');
  if (!row) return;
  const hidden = row.querySelector('.cap-pick-value');
  const checks = [...row.querySelectorAll('.cap-pick-box')];
  if (!hidden || !checks.length) return;
  checks.forEach(cb => cb.addEventListener('change', () => {
    hidden.value = checks.filter(b => b.checked).map(b => b.dataset.capGroup).join(',');
    hidden.dispatchEvent(new Event('input', {bubbles: true}));
    hidden.dispatchEvent(new Event('change', {bubbles: true}));
  }));
}

function wireEinkOnlyRows(box) {
  const targetSel = box.querySelector('[data-field="target_reader"]');
  const rows = box.querySelectorAll('[data-eink-only]');
  if (!targetSel || !rows.length) return;
  const sync = () => {
    const on = targetSel.value === 'eink';
    rows.forEach(row => row.classList.toggle('hidden', !on));
    const badgeSel = box.querySelector('.badge-style-select');
    if (badgeSel) syncBadgeStyleOptions(box, targetSel.value, badgeSel);
  };
  targetSel.addEventListener('change', sync);
  sync();
}

function syncBadgeStyleOptions(box, target, badgeSel) {
  const unsafe = badgeSel.querySelector('option[data-eink-unsafe]');
  if (unsafe) unsafe.disabled = target === 'eink';
  if (target === 'eink' && badgeSel.value === 'dot') {
    badgeSel.value = 'dagger+count';
    badgeSel.dispatchEvent(new Event('change', {bubbles: true}));
  }
  const hint = box.querySelector('.badge-style-hint');
  if (hint) {
    hint.textContent = target === 'eink'
      ? 'Kobo: dagger+count or lozenge+count work well; ◈ and • do not.'
      : '◈ renders on Apple Books / tablet; chip is the e-ink default when no style is picked.';
  }
}

function wireBadgeStyleRow(box) {
  const markerSel = box.querySelector('[data-field="marker_style"]');
  const rows = box.querySelectorAll('.badge-style-row');
  const badgeSel = box.querySelector('.badge-style-select');
  const targetSel = box.querySelector('[data-field="target_reader"]');
  if (!markerSel || !rows.length) return;
  const sync = () => {
    const on = markerSel.value === 'badge';
    rows.forEach(row => row.classList.toggle('hidden', !on));
    if (on && badgeSel && targetSel) syncBadgeStyleOptions(box, targetSel.value, badgeSel);
  };
  markerSel.addEventListener('change', sync);
  if (badgeSel && targetSel) badgeSel.addEventListener('change', () => syncBadgeStyleOptions(box, targetSel.value, badgeSel));
  sync();
}

function wireIdentityCard(box, edition) {
  const card = box.querySelector('.ed-identity-card');
  if (!card) return;
  const pick = card.querySelector('.display-name-pick');
  const custom = card.querySelector('.display-name-custom');
  const hidden = card.querySelector('.display-name-value');
  if (!pick || !custom || !hidden) return;

  const current = hidden.value || '';
  const suggestions = nameSuggestions(edition);
  // The current value, if it isn't one of the suggestions, becomes a
  // pre-selected entry so re-opening the card shows the real name.
  const options = suggestions.slice();
  if (current && options.indexOf(current) === -1) options.unshift(current);

  // Build the <option> list (escaped) + the Custom… sentinel last.
  let html = options.map(s =>
    `<option value="${escapeAttr(s)}"${s === current ? ' selected' : ''}>${escapeAttr(s)}</option>`
  ).join('');
  // "Holy Bible" maps to an EMPTY display_name (cover shows only the main
  // title). We keep it visible in the dropdown but resolve it to "" on sync.
  html += `<option value="${escapeAttr(CUSTOM_NAME_SENTINEL)}">${escapeAttr(CUSTOM_NAME_SENTINEL)}</option>`;
  pick.innerHTML = html;

  // If the current value matched nothing (e.g. blank), default the select to
  // the top suggestion WITHOUT marking the field dirty — the hidden field
  // keeps its real original value until the user actually changes something.
  if (!current && options.length) pick.value = options[0];

  // Resolve the visible select value to the stored display_name string.
  // "Holy Bible" → "" (no subtitle); everything else is literal.
  const resolve = label => (label === 'Holy Bible' ? '' : label);

  const fireChange = () => {
    // Push the resolved value into the hidden data-field input + fire the
    // events the rebind loop listens for, so the dirty-check + payload update.
    hidden.dispatchEvent(new Event('input', {bubbles: true}));
    hidden.dispatchEvent(new Event('change', {bubbles: true}));
  };

  pick.addEventListener('change', () => {
    if (pick.value === CUSTOM_NAME_SENTINEL) {
      custom.classList.remove('hidden');
      custom.value = (current && options.indexOf(current) === -1) ? current : '';
      hidden.value = custom.value;
      custom.focus();
    } else {
      custom.classList.add('hidden');
      hidden.value = resolve(pick.value);
    }
    fireChange();
  });

  custom.addEventListener('input', () => {
    hidden.value = custom.value;
    fireChange();
  });
}

// =====================================================================
// §4.6 — Cover picker + upload affordances
//
// An immediate-action panel (NOT part of the save form). The static
// markup (current-cover preview, the 25 thumbnails, the two file inputs,
// the per-book select) is rendered in the renderEditions template above;
// this function only attaches behaviour. Clicking a thumbnail recomposes
// the edition's main cover server-side (POST /api/covers/<ed>/template,
// which composes the edition title onto the chosen design + sets
// cover_image/cover_template); the file inputs surface the existing
// multipart upload endpoints (/main hero cover, /book/<code> per-book
// art). Each action refreshes the preview in place (cache-busted) — no
// innerHTML reassignment (textContent / .src / classList only).
// =====================================================================

function wireCoversSection(box, edition) {
  const body = box.querySelector('.covers-body');
  if (!body) return;
  const edId = edition.id;
  const statusEl = body.querySelector('.covers-status');
  const currentImg = body.querySelector('.covers-current');
  const coverSrc = path => path ? '/content/' + path + '?t=' + Date.now() : '';
  const setStatus = (msg, ok) => {
    if (!statusEl) return;
    statusEl.textContent = msg;
    statusEl.className = 'covers-status text-xs ' +
      (ok === false ? 'text-red-600' : ok === true ? 'text-green-700' : 'text-slate-500');
  };
  const clearHighlight = () => body.querySelectorAll('.covers-template-thumb')
    .forEach(t => t.classList.remove('ring-2', 'ring-blue-600', 'border-blue-600'));

  // Pick a design → recompose the cover server-side.
  body.querySelectorAll('.covers-template-thumb').forEach(thumb => {
    thumb.addEventListener('click', async () => {
      const stem = thumb.dataset.stem;
      setStatus('Composing cover…');
      try {
        const r = await fetch('/api/covers/' + encodeURIComponent(edId) + '/template', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({cover_template: stem}),
        });
        const j = await r.json();
        if (!r.ok || j.error) { setStatus('Failed: ' + (j.error || r.status), false); return; }
        clearHighlight();
        thumb.classList.add('ring-2', 'ring-blue-600', 'border-blue-600');
        edition.cover_template = stem;
        edition.cover_image = j.path;
        if (currentImg) currentImg.src = coverSrc(j.path);
        setStatus('Cover updated.', true);
      } catch (err) { setStatus('Failed: ' + err, false); }
    });
  });

  // Upload a main hero cover (multipart → /api/covers/<ed>/main).
  const mainInput = body.querySelector('.covers-upload-main');
  if (mainInput) {
    mainInput.addEventListener('change', async () => {
      const f = mainInput.files && mainInput.files[0];
      if (!f) return;
      setStatus('Uploading cover…');
      const fd = new FormData(); fd.append('file', f);
      try {
        const r = await fetch('/api/covers/' + encodeURIComponent(edId) + '/main', {method: 'POST', body: fd});
        const j = await r.json();
        if (!r.ok || j.error) { setStatus('Upload failed: ' + (j.error || r.status), false); }
        else {
          edition.cover_image = j.path;
          if (currentImg) currentImg.src = coverSrc(j.path);
          clearHighlight();  // an uploaded cover supersedes any template pick
          setStatus('Main cover uploaded.', true);
        }
      } catch (err) { setStatus('Upload failed: ' + err, false); }
      mainInput.value = '';
    });
  }

  // Upload per-book art (multipart → /api/covers/<ed>/book/<code>).
  const bookInput = body.querySelector('.covers-upload-book');
  const bookSelect = body.querySelector('.covers-book-select');
  if (bookInput && bookSelect) {
    bookInput.addEventListener('change', async () => {
      const f = bookInput.files && bookInput.files[0];
      if (!f) return;
      const code = bookSelect.value;
      setStatus('Uploading art for ' + code + '…');
      const fd = new FormData(); fd.append('file', f);
      try {
        const r = await fetch('/api/covers/' + encodeURIComponent(edId) + '/book/' + encodeURIComponent(code),
                              {method: 'POST', body: fd});
        const j = await r.json();
        if (!r.ok || j.error) { setStatus('Upload failed: ' + (j.error || r.status), false); }
        else { setStatus('Per-book art uploaded for ' + code + '.', true); }
      } catch (err) { setStatus('Upload failed: ' + err, false); }
      bookInput.value = '';
    });
  }
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
// ψ.19 — Reading plans section
//
// Per-edition opt-in toggles for `enabled_reading_plans`. State on
// the box:
//   box.readingPlansState = {
//     enabled:  Set<plan_id>,
//     original: Set<plan_id>,
//   }
//   box.dataset.readingPlansDirty = '0' | '1'
//
// Schema-only for now; the build pipeline ToC integration ships in
// ψ.19.1.
// =====================================================================

function wireReadingPlansSection(box, edition, onChange) {
  const body = box.querySelector('.reading-plans-body');
  if (!body) return;
  const initial = new Set(edition.enabled_reading_plans || []);
  const state = {
    enabled: new Set(initial),
    original: new Set(initial),
  };
  box.readingPlansState = state;
  body.querySelectorAll('.reading-plan-cb').forEach(cb => {
    cb.checked = state.enabled.has(cb.dataset.planId);
    cb.addEventListener('change', () => {
      if (cb.checked) state.enabled.add(cb.dataset.planId);
      else state.enabled.delete(cb.dataset.planId);
      markReadingPlansDirty(box, state);
      onChange && onChange();
    });
  });
  box.dataset.readingPlansDirty = '0';
}

function markReadingPlansDirty(box, state) {
  const o = state.original;
  const e = state.enabled;
  const sameSet = (a, b) => a.size === b.size && [...a].every(x => b.has(x));
  box.dataset.readingPlansDirty = sameSet(e, o) ? '0' : '1';
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
  box.querySelectorAll('input, select, textarea').forEach(i => {
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
  // ψ.19 — include reading-plans state if the section changed.
  if (box.dataset.readingPlansDirty === '1' && box.readingPlansState) {
    payload.enabled_reading_plans = [...box.readingPlansState.enabled];
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
      status.innerHTML = `<span class="text-red-600">✗ ${escapeHTML(result.error)}</span>`;
      return;
    }
    status.innerHTML = '<span class="text-emerald-700">✓ saved</span>';
    // σ.4.2 — if the edition name (the cover subtitle) changed, recompose the
    // cover so the new subtitle appears immediately (same endpoint the cover
    // picker uses; an empty stem recomposes with the edition's current design).
    // Only display_name has a console control today; a future cover_main_title
    // control would add its key here.
    if ('display_name' in payload) {
      maybeRecomposeCover(box, id);
    }
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
    box.querySelectorAll('input, select, textarea').forEach(i => {
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

// σ.4.2 — recompose the edition's cover after a name/main-title save so the
// new subtitle shows immediately. Reuses the cover-template endpoint the
// picker calls; an empty cover_template recomposes with the edition's current
// design (the server resolves the default). Best-effort: a failure here only
// updates a status note — the name itself already saved, and the next build /
// template-pick recomposes regardless.
async function maybeRecomposeCover(box, id) {
  const edition = DATA.editions.find(x => x.id === id) || {};
  const stem = edition.cover_template || '';
  try {
    const r = await fetch('/api/covers/' + encodeURIComponent(id) + '/template', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({cover_template: stem}),
    });
    const j = await r.json();
    if (r.ok && !j.error) {
      edition.cover_template = j.cover_template;
      edition.cover_image = j.path;
      // Refresh the in-card cover preview (cache-busted) if it's visible.
      const img = box.querySelector('.covers-current');
      if (img && j.path) img.src = '/content/' + j.path + '?t=' + Date.now();
    }
  } catch (_) { /* non-fatal: the name saved; cover updates on next build */ }
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
        status.innerHTML = `<span class="text-red-600">✗ ${escapeHTML(msg)}</span>`;
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
      status.innerHTML = `<span class="text-red-600">✗ ${escapeHTML(result.error)}</span>`;
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


# ψ.13.5: consolidated design-system substitution.
CUSTOMIZE_HTML = apply_design_system(CUSTOMIZE_HTML, "/customize")

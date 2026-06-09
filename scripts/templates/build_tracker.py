"""HTML for /build-tracker console (Ω.0 free-public pivot, 2026-05-14).

Shows the builder what's currently enabled in their selected edition:
total enabled notes, books covered, kinds enabled + per-book × per-
chapter coverage heat-grid + per-category and per-kind breakdowns.
The /matrix console is for *toggling* kinds on/off; /build-tracker
is for *seeing* what those toggles produce in the EPUB you build.

Cross-link nav substituted from `_design.HEADER_NAV_LINKS("/build-
tracker")` per §6.2 invariant.
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
    apply_design_system,
)

__all__ = ["BUILD_TRACKER_HTML", "HEADER_NAV_LINKS", "BUYER_ARC_POLISH_CSS"]

BUILD_TRACKER_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Build Tracker · YHWH Ya' Way</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  .heat-cell {
    width: 1.4rem; height: 1.4rem;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.65rem; line-height: 1;
    border: 1px solid #e5e7eb;
    border-radius: 2px;
    cursor: default;
    font-variant-numeric: tabular-nums;
  }
  /* M6 — warm "illuminated density" ramp (parchment -> gold -> deep bronze) so the
     coverage grid reads on the manuscript page instead of as cold-green islands;
     luminance is monotonic and each label clears AA (ink on the mid-golds = 4.84/6.01,
     cream on the deep grounds). Replaces the cool-gray->emerald scale the skin can't reach. */
  .heat-0   { background: #F2EAD3; color: #6E5840; }
  .heat-1   { background: #ECDCB0; color: #574532; }
  .heat-2   { background: #E0C988; color: #574532; }
  .heat-3   { background: #D3B25C; color: #4A3A24; }
  .heat-4   { background: #C49A2E; color: #2B2118; }
  .heat-5   { background: #B8860B; color: #2B2118; }
  .heat-6   { background: #8A6510; color: #FCF8EF; }
  .heat-7   { background: #574532; color: #FCF8EF; }
  .book-row { transition: background 100ms; }
  .book-row:hover { background: #F4ECD8; }
  .book-row.open { background: #EFE6CE; }
  .summary-tile {
    background: #ffffff; border: 1px solid #e5e7eb; border-radius: 6px;
    padding: 0.75rem 1rem;
  }
  .summary-tile-num {
    font-size: 1.5rem; font-weight: 700; line-height: 1.1;
    font-variant-numeric: tabular-nums;
  }
  .summary-tile-label {
    font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.04em;
    color: #64748b; margin-top: 0.125rem;
  }
  .bar-row { display: grid; grid-template-columns: 9rem 1fr 3.5rem; align-items: center; gap: 0.5rem; }
  .bar-track { height: 0.5rem; background: #f1f5f9; border-radius: 3px; overflow: hidden; }
  .bar-fill { height: 100%; background: #3b82f6; border-radius: 3px; transition: width 200ms; }
  .tab-btn { padding: 0.5rem 0.875rem; border-bottom: 2px solid transparent; font-size: 0.875rem; }
  .tab-btn[aria-selected="true"] { border-bottom-color: #2563eb; color: #1e3a8a; font-weight: 600; }
  details > summary { cursor: pointer; list-style: none; }
  details > summary::-webkit-details-marker { display: none; }
</style>
<!-- THEME_TOKENS_CSS -->
<!-- DARK_MODE_JS -->
<!-- THEME_ICONS_JS -->
<!-- THEME_TOAST_JS -->
<!-- THEME_CMD_PALETTE_JS -->
<!-- THEME_STREAK_JS -->
<!-- THEME_BOOKMARKS_JS -->
<!-- THEME_RECENTS_JS -->
<!-- THEME_HOTRELOAD_JS -->
<!-- THEME_EDITABLE_JS -->
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="theme-bg-page theme-text">

<header class="border-b theme-bg-surface theme-border">
  <div class="max-w-6xl mx-auto px-4 py-3 flex items-baseline gap-4 text-sm flex-wrap">
    <strong class="text-base">YHWH Ya' Way</strong>
    <!-- HEADER_NAV_LINKS -->
    <span id="corpus-progress" class="ml-auto text-xs theme-text-muted" title="corpus depth toward the 35,000-note Ethiopian Tewahedo target">·· loading ··</span>
  </div>
</header>
<script>
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

<main class="max-w-6xl mx-auto px-4 py-6">
  <div class="flex items-end justify-between mb-3 flex-wrap gap-3">
    <div>
      <h1 class="text-2xl font-semibold mb-1">Build tracker</h1>
      <p class="text-sm text-slate-600">
        Everything that will appear in the EPUB you are about to build.
        Pick an edition to see its per-book coverage, per-chapter note
        density, and per-category / per-kind breakdown. Switch traditions
        or toggle kinds at <a class="text-blue-700 underline hover:no-underline" href="/customize">/customize</a> or <a class="text-blue-700 underline hover:no-underline" href="/matrix">/matrix</a>; numbers below refresh.
      </p>
    </div>
    <div class="flex items-end gap-3 flex-wrap">
      <label class="text-xs text-slate-500 flex flex-col gap-1">
        <span class="uppercase tracking-wide">Edition</span>
        <select id="ed-select" class="border border-slate-300 rounded px-2 py-1.5 text-sm min-w-[16rem]"></select>
      </label>
      <a id="ed-build-link" href="/export" class="px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium">Open in /export →</a>
    </div>
  </div>

  <div id="ed-urn" class="text-xs font-mono text-slate-500 mb-4"></div>

  <section id="summary" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6" aria-busy="true">
    <div class="summary-tile"><div class="summary-tile-num" id="sum-notes">··</div><div class="summary-tile-label">Notes enabled</div></div>
    <div class="summary-tile"><div class="summary-tile-num" id="sum-books">··</div><div class="summary-tile-label">Books covered</div></div>
    <div class="summary-tile"><div class="summary-tile-num" id="sum-chapters">··</div><div class="summary-tile-label">Chapters covered</div></div>
    <div class="summary-tile"><div class="summary-tile-num" id="sum-kinds">··</div><div class="summary-tile-label">Kinds enabled</div></div>
    <div class="summary-tile"><div class="summary-tile-num" id="sum-categories">··</div><div class="summary-tile-label">Categories</div></div>
    <div class="summary-tile"><div class="summary-tile-num" id="sum-langs">··</div><div class="summary-tile-label">Popup languages</div></div>
  </section>

  <nav role="tablist" class="flex gap-2 border-b border-slate-200 mb-4">
    <button class="tab-btn" role="tab" aria-selected="true" data-tab="heat">Per-book heat-grid</button>
    <button class="tab-btn" role="tab" aria-selected="false" data-tab="cat">By category</button>
    <button class="tab-btn" role="tab" aria-selected="false" data-tab="kind">By kind</button>
  </nav>

  <section id="tab-heat" role="tabpanel">
    <p class="text-xs text-slate-500 mb-2">Each row is one book; each cell is one chapter (number = enabled-note count). Click a book to see per-chapter detail.</p>
    <div id="heat-grid" class="space-y-1" aria-busy="true">
      <div class="theme-skeleton theme-skeleton-block" style="height:1.6rem"></div>
      <div class="theme-skeleton theme-skeleton-block" style="height:1.6rem"></div>
      <div class="theme-skeleton theme-skeleton-block" style="height:1.6rem"></div>
    </div>
  </section>

  <section id="tab-cat" role="tabpanel" class="hidden">
    <p class="text-xs text-slate-500 mb-3">Enabled-note count per category. The bar length is relative to the largest enabled category in this edition.</p>
    <div id="cat-bars" class="space-y-2"></div>
  </section>

  <section id="tab-kind" role="tabpanel" class="hidden">
    <p class="text-xs text-slate-500 mb-3">Enabled-note count per kind, ranked. Disabled kinds in this edition are hidden — see <a class="text-blue-700 underline hover:no-underline" href="/matrix">/matrix</a> to toggle them on.</p>
    <table class="w-full text-sm">
      <thead class="text-xs uppercase tracking-wide text-slate-500 border-b border-slate-200">
        <tr><th class="text-left py-1.5 pr-3">Kind</th><th class="text-left py-1.5 pr-3">Category</th><th class="text-right py-1.5">Notes</th></tr>
      </thead>
      <tbody id="kind-rows"></tbody>
    </table>
  </section>
</main>

<script>
function esc(s) { return String(s ?? '').replace(/[&<>"']/g, c => ({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
}[c])); }

function heatClass(n) {
  if (n <= 0) return 'heat-0';
  if (n <= 1) return 'heat-1';
  if (n <= 3) return 'heat-2';
  if (n <= 6) return 'heat-3';
  if (n <= 12) return 'heat-4';
  if (n <= 25) return 'heat-5';
  if (n <= 50) return 'heat-6';
  return 'heat-7';
}

async function loadEditions() {
  const r = await fetch('/api/matrix');
  const data = await r.json();
  const sel = document.getElementById('ed-select');
  sel.innerHTML = '';
  for (const e of data.editions) {
    const opt = document.createElement('option');
    opt.value = e.id;
    opt.textContent = e.title || e.id;
    sel.appendChild(opt);
  }
  // Restore last-picked edition from localStorage
  const last = window.localStorage.getItem('build-tracker.edition');
  if (last && Array.from(sel.options).some(o => o.value === last)) {
    sel.value = last;
  }
  sel.addEventListener('change', () => {
    window.localStorage.setItem('build-tracker.edition', sel.value);
    loadTracker(sel.value);
  });
  loadTracker(sel.value);
}

async function loadTracker(edId) {
  if (!edId) return;
  const r = await fetch('/api/build-tracker/' + encodeURIComponent(edId));
  if (!r.ok) {
    if (window.ebibleToast) window.ebibleToast('Failed to load build tracker for ' + edId, 'error');
    return;
  }
  const data = await r.json();
  renderUrn(data.edition);
  renderSummary(data.summary);
  renderHeat(data.per_book);
  renderCategories(data.per_category);
  renderKinds(data.per_kind);
  document.getElementById('ed-build-link').setAttribute('href', '/export?edition=' + encodeURIComponent(edId));
}

function renderUrn(ed) {
  document.getElementById('ed-urn').textContent = 'urn:yhwh:edition:' + (ed.id || '');
}

function renderSummary(s) {
  document.getElementById('summary').setAttribute('aria-busy', 'false');
  document.getElementById('sum-notes').textContent = (s.total_enabled_notes || 0).toLocaleString();
  document.getElementById('sum-books').textContent = `${s.books_covered} / ${s.books_in_canon}`;
  document.getElementById('sum-chapters').textContent = `${s.chapters_covered} / ${s.chapters_in_canon}`;
  document.getElementById('sum-kinds').textContent = s.kinds_enabled;
  document.getElementById('sum-categories').textContent = s.categories_enabled;
  document.getElementById('sum-langs').textContent = s.popup_languages.length || 0;
  document.getElementById('sum-langs').setAttribute('title', s.popup_languages.join(', ') || 'no popups');
}

function renderHeat(perBook) {
  const root = document.getElementById('heat-grid');
  root.innerHTML = '';
  root.setAttribute('aria-busy', 'false');
  if (!perBook.length) {
    root.innerHTML = '<div class="text-sm text-slate-400 italic">No books in this edition\'s canon — pick another edition.</div>';
    return;
  }
  for (const b of perBook) {
    const det = document.createElement('details');
    det.className = 'book-row border border-slate-200 rounded';
    det.dataset.bookCode = b.book_code;
    det.dataset.loaded = '0';
    const cells = b.by_chapter.map((n, i) => `<span class="heat-cell ${heatClass(n)}" title="ch ${i + 1}: ${n} note${n === 1 ? '' : 's'}">${n || ''}</span>`).join('');
    det.innerHTML = `
      <summary class="px-3 py-2 flex items-center gap-3 flex-wrap">
        <span class="font-medium text-sm w-28 flex-shrink-0">${esc(b.book_label)}</span>
        <span class="text-xs text-slate-400 font-mono w-12 flex-shrink-0">${esc(b.book_code)}</span>
        <span class="flex flex-wrap gap-0.5 flex-1 min-w-0">${cells}</span>
        <span class="text-xs text-slate-500 tabular-nums w-20 text-right flex-shrink-0">${b.enabled_notes.toLocaleString()} notes</span>
      </summary>
      <div class="px-3 pb-3 pt-1 border-t border-slate-100">
        <p class="text-xs text-slate-500 mb-2">${b.enabled_chapters} of ${b.chapters_in_canon} chapters covered; ${b.enabled_notes} enabled-note${b.enabled_notes === 1 ? '' : 's'}.</p>
        <div class="book-titles text-xs text-slate-400 italic">Open for note titles…</div>
      </div>
    `;
    det.addEventListener('toggle', () => {
      det.classList.toggle('open', det.open);
      if (det.open && det.dataset.loaded === '0' && b.enabled_notes > 0) {
        loadBookTitles(det, b.book_code);
      }
    });
    root.appendChild(det);
  }
}

async function loadBookTitles(det, bookCode) {
  const slot = det.querySelector('.book-titles');
  const edId = document.getElementById('ed-select').value;
  if (!edId) return;
  slot.innerHTML = '<span class="text-slate-400">Loading note titles…</span>';
  try {
    const r = await fetch('/api/build-tracker/' + encodeURIComponent(edId) + '/' + encodeURIComponent(bookCode));
    if (!r.ok) throw new Error('http ' + r.status);
    const data = await r.json();
    const notes = data.notes || [];
    det.dataset.loaded = '1';
    if (!notes.length) {
      slot.innerHTML = '<span class="text-slate-400 italic">No enabled notes in this book.</span>';
      return;
    }
    const cap = 100;
    const head = notes.slice(0, cap).map(t =>
      `<li class="text-xs text-slate-700 leading-tight pl-2 mb-0.5"><span class="font-mono text-slate-400 inline-block w-8 text-right mr-1">${esc(t.chapter)}</span><span class="text-slate-500 inline-block w-32 mr-2 truncate" title="${esc(t.kind)}">[${esc(t.kind)}]</span>${esc(t.title)}</li>`).join('');
    const overflow = notes.length > cap ? `<li class="text-xs text-slate-400 italic pl-2 mt-1">… and ${notes.length - cap} more (showing ${cap})</li>` : '';
    slot.innerHTML = '<ul class="space-y-0 max-h-96 overflow-y-auto">' + head + overflow + '</ul>';
  } catch (e) {
    slot.innerHTML = '<span class="text-red-600">Failed to load: ' + esc(e.message) + '</span>';
  }
}

function renderCategories(cats) {
  const root = document.getElementById('cat-bars');
  root.innerHTML = '';
  if (!cats.length) {
    root.innerHTML = '<div class="text-sm text-slate-400 italic">No enabled categories.</div>';
    return;
  }
  const maxN = Math.max(...cats.map(c => c.enabled_notes), 1);
  for (const c of cats) {
    const pct = Math.round((c.enabled_notes / maxN) * 100);
    const div = document.createElement('div');
    div.className = 'bar-row';
    div.innerHTML = `
      <span class="text-sm">${esc(c.label)}</span>
      <span class="bar-track"><span class="bar-fill" style="width:${pct}%"></span></span>
      <span class="text-sm text-right tabular-nums">${c.enabled_notes.toLocaleString()}</span>
    `;
    root.appendChild(div);
  }
}

function renderKinds(kinds) {
  const tbody = document.getElementById('kind-rows');
  tbody.innerHTML = '';
  if (!kinds.length) {
    tbody.innerHTML = '<tr><td colspan="3" class="text-sm text-slate-400 italic py-2">No enabled kinds.</td></tr>';
    return;
  }
  for (const k of kinds) {
    const tr = document.createElement('tr');
    tr.className = 'border-b border-slate-100';
    tr.innerHTML = `
      <td class="py-1.5 pr-3 font-mono text-xs">${esc(k.code)}</td>
      <td class="py-1.5 pr-3 text-xs text-slate-500">${esc(k.category)}</td>
      <td class="py-1.5 text-right tabular-nums">${k.enabled_notes.toLocaleString()}</td>
    `;
    tbody.appendChild(tr);
  }
}

// Tab switcher
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.setAttribute('aria-selected', b === btn ? 'true' : 'false'));
    const target = btn.dataset.tab;
    document.getElementById('tab-heat').classList.toggle('hidden', target !== 'heat');
    document.getElementById('tab-cat').classList.toggle('hidden', target !== 'cat');
    document.getElementById('tab-kind').classList.toggle('hidden', target !== 'kind');
  });
});

loadEditions().catch(e => {
  if (window.ebibleToast) window.ebibleToast('Failed to load editions: ' + e.message, 'error');
});
</script>

</body>
</html>
"""

BUILD_TRACKER_HTML = apply_design_system(BUILD_TRACKER_HTML, "/build-tracker")

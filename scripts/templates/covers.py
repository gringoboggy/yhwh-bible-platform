"""HTML for /covers console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import COVERS_HTML` callers.

ψ.15 editor-console polish (2026-05-09): cross-link nav substituted
from `_design.HEADER_NAV_LINKS("/covers")` and `BUYER_ARC_POLISH_CSS`
inlined from `_design`, mirroring the ψ.14 buyer-arc pattern.
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
)

COVERS_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Covers · E-Bible</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  .cover-slot {
    aspect-ratio: 2 / 3;
    border: 2px dashed #cbd5e1;
    background: #f8fafc;
    transition: border-color 120ms, background 120ms;
    overflow: hidden;
    position: relative;
  }
  .cover-slot.has-cover { border-style: solid; border-color: #94a3b8; background: #fff; }
  .cover-slot.dragover { border-color: #2563eb; background: #eff6ff; }
  .cover-slot.uploading { border-color: #f59e0b; }
  .cover-slot img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .cover-slot .placeholder {
    position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
    color: #94a3b8; font-size: 0.7rem; text-align: center; padding: 0.5rem;
  }
  .cover-slot .meta-strip {
    position: absolute; left: 0; right: 0; bottom: 0;
    background: rgba(15, 23, 42, 0.78); color: #f8fafc;
    font-size: 0.625rem; padding: 0.15rem 0.4rem;
    line-height: 1.1;
  }
  .cover-slot .delete-btn {
    position: absolute; top: 0.25rem; right: 0.25rem;
    background: rgba(15, 23, 42, 0.7); color: white;
    width: 1.5rem; height: 1.5rem; border-radius: 50%;
    display: none; align-items: center; justify-content: center;
    cursor: pointer; font-size: 1rem; line-height: 1;
  }
  .cover-slot.has-cover:hover .delete-btn { display: flex; }
  .cover-slot.uploading::after {
    content: "uploading..."; position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
    background: rgba(245, 158, 11, 0.15); color: #92400e;
    font-size: 0.75rem; font-weight: 500;
  }
  .err-banner {
    background: #fef2f2; border: 1px solid #fca5a5; color: #991b1b;
    padding: 0.5rem 0.75rem; border-radius: 0.375rem;
    font-size: 0.875rem;
  }
</style>
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-800">

<header class="border-b bg-white">
  <div class="max-w-6xl mx-auto px-4 py-3 flex items-baseline gap-4 text-sm flex-wrap">
    <strong class="text-base">E-Bible</strong>
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


<main class="max-w-6xl mx-auto px-4 py-6">
  <h1 class="text-2xl font-semibold mb-2">Cover images</h1>
  <p class="text-sm text-slate-600 mb-6">
    One main cover per edition, plus optional per-book covers. Books
    listed strictly in canonical Book/Chapter order; only books in
    each edition's canon appear. Drag a file onto a slot or click to
    upload. Limits: 600×900 to 4000×6000 px, max 10 MB, JPEG/PNG/WebP,
    aspect within ±20% of 2:3 portrait.
  </p>

  <div id="covers-root" class="space-y-8">
    <p class="text-slate-500 text-sm">loading…</p>
  </div>
</main>

<input id="hidden-file" type="file" accept="image/jpeg,image/png,image/webp" class="hidden">

<script>
let DATA = null;
let pendingTarget = null;  // {edition, book?} for the hidden file picker

function escapeAttr(s) { return String(s ?? '').replace(/[&<>"']/g, c => ({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
}[c])); }

function uploadUrl(edition, book) {
  const base = `/api/covers/${encodeURIComponent(edition)}`;
  return book ? `${base}/book/${encodeURIComponent(book)}` : `${base}/main`;
}

function imgUrl(path) {
  // Cover paths in editions.yaml are relative to content/.
  // Cache-bust on path so a fresh upload re-renders without browser stale.
  return `/content/${path}?t=${Date.now()}`;
}

async function loadCovers() {
  const root = document.getElementById('covers-root');
  try {
    const r = await fetch('/api/covers');
    DATA = await r.json();
  } catch (e) {
    root.innerHTML = `<div class="err-banner">failed to load: ${escapeAttr(e.message)}</div>`;
    return;
  }
  render();
}

function render() {
  const root = document.getElementById('covers-root');
  root.innerHTML = '';
  for (const ed of DATA.editions) {
    const card = document.createElement('section');
    card.className = 'bg-white border rounded-lg p-4';
    card.dataset.edition = ed.edition_id;

    const header = document.createElement('div');
    header.className = 'flex items-baseline justify-between mb-3';
    header.innerHTML = `
      <h2 class="text-lg font-semibold">${escapeAttr(ed.edition_id)}</h2>
      <span class="text-xs text-slate-500">${ed.book_covers.length} books in canon</span>
    `;
    card.appendChild(header);

    // Main cover hero
    const heroWrap = document.createElement('div');
    heroWrap.className = 'flex gap-4 mb-5 pb-4 border-b';
    heroWrap.innerHTML = `
      <div class="w-32 flex-shrink-0">
        ${slotHTML('main cover', ed.main_cover.path, ed.main_cover.meta)}
      </div>
      <div class="text-sm text-slate-600 pt-1">
        <p class="font-medium text-slate-700">Main cover</p>
        <p class="mt-1">Used as the EPUB jacket and the title-page image. One per edition.</p>
      </div>
    `;
    const heroSlot = heroWrap.querySelector('.cover-slot');
    wireSlot(heroSlot, ed.edition_id, null);
    card.appendChild(heroWrap);

    // Per-book grid — books already in canonical order from the API
    const gridLabel = document.createElement('p');
    gridLabel.className = 'text-sm font-medium text-slate-700 mb-2';
    gridLabel.textContent = 'Per-book covers';
    card.appendChild(gridLabel);

    const grid = document.createElement('div');
    grid.className = 'grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-3';
    for (const slot of ed.book_covers) {
      const cell = document.createElement('div');
      cell.innerHTML = `
        <p class="text-xs text-slate-500 mb-1 truncate" title="${escapeAttr(slot.title)}">
          <span class="font-mono text-slate-400">${slot.book_code}</span>
        </p>
        ${slotHTML(slot.title, slot.path, slot.meta)}
      `;
      const slotEl = cell.querySelector('.cover-slot');
      wireSlot(slotEl, ed.edition_id, slot.book_code);
      grid.appendChild(cell);
    }
    card.appendChild(grid);

    // Per-edition error banner (per-card so errors don't pile up globally)
    const banner = document.createElement('div');
    banner.className = 'err-banner-host mt-3 hidden';
    card.appendChild(banner);

    root.appendChild(card);
  }
}

function slotHTML(label, path, meta) {
  const hasImage = !!(path && meta);
  const cls = hasImage ? 'cover-slot has-cover' : 'cover-slot';
  if (!hasImage) {
    return `<div class="${cls}" title="click or drop to upload">
      <div class="placeholder">${escapeAttr(label || '+ upload')}</div>
    </div>`;
  }
  const m = meta;
  return `<div class="${cls}" title="${escapeAttr(label)}">
    <img src="${imgUrl(path)}" alt="${escapeAttr(label)}">
    <button class="delete-btn" type="button" title="remove cover">×</button>
    <div class="meta-strip">
      ${m.width || '?'}×${m.height || '?'} · ${m.size_kb} KB
    </div>
  </div>`;
}

function wireSlot(slotEl, editionId, bookCode) {
  slotEl.addEventListener('click', (ev) => {
    if (ev.target.classList.contains('delete-btn')) return;
    pendingTarget = {edition: editionId, book: bookCode};
    document.getElementById('hidden-file').click();
  });

  slotEl.addEventListener('dragover', (ev) => {
    ev.preventDefault();
    slotEl.classList.add('dragover');
  });
  slotEl.addEventListener('dragleave', () => slotEl.classList.remove('dragover'));
  slotEl.addEventListener('drop', (ev) => {
    ev.preventDefault();
    slotEl.classList.remove('dragover');
    const file = ev.dataTransfer.files && ev.dataTransfer.files[0];
    if (file) doUpload(slotEl, editionId, bookCode, file);
  });

  const del = slotEl.querySelector('.delete-btn');
  if (del) {
    del.addEventListener('click', (ev) => {
      ev.stopPropagation();
      const what = bookCode ? `the ${bookCode} cover` : 'the main cover';
      if (!confirm(`Remove ${what} for ${editionId}?`)) return;
      doDelete(slotEl, editionId, bookCode);
    });
  }
}

async function doUpload(slotEl, editionId, bookCode, file) {
  slotEl.classList.add('uploading');
  clearBanner(slotEl);
  const fd = new FormData();
  fd.append('file', file);
  try {
    const r = await fetch(uploadUrl(editionId, bookCode), {
      method: 'POST', body: fd,
    });
    const result = await r.json();
    if (!r.ok || result.error) {
      showBanner(slotEl, `upload failed: ${result.error || 'unknown error'}`);
      slotEl.classList.remove('uploading');
      return;
    }
    // Refresh from authoritative server state — single source of truth
    await loadCovers();
  } catch (e) {
    showBanner(slotEl, `upload failed: ${e.message}`);
    slotEl.classList.remove('uploading');
  }
}

async function doDelete(slotEl, editionId, bookCode) {
  slotEl.classList.add('uploading');
  clearBanner(slotEl);
  try {
    const r = await fetch(uploadUrl(editionId, bookCode), {method: 'DELETE'});
    const result = await r.json();
    if (!r.ok || result.error) {
      showBanner(slotEl, `delete failed: ${result.error || 'unknown error'}`);
      slotEl.classList.remove('uploading');
      return;
    }
    await loadCovers();
  } catch (e) {
    showBanner(slotEl, `delete failed: ${e.message}`);
    slotEl.classList.remove('uploading');
  }
}

function showBanner(slotEl, message) {
  const card = slotEl.closest('section');
  if (!card) { alert(message); return; }
  const banner = card.querySelector('.err-banner-host');
  banner.classList.remove('hidden');
  banner.classList.add('err-banner');
  banner.textContent = message;
  // Auto-clear after 6s so the page doesn't accumulate stale banners
  clearTimeout(banner._timer);
  banner._timer = setTimeout(() => clearBanner(slotEl), 6000);
}

function clearBanner(slotEl) {
  const card = slotEl.closest('section');
  if (!card) return;
  const banner = card.querySelector('.err-banner-host');
  if (banner) {
    banner.classList.add('hidden');
    banner.classList.remove('err-banner');
    banner.textContent = '';
  }
}

// Hidden file picker is shared across all slots; pendingTarget routes
// the chosen file to the right edition + book.
document.getElementById('hidden-file').addEventListener('change', (ev) => {
  const file = ev.target.files[0];
  if (!file || !pendingTarget) return;
  const card = document.querySelector(`section[data-edition="${pendingTarget.edition}"]`);
  // Find the slot element matching this target so the visual feedback
  // and any error banner appear on the right card.
  const slot = card && (
    pendingTarget.book
      ? [...card.querySelectorAll('.cover-slot')].find(s => {
          // we identify per-book slots by walking up to the cell that
          // displays the book code in its label
          const code = s.parentElement.querySelector('span.font-mono');
          return code && code.textContent.trim() === pendingTarget.book;
        })
      : card.querySelector('.cover-slot')   // first slot is main cover
  );
  doUpload(slot || card, pendingTarget.edition, pendingTarget.book, file);
  ev.target.value = '';   // reset so the same file can be chosen again
  pendingTarget = null;
});

loadCovers();
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
COVERS_HTML = COVERS_HTML.replace(
    "    <!-- HEADER_NAV_LINKS -->",
    HEADER_NAV_LINKS("/covers"),
)
COVERS_HTML = COVERS_HTML.replace(
    "<!-- BUYER_ARC_POLISH_CSS -->",
    BUYER_ARC_POLISH_CSS,
)

"""HTML for /compare console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import COMPARE_HTML` callers.

ψ.14 buyer-arc polish (2026-05-08): cross-link nav substituted from
`_design.HEADER_NAV_LINKS("/compare")` at module load.
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
    apply_design_system,
)

__all__ = ["COMPARE_HTML", "HEADER_NAV_LINKS", "BUYER_ARC_POLISH_CSS"]

COMPARE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>YHWH Ya' Way · Translation Comparison</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
  .verse-cell { vertical-align: top; }
  .verse-num { font-size: 0.7rem; color: #574532; font-family: ui-monospace, SFMono-Regular, monospace; }
  .missing { color: #6E5840; font-style: italic; }
  .translation-col { min-width: 18rem; max-width: 28rem; }
</style>
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Translation Comparison</h1>
    <p class="text-xs text-slate-500">side-by-side verse-by-verse rendering · buyer demo</p>
  </div>
  <div class="flex items-center gap-4 text-xs flex-wrap">
    <!-- HEADER_NAV_LINKS -->
    <span id="corpus-progress" class="ml-auto text-xs text-slate-500" title="corpus depth toward the 35,000-note Ethiopian Tewahedo target">·· loading ··</span>
  </div>
</header>

<main class="max-w-7xl mx-auto px-6 py-6">
  <!-- Controls bar -->
  <section class="bg-white rounded-lg border border-slate-200 p-4 mb-5">
    <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
      <div class="md:col-span-4">
        <label class="text-xs font-medium text-slate-600 block mb-1">Book</label>
        <select id="book-select" class="w-full text-sm border border-slate-300 rounded px-2 py-1.5"></select>
      </div>
      <div class="md:col-span-2">
        <label class="text-xs font-medium text-slate-600 block mb-1">Chapter</label>
        <input id="chapter-input" type="number" min="1" max="150" maxlength="3" value="1"
               class="w-full text-sm border border-slate-300 rounded px-2 py-1.5">
      </div>
      <div class="md:col-span-5">
        <label class="text-xs font-medium text-slate-600 block mb-1">Translations</label>
        <div id="translation-checkboxes" class="flex flex-wrap gap-3 text-sm">
          <span class="text-slate-400 italic">loading…</span>
        </div>
      </div>
      <div class="md:col-span-1">
        <button id="compare-btn" class="w-full text-sm px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-700 text-white font-medium" type="button">Show</button>
      </div>
    </div>
    <p id="status-line" class="text-xs text-slate-500 mt-3"></p>
  </section>

  <!-- Results table -->
  <section id="results" class="bg-white rounded-lg border border-slate-200 overflow-x-auto">
    <p class="text-slate-400 italic text-sm px-5 py-8 text-center">
      Pick a book + chapter and at least one translation, then click Show.
    </p>
  </section>
</main>

<script>
// Phase ψ.4 — translation comparison console. Reads canonical book
// list + translations from /api/customize-data, then queries
// /api/compare on demand. Uses window.ebible.safeFetch when
// available (ω.0.6) for unified error surfacing; falls back to raw
// fetch otherwise.
(function () {
  'use strict';

  const $ = sel => document.querySelector(sel);
  const escHtml = s => String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  const fetcher = (window.ebible && window.ebible.safeFetch)
    ? window.ebible.safeFetch
    : async function (url, opts) {
        const r = await fetch(url, opts);
        if (!r.ok) throw new Error(r.status + ' ' + r.statusText);
        return r.json();
      };

  let DATA = { books: [], translations: [] };

  function statusMsg(text, cls) {
    const el = $('#status-line');
    el.textContent = text || '';
    el.className = 'text-xs mt-3 ' + (cls || 'text-slate-500');
  }

  function populateBookSelect() {
    const sel = $('#book-select');
    sel.innerHTML = DATA.books.map(b =>
      `<option value="${escHtml(b.code)}">${escHtml(b.code)} — ${escHtml(b.title || b.name || b.code)}</option>`
    ).join('');
    if (DATA.books.length > 0) sel.value = DATA.books[0].code;
  }

  function populateTranslationCheckboxes() {
    const wrap = $('#translation-checkboxes');
    if (!DATA.translations || DATA.translations.length === 0) {
      wrap.innerHTML = '<span class="text-slate-400 italic">no translations available</span>';
      return;
    }
    wrap.innerHTML = DATA.translations.map((t, i) => {
      const id = String(t && t.id ? t.id : t);
      const label = (t && (t.short_title || t.name || t.title)) || id;
      const checked = i === 0 ? 'checked' : '';
      return `<label class="flex items-center gap-1.5 cursor-pointer">
        <input type="checkbox" class="t-check" value="${escHtml(id)}" ${checked}>
        <span>${escHtml(label)} <span class="text-slate-400 text-xs">(${escHtml(id)})</span></span>
      </label>`;
    }).join('');
  }

  function selectedTranslations() {
    return Array.from(document.querySelectorAll('.t-check:checked')).map(c => c.value);
  }

  function renderResults(data) {
    const root = $('#results');
    if (!data.translations || data.translations.length === 0) {
      root.innerHTML = '<p class="text-slate-500 italic text-sm px-5 py-8 text-center">No translations selected.</p>';
      return;
    }
    if (!data.verses || data.verses.length === 0) {
      root.innerHTML = `<p class="text-slate-500 italic text-sm px-5 py-8 text-center">
        No verses for ${escHtml(data.book)} ${escHtml(String(data.chapter))} in the selected translation(s).
      </p>`;
      return;
    }
    const headers = data.translations.map(t =>
      `<th class="text-left px-4 py-2 text-xs font-semibold uppercase text-slate-600 translation-col">${escHtml(t)}</th>`
    ).join('');
    const rows = data.verses.map(v => {
      const cells = data.translations.map(t => {
        const text = v.by_translation[t];
        if (text == null) {
          return `<td class="verse-cell px-4 py-2 missing">—</td>`;
        }
        return `<td class="verse-cell px-4 py-2 text-sm leading-relaxed">${escHtml(text)}</td>`;
      }).join('');
      return `<tr class="border-t border-slate-100">
        <td class="verse-cell px-3 py-2 verse-num text-right">${v.verse}</td>
        ${cells}
      </tr>`;
    }).join('');
    root.innerHTML = `<table class="w-full">
      <thead class="bg-slate-50">
        <tr>
          <th class="px-3 py-2 w-10"></th>
          ${headers}
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
  }

  async function doCompare() {
    const book = $('#book-select').value;
    const chapter = $('#chapter-input').value;
    const translations = selectedTranslations();
    if (!book) { statusMsg('Pick a book.', 'text-amber-700'); return; }
    if (!chapter || parseInt(chapter, 10) < 1) {
      statusMsg('Chapter must be ≥ 1.', 'text-amber-700');
      return;
    }
    if (translations.length === 0) {
      statusMsg('Select at least one translation.', 'text-amber-700');
      return;
    }
    statusMsg('Loading…');
    try {
      const url = `/api/compare?book=${encodeURIComponent(book)}` +
                  `&chapter=${encodeURIComponent(chapter)}` +
                  `&translations=${encodeURIComponent(translations.join(','))}`;
      const data = await fetcher(url);
      if (data && data.error) {
        statusMsg('✗ ' + data.error, 'text-red-600');
        return;
      }
      const missing = data.missing_translations || [];
      if (missing.length > 0) {
        statusMsg('Note: unknown translations skipped: ' + missing.join(', '), 'text-amber-700');
      } else {
        statusMsg(`${data.verse_count} verse${data.verse_count === 1 ? '' : 's'} across ${data.translations.length} translation${data.translations.length === 1 ? '' : 's'}.`);
      }
      renderResults(data);
    } catch (e) {
      statusMsg('✗ ' + (e.message || 'request failed'), 'text-red-600');
    }
  }

  async function bootstrap() {
    try {
      const customizeData = await fetcher('/api/customize-data');
      // books_canonical is a list of {code, name, ...} objects
      DATA.books = customizeData.books_canonical || [];
      // translations is a list of {id, name, ...} or strings
      DATA.translations = customizeData.translations || [];
      populateBookSelect();
      populateTranslationCheckboxes();
      // Auto-render Genesis 1 KJV on load — buyer demo first impression
      doCompare();
    } catch (e) {
      statusMsg('Could not load book/translation list: ' + (e.message || ''), 'text-red-600');
    }
  }

  document.getElementById('compare-btn').addEventListener('click', doCompare);
  // Pressing Enter in the chapter input also triggers
  document.getElementById('chapter-input').addEventListener('keydown', ev => {
    if (ev.key === 'Enter') { ev.preventDefault(); doCompare(); }
  });

  bootstrap();
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


# ψ.13.5: consolidated design-system substitution. Equivalent to
# the prior two-replace sequence but routed through one helper so
# new markers land in exactly one place going forward.
COMPARE_HTML = apply_design_system(COMPARE_HTML, "/compare")

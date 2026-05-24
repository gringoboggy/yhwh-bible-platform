"""HTML for /audit console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import AUDIT_HTML` callers.

ψ.16 status-dashboard polish (2026-05-09): cross-link nav
substituted from `_design.HEADER_NAV_LINKS("/audit")` and
`BUYER_ARC_POLISH_CSS` inlined from `_design`.
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
    apply_design_system,
)

__all__ = ["AUDIT_HTML", "HEADER_NAV_LINKS", "BUYER_ARC_POLISH_CSS"]

AUDIT_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>YHWH Ya' Way · Attribution Audit</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
  .verse-anchor { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
  .pill { display: inline-block; padding: 0.1em 0.6em; border-radius: 9999px; font-size: 0.75em; }
</style>
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Attribution Audit</h1>
    <p class="text-xs text-slate-500">quality control for note sources · find missing or thin attributions before shipping</p>
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


<main class="p-6 max-w-6xl mx-auto">

  <div id="loading" class="text-center text-slate-400 py-20">scanning corpus …</div>
  <div id="content" class="hidden">

    <!-- Counts grid -->
    <section class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
      <div class="bg-white rounded-lg border border-slate-200 p-3">
        <div class="text-xs uppercase tracking-wide text-slate-500">Total notes</div>
        <div id="c-total" class="text-2xl font-bold"></div>
      </div>
      <div class="bg-white rounded-lg border border-emerald-300 p-3">
        <div class="text-xs uppercase tracking-wide text-emerald-700">Sourced</div>
        <div id="c-sourced" class="text-2xl font-bold text-emerald-700"></div>
        <div class="text-xs text-slate-500">references real source</div>
      </div>
      <div class="bg-white rounded-lg border border-blue-300 p-3">
        <div class="text-xs uppercase tracking-wide text-blue-700">User-original</div>
        <div id="c-user" class="text-2xl font-bold text-blue-700"></div>
        <div class="text-xs text-slate-500">user paraphrase / original</div>
      </div>
      <div class="bg-white rounded-lg border border-amber-300 p-3">
        <div class="text-xs uppercase tracking-wide text-amber-700">Thin</div>
        <div id="c-thin" class="text-2xl font-bold text-amber-700"></div>
        <div class="text-xs text-slate-500">vague or too-short</div>
      </div>
      <div class="bg-white rounded-lg border border-red-300 p-3">
        <div class="text-xs uppercase tracking-wide text-red-700">Missing</div>
        <div id="c-missing" class="text-2xl font-bold text-red-700"></div>
        <div class="text-xs text-slate-500">empty / whitespace</div>
      </div>
    </section>

    <!-- Empty state -->
    <section id="empty-state" class="hidden bg-white rounded-lg border border-slate-200 p-8 text-center">
      <div class="text-3xl mb-2">✓</div>
      <h2 class="text-lg font-semibold text-emerald-700 mb-1">All clear</h2>
      <p class="text-sm text-slate-600">Every note has at least minimal attribution. Run this audit again after adding new content.</p>
    </section>

    <!-- Issues view -->
    <section id="issues-view" class="hidden grid grid-cols-1 lg:grid-cols-[18rem_1fr] gap-6">

      <aside class="space-y-4">
        <div class="bg-white rounded-lg shadow-sm border border-slate-200">
          <div class="px-3 py-2 border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">By book</div>
          <ul id="by-book" class="divide-y divide-slate-100 text-sm"></ul>
        </div>
        <div class="bg-white rounded-lg shadow-sm border border-slate-200">
          <div class="px-3 py-2 border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">By kind</div>
          <ul id="by-kind" class="divide-y divide-slate-100 text-sm"></ul>
        </div>
      </aside>

      <section class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-200 flex items-center justify-between flex-wrap gap-2">
          <h2 class="font-semibold">Notes needing attention</h2>
          <div class="flex items-center gap-2 flex-wrap">
            <input id="filter-text" type="text" placeholder="filter…" maxlength="200" class="text-sm border border-slate-300 rounded px-2 py-1 w-56">
            <select id="filter-class" class="text-sm border border-slate-300 rounded px-2 py-1">
              <option value="">all (missing + thin)</option>
              <option value="missing">missing only</option>
              <option value="thin">thin only</option>
            </select>
          </div>
        </div>
        <div id="issue-list" class="divide-y divide-slate-100"></div>
      </section>
    </section>
  </div>
</main>

<script>
let DATA = null;
let CLASS_FILTER = '';
let TEXT_FILTER = '';

async function init() {
  const r = await fetch('/api/audit/attribution');
  DATA = await r.json();
  document.getElementById('loading').classList.add('hidden');
  document.getElementById('content').classList.remove('hidden');

  const c = DATA.counts;
  document.getElementById('c-total').textContent = c.total.toLocaleString();
  document.getElementById('c-sourced').textContent = (c.sourced || 0).toLocaleString();
  document.getElementById('c-user').textContent = (c.user || 0).toLocaleString();
  document.getElementById('c-thin').textContent = (c.thin || 0).toLocaleString();
  document.getElementById('c-missing').textContent = (c.missing || 0).toLocaleString();

  if (!DATA.needs_attention.length) {
    document.getElementById('empty-state').classList.remove('hidden');
    return;
  }
  document.getElementById('issues-view').classList.remove('hidden');
  renderRails();
  renderIssues();
  document.getElementById('filter-text').addEventListener('input', e => {
    TEXT_FILTER = e.target.value.toLowerCase();
    renderIssues();
  });
  document.getElementById('filter-class').addEventListener('change', e => {
    CLASS_FILTER = e.target.value;
    renderIssues();
  });
}

function renderRails() {
  const bb = document.getElementById('by-book');
  bb.innerHTML = DATA.by_book.map(b => `
    <li class="px-3 py-1.5 hover:bg-slate-50 cursor-pointer book-jump" data-book="${b.code}">
      <div class="flex justify-between">
        <span>${b.title}</span>
        <span class="text-xs font-mono">
          ${b.missing ? `<span class="text-red-600">${b.missing}</span>` : ''}
          ${b.thin ? ` <span class="text-amber-600">${b.thin}</span>` : ''}
        </span>
      </div>
    </li>
  `).join('');
  bb.querySelectorAll('.book-jump').forEach(el => {
    el.addEventListener('click', () => {
      document.getElementById('filter-text').value = el.dataset.book;
      TEXT_FILTER = el.dataset.book;
      renderIssues();
    });
  });

  const bk = document.getElementById('by-kind');
  bk.innerHTML = DATA.by_kind.slice(0, 20).map(k => `
    <li class="px-3 py-1.5 hover:bg-slate-50 cursor-pointer kind-jump" data-kind="${k.kind}">
      <div class="flex justify-between">
        <span class="font-mono text-xs">${k.kind}</span>
        <span class="text-xs font-mono text-slate-500">${k.count}</span>
      </div>
    </li>
  `).join('');
  bk.querySelectorAll('.kind-jump').forEach(el => {
    el.addEventListener('click', () => {
      document.getElementById('filter-text').value = el.dataset.kind;
      TEXT_FILTER = el.dataset.kind;
      renderIssues();
    });
  });
}

function renderIssues() {
  let items = DATA.needs_attention;
  if (CLASS_FILTER) items = items.filter(i => i.classification === CLASS_FILTER);
  if (TEXT_FILTER) {
    items = items.filter(i =>
      (i.book || '').toLowerCase().includes(TEXT_FILTER) ||
      (i.book_title || '').toLowerCase().includes(TEXT_FILTER) ||
      (i.kind || '').toLowerCase().includes(TEXT_FILTER) ||
      (i.title || '').toLowerCase().includes(TEXT_FILTER) ||
      (i.body_preview || '').toLowerCase().includes(TEXT_FILTER) ||
      (i.attribution || '').toLowerCase().includes(TEXT_FILTER)
    );
  }
  const wrap = document.getElementById('issue-list');
  if (!items.length) {
    wrap.innerHTML = '<div class="p-6 text-center text-slate-400 text-sm">no notes match the filter</div>';
    return;
  }
  wrap.innerHTML = items.slice(0, 200).map(n => {
    const tagColor = n.classification === 'missing' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700';
    return `
      <div class="px-4 py-3">
        <div class="flex items-baseline justify-between gap-2 flex-wrap">
          <div class="flex items-baseline gap-2 flex-wrap">
            <span class="verse-anchor text-xs text-slate-500">${n.book} ${n.chapter}:${n.verse}${n.suffix || ''}</span>
            <span class="text-xs px-1.5 py-0.5 rounded font-mono bg-slate-100">${escapeHTML(n.kind)}</span>
            <span class="pill ${tagColor}">${n.classification}</span>
          </div>
          <a href="/sources" class="text-xs text-blue-600 hover:underline">→ open in sources</a>
        </div>
        <div class="text-sm text-slate-700 mt-1">${escapeHTML(n.body_preview)}${n.body_preview.length >= 120 ? '…' : ''}</div>
        ${n.attribution ? `<div class="text-xs text-amber-700 mt-1">attribution: <em>${escapeHTML(n.attribution)}</em></div>` : '<div class="text-xs text-red-600 mt-1">⚠ no attribution at all</div>'}
      </div>
    `;
  }).join('') + (items.length > 200 ? `<div class="p-3 text-center text-xs text-slate-500">showing first 200 of ${items.length} — narrow the filter to see specific items</div>` : '');
}

function escapeHTML(s) {
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
AUDIT_HTML = apply_design_system(AUDIT_HTML, "/audit")

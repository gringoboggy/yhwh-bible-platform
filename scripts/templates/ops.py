"""HTML for /ops console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import OPS_HTML` callers.

ψ.16 status-dashboard polish (2026-05-09): cross-link nav
substituted from `_design.HEADER_NAV_LINKS("/ops")` and
`BUYER_ARC_POLISH_CSS` inlined from `_design`.
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
    apply_design_system,
)

__all__ = ["OPS_HTML", "HEADER_NAV_LINKS", "BUYER_ARC_POLISH_CSS"]

OPS_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>YHWH Ya' Way · Operator Dashboard</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
</style>
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Operator Dashboard</h1>
    <p class="text-xs text-slate-500">system health at a glance</p>
  </div>
  <div class="flex items-center gap-4 text-xs flex-wrap">
    <!-- HEADER_NAV_LINKS -->
    <span id="corpus-progress" class="ml-auto text-xs text-slate-500" title="corpus depth toward the 35,000-note Ethiopian Tewahedo target">·· loading ··</span>
  </div>
</header>

<main class="max-w-7xl mx-auto px-6 py-6">
  <!-- Phase ψ.6 — operator dashboard. Composes existing endpoints
       per Rule §9: every metric here is a tiny query against
       already-cached data, no new computation engine. -->

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6" id="ops-grid">
    <!-- Corpus -->
    <section class="bg-white rounded-lg border border-slate-200 p-4">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-sm font-semibold text-slate-700">Corpus</h2>
        <span class="text-xs text-slate-400">notes toward 35K Ethiopian flagship</span>
      </div>
      <div class="text-3xl font-bold text-slate-900" id="m-corpus-current">··</div>
      <div class="text-xs text-slate-500" id="m-corpus-detail">loading…</div>
      <div class="mt-2 h-1.5 bg-slate-100 rounded overflow-hidden">
        <div id="m-corpus-bar" class="h-full bg-emerald-500" style="width:0%"></div>
      </div>
    </section>

    <!-- Attribution -->
    <section class="bg-white rounded-lg border border-slate-200 p-4">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-sm font-semibold text-slate-700">Attribution health</h2>
        <span class="text-xs text-slate-400">notes with sources cited</span>
      </div>
      <div class="text-3xl font-bold text-slate-900" id="m-attr-pct">··</div>
      <div class="text-xs text-slate-500" id="m-attr-detail">loading…</div>
    </section>

    <!-- Preflight -->
    <section class="bg-white rounded-lg border border-slate-200 p-4">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-sm font-semibold text-slate-700">Preflight</h2>
        <a href="/preflight" class="text-xs text-blue-600 hover:underline">view full →</a>
      </div>
      <div id="m-preflight-status" class="text-3xl font-bold text-slate-900">··</div>
      <div class="text-xs text-slate-500" id="m-preflight-detail">loading…</div>
      <button id="m-preflight-run" class="mt-3 text-xs px-3 py-1 rounded border border-slate-300 hover:border-blue-500 hover:text-blue-700 text-slate-700" type="button">Run preflight now</button>
    </section>

    <!-- Save tag -->
    <section class="bg-white rounded-lg border border-slate-200 p-4">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-sm font-semibold text-slate-700">Last save</h2>
        <span class="text-xs text-slate-400">most recent CHANGELOG entry</span>
      </div>
      <div class="text-xl font-mono text-slate-900" id="m-save-tag">··</div>
      <div class="text-xs text-slate-500" id="m-save-detail">loading…</div>
    </section>

    <!-- Uptime -->
    <section class="bg-white rounded-lg border border-slate-200 p-4">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-sm font-semibold text-slate-700">Server uptime</h2>
        <span class="text-xs text-slate-400">since process start</span>
      </div>
      <div class="text-3xl font-bold text-slate-900" id="m-uptime">··</div>
      <div class="text-xs text-slate-500">module-load time, refreshes on restart</div>
    </section>

    <!-- Disk -->
    <section class="bg-white rounded-lg border border-slate-200 p-4">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-sm font-semibold text-slate-700">Disk free</h2>
        <span class="text-xs text-slate-400">on content/</span>
      </div>
      <div class="text-3xl font-bold text-slate-900" id="m-disk-free">··</div>
      <div class="text-xs text-slate-500" id="m-disk-detail">loading…</div>
    </section>
  </div>

  <p class="text-xs text-slate-400 italic text-center" id="ops-status">refreshing every 30s · click any tile for details</p>
</main>

<script>
// Phase ψ.6 — operator dashboard. Pulls /api/ops every 30s and
// updates each tile. Each section in the response has a 'status'
// field so partial failures show inline rather than crashing the
// whole page.
(function () {
  'use strict';

  const fetcher = (window.ebible && window.ebible.safeFetch)
    ? window.ebible.safeFetch
    : async function (url, opts) {
        const r = await fetch(url, opts);
        if (!r.ok) throw new Error(r.status + ' ' + r.statusText);
        return r.json();
      };

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function renderError(prefix, message) {
    return prefix + ' (' + (message || 'error') + ')';
  }

  async function refresh() {
    let data;
    try {
      data = await fetcher('/api/ops');
    } catch (e) {
      setText('ops-status', '✗ refresh failed: ' + e.message);
      return;
    }

    // Corpus
    if (data.corpus && data.corpus.status === 'ok') {
      const c = data.corpus;
      setText('m-corpus-current', (c.current || 0).toLocaleString());
      setText('m-corpus-detail', (c.percent || 0).toFixed(1) + '% of ' +
              (c.target || 0).toLocaleString() + ' target');
      const bar = document.getElementById('m-corpus-bar');
      if (bar) bar.style.width = Math.min(100, c.percent || 0) + '%';
    } else {
      setText('m-corpus-detail', renderError('error',
              data.corpus && data.corpus.message));
    }

    // Attribution
    if (data.attribution && data.attribution.status === 'ok') {
      const a = data.attribution;
      setText('m-attr-pct', (a.percent || 0).toFixed(1) + '%');
      setText('m-attr-detail', (a.attributed || 0).toLocaleString() +
              ' / ' + (a.total || 0).toLocaleString() + ' notes attributed');
    } else {
      setText('m-attr-detail', renderError('error',
              data.attribution && data.attribution.message));
    }

    // Preflight
    if (data.preflight && data.preflight.status === 'ok') {
      const p = data.preflight;
      const failed = p.items_failed || 0;
      const warn = p.items_warn || 0;
      const ok = p.items_ok || 0;
      let summary;
      if (failed > 0) summary = '✗ ' + failed + ' failing';
      else if (warn > 0) summary = '⚠ ' + warn + ' warning';
      else if (ok > 0) summary = '✓ all clear';
      else summary = '— no checks';
      setText('m-preflight-status', summary);
      setText('m-preflight-detail',
              ok + ' pass · ' + warn + ' warn · ' + failed + ' fail · ' +
              (p.items_total || 0) + ' total');
    } else {
      setText('m-preflight-detail', renderError('error',
              data.preflight && data.preflight.message));
    }

    // Save tag
    if (data.save_tag && data.save_tag.status === 'ok') {
      setText('m-save-tag', data.save_tag.name || '(unknown)');
      setText('m-save-detail', 'from CHANGELOG.md');
    }

    // Uptime
    if (data.uptime && data.uptime.status === 'ok') {
      setText('m-uptime', data.uptime.human || '0s');
    }

    // Disk
    if (data.disk && data.disk.status === 'ok') {
      const d = data.disk;
      setText('m-disk-free', d.free_human || '?');
      setText('m-disk-detail', (d.used_pct || 0).toFixed(1) + '% used overall');
    } else {
      setText('m-disk-detail', renderError('error',
              data.disk && data.disk.message));
    }

    setText('ops-status', 'refreshed: ' + new Date().toLocaleTimeString() +
                          ' · auto-refresh every 30s');
  }

  // "Run preflight now" — just navigate to /preflight; that page
  // re-runs everything on load
  const btn = document.getElementById('m-preflight-run');
  if (btn) btn.addEventListener('click', () => {
    window.location.href = '/preflight';
  });

  refresh();
  setInterval(refresh, 30000);
})();
</script>

<script>
// Phase ψ.3 — corpus progress widget. Cheap fetch + DOM update;
// silently no-ops on failure so a stale browser tab never breaks.
(function () {
  fetch('/api/corpus-progress').then(function (r) { return r.json(); })
    .then(function (d) {
      var el = document.getElementById('corpus-progress');
      if (!el) return;
      var cur = (d.current || 0).toLocaleString();
      var tgt = (d.target || 0).toLocaleString();
      var pct = (typeof d.percent === 'number') ? d.percent.toFixed(1) : '0.0';
      el.textContent = cur + ' / ' + tgt + ' (' + pct + '%)';
    })
    .catch(function () { /* swallow */ });
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
OPS_HTML = apply_design_system(OPS_HTML, "/ops")

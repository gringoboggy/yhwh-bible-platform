"""HTML for /apihelp console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import APIHELP_HTML` callers.
"""

APIHELP_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>E-Bible · API Reference</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
</style>
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">API Reference</h1>
    <p class="text-xs text-slate-500">auto-generated index of /api/* endpoints</p>
  </div>
  <div class="flex items-center gap-4 text-xs">
    <a href="/" class="text-blue-600 hover:underline">note editor</a>
    <a href="/matrix" class="text-blue-600 hover:underline">matrix</a>
    <a href="/sources" class="text-blue-600 hover:underline">sources</a>
    <a href="/export" class="text-blue-600 hover:underline">export</a>
    <a href="/customize" class="text-blue-600 hover:underline">customize</a>
    <a href="/audit" class="text-blue-600 hover:underline">audit</a>
    <a href="/publisher" class="text-blue-600 hover:underline">publisher</a>
    <a href="/wizard" class="text-blue-600 hover:underline">wizard</a>
    <a href="/diff" class="text-blue-600 hover:underline">diff</a>
    <a href="/preflight" class="text-blue-600 hover:underline">preflight</a>
    <a href="/covers" class="text-blue-600 hover:underline">covers</a>
    <a href="/compare" class="text-blue-600 hover:underline">compare</a>
    <a href="/ops" class="text-blue-600 hover:underline">ops</a>
    <a href="/apihelp" class="font-semibold">apihelp</a>
    <span id="corpus-progress" class="ml-auto text-xs text-slate-500" title="corpus depth toward the 35,000-note Ethiopian Tewahedo target">·· loading ··</span>
  </div>
</header>

<main class="max-w-7xl mx-auto px-6 py-6">
  <!-- Phase ω.3 — API reference. Auto-enumerates routes from
       scripts/web.py source; nothing here is hand-maintained,
       so adding a new route to web.py automatically shows up
       here on next page load. Recursion check: this page must
       appear in its own console list. -->

  <p class="text-sm text-slate-500 mb-4" id="api-help-status">loading routes…</p>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
    <div class="bg-white rounded-lg border border-slate-200 p-4">
      <div class="text-xs uppercase text-slate-500">API endpoints</div>
      <div class="text-3xl font-bold text-slate-900" id="api-count">··</div>
    </div>
    <div class="bg-white rounded-lg border border-slate-200 p-4">
      <div class="text-xs uppercase text-slate-500">HTML consoles</div>
      <div class="text-3xl font-bold text-slate-900" id="console-count">··</div>
    </div>
  </div>

  <section class="bg-white rounded-lg border border-slate-200 p-4 mb-4">
    <h2 class="font-semibold text-slate-800 mb-2">HTML consoles</h2>
    <p class="text-xs text-slate-500 mb-3">user-facing pages — visit each via the nav above</p>
    <table class="w-full text-sm">
      <thead><tr class="border-b text-xs uppercase text-slate-500">
        <th class="text-left py-1 pr-3">Path</th>
        <th class="text-left py-1 pr-3">Phase</th>
        <th class="text-left py-1">Description</th>
      </tr></thead>
      <tbody id="consoles-body"><tr><td colspan="3" class="text-slate-400 italic py-3">loading…</td></tr></tbody>
    </table>
  </section>

  <section class="bg-white rounded-lg border border-slate-200 p-4">
    <h2 class="font-semibold text-slate-800 mb-2">API endpoints</h2>
    <p class="text-xs text-slate-500 mb-3">JSON / data routes — useful for integrations and future Claude orientation</p>
    <table class="w-full text-sm">
      <thead><tr class="border-b text-xs uppercase text-slate-500">
        <th class="text-left py-1 pr-3 w-20">Method</th>
        <th class="text-left py-1 pr-3">Path</th>
        <th class="text-left py-1 pr-3 w-20">Phase</th>
        <th class="text-left py-1">Description</th>
      </tr></thead>
      <tbody id="api-body"><tr><td colspan="4" class="text-slate-400 italic py-3">loading…</td></tr></tbody>
    </table>
  </section>
</main>

<script>
// Phase ω.3 — API reference page. Reads /api/apihelp and renders
// two tables (consoles + API routes). The data is computed by
// regex-scanning scripts/web.py source on every request — that's
// fine, the file is small and the scan is cheap.
(function () {
  'use strict';

  const fetcher = (window.ebible && window.ebible.safeFetch)
    ? window.ebible.safeFetch
    : async function (url) {
        const r = await fetch(url);
        if (!r.ok) throw new Error(r.status + ' ' + r.statusText);
        return r.json();
      };

  const escape = (window.ebible && window.ebible.escapeHtml)
    ? window.ebible.escapeHtml
    : (s) => String(s == null ? '' : s).replace(/[&<>"']/g,
        c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function methodBadge(m) {
    const colors = {
      'GET': 'bg-blue-100 text-blue-800',
      'POST': 'bg-emerald-100 text-emerald-800',
      'GET/POST': 'bg-purple-100 text-purple-800',
    };
    const cls = colors[m] || 'bg-slate-100 text-slate-800';
    return `<span class="inline-block ${cls} text-xs font-mono px-2 py-0.5 rounded">${escape(m)}</span>`;
  }

  function phaseBadge(p) {
    if (!p) return '<span class="text-xs text-slate-400">—</span>';
    return `<span class="text-xs font-mono text-slate-600">${escape(p)}</span>`;
  }

  function truncate(s, n) {
    if (!s) return '';
    if (s.length <= n) return s;
    return s.slice(0, n) + '…';
  }

  async function load() {
    let data;
    try {
      data = await fetcher('/api/apihelp');
    } catch (e) {
      document.getElementById('api-help-status').textContent = '✗ load failed: ' + e.message;
      return;
    }

    document.getElementById('api-count').textContent = data.totals.api;
    document.getElementById('console-count').textContent = data.totals.consoles;
    document.getElementById('api-help-status').textContent =
        'auto-enumerated by scanning scripts/web.py source';

    // Console rows
    const consolesBody = document.getElementById('consoles-body');
    if (data.consoles.length === 0) {
      consolesBody.innerHTML = '<tr><td colspan="3" class="text-slate-400 italic py-3">no consoles found</td></tr>';
    } else {
      consolesBody.innerHTML = data.consoles.map(c => `
        <tr class="border-b border-slate-100 hover:bg-slate-50">
          <td class="py-1.5 pr-3"><a href="${escape(c.path)}" class="font-mono text-blue-600 hover:underline">${escape(c.path)}</a></td>
          <td class="py-1.5 pr-3">${phaseBadge(c.phase)}</td>
          <td class="py-1.5 text-slate-600">${escape(truncate(c.description, 100))}</td>
        </tr>`).join('');
    }

    // API route rows
    const apiBody = document.getElementById('api-body');
    if (data.api_routes.length === 0) {
      apiBody.innerHTML = '<tr><td colspan="4" class="text-slate-400 italic py-3">no API routes found</td></tr>';
    } else {
      apiBody.innerHTML = data.api_routes.map(r => `
        <tr class="border-b border-slate-100 hover:bg-slate-50">
          <td class="py-1.5 pr-3">${methodBadge(r.method)}</td>
          <td class="py-1.5 pr-3"><span class="font-mono text-slate-800">${escape(r.path)}</span></td>
          <td class="py-1.5 pr-3">${phaseBadge(r.phase)}</td>
          <td class="py-1.5 text-slate-600">${escape(truncate(r.description, 90))}</td>
        </tr>`).join('');
    }
  }

  load();
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

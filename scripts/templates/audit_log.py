"""HTML for /audit-log console (ξ.13) — read-only browser over the
append-only mutation ledger written by `scripts.core.audit_log`.

Companion to /audit (attribution-quality control); this surface
answers the *retail / compliance* question instead: "what changed,
who changed it, when, and was it ok?". The data source is
`<user_data>/audit/<YYYY-MM>.ndjson`; entries arrive via the
`@audit_log.audit_endpoint` decorator on every mutation route in
scripts/web.py.

ψ.13.5 design-system substitution applied at module load (matches
audit.py + every other console template).
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
    apply_design_system,
)

__all__ = ["AUDIT_LOG_HTML", "HEADER_NAV_LINKS", "BUYER_ARC_POLISH_CSS"]

AUDIT_LOG_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>E-Bible · Mutation Audit Log</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
  .mono { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
  .pill { display: inline-block; padding: 0.1em 0.6em; border-radius: 9999px; font-size: 0.75em; }
</style>
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Mutation Audit Log</h1>
    <p class="text-xs text-slate-500">append-only ledger of every save / create / delete · retail compliance trail · ξ.13</p>
  </div>
  <div class="flex items-center gap-4 text-xs flex-wrap">
    <!-- HEADER_NAV_LINKS -->
    <span id="corpus-progress" class="ml-auto text-xs text-slate-500" title="corpus depth toward the 35,000-note Ethiopian Tewahedo target">·· loading ··</span>
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


<main class="p-6 max-w-6xl mx-auto">

  <div id="loading" class="text-center text-slate-400 py-20">reading audit log …</div>
  <div id="content" class="hidden">

    <!-- Counts grid -->
    <section class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      <div class="bg-white rounded-lg border border-slate-200 p-3">
        <div class="text-xs uppercase tracking-wide text-slate-500">Entries shown</div>
        <div id="c-shown" class="text-2xl font-bold">0</div>
      </div>
      <div class="bg-white rounded-lg border border-emerald-300 p-3">
        <div class="text-xs uppercase tracking-wide text-emerald-700">Ok</div>
        <div id="c-ok" class="text-2xl font-bold text-emerald-700">0</div>
      </div>
      <div class="bg-white rounded-lg border border-red-300 p-3">
        <div class="text-xs uppercase tracking-wide text-red-700">Error</div>
        <div id="c-error" class="text-2xl font-bold text-red-700">0</div>
      </div>
      <div class="bg-white rounded-lg border border-amber-300 p-3">
        <div class="text-xs uppercase tracking-wide text-amber-700">Raised</div>
        <div id="c-raised" class="text-2xl font-bold text-amber-700">0</div>
      </div>
    </section>

    <!-- Empty state -->
    <section id="empty-state" class="hidden bg-white rounded-lg border border-slate-200 p-8 text-center">
      <div class="text-3xl mb-2">·</div>
      <h2 class="text-lg font-semibold mb-1">No entries yet</h2>
      <p class="text-sm text-slate-600">The audit log captures every save / create / delete. Make a change in any console to populate it.</p>
    </section>

    <!-- Filterable list -->
    <section id="entries-view" class="hidden bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      <div class="px-4 py-3 border-b border-slate-200 flex items-center justify-between flex-wrap gap-2">
        <h2 class="font-semibold">Recent mutations</h2>
        <div class="flex items-center gap-2 flex-wrap">
          <input id="filter-text" type="text" placeholder="filter endpoint / action / args…" maxlength="200" class="text-sm border border-slate-300 rounded px-2 py-1 w-72">
          <select id="filter-result" class="text-sm border border-slate-300 rounded px-2 py-1">
            <option value="">all results</option>
            <option value="ok">ok only</option>
            <option value="error">error only</option>
            <option value="raised">raised only</option>
          </select>
          <button id="refresh-btn" type="button" class="text-sm border border-slate-300 rounded px-3 py-1 bg-white hover:bg-slate-50">refresh</button>
        </div>
      </div>
      <div id="entry-list" class="divide-y divide-slate-100"></div>
    </section>
  </div>
</main>

<script>
let DATA = null;
let RESULT_FILTER = '';
let TEXT_FILTER = '';

async function loadEntries() {
  document.getElementById('loading').classList.remove('hidden');
  document.getElementById('content').classList.add('hidden');
  try {
    DATA = await window.safeFetch('/api/audit-log?n=200');
  } catch (_e) {
    document.getElementById('loading').textContent = 'failed to load audit log';
    return;
  }
  document.getElementById('loading').classList.add('hidden');
  document.getElementById('content').classList.remove('hidden');
  render();
}

function render() {
  const entries = (DATA && DATA.entries) || [];
  document.getElementById('c-shown').textContent = entries.length.toLocaleString();
  let ok = 0, err = 0, raised = 0;
  entries.forEach(function (e) {
    if (e.result === 'ok') ok++;
    else if (e.result === 'raised') raised++;
    else if (e.result === 'error') err++;
  });
  document.getElementById('c-ok').textContent = ok.toLocaleString();
  document.getElementById('c-error').textContent = err.toLocaleString();
  document.getElementById('c-raised').textContent = raised.toLocaleString();

  if (!entries.length) {
    document.getElementById('empty-state').classList.remove('hidden');
    document.getElementById('entries-view').classList.add('hidden');
    return;
  }
  document.getElementById('empty-state').classList.add('hidden');
  document.getElementById('entries-view').classList.remove('hidden');
  renderEntries(entries);
}

function renderEntries(entries) {
  let items = entries;
  if (RESULT_FILTER) items = items.filter(function (e) { return e.result === RESULT_FILTER; });
  if (TEXT_FILTER) {
    items = items.filter(function (e) {
      return ((e.endpoint || '').toLowerCase().includes(TEXT_FILTER) ||
              (e.action || '').toLowerCase().includes(TEXT_FILTER) ||
              JSON.stringify(e.args || {}).toLowerCase().includes(TEXT_FILTER) ||
              (e.code || '').toLowerCase().includes(TEXT_FILTER));
    });
  }
  const wrap = document.getElementById('entry-list');
  if (!items.length) {
    wrap.innerHTML = '<div class="p-6 text-center text-slate-400 text-sm">no entries match the filter</div>';
    return;
  }
  wrap.innerHTML = items.slice(0, 500).map(function (e) {
    const colorMap = {
      ok: 'bg-emerald-100 text-emerald-700',
      error: 'bg-red-100 text-red-700',
      raised: 'bg-amber-100 text-amber-700',
    };
    const tagColor = colorMap[e.result] || 'bg-slate-100 text-slate-700';
    const argsStr = (function () {
      try { return JSON.stringify(e.args || {}); }
      catch (_) { return '{}'; }
    })();
    const ts = (e.timestamp || '').replace('T', ' ').replace('Z', '');
    return (
      '<div class="px-4 py-3">' +
        '<div class="flex items-baseline justify-between gap-2 flex-wrap">' +
          '<div class="flex items-baseline gap-2 flex-wrap">' +
            '<span class="mono text-xs text-slate-500">' + window.escapeHtml(ts) + '</span>' +
            '<span class="text-xs px-1.5 py-0.5 rounded font-mono bg-slate-100">' + window.escapeHtml(e.endpoint || '') + '</span>' +
            '<span class="pill ' + tagColor + '">' + window.escapeHtml(e.result || '') + '</span>' +
            (e.action && e.action !== e.endpoint ? '<span class="text-xs text-slate-400">→ ' + window.escapeHtml(e.action) + '</span>' : '') +
            (typeof e.elapsed_ms === 'number' ? '<span class="text-xs text-slate-400">' + e.elapsed_ms.toFixed(1) + ' ms</span>' : '') +
          '</div>' +
          (e.code ? '<span class="text-xs text-red-600 mono">' + window.escapeHtml(e.code) + '</span>' : '') +
        '</div>' +
        '<div class="text-xs text-slate-600 mt-1 mono break-all">' + window.escapeHtml(argsStr.slice(0, 400)) + (argsStr.length > 400 ? '…' : '') + '</div>' +
      '</div>'
    );
  }).join('') + (items.length > 500 ? '<div class="p-3 text-center text-xs text-slate-500">showing first 500 of ' + items.length + ' — narrow the filter to see specific items</div>' : '');
}

document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('filter-text').addEventListener('input', function (ev) {
    TEXT_FILTER = ev.target.value.toLowerCase();
    render();
  });
  document.getElementById('filter-result').addEventListener('change', function (ev) {
    RESULT_FILTER = ev.target.value;
    render();
  });
  document.getElementById('refresh-btn').addEventListener('click', loadEntries);
  loadEntries();
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
      try { console.error('[ebible] error banner failed:', e, message); }
      catch (_) {}
    }
  }

  window.addEventListener('error', function (ev) {
    var msg = (ev && ev.message) ? ev.message : 'Script error';
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

  async function safeFetch(url, opts) {
    opts = opts || {};
    let response;
    try {
      response = await fetch(url, opts);
    } catch (netErr) {
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
            errMsg = text.slice(0, 200);
          }
        }
      } catch (_) {}
      showErrorBanner('API ' + response.status + ': ' + errMsg);
      const err = new Error(errMsg);
      err.status = response.status;
      throw err;
    }
    const text = await response.text();
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch (parseErr) {
      showErrorBanner('Server returned invalid JSON from ' + url);
      throw parseErr;
    }
  }

  function safe$(selector, parent) {
    try {
      return (parent || document).querySelector(selector);
    } catch (e) {
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

  window.ebible = window.ebible || {};
  window.ebible.showErrorBanner = showErrorBanner;
  window.ebible.safeFetch = safeFetch;
  window.ebible.safe$ = safe$;
  window.ebible.safe$$ = safe$$;
  window.ebible.escapeHtml = escapeHtml;
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
AUDIT_LOG_HTML = apply_design_system(AUDIT_LOG_HTML, "/audit-log")

"""HTML for /preflight console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import PREFLIGHT_HTML` callers.
"""

PREFLIGHT_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Pre-flight · E-Bible</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  .check-row { transition: background 80ms; }
  .check-row:hover { background: #f8fafc; }
  .icon { font-size: 1.25rem; line-height: 1; width: 1.5rem; flex-shrink: 0; text-align: center; }
  .pass { color: #16a34a; }
  .warn { color: #d97706; }
  .fail { color: #dc2626; }
  .pass-bg { background: #f0fdf4; border-color: #bbf7d0; }
  .warn-bg { background: #fffbeb; border-color: #fde68a; }
  .fail-bg { background: #fef2f2; border-color: #fecaca; }
  details > summary { cursor: pointer; list-style: none; }
  details > summary::-webkit-details-marker { display: none; }
  .details-list { font-family: ui-monospace, monospace; font-size: 0.8125rem; }
</style>
</head>
<body class="bg-slate-50 text-slate-800">

<header class="border-b bg-white">
  <div class="max-w-5xl mx-auto px-4 py-3 flex items-baseline gap-4 text-sm flex-wrap">
    <strong class="text-base">E-Bible</strong>
    <a href="/" class="text-blue-600 hover:underline">matrix</a>
    <a href="/sources" class="text-blue-600 hover:underline">sources</a>
    <a href="/customize" class="text-blue-600 hover:underline">customize</a>
    <a href="/audit" class="text-blue-600 hover:underline">audit</a>
    <a href="/publisher" class="text-blue-600 hover:underline">publisher</a>
    <a href="/wizard" class="text-blue-600 hover:underline">wizard</a>
    <a href="/diff" class="text-blue-600 hover:underline">diff</a>
    <a href="/compare" class="text-blue-600 hover:underline">compare</a>
    <a href="/export" class="text-blue-600 hover:underline">export</a>
    <a href="/covers" class="text-blue-600 hover:underline">covers</a>
    <span class="font-semibold">preflight</span>

    <a href="/ops" class="text-blue-600 hover:underline">ops</a>
    <a href="/apihelp" class="text-blue-600 hover:underline">apihelp</a>
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


<main class="max-w-5xl mx-auto px-4 py-6">
  <h1 class="text-2xl font-semibold mb-2">Pre-flight checklist</h1>
  <p class="text-sm text-slate-600 mb-6">
    Aggregated readiness checks across all editions. Click a check to
    expand details, or use the "fix in …" link to jump to the right
    console. Re-run by refreshing this page.
  </p>

  <div id="banner" class="mb-6 p-4 rounded-lg border-2 hidden">
    <div class="flex items-center gap-3">
      <span id="banner-icon" class="text-3xl"></span>
      <div>
        <h2 id="banner-headline" class="text-lg font-semibold"></h2>
        <p id="banner-detail" class="text-sm text-slate-600 mt-0.5"></p>
      </div>
    </div>
  </div>

  <div id="checks" class="space-y-2">
    <p class="text-slate-500 text-sm">running checks…</p>
  </div>
</main>

<script>
function escapeAttr(s) { return String(s ?? '').replace(/[&<>"']/g, c => ({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
}[c])); }

async function loadPreflight() {
  const root = document.getElementById('checks');
  let data;
  try {
    const r = await fetch('/api/preflight');
    data = await r.json();
  } catch (e) {
    root.innerHTML = `<div class="fail-bg border p-4 rounded">failed to load: ${escapeAttr(e.message)}</div>`;
    return;
  }
  renderBanner(data.summary);
  renderChecks(data.checks);
}

function renderBanner(s) {
  const banner = document.getElementById('banner');
  const icon = document.getElementById('banner-icon');
  const headline = document.getElementById('banner-headline');
  const detail = document.getElementById('banner-detail');
  banner.classList.remove('hidden', 'pass-bg', 'warn-bg', 'fail-bg');
  if (s.ready_to_ship && s.warn === 0) {
    banner.classList.add('pass-bg');
    icon.textContent = '✓';
    icon.className = 'text-3xl pass';
    headline.textContent = 'Ready to ship';
    detail.textContent = `All ${s.total} checks pass.`;
  } else if (s.ready_to_ship) {
    banner.classList.add('warn-bg');
    icon.textContent = '⚠';
    icon.className = 'text-3xl warn';
    headline.textContent = 'Ready to ship — with warnings';
    detail.textContent =
      `${s.pass} pass · ${s.warn} warn · ${s.fail} fail. ` +
      `No blockers, but consider addressing warnings before release.`;
  } else {
    banner.classList.add('fail-bg');
    icon.textContent = '✗';
    icon.className = 'text-3xl fail';
    headline.textContent = 'Not ready to ship';
    detail.textContent =
      `${s.pass} pass · ${s.warn} warn · ${s.fail} fail. ` +
      `Failing checks must be addressed before BUILD.`;
  }
}

function renderChecks(checks) {
  const root = document.getElementById('checks');
  root.innerHTML = '';
  for (const c of checks) {
    const node = document.createElement('details');
    const status = c.status; // pass/warn/fail
    const icon = {pass: '✓', warn: '⚠', fail: '✗'}[status];
    const bg = {pass: '', warn: 'warn-bg', fail: 'fail-bg'}[status];
    node.className = `check-row border rounded ${bg}`;
    const detailsBody = renderDetails(c.details);
    node.innerHTML = `
      <summary class="px-4 py-3 flex items-center gap-3">
        <span class="icon ${status}">${icon}</span>
        <div class="flex-1">
          <div class="font-medium">${escapeAttr(c.name)}</div>
          <div class="text-sm text-slate-600">${escapeAttr(c.message)}</div>
        </div>
        <a href="${escapeAttr(c.jump_to)}"
           class="text-sm text-blue-600 hover:underline shrink-0"
           onclick="event.stopPropagation()">fix in ${escapeAttr(c.jump_to)} →</a>
      </summary>
      ${detailsBody ? `<div class="px-4 pb-3 pt-1 border-t border-slate-200/50">${detailsBody}</div>` : ''}
    `;
    root.appendChild(node);
  }
}

function renderDetails(details) {
  if (!details || !details.length) return '';
  // details is an array of dicts; pretty-print each as a row.
  const rows = details.map(d => {
    if (typeof d === 'string') return `<div>${escapeAttr(d)}</div>`;
    // Show key: value pairs in a compact block.
    return '<div class="details-list">' +
      Object.entries(d).map(([k,v]) => {
        const val = Array.isArray(v) ? v.join(', ') : String(v ?? '');
        return `<span class="text-slate-500">${escapeAttr(k)}:</span> ${escapeAttr(val)}`;
      }).join(' · ') +
    '</div>';
  });
  return rows.join('');
}

loadPreflight();
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

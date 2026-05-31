"""HTML for /distribution console (mint-6).

Re-surfaces the free-distribution UI — the per-edition channel rollup +
archive.org upload + press-kit editing/download — that the deleted /exec console
once hosted (Phase 4 removed /exec; the archive_org / press_kit / distribution
backends were KEPT). Only the FREE surfaces: archive.org + own-site. No
commercial channels.

Cross-link nav + design-system markers are substituted at module load via
``apply_design_system(..., "/distribution")`` per the ψ.13.5 single-source-of-
truth convention (same pattern as ops.py / covers.py). The JS composes the
already-wired endpoints (RULES §9 — compose, don't recompute):
``/api/archive-org/status``, ``/api/distribution/rollup``,
``/api/archive-org/upload/<ed>``, ``/api/press-kit/<ed>`` (GET/PUT), and
``/api/press-kit/<ed>/download``.
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
    apply_design_system,
)

__all__ = ["DISTRIBUTION_HTML", "HEADER_NAV_LINKS", "BUYER_ARC_POLISH_CSS"]

DISTRIBUTION_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>YHWH Ya' Way · Distribution</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
</style>
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Distribution</h1>
    <p class="text-xs text-slate-500">free-distribution channels — archive.org upload + press kits</p>
  </div>
  <div class="flex items-center gap-4 text-xs flex-wrap">
    <!-- HEADER_NAV_LINKS -->
    <span id="corpus-progress" class="ml-auto text-xs text-slate-500" title="corpus depth toward the 35,000-note Ethiopian Tewahedo target">·· loading ··</span>
  </div>
</header>

<main class="max-w-7xl mx-auto px-6 py-6 space-y-6">

  <!-- Archive.org credential status -->
  <section class="bg-white rounded-lg border border-slate-200 p-4">
    <div class="flex items-center justify-between mb-2">
      <h2 class="text-sm font-semibold text-slate-700">Archive.org credentials</h2>
      <span class="text-xs text-slate-400">free public-domain bookshelf — opensource collection (CC0)</span>
    </div>
    <div id="archive-status" class="text-sm text-slate-600">loading…</div>
  </section>

  <!-- Per-edition × per-channel rollup -->
  <section class="bg-white rounded-lg border border-slate-200 overflow-hidden">
    <div class="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold text-slate-700">Distribution channels</h2>
        <p class="text-xs text-slate-500">✓ = shipped · "Upload" pushes the press kit to archive.org</p>
      </div>
      <span id="rollup-coverage" class="text-xs text-slate-400">··</span>
    </div>
    <div id="rollup-table" class="p-4 text-sm text-slate-500">loading…</div>
  </section>

  <!-- Press kits -->
  <section class="bg-white rounded-lg border border-slate-200 overflow-hidden">
    <div class="px-4 py-3 border-b border-slate-200">
      <h2 class="text-sm font-semibold text-slate-700">Press kits</h2>
      <p class="text-xs text-slate-500">150-word blurb · 500-word description · cover variants → downloadable ZIP</p>
    </div>
    <div id="press-kit-list" class="divide-y divide-slate-100 text-sm text-slate-500">loading…</div>
  </section>

</main>

<script>
// /distribution console (mint-6). Read-only rollup + free-distribution actions.
// Composes already-wired endpoints; no new server computation beyond the rollup.
(function () {
  'use strict';

  const api = (window.ebible && window.ebible.safeFetch)
    ? window.ebible.safeFetch
    : async function (url, opts) {
        const r = await fetch(url, opts);
        if (!r.ok) throw new Error(r.status + ' ' + r.statusText);
        const t = await r.text();
        return t ? JSON.parse(t) : null;
      };
  const esc = (window.ebible && window.ebible.escapeHtml)
    ? window.ebible.escapeHtml
    : function (s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
          return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
      };

  let CONFIGURED = false;
  let EDITIONS = [];

  function setHtml(id, html) { const el = document.getElementById(id); if (el) el.innerHTML = html; }

  async function loadStatus() {
    try {
      const s = await api('/api/archive-org/status');
      CONFIGURED = !!s.configured;
      if (s.configured) {
        setHtml('archive-status',
          '<span class="text-emerald-700 font-medium">✓ configured</span> · identifier prefix '
          + '<code class="text-xs bg-slate-100 px-1 rounded">' + esc(s.identifier_prefix || '') + '</code>');
      } else {
        setHtml('archive-status',
          '<span class="text-amber-700 font-medium">not configured</span> — set '
          + '<code class="text-xs bg-slate-100 px-1 rounded">' + esc(s.env_var_access || '') + '</code> and '
          + '<code class="text-xs bg-slate-100 px-1 rounded">' + esc(s.env_var_secret || '') + '</code> to enable uploads.');
      }
    } catch (e) {
      setHtml('archive-status', '<span class="text-red-600">status unavailable</span>');
    }
  }

  function cellMark(shipped) {
    return shipped
      ? '<span class="text-emerald-600" title="shipped">✓</span>'
      : '<span class="text-slate-300" title="not shipped">—</span>';
  }

  async function loadRollup() {
    let data;
    try { data = await api('/api/distribution/rollup'); }
    catch (e) { setHtml('rollup-table', '<p class="text-red-600">rollup unavailable: ' + esc(e.message) + '</p>'); return; }
    if (data && data.status === 'error') {
      setHtml('rollup-table', '<p class="text-red-600">' + esc(data.message || 'error') + '</p>'); return;
    }
    EDITIONS = data.editions || [];
    const channels = data.channels || [];
    const cov = document.getElementById('rollup-coverage');
    if (cov && data.overall) {
      cov.textContent = data.overall.shipped_cells + '/' + data.overall.total_cells
        + ' cells (' + (data.overall.percent || 0).toFixed(0) + '%)';
    }
    let html = '<div class="overflow-x-auto"><table class="w-full text-sm">';
    html += '<thead><tr class="text-left text-xs text-slate-500 border-b border-slate-200">';
    html += '<th class="py-2 pr-4 font-medium">Edition</th>';
    channels.forEach(function (c) { html += '<th class="py-2 px-3 font-medium text-center">' + esc(c.label) + '</th>'; });
    html += '<th class="py-2 pl-3 font-medium text-right">Actions</th></tr></thead><tbody>';
    EDITIONS.forEach(function (ed) {
      html += '<tr class="border-b border-slate-50">';
      html += '<td class="py-2 pr-4 text-slate-700">' + esc(ed.title)
        + ' <span class="text-xs text-slate-400">' + esc(ed.id) + '</span></td>';
      channels.forEach(function (c) {
        const shipped = ed.channels && ed.channels[c.id] && ed.channels[c.id].shipped;
        html += '<td class="py-2 px-3 text-center">' + cellMark(shipped) + '</td>';
      });
      const dis = CONFIGURED ? '' : ' disabled';
      const dtitle = CONFIGURED ? 'upload the press kit to archive.org' : 'configure archive.org credentials first';
      html += '<td class="py-2 pl-3 text-right whitespace-nowrap">'
        + '<button type="button" data-upload="' + esc(ed.id) + '" '
        + 'class="text-xs px-2 py-1 rounded border border-slate-300 hover:border-blue-500 hover:text-blue-700 '
        + 'disabled:opacity-40 disabled:cursor-not-allowed" title="' + esc(dtitle) + '"' + dis + '>Upload</button></td></tr>';
    });
    html += '</tbody></table></div>';
    setHtml('rollup-table', html);
    document.querySelectorAll('[data-upload]').forEach(function (b) {
      b.addEventListener('click', function () { doUpload(b.getAttribute('data-upload'), b); });
    });
    renderPressKitList();
  }

  async function doUpload(edId, btn) {
    if (!window.confirm('Upload the press kit for "' + edId + '" to archive.org (opensource collection)?')) return;
    const old = btn.textContent; btn.disabled = true; btn.textContent = 'Uploading…';
    try {
      const r = await api('/api/archive-org/upload/' + encodeURIComponent(edId),
        { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      btn.textContent = (r && r.url) ? '✓ uploaded' : '✓ done';
      await loadRollup();
    } catch (e) {
      btn.disabled = false; btn.textContent = old;  // safeFetch already surfaced the banner
    }
  }

  function renderPressKitList() {
    if (!EDITIONS.length) { setHtml('press-kit-list', '<p class="p-4">no editions</p>'); return; }
    let html = '';
    EDITIONS.forEach(function (ed) {
      html += '<div class="px-4 py-3">'
        + '<div class="flex items-center justify-between">'
        + '<button type="button" data-kit="' + esc(ed.id) + '" class="text-sm text-blue-600 hover:underline">'
        + esc(ed.title) + '</button>'
        + '<a href="/api/press-kit/' + encodeURIComponent(ed.id) + '/download" '
        + 'class="text-xs px-2 py-1 rounded border border-slate-300 hover:border-blue-500 hover:text-blue-700">Download ZIP</a>'
        + '</div><div id="kit-' + esc(ed.id) + '" class="hidden mt-3"></div></div>';
    });
    setHtml('press-kit-list', html);
    document.querySelectorAll('[data-kit]').forEach(function (b) {
      b.addEventListener('click', function () { toggleKit(b.getAttribute('data-kit')); });
    });
  }

  async function toggleKit(edId) {
    const box = document.getElementById('kit-' + edId);
    if (!box) return;
    if (!box.classList.contains('hidden')) { box.classList.add('hidden'); return; }
    box.classList.remove('hidden');
    box.innerHTML = '<p class="text-xs text-slate-400">loading…</p>';
    let data;
    try { data = await api('/api/press-kit/' + encodeURIComponent(edId)); }
    catch (e) { box.innerHTML = '<p class="text-xs text-red-600">unavailable</p>'; return; }
    const b = data.blurbs || {};
    box.innerHTML =
      '<label class="block text-xs text-slate-500 mb-1">150-word blurb</label>'
      + '<textarea data-f="blurb_150" rows="2" class="w-full text-sm border border-slate-200 rounded p-2 mb-2"></textarea>'
      + '<label class="block text-xs text-slate-500 mb-1">500-word description</label>'
      + '<textarea data-f="blurb_500" rows="4" class="w-full text-sm border border-slate-200 rounded p-2 mb-2"></textarea>'
      + '<div class="flex items-center gap-2"><button type="button" data-save="' + esc(edId) + '" '
      + 'class="text-xs px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700">Save</button>'
      + '<span data-msg class="text-xs text-slate-400"></span></div>';
    box.querySelector('[data-f="blurb_150"]').value = b.blurb_150 || '';
    box.querySelector('[data-f="blurb_500"]').value = b.blurb_500 || '';
    box.querySelector('[data-save]').addEventListener('click', function () { saveKit(edId, box); });
  }

  async function saveKit(edId, box) {
    const msg = box.querySelector('[data-msg]');
    const payload = {
      blurb_150: box.querySelector('[data-f="blurb_150"]').value,
      blurb_500: box.querySelector('[data-f="blurb_500"]').value,
    };
    if (msg) { msg.textContent = 'saving…'; msg.className = 'text-xs text-slate-400'; }
    try {
      await api('/api/press-kit/' + encodeURIComponent(edId),
        { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (msg) { msg.textContent = '✓ saved'; msg.className = 'text-xs text-emerald-600'; }
    } catch (e) {
      if (msg) { msg.textContent = '✗ ' + (e.message || 'failed'); msg.className = 'text-xs text-red-600'; }
    }
  }

  async function init() { await loadStatus(); await loadRollup(); }
  init();
})();
</script>

<script>
// Phase ψ.3 — corpus progress widget (shared across consoles). Cheap fetch +
// DOM update; silently no-ops on failure so a stale tab never breaks.
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

DISTRIBUTION_HTML = apply_design_system(DISTRIBUTION_HTML, "/distribution")

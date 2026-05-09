"""HTML for /publisher console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import PUBLISHER_HTML` callers.

ψ.15 editor-console polish (2026-05-09): cross-link nav substituted
from `_design.HEADER_NAV_LINKS("/publisher")` and `BUYER_ARC_POLISH_CSS`
inlined from `_design`, mirroring the ψ.14 buyer-arc pattern.
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
    apply_design_system,
)

PUBLISHER_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>E-Bible · Publisher Console</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
  .field-input {
    width: 100%; border: 1px solid #cbd5e1; border-radius: 4px;
    padding: 0.4rem 0.6rem; font-size: 0.875rem;
  }
  .field-input:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px #dbeafe; }
  .label-text { font-size: 0.75rem; font-weight: 600; color: #475569;
                text-transform: uppercase; letter-spacing: 0.03em;
                margin-bottom: 0.25rem; display: block; }
  .ed-section { transition: background 0.2s; }
  .ed-section.dirty { background: #fffbeb; }
  .ed-section.saved { background: #ecfdf5; }
  .pill {
    display: inline-flex; align-items: center; gap: 0.4em;
    padding: 0.2em 0.6em; border-radius: 9999px; font-size: 0.75em;
    background: #f1f5f9; border: 1px solid #cbd5e1;
  }
  .pill-x { cursor: pointer; opacity: 0.6; padding-left: 0.3em; }
  .pill-x:hover { opacity: 1; color: #dc2626; }
</style>
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Publisher Console</h1>
    <p class="text-xs text-slate-500">imprint · ISBNs · copyright · authors · BISAC — everything a real publisher needs to ship</p>
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
    <strong>Heads up:</strong> these fields write to <code class="font-mono">content/editions.yaml</code>.
    Defaults shown are placeholders — they will be replaced by your real values
    on the next build (after π.2 wires the build pipeline to read this block).
    Right now (π.1), these are saved but not yet baked into the EPUB output.
  </div>

  <div id="loading" class="text-center text-slate-400 py-20">loading editions…</div>
  <div id="content" class="hidden space-y-6"></div>
</main>

<script>
let DATA = null;

async function init() {
  const r = await fetch('/api/publisher');
  DATA = await r.json();
  document.getElementById('loading').classList.add('hidden');
  document.getElementById('content').classList.remove('hidden');
  render();
}

function render() {
  const wrap = document.getElementById('content');
  wrap.innerHTML = DATA.editions.map(e => editionCard(e)).join('');
  // Wire all inputs
  wrap.querySelectorAll('[data-edition]').forEach(box => {
    const inputs = box.querySelectorAll('input[data-field]');
    const btn = box.querySelector('.save-btn');
    inputs.forEach(inp => {
      inp.dataset.original = inp.value;
      inp.addEventListener('input', () => markDirty(box));
    });
    // List inputs (authors, bisac) wire add/remove
    box.querySelectorAll('.list-add').forEach(btnEl => {
      btnEl.addEventListener('click', () => addListItem(box, btnEl.dataset.field));
    });
    box.querySelectorAll('.list-add-input').forEach(inp => {
      inp.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter') {
          ev.preventDefault();
          addListItem(box, inp.dataset.field);
        }
      });
    });
    btn.addEventListener('click', () => save(box));
    // Phase ν.5 — preview button (sibling of save-btn)
    const pbtn = box.querySelector('.preview-btn');
    if (pbtn) pbtn.addEventListener('click', () => previewEdition(box));
  });
}

function editionCard(e) {
  return `
  <section class="bg-white rounded-lg shadow-sm border border-slate-200 ed-section" data-edition="${e.id}">
    <div class="px-5 py-3 border-b border-slate-200 flex items-center justify-between">
      <div>
        <h2 class="font-semibold">${esc(e.title)}</h2>
        <div class="text-xs text-slate-400 font-mono">${e.id}</div>
      </div>
      <div class="flex items-center gap-2">
        <span class="save-status text-xs"></span>
        <button class="preview-btn text-sm px-3 py-1.5 rounded border border-slate-300 hover:border-blue-500 hover:text-blue-700 text-slate-700 opacity-50 disabled:cursor-not-allowed" title="See exactly what will change before you commit (Phase ν.5)" disabled>Preview changes</button>
        <button class="save-btn text-sm px-4 py-1.5 rounded bg-blue-600 hover:bg-blue-700 text-white opacity-50" disabled>Save</button>
      </div>
    </div>
    <div class="p-5 grid grid-cols-1 md:grid-cols-2 gap-4">

      <fieldset class="md:col-span-2 border-l-4 border-blue-200 pl-3">
        <legend class="text-sm font-semibold text-blue-700 mb-2">Imprint</legend>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label class="label-text">Publisher / Imprint</label>
            <input class="field-input" data-field="publisher_name" value="${escAttr(e.publisher_name)}" maxlength="200">
          </div>
          <div>
            <label class="label-text">Publisher URL</label>
            <input class="field-input" data-field="publisher_url" value="${escAttr(e.publisher_url)}" maxlength="500" placeholder="https://example.com">
          </div>
        </div>
      </fieldset>

      <fieldset class="md:col-span-2 border-l-4 border-emerald-200 pl-3">
        <legend class="text-sm font-semibold text-emerald-700 mb-2">Identifiers</legend>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label class="label-text">ISBN (EPUB)</label>
            <input class="field-input" data-field="isbn_epub" value="${escAttr(e.isbn_epub)}" maxlength="40" placeholder="978-1-XXXXX-XXX-X">
          </div>
          <div>
            <label class="label-text">ISBN (Print)</label>
            <input class="field-input" data-field="isbn_print" value="${escAttr(e.isbn_print)}" maxlength="40" placeholder="978-1-XXXXX-XXX-X">
          </div>
          <div>
            <label class="label-text">Language code</label>
            <input class="field-input" data-field="language_code" value="${escAttr(e.language_code)}" maxlength="12" placeholder="en, am, etc">
          </div>
          <div>
            <label class="label-text">Publication date</label>
            <input class="field-input" data-field="publication_date" value="${escAttr(e.publication_date)}" maxlength="30" placeholder="YYYY-MM-DD">
          </div>
        </div>
      </fieldset>

      <fieldset class="md:col-span-2 border-l-4 border-amber-200 pl-3">
        <legend class="text-sm font-semibold text-amber-700 mb-2">Copyright</legend>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label class="label-text">Year</label>
            <input class="field-input" data-field="copyright_year" value="${escAttr(e.copyright_year)}" maxlength="10">
          </div>
          <div class="md:col-span-2">
            <label class="label-text">Holder</label>
            <input class="field-input" data-field="copyright_holder" value="${escAttr(e.copyright_holder)}" maxlength="200">
          </div>
          <div class="md:col-span-3">
            <label class="label-text">Copyright notice</label>
            <input class="field-input" data-field="copyright_notice" value="${escAttr(e.copyright_notice)}" maxlength="500">
          </div>
        </div>
      </fieldset>

      <fieldset class="md:col-span-2 border-l-4 border-indigo-200 pl-3">
        <legend class="text-sm font-semibold text-indigo-700 mb-2">Authors / Contributors</legend>
        <div class="text-xs text-slate-500 mb-2">Format: <code class="font-mono">Name (role)</code> — e.g. <code class="font-mono">Dr. Jane Smith (editor)</code></div>
        <div class="flex flex-wrap gap-2 mb-2 list-pills" data-field="authors">
          ${(e.authors || []).map((a, i) => listPill('authors', a, i)).join('')}
        </div>
        <div class="flex gap-2">
          <input class="field-input list-add-input flex-1" data-field="authors" placeholder="Add a contributor and press Enter…" maxlength="300">
          <button class="list-add px-3 py-1 text-sm rounded bg-indigo-100 hover:bg-indigo-200 text-indigo-800" data-field="authors">+ Add</button>
        </div>
      </fieldset>

      <fieldset class="md:col-span-2 border-l-4 border-purple-200 pl-3">
        <legend class="text-sm font-semibold text-purple-700 mb-2">BISAC subject codes</legend>
        <div class="text-xs text-slate-500 mb-2">e.g. <code class="font-mono">REL006150</code> (Bibles / Catholic). One per pill.</div>
        <div class="flex flex-wrap gap-2 mb-2 list-pills" data-field="bisac_codes">
          ${(e.bisac_codes || []).map((a, i) => listPill('bisac_codes', a, i)).join('')}
        </div>
        <div class="flex gap-2">
          <input class="field-input list-add-input flex-1" data-field="bisac_codes" placeholder="Add a BISAC code and press Enter…" maxlength="50">
          <button class="list-add px-3 py-1 text-sm rounded bg-purple-100 hover:bg-purple-200 text-purple-800" data-field="bisac_codes">+ Add</button>
        </div>
      </fieldset>

      <fieldset class="md:col-span-2 border-l-4 border-slate-200 pl-3">
        <legend class="text-sm font-semibold text-slate-700 mb-2">Credits</legend>
        <div class="grid grid-cols-1 gap-3">
          <div>
            <label class="label-text">Cover credit</label>
            <input class="field-input" data-field="cover_credit" value="${escAttr(e.cover_credit)}" maxlength="200" placeholder="Designer Name + license">
          </div>
          <div>
            <label class="label-text">Source-text credit</label>
            <input class="field-input" data-field="source_text_credit" value="${escAttr(e.source_text_credit)}" maxlength="500">
          </div>
        </div>
      </fieldset>
    </div>
  </section>`;
}

function listPill(field, value, idx) {
  return `<span class="pill" data-list-item data-field="${field}" data-idx="${idx}">${esc(value)}<span class="pill-x" data-remove>×</span></span>`;
}

function addListItem(box, field) {
  const input = box.querySelector(`input.list-add-input[data-field="${field}"]`);
  const v = (input.value || '').trim();
  if (!v) return;
  const wrap = box.querySelector(`.list-pills[data-field="${field}"]`);
  const pills = Array.from(wrap.querySelectorAll('[data-list-item]')).map(el => el.firstChild.textContent);
  if (pills.includes(v)) {
    input.value = '';
    return;
  }
  pills.push(v);
  wrap.innerHTML = pills.map((p, i) => listPill(field, p, i)).join('');
  // Re-wire remove buttons
  wrap.querySelectorAll('[data-remove]').forEach(x => {
    x.addEventListener('click', (ev) => {
      ev.target.closest('[data-list-item]').remove();
      markDirty(box);
    });
  });
  input.value = '';
  markDirty(box);
}

function markDirty(box) {
  box.classList.add('dirty');
  box.classList.remove('saved');
  const btn = box.querySelector('.save-btn');
  btn.disabled = false;
  btn.classList.remove('opacity-50');
  // Phase ν.5 — preview button enables together with save
  const pbtn = box.querySelector('.preview-btn');
  if (pbtn) {
    pbtn.disabled = false;
    pbtn.classList.remove('opacity-50');
  }
  box.querySelector('.save-status').textContent = '';
}

// Phase ν.5 — extracted payload builder so save() and preview share
// the same change-detection logic; without this, "what save would
// send" and "what preview shows" could drift apart silently.
function buildEditionPayload(box) {
  const id = box.dataset.edition;
  const payload = {};
  // Text fields — only include changed ones
  box.querySelectorAll('input.field-input[data-field]').forEach(inp => {
    if (inp.classList.contains('list-add-input')) return;
    if (inp.value !== inp.dataset.original) {
      payload[inp.dataset.field] = inp.value;
    }
  });
  // List fields — include only when changed vs the on-load snapshot
  const listFields = new Set();
  box.querySelectorAll('.list-pills[data-field]').forEach(wrap => {
    listFields.add(wrap.dataset.field);
  });
  for (const lf of listFields) {
    const wrap = box.querySelector(`.list-pills[data-field="${lf}"]`);
    const items = Array.from(wrap.querySelectorAll('[data-list-item]')).map(el => el.firstChild.textContent);
    const orig = (DATA.editions.find(e => e.id === id) || {})[lf] || [];
    if (JSON.stringify(items) !== JSON.stringify(orig)) {
      payload[lf] = items;
    }
  }
  return payload;
}

// Phase ν.5 — change-impact preview. Show the publisher exactly what
// the next save will alter, before they commit. Fetches the diff from
// /api/edition-meta/<id>/preview (read-only on the server side) and
// renders it in a modal. Cancel = close, Save = call save() directly.
async function previewEdition(box) {
  const id = box.dataset.edition;
  const payload = buildEditionPayload(box);
  if (Object.keys(payload).length === 0) {
    box.querySelector('.save-status').innerHTML =
      '<span class="text-slate-500">no changes to preview</span>';
    return;
  }
  const status = box.querySelector('.save-status');
  status.innerHTML = '<span class="text-slate-500">computing preview…</span>';
  try {
    const r = await fetch(`/api/edition-meta/${encodeURIComponent(id)}/preview`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    const data = await r.json();
    if (!r.ok || data.error) {
      status.innerHTML = `<span class="text-red-600">✗ ${esc(data.error || 'preview failed')}</span>`;
      return;
    }
    status.textContent = '';
    showPreviewModal(box, data);
  } catch (e) {
    status.innerHTML = `<span class="text-red-600">✗ ${esc(e.message)}</span>`;
  }
}

function showPreviewModal(box, data) {
  // Remove any existing modal so multiple clicks don't stack
  document.querySelectorAll('.preview-modal-backdrop').forEach(el => el.remove());

  const fmtValue = (v) => {
    if (v === null || v === undefined || v === '') return '<span class="text-slate-400 italic">empty</span>';
    if (typeof v === 'boolean') return v ? '<span class="text-emerald-700 font-medium">yes</span>' : '<span class="text-slate-500">no</span>';
    if (Array.isArray(v)) return v.length === 0 ? '<span class="text-slate-400 italic">empty list</span>' : `<code>${esc(JSON.stringify(v))}</code>`;
    if (typeof v === 'object') return `<code class="text-xs">${esc(JSON.stringify(v))}</code>`;
    return `<code>${esc(String(v))}</code>`;
  };

  const changesHtml = data.changes.length === 0
    ? '<p class="text-slate-500 italic">No changes to commit. Save will be a no-op.</p>'
    : `<table class="w-full text-sm">
        <thead><tr class="border-b text-xs uppercase text-slate-500">
          <th class="text-left py-1 pr-2">Field</th>
          <th class="text-left py-1 pr-2">Current</th>
          <th class="text-left py-1">Proposed</th>
        </tr></thead>
        <tbody>
        ${data.changes.map(c => `
          <tr class="border-b border-slate-100">
            <td class="py-1.5 pr-2 font-mono text-xs">${esc(c.field)}</td>
            <td class="py-1.5 pr-2">${fmtValue(c.before)}</td>
            <td class="py-1.5 text-emerald-700">${fmtValue(c.after)}</td>
          </tr>`).join('')}
        </tbody>
      </table>`;

  const unknownHtml = (data.unknown_fields && data.unknown_fields.length > 0)
    ? `<div class="mt-3 p-2 bg-amber-50 border border-amber-200 rounded text-xs">
        <strong>Unknown fields (will be silently ignored on save):</strong>
        <code class="ml-1">${data.unknown_fields.map(esc).join(', ')}</code>
      </div>`
    : '';

  const backdrop = document.createElement('div');
  backdrop.className = 'preview-modal-backdrop fixed inset-0 bg-black/40 flex items-center justify-center z-50';
  backdrop.innerHTML = `
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[85vh] overflow-hidden flex flex-col">
      <div class="px-5 py-3 border-b border-slate-200 flex items-center justify-between">
        <h3 class="font-semibold">Preview save — ${esc(data.edition_id)}</h3>
        <button class="preview-modal-close text-slate-400 hover:text-slate-600 text-xl leading-none">×</button>
      </div>
      <div class="px-5 py-4 overflow-y-auto">
        <p class="text-xs text-slate-500 mb-3">
          ${data.changes.length} change${data.changes.length === 1 ? '' : 's'} to commit
          · ${data.unchanged.length} unchanged field${data.unchanged.length === 1 ? '' : 's'}
        </p>
        ${changesHtml}
        ${unknownHtml}
      </div>
      <div class="px-5 py-3 border-t border-slate-200 flex justify-end gap-2 bg-slate-50">
        <button class="preview-modal-close text-sm px-4 py-1.5 rounded border border-slate-300 hover:border-slate-500">Cancel</button>
        <button class="preview-modal-save text-sm px-4 py-1.5 rounded bg-blue-600 hover:bg-blue-700 text-white ${data.no_changes ? 'opacity-50 cursor-not-allowed' : ''}" ${data.no_changes ? 'disabled' : ''}>Save these changes</button>
      </div>
    </div>
  `;
  document.body.appendChild(backdrop);
  // Close handlers
  backdrop.querySelectorAll('.preview-modal-close').forEach(btn => {
    btn.addEventListener('click', () => backdrop.remove());
  });
  backdrop.addEventListener('click', (ev) => {
    if (ev.target === backdrop) backdrop.remove();
  });
  // Confirm handler — proceed with the actual save
  const saveBtn = backdrop.querySelector('.preview-modal-save');
  if (saveBtn && !data.no_changes) {
    saveBtn.addEventListener('click', () => {
      backdrop.remove();
      save(box);
    });
  }
}

async function save(box) {
  const id = box.dataset.edition;
  const payload = buildEditionPayload(box);

  if (Object.keys(payload).length === 0) {
    box.querySelector('.save-status').innerHTML = '<span class="text-slate-500">no changes</span>';
    return;
  }

  const status = box.querySelector('.save-status');
  status.innerHTML = '<span class="text-slate-500">saving…</span>';
  try {
    const r = await fetch(`/api/publisher/${encodeURIComponent(id)}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    const result = await r.json();
    if (!r.ok || result.error) {
      status.innerHTML = `<span class="text-red-600">✗ ${esc(result.error || 'failed')}</span>`;
      return;
    }
    status.innerHTML = '<span class="text-emerald-700">✓ saved</span>';
    box.classList.remove('dirty');
    box.classList.add('saved');
    setTimeout(() => box.classList.remove('saved'), 1500);
    const btn = box.querySelector('.save-btn');
    btn.disabled = true;
    btn.classList.add('opacity-50');
    // Phase ν.5 — disable preview alongside save when committed
    const pbtn = box.querySelector('.preview-btn');
    if (pbtn) {
      pbtn.disabled = true;
      pbtn.classList.add('opacity-50');
    }
    // Refresh data
    const r2 = await fetch('/api/publisher');
    DATA = await r2.json();
    // Update originals + the in-DOM list pill snapshot
    box.querySelectorAll('input.field-input[data-field]').forEach(inp => {
      inp.dataset.original = inp.value;
    });
  } catch (e) {
    status.innerHTML = `<span class="text-red-600">✗ ${esc(e.message)}</span>`;
  }
}

function esc(s) {
  return (s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function escAttr(s) { return esc(s); }

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
PUBLISHER_HTML = apply_design_system(PUBLISHER_HTML, "/publisher")

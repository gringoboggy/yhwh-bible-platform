"""HTML for /matrix console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import MATRIX_HTML` callers.
"""

MATRIX_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>E-Bible · Symbol Toggle Matrix</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
  .symbol { font-size: 1.4em; line-height: 1; display: inline-block; width: 1.5em; text-align: center; }
  .cat-row { cursor: pointer; user-select: none; }
  .cat-row:hover { background: #f3f4f6; }
  .kind-row { padding-left: 2em; font-size: 0.9em; }
  .count-cell { font-variant-numeric: tabular-nums; text-align: right; padding: 0.25rem 0.5rem; min-width: 4.5rem; }
  .count-zero { color: #cbd5e0; }
  .count-disabled { color: #fbbf24; font-style: italic; }
  .count-ok { color: #1f2937; }
  .pill { display: inline-block; padding: 0.1em 0.6em; border-radius: 9999px; font-size: 0.75em; }
  /* ψ.12 — sticky column headers + first-column row labels.
     Without this, scrolling right (with many editions) loses the
     column headers and scrolling down loses the row labels. */
  .matrix-table thead th {
    position: sticky;
    top: 0;
    background: #f8fafc;
    z-index: 2;
  }
  .matrix-table tbody td:first-child,
  .matrix-table thead th:first-child {
    position: sticky;
    left: 0;
    background: white;
    z-index: 1;
  }
  .matrix-table thead th:first-child { background: #f8fafc; z-index: 3; }
  .matrix-table tbody tr.cat-row td:first-child { background: #fafafa; }
  .matrix-table-wrap { max-height: 75vh; overflow: auto; }
  details > summary { list-style: none; }
  details > summary::-webkit-details-marker { display: none; }
  details > summary::before { content: "▸"; display: inline-block; width: 1em; transition: transform 0.15s; color: #94a3b8; }
  details[open] > summary::before { transform: rotate(90deg); }
</style>
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Symbol Toggle Matrix</h1>
    <p class="text-xs text-slate-500">read-only · Phase μ.1</p>
  </div>
  <div class="flex items-center gap-4 text-xs">
    <a href="/" class="text-blue-600 hover:underline">note editor</a>
    <a href="/matrix" class="font-semibold">symbol matrix</a>
    <a href="/sources" class="text-blue-600 hover:underline">sources</a>
    <a href="/export" class="text-blue-600 hover:underline">export</a>
    <a href="/customize" class="text-blue-600 hover:underline">customize</a>
    <a href="/audit" class="text-blue-600 hover:underline">audit</a>
    <a href="/publisher" class="text-blue-600 hover:underline">publisher</a>
    <a href="/wizard" class="text-blue-600 hover:underline">wizard</a>
    <a href="/diff" class="text-blue-600 hover:underline">diff</a>
    <a href="/compare" class="text-blue-600 hover:underline">compare</a>
    <a href="/covers" class="text-blue-600 hover:underline">covers</a>
    <a href="/preflight" class="text-blue-600 hover:underline">preflight</a>

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


<main class="p-6 max-w-7xl mx-auto">
  <div id="loading" class="text-center text-slate-400 py-20">loading matrix …</div>
  <div id="content" class="hidden grid grid-cols-1 lg:grid-cols-[1fr_20rem] gap-6">

    <!-- LEFT: matrix -->
    <section class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      <div class="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
        <h2 class="font-semibold">Categories &times; Editions</h2>
        <div class="text-xs text-slate-500" id="legend">
          <span class="count-ok">●</span> enabled count &nbsp;
          <span class="count-disabled">●</span> potential (filtered out) &nbsp;
          <span class="count-zero">●</span> no notes
        </div>
      </div>
      <!-- ψ.12 — inline switch-confirm banner replaces a blocking
           confirm() that was easy to dismiss accidentally. -->
      <div id="switch-confirm" class="hidden mx-4 my-2 px-3 py-2 rounded border border-amber-300 bg-amber-50 text-sm text-amber-900 flex items-center justify-between gap-3">
        <span>You have unsaved changes. Switching editions will discard them.</span>
        <span class="flex items-center gap-2">
          <button type="button" id="switch-discard" class="text-xs px-3 py-1 rounded bg-amber-600 text-white hover:bg-amber-700">Discard &amp; switch</button>
          <button type="button" id="switch-cancel" class="text-xs px-3 py-1 rounded border border-slate-300 hover:bg-slate-50">Cancel</button>
        </span>
      </div>
      <div class="matrix-table-wrap">
      <table class="w-full text-sm matrix-table">
        <thead class="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr id="header-row">
            <th class="text-left px-3 py-2 w-72">
              <span class="inline-block w-5"></span>Category / Kind
            </th>
            <!-- edition columns injected by JS -->
          </tr>
        </thead>
        <tbody id="body"></tbody>
      </table>
      </div>
    </section>

    <!-- RIGHT: active edition panel -->
    <aside class="space-y-4">
      <section class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <label class="block text-xs uppercase tracking-wide text-slate-500 mb-1">Edit Edition</label>
        <select id="edition-select" class="w-full border border-slate-300 rounded px-2 py-1.5 text-sm"></select>
        <div id="edition-info" class="mt-3 text-sm space-y-1.5"></div>
        <div id="save-controls" class="mt-4 hidden">
          <div id="dirty-banner" class="hidden text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1.5 mb-2">
            <span id="dirty-count"></span> unsaved change(s)
          </div>
          <div class="flex gap-2">
            <button id="save-btn" class="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-3 py-1.5 rounded disabled:opacity-50 disabled:cursor-not-allowed" disabled>Save</button>
            <button id="reset-btn" class="px-3 py-1.5 text-sm border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50" disabled>Reset</button>
          </div>
          <button id="save-as-btn" class="w-full mt-2 px-3 py-1.5 text-sm border border-slate-300 rounded hover:bg-slate-50 text-slate-700">
            Save As Scenario…
          </button>
          <div id="save-status" class="text-xs text-slate-500 mt-2"></div>
        </div>
      </section>

      <section class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-xs uppercase tracking-wide text-slate-500">Saved scenarios</h3>
          <button id="refresh-scenarios" class="text-xs text-blue-600 hover:underline">refresh</button>
        </div>
        <div id="scenarios-list" class="space-y-1.5 text-sm">
          <div class="text-xs text-slate-400">no scenarios yet — use Save As to create one</div>
        </div>
      </section>

      <section class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <h3 class="text-xs uppercase tracking-wide text-slate-500 mb-2">Categories breakdown</h3>
        <div id="breakdown"></div>
      </section>
    </aside>

  </div>
</main>

<script>
let DATA = null;
let ACTIVE_EDITION = null;
let LOCAL_ENABLED = new Set();   // unsaved client state for ACTIVE_EDITION
let SERVER_ENABLED = new Set();  // last-known server state for diff

async function loadMatrix() {
  const res = await fetch('/api/matrix');
  DATA = await res.json();
  ACTIVE_EDITION = DATA.editions[0]?.id;
  document.getElementById('loading').classList.add('hidden');
  document.getElementById('content').classList.remove('hidden');
  buildHeader();
  buildBody();
  buildEditionSelector();
  refreshActiveEdition();
}

function buildHeader() {
  const tr = document.getElementById('header-row');
  for (const ed of DATA.editions) {
    const th = document.createElement('th');
    th.className = 'count-cell text-right text-xs uppercase tracking-wide text-slate-500 py-2';
    th.title = ed.title;
    th.textContent = ed.short_title || ed.id.split('-')[0];
    tr.appendChild(th);
  }
}

function kindIsEnabledLocally(code) { return LOCAL_ENABLED.has(code); }

// ψ.12 — preserve scroll position across the rare buildBody() rebuilds
// (reset, edition switch, initial render). Toggle paths now patch
// the DOM in place via incremental handlers below — they don't call
// buildBody at all.
function buildBody() {
  const wrap = document.querySelector('.matrix-table-wrap');
  const scrollTop = wrap ? wrap.scrollTop : 0;
  const scrollLeft = wrap ? wrap.scrollLeft : 0;
  const tbody = document.getElementById('body');
  tbody.innerHTML = '';
  const cats = [...DATA.categories].sort((a, b) => a.sort_order - b.sort_order);
  for (const cat of cats) {
    const kindsInCat = DATA.kinds.filter(k => k.category === cat.id);
    const catRow = document.createElement('tr');
    catRow.className = 'cat-row border-t border-slate-100';
    const allEnabled = kindsInCat.every(k => kindIsEnabledLocally(k.code));
    const someEnabled = kindsInCat.some(k => kindIsEnabledLocally(k.code));
    catRow.innerHTML = `
      <td class="px-3 py-2 font-medium">
        <details>
          <summary>
            <input type="checkbox" class="cat-toggle mr-1.5" data-cat="${cat.id}"
              ${allEnabled ? 'checked' : ''} ${someEnabled && !allEnabled ? 'data-indeterminate="1"' : ''}>
            <span class="symbol" style="color:#475569">${cat.symbol}</span>
            <span>${cat.label}</span>
            <span class="text-xs text-slate-400 ml-1">(${kindsInCat.length})</span>
          </summary>
        </details>
      </td>
    `;
    // Set indeterminate visually on category checkboxes that are partial
    const catCheckbox = catRow.querySelector('.cat-toggle');
    if (someEnabled && !allEnabled) catCheckbox.indeterminate = true;
    catCheckbox.addEventListener('change', () => onToggleCategory(cat.id, catCheckbox.checked));
    catCheckbox.addEventListener('click', e => e.stopPropagation());

    // Per-edition counts (sum across kinds in this category)
    for (const ed of DATA.editions) {
      const td = document.createElement('td');
      td.className = 'count-cell';
      const m = DATA.matrix[ed.id];
      let enabled = 0, potential = 0;
      for (const k of kindsInCat) {
        enabled += m.enabled[k.code] || 0;
        potential += m.potential[k.code] || 0;
      }
      td.append(formatCount(enabled, potential));
      catRow.appendChild(td);
    }
    tbody.appendChild(catRow);

    // Kind sub-rows
    for (const k of kindsInCat) {
      const kRow = document.createElement('tr');
      kRow.className = 'kind-row text-slate-600 border-t border-slate-50';
      const isOn = kindIsEnabledLocally(k.code);
      kRow.innerHTML = `
        <td class="px-3 py-1 font-mono text-xs">
          <input type="checkbox" class="kind-toggle mr-1.5 ml-6" data-kind="${k.code}" ${isOn ? 'checked' : ''}>
          ${k.code}
        </td>
      `;
      const kc = kRow.querySelector('.kind-toggle');
      kc.addEventListener('change', () => onToggleKind(k.code, kc.checked));
      for (const ed of DATA.editions) {
        const td = document.createElement('td');
        td.className = 'count-cell text-xs';
        const m = DATA.matrix[ed.id];
        td.append(formatCount(m.enabled[k.code] || 0, m.potential[k.code] || 0));
        kRow.appendChild(td);
      }
      tbody.appendChild(kRow);
    }
  }
  // ψ.12 — restore scroll position after the rebuild.
  if (wrap) {
    wrap.scrollTop = scrollTop;
    wrap.scrollLeft = scrollLeft;
  }
}

// ψ.12 — incremental update for one category's parent-checkbox state.
// Called from the toggle handlers instead of a full buildBody() rebuild.
// Recomputes allEnabled / someEnabled for `catId`'s kinds (using the
// current LOCAL_ENABLED set) and patches the parent checkbox + its
// indeterminate marker IN PLACE. No DOM teardown; no scroll-jump; no
// re-attachment of every kind row's event listener.
function updateCategoryCheckbox(catId) {
  const catCheckbox = document.querySelector(
    `.cat-toggle[data-cat="${catId}"]`
  );
  if (!catCheckbox) return;
  const kindsInCat = DATA.kinds.filter(k => k.category === catId);
  const allEnabled = kindsInCat.every(k => kindIsEnabledLocally(k.code));
  const someEnabled = kindsInCat.some(k => kindIsEnabledLocally(k.code));
  catCheckbox.checked = allEnabled;
  catCheckbox.indeterminate = someEnabled && !allEnabled;
}

function formatCount(enabled, potential) {
  const wrap = document.createElement('span');
  if (enabled === 0 && potential === 0) {
    wrap.className = 'count-zero';
    wrap.textContent = '·';
  } else if (enabled === 0 && potential > 0) {
    wrap.className = 'count-disabled';
    wrap.textContent = `(${potential.toLocaleString()})`;
    wrap.title = `${potential} potential note(s) — kind disabled in this edition.`;
  } else {
    wrap.className = 'count-ok font-medium';
    wrap.textContent = enabled.toLocaleString();
    if (potential > enabled) {
      wrap.title = `${enabled} shipping; ${potential - enabled} more would ship if all kinds in this category were enabled.`;
    }
  }
  return wrap;
}

function onToggleKind(code, on) {
  if (on) LOCAL_ENABLED.add(code);
  else LOCAL_ENABLED.delete(code);
  // ψ.12 — incremental: just patch the parent category checkbox's
  // indeterminate state. The toggled kind's checkbox is already in
  // its target visual state (the user clicked it).
  const kind = DATA.kinds.find(k => k.code === code);
  if (kind) updateCategoryCheckbox(kind.category);
  refreshDirtyBanner();
}

function onToggleCategory(catId, on) {
  // ψ.12 — incremental: walk every kind-row checkbox in this
  // category and set its checked state directly. No tbody teardown,
  // no listener re-attachment, no scroll jump.
  const kinds = DATA.kinds.filter(k => k.category === catId);
  for (const k of kinds) {
    if (on) LOCAL_ENABLED.add(k.code);
    else LOCAL_ENABLED.delete(k.code);
    const kc = document.querySelector(
      `.kind-toggle[data-kind="${k.code}"]`
    );
    if (kc) kc.checked = on;
  }
  // The category's own indeterminate is now resolved one way or
  // the other; the checkbox's `change` event already set its
  // own .checked, so nothing more to do for the parent.
  const catCheckbox = document.querySelector(
    `.cat-toggle[data-cat="${catId}"]`
  );
  if (catCheckbox) catCheckbox.indeterminate = false;
  refreshDirtyBanner();
}

function refreshDirtyBanner() {
  const dirty = symmetricDiff(LOCAL_ENABLED, SERVER_ENABLED);
  const banner = document.getElementById('dirty-banner');
  const saveBtn = document.getElementById('save-btn');
  const resetBtn = document.getElementById('reset-btn');
  if (dirty.size > 0) {
    banner.classList.remove('hidden');
    document.getElementById('dirty-count').textContent = dirty.size;
    saveBtn.disabled = false;
    resetBtn.disabled = false;
  } else {
    banner.classList.add('hidden');
    saveBtn.disabled = true;
    resetBtn.disabled = true;
  }
}

function symmetricDiff(a, b) {
  const out = new Set();
  for (const x of a) if (!b.has(x)) out.add(x);
  for (const x of b) if (!a.has(x)) out.add(x);
  return out;
}

function buildEditionSelector() {
  const sel = document.getElementById('edition-select');
  for (const ed of DATA.editions) {
    const o = document.createElement('option');
    o.value = ed.id;
    o.textContent = ed.title;
    sel.appendChild(o);
  }
  sel.value = ACTIVE_EDITION;
  sel.addEventListener('change', () => {
    // ψ.12 — replace the blocking confirm() with an inline banner.
    // Dirty? Show the banner and revert the picker until the user
    // explicitly clicks Discard or Cancel.
    if (symmetricDiff(LOCAL_ENABLED, SERVER_ENABLED).size > 0) {
      const banner = document.getElementById('switch-confirm');
      banner.dataset.target = sel.value;
      banner.classList.remove('hidden');
      sel.value = ACTIVE_EDITION;  // visual revert until decided
      return;
    }
    ACTIVE_EDITION = sel.value;
    refreshActiveEdition();
  });
  document.getElementById('switch-discard').addEventListener('click', () => {
    const banner = document.getElementById('switch-confirm');
    const target = banner.dataset.target;
    if (!target) return;
    ACTIVE_EDITION = target;
    sel.value = target;
    banner.classList.add('hidden');
    refreshActiveEdition();
  });
  document.getElementById('switch-cancel').addEventListener('click', () => {
    document.getElementById('switch-confirm').classList.add('hidden');
  });
  document.getElementById('save-btn').addEventListener('click', saveActiveEdition);
  document.getElementById('reset-btn').addEventListener('click', () => {
    LOCAL_ENABLED = new Set(SERVER_ENABLED);
    buildBody();
    refreshDirtyBanner();
    document.getElementById('save-status').textContent = 'reverted to last-saved state';
  });
  document.getElementById('save-as-btn').addEventListener('click', saveAsScenario);
  document.getElementById('refresh-scenarios').addEventListener('click', refreshScenarioList);
}

async function saveAsScenario() {
  const status = document.getElementById('save-status');
  const name = prompt('Scenario name (lowercase letters, digits, - or _):');
  if (!name) return;
  const label = prompt('Human-readable label (optional):', name) || name;
  const notesText = prompt('Notes / description (optional):', '') || '';
  status.textContent = 'saving scenario …';
  try {
    const r = await fetch(`/api/scenarios/${encodeURIComponent(name)}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        based_on: ACTIVE_EDITION,
        label: label,
        notes: notesText,
        enabled_kinds: [...LOCAL_ENABLED],
      }),
    });
    const result = await r.json();
    if (!r.ok || result.error) {
      status.innerHTML = `<span class="text-red-600">✗ ${result.error || 'save failed'}</span>`;
      return;
    }
    status.innerHTML = `<span class="text-emerald-700">✓ scenario "${name}" saved</span>`;
    refreshScenarioList();
  } catch (e) {
    status.innerHTML = `<span class="text-red-600">✗ ${e.message}</span>`;
  }
}

async function refreshScenarioList() {
  const list = document.getElementById('scenarios-list');
  try {
    const r = await fetch('/api/scenarios');
    const data = await r.json();
    if (!data.scenarios?.length) {
      list.innerHTML = '<div class="text-xs text-slate-400">no scenarios yet — use Save As to create one</div>';
      return;
    }
    list.innerHTML = data.scenarios.map(s => `
      <div class="flex items-center justify-between gap-2 border border-slate-200 rounded px-2 py-1.5">
        <div class="min-w-0 flex-1">
          <div class="font-medium truncate" title="${(s.notes || '').replace(/"/g, '&quot;')}">${s.label || s.name}</div>
          <div class="text-xs text-slate-500 font-mono truncate">${s.name} · from ${s.based_on || '—'} · ${(s.enabled_kinds || []).length} kinds</div>
        </div>
        <button data-scenario-load="${s.name}" class="text-xs text-blue-600 hover:underline">load</button>
        <button data-scenario-del="${s.name}" class="text-xs text-red-600 hover:underline">×</button>
      </div>
    `).join('');
    // Wire load + delete buttons
    list.querySelectorAll('[data-scenario-load]').forEach(b => {
      b.addEventListener('click', () => loadScenario(b.dataset.scenarioLoad));
    });
    list.querySelectorAll('[data-scenario-del]').forEach(b => {
      b.addEventListener('click', () => deleteScenario(b.dataset.scenarioDel));
    });
  } catch (e) {
    list.innerHTML = `<div class="text-xs text-red-600">failed: ${e.message}</div>`;
  }
}

async function loadScenario(name) {
  try {
    const r = await fetch(`/api/scenarios/${encodeURIComponent(name)}`);
    const data = await r.json();
    if (data.error) {
      document.getElementById('save-status').innerHTML = `<span class="text-red-600">✗ ${data.error}</span>`;
      return;
    }
    LOCAL_ENABLED = new Set(data.scenario.enabled_kinds || []);
    buildBody();
    refreshDirtyBanner();
    document.getElementById('save-status').innerHTML =
      `<span class="text-blue-700">✓ loaded scenario "${name}" (preview only — Save to commit to active edition, or Save As to keep separate)</span>`;
  } catch (e) {
    document.getElementById('save-status').innerHTML = `<span class="text-red-600">✗ ${e.message}</span>`;
  }
}

async function deleteScenario(name) {
  if (!confirm(`Delete scenario "${name}"?`)) return;
  try {
    const r = await fetch(`/api/scenarios/${encodeURIComponent(name)}`, {method: 'DELETE'});
    const data = await r.json();
    if (data.error) {
      document.getElementById('save-status').innerHTML = `<span class="text-red-600">✗ ${data.error}</span>`;
      return;
    }
    refreshScenarioList();
  } catch (e) {
    document.getElementById('save-status').innerHTML = `<span class="text-red-600">✗ ${e.message}</span>`;
  }
}

function refreshActiveEdition() {
  const ed = DATA.editions.find(e => e.id === ACTIVE_EDITION);
  const m = DATA.matrix[ACTIVE_EDITION];
  if (!ed || !m) return;

  SERVER_ENABLED = new Set(m.enabled_kinds_set);
  LOCAL_ENABLED = new Set(SERVER_ENABLED);

  document.getElementById('save-controls').classList.remove('hidden');
  document.getElementById('save-status').textContent = '';

  const info = document.getElementById('edition-info');
  const blocked = m.total_potential - m.total_enabled;
  info.innerHTML = `
    <div class="flex justify-between"><span class="text-slate-500">canon</span>
      <span class="font-medium">${ed.canon || '—'}</span></div>
    <div class="flex justify-between"><span class="text-slate-500">books</span>
      <span class="font-mono">${m.canon_books_count}</span></div>
    <div class="flex justify-between"><span class="text-slate-500">enabled kinds</span>
      <span class="font-mono">${m.enabled_kinds_count} / ${DATA.kinds.length}</span></div>
    <div class="flex justify-between mt-3 text-base">
      <span class="font-semibold">notes shipping</span>
      <span class="font-bold text-emerald-700">${m.total_enabled.toLocaleString()}</span>
    </div>
    <div class="flex justify-between text-xs text-slate-500">
      <span>potential (all kinds on)</span>
      <span>${m.total_potential.toLocaleString()}</span>
    </div>
    ${blocked > 0 ? `<div class="text-xs text-amber-600">+${blocked} blocked by kind filter</div>` : ''}
  `;

  buildBody();
  refreshDirtyBanner();

  const breakdown = {};
  for (const [kindCode, count] of Object.entries(m.enabled)) {
    const k = DATA.kinds.find(kk => kk.code === kindCode);
    if (!k) continue;
    breakdown[k.category] = (breakdown[k.category] || 0) + count;
  }
  const cats = [...DATA.categories].sort((a, b) => (breakdown[b.id] || 0) - (breakdown[a.id] || 0));
  const total = m.total_enabled || 1;
  const breakdownEl = document.getElementById('breakdown');
  breakdownEl.innerHTML = cats.map(c => {
    const n = breakdown[c.id] || 0;
    const pct = (n / total * 100).toFixed(1);
    if (n === 0) return '';
    return `
      <div class="mb-1.5">
        <div class="flex justify-between text-xs">
          <span><span class="symbol text-slate-500">${c.symbol}</span> ${c.label}</span>
          <span class="font-mono text-slate-500">${n.toLocaleString()} <span class="text-slate-400">(${pct}%)</span></span>
        </div>
        <div class="h-1.5 bg-slate-100 rounded overflow-hidden">
          <div class="h-full bg-blue-400" style="width:${pct}%"></div>
        </div>
      </div>`;
  }).filter(Boolean).join('');
}

async function saveActiveEdition() {
  const status = document.getElementById('save-status');
  const saveBtn = document.getElementById('save-btn');
  saveBtn.disabled = true;
  status.textContent = 'saving …';
  try {
    const r = await fetch(`/api/edition/${ACTIVE_EDITION}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({enabled_kinds: [...LOCAL_ENABLED]}),
    });
    const result = await r.json();
    if (!r.ok || result.error) {
      status.innerHTML = `<span class="text-red-600">✗ ${result.error || 'save failed'}</span>`;
      saveBtn.disabled = false;
      return;
    }
    status.innerHTML = `<span class="text-emerald-700">✓ saved · ${result.enabled_total} kinds enabled</span>`;
    // Re-fetch the matrix so counts reflect the saved state
    const fresh = await fetch('/api/matrix').then(r => r.json());
    DATA = fresh;
    refreshActiveEdition();
  } catch (e) {
    status.innerHTML = `<span class="text-red-600">✗ ${e.message}</span>`;
    saveBtn.disabled = false;
  }
}

loadMatrix().then(() => refreshScenarioList()).catch(e => {
  document.getElementById('loading').textContent = 'Failed to load matrix: ' + e.message;
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

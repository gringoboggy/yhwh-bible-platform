// Matrix console — frontend application code.
//
// Phase ψ.34 (2026-05-10) — extracted from the inline `<script>`
// block in `scripts/templates/matrix.py`. Served by the
// `/static/matrix.js` route. Browser cache: 5 minutes.
//
// History — accreted across phases ψ.18, ψ.18.1, ψ.18.2, ψ.20,
// ψ.26, ψ.27, ψ.28, ψ.29 before being lifted out of the template
// string. No behavior change in ψ.34; just the file boundary.

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
  setupKindFilter();  // ψ.28 — bind once after first DOM populate
  setupKeyboardShortcuts();  // ψ.29 — undo/redo + help modal + Cmd+S
  setupPsi27Modals();  // ψ.27 — scenario export / import modals
  setupPsi26BulkOps();  // ψ.26 — shift+click + drag + apply-to-all
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
    catRow.dataset.catId = cat.id;  // ψ.28 — for kind-filter row hide
    const allEnabled = kindsInCat.every(k => kindIsEnabledLocally(k.code));
    const someEnabled = kindsInCat.some(k => kindIsEnabledLocally(k.code));
    catRow.innerHTML = `
      <td class="px-3 py-2 font-medium">
        <details>
          <summary>
            <input type="checkbox" class="cat-toggle mr-1.5" data-cat="${cat.id}"
              ${allEnabled ? 'checked' : ''} ${someEnabled && !allEnabled ? 'data-indeterminate="1"' : ''}>
            <span class="symbol" style="color:#475569">${escapeText(cat.symbol)}</span>
            <span>${escapeText(cat.label)}</span>
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
      kRow.dataset.kindCode = k.code;  // ψ.28 — for kind-filter
      kRow.dataset.catId = cat.id;     // ψ.28 — co-hide with category
      const isOn = kindIsEnabledLocally(k.code);
      kRow.innerHTML = `
        <td class="px-3 py-1 font-mono text-xs">
          <input type="checkbox" class="kind-toggle mr-1.5 ml-6" data-kind="${k.code}" ${isOn ? 'checked' : ''}>
          ${k.code}
          <button type="button" class="psi26-applyall-btn"
            data-applyall-kind="${k.code}"
            title="Apply this kind across every edition">↗ all</button>
        </td>
      `;
      const kc = kRow.querySelector('.kind-toggle');
      // ψ.26 — click handler runs BEFORE the change handler. We use it
      // to detect shift+click + suppress drag-mode-change events.
      // The change handler still fires onToggleKind for the normal
      // single-click path.
      kc.addEventListener('click', (ev) => {
        if (handlePsi26ToggleClick(ev, k.code, kc)) {
          ev.preventDefault();
        }
      });
      kc.addEventListener('mousedown', (ev) => {
        psi26StartDrag(ev, k.code, kc);
      });
      kc.addEventListener('change', () => {
        // Drag mode suppresses the per-row undo op; bulk path flushes.
        if (PSI26_DRAG.active) return;
        onToggleKind(k.code, kc.checked);
      });
      // Apply-to-all button
      const applyBtn = kRow.querySelector('.psi26-applyall-btn');
      if (applyBtn) {
        applyBtn.addEventListener('click', (ev) => {
          ev.stopPropagation();
          showApplyToAll(k.code);
        });
      }
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
  // ψ.28 — re-apply the active kind filter; rebuilds wipe per-row
  // display state, so the previously-typed query needs replaying.
  const filterInput = document.getElementById('psi28-kind-filter');
  if (filterInput && filterInput.value) {
    applyKindFilter(filterInput.value);
  }
}

// ψ.28 — kind search-and-filter. Hides non-matching kind rows in
// real time. Match haystack per kind: kind code, kind label,
// category id, category label, category symbol. Empty query
// restores all rows. Category rows hide when zero kinds in them
// match. Pure DOM display toggle — no save state, no API call.
function applyKindFilter(query) {
  const q = (query || '').trim().toLowerCase();
  const tbody = document.getElementById('body');
  if (!tbody) return;
  const kindRows = tbody.querySelectorAll('tr.kind-row');
  const catRows = tbody.querySelectorAll('tr.cat-row');
  const kindMatchByCat = {};  // catId -> bool (any visible kind?)
  let visibleKinds = 0;
  for (const row of kindRows) {
    const code = row.dataset.kindCode || '';
    const k = DATA.kinds.find(kk => kk.code === code);
    const cat = k && DATA.categories.find(cc => cc.id === k.category);
    let match = q === '';
    if (!match) {
      const haystack = [
        code,
        (k && k.label) || '',
        (cat && cat.id) || '',
        (cat && cat.label) || '',
        (cat && cat.symbol) || '',
      ].join(' ').toLowerCase();
      match = haystack.indexOf(q) >= 0;
    }
    row.style.display = match ? '' : 'none';
    if (match) visibleKinds += 1;
    const catId = row.dataset.catId || '';
    if (catId) {
      kindMatchByCat[catId] = kindMatchByCat[catId] || match;
    }
  }
  for (const row of catRows) {
    const catId = row.dataset.catId || '';
    const visible = q === '' || !!kindMatchByCat[catId];
    row.style.display = visible ? '' : 'none';
  }
  // Update status text + clear-button visibility.
  const status = document.getElementById('psi28-filter-status');
  if (status) {
    if (q === '') {
      status.textContent = '';
    } else {
      status.textContent = `${visibleKinds}/${kindRows.length} kinds`;
    }
  }
  const clearBtn = document.getElementById('psi28-clear-filter');
  if (clearBtn) clearBtn.classList.toggle('hidden', q === '');
}

// ψ.28 — bind input + clear-button + global "/" shortcut. Bind
// once via dataset sentinel so multiple loadMatrix() calls don't
// stack listeners.
function setupKindFilter() {
  const input = document.getElementById('psi28-kind-filter');
  if (!input || input.dataset.psi28Bound === '1') return;
  input.dataset.psi28Bound = '1';
  input.addEventListener('input', () => applyKindFilter(input.value));
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      input.value = '';
      applyKindFilter('');
      input.blur();
    }
  });
  const clearBtn = document.getElementById('psi28-clear-filter');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      input.value = '';
      applyKindFilter('');
      input.focus();
    });
  }
  // Global "/" shortcut: focus the filter input unless the user is
  // typing in another input/textarea/select or a contenteditable
  // surface.
  document.addEventListener('keydown', (e) => {
    if (e.key !== '/') return;
    const a = document.activeElement;
    if (a) {
      const tag = a.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if (a.isContentEditable) return;
    }
    e.preventDefault();
    input.focus();
    input.select();
  });
}

// ψ.29 — undo/redo stack for kind/category toggle ops. Each op
// records `[{code, from, to}]` so undo restores the exact prior
// state without rebuilding tbody. Stack cleared on edition switch
// / reset / save (state-mismatch safety).
let UNDO_STACK = [];
let REDO_STACK = [];
const UNDO_MAX = 50;

function clearUndoHistory() {
  UNDO_STACK = [];
  REDO_STACK = [];
  refreshUndoButtons();
}

function pushUndoOp(op) {
  UNDO_STACK.push(op);
  if (UNDO_STACK.length > UNDO_MAX) UNDO_STACK.shift();
  REDO_STACK = [];  // any new op invalidates redo
  refreshUndoButtons();
}

function refreshUndoButtons() {
  const undoBtn = document.getElementById('psi29-undo-btn');
  const redoBtn = document.getElementById('psi29-redo-btn');
  if (undoBtn) undoBtn.disabled = UNDO_STACK.length === 0;
  if (redoBtn) redoBtn.disabled = REDO_STACK.length === 0;
}

// ψ.29 — apply an op forward (= reapply) or backward (= undo).
// Patches LOCAL_ENABLED + DOM checkbox + parent category
// indeterminate via existing ψ.12 helpers; never rebuilds tbody.
function applyOpDirection(op, direction) {
  const touchedCats = new Set();
  for (const change of op.changes) {
    const target = direction === 'forward' ? change.to : change.from;
    if (target) LOCAL_ENABLED.add(change.code);
    else LOCAL_ENABLED.delete(change.code);
    const cb = document.querySelector(
      `.kind-toggle[data-kind="${change.code}"]`
    );
    if (cb) cb.checked = target;
    const k = DATA.kinds.find(kk => kk.code === change.code);
    if (k) touchedCats.add(k.category);
  }
  for (const catId of touchedCats) updateCategoryCheckbox(catId);
  refreshDirtyBanner();
  renderSymbolTotals();
}

function undo() {
  if (UNDO_STACK.length === 0) return false;
  const op = UNDO_STACK.pop();
  applyOpDirection(op, 'backward');
  REDO_STACK.push(op);
  refreshUndoButtons();
  return true;
}

function redo() {
  if (REDO_STACK.length === 0) return false;
  const op = REDO_STACK.pop();
  applyOpDirection(op, 'forward');
  UNDO_STACK.push(op);
  refreshUndoButtons();
  return true;
}

// ψ.29 — keyboard help modal show/hide. Returns the focused
// element to the page after close so Tab navigation resumes
// from the prior position.
let __psi29HelpReturnFocus = null;
function showKeyboardHelp() {
  const overlay = document.getElementById('psi29-help-overlay');
  if (!overlay) return;
  __psi29HelpReturnFocus = document.activeElement;
  overlay.classList.remove('hidden');
  overlay.setAttribute('aria-hidden', 'false');
  const closeBtn = document.getElementById('psi29-help-close');
  if (closeBtn) closeBtn.focus();
}
function closeKeyboardHelp() {
  const overlay = document.getElementById('psi29-help-overlay');
  if (!overlay) return;
  overlay.classList.add('hidden');
  overlay.setAttribute('aria-hidden', 'true');
  if (__psi29HelpReturnFocus && typeof __psi29HelpReturnFocus.focus === 'function') {
    __psi29HelpReturnFocus.focus();
  }
  __psi29HelpReturnFocus = null;
}

// ψ.29 — global keyboard shortcut router. Bound once via
// window.__psi29Bound. Skips Cmd+Z / Cmd+Y / `?` when the user is
// typing in an INPUT/TEXTAREA/SELECT/contenteditable so native
// browser undo + literal `?` typing aren't hijacked. Cmd+S still
// fires anywhere since saving works the same regardless of focus.
function handlePsi29Shortcut(e) {
  const a = document.activeElement;
  const inInput = a && (
    a.tagName === 'INPUT' ||
    a.tagName === 'TEXTAREA' ||
    a.tagName === 'SELECT' ||
    a.isContentEditable
  );
  const mod = e.ctrlKey || e.metaKey;
  // Cmd/Ctrl + S — save the active edition.
  if (mod && !e.altKey && (e.key === 's' || e.key === 'S')) {
    e.preventDefault();
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn && !saveBtn.disabled) saveBtn.click();
    return;
  }
  // Cmd+Shift+Z or Ctrl+Y — redo (check before plain Cmd+Z below).
  if (mod && !e.altKey && (
    (e.shiftKey && (e.key === 'z' || e.key === 'Z')) ||
    (!e.shiftKey && (e.key === 'y' || e.key === 'Y'))
  )) {
    if (inInput) return;
    e.preventDefault();
    redo();
    return;
  }
  // Cmd/Ctrl + Z (no Shift) — undo.
  if (mod && !e.altKey && !e.shiftKey && (e.key === 'z' || e.key === 'Z')) {
    if (inInput) return;
    e.preventDefault();
    undo();
    return;
  }
  // Esc — close help if open.
  if (e.key === 'Escape') {
    const overlay = document.getElementById('psi29-help-overlay');
    if (overlay && !overlay.classList.contains('hidden')) {
      e.preventDefault();
      closeKeyboardHelp();
      return;
    }
  }
  // ? — show keyboard help.
  if (e.key === '?') {
    if (inInput) return;
    e.preventDefault();
    showKeyboardHelp();
    return;
  }
}

// ψ.26 — bulk operations: shift+click range-select, drag-select,
// and apply-to-all-editions. Shift+click + drag-select operate on
// LOCAL_ENABLED for the active edition and record ONE ψ.29 undo op.
// Apply-to-all-editions calls the bulk-save endpoint (clears undo
// since it bypasses LOCAL_ENABLED).

let PSI26_LAST_CLICKED_INDEX = null;  // visible-row index of the last
                                      // non-shift kind toggle click
const PSI26_DRAG = {
  active: false,
  startY: 0,
  startX: 0,
  initialChecked: false,  // target state to apply across the drag
  startCode: null,
  touched: new Map(),     // code → {from, to}
};
const PSI26_DRAG_THRESHOLD = 4;  // px; movement under this is a click

// Bulk apply: flip a list of kind codes to a target enabled-state in
// one go. Mutates LOCAL_ENABLED + DOM checkboxes + parent-category
// indeterminate state + dirty banner + symbol totals. Pushes ONE
// ψ.29 undo op covering all the changes.
function applyKindsBulk(changes) {
  if (!changes || changes.length === 0) return;
  const touchedCats = new Set();
  const ops = [];
  for (const c of changes) {
    const before = LOCAL_ENABLED.has(c.code);
    if (c.target) LOCAL_ENABLED.add(c.code);
    else LOCAL_ENABLED.delete(c.code);
    const after = LOCAL_ENABLED.has(c.code);
    if (before === after) continue;
    const cb = document.querySelector(`.kind-toggle[data-kind="${c.code}"]`);
    if (cb) cb.checked = after;
    const k = DATA.kinds.find(kk => kk.code === c.code);
    if (k) touchedCats.add(k.category);
    ops.push({code: c.code, from: before, to: after});
  }
  if (ops.length === 0) return;
  pushUndoOp({type: 'bulk', changes: ops});
  for (const catId of touchedCats) updateCategoryCheckbox(catId);
  refreshDirtyBanner();
  renderSymbolTotals();
}

// Resolve a kind code to its visible-row order (post ψ.28 filter).
// Hidden rows are excluded so range-select skips over them.
function psi26VisibleKindOrder() {
  const tbody = document.getElementById('body');
  if (!tbody) return [];
  const rows = tbody.querySelectorAll('tr.kind-row');
  const out = [];
  for (const r of rows) {
    if (r.style.display === 'none') continue;
    const code = r.dataset.kindCode;
    if (code) out.push(code);
  }
  return out;
}

// Click handler — returns true if the event was handled (caller
// should preventDefault). Returns false for normal single-click
// pass-through to the existing change handler.
function handlePsi26ToggleClick(ev, code, cb) {
  // Drag in progress? Suppress so the change event doesn't double-fire.
  if (PSI26_DRAG.active) return true;
  if (!ev.shiftKey) {
    // Plain click — record the index for future shift+click anchor.
    const order = psi26VisibleKindOrder();
    PSI26_LAST_CLICKED_INDEX = order.indexOf(code);
    return false;
  }
  // Shift+click — range-select from last anchor to this kind.
  const order = psi26VisibleKindOrder();
  const here = order.indexOf(code);
  if (here < 0) return false;
  // Target state = OPPOSITE of this checkbox's current state (we're
  // about to toggle it; anything between should match the new state).
  const target = !cb.checked;
  let lo, hi;
  if (PSI26_LAST_CLICKED_INDEX === null || PSI26_LAST_CLICKED_INDEX < 0) {
    lo = hi = here;
  } else {
    lo = Math.min(PSI26_LAST_CLICKED_INDEX, here);
    hi = Math.max(PSI26_LAST_CLICKED_INDEX, here);
  }
  const changes = [];
  for (let i = lo; i <= hi; i++) {
    changes.push({code: order[i], target});
  }
  applyKindsBulk(changes);
  PSI26_LAST_CLICKED_INDEX = here;
  return true;  // we already mutated; suppress the default click
}

function psi26StartDrag(ev, code, cb) {
  if (ev.button !== 0) return;  // left-click only
  // Shift+click is range-select, not drag — let the click handler take it.
  if (ev.shiftKey) return;
  PSI26_DRAG.active = false;  // not yet — wait for movement
  PSI26_DRAG.startY = ev.clientY;
  PSI26_DRAG.startX = ev.clientX;
  PSI26_DRAG.initialChecked = !cb.checked;  // target after the click flips it
  PSI26_DRAG.startCode = code;
  PSI26_DRAG.touched = new Map();
}

function psi26EnterDragMode() {
  if (PSI26_DRAG.active) return;
  PSI26_DRAG.active = true;
  document.body.classList.add('psi26-dragging');
}

function psi26OnMouseMove(ev) {
  if (PSI26_DRAG.startCode === null) return;
  if (!PSI26_DRAG.active) {
    const dx = ev.clientX - PSI26_DRAG.startX;
    const dy = ev.clientY - PSI26_DRAG.startY;
    if (dx * dx + dy * dy < PSI26_DRAG_THRESHOLD * PSI26_DRAG_THRESHOLD) {
      return;  // not yet a drag
    }
    psi26EnterDragMode();
    // Include the start row in the touched set with its initial flip.
    PSI26_DRAG.touched.set(PSI26_DRAG.startCode, PSI26_DRAG.initialChecked);
  }
  // Hit-test under the pointer for a kind-toggle.
  const el = document.elementFromPoint(ev.clientX, ev.clientY);
  if (!el) return;
  const row = el.closest && el.closest('tr.kind-row');
  if (!row) return;
  const code = row.dataset.kindCode;
  if (!code) return;
  if (PSI26_DRAG.touched.has(code)) return;
  PSI26_DRAG.touched.set(code, PSI26_DRAG.initialChecked);
  row.classList.add('psi26-drag-touched');
}

function psi26OnMouseUp() {
  if (PSI26_DRAG.startCode === null) return;
  if (!PSI26_DRAG.active) {
    // No drag — was just a click. Reset and let the normal flow run.
    PSI26_DRAG.startCode = null;
    return;
  }
  // Flush the touched set as one bulk op.
  const changes = [];
  for (const [code, target] of PSI26_DRAG.touched.entries()) {
    changes.push({code, target});
  }
  PSI26_DRAG.active = false;
  PSI26_DRAG.startCode = null;
  PSI26_DRAG.touched = new Map();
  document.body.classList.remove('psi26-dragging');
  // Clear visual cues
  document.querySelectorAll('.kind-row.psi26-drag-touched').forEach(r => {
    r.classList.remove('psi26-drag-touched');
  });
  applyKindsBulk(changes);
}

// Apply-to-all-editions modal. Shows the current per-edition state
// of the kind so the operator knows what's about to change.
function showApplyToAll(kindCode) {
  const overlay = document.getElementById('psi26-applyall-overlay');
  if (!overlay || !DATA) return;
  const kindEl = document.getElementById('psi26-applyall-kind');
  const summaryEl = document.getElementById('psi26-applyall-summary');
  const listEl = document.getElementById('psi26-applyall-perlist');
  const fbEl = document.getElementById('psi26-applyall-feedback');
  if (kindEl) kindEl.textContent = kindCode;
  if (fbEl) fbEl.textContent = '';
  // Compute per-edition state from /api/matrix's enabled_kinds_set.
  const rows = [];
  let enabledN = 0;
  let disabledN = 0;
  for (const ed of DATA.editions) {
    const m = DATA.matrix[ed.id];
    const onSet = new Set(m.enabled_kinds_set || []);
    const enabled = onSet.has(kindCode);
    if (enabled) enabledN += 1;
    else disabledN += 1;
    rows.push({id: ed.id, title: ed.short_title || ed.title || ed.id, enabled});
  }
  if (summaryEl) {
    summaryEl.textContent = `${enabledN} edition${enabledN === 1 ? '' : 's'} have it enabled · ${disabledN} disabled.`;
  }
  if (listEl) {
    listEl.innerHTML = rows.map(r => `
      <div class="flex items-center justify-between gap-2 py-0.5">
        <span class="font-mono">${escapeText(r.id)}</span>
        <span>${escapeText(r.title)}</span>
        <span class="${r.enabled ? 'text-emerald-700' : 'text-slate-400'}">${r.enabled ? '✓ on' : '○ off'}</span>
      </div>
    `).join('');
  }
  // Stash kind on the overlay so the action buttons can read it.
  overlay.dataset.kind = kindCode;
  overlay.classList.remove('hidden');
  overlay.setAttribute('aria-hidden', 'false');
}

function closeApplyToAll() {
  const overlay = document.getElementById('psi26-applyall-overlay');
  if (!overlay) return;
  overlay.classList.add('hidden');
  overlay.setAttribute('aria-hidden', 'true');
}

async function submitApplyToAll(enable) {
  const overlay = document.getElementById('psi26-applyall-overlay');
  const fb = document.getElementById('psi26-applyall-feedback');
  if (!overlay) return;
  const kind = overlay.dataset.kind;
  if (!kind) return;
  const enableBtn = document.getElementById('psi26-applyall-enable');
  const disableBtn = document.getElementById('psi26-applyall-disable');
  if (enableBtn) enableBtn.disabled = true;
  if (disableBtn) disableBtn.disabled = true;
  if (fb) {
    fb.className = 'text-xs mt-3 text-slate-500';
    fb.textContent = enable ? 'enabling…' : 'disabling…';
  }
  try {
    const r = await fetch('/api/matrix/apply-kind-to-all', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({kind, enable}),
    });
    const data = await r.json();
    if (!r.ok || data.error) {
      if (fb) {
        fb.className = 'text-xs mt-3 text-red-600';
        fb.textContent = `${data.error || ('http ' + r.status)}: ${data.message || ''}`;
      }
      return;
    }
    if (fb) {
      fb.className = 'text-xs mt-3 text-emerald-700';
      const fp = (data.failures || []).length;
      fb.textContent = fp
        ? `✓ changed ${data.changed} edition(s); ${fp} failure(s)`
        : `✓ changed ${data.changed} edition(s) · ${data.noop} unchanged`;
    }
    // Refresh DATA + rebuild so the matrix counts reflect the changes.
    const fresh = await fetch('/api/matrix').then(r => r.json());
    DATA = fresh;
    refreshActiveEdition();  // also clears undo history
    setTimeout(closeApplyToAll, 700);
  } catch (e) {
    if (fb) {
      fb.className = 'text-xs mt-3 text-red-600';
      fb.textContent = `error: ${e.message}`;
    }
  } finally {
    if (enableBtn) enableBtn.disabled = false;
    if (disableBtn) disableBtn.disabled = false;
  }
}

function setupPsi26BulkOps() {
  if (window.__psi26Bound) return;
  window.__psi26Bound = true;
  // Drag handlers live on document so we catch movement that leaves
  // the original checkbox.
  document.addEventListener('mousemove', psi26OnMouseMove);
  document.addEventListener('mouseup', psi26OnMouseUp);
  // Apply-to-all modal wiring.
  const close = document.getElementById('psi26-applyall-close');
  const cancel = document.getElementById('psi26-applyall-cancel');
  const enableBtn = document.getElementById('psi26-applyall-enable');
  const disableBtn = document.getElementById('psi26-applyall-disable');
  const overlay = document.getElementById('psi26-applyall-overlay');
  if (close) close.addEventListener('click', closeApplyToAll);
  if (cancel) cancel.addEventListener('click', closeApplyToAll);
  if (enableBtn) enableBtn.addEventListener('click', () => submitApplyToAll(true));
  if (disableBtn) disableBtn.addEventListener('click', () => submitApplyToAll(false));
  if (overlay) {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) closeApplyToAll();
    });
  }
}

function setupKeyboardShortcuts() {
  if (window.__psi29Bound) return;
  window.__psi29Bound = true;
  document.addEventListener('keydown', handlePsi29Shortcut);
  const helpBtn = document.getElementById('psi29-help-btn');
  if (helpBtn) helpBtn.addEventListener('click', showKeyboardHelp);
  const closeBtn = document.getElementById('psi29-help-close');
  if (closeBtn) closeBtn.addEventListener('click', closeKeyboardHelp);
  const overlay = document.getElementById('psi29-help-overlay');
  if (overlay) {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) closeKeyboardHelp();
    });
  }
  const undoBtn = document.getElementById('psi29-undo-btn');
  const redoBtn = document.getElementById('psi29-redo-btn');
  if (undoBtn) undoBtn.addEventListener('click', undo);
  if (redoBtn) redoBtn.addEventListener('click', redo);
  refreshUndoButtons();
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
  // ψ.29 — record the prior state so undo can restore it.
  const before = LOCAL_ENABLED.has(code);
  if (on) LOCAL_ENABLED.add(code);
  else LOCAL_ENABLED.delete(code);
  const after = LOCAL_ENABLED.has(code);
  if (before !== after) {
    pushUndoOp({type: 'kind', changes: [{code, from: before, to: after}]});
  }
  // ψ.12 — incremental: just patch the parent category checkbox's
  // indeterminate state. The toggled kind's checkbox is already in
  // its target visual state (the user clicked it).
  const kind = DATA.kinds.find(k => k.code === code);
  if (kind) updateCategoryCheckbox(kind.category);
  refreshDirtyBanner();
  // ψ.18 — re-render totals so per-symbol counts reflect the toggle.
  renderSymbolTotals();
}

function onToggleCategory(catId, on) {
  // ψ.12 — incremental: walk every kind-row checkbox in this
  // category and set its checked state directly. No tbody teardown,
  // no listener re-attachment, no scroll jump.
  // ψ.29 — collect the per-kind from/to deltas so undo can restore
  // exactly the kinds that flipped (skipping no-ops).
  const kinds = DATA.kinds.filter(k => k.category === catId);
  const changes = [];
  for (const k of kinds) {
    const before = LOCAL_ENABLED.has(k.code);
    if (on) LOCAL_ENABLED.add(k.code);
    else LOCAL_ENABLED.delete(k.code);
    const after = LOCAL_ENABLED.has(k.code);
    if (before !== after) {
      changes.push({code: k.code, from: before, to: after});
    }
    const kc = document.querySelector(
      `.kind-toggle[data-kind="${k.code}"]`
    );
    if (kc) kc.checked = on;
  }
  if (changes.length > 0) {
    pushUndoOp({type: 'category', catId, changes});
  }
  // The category's own indeterminate is now resolved one way or
  // the other; the checkbox's `change` event already set its
  // own .checked, so nothing more to do for the parent.
  const catCheckbox = document.querySelector(
    `.cat-toggle[data-cat="${catId}"]`
  );
  if (catCheckbox) catCheckbox.indeterminate = false;
  refreshDirtyBanner();
  // ψ.18 — re-render totals so per-symbol counts reflect the bulk toggle.
  renderSymbolTotals();
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
    clearUndoHistory();  // ψ.29 — bulk revert invalidates the stack
    buildBody();
    refreshDirtyBanner();
    renderSymbolTotals();   // ψ.18 — sidebar reflects reverted state
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
      status.innerHTML = `<span class="text-red-600">✗ ${escapeHTML(result.error || 'save failed')}</span>`;
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
    // ψ.27 — group built-in presets above user-saved scenarios.
    // api_list_scenarios pre-sorts (builtin first, then by name) but
    // we explicitly partition here for the section header.
    const builtins = data.scenarios.filter(s => s.builtin);
    const userSaved = data.scenarios.filter(s => !s.builtin);
    const renderRow = (s) => `
      <div class="flex items-center justify-between gap-2 border border-slate-200 rounded px-2 py-1.5"
           data-scenario-row="${s.name}">
        <div class="min-w-0 flex-1">
          <div class="font-medium truncate flex items-center gap-1.5" title="${(s.notes || '').replace(/"/g, '&quot;')}">
            ${s.builtin ? '<span class="text-[0.6rem] uppercase tracking-wide bg-slate-100 text-slate-600 border border-slate-200 rounded px-1 py-0.5">built-in</span>' : ''}
            <span class="truncate">${escapeText(s.label || s.name)}</span>
          </div>
          <div class="text-xs text-slate-500 font-mono truncate">${s.name} · from ${s.based_on || '—'} · ${(s.enabled_kinds || []).length} kinds</div>
        </div>
        <button data-scenario-load="${s.name}" class="text-xs text-blue-600 hover:underline">load</button>
        <button data-scenario-export="${s.name}" class="text-xs text-blue-600 hover:underline">export</button>
        ${s.builtin ? '' : `<button data-scenario-del="${s.name}" class="text-xs text-red-600 hover:underline" title="Delete scenario">×</button>`}
      </div>
    `;
    let html = '';
    if (builtins.length) {
      html += `<div class="text-[0.65rem] uppercase tracking-wide text-slate-400 mt-1 mb-1">Built-in presets</div>`;
      html += builtins.map(renderRow).join('');
    }
    if (userSaved.length) {
      html += `<div class="text-[0.65rem] uppercase tracking-wide text-slate-400 mt-3 mb-1">Saved by you</div>`;
      html += userSaved.map(renderRow).join('');
    } else if (builtins.length) {
      html += `<div class="text-[0.65rem] text-slate-400 italic mt-3">no user-saved scenarios yet — use Save As to create one</div>`;
    }
    list.innerHTML = html;
    // Wire load + export + delete buttons
    list.querySelectorAll('[data-scenario-load]').forEach(b => {
      b.addEventListener('click', () => loadScenario(b.dataset.scenarioLoad));
    });
    list.querySelectorAll('[data-scenario-export]').forEach(b => {
      b.addEventListener('click', () => showExportYaml(b.dataset.scenarioExport));
    });
    list.querySelectorAll('[data-scenario-del]').forEach(b => {
      b.addEventListener('click', () => deleteScenario(b.dataset.scenarioDel));
    });
  } catch (e) {
    list.innerHTML = `<div class="text-xs text-red-600">failed: ${e.message}</div>`;
  }
}

// ψ.27 — populate + show the Export modal with the raw YAML for a
// given scenario. Uses the existing /api/scenarios/<name>/export.yaml
// route so the textarea contents match what a download would yield.
async function showExportYaml(name) {
  const overlay = document.getElementById('psi27-export-overlay');
  const ta = document.getElementById('psi27-export-yaml');
  const nameSpan = document.getElementById('psi27-export-name');
  const dlAnchor = document.getElementById('psi27-export-download');
  const fb = document.getElementById('psi27-export-feedback');
  if (!overlay || !ta) return;
  if (fb) fb.textContent = '';
  if (nameSpan) nameSpan.textContent = name;
  ta.value = 'loading…';
  overlay.classList.remove('hidden');
  overlay.setAttribute('aria-hidden', 'false');
  try {
    const r = await fetch(`/api/scenarios/${encodeURIComponent(name)}/export.yaml`);
    if (!r.ok) {
      ta.value = `# error: ${r.status} ${r.statusText}`;
      return;
    }
    const text = await r.text();
    ta.value = text;
    if (dlAnchor) {
      const blob = new Blob([text], {type: 'application/x-yaml'});
      if (dlAnchor.dataset.previousObjectUrl) {
        URL.revokeObjectURL(dlAnchor.dataset.previousObjectUrl);
      }
      const objUrl = URL.createObjectURL(blob);
      dlAnchor.href = objUrl;
      dlAnchor.download = `${name}.yaml`;
      dlAnchor.dataset.previousObjectUrl = objUrl;
    }
  } catch (e) {
    ta.value = `# error: ${e.message}`;
  }
}

function closeExportYaml() {
  const overlay = document.getElementById('psi27-export-overlay');
  if (!overlay) return;
  overlay.classList.add('hidden');
  overlay.setAttribute('aria-hidden', 'true');
}

function showImportYaml() {
  const overlay = document.getElementById('psi27-import-overlay');
  if (!overlay) return;
  document.getElementById('psi27-import-feedback').textContent = '';
  overlay.classList.remove('hidden');
  overlay.setAttribute('aria-hidden', 'false');
  const nameInput = document.getElementById('psi27-import-name');
  if (nameInput) nameInput.focus();
}

function closeImportYaml() {
  const overlay = document.getElementById('psi27-import-overlay');
  if (!overlay) return;
  overlay.classList.add('hidden');
  overlay.setAttribute('aria-hidden', 'true');
}

async function submitImportYaml() {
  const nameEl = document.getElementById('psi27-import-name');
  const yamlEl = document.getElementById('psi27-import-yaml');
  const overwriteEl = document.getElementById('psi27-import-overwrite');
  const fb = document.getElementById('psi27-import-feedback');
  if (!nameEl || !yamlEl) return;
  const name = (nameEl.value || '').trim();
  const yamlText = yamlEl.value || '';
  const overwrite = !!(overwriteEl && overwriteEl.checked);
  fb.className = 'text-xs ml-auto text-slate-500';
  fb.textContent = 'importing…';
  try {
    const r = await fetch('/api/scenarios/_import', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({yaml: yamlText, name: name || undefined, overwrite}),
    });
    const data = await r.json();
    if (!r.ok || data.error) {
      fb.className = 'text-xs ml-auto text-red-600';
      fb.textContent = `${data.error || ('http ' + r.status)}: ${data.message || ''}`;
      return;
    }
    fb.className = 'text-xs ml-auto text-emerald-700';
    fb.textContent = `✓ saved as "${data.name}"`;
    refreshScenarioList();
    setTimeout(() => closeImportYaml(), 700);
  } catch (e) {
    fb.className = 'text-xs ml-auto text-red-600';
    fb.textContent = `error: ${e.message}`;
  }
}

function setupPsi27Modals() {
  if (window.__psi27Bound) return;
  window.__psi27Bound = true;
  // Export modal
  const expOverlay = document.getElementById('psi27-export-overlay');
  const expClose = document.getElementById('psi27-export-close');
  const expCopy = document.getElementById('psi27-export-copy');
  const expDownloadBtn = document.getElementById('psi27-export-download-btn');
  const dlAnchor = document.getElementById('psi27-export-download');
  if (expClose) expClose.addEventListener('click', closeExportYaml);
  if (expOverlay) {
    expOverlay.addEventListener('click', (e) => {
      if (e.target === expOverlay) closeExportYaml();
    });
  }
  if (expCopy) {
    expCopy.addEventListener('click', async () => {
      const ta = document.getElementById('psi27-export-yaml');
      const fb = document.getElementById('psi27-export-feedback');
      if (!ta) return;
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(ta.value);
        } else {
          ta.select();
          document.execCommand('copy');
        }
        if (fb) fb.textContent = '✓ copied';
        setTimeout(() => { if (fb) fb.textContent = ''; }, 1500);
      } catch (e) {
        if (fb) fb.textContent = `copy failed: ${e.message}`;
      }
    });
  }
  if (expDownloadBtn && dlAnchor) {
    expDownloadBtn.addEventListener('click', () => dlAnchor.click());
  }
  // Import modal
  const impOverlay = document.getElementById('psi27-import-overlay');
  const impClose = document.getElementById('psi27-import-close');
  const impCancel = document.getElementById('psi27-import-cancel');
  const impSubmit = document.getElementById('psi27-import-submit');
  const importBtn = document.getElementById('psi27-import-btn');
  if (impClose) impClose.addEventListener('click', closeImportYaml);
  if (impCancel) impCancel.addEventListener('click', closeImportYaml);
  if (impOverlay) {
    impOverlay.addEventListener('click', (e) => {
      if (e.target === impOverlay) closeImportYaml();
    });
  }
  if (impSubmit) impSubmit.addEventListener('click', submitImportYaml);
  if (importBtn) importBtn.addEventListener('click', showImportYaml);
}

async function loadScenario(name) {
  try {
    const r = await fetch(`/api/scenarios/${encodeURIComponent(name)}`);
    const data = await r.json();
    if (data.error) {
      document.getElementById('save-status').innerHTML = `<span class="text-red-600">✗ ${data.error}</span>`;
      return;
    }
    // ψ.27 — prefer the resolved kind list (recipes are materialized
    // server-side via the canonical _enabled_kinds_for_edition helper).
    // Fall back to the explicit `enabled_kinds` for back-compat with
    // user-saved records written by the older api_save_scenario.
    const sc = data.scenario;
    const kinds = sc.enabled_kinds_resolved || sc.enabled_kinds || [];
    LOCAL_ENABLED = new Set(kinds);
    buildBody();
    refreshDirtyBanner();
    renderSymbolTotals();   // ψ.18 — sidebar reflects loaded scenario
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
  // ψ.29 — undo history is per-edition state; switching/refreshing
  // the active edition (or post-save) invalidates any prior ops.
  clearUndoHistory();

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
          <span><span class="symbol text-slate-500">${escapeText(c.symbol)}</span> ${escapeText(c.label)}</span>
          <span class="font-mono text-slate-500">${n.toLocaleString()} <span class="text-slate-400">(${pct}%)</span></span>
        </div>
        <div class="h-1.5 bg-slate-100 rounded overflow-hidden">
          <div class="h-full bg-blue-400" style="width:${pct}%"></div>
        </div>
      </div>`;
  }).filter(Boolean).join('');

  // ψ.18 — Symbol totals sidebar with per-book sparklines.
  renderSymbolTotals();
}


// ψ.18 — Render the per-symbol totals + per-book sparkline panel.
// Reads from m.per_book + m.canon_book_order; iterates LOCAL_ENABLED
// so live toggles update the totals without a server round-trip.
//
// Sparkline encoding: 8-level Unicode block characters
// (' ▁▂▃▄▅▆▇█') one per book in canonical order. Empty = book
// has no notes of this kind; full block = book has the most.
const SPARK_CHARS = ' ▁▂▃▄▅▆▇█';

// ψ.18.1 / ψ.18.2 — top-5 cap for the eager chapter drilldown. The
// rest of the books (hiddenBooks) are reachable via ψ.18.2's nested
// `<details class="psi182-rest">` lazy-render handler.
const TOP_N_BOOKS = 5;

// ψ.18.2 — build one chapter-sparkline row record for a single
// book. Extracted from renderSymbolTotals so the lazy-expand
// handler can reuse the exact same shape without duplicating the
// scaling + tooltip logic. Returns the row object that
// chapterRowHtml(...) consumes.
function buildChapterSparklineRow(bookCode, count, chCount, byCh) {
  let bookMax = 0;
  for (const v of Object.values(byCh)) {
    if (v > bookMax) bookMax = v;
  }
  let upper = chCount;
  if (upper <= 0) {
    for (const ch of Object.keys(byCh)) {
      const ci = parseInt(ch, 10);
      if (ci > upper) upper = ci;
    }
  }
  const chChars = [];
  const chTooltips = [];
  for (let ci = 1; ci <= upper; ci++) {
    const v = byCh[ci] || byCh[String(ci)] || 0;
    let lvl = 0;
    if (bookMax > 0 && v > 0) {
      lvl = Math.min(8, 1 + Math.floor((v / bookMax) * 7));
    }
    chChars.push(SPARK_CHARS[lvl]);
    if (v > 0) chTooltips.push(`ch ${ci}: ${v}`);
  }
  return {
    code: bookCode,
    count,
    chapters: Object.keys(byCh).length,
    spark: chChars.join(''),
    tooltip: chTooltips.join('  ') || `${bookCode}: no chapter data`,
  };
}

// ψ.18.2 — single-row HTML serializer for a chapter-sparkline row.
// Used both eagerly (top-N) and lazily (rest) so the markup stays
// in sync.
function chapterRowHtml(br) {
  return `
      <div class="flex items-baseline gap-2 mt-1" title="${escapeAttr(br.tooltip)}">
        <span class="font-mono text-slate-500 text-[0.7rem] w-10 truncate">${escapeText(br.code)}</span>
        <span class="font-mono text-slate-400 leading-none flex-1 whitespace-nowrap overflow-hidden" style="font-size:0.7rem;letter-spacing:-0.05em">${escapeText(br.spark)}</span>
        <span class="font-mono text-slate-500 text-[0.7rem] tabular-nums">${br.count.toLocaleString()}<span class="text-slate-400"> · ${br.chapters}ch</span></span>
      </div>`;
}

// ψ.18.2 — lazy chapter-row builder for the long tail of books
// past TOP_N_BOOKS. Pulls fresh data from DATA.matrix; called by
// the delegated toggle handler on first expand of a
// `<details class="psi182-rest">` block.
function buildKindRestChapterRows(kindCode) {
  const m = DATA.matrix[ACTIVE_EDITION];
  if (!m || !m.per_book) return [];
  const perBook = m.per_book;
  const perChapter = m.per_chapter || {};
  const bookChCounts = m.book_chapter_counts || {};
  const bookCounts = perBook[kindCode] || {};
  const chapterByBook = perChapter[kindCode] || {};
  const bookTotals = Object.entries(bookCounts)
    .map(([bc, n]) => ({code: bc, count: n}))
    .sort((a, b) => b.count - a.count);
  return bookTotals.slice(TOP_N_BOOKS).map(br =>
    buildChapterSparklineRow(
      br.code, br.count,
      bookChCounts[br.code] || 0,
      chapterByBook[br.code] || {}));
}

function renderSymbolTotals() {
  const m = DATA.matrix[ACTIVE_EDITION];
  if (!m || !m.per_book) return;
  const list = document.getElementById('totals-list');
  if (!list) return;

  const perBook = m.per_book;
  const perChapter = m.per_chapter || {};        // ψ.18.1
  const bookChCounts = m.book_chapter_counts || {};  // ψ.18.1
  const canon = m.canon_book_order || [];
  // Sum across LOCAL_ENABLED (the user's pending toggle state) so
  // the panel reflects what the edition would ship right now.
  const enabled = LOCAL_ENABLED;

  // Index kinds by category for grouping; sort by count desc within.
  const kindRows = [];
  for (const k of DATA.kinds) {
    if (!enabled.has(k.code)) continue;
    const bookCounts = perBook[k.code] || {};
    let total = 0;
    let max = 0;
    for (const c of canon) {
      const v = bookCounts[c] || 0;
      total += v;
      if (v > max) max = v;
    }
    if (total === 0) continue;
    const cat = DATA.categories.find(cc => cc.id === k.category);
    const symbol = (cat && cat.symbol) || '?';
    // Build per-book sparkline string (one char per canon book)
    const chars = [];
    const tooltips = [];
    for (const code of canon) {
      const v = bookCounts[code] || 0;
      let level = 0;
      if (max > 0 && v > 0) {
        // Map 1..max to 1..8 (skip the empty space char)
        level = Math.min(8, 1 + Math.floor((v / max) * 7));
      }
      chars.push(SPARK_CHARS[level]);
      tooltips.push(`${code}: ${v}`);
    }
    // ψ.18.1 — chapter-level drilldown payload. Top N books by
    // count get a chapter sparkline (one char per chapter). The
    // long tail (rest beyond TOP_N_BOOKS) is rendered lazily by
    // ψ.18.2's nested-details handler on user expand.
    const chapterByBook = perChapter[k.code] || {};
    const bookTotals = Object.entries(bookCounts)
      .map(([bc, n]) => ({code: bc, count: n}))
      .sort((a, b) => b.count - a.count);
    let chaptersWithNotes = 0;
    for (const bc in chapterByBook) {
      chaptersWithNotes += Object.keys(chapterByBook[bc]).length;
    }
    const chapterRows = bookTotals
      .slice(0, TOP_N_BOOKS)
      .map(br => buildChapterSparklineRow(
        br.code, br.count,
        bookChCounts[br.code] || 0,
        chapterByBook[br.code] || {}));
    kindRows.push({
      code: k.code,
      label: k.label,
      symbol,
      total,
      max,
      sparkline: chars.join(''),
      tooltip: tooltips.join('  '),
      chaptersWithNotes,
      booksWithNotes: bookTotals.length,
      chapterRows,
      hiddenBooks: Math.max(0, bookTotals.length - TOP_N_BOOKS),
    });
  }
  kindRows.sort((a, b) => b.total - a.total);

  if (kindRows.length === 0) {
    list.innerHTML = '<div class="text-xs text-slate-400">no kinds enabled</div>';
    document.getElementById('totals-edition').textContent = 'whole edition';
    return;
  }

  document.getElementById('totals-edition').textContent =
    `whole edition · ${m.total_enabled.toLocaleString()} notes shipping`;

  list.innerHTML = kindRows.map(r => {
    const drilldown = r.chapterRows.map(chapterRowHtml).join('');
    // ψ.18.2 — replace the static "+ N more books" italic line with
    // a clickable nested <details>. Lazy-renders the rest of the
    // chapter-sparkline rows on first toggle (handler bound below
    // via event delegation).
    const hiddenNote = r.hiddenBooks > 0
      ? `<details class="psi182-rest" data-kind-code="${escapeAttr(r.code)}">
          <summary class="text-[0.65rem] text-slate-500 mt-1 italic hover:text-slate-700">
            <span class="psi182-arrow inline-block text-slate-400" style="font-size:0.6rem">▸</span>
            + ${r.hiddenBooks} more book${r.hiddenBooks === 1 ? '' : 's'} (click to expand)
          </summary>
          <div class="psi182-rest-rows" data-pending="1"></div>
        </details>`
      : '';
    return `
    <details class="psi181-drilldown">
      <summary class="cursor-pointer list-none">
        <div class="flex items-center gap-2 text-xs" title="${escapeAttr(r.tooltip)}">
          <span class="text-slate-400 text-[0.6rem] select-none psi181-arrow">▸</span>
          <span class="symbol text-slate-700" style="font-size:1.1em">${escapeText(r.symbol)}</span>
          <span class="flex-1 truncate text-slate-700" title="${escapeAttr(r.code)}">${escapeText(r.label)}</span>
          <span class="font-mono text-slate-600 tabular-nums">${r.total.toLocaleString()}</span>
        </div>
        <div class="font-mono text-slate-400 leading-none whitespace-nowrap overflow-hidden ml-3" title="${escapeAttr(r.tooltip)}" style="font-size:0.7rem;letter-spacing:-0.05em">${escapeText(r.sparkline)}</div>
      </summary>
      <div class="mt-2 ml-3 pl-2 border-l border-slate-200">
        <div class="text-[0.65rem] text-slate-400 mb-1">${r.chaptersWithNotes.toLocaleString()} chapter${r.chaptersWithNotes === 1 ? '' : 's'} · ${r.booksWithNotes} book${r.booksWithNotes === 1 ? '' : 's'}</div>
        ${drilldown}
        ${hiddenNote}
      </div>
    </details>
  `;}).join('');

  // ψ.18.2 — bind the lazy expand-all toggle handler exactly once
  // per `#totals-list` element (across re-renders the same node is
  // reused; toggle events bubble to it). The dataset sentinel
  // prevents stacking duplicate listeners.
  if (list.dataset.psi182Bound !== '1') {
    list.addEventListener('toggle', psi182OnRestToggle, true);
    list.dataset.psi182Bound = '1';
  }

  // ψ.20 — render the density heat-map alongside the symbol
  // totals. Same data source (m.per_book), same toggle semantics
  // (sums across LOCAL_ENABLED).
  renderDensityHeatmap();
}

// ψ.18.2 — delegated toggle handler. Fires for every <details> in
// the totals-list subtree (capture-phase since `toggle` doesn't
// bubble in some browsers); only acts on `psi182-rest` nodes that
// just opened with their rows still pending.
function psi182OnRestToggle(ev) {
  const target = ev.target;
  if (!target || !target.classList) return;
  if (!target.classList.contains('psi182-rest')) return;
  if (!target.open) return;
  const container = target.querySelector('.psi182-rest-rows');
  if (!container || container.dataset.pending !== '1') return;
  const kindCode = target.dataset.kindCode || '';
  const rows = buildKindRestChapterRows(kindCode);
  container.innerHTML = rows.map(chapterRowHtml).join('');
  container.dataset.pending = '0';
}

// ψ.20 — note-density heat-map. Cells are colored by percentile
// rank within the visible-book range; greener = denser, redder =
// sparser. Empty books (no notes for any enabled kind) get a
// muted gray cell so they're still visible in the canon order.
function renderDensityHeatmap() {
  const m = DATA.matrix[ACTIVE_EDITION];
  const grid = document.getElementById('psi20-heatmap-grid');
  if (!m || !m.per_book || !grid) return;
  const canon = m.canon_book_order || [];
  if (canon.length === 0) {
    grid.innerHTML = '<div class="text-xs text-slate-400">no books in canon</div>';
    return;
  }
  // Per-book sum across LOCAL_ENABLED kinds.
  const perBook = m.per_book;
  const enabled = LOCAL_ENABLED;
  const counts = canon.map(code => {
    let total = 0;
    for (const kindCode of enabled) {
      const bookCounts = perBook[kindCode];
      if (bookCounts && bookCounts[code]) {
        total += bookCounts[code];
      }
    }
    return {code, count: total};
  });
  // Find max for percentile coloring.
  const max = counts.reduce((a, c) => Math.max(a, c.count), 0);
  const cells = counts.map(({code, count}) => {
    if (count === 0) {
      return `<div class="psi20-cell empty" title="${escapeAttr(code)}: 0">${escapeText(code)}</div>`;
    }
    // Linear interpolation across red → amber → green based on
    // percentile rank against `max` (clamped to >= 1 so a single
    // book with notes doesn't divide by zero).
    const denom = Math.max(max, 1);
    const pct = count / denom;  // 0..1
    const color = psi20HeatColor(pct);
    return `<div class="psi20-cell" style="background:${color}" title="${escapeAttr(code)}: ${count.toLocaleString()} note${count === 1 ? '' : 's'}">${escapeText(code)}</div>`;
  }).join('');
  grid.innerHTML = cells;
}

// Linear interpolation across the red-amber-green stops. Returns
// an "rgb(r,g,b)" string. Uses Tailwind's red-600 (#dc2626),
// amber-500 (#f59e0b), green-600 (#16a34a) as endpoints.
function psi20HeatColor(pct) {
  // Two segments: 0..0.5 → red→amber; 0.5..1 → amber→green.
  const stops = [
    [0.0, 220, 38, 38],   // red-600
    [0.5, 245, 158, 11],  // amber-500
    [1.0, 22, 163, 74],   // green-600
  ];
  let i = 0;
  while (i < stops.length - 1 && pct > stops[i + 1][0]) i++;
  const [t0, r0, g0, b0] = stops[i];
  const [t1, r1, g1, b1] = stops[i + 1] || stops[i];
  const span = (t1 - t0) || 1;
  const f = Math.max(0, Math.min(1, (pct - t0) / span));
  const r = Math.round(r0 + (r1 - r0) * f);
  const g = Math.round(g0 + (g1 - g0) * f);
  const b = Math.round(b0 + (b1 - b0) * f);
  return `rgb(${r},${g},${b})`;
}

function escapeText(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function escapeAttr(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
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
      status.innerHTML = `<span class="text-red-600">✗ ${escapeHTML(result.error || 'save failed')}</span>`;
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

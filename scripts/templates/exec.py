"""ε.2 + ε.3 + ε.6 — /exec dashboard template.

Surfaces SIX executive KPI tiles + sales import card + per-channel /
per-edition rollup tables + distribution checklist grid + a recent-
activity table, rendered from `api_exec_dashboard()` +
`api_sales_rollup()` + `api_distribution_list()` on initial page load.
Tiles:

    1. Editions count           — config.load_editions()
    2. Notes corpus             — api_attribution_audit().counts.total
                                  (with target + progress %)
    3. AI spend MTD             — event log `ai_*` events × `cost`
    4. Perf budget health       — perf_budgets.BUDGETS + violations
    5. Error rate               — build outcomes success_rate
    6. Sales MTD (ε.3)          — sales.totals_mtd() — primary currency

Sales workflow (ε.3):
- Channel selector (KDP / Apple Books / Google Play Books)
- File upload (CSV per the channel's native export format)
- POSTs multipart to `/api/sales/import/<channel>`; toast on result.
- Per-channel + per-edition revenue tables refresh from
  `/api/sales/rollup` after each import.

Distribution checklist (ε.6):
- Editable grid: rows = shipped editions, columns = 5 channels
  (KDP / Apple Books / Google Play Books / Archive.org / Own site).
- Click a cell to toggle shipped/unshipped. PUT/DELETE through
  `/api/distribution/<edition>` with ζ.6 toast on result.
- Per-channel coverage % + overall % displayed below the grid.

Composes the full ζ foundation (theme tokens + dark mode + icons +
toasts + cmd palette). All values insert via `textContent` so any
future event-log payload with exotic characters stays XSS-safe.

Foundation for ε.4 (cost-per-edition rollup expands tile 3), ε.5
(quarterly auto-report composes this payload into PDF), ε.7 (press
kit auto-build can consult the channel state for what to package),
ο.4 (archive.org auto-upload auto-marks the archive_org cell).
"""

from scripts.templates._design import apply_design_system  # noqa: E402

EXEC_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>E-Bible · Executive Dashboard</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  /* ε.2: tile grid + value typography. */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
    gap: 1rem;
  }
  .kpi-tile {
    padding: 1.25rem;
    border-radius: 0.5rem;
  }
  .kpi-value {
    font-size: 2rem;
    line-height: 1.1;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }
  .kpi-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    opacity: 0.7;
    margin-bottom: 0.25rem;
  }
  .kpi-sub {
    font-size: 0.75rem;
    margin-top: 0.5rem;
    opacity: 0.7;
  }
  /* Recent-events table */
  .events-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
  }
  .events-table th,
  .events-table td {
    text-align: left;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--color-border, #e5e7eb);
  }
  .events-table th {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    opacity: 0.7;
  }
  .events-table td.mono {
    font-family: var(--font-mono, monospace);
  }
</style>
<!-- THEME_TOKENS_CSS -->
<!-- DARK_MODE_JS -->
<!-- THEME_ICONS_JS -->
<!-- THEME_TOAST_JS -->
<!-- THEME_CMD_PALETTE_JS -->
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="theme-bg-page theme-text">

<header class="border-b theme-bg-surface theme-border">
  <div class="max-w-6xl mx-auto px-4 py-3 flex items-baseline gap-4 text-sm flex-wrap">
    <strong class="text-base">E-Bible</strong>
    <!-- HEADER_NAV_LINKS -->
    <span id="corpus-progress" class="ml-auto text-xs theme-text-muted" title="corpus depth toward the 35,000-note Ethiopian Tewahedo target">·· loading ··</span>
  </div>
</header>

<main class="max-w-6xl mx-auto px-4 py-6">
  <h1 class="theme-text-2xl theme-weight-semibold mb-2">Executive Dashboard</h1>
  <p class="theme-text-sm theme-text-muted mb-6">
    Top-line KPIs from the publishing platform. Renders from the
    event log (ε.1 metrics collector) + cached corpus aggregators.
    All times UTC.
  </p>

  <section aria-label="KPI tiles" class="kpi-grid mb-8" id="kpi-grid">
    <div class="kpi-tile theme-bg-surface theme-border border" data-tile="editions">
      <div class="kpi-label">Editions</div>
      <div class="kpi-value" data-field="editions-count">·</div>
      <div class="kpi-sub" data-field="editions-sub">configured</div>
    </div>

    <div class="kpi-tile theme-bg-surface theme-border border" data-tile="notes_corpus">
      <div class="kpi-label">Notes corpus</div>
      <div class="kpi-value" data-field="notes-current">·</div>
      <div class="kpi-sub" data-field="notes-sub">toward target</div>
    </div>

    <div class="kpi-tile theme-bg-surface theme-border border" data-tile="ai_spend_mtd">
      <div class="kpi-label">AI spend (MTD)</div>
      <div class="kpi-value" data-field="ai-total">·</div>
      <div class="kpi-sub" data-field="ai-sub">events this month</div>
    </div>

    <div class="kpi-tile theme-bg-surface theme-border border" data-tile="perf_budget_health">
      <div class="kpi-label">Perf budgets</div>
      <div class="kpi-value" data-field="perf-budgets">·</div>
      <div class="kpi-sub" data-field="perf-sub">violations logged</div>
    </div>

    <div class="kpi-tile theme-bg-surface theme-border border" data-tile="error_rate">
      <div class="kpi-label">Build success</div>
      <div class="kpi-value" data-field="builds-rate">·</div>
      <div class="kpi-sub" data-field="builds-sub">terminal builds</div>
    </div>

    <div class="kpi-tile theme-bg-surface theme-border border" data-tile="sales_mtd">
      <div class="kpi-label">Sales (MTD)</div>
      <div class="kpi-value" data-field="sales-total">·</div>
      <div class="kpi-sub" data-field="sales-sub">units this month</div>
    </div>
  </section>

  <section aria-label="Sales import" class="mb-8" id="sales-import-section">
    <h2 class="theme-text-lg theme-weight-semibold mb-3">Sales import</h2>
    <div class="theme-bg-surface theme-border border rounded-lg p-4">
      <p class="theme-text-sm theme-text-muted mb-3">
        Upload a per-channel CSV. Rows append to <code class="theme-font-mono">events.jsonl</code>
        as <code class="theme-font-mono">sales_record</code> events and refresh the rollups below.
      </p>
      <form id="sales-import-form" class="flex flex-wrap gap-3 items-end" enctype="multipart/form-data">
        <label class="flex flex-col gap-1">
          <span class="theme-text-xs theme-text-muted">Channel</span>
          <select id="sales-channel" class="theme-bg-page theme-border border rounded px-2 py-1 theme-text-sm">
            <option value="kdp">KDP (Amazon)</option>
            <option value="apple">Apple Books</option>
            <option value="google">Google Play Books</option>
          </select>
        </label>
        <label class="flex flex-col gap-1">
          <span class="theme-text-xs theme-text-muted">CSV file</span>
          <input type="file" id="sales-file" accept=".csv,text/csv" required
                 class="theme-text-sm">
        </label>
        <button type="submit" id="sales-submit"
                class="theme-bg-accent rounded px-3 py-1 theme-text-sm theme-weight-semibold">
          Import
        </button>
        <span id="sales-status" class="theme-text-xs theme-text-muted"></span>
      </form>
    </div>
  </section>

  <section aria-label="Sales rollup" class="mb-8" id="sales-rollup-section">
    <h2 class="theme-text-lg theme-weight-semibold mb-3">Revenue rollup</h2>
    <div class="grid gap-4" style="grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr));">
      <div class="theme-bg-surface theme-border border rounded-lg overflow-x-auto">
        <table class="events-table">
          <thead><tr><th>Channel</th><th>Records</th><th>Units</th><th>Gross</th></tr></thead>
          <tbody id="sales-by-channel-tbody">
            <tr><td colspan="4" class="theme-text-muted">·· loading ··</td></tr>
          </tbody>
        </table>
      </div>
      <div class="theme-bg-surface theme-border border rounded-lg overflow-x-auto">
        <table class="events-table">
          <thead><tr><th>Edition</th><th>Channels</th><th>Units</th><th>Gross</th></tr></thead>
          <tbody id="sales-by-edition-tbody">
            <tr><td colspan="4" class="theme-text-muted">·· loading ··</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <section aria-label="Distribution checklist" class="mb-8" id="distribution-section">
    <h2 class="theme-text-lg theme-weight-semibold mb-3">Distribution channels</h2>
    <p class="theme-text-sm theme-text-muted mb-3">
      Per-edition shipped-to-channel checklist. Click a cell to toggle.
      Coverage % below tracks how broadly the catalogue is distributed.
    </p>
    <div class="theme-bg-surface theme-border border rounded-lg overflow-x-auto mb-3">
      <table class="events-table" id="distribution-table">
        <thead>
          <tr id="distribution-thead-row">
            <th>Edition</th>
            <!-- channel <th> cells inserted by JS -->
          </tr>
        </thead>
        <tbody id="distribution-tbody">
          <tr><td class="theme-text-muted">·· loading ··</td></tr>
        </tbody>
      </table>
    </div>
    <div class="theme-text-xs theme-text-muted" id="distribution-coverage-line">·· loading ··</div>
  </section>

  <section aria-label="Recent activity" class="mb-8">
    <h2 class="theme-text-lg theme-weight-semibold mb-3">Recent events</h2>
    <div class="theme-bg-surface theme-border border rounded-lg overflow-x-auto">
      <table class="events-table">
        <thead>
          <tr>
            <th>When</th>
            <th>Kind</th>
            <th>Detail</th>
          </tr>
        </thead>
        <tbody id="events-tbody">
          <tr><td colspan="3" class="theme-text-muted">·· loading ··</td></tr>
        </tbody>
      </table>
    </div>
    <p class="theme-text-xs theme-text-muted mt-3">
      Source: <code class="theme-font-mono">events.jsonl</code> (Δ.15
      append-only event log). Total events: <span id="events-total">·</span>.
    </p>
  </section>
</main>

<script>
function fmtUsd(n) {
  if (typeof n !== 'number') return '$0.00';
  return '$' + n.toFixed(2);
}
function fmtPercent(n) {
  if (typeof n !== 'number') return '0.0%';
  return n.toFixed(1) + '%';
}
function setText(field, value) {
  var el = document.querySelector('[data-field="' + field + '"]');
  if (!el) return;
  el.textContent = value;
}
function renderTiles(tiles) {
  var ed = tiles.editions || {};
  setText('editions-count', String(ed.count || 0).toLocaleString());

  var nc = tiles.notes_corpus || {};
  setText('notes-current', (nc.current || 0).toLocaleString());
  setText('notes-sub', fmtPercent(nc.percent || 0) + ' of ' +
    (nc.target || 0).toLocaleString());

  var ai = tiles.ai_spend_mtd || {};
  setText('ai-total', fmtUsd(ai.total_usd || 0));
  setText('ai-sub', (ai.events || 0).toLocaleString() + ' events this month');

  var pf = tiles.perf_budget_health || {};
  setText('perf-budgets', (pf.budgets_defined || 0).toLocaleString());
  setText('perf-sub', (pf.recent_violations || 0).toLocaleString() + ' violations logged');

  var er = tiles.error_rate || {};
  setText('builds-rate', fmtPercent((er.success_rate || 0) * 100));
  setText('builds-sub', (er.total_terminal || 0).toLocaleString() + ' terminal builds');

  // ε.3 — Sales MTD tile. Primary currency = USD when present, else
  // the first currency encountered. Sub line lists units + record count.
  var sm = tiles.sales_mtd || {};
  var grossByCur = sm.gross_by_currency || {};
  var primaryCurrency = 'USD';
  var primaryAmount = 0;
  if (typeof grossByCur.USD === 'number') {
    primaryAmount = grossByCur.USD;
  } else {
    var firstKey = Object.keys(grossByCur)[0];
    if (firstKey) {
      primaryCurrency = firstKey;
      primaryAmount = grossByCur[firstKey] || 0;
    }
  }
  setText('sales-total', (primaryCurrency === 'USD' ? '$' : (primaryCurrency + ' ')) + primaryAmount.toFixed(2));
  setText('sales-sub',
    (sm.units || 0).toLocaleString() + ' units · ' +
    (sm.records || 0).toLocaleString() + ' rows');
}

function fmtCurrencyBag(bag) {
  // ε.3 — render a {currency: amount} dict as "$12.50 · €4.20" — the
  // primary unit (USD) leads when present so the publisher reads
  // their main number first.
  if (!bag || typeof bag !== 'object') return '';
  var keys = Object.keys(bag);
  if (keys.length === 0) return '$0.00';
  keys.sort(function (a, b) {
    if (a === 'USD') return -1;
    if (b === 'USD') return 1;
    return a.localeCompare(b);
  });
  return keys.map(function (k) {
    var sym = (k === 'USD') ? '$' : (k + ' ');
    return sym + (bag[k] || 0).toFixed(2);
  }).join(' · ');
}

function renderSalesByChannel(byChannel) {
  var tbody = document.getElementById('sales-by-channel-tbody');
  tbody.innerHTML = '';
  var keys = Object.keys(byChannel || {});
  if (keys.length === 0) {
    var tr = document.createElement('tr');
    var td = document.createElement('td');
    td.colSpan = 4;
    td.className = 'theme-text-muted';
    td.textContent = 'No sales records yet. Upload a CSV above.';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }
  keys.sort();
  keys.forEach(function (k) {
    var v = byChannel[k] || {};
    var tr = document.createElement('tr');
    var c = document.createElement('td');
    c.className = 'mono';
    c.textContent = k;
    var r = document.createElement('td');
    r.textContent = (v.records || 0).toLocaleString();
    var u = document.createElement('td');
    u.textContent = (v.units || 0).toLocaleString();
    var g = document.createElement('td');
    g.className = 'mono';
    g.textContent = fmtCurrencyBag(v.gross_by_currency || {});
    tr.appendChild(c); tr.appendChild(r); tr.appendChild(u); tr.appendChild(g);
    tbody.appendChild(tr);
  });
}

function renderSalesByEdition(byEdition) {
  var tbody = document.getElementById('sales-by-edition-tbody');
  tbody.innerHTML = '';
  var keys = Object.keys(byEdition || {});
  if (keys.length === 0) {
    var tr = document.createElement('tr');
    var td = document.createElement('td');
    td.colSpan = 4;
    td.className = 'theme-text-muted';
    td.textContent = 'No sales records yet.';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }
  // Sort by USD gross descending; fall back to first-currency gross.
  keys.sort(function (a, b) {
    var ag = (byEdition[a].gross_by_currency || {}).USD;
    var bg = (byEdition[b].gross_by_currency || {}).USD;
    if (typeof ag !== 'number') ag = Object.values(byEdition[a].gross_by_currency || {})[0] || 0;
    if (typeof bg !== 'number') bg = Object.values(byEdition[b].gross_by_currency || {})[0] || 0;
    return bg - ag;
  });
  keys.forEach(function (k) {
    var v = byEdition[k] || {};
    var tr = document.createElement('tr');
    var ed = document.createElement('td');
    ed.className = 'mono';
    ed.textContent = k;
    var ch = document.createElement('td');
    ch.className = 'mono theme-text-muted';
    ch.textContent = (v.channels || []).join(', ');
    var u = document.createElement('td');
    u.textContent = (v.units || 0).toLocaleString();
    var g = document.createElement('td');
    g.className = 'mono';
    g.textContent = fmtCurrencyBag(v.gross_by_currency || {});
    tr.appendChild(ed); tr.appendChild(ch); tr.appendChild(u); tr.appendChild(g);
    tbody.appendChild(tr);
  });
}

async function loadSalesRollup() {
  try {
    var r = await fetch('/api/sales/rollup');
    var data = await r.json();
    if (data.status !== 'ok') return;
    renderSalesByChannel(data.by_channel || {});
    renderSalesByEdition(data.by_edition || {});
  } catch (e) {
    // Silent — sales rollup is a nice-to-have, not a hard dependency.
  }
}

// ε.6 — distribution checklist render + toggle.
function renderDistribution(rollup) {
  var theadRow = document.getElementById('distribution-thead-row');
  var tbody = document.getElementById('distribution-tbody');
  var coverageLine = document.getElementById('distribution-coverage-line');
  if (!theadRow || !tbody) return;

  // Rebuild the header from the channel list each render so a future
  // channel addition flows through without template churn.
  while (theadRow.children.length > 1) {
    theadRow.removeChild(theadRow.lastChild);
  }
  var channels = rollup.channels || [];
  channels.forEach(function (ch) {
    var th = document.createElement('th');
    th.textContent = ch.label;
    th.title = ch.id;
    theadRow.appendChild(th);
  });

  // Body rows: one per edition.
  tbody.innerHTML = '';
  var editions = rollup.editions || [];
  if (editions.length === 0) {
    var tr = document.createElement('tr');
    var td = document.createElement('td');
    td.colSpan = 1 + channels.length;
    td.className = 'theme-text-muted';
    td.textContent = 'No editions configured.';
    tr.appendChild(td);
    tbody.appendChild(tr);
  } else {
    editions.forEach(function (ed) {
      var tr = document.createElement('tr');
      var name = document.createElement('td');
      name.className = 'mono';
      name.textContent = ed.id;
      name.title = ed.title;
      tr.appendChild(name);
      channels.forEach(function (ch) {
        var cell = (ed.channels || {})[ch.id] || {shipped: false};
        var td = document.createElement('td');
        td.style.cursor = 'pointer';
        td.dataset.edition = ed.id;
        td.dataset.channel = ch.id;
        td.dataset.shipped = cell.shipped ? '1' : '0';
        td.textContent = cell.shipped ? '✓' : '·';
        td.title = cell.shipped
          ? ('Shipped' + (cell.shipped_at ? (' ' + (cell.shipped_at || '').slice(0, 10)) : '') + ' — click to unmark')
          : 'Not shipped — click to mark';
        td.addEventListener('click', onDistributionCellClick);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  }

  // Coverage line: overall + per-channel %.
  var overall = rollup.overall || {};
  var byCh = rollup.by_channel_coverage || {};
  var parts = ['Overall: ' + (overall.percent || 0).toFixed(1) + '% (' +
    (overall.shipped_cells || 0) + ' of ' + (overall.total_cells || 0) + ' cells)'];
  channels.forEach(function (ch) {
    var c = byCh[ch.id] || {};
    parts.push(ch.label + ' ' + (c.percent || 0).toFixed(1) + '%');
  });
  coverageLine.textContent = parts.join(' · ');
}

async function onDistributionCellClick(e) {
  var td = e.currentTarget;
  var editionId = td.dataset.edition;
  var channelId = td.dataset.channel;
  var wasShipped = td.dataset.shipped === '1';
  td.style.opacity = '0.5';
  try {
    var resp, data;
    if (wasShipped) {
      resp = await fetch('/api/distribution/' + encodeURIComponent(editionId) +
        '/' + encodeURIComponent(channelId), {method: 'DELETE'});
    } else {
      resp = await fetch('/api/distribution/' + encodeURIComponent(editionId), {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({channel: channelId}),
      });
    }
    data = await resp.json();
    if (resp.ok && data.ok) {
      if (window.ebibleToast) {
        window.ebibleToast(
          (wasShipped ? 'Unmarked ' : 'Marked ') + editionId + ' / ' + channelId,
          'success'
        );
      }
      loadDistribution();
    } else {
      var msg = (data && (data.message || data.error)) || ('HTTP ' + resp.status);
      if (window.ebibleToast) window.ebibleToast('Failed: ' + msg, 'error');
    }
  } catch (err) {
    if (window.ebibleToast) window.ebibleToast('Network error: ' + err.message, 'error');
  } finally {
    td.style.opacity = '1.0';
  }
}

async function loadDistribution() {
  try {
    var r = await fetch('/api/distribution');
    var data = await r.json();
    if (data.status !== 'ok') return;
    renderDistribution(data.rollup || {});
  } catch (e) {
    // Silent — checklist is a nice-to-have, not a hard dependency.
  }
}
function renderEvents(events) {
  var tbody = document.getElementById('events-tbody');
  tbody.innerHTML = '';
  if (!events || events.length === 0) {
    var row = document.createElement('tr');
    var cell = document.createElement('td');
    cell.colSpan = 3;
    cell.className = 'theme-text-muted';
    cell.textContent = 'No events yet.';
    row.appendChild(cell);
    tbody.appendChild(row);
    return;
  }
  // Newest first for display (ε.1's recent_events() returns newest-last).
  var rows = events.slice().reverse();
  rows.forEach(function (ev) {
    var tr = document.createElement('tr');
    var tdWhen = document.createElement('td');
    tdWhen.className = 'mono theme-text-muted';
    tdWhen.textContent = (ev.ts || '').slice(0, 19).replace('T', ' ');
    var tdKind = document.createElement('td');
    tdKind.className = 'mono';
    tdKind.textContent = ev.kind || '';
    var tdDetail = document.createElement('td');
    tdDetail.className = 'theme-text-muted';
    // Build a one-line detail: every field except ts/kind, joined
    // with ' · '. Insert via textContent so any field value stays
    // XSS-safe by construction.
    var parts = [];
    Object.keys(ev).forEach(function (k) {
      if (k === 'ts' || k === 'kind') return;
      parts.push(k + '=' + JSON.stringify(ev[k]));
    });
    tdDetail.textContent = parts.join(' · ');
    tr.appendChild(tdWhen);
    tr.appendChild(tdKind);
    tr.appendChild(tdDetail);
    tbody.appendChild(tr);
  });
}
async function loadDashboard() {
  try {
    var r = await fetch('/api/exec');
    var data = await r.json();
    if (data.status !== 'ok') {
      if (window.ebibleToast) {
        window.ebibleToast('Dashboard load failed: ' + (data.message || r.status), 'error');
      }
      return;
    }
    renderTiles(data.tiles || {});
    renderEvents(data.recent_events || []);
    document.getElementById('events-total').textContent =
      (data.events_total || 0).toLocaleString();
  } catch (e) {
    if (window.ebibleToast) {
      window.ebibleToast('Network error: ' + e.message, 'error');
    }
  }
}
loadDashboard();
loadSalesRollup();
loadDistribution();

// ε.3 — sales import form handler. Submits multipart to
// /api/sales/import/<channel>; toasts on success/failure; refreshes
// the dashboard tile + rollup tables after a successful import.
(function () {
  var form = document.getElementById('sales-import-form');
  if (!form) return;
  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    var channelEl = document.getElementById('sales-channel');
    var fileEl = document.getElementById('sales-file');
    var statusEl = document.getElementById('sales-status');
    var submitEl = document.getElementById('sales-submit');
    if (!fileEl.files || fileEl.files.length === 0) {
      if (window.ebibleToast) window.ebibleToast('Choose a CSV file first', 'error');
      return;
    }
    var channel = channelEl.value;
    var file = fileEl.files[0];
    var fd = new FormData();
    fd.append('file', file, file.name);
    submitEl.disabled = true;
    statusEl.textContent = 'Uploading ' + file.name + ' ...';
    try {
      var resp = await fetch('/api/sales/import/' + encodeURIComponent(channel), {
        method: 'POST',
        body: fd,
      });
      var data = await resp.json();
      if (resp.ok && data.status === 'ok') {
        statusEl.textContent = data.message || 'Imported.';
        if (window.ebibleToast) {
          window.ebibleToast(data.message || 'Imported ' + (data.imported || 0) + ' rows', 'success');
        }
        fileEl.value = '';
        loadDashboard();
        loadSalesRollup();
      } else {
        var msg = (data && (data.message || data.error)) || ('HTTP ' + resp.status);
        statusEl.textContent = 'Failed: ' + msg;
        if (window.ebibleToast) window.ebibleToast('Import failed: ' + msg, 'error');
      }
    } catch (err) {
      statusEl.textContent = 'Network error: ' + err.message;
      if (window.ebibleToast) window.ebibleToast('Network error: ' + err.message, 'error');
    } finally {
      submitEl.disabled = false;
    }
  });
})();

// Corpus-progress widget (mirrors the pattern in every other console).
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
</script>

</body>
</html>
"""


# ε.2: design-system substitution (cross-link nav + theme markers).
EXEC_HTML = apply_design_system(EXEC_HTML, "/exec")

"""ε.2 — /exec dashboard MVP template.

Surfaces five executive KPI tiles + a recent-activity table, rendered
from `api_exec_dashboard()` on initial page load. The tiles are:

    1. Editions count           — config.load_editions()
    2. Notes corpus             — api_attribution_audit().counts.total
                                  (with target + progress %)
    3. AI spend MTD             — event log `ai_*` events × `cost`
    4. Perf budget health       — perf_budgets.BUDGETS + violations
    5. Error rate               — build outcomes success_rate

Composes the full ζ foundation (theme tokens + dark mode + icons +
toasts + cmd palette). All tile values insert via `textContent` so
any future event-log payload with exotic characters stays XSS-safe.

Foundation for ε.3 (sales import → tile 6 sales MTD), ε.4 (cost-per-
edition rollup expands tile 3), ε.5 (quarterly auto-report composes
this payload into PDF), and ε.6 (channel checklist surfaces in a
companion section).
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

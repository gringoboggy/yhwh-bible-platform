"""ε.2 — /exec dashboard MVP (2026-05-11).

Composes the existing surfaces into the five executive KPI tiles the
publisher needs at-a-glance:

    1. Editions count          — config.load_editions()
    2. Notes corpus            — api_attribution_audit().counts.total
    3. AI spend MTD            — event log filter on `ai_*` kinds + `cost`
    4. Perf budget health      — scripts.perf_budgets.BUDGETS + violation scan
    5. Error rate              — metrics.summary_kpis().builds.success_rate

Per CLAUDE_PROJECT_RULES §9 "Compose, don't recompute" — every tile
sources from an existing endpoint or module so there is exactly one
walk through the corpus / event log per dashboard render.

Public API:
    api_exec_dashboard()  → dict (the 5-tile payload + recent events)

Response shape (success):
    {
      "status": "ok",
      "tiles": {
        "editions": {"count": int},
        "notes_corpus": {"current": int, "target": int, "percent": float},
        "ai_spend_mtd": {"events": int, "total_usd": float,
                         "window_start_iso": str},
        "perf_budget_health": {"budgets_defined": int,
                               "recent_violations": int},
        "error_rate": {"success_rate": float, "failure_count": int,
                       "total_terminal": int},
      },
      "events_total": int,
      "recent_events": list[dict],   # last 10
    }

The endpoint is read-only and idempotent. Future ε.* phases extend
this:
    ε.3 sales import     — adds a `sales_mtd` tile
    ε.4 cost rollup      — extends `ai_spend_mtd` to per-edition rows
    ε.5 quarterly report — composes this payload into a PDF
"""

from __future__ import annotations

from datetime import datetime, timezone


def _month_start_iso(now: datetime | None = None) -> str:
    """Return the ISO-8601 timestamp for 00:00:00 UTC on the first day
    of the current month. Injectable `now` for tests."""
    n = now or datetime.now(timezone.utc)
    return n.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()


def _ai_spend_mtd(window_start_iso: str) -> dict:
    """Sum AI cost across events since `window_start_iso`.

    Matches any event whose `kind` starts with `ai_` (e.g. `ai_xref_run`,
    `ai_cover_generate`, `ai_spend`) and includes a numeric `cost` field
    (USD). Events without a cost field are still counted toward the
    `events` total — they record that AI work happened, even if the
    cost was logged elsewhere.
    """
    from scripts.core import metrics

    total = 0.0
    events = 0
    for ev in metrics.iter_events_since(window_start_iso):
        kind = str(ev.get("kind", ""))
        if not kind.startswith("ai_"):
            continue
        events += 1
        cost = ev.get("cost")
        if isinstance(cost, (int, float)):
            total += float(cost)
    return {
        "events": events,
        "total_usd": round(total, 4),
        "window_start_iso": window_start_iso,
    }


def _perf_budget_health() -> dict:
    """Number of perf budgets defined + recent violations from the
    event log.

    The violation count looks for kind == "perf_violation" across the
    whole log. A future ε.2.x can scope to a rolling window; for MVP
    the absolute count is honest signal.
    """
    from scripts import perf_budgets
    from scripts.core import event_log

    budgets = len(perf_budgets.BUDGETS)
    violations = 0
    for ev in event_log.iter_events():
        if ev.get("kind") == "perf_violation":
            violations += 1
    return {
        "budgets_defined": budgets,
        "recent_violations": violations,
    }


def api_exec_dashboard(*, now: datetime | None = None) -> dict:
    """Render the five executive KPI tiles + recent activity.

    Pure function. Composes existing endpoints and modules; no new
    file walks. Safe to call on every page render (the underlying
    aggregators are cached or single-pass-streamed).

    Args:
        now: Inject the current time for deterministic tests. Production
             callers leave this unset.
    """
    # Lazy imports so the api module stays cheap to import in
    # environments where the corpus / event log isn't populated.
    from scripts import web
    from scripts.core import config, metrics

    # Tile 1 — editions count
    editions = config.load_editions()
    tile_editions = {"count": len(editions)}

    # Tile 2 — notes corpus. Compose existing cached aggregator.
    audit = web.api_attribution_audit()
    corpus_total = int(audit.get("counts", {}).get("total", 0))
    target = web.CORPUS_TARGET
    percent = (corpus_total / target * 100.0) if target > 0 else 0.0
    tile_notes_corpus = {
        "current": corpus_total,
        "target": target,
        "percent": round(percent, 2),
    }

    # Tile 3 — AI spend MTD
    window_start = _month_start_iso(now)
    tile_ai_spend = _ai_spend_mtd(window_start)

    # Tile 4 — perf budget health
    tile_perf = _perf_budget_health()

    # Tile 5 — error rate from build outcomes (the primary failure
    # signal the publisher cares about).
    kpis = metrics.summary_kpis()
    builds = kpis.get("builds", {})
    complete = int(builds.get("complete", 0))
    failure = int(builds.get("failure", 0))
    total_terminal = complete + failure
    tile_error_rate = {
        "success_rate": float(builds.get("success_rate", 0.0)),
        "failure_count": failure,
        "total_terminal": total_terminal,
    }

    return {
        "status": "ok",
        "tiles": {
            "editions": tile_editions,
            "notes_corpus": tile_notes_corpus,
            "ai_spend_mtd": tile_ai_spend,
            "perf_budget_health": tile_perf,
            "error_rate": tile_error_rate,
        },
        "events_total": int(kpis.get("events_total", 0)),
        "recent_events": metrics.recent_events(10),
    }

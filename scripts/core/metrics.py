"""ε.1 — metrics collector (2026-05-11).

Read-side rollup queries over `scripts.core.event_log`. The /exec
dashboard (ε.2), quarterly auto-report (ε.5), and any future
analytics surface compose these. Lightweight by design — no
external metrics service, no in-process state, just iter_events()
+ Python dicts.

**Public API**:
    events_total()                — int — count of all events
    events_by_kind()              — dict[kind, count]
    builds_by_outcome()           — dict["start"/"complete"/"failure", count]
    builds_by_edition(limit=10)   — list[(edition_id, count)] — top by build_complete
    recent_events(n=20)           — list of last N events (newest last)
    summary_kpis()                — dict[str, int|float] — composed top metrics
    iter_events_since(iso_ts)     — generator of events with ts >= iso_ts

Everything composes `event_log.iter_events()` so single-pass
streaming. No N+1 or quadratic patterns.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterator

from . import event_log


def events_total() -> int:
    """Total parseable events in the log."""
    return event_log.count()


def events_by_kind() -> dict[str, int]:
    """{kind: count} across the entire log. Missing-kind events are
    counted under empty string (defensive — emit() validates kind so
    this should never happen in practice)."""
    counts: Counter[str] = Counter()
    for event in event_log.iter_events():
        counts[str(event.get("kind", ""))] += 1
    return dict(counts)


def builds_by_outcome() -> dict[str, int]:
    """Aggregate build_* events by outcome.

    Returns:
        {"start": int, "complete": int, "failure": int} — buckets
        derived from `build_start` / `build_complete` / `build_failure`
        events. Other event kinds are ignored.
    """
    out = {"start": 0, "complete": 0, "failure": 0}
    for event in event_log.iter_events():
        k = str(event.get("kind", ""))
        if k == "build_start":
            out["start"] += 1
        elif k == "build_complete":
            out["complete"] += 1
        elif k == "build_failure":
            out["failure"] += 1
    return out


def builds_by_edition(limit: int = 10) -> list[tuple[str, int]]:
    """Top editions by `build_complete` count, newest-first by tie.

    Returns:
        list[(edition_id, count)] — sorted descending by count, capped
        at `limit`. Empty list if no build_complete events.
    """
    counts: Counter[str] = Counter()
    for event in event_log.iter_events():
        if event.get("kind") != "build_complete":
            continue
        ed = event.get("edition_id")
        if not ed:
            continue
        counts[str(ed)] += 1
    return counts.most_common(max(1, int(limit)))


def recent_events(n: int = 20) -> list[dict]:
    """Last `n` events. Pass-through to `event_log.tail()`."""
    return event_log.tail(n)


def iter_events_since(iso_ts: str) -> Iterator[dict]:
    """Yield events with `ts >= iso_ts` (string comparison works
    because ISO-8601 timestamps lex-sort identically to chronological
    order)."""
    cutoff = str(iso_ts)
    for event in event_log.iter_events():
        ts = event.get("ts", "")
        if isinstance(ts, str) and ts >= cutoff:
            yield event


def summary_kpis() -> dict:
    """One-call rollup of the metrics ε.2's dashboard needs.

    Composes the per-metric functions above. Returns a stable shape
    the dashboard can render even when some buckets are empty — every
    consumer should treat missing keys defensively.

    Shape:
        {
          "events_total": int,
          "events_by_kind_top_5": list[(kind, count)],
          "builds": {"start": int, "complete": int, "failure": int,
                     "success_rate": float},  # 0.0 if no completions
          "top_built_editions": list[(edition_id, count)],
          "recent_events": list[dict] (last 5)
        }
    """
    by_kind = events_by_kind()
    top_kinds = Counter(by_kind).most_common(5)
    builds = builds_by_outcome()
    total_terminal = builds["complete"] + builds["failure"]
    success_rate = (builds["complete"] / total_terminal) if total_terminal else 0.0
    return {
        "events_total": events_total(),
        "events_by_kind_top_5": top_kinds,
        "builds": {
            "start": builds["start"],
            "complete": builds["complete"],
            "failure": builds["failure"],
            "success_rate": round(success_rate, 4),
        },
        "top_built_editions": builds_by_edition(5),
        "recent_events": recent_events(5),
    }

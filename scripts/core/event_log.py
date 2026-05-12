"""Δ.15 — append-only event log (2026-05-11).

The lightweight foundation that ε.1 (metrics collector), ε.2
(/exec dashboard), ε.3 (sales import), ε.5 (quarterly auto-report),
and the eventual ε.* analytics surface compose against.

**Why append-only JSON Lines**:
- Trivially streamable and tail-able with standard tools.
- No schema migration cost: readers tolerate unknown fields,
  writers add fields freely.
- ~200KB/month at expected usage; no rotation needed for years.
- Greppable with the standard CLI toolchain.

**File location**: `paths.user_data_root() / 'events.jsonl'`. The
write path is created lazily on first `emit()`.

**Event shape**:

    {"ts": "2026-05-11T18:30:00.123456+00:00",
     "kind": "edition_save",
     "edition_id": "catholic-study",
     "actor": "publisher",
     ...}

`ts` and `kind` are always present. Everything else is `**fields`
the caller passes. Readers should tolerate unknown fields so
emitters can add new ones freely.

**Concurrency**: single-process append. Multi-process locking is
deferred to a future Δ.15.x. The current project is a single-
server deployment so locks would be premature optimization.

**Future ε.* extensions** (NOT in this module):
- ε.1 metrics collector: composes `iter_events()` → KPI rollups.
- ε.2 /exec dashboard: renders the rollups as tiles.
- ε.5 quarterly auto-report: aggregates events into PDF.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


def _event_log_path() -> Path:
    """Return the canonical events.jsonl path. Lazy import of paths
    so this module stays importable in environments where
    `paths.user_data_root()` doesn't resolve (tests setting
    `EBIBLE_USER_DATA_ROOT`)."""
    from . import paths

    return paths.user_data_root() / "events.jsonl"


def _now_iso() -> str:
    """ISO-8601 UTC timestamp with microsecond precision. Pin the
    format so downstream parsers (ε.1+) can rely on it."""
    return datetime.now(timezone.utc).isoformat()


def emit(kind: str, /, **fields) -> dict:
    """Write one event to the append-only log. Returns the recorded
    dict so callers can log/inspect/test what was written.

    Args:
        kind: event-type slug (snake_case convention; e.g.,
              "edition_save", "build_export", "ai_xref_run").
              Required and must be non-empty.
        **fields: arbitrary additional fields stored with the event.
                  Common ones: actor, edition_id, ref, payload.
                  Fields are passed through to `json.dumps` so they
                  must be JSON-serializable.

    Returns:
        The recorded dict (including the auto-generated `ts`).

    Raises:
        ValueError: kind is empty or not a str.
        TypeError: a passed field isn't JSON-serializable.
    """
    if not isinstance(kind, str) or not kind.strip():
        raise ValueError(f"kind must be a non-empty string; got {kind!r}")
    record = {"ts": _now_iso(), "kind": kind.strip()}
    for key, value in fields.items():
        # `ts` and `kind` are reserved — caller-supplied versions
        # are ignored (silently dropped to avoid surprising
        # overrides). Doc the contract; future versions can
        # tighten to a raise.
        if key in ("ts", "kind"):
            continue
        record[key] = value

    path = _event_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # buffering=1 is line-buffered, which flushes after every \n.
    # Append-only mode + line buffering = each emit lands as a
    # standalone line that grep / tail can consume immediately.
    with open(path, "a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def iter_events() -> Iterator[dict]:
    """Yield every event in the log, in write order. Skips any line
    that fails to parse (e.g., a partial write that an emergency
    shutdown left behind) rather than raising — readers must
    tolerate one bad line without losing the whole log.

    Returns an empty iterator if the log file doesn't exist yet.
    """
    path = _event_log_path()
    if not path.is_file():
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # Tolerate one bad line. ε.1's metrics rollups
                # will count parse failures as a separate KPI
                # if it cares.
                continue


def tail(n: int) -> list[dict]:
    """Return the last `n` events as a list. Newest last (matches
    the file's append order).

    `n` is clamped to a non-negative int; n=0 returns `[]`.
    """
    n_clamped = max(0, int(n))
    if n_clamped == 0:
        return []
    # Linear scan is fine for ~10K+ events; if the log grows past
    # ~1M events a future Δ.15.x can add a tail-index sidecar.
    events = list(iter_events())
    return events[-n_clamped:]


def count() -> int:
    """Total number of parseable events in the log. Excludes any
    lines that failed to parse — matches `iter_events()`'s view."""
    return sum(1 for _ in iter_events())

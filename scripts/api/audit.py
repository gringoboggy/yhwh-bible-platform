"""ω.35-B.7 — audit-log read endpoint, extracted from scripts/web.py.

One handler: `api_audit_log` (Phase ξ.13). Surfaces the NDJSON ledger
written by `audit_log.audit_endpoint` as a JSON envelope the
`/audit-log` console renders. Pure function; no caching — the file is
append-only and small enough for a fresh read.

Backward compatibility: re-exported from `scripts.web` so the route
table lambda (in `_QS_REGEX_GET_ROUTES`) and any test that imports
`scripts.web.api_audit_log` keeps working.
"""

from __future__ import annotations

from pathlib import Path

from scripts.core import audit_log


def api_audit_log(*, n: int = 100, base_dir: Path | None = None) -> dict:
    """Return the most recent audit-log entries.

    Composes `audit_log.read_recent` and wraps in the project's
    standard envelope shape. `n` is clamped to [1, 1000] to bound
    response size; `base_dir` is for tests (production reads
    `<user_data>/audit/`).
    """
    try:
        n_int = int(n)
    except (TypeError, ValueError):
        n_int = 100
    n_int = max(1, min(1000, n_int))
    entries = audit_log.read_recent(n=n_int, base_dir=base_dir)
    return {
        "status": "ok",
        "count": len(entries),
        "limit": n_int,
        "entries": entries,
    }

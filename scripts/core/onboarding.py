"""Wave 4 W4.3 — server-side onboarding / first-run state.

Tracks whether the user has completed the first-run welcome flow, persisted as
a small JSON marker in the frozen-aware writable data root (``paths.state_dir()``)
so it survives restarts and is a single source of truth across browser shells
(not per-browser localStorage).

Distinct from ``launcher.should_run_first_run_migration`` — that copies bundled
``content/`` to the user-data dir on first frozen launch (data migration); this
records whether the USER has seen the welcome flow (UX state).

Stdlib + ``notes_io.atomic_write`` only, per CLAUDE_PROJECT_RULES §7.1/§10.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.core import notes_io, paths


def _default_path() -> Path:
    return paths.state_dir() / "onboarding.json"


def _read(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def onboarding_state(*, path: Path | None = None) -> dict:
    """Return ``{"first_run": bool, "onboarded_at": iso|None}``.

    A missing or unreadable marker is treated as a fresh install (first_run
    True) so a corrupt file re-shows the welcome flow rather than hiding it."""
    p = path or _default_path()
    onboarded_at = _read(p).get("onboarded_at")
    return {"first_run": not bool(onboarded_at), "onboarded_at": onboarded_at}


def mark_onboarded(*, path: Path | None = None) -> dict:
    """Record that the user finished onboarding and return the new state.

    Idempotent: the first onboarding moment is preserved on repeat calls."""
    p = path or _default_path()
    data = _read(p)
    if not data.get("onboarded_at"):
        data["onboarded_at"] = datetime.now(timezone.utc).isoformat()
        p.parent.mkdir(parents=True, exist_ok=True)
        notes_io.atomic_write(p, json.dumps(data, indent=2) + "\n")
    return onboarding_state(path=p)

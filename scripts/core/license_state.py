"""ξ.26 — per-edition license-key state (2026-05-12).

Sparse JSON at `content/licenses.json` storing the active license
string per edition. Mirrors `distribution.py` / `press_kit.py` /
`auth.py` persistence discipline:

- atomic write via `notes_io.atomic_write` + `ensure_backup` backup
- schema-versioned (currently v1)
- whitelist on save (unknown fields dropped — stale-client defense)
- empty-state default on missing / malformed file

**Schema (v1)**:

    {
      "schema_version": 1,
      "editions": {
        "<edition_id>": {
          "key": "LK1:<edition>:<expires>:<issued>:<sig>",
          "stored_at": "<iso-8601 utc>"
        }
      }
    }

When an edition has no entry → no license set → the soft-enforcement
banner shows "license missing" for that edition.

**Public API**:
    SCHEMA_VERSION                              current schema version
    ENTRY_FIELDS                                whitelisted entry keys
    load_licenses()                             dict (full state)
    save_licenses(state)                        atomic write
    set_license(edition_id, key)                write helper
    remove_license(edition_id)                  write helper
    get_license(edition_id, state=None)         license str or None
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import notes_io


SCHEMA_VERSION = 1
ENTRY_FIELDS: tuple[str, ...] = ("key", "stored_at")


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _licenses_path() -> Path:
    """Canonical state-file path. Function (not constant) so tests can
    monkeypatch via a single attribute — mirrors event_log + auth."""
    return _REPO_ROOT / "content" / "licenses.json"


def _now_iso() -> str:
    """ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _empty_state() -> dict:
    return {"schema_version": SCHEMA_VERSION, "editions": {}}


def load_licenses() -> dict:
    """Load the license state. Empty-state default on missing/malformed file."""
    path = _licenses_path()
    if not path.is_file():
        return _empty_state()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return _empty_state()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return _empty_state()
    if not isinstance(data, dict):
        return _empty_state()
    if "schema_version" not in data:
        data["schema_version"] = SCHEMA_VERSION
    if "editions" not in data or not isinstance(data["editions"], dict):
        data["editions"] = {}
    return data


def save_licenses(state: dict) -> Path:
    """Persist `state` atomically. Whitelist-filters entry fields."""
    cleaned: dict = {"schema_version": SCHEMA_VERSION, "editions": {}}
    editions = state.get("editions", {}) if isinstance(state, dict) else {}
    if isinstance(editions, dict):
        for ed_id, entry in editions.items():
            if not isinstance(entry, dict):
                continue
            ed_id_str = str(ed_id)
            cleaned_entry = {k: str(entry[k]) for k in ENTRY_FIELDS if k in entry}
            if cleaned_entry.get("key"):
                cleaned["editions"][ed_id_str] = cleaned_entry

    path = _licenses_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        notes_io.ensure_backup(path)
    text = json.dumps(cleaned, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    notes_io.atomic_write(path, text)
    return path


def set_license(edition_id: str, key: str) -> dict:
    """Set the license string for `edition_id`. Returns the entry as
    written. Raises ValueError on empty inputs."""
    edition_id = (edition_id or "").strip()
    if not edition_id:
        raise ValueError("edition_id must be non-empty")
    key = (key or "").strip()
    if not key:
        raise ValueError("key must be non-empty")
    state = load_licenses()
    editions = state.setdefault("editions", {})
    entry = {"key": key, "stored_at": _now_iso()}
    editions[edition_id] = entry
    save_licenses(state)
    return entry


def remove_license(edition_id: str) -> bool:
    """Remove the license entry for `edition_id`. Returns True iff
    something was removed (idempotent — already-absent returns False)."""
    state = load_licenses()
    editions = state.get("editions", {}) if isinstance(state, dict) else {}
    if edition_id not in editions:
        return False
    del editions[edition_id]
    save_licenses(state)
    return True


def get_license(edition_id: str, state: Optional[dict] = None) -> Optional[str]:
    """Return the stored license string for `edition_id` or None."""
    s = state if state is not None else load_licenses()
    eds = s.get("editions", {}) if isinstance(s, dict) else {}
    entry = eds.get(edition_id, {}) if isinstance(eds, dict) else {}
    key = entry.get("key") if isinstance(entry, dict) else None
    return str(key) if key else None

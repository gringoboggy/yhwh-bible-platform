"""ξ.21 — admin-auth state persistence (2026-05-12).

Sparse JSON at `content/auth.json` storing 2FA enrollment state.
Mirrors `distribution.py` and `press_kit.py` persistence
discipline exactly:

- atomic write via `notes_io.atomic_write` + `ensure_backup` backup
- schema-versioned (currently v1)
- whitelist on save (unknown fields dropped — stale-client defense)
- empty-state default on missing / malformed file

**Schema (v1)**:

    {
      "schema_version": 1,
      "totp": {
        "enabled": bool,
        "secret": "<base32>",
        "enrolled_at": "<iso-8601 utc>",
        "issuer": "YHWH Bible",
        "label": "admin@ebible"
      }
    }

When `totp` is absent → 2FA is not configured (the default).

**Public API**:
    SCHEMA_VERSION                  current schema version
    DEFAULT_ISSUER                  "YHWH Bible"
    DEFAULT_LABEL                   "admin@ebible"
    load_auth()                     dict (full state)
    save_auth(state)                atomic write
    is_totp_enabled(state=None)     bool
    get_totp_secret(state=None)     base32 string or None
    enroll_totp(secret, *, issuer,
                label, now=None)    write helper
    disable_totp()                  remove the totp block

Foundation for ξ.21.x — recovery codes (single-use backup codes),
QR-code SVG rendering (currently the otpauth URI is shown as text
for the publisher to paste into their app).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import notes_io


SCHEMA_VERSION = 1
DEFAULT_ISSUER = "YHWH Bible"
DEFAULT_LABEL = "admin@ebible"

TOTP_FIELDS: tuple[str, ...] = ("enabled", "secret", "enrolled_at", "issuer", "label")


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _auth_path() -> Path:
    """Canonical state-file path. Function (not constant) so tests can
    monkeypatch via a single attribute — mirrors event_log + distribution."""
    return _REPO_ROOT / "content" / "auth.json"


def _now_iso() -> str:
    """ISO-8601 UTC timestamp — same format as event_log + distribution."""
    return datetime.now(timezone.utc).isoformat()


def _empty_state() -> dict:
    return {"schema_version": SCHEMA_VERSION}


def load_auth() -> dict:
    """Load the auth state. Empty-state default on missing / malformed file."""
    path = _auth_path()
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
    return data


def save_auth(state: dict) -> Path:
    """Persist `state` atomically. Whitelist-filters the totp block
    so stale clients can't sneak unknown keys onto disk."""
    cleaned: dict = {"schema_version": SCHEMA_VERSION}
    totp = state.get("totp") if isinstance(state, dict) else None
    if isinstance(totp, dict):
        cleaned_totp = {k: totp[k] for k in TOTP_FIELDS if k in totp}
        if cleaned_totp:
            cleaned["totp"] = cleaned_totp

    path = _auth_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        notes_io.ensure_backup(path)
    text = json.dumps(cleaned, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    notes_io.atomic_write(path, text)
    return path


def is_totp_enabled(state: Optional[dict] = None) -> bool:
    """True iff the auth state has an enabled TOTP block with a
    non-empty secret. `state` injectable for tests; production callers
    leave it None and the state is loaded fresh."""
    s = state if state is not None else load_auth()
    totp = s.get("totp", {}) if isinstance(s, dict) else {}
    if not isinstance(totp, dict):
        return False
    return bool(totp.get("enabled")) and bool(totp.get("secret", "").strip())


def get_totp_secret(state: Optional[dict] = None) -> Optional[str]:
    """Return the enrolled TOTP secret (base32 string) or None if
    not enabled. `state` injectable for tests."""
    if not is_totp_enabled(state):
        return None
    s = state if state is not None else load_auth()
    return str(s["totp"]["secret"])


def enroll_totp(
    secret: str,
    *,
    issuer: str = DEFAULT_ISSUER,
    label: str = DEFAULT_LABEL,
    now: Optional[datetime] = None,
) -> dict:
    """Persist the TOTP enrollment. Loads → mutates → saves. Returns
    the totp block as written.

    `now` injectable for tests; production callers leave it None and
    `_now_iso()` is used.
    """
    if not secret or not secret.strip():
        raise ValueError("secret must be non-empty")
    state = load_auth()
    enrolled_at = (now or datetime.now(timezone.utc)).isoformat()
    state["totp"] = {
        "enabled": True,
        "secret": secret.strip(),
        "enrolled_at": enrolled_at,
        "issuer": issuer,
        "label": label,
    }
    save_auth(state)
    return state["totp"]


def disable_totp() -> bool:
    """Remove the TOTP block. Returns True iff something was removed
    (idempotent — already-disabled returns False)."""
    state = load_auth()
    if "totp" not in state:
        return False
    state.pop("totp", None)
    save_auth(state)
    return True

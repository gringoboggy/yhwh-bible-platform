"""ε.7 — press kit API handlers (2026-05-11).

Two JSON endpoints + a binary-download route:
- `api_press_kit_get(edition_id)` — GET; returns per-edition blurbs
  + a `cover_present` flag so the UI can warn the publisher when
  the press-kit ZIP will be missing a cover.
- `api_press_kit_save(edition_id, payload)` — PUT; merge-updates
  the per-edition blurbs. Enforces per-field length limits via the
  core module's `FIELD_LIMITS` (size violations → HTTP 413).
- `build_press_kit_zip(edition_id)` — returns `(filename, bytes)` for
  the binary download wired into do_GET (the route-table dispatchers
  all expect JSON-shaped responses, so the bytes path stays in
  web.py's legacy cascade).

Edition existence is validated against `config.load_editions()` for
both save + download (the publisher can't accidentally build a
press kit for a non-existent edition).
"""

from __future__ import annotations

from scripts.core import audit_log


def _editions_index() -> dict:
    """{id: edition_dict}. Delegates to the shared config.editions_by_id()."""
    from scripts.core import config

    return config.editions_by_id()


def api_press_kit_get(edition_id: str) -> dict:
    """Per-edition blurbs + cover-presence flag.

    Returns `{status, edition_id, blurbs, cover_present, limits}`.
    `limits` lets the UI render field-length counters without
    duplicating the core constants.
    """
    from scripts.core import press_kit

    state = press_kit.load_press_kit()
    blurbs = press_kit.get_blurbs(state, edition_id)
    editions_idx = _editions_index()
    edition = editions_idx.get(edition_id)
    cover_present = bool(edition and press_kit.resolve_cover_path(edition))
    return {
        "status": "ok",
        "edition_id": edition_id,
        "edition_known": edition is not None,
        "blurbs": blurbs,
        "cover_present": cover_present,
        "limits": dict(press_kit.FIELD_LIMITS),
        "fields": list(press_kit.PRESS_KIT_FIELDS),
        "schema_version": state.get("schema_version", press_kit.SCHEMA_VERSION),
    }


@audit_log.audit_endpoint(action="press_kit_save")
def api_press_kit_save(edition_id: str, payload: dict | None) -> dict:
    """Merge-update the blurbs for one edition.

    Payload fields (all optional — pass only what you're changing):
        blurb_150           150-word blurb plain text
        blurb_500           500-word description plain text
        sample_chapter_html sample chapter HTML

    Empty string clears a field. Length violations return HTTP 413
    via the standard `{status: error, code, http, message}` envelope.
    """
    from scripts.core import press_kit

    payload = payload or {}
    if edition_id not in _editions_index():
        return {
            "ok": False,
            "error": "unknown_edition",
            "message": f"unknown edition: {edition_id!r}",
        }
    try:
        entry = press_kit.set_blurbs(
            edition_id,
            blurb_150=payload.get("blurb_150"),
            blurb_500=payload.get("blurb_500"),
            sample_chapter_html=payload.get("sample_chapter_html"),
        )
    except ValueError as e:
        # Field-length violation. Use a distinct error envelope so the
        # client can show the per-field error in the right place.
        return {
            "status": "error",
            "code": "field_too_long",
            "http": 413,
            "message": str(e),
        }
    return {
        "ok": True,
        "edition_id": edition_id,
        "blurbs": {k: entry.get(k, "") for k in press_kit.PRESS_KIT_FIELDS},
    }


def build_press_kit_zip(edition_id: str) -> tuple[str, bytes] | dict:
    """Build the press-kit ZIP. Returns `(filename, bytes)` on
    success or an error envelope dict on failure.

    The web.py legacy route inspects the return type — tuple goes to
    `_send_zip`, dict goes to the standard JSON error envelope. This
    asymmetry is the price of returning binary from a stdlib
    BaseHTTPRequestHandler-based server; the alternative is a much
    larger refactor of the dispatcher tables.
    """
    from scripts.core import press_kit

    edition = _editions_index().get(edition_id)
    if edition is None:
        return {
            "status": "error",
            "code": "unknown_edition",
            "http": 404,
            "message": f"unknown edition: {edition_id!r}",
        }
    blurbs = press_kit.get_blurbs(press_kit.load_press_kit(), edition_id)
    body = press_kit.build_zip(edition, blurbs)
    filename = f"press-kit-{edition_id}.zip"
    return (filename, body)

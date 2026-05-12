"""ε.6 — distribution channel checklist API (2026-05-11).

Three endpoints for the publisher's /exec distribution section:
- `api_distribution_list()` — GET; rollup payload (per-edition grid +
  per-channel coverage + overall coverage). Read-only.
- `api_distribution_mark(edition_id, payload)` — PUT; mark
  `edition_id × channel_id` as shipped with optional url / isbn /
  notes / shipped_at. Audit-logged.
- `api_distribution_unmark(edition_id, channel_id)` — DELETE; remove
  the entry. Idempotent (already-absent returns ok). Audit-logged.

Edition existence is validated against `config.load_editions()` — the
publisher can't mark a non-existent edition as shipped (catches typos).
Channel validity is enforced by the core module's `DISTRIBUTION_CHANNELS`
tuple.
"""

from __future__ import annotations

from scripts.core import audit_log


def api_distribution_list() -> dict:
    """Return the distribution rollup for /exec.

    Composes `distribution.load_distribution()` + the canonical
    edition list. Always returns one row per shipped edition so the
    UI can render a complete grid (rows of "not shipped" cells for
    editions that haven't gone anywhere yet).
    """
    from scripts.core import config, distribution

    state = distribution.load_distribution()
    editions = config.load_editions()
    return {
        "status": "ok",
        "rollup": distribution.rollup(state, editions),
        "schema_version": state.get("schema_version", distribution.SCHEMA_VERSION),
    }


def _editions_index() -> dict:
    """{id: edition_dict} — cached one-call helper so the per-request
    validation doesn't reparse editions.yaml twice."""
    from scripts.core import config

    return {str(e.get("id", "")): e for e in config.load_editions()}


@audit_log.audit_endpoint(action="distribution_mark")
def api_distribution_mark(edition_id: str, payload: dict | None) -> dict:
    """Mark `edition_id × payload['channel']` as shipped.

    Payload fields (all optional except `channel`):
        channel:    required; must be in DISTRIBUTION_CHANNELS
        url:        optional storefront URL
        isbn:       optional ISBN
        notes:      optional free-text
        shipped_at: optional ISO-8601 timestamp (defaults to now)

    Returns `{ok, edition_id, channel, entry}` on success.
    """
    from scripts.core import distribution

    payload = payload or {}
    channel_id = str(payload.get("channel", "")).strip().lower()
    if not channel_id:
        return {
            "ok": False,
            "error": "missing_channel",
            "message": "payload must include 'channel'",
        }
    if channel_id not in distribution.DISTRIBUTION_CHANNELS:
        return {
            "ok": False,
            "error": "unknown_channel",
            "message": (
                f"unknown distribution channel: {channel_id!r} (known: {', '.join(distribution.DISTRIBUTION_CHANNELS)})"
            ),
        }
    if edition_id not in _editions_index():
        return {
            "ok": False,
            "error": "unknown_edition",
            "message": f"unknown edition: {edition_id!r}",
        }
    try:
        entry = distribution.mark_shipped(
            edition_id,
            channel_id,
            url=payload.get("url"),
            isbn=payload.get("isbn"),
            notes=payload.get("notes"),
            shipped_at=payload.get("shipped_at"),
        )
    except ValueError as e:
        # Defensive: mark_shipped also validates channel — keep the
        # error envelope shape even if validation drifts.
        return {"ok": False, "error": "validation", "message": str(e)}
    return {
        "ok": True,
        "edition_id": edition_id,
        "channel": channel_id,
        "entry": entry,
    }


@audit_log.audit_endpoint(action="distribution_unmark")
def api_distribution_unmark(edition_id: str, channel_id: str) -> dict:
    """Remove the shipped entry for `edition_id × channel_id`.

    Idempotent — already-absent entries return `ok: True` with
    `removed: False`. Unknown channel returns an error envelope.
    Unknown edition is not an error (the entry simply doesn't exist).
    """
    from scripts.core import distribution

    channel_id = (channel_id or "").strip().lower()
    if channel_id not in distribution.DISTRIBUTION_CHANNELS:
        return {
            "ok": False,
            "error": "unknown_channel",
            "message": (
                f"unknown distribution channel: {channel_id!r} (known: {', '.join(distribution.DISTRIBUTION_CHANNELS)})"
            ),
        }
    removed = distribution.mark_unshipped(edition_id, channel_id)
    return {
        "ok": True,
        "edition_id": edition_id,
        "channel": channel_id,
        "removed": removed,
    }

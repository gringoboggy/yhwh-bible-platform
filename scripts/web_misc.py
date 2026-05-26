#!/usr/bin/env python3
"""
web_misc.py — verse-of-the-day feeds + onboarding-state JSON API
handlers, extracted from scripts/web.py in the god-module split
(2026-05-26).

Pure relocation: every handler here was moved verbatim from
``scripts/web.py``. ``scripts/web.py`` re-exports every name so the
route table + external importers keep resolving them in web.py's
namespace.
"""

from __future__ import annotations

from scripts.core import config, onboarding


def api_verse_of_day(
    date_iso: str | None = None,
    *,
    edition_id: str | None = None,
) -> dict:
    """Pure-function wrapper around `scripts.core.verse_of_day`.
    Returns the JSON-friendly payload for /api/verse-of-day.json.

    Returns:
        ``{"status": "ok", ...verse...}`` on success.
        ``{"status": "error", "code": ..., "http": ..., "message": ...}``
        on bad inputs or empty corpus (defensive — corpus is always
        populated in production).
    """
    from scripts.core.verse_of_day import verse_of_day

    if edition_id and edition_id not in config.editions_by_id():
        return {
            "status": "error",
            "code": "unknown_edition",
            "http": 400,
            "message": f"unknown edition: {edition_id}",
        }
    payload = verse_of_day(date_iso, edition_id=edition_id or None)
    if payload is None:
        return {
            "status": "error",
            "code": "no_notes",
            "http": 503,
            "message": "no notes in corpus",
        }
    return {"status": "ok", **payload}


def api_verse_of_day_rss(
    *,
    days: int = 7,
    base_url: str = "",
    edition_id: str | None = None,
) -> tuple:
    """Return ``(xml_text, content_type)`` for /api/verse-of-day.rss.

    Always returns a string (never raises) — feed consumers should
    never see a 500 on a transient edge case.
    """
    from scripts.core.verse_of_day import rss_feed

    try:
        days_i = int(days)
    except (TypeError, ValueError):
        days_i = 7
    days_i = max(1, min(days_i, 60))
    xml = rss_feed(
        days=days_i,
        base_url=base_url or "",
        edition_id=(edition_id or None) if (edition_id and edition_id in config.editions_by_id()) else None,
    )
    return xml, "application/rss+xml; charset=utf-8"


def _safe_rss_base_url(proto_header: str, host_header: str) -> str:
    """ξ.16 SEC-003 — sanitize the (proto, host) pair into a base URL
    that's safe to interpolate into RSS link tags.

    Trust order:
      1. ``YHWH_PUBLIC_BASE_URL`` env var (operator-set; authoritative).
         Empty / unset means fall through.
      2. ``Host`` header IFF it matches a strict localhost allowlist
         (``localhost``, ``127.0.0.1``, ``[::1]``, optionally with a
         port). Anything else — including domains with embedded
         colons, backslash characters, scheme-like prefixes, or
         non-ASCII — is rejected.
      3. Hardcoded ``http://localhost``.

    The proto header is similarly clamped to ``http`` or ``https``;
    anything else falls back to ``http``.
    """
    import os
    import re

    configured = (os.environ.get("YHWH_PUBLIC_BASE_URL") or "").strip()
    if configured:
        # Operator opted in. Trust it but still strip any trailing slash.
        return configured.rstrip("/")

    # Proto: only "http" or "https" — anything else (`javascript`,
    # `data`, malformed) falls back to http.
    proto = (proto_header or "http").strip().lower()
    if proto not in ("http", "https"):
        proto = "http"

    # Host: strict allowlist. Match `localhost`, `127.0.0.1`, or
    # `[::1]`, optionally suffixed `:<port>` where port is digits.
    # Anything else → fallback.
    host = (host_header or "").strip()
    # Defensive: reject control chars, whitespace, and non-ASCII.
    if not host or any(ord(c) < 0x21 or ord(c) > 0x7E for c in host):
        return "http://localhost"
    # Allow `host[:port]`. Port must be 1-5 digits.
    pattern = re.compile(r"^(localhost|127\.0\.0\.1|\[::1\])(:\d{1,5})?$")
    if not pattern.match(host):
        return "http://localhost"
    return f"{proto}://{host}"


def api_onboarding_state() -> dict:
    """Read-only onboarding state: {"first_run": bool, "onboarded_at": iso|None}."""
    return onboarding.onboarding_state()


def api_onboarding_complete(m, payload) -> dict:
    """Mark the first-run welcome flow complete (idempotent); return new state.
    POST-table signature (m, payload) — neither is used."""
    return onboarding.mark_onboarded()

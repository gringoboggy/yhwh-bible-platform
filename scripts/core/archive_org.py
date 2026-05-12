"""ο.4 — archive.org auto-upload (2026-05-11).

Month 5 #7 — the last non-money Month 5 item. Per the proposal:
"Drop edition → archive.org API push. Free distribution."

Composes ε.7's `build_zip` for the upload payload and auto-marks
ε.6's `archive_org` distribution cell on successful push (so the
checklist matrix updates without a manual toggle).

**Why archive.org**: free distribution for public-domain texts, lifts
the bandwidth burden off the publisher's own infrastructure, and
provides permanent archival of every shipped edition. Memory:
archive.org account is already available (per
`reference_external_tools.md`).

**Auth model** — Internet Archive uses S3-style credentials. The
publisher supplies them via env vars:

    EBIBLE_ARCHIVE_ORG_ACCESS_KEY
    EBIBLE_ARCHIVE_ORG_SECRET_KEY

Both are written into the `Authorization: LOW <access>:<secret>`
header on every upload request. Missing credentials → `is_configured()`
returns False; the API layer translates this to a 503-style
`{configured: false}` response (NOT an error — the publisher just
hasn't set the keys yet).

**Upload endpoint** — `https://s3.us.archive.org/<identifier>/<filename>`
PUT. Metadata fields are passed via `x-archive-meta-*` headers:

    x-archive-meta-title         — edition title
    x-archive-meta-description   — 500-word blurb if available
    x-archive-meta-mediatype     — "texts" (Internet Archive book bucket)
    x-archive-meta-collection    — "opensource" (the open-bookshelf
                                   collection that anyone can contribute to)
    x-archive-meta-language      — "eng"
    x-archive-meta-creator       — publisher name (env var, optional)
    x-archive-meta-licenseurl    — "https://creativecommons.org/publicdomain/zero/1.0/"

**Identifier rules** — archive.org identifiers must be ASCII
[a-z0-9._-], no leading dot, ≥5 chars. `sanitize_identifier`
collapses an edition_id like "catholic-study" plus a prefix
("yhwh-bible-") into a compliant slug.

**Public API**:
    is_configured()                                bool
    sanitize_identifier(edition_id, *, prefix)     str
    build_metadata_headers(edition, blurbs)        dict
    upload_press_kit(edition, blurbs, zip_bytes,   dict — result envelope
                     *, http_fn=None)

Tests inject `http_fn(url, body, headers) → (status, response_bytes)`
so the upload path runs without touching the real network. Production
defaults to `scripts.core.http.put` wrapped with the archive.org
upload allowlist.
"""

from __future__ import annotations

import os
import re
from typing import Callable


# Env-var names — single source of truth so the api layer + the UI
# status surface use the same strings.
ENV_ACCESS_KEY = "EBIBLE_ARCHIVE_ORG_ACCESS_KEY"
ENV_SECRET_KEY = "EBIBLE_ARCHIVE_ORG_SECRET_KEY"
ENV_CREATOR = "EBIBLE_PUBLISHER_NAME"  # optional; defaults to "YHWH Bible"

IDENTIFIER_PREFIX_DEFAULT = "yhwh-bible-"
ARCHIVE_S3_BASE = "https://s3.us.archive.org"

# Channel id used when auto-marking distribution after a successful
# upload. Matches `scripts.core.distribution.DISTRIBUTION_CHANNELS`.
DISTRIBUTION_CHANNEL = "archive_org"


def is_configured() -> bool:
    """True iff both access + secret env vars are set + non-empty."""
    return bool((os.environ.get(ENV_ACCESS_KEY) or "").strip()) and bool((os.environ.get(ENV_SECRET_KEY) or "").strip())


def _creator_name() -> str:
    """Publisher name surfaced as `x-archive-meta-creator`. Defaults
    to "YHWH Bible" when the env var isn't set so the metadata is
    never blank on a fresh install."""
    return (os.environ.get(ENV_CREATOR) or "").strip() or "YHWH Bible"


def sanitize_identifier(edition_id: str, *, prefix: str = IDENTIFIER_PREFIX_DEFAULT) -> str:
    """Build an archive.org-compliant identifier from `edition_id`.

    archive.org's identifier rules: ASCII lowercase letters + digits +
    period + dash + underscore; no leading dot; ≥5 chars. We collapse
    anything outside that set to a single dash, strip leading
    dots/dashes, and prefix with `yhwh-bible-` (or the caller's
    `prefix`) so YHWH-platform uploads are namespaced together.

    Empty / all-invalid input is replaced with a deterministic
    fallback ("untitled") so the identifier is always valid.
    """
    base = (edition_id or "").strip().lower()
    if not base:
        base = "untitled"
    # Collapse runs of invalid characters → single dash.
    cleaned = re.sub(r"[^a-z0-9._-]+", "-", base)
    cleaned = cleaned.lstrip(".-_")
    if not cleaned:
        cleaned = "untitled"
    identifier = f"{prefix}{cleaned}" if prefix else cleaned
    # Final length guard — archive.org accepts up to 100 chars; trim
    # rather than reject so the upload always proceeds.
    if len(identifier) > 100:
        identifier = identifier[:100]
    # The ≥5 char minimum is naturally met by the default prefix
    # (11 chars); defensive padding for an empty-prefix call.
    if len(identifier) < 5:
        identifier = (identifier + "edn00000")[:5]
    return identifier


def _sanitize_header_value(value: str) -> str:
    """archive.org's metadata headers don't accept CR/LF (HTTP
    response-splitting); collapse newlines and tabs to spaces and
    strip leading/trailing whitespace before they reach urllib.

    A safer alternative would be URL-encoding the value, but
    archive.org reads the raw header as the metadata value, so any
    encoding would surface in the published metadata."""
    if not value:
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ").replace("\t", " ")
    # Compact internal whitespace to single spaces so trim is clean.
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_metadata_headers(edition: dict, blurbs: dict) -> dict[str, str]:
    """Build the `x-archive-meta-*` header set for an upload.

    `edition` is the dict from `config.load_editions()`. `blurbs` is
    the dict from `press_kit.get_blurbs(state, edition_id)` (may be
    empty — descriptions still get a placeholder fallback so the
    archive.org item is never blank).
    """
    title = _sanitize_header_value(edition.get("title", edition.get("id", "Bible")))
    description = _sanitize_header_value(
        blurbs.get("blurb_500") or blurbs.get("blurb_150") or f"{title} (YHWH Bible Platform edition)"
    )
    return {
        "x-archive-meta-title": title,
        "x-archive-meta-description": description,
        "x-archive-meta-mediatype": "texts",
        "x-archive-meta-collection": "opensource",
        "x-archive-meta-language": "eng",
        "x-archive-meta-creator": _sanitize_header_value(_creator_name()),
        "x-archive-meta-licenseurl": "https://creativecommons.org/publicdomain/zero/1.0/",
    }


def _auth_header() -> str:
    """`Authorization: LOW <access>:<secret>` per Internet Archive's
    S3-style API. Raises RuntimeError when not configured — callers
    should call `is_configured()` first and surface a 503-style
    envelope before reaching this helper."""
    access = (os.environ.get(ENV_ACCESS_KEY) or "").strip()
    secret = (os.environ.get(ENV_SECRET_KEY) or "").strip()
    if not access or not secret:
        raise RuntimeError(f"archive.org credentials not configured (set {ENV_ACCESS_KEY} + {ENV_SECRET_KEY})")
    return f"LOW {access}:{secret}"


def upload_press_kit(
    edition: dict,
    blurbs: dict,
    zip_bytes: bytes,
    *,
    filename: str | None = None,
    http_fn: Callable[..., tuple[int, bytes]] | None = None,
) -> dict:
    """PUT a press-kit ZIP to archive.org. Returns an envelope dict:

        {
          "ok": bool,
          "identifier": "<archive.org identifier>",
          "url": "<public item URL>",
          "status_code": int,
          "filename": "<arc filename>",
          "bytes": int,
          "message": str,
        }

    `http_fn` injectable for tests — defaults to `scripts.core.http.put`
    with the archive.org upload allowlist. The injected fn receives
    `(url, body, headers)` and must return `(status_code, body_bytes)`.

    Pre-condition: `is_configured()` should be True (callers
    typically check at the API layer and return 503 envelope when
    not). This helper itself raises RuntimeError on missing creds
    rather than returning silently, since reaching it means an
    earlier check was bypassed.
    """
    edition_id = str(edition.get("id", ""))
    identifier = sanitize_identifier(edition_id)
    arc_filename = filename or f"press-kit-{edition_id}.zip"
    url = f"{ARCHIVE_S3_BASE}/{identifier}/{arc_filename}"

    headers = {
        "Authorization": _auth_header(),
        "Content-Type": "application/zip",
        # archive.org requires this header to mark uploads as new items.
        "x-archive-auto-make-bucket": "1",
    }
    headers.update(build_metadata_headers(edition, blurbs))

    if http_fn is None:
        # Lazy default — keeps the import cheap when callers inject.
        from scripts.core import http

        def _default_fn(u: str, body: bytes, hdrs: dict[str, str]) -> tuple[int, bytes]:
            return http.put(
                u,
                body,
                headers=hdrs,
                allowlist=http.DEFAULT_ARCHIVE_ORG_UPLOAD_ALLOWLIST,
            )

        http_fn = _default_fn

    try:
        status_code, response_body = http_fn(url, zip_bytes, headers)
    except Exception as e:
        # Surface as a result envelope rather than re-raising — the
        # API layer translates this for the publisher. Logging the
        # type lets the publisher distinguish 4xx (typically a
        # credentials / identifier problem) from network failures.
        return {
            "ok": False,
            "identifier": identifier,
            "url": f"https://archive.org/details/{identifier}",
            "status_code": 0,
            "filename": arc_filename,
            "bytes": len(zip_bytes),
            "message": f"upload failed: {type(e).__name__}: {e}",
        }

    public_url = f"https://archive.org/details/{identifier}"
    ok = 200 <= int(status_code) < 300
    return {
        "ok": ok,
        "identifier": identifier,
        "url": public_url,
        "status_code": int(status_code),
        "filename": arc_filename,
        "bytes": len(zip_bytes),
        "message": (
            f"uploaded {arc_filename} ({len(zip_bytes)} bytes) to {identifier}"
            if ok
            else f"upload returned HTTP {status_code}: {response_body[:200]!r}"
        ),
    }

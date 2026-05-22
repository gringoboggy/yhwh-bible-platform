"""ο.4 — archive.org auto-upload API (2026-05-11).

Two endpoints:
- `api_archive_org_status()` — GET; reports whether the publisher's
  credentials are configured + previews the identifier-prefix the
  uploader will use. Read-only; never touches the network.
- `api_archive_org_upload(edition_id, payload)` — POST; composes
  ε.7's `build_press_kit_zip` + `archive_org.upload_press_kit` +
  `distribution.mark_shipped(edition_id, "archive_org", url=...)` on
  successful push. Returns one envelope describing all three
  side-effects.

Credentials are read from env vars (see `scripts.core.archive_org`
for the var names). Missing creds → 503-style
`{configured: false, message: "..."}` envelope, NOT an error — the
publisher just hasn't set the keys yet.
"""

from __future__ import annotations

from collections.abc import Callable

from scripts.core import audit_log


def _editions_index() -> dict:
    from scripts.core import config

    return {str(e.get("id", "")): e for e in config.load_editions()}


def api_archive_org_status() -> dict:
    """Configuration + identifier-preview surface for the /exec
    Archive.org banner.

    Returns `{status, configured, message, identifier_prefix,
    env_var_access, env_var_secret}`. The env var *names* are
    surfaced so the UI can tell the publisher exactly what to set
    when configured=False.
    """
    from scripts.core import archive_org

    configured = archive_org.is_configured()
    return {
        "status": "ok",
        "configured": configured,
        "identifier_prefix": archive_org.IDENTIFIER_PREFIX_DEFAULT,
        "env_var_access": archive_org.ENV_ACCESS_KEY,
        "env_var_secret": archive_org.ENV_SECRET_KEY,
        "message": (
            "Credentials configured. Upload-ready."
            if configured
            else f"Set env vars {archive_org.ENV_ACCESS_KEY} + {archive_org.ENV_SECRET_KEY} to enable uploads."
        ),
    }


@audit_log.audit_endpoint(action="archive_org_upload")
def api_archive_org_upload(
    edition_id: str,
    payload: dict | None = None,
    *,
    http_fn: Callable[..., tuple[int, bytes]] | None = None,
) -> dict:
    """Compose press kit ZIP → archive.org upload → distribution mark.

    `payload` reserved for future options (e.g. dry-run flag, custom
    metadata overrides) — currently unused but accepted so the route
    can pass JSON through without forcing the body to be empty.

    `http_fn` injectable for tests; defaults to
    `scripts.core.http.put` with the archive-org upload allowlist.

    Pre-condition check: when credentials are absent, returns a 503
    envelope and emits no audit event for the upload itself (the
    decorator still logs the call).

    Side-effects:
    - Always: writes one audit entry via the @audit_endpoint decorator.
    - On configured=True + edition exists: builds press kit, calls
      archive.org PUT, returns envelope.
    - On configured=True + upload-ok=True: also calls
      `distribution.mark_shipped(edition_id, "archive_org",
      url=<archive.org public URL>)` so the ε.6 checklist auto-flips.
    """
    from scripts.core import archive_org, distribution, press_kit

    payload = payload or {}  # noqa: F841 — reserved for future options

    if not archive_org.is_configured():
        return {
            "status": "error",
            "code": "not_configured",
            "http": 503,
            "message": (
                f"archive.org credentials missing — set env vars "
                f"{archive_org.ENV_ACCESS_KEY} + {archive_org.ENV_SECRET_KEY}"
            ),
            "configured": False,
        }

    editions_idx = _editions_index()
    edition = editions_idx.get(edition_id)
    if edition is None:
        return {
            "status": "error",
            "code": "unknown_edition",
            "http": 404,
            "message": f"unknown edition: {edition_id!r}",
        }

    # Build the press kit (ε.7 composition).
    blurbs = press_kit.get_blurbs(press_kit.load_press_kit(), edition_id)
    zip_bytes = press_kit.build_zip(edition, blurbs)
    filename = f"press-kit-{edition_id}.zip"

    # Upload (ο.4 core).
    result = archive_org.upload_press_kit(
        edition,
        blurbs,
        zip_bytes,
        filename=filename,
        http_fn=http_fn,
    )

    distribution_marked = False
    distribution_error: str | None = None
    if result.get("ok"):
        try:
            distribution.mark_shipped(
                edition_id,
                archive_org.DISTRIBUTION_CHANNEL,
                url=result.get("url"),
                notes=f"auto-marked via ο.4 archive.org upload ({result.get('identifier')})",
            )
            distribution_marked = True
        except Exception as e:
            # The upload itself succeeded; the side-effect failed.
            # Surface the side-effect failure in the envelope but
            # don't unwind the upload.
            distribution_error = f"{type(e).__name__}: {e}"

    return {
        "ok": bool(result.get("ok")),
        "edition_id": edition_id,
        "identifier": result.get("identifier"),
        "url": result.get("url"),
        "status_code": result.get("status_code"),
        "filename": result.get("filename"),
        "bytes": result.get("bytes"),
        "distribution_marked": distribution_marked,
        "distribution_error": distribution_error,
        "message": result.get("message"),
    }

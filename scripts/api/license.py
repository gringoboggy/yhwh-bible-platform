"""ξ.26 — license-key API handlers (2026-05-12).

Three endpoints for the per-edition license validation surface:

- `api_license_status()` — GET; returns
  {enforcement_enabled, signing_key_env, editions: [{id, title,
  has_key, valid, reason, expires?}]}. Read-only; never reveals
  the signing secret or the actual license string.
- `api_license_set(edition_id, payload)` — PUT; stores a license
  key for an edition after verifying it. Refuses to persist an
  invalid key (prevents storing a bad key that would show
  "invalid" forever).
- `api_license_remove(edition_id)` — DELETE; removes the entry
  (idempotent).

Soft enforcement: the API never refuses a request based on
license state. The status endpoint surfaces per-edition validity
so the UI can render a warning banner. The build / preview /
publish paths can consult this status but should not crash.
"""

from __future__ import annotations

from scripts.core import audit_log


def _editions_index() -> dict:
    """{id: edition_dict}. Delegates to the shared config.editions_by_id()."""
    from scripts.core import config

    return config.editions_by_id()


def api_license_status() -> dict:
    """Per-edition license validity rollup.

    Computes verify() for every shipped edition against its stored
    license (if any). Returns a stable envelope the UI can render
    without follow-up calls.
    """
    from scripts.core import license_key, license_state

    state = license_state.load_licenses()
    editions = _editions_index()

    rows: list[dict] = []
    for ed_id, ed in editions.items():
        title = str(ed.get("title", ed_id))
        stored = license_state.get_license(ed_id, state)
        if not stored:
            rows.append(
                {
                    "id": ed_id,
                    "title": title,
                    "has_key": False,
                    "valid": False,
                    "reason": "missing",
                }
            )
            continue
        result = license_key.verify(stored)
        rows.append(
            {
                "id": ed_id,
                "title": title,
                "has_key": True,
                "valid": bool(result.get("valid")),
                "reason": str(result.get("reason", "")),
                "expires_iso": result.get("expires_iso"),
                "issued_at_iso": result.get("issued_at_iso"),
            }
        )

    return {
        "status": "ok",
        "enforcement_enabled": license_key.is_enforced(),
        "signing_key_env": license_key.ENV_SIGNING_KEY,
        "license_prefix": license_key.LICENSE_PREFIX,
        "editions": rows,
    }


@audit_log.audit_endpoint(action="license_set")
def api_license_set(edition_id: str, payload: dict | None) -> dict:
    """Store a license key for `edition_id`. Verifies before persisting.

    Payload:
        key: required; the LK1-format license string.

    Refuses (and emits no state change) when:
        - edition_id is not a known edition (catches typos);
        - the key fails signature verification under the active
          signing secret;
        - the key is expired.

    Soft-enforcement note: a "bad_signature" result while
    enforcement IS enabled returns ok:False here BUT the build
    pipeline never refuses. The /publisher UI surfaces the
    warning banner via api_license_status.
    """
    from scripts.core import license_key, license_state

    payload = payload or {}
    edition_id = (edition_id or "").strip()
    if edition_id not in _editions_index():
        return {
            "ok": False,
            "error": "unknown_edition",
            "message": f"unknown edition: {edition_id!r}",
        }
    key = str(payload.get("key", "")).strip()
    if not key:
        return {"ok": False, "error": "missing_key", "message": "payload.key required"}

    result = license_key.verify(key)
    if not result.get("valid"):
        return {
            "ok": False,
            "error": "invalid_key",
            "reason": str(result.get("reason", "")),
            "message": "key failed verification; not stored",
        }
    if result.get("edition_id") and result["edition_id"] != edition_id:
        return {
            "ok": False,
            "error": "edition_mismatch",
            "message": (f"key was signed for edition {result['edition_id']!r}, not {edition_id!r}"),
        }

    entry = license_state.set_license(edition_id, key)
    return {
        "ok": True,
        "edition_id": edition_id,
        "stored_at": entry.get("stored_at"),
        "expires_iso": result.get("expires_iso"),
        "issued_at_iso": result.get("issued_at_iso"),
    }


@audit_log.audit_endpoint(action="license_remove")
def api_license_remove(edition_id: str) -> dict:
    """Remove the license entry for `edition_id`. Idempotent."""
    from scripts.core import license_state

    edition_id = (edition_id or "").strip()
    removed = license_state.remove_license(edition_id)
    return {"ok": True, "edition_id": edition_id, "removed": removed}

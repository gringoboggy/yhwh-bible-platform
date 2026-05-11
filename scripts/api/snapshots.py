"""ω.35-B.1 — snapshot API handlers, extracted from scripts/web.py.

Six thin wrappers over `scripts.core.snapshots`:
- api_snapshot_list / get / diff — read-only
- api_snapshot_create / restore / delete — mutations (audit-logged)

The audit decorator wraps the mutating handlers so every snapshot
create/restore/delete leaves an entry in the audit log
(`scripts.core.audit_log`).

Backward compatibility: scripts/web.py re-imports all six names
from this module so the existing flat namespace is preserved.
Route-table lambdas in web.py continue to reference
`api_snapshot_*` by name; tests that import from `scripts.web`
keep working.
"""

from __future__ import annotations

from scripts.core import audit_log


def api_snapshot_list(edition_id: str) -> dict:
    """List every snapshot for `edition_id` (newest first by name).

    Snapshot names are alphanumeric so version-string sorting is
    stable enough for retail use; the UI can render them however
    it prefers.
    """
    from scripts.core import snapshots as snap_mod

    try:
        snaps = snap_mod.list_snapshots(edition_id)
    except ValueError as e:
        return {"status": "error", "code": "invalid_name", "http": 400, "message": str(e)}
    return {
        "status": "ok",
        "edition_id": edition_id,
        "snapshots": [s.to_dict() for s in snaps],
    }


def api_snapshot_get(edition_id: str, version: str) -> dict:
    from scripts.core import snapshots as snap_mod

    try:
        snap = snap_mod.read_snapshot(edition_id, version)
    except ValueError as e:
        return {"status": "error", "code": "invalid_name", "http": 400, "message": str(e)}
    if snap is None:
        return {
            "status": "error",
            "code": "not_found",
            "http": 404,
            "message": f"snapshot {edition_id!r}/{version!r} not found",
        }
    return {"status": "ok", **snap}


@audit_log.audit_endpoint(action="snapshot_create")
def api_snapshot_create(edition_id: str, payload: dict) -> dict:
    from scripts.core import snapshots as snap_mod

    if not isinstance(payload, dict):
        return {"status": "error", "code": "invalid_input", "http": 400, "message": "payload must be a JSON object"}
    version = payload.get("version") or ""
    label = payload.get("label") or None
    notes = payload.get("notes") or None
    overwrite = bool(payload.get("overwrite"))
    return snap_mod.create_snapshot(
        edition_id,
        version,
        label=label,
        notes=notes,
        overwrite=overwrite,
    )


def api_snapshot_diff(
    edition_id: str,
    version: str,
    *,
    against_version: str | None = None,
) -> dict:
    from scripts.core import snapshots as snap_mod

    return snap_mod.diff_snapshot(
        edition_id,
        version,
        against_version=against_version,
    )


@audit_log.audit_endpoint(action="snapshot_restore")
def api_snapshot_restore(edition_id: str, version: str) -> dict:
    from scripts.core import snapshots as snap_mod

    return snap_mod.restore_snapshot(edition_id, version)


@audit_log.audit_endpoint(action="snapshot_delete")
def api_snapshot_delete(edition_id: str, version: str) -> dict:
    from scripts.core import snapshots as snap_mod

    return snap_mod.delete_snapshot(edition_id, version)

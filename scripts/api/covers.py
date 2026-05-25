"""ω.35-B.3a — cover-mutation API handlers, extracted from scripts/web.py.

Four mutation handlers for cover uploads + deletes (Phase π.4-B):
- api_upload_cover_main / api_upload_cover_book (multipart bodies;
  audit-logged)
- api_delete_cover_main / api_delete_cover_book (mutations that
  also clear the on-disk file; audit-logged)

Out of scope for B.3a (still in web.py):
- api_covers() GET endpoint — tangled with the response-cache layer
  (_cached_covers, _compute_covers_uncached, _files_signature).
  A future B.3a.1 may absorb it once the cache-layer dependencies
  are factored out.
- Internal helper `_save_cover_bytes` — still in web.py (close to
  the _files_signature / _notes_dir_signature cache layer and the
  validate-then-write upload pipeline). Multipart helpers
  `_extract_boundary` / `_parse_multipart` were moved to
  `scripts.api.multipart` in ω.35-B.7.

Lazy import pattern: the 4 handlers below lazy-import from
`scripts.web` inside their function bodies, NOT at module top.
Reason: web.py imports this module at module-load time (re-export
pattern). Importing web.py back at THIS module's top level would
create a circular import. Inside a function body, the import
doesn't fire until call time — by which point web.py is fully
loaded.

Backward compatibility: scripts/web.py re-imports all 4 names so
the existing flat namespace stays the same. Route-table lambdas
in `_MULTIPART_ROUTES` and `_DELETE_ROUTES` continue to reference
the handlers by their flat name.
"""

from __future__ import annotations

from scripts.core import audit_log


@audit_log.audit_endpoint(action="upload_cover_main")
def api_upload_cover_main(edition_id: str, body: bytes, content_type: str) -> dict:
    """Phase π.4-B — upload a main cover for one edition."""
    from scripts.api.multipart import _extract_boundary, _parse_multipart
    from scripts.web import _save_cover_bytes

    boundary = _extract_boundary(content_type)
    if boundary is None:
        return {"error": "request must be multipart/form-data with a boundary"}
    parts = _parse_multipart(body, boundary)
    file_parts = [p for p in parts if p.get("filename")]
    if not file_parts:
        return {"error": "no file part in upload"}
    return _save_cover_bytes(file_parts[0]["data"], edition_id, None)


@audit_log.audit_endpoint(action="upload_cover_book")
def api_upload_cover_book(edition_id: str, book_code: str, body: bytes, content_type: str) -> dict:
    """Phase π.4-B — upload a per-book cover."""
    from scripts.api.multipart import _extract_boundary, _parse_multipart
    from scripts.web import _save_cover_bytes

    boundary = _extract_boundary(content_type)
    if boundary is None:
        return {"error": "request must be multipart/form-data with a boundary"}
    parts = _parse_multipart(body, boundary)
    file_parts = [p for p in parts if p.get("filename")]
    if not file_parts:
        return {"error": "no file part in upload"}
    return _save_cover_bytes(file_parts[0]["data"], edition_id, book_code)


@audit_log.audit_endpoint(action="apply_cover_template")
def api_apply_cover_template(edition_id: str, template_stem: str) -> dict:
    """§4.6 — (re)compose an edition's main cover from one of the 25 design
    templates + the edition title, write it to content/covers/<id>.jpg, and
    point both cover_image and cover_template at the result.

    Mirrors ``_save_cover_bytes``' validate → write → save-yaml transaction,
    but the bytes come from ``generate_edition_covers._compose_cover`` rather
    than an upload. Returns ``{"ok": True, ...}`` or ``{"error": "..."}``.
    """
    import io
    from pathlib import Path

    from scripts.api.editions import api_save_edition_meta
    from scripts.core import config, covers as _covers, notes_io
    from scripts.generate_edition_covers import _compose_cover, title_for_edition

    stem = (template_stem or "").strip()
    if stem not in _covers.COVER_TEMPLATES:
        return {"error": f"unknown cover_template: {stem!r}"}
    if edition_id not in config.editions_by_id():
        return {"error": f"unknown edition: {edition_id}"}

    REPO = Path(__file__).resolve().parent.parent.parent
    rel_path = f"covers/{edition_id}.jpg"
    abs_path = REPO / "content" / rel_path

    # Compose the title-only cover onto the chosen template, to JPEG bytes.
    try:
        img = _compose_cover(stem, title_for_edition(edition_id))
    except FileNotFoundError as e:
        return {"error": str(e)}
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90, optimize=True)

    # Back up any existing cover, then write atomically (same as uploads).
    if abs_path.exists():
        notes_io.ensure_backup(abs_path)
    try:
        notes_io.atomic_write_bytes(abs_path, buf.getvalue())
    except OSError as e:
        return {"error": f"failed to write cover: {e}"}

    # Record BOTH the resolved cover path and the chosen template stem. The
    # cover_template enum-validation in api_save_edition_meta runs here.
    save_result = api_save_edition_meta(edition_id, {"cover_image": rel_path, "cover_template": stem})
    if not save_result.get("ok"):
        return {"error": f"yaml save failed: {save_result.get('error')}"}

    return {"ok": True, "edition_id": edition_id, "cover_template": stem, "path": rel_path}


@audit_log.audit_endpoint(action="delete_cover_main")
def api_delete_cover_main(edition_id: str) -> dict:
    """Phase π.4-B — clear an edition's main cover assignment + file."""
    from pathlib import Path

    from scripts.core import config, notes_io

    # ω.35-B.5 — api_save_edition_meta moved to scripts.api.editions.
    # Previously imported from scripts.web (where it was inline).
    from scripts.api.editions import api_save_edition_meta

    REPO = Path(__file__).resolve().parent.parent.parent
    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}
    edition = eds[edition_id]
    cur_path = (edition.get("cover_image") or "").strip()
    # Update YAML first (set cover_image to empty)
    save_result = api_save_edition_meta(edition_id, {"cover_image": ""})
    if not save_result.get("ok"):
        return {"error": save_result.get("error", "yaml save failed")}
    # Then back up + remove the on-disk file
    if cur_path:
        abs_path = REPO / "content" / cur_path
        if abs_path.exists():
            notes_io.ensure_backup(abs_path)
            try:
                abs_path.unlink()
            except OSError:
                pass
    return {"ok": True, "edition_id": edition_id, "cleared": cur_path}


@audit_log.audit_endpoint(action="delete_cover_book")
def api_delete_cover_book(edition_id: str, book_code: str) -> dict:
    """Phase π.4-B — clear a per-book cover assignment + file."""
    from pathlib import Path

    from scripts.core import config, covers as _covers, notes_io

    # ω.35-B.5 — api_save_edition_meta moved to scripts.api.editions.
    from scripts.api.editions import api_save_edition_meta

    REPO = Path(__file__).resolve().parent.parent.parent
    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}
    if book_code not in config.books_by_code():
        return {"error": f"unknown book code: {book_code}"}
    edition = eds[edition_id]
    per_book = _covers.decode_book_covers(edition.get("book_covers"))
    cur_path = per_book.pop(book_code, "")
    save_result = api_save_edition_meta(edition_id, {"book_covers": per_book})
    if not save_result.get("ok"):
        return {"error": save_result.get("error", "yaml save failed")}
    if cur_path:
        abs_path = REPO / "content" / cur_path
        if abs_path.exists():
            notes_io.ensure_backup(abs_path)
            try:
                abs_path.unlink()
            except OSError:
                pass
    return {"ok": True, "edition_id": edition_id, "book_code": book_code, "cleared": cur_path}

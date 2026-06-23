#!/usr/bin/env python3
"""
web_covers.py — per-edition cover status + cover-byte persister,
extracted from scripts/web.py in the god-module split (2026-05-26).

Pure relocation: every function here was moved verbatim from
``scripts/web.py``. ``scripts/web.py`` re-exports every name so the
route table + external importers (``scripts/api/covers.py`` lazy-imports
``_save_cover_bytes`` from ``scripts.web``) keep resolving them in
web.py's namespace.
"""

from __future__ import annotations

import functools

from scripts.api.editions import api_save_edition_meta
from scripts.core import config, notes_io, paths
from scripts.web_helpers import _files_signature, _notes_dir_signature


@functools.lru_cache(maxsize=4)
def _cached_covers(eds_sig, books_sig, notes_sig):
    # Note: cover image mtimes are NOT in the signature — image meta
    # is read at call time and lru_cache only memoizes the structural
    # data (paths, canon membership). Re-reading meta on each call
    # is cheap (header parse only) and reflects fresh disk state.
    return _compute_covers_uncached()


def _validate_cover_path(path) -> str:
    """Return an error message if ``path`` is unsafe / malformed, else ''.

    Covers live under content/. We forbid:
      - non-string or oversized values
      - absolute paths (escape from content/)
      - parent-traversal segments (``..``)
      - hidden files (``.something``) — keeps the storage area clean
      - extensions outside our supported set

    Empty string is allowed and means "no cover set". Validation
    runs on every save BEFORE any disk write, so a bad payload
    cannot land in editions.yaml.
    """
    if path is None:
        return ""  # treated as empty
    if not isinstance(path, str):
        return "cover path must be a string"
    s = path.strip()
    if not s:
        return ""  # empty == "no cover", allowed
    if len(s) > 500:
        return "cover path too long (max 500 chars)"
    # Normalize separators for the safety checks; we accept either
    # but store as posix-style in editions.yaml.
    norm = s.replace("\\", "/")
    if norm.startswith("/"):
        return f"cover path must be relative to content/, not absolute: {s!r}"
    parts = [p for p in norm.split("/") if p]
    if any(p == ".." for p in parts):
        return f"cover path may not contain '..': {s!r}"
    if any(p.startswith(".") for p in parts):
        return f"cover path may not contain hidden segments: {s!r}"
    # Extension check — keep the door open for file types we accept;
    # we don't validate the FILE here (it may not exist yet), only the
    # path string. π.4-B's upload endpoint validates the actual bytes.
    allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
    suffix = norm.rsplit(".", 1)
    if len(suffix) != 2 or "." + suffix[1].lower() not in allowed_ext:
        return f"cover path must end in an image extension ({', '.join(sorted(allowed_ext))}): {s!r}"
    return ""


def api_covers() -> dict:
    """Phase π.4-A — per-edition cover status feed. Cached on the
    structural inputs (editions, books, notes); image metadata is
    re-read each call so newly-uploaded covers reflect immediately."""
    return _cached_covers(
        _files_signature(paths.editions_yaml()),
        _files_signature(paths.books_yaml()),
        _notes_dir_signature(),
    )


def _save_cover_bytes(data: bytes, edition_id: str, book_code: str | None) -> dict:
    """Internal helper: validate + write + update editions.yaml.

    Returns a dict suitable for direct JSON response. Either
    ``{"ok": True, "path": "...", "meta": {...}}`` on success or
    ``{"error": "..."}`` on any failure. Disk is never mutated on
    failure.
    """
    from scripts.core import covers as _covers

    try:
        data, meta = _covers.normalize_cover_image(data)
    except ValueError as e:
        return {"error": str(e)}

    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}
    if book_code is not None:
        book_code = config.resolve_book_code(book_code)
        if book_code not in config.books_by_code():
            return {"error": f"unknown book code: {book_code}"}

    # Compute the storage path. We use the canonical helpers so the
    # naming is consistent with any future migration tool.
    if book_code is None:
        rel_path = _covers.storage_path_for_main(edition_id, meta["format"])
    else:
        rel_path = _covers.storage_path_for_book(edition_id, book_code, meta["format"])
    abs_path = paths.content_root() / rel_path

    # Back up any existing file before overwrite. ensure_backup is a
    # no-op when the file doesn't exist — first-upload case.
    if abs_path.exists():
        notes_io.ensure_backup(abs_path)

    # Write the file atomically. atomic_write_bytes creates parent
    # dirs as needed.
    try:
        notes_io.atomic_write_bytes(abs_path, data)
    except OSError as e:
        return {"error": f"failed to write cover: {e}"}

    # Update editions.yaml — for main, set cover_image; for book,
    # update the book_covers entry. Reuse api_save_edition_meta so
    # validation + caching invalidation flow through one path.
    if book_code is None:
        save_payload = {"cover_image": rel_path}
    else:
        # Read existing per-book covers, modify, write back.
        edition_now = eds[edition_id]
        per_book = _covers.decode_book_covers(edition_now.get("book_covers"))
        per_book[book_code] = rel_path
        save_payload = {"book_covers": per_book}

    save_result = api_save_edition_meta(edition_id, save_payload)
    if not save_result.get("ok"):
        # Roll back the file we just wrote — keeps disk + yaml in sync
        try:
            abs_path.unlink()
        except OSError:
            pass
        return {"error": f"yaml save failed: {save_result.get('error')}"}

    return {
        "ok": True,
        "edition_id": edition_id,
        "book_code": book_code,
        "path": rel_path,
        "meta": meta,
    }


def _compute_covers_uncached() -> dict:
    """Return per-edition cover status for the publisher console
    (Phase π.4-A read API).

    For each edition, the response includes:
      - main_cover  → path + image metadata (or None if missing)
      - book_covers → list of slot records, ONE PER BOOK IN THE
                      EDITION'S CANON, in canonical Book/Chapter
                      order (Rule §6.1). Books outside the canon
                      do NOT appear — Tanakh shows 39 slots,
                      Ethiopian shows 87. Slots without an assigned
                      cover have ``meta: None``.

    The canon ordering comes from books.yaml (the single source of
    truth) intersected with each edition's canon book set from the
    matrix module. The same shape powers the future /covers UI in
    π.4-B.
    """
    from scripts.core import covers as _covers
    from scripts.core import matrix as _matrix

    editions = config.load_editions()
    books_in_order = config.load_books()
    book_rank = {b["code"]: i for i, b in enumerate(books_in_order)}
    books_idx = {b["code"]: b for b in books_in_order}

    mtx = _matrix.compute_matrix()
    edition_canons = mtx.edition_canon_books

    records = []
    for ed in editions:
        canon_set = edition_canons.get(ed["id"], set())
        # Sort by canonical position (NOT alphabetical, NOT insertion).
        canon_books = sorted(canon_set, key=lambda c: book_rank.get(c, 1_000_000))
        records.append(
            _covers.cover_record_for_edition(
                ed,
                canon_books,
                books_idx,
            )
        )
    return {"editions": records}

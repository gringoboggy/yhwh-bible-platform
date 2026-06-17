#!/usr/bin/env python3
"""
web_notes.py — note browse/edit JSON API handlers, extracted from
scripts/web.py in the god-module split (2026-05-26).

Pure relocation: every handler here was moved verbatim from
``scripts/web.py``. ``scripts/web.py`` re-exports every name so the
route table + external importers keep resolving them in web.py's
namespace.
"""

from __future__ import annotations

from scripts.core import audit_log, config, notes_io
from scripts.web_helpers import (
    NOTES_DIR,
    _nn,
    _nq,
    dict_to_tuple,
    quality_for,
    tuple_to_dict,
    write_book,
)


def _book_code_input(code: str) -> str:
    """Normalize legacy aliases at the API boundary."""
    return config.resolve_book_code(code)


# ============================================================
# JSON API handlers
# ============================================================


def api_books() -> dict:
    """List every book with note counts + per-kind histogram."""
    out = []
    for b in config.load_books():
        path = NOTES_DIR / f"{b['code']}.py"
        if not path.is_file():
            continue
        loaded = notes_io.load_notes(path)
        if loaded is None:
            continue
        notes = loaded
        kinds: dict[str, int] = {}
        for tup in notes:
            if isinstance(tup, tuple) and len(tup) >= 5:
                kinds[tup[4]] = kinds.get(tup[4], 0) + 1
        out.append(
            {
                "code": b["code"],
                # Display name: books.yaml carries the human name under
                # `title` (e.g. "The First Book of Moses, Genesis"); there is
                # no `name` field, so the old `b.get("name", b["code"])`
                # fell back to the code → the editor rendered the tag twice
                # ("gen gen"). Prefer name → title → code.
                "name": b.get("name") or b.get("title") or b["code"],
                "bxx": b.get("bxx", ""),
                "strategy": b.get("strategy", ""),
                "ch_count": b.get("ch_count", 0),
                "note_count": len(notes),
                "kinds": kinds,
            }
        )
    return {"books": out}


def api_notes(book_code: str) -> dict:
    """Return all notes in one book as dicts (with index for editing)."""
    book_code = _book_code_input(book_code)
    path = NOTES_DIR / f"{book_code}.py"
    if not path.is_file():
        return {"error": "book not found", "book": book_code}
    loaded = notes_io.load_notes_checked(path, book=book_code)
    if isinstance(loaded, dict):
        return loaded
    notes = loaded
    items = []
    for i, tup in enumerate(notes):
        if not isinstance(tup, tuple) or len(tup) < 8:
            continue
        d = tuple_to_dict(tup)
        d["index"] = i
        d["quality"] = quality_for(book_code, tup)
        items.append(d)
    return {"book": book_code, "notes": items}


def api_kinds() -> dict:
    """Return the kind taxonomy + per-kind budgets."""
    nq = _nq()
    kinds = config.load_kinds()
    out = []
    for k in kinds:
        code = k["code"]
        lo, hi = nq.budget_for(code, 50, 200)
        out.append(
            {
                "code": code,
                "category": k.get("category", ""),
                "label": k.get("label", code),
                "phase": k.get("phase", ""),
                "description": k.get("description", ""),
                "budget": [lo, hi],
            }
        )
    return {"kinds": out}


def api_template(kind: str) -> dict:
    """Return the per-kind scaffold template for a fresh note."""
    label, body, attribution = _nn().template_for(kind)
    return {"label": label, "body": body, "attribution": attribution}


def api_preview(
    edition_id: str,
    book_code: str,
    chapter,
    *,
    translation_id: str = "kjv",
) -> dict:
    """ψ.1.0 — Live one-chapter preview.

    Returns the §9 standard dict shape:
      {"status": "ok", "html": "<full standalone HTML>",
       "verse_count": int, "notes_shown": int, ...}
      {"status": "error", "code": "...", "http": 4xx, "message": "..."}

    Surfaced at GET /api/preview/<edition_id>/<book>/<chapter>
    (translation_id optional via ?translation=<id>; defaults to KJV).

    Composes scripts.core.preview.render_chapter_preview which
    composes (config + notes_io + translations + build_edition's
    enabled-kinds + tradition resolvers + theme CSS).
    """
    from scripts.core import preview

    return preview.render_chapter_preview(
        edition_id,
        _book_code_input(book_code),
        chapter,
        translation_id=translation_id,
    )


@audit_log.audit_endpoint(action="save_note")
def api_save(book_code: str, payload: dict) -> dict:
    """Replace one note (by index) or insert a new note (index=null)."""
    book_code = _book_code_input(book_code)
    path = NOTES_DIR / f"{book_code}.py"
    if not path.is_file():
        return {"error": "book not found", "book": book_code}
    loaded = notes_io.load_notes_checked(path, book=book_code)
    if isinstance(loaded, dict):
        return loaded
    from scripts.core.html_sanitize import sanitize_html

    if "body" in payload:
        payload = dict(payload)
        payload["body"] = sanitize_html(str(payload.get("body") or ""))
    notes = list(loaded)
    new_tup = dict_to_tuple(payload)
    idx = payload.get("index")
    if idx is None or idx == "":
        notes.append(new_tup)
        new_index = len(notes) - 1
    else:
        idx = int(idx)
        if idx < 0 or idx >= len(notes):
            return {"error": "index out of range", "index": idx}
        notes[idx] = new_tup
        new_index = idx
    write_book(book_code, notes)
    return {"ok": True, "index": new_index, "quality": quality_for(book_code, new_tup)}


@audit_log.audit_endpoint(action="delete_note")
def api_delete(book_code: str, index: int) -> dict:
    """Delete a note. Backup is created automatically."""
    book_code = _book_code_input(book_code)
    path = NOTES_DIR / f"{book_code}.py"
    if not path.is_file():
        return {"error": "book not found", "book": book_code}
    loaded = notes_io.load_notes_checked(path, book=book_code)
    if isinstance(loaded, dict):
        return loaded
    notes = list(loaded)
    if index < 0 or index >= len(notes):
        return {"error": "index out of range", "index": index}
    removed = notes.pop(index)
    write_book(book_code, notes)
    return {"ok": True, "removed": tuple_to_dict(removed)}


def api_search_notes(
    query: str,
    *,
    edition_id: str | None = None,
    kind: str | None = None,
    book: str | None = None,
    limit: int = 100,
) -> dict:
    """Pure-function wrapper that returns matching notes for the
    given query, optionally filtered by edition / kind / book.

    Δ.2.1 (2026-05-11) — wire flipped from
    `scripts.core.note_search.search_notes` (file-walk) to
    `scripts.core.corpus_index.search` (indexed). The Δ.2
    equivalence pin (`test_search_equivalence_with_file_walk_for_real_corpus`)
    confirms identical hit counts + identical top-5 tuples
    across the real corpus; the indexed path serves the same
    dict shape directly (no `SearchHit.to_dict()` translation
    needed). Empirical: file-walk ~3s cold on 51K notes;
    indexed ≥3× faster (per Δ.2's perf pin) and reads from the
    warm sqlite served by the Δ.6 fingerprint cache.

    Returns:
        ``{"status": "ok", "query": str, "filters": {...},
           "total": int, "hits": [{...}, ...]}`` on success.
        ``{"status": "error", "code": ..., "http": 400, "message": ...}``
        on bad input.
    """
    from scripts.core import corpus_index

    q = (query or "").strip()
    if not q:
        return {
            "status": "ok",
            "query": "",
            "filters": {
                "edition_id": edition_id,
                "kind": kind,
                "book": book,
            },
            "total": 0,
            "hits": [],
        }
    if len(q) > 500:
        return {
            "status": "error",
            "code": "query_too_long",
            "http": 400,
            "message": "query must be ≤ 500 characters",
        }
    try:
        cap = int(limit)
    except (TypeError, ValueError):
        cap = 100
    cap = max(1, min(cap, 500))

    book_filter = _book_code_input(book) if book else None
    hits = corpus_index.search(
        q,
        edition_id=edition_id or None,
        kind=kind or None,
        book=book_filter,
        limit=cap,
    )

    kinds_idx = config.kinds_by_code()
    cats_idx = config.categories_by_id()

    enriched = []
    for d in hits:
        kind_code = d.get("kind", "")
        kind_def = kinds_idx.get(kind_code, {})
        cat_id = kind_def.get("category", "?")
        cat_def = cats_idx.get(cat_id, {})
        d["kind_label"] = kind_def.get("label", kind_code)
        d["category"] = cat_id
        d["category_label"] = cat_def.get("label", cat_id)
        d["category_symbol"] = cat_def.get("symbol", "?")
        enriched.append(d)

    return {
        "status": "ok",
        "query": q,
        "filters": {
            "edition_id": edition_id,
            "kind": kind,
            "book": book,
        },
        "limit": cap,
        "total": len(enriched),
        "hits": enriched,
    }

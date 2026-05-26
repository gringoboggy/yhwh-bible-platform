#!/usr/bin/env python3
"""
web_sources.py — sources-navigator, attribution-audit, and
publisher-data JSON API handlers, extracted from scripts/web.py in
the god-module split (2026-05-26).

Pure relocation: every function/constant here was moved verbatim from
``scripts/web.py``. ``scripts/web.py`` re-exports every name so the
route table + external importers (``scripts/api/editions.py`` lazy-
imports ``PUBLISHING_LIST_FIELDS`` / ``PUBLISHING_TEXT_LIMITS`` from
``scripts.web``) keep resolving them in web.py's namespace.
"""

from __future__ import annotations

import functools
import re
from datetime import datetime, timezone

from scripts.core import config, notes_io
from scripts.web_helpers import (
    NOTES_DIR,
    REPO,
    _files_signature,
    _notes_dir_signature,
    note_id_from_tuple,
)


@functools.lru_cache(maxsize=4)
def _cached_attribution_audit(notes_sig, kinds_sig, cats_sig, books_sig):
    # Δ.3.1 (2026-05-11) — wire flipped to the indexed path.
    # `corpus_index.audit_attribution()` produces the same counts +
    # needs_attention list (Δ.3 equivalence pin confirms identity);
    # the file-walk reference at `_compute_attribution_audit_uncached`
    # is retained as the equivalence anchor and a fall-back. The
    # outer lru_cache(maxsize=4) keyed on file signatures stays —
    # it adds a second invalidation layer that catches kinds/
    # categories/books YAML mutations the inner corpus_index doesn't
    # track directly. The `by_kind` shape translation
    # (tuple-list → dict-list) preserves the frontend contract:
    # /audit consumers expect `[{"kind": k, "count": n}]`, not
    # `[(k, n)]` (which JSON-serializes to `[[k, n]]`).
    from scripts.core import corpus_index

    raw = corpus_index.audit_attribution()
    return {
        **raw,
        "by_kind": [{"kind": k, "count": n} for k, n in raw["by_kind"]],
    }


@functools.lru_cache(maxsize=4)
def _cached_publisher_data(eds_sig):
    return _compute_publisher_data_uncached()


# ============================================================
# Sources Navigator API (Phase μ.3) — browse notes by book/chapter
# ============================================================


def api_sources_index() -> dict:
    """Return a lightweight index of every book + its note count.

    Used to populate the left sidebar of the Sources Navigator. Cheap
    to compute (uses notes_io.load_notes which is mtime-cached).
    """
    books = config.load_books()
    out = []
    for b in books:
        path = NOTES_DIR / f"{b['code']}.py"
        notes = notes_io.load_notes(path) if path.is_file() else []
        out.append(
            {
                "code": b["code"],
                "title": b.get("title", b["code"]),
                "abbrev": b.get("abbrev", b["code"]),
                "section": b.get("section", ""),
                "ch_count": b.get("ch_count", 0),
                "note_count": len(notes or []),
                "sort_order": b.get("sort_order", 9999),
            }
        )
    return {"books": out}


def api_sources_for_book(book_code: str) -> dict:
    """Return every note for one book in canonical (chapter, verse) order
    along with its source attribution. The core verification view.

    Note tuple shape (positional):
        (chapter, verse, suffix, anchor, kind, title, label, body, attribution)
    """
    try:
        book = config.get_book(book_code)
    except KeyError:
        return {"error": f"unknown book: {book_code}"}
    if not book:
        return {"error": f"unknown book: {book_code}"}
    path = NOTES_DIR / f"{book_code}.py"
    if not path.is_file():
        return {"book": book_code, "notes": []}

    raw = notes_io.load_notes(path) or []
    kinds_idx = config.kinds_by_code()
    cats_idx = config.categories_by_id()

    out = []
    for i, tup in enumerate(raw):
        if len(tup) < 9:
            continue
        ch, vs, suffix, anchor, kind, title, label, body, attribution = tup[:9]
        kind_def = kinds_idx.get(kind, {})
        cat_id = kind_def.get("category", "?")
        cat_def = cats_idx.get(cat_id, {})
        # ρ.1 stable note ID — used by the per-note disable feature
        note_id = note_id_from_tuple(book_code, tup)
        out.append(
            {
                "index": i,
                "note_id": note_id,
                "chapter": ch,
                "verse": vs,
                "suffix": suffix or "",
                "anchor": anchor or "",
                "kind": kind,
                "kind_label": kind_def.get("label", kind),
                "category": cat_id,
                "category_label": cat_def.get("label", cat_id),
                "category_symbol": cat_def.get("symbol", "?"),
                "label": label,
                "title": title,
                "body": body,
                "attribution": attribution or "",
            }
        )
    # Already in canonical order in NOTES list, but enforce defensively
    out.sort(key=lambda n: (n["chapter"], n["verse"], n["suffix"]))
    return {
        "book": book_code,
        "title": book.get("title", book_code),
        "ch_count": book.get("ch_count", 0),
        "notes": out,
    }


def api_sources_summary() -> dict:
    """Return a high-level summary of the sources/attributions across the
    whole corpus. Used by the Sources Navigator's overview panel."""
    books = config.load_books()
    total_notes = 0
    notes_with_attribution = 0
    by_kind: dict[str, int] = {}
    by_book_section: dict[str, int] = {}
    # Naive source-string frequency map (the attribution is free-form text)
    source_freq: dict[str, int] = {}

    for b in books:
        path = NOTES_DIR / f"{b['code']}.py"
        notes = notes_io.load_notes(path) if path.is_file() else []
        if not notes:
            continue
        section = b.get("section", "?")
        by_book_section[section] = by_book_section.get(section, 0) + len(notes)
        for tup in notes:
            if len(tup) < 9:
                continue
            total_notes += 1
            kind = tup[4]
            by_kind[kind] = by_kind.get(kind, 0) + 1
            attr = (tup[8] or "").strip()
            if attr:
                notes_with_attribution += 1
                # Tokenize on common separators to extract source names
                # (rough — a free-text field, but useful for an overview)
                for chunk in re.split(r"[;,]\s*", attr):
                    chunk = chunk.strip()
                    if chunk:
                        source_freq[chunk] = source_freq.get(chunk, 0) + 1

    # Top sources, sorted by frequency
    top_sources = sorted(source_freq.items(), key=lambda x: -x[1])[:30]
    return {
        "total_notes": total_notes,
        "notes_with_attribution": notes_with_attribution,
        "by_section": by_book_section,
        "by_kind": dict(sorted(by_kind.items(), key=lambda x: -x[1])[:20]),
        "top_attribution_strings": [{"source": s, "count": n} for s, n in top_sources],
    }


# ============================================================
# Attribution Audit API (Phase ξ.4) — quality control on sources
# ============================================================


_THIN_ATTR_PATTERNS = (
    re.compile(r"^see\s", re.I),
    re.compile(r"^cf\.?\s", re.I),
    re.compile(r"^ibid", re.I),
    re.compile(r"^author$", re.I),
)


def _classify_attribution(attr: str) -> str:
    """Bucket an attribution string into one of:
    'missing'  — empty/whitespace, no attribution at all
    'thin'     — present but suspiciously short or vague
    'user'     — user-original / user-paraphrase (legitimate but flag)
    'sourced'  — references a real outside source (best case)
    """
    s = (attr or "").strip()
    if not s:
        return "missing"
    if any(p.match(s) for p in _THIN_ATTR_PATTERNS):
        return "thin"
    if len(s) < 12:
        return "thin"
    s_low = s.lower()
    if s_low.startswith("user original") or s_low.startswith("user paraphrase"):
        return "user"
    return "sourced"


def api_attribution_audit() -> dict:
    """Phase ξ.4 — quality-control read endpoint.

    Cached on the signature of all notes files + kinds/categories/books
    (Phase φ.1). Stays in sync with edits automatically because every
    note write updates the file's mtime.
    """
    return _cached_attribution_audit(
        _notes_dir_signature(),
        _files_signature(REPO / "content" / "kinds.yaml"),
        _files_signature(REPO / "content" / "categories.yaml"),
        _files_signature(REPO / "content" / "books.yaml"),
    )


def _compute_attribution_audit_uncached() -> dict:
    """Scan every note in the corpus and classify its attribution.

    Returns counts + a flat list of notes that need attention
    (missing or thin), each with an anchor that can be cross-linked
    to /sources for editing.
    """
    books = config.load_books()
    kinds_idx = config.kinds_by_code()
    cats_idx = config.categories_by_id()

    counts = {"total": 0, "missing": 0, "thin": 0, "user": 0, "sourced": 0}
    needs_attention = []  # missing + thin notes, in canonical order

    for book in books:
        code = book["code"]
        path = NOTES_DIR / f"{code}.py"
        if not path.is_file():
            continue
        notes = notes_io.load_notes(path) or []
        for _i, tup in enumerate(notes):
            if len(tup) < 9:
                continue
            ch, vs, suffix, anchor, kind, title, label, body, attribution = tup[:9]
            counts["total"] += 1
            cls = _classify_attribution(attribution or "")
            counts[cls] = counts.get(cls, 0) + 1
            if cls in ("missing", "thin"):
                kind_def = kinds_idx.get(kind, {})
                cat_id = kind_def.get("category", "?")
                cat_def = cats_idx.get(cat_id, {})
                needs_attention.append(
                    {
                        "book": code,
                        "book_title": book.get("title", code),
                        "section": book.get("section", ""),
                        "chapter": ch,
                        "verse": vs,
                        "suffix": suffix or "",
                        "kind": kind,
                        "kind_label": kind_def.get("label", kind),
                        "category": cat_id,
                        "category_symbol": cat_def.get("symbol", "?"),
                        "title": title,
                        "body_preview": (body or "")[:120],
                        "attribution": (attribution or "").strip(),
                        "classification": cls,
                    }
                )

    # Per-book counts of notes needing attention (for the left rail)
    by_book: dict[str, dict] = {}
    for item in needs_attention:
        b = item["book"]
        if b not in by_book:
            by_book[b] = {
                "code": b,
                "title": item["book_title"],
                "section": item["section"],
                "missing": 0,
                "thin": 0,
            }
        by_book[b][item["classification"]] += 1
    by_book_list = sorted(by_book.values(), key=lambda x: -(x["missing"] + x["thin"]))

    # Per-kind counts of notes needing attention
    by_kind: dict[str, int] = {}
    for item in needs_attention:
        by_kind[item["kind"]] = by_kind.get(item["kind"], 0) + 1
    by_kind_list = sorted(by_kind.items(), key=lambda x: -x[1])

    return {
        "counts": counts,
        "needs_attention": needs_attention,
        "by_book": by_book_list,
        "by_kind": [{"kind": k, "count": n} for k, n in by_kind_list],
    }


# ============================================================
# Publisher Console API (Phase π.1) — full publishing metadata per edition
# ============================================================
#
# Stored as flat fields in editions.yaml (backward-compat: missing fields
# fall back to sensible defaults from build_onix). The π.2 phase will
# wire these into the EPUB build pipeline.

# Sensible defaults applied when an edition has no publishing data yet.
# These match what build_onix.py currently hardcodes, so behavior on the
# next build is identical until the user explicitly edits.
# Ω.0 pivot (2026-05-14): isbn_epub / isbn_print removed — project
# is no longer for sale, so commercial identifiers are unnecessary.
PUBLISHING_DEFAULTS = {
    "publisher_name": "Independent",
    "publisher_url": "",
    "copyright_year": str(datetime.now(timezone.utc).year),
    "copyright_holder": "",
    "copyright_notice": "All rights reserved.",
    "publication_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    "language_code": "en",
    "cover_credit": "",
    "source_text_credit": ("Scripture text based on the World English Bible (public domain)."),
}

# These are list-typed fields — stored as YAML sub-lists.
PUBLISHING_LIST_FIELDS = ("authors", "bisac_codes")

# Single-line text fields (length max varies).
PUBLISHING_TEXT_LIMITS = {
    "publisher_name": 200,
    "publisher_url": 500,
    "copyright_year": 10,
    "copyright_holder": 200,
    "copyright_notice": 500,
    "publication_date": 30,
    "language_code": 12,
    "cover_credit": 200,
    "source_text_credit": 500,
}


def api_publisher_data() -> dict:
    """Phase π.1 — publisher console feed. Cached on editions.yaml mtime."""
    return _cached_publisher_data(
        _files_signature(REPO / "content" / "editions.yaml"),
    )


def _compute_publisher_data_uncached() -> dict:
    """Return all editions' publishing metadata for the /publisher UI.

    Each edition row includes both its existing meta (id, title) and
    its publishing fields (with defaults filled in for missing values
    so the UI can show the user what would actually be used at build).
    """
    editions = config.load_editions()
    out = []
    for e in editions:
        row = {
            "id": e["id"],
            "title": e.get("title", e["id"]),
            "short_title": e.get("short_title", ""),
            # Ω.0 pivot (2026-05-14): isbn_legacy / isbn_epub / isbn_print
            # all dropped. The edition URN is derived from id at render time.
        }
        for field, default in PUBLISHING_DEFAULTS.items():
            row[field] = e.get(field, default)
        for lf in PUBLISHING_LIST_FIELDS:
            row[lf] = list(e.get(lf) or [])
        out.append(row)
    return {"editions": out}

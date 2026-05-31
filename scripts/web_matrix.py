#!/usr/bin/env python3
"""
web_matrix.py — matrix grid + edition-diff JSON API handlers,
extracted from scripts/web.py in the god-module split (2026-05-26).

Pure relocation: every handler here was moved verbatim from
``scripts/web.py``. ``scripts/web.py`` re-exports every name so the
route table + external importers keep resolving them in web.py's
namespace.
"""

from __future__ import annotations

import functools

from scripts.core import config
from scripts.web_helpers import (
    REPO,
    _canons_index,
    _files_signature,
    _notes_dir_signature,
)


@functools.lru_cache(maxsize=16)
def _cached_edition_diff(a_id, b_id, eds_sig, kinds_sig, cats_sig, canons_sig, books_sig, notes_sig):
    return _compute_edition_diff_uncached(a_id, b_id)


def api_matrix() -> dict:
    """Return the symbol-toggle count grid as JSON. Read-only (μ.1)."""
    from scripts.core import matrix as matrix_mod

    m = matrix_mod.compute_matrix()
    cats = config.load_categories()
    kinds = config.load_kinds()
    editions = config.load_editions()
    # ψ.18.1: per-book chapter counts (from books.yaml's ch_count)
    # so the JS sidebar can render full-width chapter sparklines.
    book_ch_counts = {b["code"]: int(b.get("ch_count") or 0) for b in config.load_books()}
    return {
        "categories": [
            {
                "id": c["id"],
                "label": c.get("label", c["id"]),
                "symbol": c.get("symbol", "?"),
                "description": c.get("description", ""),
                "sort_order": c.get("sort_order", 999),
            }
            for c in cats
        ],
        "kinds": [
            {
                "code": k["code"],
                "category": k.get("category", "?"),
                "label": k.get("label", k["code"]),
            }
            for k in kinds
        ],
        "editions": [
            {
                "id": e["id"],
                "title": e.get("title", e["id"]),
                "short_title": e.get("short_title", e["id"]),
                "canon": e.get("canon"),
                "enabled_categories": e.get("enabled_categories") or [],
                "enabled_kinds": e.get("enabled_kinds") or [],
                "disabled_kinds": e.get("disabled_kinds") or [],
            }
            for e in editions
        ],
        "matrix": _api_matrix_per_edition(m, book_ch_counts),
    }


def _api_matrix_per_edition(m, book_ch_counts: dict[str, int]) -> dict:
    """ψ.35-B3 — build the per-edition slice of the api_matrix JSON
    response. Extracted into a helper for clarity now that the bound
    accessor calls per edition have made the comprehension less
    readable inline.

    The per-edition shape is the JSON contract the JS UI depends on
    (matrix sidebar, per-book sparkline, per-chapter drilldown).
    Pinned by ``TestPsi35B3ApiMatrixMigration``."""
    # ψ.35-B3 — was: `for ed_id in m.enabled` reading the raw
    # projection's keyset. Switched to `m.edition_canon_books` which
    # has the same keyset (both are populated from editions.yaml).
    # Per-edition values now derive from the accessor API where
    # possible; `per_book` and `per_chapter` still read raw (the
    # whole-edition nested-dict shape needs a dedicated accessor that
    # ψ.35-B3 deliberately defers — see CHANGELOG).
    out: dict = {}
    for ed_id in m.edition_canon_books:
        # ψ.35-B3 — was: `m.enabled[ed_id]` / `m.potential[ed_id]`.
        enabled_dict = m.enabled_kinds_dict(ed_id)
        potential_dict = m.potential_kinds_dict(ed_id)
        out[ed_id] = {
            "enabled": enabled_dict,
            "potential": potential_dict,
            "total_enabled": sum(enabled_dict.values()),
            "total_potential": sum(potential_dict.values()),
            "canon_books_count": len(m.edition_canon_books[ed_id]),
            "enabled_kinds_count": len(m.edition_enabled_kinds[ed_id]),
            "enabled_kinds_set": sorted(m.edition_enabled_kinds[ed_id]),
            # ψ.18: per-kind, per-book counts (potential scope — all
            # kinds in canon, regardless of enabled state). The JS
            # sidebar sums across LOCAL_ENABLED for a live total, and
            # renders the per-book counts as sparklines.
            # ψ.35-B4 — was: `m.per_book.get(ed_id, {})`. The new
            # `per_book_kinds_dict` accessor derives the same shape
            # from the canonical per_chapter store; once ψ.35-Final
            # ships, the `per_book` field on Matrix is removed and
            # only the accessor remains.
            "per_book": m.per_book_kinds_dict(ed_id),
            # ψ.18.1: per-kind, per-book, per-chapter counts — third
            # drilldown level on the totals sidebar. Same potential
            # scope as per_book; chapter keys ride out as JSON strings
            # (JavaScript object keys). `per_chapter` IS the canonical
            # store — stays as raw read across all of ψ.35.
            "per_chapter": m.per_chapter.get(ed_id, {}),
            # Canon book order (for sparkline column ordering)
            "canon_book_order": [b["code"] for b in config.load_books() if b["code"] in m.edition_canon_books[ed_id]],
            # ψ.18.1: per-book chapter counts so the chapter sparkline
            # knows the book's full width. Flat dict is fine — every
            # edition shares the same book set.
            "book_chapter_counts": {
                code: book_ch_counts[code] for code in m.edition_canon_books[ed_id] if code in book_ch_counts
            },
        }
    return out


def api_matrix_for_edition(edition_id: str) -> dict:
    """Phase ψ.36-A — per-edition matrix slice (the lazy-load endpoint).

    Same per-edition payload as ``api_matrix()['matrix'][edition_id]``
    plus the categories + kinds + this-one-edition metadata so the
    client can render a standalone view without a second
    ``/api/matrix`` round-trip. Targets the 200K-note ceiling lift
    framing of AUDIT_2026-05-11: instead of returning the whole
    matrix on every render, fetch only what the user is viewing.

    Today's corpus (51K notes) doesn't strictly need this — the
    full ``/api/matrix`` response is ~2 MB and renders fine — but
    the endpoint is a foundation the JS UI can adopt incrementally
    as corpus growth justifies it. Existing /api/matrix consumers
    are unaffected.

    Returns:
        {
            "edition": {id, title, short_title, canon, enabled_categories,
                        enabled_kinds, disabled_kinds},
            "categories": [...],     # same shape as /api/matrix
            "kinds": [...],          # same shape as /api/matrix
            "matrix": {...},         # the per-edition slot
        }

    Returns ``{"error": "unknown edition"}`` (HTTP 404 via route
    adapter) when the edition_id isn't in editions.yaml.
    """
    from scripts.core import matrix as matrix_mod

    eds_by_id = config.editions_by_id()
    if edition_id not in eds_by_id:
        return {"error": f"unknown edition: {edition_id}", "http": 404}

    m = matrix_mod.compute_matrix()
    cats = config.load_categories()
    kinds = config.load_kinds()
    edition = eds_by_id[edition_id]
    book_ch_counts = {b["code"]: int(b.get("ch_count") or 0) for b in config.load_books()}
    # Reuse the helper that builds /api/matrix's per-edition slot.
    per_edition_full = _api_matrix_per_edition(m, book_ch_counts)
    slot = per_edition_full.get(edition_id, {})
    return {
        "edition": {
            "id": edition_id,
            "title": edition.get("title", edition_id),
            "short_title": edition.get("short_title", edition_id),
            "canon": edition.get("canon"),
            "enabled_categories": edition.get("enabled_categories") or [],
            "enabled_kinds": edition.get("enabled_kinds") or [],
            "disabled_kinds": edition.get("disabled_kinds") or [],
        },
        "categories": [
            {
                "id": c["id"],
                "label": c.get("label", c["id"]),
                "symbol": c.get("symbol", "?"),
                "description": c.get("description", ""),
                "sort_order": c.get("sort_order", 999),
            }
            for c in cats
        ],
        "kinds": [
            {
                "code": k["code"],
                "category": k.get("category", "?"),
                "label": k.get("label", k["code"]),
            }
            for k in kinds
        ],
        "matrix": slot,
    }


def _diff_edition_summary(ed: dict, mtx, kinds_idx: dict, books_idx: dict, canons_idx: dict) -> dict:
    """One edition's side of the diff — headline metadata plus
    pre-computed totals so the UI doesn't have to re-derive them.
    """
    ed_id = ed["id"]
    # ψ.35-B2 — was: `mtx.enabled.get(ed_id, {})`. Accessor returns
    # the same shape from the canonical per_chapter store.
    enabled = mtx.enabled_kinds_dict(ed_id)
    canon_books = mtx.edition_canon_books.get(ed_id, set())
    enabled_kinds = mtx.edition_enabled_kinds.get(ed_id, set())
    canon_id = ed.get("canon", "")
    canon_def = canons_idx.get(canon_id, {}) or {}
    return {
        "id": ed_id,
        "title": ed.get("title", ed_id),
        "short_title": ed.get("short_title", ed_id),
        "audience": ed.get("target_audience", ""),
        # Ω.0 pivot: isbn dropped; URN derived from id. term-ref-ok
        "imprint": ed.get("imprint", ""),
        "canon_id": canon_id,
        "canon_label": canon_def.get("label", canon_id),
        "totals": {
            "books": len(canon_books),
            "kinds": len(enabled_kinds),
            "notes": sum(enabled.values()),
        },
    }


def _diff_books_section(a_books: set, b_books: set, books_idx: dict) -> dict:
    """Per-book diff: which books ship in A but not B and vice-versa.
    Sorted by canonical book ordering (the order in books.yaml)."""
    book_order = list(books_idx.keys())  # books.yaml order is canonical
    order_rank = {code: i for i, code in enumerate(book_order)}

    def _format(code_set):
        rows = []
        for code in sorted(code_set, key=lambda c: order_rank.get(c, 9999)):
            b = books_idx.get(code, {})
            rows.append(
                {
                    "code": code,
                    "title": b.get("title", code),
                }
            )
        return rows

    return {
        "only_a": _format(a_books - b_books),
        "only_b": _format(b_books - a_books),
        "both_count": len(a_books & b_books),
    }


def _diff_kinds_section(a_id: str, b_id: str, mtx, kinds_idx: dict, cats_idx: dict) -> dict:
    """Per-kind diff with shipping counts. Three buckets:
       only_a   — kinds enabled in A but not B (with A's count)
       only_b   — kinds enabled in B but not A (with B's count)
       shared   — kinds enabled in both, with both counts and the delta
    Within each bucket, sort by category sort_order, then by descending
    count so the most prominent differences appear first.
    """
    a_kinds = mtx.edition_enabled_kinds.get(a_id, set())
    b_kinds = mtx.edition_enabled_kinds.get(b_id, set())
    # ψ.35-B2 — was: `mtx.enabled.get(a_id, {})` / `mtx.enabled.get(b_id, {})`.
    a_counts = mtx.enabled_kinds_dict(a_id)
    b_counts = mtx.enabled_kinds_dict(b_id)

    def _row(code, a_n=None, b_n=None):
        k = kinds_idx.get(code, {}) or {}
        cat_id = k.get("category", "?")
        cat = cats_idx.get(cat_id, {}) or {}
        row = {
            "code": code,
            "label": k.get("label", code),
            "category": cat_id,
            "category_label": cat.get("label", cat_id),
            "category_sort": cat.get("sort_order", 999),
            "symbol": k.get("symbol") or cat.get("symbol", "?"),
        }
        if a_n is not None:
            row["a_count"] = a_n
        if b_n is not None:
            row["b_count"] = b_n
        return row

    only_a = [_row(c, a_n=a_counts.get(c, 0)) for c in a_kinds - b_kinds]
    only_b = [_row(c, b_n=b_counts.get(c, 0)) for c in b_kinds - a_kinds]
    shared = []
    for c in a_kinds & b_kinds:
        a_n = a_counts.get(c, 0)
        b_n = b_counts.get(c, 0)
        r = _row(c, a_n=a_n, b_n=b_n)
        r["delta"] = a_n - b_n
        shared.append(r)

    only_a.sort(key=lambda r: (r["category_sort"], -r.get("a_count", 0)))
    only_b.sort(key=lambda r: (r["category_sort"], -r.get("b_count", 0)))
    # shared: largest absolute count-difference first (most newsworthy)
    shared.sort(key=lambda r: (-abs(r["delta"]), r["category_sort"]))

    return {"only_a": only_a, "only_b": only_b, "shared": shared}


def _diff_categories_section(a_id: str, b_id: str, kinds_idx: dict, cats_idx: dict, mtx) -> list:
    """Category-level rollup: total notes per category, A vs B.
    Includes every category that is non-zero in at least one side, plus
    every category that is enabled (zero-count) in either edition — so
    the UI can show "0 vs 142" stark gaps that are part of the story.
    """
    from scripts.core import matrix as matrix_mod

    a_by_cat = matrix_mod.breakdown_by_category(a_id)
    b_by_cat = matrix_mod.breakdown_by_category(b_id)

    cat_ids = set(a_by_cat) | set(b_by_cat)
    rows = []
    for cid in cat_ids:
        c = cats_idx.get(cid, {}) or {}
        rows.append(
            {
                "id": cid,
                "label": c.get("label", cid),
                "symbol": c.get("symbol", "?"),
                "sort_order": c.get("sort_order", 999),
                "a_count": a_by_cat.get(cid, 0),
                "b_count": b_by_cat.get(cid, 0),
            }
        )
    rows.sort(key=lambda r: r["sort_order"])
    return rows


def _diff_headline(a_summary: dict, b_summary: dict, books_section: dict, kinds_section: dict) -> str:
    """Plain-English one-line summary suitable for a buyer-demo opening
    slide. Picks the most recognisable difference — books-only-in-one
    side first, then kinds-only-in-one side, then total-note delta.
    """
    a_short = a_summary["short_title"]
    b_short = b_summary["short_title"]
    a_only_books = books_section["only_a"]
    b_only_books = books_section["only_b"]
    a_only_kinds = len(kinds_section["only_a"])
    b_only_kinds = len(kinds_section["only_b"])

    bits = []
    if a_only_books and not b_only_books:
        bits.append(
            f"{a_short} includes {len(a_only_books)} book{'s' if len(a_only_books) != 1 else ''} that {b_short} omits"
        )
    elif b_only_books and not a_only_books:
        bits.append(
            f"{b_short} includes {len(b_only_books)} book{'s' if len(b_only_books) != 1 else ''} that {a_short} omits"
        )
    elif a_only_books and b_only_books:
        bits.append(
            f"{a_short} adds {len(a_only_books)} book"
            f"{'s' if len(a_only_books) != 1 else ''} the other lacks; "
            f"{b_short} adds {len(b_only_books)}"
        )

    if a_only_kinds or b_only_kinds:
        bits.append(f"{a_only_kinds} note kinds are exclusive to {a_short}, {b_only_kinds} to {b_short}")

    a_tot = a_summary["totals"]["notes"]
    b_tot = b_summary["totals"]["notes"]
    if a_tot != b_tot:
        diff = abs(a_tot - b_tot)
        bigger = a_short if a_tot > b_tot else b_short
        bits.append(f"{bigger} ships {diff} more notes overall")

    if not bits:
        return f"{a_short} and {b_short} are identical at the edition level."
    return " · ".join(bits) + "."


def api_edition_diff(a_id: str, b_id: str) -> dict:
    """Phase ξ.5 — sales-tool edition diff. Cached on the signature
    of every file involved in the diff computation."""
    return _cached_edition_diff(
        a_id,
        b_id,
        _files_signature(REPO / "content" / "editions.yaml"),
        _files_signature(REPO / "content" / "kinds.yaml"),
        _files_signature(REPO / "content" / "categories.yaml"),
        _files_signature(REPO / "content" / "canons.yaml"),
        _files_signature(REPO / "content" / "books.yaml"),
        _notes_dir_signature(),
    )


def _compute_edition_diff_uncached(a_id: str, b_id: str) -> dict:
    """Side-by-side diff between two editions (Phase ξ.5).

    Pure read-only view — no writes anywhere. Powers the "Catholic vs
    Evangelical: what's different" demo slide a sales rep can pull up
    in front of a publisher buyer in two clicks.

    Errors:
        unknown edition id → 404-style {"error": ...}
        a_id == b_id       → returns a valid diff (all bins empty); the
                              UI is responsible for nudging the user.
    """
    from scripts.core import matrix as matrix_mod

    eds = config.editions_by_id()
    if a_id not in eds:
        return {"error": f"unknown edition: {a_id}"}
    if b_id not in eds:
        return {"error": f"unknown edition: {b_id}"}

    mtx = matrix_mod.compute_matrix()
    kinds_idx = config.kinds_by_code()
    cats_idx = config.categories_by_id()
    books_idx = config.books_by_code()
    canons_idx = _canons_index()

    a = _diff_edition_summary(eds[a_id], mtx, kinds_idx, books_idx, canons_idx)
    b = _diff_edition_summary(eds[b_id], mtx, kinds_idx, books_idx, canons_idx)

    a_books = mtx.edition_canon_books.get(a_id, set())
    b_books = mtx.edition_canon_books.get(b_id, set())

    books_section = _diff_books_section(a_books, b_books, books_idx)
    kinds_section = _diff_kinds_section(a_id, b_id, mtx, kinds_idx, cats_idx)
    cats_section = _diff_categories_section(a_id, b_id, kinds_idx, cats_idx, mtx)
    headline = _diff_headline(a, b, books_section, kinds_section)

    # Light index for the picker dropdown (id + display name only).
    editions_index = [
        {"id": e["id"], "short_title": e.get("short_title", e["id"]), "title": e.get("title", e["id"])}
        for e in config.load_editions()
    ]

    return {
        "a": a,
        "b": b,
        "books": books_section,
        "kinds": kinds_section,
        "categories": cats_section,
        "headline": headline,
        "editions_index": editions_index,
    }

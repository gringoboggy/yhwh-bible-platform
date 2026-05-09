"""scripts.core.matrix — count grid for the symbol-toggle dev tool (Phase μ.0).

This module computes "if I shipped edition X right now, how many notes
of each kind would actually appear in it?" — answering the question
the symbol-toggle UI needs to display in every cell.

Inputs (all read via cached config loaders):
    content/books.yaml      — 87 books
    content/kinds.yaml      — 63 kinds with category mapping
    content/categories.yaml — 14 categories
    content/editions.yaml   — 5 edition profiles (kind filters + canon)
    content/canons.yaml     — canon → book-codes
    content/notes/*.py      — actual notes (1,371 today, growing)

Output shape (the "matrix"):

    {
        "edition_id": {
            "kind_code": int,    # how many notes of this kind would
                                  # ship in this edition
            ...
        },
        ...
    }

Scoping rules applied:
    1. A note only counts toward an edition if its book is in that
       edition's canon.
    2. A note only counts toward an edition if its kind is enabled
       (per enabled_categories + enabled_kinds + disabled_kinds).
    3. Disabled kinds always show 0 — useful for the UI to display
       "if you toggled this on, you'd gain N notes."

The 3rd rule means we ALSO produce a "potential" matrix that ignores
the edition's filter — so the UI can show both "currently in" and
"could be added" side by side.

Public API:
    compute_matrix() -> Matrix
    note_counts_for_edition(edition_id) -> dict[kind_code, int]
    total_for_edition(edition_id) -> int
    breakdown_by_category(edition_id) -> dict[category_id, int]
    potential_for_kind(kind_code, edition_id) -> int
        Count of notes of `kind_code` whose books are in
        `edition_id`'s canon — REGARDLESS of whether the kind is
        currently enabled. Powers "if you toggled this on..." UX.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from scripts.core import config, notes_io


# ----------------------------------------------------------------------
# Data classes
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class Matrix:
    """The full count grid plus useful pre-computed views.

    `enabled` is the actual ship counts (filter applied).
    `potential` is the same but ignoring the kind filter — i.e.,
    notes of this kind in books that are in the canon, period.
    The difference is the "would gain" column for the UI.

    ψ.18 — `per_book_enabled` adds a per-book dimension to
    `enabled` so the matrix sidebar can render counts at three
    levels (whole-edition / per-book / per-chapter via
    derivation) plus a sparkline showing which books contain
    each kind.
    """
    enabled: dict[str, dict[str, int]] = field(default_factory=dict)   # ed → kind → count
    potential: dict[str, dict[str, int]] = field(default_factory=dict)  # ed → kind → count
    edition_canon_books: dict[str, set[str]] = field(default_factory=dict)  # ed → set[book_code]
    edition_enabled_kinds: dict[str, set[str]] = field(default_factory=dict)  # ed → set[kind_code]
    # ψ.18: ed → kind → book → count.
    # Scope mirrors `potential` (any kind that has notes in canon —
    # NOT filtered by enabled state) so the matrix UI's JS can sum
    # across LOCAL_ENABLED for a live count that reflects pending
    # toggles. Only books that have notes-of-this-kind appear; books
    # with zero notes-of-this-kind are absent (not stored as 0).
    per_book: dict[str, dict[str, dict[str, int]]] = field(default_factory=dict)


# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------


def _load_canons() -> dict:
    """Read content/canons.yaml. Mirrors build_edition.load_canons but
    lives in core so we don't pull in build_edition's heavier surface."""
    canons_path = Path(__file__).resolve().parent.parent.parent / "content" / "canons.yaml"
    if not canons_path.is_file():
        return {}
    import yaml
    data = yaml.safe_load(canons_path.read_text(encoding="utf-8")) or {}
    return data.get("canons", {}) or {}


def _enabled_kinds_for_edition(edition: dict, all_kinds: Iterable[dict]) -> set[str]:
    """Apply enabled_categories + enabled_kinds + disabled_kinds to
    produce the final set of kind codes that would ship in this edition.

    Mirrors the logic in build_edition.filter_html so the matrix view
    matches what actually gets built. Same precedence:
      1. start from kinds in enabled_categories
      2. add kinds in enabled_kinds
      3. remove kinds in disabled_kinds
    """
    enabled_cats = set(edition.get("enabled_categories") or [])
    explicit_enabled = set(edition.get("enabled_kinds") or [])
    explicit_disabled = set(edition.get("disabled_kinds") or [])

    out: set[str] = set()
    for k in all_kinds:
        if k.get("category") in enabled_cats:
            out.add(k["code"])
    out |= explicit_enabled
    out -= explicit_disabled
    return out


def _canon_books_for_edition(edition: dict, canons: dict) -> set[str]:
    """Look up the book set for this edition's canon. Empty set if
    no canon declared — caller can choose to fall back to all books."""
    canon_id = edition.get("canon")
    if not canon_id:
        return set()
    canon_def = canons.get(canon_id) or {}
    return set(canon_def.get("books") or [])


def _count_kinds_in_book(notes_path: Path) -> dict[str, int]:
    """Read one book's notes file and return {kind_code: count}.

    Uses notes_io.load_notes which is LRU-cached on (path, mtime).
    Tuple shape: (chapter, verse, suffix, anchor, kind, label, title, body, attr).
    Kind is at index 4.
    """
    if not notes_path.is_file():
        return {}
    notes = notes_io.load_notes(notes_path)
    if not notes:
        return {}
    counts: dict[str, int] = {}
    for tup in notes:
        if len(tup) >= 5:
            kind = tup[4]
            counts[kind] = counts.get(kind, 0) + 1
    return counts


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


@lru_cache(maxsize=1)
def compute_matrix() -> Matrix:
    """Build the full count grid for all 5 editions × all 63 kinds.

    Cached for the life of the process. Call ``compute_matrix.cache_clear()``
    after editing notes / editions / canons to refresh.

    One pass over all 87 books, accumulating into the grid. O(N) in the
    total note count regardless of how many editions or kinds exist.
    Today: ~1,371 notes, well under 1 second. Projected at 25k notes:
    still well under 1 second since we never re-read books.
    """
    books = config.load_books()
    kinds = config.load_kinds()
    editions = config.load_editions()
    canons = _load_canons()

    notes_dir = Path(__file__).resolve().parent.parent.parent / "content" / "notes"

    # Pre-compute per-edition canon and enabled-kinds sets
    edition_canon: dict[str, set[str]] = {}
    edition_enabled: dict[str, set[str]] = {}
    for ed in editions:
        ed_id = ed["id"]
        edition_canon[ed_id] = _canon_books_for_edition(ed, canons)
        edition_enabled[ed_id] = _enabled_kinds_for_edition(ed, kinds)

    # Read each book's notes ONCE; distribute counts to every edition
    enabled: dict[str, dict[str, int]] = {ed["id"]: {} for ed in editions}
    potential: dict[str, dict[str, int]] = {ed["id"]: {} for ed in editions}
    # ψ.18: per-edition, per-kind, per-book counts (potential scope —
    # every kind, every book in canon, regardless of edition's
    # enabled-kind toggles). The JS sidebar sums across the user's
    # LOCAL_ENABLED so toggles affect counts live without re-fetching.
    per_book: dict[str, dict[str, dict[str, int]]] = {
        ed["id"]: {} for ed in editions
    }

    for book in books:
        code = book["code"]
        per_kind = _count_kinds_in_book(notes_dir / f"{code}.py")
        if not per_kind:
            continue
        # Distribute this book's counts to every edition that includes it
        for ed in editions:
            ed_id = ed["id"]
            if code not in edition_canon[ed_id]:
                continue
            # potential = all of this book's notes in canon scope
            for kind_code, n in per_kind.items():
                potential[ed_id][kind_code] = potential[ed_id].get(kind_code, 0) + n
                # ψ.18: per-book breakdown for every kind in canon
                per_book[ed_id].setdefault(kind_code, {})[code] = n
            # enabled = filtered down to active kinds (totals only)
            for kind_code, n in per_kind.items():
                if kind_code in edition_enabled[ed_id]:
                    enabled[ed_id][kind_code] = enabled[ed_id].get(kind_code, 0) + n

    return Matrix(
        enabled=enabled,
        potential=potential,
        edition_canon_books=edition_canon,
        edition_enabled_kinds=edition_enabled,
        per_book=per_book,
    )


def note_counts_for_edition(edition_id: str) -> dict[str, int]:
    """Return {kind_code: count} for the actually-shipping notes
    in this edition. Disabled kinds are absent (treat as 0)."""
    return dict(compute_matrix().enabled.get(edition_id, {}))


def total_for_edition(edition_id: str) -> int:
    """Sum of all enabled kinds' counts for this edition."""
    return sum(compute_matrix().enabled.get(edition_id, {}).values())


def breakdown_by_category(edition_id: str) -> dict[str, int]:
    """{category_id: total_notes_in_that_category} for this edition.
    Useful for the bar-visualization view in μ.2."""
    counts = note_counts_for_edition(edition_id)
    kinds_index = config.kinds_by_code()
    out: dict[str, int] = {}
    for kind_code, n in counts.items():
        cat = kinds_index.get(kind_code, {}).get("category", "?")
        out[cat] = out.get(cat, 0) + n
    return out


def potential_for_kind(kind_code: str, edition_id: str) -> int:
    """How many notes of `kind_code` would ship if this kind were
    toggled ON for this edition. Powers the "you'd gain N notes" UX."""
    return compute_matrix().potential.get(edition_id, {}).get(kind_code, 0)

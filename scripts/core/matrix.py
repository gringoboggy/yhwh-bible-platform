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

    ψ.18 — `per_book` adds a per-book dimension to the count grid
    so the matrix sidebar can render whole-edition + per-book
    levels with a sparkline.

    ψ.18.1 — `per_chapter` adds the third level: ed → kind → book
    → chapter → count. Same scope as `per_book` (potential — every
    kind in canon, regardless of enabled toggles) so the JS can
    drill down from a kind row into its chapter distribution
    without a server round-trip.
    """

    enabled: dict[str, dict[str, int]] = field(default_factory=dict)  # ed → kind → count
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
    # ψ.18.1: ed → kind → book → chapter → count.
    # Same scope as per_book; chapters with zero notes-of-this-kind
    # are absent. Chapter keys are ints in Python; JSON serialization
    # promotes them to strings (the JS sidebar handles either).
    per_chapter: dict[str, dict[str, dict[str, dict[int, int]]]] = field(default_factory=dict)


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
      4. **χ-AI-notes second gate**: AI-drafted kinds (currently just
         `comm-ai`) are removed unless the edition has
         `enable_ai_notes: true`. This is a deliberate double-opt-in:
         the kind being in `enabled_kinds` is necessary but not
         sufficient. The toggle exists because shipping AI-drafted
         content is a stronger commitment than shipping any other
         kind class — the publisher should have to confirm twice.
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

    # χ-AI-notes — strip AI-drafted kinds unless explicitly enabled.
    # Defaults to filtering OUT (no behavioral change for any
    # pre-χ-AI-notes edition that didn't set the flag).
    if not edition.get("enable_ai_notes"):
        out -= AI_DRAFTED_KINDS
    return out


# Kinds whose content is generated by an LLM at corpus time and
# shipped only after human review. Filtered out by
# `_enabled_kinds_for_edition` unless the edition opts in via
# `enable_ai_notes: true`. Single-element today; declared as a set
# so future AI-drafted kinds (illustration prompts, summary
# headers, etc.) are gated through one place.
AI_DRAFTED_KINDS: frozenset[str] = frozenset({"comm-ai"})


def _canon_books_for_edition(edition: dict, canons: dict) -> set[str]:
    """Look up the book set for this edition's canon. Empty set if
    no canon declared — caller can choose to fall back to all books."""
    canon_id = edition.get("canon")
    if not canon_id:
        return set()
    canon_def = canons.get(canon_id) or {}
    return set(canon_def.get("books") or [])


def _count_kinds_in_book(
    notes_path: Path,
) -> tuple[dict[str, int], dict[str, dict[int, int]]]:
    """Read one book's notes file and return per-kind counts plus
    per-kind chapter distributions.

    Returns ``(totals, per_chapter)`` where:
        - ``totals``     = {kind_code: total_count_in_book}
        - ``per_chapter`` = {kind_code: {chapter_int: count}}

    Uses notes_io.load_notes which is LRU-cached on (path, mtime).
    Tuple shape: (chapter, verse, suffix, anchor, kind, label, title, body, attr).
    Chapter is at index 0; kind at index 4.

    ψ.18.1 — extended to return per-chapter distribution alongside
    totals so the matrix sidebar can drill down to chapter level.
    """
    if not notes_path.is_file():
        return {}, {}
    notes = notes_io.load_notes(notes_path)
    if not notes:
        return {}, {}
    totals: dict[str, int] = {}
    per_chapter: dict[str, dict[int, int]] = {}
    for tup in notes:
        if len(tup) >= 5:
            ch = tup[0]
            kind = tup[4]
            totals[kind] = totals.get(kind, 0) + 1
            chap_dict = per_chapter.setdefault(kind, {})
            chap_dict[ch] = chap_dict.get(ch, 0) + 1
    return totals, per_chapter


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


@lru_cache(maxsize=1)
def compute_matrix() -> Matrix:
    """Build the full count grid for all editions × all kinds.

    Cached for the life of the process. Call
    ``compute_matrix.cache_clear()`` after editing notes /
    editions / canons to refresh.

    Δ.4.1 (2026-05-10) — wire-flip attempted twice (once raw,
    once with Δ.0 file lock); both reverted. Even with the lock
    serializing writes, every `compute_matrix()` call triggers a
    fingerprint stat-walk + potential rebuild at the corpus_index
    layer, which interacts badly with the test suite's expectation
    of a memory-cached compute_matrix. A clean wire-flip needs
    additional design work — likely either (a) cache the
    fingerprint check itself, or (b) make corpus_index lazily
    rebuild only on explicit invalidation rather than on every
    `connection()` call. Deferred. The Δ.4
    `compute_matrix_indexed()` implementation works correctly when
    called directly; the wire flip is the open piece.
    """
    return _compute_matrix_via_file_walk()


def _compute_matrix_via_file_walk() -> Matrix:
    """File-walk implementation. Walks every notes/<book>.py file
    once via ``_count_kinds_in_book`` and distributes counts into
    the per-edition projections.

    Retained under this name (separate from the public
    ``compute_matrix``) so the Δ.4 equivalence test can compare
    the file-walk reference to ``corpus_index.compute_matrix_indexed()``
    even though `compute_matrix` itself currently delegates to
    the file-walk path.
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
    per_book: dict[str, dict[str, dict[str, int]]] = {ed["id"]: {} for ed in editions}
    # ψ.18.1: third level — per-chapter breakdown. Same scope; lets
    # the sidebar drill from a kind row into chapter distribution.
    per_chapter: dict[str, dict[str, dict[str, dict[int, int]]]] = {ed["id"]: {} for ed in editions}

    for book in books:
        code = book["code"]
        per_kind, per_kind_chapters = _count_kinds_in_book(notes_dir / f"{code}.py")
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
                # ψ.18.1: per-chapter breakdown; copy to detach from
                # the helper's local dict so future calls can't mutate
                # cached state.
                chap_counts = per_kind_chapters.get(kind_code)
                if chap_counts:
                    per_chapter[ed_id].setdefault(kind_code, {})[code] = dict(chap_counts)
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
        per_chapter=per_chapter,
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

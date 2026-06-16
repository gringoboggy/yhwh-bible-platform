"""σ.1 — build-accurate edition statistics.

``resolved_note_counts()`` is THE source of truth for every "what you built"
surface (the cover / front-matter counts, the symbol glossary, the live
console). It reuses ``build_one``'s exact filter sets
(``build_edition.compute_edition_filter_sets``) so the printed numbers equal
the real EPUB and honor the ρ.3 hierarchical per-book / per-chapter / per-note
choices — by construction, not by re-deriving the filter logic.

A note ships iff it is in the edition's canon AND its kind is not whole-kind
stripped AND its ref-id is not in the per-edition disabled-ref-id set — exactly
the survival test ``filter_html`` applies. The slow cross-check in
``tests/test_edition_stats.py`` builds an EPUB and asserts the surviving
note-ref marker count equals ``resolved_note_counts(ed)["total"]``.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from scripts.core import config

_REF_ID_RE = re.compile(r'\bid="(ref-[^"]+)"')


@lru_cache(maxsize=1)
def _base_html_ref_ids() -> frozenset[str]:
    """The set of inline note-ref ids that physically exist in the base HTML
    (``epub_working/*.html``). A note ships only if its marker is present in the
    base — the build can never inject a marker for a coordinate the base lacks.

    This is THE difference between "the canon + hierarchy say this note is
    enabled" and "this note actually appears in the built EPUB": the documented
    base-coverage residual (e.g. the ``aes`` ch11-16 + ``1En`` 37-108 gaps) is
    notes that are on disk and in-canon but were never injected into the base,
    so no edition can ship them. Gating the counter on this set is what makes
    ``resolved_note_counts`` equal the real EPUB (see the slow cross-check pin
    in ``tests/test_edition_stats.py``). Edition-independent → cached once.
    """
    repo = Path(config.__file__).resolve().parents[2]
    base_dir = repo / "epub_working"
    out: set[str] = set()
    for html in base_dir.glob("*.html"):
        out |= set(_REF_ID_RE.findall(html.read_text(encoding="utf-8", errors="replace")))
    return frozenset(out)


def _edition_signature(edition_id: str) -> tuple:
    """A hashable fingerprint of every edition field that can change the
    resolved counts. Used as the lru_cache key so the cache invalidates when
    the edition record changes (a per-book OFF write, a canon swap, etc.) even
    though ``edition`` itself is an unhashable dict."""
    ed = config.editions_by_id().get(edition_id, {})
    keys = (
        "canon",
        "enabled_categories",
        "enabled_kinds",
        "disabled_kinds",
        "note_families_on_per_book",
        "note_families_off_per_book",
        "note_families_on_per_chapter",
        "note_families_off_per_chapter",
        "disabled_note_ids",
        "enabled_note_ids",
        "traditions",
        "traditions_default",
        "traditions_per_book",
        "time_period",
        "time_filter_ceiling",
        "popup_languages_default",
        "popup_languages_per_book",
        "popup_languages_per_chapter",
        "popup_languages_per_verse",
        "enable_ai_notes",
        "max_phase",
    )
    return tuple((k, repr(ed.get(k))) for k in keys)


def resolved_note_counts(edition: dict) -> dict:
    """Return the build-accurate note tally for one edition.

    Result keys::

        total            int                       notes that actually ship
        per_book         {book_code: count}        sums to total
        per_book_chapter {book_code: {ch: count}}  per-(book, chapter) tally;
                                                   the inner sums == per_book,
                                                   the grand sum == total
        per_category     {category_id: count}      sums to total
        per_kind         {kind_code: count}        sums to total
        popup_languages  sorted list[str]          every popup language that ships

    Honors the ρ.3 hierarchy because it reuses
    ``compute_edition_filter_sets`` — the same two sets ``filter_html`` strips
    with.
    """
    raw = _resolved_note_counts_cached(edition["id"], _edition_signature(edition["id"]))
    # Return a fresh copy: the cached object is shared across calls (lru_cache),
    # so handing out the live dict would let a consumer corrupt the cache. The
    # per_book_chapter inner dicts are copied too (nested mutable state).
    return {
        **raw,
        "per_book": dict(raw["per_book"]),
        "per_book_chapter": {bk: dict(chs) for bk, chs in raw["per_book_chapter"].items()},
        "per_category": dict(raw["per_category"]),
        "per_kind": dict(raw["per_kind"]),
        "popup_languages": list(raw["popup_languages"]),
    }


@lru_cache(maxsize=64)
def _resolved_note_counts_cached(edition_id: str, _sig: tuple) -> dict:
    from scripts.build_edition import (
        _iter_note_ref_symbols,
        _resolve_popup_languages,
        compute_edition_filter_sets,
    )
    from scripts.core import matrix as matrix_mod

    edition = config.editions_by_id()[edition_id]
    canon_books = matrix_mod.compute_matrix().edition_canon_books.get(edition_id, set())
    disabled_kinds, disabled_ref_ids = compute_edition_filter_sets(edition)
    base_ref_ids = _base_html_ref_ids()

    per_book: dict[str, int] = {}
    per_book_chapter: dict[str, dict[int, int]] = {}
    per_category: dict[str, int] = {}
    per_kind: dict[str, int] = {}
    total = 0
    # Yield shape (verified against build_edition._iter_note_ref_symbols):
    #   (ref_id, note_id, book_code, chapter, verse, suffix, kind, category)
    for ref_id, _note_id, book, ch, _vs, _suffix, kind, category in _iter_note_ref_symbols():
        if book not in canon_books:
            continue
        if kind in disabled_kinds:
            continue
        if ref_id in disabled_ref_ids:
            continue
        # Base-coverage gate: a note ships only if its marker physically exists
        # in the base HTML. Excludes the documented base-coverage residual
        # (on-disk + in-canon notes whose coordinates were never injected), so
        # the tally equals the real EPUB. See _base_html_ref_ids.
        if ref_id not in base_ref_ids:
            continue
        total += 1
        per_book[book] = per_book.get(book, 0) + 1
        # per-(book, chapter) tally: powers the /build-tracker heat-grid so the
        # live per-chapter density equals the built EPUB (σ.6.1). chapter is an
        # int from _iter_note_ref_symbols (int(tup[0])).
        bk_ch = per_book_chapter.setdefault(book, {})
        bk_ch[ch] = bk_ch.get(ch, 0) + 1
        per_kind[kind] = per_kind.get(kind, 0) + 1
        # category can be None if a kind lacks a registered category — bucket
        # those under "" so the per_category sum still equals total.
        cat_key = category if category is not None else ""
        per_category[cat_key] = per_category.get(cat_key, 0) + 1

    # Popup languages: the edition default plus whatever each canon book
    # resolves to (per-book overrides can widen the set). Sentinel book code
    # "\x00edition-default" is never a valid per-book key, so it falls through
    # to the default tier (matches web_editions.py's resolved_bible path).
    langs: set[str] = set(_resolve_popup_languages(edition, "\x00edition-default"))
    for bk in canon_books:
        langs |= set(_resolve_popup_languages(edition, bk))

    return {
        "total": total,
        "per_book": per_book,
        "per_book_chapter": per_book_chapter,
        "per_category": per_category,
        "per_kind": per_kind,
        "popup_languages": sorted(langs),
    }


def cache_clear() -> None:
    """Drop the memoized counts (call after mutating an edition record) and the
    base-HTML ref-id set (call after an ``epub_working/`` inject/bake)."""
    _resolved_note_counts_cached.cache_clear()
    _base_html_ref_ids.cache_clear()


resolved_note_counts.cache_clear = cache_clear  # type: ignore[attr-defined]

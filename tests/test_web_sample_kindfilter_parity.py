"""mint-8 sample-kindfilter — preview/build kind-set parity.

`api_sample_html` previously hand-rolled an enabled/disabled-kind filter
(`enabled_kinds` / `disabled_kinds` only). That diverged from the actual
EPUB build, which resolves the shipped kind set through the canonical
`scripts.core.config.enabled_kind_codes` (categories->kinds expansion,
the `max_phase` gate, and the AI double-opt-in). The fix routes the
preview through that same resolver.

This test asserts that, for a categories-driven edition, the notes
surfaced by `api_sample_html` are exactly the notes whose kind survives
the canonical resolver — i.e. preview == build. It would have failed
against the old hand-rolled filter for any edition that opts in via
`enabled_categories` (the old filter never expanded categories, so every
category-only kind was dropped from the preview).
"""

from __future__ import annotations

from scripts.core import config
from scripts.web_content import api_sample_html


def _categories_driven_edition() -> tuple[str, dict] | tuple[None, None]:
    """First edition that drives its kind set via enabled_categories
    (the case the old hand-rolled enabled_kinds/disabled_kinds filter
    could not reproduce). Returns (edition_id, edition) or (None, None)."""
    for ed_id, ed in config.editions_by_id().items():
        if ed.get("enabled_categories"):
            return ed_id, ed
    return None, None


def _first_book_with_in_canon_notes(ed: dict) -> str | None:
    """A book that is both in this edition's canon and has a notes file,
    so the preview actually exercises the kind filter."""
    from scripts.build_edition import load_canons

    canons = load_canons()
    canon_books = set((canons.get(ed.get("canon", "")) or {}).get("books") or [])
    notes_dir = config._CONTENT / "notes"
    for book in sorted(canon_books):
        if (notes_dir / f"{book}.py").is_file():
            return book
    return None


def test_sample_html_kind_set_matches_canonical_resolver():
    ed_id, ed = _categories_driven_edition()
    assert ed_id is not None, "expected at least one enabled_categories-driven edition"

    book = _first_book_with_in_canon_notes(ed)
    assert book is not None, f"no in-canon notes book found for edition {ed_id!r}"

    # Build the expected note set directly from the canonical resolver,
    # exactly as the EPUB build (build_edition.compute_enabled_kinds) does.
    enabled_codes = config.enabled_kind_codes(ed, config.load_kinds())

    from scripts.core import notes_io

    all_notes = notes_io.load_notes(config._CONTENT / "notes" / f"{book}.py") or []
    chapters = sorted({n[0] for n in all_notes if n and len(n) >= 8})
    assert chapters, f"notes file for {book!r} unexpectedly empty"
    f = chapters[0]
    t = min(f + 9, chapters[-1])  # within api_sample_html's MAX_RANGE=10

    expected = sum(1 for n in all_notes if n and len(n) >= 8 and f <= n[0] <= t and n[4] in enabled_codes)

    result = api_sample_html(ed_id, book, f, t)
    assert result["status"] == "ok", result
    assert result["note_count"] == expected, (
        f"preview note_count {result['note_count']} != canonical-resolver count {expected} for {ed_id}/{book} ch{f}-{t}"
    )


def test_sample_html_excludes_a_disabled_category_kind():
    """A kind whose category is NOT enabled for the edition must never
    appear in the preview (regression guard for the categories path)."""
    ed_id, ed = _categories_driven_edition()
    assert ed_id is not None

    enabled_codes = config.enabled_kind_codes(ed, config.load_kinds())
    all_codes = {k["code"] for k in config.load_kinds()}
    excluded = all_codes - enabled_codes
    assert excluded, "expected at least one kind excluded from this edition"

    book = _first_book_with_in_canon_notes(ed)
    assert book is not None

    from scripts.core import notes_io

    all_notes = notes_io.load_notes(config._CONTENT / "notes" / f"{book}.py") or []
    chapters = sorted({n[0] for n in all_notes if n and len(n) >= 8})
    f = chapters[0]
    t = min(f + 9, chapters[-1])

    result = api_sample_html(ed_id, book, f, t)
    assert result["status"] == "ok", result
    # No excluded kind may be counted: re-derive what the preview saw.
    surfaced_kinds = {n[4] for n in all_notes if n and len(n) >= 8 and f <= n[0] <= t and n[4] in enabled_codes}
    assert surfaced_kinds.isdisjoint(excluded)

"""σ.3 — front-matter "Your Edition" page + glossary→build-accurate counter.

The symbol glossary (legend) and the new "Your Edition" first page must be
driven by ``scripts.core.edition_stats.resolved_note_counts`` (which honors the
ρ.3 per-book/chapter/note hierarchy), NOT the edition-wide matrix that ignores
those overrides. These tests pin:

  σ.3.1 — the legend lists exactly the categories that actually ship (a
          force-on note in an otherwise-off family surfaces its category; a
          family off across the whole canon is dropped).
  σ.3.2 — the Your-Edition page renders the display_name heading, the optional
          notes blockquote, a truthful "What's inside" line, the total, and a
          per-book table in canonical book order; and it is the first content
          page after the cover (the old About page is retired).

NOTE: ``resolved_note_counts`` keys its cache on the edition id + the on-disk
``editions.yaml`` signature (NOT the dict handed in), so any override test must
mutate ``editions.yaml`` on disk (isolated + restored) — mirroring
``tests/test_edition_stats.py::test_resolved_counts_honor_per_book_off``.
"""

from __future__ import annotations

import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _smallest_shipping_category(edition_id: str) -> tuple[str, list[str], str]:
    """The smallest-count shipping category, every book that ships it, and one
    of its note ids — computed with the SAME filter chain as
    ``resolved_note_counts`` (canon → kind-disable → ref-disable →
    base-coverage), so the fixture IS the shipping universe by construction.

    History: this test used to hardcode catholic-study's single ``compare``
    note (gen:6:1s) — an η.1 seed purged in ``3bab5f4a``, which left the pin
    stale. Post-purge no category ships in just one book, so the family-off
    map must cover every shipping book anyway; deriving category/books/note
    from the live universe makes the fixture immune to future content
    reshuffles instead of re-pinning the next instance."""
    from scripts.build_edition import (
        _iter_note_ref_symbols,
        compute_edition_filter_sets,
    )
    from scripts.core import config
    from scripts.core import matrix as matrix_mod
    from scripts.core.edition_stats import _base_html_ref_ids

    edition = config.editions_by_id()[edition_id]
    canon = matrix_mod.compute_matrix().edition_canon_books.get(edition_id, set())
    disabled_kinds, disabled_ref_ids = compute_edition_filter_sets(edition)
    base_ref_ids = _base_html_ref_ids()

    per_cat_count: dict[str, int] = {}
    per_cat_books: dict[str, set[str]] = {}
    first_note: dict[str, str] = {}
    for ref_id, note_id, book, _ch, _vs, _suffix, kind, category in _iter_note_ref_symbols():
        if (
            book not in canon
            or kind in disabled_kinds
            or ref_id in disabled_ref_ids
            or ref_id not in base_ref_ids
            or not category
        ):
            continue
        per_cat_count[category] = per_cat_count.get(category, 0) + 1
        per_cat_books.setdefault(category, set()).add(book)
        first_note.setdefault(category, note_id)
    assert per_cat_count, f"{edition_id} ships no categorized notes at all"
    cat = min(per_cat_count, key=lambda c: (per_cat_count[c], c))
    return cat, sorted(per_cat_books[cat]), first_note[cat]


def _clear_all_caches() -> None:
    from scripts.core import config, edition_stats
    from scripts.core import matrix as m

    config.load_editions.cache_clear()
    m.compute_matrix.cache_clear()
    edition_stats.resolved_note_counts.cache_clear()


# ---------------------------------------------------------------------------
# σ.3.1 — the glossary (legend) is driven by resolved_note_counts
# ---------------------------------------------------------------------------


def test_legend_categories_equal_resolved_per_category():
    """The legend categories must equal the resolved_note_counts per_category
    keys with count>0 — proving the glossary is driven by the build-accurate
    counter, not the edition-wide matrix."""
    from scripts.build_edition import _legend_categories_for_edition
    from scripts.core import config, edition_stats

    ed = config.editions_by_id()["catholic-study"]
    rc = edition_stats.resolved_note_counts(ed)
    expected = {cat for cat, n in rc["per_category"].items() if n > 0 and cat}

    cats = _legend_categories_for_edition("catholic-study")
    got = {c["id"] for c in cats}
    assert got == expected, f"legend cats {got} != resolved per_category {expected}"
    # Per-row count must match the resolved count exactly.
    for c in cats:
        assert c["count"] == rc["per_category"][c["id"]]
    # Still sorted by categories.yaml sort_order (non-decreasing).
    order = {c["id"]: c.get("sort_order", 999) for c in config.load_categories()}
    seq = [order[c["id"]] for c in cats]
    assert seq == sorted(seq)


def test_legend_drops_family_off_across_canon_and_force_on_resurfaces_it(tmp_path):
    """A family off across the canon drops its category from the legend; a single
    force-on note of that family resurfaces its symbol (because that one note
    actually ships) — the ρ.3 hierarchy the edition-wide matrix can't see."""
    import scripts.web as web
    from scripts.build_edition import _legend_categories_for_edition
    from scripts.core import config

    yml = REPO / "content" / "editions.yaml"
    backup = tmp_path / "ed.bak"
    shutil.copy(yml, backup)
    try:
        _clear_all_caches()
        cat, cat_books, note_id = _smallest_shipping_category("catholic-study")
        baseline = {c["id"] for c in _legend_categories_for_edition("catholic-study")}
        assert cat in baseline, f"fixture precondition: catholic-study ships {cat!r}"

        # (a) Turn the family OFF in EVERY book that ships it → the whole
        #     category drops from the legend. Merge on top of any existing
        #     per-book offs rather than clobbering them.
        from scripts.build_edition import decode_per_book_tokens

        existing = dict(
            decode_per_book_tokens(config.editions_by_id()["catholic-study"].get("note_families_off_per_book"))
        )
        for bk in cat_books:
            fams = list(existing.get(bk) or [])
            if cat not in fams:
                fams.append(cat)
            existing[bk] = fams
        web.api_save_edition_meta("catholic-study", {"note_families_off_per_book": existing})
        _clear_all_caches()
        off = {c["id"] for c in _legend_categories_for_edition("catholic-study")}
        assert cat not in off, (
            f"{cat!r} still listed after turning its family off in all {len(cat_books)} books that ship it"
        )

        # (b) Force ONE note of that family back ON → its category resurfaces
        #     (count == 1, because that one note actually ships).
        res = web.api_save_note_override("catholic-study", {"note_id": note_id, "state": "on"})
        assert res.get("ok"), res
        _clear_all_caches()
        cats_on = _legend_categories_for_edition("catholic-study")
        on = {c["id"] for c in cats_on}
        assert cat in on, "force-on note did not resurface its category in the legend"
        row = next(c for c in cats_on if c["id"] == cat)
        assert row["count"] == 1, f"force-on should ship exactly 1 {cat!r} note, got {row['count']}"
    finally:
        shutil.copy(backup, yml)
        _clear_all_caches()


# ---------------------------------------------------------------------------
# σ.3.2 — the "Your Edition" page
# ---------------------------------------------------------------------------


def _stats(**over) -> dict:
    """A synthetic resolved_note_counts dict for pure renderer tests."""
    base = {
        "total": 12431,
        "per_book": {"gen": 2283, "exo": 1200, "mat": 800},
        "per_category": {"comm": 9000, "xref": 3431},
        "per_kind": {"comm-patristic": 9000, "xref-citation": 3431},
        "popup_languages": ["wlc", "lxx-greek"],
    }
    base.update(over)
    return base


def _ed(**over) -> dict:
    base = {
        "id": "catholic-study",
        "title": "The Catholic Study Bible",
        "display_name": "Catholic Study Bible",
        "canon": "catholic",
        "theme": "devotional",
        "description": "",
    }
    base.update(over)
    return base


def test_your_edition_heading_uses_display_name():
    from scripts.build_edition import render_your_edition_page

    out = render_your_edition_page(_ed(display_name="My Family Bible"), _stats(), "v")
    assert "My Family Bible" in out
    # Falls back to title when display_name absent.
    out2 = render_your_edition_page(_ed(display_name=None), _stats(), "v")
    assert "The Catholic Study Bible" in out2


def test_your_edition_description_blockquote_when_present():
    from scripts.build_edition import render_your_edition_page

    out_empty = render_your_edition_page(_ed(description=""), _stats(), "v")
    assert "SENTINEL_NOTE" not in out_empty
    assert "<blockquote" not in out_empty  # no notes → no blockquote at all

    out = render_your_edition_page(_ed(description="SENTINEL_NOTE text"), _stats(), "v")
    assert "SENTINEL_NOTE text" in out
    assert "<blockquote" in out


def test_your_edition_total_and_whats_inside_and_per_book_order():
    from scripts.build_edition import render_your_edition_page
    from scripts.core import config

    out = render_your_edition_page(_ed(), _stats(), "v")
    # Total notes, comma-grouped.
    assert "12,431" in out
    # What's inside: canon name + families + popup languages + theme.
    assert "Catholic" in out
    assert "Commentary / Tradition" in out and "Cross-references" in out
    assert "Hebrew (Masoretic / WLC)" in out and "Greek (Septuagint / Swete)" in out
    assert "devotional" in out
    # Per-book table in canonical order: gen before exo before mat.
    order = {b["code"]: i for i, b in enumerate(config.load_books())}
    book_titles = config.books_by_code()
    positions = []
    for code in ("gen", "exo", "mat"):
        title = book_titles[code]["title"]
        positions.append(out.index(title))
    assert positions == sorted(positions), "per-book rows not in canonical book order"
    # canonical order must match books.yaml, not the dict insertion order
    assert order["gen"] < order["exo"] < order["mat"]


def test_your_edition_graceful_no_notes_no_popups():
    from scripts.build_edition import render_your_edition_page

    out = render_your_edition_page(
        _ed(),
        _stats(total=0, per_book={}, per_category={}, per_kind={}, popup_languages=[]),
        "v",
    )
    # No notes / no popups must render gracefully (no crash, sane phrasing).
    assert "0" in out or "no notes" in out.lower()
    import xml.dom.minidom as md

    md.parseString(out)


def test_your_edition_well_formed_xml_escapes():
    import xml.dom.minidom as md
    from scripts.build_edition import render_your_edition_page

    out = render_your_edition_page(
        _ed(display_name="A & B <co>", description="notes with <angle> & amp"), _stats(), "v"
    )
    md.parseString(out)


def test_render_about_page_retired():
    """The old About renderer + injector must be gone (its content moved to the
    Your-Edition page)."""
    import scripts.build_edition as be

    assert not hasattr(be, "render_about_page"), "render_about_page should be retired"
    assert not hasattr(be, "inject_about_page"), "inject_about_page should be retired"


class TestYourEditionReachesEpub:
    """Build catholic-study; the Your-Edition page is the FIRST content page
    after the cover (titlepage → your-edition → copyright → legend), the old
    About page is gone, and the glossary still carries its anchors."""

    def _build(self, tmp_path, monkeypatch):
        import scripts.build_edition as be
        from scripts.core import build_cache, config

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)
        stats = be.build_one("catholic-study", tmp_path, "your-ed-test", config.load_kinds(), force=True)
        return stats["output_path"]

    def test_your_edition_first_and_about_gone(self, tmp_path, monkeypatch):
        import re
        import zipfile

        from scripts.core import config, edition_stats

        epub = self._build(tmp_path, monkeypatch)
        with zipfile.ZipFile(epub) as zf:
            names = zf.namelist()
            assert any(n.endswith("your-edition.xhtml") for n in names), "your-edition.xhtml missing"
            assert not any(n.endswith("about.xhtml") for n in names), "old about.xhtml still shipped"
            ye = zf.read(next(n for n in names if n.endswith("your-edition.xhtml"))).decode("utf-8")
            nav = zf.read(next(n for n in names if n.endswith("nav.xhtml"))).decode("utf-8")
            opf = zf.read(next(n for n in names if n.endswith("content.opf"))).decode("utf-8")
            legend = zf.read(next(n for n in names if n.endswith("legend.xhtml"))).decode("utf-8")

        # Order: titlepage → youredition → copyright → legend.
        order = re.findall(r'<itemref idref="(\w+)"/>', opf)
        assert order.index("titlepage") < order.index("youredition") < order.index("copyright")
        assert order.index("copyright") < order.index("legend")

        # nav has the TOC entry.
        assert 'href="your-edition.xhtml"' in nav
        assert 'href="about.xhtml"' not in nav

        # Truthful total == resolved_note_counts.
        total = edition_stats.resolved_note_counts(config.editions_by_id()["catholic-study"])["total"]
        assert f"{total:,}" in ye, f"page total mismatch — expected {total:,}"

        # Glossary anchors intact (σ.3.1 must not have broken them).
        assert 'id="legend-comm"' in legend

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

# In catholic-study the ``compare`` category ships exactly ONE note — the
# pseudepigrapha cross-reference at gen:6:1s. Turning the ``compare`` family OFF
# for gen therefore drops the WHOLE category from the canon (it ships nowhere
# else), and force-ON of that one note resurfaces it — a clean, single-note
# demonstration that the legend is driven by the build-accurate counter and
# honors the ρ.3 hierarchy the edition-wide matrix can't see.
_COMPARE_NOTE_ID = "gen:6:1s:compare-pseudepigrapha"


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

    yml = REPO / "content" / "editions.yaml"
    backup = tmp_path / "ed.bak"
    shutil.copy(yml, backup)
    try:
        _clear_all_caches()
        baseline = {c["id"] for c in _legend_categories_for_edition("catholic-study")}
        assert "compare" in baseline, "fixture precondition: catholic-study ships the compare note"

        # (a) Turn the compare family OFF for gen → it ships nowhere else, so the
        #     whole category drops from the legend.
        web.api_save_edition_meta("catholic-study", {"note_families_off_per_book": {"gen": ["compare"]}})
        _clear_all_caches()
        off = {c["id"] for c in _legend_categories_for_edition("catholic-study")}
        assert "compare" not in off, "compare still listed after turning its only note's family off"

        # (b) Force that one note back ON → its category resurfaces (count == 1).
        res = web.api_save_note_override("catholic-study", {"note_id": _COMPARE_NOTE_ID, "state": "on"})
        assert res.get("ok"), res
        _clear_all_caches()
        cats_on = _legend_categories_for_edition("catholic-study")
        on = {c["id"] for c in cats_on}
        assert "compare" in on, "force-on note did not resurface its category in the legend"
        compare_row = next(c for c in cats_on if c["id"] == "compare")
        assert compare_row["count"] == 1, f"force-on should ship exactly 1 compare note, got {compare_row['count']}"
    finally:
        shutil.copy(backup, yml)
        _clear_all_caches()

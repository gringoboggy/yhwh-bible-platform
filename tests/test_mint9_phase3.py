"""mint-9 (deep-audit round 2) Phase-3 guards — behavior-changing correctness.

#11 inject.find_aside_insertion_point used `existing_ch != ch` to decide an
    existing aside "precedes" the insertion, so in a Strategy-B SHARED notes
    section a HIGHER-chapter aside was treated as preceding → a re-injected
    lower-chapter note landed AFTER it. Fixed to a proper (ch, v, suffix)
    ordering compare. Byte-identical for single-chapter (Strategy-A) sections.

#12 api_save_edition computed its kind baseline from category membership ONLY,
    ignoring the phase + AI gates. A max_phase-limited edition therefore put
    phase-gated kinds into the computed disabled_kinds. Fixed via the new
    config.category_baseline_kinds (phase + AI gated).

#8  the copyright/about matter pages printed the matrix note total, which omits
    the tradition/time ref-id filters. SUPERSEDED by σ.6.2 (2026-06-04): the
    copyright page now reads edition_stats.resolved_note_counts directly, which
    honors the full ρ.3 hierarchy + the base-HTML coverage gate — strictly more
    accurate than the retired annotation_count_override. These tests now pin
    "copyright count == resolved total == legend category count".
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import matter_pages  # noqa: E402
from scripts.core import config  # noqa: E402
from scripts.inject import find_aside_insertion_point  # noqa: E402


# ---------------------------------------------------------------------------
# #11 — Strategy-B cross-chapter aside ordering
# ---------------------------------------------------------------------------


def _section(html: str) -> tuple[int, int]:
    """The whole string is the notes 'section' for these unit tests."""
    return (0, len(html))


def test_lower_chapter_note_lands_before_higher_chapter_aside() -> None:
    """A Strategy-B shared section holding ch-3 then ch-5 asides: inserting a
    ch-4 note must land BETWEEN them, not after the ch-5 aside (the #11 bug)."""
    prefix = "b13"  # 2 Chronicles bxx
    html = (
        '<aside class="note note-x" id="note-b130301a" epub:type="footnote">A</aside>\n'
        '<aside class="note note-x" id="note-b130501a" epub:type="footnote">B</aside>\n'
    )
    # Insert ch=4, v=1 — should land after the ch-3 aside's </aside>, before ch-5.
    pos = find_aside_insertion_point(html, _section(html), ch=4, v=1, suffix="", prefix=prefix)
    ch3_close = html.index("</aside>") + len("</aside>")
    ch5_start = html.index('id="note-b130501a"')
    assert ch3_close <= pos <= ch5_start, (
        f"ch-4 insertion {pos} not between ch-3 close ({ch3_close}) and ch-5 start ({ch5_start})"
    )


def test_strategy_a_single_chapter_ordering_unchanged() -> None:
    """For a single-chapter (Strategy-A) section the new compare is identical to
    the old one: a new v=2 note lands before an existing v=3 aside."""
    prefix = "g"  # Genesis id_prefix
    html = (
        '<aside class="note note-x" id="note-g0101a" epub:type="footnote">A</aside>\n'
        '<aside class="note note-x" id="note-g0103a" epub:type="footnote">C</aside>\n'
    )
    pos = find_aside_insertion_point(html, _section(html), ch=1, v=2, suffix="", prefix=prefix)
    v3_start = html.index('id="note-g0103a"')
    # v=2 must insert before the v=3 aside (at its <aside start).
    assert pos <= v3_start
    assert pos == html.index('<aside class="note note-x" id="note-g0103a"')


def test_higher_verse_in_same_chapter_inserts_before() -> None:
    """Same chapter, existing later verse → insert before it (regression check)."""
    prefix = "g"
    html = '<aside class="note note-x" id="note-g0105a" epub:type="footnote">E</aside>\n'
    pos = find_aside_insertion_point(html, _section(html), ch=1, v=2, suffix="", prefix=prefix)
    assert pos == 0  # before the only (later) aside


# ---------------------------------------------------------------------------
# #12 — category_baseline_kinds respects phase + AI gates
# ---------------------------------------------------------------------------


def test_category_baseline_excludes_later_phase_kinds() -> None:
    all_kinds = [
        {"code": "legacy-k", "category": "comm", "phase": "legacy"},
        {"code": "mvp-k", "category": "comm", "phase": "mvp"},
        {"code": "p3-k", "category": "comm", "phase": "phase3"},
    ]
    ed = {"id": "e", "enabled_categories": ["comm"], "max_phase": "mvp"}
    baseline = config.category_baseline_kinds(ed, all_kinds)
    assert "legacy-k" in baseline and "mvp-k" in baseline
    assert "p3-k" not in baseline, "phase3 kind must be gated out of a max_phase=mvp baseline"


def test_category_baseline_excludes_ai_kinds_without_optin() -> None:
    ai_code = next(iter(config.AI_DRAFTED_KINDS), None)
    if ai_code is None:
        import pytest

        pytest.skip("no AI_DRAFTED_KINDS registered")
    all_kinds = [{"code": ai_code, "category": "comm", "phase": "legacy"}]
    ed_no_ai = {"id": "e", "enabled_categories": ["comm"]}
    ed_ai = {"id": "e", "enabled_categories": ["comm"], "enable_ai_notes": True}
    assert ai_code not in config.category_baseline_kinds(ed_no_ai, all_kinds)
    assert ai_code in config.category_baseline_kinds(ed_ai, all_kinds)


def test_category_baseline_unknown_phase_raises() -> None:
    import pytest

    with pytest.raises(ValueError, match="unknown max_phase"):
        config.category_baseline_kinds(
            {"id": "e", "enabled_categories": ["comm"], "max_phase": "nope"},
            [{"code": "k", "category": "comm", "phase": "legacy"}],
        )


# ---------------------------------------------------------------------------
# #8 — copyright counts via the build-accurate counter (σ.6.2)
# ---------------------------------------------------------------------------
#
# RETIRED (σ.6.2, 2026-06-04): the mint-9 #8 ``annotation_count_override`` param
# (and build_one's _annot_override / _count_in_scope_disabled_ref_ids block) are
# gone. inject_copyright_page now reads edition_stats.resolved_note_counts
# directly — which honors the FULL ρ.3 hierarchy (per-book/chapter/note
# overrides) AND the base-HTML coverage gate, strictly subsuming the old
# tradition/time-only correction. The tests below pin the new contract: the
# printed copyright count == resolved total, and the printed category count ==
# the symbol legend's category count (== Your-Edition total).


def _copyright_counts(tmp_path, edition) -> tuple[int, int]:
    """Run inject_copyright_page into an empty temp dir (the OPF/nav patches
    no-op without those files) and parse back the rendered annotation count +
    category count from copyright.xhtml."""
    import re

    matter_pages.inject_copyright_page(tmp_path, edition, "v28a")
    text = (tmp_path / "copyright.xhtml").read_text(encoding="utf-8")
    m = re.search(r"carries <strong>([\d,]+)</strong> annotations across <strong>(\d+) categories", text)
    assert m, f"could not parse copyright counts from:\n{text}"
    return int(m.group(1).replace(",", "")), int(m.group(2))


def test_copyright_count_equals_resolved_total(tmp_path) -> None:
    """The printed annotation count == edition_stats.resolved_note_counts total
    (build-accurate; == the real EPUB)."""
    from scripts.core import edition_stats

    ed = config.editions_by_id()["catholic-study"]
    expected_total = edition_stats.resolved_note_counts(ed)["total"]
    ann, _cat = _copyright_counts(tmp_path, ed)
    assert ann == expected_total


def test_copyright_category_count_matches_legend(tmp_path) -> None:
    """The printed category count == the symbol legend's category count (both
    derive from resolved_note_counts per_category, count>0) — even for an
    override edition that zeroes a category."""
    import shutil

    from scripts.core import config as cfg
    from scripts.core import edition_stats
    from scripts.matter_pages import _legend_categories_for_edition

    yml = REPO_ROOT / "content" / "editions.yaml"
    backup = tmp_path / "ed.bak"
    shutil.copy(yml, backup)

    def _clear():
        cfg.load_editions.cache_clear()
        from scripts.core import matrix as m

        m.compute_matrix.cache_clear()
        edition_stats.resolved_note_counts.cache_clear()

    try:
        _clear()
        import scripts.web as web

        # Drop a whole category edition-wide so legend + copyright must agree on
        # the reduced category count, not just the unfiltered default.
        web.api_save_edition_meta("catholic-study", {"disabled_kinds": ["xref"]})
        _clear()

        ed = cfg.editions_by_id()["catholic-study"]
        _ann, cat = _copyright_counts(tmp_path, ed)
        legend_cats = len(_legend_categories_for_edition("catholic-study"))
        assert cat == legend_cats, f"copyright {cat} categories != legend {legend_cats}"
    finally:
        shutil.copy(backup, yml)
        _clear()


def test_render_copyright_renders_given_count() -> None:
    """render_copyright_page renders whatever annotation_count it's given — the
    inject_* layer is what now sources it from resolved_note_counts."""
    eds = config.editions_by_id()
    ed = eds.get("catholic-study") or next(iter(eds.values()))
    pub = matter_pages._resolve_publishing(ed)
    html_full = matter_pages.render_copyright_page(ed, pub, "v28a", annotation_count=41881, category_count=5)
    html_filtered = matter_pages.render_copyright_page(ed, pub, "v28a", annotation_count=40000, category_count=5)
    assert "41,881" in html_full or "41881" in html_full
    assert "40,000" in html_filtered or "40000" in html_filtered


if __name__ == "__main__":  # pragma: no cover
    import pytest

    sys.exit(pytest.main([__file__, "-q"]))

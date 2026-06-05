from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_filter_sets_helper_exists_and_shapes():
    from scripts.build_edition import compute_edition_filter_sets
    from scripts.core import config

    ed = config.editions_by_id()["catholic-study"]
    disabled_kinds, disabled_ref_ids = compute_edition_filter_sets(ed)
    assert isinstance(disabled_kinds, set)
    assert isinstance(disabled_ref_ids, set)


# ---------------------------------------------------------------------------
# σ.1.2 — resolved_note_counts (the build-accurate counter)
# ---------------------------------------------------------------------------


def test_resolved_counts_match_no_override_edition():
    from scripts.core import edition_stats, config

    ed = config.editions_by_id()["catholic-study"]
    rc = edition_stats.resolved_note_counts(ed)
    assert rc["total"] > 0
    assert sum(rc["per_book"].values()) == rc["total"]
    assert sum(rc["per_category"].values()) == rc["total"]
    assert sum(rc["per_kind"].values()) == rc["total"]
    assert isinstance(rc["popup_languages"], list)
    # σ.6.1 — per-(book, chapter) tally: every grand sum == total, and each
    # book's inner-chapter sum == that book's per_book count.
    pbc = rc["per_book_chapter"]
    assert sum(sum(chs.values()) for chs in pbc.values()) == rc["total"]
    for bk, n in rc["per_book"].items():
        assert sum(pbc.get(bk, {}).values()) == n, f"per_book_chapter[{bk}] sum != per_book"


def test_resolved_counts_honor_per_book_off(tmp_path):
    import shutil

    import scripts.web as web
    from scripts.core import config, edition_stats

    yml = REPO_ROOT / "content" / "editions.yaml"
    backup = tmp_path / "ed.bak"
    shutil.copy(yml, backup)
    try:
        config.load_editions.cache_clear()
        before = edition_stats.resolved_note_counts(config.editions_by_id()["catholic-study"])
        web.api_save_edition_meta("catholic-study", {"note_families_off_per_book": {"gen": ["xref"]}})
        config.load_editions.cache_clear()
        from scripts.core import matrix as m

        m.compute_matrix.cache_clear()
        edition_stats.resolved_note_counts.cache_clear()
        after = edition_stats.resolved_note_counts(config.editions_by_id()["catholic-study"])
        assert after["total"] < before["total"]
        assert after["per_book"].get("gen", 0) < before["per_book"]["gen"]
    finally:
        shutil.copy(backup, yml)
        config.load_editions.cache_clear()
        from scripts.core import matrix as m2

        m2.compute_matrix.cache_clear()
        edition_stats.resolved_note_counts.cache_clear()


def _count_note_ref_markers_in_epub(epub_path) -> int:
    """Count surviving inline note-ref markers across the EPUB's content files.

    The build emits exactly one ``<a class="note-ref note-{kind}" id="ref-…">``
    marker per shipped note (scripts.inject.build_marker) IN ``numbers`` mode.
    Asides use ``class="note note-{kind}"`` and the legend page uses
    ``class="legend-…"`` — neither matches the ``class="note-ref `` token, so this
    counts only the inline note-ref markers, i.e. exactly the notes that ship.
    (This cross-check builds in ``numbers`` mode on purpose: ``badge`` mode — the
    default — collapses a verse's markers into one count badge, so the per-note
    marker proxy only holds in ``numbers`` mode. Which notes SHIP is identical in
    both modes; only the inline display differs.)
    """
    import zipfile

    needle = 'class="note-ref '
    total = 0
    with zipfile.ZipFile(epub_path) as zf:
        for name in zf.namelist():
            low = name.lower()
            if not (low.endswith(".html") or low.endswith(".xhtml") or low.endswith(".htm")):
                continue
            text = zf.read(name).decode("utf-8", "replace")
            total += text.count(needle)
    return total


def _build_catholic_study_and_count_note_refs(tmp_path, monkeypatch) -> int:
    import scripts.build_edition as be
    from scripts.core import build_cache, config
    from pathlib import Path

    monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
    monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)

    # Build in numbers mode so each shipped note carries its inline note-ref
    # marker — the proxy this cross-check counts (badge mode, the default,
    # collapses them per verse).
    eds = dict(config.editions_by_id())
    ed = dict(eds["catholic-study"])
    ed["marker_style"] = "numbers"
    eds["catholic-study"] = ed
    monkeypatch.setattr(config, "editions_by_id", lambda: eds)

    all_kinds = config.load_kinds()
    stats = be.build_one("catholic-study", tmp_path, "stats-xcheck", all_kinds, force=True)
    epub = Path(stats["output_path"])
    assert epub.is_file(), f"build produced no EPUB at {epub}"
    return _count_note_ref_markers_in_epub(epub)


@pytest.mark.slow
def test_resolved_total_equals_built_epub_note_count(tmp_path, monkeypatch):
    from scripts.core import config, edition_stats

    expected = edition_stats.resolved_note_counts(config.editions_by_id()["catholic-study"])["total"]
    built = _build_catholic_study_and_count_note_refs(tmp_path, monkeypatch)
    assert built == expected, f"resolved {expected} != built EPUB {built}"

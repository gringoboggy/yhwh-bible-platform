"""Torrey + Nave's topical-index merge — unit/render/mode pins."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


class _Hit:
    def __init__(self, b, c, v):
        self.target_book, self.target_chapter, self.target_verse = b, c, v


class _FakeSource:
    """Stub of NavesTopical / TorreyTopical with the index-building surface."""

    def __init__(self, topics):
        self._t = topics  # {topic: [(book, ch, vs), ...]}

    def topics(self):
        return sorted(self._t)

    def verses_for(self, topic):
        return [_Hit(*r) for r in self._t.get(topic, [])]


BOOK_ORDER = {"gen": 0, "exo": 1, "mat": 50, "tob": 80}


class TestTopicHelpers:
    def test_norm_topic_casefolds_collapses_ws_strips_edges(self):
        from scripts.matter_pages import _norm_topic

        assert _norm_topic("  ASSURANCE  ") == "assurance"
        assert _norm_topic("Affections, The") == "affections, the"  # comma preserved
        assert _norm_topic("Faith.") == "faith"

    def test_title_topic_titlecases_allcaps_and_hyphens(self):
        from scripts.matter_pages import _title_topic

        assert _title_topic("AARON") == "Aaron"
        assert _title_topic("ABED-NEGO") == "Abed-Nego"
        assert _title_topic("GOD'S WILL") == "God's Will"

    def test_topical_index_sources_constant(self):
        from scripts.matter_pages import TOPICAL_INDEX_SOURCES

        assert set(TOPICAL_INDEX_SOURCES) == {"both", "naves", "torrey"}


class TestBuildMergedTopicIndex:
    def _idx(self, naves, torrey, canon=None):
        from scripts.matter_pages import build_merged_topic_index

        return build_merged_topic_index(
            _FakeSource(naves) if naves is not None else None,
            _FakeSource(torrey) if torrey is not None else None,
            canon_books=canon,
            book_order=BOOK_ORDER,
        )

    def test_both_sides_tag_NT_and_union_deduped_ordered(self):
        idx = self._idx(
            {"Assurance": [("mat", 8, 10), ("gen", 15, 6)]},
            {"Assurance": [("gen", 15, 6), ("exo", 14, 13)]},  # gen dup collapses
        )
        assert idx == [("Assurance", "N·T", [("gen", 15, 6), ("exo", 14, 13), ("mat", 8, 10)])]

    def test_naves_only_tag_N_titlecased_display(self):
        idx = self._idx({"AARON": [("exo", 4, 14)]}, {})
        assert idx == [("Aaron", "N", [("exo", 4, 14)])]

    def test_torrey_only_tag_T_verbatim_display(self):
        idx = self._idx({}, {"Adoption": [("gen", 1, 1)]})
        assert idx == [("Adoption", "T", [("gen", 1, 1)])]

    def test_casefold_match_merges_caps_variants_prefers_torrey_casing(self):
        idx = self._idx({"ASSURANCE": [("gen", 1, 1)]}, {"Assurance": [("exo", 1, 1)]})
        assert idx == [("Assurance", "N·T", [("gen", 1, 1), ("exo", 1, 1)])]

    def test_canon_filter_drops_out_of_canon_and_omits_empty_topic(self):
        idx = self._idx(
            {"FAITH": [("tob", 2, 1), ("gen", 15, 6)], "TOBIT-ONLY": [("tob", 1, 1)]},
            {},
            canon={"gen", "exo", "mat"},
        )
        d = dict((t, refs) for t, _tag, refs in idx)
        assert "Tobit-Only" not in d  # all refs out of canon -> omitted
        assert d["Faith"] == [("gen", 15, 6)]

    def test_canon_makes_tag_T_when_only_torrey_has_in_canon_refs(self):
        # Nave's has the name but its only ref is out of canon -> tag reflects
        # in-edition verse presence (T), not mere name presence.
        idx = self._idx({"Grace": [("tob", 3, 1)]}, {"Grace": [("gen", 6, 8)]}, canon={"gen"})
        assert idx == [("Grace", "T", [("gen", 6, 8)])]

    def test_sorted_alphabetically_by_display_casefold(self):
        idx = self._idx({"ZEAL": [("gen", 1, 1)], "ABEL": [("gen", 4, 2)]}, {"Mercy": [("gen", 1, 1)]})
        assert [t for t, _tag, _refs in idx] == ["Abel", "Mercy", "Zeal"]

    def test_both_sources_none_returns_empty(self):
        assert self._idx(None, None) == []


class TestRenderMerged:
    def test_default_naves_intro_byte_stable(self):
        from scripts.matter_pages import render_topical_index_page

        out = render_topical_index_page([("FAITH", [("gen", 15, 6)])], book_abbrev=str.title)
        assert "after Nave&#x2019;s Topical Bible (Orville J. Nave, 1896; public domain)" in out
        ET.fromstring(out)

    def test_torrey_intro_param_overrides(self):
        from scripts.matter_pages import _TORREY_TOPICAL_INTRO, render_topical_index_page

        out = render_topical_index_page(
            [("Adoption", [("gen", 1, 1)])], book_abbrev=str.title, intro=_TORREY_TOPICAL_INTRO
        )
        assert "Torrey" in out
        assert "after Nave" not in out
        ET.fromstring(out)

    def test_merged_render_has_tags_intro_and_is_wellformed(self):
        from scripts.matter_pages import render_merged_topical_index_page

        idx = [("Assurance", "N·T", [("gen", 15, 6)]), ("Adoption", "T", [("mat", 8, 10)])]
        out = render_merged_topical_index_page(idx, book_abbrev=str.title)
        ET.fromstring(out)  # well-formed XHTML
        assert "Nave" in out and "Torrey" in out
        assert "(N·T)" in out and "(T)" in out
        assert "Assurance" in out and "Gen 15:6" in out
        assert "topic-src" in out

    def test_merged_render_empty_index_valid(self):
        from scripts.matter_pages import render_merged_topical_index_page

        ET.fromstring(render_merged_topical_index_page([], book_abbrev=str.title))


class TestWriteTopicalPage:
    """The mode branch in isolation — writes topical.xhtml, returns topical_ok."""

    def _call(self, tmp_path, mode, *, naves, torrey):
        from scripts.matter_pages import _write_topical_page

        ok = _write_topical_page(
            tmp_path,
            mode,
            canon_books=None,
            book_order=BOOK_ORDER,
            naves=_FakeSource(naves) if naves is not None else None,
            torrey=_FakeSource(torrey) if torrey is not None else None,
        )
        page = (tmp_path / "topical.xhtml").read_text(encoding="utf-8") if ok else ""
        return ok, page

    def test_both_mode_writes_merged_with_tags(self, tmp_path):
        ok, page = self._call(tmp_path, "both", naves={"AARON": [("exo", 4, 14)]}, torrey={"Adoption": [("gen", 1, 1)]})
        assert ok
        assert "(N)" in page and "(T)" in page and "Torrey" in page

    def test_naves_mode_writes_single_source_no_tags(self, tmp_path):
        ok, page = self._call(
            tmp_path, "naves", naves={"AARON": [("exo", 4, 14)]}, torrey={"Adoption": [("gen", 1, 1)]}
        )
        assert ok
        assert "after Nave" in page
        assert "topic-src" not in page  # no tags in single-source mode
        assert "Adoption" not in page  # Torrey excluded

    def test_torrey_mode_uses_torrey_intro(self, tmp_path):
        ok, page = self._call(
            tmp_path, "torrey", naves={"AARON": [("exo", 4, 14)]}, torrey={"Adoption": [("gen", 1, 1)]}
        )
        assert ok and "Torrey" in page and "Adoption" in page

    def test_both_mode_degrades_to_naves_when_torrey_missing(self, tmp_path):
        ok, page = self._call(tmp_path, "both", naves={"AARON": [("exo", 4, 14)]}, torrey=None)
        assert ok
        assert "after Nave" in page and "topic-src" not in page  # byte-compat naves path

    def test_both_mode_degrades_to_torrey_when_naves_missing(self, tmp_path):
        ok, page = self._call(tmp_path, "both", naves=None, torrey={"Adoption": [("gen", 1, 1)]})
        assert ok and "Torrey" in page

    def test_both_missing_writes_nothing_returns_false(self, tmp_path):
        ok, _ = self._call(tmp_path, "both", naves=None, torrey=None)
        assert ok is False
        assert not (tmp_path / "topical.xhtml").exists()

    def test_unset_mode_defaults_to_both(self, tmp_path):
        ok, page = self._call(tmp_path, None, naves={"AARON": [("exo", 4, 14)]}, torrey={"Adoption": [("gen", 1, 1)]})
        assert ok and "topic-src" in page


class TestSourcesPageCreditsTorrey:
    def test_sources_page_lists_both_topical_works(self):
        from scripts.matter_pages import render_sources_page

        out = render_sources_page()
        ET.fromstring(out)
        assert "Nave" in out  # pre-existing
        assert "Torrey&#x2019;s New Topical Textbook" in out
        assert "R.A. Torrey, 1897" in out


class TestConfigField:
    def test_reexported_from_build_edition(self):
        from scripts.build_edition import TOPICAL_INDEX_SOURCES

        assert set(TOPICAL_INDEX_SOURCES) == {"both", "naves", "torrey"}

    def test_validator_rejects_invalid(self):
        from scripts.api.editions import api_save_edition_meta

        res = api_save_edition_meta("catholic-study", {"topical_index_source": "bogus"})
        assert "error" in res and "topical_index_source" in res["error"]

    def test_accepts_and_persists_torrey(self):
        from scripts.api.editions import api_save_edition_meta

        edyaml = REPO / "content" / "editions.yaml"
        backup = edyaml.read_bytes()
        try:
            res = api_save_edition_meta("catholic-study", {"topical_index_source": "torrey"})
            assert "error" not in res, res
            config.load_editions.cache_clear()
            assert config.editions_by_id()["catholic-study"].get("topical_index_source") == "torrey"
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()

    def test_api_customize_data_defaults_to_both(self):
        from scripts.web import api_customize_data

        eds = {e["id"]: e for e in api_customize_data()["editions"]}
        assert eds["catholic-study"].get("topical_index_source") == "both"

    def test_customize_template_has_the_select(self):
        src = (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        assert 'data-field="topical_index_source"' in src

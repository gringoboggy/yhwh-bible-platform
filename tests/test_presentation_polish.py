"""EPUB presentation polish (2026-05-24) — front matter, reader guide, CSS fixes.
Spec: docs/superpowers/specs/2026-05-24-epub-presentation-polish-design.md.
NOTE: this work INTENTIONALLY changes built output — pin the NEW output, do not
assume byte-identity."""

from __future__ import annotations

from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
BASE_CSS = REPO / "epub_working" / "stylesheet.css"


class TestLeftAlign:
    def test_base_stylesheet_has_no_justified_body_text(self):
        css = BASE_CSS.read_text(encoding="utf-8")
        assert "text-align: justify" not in css, (
            "justified body text still present — stretches short lines in Apple Books"
        )

    def test_base_stylesheet_drops_hyphenation_with_justify(self):
        css = BASE_CSS.read_text(encoding="utf-8")
        assert "hyphens: auto" not in css
        assert "-webkit-hyphens: auto" not in css


class TestCoverFit:
    def test_cover_img_fits_frame(self):
        css = BASE_CSS.read_text(encoding="utf-8")
        assert "object-fit: contain" in css, "cover image missing object-fit: contain"
        assert "max-height: 100%" in css, "cover image missing a height cap"


class TestColophon:
    def _pub(self):
        return {
            "publisher_name": "YHWH Ya' Way Editions",
            "copyright_year": "2026",
            "copyright_holder": "Bogdan Zorlescu",
        }

    def test_no_todo_placeholders(self):
        from scripts.build_edition import render_copyright_page

        out = render_copyright_page(
            {"id": "catholic-study", "title": "Cath"}, self._pub(), "v", annotation_count=12345, category_count=9
        )
        assert "TODO_" not in out

    def test_no_stale_hardcoded_count(self):
        from scripts.build_edition import render_copyright_page

        out = render_copyright_page(
            {"id": "x", "title": "T"}, self._pub(), "v", annotation_count=12345, category_count=9
        )
        assert "1,371" not in out and "14 categories" not in out

    def test_real_counts_rendered(self):
        from scripts.build_edition import render_copyright_page

        out = render_copyright_page(
            {"id": "x", "title": "T"}, self._pub(), "v", annotation_count=12345, category_count=9
        )
        assert "12,345" in out and "9 categories" in out

    def test_identity_and_urn(self):
        from scripts.build_edition import render_copyright_page

        out = render_copyright_page(
            {"id": "catholic-study", "title": "T"}, self._pub(), "v", annotation_count=10, category_count=1
        )
        assert "Way Editions" in out and "Bogdan Zorlescu" in out and "2026" in out
        assert "urn:yhwh:edition:catholic-study" in out

    def test_no_long_description_on_colophon(self):
        from scripts.build_edition import render_copyright_page

        ed = {"id": "x", "title": "T", "description": "UNIQUE_DESC_SENTINEL_12321"}
        out = render_copyright_page(ed, self._pub(), "v", annotation_count=10, category_count=1)
        assert "UNIQUE_DESC_SENTINEL_12321" not in out

    def test_well_formed_xml(self):
        import xml.dom.minidom as md
        from scripts.build_edition import render_copyright_page

        out = render_copyright_page(
            {"id": "x", "title": "T & <co>"}, self._pub(), "v", annotation_count=10, category_count=1
        )
        md.parseString(out)


class TestSymbolLegendPure:
    def _cats(self):
        return [
            {
                "id": "comm",
                "symbol": "◇",
                "label": "Commentary / Tradition",
                "description": "Interpretive readings",
                "count": 100,
            },
            {"id": "topic", "symbol": "✦", "label": "Topical", "description": "Topical groupings", "count": 50},
        ]

    def test_renders_symbol_label_description_count(self):
        from scripts.build_edition import render_symbol_legend_page

        out = render_symbol_legend_page({"id": "x", "title": "T"}, self._cats(), "v")
        assert "A Guide to the Notes" in out
        for c in self._cats():
            assert c["symbol"] in out and c["label"] in out and c["description"] in out
        assert "100 notes" in out and "50 notes" in out

    def test_each_row_has_anchor_id(self):
        from scripts.build_edition import render_symbol_legend_page

        out = render_symbol_legend_page({"id": "x", "title": "T"}, self._cats(), "v")
        assert 'id="legend-comm"' in out and 'id="legend-topic"' in out

    def test_well_formed_xml(self):
        import xml.dom.minidom as md
        from scripts.build_edition import render_symbol_legend_page

        md.parseString(render_symbol_legend_page({"id": "x", "title": "T"}, self._cats(), "v"))


class TestLegendCategories:
    def test_edition_aware_only_present(self):
        from scripts.build_edition import _legend_categories_for_edition

        cats = _legend_categories_for_edition("jewish-study")
        assert cats, "jewish-study should have at least one category with notes"
        assert all(c["count"] > 0 for c in cats), "only categories with notes (>0) should appear"
        # sorted by categories.yaml sort_order (non-decreasing) — verify order is stable
        from scripts.core import config

        order = {c["id"]: c.get("sort_order", 999) for c in config.load_categories()}
        seq = [order[c["id"]] for c in cats]
        assert seq == sorted(seq)


class TestLegendReachesEpub:
    def test_legend_page_and_nav(self, tmp_path, monkeypatch):
        import zipfile
        import scripts.build_edition as be
        from scripts.core import build_cache, config

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)
        stats = be.build_one("catholic-study", tmp_path, "legend-test", config.load_kinds(), force=True)
        with zipfile.ZipFile(stats["output_path"]) as zf:
            names = zf.namelist()
            legend = zf.read(next(n for n in names if n.endswith("legend.xhtml"))).decode("utf-8")
            nav = zf.read(next(n for n in names if n.endswith("nav.xhtml"))).decode("utf-8")
        assert "A Guide to the Notes" in legend
        assert 'href="legend.xhtml"' in nav
        assert "◇" in legend  # catholic-study includes the comm category


class TestAboutPagePure:
    def _specs(self):
        return {
            "canon_label": "Catholic",
            "book_count": 73,
            "annotation_count": 12345,
            "category_count": 2,
            "categories": [{"label": "Commentary / Tradition", "count": 2690}, {"label": "Apologetic", "count": 55}],
            "witness_labels": ["Hebrew (Masoretic / WLC)", "Latin (Clementine Vulgate)"],
            "theme": "devotional",
            "description": "",
        }

    def test_renders_specs(self):
        from scripts.build_edition import render_about_page

        out = render_about_page({"id": "x", "title": "T"}, self._specs(), "v")
        assert "About this Edition" in out
        assert "Catholic" in out and "73" in out and "12,345" in out
        assert "Commentary / Tradition" in out and "2,690 notes" in out
        assert "Apologetic" in out and "55 notes" in out
        assert "Hebrew (Masoretic / WLC)" in out and "Latin (Clementine Vulgate)" in out

    def test_description_optional(self):
        from scripts.build_edition import render_about_page

        s = self._specs()
        assert "SENTINEL_DESC" not in render_about_page({"id": "x", "title": "T"}, s, "v")
        s2 = dict(s)
        s2["description"] = "SENTINEL_DESC text"
        assert "SENTINEL_DESC text" in render_about_page({"id": "x", "title": "T"}, s2, "v")

    def test_well_formed_xml(self):
        import xml.dom.minidom as md
        from scripts.build_edition import render_about_page

        md.parseString(render_about_page({"id": "x", "title": "T & <co>"}, self._specs(), "v"))


class TestAboutSpecs:
    def test_specs_composed_for_edition(self):
        from scripts.build_edition import _about_specs_for_edition

        s = _about_specs_for_edition("catholic-study")
        assert s["book_count"] > 0 and s["annotation_count"] > 0
        assert s["category_count"] == len(s["categories"])
        assert all(c["count"] > 0 for c in s["categories"])
        assert isinstance(s["witness_labels"], list)


class TestAboutReachesEpub:
    def test_about_page_and_nav(self, tmp_path, monkeypatch):
        import zipfile
        import scripts.build_edition as be
        from scripts.core import build_cache, config

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)
        stats = be.build_one("catholic-study", tmp_path, "about-test", config.load_kinds(), force=True)
        with zipfile.ZipFile(stats["output_path"]) as zf:
            names = zf.namelist()
            about = zf.read(next(n for n in names if n.endswith("about.xhtml"))).decode("utf-8")
            nav = zf.read(next(n for n in names if n.endswith("nav.xhtml"))).decode("utf-8")
        assert "About this Edition" in about and 'href="about.xhtml"' in nav


class TestBackMatterPure:
    def test_sources_lists_key_sources(self):
        from scripts.build_edition import render_sources_page

        out = render_sources_page("v")
        assert "Sources" in out and "World English Bible" in out and "Public Domain" in out
        assert "Strong" in out  # lexicon credited
        import xml.dom.minidom as md

        md.parseString(out)

    def test_reference_tables_has_units(self):
        from scripts.build_edition import render_reference_tables_page

        out = render_reference_tables_page("v")
        assert "cubit" in out and "shekel" in out and "ephah" in out
        import xml.dom.minidom as md

        md.parseString(out)

    def test_closing_colophon(self):
        from scripts.build_edition import render_closing_colophon_page

        out = render_closing_colophon_page({"id": "catholic-study", "title": "T"}, "v")
        assert "urn:yhwh:edition:catholic-study" in out and "YHWH Ya" in out
        import xml.dom.minidom as md

        md.parseString(out)


class TestBackMatterReachesEpub:
    def test_back_pages_in_order(self, tmp_path, monkeypatch):
        import re
        import zipfile

        import scripts.build_edition as be
        from scripts.core import build_cache, config

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)
        stats = be.build_one("catholic-study", tmp_path, "back-test", config.load_kinds(), force=True)
        with zipfile.ZipFile(stats["output_path"]) as zf:
            names = zf.namelist()
            opf = zf.read(next(n for n in names if n.endswith("content.opf"))).decode("utf-8")
            assert any(n.endswith("sources.xhtml") for n in names)
            assert any(n.endswith("reftables.xhtml") for n in names)
            assert any(n.endswith("topical.xhtml") for n in names)  # §5.4 #4 Nave's index
            assert any(n.endswith("colophonend.xhtml") for n in names)
        order = re.findall(r'<itemref idref="(\w+)"/>', opf)
        # back matter appears at the very end, in order:
        # sources -> reftables -> topical -> colophon (colophon last)
        assert order.index("backsources") < order.index("backreftables") < order.index("backcolophon")
        assert order.index("backreftables") < order.index("backtopical") < order.index("backcolophon")
        assert order[-1] == "backcolophon", "closing colophon must be the last page"


class TestDedicationPage:
    def test_renders_when_present(self):
        from scripts.build_edition import render_dedication_page

        out = render_dedication_page({"id": "x", "dedication": "For my family."})
        assert "For my family." in out
        import xml.dom.minidom as md

        md.parseString(out)

    def test_build_includes_dedication_after_title_when_set(self, tmp_path, monkeypatch):
        import re
        import shutil
        import zipfile
        from pathlib import Path

        import scripts.build_edition as be
        import scripts.web as web
        from scripts.core import build_cache, config

        eds = Path(config.__file__).resolve().parents[2] / "content" / "editions.yaml"
        backup = tmp_path / "eds.bak"
        shutil.copy(eds, backup)
        try:
            monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
            monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)
            web.api_save_edition_meta("catholic-study", {"dedication": "DEDICATION_SENTINEL_42."})
            config.load_editions.cache_clear()
            stats = be.build_one("catholic-study", tmp_path, "ded-test", config.load_kinds(), force=True)
            with zipfile.ZipFile(stats["output_path"]) as zf:
                names = zf.namelist()
                ded = zf.read(next(n for n in names if n.endswith("dedication.xhtml"))).decode("utf-8")
                opf = zf.read(next(n for n in names if n.endswith("content.opf"))).decode("utf-8")
            assert "DEDICATION_SENTINEL_42." in ded
            order = re.findall(r'<itemref idref="(\w+)"/>', opf)
            assert order.index("titlepage") < order.index("dedication") < order.index("copyright")
        finally:
            shutil.copy(backup, eds)
            config.load_editions.cache_clear()

    def test_no_dedication_page_when_empty(self, tmp_path, monkeypatch):
        import zipfile
        import scripts.build_edition as be
        from scripts.core import build_cache, config

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)
        stats = be.build_one("evangelical-reformed", tmp_path, "ded-test", config.load_kinds(), force=True)
        with zipfile.ZipFile(stats["output_path"]) as zf:
            assert not any(n.endswith("dedication.xhtml") for n in zf.namelist())


class TestEditableDescDed:
    def setup_method(self):
        import scripts.web as web

        self.web = web

    def test_round_trip(self, tmp_path):
        import shutil
        from pathlib import Path
        from scripts.core import config

        eds = Path(config.__file__).resolve().parents[2] / "content" / "editions.yaml"
        backup = tmp_path / "eds.bak"
        shutil.copy(eds, backup)
        try:
            config.load_editions.cache_clear()
            r = self.web.api_save_edition_meta("catholic-study", {"description": "DESC_RT", "dedication": "DED_RT"})
            assert r.get("ok"), r
            cath = next(e for e in self.web.api_customize_data()["editions"] if e["id"] == "catholic-study")
            assert cath["description"] == "DESC_RT" and cath["dedication"] == "DED_RT"
        finally:
            shutil.copy(backup, eds)
            config.load_editions.cache_clear()

    def test_customize_ui_has_textareas(self):
        from scripts.templates.customize import CUSTOMIZE_HTML

        assert 'data-field="description"' in CUSTOMIZE_HTML and 'data-field="dedication"' in CUSTOMIZE_HTML
        assert "input, select, textarea" in CUSTOMIZE_HTML


# ──────────────────────────────────────────────────────────────
# FIX 2 + FIX 4 — front-matter consolidation (integration)
# ──────────────────────────────────────────────────────────────


class TestFrontMatterConsolidation:
    """Build catholic-study and assert Phase-1 pre-commit gates."""

    EDITION = "catholic-study"

    def _build(self, tmp_path, monkeypatch):
        import scripts.build_edition as be
        from scripts.core import build_cache, config

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)
        assert self.EDITION in config.editions_by_id()
        stats = be.build_one(self.EDITION, tmp_path, "polish-test", config.load_kinds(), force=True)
        epub = Path(stats["output_path"])
        assert epub.is_file()
        return epub

    def test_placeholder_introduction_dropped(self, tmp_path, monkeypatch):
        """FIX 2: introduction.xhtml must NOT appear in the built EPUB's
        content.opf spine or as a zip member."""
        import zipfile

        epub = self._build(tmp_path, monkeypatch)
        with zipfile.ZipFile(epub) as zf:
            names = zf.namelist()
            # introduction.xhtml must not be a zip member
            intro_files = [n for n in names if "introduction.xhtml" in n]
            assert not intro_files, f"introduction.xhtml still bundled in the EPUB: {intro_files}"
            # content.opf must not contain the introduction spine itemref
            opf_names = [n for n in names if n.endswith("content.opf")]
            assert opf_names, "content.opf not found inside EPUB zip"
            opf_text = zf.read(opf_names[0]).decode("utf-8")
            assert '<itemref idref="introduction"/>' not in opf_text, (
                "introduction itemref still in built content.opf spine — "
                "_drop_placeholder_introduction may not have run"
            )
            assert 'href="introduction.xhtml"' not in opf_text, (
                "introduction manifest <item> still in built content.opf — "
                "dangling reference to a removed file → epubcheck RSC-001"
            )

    def test_drop_introduction_removes_manifest_item(self, tmp_path):
        """The manifest <item> (not just the spine itemref) must be removed —
        its media-type ``application/xhtml+xml`` contains a '/', so a naive
        ``[^/]*`` pattern stops at that slash and leaves the item behind,
        dangling at a now-deleted file (epubcheck RSC-001)."""
        from scripts.build_edition import _drop_placeholder_introduction

        opf = tmp_path / "content.opf"
        opf.write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n<package><manifest>\n'
            '    <item id="introduction" href="introduction.xhtml" media-type="application/xhtml+xml"/>\n'
            '    <item id="about" href="about.xhtml" media-type="application/xhtml+xml"/>\n'
            "  </manifest>\n  <spine>\n"
            '    <itemref idref="introduction"/>\n'
            '    <itemref idref="about"/>\n'
            "  </spine>\n</package>\n",
            encoding="utf-8",
        )
        (tmp_path / "introduction.xhtml").write_text("<html/>", encoding="utf-8")

        _drop_placeholder_introduction(tmp_path)

        result = opf.read_text(encoding="utf-8")
        assert "introduction.xhtml" not in result, "manifest item to introduction.xhtml survived"
        assert 'idref="introduction"' not in result, "spine itemref survived"
        # neighbouring entries must be untouched
        assert 'href="about.xhtml"' in result and 'idref="about"' in result
        assert not (tmp_path / "introduction.xhtml").exists()

    def test_about_manifest_registered(self, tmp_path, monkeypatch):
        """FIX 4: about.xhtml must be registered in the OPF manifest."""
        import zipfile

        epub = self._build(tmp_path, monkeypatch)
        with zipfile.ZipFile(epub) as zf:
            names = zf.namelist()
            opf_names = [n for n in names if n.endswith("content.opf")]
            assert opf_names, "content.opf not found inside EPUB zip"
            opf_text = zf.read(opf_names[0]).decode("utf-8")
            assert '<item id="about"' in opf_text, (
                "about.xhtml not registered in OPF manifest — inject_about_page may have silently no-op'd (FIX 4)"
            )


# ──────────────────────────────────────────────────────────────
# FIX 3 — CSS page-break-before: avoid on mid-page h2 headings
# ──────────────────────────────────────────────────────────────

_CSS = Path(__file__).resolve().parent.parent / "epub_working" / "stylesheet.css"


class TestPageBreakAvoidRules:
    """stylesheet.css must prevent mid-page fragmentation on the new h2 headings."""

    def test_sources_heading_has_avoid(self):
        css = _CSS.read_text(encoding="utf-8")
        idx = css.find(".sources-heading")
        assert idx >= 0, ".sources-heading rule missing from stylesheet.css"
        snippet = css[idx : idx + 400]
        assert "page-break-before: avoid" in snippet, ".sources-heading must set page-break-before: avoid"
        assert "break-before: avoid" in snippet, ".sources-heading must set break-before: avoid (modern property)"

    def test_copyright_heading_has_avoid(self):
        css = _CSS.read_text(encoding="utf-8")
        idx = css.find(".copyright-heading")
        assert idx >= 0, ".copyright-heading rule missing from stylesheet.css"
        snippet = css[idx : idx + 200]
        assert "page-break-before: avoid" in snippet, ".copyright-heading must set page-break-before: avoid"
        assert "break-before: avoid" in snippet, ".copyright-heading must set break-before: avoid (modern property)"


# ──────────────────────────────────────────────────────────────
# FIX 5 — render_dedication_page signature (no `version` param)
# ──────────────────────────────────────────────────────────────


class TestDedicationPageSignature:
    """render_dedication_page must no longer accept a `version` parameter."""

    def test_renders_without_version_arg(self):
        from scripts.build_edition import render_dedication_page

        edition = {"dedication": "To the glory of God.", "id": "test", "title": "T"}
        out = render_dedication_page(edition)
        assert "To the glory of God." in out
        assert "dedication-text" in out

    def test_no_version_parameter(self):
        import inspect
        from scripts.build_edition import render_dedication_page

        sig = inspect.signature(render_dedication_page)
        assert "version" not in sig.parameters, (
            "render_dedication_page must not have a `version` parameter (it was unused — FIX 5)"
        )

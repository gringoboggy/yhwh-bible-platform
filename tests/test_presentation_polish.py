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
    """finding 1b (device-QA 2026-06-08): justified PROSE is the EPUB DEFAULT — so the
    reader's GLOBAL justify toggle (which also spaced out the ToC book-names) is never
    needed — but justification is SCOPED to prose containers; ToC / titles / headings /
    pills / captions / labels are NEVER justified. This SUPERSEDES the 2026-05-24
    'no justify anywhere' contract (justify shipped as the prose default in beta-2)."""

    # Furniture selectors that must NEVER carry text-align:justify (the build guard).
    _FURNITURE_KEYWORDS = (
        "toc",
        "title",
        "heading",
        "eyebrow",
        "pill",
        "caption",
        "-label",
        "cover",
        "bookpage",
        "legend",
        "backmatter",
        "-rule",
    )

    def test_prose_is_justified_by_default(self):
        # Verse paragraphs + note bodies carry justify + hyphenation as the EPUB's own
        # default, so the reader never reaches for the global justify toggle.
        css = BASE_CSS.read_text(encoding="utf-8")
        assert "text-align: justify" in css, "prose justify is the finding-1b default — missing"
        assert "hyphens: auto" in css, "justify must be paired with hyphens:auto to avoid rivers"

    def test_no_furniture_selector_is_justified(self):
        # The finding-1b BUILD GUARD: no heading/title/ToC/pill/caption/label selector
        # may resolve to text-align:justify (the reader's global toggle would then space
        # it out). Only prose containers (.verse-p / .note) are justified.
        import re

        css = BASE_CSS.read_text(encoding="utf-8")
        # Strip /* … */ comments first — a comment preceding a rule is otherwise
        # captured as part of its "selector" and a comment that merely NAMES a
        # furniture class (e.g. ".note-label") would false-positive a prose block.
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
        offenders = []
        for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
            if "text-align: justify" not in body and "text-align:justify" not in body:
                continue
            low = sel.lower()
            if any(k in low for k in self._FURNITURE_KEYWORDS):
                offenders.append(sel.strip())
        assert not offenders, "furniture selectors must never be justified (finding 1b guard): " + "; ".join(offenders)


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
            {"id": "catholic-study", "title": "Cath"}, self._pub(), annotation_count=12345, category_count=9
        )
        assert "TODO_" not in out

    def test_no_stale_hardcoded_count(self):
        from scripts.build_edition import render_copyright_page

        out = render_copyright_page({"id": "x", "title": "T"}, self._pub(), annotation_count=12345, category_count=9)
        assert "1,371" not in out and "14 categories" not in out

    def test_real_counts_rendered(self):
        from scripts.build_edition import render_copyright_page

        out = render_copyright_page({"id": "x", "title": "T"}, self._pub(), annotation_count=12345, category_count=9)
        assert "12,345" in out and "9 categories" in out

    def test_identity_and_urn(self):
        from scripts.build_edition import render_copyright_page

        out = render_copyright_page(
            {"id": "catholic-study", "title": "T"}, self._pub(), annotation_count=10, category_count=1
        )
        assert "Way Editions" in out and "Bogdan Zorlescu" in out and "2026" in out
        # device-QA 2026-06-09: the "This Edition" identity block (Edition ID + Build)
        # MOVED to the Your Edition page (co-located with the note details — more
        # logical per the user). The front colophon is now legal/publisher only.
        assert "urn:yhwh:edition:catholic-study" not in out
        assert "This Edition" not in out

    def test_no_long_description_on_colophon(self):
        from scripts.build_edition import render_copyright_page

        ed = {"id": "x", "title": "T", "description": "UNIQUE_DESC_SENTINEL_12321"}
        out = render_copyright_page(ed, self._pub(), annotation_count=10, category_count=1)
        assert "UNIQUE_DESC_SENTINEL_12321" not in out

    def test_well_formed_xml(self):
        import xml.dom.minidom as md
        from scripts.build_edition import render_copyright_page

        out = render_copyright_page(
            {"id": "x", "title": "T & <co>"}, self._pub(), annotation_count=10, category_count=1
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

        out = render_symbol_legend_page({"id": "x", "title": "T"}, self._cats())
        assert "A Guide to the Notes" in out
        for c in self._cats():
            assert c["symbol"] in out and c["label"] in out and c["description"] in out
        assert "100 notes" in out and "50 notes" in out

    def test_each_row_has_anchor_id(self):
        from scripts.build_edition import render_symbol_legend_page

        out = render_symbol_legend_page({"id": "x", "title": "T"}, self._cats())
        assert 'id="legend-comm"' in out and 'id="legend-topic"' in out

    def test_well_formed_xml(self):
        import xml.dom.minidom as md
        from scripts.build_edition import render_symbol_legend_page

        md.parseString(render_symbol_legend_page({"id": "x", "title": "T"}, self._cats()))


class TestLegendCategories:
    def test_edition_aware_only_present(self):
        from scripts.build_edition import _legend_categories_for_edition

        cats = _legend_categories_for_edition("evangelical-reformed")
        assert cats, "evangelical-reformed should have at least one category with notes"
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


# σ.3.2 (2026-06-04): the old About page was RETIRED. Its per-edition summary
# now lives on the "Your Edition" page (the first content page after the cover),
# driven by the build-accurate edition_stats.resolved_note_counts instead of the
# edition-wide matrix. The detailed Your-Edition tests live in
# tests/test_matter_pages_your_edition.py; these keep a presentation-polish
# smoke-pin that the page reaches the EPUB and the About page is gone.


class TestYourEditionReplacesAbout:
    def _stats(self):
        return {
            "total": 12345,
            "per_book": {"gen": 12000, "mat": 345},
            "per_category": {"comm": 12000, "xref": 345},
            "per_kind": {"comm-patristic": 12000, "xref-citation": 345},
            "popup_languages": ["wlc", "vulgate"],
        }

    def test_renders_display_name_total_and_whats_inside(self):
        from scripts.build_edition import render_your_edition_page

        ed = {"id": "catholic-study", "title": "T", "display_name": "Catholic Study Bible", "canon": "catholic"}
        out = render_your_edition_page(ed, self._stats(), "v")
        assert "Catholic Study Bible" in out
        assert "12,345" in out
        # What's inside surfaces the note families + popup languages by label.
        assert "Commentary / Tradition" in out and "Cross-references" in out
        assert "Hebrew (Masoretic / WLC)" in out and "Latin (Clementine Vulgate)" in out

    def test_description_optional_blockquote(self):
        from scripts.build_edition import render_your_edition_page

        ed = {"id": "catholic-study", "title": "T", "canon": "catholic"}
        assert "SENTINEL_DESC" not in render_your_edition_page(ed, self._stats(), "v")
        ed2 = {**ed, "description": "SENTINEL_DESC text"}
        out = render_your_edition_page(ed2, self._stats(), "v")
        assert "SENTINEL_DESC text" in out and "<blockquote" in out

    def test_well_formed_xml(self):
        import xml.dom.minidom as md
        from scripts.build_edition import render_your_edition_page

        ed = {"id": "catholic-study", "title": "T & <co>", "canon": "catholic"}
        md.parseString(render_your_edition_page(ed, self._stats(), "v"))

    def test_carries_edition_identity_moved_from_colophon(self):
        # device-QA 2026-06-09: the "This Edition" identity (Edition ID + Build)
        # now lives HERE, beside the per-book note details — not split onto the
        # front colophon. `version` (previously an unused param) is the Build stamp.
        from scripts.build_edition import render_your_edition_page

        ed = {"id": "catholic-study", "title": "T", "display_name": "Catholic Study Bible", "canon": "catholic"}
        out = render_your_edition_page(ed, self._stats(), "v9.9.9-test")
        assert "urn:yhwh:edition:catholic-study" in out  # Edition ID relocated here
        assert "v9.9.9-test" in out  # Build stamp relocated here


class TestYourEditionReachesEpub:
    def test_your_edition_page_and_nav_about_gone(self, tmp_path, monkeypatch):
        import zipfile
        import scripts.build_edition as be
        from scripts.core import build_cache, config

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)
        stats = be.build_one("catholic-study", tmp_path, "your-ed-test", config.load_kinds(), force=True)
        with zipfile.ZipFile(stats["output_path"]) as zf:
            names = zf.namelist()
            assert not any(n.endswith("about.xhtml") for n in names), "old about.xhtml still shipped"
            ye = zf.read(next(n for n in names if n.endswith("your-edition.xhtml"))).decode("utf-8")
            nav = zf.read(next(n for n in names if n.endswith("nav.xhtml"))).decode("utf-8")
        assert "Your Edition" in ye and 'href="your-edition.xhtml"' in nav
        assert 'href="about.xhtml"' not in nav


class TestBackMatterPure:
    def test_sources_lists_key_sources(self):
        from scripts.build_edition import render_sources_page

        out = render_sources_page()
        assert "Sources" in out and "World English Bible" in out and "Public Domain" in out
        assert "Strong" in out  # lexicon credited
        import xml.dom.minidom as md

        md.parseString(out)

    def test_reference_tables_has_units(self):
        from scripts.build_edition import render_reference_tables_page

        out = render_reference_tables_page()
        assert "cubit" in out and "shekel" in out and "ephah" in out
        import xml.dom.minidom as md

        md.parseString(out)

    def test_closing_colophon(self):
        # K-R2-6: the closing colophon is reader-facing — NO internal build
        # strings (Generated vX / the edition URN); identity lives on the
        # Your-Edition page. Signature pin: the version param is gone with them.
        import inspect

        from scripts.build_edition import render_closing_colophon_page

        assert list(inspect.signature(render_closing_colophon_page).parameters) == ["edition"]
        out = render_closing_colophon_page({"id": "catholic-study", "title": "T"})
        assert "YHWH Ya" in out and "Soli Deo Gloria" in out
        assert "urn:yhwh" not in out, "the URN must not be reader-visible here"
        assert "Generated" not in out, "internal build strings must not be reader-visible"
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

    def test_your_edition_manifest_registered(self, tmp_path, monkeypatch):
        """σ.3.2: your-edition.xhtml (which replaced the retired About page) must be
        registered in the OPF manifest."""
        import zipfile

        epub = self._build(tmp_path, monkeypatch)
        with zipfile.ZipFile(epub) as zf:
            names = zf.namelist()
            opf_names = [n for n in names if n.endswith("content.opf")]
            assert opf_names, "content.opf not found inside EPUB zip"
            opf_text = zf.read(opf_names[0]).decode("utf-8")
            assert '<item id="youredition"' in opf_text, (
                "your-edition.xhtml not registered in OPF manifest — inject_your_edition_page may have no-op'd"
            )
            assert '<item id="about"' not in opf_text, "retired about.xhtml still in OPF manifest"


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

    def test_copyright_heading_css_stays_dead(self):
        # W3 (turn-56 review): the relocated <h2 class="copyright-heading"> was
        # the only emitter; both .copyright-heading rules were dead CSS in every
        # edition and were deleted. Guard against resurrection without an emitter.
        css = _CSS.read_text(encoding="utf-8")
        assert ".copyright-heading" not in css, (
            "dead .copyright-heading CSS resurfaced — it has no emitter "
            "(the identity heading moved to the Your Edition page, 2030e7e0/W3)"
        )

    def test_copyright_heading_has_no_emitter(self):
        # Two-sided guard (turn-57/58 review C9): the CSS pin above cannot see
        # a render function RE-EMITTING class="copyright-heading" (that would
        # ship an unstyled class silently, then block restoring its CSS).
        # Source-scan every build script so the emitter side stays dead too.
        for py in (REPO / "scripts").rglob("*.py"):
            assert "copyright-heading" not in py.read_text(encoding="utf-8"), (
                f"{py.name} emits/mentions copyright-heading — the class was "
                "retired with W3 (identity moved to the Your Edition page); "
                "restoring it needs BOTH an emitter and its CSS, deliberately"
            )


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


class TestCopyrightPageSignature:
    """render_copyright_page must no longer accept a `version` parameter —
    its only consumer was the "Build:" identity line, which moved to the
    Your Edition page (2030e7e0); W4 mirrors FIX 5."""

    def test_no_version_parameter(self):
        import inspect
        from scripts.build_edition import render_copyright_page

        sig = inspect.signature(render_copyright_page)
        assert "version" not in sig.parameters, (
            "render_copyright_page must not have a `version` parameter (it was unused — W4)"
        )


class TestNoDeadVersionParams:
    """Self-enforcing guard for the FIX-5/W4 *class* (turn-57/58 review C8):
    no function in matter_pages.py may declare a `version` parameter it never
    reads. The per-function signature pins above caught two instances; this
    sweeps the whole module so the pattern cannot silently return (a dead
    `version` param implies the caller threads build identity into a page
    that does not print it)."""

    def test_every_version_param_is_read(self):
        import ast

        src = (REPO / "scripts" / "matter_pages.py").read_text(encoding="utf-8")
        offenders = []
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                all_args = node.args.args + node.args.kwonlyargs + node.args.posonlyargs
                if any(a.arg == "version" for a in all_args):
                    reads = any(
                        isinstance(n, ast.Name) and n.id == "version" and isinstance(n.ctx, ast.Load)
                        for n in ast.walk(node)
                    )
                    if not reads:
                        offenders.append(f"{node.name}:{node.lineno}")
        assert not offenders, (
            f"matter_pages.py functions declare a `version` param they never read "
            f"(drop it + sweep the call sites — FIX 5/W4 class): {offenders}"
        )


# ──────────────────────────────────────────────────────────────
# Phase 2 — cross-reader CSS quick wins (overhaul plan 2026-06-05)
# ──────────────────────────────────────────────────────────────


def _rule_body(css: str, selector: str) -> str:
    """Return the declaration block (between the first { and its matching })
    for the given CSS selector, so substring asserts don't bleed into a
    neighbouring rule."""
    sel_idx = css.find(selector)
    assert sel_idx >= 0, f"selector {selector!r} not found in stylesheet.css"
    open_idx = css.find("{", sel_idx)
    assert open_idx >= 0, f"no opening brace after {selector!r}"
    close_idx = css.find("}", open_idx)
    assert close_idx >= 0, f"no closing brace after {selector!r}"
    return css[open_idx + 1 : close_idx]


class TestPhase2CrossReaderCSS:
    """Phase 2 of the EPUB reading-experience overhaul: long-token wrapping in
    note popups (Apple #8), the blue "│" verse-number artifact (Apple #9), and
    the Apple TOC expand→next-page jump (Apple #10). This INTENTIONALLY changes
    built CSS — pin the NEW output, not byte-identity."""

    def test_note_wraps_long_tokens(self):
        """Apple #8: .note must wrap long unbreakable tokens (Hebrew strings,
        ref-chains) so the popup text can't overflow the box width."""
        body = _rule_body(_CSS.read_text(encoding="utf-8"), ".note ")
        assert "overflow-wrap: break-word" in body, (
            ".note must set overflow-wrap: break-word so long tokens wrap (Apple #8)"
        )
        assert "word-break: break-word" in body, ".note must set word-break: break-word (Apple #8)"

    def test_vnote_wraps_long_tokens(self):
        """Apple #8: .vnote (the verse-reference popup body) must also wrap."""
        body = _rule_body(_CSS.read_text(encoding="utf-8"), ".vnote {")
        assert "overflow-wrap: break-word" in body, (
            ".vnote must set overflow-wrap: break-word so long tokens wrap (Apple #8)"
        )
        assert "word-break: break-word" in body, ".vnote must set word-break: break-word (Apple #8)"

    def test_vn_no_super_lineheight_artifact(self):
        """Apple #9: the .vn verse-number rule must NOT pair vertical-align:super
        with line-height:0 — that exact combo triggers the iOS Apple Books blue
        vertical-bar ("│") artifact (documented at ~line 132). Use an explicit
        baseline shift instead, mirroring .verse-num-sup / .note-ref sup."""
        body = _rule_body(_CSS.read_text(encoding="utf-8"), ".vn {")
        assert "vertical-align: super" not in body, (
            ".vn must not use vertical-align: super (iOS Apple Books │ artifact — Apple #9)"
        )
        assert "line-height: 0" not in body, (
            ".vn must not use line-height: 0 (combines with super to cause the │ artifact — Apple #9)"
        )
        # the explicit baseline shift replacement must be present
        assert "vertical-align:" in body, ".vn must keep an explicit vertical-align baseline shift"

    def test_toc_details_avoids_page_break(self):
        """Apple #10: expanding a book low on the page jumps the whole book +
        pills to the next page; .toc-wrap details must avoid breaking inside."""
        body = _rule_body(_CSS.read_text(encoding="utf-8"), ".toc-wrap details {")
        assert "page-break-inside: avoid" in body, ".toc-wrap details must set page-break-inside: avoid (Apple #10)"
        assert "break-inside: avoid" in body, (
            ".toc-wrap details must set break-inside: avoid (modern property — Apple #10)"
        )


class TestTitlePageArtFit:
    """device-QA (Apple Books, 2026-06-09): the per-book title boxes push onto the
    NEXT page even more, *regardless of font size*. Root cause: the finding-3 height
    cap (max-height:42vh / 88vh) is SILENTLY IGNORED by Apple Books on a bare <img>
    unless object-fit is set (eink-research :225,:477; Mac turn-38 follow-up #1, never
    applied). So the art renders at full intrinsic height (font-independent → "regardless
    of font size") and the finding-3 break-inside:avoid then shoves the whole oversized
    frame to the next page. object-fit:contain makes the vh cap effective on-device, so
    the framed box fits one page again. (Re-verify on Apple Books — the device is the oracle.)"""

    def test_framed_art_caps_height_with_object_fit(self):
        body = _rule_body(_CSS.read_text(encoding="utf-8"), ".bookpage-art {")
        assert "max-height: 42vh" in body, ".bookpage-art must keep the finding-3 height cap"
        assert "object-fit: contain" in body, (
            ".bookpage-art needs object-fit:contain or Apple Books ignores max-height (boxes push to next page)"
        )

    def test_full_bleed_art_caps_height_with_object_fit(self):
        body = _rule_body(_CSS.read_text(encoding="utf-8"), ".bookpage-art-bleed {")
        assert "max-height: 88vh" in body, ".bookpage-art-bleed must keep the finding-3 height cap"
        assert "object-fit: contain" in body, (
            ".bookpage-art-bleed needs object-fit:contain or Apple Books ignores max-height"
        )

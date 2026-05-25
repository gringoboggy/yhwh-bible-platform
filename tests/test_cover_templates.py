"""§4.6 cover-template picker — the 25-design cover library wiring.

Spec: docs/superpowers/specs/2026-05-24-epub-presentation-polish-design.md §4.6 + §7.
Mirrors the title_page_style enum field end-to-end (const + api_save_edition_meta
enum validation + api_customize_data default + /customize control), and adds a
recompose endpoint that composes the chosen template into the edition's main
cover via generate_edition_covers._compose_cover, plus picker + upload UI.
"""

from __future__ import annotations

import sys
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

FAMILIES = ("01_ornate_leafy", "02_classical_corner", "03_beadline", "04_minimal_lines", "05_missal_central")
COLORS = ("black", "brown", "forest", "navy", "red")


class TestCoverTemplateConst:
    def test_twenty_five_stems_from_five_families_times_five_colors(self):
        from scripts.core.covers import COVER_TEMPLATES

        assert len(COVER_TEMPLATES) == 25
        expected = {f"{fam}_{color}" for fam in FAMILIES for color in COLORS}
        assert set(COVER_TEMPLATES) == expected

    def test_every_stem_has_a_template_png_on_disk(self):
        from scripts.core.covers import COVER_TEMPLATES

        tdir = REPO / "content" / "covers" / "templates"
        for stem in COVER_TEMPLATES:
            assert (tdir / f"{stem}.png").is_file(), f"missing template png: {stem}"

    def test_every_template_file_is_really_a_png(self):
        """The picker serves thumbnails through the /content/covers/ route,
        which refuses (415) any file whose magic bytes don't match its .png
        extension (SEC-001 in _send_file). So every template must actually be
        PNG-encoded — a JPEG/WebP misnamed .png would render a broken thumbnail."""
        from scripts.core.covers import COVER_TEMPLATES, _detect_format

        tdir = REPO / "content" / "covers" / "templates"
        mismatched = [
            stem
            for stem in sorted(COVER_TEMPLATES)
            if _detect_format((tdir / f"{stem}.png").read_bytes()[:32], ".png") != "png"
        ]
        assert not mismatched, f"templates misnamed .png but not PNG-encoded: {mismatched}"


class TestCoverTemplateCatalog:
    def test_catalog_has_25_entries_grouped_family_major(self):
        from scripts.core.covers import cover_template_catalog

        cat = cover_template_catalog()
        assert len(cat) == 25
        # family-major ordering: the first 5 entries all share family[0],
        # cycling through the 5 colors in declared order.
        assert [e["family"] for e in cat[:5]] == ["01_ornate_leafy"] * 5
        assert [e["color"] for e in cat[:5]] == list(COLORS)

    def test_catalog_entry_shape(self):
        from scripts.core.covers import cover_template_catalog

        e = cover_template_catalog()[0]
        assert e["stem"] == "01_ornate_leafy_black"
        assert e["family"] == "01_ornate_leafy"
        assert e["family_label"]  # non-empty human label
        assert e["color"] == "black"
        assert e["thumb"] == "/content/covers/templates/01_ornate_leafy_black.png"


class TestCoverTemplateValidator:
    def test_rejects_unknown_value(self):
        from scripts.api.editions import api_save_edition_meta

        res = api_save_edition_meta("catholic-study", {"cover_template": "rococo_teal"})
        assert "error" in res and "cover_template" in res["error"]

    def test_accepts_and_persists_a_valid_stem(self):
        from scripts.api.editions import api_save_edition_meta

        edyaml = REPO / "content" / "editions.yaml"
        backup = edyaml.read_bytes()
        try:
            res = api_save_edition_meta("catholic-study", {"cover_template": "03_beadline_navy"})
            assert "error" not in res, res
            config.load_editions.cache_clear()
            ed = config.editions_by_id()["catholic-study"]
            assert ed.get("cover_template") == "03_beadline_navy"
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()


class TestCoverTemplateLoader:
    def test_api_customize_data_defaults_cover_template_to_empty(self):
        from scripts.web import api_customize_data

        data = api_customize_data()
        eds = {e["id"]: e for e in data["editions"]}
        # Unset on disk → the loader supplies "" (back-compat: no template picked).
        assert eds["catholic-study"].get("cover_template") == ""

    def test_api_customize_data_exposes_the_template_catalog(self):
        from scripts.web import api_customize_data

        data = api_customize_data()
        cat = data.get("cover_templates")
        assert isinstance(cat, list) and len(cat) == 25
        assert cat[0]["stem"] == "01_ornate_leafy_black"
        assert cat[0]["thumb"] == "/content/covers/templates/01_ornate_leafy_black.png"


class TestCoverTitleFit:
    """The composed cover title must never run past the cover edges, even for
    long edition titles — _compose_cover auto-shrinks the font to fit width."""

    def _draw(self):
        from PIL import Image, ImageDraw

        return ImageDraw.Draw(Image.new("RGB", (32, 32)))

    def test_every_real_edition_title_fits_within_cover_width(self):
        # The actual guarantee the user cares about: no shipped edition title
        # overruns the cover edges after auto-fit.
        from scripts.generate_edition_covers import EDITIONS, TITLE_LINE_SPACING, TITLE_MAX_WIDTH, _fit_title_font

        draw = self._draw()
        overflowing = []
        for _ed, _stem, title in EDITIONS:
            font = _fit_title_font(title, draw)
            bbox = draw.multiline_textbbox((0, 0), title, font=font, align="center", spacing=TITLE_LINE_SPACING)
            if (bbox[2] - bbox[0]) > TITLE_MAX_WIDTH:
                overflowing.append((title.replace("\n", " / "), bbox[2] - bbox[0]))
        assert not overflowing, f"edition titles still overflow after fit: {overflowing}"

    def test_a_title_too_wide_at_max_gets_shrunk(self):
        from scripts.generate_edition_covers import TITLE_FONT_MAX, _fit_title_font

        # A long single line that overflows at the max font must shrink.
        font = _fit_title_font("The Catholic Study Bible Ethiopian Edition", self._draw())
        assert font.size < TITLE_FONT_MAX

    def test_short_title_keeps_the_max_font(self):
        from scripts.generate_edition_covers import TITLE_FONT_MAX, _fit_title_font

        font = _fit_title_font("Genesis", self._draw())
        assert font.size == TITLE_FONT_MAX

    def test_compose_cover_fits_a_long_single_line_title(self):
        # End-to-end: composing a real cover with a long one-line title must not
        # raise and must still produce a full-size cover.
        from scripts.generate_edition_covers import FINAL_HEIGHT, FINAL_WIDTH, _compose_cover

        img = _compose_cover("03_beadline_navy", "The Catholic Study Bible Ethiopian Edition Of Many Words")
        assert img.size == (FINAL_WIDTH, FINAL_HEIGHT)


class TestTitleForEdition:
    def test_known_edition_uses_the_bespoke_title(self):
        from scripts.generate_edition_covers import title_for_edition

        assert title_for_edition("catholic-study") == "The Catholic Study Bible\nEthiopian Edition"

    def test_unknown_edition_falls_back_to_the_id(self):
        from scripts.generate_edition_covers import title_for_edition

        assert title_for_edition("no-such-edition") == "no-such-edition"


class TestApplyCoverTemplate:
    def test_rejects_unknown_template(self):
        from scripts.api.covers import api_apply_cover_template

        res = api_apply_cover_template("catholic-study", "rococo_teal")
        assert "error" in res and "cover_template" in res["error"]

    def test_rejects_unknown_edition(self):
        from scripts.api.covers import api_apply_cover_template

        res = api_apply_cover_template("no-such-edition", "03_beadline_navy")
        assert "error" in res and "edition" in res["error"]

    def test_composes_writes_and_sets_both_fields(self):
        from scripts.api.covers import api_apply_cover_template

        edyaml = REPO / "content" / "editions.yaml"
        cover = REPO / "content" / "covers" / "catholic-study.jpg"
        ed_backup = edyaml.read_bytes()
        cover_backup = cover.read_bytes() if cover.is_file() else None
        try:
            res = api_apply_cover_template("catholic-study", "03_beadline_navy")
            assert res.get("ok") is True, res
            assert res["cover_template"] == "03_beadline_navy"
            assert res["path"] == "covers/catholic-study.jpg"
            # A real JPEG landed on disk (SOI magic bytes).
            assert cover.is_file()
            assert cover.read_bytes()[:2] == b"\xff\xd8"
            # editions.yaml now records BOTH the template and the cover path.
            config.load_editions.cache_clear()
            ed = config.editions_by_id()["catholic-study"]
            assert ed.get("cover_template") == "03_beadline_navy"
            assert ed.get("cover_image") == "covers/catholic-study.jpg"
        finally:
            edyaml.write_bytes(ed_backup)
            if cover_backup is not None:
                cover.write_bytes(cover_backup)
            elif cover.is_file():
                cover.unlink()
            config.load_editions.cache_clear()


class TestApplyCoverTemplateRoute:
    def test_post_route_matches_and_dispatches(self, monkeypatch):
        import scripts.web as web

        captured: dict = {}

        def fake(edition_id, stem):
            captured["edition_id"] = edition_id
            captured["stem"] = stem
            return {"ok": True}

        # The route lambda resolves api_apply_cover_template from web's module
        # namespace at call time, so patching it here verifies routing without
        # mutating editions.yaml or writing a cover.
        monkeypatch.setattr(web, "api_apply_cover_template", fake)

        path = "/api/covers/catholic-study/template"
        for pattern, handler in web._POST_ROUTES:
            m = pattern.match(path)
            if m:
                res = handler(m, {"cover_template": "03_beadline_navy"})
                assert res == {"ok": True}
                assert captured == {"edition_id": "catholic-study", "stem": "03_beadline_navy"}
                break
        else:
            raise AssertionError("no _POST_ROUTES entry matched /api/covers/<ed>/template")


class TestCoverPickerUI:
    """The /customize page is a JS-in-Python template string; assert the
    picker + upload affordances are present in the template source (same
    shape as the title_page_style <select> test)."""

    def _src(self) -> str:
        return (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")

    def test_has_cover_picker_section(self):
        src = self._src()
        assert "covers-section" in src
        assert "covers-template-thumb" in src

    def test_picker_iterates_catalog_and_posts_recompose(self):
        src = self._src()
        assert "DATA.cover_templates" in src
        assert "/api/covers/" in src
        assert "/template'" in src
        assert "cover_template:" in src

    def test_surfaces_main_and_per_book_upload_endpoints(self):
        src = self._src()
        assert "covers-upload-main" in src and "/main'" in src
        assert "covers-upload-book" in src and "/book/'" in src

    def test_wires_the_covers_section_in_the_rebind_loop(self):
        assert "wireCoversSection(" in self._src()

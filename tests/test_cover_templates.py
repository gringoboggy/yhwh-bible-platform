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
    """σ.2 — the composed cover text must never run past the cover edges. The
    fit_text_block wrap-then-shrink fitter GUARANTEES every line fits the safe
    width (the σ.2 overflow fix). Deeper coverage lives in tests/test_cover_fit.py."""

    def _draw(self):
        from PIL import Image, ImageDraw

        return ImageDraw.Draw(Image.new("RGB", (1024, 1536)))

    def test_every_real_edition_cover_text_fits_within_cover_width(self):
        # The actual guarantee the user cares about: no shipped edition's cover
        # text (HOLY BIBLE main + its subtitle) overruns the cover edges.
        from scripts.core import config
        from scripts.generate_edition_covers import (
            SUBTITLE_FONT_MAX,
            SUBTITLE_FONT_MIN,
            TITLE_FONT_MAX,
            TITLE_FONT_MIN,
            TITLE_MAX_WIDTH,
            cover_text_for_edition,
            fit_text_block,
        )

        draw = self._draw()
        overflowing = []
        for ed_id in config.editions_by_id():
            main, subtitle = cover_text_for_edition(ed_id)
            main_lines, main_font = fit_text_block(
                draw, main, TITLE_MAX_WIDTH, max_pt=TITLE_FONT_MAX, min_pt=TITLE_FONT_MIN
            )
            for line in main_lines:
                w = draw.textbbox((0, 0), line, font=main_font)[2]
                if w > TITLE_MAX_WIDTH:
                    overflowing.append((ed_id, "main", line, w))
            if subtitle:
                sub_lines, sub_font = fit_text_block(
                    draw, subtitle, TITLE_MAX_WIDTH, max_pt=SUBTITLE_FONT_MAX, min_pt=SUBTITLE_FONT_MIN
                )
                for line in sub_lines:
                    w = draw.textbbox((0, 0), line, font=sub_font)[2]
                    if w > TITLE_MAX_WIDTH:
                        overflowing.append((ed_id, "subtitle", line, w))
        assert not overflowing, f"cover text still overflows after fit: {overflowing}"

    def test_a_subtitle_too_wide_at_max_gets_shrunk(self):
        from scripts.generate_edition_covers import (
            SUBTITLE_FONT_MAX,
            SUBTITLE_FONT_MIN,
            TITLE_MAX_WIDTH,
            fit_text_block,
        )

        # A long subtitle that overflows at the max font must shrink/wrap.
        lines, font = fit_text_block(
            self._draw(),
            "The Catholic Study Bible Ethiopian Edition Of Many Words",
            TITLE_MAX_WIDTH,
            max_pt=SUBTITLE_FONT_MAX,
            min_pt=SUBTITLE_FONT_MIN,
        )
        assert font.size < SUBTITLE_FONT_MAX or len(lines) > 1

    def test_short_main_keeps_the_max_font(self):
        from scripts.generate_edition_covers import TITLE_FONT_MAX, TITLE_FONT_MIN, TITLE_MAX_WIDTH, fit_text_block

        lines, font = fit_text_block(
            self._draw(), "HOLY BIBLE", TITLE_MAX_WIDTH, max_pt=TITLE_FONT_MAX, min_pt=TITLE_FONT_MIN
        )
        assert font.size == TITLE_FONT_MAX
        assert lines == ["HOLY BIBLE"]

    def test_compose_cover_fits_a_long_subtitle(self):
        # End-to-end: composing a real cover with a long subtitle must not raise
        # and must still produce a full-size cover.
        from scripts.generate_edition_covers import FINAL_HEIGHT, FINAL_WIDTH, _compose_cover

        img = _compose_cover(
            "03_beadline_navy", "HOLY BIBLE", "The Catholic Study Bible Ethiopian Edition Of Many Words"
        )
        assert img.size == (FINAL_WIDTH, FINAL_HEIGHT)


class TestCoverTextForEdition:
    def test_known_edition_default_main_and_subtitle(self):
        from scripts.generate_edition_covers import cover_text_for_edition

        main, subtitle = cover_text_for_edition("catholic-study")
        assert main == "HOLY BIBLE"
        assert isinstance(subtitle, str) and subtitle

    def test_unknown_edition_defaults_to_holy_bible_no_subtitle(self):
        from scripts.generate_edition_covers import cover_text_for_edition

        main, subtitle = cover_text_for_edition("no-such-edition")
        assert main == "HOLY BIBLE"
        assert subtitle == ""


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


class TestCustomizePickerIntegration:
    """σ.4.2 — the "Your edition's name & notes" card: a smart-suggestion name
    picker (derived from the edition's canon + enabled families, never assuming
    "Study"), a Custom… free-text option, and a notes textarea bound to
    ``description``. On save the cover recomposes so the new name shows. These
    assert the served /customize HTML + the wiring in the JS template source."""

    def _src(self) -> str:
        return (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")

    def _html(self) -> str:
        from scripts.web import CUSTOMIZE_HTML

        return CUSTOMIZE_HTML

    def test_name_card_renders_in_served_html(self):
        html = self._html()
        # The collapsible identity card + its three controls render in the page
        # (per-card CLASSES, not ids, so the markup stays valid across cards).
        assert "ed-identity-card" in html
        assert "display-name-pick" in html
        assert "display-name-custom" in html
        assert "edition-notes" in html

    def test_name_controls_carry_the_right_data_fields(self):
        src = self._src()
        # The chosen/typed name posts as display_name; the notes box posts as
        # description (the existing field shown on the Your-Edition page).
        assert 'data-field="display_name"' in src
        assert 'data-field="description"' in src

    def test_smart_suggestion_function_present(self):
        src = self._src()
        # The suggestions are computed in JS from the customize data.
        assert "nameSuggestions" in src
        # It must derive a canon label and offer the plain "<Canon> Bible" + the
        # bare "Holy Bible" (empty subtitle) option.
        assert "Holy Bible" in src
        # Study Bible suggestion is GUARDED behind study-family detection — the
        # guard token must appear next to the Study Bible string so it is never
        # offered unconditionally.
        assert "Study Bible" in src
        assert "enabled_categories" in src

    def test_custom_option_reveals_a_capped_text_input(self):
        src = self._src()
        # ✏ Custom… option + a maxlength-capped free-text input (σ.4.4 cap).
        assert "Custom" in src
        assert 'maxlength="48"' in src or "maxlength='48'" in src

    def test_save_recomposes_the_cover(self):
        src = self._src()
        # After a successful save, the cover re-composes via the same template
        # endpoint the picker uses, so the new name appears immediately.
        assert "recomposeCoverAfterSave" in src or "maybeRecomposeCover" in src
        assert "/template" in src

    def test_name_card_wired_in_rebind_loop(self):
        assert "wireIdentityCard(" in self._src()

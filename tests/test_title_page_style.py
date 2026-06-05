"""§4.5 `title_page_style` — per-edition setting wiring (schema/loader/validator/UI).

Spec: docs/superpowers/specs/2026-05-24-epub-presentation-polish-design.md §4.5 + §7.
Mirrors the `chapter_number_format` enum field end-to-end: it lives in
EDITABLE_TEXT, has an api_save_edition_meta enum-validation block, surfaces in
api_customize_data (default "framed" — the cross-reader default since the
2026-06-05 reading-experience overhaul), and has a /customize <select>.

Build-time rendering (apply_title_pages) is covered separately once it lands."""

from __future__ import annotations

import sys
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

VALID = ("full-bleed", "framed")


class TestTitlePageStyleConst:
    def test_enum_constant_exposes_both_options(self):
        from scripts.build_edition import TITLE_PAGE_STYLES

        assert set(TITLE_PAGE_STYLES) == set(VALID)


class TestTitlePageStyleValidator:
    def test_rejects_unknown_value(self):
        from scripts.api.editions import api_save_edition_meta

        res = api_save_edition_meta("catholic-study", {"title_page_style": "fancy"})
        assert "error" in res and "title_page_style" in res["error"]

    def test_accepts_and_persists_framed(self):
        from scripts.api.editions import api_save_edition_meta

        edyaml = REPO / "content" / "editions.yaml"
        backup = edyaml.read_bytes()
        try:
            res = api_save_edition_meta("catholic-study", {"title_page_style": "framed"})
            assert "error" not in res, res
            config.load_editions.cache_clear()
            ed = config.editions_by_id()["catholic-study"]
            assert ed.get("title_page_style") == "framed"
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()


class TestTitlePageStyleLoader:
    def test_api_customize_data_defaults_to_framed(self):
        from scripts.web import api_customize_data

        data = api_customize_data()
        eds = {e["id"]: e for e in data["editions"]}
        # Unset on disk → the loader supplies the default. Since the 2026-06-05
        # reading-experience overhaul the cross-reader default is "framed"
        # (full-bleed's position:absolute overlay defeats Kobo's engine).
        assert eds["catholic-study"].get("title_page_style") == "framed"


class TestTitlePageStyleUI:
    def test_customize_template_has_the_select(self):
        # The /customize page is a JS-in-Python template string; assert the
        # control is present in the template source (same shape as the
        # existing chapter_number_format <select>).
        src = (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        assert 'data-field="title_page_style"' in src


def _book_title_page(idx: int, code: str, title: str) -> str:
    return (
        f'<div class="book-title-page" id="bp-{idx:02d}" data-book-idx="{idx}" epub:type="bodymatter">\n'
        '  <div class="book-title-frame">\n'
        '    <p class="bookpage-eyebrow">BOOK</p>\n'
        f'    <h1 class="bookpage-title">{title}</h1>\n'
        '    <div class="bookpage-rule">&#10070;</div>\n'
        "  </div>\n</div>\n"
    )


def _book_idx(book: dict, fallback: int) -> int:
    bp = book.get("bp", "")
    return int(bp.split("-", 1)[1]) if bp.startswith("bp-") else fallback


class TestApplyTitlePages:
    def test_framed_injects_img_with_alt_inside_frame(self, tmp_path):
        from scripts.build_edition import apply_title_pages

        (tmp_path / "index_split_000.html").write_text(_book_title_page(0, "gen", "Genesis"), encoding="utf-8")
        paths = apply_title_pages(tmp_path, {"id": "x", "title_page_style": "framed"}, {"gen"})

        out = (tmp_path / "index_split_000.html").read_text(encoding="utf-8")
        assert paths == ["images/book-gen.jpg"]
        assert (tmp_path / "images" / "book-gen.jpg").is_file()
        assert '<img class="bookpage-art" src="images/book-gen.jpg" alt="' in out
        assert "style-full-bleed" not in out
        # the framed image sits INSIDE the frame (after the frame opens)
        assert out.index("book-title-frame") < out.index("bookpage-art")

    def test_full_bleed_adds_class_and_bleed_img_before_frame(self, tmp_path):
        from scripts.build_edition import apply_title_pages

        (tmp_path / "i.html").write_text(_book_title_page(0, "gen", "Genesis"), encoding="utf-8")
        apply_title_pages(tmp_path, {"id": "x", "title_page_style": "full-bleed"}, {"gen"})

        out = (tmp_path / "i.html").read_text(encoding="utf-8")
        assert 'class="book-title-page style-full-bleed"' in out
        assert "bookpage-art-bleed" in out
        assert out.index("bookpage-art-bleed") < out.index("book-title-frame")

    def test_default_style_framed_when_unset(self, tmp_path):
        from scripts.build_edition import apply_title_pages

        (tmp_path / "i.html").write_text(_book_title_page(0, "gen", "Genesis"), encoding="utf-8")
        apply_title_pages(tmp_path, {"id": "x"}, {"gen"})
        out = (tmp_path / "i.html").read_text(encoding="utf-8")
        # Cross-reader default since the 2026-06-05 reading-experience overhaul:
        # framed (contained art plate inside the frame), NOT full-bleed.
        assert "style-full-bleed" not in out
        assert '<img class="bookpage-art" src="images/book-gen.jpg" alt="' in out

    def test_artless_book_is_unchanged(self, tmp_path):
        from scripts.build_edition import apply_title_pages

        defaults = REPO / "content" / "covers" / "_book_defaults"
        artless = None
        for i, b in enumerate(config.load_books()):
            if not (defaults / f"{b['code']}.jpg").is_file():
                artless = (_book_idx(b, i), b["code"])
                break
        assert artless, "expected at least one book without default art (deutero/Ethiopic)"
        idx, code = artless
        html_in = _book_title_page(idx, code, "Some Book")
        (tmp_path / "i.html").write_text(html_in, encoding="utf-8")

        paths = apply_title_pages(tmp_path, {"id": "x"}, {code})
        out = (tmp_path / "i.html").read_text(encoding="utf-8")
        assert paths == []
        assert "bookpage-art" not in out
        assert out == html_in


class TestPatchOpfBookImages:
    def test_registers_items_with_media_types(self):
        from scripts.build_edition import patch_opf_book_images

        opf = '<manifest>\n  <item id="x" href="a.xhtml" media-type="application/xhtml+xml"/>\n</manifest>'
        out = patch_opf_book_images(opf, ["images/book-gen.jpg", "images/book-exo.png"])
        assert 'href="images/book-gen.jpg" media-type="image/jpeg"' in out
        assert 'href="images/book-exo.png" media-type="image/png"' in out

    def test_noop_when_empty(self):
        from scripts.build_edition import patch_opf_book_images

        opf = "<manifest></manifest>"
        assert patch_opf_book_images(opf, []) == opf

    def test_idempotent_when_already_registered(self):
        from scripts.build_edition import patch_opf_book_images

        opf = '<manifest>\n  <item id="book-gen" href="images/book-gen.jpg" media-type="image/jpeg"/>\n</manifest>'
        assert patch_opf_book_images(opf, ["images/book-gen.jpg"]) == opf

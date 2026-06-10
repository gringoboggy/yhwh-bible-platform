"""K-R2 metadata / front-back-matter sweep (device-QA round 2, 2026-06-09).

K-R2-7: the ", or …" alternate book names survived in books.yaml, the base
nav.xhtml/toc.ncx, the bookpage-title h1s, and thousands of generated title=
tooltip attributes (the v0.0.3 (e) sweep missed those surfaces) — all swept.
K-R2-8: the OPF dc:description said "88 scriptures" (the count rule: 83, NEVER
87/88) and shipped Ethiopian-specific copy on every edition's library card —
patch_opf now writes the edition's own description (or a neutral default).
K-R2-6: ONE page named Colophon — the front page is retitled Copyright; the
closing colophon drops the internal Generated-vX/URN strings and is
option-gated (closing_colophon: false removes it entirely).
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ALT_NAMES = (
    "Ecclesiastes or, The Preacher",
    "The Song of Songs, or Song of Solomon",
    "The Wisdom of Jesus the Son of Sirach, or Ecclesiasticus",
    "4 Baruch, or Paralipomena of Jeremiah",
)


class TestAltNamesGone:
    def test_base_nav_ncx_and_books_yaml_carry_no_alt_names(self):
        for rel in ("epub_working/nav.xhtml", "epub_working/toc.ncx", "content/books.yaml"):
            text = (REPO / rel).read_text(encoding="utf-8")
            for name in ALT_NAMES:
                assert name not in text, f"{rel} still carries {name!r}"

    def test_base_html_carries_no_alt_names(self):
        # the heavy surfaces: bookpage-title h1s + the generated title= tooltips
        for piece in ("index_split_000.html", "index_split_037.html", "index_split_038.html", "index_split_045.html"):
            text = (REPO / "epub_working" / piece).read_text(encoding="utf-8")
            for name in ALT_NAMES:
                assert name not in text, f"{piece} still carries {name!r}"

    def test_books_yaml_has_the_clean_titles(self):
        text = (REPO / "content" / "books.yaml").read_text(encoding="utf-8")
        for clean in (
            '"Ecclesiastes"',
            '"The Song of Songs"',
            '"The Wisdom of Jesus the Son of Sirach"',
            '"4 Baruch"',
        ):
            assert clean in text, f"books.yaml missing cleaned title {clean}"


class TestOpfDescription:
    def test_base_opf_says_83_never_88(self):
        opf = (REPO / "epub_working" / "content.opf").read_text(encoding="utf-8")
        assert "83 scriptures" in opf
        assert "88 scriptures" not in opf and "88" not in opf.split("<dc:description>")[1].split("</dc:description>")[0]

    def test_patch_opf_uses_edition_description(self):
        from scripts.build_edition import patch_opf

        opf = (REPO / "epub_working" / "content.opf").read_text(encoding="utf-8")
        out = patch_opf(opf, {"id": "x", "title": "My Bible", "description": "A custom synopsis."}, "v1")
        assert "<dc:description>A custom synopsis.</dc:description>" in out

    def test_patch_opf_neutral_default_when_unset(self):
        # a non-described edition must NOT inherit the Ethiopian-specific base copy
        from scripts.build_edition import patch_opf

        opf = (REPO / "epub_working" / "content.opf").read_text(encoding="utf-8")
        out = patch_opf(opf, {"id": "x", "title": "My Catholic Bible"}, "v1")
        desc = out.split("<dc:description>")[1].split("</dc:description>")[0]
        assert "Ethiopian" not in desc and "scriptures" not in desc
        assert "My Catholic Bible" in desc

    def test_eth_edition_declares_the_83_description(self):
        from scripts.core import config

        eth = config.editions_by_id()["ethiopian-tewahedo"]
        assert "83 scriptures" in (eth.get("description") or "")

    def test_base_introduction_says_eighty_three(self):
        text = (REPO / "epub_working" / "introduction.xhtml").read_text(encoding="utf-8")
        assert "eighty-three" in text and "eighty-eight" not in text


class TestSingleColophon:
    def test_copyright_page_is_titled_copyright(self):
        from scripts.matter_pages import render_copyright_page

        out = render_copyright_page({"id": "x", "title": "T"}, {}, annotation_count=1, category_count=1)
        assert "<title>Copyright</title>" in out
        assert "<title>Colophon</title>" not in out

    def test_closing_colophon_gated_off(self, tmp_path):
        from scripts.matter_pages import inject_back_matter

        (tmp_path / "content.opf").write_text(
            "<package><manifest></manifest><spine></spine></package>", encoding="utf-8"
        )
        (tmp_path / "nav.xhtml").write_text("<nav><ol></ol></nav>", encoding="utf-8")
        inject_back_matter(tmp_path, {"id": "x", "title": "T", "closing_colophon": False}, "v")
        assert not (tmp_path / "colophonend.xhtml").exists(), "closing_colophon: false must drop the page"
        opf = (tmp_path / "content.opf").read_text(encoding="utf-8")
        assert "backcolophon" not in opf
        nav = (tmp_path / "nav.xhtml").read_text(encoding="utf-8")
        assert "colophonend" not in nav

    def test_closing_colophon_default_on(self, tmp_path):
        from scripts.matter_pages import inject_back_matter

        (tmp_path / "content.opf").write_text(
            "<package><manifest></manifest><spine></spine></package>", encoding="utf-8"
        )
        (tmp_path / "nav.xhtml").write_text("<nav><ol></ol></nav>", encoding="utf-8")
        inject_back_matter(tmp_path, {"id": "x", "title": "T"}, "v")
        assert (tmp_path / "colophonend.xhtml").exists()
        out = (tmp_path / "colophonend.xhtml").read_text(encoding="utf-8")
        assert "Generated" not in out and "urn:yhwh" not in out

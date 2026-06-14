"""The productized Send-to-Kindle ("june10") recipe — kindle_post.

Turn-84 (Mac, 2026-06-14) USER-CONFIRMED on a real Send-to-Kindle upload: the
minimal recipe DELIVERS where the over-engineered ``--target-reader kindle``
artifact (compaction + language cap + ToC-rows + unhide + 2 MB split) FAILED.
The proven recipe is a STANDARD (everywhere) build + a deterministic post-process:

  * physically strip every ``display:none`` / ``visibility:hidden`` (CSS + inline)
  * KEEP the ``.vn-sep`` separator spans (Mac turn-85 correction: the measured
    june10recipe.epub kept all 132,949 — they are the visible language separators
    in the footnote popups once their hide rule is stripped; dropping them was a
    FAIL-column behavior)
  * collapse ``<dc:language>`` to a SINGLE ``en-US`` (Amazon's E999 trigger)
  * LEAVE ``hidden=""`` attributes intact (test-2 delivered with them in place)
  * OCF re-zip (``mimetype`` first + stored)

These pins lock that contract. The strip half intentionally matches
``dev/verify_kr2_build.py``'s gate-5 hidden-content detector
(``display:none|visibility:hidden``) so a post-processed artifact carries ZERO
hidden content by that gate's own measure.
"""

import io
import zipfile

from scripts.core import kindle_post


class TestStripHiddenCss:
    def test_strips_display_none_and_visibility_hidden(self):
        css = ".notes-section { display: none; color: red; }\n.x { visibility: hidden; }\n"
        out, n = kindle_post.strip_hidden_css(css)
        assert "display: none" not in out
        assert "visibility: hidden" not in out
        assert "color: red" in out  # sibling declarations survive
        assert n == 2

    def test_leaves_unrelated_css_untouched(self):
        css = ".a { display: block; }\n.b { color: blue; }\n"
        out, n = kindle_post.strip_hidden_css(css)
        assert out == css
        assert n == 0

    def test_idempotent(self):
        css = ".notes-section { display:none; }\n"
        once, _ = kindle_post.strip_hidden_css(css)
        twice, n2 = kindle_post.strip_hidden_css(once)
        assert once == twice
        assert n2 == 0


class TestStripHiddenHtml:
    def test_strips_inline_hidden_keeps_rest_of_style(self):
        html = '<p style="margin:0;display:none">x</p>'
        out, n_inl = kindle_post.strip_hidden_html(html)
        assert "display:none" not in out
        assert "margin:0" in out
        assert n_inl == 1

    def test_keeps_vn_sep_spans(self):
        # the measured june10recipe.epub KEPT all its vn-sep spans (they are the
        # visible language separators in the footnote popups) — never drop them.
        html = '<p>a<span class="vn-sep">•</span>b</p>'
        out, n_inl = kindle_post.strip_hidden_html(html)
        assert out == html  # byte-identical — vn-sep untouched
        assert n_inl == 0

    def test_preserves_hidden_attribute(self):
        # the proven recipe LEAVES hidden="" in place (do NOT unhide)
        html = '<aside epub:type="footnotes" hidden="">note</aside>'
        out, _n_inl = kindle_post.strip_hidden_html(html)
        assert 'hidden=""' in out


class TestCollapseDcLanguage:
    def test_collapses_multi_language_to_single_en_us(self):
        opf = (
            "<metadata><dc:language>en</dc:language><dc:language>he</dc:language>"
            "<dc:language>grc</dc:language></metadata>"
        )
        out, n = kindle_post.collapse_dc_language(opf)
        assert out.count("<dc:language>") == 1
        assert "<dc:language>en-US</dc:language>" in out
        assert n == 3

    def test_single_language_becomes_en_us(self):
        opf = "<metadata><dc:language>en</dc:language></metadata>"
        out, n = kindle_post.collapse_dc_language(opf)
        assert out.count("<dc:language>") == 1
        assert "<dc:language>en-US</dc:language>" in out
        assert n == 1

    def test_no_language_is_noop(self):
        opf = "<metadata><dc:title>X</dc:title></metadata>"
        out, n = kindle_post.collapse_dc_language(opf)
        assert out == opf
        assert n == 0


def _synthetic_epub() -> bytes:
    """A minimal everywhere-shaped EPUB: mimetype, an OPF with multi-language,
    a stylesheet that hides notes, and one content file with an inline hide,
    a vn-sep span, and a hidden="" footnote wrapper."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr(
            "OEBPS/content.opf",
            "<?xml version='1.0'?><package><metadata "
            'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            "<dc:title>X</dc:title><dc:language>en</dc:language>"
            "<dc:language>he</dc:language></metadata></package>",
        )
        z.writestr("OEBPS/stylesheet.css", ".notes-section { display: none; }\n.keep { color: #111; }\n")
        z.writestr(
            "OEBPS/index_split_000.html",
            '<html><body><p style="display:none">h</p>'
            '<span class="vn-sep">•</span>'
            '<aside class="notes-section" epub:type="footnotes" hidden="">N</aside>'
            "</body></html>",
        )
    return buf.getvalue()


class TestMakeKindleSafe:
    def test_produces_zero_hidden_single_language_kept_hidden_attr(self, tmp_path):
        src = tmp_path / "src.epub"
        dst = tmp_path / "out.epub"
        src.write_bytes(_synthetic_epub())

        stats = kindle_post.make_kindle_safe(src, dst)

        with zipfile.ZipFile(dst) as z:
            css = z.read("OEBPS/stylesheet.css").decode()
            html = z.read("OEBPS/index_split_000.html").decode()
            opf = z.read("OEBPS/content.opf").decode()
            names = z.namelist()
            # mimetype is first and STORED (OCF contract)
            first = z.infolist()[0]
            assert first.filename == "mimetype"
            assert first.compress_type == zipfile.ZIP_STORED

        assert "display: none" not in css and "display:none" not in html
        assert 'class="vn-sep"' in html  # KEPT (june10 kept all 132,949)
        assert 'hidden=""' in html  # left intact
        assert opf.count("<dc:language>") == 1 and "en-US" in opf
        assert "mimetype" in names and "OEBPS/content.opf" in names
        assert stats["css_hidden_stripped"] >= 1
        assert stats["dc_language_collapsed"] == 2

    def test_mimetype_bytes_exact(self, tmp_path):
        src = tmp_path / "src.epub"
        dst = tmp_path / "out.epub"
        src.write_bytes(_synthetic_epub())
        kindle_post.make_kindle_safe(src, dst)
        with zipfile.ZipFile(dst) as z:
            assert z.read("mimetype") == b"application/epub+zip"


class TestVerifyKindleSafe:
    def test_conformant_artifact_passes(self, tmp_path):
        src = tmp_path / "src.epub"
        dst = tmp_path / "out.epub"
        src.write_bytes(_synthetic_epub())
        kindle_post.make_kindle_safe(src, dst)
        assert kindle_post.verify_kindle_safe(dst) == []

    def test_raw_everywhere_artifact_fails(self, tmp_path):
        # the un-processed synthetic build has hidden CSS + multi-language ->
        # the checker must flag it (fires-on-defect proof)
        src = tmp_path / "src.epub"
        src.write_bytes(_synthetic_epub())
        fails = kindle_post.verify_kindle_safe(src)
        assert any("display:none" in f or "dc:language" in f for f in fails), fails

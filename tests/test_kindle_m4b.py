"""M4b Kindle fork — study glossary backmatter + badge navigate (Option B)."""

import io
import zipfile

from scripts.core import kindle_post

_CHAPTER_HTML = (
    "<html><body>"
    '<p class="verse-p-flush">'
    '<a class="vn-link" id="v-gen-1-1" href="#vnote-gen-1-1" epub:type="noteref" title="Genesis 1:1">'
    '<span class="vn">1</span></a> In the beginning.'
    '<a class="vn-link" id="v-gen-1-18" href="#vnote-gen-1-18" epub:type="noteref" title="Genesis 1:18">'
    '<span class="vn">18</span></a> And there was evening.'
    '<a class="verse-notes-badge" id="vbadge-gen-1-1-s1" href="#vnotes-gen-1-1-s1" '
    'epub:type="noteref" title="3 notes"><sup class="marker-badge">3</sup></a>'
    "</p>"
    '<aside class="notes-section" epub:type="footnotes" hidden="">'
    '<aside class="verse-notes" id="vnotes-gen-1-1-s1" epub:type="footnote" hidden="">'
    '<p class="vn-back"><a href="#vbadge-gen-1-1-s1" class="note-back">↩</a> <strong>1:1</strong></p>'
    '<p>See also <a href="#v-gen-1-18">Gen 1:18</a>.</p>'
    "<p>Study body</p></aside>"
    "</aside>"
    '<section class="verse-refs-section" epub:type="footnotes" hidden="">'
    '<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote" hidden="">'
    '<p class="vnote-text">Hebrew witness</p></aside>'
    "</section>"
    "</body></html>"
)

_MULTI_CHAPTER_HTML = (
    "<html><body>"
    '<a id="ch-b00-c1" class="ch-anchor"></a>'
    '<p class="verse-p-flush">'
    '<a class="vn-link" id="v-gen-1-1" href="#vnote-gen-1-1" epub:type="noteref" title="Genesis 1:1">'
    '<span class="vn">1</span></a> Verse one.'
    '<a class="verse-notes-badge" id="vbadge-gen-1-1-s1" href="#vnotes-gen-1-1-s1" '
    'epub:type="noteref"><sup class="marker-badge">2</sup></a>'
    "</p>"
    '<a id="ch-b00-c2" class="ch-anchor"></a>'
    '<p class="verse-p-flush">'
    '<a class="vn-link" id="v-gen-2-1" href="#vnote-gen-2-1" epub:type="noteref" title="Genesis 2:1">'
    '<span class="vn">1</span></a> Verse two.'
    '<a class="verse-notes-badge" id="vbadge-gen-2-1-s1" href="#vnotes-gen-2-1-s1" '
    'epub:type="noteref"><sup class="marker-badge">1</sup></a>'
    "</p>"
    '<aside class="notes-section" epub:type="footnotes" hidden="">'
    '<aside class="verse-notes" id="vnotes-gen-1-1-s1" epub:type="footnote" hidden="">'
    "<p>Study ch1</p></aside>"
    '<aside class="verse-notes" id="vnotes-gen-2-1-s1" epub:type="footnote" hidden="">'
    "<p>Study ch2</p></aside>"
    "</aside>"
    '<section class="verse-refs-section" epub:type="footnotes" hidden="">'
    '<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote" hidden="">'
    '<p class="vnote-text">Ch1 translation</p></aside>'
    '<aside class="vnote" id="vnote-gen-2-1" epub:type="footnote" hidden="">'
    '<p class="vnote-text">Ch2 translation</p></aside>'
    "</section>"
    "</body></html>"
)


def _m4b_fixture_epub(*, chapter_html: str = _CHAPTER_HTML, multi: bool = False) -> bytes:
    body = _MULTI_CHAPTER_HTML if multi else chapter_html
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr(
            "OEBPS/content.opf",
            """<?xml version='1.0'?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="uid" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>X</dc:title><dc:language>en-US</dc:language>
  </metadata>
  <manifest>
    <item id="chap" href="index_split_000_00.html" media-type="application/xhtml+xml"/>
    <item id="backsources" href="sources.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chap"/>
    <itemref idref="backsources"/>
  </spine>
</package>""",
        )
        z.writestr("OEBPS/stylesheet.css", ".notes-section { display: block; }\n")
        z.writestr("OEBPS/index_split_000_00.html", body)
        z.writestr("OEBPS/sources.xhtml", "<html><body>Sources</body></html>")
        z.writestr(
            "OEBPS/nav.xhtml",
            '<html><body><nav epub:type="toc"><ol>'
            '<li><a href="sources.xhtml">Sources</a></li>'
            "</ol></nav></body></html>",
        )
        z.writestr("OEBPS/toc.ncx", '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/"><navMap></navMap></ncx>')
    return buf.getvalue()


class TestApplyKindleM4bHtml:
    def test_keeps_study_badge_and_vn_link(self):
        out, stats = kindle_post.apply_kindle_m4b_html(_CHAPTER_HTML)
        assert 'class="verse-notes-badge"' in out
        assert 'class="vn-link"' in out
        assert stats["badges_kept"] == 1
        assert stats["vn_links"] == 2

    def test_extracts_vnotes_from_scripture(self):
        out, stats = kindle_post.apply_kindle_m4b_html(_CHAPTER_HTML)
        assert 'id="vnotes-gen-1-1-s1"' not in out
        assert stats["asides_relocated"] == 1

    def test_leaves_vnote_in_hidden_tail(self):
        out, _stats = kindle_post.apply_kindle_m4b_html(_CHAPTER_HTML)
        assert 'id="vnote-gen-1-1"' in out
        assert "Hebrew witness" in out
        assert "kindle-chapter-study" not in out

    def test_idempotent_clean(self):
        once, _ = kindle_post.apply_kindle_m4b_html(_CHAPTER_HTML)
        twice, stats2 = kindle_post.apply_kindle_m4b_html(once)
        assert twice == once
        assert stats2["asides_relocated"] == 0


class TestApplyKindleM4bEpub:
    def test_builds_glossary_and_retargets_badges(self, tmp_path):
        src = tmp_path / "src.epub"
        src.write_bytes(_m4b_fixture_epub())
        stats = kindle_post.apply_kindle_m4b(src)
        assert stats["asides_relocated"] == 1
        assert stats["badges_retargeted"] == 1
        assert stats["glossary_pieces"] >= 1
        with zipfile.ZipFile(src) as z:
            names = z.namelist()
            assert any("kindle_study_glossary" in n for n in names)
            chap = z.read("OEBPS/index_split_000_00.html").decode()
            assert 'href="kindle_study_glossary' in chap
            assert 'href="#vnotes-gen-1-1-s1"' not in chap
            glossary = next(z.read(n).decode() for n in names if "kindle_study_glossary" in n)
            assert 'id="vnotes-gen-1-1-s1"' in glossary
            assert "Study body" in glossary
            assert 'href="index_split_000_00.html#v-gen-1-1"' in glossary
            assert 'href="#v-gen-1-18"' not in glossary
            assert 'href="index_split_000_00.html#v-gen-1-18"' in glossary
            nav = z.read("OEBPS/nav.xhtml").decode()
            assert "Study Notes" in nav
            if "sources.xhtml" in nav:
                assert nav.index("Study Notes") < nav.index("sources.xhtml")

    def test_multi_chapter_collects_both_asides(self, tmp_path):
        src = tmp_path / "src.epub"
        src.write_bytes(_m4b_fixture_epub(multi=True))
        stats = kindle_post.apply_kindle_m4b(src)
        assert stats["asides_relocated"] == 2
        assert stats["badges_retargeted"] == 2
        with zipfile.ZipFile(src) as z:
            chap = z.read("OEBPS/index_split_000_00.html").decode()
            assert "kindle-chapter-study" not in chap
            assert chap.index("ch-b00-c1") < chap.index("ch-b00-c2")

    def test_verify_passes(self, tmp_path):
        src = tmp_path / "src.epub"
        src.write_bytes(_m4b_fixture_epub())
        kindle_post.apply_kindle_m4b(src)
        assert kindle_post.verify_kindle_m4b(src) == []


class TestMakeKindleM4b:
    def test_chains_safe_post_and_m4b(self, tmp_path):
        src = tmp_path / "src.epub"
        dst = tmp_path / "out.epub"
        src.write_bytes(_m4b_fixture_epub())
        stats = kindle_post.make_kindle_m4b(src, dst)
        assert stats["asides_relocated"] == 1
        assert kindle_post.verify_kindle_safe(dst) == []
        assert kindle_post.verify_kindle_m4b(dst) == []


class TestKindleM4bCss:
    def test_appends_kindle_title_and_toc_rules(self):
        css = ".book-title-page { page-break-before: always; }\n"
        out = kindle_post.apply_kindle_m4b_css(css)
        assert "yhwh:kindle-m4b" in out
        assert "page-break-after: auto" in out
        assert "toc-chapter-row" in out


class TestVerifyKindleM4b:
    def test_raw_chapter_html_fails_m4b_2(self):
        fails = kindle_post.verify_kindle_m4b_scripture_html(_CHAPTER_HTML)
        assert any("m4b-2" in f for f in fails)

    def test_same_file_badge_href_fails_m4b_1(self):
        fails = kindle_post.verify_kindle_m4b_scripture_html(_CHAPTER_HTML)
        assert any("m4b-1" in f for f in fails)

    def test_m4b_output_passes(self, tmp_path):
        src = tmp_path / "src.epub"
        src.write_bytes(_m4b_fixture_epub())
        kindle_post.apply_kindle_m4b(src)
        assert kindle_post.verify_kindle_m4b(src) == []

    def test_raw_chapter_html_fails_m4b_5_when_inline(self):
        inline = _CHAPTER_HTML.replace(
            '<sup class="marker-badge">3</sup></a></p>',
            '<sup class="marker-badge">3</sup></a></p>\n'
            '<aside class="vnote" id="vnote-gen-1-2" epub:type="footnote">'
            "<p>Inline popup</p></aside>",
        )
        fails = kindle_post.verify_kindle_m4b_scripture_html(inline)
        assert any("m4b-5" in f for f in fails)

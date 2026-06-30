"""Play Books endnote post-process — relocate notes to back-matter, keep EPUB3.

Synthetic in-memory EPUB fixtures only (the box is RAM-constrained — never build
a full edition). The chapter fixture mirrors ``tests/test_kindle_m4b.py``: a
hidden ``notes-section`` husk holding a study ``verse-notes`` aside, a
``verse-refs-section`` holding two translation ``vnote`` asides, a study badge,
and two verse-number ``vn-link`` anchors — the exact shape ``make_play_safe``
relocates. The OPF declares TWO ``dc:language`` values and the stylesheet keeps a
``display:none`` rule so the tests can prove Play does NOT collapse the language
nor strip hidden CSS (that is the Kindle-only path)."""

import io
import zipfile

from scripts.core import play_post

# A study notes-section husk + a translation verse-refs-section, with same-file
# badge/vn-link source links — what the Play estimator inflates into phantom
# pages and what make_play_safe must relocate to reachable back-matter.
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
    '<p class="vnote-text">Hebrew witness</p>'
    '<p><a href="#v-gen-1-1" class="vnote-back" title="Back">↩</a></p></aside>'
    '<aside class="vnote" id="vnote-gen-1-18" epub:type="footnote" hidden="">'
    '<p class="vnote-text">Greek witness</p>'
    '<p><a href="#v-gen-1-18" class="vnote-back" title="Back">↩</a></p></aside>'
    "</section>"
    "</body></html>"
)

# Play renders hidden content + multi-language; the fixture keeps both so the
# preservation tests are meaningful (kindle_post would strip/collapse these).
_CSS = ".notes-section { display: block; }\n.secret { display: none; }\n"
_LANGS = ("en-US", "hbo")

# Scripture whose badge/vn-link still point same-file but whose target asides are
# GONE — the Play teleport bug (links relocated-out but never retargeted).
_DANGLING_SCRIPTURE = (
    "<html><body>"
    '<p class="verse-p-flush">'
    '<a class="vn-link" id="v-gen-1-1" href="#vnote-gen-1-1" epub:type="noteref">'
    '<span class="vn">1</span></a> Text.'
    '<a class="verse-notes-badge" id="vbadge-gen-1-1-s1" href="#vnotes-gen-1-1-s1" '
    'epub:type="noteref"><sup class="marker-badge">3</sup></a>'
    "</p>"
    "</body></html>"
)

# A leftover hidden wrapper past the E999/phantom-page size ceiling.
_OVERSIZED_SCRIPTURE = '<html><body><aside class="notes-section" hidden="">' + ("x" * 10_001) + "</aside></body></html>"


def _minimal_epub(scripture: str, *, css: str = _CSS, langs: tuple[str, ...] = _LANGS) -> bytes:
    """A minimal OCF EPUB (``mimetype`` first + STORED) with one scripture spine
    file + the back-matter scaffolding the relocation splices the glossary into."""
    lang_xml = "".join(f"<dc:language>{lang}</dc:language>" for lang in langs)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        mt = zipfile.ZipInfo("mimetype")
        mt.compress_type = zipfile.ZIP_STORED
        z.writestr(mt, "application/epub+zip")
        z.writestr(
            "OEBPS/content.opf",
            f"""<?xml version='1.0'?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="uid" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>X</dc:title>{lang_xml}
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
        z.writestr("OEBPS/stylesheet.css", css)
        z.writestr("OEBPS/index_split_000_00.html", scripture)
        z.writestr("OEBPS/sources.xhtml", "<html><body>Sources</body></html>")
        z.writestr(
            "OEBPS/nav.xhtml",
            '<html><body><nav epub:type="toc"><ol>'
            '<li><a href="sources.xhtml">Sources</a></li>'
            "</ol></nav></body></html>",
        )
        z.writestr("OEBPS/toc.ncx", '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/"><navMap></navMap></ncx>')
    return buf.getvalue()


class TestMakePlaySafe:
    def test_relocates_husks_and_retargets_links(self, tmp_path):
        src = tmp_path / "src.epub"
        dst = tmp_path / "out.epub"
        src.write_bytes(_minimal_epub(_CHAPTER_HTML))
        stats = play_post.make_play_safe(src, dst)
        assert stats["asides_relocated"] == 1
        assert stats["witness_relocated"] == 2
        assert stats["badges_retargeted"] == 1
        assert stats["vn_links_retargeted"] == 2
        with zipfile.ZipFile(dst) as z:
            names = z.namelist()
            assert any("kindle_study_glossary" in n for n in names)
            assert any("kindle_witness_glossary" in n for n in names)
            chap = z.read("OEBPS/index_split_000_00.html").decode()
            # the phantom-page husks are gone
            assert 'class="notes-section"' not in chap
            assert 'class="verse-refs-section"' not in chap
            # the same-file dangling fragments are gone — links now cross-file
            assert 'href="#vnotes-gen-1-1-s1"' not in chap
            assert 'href="#vnote-gen-1-1"' not in chap
            assert 'href="#vnote-gen-1-18"' not in chap
            assert 'href="kindle_study_glossary' in chap
            assert 'href="kindle_witness_glossary' in chap
            # the relocated notes live in reachable back-matter
            study = next(z.read(n).decode() for n in names if "kindle_study_glossary" in n)
            assert "Study body" in study
            witness = next(z.read(n).decode() for n in names if "kindle_witness_glossary" in n)
            assert "Hebrew witness" in witness and "Greek witness" in witness
            nav = z.read("OEBPS/nav.xhtml").decode()
            assert "Study Notes" in nav
            assert "Original-Language Witnesses" in nav

    def test_verify_clean_after_make(self, tmp_path):
        src = tmp_path / "src.epub"
        dst = tmp_path / "out.epub"
        src.write_bytes(_minimal_epub(_CHAPTER_HTML))
        play_post.make_play_safe(src, dst)
        assert play_post.verify_play_safe(dst) == []

    def test_keeps_epub3_language_and_hidden_css(self, tmp_path):
        # The Play-vs-Kindle contract: make_play_safe must NOT collapse
        # dc:language to a single value, NOR strip display:none (those are the
        # Kindle-only make_kindle_safe transforms Play never receives).
        src = tmp_path / "src.epub"
        dst = tmp_path / "out.epub"
        src.write_bytes(_minimal_epub(_CHAPTER_HTML))
        play_post.make_play_safe(src, dst)
        with zipfile.ZipFile(dst) as z:
            opf = z.read("OEBPS/content.opf").decode()
            assert opf.count("<dc:language>") == 2
            css = z.read("OEBPS/stylesheet.css").decode()
            assert "display: none" in css

    def test_does_not_inject_kindle_m4b_css(self, tmp_path):
        # make_play_safe must NOT reuse apply_kindle_m4b_css — that block carries
        # a Kindle-only body justify rule Play should not get.
        src = tmp_path / "src.epub"
        dst = tmp_path / "out.epub"
        src.write_bytes(_minimal_epub(_CHAPTER_HTML))
        play_post.make_play_safe(src, dst)
        with zipfile.ZipFile(dst) as z:
            for name in z.namelist():
                if name.endswith(".css"):
                    css = z.read(name).decode()
                    assert "yhwh:kindle-m4b" not in css
                    assert "text-align: justify" not in css


class TestVerifyPlaySafe:
    def test_flags_dangling_same_file_frag(self, tmp_path):
        src = tmp_path / "dirty.epub"
        src.write_bytes(_minimal_epub(_DANGLING_SCRIPTURE))
        fails = play_post.verify_play_safe(src)
        assert any("vnotes-gen-1-1-s1" in f for f in fails)
        assert any("vnote-gen-1-1" in f for f in fails)

    def test_flags_oversized_hidden_block(self, tmp_path):
        src = tmp_path / "big.epub"
        src.write_bytes(_minimal_epub(_OVERSIZED_SCRIPTURE))
        fails = play_post.verify_play_safe(src)
        assert any("e999" in f for f in fails)

    def test_clean_fixture_after_make_has_no_fails(self, tmp_path):
        # Round-trip: relocate, then both gates pass.
        src = tmp_path / "src.epub"
        dst = tmp_path / "out.epub"
        src.write_bytes(_minimal_epub(_CHAPTER_HTML))
        play_post.make_play_safe(src, dst)
        assert play_post.verify_play_safe(dst) == []

"""M4b Kindle fork — marker suppress + chapter-tail study blocks (structural gates)."""

import io
import zipfile

from scripts.core import kindle_post

_CHAPTER_HTML = (
    "<html><body>"
    '<p class="verse-p-flush">'
    '<a class="vn-link" id="v-gen-1-1" href="#vnote-gen-1-1" epub:type="noteref" title="Genesis 1:1">'
    '<span class="vn">1</span></a> In the beginning.'
    '<a class="verse-notes-badge" id="vbadge-gen-1-1-s1" href="#vnotes-gen-1-1-s1" '
    'epub:type="noteref" title="3 notes"><sup class="marker-badge">3</sup></a>'
    "</p>"
    '<aside class="notes-section" epub:type="footnotes" hidden="">'
    '<aside class="verse-notes" id="vnotes-gen-1-1-s1" epub:type="footnote" hidden="">'
    '<p class="vn-back"><a href="#vbadge-gen-1-1-s1" class="note-back">↩</a> <strong>1:1</strong></p>'
    "<p>Study body</p></aside>"
    "</aside>"
    "</body></html>"
)


class TestApplyKindleM4bHtml:
    def test_removes_study_badge_keeps_vn_link(self):
        out, stats = kindle_post.apply_kindle_m4b_html(_CHAPTER_HTML)
        assert "verse-notes-badge" not in out
        assert 'class="vn-link"' in out
        assert stats["badges_removed"] == 1
        assert stats["vn_links"] == 1

    def test_relocates_vnotes_into_kindle_chapter_study(self):
        out, stats = kindle_post.apply_kindle_m4b_html(_CHAPTER_HTML)
        assert 'class="kindle-chapter-study"' in out
        assert 'id="vnotes-gen-1-1-s1"' in out
        assert "Study body" in out
        assert stats["asides_relocated"] == 1
        assert stats["chapters_emitted"] == 1
        # aside must not remain inside the emptied notes-section wrapper
        assert out.count('id="vnotes-gen-1-1-s1"') == 1

    def test_study_aside_not_hidden_after_relocate(self):
        out, _stats = kindle_post.apply_kindle_m4b_html(_CHAPTER_HTML)
        study = out[out.index("kindle-chapter-study") : out.index("</div>", out.index("kindle-chapter-study")) + 6]
        assert 'id="vnotes-gen-1-1-s1"' in study
        assert "hidden" not in study

    def test_strips_vn_back_to_suppressed_vbadge(self):
        out, _stats = kindle_post.apply_kindle_m4b_html(_CHAPTER_HTML)
        assert "vbadge-gen-1-1-s1" not in out
        assert kindle_post.verify_kindle_m4b_html(out) == []

    def test_nested_vn_group_inside_study_aside_passes_verify(self):
        nested = _CHAPTER_HTML.replace(
            "<p>Study body</p>",
            '<section class="vn-group note-cat-comm"><p class="vn-cat-head">Comm</p>'
            '<aside class="vn-item"><p>Nested study</p></aside></section>',
        )
        out, _stats = kindle_post.apply_kindle_m4b_html(nested)
        assert kindle_post.verify_kindle_m4b_html(out) == []
        assert "Nested study" in out

    def test_idempotent(self):
        once, _ = kindle_post.apply_kindle_m4b_html(_CHAPTER_HTML)
        twice, stats2 = kindle_post.apply_kindle_m4b_html(once)
        assert twice == once
        assert stats2["badges_removed"] == 0


def _m4b_fixture_epub() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr(
            "OEBPS/content.opf",
            "<?xml version='1.0'?><package><metadata "
            'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            "<dc:title>X</dc:title><dc:language>en-US</dc:language></metadata></package>",
        )
        z.writestr("OEBPS/stylesheet.css", ".notes-section { display: block; }\n")
        z.writestr("OEBPS/chapter.xhtml", _CHAPTER_HTML)
    return buf.getvalue()


class TestMakeKindleM4b:
    def test_chains_safe_post_and_m4b(self, tmp_path):
        src = tmp_path / "src.epub"
        dst = tmp_path / "out.epub"
        src.write_bytes(_m4b_fixture_epub())
        stats = kindle_post.make_kindle_m4b(src, dst)
        assert stats["badges_removed"] == 1
        assert kindle_post.verify_kindle_safe(dst) == []
        assert kindle_post.verify_kindle_m4b(dst) == []


class TestVerifyKindleM4b:
    def test_raw_chapter_html_fails_m4b_1(self):
        fails = kindle_post.verify_kindle_m4b_html(_CHAPTER_HTML)
        assert any("m4b-1" in f for f in fails)

    def test_m4b_output_passes(self):
        out, _ = kindle_post.apply_kindle_m4b_html(_CHAPTER_HTML)
        assert kindle_post.verify_kindle_m4b_html(out) == []

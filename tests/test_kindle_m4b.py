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
    '<section class="verse-refs-section" epub:type="footnotes" hidden="">'
    '<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote" hidden="">'
    '<p class="vnote-text">Hebrew witness</p></aside>'
    "</section>"
    "</body></html>"
)

_ANCHOR_IN_VERSE_P_HTML = (
    "<html><body>"
    '<a id="ch-b00-c1" class="ch-anchor"></a>'
    '<p class="verse-p-flush">'
    '<a class="vn-link" id="v-gen-1-1" href="#vnote-gen-1-1" epub:type="noteref">'
    '<span class="vn">1</span></a> Chapter one end.'
    '<a class="verse-notes-badge" id="vbadge-gen-1-1-s1" href="#vnotes-gen-1-1-s1" '
    'epub:type="noteref"><sup class="marker-badge">1</sup></a>'
    "</p>"
    '<p class="verse-p"><a id="ch-b00-c2" class="ch-anchor"></a>'
    '<a class="vn-link" id="v-gen-2-1" href="#vnote-gen-2-1" epub:type="noteref">'
    '<span class="vn">1</span></a> Chapter two.</p>'
    '<aside class="notes-section" epub:type="footnotes" hidden="">'
    '<aside class="verse-notes" id="vnotes-gen-1-1-s1" epub:type="footnote" hidden="">'
    "<p>Study body</p></aside>"
    "</aside>"
    '<section class="verse-refs-section" epub:type="footnotes" hidden="">'
    '<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote" hidden="">'
    '<p class="vnote-text">Translation</p></aside>'
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
    "</p>"
    '<aside class="notes-section" epub:type="footnotes" hidden="">'
    '<aside class="verse-notes" id="vnotes-gen-1-1-s1" epub:type="footnote" hidden="">'
    '<p class="vn-back"><a href="#vbadge-gen-1-1-s1" class="note-back">↩</a> <strong>1:1</strong></p>'
    "<p>Study ch1</p></aside>"
    "</aside>"
    '<section class="verse-refs-section" epub:type="footnotes" hidden="">'
    '<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote" hidden="">'
    '<p class="vnote-text">Ch1 translation</p></aside>'
    '<aside class="vnote" id="vnote-gen-2-1" epub:type="footnote" hidden="">'
    '<p class="vnote-text">Ch2 translation</p></aside>'
    "</section>"
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

    def test_study_aside_has_coord_backlink_to_v_anchor(self):
        out, _stats = kindle_post.apply_kindle_m4b_html(_CHAPTER_HTML)
        assert 'href="#v-gen-1-1"' in out
        assert "<strong>1:1</strong>" in out
        assert "vbadge-gen-1-1-s1" not in out
        assert kindle_post.verify_kindle_m4b_html(out) == []

    def test_strategy_b_backlink_uses_chapter_anchor(self):
        html = (
            "<html><body>"
            '<p id="ch-b15-c2" class="ch-heading"><span class="bold-num">2</span></p>'
            '<p class="verse-p"><span class="vn">1</span> Jubilees text.'
            '<a class="verse-notes-badge" href="#vnotes-jub-2-1-s1" epub:type="noteref">'
            '<sup class="marker-badge">1</sup></a></p>'
            '<aside class="notes-section" hidden="">'
            '<aside class="verse-notes" id="vnotes-jub-2-1-s1" epub:type="footnote" hidden="">'
            "<p>Study</p></aside></aside></body></html>"
        )
        out, _ = kindle_post.apply_kindle_m4b_html(html)
        assert 'href="#ch-b15-c2"' in out
        assert 'href="#v-jub-2-1"' not in out
        assert "<strong>2:1</strong>" in out

    def test_exposes_vnote_in_chapter_tail_block(self):
        out, stats = kindle_post.apply_kindle_m4b_html(_CHAPTER_HTML)
        assert stats["vnotes_exposed"] == 1
        assert "verse-refs-section" not in out
        assert "Hebrew witness" in out
        assert 'class="kindle-chapter-translations"' in out
        vnote_pos = out.index('id="vnote-gen-1-1"')
        study_pos = out.index("kindle-chapter-study")
        assert vnote_pos < study_pos
        verse_end = out.index("</p>", out.index("In the beginning"))
        assert vnote_pos > verse_end

    def test_study_block_not_inside_verse_p_opening(self):
        out, _stats = kindle_post.apply_kindle_m4b_html(_ANCHOR_IN_VERSE_P_HTML)
        assert '<p class="verse-p"><!-- yhwh:kindle-study-start -->' not in out
        assert out.index("kindle-chapter-study") < out.index('<p class="verse-p"><a id="ch-b00-c2"')

    def test_per_chapter_study_block_before_next_chapter(self):
        out, stats = kindle_post.apply_kindle_m4b_html(_MULTI_CHAPTER_HTML)
        assert stats["chapters_emitted"] == 1
        study_pos = out.index("kindle-chapter-study")
        ch2_pos = out.index('id="ch-b00-c2"')
        assert study_pos < ch2_pos
        assert "Study ch1" in out

    def test_multi_chapter_injection_recomputes_anchor_positions(self):
        html = _MULTI_CHAPTER_HTML.replace(
            '<a id="ch-b00-c2" class="ch-anchor"></a>',
            '<a id="ch-b00-c2" class="ch-anchor"></a>'
            '<p class="verse-p-flush">'
            '<a class="vn-link" id="v-gen-2-2" href="#vnote-gen-2-2" epub:type="noteref">'
            '<span class="vn">2</span></a> Verse two.'
            '<a class="verse-notes-badge" id="vbadge-gen-2-2-s1" href="#vnotes-gen-2-2-s1" '
            'epub:type="noteref"><sup class="marker-badge">1</sup></a></p>'
            '<aside class="notes-section" hidden="">'
            '<aside class="verse-notes" id="vnotes-gen-2-2-s1" epub:type="footnote" hidden="">'
            "<p>Study ch2</p></aside></aside>"
            '<section class="verse-refs-section" hidden="">'
            '<aside class="vnote" id="vnote-gen-2-2" epub:type="footnote" hidden="">'
            '<p class="vnote-text">Ch2 translation</p></aside></section>',
        )
        out, stats = kindle_post.apply_kindle_m4b_html(html)
        assert stats["chapters_emitted"] == 2
        assert stats["vnotes_exposed"] == 2
        assert kindle_post.verify_kindle_m4b_html(out) == []
        assert "Study ch2" in out
        assert "Ch2 translation" in out
        ch1_study = out.index("Study Notes — gen 1")
        ch2_anchor = out.index('id="ch-b00-c2"')
        assert ch1_study < ch2_anchor

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


class TestKindleM4bCss:
    def test_appends_kindle_title_and_toc_rules(self):
        css = ".book-title-page { page-break-before: always; }\n"
        out = kindle_post.apply_kindle_m4b_css(css)
        assert "yhwh:kindle-m4b" in out
        assert "page-break-after: auto" in out
        assert "toc-chapter-row" in out


class TestVerifyKindleM4b:
    def test_raw_chapter_html_fails_m4b_1(self):
        fails = kindle_post.verify_kindle_m4b_html(_CHAPTER_HTML)
        assert any("m4b-1" in f for f in fails)

    def test_m4b_output_passes(self):
        out, _ = kindle_post.apply_kindle_m4b_html(_CHAPTER_HTML)
        assert kindle_post.verify_kindle_m4b_html(out) == []

    def test_hidden_vnote_tail_fails_m4b_4(self):
        fails = kindle_post.verify_kindle_m4b_html(_CHAPTER_HTML)
        assert any("m4b-4" in f for f in fails)

    def test_inline_vnote_in_prose_fails_m4b_5(self):
        inline = _CHAPTER_HTML.replace(
            "</section>\n</body></html>",
            '</section>\n<p class="verse-p-flush">Verse</p>\n'
            '<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote">'
            "<p>Inline popup</p></aside>\n</body></html>",
        )
        fails = kindle_post.verify_kindle_m4b_html(inline)
        assert any("m4b-5" in f for f in fails)

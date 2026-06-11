"""Kindle STK bisect ladder — rung 2 DELINK (K-KIN round-3 probe).

Round-2 (rung-1 UNHIDE shipped in-build) still failed STK at ~46 min, so the
hidden-text hypothesis is dead and the ~112k-link anchor/popup graph (ranked
cause #2, notes/2026-06-11-kindle-stk-failure-forensics.md) is the live
suspect. Rung 2 rewrites the staged artifact one-variable: the four
note-graph anchor classes (vn-link, verse-notes-badge, vnote-back, note-back)
become spans and asides become divs — text byte-constant, ids kept, every
other link (note-sym, nav, ch-anchor) untouched. The output is a DIAGNOSTIC
probe, not a shippable edition (popups are intentionally dead).
"""

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location("kindle_bisect", REPO / "dev" / "kindle_bisect.py")
kindle_bisect = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kindle_bisect)

delink_html = kindle_bisect.delink_html


NOTEREF = (
    '<a class="vn-link" id="v-gen-27-1" href="#vnote-gen-27-1" '
    'epub:type="noteref" title="Genesis 27:1"><span class="vn">1</span></a>'
)
BADGE = (
    '<a class="verse-notes-badge" id="vbadge-gen-27-4" href="#vnotes-gen-27-4" epub:type="noteref" title="Notes">◈</a>'
)
# real artifact order: href BEFORE class on the back-links
VNOTE_BACK = '<a href="#v-gen-27-1" class="vnote-back" title="Back">↩</a>'
NOTE_BACK = '<a href="#vbadge-gen-27-4" class="note-back" title="Back">↩</a>'
ASIDE = '<aside class="verse-notes" id="vnotes-gen-27-4" epub:type="footnote"><p>body</p></aside>'
KEEP_SYM = '<a class="note-sym" href="legend.xhtml#legend-lang" title="L">⌘</a>'
KEEP_PLAIN = '<a href="index_split_002_00.html#ch-b00-c27">Genesis 27</a>'
KEEP_CH = '<a id="ch-b00-c28" class="ch-anchor"></a>'


class TestDelinkNoteGraph:
    def test_vn_link_noteref_becomes_span_keeping_id_and_text(self):
        out = delink_html(NOTEREF)
        assert out == ('<span class="vn-link" id="v-gen-27-1" title="Genesis 27:1"><span class="vn">1</span></span>')

    def test_badge_noteref_becomes_span(self):
        out = delink_html(BADGE)
        assert "<a" not in out and "href=" not in out and "noteref" not in out
        assert 'id="vbadge-gen-27-4"' in out and "◈" in out

    def test_backlinks_become_spans_with_href_before_class(self):
        for src in (VNOTE_BACK, NOTE_BACK):
            out = delink_html(src)
            assert "<a" not in out and "href=" not in out
            assert "↩" in out and out.startswith("<span")

    def test_aside_becomes_div_dropping_epub_type(self):
        out = delink_html(ASIDE)
        assert out == ('<div class="verse-notes" id="vnotes-gen-27-4"><p>body</p></div>')

    def test_footnotes_container_aside_also_converts(self):
        src = '<aside class="notes-section" id="notes-b00-c27" epub:type="footnotes"><hr class="notes-rule"/></aside>'
        out = delink_html(src)
        assert "<aside" not in out and "</aside>" not in out
        assert 'id="notes-b00-c27"' in out and "notes-rule" in out


HUSK_DOC = (
    "<?xml version='1.0' encoding='utf-8'?>\n"
    '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>t</title></head>\n'
    '  <body class="bible-body"><div class="appendix-section" id="bp-45" data-book-idx="45" epub:type="bodymatter">\n'
    '  <div class="book-title-frame">\n'
    '    <p class="bookpage-eyebrow">BOOK XLVI</p>\n'
    '    <h1 class="bookpage-title">The Prayer of Azariah and the Song of the Three Holy Children</h1>\n'
    '    <div class="bookpage-rule">❖</div>\n'
    "  </div>\n"
    "</div></body></html>"
)
# the healthy shape: book-title-page class WITH art — James's real tiny piece
TITLE_WITH_ART_DOC = HUSK_DOC.replace('class="appendix-section"', 'class="book-title-page"').replace(
    '<p class="bookpage-eyebrow">',
    '<img class="bookpage-art" src="images/book-jam.jpg" alt="art"/><p class="bookpage-eyebrow">',
)
# an appendix-section title frame whose book KEPT content in the same piece
HUSK_PLUS_CONTENT_DOC = HUSK_DOC.replace(
    "</div></body></html>",
    '</div><p class="verse"><a id="v-aes-1-1"></a>1 text</p></div></body></html>',
)


class TestIsHuskDoc:
    def test_appendix_title_only_no_art_is_husk(self):
        assert kindle_bisect.is_husk_doc(HUSK_DOC)

    def test_book_title_page_with_art_is_not_husk(self):
        assert not kindle_bisect.is_husk_doc(TITLE_WITH_ART_DOC)

    def test_appendix_title_with_verse_content_is_not_husk(self):
        assert not kindle_bisect.is_husk_doc(HUSK_PLUS_CONTENT_DOC)

    def test_ordinary_content_doc_is_not_husk(self):
        assert not kindle_bisect.is_husk_doc("<html><body><p>In the beginning</p></body></html>")


# the in-book HTML TOC page shape (index_split_000_00.html on the real
# artifact): a toc-book <li> per book — label + chapter rows, BOTH href the
# husk (the lone "1" chapter row pointing at a title page is itself the
# splice-residue tell).
TOC_PAGE_DOC = (
    "<html><body><ol>"
    '<li class="toc-book">\n'
    '  <p class="toc-book-label"><a href="husk.html#bp-45">The Prayer of Azariah and the Song '
    "of the Three Holy Children</a></p>\n"
    '    <p class="toc-chapter-row"><a href="husk.html#bp-45">1</a></p>\n'
    "  </li>\n"
    '<li class="toc-book">\n'
    '  <p class="toc-book-label"><a href="keep.html#bp-46">A Kept Book</a></p>\n'
    '    <p class="toc-chapter-row"><a href="keep.html#bp-46">1</a></p>\n'
    "  </li>\n"
    "</ol></body></html>"
)


def _mini_epub(path):
    import zipfile

    opf = (
        "<package><manifest>"
        '<item id="husk" href="husk.html" media-type="application/xhtml+xml"/>'
        '<item id="keep" href="keep.html" media-type="application/xhtml+xml"/>'
        '<item id="tocpage" href="toc_page.html" media-type="application/xhtml+xml"/>'
        '<item id="nav" href="nav.xhtml" properties="nav" media-type="application/xhtml+xml"/>'
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
        '</manifest><spine toc="ncx">'
        '<itemref idref="tocpage"/>'
        '<itemref idref="husk"/>'
        '<itemref idref="keep"/>'
        "</spine></package>"
    )
    nav = (
        '<html xmlns:epub="http://www.idpf.org/2007/ops"><body><nav epub:type="toc"><ol>'
        '<li><a href="husk.html#bp-45">The Prayer of Azariah and the Song of the Three Holy Children</a></li>'
        '<li><a href="keep.html#bp-46">A Kept Book</a></li>'
        "</ol></nav></body></html>"
    )
    # the husk's navPoint sits BETWEEN two kept ones — guards against the
    # cross-navPoint swallow (a non-tempered regex eats Before too; caught by
    # epubcheck "first playOrder value is not 1" on the real artifact).
    ncx = (
        "<ncx><navMap>"
        '<navPoint id="num_book_44" playOrder="34"><navLabel><text>Before</text></navLabel>'
        '<content src="toc_page.html#top"/></navPoint>'
        '<navPoint id="num_book_45" playOrder="35"><navLabel><text>Azariah</text></navLabel>'
        '<content src="husk.html#bp-45"/></navPoint>'
        '<navPoint id="num_book_46" playOrder="36"><navLabel><text>A Kept Book</text></navLabel>'
        '<content src="keep.html#bp-46"/></navPoint>'
        "</navMap></ncx>"
    )
    keep = TITLE_WITH_ART_DOC.replace('id="bp-45"', 'id="bp-46"')
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", zipfile.ZIP_STORED)
        z.writestr("content.opf", opf)
        z.writestr("nav.xhtml", nav)
        z.writestr("toc.ncx", ncx)
        z.writestr("husk.html", HUSK_DOC)
        z.writestr("keep.html", keep)
        z.writestr("toc_page.html", TOC_PAGE_DOC)
    return path


class TestBuildTochusk:
    def _run(self, tmp_path):
        import zipfile

        src = _mini_epub(tmp_path / "src.epub")
        out = tmp_path / "out.epub"
        stats = kindle_bisect.build_tochusk(src, out)
        with zipfile.ZipFile(out) as z:
            return stats, z.namelist(), {n: z.read(n).decode("utf-8") for n in z.namelist() if n != "mimetype"}

    def test_husk_file_removed_keep_file_survives(self, tmp_path):
        stats, names, _ = self._run(tmp_path)
        assert "husk.html" not in names and "keep.html" in names
        assert stats["husks_removed"] == 1

    def test_opf_manifest_and_spine_entries_removed(self, tmp_path):
        _, _, texts = self._run(tmp_path)
        opf = texts["content.opf"]
        assert "husk.html" not in opf and 'idref="husk"' not in opf
        assert "keep.html" in opf and 'idref="keep"' in opf

    def test_nav_and_ncx_entries_removed(self, tmp_path):
        _, _, texts = self._run(tmp_path)
        assert "husk.html" not in texts["nav.xhtml"]
        assert "A Kept Book" in texts["nav.xhtml"]
        assert "husk.html" not in texts["toc.ncx"]
        assert 'src="keep.html#bp-46"' in texts["toc.ncx"]

    def test_ncx_neighbors_survive_and_playorder_renumbered(self, tmp_path):
        import re

        _, _, texts = self._run(tmp_path)
        ncx = texts["toc.ncx"]
        # both navPoints flanking the husk's survive (cross-navPoint swallow guard)
        assert "<text>Before</text>" in ncx and "<text>A Kept Book</text>" in ncx
        # playOrder is renumbered contiguously from 1 (epubcheck RSC-005 guard)
        assert re.findall(r'playOrder="(\d+)"', ncx) == ["1", "2"]

    def test_html_toc_page_book_block_removed_whole(self, tmp_path):
        _, names, texts = self._run(tmp_path)
        assert "toc_page.html" in names
        toc = texts["toc_page.html"]
        assert "husk.html" not in toc and "Azariah" not in toc
        assert 'href="keep.html#bp-46">A Kept Book' in toc
        # the kept book's chapter row survives the surgical li removal
        assert 'class="toc-chapter-row"><a href="keep.html#bp-46">1</a>' in toc

    def test_no_surviving_doc_references_removed_files(self, tmp_path):
        _, _, texts = self._run(tmp_path)
        for name, text in texts.items():
            assert "husk.html" not in text, name

    def test_kept_docs_byte_identical(self, tmp_path):
        _, _, texts = self._run(tmp_path)
        assert texts["keep.html"] == TITLE_WITH_ART_DOC.replace('id="bp-45"', 'id="bp-46"')

    def test_mimetype_still_first_and_stored(self, tmp_path):
        import zipfile

        src = _mini_epub(tmp_path / "src.epub")
        out = tmp_path / "out.epub"
        kindle_bisect.build_tochusk(src, out)
        with zipfile.ZipFile(out) as z:
            infos = z.infolist()
            assert infos[0].filename == "mimetype"
            assert infos[0].compress_type == zipfile.ZIP_STORED


class TestDelinkLeavesTheRestAlone:
    def test_non_note_links_unchanged(self):
        for src in (KEEP_SYM, KEEP_PLAIN, KEEP_CH):
            assert delink_html(src) == src

    def test_stripped_text_is_byte_constant(self):
        import re

        src = NOTEREF + ASIDE + VNOTE_BACK + KEEP_SYM + "<p>between text</p>"
        strip = lambda s: re.sub(r"<[^>]+>", "", s)  # noqa: E731
        assert strip(delink_html(src)) == strip(src)

    def test_no_note_graph_markup_survives(self):
        src = NOTEREF + BADGE + VNOTE_BACK + NOTE_BACK + ASIDE
        out = delink_html(src)
        assert 'epub:type="noteref"' not in out
        assert "<aside" not in out
        assert 'class="vn-link" id' not in out or "<a" not in out

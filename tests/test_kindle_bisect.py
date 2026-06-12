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


# ── rung 3 HALF-SPINE ───────────────────────────────────────────────────
# Blocker #2 (the generic no-E-code internal error) survived BOTH tochusk and
# the chained delink-on-tochusk probe, so neither the TOC husks (gone) nor
# the note-graph (spans/divs) is the remaining cause — binary content search
# is next. The rung keeps a contiguous spine range, drops the rest, strips
# every nav/ncx/opf entry for dropped docs, and neutralizes any leftover
# cross-file link INTO a dropped doc (anchor → span) so the probe stays
# epubcheck-error-free and the Previewer verdict localizes the trigger.


def _mini_halfspine_epub(path, include_back=False):
    import zipfile

    opf = (
        "<package><manifest>"
        '<item id="d0" href="d0.html" media-type="application/xhtml+xml"/>'
        '<item id="d1" href="d1.html" media-type="application/xhtml+xml"/>'
        '<item id="d2" href="d2.html" media-type="application/xhtml+xml"/>'
        '<item id="d3" href="d3.html" media-type="application/xhtml+xml"/>'
        + ('<item id="back" href="back.html" media-type="application/xhtml+xml"/>' if include_back else "")
        + '<item id="css" href="stylesheet.css" media-type="text/css"/>'
        '<item id="nav" href="nav.xhtml" properties="nav" media-type="application/xhtml+xml"/>'
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
        '</manifest><spine toc="ncx">'
        '<itemref idref="d0"/><itemref idref="d1"/><itemref idref="d2"/><itemref idref="d3"/>'
        + ('<itemref idref="back"/>' if include_back else "")
        + '</spine><guide><reference type="text" title="Start" href="d3.html#top"/></guide></package>'
    )
    nav = (
        '<html xmlns:epub="http://www.idpf.org/2007/ops"><head><title>T</title>'
        '<link rel="stylesheet" type="text/css" href="stylesheet.css"/></head>'
        "<body>"
        '<nav epub:type="toc"><ol>'
        '<li><a href="d0.html#a">D0</a></li><li><a href="d1.html#a">D1</a></li>'
        '<li><a href="d2.html#a">D2</a></li><li><a href="d3.html#a">D3</a></li>'
        + ('<li><a href="back.html">Colophon</a></li>' if include_back else "")
        + "</ol></nav></body></html>"
    )
    ncx = (
        "<ncx><navMap>"
        '<navPoint id="n0" playOrder="1"><navLabel><text>D0</text></navLabel><content src="d0.html#a"/></navPoint>'
        '<navPoint id="n1" playOrder="2"><navLabel><text>D1</text></navLabel><content src="d1.html#a"/></navPoint>'
        '<navPoint id="n2" playOrder="3"><navLabel><text>D2</text></navLabel><content src="d2.html#a"/></navPoint>'
        '<navPoint id="n3" playOrder="4"><navLabel><text>D3</text></navLabel><content src="d3.html#a"/></navPoint>'
        + (
            '<navPoint id="n4" playOrder="5"><navLabel><text>Colophon</text></navLabel>'
            '<content src="back.html"/></navPoint>'
            if include_back
            else ""
        )
        + "</navMap></ncx>"
    )
    d0 = (
        '<html><body><p id="a">zero '
        '<a href="d1.html#a">to kept</a> '
        '<a href="d2.html#a" epub:type="noteref">to dropped</a>'
        "</p></body></html>"
    )
    docs = {
        "d0.html": d0,
        "d1.html": '<html><body><p id="a">one</p></body></html>',
        "d2.html": '<html><body><p id="a">two</p></body></html>',
        "d3.html": '<html><body><p id="a">three</p></body></html>',
    }
    if include_back:
        docs["back.html"] = "<html><body><p>colophon</p></body></html>"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", zipfile.ZIP_STORED)
        z.writestr("content.opf", opf)
        z.writestr("nav.xhtml", nav)
        z.writestr("toc.ncx", ncx)
        z.writestr("stylesheet.css", "p { margin: 0; }")
        for n, t in docs.items():
            z.writestr(n, t)
    return path


class TestBuildHalfspine:
    def _run(self, tmp_path, keep, include_back=False):
        import zipfile

        src = _mini_halfspine_epub(tmp_path / "src.epub", include_back=include_back)
        out = tmp_path / "out.epub"
        stats = kindle_bisect.build_halfspine(src, out, keep=keep)
        with zipfile.ZipFile(out) as z:
            return stats, z.namelist(), {n: z.read(n).decode("utf-8") for n in z.namelist() if n != "mimetype"}

    def test_first_half_kept_second_dropped(self, tmp_path):
        stats, names, _ = self._run(tmp_path, "first")
        assert "d0.html" in names and "d1.html" in names
        assert "d2.html" not in names and "d3.html" not in names
        assert stats["docs_kept"] == 2 and stats["docs_dropped"] == 2

    def test_second_half_kept_first_dropped(self, tmp_path):
        _, names, _ = self._run(tmp_path, "second")
        assert "d2.html" in names and "d3.html" in names
        assert "d0.html" not in names and "d1.html" not in names

    def test_explicit_range_keeps_that_slice(self, tmp_path):
        _, names, _ = self._run(tmp_path, "1:3")
        assert "d1.html" in names and "d2.html" in names
        assert "d0.html" not in names and "d3.html" not in names

    def test_opf_entries_and_guide_ref_stripped(self, tmp_path):
        _, _, texts = self._run(tmp_path, "first")
        opf = texts["content.opf"]
        for b in ("d2.html", "d3.html"):
            assert b not in opf
        assert 'idref="d2"' not in opf and 'idref="d3"' not in opf
        assert 'idref="d0"' in opf and 'idref="d1"' in opf

    def test_nav_and_ncx_pruned_and_renumbered(self, tmp_path):
        import re

        _, _, texts = self._run(tmp_path, "first")
        assert "d2.html" not in texts["nav.xhtml"] and "d3.html" not in texts["nav.xhtml"]
        ncx = texts["toc.ncx"]
        assert "d2.html" not in ncx and "d3.html" not in ncx
        assert re.findall(r'playOrder="(\d+)"', ncx) == ["1", "2"]

    def test_cross_file_link_into_dropped_becomes_span(self, tmp_path):
        _, _, texts = self._run(tmp_path, "first")
        d0 = texts["d0.html"]
        assert "d2.html" not in d0, "dangling href into a dropped doc must be neutralized"
        assert "to dropped</span>" in d0 and 'epub:type="noteref"' not in d0
        assert '<a href="d1.html#a">to kept</a>' in d0, "links into kept docs survive untouched"

    def test_fragmentless_backmatter_entries_removed_whole(self, tmp_path):
        # the real artifact's back-matter lis (Sources/Reference Tables/Topical
        # Index/Colophon) carry NO #fragment; a span-converted li is invalid
        # nav markup (li needs a, or span + nested ol) — epubcheck RSC-005 ×4.
        _, names, texts = self._run(tmp_path, "first", include_back=True)
        assert "back.html" not in names
        nav = texts["nav.xhtml"]
        assert "back.html" not in nav and "<li><span>Colophon</span></li>" not in nav
        assert "Colophon" not in nav, "the fragment-less li must be removed whole, not span-converted"
        assert "back.html" not in texts["toc.ncx"]

    def test_assets_and_nav_docs_always_survive(self, tmp_path):
        _, names, _ = self._run(tmp_path, "second")
        for keeper in ("stylesheet.css", "nav.xhtml", "toc.ncx", "content.opf"):
            assert keeper in names

    def test_nav_head_survives_keep_second(self, tmp_path):
        # `<li[^>]*>` also matches `<link …>` — on keep=second the very FIRST
        # toc li targets a dropped doc, so a scan started at the head's <link>
        # reaches that href with no intervening </li> and swallows
        # </head><body><nav><ol> whole (epubcheck RSC-016 "head must be
        # terminated" on the real half-second probe). `<li\b` must not match
        # `<link`.
        _, _, texts = self._run(tmp_path, "second")
        nav = texts["nav.xhtml"]
        assert "</head>" in nav and "<nav " in nav.replace("epub:type", " epub:type") or "</head>" in nav
        assert "<link " in nav, "the stylesheet link in <head> must survive"
        assert 'href="d2.html#a"' in nav and 'href="d3.html#a"' in nav

    def test_emptied_guide_is_removed_whole(self, tmp_path):
        # keep=first drops d3; the guide's ONLY reference targets d3 — a
        # leftover `<guide></guide>` is invalid OPF (RSC-005 "guide
        # incomplete; missing required element reference").
        _, _, texts = self._run(tmp_path, "first")
        assert "<guide" not in texts["content.opf"]

    def test_mimetype_still_first_and_stored(self, tmp_path):
        import zipfile

        src = _mini_halfspine_epub(tmp_path / "src.epub")
        out = tmp_path / "out.epub"
        kindle_bisect.build_halfspine(src, out, keep="first")
        with zipfile.ZipFile(out) as z:
            infos = z.infolist()
            assert infos[0].filename == "mimetype"
            assert infos[0].compress_type == zipfile.ZIP_STORED


# ── rung IMGSTRIP ───────────────────────────────────────────────────────
# The halfspine P/P + 182-doc/2MB-split FAIL matrix leaves two candidate
# blocker-#2 drivers: aggregate doc-count and total bytes/converter work.
# Images are 10.3MB of the 25MB artifact; this rung collapses every raster
# to a 1×1 placeholder of the SAME format — filenames, manifest, and every
# content doc stay byte-identical, so the Previewer verdict isolates the
# image byte-mass one-variable (epubcheck stays clean: signature still
# matches the declared media-type).


def _gradient_image_bytes(fmt, size=128):
    """A deterministic multi-KB raster — must dwarf the 1×1 placeholder."""
    from io import BytesIO

    from PIL import Image

    im = Image.new("RGB", (size, size))
    im.putdata([(x % 256, y % 256, (x * y) % 256) for y in range(size) for x in range(size)])
    buf = BytesIO()
    im.save(buf, format=fmt)
    return buf.getvalue()


def _mini_imgstrip_epub(path):
    import zipfile

    opf = (
        "<package><manifest>"
        '<item id="doc" href="doc.html" media-type="application/xhtml+xml"/>'
        '<item id="css" href="stylesheet.css" media-type="text/css"/>'
        '<item id="cov" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>'
        '<item id="art" href="images/art.png" media-type="image/png"/>'
        '<item id="anim" href="images/anim.gif" media-type="image/gif"/>'
        '</manifest><spine><itemref idref="doc"/></spine></package>'
    )
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", zipfile.ZIP_STORED)
        z.writestr("content.opf", opf)
        z.writestr("doc.html", '<html><body><img src="images/cover.jpg" alt="c"/><p>text</p></body></html>')
        z.writestr("stylesheet.css", "p { margin: 0; }")
        z.writestr("images/cover.jpg", _gradient_image_bytes("JPEG"))
        z.writestr("images/art.png", _gradient_image_bytes("PNG"))
        z.writestr("images/anim.gif", _gradient_image_bytes("GIF"))
    return path


class TestBuildImgstrip:
    def _run(self, tmp_path):
        import zipfile

        src = _mini_imgstrip_epub(tmp_path / "src.epub")
        out = tmp_path / "out.epub"
        stats = kindle_bisect.build_imgstrip(src, out)
        with zipfile.ZipFile(src) as z:
            before = {n: z.read(n) for n in z.namelist()}
        with zipfile.ZipFile(out) as z:
            after = {n: z.read(n) for n in z.namelist()}
        return stats, before, after

    def test_every_raster_shrinks_and_keeps_its_format(self, tmp_path):
        from io import BytesIO

        from PIL import Image

        _, before, after = self._run(tmp_path)
        for name, fmt in (("images/cover.jpg", "JPEG"), ("images/art.png", "PNG"), ("images/anim.gif", "GIF")):
            assert len(after[name]) < len(before[name]), name
            im = Image.open(BytesIO(after[name]))
            assert im.format == fmt, f"{name}: placeholder must keep the declared format"
            assert im.size == (1, 1)

    def test_non_image_entries_byte_identical(self, tmp_path):
        _, before, after = self._run(tmp_path)
        for name in ("mimetype", "content.opf", "doc.html", "stylesheet.css"):
            assert after[name] == before[name], name

    def test_no_entry_added_or_dropped(self, tmp_path):
        _, before, after = self._run(tmp_path)
        assert sorted(before) == sorted(after)

    def test_stats_report_the_byte_shrink(self, tmp_path):
        stats, before, after = self._run(tmp_path)
        rasters = ("images/cover.jpg", "images/art.png", "images/anim.gif")
        assert stats["images_replaced"] == 3
        assert stats["image_bytes_before"] == sum(len(before[n]) for n in rasters)
        assert stats["image_bytes_after"] == sum(len(after[n]) for n in rasters)
        assert stats["image_bytes_after"] < stats["image_bytes_before"]

    def test_mimetype_still_first_and_stored(self, tmp_path):
        import zipfile

        src = _mini_imgstrip_epub(tmp_path / "src.epub")
        out = tmp_path / "out.epub"
        kindle_bisect.build_imgstrip(src, out)
        with zipfile.ZipFile(out) as z:
            infos = z.infolist()
            assert infos[0].filename == "mimetype"
            assert infos[0].compress_type == zipfile.ZIP_STORED


# ── rung VNOTEGUT ───────────────────────────────────────────────────────
# The volume ladder cuts apparatus bytes and popup COUNT together, so a
# per-popup converter cost (33,969 noteref→footnote structures) is still
# confounded with raw byte volume. This rung guts every per-verse `vnote`
# popup aside to its FIRST <p> (the verse header) — count and ids constant,
# bytes slashed (~34MB raw, below the passing halves) — so the verdict
# discriminates count-driver (FAIL ⇒ only two-volume ships) from
# bytes-driver (PASS ⇒ compaction/language knobs viable). Chapter-end
# notes-sections and all text outside vnote asides stay byte-identical.

VNOTE_DOC = (
    "<html><body>"
    '<p id="v-exo-1-1">verse text '
    '<a class="vn-link" href="#vnote-exo-1-1" epub:type="noteref"><span class="vn">1</span></a>'
    "</p>"
    '<aside class="vnote" id="vnote-exo-1-1" epub:type="footnote">'
    "<p><strong>Exodus 1:1.</strong></p>"
    '<p class="vnote-source-label"><span class="vn-sep"> ◦ </span>Hebrew (Masoretic / WLC)</p>'
    '<p class="vnote-hebrew" dir="rtl" lang="he"><em>שְׁמוֹת</em></p>'
    '<p class="vnote-source-label"><span class="vn-sep"> ◦ </span>Greek (Septuagint / Swete)</p>'
    '<p class="vnote-greek" lang="grc">ΤΑΥΤΑ τὰ ὀνόματα</p>'
    "</aside>"
    '<aside class="notes-section" epub:type="footnotes"><hr class="notes-rule"/>'
    '<aside class="verse-notes" id="vnotes-exo-1-1" epub:type="footnote"><p>note body</p></aside>'
    "</aside>"
    "</body></html>"
)


def _mini_vnotegut_epub(path):
    import zipfile

    opf = (
        "<package><manifest>"
        '<item id="doc" href="doc.html" media-type="application/xhtml+xml"/>'
        "</manifest><spine>"
        '<itemref idref="doc"/>'
        "</spine></package>"
    )
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", zipfile.ZIP_STORED)
        z.writestr("content.opf", opf)
        z.writestr("doc.html", VNOTE_DOC)
    return path


# ── rung LANGCAP ────────────────────────────────────────────────────────
# The SHIP-CANDIDATE simulator (user pick, pre-recorded via the board):
# per-reader popup-language cap at 2 = keep Hebrew + Greek (drop Latin +
# Arabic content paragraphs AND every source-label paragraph, re-inserting
# a compact label before each kept content para) + compact the per-verse
# popup header to "Book N:M". vnotegut PASS proved the driver is BYTES at
# constant popup count, so this artifact (~48.7MB raw — inside the unknown
# (45.3, 55.2) band) gets its own oracle verdict BEFORE the design is
# encoded into the build pipeline.


class TestLangcapHtml:
    def test_latin_and_arabic_paras_dropped_hebrew_greek_kept(self):
        out = kindle_bisect.langcap_html(
            VNOTE_DOC.replace(
                '<p class="vnote-greek" lang="grc">ΤΑΥΤΑ τὰ ὀνόματα</p>',
                '<p class="vnote-greek" lang="grc">ΤΑΥΤΑ τὰ ὀνόματα</p>'
                '<p class="vnote-source-label"><span class="vn-sep"> ◦ </span>Latin (Clementine Vulgate)</p>'
                '<p class="vnote-vulgate" lang="la">Haec sunt nomina</p>'
                '<p class="vnote-source-label"><span class="vn-sep"> ◦ </span>Arabic (Van Dyck)</p>'
                '<p class="vnote-arabic" dir="rtl" lang="ar">وهذه أسماء</p>',
            )
        )
        assert "vnote-vulgate" not in out and "vnote-arabic" not in out
        assert "Clementine Vulgate" not in out and "Van Dyck" not in out
        assert '<p class="vnote-hebrew"' in out and '<p class="vnote-greek"' in out

    def test_labels_compacted_to_short_forms(self):
        out = kindle_bisect.langcap_html(VNOTE_DOC)
        assert "Masoretic" not in out and "Septuagint" not in out
        assert '<p class="vnote-source-label">Heb</p><p class="vnote-hebrew"' in out
        assert '<p class="vnote-source-label">Grc</p><p class="vnote-greek"' in out

    def test_header_compacted_to_book_ref(self):
        src = VNOTE_DOC.replace(
            "<p><strong>Exodus 1:1.</strong></p>",
            "<p><strong>The Second Book of Moses, Exodus 1:1.</strong></p>",
        )
        out = kindle_bisect.langcap_html(src)
        assert "<p><strong>Exodus 1:1</strong></p>" in out
        assert "Second Book of Moses" not in out

    def test_notes_sections_and_verse_text_untouched(self):
        out = kindle_bisect.langcap_html(VNOTE_DOC)
        assert '<aside class="verse-notes" id="vnotes-exo-1-1" epub:type="footnote"><p>note body</p></aside>' in out
        assert '<a class="vn-link" href="#vnote-exo-1-1" epub:type="noteref"><span class="vn">1</span></a>' in out

    def test_aside_count_and_ids_preserved(self):
        import re

        out = kindle_bisect.langcap_html(VNOTE_DOC)
        assert len(re.findall(r'<aside class="vnote"', out)) == 1
        assert 'id="vnote-exo-1-1"' in out


class TestLangcapKeepGroups:
    """cap=1 measurement (langcap FAIL follow-up, threshold < 48.7MB):
    keep_groups parameterizes WHICH language groups survive — cap-1
    Hebrew-only is the next ladder rung (~ proven-passing territory)."""

    def test_hebrew_only_drops_greek_too(self):
        out = kindle_bisect.langcap_html(VNOTE_DOC, keep_groups=("hebrew",))
        assert "vnote-greek" not in out and "Septuagint" not in out
        assert '<p class="vnote-source-label">Heb</p><p class="vnote-hebrew"' in out

    def test_greek_only_drops_hebrew(self):
        out = kindle_bisect.langcap_html(VNOTE_DOC, keep_groups=("greek",))
        assert "vnote-hebrew" not in out and "Masoretic" not in out
        assert '<p class="vnote-source-label">Grc</p><p class="vnote-greek"' in out

    def test_default_is_hebrew_greek(self):
        assert kindle_bisect.langcap_html(VNOTE_DOC) == kindle_bisect.langcap_html(
            VNOTE_DOC, keep_groups=("hebrew", "greek")
        )

    def test_unknown_group_raises(self):
        import pytest

        with pytest.raises(ValueError):
            kindle_bisect.langcap_html(VNOTE_DOC, keep_groups=("klingon",))

    def test_aside_count_preserved_under_cap1(self):
        import re

        out = kindle_bisect.langcap_html(VNOTE_DOC, keep_groups=("hebrew",))
        assert len(re.findall(r'<aside class="vnote"', out)) == 1


class TestBuildVnotegut:
    def _run(self, tmp_path):
        import zipfile

        src = _mini_vnotegut_epub(tmp_path / "src.epub")
        out = tmp_path / "out.epub"
        stats = kindle_bisect.build_vnotegut(src, out)
        with zipfile.ZipFile(out) as z:
            return stats, {n: z.read(n) for n in z.namelist()}

    def test_vnote_count_and_id_survive_but_body_is_gutted(self, tmp_path):
        import re

        stats, after = self._run(tmp_path)
        doc = after["doc.html"].decode("utf-8")
        assert len(re.findall(r'<aside class="vnote"', doc)) == 1
        assert 'id="vnote-exo-1-1"' in doc and 'epub:type="footnote"' in doc
        assert "<p><strong>Exodus 1:1.</strong></p>" in doc, "the first <p> (verse header) must survive"
        assert "vnote-hebrew" not in doc and "vnote-greek" not in doc and "vnote-source-label" not in doc
        assert stats["vnotes_gutted"] == 1
        assert stats["bytes_after"] < stats["bytes_before"]

    def test_noteref_link_and_verse_text_untouched(self, tmp_path):
        _, after = self._run(tmp_path)
        doc = after["doc.html"].decode("utf-8")
        assert '<a class="vn-link" href="#vnote-exo-1-1" epub:type="noteref"><span class="vn">1</span></a>' in doc

    def test_notes_section_asides_untouched(self, tmp_path):
        _, after = self._run(tmp_path)
        doc = after["doc.html"].decode("utf-8")
        assert '<aside class="verse-notes" id="vnotes-exo-1-1" epub:type="footnote"><p>note body</p></aside>' in doc

    def test_non_content_entries_byte_identical(self, tmp_path):
        import zipfile

        src = _mini_vnotegut_epub(tmp_path / "src.epub")
        out = tmp_path / "out.epub"
        kindle_bisect.build_vnotegut(src, out)
        with zipfile.ZipFile(src) as z:
            before = {n: z.read(n) for n in z.namelist()}
        with zipfile.ZipFile(out) as z:
            after = {n: z.read(n) for n in z.namelist()}
        assert after["content.opf"] == before["content.opf"]
        assert after["mimetype"] == before["mimetype"]

    def test_mimetype_still_first_and_stored(self, tmp_path):
        import zipfile

        src = _mini_vnotegut_epub(tmp_path / "src.epub")
        out = tmp_path / "out.epub"
        kindle_bisect.build_vnotegut(src, out)
        with zipfile.ZipFile(out) as z:
            infos = z.infolist()
            assert infos[0].filename == "mimetype"
            assert infos[0].compress_type == zipfile.ZIP_STORED

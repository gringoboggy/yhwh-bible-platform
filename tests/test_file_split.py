"""RX Phase 4b — build-time EPUB file-splitter (apply_file_split).

The splitter is a per-edition BUILD-TIME post-pass (like apply_badge_markers): it
splits the 2-5 MB ``index_split_*.html`` files of the per-edition temp tree into
~0.4 MB pieces so e-ink Kobo can render them, rewrites every cross-file href to the
new piece that now holds the target id, distributes each file's single trailing
``notes-section`` into per-piece notes-sections (so the bare ``#id`` footnote/popup
contract stays SAME-FILE = native popups on every reader), and regenerates the OPF
manifest+spine + nav.xhtml + toc.ncx. ``epub_working/`` (the canonical 61-file base)
is never touched.

These tests pin the contract with small synthetic documents whose structure mirrors
the real calibre split files (verified against epub_working in the RX Phase 4
discovery), plus a real-build integration test gated behind the slow marker.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


# A two-chapter synthetic split file mirroring the real structure:
#   head → body{ book-title-page(bp) · ch1(<p ch-heading> form) · ch2(<a ch-anchor> form) ·
#   single trailing notes-section with verse-popup (vnote-) + editorial (note-) asides } → tail.
# ch1 carries a CROSS-CHAPTER bare link (#v-gen-2-1) whose target lives in ch2 — the
# split must turn that into a cross-FILE link once the two chapters land in two pieces.
SYNTH = """<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
<head>
<title>Converted Ebook</title>
<link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body class="bible-body">
<div class="book-title-page" id="bp-00" data-book-idx="0" epub:type="bodymatter"><h1>Genesis</h1></div>
<p id="ch-b00-c1" class="ch-heading"><span class="section-heading"><span class="bold-num">1</span></span></p>
<p class="verse-p"><a class="vn-link" id="v-gen-1-1" href="#vnote-gen-1-1" epub:type="noteref"><span class="vn">1</span></a> In the beginning<a class="note-ref note-word" id="ref-x1" href="#note-x1" epub:type="noteref"><sup class="marker-num">1</sup></a> God created. <a href="#v-gen-2-1">cf 2:1</a> <a href="index_split_009.html#v-exo-1-1">cf Exo 1:1</a></p>
<a id="ch-b00-c2" class="ch-anchor"></a><p id="page_2" class="ch-heading"><span class="section-heading"><span class="bold-num">2</span></span></p>
<p class="verse-p"><a class="vn-link" id="v-gen-2-1" href="#vnote-gen-2-1" epub:type="noteref"><span class="vn">1</span></a> Thus the heavens<a class="note-ref note-word" id="ref-x2" href="#note-x2" epub:type="noteref"><sup class="marker-num">1</sup></a> were finished.</p>
<aside class="notes-section" epub:type="footnotes" hidden="">
<aside class="note note-word" id="vnote-gen-1-1" epub:type="footnote"><p>verse one popup</p></aside>
<aside class="note note-word" id="note-x1" epub:type="footnote"><p>note one <a href="#ref-x1" class="note-back">↩</a></p></aside>
<aside class="note note-word" id="vnote-gen-2-1" epub:type="footnote"><p>verse two popup</p></aside>
<aside class="note note-word" id="note-x2" epub:type="footnote"><p>note two <a href="#ref-x2" class="note-back">↩</a></p></aside>
</aside>
</body></html>"""


class TestSplitHtmlDocumentUnit:
    """``split_html_document(text, stem, target)`` cuts one file into well-formed
    pieces at top-level book/chapter boundaries, never mid-chapter, and gives each
    piece a notes-section holding exactly the asides its chapters reference."""

    def _split(self, target):
        from scripts.build_edition import split_html_document

        return split_html_document(SYNTH, "index_split_007", target)

    def test_no_split_when_under_target(self):
        pieces = self._split(10_000_000)
        assert len(pieces) == 1
        name, text = pieces[0]
        assert name == "index_split_007.html", "an unsplit file must keep its original name"
        assert text == SYNTH, "an unsplit file must be byte-identical (zero churn)"

    def test_splits_at_chapter_boundary_into_two_pieces(self):
        # target chosen so book-title-page+ch1 pack into piece 0 and ch2 into piece 1
        pieces = self._split(1000)
        assert len(pieces) == 2, f"expected 2 pieces, got {len(pieces)}"
        names = [n for n, _ in pieces]
        assert names == ["index_split_007_00.html", "index_split_007_01.html"]

    def test_every_piece_is_wellformed_standalone_xhtml(self):
        for _name, text in self._split(1000):
            assert text.startswith("<?xml"), "piece lost the XML prolog"
            assert '<html xmlns="http://www.w3.org/1999/xhtml"' in text
            assert '<link rel="stylesheet" type="text/css" href="stylesheet.css"/>' in text
            assert '<body class="bible-body">' in text
            assert text.rstrip().endswith("</html>")
            # balanced div + aside tags (cut at a top-level boundary)
            assert text.count("<div") == text.count("</div>"), "unbalanced <div> in a piece"
            assert text.count("<aside") == text.count("</aside>"), "unbalanced <aside> in a piece"

    def test_book_title_and_chapter_one_lead_the_first_piece(self):
        p0 = dict(self._split(1000))["index_split_007_00.html"]
        assert 'id="bp-00"' in p0, "book-title-page must lead the first piece"
        assert 'id="ch-b00-c1"' in p0, "chapter 1 starts in the first piece"

    def test_no_content_lost_across_pieces(self):
        # Every anchor + aside id from the source survives exactly once across the pieces
        # (EPUB spine concatenates pieces, so a mid-chapter file cut is invisible to readers).
        joined = "".join(t for _, t in self._split(1000))
        for marker in (
            'id="bp-00"',
            'id="ch-b00-c1"',
            'id="ch-b00-c2"',
            'id="v-gen-1-1"',
            'id="v-gen-2-1"',
            'id="vnote-gen-1-1"',
            'id="note-x1"',
            'id="vnote-gen-2-1"',
            'id="note-x2"',
        ):
            assert joined.count(marker) == 1, (
                f"{marker} must appear exactly once across pieces, got {joined.count(marker)}"
            )

    def test_notes_distributed_to_referencing_piece(self):
        d = dict(self._split(1000))
        p0, p1 = d["index_split_007_00.html"], d["index_split_007_01.html"]
        # ch1's asides (the verse popup + the editorial note it references) live with ch1
        assert 'id="vnote-gen-1-1"' in p0 and 'id="note-x1"' in p0
        assert 'id="vnote-gen-1-1"' not in p1 and 'id="note-x1"' not in p1
        # ch2's asides live with ch2
        assert 'id="vnote-gen-2-1"' in p1 and 'id="note-x2"' in p1
        assert 'id="vnote-gen-2-1"' not in p0 and 'id="note-x2"' not in p0
        # each piece keeps a notes-section wrapper around its asides
        assert '<aside class="notes-section"' in p0 and '<aside class="notes-section"' in p1

    def test_same_file_footnote_links_stay_resolvable_in_piece(self):
        # the marker→aside and aside→marker bare links must both be intra-piece
        d = dict(self._split(1000))
        for text in d.values():
            for frag in re.findall(r'href="#(note-[^"]+|ref-[^"]+|vnote-[^"]+)"', text):
                assert f'id="{frag}"' in text, f"bare #{frag} unresolved within its piece"


# A two-chapter file mirroring the real Acts 21→22 shape that broke catholic-study: ch2's
# anchor (and verses) are NESTED inside a <p class="verse-p"> (not a top-level sibling), so
# a cut at the ch2 boundary lands INSIDE that paragraph. ch1 ends with the ch2 number as a
# trailing section-heading inside ch1's own <p>. Heavy per-verse asides force a split.
NESTED = (
    "<?xml version='1.0' encoding='utf-8'?>\n"
    '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">\n'
    '<head><title>T</title><link rel="stylesheet" type="text/css" href="stylesheet.css"/></head>\n'
    '<body class="bible-body">\n'
    '<a id="ch-b00-c1" class="ch-anchor"></a><p id="page_1" class="ch-heading"><span class="bold-num">1</span></p>\n'
    '<p class="verse-p">'
    '<a class="vn-link" id="v-x-1-1" href="#vnote-x-1-1" epub:type="noteref"><span class="vn">1</span></a> ch1 v1'
    '<a class="note-ref note-word" id="ref-a1" href="#note-a1" epub:type="noteref"><sup>1</sup></a> '
    '<a class="vn-link" id="v-x-1-2" href="#vnote-x-1-2" epub:type="noteref"><span class="vn">2</span></a> ch1 v2'
    '<a class="note-ref note-word" id="ref-a2" href="#note-a2" epub:type="noteref"><sup>1</sup></a> '
    '<span class="section-heading"><span class="bold-num">2</span></span></p>\n'
    '<p class="verse-p"><a id="ch-b00-c2" class="ch-anchor"></a>'
    '<a class="vn-link" id="v-x-2-1" href="#vnote-x-2-1" epub:type="noteref"><span class="vn">1</span></a> ch2 v1'
    '<a class="note-ref note-word" id="ref-a3" href="#note-a3" epub:type="noteref"><sup>1</sup></a> '
    '<a class="vn-link" id="v-x-2-2" href="#vnote-x-2-2" epub:type="noteref"><span class="vn">2</span></a> ch2 v2'
    '<a class="note-ref note-word" id="ref-a4" href="#note-a4" epub:type="noteref"><sup>1</sup></a></p>\n'
    '<aside class="notes-section" epub:type="footnotes" hidden="">\n'
    + "".join(
        f'<aside class="note note-word" id="{aid}" epub:type="footnote"><p>{"X" * 200}</p></aside>\n'
        for aid in (
            "vnote-x-1-1",
            "note-a1",
            "vnote-x-1-2",
            "note-a2",
            "vnote-x-2-1",
            "note-a3",
            "vnote-x-2-2",
            "note-a4",
        )
    )
    + "</aside>\n"
    "</body></html>"
)


class TestStackAwareSplit:
    """The unified splitter may cut INSIDE a <p>/<div>; a stack-aware wrapper reopens what
    a piece starts inside and closes what is still open at its end, so every piece is
    well-formed — the bug that failed catholic-study (a chapter anchor nested in the
    previous chapter's <p class="verse-p">)."""

    def test_nested_chapter_anchor_pieces_are_wellformed(self):
        from scripts.build_edition import split_html_document

        pieces = split_html_document(NESTED, "index_split_009", 500)
        assert len(pieces) >= 2, "heavy per-verse asides must force a split"
        for name, t in pieces:
            assert len(re.findall(r"<p\b", t)) == t.count("</p>"), f"{name}: unbalanced <p>"
            assert t.count("<aside") == t.count("</aside>"), f"{name}: unbalanced <aside>"
            assert t.count("<body") == t.count("</body>"), f"{name}: unbalanced <body>"
            assert t.rstrip().endswith("</html>")
        # nothing lost: each chapter anchor + verse + aside survives exactly once
        joined = "".join(t for _, t in pieces)
        for marker in (
            'id="ch-b00-c1"',
            'id="ch-b00-c2"',
            'id="v-x-2-1"',
            'id="vnote-x-2-1"',
            'id="note-a4"',
        ):
            assert joined.count(marker) == 1, f"{marker} count {joined.count(marker)} != 1"

    def test_split_at_paragraph_reopens_verse_p(self):
        from scripts.build_edition import split_html_document

        d = dict(split_html_document(NESTED, "index_split_009", 500))
        # if ch2 landed in its own piece, that piece reopens the <p class="verse-p"> it started inside
        for name, t in d.items():
            if 'id="ch-b00-c2"' in t and 'id="ch-b00-c1"' not in t:
                body = t[t.index("<body") :]
                assert '<p class="verse-p">' in body[: body.index('id="ch-b00-c2"')], (
                    f"{name}: piece starting inside a verse-p must reopen it"
                )

    def test_stack_at_positions(self):
        from scripts.build_edition import _stack_at_positions

        c = '<div class="d"><p class="verse-p"><a id="x">hi</a></p></div>'
        pos_in_a = c.index('<a id="x"')
        pos_after = len(c)
        st = _stack_at_positions(c, [0, pos_in_a, pos_after])
        assert st[0] == []
        assert [_n(t) for t in st[pos_in_a]] == ["div", "p"], "inside <div><p> the open stack is [div, p]"
        assert st[pos_after] == [], "balanced content closes the stack"


def _n(open_tag):
    return re.match(r"<([a-zA-Z][a-zA-Z0-9:]*)", open_tag).group(1)


class TestRewriteLinks:
    """After splitting, ``apply_file_split`` resolves every cross-piece reference:
    full ``index_split_NNN.html#frag`` links remap to the piece holding frag, and a
    bare ``#frag`` that now lands in another piece is promoted to a cross-file link."""

    def test_cross_chapter_bare_link_becomes_cross_file(self, tmp_path, monkeypatch):
        # Drive split_html_document + the link rewrite directly via a tiny tmp tree.
        from scripts import build_edition as be

        tmp = tmp_path / "build"
        tmp.mkdir()
        (tmp / "index_split_007.html").write_text(SYNTH, encoding="utf-8")
        # minimal opf/nav/ncx so the regen steps have something to edit
        (tmp / "content.opf").write_text(_MIN_OPF, encoding="utf-8")
        (tmp / "nav.xhtml").write_text(_MIN_NAV, encoding="utf-8")
        (tmp / "toc.ncx").write_text(_MIN_NCX, encoding="utf-8")

        stats = be.apply_file_split(tmp, {"id": "x", "reader_file_split": True, "reader_file_split_target": 1000})
        assert stats["files_split"] == 1
        assert stats["pieces_created"] == 2

        p0 = (tmp / "index_split_007_00.html").read_text(encoding="utf-8")
        # ch1's #v-gen-2-1 (target now in piece 01) was promoted to a cross-file link
        assert 'href="index_split_007_01.html#v-gen-2-1"' in p0
        assert 'href="#v-gen-2-1"' not in p0
        # ch1's own footnote bare links stay bare (same piece)
        assert 'href="#note-x1"' in p0
        # the original file is gone; pieces replace it
        assert not (tmp / "index_split_007.html").exists()

    def test_opf_manifest_and_spine_expanded(self, tmp_path):
        from scripts import build_edition as be

        tmp = tmp_path / "build"
        tmp.mkdir()
        (tmp / "index_split_007.html").write_text(SYNTH, encoding="utf-8")
        (tmp / "content.opf").write_text(_MIN_OPF, encoding="utf-8")
        (tmp / "nav.xhtml").write_text(_MIN_NAV, encoding="utf-8")
        (tmp / "toc.ncx").write_text(_MIN_NCX, encoding="utf-8")

        be.apply_file_split(tmp, {"id": "x", "reader_file_split": True, "reader_file_split_target": 1000})
        opf = (tmp / "content.opf").read_text(encoding="utf-8")
        # old single item/itemref gone; two piece items + itemrefs present, in order
        assert 'href="index_split_007.html"' not in opf
        assert 'href="index_split_007_00.html"' in opf and 'href="index_split_007_01.html"' in opf
        i0 = opf.index("index_split_007_00.html")
        i1 = opf.index("index_split_007_01.html")
        assert i0 < i1, "piece spine/manifest order must follow piece order"
        # spine itemref count for the pieces == 2
        ids = re.findall(r'<item id="([^"]+)" href="index_split_007_0\d\.html"', opf)
        assert len(ids) == 2
        for pid in ids:
            assert f'<itemref idref="{pid}"/>' in opf

    def test_nav_and_ncx_book_anchor_remapped(self, tmp_path):
        from scripts import build_edition as be

        tmp = tmp_path / "build"
        tmp.mkdir()
        (tmp / "index_split_007.html").write_text(SYNTH, encoding="utf-8")
        (tmp / "content.opf").write_text(_MIN_OPF, encoding="utf-8")
        (tmp / "nav.xhtml").write_text(_MIN_NAV, encoding="utf-8")
        (tmp / "toc.ncx").write_text(_MIN_NCX, encoding="utf-8")

        be.apply_file_split(tmp, {"id": "x", "reader_file_split": True, "reader_file_split_target": 1000})
        nav = (tmp / "nav.xhtml").read_text(encoding="utf-8")
        ncx = (tmp / "toc.ncx").read_text(encoding="utf-8")
        # bp-00 lives in piece 00 → both nav + ncx now point there
        assert 'href="index_split_007_00.html#bp-00"' in nav
        assert 'src="index_split_007_00.html#bp-00"' in ncx
        assert "index_split_007.html#bp-00" not in nav
        assert "index_split_007.html#bp-00" not in ncx

    def test_deterministic(self, tmp_path):
        from scripts import build_edition as be

        def run(tag):
            d = tmp_path / "run" / tag
            d.mkdir(parents=True)
            (d / "index_split_007.html").write_text(SYNTH, encoding="utf-8")
            (d / "content.opf").write_text(_MIN_OPF, encoding="utf-8")
            (d / "nav.xhtml").write_text(_MIN_NAV, encoding="utf-8")
            (d / "toc.ncx").write_text(_MIN_NCX, encoding="utf-8")
            be.apply_file_split(d, {"id": "x", "reader_file_split": True, "reader_file_split_target": 1000})
            return {p.name: p.read_text(encoding="utf-8") for p in sorted(d.glob("*"))}

        assert run("a") == run("b"), "apply_file_split is not deterministic"

    def test_no_op_when_flag_off(self, tmp_path):
        from scripts import build_edition as be

        tmp = tmp_path / "build"
        tmp.mkdir()
        (tmp / "index_split_007.html").write_text(SYNTH, encoding="utf-8")
        before = SYNTH
        stats = be.apply_file_split(tmp, {"id": "x", "reader_file_split": False})  # explicit opt-out
        assert stats["files_split"] == 0
        assert (tmp / "index_split_007.html").read_text(encoding="utf-8") == before


_MIN_OPF = """<?xml version="1.0"  encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uuid_id">
  <metadata/>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="titlepage" href="titlepage.xhtml" media-type="application/xhtml+xml"/>
    <item id="id154" href="index_split_007.html" media-type="application/xhtml+xml"/>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="css" href="stylesheet.css" media-type="text/css"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="titlepage"/>
    <itemref idref="id154"/>
  </spine>
</package>
"""

_MIN_NAV = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Navigation</title></head>
<body>
  <nav epub:type="toc" id="toc">
    <h2>Contents</h2>
    <ol>
      <li><a href="index_split_007.html#bp-00">The First Book of Moses, Genesis</a></li>
    </ol>
  </nav>
</body>
</html>
"""

_MIN_NCX = """<?xml version='1.0' encoding='utf-8'?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="en">
  <head/>
  <docTitle><text>The Ethiopian Bible</text></docTitle>
  <navMap>
    <navPoint id="num_book_0" playOrder="1">
      <navLabel><text>The First Book of Moses, Genesis</text></navLabel>
      <content src="index_split_007.html#bp-00"/>
    </navPoint>
  </navMap>
</ncx>
"""

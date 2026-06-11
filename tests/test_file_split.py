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


# SYNTH minus the book-title-page — a mid-book continuation file (the calibre base cuts
# books across files), used to pin that a file WITHOUT a bp- boundary keeps zero churn.
CH_ONLY = SYNTH.replace(
    '<div class="book-title-page" id="bp-00" data-book-idx="0" epub:type="bodymatter"><h1>Genesis</h1></div>\n',
    "",
)


class TestSplitHtmlDocumentUnit:
    """``split_html_document(text, stem, target)`` cuts one file into well-formed
    pieces at top-level book/chapter boundaries, never mid-chapter, and gives each
    piece a notes-section holding exactly the asides its chapters reference. A
    book-title-page is ALWAYS isolated into its own piece (K-R2-1: a fresh spine file
    is the only page-break Kobo's kepub renderer honors at #book-inner nesting)."""

    def _split(self, target, text=SYNTH):
        from scripts.build_edition import split_html_document

        return split_html_document(text, "index_split_007", target)

    def test_no_split_when_under_target_and_no_book_boundary(self):
        pieces = self._split(10_000_000, text=CH_ONLY)
        assert len(pieces) == 1
        name, text = pieces[0]
        assert name == "index_split_007.html", "an unsplit file must keep its original name"
        assert text == CH_ONLY, "an unsplit file must be byte-identical (zero churn)"

    def test_strip_notes_sections_removes_empty_verse_refs_husk(self):
        # round-7 5.4: the base also wraps vnote asides in `<section
        # class="verse-refs-section">` containers (58 in the live base, e.g.
        # index_split_035) — harvesting the asides used to leave an empty
        # multi-newline <section> husk in every edition. Real-base shape:
        # whitespace (≈52 newlines in the live husk) between open and close.
        from scripts.build_edition import _strip_notes_sections

        body = (
            '<p class="verse-p"><a class="vn-link" id="v-psa-119-89" href="#vnote-psa-119-89" '
            'epub:type="noteref">89</a> For ever, O LORD, thy word is settled in heaven.</p>\n'
            '<section class="verse-refs-section" epub:type="footnotes" hidden="">'
            '<aside class="vnote" id="vnote-psa-119-89" epub:type="footnote"><p>x</p></aside>\n\n\n'
            "</section>\n"
        )
        prose, asides = _strip_notes_sections(body)
        assert [a_id for a_id, _ in asides] == ["vnote-psa-119-89"], "the vnote aside is harvested"
        assert "verse-refs-section" not in prose, f"empty husk must be cleaned: {prose!r}"
        assert "thy word is settled" in prose, "prose is preserved"

    def test_book_title_page_is_isolated_even_under_target(self):
        # A file containing a book-title-page splits even when under target: the title
        # must lead (and own) a fresh spine file so it starts a fresh page everywhere.
        pieces = self._split(10_000_000)
        assert len(pieces) == 2, f"expected [title][rest], got {len(pieces)}"
        d = dict(pieces)
        p0, p1 = d["index_split_007_00.html"], d["index_split_007_01.html"]
        assert 'id="bp-00"' in p0 and 'id="ch-b00-c1"' not in p0, "title piece holds ONLY the title page"
        assert '<aside class="notes-section"' not in p0, "title piece carries no notes"
        assert 'id="ch-b00-c1"' in p1, "chapter 1 leads the next piece"

    def test_splits_into_title_and_chapter_pieces(self):
        # target chosen so ch1 packs into one piece and ch2 into the next; the title
        # page is always its own piece in front.
        pieces = self._split(1000)
        assert len(pieces) == 3, f"expected 3 pieces, got {len(pieces)}"
        names = [n for n, _ in pieces]
        assert names == ["index_split_007_00.html", "index_split_007_01.html", "index_split_007_02.html"]

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

    def test_title_leads_alone_and_chapters_align_to_pieces(self):
        d = dict(self._split(1000))
        p0, p1, p2 = (d[f"index_split_007_0{k}.html"] for k in range(3))
        assert 'id="bp-00"' in p0 and 'id="ch-b00-c1"' not in p0, "title piece = title only"
        assert 'id="ch-b00-c1"' in p1, "chapter 1 leads piece 1"
        # the pop rule: a piece never ENDS with a bare next-chapter opener — ch2's
        # anchor + heading lead piece 2 with ch2's verses instead of stranding at the
        # bottom of piece 1 (the K-R2-4 orphaned-numeral seam).
        assert 'id="ch-b00-c2"' not in p1 and 'id="page_2"' not in p1
        assert 'id="ch-b00-c2"' in p2 and 'id="v-gen-2-1"' in p2

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
        p1, p2 = d["index_split_007_01.html"], d["index_split_007_02.html"]
        # ch1's asides (the verse popup + the editorial note it references) live with ch1
        assert 'id="vnote-gen-1-1"' in p1 and 'id="note-x1"' in p1
        assert 'id="vnote-gen-1-1"' not in p2 and 'id="note-x1"' not in p2
        # ch2's asides live with ch2
        assert 'id="vnote-gen-2-1"' in p2 and 'id="note-x2"' in p2
        assert 'id="vnote-gen-2-1"' not in p1 and 'id="note-x2"' not in p1
        # each chapter piece keeps a notes-section wrapper around its asides
        assert '<aside class="notes-section"' in p1 and '<aside class="notes-section"' in p2

    def test_same_file_footnote_links_stay_resolvable_in_piece(self):
        # the marker→aside and aside→marker bare links must both be intra-piece
        d = dict(self._split(1000))
        for text in d.values():
            for frag in re.findall(r'href="#(note-[^"]+|ref-[^"]+|vnote-[^"]+)"', text):
                assert f'id="{frag}"' in text, f"bare #{frag} unresolved within its piece"


# A mid-file book boundary — the calibre base cuts arbitrarily, so a file can carry the
# TAIL of one book followed by the next book's title page (the K-R2-1 kobo22 shape: the
# in-content ToC tail + Genesis title + ch1 shared one piece and one Kobo page).
MIDFILE_BOOK = (
    "<?xml version='1.0' encoding='utf-8'?>\n"
    '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">\n'
    '<head><title>T</title><link rel="stylesheet" type="text/css" href="stylesheet.css"/></head>\n'
    '<body class="bible-body">\n'
    '<p id="page_60" class="ch-heading"><span class="bold-num">50</span></p>\n'
    '<p class="verse-p"><a class="vn-link" id="v-gen-50-1" href="#vnote-gen-50-1" epub:type="noteref">'
    '<span class="vn">1</span></a> previous book tail.</p>\n'
    '<div class="book-title-page" id="bp-01" data-book-idx="1" epub:type="bodymatter"><h1>Exodus</h1></div>\n'
    '<p id="page_61" class="ch-heading"><span class="bold-num">1</span></p>\n'
    '<p class="verse-p"><a class="vn-link" id="v-exo-1-1" href="#vnote-exo-1-1" epub:type="noteref">'
    '<span class="vn">1</span></a> next book begins.</p>\n'
    '<aside class="notes-section" epub:type="footnotes" hidden="">\n'
    '<aside class="note note-word" id="vnote-gen-50-1" epub:type="footnote"><p>tail popup</p></aside>\n'
    '<aside class="note note-word" id="vnote-exo-1-1" epub:type="footnote"><p>exo popup</p></aside>\n'
    "</aside>\n"
    "</body></html>"
)

# The REAL base's chapter form: headings carry page_N ids (NOT ch-bNN-cMM — that form
# exists only where a <a class="ch-anchor"> was emitted), so the splitter must treat the
# ch-heading CLASS as a cut candidate or a sparsely-noted book packs into one giant
# over-cap atom (the 700-880 KB pieces found in the K-R2 kepub inspection).
PAGEID_BOOK = (
    "<?xml version='1.0' encoding='utf-8'?>\n"
    '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">\n'
    '<head><title>T</title><link rel="stylesheet" type="text/css" href="stylesheet.css"/></head>\n'
    '<body class="bible-body">\n'
    + "".join(
        f'<p id="page_{n}" class="ch-heading"><span class="bold-num">{n}</span></p>\n'
        f'<p class="verse-p">{"prose " * 120}</p>\n'
        for n in range(1, 7)
    )
    + "</body></html>"
)


class TestBookBoundaryIsolation:
    """K-R2-1: every book-title page owns a fresh spine file (forced split, even in an
    under-target file), and the real base's page_N-id chapter headings are cut
    candidates so pieces stay near target."""

    def test_under_target_midfile_book_boundary_splits_three_ways(self):
        from scripts.build_edition import split_html_document

        pieces = split_html_document(MIDFILE_BOOK, "index_split_003", 10_000_000)
        assert len(pieces) == 3, f"expected [prev tail][title][next book], got {len(pieces)}"
        d = dict(pieces)
        tail = d["index_split_003_00.html"]
        title = d["index_split_003_01.html"]
        rest = d["index_split_003_02.html"]
        assert 'id="v-gen-50-1"' in tail and 'id="bp-01"' not in tail
        assert 'id="bp-01"' in title and 'id="page_61"' not in title and 'class="verse-p"' not in title
        assert 'id="page_61"' in rest and 'id="v-exo-1-1"' in rest
        # asides follow their referencing pieces; the title piece carries none
        assert 'id="vnote-gen-50-1"' in tail and 'id="vnote-exo-1-1"' in rest
        assert "notes-section" not in title

    def test_page_id_headings_are_cut_candidates(self):
        from scripts.build_edition import split_html_document

        # each chapter ≈ 800 B; target 2000 forces cuts that are only available via the
        # ch-heading class (no bp-/ch-bNN-cMM/vn-link ids exist in this fixture)
        pieces = split_html_document(PAGEID_BOOK, "index_split_011", 2000)
        assert len(pieces) > 1, "page_N-id headings must provide cut candidates"
        for name, t in pieces:
            assert len(re.findall(r"<p\b", t)) == t.count("</p>"), f"{name}: unbalanced <p>"
        # no piece ends with a stranded chapter numeral: every heading in a piece is
        # followed by its verse prose within that same piece
        for name, t in pieces:
            last_head = t.rfind('class="ch-heading"')
            if last_head != -1:
                assert 'class="verse-p"' in t[last_head:], f"{name}: trailing orphan ch-heading"
        joined = "".join(t for _, t in pieces)
        for n in range(1, 7):
            assert joined.count(f'id="page_{n}"') == 1


# The K-KIN husk class (Kindle round 6, 2026-06-11): apply_appendix_demotion_and_renumber
# flips a demoted addition's title div to class="appendix-section" (keeping its bp-NN id
# so ToC/nav/ncx anchors resolve), but the splitter's forced K-R2-1 title isolation keyed
# on the bp ID alone — so the ~750 B CSS-hidden frame became its OWN spine piece (an empty
# husk) and every nav/ncx/in-book-ToC link targeting #bp-NN pointed at it. Kindle's KFX
# preprocessor refuses an effectively-empty piece as a TOC link target: E24010 "Hyperlink
# not resolved in toc" ×3 (bp-45/46/47 Azariah/Susanna/Bel) → E24001 "TOC could not be
# built" → Send-to-Kindle rejects the whole book. Forced isolation is for REAL
# book-title-page divs only; a demoted frame must flow with its parent book's content so
# its anchor always lands in a content-bearing piece. (Proven by the rung-tochusk probe:
# removing the husks eliminated E24010/E24001 on the local Previewer oracle, ×2 runs.)
DEMOTED_MIDFILE = MIDFILE_BOOK.replace(
    '<div class="book-title-page" id="bp-01"', '<div class="appendix-section" id="bp-01"'
)


class TestDemotedAppendixHuskFix:
    """A demoted appendix-section frame (bp id kept) is NOT force-isolated into its own
    spine piece — a frame-only piece is the Kindle-refused E24010/E24001 husk."""

    def test_demoted_frame_under_target_returns_file_unchanged(self):
        from scripts.build_edition import split_html_document

        pieces = split_html_document(DEMOTED_MIDFILE, "index_split_003", 10_000_000)
        assert len(pieces) == 1, f"a demoted frame must not force a split, got {len(pieces)} pieces"
        name, text = pieces[0]
        assert name == "index_split_003.html"
        assert text == DEMOTED_MIDFILE, "an unsplit file must be byte-identical (zero churn)"

    def test_demoted_frame_flows_with_content_when_size_splits(self):
        from scripts.build_edition import split_html_document

        # A size-driven split: the piece holding the demoted bp anchor must also hold
        # real content — a frame-only piece is the husk the KFX preprocessor refuses.
        pieces = split_html_document(DEMOTED_MIDFILE, "index_split_003", 600)
        holders = [t for _, t in pieces if 'id="bp-01"' in t]
        assert len(holders) == 1, "the demoted bp anchor lives in exactly one piece"
        assert 'class="verse-p"' in holders[0] or 'class="ch-heading"' in holders[0], (
            "the demoted frame's piece must carry content (husk = E24010/E24001)"
        )

    def test_real_title_page_still_isolated_alongside_demoted(self):
        from scripts.build_edition import split_html_document

        # A file holding BOTH a real title page and a demoted frame: K-R2-1 still
        # isolates the real title; the demoted frame still flows with content.
        both = MIDFILE_BOOK.replace(
            '<p id="page_61" class="ch-heading">',
            '<div class="appendix-section" id="bp-45"><h1>The Prayer of Azariah</h1></div>\n'
            '<p id="page_61" class="ch-heading">',
        )
        pieces = split_html_document(both, "index_split_004", 10_000_000)
        assert len(pieces) == 3, f"[tail][title][demoted+rest], got {[n for n, _ in pieces]}"
        d = dict(pieces)
        title = d["index_split_004_01.html"]
        rest = d["index_split_004_02.html"]
        assert 'id="bp-01"' in title and 'id="bp-45"' not in title, "real title stays a singleton"
        assert 'id="bp-45"' in rest and 'id="page_61"' in rest, "demoted frame flows with content"


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


# A calibre FILE boundary that strands a chapter opener: file 007 ENDS with the
# next chapter's anchor + heading (the real base does this at Gen 27 / 1Ch 3 /
# Ps 73 / Isa 33 / Jer 25 — the K-R2-4 "chapter 3 gap" class at FILE level),
# while file 008 carries that chapter's verses.
FILE_A_TAIL_OPENER = (
    "<?xml version='1.0' encoding='utf-8'?>\n"
    '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">\n'
    '<head><title>T</title><link rel="stylesheet" type="text/css" href="stylesheet.css"/></head>\n'
    '<body class="bible-body">\n'
    '<p id="page_9" class="ch-heading"><span class="bold-num">26</span></p>\n'
    '<p class="verse-p"><a class="vn-link" id="v-gen-26-1" href="#vnote-gen-26-1" epub:type="noteref">'
    '<span class="vn">1</span></a> chapter twenty-six text.</p>\n'
    '<a id="ch-b00-c27" class="ch-anchor"></a>'
    '<p id="page_10" class="ch-heading"><span class="bold-num">27</span></p>\n'
    '<aside class="notes-section" epub:type="footnotes" hidden="">\n'
    '<aside class="note note-word" id="vnote-gen-26-1" epub:type="footnote"><p>x</p></aside>\n'
    "</aside>\n"
    "</body></html>"
)
FILE_B_NEXT = (
    "<?xml version='1.0' encoding='utf-8'?>\n"
    '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">\n'
    '<head><title>T</title><link rel="stylesheet" type="text/css" href="stylesheet.css"/></head>\n'
    '<body class="bible-body">\n'
    '<p class="verse-p"><a class="vn-link" id="v-gen-27-1" href="#vnote-gen-27-1" epub:type="noteref">'
    '<span class="vn">1</span></a> chapter twenty-seven text.</p>\n'
    '<aside class="notes-section" epub:type="footnotes" hidden="">\n'
    '<aside class="note note-word" id="vnote-gen-27-1" epub:type="footnote"><p>y</p></aside>\n'
    "</aside>\n"
    "</body></html>"
)


class TestTitleAtomDivClose:
    """C1 + C16 (Mac splitter review 2026-06-10), pinned on the REAL base — the
    synthetic masked both. C1: a book's intro blurb (a <p> between the
    book-title-page div and the first chapter — Jubilees, Additions-to-Esther)
    must travel WHOLE to the piece after the title singleton, never torn
    mid-sentence onto the title page (shipped torn in r3: piece 018_02 ended
    "…the Book of Jubilees?), </p>"). C16: reopen prefixes replay open tags
    WITHOUT their ids, so no id appears in two pieces (idmap poisoning)."""

    def _split_real(self, fname):
        from scripts.build_edition import FILE_SPLIT_TARGET_DEFAULT, split_html_document

        text = (REPO / "epub_working" / fname).read_text(encoding="utf-8")
        return split_html_document(text, fname[: -len(".html")], FILE_SPLIT_TARGET_DEFAULT)

    def test_jubilees_intro_blurb_not_torn_onto_title_page(self):
        pieces = self._split_real("index_split_018.html")
        title_piece = next(t for _n, t in pieces if 'id="bp-15"' in t)
        # the title piece ends at the title div's close — no blurb fragment on it
        assert "Moses receives the tables" not in title_piece, "Jubilees blurb torn onto the title page (C1)"
        assert 'id="page_639"' not in title_piece
        # the blurb paragraph survives INTACT in exactly one piece: its opening
        # text and its tail anchor (the old tear point) sit in the SAME piece.
        holders = [t for _n, t in pieces if "Moses receives the tables" in t]
        assert len(holders) == 1
        assert 'id="v-man-1-29"' in holders[0], "blurb torn mid-paragraph across pieces (C1)"

    def test_addesther_intro_blurb_not_torn_onto_title_page(self):
        pieces = self._split_real("index_split_028.html")
        title_piece = next((t for _n, t in pieces if 'id="bp-25"' in t), None)
        assert title_piece is not None, "bp-25 title piece missing from index_split_028"
        assert 'class="verse-p"' not in title_piece.split('<aside class="notes-section"')[0], (
            "content paragraph torn onto the Additions-to-Esther title page (C1)"
        )

    def test_no_id_duplicated_across_pieces_real_base(self):
        # C16: with reopen-id stripping, every id is unique across a file's pieces.
        for fname in ("index_split_018.html", "index_split_028.html", "index_split_000.html"):
            seen: dict[str, str] = {}
            for n, t in self._split_real(fname):
                for m in re.finditer(r'\sid="([^"]+)"', t):
                    assert seen.setdefault(m.group(1), n) == n, (
                        f"id {m.group(1)!r} appears in both {seen[m.group(1)]} and {n} (C16)"
                    )


class TestCrossFileOpenerPop:
    """A chapter opener stranded at the END of an original calibre file moves to
    the head of the NEXT file's first piece, so the numeral renders with its
    chapter instead of alone at the bottom of the previous page."""

    def _run(self, tmp_path):
        from scripts import build_edition as be

        tmp = tmp_path / "build"
        tmp.mkdir()
        (tmp / "index_split_007.html").write_text(FILE_A_TAIL_OPENER, encoding="utf-8")
        (tmp / "index_split_008.html").write_text(FILE_B_NEXT, encoding="utf-8")
        opf = _MIN_OPF.replace(
            '<item id="id154" href="index_split_007.html" media-type="application/xhtml+xml"/>',
            '<item id="id154" href="index_split_007.html" media-type="application/xhtml+xml"/>\n'
            '    <item id="id155" href="index_split_008.html" media-type="application/xhtml+xml"/>',
        ).replace(
            '<itemref idref="id154"/>',
            '<itemref idref="id154"/>\n    <itemref idref="id155"/>',
        )
        (tmp / "content.opf").write_text(opf, encoding="utf-8")
        (tmp / "nav.xhtml").write_text(_MIN_NAV, encoding="utf-8")
        (tmp / "toc.ncx").write_text(_MIN_NCX, encoding="utf-8")
        be.apply_file_split(tmp, {"id": "x", "reader_file_split": True, "reader_file_split_target": 400})
        return tmp

    def test_opener_moves_to_the_next_files_first_piece(self, tmp_path):
        tmp = self._run(tmp_path)
        texts = {p.name: p.read_text(encoding="utf-8") for p in sorted(tmp.glob("index_split_*.html"))}
        holder = [n for n, t in texts.items() if 'id="ch-b00-c27"' in t]
        assert len(holder) == 1, f"opener must live in exactly one piece, got {holder}"
        assert holder[0].startswith("index_split_008"), f"opener must move to file 008, got {holder[0]}"
        t = texts[holder[0]]
        body = t[t.find("<body") :]
        assert body.find('id="ch-b00-c27"') < body.find('id="v-gen-27-1"'), "opener leads its chapter"
        # the donor file's pieces no longer end with a stranded opener (checked
        # with the production pattern itself — same boundary semantics)
        from scripts.build_edition import _TRAILING_OPENER_RE

        for n, t in texts.items():
            if n.startswith("index_split_007"):
                pre_notes = t.split('<aside class="notes-section"')[0]
                m = _TRAILING_OPENER_RE.search(pre_notes)
                # the pattern may lazily span [heading + verse text] — the SAME
                # guards production uses (vn-link content / size) mark that as
                # NOT a bare opener; only a bare-opener match means stranded.
                bare = m is not None and 'class="vn-link' not in m.group(0) and len(m.group(0)) <= 900
                assert not bare, f"{n} still ends with a stranded opener"

    def test_trailing_opener_regex_matches_only_the_last_heading(self):
        # the tempered dot keeps the match anchored to the LAST heading; a plain
        # lazy .*? matched from the FIRST heading across the whole piece (200KB+
        # on real data), defeating the size guard so the pop never fired.
        from scripts.build_edition import _TRAILING_OPENER_RE

        seg = (
            '<p id="page_1" class="ch-heading"><span class="bold-num">1</span></p>'
            '<p class="verse-p">' + "x" * 5000 + "</p>"
            '<a id="ch-b00-c2" class="ch-anchor"></a>'
            '<p id="page_2" class="ch-heading"><span class="bold-num">2</span></p>  '
        )
        m = _TRAILING_OPENER_RE.search(seg)
        assert m, "the trailing bare opener must match"
        assert len(m.group(0)) < 900, f"match spans {len(m.group(0))} chars — not tail-anchored"
        assert "page_2" in m.group(0) and "verse-p" not in m.group(0)

    def test_links_to_the_moved_opener_resolve(self, tmp_path):
        tmp = self._run(tmp_path)
        # nav/ncx (or any cross-file href) pointing at the moved ids must target
        # the piece that now holds them
        texts = {p.name: p.read_text(encoding="utf-8") for p in sorted(tmp.glob("index_split_*.html"))}
        holder = next(n for n, t in texts.items() if 'id="page_10"' in t)
        for fp in sorted(tmp.iterdir()):
            if fp.suffix not in (".html", ".xhtml", ".ncx"):
                continue
            for m in re.finditer(r'(?:href|src)="([^"#]+)#page_10"', fp.read_text(encoding="utf-8")):
                assert m.group(1) == holder, f"{fp.name} points #page_10 at {m.group(1)}, holder is {holder}"


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
        assert stats["pieces_created"] == 3

        p1 = (tmp / "index_split_007_01.html").read_text(encoding="utf-8")
        # ch1's #v-gen-2-1 (target now in piece 02) was promoted to a cross-file link
        assert 'href="index_split_007_02.html#v-gen-2-1"' in p1
        assert 'href="#v-gen-2-1"' not in p1
        # ch1's own footnote bare links stay bare (same piece)
        assert 'href="#note-x1"' in p1
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
        # old single item/itemref gone; three piece items + itemrefs present, in order
        assert 'href="index_split_007.html"' not in opf
        assert 'href="index_split_007_00.html"' in opf and 'href="index_split_007_02.html"' in opf
        i0 = opf.index("index_split_007_00.html")
        i2 = opf.index("index_split_007_02.html")
        assert i0 < i2, "piece spine/manifest order must follow piece order"
        # spine itemref count for the pieces == 3
        ids = re.findall(r'<item id="([^"]+)" href="index_split_007_0\d\.html"', opf)
        assert len(ids) == 3
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


_TOC_PAGE = (
    "<?xml version='1.0' encoding='utf-8'?>\n"
    '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>T</title></head><body>\n'
    '<div class="toc-wrap"><h1 class="toc-title">Contents</h1><ol class="toc-books">\n'
    '<li class="toc-book"><details><summary><a href="index_split_000.html#bp-00">Genesis</a></summary>'
    '<ol class="toc-chapters"><li><a href="index_split_000.html#page_4">1</a></li>'
    '<li><a href="index_split_001.html#page_9">2</a></li></ol></details></li>\n'
    '<li class="toc-book"><details><summary><a href="index_split_003.html#bp-01">Exodus</a></summary>'
    '<ol class="toc-chapters"><li><a href="index_split_003.html#page_70">1</a></li></ol></details></li>\n'
    "</ol></div>\n</body></html>"
)


class TestInContentTocModes:
    """The in-content ToC's two modes (beta-3 (b), user-decided; re-trued 2026-06-09):
    the shipped default (``reader_toc_books_only: true`` on every edition) UNWRAPS the
    base's ``<details>`` into a flat label + ALWAYS-VISIBLE chapter pills (no reader can
    strand the pills behind an unsupported disclosure widget); the opt-in expandable
    mode (``reader_toc_collapsible: true``) KEEPS the base's ``<details>`` so capable
    readers (Apple Books) can collapse/expand, while e-ink readers that ignore
    ``<details>`` still render the pills."""

    def test_books_only_flattens_but_keeps_chapter_pills(self, tmp_path):
        from scripts.build_edition import apply_reader_toc_transforms

        (tmp_path / "index_split_000.html").write_text(_TOC_PAGE, encoding="utf-8")
        s = apply_reader_toc_transforms(tmp_path, {"reader_toc_books_only": True})
        assert s["books_transformed"] == 2
        out = (tmp_path / "index_split_000.html").read_text(encoding="utf-8")
        assert out.count('class="toc-book-label"') == 2, "both book labels kept"
        assert "#bp-00" in out and "#bp-01" in out, "book anchors preserved"
        assert "<details" not in out, "flat mode strips the <details> wrapper"
        assert out.count('class="toc-chapters"') == 2, "chapter pills are KEPT (beta-3 (b))"
        assert "#page_4" in out and "#page_70" in out, "chapter links preserved"

    def test_collapsible_optin_keeps_details_expandable(self, tmp_path):
        from scripts.build_edition import apply_reader_toc_transforms

        (tmp_path / "index_split_000.html").write_text(_TOC_PAGE, encoding="utf-8")
        apply_reader_toc_transforms(tmp_path, {"reader_toc_collapsible": True})
        out = (tmp_path / "index_split_000.html").read_text(encoding="utf-8")
        assert out.count("<details") == 2, "expandable mode keeps the base <details>"
        assert out.count('class="toc-chapters"') == 2, "pills stay inside the disclosure"

    def test_collapsible_default_open_adds_open_attribute(self, tmp_path):
        from scripts.build_edition import apply_reader_toc_transforms

        (tmp_path / "index_split_000.html").write_text(_TOC_PAGE, encoding="utf-8")
        s = apply_reader_toc_transforms(tmp_path, {"reader_toc_collapsible": True, "reader_toc_default_open": True})
        assert s["defaults_opened"] == 2
        out = (tmp_path / "index_split_000.html").read_text(encoding="utf-8")
        assert out.count('<details open="">') == 2, 'default-open emits open="" on each book'


class TestNativeTocChapterEnrichment:
    """enrich_nav_chapters adds per-chapter entries under each book in nav.xhtml +
    toc.ncx so one-tap chapter jump survives in the reader's native ToC."""

    NAV = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">\n'
        "<head><title>Navigation</title></head><body>\n"
        '<nav epub:type="toc" id="toc"><h2>Contents</h2><ol>\n'
        '<li><a href="index_split_000.html#bp-00">Genesis</a></li>\n'
        '<li><a href="index_split_003.html#bp-01">Exodus</a></li>\n'
        "</ol></nav></body></html>\n"
    )
    NCX = (
        "<?xml version='1.0' encoding='utf-8'?>\n"
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head/>'
        "<docTitle><text>T</text></docTitle><navMap>\n"
        '<navPoint id="num_book_0" playOrder="1"><navLabel><text>Genesis</text></navLabel>'
        '<content src="index_split_000.html#bp-00"/></navPoint>\n'
        '<navPoint id="num_book_1" playOrder="2"><navLabel><text>Exodus</text></navLabel>'
        '<content src="index_split_003.html#bp-01"/></navPoint>\n'
        "</navMap></ncx>\n"
    )
    CONTENT = (
        '<html><body class="bible-body">'
        '<a id="ch-b00-c1" class="ch-anchor"></a>g1'
        '<a id="ch-b00-c2" class="ch-anchor"></a>g2'
        '<a id="ch-b01-c1" class="ch-anchor"></a>e1'
        "</body></html>"
    )

    def _setup(self, tmp_path):
        (tmp_path / "nav.xhtml").write_text(self.NAV, encoding="utf-8")
        (tmp_path / "toc.ncx").write_text(self.NCX, encoding="utf-8")
        (tmp_path / "index_split_000.html").write_text(self.CONTENT, encoding="utf-8")

    def test_nav_and_ncx_get_chapter_entries(self, tmp_path):
        from scripts.build_edition import enrich_nav_chapters

        self._setup(tmp_path)
        s = enrich_nav_chapters(tmp_path)
        assert s["nav_chapters_added"] == 3 and s["ncx_chapters_added"] == 3
        nav = (tmp_path / "nav.xhtml").read_text(encoding="utf-8")
        # Genesis (bp-00) gets its 2 chapters nested; Exodus (bp-01) gets 1
        assert '<ol class="toc-nav-chapters">' in nav
        assert 'href="index_split_000.html#ch-b00-c1"' in nav
        assert 'href="index_split_000.html#ch-b00-c2"' in nav
        assert 'href="index_split_000.html#ch-b01-c1"' in nav
        ncx = (tmp_path / "toc.ncx").read_text(encoding="utf-8")
        assert 'id="num-ch-b00-c1"' in ncx and 'src="index_split_000.html#ch-b00-c1"' in ncx
        # playOrder is gapless 1..5 (2 books + 3 chapters), depth-first
        orders = [int(x) for x in re.findall(r'playOrder="(\d+)"', ncx)]
        assert orders == list(range(1, len(orders) + 1)), f"playOrder not gapless: {orders}"

    def test_no_op_without_chapter_anchors(self, tmp_path):
        from scripts.build_edition import enrich_nav_chapters

        (tmp_path / "nav.xhtml").write_text(self.NAV, encoding="utf-8")
        (tmp_path / "toc.ncx").write_text(self.NCX, encoding="utf-8")
        (tmp_path / "index_split_000.html").write_text("<html><body>no anchors</body></html>", encoding="utf-8")
        s = enrich_nav_chapters(tmp_path)
        assert s["nav_chapters_added"] == 0 and s["ncx_chapters_added"] == 0
        assert (tmp_path / "nav.xhtml").read_text(encoding="utf-8") == self.NAV

    def test_enrich_is_the_last_nav_pass_in_build_one(self):
        """Regression: enrich_nav_chapters MUST run after every front/back-matter +
        reading-plan nav injector and before the splitter. Those injectors insert <li>s
        into the flat book <ol> at the first </ol>; once enrich nests a chapter <ol>
        inside each book <li>, the first </ol> belongs to a book's chapters, so an
        injector running afterwards lands its entry inside that book's chapter list →
        an out-of-spine-order nav (epubcheck NAV-011). It must precede apply_file_split,
        which remaps the chapter hrefs from index_split files to the final pieces."""
        src = Path(__file__).resolve().parents[1].joinpath("scripts", "build_edition.py").read_text(encoding="utf-8")
        body = src[src.index("def build_one(") :]
        pos_enrich = body.index("enrich_nav_chapters(tmp)")
        assert body.index("inject_back_matter(") < pos_enrich, "enrich must run AFTER inject_back_matter"
        assert body.index("inject_reading_plans_page(") < pos_enrich, "enrich must run AFTER reading-plans"
        assert pos_enrich < body.index("apply_file_split(tmp"), "enrich must run BEFORE apply_file_split"


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


class TestSpillDuplicateNoterefClone:
    """Round-6 gate catch (K-R4-2 fallout): a spill-duplicate verse anchor
    (v-…-x2) can land in a DIFFERENT piece than its aside (which lives with
    its FIRST referencer) — the link-rewrite pass would then promote that
    noteref to a cross-file link, which NAVIGATES instead of popping on Kobo
    (the gate-2 K-R3-4 class; 1en 106:1 in the round-6 build). The splitter
    must instead CLONE the aside into the referencing piece under a derived
    unique id and retarget the local noteref href."""

    DOC = """<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
<head><title>x</title></head>
<body class="bible-body">
<div class="book-title-page" id="bp-21" data-book-idx="21" epub:type="bodymatter"><h1>1 Enoch</h1></div>
<p id="ch-b21-c105" class="ch-heading"><span class="bold-num">105</span></p>
<p class="verse-p"><a class="vn-link" id="v-1en-105-1" href="#vnote-1en-105-1" epub:type="noteref"><span class="vn">1</span></a> FILLER</p>
<a id="ch-b21-c106" class="ch-anchor"></a><p id="page_106" class="ch-heading"><span class="bold-num">106</span></p>
<p class="verse-p"><a class="vn-link" id="v-1en-106-1" href="#vnote-1en-106-1" epub:type="noteref"><span class="vn">1</span></a> And after some days my son Methuselah took a wife.</p>
<a id="ch-b21-c107" class="ch-anchor"></a><p id="page_107" class="ch-heading"><span class="bold-num">107</span></p>
<p class="verse-p"><a class="vn-link" id="v-1en-106-1-x2" href="#vnote-1en-106-1" epub:type="noteref"><span class="vn">1</span></a> SPILL REGION</p>
<aside class="notes-section" epub:type="footnotes" hidden="">
<aside class="vnote" id="vnote-1en-105-1" epub:type="footnote"><p>popup 105</p></aside>
<aside class="vnote" id="vnote-1en-106-1" epub:type="footnote"><p>popup 106 <a href="#v-1en-106-1" class="vnote-back">↩</a></p></aside>
</aside>
</body></html>"""

    def test_every_noteref_resolves_same_piece(self):
        from scripts.build_edition import split_html_document

        # pad chapters so each lands in its own piece under a small target
        doc = self.DOC.replace("FILLER", "filler word " * 60).replace("SPILL REGION", "spill region prose " * 60)
        pieces = split_html_document(doc, "index_split_022", 900)
        assert len(pieces) >= 3, [n for n, _ in pieces]
        seen_ids: dict[str, str] = {}
        for name, text in pieces:
            ids = set(re.findall(r'\sid="([^"]+)"', text))
            for i in ids:
                assert i not in seen_ids or seen_ids[i] == name, f"id {i} duplicated across pieces"
                seen_ids.setdefault(i, name)
            for tag in re.findall(r'<a\b[^>]*epub:type="noteref"[^>]*>', text):
                href = re.search(r'href="([^"]*)"', tag)
                assert href is not None
                target = href.group(1)
                if target.startswith("#"):
                    assert target[1:] in ids, (
                        f"{name}: noteref {target} does not resolve in its own piece "
                        "(would be PROMOTED cross-file → Kobo navigates instead of popping)"
                    )


class TestKindleSplitTarget:
    """K-KIN blocker #2 (P/P halfspine verdict): the whole 297-doc artifact fails
    KFX conversion with a generic internal error while EACH HALF (~149 docs)
    converts clean — and the full-size delink probe (links/asides gutted) still
    failed, so the driver is aggregate doc-count/per-doc overhead, NOT the link
    graph. The ~0.4 MB e-ink split exists for Kobo's renderer; Kindle paginates
    internally, so the kindle target packs to a larger per-piece cap (fewer
    docs, same bytes). One resolver, explicit override wins."""

    def test_default_target_unchanged(self):
        from scripts.build_edition import FILE_SPLIT_TARGET_DEFAULT, resolve_file_split_target

        assert resolve_file_split_target({}) == FILE_SPLIT_TARGET_DEFAULT
        assert resolve_file_split_target({"target_reader": "eink"}) == FILE_SPLIT_TARGET_DEFAULT

    def test_kindle_target_packs_larger(self):
        from scripts.build_edition import (
            FILE_SPLIT_TARGET_DEFAULT,
            FILE_SPLIT_TARGET_KINDLE,
            resolve_file_split_target,
        )

        assert resolve_file_split_target({"target_reader": "kindle"}) == FILE_SPLIT_TARGET_KINDLE
        assert FILE_SPLIT_TARGET_KINDLE > FILE_SPLIT_TARGET_DEFAULT

    def test_explicit_override_wins_everywhere(self):
        from scripts.build_edition import resolve_file_split_target

        assert resolve_file_split_target({"reader_file_split_target": 123_456}) == 123_456
        assert resolve_file_split_target({"reader_file_split_target": 123_456, "target_reader": "kindle"}) == 123_456

    def test_apply_file_split_consumes_the_resolver(self, tmp_path):
        # A ~25 KB no-title file splits under a tiny default-target edition but
        # stays whole under the kindle target (25 KB << the kindle cap).
        from scripts.build_edition import apply_file_split

        # filler in BOTH chapters' verses: the body must be decisively over the
        # 10 KB default-leg target WITH a cut candidate between heavy atoms —
        # atom weights exclude head/tail, so a marginal fixture packs into one
        # group and never splits.
        big = CH_ONLY.replace('<p class="verse-p">', '<p class="verse-p">' + "filler " * 1200)
        for target_reader, expect_split in (("", True), ("kindle", False)):
            tmp = tmp_path / (target_reader or "default")
            tmp.mkdir()
            (tmp / "index_split_007.html").write_text(big, encoding="utf-8")
            ed = {"id": "x", "reader_file_split": True, "reader_file_split_target": 10_000}
            if target_reader:
                ed = {"id": "x", "reader_file_split": True, "target_reader": target_reader}
            stats = apply_file_split(tmp, ed)
            assert (stats["files_split"] > 0) == expect_split, (target_reader, stats)

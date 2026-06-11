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

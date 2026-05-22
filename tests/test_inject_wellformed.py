"""Regression: inject must never splice a new aside INTO an existing
aside's opening tag.

Root cause (find_aside_insertion_point, the ``existing_ch != ch`` branch):
the insertion offset was set to ``m.end()`` — the byte just after an
existing aside's ``id="note-…"`` attribute, i.e. INSIDE its opening tag.
Splicing there produced ``<aside …id="note-X"<aside …>…`` — malformed
XHTML that EPUB3 readers / epubcheck reject (1,322 occurrences across the
master HTML; surfaced only when validating XML well-formedness, since the
paired-marker check counts href/id pairs, not structure).

These tests pin the well-formedness contract so the defect can't recur.
"""

import sys
from pathlib import Path
from xml.etree import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts import inject  # noqa: E402

_XHTML = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<html xmlns="http://www.w3.org/1999/xhtml" '
    'xmlns:epub="http://www.idpf.org/2007/ops"><body>{body}</body></html>'
)


def _section_holding_foreign_chapter_aside():
    """A notes-section whose existing child aside belongs to a DIFFERENT
    chapter (ch33), reproducing the base-HTML / cascade topology that drives
    find_aside_insertion_point into the ``existing_ch != ch`` branch."""
    inner = (
        '\n<aside class="note note-comm" id="note-e3311" epub:type="footnote">\n<p>foreign ch33 body</p>\n</aside>\n'
    )
    body = '<aside class="notes-section" epub:type="footnotes" hidden="">' + inner + "</aside>\n"
    html = _XHTML.format(body=body)
    inside_start = html.index('hidden="">') + len('hidden="">')
    section = inject._aside_inside_range(html, inside_start)
    return html, section


class TestInjectAsideWellFormed:
    def test_insert_with_foreign_chapter_aside_stays_wellformed(self):
        html, section = _section_holding_foreign_chapter_aside()
        off = inject.find_aside_insertion_point(html, section, ch=26, v=33, suffix="a", prefix="e")
        block = inject.build_aside("lang-hebrew", "e2633a", "Hebrew", "<p>new body</p>")
        spliced = html[:off] + block + html[off:]
        # EPUB3 requires XML well-formedness; a mid-tag splice raises ParseError.
        ET.fromstring(spliced)

    def test_insertion_point_not_inside_open_tag(self):
        html, section = _section_holding_foreign_chapter_aside()
        off = inject.find_aside_insertion_point(html, section, ch=26, v=33, suffix="a", prefix="e")
        last_open = html.rfind("<", 0, off)
        last_close = html.rfind(">", 0, off)
        assert last_close >= last_open, (
            f"insertion offset {off} lands INSIDE an open tag: ...{html[off - 25 : off]!r}|{html[off : off + 12]!r}..."
        )


def test_chapter_region_b_end_lands_at_tag_start_not_inside_tag():
    """Root cause of the marker mid-tag splice (``<a<a …note-ref…>``):
    find_chapter_region_b ended the chapter region at the next chapter's
    ``id="ch-…"`` ATTRIBUTE position — which is INSIDE its ``<a>`` opening tag
    (``<a id="ch-…">`` → offset +3). The last verse's region thus carried a
    trailing ``<a `` fragment; the verse-end fallback trimmed the space and
    spliced the marker at tag-start+2, splitting the next chapter's tag and
    breaking XHTML. The region must end at that tag's ``<``, never inside it."""
    text = (
        '<a id="ch-b10-c1" class="ch-anchor"></a>'
        '<p><span class="vn">1</span> First chapter, only verse.</p>'
        '<a id="ch-b10-c2" class="ch-anchor"></a>'
        '<p><span class="vn">1</span> Second chapter.</p>'
    )
    _start, end = inject.find_chapter_region_b(text, "b10", 1, 2)
    assert text[end : end + 2] == "<a", (
        f"region end {end} is inside a tag, not at the next chapter tag start: {text[end - 4 : end + 16]!r}"
    )


def _no_unclosed_tag_before(s: str, off: int) -> bool:
    """True iff offset ``off`` is NOT inside an unterminated ``<…`` open tag."""
    return s.rfind("<", 0, off) <= s.rfind(">", 0, off)


def test_marker_fallback_backs_out_of_partial_tag():
    """Verse-end fallback must never land inside an unterminated opening tag.
    Strategy-B chapter-boundary / spill regions can over-run into the next
    chapter's ``<a id="ch-…">`` tag, leaving the verse region ending in a
    partial ``<a `` — the marker must back up to that tag's ``<``, not splice
    inside it (``<a<a …note-ref…>``)."""
    verse_html = "In the beginning God created. <a "
    off = inject.find_marker_insertion_point(verse_html, "")
    assert _no_unclosed_tag_before(verse_html, off), f"fallback offset {off} is inside a tag: {verse_html[:off]!r}"


def test_marker_fallback_not_placed_after_body():
    """Verse-end fallback must never land after ``</body>``. A last-chapter
    region that ran to EOF would otherwise place the marker after
    ``</body></html>`` ('junk after document element')."""
    verse_html = "Final verse text.</aside></body></html>"
    off = inject.find_marker_insertion_point(verse_html, "")
    assert "</body>" not in verse_html[:off], f"fallback offset {off} is past </body>: {verse_html[:off]!r}"
    assert _no_unclosed_tag_before(verse_html, off)


def test_chapter_region_b_excludes_notes_section_and_epilogue():
    """The LAST chapter's region must stop at the per-file notes-section /
    ``</body>``, not run to EOF — otherwise its verse-end-fallback marker is
    placed among the footnotes or after ``</body></html>``."""
    text = (
        '<a id="ch-b12-c29" class="ch-anchor"></a>'
        '<p><span class="vn">1</span> Final chapter, only verse.</p>'
        '<aside class="notes-section" epub:type="footnotes" hidden="">'
        '<aside class="note note-comm" id="note-1c2901" epub:type="footnote"><p>n</p></aside>'
        "</aside></body></html>"
    )
    _start, end = inject.find_chapter_region_b(text, "b12", 29, 29)
    assert text[end:].startswith('<aside class="notes-section"'), (
        f"region should end at the notes-section, got {text[end : end + 40]!r}"
    )


def test_all_master_html_is_wellformed_xml():
    """Integration guard: every ``epub_working/index_split_*.html`` must be
    well-formed XML. EPUB3 serves XHTML, so malformed markup makes editions
    unreadable on strict readers / fail epubcheck. The mid-tag aside-splice
    bug put 1,322 malformed asides into the master HTML yet ``ebible verify``
    stayed green — because that gate checks marker/id PAIRING, not XML
    structure. This pins the structural contract so the gap can't reopen."""
    epub_dir = REPO_ROOT / "epub_working"
    files = sorted(epub_dir.glob("index_split_*.html"))
    assert files, "no master HTML files found in epub_working/"
    bad = []
    for f in files:
        try:
            ET.fromstring(f.read_text(encoding="utf-8"))
        except ET.ParseError as e:
            bad.append(f"{f.name}: {e}")
    assert not bad, f"{len(bad)}/{len(files)} master HTML file(s) malformed:\n" + "\n".join(bad[:10])

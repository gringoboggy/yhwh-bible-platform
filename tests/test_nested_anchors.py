"""Nested-<a> detection + repair (epubcheck RSC-005 guard).

The recovered base HTML (v28a-50 snapshot) shipped 746 verses where a
``note-ref`` word-study marker sits INSIDE the ``vn-link`` verse-number
anchor — an ``<a>`` nested in an ``<a>``, which is invalid XHTML and the
sole cause of the RSC-005 errors. The repair relocates the note-ref to a
sibling immediately before the vn-link (preserving the exact glyph order),
so the vn-link wraps only its ``<span class="vn">N</span>``."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


BROKEN = (
    '<a class="vn-link" id="v-phi-1-6" href="#vnote-phi-1-6" epub:type="noteref" '
    'title="Paul’s Letter to the Philippians 1:6">'
    '<a class="note-ref note-lang-greek" id="ref-b700105a" href="#note-b700105a" '
    'epub:type="noteref" title="Greek word study">'
    '<sup class="marker-lang-greek">⌘</sup></a>'
    '<span class="vn">6</span></a>'
)
FIXED = (
    '<a class="note-ref note-lang-greek" id="ref-b700105a" href="#note-b700105a" '
    'epub:type="noteref" title="Greek word study">'
    '<sup class="marker-lang-greek">⌘</sup></a>'
    '<a class="vn-link" id="v-phi-1-6" href="#vnote-phi-1-6" epub:type="noteref" '
    'title="Paul’s Letter to the Philippians 1:6">'
    '<span class="vn">6</span></a>'
)
GOOD = (
    '<a class="vn-link" id="v-1ki-1-1" href="#vnote-1ki-1-1" epub:type="noteref" '
    'title="The First Book of Kings 1:1"><span class="vn">1</span></a>And king David was old.'
)


class TestDetect:
    def test_finds_note_ref_inside_vn_link(self):
        from scripts.check_nested_anchors import find_nested_anchors

        nested = find_nested_anchors(BROKEN)
        assert len(nested) == 1
        inner, outer = nested[0]
        assert "vn-link" in outer["class"]
        assert "note-ref" in inner["class"]

    def test_clean_wrapper_has_no_nesting(self):
        from scripts.check_nested_anchors import find_nested_anchors

        assert find_nested_anchors(GOOD) == []

    def test_already_fixed_has_no_nesting(self):
        from scripts.check_nested_anchors import find_nested_anchors

        assert find_nested_anchors(FIXED) == []


class TestRepair:
    def test_relocates_note_ref_before_vn_link(self):
        from scripts.check_nested_anchors import repair_html

        out, n = repair_html(BROKEN)
        assert n == 1
        assert out == FIXED

    def test_repair_removes_all_nesting(self):
        from scripts.check_nested_anchors import find_nested_anchors, repair_html

        out, _ = repair_html(BROKEN)
        assert find_nested_anchors(out) == []

    def test_idempotent_on_clean_wrapper(self):
        from scripts.check_nested_anchors import repair_html

        out, n = repair_html(GOOD)
        assert n == 0
        assert out == GOOD

    def test_idempotent_second_pass(self):
        from scripts.check_nested_anchors import repair_html

        once, _ = repair_html(BROKEN)
        twice, n2 = repair_html(once)
        assert n2 == 0
        assert twice == once

    def test_preserves_all_bytes_just_reordered(self):
        # The repair only MOVES bytes (an open tag), never adds or drops any.
        from scripts.check_nested_anchors import repair_html

        out, _ = repair_html(BROKEN)
        assert sorted(out) == sorted(BROKEN)

    def test_handles_two_markers_before_span(self):
        from scripts.check_nested_anchors import find_nested_anchors, repair_html

        two = (
            '<a class="vn-link" id="v-psa-1-1" href="#vnote-psa-1-1" epub:type="noteref" title="Psalms 1:1">'
            '<a class="note-ref note-lang-hebrew" id="ref-a" href="#note-a" epub:type="noteref" title="x">'
            '<sup class="marker-lang-hebrew">⌘</sup></a>'
            '<a class="note-ref note-lang-hebrew" id="ref-b" href="#note-b" epub:type="noteref" title="y">'
            '<sup class="marker-lang-hebrew">⌘</sup></a>'
            '<span class="vn">1</span></a>'
        )
        out, n = repair_html(two)
        assert find_nested_anchors(out) == []
        assert '<span class="vn">1</span></a>' in out
        assert sorted(out) == sorted(two)


class TestCommittedBaseClean:
    """Regression gate: the shipped base HTML must have zero nested <a>.

    Fails (746) until the one-time repair has been run across epub_working/."""

    def test_epub_working_has_zero_nested_anchors(self):
        from scripts.check_nested_anchors import find_nested_anchors

        total = 0
        offenders = []
        for f in sorted((REPO / "epub_working").glob("*.html")):
            n = len(find_nested_anchors(f.read_text(encoding="utf-8")))
            if n:
                offenders.append(f"{f.name}:{n}")
            total += n
        assert total == 0, f"nested <a> found in: {offenders}"

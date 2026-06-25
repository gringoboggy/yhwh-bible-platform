"""Regression tests for dev/audit_verse_formatting.py — the WS1 scripture-body formatting
auditor (Kobo deep-audit program, 2026-06-24; re-architected the same day).

The real device defect = a verse's TEXT spans a <p class="verse-p"> boundary, whose
signature is ALPHABETIC PROSE before a paragraph's first verse marker (the prose is the
previous verse's tail). The auditor must:
  - flag that (gen 19:1: "Lot saw them…" opens a 2nd paragraph that then carries v2),
  - NOT flag 1 Clement strategy-B chapters (plain <span class="vn"> verses, no v- anchor),
  - NOT flag psalm superscriptions / Song speaker rubrics / section headings (prose-only,
    no verse marker),
  - NOT flag chapter-start paragraphs whose leading content is only note-markers/badges,
  - attribute ¶ / [bracket] to the nearest PRECEDING verse marker (gen 46:13, not 46:1),
  - route irregular-apocrypha breaks (1 Enoch, Jubilees…) to a WARN bucket, not the ERROR gate.
"""

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("audit_verse_formatting", REPO / "dev" / "audit_verse_formatting.py")
avf = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = avf  # dataclasses field() resolution needs the module registered
_spec.loader.exec_module(avf)


def _vp(*chunks):
    return '<p class="verse-p">' + "".join(chunks) + "</p>"


def _vn(book, ch, v, num=None):
    """Strategy-A verse marker: deep-link anchor wrapping the verse-number span."""
    num = num if num is not None else v
    return (
        f'<a class="vn-link" id="v-{book}-{ch}-{v}" href="#vnote-{book}-{ch}-{v}" '
        f'epub:type="noteref" title="{book} {ch}:{v}"><span class="vn">{num}</span></a>'
    )


def _plain_vn(num):
    """Strategy-B verse marker: a bare verse-number span (1 Clement etc.)."""
    return f'<span class="vn">{num}</span>'


def _markers(*nums):
    """Leading note-ref markers + a category badge (digits/glyphs — NOT prose)."""
    sup = "".join(f'<a class="note-ref"><sup class="marker-num">{n}</sup></a>' for n in nums)
    return sup + '<span class="marker-badge">✦</span>'


class TestCleanVerse:
    def test_clean_verse_has_no_findings(self):
        rep = avf.scan_html(_vp(_vn("gen", 1, 1), " In the beginning God created the heavens and the earth."), "clean")
        assert rep.verses == 1
        assert rep.mid_verse_break == [] and rep.pilcrow == [] and rep.kjv_bracket == []
        assert rep.failed is False

    def test_chapter_start_with_leading_note_markers_is_not_a_break(self):
        # Leading "12✦" are markers/badges (digits + glyph), not prose → must NOT flag.
        html = _vp(
            _markers(1, 2), _vn("gen", 2, 1), "  The heavens, the earth, and all their vast array were finished."
        )
        rep = avf.scan_html(html, "gen")
        assert rep.mid_verse_break == []
        assert rep.superscription == []
        assert rep.verses == 1


class TestMidVerseLineBreak:
    def test_prose_before_next_marker_is_flagged_to_previous_verse(self):
        # gen 19:1 split: paragraph B opens with v1's tail prose, then carries v2's marker.
        html = (
            _vp(_vn("gen", 19, 1), " The two angels came to Sodom at evening. Lot sat in the gate of Sodom.")
            + "\n"
            + _vp(
                "Lot saw them, and rose up to meet them. He bowed himself with his face to the earth,",
                _vn("gen", 19, 2),
                " and he said, “See now, my lords.”",
            )
        )
        rep = avf.scan_html(html, "gen")
        assert [f.verse for f in rep.mid_verse_break] == ["gen 19:1"]
        assert rep.failed is True

    def test_irregular_book_break_is_warn_not_error(self):
        # 1 Enoch is an irregular-layout apocryphon → break routes to the WARN bucket.
        html = _vp(_vn("1en", 27, 1), " text of verse one.") + _vp(
            "continuation prose of verse one,", _vn("1en", 27, 2), " verse two text."
        )
        rep = avf.scan_html(html, "1en")
        assert rep.mid_verse_break == []  # not in the ERROR gate
        assert [f.verse for f in rep.irregular_break] == ["1en 27:1"]
        assert rep.failed is False  # WARN-only does not fail the gate

    def test_gate_all_includes_irregular(self):
        html = _vp(_vn("1en", 27, 1), " one.") + _vp("tail prose,", _vn("1en", 27, 2), " two.")
        rep = avf.scan_html(html, "1en", gate_all=True)
        assert [f.verse for f in rep.mid_verse_break] == ["1en 27:1"]


class TestStrategyBNotFlagged:
    def test_plain_vn_chapter_is_not_a_break(self):
        # 1 Clement: each chapter is one paragraph, verses are inline plain <span class="vn">.
        html = _vp(
            _plain_vn(1), " By reason of the sudden calamities. ", _plain_vn(2), " And ye were all lowly in mind."
        )
        rep = avf.scan_html(html, "1cl")
        assert rep.mid_verse_break == []
        assert rep.irregular_break == []
        assert rep.strategy_b_verses == 2
        assert rep.verses == 0  # no deep-link anchors

    def test_strategy_b_midverse_split_is_a_warn(self):
        # A 1cl chapter split mid-verse: 2nd paragraph opens with prose then a plain vn.
        html = _vp("And again He saith, they lied unto Him with their tongue;", _plain_vn(5), " For this cause.")
        rep = avf.scan_html(html, "1cl")
        assert rep.mid_verse_break == [] and rep.irregular_break == []
        assert len(rep.strategy_b_continuation) == 1


class TestSuperscriptionsAndRubrics:
    def test_psalm_superscription_is_not_a_break(self):
        html = _vp(_vn("psa", 2, 12), " Blessed are all those who take refuge in him.") + _vp(
            "A Psalm by David, when he fled from Absalom his son."
        )
        rep = avf.scan_html(html, "psa")
        assert rep.mid_verse_break == []
        assert len(rep.superscription) == 1

    def test_song_speaker_rubric_is_not_a_break(self):
        html = _vp(_vn("sng", 1, 1), " The Song of songs, which is Solomon’s.") + _vp(
            '<em class="cited-work">Beloved</em>'
        )
        rep = avf.scan_html(html, "sng")
        assert rep.mid_verse_break == []
        assert len(rep.superscription) == 1


class TestPilcrowAndBrackets:
    def test_pilcrow_attributed_to_nearest_preceding_verse(self):
        # Multi-verse paragraph: the ¶ sits after v13's marker → must read 46:13, not 46:1.
        html = _vp(
            _vn("gen", 46, 11),
            " The sons of Levi.",
            _vn("gen", 46, 12),
            " The sons of Judah.",
            _vn("gen", 46, 13),
            " ¶ And the sons of Issachar; Tola, and Phuvah.",
        )
        rep = avf.scan_html(html, "gen")
        assert [f.verse for f in rep.pilcrow] == ["gen 46:13"]
        assert rep.failed is True

    def test_kjv_bracket_attributed_to_nearest_preceding_verse(self):
        html = _vp(
            _vn("gen", 49, 13),
            " Zebulun will dwell at the haven of the sea.",
            _vn("gen", 49, 14),
            " Issachar [is] a strong ass couching down between two burdens.",
        )
        rep = avf.scan_html(html, "gen")
        assert [f.verse for f in rep.kjv_bracket] == ["gen 49:14"]

    def test_digit_brackets_are_not_kjv_supplied_words(self):
        rep = avf.scan_html(_vp(_vn("gen", 1, 1), " In the beginning [1] God created the heavens."), "gen")
        assert rep.kjv_bracket == []


class TestBadgeTrail:
    def test_counts_badge_trail_spans(self):
        html = _vp(_vn("gen", 1, 1), ' x.<span class="badge-trail" aria-hidden="true"> ​ </span>') + _vp(
            _vn("gen", 1, 2), ' y.<span class="badge-trail" aria-hidden="true"> ​ </span>'
        )
        rep = avf.scan_html(html, "gen")
        assert rep.badge_trail == 2


class TestReportAggregateAndExit:
    def test_failed_only_on_error_classes(self):
        clean = avf.scan_html(_vp(_vn("gen", 1, 1), " clean."), "x")
        assert clean.failed is False
        broken = avf.scan_html(
            _vp(_vn("gen", 1, 1), " head.") + _vp("spilled tail prose,", _vn("gen", 1, 2), " next."), "x"
        )
        assert broken.failed is True

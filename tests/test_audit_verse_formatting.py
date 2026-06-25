"""Regression tests for dev/audit_verse_formatting.py — the WS1 scripture-body formatting
auditor (Kobo deep-audit program, 2026-06-24).

Device-QA root causes it must catch (proven against the built flagship epub):
- mid-verse line break = a verse split across multiple <p class="verse-p"> blocks (gen 19:1:
  "Lot saw them…" is a 2nd paragraph still tagged vbadge-gen-19-1-comm)
- the "weird symbol" = a pilcrow ¶ in the verse text (gen 46:13 / 49:14)
- mixed-translation: KJV-isms (¶ + [bracketed] supplied words) on verses whose neighbors are WEB
"""

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("audit_verse_formatting", REPO / "dev" / "audit_verse_formatting.py")
avf = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = avf  # dataclasses field() resolution needs the module registered
_spec.loader.exec_module(avf)


def _vp(anchor_html, text):
    return f'<p class="verse-p">{anchor_html}{text}</p>'


def _vn(book, ch, v, num=None):
    num = num if num is not None else v
    return f'<a class="vn-link" id="v-{book}-{ch}-{v}" href="#vnote-{book}-{ch}-{v}"><span class="vn">{num}</span></a>'


class TestCleanVerse:
    def test_clean_verse_has_no_findings(self):
        html = _vp(_vn("gen", 1, 1), " In the beginning God created the heavens and the earth.")
        rep = avf.scan_html(html, "clean")
        assert rep.verses == 1
        assert rep.multi_paragraph == [] and rep.pilcrow == [] and rep.kjv_bracket == []


class TestMidVerseLineBreak:
    def test_continuation_paragraph_is_flagged(self):
        # gen 19:1 split across two <p class="verse-p"> — the 2nd has no v- anchor (a mid-verse break).
        html = (
            _vp(_vn("gen", 19, 1), " The two angels came to Sodom at evening. Lot sat in the gate.")
            + "\n"
            + _vp(
                '<a class="study-glossary-jump" id="vbadge-gen-19-1-comm" href="x"></a>',
                "Lot saw them, and rose up to meet them.",
            )
            + "\n"
            + _vp(_vn("gen", 19, 2), " He said, behold now, my lords.")
        )
        rep = avf.scan_html(html, "gen")
        assert rep.verses == 2  # two verse-start paragraphs (v1, v2)
        assert [f.verse for f in rep.multi_paragraph] == ["gen 19:1"]  # the continuation belongs to v1

    def test_two_continuations_attributed_to_their_verses(self):
        html = (
            _vp(_vn("gen", 19, 1), " A.")
            + _vp("", "continuation of one")  # no anchor at all -> still current verse
            + _vp(_vn("gen", 19, 2), " B.")
            + _vp('<a id="vbadge-gen-19-2-hist" href="x"></a>', "continuation of two")
        )
        rep = avf.scan_html(html, "gen")
        assert [f.verse for f in rep.multi_paragraph] == ["gen 19:1", "gen 19:2"]


class TestPilcrowAndBrackets:
    def test_pilcrow_in_verse_is_flagged(self):
        html = _vp(_vn("gen", 46, 13), " ¶ And the sons of Issachar; Tola, and Phuvah.")
        rep = avf.scan_html(html, "gen")
        assert [f.verse for f in rep.pilcrow] == ["gen 46:13"]

    def test_kjv_bracket_and_pilcrow_both_flagged(self):
        html = _vp(_vn("gen", 49, 14), " ¶ Issachar [is] a strong ass couching down between two burdens:")
        rep = avf.scan_html(html, "gen")
        assert [f.verse for f in rep.pilcrow] == ["gen 49:14"]
        assert [f.verse for f in rep.kjv_bracket] == ["gen 49:14"]

    def test_digit_brackets_are_not_kjv_supplied_words(self):
        # [1] (a footnote marker) must NOT be flagged as a KJV supplied word.
        html = _vp(_vn("gen", 1, 1), " In the beginning [1] God created the heavens.")
        rep = avf.scan_html(html, "gen")
        assert rep.kjv_bracket == []


class TestBadgeTrail:
    def test_counts_badge_trail_spans(self):
        html = _vp(_vn("gen", 1, 1), ' x.<span class="badge-trail" aria-hidden="true"> ​ ​ </span>') + _vp(
            _vn("gen", 1, 2), ' y.<span class="badge-trail" aria-hidden="true"> ​ </span>'
        )
        rep = avf.scan_html(html, "gen")
        assert rep.badge_trail == 2


class TestReportAggregateAndExit:
    def test_failed_true_on_any_break_or_pilcrow(self):
        clean = avf.scan_html(_vp(_vn("gen", 1, 1), " clean."), "x")
        assert clean.failed is False
        broken = avf.scan_html(_vp(_vn("gen", 46, 13), " ¶ pilcrow."), "x")
        assert broken.failed is True

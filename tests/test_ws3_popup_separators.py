"""WS3 — Kobo run-on popup fix (2026-06-25).

The study/cascade ``verse-notes`` family separated its category heads, source
bylines, and note rows ONLY with hidden ``<span class="vn-sep">`` spans carrying
U+2028. Kobo's native Footnote-preview overlay (tag-stripped, book-CSS dropped)
drops the U+2028, so the blocks ran together on-device. WS3 first gave the family
a visible ``·`` (U+00B7) plus a kobo-safe ``<br class="kobo-vn-br">``; the
2026-06-28 device-QA round then REVISED the decision to **clean, no visible
marker** (the ``·`` — and its Play-profile cousins ``¶``/``◦``/``•`` — cluttered
the CSS-blind footnote popups), so the eink separator is now the **bare
``<br class="kobo-vn-br">`` only**, no glyph. Still EINK-ONLY, threaded as
``eink=False`` by default so non-eink / 9-KJV output stays byte-identical.

Tests assert against the real ``build_edition`` separator constants (current and
eink) rather than retyped glyph literals, so test and implementation can never
drift on an invisible character (NBSP / U+2028).

Spec + device sources: ``dev/audit/kobo-popup-formatting-research.md`` §Recommended fix.
"""

import scripts.build_edition as be
from scripts.build_edition import (
    _VN_SEP_BYLINE,
    _VN_SEP_BYLINE_EINK,
    _VN_SEP_CAT,
    _VN_SEP_CAT_EINK,
    _VN_SEP_ITEM,
    _VN_SEP_ITEM_EINK,
    _badge_aside_inner_to_row,
    _chunk_vn_item_row,
    _emit_cascade_sections,
)

_KOBO_BR = '<br class="kobo-vn-br" />'  # ASCII — unambiguous
# chr() so an invisible/look-alike character can never sneak in (a regular space is
# NOT U+2028; the · / • below must be exactly U+00B7 / U+2022).
_MIDDOT = chr(0x00B7)  # · the only on-device-proven visible separator glyph
_U2028 = chr(0x2028)  # the Nickel-dropped LINE SEPARATOR the eink faces must avoid
_BULLET = chr(0x2022)  # • the near-crash glyph the eink faces must avoid


def _cascade_rows():
    return [
        {
            "cat": "lang",
            "source_key": "strongs",
            "source_display": "Strong's Concordance",
            "suppress_byline": False,
            "row": '<div class="vn-item note-lang-hebrew">L1</div>',
        },
        {
            "cat": "topic",
            "source_key": "nave",
            "source_display": "Nave's Topical Bible",
            "suppress_byline": False,
            "row": '<div class="vn-item note-topic-nave">T1</div>',
        },
    ]


_CAT_META = {"lang": ("⌘", "Linguistic"), "topic": ("✦", "Topical")}


class TestEinkSeparatorConstants:
    """Device-QA 2026-06-28 decision: CLEAN, no visible marker. All three eink
    faces (item / byline / cat-head) are the bare kobo-safe ``<br>`` only — no
    middot, no bullet, no Nickel-dropped U+2028. Line structure comes from the
    break (plus the block ``<p>`` flow), not a glyph."""

    def test_all_eink_separators_are_the_bare_kobo_break(self):
        for const in (_VN_SEP_ITEM_EINK, _VN_SEP_BYLINE_EINK, _VN_SEP_CAT_EINK):
            assert const == _KOBO_BR

    def test_no_visible_or_dropped_glyph_on_any_eink_separator(self):
        # the · is GONE (clean, no marker); the • near-crash and U+2028 Nickel-drop
        # were never wanted on eink — assert all three stay absent.
        for const in (_VN_SEP_ITEM_EINK, _VN_SEP_BYLINE_EINK, _VN_SEP_CAT_EINK):
            assert _MIDDOT not in const
            assert _BULLET not in const
            assert _U2028 not in const


class TestCascadeSeparators:
    def test_default_keeps_hidden_separators_byte_stable(self):
        # Non-eink (default) is the byte-stable 9-KJV path: hidden spans unchanged.
        out = _emit_cascade_sections(_cascade_rows(), _CAT_META)
        assert out.count(f'<p class="vn-cat-head">{_VN_SEP_CAT}<span class="vn-cat-sym"') == 2
        assert out.count(f'<p class="vn-source-byline">{_VN_SEP_BYLINE}') == 2
        assert _KOBO_BR not in out

    def test_eink_swaps_to_device_proven_separators(self):
        out = _emit_cascade_sections(_cascade_rows(), _CAT_META, eink=True)
        assert out.count(f'<p class="vn-cat-head">{_VN_SEP_CAT_EINK}<span class="vn-cat-sym"') == 2
        assert out.count(f'<p class="vn-source-byline">{_VN_SEP_BYLINE_EINK}') == 2
        # the Nickel-dropped hidden separators are gone on eink
        assert _VN_SEP_CAT not in out
        assert _VN_SEP_BYLINE not in out


class TestBadgeRowSeparator:
    def test_default_item_separator_unchanged(self):
        row = _badge_aside_inner_to_row("<p>body text</p>", "comm")
        assert row.startswith(f'<div class="vn-item note-comm">{_VN_SEP_ITEM}')

    def test_eink_item_separator_is_device_proven(self):
        row = _badge_aside_inner_to_row("<p>body text</p>", "comm", eink=True)
        assert row.startswith(f'<div class="vn-item note-comm">{_VN_SEP_ITEM_EINK}')
        assert _VN_SEP_ITEM not in row


class TestChunkRowSeparator:
    ROW_FMT = '<div class="vn-item note-dict-easton">' + _VN_SEP_ITEM + "<p>{}</p></div>"

    def _long_row(self):
        body = " ".join(f"Sentence number {i} about David the king of Israel." for i in range(400))
        return self.ROW_FMT.format(body)

    def test_default_continuation_uses_hidden_item_separator(self):
        parts = _chunk_vn_item_row(self._long_row(), 3_800)
        assert len(parts) >= 2
        # continuation parts (index >= 1) carry the hidden item separator unchanged
        assert any(_VN_SEP_ITEM in p for p in parts[1:])
        assert all(_KOBO_BR not in p for p in parts)

    def test_eink_continuation_uses_device_proven_separator(self):
        parts = _chunk_vn_item_row(self._long_row(), 3_800, eink=True)
        assert len(parts) >= 2
        assert any(_VN_SEP_ITEM_EINK in p for p in parts[1:])
        # the GENERATED continuation parts (index >= 1) carry the eink separator, not the
        # hidden one (part 0 keeps the input row's own prefix separator verbatim, by design)
        assert all(_VN_SEP_ITEM not in p for p in parts[1:])


class TestF1NoLeadingBreakAfterByline:
    """device-QA round-2 F1: on eink the FIRST ``.vn-item`` row after a source byline
    carried a leading ``<br class="kobo-vn-br">`` (baked by ``_badge_aside_inner_to_row``)
    → a blank line between the italic byline and the note body. The byline ``<p>`` already
    starts a new line, so that first leading break is dropped on eink (continuation rows
    keep theirs to stay separated). Non-eink output is untouched (byte-stable / 9-KJV)."""

    def _rows_with_real_seps(self, eink: bool):
        return [
            {
                "cat": "lang",
                "source_key": "strongs",
                "source_display": "Strong's Concordance",
                "suppress_byline": False,
                "row": _badge_aside_inner_to_row("<p>Body one.</p>", "lang-hebrew", eink=eink),
            },
            {
                "cat": "lang",
                "source_key": "strongs",
                "source_display": "Strong's Concordance",
                "suppress_byline": False,
                "row": _badge_aside_inner_to_row("<p>Body two.</p>", "lang-hebrew", eink=eink),
            },
        ]

    def test_first_row_after_byline_drops_leading_break_on_eink(self):
        out = _emit_cascade_sections(self._rows_with_real_seps(eink=True), _CAT_META, eink=True)
        # byline still emitted with its own eink break
        assert f'<p class="vn-source-byline">{_VN_SEP_BYLINE_EINK}' in out
        # FIRST row's body abuts the div open — no leading break before it
        assert '<div class="vn-item note-lang-hebrew"><p>Body one.' in out
        assert f'<div class="vn-item note-lang-hebrew">{_KOBO_BR}<p>Body one.' not in out
        # the SECOND row in the same source group keeps its leading break (separation)
        assert f'<div class="vn-item note-lang-hebrew">{_KOBO_BR}<p>Body two.' in out

    def test_non_eink_first_row_keeps_hidden_sep_byte_stable(self):
        out = _emit_cascade_sections(self._rows_with_real_seps(eink=False), _CAT_META)
        # the hidden U+2028 item separator on the first row is preserved (golden byte-stable)
        assert f'<div class="vn-item note-lang-hebrew">{_VN_SEP_ITEM}<p>Body one.' in out
        assert _KOBO_BR not in out


class TestEinkReaderCss:
    def test_kobo_vn_br_line_height_rule_present(self):
        assert "br.kobo-vn-br {" in be._EINK_READER_CSS

    def test_eink_overrides_inline_block_badge_to_plain_inline(self):
        # device-QA round-2 C: the base sheet's inline-block badge rule breaks Kobo's
        # justified flow; the eink append re-asserts plain inline AFTER it (last-rule-wins).
        base = ".verse-notes-badge, .study-glossary-jump, .vn-link { display: inline-block; white-space: nowrap; }\n"
        out = be.apply_eink_reader_css(base, {"target_reader": "eink"})
        assert out.rindex("display: inline;") > out.index("display: inline-block;")

    def test_non_eink_leaves_inline_block_untouched(self):
        base = ".verse-notes-badge { display: inline-block; }\n"
        assert be.apply_eink_reader_css(base, {"target_reader": "tablet"}) == base

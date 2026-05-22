"""Tests for the note-marker symbol system: data-driven glyph_for + the
base-HTML glyph resync. Symbols are defined in content/categories.yaml (one per
category) and content/kinds.yaml (per kind, incl. overrides like comm-ai)."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


class TestGlyphForDataDriven:
    def test_topic_renders_topical_symbol(self):
        from scripts.inject import glyph_for

        assert glyph_for("topic-nave") == "✦"

    def test_hist_kind_renders_historical_symbol(self):
        # The bug: only dict-* got ⌂; hist-* fell through to ◇.
        from scripts.inject import glyph_for

        assert glyph_for("hist-ane") == "⌂"

    def test_dist_renders_distinctive_symbol(self):
        from scripts.inject import glyph_for

        assert glyph_for("dist-typological") == "❖"

    def test_comm_ai_renders_its_override_symbol(self):
        # comm-ai deliberately overrides its category (◇) with its own AI badge.
        from scripts.inject import glyph_for

        assert glyph_for("comm-ai") == "Ⓐ"

    def test_all_15_category_symbols_reachable(self):
        from scripts.core import config
        from scripts.inject import glyph_for

        cats = {c["id"]: c["symbol"] for c in config.load_categories()}
        produced = {glyph_for(k["code"]) for k in config.load_kinds()}
        missing = {cid: sym for cid, sym in cats.items() if sym not in produced}
        assert not missing, f"category symbols never produced by any kind: {missing}"

    def test_regressions_unchanged(self):
        from scripts.inject import glyph_for

        assert glyph_for("lang-hebrew") == "⌘"
        assert glyph_for("comm-ethiopian") == "◇"
        assert glyph_for("xref-citation") == "‖"
        assert glyph_for("text-witness") == "✧"
        assert glyph_for("dict-easton") == "⌂"

    def test_unknown_kind_falls_back_to_default(self):
        from scripts.inject import glyph_for

        assert glyph_for("totally-unknown-xyz") == "◇"


class TestResyncGlyphs:
    def test_fixes_wrong_marker_glyph(self):
        from scripts.resync_marker_glyphs import resync_glyphs

        out, n = resync_glyphs('<sup class="marker-topic-nave">◇</sup>')
        assert out == '<sup class="marker-topic-nave">✦</sup>'
        assert n == 1

    def test_fixes_note_back_glyph(self):
        from scripts.resync_marker_glyphs import resync_glyphs

        text = (
            '<aside class="note note-topic-nave" id="note-g0101a" epub:type="footnote">\n'
            '  <p><a href="#ref-g0101a" class="note-back" title="Back">◇</a> '
            '<span class="note-label">Topic.</span> body</p>\n</aside>'
        )
        out, n = resync_glyphs(text)
        assert '<a href="#ref-g0101a" class="note-back" title="Back">✦</a>' in out
        assert n == 1

    def test_correct_glyph_unchanged_and_idempotent(self):
        from scripts.resync_marker_glyphs import resync_glyphs

        text = '<sup class="marker-lang-hebrew">⌘</sup>'
        out, n = resync_glyphs(text)
        assert out == text and n == 0
        out2, n2 = resync_glyphs(out)
        assert out2 == out and n2 == 0

    def test_marker_and_noteback_together(self):
        from scripts.resync_marker_glyphs import resync_glyphs

        text = (
            '<sup class="marker-dist-typological">◇</sup>'
            '<aside class="note note-dist-typological" id="note-x" epub:type="footnote">\n'
            '  <p><a href="#ref-x" class="note-back" title="Back">◇</a> body</p>\n</aside>'
        )
        out, n = resync_glyphs(text)
        assert '<sup class="marker-dist-typological">❖</sup>' in out
        assert '<a href="#ref-x" class="note-back" title="Back">❖</a>' in out
        assert n == 2

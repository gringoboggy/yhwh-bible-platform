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

        # State-independent (RULES §8): clear the config singletons so an earlier
        # test that mutated categories/kinds can't leak a stale symbol in here.
        config.load_categories.cache_clear()
        config.load_kinds.cache_clear()

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

    def test_leaves_numbered_marker_untouched(self):
        # After the Wave-3 re-bake the inline marker holds a footnote NUMBER
        # (class marker-num), not a category glyph. glyph_for("num") would be
        # the ◇ default — resync_glyphs must NOT overwrite the number with it.
        from scripts.resync_marker_glyphs import resync_glyphs

        out, n = resync_glyphs('<sup class="marker-num">5</sup>')
        assert out == '<sup class="marker-num">5</sup>'
        assert n == 0

    def test_leaves_return_arrow_back_link_untouched(self):
        # The Wave-3 back-link is a fixed ↩ (the category symbol moved into a
        # sibling note-sym). resync_glyphs must not revert ↩ to the kind glyph.
        from scripts.resync_marker_glyphs import resync_glyphs

        text = (
            '<aside class="note note-topic-nave" id="note-g0101a" epub:type="footnote">\n'
            '  <p><a href="#ref-g0101a" class="note-back" title="Back">↩</a> '
            '<a class="note-sym" href="legend.xhtml#legend-topic" title="Topical">✦</a> '
            '<span class="note-label">Topic.</span> body</p>\n</aside>'
        )
        out, n = resync_glyphs(text)
        assert 'class="note-back" title="Back">↩</a>' in out
        assert n == 0


class TestHtmlTitleDataDriven:
    def test_topic_uses_descriptive_title(self):
        from scripts.inject import html_title_for

        t = html_title_for("topic-nave")
        assert t != "Note"
        assert "Nave" in t

    def test_every_registered_kind_uses_its_title_attr(self):
        from scripts.core import config
        from scripts.inject import html_title_for

        bad = {
            c: (html_title_for(c), k["title_attr"])
            for c, k in config.kinds_by_code().items()
            if k.get("title_attr") and html_title_for(c) != k["title_attr"]
        }
        assert not bad, f"kinds whose tooltip != their title_attr: {bad}"

    def test_lang_hebrew_uses_title_attr(self):
        from scripts.inject import html_title_for

        assert html_title_for("lang-hebrew") == "Hebrew word study"

    def test_unregistered_falls_back_to_note(self):
        from scripts.inject import html_title_for

        assert html_title_for("totally-unknown-xyz") == "Note"


class TestResyncTitles:
    def test_resyncs_default_note_to_title_attr(self):
        from scripts.inject import html_title_for
        from scripts.resync_marker_glyphs import resync_titles

        text = (
            '<a class="note-ref note-topic-nave" id="ref-x" href="#note-x" '
            'epub:type="noteref" title="Note"><sup class="marker-topic-nave">✦</sup></a>'
        )
        out, n = resync_titles(text)
        assert f'title="{html_title_for("topic-nave")}"' in out
        assert n == 1

    def test_idempotent_when_already_correct(self):
        from scripts.inject import html_title_for
        from scripts.resync_marker_glyphs import resync_titles

        correct = html_title_for("lang-hebrew")
        text = (
            '<a class="note-ref note-lang-hebrew" id="ref-y" href="#note-y" '
            f'epub:type="noteref" title="{correct}"><sup class="marker-lang-hebrew">⌘</sup></a>'
        )
        out, n = resync_titles(text)
        assert out == text and n == 0

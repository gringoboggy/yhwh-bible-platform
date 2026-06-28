"""Round-16 remediation — Phase H (behaviour-changing build-path fixes).

Unit pins for the byte-sensitive Phase-H items. The full 9-KJV byte-proof lives in
``test_kjv_golden_hash_gate.py`` (slow); these are the fast per-helper RED→GREEN pins.
Item numbers track ``dev/audit/round16-unified-remediation-plan.md`` Phase H.

  H2  eink study-glossary return link — per-chapter v-anchor gate (not strategy=='B')
  H3  numbers+eink note-sym glyph repair pass (badge path already substitutes)
  H4  eink backmatter glossary split-group part indicator (vn-part)
  H5  apply_eink_verse_line_breaks recognises verse-p-flush openers
  H7  OPF a11y:certifiedBy no longer ships the TODO_CERTIFIER_NAME placeholder
  H9  computer target reader is an explicit alias of everywhere
  H10 dot marker_badge_style coerced to chip on eink (eink-unsafe guard)

H1 (kindle build_one kindle-safe) is a slow build pin in
``test_kjv_golden_hash_gate``/``test_round16_build_gates``; H6/H8 are pinned by the
golden + the build-free gate tests in ``test_round16_source_gates.py``.
"""

from __future__ import annotations

import scripts.build_edition as be


# ----------------------------------------------------------------------
# H9 — computer is an explicit alias of everywhere
# ----------------------------------------------------------------------
class TestComputerAlias:
    def test_resolve_target_reader_aliases_computer_to_everywhere(self):
        assert be.resolve_target_reader({"target_reader": "computer"}) == "everywhere"

    def test_apply_target_override_folds_computer_to_everywhere(self):
        folded = be.apply_target_override({"id": "x"}, "computer")
        assert folded["target_reader"] == "everywhere"

    def test_real_targets_unchanged_by_alias(self):
        # the byte-stable golden cells use these — the alias must not perturb them
        assert be.resolve_target_reader({"target_reader": "tablet"}) == "tablet"
        assert be.resolve_target_reader({"target_reader": "kindle"}) == "kindle"
        assert be.resolve_target_reader({"target_reader": "eink"}) == "eink"
        assert be.resolve_target_reader({}) == "everywhere"


# ----------------------------------------------------------------------
# H10 — dot marker_badge_style is eink-unsafe → coerce to chip on eink only
# ----------------------------------------------------------------------
class TestDotBadgeEinkGuard:
    def test_dot_coerced_to_chip_on_eink(self):
        ed = {"target_reader": "eink", "marker_badge_style": "dot"}
        assert be.resolve_marker_badge_style(ed) == "chip"

    def test_dot_preserved_on_non_eink(self):
        ed = {"target_reader": "everywhere", "marker_badge_style": "dot"}
        assert be.resolve_marker_badge_style(ed) == "dot"

    def test_safe_eink_style_preserved(self):
        ed = {"target_reader": "eink", "marker_badge_style": "lozenge"}
        assert be.resolve_marker_badge_style(ed) == "lozenge"


# ----------------------------------------------------------------------
# H2 — eink study-glossary return link gates on per-chapter v-anchors
# ----------------------------------------------------------------------
class TestStudyReturnLinkVerseAnchored:
    def test_verse_anchored_true_uses_v_anchor(self):
        # psa is strategy B WITH a bxx but its chapters DO carry per-verse anchors
        link = be._study_verse_return_link("psa", 23, 1, verse_anchored=True)
        assert 'href="#v-psa-23-1"' in link

    def test_verse_anchored_false_uses_chapter_opener(self):
        link = be._study_verse_return_link("psa", 23, 1, verse_anchored=False)
        assert 'href="#ch-b30-c23"' in link

    def test_legacy_none_preserves_strategy_inference(self):
        # back-compat: None == the historical strategy-only behaviour
        # strategy-B + bxx → chapter opener
        assert 'href="#ch-b30-c23"' in be._study_verse_return_link("psa", 23, 1, verse_anchored=None)
        # strategy-A → per-verse anchor
        assert 'href="#v-gen-1-1"' in be._study_verse_return_link("gen", 1, 1, verse_anchored=None)


# ----------------------------------------------------------------------
# H5 — apply_eink_verse_line_breaks treats verse-p-flush as a para opener
# ----------------------------------------------------------------------
class TestVersePFlushOpener:
    def test_flush_opener_recognised(self):
        # a vn-link directly after a verse-p-flush opener must NOT be double-broken
        assert be._VN_LINK_AT_PARA_START_RE.search('<p class="verse-p-flush">  ')

    def test_plain_verse_p_still_recognised(self):
        assert be._VN_LINK_AT_PARA_START_RE.search('<p class="verse-p">  ')

    def test_midparagraph_not_matched(self):
        assert not be._VN_LINK_AT_PARA_START_RE.search("some prose text ")


# ----------------------------------------------------------------------
# H3 — eink numbers-mode note-sym glyph repair (badge path already does it)
# ----------------------------------------------------------------------
class TestEinkNoteSymRepair:
    _ROW = '<a class="note-sym" href="legend.xhtml#legend-topic">✦</a>'

    def test_repairs_on_eink_numbers(self):
        pre = {"a.html": self._ROW}
        n = be.apply_eink_note_sym_repair({"target_reader": "eink"}, preloaded=pre, marker_style="numbers")
        assert n == 1
        assert "✦" not in pre["a.html"]  # the Cardo-absent glyph is gone

    def test_noop_in_badge_mode(self):
        pre = {"a.html": self._ROW}
        n = be.apply_eink_note_sym_repair({"target_reader": "eink"}, preloaded=pre, marker_style="badge")
        assert n == 0
        assert pre["a.html"] == self._ROW

    def test_noop_on_non_eink(self):
        pre = {"a.html": self._ROW}
        n = be.apply_eink_note_sym_repair({"target_reader": "everywhere"}, preloaded=pre, marker_style="numbers")
        assert n == 0
        assert pre["a.html"] == self._ROW


# ----------------------------------------------------------------------
# H4 — eink backmatter glossary split-group part indicator
# ----------------------------------------------------------------------
class TestGlossaryPartIndicator:
    def _rows(self, n: int, size: int):
        # n rows in ONE category, each big enough that >1 together exceeds the pack cap
        return [{"cat": "comm", "row": f'<div class="vn-item note-comm">{"x" * size}</div>'} for _ in range(n)]

    def test_multi_group_carries_part_indicator(self):
        # two ~5k rows in one category → two packed footnote groups → vn-part (1/2),(2/2)
        rows = self._rows(2, 5000)
        inner, _targets = be._emit_backmatter_glossary_inner(
            rows, {"comm": ("⊕", "Commentary")}, "psa", 23, 1, s2_group=False, eink=True
        )
        assert 'class="vn-part"' in inner
        assert "(1/2)" in inner
        assert "(2/2)" in inner

    def test_single_group_has_no_part_indicator(self):
        rows = self._rows(1, 500)
        inner, _targets = be._emit_backmatter_glossary_inner(
            rows, {"comm": ("⊕", "Commentary")}, "psa", 23, 1, s2_group=False, eink=True
        )
        assert "vn-part" not in inner


# ----------------------------------------------------------------------
# H7 — OPF a11y:certifiedBy no longer ships the TODO placeholder
# ----------------------------------------------------------------------
class TestOpfCertifierNoPlaceholder:
    def _patched_opf(self) -> str:
        from scripts.core import config

        ed = config.editions_by_id()["catholic-study"]
        opf = '<?xml version="1.0"?>\n<package><metadata>\n    <dc:language>en</dc:language>\n  </metadata></package>\n'
        return be.patch_opf(opf, ed, "v28a-test")

    def test_no_todo_certifier_placeholder(self):
        assert "TODO_CERTIFIER_NAME" not in self._patched_opf()

"""K-R6-6 — ``marker_badge_style``: the in-page verse-badge form.

Round-6b device QA (2026-06-11, definitive): the ◈ note-mark glyph has NEVER
rendered on Kobo — any font, incl. Cardo; in-page badges displayed as bare
superscript numbers. So eink targets default to a no-glyph bordered CSS chip
with the count inside (border+radius+padding apply in the book view on every
engine); every other target keeps the shipped ◈+count form (Apple renders ◈
fine). Option-gated per the presentation-configurable doctrine
(``marker_badge_style: chip | glyph+count``), resolved through ONE resolver
consumed by the emitter, the API validator, and /customize (matrix==build).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


class TestResolver:
    def test_enum_exposes_both_values(self):
        from scripts.build_edition import MARKER_BADGE_STYLES

        assert MARKER_BADGE_STYLES == {"chip", "glyph+count"}

    def test_explicit_value_wins_on_any_target(self):
        from scripts.build_edition import resolve_marker_badge_style

        assert resolve_marker_badge_style({"marker_badge_style": "chip"}) == "chip"
        assert (
            resolve_marker_badge_style({"marker_badge_style": "glyph+count", "target_reader": "eink"}) == "glyph+count"
        )

    def test_eink_defaults_to_chip(self):
        from scripts.build_edition import resolve_marker_badge_style

        assert resolve_marker_badge_style({"target_reader": "eink"}) == "chip"

    def test_other_targets_default_to_glyph_count(self):
        from scripts.build_edition import resolve_marker_badge_style

        for t in ("", "everywhere", "tablet", "computer", "kindle"):
            assert resolve_marker_badge_style({"target_reader": t}) == "glyph+count", t

    def test_junk_value_falls_back_to_target_default(self):
        # Unknown/stale values resolve to the target default — a stale on-disk
        # value can never activate a variant (the TARGET_READERS convention).
        from scripts.build_edition import resolve_marker_badge_style

        assert resolve_marker_badge_style({"marker_badge_style": "sparkle", "target_reader": "eink"}) == "chip"
        assert resolve_marker_badge_style({"marker_badge_style": "sparkle"}) == "glyph+count"


class TestCssAppend:
    def test_chip_appends_the_chip_rule(self):
        from scripts.build_edition import apply_marker_badge_style

        out = apply_marker_badge_style("BASE", "chip")
        assert out.startswith("BASE") and "marker_badge_style=chip" in out

    def test_glyph_count_appends_nothing(self):
        from scripts.build_edition import apply_marker_badge_style

        assert apply_marker_badge_style("BASE", "glyph+count") == "BASE"


class TestEmitter:
    """``apply_badge_markers`` consults the resolver: chip drops the ◈ from the
    badge TEXT (count only — no glyph dependency); glyph+count is byte-identical
    to the shipped form."""

    def _badge_tree(self, tmp_path):
        book = config.get_book("gen")
        epub = REPO / "epub_working"
        tmp = tmp_path / "build"
        tmp.mkdir()
        gen1 = None
        for f in book["files"]:
            t = (epub / f).read_text(encoding="utf-8")
            (tmp / f).write_text(t, encoding="utf-8")
            if gen1 is None and 'id="v-gen-1-1"' in t:
                gen1 = f
        assert gen1, "gen 1 base file not found"
        return tmp, gen1

    def test_eink_edition_emits_count_only_badges(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp, fname = self._badge_tree(tmp_path)
        stats = apply_badge_markers(tmp, {"id": "x", "marker_style": "badge", "target_reader": "eink"})
        assert stats["badges_inserted"] > 0
        text = (tmp / fname).read_text(encoding="utf-8")
        sups = re.findall(r'<sup class="marker-badge">([^<]*)</sup>', text)
        assert sups, "badges expected in gen 1"
        for sup in sups:
            assert re.fullmatch(r"\d+", sup), f"eink badge must be count-only (no ◈): {sup!r}"

    def test_default_edition_keeps_the_glyph(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp, fname = self._badge_tree(tmp_path)
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        text = (tmp / fname).read_text(encoding="utf-8")
        sups = re.findall(r'<sup class="marker-badge">([^<]*)</sup>', text)
        assert sups and all(s.startswith("◈") for s in sups), "non-eink badges keep ◈+count"


class TestValidator:
    def test_accepts_chip_and_persists(self):
        from scripts.api.editions import api_save_edition_meta

        edyaml = REPO / "content" / "editions.yaml"
        backup = edyaml.read_bytes()
        try:
            res = api_save_edition_meta("catholic-study", {"marker_badge_style": "chip"})
            assert "error" not in res, res
            config.load_editions.cache_clear()
            assert config.editions_by_id()["catholic-study"].get("marker_badge_style") == "chip"
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()

    def test_rejects_unknown_value(self):
        from scripts.api.editions import api_save_edition_meta

        res = api_save_edition_meta("catholic-study", {"marker_badge_style": "bogus"})
        assert "error" in res and "marker_badge_style" in res["error"]


class TestLoaderAndUI:
    def test_api_customize_data_surfaces_the_resolved_value(self):
        from scripts.web import api_customize_data

        eds = {e["id"]: e for e in api_customize_data()["editions"]}
        # catholic-study pins neither marker_badge_style nor an eink target →
        # the surfaced value is the resolved default for its target.
        assert eds["catholic-study"].get("marker_badge_style") == "glyph+count"

    def test_customize_template_has_the_select(self):
        src = (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        assert 'data-field="marker_badge_style"' in src
        assert '<option value="chip"' in src and '<option value="glyph+count"' in src

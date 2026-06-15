"""K-R6-6 — ``marker_badge_style``: the in-page verse-badge form.

Round-6b device QA (2026-06-11, definitive): the ◈ note-mark glyph has NEVER
rendered on Kobo — any font, incl. Cardo; in-page badges displayed as bare
superscript numbers. So eink targets default to a no-glyph bordered CSS chip
with the count inside (border+radius+padding apply in the book view on every
engine); every other target keeps the shipped ◈+count form (Apple renders ◈
fine). Option-gated per the presentation-configurable doctrine
(``marker_badge_style: chip | glyph+count | dot | dagger | asterisk | lozenge``),
resolved through ONE resolver
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

        assert MARKER_BADGE_STYLES == {
            "chip",
            "glyph+count",
            "dot",
            "dagger",
            "dagger+count",
            "asterisk",
            "lozenge",
            "lozenge+count",
        }

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
    def test_chip_family_appends_the_chip_rule(self):
        from scripts.build_edition import apply_marker_badge_style

        for style in ("chip", "dot", "dagger", "dagger+count", "asterisk", "lozenge", "lozenge+count"):
            out = apply_marker_badge_style("BASE", style)
            assert out.startswith("BASE") and ".marker-badge" in out, style

    def test_glyph_count_appends_nothing(self):
        from scripts.build_edition import apply_marker_badge_style

        assert apply_marker_badge_style("BASE", "glyph+count") == "BASE"


class TestBadgeText:
    def test_symbol_styles_drop_the_count(self):
        from scripts.build_edition import format_marker_badge_text

        base = {"id": "x", "marker_style": "badge", "target_reader": "eink"}
        assert format_marker_badge_text({**base, "marker_badge_style": "dot"}, 4) == "•"
        assert format_marker_badge_text({**base, "marker_badge_style": "dagger"}, 4) == "†"
        assert format_marker_badge_text({**base, "marker_badge_style": "asterisk"}, 4) == "*"
        assert format_marker_badge_text({**base, "marker_badge_style": "lozenge"}, 4) == "◇"
        assert format_marker_badge_text({**base, "marker_badge_style": "dagger+count"}, 4) == "†4"
        assert format_marker_badge_text({**base, "marker_badge_style": "lozenge+count"}, 7) == "◇7"

    def test_chip_keeps_count_glyph_count_keeps_diamond(self):
        from scripts.build_edition import format_marker_badge_text

        assert format_marker_badge_text({"marker_badge_style": "chip", "target_reader": "eink"}, 3) == "3"
        assert format_marker_badge_text({"marker_badge_style": "glyph+count"}, 3) == "◈3"


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
            assert re.fullmatch(r"\d+", sup), f"eink chip badge must be count-only (no ◈): {sup!r}"
        assert 'class="badge-trail"' in text

    def test_terminal_badge_gets_paragraph_seam_before_next_vn_link(self, tmp_path):
        from scripts.build_edition import apply_badge_markers, apply_eink_verse_line_breaks

        tmp, fname = self._badge_tree(tmp_path)
        edition = {
            "id": "x",
            "marker_style": "badge",
            "target_reader": "eink",
            "reader_eink_study_layout": "inline",
            "reader_eink_verse_lines": True,
        }
        apply_badge_markers(tmp, edition)
        apply_eink_verse_line_breaks(tmp, edition)
        text = (tmp / fname).read_text(encoding="utf-8")
        m = re.search(
            r'vbadge-gen-1-12-s1[^>]*>.*?</a>.*?</p>\s*<p class="verse-p">\s*<a class="vn-link" id="v-gen-1-13"',
            text,
            re.DOTALL,
        )
        assert m, "terminal gen 1:12 study badge must close <p> before next verse vn-link"

    def test_eink_inline_verse_notes_follow_badge_cluster(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp, fname = self._badge_tree(tmp_path)
        apply_badge_markers(
            tmp,
            {"id": "x", "marker_style": "badge", "target_reader": "eink", "reader_eink_study_layout": "popup"},
        )
        text = (tmp / fname).read_text(encoding="utf-8")
        m = re.search(
            r'(vbadge-gen-1-12-s1[^>]*>.*?</a>.*?<aside class="verse-notes(?: verse-notes--eink-anchor)?" id="vnotes-gen-1-12-s1")',
            text,
            re.DOTALL,
        )
        assert m, "eink study aside must sit inline immediately after its badge"
        assert "verse-notes--eink-anchor" in text, "popup mode hides inline anchors"
        assert text.count('id="vnotes-gen-1-12-s1"') == 1
        aside_close = text.find("</aside>", m.end())
        assert aside_close != -1
        tail = text[aside_close : aside_close + 200]
        assert 'id="v-gen-1-13"' in tail, "next verse vn-link must follow the inline aside (Kobo scan chain)"
        bm = text.index('id="vbadge-gen-1-12-s1"')
        am = text.index('id="vnotes-gen-1-12-s1"')
        vm = text.index('id="v-gen-1-13"')
        assert bm < am < vm, "document order: badge → aside → next vn-link"

    def test_dot_style_emits_symbol_only_badges(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp, fname = self._badge_tree(tmp_path)
        apply_badge_markers(
            tmp,
            {"id": "x", "marker_style": "badge", "target_reader": "eink", "marker_badge_style": "dot"},
        )
        text = (tmp / fname).read_text(encoding="utf-8")
        sups = re.findall(r'<sup class="marker-badge">([^<]*)</sup>', text)
        assert sups and all(s == "•" for s in sups)

    def test_default_edition_keeps_the_glyph(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp, fname = self._badge_tree(tmp_path)
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        text = (tmp / fname).read_text(encoding="utf-8")
        sups = re.findall(r'<sup class="marker-badge">([^<]*)</sup>', text)
        assert sups and all(s.startswith("◈") for s in sups), "non-eink badges keep ◈+count"


class TestReaderEinkStudyLayout:
    def test_eink_defaults_to_backmatter(self):
        from scripts.build_edition import resolve_reader_eink_study_layout

        assert resolve_reader_eink_study_layout({"target_reader": "eink"}) == "backmatter"
        assert resolve_reader_eink_study_layout({}) == "popup"

    def test_legacy_inline_flag_maps_to_inline(self):
        from scripts.build_edition import resolve_reader_eink_study_layout

        assert resolve_reader_eink_study_layout({"target_reader": "eink", "reader_eink_study_inline": True}) == "inline"

    def test_backmatter_collects_entries_not_inline(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp, fname = TestEmitter()._badge_tree(tmp_path)
        stats = apply_badge_markers(
            tmp,
            {"id": "x", "marker_style": "badge", "target_reader": "eink", "reader_eink_study_layout": "backmatter"},
        )
        text = (tmp / fname).read_text(encoding="utf-8")
        assert stats["study_backmatter_entries"], "entries collected for glossary"
        assert 'id="vnotes-gen-1-12-s1"' not in text, "asides must not stay in prose"
        assert "study-return" in stats["study_backmatter_entries"][0][2]

    def test_backmatter_emits_colored_category_badges(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp, fname = TestEmitter()._badge_tree(tmp_path)
        edition = {
            "id": "x",
            "marker_style": "badge",
            "target_reader": "eink",
            "reader_eink_study_layout": "backmatter",
            "note_group_by_category": True,
        }
        stats = apply_badge_markers(tmp, edition)
        text = (tmp / fname).read_text(encoding="utf-8")
        assert stats["study_category_badges"] >= 1
        assert 'class="verse-notes-badge badge-cat-' in text
        badge_tags = re.findall(r'<a class="verse-notes-badge[^"]*"[^>]*>', text)
        assert badge_tags and 'epub:type="noteref"' not in badge_tags[0]
        glossary = next(row[2] for row in stats["study_backmatter_entries"] if "vnotes-gen-1-1-" in row[2])
        assert re.search(r'id="vnotes-gen-1-1-[a-z]+"', glossary)
        assert "study-glossary-entry" in glossary
        hrefs = re.findall(r'href="#(vnotes-gen-1-1-[a-z]+)"', text)
        assert hrefs, "category badges must target anchored glossary sections"

    def test_study_inline_drops_anchor_hide_class(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp, fname = TestEmitter()._badge_tree(tmp_path)
        apply_badge_markers(
            tmp,
            {"id": "x", "marker_style": "badge", "target_reader": "eink", "reader_eink_study_layout": "inline"},
        )
        text = (tmp / fname).read_text(encoding="utf-8")
        assert "verse-notes--eink-anchor" not in text
        assert 'class="verse-notes" id="vnotes-' in text

    def test_inject_study_backmatter_writes_file(self, tmp_path):
        from scripts.build_edition import apply_badge_markers
        from scripts.matter_pages import EINK_STUDY_BACKMATTER_FILE, inject_eink_study_backmatter

        tmp, _fname = TestEmitter()._badge_tree(tmp_path)
        (tmp / "content.opf").write_text("<package><manifest></manifest><spine></spine></package>", encoding="utf-8")
        (tmp / "nav.xhtml").write_text("<html><body><ol></ol></body></html>", encoding="utf-8")
        stats = apply_badge_markers(
            tmp,
            {"id": "x", "marker_style": "badge", "target_reader": "eink", "reader_eink_study_layout": "backmatter"},
        )
        out = inject_eink_study_backmatter(tmp, {"id": "x", "title": "Test"}, stats["study_backmatter_entries"])
        assert out["entries_written"] > 0
        assert (tmp / EINK_STUDY_BACKMATTER_FILE).is_file()
        assert "Study Notes" in (tmp / EINK_STUDY_BACKMATTER_FILE).read_text(encoding="utf-8")

    def test_eink_reader_css_appends_on_eink_only(self):
        from scripts.build_edition import apply_eink_reader_css

        out = apply_eink_reader_css("BASE", {"target_reader": "eink"})
        assert "study-glossary-entry" in out and "eyebrow-book" in out
        assert apply_eink_reader_css("BASE", {"target_reader": "tablet"}) == "BASE"

    def test_customize_wiring(self):
        src = (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        assert 'data-field="reader_eink_study_layout"' in src

    def test_wizard_surfaces_study_layout_pick(self):
        from scripts.templates.wizard import WIZARD_HTML

        assert 'id="w-eink-study-layout"' in WIZARD_HTML
        assert "reader_eink_study_layout:" in WIZARD_HTML


class TestReaderEinkVerseLines:
    def test_resolver_defaults_off(self):
        from scripts.build_edition import resolve_reader_eink_verse_lines

        assert resolve_reader_eink_verse_lines({}) is False
        assert resolve_reader_eink_verse_lines({"target_reader": "eink"}) is False
        assert resolve_reader_eink_verse_lines({"target_reader": "tablet", "reader_eink_verse_lines": True}) is False

    def test_resolver_on_when_eink_and_flag(self):
        from scripts.build_edition import resolve_reader_eink_verse_lines

        assert resolve_reader_eink_verse_lines({"target_reader": "eink", "reader_eink_verse_lines": True}) is True

    def test_apply_is_noop_when_flag_off(self, tmp_path):
        from scripts.build_edition import apply_eink_verse_line_breaks

        tmp, fname = TestEmitter()._badge_tree(tmp_path)
        before = (tmp / fname).read_text(encoding="utf-8")
        n = apply_eink_verse_line_breaks(tmp, {"id": "x", "target_reader": "eink"})
        after = (tmp / fname).read_text(encoding="utf-8")
        assert n == 0
        assert after == before

    def test_customize_wiring(self):
        from scripts.api.editions import EDITABLE_BOOL_FIELDS

        src = (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        assert 'data-field="reader_eink_verse_lines"' in src
        assert "wireEinkOnlyRows" in src
        assert "wireBadgeStyleRow" in src
        assert "reader_eink_verse_lines" in EDITABLE_BOOL_FIELDS

    def test_wizard_surfaces_badge_and_verse_line_picks(self):
        from scripts.templates.wizard import WIZARD_HTML

        assert 'id="w-badge-style"' in WIZARD_HTML
        assert 'id="w-eink-verse-lines"' in WIZARD_HTML
        assert "marker_badge_style:" in WIZARD_HTML
        assert "reader_eink_verse_lines:" in WIZARD_HTML


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
        assert "Study-note badge style" in src
        assert '<option value="chip"' in src and '<option value="glyph+count"' in src
        assert '<option value="dagger+count"' in src

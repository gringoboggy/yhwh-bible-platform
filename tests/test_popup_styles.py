"""§4.2 `verse_popup_style` (+ §4.4 `note_popup_style`) — per-edition popup
layout settings (Wave 3, CSS-only — no base re-bake).

Spec: docs/superpowers/specs/2026-05-24-epub-presentation-polish-design.md §4.2/§4.4 + §7.
Each is wired exactly like `title_page_style` (const + api_save_edition_meta enum
validation + api_customize_data default + /customize <select>), and applied at
build time by appending the chosen variant's CSS to the edition stylesheet —
"most settings switch a container/body class; the data is unchanged" (spec §7).
"""

from __future__ import annotations

import sys
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


class TestVersePopupStyleConst:
    def test_enum_exposes_cards_and_stack(self):
        from scripts.build_edition import VERSE_POPUP_STYLES

        assert set(VERSE_POPUP_STYLES) == {"cards", "stack"}


class TestVersePopupStyleValidator:
    def test_rejects_unknown_value(self):
        from scripts.api.editions import api_save_edition_meta

        res = api_save_edition_meta("catholic-study", {"verse_popup_style": "grid"})
        assert "error" in res and "verse_popup_style" in res["error"]

    def test_accepts_and_persists_stack(self):
        from scripts.api.editions import api_save_edition_meta

        edyaml = REPO / "content" / "editions.yaml"
        backup = edyaml.read_bytes()
        try:
            res = api_save_edition_meta("catholic-study", {"verse_popup_style": "stack"})
            assert "error" not in res, res
            config.load_editions.cache_clear()
            assert config.editions_by_id()["catholic-study"].get("verse_popup_style") == "stack"
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()


class TestVersePopupStyleLoader:
    def test_api_customize_data_defaults_to_cards(self):
        from scripts.web import api_customize_data

        eds = {e["id"]: e for e in api_customize_data()["editions"]}
        assert eds["catholic-study"].get("verse_popup_style") == "cards"


class TestVersePopupStyleUI:
    def test_customize_template_has_the_select(self):
        src = (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        assert 'data-field="verse_popup_style"' in src


class TestApplyVersePopupStyle:
    """Build-time application: 'cards' (default) appends tinted-card-with-spine
    CSS to the edition stylesheet; 'stack' is the flat base layout (no append).
    Mirrors the theme-override mechanism — no base re-bake."""

    def test_cards_appends_card_css(self):
        from scripts.build_edition import apply_verse_popup_style

        out = apply_verse_popup_style("BASE_CSS", "cards")
        assert out.startswith("BASE_CSS")
        assert ".vnote-hebrew" in out and ".vnote-greek" in out
        assert "border-left" in out  # the colored spine

    def test_stack_is_the_flat_base_unchanged(self):
        from scripts.build_edition import apply_verse_popup_style

        assert apply_verse_popup_style("BASE_CSS", "stack") == "BASE_CSS"

    def test_unset_defaults_to_cards(self):
        from scripts.build_edition import apply_verse_popup_style

        assert apply_verse_popup_style("BASE_CSS", "") != "BASE_CSS"


# ----------------------------------------------------------------------
# §4.4 note_popup_style — note/aside popup layout (chip default / pills).
# Same CSS-only wiring as verse_popup_style; targets the EXISTING baked
# classes (.note-label for the chip; in-note `a:not(.note-back)` for the
# pills) so no base re-bake is needed. The §4.4 symbol-into-note move +
# stray-‖ removal are base-HTML changes tracked separately (symbols-into-
# notes Wave-3 task); this setting is the layout treatment only.
# ----------------------------------------------------------------------


class TestNotePopupStyleConst:
    def test_enum_exposes_chip_and_pills(self):
        from scripts.build_edition import NOTE_POPUP_STYLES

        assert set(NOTE_POPUP_STYLES) == {"chip", "pills"}


class TestNotePopupStyleValidator:
    def test_rejects_unknown_value(self):
        from scripts.api.editions import api_save_edition_meta

        res = api_save_edition_meta("catholic-study", {"note_popup_style": "boxes"})
        assert "error" in res and "note_popup_style" in res["error"]

    def test_accepts_and_persists_pills(self):
        from scripts.api.editions import api_save_edition_meta

        edyaml = REPO / "content" / "editions.yaml"
        backup = edyaml.read_bytes()
        try:
            res = api_save_edition_meta("catholic-study", {"note_popup_style": "pills"})
            assert "error" not in res, res
            config.load_editions.cache_clear()
            assert config.editions_by_id()["catholic-study"].get("note_popup_style") == "pills"
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()


class TestNotePopupStyleLoader:
    def test_api_customize_data_defaults_to_chip(self):
        from scripts.web import api_customize_data

        eds = {e["id"]: e for e in api_customize_data()["editions"]}
        assert eds["catholic-study"].get("note_popup_style") == "chip"


class TestNotePopupStyleUI:
    def test_customize_template_has_the_select(self):
        src = (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        assert 'data-field="note_popup_style"' in src


class TestApplyNotePopupStyle:
    """Build-time application: 'chip' (default) appends a tinted label-chip rule
    (targets .note-label); 'pills' appends a pill rule for in-note cross-refs
    (targets `.note a:not(.note-back)`). Both CSS-only — no base re-bake."""

    def test_chip_appends_label_chip_css(self):
        from scripts.build_edition import apply_note_popup_style

        out = apply_note_popup_style("BASE_CSS", "chip")
        assert out.startswith("BASE_CSS")
        assert ".note-label" in out
        assert "border-radius" in out  # the chip shape

    def test_pills_appends_pill_css(self):
        from scripts.build_edition import apply_note_popup_style

        out = apply_note_popup_style("BASE_CSS", "pills")
        assert out.startswith("BASE_CSS")
        assert "a:not(.note-back)" in out  # in-note cross-references only
        assert "border-radius" in out  # the pill shape

    def test_unset_defaults_to_chip(self):
        from scripts.build_edition import apply_note_popup_style

        out = apply_note_popup_style("BASE_CSS", "")
        assert out != "BASE_CSS"
        assert ".note-label" in out  # chip targets the label

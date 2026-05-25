"""`marker_style` edition field (Wave 3 §4.1) — the forward-compat enum.

Numbering is BASE-WIDE: the re-bake (`resync_marker_glyphs`) numbers the shared
base, so `marker_style` is currently a declarative per-edition setting that
records the builder's choice and defaults to `numbers`. `badge` is DEFERRED
(spec §4.1 — it needs a per-verse note container whose injection point is TBD),
so the validator accepts only `numbers` until badge lands. Wired like the other
enum settings: const + api_save_edition_meta validation + api_customize_data
default + /customize <select>.
"""

from __future__ import annotations

import sys
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


class TestMarkerStyleConst:
    def test_enum_exposes_numbers(self):
        from scripts.build_edition import MARKER_STYLES

        assert "numbers" in MARKER_STYLES

    def test_badge_is_deferred_not_yet_valid(self):
        from scripts.build_edition import MARKER_STYLES

        assert "badge" not in MARKER_STYLES


class TestMarkerStyleValidator:
    def test_rejects_deferred_badge(self):
        from scripts.api.editions import api_save_edition_meta

        res = api_save_edition_meta("catholic-study", {"marker_style": "badge"})
        assert "error" in res and "marker_style" in res["error"]

    def test_accepts_and_persists_numbers(self):
        from scripts.api.editions import api_save_edition_meta

        edyaml = REPO / "content" / "editions.yaml"
        backup = edyaml.read_bytes()
        try:
            res = api_save_edition_meta("catholic-study", {"marker_style": "numbers"})
            assert "error" not in res, res
            config.load_editions.cache_clear()
            assert config.editions_by_id()["catholic-study"].get("marker_style") == "numbers"
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()


class TestMarkerStyleLoader:
    def test_api_customize_data_defaults_to_numbers(self):
        from scripts.web import api_customize_data

        eds = {e["id"]: e for e in api_customize_data()["editions"]}
        assert eds["catholic-study"].get("marker_style") == "numbers"


class TestMarkerStyleUI:
    def test_customize_template_has_the_select(self):
        src = (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        assert 'data-field="marker_style"' in src

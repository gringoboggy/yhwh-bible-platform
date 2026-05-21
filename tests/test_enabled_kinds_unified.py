"""Unified enabled-kinds resolver — pins the single source of truth.

"Which kinds ship in an edition" used to be computed in three places with
drifting gates: build_edition.compute_enabled_kinds had the phase gate but no
ai-notes gate; matrix._enabled_kinds_for_edition had the ai-notes gate but no
phase gate; config._kinds_in_edition had phase-only. The matrix therefore
over-counted vs. what actually builds. This pins the canonical
``config.enabled_kind_codes`` and the invariant that all three agree.
"""

from __future__ import annotations

import pytest

from scripts.core import config

# Synthetic kinds spanning every phase + the AI-drafted kind.
KINDS = [
    {"code": "word", "category": "lang", "phase": "legacy"},
    {"code": "comm-rabbinic", "category": "comm", "phase": "mvp"},
    {"code": "comm-modern-critical", "category": "comm", "phase": "phase2"},
    {"code": "modern-science", "category": "modern", "phase": "phase3"},
    {"code": "comm-ai", "category": "comm", "phase": "mvp"},
]


class TestEnabledKindCodes:
    def test_phase_gate_excludes_kinds_above_max_phase(self):
        ed = {
            "id": "e",
            "enabled_categories": ["lang", "comm", "modern"],
            "max_phase": "mvp",
        }
        out = config.enabled_kind_codes(ed, KINDS)
        assert "word" in out  # legacy always passes
        assert "comm-rabbinic" in out  # mvp <= mvp
        assert "comm-modern-critical" not in out  # phase2 > mvp
        assert "modern-science" not in out  # phase3 > mvp

    def test_phase3_edition_includes_everything_phasewise(self):
        ed = {
            "id": "e",
            "enabled_categories": ["lang", "comm", "modern"],
            "max_phase": "phase3",
            "enable_ai_notes": True,
        }
        out = config.enabled_kind_codes(ed, KINDS)
        assert {"word", "comm-rabbinic", "comm-modern-critical", "modern-science"} <= out

    def test_ai_kind_excluded_unless_opted_in(self):
        ed = {"id": "e", "enabled_categories": ["comm"], "max_phase": "phase3"}
        assert "comm-ai" not in config.enabled_kind_codes(ed, KINDS)

    def test_ai_kind_included_when_opted_in(self):
        ed = {
            "id": "e",
            "enabled_categories": ["comm"],
            "max_phase": "phase3",
            "enable_ai_notes": True,
        }
        assert "comm-ai" in config.enabled_kind_codes(ed, KINDS)

    def test_ai_kind_gated_even_if_explicitly_enabled(self):
        # Double opt-in: listing comm-ai in enabled_kinds is necessary but
        # not sufficient — enable_ai_notes must also be true.
        ed = {"id": "e", "enabled_kinds": ["comm-ai"], "max_phase": "phase3"}
        assert "comm-ai" not in config.enabled_kind_codes(ed, KINDS)

    def test_explicit_disable_wins(self):
        ed = {
            "id": "e",
            "enabled_categories": ["comm"],
            "disabled_kinds": ["comm-rabbinic"],
            "max_phase": "phase3",
        }
        assert "comm-rabbinic" not in config.enabled_kind_codes(ed, KINDS)

    def test_explicit_enable_adds_outside_category(self):
        ed = {
            "id": "e",
            "enabled_categories": [],
            "enabled_kinds": ["word"],
            "max_phase": "phase3",
        }
        out = config.enabled_kind_codes(ed, KINDS)
        assert "word" in out
        assert "comm-rabbinic" not in out  # category off + not explicitly enabled

    def test_unknown_max_phase_raises(self):
        ed = {"id": "e", "enabled_categories": ["lang"], "max_phase": "bogus"}
        with pytest.raises(ValueError):
            config.enabled_kind_codes(ed, KINDS)


class TestThreeResolversAgree:
    """The invariant the divergence violated: matrix / build / config agree
    on the enabled-kind set for every real edition."""

    def test_matrix_build_config_agree_for_every_edition(self):
        from scripts.build_edition import compute_enabled_kinds
        from scripts.core import matrix as matrix_mod

        kinds = config.load_kinds()
        editions = config.load_editions()
        for ed in editions:
            eid = ed["id"]
            via_matrix = set(matrix_mod._enabled_kinds_for_edition(ed, kinds))
            via_build = compute_enabled_kinds(ed, kinds)[0]
            via_config = {k["code"] for k in config._kinds_in_edition(eid)}
            assert via_matrix == via_build, f"matrix vs build mismatch for {eid}: {via_matrix ^ via_build}"
            assert via_matrix == via_config, f"matrix vs config mismatch for {eid}: {via_matrix ^ via_config}"

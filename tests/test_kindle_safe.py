"""Kindle target resolver tests (retained after dead-variant retirement, turn 86).

The old "kindle_safe variant" (turn-69 ①) implementation (apply_kindle_* fns,
_KINDLE_SAFE_CSS, etc. inside build_edition) was retired in favor of the single
production `kindle_post` path. These tests keep only the still-valid one-resolver
plumbing. Variant-specific apply tests were removed as part of consolidation.
See LANE_HANDOFF turn 86 and kindle_post.py.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class TestTargetReaderResolver:
    """The one resolver both matrix and build call (MATRIX_MAP finding #3)."""

    def test_target_readers_constant_has_five_values(self):
        from scripts.build_edition import TARGET_READERS

        assert TARGET_READERS == ("everywhere", "eink", "tablet", "computer", "kindle")

    def test_resolver_defaults_unset_to_everywhere(self):
        from scripts.build_edition import resolve_target_reader

        assert resolve_target_reader({}) == "everywhere"
        assert resolve_target_reader({"target_reader": ""}) == "everywhere"
        assert resolve_target_reader({"target_reader": "  "}) == "everywhere"

    def test_resolver_passes_valid_values_and_defuses_unknown(self):
        from scripts.build_edition import resolve_target_reader

        assert resolve_target_reader({"target_reader": "kindle"}) == "kindle"
        assert resolve_target_reader({"target_reader": "eink"}) == "eink"
        # an unknown on-disk value must never activate a variant
        assert resolve_target_reader({"target_reader": "smartfridge"}) == "everywhere"

    def test_is_kindle_target(self):
        from scripts.build_edition import is_kindle_target

        assert is_kindle_target({"target_reader": "kindle"}) is True
        assert is_kindle_target({}) is False
        assert is_kindle_target({"target_reader": "eink"}) is False

    def test_api_validator_imports_the_shared_constant(self):
        # one-resolver rule: no inline enum copy in the API layer
        src = (REPO / "scripts" / "api" / "editions.py").read_text(encoding="utf-8")
        assert 'valid_targets = {"everywhere", "eink", "tablet", "computer"}' not in src
        assert "TARGET_READERS" in src

    # The remainder of the original file tested the retired --target-reader kindle
    # FAIL variant (apply_kindle_safe_css, apply_kindle_toc_rows, apply_kindle_unhide,
    # _KINDLE_SAFE_CSS etc.). Those tests + imports were deleted during dead-variant
    # consolidation (turn 86). Coverage for the real path lives in test_kindle_post.py
    # and test_kindle_safe_gate.py.

    def test_api_accepts_kindle(self):
        from scripts.api.editions import api_save_edition_meta
        from scripts.core import config

        yaml_path = REPO / "content" / "editions.yaml"
        original = yaml_path.read_bytes()
        try:
            r = api_save_edition_meta("catholic-study", {"target_reader": "kindle"})
            assert "error" not in r, r
            assert 'target_reader: "kindle"' in yaml_path.read_text(encoding="utf-8")
        finally:
            yaml_path.write_bytes(original)
            config.load_editions.cache_clear()

    def test_customize_surface_routes_through_the_resolver(self):
        src = (REPO / "scripts" / "web_editions.py").read_text(encoding="utf-8")
        assert 'e.get("target_reader", "everywhere")' not in src
        assert "resolve_target_reader" in src


# All subsequent classes (TestKindleWizardSurfaces, TestKindleSafeCss,
# TestKindleTocRows, TestOpfTargetStamp, TestKindleUnhideAttrs, etc.) tested
# the retired --target-reader kindle FAIL variant implementation. They were
# removed during dead-variant consolidation (turn 86, see LANE_HANDOFF).
# The resolver tests above are the only parts that remain relevant.
# Real Kindle behavior is now exercised via test_kindle_post.py + the gate
# in test_kindle_safe_gate.py + the matrix M4 column.

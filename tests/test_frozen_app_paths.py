"""Round-11 frozen-app content_root() HIGH — guard + routing pins.

In a frozen PyInstaller build the bundled content/ lives under the read-only
``_MEIPASS`` extraction dir, so ``content_root()`` MUST resolve to the writable
user-data dir (mirroring the ``_build_output_root()`` frozen guard) and every
content read/write must flow through the ``paths`` resolver — otherwise in-app
edits are lost on exit / blocked on macOS.

Lazy-imports inside each test so the file has no top-level project imports.
"""

from __future__ import annotations

import sys


class TestFrozenContentRootGuard:
    def test_content_root_frozen_returns_user_data_content(self, monkeypatch):
        # The frozen guard: with sys.frozen set and no env/test override, the
        # resolver must return user_data_root()/"content" — the EXACT dir the
        # first-run migration seeds — NOT user_data_root() itself (off-by-one =
        # an empty content root) and NOT the in-tree bundle. (round-13 Mac
        # cross-OS finding.)
        from scripts.core import paths

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.delenv("YHWH_CONTENT_ROOT", raising=False)
        paths.set_content_root_for_testing(None)
        paths.reset_content_root()
        try:
            assert paths.content_root() == paths.user_data_root() / "content"
        finally:
            paths.set_content_root_for_testing(None)
            paths.reset_content_root()

    def test_content_root_dev_unchanged(self, monkeypatch):
        # Dev mode (not frozen) must STILL resolve to the in-tree content/ — the
        # guard only changes frozen behavior, so dev builds stay byte-stable.
        from scripts.core import paths

        monkeypatch.setattr(sys, "frozen", False, raising=False)
        monkeypatch.delenv("YHWH_CONTENT_ROOT", raising=False)
        paths.set_content_root_for_testing(None)
        paths.reset_content_root()
        try:
            assert paths.content_root() == paths.repo_root() / "content"
        finally:
            paths.set_content_root_for_testing(None)
            paths.reset_content_root()


class TestContentSitesRouteThroughResolver:
    """A few representative read/write sites must honor content_root() (so a
    frozen build's user-data dir is used). Proven via set_content_root_for_testing
    — pre-routing these read/write the hardcoded in-tree dir and ignore it."""

    def test_note_save_routes_through_content_root(self, tmp_path, monkeypatch):
        from scripts.core import paths
        from scripts import web_helpers

        (tmp_path / "notes").mkdir()  # production: the first-run migration copies content/notes/ here
        paths.set_content_root_for_testing(tmp_path)
        try:
            web_helpers.write_book("zzz", [(1, 1, "", "", "word", "T", "L", "body", None)])
            assert (tmp_path / "notes" / "zzz.py").is_file(), "write_book must land under content_root()/notes"
        finally:
            paths.set_content_root_for_testing(None)

    def test_config_loaders_route_through_content_root(self, tmp_path, monkeypatch):
        # config's cached loaders must read from the ACTIVE content root.
        from scripts.core import config, paths

        # Seed a minimal kinds.yaml under the override root.
        (tmp_path / "kinds.yaml").write_text(
            "kinds:\n  - code: word\n    category: lang\n    label: Word\n", encoding="utf-8"
        )
        paths.set_content_root_for_testing(tmp_path)
        config.load_kinds.cache_clear()
        try:
            kinds = config.load_kinds()
            assert any(k.get("code") == "word" for k in kinds)
            assert len(kinds) == 1, "loader must read the override root, not the in-tree kinds.yaml"
        finally:
            paths.set_content_root_for_testing(None)
            config.load_kinds.cache_clear()


class TestNoOrphanedApiConstants:
    """round-13 #5: the frozen-app content_root() routing made several
    module-level path constants dead. A dead path constant invites the
    stale-monkeypatch leak class (a test patching a no-longer-read constant
    silently writes the REAL tree). These three api modules had a truly-unused
    ``REPO`` removed; pin it gone so it can't creep back. exports.py / preflight.py
    keep a LIVE ``REPO`` (genuine dev-server paths) and are intentionally excluded."""

    DEAD_REPO_FILES = ["scripts/api/customize.py", "scripts/api/editions.py", "scripts/api/sources.py"]

    def test_no_module_level_repo_constant(self):
        import ast
        from pathlib import Path

        repo = Path(__file__).resolve().parents[1]
        offenders = []
        for rel in self.DEAD_REPO_FILES:
            tree = ast.parse((repo / rel).read_text(encoding="utf-8"))
            for node in tree.body:  # module top-level only
                if isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == "REPO" for t in node.targets
                ):
                    offenders.append(f"{rel}:{node.lineno}")
        assert not offenders, f"dead module-level REPO constant reintroduced: {offenders}"

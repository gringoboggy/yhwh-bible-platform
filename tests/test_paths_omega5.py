"""ω.27 follow-on (2026-05-11) — ω.5 per-user-data location test
classes, split out of the monolithic ``tests/test_scripts.py``
into a topic file alongside the other ω.27 follow-on splits.

Twelfth topic extraction. The ω.5 arc separated dev-mode
(in-tree `content/`) from installed-binary mode (per-user
content directory under `user_data_dir`). Foundational for
the θ desktop-binary cluster:

- TestPathsRepoAndUserData      — repo_root() + user_data_root()
- TestPathsContentRootResolver  — content_root() routing logic
- TestPathsSubPathHelpers       — notes_dir(), exports_dir(), etc.
- TestPathsCacheBehavior        — lru_cache invalidation contract
- TestCoreModulesUsePathsResolver — pin that every core module
  goes through paths.* not raw paths
- TestMigrateToUserData         — first-run migration (in-tree
  content/ → user_data_dir on installed binary first launch)

Pairs with the θ.1 launcher's bootstrap_user_data flow (in
test_desktop_theta.py — ω.27 follow-on #8).

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


# ============================================================


class TestPathsRepoAndUserData:
    """Tests for the foundation resolvers: repo_root() and
    user_data_root(). These are platform-aware but stable; they
    don't depend on any cached state."""

    @classmethod
    def setup_class(cls):
        from scripts.core import paths as p

        cls.p = p

    def test_repo_root_is_parent_of_scripts_dir(self):
        rr = self.p.repo_root()
        assert (rr / "scripts").is_dir()
        assert (rr / "scripts" / "core" / "paths.py").is_file()

    def test_repo_root_is_stable_across_calls(self):
        # Pure function — same answer every call. Important because
        # this is the read-only resource path in installed builds.
        assert self.p.repo_root() == self.p.repo_root()

    def test_user_data_root_returns_path_under_home_or_appdata(
        self,
        monkeypatch,
    ):
        # Don't try to verify the *exact* dir per platform — this
        # test runs cross-platform and the env vars are real on each.
        # Just verify the result is a Path that ends with "YHWH" so
        # accidental refactors that point at the wrong root surface.
        udr = self.p.user_data_root()
        assert udr.name == "YHWH"

    def test_user_data_root_uses_appdata_on_windows(self, monkeypatch):
        monkeypatch.setattr(self.p.sys, "platform", "win32")
        monkeypatch.setenv("APPDATA", "C:\\synthetic\\AppData\\Roaming")
        udr = self.p.user_data_root()
        # Path normalisation: "\\" or "/" separators both fine
        assert udr.name == "YHWH"
        assert "AppData" in str(udr) or "synthetic" in str(udr)

    def test_user_data_root_uses_app_support_on_macos(self, monkeypatch):
        monkeypatch.setattr(self.p.sys, "platform", "darwin")
        udr = self.p.user_data_root()
        assert "Library" in str(udr)
        assert "Application Support" in str(udr)
        assert udr.name == "YHWH"

    def test_user_data_root_respects_xdg_data_home_on_linux(
        self,
        monkeypatch,
        tmp_path,
    ):
        monkeypatch.setattr(self.p.sys, "platform", "linux")
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        udr = self.p.user_data_root()
        assert udr == tmp_path / "xdg" / "YHWH"

    def test_user_data_root_falls_back_to_local_share_on_linux(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(self.p.sys, "platform", "linux")
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        udr = self.p.user_data_root()
        assert ".local" in str(udr) and "share" in str(udr)
        assert udr.name == "YHWH"


class TestPathsContentRootResolver:
    """Resolution order: testing override > env var > in-tree (dev)
    > user_data_root (installed)."""

    @classmethod
    def setup_class(cls):
        from scripts.core import paths as p

        cls.p = p

    def teardown_method(self):
        # Always clear test-state contamination — cached _content_root
        # would otherwise leak between tests.
        self.p.set_content_root_for_testing(None)

    def test_content_root_returns_in_tree_in_dev(self):
        # The repo's own content/editions.yaml exists, so dev mode
        # is detected automatically.
        cr = self.p.content_root()
        assert cr == self.p.repo_root() / "content"
        assert (cr / "editions.yaml").is_file()

    def test_set_content_root_for_testing_overrides_resolution(
        self,
        tmp_path,
    ):
        synthetic = tmp_path / "synthetic_content"
        synthetic.mkdir()
        self.p.set_content_root_for_testing(synthetic)
        assert self.p.content_root() == synthetic

    def test_set_content_root_for_testing_none_clears_override(
        self,
        tmp_path,
    ):
        self.p.set_content_root_for_testing(tmp_path / "nope")
        assert self.p.content_root() == tmp_path / "nope"
        self.p.set_content_root_for_testing(None)
        # Now back to dev resolution
        assert self.p.content_root() == self.p.repo_root() / "content"

    def test_env_var_overrides_in_tree(self, tmp_path, monkeypatch):
        synthetic = tmp_path / "env_content"
        synthetic.mkdir()
        monkeypatch.setenv("YHWH_CONTENT_ROOT", str(synthetic))
        # Env var only takes effect after cache reset
        self.p.reset_content_root()
        assert self.p.content_root() == synthetic

    def test_env_var_expands_user(self, tmp_path, monkeypatch):
        # ~ expansion is a usability nicety — verify it works.
        monkeypatch.setenv("YHWH_CONTENT_ROOT", "~/synthetic_path")
        self.p.reset_content_root()
        cr = self.p.content_root()
        assert "~" not in str(cr)
        assert cr.name == "synthetic_path"

    def test_in_tree_detection_requires_editions_yaml_marker(
        self,
        tmp_path,
        monkeypatch,
    ):
        # Mock repo_root() to point at a dir without editions.yaml;
        # in_tree detection should fail and fall back to user_data.
        monkeypatch.setattr(self.p, "repo_root", lambda: tmp_path)
        monkeypatch.delenv("YHWH_CONTENT_ROOT", raising=False)
        self.p.reset_content_root()
        cr = self.p.content_root()
        assert cr == self.p.user_data_root()


class TestPathsSubPathHelpers:
    """Sub-path helpers cascade from content_root() so a single
    override point updates every downstream consumer."""

    @classmethod
    def setup_class(cls):
        from scripts.core import paths as p

        cls.p = p

    def teardown_method(self):
        self.p.set_content_root_for_testing(None)

    def test_all_sub_paths_inherit_from_content_root(self, tmp_path):
        self.p.set_content_root_for_testing(tmp_path)
        assert self.p.notes_dir() == tmp_path / "notes"
        assert self.p.candidates_dir() == tmp_path / "candidates"
        assert self.p.sources_dir() == tmp_path / "sources"
        assert self.p.translations_dir() == tmp_path / "translations"
        assert self.p.covers_dir() == tmp_path / "covers"
        assert self.p.audio_dir() == tmp_path / "audio"

    def test_all_yaml_helpers_inherit_from_content_root(self, tmp_path):
        self.p.set_content_root_for_testing(tmp_path)
        assert self.p.editions_yaml() == tmp_path / "editions.yaml"
        assert self.p.books_yaml() == tmp_path / "books.yaml"
        assert self.p.kinds_yaml() == tmp_path / "kinds.yaml"
        assert self.p.categories_yaml() == tmp_path / "categories.yaml"
        assert self.p.themes_yaml() == tmp_path / "themes.yaml"
        assert self.p.canons_yaml() == tmp_path / "canons.yaml"
        assert self.p.traditions_yaml() == tmp_path / "traditions.yaml"

    def test_build_output_dirs_are_siblings_of_content_root(
        self,
        tmp_path,
    ):
        # exports/, builds/, epub_working/ live next to content/, not
        # inside it — preserves today's repo layout in dev and the
        # user-data layout for installed builds.
        synthetic_content = tmp_path / "content"
        synthetic_content.mkdir()
        self.p.set_content_root_for_testing(synthetic_content)
        assert self.p.exports_dir() == tmp_path / "exports"
        assert self.p.epub_working_dir() == tmp_path / "epub_working"
        assert self.p.builds_dir() == tmp_path / "builds"
        assert self.p.backups_dir() == tmp_path / "epub_working" / ".backups"

    def test_dev_mode_yaml_helpers_resolve_to_real_files(self):
        # Sanity: in dev mode (no override), the YAML helpers point
        # at files that actually exist on disk. Catches regressions
        # where a helper accidentally points at the wrong filename.
        assert self.p.editions_yaml().is_file()
        assert self.p.books_yaml().is_file()
        assert self.p.kinds_yaml().is_file()


class TestPathsCacheBehavior:
    """The _content_root_cached lru_cache speeds up repeated lookups
    but must invalidate cleanly when state changes mid-process."""

    @classmethod
    def setup_class(cls):
        from scripts.core import paths as p

        cls.p = p

    def teardown_method(self):
        self.p.set_content_root_for_testing(None)

    def test_reset_invalidates_cache(self, tmp_path, monkeypatch):
        # First call caches the dev-mode answer
        baseline = self.p.content_root()
        # Then change env, but cache means content_root() doesn't see it
        monkeypatch.setenv("YHWH_CONTENT_ROOT", str(tmp_path))
        # Without reset, content_root() returns the cached baseline
        assert self.p.content_root() == baseline
        # After reset, env var wins
        self.p.reset_content_root()
        assert self.p.content_root() == tmp_path

    def test_set_test_override_invalidates_cache(self, tmp_path):
        # First call caches dev-mode
        baseline = self.p.content_root()
        # Setting the override should immediately take effect
        self.p.set_content_root_for_testing(tmp_path)
        assert self.p.content_root() == tmp_path
        # Clearing should immediately fall back to dev resolution
        self.p.set_content_root_for_testing(None)
        assert self.p.content_root() == baseline


class TestCoreModulesUsePathsResolver:
    """ω.5 migration verification: scripts/core/ modules that import
    from paths.py must use the resolver, not hardcode their own
    ``Path(__file__).resolve().parent.parent / "content"``."""

    @classmethod
    def setup_class(cls):
        from scripts.core import paths as p

        cls.p = p

    def teardown_method(self):
        self.p.set_content_root_for_testing(None)
        # Bust per-module path-derived caches that may have been
        # populated against the override.
        from scripts.core import sources, translations, covers, traditions

        for mod in (sources, translations, covers, traditions):
            for name in (
                "strongs_hebrew",
                "strongs_greek",
                "tsk",
                "naves_topical",
                "kenyon_text",
                "anthropic_xref_client",
            ):
                fn = getattr(mod, name, None)
                if fn is not None and hasattr(fn, "cache_clear"):
                    fn.cache_clear()

    def test_sources_module_uses_paths_resolver(self, tmp_path):
        # Override content_root to a fresh temp dir, then
        # re-import the path constants the module exposes. Verifies
        # the module is actually composing through paths.py.
        synthetic = tmp_path / "alt_content"
        synthetic.mkdir()
        (synthetic / "sources").mkdir()
        self.p.set_content_root_for_testing(synthetic)

        # sources.SourceMissingError-derived classes resolve their
        # PATH lazily from the resolver, so a fresh instance must
        # look in the override.
        from scripts.core import sources

        assert sources._sources_dir() == synthetic / "sources"

    def test_translations_module_uses_paths_resolver(self, tmp_path):
        synthetic = tmp_path / "alt_content"
        synthetic.mkdir()
        self.p.set_content_root_for_testing(synthetic)

        from scripts.core import translations

        assert translations._translations_dir() == synthetic / "translations"

    def test_covers_module_uses_paths_resolver(self, tmp_path):
        synthetic = tmp_path / "alt_content"
        synthetic.mkdir()
        self.p.set_content_root_for_testing(synthetic)

        from scripts.core import covers

        assert covers._covers_dir() == synthetic / "covers"

    def test_traditions_module_uses_paths_resolver(self, tmp_path):
        synthetic = tmp_path / "alt_content"
        synthetic.mkdir()
        self.p.set_content_root_for_testing(synthetic)

        from scripts.core import traditions

        assert traditions._traditions_yaml_path() == synthetic / "traditions.yaml"

    def test_config_module_uses_paths_resolver(self, tmp_path):
        synthetic = tmp_path / "alt_content"
        synthetic.mkdir()
        self.p.set_content_root_for_testing(synthetic)

        from scripts.core import config

        assert config._books_yaml_path() == synthetic / "books.yaml"


class TestMigrateToUserData:
    """ω.5 migration helper: copy in-tree content/ → user_data_root/content."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.mod = importlib.import_module("scripts.migrate_to_user_data")

    def _seed_src(self, src: Path):
        """Build a minimal in-tree-style content/ fixture."""
        src.mkdir(parents=True)
        (src / "editions.yaml").write_text("editions: []\n", encoding="utf-8")
        (src / "books.yaml").write_text("books: []\n", encoding="utf-8")
        notes = src / "notes"
        notes.mkdir()
        (notes / "gen.py").write_text("NOTES = ()\n", encoding="utf-8")
        sources = src / "sources"
        sources.mkdir()
        (sources / "ATTRIBUTIONS.md").write_text("# attr\n", encoding="utf-8")

    def test_plan_migration_counts_files(self, tmp_path):
        src = tmp_path / "src"
        self._seed_src(src)
        plan = self.mod.plan_migration(src, tmp_path / "dst")
        assert plan["src_exists"]
        assert len(plan["files"]) == 4
        assert plan["total_bytes"] > 0

    def test_plan_migration_handles_missing_source(self, tmp_path):
        plan = self.mod.plan_migration(
            tmp_path / "nope",
            tmp_path / "dst",
        )
        assert plan["src_exists"] is False
        assert plan["files"] == []

    def test_perform_migration_copies_all_files(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        self._seed_src(src)
        result = self.mod.perform_migration(src, dst)
        assert result["copied"] == 4
        assert result["skipped"] == 0
        assert not result["errors"]
        assert (dst / "editions.yaml").is_file()
        assert (dst / "notes" / "gen.py").is_file()
        assert (dst / "sources" / "ATTRIBUTIONS.md").is_file()

    def test_perform_migration_idempotent_skips_existing(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        self._seed_src(src)
        first = self.mod.perform_migration(src, dst)
        assert first["copied"] == 4
        # Second run: everything skipped
        second = self.mod.perform_migration(src, dst)
        assert second["copied"] == 0
        assert second["skipped"] == 4

    def test_perform_migration_force_overwrites(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        self._seed_src(src)
        self.mod.perform_migration(src, dst)
        # Modify destination, re-run with force, verify overwrite
        (dst / "editions.yaml").write_text("# stale\n", encoding="utf-8")
        result = self.mod.perform_migration(src, dst, force=True)
        assert result["copied"] == 4
        assert (dst / "editions.yaml").read_text(encoding="utf-8") == "editions: []\n"

    def test_main_dry_run_writes_nothing(self, tmp_path, monkeypatch, capsys):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        self._seed_src(src)
        monkeypatch.setattr(self.mod, "_src_content", lambda: src)
        monkeypatch.setattr(self.mod, "_dst_content", lambda: dst)
        rc = self.mod.main(["--dry-run"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "dry-run" in out
        assert not dst.exists()

    def test_main_already_migrated_short_circuits(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        self._seed_src(src)
        # Pre-create destination with the editions.yaml marker
        dst.mkdir()
        (dst / "editions.yaml").write_text("editions: []\n", encoding="utf-8")
        monkeypatch.setattr(self.mod, "_src_content", lambda: src)
        monkeypatch.setattr(self.mod, "_dst_content", lambda: dst)
        rc = self.mod.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Already migrated" in out

    def test_main_refuses_when_source_missing(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        monkeypatch.setattr(self.mod, "_src_content", lambda: tmp_path / "nope")
        monkeypatch.setattr(self.mod, "_dst_content", lambda: tmp_path / "dst")
        rc = self.mod.main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "REFUSING" in out

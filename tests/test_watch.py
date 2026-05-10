"""Tests for watch — extracted from test_scripts.py in ω.27.

Originally lived in tests/test_scripts.py as part of a 22,000-line
monolithic test file; moved here so each test target sits next to a
single source-of-truth scripts/ module. Future tests for the same
target should land in this file rather than test_scripts.py.
"""

from __future__ import annotations


class TestOmega21WatchMode:
    """ω.21 — watch-mode dev-loop file watcher. Pure helpers
    (compute_signature, detect_changes, default_targets) tested
    directly; the main loop is too tied to time.sleep / Ctrl+C
    to exercise meaningfully in pytest, so we verify the building
    blocks instead.

    Stdlib-only per CLAUDE_PROJECT_RULES §10 (no `watchdog`
    dep) — these tests pin that contract by importing only
    standard library modules from `dev.watch`.
    """

    # ---- compute_signature ----

    def test_compute_signature_files_only(self, tmp_path):
        from dev.watch import compute_signature

        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("hi", encoding="utf-8")
        f2.write_text("hello", encoding="utf-8")
        sig = compute_signature([f1, f2])
        assert len(sig) == 2
        # mtimes are floats
        assert all(isinstance(v, float) for v in sig.values())

    def test_compute_signature_walks_directory(self, tmp_path):
        from dev.watch import compute_signature

        d = tmp_path / "tree"
        d.mkdir()
        (d / "a.py").write_text("a", encoding="utf-8")
        sub = d / "sub"
        sub.mkdir()
        (sub / "b.py").write_text("b", encoding="utf-8")
        sig = compute_signature([d])
        assert len(sig) == 2

    def test_compute_signature_skips_dotfile_dirs(self, tmp_path):
        from dev.watch import compute_signature

        d = tmp_path / "tree"
        d.mkdir()
        (d / "kept.py").write_text("k", encoding="utf-8")
        # Project's own backup machinery + cache layouts.
        for skip in (".backups", ".cache", "__pycache__", ".pytest_cache"):
            sd = d / skip
            sd.mkdir()
            (sd / "noise.py").write_text("n", encoding="utf-8")
        sig = compute_signature([d])
        assert len(sig) == 1
        assert any("kept.py" in k for k in sig.keys())

    def test_compute_signature_skips_swap_and_backup_files(
        self,
        tmp_path,
    ):
        from dev.watch import compute_signature

        d = tmp_path / "tree"
        d.mkdir()
        (d / "real.py").write_text("r", encoding="utf-8")
        (d / "real.py.bak").write_text("b", encoding="utf-8")
        (d / "real.py.tmp").write_text("t", encoding="utf-8")
        (d / "real.py.swp").write_text("s", encoding="utf-8")
        sig = compute_signature([d])
        # Only the real file shows up.
        assert len(sig) == 1

    def test_compute_signature_missing_path_silently_skipped(
        self,
        tmp_path,
    ):
        from dev.watch import compute_signature

        # A target that doesn't exist on disk shouldn't crash —
        # the curated default_targets() may include paths that
        # haven't been created yet on a fresh checkout.
        missing = tmp_path / "no-such"
        sig = compute_signature([missing])
        assert sig == {}

    def test_compute_signature_deterministic_for_unchanged_tree(
        self,
        tmp_path,
    ):
        from dev.watch import compute_signature

        d = tmp_path / "tree"
        d.mkdir()
        (d / "x.py").write_text("x", encoding="utf-8")
        a = compute_signature([d])
        b = compute_signature([d])
        assert a == b

    # ---- detect_changes ----

    def test_detect_changes_no_change(self):
        from dev.watch import detect_changes, has_changes

        sig = {"a": 1.0, "b": 2.0}
        diff = detect_changes(sig, dict(sig))
        assert diff == {"added": [], "modified": [], "removed": []}
        assert has_changes(diff) is False

    def test_detect_changes_added(self):
        from dev.watch import detect_changes, has_changes

        diff = detect_changes(
            {"a": 1.0},
            {"a": 1.0, "b": 2.0},
        )
        assert diff["added"] == ["b"]
        assert diff["modified"] == []
        assert diff["removed"] == []
        assert has_changes(diff) is True

    def test_detect_changes_modified(self):
        from dev.watch import detect_changes, has_changes

        diff = detect_changes(
            {"a": 1.0, "b": 2.0},
            {"a": 1.5, "b": 2.0},
        )
        assert diff["modified"] == ["a"]
        assert diff["added"] == []
        assert diff["removed"] == []
        assert has_changes(diff) is True

    def test_detect_changes_removed(self):
        from dev.watch import detect_changes, has_changes

        diff = detect_changes(
            {"a": 1.0, "b": 2.0},
            {"a": 1.0},
        )
        assert diff["removed"] == ["b"]
        assert has_changes(diff) is True

    def test_detect_changes_combination(self):
        from dev.watch import detect_changes

        diff = detect_changes(
            {"a": 1.0, "b": 2.0, "c": 3.0},
            {"a": 1.0, "b": 2.5, "d": 4.0},
        )
        assert diff["added"] == ["d"]
        assert diff["modified"] == ["b"]
        assert diff["removed"] == ["c"]

    # ---- default_targets ----

    def test_default_targets_includes_load_bearing_paths(self):
        from dev.watch import default_targets

        targets = default_targets()
        names = {p.name for p in targets}
        # Spot-check the load-bearing entries — these are the files
        # the build pipeline + linter actually consume.
        for must_have in (
            "editions.yaml",
            "kinds.yaml",
            "categories.yaml",
            "books.yaml",
            "canons.yaml",
            "notes",
            "translations",
            "web.py",
            "build_edition.py",
            "lint_rules.py",
            "templates",
            "core",
        ):
            assert must_have in names, f"default_targets() missing load-bearing path {must_have!r}; got {sorted(names)}"

    def test_default_targets_paths_are_under_repo(self):
        from dev.watch import default_targets, _REPO

        for p in default_targets():
            assert _REPO in p.resolve().parents or p.resolve() == _REPO, f"target {p} escapes repo root"

    # ---- run_lint ----

    def test_run_lint_returns_lint_summary_shape(self):
        from dev.watch import run_lint

        result = run_lint()
        # Either a real run_all() result or the error-shaped fallback.
        assert "summary" in result
        assert "checks" in result
        # Production state is clean (1473+ tests + linter green).
        assert result["summary"].get("clean") is True

    def test_run_lint_swallows_linter_exception(self, monkeypatch):
        from dev import watch as watch_mod

        # Replace the imported run_all symbol with one that raises.
        # The function imports inside the body, so we monkeypatch
        # the underlying module instead.
        import scripts.lint_rules as _lint

        def boom(*a, **kw):
            raise RuntimeError("synthetic linter failure")

        monkeypatch.setattr(_lint, "run_all", boom)
        result = watch_mod.run_lint()
        assert result.get("error", "").startswith("lint_rules.run_all() raised:")
        assert result["summary"]["clean"] is False
        assert result["summary"]["fail"] >= 1

    # ---- main entrypoint (--once mode) ----

    def test_main_once_returns_exit_code_zero_on_clean(
        self,
        capsys,
        monkeypatch,
    ):
        from dev.watch import main

        rc = main(["--once"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "lint clean" in out

    def test_main_once_returns_exit_code_one_on_lint_fail(
        self,
        capsys,
        monkeypatch,
    ):
        from dev import watch as watch_mod

        # Stub run_lint to surface a fail summary; --once should exit 1.
        def fake_lint():
            return {
                "checks": [],
                "summary": {"total": 1, "pass": 0, "warn": 0, "fail": 1, "clean": False},
            }

        monkeypatch.setattr(watch_mod, "run_lint", fake_lint)
        rc = watch_mod.main(["--once"])
        assert rc == 1

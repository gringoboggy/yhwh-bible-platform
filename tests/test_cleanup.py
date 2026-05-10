"""Tests for cleanup — extracted from test_scripts.py in ω.27.

Originally lived in tests/test_scripts.py as part of a 22,000-line
monolithic test file; moved here so each test target sits next to a
single source-of-truth scripts/ module. Future tests for the same
target should land in this file rather than test_scripts.py.
"""

from __future__ import annotations


class TestOmega28BackupRetention:
    """ω.28 — per-pattern backup retention policy. Today
    `cleanup.py` keeps 5 revisions per stem uniformly; ω.28 makes
    that configurable via `content/.backup_retention.yaml`.
    Defaults preserve current behavior so the absence of the file
    is a no-op shift."""

    @staticmethod
    def _make_backup_files(
        backups_dir,
        stem,
        count,
        *,
        base_mtime=None,
    ):
        """Create `count` synthetic backup files for one stem with
        spaced mtimes (oldest first). Returns the list of paths,
        newest last.

        Format matches `notes_io.ensure_backup`'s on-disk shape:
        ``<base>.<ISO_TS>.<ext>.bak`` (timestamp goes BETWEEN
        the base name and the extension). `stem_of` recovers
        ``<base>.<ext>`` by stripping the `.bak` suffix and the
        timestamp segment via regex.
        """
        import os as _os

        backups_dir.mkdir(parents=True, exist_ok=True)
        # Split "gen.py" → ("gen", "py")
        if "." in stem:
            base, _, ext = stem.rpartition(".")
        else:
            base, ext = stem, "bak"
        files = []
        if base_mtime is None:
            import time as _t

            base_mtime = _t.time()
        for i in range(count):
            # 8-digit date + T + 6-digit time + Z, matching the
            # format `notes_io.ensure_backup` produces. Each
            # iteration bumps the day so the timestamps + mtimes
            # are unique.
            ts = f"{20260101 + i:08d}T120000Z"
            f = backups_dir / f"{base}.{ts}.{ext}.bak"
            f.write_text("x", encoding="utf-8")
            mtime = base_mtime + i  # newer indexes = newer mtime
            _os.utime(f, (mtime, mtime))
            files.append(f)
        return files

    # ---- load_retention_policy ----

    def test_load_missing_file_returns_defaults(self, tmp_path):
        from scripts.cleanup import load_retention_policy, _DEFAULT_RETENTION

        policy = load_retention_policy(tmp_path / "no-such.yaml")
        assert policy == _DEFAULT_RETENTION
        # Default rule covers the common patterns.
        patterns = {r["pattern"] for r in policy["rules"]}
        assert "content/notes/*.py" in patterns
        assert "editions.yaml" in patterns

    def test_load_corrupt_yaml_returns_defaults(self, tmp_path):
        from scripts.cleanup import load_retention_policy, _DEFAULT_RETENTION

        cfg = tmp_path / "bad.yaml"
        cfg.write_text("not: [valid yaml", encoding="utf-8")
        policy = load_retention_policy(cfg)
        assert policy == _DEFAULT_RETENTION

    def test_load_explicit_rules(self, tmp_path):
        from scripts.cleanup import load_retention_policy

        cfg = tmp_path / "policy.yaml"
        cfg.write_text(
            "rules:\n"
            "  - pattern: 'foo/*.py'\n"
            "    keep_revisions: 7\n"
            "  - pattern: 'bar.yaml'\n"
            "    keep_days: 14\n"
            "default:\n"
            "  keep_revisions: 3\n",
            encoding="utf-8",
        )
        policy = load_retention_policy(cfg)
        assert policy["default"]["keep_revisions"] == 3
        assert len(policy["rules"]) == 2
        rules_by_pat = {r["pattern"]: r for r in policy["rules"]}
        assert rules_by_pat["foo/*.py"]["keep_revisions"] == 7
        assert rules_by_pat["bar.yaml"]["keep_days"] == 14

    def test_load_drops_invalid_rule_entries(self, tmp_path):
        # Rules without exactly one of keep_revisions / keep_days
        # are silently dropped. Pin so a typo in the YAML doesn't
        # crash cleanup.
        from scripts.cleanup import load_retention_policy

        cfg = tmp_path / "policy.yaml"
        cfg.write_text(
            "rules:\n"
            "  - pattern: 'good/*.py'\n"
            "    keep_revisions: 5\n"
            "  - pattern: 'no-keep/*.py'\n"  # missing both
            "  - pattern: 'both/*.py'\n"  # has both
            "    keep_revisions: 3\n"
            "    keep_days: 7\n"
            "default:\n"
            "  keep_revisions: 2\n",
            encoding="utf-8",
        )
        policy = load_retention_policy(cfg)
        patterns = {r["pattern"] for r in policy["rules"]}
        assert patterns == {"good/*.py"}

    # ---- select_rule ----

    def test_select_rule_first_match_wins(self):
        from scripts.cleanup import select_rule
        from pathlib import Path

        policy = {
            "rules": [
                {"pattern": "content/notes/*.py", "keep_revisions": 10},
                {"pattern": "*.py", "keep_revisions": 999},
            ],
            "default": {"keep_revisions": 5},
        }
        # Both rules match content/notes/gen.py; the FIRST wins.
        rule = select_rule(Path("content/notes/gen.py"), policy)
        assert rule["keep_revisions"] == 10

    def test_select_rule_falls_back_to_default(self):
        from scripts.cleanup import select_rule
        from pathlib import Path

        policy = {
            "rules": [
                {"pattern": "scripts/*.py", "keep_revisions": 10},
            ],
            "default": {"keep_revisions": 5},
        }
        rule = select_rule(Path("content/notes/gen.py"), policy)
        assert rule["keep_revisions"] == 5

    def test_select_rule_handles_basename_match(self):
        # PurePath.match is right-anchored, so the pattern
        # "editions.yaml" (no path) matches
        # "content/editions.yaml". Pin this — the production
        # default policy relies on it.
        from scripts.cleanup import select_rule
        from pathlib import Path

        policy = {
            "rules": [
                {"pattern": "editions.yaml", "keep_days": 30},
            ],
            "default": {"keep_revisions": 5},
        }
        rule = select_rule(Path("content/editions.yaml"), policy)
        assert rule["keep_days"] == 30

    # ---- _backups_to_prune ----

    def test_backups_to_prune_keep_revisions(self, tmp_path):
        from scripts.cleanup import _backups_to_prune

        files = self._make_backup_files(tmp_path / ".backups", "x.py", 8)
        # Keep 3: prune the oldest 5.
        to_prune = _backups_to_prune(files, {"keep_revisions": 3})
        assert len(to_prune) == 5
        # The 3 newest survive (largest mtimes).
        kept = set(files) - set(to_prune)
        assert kept == set(files[-3:])

    def test_backups_to_prune_keep_revisions_zero(self, tmp_path):
        from scripts.cleanup import _backups_to_prune

        files = self._make_backup_files(tmp_path / ".backups", "x.py", 4)
        # Keep 0 → prune all.
        to_prune = _backups_to_prune(files, {"keep_revisions": 0})
        assert len(to_prune) == 4

    def test_backups_to_prune_keep_days(self, tmp_path):
        import time as _t
        import os as _os
        from scripts.cleanup import _backups_to_prune

        backups = tmp_path / ".backups"
        backups.mkdir()
        now = _t.time()
        # 3 files: 5 days old, 35 days old, 100 days old.
        ages = (5, 35, 100)
        files = []
        for i, days in enumerate(ages):
            f = backups / f"x.{i}.bak"
            f.write_text("x", encoding="utf-8")
            mtime = now - days * 86400
            _os.utime(f, (mtime, mtime))
            files.append(f)
        # Keep 30 days: 35-day and 100-day files prune.
        to_prune = _backups_to_prune(
            files,
            {"keep_days": 30},
            now=now,
        )
        assert len(to_prune) == 2
        # The 5-day file survives.
        assert files[0] not in to_prune

    def test_backups_to_prune_unknown_rule_is_noop(self, tmp_path):
        from scripts.cleanup import _backups_to_prune

        files = self._make_backup_files(tmp_path / ".backups", "x.py", 3)
        # Rule has neither keep_revisions nor keep_days.
        to_prune = _backups_to_prune(files, {})
        assert to_prune == []

    # ---- plan_backups dispatch ----

    def test_plan_backups_legacy_keep_arg_overrides_policy(
        self,
        tmp_path,
        monkeypatch,
    ):
        from scripts import cleanup as _cu
        from pathlib import Path

        # Synthetic .backups/ tree under a fake REPO_ROOT.
        repo = tmp_path / "repo"
        repo.mkdir()
        notes_backups = repo / "content" / "notes" / ".backups"
        files = self._make_backup_files(notes_backups, "gen.py", 8)
        monkeypatch.setattr(_cu, "REPO_ROOT", repo)
        grouped = {notes_backups: files}
        # keep=2 wins over the (nonexistent here) policy default of 5.
        targets, _ = _cu.plan_backups(grouped, keep=2)
        assert len(targets) == 6  # 8 - 2 = 6 to prune

    def test_plan_backups_uses_policy_when_keep_is_none(
        self,
        tmp_path,
        monkeypatch,
    ):
        from scripts import cleanup as _cu

        repo = tmp_path / "repo"
        repo.mkdir()
        notes_backups = repo / "content" / "notes" / ".backups"
        files = self._make_backup_files(notes_backups, "gen.py", 12)
        monkeypatch.setattr(_cu, "REPO_ROOT", repo)
        grouped = {notes_backups: files}
        # Default policy: content/notes/*.py keeps 10 revisions.
        targets, _ = _cu.plan_backups(grouped, keep=None)
        assert len(targets) == 2  # 12 - 10 = 2 to prune

    def test_plan_backups_pattern_dispatch(
        self,
        tmp_path,
        monkeypatch,
    ):
        # Two stems matching different rules: one matches the
        # notes/*.py rule (keep 10); the other matches the default
        # (keep 5). Verify each prunes the right amount.
        from scripts import cleanup as _cu

        repo = tmp_path / "repo"
        repo.mkdir()
        notes_backups = repo / "content" / "notes" / ".backups"
        notes_files = self._make_backup_files(
            notes_backups,
            "gen.py",
            13,
        )
        misc_backups = repo / "scripts" / ".backups"
        misc_files = self._make_backup_files(
            misc_backups,
            "helper.py",
            8,
        )
        monkeypatch.setattr(_cu, "REPO_ROOT", repo)
        grouped = {
            notes_backups: notes_files,
            misc_backups: misc_files,
        }
        targets, _ = _cu.plan_backups(grouped, keep=None)
        # notes: keep 10 → prune 3; misc: default keep 5 → prune 3.
        # Total: 6.
        assert len(targets) == 6

    def test_plan_backups_legacy_signature_back_compat(
        self,
        tmp_path,
        monkeypatch,
    ):
        # Old callers used `plan_backups(grouped, 5)` positional.
        # Pin that signature still works after the kwarg refactor.
        from scripts import cleanup as _cu

        repo = tmp_path / "repo"
        repo.mkdir()
        bk = repo / "content" / ".backups"
        files = self._make_backup_files(bk, "x.yaml", 10)
        monkeypatch.setattr(_cu, "REPO_ROOT", repo)
        grouped = {bk: files}
        targets, _ = _cu.plan_backups(grouped, 4)  # positional
        assert len(targets) == 6

    # ---- defaults shape ----

    def test_default_retention_covers_load_bearing_files(self):
        from scripts.cleanup import _DEFAULT_RETENTION

        patterns = {r["pattern"] for r in _DEFAULT_RETENTION["rules"]}
        # The PLAN spec called out these specific patterns.
        for required in (
            "content/notes/*.py",
            "editions.yaml",
            "epub_working/**",
        ):
            assert required in patterns
        # Default fallback preserves current 5-revision behavior.
        assert _DEFAULT_RETENTION["default"]["keep_revisions"] == 5

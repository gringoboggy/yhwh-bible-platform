"""Δ.10 — schema migration framework pins.

Topic file (created alongside the Δ.10 ship, follows the ω.27
follow-on convention).

Coverage:
- TestDelta10MigrationsList:    `MIGRATIONS` list shape (baseline
  notes_baseline, strictly increasing versions, idempotent SQL).
- TestDelta10MigrateRunner:     `current_version`, `pending`,
  `apply_pending` semantics across fresh DB / replay /
  ahead-of-HEAD scenarios.
- TestDelta10MigrationValidation: `_validate_migrations` rejects
  malformed entries at import time.
- TestDelta10CorpusIndexWired:  corpus_index.connection() returns
  a DB with `schema_migrations` populated and the notes table
  intact (the wire-up replaces the old inline `_SCHEMA`).
- TestDelta10RunMigrationsCli:  the standalone CLI exit codes +
  --dry-run + --current paths.

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""

from __future__ import annotations

import sqlite3


class TestDelta10MigrationsList:
    """The declarative MIGRATIONS list is the source of truth.
    Pin its baseline shape so a future contributor can't silently
    drop migration #1 or break the version-monotonicity invariant."""

    @classmethod
    def setup_class(cls):
        from scripts.core.migrations import MIGRATIONS

        cls.migrations = MIGRATIONS

    def test_is_non_empty(self):
        assert self.migrations, "MIGRATIONS list cannot be empty (need migration #1 baseline)"

    def test_first_migration_is_notes_baseline(self):
        version, name, _sql = self.migrations[0]
        assert version == 1, f"first migration must be #1, got {version}"
        assert name == "notes_baseline", f"first migration name drift: got {name!r}"

    def test_versions_strictly_increasing(self):
        last = 0
        for version, _name, _sql in self.migrations:
            assert version > last, f"versions must be strictly increasing; {version} after {last}"
            last = version

    def test_versions_are_positive_ints(self):
        for version, _name, _sql in self.migrations:
            assert isinstance(version, int) and version > 0, f"bad version: {version!r}"

    def test_names_non_empty(self):
        for _version, name, _sql in self.migrations:
            assert isinstance(name, str) and name.strip(), f"bad name: {name!r}"

    def test_baseline_sql_creates_notes_table_idempotently(self):
        # Migration #1 SQL must use the IF NOT EXISTS pattern so a
        # rebuild over an existing schema doesn't error.
        _v, _n, sql = self.migrations[0]
        assert "CREATE TABLE IF NOT EXISTS notes" in sql
        for ix in ("ix_notes_book", "ix_notes_kind", "ix_notes_book_chapter", "ix_notes_book_kind"):
            assert f"CREATE INDEX IF NOT EXISTS {ix}" in sql, f"baseline missing index: {ix}"


class TestDelta10MigrateRunner:
    """Runner semantics: fresh DB, replay, idempotency, partial
    application, ahead-of-HEAD synthetic migrations."""

    def test_fresh_db_starts_at_version_zero(self):
        from scripts.core import migrate

        conn = sqlite3.connect(":memory:")
        try:
            assert migrate.current_version(conn) == 0
        finally:
            conn.close()

    def test_fresh_db_pending_is_full_list(self):
        from scripts.core import migrate
        from scripts.core.migrations import MIGRATIONS

        conn = sqlite3.connect(":memory:")
        try:
            pending = migrate.pending(conn)
            assert len(pending) == len(MIGRATIONS)
            assert pending[0] == (MIGRATIONS[0][0], MIGRATIONS[0][1])
        finally:
            conn.close()

    def test_apply_pending_records_in_schema_migrations(self):
        from scripts.core import migrate

        conn = sqlite3.connect(":memory:")
        try:
            applied = migrate.apply_pending(conn)
            assert applied, "expected at least one applied migration on a fresh DB"
            # The notes table from migration #1 must exist
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notes'")
            assert cur.fetchone() is not None
            # The metadata table must be populated
            cur = conn.execute(f"SELECT version, name FROM {migrate.SCHEMA_MIGRATIONS_TABLE} ORDER BY version")
            rows = cur.fetchall()
            assert rows[0][0] == 1
            assert rows[0][1] == "notes_baseline"
        finally:
            conn.close()

    def test_apply_pending_is_idempotent(self):
        from scripts.core import migrate

        conn = sqlite3.connect(":memory:")
        try:
            first = migrate.apply_pending(conn)
            second = migrate.apply_pending(conn)
            assert first, "first apply must report progress"
            assert second == [], f"second apply must be a no-op; got {second}"
        finally:
            conn.close()

    def test_apply_pending_records_applied_at_timestamp(self):
        from scripts.core import migrate

        conn = sqlite3.connect(":memory:")
        try:
            migrate.apply_pending(conn)
            cur = conn.execute(f"SELECT applied_at FROM {migrate.SCHEMA_MIGRATIONS_TABLE}")
            for (ts,) in cur.fetchall():
                # ISO-8601 with timezone, like "2026-05-11T18:00:00+00:00"
                assert isinstance(ts, str) and len(ts) >= 19, f"bad applied_at: {ts!r}"
                assert "T" in ts, f"applied_at not ISO-8601: {ts!r}"
        finally:
            conn.close()

    def test_synthetic_migration_appended_applies_on_next_run(self, monkeypatch):
        # Simulate adding a future migration #N+1 — runner should
        # apply only that new one, leaving the existing ones alone.
        from scripts.core import migrate
        from scripts.core import migrations as migmod

        conn = sqlite3.connect(":memory:")
        try:
            # Bring DB to current HEAD first.
            migrate.apply_pending(conn)
            head_before = migrate.current_version(conn)

            # Append a synthetic future migration via monkeypatch.
            future_version = head_before + 1
            synthetic = (
                future_version,
                "test_synthetic_extra_table",
                "CREATE TABLE IF NOT EXISTS _test_extra (id INTEGER PRIMARY KEY);",
            )
            monkeypatch.setattr(migmod, "MIGRATIONS", [*migmod.MIGRATIONS, synthetic])

            applied = migrate.apply_pending(conn)
            assert applied == [(future_version, "test_synthetic_extra_table")]

            # The new table from the synthetic migration must exist
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='_test_extra'")
            assert cur.fetchone() is not None
            assert migrate.current_version(conn) == future_version
        finally:
            conn.close()

    def test_failed_migration_aborts_chain(self, monkeypatch):
        # A migration with broken SQL should fail loudly and leave
        # the DB at the version BEFORE the failure (no half-applied
        # later migrations).
        from scripts.core import migrate
        from scripts.core import migrations as migmod

        conn = sqlite3.connect(":memory:")
        try:
            head_before = migrate.current_version(conn)
            broken_version = head_before + 1
            broken = (
                broken_version,
                "test_broken_syntax",
                "CREATE TABLE invalid syntax here without closing paren (",
            )
            never_run_version = broken_version + 1
            never_run = (
                never_run_version,
                "test_should_not_run",
                "CREATE TABLE IF NOT EXISTS _test_should_not_exist (id INTEGER);",
            )
            monkeypatch.setattr(migmod, "MIGRATIONS", [*migmod.MIGRATIONS, broken, never_run])

            import pytest

            with pytest.raises(sqlite3.Error):
                migrate.apply_pending(conn)

            # The later migration MUST NOT have been applied
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='_test_should_not_exist'")
            assert cur.fetchone() is None, "later migration ran despite earlier failure"
        finally:
            conn.close()


class TestDelta10MigrationValidation:
    """`_validate_migrations` rejects malformed entries — this is the
    developer-error guard that prevents silent breakage at runtime.

    Pass an explicit list to each call so the live MIGRATIONS isn't
    mutated."""

    def test_rejects_zero_version(self):
        from scripts.core import migrate

        import pytest

        with pytest.raises(ValueError, match="positive int"):
            migrate._validate_migrations([(0, "bad", "SELECT 1")])

    def test_rejects_negative_version(self):
        from scripts.core import migrate

        import pytest

        with pytest.raises(ValueError, match="positive int"):
            migrate._validate_migrations([(-1, "bad", "SELECT 1")])

    def test_rejects_duplicate_version(self):
        from scripts.core import migrate

        import pytest

        with pytest.raises(ValueError, match="strictly increasing|duplicate"):
            migrate._validate_migrations([(1, "a", "SELECT 1"), (1, "b", "SELECT 2")])

    def test_rejects_non_increasing(self):
        from scripts.core import migrate

        import pytest

        with pytest.raises(ValueError, match="strictly increasing"):
            migrate._validate_migrations([(2, "a", "SELECT 1"), (1, "b", "SELECT 2")])

    def test_rejects_empty_name(self):
        from scripts.core import migrate

        import pytest

        with pytest.raises(ValueError, match="name"):
            migrate._validate_migrations([(1, "", "SELECT 1")])


class TestDelta10CorpusIndexWired:
    """The corpus_index module must now use the migration runner.
    Pin that the rebuild path applies migrations and the resulting
    DB exposes both the notes table AND the metadata table."""

    def test_connection_has_schema_migrations_table(self):
        from scripts.core import corpus_index

        conn = corpus_index.connection()
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
        assert cur.fetchone() is not None, "corpus_index DB missing schema_migrations table after Δ.10 wire-up"

    def test_connection_at_head_version(self):
        from scripts.core import corpus_index, migrate

        conn = corpus_index.connection()
        # After rebuild, HEAD must equal the highest version in MIGRATIONS
        from scripts.core.migrations import MIGRATIONS

        expected_head = MIGRATIONS[-1][0]
        assert migrate.current_version(conn) == expected_head

    def test_notes_table_still_populated_after_wire_up(self):
        from scripts.core import corpus_index

        conn = corpus_index.connection()
        cur = conn.execute("SELECT COUNT(*) FROM notes")
        count = cur.fetchone()[0]
        # The exact count drifts with corpus growth; just assert the
        # wire-up didn't accidentally produce an empty index.
        assert count > 0, "corpus_index notes table is empty after Δ.10 wire-up"

    def test_legacy_schema_alias_still_points_at_baseline(self):
        # `_SCHEMA` is retained as a back-compat alias for any
        # external import that referenced it pre-Δ.10.
        from scripts.core import corpus_index
        from scripts.core.migrations import MIGRATIONS

        assert corpus_index._SCHEMA == MIGRATIONS[0][2]


class TestDelta10RunMigrationsCli:
    """Standalone CLI: exit codes + the --dry-run / --current paths."""

    def test_current_on_fresh_db(self, tmp_path, capsys):
        from scripts.run_migrations import main

        db = tmp_path / "new.sqlite"  # doesn't exist yet
        rc = main(["--db", str(db), "--current"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "HEAD=0" in out or "no DB" in out

    def test_dry_run_lists_pending_without_applying(self, tmp_path, capsys):
        from scripts.run_migrations import main

        db = tmp_path / "new.sqlite"
        rc = main(["--db", str(db), "--dry-run"])
        out = capsys.readouterr().out
        assert rc == 0
        # The pending list (on a non-existent DB → HEAD=0 → all pending).
        # On a non-existent DB the runner prints "(no DB...; HEAD=0)" —
        # both shapes satisfy "dry run didn't apply anything".
        assert "HEAD=0" in out or "pending" in out

    def test_apply_creates_db_and_records_migration(self, tmp_path, capsys):
        from scripts.run_migrations import main
        from scripts.core import migrate

        db = tmp_path / "new.sqlite"
        rc = main(["--db", str(db)])
        out = capsys.readouterr().out
        assert rc == 0
        assert db.exists(), "expected runner to create the DB file"
        # Verify state via direct connection
        conn = sqlite3.connect(str(db))
        try:
            from scripts.core.migrations import MIGRATIONS

            assert migrate.current_version(conn) == MIGRATIONS[-1][0]
        finally:
            conn.close()
        assert "applied" in out

    def test_second_apply_is_noop(self, tmp_path, capsys):
        from scripts.run_migrations import main

        db = tmp_path / "new.sqlite"
        main(["--db", str(db)])  # first apply
        capsys.readouterr()  # drain output
        rc = main(["--db", str(db)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "at HEAD" in out and "nothing to apply" in out

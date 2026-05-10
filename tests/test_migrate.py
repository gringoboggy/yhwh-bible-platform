"""Tests for migrate — extracted from test_scripts.py in ω.27.

Originally lived in tests/test_scripts.py as part of a 22,000-line
monolithic test file; moved here so each test target sits next to a
single source-of-truth scripts/ module. Future tests for the same
target should land in this file rather than test_scripts.py.
"""

from __future__ import annotations


class TestOmega22MigrationFramework:
    """ω.22 — versioned migration runner. Each migration is a
    Python module under `scripts/migrations/` exposing ID,
    DESCRIPTION, up(), down(). Runner reads + writes the
    `content/.migration_state.yaml` ledger.

    Tests use synthetic migration files in tmp_path + an
    injected state_path so we don't actually invoke the wrapped
    ω.5 / ψ.8 helpers (those are exercised in their own tests).
    """

    # ---- helpers shared across tests ----

    @staticmethod
    def _make_migration(
        d,
        ident: str,
        name: str,
        *,
        up_returns: dict | None = None,
        down_returns: dict | None = None,
        up_raises: str | None = None,
        down_raises_not_implemented: bool = False,
    ):
        """Write a synthetic migration module file."""
        from pathlib import Path

        path = Path(d) / f"{ident}_{name}.py"
        body = [
            f'ID = "{ident}"',
            f'DESCRIPTION = "test migration {name}"',
        ]
        if up_returns is None:
            up_returns = {"ok": True, "message": "ok"}
        if up_raises:
            body.append(f"def up():\n    raise RuntimeError({up_raises!r})")
        else:
            body.append(f"def up(): return {up_returns!r}")
        if down_raises_not_implemented:
            body.append('def down():\n    raise NotImplementedError("forward-only test migration")')
        elif down_returns is not None:
            body.append(f"def down(): return {down_returns!r}")
        else:
            body.append('def down(): return {"ok": True, "message": "ok"}')
        path.write_text("\n".join(body) + "\n", encoding="utf-8")
        return path

    # ---- discover_migrations ----

    def test_discover_finds_well_named_files_in_order(
        self,
        tmp_path,
    ):
        from scripts.migrate import discover_migrations

        d = tmp_path / "migs"
        d.mkdir()
        self._make_migration(d, "0002", "second")
        self._make_migration(d, "0001", "first")
        self._make_migration(d, "0010", "tenth")
        result = discover_migrations(d)
        ids = [m["id"] for m in result]
        assert ids == ["0001", "0002", "0010"]

    def test_discover_skips_bad_names(self, tmp_path):
        from scripts.migrate import discover_migrations

        d = tmp_path / "migs"
        d.mkdir()
        # Real migration:
        self._make_migration(d, "0001", "good")
        # Distractors that the runner must skip:
        (d / "README.md").write_text("not a migration", encoding="utf-8")
        (d / "999_no_zero_pad.py").write_text("ID='999'\n", encoding="utf-8")
        (d / "0001.py").write_text("# no name\n", encoding="utf-8")
        (d / "abcd_letters.py").write_text("# nope\n", encoding="utf-8")
        result = discover_migrations(d)
        assert [m["id"] for m in result] == ["0001"]

    def test_discover_handles_missing_dir(self, tmp_path):
        from scripts.migrate import discover_migrations

        result = discover_migrations(tmp_path / "no-such-dir")
        assert result == []

    def test_discover_attaches_module_and_description(
        self,
        tmp_path,
    ):
        from scripts.migrate import discover_migrations

        d = tmp_path / "migs"
        d.mkdir()
        self._make_migration(d, "0001", "demo")
        m = discover_migrations(d)[0]
        assert m["module"].ID == "0001"
        assert m["description"] == "test migration demo"
        assert m["path"].name == "0001_demo.py"

    # ---- load_state / save_state ----

    def test_load_state_missing_file_returns_empty(self, tmp_path):
        from scripts.migrate import load_state

        state = load_state(tmp_path / "no-state.yaml")
        assert state == {"applied": []}

    def test_load_state_round_trip(self, tmp_path):
        from scripts.migrate import load_state, save_state

        sp = tmp_path / "state.yaml"
        save_state(
            {
                "applied": [
                    {"id": "0001", "name": "demo", "applied_at": "2026-05-09"},
                ]
            },
            sp,
        )
        loaded = load_state(sp)
        assert len(loaded["applied"]) == 1
        assert loaded["applied"][0]["id"] == "0001"

    def test_load_state_corrupt_returns_empty(self, tmp_path):
        # If the YAML has the wrong shape, the runner treats it as
        # empty rather than crashing — important for first-time
        # users who hand-edit the file.
        from scripts.migrate import load_state

        sp = tmp_path / "state.yaml"
        sp.write_text("not_applied_key: 42\n", encoding="utf-8")
        loaded = load_state(sp)
        assert loaded == {"applied": []}

    # ---- pending / applied filters ----

    def test_pending_and_applied_partition(self, tmp_path):
        from scripts.migrate import (
            discover_migrations,
            pending_migrations,
            applied_migrations,
        )

        d = tmp_path / "migs"
        d.mkdir()
        self._make_migration(d, "0001", "first")
        self._make_migration(d, "0002", "second")
        self._make_migration(d, "0003", "third")
        migrations = discover_migrations(d)

        state = {
            "applied": [
                {"id": "0001", "name": "first", "applied_at": "x"},
            ]
        }
        pending = pending_migrations(state, migrations)
        applied = applied_migrations(state, migrations)
        assert [m["id"] for m in pending] == ["0002", "0003"]
        assert [m["id"] for m in applied] == ["0001"]

    # ---- apply_up ----

    def test_apply_up_records_ledger_entry(self, tmp_path):
        from scripts.migrate import (
            apply_up,
            discover_migrations,
            load_state,
        )

        d = tmp_path / "migs"
        d.mkdir()
        self._make_migration(d, "0001", "demo")
        sp = tmp_path / "state.yaml"
        m = discover_migrations(d)[0]

        result = apply_up(m, load_state(sp), state_path=sp)
        assert result["ok"] is True
        assert result["skipped"] is False

        state = load_state(sp)
        assert any(e["id"] == "0001" for e in state["applied"])
        assert "applied_at" in state["applied"][0]

    def test_apply_up_idempotent_on_already_applied(self, tmp_path):
        from scripts.migrate import apply_up, discover_migrations

        d = tmp_path / "migs"
        d.mkdir()
        self._make_migration(d, "0001", "demo")
        sp = tmp_path / "state.yaml"
        m = discover_migrations(d)[0]

        state = {
            "applied": [
                {"id": "0001", "name": "demo", "applied_at": "x"},
            ]
        }
        result = apply_up(m, state, state_path=sp)
        assert result["ok"] is True
        assert result["skipped"] is True
        assert "already applied" in result["message"]

    def test_apply_up_surfaces_module_failure(self, tmp_path):
        from scripts.migrate import apply_up, discover_migrations

        d = tmp_path / "migs"
        d.mkdir()
        self._make_migration(d, "0001", "broken", up_raises="boom")
        sp = tmp_path / "state.yaml"
        m = discover_migrations(d)[0]

        result = apply_up(m, {"applied": []}, state_path=sp)
        assert result["ok"] is False
        assert "boom" in result["message"]
        # And the ledger stays empty.
        from scripts.migrate import load_state

        assert load_state(sp)["applied"] == []

    # ---- apply_down ----

    def test_apply_down_removes_ledger_entry(self, tmp_path):
        from scripts.migrate import (
            apply_down,
            discover_migrations,
            load_state,
            save_state,
        )

        d = tmp_path / "migs"
        d.mkdir()
        self._make_migration(d, "0001", "demo")
        sp = tmp_path / "state.yaml"
        save_state(
            {
                "applied": [
                    {"id": "0001", "name": "demo", "applied_at": "x"},
                ]
            },
            sp,
        )
        m = discover_migrations(d)[0]

        result = apply_down(m, load_state(sp), state_path=sp)
        assert result["ok"] is True
        assert load_state(sp)["applied"] == []

    def test_apply_down_forward_only_returns_clear_error(
        self,
        tmp_path,
    ):
        from scripts.migrate import apply_down, discover_migrations

        d = tmp_path / "migs"
        d.mkdir()
        self._make_migration(
            d,
            "0001",
            "fwdonly",
            down_raises_not_implemented=True,
        )
        sp = tmp_path / "state.yaml"
        m = discover_migrations(d)[0]

        state = {
            "applied": [
                {"id": "0001", "name": "fwdonly", "applied_at": "x"},
            ]
        }
        result = apply_down(m, state, state_path=sp)
        assert result["ok"] is False
        assert result.get("forward_only") is True
        assert "forward-only" in result["message"]

    def test_apply_down_on_not_applied_is_noop(self, tmp_path):
        from scripts.migrate import apply_down, discover_migrations

        d = tmp_path / "migs"
        d.mkdir()
        self._make_migration(d, "0001", "demo")
        sp = tmp_path / "state.yaml"
        m = discover_migrations(d)[0]

        result = apply_down(m, {"applied": []}, state_path=sp)
        assert result["ok"] is True
        assert result["skipped"] is True

    # ---- run_up / run_down ----

    def test_run_up_applies_all_pending(self, tmp_path):
        from scripts.migrate import run_up, load_state

        d = tmp_path / "migs"
        d.mkdir()
        self._make_migration(d, "0001", "first")
        self._make_migration(d, "0002", "second")
        self._make_migration(d, "0003", "third")
        sp = tmp_path / "state.yaml"

        result = run_up(migrations_dir=d, state_path=sp)
        assert result["ok"] is True
        assert result["summary"]["applied_count"] == 3
        applied_ids = {e["id"] for e in load_state(sp)["applied"]}
        assert applied_ids == {"0001", "0002", "0003"}

    def test_run_up_to_stops_at_target(self, tmp_path):
        from scripts.migrate import run_up, load_state

        d = tmp_path / "migs"
        d.mkdir()
        self._make_migration(d, "0001", "first")
        self._make_migration(d, "0002", "second")
        self._make_migration(d, "0003", "third")
        sp = tmp_path / "state.yaml"

        result = run_up(to="0002", migrations_dir=d, state_path=sp)
        assert result["ok"] is True
        ids = {e["id"] for e in load_state(sp)["applied"]}
        assert ids == {"0001", "0002"}

    def test_run_down_rolls_back_to_target(self, tmp_path):
        from scripts.migrate import (
            run_up,
            run_down,
            load_state,
        )

        d = tmp_path / "migs"
        d.mkdir()
        self._make_migration(d, "0001", "first")
        self._make_migration(d, "0002", "second")
        self._make_migration(d, "0003", "third")
        sp = tmp_path / "state.yaml"

        run_up(migrations_dir=d, state_path=sp)
        result = run_down(to="0001", migrations_dir=d, state_path=sp)
        assert result["ok"] is True
        ids = {e["id"] for e in load_state(sp)["applied"]}
        assert ids == {"0001"}

    def test_run_up_stops_on_failure(self, tmp_path):
        from scripts.migrate import run_up, load_state

        d = tmp_path / "migs"
        d.mkdir()
        self._make_migration(d, "0001", "first")
        self._make_migration(d, "0002", "broken", up_raises="kaboom")
        self._make_migration(d, "0003", "third")
        sp = tmp_path / "state.yaml"

        result = run_up(migrations_dir=d, state_path=sp)
        assert result["ok"] is False
        ids = {e["id"] for e in load_state(sp)["applied"]}
        # 0001 applied; 0002 failed; 0003 never attempted.
        assert ids == {"0001"}
        assert "kaboom" in result["failed"]["message"]

    # ---- status ----

    def test_status_snapshot_shape(self, tmp_path):
        from scripts.migrate import status, run_up

        d = tmp_path / "migs"
        d.mkdir()
        self._make_migration(d, "0001", "first")
        self._make_migration(d, "0002", "second")
        sp = tmp_path / "state.yaml"

        run_up(to="0001", migrations_dir=d, state_path=sp)
        snap = status(migrations_dir=d, state_path=sp)
        assert [m["id"] for m in snap["applied"]] == ["0001"]
        assert [m["id"] for m in snap["pending"]] == ["0002"]
        assert snap["total"] == 2

    # ---- real-world wiring ----

    def test_real_migrations_discovered(self):
        # Pin that 0001 + 0002 are picked up from the production
        # tree; if a future contributor renames or removes one, this
        # test surfaces the regression.
        from scripts.migrate import discover_migrations

        migrations = discover_migrations()
        ids = [m["id"] for m in migrations]
        assert "0001" in ids
        assert "0002" in ids
        # 0001 must wrap migrate_to_user_data; 0002 wraps
        # backfill_traditions. Verify by name.
        names = {m["id"]: m["name"] for m in migrations}
        assert names["0001"] == "migrate_to_user_data"
        assert names["0002"] == "backfill_traditions"

    def test_real_migration_modules_have_required_attrs(self):
        from scripts.migrate import discover_migrations

        for m in discover_migrations():
            mod = m["module"]
            assert hasattr(mod, "ID")
            assert hasattr(mod, "DESCRIPTION")
            assert callable(getattr(mod, "up", None))
            assert callable(getattr(mod, "down", None))

    def test_real_migrations_are_forward_only(self):
        # Both 0001 and 0002 are forward-only by design — verify
        # their down() raises NotImplementedError (the framework
        # surfaces this as forward_only=True).
        from scripts.migrate import discover_migrations

        for m in discover_migrations():
            import pytest

            with pytest.raises(NotImplementedError):
                m["module"].down()

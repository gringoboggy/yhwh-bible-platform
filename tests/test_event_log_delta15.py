"""Δ.15 — event log pins.

Topic file (created alongside the Δ.15 ship). Opens Month 5's
executive/business track. The event-log foundation that ε.1+
will compose against.

Coverage:
- TestDelta15EmitBasic:       `emit()` writes one valid JSON
  line, returns the recorded dict, generates ISO-8601 ts,
  preserves the kind.
- TestDelta15EmitFields:      arbitrary fields pass through;
  `ts` and `kind` from caller are silently ignored (reserved);
  non-JSON-serializable values raise TypeError.
- TestDelta15EmitValidation:  empty/blank/non-str kind raises
  ValueError.
- TestDelta15IterEvents:      reads back in write order; empty
  file (or missing) yields nothing; malformed lines skipped.
- TestDelta15TailAndCount:    tail(n) returns last N; count()
  matches iter_events length.
- TestDelta15FilePath:        log lives under `user_data_root() /
  events.jsonl`; parent dir is created on first emit.

Pinning rationale: Δ.15 is the foundation that ε.1 metrics +
ε.2 dashboard + ε.5 reports all consume. Drift in the line
format, the field reservations, or the parse-tolerance contract
would cascade through every downstream consumer.

All tests use `monkeypatch` of `event_log._event_log_path` to
isolate file state in tmp_path — production events.jsonl stays
untouched.
"""

from __future__ import annotations


def _isolate_log(monkeypatch, tmp_path):
    """Helper: redirect event_log to a tmp file."""
    from scripts.core import event_log

    log_path = tmp_path / "events.jsonl"
    monkeypatch.setattr(event_log, "_event_log_path", lambda: log_path)
    return log_path


class TestDelta15EmitBasic:
    """`emit()` writes a single JSON line per call."""

    def test_emit_writes_to_file(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        log = _isolate_log(monkeypatch, tmp_path)
        event_log.emit("test_event")
        assert log.is_file()
        assert log.stat().st_size > 0

    def test_emit_returns_recorded_dict(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        _isolate_log(monkeypatch, tmp_path)
        record = event_log.emit("save", edition_id="x")
        assert record["kind"] == "save"
        assert record["edition_id"] == "x"
        assert "ts" in record

    def test_emit_generates_iso_8601_ts(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        _isolate_log(monkeypatch, tmp_path)
        record = event_log.emit("save")
        # ISO-8601: YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM
        ts = record["ts"]
        assert "T" in ts
        assert "+" in ts or "Z" in ts, "ts must carry timezone info"
        assert len(ts) >= 19

    def test_emit_writes_one_line_per_call(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        log = _isolate_log(monkeypatch, tmp_path)
        for i in range(5):
            event_log.emit("test", n=i)
        # File should have exactly 5 newline-terminated lines.
        text = log.read_text(encoding="utf-8")
        lines = [line for line in text.split("\n") if line]
        assert len(lines) == 5

    def test_emitted_line_is_valid_json(self, monkeypatch, tmp_path):
        import json

        from scripts.core import event_log

        log = _isolate_log(monkeypatch, tmp_path)
        event_log.emit("kind_x", foo="bar", n=42)
        line = log.read_text(encoding="utf-8").strip()
        parsed = json.loads(line)
        assert parsed["kind"] == "kind_x"
        assert parsed["foo"] == "bar"
        assert parsed["n"] == 42


class TestDelta15EmitFields:
    """Arbitrary fields pass through; `ts`/`kind` reserved."""

    def test_arbitrary_fields_preserved(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        _isolate_log(monkeypatch, tmp_path)
        record = event_log.emit(
            "build_export",
            edition_id="catholic-study",
            actor="publisher",
            payload={"verses": 51000},
        )
        assert record["edition_id"] == "catholic-study"
        assert record["actor"] == "publisher"
        assert record["payload"] == {"verses": 51000}

    def test_caller_supplied_ts_ignored(self, monkeypatch, tmp_path):
        # `ts` is auto-generated; caller's value gets dropped so the
        # log can't be back-dated by a buggy caller.
        from scripts.core import event_log

        _isolate_log(monkeypatch, tmp_path)
        record = event_log.emit("save", ts="1999-01-01T00:00:00+00:00")
        assert record["ts"] != "1999-01-01T00:00:00+00:00"
        assert "2026" in record["ts"] or "2027" in record["ts"]

    def test_caller_supplied_kind_field_ignored(self, monkeypatch, tmp_path):
        # `kind` comes from the positional arg only — a stray
        # `kind=` kwarg can't override it.
        from scripts.core import event_log

        _isolate_log(monkeypatch, tmp_path)
        record = event_log.emit("real_kind", kind="hijacked")
        assert record["kind"] == "real_kind"

    def test_non_json_serializable_raises_typeerror(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        import pytest

        _isolate_log(monkeypatch, tmp_path)

        class NotSerializable:
            pass

        with pytest.raises(TypeError):
            event_log.emit("save", obj=NotSerializable())


class TestDelta15EmitValidation:
    """Empty / non-string kind rejected."""

    def test_empty_kind_raises(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        import pytest

        _isolate_log(monkeypatch, tmp_path)
        with pytest.raises(ValueError):
            event_log.emit("")

    def test_whitespace_kind_raises(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        import pytest

        _isolate_log(monkeypatch, tmp_path)
        with pytest.raises(ValueError):
            event_log.emit("   ")

    def test_non_string_kind_raises(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        import pytest

        _isolate_log(monkeypatch, tmp_path)
        with pytest.raises(ValueError):
            event_log.emit(42)  # type: ignore[arg-type]

    def test_kind_stripped_of_whitespace(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        _isolate_log(monkeypatch, tmp_path)
        record = event_log.emit("  save  ")
        assert record["kind"] == "save"


class TestDelta15IterEvents:
    """`iter_events()` reads back in write order."""

    def test_empty_log_yields_nothing(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        _isolate_log(monkeypatch, tmp_path)
        assert list(event_log.iter_events()) == []

    def test_missing_file_yields_nothing(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        # Point at a non-existent file (don't emit anything first).
        log_path = tmp_path / "does_not_exist.jsonl"
        monkeypatch.setattr(event_log, "_event_log_path", lambda: log_path)
        assert list(event_log.iter_events()) == []

    def test_yields_in_write_order(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        _isolate_log(monkeypatch, tmp_path)
        for i in range(3):
            event_log.emit("seq", n=i)
        events = list(event_log.iter_events())
        assert [e["n"] for e in events] == [0, 1, 2]

    def test_malformed_lines_skipped(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        log = _isolate_log(monkeypatch, tmp_path)
        # Hand-write a bad line + a good line.
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(
            'not-json-at-all\n{"ts": "2026-01-01T00:00:00+00:00", "kind": "x"}\n',
            encoding="utf-8",
        )
        events = list(event_log.iter_events())
        assert len(events) == 1, "malformed line should be skipped, valid line preserved"
        assert events[0]["kind"] == "x"

    def test_empty_lines_skipped(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        log = _isolate_log(monkeypatch, tmp_path)
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(
            '{"ts": "2026-01-01T00:00:00+00:00", "kind": "a"}\n\n\n{"ts": "2026-01-01T00:00:01+00:00", "kind": "b"}\n',
            encoding="utf-8",
        )
        events = list(event_log.iter_events())
        assert len(events) == 2


class TestDelta15TailAndCount:
    """`tail()` and `count()` helpers."""

    def test_tail_returns_last_n(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        _isolate_log(monkeypatch, tmp_path)
        for i in range(10):
            event_log.emit("seq", n=i)
        last_3 = event_log.tail(3)
        assert [e["n"] for e in last_3] == [7, 8, 9]

    def test_tail_handles_zero(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        _isolate_log(monkeypatch, tmp_path)
        event_log.emit("a")
        assert event_log.tail(0) == []

    def test_tail_handles_more_than_available(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        _isolate_log(monkeypatch, tmp_path)
        event_log.emit("a")
        event_log.emit("b")
        last_100 = event_log.tail(100)
        assert len(last_100) == 2

    def test_tail_clamps_negative_to_zero(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        _isolate_log(monkeypatch, tmp_path)
        event_log.emit("a")
        assert event_log.tail(-5) == []

    def test_count_matches_iter_events_length(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        _isolate_log(monkeypatch, tmp_path)
        for i in range(7):
            event_log.emit("x", n=i)
        assert event_log.count() == 7
        assert event_log.count() == len(list(event_log.iter_events()))

    def test_count_empty(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        _isolate_log(monkeypatch, tmp_path)
        assert event_log.count() == 0


class TestDelta15FilePath:
    """The log lives under `user_data_root()`; parent created on
    first emit."""

    def test_default_path_includes_events_jsonl(self, monkeypatch, tmp_path):
        # Patch user_data_root, NOT _event_log_path, to verify the
        # default resolution still produces .../events.jsonl.
        from scripts.core import event_log, paths

        monkeypatch.setattr(paths, "user_data_root", lambda: tmp_path)
        # Re-call (not the isolation helper) — let the path module
        # resolve naturally.
        resolved = event_log._event_log_path()
        assert resolved.name == "events.jsonl"
        assert resolved.parent == tmp_path

    def test_parent_dir_created_on_first_emit(self, monkeypatch, tmp_path):
        from scripts.core import event_log

        deep = tmp_path / "nested" / "dir" / "events.jsonl"
        monkeypatch.setattr(event_log, "_event_log_path", lambda: deep)
        assert not deep.parent.exists()
        event_log.emit("test")
        assert deep.parent.is_dir()
        assert deep.is_file()

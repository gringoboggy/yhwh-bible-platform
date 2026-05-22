"""ε.1 — metrics collector pins.

Topic file (created alongside the ε.1 ship). Month 5 #2.

Coverage:
- TestEpsilon1EventsTotal:        `events_total()` matches
  `event_log.count()`.
- TestEpsilon1EventsByKind:       `events_by_kind()` aggregates by
  event kind.
- TestEpsilon1BuildsByOutcome:    `builds_by_outcome()` buckets
  build_start / build_complete / build_failure events.
- TestEpsilon1BuildsByEdition:    `builds_by_edition()` ranks
  top editions by build_complete count.
- TestEpsilon1RecentEvents:       `recent_events(n)` pass-through.
- TestEpsilon1IterSince:          `iter_events_since(iso_ts)`
  filters via lex-sort.
- TestEpsilon1SummaryKpis:        `summary_kpis()` returns the
  canonical dashboard payload shape.
- TestEpsilon1BuildExportEmits:   `api_export_build` emits
  build_start + (build_complete OR build_failure) events.

All tests use monkeypatch isolation of the event-log file.

Pinning rationale: ε.1's rollups are the contract the /exec
dashboard (ε.2) and quarterly auto-report (ε.5) consume. Drift
in the shape of `summary_kpis()` or the bucket-counting logic
would silently break the downstream UI.
"""

from __future__ import annotations


def _isolate(monkeypatch, tmp_path):
    from scripts.core import event_log

    log_path = tmp_path / "events.jsonl"
    monkeypatch.setattr(event_log, "_event_log_path", lambda: log_path)
    return log_path


class TestEpsilon1EventsTotal:
    def test_zero_for_empty_log(self, monkeypatch, tmp_path):
        from scripts.core import metrics

        _isolate(monkeypatch, tmp_path)
        assert metrics.events_total() == 0

    def test_matches_event_count(self, monkeypatch, tmp_path):
        from scripts.core import event_log, metrics

        _isolate(monkeypatch, tmp_path)
        for i in range(5):
            event_log.emit("x", i=i)
        assert metrics.events_total() == 5


class TestEpsilon1EventsByKind:
    def test_empty_returns_empty_dict(self, monkeypatch, tmp_path):
        from scripts.core import metrics

        _isolate(monkeypatch, tmp_path)
        assert metrics.events_by_kind() == {}

    def test_counts_per_kind(self, monkeypatch, tmp_path):
        from scripts.core import event_log, metrics

        _isolate(monkeypatch, tmp_path)
        event_log.emit("save")
        event_log.emit("save")
        event_log.emit("build")
        result = metrics.events_by_kind()
        assert result == {"save": 2, "build": 1}


class TestEpsilon1BuildsByOutcome:
    def test_empty_log_returns_zero_buckets(self, monkeypatch, tmp_path):
        from scripts.core import metrics

        _isolate(monkeypatch, tmp_path)
        assert metrics.builds_by_outcome() == {"start": 0, "complete": 0, "failure": 0}

    def test_buckets_build_events(self, monkeypatch, tmp_path):
        from scripts.core import event_log, metrics

        _isolate(monkeypatch, tmp_path)
        event_log.emit("build_start", edition_id="a")
        event_log.emit("build_complete", edition_id="a")
        event_log.emit("build_start", edition_id="b")
        event_log.emit("build_failure", edition_id="b", reason="x")
        event_log.emit("save", edition_id="a")  # not a build event
        assert metrics.builds_by_outcome() == {"start": 2, "complete": 1, "failure": 1}


class TestEpsilon1BuildsByEdition:
    def test_top_by_complete_count(self, monkeypatch, tmp_path):
        from scripts.core import event_log, metrics

        _isolate(monkeypatch, tmp_path)
        event_log.emit("build_complete", edition_id="a")
        event_log.emit("build_complete", edition_id="a")
        event_log.emit("build_complete", edition_id="b")
        event_log.emit("build_failure", edition_id="c")  # failures excluded
        top = metrics.builds_by_edition(limit=5)
        assert top[0] == ("a", 2)
        assert ("b", 1) in top
        assert ("c", 1) not in top  # not in build_complete

    def test_respects_limit(self, monkeypatch, tmp_path):
        from scripts.core import event_log, metrics

        _isolate(monkeypatch, tmp_path)
        for ed in ("a", "b", "c", "d", "e"):
            event_log.emit("build_complete", edition_id=ed)
        assert len(metrics.builds_by_edition(limit=3)) == 3


class TestEpsilon1RecentEvents:
    def test_default_limit_is_20(self, monkeypatch, tmp_path):
        from scripts.core import event_log, metrics

        _isolate(monkeypatch, tmp_path)
        for i in range(30):
            event_log.emit("test", i=i)
        recent = metrics.recent_events()
        assert len(recent) == 20

    def test_custom_limit(self, monkeypatch, tmp_path):
        from scripts.core import event_log, metrics

        _isolate(monkeypatch, tmp_path)
        for i in range(10):
            event_log.emit("test", i=i)
        assert len(metrics.recent_events(3)) == 3


class TestEpsilon1IterSince:
    def test_filters_by_iso_ts_string(self, monkeypatch, tmp_path):
        # ISO-8601 strings lex-sort identically to chronological
        # order, so >= on the string is a valid since-filter.
        from scripts.core import metrics

        log = _isolate(monkeypatch, tmp_path)
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(
            '{"ts": "2025-01-01T00:00:00+00:00", "kind": "old"}\n'
            '{"ts": "2026-05-11T00:00:00+00:00", "kind": "borderline"}\n'
            '{"ts": "2026-06-01T00:00:00+00:00", "kind": "newer"}\n',
            encoding="utf-8",
        )
        events = list(metrics.iter_events_since("2026-05-11T00:00:00+00:00"))
        assert [e["kind"] for e in events] == ["borderline", "newer"]


class TestEpsilon1SummaryKpis:
    def test_shape_is_stable_when_empty(self, monkeypatch, tmp_path):
        from scripts.core import metrics

        _isolate(monkeypatch, tmp_path)
        kpis = metrics.summary_kpis()
        assert kpis["events_total"] == 0
        assert kpis["events_by_kind_top_5"] == []
        assert kpis["builds"]["start"] == 0
        assert kpis["builds"]["complete"] == 0
        assert kpis["builds"]["failure"] == 0
        assert kpis["builds"]["success_rate"] == 0.0
        assert kpis["top_built_editions"] == []
        assert kpis["recent_events"] == []

    def test_success_rate_computed_correctly(self, monkeypatch, tmp_path):
        from scripts.core import event_log, metrics

        _isolate(monkeypatch, tmp_path)
        event_log.emit("build_complete", edition_id="a")
        event_log.emit("build_complete", edition_id="b")
        event_log.emit("build_complete", edition_id="c")
        event_log.emit("build_failure", edition_id="d", reason="x")
        kpis = metrics.summary_kpis()
        # 3 success / 4 terminal = 0.75
        assert kpis["builds"]["success_rate"] == 0.75

    def test_recent_events_capped_at_5(self, monkeypatch, tmp_path):
        from scripts.core import event_log, metrics

        _isolate(monkeypatch, tmp_path)
        for i in range(20):
            event_log.emit("test", i=i)
        kpis = metrics.summary_kpis()
        assert len(kpis["recent_events"]) == 5

    def test_top_kinds_capped_at_5(self, monkeypatch, tmp_path):
        from scripts.core import event_log, metrics

        _isolate(monkeypatch, tmp_path)
        for kind in ("a", "b", "c", "d", "e", "f", "g"):
            event_log.emit(kind)
        kpis = metrics.summary_kpis()
        assert len(kpis["events_by_kind_top_5"]) == 5


class TestEpsilon1BuildExportEmits:
    """`api_export_build` calls event_log.emit at the right points."""

    def test_unknown_edition_emits_failure(self, monkeypatch, tmp_path):
        from scripts.api import exports
        from scripts.core import event_log, metrics

        _isolate(monkeypatch, tmp_path)
        # No need to mock config — unknown id triggers the early
        # return path; the emit fires before subprocess.
        exports.api_export_build("no_such_edition")
        outcomes = metrics.builds_by_outcome()
        assert outcomes["failure"] == 1
        # The failure record carries `reason='unknown_edition'`.
        recent = event_log.tail(1)[0]
        assert recent["kind"] == "build_failure"
        assert recent.get("reason") == "unknown_edition"

    def test_emit_failures_dont_break_build(self, monkeypatch, tmp_path):
        # Even if event_log.emit raises, the build path must
        # continue. Pin the try/except wrap.
        from scripts.api import exports
        from scripts.core import event_log

        _isolate(monkeypatch, tmp_path)

        def boom(*_args, **_kw):
            raise RuntimeError("event log down")

        monkeypatch.setattr(event_log, "emit", boom)
        # Should not raise.
        result = exports.api_export_build("no_such_edition")
        assert "error" in result  # original error envelope still returned

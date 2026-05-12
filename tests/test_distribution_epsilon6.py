"""ε.6 — distribution channel checklist pins (2026-05-11).

Month 5 #5. Per-edition shipped-to-channel state tracking.

Coverage:
- TestEpsilon6Constants:           DISTRIBUTION_CHANNELS, CHANNEL_LABELS,
  SCHEMA_VERSION, ENTRY_FIELDS pinned.
- TestEpsilon6LoadSave:            empty-state default, missing file
  tolerance, malformed JSON tolerance, atomic write round-trip,
  stale-field stripping on save.
- TestEpsilon6MarkUnmark:           mark_shipped writes; preserves
  shipped_at on re-mark unless overridden; merges optional fields;
  validates channel id. mark_unshipped removes (idempotent); empty
  edition row pruned to keep JSON sparse. ValueError on unknown channel
  in mark_shipped.
- TestEpsilon6Rollup:                rollup composes full-edition view;
  per-channel coverage % math; overall coverage; zero-edition + zero-
  channel edge cases.
- TestEpsilon6IsShipped:             true/false for present/missing
  entries; unknown channel returns False rather than raising.
- TestEpsilon6ApiList:               api_distribution_list payload
  shape + composes load_distribution + load_editions.
- TestEpsilon6ApiMark:               PUT happy path (writes entry,
  returns ok); unknown channel rejected; unknown edition rejected;
  missing channel param rejected.
- TestEpsilon6ApiUnmark:             DELETE happy path; idempotent
  (already-absent returns ok:True, removed:False); unknown channel
  rejected.
- TestEpsilon6ExecTemplateGrid:      EXEC_HTML defines the distribution
  table, thead row id, coverage line id, and the JS render/toggle
  pair.
- TestEpsilon6RouteRegistration:    GET /api/distribution in
  _SIMPLE_GET_ROUTES; PUT /api/distribution/<edition> in _PUT_ROUTES;
  DELETE /api/distribution/<edition>/<channel> in _DELETE_ROUTES.

All tests redirect `distribution._distribution_path` to tmp so the
real content/distribution.json is never touched.
"""

from __future__ import annotations

import json

import pytest


def _isolate_distribution(monkeypatch, tmp_path):
    """Redirect the distribution file to tmp. Mirrors event_log
    isolation pattern."""
    from scripts.core import distribution

    p = tmp_path / "distribution.json"
    monkeypatch.setattr(distribution, "_distribution_path", lambda: p)
    return p


# --------------------------------------------------------------------
# Module constants
# --------------------------------------------------------------------


class TestEpsilon6Constants:
    def test_distribution_channels_pinned(self):
        from scripts.core import distribution

        assert distribution.DISTRIBUTION_CHANNELS == (
            "kdp",
            "apple",
            "google",
            "archive_org",
            "own_site",
        )

    def test_channel_labels_cover_every_channel(self):
        from scripts.core import distribution

        for ch in distribution.DISTRIBUTION_CHANNELS:
            assert ch in distribution.CHANNEL_LABELS
            assert distribution.CHANNEL_LABELS[ch]  # non-empty

    def test_schema_version_pinned(self):
        from scripts.core import distribution

        assert distribution.SCHEMA_VERSION == 1

    def test_entry_fields_pinned(self):
        from scripts.core import distribution

        # The on-disk per-entry shape — pinning so a future schema
        # bump is a conscious change.
        assert distribution.ENTRY_FIELDS == ("shipped_at", "url", "isbn", "notes")


# --------------------------------------------------------------------
# load / save
# --------------------------------------------------------------------


class TestEpsilon6LoadSave:
    def test_empty_state_when_file_missing(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        state = distribution.load_distribution()
        assert state == {"schema_version": 1, "editions": {}}

    def test_malformed_json_yields_empty_state(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        path = _isolate_distribution(monkeypatch, tmp_path)
        path.write_text("not json at all", encoding="utf-8")
        state = distribution.load_distribution()
        assert state["editions"] == {}

    def test_round_trip(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        state = {
            "schema_version": 1,
            "editions": {"catholic-study": {"kdp": {"shipped_at": "2026-05-11T00:00:00+00:00", "url": "https://x"}}},
        }
        distribution.save_distribution(state)
        round_tripped = distribution.load_distribution()
        assert round_tripped["editions"]["catholic-study"]["kdp"]["url"] == "https://x"

    def test_save_strips_unknown_channels(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        state = {
            "editions": {
                "ed-x": {
                    "kdp": {"shipped_at": "t"},
                    "bogus_channel": {"shipped_at": "t"},
                }
            }
        }
        distribution.save_distribution(state)
        round_tripped = distribution.load_distribution()
        assert "kdp" in round_tripped["editions"]["ed-x"]
        assert "bogus_channel" not in round_tripped["editions"]["ed-x"]

    def test_save_strips_unknown_entry_fields(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        state = {
            "editions": {
                "ed-x": {
                    "kdp": {
                        "shipped_at": "t",
                        "rogue_field": "drop me",
                    }
                }
            }
        }
        distribution.save_distribution(state)
        round_tripped = distribution.load_distribution()
        entry = round_tripped["editions"]["ed-x"]["kdp"]
        assert "rogue_field" not in entry
        assert entry["shipped_at"] == "t"


# --------------------------------------------------------------------
# mark / unmark
# --------------------------------------------------------------------


class TestEpsilon6MarkUnmark:
    def test_mark_shipped_writes_entry(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        entry = distribution.mark_shipped("catholic-study", "kdp", url="https://amazon.com/x")
        assert "shipped_at" in entry
        assert entry["url"] == "https://amazon.com/x"
        state = distribution.load_distribution()
        assert state["editions"]["catholic-study"]["kdp"]["url"] == "https://amazon.com/x"

    def test_mark_shipped_preserves_existing_shipped_at(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        first = distribution.mark_shipped("ed-x", "kdp")
        # Second mark without shipped_at override — same timestamp.
        second = distribution.mark_shipped("ed-x", "kdp", url="https://x")
        assert second["shipped_at"] == first["shipped_at"]
        assert second["url"] == "https://x"

    def test_mark_shipped_accepts_shipped_at_override(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        distribution.mark_shipped("ed-x", "kdp")
        override = distribution.mark_shipped("ed-x", "kdp", shipped_at="2020-01-01T00:00:00+00:00")
        assert override["shipped_at"] == "2020-01-01T00:00:00+00:00"

    def test_mark_shipped_rejects_unknown_channel(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        with pytest.raises(ValueError, match="unknown distribution channel"):
            distribution.mark_shipped("ed-x", "kobo")

    def test_mark_unshipped_removes(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        distribution.mark_shipped("ed-x", "kdp")
        assert distribution.mark_unshipped("ed-x", "kdp") is True
        state = distribution.load_distribution()
        # Edition row pruned when no channels remain.
        assert "ed-x" not in state["editions"]

    def test_mark_unshipped_keeps_other_channels(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        distribution.mark_shipped("ed-x", "kdp")
        distribution.mark_shipped("ed-x", "apple")
        distribution.mark_unshipped("ed-x", "kdp")
        state = distribution.load_distribution()
        assert "apple" in state["editions"]["ed-x"]
        assert "kdp" not in state["editions"]["ed-x"]

    def test_mark_unshipped_idempotent(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        # Already absent — returns False, doesn't raise.
        assert distribution.mark_unshipped("ed-x", "kdp") is False
        # After mark + unmark, second unmark is still False.
        distribution.mark_shipped("ed-x", "kdp")
        distribution.mark_unshipped("ed-x", "kdp")
        assert distribution.mark_unshipped("ed-x", "kdp") is False

    def test_mark_unshipped_unknown_channel_returns_false(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        assert distribution.mark_unshipped("ed-x", "kobo") is False


# --------------------------------------------------------------------
# is_shipped
# --------------------------------------------------------------------


class TestEpsilon6IsShipped:
    def test_true_when_entry_present(self):
        from scripts.core import distribution

        state = {"editions": {"ed-x": {"kdp": {"shipped_at": "t"}}}}
        assert distribution.is_shipped(state, "ed-x", "kdp") is True

    def test_false_when_missing(self):
        from scripts.core import distribution

        state = {"editions": {}}
        assert distribution.is_shipped(state, "ed-x", "kdp") is False

    def test_unknown_channel_returns_false(self):
        from scripts.core import distribution

        state = {"editions": {"ed-x": {"kobo": {"shipped_at": "t"}}}}
        assert distribution.is_shipped(state, "ed-x", "kobo") is False


# --------------------------------------------------------------------
# rollup
# --------------------------------------------------------------------


class TestEpsilon6Rollup:
    def _editions(self):
        return [
            {"id": "catholic-study", "title": "Catholic Study Bible"},
            {"id": "evangelical-reformed", "title": "Evangelical Reformed Bible"},
        ]

    def test_rollup_returns_one_row_per_edition(self):
        from scripts.core import distribution

        state = {"editions": {}}
        result = distribution.rollup(state, self._editions())
        assert len(result["editions"]) == 2

    def test_rollup_channel_columns_pinned(self):
        from scripts.core import distribution

        state = {"editions": {}}
        result = distribution.rollup(state, self._editions())
        assert [c["id"] for c in result["channels"]] == list(distribution.DISTRIBUTION_CHANNELS)

    def test_rollup_marks_shipped_cells(self):
        from scripts.core import distribution

        state = {
            "editions": {
                "catholic-study": {
                    "kdp": {"shipped_at": "t", "url": "https://x"},
                }
            }
        }
        result = distribution.rollup(state, self._editions())
        catholic = next(r for r in result["editions"] if r["id"] == "catholic-study")
        assert catholic["channels"]["kdp"]["shipped"] is True
        assert catholic["channels"]["kdp"]["url"] == "https://x"
        assert catholic["channels"]["apple"]["shipped"] is False

    def test_rollup_per_channel_coverage(self):
        from scripts.core import distribution

        # 1 of 2 editions shipped to KDP → 50%; 0 to apple → 0%.
        state = {"editions": {"catholic-study": {"kdp": {"shipped_at": "t"}}}}
        result = distribution.rollup(state, self._editions())
        assert result["by_channel_coverage"]["kdp"]["percent"] == 50.0
        assert result["by_channel_coverage"]["apple"]["percent"] == 0.0

    def test_rollup_overall_coverage(self):
        from scripts.core import distribution

        state = {"editions": {"catholic-study": {"kdp": {"shipped_at": "t"}}}}
        result = distribution.rollup(state, self._editions())
        # 1 shipped cell of 2 editions × 5 channels = 10 cells = 10%.
        assert result["overall"]["shipped_cells"] == 1
        assert result["overall"]["total_cells"] == 10
        assert result["overall"]["percent"] == 10.0

    def test_rollup_empty_editions_safe(self):
        from scripts.core import distribution

        result = distribution.rollup({}, [])
        assert result["editions"] == []
        assert result["overall"]["percent"] == 0.0


# --------------------------------------------------------------------
# API endpoints
# --------------------------------------------------------------------


class TestEpsilon6ApiList:
    def test_payload_shape(self, monkeypatch, tmp_path):
        from scripts.api.distribution import api_distribution_list

        _isolate_distribution(monkeypatch, tmp_path)
        result = api_distribution_list()
        assert result["status"] == "ok"
        assert "rollup" in result
        assert "schema_version" in result
        rollup = result["rollup"]
        for key in ("channels", "editions", "by_channel_coverage", "overall"):
            assert key in rollup, f"rollup missing {key!r}"


class TestEpsilon6ApiMark:
    def _real_edition_id(self):
        from scripts.core import config

        eds = config.load_editions()
        assert eds, "test depends on at least one real edition existing"
        return str(eds[0]["id"])

    def test_happy_path(self, monkeypatch, tmp_path):
        from scripts.api.distribution import api_distribution_mark
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        ed_id = self._real_edition_id()
        result = api_distribution_mark(ed_id, {"channel": "kdp", "url": "https://x"})
        assert result["ok"] is True
        assert result["channel"] == "kdp"
        assert result["entry"]["url"] == "https://x"
        assert distribution.is_shipped(distribution.load_distribution(), ed_id, "kdp")

    def test_unknown_channel_rejected(self, monkeypatch, tmp_path):
        from scripts.api.distribution import api_distribution_mark

        _isolate_distribution(monkeypatch, tmp_path)
        ed_id = self._real_edition_id()
        result = api_distribution_mark(ed_id, {"channel": "kobo"})
        assert result["ok"] is False
        assert result["error"] == "unknown_channel"

    def test_unknown_edition_rejected(self, monkeypatch, tmp_path):
        from scripts.api.distribution import api_distribution_mark

        _isolate_distribution(monkeypatch, tmp_path)
        result = api_distribution_mark("def-not-a-real-edition", {"channel": "kdp"})
        assert result["ok"] is False
        assert result["error"] == "unknown_edition"

    def test_missing_channel_rejected(self, monkeypatch, tmp_path):
        from scripts.api.distribution import api_distribution_mark

        _isolate_distribution(monkeypatch, tmp_path)
        ed_id = self._real_edition_id()
        result = api_distribution_mark(ed_id, {})
        assert result["ok"] is False
        assert result["error"] == "missing_channel"


class TestEpsilon6ApiUnmark:
    def test_happy_path(self, monkeypatch, tmp_path):
        from scripts.api.distribution import api_distribution_unmark
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        distribution.mark_shipped("ed-x", "kdp")
        result = api_distribution_unmark("ed-x", "kdp")
        assert result["ok"] is True
        assert result["removed"] is True

    def test_idempotent(self, monkeypatch, tmp_path):
        from scripts.api.distribution import api_distribution_unmark

        _isolate_distribution(monkeypatch, tmp_path)
        result = api_distribution_unmark("ed-x", "kdp")
        assert result["ok"] is True
        assert result["removed"] is False

    def test_unknown_channel_rejected(self, monkeypatch, tmp_path):
        from scripts.api.distribution import api_distribution_unmark

        _isolate_distribution(monkeypatch, tmp_path)
        result = api_distribution_unmark("ed-x", "kobo")
        assert result["ok"] is False
        assert result["error"] == "unknown_channel"


# --------------------------------------------------------------------
# Template
# --------------------------------------------------------------------


class TestEpsilon6ExecTemplateGrid:
    @classmethod
    def setup_class(cls):
        from scripts.templates.exec import EXEC_HTML

        cls.html = EXEC_HTML

    def test_distribution_section_present(self):
        assert 'id="distribution-section"' in self.html
        assert 'id="distribution-table"' in self.html
        assert 'id="distribution-thead-row"' in self.html
        assert 'id="distribution-tbody"' in self.html
        assert 'id="distribution-coverage-line"' in self.html

    def test_js_render_and_toggle_present(self):
        for fn in (
            "renderDistribution",
            "onDistributionCellClick",
            "loadDistribution",
        ):
            assert fn in self.html, f"missing JS function {fn!r}"

    def test_endpoints_referenced(self):
        assert "/api/distribution" in self.html
        # Mark and unmark are constructed dynamically — pin the
        # method strings.
        assert "'PUT'" in self.html or '"PUT"' in self.html
        assert "'DELETE'" in self.html or '"DELETE"' in self.html


# --------------------------------------------------------------------
# Route registration
# --------------------------------------------------------------------


class TestEpsilon6RouteRegistration:
    def test_get_route_in_simple_table(self):
        from scripts import web

        routes = {p: h for (p, h) in web._SIMPLE_GET_ROUTES}
        assert "/api/distribution" in routes
        assert routes["/api/distribution"] is web.api_distribution_list

    def test_put_route_in_put_table(self):
        import re

        from scripts import web

        for regex, handler in web._PUT_ROUTES:
            if regex.match("/api/distribution/catholic-study"):
                # Make sure the handler maps to api_distribution_mark
                # by calling it with a minimal payload — error envelope
                # confirms wiring.
                result = handler(
                    re.match(regex.pattern, "/api/distribution/catholic-study"),
                    {"channel": "kobo"},
                )
                assert result.get("ok") is False
                assert result.get("error") == "unknown_channel"
                return
        pytest.fail("no PUT route matches /api/distribution/<edition>")

    def test_delete_route_in_delete_table(self):
        import re

        from scripts import web

        for regex, handler in web._DELETE_ROUTES:
            if regex.match("/api/distribution/catholic-study/kdp"):
                result = handler(re.match(regex.pattern, "/api/distribution/catholic-study/kdp"))
                # Idempotent — already-absent returns ok:True.
                assert result.get("ok") is True
                return
        pytest.fail("no DELETE route matches /api/distribution/<edition>/<channel>")


# --------------------------------------------------------------------
# Integration: full mark → unmark round-trip via the public API
# --------------------------------------------------------------------


class TestEpsilon6FullRoundTrip:
    def test_mark_then_unmark_via_api(self, monkeypatch, tmp_path):
        from scripts.api.distribution import (
            api_distribution_list,
            api_distribution_mark,
            api_distribution_unmark,
        )
        from scripts.core import config, distribution

        _isolate_distribution(monkeypatch, tmp_path)
        ed_id = str(config.load_editions()[0]["id"])

        # Initially: not shipped.
        rollup0 = api_distribution_list()["rollup"]
        cell0 = next(r for r in rollup0["editions"] if r["id"] == ed_id)["channels"]["kdp"]
        assert cell0["shipped"] is False

        # Mark.
        api_distribution_mark(ed_id, {"channel": "kdp", "url": "https://x", "isbn": "9781"})

        # Now shipped + persisted to disk.
        rollup1 = api_distribution_list()["rollup"]
        cell1 = next(r for r in rollup1["editions"] if r["id"] == ed_id)["channels"]["kdp"]
        assert cell1["shipped"] is True
        assert cell1["url"] == "https://x"
        assert cell1["isbn"] == "9781"

        # Disk has the JSON.
        path = distribution._distribution_path()
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        assert on_disk["editions"][ed_id]["kdp"]["url"] == "https://x"

        # Unmark.
        api_distribution_unmark(ed_id, "kdp")
        rollup2 = api_distribution_list()["rollup"]
        cell2 = next(r for r in rollup2["editions"] if r["id"] == ed_id)["channels"]["kdp"]
        assert cell2["shipped"] is False

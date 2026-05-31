"""ε.6 — distribution channel checklist pins (2026-05-11).

Month 5 #5. Per-edition shipped-to-channel state tracking.

As of Phase 4 (decommercialize, free-public pivot) only the free
surfaces survive: archive_org / own_site. The commercial channels
(kdp/apple/google) and the `scripts.api.distribution` HTTP layer were
removed; this suite tracks only the surviving core library.

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

All tests redirect `distribution._distribution_path` to tmp so the
real content/distribution.json is never touched.
"""

from __future__ import annotations

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
        assert distribution.ENTRY_FIELDS == ("shipped_at", "url", "notes")


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
            "editions": {
                "catholic-study": {"archive_org": {"shipped_at": "2026-05-11T00:00:00+00:00", "url": "https://x"}}
            },
        }
        distribution.save_distribution(state)
        round_tripped = distribution.load_distribution()
        assert round_tripped["editions"]["catholic-study"]["archive_org"]["url"] == "https://x"

    def test_save_strips_unknown_channels(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        state = {
            "editions": {
                "ed-x": {
                    "archive_org": {"shipped_at": "t"},
                    "bogus_channel": {"shipped_at": "t"},
                }
            }
        }
        distribution.save_distribution(state)
        round_tripped = distribution.load_distribution()
        assert "archive_org" in round_tripped["editions"]["ed-x"]
        assert "bogus_channel" not in round_tripped["editions"]["ed-x"]

    def test_save_strips_unknown_entry_fields(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        state = {
            "editions": {
                "ed-x": {
                    "archive_org": {
                        "shipped_at": "t",
                        "rogue_field": "drop me",
                    }
                }
            }
        }
        distribution.save_distribution(state)
        round_tripped = distribution.load_distribution()
        entry = round_tripped["editions"]["ed-x"]["archive_org"]
        assert "rogue_field" not in entry
        assert entry["shipped_at"] == "t"


# --------------------------------------------------------------------
# mark / unmark
# --------------------------------------------------------------------


class TestEpsilon6MarkUnmark:
    def test_mark_shipped_writes_entry(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        entry = distribution.mark_shipped("catholic-study", "archive_org", url="https://archive.org/x")
        assert "shipped_at" in entry
        assert entry["url"] == "https://archive.org/x"
        state = distribution.load_distribution()
        assert state["editions"]["catholic-study"]["archive_org"]["url"] == "https://archive.org/x"

    def test_mark_shipped_preserves_existing_shipped_at(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        first = distribution.mark_shipped("ed-x", "archive_org")
        # Second mark without shipped_at override — same timestamp.
        second = distribution.mark_shipped("ed-x", "archive_org", url="https://x")
        assert second["shipped_at"] == first["shipped_at"]
        assert second["url"] == "https://x"

    def test_mark_shipped_accepts_shipped_at_override(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        distribution.mark_shipped("ed-x", "archive_org")
        override = distribution.mark_shipped("ed-x", "archive_org", shipped_at="2020-01-01T00:00:00+00:00")
        assert override["shipped_at"] == "2020-01-01T00:00:00+00:00"

    def test_mark_shipped_rejects_unknown_channel(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        with pytest.raises(ValueError, match="unknown distribution channel"):
            distribution.mark_shipped("ed-x", "kobo")

    def test_mark_unshipped_removes(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        distribution.mark_shipped("ed-x", "archive_org")
        assert distribution.mark_unshipped("ed-x", "archive_org") is True
        state = distribution.load_distribution()
        # Edition row pruned when no channels remain.
        assert "ed-x" not in state["editions"]

    def test_mark_unshipped_keeps_other_channels(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        distribution.mark_shipped("ed-x", "archive_org")
        distribution.mark_shipped("ed-x", "own_site")
        distribution.mark_unshipped("ed-x", "archive_org")
        state = distribution.load_distribution()
        assert "own_site" in state["editions"]["ed-x"]
        assert "archive_org" not in state["editions"]["ed-x"]

    def test_mark_unshipped_idempotent(self, monkeypatch, tmp_path):
        from scripts.core import distribution

        _isolate_distribution(monkeypatch, tmp_path)
        # Already absent — returns False, doesn't raise.
        assert distribution.mark_unshipped("ed-x", "archive_org") is False
        # After mark + unmark, second unmark is still False.
        distribution.mark_shipped("ed-x", "archive_org")
        distribution.mark_unshipped("ed-x", "archive_org")
        assert distribution.mark_unshipped("ed-x", "archive_org") is False

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

        state = {"editions": {"ed-x": {"archive_org": {"shipped_at": "t"}}}}
        assert distribution.is_shipped(state, "ed-x", "archive_org") is True

    def test_false_when_missing(self):
        from scripts.core import distribution

        state = {"editions": {}}
        assert distribution.is_shipped(state, "ed-x", "archive_org") is False

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
                    "archive_org": {"shipped_at": "t", "url": "https://x"},
                }
            }
        }
        result = distribution.rollup(state, self._editions())
        catholic = next(r for r in result["editions"] if r["id"] == "catholic-study")
        assert catholic["channels"]["archive_org"]["shipped"] is True
        assert catholic["channels"]["archive_org"]["url"] == "https://x"
        assert catholic["channels"]["own_site"]["shipped"] is False

    def test_rollup_per_channel_coverage(self):
        from scripts.core import distribution

        # 1 of 2 editions shipped to archive_org → 50%; 0 to own_site → 0%.
        state = {"editions": {"catholic-study": {"archive_org": {"shipped_at": "t"}}}}
        result = distribution.rollup(state, self._editions())
        assert result["by_channel_coverage"]["archive_org"]["percent"] == 50.0
        assert result["by_channel_coverage"]["own_site"]["percent"] == 0.0

    def test_rollup_overall_coverage(self):
        from scripts.core import distribution

        state = {"editions": {"catholic-study": {"archive_org": {"shipped_at": "t"}}}}
        result = distribution.rollup(state, self._editions())
        # 1 shipped cell of 2 editions × 2 channels = 4 cells = 25%.
        assert result["overall"]["shipped_cells"] == 1
        assert result["overall"]["total_cells"] == 4
        assert result["overall"]["percent"] == 25.0

    def test_rollup_empty_editions_safe(self):
        from scripts.core import distribution

        result = distribution.rollup({}, [])
        assert result["editions"] == []
        assert result["overall"]["percent"] == 0.0

"""ρ.3 Phase C2-5 — verse-level note "ships?" override.

Tests the atomic three-state ``api_save_note_override`` endpoint (force-on via
``enabled_note_ids`` / force-off via ``disabled_note_ids``, mutually exclusive)
and the byte-neutral ``ships`` / ``kind_enabled`` read-API flags exposed by the
chapter level of ``api_build_my_bible``.

Every test that MUTATES ``content/editions.yaml`` backs it up + restores it in a
``finally`` (mirroring the existing note-toggle tests) so the working tree stays
clean after the run.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _import_web():
    import importlib

    return importlib.import_module("scripts.web")


def _import_editions():
    import importlib

    return importlib.import_module("scripts.api.editions")


# A note whose FAMILY is ON for catholic-study at gen:1 (kind "word").
NID_FAMILY_ON = "gen:1:1b:word"
# A note whose FAMILY is OFF for catholic-study at gen:1 (kind "topic-nave").
NID_FAMILY_OFF = "gen:1:1i:topic-nave"
ED = "catholic-study"


@pytest.fixture()
def yaml_isolation(tmp_path):
    """Back up + restore content/editions.yaml around a mutating test."""
    from scripts.core import config

    path = REPO_ROOT / "content" / "editions.yaml"
    backup = tmp_path / "editions.preserve.yaml"
    shutil.copy(path, backup)
    config.load_editions.cache_clear()
    try:
        yield path
    finally:
        shutil.copy(backup, path)
        config.load_editions.cache_clear()
        from scripts.core import matrix as matrix_mod

        matrix_mod.compute_matrix.cache_clear()


def _edition(ed_id):
    from scripts.core import config

    config.load_editions.cache_clear()
    return config.editions_by_id()[ed_id]


# --------------------------------------------------------------------------- #
# api_save_note_override — three-state writes + mutual exclusivity
# --------------------------------------------------------------------------- #


class TestNoteOverrideAPI:
    def test_state_on_forces_on_and_clears_disabled(self, yaml_isolation):
        ed = _import_editions()
        # Seed: the note is force-OFF first, then flip to ON → must move lists.
        ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "off"})
        e = _edition(ED)
        assert NID_FAMILY_OFF in (e.get("disabled_note_ids") or [])

        r = ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "on"})
        assert r.get("ok"), r
        assert r["state"] == "on"
        e = _edition(ED)
        assert NID_FAMILY_OFF in (e.get("enabled_note_ids") or [])
        assert NID_FAMILY_OFF not in (e.get("disabled_note_ids") or [])

    def test_state_off_forces_off_and_clears_enabled(self, yaml_isolation):
        ed = _import_editions()
        ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "on"})
        e = _edition(ED)
        assert NID_FAMILY_OFF in (e.get("enabled_note_ids") or [])

        r = ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "off"})
        assert r.get("ok"), r
        e = _edition(ED)
        assert NID_FAMILY_OFF in (e.get("disabled_note_ids") or [])
        assert NID_FAMILY_OFF not in (e.get("enabled_note_ids") or [])

    def test_state_default_removes_from_both(self, yaml_isolation):
        ed = _import_editions()
        ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "on"})
        r = ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "default"})
        assert r.get("ok"), r
        e = _edition(ED)
        assert NID_FAMILY_OFF not in (e.get("enabled_note_ids") or [])
        assert NID_FAMILY_OFF not in (e.get("disabled_note_ids") or [])

    def test_mutual_exclusivity_never_in_both(self, yaml_isolation):
        ed = _import_editions()
        for state in ("on", "off", "on", "default", "off"):
            ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": state})
            e = _edition(ED)
            in_on = NID_FAMILY_OFF in (e.get("enabled_note_ids") or [])
            in_off = NID_FAMILY_OFF in (e.get("disabled_note_ids") or [])
            assert not (in_on and in_off), f"in BOTH after state={state}"

    def test_counts_reported(self, yaml_isolation):
        ed = _import_editions()
        r = ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "on"})
        assert r["enabled_count"] == 1
        assert r["disabled_count"] == 0
        r = ed.api_save_note_override(ED, {"note_id": NID_FAMILY_ON, "state": "off"})
        assert r["enabled_count"] == 1
        assert r["disabled_count"] == 1

    def test_unchanged_when_already_default(self, yaml_isolation):
        ed = _import_editions()
        r = ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "default"})
        assert r.get("ok"), r
        assert r.get("unchanged") is True

    def test_unchanged_when_already_in_target_state(self, yaml_isolation):
        # Re-asserting a state the note is already in is a no-op (both writes
        # idempotent). Covers the "on→on" / "off→off" no-op paths.
        ed = _import_editions()
        ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "on"})
        r = ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "on"})
        assert r.get("ok"), r
        assert r.get("unchanged") is True
        ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "off"})
        r = ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "off"})
        assert r.get("ok"), r
        assert r.get("unchanged") is True

    def test_bad_state(self, yaml_isolation):
        ed = _import_editions()
        r = ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "maybe"})
        assert "error" in r

    def test_bad_note_id(self, yaml_isolation):
        ed = _import_editions()
        r = ed.api_save_note_override(ED, {"note_id": "malformed", "state": "on"})
        assert "error" in r
        r = ed.api_save_note_override(ED, {"note_id": "fake:1:1a:word", "state": "on"})
        assert "error" in r

    def test_unknown_edition(self, yaml_isolation):
        ed = _import_editions()
        r = ed.api_save_note_override("not-real", {"note_id": NID_FAMILY_OFF, "state": "on"})
        assert "error" in r

    def test_yaml_round_trips(self, yaml_isolation):
        """config.load_editions() must parse cleanly after the write, and a
        third-party parser (pyyaml) must agree on the list contents."""
        ed = _import_editions()
        ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "on"})

        from scripts.core import config

        config.load_editions.cache_clear()
        e = config.editions_by_id()[ED]
        assert NID_FAMILY_OFF in (e.get("enabled_note_ids") or [])

        import yaml

        raw = yaml.safe_load(yaml_isolation.read_text(encoding="utf-8"))
        cath = next(x for x in raw["editions"] if x["id"] == ED)
        assert NID_FAMILY_OFF in (cath.get("enabled_note_ids") or [])
        # Other editions untouched.
        eth = next(x for x in raw["editions"] if x["id"] == "ethiopian-tewahedo")
        assert NID_FAMILY_OFF not in (eth.get("enabled_note_ids") or [])


# --------------------------------------------------------------------------- #
# Read-API round-trip: ships / forced_on / disabled flip with the override
# --------------------------------------------------------------------------- #


class TestShipsReadFlags:
    def test_fixture_notes_exist_with_expected_family_state(self):
        # Guard: these tests pin two specific gen 1 notes whose FAMILY state
        # under `catholic-study` is fixed (NID_FAMILY_ON kind enabled,
        # NID_FAMILY_OFF kind disabled). If the corpus or edition canon/kinds
        # drift so the constants no longer hold, fail HERE with a clear message
        # instead of a confusing KeyError deeper in the suite.
        web = _import_web()
        notes = {n["note_id"]: n for v in web.api_build_my_bible(ED, "gen", 1)["verses"] for n in v["notes"]}
        assert NID_FAMILY_ON in notes, f"fixture note {NID_FAMILY_ON} no longer in {ED} gen 1 — update the constant"
        assert NID_FAMILY_OFF in notes, f"fixture note {NID_FAMILY_OFF} no longer in {ED} gen 1 — update the constant"
        assert notes[NID_FAMILY_ON]["kind_enabled"] is True, f"{NID_FAMILY_ON} family no longer ON for {ED}"
        assert notes[NID_FAMILY_OFF]["kind_enabled"] is False, f"{NID_FAMILY_OFF} family no longer OFF for {ED}"

    def test_flags_present_and_correct_at_default(self):
        web = _import_web()
        r = web.api_build_my_bible(ED, "gen", 1)
        notes = {n["note_id"]: n for v in r["verses"] for n in v["notes"]}
        # family-ON note ships by default
        on = notes[NID_FAMILY_ON]
        assert on["kind_enabled"] is True
        assert on["ships"] is True
        assert on["forced_on"] is False
        # family-OFF note does NOT ship by default
        off = notes[NID_FAMILY_OFF]
        assert off["kind_enabled"] is False
        assert off["ships"] is False
        assert off["forced_on"] is False

    def test_force_on_flips_ships(self, yaml_isolation):
        ed = _import_editions()
        web = _import_web()
        ed.api_save_note_override(ED, {"note_id": NID_FAMILY_OFF, "state": "on"})
        r = web.api_build_my_bible(ED, "gen", 1)
        notes = {n["note_id"]: n for v in r["verses"] for n in v["notes"]}
        off = notes[NID_FAMILY_OFF]
        assert off["forced_on"] is True
        assert off["kind_enabled"] is False  # family still off — force-on wins
        assert off["ships"] is True

    def test_force_off_flips_ships(self, yaml_isolation):
        ed = _import_editions()
        web = _import_web()
        ed.api_save_note_override(ED, {"note_id": NID_FAMILY_ON, "state": "off"})
        r = web.api_build_my_bible(ED, "gen", 1)
        notes = {n["note_id"]: n for v in r["verses"] for n in v["notes"]}
        on = notes[NID_FAMILY_ON]
        assert on["disabled"] is True
        assert on["kind_enabled"] is True
        assert on["ships"] is False


# --------------------------------------------------------------------------- #
# Regression: the legacy note-toggle path is unbroken by the helper refactor
# --------------------------------------------------------------------------- #


class TestNoteTogglePathIntact:
    def test_toggle_disable_then_reenable(self, yaml_isolation):
        web = _import_web()
        r = web.api_save_note_toggle(ED, {"note_id": NID_FAMILY_ON, "enabled": False})
        assert r.get("ok"), r
        assert r["disabled_count"] == 1
        e = _edition(ED)
        assert e["disabled_note_ids"] == [NID_FAMILY_ON]

        r = web.api_save_note_toggle(ED, {"note_id": NID_FAMILY_ON, "enabled": True})
        assert r.get("ok"), r
        assert r["disabled_count"] == 0

    def test_toggle_rejects_bad_input(self, yaml_isolation):
        web = _import_web()
        assert "error" in web.api_save_note_toggle(ED, {"note_id": "malformed", "enabled": False})
        assert "error" in web.api_save_note_toggle("not-real", {"note_id": NID_FAMILY_ON, "enabled": False})
        assert "error" in web.api_save_note_toggle(ED, {"note_id": NID_FAMILY_ON, "enabled": "maybe"})

"""σ.4.1 — edition-identity API round-trip tests.

The /customize console lets the builder name their edition (``display_name`` =
the cover subtitle / Your-Edition heading) and set a fixed cover main title
(``cover_main_title``, default "HOLY BIBLE"). This file proves both fields are:

  - editable via ``api_save_edition_meta`` (persist to editions.yaml),
  - surfaced back in ``api_customize_data``'s per-edition record (so the
    console can pre-select the current name), and
  - carried by ``api_clone_edition`` to a clone.

Every test that writes editions.yaml backs it up + restores in a ``finally`` and
clears the config/matrix caches, so ``git status --short content/editions.yaml``
stays clean afterward (the σ-plan edition-mutation isolation rule).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
EDITIONS_YAML = REPO / "content" / "editions.yaml"


def _clear_caches() -> None:
    config.load_editions.cache_clear()
    from scripts.core import matrix as matrix_mod

    matrix_mod.compute_matrix.cache_clear()


# ---------------------------------------------------------------------------
# σ.4.1 — round-trip: POST display_name + cover_main_title, re-read both
# ---------------------------------------------------------------------------


def test_save_and_read_back_display_name_and_cover_main_title(tmp_path):
    from scripts.api.editions import api_save_edition_meta
    from scripts.web import api_customize_data

    backup = tmp_path / "ed.bak"
    shutil.copy(EDITIONS_YAML, backup)
    try:
        _clear_caches()
        res = api_save_edition_meta(
            "catholic-study",
            {"display_name": "My Custom Name", "cover_main_title": "SACRED SCRIPTURE"},
        )
        assert "error" not in res, res
        assert "display_name" in res["updated"]
        assert "cover_main_title" in res["updated"]

        _clear_caches()
        # Persisted to the edition record.
        ed = config.editions_by_id()["catholic-study"]
        assert ed.get("display_name") == "My Custom Name"
        assert ed.get("cover_main_title") == "SACRED SCRIPTURE"

        # Surfaced back through the customize data the console consumes.
        data = api_customize_data()
        rec = {e["id"]: e for e in data["editions"]}["catholic-study"]
        assert rec["display_name"] == "My Custom Name"
        assert rec["cover_main_title"] == "SACRED SCRIPTURE"
    finally:
        shutil.copy(backup, EDITIONS_YAML)
        _clear_caches()


def test_customize_data_surfaces_default_cover_main_title():
    # cover_main_title is unset on disk for catholic-study → the record exposes
    # "" so the console can default the field placeholder to HOLY BIBLE.
    from scripts.web import api_customize_data

    _clear_caches()
    data = api_customize_data()
    rec = {e["id"]: e for e in data["editions"]}["catholic-study"]
    assert "display_name" in rec  # always present (its display_name is set)
    assert "cover_main_title" in rec
    assert isinstance(rec["cover_main_title"], str)


def test_customize_data_surfaces_enabled_categories_for_suggestions():
    # The smart-name suggestions need to know which note families this edition
    # ships, so the per-edition record exposes enabled_categories.
    from scripts.web import api_customize_data

    _clear_caches()
    data = api_customize_data()
    rec = {e["id"]: e for e in data["editions"]}["catholic-study"]
    assert isinstance(rec.get("enabled_categories"), list)
    assert rec["enabled_categories"]  # catholic-study enables several categories


def test_blank_display_name_persists_empty(tmp_path):
    # Leaving the name blank → display_name "" → the cover shows only HOLY BIBLE
    # (no subtitle). The empty string must round-trip, not fall back to title.
    from scripts.api.editions import api_save_edition_meta

    backup = tmp_path / "ed.bak"
    shutil.copy(EDITIONS_YAML, backup)
    try:
        _clear_caches()
        res = api_save_edition_meta("catholic-study", {"display_name": ""})
        assert "error" not in res, res
        _clear_caches()
        ed = config.editions_by_id()["catholic-study"]
        assert ed.get("display_name", "") == ""
    finally:
        shutil.copy(backup, EDITIONS_YAML)
        _clear_caches()


# ---------------------------------------------------------------------------
# σ.4 review fix — the Preview-changes path also recognizes the identity fields
# ---------------------------------------------------------------------------


def test_preview_recognizes_identity_fields():
    # api_preview_edition_changes has its OWN EDITABLE set that didn't include
    # the identity fields → "Preview changes" wrongly listed them as
    # unknown_fields (while a direct Save persisted them fine). They must
    # register as real changes, never as unknown. Read-only (no persistence).
    from scripts.api.editions import api_preview_edition_changes

    _clear_caches()
    res = api_preview_edition_changes(
        "catholic-study",
        {"display_name": "Zzz Brand New Preview Name", "cover_main_title": "ZZZ MAIN TITLE"},
    )
    assert "error" not in res, res
    assert "display_name" not in res.get("unknown_fields", [])
    assert "cover_main_title" not in res.get("unknown_fields", [])
    changed = {c["field"] for c in res["changes"]}
    assert "display_name" in changed
    assert "cover_main_title" in changed


def test_preview_no_drift_from_save_registry():
    # R16 Phase G (#18) — the preview's EDITABLE is now DERIVED from the save
    # registry, so EVERY scalar api_save_edition_meta accepts is previewable (none
    # is mislabeled "silently ignored"). Pins the no-drift invariant.
    from scripts.api.editions import (
        EDITABLE_BOOL_FIELDS,
        EDITABLE_TEXT_FIELDS,
        api_preview_edition_changes,
    )

    _clear_caches()
    payload = {f: "x" for f in EDITABLE_TEXT_FIELDS} | {f: True for f in EDITABLE_BOOL_FIELDS}
    res = api_preview_edition_changes("catholic-study", payload)
    assert "error" not in res, res
    assert not res.get("unknown_fields"), res.get("unknown_fields")


def test_preview_recognizes_previously_dropped_scalar_fields():
    # R16 Phase G (#18) — these were savable but absent from the old hardcoded set.
    from scripts.api.editions import api_preview_edition_changes

    _clear_caches()
    res = api_preview_edition_changes(
        "catholic-study", {"time_filter_ceiling": "1900", "reader_eink_verse_lines": True}
    )
    assert "error" not in res, res
    assert "time_filter_ceiling" not in res.get("unknown_fields", [])
    assert "reader_eink_verse_lines" not in res.get("unknown_fields", [])


def test_customize_data_surfaces_four_presentation_fields():
    # R16 Phase G (#19) — these are saved + build-read but were absent from the
    # api_customize_data loader, so /customize could not display or reset them.
    from scripts.web import api_customize_data

    _clear_caches()
    data = api_customize_data()
    rec = {e["id"]: e for e in data["editions"]}["catholic-study"]
    for k in (
        "chapter_number_format",
        "chapter_number_decoration",
        "note_popup_split_cap",
        "note_popup_split_byte_cap",
    ):
        assert k in rec, k


# ---------------------------------------------------------------------------
# σ.4.1 — clone carries display_name + cover_main_title
# ---------------------------------------------------------------------------


def test_clone_carries_display_name_and_cover_main_title(tmp_path):
    from scripts.api.editions import api_clone_edition, api_save_edition_meta

    backup = tmp_path / "ed.bak"
    shutil.copy(EDITIONS_YAML, backup)
    new_id = "sigma41-clone-test"
    try:
        _clear_caches()
        # Give the source distinctive values to prove they propagate.
        api_save_edition_meta(
            "catholic-study",
            {"display_name": "Source Name For Clone", "cover_main_title": "WORD OF GOD"},
        )
        _clear_caches()
        res = api_clone_edition({"source_id": "catholic-study", "new_id": new_id})
        assert res.get("ok") is True, res
        _clear_caches()
        clone = config.editions_by_id()[new_id]
        assert clone.get("display_name") == "Source Name For Clone"
        assert clone.get("cover_main_title") == "WORD OF GOD"
    finally:
        shutil.copy(backup, EDITIONS_YAML)
        _clear_caches()

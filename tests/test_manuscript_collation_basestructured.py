# tests/test_manuscript_collation_basestructured.py
"""TDD tests for collate_base_structured() — Phase A1.

Primary verses are the BASE witness's own sense-units (no KJV spine).
"""

import importlib
import json

mc = importlib.import_module("scripts.core.manuscript_collation")


def _load(book, chapter):
    """Load both witness records from disk for (book, chapter)."""
    track = "kings" if book in {"1ki", "2ki"} else "samuel"
    gg = json.load(
        open(
            f"content/manuscript/{track}/calibration/{book}{chapter}_witnessGG.json",
            encoding="utf-8",
        )
    )
    cam = json.load(
        open(
            f"content/manuscript/{track}/calibration/{book}{chapter}_witnessCAM_hires.json",
            encoding="utf-8",
        )
    )
    return gg, cam


def test_base_structured_primary_is_base_witness_units():
    gg, cam = _load("1ki", 6)
    out = mc.collate_base_structured(gg, cam, book="1ki", chapter=6)
    assert out["base_witness"] == "CAM"
    assert len(out["primary_verses"]) == 33  # CAM's own units, not 38 KJV
    assert all(v["geez_text"] for v in out["primary_verses"])  # no empty rows


def test_token_conservation_base_structured():
    gg, cam = _load("1ki", 6)
    out = mc.collate_base_structured(gg, cam, book="1ki", chapter=6)
    assert mc.tokens_conserved(out, gg, cam)  # GG 433==433, CAM 500==500


def test_apparatus_present_with_valid_classes():
    gg, cam = _load("1ki", 6)
    out = mc.collate_base_structured(gg, cam, book="1ki", chapter=6)
    valid = {"agree", "disagree", "lacuna", "insertion"}
    for pv in out["primary_verses"]:
        assert "apparatus" in pv and isinstance(pv["apparatus"], list)
        for cell in pv["apparatus"]:
            assert set(cell) == {"base", "other", "class"}
            assert cell["class"] in valid


def test_metrics_are_geez_internal_no_kjv_gate():
    gg, cam = _load("1ki", 6)
    out = mc.collate_base_structured(gg, cam, book="1ki", chapter=6)
    m = out["metrics"]
    assert isinstance(m["witness_agreement_pct"], float)
    assert set(m["lacuna_counts"]) == {"gg", "cam"}
    assert m["kjv_coverage"] is None  # informative, not computed yet
    assert "semantic_pass_pct" not in m and "semantic_pass_basis" not in m  # no KJV gate


def test_recension_shorter_chapter_not_failed():
    gg, cam = _load("1ki", 6)
    out = mc.collate_base_structured(gg, cam, book="1ki", chapter=6)
    ok, reasons = mc.base_structured_ok(out, gg, cam)
    assert ok, reasons  # 1ki6 (CAM 33 / GG 18) is NOT a fail

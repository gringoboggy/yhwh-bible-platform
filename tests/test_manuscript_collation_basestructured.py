# tests/test_manuscript_collation_basestructured.py
"""TDD tests for collate_base_structured() — Phase A1.

Primary verses are the BASE witness's own sense-units (no KJV spine).
"""

import importlib
import json
import subprocess

import pytest

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


# ──────────────────────────────────────────────────────────────────────────────
#  Phase A4 — 10 re-collated v2 files + immutability gate
# ──────────────────────────────────────────────────────────────────────────────

DONE = [
    ("1ki", 1),
    ("1ki", 2),
    ("1ki", 3),
    ("1ki", 4),
    ("1ki", 5),
    ("1ki", 6),
    ("1sa", 1),
    ("1sa", 3),
    ("1sa", 17),
    ("2sa", 11),
]


def _v2_path(book, chapter):
    track = "kings" if book in {"1ki", "2ki"} else "samuel"
    return f"content/manuscript/{track}/collation/{book}{chapter}_collation_v2.json"


@pytest.mark.parametrize("book,chapter", DONE)
def test_v2_collation_exists_and_honest(book, chapter):
    import os

    p = _v2_path(book, chapter)
    assert os.path.exists(p), f"missing {p}"
    out = json.load(open(p, encoding="utf-8"))
    assert out["book"] == book and out["chapter"] == chapter
    assert out["base_witness"] in {"CAM", "GG"}
    assert out["primary_verses"] and all("apparatus" in pv for pv in out["primary_verses"])
    assert "metrics" in out and out["metrics"]["kjv_coverage"] is None
    gg, cam = _load(book, chapter)
    ok, reasons = mc.base_structured_ok(out, gg, cam)
    assert ok, f"{book}{chapter} honesty gate: {reasons}"  # 0 fabrication, honest lacunae


def test_samuel_kings_calibration_byte_stable_vs_head():
    r = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            "HEAD",
            "--",
            "content/manuscript/samuel/calibration",
            "content/manuscript/kings/calibration",
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert r.returncode == 0, f"calibration witnesses/goldens changed vs HEAD:\n{r.stdout}{r.stderr}"


# ──────────────────────────────────────────────────────────────────────────────
#  Phase A5 — token-extent fix for _pick_base (1ki2 GG→CAM)
# ──────────────────────────────────────────────────────────────────────────────


def test_pick_base_uses_token_extent_not_unit_count():
    # Segmentation, NOT extent: GG many short units, CAM few long units, EQUAL tokens
    # -> must NOT flip to GG; clause-2 decision-of-record -> CAM.
    gg = {"verses": [{"tokens": ["a", "b"]} for _ in range(6)]}  # 6 units / 12 tokens
    cam = {
        "verses": [
            {"tokens": ["a", "b", "c", "d", "e", "f"]},  # 2 units / 12 tokens
            {"tokens": ["g", "h", "i", "j", "k", "l"]},
        ]
    }
    base, rationale = mc._pick_base(gg, cam)
    assert base == "CAM", rationale
    # Real extent: GG materially MORE tokens -> clause-1 picks GG.
    gg2 = {"verses": [{"tokens": ["x"] * 100}]}  # 100 tokens
    cam2 = {"verses": [{"tokens": ["y"] * 20}]}  # 20 tokens (< 0.70*100)
    base2, _ = mc._pick_base(gg2, cam2)
    assert base2 == "GG"


def test_1ki2_base_is_cam_after_token_extent_fix():
    gg, cam = _load("1ki", 2)
    out = mc.collate_base_structured(gg, cam, book="1ki", chapter=2)
    assert out["base_witness"] == "CAM"  # was GG under the old unit-count rule
    assert len(out["primary_verses"]) == 27  # CAM's own 27 units (not GG's 46)
    assert mc.base_structured_ok(out, gg, cam)[0]

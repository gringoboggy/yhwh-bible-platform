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

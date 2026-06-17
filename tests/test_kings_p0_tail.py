"""Kings P0 tail — 1ki 19–22 + 2ki 1–25 folio slots filled."""

from __future__ import annotations

from scripts.core import manuscript_manifest as mm


class TestKingsP0Tail:
    def test_1ki_19_through_22_have_both_witness_folios(self):
        man = mm.load_manifest(track="kings")
        for ch in range(19, 23):
            e = mm.chapter_entry(man, "1ki", ch)
            assert e is not None
            assert (e.get("CAM") or {}).get("folios")
            assert (e.get("GG") or {}).get("folios")

    def test_2ki_1_through_25_have_both_witness_folios(self):
        man = mm.load_manifest(track="kings")
        for ch in range(1, 26):
            e = mm.chapter_entry(man, "2ki", ch)
            assert e is not None
            assert (e.get("CAM") or {}).get("folios")
            assert (e.get("GG") or {}).get("folios")

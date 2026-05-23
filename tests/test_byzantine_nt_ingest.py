"""Phase 2 — Greek NT ingestion (Robinson-Pierpont Byzantine Majority Text).

Source: byztxt/byzantine-majority-text, csv-unicode/ccat/no-variants/*.csv — accented
polytonic Greek Unicode, Public Domain (Unlicense). Versification is KJV-standard
(near-identity): all 27 chapter counts match; the single-verse Byzantine omissions
(Luke 17:36, Acts 8:37/15:34/24:7) are GAP-PRESERVED (KJV numbering kept, verse
absent), so identity is clean. The one reorder is the Romans doxology — the
Byzantine text places KJV 16:25-27 at the end of chapter 14 (as 14:24-26).
"""

from __future__ import annotations

from pathlib import Path

import pytest

FX_BYZ = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "byzantine_sample"


class TestByzantineToKjvBookMapAndIdentity:
    @pytest.mark.parametrize(
        "book,ch,vs,expected",
        [
            ("MAT", 1, 1, ("mat", 1, 1)),
            ("MAR", 1, 1, ("mrk", 1, 1)),
            ("LUK", 1, 1, ("luk", 1, 1)),
            ("JOH", 3, 16, ("jhn", 3, 16)),
            ("ACT", 1, 1, ("act", 1, 1)),
            ("1CO", 13, 1, ("1co", 13, 1)),
            ("JAM", 1, 1, ("jam", 1, 1)),
            ("JUD", 1, 1, ("jud", 1, 1)),
            ("REV", 22, 21, ("rev", 22, 21)),
        ],
    )
    def test_identity_books(self, book, ch, vs, expected):
        from scripts.core.versification import byzantine_to_kjv

        assert byzantine_to_kjv(book, ch, vs) == expected

    @pytest.mark.parametrize("book", ["ACT24", "PA", "GEN", "PSA", "MT", "RE"])
    def test_non_nt_and_apparatus_files_omitted(self, book):
        """The Pericope-Adulterae apparatus file, the Acts-24 variant, OT books, and
        the Scrivener-style codes (MT/RE) are not in the byztxt CSV map -> None."""
        from scripts.core.versification import byzantine_to_kjv

        assert byzantine_to_kjv(book, 1, 1) is None

    def test_gap_preserved_omissions_stay_identity(self):
        """RP omits Luke 17:36 / Acts 8:37 etc. but KEEPS KJV numbering (gap), so the
        following verses map identity, not shifted."""
        from scripts.core.versification import byzantine_to_kjv

        assert byzantine_to_kjv("LUK", 17, 37) == ("luk", 17, 37)
        assert byzantine_to_kjv("ACT", 8, 38) == ("act", 8, 38)

    def test_out_of_extent_guarded(self):
        from scripts.core.versification import byzantine_to_kjv

        assert byzantine_to_kjv("MAT", 1, 99) is None
        assert byzantine_to_kjv("ROM", 17, 1) is None  # Romans has 16 chapters


class TestByzantineToKjvRomansDoxology:
    @pytest.mark.parametrize(
        "ch,vs,expected",
        [
            (14, 23, ("rom", 14, 23)),  # identity up to 14:23
            (14, 24, ("rom", 16, 25)),  # doxology relocated from end of ch14
            (14, 25, ("rom", 16, 26)),
            (14, 26, ("rom", 16, 27)),
            (16, 1, ("rom", 16, 1)),  # ch16 body identity
            (16, 24, ("rom", 16, 24)),
            (1, 1, ("rom", 1, 1)),  # untouched chapters identity
            (15, 33, ("rom", 15, 33)),
        ],
    )
    def test_doxology_reorder(self, ch, vs, expected):
        from scripts.core.versification import byzantine_to_kjv

        assert byzantine_to_kjv("ROM", ch, vs) == expected


class TestByzantineDriver:
    def test_clean_greek_nt_strips_pilcrow_and_collapses_ws(self):
        from scripts.extract_byzantine_nt import _clean_greek_nt

        assert _clean_greek_nt("¶Τῷ δὲ  δυναμένῳ") == "Τῷ δὲ δυναμένῳ"
        assert _clean_greek_nt("χάρις ὑμῖν καὶ εἰρήνη") == "χάρις ὑμῖν καὶ εἰρήνη"

    def test_build_verses_maps_romans_doxology_and_strips_marker(self):
        from scripts.extract_byzantine_nt import build_verses

        by_code, stats = build_verses(FX_BYZ)
        assert "rom" in by_code
        coords = {(c, v) for c, v, _ in by_code["rom"]}
        # 14:24-26 relocate to 16:25-27; 14:23 + 16:1 + 16:24 stay
        assert coords == {(14, 23), (16, 1), (16, 24), (16, 25), (16, 26), (16, 27)}
        assert by_code["rom"] == sorted(by_code["rom"])
        dox = next(t for c, v, t in by_code["rom"] if (c, v) == (16, 25))
        assert dox.startswith("Τῷ δὲ δυναμένῳ") and "¶" not in dox  # marker stripped
        assert stats["collisions"] == 0

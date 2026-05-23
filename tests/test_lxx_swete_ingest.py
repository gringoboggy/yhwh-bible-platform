"""Phase 2 — LXX Greek ingestion (Swete 1909-1930, via the eliranwong digitization).

PD basis: Swete's text is public domain by age (d. 1917; editions 1907-1930). Only
the public-domain Greek TEXT (the ``00`` verse refs + ``01`` words) is extracted;
eliranwong's GPL-licensed additions (SBL transliteration ``03``, morphology,
pronunciation) are NOT used. See ATTRIBUTIONS.md for the provenance chain.

Reconstruction characterization: the Swete source stores the text as a flat word
list (``01-Swete_word_with_punctuations.csv``: ``word_id -> word``) plus a
versification index (``00-Swete_versification.csv``: ``word_id -> Book.Ch:Vs``
giving each verse's first word). A verse is the words from its start id up to (not
including) the next verse's start id, space-joined. Greek is stored PLAIN (not
em-per-word — matching the recovered base + the Brenton seed). The expected fixture
was auto-reconstructed from the real source slice, not hand-transcribed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
FX = REPO / "tests" / "fixtures"
FX_VERS = FX / "swete_gen_versification.tsv"
FX_WORDS = FX / "swete_gen_words.tsv"
FX_EXPECTED = FX / "swete_gen_expected.json"

_EXPECTED = json.loads(FX_EXPECTED.read_text(encoding="utf-8"))


@pytest.mark.parametrize("ref", sorted(_EXPECTED))
def test_reconstruct_verse_text_from_word_list(ref):
    """Each verse = its words (start-id .. next-start-id) joined by single spaces,
    reproducing the Swete source's plain Greek with attached punctuation."""
    from scripts.extract_lxx_swete import parse_versification, parse_words, reconstruct

    vers = parse_versification(FX_VERS)
    words = parse_words(FX_WORDS)
    got = dict(reconstruct(vers, words))
    assert got[ref] == _EXPECTED[ref]


def test_reconstruct_is_plain_greek_not_em_wrapped():
    """LXX Greek is plain text (space-joined), NOT the em-per-word markup WLC uses
    — matching the recovered base's vnote-greek format."""
    from scripts.extract_lxx_swete import parse_versification, parse_words, reconstruct

    got = dict(reconstruct(parse_versification(FX_VERS), parse_words(FX_WORDS)))
    assert "<em>" not in got["Gen.1:1"]
    assert got["Gen.1:1"].startswith("ΕΝ ΑΡΧΗ")  # Swete caps the opening words


# ---------------------------------------------------------------------------
# LXX (Swete) -> canonical KJV versification map: scripts.core.versification.
# Expected values were derived by content-aligning the real Swete source against
# the KJV text (the OAN proper nouns, the Daniel-3 seams, the Psalm titles, the
# Proverbs Agur/Lemuel relocations) — see dev/CHANGELOG.md 2026-05-23. NOT memory.
# ---------------------------------------------------------------------------


class TestLxxSweteToKjvBookMapAndIdentity:
    def test_identity_books_map_straight_through(self):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Gen", 1, 1) == ("gen", 1, 1)
        assert lxx_swete_to_kjv("Isa", 1, 1) == ("isa", 1, 1)
        assert lxx_swete_to_kjv("Sol", 1, 1) == ("sng", 1, 1)  # Song of Songs
        assert lxx_swete_to_kjv("Dat", 1, 1) == ("dan", 1, 1)  # Theodotion Daniel

    @pytest.mark.parametrize("book", ["Wis", "Sir", "1Es", "Tob", "Jdt", "Bar", "Pss", "1En", "Ode", "3Ma"])
    def test_non_39_ot_books_omitted(self, book):
        """Deuterocanon / recension-dups / Greek-1En are out of scope this pass -> None."""
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv(book, 1, 1) is None

    def test_out_of_canonical_extent_is_guarded_to_none(self):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Gen", 1, 99) is None  # Gen 1 has 31 verses
        assert lxx_swete_to_kjv("Gen", 51, 1) is None  # Gen has 50 chapters


class TestLxxSweteToKjvPsalms:
    @pytest.mark.parametrize(
        "lxx_ch,lxx_v,expected",
        [
            (1, 1, ("psa", 1, 1)),  # offset 0
            (3, 1, None),  # superscription title dropped
            (3, 2, ("psa", 3, 1)),  # offset 1
            (10, 1, ("psa", 11, 1)),  # +1 chapter, offset 0
            (11, 1, None),
            (11, 2, ("psa", 12, 1)),  # +1 chapter + 1 superscription
            (116, 1, ("psa", 117, 1)),  # +1 chapter, offset 0
            (118, 1, ("psa", 119, 1)),  # the 176-verse psalm
            (148, 1, ("psa", 148, 1)),  # same number again
            (150, 6, ("psa", 150, 6)),
            (151, 1, None),  # LXX Ps 151 omitted (not in KJV)
        ],
    )
    def test_chapter_shift_and_superscription(self, lxx_ch, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Psa", lxx_ch, lxx_v) == expected

    @pytest.mark.parametrize(
        "lxx_v,expected",
        [(1, None), (2, ("psa", 9, 1)), (21, ("psa", 9, 20)), (22, ("psa", 10, 1)), (39, ("psa", 10, 18))],
    )
    def test_lxx_9_merges_kjv_9_and_10(self, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Psa", 9, lxx_v) == expected

    @pytest.mark.parametrize(
        "lxx_v,expected",
        [(1, ("psa", 114, 1)), (8, ("psa", 114, 8)), (9, ("psa", 115, 1)), (26, ("psa", 115, 18))],
    )
    def test_lxx_113_merges_kjv_114_and_115(self, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Psa", 113, lxx_v) == expected

    def test_lxx_114_115_split_into_kjv_116(self):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Psa", 114, 1) == ("psa", 116, 1)
        assert lxx_swete_to_kjv("Psa", 114, 9) == ("psa", 116, 9)
        assert lxx_swete_to_kjv("Psa", 115, 1) == ("psa", 116, 10)
        assert lxx_swete_to_kjv("Psa", 115, 10) == ("psa", 116, 19)

    def test_lxx_146_147_split_into_kjv_147(self):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Psa", 146, 1) == ("psa", 147, 1)
        assert lxx_swete_to_kjv("Psa", 146, 11) == ("psa", 147, 11)
        assert lxx_swete_to_kjv("Psa", 147, 1) == ("psa", 147, 12)
        assert lxx_swete_to_kjv("Psa", 147, 9) == ("psa", 147, 20)

    @pytest.mark.parametrize("lxx_ch,kjv_ch", [(50, 51), (51, 52), (53, 54), (59, 60)])
    def test_two_verse_superscriptions_drop_two(self, lxx_ch, kjv_ch):
        """Pss 50/51/53/59 carry a 2-line title in the LXX -> drop 2, body starts at v3."""
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Psa", lxx_ch, 1) is None
        assert lxx_swete_to_kjv("Psa", lxx_ch, 2) is None
        assert lxx_swete_to_kjv("Psa", lxx_ch, 3) == ("psa", kjv_ch, 1)


class TestLxxSweteToKjvDaniel:
    @pytest.mark.parametrize(
        "lxx_ch,lxx_v,expected",
        [
            (2, 1, ("dan", 2, 1)),  # identity
            (3, 23, ("dan", 3, 23)),  # pre-Addition
            (3, 24, None),  # Prayer of Azariah begins (Addition)
            (3, 90, None),  # Song of the Three ends (Addition)
            (3, 91, ("dan", 3, 24)),  # narrative resumes
            (3, 97, ("dan", 3, 30)),
            (3, 98, ("dan", 4, 1)),  # doxology = KJV 4:1-3
            (3, 100, ("dan", 4, 3)),
            (4, 1, ("dan", 4, 4)),  # +3 offset through ch4
            (4, 34, ("dan", 4, 37)),
            (5, 1, ("dan", 5, 1)),  # identity again
        ],
    )
    def test_theodotion_daniel_additions(self, lxx_ch, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Dat", lxx_ch, lxx_v) == expected


class TestLxxSweteToKjvJeremiah:
    @pytest.mark.parametrize(
        "lxx_ch,lxx_v,expected",
        [
            (1, 1, ("jer", 1, 1)),  # identity 1-24
            (24, 1, ("jer", 24, 1)),
            (52, 1, ("jer", 52, 1)),  # identity tail
            (25, 13, ("jer", 25, 13)),
            (25, 14, None),  # general OAN super-heading
            (25, 15, ("jer", 49, 35)),  # Elam body
            (25, 19, ("jer", 49, 39)),
            (26, 1, ("jer", 49, 34)),  # Elam dating colophon
            (26, 2, ("jer", 46, 2)),  # Egypt
            (26, 28, ("jer", 46, 28)),
            (27, 1, ("jer", 50, 1)),  # Babylon
            (28, 1, ("jer", 51, 1)),  # Babylon
            (29, 1, ("jer", 47, 1)),  # Philistines
            (29, 7, ("jer", 47, 7)),
            (29, 8, ("jer", 49, 7)),  # Edom
            (29, 23, ("jer", 49, 22)),
            (30, 1, ("jer", 49, 1)),  # Ammon
            (30, 5, ("jer", 49, 5)),
            (30, 6, ("jer", 49, 28)),  # Kedar
            (30, 11, ("jer", 49, 33)),
            (30, 12, ("jer", 49, 23)),  # Damascus
            (30, 16, ("jer", 49, 27)),
            (31, 1, ("jer", 48, 1)),  # Moab
            (31, 44, ("jer", 48, 44)),
            (32, 1, ("jer", 25, 15)),  # cup of wrath
            (32, 24, ("jer", 25, 38)),
            (33, 1, ("jer", 26, 1)),
            (37, 1, ("jer", 30, 1)),  # mid relocation, no internal reorder
            (51, 30, ("jer", 44, 30)),
            (51, 31, ("jer", 45, 1)),  # Baruch
            (51, 35, ("jer", 45, 5)),
        ],
    )
    def test_oan_reorder(self, lxx_ch, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Jer", lxx_ch, lxx_v) == expected

    @pytest.mark.parametrize(
        "lxx_v,expected",
        [
            (1, ("jer", 27, 2)),
            (5, ("jer", 27, 6)),
            (6, ("jer", 27, 8)),  # MT 27:7 is a LXX-minus
            (13, ("jer", 27, 16)),
            (14, None),  # "I did not send them" doublet -> omit
            (15, ("jer", 27, 18)),
            (18, ("jer", 27, 22)),
        ],
    )
    def test_lxx_34_to_mt_27_scattered_pluses(self, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Jer", 34, lxx_v) == expected


class TestLxxSweteToKjv1KingsSwap:
    @pytest.mark.parametrize(
        "lxx_ch,lxx_v,expected",
        [
            (1, 1, ("1ki", 1, 1)),  # identity
            (19, 1, ("1ki", 19, 1)),
            (20, 1, ("1ki", 21, 1)),  # Naboth's vineyard = KJV 21
            (20, 29, ("1ki", 21, 29)),
            (21, 1, ("1ki", 20, 1)),  # Ben-hadad = KJV 20
            (21, 43, ("1ki", 20, 43)),
            (22, 1, ("1ki", 22, 1)),  # identity
        ],
    )
    def test_20_21_swap(self, lxx_ch, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("1Ki", lxx_ch, lxx_v) == expected


class TestLxxSweteToKjvEsther:
    @pytest.mark.parametrize("ch,vs", [(1, 1), (3, 13), (4, 17), (5, 1), (8, 12), (10, 3)])
    def test_addition_verses_omitted(self, ch, vs):
        """The six Greek Esther Additions are packed into these single verses -> omit."""
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Est", ch, vs) is None

    @pytest.mark.parametrize("ch,vs", [(1, 2), (2, 5), (3, 1), (9, 1), (10, 1)])
    def test_canonical_verses_identity(self, ch, vs):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Est", ch, vs) == ("est", ch, vs)


class TestLxxSweteToKjvProverbs:
    @pytest.mark.parametrize(
        "lxx_ch,lxx_v,expected",
        [
            (1, 1, ("pro", 1, 1)),  # identity
            (23, 1, ("pro", 23, 1)),
            (24, 1, ("pro", 24, 1)),  # 24:1-22 identity
            (24, 22, ("pro", 24, 22)),
            (24, 23, None),  # transitional, dropped
            (24, 24, ("pro", 30, 1)),  # Agur part 1
            (24, 37, ("pro", 30, 14)),
            (24, 38, ("pro", 24, 23)),  # words of the wise
            (24, 49, ("pro", 24, 34)),
            (24, 50, ("pro", 30, 15)),  # Agur part 2
            (24, 68, ("pro", 30, 33)),
            (24, 69, ("pro", 31, 1)),  # Lemuel part 1
            (24, 77, ("pro", 31, 9)),
            (25, 1, ("pro", 25, 1)),  # identity 25-28
            (28, 1, ("pro", 28, 1)),
            (29, 1, ("pro", 29, 1)),  # 29:1-27 identity
            (29, 27, ("pro", 29, 27)),
            (29, 28, ("pro", 31, 10)),  # the virtuous-woman acrostic
            (29, 49, ("pro", 31, 31)),
        ],
    )
    def test_proverbs_reorder(self, lxx_ch, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Pro", lxx_ch, lxx_v) == expected


class TestLxxSweteToKjvExodus:
    @pytest.mark.parametrize("ch,vs", [(1, 1), (35, 1), (40, 1)])
    def test_non_tabernacle_identity(self, ch, vs):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Exo", ch, vs) == ("exo", ch, vs)

    @pytest.mark.parametrize("ch", [36, 37, 38, 39])
    def test_tabernacle_chapters_deferred(self, ch):
        """LXX Exo 36-39 (tabernacle) is reordered AND heavily abbreviated -> deferred
        (omit rather than ship a guessed/wrong alignment)."""
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Exo", ch, 1) is None


class TestBuildVerses:
    def test_parse_ref(self):
        from scripts.extract_lxx_swete import parse_ref

        assert parse_ref("Gen.1:1") == ("Gen", 1, 1)
        assert parse_ref("1Ki.20:5") == ("1Ki", 20, 5)

    def test_clean_greek_strips_editorial_sigla_and_markers(self):
        """Swete's critical sigla (⸀⸂⸆…) and the digitization's [n] verse markers
        are editorial noise — strip them and collapse the resulting whitespace."""
        from scripts.extract_lxx_swete import _clean_greek

        assert _clean_greek("ἐπὶ τῶν κλειδῶν ⸂⸆⸃ τὸ πρωὶ") == "ἐπὶ τῶν κλειδῶν τὸ πρωὶ"
        assert _clean_greek("⸂[1] ΕΤΟΥΣ δευτέρου") == "ΕΤΟΥΣ δευτέρου"
        assert _clean_greek("ΕΝ ΑΡΧΗ ἐποίησεν ὁ θεός") == "ΕΝ ΑΡΧΗ ἐποίησεν ὁ θεός"  # clean text untouched

    def test_build_verses_groups_by_code_at_canonical_coords(self):
        """The driver reconstructs, remaps to canonical coords, and groups by project
        code with verses sorted; Greek stays plain (no em-wrapping)."""
        from scripts.extract_lxx_swete import build_verses

        by_code, stats = build_verses(FX_VERS, FX_WORDS)
        assert "gen" in by_code
        coords = {(c, v) for c, v, _ in by_code["gen"]}
        assert (1, 1) in coords
        assert by_code["gen"] == sorted(by_code["gen"])  # sorted by (ch, vs)
        text11 = next(t for c, v, t in by_code["gen"] if (c, v) == (1, 1))
        assert text11.startswith("ΕΝ ΑΡΧΗ") and "<em>" not in text11
        assert stats["written"] >= 1 and stats["collisions"] == 0

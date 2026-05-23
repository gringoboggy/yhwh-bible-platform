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

    @pytest.mark.parametrize(
        "book",
        # Still-deferred deuterocanon (need verified reorder tables — measured
        # divergences recorded in dev/PLAN_2026-05-21.md): Sir (30-36 Greek
        # transposition), 1Es (scattered intra-chapter divisions), Tob (ch6/7
        # boundary), Jdt (ch16 split+merge). Plus: recension-dups not used
        # (Tbs Tobit-long, Sus/Bel Old-Greek vs the Theodotion Sut/Bet we ship,
        # Dan Old-Greek vs Dat); no-base-home books (Pss Psalms-of-Solomon,
        # 1Ma-4Ma, Ode — though man/paz come from Ode/Dat respectively, both
        # deferred); 1En (no KJV skeleton + base render gap).
        ["Tbs", "Pss", "1En", "Ode", "1Ma", "2Ma", "3Ma", "4Ma", "Sus", "Bel", "Dan"],
    )
    def test_deferred_and_unused_books_omitted(self, book):
        """Books not yet in scope this pass map to None (deferred or no base home)."""
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
            (3, 24, ("paz", 1, 1)),  # Prayer of Azariah begins → relocated to paz (not dan)
            (3, 90, ("paz", 1, 68)),  # Song of the Three ends → paz (see TestLxxSwetePrayerOfAzariah)
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


class TestLxxSweteDeuterocanonIdentity:
    """Deuterocanon books whose Swete versification matches the KJV skeleton
    EXACTLY — verified by interior content-alignment (not just endpoints; the
    Judith-16 split+merge proved exact-count can hide an internal shift). wis is
    originally-Greek; sus/bel use the Theodotion recension (Sut/Bet) the KJV/
    Vulgate tradition follows (the Old-Greek Sus=60/Bel match differently)."""

    @pytest.mark.parametrize(
        "swete_book,ch,vs,expected",
        [
            # Wisdom — verified at ch starts AND ends across 1/2/6/7/10/13/16/18/19
            ("Wis", 1, 1, ("wis", 1, 1)),
            ("Wis", 2, 24, ("wis", 2, 24)),
            ("Wis", 10, 21, ("wis", 10, 21)),
            ("Wis", 16, 29, ("wis", 16, 29)),
            ("Wis", 19, 22, ("wis", 19, 22)),
            ("Wis", 19, 23, None),  # out of extent (wis 19 has 22 verses)
            # Susanna (Theodotion Sut) — verified at 1/15/30/45/60/64
            ("Sut", 1, 1, ("sus", 1, 1)),
            ("Sut", 1, 30, ("sus", 1, 30)),
            ("Sut", 1, 64, ("sus", 1, 64)),
            ("Sut", 1, 65, None),  # out of extent (sus has 64)
            # Bel & the Dragon (Theodotion Bet) — verified at 1/10/20/31/42
            ("Bet", 1, 1, ("bel", 1, 1)),
            ("Bet", 1, 20, ("bel", 1, 20)),
            ("Bet", 1, 42, ("bel", 1, 42)),
            ("Bet", 1, 43, None),  # out of extent (bel has 42)
        ],
    )
    def test_identity_deutero(self, swete_book, ch, vs, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv(swete_book, ch, vs) == expected


class TestLxxSweteBaruch:
    """Baruch ch1/2/4/5 are identity (exact counts; Greek 4:1 aligns); ch3 has ONE
    verified split: KJV 3:34 ("stars shined... when he calleth them, they say,
    Here we be...") = Greek 3:34 + 3:35 combined, so KJV 3:35-37 = Greek 3:36-38."""

    @pytest.mark.parametrize(
        "lxx_ch,lxx_v,expected",
        [
            (1, 1, ("bar", 1, 1)),  # identity ch1
            (2, 35, ("bar", 2, 35)),  # identity ch2 (last)
            (3, 1, ("bar", 3, 1)),  # identity within ch3 head
            (3, 33, ("bar", 3, 33)),  # last identity verse before the split
            (3, 34, ("bar", 3, 34)),  # Greek 3:34 = first clause of KJV 3:34
            (3, 35, ("bar", 3, 34)),  # Greek 3:35 = second clause of KJV 3:34 -> concatenated onto 3:34
            (3, 36, ("bar", 3, 35)),  # "This is our God"
            (3, 37, ("bar", 3, 36)),  # "found out all the way of knowledge"
            (3, 38, ("bar", 3, 37)),  # "Afterward did he shew himself upon earth"
            (4, 1, ("bar", 4, 1)),  # identity resumes ch4
            (5, 9, ("bar", 5, 9)),  # identity ch5 (last)
        ],
    )
    def test_baruch_ch3_split(self, lxx_ch, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Bar", lxx_ch, lxx_v) == expected


class TestLxxSweteLetterOfJeremiah:
    """The Letter of Jeremiah (Swete ``Epj`` -> ``lje``) is a single chapter with
    ONE verified split at the head: KJV 1:1 + 1:2 = Greek G1 (the heading absorbs
    the 'because of your sins' statement), then a uniform +1 offset across all 72
    Greek verses (verified at G2/G6/G35/G59/G72 vs the KJV English)."""

    @pytest.mark.parametrize(
        "lxx_v,expected",
        [
            (1, ("lje", 1, 1)),  # G1 -> KJV 1:1 (KJV 1:2 absorbed; no own Greek)
            (2, ("lje", 1, 3)),  # offset +1 begins ("when ye come to Babylon...")
            (6, ("lje", 1, 7)),  # "mine angel is with you"
            (35, ("lje", 1, 36)),  # "save no man from death"
            (59, ("lje", 1, 60)),  # "sun, moon, and stars... obedient"
            (72, ("lje", 1, 73)),  # last verse "Better... the just man"
            (73, None),  # no Greek 1:73 (Greek has 72) -> out of source
        ],
    )
    def test_epj_single_head_split(self, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Epj", 1, lxx_v) == expected

    def test_kjv_1_2_has_no_greek_source(self):
        """KJV lje 1:2 is folded into Greek G1, so nothing maps onto it (KJV 1:2
        gets no Greek popup; KJV 1:1 carries the Greek heading)."""
        from scripts.core.versification import lxx_swete_to_kjv

        # No Epj verse maps to (lje, 1, 2):
        hits = [v for v in range(1, 73) if lxx_swete_to_kjv("Epj", 1, v) == ("lje", 1, 2)]
        assert hits == []


class TestLxxSweteSirach:
    """Sirach — the Greek 30:25–36:16a block transposition + internal verse-merges,
    all derived by content-aligning the real Swete text against the KJV (not memory).
    Greek→KJV: G30:1-24=30; G30:25-40=33:16-31; G31=34 (5 merges); G32=35 (6 merges);
    G33:1-13=36:1-11 (2 merges); G34=31; G35=32; G36:1-15=33:1-15; G36:16 conflated
    seam→omit; G36:17-31=36:12-26. Each LXX-split verse's 2nd half is concatenated
    onto its canonical coord (popup shows the whole verse). Minors ch20/23/41 all
    identity (each Greek-fewer with only terminal KJV extras: KJV 20:32, 23:28,
    41:23-24 have no Greek)."""

    @pytest.mark.parametrize(
        "lxx_ch,lxx_v,expected",
        [
            # identity outside the transposition
            (1, 1, ("sir", 1, 1)),
            (29, 28, ("sir", 29, 28)),
            (37, 1, ("sir", 37, 1)),  # identity resumes cleanly after the swap
            (51, 30, ("sir", 51, 30)),
            # ch30: 1-24 identity (Greek 30:24 absorbs KJV 30:25); 25-40 → KJV 33:16-31
            (30, 1, ("sir", 30, 1)),
            (30, 24, ("sir", 30, 24)),
            (30, 25, ("sir", 33, 16)),  # "as one that gathereth after the grapegatherers"
            (30, 33, ("sir", 33, 24)),
            (30, 40, ("sir", 33, 31)),
            # ch31 → KJV 34, merges at G31:11/15/18/22/27 (2nd halves concatenated)
            (31, 1, ("sir", 34, 1)),
            (31, 10, ("sir", 34, 10)),
            (31, 11, ("sir", 34, 10)),  # 2nd half -> concatenated onto KJV 34:10
            (31, 12, ("sir", 34, 11)),
            (31, 15, ("sir", 34, 13)),  # -> concatenated onto 34:13
            (31, 16, ("sir", 34, 14)),
            (31, 18, ("sir", 34, 15)),  # -> concatenated onto 34:15
            (31, 19, ("sir", 34, 16)),
            (31, 31, ("sir", 34, 26)),
            # ch32 → KJV 35, merges at G32:2/4/15/19/23/25 (concatenated)
            (32, 1, ("sir", 35, 1)),
            (32, 2, ("sir", 35, 1)),  # 2nd half -> concatenated onto KJV 35:1
            (32, 3, ("sir", 35, 2)),
            (32, 5, ("sir", 35, 3)),
            (32, 14, ("sir", 35, 12)),
            (32, 26, ("sir", 35, 20)),
            # ch33:1-13 → KJV 36:1-11, merges at G33:7/9 (concatenated)
            (33, 1, ("sir", 36, 1)),
            (33, 6, ("sir", 36, 6)),
            (33, 7, ("sir", 36, 6)),  # 2nd half -> concatenated onto KJV 36:6
            (33, 8, ("sir", 36, 7)),
            (33, 13, ("sir", 36, 11)),
            # ch34 → KJV 31, ch35 → KJV 32 (clean whole-chapter relocations)
            (34, 1, ("sir", 31, 1)),
            (34, 31, ("sir", 31, 31)),
            (35, 1, ("sir", 32, 1)),
            (35, 24, ("sir", 32, 24)),
            # ch36: 1-15 → KJV 33:1-15; 16 conflated seam → omit; 17-31 → KJV 36:12-26
            (36, 1, ("sir", 33, 1)),
            (36, 15, ("sir", 33, 15)),
            (36, 16, None),
            (36, 17, ("sir", 36, 12)),
            (36, 31, ("sir", 36, 26)),
            # minors: ch20/23/41 all identity (Greek-fewer with terminal KJV extras)
            (20, 1, ("sir", 20, 1)),
            (20, 31, ("sir", 20, 31)),
            (23, 1, ("sir", 23, 1)),
            (23, 27, ("sir", 23, 27)),
            (41, 1, ("sir", 41, 1)),
            (41, 19, ("sir", 41, 19)),
            (41, 20, ("sir", 41, 20)),  # litany aligns 1:1 — included, not omitted
            (41, 22, ("sir", 41, 22)),  # last Greek verse; KJV 41:23-24 are terminal extras
        ],
    )
    def test_sirach_transposition_and_minors(self, lxx_ch, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Sir", lxx_ch, lxx_v) == expected


class TestLxxSweteTobit:
    """Tobit (short recension Tob→tob). ch1-5, 8-14 identity (verified first+last).
    ch6 is a clean offset −1: Greek 6:1 ("she ceased weeping") = the tail of KJV
    5:22 (concatenated), then Greek 6:2-18 → KJV 6:1-17. ch7 is multi-divergence,
    all content-verified: G7:1-7 identity; KJV 7:8 = G7:8+G7:9 (concatenated); G7:10
    = the Greek-merge of KJV 7:9+7:10 (→7:9; KJV 7:10 unmapped); G7:11→7:11; KJV 7:12
    absent in Greek; G7:12-17 → KJV 7:13-18."""

    @pytest.mark.parametrize(
        "lxx_ch,lxx_v,expected",
        [
            (1, 1, ("tob", 1, 1)),  # identity book head
            (5, 22, ("tob", 5, 22)),  # ch5 last (identity)
            (6, 1, ("tob", 5, 22)),  # "she ceased weeping" -> concatenated onto KJV 5:22
            (6, 2, ("tob", 6, 1)),  # ch6 body offset −1
            (6, 18, ("tob", 6, 17)),  # ch6 last
            (7, 1, ("tob", 7, 1)),  # ch7 identity head
            (7, 7, ("tob", 7, 7)),
            (7, 8, ("tob", 7, 8)),  # KJV 7:8 first half
            (7, 9, ("tob", 7, 8)),  # KJV 7:8 second half -> concatenated
            (7, 10, ("tob", 7, 9)),  # Greek-merge of KJV 7:9+7:10 -> 7:9 (KJV 7:10 unmapped)
            (7, 11, ("tob", 7, 11)),
            (7, 12, ("tob", 7, 13)),  # KJV 7:12 absent in Greek
            (7, 13, ("tob", 7, 14)),
            (7, 17, ("tob", 7, 18)),  # ch7 last
            (8, 1, ("tob", 8, 1)),  # ch8+ identity resumes
            (14, 15, ("tob", 14, 15)),  # book last
        ],
    )
    def test_tobit_ch6_ch7(self, lxx_ch, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Tob", lxx_ch, lxx_v) == expected

    def test_kjv_7_10_and_7_12_have_no_greek(self):
        """KJV tob 7:10 (Greek-merged into the same verse as 7:9) and 7:12 (absent in
        the short Greek) receive no Greek of their own — never misplaced."""
        from scripts.core.versification import lxx_swete_to_kjv

        hits = [v for v in range(1, 18) if lxx_swete_to_kjv("Tob", 7, v) in {("tob", 7, 10), ("tob", 7, 12)}]
        assert hits == []


class TestLxxSweteJudith:
    """Judith (Swete Jdt→jdt). ch1-14 identity (per-chapter counts match AND ch14
    verified verse-by-verse). The 15/16 song boundary diverges, content-aligned
    against the real Greek↔KJV: G15:1-13 = KJV 15:1-13; G15:14 ("Judith began this
    thanksgiving in all Israel...") = KJV 16:1 (the song-intro, pulled forward). Then
    ch16 runs at offset +1 (G16:1 "Begin unto my God with timbrels" = KJV 16:2) until
    a catch-up MERGE: G16:7 ("put off her widow's garment...anointed her face") +
    G16:8 ("and bound her hair...linen garment to deceive him") are the two clauses of
    KJV 16:8 (concatenated), after which offset 0 resumes and G16:25 = KJV 16:25."""

    @pytest.mark.parametrize(
        "lxx_ch,lxx_v,expected",
        [
            (1, 1, ("jdt", 1, 1)),  # book head identity (ch1-14 not reordered)
            (14, 1, ("jdt", 14, 1)),
            (14, 19, ("jdt", 14, 19)),  # last identity verse before the song boundary
            (15, 1, ("jdt", 15, 1)),  # ch15 body identity
            (15, 13, ("jdt", 15, 13)),  # last ch15 verse that stays in ch15
            (15, 14, ("jdt", 16, 1)),  # song-intro pulled forward to KJV 16:1
            (16, 1, ("jdt", 16, 2)),  # +1 offset begins ("Begin unto my God...")
            (16, 6, ("jdt", 16, 7)),
            (16, 7, ("jdt", 16, 8)),  # first clause of KJV 16:8
            (16, 8, ("jdt", 16, 8)),  # second clause -> concatenated onto KJV 16:8
            (16, 9, ("jdt", 16, 9)),  # offset 0 resumes ("Her sandals ravished...")
            (16, 25, ("jdt", 16, 25)),  # last verse ("...nor a long time after her death")
        ],
    )
    def test_judith_song_boundary(self, lxx_ch, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Jdt", lxx_ch, lxx_v) == expected

    def test_every_kjv_judith_16_verse_receives_greek(self):
        """The merge is exact: all 25 KJV jdt 16 verses get Greek (none orphaned),
        and no Greek verse is misplaced outside the chapter."""
        from scripts.core.versification import lxx_swete_to_kjv

        covered = set()
        for v in range(1, 15):  # G15:1-14
            m = lxx_swete_to_kjv("Jdt", 15, v)
            if m and m[1] == 16:
                covered.add(m[2])
        for v in range(1, 26):  # G16:1-25
            m = lxx_swete_to_kjv("Jdt", 16, v)
            assert m is not None and m[0] == "jdt" and m[1] == 16
            covered.add(m[2])
        assert covered == set(range(1, 26))


class TestLxxSwete1Esdras:
    """1 Esdras (Swete 1Es→1es). ch4/7/9 identity (counts match). ch1/2/3/5/6/8 are
    Greek-FEWER than the KJV (Apocrypha) enumeration — the Greek combines verses the
    KJV splits, content-aligned against the real Greek↔KJV. Each combine leaves a KJV
    verse with no Greek of its own (never fabricated); ch8 additionally has ONE Greek
    SPLIT (G8:49+G8:50 = KJV 8:50, concatenated). Per chapter the net (merges−splits)
    equals the KJV-minus-Greek count: ch1 +3, ch2 +5, ch3 +1, ch5 +3, ch6 +1, ch8 +4.
    Merge loci (KJV verse with no Greek): ch1 K1:11/18/52; ch2 K2:7/20/21/23/29; ch3
    K3:15; ch5 K5:42/55/60; ch6 K6:9; ch8 K8:44/57/64/66/94."""

    @pytest.mark.parametrize(
        "lxx_ch,lxx_v,expected",
        [
            # ch1 (+3): merges at G1:10=K1:10+11, G1:16=K1:17+18, G1:49=K1:51+52
            (1, 1, ("1es", 1, 1)),
            (1, 10, ("1es", 1, 10)),  # "priests and Levites stood comely" = KJV 1:10+11
            (1, 11, ("1es", 1, 12)),  # offset +1 ("roasted the passover with fire")
            (1, 16, ("1es", 1, 17)),  # = KJV 1:17+18
            (1, 17, ("1es", 1, 19)),  # offset +2
            (1, 49, ("1es", 1, 51)),  # = KJV 1:51+52
            (1, 50, ("1es", 1, 53)),  # offset +3
            (1, 55, ("1es", 1, 58)),  # last (the 70-years sabbath)
            # ch2 (+5): G2:6=K6+7, G2:18=K19+20+21, G2:19=K22+23, G2:24=K28+29
            (2, 6, ("1es", 2, 6)),
            (2, 7, ("1es", 2, 8)),  # offset +1
            (2, 18, ("1es", 2, 19)),  # = KJV 2:19+20+21 (triple)
            (2, 19, ("1es", 2, 22)),  # offset +3; = KJV 2:22+23
            (2, 20, ("1es", 2, 24)),  # offset +4
            (2, 24, ("1es", 2, 28)),  # = KJV 2:28+29
            (2, 25, ("1es", 2, 30)),  # offset +5 (last)
            # ch3 (+1): G3:14=K3:14+15
            (3, 14, ("1es", 3, 14)),
            (3, 15, ("1es", 3, 16)),  # offset +1
            (3, 23, ("1es", 3, 24)),  # last
            # ch4 identity (63=63)
            (4, 1, ("1es", 4, 1)),
            (4, 63, ("1es", 4, 63)),
            # ch5 (+3): G5:41=K41+42, G5:53=K54+55, G5:57=K59+60
            (5, 41, ("1es", 5, 41)),
            (5, 42, ("1es", 5, 43)),  # offset +1
            (5, 53, ("1es", 5, 54)),  # = KJV 5:54+55
            (5, 54, ("1es", 5, 56)),  # offset +2
            (5, 57, ("1es", 5, 59)),  # = KJV 5:59+60
            (5, 58, ("1es", 5, 61)),  # offset +3
            (5, 70, ("1es", 5, 73)),  # last
            # ch6 (+1): G6:8=K6:8+9
            (6, 8, ("1es", 6, 8)),
            (6, 9, ("1es", 6, 10)),  # offset +1
            (6, 33, ("1es", 6, 34)),  # last
            # ch7 identity (15=15)
            (7, 1, ("1es", 7, 1)),
            (7, 15, ("1es", 7, 15)),
            # ch8 (+4): 5 merges + 1 split. G8:43=K43+44; G8:49+G8:50=K50 (split);
            # G8:56=K56+57; G8:62=K63+64; G8:63=K65+66; G8:90=K93+94
            (8, 43, ("1es", 8, 43)),  # = KJV 8:43+44
            (8, 44, ("1es", 8, 45)),  # offset +1
            (8, 49, ("1es", 8, 50)),  # first half of KJV 8:50
            (8, 50, ("1es", 8, 50)),  # second half -> concatenated onto KJV 8:50 (offset back to 0)
            (8, 51, ("1es", 8, 51)),
            (8, 56, ("1es", 8, 56)),  # = KJV 8:56+57
            (8, 57, ("1es", 8, 58)),  # offset +1
            (8, 62, ("1es", 8, 63)),  # = KJV 8:63+64
            (8, 63, ("1es", 8, 65)),  # offset +2; = KJV 8:65+66
            (8, 64, ("1es", 8, 67)),  # offset +3
            (8, 90, ("1es", 8, 93)),  # = KJV 8:93+94
            (8, 91, ("1es", 8, 95)),  # offset +4
            (8, 92, ("1es", 8, 96)),  # last
            # ch9 identity (55=55)
            (9, 1, ("1es", 9, 1)),
            (9, 55, ("1es", 9, 55)),
        ],
    )
    def test_1esdras_scattered_divisions(self, lxx_ch, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("1Es", lxx_ch, lxx_v) == expected

    def test_kjv_combine_loci_receive_no_greek(self):
        """The KJV verses the Greek combined into a neighbour get no Greek of their own
        (never fabricated by splitting one source verse)."""
        from scripts.core.versification import lxx_swete_to_kjv

        gaps = {1: {11, 18, 52}, 2: {7, 20, 21, 23, 29}, 3: {15}, 5: {42, 55, 60}, 6: {9}, 8: {44, 57, 64, 66, 94}}
        for ch, gap_vs in gaps.items():
            hit = {
                kv for v in range(1, 100) for m in [lxx_swete_to_kjv("1Es", ch, v)] if m and m[1] == ch for kv in [m[2]]
            }
            assert gap_vs.isdisjoint(hit), f"ch{ch}: {gap_vs & hit} unexpectedly received Greek"

    def test_ch8_split_concatenates_two_greek_into_kjv_8_50(self):
        """The lone Greek split: G8:49 and G8:50 both land on KJV 8:50 (build_verses
        concatenates them so the popup shows the whole verse)."""
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("1Es", 8, 49) == ("1es", 8, 50)
        assert lxx_swete_to_kjv("1Es", 8, 50) == ("1es", 8, 50)


class TestLxxSwetePrayerOfManasseh:
    """The Prayer of Manasseh is Swete ``Ode 8`` (VERIFIED against the real source — NOT
    the Rahlfs ``Ode 12`` numbering, which in THIS eliranwong digitization is the Nunc
    Dimittis / Prayer of Simeon). Ode 8 = "Προσευχὴ Μαννασσή. Κύριε παντοκράτωρ
    ἐπουράνιε..." with 15 verses, a CLEAN verse-for-verse identity onto KJV man 1 (the
    Greek title rides in v1). Every other Swete Ode is a canticle with no project book
    home (Song of Moses, Magnificat, Benedictus, Nunc Dimittis, ...) -> omit."""

    @pytest.mark.parametrize(
        "ode_v,expected",
        [
            (1, ("man", 1, 1)),  # "Prayer of Manasseh. O Lord almighty, God of our fathers..."
            (2, ("man", 1, 2)),  # "who hast made heaven and earth"
            (8, ("man", 1, 8)),  # "Thou therefore, O Lord, that art the God of the just"
            (11, ("man", 1, 11)),  # "Now therefore I bow the knee of mine heart"
            (15, ("man", 1, 15)),  # last ("I will praise thee for ever... Amen")
            (16, None),  # out of extent (man 1 has 15 verses)
        ],
    )
    def test_manasseh_from_ode_8_identity(self, ode_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Ode", 8, ode_v) == expected

    @pytest.mark.parametrize("ch,vs", [(1, 1), (9, 26), (11, 46), (12, 29), (13, 68), (14, 1)])
    def test_other_odes_have_no_project_home(self, ch, vs):
        """Ode 12 in particular is the Nunc Dimittis here — it must NOT map to man."""
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Ode", ch, vs) is None


class TestLxxSwetePrayerOfAzariah:
    """The Prayer of Azariah / Song of the Three (paz) is the Theodotion-Daniel Addition
    Dat 3:24-90 (already OMITTED from _DAN_SEGMENTS, so no fan-out conflict). Content-
    aligned vs the real Greek↔KJV paz: the prayer G3:24-51 → paz 1:1-28 (offset −23);
    G3:52 combines KJV 1:29+1:30 (1:30 gets no Greek) so the litany runs at offset −22;
    the Benedicite REORDERS (angels/heavens swapped; the cold/frost/lightning block
    permuted) and TWO source-empty verses G3:67/G3:68 leave KJV 1:46 + 1:49 without Greek.
    Dat 3:1-23 + 3:91-100 still belong to dan (the cross-book intercept is bounded to
    24-90)."""

    @pytest.mark.parametrize(
        "lxx_v,expected",
        [
            (24, ("paz", 1, 1)),  # "And they walked in the midst of the fire, praising God"
            (25, ("paz", 1, 2)),  # "Then Azarias stood up and prayed"
            (51, ("paz", 1, 28)),  # "the three, as out of one mouth, praised" (offset −23)
            (52, ("paz", 1, 29)),  # = KJV 1:29+1:30 (1:30 unmapped); offset drops to −22
            (53, ("paz", 1, 31)),  # "Blessed art thou in the temple of thine holy glory"
            (57, ("paz", 1, 35)),  # "O all ye works of the Lord"
            (58, ("paz", 1, 37)),  # angels — SWAPPED past heavens
            (59, ("paz", 1, 36)),  # heavens — SWAPPED
            (60, ("paz", 1, 38)),  # waters above the heaven
            (66, ("paz", 1, 44)),  # fire and heat
            (67, None),  # source-empty
            (68, None),  # source-empty
            (69, ("paz", 1, 45)),  # "cold and heat" -> winter and summer
            (70, ("paz", 1, 50)),  # "hoarfrost and snows" -> frost and snow
            (71, ("paz", 1, 47)),  # nights and days
            (72, ("paz", 1, 48)),  # light and darkness
            (73, ("paz", 1, 51)),  # lightnings and clouds
            (74, ("paz", 1, 52)),  # the earth (offset −22 resumes, monotonic to the end)
            (88, ("paz", 1, 66)),  # Ananias, Azarias, Misael
            (90, ("paz", 1, 68)),  # last ("O all ye that worship the Lord")
        ],
    )
    def test_azariah_from_theodotion_dat3(self, lxx_v, expected):
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Dat", 3, lxx_v) == expected

    def test_dat3_addition_boundary_stays_in_daniel(self):
        """Dat 3:23 (pre-Addition) and 3:91 (narrative resumes) still map to dan, not paz."""
        from scripts.core.versification import lxx_swete_to_kjv

        assert lxx_swete_to_kjv("Dat", 3, 23) == ("dan", 3, 23)
        assert lxx_swete_to_kjv("Dat", 3, 91) == ("dan", 3, 24)

    def test_combine_and_empty_loci_receive_no_greek(self):
        """KJV paz 1:30 (Greek-combined into 1:29) and 1:46/1:49 (the two source-empty
        Benedicite verses) receive no Greek of their own."""
        from scripts.core.versification import lxx_swete_to_kjv

        hit = {m[2] for v in range(24, 91) for m in [lxx_swete_to_kjv("Dat", 3, v)] if m and m[0] == "paz"}
        assert {30, 46, 49}.isdisjoint(hit)
        assert len(hit) == 65  # 65 of paz's 68 verses receive Greek


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
        assert stats["written"] >= 1 and stats["merged"] == 0

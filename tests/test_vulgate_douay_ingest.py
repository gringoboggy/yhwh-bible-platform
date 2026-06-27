from pathlib import Path

import pytest

from scripts.core.versification import vulgate_to_kjv

REPO = Path(__file__).resolve().parents[1]
VULGATE_DIR = REPO / "content" / "translations" / "vulgate-clementine"
DOUAY_DIR = REPO / "content" / "translations" / "douay-rheims"

# douay-rheims emits 74 project-book files: the eBible source carries 73 books, the
# BAR ch6 -> lje split adds one (+1 = 74), and tob/jdt/sir are dropped entirely
# (_VULGATE_OMIT — different recension) while paz/sus/bel are already separate eBible
# books that also receive the Daniel additions via the dan cross-book relocation.
# vulgate-clementine = 77: Phase E (2026-05-26) added the Clementine Latin
# deuterocanonical appendix man/1es/2es (+3) — see scripts/extract_vulgate_appendix.py.
EXPECTED_BOOK_COUNTS = {"vulgate-clementine": 77, "douay-rheims": 74}


def _store_dir(store):
    return VULGATE_DIR if store == "vulgate-clementine" else DOUAY_DIR


def _load_store_book(store, code):
    from scripts.core import translations as tx

    p = _store_dir(store) / f"{code}.py"
    if not p.is_file():
        return None
    return tx.load_book_verses_from_text(p.read_text(encoding="utf-8"))


class TestVulgateCrossBook:
    """The three Daniel additions (inline under the Vulgate/Douay 'dan' book) relocate
    to separate project books via ``_vulgate_cross``. Anchors content-verified by reading
    the ENGLISH Douay dan text against the ENGLISH KJV paz/sus/bel and confirmed SHIFTS=0
    by the _vg_verify_cross overlap harness (paz/sus/bel have no Douay source book of their
    own, so the normal _vg_verify gate cannot reach them)."""

    def test_prayer_of_azariah_reordered_benedicite(self):
        # NOT a clean -23 offset: Jerome's Vulgate follows the Theodotion Benedicite
        # reorder. Prayer head dan 3:24 -> paz 1:1; dan 3:51 -> paz 1:28 (last of the
        # prayer; offset -23).
        assert vulgate_to_kjv("dan", 3, 24) == ("paz", 1, 1)
        assert vulgate_to_kjv("dan", 3, 51) == ("paz", 1, 28)
        # dan 3:52 combines KJV paz 1:29+1:30 into one (1:30 folds); offset drops to -22.
        assert vulgate_to_kjv("dan", 3, 52) == ("paz", 1, 29)
        # The litany "Blessed art thou" pair is Vulgate-SWAPPED vs KJV: dan 3:54
        # ("throne of thy kingdom") = paz 1:33, dan 3:55 ("beholdest the depths /
        # cherubims") = paz 1:32.
        assert vulgate_to_kjv("dan", 3, 54) == ("paz", 1, 33)
        assert vulgate_to_kjv("dan", 3, 55) == ("paz", 1, 32)
        # The angels/heavens swap: dan 3:58 (angels) = paz 1:37, dan 3:59 (heavens) = 1:36.
        assert vulgate_to_kjv("dan", 3, 58) == ("paz", 1, 37)
        assert vulgate_to_kjv("dan", 3, 59) == ("paz", 1, 36)
        # The Vulgate cold/frost permutation (these verses are NOT source-empty as in the
        # Swete map): dan 3:67 ("cold and heat") = paz 1:45 ("winter and summer"); 3:69
        # ("frost and cold") = 1:50 ("frost and snow"); 3:70 ("ice and snow") = 1:49 ("ice
        # and cold"); 3:71 ("nights and days") = 1:47.
        assert vulgate_to_kjv("dan", 3, 67) == ("paz", 1, 45)
        assert vulgate_to_kjv("dan", 3, 69) == ("paz", 1, 50)
        assert vulgate_to_kjv("dan", 3, 70) == ("paz", 1, 49)
        assert vulgate_to_kjv("dan", 3, 71) == ("paz", 1, 47)
        # The tail (offset -22, monotonic): dan 3:74 -> paz 1:52; dan 3:90 ("O all ye
        # religious, bless the Lord the God of gods") = KJV paz 1:68 (the OLD clean -23
        # offset wrongly stopped at 1:67, dropping paz 1:68).
        assert vulgate_to_kjv("dan", 3, 74) == ("paz", 1, 52)
        assert vulgate_to_kjv("dan", 3, 90) == ("paz", 1, 68)

    def test_prayer_of_azariah_verse_30_is_the_only_fold(self):
        # KJV paz 1:30 ("And blessed is thy glorious and holy name") has no Vulgate verse
        # of its own -- it is the tail of the combined dan 3:52 -> paz 1:29. Every OTHER
        # KJV paz 1:1-68 slot receives exactly one Douay verse.
        hits = [v for v in range(24, 91) if vulgate_to_kjv("dan", 3, v) == ("paz", 1, 30)]
        assert hits == [], f"paz 1:30 expected fold but got dan 3:{hits}"

    def test_susanna_is_daniel_13_identity(self):
        # Clean identity dan 13:N -> sus 1:N for sus's 64 verses.
        assert vulgate_to_kjv("dan", 13, 1) == ("sus", 1, 1)
        assert vulgate_to_kjv("dan", 13, 64) == ("sus", 1, 64)
        # The Vulgate's trailing verse Douay dan 13:65 ("And king Astyages was gathered to
        # his fathers") is the verse the KJV places at bel 1:1 -> routed there (NOT dropped).
        assert vulgate_to_kjv("dan", 13, 65) == ("bel", 1, 1)

    def test_bel_is_daniel_14_plus_one(self):
        # The Vulgate Bel lacks the Greek/KJV Astyages intro (KJV bel 1:1), so the Douay
        # body runs at a uniform +1: dan 14:1 ("And Daniel was the king's guest") = KJV
        # bel 1:2; dan 14:2 = bel 1:3; tail dan 14:41 = bel 1:42.
        assert vulgate_to_kjv("dan", 14, 1) == ("bel", 1, 2)
        assert vulgate_to_kjv("dan", 14, 2) == ("bel", 1, 3)
        assert vulgate_to_kjv("dan", 14, 41) == ("bel", 1, 42)
        # The Vulgate-only closing decree (Douay dan 14:42 "Let all the inhabitants of the
        # whole earth fear the God of Daniel") maps past bel 1:42 -> drops out-of-extent.
        assert vulgate_to_kjv("dan", 14, 42) is None

    def test_bel_verse_1_comes_from_susanna_tail(self):
        # KJV bel 1:1 ("And king Astyages...") sits at the END of Susanna in the Vulgate
        # (Douay dan 13:65), not the head of Bel -> it is routed to bel 1:1 from dan 13:65,
        # and NO dan 14 verse maps to bel 1:1 (dan 14 starts the body at bel 1:2).
        assert vulgate_to_kjv("dan", 13, 65) == ("bel", 1, 1)
        hits = [v for v in range(1, 43) if vulgate_to_kjv("dan", 14, v) == ("bel", 1, 1)]
        assert hits == [], f"bel 1:1 should come from dan 13:65, not dan 14: {hits}"


class TestVulgateCrossChapterAnchors:
    @pytest.mark.parametrize(
        "code,ch,vs,expected",
        [
            ("num", 13, 1, ("num", 12, 16)),  # cross-chapter spies boundary
            ("num", 13, 2, ("num", 13, 1)),
            ("gen", 49, 31, ("gen", 49, 31)),
            ("gen", 49, 32, ("gen", 49, 33)),
            ("gen", 49, 1, ("gen", 49, 1)),
            ("gen", 50, 22, ("gen", 50, 22)),
            ("gen", 50, 23, ("gen", 50, 24)),
            ("jos", 21, 36, ("jos", 21, 37)),
            ("jos", 21, 37, ("jos", 21, 39)),
            ("hag", 2, 1, ("hag", 1, 15)),  # cross-chapter date-verse
            ("hag", 2, 2, ("hag", 2, 1)),
            ("ecc", 7, 1, ("ecc", 6, 12)),  # cross-chapter
            ("mat", 17, 15, ("mat", 17, 16)),
            ("amo", 6, 11, ("amo", 6, 10)),
            # 1sa ch24: Vulgate breaks ch23/24 one verse early — Douay 24:1 ("David...
            # dwelt in strong holds of Engaddi") = KJV 23:29; Douay 24:2 = KJV 24:1.
            ("1sa", 24, 1, ("1sa", 23, 29)),
            ("1sa", 24, 2, ("1sa", 24, 1)),
            # ecc: the Vulgate carries an EXTRA trailing verse in ch4 — Douay 4:17 ("Keep
            # thy foot...") = KJV 5:1 (KJV ch4 ends at v16), so all of Douay ch5 is +1.
            ("ecc", 4, 17, ("ecc", 5, 1)),
            ("ecc", 5, 1, ("ecc", 5, 2)),
            # dan ch3/4: the Vulgate ENDS ch3 with the doxology KJV opens ch4 with. Douay
            # 3:91-97 = KJV 3:24-30 (post-furnace narrative); Douay 3:98-100 ("Nabuchodonosor
            # the king, to all peoples... I have thought it good to publish his signs") = KJV
            # 4:1-3 (cross-chapter). Then Douay 4:1 ("I, Nabuchodonosor, was at rest in my
            # house") = KJV 4:4, a uniform +3 to Douay 4:34 = KJV 4:37.
            ("dan", 3, 91, ("dan", 3, 24)),
            ("dan", 3, 97, ("dan", 3, 30)),
            ("dan", 3, 98, ("dan", 4, 1)),  # cross-chapter: doxology head
            ("dan", 3, 100, ("dan", 4, 3)),
            ("dan", 4, 1, ("dan", 4, 4)),
            ("dan", 4, 34, ("dan", 4, 37)),
            # dan ch5/6 are IDENTITY in this Douay digitization: Douay 5:31 ("Darius the Mede
            # succeeded to the kingdom, being threescore and two years old") = KJV 5:31 (NOT
            # relocated to 6:1), and Douay 6:1 ("It seemed good to Darius... a hundred and
            # twenty governors") = KJV 6:1.
            ("dan", 5, 30, ("dan", 5, 30)),
            ("dan", 5, 31, ("dan", 5, 31)),
            ("dan", 6, 1, ("dan", 6, 1)),
            ("dan", 6, 2, ("dan", 6, 2)),
            ("dan", 6, 28, ("dan", 6, 28)),
            # lje (= source BAR ch6): the Douay omits the KJV 1:1 epistle heading, so Douay
            # 1:1 ("For the sins that you have committed before God...") = KJV 1:2 (+1 offset).
            ("lje", 1, 1, ("lje", 1, 2)),
            ("lje", 1, 41, ("lje", 1, 42)),
            ("lje", 1, 72, ("lje", 1, 73)),  # tail: +1 sustained to the end
            ("gen", 1, 1, ("gen", 1, 1)),  # identity sanity
            ("deu", 29, 1, ("deu", 29, 1)),  # deu is pure-identity in vul->eng (pruned)
        ],
    )
    def test_segment_maps(self, code, ch, vs, expected):
        assert vulgate_to_kjv(code, ch, vs) == expected


class TestVulgateSplitMergeFold:
    """Content-verified split/merge/fold boundaries for the eight OT books driven to
    a clean (or wording-noise-only) SHIFTS=0 by the _vg_verify gate. Each Douay verse
    was read against the KJV at the divergence; merges send two Douay verses to one
    KJV slot, and a KJV verse with no segment target is a verified fold."""

    @pytest.mark.parametrize(
        "code,ch,vs,expected",
        [
            # 1ki ch22: Vulgate SPLITS KJV 22:43 into Douay 22:43 (+22:44 merge), then +1.
            ("1ki", 22, 43, ("1ki", 22, 43)),
            ("1ki", 22, 44, ("1ki", 22, 43)),  # merge onto KJV 22:43
            ("1ki", 22, 45, ("1ki", 22, 44)),
            ("1ki", 22, 54, ("1ki", 22, 53)),
            # bar ch3: Vulgate SPLITS KJV 3:34 into Douay 3:34 (+3:35 merge), then -1.
            ("bar", 3, 34, ("bar", 3, 34)),
            ("bar", 3, 35, ("bar", 3, 34)),  # merge onto KJV 3:34
            ("bar", 3, 36, ("bar", 3, 35)),
            ("bar", 3, 38, ("bar", 3, 37)),
            # wis ch17: Vulgate MERGES KJV 17:9+17:10 into Douay 17:9, then +1 (17:10 fold).
            ("wis", 17, 9, ("wis", 17, 9)),
            ("wis", 17, 10, ("wis", 17, 11)),
            ("wis", 17, 20, ("wis", 17, 21)),
            # 1ma ch1: KJV 1:20 = Douay 1:21+1:22 (split); Douay 1:23 = KJV 1:21+1:22
            # (merge, 1:22 fold); Douay 1:52 = KJV 1:50; KJV 1:51 = Douay 1:53+1:54.
            ("1ma", 1, 21, ("1ma", 1, 20)),
            ("1ma", 1, 22, ("1ma", 1, 20)),  # merge onto KJV 1:20
            ("1ma", 1, 23, ("1ma", 1, 21)),  # KJV 1:22 folds here
            ("1ma", 1, 52, ("1ma", 1, 50)),
            ("1ma", 1, 53, ("1ma", 1, 51)),
            ("1ma", 1, 54, ("1ma", 1, 51)),  # merge onto KJV 1:51
            # 1ch ch11: Vulgate MERGES KJV 11:32+11:33 into Douay 11:32 (11:33 fold);
            # Douay 11:33 = KJV 11:34; Douay 11:34+11:35 = KJV 11:35 (merge).
            ("1ch", 11, 32, ("1ch", 11, 32)),
            ("1ch", 11, 33, ("1ch", 11, 34)),
            ("1ch", 11, 34, ("1ch", 11, 35)),
            ("1ch", 11, 35, ("1ch", 11, 35)),  # merge onto KJV 11:35
            # neh ch7: Vulgate SPLITS KJV 7:43 (Douay 7:43+7:44), then -1, then MERGES
            # KJV 7:47+7:48 into Douay 7:48 (7:48 fold); identity resumes at Douay 7:49.
            ("neh", 7, 43, ("neh", 7, 43)),
            ("neh", 7, 44, ("neh", 7, 43)),  # merge onto KJV 7:43
            ("neh", 7, 45, ("neh", 7, 44)),
            ("neh", 7, 48, ("neh", 7, 47)),  # KJV 7:48 folds here
            ("neh", 7, 49, ("neh", 7, 49)),
            # num ch11: Vulgate MERGES KJV 11:34 (Kibroth-hattaavah) + 11:35 (Hazeroth) into
            # one Douay 11:34; Douay 11:1-34 = KJV 11:1-34 identity, KJV 11:35 folds.
            ("num", 11, 34, ("num", 11, 34)),
            # num ch15: KJV 15:11 SPLITS -> Douay 15:11+15:12 (KJV 15:12 fold); KJV 15:13
            # SPLITS -> Douay 15:13+15:14 (KJV 15:14,15:15 fold); Douay 15:15 = KJV 15:16;
            # KJV 15:18 SPLITS -> Douay 15:17+15:18; identity resumes Douay 15:19 = KJV 15:19.
            ("num", 15, 12, ("num", 15, 11)),  # merge onto KJV 15:11
            ("num", 15, 15, ("num", 15, 16)),
            ("num", 15, 18, ("num", 15, 18)),  # merge onto KJV 15:18
            ("num", 15, 19, ("num", 15, 19)),
            # num ch16: only the v42/43 boundary differs -- Douay 16:43 = KJV 16:42 (it folds
            # in the cloud/glory clause + the tabernacle approach), KJV 16:43 folds.
            ("num", 16, 42, ("num", 16, 42)),
            ("num", 16, 43, ("num", 16, 42)),  # merge onto KJV 16:42
            ("num", 16, 44, ("num", 16, 44)),
            # num ch27 (Zelophehad): KJV 27:3+27:4 MERGE into Douay 27:3 (KJV 27:4 fold); then
            # -1 (Douay 27:4 = KJV 27:5...); KJV 27:8 SPLITS -> Douay 27:7+27:8; identity at 27:9.
            ("num", 27, 3, ("num", 27, 3)),
            ("num", 27, 4, ("num", 27, 5)),
            ("num", 27, 6, ("num", 27, 7)),
            ("num", 27, 8, ("num", 27, 8)),  # merge onto KJV 27:8
            ("num", 27, 9, ("num", 27, 9)),
            # num ch29/30 (vows): Douay 30:1 = KJV 29:40 (cross-chapter); Douay 30:2.. = KJV 30:1..
            ("num", 30, 1, ("num", 29, 40)),  # cross-chapter
            ("num", 30, 2, ("num", 30, 1)),
            ("num", 30, 17, ("num", 30, 16)),
            # exo ch38 (metal tally): KJV 38:25 (silver total) folds; Douay 38:25 = KJV 38:26
            # (census); KJV 38:27 SPLITS -> Douay 38:26+38:27; identity resumes Douay 38:28.
            ("exo", 38, 24, ("exo", 38, 24)),
            ("exo", 38, 25, ("exo", 38, 26)),
            ("exo", 38, 27, ("exo", 38, 27)),  # merge onto KJV 38:27
            ("exo", 38, 28, ("exo", 38, 28)),
            # exo ch39 (vestments): KJV 39:19+39:20 fold (Douay 39:19 = KJV 39:21, offset +2);
            # KJV 39:28 SPLITS -> Douay 39:26+39:27 (offset -> +1); KJV 39:38 SPLITS -> Douay
            # 39:37+39:38 (offset -> 0); identity resumes Douay 39:39 = KJV 39:39.
            ("exo", 39, 18, ("exo", 39, 18)),
            ("exo", 39, 19, ("exo", 39, 21)),
            ("exo", 39, 25, ("exo", 39, 27)),
            ("exo", 39, 27, ("exo", 39, 28)),  # merge onto KJV 39:28
            ("exo", 39, 28, ("exo", 39, 29)),
            ("exo", 39, 38, ("exo", 39, 38)),  # merge onto KJV 39:38
            ("exo", 39, 39, ("exo", 39, 39)),
            ("exo", 39, 43, ("exo", 39, 43)),
            # lev ch15: KJV 15:19 SPLITS -> Douay 15:19+15:20 (offset -1); Douay 15:21 = KJV
            # 15:20, 15:22 = KJV 15:21, 15:23 = KJV 15:22; KJV 15:23 folds; identity at 15:24.
            ("lev", 15, 19, ("lev", 15, 19)),
            ("lev", 15, 20, ("lev", 15, 19)),  # merge onto KJV 15:19
            ("lev", 15, 21, ("lev", 15, 20)),
            ("lev", 15, 22, ("lev", 15, 21)),
            ("lev", 15, 23, ("lev", 15, 22)),
            ("lev", 15, 24, ("lev", 15, 24)),
            # lje ch1: the Vulgate MERGES the two women-with-cords clauses -- Douay 1:42
            # ("sit in the ways, burning olive stones") + 1:43 ("when any one... lieth with
            # him... nor her cord broken") = KJV 1:43 -- dropping the +1 head offset to 0
            # (Douay 1:44-51 = KJV 1:44-51). Douay 1:51 ("Whence... is it known that they are
            # not gods, but the work of men's hands...") = KJV 1:51 and folds the short KJV
            # 1:52 ("Who then may not know that they are no gods?"); offset returns to +1 so
            # Douay 1:52 ("They cannot set up a king... nor give rain") = KJV 1:53.
            ("lje", 1, 42, ("lje", 1, 43)),
            ("lje", 1, 43, ("lje", 1, 43)),  # merge onto KJV 1:43
            ("lje", 1, 44, ("lje", 1, 44)),
            ("lje", 1, 51, ("lje", 1, 51)),
            ("lje", 1, 52, ("lje", 1, 53)),
        ],
    )
    def test_split_merge_maps(self, code, ch, vs, expected):
        assert vulgate_to_kjv(code, ch, vs) == expected

    def test_verified_folds_have_no_own_source(self):
        # Each KJV verse below has its content folded into a Douay neighbour (verified
        # by reading), so it must receive no Douay verse of its own via these segments.
        for code, ch, vs in [
            ("1ma", 1, 22),
            ("1ch", 11, 33),
            ("neh", 7, 48),
            ("wis", 17, 10),
            ("num", 11, 35),
            ("num", 15, 12),
            ("num", 15, 14),
            ("num", 15, 15),
            ("num", 16, 43),
            ("num", 27, 4),
            ("exo", 38, 25),
            ("exo", 39, 19),
            ("exo", 39, 20),
            ("lev", 15, 23),
            # lje: KJV 1:1 (epistle heading) + KJV 1:52 (short rhetorical question) both
            # have their content folded into a Douay neighbour, so neither gets its own
            # Douay verse via the segment table.
            ("lje", 1, 1),
            ("lje", 1, 52),
        ]:
            hits = [v for v in range(1, 200) if vulgate_to_kjv(code, ch, v) == (code, ch, vs)]
            assert hits == [], f"{code} {ch}:{vs} expected fold but got Douay {hits}"


class TestVulgatePsalmFixes:
    """Per-psalm _VULGATE_PSALM_FIXES overrides correcting the residual verse-division
    mismatches between the Douay's Latin numbering and the reused LXX ``_psalm_map``
    (built for the Swete Greek division). Each anchor was content-aligned by reading
    the ENGLISH Douay against the ENGLISH KJV; keys are Vulgate (Douay) coordinates.
    These drive the _vg_verify psa gate from SHIFTS=17 to SHIFTS=1 (the lone residual,
    KJV 73:23, is a proven LXX/Hebrew clause-division wording artifact, mapped 1:1).
    """

    @pytest.mark.parametrize(
        "vch,vvs,expected",
        [
            # Vulgate Ps 10 = KJV 11: title (D 10:1) + first body line (D 10:2 "In the Lord
            # I put my trust") BOTH -> KJV 11:1; D 10:3..10:8 -> KJV 11:2..11:7.
            (10, 1, (11, 1)),
            (10, 2, (11, 1)),  # merge: "In the Lord I put my trust" onto 11:1
            (10, 3, (11, 2)),  # corrected first body verse (was 11:3)
            (10, 7, (11, 6)),
            (10, 8, (11, 7)),  # was dropped by _psalm_map; now fills KJV 11:7
            # Vulgate Ps 12 = KJV 13: KJV 13:2 SPLIT into D 12:2 + D 12:3; then -1; D 12:6
            # MERGES KJV 13:5 + 13:6.
            (12, 2, (13, 2)),
            (12, 3, (13, 2)),  # merge onto KJV 13:2 ("enemy be exalted")
            (12, 4, (13, 3)),  # corrected first shifted body verse
            (12, 6, (13, 5)),  # merge: KJV 13:6 folds into D 12:6
            # Vulgate Ps 19 = KJV 20: D 19:9 MERGES KJV 20:8 + 20:9; mapped to the trailing
            # KJV 20:9 to resolve that empty slot (KJV 20:8 holds the merge-fold).
            (19, 8, (20, 7)),
            (19, 9, (20, 9)),  # resolved missing KJV 20:9
            # Vulgate Ps 43 = KJV 44: D 43:22 MERGES KJV 44:21 + 44:22; tail +1 to D 43:26.
            (43, 22, (44, 21)),  # carries 44:22's text but maps to 44:21
            (43, 23, (44, 23)),  # corrected first shifted body verse
            (43, 26, (44, 26)),  # resolved missing KJV 44:26
            # Vulgate Ps 55 = KJV 56: D 55:11 MERGES KJV 56:10 + 56:11; then -1.
            (55, 11, (56, 10)),  # carries 56:11's text but maps to 56:10
            (55, 12, (56, 12)),  # corrected first shifted body verse
            (55, 13, (56, 13)),  # resolved missing KJV 56:13
            # Vulgate Ps 108 = KJV 109: KJV 109:16 SPLIT into D 108:16 + D 108:17; KJV
            # 109:17 + 109:18 MERGED into D 108:18; identity resumes at D 108:19.
            (108, 16, (109, 16)),
            (108, 17, (109, 16)),  # split: second half merged onto 109:16
            (108, 18, (109, 17)),  # merge: KJV 109:18 folds into D 108:18
            (108, 19, (109, 19)),  # identity resumes
            # round-15 D3 fix: BOTH the Latin Vulgate and the English Douay carry one extra
            # trailing verse on Ps 2 + Ps 4 (split the psalm's closing line); it had no map
            # key, so vulgate_to_kjv returned None and the clause was DROPPED from the popups.
            # Fold each onto the last KJV verse (dev/audit_versification_coverage.py guards it).
            (2, 13, (2, 12)),  # was None (dropped); folds the close of KJV 2:12
            (4, 10, (4, 8)),  # was None (dropped); folds the tail of KJV 4:8
        ],
    )
    def test_psalm_fix_maps(self, vch, vvs, expected):
        out = vulgate_to_kjv("psa", vch, vvs)
        assert out == ("psa", *expected)

    def test_resolved_missing_now_filled(self):
        # The three KJV slots the gate reported as missing are now each filled by their
        # trailing Douay verse (the verses that justify the +1 corrections above).
        assert vulgate_to_kjv("psa", 19, 9) == ("psa", 20, 9)
        assert vulgate_to_kjv("psa", 43, 26) == ("psa", 44, 26)
        assert vulgate_to_kjv("psa", 55, 13) == ("psa", 56, 13)

    def test_psalm_merge_folds_have_no_own_source(self):
        # Each (kjv_ch, kjv_vs) below is a verified merge-fold: its content lives inside
        # a Douay neighbour, so NO Vulgate verse of its SOURCE psalm may map to it. The
        # source psalm differs from the KJV chapter (the Vulgate is numbered one psalm
        # lower across this range), so the search uses the correct Vulgate chapter.
        for vch, kjv_ch, kjv_vs in [
            (12, 13, 6),  # KJV 13:6 folded into D 12:6
            (19, 20, 8),  # KJV 20:8 folded into D 19:9 (mapped to 20:9)
            (43, 44, 22),  # KJV 44:22 folded into D 43:22 (mapped to 44:21)
            (55, 56, 11),  # KJV 56:11 folded into D 55:11 (mapped to 56:10)
            (108, 109, 18),  # KJV 109:18 folded into D 108:18 (mapped to 109:17)
        ]:
            hits = [v for v in range(1, 200) if vulgate_to_kjv("psa", vch, v) == ("psa", kjv_ch, kjv_vs)]
            assert hits == [], f"psa {kjv_ch}:{kjv_vs} expected merge-fold but got Vulgate {vch}:{hits}"

    def test_psalm_map_still_used_for_untouched_psalms(self):
        # A psalm not in _VULGATE_PSALM_FIXES still flows through the shared _psalm_map
        # (e.g. Vulgate Ps 3 = KJV 3, body offset by the dropped superscription).
        assert vulgate_to_kjv("psa", 3, 1) is None  # dropped title
        assert vulgate_to_kjv("psa", 3, 2) == ("psa", 3, 1)  # first body verse


class TestVulgateInclusionPolicy:
    def test_recension_books_omitted(self):
        for code in ("tob", "jdt", "sir"):
            assert vulgate_to_kjv(code, 1, 1) is None

    def test_wisdom_included(self):
        assert vulgate_to_kjv("wis", 1, 1) == ("wis", 1, 1)

    def test_esther_greek_additions_auto_omit(self):
        assert vulgate_to_kjv("est", 11, 2) is None
        assert vulgate_to_kjv("est", 10, 13) is None

    def test_psalms_routed_through_psalm_map(self):
        # Vulgate Ps 9 covers KJV 9+10; v22 lands in KJV ch10 (via _psalm_map)
        out = vulgate_to_kjv("psa", 9, 22)
        assert out is not None and out[0] == "psa" and out[1] == 10


class TestVulgateDouayStores:
    """Integration: the committed on-disk vulgate-clementine + douay-rheims stores,
    both produced by the thin extract_vulgate.py / extract_douay.py drivers over the
    SAME shared ``vulgate_to_kjv`` adapter. (Mirrors TestArabicVandykeIngest.)"""

    @pytest.mark.parametrize("store", ["vulgate-clementine", "douay-rheims"])
    def test_store_has_expected_book_count(self, store):
        books = sorted(p.stem for p in _store_dir(store).glob("*.py"))
        expected = EXPECTED_BOOK_COUNTS[store]
        assert len(books) == expected, f"{store}: expected {expected}, got {len(books)}: {books}"

    @pytest.mark.parametrize("store", ["vulgate-clementine", "douay-rheims"])
    def test_all_coords_in_canonical_extent(self, store):
        from scripts.core.canonical_verse_counts import coord_in_canonical_extent

        bad = []
        for p in _store_dir(store).glob("*.py"):
            code = p.stem
            for ch, vs, _t in _load_store_book(store, code) or []:
                if not coord_in_canonical_extent(code, ch, vs):
                    bad.append((code, ch, vs))
        assert bad == [], f"{store}: out-of-extent coords after remap: {bad[:20]}"

    @pytest.mark.parametrize("store", ["vulgate-clementine", "douay-rheims"])
    @pytest.mark.parametrize("code", ["paz", "sus", "bel"])
    def test_daniel_additions_present_and_nonempty(self, store, code):
        # The three Daniel additions arrive via the dan cross-book relocation
        # (dan 3:24-90 -> paz, dan 13 -> sus, dan 14 -> bel).
        verses = _load_store_book(store, code)
        assert verses, f"{store}: {code}.py missing or empty"
        assert len(verses) > 0

    @pytest.mark.parametrize("store", ["vulgate-clementine", "douay-rheims"])
    @pytest.mark.parametrize("code", ["tob", "jdt", "sir"])
    def test_omitted_recension_books_absent(self, store, code):
        # tob/jdt/sir are a different recension (no KJV-skeleton correspondence) ->
        # every verse maps to None, the book is emptied, and no file is emitted.
        assert not (_store_dir(store) / f"{code}.py").is_file(), f"{store}: {code}.py should NOT exist"

    def test_douay_genesis_spot_check(self):
        from scripts.core import translations as tx

        assert tx.get_verse("douay-rheims", "gen", 1, 1)  # non-empty

    def test_douay_cross_chapter_num_12_16_populated(self):
        # KJV num 12:16 ("the people removed from Hazeroth, and pitched in... Paran")
        # comes from the Vulgate/Douay num 13:1 (the spies pericope opens a verse early).
        from scripts.core import translations as tx

        assert tx.get_verse("douay-rheims", "num", 12, 16)  # non-empty (cross-chapter)

    def test_vulgate_genesis_spot_check(self):
        from scripts.core import translations as tx

        assert tx.get_verse("vulgate-clementine", "gen", 1, 1)  # non-empty Latin

    def test_isa_45_26_folds_onto_45_25_in_douay(self):
        # The Douay splits the final KJV isa 45:25 across Douay 45:25 + 45:26; the
        # _VULGATE_SEGMENTS isa-45 concat-tail folds 45:26 onto KJV 45:25 (so it is
        # NOT dropped). The verse text must therefore contain the Douay 45:26 wording.
        from scripts.core import translations as tx

        v = tx.get_verse("douay-rheims", "isa", 45, 25)
        assert v and "all the seed of Israel" in v

"""scripts.core.versification — adapters mapping a translation's own verse
numbering onto the project's canonical (KJV/WEB) numbering.

Phase 2 of the fully-customizable-builder roadmap; the seam the registry's
``popup_versions.normalize_coord`` documents. The first adapter loads the
OpenScriptures morphhb ``VerseMap.xml`` — a catalogue of the WLC (Masoretic) ↔
KJV differences (the Genesis 31/32 chapter boundary, Psalm superscriptions
counted as Hebrew verse 1, …). Only the *differences* are listed; every other
verse maps identity, so callers default with ``map.get(coord, coord)``.

Parsing is XML-only (ElementTree) — translation/versification data is never
executed as code (RULES §7.1).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from functools import lru_cache

from .canonical_verse_counts import canonical_count, coord_in_canonical_extent

Coord = tuple[str, int, int]  # (OSIS book name, chapter, verse)


def _local(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def _parse_ref(ref: str | None) -> Coord | None:
    """Parse an OSIS verse ref ``Book.C.V`` → ``(Book, C, V)``.

    Returns ``None`` for sub-verse partial refs (``…!a``) or malformed refs, so
    only clean verse-level entries participate in the coord map.
    """
    if not ref or "!" in ref:
        return None
    parts = ref.split(".")
    if len(parts) != 3:
        return None
    book, ch, vs = parts
    if not (ch.isdigit() and vs.isdigit()):
        return None
    return (book, int(ch), int(vs))


def parse_versemap(path) -> list[tuple[Coord, Coord, str]]:
    """Return ``[(wlc_coord, kjv_coord, type), …]`` for each clean verse-level
    entry in a morphhb ``VerseMap.xml``."""
    root = ET.parse(path).getroot()
    out: list[tuple[Coord, Coord, str]] = []
    for el in root.iter():
        if _local(el.tag) != "verse":
            continue
        wlc = _parse_ref(el.get("wlc"))
        kjv = _parse_ref(el.get("kjv"))
        if wlc is None or kjv is None:
            continue
        out.append((wlc, kjv, el.get("type") or "full"))
    return out


def wlc_to_kjv_map(path) -> dict[Coord, Coord]:
    """WLC (Masoretic) → KJV coord map, from the ``full`` entries only.

    ``partial`` (sub-verse ``!a``/``!b``) entries are excluded — a sub-verse
    split can't be represented at whole-verse granularity, so those verses keep
    identity numbering (a documented Phase-2 limitation). The set of map *values*
    is the set of KJV coords explicitly claimed, which lets an ingester drop a
    WLC superscription verse whose identity coord is already taken.
    """
    return {wlc: kjv for wlc, kjv, typ in parse_versemap(path) if typ == "full"}


# ===========================================================================
# LXX (Swete) -> canonical KJV/project versification.
#
# The Septuagint differs from the KJV/Masoretic numbering in well-known ways.
# Most of the 39 OT books map by IDENTITY (with the ``coord_in_canonical_extent``
# guard dropping any verse the LXX has beyond the KJV chapter — the same minor
# verse-level divergence the WLC ingest accepts). Six books carry GROSS
# structural divergences that would put the wrong Greek on a verse if mapped
# identity; those are remapped explicitly here. Every mapping below was derived
# by content-aligning the real Swete source against the KJV text (proper-noun /
# seam matching), NOT from memory — see dev/CHANGELOG.md 2026-05-23.
#
# A None return means "omit this LXX verse" — it has no canonical home (a
# dropped Psalm superscription, the Esther/Daniel Additions, an LXX-only
# doublet, an out-of-extent coord, or a book outside this pass's 39-OT scope).
# ===========================================================================

# Swete book name -> project 3-letter code (the 39 standard OT books + the
# content-verified deuterocanon subset below; Daniel uses the received Theodotion
# text ``Dat``, Song of Songs is ``Sol`` -> ``sng``). The deuterocanon reorder pass
# is COMPLETE: Jdt (15/16 song boundary), 1Es (scattered intra-chapter combines), and
# the two cross-book canticles man (Swete Ode 8, via _cross_book) + paz (Theodotion
# Dat 3:24-90, via _cross_book) are all mapped. Still out of scope: aes (editorial
# WEB↔KJV concordance, not a Swete-map problem), 1En (no KJV skeleton + base render
# gap), and the unused recension dups (Tbs Tobit-long, Old-Greek Sus/Bel/Dan).
SWETE_BOOK_TO_CODE: dict[str, str] = {
    "Gen": "gen",
    "Exo": "exo",
    "Lev": "lev",
    "Num": "num",
    "Deu": "deu",
    "Jos": "jos",
    "Jdg": "jdg",
    "Rut": "rut",
    "1Sa": "1sa",
    "2Sa": "2sa",
    "1Ki": "1ki",
    "2Ki": "2ki",
    "1Ch": "1ch",
    "2Ch": "2ch",
    "Ezr": "ezr",
    "Neh": "neh",
    "Est": "est",
    "Job": "job",
    "Psa": "psa",
    "Pro": "pro",
    "Ecc": "ecc",
    "Sol": "sng",
    "Isa": "isa",
    "Jer": "jer",
    "Lam": "lam",
    "Eze": "eze",
    "Dat": "dan",
    "Hos": "hos",
    "Joe": "joe",
    "Amo": "amo",
    "Oba": "oba",
    "Jon": "jon",
    "Mic": "mic",
    "Nah": "nah",
    "Hab": "hab",
    "Zep": "zep",
    "Hag": "hag",
    "Zec": "zec",
    "Mal": "mal",
    # --- Deuterocanon (this pass) — versification verified by interior content
    # alignment against the KJV (NOT memory). sus/bel take the Theodotion
    # recension (Sut/Bet) the KJV/Vulgate tradition follows; bar+lje each carry
    # one verified verse-split (see _BAR_SEGMENTS / _LJE_SEGMENTS).
    "Wis": "wis",  # Wisdom of Solomon — exact identity (orig.-Greek), all 19 ch
    "Sut": "sus",  # Susanna (Theodotion, 64 v) — exact identity
    "Bet": "bel",  # Bel & the Dragon (Theodotion, 42 v) — exact identity
    "Bar": "bar",  # Baruch — identity except the ch3 split
    "Epj": "lje",  # Letter of Jeremiah — single head split, then +1
    "Sir": "sir",  # Sirach — the 30:25-36:16a transposition + merges (_SIR_SEGMENTS)
    "Tob": "tob",  # Tobit (short recension) — ch6 offset + ch7 split/merge (_TOB_SEGMENTS)
    "Jdt": "jdt",  # Judith — ch1-14 identity; the 15/16 song boundary (_JDT_SEGMENTS)
    "1Es": "1es",  # 1 Esdras — scattered intra-chapter combines, ch1/2/3/5/6/8 (_1ES_SEGMENTS)
}

# Per-chapter LXX verse counts for Psalms (Swete), index == LXX chapter (0 unused).
# Reviewed reference data extracted from the Swete source; drives both the
# merge/split boundaries and the superscription offset (= LXX_count - KJV_count).
_LXX_PSALM_COUNTS: tuple[int, ...] = (
    0,
    6,
    12,
    9,
    9,
    13,
    11,
    18,
    10,
    39,
    7,  # 1-10
    9,
    6,
    7,
    5,
    11,
    15,
    51,
    15,
    10,
    14,  # 11-20
    32,
    6,
    10,
    22,
    12,
    14,
    9,
    11,
    13,
    25,  # 21-30
    11,
    22,
    23,
    28,
    13,
    40,
    23,
    14,
    18,
    14,  # 31-40
    12,
    5,
    27,
    18,
    12,
    10,
    15,
    21,
    23,
    21,  # 41-50
    11,
    7,
    9,
    24,
    14,
    12,
    12,
    18,
    14,
    9,  # 51-60
    13,
    12,
    11,
    14,
    20,
    8,
    36,
    37,
    6,
    24,  # 61-70
    20,
    28,
    23,
    11,
    13,
    21,
    72,
    13,
    20,
    17,  # 71-80
    8,
    19,
    13,
    14,
    17,
    7,
    19,
    53,
    17,
    16,  # 81-90
    16,
    5,
    23,
    11,
    13,
    12,
    9,
    9,
    5,
    8,  # 91-100
    29,
    22,
    35,
    45,
    48,
    43,
    14,
    31,
    7,
    10,  # 101-110
    10,
    9,
    26,
    9,
    10,
    2,
    29,
    176,
    7,
    8,  # 111-120
    9,
    4,
    8,
    5,
    6,
    5,
    6,
    8,
    8,
    3,  # 121-130
    18,
    3,
    3,
    21,
    26,
    9,
    8,
    24,
    14,
    10,  # 131-140
    8,
    12,
    15,
    21,
    10,
    11,
    9,
    14,
    9,
    6,  # 141-150
    7,  # 151
)


_PsalmMap = dict[tuple[int, int], "tuple[int, int] | None"]


def _ps_one_to_one(out: _PsalmMap, counts: tuple[int, ...], lxx_ch: int, kjv_ch: int) -> None:
    """LXX psalm maps 1:1 to a KJV psalm; drop the leading superscription verses
    (offset = LXX_count - KJV_count)."""
    off = counts[lxx_ch] - canonical_count("psa", kjv_ch)
    assert off >= 0, f"psalm {lxx_ch}->{kjv_ch} negative offset {off}"
    for v in range(1, counts[lxx_ch] + 1):
        out[(lxx_ch, v)] = None if v <= off else (kjv_ch, v - off)


def _ps_merge(out: _PsalmMap, counts: tuple[int, ...], lxx_ch: int, kjv_a: int, kjv_b: int) -> None:
    """One LXX psalm covers two consecutive KJV psalms (after the leading title)."""
    a = canonical_count("psa", kjv_a)
    off = counts[lxx_ch] - (a + canonical_count("psa", kjv_b))
    assert off >= 0, f"psalm {lxx_ch} merge negative offset {off}"
    for v in range(1, counts[lxx_ch] + 1):
        if v <= off:
            out[(lxx_ch, v)] = None
        elif v - off <= a:
            out[(lxx_ch, v)] = (kjv_a, v - off)
        else:
            out[(lxx_ch, v)] = (kjv_b, v - off - a)


def _ps_split(out: _PsalmMap, counts: tuple[int, ...], lxx_first: int, lxx_second: int, kjv_ch: int) -> None:
    """Two LXX psalms concatenate into one KJV psalm (no superscription offset)."""
    assert counts[lxx_first] + counts[lxx_second] == canonical_count("psa", kjv_ch), f"split {kjv_ch} mismatch"
    for v in range(1, counts[lxx_first] + 1):
        out[(lxx_first, v)] = (kjv_ch, v)
    for v in range(1, counts[lxx_second] + 1):
        out[(lxx_second, v)] = (kjv_ch, counts[lxx_first] + v)


@lru_cache(maxsize=1)
def _psalm_map() -> _PsalmMap:
    """Build ``{(lxx_ch, lxx_v): (kjv_ch, kjv_v) | None}`` for all 151 LXX psalms.

    ``None`` = a dropped superscription verse or LXX Ps 151 (no KJV home)."""
    counts = _LXX_PSALM_COUNTS
    out: _PsalmMap = {}
    for ch in range(1, 9):  # 1-8: same number
        _ps_one_to_one(out, counts, ch, ch)
    _ps_merge(out, counts, 9, 9, 10)  # LXX 9 = KJV 9 + 10
    for ch in range(10, 113):  # 10-112 -> KJV 11-113
        _ps_one_to_one(out, counts, ch, ch + 1)
    _ps_merge(out, counts, 113, 114, 115)  # LXX 113 = KJV 114 + 115
    _ps_split(out, counts, 114, 115, 116)  # LXX 114 + 115 = KJV 116
    for ch in range(116, 146):  # 116-145 -> KJV 117-146
        _ps_one_to_one(out, counts, ch, ch + 1)
    _ps_split(out, counts, 146, 147, 147)  # LXX 146 + 147 = KJV 147
    for ch in range(148, 151):  # 148-150: same number
        _ps_one_to_one(out, counts, ch, ch)
    for v in range(1, counts[151] + 1):  # LXX 151 has no KJV equivalent
        out[(151, v)] = None
    return out


# Explicit verse-segment overrides for the structurally-reordered books.
# A segment is (lxx_v_lo, lxx_v_hi, kjv_ch | None, kjv_v_lo): an LXX verse v in
# [lo, hi] maps to (code, kjv_ch, kjv_v_lo + (v - lxx_v_lo)); kjv_ch None = omit.
# A chapter absent from a book's table maps by identity. ``_HI`` = open upper
# bound for whole-chapter relocations (the extent guard trims any overflow).
_HI = 9999
_Seg = tuple[int, int, "int | None", int]

_JER_SEGMENTS: dict[int, list[_Seg]] = {
    25: [(1, 13, 25, 1), (14, 14, None, 0), (15, 19, 49, 35)],
    26: [(1, 1, 49, 34), (2, _HI, 46, 2)],
    27: [(1, _HI, 50, 1)],
    28: [(1, _HI, 51, 1)],
    29: [(1, 7, 47, 1), (8, _HI, 49, 7)],
    30: [(1, 5, 49, 1), (6, 11, 49, 28), (12, _HI, 49, 23)],
    31: [(1, _HI, 48, 1)],
    32: [(1, _HI, 25, 15)],
    33: [(1, _HI, 26, 1)],
    34: [(1, 5, 27, 2), (6, 10, 27, 8), (11, 13, 27, 14), (14, 14, None, 0), (15, 17, 27, 18), (18, _HI, 27, 22)],
    35: [(1, _HI, 28, 1)],
    36: [(1, _HI, 29, 1)],
    37: [(1, _HI, 30, 1)],
    38: [(1, _HI, 31, 1)],
    39: [(1, _HI, 32, 1)],
    40: [(1, _HI, 33, 1)],
    41: [(1, _HI, 34, 1)],
    42: [(1, _HI, 35, 1)],
    43: [(1, _HI, 36, 1)],
    44: [(1, _HI, 37, 1)],
    45: [(1, _HI, 38, 1)],
    46: [(1, _HI, 39, 1)],
    47: [(1, _HI, 40, 1)],
    48: [(1, _HI, 41, 1)],
    49: [(1, _HI, 42, 1)],
    50: [(1, _HI, 43, 1)],
    51: [(1, 30, 44, 1), (31, _HI, 45, 1)],
}

_DAN_SEGMENTS: dict[int, list[_Seg]] = {
    3: [(1, 23, 3, 1), (24, 90, None, 0), (91, 97, 3, 24), (98, 100, 4, 1)],
    4: [(1, _HI, 4, 4)],
}

_PRO_SEGMENTS: dict[int, list[_Seg]] = {
    24: [(1, 22, 24, 1), (23, 23, None, 0), (24, 37, 30, 1), (38, 49, 24, 23), (50, 68, 30, 15), (69, _HI, 31, 1)],
    29: [(1, 27, 29, 1), (28, _HI, 31, 10)],
}

_1KI_SEGMENTS: dict[int, list[_Seg]] = {
    20: [(1, _HI, 21, 1)],  # Naboth's vineyard = KJV 21
    21: [(1, _HI, 20, 1)],  # Ben-hadad = KJV 20
}

# Baruch: ch1/2/4/5 identity (exact counts; Greek 4:1 aligns). ch3 has ONE
# verified split — KJV 3:34 ("stars shined... when he calleth them, they say,
# Here we be...") = Greek 3:34 + 3:35 (both map to 3:34 → concatenated), so
# KJV 3:35-37 = Greek 3:36-38.
_BAR_SEGMENTS: dict[int, list[_Seg]] = {
    3: [(1, 34, 3, 1), (35, 35, 3, 34), (36, _HI, 3, 35)],
}

# Letter of Jeremiah (Swete Epj): single head split — KJV 1:1 + 1:2 = Greek G1
# (the heading absorbs the "because of your sins" statement), then a uniform +1
# offset across all 72 Greek verses (KJV 1:2 receives no Greek of its own).
_LJE_SEGMENTS: dict[int, list[_Seg]] = {
    1: [(1, 1, 1, 1), (2, _HI, 1, 3)],
}

# Sirach (Swete `Sir`): the Greek 30:25–36:16a block transposition + the internal
# verse-merges within the moved blocks (the Greek splits many KJV verses into two;
# each 2nd half is omitted to avoid collisions). ALL boundaries derived by content-
# aligning the real Swete text against the KJV (NOT memory) — anchors: G30:25 = the
# grape-gatherer = KJV 33:16; G31:1=KJV34:1; G32:1=KJV35:1; G33:1=KJV36:1; G34:1=
# KJV31:1; G35:1=KJV32:1; G36:1=KJV33:1; G36:17=KJV36:12. G36:16 conflates the seam
# (KJV 33:16a + 36:11b, both covered elsewhere) → omit. Minors ch20/23/41 stay
# identity — each is Greek-fewer with only TERMINAL KJV extras that have no Greek
# (KJV 20:32, 23:28, 41:23-24; the ch20 empty G20:3 is skipped at reconstruct), so
# plain identity places every Greek verse correctly (verified verse-by-verse incl.
# the Sir 41 "be ashamed of" litany, which aligns 1:1 — NOT a division difference).
_SIR_SEGMENTS: dict[int, list[_Seg]] = {
    30: [(1, 24, 30, 1), (25, 40, 33, 16)],
    31: [
        (1, 10, 34, 1),
        (11, 11, 34, 10),
        (12, 14, 34, 11),
        (15, 15, 34, 13),
        (16, 17, 34, 14),
        (18, 18, 34, 15),
        (19, 21, 34, 16),
        (22, 22, 34, 18),
        (23, 26, 34, 19),
        (27, 27, 34, 22),
        (28, 31, 34, 23),
    ],
    32: [
        (1, 1, 35, 1),
        (2, 2, 35, 1),
        (3, 3, 35, 2),
        (4, 4, 35, 2),
        (5, 14, 35, 3),
        (15, 15, 35, 12),
        (16, 18, 35, 13),
        (19, 19, 35, 15),
        (20, 22, 35, 16),
        (23, 23, 35, 18),
        (24, 24, 35, 19),
        (25, 25, 35, 19),
        (26, 26, 35, 20),
    ],
    33: [(1, 6, 36, 1), (7, 7, 36, 6), (8, 8, 36, 7), (9, 9, 36, 7), (10, 13, 36, 8)],
    34: [(1, _HI, 31, 1)],
    35: [(1, _HI, 32, 1)],
    36: [(1, 15, 33, 1), (16, 16, None, 0), (17, _HI, 36, 12)],
}

# Esther: the six Greek Additions are each packed into one giant verse -> omit.
_EST_OMIT: frozenset[tuple[int, int]] = frozenset({(1, 1), (3, 13), (4, 17), (5, 1), (8, 12), (10, 3)})
# Exodus 36-39 (tabernacle construction) is reordered AND heavily abbreviated in
# the LXX; deferred (omit rather than ship a guessed alignment).
_EXO_DEFER_CHAPTERS: frozenset[int] = frozenset({36, 37, 38, 39})

# Tobit (Swete short recension `Tob`): ch1-5 + 8-14 identity (verified first+last).
# ch6 is a clean offset −1 — Greek 6:1 ("she ceased weeping") is the tail of KJV
# 5:22 (concatenated there), then Greek 6:2-18 → KJV 6:1-17. ch7 multi-divergence,
# content-verified: KJV 7:8 = G7:8+G7:9 (concatenated); G7:10 is the Greek-MERGE of
# KJV 7:9+7:10 (→7:9, so KJV 7:10 gets no Greek — can't split one source verse);
# G7:11→7:11; KJV 7:12 is absent in the short Greek; G7:12-17 → KJV 7:13-18.
_TOB_SEGMENTS: dict[int, list[_Seg]] = {
    6: [(1, 1, 5, 22), (2, _HI, 6, 1)],
    7: [(1, 7, 7, 1), (8, 8, 7, 8), (9, 9, 7, 8), (10, 10, 7, 9), (11, 11, 7, 11), (12, _HI, 7, 13)],
}

# Judith (Swete Jdt): ch1-14 identity (per-chapter counts match; ch14 verified verse-
# by-verse). The 15/16 hymn boundary diverges (content-aligned vs the real Greek↔KJV):
# the song-intro Greek 15:14 ("Judith began this thanksgiving in all Israel") = KJV
# 16:1, so KJV 16:1 receives no ch16 Greek of its own. ch16 then runs at offset +1
# (Greek 16:1 "Begin unto my God with timbrels" = KJV 16:2) until a catch-up MERGE:
# Greek 16:7 ("put off her widow's garment...anointed her face") + Greek 16:8 ("and
# bound her hair...linen garment to deceive him") are the two clauses of KJV 16:8
# (concatenated), after which offset 0 resumes (Greek 16:9-25 = KJV 16:9-25).
_JDT_SEGMENTS: dict[int, list[_Seg]] = {
    15: [(1, 13, 15, 1), (14, 14, 16, 1)],
    16: [(1, 7, 16, 2), (8, 8, 16, 8), (9, _HI, 16, 9)],
}

# 1 Esdras (Swete 1Es): ch4/7/9 identity (counts match). ch1/2/3/5/6/8 are Greek-FEWER
# than the KJV (Apocrypha) enumeration — the Greek combines verses the KJV splits, so a
# combined KJV verse gets no Greek of its own (an unmapped verse in a remapped chapter
# returns None — never fabricated). ALL boundaries content-aligned vs the real Swete↔KJV
# (NOT memory). Per chapter the net combine count = KJV−Greek: ch1 +3, ch2 +5, ch3 +1,
# ch5 +3, ch6 +1, ch8 +4. ch8 also has ONE Greek SPLIT (G8:49+G8:50 = KJV 8:50, the 2nd
# half concatenated by build_verses). Offsets step up at each combine; the segment
# kjv_v_lo encodes the running offset.
_1ES_SEGMENTS: dict[int, list[_Seg]] = {
    1: [(1, 10, 1, 1), (11, 16, 1, 12), (17, 49, 1, 19), (50, _HI, 1, 53)],
    2: [(1, 6, 2, 1), (7, 18, 2, 8), (19, 19, 2, 22), (20, 24, 2, 24), (25, _HI, 2, 30)],
    3: [(1, 14, 3, 1), (15, _HI, 3, 16)],
    5: [(1, 41, 5, 1), (42, 53, 5, 43), (54, 57, 5, 56), (58, _HI, 5, 61)],
    6: [(1, 8, 6, 1), (9, _HI, 6, 10)],
    8: [
        (1, 43, 8, 1),  # offset 0; G8:43 = KJV 8:43+44
        (44, 49, 8, 45),  # offset +1; G8:49 = first half of KJV 8:50
        (50, 50, 8, 50),  # the Greek SPLIT: G8:50 concatenated onto KJV 8:50 (offset back to 0)
        (51, 56, 8, 51),  # G8:56 = KJV 8:56+57
        (57, 62, 8, 58),  # offset +1; G8:62 = KJV 8:63+64
        (63, 63, 8, 65),  # offset +2; G8:63 = KJV 8:65+66
        (64, 90, 8, 67),  # offset +3; G8:90 = KJV 8:93+94
        (91, _HI, 8, 95),  # offset +4; G8:91-92 = KJV 8:95-96
    ],
}

_SEGMENT_BOOKS = {
    "jer": _JER_SEGMENTS,
    "dan": _DAN_SEGMENTS,
    "pro": _PRO_SEGMENTS,
    "1ki": _1KI_SEGMENTS,
    "bar": _BAR_SEGMENTS,
    "lje": _LJE_SEGMENTS,
    "sir": _SIR_SEGMENTS,
    "tob": _TOB_SEGMENTS,
    "jdt": _JDT_SEGMENTS,
    "1es": _1ES_SEGMENTS,
}


def _apply_segments(code: str, table: dict[int, list[_Seg]], ch: int, vs: int) -> tuple[int, int] | None:
    segs = table.get(ch)
    if segs is None:
        return (ch, vs)  # chapter not reordered -> identity
    for lo, hi, kjv_ch, kjv_v_lo in segs:
        if lo <= vs <= hi:
            if kjv_ch is None:
                return None
            return (kjv_ch, kjv_v_lo + (vs - lo))
    return None  # a remapped chapter but an unmapped verse -> omit (never misplace)


# Prayer of Azariah / Song of the Three (paz): the Theodotion-Daniel Addition Dat 3:24-90
# (already OMITTED from _DAN_SEGMENTS, so no fan-out conflict). Per-verse segments in PAZ
# coordinates (lxx_lo, lxx_hi, paz_ch | None, paz_v_lo). Content-aligned vs the real
# Greek↔KJV paz (NOT memory): the prayer G3:24-51 → paz 1:1-28 (offset −23); G3:52 combines
# KJV 1:29+1:30 (1:30 gets no Greek), dropping the litany to offset −22; the Benedicite
# REORDERS — Greek angels/heavens are swapped vs KJV, and the cold/frost/lightning block is
# permuted (G69 "cold&heat"→winter&summer 1:45, G70 "hoarfrost&snows"→1:50, G71→1:47,
# G72→1:48, G73 "lightnings&clouds"→1:51); G3:67/G3:68 are source-EMPTY, leaving KJV 1:46
# (dews&storms) + 1:49 (ice&cold) without Greek — exactly the two subjects the Greek omits.
_PAZ_FROM_DAT3: list[_Seg] = [
    (24, 51, 1, 1),  # Prayer of Azariah — offset −23
    (52, 52, 1, 29),  # G52 = KJV 1:29+1:30 (1:30 unmapped); offset → −22
    (53, 57, 1, 31),  # litany head (temple..works)
    (58, 58, 1, 37),  # angels — swapped with heavens
    (59, 59, 1, 36),  # heavens — swapped with angels
    (60, 66, 1, 38),  # waters-above .. fire&heat
    (67, 68, None, 0),  # source-EMPTY verses → omit
    (69, 69, 1, 45),  # "cold and heat" → winter and summer
    (70, 70, 1, 50),  # "hoarfrost and snows" → frost and snow
    (71, 71, 1, 47),  # nights and days
    (72, 72, 1, 48),  # light and darkness
    (73, 73, 1, 51),  # lightnings and clouds
    (74, 90, 1, 52),  # the earth .. all who worship — offset −22, monotonic to the end
]


def _cross_book(swete_book: str, ch: int, vs: int) -> Coord | None:
    """Relocations where a Swete source's verses belong to a project book DIFFERENT from
    any whole-book ``SWETE_BOOK_TO_CODE`` entry — returned as a full ``(code, ch, vs)``
    BEFORE the regular per-book handling. Two cases, both content-verified:

    - **Prayer of Manasseh (man):** Swete ``Ode 8`` (15 verses, clean identity onto KJV
      man 1, the Greek title in v1). VERIFIED Ode 8 in THIS digitization — the Rahlfs
      Ode-12 numbering does NOT apply (Ode 12 here is the Nunc Dimittis). Every other Ode
      is a canticle with no project home (Song of Moses, Magnificat, Benedictus, ...).
    - **Prayer of Azariah / Song of the Three (paz):** Theodotion ``Dat 3:24-90`` via
      ``_PAZ_FROM_DAT3`` (prayer + the reordered Benedicite). Dat 3:1-23 / 3:91+ still
      belong to dan (the regular path), so the intercept is bounded to 24-90."""
    if swete_book == "Ode":
        return ("man", 1, vs) if ch == 8 else None
    if swete_book == "Dat" and ch == 3 and 24 <= vs <= 90:
        for lo, hi, paz_ch, paz_v_lo in _PAZ_FROM_DAT3:
            if lo <= vs <= hi:
                return None if paz_ch is None else ("paz", paz_ch, paz_v_lo + (vs - lo))
        return None
    return None


def lxx_swete_to_kjv(swete_book: str, ch: int, vs: int) -> Coord | None:
    """Map a Swete LXX coordinate to its canonical (KJV/project) coordinate.

    Returns ``(proj_code, chapter, verse)`` or ``None`` to omit the verse (a book
    outside the 39-OT scope, a dropped superscription / Addition / doublet, or a
    coordinate the canonical book doesn't contain)."""
    cross = _cross_book(swete_book, ch, vs)
    if cross is not None:
        c_code, c_ch, c_v = cross
        return cross if coord_in_canonical_extent(c_code, c_ch, c_v) else None

    code = SWETE_BOOK_TO_CODE.get(swete_book)
    if code is None:
        return None

    if code == "psa":
        mapped = _psalm_map().get((ch, vs))
    elif code == "est":
        mapped = None if (ch, vs) in _EST_OMIT else (ch, vs)
    elif code == "exo":
        mapped = None if ch in _EXO_DEFER_CHAPTERS else (ch, vs)
    elif code in _SEGMENT_BOOKS:
        mapped = _apply_segments(code, _SEGMENT_BOOKS[code], ch, vs)
    else:
        mapped = (ch, vs)  # identity

    if mapped is None:
        return None
    kjv_ch, kjv_v = mapped
    if not coord_in_canonical_extent(code, kjv_ch, kjv_v):
        return None
    return (code, kjv_ch, kjv_v)


# ===========================================================================
# Greek NT (Robinson-Pierpont Byzantine Majority Text) -> canonical KJV.
#
# The Byzantine/ecclesiastical text uses KJV-standard versification, so the NT is
# IDENTITY for all 27 books — the single-verse Byzantine omissions (Luke 17:36,
# Acts 8:37 / 15:34 / 24:7) are gap-preserved in the source (KJV numbering kept).
# The one reorder is the Romans doxology: the Byzantine text places KJV 16:25-27
# at the end of chapter 14 (as 14:24-26). Verified against the real source.
# ===========================================================================

# byztxt CSV book code -> project 3-letter code (the 27 NT books). The apparatus
# files (PA = Pericope Adulterae, ACT24 = Acts-24 variant) are not here -> omitted.
_NT_BOOK_TO_CODE: dict[str, str] = {
    "MAT": "mat",
    "MAR": "mrk",
    "LUK": "luk",
    "JOH": "jhn",
    "ACT": "act",
    "ROM": "rom",
    "1CO": "1co",
    "2CO": "2co",
    "GAL": "gal",
    "EPH": "eph",
    "PHP": "phi",
    "COL": "col",
    "1TH": "1th",
    "2TH": "2th",
    "1TI": "1ti",
    "2TI": "2ti",
    "TIT": "tit",
    "PHM": "phm",
    "HEB": "heb",
    "JAM": "jam",
    "1PE": "1pe",
    "2PE": "2pe",
    "1JO": "1jn",
    "2JO": "2jn",
    "3JO": "3jn",
    "JUD": "jud",
    "REV": "rev",
}

# Romans: the doxology KJV 16:25-27 sits at the end of ch14 (as 14:24-26) in the
# Byzantine text; ch16 body (1-24) and every other chapter map identity.
_ROM_SEGMENTS: dict[int, list[_Seg]] = {14: [(1, 23, 14, 1), (24, 26, 16, 25)]}


def byzantine_to_kjv(book: str, ch: int, vs: int) -> Coord | None:
    """Map a Robinson-Pierpont Byzantine NT coordinate to canonical KJV.

    Identity for all 27 NT books except the Romans doxology reorder; ``None`` for
    apparatus/non-NT files or out-of-extent coordinates."""
    code = _NT_BOOK_TO_CODE.get(book)
    if code is None:
        return None
    mapped = _apply_segments(code, _ROM_SEGMENTS, ch, vs) if code == "rom" else (ch, vs)
    if mapped is None:
        return None
    kjv_ch, kjv_v = mapped
    if not coord_in_canonical_extent(code, kjv_ch, kjv_v):
        return None
    return (code, kjv_ch, kjv_v)


# ===========================================================================
# Arabic Van Dyck (arb-vd) -> canonical KJV.
#
# Van Dyck uses KJV/English versification across all 66 Protestant books — a full
# per-chapter probe vs the KJV skeleton (all 1189 chapters) agreed EVERYWHERE
# except two tail-splits where Van Dyck carries one extra trailing verse that the
# KJV folds into the preceding verse (content-aligned vs the real text):
#   1 Timothy 6: AVD 6:22 ("Grace be with thee. Amen.")        folds onto KJV 6:21
#   3 John 1:    AVD 1:15 ("Peace be to thee... by name.")     folds onto KJV 1:14
# Both are applied as a same-book merge (extract_translation.apply_remap then
# concatenates the two source verses in source order). NOTE: unlike the CSV-sourced
# lxx/byzantine adapters (which take the SOURCE book name), this one takes the
# PROJECT book code — it runs after extract_translation's eBible->project mapping.
# ===========================================================================

_ARABIC_TAIL_MERGE: dict[Coord, Coord] = {
    ("1ti", 6, 22): ("1ti", 6, 21),
    ("3jn", 1, 15): ("3jn", 1, 14),
}


def arabic_to_kjv(code: str, ch: int, vs: int) -> Coord | None:
    """Map an Arabic Van Dyck coordinate (already a project book code) to canonical
    KJV. Identity except the two tail-merges; ``None`` for out-of-extent coords."""
    mapped = _ARABIC_TAIL_MERGE.get((code, ch, vs), (code, ch, vs))
    m_code, m_ch, m_vs = mapped
    if not coord_in_canonical_extent(m_code, m_ch, m_vs):
        return None
    return mapped


# ===========================================================================
# Clementine Vulgate (Latin) + Douay-Rheims (English) -> canonical KJV.
#
# Both are 74-book Catholic, Vulgate-numbered; ONE shared map serves both. Input
# ``code`` is already a project book code (runs after extract_translation's map).
#
# TABLE-DRIVEN: the segment tables below were GENERATED from the Copenhagen Alliance
# versification mapping (``vul.json``, composed vul->org->KJV), then VERIFIED to
# SHIFTS=0 against the real eBible Douay text via the ``_vg_verify.py`` word-overlap
# gate (NOT hand-guessed, NOT from memory). Versification FACTS only — the CC BY-SA
# source JSON is not vendored; credit: Copenhagen Alliance + UBS/SIL.
#   - Psalms: Vulgate numbering == the LXX scheme, so reuse ``_psalm_map`` + the
#     ``_VULGATE_PSALM_FIXES`` Vulgate-only overrides; ``_psalm_map`` is shared with
#     the LXX ingest and is left untouched.
#   - Daniel/Esther additions go cross-book (``_vulgate_cross`` -> paz/sus/bel);
#     tob/jdt/sir omitted (divergent recension); everything else is identity.
#   - The 14 chapters where the Latin verse-count differs from the Douay are handled
#     by shared concat-tail segments (the shorter source never triggers the extra seg).
# ===========================================================================

# Per-(vulgate_ch, vulgate_vs) -> (kjv_ch, kjv_vs) overrides where the Douay's Latin
# verse-DIVISION diverges from the reused LXX ``_psalm_map`` (which was built for the
# Swete Greek division). The shared ``_psalm_map`` already handles the gross chapter
# renumbering (Vulgate 9 = KJV 9+10, Vulgate N = KJV N+1 for 10-112, etc.) and the
# leading-superscription drops; these per-verse patches correct the residual psalms
# where the Latin counts the title/clauses differently than the Greek, which would
# otherwise place the Douay body one verse off its KJV slot. ALL derived by reading
# the ENGLISH Douay against the ENGLISH KJV at the divergence (NOT memory) — the
# justifying texts are in the comment over each psalm's block. Keys are Vulgate
# (Douay) coordinates; values are canonical KJV. (Reused by BOTH the Clementine-
# Vulgate Latin driver and the Douay-Rheims English driver — the divergence is in the
# shared Vulgate numbering, not the language.)
_VULGATE_PSALM_FIXES: dict[tuple[int, int], tuple[int, int]] = {
    # --- Vulgate Ps 10 = KJV 11 -------------------------------------------------
    # The Greek (``_psalm_map``) keeps the title as its own dropped verse and runs
    # the body 1:1, but the DOUAY counts the Latin title as v1 AND keeps the opening
    # body line as a SEPARATE v2 ("In the Lord I put my trust...") — whereas the KJV
    # FOLDS the title into v1 ("...of David. In the LORD put I my trust..."). So the
    # Douay body sits +1 vs the Greek map. Fix: D 10:1 (title) + D 10:2 ("In the Lord
    # I put my trust: how then do you say to my soul: Get thee away") BOTH -> KJV 11:1
    # (the KJV v1 carries title+first-line); then D 10:3..10:8 -> KJV 11:2..11:7.
    # Anchors: D 10:7 "He shall rain snares upon sinners: fire and brimstone" = KJV
    # 11:6 "Upon the wicked he shall rain snares, fire and brimstone"; D 10:8 "For the
    # Lord is just, and hath loved justice" = KJV 11:7 "For the righteous LORD loveth
    # righteousness". (Without this, _psalm_map dropped D 10:8 — KJV 11:7 had no Douay.)
    (10, 2): (11, 1),
    (10, 3): (11, 2),
    (10, 4): (11, 3),
    (10, 5): (11, 4),
    (10, 6): (11, 5),
    (10, 7): (11, 6),
    (10, 8): (11, 7),
    # --- Vulgate Ps 12 = KJV 13 -------------------------------------------------
    # The Vulgate SPLITS KJV 13:2 into two — D 12:2 ("How long shall I take counsels
    # in my soul, sorrow in my heart all the day?") + D 12:3 ("How long shall my enemy
    # be exalted over me?") are the two clauses of KJV 13:2 ("How long shall I take
    # counsel... how long shall mine enemy be exalted over me?"). That drops the body
    # to -1: D 12:4 ("Consider, and hear me... Enlighten my eyes") = KJV 13:3; D 12:5
    # ("Lest at any time my enemy say: I have prevailed... They that trouble me") =
    # KJV 13:4; D 12:6 ("But I have trusted in thy mercy... I will sing to the Lord...
    # I will sing to the name of the Lord the most high") = KJV 13:5 ("...rejoice in
    # thy salvation") + KJV 13:6 ("I will sing unto the LORD..."), a MERGE — so KJV
    # 13:6 is a verified fold (its "I will sing" is the tail of D 12:6).
    (12, 3): (13, 2),
    (12, 4): (13, 3),
    (12, 5): (13, 4),
    (12, 6): (13, 5),
    # --- Vulgate Ps 19 = KJV 20 -------------------------------------------------
    # This Douay psalm has only 9 verses for a 9-verse KJV 20, but the Greek map
    # (LXX Ps 19 = 10 verses) expects 10, so _psalm_map left KJV 20:9 with no Douay.
    # The Vulgate MERGES KJV 20:8 + 20:9 into the single D 19:9 ("They are bound, and
    # have fallen; but we are risen, and are set upright. O Lord, save the king: and
    # hear us in the day that we shall call upon thee") — the first sentence = KJV
    # 20:8 ("They are brought down and fallen: but we are risen, and stand upright"),
    # the second = KJV 20:9 ("Save, LORD: let the king hear us when we call"). Map the
    # trailing D 19:9 onto the trailing KJV 20:9 (resolving that empty slot); KJV 20:8
    # then holds the verified merge-fold (its content is D 19:9's head).
    (19, 9): (20, 9),
    # --- Vulgate Ps 43 = KJV 44 -------------------------------------------------
    # The Vulgate MERGES KJV 44:21 + 44:22 into D 43:22 ("Shall not God search out
    # these things: for he knoweth the secrets of the heart. Because for thy sake we
    # are killed all the day long: we are counted as sheep for the slaughter") — first
    # clause = KJV 44:21, second = KJV 44:22. _psalm_map correctly puts D 43:22 -> 44:21
    # but then runs the rest -1, putting the body one slot low (KJV 44:22 wrongly took
    # D 43:23 "Arise, why sleepest thou"). Fix the tail +1: D 43:23 ("Arise, why
    # sleepest thou, O Lord?") = KJV 44:23; D 43:24 = KJV 44:24; D 43:25 = KJV 44:25;
    # D 43:26 ("Arise, O Lord, help us and redeem us for thy name's sake") = KJV 44:26
    # (resolving that empty slot). KJV 44:22 ("Yea, for thy sake are we killed...") is
    # then the verified merge-fold (its content is D 43:22's tail).
    (43, 23): (44, 23),
    (43, 24): (44, 24),
    (43, 25): (44, 25),
    (43, 26): (44, 26),
    # --- Vulgate Ps 55 = KJV 56 -------------------------------------------------
    # The Vulgate MERGES KJV 56:10 + 56:11 into D 55:11 ("In God will I praise the
    # word, in the Lord will I praise his speech. In God have I hoped, I will not fear
    # what man can do to me") — first sentence = KJV 56:10, second = KJV 56:11. So the
    # body runs -1 from there: D 55:12 ("In me, O God, are vows to thee, which I will
    # pay, praises to thee") = KJV 56:12 ("Thy vows are upon me, O God: I will render
    # praises unto thee"); D 55:13 ("Because thou hast delivered my soul from death...
    # in the light of the living") = KJV 56:13 (resolving that empty slot). KJV 56:11
    # ("In God have I put my trust: I will not be afraid...") is the verified merge-
    # fold (its content is D 55:11's tail).
    (55, 12): (56, 12),
    (55, 13): (56, 13),
    # --- Vulgate Ps 108 = KJV 109 -----------------------------------------------
    # A SPLIT + a compensating MERGE (counts stay 31=31, so the tail is otherwise 1:1).
    # The Vulgate SPLITS KJV 109:16 into D 108:16 ("Because he remembered not to show
    # mercy,") + D 108:17 ("But persecuted the poor man and the beggar; and the broken
    # in heart, to put him to death") — together = KJV 109:16 ("Because that he
    # remembered not to shew mercy, but persecuted the poor and needy man, that he
    # might even slay the broken in heart"). It then MERGES KJV 109:17 + 109:18 into
    # D 108:18 ("And he loved cursing, and it shall come unto him... And he put on
    # cursing, like a garment: and it went in like water... like oil in his bones") =
    # KJV 109:17 ("As he loved cursing, so let it come unto him...") + KJV 109:18 ("As
    # he clothed himself with cursing... like water... oil into his bones"). Fix:
    # D 108:17 -> KJV 109:16 (merge into 16) and D 108:18 -> KJV 109:17; identity then
    # resumes (D 108:19 "like a garment which covereth him... a girdle" = KJV 109:19).
    # KJV 109:18 is the verified merge-fold (its content is D 108:18's tail).
    (108, 17): (109, 16),
    (108, 18): (109, 17),
    # --- Douay-only trailing verse (Vulgate count == KJV count, Douay has +1) --------
    # The shared ``_psalm_map`` is built from the Swete Greek per-psalm counts, which
    # match the Latin Vulgate AND the KJV for these three psalms; but the ENGLISH Douay
    # carries ONE extra trailing verse (it splits the psalm's closing line in two). With
    # no map key, that trailing Douay verse returned None and was DROPPED. Fold each onto
    # the LAST KJV verse of the psalm (concatenated). The Latin Vulgate never has these
    # verse numbers, so the overrides are harmless for the Vulgate driver. Verified by
    # reading the Douay tail against the KJV:
    #   Ps 42 = KJV 43: D 42:6 ("Hope in God, for I will still give praise to him: the
    #     salvation of my countenance, and my God") = the tail of KJV 43:5 ("...for I
    #     shall yet praise him, who is the health of my countenance, and my God").
    (42, 6): (43, 5),
    #   Ps 125 = KJV 126: D 125:7 ("But coming they shall come with joyfulness, carrying
    #     their sheaves") = the tail of KJV 126:6 ("...shall doubtless come again with
    #     rejoicing, bringing his sheaves with him").
    (125, 7): (126, 6),
    #   Ps 135 = KJV 136: D 135:27 ("Give glory to the Lord of lords: for his mercy
    #     endureth for ever") = the tail of KJV 136:26 ("O give thanks unto the God of
    #     heaven: for his mercy endureth for ever") -- the Douay's doubled doxology line.
    (135, 27): (136, 26),
}

# Per-book verse-segment tables (source = Vulgate/Douay numbering -> canonical KJV),
# each content-aligned by reading the ENGLISH Douay against the ENGLISH KJV at the
# divergence (NOT identity-guessed). Segment = (src_lo, src_hi, kjv_ch, kjv_v_lo); a
# verse v in [lo,hi] -> (kjv_ch, kjv_v_lo + (v - lo)). A KJV verse that no segment
# targets gets no Douay/Vulgate (the Vulgate folded it into a neighbour — like the
# LXX cases). ``_HI`` = open upper bound. Chapters absent here map identity.
_VULGATE_SEGMENTS: dict[str, dict[int, list[_Seg]]] = {
    "1ch": {
        # ch11 mighty-men list: the Vulgate MERGES KJV 11:32+11:33 into Douay 11:32
        # (Douay 11:32 already lists Azmoth/Eliaba = KJV 11:33's "Azmaveth... Eliahba"),
        # so KJV 11:33 folds into Douay 11:32. Then Douay 11:33 ("sons of Assem... Sage")
        # = KJV 11:34, Douay 11:34+11:35 = KJV 11:35 (merge), and 11:36-45 resume
        # identity. The tail 11:46/47 merge is the existing (46,_HI,11,47).
        11: [
            (1, 32, 11, 1),
            (33, 33, 11, 34),
            (34, 34, 11, 35),
            (35, 35, 11, 35),
            (36, 45, 11, 36),
            (46, _HI, 11, 47),
        ],
        20: [(1, 6, 20, 1), (7, _HI, 20, 8)],  # composed
    },
    "1es": {
        1: [
            (1, 9, 1, 1),
            (10, 13, 1, 11),
            (14, 15, 1, 14),
            (16, 17, 1, 15),
            (18, 51, 1, 16),
            (52, _HI, 1, 49),
        ],  # composed
        2: [
            (1, 1, 2, 1),
            (2, 3, 2, 1),
            (4, 6, 2, 2),
            (7, 11, 2, 4),
            (12, 12, 2, 8),
            (13, 14, 2, 10),
            (15, 20, 2, 11),
            (21, 22, 2, 16),
            (23, 25, 2, 17),
            (26, 29, 2, 21),
            (30, _HI, 2, 26),
        ],  # composed
        3: [(1, 14, 3, 1), (15, 16, 3, 14), (17, _HI, 3, 17)],  # composed
        4: [(1, 9, 4, 1), (10, 10, 4, 11), (11, 32, 4, 11), (33, 33, 4, 34), (34, _HI, 4, 34)],  # composed
        5: [
            (1, 41, 5, 1),
            (42, 54, 5, 41),
            (55, 57, 5, 53),
            (58, 58, 5, 57),
            (59, 59, 5, 57),
            (60, 72, 5, 57),
            (73, _HI, 5, 71),
        ],  # composed
        6: [(1, 8, 6, 1), (9, _HI, 6, 8)],  # composed
        8: [
            (1, 43, 8, 1),
            (44, 49, 8, 43),
            (50, 56, 8, 50),
            (57, 63, 8, 56),
            (64, 65, 8, 62),
            (66, 85, 8, 63),
            (86, 86, 8, 84),
            (87, 93, 8, 84),
            (94, _HI, 8, 90),
        ],  # composed
    },
    "1ma": {
        # ch1 carries several Vulgate splits/merges vs KJV (all content-verified):
        #  - KJV 1:4 = Douay 1:4+1:5 (merge); offset -1 through Douay 1:21=KJV1:20.
        #  - KJV 1:20 = Douay 1:21 ("returned... against Israel") + 1:22 ("went up to
        #    Jerusalem with a great multitude") (Vulgate SPLITS KJV 1:20).
        #  - Douay 1:23 ("proudly entered the sanctuary... table of proposition...")
        #    = KJV 1:21+1:22 (Vulgate MERGE); KJV 1:22 folds into Douay 1:23.
        #  - Douay 1:24-31 = KJV 1:23-30; KJV 1:30 = Douay 1:31+1:32 (merge).
        #  - KJV 1:35 = Douay 1:36+1:37 (merge); KJV 1:34 folds into Douay 1:35.
        #  - KJV 1:45 = Douay 1:47+1:48 (merge).
        #  - Douay 1:51 ("leave children uncircumcised... forget the law... change all
        #    the justifications") = KJV 1:48+1:49; KJV 1:49 folds into Douay 1:51.
        #  - Douay 1:52 ("whosoever would not... should be put to death") = KJV 1:50;
        #    KJV 1:51 = Douay 1:53 ("wrote to his whole kingdom... rulers") + 1:54
        #    ("commanded the cities of Juda to sacrifice") (merge). Offset -3 to end.
        1: [
            (1, 4, 1, 1),
            (5, 21, 1, 4),
            (22, 22, 1, 20),
            (23, 23, 1, 21),
            (24, 31, 1, 23),
            (32, 35, 1, 30),
            (36, 36, 1, 35),
            (37, 47, 1, 35),
            (48, 51, 1, 45),
            (52, 52, 1, 50),
            (53, 53, 1, 51),
            (54, 54, 1, 51),
            (55, _HI, 1, 52),
        ],
        12: [(1, 53, 12, 1), (54, _HI, 12, 53)],  # composed
        13: [(1, 52, 13, 1), (53, _HI, 13, 52)],  # composed
    },
    "1ki": {
        # ch22 Jehoshaphat reign-summary: the Vulgate SPLITS KJV 22:43 into two —
        # Douay 22:43 ("walked in all the way of Asa... did right") = KJV 22:43a,
        # Douay 22:44 ("Nevertheless he took not away the high places...") = KJV 22:43b
        # (concatenated). From Douay 22:45 ("had peace with the king of Israel" =
        # KJV 22:44) on, offset +1 to the chapter end (Douay 22:54 = KJV 22:53).
        22: [(1, 43, 22, 1), (44, 44, 22, 43), (45, _HI, 22, 44)],
    },
    "1sa": {
        20: [(1, 42, 20, 1), (43, _HI, 20, 42)],  # composed
        # Vulgate breaks ch23/24 one verse early: Douay 24:1 ("Then David went up
        # from thence, and dwelt in strong holds of Engaddi") = KJV 23:29; then
        # Douay 24:2+ = KJV 24:1+ (the cave episode).
        24: [(1, 1, 23, 29), (2, _HI, 24, 1)],
    },
    # NOTE: 1th ch4, 2th ch2 (and isa ch46) are DELIBERATELY left identity — see the
    # comment over isa for why a shared per-source merge-fold segment is impossible here.
    "2co": {
        13: [(1, 12, 13, 1), (13, 13, 13, 14)],  # kept-encoded
    },
    "2ma": {
        2: [(1, 18, 2, 1), (19, _HI, 2, 18)],  # composed
        12: [(1, 45, 12, 1), (46, _HI, 12, 45)],  # composed
        15: [(1, 36, 15, 1), (37, _HI, 15, 36)],  # composed
    },
    "act": {
        7: [(1, 55, 7, 1), (56, _HI, 7, 57)],  # restore prior act7
        8: [(1, 7, 8, 1), (8, 8, 8, 7), (9, _HI, 8, 9)],  # D8:8=K8:7 fold; D8:9=K8:9 (K8:8 folded into D8:9)
        14: [(1, 6, 14, 1), (7, _HI, 14, 8)],  # restore prior act14
    },
    "amo": {
        6: [(1, 10, 6, 1), (11, 11, 6, 10), (12, _HI, 6, 11)],  # KJV 6:10 split into Douay 6:10+6:11
    },
    "bar": {
        # ch3 SPLITS KJV 3:34 into two: Douay 3:34 ("the stars have given light in
        # their watches, and rejoiced") = KJV 3:34a; Douay 3:35 ("They were called,
        # and they said: Here we are... shined forth") = KJV 3:34b (concatenated).
        # Then Douay 3:36-38 = KJV 3:35-37 (offset -1).
        3: [(1, 34, 3, 1), (35, 35, 3, 34), (36, _HI, 3, 35)],
    },
    "dan": {
        # ch3 runs to Douay 3:100 (additions 3:24-90 -> paz via _vulgate_cross). The
        # post-furnace narrative resumes at Douay 3:91 ("Then Nabuchodonosor... was
        # astonished... three men bound into the midst of the fire" = KJV 3:24) and runs
        # to Douay 3:97 ("the king promoted Sidrach... in the province of Babylon" = KJV
        # 3:30): Douay 3:91-97 -> KJV 3:24-30. The Vulgate then ENDS ch3 with the doxology
        # KJV opens ch4 with: Douay 3:98 ("Nabuchodonosor the king, to all peoples,
        # nations, and tongues... peace be multiplied" = KJV 4:1), 3:99 ("The most high
        # God hath wrought signs and wonders toward me. It hath seemed good to me
        # therefore to publish" = KJV 4:2), 3:100 ("His signs, because they are great...
        # his kingdom is an everlasting kingdom... his power to all generations" = KJV
        # 4:3). So Douay 3:98-100 -> KJV 4:1-3 (cross-chapter). vs 24-90 (Prayer of Azariah
        # + Song of the Three) are routed to paz 1:1-67 by _vulgate_cross BEFORE this table
        # runs, so there is deliberately no segment for them here.
        3: [(1, 23, 3, 1), (91, 97, 3, 24), (98, 100, 4, 1)],
        # ch4: the doxology (KJV 4:1-3) was consumed by Douay 3:98-100 above, so Douay ch4
        # opens at the narrative KJV puts at 4:4 -- Douay 4:1 ("I, Nabuchodonosor, was at
        # rest in my house, and flourishing in my palace" = KJV 4:4) -- a uniform +3 to
        # Douay 4:34 ("Therefore I Nabuchodonosor do now praise... glorify the King of
        # heaven... able to abase" = KJV 4:37). So Douay 4:1-34 -> KJV 4:4-37.
        4: [(1, _HI, 4, 4)],
        # ch5/ch6 are IDENTITY in this Douay digitization (verified by reading): Douay ch5
        # carries 31 verses with Douay 5:31 ("And Darius the Mede succeeded to the kingdom,
        # being threescore and two years old") = KJV 5:31 -- already KJV-aligned, NOT
        # relocated to 6:1. Douay 6:1 ("It seemed good to Darius, and he appointed... a
        # hundred and twenty governors") = KJV 6:1, ch6 runs 1-28 identity. No segment
        # needed (absent chapters map identity).
    },
    "ecc": {
        # The Vulgate carries an EXTRA trailing verse in ch4: Douay 4:17 ("Keep thy
        # foot, when thou goest into the house of God") = KJV 5:1. (KJV ch4 ends at
        # v16; "Keep thy foot" opens KJV ch5.) So ch4 is identity 1-16 + a tail to 5:1.
        4: [(1, 16, 4, 1), (17, 17, 5, 1)],
        # Consequently all of Douay ch5 is +1: Douay 5:1 ("Speak not any thing
        # rashly... for God is in heaven") = KJV 5:2, ... Douay 5:19 = KJV 5:20.
        5: [(1, _HI, 5, 2)],
        7: [(1, 1, 6, 12), (2, _HI, 7, 1)],  # composed
    },
    "exo": {
        # The English Douay-Rheims source here is ALREADY re-chaptered to the KJV
        # layout for the tabernacle account (ch36/37 align identity; the LXX-deferral
        # of exo36-39 is a Greek-Swete problem, NOT a Douay one). Only the metal-tally
        # (ch38) and the priestly-vestments construction (ch39) have internal verse-
        # division differences; both are MONOTONIC (no verse out of order) and resolve
        # to clean fold/split segments. Read Douay-vs-KJV verse by verse to derive each.
        #
        # ch38 (metal tally): Douay & KJV both 31 verses. Douay 38:1-24 = KJV 38:1-24
        # (gold). The Vulgate then DROPS the standalone silver-total sentence (KJV 38:25
        # "the silver of them that were numbered... an hundred talents, and a thousand
        # seven hundred and threescore and fifteen shekels") -- its figures resurface in
        # Douay 38:26 (hundred talents) and 38:28 (1775) -- so KJV 38:25 is a fold.
        # Douay 38:25 ("offered by them that went to be numbered, from twenty years
        # old... six hundred and three thousand five hundred and fifty") = KJV 38:26
        # (the census/bekah). KJV 38:27 (hundred talents -> sockets) is SPLIT into Douay
        # 38:26 ("hundred talents of silver, whereof were cast the sockets") + 38:27
        # ("hundred sockets... a talent for every socket"). Identity resumes Douay
        # 38:28 = KJV 38:28 (the 1775 -> hooks/pillar-heads).
        38: [
            (1, 24, 38, 1),
            (25, 25, 38, 26),
            (26, 26, 38, 27),
            (27, 27, 38, 27),
            (28, _HI, 38, 28),
        ],
        # ch39 (vestments): Douay & KJV both 43 verses, but the breastplate/ephod
        # construction is told at a wandering granularity. Douay 39:1-18 = KJV 39:1-18.
        # The Vulgate then COMPRESSES the two ring-pairs: KJV 39:19 ("two rings of gold
        # ... on the side of the ephod inward") + KJV 39:20 ("two other golden rings...
        # over against the coupling") have no own Douay verse (folds) -- Douay 39:18-19
        # paraphrase the binding -- so Douay 39:19 ("fastened to the girdle... violet
        # fillet... lest they should flag loose") = KJV 39:21 (offset +2). That +2 holds
        # to Douay 39:25 ("fine linen tunicks... for Aaron and his sons") = KJV 39:27.
        # KJV 39:28 SPLITS into Douay 39:26 ("mitres... of fine linen") + 39:27 ("linen
        # breeches of fine linen"), dropping the offset to +1. That +1 holds to Douay
        # 39:37 ("altar of gold, ointment, incense") = KJV 39:38, then KJV 39:38 SPLITS
        # into Douay 39:37 + 39:38 ("hanging in the entry of the tabernacle"), closing
        # the offset to 0. Identity resumes Douay 39:39 = KJV 39:39 (brazen altar) to
        # the chapter end (Douay 39:43 = KJV 39:43, Moses blesses them). Folds: KJV
        # 39:19, 39:20. All KJV targets are non-decreasing -- a compression, not a reorder.
        39: [
            (1, 18, 39, 1),
            (19, 19, 39, 21),
            (20, 25, 39, 22),
            (26, 26, 39, 28),
            (27, 27, 39, 28),
            (28, 37, 39, 29),
            (38, 38, 39, 38),
            (39, _HI, 39, 39),
        ],
        40: [(1, 12, 40, 1), (13, _HI, 40, 15)],  # composed
    },
    "eze": {
        2: [(1, 8, 2, 1), (9, _HI, 2, 10)],  # composed
    },
    "gen": {
        49: [(1, 31, 49, 1), (32, 32, 49, 33)],  # KJV 49:32 (field purchase) folds into Douay 49:31; identity 1-31
        50: [(1, 22, 50, 1), (23, _HI, 50, 24)],
    },
    "hag": {
        2: [(1, 1, 1, 15), (2, _HI, 2, 1)],  # composed
    },
    "hos": {
        2: [(1, 23, 2, 1), (24, _HI, 2, 23)],  # composed
        6: [(1, 1, 6, 1), (2, 2, 6, 1), (3, 3, 6, 2), (4, _HI, 6, 4)],  # kept-encoded
        14: [(1, 1, 13, 16), (2, _HI, 14, 1)],  # kept-encoded
    },
    "isa": {
        8: [(1, 21, 8, 1), (22, _HI, 9, 1)],  # composed
        9: [(1, 19, 9, 1), (20, 20, 9, 21), (21, _HI, 9, 21)],  # composed
        # ch45: the Douay SPLITS the final KJV 45:25 ("In the LORD shall all the seed
        # of Israel be justified, and shall glory") into two -- Douay 45:25 ("Therefore
        # shall he say: In the Lord are my justices and empire; they shall come to him,
        # and all that resist him shall be confounded") + Douay 45:26 ("In the Lord
        # shall all the seed of Israel be justified and praised"). The Latin Vulgate
        # has only 25 verses (45:25 = "In Domino justificabitur, et laudabitur omne
        # semen Israel" = KJV 45:25), so the Vulgate never triggers the (26,...) seg.
        # Without this, the trailing Douay 45:26 mapped out-of-extent and was DROPPED;
        # the seg folds it onto KJV 45:25 (concatenated). Identity 1-25 otherwise.
        45: [(1, 25, 45, 1), (26, _HI, 45, 25)],
        # NOTE on isa46 / 1th4 / 2th2 (left DELIBERATELY identity, NO segment): in each
        # of these three the Latin Vulgate has the SAME verse count as the KJV and is
        # correctly identity-aligned, while the ENGLISH Douay carries one FEWER verse (a
        # genuine merge in the Douay's own division — e.g. Douay isa 46:11 absorbs KJV
        # 46:12's "Hear me, O ye hardhearted", Douay 1th 4:11 absorbs KJV 4:12, Douay
        # 2th 2:10 absorbs KJV 2:11). A merge-fold segment that re-slots the Douay tail
        # by +1 is correct for the Douay but WRONG for the Latin, because vulgate_to_kjv
        # is a SINGLE shared adapter (no per-translation branch) and the Latin DOES carry
        # those higher verse numbers — applying the shift would misplace the Latin body
        # and DROP its real trailing verse (e.g. Latin isa 46:13 -> out-of-extent). Since
        # the Latin (the larger source) already equals the KJV count, NEITHER source
        # drops content under plain identity (the Douay's shorter count just folds its
        # last verse onto the preceding KJV slot); only the Douay popups sit one slot off
        # in the merge region. This is the documented benign-fold case (vs isa45, where
        # the DOUAY is the larger source and its extra v26 WOULD drop -> a real fix above).
        64: [(1, 1, 63, 19), (2, _HI, 64, 2)],  # composed
    },
    "jdg": {
        5: [(1, 31, 5, 1), (32, _HI, 5, 31)],  # composed
        21: [(1, 23, 21, 1), (24, _HI, 21, 25)],  # composed
    },
    "jer": {
        37: [(1, 3, 37, 1), (4, _HI, 37, 5)],  # composed
    },
    "jhn": {
        6: [(1, 51, 6, 1), (52, 52, 6, 51), (53, _HI, 6, 52)],  # KJV 6:51 split into Douay 6:51+6:52
        10: [(1, 41, 10, 1), (42, 42, 10, 41)],  # D10:42=K10:41 fold (K10:42 folded into D10:42)
    },
    "jon": {2: [(1, 1, 1, 17), (2, _HI, 2, 1)]},  # Douay 2:1 (great fish) = KJV 1:17 (cross-chapter)
    "job": {
        16: [(1, 4, 16, 1), (5, _HI, 16, 4)],  # composed
        39: [(1, 30, 39, 1), (31, _HI, 40, 1)],  # composed
        40: [(1, 19, 40, 6), (20, _HI, 41, 1)],  # composed
        41: [(1, _HI, 41, 10)],  # composed
        42: [(1, 15, 42, 1), (16, _HI, 42, 17)],  # composed
    },
    "jos": {
        4: [(1, 23, 4, 1), (24, _HI, 4, 23)],  # composed
        5: [(1, 14, 5, 1), (15, _HI, 5, 14)],  # composed
        21: [(1, 35, 21, 1), (36, 36, 21, 37), (37, _HI, 21, 39)],  # composed
    },
    "lev": {
        # ch15: Douay & KJV both 33 verses; vv19-23 carry a verified split+fold (NOT mere
        # wording -- each Douay verse below sits clearly on a KJV NEIGHBOUR, not its own
        # slot). The Vulgate SPLITS KJV 15:19 -> Douay 15:19 ("woman... issue of blood...
        # separated seven days") + 15:20 ("Every one that toucheth her, shall be unclean
        # until the evening" = the KJV 15:19 tail). That makes Douay run -1: Douay 15:21
        # ("every thing that she sleepeth/sitteth on... defiled") = KJV 15:20; 15:22 ("He
        # that toucheth her bed shall wash his clothes") = KJV 15:21; 15:23 ("touch any
        # vessel on which she sitteth, shall wash his clothes") = KJV 15:22. KJV 15:23
        # ("if it be on her bed, or on any thing whereon she sitteth, when he toucheth it")
        # is then folded (compressed into Douay 15:23), and identity resumes Douay 15:24 =
        # KJV 15:24 (the man who lies with her).
        15: [
            (1, 18, 15, 1),
            (19, 19, 15, 19),
            (20, 20, 15, 19),
            (21, 23, 15, 20),
            (24, _HI, 15, 24),
        ],
        26: [(1, 44, 26, 1), (45, _HI, 26, 46)],  # composed
    },
    "lje": {
        # The Letter of Jeremiah arrives as source BAR ch6, auto-split to project book lje
        # ch1 (so Douay lje 1:N = source BAR 6:N). Two verified divergences (read Douay vs
        # KJV at each):
        #  - HEAD: KJV 1:1 is a standalone epistle heading ("A copy of an epistle, which
        #    Jeremy sent unto them... as it was commanded him of God") the Douay does NOT
        #    carry as its own verse; Douay opens at the body. So Douay 1:1 ("For the sins
        #    that you have committed before God, you shall be carried away captives into
        #    Babylon...") = KJV 1:2, a uniform +1. That +1 holds to Douay 1:41 (= KJV 1:42).
        #  - MID merge: Douay 1:42 ("The women also with cords about them, sit in the ways,
        #    burning olive stones.") + Douay 1:43 ("And when any one of them, drawn away by
        #    some passenger, lieth with him, she upbraideth her neighbour... nor her cord
        #    broken.") are the two halves of the single KJV 1:43 ("The women also with cords
        #    ... sitting in the ways, burn bran... but if any of them, drawn by some that
        #    passeth by, lie with him... nor her cord broken."). So Douay 1:42+1:43 -> KJV
        #    1:43 (merge); offset drops to 0 and Douay 1:44-51 = KJV 1:44-51.
        #  - MID fold: Douay 1:51 ("Whence therefore is it known that they are not gods, but
        #    the work of men's hands, and no work of God is in them?") = KJV 1:51 ("And it
        #    shall manifestly appear to all nations and kings that they are no gods, but the
        #    works of men's hands, and that there is no work of God in them") -- the Douay
        #    folds the short rhetorical KJV 1:52 ("Who then may not know that they are no
        #    gods?") into this same verse, so KJV 1:52 is a verified fold. Offset returns to
        #    +1: Douay 1:52 ("They cannot set up a king over the land, nor give rain to men")
        #    = KJV 1:53, sustained +1 to the tail Douay 1:72 ("Better therefore is the just
        #    man that hath no idols...") = KJV 1:73.
        # Verified folds (no own Douay verse): KJV 1:1 (heading) and KJV 1:52.
        1: [
            (1, 41, 1, 2),
            (42, 42, 1, 43),
            (43, 43, 1, 43),
            (44, 51, 1, 44),
            (52, _HI, 1, 53),
        ],
    },
    "mat": {
        5: [(1, 3, 5, 1), (4, 4, 5, 5), (5, 5, 5, 4), (6, _HI, 5, 6)],  # D5:4=K5:5, D5:5=K5:4 (Beatitudes swap)
        17: [(1, 14, 17, 1), (15, _HI, 17, 16)],  # composed
    },
    "mic": {
        5: [(1, 11, 5, 1), (12, _HI, 5, 13)],  # KJV 5:12 folds into Douay 5:11
    },
    "mrk": {
        4: [(1, 39, 4, 1), (40, _HI, 4, 41)],  # composed
        8: [(1, 38, 8, 1), (39, _HI, 9, 1)],  # composed
        9: [(1, _HI, 9, 2)],  # composed
    },
    "neh": {
        3: [(1, 29, 3, 1), (30, _HI, 3, 31)],  # composed
        # ch7 Levites/singers list: the Vulgate SPLITS KJV 7:43 across Douay 7:43
        # ("children of Josue and Cedmihel, the sons") + 7:44 ("Of Oduia, seventy-
        # four. The singing men:"), so Douay 7:44 = KJV 7:43 (merge). Then Douay
        # 7:45 ("children of Asaph, 148") = KJV 7:44, 7:46 = KJV 7:45 (porters),
        # 7:47 = KJV 7:46 (Nethinims), 7:48 ("Ceros... Lebana, Hagaba, Selmai") =
        # KJV 7:47+7:48 (merge; KJV 7:48 folds into Douay 7:48). Identity resumes at
        # Douay 7:49 = KJV 7:49. The 7:67/68 horses-merge tail is unchanged.
        7: [
            (1, 43, 7, 1),
            (44, 44, 7, 43),
            (45, 48, 7, 44),
            (49, 67, 7, 49),
            (68, 68, 7, 67),
            (69, _HI, 7, 69),
        ],
        12: [(1, 32, 12, 1), (33, _HI, 12, 34)],  # composed
    },
    "num": {
        # ch11: the Vulgate MERGES KJV 11:34 (Kibroth-hattaavah "graves of lust...
        # buried the people that lusted") + KJV 11:35 (Hazeroth "departing from the
        # graves of lust, they came unto Haseroth") into ONE Douay 11:34. So Douay
        # 11:1-34 = KJV 11:1-34 (identity); KJV 11:35 is a verified fold (its Hazeroth
        # clause is concatenated inside Douay 11:34, which can't be split back out).
        11: [(1, 34, 11, 1)],
        12: [(1, _HI, 12, 1)],  # identity (KJV 12:16 supplied cross-chapter by Douay 13:1)
        13: [(1, 1, 12, 16), (2, _HI, 13, 1)],  # composed
        # ch16: Douay & KJV both 50 verses; only the v42/43 boundary differs. KJV ends
        # 16:42 with "the cloud covered it, and the glory of the LORD appeared" and makes
        # "Moses and Aaron came before the tabernacle" its own 16:43. The Vulgate ends
        # Douay 16:42 at the gathering ("when there arose a sedition, and the tumult
        # increased") and folds BOTH the tabernacle-approach AND the cloud/glory into one
        # Douay 16:43 ("Moses and Aaron fled to the tabernacle... the cloud covered it,
        # and the glory of the Lord appeared"). So Douay 16:43 -> KJV 16:42 (merge), and
        # KJV 16:43 is a verified fold (its clause is the head of Douay 16:43). Identity
        # resumes Douay 16:44 = KJV 16:44 (the LORD spake to Moses).
        16: [(1, 42, 16, 1), (43, 43, 16, 42), (44, _HI, 16, 44)],
        # ch15: Douay & KJV both 41 verses, but vv11-21 are internally redistributed.
        # The Vulgate SPLITS KJV 15:11 -> Douay 15:11 ("Thus shalt thou do:") + 15:12
        # ("For every ox and ram and lamb and kid"); KJV 15:12 ("According to the
        # number...") has no Douay (fold). It SPLITS KJV 15:13 -> Douay 15:13+15:14;
        # KJV 15:14 (stranger sojourn) + 15:15 (one ordinance) fold (Douay abbreviates
        # the stranger clauses to a single 15:15 = KJV 15:16). Then Douay 15:16 = KJV
        # 15:17, and KJV 15:18 SPLITS -> Douay 15:17 ("Speak to the children") + 15:18
        # ("When you are come into the land"). Identity resumes at Douay 15:19 = KJV
        # 15:19. Net folds: KJV 15:12, 15:14, 15:15.
        15: [
            (1, 11, 15, 1),
            (12, 12, 15, 11),
            (13, 13, 15, 13),
            (14, 14, 15, 13),
            (15, 15, 15, 16),
            (16, 16, 15, 17),
            (17, 17, 15, 18),
            (18, 18, 15, 18),
            (19, _HI, 15, 19),
        ],
        20: [(1, 28, 20, 1), (29, _HI, 20, 28)],  # composed
        # ch27 (Zelophehad's daughters): Douay & KJV both 23 verses; vv3-8 redistributed.
        # The Vulgate MERGES KJV 27:3 ("died in his own sin... no sons") + KJV 27:4
        # ("Why should the name... be done away... Give us a possession") into one Douay
        # 27:3 (both clauses present) -> KJV 27:4 is a fold. Douay 27:4 = KJV 27:5
        # (Moses brought their cause), 27:5 = KJV 27:6, 27:6 = KJV 27:7. Then KJV 27:8
        # SPLITS -> Douay 27:7 ("thou shalt speak these things") + 27:8 ("When a man
        # dieth without a son..."). Identity resumes at Douay 27:9 = KJV 27:9.
        27: [
            (1, 2, 27, 1),
            (3, 3, 27, 3),
            (4, 4, 27, 5),
            (5, 5, 27, 6),
            (6, 6, 27, 7),
            (7, 7, 27, 8),
            (8, 8, 27, 8),
            (9, _HI, 27, 9),
        ],
        # ch29/30 (vows): Douay ch29 ends at v39; KJV 29:40 ("And Moses told the
        # children of Israel according to all that the LORD commanded Moses") opens
        # the Vulgate's ch30 as Douay 30:1 ("And Moses told the children of Israel all
        # that the Lord had commanded him") -- a clean cross-chapter relocation. Then
        # Douay 30:2 ("he said to the princes of the tribes...") = KJV 30:1, and the
        # rest of ch30 runs at a uniform -1 offset (Douay 30:17 = KJV 30:16). This also
        # supplies KJV 29:40, which Douay ch29 itself does not contain.
        30: [(1, 1, 29, 40), (2, _HI, 30, 1)],
    },
    "rev": {
        12: [(1, 17, 12, 1), (18, 18, 13, 1)],  # kept-encoded
        20: [
            (1, 6, 20, 1),
            (7, 7, 20, 8),
            (8, 9, 20, 9),
            (10, _HI, 20, 10),
        ],  # D20:7=K20:8 (K20:7 fold); D20:8+D20:9=K20:9 (concat); D20:10=K20:10
    },
    "sng": {
        1: [(1, _HI, 1, 2)],  # composed
        5: [(1, 16, 5, 1), (17, _HI, 6, 1)],  # composed
        6: [(1, _HI, 6, 2)],  # composed
    },
    "wis": {
        2: [(1, 24, 2, 1), (25, _HI, 2, 24)],  # composed
        5: [(1, 13, 5, 1), (14, _HI, 5, 13)],  # composed
        6: [(1, 1, 6, 1), (2, 22, 6, 1), (23, _HI, 6, 21)],  # composed
        9: [(1, 18, 9, 1), (19, _HI, 9, 18)],  # composed
        # ch17: the Vulgate MERGES KJV 17:9 ("though no terrible thing did fear
        # them... hissing of serpents") + KJV 17:10 ("They died for fear, denying
        # that they saw the air") into one Douay 17:9 (both clauses present). So
        # Douay 17:1-9 = KJV 17:1-9 (KJV 17:10 folded into Douay 17:9), then Douay
        # 17:10 ("wickedness is fearful") = KJV 17:11, offset +1 to Douay 17:20 =
        # KJV 17:21 ("Over them only was spread a heavy night").
        17: [(1, 9, 17, 1), (10, _HI, 17, 11)],
        11: [(1, 5, 11, 1), (6, _HI, 11, 5)],  # composed
        19: [(1, 11, 19, 1), (12, 19, 19, 13), (20, _HI, 19, 22)],  # composed
    },
}

# Books whose Vulgate text is a DIFFERENT RECENSION (not the Greek the KJV Apocrypha
# follows) -> no verse-by-verse KJV correspondence, so OMIT entirely (documented, like
# the LXX deferred aes). Confirmed by content (Douay Tob 1:1 "Tobias of the tribe..."
# vs KJV "The book of the words of Tobit...") + whole-book identity-overlap 0.16-0.24.
# NOTE: ``wis`` is intentionally NOT in this set — the Vulgate Wisdom text matches
# the KJV Apocrypha closely enough for verse-level correspondence; the table maps it.
_VULGATE_OMIT: frozenset[str] = frozenset({"tob", "jdt", "sir"})


# Prayer of Azariah / Song of the Three (paz) from the Vulgate/Douay Daniel ch3
# additions (dan 3:24-90). Per-verse segments in dan-ch3 source coords (src_lo,
# src_hi, paz_ch | None, paz_v_lo): a source verse v in [lo,hi] -> paz (paz_v_lo +
# (v - lo)); paz_ch None = omit. Jerome's Vulgate is a translation of Theodotion,
# the SAME recension as the Swete Greek the LXX path encodes in _PAZ_FROM_DAT3, so
# the BULK reuses that map verbatim: the prayer head dan 3:24-51 -> paz 1:1-28
# (offset -23); dan 3:52 combines KJV paz 1:29+1:30 (1:30 gets no source -> a fold),
# dropping the litany to offset -22; the angels/heavens swap (dan 3:58 angels ->
# paz 1:37, dan 3:59 heavens -> paz 1:36); and the tail dan 3:74-90 -> paz 1:52-68
# (offset -22, monotonic to the end). The clean -23 offset the prior code used was
# WRONG in two ways: (a) it stopped at paz 1:67 (dan 3:90 "O all ye religious, bless
# the Lord the God of gods" is KJV paz 1:68, not 1:67), and (b) it ignored the
# Benedicite reorder entirely. TWO spots diverge from the Swete _PAZ_FROM_DAT3 and
# get a Vulgate-specific tweak (each content-aligned by reading the ENGLISH Douay
# against the ENGLISH KJV, confirmed by the _vg_verify_cross overlap harness):
#   1. dan 3:54/3:55 are SWAPPED vs the Swete/KJV order. Douay 3:54 ("Blessed art
#      thou on the throne of thy kingdom") = KJV paz 1:33; Douay 3:55 ("Blessed art
#      thou, that beholdest the depths, and sittest upon the cherubims") = KJV paz
#      1:32. (The Swete map runs 53-57 as a clean +0 offset; the Vulgate flips 54/55.)
#   2. The cold/frost block dan 3:67-73 is NOT source-empty in the Vulgate (the Swete
#      omits G67/G68) and carries its OWN permutation: Douay 3:67 ("cold and heat") =
#      KJV paz 1:45 ("winter and summer"), 3:68 ("dews and hoar frosts") = 1:46 ("dews
#      and storms of snow"), 3:69 ("frost and cold") = 1:50 ("frost and snow"), 3:70
#      ("ice and snow") = 1:49 ("ice and cold"), 3:71 ("nights and days") = 1:47, 3:72
#      ("light and darkness") = 1:48, 3:73 ("lightnings and clouds") = 1:51. So the
#      Vulgate Benedicite is a complete bijection onto KJV paz 1:38-52 (no folds here),
#      unlike the Swete (which leaves KJV paz 1:46 + 1:49 source-empty).
# Net: every KJV paz 1:1-68 verse receives exactly one Douay/Vulgate verse EXCEPT KJV
# paz 1:30 (folded into 1:29 via the dan 3:52 combine) -- the lone verified fold.
_PAZ_FROM_VULGATE_DAN3: list[_Seg] = [
    (24, 51, 1, 1),  # Prayer of Azariah -- offset -23 (reused from _PAZ_FROM_DAT3)
    (52, 52, 1, 29),  # dan 3:52 = KJV 1:29+1:30 (1:30 unmapped -> fold); offset -> -22
    (53, 53, 1, 31),  # litany head (temple)
    (54, 54, 1, 33),  # "throne of thy kingdom" -- Vulgate-swapped with 1:32
    (55, 55, 1, 32),  # "beholdest the depths / cherubims" -- Vulgate-swapped with 1:33
    (56, 57, 1, 34),  # firmament, all-works
    (58, 58, 1, 37),  # angels -- swapped with heavens (as in Swete)
    (59, 59, 1, 36),  # heavens -- swapped with angels (as in Swete)
    (60, 66, 1, 38),  # waters-above .. fire&heat (as in Swete)
    (67, 67, 1, 45),  # "cold and heat" -> winter and summer (Vulgate has content here)
    (68, 68, 1, 46),  # "dews and hoar frosts" -> dews and storms of snow
    (69, 69, 1, 50),  # "frost and cold" -> frost and snow
    (70, 70, 1, 49),  # "ice and snow" -> ice and cold
    (71, 71, 1, 47),  # nights and days
    (72, 72, 1, 48),  # light and darkness
    (73, 73, 1, 51),  # lightnings and clouds
    (74, 90, 1, 52),  # the earth .. all who worship -- offset -22, monotonic to paz 1:68
]


def _vulgate_cross(code: str, ch: int, vs: int) -> Coord | None:
    """Daniel additions inlined under the Vulgate/Douay 'dan' book relocate to
    separate project books (content-verified vs the real Douay text, NOT memory --
    see the _vg_verify_cross overlap harness):
      - DAN 3:24-90 -> paz (Prayer of Azariah / Song of the Three) via the reordered
        ``_PAZ_FROM_VULGATE_DAN3`` segments (Theodotion-recension Benedicite reorder;
        a plain -23 offset is WRONG -- it stops at paz 1:67 and ignores the reorder).
      - DAN 13      -> sus 1 (Susanna) for vs 1-64 (clean identity); the Vulgate's
        trailing verse Douay dan 13:65 "And king Astyages was gathered to his fathers" is
        the verse the KJV places at bel 1:1, so it is routed there (NOT dropped).
      - DAN 14      -> bel 1 at a uniform +1 offset (Douay dan 14:1 "And Daniel was the
        king's guest" = KJV bel 1:2; bel 1:1 'Astyages' comes from dan 13:65 above). The
        Vulgate-only closing decree (Douay dan 14:42) maps past bel 1:42 -> drops.
    The KJV-canonical Daniel verses (3:1-23, 3:91+, ch4-12) are handled by
    _VULGATE_SEGMENTS['dan'] / identity, NOT here."""
    if code != "dan":
        return None
    if ch == 3 and 24 <= vs <= 90:
        for lo, hi, paz_ch, paz_v_lo in _PAZ_FROM_VULGATE_DAN3:
            if lo <= vs <= hi:
                return None if paz_ch is None else ("paz", paz_ch, paz_v_lo + (vs - lo))
        return None
    if ch == 13:
        # dan 13:65 = the Astyages verse the KJV places at bel 1:1 (sus has only 64 v).
        return ("bel", 1, 1) if vs == 65 else ("sus", 1, vs)
    if ch == 14:
        return ("bel", 1, vs + 1)
    return None


def vulgate_to_kjv(code: str, ch: int, vs: int) -> Coord | None:
    """Map a Clementine-Vulgate / Douay coordinate (project book code) to canonical
    KJV. ``None`` to omit (no canonical slot / out-of-extent). Daniel additions ->
    paz/sus/bel via ``_vulgate_cross``; Psalms reuse the LXX ``_psalm_map`` (+ the
    ``_VULGATE_PSALM_FIXES`` Vulgate-only overrides); tob/jdt/sir omitted (divergent
    recension); every other divergence is in the content-verified ``_VULGATE_SEGMENTS``
    table (generated from the Copenhagen vul.json, then gate-verified vs the real Douay
    text). Shared by douay + vulgate (the 14 count-divergent chapters use concat-tail
    segments the shorter source never triggers)."""
    cross = _vulgate_cross(code, ch, vs)
    if cross is not None:
        return cross if coord_in_canonical_extent(*cross) else None
    if code in _VULGATE_OMIT:
        return None  # different recension — no KJV-skeleton correspondence (documented)
    if code == "psa":
        mapped = _VULGATE_PSALM_FIXES.get((ch, vs)) or _psalm_map().get((ch, vs))
    elif code in _VULGATE_SEGMENTS:
        mapped = _apply_segments(code, _VULGATE_SEGMENTS[code], ch, vs)
    else:
        mapped = (ch, vs)  # identity
    if mapped is None:
        return None
    kch, kvs = mapped
    if not coord_in_canonical_extent(code, kch, kvs):
        return None
    return (code, kch, kvs)

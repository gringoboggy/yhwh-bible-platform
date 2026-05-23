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
# Both are 74-book Catholic, Vulgate-numbered; ONE shared map serves both (the
# ~14 chapters where Douay's verse split differs from the Latin Vulgate are
# handled per-source by the drivers, not here). Input ``code`` is already a
# project book code (this runs after extract_translation's eBible->project map).
#
# Derived by content-aligning the ENGLISH Douay against the ENGLISH KJV (word
# overlap), NOT identity-guessed and NOT from memory:
#   - Psalms: the Septuagint/Vulgate numbering == the LXX scheme, so reuse the
#     existing ``_psalm_map`` (content-verified vs the Douay); a few psalms whose
#     Latin verse-division differs from the Greek get a per-psalm patch below.
#   - Daniel/Esther additions, Sirach/Tobit/Judith recension splits, and the
#     scattered single-verse offsets get per-book SEGMENT tables (added as each
#     is content-verified). Everything else is identity.
# ===========================================================================

# Per-(code, vulgate_ch, vulgate_vs) -> (kjv_ch, kjv_vs) overrides where the Latin
# verse-division diverges from both identity AND the reused LXX psalm map. Filled
# as content-alignment verifies each; empty entries mean "still identity/psalm-map".
_VULGATE_PSALM_FIXES: dict[tuple[int, int], tuple[int, int]] = {}
_VULGATE_SEGMENTS: dict[str, dict[int, list[_Seg]]] = {}
_VULGATE_CROSS: dict[str, object] = {}  # code -> callable(ch,vs)->Coord|None for additions


def vulgate_to_kjv(code: str, ch: int, vs: int) -> Coord | None:
    """Map a Clementine-Vulgate / Douay coordinate (project book code) to canonical
    KJV. ``None`` to omit (no canonical slot / out-of-extent). WORK IN PROGRESS —
    Psalms reuse the LXX map; other divergent books are identity until their
    content-verified segment tables land below."""
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

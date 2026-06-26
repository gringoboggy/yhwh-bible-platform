"""Per-chapter verse-count tables for the six Tewahedo-distinctive books that
have NO KJV/LXX skeleton but DO have an authoritative hand-typed enumeration.

Dependency-free leaf: plain ``{chapter: verse_count}`` dict literals, no imports,
no OCR/PDF deps. This is the canonical *home* for these tables — they were
relocated here verbatim from ``scripts/extract_parallel_pdf.py`` (R14 audit,
data-validity fix) so that the dependency-light core leaf
``scripts/core/canonical_verse_counts.py`` can consult them as a per-chapter
extent ceiling WITHOUT importing the 3,700-line ``extract_parallel_pdf`` OCR CLI
(top-level ``yaml``, lazy ``fitz``/Tesseract). ``extract_parallel_pdf.py``
re-imports them from here, so its ``renumber_against_floor`` / floor-dict
behavior is byte-identical.

Each dict is ``{chapter: verse_count}``. For a 1-start contiguous book the count
IS the highest verse number, so the count doubles as the per-chapter verse
CEILING used by ``coord_in_canonical_extent``. The counts are canonical-CEILING
floors per the τ.6.x.0b honesty contract (the τ.6.x.3 batched audit reconciles
the exact Ethiopic recension); the six books' max chapter keys equal their
``content/books.yaml`` ``ch_count`` (mq1=36, mq2=21, mq3=10, 4ba=9, jub=50,
1en=108).

The remaining two Tewahedo-distinctive books (``1cl``, ``2en``) have no verse
table at all — ``coord_in_canonical_extent`` enforces only their ``books.yaml``
``ch_count`` chapter ceiling for those.
"""

from __future__ import annotations

# 1/2/3 Mäqabyan (mq1/mq2/mq3). ch_counts match content/books.yaml (mq1:36 /
# mq2:21 / mq3:10) + build_meqabyan_revision.py BOOKS. Mäqabyan output is
# `ocr-tier3` and EXPLICITLY δ.1.x-REPLACEABLE — the OCR witness the δ.1.x
# page-image-tier1 divergence apparatus diverges FROM, NOT the long-term
# authoritative text. Fourteenth/fifteenth/sixteenth renumber-floors.
MQ1_VERSE_COUNTS = {
    1: 14,
    2: 28,
    3: 38,
    4: 5,
    5: 14,
    6: 23,
    7: 1,
    8: 22,
    9: 3,
    10: 5,
    11: 3,
    12: 1,
    13: 20,
    14: 15,
    15: 8,
    16: 1,
    17: 14,
    18: 2,
    19: 1,
    20: 14,
    21: 14,
    22: 14,
    23: 14,
    24: 14,
    25: 9,
    26: 14,
    27: 14,
    28: 38,
    29: 5,
    30: 21,
    31: 14,
    32: 14,
    33: 8,
    34: 14,
    35: 14,
    36: 49,
}
# Total 1 Mäqabyan verses = 502 (36 ch; Maqabis-of-Benjamin
# martyrology vs Ṣiruṣaydan).

MQ2_VERSE_COUNTS = {
    1: 14,
    2: 9,
    3: 11,
    4: 17,
    5: 14,
    6: 8,
    7: 9,
    8: 14,
    9: 11,
    10: 14,
    11: 9,
    12: 18,
    13: 7,
    14: 29,
    15: 11,
    16: 8,
    17: 5,
    18: 14,
    19: 10,
    20: 13,
    21: 11,
}
# Total 2 Mäqabyan verses = 256 (21 ch; Maqabis-of-Moab conversion
# + sons' martyrdom + Ṣiruṣaydan's death).

MQ3_VERSE_COUNTS = {
    1: 28,
    2: 24,
    3: 15,
    4: 34,
    5: 14,
    6: 14,
    7: 14,
    8: 10,
    9: 5,
    10: 30,
}
# Total 3 Mäqabyan verses = 188 (10 ch; homiletic + angelological
# dialogue + Satan-refused-Adam tradition + resurrection-doctrine).
# Trilogy total = 502 + 256 + 188 = 946 verses / 67 chapters.


# 4 Baruch / Paraleipomena Jeremiou (4ba). content/books.yaml fixes `4ba` at
# ch_count: 9. Kraft-Purintun 1972 9-chapter division, cross-checked against
# Harris 1889. The Ethiopic recension carries an extended Christian conclusion
# in ch 9; per the τ.6.x.0b honesty contract the floor is the canonical
# CEILING (τ.6.x.3 reconciles the Ethiopic recension).
FOUR_BARUCH_VERSE_COUNTS = {
    1: 11,
    2: 10,
    3: 22,
    4: 11,
    5: 34,
    6: 25,
    7: 37,
    8: 9,
    9: 32,
}
# Total 4 Baruch verses = 191 (9 ch; Kraft-Purintun 1972; the
# Ethiopic ch-9 Christian expansion is reconciled at τ.6.x.3).


# The Book of Jubilees / Mäṣḥafä Kufāle (jub). content/books.yaml fixes `jub`
# at ch_count: 50. A uniquely-Tewahedo-canonical OT text. Verse counts use the
# standard R.H. Charles 1913 / VanderKam 1989 (CSCO 510-511) Jubilees
# enumeration (50 ch / ~1306 v). Per the τ.6.x.0b honesty contract the floor is
# the canonical CEILING; the γ.4.5 content/notes/jub.py maxima never exceed it
# and match exactly at the distinctive chapters (ch6=38, ch7=39, ch9=15).
JUBILEES_VERSE_COUNTS = {
    1: 29,
    2: 33,
    3: 35,
    4: 33,
    5: 32,
    6: 38,
    7: 39,
    8: 30,
    9: 15,
    10: 35,
    11: 24,
    12: 31,
    13: 29,
    14: 24,
    15: 34,
    16: 31,
    17: 18,
    18: 19,
    19: 31,
    20: 13,
    21: 26,
    22: 30,
    23: 32,
    24: 33,
    25: 23,
    26: 35,
    27: 27,
    28: 30,
    29: 20,
    30: 26,
    31: 32,
    32: 34,
    33: 23,
    34: 21,
    35: 27,
    36: 24,
    37: 25,
    38: 24,
    39: 18,
    40: 13,
    41: 28,
    42: 25,
    43: 24,
    44: 34,
    45: 16,
    46: 16,
    47: 12,
    48: 19,
    49: 23,
    50: 13,
}
# Total Jubilees verses = 1306 (50 ch; R.H. Charles 1913 /
# VanderKam 1989 CSCO enumeration; canonical CEILING — τ.6.x.3
# reconciles the exact Ethiopic Mäṣḥafä Kufāle recension).


# The Book of Enoch / Mäṣḥafä Hēnok / 1 Enoch (1en). content/books.yaml fixes
# `1en` at ch_count: 108. Uniquely-Tewahedo-canonical. Verse counts use the
# standard R.H. Charles 1912 "The Book of Enoch" enumeration. Five sections:
# Watchers (1-36), Parables (37-71), Astronomical (72-82), Dream-Visions
# (83-90), Epistle (91-108). Per the τ.6.x.0b honesty contract the floor is the
# canonical CEILING; all 108 chapters were hard-validated ≥ the γ.4.4
# content/notes/1en.py per-chapter maxima (exact matches at 14=25, 60=25,
# 90=42).
ONE_ENOCH_VERSE_COUNTS = {
    1: 9,
    2: 3,
    3: 1,
    4: 1,
    5: 9,
    6: 8,
    7: 6,
    8: 4,
    9: 11,
    10: 22,
    11: 2,
    12: 6,
    13: 10,
    14: 25,
    15: 12,
    16: 4,
    17: 8,
    18: 16,
    19: 3,
    20: 8,
    21: 10,
    22: 14,
    23: 4,
    24: 6,
    25: 7,
    26: 6,
    27: 5,
    28: 3,
    29: 2,
    30: 3,
    31: 3,
    32: 6,
    33: 4,
    34: 3,
    35: 1,
    36: 4,
    37: 5,
    38: 6,
    39: 14,
    40: 10,
    41: 9,
    42: 3,
    43: 4,
    44: 1,
    45: 6,
    46: 8,
    47: 4,
    48: 10,
    49: 4,
    50: 5,
    51: 5,
    52: 9,
    53: 7,
    54: 10,
    55: 4,
    56: 8,
    57: 3,
    58: 6,
    59: 3,
    60: 25,
    61: 13,
    62: 16,
    63: 12,
    64: 2,
    65: 12,
    66: 3,
    67: 13,
    68: 5,
    69: 29,
    70: 4,
    71: 17,
    72: 37,
    73: 8,
    74: 17,
    75: 9,
    76: 14,
    77: 9,
    78: 17,
    79: 6,
    80: 8,
    81: 10,
    82: 20,
    83: 11,
    84: 6,
    85: 10,
    86: 6,
    87: 4,
    88: 3,
    89: 77,
    90: 42,
    91: 19,
    92: 5,
    93: 14,
    94: 11,
    95: 7,
    96: 8,
    97: 10,
    98: 16,
    99: 16,
    100: 13,
    101: 9,
    102: 11,
    103: 15,
    104: 13,
    105: 2,
    106: 19,
    107: 3,
    108: 15,
}
# Total 1 Enoch verses = 1064 (108 ch; R.H. Charles 1912
# enumeration; canonical CEILING ≥ the γ.4.4 notes/1en.py maxima
# at all 108 ch — τ.6.x.3 reconciles the exact Ethiopic Mäṣḥafä
# Hēnok recension).

"""Round-14 data-validity fix: the canonical-extent guard now validates the 8
Tewahedo-distinctive books instead of being a silent no-op.

Before the fix, ``coord_in_canonical_extent``/``html_chapter_count`` kept ANY
coordinate (and returned chapter-count 0) for the 8 books in
``TEWAHEDO_DISTINCTIVE_NO_KJV`` because they have no KJV/LXX skeleton — so an
impossible OCR/parse coordinate (e.g. ``1en`` 999:99) reached the promote
boundary undetected. Six of the 8 have an authoritative hand-typed verse table
(now in ``scripts/core/distinctive_verse_counts.py``); the other two (``1cl``,
``2en``) have a ``books.yaml`` ``ch_count``. The guard consults these.

Two assertions:
  (a) impossible distinctive coords now return False;
  (b) ★the byte-identity safety net★ — every existing on-disk note coordinate for
      the 8 distinctive books STILL validates True under the new guard, proving
      the ceiling rejects no real data (so the Ethiopian build stays
      byte-identical and the 9 KJV editions are unaffected).
"""

from __future__ import annotations

from pathlib import Path

from scripts.core.canonical_verse_counts import (
    TEWAHEDO_DISTINCTIVE_NO_KJV,
    coord_in_canonical_extent,
    html_chapter_count,
)
from scripts.core.notes_io import load_notes

REPO = Path(__file__).resolve().parents[1]
NOTES_DIR = REPO / "content" / "notes"

# books.yaml ch_count for each distinctive book (= max chapter of its verse
# table for the six; the chapter ceiling for 1cl/2en).
_CH_COUNT = {
    "mq1": 36,
    "mq2": 21,
    "mq3": 10,
    "4ba": 9,
    "jub": 50,
    "1en": 108,
    "1cl": 65,
    "2en": 68,
}


def _iter_on_disk_coords():
    """Yield ``(book, chapter, verse)`` for every note in every distinctive book."""
    for book in TEWAHEDO_DISTINCTIVE_NO_KJV:
        p = NOTES_DIR / f"{book}.py"
        if not p.exists():
            continue
        for tup in load_notes(p) or []:
            yield book, tup[0], tup[1]


class TestImpossibleCoordsRejected:
    """(a) The guard now rejects genuinely impossible distinctive coordinates."""

    def test_named_impossible_coords(self):
        # the three coords called out in the round-14 finding
        assert coord_in_canonical_extent("1en", 999, 99) is False
        assert coord_in_canonical_extent("jub", 500, 1) is False
        assert coord_in_canonical_extent("mq1", 200, 1) is False

    def test_verse_over_chapter_ceiling(self):
        # 1en ch1 has 9 verses; mq1 ch36 has 49; jub ch50 has 13
        assert coord_in_canonical_extent("1en", 1, 10) is False
        assert coord_in_canonical_extent("mq1", 36, 50) is False
        assert coord_in_canonical_extent("jub", 50, 14) is False

    def test_chapter_over_book_ceiling(self):
        # 4ba has 9 chapters; mq3 has 10
        assert coord_in_canonical_extent("4ba", 10, 1) is False
        assert coord_in_canonical_extent("mq3", 11, 1) is False

    def test_no_verse_table_books_use_ch_count(self):
        # 1cl (65 ch) / 2en (68 ch) — chapter ceiling only
        assert coord_in_canonical_extent("1cl", 300, 1) is False
        assert coord_in_canonical_extent("2en", 999, 1) is False
        assert coord_in_canonical_extent("1cl", 65, 1) is True
        assert coord_in_canonical_extent("2en", 68, 1) is True

    def test_negative_verse_rejected(self):
        assert coord_in_canonical_extent("1en", 1, -1) is False


class TestValidDistinctiveCoordsKept:
    """In-extent distinctive coordinates (incl. the verse-0 chapter-level note
    convention) still validate True."""

    def test_real_in_extent_coords(self):
        for b, c, v in [
            ("1en", 1, 9),
            ("1en", 108, 15),
            ("1en", 89, 77),  # the longest chapter
            ("jub", 6, 38),
            ("jub", 7, 39),
            ("mq1", 36, 49),
            ("4ba", 9, 32),
        ]:
            assert coord_in_canonical_extent(b, c, v) is True, (b, c, v)

    def test_chapter_level_verse_zero_kept(self):
        # verse 0 is the project's chapter-level note convention (the two real
        # on-disk 1en 91:0 / 94:0 chapter-intro comm notes must validate).
        assert coord_in_canonical_extent("1en", 91, 0) is True
        assert coord_in_canonical_extent("1en", 94, 0) is True


class TestHtmlChapterCount:
    """html_chapter_count now returns the distinctive ceiling, not 0."""

    def test_six_verse_table_books(self):
        for b in ("mq1", "mq2", "mq3", "4ba", "jub", "1en"):
            assert html_chapter_count(b) == _CH_COUNT[b], b

    def test_two_ch_count_only_books(self):
        assert html_chapter_count("1cl") == 65
        assert html_chapter_count("2en") == 68

    def test_unknown_code_still_zero(self):
        assert html_chapter_count("zzz") == 0


class TestUnknownCodesStillKept:
    """Keep-all is reserved for genuinely unknown/test book codes."""

    def test_unknown_book_kept(self):
        assert coord_in_canonical_extent("zz", 99, 99) is True
        assert coord_in_canonical_extent("zzz", 1, 1) is True


class TestByteIdentitySafetyNet:
    """(b) The load-bearing proof: every existing on-disk distinctive note coord
    still validates True, so the new ceiling drops NO real data."""

    def test_every_on_disk_distinctive_coord_validates(self):
        coords = list(_iter_on_disk_coords())
        assert coords, "expected on-disk distinctive note coords to scan"
        bad = [(b, c, v) for (b, c, v) in coords if not coord_in_canonical_extent(b, c, v)]
        assert not bad, (
            f"{len(bad)} on-disk distinctive coord(s) newly rejected by the guard "
            f"(would change shipped output): {bad[:20]}"
        )

    def test_scanned_a_meaningful_corpus(self):
        # guards against a silently-empty scan masking a regression
        assert len(list(_iter_on_disk_coords())) >= 800

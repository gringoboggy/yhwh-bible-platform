"""Phase-3 render scaffolding: pin the Samuel/Kings verse-count floors
against the KJV skeleton.

These floors live in ``scripts/extract_parallel_pdf.py`` (the conventional
home for VERSE_COUNTS data — Genesis through Psalms + Apocrypha all live
there). They were added at audit U-belt 2026-05-20 as Phase-3 scaffolding
for the τ.6.x.4 manuscript-collation track. The test here pins them
against the KJV skeleton (``scripts.core.manuscript_collation.load_kjv_skeleton``)
so accidental drift between the floor data and the skeleton is caught at
commit time.

Why this pin matters: the manuscript marathon collates chapters that ARE
spine-aligned via ``load_kjv_skeleton`` — they cannot legally exceed the
KJV count (overflow is a token-conservation failure). The floors here ARE
the ceiling. If a chapter's floor drifts above the skeleton, the Phase-3
render's ``renumber_against_floor`` would over-promise on chapter shape.
"""

import importlib

mc = importlib.import_module("scripts.core.manuscript_collation")
epp = importlib.import_module("scripts.extract_parallel_pdf")


class TestVerseCountFloorsMatchKJVSkeleton:
    """Per-chapter ``floor[ch] == len(load_kjv_skeleton(book, ch))`` for
    every (book, chapter) in Samuel + Kings. Drift is silent today; this
    pin makes it loud."""

    def test_first_samuel_floor_matches_skeleton(self):
        for ch, count in epp.FIRST_SAMUEL_VERSE_COUNTS.items():
            skel = mc.load_kjv_skeleton("1sa", ch)
            assert count == len(skel), f"1sa ch{ch}: floor={count} vs skeleton={len(skel)}"

    def test_second_samuel_floor_matches_skeleton(self):
        for ch, count in epp.SECOND_SAMUEL_VERSE_COUNTS.items():
            skel = mc.load_kjv_skeleton("2sa", ch)
            assert count == len(skel), f"2sa ch{ch}: floor={count} vs skeleton={len(skel)}"

    def test_first_kings_floor_matches_skeleton(self):
        for ch, count in epp.FIRST_KINGS_VERSE_COUNTS.items():
            skel = mc.load_kjv_skeleton("1ki", ch)
            assert count == len(skel), f"1ki ch{ch}: floor={count} vs skeleton={len(skel)}"

    def test_second_kings_floor_matches_skeleton(self):
        for ch, count in epp.SECOND_KINGS_VERSE_COUNTS.items():
            skel = mc.load_kjv_skeleton("2ki", ch)
            assert count == len(skel), f"2ki ch{ch}: floor={count} vs skeleton={len(skel)}"


class TestVerseCountFloorsCoverAllChapters:
    """No silent gaps: the floor must have an entry for every chapter
    of the canonical book (not just the chapters that already shipped)."""

    def test_first_samuel_31_chapters(self):
        assert set(epp.FIRST_SAMUEL_VERSE_COUNTS.keys()) == set(range(1, 32))

    def test_second_samuel_24_chapters(self):
        assert set(epp.SECOND_SAMUEL_VERSE_COUNTS.keys()) == set(range(1, 25))

    def test_first_kings_22_chapters(self):
        assert set(epp.FIRST_KINGS_VERSE_COUNTS.keys()) == set(range(1, 23))

    def test_second_kings_25_chapters(self):
        assert set(epp.SECOND_KINGS_VERSE_COUNTS.keys()) == set(range(1, 26))


class TestVerseCountTotals:
    """Canonical KJV totals — the ceiling for Phase-3 render scope.
    Total Samuel + Kings = 3040 verses across 102 chapters."""

    def test_first_samuel_total_810(self):
        assert sum(epp.FIRST_SAMUEL_VERSE_COUNTS.values()) == 810

    def test_second_samuel_total_695(self):
        assert sum(epp.SECOND_SAMUEL_VERSE_COUNTS.values()) == 695

    def test_first_kings_total_816(self):
        assert sum(epp.FIRST_KINGS_VERSE_COUNTS.values()) == 816

    def test_second_kings_total_719(self):
        assert sum(epp.SECOND_KINGS_VERSE_COUNTS.values()) == 719

    def test_combined_samuel_kings_total_3040(self):
        total = (
            sum(epp.FIRST_SAMUEL_VERSE_COUNTS.values())
            + sum(epp.SECOND_SAMUEL_VERSE_COUNTS.values())
            + sum(epp.FIRST_KINGS_VERSE_COUNTS.values())
            + sum(epp.SECOND_KINGS_VERSE_COUNTS.values())
        )
        assert total == 3040

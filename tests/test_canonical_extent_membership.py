"""coord_in_canonical_extent tests true verse-number MEMBERSHIP, not 1..count.

Regression pin for the round-13 data-validity finding DV2: the extent guard used
``1 <= verse <= shape[chapter]``, which is wrong for a non-1-start chapter. The one
such chapter in the whole KJV skeleton is ``aes`` (Additions to Esther) ch10, whose
verses are numbered **4..13** (they continue canonical Esther 10:3). The count model
wrongly REJECTED aes 10:11-13 (real verses) and wrongly ACCEPTED aes 10:1-3 (which do
not exist). The membership model fixes both, and is byte-identical for every contiguous
1-start chapter (verified: 1361 of 1362 skeleton chapters are exactly {1..count}).
"""

from __future__ import annotations

import pytest

from scripts.core.canonical_verse_counts import (
    CANONICAL_BOOKS,
    canonical_book_shape,
    coord_in_canonical_extent,
)
from scripts.core.manuscript_collation import load_kjv_skeleton


class TestNonStartChapterMembership:
    def test_aes_ch10_real_verses_accepted(self):
        # aes ch10 is numbered 4..13 — all real, must be in extent
        for v in (4, 5, 11, 12, 13):
            assert coord_in_canonical_extent("aes", 10, v) is True, v

    def test_aes_ch10_impossible_verses_rejected(self):
        # below the real start (1..3) and past the real end (14+) do not exist
        for v in (1, 2, 3, 14, 99):
            assert coord_in_canonical_extent("aes", 10, v) is False, v


class TestContiguousBooksUnchanged:
    def test_one_start_books_membership_equals_range(self):
        assert coord_in_canonical_extent("gen", 1, 31) is True
        assert coord_in_canonical_extent("gen", 1, 32) is False
        assert coord_in_canonical_extent("gen", 50, 26) is True
        assert coord_in_canonical_extent("psa", 119, 176) is True
        assert coord_in_canonical_extent("psa", 117, 2) is True
        assert coord_in_canonical_extent("psa", 117, 3) is False
        assert coord_in_canonical_extent("gen", 87, 1) is False  # chapter-missing

    def test_distinctive_books_now_validated(self):
        # R14 data-validity fix: Tewahedo distinctives no longer no-op. They are
        # validated against their hand-typed verse tables (six books) / books.yaml
        # ch_count (1cl, 2en), so an impossible verse is now REJECTED rather than
        # kept. Full coverage lives in tests/test_canonical_extent_distinctive.py.
        assert coord_in_canonical_extent("1en", 71, 99) is False  # 1en 71 has 17 verses
        assert coord_in_canonical_extent("jub", 50, 99) is False  # jub 50 has 13 verses
        # real in-extent coords still validate
        assert coord_in_canonical_extent("1en", 71, 17) is True
        assert coord_in_canonical_extent("jub", 50, 13) is True

    @pytest.mark.slow
    def test_byte_stable_vs_count_model_across_whole_skeleton(self):
        # The membership model must equal the old 1..count model for EVERY coordinate
        # of EVERY contiguous chapter — i.e. everywhere except aes 10.
        for book in CANONICAL_BOOKS:
            shape = canonical_book_shape(book)
            for ch, count in shape.items():
                verses = {v for (_c, v, *_t) in load_kjv_skeleton(book, ch)}
                if verses == set(range(1, count + 1)):
                    # probe one in-range and one out-of-range coord
                    assert coord_in_canonical_extent(book, ch, count) is True, (book, ch, count)
                    assert coord_in_canonical_extent(book, ch, count + 1) is False, (book, ch, count)
                else:
                    # the sole non-1-start chapter
                    assert (book, ch) == ("aes", 10), (book, ch, sorted(verses))


class TestShapeContractPreserved:
    def test_canonical_book_shape_still_returns_counts(self):
        sh = canonical_book_shape("gen")
        assert sh[1] == 31 and sh[50] == 26
        assert canonical_book_shape("aes")[10] == 10  # count stays 10 (verses 4..13)

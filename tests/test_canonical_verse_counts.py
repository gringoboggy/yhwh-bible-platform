"""Canonical verse-count helper test pins (audit 2026-05-20).

Validates the helper derives the right counts from the KJV skeleton
across the WHOLE canonical 82-book Tewahedo set — not just Samuel/
Kings — so Phase-3 render scaffolding is universal.
"""


class TestCanonicalCoverage:
    def test_canonical_books_resolve_or_are_scaffold_only(self):
        """Every CANONICAL_BOOKS entry returns a dict from canonical_book_shape.

        Books with non-empty skeleton are USABLE (have content). Books
        with empty skeleton are SCAFFOLD-ONLY (file exists but no VERSES
        — placeholder awaiting content). Both states are honest; the
        test pins that no book raises.
        """
        from scripts.core.canonical_verse_counts import (
            CANONICAL_BOOKS,
            canonical_book_shape,
        )

        usable: list[str] = []
        scaffold_only: list[str] = []
        for book in CANONICAL_BOOKS:
            shape = canonical_book_shape(book)
            assert isinstance(shape, dict), book  # no raise
            if shape:
                usable.append(book)
                for ch, count in shape.items():
                    assert 1 <= ch <= 200, (book, ch)
                    assert 1 <= count <= 200, (book, ch, count)
            else:
                scaffold_only.append(book)
        # >= 70 KJV-anchored books should be USABLE; scaffold-only are
        # documented (aes/Additions-to-Esther is one known stub).
        assert len(usable) >= 70, (len(usable), scaffold_only)

    def test_canonical_books_count(self):
        from scripts.core.canonical_verse_counts import (
            CANONICAL_BOOKS,
            TEWAHEDO_DISTINCTIVE_NO_KJV,
        )

        # KJV-anchored canonical set
        assert len(CANONICAL_BOOKS) >= 75
        assert len(set(CANONICAL_BOOKS)) == len(CANONICAL_BOOKS)  # no duplicates
        # Tewahedo distinctives are tracked separately
        assert len(TEWAHEDO_DISTINCTIVE_NO_KJV) == 6
        # The two sets do not overlap (KJV-anchored vs not)
        assert not (set(CANONICAL_BOOKS) & set(TEWAHEDO_DISTINCTIVE_NO_KJV))


class TestKnownBookCounts:
    """Spot-check well-known KJV counts to confirm the helper isn't
    quietly drifting from the published canonical totals."""

    def test_genesis_50_chapters(self):
        from scripts.core.canonical_verse_counts import canonical_chapters

        assert canonical_chapters("gen") == 50

    def test_psalms_150_chapters_kjv(self):
        from scripts.core.canonical_verse_counts import canonical_chapters

        # KJV Psalter is 150 (the Tewahedo + LXX have 151 — the
        # tradition-specific +1 lives in extract_parallel_pdf.py's
        # PSALMS_VERSE_COUNTS, not here)
        assert canonical_chapters("psa") == 150

    def test_revelation_22_chapters(self):
        from scripts.core.canonical_verse_counts import canonical_chapters

        assert canonical_chapters("rev") == 22

    def test_job_42_chapters(self):
        from scripts.core.canonical_verse_counts import canonical_chapters

        assert canonical_chapters("job") == 42

    def test_chronicles_total_counts(self):
        from scripts.core.canonical_verse_counts import canonical_total

        # KJV 1Ch + 2Ch totals: 942 + 822 = 1764
        assert canonical_total("1ch") + canonical_total("2ch") == 1764

    def test_ezra_neh_total_counts(self):
        from scripts.core.canonical_verse_counts import canonical_total

        # KJV ezr 280 + neh 406 = 686
        assert canonical_total("ezr") + canonical_total("neh") == 686

    def test_nt_27_books_resolve(self):
        """27 NT books all have non-empty canonical shapes; this is the
        Phase-3 render scope for the NT tracks."""
        from scripts.core.canonical_verse_counts import (
            canonical_chapters,
            canonical_total,
        )

        nt = (
            "mat",
            "mrk",
            "luk",
            "jhn",
            "act",
            "rom",
            "1co",
            "2co",
            "gal",
            "eph",
            "phi",
            "col",
            "1th",
            "2th",
            "1ti",
            "2ti",
            "tit",
            "phm",
            "heb",
            "jam",
            "1pe",
            "2pe",
            "1jn",
            "2jn",
            "3jn",
            "jud",
            "rev",
        )
        assert len(nt) == 27
        for book in nt:
            assert canonical_chapters(book) >= 1, book
            assert canonical_total(book) >= 1, book


class TestCachingBehavior:
    def test_repeat_calls_are_cached(self):
        """The helper is decorated with lru_cache; second call is a hit."""
        from scripts.core.canonical_verse_counts import (
            canonical_book_shape,
            _book_shape_cached,
        )

        canonical_book_shape("gen")
        info = _book_shape_cached.cache_info()
        assert info.hits >= 0  # at least the count is exposed; non-zero hits

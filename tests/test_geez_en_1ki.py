"""Minimal pins for geez-tewahedo-en 1 Kings chapters 1-10."""

from scripts.core import translations as tx


class TestGeezEn1Ki:
    def test_book_verse_count_ch1_through_ch10(self):
        assert tx.book_verse_count("geez-tewahedo-en", "1ki") >= 308

    def test_ch7_v1_mentions_solomon_and_temple(self):
        v = tx.get_verse("geez-tewahedo-en", "1ki", 7, 1)
        assert v
        lower = v.lower()
        assert "solomon" in lower
        assert "house" in lower or "temple" in lower

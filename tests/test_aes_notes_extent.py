"""aes Additions-to-Esther notes must stay within canonical ch10 extent (10 v)."""

from __future__ import annotations

from pathlib import Path

from scripts.core.canonical_verse_counts import coord_in_canonical_extent
from scripts.core import notes_io

REPO = Path(__file__).resolve().parent.parent


class TestAesNotesExtent:
    def test_no_ch10_verse_beyond_canonical_ceiling(self):
        notes = notes_io.load_notes(REPO / "content/notes/aes.py")
        bad = [(ch, v) for ch, v, *_ in notes if not coord_in_canonical_extent("aes", ch, v)]
        assert bad == [], f"out-of-extent aes notes: {bad}"

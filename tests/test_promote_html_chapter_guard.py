"""Tests for the base-HTML chapter-extent guard (mint-8 finding #14).

The guard rejects, at promote time, any note whose chapter exceeds the
number of chapters the base HTML renders for a book — such a note is
uninjectable (no chapter anchor to attach to). This is the FUTURE-facing
prevention added alongside the parked aes ch11-16 residual; these tests
exercise the guard directly without reusing fixtures from other files.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import promote  # noqa: E402
from scripts.core.canonical_verse_counts import (  # noqa: E402
    canonical_chapters,
    html_chapter_count,
)

# A minimal but valid <book>.py NOTES module (mirrors content/notes/*.py).
_EMPTY_BOOK = "NOTES = [\n]\n"


def _write_book(notes_dir: Path, book: str) -> Path:
    notes_dir.mkdir(parents=True, exist_ok=True)
    path = notes_dir / f"{book}.py"
    path.write_text(_EMPTY_BOOK, encoding="utf-8")
    return path


def test_html_chapter_count_matches_books_yaml_for_gen() -> None:
    """gen renders all 50 of its (KJV-skeleton) chapters in the base HTML."""
    assert html_chapter_count("gen") == 50
    # The helper currently mirrors the canonical/skeleton chapter count.
    assert html_chapter_count("gen") == canonical_chapters("gen")


def test_promote_candidate_rejects_chapter_above_html_extent(tmp_path, monkeypatch) -> None:
    """A note whose chapter is above the base-HTML extent is rejected and
    nothing is written to the book file."""
    notes_dir = tmp_path / "notes"
    # Obadiah (oba) is a single-chapter book → chapter 2 is above extent.
    assert html_chapter_count("oba") == 1
    book_path = _write_book(notes_dir, "oba")
    before = book_path.read_text(encoding="utf-8")
    monkeypatch.setattr(promote, "NOTES_DIR", notes_dir)

    candidate = {
        "id": "oba-2-1-001",
        "chapter": 2,
        "verse": 1,
        "kind": "note",
        "draft_body": "should not land",
        "draft_title": "X",
        "draft_label": "X",
        "anchor": "",
    }
    ok, suffix = promote.promote_candidate("oba", candidate)

    assert ok is False
    assert suffix == ""
    # Nothing written: the book file is byte-for-byte unchanged.
    assert book_path.read_text(encoding="utf-8") == before


def test_promote_candidate_in_extent_not_rejected_by_this_guard(tmp_path, monkeypatch) -> None:
    """An in-extent chapter must NOT be rejected by the html_chapter_count
    guard — it should be accepted (and written) on this clean book file."""
    notes_dir = tmp_path / "notes"
    book_path = _write_book(notes_dir, "gen")
    monkeypatch.setattr(promote, "NOTES_DIR", notes_dir)

    candidate = {
        "id": "gen-1-1-001",
        "chapter": 1,  # well within gen's 50-chapter extent
        "verse": 1,
        "kind": "note",
        "draft_body": "valid in-extent note body",
        "draft_title": "Note",
        "draft_label": "Note",
        "anchor": "",
    }
    ok, _suffix = promote.promote_candidate("gen", candidate)

    # The html_chapter_count guard must not be the thing that blocks this.
    assert ok is True
    assert "valid in-extent note body" in book_path.read_text(encoding="utf-8")


def test_batch_insert_drops_above_extent_chapter(tmp_path) -> None:
    """batch_insert_notes drops a note whose chapter exceeds the base-HTML
    extent and keeps an in-extent note in the same batch."""
    book_path = _write_book(tmp_path, "oba")

    inserted = promote.batch_insert_notes(
        book_path,
        [
            {"chapter": 2, "verse": 1, "kind": "note", "body": "above-extent"},
            {"chapter": 1, "verse": 1, "kind": "note", "body": "in-extent"},
        ],
    )

    text = book_path.read_text(encoding="utf-8")
    assert inserted == 1
    assert "above-extent" not in text
    assert "in-extent" in text


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-q"]))

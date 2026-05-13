"""N-W4 contract — promote_candidate must be idempotent.

Regression test for the χ-cluster pipeline bug discovered during the
γ.4.6.B ship: running batch_promote_xrefs against a candidate set
that was already promoted (because run_ethiopian_at_scale.py regen-
erates candidate JSONs with status="pending" afresh) produced
duplicate tuples with the NEXT free suffix letter. The fix, landed
in `scripts/promote.py` (`note_already_exists` helper + early-return
in `promote_candidate`), ensures that a candidate identical to an
existing note (same chapter, verse, kind, body, attribution) is
treated as a skip.

These tests use ``tmp_path`` for a self-contained book file fixture;
they do NOT touch the real ``content/notes/`` corpus.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import scripts.promote as promote_mod  # noqa: E402
from scripts.promote import note_already_exists, promote_candidate  # noqa: E402

BOOK_FILE_TEMPLATE = '''"""Tmp test fixture for {book} notes."""

NOTES = [
{tuples}
]
NOTES_{book_upper} = NOTES
'''


def _write_book_file(tmp_path: Path, book: str, tuples_text: str) -> Path:
    notes_dir = tmp_path / "content" / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    path = notes_dir / f"{book}.py"
    path.write_text(
        BOOK_FILE_TEMPLATE.format(
            book=book,
            book_upper=book.upper(),
            tuples=tuples_text,
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def fake_book(tmp_path, monkeypatch):
    """Set up a tmp book file (tst.py) with one pre-existing comm-
    ethiopian tuple, and redirect ``promote.NOTES_DIR`` to the tmp
    location so promote_candidate writes into our fixture."""
    body = '<aside class="note-comm-ethiopian"><strong>Cyril</strong><p>Body text.</p></aside>'
    attribution = "Cyril of Alexandria, Commentary on Matthew. PD."
    tuples_text = (
        f"    (\n"
        f"        1, 1, 'a', '',\n"
        f"        'comm-ethiopian', 'Title',\n"
        f"        'Label',\n"
        f"        {body!r},\n"
        f"        {attribution!r},\n"
        f"    ),\n"
    )
    book_path = _write_book_file(tmp_path, "tst", tuples_text)
    notes_dir = book_path.parent
    monkeypatch.setattr(promote_mod, "NOTES_DIR", notes_dir)
    return {
        "path": book_path,
        "body": body,
        "attribution": attribution,
    }


def _candidate(*, verse=1, chapter=1, kind="comm-ethiopian", body="body", attribution="src"):
    return {
        "id": f"tst-{chapter}-{verse}-001",
        "chapter": chapter,
        "verse": verse,
        "kind": kind,
        "anchor": "",
        "draft_title": "Title",
        "draft_label": "Label",
        "draft_body": body,
        "source_attribution": attribution,
        "source_name": "Cyril of Alexandria",
        "confidence": 0.9,
    }


class TestNoteAlreadyExists:
    """Contract: note_already_exists returns True only when a tuple
    with identical (chapter, verse, kind, body, attribution) is
    present in the target book file."""

    def test_returns_true_on_exact_match(self, fake_book):
        assert note_already_exists(
            fake_book["path"], 1, 1, "comm-ethiopian", fake_book["body"], fake_book["attribution"]
        )

    def test_returns_false_on_different_body(self, fake_book):
        assert not note_already_exists(
            fake_book["path"], 1, 1, "comm-ethiopian", "<aside>DIFFERENT body</aside>", fake_book["attribution"]
        )

    def test_returns_false_on_different_attribution(self, fake_book):
        assert not note_already_exists(
            fake_book["path"], 1, 1, "comm-ethiopian", fake_book["body"], "DIFFERENT attribution"
        )

    def test_returns_false_on_different_kind(self, fake_book):
        assert not note_already_exists(
            fake_book["path"], 1, 1, "topic-nave", fake_book["body"], fake_book["attribution"]
        )

    def test_returns_false_on_different_verse(self, fake_book):
        assert not note_already_exists(
            fake_book["path"], 1, 2, "comm-ethiopian", fake_book["body"], fake_book["attribution"]
        )

    def test_returns_false_on_different_chapter(self, fake_book):
        assert not note_already_exists(
            fake_book["path"], 2, 1, "comm-ethiopian", fake_book["body"], fake_book["attribution"]
        )

    def test_returns_false_when_file_missing(self, tmp_path):
        assert not note_already_exists(tmp_path / "no.py", 1, 1, "comm-ethiopian", "body", "attr")

    def test_handles_none_attribution_equiv_to_empty(self, fake_book):
        """A tuple stored with empty-string attribution should match
        a query with None attribution (and vice versa)."""
        # Add a tuple with empty 9th-field attribution
        text = fake_book["path"].read_text(encoding="utf-8")
        body_2 = "<aside>second body</aside>"
        new_tuple = (
            f"    (\n"
            f"        2, 5, '', '',\n"
            f"        'comm', 'Title',\n"
            f"        'Label',\n"
            f"        {body_2!r},\n"
            f"        '',\n"
            f"    ),\n"
        )
        text = text.replace("NOTES = [\n", "NOTES = [\n" + new_tuple)
        fake_book["path"].write_text(text, encoding="utf-8")
        # Query with None attribution should still match
        assert note_already_exists(fake_book["path"], 2, 5, "comm", body_2, None)
        # Query with non-empty different attribution should NOT match
        assert not note_already_exists(fake_book["path"], 2, 5, "comm", body_2, "different")


class TestPromoteCandidateIdempotency:
    """Contract: promote_candidate returns (False, '') without writing
    when the same (chapter, verse, kind, body, attribution) already
    exists. Critical for χ-cluster pipeline idempotency."""

    def test_first_promote_succeeds(self, fake_book):
        c = _candidate(
            verse=2,
            body="<aside class='note-comm-ethiopian'>fresh content</aside>",
            attribution="Fresh source. PD.",
        )
        ok, suffix = promote_candidate("tst", c)
        assert ok is True
        assert suffix == ""  # first note on this verse → empty suffix

    def test_second_promote_of_same_candidate_is_skipped(self, fake_book):
        c = _candidate(
            verse=3,
            body="<aside class='note-comm-ethiopian'>same content</aside>",
            attribution="Same source. PD.",
        )
        # First promote → ok
        ok1, _ = promote_candidate("tst", c)
        assert ok1 is True
        # Second promote of identical candidate → MUST be skipped
        ok2, suffix2 = promote_candidate("tst", c)
        assert ok2 is False
        assert suffix2 == ""

    def test_second_promote_of_pre_existing_fixture_is_skipped(self, fake_book):
        """The fixture pre-seeds a note at 1:1; promoting the SAME
        content again must skip."""
        c = _candidate(
            verse=1,
            chapter=1,
            body=fake_book["body"],
            attribution=fake_book["attribution"],
        )
        ok, _ = promote_candidate("tst", c)
        assert ok is False

    def test_different_body_same_verse_is_not_skipped(self, fake_book):
        """Two notes on the same verse with the same kind but DIFFERENT
        body are legitimately different — must promote both."""
        c = _candidate(
            verse=1,
            chapter=1,
            body="<aside>DIFFERENT body content</aside>",
            attribution=fake_book["attribution"],
        )
        ok, suffix = promote_candidate("tst", c)
        assert ok is True
        # Should get suffix 'b' (the pre-seed has 'a'; '' is free per
        # pick_free_suffix). Actually pick_free_suffix picks '' if free;
        # since pre-seed has 'a' but '' is free, suffix is ''.
        assert suffix == ""

    def test_running_promote_twenty_times_writes_only_once(self, fake_book):
        """Twenty repeated promotes of the same candidate must produce
        exactly ONE tuple in the file, not twenty."""
        c = _candidate(
            verse=7,
            body="<aside class='note-comm-ethiopian'>repeat test</aside>",
            attribution="Repeat source. PD.",
        )
        n_ok = 0
        for _ in range(20):
            ok, _ = promote_candidate("tst", c)
            if ok:
                n_ok += 1
        assert n_ok == 1, f"expected exactly 1 successful promote across 20 tries; got {n_ok}"
        # Verify the file has exactly one matching tuple. ``repeat test``
        # is the unique body marker; check for the substring regardless
        # of which Python string-quote style was emitted (the body
        # contains single quotes from class='…' so the emitter wraps
        # in double quotes).
        text = fake_book["path"].read_text(encoding="utf-8")
        assert text.count("repeat test</aside>") == 1, "expected exactly one occurrence of the body text in file"

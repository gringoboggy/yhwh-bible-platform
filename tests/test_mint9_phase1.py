"""mint-9 (deep-audit round 2) Phase-1 guards.

Covers two HIGH findings:

  #2  build_edition._iter_note_ref_traditions / _iter_note_ref_attribution_years
      skipped Strategy-B books that lack ``id_prefix`` (the bulk of the canon),
      so their notes silently survived tradition/time filters. inject.py builds
      those books' HTML ref-ids from ``bxx`` (inject.py:674-677); the iterators
      now mirror that fallback so the emitted ref-id matches the live HTML.

  #3  promote.format_tuple_text.py_str escaped \\n/\\r but NOT the backslash
      itself, so a note body containing a literal "\\" produced an invalid
      one-line Python literal. batch_insert_notes' post-splice ``ast.parse``
      then SILENTLY dropped the whole (otherwise valid) batch via a bare
      ``except SyntaxError: return 0``. Root-cause: escape backslash first.
      Safety net: the post-splice guard now logs before dropping.

These tests fail on the pre-fix code (the backslash body round-trips wrong /
the Strategy-B ref-id is absent), so they are real guards, not tautologies.
"""

from __future__ import annotations

import ast
import logging
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import build_edition  # noqa: E402
from scripts import promote  # noqa: E402
from scripts.promote import batch_insert_notes, format_tuple_text  # noqa: E402


# ---------------------------------------------------------------------------
# #3 — backslash root cause + post-splice silent-drop safety net
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "body",
    [
        r"A Windows path C:\Users\bogda and a \tab",
        r"LaTeX \frac{a}{b} and a trailing backslash \\",
        "newline\nand carriage\rreturn",
        "quotes \"double\" and 'single' mixed",
        "plain ascii — unchanged",
    ],
)
def test_format_tuple_text_roundtrips_backslash_bodies(body: str) -> None:
    """A body with a literal backslash must survive format → ast round-trip.

    Pre-fix (no backslash escaping) this raised SyntaxError for the path and
    LaTeX cases, which is exactly what triggered the silent batch drop.
    """
    txt = format_tuple_text(1, 1, "", "", "comm-test", "Title", "Label", body)
    tup = ast.literal_eval(txt.strip().rstrip(","))
    assert tup[7] == body, f"body corrupted in round-trip: {tup[7]!r} != {body!r}"


def test_batch_insert_accepts_backslash_body(tmp_path) -> None:
    """A note body with a raw backslash is inserted, not silently dropped."""
    p = tmp_path / "gen.py"
    p.write_text("NOTES = [\n]\n", encoding="utf-8")
    inserted = batch_insert_notes(
        p,
        [{"chapter": 1, "verse": 1, "kind": "topic-nave", "body": r"path C:\x\y backslash"}],
    )
    assert inserted == 1
    # The written file must itself be valid Python (no corruption).
    ast.parse(p.read_text(encoding="utf-8"))


def test_batch_insert_logs_when_post_splice_parse_fails(tmp_path, monkeypatch, caplog) -> None:
    """If generated text is invalid, the drop is LOGGED, never silent (#3).

    We force the failure by monkeypatching format_tuple_text to emit a broken
    tuple, proving the post-splice ``except SyntaxError`` path logs an error.
    """
    p = tmp_path / "gen.py"
    p.write_text("NOTES = [\n]\n", encoding="utf-8")
    before = p.read_text(encoding="utf-8")

    def _broken(*_a, **_k):
        return "    (this is not valid python,\n"

    monkeypatch.setattr(promote, "format_tuple_text", _broken)
    with caplog.at_level(logging.ERROR):
        inserted = batch_insert_notes(p, [{"chapter": 1, "verse": 1, "kind": "topic-nave", "body": "x"}])
    assert inserted == 0
    # File untouched (no backup/write on the failure path).
    assert p.read_text(encoding="utf-8") == before
    assert any("dropping" in r.message.lower() for r in caplog.records), (
        "post-splice SyntaxError drop must emit an ERROR log, not be silent"
    )


# ---------------------------------------------------------------------------
# #2 — tradition/time filter Strategy-B bxx fallback
# ---------------------------------------------------------------------------


def _ref_ids_for_book(book_code: str) -> set[str]:
    """All HTML ref-ids the tradition iterator emits for one book."""
    return {ref_id for (ref_id, _trad, bc) in build_edition._iter_note_ref_traditions() if bc == book_code}


def test_strategy_b_book_emits_bxx_ref_ids() -> None:
    """A Strategy-B book with real notes (2ch, bxx=b13) must now yield
    ``ref-b13....`` ids — pre-fix the iterator skipped it entirely, so its
    notes could never join any tradition/time disabled set."""
    from scripts.core import config

    book = config.books_by_code().get("2ch") or {}
    if not book or book.get("id_prefix"):
        pytest.skip("2ch is not a no-id_prefix Strategy-B book in this config")
    bxx = book.get("bxx")
    assert bxx, "2ch should have a bxx in books.yaml"

    ref_ids = _ref_ids_for_book("2ch")
    # 2ch has real notes on disk (e.g. ch1 v1 lang-hebrew); if it has any notes
    # at all, the iterator must surface them with bxx-based ids.
    from scripts.core.notes_io import load_notes

    notes = load_notes(REPO_ROOT / "content" / "notes" / "2ch.py") or []
    if not notes:
        pytest.skip("2ch has no notes on disk in this checkout")
    assert ref_ids, "Strategy-B book 2ch yielded no ref-ids (bxx fallback missing)"
    assert all(r.startswith(f"ref-{bxx}") for r in ref_ids), (
        f"2ch ref-ids must use the bxx prefix {bxx!r}: {sorted(ref_ids)[:3]}"
    )


def test_iterator_ref_ids_match_inject_format() -> None:
    """The iterator's id format must equal inject.py's: ref-<prefix><cc><vv><suffix>
    with prefix = id_prefix or bxx. Spot-check the 5-digit zero-padded shape."""
    ids = _ref_ids_for_book("2ch")
    if not ids:
        pytest.skip("no 2ch notes to check")
    sample = sorted(ids)[0]
    # ref-b13 + at least 4 digits (ccvv)
    assert sample.startswith("ref-"), sample
    digits = sample.removeprefix("ref-")[3:]  # strip 'b13'
    assert digits[:4].isdigit(), f"expected zero-padded ccvv after bxx: {sample}"


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-q"]))

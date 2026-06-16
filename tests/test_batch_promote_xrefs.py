"""mint-11 audit fixes for the fast by-book promote path
(``scripts/batch_promote_xrefs.py``).

HIGH-1: the status-marking loop must NOT mark candidates ``"promoted"`` for books
        whose notes file is missing (e.g. ``1ma``/``2ma``) — doing so silently
        drops them from the pipeline with no insert and no error.
HIGH-2: ``_candidate_to_note`` must strip the editorial ``[Reviewer: …]`` scaffold,
        mirroring the slow ``promote_candidate`` path, so it never reaches the
        corpus / built EPUBs.
"""

from __future__ import annotations

import json

from scripts import batch_promote_xrefs as bpx

SCAFFOLD = " <em>[Reviewer: extend this with context before promoting.]</em>"

# A real-shaped NOTES file (9-field tuple, multi-line) so batch_insert_notes can
# splice into it cleanly — an empty single-line ``NOTES = []`` makes it generate
# invalid Python and drop the insert.
_SEED_NOTES = """NOTES = [
    (
        1,
        1,
        "",
        "seed",
        "commentary",
        "Seed",
        "note",
        "An existing seed note.",
        "Test fixture",
    ),
]
"""


def _write_queue(path, book, chapter, candidates):
    path.write_text(
        json.dumps({"book": book, "chapter": chapter, "candidates": candidates}, indent=2),
        encoding="utf-8",
    )


# ── HIGH-2 ────────────────────────────────────────────────────────────────────
def test_candidate_to_note_strips_reviewer_scaffold():
    c = {
        "kind": "xref-citation",
        "verse": 1,
        "draft_body": "See also John 1:1." + SCAFFOLD,
        "draft_title": "Cross-reference",
        "draft_label": "xref",
    }
    note = bpx._candidate_to_note(c, chapter=1)
    assert "[Reviewer:" not in note["body"]
    assert note["body"] == "See also John 1:1."


# ── HIGH-1 ────────────────────────────────────────────────────────────────────
def test_promote_by_book_does_not_mark_missing_book_candidates(tmp_path, monkeypatch):
    """A book with no ``<book>.py`` notes file (e.g. 1ma) keeps its candidates
    ``"pending"`` instead of being silently marked ``"promoted"`` with no insert."""
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    monkeypatch.setattr(bpx, "NOTES_DIR", notes_dir)

    q = tmp_path / "1ma_1.json"
    _write_queue(
        q,
        "1ma",
        1,
        [{"id": "c1", "kind": "xref-citation", "status": "pending", "verse": 1, "draft_body": "x"}],
    )

    attempted, promoted, books_changed = bpx.promote_by_book([q], None, None)

    data = json.loads(q.read_text(encoding="utf-8"))
    assert data["candidates"][0]["status"] == "pending", "missing-book candidate was wrongly marked promoted"
    assert promoted == 0
    assert books_changed == 0


def test_promote_by_book_marks_present_book_candidates(tmp_path, monkeypatch):
    """A book WITH a notes file is inserted and its candidate marked ``"promoted"``
    (the fix must not regress the normal happy path)."""
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "gen.py").write_text(_SEED_NOTES, encoding="utf-8")
    monkeypatch.setattr(bpx, "NOTES_DIR", notes_dir)

    q = tmp_path / "gen_1.json"
    _write_queue(
        q,
        "gen",
        1,
        [
            {
                "id": "c1",
                "kind": "xref-citation",
                "status": "pending",
                "verse": 1,
                "draft_body": "See John 1:1.",
                "draft_title": "X",
                "draft_label": "xref",
            }
        ],
    )

    attempted, promoted, books_changed = bpx.promote_by_book([q], None, None)

    data = json.loads(q.read_text(encoding="utf-8"))
    assert data["candidates"][0]["status"] == "promoted"
    assert promoted == 1
    assert books_changed == 1


def test_promote_by_book_mixed_present_and_missing(tmp_path, monkeypatch):
    """With one present book and one missing book in the same run, only the present
    book's candidate is marked — the missing book's stays pending."""
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "gen.py").write_text(_SEED_NOTES, encoding="utf-8")
    monkeypatch.setattr(bpx, "NOTES_DIR", notes_dir)

    qg = tmp_path / "gen_1.json"
    _write_queue(
        qg,
        "gen",
        1,
        [{"id": "g1", "kind": "xref-citation", "status": "pending", "verse": 1, "draft_body": "See John 1:1."}],
    )
    qm = tmp_path / "1ma_1.json"
    _write_queue(
        qm,
        "1ma",
        1,
        [{"id": "m1", "kind": "xref-citation", "status": "pending", "verse": 1, "draft_body": "y"}],
    )

    bpx.promote_by_book([qg, qm], None, None)

    assert json.loads(qg.read_text(encoding="utf-8"))["candidates"][0]["status"] == "promoted"
    assert json.loads(qm.read_text(encoding="utf-8"))["candidates"][0]["status"] == "pending"


def test_promote_by_book_does_not_mark_when_all_coords_dropped(tmp_path, monkeypatch):
    """Out-of-extent candidates must stay pending when batch_insert_notes inserts zero."""
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "gen.py").write_text(_SEED_NOTES, encoding="utf-8")
    monkeypatch.setattr(bpx, "NOTES_DIR", notes_dir)

    q = tmp_path / "gen_99.json"
    _write_queue(
        q,
        "gen",
        99,
        [
            {
                "id": "c1",
                "kind": "xref-citation",
                "status": "pending",
                "verse": 1,
                "draft_body": "Impossible coord.",
                "draft_title": "X",
                "draft_label": "xref",
            }
        ],
    )

    attempted, promoted, books_changed = bpx.promote_by_book([q], None, None)

    data = json.loads(q.read_text(encoding="utf-8"))
    assert data["candidates"][0]["status"] == "pending"
    assert promoted == 0
    assert books_changed == 0
    assert attempted == 1

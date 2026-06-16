"""Phase 1 — inject.py must surface unparseable notes files, not treat as empty."""

from __future__ import annotations


def test_inject_book_reports_syntax_error_on_broken_notes_file(tmp_path, monkeypatch):
    from scripts import inject

    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "gen.py").write_text("NOTES = [(  # broken\n", encoding="utf-8")
    monkeypatch.setattr(inject, "NOTES_DIR", notes_dir)

    book = {
        "code": "gen",
        "id_prefix": "gen",
        "strategy": "A",
        "files": ["index_split_001.html"],
        "ch_count": 50,
    }
    result = inject.inject_book(book, dry_run=True)
    assert "error" in result
    assert "unparseable" in result["error"].lower() or "syntax" in result["error"].lower()

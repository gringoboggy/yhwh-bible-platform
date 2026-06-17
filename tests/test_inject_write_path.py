"""Phase 4 — inject_book dry_run=False must write HTML + backup."""

from __future__ import annotations

GEN_HTML = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
<p class="verse-p"><a class="vn-link" id="v-gen-1-1" href="#vnote-gen-1-1"><span class="vn">1</span></a> In the beginning God created.</p>
</body>
</html>
"""

GEN_NOTES = '''"""Notes for gen."""

NOTES = [
    (1, 1, "", "beginning", "xref-citation", "Cross-ref", "Cite.", "<p>body</p>", None),
]
'''


def test_inject_book_writes_html_backup_and_idempotent_second_run(tmp_path, monkeypatch):
    from scripts import inject

    epub = tmp_path / "epub"
    epub.mkdir()
    html_path = epub / "index_split_000.html"
    html_path.write_text(GEN_HTML, encoding="utf-8")

    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "gen.py").write_text(GEN_NOTES, encoding="utf-8")

    monkeypatch.setattr(inject, "EPUB_DIR", epub)
    monkeypatch.setattr(inject, "NOTES_DIR", notes_dir)

    book = {
        "code": "gen",
        "bxx": "b00",
        "id_prefix": "g",
        "strategy": "A",
        "ch_count": 50,
        "files": ["index_split_000.html"],
    }

    first = inject.inject_book(book, dry_run=False)
    assert first.get("injected") == 1, first
    assert first.get("files_changed") == ["index_split_000.html"]

    out = html_path.read_text(encoding="utf-8")
    assert 'id="ref-g0101"' in out
    assert "note-aside" in out or "aside" in out

    backups = list((epub / ".backups").glob("index_split_000.*.html.bak"))
    assert backups, "ensure_backup should snapshot HTML before write"

    second = inject.inject_book(book, dry_run=False)
    assert second.get("injected") == 0, second
    assert second.get("already_in") == 1, second

"""Phase 1 — promote._chapter_from_id must parse chapter from the id tail."""

from __future__ import annotations


class TestChapterFromId:
    def test_simple_book_code(self):
        from scripts.promote import _chapter_from_id

        assert _chapter_from_id("gen-1-5-042") == 1
        assert _chapter_from_id("1co-13-1-001") == 13

    def test_hyphenated_book_segment_uses_rsplit(self):
        from scripts.promote import _chapter_from_id

        assert _chapter_from_id("lxx-brenton-english-13-1-001") == 13
        assert _chapter_from_id("a-b-c-d-e-10-20-001") == 10

    def test_promote_candidate_uses_explicit_zero_chapter(self, tmp_path, monkeypatch):
        """chapter=0 is invalid but must not be replaced by the id-parse fallback."""
        from scripts import promote

        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        (notes_dir / "gen.py").write_text("NOTES = []\n", encoding="utf-8")
        monkeypatch.setattr(promote, "NOTES_DIR", notes_dir)

        c = {
            "id": "gen-99-1-001",
            "chapter": 0,
            "verse": 1,
            "kind": "xref-citation",
            "draft_body": "See also.",
            "draft_title": "X",
            "draft_label": "xref",
        }
        ok, _ = promote.promote_candidate("gen", c)
        assert ok is False

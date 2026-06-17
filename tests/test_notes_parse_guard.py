"""Phase 4 — load_notes None must not be conflated with empty corpus."""

from __future__ import annotations

import json

import pytest


def test_load_notes_checked_returns_error_on_syntax_error(tmp_path):
    from scripts.core import notes_io

    path = tmp_path / "gen.py"
    path.write_text("NOTES = [(  # broken\n", encoding="utf-8")
    result = notes_io.load_notes_checked(path, book="gen")
    assert isinstance(result, dict)
    assert result.get("http") == 500
    assert "unparseable" in result.get("error", "").lower()


def test_api_notes_refuses_unparseable_book(tmp_path, monkeypatch):
    from scripts import web_notes

    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "gen.py").write_text("NOTES = [(  # broken\n", encoding="utf-8")
    monkeypatch.setattr(web_notes, "NOTES_DIR", notes_dir)

    result = web_notes.api_notes("gen")
    assert result.get("http") == 500
    assert "unparseable" in result.get("error", "").lower()


def test_api_save_refuses_unparseable_book(tmp_path, monkeypatch):
    from scripts import web_notes

    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    corrupt = notes_dir / "gen.py"
    corrupt.write_text("NOTES = [(  # broken\n", encoding="utf-8")
    monkeypatch.setattr(web_notes, "NOTES_DIR", notes_dir)

    before = corrupt.read_text(encoding="utf-8")
    result = web_notes.api_save(
        "gen",
        {
            "ch": 1,
            "v": 1,
            "kind": "comm",
            "body": "<p>new</p>",
            "index": None,
        },
    )
    assert result.get("http") == 500
    assert corrupt.read_text(encoding="utf-8") == before


def test_api_delete_refuses_unparseable_book(tmp_path, monkeypatch):
    from scripts import web_notes

    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    corrupt = notes_dir / "gen.py"
    corrupt.write_text("NOTES = [(  # broken\n", encoding="utf-8")
    monkeypatch.setattr(web_notes, "NOTES_DIR", notes_dir)

    before = corrupt.read_text(encoding="utf-8")
    result = web_notes.api_delete("gen", 0)
    assert result.get("http") == 500
    assert corrupt.read_text(encoding="utf-8") == before


def test_append_candidates_aborts_on_corrupt_json(tmp_path):
    from scripts.core.at_scale_base import CandidateQueueCorruptError, append_candidates

    out = tmp_path / "gen_ch_001.json"
    out.write_text("{not json", encoding="utf-8")
    with pytest.raises(CandidateQueueCorruptError):
        append_candidates(out, "gen", 1, [{"verse": 1, "kind": "xref", "draft_body": "x"}])


def test_api_sources_for_book_refuses_unparseable(tmp_path, monkeypatch):
    from scripts import web_sources

    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "gen.py").write_text("NOTES = [(  # broken\n", encoding="utf-8")
    monkeypatch.setattr(web_sources, "NOTES_DIR", notes_dir)

    result = web_sources.api_sources_for_book("gen")
    assert result.get("http") == 500
    assert "unparseable" in result.get("error", "").lower()


def test_preview_refuses_unparseable_notes(tmp_path, monkeypatch):
    from scripts.core import preview

    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "gen.py").write_text("NOTES = [(  # broken\n", encoding="utf-8")
    monkeypatch.setattr(preview, "NOTES_DIR", notes_dir)

    result = preview.render_chapter_preview("ethiopian-tewahedo", "gen", 1)
    assert result["status"] == "error"
    assert result.get("http") == 500
    assert "unparseable" in result.get("message", "").lower()


def test_api_save_sanitizes_script_in_body(tmp_path, monkeypatch):
    from scripts import web_helpers, web_notes
    from scripts.core import notes_io

    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "gen.py").write_text("NOTES = []\n", encoding="utf-8")
    monkeypatch.setattr(web_notes, "NOTES_DIR", notes_dir)
    monkeypatch.setattr(web_helpers, "NOTES_DIR", notes_dir)

    result = web_notes.api_save(
        "gen",
        {
            "ch": 1,
            "v": 1,
            "kind": "comm",
            "body": "<p>ok</p><script>alert(1)</script>",
            "index": None,
        },
    )
    assert result.get("ok") is True
    notes = notes_io.load_notes(notes_dir / "gen.py")
    assert notes is not None
    assert len(notes) == 1
    assert "<script>" not in notes[0][7].lower()

"""Phase 1 — prospect.py write_queue must preserve promotion status (mint-10 parity)."""

from __future__ import annotations

import json

import pytest


class _FakeCand:
    def __init__(self, verse: int, kind: str, body: str):
        self.book = "gen"
        self.chapter = 1
        self.verse = verse
        self.kind = kind
        self.anchor = ""
        self.confidence = 0.9
        self.source_name = "src"
        self.source_attribution = "attr"
        self.draft_title = "t"
        self.draft_label = "l"
        self.draft_body = body
        self.detector = "Fake"
        self.reviewer_notes = ""


def test_prospect_write_queue_preserves_promoted_status(tmp_path, monkeypatch):
    from scripts import prospect

    cand_dir = tmp_path / "candidates"
    cand_dir.mkdir()
    monkeypatch.setattr(prospect, "CANDIDATES_DIR", cand_dir)

    out_path = cand_dir / "gen_ch_001.json"
    out_path.write_text(
        json.dumps(
            {
                "book": "gen",
                "chapter": 1,
                "n_candidates": 1,
                "candidates": [
                    {
                        "id": "gen-1-1-001",
                        "verse": 1,
                        "kind": "topic-nave",
                        "draft_body": "Kept body",
                        "status": "promoted",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    prospect.write_queue("gen", 1, [_FakeCand(2, "topic-nave", "New body")])

    cands = json.loads(out_path.read_text(encoding="utf-8"))["candidates"]
    promoted = [c for c in cands if c["draft_body"] == "Kept body"]
    assert len(promoted) == 1 and promoted[0]["status"] == "promoted"
    new_entries = [c for c in cands if c["draft_body"] == "New body"]
    assert len(new_entries) == 1 and new_entries[0]["status"] == "pending"


def test_prospect_write_queue_delegates_to_append_candidates(monkeypatch):
    from scripts import prospect

    called = {}

    def fake_append(out_path, book, chapter, candidates):
        called["args"] = (out_path, book, chapter, candidates)
        return out_path

    monkeypatch.setattr(prospect, "append_candidates", fake_append)
    prospect.write_queue("gen", 1, [object()])
    assert called["args"][1] == "gen"
    assert called["args"][2] == 1


def test_prospect_main_handles_none_out_path_without_crashing(monkeypatch, capsys):
    """round-14 audit regression: a chapter with verses>0 but every candidate deduped →
    prospect_chapter returns out_path=None; main() must NOT AttributeError on the
    `stats["out_path"].relative_to(...)` line — it prints a 'queue already complete' line
    and continues (exit 0)."""
    import sys

    from scripts import prospect
    from scripts.core import config, sources

    monkeypatch.setattr(sources, "strongs_hebrew", lambda: {})
    monkeypatch.setattr(sources, "tsk", lambda: {})
    monkeypatch.setattr(config, "get_book", lambda b: {"code": b})
    monkeypatch.setattr(config, "kinds_by_code", lambda: {})
    monkeypatch.setattr(
        prospect,
        "prospect_chapter",
        lambda *a, **k: {"verses": 7, "candidates": 0, "deduped": 7, "out_path": None},
    )
    monkeypatch.setattr(sys, "argv", ["prospect", "gen", "1"])

    with pytest.raises(SystemExit) as exc:
        prospect.main()
    assert exc.value.code == 0
    assert "queue already complete" in capsys.readouterr().out

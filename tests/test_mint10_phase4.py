"""mint-10 Phase 4 — at-scale driver ★BUGCLUSTER sweep regressions.

- All 8 candidate-generating drivers (4 accumulators: xref/naves/torrey/ethiopian
  + 4 kind-replace: hebrew/greek/ai_xrefs/ai_notes) now delegate ``write_queue`` to
  the single ``at_scale_base.append_candidates``, which preserves every existing
  entry AND its ``status``. The kind-replace drivers used to PURGE their own kind
  before re-adding it, silently resetting a prior ``promoted`` back to ``pending``.
- ``resolve_books`` normalizes an explicit ``--books`` arg to canonical codes.
"""

import json

import pytest


DRIVER_MODULES = [
    "scripts.run_xref_at_scale",
    "scripts.run_naves_at_scale",
    "scripts.run_torrey_at_scale",
    "scripts.run_ethiopian_at_scale",
    "scripts.run_hebrew_at_scale",
    "scripts.run_greek_at_scale",
    "scripts.run_ai_xrefs_at_scale",
    "scripts.run_ai_notes_at_scale",
]


class _FakeCandidate:
    """Minimal stand-in carrying the attributes candidate_to_dict reads."""

    def __init__(self, book, chapter, verse, kind, body):
        self.book = book
        self.chapter = chapter
        self.verse = verse
        self.kind = kind
        self.anchor = ""
        self.confidence = 0.9
        self.source_name = "src"
        self.source_attribution = "attr"
        self.draft_title = "t"
        self.draft_label = "l"
        self.draft_body = body
        self.detector = "FakeDetector"
        self.reviewer_notes = ""


class TestMint10AllDriversDelegate:
    @pytest.mark.parametrize("modname", DRIVER_MODULES)
    def test_write_queue_delegates_to_append_candidates(self, modname, monkeypatch):
        import importlib

        mod = importlib.import_module(modname)
        called = {}

        def fake_append(out_path, book, chapter, candidates):
            called["args"] = (out_path, book, chapter, candidates)
            return out_path

        # Each driver imported append_candidates into its own namespace.
        monkeypatch.setattr(mod, "append_candidates", fake_append)
        mod.write_queue("gen", 1, [object()])
        assert called, f"{modname}.write_queue did not delegate to append_candidates"
        assert called["args"][1] == "gen"
        assert called["args"][2] == 1


class TestMint10AppendCandidatesContract:
    def test_preserves_existing_status_and_dedups(self, tmp_path):
        from scripts.core.at_scale_base import append_candidates

        out_path = tmp_path / "gen_ch_001.json"
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
                            "draft_body": "Existing body",
                            "status": "promoted",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        dup = _FakeCandidate("gen", 1, 1, "topic-nave", "Existing body")  # same (verse,kind,body)
        new = _FakeCandidate("gen", 1, 2, "topic-nave", "New body")
        ret = append_candidates(out_path, "gen", 1, [dup, new])
        assert ret == out_path

        cands = json.loads(out_path.read_text(encoding="utf-8"))["candidates"]
        # Existing promoted entry kept verbatim — status NOT reset (the bug).
        promoted = [c for c in cands if c["draft_body"] == "Existing body"]
        assert len(promoted) == 1 and promoted[0]["status"] == "promoted"
        # Duplicate not re-added; the genuinely-new one added as pending.
        new_entries = [c for c in cands if c["draft_body"] == "New body"]
        assert len(new_entries) == 1 and new_entries[0]["status"] == "pending"
        assert len(cands) == 2

    def test_nothing_new_returns_none(self, tmp_path):
        from scripts.core.at_scale_base import append_candidates

        # Empty input → no write.
        assert append_candidates(tmp_path / "x_ch_001.json", "gen", 1, []) is None


class TestMint10ResolveBooksNormalizes:
    def test_explicit_books_are_canonicalized(self):
        from scripts.core.at_scale_base import resolve_books
        from scripts.core.sources import _normalize_book_code

        raw = "php,jas,gen"
        expected = [_normalize_book_code(b) for b in ("php", "jas", "gen")]
        assert resolve_books(raw) == expected
        # And the normalization is non-trivial (legacy aliases really change) —
        # guards against resolve_books silently dropping the normalize again.
        assert expected != ["php", "jas", "gen"]

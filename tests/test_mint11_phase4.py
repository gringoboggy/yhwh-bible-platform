"""mint-11 round-4 fixes — Phase 4 (silent-data-loss & atomicity correctness).

Covers:
- #2  promote.batch_insert_notes within-batch dedup gap (duplicate notes when
      new_notes carries two identical (ch,v,kind,body) dicts).
- #3a update_book_floors crashed with len(None) when a notes file fails to parse.
- #14 corpus_index._build_to computed the fingerprint AFTER the atomic swap (stale-
      index race).
- #4  standalone_store wrote the live geez-tewahedo corpus with bare write_text
      (no atomicity — a crash mid-write left a SyntaxError-on-load store).
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class TestMint11PromoteWithinBatchDedup:
    def test_identical_notes_in_one_batch_insert_once(self, tmp_path):
        """Two byte-identical (ch,v,kind,body) dicts in a single new_notes batch
        must collapse to ONE insert. Pre-fix: existing_bodies was not updated as
        each note inserted, so the second identical note slipped through (= 2)."""
        from scripts.core.notes_io import load_notes
        from scripts.promote import batch_insert_notes

        p = tmp_path / "gen.py"
        p.write_text("NOTES = [\n]\n", encoding="utf-8")
        new = [
            {"ch": 1, "v": 1, "kind": "topic-nave", "body": "dup body"},
            {"ch": 1, "v": 1, "kind": "topic-nave", "body": "dup body"},  # identical
        ]
        inserted = batch_insert_notes(p, new)
        assert inserted == 1, f"within-batch duplicate not deduped (got {inserted})"
        assert len(load_notes(p)) == 1

    def test_distinct_bodies_same_verse_still_both_insert(self, tmp_path):
        """Guard against over-dedup: two DIFFERENT bodies on the same verse/kind
        must both insert (the dedup keys on body, not just (ch,v,kind))."""
        from scripts.core.notes_io import load_notes
        from scripts.promote import batch_insert_notes

        p = tmp_path / "gen.py"
        p.write_text("NOTES = [\n]\n", encoding="utf-8")
        new = [
            {"ch": 1, "v": 1, "kind": "topic-nave", "body": "body A"},
            {"ch": 1, "v": 1, "kind": "topic-nave", "body": "body B"},
        ]
        assert batch_insert_notes(p, new) == 2
        assert len(load_notes(p)) == 2


class TestMint11UpdateBookFloorsParseFailure:
    def test_compute_floors_survives_a_bad_notes_file(self, tmp_path, monkeypatch):
        """A notes file that fails to parse (load_notes -> None) must be skipped
        with a warning, not crash compute_floors with len(None)."""
        import warnings

        import scripts.update_book_floors as ubf

        nd = tmp_path / "notes"
        nd.mkdir()
        (nd / "gen.py").write_text("NOTES = []\n", encoding="utf-8")
        (nd / "bad.py").write_text("NOTES = [ this is ( not valid python\n", encoding="utf-8")
        monkeypatch.setattr(ubf, "NOTES_DIR", nd)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            floors = ubf.compute_floors()  # must not raise
        assert "gen" in floors
        assert "bad" not in floors, "a parse-failed book must be skipped, not floored"
        assert any("bad" in str(w.message) for w in caught), "expected a warning for the bad file"


class TestMint11SourceGuards:
    def test_corpus_index_fingerprint_computed_before_swap(self):
        """#14: in _build_to the fingerprint must be computed BEFORE tmp.replace,
        else a notes edit in the gap is recorded as a MATCH (stale index never
        rebuilds)."""
        src = (REPO / "scripts" / "core" / "corpus_index.py").read_text(encoding="utf-8")
        start = src.index("def _build_to(")
        end = src.index("\ndef ", start + 1)
        # Strip full-line comments so the comment that mentions `tmp.replace(path)`
        # (it explains the Windows-atomic rename) cannot false-match ahead of the
        # real call — this guard is about CODE order, not prose.
        body = "\n".join(ln for ln in src[start:end].splitlines() if not ln.lstrip().startswith("#"))
        fp_pos = body.index("_compute_fingerprint()")
        swap_pos = body.index("tmp.replace(path)")
        assert fp_pos < swap_pos, "fingerprint must be computed before the atomic swap (mint-11 #14)"

    def test_standalone_store_uses_atomic_write(self):
        """#4: the live geez-tewahedo corpus writes must go through atomic_write,
        not bare Path.write_text."""
        src = (REPO / "scripts" / "core" / "standalone_store.py").read_text(encoding="utf-8")
        assert src.count("atomic_write(") >= 3, "all three corpus writes must use atomic_write"
        assert ".write_text(" not in src, "no bare write_text on the corpus store (use atomic_write)"

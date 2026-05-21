"""Tests for the --workers / --cache wiring in the at-scale drivers.

Proves the opt-in additions are correct:
  1. parallel output is byte-identical to serial (parallel_map preserves
     input order, so aggregation is deterministic);
  2. cache + parallelism compose without sqlite cross-thread errors
     (WorkCache is thread-safe).

Uses monkeypatched `iter_target_verses` + a fake detector, so no real KJV
data, no network, no API key.
"""

import json
from types import SimpleNamespace


def _cand(book, ch, v):
    # Shape consumed by candidate_to_dict in both drivers.
    return SimpleNamespace(
        book=book,
        chapter=ch,
        verse=v,
        kind="comm-ai",
        anchor=f"{book}.{ch}.{v}",
        confidence=0.9,
        source_name="x",
        source_attribution="y",
        draft_title="t",
        draft_label="l",
        draft_body="b",
        detector="Fake",
        reviewer_notes="r",
    )


class _FakeDetector:
    def detect(self, book, ch, v, text):
        return [_cand(book, ch, v)]


def _strip_ts(doc):
    doc = dict(doc)
    doc.pop("generated_at", None)
    return doc


def test_run_ai_notes_parallel_output_identical(monkeypatch, tmp_path):
    import scripts.run_ai_notes_at_scale as mod

    fixed = [("jhn", 3, 16, "a"), ("jhn", 3, 17, "b"), ("jhn", 3, 18, "c"), ("rom", 1, 1, "d")]
    monkeypatch.setattr(mod, "iter_target_verses", lambda books, mv: iter(fixed[:mv]))
    df = lambda: _FakeDetector()  # noqa: E731

    d1, d2 = tmp_path / "serial", tmp_path / "par"
    monkeypatch.setattr(mod, "CANDIDATES_DIR", d1)
    s1 = mod.run_ai_notes(["jhn", "rom"], max_verses=10, min_confidence=0.0, model="m", detector_factory=df, workers=1)
    monkeypatch.setattr(mod, "CANDIDATES_DIR", d2)
    s2 = mod.run_ai_notes(["jhn", "rom"], max_verses=10, min_confidence=0.0, model="m", detector_factory=df, workers=4)

    assert s1["verses_processed"] == s2["verses_processed"] == 4
    assert s1["per_book"] == s2["per_book"]
    # written candidate files must be byte-identical (modulo the timestamp)
    names = {p.name for p in d1.glob("*.json")}
    assert names == {p.name for p in d2.glob("*.json")} and names
    for name in names:
        a = _strip_ts(json.loads((d1 / name).read_text(encoding="utf-8")))
        b = _strip_ts(json.loads((d2 / name).read_text(encoding="utf-8")))
        assert a == b, name


def test_run_ai_xrefs_parallel_output_identical(monkeypatch, tmp_path):
    import scripts.run_ai_xrefs_at_scale as mod

    fixed = [("jhn", 3, 16, "a"), ("jhn", 3, 17, "b"), ("rom", 1, 1, "c")]
    monkeypatch.setattr(mod, "iter_target_verses", lambda books, mv: iter(fixed[:mv]))
    df = lambda: _FakeDetector()  # noqa: E731

    d1, d2 = tmp_path / "serial", tmp_path / "par"
    monkeypatch.setattr(mod, "CANDIDATES_DIR", d1)
    s1 = mod.run_ai_xrefs(
        ["jhn", "rom"], max_verses=10, min_confidence=0.0, top_n=3, model="m", detector_factory=df, workers=1
    )
    monkeypatch.setattr(mod, "CANDIDATES_DIR", d2)
    s2 = mod.run_ai_xrefs(
        ["jhn", "rom"], max_verses=10, min_confidence=0.0, top_n=3, model="m", detector_factory=df, workers=4
    )

    assert s1["per_book"] == s2["per_book"]
    assert s1["verses_processed"] == s2["verses_processed"] == 3


def test_parallel_with_cache_no_thread_error(monkeypatch, tmp_path):
    """End-to-end: run_ai_notes with workers>1 AND a shared WorkCache must
    not raise sqlite's 'objects created in a thread...' error."""
    import scripts.run_ai_notes_at_scale as mod
    from scripts.core.detectors import AINoteDetector
    from scripts.core.sources import AnthropicNoteClient
    from scripts.core.work_cache import WorkCache

    fixed = [("jhn", 3, i, f"t{i}") for i in range(1, 9)]
    monkeypatch.setattr(mod, "iter_target_verses", lambda books, mv: iter(fixed[:mv]))
    monkeypatch.setattr(mod, "CANDIDATES_DIR", tmp_path)

    def stub(system, user, *, model):
        # a dict whose verse_anchor won't match -> draft_note returns None ->
        # no candidate; we only care that the cache+threads plumbing is safe
        return {"verse_anchor": "nope"}

    cache = WorkCache(":memory:")
    client = AnthropicNoteClient(model="m", completion_fn=stub, cache=cache)
    df = lambda: AINoteDetector(client=client, min_confidence=0.0)  # noqa: E731

    stats = mod.run_ai_notes(["jhn"], max_verses=10, min_confidence=0.0, model="m", detector_factory=df, workers=4)
    assert stats["verses_processed"] == 8

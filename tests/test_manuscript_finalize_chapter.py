"""Deterministic finalize for the agent-path workflow (P1 of the Sam/Kings cloud plan).

Composes converge + assemble + collate + honesty gate. Synthetic Ge'ez witnesses
(CI-safe; no images, no vision).
"""

from scripts.manuscript_finalize_chapter import finalize_chapter


def _pass(verses):
    return {"verses": verses, "transcription_notes": "t"}


VERSES = [
    {"v": 1, "geez": "ወይቤ ፡ ንጉሥ ፡ ኀበ ፡ ሰብእ", "column": "f126r-A-L1", "line_start": 1, "uncertain": []},
    {"v": 2, "geez": "ወሖረ ፡ ብእሲ ፡ ውስተ ፡ ሀገር", "column": "f126r-A-L4", "line_start": 4, "uncertain": []},
]


def test_finalize_chapter_clean(tmp_path):
    payload = {
        "track": "kings",
        "book": "1ki",
        "chapter": 1,
        "gg": {"a": _pass(VERSES), "b": _pass(VERSES), "source_images": ["g.jpg"], "folios": ["f028v"]},
        "cam": {"a": _pass(VERSES), "b": _pass(VERSES), "source_images": ["c.jpg"], "folios": ["f126r"]},
    }
    res = finalize_chapter(payload, out_dir=str(tmp_path))
    assert res["needs_qa"] is False
    assert res["gg_valid"], res["gg_errors"]
    assert res["cam_valid"], res["cam_errors"]
    assert res["collation_ok"], res["collation_reasons"]
    assert res["gg_convergence_pct"] == 100.0
    assert res["verse_count"] == 2
    assert (tmp_path / "1ki1_witnessGG.json").exists()
    assert (tmp_path / "1ki1_witnessCAM.json").exists()


def test_finalize_flags_qa_on_divergence(tmp_path):
    a = _pass([{"v": 1, "geez": "ወይቤ ፡ ንጉሥ", "column": "c", "line_start": 1, "uncertain": []}])
    b = _pass([{"v": 1, "geez": "ወይቤ ፡ ካህን", "column": "c", "line_start": 1, "uncertain": []}])  # ንጉሥ vs ካህን
    payload = {
        "track": "kings",
        "book": "1ki",
        "chapter": 2,
        "gg": {"a": a, "b": b, "source_images": ["g.jpg"], "folios": ["f"]},
        "cam": {"a": a, "b": a, "source_images": ["c.jpg"], "folios": ["f"]},
    }
    res = finalize_chapter(payload, out_dir=str(tmp_path))
    assert res["needs_qa"] is True  # GG's two passes diverge
    assert res["gg_convergence_pct"] < 100.0
    assert any(loc["v"] == 1 for loc in res["gg_divergent_loci"])

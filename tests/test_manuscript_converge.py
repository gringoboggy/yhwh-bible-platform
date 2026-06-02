"""Convergence gate over two blind transcription passes (model_out dicts).

Drives scripts/core/manuscript_converge.py (P1 of the Sam/Kings cloud plan).
Two verses converge iff their geez tokenizes (manuscript_records._geez_to_tokens)
to fold_skeleton-equal sequences; any divergence flags the chapter needs_qa.
"""

from scripts.core.manuscript_converge import converge_passes


def _mo(verses):
    return {"verses": verses, "transcription_notes": ""}


def test_identical_passes_fully_converge():
    a = _mo([{"v": 1, "geez": "ወይቤ ፡ ንጉሥ", "column": "c", "line_start": 1, "uncertain": []}])
    res = converge_passes(a, a)
    assert res["needs_qa"] is False
    assert res["convergence_pct"] == 100.0
    assert res["identical_pct"] == 100.0
    assert res["accepted"]["verses"][0]["geez"] == "ወይቤ ፡ ንጉሥ"
    assert res["divergent_loci"] == []


def test_token_divergence_flags_qa_and_records_locus():
    a = _mo([{"v": 1, "geez": "ወፈቀደ ፡ ንጉሥ", "column": "c", "line_start": 1, "uncertain": []}])
    b = _mo([{"v": 1, "geez": "ወረቀደ ፡ ንጉሥ", "column": "c", "line_start": 1, "uncertain": []}])  # ፈ→ረ misread
    res = converge_passes(a, b)
    assert res["needs_qa"] is True
    assert any(loc["v"] == 1 for loc in res["divergent_loci"])
    assert res["accepted"]["verses"][0]["geez"] == "ወፈቀደ ፡ ንጉሥ"  # pass A is the draft for divergent verses


def test_verse_only_in_one_pass_is_divergent():
    a = _mo(
        [
            {"v": 1, "geez": "ሀለወ ፡ ብእሲ", "column": "c", "line_start": 1, "uncertain": []},
            {"v": 2, "geez": "ወወለደ ፡ ወልደ", "column": "c", "line_start": 2, "uncertain": []},
        ]
    )
    b = _mo([{"v": 1, "geez": "ሀለወ ፡ ብእሲ", "column": "c", "line_start": 1, "uncertain": []}])
    res = converge_passes(a, b)
    assert res["needs_qa"] is True
    assert any(loc["v"] == 2 for loc in res["divergent_loci"])
    assert res["convergence_pct"] == 50.0  # 1 of 2 verses converge


def test_empty_passes_do_not_divide_by_zero():
    res = converge_passes(_mo([]), _mo([]))
    assert res["needs_qa"] is False
    assert res["convergence_pct"] == 0.0
    assert res["verse_count"] == 0

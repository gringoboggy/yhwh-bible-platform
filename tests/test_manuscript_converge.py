"""Convergence gate over two blind transcription passes (model_out dicts).

Drives scripts/core/manuscript_converge.py (P1 of the Sam/Kings cloud plan).
Two verses converge iff their geez tokenizes (manuscript_records._geez_to_tokens)
to fold_skeleton-equal sequences; any divergence flags the chapter needs_qa.
"""

from scripts.core.manuscript_converge import converge_passes, renumber_verses, sanitize_model_out


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


# ── sanitize_model_out (the fixes the 1Ki1 proof surfaced) ────────────────────


def test_sanitize_strips_rubric_knot():
    mo = _mo([{"v": 1, "geez": "❈ ክፍል ፡ ፪ ወይቤ ፡ ንጉሥ", "column": "c", "line_start": 1, "uncertain": []}])
    s = sanitize_model_out(mo)
    assert "❈" not in s["verses"][0]["geez"]


def test_sanitize_clamps_oob_token_index():
    mo = _mo(
        [
            {
                "v": 1,
                "geez": "ወይቤ ፡ ንጉሥ",
                "column": "c",
                "line_start": 1,
                "uncertain": [{"token_index": 9, "marker": "uncertain", "note": "x"}],
            }
        ]
    )
    s = sanitize_model_out(mo)
    assert s["verses"][0]["uncertain"][0]["token_index"] == 1  # 2 tokens → clamped to 1


def test_sanitize_downgrades_orphan_illegible():
    mo = _mo(
        [
            {
                "v": 1,
                "geez": "ወይቤ ፡ ንጉሥ",
                "column": "c",
                "line_start": 1,
                "uncertain": [{"token_index": 0, "marker": "illegible", "note": "faded"}],
            }
        ]
    )
    s = sanitize_model_out(mo)
    assert s["verses"][0]["uncertain"][0]["marker"] == "damaged"


def test_sanitize_keeps_real_illegible():
    mo = _mo(
        [
            {
                "v": 1,
                "geez": "ወይቤ ፡ ⟦illegible⟧",
                "column": "c",
                "line_start": 1,
                "uncertain": [{"token_index": 1, "marker": "illegible", "note": "lacuna"}],
            }
        ]
    )
    s = sanitize_model_out(mo)
    assert s["verses"][0]["uncertain"][0]["marker"] == "illegible"


def test_sanitized_output_validates():
    """The exact 1Ki1 failure mode (❈ + OOB index + orphan illegible) → after
    sanitize + assemble, validate_witness passes."""
    from scripts.core.manuscript_records import validate_witness
    from scripts.run_manuscript_transcribe_at_scale import assemble_witness

    mo = _mo(
        [
            {
                "v": 1,
                "geez": "❈ ክፍል ፡ ፪ ወይቤ ፡ ንጉሥ",
                "column": "c",
                "line_start": 1,
                "uncertain": [{"token_index": 12, "marker": "illegible", "note": "x"}],
            },
            {"v": 2, "geez": "ወሖረ ፡ ብእሲ", "column": "c", "line_start": 2, "uncertain": []},
        ]
    )
    s = sanitize_model_out(mo)
    rec = assemble_witness(s, book="1ki", chapter=1, witness_sig="GG", source_images=["g.jpg"], folio_sigla=["f028v"])
    ok, errs = validate_witness(rec)
    assert ok, errs


def test_renumber_makes_contiguous():
    mo = _mo(
        [
            {"v": 1, "geez": "ሀ", "column": "c", "line_start": 1, "uncertain": []},
            {"v": 2, "geez": "ለ", "column": "c", "line_start": 2, "uncertain": []},
            {"v": 4, "geez": "ሐ", "column": "c", "line_start": 3, "uncertain": []},  # gap at 3
        ]
    )
    r = renumber_verses(mo)
    assert [v["v"] for v in r["verses"]] == [1, 2, 3]
    assert [v["geez"] for v in r["verses"]] == ["ሀ", "ለ", "ሐ"]  # content/order preserved


def test_converge_accepted_is_contiguous():
    a = _mo(
        [
            {"v": 1, "geez": "ሀ", "column": "c", "line_start": 1, "uncertain": []},
            {"v": 5, "geez": "ለ", "column": "c", "line_start": 2, "uncertain": []},  # jump in numbering
        ]
    )
    res = converge_passes(a, a)
    assert [v["v"] for v in res["accepted"]["verses"]] == [1, 2]

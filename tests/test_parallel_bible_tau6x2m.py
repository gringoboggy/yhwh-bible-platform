"""τ.6.x.2.m — Geʽez Esther full-book ingest pins (2026-05-16).

TWELFTH Geʽez per-book ingest (geez-tewahedo/) and the FOURTH Geʽez
deuterocanonical-block ingest. CONTINUES the post-Psalms Geʽez
deuterocanon-catchup sub-arc (2es τ.6.x.2.j → tob τ.6.x.2.k → jdt
τ.6.x.2.l → est τ.6.x.2.m). Pipeline reused VERBATIM from the
Amharic τ.7.x.m ship (same PDF page range p1308-1317, same
ESTHER_VERSE_COUNTS renumber-floor, same structural_map.esther
block) — the ONLY delta is the `--lang geez` column flip
(zero-parser-API-delta).

content/books.yaml fixes `est` at ch_count: 10 — the Hebrew/
Masoretic protocanonical Esther core (the Greek Additions are the
SEPARATE `b25` book, NOT this floor). Coverage is honestly 82.6%
(138/167) at ocr-tier3 — ABOVE the τ.6.x.2.a-h Geʽez band (53-67%)
because Esther is a short book whose dense narrative OCR'd
relatively well; still a clean renumber UNDERFLOW (138 < 167): ch
1-8 fill exactly (cumulative floor = 132), ch 9 partial (6/32), ch
10 empty, no overflow. The Geʽez column recovered slightly more
than Amharic for this book (138 vs the τ.7.x.m 133) —
region/book-dependent at ocr-tier3, reconciled at the τ.6.x.3
batched audit per the τ.6.x.0b honesty contract. The two columns
extract DISTINCT text (verified at ship — not a misattribution
bug).

Per memory `feedback_share_pin_pattern` the deuterocanon-progress
pin here is written POSITIVE/MONOTONIC from the start (asserts what
HAS shipped + an absolute monotone counter) — it never enumerates
the forward not-yet-shipped frontier (that anti-pattern broke the
tau6x2j pin at the τ.6.x.2.l ship and was root-caused there).

Pins validate:
1. ESTHER_VERSE_COUNTS reused UNCHANGED (zero-parser-API-delta).
2. structural_map.esther reused UNCHANGED (verified at τ.7.x.m).
3. geez-tewahedo/est.py module shape + INGEST_PHASE τ.6.x.2.m.
4. Per-chapter coverage (1-8 full; 9 partial; 10 empty; no overflow).
5. geez _meta.yaml ingest_record_tau6x2m + stats (13 books, 4 deutero).
6. _source.yaml ocr_strategy.tau6x2m_ingest block.
7. Cross-column coherence: tau7xm_ingest geez slot-state updated.
8. Amharic τ.7.x.m stream + the τ.6.x.2.a-l Geʽez arc preserved.
9. State-docs (CHANGELOG/SESSION_STATE/IN_FLIGHT/PLAN) record τ.6.x.2.m.
"""

from __future__ import annotations

import ast
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SOURCE_YAML = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
GEEZ_TEWAHEDO = REPO / "content" / "translations" / "geez-tewahedo"
AMHARIC_TEWAHEDO = REPO / "content" / "translations" / "amharic-tewahedo"


def _source_yaml() -> dict:
    return yaml.safe_load(SOURCE_YAML.read_text(encoding="utf-8"))


def _geez_meta() -> dict:
    return yaml.safe_load((GEEZ_TEWAHEDO / "_meta.yaml").read_text(encoding="utf-8"))


def _verses(translation_dir: Path, book: str) -> list[tuple]:
    py = translation_dir / f"{book}.py"
    tree = ast.parse(py.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSES":
                    return ast.literal_eval(node.value)
    raise AssertionError(f"{translation_dir.name}/{book}.py must define VERSES")


def _constants(translation_dir: Path, book: str) -> dict:
    py = translation_dir / f"{book}.py"
    tree = ast.parse(py.read_text(encoding="utf-8"))
    out: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id != "VERSES":
                    try:
                        out[target.id] = ast.literal_eval(node.value)
                    except Exception:
                        pass
    return out


def _by_chapter(translation_dir: Path, book: str) -> dict[int, list[tuple]]:
    out: dict[int, list[tuple]] = {}
    for ch, v, t in _verses(translation_dir, book):
        out.setdefault(ch, []).append((v, t))
    return out


# ───────────────────────────── floor dict ──────────────────────────


class TestTau6X2MEstherVerseCountsReusedUnchanged:
    """ESTHER_VERSE_COUNTS was added at the Amharic τ.7.x.m ship and is
    reused VERBATIM for the Geʽez column — zero-parser-API-delta."""

    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_module_symbol_present(self):
        from extract_parallel_pdf import ESTHER_VERSE_COUNTS

        assert isinstance(ESTHER_VERSE_COUNTS, dict)

    def test_ten_chapters(self):
        from extract_parallel_pdf import ESTHER_VERSE_COUNTS

        assert sorted(ESTHER_VERSE_COUNTS.keys()) == list(range(1, 11))

    def test_total_verses_167(self):
        from extract_parallel_pdf import ESTHER_VERSE_COUNTS

        assert sum(ESTHER_VERSE_COUNTS.values()) == 167

    def test_chapters_1_through_8_sum_to_132(self):
        """The τ.6.x.2.m boundary: 138 extracted Geʽez verses renumber
        to fill ch 1-8 (cumulative floor = 132) + ch 9 partial (6/32)
        + ch 10 empty."""
        from extract_parallel_pdf import ESTHER_VERSE_COUNTS

        assert sum(ESTHER_VERSE_COUNTS[c] for c in range(1, 9)) == 132

    def test_books_yaml_est_ch_count_10(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "est")
        assert rec["ch_count"] == 10


# ─────────────────────────── structural_map ────────────────────────


class TestTau6X2MStructuralMapEstherReusedUnchanged:
    """structural_map.esther was verified at the Amharic τ.7.x.m ship;
    the Geʽez column reuses it UNCHANGED (same parallel PDF)."""

    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["esther"]

    def test_block_present(self):
        assert "esther" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["est"]

    def test_pdf_page_range_1308_1317(self):
        assert self._blk()["pdf_page_range"] == [1308, 1317]

    def test_verified_at_tau7xm_not_re_verified_at_tau6x2m(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.m"

    def test_chapter_count_expected_10(self):
        assert self._blk()["chapter_count_expected"] == 10


# ──────────────────────────── output module ────────────────────────


class TestTau6X2MEstPy:
    def test_est_py_exists(self):
        assert (GEEZ_TEWAHEDO / "est.py").is_file()

    def test_translation_and_book_constants(self):
        c = _constants(GEEZ_TEWAHEDO, "est")
        assert c.get("TRANSLATION") == "geez-tewahedo"
        assert c.get("BOOK") == "est"

    def test_source_quality_ocr_tier3(self):
        assert _constants(GEEZ_TEWAHEDO, "est").get("SOURCE_QUALITY") == "ocr-tier3"

    def test_source_provenance(self):
        assert _constants(GEEZ_TEWAHEDO, "est").get("SOURCE_PROVENANCE") == "parallel-bible-eotc"

    def test_ingest_phase_tau6x2m(self):
        assert _constants(GEEZ_TEWAHEDO, "est").get("INGEST_PHASE") == "τ.6.x.2.m"

    def test_geez_est_total_verse_count_floor(self):
        # Empirical at ship: 138. Floor 125 guards regression while
        # permitting parser refinement.
        verses = _verses(GEEZ_TEWAHEDO, "est")
        assert len(verses) >= 125, f"τ.6.x.2.m Geʽez Esther must have ≥125 verses; got {len(verses)}"

    def test_first_verse_is_est_1_1(self):
        ch, v, text = _verses(GEEZ_TEWAHEDO, "est")[0]
        assert (ch, v) == (1, 1)
        assert text

    def test_geez_text_distinct_from_amharic_column(self):
        geez_first = _verses(GEEZ_TEWAHEDO, "est")[0][2]
        amh_first = _verses(AMHARIC_TEWAHEDO, "est")[0][2]
        assert geez_first != amh_first, "Geʽez est[1:1] must differ from Amharic est[1:1]"


# ─────────────────────────── coverage shape ────────────────────────


class TestTau6X2MEstCoverage:
    """Renumber UNDERFLOW: ch 1-8 fully populated (cumulative floor =
    132); ch 9 partial (6/32 — 138-132); ch 10 empty; no overflow."""

    def test_geez_est_chapters_1_through_8_fully_populated(self):
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import ESTHER_VERSE_COUNTS

        by_ch = _by_chapter(GEEZ_TEWAHEDO, "est")
        for ch in range(1, 9):
            got = len(by_ch.get(ch, []))
            exp = ESTHER_VERSE_COUNTS[ch]
            assert got == exp, f"τ.6.x.2.m est ch {ch} must have exactly {exp} verses; got {got}"

    def test_geez_est_chapter_9_partial(self):
        by_ch = _by_chapter(GEEZ_TEWAHEDO, "est")
        got = len(by_ch.get(9, []))
        assert 1 <= got < 32, f"τ.6.x.2.m est ch 9 partial expected (1..31); got {got}"

    def test_geez_est_chapter_10_empty(self):
        by_ch = _by_chapter(GEEZ_TEWAHEDO, "est")
        assert len(by_ch.get(10, [])) == 0, "τ.6.x.2.m est ch 10 should be empty at ocr-tier3"

    def test_geez_est_no_overflow_above_chapter_10(self):
        by_ch = _by_chapter(GEEZ_TEWAHEDO, "est")
        overflow = sum(len(v) for ch, v in by_ch.items() if ch > 10)
        assert overflow == 0, f"τ.6.x.2.m renumber overflow should be 0; got {overflow} above ch 10"


# ───────────────────── _source.yaml ingest block ───────────────────


class TestTau6X2MSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau6x2m_ingest"]

    def test_block_exists(self):
        assert "tau6x2m_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.6.x.2.m"

    def test_helpers_reused_not_added(self):
        reused = self._blk()["helpers_reused"]
        assert "ESTHER_VERSE_COUNTS" in reused
        assert "structural_map.esther" in reused

    def test_empirical_validation_coverage(self):
        ev = self._blk()["empirical_validation"]
        assert ev["coverage_pct"] == 82.6
        assert ev["renumbered_verse_count"] == 138
        assert ev["extraction_engine"] == "text-layer"
        assert ev["pdf_pages_consumed"] == [1308, 1317]

    def test_no_ingest_false(self):
        assert self._blk()["no_ingest_at_this_phase"] is False

    def test_arc_context_geez_deuterocanon_catchup_continue(self):
        assert self._blk()["arc_context"] == "geez-deuterocanon-catchup-continue"

    def test_closed_arc_tau7xa_through_tau7xm_preserved(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        for letter in "abcdefghijklm":
            assert contracts.get(f"tau7x{letter}_ingest") is True, f"tau7x{letter} must be preserved"

    def test_closed_arc_geez_through_tau6x2l_preserved(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        for letter in "abcdefgh":
            assert contracts.get(f"tau6x2{letter}_ingest") is True
        for letter in "ijkl":
            assert contracts.get(f"tau6x2{letter}_ingest") is True, f"τ.6.x.2.{letter} must be preserved"

    def test_next_phase_tau6x2n(self):
        assert self._blk()["next_phase"] == "τ.6.x.2.n"


# ─────────────────── cross-column coherence (tau7xm) ────────────────


class TestTau6X2MCrossColumnCoherence:
    """Shipping τ.6.x.2.m updates tau7xm_ingest's geez_tewahedo_est
    slot no-op→shipped + adds the geez-catchup back-link, WITHOUT
    touching pipeline_reused_at_phase (= τ.7.x.n, pinned elsewhere)."""

    def _tau7xm(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xm_ingest"]

    def test_tau7xm_geez_slot_state_updated_to_shipped(self):
        slot = self._tau7xm()["translation_slot_state"]["geez_tewahedo_est"]
        assert "shipped-at-τ.6.x.2.m" in slot
        assert "no-op" not in slot

    def test_tau7xm_geez_catchup_back_link_added(self):
        assert self._tau7xm().get("geez_catchup_reused_at_phase") == "τ.6.x.2.m"

    def test_tau7xm_pipeline_reused_at_phase_still_tau7xn(self):
        assert self._tau7xm()["pipeline_reused_at_phase"] == "τ.7.x.n"


# ─────────────────────── geez _meta.yaml record ────────────────────


class TestTau6X2MGeezMetaYaml:
    def test_stats_books_at_least_thirteen(self):
        assert _geez_meta()["stats"]["books"] >= 13

    def test_stats_verses_at_least_7927(self):
        # 7789 (post-τ.6.x.2.l) + 138 (est) = 7927.
        assert _geez_meta()["stats"]["verses"] >= 7927

    def test_stats_books_outside_kjv_at_least_four(self):
        """2es + tob + jdt + est — the Hebrew/Masoretic Esther core
        sits outside the 66-book KJV canon in the Tewahedo ordering
        (sourced from the EOTC-parallel block, the τ.7.x.m precedent)."""
        assert _geez_meta()["stats"]["books_outside_kjv"] >= 4

    def test_ingest_record_tau6x2m(self):
        rec = _geez_meta()["ingest_record_tau6x2m"]
        assert rec["phase"] == "τ.6.x.2.m"
        assert rec["ingested_book_codes"] == ["est"]
        assert rec["engine"] == "text-layer"
        assert rec["coverage"]["verses_extracted"] == 138
        assert rec["coverage"]["coverage_pct"] == 82.6
        assert rec["audit_handoff"] == "τ.6.x.3"

    def test_prior_geez_ingest_records_still_present(self):
        m = _geez_meta()
        for letter in "abcdefgh":
            assert f"ingest_record_tau6x2{letter}" in m, f"prior geez ingest record missing: {letter}"
        for letter in "ijkl":
            assert f"ingest_record_tau6x2{letter}" in m, f"τ.6.x.2.{letter} record must persist"


# ─────────────────── prior-arc invariants preserved ────────────────


class TestTau6X2MPriorArcsPreserved:
    def test_amharic_est_preserved(self):
        assert (AMHARIC_TEWAHEDO / "est.py").is_file()
        assert _constants(AMHARIC_TEWAHEDO, "est").get("INGEST_PHASE") == "τ.7.x.m"

    def test_geez_2es_tob_jdt_preserved(self):
        """τ.6.x.2.j/k/l must persist (additive ship)."""
        assert _constants(GEEZ_TEWAHEDO, "2es").get("INGEST_PHASE") == "τ.6.x.2.j"
        assert _constants(GEEZ_TEWAHEDO, "tob").get("INGEST_PHASE") == "τ.6.x.2.k"
        assert _constants(GEEZ_TEWAHEDO, "jdt").get("INGEST_PHASE") == "τ.6.x.2.l"

    def test_geez_8book_narrative_arc_preserved(self):
        for book in ("gen", "ex", "lev", "num", "deu", "jos", "jdg", "rut"):
            assert (GEEZ_TEWAHEDO / f"{book}.py").is_file(), f"τ.6.x.2.a-h Geʽez {book} must persist"

    def test_geez_psalms_hacohen_preserved(self):
        assert _constants(GEEZ_TEWAHEDO, "psa").get("INGEST_PHASE") == "τ.6.x.2.i"

    def test_geez_est_is_a_durable_deuterocanon_milestone(self):
        """ABSOLUTE/POSITIVE milestone-pin (memory
        `feedback_share_pin_pattern`) — written durable from the
        start (no forward not-yet-shipped enumeration; that anti-
        pattern broke the tau6x2j equivalent at the τ.6.x.2.l ship
        and was root-caused there). τ.6.x.2.m shipped Geʽez Esther
        (the FOURTH Geʽez deuterocanon-block book); the count only
        grows — never asserts what has NOT yet shipped."""
        assert (GEEZ_TEWAHEDO / "est.py").is_file(), "τ.6.x.2.m est must remain shipped"
        assert _geez_meta()["stats"]["books_outside_kjv"] >= 4, (
            "τ.6.x.2.m established ≥4 Geʽez deuterocanon books (2es+tob+jdt+est; monotonic)"
        )


# ───────────────────────────── state docs ──────────────────────────


class TestTau6X2MStateDocs:
    def test_changelog_records_tau6x2m(self):
        txt = (REPO / "dev" / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "τ.6.x.2.m" in txt

    def test_session_state_mentions_tau6x2m(self):
        txt = (REPO / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
        assert "τ.6.x.2.m" in txt

    def test_in_flight_mentions_tau6x2m(self):
        txt = (REPO / "dev" / "IN_FLIGHT.md").read_text(encoding="utf-8")
        assert "τ.6.x.2.m" in txt

    def test_plan_ledger_records_tau6x2m(self):
        txt = (REPO / "dev" / "PLAN_2026-05-09.md").read_text(encoding="utf-8")
        assert "τ.6.x.2.m" in txt

"""τ.6.x.2.l — Geʽez Judith full-book ingest pins (2026-05-16).

ELEVENTH Geʽez per-book ingest (geez-tewahedo/) and the THIRD Geʽez
deuterocanonical ingest. CONTINUES the post-Psalms Geʽez
deuterocanon-catchup sub-arc (2es τ.6.x.2.j → tob τ.6.x.2.k → jdt
τ.6.x.2.l). Pipeline reused VERBATIM from the Amharic τ.7.x.l ship
(same PDF page range p1294-1307, same JUDITH_VERSE_COUNTS
renumber-floor, same structural_map.judith block) — the ONLY delta
is the `--lang geez` column flip (zero-parser-API-delta).

Coverage is honestly 54.9% (186/339) at ocr-tier3 — in the
τ.6.x.2.a-h Geʽez band (53-67%). Clean renumber UNDERFLOW (186 <
339): ch 1-8 fill exactly (cumulative floor = 182), ch 9 partial
(4/14), ch 10-16 empty, no overflow. The Geʽez column recovered
MORE than Amharic for this book (186 vs the τ.7.x.l 120) —
region/book-dependent at ocr-tier3, reconciled at the τ.6.x.3
batched audit per the τ.6.x.0b honesty contract. The two columns
extract DISTINCT text (verified at ship — not a misattribution
bug).

Pins validate:
1. JUDITH_VERSE_COUNTS reused UNCHANGED (zero-parser-API-delta).
2. structural_map.judith reused UNCHANGED (verified at τ.7.x.l).
3. geez-tewahedo/jdt.py module shape + INGEST_PHASE τ.6.x.2.l.
4. Per-chapter coverage (1-8 full; 9 partial; 10-16 empty; no overflow).
5. geez _meta.yaml ingest_record_tau6x2l + stats (12 books, 3 deutero).
6. _source.yaml ocr_strategy.tau6x2l_ingest block.
7. Cross-column coherence: tau7xl_ingest geez slot-state updated.
8. Amharic τ.7.x.l stream + the τ.6.x.2.a-k Geʽez arc preserved.
9. State-docs (CHANGELOG/SESSION_STATE/IN_FLIGHT/PLAN) record τ.6.x.2.l.
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


class TestTau6X2LJudithVerseCountsReusedUnchanged:
    """JUDITH_VERSE_COUNTS was added at the Amharic τ.7.x.l ship and is
    reused VERBATIM for the Geʽez column — zero-parser-API-delta."""

    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_module_symbol_present(self):
        from extract_parallel_pdf import JUDITH_VERSE_COUNTS

        assert isinstance(JUDITH_VERSE_COUNTS, dict)

    def test_sixteen_chapters(self):
        from extract_parallel_pdf import JUDITH_VERSE_COUNTS

        assert sorted(JUDITH_VERSE_COUNTS.keys()) == list(range(1, 17))

    def test_total_verses_339(self):
        from extract_parallel_pdf import JUDITH_VERSE_COUNTS

        assert sum(JUDITH_VERSE_COUNTS.values()) == 339

    def test_chapters_1_through_8_sum_to_182(self):
        """The τ.6.x.2.l boundary: 186 extracted Geʽez verses renumber
        to fill ch 1-8 (cumulative floor = 182) + ch 9 partial (4/14)
        + ch 10-16 empty."""
        from extract_parallel_pdf import JUDITH_VERSE_COUNTS

        assert sum(JUDITH_VERSE_COUNTS[c] for c in range(1, 9)) == 182


# ─────────────────────────── structural_map ────────────────────────


class TestTau6X2LStructuralMapJudithReusedUnchanged:
    """structural_map.judith was verified at the Amharic τ.7.x.l ship;
    the Geʽez column reuses it UNCHANGED (same parallel PDF)."""

    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["judith"]

    def test_block_present(self):
        assert "judith" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["jdt"]

    def test_pdf_page_range_1294_1307(self):
        assert self._blk()["pdf_page_range"] == [1294, 1307]

    def test_verified_at_tau7xl_not_re_verified_at_tau6x2l(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.l"

    def test_chapter_count_expected_16(self):
        assert self._blk()["chapter_count_expected"] == 16


# ──────────────────────────── output module ────────────────────────


class TestTau6X2LJdtPy:
    def test_jdt_py_exists(self):
        assert (GEEZ_TEWAHEDO / "jdt.py").is_file()

    def test_translation_and_book_constants(self):
        c = _constants(GEEZ_TEWAHEDO, "jdt")
        assert c.get("TRANSLATION") == "geez-tewahedo"
        assert c.get("BOOK") == "jdt"

    def test_source_quality_ocr_tier3(self):
        assert _constants(GEEZ_TEWAHEDO, "jdt").get("SOURCE_QUALITY") == "ocr-tier3"

    def test_source_provenance(self):
        assert _constants(GEEZ_TEWAHEDO, "jdt").get("SOURCE_PROVENANCE") == "parallel-bible-eotc"

    def test_ingest_phase_tau6x2l(self):
        assert _constants(GEEZ_TEWAHEDO, "jdt").get("INGEST_PHASE") == "τ.6.x.2.l"

    def test_geez_jdt_total_verse_count_floor(self):
        # Empirical at ship: 186. Floor 170 guards regression while
        # permitting parser refinement.
        verses = _verses(GEEZ_TEWAHEDO, "jdt")
        assert len(verses) >= 170, f"τ.6.x.2.l Geʽez Judith must have ≥170 verses; got {len(verses)}"

    def test_first_verse_is_jdt_1_1(self):
        ch, v, text = _verses(GEEZ_TEWAHEDO, "jdt")[0]
        assert (ch, v) == (1, 1)
        assert text

    def test_geez_text_distinct_from_amharic_column(self):
        geez_first = _verses(GEEZ_TEWAHEDO, "jdt")[0][2]
        amh_first = _verses(AMHARIC_TEWAHEDO, "jdt")[0][2]
        assert geez_first != amh_first, "Geʽez jdt[1:1] must differ from Amharic jdt[1:1]"


# ─────────────────────────── coverage shape ────────────────────────


class TestTau6X2LJdtCoverage:
    """Renumber UNDERFLOW: ch 1-8 fully populated (cumulative floor =
    182); ch 9 partial (4/14 — 186-182); ch 10-16 empty; no overflow."""

    def test_geez_jdt_chapters_1_through_8_fully_populated(self):
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import JUDITH_VERSE_COUNTS

        by_ch = _by_chapter(GEEZ_TEWAHEDO, "jdt")
        for ch in range(1, 9):
            got = len(by_ch.get(ch, []))
            exp = JUDITH_VERSE_COUNTS[ch]
            assert got == exp, f"τ.6.x.2.l jdt ch {ch} must have exactly {exp} verses; got {got}"

    def test_geez_jdt_chapter_9_partial(self):
        by_ch = _by_chapter(GEEZ_TEWAHEDO, "jdt")
        got = len(by_ch.get(9, []))
        assert 1 <= got < 14, f"τ.6.x.2.l jdt ch 9 partial expected (1..13); got {got}"

    def test_geez_jdt_chapters_10_through_16_empty(self):
        by_ch = _by_chapter(GEEZ_TEWAHEDO, "jdt")
        for ch in range(10, 17):
            assert len(by_ch.get(ch, [])) == 0, f"τ.6.x.2.l jdt ch {ch} should be empty at ocr-tier3"

    def test_geez_jdt_no_overflow_above_chapter_16(self):
        by_ch = _by_chapter(GEEZ_TEWAHEDO, "jdt")
        overflow = sum(len(v) for ch, v in by_ch.items() if ch > 16)
        assert overflow == 0, f"τ.6.x.2.l renumber overflow should be 0; got {overflow} above ch 16"


# ───────────────────── _source.yaml ingest block ───────────────────


class TestTau6X2LSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau6x2l_ingest"]

    def test_block_exists(self):
        assert "tau6x2l_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.6.x.2.l"

    def test_helpers_reused_not_added(self):
        reused = self._blk()["helpers_reused"]
        assert "JUDITH_VERSE_COUNTS" in reused
        assert "structural_map.judith" in reused

    def test_empirical_validation_coverage(self):
        ev = self._blk()["empirical_validation"]
        assert ev["coverage_pct"] == 54.9
        assert ev["renumbered_verse_count"] == 186
        assert ev["extraction_engine"] == "text-layer"
        assert ev["pdf_pages_consumed"] == [1294, 1307]

    def test_no_ingest_false(self):
        assert self._blk()["no_ingest_at_this_phase"] is False

    def test_arc_context_geez_deuterocanon_catchup_continue(self):
        assert self._blk()["arc_context"] == "geez-deuterocanon-catchup-continue"

    def test_closed_arc_tau7xa_through_tau7xm_preserved(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        for letter in "abcdefghijklm":
            assert contracts.get(f"tau7x{letter}_ingest") is True, f"tau7x{letter} must be preserved"

    def test_closed_arc_geez_through_tau6x2k_preserved(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        for letter in "abcdefgh":
            assert contracts.get(f"tau6x2{letter}_ingest") is True
        for letter in "ijk":
            assert contracts.get(f"tau6x2{letter}_ingest") is True, f"τ.6.x.2.{letter} must be preserved"

    def test_next_phase_tau6x2m(self):
        assert self._blk()["next_phase"] == "τ.6.x.2.m"


# ─────────────────── cross-column coherence (tau7xl) ────────────────


class TestTau6X2LCrossColumnCoherence:
    """Shipping τ.6.x.2.l updates tau7xl_ingest's geez_tewahedo_jdt
    slot no-op→shipped + adds the geez-catchup back-link, WITHOUT
    touching pipeline_reused_at_phase (= τ.7.x.m, pinned elsewhere)."""

    def _tau7xl(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xl_ingest"]

    def test_tau7xl_geez_slot_state_updated_to_shipped(self):
        slot = self._tau7xl()["translation_slot_state"]["geez_tewahedo_jdt"]
        assert "shipped-at-τ.6.x.2.l" in slot
        assert "no-op" not in slot

    def test_tau7xl_geez_catchup_back_link_added(self):
        assert self._tau7xl().get("geez_catchup_reused_at_phase") == "τ.6.x.2.l"

    def test_tau7xl_pipeline_reused_at_phase_still_tau7xm(self):
        assert self._tau7xl()["pipeline_reused_at_phase"] == "τ.7.x.m"


# ─────────────────────── geez _meta.yaml record ────────────────────


class TestTau6X2LGeezMetaYaml:
    def test_stats_books_at_least_twelve(self):
        assert _geez_meta()["stats"]["books"] >= 12

    def test_stats_verses_at_least_7789(self):
        # 7603 (post-τ.6.x.2.k) + 186 (jdt) = 7789.
        assert _geez_meta()["stats"]["verses"] >= 7789

    def test_stats_books_outside_kjv_at_least_three(self):
        """2es + tob + jdt are all deuterocanonical."""
        assert _geez_meta()["stats"]["books_outside_kjv"] >= 3

    def test_ingest_record_tau6x2l(self):
        rec = _geez_meta()["ingest_record_tau6x2l"]
        assert rec["phase"] == "τ.6.x.2.l"
        assert rec["ingested_book_codes"] == ["jdt"]
        assert rec["engine"] == "text-layer"
        assert rec["coverage"]["verses_extracted"] == 186
        assert rec["coverage"]["coverage_pct"] == 54.9
        assert rec["audit_handoff"] == "τ.6.x.3"

    def test_prior_geez_ingest_records_still_present(self):
        m = _geez_meta()
        for letter in "abcdefgh":
            assert f"ingest_record_tau6x2{letter}" in m, f"prior geez ingest record missing: {letter}"
        for letter in "ijk":
            assert f"ingest_record_tau6x2{letter}" in m, f"τ.6.x.2.{letter} record must persist"


# ─────────────────── prior-arc invariants preserved ────────────────


class TestTau6X2LPriorArcsPreserved:
    def test_amharic_jdt_preserved(self):
        assert (AMHARIC_TEWAHEDO / "jdt.py").is_file()
        assert _constants(AMHARIC_TEWAHEDO, "jdt").get("INGEST_PHASE") == "τ.7.x.l"

    def test_geez_2es_tob_preserved(self):
        """τ.6.x.2.j 2es + τ.6.x.2.k tob must persist (additive ship)."""
        assert _constants(GEEZ_TEWAHEDO, "2es").get("INGEST_PHASE") == "τ.6.x.2.j"
        assert _constants(GEEZ_TEWAHEDO, "tob").get("INGEST_PHASE") == "τ.6.x.2.k"

    def test_geez_8book_narrative_arc_preserved(self):
        for book in ("gen", "ex", "lev", "num", "deu", "jos", "jdg", "rut"):
            assert (GEEZ_TEWAHEDO / f"{book}.py").is_file(), f"τ.6.x.2.a-h Geʽez {book} must persist"

    def test_geez_psalms_hacohen_preserved(self):
        assert _constants(GEEZ_TEWAHEDO, "psa").get("INGEST_PHASE") == "τ.6.x.2.i"

    def test_geez_jdt_is_a_durable_deuterocanon_milestone(self):
        """ABSOLUTE/POSITIVE milestone-pin (memory
        `feedback_share_pin_pattern`) — written durable from the
        start (no forward not-yet-shipped enumeration; that anti-
        pattern broke the tau6x2j equivalent at this very ship).
        τ.6.x.2.l shipped Geʽez Judith (the THIRD Geʽez
        deuterocanonical book); the count only grows."""
        assert (GEEZ_TEWAHEDO / "jdt.py").is_file(), "τ.6.x.2.l jdt must remain shipped"
        assert _geez_meta()["stats"]["books_outside_kjv"] >= 3, (
            "τ.6.x.2.l established ≥3 Geʽez deuterocanon books (2es+tob+jdt; monotonic)"
        )


# ───────────────────────────── state docs ──────────────────────────


class TestTau6X2LStateDocs:
    # Doc-pins collapsed to the CHANGELOG chokepoint (2026-05-21): the
    # old test_session_state_*/test_in_flight_*/test_plan_ledger_* pins
    # read SESSION_STATE.md / IN_FLIGHT.md (rolling, trimmed) and the
    # moved PLAN_2026-05-09.md. The durable phase record is CHANGELOG.md.
    def test_phase_recorded_in_changelog(self):
        from tests.fixtures import assert_phase_recorded

        assert_phase_recorded("τ.6.x.2.l")

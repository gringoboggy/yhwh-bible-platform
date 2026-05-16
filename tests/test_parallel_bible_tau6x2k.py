"""τ.6.x.2.k — Geʽez Tobit full-book ingest pins (2026-05-16).

TENTH Geʽez per-book ingest (geez-tewahedo/) and the SECOND Geʽez
deuterocanonical ingest. CONTINUES the post-Psalms Geʽez
deuterocanon-catchup sub-arc opened at τ.6.x.2.j (2 Esdras);
together τ.6.x.2.j + τ.6.x.2.k drain the Geʽez column of the
p1239-1293 EOTC-parallel block (mirroring the Amharic τ.7.x.j +
τ.7.x.k pair). Pipeline reused VERBATIM from the Amharic τ.7.x.k
ship (same PDF page range p1285-1293, same TOBIT_VERSE_COUNTS
renumber-floor, same structural_map.tobit block) — the ONLY delta
is the `--lang geez` column flip (zero-parser-API-delta).

Coverage is honestly 54.5% (134/246) at ocr-tier3 — in the
τ.6.x.2.a-h Geʽez band (53-67%). Clean renumber UNDERFLOW (134 <
246): ch 1-7 fill exactly (cumulative floor = 131), ch 8 partial
(3/21), ch 9-14 empty, no overflow. The Geʽez column recovered
MORE than Amharic for this book (134 vs the τ.7.x.k 118) —
region/book-dependent at ocr-tier3, reconciled at the τ.6.x.3
batched audit per the τ.6.x.0b honesty contract. The two columns
extract DISTINCT text (verified at ship — not a misattribution
bug).

Pins validate:
1. TOBIT_VERSE_COUNTS reused UNCHANGED (zero-parser-API-delta).
2. structural_map.tobit reused UNCHANGED (verified at τ.7.x.k).
3. geez-tewahedo/tob.py module shape + INGEST_PHASE τ.6.x.2.k.
4. Per-chapter coverage (1-7 full; 8 partial; 9-14 empty; no overflow).
5. geez _meta.yaml ingest_record_tau6x2k + stats (11 books, 2 deutero).
6. _source.yaml ocr_strategy.tau6x2k_ingest block.
7. Cross-column coherence: tau7xk_ingest geez slot-state updated.
8. Amharic τ.7.x.k stream + the τ.6.x.2.a-j Geʽez arc preserved.
9. State-docs (CHANGELOG/SESSION_STATE/IN_FLIGHT/PLAN) record τ.6.x.2.k.
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


class TestTau6X2KTobitVerseCountsReusedUnchanged:
    """TOBIT_VERSE_COUNTS was added at the Amharic τ.7.x.k ship and is
    reused VERBATIM for the Geʽez column — zero-parser-API-delta."""

    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_module_symbol_present(self):
        from extract_parallel_pdf import TOBIT_VERSE_COUNTS

        assert isinstance(TOBIT_VERSE_COUNTS, dict)

    def test_fourteen_chapters(self):
        from extract_parallel_pdf import TOBIT_VERSE_COUNTS

        assert sorted(TOBIT_VERSE_COUNTS.keys()) == list(range(1, 15))

    def test_total_verses_246(self):
        from extract_parallel_pdf import TOBIT_VERSE_COUNTS

        assert sum(TOBIT_VERSE_COUNTS.values()) == 246

    def test_chapters_1_through_7_sum_to_131(self):
        """The τ.6.x.2.k boundary: 134 extracted Geʽez verses renumber
        to fill ch 1-7 (cumulative floor = 131) + ch 8 partial (3/21)
        + ch 9-14 empty."""
        from extract_parallel_pdf import TOBIT_VERSE_COUNTS

        assert sum(TOBIT_VERSE_COUNTS[c] for c in range(1, 8)) == 131


# ─────────────────────────── structural_map ────────────────────────


class TestTau6X2KStructuralMapTobitReusedUnchanged:
    """structural_map.tobit was verified at the Amharic τ.7.x.k ship;
    the Geʽez column reuses it UNCHANGED (same parallel PDF)."""

    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["tobit"]

    def test_block_present(self):
        assert "tobit" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["tob"]

    def test_pdf_page_range_1285_1293(self):
        assert self._blk()["pdf_page_range"] == [1285, 1293]

    def test_verified_at_tau7xk_not_re_verified_at_tau6x2k(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.k"

    def test_chapter_count_expected_14(self):
        assert self._blk()["chapter_count_expected"] == 14


# ──────────────────────────── output module ────────────────────────


class TestTau6X2KTobPy:
    def test_tob_py_exists(self):
        assert (GEEZ_TEWAHEDO / "tob.py").is_file()

    def test_translation_and_book_constants(self):
        c = _constants(GEEZ_TEWAHEDO, "tob")
        assert c.get("TRANSLATION") == "geez-tewahedo"
        assert c.get("BOOK") == "tob"

    def test_source_quality_ocr_tier3(self):
        assert _constants(GEEZ_TEWAHEDO, "tob").get("SOURCE_QUALITY") == "ocr-tier3"

    def test_source_provenance(self):
        assert _constants(GEEZ_TEWAHEDO, "tob").get("SOURCE_PROVENANCE") == "parallel-bible-eotc"

    def test_ingest_phase_tau6x2k(self):
        assert _constants(GEEZ_TEWAHEDO, "tob").get("INGEST_PHASE") == "τ.6.x.2.k"

    def test_geez_tob_total_verse_count_floor(self):
        # Empirical at ship: 134. Floor 120 guards regression while
        # permitting parser refinement (the τ.7.x.k ≥100 convention).
        verses = _verses(GEEZ_TEWAHEDO, "tob")
        assert len(verses) >= 120, f"τ.6.x.2.k Geʽez Tobit must have ≥120 verses; got {len(verses)}"

    def test_first_verse_is_tob_1_1(self):
        ch, v, text = _verses(GEEZ_TEWAHEDO, "tob")[0]
        assert (ch, v) == (1, 1)
        assert text

    def test_geez_text_distinct_from_amharic_column(self):
        """The Geʽez and Amharic Tobit columns extract DISTINCT text —
        NOT a column-misattribution bug (verified at ship)."""
        geez_first = _verses(GEEZ_TEWAHEDO, "tob")[0][2]
        amh_first = _verses(AMHARIC_TEWAHEDO, "tob")[0][2]
        assert geez_first != amh_first, "Geʽez tob[1:1] must differ from Amharic tob[1:1]"


# ─────────────────────────── coverage shape ────────────────────────


class TestTau6X2KTobCoverage:
    """Renumber UNDERFLOW: ch 1-7 fully populated (cumulative floor =
    131); ch 8 partial (3/21 — 134-131); ch 9-14 empty; no overflow."""

    def test_geez_tob_chapters_1_through_7_fully_populated(self):
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import TOBIT_VERSE_COUNTS

        by_ch = _by_chapter(GEEZ_TEWAHEDO, "tob")
        for ch in range(1, 8):
            got = len(by_ch.get(ch, []))
            exp = TOBIT_VERSE_COUNTS[ch]
            assert got == exp, f"τ.6.x.2.k tob ch {ch} must have exactly {exp} verses; got {got}"

    def test_geez_tob_chapter_8_partial(self):
        from extract_parallel_pdf import TOBIT_VERSE_COUNTS  # noqa: F401

        by_ch = _by_chapter(GEEZ_TEWAHEDO, "tob")
        got = len(by_ch.get(8, []))
        assert 1 <= got < 21, f"τ.6.x.2.k tob ch 8 partial expected (1..20); got {got}"

    def test_geez_tob_chapters_9_through_14_empty(self):
        by_ch = _by_chapter(GEEZ_TEWAHEDO, "tob")
        for ch in range(9, 15):
            assert len(by_ch.get(ch, [])) == 0, f"τ.6.x.2.k tob ch {ch} should be empty at ocr-tier3"

    def test_geez_tob_no_overflow_above_chapter_14(self):
        by_ch = _by_chapter(GEEZ_TEWAHEDO, "tob")
        overflow = sum(len(v) for ch, v in by_ch.items() if ch > 14)
        assert overflow == 0, f"τ.6.x.2.k renumber overflow should be 0; got {overflow} above ch 14"


# ───────────────────── _source.yaml ingest block ───────────────────


class TestTau6X2KSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau6x2k_ingest"]

    def test_block_exists(self):
        assert "tau6x2k_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.6.x.2.k"

    def test_helpers_reused_not_added(self):
        reused = self._blk()["helpers_reused"]
        assert "TOBIT_VERSE_COUNTS" in reused
        assert "structural_map.tobit" in reused

    def test_empirical_validation_coverage(self):
        ev = self._blk()["empirical_validation"]
        assert ev["coverage_pct"] == 54.5
        assert ev["renumbered_verse_count"] == 134
        assert ev["extraction_engine"] == "text-layer"
        assert ev["pdf_pages_consumed"] == [1285, 1293]

    def test_no_ingest_false(self):
        assert self._blk()["no_ingest_at_this_phase"] is False

    def test_arc_context_geez_deuterocanon_catchup_continue(self):
        assert self._blk()["arc_context"] == "geez-deuterocanon-catchup-continue"

    def test_block_drained_p1239_1293(self):
        """τ.6.x.2.j (Geʽez 2es) + τ.6.x.2.k (Geʽez tob) together drain
        the Geʽez column of the p1239-1293 EOTC-parallel block (mirrors
        the Amharic τ.7.x.j + τ.7.x.k pair)."""
        assert self._blk()["geez_block_drained"] == "p1239-1293"

    def test_closed_arc_tau7xa_through_tau7xm_preserved(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        for letter in "abcdefghijklm":
            assert contracts.get(f"tau7x{letter}_ingest") is True, f"tau7x{letter} must be preserved"

    def test_closed_arc_geez_through_tau6x2j_preserved(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        for letter in "abcdefgh":
            assert contracts.get(f"tau6x2{letter}_ingest") is True
        assert contracts.get("tau6x2i_ingest") is True, "τ.6.x.2.i HaCohen Psalms must be preserved"
        assert contracts.get("tau6x2j_ingest") is True, "τ.6.x.2.j Geʽez 2 Esdras must be preserved"

    def test_next_phase_tau6x2l(self):
        assert self._blk()["next_phase"] == "τ.6.x.2.l"


# ─────────────────── cross-column coherence (tau7xk) ────────────────


class TestTau6X2KCrossColumnCoherence:
    """Shipping τ.6.x.2.k updates tau7xk_ingest's geez_tewahedo_tob
    slot no-op→shipped + adds the geez-catchup back-link, WITHOUT
    touching pipeline_reused_at_phase (= τ.7.x.l, pinned elsewhere)."""

    def _tau7xk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xk_ingest"]

    def test_tau7xk_geez_slot_state_updated_to_shipped(self):
        slot = self._tau7xk()["translation_slot_state"]["geez_tewahedo_tob"]
        assert "shipped-at-τ.6.x.2.k" in slot
        assert "no-op" not in slot

    def test_tau7xk_geez_catchup_back_link_added(self):
        assert self._tau7xk().get("geez_catchup_reused_at_phase") == "τ.6.x.2.k"

    def test_tau7xk_pipeline_reused_at_phase_still_tau7xl(self):
        assert self._tau7xk()["pipeline_reused_at_phase"] == "τ.7.x.l"


# ─────────────────────── geez _meta.yaml record ────────────────────


class TestTau6X2KGeezMetaYaml:
    def test_stats_books_at_least_eleven(self):
        assert _geez_meta()["stats"]["books"] >= 11

    def test_stats_verses_at_least_7603(self):
        # 7469 (post-τ.6.x.2.j) + 134 (tob) = 7603.
        assert _geez_meta()["stats"]["verses"] >= 7603

    def test_stats_books_outside_kjv_at_least_two(self):
        """2es + tob are both deuterocanonical — the FIRST TWO Geʽez
        books outside the 66-book KJV canon."""
        assert _geez_meta()["stats"]["books_outside_kjv"] >= 2

    def test_ingest_record_tau6x2k(self):
        rec = _geez_meta()["ingest_record_tau6x2k"]
        assert rec["phase"] == "τ.6.x.2.k"
        assert rec["ingested_book_codes"] == ["tob"]
        assert rec["engine"] == "text-layer"
        assert rec["coverage"]["verses_extracted"] == 134
        assert rec["coverage"]["coverage_pct"] == 54.5
        assert rec["audit_handoff"] == "τ.6.x.3"

    def test_ingest_record_tau6x2k_block_drained_marker(self):
        assert _geez_meta()["ingest_record_tau6x2k"].get("geez_block_drained") == "p1239-1293"

    def test_prior_geez_ingest_records_still_present(self):
        m = _geez_meta()
        for letter in "abcdefgh":
            assert f"ingest_record_tau6x2{letter}" in m, f"prior geez ingest record missing: {letter}"
        assert "ingest_record_tau6x2i" in m, "τ.6.x.2.i HaCohen Psalms record must persist"
        assert "ingest_record_tau6x2j" in m, "τ.6.x.2.j Geʽez 2 Esdras record must persist"


# ─────────────────── prior-arc invariants preserved ────────────────


class TestTau6X2KPriorArcsPreserved:
    def test_amharic_tob_preserved(self):
        assert (AMHARIC_TEWAHEDO / "tob.py").is_file()
        assert _constants(AMHARIC_TEWAHEDO, "tob").get("INGEST_PHASE") == "τ.7.x.k"

    def test_geez_2es_tau6x2j_preserved(self):
        """τ.6.x.2.j Geʽez 2 Esdras must persist (additive ship)."""
        assert (GEEZ_TEWAHEDO / "2es.py").is_file()
        assert _constants(GEEZ_TEWAHEDO, "2es").get("INGEST_PHASE") == "τ.6.x.2.j"

    def test_geez_8book_narrative_arc_preserved(self):
        for book in ("gen", "ex", "lev", "num", "deu", "jos", "jdg", "rut"):
            assert (GEEZ_TEWAHEDO / f"{book}.py").is_file(), f"τ.6.x.2.a-h Geʽez {book} must persist"

    def test_geez_psalms_hacohen_preserved(self):
        assert (GEEZ_TEWAHEDO / "psa.py").is_file()
        assert _constants(GEEZ_TEWAHEDO, "psa").get("INGEST_PHASE") == "τ.6.x.2.i"

    def test_geez_deuterocanon_catchup_not_yet_past_tob(self):
        """τ.6.x.2.k ships tob; jdt/est/jub/1en Geʽez remain queued
        (the next sub-ships). Milestone-pin — flips per-book as the
        catchup advances (feedback_share_pin_pattern)."""
        for book in ("jdt", "est", "jub", "1en"):
            assert not (GEEZ_TEWAHEDO / f"{book}.py").exists(), (
                f"τ.6.x.2.k scope is tob-only; geez-tewahedo/{book}.py must NOT exist yet"
            )


# ───────────────────────────── state docs ──────────────────────────


class TestTau6X2KStateDocs:
    def test_changelog_records_tau6x2k(self):
        txt = (REPO / "dev" / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "τ.6.x.2.k" in txt

    def test_session_state_mentions_tau6x2k(self):
        txt = (REPO / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
        assert "τ.6.x.2.k" in txt

    def test_in_flight_mentions_tau6x2k(self):
        txt = (REPO / "dev" / "IN_FLIGHT.md").read_text(encoding="utf-8")
        assert "τ.6.x.2.k" in txt

    def test_plan_ledger_records_tau6x2k(self):
        txt = (REPO / "dev" / "PLAN_2026-05-09.md").read_text(encoding="utf-8")
        assert "τ.6.x.2.k" in txt

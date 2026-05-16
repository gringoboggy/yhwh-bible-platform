"""τ.6.x.2.j — Geʽez 2 Esdras / Ezra Sutuʼel full-book ingest pins
(2026-05-16).

NINTH Geʽez per-book ingest (geez-tewahedo/) and the FIRST Geʽez
deuterocanonical (non-protocanonical) ingest. Mirrors the Amharic
τ.7.x.j 2 Esdras ship (same PDF page range p1239-1284, same
EZRA_SUTUEL_VERSE_COUNTS renumber-floor, same structural_map.
ezra_sutuel block) — the ONLY delta is the `--lang geez` column
flip (zero-parser-API-delta; the cross-column reuse the τ.6.x.2.a-h
batch established now extends to the deep p1239+ deuterocanon
region).

Sequencing context:
- τ.6.x.2.a-h CLOSED the parallel-column-catchup arc for p0-437
  (Pentateuch → Ruth = 8 narrative books in BOTH columns).
- τ.6.x.2.i shipped Geʽez Psalms via the τ.6.x.5 EXTERNAL HaCohen
  path (digitized-critical-edition; NOT the OCR'd parallel column).
- τ.6.x.2.j RESUMES the narrative Geʽez catchup on the parallel-PDF
  path: 2 Esdras (`መጽሐፈ ዕዝራ ሱቱኤል`), the FIRST of the post-Psalms
  Geʽez deuterocanon-catchup sub-arc (2es → tob → jdt → est → mq →
  jub → 1en — the books the τ.6.x.2.a-h cadence left and the
  Amharic τ.7.x.j+ stream already shipped).

Coverage is honestly 63.6% (601/945) at ocr-tier3 — squarely in
the τ.6.x.2.a-h Geʽez band (53-67%). A clean renumber UNDERFLOW
(601 < 945 → ch 1-10 fill exactly, ch 11-16 empty, no partial, no
overflow); contrast the τ.7.x.v NT renumber-OVERFLOW which honestly
blocked. The Geʽez column recovered MORE than Amharic for this book
(601 vs the τ.7.x.j 322) — region/book-dependent at ocr-tier3,
reconciled at the τ.6.x.3 batched audit per the τ.6.x.0b honesty
contract. The two columns extract DISTINCT text (verified at ship —
not a column-misattribution bug).

Pins validate:
1. EZRA_SUTUEL_VERSE_COUNTS reused UNCHANGED (zero-parser-API-delta).
2. structural_map.ezra_sutuel reused UNCHANGED (verified at τ.7.x.j).
3. geez-tewahedo/2es.py module shape + INGEST_PHASE τ.6.x.2.j.
4. Per-chapter coverage (1-10 full; 11-16 empty; no partial/overflow).
5. geez _meta.yaml ingest_record_tau6x2j + stats (10 books).
6. _source.yaml ocr_strategy.tau6x2j_ingest block.
7. Cross-column coherence: tau7xj_ingest geez slot-state updated.
8. Amharic τ.7.x.j stream + the τ.6.x.2.a-i Geʽez arc preserved.
9. State-docs (CHANGELOG/SESSION_STATE/IN_FLIGHT/PLAN) record τ.6.x.2.j.
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


class TestTau6X2JEzraSutuelVerseCountsReusedUnchanged:
    """EZRA_SUTUEL_VERSE_COUNTS was added at the Amharic τ.7.x.j ship
    and is reused VERBATIM for the Geʽez column — zero-parser-API-
    delta. These pins assert the floor is still the τ.7.x.j shape."""

    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_module_symbol_present(self):
        from extract_parallel_pdf import EZRA_SUTUEL_VERSE_COUNTS

        assert isinstance(EZRA_SUTUEL_VERSE_COUNTS, dict)

    def test_sixteen_chapters(self):
        from extract_parallel_pdf import EZRA_SUTUEL_VERSE_COUNTS

        assert sorted(EZRA_SUTUEL_VERSE_COUNTS.keys()) == list(range(1, 17))

    def test_total_verses_945(self):
        from extract_parallel_pdf import EZRA_SUTUEL_VERSE_COUNTS

        assert sum(EZRA_SUTUEL_VERSE_COUNTS.values()) == 945

    def test_chapter_7_is_the_140_verse_giant(self):
        """The Ethiopic preserves the 7:36-105 fragment the Latin
        lost — ch 7 is the full 140-verse form + the book's largest."""
        from extract_parallel_pdf import EZRA_SUTUEL_VERSE_COUNTS

        assert EZRA_SUTUEL_VERSE_COUNTS[7] == 140
        assert max(EZRA_SUTUEL_VERSE_COUNTS, key=EZRA_SUTUEL_VERSE_COUNTS.get) == 7

    def test_chapters_1_through_10_sum_to_601(self):
        """The τ.6.x.2.j clean-underflow boundary: 601 extracted Geʽez
        verses renumber to EXACTLY fill chapters 1-10 (cumulative sum
        = 601), leaving 11-16 empty with zero partial / zero overflow."""
        from extract_parallel_pdf import EZRA_SUTUEL_VERSE_COUNTS

        assert sum(EZRA_SUTUEL_VERSE_COUNTS[c] for c in range(1, 11)) == 601


# ─────────────────────────── structural_map ────────────────────────


class TestTau6X2JStructuralMapEzraSutuelReusedUnchanged:
    """structural_map.ezra_sutuel was verified at the Amharic τ.7.x.j
    ship; the Geʽez column reuses it UNCHANGED (same parallel PDF —
    Geʽez = left column, Amharic = right column, same page range)."""

    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["ezra_sutuel"]

    def test_block_present(self):
        assert "ezra_sutuel" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["2es"]

    def test_pdf_page_range_1239_1284(self):
        assert self._blk()["pdf_page_range"] == [1239, 1284]

    def test_verified_at_tau7xj_not_re_verified_at_tau6x2j(self):
        """The Geʽez ingest does NOT re-verify the structural_map —
        it reuses the Amharic-verified block (the τ.6.x.2.a-h
        precedent: Geʽez reused τ.7.x.a-h structural_map verbatim)."""
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.j"

    def test_chapter_count_expected_16(self):
        assert self._blk()["chapter_count_expected"] == 16


# ──────────────────────────── output module ────────────────────────


class TestTau6X2J2esPy:
    def test_2es_py_exists(self):
        assert (GEEZ_TEWAHEDO / "2es.py").is_file()

    def test_translation_and_book_constants(self):
        c = _constants(GEEZ_TEWAHEDO, "2es")
        assert c.get("TRANSLATION") == "geez-tewahedo"
        assert c.get("BOOK") == "2es"

    def test_source_quality_ocr_tier3(self):
        assert _constants(GEEZ_TEWAHEDO, "2es").get("SOURCE_QUALITY") == "ocr-tier3"

    def test_source_provenance(self):
        assert _constants(GEEZ_TEWAHEDO, "2es").get("SOURCE_PROVENANCE") == "parallel-bible-eotc"

    def test_ingest_phase_tau6x2j(self):
        assert _constants(GEEZ_TEWAHEDO, "2es").get("INGEST_PHASE") == "τ.6.x.2.j"

    def test_geez_2es_total_verse_count_floor(self):
        # Empirical at ship: 601. Floor 550 guards regression while
        # permitting parser refinement (the τ.7.x.j ≥300 convention).
        verses = _verses(GEEZ_TEWAHEDO, "2es")
        assert len(verses) >= 550, f"τ.6.x.2.j Geʽez 2 Esdras must have ≥550 verses; got {len(verses)}"

    def test_first_verse_is_2es_1_1(self):
        ch, v, text = _verses(GEEZ_TEWAHEDO, "2es")[0]
        assert (ch, v) == (1, 1)
        assert text

    def test_geez_text_distinct_from_amharic_column(self):
        """The Geʽez and Amharic columns extract DISTINCT text — this
        is NOT a column-misattribution bug (verified at ship). The
        first verse differs between the two slots."""
        geez_first = _verses(GEEZ_TEWAHEDO, "2es")[0][2]
        amh_first = _verses(AMHARIC_TEWAHEDO, "2es")[0][2]
        assert geez_first != amh_first, "Geʽez 2es[1:1] must differ from Amharic 2es[1:1]"


# ─────────────────────────── coverage shape ────────────────────────


class TestTau6X2J2esCoverage:
    """Clean renumber UNDERFLOW: ch 1-10 fully populated (cumulative
    floor sum = 601 = extracted count exactly); ch 11-16 empty; NO
    partial chapter; NO overflow above ch 16 (the τ.6.x.2.f Joshua
    no-partial precedent)."""

    def test_geez_2es_chapters_1_through_10_fully_populated(self):
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import EZRA_SUTUEL_VERSE_COUNTS

        by_ch = _by_chapter(GEEZ_TEWAHEDO, "2es")
        for ch in range(1, 11):
            got = len(by_ch.get(ch, []))
            exp = EZRA_SUTUEL_VERSE_COUNTS[ch]
            assert got == exp, f"τ.6.x.2.j 2es ch {ch} must have exactly {exp} verses; got {got}"

    def test_geez_2es_chapters_11_through_16_empty(self):
        by_ch = _by_chapter(GEEZ_TEWAHEDO, "2es")
        for ch in range(11, 17):
            assert len(by_ch.get(ch, [])) == 0, f"τ.6.x.2.j 2es ch {ch} should be empty at ocr-tier3"

    def test_geez_2es_no_partial_chapter(self):
        """The 601 = sum(ch1..10) exact-boundary means NO partial
        chapter (unlike the τ.7.x.j Amharic 2es ch-7-partial)."""
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import EZRA_SUTUEL_VERSE_COUNTS

        by_ch = _by_chapter(GEEZ_TEWAHEDO, "2es")
        for ch, verses in by_ch.items():
            if verses:
                assert len(verses) == EZRA_SUTUEL_VERSE_COUNTS[ch], (
                    f"τ.6.x.2.j 2es ch {ch} must be exactly full (no partial); "
                    f"got {len(verses)}/{EZRA_SUTUEL_VERSE_COUNTS[ch]}"
                )

    def test_geez_2es_no_overflow_above_chapter_16(self):
        by_ch = _by_chapter(GEEZ_TEWAHEDO, "2es")
        overflow = sum(len(v) for ch, v in by_ch.items() if ch > 16)
        assert overflow == 0, f"τ.6.x.2.j renumber overflow should be 0; got {overflow} above ch 16"


# ───────────────────── _source.yaml ingest block ───────────────────


class TestTau6X2JSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau6x2j_ingest"]

    def test_block_exists(self):
        assert "tau6x2j_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.6.x.2.j"

    def test_helpers_reused_not_added(self):
        """Zero-parser-API-delta: EZRA_SUTUEL_VERSE_COUNTS +
        structural_map.ezra_sutuel are REUSED from τ.7.x.j, not
        newly added."""
        reused = self._blk()["helpers_reused"]
        assert "EZRA_SUTUEL_VERSE_COUNTS" in reused
        assert "structural_map.ezra_sutuel" in reused

    def test_empirical_validation_coverage(self):
        ev = self._blk()["empirical_validation"]
        assert ev["coverage_pct"] == 63.6
        assert ev["renumbered_verse_count"] == 601
        assert ev["extraction_engine"] == "text-layer"
        assert ev["pdf_pages_consumed"] == [1239, 1284]

    def test_no_ingest_false(self):
        assert self._blk()["no_ingest_at_this_phase"] is False

    def test_arc_context_geez_deuterocanon_catchup_resume(self):
        assert self._blk()["arc_context"] == "geez-deuterocanon-catchup-resume"

    def test_resumes_geez_catchup_narrative(self):
        assert "arc_resumes_geez_deuterocanon_catchup" in self._blk()
        narrative = self._blk()["arc_resumes_geez_deuterocanon_catchup"]
        assert "τ.6.x.2.a-h" in narrative and "τ.6.x.2.i" in narrative

    def test_closed_arc_tau7xa_through_tau7xm_preserved(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        for letter in "abcdefghijklm":
            assert contracts.get(f"tau7x{letter}_ingest") is True, f"tau7x{letter} must be preserved"

    def test_closed_arc_tau6x2_geez_batch_and_psalms_preserved(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        for letter in "abcdefgh":
            assert contracts.get(f"tau6x2{letter}_ingest") is True
        assert contracts.get("tau6x2i_ingest") is True, "τ.6.x.2.i HaCohen Psalms must be preserved"

    def test_next_phase_tau6x2k(self):
        assert self._blk()["next_phase"] == "τ.6.x.2.k"


# ─────────────────── cross-column coherence (tau7xj) ────────────────


class TestTau6X2JCrossColumnCoherence:
    """The Amharic τ.7.x.j tau7xj_ingest block recorded
    geez_tewahedo_2es as 'no-op ... queued'; shipping τ.6.x.2.j
    updates that to 'shipped' + adds the geez-catchup back-link —
    WITHOUT touching pipeline_reused_at_phase (= τ.7.x.k, pinned by
    test_parallel_bible_tau7xj.py)."""

    def _tau7xj(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xj_ingest"]

    def test_tau7xj_geez_slot_state_updated_to_shipped(self):
        slot = self._tau7xj()["translation_slot_state"]["geez_tewahedo_2es"]
        assert "shipped-at-τ.6.x.2.j" in slot
        assert "no-op" not in slot

    def test_tau7xj_geez_catchup_back_link_added(self):
        assert self._tau7xj().get("geez_catchup_reused_at_phase") == "τ.6.x.2.j"

    def test_tau7xj_pipeline_reused_at_phase_still_tau7xk(self):
        """The existing τ.7.x.j → τ.7.x.k back-link pin must NOT
        regress (test_parallel_bible_tau7xj.py pins this == τ.7.x.k)."""
        assert self._tau7xj()["pipeline_reused_at_phase"] == "τ.7.x.k"


# ─────────────────────── geez _meta.yaml record ────────────────────


class TestTau6X2JGeezMetaYaml:
    def test_stats_books_at_least_ten(self):
        assert _geez_meta()["stats"]["books"] >= 10

    def test_stats_verses_at_least_7469(self):
        # 6868 (8-book parallel-PDF + psa) + 601 (2es) = 7469.
        assert _geez_meta()["stats"]["verses"] >= 7469

    def test_stats_books_outside_kjv_at_least_one(self):
        """2 Esdras is deuterocanonical — the FIRST Geʽez book
        outside the 66-book KJV canon (gen-rut + psa are all
        protocanonical so the prior value was 0)."""
        assert _geez_meta()["stats"]["books_outside_kjv"] >= 1

    def test_ingest_record_tau6x2j(self):
        rec = _geez_meta()["ingest_record_tau6x2j"]
        assert rec["phase"] == "τ.6.x.2.j"
        assert rec["ingested_book_codes"] == ["2es"]
        assert rec["engine"] == "text-layer"
        assert rec["coverage"]["verses_extracted"] == 601
        assert rec["coverage"]["coverage_pct"] == 63.6
        assert rec["audit_handoff"] == "τ.6.x.3"

    def test_ingest_record_tau6x2j_deuterocanon_first_geez_marker(self):
        assert _geez_meta()["ingest_record_tau6x2j"].get("deuterocanon_first_geez") is True

    def test_prior_geez_ingest_records_still_present(self):
        m = _geez_meta()
        for letter in "abcdefgh":
            assert f"ingest_record_tau6x2{letter}" in m, f"prior geez ingest record missing: {letter}"
        assert "ingest_record_tau6x2i" in m, "τ.6.x.2.i HaCohen Psalms record must persist"


# ─────────────────── prior-arc invariants preserved ────────────────


class TestTau6X2JPriorArcsPreserved:
    def test_amharic_2es_preserved(self):
        """The Amharic τ.7.x.j 2es ship is untouched (cross-column
        invariant — the Geʽez ingest must not regress Amharic)."""
        assert (AMHARIC_TEWAHEDO / "2es.py").is_file()
        assert _constants(AMHARIC_TEWAHEDO, "2es").get("INGEST_PHASE") == "τ.7.x.j"

    def test_geez_8book_narrative_arc_preserved(self):
        for book in ("gen", "ex", "lev", "num", "deu", "jos", "jdg", "rut"):
            assert (GEEZ_TEWAHEDO / f"{book}.py").is_file(), f"τ.6.x.2.a-h Geʽez {book} must persist"

    def test_geez_psalms_hacohen_preserved(self):
        """τ.6.x.2.i Geʽez Psalms (τ.6.x.5 HaCohen external path)
        must persist and remain digitized-critical-edition."""
        assert (GEEZ_TEWAHEDO / "psa.py").is_file()
        assert _constants(GEEZ_TEWAHEDO, "psa").get("INGEST_PHASE") == "τ.6.x.2.i"

    def test_geez_deuterocanon_catchup_not_yet_past_2es(self):
        """τ.6.x.2.j ships ONLY 2es; tob/jdt/est/mq/jub/1en Geʽez
        remain queued (the next sub-ships). Milestone-pin: this
        flips per-book as the catchup advances (feedback_share_pin
        _pattern)."""
        for book in ("tob", "jdt", "est", "jub", "1en"):
            assert not (GEEZ_TEWAHEDO / f"{book}.py").exists(), (
                f"τ.6.x.2.j scope is 2es-only; geez-tewahedo/{book}.py must NOT exist yet"
            )


# ───────────────────────────── state docs ──────────────────────────


class TestTau6X2JStateDocs:
    def test_changelog_records_tau6x2j(self):
        txt = (REPO / "dev" / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "τ.6.x.2.j" in txt

    def test_session_state_mentions_tau6x2j(self):
        txt = (REPO / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
        assert "τ.6.x.2.j" in txt

    def test_in_flight_mentions_tau6x2j(self):
        txt = (REPO / "dev" / "IN_FLIGHT.md").read_text(encoding="utf-8")
        assert "τ.6.x.2.j" in txt

    def test_plan_ledger_records_tau6x2j(self):
        txt = (REPO / "dev" / "PLAN_2026-05-09.md").read_text(encoding="utf-8")
        assert "τ.6.x.2.j" in txt

"""τ.7.x.j + τ.7.x.k — Amharic 2 Esdras / Ezra Sutuʼel + Tobit
full-book ingest pins (2026-05-15).

TENTH + ELEVENTH τ.7.x.* per-book ships under D4-c Amharic-first +
D1-a per-book cadence. **FIRST TWO deuterocanonical (non-
protocanonical) τ.7.x.* ingests** — the prior nine (gen→psa,
τ.7.x.a-i) are all protocanonical.

Together they drain the THIRD EOTC-parallel block of the source PDF
(p1239-1293), discovered/verified by the τ.7.x.j structural scan:
- **τ.7.x.j 2 Esdras / Ezra Sutuʼel** (`መጽሐፈ ዕዝራ ሱቱኤል`): p1239-1284,
  FIRST in PDF reading order; EZRA_SUTUEL_VERSE_COUNTS (16 ch / 945 v
  per content/books.yaml `2es` ch_count: 16; NRSV 16-ch incl. the
  restored 7:36-105 Ethiopic fragment so ch 7 = 140 v).
- **τ.7.x.k Tobit** (`መጽሐፈ ጦቢት`): p1285-1293, SECOND in PDF;
  TOBIT_VERSE_COUNTS (14 ch / 246 v per `tob` ch_count: 14; NRSV/GII).

PDF reading order (2 Esdras then Tobit) governs the phase→book
assignment per §2.3/§6.1 verifiable-canonical-order + every prior
ship's ascending-PDF-page convention. The 2 Esdras→Tobit boundary
(p1284/1285) and Tobit→Judith boundary (p1293/1294) were fixed by
content-boundary scan; cross-validated because Mäqabyan I opens at
p1318 EXACTLY matching the pre-existing structural_map.meqabyan
[1318, 1378].

Coverage is honestly LOW (2es 34.1%, tob 48.0%) — a new τ.7.x.*
band-bottom — because these deuterocanonical books sit deep in the
PDF "(ረቂቅ)"/draft parallel region where the text-layer is more
garbled + the apocalyptic chapters are very long. This is expected
per the τ.6.x.0b honesty contract and reconciled at the τ.6.x.3
batched audit; the zero-parser-API-delta invariant is preserved
(only EZRA_SUTUEL_VERSE_COUNTS + TOBIT_VERSE_COUNTS + structural_map
blocks + CLI dispatch changed — the τ.7.x.a template generalizes to
deuterocanon with ZERO pipeline change).

Pins validate:
1. EZRA_SUTUEL_VERSE_COUNTS / TOBIT_VERSE_COUNTS dict shapes.
2. structural_map.ezra_sutuel / structural_map.tobit blocks.
3. amharic-tewahedo/2es.py + tob.py module shape + INGEST_PHASE.
4. Per-chapter coverage (1-6 full; 7 partial; rest empty; no overflow).
5. _meta.yaml ingest_record_tau7xj / _tau7xk + stats (11 books).
6. _source.yaml ocr_strategy.tau7xj_ingest / _tau7xk_ingest blocks.
7. Back-link chain tau7xi→τ.7.x.j→τ.7.x.k; τ.7.x.i pins preserved.
8. CLI --renumber {…, psalms, ezra_sutuel, tobit}.
9. Geʽez 2es/tob NOT created (D4-c; queued for τ.6.x.2.j/k).
10. Deuterocanon-first markers + p1239-1293 block-drained.
11. All prior τ.7.x.a-i + τ.6.x.2.a-h closed-arc invariants preserved.
"""

from __future__ import annotations

import ast
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SOURCE_YAML = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
AMHARIC_TEWAHEDO = REPO / "content" / "translations" / "amharic-tewahedo"
GEEZ_TEWAHEDO = REPO / "content" / "translations" / "geez-tewahedo"


def _source_yaml() -> dict:
    return yaml.safe_load(SOURCE_YAML.read_text(encoding="utf-8"))


def _meta() -> dict:
    return yaml.safe_load((AMHARIC_TEWAHEDO / "_meta.yaml").read_text(encoding="utf-8"))


def _verses(book: str) -> list[tuple]:
    py = AMHARIC_TEWAHEDO / f"{book}.py"
    tree = ast.parse(py.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSES":
                    return ast.literal_eval(node.value)
    raise AssertionError(f"amharic-tewahedo/{book}.py must define VERSES")


def _constants(book: str) -> dict:
    py = AMHARIC_TEWAHEDO / f"{book}.py"
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


def _by_chapter(book: str) -> dict[int, list[tuple]]:
    out: dict[int, list[tuple]] = {}
    for ch, v, t in _verses(book):
        out.setdefault(ch, []).append((v, t))
    return out


# ───────────────────────────── floor dicts ─────────────────────────


class TestTau7XJEzraSutuelVerseCounts:
    """EZRA_SUTUEL_VERSE_COUNTS is the τ.7.x.j renumber-floor dict."""

    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_module_symbol_present(self):
        from extract_parallel_pdf import EZRA_SUTUEL_VERSE_COUNTS

        assert isinstance(EZRA_SUTUEL_VERSE_COUNTS, dict)

    def test_sixteen_chapters(self):
        """content/books.yaml fixes `2es` at ch_count: 16."""
        from extract_parallel_pdf import EZRA_SUTUEL_VERSE_COUNTS

        assert sorted(EZRA_SUTUEL_VERSE_COUNTS.keys()) == list(range(1, 17))

    def test_total_verses_945(self):
        """NRSV 16-ch 2 Esdras incl. the restored 7:36-105 fragment."""
        from extract_parallel_pdf import EZRA_SUTUEL_VERSE_COUNTS

        assert sum(EZRA_SUTUEL_VERSE_COUNTS.values()) == 945

    def test_chapter_7_is_the_140_verse_giant(self):
        """The Ethiopic preserves the "missing fragment" 7:36-105 the
        Latin lost — so ch 7 is the full 140-verse form."""
        from extract_parallel_pdf import EZRA_SUTUEL_VERSE_COUNTS

        assert EZRA_SUTUEL_VERSE_COUNTS[7] == 140
        # ch 7 is the single largest chapter in the book
        assert max(EZRA_SUTUEL_VERSE_COUNTS, key=EZRA_SUTUEL_VERSE_COUNTS.get) == 7

    def test_books_yaml_2es_ch_count_16(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "2es")
        assert rec["ch_count"] == 16
        assert "Sutu" in rec["title"]  # "Ezra Sutu'el"


class TestTau7XKTobitVerseCounts:
    """TOBIT_VERSE_COUNTS is the τ.7.x.k renumber-floor dict."""

    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_module_symbol_present(self):
        from extract_parallel_pdf import TOBIT_VERSE_COUNTS

        assert isinstance(TOBIT_VERSE_COUNTS, dict)

    def test_fourteen_chapters(self):
        """content/books.yaml fixes `tob` at ch_count: 14 (LXX)."""
        from extract_parallel_pdf import TOBIT_VERSE_COUNTS

        assert sorted(TOBIT_VERSE_COUNTS.keys()) == list(range(1, 15))

    def test_total_verses_246(self):
        """NRSV/GII 14-ch Tobit enumeration."""
        from extract_parallel_pdf import TOBIT_VERSE_COUNTS

        assert sum(TOBIT_VERSE_COUNTS.values()) == 246

    def test_books_yaml_tob_ch_count_14(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "tob")
        assert rec["ch_count"] == 14
        assert "Tobit" in rec["title"]


# ─────────────────────────── structural_map ────────────────────────


class TestTau7XJStructuralMapEzraSutuel:
    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["ezra_sutuel"]

    def test_block_present(self):
        assert "ezra_sutuel" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["2es"]

    def test_pdf_page_range_1239_1284(self):
        assert self._blk()["pdf_page_range"] == [1239, 1284]

    def test_pdf_index_offset_zero(self):
        assert self._blk()["pdf_index_offset"] == 0

    def test_verified_at_tau7xj(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.j"

    def test_chapter_count_expected_16(self):
        assert self._blk()["chapter_count_expected"] == 16

    def test_notes_document_meqabyan_crossvalidation(self):
        """The decisive scan cross-validation (Mäqabyan I @ p1318 ==
        pre-existing structural_map.meqabyan [1318,1378]) is recorded
        in the τ.7.x.j ingest block's boundary_verification."""
        bv = _source_yaml()["ocr_strategy"]["tau7xj_ingest"]["structural_map_addition"]["boundary_verification"]
        assert "1318" in bv and "meqabyan" in bv.lower()


class TestTau7XKStructuralMapTobit:
    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["tobit"]

    def test_block_present(self):
        assert "tobit" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["tob"]

    def test_pdf_page_range_1285_1293(self):
        assert self._blk()["pdf_page_range"] == [1285, 1293]

    def test_verified_at_tau7xk(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.k"

    def test_chapter_count_expected_14(self):
        assert self._blk()["chapter_count_expected"] == 14

    def test_notes_document_colophon_and_judith_boundary(self):
        notes = self._blk()["notes"]
        assert "ተፈጸመ" in notes
        assert "1293" in notes and "1294" in notes


# ──────────────────────────── output modules ───────────────────────


class TestTau7XJ2esPy:
    def test_2es_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "2es.py").is_file()

    def test_translation_and_book_constants(self):
        c = _constants("2es")
        assert c.get("TRANSLATION") == "amharic-tewahedo"
        assert c.get("BOOK") == "2es"

    def test_source_quality_ocr_tier3(self):
        assert _constants("2es").get("SOURCE_QUALITY") == "ocr-tier3"

    def test_source_provenance(self):
        assert _constants("2es").get("SOURCE_PROVENANCE") == "parallel-bible-eotc"

    def test_ingest_phase_tau7xj(self):
        assert _constants("2es").get("INGEST_PHASE") == "τ.7.x.j"

    def test_amharic_2es_total_verse_count_floor(self):
        # Empirical at ship: 322. Floor 300 guards regression while
        # permitting parser refinement.
        verses = _verses("2es")
        assert len(verses) >= 300, f"τ.7.x.j 2 Esdras ingest must have ≥300 verses; got {len(verses)}"

    def test_first_verse_is_2es_1_1(self):
        ch, v, text = _verses("2es")[0]
        assert (ch, v) == (1, 1)
        assert text


class TestTau7XKTobPy:
    def test_tob_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "tob.py").is_file()

    def test_translation_and_book_constants(self):
        c = _constants("tob")
        assert c.get("TRANSLATION") == "amharic-tewahedo"
        assert c.get("BOOK") == "tob"

    def test_source_quality_ocr_tier3(self):
        assert _constants("tob").get("SOURCE_QUALITY") == "ocr-tier3"

    def test_ingest_phase_tau7xk(self):
        assert _constants("tob").get("INGEST_PHASE") == "τ.7.x.k"

    def test_amharic_tob_total_verse_count_floor(self):
        # Empirical at ship: 118. Floor 100 guards regression.
        verses = _verses("tob")
        assert len(verses) >= 100, f"τ.7.x.k Tobit ingest must have ≥100 verses; got {len(verses)}"

    def test_first_verse_is_tob_1_1(self):
        ch, v, text = _verses("tob")[0]
        assert (ch, v) == (1, 1)
        assert text


# ─────────────────────────── coverage shape ────────────────────────


class TestTau7XJ2esCoverage:
    """Empirical post-renumber distribution: ch 1-6 full; 7 partial
    (31/140); 8-16 empty; no overflow above ch 16."""

    def test_amharic_2es_chapters_1_through_6_fully_populated(self):
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import EZRA_SUTUEL_VERSE_COUNTS

        by_ch = _by_chapter("2es")
        for ch in range(1, 7):
            got = len(by_ch.get(ch, []))
            exp = EZRA_SUTUEL_VERSE_COUNTS[ch]
            assert got == exp, f"τ.7.x.j 2es ch {ch} must have exactly {exp} verses; got {got}"

    def test_amharic_2es_chapter_7_partial(self):
        by_ch = _by_chapter("2es")
        got = len(by_ch.get(7, []))
        assert 1 <= got < 140, f"τ.7.x.j 2es ch 7 partial expected (1..139); got {got}"

    def test_amharic_2es_chapters_8_through_16_empty(self):
        by_ch = _by_chapter("2es")
        for ch in range(8, 17):
            assert len(by_ch.get(ch, [])) == 0, f"τ.7.x.j 2es ch {ch} should be empty at ocr-tier3"

    def test_amharic_2es_no_overflow_above_chapter_16(self):
        by_ch = _by_chapter("2es")
        overflow = sum(len(v) for ch, v in by_ch.items() if ch > 16)
        assert overflow == 0, f"τ.7.x.j renumber overflow should be 0; got {overflow} above ch 16"


class TestTau7XKTobCoverage:
    """Empirical: ch 1-6 full; 7 partial (4/17); 8-14 empty; no overflow."""

    def test_amharic_tob_chapters_1_through_6_fully_populated(self):
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import TOBIT_VERSE_COUNTS

        by_ch = _by_chapter("tob")
        for ch in range(1, 7):
            got = len(by_ch.get(ch, []))
            exp = TOBIT_VERSE_COUNTS[ch]
            assert got == exp, f"τ.7.x.k tob ch {ch} must have exactly {exp} verses; got {got}"

    def test_amharic_tob_chapter_7_partial(self):
        by_ch = _by_chapter("tob")
        got = len(by_ch.get(7, []))
        assert 1 <= got < 17, f"τ.7.x.k tob ch 7 partial expected (1..16); got {got}"

    def test_amharic_tob_chapters_8_through_14_empty(self):
        by_ch = _by_chapter("tob")
        for ch in range(8, 15):
            assert len(by_ch.get(ch, [])) == 0, f"τ.7.x.k tob ch {ch} should be empty at ocr-tier3"

    def test_amharic_tob_no_overflow_above_chapter_14(self):
        by_ch = _by_chapter("tob")
        overflow = sum(len(v) for ch, v in by_ch.items() if ch > 14)
        assert overflow == 0, f"τ.7.x.k renumber overflow should be 0; got {overflow} above ch 14"


# ───────────────────── _source.yaml ingest blocks ──────────────────


class TestTau7XJSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xj_ingest"]

    def test_block_exists(self):
        assert "tau7xj_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.7.x.j"

    def test_structural_map_addition(self):
        sma = self._blk()["structural_map_addition"]
        assert sma["section"] == "ezra_sutuel"
        assert sma["pdf_page_range"] == [1239, 1284]
        assert sma["chapter_count_expected"] == 16

    def test_helpers_added(self):
        assert "EZRA_SUTUEL_VERSE_COUNTS" in self._blk()["helpers_added"]

    def test_cli_extensions(self):
        assert "renumber_choice_extended" in self._blk()["cli_extensions"]

    def test_empirical_validation_coverage(self):
        ev = self._blk()["empirical_validation"]
        assert ev["coverage_pct"] == 34.1
        assert ev["renumbered_verse_count"] == 322

    def test_no_ingest_false(self):
        assert self._blk()["no_ingest_at_this_phase"] is False

    def test_deuterocanon_first_arc(self):
        assert "arc_continues_deuterocanon" in self._blk()
        assert "FIRST" in self._blk()["arc_continues_deuterocanon"]

    def test_closed_arc_tau7xa_through_tau7xi_preserved(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        for letter in "abcdefghi":
            assert contracts.get(f"tau7x{letter}_ingest") is True, f"tau7x{letter} must be preserved"

    def test_closed_arc_tau6x2_geez_batch_preserved(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        for letter in "abcdefgh":
            assert contracts.get(f"tau6x2{letter}_ingest") is True

    def test_next_phase_tau7xk(self):
        assert self._blk()["next_phase"] == "τ.7.x.k"

    def test_pipeline_reused_back_link_to_tau7xk(self):
        assert self._blk()["pipeline_reused_at_phase"] == "τ.7.x.k"


class TestTau7XKSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xk_ingest"]

    def test_block_exists(self):
        assert "tau7xk_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.7.x.k"

    def test_structural_map_addition(self):
        sma = self._blk()["structural_map_addition"]
        assert sma["section"] == "tobit"
        assert sma["pdf_page_range"] == [1285, 1293]
        assert sma["chapter_count_expected"] == 14

    def test_helpers_added(self):
        assert "TOBIT_VERSE_COUNTS" in self._blk()["helpers_added"]

    def test_empirical_validation_coverage(self):
        ev = self._blk()["empirical_validation"]
        assert ev["coverage_pct"] == 48.0
        assert ev["renumbered_verse_count"] == 118

    def test_block_drained_p1239_1293(self):
        assert self._blk()["block_drained"] == "p1239-1293"

    def test_closed_arc_tau7xj_preserved(self):
        assert self._blk()["closed_arc_contracts_preserved"]["tau7xj_ingest"] is True

    def test_next_phase_tau7xl(self):
        assert self._blk()["next_phase"] == "τ.7.x.l"


# ─────────────────────── _meta.yaml ingest records ─────────────────


class TestTau7XJKMetaYamlIngestRecords:
    def test_stats_books_at_least_eleven(self):
        assert _meta()["stats"]["books"] >= 11

    def test_stats_verses_at_least_8682(self):
        assert _meta()["stats"]["verses"] >= 8682

    def test_stats_books_outside_kjv_two(self):
        """2es + tob are deuterocanonical — outside the 66-book KJV canon."""
        assert _meta()["stats"]["books_outside_kjv"] >= 2

    def test_tau7xj_ingest_record(self):
        m = _meta()
        assert m["ingest_record_tau7xj"]["phase"] == "τ.7.x.j"
        assert m["ingest_record_tau7xj"]["ingested_book_codes"] == ["2es"]
        assert m["ingest_record_tau7xj"]["coverage"]["verses_extracted"] == 322

    def test_tau7xk_ingest_record(self):
        m = _meta()
        assert m["ingest_record_tau7xk"]["phase"] == "τ.7.x.k"
        assert m["ingest_record_tau7xk"]["ingested_book_codes"] == ["tob"]
        assert m["ingest_record_tau7xk"]["coverage"]["verses_extracted"] == 118

    def test_tau7xj_deuterocanon_first_marker(self):
        assert _meta()["ingest_record_tau7xj"].get("deuterocanon_first") is True

    def test_tau7xk_block_drained_marker(self):
        assert _meta()["ingest_record_tau7xk"].get("block_drained") == "p1239-1293"

    def test_prior_ingest_records_still_present(self):
        m = _meta()
        assert "ingest_record" in m  # τ.7.x.a base record
        for tag in ("tau7xb", "tau7xc", "tau7xd", "tau7xe", "tau7xf", "tau7xg", "tau7xh", "tau7xi"):
            assert f"ingest_record_{tag}" in m, f"prior ingest record missing: {tag}"

    def test_tau7xi_pipeline_reused_back_link_added(self):
        """The established single-key back-link: τ.7.x.i record now
        points forward to τ.7.x.j (which reused its pipeline)."""
        assert _meta()["ingest_record_tau7xi"]["pipeline_reused_at_phase"] == "τ.7.x.j"


# ───────────────────── deuterocanon arc + invariants ───────────────


class TestTau7XJKDeuterocanonArc:
    def test_both_books_shipped_amharic(self):
        assert (AMHARIC_TEWAHEDO / "2es.py").is_file()
        assert (AMHARIC_TEWAHEDO / "tob.py").is_file()

    def test_protocanon_nine_preserved(self):
        for book in ("gen", "ex", "lev", "num", "deu", "jos", "jdg", "rut", "psa"):
            assert (AMHARIC_TEWAHEDO / f"{book}.py").is_file(), f"prior τ.7.x.* book {book} must persist"

    def test_geez_2es_tob_ingested_p1239_1293_block_drained(self):
        """MIGRATED TWICE per memory `feedback_share_pin_pattern` +
        the τ.6.x.2.a-h precedent. Originally `test_geez_2es_tob_not_
        created` (BOTH must NOT exist, D4-c deferral); at τ.6.x.2.j
        the 2es half flipped to "must EXIST"; at τ.6.x.2.k the tob
        half flips too. Durable invariant: τ.6.x.2.j (2es) + τ.6.x.2.k
        (tob) together drained the Geʽez column of the p1239-1293
        EOTC-parallel block — both files present at ocr-tier3 (mirrors
        the Amharic τ.7.x.j + τ.7.x.k pair this test file covers)."""
        assert (GEEZ_TEWAHEDO / "2es.py").is_file(), "Geʽez 2es.py must EXIST after the τ.6.x.2.j catchup ship"
        assert (GEEZ_TEWAHEDO / "tob.py").is_file(), "Geʽez tob.py must EXIST after the τ.6.x.2.k catchup ship"

    def test_geez_8book_arc_preserved(self):
        for book in ("gen", "ex", "lev", "num", "deu", "jos", "jdg", "rut"):
            assert (GEEZ_TEWAHEDO / f"{book}.py").is_file()

    def test_skip_the_gap_books_still_absent(self):
        """τ.7.x.i skip-the-gap invariant preserved: the still-skipped
        dzamaragna-gap books must NOT exist in amharic-tewahedo. NOTE:
        `est` was converted at τ.7.x.m (sourced from the EOTC-parallel
        block p1308-1317) so it is NO LONGER in this list (10→9); the
        other 9 remain skipped. Share-pin→milestone-pin convention."""
        for book in ("1sa", "2sa", "1ki", "2ki", "1ch", "2ch", "ezr", "neh", "job"):
            assert not (AMHARIC_TEWAHEDO / f"{book}.py").exists(), (
                f"skip-the-gap invariant: amharic-tewahedo/{book}.py must NOT exist"
            )

    def test_cli_renumber_choices_extended(self):
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        import importlib

        import extract_parallel_pdf

        importlib.reload(extract_parallel_pdf)
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert '"ezra_sutuel"' in src and '"tobit"' in src
        # the four dispatch sites: choices list + help + _build_docstring_extra + main
        assert src.count("EZRA_SUTUEL_VERSE_COUNTS") >= 3
        assert src.count("TOBIT_VERSE_COUNTS") >= 3


class TestTau7XJKBackLinkChainAndPriorPinsPreserved:
    """The τ.7.x.i → τ.7.x.j → τ.7.x.k back-link chain, AND the
    τ.7.x.i regression pins must STILL hold (additive ship)."""

    def test_tau7xi_next_phase_still_tau7xj(self):
        """τ.7.x.i test_next_phase_tau7xj pin must remain green."""
        assert _source_yaml()["ocr_strategy"]["tau7xi_ingest"]["next_phase"] == "τ.7.x.j"

    def test_tau7xi_pipeline_reused_at_tau7xj(self):
        assert _source_yaml()["ocr_strategy"]["tau7xi_ingest"]["pipeline_reused_at_phase"] == "τ.7.x.j"

    def test_tau7xh_back_links_preserved(self):
        """τ.7.x.i's test_reciprocal_back_link_in_tau7xh_also_reused
        pin must remain green — do not mutate tau7xh."""
        h = _source_yaml()["ocr_strategy"]["tau7xh_ingest"]
        assert h.get("pipeline_reused_at_phase") == "τ.6.x.2.h"
        assert h.get("also_reused_at_phase") == "τ.7.x.i"

    def test_tau7xi_psalms_block_unchanged(self):
        psa = _source_yaml()["structural_map"]["psalms"]
        assert psa["pdf_page_range"] == [803, 906]
        assert psa["verified_at_phase"] == "τ.7.x.i"

    def test_tau7xi_psa_still_shipped(self):
        assert (AMHARIC_TEWAHEDO / "psa.py").is_file()
        assert _constants("psa").get("INGEST_PHASE") == "τ.7.x.i"


class TestTau7XJKStateDocs:
    def test_session_state_mentions_both_phases(self):
        txt = (REPO / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
        assert "τ.7.x.j" in txt and "τ.7.x.k" in txt

    def test_in_flight_mentions_tau7xj(self):
        txt = (REPO / "dev" / "IN_FLIGHT.md").read_text(encoding="utf-8")
        assert "τ.7.x.j" in txt

    def test_changelog_records_tau7xj_tau7xk(self):
        txt = (REPO / "dev" / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "τ.7.x.j" in txt and "τ.7.x.k" in txt

    def test_plan_ledger_records_tau7xj(self):
        txt = (REPO / "dev" / "PLAN_2026-05-09.md").read_text(encoding="utf-8")
        assert "τ.7.x.j" in txt

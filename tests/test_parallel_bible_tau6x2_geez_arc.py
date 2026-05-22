"""τ.6.x.2.a-h — Geʽez catchup batch (D4-c) (2026-05-15).

Single test file covering the τ.6.x.2.a-h Geʽez 8-book batch ship —
the D4-c sequencing-inversion catchup that brings the Geʽez column
to PARITY with the Amharic column for the entire parallel-Bible-EOTC
scan range (pages 0-437; Pentateuch + Joshua + Judges + Ruth = 8
books in both columns).

Per D4-c at τ.6.x.2.D: Amharic was shipped FIRST (τ.7.x.a-h, 2026-05-15)
then Geʽez catchup (τ.6.x.2.a-h, 2026-05-15 same session). Both
columns now at parity for the parallel-Bible-EOTC scan boundary.

Pipeline reused VERBATIM from τ.7.x.a-h with only `--lang geez` flag
flip as the per-ship delta. 16-ship template stability across both
columns (8 Amharic + 8 Geʽez) with zero parser API drift.

Per-book Geʽez coverage (consistent ~50-65% recovery, lower than
Amharic's 70-93% — Geʽez column harder to parse per τ.6.x.0a
honesty contract):

| Phase     | Book | Verses | Floor | Coverage | Amharic eq |
|-----------|------|-------:|------:|---------:|-----------:|
| τ.6.x.2.a | gen  |   1022 |  1534 |    66.6% |      85.3% |
| τ.6.x.2.b | ex   |    643 |  1213 |    53.0% |      78.1% |
| τ.6.x.2.c | lev  |    534 |   859 |    62.2% |      93.4% |
| τ.6.x.2.d | num  |    830 |  1288 |    64.4% |      85.9% |
| τ.6.x.2.e | deu  |    508 |   959 |    53.0% |      81.4% |
| τ.6.x.2.f | jos  |    351 |   658 |    53.3% |      73.4% |
| τ.6.x.2.g | jdg  |    393 |   618 |    63.6% |      82.7% |
| τ.6.x.2.h | rut  |     56 |    85 |    65.9% |      70.6% |
| TOTAL     |      |   4337 |  7214 |    60.1% |      83.2% |

Pins validate:
1. All 8 Geʽez per-book files exist and have INGEST_PHASE='τ.6.x.2.X'.
2. Per-book verse count floors (≥80% of empirical to guard against regression).
3. Per-book chapter coverage breakdown matches the τ.7.x.* renumber pattern.
4. Each tau6x2X_ingest block records the catchup-batch arc context.
5. _meta.yaml stats upgraded from Π.0 seed (1 book / 3 verses) to
   8-book ingest (8 books / 4337 verses).
6. Eight prior tau6x2X ingest records present.
7. Amharic τ.7.x.a-h state preserved (no regressions).
8. τ.6.x.2.e records §8.1 Pentateuch arc-close (Geʽez stream).
9. τ.6.x.2.h records parallel-column-catchup arc-close.
10. Both columns at parity for parallel-Bible-EOTC scan range.
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


def _geez_meta() -> dict:
    return yaml.safe_load((GEEZ_TEWAHEDO / "_meta.yaml").read_text(encoding="utf-8"))


def _amharic_meta() -> dict:
    return yaml.safe_load((AMHARIC_TEWAHEDO / "_meta.yaml").read_text(encoding="utf-8"))


def _verses_of(book: str) -> list[tuple]:
    path = GEEZ_TEWAHEDO / f"{book}.py"
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSES":
                    return ast.literal_eval(node.value)
    raise AssertionError(f"geez-tewahedo/{book}.py must define VERSES")


def _constants_of(book: str) -> dict:
    path = GEEZ_TEWAHEDO / f"{book}.py"
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
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


# Empirical at ship: 8 books with these expected verse counts.
EMPIRICAL_VERSE_COUNTS = {
    "gen": 1022,
    "ex": 643,
    "lev": 534,
    "num": 830,
    "deu": 508,
    "jos": 351,
    "jdg": 393,
    "rut": 56,
}

# Floors below empirical to guard against regression; permits parser refinement.
REGRESSION_FLOORS = {
    "gen": 950,
    "ex": 600,
    "lev": 500,
    "num": 780,
    "deu": 475,
    "jos": 325,
    "jdg": 365,
    "rut": 50,
}

PHASE_OF = {
    "gen": "τ.6.x.2.a",
    "ex": "τ.6.x.2.b",
    "lev": "τ.6.x.2.c",
    "num": "τ.6.x.2.d",
    "deu": "τ.6.x.2.e",
    "jos": "τ.6.x.2.f",
    "jdg": "τ.6.x.2.g",
    "rut": "τ.6.x.2.h",
}


class TestTau6X2GeezBatchFilesExist:
    """All 8 Geʽez per-book files exist after the τ.6.x.2.a-h batch ship."""

    def test_all_eight_geez_books_present(self):
        for book in EMPIRICAL_VERSE_COUNTS:
            path = GEEZ_TEWAHEDO / f"{book}.py"
            assert path.is_file(), f"τ.6.x.2.a-h: geez-tewahedo/{book}.py must exist after batch ship"


class TestTau6X2GeezBatchModuleConstants:
    """Each Geʽez .py file declares the τ.7.x.* module-constant set
    with INGEST_PHASE pointing to its τ.6.x.2.X phase."""

    def test_translation_constant_all_books(self):
        for book in EMPIRICAL_VERSE_COUNTS:
            c = _constants_of(book)
            assert c.get("TRANSLATION") == "geez-tewahedo", f"{book}: TRANSLATION constant"

    def test_book_constant_all_books(self):
        for book in EMPIRICAL_VERSE_COUNTS:
            c = _constants_of(book)
            assert c.get("BOOK") == book, f"{book}: BOOK constant"

    def test_source_quality_tier3_all_books(self):
        for book in EMPIRICAL_VERSE_COUNTS:
            c = _constants_of(book)
            assert c.get("SOURCE_QUALITY") == "ocr-tier3", f"{book}: SOURCE_QUALITY"

    def test_source_provenance_all_books(self):
        for book in EMPIRICAL_VERSE_COUNTS:
            c = _constants_of(book)
            assert c.get("SOURCE_PROVENANCE") == "parallel-bible-eotc", f"{book}: SOURCE_PROVENANCE"

    def test_ingest_phase_per_book(self):
        for book, phase in PHASE_OF.items():
            c = _constants_of(book)
            assert c.get("INGEST_PHASE") == phase, f"{book}: INGEST_PHASE should be {phase}"


class TestTau6X2GeezBatchVerseCounts:
    """Per-book verse counts meet regression-protection floors."""

    def test_gen_at_least_floor(self):
        assert len(_verses_of("gen")) >= REGRESSION_FLOORS["gen"]

    def test_ex_at_least_floor(self):
        assert len(_verses_of("ex")) >= REGRESSION_FLOORS["ex"]

    def test_lev_at_least_floor(self):
        assert len(_verses_of("lev")) >= REGRESSION_FLOORS["lev"]

    def test_num_at_least_floor(self):
        assert len(_verses_of("num")) >= REGRESSION_FLOORS["num"]

    def test_deu_at_least_floor(self):
        assert len(_verses_of("deu")) >= REGRESSION_FLOORS["deu"]

    def test_jos_at_least_floor(self):
        assert len(_verses_of("jos")) >= REGRESSION_FLOORS["jos"]

    def test_jdg_at_least_floor(self):
        assert len(_verses_of("jdg")) >= REGRESSION_FLOORS["jdg"]

    def test_rut_at_least_floor(self):
        assert len(_verses_of("rut")) >= REGRESSION_FLOORS["rut"]

    def test_combined_eight_book_at_least_floor(self):
        """Combined Geʽez 8-book verse count should be ≥4000 (vs
        empirical 4337 at ship; gives ~8% headroom)."""
        total = sum(len(_verses_of(b)) for b in EMPIRICAL_VERSE_COUNTS)
        assert total >= 4000, f"Combined Geʽez 8-book verses must be ≥4000; got {total}"


class TestTau6X2GeezBatchCoverage:
    """Per-book coverage ≥50% — Geʽez is consistently ~50-65% at
    ocr-tier3 (lower than Amharic per τ.6.x.0a honesty contract)."""

    def _coverage_pct(self, book: str) -> float:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import (
            DEUTERONOMY_VERSE_COUNTS,
            EXODUS_VERSE_COUNTS,
            GENESIS_VERSE_COUNTS,
            JOSHUA_VERSE_COUNTS,
            JUDGES_VERSE_COUNTS,
            LEVITICUS_VERSE_COUNTS,
            NUMBERS_VERSE_COUNTS,
            RUTH_VERSE_COUNTS,
        )

        floors = {
            "gen": GENESIS_VERSE_COUNTS,
            "ex": EXODUS_VERSE_COUNTS,
            "lev": LEVITICUS_VERSE_COUNTS,
            "num": NUMBERS_VERSE_COUNTS,
            "deu": DEUTERONOMY_VERSE_COUNTS,
            "jos": JOSHUA_VERSE_COUNTS,
            "jdg": JUDGES_VERSE_COUNTS,
            "rut": RUTH_VERSE_COUNTS,
        }
        return 100.0 * len(_verses_of(book)) / sum(floors[book].values())

    def test_per_book_coverage_at_least_50_pct(self):
        """Each of 8 books covers ≥50% of its renumber-floor."""
        for book in EMPIRICAL_VERSE_COUNTS:
            pct = self._coverage_pct(book)
            assert pct >= 50.0, f"τ.6.x.2.{book}: coverage must be ≥50%; got {pct:.1f}%"

    def test_combined_eight_book_coverage_at_least_55_pct(self):
        """Combined 8-book Geʽez coverage ≥55% (empirical 60.1% at
        ship)."""
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import (
            DEUTERONOMY_VERSE_COUNTS,
            EXODUS_VERSE_COUNTS,
            GENESIS_VERSE_COUNTS,
            JOSHUA_VERSE_COUNTS,
            JUDGES_VERSE_COUNTS,
            LEVITICUS_VERSE_COUNTS,
            NUMBERS_VERSE_COUNTS,
            RUTH_VERSE_COUNTS,
        )

        floors = [
            GENESIS_VERSE_COUNTS,
            EXODUS_VERSE_COUNTS,
            LEVITICUS_VERSE_COUNTS,
            NUMBERS_VERSE_COUNTS,
            DEUTERONOMY_VERSE_COUNTS,
            JOSHUA_VERSE_COUNTS,
            JUDGES_VERSE_COUNTS,
            RUTH_VERSE_COUNTS,
        ]
        total_extracted = sum(len(_verses_of(b)) for b in EMPIRICAL_VERSE_COUNTS)
        total_expected = sum(sum(f.values()) for f in floors)
        pct = 100.0 * total_extracted / total_expected
        assert pct >= 55.0, f"Combined Geʽez 8-book coverage must be ≥55%; got {pct:.1f}%"


class TestTau6X2SourceYamlIngestBlocks:
    """ocr_strategy.tau6x2a-h_ingest blocks all present and well-formed."""

    def test_all_eight_blocks_exist(self):
        ocr = _source_yaml()["ocr_strategy"]
        for phase_letter in "abcdefgh":
            block_name = f"tau6x2{phase_letter}_ingest"
            assert block_name in ocr, f"_source.yaml: {block_name} block missing"

    def test_all_blocks_record_correct_phase(self):
        ocr = _source_yaml()["ocr_strategy"]
        for phase_letter in "abcdefgh":
            block = ocr[f"tau6x2{phase_letter}_ingest"]
            assert block["shipped_at_phase"] == f"τ.6.x.2.{phase_letter}"

    def test_all_blocks_record_arc_context_catchup(self):
        ocr = _source_yaml()["ocr_strategy"]
        for phase_letter in "abcdefgh":
            block = ocr[f"tau6x2{phase_letter}_ingest"]
            assert "parallel-column-catchup-batch" in block["arc_context"], (
                f"τ.6.x.2.{phase_letter}: arc_context must reference parallel-column-catchup-batch"
            )

    def test_tau6x2e_records_pentateuch_arc_close(self):
        """τ.6.x.2.e closes the Geʽez §8.1 Pentateuch arc (mirrors τ.7.x.e Amharic)."""
        block = _source_yaml()["ocr_strategy"]["tau6x2e_ingest"]
        assert block.get("arc_close") == "§8.1", "τ.6.x.2.e must record §8.1 Pentateuch arc-close (Geʽez stream)"

    def test_tau6x2h_records_catchup_arc_close(self):
        """τ.6.x.2.h closes the parallel-column-catchup arc."""
        block = _source_yaml()["ocr_strategy"]["tau6x2h_ingest"]
        assert "arc_close_parallel_column_catchup" in block, "τ.6.x.2.h must record parallel-column-catchup arc-close"
        assert "CLOSE" in block["arc_context"], "τ.6.x.2.h arc_context must indicate CLOSE variant of catchup batch"

    def test_tau6x2a_records_upgrade_from_seed(self):
        """τ.6.x.2.a upgrades Geʽez Genesis from Π.0-seed (3 verses)
        to ocr-tier3 full-book ingest."""
        block = _source_yaml()["ocr_strategy"]["tau6x2a_ingest"]
        assert block.get("upgraded_from") == "Π.0-seed-3-verses", "τ.6.x.2.a must record upgrade from Π.0 seed"

    def test_tau7xh_back_link_to_tau6x2h(self):
        """τ.7.x.h tau7xh_ingest block must carry pipeline_reused_at_
        phase = τ.6.x.2.h (the Geʽez catchup back-link annotation)."""
        h = _source_yaml()["ocr_strategy"]["tau7xh_ingest"]
        assert h.get("pipeline_reused_at_phase") == "τ.6.x.2.h"


class TestTau6X2GeezMetaYaml:
    """geez-tewahedo/_meta.yaml upgraded from Π.0 seed to 8-book ingest."""

    def test_stats_books_at_least_eight(self):
        m = _geez_meta()
        assert m["stats"]["books"] >= 8

    def test_stats_verses_at_least_4000(self):
        m = _geez_meta()
        assert m["stats"]["verses"] >= 4000

    def test_all_eight_ingest_records_present(self):
        m = _geez_meta()
        for phase_letter in "abcdefgh":
            record_key = f"ingest_record_tau6x2{phase_letter}"
            assert record_key in m, f"geez _meta.yaml: {record_key} missing"

    def test_ingest_records_carry_correct_phase(self):
        m = _geez_meta()
        for phase_letter in "abcdefgh":
            rec = m[f"ingest_record_tau6x2{phase_letter}"]
            assert rec["phase"] == f"τ.6.x.2.{phase_letter}"

    def test_ingest_record_tau6x2a_book_codes_gen(self):
        m = _geez_meta()
        assert m["ingest_record_tau6x2a"]["ingested_book_codes"] == ["gen"]

    def test_ingest_record_tau6x2h_book_codes_rut(self):
        m = _geez_meta()
        assert m["ingest_record_tau6x2h"]["ingested_book_codes"] == ["rut"]

    def test_tau6x2a_upgraded_from_seed(self):
        m = _geez_meta()
        assert m["ingest_record_tau6x2a"].get("upgraded_from") == "Π.0-seed-3-verses"

    def test_tau6x2e_records_pentateuch_arc_close(self):
        m = _geez_meta()
        assert m["ingest_record_tau6x2e"].get("arc_close_pentateuch") == "§8.1"

    def test_tau6x2h_records_catchup_arc_close(self):
        m = _geez_meta()
        rec = m["ingest_record_tau6x2h"]
        assert "arc_close_parallel_column_catchup" in rec


class TestTau6X2AmharicStreamPreserved:
    """τ.7.x.a-h Amharic stream preserved through the Geʽez catchup
    batch. Cross-column ingest must not regress the Amharic state."""

    def test_amharic_stats_still_at_eight_books(self):
        m = _amharic_meta()
        assert m["stats"]["books"] >= 8, "Amharic stream must still have ≥8 books"

    def test_amharic_stats_still_at_least_5800_verses(self):
        m = _amharic_meta()
        assert m["stats"]["verses"] >= 5800, "Amharic stream must still have ≥5800 verses"

    def test_amharic_per_book_files_still_exist(self):
        for book in ("gen", "ex", "lev", "num", "deu", "jos", "jdg", "rut"):
            path = AMHARIC_TEWAHEDO / f"{book}.py"
            assert path.is_file(), (
                f"Cross-column invariant: amharic-tewahedo/{book}.py must still exist after τ.6.x.2.a-h"
            )

    def test_amharic_ingest_records_all_present(self):
        m = _amharic_meta()
        # ingest_record (gen, τ.7.x.a) + ingest_record_tau7x{b..h}
        assert "ingest_record" in m
        for tag in ("tau7xb", "tau7xc", "tau7xd", "tau7xe", "tau7xf", "tau7xg", "tau7xh"):
            assert f"ingest_record_{tag}" in m, f"Amharic {tag} ingest record must still exist"


class TestTau6X2ParallelColumnParity:
    """At τ.6.x.2.h close, both columns are at parity for the
    parallel-Bible-EOTC scan range (pages 0-437; 8 books)."""

    def test_both_columns_have_same_book_set(self):
        """Both amharic-tewahedo/ and geez-tewahedo/ have the same
        8 per-book .py files after the catchup batch."""
        expected = {f"{b}.py" for b in EMPIRICAL_VERSE_COUNTS}
        amharic_present = {f.name for f in AMHARIC_TEWAHEDO.iterdir() if f.suffix == ".py"}
        geez_present = {f.name for f in GEEZ_TEWAHEDO.iterdir() if f.suffix == ".py"}
        # Both should be SUPERSET of the expected 8 (no other books shipped yet).
        for book_file in expected:
            assert book_file in amharic_present, f"Parity: amharic missing {book_file}"
            assert book_file in geez_present, f"Parity: geez missing {book_file}"

    def test_no_post_437_book_in_either_column(self):
        """Per τ.7.x.h structural discovery: no τ.7.x.i+ ship yet
        in either column (next book would need new publication-
        format handler)."""
        # 1 Samuel = 1sa; 1 Kingdoms = 1ki under LXX naming
        for col_dir in (AMHARIC_TEWAHEDO, GEEZ_TEWAHEDO):
            for next_book in ("1sa.py", "1ki.py", "2sa.py"):
                assert not (col_dir / next_book).exists(), (
                    f"τ.7.x.i+ must NOT exist yet: {col_dir.name}/{next_book} should not be created until "
                    f"new publication-format handler is in place"
                )


class TestTau6X2StateDocs:
    # Doc-pins collapsed to the CHANGELOG chokepoint (2026-05-21): the old
    # session_state / in_flight / plan_ledger pins read SESSION_STATE.md /
    # IN_FLIGHT.md (rolling, trimmed) and the moved PLAN_2026-05-09.md. The
    # durable phase record is CHANGELOG.md, which carries the batch tag.
    def test_phase_recorded_in_changelog(self):
        from tests.fixtures import assert_phase_recorded

        assert_phase_recorded("τ.6.x.2.a-h")

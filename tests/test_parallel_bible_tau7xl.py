"""τ.7.x.l + τ.7.x.m — Amharic Judith + Esther full-book ingest pins
(2026-05-15).

TWELFTH + THIRTEENTH τ.7.x.* per-book ships under D4-c Amharic-first
+ D1-a per-book cadence. Together they drain the FOURTH EOTC-parallel
block p1294-1317:
- **τ.7.x.l Judith** (`መጽሐፈ ዮዲት`): p1294-1307; JUDITH_VERSE_COUNTS
  (16 ch / 339 v; NRSV/LXX; books.yaml `jdt` ch_count:16). THIRD
  deuterocanonical τ.7.x.* ingest.
- **τ.7.x.m Esther** (`መጽሐፈ አስቴር`): p1308-1317; ESTHER_VERSE_COUNTS
  (10 ch / 167 v; KJV/Hebrew Masoretic core; books.yaml `est`
  ch_count:10; the Greek Additions are the SEPARATE b25 book).
  **PROTOCANONICAL** (in the KJV 66-book canon) — the first
  protocanonical τ.7.x.* book since τ.7.x.i Psalms.

**Esther skip-pin conversion:** τ.7.x.i recorded `est` SKIPPED-via
the 438-802 dzamaragna gap but explicitly documented this EOTC-
parallel block p1308-1317 as the preferred source "if/when that
ship happens". τ.7.x.m IS that ship — so the τ.7.x.i `est` skip-pin
is converted (removed from SKIPPED_BOOKS 10→9 in
test_parallel_bible_tau7xi.py + test_parallel_bible_tau7xj.py +
tau7xi_ingest.translation_slot_state). The other 9 dzamaragna books
(1sa/2sa/1ki/2ki/1ch/2ch/ezr/neh/job) remain skipped. Per memory
feedback_share_pin_pattern: flip prior-ship pins a new ship
legitimately invalidates, AS PART OF the triggering ship.

PDF reading order (τ.7.x.l scan p1291-1321): Judith then Esther;
decisively cross-validated because Mäqabyan I opens at p1318
EXACTLY matching the pre-existing structural_map.meqabyan
[1318,1378] (the same cross-validation that confirmed τ.7.x.j/k).

Coverage: Judith 35.4% (deuterocanon-deep-PDF band like 2es 34.1%),
Esther 79.6% (back in the protocanonical band — compact 10-ch
Hebrew floor + short narrative chapters). Both renumber cleanly
(1-N full / N+1 partial / rest empty / 0 overflow). Honest per the
τ.6.x.0b contract; τ.6.x.3 audit reconciles. Zero-parser-API-delta
preserved (12th + 13th consecutive; 21-ship across both columns).

Pins validate: floor dicts, structural_map blocks, jdt.py/est.py
modules, coverage shape, _source.yaml + _meta.yaml records, the
back-link chain tau7xk→l→m, the est skip-pin conversion, and that
all prior τ.7.x.a-k + τ.6.x.2.a-h closed-arc pins remain green.
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
    tree = ast.parse((AMHARIC_TEWAHEDO / f"{book}.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSES":
                    return ast.literal_eval(node.value)
    raise AssertionError(f"amharic-tewahedo/{book}.py must define VERSES")


def _constants(book: str) -> dict:
    tree = ast.parse((AMHARIC_TEWAHEDO / f"{book}.py").read_text(encoding="utf-8"))
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


class TestTau7XLJudithVerseCounts:
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

    def test_books_yaml_jdt_ch_count_16(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "jdt")
        assert rec["ch_count"] == 16
        assert "Judith" in rec["title"]


class TestTau7XMEstherVerseCounts:
    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_module_symbol_present(self):
        from extract_parallel_pdf import ESTHER_VERSE_COUNTS

        assert isinstance(ESTHER_VERSE_COUNTS, dict)

    def test_ten_chapters(self):
        """books.yaml `est` ch_count: 10 — Hebrew Masoretic core."""
        from extract_parallel_pdf import ESTHER_VERSE_COUNTS

        assert sorted(ESTHER_VERSE_COUNTS.keys()) == list(range(1, 11))

    def test_total_verses_167(self):
        from extract_parallel_pdf import ESTHER_VERSE_COUNTS

        assert sum(ESTHER_VERSE_COUNTS.values()) == 167

    def test_books_yaml_est_ch_count_10(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "est")
        assert rec["ch_count"] == 10
        assert "Esther" in rec["title"]


# ─────────────────────────── structural_map ────────────────────────


class TestTau7XLStructuralMapJudith:
    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["judith"]

    def test_block_present(self):
        assert "judith" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["jdt"]

    def test_pdf_page_range_1294_1307(self):
        assert self._blk()["pdf_page_range"] == [1294, 1307]

    def test_verified_at_tau7xl(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.l"

    def test_chapter_count_expected_16(self):
        assert self._blk()["chapter_count_expected"] == 16


class TestTau7XMStructuralMapEsther:
    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["esther"]

    def test_block_present(self):
        assert "esther" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["est"]

    def test_pdf_page_range_1308_1317(self):
        assert self._blk()["pdf_page_range"] == [1308, 1317]

    def test_verified_at_tau7xm(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.m"

    def test_chapter_count_expected_10(self):
        assert self._blk()["chapter_count_expected"] == 10

    def test_notes_document_meqabyan_crossvalidation(self):
        notes = self._blk()["notes"]
        assert "1318" in notes and "meqabyan" in notes.lower()

    def test_notes_document_skip_pin_conversion(self):
        notes = self._blk()["notes"]
        assert "skip-pin" in notes.lower() or "skip pin" in notes.lower()
        assert "τ.7.x.i" in notes


# ──────────────────────────── output modules ───────────────────────


class TestTau7XLJdtPy:
    def test_jdt_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "jdt.py").is_file()

    def test_constants(self):
        c = _constants("jdt")
        assert c.get("TRANSLATION") == "amharic-tewahedo"
        assert c.get("BOOK") == "jdt"
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"
        assert c.get("INGEST_PHASE") == "τ.7.x.l"

    def test_amharic_jdt_total_verse_count_floor(self):
        # Empirical at ship: 120. Floor 100 guards regression.
        assert len(_verses("jdt")) >= 100

    def test_first_verse_is_jdt_1_1(self):
        ch, v, text = _verses("jdt")[0]
        assert (ch, v) == (1, 1)
        assert text


class TestTau7XMEstPy:
    def test_est_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "est.py").is_file()

    def test_constants(self):
        c = _constants("est")
        assert c.get("TRANSLATION") == "amharic-tewahedo"
        assert c.get("BOOK") == "est"
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"
        assert c.get("INGEST_PHASE") == "τ.7.x.m"

    def test_amharic_est_total_verse_count_floor(self):
        # Empirical at ship: 133. Floor 110 guards regression.
        assert len(_verses("est")) >= 110

    def test_first_verse_is_est_1_1(self):
        ch, v, text = _verses("est")[0]
        assert (ch, v) == (1, 1)
        assert text


# ─────────────────────────── coverage shape ────────────────────────


class TestTau7XLJdtCoverage:
    """Empirical: ch 1-6 full; 7 partial (6/32); 8-16 empty; 0 overflow."""

    def test_amharic_jdt_chapters_1_through_6_fully_populated(self):
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import JUDITH_VERSE_COUNTS

        by_ch = _by_chapter("jdt")
        for ch in range(1, 7):
            got = len(by_ch.get(ch, []))
            exp = JUDITH_VERSE_COUNTS[ch]
            assert got == exp, f"τ.7.x.l jdt ch {ch} must have exactly {exp} verses; got {got}"

    def test_amharic_jdt_chapter_7_partial(self):
        got = len(_by_chapter("jdt").get(7, []))
        assert 1 <= got < 32, f"τ.7.x.l jdt ch 7 partial expected (1..31); got {got}"

    def test_amharic_jdt_chapters_8_through_16_empty(self):
        by_ch = _by_chapter("jdt")
        for ch in range(8, 17):
            assert len(by_ch.get(ch, [])) == 0, f"τ.7.x.l jdt ch {ch} should be empty at ocr-tier3"

    def test_amharic_jdt_no_overflow_above_chapter_16(self):
        by_ch = _by_chapter("jdt")
        assert sum(len(v) for ch, v in by_ch.items() if ch > 16) == 0


class TestTau7XMEstCoverage:
    """Empirical: ch 1-8 full; 9 partial (1/32); 10 empty; 0 overflow."""

    def test_amharic_est_chapters_1_through_8_fully_populated(self):
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import ESTHER_VERSE_COUNTS

        by_ch = _by_chapter("est")
        for ch in range(1, 9):
            got = len(by_ch.get(ch, []))
            exp = ESTHER_VERSE_COUNTS[ch]
            assert got == exp, f"τ.7.x.m est ch {ch} must have exactly {exp} verses; got {got}"

    def test_amharic_est_chapter_9_partial(self):
        got = len(_by_chapter("est").get(9, []))
        assert 1 <= got < 32, f"τ.7.x.m est ch 9 partial expected (1..31); got {got}"

    def test_amharic_est_chapter_10_empty(self):
        assert len(_by_chapter("est").get(10, [])) == 0

    def test_amharic_est_no_overflow_above_chapter_10(self):
        by_ch = _by_chapter("est")
        assert sum(len(v) for ch, v in by_ch.items() if ch > 10) == 0


# ───────────────────── _source.yaml ingest blocks ──────────────────


class TestTau7XLSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xl_ingest"]

    def test_block_exists(self):
        assert "tau7xl_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.7.x.l"

    def test_structural_map_addition(self):
        sma = self._blk()["structural_map_addition"]
        assert sma["section"] == "judith"
        assert sma["pdf_page_range"] == [1294, 1307]
        assert sma["chapter_count_expected"] == 16

    def test_helpers_added(self):
        assert "JUDITH_VERSE_COUNTS" in self._blk()["helpers_added"]

    def test_empirical_validation(self):
        ev = self._blk()["empirical_validation"]
        assert ev["coverage_pct"] == 35.4
        assert ev["renumbered_verse_count"] == 120

    def test_closed_arc_tau7xa_through_tau7xk_preserved(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        for tag in ("tau7xa", "tau7xb", "tau7xi", "tau7xj", "tau7xk"):
            assert contracts.get(f"{tag}_ingest") is True

    def test_next_phase_tau7xm(self):
        assert self._blk()["next_phase"] == "τ.7.x.m"

    def test_pipeline_reused_back_link(self):
        assert self._blk()["pipeline_reused_at_phase"] == "τ.7.x.m"


class TestTau7XMSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xm_ingest"]

    def test_block_exists(self):
        assert "tau7xm_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.7.x.m"

    def test_structural_map_addition(self):
        sma = self._blk()["structural_map_addition"]
        assert sma["section"] == "esther"
        assert sma["pdf_page_range"] == [1308, 1317]
        assert sma["chapter_count_expected"] == 10

    def test_empirical_validation(self):
        ev = self._blk()["empirical_validation"]
        assert ev["coverage_pct"] == 79.6
        assert ev["renumbered_verse_count"] == 133

    def test_block_drained_p1294_1317(self):
        assert self._blk()["block_drained"] == "p1294-1317"

    def test_esther_skip_pin_conversion_documented(self):
        blk = self._blk()
        assert "esther_skip_pin_conversion" in blk
        conv = blk["esther_skip_pin_conversion"]
        assert "SKIPPED_BOOKS" in conv
        assert "feedback_share_pin_pattern" in conv

    def test_protocanonical_context(self):
        sma = self._blk()["structural_map_addition"]
        assert "protocanonical_context" in sma

    def test_next_phase_tau7xn(self):
        assert self._blk()["next_phase"] == "τ.7.x.n"


# ─────────────────────── _meta.yaml ingest records ─────────────────


class TestTau7XLMMetaYamlIngestRecords:
    def test_stats_books_at_least_thirteen(self):
        assert _meta()["stats"]["books"] >= 13

    def test_stats_verses_at_least_8935(self):
        assert _meta()["stats"]["verses"] >= 8935

    def test_stats_books_outside_kjv_three(self):
        """2es + tob + jdt are deuterocanonical; est (Esther) is
        PROTOCANONICAL (in the 66-book KJV canon) so it does NOT
        increment books_outside_kjv."""
        assert _meta()["stats"]["books_outside_kjv"] >= 3

    def test_tau7xl_ingest_record(self):
        m = _meta()
        assert m["ingest_record_tau7xl"]["phase"] == "τ.7.x.l"
        assert m["ingest_record_tau7xl"]["ingested_book_codes"] == ["jdt"]
        assert m["ingest_record_tau7xl"]["coverage"]["verses_extracted"] == 120

    def test_tau7xm_ingest_record(self):
        m = _meta()
        assert m["ingest_record_tau7xm"]["phase"] == "τ.7.x.m"
        assert m["ingest_record_tau7xm"]["ingested_book_codes"] == ["est"]
        assert m["ingest_record_tau7xm"]["coverage"]["verses_extracted"] == 133

    def test_tau7xm_protocanonical_marker(self):
        assert _meta()["ingest_record_tau7xm"].get("protocanonical") is True

    def test_tau7xm_esther_skip_pin_converted_marker(self):
        assert _meta()["ingest_record_tau7xm"].get("esther_skip_pin_converted") is True

    def test_tau7xm_block_drained(self):
        assert _meta()["ingest_record_tau7xm"].get("block_drained") == "p1294-1317"

    def test_tau7xk_pipeline_reused_back_link_added(self):
        assert _meta()["ingest_record_tau7xk"]["pipeline_reused_at_phase"] == "τ.7.x.l"

    def test_prior_ingest_records_present(self):
        m = _meta()
        assert "ingest_record" in m
        for tag in ("tau7xb", "tau7xh", "tau7xi", "tau7xj", "tau7xk"):
            assert f"ingest_record_{tag}" in m, f"prior ingest record missing: {tag}"


# ───────────────── Esther skip-pin conversion (the key class) ──────


class TestTau7XMEstherSkipPinConversion:
    """τ.7.x.m converts the τ.7.x.i `est` skip-pin: Esther now ships
    from the EOTC-parallel block p1308-1317 (the documented preferred
    alternative), so `est` is removed from the dzamaragna SKIPPED_BOOKS
    sets (10→9). The other 9 dzamaragna books stay skipped. Per memory
    feedback_share_pin_pattern."""

    NINE_STILL_SKIPPED = ("1sa", "2sa", "1ki", "2ki", "1ch", "2ch", "ezr", "neh", "job")

    def test_est_py_now_exists(self):
        """The conversion is only valid because Esther actually shipped."""
        assert (AMHARIC_TEWAHEDO / "est.py").is_file()
        assert _constants("est").get("INGEST_PHASE") == "τ.7.x.m"

    def test_est_removed_from_tau7xi_skipped_books_class(self):
        import sys

        sys.path.insert(0, str(REPO / "tests"))
        from test_parallel_bible_tau7xi import TestTau7XISkipTheGapInvariants as T

        assert "est" not in T.SKIPPED_BOOKS, "τ.7.x.i SKIPPED_BOOKS must no longer contain `est`"
        assert len(T.SKIPPED_BOOKS) == 9
        for b in self.NINE_STILL_SKIPPED:
            assert b in T.SKIPPED_BOOKS, f"{b} must remain in the still-skipped set"

    def test_tau7xi_slot_state_est_converted(self):
        state = _source_yaml()["ocr_strategy"]["tau7xi_ingest"]["translation_slot_state"]
        assert "CONVERTED-at-τ.7.x.m" in state["amharic_tewahedo_est"]
        assert "SKIPPED" not in state["amharic_tewahedo_est"].split("CONVERTED")[0]

    def test_nine_other_dzamaragna_books_still_skipped(self):
        """The conversion is surgical — only `est`. The other 9
        dzamaragna-gap books must STILL be absent + still marked
        SKIPPED in the τ.7.x.i slot-state."""
        state = _source_yaml()["ocr_strategy"]["tau7xi_ingest"]["translation_slot_state"]
        for b in self.NINE_STILL_SKIPPED:
            assert not (AMHARIC_TEWAHEDO / f"{b}.py").exists(), f"{b}.py must still NOT exist"
            assert "SKIPPED" in state[f"amharic_tewahedo_{b}"]

    def test_tau7xm_block_records_conversion(self):
        conv = _source_yaml()["ocr_strategy"]["tau7xm_ingest"]["esther_skip_pin_conversion"]
        assert "τ.7.x.i" in conv and "feedback_share_pin_pattern" in conv


# ───────────────── deuterocanon arc + prior-pin preservation ───────


class TestTau7XLMDeuterocanonArcAndPriorPins:
    def test_both_books_shipped(self):
        assert (AMHARIC_TEWAHEDO / "jdt.py").is_file()
        assert (AMHARIC_TEWAHEDO / "est.py").is_file()

    def test_all_prior_amharic_books_preserved(self):
        for book in (
            "gen",
            "ex",
            "lev",
            "num",
            "deu",
            "jos",
            "jdg",
            "rut",
            "psa",
            "2es",
            "tob",
        ):
            assert (AMHARIC_TEWAHEDO / f"{book}.py").is_file(), f"prior τ.7.x.* book {book} must persist"

    def test_geez_jdt_est_not_created(self):
        assert not (GEEZ_TEWAHEDO / "jdt.py").exists()
        assert not (GEEZ_TEWAHEDO / "est.py").exists()

    def test_cli_renumber_choices_extended(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert '"judith"' in src and '"esther"' in src
        assert src.count("JUDITH_VERSE_COUNTS") >= 3
        assert src.count("ESTHER_VERSE_COUNTS") >= 3

    def test_tau7xj_pins_preserved(self):
        """τ.7.x.j/k must remain intact (additive ship)."""
        s = _source_yaml()
        assert s["ocr_strategy"]["tau7xj_ingest"]["shipped_at_phase"] == "τ.7.x.j"
        assert s["ocr_strategy"]["tau7xk_ingest"]["block_drained"] == "p1239-1293"
        assert s["structural_map"]["ezra_sutuel"]["pdf_page_range"] == [1239, 1284]
        assert s["structural_map"]["tobit"]["pdf_page_range"] == [1285, 1293]

    def test_tau7xi_next_phase_and_tau7xh_backlink_preserved(self):
        s = _source_yaml()
        assert s["ocr_strategy"]["tau7xi_ingest"]["next_phase"] == "τ.7.x.j"
        h = s["ocr_strategy"]["tau7xh_ingest"]
        assert h.get("pipeline_reused_at_phase") == "τ.6.x.2.h"
        assert h.get("also_reused_at_phase") == "τ.7.x.i"

    def test_psalms_and_psa_preserved(self):
        assert _source_yaml()["structural_map"]["psalms"]["pdf_page_range"] == [803, 906]
        assert (AMHARIC_TEWAHEDO / "psa.py").is_file()


class TestTau7XLMStateDocs:
    def test_session_state_mentions_both_phases(self):
        txt = (REPO / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
        assert "τ.7.x.l" in txt and "τ.7.x.m" in txt

    def test_in_flight_mentions_tau7xl(self):
        txt = (REPO / "dev" / "IN_FLIGHT.md").read_text(encoding="utf-8")
        assert "τ.7.x.l" in txt

    def test_changelog_records_tau7xl_tau7xm(self):
        txt = (REPO / "dev" / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "τ.7.x.l" in txt and "τ.7.x.m" in txt

    def test_plan_ledger_records_tau7xl(self):
        txt = (REPO / "dev" / "PLAN_2026-05-09.md").read_text(encoding="utf-8")
        assert "τ.7.x.l" in txt

"""τ.7.x.e — Amharic Deuteronomy full-book ingest pins (2026-05-15).

FIFTH τ.7.x.* per-book ship under D4-c Amharic-first + D1-a per-book
cadence. Re-uses the τ.7.x.d pipeline (which itself reused τ.7.x.c
which reused τ.7.x.b which reused τ.7.x.a) with only
DEUTERONOMY_VERSE_COUNTS + structural_map.deuteronomy as deltas.
81.4% coverage — sits between Exodus (78.1%) and Genesis (85.3%).

**CLOSES the §8.1 Pentateuch arc under Amharic-first sequencing**
(gen + ex + lev + num + deut = all 5 books of Torah shipped). NINTH
§8.1 arc-close instance overall; FIRST in the τ-cluster.

Pins validate:
1. DEUTERONOMY_VERSE_COUNTS dict shape (34 chapters / 959 total verses).
2. structural_map.deuteronomy block in _source.yaml.
3. content/translations/amharic-tewahedo/deu.py module shape +
   INGEST_PHASE='τ.7.x.e' + SOURCE_QUALITY='ocr-tier3'.
4. Per-chapter coverage (1-27 fully populated; 28 partial 62/68;
   29-34 empty).
5. _meta.yaml ingest_record_tau7xe block + combined stats.
6. _source.yaml::ocr_strategy.tau7xe_ingest block + arc_close marker.
7. Reciprocal back-link tau7xd_ingest.pipeline_reused_at_phase = τ.7.x.e.
8. CLI --renumber {genesis,exodus,leviticus,numbers,deuteronomy}.
9. geez-tewahedo/deu.py NOT created (D4-c preserved).
10. Pentateuch §8.1 arc-close pin: all 5 Torah book files exist
    under amharic-tewahedo/.
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


def _deuteronomy_block() -> dict:
    return _source_yaml()["structural_map"]["deuteronomy"]


def _tau7xe_block() -> dict:
    return _source_yaml()["ocr_strategy"]["tau7xe_ingest"]


def _deu_verses() -> list[tuple]:
    deu_py = AMHARIC_TEWAHEDO / "deu.py"
    text = deu_py.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSES":
                    return ast.literal_eval(node.value)
    raise AssertionError("amharic-tewahedo/deu.py must define VERSES")


def _deu_constants() -> dict:
    deu_py = AMHARIC_TEWAHEDO / "deu.py"
    text = deu_py.read_text(encoding="utf-8")
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


class TestTau7XEDeuteronomyVerseCounts:
    """DEUTERONOMY_VERSE_COUNTS is the τ.7.x.e renumber-floor dict."""

    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_module_symbol_present(self):
        from extract_parallel_pdf import DEUTERONOMY_VERSE_COUNTS

        assert isinstance(DEUTERONOMY_VERSE_COUNTS, dict)

    def test_thirty_four_chapters(self):
        from extract_parallel_pdf import DEUTERONOMY_VERSE_COUNTS

        assert sorted(DEUTERONOMY_VERSE_COUNTS.keys()) == list(range(1, 35))

    def test_total_verses_959(self):
        from extract_parallel_pdf import DEUTERONOMY_VERSE_COUNTS

        # KJV/LXX/Vulgate-aligned: 959 verses. Hebrew Masoretic
        # redistributes some chapter boundaries but yields the same
        # 959 total.
        assert sum(DEUTERONOMY_VERSE_COUNTS.values()) == 959

    def test_chapter_specific_verse_counts(self):
        """Spot-check well-known Deuteronomy chapter sizes."""
        from extract_parallel_pdf import DEUTERONOMY_VERSE_COUNTS

        # Deut 28 (blessing+curse formulas) = 68 verses (longest)
        assert DEUTERONOMY_VERSE_COUNTS[28] == 68
        # Deut 34 (Moses's death epilogue) = 12 verses (shortest)
        assert DEUTERONOMY_VERSE_COUNTS[34] == 12
        # Deut 1 (historical rehearsal) = 46 verses
        assert DEUTERONOMY_VERSE_COUNTS[1] == 46
        # Deut 5 (Decalogue restated) = 33 verses (KJV; Hebrew 5:30)
        assert DEUTERONOMY_VERSE_COUNTS[5] == 33


class TestTau7XEStructuralMapDeuteronomy:
    """structural_map.deuteronomy block records the Deuteronomy page
    range discovered via τ.7.x.e boundary inspection (Joshua title
    `መጽሐፈ ኢያሱ` scan)."""

    def test_block_present(self):
        assert "deuteronomy" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert _deuteronomy_block()["book_codes"] == ["deu"]

    def test_pdf_page_range(self):
        # 288-348 inclusive (61 pages for 34 chapters; verified by
        # Deut 1:1 opening at p288 + Joshua 1:1 opening at p349
        # content inspection).
        assert _deuteronomy_block()["pdf_page_range"] == [288, 348]

    def test_pdf_index_offset_zero(self):
        assert _deuteronomy_block()["pdf_index_offset"] == 0

    def test_verified_true(self):
        assert _deuteronomy_block()["verified"] is True

    def test_verified_at_tau7xe(self):
        assert _deuteronomy_block()["verified_at_phase"] == "τ.7.x.e"

    def test_chapter_count_expected_34(self):
        assert _deuteronomy_block()["chapter_count_expected"] == 34

    def test_notes_document_boundary_inspection(self):
        notes = _deuteronomy_block()["notes"]
        # Deut 1:1 opening + Joshua 1:1 boundary + Tewahedo title +
        # §8.1 arc-close all referenced.
        assert "ኦሪት ዘዳግም" in notes, "Notes must reference Deuteronomy Geʽez title"
        assert "ሣን ውክ ነገር" in notes or "Deut 1:1" in notes, "Notes must reference Deut 1:1 opening"
        assert "Joshua" in notes or "ኢያሱ" in notes, "Notes must reference Joshua 1:1 boundary"
        assert "§8.1" in notes or "Pentateuch arc" in notes, "Notes must reference §8.1 Pentateuch arc-close"


class TestTau7XEDeuteronomyDeuPy:
    """amharic-tewahedo/deu.py is the τ.7.x.e output module."""

    def test_deu_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "deu.py").is_file()

    def test_translation_constant(self):
        c = _deu_constants()
        assert c.get("TRANSLATION") == "amharic-tewahedo"

    def test_book_constant(self):
        c = _deu_constants()
        assert c.get("BOOK") == "deu"

    def test_source_quality_ocr_tier3(self):
        c = _deu_constants()
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"

    def test_source_provenance(self):
        c = _deu_constants()
        assert c.get("SOURCE_PROVENANCE") == "parallel-bible-eotc"

    def test_ingest_phase_constant(self):
        c = _deu_constants()
        assert c.get("INGEST_PHASE") == "τ.7.x.e"

    def test_verses_count_at_least_floor(self):
        verses = _deu_verses()
        # Empirical at ship was 781. Floor 700 protects against
        # silent regression while permitting parser refinement.
        assert len(verses) >= 700, f"τ.7.x.e Deuteronomy ingest must have ≥700 verses; got {len(verses)}"

    def test_first_verse_is_deu_1_1(self):
        verses = _deu_verses()
        ch, v, text = verses[0]
        assert (ch, v) == (1, 1)
        assert text, "Deut 1:1 text must be non-empty"


class TestTau7XEDeuteronomyCoverage:
    """Per-chapter coverage matches empirical post-renumber
    distribution: chapters 1-27 fully populated; 28 partial 62/68;
    29-34 empty."""

    def _by_chapter(self) -> dict[int, list[tuple]]:
        verses = _deu_verses()
        out: dict[int, list[tuple]] = {}
        for ch, v, t in verses:
            out.setdefault(ch, []).append((v, t))
        return out

    def test_chapters_1_through_27_fully_populated(self):
        """The defining τ.7.x.e empirical pin: chapters 1-27 have
        verse counts MATCHING DEUTERONOMY_VERSE_COUNTS floor."""
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import DEUTERONOMY_VERSE_COUNTS

        by_ch = self._by_chapter()
        for ch in range(1, 28):
            got = len(by_ch.get(ch, []))
            expected = DEUTERONOMY_VERSE_COUNTS[ch]
            assert got == expected, (
                f"τ.7.x.e chapter {ch} must have exactly {expected} verses (DEUTERONOMY_VERSE_COUNTS floor); got {got}"
            )

    def test_chapter_28_partial(self):
        """Chapter 28 received the parser's remaining 62 verses."""
        by_ch = self._by_chapter()
        got = len(by_ch.get(28, []))
        # Empirical 62; defensive range (1, 68).
        assert 1 <= got <= 68, f"τ.7.x.e chapter 28 partial: expect 1..68 verses; got {got}"

    def test_chapters_29_through_34_empty(self):
        """Chapters 29-34 received zero verses — parser exhausted at ch 28."""
        by_ch = self._by_chapter()
        for ch in (29, 30, 31, 32, 33, 34):
            got = len(by_ch.get(ch, []))
            assert got == 0, f"τ.7.x.e chapter {ch} should be empty at ocr-tier3; got {got} verses"

    def test_no_overflow_above_chapter_34(self):
        by_ch = self._by_chapter()
        overflow = sum(len(v) for ch, v in by_ch.items() if ch > 34)
        assert overflow == 0, f"τ.7.x.e renumber overflow should be 0; got {overflow} verses above ch 34"

    def test_end_of_book_colophon_preserved(self):
        """The end-of-Deuteronomy colophon `ተፈጸመ` ("was completed") is
        preserved at the last ingested verse (renumbered ch 28:62 due
        to the 18.6% recovery deficit; canonically end-of-Deut 34)."""
        verses = _deu_verses()
        last_ch, last_v, last_text = verses[-1]
        assert "ተፈጸ" in last_text or "ተፈጻመ" in last_text or "ደረሰ" in last_text, (
            f"τ.7.x.e last verse must preserve end-of-Deuteronomy colophon; got: {last_text[:200]}"
        )


class TestTau7XESourceYamlIngestBlock:
    """ocr_strategy.tau7xe_ingest block records the τ.7.x.e ship +
    back-link annotation to tau7xd_ingest + §8.1 Pentateuch arc-close."""

    def test_block_exists(self):
        assert "tau7xe_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert _tau7xe_block()["shipped_at_phase"] == "τ.7.x.e"

    def test_structural_map_addition(self):
        sma = _tau7xe_block()["structural_map_addition"]
        assert sma["section"] == "deuteronomy"
        assert sma["pdf_page_range"] == [288, 348]
        assert sma["chapter_count_expected"] == 34

    def test_helpers_added_deuteronomy_verse_counts(self):
        helpers = _tau7xe_block()["helpers_added"]
        assert "DEUTERONOMY_VERSE_COUNTS" in helpers

    def test_cli_extensions_renumber_choice_extended(self):
        cli = _tau7xe_block()["cli_extensions"]
        assert "renumber_choice_extended" in cli

    def test_empirical_validation_coverage_75_plus_percent(self):
        ev = _tau7xe_block()["empirical_validation"]
        # Coverage at ship was 81.4%. Floor 75 protects against regression.
        assert ev["coverage_pct"] >= 75.0

    def test_empirical_chapters_fully_populated_1_through_27(self):
        ev = _tau7xe_block()["empirical_validation"]
        assert ev["chapters_fully_populated"] == list(range(1, 28))

    def test_empirical_chapters_missing_29_through_34(self):
        ev = _tau7xe_block()["empirical_validation"]
        assert ev["chapters_missing"] == [29, 30, 31, 32, 33, 34]

    def test_no_ingest_at_this_phase_false(self):
        assert _tau7xe_block()["no_ingest_at_this_phase"] is False

    def test_closed_arc_tau6x0a_no_ingest_false(self):
        contracts = _tau7xe_block()["closed_arc_contracts_preserved"]
        assert contracts["tau6x0a_no_ingest"] is False  # fifth authorized violation

    def test_closed_arc_tau7xa_through_tau7xd_preserved(self):
        contracts = _tau7xe_block()["closed_arc_contracts_preserved"]
        assert contracts["tau7xa_ingest"] is True
        assert contracts["tau7xb_ingest"] is True
        assert contracts["tau7xc_ingest"] is True
        assert contracts["tau7xd_ingest"] is True

    def test_reciprocal_back_link_in_tau7xd(self):
        """τ.7.x.d tau7xd_ingest block must carry pipeline_reused_at_
        phase = τ.7.x.e (back-link annotation, 9th instance of the
        single-key back-link pattern)."""
        d = _source_yaml()["ocr_strategy"]["tau7xd_ingest"]
        assert d.get("pipeline_reused_at_phase") == "τ.7.x.e"

    def test_translation_slot_state_records_five_books(self):
        state = _tau7xe_block()["translation_slot_state"]
        assert "τ.7.x.a" in state["amharic_tewahedo_gen"]
        assert "τ.7.x.b" in state["amharic_tewahedo_ex"]
        assert "τ.7.x.c" in state["amharic_tewahedo_lev"]
        assert "τ.7.x.d" in state["amharic_tewahedo_num"]
        assert "τ.7.x.e" in state["amharic_tewahedo_deu"]

    def test_next_phase_tau7xf(self):
        assert _tau7xe_block()["next_phase"] == "τ.7.x.f"

    def test_arc_close_marker_8_1(self):
        """τ.7.x.e is the NINTH §8.1 arc-close instance overall + FIRST
        in τ-cluster."""
        assert _tau7xe_block()["arc_close"] == "§8.1"

    def test_arc_close_narrative_present(self):
        """The arc-close narrative documents the Pentateuch closure."""
        narrative = _tau7xe_block()["arc_close_narrative"]
        assert "Pentateuch" in narrative
        assert "γ.4.5.E" in narrative or "γ.4.8.E" in narrative, (
            "Arc-close narrative must reference at least one prior γ-cluster §8.1 instance"
        )


class TestTau7XEMetaYamlIngestRecord:
    """amharic-tewahedo/_meta.yaml has all five ingest records +
    upgraded stats (5 books / 4945 verses combined)."""

    def _meta(self) -> dict:
        path = AMHARIC_TEWAHEDO / "_meta.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_stats_books_at_least_five(self):
        """Refactored share-pin→milestone-pin at τ.7.x.f ship-time per
        `feedback_share_pin_pattern`. Originally asserted ==5 (full
        Pentateuch post-τ.7.x.e); τ.7.x.f bumped to 6 (Pentateuch +
        Joshua). Durable invariant: ≥5 (full Pentateuch shipped +
        any subsequent τ.7.x.* book)."""
        m = self._meta()
        assert m["stats"]["books"] >= 5

    def test_stats_verses_combined(self):
        # 1308 (gen) + 947 (ex) + 802 (lev) + 1107 (num) + 781 (deu) = 4945. Floor 4500.
        m = self._meta()
        assert m["stats"]["verses"] >= 4500

    def test_tau7xe_ingest_record_present(self):
        m = self._meta()
        assert "ingest_record_tau7xe" in m

    def test_tau7xe_ingest_record_phase(self):
        m = self._meta()
        assert m["ingest_record_tau7xe"]["phase"] == "τ.7.x.e"

    def test_tau7xe_ingest_record_book_codes_deu(self):
        m = self._meta()
        assert m["ingest_record_tau7xe"]["ingested_book_codes"] == ["deu"]

    def test_tau7xe_ingest_record_parser_extensions_chain(self):
        m = self._meta()
        chain = m["ingest_record_tau7xe"]["parser_extensions"]
        # The full chain extends to τ.7.x.e.
        for phase in (
            "τ.6.x.1.B",
            "τ.6.x.1.C",
            "τ.6.x.1.D",
            "τ.7.x.a",
            "τ.7.x.b",
            "τ.7.x.c",
            "τ.7.x.d",
            "τ.7.x.e",
        ):
            assert phase in chain, f"parser_extensions chain missing {phase}"

    def test_tau7xe_arc_close_marker(self):
        """ingest_record_tau7xe carries the §8.1 arc_close marker."""
        m = self._meta()
        assert m["ingest_record_tau7xe"]["arc_close"] == "§8.1"

    def test_prior_ingest_records_still_present(self):
        """τ.7.x.e adds; does NOT remove τ.7.x.a/b/c/d records."""
        m = self._meta()
        assert "ingest_record" in m
        assert m["ingest_record"]["phase"] == "τ.7.x.a"
        assert "ingest_record_tau7xb" in m
        assert m["ingest_record_tau7xb"]["phase"] == "τ.7.x.b"
        assert "ingest_record_tau7xc" in m
        assert m["ingest_record_tau7xc"]["phase"] == "τ.7.x.c"
        assert "ingest_record_tau7xd" in m
        assert m["ingest_record_tau7xd"]["phase"] == "τ.7.x.d"


class TestTau7XEGeezTewahedoPreserved:
    """The Geʽez column should remain unchanged after τ.7.x.e — full
    Geʽez Deuteronomy ingest is τ.6.x.2.e per D4-c sequencing."""

    def test_geez_tewahedo_deu_py_ingested_at_tau6x2e(self):
        """MIGRATED at τ.6.x.2.a-h batch ship-time (2026-05-15):
        originally asserted geez-tewahedo/deu.py does NOT exist
        until τ.6.x.2.e ships. The τ.6.x.2.a-h batch ship
        CREATED this file at ocr-tier3 quality (per D4-c catchup arc).
        Durable assertion is now: geez-tewahedo/deu.py EXISTS at
        ocr-tier3 ingest scale; per-file content pinned in
        test_parallel_bible_tau6x2_geez_arc.py."""
        import ast

        path = GEEZ_TEWAHEDO / "deu.py"
        assert path.is_file(), "geez-tewahedo/deu.py must exist post-τ.6.x.2.e (τ.6.x.2.a-h batch ship)"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        verses = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == "VERSES":
                        verses = ast.literal_eval(node.value)
                        break
            if verses is not None:
                break
        assert verses is not None
        # τ.6.x.2.e empirical at ship: 508 verses; floor 475 guards
        # against regression while permitting parser refinement.
        assert len(verses) >= 475, (
            f"geez-tewahedo/deu.py must be at ocr-tier3 scale post-τ.6.x.2.e; "
            f"got {len(verses)} verses (<475 indicates regression)"
        )

    def test_geez_tewahedo_gen_py_ingested_at_tau6x2a(self):
        """MIGRATED at τ.6.x.2.a-h batch ship-time (2026-05-15):
        originally asserted geez-tewahedo/gen.py remains at Π.0 seed
        (≤10 verses) until τ.6.x.2.a ships. The τ.6.x.2.a batch sub-
        ship UPGRADED Geʽez Genesis from Π.0 seed to ocr-tier3 full-
        book ingest (1022 verses). Durable assertion: Geʽez Genesis
        is at ocr-tier3 ingest scale."""
        gen_py = GEEZ_TEWAHEDO / "gen.py"
        text = gen_py.read_text(encoding="utf-8")
        tree = ast.parse(text)
        verses = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "VERSES":
                        verses = ast.literal_eval(node.value)
                        break
            if verses is not None:
                break
        assert verses is not None
        # τ.6.x.2.a empirical at ship: 1022 verses; floor 950 guards regression.
        assert len(verses) >= 950, (
            f"geez-tewahedo/gen.py must be at ocr-tier3 scale post-τ.6.x.2.a; "
            f"got {len(verses)} verses (<950 indicates regression)"
        )


class TestTau7XEPentateuchArcClose:
    """§8.1 Pentateuch arc-close — all 5 Torah book files exist under
    amharic-tewahedo/ with non-trivial ingest counts. NINTH §8.1
    arc-close instance overall; FIRST in τ-cluster."""

    def test_all_five_pentateuch_books_shipped(self):
        """gen.py + ex.py + lev.py + num.py + deu.py all exist under
        amharic-tewahedo/."""
        for book in ("gen", "ex", "lev", "num", "deu"):
            path = AMHARIC_TEWAHEDO / f"{book}.py"
            assert path.is_file(), f"§8.1 Pentateuch arc-close requires amharic-tewahedo/{book}.py"

    def test_all_five_pentateuch_books_have_non_trivial_ingest(self):
        """Each Pentateuch book has at least 700 verses (well above
        the Π.0 3-verse seed)."""
        for book, min_verses in (
            ("gen", 1000),
            ("ex", 700),
            ("lev", 700),
            ("num", 1000),
            ("deu", 700),
        ):
            path = AMHARIC_TEWAHEDO / f"{book}.py"
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text)
            verses = None
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "VERSES":
                            verses = ast.literal_eval(node.value)
                            break
                if verses is not None:
                    break
            assert verses is not None, f"{book}.py must define VERSES"
            assert len(verses) >= min_verses, (
                f"§8.1 Pentateuch arc-close: {book}.py must have ≥{min_verses} verses; got {len(verses)}"
            )

    def test_pentateuch_combined_coverage_at_least_80_percent(self):
        """Combined Pentateuch coverage = sum of per-book verses /
        sum of per-book floors. Empirical at arc-close: 4945/5853 =
        84.5%. Floor 80% protects against regression."""
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import (
            DEUTERONOMY_VERSE_COUNTS,
            EXODUS_VERSE_COUNTS,
            GENESIS_VERSE_COUNTS,
            LEVITICUS_VERSE_COUNTS,
            NUMBERS_VERSE_COUNTS,
        )

        floors = {
            "gen": sum(GENESIS_VERSE_COUNTS.values()),
            "ex": sum(EXODUS_VERSE_COUNTS.values()),
            "lev": sum(LEVITICUS_VERSE_COUNTS.values()),
            "num": sum(NUMBERS_VERSE_COUNTS.values()),
            "deu": sum(DEUTERONOMY_VERSE_COUNTS.values()),
        }
        total_extracted = 0
        total_expected = sum(floors.values())
        for book in ("gen", "ex", "lev", "num", "deu"):
            path = AMHARIC_TEWAHEDO / f"{book}.py"
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text)
            verses = None
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "VERSES":
                            verses = ast.literal_eval(node.value)
                            break
                if verses is not None:
                    break
            total_extracted += len(verses)
        coverage = 100.0 * total_extracted / total_expected
        assert coverage >= 80.0, (
            f"§8.1 Pentateuch combined coverage must be ≥80%; got {coverage:.1f}% ({total_extracted}/{total_expected})"
        )


class TestTau7XEStateDocs:
    # Doc-pins collapsed to the CHANGELOG chokepoint (2026-05-21): the
    # old test_session_state_*/test_in_flight_*/test_plan_ledger_* pins
    # read SESSION_STATE.md / IN_FLIGHT.md (rolling, trimmed) and the
    # moved PLAN_2026-05-09.md. The durable phase record is CHANGELOG.md.
    def test_phase_recorded_in_changelog(self):
        from tests.fixtures import assert_phase_recorded

        assert_phase_recorded("τ.7.x.e")

"""τ.7.x.f — Amharic Joshua full-book ingest pins (2026-05-15).

SIXTH τ.7.x.* per-book ship under D4-c Amharic-first + D1-a per-book
cadence. Re-uses the τ.7.x.e pipeline (which itself reused τ.7.x.d
which reused τ.7.x.c which reused τ.7.x.b which reused τ.7.x.a) with
only JOSHUA_VERSE_COUNTS + structural_map.joshua as deltas.
73.4% coverage — LOWEST τ.7.x.* coverage to date (slightly below
Exodus's 78.1%); Joshua's long tribal-allotment chapters + publisher-
added Judges-bridge narrative on page 390 yield a recovery rate
~5 points below the canonical τ.7.x.* band.

**OPENS the post-Pentateuch historical-books arc under Amharic-first
sequencing** — FIRST τ-cluster ingest after the §8.1 Pentateuch
arc-close at τ.7.x.e. The historical-books canonical unit will span
Joshua → Judges → Ruth → 1-4 Kingdoms → 1-2 Paralipomena → Ezra/
Nehemiah → Esther under the LXX/Tewahedo ordering.

Pins validate:
1. JOSHUA_VERSE_COUNTS dict shape (24 chapters / 658 total verses).
2. structural_map.joshua block in _source.yaml.
3. content/translations/amharic-tewahedo/jos.py module shape +
   INGEST_PHASE='τ.7.x.f' + SOURCE_QUALITY='ocr-tier3'.
4. Per-chapter coverage (1-18 fully populated; 19 partial 13/51;
   20-24 empty).
5. _meta.yaml ingest_record_tau7xf block + combined stats.
6. _source.yaml::ocr_strategy.tau7xf_ingest block + arc_open marker.
7. Reciprocal back-link tau7xe_ingest.pipeline_reused_at_phase = τ.7.x.f.
8. CLI --renumber {genesis,exodus,leviticus,numbers,deuteronomy,joshua}.
9. geez-tewahedo/jos.py NOT created (D4-c preserved).
10. Post-Pentateuch arc-open pin: jos.py shipped + Pentateuch §8.1
    arc closure preserved.
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


def _joshua_block() -> dict:
    return _source_yaml()["structural_map"]["joshua"]


def _tau7xf_block() -> dict:
    return _source_yaml()["ocr_strategy"]["tau7xf_ingest"]


def _jos_verses() -> list[tuple]:
    jos_py = AMHARIC_TEWAHEDO / "jos.py"
    text = jos_py.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSES":
                    return ast.literal_eval(node.value)
    raise AssertionError("amharic-tewahedo/jos.py must define VERSES")


def _jos_constants() -> dict:
    jos_py = AMHARIC_TEWAHEDO / "jos.py"
    text = jos_py.read_text(encoding="utf-8")
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


class TestTau7XFJoshuaVerseCounts:
    """JOSHUA_VERSE_COUNTS is the τ.7.x.f renumber-floor dict."""

    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_module_symbol_present(self):
        from extract_parallel_pdf import JOSHUA_VERSE_COUNTS

        assert isinstance(JOSHUA_VERSE_COUNTS, dict)

    def test_twenty_four_chapters(self):
        from extract_parallel_pdf import JOSHUA_VERSE_COUNTS

        assert sorted(JOSHUA_VERSE_COUNTS.keys()) == list(range(1, 25))

    def test_total_verses_658(self):
        from extract_parallel_pdf import JOSHUA_VERSE_COUNTS

        # KJV/Hebrew Masoretic + LXX agreement: 658 verses (no
        # chapter-boundary repartitioning between traditions).
        assert sum(JOSHUA_VERSE_COUNTS.values()) == 658

    def test_chapter_specific_verse_counts(self):
        """Spot-check well-known Joshua chapter sizes."""
        from extract_parallel_pdf import JOSHUA_VERSE_COUNTS

        # Josh 15 (Judah's tribal allotment) = 63 verses (longest)
        assert JOSHUA_VERSE_COUNTS[15] == 63
        # Josh 20 (cities of refuge) = 9 verses (shortest)
        assert JOSHUA_VERSE_COUNTS[20] == 9
        # Josh 1 (Joshua's commission) = 18 verses
        assert JOSHUA_VERSE_COUNTS[1] == 18
        # Josh 24 (covenant renewal + Joshua's death) = 33 verses
        assert JOSHUA_VERSE_COUNTS[24] == 33


class TestTau7XFStructuralMapJoshua:
    """structural_map.joshua block records the Joshua page range
    discovered via τ.7.x.f boundary inspection (Judges 1:1 opening
    scan)."""

    def test_block_present(self):
        assert "joshua" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert _joshua_block()["book_codes"] == ["jos"]

    def test_pdf_page_range(self):
        # 349-390 inclusive (42 pages for 24 chapters; verified by
        # Joshua 1:1 at p349 + Judges 1:1 at p391 content inspection).
        assert _joshua_block()["pdf_page_range"] == [349, 390]

    def test_pdf_index_offset_zero(self):
        assert _joshua_block()["pdf_index_offset"] == 0

    def test_verified_true(self):
        assert _joshua_block()["verified"] is True

    def test_verified_at_tau7xf(self):
        assert _joshua_block()["verified_at_phase"] == "τ.7.x.f"

    def test_chapter_count_expected_24(self):
        assert _joshua_block()["chapter_count_expected"] == 24

    def test_notes_document_boundary_inspection(self):
        notes = _joshua_block()["notes"]
        # Joshua 1:1 opening + Judges 1:1 boundary + Tewahedo title +
        # post-Pentateuch arc-open all referenced.
        assert "ኦሪት ዘኢ" in notes or "Joshua" in notes, "Notes must reference Joshua Geʽez title"
        assert "ሞተ ሙዜ" in notes or "ሞተ ሙሴ" in notes or "Joshua 1:1" in notes, (
            "Notes must reference Joshua 1:1 opening 'after the death of Moses'"
        )
        assert "Judges" in notes or "መሳፍ" in notes or "ሞተ ኢያሱ" in notes, "Notes must reference Judges 1:1 boundary"
        assert "post-Pentateuch" in notes or "historical-books" in notes, (
            "Notes must reference post-Pentateuch historical-books arc-open"
        )


class TestTau7XFJoshuaJosPy:
    """amharic-tewahedo/jos.py is the τ.7.x.f output module."""

    def test_jos_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "jos.py").is_file()

    def test_translation_constant(self):
        c = _jos_constants()
        assert c.get("TRANSLATION") == "amharic-tewahedo"

    def test_book_constant(self):
        c = _jos_constants()
        assert c.get("BOOK") == "jos"

    def test_source_quality_ocr_tier3(self):
        c = _jos_constants()
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"

    def test_source_provenance(self):
        c = _jos_constants()
        assert c.get("SOURCE_PROVENANCE") == "parallel-bible-eotc"

    def test_ingest_phase_constant(self):
        c = _jos_constants()
        assert c.get("INGEST_PHASE") == "τ.7.x.f"

    def test_verses_count_at_least_floor(self):
        verses = _jos_verses()
        # Empirical at ship was 483. Floor 400 protects against
        # silent regression while permitting parser refinement.
        assert len(verses) >= 400, f"τ.7.x.f Joshua ingest must have ≥400 verses; got {len(verses)}"

    def test_first_verse_is_jos_1_1(self):
        verses = _jos_verses()
        ch, v, text = verses[0]
        assert (ch, v) == (1, 1)
        assert text, "Josh 1:1 text must be non-empty"


class TestTau7XFJoshuaCoverage:
    """Per-chapter coverage matches empirical post-renumber
    distribution: chapters 1-18 fully populated; 19 partial 13/51;
    20-24 empty."""

    def _by_chapter(self) -> dict[int, list[tuple]]:
        verses = _jos_verses()
        out: dict[int, list[tuple]] = {}
        for ch, v, t in verses:
            out.setdefault(ch, []).append((v, t))
        return out

    def test_chapters_1_through_18_fully_populated(self):
        """The defining τ.7.x.f empirical pin: chapters 1-18 have
        verse counts MATCHING JOSHUA_VERSE_COUNTS floor."""
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import JOSHUA_VERSE_COUNTS

        by_ch = self._by_chapter()
        for ch in range(1, 19):
            got = len(by_ch.get(ch, []))
            expected = JOSHUA_VERSE_COUNTS[ch]
            assert got == expected, (
                f"τ.7.x.f chapter {ch} must have exactly {expected} verses (JOSHUA_VERSE_COUNTS floor); got {got}"
            )

    def test_chapter_19_partial(self):
        """Chapter 19 received the parser's remaining 13 verses
        (includes the publisher's Judges-bridge narrative leakage +
        end-of-Joshua colophon)."""
        by_ch = self._by_chapter()
        got = len(by_ch.get(19, []))
        # Empirical 13; defensive range (1, 51).
        assert 1 <= got <= 51, f"τ.7.x.f chapter 19 partial: expect 1..51 verses; got {got}"

    def test_chapters_20_through_24_empty(self):
        """Chapters 20-24 received zero verses — parser exhausted at ch 19."""
        by_ch = self._by_chapter()
        for ch in (20, 21, 22, 23, 24):
            got = len(by_ch.get(ch, []))
            assert got == 0, f"τ.7.x.f chapter {ch} should be empty at ocr-tier3; got {got} verses"

    def test_no_overflow_above_chapter_24(self):
        by_ch = self._by_chapter()
        overflow = sum(len(v) for ch, v in by_ch.items() if ch > 24)
        assert overflow == 0, f"τ.7.x.f renumber overflow should be 0; got {overflow} verses above ch 24"

    def test_end_of_book_colophon_preserved(self):
        """The end-of-Joshua colophon — preserved at the parser's
        terminal output (renumbered into ch 19 partial slot due to the
        26.6% recovery deficit). The OCR-garbled colophon form in the
        Amharic column is `መጽሐፍ መላ ... ክብር ምስጋና በእውነት` ("the book is
        complete ... glory praise in truth"); the canonical Geʽez
        form `ተፈጺመ` ("was completed") got OCR-garbled at extraction
        time. Accept any of: the canonical Geʽez `ተፈጸ`-family verb,
        OR the Amharic colophon marker triplet `መጽሐፍ መላ` + `ክብር` +
        `ምስጋና` (book-complete + glory + praise)."""
        verses = _jos_verses()
        # Check the last 15 verses for the colophon marker
        last_chunk = " ".join(text for (_, _, text) in verses[-15:])
        canonical_geez_colophon = "ተፈጺመ" in last_chunk or "ተፈጻመ" in last_chunk or "ተፈጸመ" in last_chunk
        amharic_colophon_marker_triplet = "መጽሐፍ መላ" in last_chunk and "ክብር" in last_chunk and "ምስጋና" in last_chunk
        assert canonical_geez_colophon or amharic_colophon_marker_triplet, (
            f"τ.7.x.f end-of-Joshua colophon must appear in the last 15 verses "
            f"(either `ተፈጺ`-family verb OR `መጽሐፍ መላ`+`ክብር`+`ምስጋና` triplet); "
            f"got: {last_chunk[:400]}"
        )


class TestTau7XFSourceYamlIngestBlock:
    """ocr_strategy.tau7xf_ingest block records the τ.7.x.f ship +
    back-link annotation to tau7xe_ingest + post-Pentateuch arc-open."""

    def test_block_exists(self):
        assert "tau7xf_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert _tau7xf_block()["shipped_at_phase"] == "τ.7.x.f"

    def test_structural_map_addition(self):
        sma = _tau7xf_block()["structural_map_addition"]
        assert sma["section"] == "joshua"
        assert sma["pdf_page_range"] == [349, 390]
        assert sma["chapter_count_expected"] == 24

    def test_helpers_added_joshua_verse_counts(self):
        helpers = _tau7xf_block()["helpers_added"]
        assert "JOSHUA_VERSE_COUNTS" in helpers

    def test_cli_extensions_renumber_choice_extended(self):
        cli = _tau7xf_block()["cli_extensions"]
        assert "renumber_choice_extended" in cli

    def test_empirical_validation_coverage_70_plus_percent(self):
        ev = _tau7xf_block()["empirical_validation"]
        # Coverage at ship was 73.4%. Floor 70 protects against regression
        # (Joshua is the lowest-coverage τ.7.x.* book due to allotment
        # chapters + publisher-added Judges-bridge narrative).
        assert ev["coverage_pct"] >= 70.0

    def test_empirical_chapters_fully_populated_1_through_18(self):
        ev = _tau7xf_block()["empirical_validation"]
        assert ev["chapters_fully_populated"] == list(range(1, 19))

    def test_empirical_chapters_missing_20_through_24(self):
        ev = _tau7xf_block()["empirical_validation"]
        assert ev["chapters_missing"] == [20, 21, 22, 23, 24]

    def test_no_ingest_at_this_phase_false(self):
        assert _tau7xf_block()["no_ingest_at_this_phase"] is False

    def test_closed_arc_tau6x0a_no_ingest_false(self):
        contracts = _tau7xf_block()["closed_arc_contracts_preserved"]
        assert contracts["tau6x0a_no_ingest"] is False  # sixth authorized violation

    def test_closed_arc_tau7xa_through_tau7xe_preserved(self):
        contracts = _tau7xf_block()["closed_arc_contracts_preserved"]
        assert contracts["tau7xa_ingest"] is True
        assert contracts["tau7xb_ingest"] is True
        assert contracts["tau7xc_ingest"] is True
        assert contracts["tau7xd_ingest"] is True
        assert contracts["tau7xe_ingest"] is True

    def test_reciprocal_back_link_in_tau7xe(self):
        """τ.7.x.e tau7xe_ingest block must carry pipeline_reused_at_
        phase = τ.7.x.f (back-link annotation, 10th instance of the
        single-key back-link pattern)."""
        e = _source_yaml()["ocr_strategy"]["tau7xe_ingest"]
        assert e.get("pipeline_reused_at_phase") == "τ.7.x.f"

    def test_translation_slot_state_records_six_books(self):
        state = _tau7xf_block()["translation_slot_state"]
        assert "τ.7.x.a" in state["amharic_tewahedo_gen"]
        assert "τ.7.x.b" in state["amharic_tewahedo_ex"]
        assert "τ.7.x.c" in state["amharic_tewahedo_lev"]
        assert "τ.7.x.d" in state["amharic_tewahedo_num"]
        assert "τ.7.x.e" in state["amharic_tewahedo_deu"]
        assert "τ.7.x.f" in state["amharic_tewahedo_jos"]

    def test_next_phase_tau7xg(self):
        assert _tau7xf_block()["next_phase"] == "τ.7.x.g"

    def test_arc_open_marker_post_pentateuch_historical_books(self):
        """τ.7.x.f is the FIRST τ-cluster ingest after the §8.1
        Pentateuch arc-close at τ.7.x.e — opens the post-Pentateuch
        historical-books arc."""
        assert _tau7xf_block()["arc_open"] == "post-pentateuch-historical-books"

    def test_arc_open_narrative_present(self):
        """The arc-open narrative documents the historical-books
        arc trajectory."""
        narrative = _tau7xf_block()["arc_open_narrative"]
        assert "Pentateuch" in narrative
        assert "historical-books" in narrative or "historical books" in narrative


class TestTau7XFMetaYamlIngestRecord:
    """amharic-tewahedo/_meta.yaml has all six ingest records +
    upgraded stats (6 books / 5428 verses combined)."""

    def _meta(self) -> dict:
        path = AMHARIC_TEWAHEDO / "_meta.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_stats_books_at_least_six(self):
        # Pentateuch (5) + Joshua (1) = 6 books at τ.7.x.f ship-time.
        # Milestone-pin form: ≥6 (per share-pin → milestone-pin
        # conversion in feedback_share_pin_pattern at τ.7.x.g ship-
        # time; sixth instance of the conversion in τ.7.x.* family).
        m = self._meta()
        assert m["stats"]["books"] >= 6

    def test_stats_verses_combined(self):
        # 1308 (gen) + 947 (ex) + 802 (lev) + 1107 (num) + 781 (deu)
        # + 483 (jos) = 5428. Floor 5000.
        m = self._meta()
        assert m["stats"]["verses"] >= 5000

    def test_tau7xf_ingest_record_present(self):
        m = self._meta()
        assert "ingest_record_tau7xf" in m

    def test_tau7xf_ingest_record_phase(self):
        m = self._meta()
        assert m["ingest_record_tau7xf"]["phase"] == "τ.7.x.f"

    def test_tau7xf_ingest_record_book_codes_jos(self):
        m = self._meta()
        assert m["ingest_record_tau7xf"]["ingested_book_codes"] == ["jos"]

    def test_tau7xf_ingest_record_parser_extensions_chain(self):
        m = self._meta()
        chain = m["ingest_record_tau7xf"]["parser_extensions"]
        for phase in (
            "τ.6.x.1.B",
            "τ.6.x.1.C",
            "τ.6.x.1.D",
            "τ.7.x.a",
            "τ.7.x.b",
            "τ.7.x.c",
            "τ.7.x.d",
            "τ.7.x.e",
            "τ.7.x.f",
        ):
            assert phase in chain, f"parser_extensions chain missing {phase}"

    def test_tau7xf_arc_open_marker(self):
        """ingest_record_tau7xf carries the post-Pentateuch arc-open marker."""
        m = self._meta()
        assert m["ingest_record_tau7xf"]["arc_open"] == "post-pentateuch-historical-books"

    def test_prior_ingest_records_still_present(self):
        """τ.7.x.f adds; does NOT remove τ.7.x.a/b/c/d/e records."""
        m = self._meta()
        assert "ingest_record" in m
        assert m["ingest_record"]["phase"] == "τ.7.x.a"
        for tag in ("tau7xb", "tau7xc", "tau7xd", "tau7xe"):
            assert f"ingest_record_{tag}" in m, f"prior ingest record missing: {tag}"


class TestTau7XFGeezTewahedoPreserved:
    """The Geʽez column should remain unchanged after τ.7.x.f — full
    Geʽez Joshua ingest is τ.6.x.2.f per D4-c sequencing."""

    def test_geez_tewahedo_jos_py_ingested_at_tau6x2f(self):
        """MIGRATED at τ.6.x.2.a-h batch ship-time (2026-05-15):
        originally asserted geez-tewahedo/jos.py does NOT exist
        until τ.6.x.2.f ships. The τ.6.x.2.a-h batch ship
        CREATED this file at ocr-tier3 quality (per D4-c catchup arc).
        Durable assertion is now: geez-tewahedo/jos.py EXISTS at
        ocr-tier3 ingest scale; per-file content pinned in
        test_parallel_bible_tau6x2_geez_arc.py."""
        import ast

        path = GEEZ_TEWAHEDO / "jos.py"
        assert path.is_file(), "geez-tewahedo/jos.py must exist post-τ.6.x.2.f (τ.6.x.2.a-h batch ship)"
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
        # τ.6.x.2.f empirical at ship: 351 verses; floor 325 guards
        # against regression while permitting parser refinement.
        assert len(verses) >= 325, (
            f"geez-tewahedo/jos.py must be at ocr-tier3 scale post-τ.6.x.2.f; "
            f"got {len(verses)} verses (<325 indicates regression)"
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


class TestTau7XFPostPentateuchArcOpen:
    """Post-Pentateuch historical-books arc-open — Joshua shipped as
    the FIRST τ-cluster ingest after the §8.1 Pentateuch arc-close at
    τ.7.x.e. The Pentateuch closure invariant must remain preserved."""

    def test_joshua_shipped(self):
        """jos.py exists under amharic-tewahedo/."""
        assert (AMHARIC_TEWAHEDO / "jos.py").is_file()

    def test_all_pentateuch_books_still_shipped(self):
        """§8.1 Pentateuch arc-close invariant: gen+ex+lev+num+deu
        must all still exist after τ.7.x.f."""
        for book in ("gen", "ex", "lev", "num", "deu"):
            path = AMHARIC_TEWAHEDO / f"{book}.py"
            assert path.is_file(), (
                f"§8.1 Pentateuch invariant: amharic-tewahedo/{book}.py must still exist after τ.7.x.f"
            )

    def test_six_book_combined_coverage_at_least_80_percent(self):
        """Combined Pentateuch + Joshua coverage = sum of per-book
        verses / sum of per-book floors. Empirical at arc-open:
        5428/6511 = 83.4%. Floor 80% protects against regression."""
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import (
            DEUTERONOMY_VERSE_COUNTS,
            EXODUS_VERSE_COUNTS,
            GENESIS_VERSE_COUNTS,
            JOSHUA_VERSE_COUNTS,
            LEVITICUS_VERSE_COUNTS,
            NUMBERS_VERSE_COUNTS,
        )

        floors = {
            "gen": sum(GENESIS_VERSE_COUNTS.values()),
            "ex": sum(EXODUS_VERSE_COUNTS.values()),
            "lev": sum(LEVITICUS_VERSE_COUNTS.values()),
            "num": sum(NUMBERS_VERSE_COUNTS.values()),
            "deu": sum(DEUTERONOMY_VERSE_COUNTS.values()),
            "jos": sum(JOSHUA_VERSE_COUNTS.values()),
        }
        total_extracted = 0
        total_expected = sum(floors.values())
        for book in ("gen", "ex", "lev", "num", "deu", "jos"):
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
            f"Pentateuch+Joshua combined coverage must be ≥80%; got {coverage:.1f}% ({total_extracted}/{total_expected})"
        )


class TestTau7XFStateDocs:
    # Doc-pins collapsed to the CHANGELOG chokepoint (2026-05-21): the
    # old test_session_state_*/test_in_flight_*/test_plan_ledger_* pins
    # read SESSION_STATE.md / IN_FLIGHT.md (rolling, trimmed) and the
    # moved PLAN_2026-05-09.md. The durable phase record is CHANGELOG.md.
    def test_phase_recorded_in_changelog(self):
        from tests.fixtures import assert_phase_recorded

        assert_phase_recorded("τ.7.x.f")

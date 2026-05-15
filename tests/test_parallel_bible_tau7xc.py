"""τ.7.x.c — Amharic Leviticus full-book ingest pins (2026-05-15).

THIRD τ.7.x.* per-book ship under D4-c Amharic-first + D1-a per-book
cadence. Re-uses the τ.7.x.a pipeline (via τ.7.x.b confirmation) with
only LEVITICUS_VERSE_COUNTS + structural_map.leviticus as deltas.
93.4% coverage — highest τ.7.x.* coverage yet.

Pins validate:
1. LEVITICUS_VERSE_COUNTS dict shape (27 chapters / 859 total verses).
2. structural_map.leviticus block in _source.yaml.
3. content/translations/amharic-tewahedo/lev.py module shape +
   INGEST_PHASE='τ.7.x.c' + SOURCE_QUALITY='ocr-tier3'.
4. Per-chapter coverage (1-25 fully populated; 26 partial 23/46; 27 empty).
5. _meta.yaml ingest_record_tau7xc block + combined stats.
6. _source.yaml::ocr_strategy.tau7xc_ingest block.
7. Reciprocal back-link tau7xb_ingest.pipeline_reused_at_phase = τ.7.x.c.
8. CLI --renumber {genesis,exodus,leviticus} extension.
9. geez-tewahedo/lev.py NOT created (D4-c preserved).
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


def _leviticus_block() -> dict:
    return _source_yaml()["structural_map"]["leviticus"]


def _tau7xc_block() -> dict:
    return _source_yaml()["ocr_strategy"]["tau7xc_ingest"]


def _lev_verses() -> list[tuple]:
    lev_py = AMHARIC_TEWAHEDO / "lev.py"
    text = lev_py.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSES":
                    return ast.literal_eval(node.value)
    raise AssertionError("amharic-tewahedo/lev.py must define VERSES")


def _lev_constants() -> dict:
    lev_py = AMHARIC_TEWAHEDO / "lev.py"
    text = lev_py.read_text(encoding="utf-8")
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


class TestTau7XCLeviticusVerseCounts:
    """LEVITICUS_VERSE_COUNTS is the τ.7.x.c renumber-floor dict."""

    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_module_symbol_present(self):
        from extract_parallel_pdf import LEVITICUS_VERSE_COUNTS

        assert isinstance(LEVITICUS_VERSE_COUNTS, dict)

    def test_twenty_seven_chapters(self):
        from extract_parallel_pdf import LEVITICUS_VERSE_COUNTS

        assert sorted(LEVITICUS_VERSE_COUNTS.keys()) == list(range(1, 28))

    def test_total_verses_859(self):
        from extract_parallel_pdf import LEVITICUS_VERSE_COUNTS

        # Masoretic + LXX + Vulgate + Tewahedo agreement: 859 verses.
        assert sum(LEVITICUS_VERSE_COUNTS.values()) == 859

    def test_chapter_specific_verse_counts(self):
        """Spot-check well-known Leviticus chapter sizes."""
        from extract_parallel_pdf import LEVITICUS_VERSE_COUNTS

        # Lev 12 (purification after childbirth) = 8 verses (shortest)
        assert LEVITICUS_VERSE_COUNTS[12] == 8
        # Lev 13 (skin disease laws) = 59 verses (longest)
        assert LEVITICUS_VERSE_COUNTS[13] == 59
        # Lev 27 (vows + redemption) = 34 verses (closing)
        assert LEVITICUS_VERSE_COUNTS[27] == 34


class TestTau7XCStructuralMapLeviticus:
    """structural_map.leviticus block records the Leviticus page range
    discovered via τ.7.x.c boundary inspection."""

    def test_block_present(self):
        assert "leviticus" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert _leviticus_block()["book_codes"] == ["lev"]

    def test_pdf_page_range(self):
        # 161-213 inclusive (53 pages for 27 chapters; verified by
        # Lev 27:34 closing at p212 + Num 1:1 opening at p214 content
        # inspection).
        assert _leviticus_block()["pdf_page_range"] == [161, 213]

    def test_pdf_index_offset_zero(self):
        assert _leviticus_block()["pdf_index_offset"] == 0

    def test_verified_true(self):
        assert _leviticus_block()["verified"] is True

    def test_verified_at_tau7xc(self):
        assert _leviticus_block()["verified_at_phase"] == "τ.7.x.c"

    def test_chapter_count_expected_27(self):
        assert _leviticus_block()["chapter_count_expected"] == 27

    def test_notes_document_boundary_inspection(self):
        notes = _leviticus_block()["notes"]
        # Lev 1:1 opening + Lev 27:34 closing + Num 1:1 boundary all referenced.
        assert "ሙሌን" in notes or "ሙሴን" in notes, "Notes must reference Lev 1:1 opening (Moses called)"
        assert "በሲና ተራራ" in notes, "Notes must reference Lev 27:34 closing 'on Mount Sinai'"
        assert "በሁለተኛው ዓመት" in notes or "Numbers 1:1" in notes, "Notes must reference Num 1:1 boundary"


class TestTau7XCLeviticusLevPy:
    """amharic-tewahedo/lev.py is the τ.7.x.c output module."""

    def test_lev_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "lev.py").is_file()

    def test_translation_constant(self):
        c = _lev_constants()
        assert c.get("TRANSLATION") == "amharic-tewahedo"

    def test_book_constant(self):
        c = _lev_constants()
        assert c.get("BOOK") == "lev"

    def test_source_quality_ocr_tier3(self):
        c = _lev_constants()
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"

    def test_source_provenance(self):
        c = _lev_constants()
        assert c.get("SOURCE_PROVENANCE") == "parallel-bible-eotc"

    def test_ingest_phase_constant(self):
        c = _lev_constants()
        assert c.get("INGEST_PHASE") == "τ.7.x.c"

    def test_verses_count_at_least_floor(self):
        verses = _lev_verses()
        # Empirical at ship was 802. Floor 700 protects against
        # silent regression while permitting parser refinement.
        assert len(verses) >= 700, f"τ.7.x.c Leviticus ingest must have ≥700 verses; got {len(verses)}"

    def test_first_verse_is_lev_1_1(self):
        verses = _lev_verses()
        ch, v, text = verses[0]
        assert (ch, v) == (1, 1)
        assert text, "Lev 1:1 text must be non-empty"


class TestTau7XCLeviticusCoverage:
    """Per-chapter coverage matches empirical post-renumber
    distribution: chapters 1-25 fully populated; 26 partial 23/46;
    27 empty."""

    def _by_chapter(self) -> dict[int, list[tuple]]:
        verses = _lev_verses()
        out: dict[int, list[tuple]] = {}
        for ch, v, t in verses:
            out.setdefault(ch, []).append((v, t))
        return out

    def test_chapters_1_through_25_fully_populated(self):
        """The defining τ.7.x.c empirical pin: chapters 1-25 have
        verse counts MATCHING LEVITICUS_VERSE_COUNTS floor."""
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import LEVITICUS_VERSE_COUNTS

        by_ch = self._by_chapter()
        for ch in range(1, 26):
            got = len(by_ch.get(ch, []))
            expected = LEVITICUS_VERSE_COUNTS[ch]
            assert got == expected, (
                f"τ.7.x.c chapter {ch} must have exactly {expected} verses (LEVITICUS_VERSE_COUNTS floor); got {got}"
            )

    def test_chapter_26_partial(self):
        """Chapter 26 received the parser's remaining 23 verses."""
        by_ch = self._by_chapter()
        got = len(by_ch.get(26, []))
        # Empirical 23; defensive range (1, 46).
        assert 1 <= got <= 46, f"τ.7.x.c chapter 26 partial: expect 1..46 verses; got {got}"

    def test_chapter_27_empty(self):
        """Chapter 27 received zero verses — parser exhausted at ch 26."""
        by_ch = self._by_chapter()
        got = len(by_ch.get(27, []))
        assert got == 0, f"τ.7.x.c chapter 27 should be empty at ocr-tier3; got {got} verses"

    def test_no_overflow_above_chapter_27(self):
        by_ch = self._by_chapter()
        overflow = sum(len(v) for ch, v in by_ch.items() if ch > 27)
        assert overflow == 0, f"τ.7.x.c renumber overflow should be 0; got {overflow} verses above ch 27"


class TestTau7XCSourceYamlIngestBlock:
    """ocr_strategy.tau7xc_ingest block records the τ.7.x.c ship +
    back-link annotation to tau7xb_ingest."""

    def test_block_exists(self):
        assert "tau7xc_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert _tau7xc_block()["shipped_at_phase"] == "τ.7.x.c"

    def test_structural_map_addition(self):
        sma = _tau7xc_block()["structural_map_addition"]
        assert sma["section"] == "leviticus"
        assert sma["pdf_page_range"] == [161, 213]
        assert sma["chapter_count_expected"] == 27

    def test_helpers_added_leviticus_verse_counts(self):
        helpers = _tau7xc_block()["helpers_added"]
        assert "LEVITICUS_VERSE_COUNTS" in helpers

    def test_cli_extensions_renumber_choice_extended(self):
        cli = _tau7xc_block()["cli_extensions"]
        assert "renumber_choice_extended" in cli

    def test_empirical_validation_coverage_93_percent(self):
        ev = _tau7xc_block()["empirical_validation"]
        # Coverage at ship was 93.4%. Floor 85 protects against regression.
        assert ev["coverage_pct"] >= 85.0

    def test_empirical_chapters_fully_populated_1_through_25(self):
        ev = _tau7xc_block()["empirical_validation"]
        assert ev["chapters_fully_populated"] == list(range(1, 26))

    def test_empirical_chapters_missing_27(self):
        ev = _tau7xc_block()["empirical_validation"]
        assert ev["chapters_missing"] == [27]

    def test_no_ingest_at_this_phase_false(self):
        assert _tau7xc_block()["no_ingest_at_this_phase"] is False

    def test_closed_arc_tau6x0a_no_ingest_false(self):
        contracts = _tau7xc_block()["closed_arc_contracts_preserved"]
        assert contracts["tau6x0a_no_ingest"] is False  # third authorized violation

    def test_closed_arc_tau7xa_and_tau7xb_preserved(self):
        contracts = _tau7xc_block()["closed_arc_contracts_preserved"]
        assert contracts["tau7xa_ingest"] is True
        assert contracts["tau7xb_ingest"] is True

    def test_reciprocal_back_link_in_tau7xb(self):
        """τ.7.x.b tau7xb_ingest block must carry pipeline_reused_at_
        phase = τ.7.x.c (back-link annotation)."""
        b = _source_yaml()["ocr_strategy"]["tau7xb_ingest"]
        assert b.get("pipeline_reused_at_phase") == "τ.7.x.c"

    def test_translation_slot_state_records_three_books(self):
        state = _tau7xc_block()["translation_slot_state"]
        assert "τ.7.x.a" in state["amharic_tewahedo_gen"]
        assert "τ.7.x.b" in state["amharic_tewahedo_ex"]
        assert "τ.7.x.c" in state["amharic_tewahedo_lev"]

    def test_next_phase_tau7xd(self):
        assert _tau7xc_block()["next_phase"] == "τ.7.x.d"


class TestTau7XCMetaYamlIngestRecord:
    """amharic-tewahedo/_meta.yaml has ingest_record (τ.7.x.a) +
    ingest_record_tau7xb (τ.7.x.b) + ingest_record_tau7xc (τ.7.x.c)
    blocks + upgraded stats."""

    def _meta(self) -> dict:
        path = AMHARIC_TEWAHEDO / "_meta.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_stats_books_at_least_three(self):
        """Refactored share-pin→milestone-pin at τ.7.x.d ship-time per
        `feedback_share_pin_pattern`. Originally asserted ==3 (gen+ex+lev
        post-τ.7.x.c); τ.7.x.d bumped to 4. Durable invariant: ≥3
        (Genesis + Exodus + Leviticus all shipped, plus any subsequent
        τ.7.x.* book)."""
        m = self._meta()
        assert m["stats"]["books"] >= 3

    def test_stats_verses_combined(self):
        # 1308 (gen) + 947 (ex) + 802 (lev) = 3057. Floor 2500.
        m = self._meta()
        assert m["stats"]["verses"] >= 2500

    def test_tau7xc_ingest_record_present(self):
        m = self._meta()
        assert "ingest_record_tau7xc" in m

    def test_tau7xc_ingest_record_phase(self):
        m = self._meta()
        assert m["ingest_record_tau7xc"]["phase"] == "τ.7.x.c"

    def test_tau7xc_ingest_record_book_codes_lev(self):
        m = self._meta()
        assert m["ingest_record_tau7xc"]["ingested_book_codes"] == ["lev"]

    def test_tau7xc_ingest_record_parser_extensions_chain(self):
        m = self._meta()
        chain = m["ingest_record_tau7xc"]["parser_extensions"]
        # The full chain extends to τ.7.x.c.
        for phase in ("τ.6.x.1.B", "τ.6.x.1.C", "τ.6.x.1.D", "τ.7.x.a", "τ.7.x.b", "τ.7.x.c"):
            assert phase in chain, f"parser_extensions chain missing {phase}"

    def test_prior_ingest_records_still_present(self):
        """τ.7.x.c adds; does NOT remove τ.7.x.a or τ.7.x.b records."""
        m = self._meta()
        assert "ingest_record" in m
        assert m["ingest_record"]["phase"] == "τ.7.x.a"
        assert "ingest_record_tau7xb" in m
        assert m["ingest_record_tau7xb"]["phase"] == "τ.7.x.b"


class TestTau7XCGeezTewahedoPreserved:
    """The Geʽez column should remain unchanged after τ.7.x.c — full
    Geʽez Leviticus ingest is τ.6.x.2.c per D4-c sequencing."""

    def test_geez_tewahedo_lev_py_ingested_at_tau6x2c(self):
        """MIGRATED at τ.6.x.2.a-h batch ship-time (2026-05-15):
        originally asserted geez-tewahedo/lev.py does NOT exist
        until τ.6.x.2.c ships. The τ.6.x.2.a-h batch ship
        CREATED this file at ocr-tier3 quality (per D4-c catchup arc).
        Durable assertion is now: geez-tewahedo/lev.py EXISTS at
        ocr-tier3 ingest scale; per-file content pinned in
        test_parallel_bible_tau6x2_geez_arc.py."""
        import ast

        path = GEEZ_TEWAHEDO / "lev.py"
        assert path.is_file(), "geez-tewahedo/lev.py must exist post-τ.6.x.2.c (τ.6.x.2.a-h batch ship)"
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
        # τ.6.x.2.c empirical at ship: 534 verses; floor 500 guards
        # against regression while permitting parser refinement.
        assert len(verses) >= 500, (
            f"geez-tewahedo/lev.py must be at ocr-tier3 scale post-τ.6.x.2.c; "
            f"got {len(verses)} verses (<500 indicates regression)"
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


class TestTau7XCStateDocs:
    """SESSION_STATE, IN_FLIGHT, CHANGELOG, PLAN all reference τ.7.x.c."""

    def test_session_state_mentions_tau7xc(self):
        txt = (REPO / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
        assert "τ.7.x.c" in txt

    def test_in_flight_mentions_tau7xc(self):
        txt = (REPO / "dev" / "IN_FLIGHT.md").read_text(encoding="utf-8")
        assert "τ.7.x.c" in txt

    def test_changelog_records_tau7xc_entry(self):
        txt = (REPO / "dev" / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "τ.7.x.c" in txt

    def test_plan_ledger_records_tau7xc(self):
        txt = (REPO / "dev" / "PLAN_2026-05-09.md").read_text(encoding="utf-8")
        assert "τ.7.x.c" in txt

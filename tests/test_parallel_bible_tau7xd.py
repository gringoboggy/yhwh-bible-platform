"""τ.7.x.d — Amharic Numbers full-book ingest pins (2026-05-15).

FOURTH τ.7.x.* per-book ship under D4-c Amharic-first + D1-a per-book
cadence. Re-uses the τ.7.x.c pipeline (which itself reused τ.7.x.b
which reused τ.7.x.a) with only NUMBERS_VERSE_COUNTS +
structural_map.numbers as deltas. 85.9% coverage — sits between
Genesis (85.3%) and Leviticus (93.4%) at the typical narrative-dense
book recovery profile.

Pins validate:
1. NUMBERS_VERSE_COUNTS dict shape (36 chapters / 1288 total verses).
2. structural_map.numbers block in _source.yaml.
3. content/translations/amharic-tewahedo/num.py module shape +
   INGEST_PHASE='τ.7.x.d' + SOURCE_QUALITY='ocr-tier3'.
4. Per-chapter coverage (1-30 fully populated; 31 partial 47/54;
   32-36 empty).
5. _meta.yaml ingest_record_tau7xd block + combined stats.
6. _source.yaml::ocr_strategy.tau7xd_ingest block.
7. Reciprocal back-link tau7xc_ingest.pipeline_reused_at_phase = τ.7.x.d.
8. CLI --renumber {genesis,exodus,leviticus,numbers} extension.
9. geez-tewahedo/num.py NOT created (D4-c preserved).
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


def _numbers_block() -> dict:
    return _source_yaml()["structural_map"]["numbers"]


def _tau7xd_block() -> dict:
    return _source_yaml()["ocr_strategy"]["tau7xd_ingest"]


def _num_verses() -> list[tuple]:
    num_py = AMHARIC_TEWAHEDO / "num.py"
    text = num_py.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSES":
                    return ast.literal_eval(node.value)
    raise AssertionError("amharic-tewahedo/num.py must define VERSES")


def _num_constants() -> dict:
    num_py = AMHARIC_TEWAHEDO / "num.py"
    text = num_py.read_text(encoding="utf-8")
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


class TestTau7XDNumbersVerseCounts:
    """NUMBERS_VERSE_COUNTS is the τ.7.x.d renumber-floor dict."""

    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_module_symbol_present(self):
        from extract_parallel_pdf import NUMBERS_VERSE_COUNTS

        assert isinstance(NUMBERS_VERSE_COUNTS, dict)

    def test_thirty_six_chapters(self):
        from extract_parallel_pdf import NUMBERS_VERSE_COUNTS

        assert sorted(NUMBERS_VERSE_COUNTS.keys()) == list(range(1, 37))

    def test_total_verses_1288(self):
        from extract_parallel_pdf import NUMBERS_VERSE_COUNTS

        # Masoretic + LXX + Tewahedo agreement: 1288 verses (Vulgate
        # 16:36-50 → 17:1-15 repartitioning NOT followed in the
        # parallel-Bible-EOTC source).
        assert sum(NUMBERS_VERSE_COUNTS.values()) == 1288

    def test_chapter_specific_verse_counts(self):
        """Spot-check well-known Numbers chapter sizes."""
        from extract_parallel_pdf import NUMBERS_VERSE_COUNTS

        # Num 7 (princes' offerings) = 89 verses (longest chapter)
        assert NUMBERS_VERSE_COUNTS[7] == 89
        # Num 17 (Aaron's rod) = 13 verses (Hebrew enumeration, NOT
        # the Vulgate 28-verse repartitioned form)
        assert NUMBERS_VERSE_COUNTS[17] == 13
        # Num 36 (daughters-of-Zelophehad close) = 13 verses
        assert NUMBERS_VERSE_COUNTS[36] == 13
        # Num 1 (first census) = 54 verses
        assert NUMBERS_VERSE_COUNTS[1] == 54


class TestTau7XDStructuralMapNumbers:
    """structural_map.numbers block records the Numbers page range
    discovered via τ.7.x.d boundary inspection (Deuteronomy title
    `ኦሪት ዘዳግም` scan)."""

    def test_block_present(self):
        assert "numbers" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert _numbers_block()["book_codes"] == ["num"]

    def test_pdf_page_range(self):
        # 214-287 inclusive (74 pages for 36 chapters; verified by
        # Num 1:1 opening at p214 + Deut 1:1 opening at p288 content
        # inspection).
        assert _numbers_block()["pdf_page_range"] == [214, 287]

    def test_pdf_index_offset_zero(self):
        assert _numbers_block()["pdf_index_offset"] == 0

    def test_verified_true(self):
        assert _numbers_block()["verified"] is True

    def test_verified_at_tau7xd(self):
        assert _numbers_block()["verified_at_phase"] == "τ.7.x.d"

    def test_chapter_count_expected_36(self):
        assert _numbers_block()["chapter_count_expected"] == 36

    def test_notes_document_boundary_inspection(self):
        notes = _numbers_block()["notes"]
        # Num 1:1 opening + Deut 1:1 boundary + Tewahedo title-meaning
        # introduction all referenced.
        assert "ኦሪት ዘጐልቍ" in notes, "Notes must reference Tewahedo Numbers title 'law of numbering'"
        assert "ኦሪት ዘዳግም" in notes, "Notes must reference Deuteronomy title scan"
        assert "በገዳም ዘሲና" in notes or "wilderness of Sinai" in notes, (
            "Notes must reference Num 1:1 'wilderness of Sinai'"
        )


class TestTau7XDNumbersNumPy:
    """amharic-tewahedo/num.py is the τ.7.x.d output module."""

    def test_num_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "num.py").is_file()

    def test_translation_constant(self):
        c = _num_constants()
        assert c.get("TRANSLATION") == "amharic-tewahedo"

    def test_book_constant(self):
        c = _num_constants()
        assert c.get("BOOK") == "num"

    def test_source_quality_ocr_tier3(self):
        c = _num_constants()
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"

    def test_source_provenance(self):
        c = _num_constants()
        assert c.get("SOURCE_PROVENANCE") == "parallel-bible-eotc"

    def test_ingest_phase_constant(self):
        c = _num_constants()
        assert c.get("INGEST_PHASE") == "τ.7.x.d"

    def test_verses_count_at_least_floor(self):
        verses = _num_verses()
        # Empirical at ship was 1107. Floor 1000 protects against
        # silent regression while permitting parser refinement.
        assert len(verses) >= 1000, f"τ.7.x.d Numbers ingest must have ≥1000 verses; got {len(verses)}"

    def test_first_verse_is_num_1_1(self):
        verses = _num_verses()
        ch, v, text = verses[0]
        assert (ch, v) == (1, 1)
        assert text, "Num 1:1 text must be non-empty"


class TestTau7XDNumbersCoverage:
    """Per-chapter coverage matches empirical post-renumber
    distribution: chapters 1-30 fully populated; 31 partial 47/54;
    32-36 empty."""

    def _by_chapter(self) -> dict[int, list[tuple]]:
        verses = _num_verses()
        out: dict[int, list[tuple]] = {}
        for ch, v, t in verses:
            out.setdefault(ch, []).append((v, t))
        return out

    def test_chapters_1_through_30_fully_populated(self):
        """The defining τ.7.x.d empirical pin: chapters 1-30 have
        verse counts MATCHING NUMBERS_VERSE_COUNTS floor."""
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import NUMBERS_VERSE_COUNTS

        by_ch = self._by_chapter()
        for ch in range(1, 31):
            got = len(by_ch.get(ch, []))
            expected = NUMBERS_VERSE_COUNTS[ch]
            assert got == expected, (
                f"τ.7.x.d chapter {ch} must have exactly {expected} verses (NUMBERS_VERSE_COUNTS floor); got {got}"
            )

    def test_chapter_31_partial(self):
        """Chapter 31 received the parser's remaining 47 verses."""
        by_ch = self._by_chapter()
        got = len(by_ch.get(31, []))
        # Empirical 47; defensive range (1, 54).
        assert 1 <= got <= 54, f"τ.7.x.d chapter 31 partial: expect 1..54 verses; got {got}"

    def test_chapters_32_through_36_empty(self):
        """Chapters 32-36 received zero verses — parser exhausted at ch 31."""
        by_ch = self._by_chapter()
        for ch in (32, 33, 34, 35, 36):
            got = len(by_ch.get(ch, []))
            assert got == 0, f"τ.7.x.d chapter {ch} should be empty at ocr-tier3; got {got} verses"

    def test_no_overflow_above_chapter_36(self):
        by_ch = self._by_chapter()
        overflow = sum(len(v) for ch, v in by_ch.items() if ch > 36)
        assert overflow == 0, f"τ.7.x.d renumber overflow should be 0; got {overflow} verses above ch 36"

    def test_end_of_book_colophon_preserved(self):
        """The end-of-Numbers colophon `ተፈጸመ ዘፈጠረ ኵሎ ዓለመ` is preserved
        at the last ingested verse (renumbered ch 31:47 due to the
        14.1% recovery deficit; canonically end-of-Num 36)."""
        verses = _num_verses()
        last_ch, last_v, last_text = verses[-1]
        assert "ተፈጸ" in last_text or "ተፈጻመ" in last_text, (
            f"τ.7.x.d last verse must preserve end-of-Numbers colophon; got: {last_text[:200]}"
        )


class TestTau7XDSourceYamlIngestBlock:
    """ocr_strategy.tau7xd_ingest block records the τ.7.x.d ship +
    back-link annotation to tau7xc_ingest."""

    def test_block_exists(self):
        assert "tau7xd_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert _tau7xd_block()["shipped_at_phase"] == "τ.7.x.d"

    def test_structural_map_addition(self):
        sma = _tau7xd_block()["structural_map_addition"]
        assert sma["section"] == "numbers"
        assert sma["pdf_page_range"] == [214, 287]
        assert sma["chapter_count_expected"] == 36

    def test_helpers_added_numbers_verse_counts(self):
        helpers = _tau7xd_block()["helpers_added"]
        assert "NUMBERS_VERSE_COUNTS" in helpers

    def test_cli_extensions_renumber_choice_extended(self):
        cli = _tau7xd_block()["cli_extensions"]
        assert "renumber_choice_extended" in cli

    def test_empirical_validation_coverage_85_plus_percent(self):
        ev = _tau7xd_block()["empirical_validation"]
        # Coverage at ship was 85.9%. Floor 80 protects against regression.
        assert ev["coverage_pct"] >= 80.0

    def test_empirical_chapters_fully_populated_1_through_30(self):
        ev = _tau7xd_block()["empirical_validation"]
        assert ev["chapters_fully_populated"] == list(range(1, 31))

    def test_empirical_chapters_missing_32_through_36(self):
        ev = _tau7xd_block()["empirical_validation"]
        assert ev["chapters_missing"] == [32, 33, 34, 35, 36]

    def test_no_ingest_at_this_phase_false(self):
        assert _tau7xd_block()["no_ingest_at_this_phase"] is False

    def test_closed_arc_tau6x0a_no_ingest_false(self):
        contracts = _tau7xd_block()["closed_arc_contracts_preserved"]
        assert contracts["tau6x0a_no_ingest"] is False  # fourth authorized violation

    def test_closed_arc_tau7xa_through_tau7xc_preserved(self):
        contracts = _tau7xd_block()["closed_arc_contracts_preserved"]
        assert contracts["tau7xa_ingest"] is True
        assert contracts["tau7xb_ingest"] is True
        assert contracts["tau7xc_ingest"] is True

    def test_reciprocal_back_link_in_tau7xc(self):
        """τ.7.x.c tau7xc_ingest block must carry pipeline_reused_at_
        phase = τ.7.x.d (back-link annotation, 8th instance of the
        single-key back-link pattern)."""
        c = _source_yaml()["ocr_strategy"]["tau7xc_ingest"]
        assert c.get("pipeline_reused_at_phase") == "τ.7.x.d"

    def test_translation_slot_state_records_four_books(self):
        state = _tau7xd_block()["translation_slot_state"]
        assert "τ.7.x.a" in state["amharic_tewahedo_gen"]
        assert "τ.7.x.b" in state["amharic_tewahedo_ex"]
        assert "τ.7.x.c" in state["amharic_tewahedo_lev"]
        assert "τ.7.x.d" in state["amharic_tewahedo_num"]

    def test_next_phase_tau7xe(self):
        assert _tau7xd_block()["next_phase"] == "τ.7.x.e"


class TestTau7XDMetaYamlIngestRecord:
    """amharic-tewahedo/_meta.yaml has all four ingest records +
    upgraded stats (4 books / 4164 verses combined)."""

    def _meta(self) -> dict:
        path = AMHARIC_TEWAHEDO / "_meta.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_stats_books_at_least_four(self):
        """Refactored share-pin→milestone-pin at τ.7.x.e ship-time per
        `feedback_share_pin_pattern`. Originally asserted ==4 (gen+ex
        +lev+num post-τ.7.x.d); τ.7.x.e bumped to 5. Durable
        invariant: ≥4 (Genesis + Exodus + Leviticus + Numbers all
        shipped, plus any subsequent τ.7.x.* book)."""
        m = self._meta()
        assert m["stats"]["books"] >= 4

    def test_stats_verses_combined(self):
        # 1308 (gen) + 947 (ex) + 802 (lev) + 1107 (num) = 4164. Floor 3500.
        m = self._meta()
        assert m["stats"]["verses"] >= 3500

    def test_tau7xd_ingest_record_present(self):
        m = self._meta()
        assert "ingest_record_tau7xd" in m

    def test_tau7xd_ingest_record_phase(self):
        m = self._meta()
        assert m["ingest_record_tau7xd"]["phase"] == "τ.7.x.d"

    def test_tau7xd_ingest_record_book_codes_num(self):
        m = self._meta()
        assert m["ingest_record_tau7xd"]["ingested_book_codes"] == ["num"]

    def test_tau7xd_ingest_record_parser_extensions_chain(self):
        m = self._meta()
        chain = m["ingest_record_tau7xd"]["parser_extensions"]
        # The full chain extends to τ.7.x.d.
        for phase in ("τ.6.x.1.B", "τ.6.x.1.C", "τ.6.x.1.D", "τ.7.x.a", "τ.7.x.b", "τ.7.x.c", "τ.7.x.d"):
            assert phase in chain, f"parser_extensions chain missing {phase}"

    def test_prior_ingest_records_still_present(self):
        """τ.7.x.d adds; does NOT remove τ.7.x.a/b/c records."""
        m = self._meta()
        assert "ingest_record" in m
        assert m["ingest_record"]["phase"] == "τ.7.x.a"
        assert "ingest_record_tau7xb" in m
        assert m["ingest_record_tau7xb"]["phase"] == "τ.7.x.b"
        assert "ingest_record_tau7xc" in m
        assert m["ingest_record_tau7xc"]["phase"] == "τ.7.x.c"


class TestTau7XDGeezTewahedoPreserved:
    """The Geʽez column should remain unchanged after τ.7.x.d — full
    Geʽez Numbers ingest is τ.6.x.2.d per D4-c sequencing."""

    def test_geez_tewahedo_num_py_not_created(self):
        assert not (GEEZ_TEWAHEDO / "num.py").exists(), (
            "geez-tewahedo/num.py must NOT be created at τ.7.x.d; Geʽez Numbers is τ.6.x.2.d under D4-c sequencing"
        )

    def test_geez_tewahedo_gen_py_still_seed(self):
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
        assert len(verses) <= 10, f"geez-tewahedo/gen.py should remain at Π.0 seed; got {len(verses)}"


class TestTau7XDStateDocs:
    """SESSION_STATE, IN_FLIGHT, CHANGELOG, PLAN all reference τ.7.x.d."""

    def test_session_state_mentions_tau7xd(self):
        txt = (REPO / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
        assert "τ.7.x.d" in txt

    def test_in_flight_mentions_tau7xd(self):
        txt = (REPO / "dev" / "IN_FLIGHT.md").read_text(encoding="utf-8")
        assert "τ.7.x.d" in txt

    def test_changelog_records_tau7xd_entry(self):
        txt = (REPO / "dev" / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "τ.7.x.d" in txt

    def test_plan_ledger_records_tau7xd(self):
        txt = (REPO / "dev" / "PLAN_2026-05-09.md").read_text(encoding="utf-8")
        assert "τ.7.x.d" in txt

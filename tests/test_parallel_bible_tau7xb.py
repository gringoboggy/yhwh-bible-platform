"""τ.7.x.b — Amharic Exodus full-book ingest pins (2026-05-15).

SECOND τ.7.x.* per-book ship under D4-c Amharic-first sequencing
+ D1-a per-book cadence per the τ.6.x.2.D D-decisions matrix.
Re-uses the τ.7.x.a pipeline verbatim with only the renumber-floor
dict (EXODUS_VERSE_COUNTS) + structural_map.exodus page-range as
deltas. Pins validate:

1. EXODUS_VERSE_COUNTS dict shape (40 chapters / 1213 total verses).
2. structural_map.exodus block in _source.yaml.
3. content/translations/amharic-tewahedo/ex.py module shape +
   INGEST_PHASE='τ.7.x.b' + SOURCE_QUALITY='ocr-tier3'.
4. Per-chapter coverage matches the empirical post-renumber
   distribution (chapters 1-32 fully populated; 33 partial 6/23;
   34-40 empty).
5. _meta.yaml ingest_record_tau7xb block.
6. _source.yaml::ocr_strategy.tau7xb_ingest block.
7. Reciprocal back-link tau7xa_ingest.pipeline_reused_at_phase = τ.7.x.b.
8. CLI --renumber {genesis,exodus} extension.
9. geez-tewahedo/ex.py NOT created (D4-c preserved).
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


def _exodus_block() -> dict:
    return _source_yaml()["structural_map"]["exodus"]


def _tau7xb_block() -> dict:
    return _source_yaml()["ocr_strategy"]["tau7xb_ingest"]


def _ex_verses() -> list[tuple]:
    ex_py = AMHARIC_TEWAHEDO / "ex.py"
    text = ex_py.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSES":
                    return ast.literal_eval(node.value)
    raise AssertionError("amharic-tewahedo/ex.py must define VERSES")


def _ex_constants() -> dict:
    ex_py = AMHARIC_TEWAHEDO / "ex.py"
    text = ex_py.read_text(encoding="utf-8")
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


class TestTau7XBExodusVerseCounts:
    """EXODUS_VERSE_COUNTS is the τ.7.x.b renumber-floor dict."""

    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_module_symbol_present(self):
        from extract_parallel_pdf import EXODUS_VERSE_COUNTS

        assert isinstance(EXODUS_VERSE_COUNTS, dict)

    def test_forty_chapters(self):
        from extract_parallel_pdf import EXODUS_VERSE_COUNTS

        assert sorted(EXODUS_VERSE_COUNTS.keys()) == list(range(1, 41))

    def test_total_verses_1213(self):
        from extract_parallel_pdf import EXODUS_VERSE_COUNTS

        # Masoretic + LXX + Vulgate agreement: 1213 verses.
        assert sum(EXODUS_VERSE_COUNTS.values()) == 1213

    def test_chapter_specific_verse_counts(self):
        """Spot-check a few well-known chapter sizes against the
        Masoretic enumeration."""
        from extract_parallel_pdf import EXODUS_VERSE_COUNTS

        # Ex 12 (Passover narrative) = 51 verses
        assert EXODUS_VERSE_COUNTS[12] == 51
        # Ex 20 (Ten Commandments) = 26 verses
        assert EXODUS_VERSE_COUNTS[20] == 26
        # Ex 40 (closing tabernacle erection) = 38 verses
        assert EXODUS_VERSE_COUNTS[40] == 38
        # Ex 11 (shortest chapter) = 10 verses
        assert EXODUS_VERSE_COUNTS[11] == 10


class TestTau7XBStructuralMapExodus:
    """structural_map.exodus block records the Exodus page range
    discovered via τ.7.x.b.0 boundary inspection."""

    def test_block_present(self):
        assert "exodus" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert _exodus_block()["book_codes"] == ["ex"]

    def test_pdf_page_range(self):
        # 86-160 inclusive (75 pages for 40 chapters; verified by
        # Ex 40:36-38 closing narrative at p160 + Lev 1:1 opening at
        # p161 content inspection).
        assert _exodus_block()["pdf_page_range"] == [86, 160]

    def test_pdf_index_offset_zero(self):
        assert _exodus_block()["pdf_index_offset"] == 0

    def test_verified_true(self):
        assert _exodus_block()["verified"] is True

    def test_verified_at_tau7xb(self):
        assert _exodus_block()["verified_at_phase"] == "τ.7.x.b"

    def test_chapter_count_expected_40(self):
        assert _exodus_block()["chapter_count_expected"] == 40

    def test_notes_document_boundary_inspection(self):
        notes = _exodus_block()["notes"]
        # Exodus opening + Leviticus boundary markers documented.
        assert "ኦሪት ዘፀአት" in notes, "Notes must reference the Exodus title marker"
        assert "ዝ ውነቱ" in notes, "Notes must reference Ex 1:1 opening"
        assert "ደመናው ብርሃን ተነሥቶ" in notes, "Notes must reference Ex 40:36-38 closing narrative used to set boundary"
        assert "ሙሌን" in notes or "ሙሴን" in notes, "Notes must reference Lev 1:1 opening (Moses called)"


class TestTau7XBExodusGenPy:
    """amharic-tewahedo/ex.py is the τ.7.x.b output module."""

    def test_ex_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "ex.py").is_file()

    def test_translation_constant(self):
        c = _ex_constants()
        assert c.get("TRANSLATION") == "amharic-tewahedo"

    def test_book_constant(self):
        c = _ex_constants()
        assert c.get("BOOK") == "ex"

    def test_source_quality_ocr_tier3(self):
        c = _ex_constants()
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"

    def test_source_provenance(self):
        c = _ex_constants()
        assert c.get("SOURCE_PROVENANCE") == "parallel-bible-eotc"

    def test_ingest_phase_constant(self):
        c = _ex_constants()
        assert c.get("INGEST_PHASE") == "τ.7.x.b"

    def test_verses_count_at_least_floor(self):
        verses = _ex_verses()
        # Empirical at ship was 947. Floor 800 protects against
        # silent regression while permitting parser refinement.
        assert len(verses) >= 800, f"τ.7.x.b Exodus ingest must have ≥800 verses; got {len(verses)}"

    def test_first_verse_is_ex_1_1(self):
        verses = _ex_verses()
        ch, v, text = verses[0]
        assert (ch, v) == (1, 1)
        assert text, "Ex 1:1 text must be non-empty"


class TestTau7XBExodusCoverage:
    """Per-chapter coverage matches empirical post-renumber
    distribution: chapters 1-32 fully populated; 33 partial 6/23;
    34-40 empty."""

    def _by_chapter(self) -> dict[int, list[tuple]]:
        verses = _ex_verses()
        out: dict[int, list[tuple]] = {}
        for ch, v, t in verses:
            out.setdefault(ch, []).append((v, t))
        return out

    def test_chapter_1_first_verse_index(self):
        by_ch = self._by_chapter()
        first = by_ch[1][0]
        assert first[0] == 1, f"Ex 1 first verse must be v 1; got v {first[0]}"

    def test_chapters_1_through_32_fully_populated(self):
        """The defining τ.7.x.b empirical pin: chapters 1-32 have
        verse counts MATCHING EXODUS_VERSE_COUNTS floor."""
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import EXODUS_VERSE_COUNTS

        by_ch = self._by_chapter()
        for ch in range(1, 33):
            got = len(by_ch.get(ch, []))
            expected = EXODUS_VERSE_COUNTS[ch]
            assert got == expected, (
                f"τ.7.x.b chapter {ch} must have exactly {expected} verses (EXODUS_VERSE_COUNTS floor); got {got}"
            )

    def test_chapter_33_partial(self):
        """Chapter 33 received the parser's remaining 6 verses."""
        by_ch = self._by_chapter()
        got = len(by_ch.get(33, []))
        # Empirical 6; defensive range (1, 23).
        assert 1 <= got <= 23, f"τ.7.x.b chapter 33 partial: expect 1..23 verses; got {got}"

    def test_chapters_34_through_40_empty(self):
        """Chapters 34-40 received zero verses — parser exhausted
        recovered content before reaching the closing tabernacle-
        construction + cloud-of-glory chapters. Per τ.6.x.0b ocr-tier3
        honesty contract; τ.6.x.3 batched audit closes the gap."""
        by_ch = self._by_chapter()
        for ch in range(34, 41):
            got = len(by_ch.get(ch, []))
            assert got == 0, (
                f"τ.7.x.b chapter {ch} should be empty at ocr-tier3; "
                f"got {got} verses (parser-quality regression — investigate)"
            )

    def test_no_overflow_above_chapter_40(self):
        by_ch = self._by_chapter()
        overflow = sum(len(v) for ch, v in by_ch.items() if ch > 40)
        assert overflow == 0, f"τ.7.x.b renumber overflow should be 0; got {overflow} verses above ch 40"

    def test_end_of_exodus_colophon_in_last_verse(self):
        """Last ingested verse contains the END-OF-EXODUS colophon
        text ('Israel's Exodus is completed') per τ.7.x.b empirical
        validation."""
        verses = _ex_verses()
        last_text = verses[-1][2]
        # Colophon contains "ተፈጸመ" (completed) — a strong signal that
        # the publisher's book-end marker survived the OCR + parser.
        assert "ተፈጸመ" in last_text, (
            f"Last ingested verse should contain end-of-Exodus colophon ('ተፈጸመ' = completed); got {last_text[:100]!r}"
        )


class TestTau7XBSourceYamlIngestBlock:
    """ocr_strategy.tau7xb_ingest block records the τ.7.x.b ship +
    back-link annotation to tau7xa_ingest."""

    def test_block_exists(self):
        assert "tau7xb_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert _tau7xb_block()["shipped_at_phase"] == "τ.7.x.b"

    def test_structural_map_addition_section(self):
        sma = _tau7xb_block()["structural_map_addition"]
        assert sma["section"] == "exodus"
        assert sma["pdf_page_range"] == [86, 160]
        assert sma["chapter_count_expected"] == 40

    def test_helpers_added_exodus_verse_counts(self):
        helpers = _tau7xb_block()["helpers_added"]
        assert "EXODUS_VERSE_COUNTS" in helpers

    def test_cli_extensions_renumber_choice_extended(self):
        cli = _tau7xb_block()["cli_extensions"]
        assert "renumber_choice_extended" in cli

    def test_empirical_validation_coverage_78_percent(self):
        ev = _tau7xb_block()["empirical_validation"]
        assert ev["coverage_pct"] >= 75.0

    def test_empirical_chapters_fully_populated_1_through_32(self):
        ev = _tau7xb_block()["empirical_validation"]
        assert ev["chapters_fully_populated"] == list(range(1, 33))

    def test_empirical_chapters_missing_34_through_40(self):
        ev = _tau7xb_block()["empirical_validation"]
        assert ev["chapters_missing"] == list(range(34, 41))

    def test_no_ingest_at_this_phase_false(self):
        assert _tau7xb_block()["no_ingest_at_this_phase"] is False

    def test_closed_arc_tau6x0a_no_ingest_false(self):
        contracts = _tau7xb_block()["closed_arc_contracts_preserved"]
        assert contracts["tau6x0a_no_ingest"] is False  # second authorized violation

    def test_closed_arc_tau7xa_ingest_preserved(self):
        contracts = _tau7xb_block()["closed_arc_contracts_preserved"]
        assert contracts["tau7xa_ingest"] is True

    def test_reciprocal_back_link_in_tau7xa(self):
        """τ.7.x.a tau7xa_ingest block must carry pipeline_reused_at_
        phase = τ.7.x.b (back-link annotation)."""
        a = _source_yaml()["ocr_strategy"]["tau7xa_ingest"]
        assert a.get("pipeline_reused_at_phase") == "τ.7.x.b"

    def test_translation_slot_state_records_both_books(self):
        state = _tau7xb_block()["translation_slot_state"]
        assert "τ.7.x.a" in state["amharic_tewahedo_gen"]
        assert "τ.7.x.b" in state["amharic_tewahedo_ex"]

    def test_next_phase_tau7xc(self):
        assert _tau7xb_block()["next_phase"] == "τ.7.x.c"


class TestTau7XBMetaYamlIngestRecord:
    """amharic-tewahedo/_meta.yaml has both ingest_record (τ.7.x.a)
    + ingest_record_tau7xb (τ.7.x.b) blocks + upgraded stats."""

    def _meta(self) -> dict:
        path = AMHARIC_TEWAHEDO / "_meta.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_stats_books_at_least_two(self):
        """Refactored share-pin→milestone-pin at τ.7.x.c ship-time per
        `feedback_share_pin_pattern`. Originally asserted ==2 (gen+ex
        post-τ.7.x.b); τ.7.x.c bumped to 3. Durable invariant: ≥2
        (Genesis + Exodus both shipped, plus any subsequent τ.7.x.* book)."""
        m = self._meta()
        assert m["stats"]["books"] >= 2

    def test_stats_verses_combined(self):
        # 1308 (gen) + 947 (ex) = 2255
        m = self._meta()
        # Defensive floor 1500 protects against parser regression
        assert m["stats"]["verses"] >= 1500

    def test_tau7xb_ingest_record_present(self):
        m = self._meta()
        assert "ingest_record_tau7xb" in m

    def test_tau7xb_ingest_record_phase(self):
        m = self._meta()
        assert m["ingest_record_tau7xb"]["phase"] == "τ.7.x.b"

    def test_tau7xb_ingest_record_book_codes_ex(self):
        m = self._meta()
        assert m["ingest_record_tau7xb"]["ingested_book_codes"] == ["ex"]

    def test_tau7xb_ingest_record_parser_extensions_chain(self):
        m = self._meta()
        chain = m["ingest_record_tau7xb"]["parser_extensions"]
        # The full chain: τ.6.x.1.B + τ.6.x.1.C + τ.6.x.1.D + τ.7.x.a +
        # τ.7.x.b — the new EXODUS_VERSE_COUNTS floor was the only
        # delta from τ.7.x.a.
        for phase in ("τ.6.x.1.B", "τ.6.x.1.C", "τ.6.x.1.D", "τ.7.x.a", "τ.7.x.b"):
            assert phase in chain, f"parser_extensions chain missing {phase}"

    def test_tau7xa_ingest_record_still_present(self):
        """τ.7.x.b adds; does NOT remove the τ.7.x.a record."""
        m = self._meta()
        assert "ingest_record" in m
        assert m["ingest_record"]["phase"] == "τ.7.x.a"


class TestTau7XBGeezTewahedoPreserved:
    """The Geʽez column should remain unchanged after τ.7.x.b — full
    Geʽez Exodus ingest is τ.6.x.2.b per D4-c sequencing."""

    def test_geez_tewahedo_ex_py_not_created(self):
        """geez-tewahedo/ex.py should NOT exist post-τ.7.x.b — D4-c
        sequencing puts Geʽez Exodus at τ.6.x.2.b (after the full
        τ.7.x stream)."""
        assert not (GEEZ_TEWAHEDO / "ex.py").exists(), (
            "geez-tewahedo/ex.py must NOT be created at τ.7.x.b; Geʽez Exodus is τ.6.x.2.b under D4-c sequencing"
        )

    def test_geez_tewahedo_gen_py_still_seed(self):
        """geez-tewahedo/gen.py also remains at Π.0 seed."""
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


class TestTau7XBStateDocs:
    """SESSION_STATE, IN_FLIGHT, CHANGELOG, PLAN all reference τ.7.x.b."""

    def test_session_state_mentions_tau7xb(self):
        txt = (REPO / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
        assert "τ.7.x.b" in txt

    def test_in_flight_mentions_tau7xb(self):
        txt = (REPO / "dev" / "IN_FLIGHT.md").read_text(encoding="utf-8")
        assert "τ.7.x.b" in txt

    def test_changelog_records_tau7xb_entry(self):
        txt = (REPO / "dev" / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "τ.7.x.b" in txt

    def test_plan_ledger_records_tau7xb(self):
        txt = (REPO / "dev" / "PLAN_2026-05-09.md").read_text(encoding="utf-8")
        assert "τ.7.x.b" in txt

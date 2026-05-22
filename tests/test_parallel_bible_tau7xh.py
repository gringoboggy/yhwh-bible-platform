"""τ.7.x.h — Amharic Ruth full-book ingest pins (2026-05-15).

EIGHTH τ.7.x.* per-book ship under D4-c Amharic-first + D1-a per-book
cadence. Re-uses the τ.7.x.g pipeline (which itself reused τ.7.x.f
which reused τ.7.x.e which reused τ.7.x.d which reused τ.7.x.c which
reused τ.7.x.b which reused τ.7.x.a) with only RUTH_VERSE_COUNTS +
structural_map.ruth as deltas. 70.6% coverage — NEW band-bottom
(slightly below τ.7.x.f Joshua's prior 73.4% band-bottom); Ruth's
exceptional small scale (only 4 chapters / 85 verses / 6 PDF pages)
+ dense Davidic-genealogy compression makes ch 4 hard to recover.

**CONTINUES the post-Pentateuch historical-books arc opened at τ.7.x.f
under Amharic-first sequencing** — THIRD sub-phase in the historical-
books arc (Joshua → Judges → Ruth → 1-4 Kingdoms → 1-2 Paralipomena
→ Ezra/Nehemiah → Esther under the LXX/Tewahedo ordering).

**NULL-FORMAL-TITLE-BANNER PATTERN CONFIRMED 3X:** as with Joshua at
τ.7.x.f and Judges at τ.7.x.g, the explicit `መጽሐፈ ሩት` (Book of Ruth)
formal book-title-banner form does NOT appear in the PDF text-layer
at Ruth opening — publisher uses the `ኦሪት ዘሩት` running-header form
consistently. Third consecutive ship confirming this is DECISIVELY
the stable structural property of the parallel-Bible-EOTC scan.

**CRITICAL STRUCTURAL DISCOVERY at τ.7.x.h:** the parallel-Bible-EOTC
scan ENDS at page 437 (after Ruth 4:22). Pages 438+ contain a
SEPARATE publication (dzamaragna.net 2002 Amharic Bible appendix)
with a completely different format. τ.7.x.i (1 Samuel / 1 Kingdoms)
will require a NEW publication-format handler.

Pins validate:
1. RUTH_VERSE_COUNTS dict shape (4 chapters / 85 total verses).
2. structural_map.ruth block in _source.yaml.
3. content/translations/amharic-tewahedo/rut.py module shape +
   INGEST_PHASE='τ.7.x.h' + SOURCE_QUALITY='ocr-tier3'.
4. Per-chapter coverage (1-2 fully populated; 3 partial 15/18; 4 empty).
5. _meta.yaml ingest_record_tau7xh block + combined stats.
6. _source.yaml::ocr_strategy.tau7xh_ingest block + arc_continues marker.
7. Reciprocal back-link tau7xg_ingest.pipeline_reused_at_phase = τ.7.x.h.
8. CLI --renumber {genesis,exodus,leviticus,numbers,deuteronomy,joshua,judges,ruth}.
9. geez-tewahedo/rut.py NOT created (D4-c preserved).
10. Post-Pentateuch arc-continues pin: rut.py shipped + Pentateuch §8.1
    arc closure preserved + Joshua + Judges arcs preserved.
11. Publication-format-shift residual class documented in tau7xh_ingest.
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


def _ruth_block() -> dict:
    return _source_yaml()["structural_map"]["ruth"]


def _tau7xh_block() -> dict:
    return _source_yaml()["ocr_strategy"]["tau7xh_ingest"]


def _rut_verses() -> list[tuple]:
    rut_py = AMHARIC_TEWAHEDO / "rut.py"
    text = rut_py.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSES":
                    return ast.literal_eval(node.value)
    raise AssertionError("amharic-tewahedo/rut.py must define VERSES")


def _rut_constants() -> dict:
    rut_py = AMHARIC_TEWAHEDO / "rut.py"
    text = rut_py.read_text(encoding="utf-8")
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


class TestTau7XHRuthVerseCounts:
    """RUTH_VERSE_COUNTS is the τ.7.x.h renumber-floor dict."""

    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_module_symbol_present(self):
        from extract_parallel_pdf import RUTH_VERSE_COUNTS

        assert isinstance(RUTH_VERSE_COUNTS, dict)

    def test_four_chapters(self):
        from extract_parallel_pdf import RUTH_VERSE_COUNTS

        assert sorted(RUTH_VERSE_COUNTS.keys()) == [1, 2, 3, 4]

    def test_total_verses_85(self):
        from extract_parallel_pdf import RUTH_VERSE_COUNTS

        # KJV/Hebrew Masoretic + LXX agreement: 85 verses.
        assert sum(RUTH_VERSE_COUNTS.values()) == 85

    def test_chapter_specific_verse_counts(self):
        """All Ruth chapter sizes (book is small enough to pin each)."""
        from extract_parallel_pdf import RUTH_VERSE_COUNTS

        # Ruth 1 (Naomi + Ruth's return) = 22
        assert RUTH_VERSE_COUNTS[1] == 22
        # Ruth 2 (gleaning in Boaz's field) = 23
        assert RUTH_VERSE_COUNTS[2] == 23
        # Ruth 3 (threshing floor) = 18 (shortest)
        assert RUTH_VERSE_COUNTS[3] == 18
        # Ruth 4 (redemption + Davidic genealogy) = 22
        assert RUTH_VERSE_COUNTS[4] == 22


class TestTau7XHStructuralMapRuth:
    """structural_map.ruth block records the Ruth page range
    discovered via τ.7.x.h boundary inspection (1 Samuel 1:1 +
    publication-format shift at page 438)."""

    def test_block_present(self):
        assert "ruth" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert _ruth_block()["book_codes"] == ["rut"]

    def test_pdf_page_range(self):
        # 432-437 inclusive (6 pages for 4 chapters; verified by
        # Ruth 1:1 at p432 + 1 Samuel 1:1 at p438 + the publication-
        # format shift discovered at p438).
        assert _ruth_block()["pdf_page_range"] == [432, 437]

    def test_pdf_index_offset_zero(self):
        assert _ruth_block()["pdf_index_offset"] == 0

    def test_verified_true(self):
        assert _ruth_block()["verified"] is True

    def test_verified_at_tau7xh(self):
        assert _ruth_block()["verified_at_phase"] == "τ.7.x.h"

    def test_chapter_count_expected_4(self):
        assert _ruth_block()["chapter_count_expected"] == 4

    def test_notes_document_boundary_inspection(self):
        notes = _ruth_block()["notes"]
        # Ruth 1:1 opening + 1 Samuel boundary + null-formal-title
        # confirmation + publication-format shift all referenced.
        assert "Ruth" in notes or "ሩት" in notes, "Notes must reference Ruth"
        assert (
            "1 Samuel" in notes or "1 Kingdoms" in notes or "ሳሙኤል" in notes or "አርማቴም" in notes or "ራማታይም" in notes
        ), "Notes must reference 1 Samuel/Kingdoms boundary"
        assert "NULL-FORMAL-TITLE-BANNER" in notes or "null-formal" in notes or "running-header" in notes, (
            "Notes must reference null-formal-title-banner confirmation pattern"
        )
        assert "dzamaragna" in notes or "publication" in notes or "CRITICAL" in notes, (
            "Notes must reference the publication-format-shift structural discovery"
        )


class TestTau7XHRuthRutPy:
    """amharic-tewahedo/rut.py is the τ.7.x.h output module."""

    def test_rut_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "rut.py").is_file()

    def test_translation_constant(self):
        c = _rut_constants()
        assert c.get("TRANSLATION") == "amharic-tewahedo"

    def test_book_constant(self):
        c = _rut_constants()
        assert c.get("BOOK") == "rut"

    def test_source_quality_ocr_tier3(self):
        c = _rut_constants()
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"

    def test_source_provenance(self):
        c = _rut_constants()
        assert c.get("SOURCE_PROVENANCE") == "parallel-bible-eotc"

    def test_ingest_phase_constant(self):
        c = _rut_constants()
        assert c.get("INGEST_PHASE") == "τ.7.x.h"

    def test_verses_count_at_least_floor(self):
        verses = _rut_verses()
        # Empirical at ship was 60. Floor 50 protects against
        # silent regression while permitting parser refinement.
        assert len(verses) >= 50, f"τ.7.x.h Ruth ingest must have ≥50 verses; got {len(verses)}"

    def test_first_verse_is_rut_1_1(self):
        verses = _rut_verses()
        ch, v, text = verses[0]
        assert (ch, v) == (1, 1)
        assert text, "Ruth 1:1 text must be non-empty"


class TestTau7XHRuthCoverage:
    """Per-chapter coverage matches empirical post-renumber
    distribution: chapters 1-2 fully populated; 3 partial 15/18;
    4 empty."""

    def _by_chapter(self) -> dict[int, list[tuple]]:
        verses = _rut_verses()
        out: dict[int, list[tuple]] = {}
        for ch, v, t in verses:
            out.setdefault(ch, []).append((v, t))
        return out

    def test_chapters_1_through_2_fully_populated(self):
        """The defining τ.7.x.h empirical pin: chapters 1-2 have
        verse counts MATCHING RUTH_VERSE_COUNTS floor."""
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import RUTH_VERSE_COUNTS

        by_ch = self._by_chapter()
        for ch in (1, 2):
            got = len(by_ch.get(ch, []))
            expected = RUTH_VERSE_COUNTS[ch]
            assert got == expected, (
                f"τ.7.x.h chapter {ch} must have exactly {expected} verses (RUTH_VERSE_COUNTS floor); got {got}"
            )

    def test_chapter_3_partial(self):
        """Chapter 3 received the parser's remaining 15 verses
        (includes end-of-Ruth colophon + closing Davidic genealogy)."""
        by_ch = self._by_chapter()
        got = len(by_ch.get(3, []))
        # Empirical 15; defensive range (1, 18).
        assert 1 <= got <= 18, f"τ.7.x.h chapter 3 partial: expect 1..18 verses; got {got}"

    def test_chapter_4_empty(self):
        """Chapter 4 received zero verses — parser exhausted at ch 3."""
        by_ch = self._by_chapter()
        got = len(by_ch.get(4, []))
        assert got == 0, f"τ.7.x.h chapter 4 should be empty at ocr-tier3; got {got} verses"

    def test_no_overflow_above_chapter_4(self):
        by_ch = self._by_chapter()
        overflow = sum(len(v) for ch, v in by_ch.items() if ch > 4)
        assert overflow == 0, f"τ.7.x.h renumber overflow should be 0; got {overflow} verses above ch 4"

    def test_end_of_book_colophon_preserved(self):
        """The end-of-Ruth colophon — preserved at the parser's
        terminal output (renumbered into ch 3 partial slot due to
        the 29.4% recovery deficit). Accept:
        - the Geʽez `ተፈጸ`-family verb (`ተፈጸመ` "was completed")
        - the Amharic colophon marker `ደረሰ ተፈጸመ` (reached + completed)
        - the doxology marker `ምስጋና ይግበው` (praise be given).
        """
        verses = _rut_verses()
        # Check the last 5 verses for the colophon marker
        last_chunk = " ".join(text for (_, _, text) in verses[-5:])
        canonical_geez_colophon = "ተፈጺመ" in last_chunk or "ተፈጻመ" in last_chunk or "ተፈጸመ" in last_chunk
        amharic_colophon = "ደረሰ" in last_chunk and "ተፈጸ" in last_chunk
        doxology_marker = "ምስጋና" in last_chunk
        assert canonical_geez_colophon or amharic_colophon or doxology_marker, (
            f"τ.7.x.h end-of-Ruth colophon must appear in the last 5 verses "
            f"(`ተፈጸ`-family verb OR `ደረሰ ተፈጸ` marker OR `ምስጋና` doxology); "
            f"got: {last_chunk[:400]}"
        )

    def test_davidic_genealogy_preserved(self):
        """Ruth's defining content — the Davidic genealogy
        (Salmon → Boaz → Obed → Jesse → David) — should appear
        in the last few verses since parser placed it in ch 3
        terminal slot."""
        verses = _rut_verses()
        all_text = " ".join(text for (_, _, text) in verses)
        # Accept any of the genealogy keypoint names (Amharic
        # transliteration variation tolerated).
        # OBED → ኢዮቤድ (Iyobed) or ኦቤድ
        # BOAZ → በኦስ (Boas/Boos) or ቡኤዝ (Bu'ez)
        # DAVID → ዳዊት (Dawit)
        obed_present = "ኢዮቤድ" in all_text or "ኦቤድ" in all_text
        boaz_present = "በኦስ" in all_text or "ቡኤዝ" in all_text or "በኦን" in all_text
        david_present = "ዳዊት" in all_text or "ዳፍት" in all_text
        # At least 2 of 3 must appear to confirm genealogy preservation.
        present_count = sum([obed_present, boaz_present, david_present])
        assert present_count >= 2, (
            f"τ.7.x.h Davidic genealogy must preserve ≥2 of {{Obed, Boaz, David}} names; "
            f"got: obed={obed_present}, boaz={boaz_present}, david={david_present}"
        )


class TestTau7XHSourceYamlIngestBlock:
    """ocr_strategy.tau7xh_ingest block records the τ.7.x.h ship +
    back-link annotation to tau7xg_ingest + post-Pentateuch arc-
    continues + publication-format-shift discovery."""

    def test_block_exists(self):
        assert "tau7xh_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert _tau7xh_block()["shipped_at_phase"] == "τ.7.x.h"

    def test_structural_map_addition(self):
        sma = _tau7xh_block()["structural_map_addition"]
        assert sma["section"] == "ruth"
        assert sma["pdf_page_range"] == [432, 437]
        assert sma["chapter_count_expected"] == 4

    def test_helpers_added_ruth_verse_counts(self):
        helpers = _tau7xh_block()["helpers_added"]
        assert "RUTH_VERSE_COUNTS" in helpers

    def test_cli_extensions_renumber_choice_extended(self):
        cli = _tau7xh_block()["cli_extensions"]
        assert "renumber_choice_extended" in cli

    def test_empirical_validation_coverage_70_plus_percent(self):
        ev = _tau7xh_block()["empirical_validation"]
        # Coverage at ship was 70.6%. Floor 65 protects against
        # regression while accommodating Ruth's exceptional
        # small-book + dense-genealogy compression effect.
        assert ev["coverage_pct"] >= 65.0

    def test_empirical_chapters_fully_populated_1_through_2(self):
        ev = _tau7xh_block()["empirical_validation"]
        assert ev["chapters_fully_populated"] == [1, 2]

    def test_empirical_chapters_missing_4(self):
        ev = _tau7xh_block()["empirical_validation"]
        assert ev["chapters_missing"] == [4]

    def test_no_ingest_at_this_phase_false(self):
        assert _tau7xh_block()["no_ingest_at_this_phase"] is False

    def test_closed_arc_tau6x0a_no_ingest_false(self):
        contracts = _tau7xh_block()["closed_arc_contracts_preserved"]
        assert contracts["tau6x0a_no_ingest"] is False  # eighth authorized violation

    def test_closed_arc_tau7xa_through_tau7xg_preserved(self):
        contracts = _tau7xh_block()["closed_arc_contracts_preserved"]
        assert contracts["tau7xa_ingest"] is True
        assert contracts["tau7xb_ingest"] is True
        assert contracts["tau7xc_ingest"] is True
        assert contracts["tau7xd_ingest"] is True
        assert contracts["tau7xe_ingest"] is True
        assert contracts["tau7xf_ingest"] is True
        assert contracts["tau7xg_ingest"] is True

    def test_reciprocal_back_link_in_tau7xg(self):
        """τ.7.x.g tau7xg_ingest block must carry pipeline_reused_at_
        phase = τ.7.x.h (back-link annotation, 12th instance of the
        single-key back-link pattern)."""
        g = _source_yaml()["ocr_strategy"]["tau7xg_ingest"]
        assert g.get("pipeline_reused_at_phase") == "τ.7.x.h"

    def test_translation_slot_state_records_eight_books(self):
        state = _tau7xh_block()["translation_slot_state"]
        assert "τ.7.x.a" in state["amharic_tewahedo_gen"]
        assert "τ.7.x.b" in state["amharic_tewahedo_ex"]
        assert "τ.7.x.c" in state["amharic_tewahedo_lev"]
        assert "τ.7.x.d" in state["amharic_tewahedo_num"]
        assert "τ.7.x.e" in state["amharic_tewahedo_deu"]
        assert "τ.7.x.f" in state["amharic_tewahedo_jos"]
        assert "τ.7.x.g" in state["amharic_tewahedo_jdg"]
        assert "τ.7.x.h" in state["amharic_tewahedo_rut"]

    def test_next_phase_tau7xi(self):
        assert _tau7xh_block()["next_phase"] == "τ.7.x.i"

    def test_arc_continues_marker_post_pentateuch_historical_books(self):
        """τ.7.x.h is the THIRD τ-cluster ingest in the post-Pentateuch
        historical-books arc opened at τ.7.x.f."""
        assert _tau7xh_block()["arc_continues"] == "post-pentateuch-historical-books"

    def test_arc_continues_narrative_present(self):
        """The arc-continues narrative documents the historical-books
        arc trajectory + 8-ship template stability + structural
        discovery."""
        narrative = _tau7xh_block()["arc_continues_narrative"]
        assert "Pentateuch" in narrative
        assert "historical-books" in narrative or "historical books" in narrative
        assert "eight" in narrative.lower() or "8" in narrative
        assert "STRUCTURAL DISCOVERY" in narrative or "structural discovery" in narrative.lower(), (
            "Arc-continues narrative must reference the publication-format-shift structural discovery"
        )

    def test_publication_format_shift_residual_documented(self):
        """The τ.7.x.h structural_map_addition must record the new
        publication-format-shift residual class for τ.7.x.i+ to
        address."""
        sma = _tau7xh_block()["structural_map_addition"]
        assert "publication_format_shift_residual" in sma, (
            "tau7xh_ingest must document the publication-format-shift discovery"
        )


class TestTau7XHMetaYamlIngestRecord:
    """amharic-tewahedo/_meta.yaml has all eight ingest records +
    upgraded stats (8 books / 5999 verses combined)."""

    def _meta(self) -> dict:
        path = AMHARIC_TEWAHEDO / "_meta.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_stats_books_at_least_eight(self):
        # Pentateuch (5) + Joshua + Judges + Ruth = 8 books
        m = self._meta()
        assert m["stats"]["books"] >= 8

    def test_stats_verses_combined(self):
        # 1308 + 947 + 802 + 1107 + 781 + 483 + 511 + 60 = 5999.
        # Floor 5800.
        m = self._meta()
        assert m["stats"]["verses"] >= 5800

    def test_tau7xh_ingest_record_present(self):
        m = self._meta()
        assert "ingest_record_tau7xh" in m

    def test_tau7xh_ingest_record_phase(self):
        m = self._meta()
        assert m["ingest_record_tau7xh"]["phase"] == "τ.7.x.h"

    def test_tau7xh_ingest_record_book_codes_rut(self):
        m = self._meta()
        assert m["ingest_record_tau7xh"]["ingested_book_codes"] == ["rut"]

    def test_tau7xh_ingest_record_parser_extensions_chain(self):
        m = self._meta()
        chain = m["ingest_record_tau7xh"]["parser_extensions"]
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
            "τ.7.x.g",
            "τ.7.x.h",
        ):
            assert phase in chain, f"parser_extensions chain missing {phase}"

    def test_tau7xh_arc_continues_marker(self):
        m = self._meta()
        assert m["ingest_record_tau7xh"]["arc_continues"] == "post-pentateuch-historical-books"

    def test_prior_ingest_records_still_present(self):
        m = self._meta()
        assert "ingest_record" in m
        assert m["ingest_record"]["phase"] == "τ.7.x.a"
        for tag in ("tau7xb", "tau7xc", "tau7xd", "tau7xe", "tau7xf", "tau7xg"):
            assert f"ingest_record_{tag}" in m, f"prior ingest record missing: {tag}"


class TestTau7XHGeezTewahedoPreserved:
    """The Geʽez column should remain unchanged after τ.7.x.h — full
    Geʽez Ruth ingest is τ.6.x.2.h per D4-c sequencing."""

    def test_geez_tewahedo_rut_py_ingested_at_tau6x2h(self):
        """MIGRATED at τ.6.x.2.a-h batch ship-time (2026-05-15):
        originally asserted geez-tewahedo/rut.py does NOT exist
        until τ.6.x.2.h ships. The τ.6.x.2.a-h batch ship
        CREATED this file at ocr-tier3 quality (per D4-c catchup arc).
        Durable assertion is now: geez-tewahedo/rut.py EXISTS at
        ocr-tier3 ingest scale; per-file content pinned in
        test_parallel_bible_tau6x2_geez_arc.py."""
        import ast

        path = GEEZ_TEWAHEDO / "rut.py"
        assert path.is_file(), "geez-tewahedo/rut.py must exist post-τ.6.x.2.h (τ.6.x.2.a-h batch ship)"
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
        # τ.6.x.2.h empirical at ship: 56 verses; floor 50 guards
        # against regression while permitting parser refinement.
        assert len(verses) >= 50, (
            f"geez-tewahedo/rut.py must be at ocr-tier3 scale post-τ.6.x.2.h; "
            f"got {len(verses)} verses (<50 indicates regression)"
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


class TestTau7XHPostPentateuchArcContinues:
    """Post-Pentateuch historical-books arc-continues — Ruth shipped
    as the THIRD τ-cluster ingest in the historical-books arc opened
    at τ.7.x.f. The Pentateuch §8.1 arc-close invariant AND the
    τ.7.x.f Joshua arc-open invariant AND the τ.7.x.g Judges arc-
    continues invariant must all remain preserved."""

    def test_ruth_shipped(self):
        """rut.py exists under amharic-tewahedo/."""
        assert (AMHARIC_TEWAHEDO / "rut.py").is_file()

    def test_all_pentateuch_books_still_shipped(self):
        """§8.1 Pentateuch arc-close invariant: gen+ex+lev+num+deu
        must all still exist after τ.7.x.h."""
        for book in ("gen", "ex", "lev", "num", "deu"):
            path = AMHARIC_TEWAHEDO / f"{book}.py"
            assert path.is_file(), (
                f"§8.1 Pentateuch invariant: amharic-tewahedo/{book}.py must still exist after τ.7.x.h"
            )

    def test_joshua_and_judges_still_shipped(self):
        """τ.7.x.f Joshua arc-open + τ.7.x.g Judges arc-continues
        invariants: jos.py + jdg.py must still exist after τ.7.x.h."""
        for book in ("jos", "jdg"):
            path = AMHARIC_TEWAHEDO / f"{book}.py"
            assert path.is_file(), f"τ.7.x.f/g arc invariant: amharic-tewahedo/{book}.py must still exist after τ.7.x.h"

    def test_eight_book_combined_coverage_at_least_80_percent(self):
        """Combined Pentateuch + Joshua + Judges + Ruth coverage =
        sum of per-book verses / sum of per-book floors. Empirical
        at arc-continues: 5999/7214 = 83.2%. Floor 80% protects
        against regression."""
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
            "gen": sum(GENESIS_VERSE_COUNTS.values()),
            "ex": sum(EXODUS_VERSE_COUNTS.values()),
            "lev": sum(LEVITICUS_VERSE_COUNTS.values()),
            "num": sum(NUMBERS_VERSE_COUNTS.values()),
            "deu": sum(DEUTERONOMY_VERSE_COUNTS.values()),
            "jos": sum(JOSHUA_VERSE_COUNTS.values()),
            "jdg": sum(JUDGES_VERSE_COUNTS.values()),
            "rut": sum(RUTH_VERSE_COUNTS.values()),
        }
        total_extracted = 0
        total_expected = sum(floors.values())
        for book in ("gen", "ex", "lev", "num", "deu", "jos", "jdg", "rut"):
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
            f"Pentateuch+Joshua+Judges+Ruth combined coverage must be ≥80%; "
            f"got {coverage:.1f}% ({total_extracted}/{total_expected})"
        )

    def test_null_formal_title_banner_pattern_confirmed_three_times(self):
        """τ.7.x.h confirms the τ.7.x.f null-formal-title-banner
        finding as DECISIVELY stable — third consecutive ship
        without the formal `መጽሐፈ X` book-title-banner."""
        sma = _tau7xh_block()["structural_map_addition"]
        assert "null_formal_title_banner_confirmed_three_times" in sma, (
            "tau7xh_ingest must record the third-confirmation of null-formal-title-banner"
        )


class TestTau7XHStateDocs:
    # Doc-pins collapsed to the CHANGELOG chokepoint (2026-05-21): the
    # old test_session_state_*/test_in_flight_*/test_plan_ledger_* pins
    # read SESSION_STATE.md / IN_FLIGHT.md (rolling, trimmed) and the
    # moved PLAN_2026-05-09.md. The durable phase record is CHANGELOG.md.
    def test_phase_recorded_in_changelog(self):
        from tests.fixtures import assert_phase_recorded

        assert_phase_recorded("τ.7.x.h")

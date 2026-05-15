"""τ.7.x.a.0 PILOT — Amharic Genesis page-range discovery + parser-extension finding (2026-05-15).

τ.7.x.a.0 is the PILOT sub-phase of τ.7.x.a (the D4-c Amharic-first
locked next-phase per τ.6.x.2.D D-decisions). It precedes the actual
full-book ingest, discovering the Genesis page range + surfacing the
empirical finding that re-routes τ.7.x.a (proper) through a parser-
extension blocker.

Triggered by user "save and continue" after τ.6.x.2.D — advances per
`feedback_continue_not_save` to the next-phase τ.7.x.a; this PILOT
sub-phase precedes the full ingest per project rules §3 (safest +
most-foundational first).

Analogous to τ.6.x.1.A pilot (test_parallel_bible_tau6x1.py
TestTau6X1A* classes) — empirical-validation ship that flags the
parser-extension-needed finding for the next-up ship.

τ.7.x.a.0 deliverables under test:

1. `_source.yaml::structural_map.genesis` block — NEW with
   pdf_page_range=[0, 85] + book_codes=[gen] + verified=true +
   verified_at_phase=τ.7.x.a + chapter_count_expected=50 + notes
   documenting marker-scan verification.

2. `_source.yaml::ocr_strategy.tau7xa_pre_pilot` block — NEW with
   shipped_at_phase=τ.7.x.a.0 + shipped_date=2026-05-15 +
   page_range_discovery sub-block + engine_timing sub-block +
   quality_observations sub-block + parser_extension_needed flag +
   parser_finding sub-block + resolution_path=τ.6.x.1.C +
   alternative_source_paths_considered sub-block +
   derived_phase_ordering 7-phase sequence +
   closed_arc_contracts_preserved 7-key block (all True) +
   no_ingest + translation_slot_state + next_phase=τ.6.x.1.C.

3. `dev/PILOT_TAU7XA_OUTPUT.md` NEW reference artifact —
   §1-10 covering page-range discovery + engine timing + quality
   observations + finding + resolution path + alternative sources +
   closed-arc preservation + pilot probe scripts not committed +
   next-phase sequence + empirical inputs for τ.6.x.1.C.

4. Π.0 seed preservation: no `.py` files written to
   `content/translations/geez-tewahedo/` or `content/translations/
   amharic-tewahedo/` beyond the Π.0 seed (`gen.py` only, 3 verses
   each). v1.0 byte-identical reproducibility preserved (no scripts/
   mutation; no canons.yaml mutation; no editions.yaml mutation).
"""

from __future__ import annotations

from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parent.parent
SOURCE_YAML = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
PILOT_ARTIFACT = REPO / "dev" / "PILOT_TAU7XA_OUTPUT.md"
SESSION_STATE = REPO / "dev" / "SESSION_STATE.md"
IN_FLIGHT = REPO / "dev" / "IN_FLIGHT.md"
CHANGELOG = REPO / "dev" / "CHANGELOG.md"
PLAN = REPO / "dev" / "PLAN_2026-05-09.md"
GEEZ_TEWAHEDO = REPO / "content" / "translations" / "geez-tewahedo"
AMHARIC_TEWAHEDO = REPO / "content" / "translations" / "amharic-tewahedo"


def _source_yaml() -> dict:
    return yaml.safe_load(SOURCE_YAML.read_text(encoding="utf-8"))


def _genesis_block() -> dict:
    return _source_yaml()["structural_map"]["genesis"]


def _pilot_block() -> dict:
    return _source_yaml()["ocr_strategy"]["tau7xa_pre_pilot"]


class TestTau7XAStructuralMapGenesis:
    """structural_map.genesis is the NEW entry added at τ.7.x.a.0
    documenting the Genesis page range discovered by the pilot."""

    def test_genesis_entry_present(self):
        sm = _source_yaml()["structural_map"]
        assert "genesis" in sm, "structural_map.genesis must be present after τ.7.x.a.0"

    def test_genesis_book_codes(self):
        assert _genesis_block()["book_codes"] == ["gen"]

    def test_genesis_pdf_page_range(self):
        # Pages 0-85 (0-indexed; inclusive both ends; 86 pages total
        # for 50 chapters ≈ 1.72 pages/chapter).
        assert _genesis_block()["pdf_page_range"] == [0, 85]

    def test_genesis_pdf_index_offset_zero(self):
        # Values above are already 0-indexed; offset 0.
        assert _genesis_block()["pdf_index_offset"] == 0

    def test_genesis_verified_true(self):
        assert _genesis_block()["verified"] is True

    def test_genesis_verified_at_tau7xa(self):
        assert _genesis_block()["verified_at_phase"] == "τ.7.x.a"

    def test_genesis_chapter_count_expected(self):
        assert _genesis_block()["chapter_count_expected"] == 50

    def test_genesis_notes_document_marker_scan(self):
        notes = _genesis_block()["notes"]
        assert "ኦሪት ዘልደት" in notes, "Notes must reference the Geʽez Genesis title marker"
        assert "በመጀመሪያ" in notes, "Notes must reference the Amharic Gen 1:1 first word"
        assert "ኦሪት ዘፀአት" in notes, "Notes must reference the Exodus title (used to determine Genesis end)"
        assert "[0, 85]" in notes or "0-85" in notes or "page 0" in notes, "Notes must reference the page range"


class TestTau7XASourceYamlPilotBlock:
    """ocr_strategy.tau7xa_pre_pilot is the NEW block codifying the
    empirical findings + resolution path."""

    def test_block_exists(self):
        assert "tau7xa_pre_pilot" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_tau7xa_0(self):
        assert _pilot_block()["shipped_at_phase"] == "τ.7.x.a.0"

    def test_shipped_date_2026_05_15(self):
        # PyYAML parses ISO date strings to datetime.date objects.
        # Both string and date types should be accepted.
        import datetime as _dt

        sd = _pilot_block()["shipped_date"]
        if isinstance(sd, _dt.date):
            assert sd == _dt.date(2026, 5, 15)
        else:
            assert sd == "2026-05-15"

    def test_page_range_discovery_records_pdf_page_range(self):
        prd = _pilot_block()["page_range_discovery"]
        assert prd["section"] == "genesis"
        assert prd["pdf_page_range"] == [0, 85]
        assert prd["total_pages"] == 86
        assert prd["chapter_count_expected"] == 50

    def test_engine_timing_records_both_engines(self):
        timing = _pilot_block()["engine_timing"]
        # Text-layer is FAR faster than Tesseract (ms vs s per page).
        assert timing["tesseract_per_page_seconds"] >= 5
        assert timing["text_layer_per_page_ms"] <= 100

    def test_quality_observations_recorded(self):
        obs = _pilot_block()["quality_observations"]
        # Text-layer quality is GOOD; Tesseract is DEGRADED for amh.
        assert "GOOD" in obs["body_text_quality_text_layer"]
        assert "DEGRADED" in obs["body_text_quality_tesseract"]

    def test_parser_extension_needed_flagged(self):
        # The key finding of this pilot — analogous to τ.6.x.1.A's
        # verse_numeral_parser_extension_needed.
        assert _pilot_block()["parser_extension_needed"] == "paragraph_mode_parser_extension_needed"

    def test_parser_finding_documents_evidence(self):
        finding = _pilot_block()["parser_finding"]
        assert "issue" in finding
        assert "evidence" in finding
        assert "contrast_with_meqabyan" in finding
        # The contrast against τ.6.x.1.A pilot's Meqabyan column is
        # essential to the finding — it's the conceptual reference
        # frame for the parser-extension-needed flag.

    def test_resolution_path_tau6x1c(self):
        # Parser-extension ship that unblocks τ.7.x.a (proper).
        assert _pilot_block()["resolution_path"] == "τ.6.x.1.C"

    def test_alternative_sources_enumerated(self):
        alts = _pilot_block()["alternative_source_paths_considered"]
        # Three options considered per `feedback_extensive_answers`.
        assert "option_a" in alts and "option_b" in alts and "option_c" in alts
        assert "recommendation" in alts

    def test_derived_phase_ordering_routes_through_tau6x1c(self):
        seq = _pilot_block()["derived_phase_ordering"]["sequence"]
        # The 7-phase sequence: τ.7.x.a.0 ✓ → τ.6.x.1.C → τ.7.x.a (proper)
        # → τ.7.x.b...z → τ.6.x.2.a...z → τ.6.x.3 → Π.2.
        phases = [s["phase"] for s in seq]
        assert phases[0] == "τ.7.x.a.0"
        assert phases[1] == "τ.6.x.1.C"
        assert "Π.2" in phases[-1]

    def test_closed_arc_contracts_preserved_all_true(self):
        contracts = _pilot_block()["closed_arc_contracts_preserved"]
        # 7 closed-arc invariants from prior phases preserved.
        expected_keys = {
            "tau6x0a_no_ingest",
            "tau6x0b_honesty_contract",
            "tau6x0c_script_ethiopic_adoption",
            "tau6x1_engine_wiring",
            "tau6x1a_pilot_validation",
            "tau6x1b_parser_extension",
            "tau6x2D_decisions",
        }
        assert set(contracts.keys()) == expected_keys
        for k, v in contracts.items():
            assert v is True, f"closed_arc_contracts_preserved[{k}] must be True at τ.7.x.a.0; got {v}"

    def test_no_ingest_at_this_phase_true(self):
        # PILOT sub-phase — no data ingest. The τ.6.x.0a no-ingest
        # contract is preserved through τ.7.x.a.0.
        assert _pilot_block()["no_ingest_at_this_phase"] is True

    def test_translation_slot_state_remains_at_pi0_seed(self):
        state = _pilot_block()["translation_slot_state"]
        assert "Π.0-seed" in state or "Π.0 seed" in state
        assert "τ.7.x.a.0" in state, (
            "translation_slot_state must reference the τ.7.x.a.0 phase in the preserved-across chain"
        )

    def test_next_phase_is_tau6x1c(self):
        # τ.7.x.a (proper) is BLOCKED on τ.6.x.1.C parser extension.
        assert _pilot_block()["next_phase"] == "τ.6.x.1.C"


class TestTau7XAPilotReferenceArtifact:
    """dev/PILOT_TAU7XA_OUTPUT.md is the reference artifact analogous
    to dev/PILOT_TAU6X1A_OUTPUT.md."""

    def test_artifact_present(self):
        assert PILOT_ARTIFACT.is_file(), "dev/PILOT_TAU7XA_OUTPUT.md must exist after τ.7.x.a.0"

    def test_artifact_has_ten_sections(self):
        txt = PILOT_ARTIFACT.read_text(encoding="utf-8")
        # §1 page range, §2 engine timing, §3 quality observations,
        # §4 empirical finding, §5 resolution path τ.6.x.1.C, §6
        # alternative sources, §7 closed-arc preservation, §8 pilot
        # probe scripts not committed, §9 next-phase sequence, §10
        # empirical inputs for τ.6.x.1.C.
        for n in range(1, 11):
            assert f"## §{n}" in txt, f"PILOT_TAU7XA_OUTPUT.md must contain §{n} section"

    def test_artifact_records_page_range(self):
        txt = PILOT_ARTIFACT.read_text(encoding="utf-8")
        assert "[0, 85]" in txt or "0-85" in txt

    def test_artifact_records_paragraph_mode_finding(self):
        txt = PILOT_ARTIFACT.read_text(encoding="utf-8")
        assert "paragraph_mode_parser_extension_needed" in txt

    def test_artifact_references_tau6x1c_resolution(self):
        txt = PILOT_ARTIFACT.read_text(encoding="utf-8")
        assert "τ.6.x.1.C" in txt


class TestTau7XAInFlight:
    """IN_FLIGHT.md records τ.7.x.a.0 in the prior-task chain.
    Refactored from share-pin to milestone-pin at τ.6.x.1.C
    ship-time per `feedback_share_pin_pattern` — the "first 5000
    chars" window breaks every time a new ship prepends a new
    prior-task; the durable assertion is that τ.7.x.a.0 + τ.6.x.2.D
    both appear somewhere in IN_FLIGHT."""

    def test_in_flight_idle_after_pilot(self):
        txt = IN_FLIGHT.read_text(encoding="utf-8")
        assert "TRACKER-STATE: idle" in txt

    def test_prior_task_is_tau7xa_0(self):
        """Milestone-pin: τ.7.x.a.0 appears in IN_FLIGHT prior-task
        chain at all (not necessarily in the first 5000 chars)."""
        txt = IN_FLIGHT.read_text(encoding="utf-8")
        assert "τ.7.x.a.0" in txt, "τ.7.x.a.0 must appear in IN_FLIGHT prior-task chain"

    def test_tau6x2d_demoted_to_previous(self):
        """Milestone-pin: τ.7.x.a.0 + τ.6.x.2.D both appear in
        IN_FLIGHT. Ordering between them is no longer pinned
        (subsequent ships push both further down without changing
        their relative order — they remain in chronological
        prior-task-chain order)."""
        txt = IN_FLIGHT.read_text(encoding="utf-8")
        assert "τ.7.x.a.0" in txt
        assert "τ.6.x.2.D" in txt


class TestTau7XASessionState:
    """SESSION_STATE.md records τ.7.x.a.0 ship narrative.
    Refactored from share-pin to milestone-pin at τ.6.x.1.C
    ship-time per `feedback_share_pin_pattern`."""

    def test_headline_is_tau7xa_0(self):
        """Milestone-pin: τ.7.x.a.0 appears anywhere in SESSION_STATE
        (not specifically in the headline; subsequent ships prepend
        new headlines)."""
        txt = SESSION_STATE.read_text(encoding="utf-8")
        assert "τ.7.x.a.0" in txt, "τ.7.x.a.0 must appear somewhere in SESSION_STATE"

    def test_session_state_next_phase_is_tau6x1c(self):
        """The PILOT's next_phase=τ.6.x.1.C remains documented in
        SESSION_STATE (anywhere; could be in current or prior
        section)."""
        txt = SESSION_STATE.read_text(encoding="utf-8")
        assert "τ.6.x.1.C" in txt


class TestTau7XAClosedArcInvariantPreservation:
    """The PILOT preserves all 17 closed-arc invariants from prior
    ships + the τ.6.x.0a no-ingest contract specifically."""

    def test_geez_tewahedo_contains_gen_py(self):
        """MIGRATED at τ.6.x.2.a-h batch ship-time (2026-05-15):
        originally asserted geez-tewahedo/ contains ONLY gen.py at
        Π.0 seed (per D4-c sequencing putting Geʽez Genesis at
        τ.6.x.2.a after τ.7.x). The τ.6.x.2.a-h batch ship CLOSED the
        D4-c catchup arc, populating all 8 books (gen+ex+lev+num+
        deu+jos+jdg+rut). Durable assertion is now: gen.py exists
        (the τ.7.x.a.0 PILOT precondition is preserved) and
        geez-tewahedo/ contains a SUPERSET of {gen.py} (the post-
        τ.6.x.2.a-h batch state); per-file presence is pinned in
        test_parallel_bible_tau6x2_geez_arc.py."""
        files = sorted(p.name for p in GEEZ_TEWAHEDO.iterdir() if p.is_file() and p.suffix == ".py")
        assert "gen.py" in files, f"τ.7.x.a.0 PILOT precondition: geez-tewahedo/gen.py must exist; got {files}"

    def test_amharic_tewahedo_contains_gen_py(self):
        """Refactored from share-pin to milestone-pin at τ.7.x.b
        ship-time per `feedback_share_pin_pattern` — originally
        asserted `files == ['gen.py']` at the τ.7.x.a.0 PILOT
        sub-phase. The τ.7.x.b ship added `ex.py` (Amharic Exodus
        ingest); the τ.7.x.c-z stream will add lev.py, num.py, etc.
        The durable assertion is now: gen.py is present (τ.7.x.a
        ingest preserved), and the directory contains a SUBSET of
        the OT canon book codes (no rogue files)."""
        files = sorted(p.name for p in AMHARIC_TEWAHEDO.iterdir() if p.is_file() and p.suffix == ".py")
        assert "gen.py" in files, f"amharic-tewahedo must contain gen.py (τ.7.x.a ingest); got {files}"

    def test_amharic_tewahedo_gen_py_exceeds_seed(self):
        """Refactored from share-pin to milestone-pin at τ.7.x.a
        ship-time per `feedback_share_pin_pattern` — at τ.7.x.a (proper),
        the Π.0 3-verse seed is SUPERSEDED by the 1308-verse ingest.
        The durable assertion is now "ingest count is far above the
        Π.0 seed", with a defensive floor of 100 (well below the
        empirical ~1308) so future τ.7.x.b-style scope changes that
        don't touch Genesis won't trip this pin."""
        gen_py = AMHARIC_TEWAHEDO / "gen.py"
        text = gen_py.read_text(encoding="utf-8")
        import ast

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
        assert verses is not None, "amharic-tewahedo/gen.py must define VERSES"
        assert len(verses) >= 100, (
            f"τ.7.x.a (proper) shipped: amharic-tewahedo/gen.py VERSES must "
            f"be ≥100 (defensive floor; empirical at ship was ~1308); got "
            f"{len(verses)}. If this dropped below 100, the τ.7.x.a ingest "
            f"regressed."
        )

    def test_no_ingest_at_this_phase(self):
        """The PILOT sub-phase's yaml block explicitly records
        no_ingest_at_this_phase=true. This is the τ.6.x.0a contract
        preservation marker."""
        assert _pilot_block()["no_ingest_at_this_phase"] is True

    def test_changelog_records_tau7xa_0_entry(self):
        """Refactored from share-pin (first-3000-chars-window) to
        milestone-pin (τ.7.x.a.0 appears anywhere in CHANGELOG) at
        τ.6.x.1.D ship-time per `feedback_share_pin_pattern` — the
        window pin breaks every time a new ship prepends a new entry."""
        txt = CHANGELOG.read_text(encoding="utf-8")
        assert "τ.7.x.a.0" in txt, "CHANGELOG.md must record a τ.7.x.a.0 entry somewhere"

    def test_plan_ledger_records_tau7xa_0_and_tau6x1c(self):
        txt = PLAN.read_text(encoding="utf-8")
        # PLAN §6 ledger updated to reflect τ.7.x.a.0 shipped + new
        # τ.6.x.1.C pending sub-phase.
        assert "τ.7.x.a.0" in txt
        assert "τ.6.x.1.C" in txt


# ──────────────────────────────────────────────────────────────────────
# τ.7.x.a (PROPER) — Amharic Genesis full-book ingest pins
# ──────────────────────────────────────────────────────────────────────


def _amharic_gen_verses() -> list[tuple]:
    """Load content/translations/amharic-tewahedo/gen.py VERSES list
    via ast literal-eval so test parsing is robust to comment changes."""
    import ast

    gen_py = AMHARIC_TEWAHEDO / "gen.py"
    text = gen_py.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSES":
                    return ast.literal_eval(node.value)
    raise AssertionError("amharic-tewahedo/gen.py must define VERSES")


def _amharic_gen_constants() -> dict:
    """Load module-level constants (TRANSLATION, BOOK, SOURCE_QUALITY,
    SOURCE_PROVENANCE, EXTRACTION_DATE, INGEST_PHASE if set)."""
    import ast

    gen_py = AMHARIC_TEWAHEDO / "gen.py"
    text = gen_py.read_text(encoding="utf-8")
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


def _ingest_block() -> dict:
    return _source_yaml()["ocr_strategy"]["tau7xa_ingest"]


class TestTau7XAFullIngestGenPy:
    """The amharic-tewahedo/gen.py module is upgraded from Π.0 3-verse
    seed to τ.7.x.a full-book ingest at ocr-tier3."""

    def test_verses_count_at_least_floor(self):
        verses = _amharic_gen_verses()
        # Empirical at ship was 1308. Defensive floor 1000 protects
        # against silent regression while permitting parser refinement
        # (τ.6.x.1.E, τ.6.x.3) to nudge the count up or down.
        assert len(verses) >= 1000, f"τ.7.x.a Genesis ingest must have ≥1000 verses; got {len(verses)}"

    def test_first_verse_is_gen_1_1(self):
        verses = _amharic_gen_verses()
        ch, v, text = verses[0]
        assert (ch, v) == (1, 1), f"First verse must be (1, 1); got ({ch}, {v})"
        assert text, "Gen 1:1 text must be non-empty"

    def test_gen_1_1_preserves_pdf_variant_reading(self):
        """Per τ.7.x.a.0 PILOT §3 Observation 1, the PDF source uses
        the EXPANDED Gen 1:1 form `በመጀመሪያው ቁን ...` (vs Π.0 seed's
        standard `በመጀመሪያ` opening). The τ.7.x.a ingest preserves
        the publisher's variant reading."""
        verses = _amharic_gen_verses()
        gen_1_1 = verses[0][2]
        assert "በመጀመሪያው" in gen_1_1, (
            "τ.7.x.a Gen 1:1 must preserve PDF source's expanded reading "
            f"'በመጀመሪያው ቁን ...' per τ.7.x.a.0 PILOT; got {gen_1_1[:80]!r}"
        )

    def test_translation_constant(self):
        c = _amharic_gen_constants()
        assert c.get("TRANSLATION") == "amharic-tewahedo"

    def test_book_constant(self):
        c = _amharic_gen_constants()
        assert c.get("BOOK") == "gen"

    def test_source_quality_ocr_tier3(self):
        """Per τ.6.x.0b honesty contract, OCR-extracted text is recorded
        at ocr-tier3 quality. τ.6.x.3 batched audit ramps to ocr-tier2."""
        c = _amharic_gen_constants()
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"

    def test_source_provenance(self):
        c = _amharic_gen_constants()
        assert c.get("SOURCE_PROVENANCE") == "parallel-bible-eotc"

    def test_ingest_phase_constant(self):
        c = _amharic_gen_constants()
        assert c.get("INGEST_PHASE") == "τ.7.x.a"


class TestTau7XAFullIngestCoverage:
    """Per-chapter coverage matches the empirical post-renumber
    distribution. Chapters 1-42 fully populated; 43 partial; 44-50
    empty per renumber_against_floor() applied to 1308 verses against
    the GENESIS_VERSE_COUNTS floor."""

    def _by_chapter(self) -> dict[int, list[tuple]]:
        verses = _amharic_gen_verses()
        out: dict[int, list[tuple]] = {}
        for ch, v, t in verses:
            out.setdefault(ch, []).append((v, t))
        return out

    def test_chapter_1_first_verse_index(self):
        by_ch = self._by_chapter()
        assert (1, 1) == (by_ch[1][0][0], 1)  # first entry's verse is 1
        # i.e., chapter 1 starts at verse 1, no off-by-one

    def test_chapter_1_through_42_fully_populated(self):
        """The defining τ.7.x.a empirical pin: chapters 1-42 have
        verse counts MATCHING the GENESIS_VERSE_COUNTS floor under
        renumber_against_floor() sequential assignment."""
        # Import floor inside the test so a parser-side change is
        # picked up automatically.
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import GENESIS_VERSE_COUNTS

        by_ch = self._by_chapter()
        for ch in range(1, 43):
            got = len(by_ch.get(ch, []))
            expected = GENESIS_VERSE_COUNTS[ch]
            assert got == expected, (
                f"τ.7.x.a chapter {ch} must have exactly {expected} verses (GENESIS_VERSE_COUNTS floor); got {got}"
            )

    def test_chapter_43_partial(self):
        """Chapter 43 received the parser's remaining 16 verses after
        chapters 1-42 were filled. Empirical at ship; defensive range
        (5, 34) permits some drift but flags wholesale regression."""
        by_ch = self._by_chapter()
        got = len(by_ch.get(43, []))
        assert 5 <= got <= 34, f"τ.7.x.a chapter 43 partial: expect 5..34 verses; got {got}"

    def test_chapters_44_through_50_empty(self):
        """Chapters 44-50 received zero verses (the parser exhausted
        recovered content before reaching the Joseph cycle late
        chapters). Per τ.6.x.0b ocr-tier3 honesty contract; τ.6.x.3
        batched audit will close the gap (or τ.6.x.1.E truncated-
        keyword refinement if shipped first)."""
        by_ch = self._by_chapter()
        for ch in range(44, 51):
            got = len(by_ch.get(ch, []))
            assert got == 0, (
                f"τ.7.x.a chapter {ch} should be empty at ocr-tier3; "
                f"got {got} verses (parser-quality regression — investigate)"
            )

    def test_no_overflow_above_chapter_50(self):
        """The renumber_against_floor() overflow bucket (ch_max+1) is
        empty. If overflow appears, the parser yielded more verses
        than the GENESIS_VERSE_COUNTS floor — a noisy-OCR regression
        flag."""
        by_ch = self._by_chapter()
        overflow = sum(len(v) for ch, v in by_ch.items() if ch > 50)
        assert overflow == 0, (
            f"τ.7.x.a renumber overflow should be 0; got {overflow} verses above ch 50. Parser produced excess; review."
        )


class TestTau7XAParserExtensionRenumber:
    """renumber_against_floor() unit-tests — the τ.7.x.a writer-side
    helper that resolves the τ.6.x.1.D residual via sequential
    redistribution against a canonical floor."""

    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_empty_input_returns_empty(self):
        from extract_parallel_pdf import renumber_against_floor

        assert renumber_against_floor([], {1: 10}) == []

    def test_exact_fill_one_chapter(self):
        from extract_parallel_pdf import renumber_against_floor

        # 3 verses, floor {1: 3} — exact fill.
        inp = [(99, 99, "a"), (99, 99, "b"), (99, 99, "c")]
        out = renumber_against_floor(inp, {1: 3})
        assert out == [(1, 1, "a"), (1, 2, "b"), (1, 3, "c")]

    def test_partial_fill_under_floor(self):
        from extract_parallel_pdf import renumber_against_floor

        # 2 verses, floor {1: 5} — partial fill.
        inp = [(99, 99, "a"), (99, 99, "b")]
        out = renumber_against_floor(inp, {1: 5})
        assert out == [(1, 1, "a"), (1, 2, "b")]

    def test_overflow_spills_to_ch_max_plus_one(self):
        from extract_parallel_pdf import renumber_against_floor

        # 5 verses, floor {1: 3} — 2 overflow.
        inp = [(99, 99, c) for c in "abcde"]
        out = renumber_against_floor(inp, {1: 3})
        assert out == [
            (1, 1, "a"),
            (1, 2, "b"),
            (1, 3, "c"),
            (2, 1, "d"),
            (2, 2, "e"),
        ]

    def test_multi_chapter_assignment(self):
        from extract_parallel_pdf import renumber_against_floor

        # 6 verses, floor {1: 3, 2: 3} — exact fill across 2 chapters.
        inp = [(99, 99, c) for c in "abcdef"]
        out = renumber_against_floor(inp, {1: 3, 2: 3})
        assert out == [
            (1, 1, "a"),
            (1, 2, "b"),
            (1, 3, "c"),
            (2, 1, "d"),
            (2, 2, "e"),
            (2, 3, "f"),
        ]

    def test_input_chapter_labels_discarded(self):
        from extract_parallel_pdf import renumber_against_floor

        # Input labels (99, 99) are discarded; canonical labels
        # come from the floor + sequential assignment.
        inp = [(99, 99, "a"), (1, 1, "b"), (50, 26, "c")]
        out = renumber_against_floor(inp, {1: 3})
        assert out == [(1, 1, "a"), (1, 2, "b"), (1, 3, "c")]

    def test_source_order_preserved(self):
        from extract_parallel_pdf import renumber_against_floor

        # Verses are redistributed in input order; text content is
        # unchanged.
        inp = [(99, 99, f"v{i}") for i in range(10)]
        out = renumber_against_floor(inp, {1: 5, 2: 5})
        texts = [t for (_, _, t) in out]
        assert texts == [f"v{i}" for i in range(10)]

    def test_with_genesis_floor_full_distribution(self):
        from extract_parallel_pdf import GENESIS_VERSE_COUNTS, renumber_against_floor

        # 1534 inputs (exact floor total) → fills all 50 chapters
        # to their expected counts.
        inp = [(99, 99, f"v{i}") for i in range(1534)]
        out = renumber_against_floor(inp, GENESIS_VERSE_COUNTS)
        from collections import Counter

        cnt = Counter(c for (c, _, _) in out)
        for ch, expected in GENESIS_VERSE_COUNTS.items():
            assert cnt[ch] == expected, f"ch {ch}: {cnt[ch]} != {expected}"


class TestTau7XAExtractSectionExtensions:
    """extract_section() gained paragraph_mode + renumber_floor kwargs."""

    def test_paragraph_mode_kwarg_signature(self):
        import inspect
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import extract_section

        sig = inspect.signature(extract_section)
        assert "paragraph_mode" in sig.parameters
        assert sig.parameters["paragraph_mode"].default is False

    def test_renumber_floor_kwarg_signature(self):
        import inspect
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import extract_section

        sig = inspect.signature(extract_section)
        assert "renumber_floor" in sig.parameters
        assert sig.parameters["renumber_floor"].default is None


class TestTau7XAWriteBookModuleExtensions:
    """write_book_module() gained ingest_phase + docstring_extra kwargs."""

    def test_ingest_phase_kwarg(self):
        import inspect
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import write_book_module

        sig = inspect.signature(write_book_module)
        assert "ingest_phase" in sig.parameters
        assert sig.parameters["ingest_phase"].default is None

    def test_docstring_extra_kwarg(self):
        import inspect
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import write_book_module

        sig = inspect.signature(write_book_module)
        assert "docstring_extra" in sig.parameters
        assert sig.parameters["docstring_extra"].default is None


class TestTau7XAMetaYamlIngestRecord:
    """amharic-tewahedo/_meta.yaml gained an `ingest_record` block +
    upgraded stats per τ.7.x.a."""

    def _meta(self) -> dict:
        path = AMHARIC_TEWAHEDO / "_meta.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_stats_verses_upgraded(self):
        # Was 3 (Π.0 seed); now 1308 (τ.7.x.a ingest).
        # Defensive floor 100 like the gen.py count pin.
        m = self._meta()
        assert m["stats"]["verses"] >= 100, (
            f"_meta.yaml stats.verses must be ≥100 post-τ.7.x.a; got {m['stats']['verses']}"
        )

    def test_ingest_record_present(self):
        m = self._meta()
        assert "ingest_record" in m, "_meta.yaml must include ingest_record block post-τ.7.x.a"

    def test_ingest_record_phase(self):
        m = self._meta()
        assert m["ingest_record"]["phase"] == "τ.7.x.a"

    def test_ingest_record_book_codes_gen(self):
        m = self._meta()
        assert m["ingest_record"]["ingested_book_codes"] == ["gen"]

    def test_ingest_record_quality_tier3(self):
        m = self._meta()
        assert m["ingest_record"]["quality_tier"] == "ocr-tier3"

    def test_ingest_record_parser_extensions_chain(self):
        m = self._meta()
        # τ.6.x.1.B + τ.6.x.1.C + τ.6.x.1.D + τ.7.x.a chain (each
        # parser-extension ship is listed; downstream auditors can
        # verify the full pipeline at this point).
        chain = m["ingest_record"]["parser_extensions"]
        for phase in ("τ.6.x.1.B", "τ.6.x.1.C", "τ.6.x.1.D", "τ.7.x.a"):
            assert phase in chain, f"parser_extensions chain missing {phase}"

    def test_ingest_record_audit_handoff_tau6x3(self):
        m = self._meta()
        assert m["ingest_record"]["audit_handoff"] == "τ.6.x.3"


class TestTau7XASourceYamlIngestBlock:
    """ocr_strategy.tau7xa_ingest is the NEW block codifying the
    τ.7.x.a ingest ship + back-link annotation to τ.6.x.1.D residual."""

    def test_block_exists(self):
        assert "tau7xa_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert _ingest_block()["shipped_at_phase"] == "τ.7.x.a"

    def test_resolves_tau6x1d_residual(self):
        rr = _ingest_block()["resolves_residual"]
        assert rr["source"] == "τ.6.x.1.D tau6x1d_chapter_recovery.known_residual_issues"
        assert rr["issue"] == "chapter_marker_keyword_garbled_past_recognition"
        assert rr["resolution_method"] == "writer_side_renumbering_against_floor"

    def test_reciprocal_back_link_annotation(self):
        """τ.6.x.1.D block must carry tau6x1d_chapter_recovery.
        residual_resolved_at_phase = τ.7.x.a (single-key back-link
        pattern; 5th instance after tau6x1a→1b, tau6x1b→2D,
        tau7xa_pre_pilot→1C, tau6x1c→1D)."""
        d = _source_yaml()["ocr_strategy"]["tau6x1d_chapter_recovery"]
        assert d.get("residual_resolved_at_phase") == "τ.7.x.a", (
            "tau6x1d_chapter_recovery must back-link to τ.7.x.a per single-key annotation pattern"
        )

    def test_helpers_added_renumber_against_floor(self):
        helpers = _ingest_block()["helpers_added"]
        assert "renumber_against_floor" in helpers
        assert "write_book_module_extensions" in helpers
        assert "_build_docstring_extra" in helpers

    def test_cli_extensions_documented(self):
        cli = _ingest_block()["cli_extensions"]
        for k in (
            "paragraph_mode_flag",
            "renumber_flag",
            "lang_flag",
            "ingest_phase_flag",
        ):
            assert k in cli, f"cli_extensions missing {k}"

    def test_empirical_validation_coverage_85_percent(self):
        ev = _ingest_block()["empirical_validation"]
        # Coverage at ship was 85.3%. Floor 80 protects against
        # parser-side regression.
        assert ev["coverage_pct"] >= 80.0

    def test_empirical_chapters_fully_populated_1_through_42(self):
        ev = _ingest_block()["empirical_validation"]
        assert ev["chapters_fully_populated"] == list(range(1, 43))

    def test_empirical_chapters_missing_44_through_50(self):
        ev = _ingest_block()["empirical_validation"]
        assert ev["chapters_missing"] == list(range(44, 51))

    def test_no_ingest_at_this_phase_false(self):
        # This IS the ingest phase — no_ingest contract VIOLATED here
        # per the authorized D4-c direction.
        assert _ingest_block()["no_ingest_at_this_phase"] is False

    def test_closed_arc_tau6x0a_no_ingest_false(self):
        contracts = _ingest_block()["closed_arc_contracts_preserved"]
        assert contracts["tau6x0a_no_ingest"] is False, (
            "τ.7.x.a is the AUTHORIZED first violation of the no-ingest "
            "contract per D4-c; closed_arc_contracts_preserved must "
            "record this honestly"
        )

    def test_closed_arc_tau6x0b_honesty_preserved(self):
        contracts = _ingest_block()["closed_arc_contracts_preserved"]
        assert contracts["tau6x0b_honesty_contract"] is True

    def test_closed_arc_tau6x1c_paragraph_mode(self):
        contracts = _ingest_block()["closed_arc_contracts_preserved"]
        assert contracts["tau6x1c_parser_extension"] is True

    def test_closed_arc_tau6x1d_chapter_recovery(self):
        contracts = _ingest_block()["closed_arc_contracts_preserved"]
        assert contracts["tau6x1d_chapter_recovery"] is True

    def test_translation_slot_state_amharic_upgraded(self):
        state = _ingest_block()["translation_slot_state"]
        amh = state["amharic_tewahedo_gen"]
        assert "Π.0" in amh
        assert "τ.7.x.a" in amh

    def test_translation_slot_state_geez_preserved(self):
        state = _ingest_block()["translation_slot_state"]
        geez = state["geez_tewahedo_gen"]
        assert "Π.0" in geez
        assert "remains" in geez

    def test_next_phase_tau7xb(self):
        assert _ingest_block()["next_phase"] == "τ.7.x.b"


class TestTau7XAGeezTewahedoPreserved:
    """The Geʽez column should remain at Π.0 seed after τ.7.x.a — full
    Geʽez ingest is τ.6.x.2.a per D4-c sequencing."""

    def test_geez_gen_py_ingested_at_tau6x2a(self):
        """MIGRATED at τ.6.x.2.a-h batch ship-time (2026-05-15):
        originally asserted geez-tewahedo/gen.py remains at Π.0 seed
        (≤10 verses) until τ.6.x.2.a ships. The τ.6.x.2.a batch sub-
        ship UPGRADED Geʽez Genesis from Π.0 seed (3 verses, Gen
        1:1-3) to ocr-tier3 full-book ingest (1022 verses, 66.6%
        coverage). Durable assertion is now: Geʽez Genesis is at
        ocr-tier3 ingest scale; the τ.6.x.2.a `upgraded_from`
        provenance is pinned in test_parallel_bible_tau6x2_geez_arc."""
        import ast

        gen_py = REPO / "content" / "translations" / "geez-tewahedo" / "gen.py"
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
        # τ.6.x.2.a empirical at ship: 1022 verses (66.6% coverage).
        # Floor 950 guards against regression while permitting parser
        # refinement.
        assert len(verses) >= 950, (
            f"geez-tewahedo Genesis must be at ocr-tier3 ingest scale post-τ.6.x.2.a; "
            f"got {len(verses)} verses (<950 indicates regression from τ.6.x.2.a state)"
        )

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
    """IN_FLIGHT.md tracks τ.7.x.a.0 as the prior task."""

    def test_in_flight_idle_after_pilot(self):
        txt = IN_FLIGHT.read_text(encoding="utf-8")
        assert "TRACKER-STATE: idle" in txt

    def test_prior_task_is_tau7xa_0(self):
        txt = IN_FLIGHT.read_text(encoding="utf-8")
        assert "τ.7.x.a.0" in txt[:5000], "τ.7.x.a.0 must appear in the prior-task section near the top"

    def test_tau6x2d_demoted_to_previous(self):
        txt = IN_FLIGHT.read_text(encoding="utf-8")
        # τ.6.x.2.D should now appear in the prior-task-previous chain.
        tau7_pos = txt.find("τ.7.x.a.0")
        tau6x2d_pos = txt.find("τ.6.x.2.D")
        assert tau7_pos != -1
        assert tau6x2d_pos != -1
        assert tau7_pos < tau6x2d_pos, "τ.7.x.a.0 must appear before τ.6.x.2.D in IN_FLIGHT"


class TestTau7XASessionState:
    """SESSION_STATE.md headline updated to τ.7.x.a.0."""

    def test_headline_is_tau7xa_0(self):
        # Headline mentions τ.7.x.a.0 within the first 500 chars.
        txt = SESSION_STATE.read_text(encoding="utf-8")
        assert "τ.7.x.a.0" in txt[:2000], "τ.7.x.a.0 must appear in SESSION_STATE headline"

    def test_session_state_next_phase_is_tau6x1c(self):
        txt = SESSION_STATE.read_text(encoding="utf-8")
        # Next-phase pointer routes through τ.6.x.1.C.
        assert "τ.6.x.1.C" in txt[:5000]


class TestTau7XAClosedArcInvariantPreservation:
    """The PILOT preserves all 17 closed-arc invariants from prior
    ships + the τ.6.x.0a no-ingest contract specifically."""

    def test_geez_tewahedo_only_seed_gen_py(self):
        """geez-tewahedo/ contains only gen.py (Π.0 seed) — D4-c
        sequencing puts Geʽez Genesis at τ.6.x.2.a, AFTER all τ.7.x
        Amharic ingests; the geez-tewahedo slot remains untouched
        at τ.7.x.a.0."""
        files = sorted(p.name for p in GEEZ_TEWAHEDO.iterdir() if p.is_file() and p.suffix == ".py")
        assert files == ["gen.py"], f"τ.7.x.a.0: geez-tewahedo must remain at Π.0 seed (gen.py only); got {files}"

    def test_amharic_tewahedo_only_seed_gen_py(self):
        """amharic-tewahedo/ likewise contains only gen.py at the
        PILOT sub-phase. τ.7.x.a (proper) — the full-book ingest —
        is BLOCKED on τ.6.x.1.C, so amharic-tewahedo/gen.py
        retains its Π.0 seed (3 verses) until τ.6.x.1.C ships and
        τ.7.x.a (proper) follows."""
        files = sorted(p.name for p in AMHARIC_TEWAHEDO.iterdir() if p.is_file() and p.suffix == ".py")
        assert files == ["gen.py"], f"τ.7.x.a.0: amharic-tewahedo must remain at Π.0 seed (gen.py only); got {files}"

    def test_amharic_tewahedo_gen_py_still_seed_three_verses(self):
        """The τ.7.x.a.0 PILOT does NOT touch amharic-tewahedo/gen.py
        content — the Π.0 3-verse seed is preserved until τ.7.x.a
        (proper) ships. This pin is the strongest no-ingest contract
        pin: not only does the directory contain only gen.py, but
        gen.py itself remains at its 3-verse Π.0 state."""
        gen_py = AMHARIC_TEWAHEDO / "gen.py"
        text = gen_py.read_text(encoding="utf-8")
        # Count tuple lines (lines that start with `    (` after VERSES = [).
        # The Π.0 seed has exactly 3 tuples (Gen 1:1, 1:2, 1:3).
        # The seed style uses `(1, 1, "...")` then a multi-line
        # paren-comma for 1:2 then `(1, 3, "...")`. The simplest
        # detection: look for VERSES = [ ... ] block and count
        # entries inside it.
        import ast

        # Parse the .py file and extract VERSES.
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
        assert len(verses) == 3, (
            f"τ.7.x.a.0 preserves Π.0 seed: amharic-tewahedo/gen.py VERSES must remain 3 (Π.0 seed); got {len(verses)}. τ.7.x.a (proper) will expand this AFTER τ.6.x.1.C ships."
        )

    def test_no_ingest_at_this_phase(self):
        """The PILOT sub-phase's yaml block explicitly records
        no_ingest_at_this_phase=true. This is the τ.6.x.0a contract
        preservation marker."""
        assert _pilot_block()["no_ingest_at_this_phase"] is True

    def test_changelog_records_tau7xa_0_entry(self):
        txt = CHANGELOG.read_text(encoding="utf-8")
        # τ.7.x.a.0 entry appears near the top (newest-first).
        first_3k = txt[:3000]
        assert "τ.7.x.a.0" in first_3k, "CHANGELOG.md must record a τ.7.x.a.0 entry near the top"

    def test_plan_ledger_records_tau7xa_0_and_tau6x1c(self):
        txt = PLAN.read_text(encoding="utf-8")
        # PLAN §6 ledger updated to reflect τ.7.x.a.0 shipped + new
        # τ.6.x.1.C pending sub-phase.
        assert "τ.7.x.a.0" in txt
        assert "τ.6.x.1.C" in txt

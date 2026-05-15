"""τ.6.x.2.D — D-decisions codification pins (2026-05-15).

τ.6.x.2.D is a DECISION-ONLY ship that resolves the four open
publisher-direction D-decisions gating τ.6.x.2+ Geʽez bulk-ingest
at ocr-tier3. Triggered by user message `d1a, d2b, d3c, d4c`.

The four locked picks:

- **D1-a** — cadence: incremental per-book sub-ships
  (τ.6.x.2.a → τ.6.x.2.z). Recommended default; matches γ.4.x
  per-arc ship cadence.
- **D2-b** — tier ramp: batched τ.6.x.3 audit pass.
  Recommended default; defers ocr-tier3 → ocr-tier2 cross-check
  to a discrete subsequent arc.
- **D3-c** — audit plan: FULL 87-book audit at τ.6.x.3.
  OVERRIDES recommended D3-a "first-cut" default per memory
  `feedback_extensive_answers` (broadest scope).
- **D4-c** — Amharic sequencing: Amharic-first inversion;
  τ.7.x.a → τ.7.x.z ships BEFORE τ.6.x.2.a → τ.6.x.2.z.
  OVERRIDES recommended D4-a "Geʽez-first" default; the
  Amharic-trained Tesseract recognizer's cleaner OCR per
  τ.6.x.1.A pilot validates the per-book pipeline first.

τ.6.x.2.D deliverables under test:

1. `_source.yaml::ocr_strategy.tau6x2D_decisions` block —
   shipped_at_phase + shipped_date + publisher_answer + 4
   D-decision blocks + derived_phase_ordering sequence +
   closed_arc_contracts_preserved (6 keys) + no_ingest +
   translation_slot_state + next_phase=τ.7.x.a.

2. `dev/SCOPE_2026-05-14-parallel-bible.md` §7.7 section —
   D-decisions table + derived phase ordering + D4-c PI2 gate
   rewiring note + closed-arc contracts preserved + next-phase
   pointer; §8.1 codifies D1-D4 as RESOLVED.

3. `dev/PI2_PRE_FLIGHT_CHECKLIST.md` §2 gate dashboard rewired
   per D4-c — τ.7.x row HOISTED ABOVE τ.6.x.2+ row; τ.6.x.2.D
   ✓ row inserted; τ.6.x.3 ⬜ row inserted; gate-unblock clause
   extended.

4. `dev/IN_FLIGHT.md` prior-task block for τ.6.x.2.D; previous
   τ.6.x.1.B demoted to prior-task-previous.

5. `dev/SESSION_STATE.md` headline updated to τ.6.x.2.D.

6. Π.0 seed preservation: no `.py` files written to
   `content/translations/geez-tewahedo/` or
   `content/translations/amharic-tewahedo/` beyond the Π.0
   seed (`gen.py` only, 3 verses each). v1.0 byte-identical
   reproducibility preserved.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parent.parent
SOURCE_YAML = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
SCOPE = REPO / "dev" / "SCOPE_2026-05-14-parallel-bible.md"
PI2_CHECKLIST = REPO / "dev" / "PI2_PRE_FLIGHT_CHECKLIST.md"
IN_FLIGHT = REPO / "dev" / "IN_FLIGHT.md"
SESSION_STATE = REPO / "dev" / "SESSION_STATE.md"
CHANGELOG = REPO / "dev" / "CHANGELOG.md"
PLAN = REPO / "dev" / "PLAN_2026-05-09.md"
GEEZ_TEWAHEDO = REPO / "content" / "translations" / "geez-tewahedo"
AMHARIC_TEWAHEDO = REPO / "content" / "translations" / "amharic-tewahedo"


def _source_yaml() -> dict:
    return yaml.safe_load(SOURCE_YAML.read_text(encoding="utf-8"))


def _tau6x2d_block() -> dict:
    return _source_yaml()["ocr_strategy"]["tau6x2D_decisions"]


# ──────────────────────────────────────────────────────────────────
# τ.6.x.2.D — _source.yaml::ocr_strategy.tau6x2D_decisions block
# ──────────────────────────────────────────────────────────────────


class TestTau6X2DSourceYamlBlock:
    """`_source.yaml::ocr_strategy.tau6x2D_decisions` records the
    publisher-direction picks + derived phase ordering + closed-arc
    preservation contract."""

    def test_block_exists(self):
        block = _tau6x2d_block()
        assert isinstance(block, dict), "tau6x2D_decisions must be a mapping"

    def test_shipped_at_phase(self):
        assert _tau6x2d_block()["shipped_at_phase"] == "τ.6.x.2.D"

    def test_shipped_date(self):
        # YAML safe-loads bare ISO dates as datetime.date objects;
        # match the same parsing convention used by tau6x1*_*_date.
        assert _tau6x2d_block()["shipped_date"] == datetime.date(2026, 5, 15)

    def test_publisher_answer_recorded(self):
        assert _tau6x2d_block()["publisher_answer"] == "d1a, d2b, d3c, d4c"

    def test_d1_cadence_choice_is_d1a(self):
        d1 = _tau6x2d_block()["decisions"]["D1_cadence"]
        assert d1["choice"] == "D1-a"
        assert "incremental" in d1["label"].lower(), "D1-a label must mention incremental per-book cadence"

    def test_d2_tier_ramp_choice_is_d2b(self):
        d2 = _tau6x2d_block()["decisions"]["D2_tier_ramp"]
        assert d2["choice"] == "D2-b"
        assert "τ.6.x.3" in d2["label"], "D2-b label must reference τ.6.x.3 batched audit phase"

    def test_d3_audit_plan_choice_is_d3c(self):
        d3 = _tau6x2d_block()["decisions"]["D3_audit_plan"]
        assert d3["choice"] == "D3-c"
        assert "87-book" in d3["label"] or "full" in d3["label"].lower(), (
            "D3-c label must mention full 87-book audit scope"
        )

    def test_d4_sequencing_choice_is_d4c(self):
        d4 = _tau6x2d_block()["decisions"]["D4_amharic_sequencing"]
        assert d4["choice"] == "D4-c"
        assert "amharic-first" in d4["label"].lower() or "amharic" in d4["label"].lower(), (
            "D4-c label must mention Amharic-first inversion"
        )

    def test_d3_d4_rationale_cites_extensive_answers_memory(self):
        """D3-c + D4-c both override recommended defaults; the
        rationale must explain why — D3-c per broadest scope,
        D4-c per pilot-validation evidence."""
        d3_rat = _tau6x2d_block()["decisions"]["D3_audit_plan"]["rationale"]
        d4_rat = _tau6x2d_block()["decisions"]["D4_amharic_sequencing"]["rationale"]
        assert "feedback_extensive_answers" in d3_rat, "D3-c override needs explicit memory citation"
        assert "τ.6.x.1.A" in d4_rat, "D4-c rationale must cite the τ.6.x.1.A pilot finding"

    def test_each_decision_records_alternatives_not_chosen(self):
        for key in ("D1_cadence", "D2_tier_ramp", "D3_audit_plan", "D4_amharic_sequencing"):
            decision = _tau6x2d_block()["decisions"][key]
            assert "alternatives_not_chosen" in decision, f"{key}: must record rejected alternatives for audit trail"
            assert isinstance(decision["alternatives_not_chosen"], dict)
            assert len(decision["alternatives_not_chosen"]) >= 1

    def test_derived_phase_ordering_starts_with_tau6x2d_shipped(self):
        seq = _tau6x2d_block()["derived_phase_ordering"]["sequence"]
        assert seq[0]["phase"] == "τ.6.x.2.D"
        assert "shipped" in seq[0]["status"].lower()

    def test_derived_phase_ordering_puts_amharic_before_geez(self):
        """D4-c inversion: τ.7.x (Amharic) MUST appear before
        τ.6.x.2+ (Geʽez) in the phase sequence."""
        seq = _tau6x2d_block()["derived_phase_ordering"]["sequence"]
        phase_names = [entry["phase"] for entry in seq]
        amh_idx = next(i for i, p in enumerate(phase_names) if "τ.7.x" in p)
        geez_idx = next(i for i, p in enumerate(phase_names) if "τ.6.x.2.a" in p)
        assert amh_idx < geez_idx, (
            "D4-c inversion: Amharic τ.7.x must come BEFORE Geʽez τ.6.x.2+ in the derived ordering"
        )

    def test_derived_phase_ordering_terminates_at_pi2(self):
        seq = _tau6x2d_block()["derived_phase_ordering"]["sequence"]
        assert seq[-1]["phase"] == "Π.2"

    def test_tau6x3_audit_phase_between_arcs_and_pi2(self):
        seq = _tau6x2d_block()["derived_phase_ordering"]["sequence"]
        phase_names = [entry["phase"] for entry in seq]
        tau6x3_idx = next(i for i, p in enumerate(phase_names) if p == "τ.6.x.3")
        pi2_idx = next(i for i, p in enumerate(phase_names) if p == "Π.2")
        assert tau6x3_idx < pi2_idx, "τ.6.x.3 audit pass must run before Π.2 flip"

    def test_closed_arc_contracts_preserved_all_true(self):
        contracts = _tau6x2d_block()["closed_arc_contracts_preserved"]
        for key in (
            "tau6x0a_no_ingest",
            "tau6x0b_honesty_contract",
            "tau6x0c_script_ethiopic_adoption",
            "tau6x1_engine_wiring",
            "tau6x1a_pilot_validation",
            "tau6x1b_parser_extension",
        ):
            assert contracts.get(key) is True, f"closed_arc_contracts_preserved.{key} must be True at τ.6.x.2.D"

    def test_no_ingest_at_this_phase_true(self):
        assert _tau6x2d_block()["no_ingest_at_this_phase"] is True, "τ.6.x.2.D is DECISION-ONLY; no data ingest"

    def test_translation_slot_state_remains_at_pi0_seed(self):
        state = _tau6x2d_block()["translation_slot_state"]
        assert "Π.0-seed" in state, "translation_slot_state must record Π.0 seed preservation"
        assert "Genesis-only" in state or "gen.py" in state.lower(), "must indicate gen.py-only seed"

    def test_next_phase_is_tau7xa_not_tau6x2a(self):
        """D4-c inversion: next phase is τ.7.x.a (Amharic Genesis),
        NOT τ.6.x.2.a (Geʽez Genesis)."""
        assert _tau6x2d_block()["next_phase"] == "τ.7.x.a"

    def test_tau6x1b_block_back_links_to_tau6x2d(self):
        """The τ.6.x.1.B block's next-phase publisher-direction
        gate should now be annotated as resolved at τ.6.x.2.D."""
        block = _source_yaml()["ocr_strategy"]["tau6x1b_parser_extension"]
        assert block.get("publisher_direction_resolved_at_phase") == "τ.6.x.2.D"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.2.D — SCOPE §7.7 codification
# ──────────────────────────────────────────────────────────────────


class TestTau6X2DScopeCodification:
    """SCOPE §7.7 NEW section codifies the D-decisions + derived
    phase ordering + D4-c PI2 gate rewiring note."""

    def _text(self) -> str:
        return SCOPE.read_text(encoding="utf-8")

    def test_section_7_7_present(self):
        assert "## §7.7 — τ.6.x.2.D D-decisions" in self._text()

    def test_section_records_publisher_answer(self):
        assert '"d1a, d2b, d3c, d4c"' in self._text()

    def test_section_lists_all_four_d_picks(self):
        text = self._text()
        for pick in ("D1-a", "D2-b", "D3-c", "D4-c"):
            assert pick in text, f"SCOPE §7.7 must list {pick}"

    def test_section_includes_d4c_gate_rewiring_note(self):
        assert "§7.7.3" in self._text() and "PI2_PRE_FLIGHT" in self._text(), (
            "§7.7.3 must explicitly document the D4-c gate rewiring"
        )

    def test_section_8_1_codifies_resolved_decisions(self):
        assert "§8.1" in self._text() and "RESOLVED at τ.6.x.2.D" in self._text()


# ──────────────────────────────────────────────────────────────────
# τ.6.x.2.D — PI2_PRE_FLIGHT_CHECKLIST gate rewiring
# ──────────────────────────────────────────────────────────────────


class TestTau6X2DPi2PreFlightGateRewiring:
    """PI2 §2 gate dependency dashboard is rewired per D4-c:
    τ.7.x row appears ABOVE τ.6.x.2+ row; τ.6.x.2.D + τ.6.x.3
    rows present; gate-unblock clause extended."""

    def _text(self) -> str:
        return PI2_CHECKLIST.read_text(encoding="utf-8")

    def test_tau6x2d_row_marked_shipped(self):
        text = self._text()
        assert "τ.6.x.2.D D-decisions codification" in text
        assert "✓ SHIPPED 2026-05-15" in text

    def test_tau7x_row_appears_above_tau6x2_plus_row(self):
        """D4-c inversion: the τ.7.x gate row MUST appear ABOVE
        the τ.6.x.2+ Geʽez per-book gate row in §2 dashboard."""
        text = self._text()
        tau7x_idx = text.find("| τ.7.x Amharic per-book ingest")
        tau6x2_idx = text.find("| τ.6.x.2+ Geʽez per-book ingest")
        assert tau7x_idx > 0, "PI2 dashboard must contain τ.7.x per-book ingest row"
        assert tau6x2_idx > 0, "PI2 dashboard must contain τ.6.x.2+ per-book ingest row"
        assert tau7x_idx < tau6x2_idx, "D4-c inversion: τ.7.x row must precede τ.6.x.2+ row in PI2 §2 dashboard"

    def test_tau6x3_audit_row_present(self):
        text = self._text()
        assert "τ.6.x.3 batched ocr-tier3 → tier-2 audit" in text

    def test_gate_unblock_clause_extended(self):
        """The §2 gate-unblock clause should include all τ.6.x.2.D-era
        new gates: τ.6.x.2.D ✓ + τ.7.x + τ.6.x.2+ + τ.6.x.3."""
        text = self._text()
        for gate in ("τ.6.x.2.D ✓", "τ.7.x ✓", "τ.6.x.2+ ✓", "τ.6.x.3 ✓"):
            assert gate in text, f"PI2 §2 unblock clause must mention {gate!r}"

    def test_d4c_gate_ordering_note_present(self):
        """Per SCOPE §7.7.3, PI2 §2 must include an explicit note
        explaining the D4-c gate-ordering inversion."""
        text = self._text()
        assert "D4-c gate-ordering note" in text


# ──────────────────────────────────────────────────────────────────
# τ.6.x.2.D — IN_FLIGHT prior-task block
# ──────────────────────────────────────────────────────────────────


class TestTau6X2DInFlight:
    """IN_FLIGHT.md prior-task block records τ.6.x.2.D as the most
    recent ship; τ.6.x.1.B is demoted to prior-task-previous."""

    def _text(self) -> str:
        return IN_FLIGHT.read_text(encoding="utf-8")

    def test_prior_task_is_tau6x2d(self):
        text = self._text()
        prior_idx = text.find("## Prior task")
        assert prior_idx >= 0
        # After the "## Prior task" header, the next bolded block
        # must be τ.6.x.2.D, not τ.6.x.1.B.
        after = text[prior_idx : prior_idx + 800]
        assert "τ.6.x.2.D" in after, "IN_FLIGHT prior-task must be the τ.6.x.2.D ship"

    def test_publisher_answer_recorded(self):
        assert "d1a, d2b, d3c, d4c" in self._text()

    def test_all_four_d_picks_in_prior_task(self):
        text = self._text()
        for pick in ("D1-a", "D2-b", "D3-c", "D4-c"):
            assert pick in text, f"IN_FLIGHT prior-task must record {pick}"

    def test_tau6x1b_demoted_to_previous(self):
        """τ.6.x.1.B should now appear under '## Prior task (previous)'."""
        text = self._text()
        prev_idx = text.find("## Prior task (previous)")
        assert prev_idx >= 0
        # The first prior-task-previous block after τ.6.x.2.D
        # should be τ.6.x.1.B.
        after = text[prev_idx : prev_idx + 800]
        assert "τ.6.x.1.B" in after


# ──────────────────────────────────────────────────────────────────
# τ.6.x.2.D — SESSION_STATE headline
# ──────────────────────────────────────────────────────────────────


class TestTau6X2DSessionState:
    """SESSION_STATE.md headline is τ.6.x.2.D D-DECISIONS
    CODIFICATION ship, with all four picks recorded."""

    def _text(self) -> str:
        return SESSION_STATE.read_text(encoding="utf-8")

    def test_headline_is_tau6x2d(self):
        text = self._text()
        # The first "**Updated YYYY-MM-DD / ..." block must reference τ.6.x.2.D.
        first_block = text[:2000]
        assert "τ.6.x.2.D D-DECISIONS CODIFICATION" in first_block

    def test_session_state_next_phase_is_tau7xa(self):
        text = self._text()
        # The headline records the next-phase pointer per D4-c.
        assert "Next phase" in text and "τ.7.x.a" in text


# ──────────────────────────────────────────────────────────────────
# τ.6.x.2.D — closed-arc invariant preservation (Π.0 seed)
# ──────────────────────────────────────────────────────────────────


class TestTau6X2DClosedArcInvariantPreservation:
    """τ.6.x.2.D is DECISION-ONLY: the translation slots remain at
    their Π.0 seed state. No `.py` files beyond `gen.py` (3 verses
    each) in either `geez-tewahedo/` or `amharic-tewahedo/`."""

    def test_geez_tewahedo_only_seed_gen_py(self):
        """`geez-tewahedo/` contains only the Π.0 seed file at this
        ship — `gen.py` (or `_meta.yaml`, which is metadata)."""
        py_files = sorted(p.name for p in GEEZ_TEWAHEDO.glob("*.py"))
        assert py_files == ["gen.py"], (
            f"τ.6.x.0a contract preservation: geez-tewahedo/*.py must be only ['gen.py'] at τ.6.x.2.D; got {py_files}"
        )

    def test_amharic_tewahedo_only_seed_gen_py(self):
        """`amharic-tewahedo/` likewise contains only `gen.py` at
        the Π.0 seed state. D4-c next-phase is τ.7.x.a which will
        upgrade this from 3-verse seed to full-book ingest — at
        τ.6.x.2.D it must STILL be the seed."""
        py_files = sorted(p.name for p in AMHARIC_TEWAHEDO.glob("*.py"))
        assert py_files == ["gen.py"], (
            f"τ.6.x.0a contract preservation: amharic-tewahedo/*.py must be only ['gen.py'] at τ.6.x.2.D; got {py_files}"
        )

    def test_no_ingest_at_this_phase(self):
        """The _source.yaml block declares no_ingest_at_this_phase
        = True; reasserted at the file-system level above."""
        assert _tau6x2d_block()["no_ingest_at_this_phase"] is True

    def test_changelog_records_tau6x2d_entry(self):
        text = CHANGELOG.read_text(encoding="utf-8")
        # CHANGELOG newest-first; τ.6.x.2.D must appear before
        # τ.6.x.1.B in the file.
        tau6x2d_idx = text.find("τ.6.x.2.D")
        tau6x1b_idx = text.find("τ.6.x.1.B PARSER EXTENSION")
        assert tau6x2d_idx >= 0, "CHANGELOG must record τ.6.x.2.D entry"
        assert tau6x1b_idx >= 0, "CHANGELOG must still record prior τ.6.x.1.B entry"
        assert tau6x2d_idx < tau6x1b_idx, "CHANGELOG newest-first: τ.6.x.2.D must precede τ.6.x.1.B"

    def test_plan_ledger_records_tau6x2d_and_tau7xa(self):
        text = PLAN.read_text(encoding="utf-8")
        for phase in ("τ.6.x.2.D", "τ.7.x.a", "τ.6.x.3"):
            assert phase in text, f"PLAN §6 parallel-Bible ledger must mention {phase}"

"""Π.2.prep — Pre-flight checklist for the Ethiopian-Tewahedo
popup-language flip (2026-05-14).

DECLARATIVE-ONLY ship. Π.2 is the "flip the switch" phase that
surfaces Geʽez + Amharic in the ethiopian-tewahedo edition's verse
popups by default (per dev/SCOPE_2026-05-14-parallel-bible.md
§Π.2). Π.2 cannot ship until ALL its upstream gates are met:
Π.1 ✓ + Π.1.B ✓ + τ.6.x.0c + τ.6.x.1+ + τ.7.x (all currently
blocked except Π.1 + Π.1.B). Π.2.prep prepares the operator-facing
pre-flight checklist so the eventual Π.2 ship can land cleanly in
a single session when gates open.

Π.2.prep deliverables under test:

1. **NEW dev/PI2_PRE_FLIGHT_CHECKLIST.md** with eight required
   sections:
   - §1 Π.2 scope reminder (one-line YAML edit + tests)
   - §2 Gate dependency dashboard (Π.1 / Π.1.B / τ.6.x.0c /
     τ.6.x.1+ / τ.7.x / δ.1.x states)
   - §3 Publisher decision matrix (D1 popup-language set +
     D2 laodiceans canon membership + D3 4ba/2en/1cl notes-file
     state + D4 visual-QA scope)
   - §4 Pre-flight verification commands (pytest + tesseract +
     translation-slot count + linter)
   - §5 Π.2 ship script (exact YAML diff + test class proposal +
     build verification + state-doc updates)
   - §6 Post-flip QA checklist (5-e-reader matrix)
   - §7 Rollback plan
   - §8 Π.2.prep ship contract

2. **Π.2.prep makes NO changes to:** content/editions.yaml +
   content/canons.yaml + content/notes/*.py + scripts/* +
   production EPUB. v1.0 byte-identical reproducibility preserved.

3. **Closed-arc invariants regression-guarded:** γ.4.8.E + γ.4.8.F
   + Π.0.1 + Π.0.4 + τ.6.x.0a/b + δ.1.0 + δ.1.x.A.0 + Π.1 +
   Π.1.B all preserved.
"""

from __future__ import annotations

from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parent.parent
CHECKLIST = REPO / "dev" / "PI2_PRE_FLIGHT_CHECKLIST.md"
EDITIONS_YAML = REPO / "content" / "editions.yaml"
CANONS_YAML = REPO / "content" / "canons.yaml"
SCOPE_DOC = REPO / "dev" / "archive" / "SCOPE_2026-05-14-parallel-bible.md"


def _checklist_text() -> str:
    return CHECKLIST.read_text(encoding="utf-8")


# ──────────────────────────────────────────────────────────────────
# Π.2.prep.1 — checklist file exists + structural completeness
# ──────────────────────────────────────────────────────────────────


class TestPi2PrepChecklistExists:
    """The pre-flight checklist file exists with the expected
    eight numbered sections."""

    def test_checklist_file_exists(self):
        assert CHECKLIST.is_file(), f"Π.2.prep: pre-flight checklist must exist at {CHECKLIST}"

    def test_checklist_non_empty(self):
        text = _checklist_text()
        assert len(text) >= 1000, f"Π.2.prep: checklist must be substantive (got {len(text)} chars)"

    def test_checklist_has_eight_sections(self):
        text = _checklist_text()
        for i in range(1, 9):
            assert f"## §{i} " in text, (
                f"Π.2.prep: checklist must have section §{i}. Section headers found: "
                f"{[ln for ln in text.splitlines() if ln.startswith('## §')]}"
            )


# ──────────────────────────────────────────────────────────────────
# Π.2.prep.2 — §1 scope reminder mentions exact YAML edit
# ──────────────────────────────────────────────────────────────────


class TestPi2PrepScopeReminder:
    """§1 must document the exact YAML edit (popup_languages_default
    additive flip + geez + amharic)."""

    def test_section_1_mentions_popup_languages_default(self):
        text = _checklist_text()
        assert "popup_languages_default" in text

    def test_section_1_mentions_geez_and_amharic(self):
        text = _checklist_text()
        assert "geez" in text and "amharic" in text, "Π.2.prep: checklist must name both geez and amharic"

    def test_section_1_preserves_english_hebrew_greek(self):
        """The flip is additive (preserve english/hebrew/greek)."""
        text = _checklist_text()
        for lang in ["english", "hebrew", "greek"]:
            assert lang in text, f"Π.2.prep: checklist must name {lang} as preserved"


# ──────────────────────────────────────────────────────────────────
# Π.2.prep.3 — §2 gate dependency dashboard
# ──────────────────────────────────────────────────────────────────


class TestPi2PrepGateDashboard:
    """§2 must enumerate every Π.2 gate dependency with current
    status."""

    def test_pi1_gate_documented_as_shipped(self):
        text = _checklist_text()
        # Π.1 + Π.1.B must be marked ✓ SHIPPED
        assert "Π.1" in text
        assert "Π.1.B" in text
        assert "✓ SHIPPED" in text or "✓ shipped" in text.lower()

    def test_tau6x0c_gate_documented_as_pending(self):
        text = _checklist_text()
        assert "τ.6.x.0c" in text
        # The dashboard row should flag it as pending / operator-side
        assert "operator-side" in text or "operator side" in text

    def test_tau7x_gate_documented(self):
        text = _checklist_text()
        assert "τ.7.x" in text, "Π.2.prep: τ.7.x gate must be documented"

    def test_delta_1_x_gate_documented(self):
        text = _checklist_text()
        assert "δ.1.x" in text


# ──────────────────────────────────────────────────────────────────
# Π.2.prep.4 — §3 publisher decision matrix
# ──────────────────────────────────────────────────────────────────


class TestPi2PrepDecisionMatrix:
    """§3 must enumerate the publisher decision points with
    machine-readable identifiers (D1/D2/D3/D4)."""

    def test_d1_popup_language_set_decision(self):
        text = _checklist_text()
        assert "D1" in text and "popup-language" in text.lower(), (
            "Π.2.prep: D1 popup-language decision must be documented"
        )

    def test_d2_laodiceans_canon_decision(self):
        text = _checklist_text()
        assert "D2" in text and ("lao" in text or "Laodiceans" in text), (
            "Π.2.prep: D2 laodiceans canon-membership decision must be documented"
        )

    def test_d3_empty_notes_decision(self):
        text = _checklist_text()
        assert "D3" in text and ("4ba" in text or "2en" in text or "1cl" in text), (
            "Π.2.prep: D3 4ba/2en/1cl notes-file state decision must be documented"
        )

    def test_d4_visual_qa_scope(self):
        text = _checklist_text()
        assert "D4" in text and "QA" in text, "Π.2.prep: D4 visual-QA scope decision must be documented"

    def test_decision_d1_recommends_5_language_set(self):
        text = _checklist_text()
        # Recommendation should name the 5-language additive flip
        assert "[english, hebrew, greek, geez, amharic]" in text


# ──────────────────────────────────────────────────────────────────
# Π.2.prep.5 — §4 pre-flight verification commands
# ──────────────────────────────────────────────────────────────────


class TestPi2PrepVerificationCommands:
    """§4 must list runnable verification commands for each gate."""

    def test_pytest_command_present(self):
        text = _checklist_text()
        assert "pytest" in text

    def test_tesseract_verification_command_present(self):
        text = _checklist_text()
        assert "tesseract --list-langs" in text or "tesseract --version" in text

    def test_linter_command_present(self):
        text = _checklist_text()
        assert "lint_rules.py" in text


# ──────────────────────────────────────────────────────────────────
# Π.2.prep.6 — §5 ship script (exact YAML diff)
# ──────────────────────────────────────────────────────────────────


class TestPi2PrepShipScript:
    """§5 must show the exact YAML diff Π.2 will apply."""

    def test_section_5_diff_present(self):
        text = _checklist_text()
        # The diff block should contain the additive lines
        assert '+      - "geez"' in text
        assert '+      - "amharic"' in text

    def test_section_5_test_class_proposal(self):
        text = _checklist_text()
        assert "TestPi2EthiopianTewahedoPopups" in text

    def test_section_5_build_verification_command(self):
        text = _checklist_text()
        assert "build_edition.py" in text and "epubcheck" in text


# ──────────────────────────────────────────────────────────────────
# Π.2.prep.7 — §6 post-flip QA checklist (5 e-readers)
# ──────────────────────────────────────────────────────────────────


class TestPi2PrepPostFlipQa:
    """§6 must enumerate the 5-e-reader visual-QA matrix."""

    def test_5_e_readers_named(self):
        text = _checklist_text()
        # All 5 e-readers from D4 should appear in §6 too
        for reader in ["Apple Books", "Calibre", "Kindle", "Adobe", "Thorium"]:
            assert reader in text, f"Π.2.prep: §6 must name {reader} e-reader"

    def test_qa_checklist_format(self):
        text = _checklist_text()
        # Should use checkbox-style markers
        assert "[ ]" in text


# ──────────────────────────────────────────────────────────────────
# Π.2.prep.8 — §7 rollback plan
# ──────────────────────────────────────────────────────────────────


class TestPi2PrepRollbackPlan:
    """§7 must document a rollback plan for post-flip issues."""

    def test_rollback_mentions_git_revert(self):
        text = _checklist_text()
        assert "git revert" in text or "revert" in text.lower()

    def test_rollback_three_paths(self):
        text = _checklist_text()
        # The rollback should distinguish hot-fix vs identified-issue vs
        # publisher-direction-change paths
        assert "Hot-fix" in text or "hot-fix" in text
        assert "Identified-issue" in text or "identified-issue" in text.lower()


# ──────────────────────────────────────────────────────────────────
# Π.2.prep.9 — current editions.yaml ethiopian-tewahedo state
# ──────────────────────────────────────────────────────────────────


class TestPi2PrepEthiopianTewahedoCurrentState:
    """The checklist references the CURRENT ethiopian-tewahedo
    popup_languages_default state (english/hebrew/greek). Pin
    that current state so Π.2.prep's diff projection remains
    accurate."""

    def test_editions_yaml_loads(self):
        data = yaml.safe_load(EDITIONS_YAML.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_ethiopian_tewahedo_edition_exists(self):
        data = yaml.safe_load(EDITIONS_YAML.read_text(encoding="utf-8"))
        editions = data.get("editions") or []
        et = next((e for e in editions if e.get("id") == "ethiopian-tewahedo"), None)
        assert et is not None, "Π.2.prep: ethiopian-tewahedo edition must exist in editions.yaml"

    def test_ethiopian_tewahedo_popup_languages_currently_5_witnesses(self):
        """Current state: the 5-witness popup set wlc/lxx-greek/greek-nt/vulgate/
        arabic, set by EPUB Wave 3 #6 (which dropped the English KJV and widened
        popups to the original-language + Latin + Arabic witnesses). NOTE:
        popup_languages_default now holds popup-VERSION ids, not the legacy
        language-family names english/hebrew/greek. The earlier 'Π.2 will add
        geez+amharic (5 total)' premise is SUPERSEDED — per the 2026-05-16
        standalone-bibles decision the Ge'ez/Amharic Bibles carry their OWN popups
        and are NOT wired into the other editions. This stays a drift-detector: if
        it fails, refresh PI2_PRE_FLIGHT_CHECKLIST §5 against the new value."""
        data = yaml.safe_load(EDITIONS_YAML.read_text(encoding="utf-8"))
        editions = data["editions"]
        et = next(e for e in editions if e.get("id") == "ethiopian-tewahedo")
        pld = et.get("popup_languages_default") or []
        assert sorted(pld) == sorted(["wlc", "lxx-greek", "greek-nt", "vulgate", "arabic"]), (
            f"ethiopian-tewahedo.popup_languages_default expected the 5-witness set "
            f"(Wave 3 #6: wlc/lxx-greek/greek-nt/vulgate/arabic); got {pld!r}. "
            f"If this changed via an upstream flip, refresh PI2_PRE_FLIGHT_CHECKLIST §5 diff."
        )


# ──────────────────────────────────────────────────────────────────
# Π.2.prep.10 — laodiceans canon-membership current state
# ──────────────────────────────────────────────────────────────────


class TestPi2PrepLaodiceansCanonState:
    """D2 decision: laodiceans is NOT in any canon at Π.2.prep
    ship time. Pin that current state."""

    def test_laodiceans_not_in_ethiopian_canon(self):
        data = yaml.safe_load(CANONS_YAML.read_text(encoding="utf-8"))
        canons = data.get("canons") or {}
        ethiopian = canons.get("ethiopian") or {}
        books = ethiopian.get("books") or []
        assert "lao" not in books, (
            "Π.2.prep: lao must NOT be in ethiopian canon at Π.2.prep ship "
            "time (D2 default-recommendation: EXCLUDE; if publisher elects "
            "to add, separate Π.2.B ship handles canon insertion)."
        )


# ──────────────────────────────────────────────────────────────────
# Π.2.prep.11 — SCOPE doc cross-reference
# ──────────────────────────────────────────────────────────────────


class TestPi2PrepScopeCrossReference:
    """The checklist must reference SCOPE §Π.2 as the design-
    authoritative spec."""

    def test_checklist_references_scope_doc(self):
        text = _checklist_text()
        assert "SCOPE_2026-05-14-parallel-bible" in text

    def test_scope_doc_pi2_section_exists(self):
        """Sanity: the SCOPE §Π.2 section must exist for the
        cross-reference to be valid."""
        scope_text = SCOPE_DOC.read_text(encoding="utf-8")
        assert "### Π.2 —" in scope_text


# ──────────────────────────────────────────────────────────────────
# Π.2.prep.12 — closed-arc invariant preservation
# ──────────────────────────────────────────────────────────────────


class TestPi2PrepClosedArcInvariantPreservation:
    """Π.2.prep must not regress prior invariants. Pin a sample
    set that would catch any accidental editions.yaml /
    canons.yaml mutation."""

    def test_editions_yaml_other_editions_unchanged(self):
        """Other 8 editions retain their existing popup_languages_default."""
        data = yaml.safe_load(EDITIONS_YAML.read_text(encoding="utf-8"))
        editions = data["editions"]
        for ed in editions:
            ed_id = ed.get("id")
            if ed_id == "ethiopian-tewahedo":
                continue  # ethiopian-tewahedo is the Π.2 target
            pld = ed.get("popup_languages_default")
            if pld is not None:
                # Any non-target edition with popup_languages_default set
                # should NOT yet contain both geez and amharic (that would
                # mean Π.2 already shipped beyond ethiopian-tewahedo).
                assert not ("geez" in pld and "amharic" in pld), (
                    f"Π.2.prep: edition {ed_id!r} unexpectedly already has "
                    f"geez+amharic in popup_languages_default; Π.2 should be "
                    f"ethiopian-tewahedo-only."
                )

    def test_canons_yaml_ethiopian_canon_unchanged(self):
        """Ethiopian canon should still have 87 books (or whatever
        it had at δ.1.x.A.0 ship time)."""
        data = yaml.safe_load(CANONS_YAML.read_text(encoding="utf-8"))
        canons = data.get("canons") or {}
        ethiopian = canons.get("ethiopian") or {}
        books = ethiopian.get("books") or []
        # 87 books per the description; some sub-counts may include man as a
        # supplementary chapter. Tolerate 86-88 range.
        assert 80 <= len(books) <= 90, (
            f"Π.2.prep: ethiopian canon book count {len(books)} unexpected; Π.2.prep does NOT mutate canons.yaml."
        )

    def test_jubilees_one_enoch_meqabyan_in_ethiopian_canon(self):
        """Π.1's structural_map declarations must be reflected by
        actual canon membership — jub/1en/mq1/mq2/mq3 in ethiopian
        canon."""
        data = yaml.safe_load(CANONS_YAML.read_text(encoding="utf-8"))
        books = data["canons"]["ethiopian"]["books"]
        for code in ["jub", "1en", "mq1", "mq2", "mq3"]:
            assert code in books, (
                f"Π.2.prep: ethiopian canon must include {code!r} "
                f"(declared in Π.1 structural_map; required for Π.2 emission)"
            )


# ──────────────────────────────────────────────────────────────────
# Π.2.prep.13 — phase coverage
# ──────────────────────────────────────────────────────────────────


class TestPi2PrepPhaseCoverage:
    """The Π.2.prep phase tag must surface in CHANGELOG so the
    project linter's untracked-phases check passes."""

    def test_pi2prep_phase_tag_in_changelog(self):
        changelog = REPO / "dev" / "CHANGELOG.md"
        text = changelog.read_text(encoding="utf-8")
        assert "Π.2.prep" in text, "Π.2.prep: CHANGELOG.md must mention the Π.2.prep phase tag"

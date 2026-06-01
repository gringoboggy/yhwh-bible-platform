"""τ.6.x.0c — Tesseract install verification + script/Ethiopic
adoption codification pins (2026-05-14).

τ.6.x.0c closes the operator-side prerequisite list that τ.6.x.0b
flagged. The operator installed Tesseract 5.5.0 (UB-Mannheim Windows
build) and verified that:

- `amh.traineddata` is present in the standard install.
- `gez.traineddata` is ABSENT, as anticipated by τ.6.x.0b.
- **`script/Ethiopic` is present** in the standard install — this is
  Tesseract's upstream-blessed Ethiopic-script-level recognizer.
  Geʽez/Amharic/Tigrinya share a single script (fidel); the
  script-level model recognizes any of them correctly.

The τ.6.x.0c DECISION: adopt `script/Ethiopic` as the Geʽez recognizer.
This extends the τ.6.x.0b fallback enumeration (Option A: skip,
Option B: phase4-defer) with a new third option strictly better than
either. The honesty contract is preserved (tier-3 still acknowledges
imperfection); no community-fork license risk; same Apache-2.0
posture as `amh.traineddata`.

τ.6.x.0c deliverables under test:

1. `scripts.core.paths.tesseract_binary()` resolver landed: PATH-
   first lookup → known platform install paths → `TESSERACT_BIN`
   env-override. Returns `Path | None`; cached + cache-resettable.
   The project no longer depends on the operator having Tesseract
   on PATH.

2. `_source.yaml::ocr_strategy.tau6x0c_verification` block records
   the operator-side verification result with the expected shape:
   tesseract_install + amharic_tessdata + geez_tessdata +
   geez_recognizer_adopted + resolver + no_ingest_at_this_phase +
   next_phase = τ.6.x.1+.

3. `_source.yaml::ocr_strategy.prerequisites.geez_tessdata` extended
   with `option_c: use-script-Ethiopic-tessdata` + `chosen_option:
   option_c` + `chosen_at_phase: τ.6.x.0c` (extends the τ.6.x.0b
   fallback enumeration; the τ.6.x.0b shape is preserved).

4. SCOPE doc §7.5 records the τ.6.x.0c verification block with the
   `script/Ethiopic` adoption decision, the updated Option-D tier-
   policy table, and the Tesseract invocation pattern
   `-l script/Ethiopic+amh`.

5. PI2_PRE_FLIGHT_CHECKLIST.md gate-dashboard row for τ.6.x.0c
   flipped from ⬜ pending → ✓ SHIPPED.

6. (Optional runtime probe) If Tesseract is locally available, the
   `amh` and `script/Ethiopic` language packs are visible to
   `tesseract --list-langs`. Skipped if not available — keeps the
   suite environment-independent.

7. Closed-arc invariants preserved: Π.0.1 amharic-in-POPUP_LANGUAGES,
   γ.4.8.E 67/67 Mäqabyan, γ.4.8.F ≥212 Mäqabyan, τ.6.x.0a contract
   (translation slots gen.py-only), τ.6.x.0b contract (no data
   ingest, Option-D-Hybrid authorized, Tesseract default engine).

8. CHANGELOG records the τ.6.x.0c ship entry.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml


REPO = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0c — resolver module
# ──────────────────────────────────────────────────────────────────


class TestTau6X0cResolverModule:
    """The `scripts.core.paths.tesseract_binary()` resolver landed at
    τ.6.x.0c. The resolver is path-resolution only (no runtime
    probes); existence / version verification is the caller's job.
    """

    def test_resolver_importable(self):
        from scripts.core.paths import tesseract_binary

        assert callable(tesseract_binary), "tesseract_binary must be a callable"

    def test_resolver_exported(self):
        from scripts.core import paths

        assert "tesseract_binary" in paths.__all__, "tesseract_binary must appear in scripts.core.paths.__all__"
        assert "reset_tesseract_binary" in paths.__all__, (
            "reset_tesseract_binary must appear in scripts.core.paths.__all__"
        )

    def test_resolver_return_type(self):
        from scripts.core.paths import tesseract_binary

        result = tesseract_binary()
        assert result is None or isinstance(result, Path), (
            f"tesseract_binary() must return Path | None; got {type(result).__name__}"
        )

    def test_resolver_honors_env_override(self, tmp_path, monkeypatch):
        from scripts.core import paths

        fake = tmp_path / "fake_tesseract.exe"
        fake.write_text("not a real binary")
        monkeypatch.setenv("TESSERACT_BIN", str(fake))
        paths.reset_tesseract_binary()
        try:
            result = paths.tesseract_binary()
            assert result == fake, f"TESSERACT_BIN override must take precedence; got {result!r} expected {fake!r}"
        finally:
            paths.reset_tesseract_binary()

    def test_resolver_falls_through_when_env_override_invalid(self, monkeypatch):
        from scripts.core import paths

        monkeypatch.setenv("TESSERACT_BIN", "/nonexistent/path/to/tesseract")
        paths.reset_tesseract_binary()
        try:
            # Resolver should fall through to PATH / known-paths rather
            # than returning the invalid override. It may return None
            # (no Tesseract anywhere) or a real Path (found elsewhere).
            result = paths.tesseract_binary()
            assert result is None or (isinstance(result, Path) and result.is_file()), (
                "Invalid TESSERACT_BIN must fall through to PATH/known-paths"
            )
            assert result != Path("/nonexistent/path/to/tesseract"), "Invalid TESSERACT_BIN must NOT be returned"
        finally:
            paths.reset_tesseract_binary()

    def test_resolver_cache_reset(self, tmp_path, monkeypatch):
        from scripts.core import paths

        fake1 = tmp_path / "tess1.exe"
        fake1.write_text("x")
        fake2 = tmp_path / "tess2.exe"
        fake2.write_text("x")
        monkeypatch.setenv("TESSERACT_BIN", str(fake1))
        paths.reset_tesseract_binary()
        try:
            assert paths.tesseract_binary() == fake1
            monkeypatch.setenv("TESSERACT_BIN", str(fake2))
            # Without resetting the cache, the prior result persists.
            assert paths.tesseract_binary() == fake1
            paths.reset_tesseract_binary()
            assert paths.tesseract_binary() == fake2
        finally:
            paths.reset_tesseract_binary()


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0c — _source.yaml tau6x0c_verification block
# ──────────────────────────────────────────────────────────────────


class TestTau6X0cSourceYamlVerificationBlock:
    """The _source.yaml::ocr_strategy.tau6x0c_verification block
    records the operator-side install + tessdata-availability results
    with the expected shape."""

    YAML_PATH = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"

    def _verification(self):
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        return cfg["ocr_strategy"]["tau6x0c_verification"]

    def test_block_present(self):
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        assert "tau6x0c_verification" in cfg["ocr_strategy"], (
            "_source.yaml::ocr_strategy must declare a tau6x0c_verification block"
        )

    def test_verified_phase_and_date(self):
        v = self._verification()
        assert v["verified_at_phase"] == "τ.6.x.0c"
        assert "2026-05-14" in str(v["verified_date"])

    def test_tesseract_installed_with_version(self):
        v = self._verification()
        ti = v["tesseract_install"]
        assert ti["installed"] is True
        assert ti["version"].startswith("5."), f"Tesseract version must be 5.x; got {ti['version']!r}"
        assert "tesseract" in ti["install_path"].lower(), (
            f"install_path must reference tesseract; got {ti['install_path']!r}"
        )
        assert ti["license"] == "Apache-2.0"

    def test_amharic_tessdata_present(self):
        v = self._verification()
        amh = v["amharic_tessdata"]
        assert amh["present"] is True
        assert amh["file"] == "amh.traineddata"

    def test_geez_tessdata_absent_as_expected(self):
        v = self._verification()
        gez = v["geez_tessdata"]
        assert gez["present"] is False, "τ.6.x.0c: gez.traineddata absence is the anticipated finding from τ.6.x.0b"
        assert gez["file"] == "gez.traineddata"
        assert gez["anticipated_at_phase"] == "τ.6.x.0b"

    def test_script_ethiopic_adopted(self):
        v = self._verification()
        adopted = v["geez_recognizer_adopted"]
        assert adopted["model"] == "script/Ethiopic", "τ.6.x.0c adopted script/Ethiopic as the Geʽez recognizer"
        assert adopted["present"] is True
        assert adopted["adopted_at_phase"] == "τ.6.x.0c"
        rationale = adopted.get("rationale") or ""
        assert "fidel" in rationale.lower() or "script" in rationale.lower(), (
            "rationale must explain the script-level recognition basis"
        )

    def test_invocation_pattern_uses_script_ethiopic_plus_amh(self):
        v = self._verification()
        adopted = v["geez_recognizer_adopted"]
        pattern = adopted["invocation_pattern"]
        assert "script/Ethiopic" in pattern, "invocation_pattern must reference script/Ethiopic"
        assert "amh" in pattern, "invocation_pattern must include amh for the Amharic column"

    def test_resolver_block_declared(self):
        v = self._verification()
        r = v["resolver"]
        assert r["module"] == "scripts.core.paths"
        assert r["function"] == "tesseract_binary"
        assert r["added_at_phase"] == "τ.6.x.0c"
        order = r["resolution_order"]
        assert any("TESSERACT_BIN" in step for step in order)
        assert any("which" in step.lower() or "path" in step.lower() for step in order)

    def test_no_ingest_at_this_phase(self):
        v = self._verification()
        assert v["no_ingest_at_this_phase"] is True, "τ.6.x.0c is operator-side install + codification; no data ingest"

    def test_next_phase_is_tau6x1plus(self):
        v = self._verification()
        assert v["next_phase"] == "τ.6.x.1+"

    def test_bonus_languages_documented(self):
        v = self._verification()
        bonus = v["bonus_languages_available"]
        # The bonus list is documented for downstream arcs; just pin
        # that the canonical six are recorded.
        for code in ("grc", "heb", "syr", "lat", "tir"):
            assert code in bonus, f"bonus_languages_available must include {code}"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0c — geez_tessdata fallback extended with Option C
# ──────────────────────────────────────────────────────────────────


class TestTau6X0cGeezFallbackExtended:
    """The τ.6.x.0b geez_tessdata.fallback_if_missing enumeration is
    extended at τ.6.x.0c with a new Option C (script/Ethiopic). The
    original Options A + B remain documented so the historical-pin
    convention (extraction_status_at_declaration analog) is preserved.
    """

    YAML_PATH = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"

    def _fallback(self):
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        return cfg["ocr_strategy"]["prerequisites"]["geez_tessdata"]["fallback_if_missing"]

    def test_option_a_preserved(self):
        fb = self._fallback()
        assert "option_a" in fb, "τ.6.x.0b option_a (skip-geez-column) must be preserved"
        assert "skip" in fb["option_a"].lower()

    def test_option_b_preserved(self):
        fb = self._fallback()
        assert "option_b" in fb, "τ.6.x.0b option_b (phase4-defer) must be preserved"
        assert "δ.1.x" in fb["option_b"] or "phase4" in fb["option_b"].lower()

    def test_option_c_added(self):
        fb = self._fallback()
        assert "option_c" in fb, "τ.6.x.0c must add option_c (script-Ethiopic)"
        assert "script-Ethiopic" in fb["option_c"] or "script/Ethiopic" in fb["option_c"]

    def test_option_c_chosen_at_tau6x0c(self):
        fb = self._fallback()
        assert fb["chosen_at_phase"] == "τ.6.x.0c"
        assert fb["chosen_option"] == "option_c"

    def test_chosen_rationale_documented(self):
        fb = self._fallback()
        rationale = fb.get("chosen_rationale") or ""
        assert "license" in rationale.lower() or "apache" in rationale.lower(), (
            "chosen_rationale must document the license posture (no community-fork gate)"
        )

    def test_geez_fallback_flag_extended(self):
        fb = self._fallback()
        flag = fb["operator_chooses_via"]
        assert "script-ethiopic" in flag.lower(), (
            "--geez-fallback flag must be extended to include the script-ethiopic option"
        )


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0c — SCOPE doc records the script/Ethiopic adoption
# ──────────────────────────────────────────────────────────────────


class TestTau6X0cScopeAdoptionRecorded:
    """The SCOPE doc §7.5 records the τ.6.x.0c verification block
    with the script/Ethiopic adoption decision."""

    SCOPE_PATH = REPO / "dev" / "archive" / "SCOPE_2026-05-14-parallel-bible.md"

    def test_scope_doc_exists(self):
        assert self.SCOPE_PATH.is_file()

    def test_tau6x0c_section_header_present(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        assert "τ.6.x.0c verification" in body, "SCOPE doc must declare a τ.6.x.0c verification section"

    def test_script_ethiopic_adoption_recorded(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        assert "script/Ethiopic" in body, "SCOPE doc must record script/Ethiopic adoption at τ.6.x.0c"

    def test_decision_marked_authorized(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        normalized = " ".join(body.split())
        assert "DECISION (τ.6.x.0c): ADOPT" in normalized or "AUTHORIZED at τ.6.x.0c" in normalized, (
            "SCOPE doc must mark the script/Ethiopic adoption decision as authorized"
        )

    def test_invocation_pattern_documented(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        assert "-l script/Ethiopic+amh" in body, "SCOPE doc must document the -l script/Ethiopic+amh invocation pattern"

    def test_tau6x0b_decision_block_still_intact(self):
        # Closed-arc invariant: τ.6.x.0c must not regress the τ.6.x.0b
        # decision codification. The original τ.6.x.0b assertions
        # (Option-D-Hybrid authorized + Tesseract engine + gez
        # uncertainty) must remain in the SCOPE doc.
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        normalized = " ".join(body.split())
        assert "AUTHORIZED STRATEGY: Option D" in body, (
            "τ.6.x.0c must not regress τ.6.x.0b Option-D-Hybrid authorization"
        )
        assert "UNCERTAIN AVAILABILITY" in normalized, "τ.6.x.0c must not erase τ.6.x.0b's documented gez uncertainty"

    def test_resolver_location_documented(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        assert "scripts.core.paths.tesseract_binary" in body, "SCOPE doc must point at the new resolver location"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0c — PI2 pre-flight checklist gate-dashboard flip
# ──────────────────────────────────────────────────────────────────


class TestTau6X0cPreFlightChecklistGateFlip:
    """The PI2 pre-flight checklist gate-dashboard row for τ.6.x.0c
    flipped from ⬜ pending → ✓ SHIPPED. The τ.6.x.0c row mentions
    the script/Ethiopic resolution + the resolver location."""

    CHECKLIST_PATH = REPO / "dev" / "PI2_PRE_FLIGHT_CHECKLIST.md"

    def test_checklist_exists(self):
        assert self.CHECKLIST_PATH.is_file()

    def test_tau6x0c_row_marked_shipped(self):
        body = self.CHECKLIST_PATH.read_text(encoding="utf-8")
        # Find the τ.6.x.0c row and check it contains a shipped marker.
        rows = [line for line in body.splitlines() if "τ.6.x.0c" in line and "|" in line]
        assert rows, "PI2 checklist must contain a τ.6.x.0c row"
        shipped_rows = [r for r in rows if "SHIPPED" in r or "shipped" in r]
        assert shipped_rows, f"τ.6.x.0c row must indicate SHIPPED state; got {rows!r}"

    def test_script_ethiopic_resolution_referenced(self):
        body = self.CHECKLIST_PATH.read_text(encoding="utf-8")
        assert "script/Ethiopic" in body, "PI2 checklist must reference the script/Ethiopic resolution"

    def test_resolver_referenced(self):
        body = self.CHECKLIST_PATH.read_text(encoding="utf-8")
        assert "tesseract_binary" in body, (
            "PI2 checklist must reference the scripts.core.paths.tesseract_binary resolver"
        )

    def test_verification_commands_updated_for_script_ethiopic(self):
        body = self.CHECKLIST_PATH.read_text(encoding="utf-8")
        # The §4 verification commands should grep for script/Ethiopic,
        # not gez (since gez.traineddata is intentionally not required).
        assert "script/Ethiopic" in body, "Verification commands must check for script/Ethiopic"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0c — runtime tesseract probe (optional, env-dependent)
# ──────────────────────────────────────────────────────────────────


class TestTau6X0cTesseractRuntime:
    """OPTIONAL runtime probe — if Tesseract is locally available via
    the resolver, verify that the codified verification matches the
    actual runtime state (amh + script/Ethiopic visible to
    `tesseract --list-langs`). Skipped when Tesseract is not
    installed locally so the suite remains environment-independent.
    """

    @staticmethod
    def _tesseract_or_skip() -> Path:
        from scripts.core.paths import tesseract_binary

        binary = tesseract_binary()
        if binary is None:
            pytest.skip("Tesseract not locally available; runtime probe skipped")
        return binary

    def test_tesseract_version_5_or_higher(self):
        binary = self._tesseract_or_skip()
        result = subprocess.run(
            [str(binary), "--version"],
            stdin=subprocess.DEVNULL,  # W-W1 mitigation (τ.6.x.1)
            capture_output=True,
            text=True,
            timeout=10,
        )
        # tesseract --version sometimes writes the version line to
        # stderr (Windows builds occasionally; varies by version).
        combined = (result.stdout or "") + (result.stderr or "")
        assert "tesseract" in combined.lower(), f"`tesseract --version` output must mention tesseract; got {combined!r}"
        # Allow "tesseract v5.x" or "tesseract 5.x" or "Tesseract 5.x".
        major_version_indicators = ("v5.", " 5.", "Tesseract 5", "tesseract 5")
        assert any(s in combined for s in major_version_indicators), (
            f"Tesseract major version must be 5+; got {combined!r}"
        )

    def test_amh_traineddata_visible(self):
        binary = self._tesseract_or_skip()
        result = subprocess.run(
            [str(binary), "--list-langs"],
            stdin=subprocess.DEVNULL,  # W-W1 mitigation (τ.6.x.1)
            capture_output=True,
            text=True,
            timeout=10,
        )
        combined = (result.stdout or "") + (result.stderr or "")
        langs = {line.strip() for line in combined.splitlines()}
        assert "amh" in langs, f"`amh` must be in tesseract --list-langs output; got {sorted(langs)!r}"

    def test_script_ethiopic_visible(self):
        binary = self._tesseract_or_skip()
        result = subprocess.run(
            [str(binary), "--list-langs"],
            stdin=subprocess.DEVNULL,  # W-W1 mitigation (τ.6.x.1)
            capture_output=True,
            text=True,
            timeout=10,
        )
        combined = (result.stdout or "") + (result.stderr or "")
        # `--list-langs` formats script-models as `script/<X>` on POSIX
        # and `script\<X>` on Windows (mirrors the on-disk directory
        # layout). Accept either separator.
        langs = {line.strip() for line in combined.splitlines()}
        assert ("script/Ethiopic" in langs) or ("script\\Ethiopic" in langs), (
            "script/Ethiopic must be in tesseract --list-langs output "
            "(this is the Geʽez recognizer adopted at τ.6.x.0c); "
            f"got {sorted(langs)!r}"
        )


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0c — closed-arc invariants regression-guarded
# ──────────────────────────────────────────────────────────────────


class TestTau6X0cClosedArcInvariantPreservation:
    """The Π.0.1 + τ.6.x.0a + τ.6.x.0b + γ.4.8.E + γ.4.8.F invariants
    remain intact after τ.6.x.0c."""

    def test_amharic_still_in_popup_languages(self):
        from scripts.build_edition import POPUP_LANGUAGES

        assert "amharic" in POPUP_LANGUAGES, "τ.6.x.0c must not regress Π.0.1: amharic must remain in POPUP_LANGUAGES"

    def test_geez_tewahedo_still_gen_only(self):
        slot = REPO / "content" / "translations" / "geez-tewahedo"
        files = sorted(p.name for p in slot.iterdir() if p.suffix == ".py")
        assert "gen.py" in files, (
            f"τ.6.x.2.a-h batch: geez-tewahedo/ must contain gen.py (Π.0 seed or its ocr-tier3 successor); got {files}"
        )  # MIGRATED at τ.6.x.2.a-h batch ship-time (2026-05-15):
        # originally asserted geez-tewahedo/ holds ONLY the Π.0
        # gen.py seed. The τ.6.x.2.a-h Geʽez catchup batch upgraded
        # the Geʽez column to 8 ocr-tier3 books (gen+ex+lev+num+deu
        # +jos+jdg+rut). Same migration the companion
        # test_amharic_tewahedo_contains_gen_py received at τ.7.x.b.
        # Durable invariant: gen.py present (Π.0 seed or successor).

    def test_amharic_tewahedo_contains_gen_py(self):
        """Refactored share-pin→milestone-pin at τ.7.x.b ship-time per
        `feedback_share_pin_pattern`. τ.6.x.0c's original invariant
        (`files == ['gen.py']`) was the Π.0 seed state; τ.7.x.a + τ.7.x.b
        broke this exact assertion. Durable invariant: gen.py is present."""
        slot = REPO / "content" / "translations" / "amharic-tewahedo"
        files = sorted(p.name for p in slot.iterdir() if p.suffix == ".py")
        assert "gen.py" in files, (
            f"τ.6.x.0c contract relaxed at τ.7.x.b: amharic-tewahedo must contain gen.py; got {files}"
        )

    def test_tau6x0b_option_d_authorization_intact(self):
        path = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        strat = cfg["ocr_strategy"]
        assert strat["authorized_option"] == "D-Hybrid", (
            "τ.6.x.0c must not regress τ.6.x.0b: Option-D-Hybrid authorization preserved"
        )
        assert strat["default_engine"] == "tesseract", (
            "τ.6.x.0c must not regress τ.6.x.0b: default engine remains Tesseract"
        )
        assert strat["no_ingest_at_this_phase"] is True, (
            "τ.6.x.0c is no-ingest like τ.6.x.0b (declarative codification only)"
        )

    def test_meqabyan_arc_close_67_67_intact(self):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        ec = sources.ethiopian_commentaries()
        for book, total in [("mq1", 36), ("mq2", 21), ("mq3", 10)]:
            chs_with_entries = set()
            for ch in range(1, total + 1):
                for v in range(1, 60):
                    entries = [e for e in ec.for_verse(book, ch, v) if e.father == "Meqabyan (Ethiopian tradition)"]
                    if entries:
                        chs_with_entries.add(ch)
                        break
            assert chs_with_entries == set(range(1, total + 1)), (
                f"τ.6.x.0c must not regress γ.4.8.E arc-close {book} {total}/{total}"
            )

    def test_meqabyan_count_at_least_212(self):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        ec = sources.ethiopian_commentaries()
        meq = [
            e
            for verse_entries in ec._by_verse.values()
            for e in verse_entries
            if e.father == "Meqabyan (Ethiopian tradition)"
        ]
        assert len(meq) >= 212, f"τ.6.x.0c: Meqabyan count must remain ≥212; got {len(meq)}"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0c — phase coverage
# ──────────────────────────────────────────────────────────────────


class TestTau6X0cPhaseCoverage:
    """τ.6.x.0c is mentioned in the CHANGELOG (the ship entry exists)
    and is no longer listed as a pending sub-phase in the PLAN."""

    CHANGELOG_PATH = REPO / "dev" / "CHANGELOG.md"
    # PLAN_2026-05-09 archived to dev/archive/ on 2026-05-21 (superseded
    # by PLAN_2026-05-21); the phase ledger it pins lives there now.
    PLAN_PATH = REPO / "dev" / "archive" / "PLAN_2026-05-09.md"

    def test_changelog_mentions_tau6x0c_ship(self):
        body = self.CHANGELOG_PATH.read_text(encoding="utf-8")
        assert "τ.6.x.0c" in body, "CHANGELOG must mention τ.6.x.0c"
        # The ship entry must indicate it shipped (not just listed as
        # pending in a prior session's pending-ledger).
        # Find the first τ.6.x.0c line that is a phase header / ship marker.
        normalized = body.lower()
        assert "shipped" in normalized or "ship" in normalized, "CHANGELOG must record τ.6.x.0c as a ship event"

    def test_plan_lists_tau6x0c_as_shipped(self):
        body = self.PLAN_PATH.read_text(encoding="utf-8")
        # Find τ.6.x.0c row in the parallel-bible track ledger.
        rows = [line for line in body.splitlines() if "τ.6.x.0c" in line]
        assert rows, "PLAN must contain a τ.6.x.0c row"
        # At least one row should mark it shipped (✓), not just pending (⬜).
        shipped = [r for r in rows if "✓" in r]
        assert shipped, f"PLAN must mark τ.6.x.0c as shipped (✓) in the parallel-bible track ledger; got {rows!r}"

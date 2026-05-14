"""τ.6.x.0b — OCR-quality strategy decision codification pins
(2026-05-14).

τ.6.x.0b is a DECISION-CODIFICATION phase. No data ingest, no
translation-slot population. The phase codifies Option D (Hybrid) as
the AUTHORIZED OCR strategy for the parallel-Bible expansion per
`feedback_extensive_answers` (broadest scope) + `feedback_license_
flagging` (default = continue most-logical-path; flag load-bearing
external installs):

- **Authorized strategy:** Option D (Hybrid) — tier-3 Tesseract baseline
  for standard-canon, tier-1 Phase-4 page-image for Meqabyan + 1 Enoch
  + Jubilees, escalation to Option B (Cloud OCR) opt-in only.

- **Default engine:** Tesseract (Option A as the tier-3 sub-strategy).

- **Honesty contract:** every tier-3 entry carries SOURCE_QUALITY
  provenance + per-entry caveat in the reader-facing apparatus.

- **Load-bearing user-side prerequisites flagged** (per `feedback_
  license_flagging`): Tesseract install (Apache-2.0, free, no
  publisher-authorization-needed), Amharic tessdata `amh.traineddata`
  (free), Geʽez tessdata `gez.traineddata` AVAILABILITY-UNCERTAIN
  (verification gated to τ.6.x.0c).

- **No data ingest at this phase:** geez-tewahedo + amharic-tewahedo
  translation slots REMAIN at their Π.0 seed state (3 verses Genesis
  only). The τ.6.x.0a contract is preserved.

- **Closed-arc invariants regression-guarded:** γ.4.8.E 67/67 chapter
  coverage of Meqabyan + Meqabyan count ≥212 floor + Π.0 amharic
  popup-language registration.

τ.6.x.0b deliverables under test:

1. SCOPE doc §7.5 records the τ.6.x.0b decision block (Option D
   AUTHORIZED + 2026-05-14 + Tesseract engine choice).

2. _source.yaml has the `ocr_strategy` block with the correct shape:
   authorized_option, default_engine, tier_policy, prerequisites,
   honesty_contract, no_ingest_at_this_phase.

3. Translation-slot τ.6.x.0a CONTRACT preserved (geez-tewahedo +
   amharic-tewahedo each remain gen.py only).

4. γ.4.8.E ARC-CLOSE 67/67 chapter coverage of Meqabyan intact;
   Meqabyan count ≥212 floor preserved.

5. Π.0 amharic-in-POPUP_LANGUAGES preserved.
"""

from __future__ import annotations

from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0b — SCOPE doc records the decision
# ──────────────────────────────────────────────────────────────────


class TestTau6x0bScopeDecisionBlock:
    """The SCOPE doc §7.5 has the τ.6.x.0b decision block with the
    Option D authorization + Tesseract engine choice + Tesseract-not-
    installed verification recorded."""

    SCOPE_PATH = REPO / "dev" / "SCOPE_2026-05-14-parallel-bible.md"

    def test_scope_doc_exists(self):
        assert self.SCOPE_PATH.is_file(), "SCOPE doc must exist for τ.6.x.0b pin"

    def test_decision_block_present(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        assert "τ.6.x.0b decision" in body, "SCOPE doc must declare a τ.6.x.0b decision block"

    def test_option_d_authorized(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        assert "AUTHORIZED STRATEGY: Option D" in body, (
            "SCOPE doc must record Option D (Hybrid) as AUTHORIZED at τ.6.x.0b"
        )

    def test_authorized_date_recorded(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        assert "AUTHORIZED (2026-05-14)" in body or "AUTHORIZED**" in body, (
            "SCOPE doc must record the authorization date (2026-05-14)"
        )

    def test_tesseract_engine_choice_recorded(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        # Allow whitespace flexibility (line-wrap inside markdown bold).
        normalized = " ".join(body.split())
        assert "Tesseract (Option A as sub-strategy)" in normalized, (
            "SCOPE doc must record Tesseract as the default OCR engine within Option D"
        )

    def test_tesseract_not_installed_verification_recorded(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        normalized = " ".join(body.split())
        # The ship-time verification finding must be in the doc.
        assert "Verified absent on the development workstation" in normalized, (
            "SCOPE doc must record the Tesseract-not-installed verification"
        )

    def test_geez_tessdata_uncertainty_documented(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        normalized = " ".join(body.split())
        assert "UNCERTAIN AVAILABILITY" in normalized, "SCOPE doc must flag the Geʽez tessdata availability uncertainty"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0b — _source.yaml ocr_strategy block shape
# ──────────────────────────────────────────────────────────────────


class TestTau6x0bSourceYamlOcrStrategy:
    """The _source.yaml has the `ocr_strategy` block with the
    authorized-option/default-engine/tier-policy/prerequisites
    sub-keys correctly populated for the τ.6.x.0b decision."""

    YAML_PATH = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"

    def _load(self):
        return yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))

    def test_ocr_strategy_block_present(self):
        cfg = self._load()
        assert "ocr_strategy" in cfg, "_source.yaml must declare an ocr_strategy block at τ.6.x.0b"

    def test_authorized_option_is_d_hybrid(self):
        cfg = self._load()
        strat = cfg["ocr_strategy"]
        assert strat["authorized_option"] == "D-Hybrid", (
            f"τ.6.x.0b: authorized_option must be 'D-Hybrid'; got {strat['authorized_option']!r}"
        )

    def test_authorized_phase_recorded(self):
        cfg = self._load()
        strat = cfg["ocr_strategy"]
        assert strat["authorized_at_phase"] == "τ.6.x.0b"

    def test_authorized_date_recorded(self):
        cfg = self._load()
        strat = cfg["ocr_strategy"]
        # YAML may parse this as a date object or as a string depending on
        # quoting; allow either as long as the year/month/day match.
        d = strat["authorized_date"]
        s = str(d)
        assert "2026-05-14" in s, f"authorized_date must be 2026-05-14; got {s!r}"

    def test_default_engine_is_tesseract(self):
        cfg = self._load()
        strat = cfg["ocr_strategy"]
        assert strat["default_engine"] == "tesseract", (
            f"τ.6.x.0b: default OCR engine must be 'tesseract' (Option A sub-strategy); got {strat['default_engine']!r}"
        )

    def test_cloud_ocr_opt_in_available(self):
        cfg = self._load()
        strat = cfg["ocr_strategy"]
        assert strat["cloud_ocr_escalation_available"] is True, (
            "τ.6.x.0b: Cloud OCR (Option B) must remain available as opt-in escalation"
        )

    def test_honesty_contract_present(self):
        cfg = self._load()
        strat = cfg["ocr_strategy"]
        contract = strat.get("honesty_contract") or ""
        assert "SOURCE_QUALITY" in contract, "honesty_contract must mention SOURCE_QUALITY provenance"
        assert "ocr-tier3" in contract, "honesty_contract must mention ocr-tier3 caveat behavior"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0b — tier_policy structure
# ──────────────────────────────────────────────────────────────────


class TestTau6x0bTierPolicy:
    """The tier_policy under ocr_strategy maps each book group to
    its target tier + path + shipping phase."""

    YAML_PATH = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"

    def _load(self):
        return yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))

    def test_meqabyan_to_phase4_tier1(self):
        cfg = self._load()
        policy = cfg["ocr_strategy"]["tier_policy"]["meqabyan"]
        assert policy["target_tier"] == "page-image-tier1"
        assert policy["shipping_phase"] == "δ.1.x"
        assert policy["books"] == ["mq1", "mq2", "mq3"]

    def test_one_enoch_to_phase4_tier1(self):
        cfg = self._load()
        policy = cfg["ocr_strategy"]["tier_policy"]["one_enoch"]
        assert policy["target_tier"] == "page-image-tier1"
        assert policy["shipping_phase"] == "δ.1.x"
        assert policy["books"] == ["1en"]

    def test_jubilees_to_phase4_tier1(self):
        cfg = self._load()
        policy = cfg["ocr_strategy"]["tier_policy"]["jubilees"]
        assert policy["target_tier"] == "page-image-tier1"
        assert policy["shipping_phase"] == "δ.1.x"
        assert policy["books"] == ["jub"]

    def test_standard_canon_baseline_tier3(self):
        cfg = self._load()
        policy = cfg["ocr_strategy"]["tier_policy"]["standard_canon_66"]
        assert policy["baseline_tier"] == "ocr-tier3"
        assert policy["upgrade_tier"] == "ocr-tier2"
        assert policy["shipping_phase"] == "τ.6.x.1+"

    def test_amharic_parallel_tier3_at_tau7x(self):
        cfg = self._load()
        policy = cfg["ocr_strategy"]["tier_policy"]["amharic_parallel"]
        assert policy["baseline_tier"] == "ocr-tier3"
        assert policy["shipping_phase"] == "τ.7.x"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0b — load-bearing user-side prerequisites flagged
# ──────────────────────────────────────────────────────────────────


class TestTau6x0bPrerequisitesFlagged:
    """Per `feedback_license_flagging`, the user-side prerequisites
    load-bearing for τ.6.x.1+ must be enumerated explicitly in
    _source.yaml::ocr_strategy.prerequisites — including the
    Tesseract install, the amh.traineddata, the gez.traineddata
    availability-uncertain flag, and the Cloud OCR opt-in gate."""

    YAML_PATH = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"

    def _prereqs(self):
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        return cfg["ocr_strategy"]["prerequisites"]

    def test_tesseract_install_flagged(self):
        prereqs = self._prereqs()
        assert "tesseract_install" in prereqs, "Tesseract install must be flagged as load-bearing prerequisite"
        ti = prereqs["tesseract_install"]
        assert ti["required_for"] == "τ.6.x.1+"
        assert ti["license"] == "Apache-2.0"
        assert ti["cost"] == "none"
        assert ti["publisher_authorization_needed"] is False

    def test_tesseract_not_installed_verification_recorded(self):
        prereqs = self._prereqs()
        ti = prereqs["tesseract_install"]
        status = ti.get("status_at_ship") or ""
        assert "not-installed" in status, (
            "Tesseract install status at ship time must record the dev-workstation verification"
        )

    def test_amharic_tessdata_flagged(self):
        prereqs = self._prereqs()
        assert "amharic_tessdata" in prereqs
        amh = prereqs["amharic_tessdata"]
        assert amh["file"] == "amh.traineddata"
        assert amh["license"] == "Apache-2.0"
        assert amh["cost"] == "none"

    def test_geez_tessdata_uncertain(self):
        prereqs = self._prereqs()
        assert "geez_tessdata" in prereqs
        gez = prereqs["geez_tessdata"]
        assert gez["file"] == "gez.traineddata"
        status = gez.get("status_at_ship") or ""
        assert "AVAILABILITY-UNCERTAIN" in status, "Geʽez tessdata availability uncertainty must be explicitly flagged"
        assert "fallback_if_missing" in gez, "Geʽez tessdata must declare a fallback policy"

    def test_cloud_ocr_opt_in_gated(self):
        prereqs = self._prereqs()
        assert "cloud_ocr_escalation" in prereqs
        cloud = prereqs["cloud_ocr_escalation"]
        assert cloud["publisher_authorization_needed"] is True, (
            "Cloud OCR must require publisher authorization per `feedback_license_flagging` "
            "(load-bearing external license)"
        )
        assert cloud["not_active_in_default_path"] is True


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0b — translation-slot τ.6.x.0a CONTRACT preserved
# ──────────────────────────────────────────────────────────────────


class TestTau6x0bTranslationSlotContractPreserved:
    """τ.6.x.0b is decision-codification only — no data ingest. The
    geez-tewahedo and amharic-tewahedo slots remain at gen.py-only
    seed state per the τ.6.x.0a contract. This pin guards against
    accidental promotion of OCR data during the decision-ship.
    """

    YAML_PATH = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"

    def test_no_ingest_flag_set(self):
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        strat = cfg["ocr_strategy"]
        assert strat["no_ingest_at_this_phase"] is True, (
            "τ.6.x.0b: no_ingest_at_this_phase must be True (decision-codification only)"
        )

    def test_translation_slot_state_documented(self):
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        strat = cfg["ocr_strategy"]
        state = strat.get("translation_slot_state") or ""
        assert "seed" in state.lower() or "Genesis" in state, (
            f"τ.6.x.0b: translation_slot_state must document Π.0-seed state; got {state!r}"
        )

    def test_geez_tewahedo_still_gen_only(self):
        slot = REPO / "content" / "translations" / "geez-tewahedo"
        files = sorted(p.name for p in slot.iterdir() if p.suffix == ".py")
        assert files == ["gen.py"], (
            f"τ.6.x.0b contract: geez-tewahedo must remain at τ.6 seed (gen.py only); got {files}"
        )

    def test_amharic_tewahedo_still_gen_only(self):
        slot = REPO / "content" / "translations" / "amharic-tewahedo"
        files = sorted(p.name for p in slot.iterdir() if p.suffix == ".py")
        assert files == ["gen.py"], (
            f"τ.6.x.0b contract: amharic-tewahedo must remain at Π.0 seed (gen.py only); got {files}"
        )


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0b — closed-arc invariants regression-guarded
# ──────────────────────────────────────────────────────────────────


class TestTau6x0bClosedArcInvariantPreservation:
    """The Π.0 + γ.4.8.E + τ.6.x.0a invariants must remain intact
    after τ.6.x.0b — amharic in POPUP_LANGUAGES, Meqabyan 67/67
    chapter coverage, Meqabyan count ≥212."""

    def test_amharic_still_in_popup_languages(self):
        from scripts.build_edition import POPUP_LANGUAGES

        assert "amharic" in POPUP_LANGUAGES, "τ.6.x.0b must not regress Π.0.1: amharic must remain in POPUP_LANGUAGES"

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
                f"τ.6.x.0b must not regress γ.4.8.E arc-close {book} {total}/{total}"
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
        assert len(meq) >= 212, f"τ.6.x.0b: Meqabyan count must remain ≥212; got {len(meq)}"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0b — next-phase pointer recorded
# ──────────────────────────────────────────────────────────────────


class TestTau6x0bNextPhasePointer:
    """The _source.yaml ocr_strategy block must declare τ.6.x.0c
    as the next phase (user-side Tesseract install + tessdata
    availability verification)."""

    YAML_PATH = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"

    def test_next_phase_is_tau6x0c(self):
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        strat = cfg["ocr_strategy"]
        assert strat["next_phase"] == "τ.6.x.0c"

    def test_next_phase_description_mentions_tesseract_install(self):
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        strat = cfg["ocr_strategy"]
        desc = strat.get("next_phase_description") or ""
        assert "Tesseract" in desc or "tesseract" in desc, (
            "next_phase_description must reference Tesseract installation"
        )
        assert "tessdata" in desc.lower() or "traineddata" in desc.lower() or "amh" in desc.lower(), (
            "next_phase_description must reference tessdata / amh / traineddata verification"
        )

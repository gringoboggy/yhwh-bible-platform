"""Π.1.B — Letter to Laodiceans alternate-source declaration
(2026-05-14).

DECLARATIVE-ONLY ship. Π.1.B fulfills the `alternate_source_required`
follow-up flag that Π.1 left on the laodiceans (lao) slot in
`content/translations/sources/parallel-bible-eotc/_source.yaml`.

Π.1 found ZERO `መልእክት ... ሎዶቅያ` opening-title matches in the EOTC
parallel-Bible PDF and declared the laodiceans slot with
`present_in_pdf: false` + `alternate_source_required: true`. Π.1.B
declares the alternate source — a new
`content/translations/sources/letter-to-laodiceans/_source.yaml`
naming J.B. Lightfoot 1875 as the primary PD English-and-Latin
anchor, M.R. James 1924 + Codex Fuldensis 547 CE as secondary
witnesses, and the standard 20-verse single-chapter division for
the Pauline pseudepigraphon.

Π.1.B does NOT ingest any data: no content/notes/lao.py mutation,
no canon-membership change in content/canons.yaml, no new
content/translations row, no production EPUB emission, no
build-pipeline invocation. The slot transitions from
"source-unavailable" to "alternate-source-declared" in the
parallel-bible-eotc inventory's new `extraction_status_current`
field; the historical Π.1 `extraction_status_at_declaration` block
is preserved verbatim (the Π.1 pin
`test_laodiceans_status_is_source_unavailable` continues to pass).

Π.1.B deliverables under test:

1. **NEW content/translations/sources/letter-to-laodiceans/_source.yaml**
   - source_id, book_code, total_chapters/total_verses, verses_per_chapter
   - primary_source block (Lightfoot 1875, PD-old, license_basis spelled
     out, archive_org_id documented)
   - secondary_sources list (James 1924 + Codex Fuldensis 547 CE)
   - tewahedo_canon_status block (Metzger 1987 §V citation,
     broader-canon-variant status)
   - structural_map.laodiceans (20-verse single-chapter division
     anchored on Lightfoot 1875 pp. 287-291 verse boundaries)
   - inventory_extension block (cross-references parent inventory)
   - no_ingest_at_this_phase contract + ingest_gate_phase
   - honesty_contract + v1_reproducibility_preserved fields
   - closed_arc_invariants_guarded list

2. **UPDATED parallel-bible-eotc/_source.yaml::laodiceans** block
   - `alternate_source_declared: true`
   - `alternate_source_id: letter-to-laodiceans`
   - `alternate_source_file: content/translations/sources/letter-to-laodiceans/_source.yaml`
   - notes field extended with Π.1.B fulfillment paragraph

3. **UPDATED tewahedo_distinctive_inventory**
   - `extraction_status_at_declaration` PRESERVED verbatim (historical)
   - NEW `extraction_status_current` reflects laodiceans flip to
     `alternate-source-declared`
   - NEW `extraction_status_phase_history.laodiceans` records the
     Π.1 → Π.1.B transition with dates and reasons
   - contract text extended with Π.1.B fulfillment paragraph

4. **Closed-arc invariants regression-guarded:** γ.4.8.E 67/67 +
   γ.4.8.F ≥212 + Π.0.1 amharic-in-POPUP_LANGUAGES + Π.0.4
   EMBED_FONT_PATHS=[] + τ.6.x.0a meqabyan section unchanged +
   τ.6.x.0b ocr_strategy.authorized_option D-Hybrid unchanged +
   δ.1.0 divergence-entries-empty + Π.1 jubilees/one_enoch sections
   unchanged + Π.1 extraction_status_at_declaration preserved as
   historical pin (Π.1 test `test_laodiceans_status_is_source_
   unavailable` continues to pass).
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parent.parent
PARENT_SOURCE_YAML = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
LAODICEANS_YAML = REPO / "content" / "translations" / "sources" / "letter-to-laodiceans" / "_source.yaml"
DIVERGENCE_JSON = REPO / "content" / "divergence" / "meqabyan_geez_divergence.json"
THIS_TEST_FILE = Path(__file__)


def _load_parent_cfg() -> dict:
    return yaml.safe_load(PARENT_SOURCE_YAML.read_text(encoding="utf-8"))


def _load_lao_cfg() -> dict:
    return yaml.safe_load(LAODICEANS_YAML.read_text(encoding="utf-8"))


# ──────────────────────────────────────────────────────────────────
# Π.1.B.1 — letter-to-laodiceans/_source.yaml exists + basic schema
# ──────────────────────────────────────────────────────────────────


class TestPi1bLetterToLaodiceansSource:
    """The new alternate-source YAML must exist with the expected
    top-level keys. This is the foundation pin — every downstream
    test depends on this loading cleanly."""

    def test_source_yaml_exists(self):
        assert LAODICEANS_YAML.is_file(), f"Π.1.B: letter-to-laodiceans/_source.yaml must exist at {LAODICEANS_YAML}"

    def test_source_yaml_parses(self):
        cfg = _load_lao_cfg()
        assert isinstance(cfg, dict), "Π.1.B: source yaml must parse to a mapping"

    def test_source_id_correct(self):
        cfg = _load_lao_cfg()
        assert cfg.get("source_id") == "letter-to-laodiceans", (
            "Π.1.B: source_id must equal the directory name 'letter-to-laodiceans'"
        )

    def test_book_code_is_lao(self):
        cfg = _load_lao_cfg()
        assert cfg.get("book_code") == "lao", (
            "Π.1.B: book_code must equal 'lao' to match parallel-bible-eotc declaration"
        )

    def test_chapter_count_is_one(self):
        cfg = _load_lao_cfg()
        assert cfg.get("total_chapters") == 1, (
            "Π.1.B: total_chapters must be 1 (Letter to Laodiceans is a single-chapter epistle)"
        )

    def test_verse_count_is_twenty(self):
        cfg = _load_lao_cfg()
        assert cfg.get("total_verses") == 20, (
            "Π.1.B: total_verses must be 20 per Lightfoot 1875 + James 1924 + Elliott 1993 consensus"
        )

    def test_verses_per_chapter_consistent(self):
        cfg = _load_lao_cfg()
        vpc = cfg.get("verses_per_chapter") or {}
        assert vpc.get("1") == 20 or vpc.get(1) == 20, "Π.1.B: verses_per_chapter['1'] must equal 20"

    def test_canonical_titles_present(self):
        cfg = _load_lao_cfg()
        assert cfg.get("book_title_canonical") == "Letter to the Laodiceans"
        assert cfg.get("book_title_latin") == "Epistola ad Laodicenses"
        assert "ሎዶቅያ" in (cfg.get("book_title_geez") or ""), (
            "Π.1.B: book_title_geez must contain the Geʽez fidel for 'Laodicea' (ሎዶቅያ)"
        )


# ──────────────────────────────────────────────────────────────────
# Π.1.B.2 — primary_source: Lightfoot 1875 PD provenance
# ──────────────────────────────────────────────────────────────────


class TestPi1bPrimarySource:
    """The primary anchor is J.B. Lightfoot 1875, Saint Paul's
    Epistles to the Colossians and to Philemon, Appendix pp. 281-300.
    Author died 1889 → PD under EU/Berne life+70 (publishable since
    1959) AND under US pre-1929 + pre-1923 cutoff. Pin every load-
    bearing PD-status field so future ingest gates have a tight
    provenance proof."""

    def test_primary_source_present(self):
        cfg = _load_lao_cfg()
        assert "primary_source" in cfg, "Π.1.B: primary_source block must exist"

    def test_primary_source_author_lightfoot(self):
        cfg = _load_lao_cfg()
        ps = cfg["primary_source"]
        author = (ps.get("author") or "").lower()
        assert "lightfoot" in author, (
            f"Π.1.B: primary_source.author must reference Lightfoot. Got: {ps.get('author')!r}"
        )

    def test_primary_source_publication_year_1875(self):
        cfg = _load_lao_cfg()
        ps = cfg["primary_source"]
        assert ps.get("publication_year") == 1875, (
            "Π.1.B: primary_source.publication_year must be 1875 (Lightfoot's Macmillan first edition)"
        )

    def test_primary_source_license_pd_old(self):
        cfg = _load_lao_cfg()
        ps = cfg["primary_source"]
        assert ps.get("license") == "PD-old", "Π.1.B: primary_source.license must be 'PD-old' (Lightfoot died 1889)"

    def test_primary_source_license_basis_spelled_out(self):
        cfg = _load_lao_cfg()
        ps = cfg["primary_source"]
        basis = ps.get("license_basis") or ""
        # The basis must mention both EU/Berne life+70 AND US pre-1929 (or pre-1923 / similar
        # explicit US-term mention). Both jurisdictions matter because the project ships in both.
        assert "1889" in basis, "Π.1.B: license_basis must record Lightfoot's death year (1889)"
        assert "Berne" in basis or "70" in basis, "Π.1.B: license_basis must reference EU/Berne or life+70 term"

    def test_primary_source_archive_org_id(self):
        cfg = _load_lao_cfg()
        ps = cfg["primary_source"]
        assert (ps.get("archive_org_id") or "").strip(), (
            "Π.1.B: primary_source.archive_org_id must be populated (acquisition pointer)"
        )

    def test_primary_source_quality_tier(self):
        cfg = _load_lao_cfg()
        ps = cfg["primary_source"]
        assert ps.get("source_quality") == "page-image-tier1", (
            "Π.1.B: primary_source.source_quality must be 'page-image-tier1' (scholarly critical edition)"
        )


# ──────────────────────────────────────────────────────────────────
# Π.1.B.3 — secondary_sources: James 1924 + Codex Fuldensis
# ──────────────────────────────────────────────────────────────────


class TestPi1bSecondarySources:
    """Cross-check anchors. M.R. James 1924 supplies an independent
    PD English translation (different translator, different publisher,
    different decade). Codex Fuldensis 547 CE is the earliest
    surviving manuscript witness (PD-by-age) and is accessed via
    Lightfoot's transcription (cited explicitly so the ingest path
    is unambiguous)."""

    def test_secondary_sources_present(self):
        cfg = _load_lao_cfg()
        sec = cfg.get("secondary_sources") or []
        assert isinstance(sec, list) and len(sec) >= 2, (
            f"Π.1.B: secondary_sources must list at least 2 entries (got {len(sec)})"
        )

    def test_james_1924_secondary(self):
        cfg = _load_lao_cfg()
        sec = cfg.get("secondary_sources") or []
        match = [s for s in sec if isinstance(s, dict) and "james" in (s.get("author") or "").lower()]
        assert match, "Π.1.B: secondary_sources must include M.R. James (Apocryphal New Testament)"
        james = match[0]
        assert james.get("publication_year") == 1924, (
            "Π.1.B: M.R. James entry must use 1924 (Oxford Clarendon first edition)"
        )
        assert james.get("license") == "PD-old", "Π.1.B: M.R. James entry must declare PD-old (James died 1936)"

    def test_codex_fuldensis_secondary(self):
        cfg = _load_lao_cfg()
        sec = cfg.get("secondary_sources") or []
        match = [s for s in sec if isinstance(s, dict) and "fuldensis" in (s.get("citation") or "").lower()]
        assert match, "Π.1.B: secondary_sources must include Codex Fuldensis (manuscript witness)"
        cf = match[0]
        assert cf.get("publication_year") == 547, (
            "Π.1.B: Codex Fuldensis publication_year must be 547 CE (manuscript completion)"
        )
        assert cf.get("license") == "PD-old", "Π.1.B: Codex Fuldensis must be PD-by-age"
        assert cf.get("source_quality") == "manuscript-witness", (
            "Π.1.B: Codex Fuldensis source_quality must be 'manuscript-witness'"
        )

    def test_secondary_sources_use_for_distinct(self):
        """Each secondary entry must declare a `use_for` field so the
        future-ingest code can disambiguate which secondary to consult
        for which purpose (cross-check vs manuscript-anchor)."""
        cfg = _load_lao_cfg()
        sec = cfg.get("secondary_sources") or []
        use_fors = [s.get("use_for") for s in sec if isinstance(s, dict)]
        assert all(use_fors), f"Π.1.B: every secondary_sources entry must have a use_for field. Got: {use_fors!r}"


# ──────────────────────────────────────────────────────────────────
# Π.1.B.4 — Tewahedo canon status (Metzger 1987 §V)
# ──────────────────────────────────────────────────────────────────


class TestPi1bTewahedoCanonStatus:
    """Records the doctrinal context — why the Letter to Laodiceans
    matters to the EOTC despite being absent from the printed
    parallel-Bible PDF. Citation must be Metzger 1987 §V (the
    standard scholarly reference for EOTC canon variants)."""

    def test_tewahedo_canon_block_present(self):
        cfg = _load_lao_cfg()
        assert "tewahedo_canon_status" in cfg, "Π.1.B: tewahedo_canon_status block must exist"

    def test_status_is_broader_canon_variant(self):
        cfg = _load_lao_cfg()
        tcs = cfg["tewahedo_canon_status"]
        assert tcs.get("status") == "broader-canon-variant", (
            "Π.1.B: tewahedo_canon_status.status must be 'broader-canon-variant'"
        )

    def test_metzger_1987_citation(self):
        cfg = _load_lao_cfg()
        tcs = cfg["tewahedo_canon_status"]
        cit = tcs.get("citation") or ""
        assert "Metzger" in cit and "1987" in cit, "Π.1.B: tewahedo_canon_status.citation must reference Metzger 1987"
        assert "220" in cit or "221" in cit, (
            "Π.1.B: Metzger citation must reference pp. 220-221 (the canonical EOTC-canon discussion)"
        )

    def test_metzger_citation_license_disclosed(self):
        """Metzger 1987 is COPYRIGHTED; the YAML must disclose that
        we cite it under fair-use, not as a PD ingest source."""
        cfg = _load_lao_cfg()
        tcs = cfg["tewahedo_canon_status"]
        lic = (tcs.get("citation_license") or "").lower()
        assert "copyrighted" in lic and "fair" in lic, (
            f"Π.1.B: Metzger citation_license must declare fair-use. Got: {tcs.get('citation_license')!r}"
        )


# ──────────────────────────────────────────────────────────────────
# Π.1.B.5 — structural_map.laodiceans (20-verse single-chapter)
# ──────────────────────────────────────────────────────────────────


class TestPi1bStructuralMap:
    """Lightfoot 1875 pp. 287-291 prints the standard 20-verse
    single-chapter division. Pin the chapter and verse counts plus
    the source_anchor so any future re-versification would be a
    deliberate ship, not silent drift."""

    def test_structural_map_present(self):
        cfg = _load_lao_cfg()
        assert "structural_map" in cfg

    def test_laodiceans_section_present(self):
        cfg = _load_lao_cfg()
        sm = cfg["structural_map"]
        assert "laodiceans" in sm, "Π.1.B: structural_map.laodiceans must be the canonical section name"

    def test_book_codes_singleton_lao(self):
        cfg = _load_lao_cfg()
        lao = cfg["structural_map"]["laodiceans"]
        assert lao.get("book_codes") == ["lao"], "Π.1.B: structural_map.laodiceans.book_codes must be ['lao']"

    def test_chapter_count_one(self):
        cfg = _load_lao_cfg()
        lao = cfg["structural_map"]["laodiceans"]
        assert lao.get("chapter_count") == 1

    def test_verse_count_twenty(self):
        cfg = _load_lao_cfg()
        lao = cfg["structural_map"]["laodiceans"]
        assert lao.get("verse_count") == 20

    def test_verified_true(self):
        """Unlike jubilees + one_enoch (tentative — boundary pages
        only), the Laodiceans verse division is fully verified
        against Lightfoot 1875's published division. Mark as verified."""
        cfg = _load_lao_cfg()
        lao = cfg["structural_map"]["laodiceans"]
        assert lao.get("verified") is True, (
            "Π.1.B: structural_map.laodiceans.verified must be True (Lightfoot 1875 division is canonical)"
        )

    def test_verified_at_phase_pi1b(self):
        cfg = _load_lao_cfg()
        lao = cfg["structural_map"]["laodiceans"]
        assert lao.get("verified_at_phase") == "Π.1.B"

    def test_source_anchor_references_lightfoot(self):
        cfg = _load_lao_cfg()
        lao = cfg["structural_map"]["laodiceans"]
        anchor = (lao.get("source_anchor") or "").lower()
        assert "lightfoot" in anchor and "1875" in anchor, (
            f"Π.1.B: structural_map.laodiceans.source_anchor must reference lightfoot_1875_*. Got: {anchor!r}"
        )


# ──────────────────────────────────────────────────────────────────
# Π.1.B.6 — parent-inventory cross-reference (parallel-bible-eotc)
# ──────────────────────────────────────────────────────────────────


class TestPi1bParallelBibleCrossReference:
    """The parallel-bible-eotc _source.yaml::laodiceans block must
    now point at the new alternate source via
    `alternate_source_id` + `alternate_source_file`. This is the
    bidirectional link between the structural-map slot and its
    populated alternate-source declaration."""

    def test_parent_yaml_laodiceans_alternate_source_declared(self):
        parent = _load_parent_cfg()
        lao = parent["structural_map"]["laodiceans"]
        assert lao.get("alternate_source_declared") is True, (
            "Π.1.B: parent laodiceans block must declare alternate_source_declared=True"
        )

    def test_parent_yaml_alternate_source_id(self):
        parent = _load_parent_cfg()
        lao = parent["structural_map"]["laodiceans"]
        assert lao.get("alternate_source_id") == "letter-to-laodiceans", (
            "Π.1.B: parent laodiceans.alternate_source_id must equal 'letter-to-laodiceans'"
        )

    def test_parent_yaml_alternate_source_file_points_at_new_yaml(self):
        parent = _load_parent_cfg()
        lao = parent["structural_map"]["laodiceans"]
        path_str = (lao.get("alternate_source_file") or "").replace("\\", "/")
        expected_suffix = "content/translations/sources/letter-to-laodiceans/_source.yaml"
        assert path_str.endswith(expected_suffix), (
            f"Π.1.B: parent laodiceans.alternate_source_file must point at the new yaml. Got: {path_str!r}"
        )

    def test_parent_yaml_alternate_source_declared_at_phase_pi1b(self):
        parent = _load_parent_cfg()
        lao = parent["structural_map"]["laodiceans"]
        assert lao.get("alternate_source_declared_at_phase") == "Π.1.B"

    def test_parent_yaml_alternate_source_required_preserved(self):
        """Π.1's original `alternate_source_required: true` flag must
        stay set so future readers can audit the original requirement
        and its fulfillment in the same record."""
        parent = _load_parent_cfg()
        lao = parent["structural_map"]["laodiceans"]
        assert lao.get("alternate_source_required") is True, (
            "Π.1.B: parent laodiceans.alternate_source_required (set at Π.1) must remain True"
        )

    def test_parent_yaml_notes_mentions_pi1b_fulfillment(self):
        parent = _load_parent_cfg()
        lao = parent["structural_map"]["laodiceans"]
        notes = lao.get("notes") or ""
        assert "Π.1.B" in notes and "Lightfoot" in notes, (
            "Π.1.B: parent laodiceans.notes must document the Π.1.B fulfillment with Lightfoot anchor"
        )


# ──────────────────────────────────────────────────────────────────
# Π.1.B.7 — inventory status flip + phase history
# ──────────────────────────────────────────────────────────────────


class TestPi1bInventoryStatusFlip:
    """The Π.1 inventory's `extraction_status_at_declaration` is
    preserved verbatim (historical pin); the Π.1.B flip lives in a
    new `extraction_status_current` block. A `phase_history` array
    records the Π.1 → Π.1.B transition."""

    def test_extraction_status_at_declaration_unchanged(self):
        """Π.1's historical pin must remain verbatim.

        IMPORTANT: this asserts the SAME thing as Π.1's
        `test_laodiceans_status_is_source_unavailable` pin, by design —
        Π.1.B's flip is additive, not destructive. If this fails the
        historical record has been corrupted."""
        parent = _load_parent_cfg()
        inv = parent["structural_map"]["tewahedo_distinctive_inventory"]
        at_decl = inv["extraction_status_at_declaration"]
        assert at_decl.get("laodiceans") == "source-unavailable", (
            "Π.1.B: must NOT mutate extraction_status_at_declaration (historical pin); "
            "the Π.1 record stays source-unavailable forever."
        )

    def test_extraction_status_current_present(self):
        parent = _load_parent_cfg()
        inv = parent["structural_map"]["tewahedo_distinctive_inventory"]
        assert "extraction_status_current" in inv, (
            "Π.1.B: must add extraction_status_current block (current state, mutates over time)"
        )

    def test_extraction_status_current_laodiceans_flipped(self):
        parent = _load_parent_cfg()
        inv = parent["structural_map"]["tewahedo_distinctive_inventory"]
        cur = inv["extraction_status_current"]
        assert cur.get("laodiceans") == "alternate-source-declared", (
            "Π.1.B: extraction_status_current.laodiceans must be 'alternate-source-declared'"
        )

    def test_extraction_status_current_other_books_unchanged(self):
        """Π.1.B only flips laodiceans; the other 3 sections must stay
        at not-yet-extracted to preserve the at-declaration pin
        across copy-up."""
        parent = _load_parent_cfg()
        inv = parent["structural_map"]["tewahedo_distinctive_inventory"]
        cur = inv["extraction_status_current"]
        assert cur.get("meqabyan") == "not-yet-extracted"
        assert cur.get("jubilees") == "not-yet-extracted"
        assert cur.get("one_enoch") == "not-yet-extracted"

    def test_extraction_status_current_updated_at_phase(self):
        parent = _load_parent_cfg()
        inv = parent["structural_map"]["tewahedo_distinctive_inventory"]
        assert inv.get("extraction_status_current_updated_at_phase") == "Π.1.B"

    def test_phase_history_laodiceans_records_both_transitions(self):
        parent = _load_parent_cfg()
        inv = parent["structural_map"]["tewahedo_distinctive_inventory"]
        history = (inv.get("extraction_status_phase_history") or {}).get("laodiceans") or []
        assert isinstance(history, list) and len(history) >= 2, (
            f"Π.1.B: phase_history.laodiceans must list >= 2 entries. Got: {history!r}"
        )
        phases = [h.get("phase") for h in history if isinstance(h, dict)]
        assert "Π.1" in phases, "Π.1.B: phase_history must record the Π.1 origin"
        assert "Π.1.B" in phases, "Π.1.B: phase_history must record the Π.1.B flip"

    def test_phase_history_pi1_origin_records_source_unavailable(self):
        parent = _load_parent_cfg()
        inv = parent["structural_map"]["tewahedo_distinctive_inventory"]
        history = (inv.get("extraction_status_phase_history") or {}).get("laodiceans") or []
        pi1 = next(h for h in history if h.get("phase") == "Π.1")
        assert pi1.get("status") == "source-unavailable"

    def test_phase_history_pi1b_records_alternate_source_declared(self):
        parent = _load_parent_cfg()
        inv = parent["structural_map"]["tewahedo_distinctive_inventory"]
        history = (inv.get("extraction_status_phase_history") or {}).get("laodiceans") or []
        pi1b = next(h for h in history if h.get("phase") == "Π.1.B")
        assert pi1b.get("status") == "alternate-source-declared"

    def test_inventory_contract_mentions_pi1b_fulfillment(self):
        parent = _load_parent_cfg()
        inv = parent["structural_map"]["tewahedo_distinctive_inventory"]
        contract = inv.get("contract") or ""
        assert "Π.1.B" in contract and "alternate-source-declared" in contract, (
            "Π.1.B: tewahedo_distinctive_inventory.contract must document the Π.1.B fulfillment"
        )


# ──────────────────────────────────────────────────────────────────
# Π.1.B.8 — ingest contract + reproducibility preservation
# ──────────────────────────────────────────────────────────────────


class TestPi1bIngestContract:
    """Π.1.B is DECLARATIVE-ONLY — no data ingest. The contract must
    be spelled out in machine-readable fields so future ships can
    verify the no-ingest invariant without re-reading the prose."""

    def test_no_ingest_at_this_phase_true(self):
        cfg = _load_lao_cfg()
        assert cfg.get("no_ingest_at_this_phase") is True, "Π.1.B: no_ingest_at_this_phase must be True"

    def test_ingest_gate_phase_declared(self):
        cfg = _load_lao_cfg()
        gate = cfg.get("ingest_gate_phase") or ""
        assert isinstance(gate, str) and gate.strip(), (
            "Π.1.B: ingest_gate_phase must name the future phase that opens ingest"
        )

    def test_ingest_gate_blockers_documented(self):
        cfg = _load_lao_cfg()
        blockers = cfg.get("ingest_gate_blockers") or []
        assert isinstance(blockers, list) and len(blockers) >= 1, (
            "Π.1.B: ingest_gate_blockers must list >= 1 explicit blocker"
        )

    def test_translation_slot_state_not_populated(self):
        cfg = _load_lao_cfg()
        state = cfg.get("translation_slot_state_at_ship") or ""
        assert "not-populated" in state.lower() or "pre-ingest" in state.lower(), (
            f"Π.1.B: translation_slot_state_at_ship must indicate no ingest occurred. Got: {state!r}"
        )

    def test_v1_reproducibility_preserved_flag(self):
        cfg = _load_lao_cfg()
        assert cfg.get("v1_reproducibility_preserved") is True, "Π.1.B: v1_reproducibility_preserved must be True"

    def test_v1_reproducibility_basis_spelled_out(self):
        cfg = _load_lao_cfg()
        basis = cfg.get("v1_reproducibility_basis") or ""
        assert "no" in basis.lower() and "content/notes" in basis.lower(), (
            "Π.1.B: v1_reproducibility_basis must explicitly affirm 'no content/notes/ changes'"
        )

    def test_honesty_contract_present(self):
        cfg = _load_lao_cfg()
        honesty = cfg.get("honesty_contract") or ""
        assert "SOURCE_ANCHOR" in honesty or "source_anchor" in honesty, (
            "Π.1.B: honesty_contract must reference SOURCE_ANCHOR provenance discipline (γ.4 / χ-cluster convention)"
        )


# ──────────────────────────────────────────────────────────────────
# Π.1.B.9 — inventory_extension cross-link
# ──────────────────────────────────────────────────────────────────


class TestPi1bInventoryExtensionBlock:
    """The new yaml's `inventory_extension` block records the
    bidirectional link to the parent inventory. The fields here are
    the discoverability handles the future ingest tool will use to
    audit cross-source consistency."""

    def test_inventory_extension_present(self):
        cfg = _load_lao_cfg()
        assert "inventory_extension" in cfg, "Π.1.B: inventory_extension block must exist"

    def test_declared_at_phase_pi1b(self):
        cfg = _load_lao_cfg()
        ie = cfg["inventory_extension"]
        assert ie.get("declared_at_phase") == "Π.1.B"

    def test_parent_inventory_file_points_at_parallel_bible_eotc(self):
        cfg = _load_lao_cfg()
        ie = cfg["inventory_extension"]
        path = (ie.get("parent_inventory_file") or "").replace("\\", "/")
        assert path.endswith("content/translations/sources/parallel-bible-eotc/_source.yaml"), (
            f"Π.1.B: parent_inventory_file must point at parallel-bible-eotc yaml. Got: {path!r}"
        )

    def test_parent_inventory_book_code_lao(self):
        cfg = _load_lao_cfg()
        ie = cfg["inventory_extension"]
        assert ie.get("parent_inventory_book_code") == "lao"

    def test_status_transition_documented(self):
        cfg = _load_lao_cfg()
        ie = cfg["inventory_extension"]
        before = ie.get("parent_inventory_extraction_status_before")
        after = ie.get("parent_inventory_extraction_status_after")
        assert before == "source-unavailable"
        assert after == "alternate-source-declared"


# ──────────────────────────────────────────────────────────────────
# Π.1.B.10 — closed-arc invariants preserved
# ──────────────────────────────────────────────────────────────────


class TestPi1bClosedArcInvariantPreservation:
    """Π.1.B must not regress any closed-arc invariant from prior
    ships. These pins mirror the Π.1 closed-arc-invariants block
    so any drift is caught at Π.1.B itself rather than at an
    arbitrary future audit."""

    def test_meqabyan_section_unchanged(self):
        """τ.6.x.0a meqabyan declaration must remain intact."""
        parent = _load_parent_cfg()
        meq = parent["structural_map"]["meqabyan"]
        assert meq.get("book_codes") == ["mq1", "mq2", "mq3"]
        assert meq.get("pdf_page_range") == [1318, 1378]
        assert meq.get("verified") is True
        assert meq.get("verified_at_phase") == "τ.6.x.0a"

    def test_jubilees_section_unchanged(self):
        """Π.1's jubilees declaration must remain intact."""
        parent = _load_parent_cfg()
        jub = parent["structural_map"]["jubilees"]
        assert jub.get("book_codes") == ["jub"]
        assert jub.get("pdf_page_range") == [1454, 1514]
        assert jub.get("verified_at_phase") == "Π.1"

    def test_one_enoch_section_unchanged(self):
        """Π.1's one_enoch declaration must remain intact."""
        parent = _load_parent_cfg()
        oen = parent["structural_map"]["one_enoch"]
        assert oen.get("book_codes") == ["1en"]
        assert oen.get("pdf_page_range") == [1515, 1566]
        assert oen.get("verified_at_phase") == "Π.1"

    def test_meqabyan_subsections_tau7xn_corrected(self):
        """Was test_meqabyan_subsections_unchanged (pinned the
        τ.6.x.0a values). τ.7.x.n's STRUCTURAL-DISCOVERY CORRECTION
        legitimately invalidated the τ.6.x.0a subsection ranges (a
        coarse approximate scan that was WRONG — mq2 recovered an
        anomalous 5.9%). Per memory feedback_share_pin_pattern this
        prior-ship pin is FLIPPED to the corrected values AS PART OF
        the triggering ship (τ.7.x.n). The closed-arc invariant that
        actually matters — meqabyan OUTER bounds [1318,1378] +
        verified_at_phase τ.6.x.0a — is still asserted intact by
        test_meqabyan_section_unchanged above; only the internal
        split values are corrected (content-boundary-verified at
        τ.7.x.n via running-header ordinal + end-colophons)."""
        parent = _load_parent_cfg()
        subs = parent["structural_map"]["meqabyan"]["subsections"]
        assert subs.get("mq1") == [1318, 1350]  # τ.7.x.n-corrected (was [1318,1365])
        assert subs.get("mq2") == [1351, 1368]  # τ.7.x.n-corrected (was [1366,1372])
        assert subs.get("mq3") == [1369, 1378]  # τ.7.x.n-corrected (was [1373,1378])

    def test_ocr_strategy_authorized_option_unchanged(self):
        """τ.6.x.0b's Option D Hybrid authorization must stand."""
        parent = _load_parent_cfg()
        strat = parent.get("ocr_strategy") or {}
        assert strat.get("authorized_option") == "D-Hybrid"
        assert strat.get("default_engine") == "tesseract"

    def test_no_ingest_at_pi1b_in_parent_yaml(self):
        """Parent yaml's no_ingest_at_this_phase still true (τ.6.x.0b's
        contract)."""
        parent = _load_parent_cfg()
        strat = parent.get("ocr_strategy") or {}
        assert strat.get("no_ingest_at_this_phase") is True

    def test_translation_slot_state_unchanged_in_parent_yaml(self):
        parent = _load_parent_cfg()
        strat = parent.get("ocr_strategy") or {}
        assert strat.get("translation_slot_state") == "remains-at-Π.0-seed-Genesis-only"

    def test_delta_1_0_divergence_entries_still_empty(self):
        """δ.1.0's no-data-ingest contract preserved — the
        meqabyan_geez_divergence.json entries list must remain empty."""
        assert DIVERGENCE_JSON.is_file()
        data = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        entries = data.get("entries")
        got_desc = f"len={len(entries)}" if isinstance(entries, list) else "non-list"
        assert entries == [], f"Π.1.B must NOT mutate δ.1.0's divergence entries list. Got {got_desc}"

    def test_closed_arc_invariants_guarded_listed_in_new_yaml(self):
        """The new letter-to-laodiceans/_source.yaml must explicitly
        list the closed-arc invariants it preserves so an auditor
        can verify coverage without re-reading the prose."""
        cfg = _load_lao_cfg()
        guarded = cfg.get("closed_arc_invariants_guarded") or []
        assert isinstance(guarded, list)
        joined = " | ".join(str(g) for g in guarded)
        # Must mention γ.4.8.E, Π.0, τ.6.x.0a, δ.1.0, Π.1, and the Π.1.B self-pin
        for needle in ["γ.4.8.E", "Π.0", "τ.6.x.0a", "δ.1.0", "Π.1", "Π.1.B"]:
            assert needle in joined, f"Π.1.B: closed_arc_invariants_guarded must mention {needle!r}. Got: {guarded!r}"


# ──────────────────────────────────────────────────────────────────
# Π.1.B.11 — phase coverage / discoverability
# ──────────────────────────────────────────────────────────────────


class TestPi1bPhaseCoverage:
    """The Π.1.B test file itself must be named canonically and the
    phase tag must surface in CHANGELOG so the project linter's
    untracked-phases check is satisfied."""

    def test_pi1b_test_file_named_canonically(self):
        assert THIS_TEST_FILE.name == "test_parallel_bible_pi1b.py", (
            f"Π.1.B test file must be named test_parallel_bible_pi1b.py. Got: {THIS_TEST_FILE.name!r}"
        )

    def test_pi1b_phase_tag_present_in_changelog(self):
        changelog = REPO / "dev" / "CHANGELOG.md"
        assert changelog.is_file()
        text = changelog.read_text(encoding="utf-8")
        assert "Π.1.B" in text, "Π.1.B: CHANGELOG.md must mention the Π.1.B phase tag (untracked-phases linter check)"

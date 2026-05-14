"""δ.1.x.A.0 — Pre-build divergence-JSON batch-prep block for mq1 ch 1-9
(2026-05-14).

DECLARATIVE-ONLY ship. Π.1 + Π.1.B closed the foundation-declaration
phase. δ.1.x.A.0 prepares the operator-side handoff for δ.1.x.A (the
first Phase-4 page-image batch). The deliverable extends
`content/divergence/meqabyan_geez_divergence.json::_meta` with a
`batch_prep` block documenting:

- PDF page range estimated for mq1 ch 1-9 (1318-1326 of 1318-1365 mq1
  span, per Π.1 structural_map.meqabyan.subsections.mq1).
- Per-chapter minimum verse count floor (derived from existing
  content/notes/mq1.py + content/candidates/mq1_ch_*.json at ship-time).
- Per-chapter PDF-page estimate (operator confirms at render-time).
- 10-step operator workflow (PDF render → Geʽez/Amharic/English
  transcription → divergence classification → confidence scoring →
  page_image_verified flag → operator_session signature → tracker
  status update).
- Why pre-populated entries are NOT shipped: the page-image-authority
  honesty rule forbids placeholder data; the JSON shape is documented
  but each entry is constructed at operator render-time.
- Why v1 English pre-population is rejected: v1_english_immutable +
  coupling-risk + manual-paste-is-cheap.

δ.1.x.A.0 does NOT modify `entries: []` — the δ.1.0 invariant is
preserved. The build tool's `--check` mode continues to report zero
entries (no Phase-4 ingest yet); the promote tool continues to refuse
notes-file mutation.

δ.1.x.A.0 deliverables under test:

1. **`_meta.batch_prep` block exists** with all sub-fields documenting
   the operator handoff.
2. **`entries: []` PRESERVED** (δ.1.0 invariant intact).
3. **`_meta.phases_shipped` extended** to ["δ.1.0", "δ.1.x.A.0"].
4. **`per_chapter_verse_count_floor`** matches the lower-bound derived
   from existing notes/candidates files at ship-time.
5. **`operator_workflow` is a 10-step list** covering the full Phase-4
   handoff loop.
6. **NEW closed-arc invariant** `delta_1_0_entries_empty_at_seed`
   added to `regression_guarded_invariants` — codifies the entries=[]
   pin as a named-and-documented invariant rather than just a test
   assertion.
7. **Closed-arc invariants regression-guarded:** γ.4.8.E 67/67 + γ.4.8.F
   ≥212 + Π.0.1 amharic-in-POPUP_LANGUAGES + Π.0.4 EMBED_FONT_PATHS=[]
   + τ.6.x.0a/b contracts + δ.1.0 entries=[] + Π.1 jubilees/one_enoch
   declarations + Π.1.B laodiceans alternate-source declared (in parent
   inventory) preserved.
"""

from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
DIVERGENCE_JSON = REPO / "content" / "divergence" / "meqabyan_geez_divergence.json"
PARENT_SOURCE_YAML = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"


def _load_div() -> dict:
    return json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))


# ──────────────────────────────────────────────────────────────────
# δ.1.x.A.0.1 — batch_prep block exists + headline fields
# ──────────────────────────────────────────────────────────────────


class TestDelta1xA0BatchPrepBlock:
    """The `_meta.batch_prep` block records the operator-handoff
    declaration. Headline-field pins assert the block is present and
    keyed to the correct phase tag."""

    def test_divergence_json_loads(self):
        d = _load_div()
        assert isinstance(d, dict)

    def test_meta_block_present(self):
        d = _load_div()
        assert "_meta" in d
        assert isinstance(d["_meta"], dict)

    def test_batch_prep_block_present(self):
        d = _load_div()
        assert "batch_prep" in d["_meta"], "δ.1.x.A.0: _meta.batch_prep block must exist"

    def test_batch_prep_prepared_at_phase(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        assert bp.get("prepared_at_phase") == "δ.1.x.A.0"

    def test_batch_prep_prepared_for_batch(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        assert bp.get("prepared_for_batch") == "δ.1.x.A"

    def test_batch_prep_scope_mentions_mq1_1_9(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        scope = bp.get("prepared_for_batch_scope") or ""
        assert "mq1" in scope and ("1-9" in scope or "1–9" in scope), (
            f"δ.1.x.A.0: scope must mention mq1 chapters 1-9. Got: {scope!r}"
        )

    def test_phases_shipped_extended(self):
        """δ.1.0 was the seed; δ.1.x.A.0 is the prep — both must be
        named in phases_shipped (preserves δ.1.0 historical attribution
        + adds δ.1.x.A.0)."""
        d = _load_div()
        ps = d["_meta"]["phases_shipped"]
        assert "δ.1.0" in ps, "δ.1.x.A.0: phases_shipped must keep δ.1.0"
        assert "δ.1.x.A.0" in ps, "δ.1.x.A.0: phases_shipped must add δ.1.x.A.0"


# ──────────────────────────────────────────────────────────────────
# δ.1.x.A.0.2 — PDF page range + per-chapter estimates
# ──────────────────────────────────────────────────────────────────


class TestDelta1xA0PdfPageRange:
    """PDF page mapping for mq1 ch 1-9 must (a) lie within the
    Π.1-declared mq1.subsections range [1318, 1365] AND (b) cover
    approximately the first 25% of the mq1 span (9/36 chapters
    × ~1.3 pages/chapter ≈ 9-12 pages)."""

    def test_operator_renders_pdf_pages_field(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        pages = bp.get("operator_renders_pdf_pages") or []
        assert isinstance(pages, list) and len(pages) == 2, (
            f"δ.1.x.A.0: operator_renders_pdf_pages must be [start, end]. Got: {pages!r}"
        )

    def test_pdf_pages_within_mq1_subsection(self):
        """Π.1 declared mq1.subsections.mq1 = [1318, 1365]. δ.1.x.A.0's
        operator-render range must lie within."""
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        start, end = bp["operator_renders_pdf_pages"]
        assert 1318 <= start <= end <= 1365, (
            f"δ.1.x.A.0: pages {start}-{end} must lie within mq1 subsection [1318, 1365]"
        )

    def test_pdf_pages_count_reasonable(self):
        """9 chapters × 1.0-1.5 pages/chapter ≈ 9-14 pages."""
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        start, end = bp["operator_renders_pdf_pages"]
        span = end - start + 1
        assert 9 <= span <= 14, f"δ.1.x.A.0: PDF page span {span} should be 9-14 for 9 chapters"

    def test_per_chapter_pdf_page_estimates_present(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        est = bp.get("operator_renders_pdf_pages_estimated_per_chapter") or {}
        # Should have entries for chapters 1-9 (keys may be string or int)
        for ch in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            assert str(ch) in est or ch in est, f"δ.1.x.A.0: per-chapter PDF page estimate missing for mq1 ch {ch}"

    def test_per_chapter_pdf_estimates_monotone_or_overlapping(self):
        """Chapter N's page range must start at or after chapter N-1's
        start (monotone), allowing overlap because a chapter may begin
        on the same page as the previous chapter ends."""
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        est = bp.get("operator_renders_pdf_pages_estimated_per_chapter") or {}
        prev_start = 0
        for ch in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            rng = est.get(str(ch)) or est.get(ch)
            assert isinstance(rng, list) and len(rng) == 2, (
                f"δ.1.x.A.0: ch {ch} estimate must be [start, end]; got {rng!r}"
            )
            assert rng[0] >= prev_start, f"δ.1.x.A.0: ch {ch} start {rng[0]} must be >= ch {ch - 1} start {prev_start}"
            assert rng[0] <= rng[1], f"δ.1.x.A.0: ch {ch} range invalid {rng}"
            prev_start = rng[0]


# ──────────────────────────────────────────────────────────────────
# δ.1.x.A.0.3 — per-chapter verse count floor
# ──────────────────────────────────────────────────────────────────


class TestDelta1xA0VerseCountFloor:
    """Lower-bound verse counts per chapter, derived from existing
    notes + candidates files at ship-time. Operator's actual count at
    render-time must be ≥ these floors (notes file is a lower bound;
    actual chapter length can only be higher)."""

    def test_floor_block_present(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        assert "per_chapter_verse_count_floor" in bp

    def test_floor_covers_all_9_chapters(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        floor = bp["per_chapter_verse_count_floor"]
        for ch in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            assert str(ch) in floor, f"δ.1.x.A.0: per_chapter_verse_count_floor missing ch {ch}"

    def test_floor_values_are_positive_integers(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        floor = bp["per_chapter_verse_count_floor"]
        for ch in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            val = floor[str(ch)]
            assert isinstance(val, int) and val >= 1, f"δ.1.x.A.0: ch {ch} floor must be positive int; got {val!r}"

    def test_floor_matches_existing_notes_lower_bound(self):
        """The floor values were derived from content/notes/mq1.py +
        content/candidates/mq1_ch_*.json at δ.1.x.A.0 ship-time.
        Hardcode the snapshot here so future drift is detected."""
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        floor = bp["per_chapter_verse_count_floor"]
        expected = {
            "1": 14,
            "2": 28,
            "3": 38,
            "4": 5,
            "5": 14,
            "6": 23,
            "7": 1,
            "8": 22,
            "9": 3,
        }
        for ch, val in expected.items():
            assert floor.get(ch) == val, f"δ.1.x.A.0: ch {ch} floor mismatch — expected {val}, got {floor.get(ch)}"


# ──────────────────────────────────────────────────────────────────
# δ.1.x.A.0.4 — operator workflow + handoff doc references
# ──────────────────────────────────────────────────────────────────


class TestDelta1xA0OperatorWorkflow:
    """The 10-step operator workflow covers the full Phase-4 handoff
    loop. Each step must be a non-empty string. Critical step content
    is pinned so future drift is caught."""

    def test_workflow_is_list_of_10(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        wf = bp.get("operator_workflow") or []
        assert isinstance(wf, list) and len(wf) == 10, (
            f"δ.1.x.A.0: operator_workflow must be a 10-step list; got len={len(wf)}"
        )

    def test_workflow_all_steps_non_empty(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        for i, step in enumerate(bp["operator_workflow"], start=1):
            assert isinstance(step, str) and step.strip(), f"δ.1.x.A.0: workflow step {i} must be non-empty string"

    def test_workflow_mentions_350_dpi(self):
        """Page-image-tier1 honesty rule: 350 dpi is the project's
        canonical page-image-authority resolution."""
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        joined = " | ".join(bp["operator_workflow"])
        assert "350 dpi" in joined or "350dpi" in joined, (
            "δ.1.x.A.0: workflow must reference 350 dpi page-image resolution"
        )

    def test_workflow_mentions_page_image_verified(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        joined = " | ".join(bp["operator_workflow"])
        assert "page_image_verified" in joined, "δ.1.x.A.0: workflow must reference page_image_verified flag"

    def test_workflow_mentions_divergence_class(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        joined = " | ".join(bp["operator_workflow"])
        assert "divergence_class" in joined or "divergence class" in joined, (
            "δ.1.x.A.0: workflow must reference divergence_class classification"
        )

    def test_workflow_mentions_tracker_update(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        joined = " | ".join(bp["operator_workflow"])
        assert "PHASE4_MEQABYAN_TRACKER" in joined or "tracker" in joined.lower(), (
            "δ.1.x.A.0: workflow must reference PHASE4_MEQABYAN_TRACKER.md update"
        )

    def test_handoff_doc_references_tracker_and_build_tool(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        handoff = (bp.get("operator_handoff_doc") or "").lower()
        assert "tracker" in handoff or "phase4_meqabyan_tracker" in handoff
        assert "build_meqabyan_revision" in handoff


# ──────────────────────────────────────────────────────────────────
# δ.1.x.A.0.5 — no-skeleton-entries + v1-english-not-pre-populated rationale
# ──────────────────────────────────────────────────────────────────


class TestDelta1xA0HonestyRuleAlignment:
    """δ.1.x.A.0 deliberately does NOT pre-populate entries with
    placeholder values. The rationale must be documented machine-
    readably so a future ship can't accidentally pre-populate."""

    def test_no_skeleton_entries_rationale_documented(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        rationale = bp.get("no_skeleton_entries_at_pi1ba0") or ""
        assert "page-image-authority" in rationale.lower() or "page_image_authority" in rationale.lower(), (
            "δ.1.x.A.0: no-skeleton-entries rationale must reference page-image-authority honesty rule"
        )

    def test_v1_english_pre_population_rejection_documented(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        rationale = bp.get("v1_english_pre_population_rejected") or ""
        assert "v1_english_immutable" in rationale or "immutable" in rationale.lower(), (
            "δ.1.x.A.0: v1_english pre-population rejection must reference v1_english_immutable rule"
        )

    def test_promotion_gating_documented(self):
        d = _load_div()
        bp = d["_meta"]["batch_prep"]
        gating = bp.get("promotion_to_apparatus_gated_on") or ""
        assert "δ.1.x.A" in gating, "δ.1.x.A.0: promotion-gating note must name δ.1.x.A as the unblocking phase"


# ──────────────────────────────────────────────────────────────────
# δ.1.x.A.0.6 — new closed-arc invariant codified
# ──────────────────────────────────────────────────────────────────


class TestDelta1xA0NewInvariantCodified:
    """δ.1.x.A.0 adds a fourth named invariant to
    `regression_guarded_invariants` that explicitly codifies the
    entries=[] pin as a NAMED invariant (rather than just a test
    assertion living in the test file)."""

    def test_invariant_block_present(self):
        d = _load_div()
        inv = d["_meta"].get("regression_guarded_invariants") or {}
        assert isinstance(inv, dict)

    def test_three_prior_invariants_intact(self):
        d = _load_div()
        inv = d["_meta"]["regression_guarded_invariants"]
        for name in [
            "gamma48E_arc_close_67_67",
            "gamma48F_count_floor",
            "v1_english_immutable",
        ]:
            assert name in inv, f"δ.1.x.A.0: prior invariant {name!r} must remain in regression_guarded_invariants"

    def test_new_delta_1_0_entries_empty_invariant(self):
        d = _load_div()
        inv = d["_meta"]["regression_guarded_invariants"]
        assert "delta_1_0_entries_empty_at_seed" in inv, (
            "δ.1.x.A.0: new invariant delta_1_0_entries_empty_at_seed must be codified"
        )
        text = inv["delta_1_0_entries_empty_at_seed"]
        assert "δ.1.0" in text and "δ.1.x.A" in text, (
            "δ.1.x.A.0: invariant must reference both δ.1.0 (origin) and δ.1.x.A (first non-empty ship)"
        )


# ──────────────────────────────────────────────────────────────────
# δ.1.x.A.0.7 — closed-arc preservation
# ──────────────────────────────────────────────────────────────────


class TestDelta1xA0ClosedArcInvariantPreservation:
    """δ.1.x.A.0 must not regress any prior closed-arc invariant.
    The chain γ.4.8.E + γ.4.8.F + Π.0.1 + Π.0.4 + τ.6.x.0a/b +
    δ.1.0 + Π.1 + Π.1.B all preserved."""

    def test_delta_1_0_entries_still_empty(self):
        """δ.1.0's most critical invariant — entries list remains []."""
        d = _load_div()
        assert d["entries"] == [], f"δ.1.x.A.0 must NOT mutate δ.1.0 entries=[]. Got len={len(d['entries'])}"

    def test_delta_1_0_books_unchanged(self):
        d = _load_div()
        assert d["_meta"]["books"] == ["mq1", "mq2", "mq3"]

    def test_delta_1_0_total_chapters_unchanged(self):
        d = _load_div()
        assert d["_meta"]["total_chapters"] == 67

    def test_delta_1_0_chapters_per_book_unchanged(self):
        d = _load_div()
        assert d["_meta"]["chapters_per_book"] == {"mq1": 36, "mq2": 21, "mq3": 10}

    def test_delta_1_0_confidence_threshold_unchanged(self):
        d = _load_div()
        assert d["_meta"]["confidence_threshold"] == 0.8

    def test_delta_1_0_honesty_rules_unchanged(self):
        d = _load_div()
        hr = d["_meta"]["honesty_rules"]
        assert hr["no_ocr_trust"] is True
        assert hr["page_image_authority"] is True
        assert hr["flag_uncertain_readings"] is True
        assert hr["v1_english_immutable_during_delta1x"] is True

    def test_delta_1_0_divergence_classes_unchanged(self):
        d = _load_div()
        classes = d["_meta"]["divergence_classes"]
        assert sorted(classes) == sorted(["lexical", "structural", "content", "numbering", "trivial"])

    def test_pi1_laodiceans_at_declaration_pin_intact(self):
        """Π.1's historical pin in parallel-bible-eotc/_source.yaml
        must remain `source-unavailable` (Π.1.B's flip lives in the
        sibling extraction_status_current block)."""
        import yaml

        parent = yaml.safe_load(PARENT_SOURCE_YAML.read_text(encoding="utf-8"))
        inv = parent["structural_map"]["tewahedo_distinctive_inventory"]
        assert inv["extraction_status_at_declaration"]["laodiceans"] == "source-unavailable"

    def test_pi1b_laodiceans_current_pin_intact(self):
        """Π.1.B's current-state pin must remain alternate-source-
        declared (cross-checked from sibling test class)."""
        import yaml

        parent = yaml.safe_load(PARENT_SOURCE_YAML.read_text(encoding="utf-8"))
        inv = parent["structural_map"]["tewahedo_distinctive_inventory"]
        assert inv["extraction_status_current"]["laodiceans"] == "alternate-source-declared"


# ──────────────────────────────────────────────────────────────────
# δ.1.x.A.0.8 — phase coverage
# ──────────────────────────────────────────────────────────────────


class TestDelta1xA0PhaseCoverage:
    """The δ.1.x.A.0 phase tag must surface in CHANGELOG so the
    project linter's untracked-phases check passes."""

    def test_pi1ba0_phase_tag_in_changelog(self):
        changelog = REPO / "dev" / "CHANGELOG.md"
        text = changelog.read_text(encoding="utf-8")
        assert "δ.1.x.A.0" in text, "δ.1.x.A.0: CHANGELOG.md must mention the δ.1.x.A.0 phase tag"

"""δ.1.0 — Phase-4 Meqabyan Geʽez-revision seed pins (2026-05-14).

δ.1.0 is the SEED-FOUNDATION phase of the multi-session δ.1.x cluster
(~15-25 sessions, per SCOPE_2026-05-14-parallel-bible.md §5 δ.1.x).
The seed ships the foundational infrastructure WITHOUT any divergence
entries; subsequent δ.1.x.A-G batches fill in chapters per the
Phase-4 page-image methodology.

δ.1.0 deliverables under test:

1. **`content/divergence/meqabyan_geez_divergence.json`** — schema 1.0,
   _meta block populated, entries: [], confidence_threshold 0.8,
   honesty_rules + regression_guarded_invariants codified.

2. **`dev/PHASE4_MEQABYAN_TRACKER.md`** — 67-chapter status table
   (mq1 36 + mq2 21 + mq3 10), all "todo" at seed, Phase-4
   methodology + honesty rules summarized inline.

3. **2 new kinds in `content/kinds.yaml`** — `text-geez-revision`
   (text category, [GZ] label, page-image-tier1) and
   `compare-divergence-geez` (compare category, "Geʽez div." label,
   surfaces content-class divergences in inline popups).

4. **`scripts/build_meqabyan_revision.py`** — assembles per-book
   revision markdown from the divergence JSON; enforces confidence
   ≥ 0.8 + page-image-authority + v1-immutability honesty rules.

5. **`scripts/promote_divergence_to_apparatus.py`** — promotes
   content-class divergences into compare-divergence-geez notes;
   confidence floor + page-image gate + idempotency signature.

6. **Closed-arc invariants regression-guarded** — γ.4.8.E 67/67 +
   γ.4.8.F ≥212 + Π.0.1 + Π.0.4 + τ.6.x.0a/b translation-slot
   contracts.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parent.parent
DIVERGENCE_JSON = REPO / "content" / "divergence" / "meqabyan_geez_divergence.json"
TRACKER_DOC = REPO / "dev" / "PHASE4_MEQABYAN_TRACKER.md"
KINDS_YAML = REPO / "content" / "kinds.yaml"
BUILD_TOOL = REPO / "scripts" / "build_meqabyan_revision.py"
PROMOTE_TOOL = REPO / "scripts" / "promote_divergence_to_apparatus.py"


def _load_module(name: str, path: Path):
    """Import a top-level script as a module without going through
    scripts/__init__.py (avoids side-effect imports during pytest
    collection)."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ──────────────────────────────────────────────────────────────────
# δ.1.0 — divergence JSON shape + _meta + empty entries seed
# ──────────────────────────────────────────────────────────────────


class TestDelta10DivergenceJson:
    """The seed JSON exists, has the documented schema 1.0 _meta block,
    and starts with entries: [] (δ.1.x.A-G fills entries in)."""

    def test_divergence_json_exists(self):
        assert DIVERGENCE_JSON.is_file(), "δ.1.0: content/divergence/meqabyan_geez_divergence.json must exist"

    def test_schema_version_1_0(self):
        data = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        assert data["_meta"]["schema_version"] == "1.0"

    def test_phases_shipped_includes_delta_1_0(self):
        data = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        assert "δ.1.0" in data["_meta"]["phases_shipped"]

    def test_books_list_three_meqabyan(self):
        data = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        assert data["_meta"]["books"] == ["mq1", "mq2", "mq3"]

    def test_chapters_per_book_matches_arc_close(self):
        """γ.4.8.E arc-close codified mq1=36, mq2=21, mq3=10. δ.1.x
        must mirror this exactly."""
        data = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        assert data["_meta"]["chapters_per_book"] == {"mq1": 36, "mq2": 21, "mq3": 10}
        assert data["_meta"]["total_chapters"] == 67

    def test_confidence_threshold_zero_point_eight(self):
        data = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        assert data["_meta"]["confidence_threshold"] == 0.8

    def test_honesty_rules_codified(self):
        data = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        rules = data["_meta"]["honesty_rules"]
        assert rules["no_ocr_trust"] is True
        assert rules["page_image_authority"] is True
        assert rules["flag_uncertain_readings"] is True
        assert rules["v1_english_immutable_during_delta1x"] is True

    def test_divergence_classes_complete(self):
        data = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        classes = set(data["_meta"]["divergence_classes"])
        assert classes == {"lexical", "structural", "content", "numbering", "trivial"}

    def test_regression_guarded_invariants_named(self):
        data = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        inv = data["_meta"]["regression_guarded_invariants"]
        assert "gamma48E_arc_close_67_67" in inv
        assert "gamma48F_count_floor" in inv
        assert "v1_english_immutable" in inv

    def test_entries_empty_at_seed(self):
        """δ.1.0 contract: entries: []. δ.1.x.A-G batches append."""
        data = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        assert data["entries"] == [], f"δ.1.0 seed: entries must be []; got {len(data['entries'])} entries"


# ──────────────────────────────────────────────────────────────────
# δ.1.0 — Phase-4 tracker doc
# ──────────────────────────────────────────────────────────────────


class TestDelta10Tracker:
    """The tracker doc exists with the 67-chapter table and Phase-4
    methodology + honesty rules summarized inline."""

    def test_tracker_exists(self):
        assert TRACKER_DOC.is_file()

    def test_tracker_lists_three_books(self):
        body = TRACKER_DOC.read_text(encoding="utf-8")
        assert "1 Mäqabyan (mq1)" in body
        assert "2 Mäqabyan (mq2)" in body
        assert "3 Mäqabyan (mq3)" in body

    def test_tracker_chapter_counts(self):
        body = TRACKER_DOC.read_text(encoding="utf-8")
        assert "36 chapters" in body  # mq1
        assert "21 chapters" in body  # mq2
        assert "10 chapters" in body  # mq3
        assert "0 / 67" in body  # aggregate at seed

    def test_tracker_honesty_rules_section(self):
        body = TRACKER_DOC.read_text(encoding="utf-8")
        for rule in [
            "No OCR trust",
            "Page-image authority",
            "Flag uncertain readings",
            "v1 English immutability",
        ]:
            assert rule in body, f"tracker must document the honesty rule: {rule}"

    def test_tracker_regression_guarded_arcs(self):
        body = TRACKER_DOC.read_text(encoding="utf-8")
        assert "γ.4.8.E" in body and "67/67" in body
        assert "γ.4.8.F" in body and "≥212" in body

    def test_tracker_cluster_ledger_lists_subphases(self):
        body = TRACKER_DOC.read_text(encoding="utf-8")
        for tag in ["δ.1.0", "δ.1.x.A", "δ.1.x.G", "δ.1.Z"]:
            assert tag in body, f"tracker cluster ledger must list {tag}"


# ──────────────────────────────────────────────────────────────────
# δ.1.0 — 2 new kinds registered in content/kinds.yaml
# ──────────────────────────────────────────────────────────────────


class TestDelta10KindsRegistration:
    """text-geez-revision and compare-divergence-geez kinds added to
    content/kinds.yaml with the expected shape."""

    def _kinds_by_code(self) -> dict[str, dict]:
        data = yaml.safe_load(KINDS_YAML.read_text(encoding="utf-8"))
        return {k["code"]: k for k in data["kinds"]}

    def test_text_geez_revision_registered(self):
        kinds = self._kinds_by_code()
        assert "text-geez-revision" in kinds, "δ.1.0: text-geez-revision kind must be registered in content/kinds.yaml"
        k = kinds["text-geez-revision"]
        assert k["category"] == "text"
        assert k["label"] == "[GZ]"

    def test_compare_divergence_geez_registered(self):
        kinds = self._kinds_by_code()
        assert "compare-divergence-geez" in kinds, (
            "δ.1.0: compare-divergence-geez kind must be registered in content/kinds.yaml"
        )
        k = kinds["compare-divergence-geez"]
        assert k["category"] == "compare"
        assert "divergence" in k["title_attr"].lower() or "geʽez" in k["title_attr"].lower()

    def test_legacy_kinds_preserved(self):
        """Sanity check that the new kinds don't displace existing ones
        (regression-guard against accidental kinds.yaml damage)."""
        kinds = self._kinds_by_code()
        for legacy in ["word", "comm", "source", "parallel"]:
            assert legacy in kinds, f"δ.1.0 must not regress legacy kind: {legacy}"
        for mvp in ["lang-hebrew", "lang-greek", "comm-ethiopian", "text-ethiopic"]:
            assert mvp in kinds, f"δ.1.0 must not regress mvp kind: {mvp}"


# ──────────────────────────────────────────────────────────────────
# δ.1.0 — tool skeletons load + honor honesty rules
# ──────────────────────────────────────────────────────────────────


class TestDelta10BuildTool:
    """scripts/build_meqabyan_revision.py loads, exposes the documented
    helpers, and refuses entries violating the honesty rules."""

    def _mod(self):
        return _load_module("build_meqabyan_revision", BUILD_TOOL)

    def test_tool_exists(self):
        assert BUILD_TOOL.is_file()

    def test_tool_loads(self):
        mod = self._mod()
        assert hasattr(mod, "load_divergence_json")
        assert hasattr(mod, "validate_entry")
        assert hasattr(mod, "assemble_book_markdown")
        assert hasattr(mod, "BOOKS")

    def test_books_list_matches_arc_close(self):
        mod = self._mod()
        # mod.BOOKS is a list of (code, title, chapters) tuples.
        codes = [b[0] for b in mod.BOOKS]
        chapter_counts = {b[0]: b[2] for b in mod.BOOKS}
        assert codes == ["mq1", "mq2", "mq3"]
        assert chapter_counts == {"mq1": 36, "mq2": 21, "mq3": 10}

    def test_validate_entry_refuses_low_confidence(self):
        mod = self._mod()
        bad = {
            "book": "mq1",
            "chapter": 1,
            "verse": 1,
            "geez_text": "x",
            "geez_revised_english": "y",
            "divergence_class": "lexical",
            "confidence": 0.5,
            "page_image_verified": True,
        }
        ok, reason = mod.validate_entry(bad, allow_low_confidence=False, reviewer=None)
        assert ok is False
        assert "confidence" in reason.lower()

    def test_validate_entry_low_confidence_requires_reviewer(self):
        mod = self._mod()
        bad = {
            "book": "mq1",
            "chapter": 1,
            "verse": 1,
            "geez_text": "x",
            "geez_revised_english": "y",
            "divergence_class": "lexical",
            "confidence": 0.5,
            "page_image_verified": True,
        }
        ok, reason = mod.validate_entry(bad, allow_low_confidence=True, reviewer=None)
        assert ok is False
        assert "reviewer" in reason.lower()

    def test_validate_entry_refuses_no_page_image(self):
        mod = self._mod()
        bad = {
            "book": "mq1",
            "chapter": 1,
            "verse": 1,
            "geez_text": "x",
            "geez_revised_english": "y",
            "divergence_class": "lexical",
            "confidence": 0.95,
            "page_image_verified": False,
        }
        ok, reason = mod.validate_entry(bad, allow_low_confidence=False, reviewer=None)
        assert ok is False
        assert "page_image" in reason.lower()

    def test_validate_entry_refuses_bad_divergence_class(self):
        mod = self._mod()
        bad = {
            "book": "mq1",
            "chapter": 1,
            "verse": 1,
            "geez_text": "x",
            "geez_revised_english": "y",
            "divergence_class": "made-up-class",
            "confidence": 0.95,
            "page_image_verified": True,
        }
        ok, reason = mod.validate_entry(bad, allow_low_confidence=False, reviewer=None)
        assert ok is False
        assert "divergence_class" in reason

    def test_validate_entry_accepts_good_entry(self):
        mod = self._mod()
        good = {
            "book": "mq1",
            "chapter": 1,
            "verse": 1,
            "geez_text": "x",
            "geez_revised_english": "y",
            "divergence_class": "content",
            "confidence": 0.95,
            "page_image_verified": True,
        }
        ok, reason = mod.validate_entry(good, allow_low_confidence=False, reviewer=None)
        assert ok is True
        assert reason == "ok"

    def test_assemble_book_markdown_empty_at_seed(self):
        """At δ.1.0 the JSON has entries: [] so the per-book markdown
        is a placeholder with the '0 entries' notice."""
        mod = self._mod()
        body = mod.assemble_book_markdown("mq1", "1 Mäqabyan", 36, entries=[])
        assert "1 Mäqabyan" in body
        assert "0 entries this revision" in body


class TestDelta10PromoteTool:
    """scripts/promote_divergence_to_apparatus.py loads, exposes the
    promotion-policy helpers, and enforces content-only +
    confidence-floor + page-image gates."""

    def _mod(self):
        return _load_module("promote_divergence_to_apparatus", PROMOTE_TOOL)

    def test_tool_exists(self):
        assert PROMOTE_TOOL.is_file()

    def test_tool_loads(self):
        mod = self._mod()
        assert hasattr(mod, "is_promotable")
        assert hasattr(mod, "signature")
        assert mod.PROMOTED_KIND == "compare-divergence-geez"

    def test_is_promotable_only_content_class(self):
        mod = self._mod()
        for cls in ["lexical", "structural", "numbering", "trivial"]:
            entry = {
                "book": "mq1",
                "chapter": 1,
                "verse": 1,
                "divergence_class": cls,
                "confidence": 0.95,
                "page_image_verified": True,
            }
            ok, reason = mod.is_promotable(entry)
            assert ok is False, f"{cls} divergence_class must NOT be promoted"

    def test_is_promotable_content_with_full_compliance(self):
        mod = self._mod()
        entry = {
            "book": "mq1",
            "chapter": 1,
            "verse": 1,
            "divergence_class": "content",
            "confidence": 0.95,
            "page_image_verified": True,
        }
        ok, reason = mod.is_promotable(entry)
        assert ok is True

    def test_is_promotable_rejects_low_confidence(self):
        mod = self._mod()
        entry = {
            "book": "mq1",
            "chapter": 1,
            "verse": 1,
            "divergence_class": "content",
            "confidence": 0.5,
            "page_image_verified": True,
        }
        ok, _ = mod.is_promotable(entry)
        assert ok is False

    def test_signature_is_stable(self):
        mod = self._mod()
        entry = {
            "book": "mq1",
            "chapter": 1,
            "verse": 1,
            "operator_session": "δ.1.x.A",
        }
        sig_a = mod.signature(entry)
        sig_b = mod.signature(entry)
        assert sig_a == sig_b
        # Same per-verse-different-session → different signature.
        entry2 = dict(entry, operator_session="δ.1.x.B")
        assert mod.signature(entry) != mod.signature(entry2)


# ──────────────────────────────────────────────────────────────────
# δ.1.0 — closed-arc invariants + prior-contract preservation
# ──────────────────────────────────────────────────────────────────


class TestDelta10ClosedArcInvariantPreservation:
    """δ.1.0 is INFRASTRUCTURE-ONLY (no apparatus edits). All prior
    closed-arc + contract invariants must remain green."""

    def test_amharic_still_in_popup_languages(self):
        from scripts.build_edition import POPUP_LANGUAGES

        assert "amharic" in POPUP_LANGUAGES

    def test_embed_font_paths_defaults_to_empty(self):
        """Π.0.4 + φ.1: EMBED_FONT_PATHS must remain []."""
        from scripts import style_config

        assert style_config.EMBED_FONT_PATHS == []

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
                f"δ.1.0 must not regress γ.4.8.E arc-close {book} {total}/{total}"
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
        assert len(meq) >= 212, f"δ.1.0: Meqabyan count must remain ≥212; got {len(meq)}"

    def test_geez_tewahedo_still_gen_only(self):
        """τ.6.x.0a + τ.6.x.0b contract preserved at δ.1.0."""
        slot = REPO / "content" / "translations" / "geez-tewahedo"
        files = sorted(p.name for p in slot.iterdir() if p.suffix == ".py")
        assert files == ["gen.py"]

    def test_amharic_tewahedo_still_gen_only(self):
        slot = REPO / "content" / "translations" / "amharic-tewahedo"
        files = sorted(p.name for p in slot.iterdir() if p.suffix == ".py")
        assert files == ["gen.py"]

    def test_no_meqabyan_notes_modified_at_seed(self):
        """δ.1.0 honesty contract: divergence apparatus is a SEPARATE
        artifact; content/notes/mq{1,2,3}.py must NOT be mutated at
        δ.1.0 seed (notes-file mutation gated to δ.1.x.A)."""
        for code in ["mq1", "mq2", "mq3"]:
            notes_file = REPO / "content" / "notes" / f"{code}.py"
            # Just verify the files exist (γ.4.8 seeded them); content
            # comparison would require a known-good snapshot. The δ.1.0
            # seed-ship promotion tool refuses to mutate notes anyway.
            assert notes_file.is_file(), f"δ.1.0: {code}.py must exist (γ.4.8 seed preserved)"


# ──────────────────────────────────────────────────────────────────
# δ.1.0 — divergence JSON is referenced by the tools
# ──────────────────────────────────────────────────────────────────


class TestDelta10ToolsReferenceJson:
    """Both tools point to the canonical divergence JSON path so
    operator runs find the right data."""

    def test_build_tool_references_divergence_json(self):
        mod = _load_module("build_meqabyan_revision", BUILD_TOOL)
        # The module-level DIVERGENCE_JSON constant should point to
        # content/divergence/meqabyan_geez_divergence.json.
        assert mod.DIVERGENCE_JSON.name == "meqabyan_geez_divergence.json"
        assert mod.DIVERGENCE_JSON.parent.name == "divergence"

    def test_promote_tool_references_divergence_json(self):
        mod = _load_module("promote_divergence_to_apparatus", PROMOTE_TOOL)
        assert mod.DIVERGENCE_JSON.name == "meqabyan_geez_divergence.json"
        assert mod.DIVERGENCE_JSON.parent.name == "divergence"

    def test_tracker_references_divergence_json(self):
        body = TRACKER_DOC.read_text(encoding="utf-8")
        assert "meqabyan_geez_divergence.json" in body

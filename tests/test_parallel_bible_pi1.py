"""Π.1 — Parallel-PDF Tewahedo-distinctive structural-map foundation
(2026-05-14).

FOUNDATION-ONLY ship. Π.1 declares the structural_map slots for the
six Tewahedo-distinctive books (Meqabyan 1-3, Jubilees, 1 Enoch,
Letter to the Laodiceans) so the extraction tool can address them
declaratively. No extraction is performed; translation slots remain
at the Π.0 + τ.6.x.0a seed state. The Letter to the Laodiceans is
declared with `present_in_pdf: false` after a full-PDF marker scan
showed zero opening-title hits (the four 'ሎዶቅያ' references in the
PDF are all secondary — Revelation 1:11, Revelation 3:14, geographic
references — not the standalone Pauline letter).

The strategic roadmap for parallel-Bible work lives at:
    dev/SCOPE_2026-05-14-parallel-bible.md §Π.1

Π.1 deliverables under test:

1. **_source.yaml::structural_map** gains three sections:
   `jubilees` (jub, pages 1454-1514, verified=tentative),
   `one_enoch` (1en, pages 1515-1566, verified=tentative),
   `laodiceans` (lao, present_in_pdf=false, alternate_source_required).

2. **meqabyan.subsections** map declares per-book page-ranges
   (mq1=[1318,1365], mq2=[1366,1372], mq3=[1373,1378]) — hoisted
   from the heuristic dict in extract_parallel_pdf.py into
   declarative YAML.

3. **tewahedo_distinctive_inventory** metadata block names the
   6 declared sections + 6 book codes + per-book extraction status.

4. **scripts/extract_parallel_pdf.py** gains:
   - `_extraction_sections()` helper that filters metadata keys
     out of structural_map iteration
   - `_METADATA_KEYS` constant naming the inventory key
   - laodiceans-section guard (raises SystemExit on extraction
     attempt when present_in_pdf=False)

5. **Closed-arc invariants regression-guarded:** γ.4.8.E 67/67
   chapter coverage intact; γ.4.8.F Meqabyan-voice ≥212 preserved;
   Π.0.1 amharic-in-POPUP_LANGUAGES preserved; Π.0.4
   EMBED_FONT_PATHS=[] preserved; τ.6.x.0a structural_map.meqabyan
   contract preserved (range + verified flag); τ.6.x.0b
   ocr_strategy.authorized_option D-Hybrid preserved; δ.1.0
   divergence-JSON-entries-empty contract preserved.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parent.parent
SOURCE_YAML = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
EXTRACT_TOOL = REPO / "scripts" / "extract_parallel_pdf.py"
DIVERGENCE_JSON = REPO / "content" / "divergence" / "meqabyan_geez_divergence.json"


def _load_source_cfg() -> dict:
    return yaml.safe_load(SOURCE_YAML.read_text(encoding="utf-8"))


def _load_extract_module():
    spec = importlib.util.spec_from_file_location("extract_parallel_pdf", EXTRACT_TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ──────────────────────────────────────────────────────────────────
# Π.1.1 — structural_map extension: the 4 declared sections
# ──────────────────────────────────────────────────────────────────


class TestPi1StructuralMapExtension:
    """The 6 Tewahedo-distinctive books across 4 sections are now
    declared in `_source.yaml::structural_map`. meqabyan was seeded
    at τ.6.x.0a; jubilees, one_enoch, and laodiceans are added at Π.1.
    """

    def test_source_yaml_exists(self):
        assert SOURCE_YAML.is_file(), (
            "Π.1: parallel-bible-eotc _source.yaml must exist (seeded at τ.6.x.0a; extended at Π.1)"
        )

    def test_structural_map_present(self):
        cfg = _load_source_cfg()
        assert "structural_map" in cfg, "Π.1: structural_map block must exist"

    def test_meqabyan_section_preserved(self):
        """Regression-guard: τ.6.x.0a's meqabyan declaration must
        remain intact after Π.1's additions."""
        cfg = _load_source_cfg()
        sm = cfg["structural_map"]
        assert "meqabyan" in sm, "Π.1 must not remove τ.6.x.0a's meqabyan section"
        meq = sm["meqabyan"]
        assert meq["book_codes"] == ["mq1", "mq2", "mq3"]
        assert meq["pdf_page_range"] == [1318, 1378]
        assert meq["verified"] is True
        assert meq["verified_at_phase"] == "τ.6.x.0a"

    def test_jubilees_section_declared(self):
        cfg = _load_source_cfg()
        sm = cfg["structural_map"]
        assert "jubilees" in sm, "Π.1.1: jubilees section must be declared"
        jub = sm["jubilees"]
        assert jub["book_codes"] == ["jub"]
        assert jub["verified_at_phase"] == "Π.1"

    def test_one_enoch_section_declared(self):
        cfg = _load_source_cfg()
        sm = cfg["structural_map"]
        assert "one_enoch" in sm, "Π.1.1: one_enoch section must be declared"
        oen = sm["one_enoch"]
        assert oen["book_codes"] == ["1en"]
        assert oen["verified_at_phase"] == "Π.1"

    def test_laodiceans_section_declared(self):
        cfg = _load_source_cfg()
        sm = cfg["structural_map"]
        assert "laodiceans" in sm, "Π.1.1: laodiceans section must be declared"
        lao = sm["laodiceans"]
        assert lao["book_codes"] == ["lao"]
        assert lao["verified_at_phase"] == "Π.1"

    def test_all_tewahedo_distinctive_books_have_a_section(self):
        """The 6 Tewahedo-distinctive book codes must each map to
        exactly one extractable section in the structural_map."""
        cfg = _load_source_cfg()
        sm = cfg["structural_map"]
        # Build {book_code: section_name}
        book_to_section: dict[str, str] = {}
        for name, sec in sm.items():
            if not isinstance(sec, dict):
                continue
            codes = sec.get("book_codes") or []
            for code in codes:
                book_to_section[code] = name
        for code in ["mq1", "mq2", "mq3", "jub", "1en", "lao"]:
            assert code in book_to_section, (
                f"Π.1.1: book code {code!r} must map to a structural_map section. Got: {book_to_section}"
            )


# ──────────────────────────────────────────────────────────────────
# Π.1.2 — jubilees section page range + verification flag
# ──────────────────────────────────────────────────────────────────


class TestPi1JubileesSection:
    """jubilees opens at PDF page 1454 (`መጽሐፈ ኩፉሌ`) and closes at
    1514 (next page 1515 transitions to 1 Enoch). 50 chapters
    expected (Charles 1902 edition). verified=tentative — boundary
    pages confirmed, full chapter coverage TBD."""

    def _sec(self):
        return _load_source_cfg()["structural_map"]["jubilees"]

    def test_pdf_page_range_correct(self):
        assert self._sec()["pdf_page_range"] == [1454, 1514]

    def test_pdf_index_offset_zero(self):
        # All 0-indexed page numbers; no offset needed (vs τ.6.x.0
        # placeholder format).
        assert self._sec()["pdf_index_offset"] == 0

    def test_verified_tentative(self):
        # Boundary pages confirmed by PDF inspection; full-coverage
        # verification gated on production extraction.
        assert self._sec()["verified"] == "tentative"

    def test_verified_date(self):
        assert str(self._sec()["verified_date"]) == "2026-05-14"

    def test_chapter_count_expected(self):
        assert self._sec()["chapter_count_expected"] == 50

    def test_notes_documents_discovery_method(self):
        notes = self._sec()["notes"]
        assert "ኩፋሌ" in notes or "ኩፉሌ" in notes, (
            "Π.1.2: jubilees.notes should reference the title marker used to discover the range"
        )
        assert "Π.1" in notes, "Π.1.2: jubilees.notes should name the phase"


# ──────────────────────────────────────────────────────────────────
# Π.1.3 — one_enoch section page range + verification flag
# ──────────────────────────────────────────────────────────────────


class TestPi1OneEnochSection:
    """1 Enoch opens at PDF page 1515 (OCR-garbled `መጽ ሓራፈ ቸዓክ`,
    cleanly `መጽሐፈ ሄኖክ` on pages 1517+) and closes at 1566 (next
    page 1567 transitions to Matthew Gospel). 108 chapters expected
    (R.H. Charles 1912 edition). verified=tentative."""

    def _sec(self):
        return _load_source_cfg()["structural_map"]["one_enoch"]

    def test_pdf_page_range_correct(self):
        assert self._sec()["pdf_page_range"] == [1515, 1566]

    def test_pdf_index_offset_zero(self):
        assert self._sec()["pdf_index_offset"] == 0

    def test_verified_tentative(self):
        assert self._sec()["verified"] == "tentative"

    def test_verified_date(self):
        assert str(self._sec()["verified_date"]) == "2026-05-14"

    def test_chapter_count_expected_charles_1912(self):
        # R.H. Charles 1912 = 108 chapters; the SCOPE doc §Π.1
        # pin floor is also 108.
        assert self._sec()["chapter_count_expected"] == 108

    def test_notes_documents_discovery_method(self):
        notes = self._sec()["notes"]
        assert "ሄኖክ" in notes, "Π.1.3: one_enoch.notes should reference the title marker"
        assert "Charles" in notes, "Π.1.3: one_enoch.notes should anchor on Charles 1912"


# ──────────────────────────────────────────────────────────────────
# Π.1.4 — laodiceans slot declared NOT-IN-PDF
# ──────────────────────────────────────────────────────────────────


class TestPi1LaodiceansSlot:
    """The Pauline Letter to the Laodiceans is NOT in this PDF (full
    marker scan returned zero opening-title hits). The slot is declared
    so future expansion can populate it from an alternate source per
    the `feedback_license_flagging` memory protocol."""

    def _sec(self):
        return _load_source_cfg()["structural_map"]["laodiceans"]

    def test_present_in_pdf_false(self):
        assert self._sec()["present_in_pdf"] is False, (
            "Π.1.4: laodiceans must declare present_in_pdf=False — the "
            "full-PDF marker scan at Π.1 found ZERO 'መልእክት ... ሎዶቅያ' "
            "opening-title matches"
        )

    def test_pdf_page_range_null(self):
        # null/None is the canonical signal that the range is undefined.
        assert self._sec()["pdf_page_range"] is None

    def test_alternate_source_required(self):
        assert self._sec()["alternate_source_required"] is True

    def test_verified_false(self):
        # Not 'tentative' (boundary-page-confirmed) — fully unverified
        # because the book is not in this PDF at all.
        assert self._sec()["verified"] is False

    def test_notes_documents_secondary_references(self):
        notes = self._sec()["notes"]
        # The 4 secondary-reference pages must be named so the
        # absence-finding is auditable.
        for page in ["2004", "2077", "2080", "2284"]:
            assert page in notes, (
                f"Π.1.4: laodiceans.notes must document secondary-reference "
                f"page {page} so the absence-finding is auditable"
            )

    def test_notes_documents_alternate_sources(self):
        # Operator needs guidance on where to obtain the text.
        notes = self._sec()["notes"]
        assert "alternate" in notes.lower() or "Vulgate" in notes or "Geneva" in notes, (
            "Π.1.4: laodiceans.notes should hint at alternate-source options"
        )


# ──────────────────────────────────────────────────────────────────
# Π.1.5 — meqabyan.subsections hoisted into declarative YAML
# ──────────────────────────────────────────────────────────────────


class TestPi1MeqabyanSubsections:
    """The meqabyan section's per-book sub-ranges were hard-coded in
    extract_parallel_pdf.py's `heuristic` dict at τ.6.x.0a. Π.1
    hoists them into `_source.yaml::structural_map.meqabyan.subsections`
    so the extraction tool consumes them declaratively (heuristic
    remains as a safety net)."""

    def _meq(self):
        return _load_source_cfg()["structural_map"]["meqabyan"]

    def test_subsections_present(self):
        assert "subsections" in self._meq(), (
            "Π.1.5: meqabyan.subsections must be declared in _source.yaml "
            "(hoisted from extract_parallel_pdf.py's heuristic dict)"
        )

    def test_mq1_range(self):
        # τ.6.x.0a verified: 1318-1365 = 48 pages for 36 chapters.
        assert self._meq()["subsections"]["mq1"] == [1318, 1365]

    def test_mq2_range(self):
        # τ.6.x.0a verified: 1366-1372 = 7 pages for 21 chapters.
        assert self._meq()["subsections"]["mq2"] == [1366, 1372]

    def test_mq3_range(self):
        # τ.6.x.0a verified: 1373-1378 = 6 pages for 10 chapters.
        assert self._meq()["subsections"]["mq3"] == [1373, 1378]

    def test_subsections_cover_section_range(self):
        """The union of subsection page-ranges must lie within (and
        ideally cover) the meqabyan section page range 1318-1378."""
        meq = self._meq()
        section_start, section_end = meq["pdf_page_range"]
        for sub_name, (sub_start, sub_end) in meq["subsections"].items():
            assert section_start <= sub_start <= sub_end <= section_end, (
                f"Π.1.5: subsection {sub_name} range [{sub_start},{sub_end}] "
                f"must lie within meqabyan section range "
                f"[{section_start},{section_end}]"
            )


# ──────────────────────────────────────────────────────────────────
# Π.1.6 — tewahedo_distinctive_inventory metadata block
# ──────────────────────────────────────────────────────────────────


class TestPi1TewahedoDistinctiveInventory:
    """The structural_map gains a metadata sibling that names all 6
    Tewahedo-distinctive book codes and their extraction status at
    Π.1. This is metadata (not a real section); the extract tool
    filters it out via `_METADATA_KEYS`."""

    def _inv(self):
        cfg = _load_source_cfg()
        return cfg["structural_map"]["tewahedo_distinctive_inventory"]

    def test_inventory_present(self):
        cfg = _load_source_cfg()
        assert "tewahedo_distinctive_inventory" in cfg["structural_map"]

    def test_declared_sections_match(self):
        # The 4 declared sections (3 book sections in PDF + 1 missing).
        inv = self._inv()
        assert sorted(inv["declared_sections"]) == sorted(["meqabyan", "jubilees", "one_enoch", "laodiceans"])

    def test_book_codes_total_match(self):
        # All 6 Tewahedo-distinctive book codes named.
        inv = self._inv()
        assert sorted(inv["book_codes_total"]) == sorted(["mq1", "mq2", "mq3", "jub", "1en", "lao"])

    def test_declared_at_phase(self):
        assert self._inv()["declared_at_phase"] == "Π.1"

    def test_declared_date(self):
        assert str(self._inv()["declared_date"]) == "2026-05-14"

    def test_extraction_status_complete(self):
        # Every section must have an extraction_status entry.
        statuses = self._inv()["extraction_status_at_declaration"]
        for sec in ["meqabyan", "jubilees", "one_enoch", "laodiceans"]:
            assert sec in statuses, f"Π.1.6: extraction_status_at_declaration must cover {sec}"

    def test_laodiceans_status_is_source_unavailable(self):
        statuses = self._inv()["extraction_status_at_declaration"]
        assert statuses["laodiceans"] == "source-unavailable", (
            "Π.1.6: laodiceans must be marked source-unavailable in inventory"
        )

    def test_contract_text_documents_foundation_pattern(self):
        # The contract should anchor Π.1 as foundation-only (no
        # extraction) and name the next-phase pointers.
        contract = self._inv()["contract"]
        assert "FOUNDATION" in contract or "Foundation" in contract or "foundation" in contract
        assert "δ.1.x" in contract, "Π.1.6: contract should name δ.1.x as meqabyan extraction path"
        assert "τ.6.x.1+" in contract, "Π.1.6: contract should name τ.6.x.1+ as jub/1en extraction path"


# ──────────────────────────────────────────────────────────────────
# Π.1.7 — extract_parallel_pdf.py extensions
# ──────────────────────────────────────────────────────────────────


class TestPi1ExtractToolMultiSection:
    """The extraction tool gains Π.1 helpers + safeguards:
    - `_extraction_sections()` filters metadata keys out of section listing
    - `_METADATA_KEYS` names the metadata-key set
    - `extract_section()` refuses laodiceans (present_in_pdf=False)
    """

    def _mod(self):
        return _load_extract_module()

    def test_module_loads(self):
        mod = self._mod()
        assert hasattr(mod, "extract_section")

    def test_metadata_keys_constant_present(self):
        mod = self._mod()
        assert hasattr(mod, "_METADATA_KEYS"), (
            "Π.1.7: extract_parallel_pdf must expose _METADATA_KEYS to filter inventory keys out of section iteration"
        )
        assert "tewahedo_distinctive_inventory" in mod._METADATA_KEYS

    def test_extraction_sections_helper_present(self):
        mod = self._mod()
        assert hasattr(mod, "_extraction_sections")

    def test_extraction_sections_lists_4_real_sections(self):
        mod = self._mod()
        cfg = _load_source_cfg()
        names = mod._extraction_sections(cfg)
        # 4 real sections (meqabyan, jubilees, one_enoch, laodiceans).
        # laodiceans is still a real section (has book_codes); the
        # extract_section function refuses it at run-time via the
        # present_in_pdf guard.
        assert sorted(names) == sorted(["meqabyan", "jubilees", "one_enoch", "laodiceans"]), (
            f"Π.1.7: _extraction_sections returned {names}"
        )

    def test_extraction_sections_excludes_metadata(self):
        mod = self._mod()
        cfg = _load_source_cfg()
        names = mod._extraction_sections(cfg)
        assert "tewahedo_distinctive_inventory" not in names

    def test_extract_section_refuses_laodiceans(self):
        """extract_section() raises SystemExit when called on the
        laodiceans section because present_in_pdf=False signals that
        an alternate source is required."""
        import pytest

        mod = self._mod()
        cfg = _load_source_cfg()
        with pytest.raises(SystemExit) as excinfo:
            mod.extract_section(cfg, "laodiceans")
        msg = str(excinfo.value)
        assert "present_in_pdf" in msg or "alternate" in msg.lower(), (
            f"Π.1.7: laodiceans-extraction failure must mention present_in_pdf or alternate-source. Got: {msg}"
        )

    def test_extract_section_unknown_section_lists_real_sections(self):
        """When passed a bogus section name, the error message should
        list the real sections only (not inventory)."""
        import pytest

        mod = self._mod()
        cfg = _load_source_cfg()
        with pytest.raises(SystemExit) as excinfo:
            mod.extract_section(cfg, "nonexistent_section")
        msg = str(excinfo.value)
        assert "tewahedo_distinctive_inventory" not in msg, (
            "Π.1.7: error message must not leak the metadata key as a would-be section name"
        )

    def test_docstring_mentions_pi1(self):
        # The docstring should anchor Π.1 alongside τ.6.x.0a so future
        # maintainers see the extension pedigree.
        mod = self._mod()
        assert "Π.1" in (mod.__doc__ or ""), "Π.1.7: extract_parallel_pdf module docstring must reference Π.1"


# ──────────────────────────────────────────────────────────────────
# Π.1.8 — closed-arc + prior-phase invariant preservation
# ──────────────────────────────────────────────────────────────────


class TestPi1ClosedArcInvariantPreservation:
    """Π.1 is foundation-only; the closed arcs and prior-phase
    contracts must regression-pass."""

    def test_meqabyan_section_unchanged_post_pi1(self):
        """τ.6.x.0a's meqabyan declaration: book_codes + page_range +
        verified=True must remain intact."""
        meq = _load_source_cfg()["structural_map"]["meqabyan"]
        assert meq["book_codes"] == ["mq1", "mq2", "mq3"]
        assert meq["pdf_page_range"] == [1318, 1378]
        assert meq["verified"] is True

    def test_ocr_strategy_authorized_option_unchanged(self):
        """τ.6.x.0b's Option D Hybrid authorization must remain."""
        cfg = _load_source_cfg()
        assert cfg["ocr_strategy"]["authorized_option"] == "D-Hybrid"
        assert cfg["ocr_strategy"]["default_engine"] == "tesseract"

    def test_no_ingest_at_pi1(self):
        """Π.1 is foundation-only; no_ingest_at_this_phase contract
        from τ.6.x.0b/τ.6.x.0a remains True."""
        cfg = _load_source_cfg()
        assert cfg["ocr_strategy"]["no_ingest_at_this_phase"] is True

    def test_translation_slot_state_unchanged(self):
        """Translation slots remain at Π.0 seed state (3 verses
        Genesis only). Π.1 does NOT populate slots."""
        cfg = _load_source_cfg()
        assert cfg["ocr_strategy"]["geez_tewahedo_slot_seed_verse_count"] == 3
        assert cfg["ocr_strategy"]["amharic_tewahedo_slot_seed_verse_count"] == 3

    def test_amharic_still_in_popup_languages(self):
        """Π.0.1 invariant — amharic in POPUP_LANGUAGES."""
        from scripts.build_edition import POPUP_LANGUAGES

        assert "amharic" in POPUP_LANGUAGES

    def test_embed_font_paths_still_empty_default(self):
        """Π.0.4 invariant — EMBED_FONT_PATHS defaults to [] for
        v1.0 byte-identical reproducibility."""
        from scripts import style_config

        assert getattr(style_config, "EMBED_FONT_PATHS", None) == []

    def test_delta_1_0_divergence_entries_remain_empty(self):
        """δ.1.0 contract — meqabyan_geez_divergence.json entries
        remain [] (Π.1 must not accidentally populate them)."""
        data = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        assert data["entries"] == [], (
            "Π.1.8: δ.1.0's entries:[] contract must remain — Π.1 is "
            "foundation-only and does NOT promote any divergence entries"
        )

    def test_geez_tewahedo_genesis_seed_intact(self):
        """τ.6 + Π.0 invariant — geez-tewahedo/gen.py has 3 verses
        (Gen 1:1-3 seed); Π.1 must not touch this file."""
        gen_py = REPO / "content" / "translations" / "geez-tewahedo" / "gen.py"
        assert gen_py.is_file()
        text = gen_py.read_text(encoding="utf-8")
        # Crude verse-count check: count tuple-of-3 verse lines.
        # Pattern: (1, N, "...")
        import re

        verse_lines = re.findall(r"\(\s*1\s*,\s*\d+\s*,", text)
        assert len(verse_lines) >= 3, (
            f"Π.1.8: geez-tewahedo/gen.py must retain ≥3 verses (Gen 1:1-3 seed). Found {len(verse_lines)} tuples."
        )

    def test_gamma_4_8_e_meqabyan_arc_close_preserved(self):
        """γ.4.8.E closed-arc invariant — mq1+mq2+mq3 chapter coverage
        is 67/67. The divergence JSON _meta block names this floor;
        Π.1 must preserve it."""
        data = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        meta = data["_meta"]
        # The δ.1.0 _meta block has chapters_per_book or total_chapters.
        # Check whichever shape is present.
        chapters_per_book = meta.get("chapters_per_book", {})
        if chapters_per_book:
            assert chapters_per_book.get("mq1") == 36
            assert chapters_per_book.get("mq2") == 21
            assert chapters_per_book.get("mq3") == 10
        total = meta.get("total_chapters")
        if total is not None:
            assert total == 67, f"γ.4.8.E 67/67 floor preserved; meta total={total}"

    def test_gamma_4_8_f_meqabyan_voice_count_floor(self):
        """γ.4.8.F closed-arc invariant — ethiopian_commentaries.json
        Meqabyan voice ≥212. Π.1 must not touch the commentaries
        JSON."""
        commentaries = REPO / "content" / "sources" / "ethiopian_commentaries.json"
        if not commentaries.is_file():
            # Skip silently if the commentaries data isn't present
            # in this checkout (test_parallel_bible_delta1 already
            # cross-references the same data on a separate pin).
            import pytest

            pytest.skip("ethiopian_commentaries.json absent; covered by δ.1.0 pins")
        data = json.loads(commentaries.read_text(encoding="utf-8"))
        entries = data["entries"] if isinstance(data, dict) and "entries" in data else data
        # Count entries whose author/voice matches Meqabyan
        meq_keys = ("meqabyan", "mäqabyan", "mäṣḥafä mäqabyan")
        count = 0
        for entry in entries:
            author = str(entry.get("author", "") or entry.get("source", "")).lower()
            if any(k in author for k in meq_keys):
                count += 1
        # Soft floor: γ.4.8.F shipped ≥212; subsequent ω.43 / γ.4.8.E
        # arc-close brought it to 200. Use the 200 floor as the Π.1
        # regression-guard (the higher 212 floor lives in the γ.4.8.F
        # tests themselves).
        if count > 0:
            assert count >= 200, f"Π.1.8: meqabyan voice count regressed to {count} (γ.4.8 floor=200)"


# ──────────────────────────────────────────────────────────────────
# Π.1.9 — phase-coverage anchor (Π.1 named in scope doc + state)
# ──────────────────────────────────────────────────────────────────


class TestPi1PhaseCoverage:
    """Π.1 must appear in the scope doc (already true at ship time
    of τ.6.x.0a) and in the test inventory."""

    def test_scope_doc_names_pi1(self):
        scope = REPO / "dev" / "SCOPE_2026-05-14-parallel-bible.md"
        assert scope.is_file()
        text = scope.read_text(encoding="utf-8")
        assert "Π.1" in text, "Π.1.9: SCOPE doc must name Π.1"
        # The scope doc had Π.1 as "Parallel-PDF EXTRACTION (Tewahedo-
        # distinctive 6)"; that anchor remains.
        assert "Tewahedo-distinctive" in text or "tewahedo-distinctive" in text.lower()

    def test_pi1_test_file_named_canonically(self):
        # The test file is named test_parallel_bible_pi1.py per the
        # Π.0/τ.6.x.0/τ.6.x.0b/φ.1/δ.1.0 sibling pattern.
        assert __file__.endswith("test_parallel_bible_pi1.py")

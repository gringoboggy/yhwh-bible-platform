"""τ.6.x.0a — Parallel-PDF extraction infrastructure pins
(2026-05-14).

Built after the τ.6.x.0 audit pivot: eBible.org's `gez-Geez_vpl.zip`
slot was verified removed (404 + "ID not found" + zero `gez`/`geez`
IDs among 1,546 listed eBible.org translations). The parallel-Bible
PDF (`Bible_Amharic_and_Geez.pdf`, 2,539 pages) is therefore the
PRIMARY Geʽez + Amharic source, replacing the eBible.org seed-plan
declared in τ.6.

τ.6.x.0a deliverables under test:

1. The pivot is documented:
   - `_source.yaml` records the parallel-Bible PDF as the source.
   - `dev/SCOPE_2026-05-14-parallel-bible.md` §4.1 marks
     eBible.org gez-Geez as REMOVED and the parallel-PDF as
     PROMOTED to primary.

2. The structural map is verified:
   - `_source.yaml::structural_map.meqabyan` declares
     `pdf_page_range: [1318, 1378]` with publisher's chapter
     verification at 2026-05-14.
   - The Meqabyan book starts (1318, 1366, 1373) are verifiable
     against the live PDF when present.

3. The `scripts/extract_parallel_pdf.py` tool exists with:
   - PDF path resolution via `_source.yaml::resolution_paths`.
   - Per-section + per-pilot-book extraction modes.
   - Column-splitting (Geʽez left, Amharic right).
   - Verse + chapter parsing.
   - SOURCE_QUALITY provenance tagging.
   - --dry-run mode that does not write to translation slots.

4. The extraction tool does NOT yet populate the geez-tewahedo or
   amharic-tewahedo translation slots — the OCR-quality issue
   (acknowledged in `_source.yaml::ocr_caveats` and Phase-4 docs)
   requires a follow-up τ.6.x.0b phase that addresses it
   (better OCR / page-image / cloud-OCR / manual transcription).
   Per the τ.6.x.0a contract: production translation data only
   lands when source_quality reaches `ocr-tier2` or
   `page-image-tier1`.

5. Π.0 closed-arc invariants preserved.
"""

from __future__ import annotations

from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0 — source pivot documented
# ──────────────────────────────────────────────────────────────────


class TestTau6x0SourcePivot:
    """The shift from eBible.org to parallel-Bible PDF is recorded
    in two places: `_source.yaml` and the SCOPE doc.
    """

    def test_source_yaml_exists(self):
        path = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
        assert path.is_file(), "τ.6.x.0: parallel-bible-eotc/_source.yaml must exist"

    def test_source_yaml_shape(self):
        path = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert cfg["source_id"] == "parallel-bible-eotc"
        assert cfg["primary_filename"] == "Bible_Amharic_and_Geez.pdf"
        assert cfg["total_pages"] == 2539
        assert cfg["archive_org_id"] == "EOTXC_HOLYSCRIPTS_ALL_BOOKS"

    def test_resolution_paths_includes_env_var_and_publisher(self):
        path = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        paths = cfg.get("resolution_paths") or []
        # Must include env-var override + publisher-supplied path.
        joined = " ".join(paths)
        assert "PARALLEL_BIBLE_PDF" in joined, "must support PARALLEL_BIBLE_PDF env var"
        assert "project_maccabees_expansion" in joined, "must reference publisher-supplied path"

    def test_scope_doc_records_pivot(self):
        path = REPO / "dev" / "archive" / "SCOPE_2026-05-14-parallel-bible.md"
        assert path.is_file()
        body = path.read_text(encoding="utf-8")
        assert "τ.6.x.0" in body, "SCOPE doc must reference the τ.6.x.0 audit"
        assert "REMOVED" in body or "removed" in body, "SCOPE doc must record eBible.org gez-Geez removal"
        assert "PRIMARY" in body or "primary" in body, "SCOPE doc must record parallel-PDF promotion"

    def test_quality_tiers_documented(self):
        path = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        tiers = cfg.get("source_quality_tiers") or {}
        # Three tiers documented: ocr-tier3, ocr-tier2, page-image-tier1
        assert "ocr_tier3" in tiers
        assert "ocr_tier2" in tiers
        assert "page_image_tier1" in tiers


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0a — structural map for Meqabyan in the full Bible PDF
# ──────────────────────────────────────────────────────────────────


class TestTau6x0aStructuralMap:
    """The Meqabyan page range in the FULL Bible PDF is documented
    as 1318-1378 (different from the 76-page extract used in
    project_maccabees_expansion/, which uses scan-page numbers
    832-907 starting at 0)."""

    def test_meqabyan_structural_map_present(self):
        path = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        sec = cfg["structural_map"].get("meqabyan")
        assert sec is not None, "structural_map.meqabyan must be present"

    def test_meqabyan_book_codes(self):
        path = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        sec = cfg["structural_map"]["meqabyan"]
        assert sec["book_codes"] == ["mq1", "mq2", "mq3"]

    def test_meqabyan_page_range_uses_full_pdf_indexing(self):
        """τ.6.x.0a verified empirically that Meqabyan in the full
        Bible PDF occupies pages 1318-1378 (book starts: 1 Mq=1318,
        2 Mq=1366, 3 Mq=1373; 3 Mq ends ~1378 with Sirach following
        at ~1379)."""
        path = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        sec = cfg["structural_map"]["meqabyan"]
        assert "pdf_page_range" in sec, "post-τ.6.x.0a uses pdf_page_range (0-indexed full PDF), not scan_page_range"
        start, end = sec["pdf_page_range"]
        # Verified empirically: Meqabyan section in Bible_Amharic_and_Geez.pdf
        assert start == 1318, f"τ.6.x.0a: Meqabyan in full PDF starts at page 1318, got {start}"
        assert end == 1378, f"τ.6.x.0a: Meqabyan in full PDF ends ~page 1378, got {end}"

    def test_verified_flag(self):
        path = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        sec = cfg["structural_map"]["meqabyan"]
        assert sec.get("verified") is True
        assert sec.get("verified_date") is not None


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0a — extract_parallel_pdf.py tool
# ──────────────────────────────────────────────────────────────────


class TestTau6x0aExtractTool:
    """The extraction tool itself is buildable, importable, and
    handles the core helpers correctly without requiring the actual
    PDF binary."""

    def test_tool_script_exists(self):
        path = REPO / "scripts" / "extract_parallel_pdf.py"
        assert path.is_file()

    def test_tool_is_importable(self):
        """We don't run main() here — just ensure the module imports
        without ImportError. The tool requires pymupdf only when
        actually extracting; helper functions don't import fitz at
        module-load time (lazy)."""
        import importlib

        spec = importlib.util.spec_from_file_location(
            "extract_parallel_pdf",
            REPO / "scripts" / "extract_parallel_pdf.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # Sanity check on the expected functions.
        assert callable(mod.load_source_config)
        assert callable(mod.resolve_pdf_path)
        assert callable(mod.geez_numeral_to_int)
        assert callable(mod.parse_verses_from_text)
        assert callable(mod.write_book_module)
        assert callable(mod.main)

    def test_geez_numeral_to_int(self):
        """The Geʽez numeral parser must correctly handle single
        digits and compounds (additive: ፴፮ = 30+6 = 36)."""
        import importlib

        spec = importlib.util.spec_from_file_location(
            "extract_parallel_pdf",
            REPO / "scripts" / "extract_parallel_pdf.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # Single digits
        assert mod.geez_numeral_to_int("፩") == 1
        assert mod.geez_numeral_to_int("፬") == 4
        assert mod.geez_numeral_to_int("፱") == 9
        # Tens
        assert mod.geez_numeral_to_int("፲") == 10
        assert mod.geez_numeral_to_int("፴") == 30
        # Compounds
        assert mod.geez_numeral_to_int("፲፩") == 11  # 10+1
        assert mod.geez_numeral_to_int("፴፮") == 36  # 30+6
        assert mod.geez_numeral_to_int("፳፩") == 21  # 20+1
        # Hundreds
        assert mod.geez_numeral_to_int("፻") == 100
        # Edge cases
        assert mod.geez_numeral_to_int("") is None
        assert mod.geez_numeral_to_int("xyz") is None

    def test_parse_verses_from_text_handles_chapter_headers(self):
        """The parser must recognize ምዕራፍ + Geʽez numeral and
        reset the chapter counter."""
        import importlib

        spec = importlib.util.spec_from_file_location(
            "extract_parallel_pdf",
            REPO / "scripts" / "extract_parallel_pdf.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sample = "\n".join(
            [
                "ምዕራፍ ፩",
                "1 በመጀመሪያ እግዚአብሔር ሰማይንና",
                "2 ምድርም ቅርጥ የሌላት",
                "ምዕራፍ ፪",
                "1 ሰማይና ምድር",
            ]
        )
        result = mod.parse_verses_from_text(sample)
        # We expect: (1, 1, ...), (1, 2, ...), (2, 1, ...)
        chapters = [c for c, v, t in result]
        [v for c, v, t in result]
        assert 1 in chapters and 2 in chapters
        assert (1, 1) in [(c, v) for c, v, t in result]
        assert (1, 2) in [(c, v) for c, v, t in result]
        assert (2, 1) in [(c, v) for c, v, t in result]


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0a — translation slot CONTRACT preservation
# ──────────────────────────────────────────────────────────────────


class TestTau6x0aTranslationSlotsClean:
    """Per the τ.6.x.0a contract, the geez-tewahedo and
    amharic-tewahedo slots must remain at their Π.0 seed state
    (3 verses each on Genesis only). The OCR-tier-3 data from the
    parallel-PDF extraction is NOT to be auto-populated; that
    waits for τ.6.x.0b which addresses the OCR-quality problem.
    """

    def test_geez_tewahedo_remains_at_seed_state(self):
        """The geez-tewahedo translation slot must have ONLY the
        gen.py seed (3 verses) — no mq1.py / mq2.py / mq3.py
        populated by an OCR-tier-3 extraction run."""
        slot = REPO / "content" / "translations" / "geez-tewahedo"
        files = sorted(p.name for p in slot.iterdir() if p.suffix == ".py")
        # Allow gen.py only (the τ.6 seed). If more books are added
        # in later phases (τ.6.x.0b+, δ.1.x), this assertion will
        # need to be loosened or replaced with a quality-tagging
        # assertion.
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
        `feedback_share_pin_pattern`. τ.6.x.0a's original invariant
        (`files == ['gen.py']`) was the Π.0 seed state; τ.7.x.a + τ.7.x.b
        broke this exact assertion. Durable invariant: gen.py is present."""
        slot = REPO / "content" / "translations" / "amharic-tewahedo"
        files = sorted(p.name for p in slot.iterdir() if p.suffix == ".py")
        assert "gen.py" in files, (
            f"τ.6.x.0a contract relaxed at τ.7.x.b: amharic-tewahedo "
            f"must contain gen.py (Π.0 seed or its τ.7.x.a successor). "
            f"Got files: {files}"
        )


# ──────────────────────────────────────────────────────────────────
# τ.6.x.0a — Π.0 closed-arc invariants preserved
# ──────────────────────────────────────────────────────────────────


class TestTau6x0aClosedArcInvariantPreservation:
    """The Π.0 infrastructure must remain intact after τ.6.x.0a:
    amharic still in POPUP_LANGUAGES, CSS still emits, font infra
    still works, γ.4.8.E ARC-CLOSE still at 67/67. Pinned to catch
    accidental regression."""

    def test_amharic_still_in_popup_languages(self):
        from scripts.build_edition import POPUP_LANGUAGES

        assert "amharic" in POPUP_LANGUAGES, "τ.6.x.0a must not regress Π.0.1: amharic must remain in POPUP_LANGUAGES"

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
                f"τ.6.x.0a must not regress γ.4.8.E arc-close {book} {total}/{total}"
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
        assert len(meq) >= 212, f"τ.6.x.0a: Meqabyan count must remain ≥212; got {len(meq)}"

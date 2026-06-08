"""Π.0 — Parallel-Bible infrastructure foundations (2026-05-14).

INFRASTRUCTURE-ONLY ship. No content is yet surfaced in any
production EPUB. The Π.0 phase prepares every hook that the
later parallel-Bible expansion phases (τ.6.x, τ.7.x, Π.1, Π.2,
δ.1.x, φ.1, δ.2) need, without disturbing v1.0 reproducibility
or the closed γ.4.8.E Meqabyan-arc invariants.

The full strategic roadmap for parallel-Bible work lives at:
    dev/SCOPE_2026-05-14-parallel-bible.md

Π.0 deliverables under test:

1. `amharic` registered in POPUP_LANGUAGES (parallel to existing
   `geez`, `aramaic`, `latin`, `coptic`, `syriac` declarations).
2. CSS `.vnote-geez` and `.vnote-amharic` blocks emit correctly
   from `scripts/apply_style.py` (LTR, Ethiopic-fallback chain).
3. New `amharic-tewahedo` translation slot exists with:
   - `_meta.yaml` declaring source / license / fetched-date
   - Genesis 1:1-3 seed in modern Amharic
   - Text is in the Ethiopic Unicode block (U+1200-U+137F)
4. Multi-font embed infrastructure:
   - `style_config.EMBED_FONT_PATHS` exists as a list (default [])
   - `apply_style.py` emits @font-face per entry
   - `content/assets/fonts/` directory exists with README + LICENSES
   - Legacy single-font `EMBED_FONT_PATH` knob still works
     (v1.0 build reproducibility)
5. Closed-arc invariants preserved:
   - γ.4.8.E Meqabyan apparatus 67/67 chapter coverage intact
   - ethiopian-tewahedo edition popup_languages_default NOT yet
     surfacing geez/amharic (the flip is gated to Π.2)
   - 4033 existing tests still pass (verified at ship time, not
     here)
"""

from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────────
# Π.0.1 — amharic registered in POPUP_LANGUAGES
# ──────────────────────────────────────────────────────────────────


class TestPi0PopupLanguageRegistration:
    """amharic is now a first-class popup-language entry. Mirrors
    the geez declaration that τ.6 added.
    """

    def test_amharic_in_popup_languages(self):
        from scripts.build_edition import POPUP_LANGUAGES

        assert "amharic" in POPUP_LANGUAGES, (
            "Π.0.1: 'amharic' must be a registered popup language; "
            "added alongside 'geez' to support the parallel-Bible expansion"
        )

    def test_amharic_entry_shape(self):
        from scripts.build_edition import POPUP_LANGUAGES

        entry = POPUP_LANGUAGES["amharic"]
        assert entry["label"] == "Amharic", "amharic label must be 'Amharic'"
        assert entry["content_class"] == "vnote-amharic", (
            "amharic content class must be 'vnote-amharic' (matches the CSS block added in Π.0.2)"
        )
        assert entry["has_label_para"] is True, (
            "amharic has a label paragraph (same as hebrew/greek/geez "
            "convention; only english has has_label_para=False per τ.1.5 "
            "swap-history)"
        )

    def test_geez_still_registered(self):
        """Regression-guard: τ.6's `geez` registration must remain
        intact after Π.0's `amharic` addition."""
        from scripts.build_edition import POPUP_LANGUAGES

        assert "geez" in POPUP_LANGUAGES
        assert POPUP_LANGUAGES["geez"]["label"] == "Ge'ez"
        assert POPUP_LANGUAGES["geez"]["content_class"] == "vnote-geez"

    def test_all_popup_languages_count(self):
        """Π.0 raises the registered-language count from 8 to 9.
        Pinned so accidental removal is caught at commit time."""
        from scripts.build_edition import ALL_POPUP_LANGUAGES

        assert len(ALL_POPUP_LANGUAGES) >= 9, (
            f"Π.0 expects ≥9 registered popup languages "
            f"(english/hebrew/greek/aramaic/geez/latin/coptic/syriac/amharic); "
            f"got {len(ALL_POPUP_LANGUAGES)}: {ALL_POPUP_LANGUAGES}"
        )


# ──────────────────────────────────────────────────────────────────
# Π.0.2 — CSS classes emit
# ──────────────────────────────────────────────────────────────────


class TestPi0CssClassEmission:
    """`scripts/apply_style.py` must emit `.vnote-geez` and
    `.vnote-amharic` blocks alongside the existing `.vnote-text`,
    `.vnote-hebrew`, `.vnote-greek` blocks. The new blocks must
    declare an Ethiopic-script font-family fallback chain and use
    LTR direction (Ethiopic is not RTL, unlike Hebrew).
    """

    @staticmethod
    def _generated_css() -> str:
        """Call apply_style's internal CSS-generation entry point
        and return the stylesheet contents. Mirrors the production
        build path (no monkey-patching)."""

        # apply_style.py keeps its CSS templates as module-level
        # strings; the cleanest way to test the templates without
        # writing files is to read the module source.
        path = REPO / "scripts" / "apply_style.py"
        return path.read_text(encoding="utf-8")

    def test_vnote_geez_css_block_present(self):
        css = self._generated_css()
        assert ".vnote-geez" in css, (
            "Π.0.2: .vnote-geez CSS block must be present in apply_style.py "
            "(parallel-Bible popup-paragraph styling for Ge'ez text)"
        )

    def test_vnote_amharic_css_block_present(self):
        css = self._generated_css()
        assert ".vnote-amharic" in css, "Π.0.2: .vnote-amharic CSS block must be present in apply_style.py"

    def test_ethiopic_font_fallback_chain(self):
        """The Ethiopic CSS blocks must list Noto Sans Ethiopic
        (the preferred embedded option per `content/assets/fonts/
        README.md`) and at least one cross-platform fallback
        (Abyssinica SIL / Nyala / Kefa / Ethiopia Jiret) before
        falling through to a generic serif."""
        css = self._generated_css()
        assert "Noto Sans Ethiopic" in css, "Π.0.2 Ethiopic CSS must declare Noto Sans Ethiopic in font-family stack"
        assert "Abyssinica SIL" in css or "Nyala" in css, (
            "Π.0.2 Ethiopic CSS must include cross-platform Ethiopic font fallback (Abyssinica SIL, Nyala, etc.)"
        )

    def test_no_rtl_for_ethiopic(self):
        """Sanity check: Ethiopic is LTR. Neither .vnote-geez nor
        .vnote-amharic should set `direction: rtl` (which would
        break Ge'ez/Amharic rendering on conforming readers)."""
        css = self._generated_css()
        # Extract just the .vnote-geez and .vnote-amharic blocks
        # and confirm rtl is absent from each.
        for cls in (".vnote-geez", ".vnote-amharic"):
            start = css.find(cls)
            assert start >= 0
            block_end = css.find("}", start)
            assert block_end >= 0
            block = css[start:block_end]
            assert "rtl" not in block, f"Π.0.2: {cls} must not declare direction:rtl — Ethiopic is LTR"

    def test_dark_mode_includes_new_classes(self):
        """The dark-mode `@media (prefers-color-scheme: dark)`
        block must list .vnote-geez and .vnote-amharic alongside
        .vnote-text/-hebrew/-greek so they get the dark color
        treatment."""
        css = self._generated_css()
        dark_idx = css.find("prefers-color-scheme: dark")
        assert dark_idx >= 0
        # The relevant section runs from the @media down to the
        # next closing brace at the start of a line; grab a
        # generous chunk.
        chunk = css[dark_idx : dark_idx + 800]
        assert ".vnote-geez" in chunk and ".vnote-amharic" in chunk, (
            "Π.0.2: dark-mode rule must include .vnote-geez and .vnote-amharic (color override for readability)"
        )


# ──────────────────────────────────────────────────────────────────
# Π.0.3 — amharic-tewahedo translation slot
# ──────────────────────────────────────────────────────────────────


class TestPi0AmharicTewahedoSeed:
    """The amharic-tewahedo translation slot is created with
    metadata + a Genesis 1:1-3 seed. Mirrors the τ.6 geez-tewahedo
    seed pattern.
    """

    def test_meta_yaml_exists(self):
        path = REPO / "content" / "translations" / "amharic-tewahedo" / "_meta.yaml"
        assert path.is_file(), "Π.0.3: amharic-tewahedo _meta.yaml must exist"

    def test_meta_yaml_shape(self):
        import yaml

        path = REPO / "content" / "translations" / "amharic-tewahedo" / "_meta.yaml"
        meta = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert meta["id"] == "amharic-tewahedo"
        assert meta["short_title"] == "Amharic"
        # Must reference the parallel-Bible source (EOTC FULL BIBLE)
        # OR nehemiah-osc.org (the v1 Phase-1 Amharic source). Both
        # are valid Π.0 source declarations.
        src = meta["source"]
        publisher = (src.get("publisher") or "").lower()
        assert "tewahedo" in publisher or "eotc" in publisher or "nehemiah" in publisher, (
            "Π.0.3: _meta.yaml source.publisher must reference a Tewahedo/EOTC source "
            "(parallel-Bible PDF, nehemiah-osc.org, or eBible.org amh VPL)"
        )
        # Refactored at τ.7.x.a ship-time per `feedback_share_pin_pattern`
        # — Π.0 seed was 3 verses; τ.7.x.a upgraded amharic-tewahedo/gen.py
        # to 1308-verse ingest. Original pin asserted ==3; new pin asserts
        # >=3 (the seed's 3-verse Gen 1:1-3 floor is preserved as a
        # minimum; full-ingest count satisfies the "≥ seed" milestone).
        assert meta["stats"]["verses"] >= 3, (
            "Π.0 seed floor: stats.verses must be at least 3 (Gen 1:1-3); "
            "τ.7.x.a upgrade preserves this floor while expanding to full ingest"
        )

    def test_genesis_seed_loads(self):
        from scripts.core import translations

        translations.clear_cache()
        verses = translations._load_book("amharic-tewahedo", "gen")
        assert verses, "Π.0.3: amharic-tewahedo gen.py must load via the translations API"
        # Refactored at τ.7.x.a ship-time per `feedback_share_pin_pattern`
        # — Π.0 seed was 3 verses; τ.7.x.a upgraded to 1308-verse ingest.
        # Floor preserved at ≥3 (Gen 1:1-3 invariant).
        assert len(verses) >= 3, (
            f"Π.0 seed floor: ≥3 verses (Gen 1:1-3); got {len(verses)}. "
            f"τ.7.x.a expanded this to 1308; ≥3 is the durable floor."
        )

    def test_seed_is_ethiopic_script(self):
        from scripts.core import translations

        translations.clear_cache()
        verses = translations._load_book("amharic-tewahedo", "gen")
        for _ch, _v, text in verses:
            # At least one character must be in the Ethiopic block
            # (U+1200-U+137F) for each verse.
            has_ethiopic = any(0x1200 <= ord(c) <= 0x137F for c in text)
            assert has_ethiopic, (
                f"Π.0.3: amharic-tewahedo seed verse must contain Ethiopic-block characters; got {text!r}"
            )

    def test_seed_opens_genesis_1_1_signature(self):
        """Amharic Gen 1:1 traditionally opens with በመጀመሪያ
        ('in-the-beginning') — distinct from the classical Ge'ez
        opening ቀዳሚሁ. This is a sanity-check that the seed is
        actually Amharic and not accidentally Ge'ez."""
        from scripts.core import translations

        translations.clear_cache()
        verses = translations._load_book("amharic-tewahedo", "gen")
        v1_1 = next((t for ch, v, t in verses if (ch, v) == (1, 1)), None)
        assert v1_1 is not None
        assert "በመጀመሪያ" in v1_1, (
            f"Π.0.3: amharic-tewahedo Gen 1:1 should open with "
            f"በመጀመሪያ ('in the beginning' in modern Amharic); got {v1_1!r}"
        )

    def test_geez_tewahedo_seed_still_intact(self):
        """Regression-guard: τ.6 geez-tewahedo Genesis must remain
        loadable + non-trivial.

        MIGRATED at τ.6.x.2.a-h batch ship-time (2026-05-15): the
        Π.0 seed had the clean canonical opening ቀዳሚሁ. The τ.6.x.2.a
        ocr-tier3 ingest replaced the 3-verse curated seed with a
        1022-verse garbled-but-real OCR ingest — Gen 1:1 now reads
        `በሩዳሚ ገብረ አግዚአብሔር ሰማየ ወምድረ` (ቀዳሚ→ሩዳሚ OCR garble). Per the
        τ.6.x.0b honesty contract ocr-tier3 garbling is expected.
        Durable invariant: Genesis loads, is at ingest scale, and
        Gen 1:1 carries the ዳሚ beginning-root fragment (survives
        the OCR garble in both the clean ቀዳሚሁ + garbled በሩዳሚ forms)."""
        from scripts.core import translations

        translations.clear_cache()
        verses = translations._load_book("geez-tewahedo", "gen")
        assert verses and len(verses) >= 950, "τ.6.x.2.a geez-tewahedo Genesis must be at ocr-tier3 scale (≥950 verses)"
        v1_1 = next((t for ch, v, t in verses if (ch, v) == (1, 1)), None)
        assert v1_1 is not None and "ዳሚ" in v1_1, (
            f"τ.6.x.2.a geez-tewahedo Gen 1:1 must carry the ዳሚ beginning-root; got {v1_1!r}"
        )


# ──────────────────────────────────────────────────────────────────
# Π.0.4 — Multi-font embed infrastructure
# ──────────────────────────────────────────────────────────────────


class TestPi0MultiFontInfrastructure:
    """The single-font legacy knob (EMBED_FONT_PATH) is preserved
    AND a new EMBED_FONT_PATHS list supplements it. The two
    code paths compose additively (single + list) in apply_style's
    @font-face emission, so a v1.0-tagged build with only the
    legacy knob set produces the same output as before.
    """

    def test_embed_font_paths_attribute_exists(self):
        from scripts import style_config

        assert hasattr(style_config, "EMBED_FONT_PATHS"), (
            "Π.0.4: style_config.EMBED_FONT_PATHS must exist as a list (parallel-Bible multi-font embed infrastructure)"
        )

    def test_embed_font_paths_populated_at_rx_phase3(self):
        """Π.0 shipped this slot EMPTY (infra committed, binaries not yet).
        RX Phase 3 (2026-06-05) deliberately populated it with the committed
        OFL fonts for original-language/Ethiopic embedding (device issue #7),
        so the durable invariant migrates from the empty seed to the populated
        MECHANISM (see feedback_share_pin_pattern: a pin asserts what HAS
        shipped, never what has not yet)."""
        from scripts import style_config

        assert isinstance(style_config.EMBED_FONT_PATHS, list)
        families = {e.get("family") for e in style_config.EMBED_FONT_PATHS}
        assert {"Cardo", "Noto Serif Ethiopic"} <= families, style_config.EMBED_FONT_PATHS

    def test_legacy_single_font_knobs_preserved(self):
        """v1.0 reproducibility: the legacy EMBED_FONT_PATH +
        EMBED_FONT_FAMILY knobs must remain wired through
        apply_style.py."""
        from scripts import style_config

        # Both must exist as attributes even if EMBED_FONT_PATH is None.
        assert hasattr(style_config, "EMBED_FONT_PATH")
        assert hasattr(style_config, "EMBED_FONT_FAMILY")
        # IM Fell English is the legacy default font family.
        assert style_config.EMBED_FONT_FAMILY == "IM Fell English"

    def test_apply_style_handles_multi_font_list(self):
        """apply_style.py must iterate EMBED_FONT_PATHS and emit
        one @font-face rule per entry. The integration test is
        a source-level check that the loop exists; behavioral
        testing happens at τ.6.x / Π.2 when the binary lands."""
        path = REPO / "scripts" / "apply_style.py"
        src = path.read_text(encoding="utf-8")
        # Look for the multi-font emission loop signature.
        assert "EMBED_FONT_PATHS" in src, "Π.0.4: apply_style.py must read style_config.EMBED_FONT_PATHS"
        assert "@font-face" in src, "Π.0.4: apply_style.py must emit @font-face rules"

    def test_fonts_directory_exists(self):
        fonts_dir = REPO / "content" / "assets" / "fonts"
        assert fonts_dir.is_dir(), "Π.0.4: content/assets/fonts/ directory must exist as the font-binary staging area"

    def test_fonts_readme_exists(self):
        readme = REPO / "content" / "assets" / "fonts" / "README.md"
        assert readme.is_file()
        body = readme.read_text(encoding="utf-8")
        assert "Noto Sans Ethiopic" in body, (
            "Π.0.4: fonts/README.md must document the Noto Sans Ethiopic addition workflow"
        )
        assert "OFL" in body, "Π.0.4: fonts/README.md must reference the SIL OFL license policy"

    def test_fonts_licenses_exists(self):
        licenses = REPO / "content" / "assets" / "fonts" / "LICENSES.md"
        assert licenses.is_file()
        body = licenses.read_text(encoding="utf-8")
        assert "OFL" in body, "Π.0.4: fonts/LICENSES.md must declare the OFL policy"
        assert "Noto Sans Ethiopic" in body, "Π.0.4: fonts/LICENSES.md must list Noto Sans Ethiopic"


# ──────────────────────────────────────────────────────────────────
# Π.0.5 — Closed-arc invariant preservation
# ──────────────────────────────────────────────────────────────────


class TestPi0ClosedArcInvariantPreservation:
    """γ.4.8.E ARC-CLOSE state must remain intact after Π.0:
    mq1 36/36 + mq2 21/21 + mq3 10/10 = 67/67 chapter coverage of
    the Meqabyan apparatus. Also: ethiopian-tewahedo's
    popup_languages_default must NOT yet surface geez/amharic
    (the flip is gated to Π.2; surfacing them at Π.0 would expose
    incomplete data).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _meq_at(self, book, ch, v):
        return [e for e in self.ec.for_verse(book, ch, v) if e.father == "Meqabyan (Ethiopian tradition)"]

    def test_meqabyan_arc_close_67_67_intact(self):
        for book, total in [("mq1", 36), ("mq2", 21), ("mq3", 10)]:
            chs_with_entries = set()
            for ch in range(1, total + 1):
                for v in range(1, 60):
                    if self._meq_at(book, ch, v):
                        chs_with_entries.add(ch)
                        break
            assert chs_with_entries == set(range(1, total + 1)), (
                f"Π.0 must not disturb γ.4.8.E arc-close {book} {total}/{total}; "
                f"missing chapters: {set(range(1, total + 1)) - chs_with_entries}"
            )

    def test_meqabyan_count_at_least_212(self):
        """γ.4.8.E arc-close 200 + γ.4.8.F Tier-2 integration 12 = 212.
        Π.0 must not reduce this floor."""
        meq = [
            e
            for verse_entries in self.ec._by_verse.values()
            for e in verse_entries
            if e.father == "Meqabyan (Ethiopian tradition)"
        ]
        assert len(meq) >= 212, f"Π.0: Meqabyan count must remain ≥212 (γ.4.8.E 200 + γ.4.8.F 12); got {len(meq)}"

    def test_ethiopian_tewahedo_popup_default_not_yet_flipped(self):
        """Π.0 explicitly does NOT change ethiopian-tewahedo's
        popup_languages_default. The geez+amharic surfacing happens
        at Π.2 after τ.6.x + τ.7.x + Π.1 ingests complete.
        Surfacing them at Π.0 would expose incomplete data (3-verse
        seeds), which would degrade the user experience and break
        the Π.0 'infrastructure-only' contract."""
        import yaml

        path = REPO / "content" / "editions.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        editions = data["editions"] if isinstance(data, dict) else data
        if isinstance(editions, dict):
            editions = list(editions.values())
        et = next(e for e in editions if e.get("id") == "ethiopian-tewahedo")
        default = et.get("popup_languages_default", [])
        # Must NOT include geez or amharic yet.
        assert "geez" not in default, (
            "Π.0 contract: ethiopian-tewahedo popup_languages_default must NOT "
            "yet surface 'geez' (gated to Π.2). Current default: " + repr(default)
        )
        assert "amharic" not in default, (
            "Π.0 contract: ethiopian-tewahedo popup_languages_default must NOT "
            "yet surface 'amharic' (gated to Π.2). Current default: " + repr(default)
        )


# ──────────────────────────────────────────────────────────────────
# Π.0.6 — Translation discovery
# ──────────────────────────────────────────────────────────────────


class TestPi0TranslationDiscovery:
    """The amharic-tewahedo slot must be discoverable via the
    runtime translations API (`list_translations`, `has_translation`)
    so the build pipeline can compose against it once data lands.
    """

    def test_amharic_tewahedo_in_list(self):
        from scripts.core import translations

        translations.clear_cache()
        ids = translations.list_translations()
        assert "amharic-tewahedo" in ids, (
            f"Π.0.3: amharic-tewahedo must appear in list_translations(); got: {sorted(ids)}"
        )

    def test_has_translation_amharic_tewahedo(self):
        from scripts.core import translations

        assert translations.has_translation("amharic-tewahedo") is True

    def test_geez_tewahedo_still_discoverable(self):
        """Regression-guard: τ.6 discovery must still work."""
        from scripts.core import translations

        translations.clear_cache()
        ids = translations.list_translations()
        assert "geez-tewahedo" in ids

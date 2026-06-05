"""φ.1 — Font + typography polish pins (2026-05-14).

φ.1 is the FONT-AND-TYPOGRAPHY POLISH phase of the 8-phase parallel-
Bible expansion. It's parallel-unblocked relative to τ.6.x.0c (user-
side Tesseract install) and δ.1.x (Phase-4 Meqabyan) — runs
concurrently with both. φ.1 deliverables refine the Π.0 .vnote-geez /
.vnote-amharic CSS classes for production fidel rendering AND wire
the OPF font-manifest emission that Π.0 left as a gap.

φ.1 deliverables under test:

1. **CSS polish — five Ethiopic-aware refinements** to .vnote-geez and
   .vnote-amharic in scripts/apply_style.py:
   - text-rendering: optimizeLegibility
   - font-feature-settings: "kern", "liga"
   - hyphens: none
   - unicode-bidi: isolate
   - word-break: keep-all

2. **@font-face polish** — font-display: swap added so readers render
   fallback text immediately rather than blocking on embedded font
   download; optional unicode_range supported per EMBED_FONT_PATHS
   entry.

3. **OPF font-manifest emission** — new patch_opf_fonts() helper in
   scripts/build_edition.py registers EMBED_FONT_PATHS + legacy
   EMBED_FONT_PATH entries in content.opf manifest with correct
   media-type. Idempotent + no-op when both knobs empty (v1.0
   reproducibility).

4. **fonts/README.md** updated with accurate Π.0/φ.1 workflow,
   correcting the misleading "already plumbed" statement.

5. **Closed-arc invariants regression-guarded** — Π.0.4 (EMBED_
   FONT_PATHS defaults to []) preserved + γ.4.8.E (67/67) + Meqabyan
   ≥212 floor.

6. **τ.6.x.0a + τ.6.x.0b CONTRACTs preserved** — translation slots
   remain at Π.0 seed.
"""

from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────────
# φ.1 — CSS polish: five Ethiopic-aware refinements
# ──────────────────────────────────────────────────────────────────


class TestPhi1CssPolish:
    """The .vnote-geez and .vnote-amharic classes in apply_style.py
    each declare the five φ.1 typography refinements:
    text-rendering, font-feature-settings, hyphens, unicode-bidi,
    word-break."""

    APPLY_STYLE = REPO / "scripts" / "apply_style.py"

    def _block(self, klass: str) -> str:
        """Extract the CSS block for `.vnote-geez` or `.vnote-amharic`
        from apply_style.py source (so the test doesn't need the
        epub_working/ directory)."""
        src = self.APPLY_STYLE.read_text(encoding="utf-8")
        marker = f".{klass} {{"
        idx = src.find(marker)
        assert idx != -1, f"apply_style.py must contain a `{marker}` rule"
        end = src.find("}", idx)
        assert end != -1
        return src[idx : end + 1]

    def test_geez_has_text_rendering(self):
        block = self._block("vnote-geez")
        assert "text-rendering: optimizeLegibility" in block, (
            "φ.1: .vnote-geez must declare text-rendering: optimizeLegibility"
        )

    def test_geez_has_font_feature_settings(self):
        block = self._block("vnote-geez")
        assert 'font-feature-settings: "kern", "liga"' in block, (
            "φ.1: .vnote-geez must enable kern + liga via font-feature-settings"
        )

    def test_geez_has_hyphens_none(self):
        block = self._block("vnote-geez")
        assert "hyphens: none" in block, "φ.1: .vnote-geez must disable hyphenation (Ethiopic does not hyphenate)"

    def test_geez_has_unicode_bidi_isolate(self):
        block = self._block("vnote-geez")
        assert "unicode-bidi: isolate" in block, "φ.1: .vnote-geez must isolate bidirectional reorderings"

    def test_geez_has_word_break_keep_all(self):
        block = self._block("vnote-geez")
        assert "word-break: keep-all" in block, (
            "φ.1: .vnote-geez must force breaks at explicit boundaries (U+1361 wordspace)"
        )

    def test_amharic_has_text_rendering(self):
        block = self._block("vnote-amharic")
        assert "text-rendering: optimizeLegibility" in block, (
            "φ.1: .vnote-amharic must declare text-rendering: optimizeLegibility"
        )

    def test_amharic_has_font_feature_settings(self):
        block = self._block("vnote-amharic")
        assert 'font-feature-settings: "kern", "liga"' in block

    def test_amharic_has_hyphens_none(self):
        block = self._block("vnote-amharic")
        assert "hyphens: none" in block

    def test_amharic_has_unicode_bidi_isolate(self):
        block = self._block("vnote-amharic")
        assert "unicode-bidi: isolate" in block

    def test_amharic_has_word_break_keep_all(self):
        block = self._block("vnote-amharic")
        assert "word-break: keep-all" in block

    def test_existing_ethiopic_font_stack_preserved(self):
        """The Π.0 font-family fallback chain must remain intact
        (regression-guard against typography work clobbering it)."""
        block = self._block("vnote-geez")
        assert "Noto Sans Ethiopic" in block
        assert "Abyssinica SIL" in block
        block_amh = self._block("vnote-amharic")
        assert "Noto Sans Ethiopic" in block_amh
        assert "Abyssinica SIL" in block_amh


# ──────────────────────────────────────────────────────────────────
# φ.1 — @font-face polish: font-display: swap + optional unicode-range
# ──────────────────────────────────────────────────────────────────


class TestPhi1FontFacePolish:
    """The @font-face emission loop in apply_style.py adds
    font-display: swap (both code paths) and supports an optional
    unicode_range per EMBED_FONT_PATHS entry."""

    APPLY_STYLE = REPO / "scripts" / "apply_style.py"

    def test_font_display_swap_in_legacy_path(self):
        src = self.APPLY_STYLE.read_text(encoding="utf-8")
        # Find the legacy EMBED_FONT_PATH block.
        legacy_idx = src.find("style_config.EMBED_FONT_PATH:")
        assert legacy_idx != -1, "Legacy EMBED_FONT_PATH code path must exist"
        # font-display: swap must appear in the source near the legacy block.
        # Allow looking forward up to ~600 chars to find the emitted CSS.
        tail = src[legacy_idx : legacy_idx + 800]
        assert "font-display: swap" in tail, "φ.1: legacy single-font @font-face must include font-display: swap"

    def test_font_display_swap_in_multi_path(self):
        src = self.APPLY_STYLE.read_text(encoding="utf-8")
        multi_idx = src.find('EMBED_FONT_PATHS", []) or [])')
        if multi_idx == -1:
            # Allow alternate ordering of args in the getattr call.
            multi_idx = src.find("EMBED_FONT_PATHS")
        assert multi_idx != -1, "Multi-font EMBED_FONT_PATHS code path must exist"
        tail = src[multi_idx : multi_idx + 1500]
        assert "font-display: swap" in tail, "φ.1: multi-font @font-face loop must include font-display: swap"

    def test_unicode_range_supported(self):
        src = self.APPLY_STYLE.read_text(encoding="utf-8")
        assert "unicode_range" in src, (
            "φ.1: apply_style.py must read entry.get('unicode_range') from EMBED_FONT_PATHS entries"
        )
        assert "unicode-range:" in src, (
            "φ.1: apply_style.py must emit unicode-range: <value> in @font-face when provided"
        )


# ──────────────────────────────────────────────────────────────────
# φ.1 — OPF font-manifest emission
# ──────────────────────────────────────────────────────────────────


class TestPhi1OpfFontManifest:
    """patch_opf_fonts() in build_edition.py registers EMBED_FONT_PATHS
    and legacy EMBED_FONT_PATH entries in content.opf manifest with
    correct media-type. Idempotent + no-op when both knobs empty."""

    BUILD_EDITION = REPO / "scripts" / "build_edition.py"

    def test_patch_opf_fonts_defined(self):
        src = self.BUILD_EDITION.read_text(encoding="utf-8")
        assert "def patch_opf_fonts(" in src, "φ.1: build_edition.py must define patch_opf_fonts()"

    def test_patch_opf_fonts_wired_into_build(self):
        src = self.BUILD_EDITION.read_text(encoding="utf-8")
        # The call must be inside the OPF patching block.
        assert "patch_opf_fonts(opf_text)" in src, (
            "φ.1: patch_opf_fonts() must be called on opf_text in the build pipeline"
        )

    def test_media_type_map_complete(self):
        from scripts.build_edition import _FONT_MEDIA_TYPES

        assert _FONT_MEDIA_TYPES[".ttf"] == "font/ttf"
        assert _FONT_MEDIA_TYPES[".otf"] == "application/vnd.ms-opentype"
        assert _FONT_MEDIA_TYPES[".woff"] == "font/woff"
        assert _FONT_MEDIA_TYPES[".woff2"] == "font/woff2"

    def test_noop_when_no_fonts(self, monkeypatch):
        """When EMBED_FONT_PATH is None AND EMBED_FONT_PATHS is empty,
        patch_opf_fonts() must return its input unchanged.
        v1.0 reproducibility guard."""
        from scripts import build_edition, style_config

        monkeypatch.setattr(style_config, "EMBED_FONT_PATH", None)
        monkeypatch.setattr(style_config, "EMBED_FONT_PATHS", [])

        sample = (
            '<?xml version="1.0"?>'
            "<package><manifest>"
            '<item id="x" href="x.html" media-type="application/xhtml+xml"/>'
            "</manifest></package>"
        )
        assert build_edition.patch_opf_fonts(sample) == sample

    def test_adds_ttf_manifest_entry(self, monkeypatch):
        from scripts import build_edition, style_config

        monkeypatch.setattr(style_config, "EMBED_FONT_PATH", None)
        monkeypatch.setattr(
            style_config,
            "EMBED_FONT_PATHS",
            [{"path": "fonts/NotoSansEthiopic-Regular.ttf", "family": "Noto Sans Ethiopic"}],
        )
        sample = '<package><manifest><item id="x" href="x.html"/></manifest></package>'
        result = build_edition.patch_opf_fonts(sample)
        assert 'href="fonts/NotoSansEthiopic-Regular.ttf"' in result
        assert 'media-type="font/ttf"' in result

    def test_idempotent_when_already_registered(self, monkeypatch):
        """A second call must not duplicate the manifest entry."""
        from scripts import build_edition, style_config

        monkeypatch.setattr(style_config, "EMBED_FONT_PATH", None)
        monkeypatch.setattr(
            style_config,
            "EMBED_FONT_PATHS",
            [{"path": "fonts/NotoSansEthiopic-Regular.ttf", "family": "Noto Sans Ethiopic"}],
        )
        sample = '<package><manifest><item id="x" href="x.html"/></manifest></package>'
        once = build_edition.patch_opf_fonts(sample)
        twice = build_edition.patch_opf_fonts(once)
        assert once.count('href="fonts/NotoSansEthiopic-Regular.ttf"') == 1
        assert twice.count('href="fonts/NotoSansEthiopic-Regular.ttf"') == 1
        assert once == twice

    def test_legacy_embed_font_path_registered(self, monkeypatch):
        """The legacy single-font EMBED_FONT_PATH must also land in
        the manifest when set."""
        from scripts import build_edition, style_config

        monkeypatch.setattr(style_config, "EMBED_FONT_PATH", "fonts/IMFellEnglish.otf")
        monkeypatch.setattr(style_config, "EMBED_FONT_FAMILY", "IM Fell English")
        monkeypatch.setattr(style_config, "EMBED_FONT_PATHS", [])
        sample = '<package><manifest><item id="x" href="x.html"/></manifest></package>'
        result = build_edition.patch_opf_fonts(sample)
        assert 'href="fonts/IMFellEnglish.otf"' in result
        assert 'media-type="application/vnd.ms-opentype"' in result


# ──────────────────────────────────────────────────────────────────
# φ.1 — fonts/README.md accurate workflow
# ──────────────────────────────────────────────────────────────────


class TestPhi1FontsReadmeAccurate:
    """The fonts/README.md was updated at φ.1 to document the actual
    apply_style + build_edition flow accurately. The 'already plumbed'
    misleading statement is removed; the φ.1 typography-polish + OPF-
    emission story is added."""

    README = REPO / "content" / "assets" / "fonts" / "README.md"

    def test_readme_mentions_phi1(self):
        body = self.README.read_text(encoding="utf-8")
        assert "φ.1" in body, "fonts/README.md must document the φ.1 ship"

    def test_readme_mentions_patch_opf_fonts(self):
        body = self.README.read_text(encoding="utf-8")
        assert "patch_opf_fonts" in body, "fonts/README.md must reference the φ.1 patch_opf_fonts() helper"

    def test_readme_mentions_font_display_swap(self):
        body = self.README.read_text(encoding="utf-8")
        assert "font-display: swap" in body, "fonts/README.md must document the φ.1 font-display: swap addition"

    def test_readme_lists_five_typography_refinements(self):
        body = self.README.read_text(encoding="utf-8")
        for needle in [
            "text-rendering: optimizeLegibility",
            "font-feature-settings",
            "hyphens: none",
            "unicode-bidi: isolate",
            "word-break: keep-all",
        ]:
            assert needle in body, f"fonts/README.md must document the φ.1 typography refinement: {needle}"

    def test_readme_documents_unicode_range(self):
        body = self.README.read_text(encoding="utf-8")
        assert "unicode_range" in body or "unicode-range" in body, (
            "fonts/README.md must document the φ.1 unicode_range knob"
        )

    def test_readme_already_plumbed_lie_removed(self):
        body = self.README.read_text(encoding="utf-8")
        # The pre-φ.1 README stated "already plumbed in apply_style.py"
        # which was inaccurate (the apply step doesn't auto-copy
        # content/assets/fonts/*.ttf into epub_working/fonts/). The
        # φ.1 ship removed that line.
        assert "already plumbed in `apply_style.py`" not in body, (
            "fonts/README.md must no longer claim the auto-copy is 'already plumbed' (Π.0 false statement)"
        )


# ──────────────────────────────────────────────────────────────────
# φ.1 — Π.0 + γ.4.8.E + τ.6.x.0a/b invariants regression-guarded
# ──────────────────────────────────────────────────────────────────


class TestPhi1ClosedArcInvariantPreservation:
    """φ.1 must not regress: Π.0.4 (EMBED_FONT_PATHS defaults to []),
    γ.4.8.E (Meqabyan 67/67), Meqabyan count ≥212, τ.6.x.0a +
    τ.6.x.0b translation-slot contracts."""

    def test_embed_font_paths_populated_at_rx_phase3(self):
        """RX Phase 3 (2026-06-05) MIGRATED this pin. φ.1's original
        invariant asserted EMBED_FONT_PATHS == [] (the Π.0 seed: infra
        committed, binaries not yet). RX Phase 3 deliberately enables
        original-language font embedding (device issue #7), so the list
        is now populated with the committed OFL fonts. The durable
        invariant is the MECHANISM (style_config drives patch_opf_fonts +
        @font-face), proven by test_font_embed.py — not the empty default.

        See `feedback_share_pin_pattern`: a pin may assert what HAS
        shipped, never what has NOT yet. The empty-default assertion is
        the latter once fonts ship, so it migrates to the populated state."""
        from scripts import style_config

        families = {e.get("family") for e in style_config.EMBED_FONT_PATHS}
        assert "Cardo" in families, (
            f"RX Phase 3: EMBED_FONT_PATHS must register Cardo; got {style_config.EMBED_FONT_PATHS}"
        )
        assert "Noto Serif Ethiopic" in families, (
            f"RX Phase 3: EMBED_FONT_PATHS must register Noto Serif Ethiopic; got {style_config.EMBED_FONT_PATHS}"
        )

    def test_embed_font_path_defaults_to_none(self):
        from scripts import style_config

        assert style_config.EMBED_FONT_PATH is None, (
            "φ.1: legacy EMBED_FONT_PATH must remain None in committed config (v1.0 reproducibility)"
        )

    def test_amharic_still_in_popup_languages(self):
        from scripts.build_edition import POPUP_LANGUAGES

        assert "amharic" in POPUP_LANGUAGES, "φ.1 must not regress Π.0.1: amharic must remain in POPUP_LANGUAGES"

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
                f"φ.1 must not regress γ.4.8.E arc-close {book} {total}/{total}"
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
        assert len(meq) >= 212, f"φ.1: Meqabyan count must remain ≥212; got {len(meq)}"

    def test_geez_tewahedo_still_gen_only(self):
        """τ.6.x.0a + τ.6.x.0b contract: no OCR ingest at φ.1."""
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
        `feedback_share_pin_pattern`. φ.1's original invariant
        (`files == ['gen.py']`) was the Π.0 seed state; τ.7.x.a + τ.7.x.b
        broke this exact assertion by expanding gen.py + adding ex.py.
        Durable invariant: gen.py is present in the amharic slot."""
        slot = REPO / "content" / "translations" / "amharic-tewahedo"
        files = sorted(p.name for p in slot.iterdir() if p.suffix == ".py")
        assert "gen.py" in files, f"φ.1: amharic-tewahedo must contain gen.py; got {files}"

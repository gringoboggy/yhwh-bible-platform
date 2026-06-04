"""Per-edition cover application — build_edition must swap the base master
cover (epub_working/cover.jpeg) for the edition's declared cover_image so each
built EPUB ships its own curated cover. Fixes visual-QA finding (b): the
editions declare distinct covers the build previously ignored. As of σ.5 all
11 editions declare a cover (9 curated + the 2 standalone Bibles' Ethiopic-
script covers); any edition that declares none keeps the master."""

from __future__ import annotations

import zipfile
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
COVERS = REPO / "content" / "covers"


class TestApplyEditionCover:
    def test_declared_cover_replaces_master(self, tmp_path):
        from scripts.build_edition import apply_edition_cover

        dst = tmp_path / "cover.jpeg"
        dst.write_bytes(b"MASTER-COVER-PLACEHOLDER")
        applied = apply_edition_cover({"cover_image": "covers/catholic-study.jpg"}, tmp_path)

        assert applied == "covers/catholic-study.jpg"
        assert dst.read_bytes() == (COVERS / "catholic-study.jpg").read_bytes()
        assert dst.read_bytes() != b"MASTER-COVER-PLACEHOLDER"

    def test_empty_cover_image_keeps_master(self, tmp_path):
        """Standalone bibles declare cover_image: '' — the master cover stays
        (back-compat: builds for editions without a cover are byte-identical)."""
        from scripts.build_edition import apply_edition_cover

        dst = tmp_path / "cover.jpeg"
        dst.write_bytes(b"MASTER-COVER-PLACEHOLDER")
        applied = apply_edition_cover({"cover_image": ""}, tmp_path)

        assert applied is None
        assert dst.read_bytes() == b"MASTER-COVER-PLACEHOLDER"

    def test_missing_cover_file_keeps_master(self, tmp_path):
        from scripts.build_edition import apply_edition_cover

        dst = tmp_path / "cover.jpeg"
        dst.write_bytes(b"MASTER-COVER-PLACEHOLDER")
        applied = apply_edition_cover({"cover_image": "covers/does-not-exist.jpg"}, tmp_path)

        assert applied is None
        assert dst.read_bytes() == b"MASTER-COVER-PLACEHOLDER"

    def test_no_cover_jpeg_in_build_dir_is_a_noop(self, tmp_path):
        """If the base has no cover.jpeg to replace, never create a stray one."""
        from scripts.build_edition import apply_edition_cover

        applied = apply_edition_cover({"cover_image": "covers/catholic-study.jpg"}, tmp_path)
        assert applied is None
        assert not (tmp_path / "cover.jpeg").exists()


class TestCoverReachesEpub:
    """The fix must reach the built EPUB: a declared cover edition's packaged
    cover.jpeg should be the edition's curated cover, not the master."""

    def test_declared_cover_build_ships_edition_cover(self, tmp_path, monkeypatch):
        import scripts.build_edition as be
        from scripts.core import build_cache

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)

        all_kinds = config.load_kinds()
        stats = be.build_one("catholic-study", tmp_path, "cover-test", all_kinds, force=True)
        epub = Path(stats["output_path"])
        assert epub.is_file()
        assert stats.get("cover_applied") == "covers/catholic-study.jpg"

        with zipfile.ZipFile(epub) as zf:
            cover_name = next(n for n in zf.namelist() if n.endswith("cover.jpeg"))
            epub_cover = zf.read(cover_name)

        assert epub_cover == (COVERS / "catholic-study.jpg").read_bytes()


class TestComposeCover:
    """σ.2 cover composition (2026-06-04): the cover carries a FIXED main title
    (default "HOLY BIBLE") + a small builder-chosen subtitle (the edition's
    display_name / title), drawn through an overflow-proof wrap-then-shrink
    fitter. The hard-coded per-edition title strings were dropped; the
    EDITION_TEMPLATES map keeps each edition's factory template."""

    def test_edition_templates_cover_all_nine(self):
        from scripts.generate_edition_covers import EDITION_TEMPLATES, STANDARD_EDITION_IDS

        # Each standard edition maps to a factory template stem.
        assert len(EDITION_TEMPLATES) == 9
        assert list(EDITION_TEMPLATES.keys()) == STANDARD_EDITION_IDS
        assert all(isinstance(stem, str) and stem for stem in EDITION_TEMPLATES.values())

    def test_compose_returns_final_dimensions(self):
        from scripts.generate_edition_covers import FINAL_HEIGHT, FINAL_WIDTH, _compose_cover

        img = _compose_cover("02_classical_corner_navy", "HOLY BIBLE", "The Catholic Study Bible")
        assert img.size == (FINAL_WIDTH, FINAL_HEIGHT)
        assert img.mode == "RGB"


class TestEthiopicCoverFont:
    """σ.5.1 — the 2 standalone Bibles get covers with Ethiopic-script main
    titles (መጽሐፍ ቅዱስ). The cover title font (FONT_TITLE_PATH = Times New Roman
    Bold) has NO Ethiopic coverage, so it would render tofu boxes — and tofu
    boxes have width, so fit_text_block can't catch them. _font_for_text must
    pick an Ethiopic-capable font for any text carrying Ethiopic codepoints.

    Tofu-detection signal (verified empirically): Times renders EVERY Ethiopic
    codepoint as the SAME .notdef box (identical getmask bbox); a real Ethiopic
    font renders DISTINCT, varied glyph bboxes per character."""

    SAMPLE = "መጽሐፍ ቅዱስ"  # "Holy Bible" in Ge'ez/Amharic — distinct Ethiopic glyphs

    def test_font_for_text_picks_ethiopic_for_ethiopic_text(self):
        from scripts.generate_edition_covers import FONT_TITLE_PATH, _font_for_text

        font = _font_for_text(self.SAMPLE, 72)
        # The selected font is NOT Times — it must be an Ethiopic-capable face.
        assert font.path != FONT_TITLE_PATH
        assert font.path.lower().endswith((".ttf", ".otf", ".ttc"))

    def test_font_for_text_keeps_times_for_latin_text(self):
        from scripts.generate_edition_covers import FONT_TITLE_PATH, _font_for_text

        font = _font_for_text("HOLY BIBLE", 72)
        # Latin text keeps the established Times look (byte-neutral for the 9).
        assert font.path == FONT_TITLE_PATH

    def test_ethiopic_font_renders_real_glyphs_not_tofu(self):
        """The chosen Ethiopic font must render DISTINCT glyphs for distinct
        Ethiopic codepoints. Tofu (a missing-glyph box) renders the same shape
        for every codepoint — so distinct, varied bboxes prove real coverage."""
        from scripts.generate_edition_covers import _font_for_text

        font = _font_for_text(self.SAMPLE, 72)
        ethiopic_chars = [c for c in self.SAMPLE if 0x1200 <= ord(c) <= 0x137F]
        assert len(ethiopic_chars) >= 4
        bboxes = []
        for c in ethiopic_chars:
            bbox = font.getmask(c).getbbox()
            assert bbox is not None, f"{c!r} rendered nothing (no ink at all)"
            bboxes.append(bbox)
        # Tofu = identical box for every char. Real coverage = varied bboxes.
        assert len(set(bboxes)) > 1, f"all Ethiopic glyphs share one bbox (tofu): {bboxes}"

    def test_compose_ethiopic_cover_has_ink_in_title_region(self, tmp_path):
        """Render-smoke: an Ethiopic-title cover must have non-background pixels
        in the title region (proves the glyphs actually drew, not silently
        skipped). Compare the title band against a plain template render."""
        from scripts.generate_edition_covers import TITLE_CENTER_Y, _compose_cover

        img = _compose_cover("05_missal_central_red", self.SAMPLE, "Ge'ez Tewahedo Bible")
        # Sample the cream title color (245,230,195) presence in the title band.
        from scripts.generate_edition_covers import TITLE_COLOR

        band = img.crop((150, TITLE_CENTER_Y - 120, img.width - 150, TITLE_CENTER_Y + 120)).convert("RGB")
        raw = band.tobytes()
        pixels = [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)]
        # Count pixels close to the warm-cream title color (the drawn glyphs).
        cream_hits = sum(
            1
            for r, g, b in pixels
            if abs(r - TITLE_COLOR[0]) < 30 and abs(g - TITLE_COLOR[1]) < 30 and abs(b - TITLE_COLOR[2]) < 30
        )
        assert cream_hits > 200, f"too little title ink in band ({cream_hits}px) — glyphs may not have drawn"

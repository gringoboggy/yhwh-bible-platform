"""RX Phase 3 — embed original-language fonts (fixes device issue #7).

Hebrew/Greek originals rendered tiny/tofu on Kobo (and any reader lacking
SBL Hebrew / SBL Greek); Ge'ez fidel had no embedded face at all. Phase 3
embeds OFL-licensed fonts so the scripts render legibly everywhere:

  - **Cardo** (David Perry, OFL 1.1) — Latin + Greek + Hebrew, three faces
    (Regular / Italic / Bold) — prepended to the .vnote-hebrew / .vnote-greek
    popup stacks.
  - **Noto Serif Ethiopic** (Google, OFL 1.1) — Ethiopic, unicode-range
    scoped to the Ethiopic blocks (base + Supplement + Extended + Extended-A)
    so it activates only for Ge'ez/Amharic (the standalone Ge'ez Bibles'
    body text) and never overrides Latin. Embedded as **ttf** — device-QA
    2026-06-09 (colour Kobo) showed tofu in the Ge'ez popups with the woff2
    embed. Root cause = the CONTAINER: Kobo's renderers support TTF/OTF/
    WOFF 1.0 but NOT woff2 (the woff2 carried the same full v2.102 face,
    Mac-lane cmap-verified; the Cardo ttf faces rendered fine).

The fonts are wired through ``style_config.EMBED_FONT_PATHS`` → the build's
``patch_opf_fonts`` (OPF manifest <item>) + the copytree of ``epub_working/``
(the bytes ship) + hand-authored ``@font-face`` rules in stylesheet.css.

This test pins the WIRING (config + CSS + bytes on disk) cheaply, then
proves end-to-end that a built EPUB actually CONTAINS the font bytes,
the OPF font <item>s, and the @font-face — exactly the shape epubcheck
needs (a CSS-referenced font missing from the zip or the manifest is an
epubcheck error, so this is the real proof the embed is correct).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EPUB_WORKING = REPO / "epub_working"
STYLESHEET = EPUB_WORKING / "stylesheet.css"

# The committed font files (full, un-subset) + their in-EPUB relative hrefs.
_FONT_FILES = [
    "Cardo-Regular.ttf",
    "Cardo-Italic.ttf",
    "Cardo-Bold.ttf",
    "NotoSerifEthiopic-Regular.ttf",
]

# Full Ethiopic coverage: all five blocks — base + Supplement + Extended +
# Extended-A + Extended-B, per the K② recipe (the font is cmap-verified
# glyph-backed in every one; the pre-device-QA embed was U+1200-137F only).
_ETHIOPIC_RANGE = "U+1200-137F, U+1380-139F, U+2D80-2DDF, U+AB00-AB2F, U+1E7E0-1E7FF"


class TestEmbedFontPathsConfig:
    """style_config.EMBED_FONT_PATHS registers the Phase-3 OFL fonts."""

    def test_registers_cardo_three_faces(self):
        from scripts import style_config

        cardo = [e for e in style_config.EMBED_FONT_PATHS if e.get("family") == "Cardo"]
        assert len(cardo) == 3, f"Cardo must be embedded in 3 faces (Reg/Ital/Bold); got {cardo}"
        paths = {e["path"] for e in cardo}
        assert paths == {
            "fonts/Cardo-Regular.ttf",
            "fonts/Cardo-Italic.ttf",
            "fonts/Cardo-Bold.ttf",
        }, f"Cardo face paths wrong: {paths}"
        # Italic + Bold faces must declare their style/weight so readers pick them.
        ital = next(e for e in cardo if e["path"].endswith("Italic.ttf"))
        bold = next(e for e in cardo if e["path"].endswith("Bold.ttf"))
        assert ital.get("style") == "italic"
        assert bold.get("weight") == "bold"

    def test_registers_noto_serif_ethiopic_scoped(self):
        from scripts import style_config

        noto = [e for e in style_config.EMBED_FONT_PATHS if e.get("family") == "Noto Serif Ethiopic"]
        assert len(noto) == 1, f"Noto Serif Ethiopic must be embedded once; got {noto}"
        entry = noto[0]
        # ttf, NOT woff2 — Kobo supports TTF/OTF/WOFF 1.0 containers only
        # (device-QA 2026-06-09: Ge'ez tofu in the kepub popups on woff2).
        assert entry["path"] == "fonts/NotoSerifEthiopic-Regular.ttf"
        # Scoped to the Ethiopic blocks so it never overrides Latin/Hebrew/Greek.
        assert entry.get("unicode_range") == _ETHIOPIC_RANGE, (
            f"Noto Serif Ethiopic must be unicode-range scoped to Ethiopic; got {entry}"
        )

    def test_font_bytes_present_under_epub_working(self):
        """patch_opf_fonts only registers the manifest <item>; the bytes
        ship because build copytree's epub_working/fonts/. Guard the bytes
        are actually there (a dangling <item> would be an epubcheck error)."""
        for fname in _FONT_FILES:
            f = EPUB_WORKING / "fonts" / fname
            assert f.is_file(), f"font byte missing from epub_working/fonts/: {fname}"
            assert f.stat().st_size > 10_000, f"font {fname} suspiciously small ({f.stat().st_size} B)"


class TestStylesheetFontFaceAndStacks:
    """The hand-authored @font-face rules + font-stack changes live in
    epub_working/stylesheet.css, OUTSIDE the apply_style.py managed region."""

    def _css(self) -> str:
        return STYLESHEET.read_text(encoding="utf-8")

    def test_font_face_for_each_embedded_file(self):
        css = self._css()
        for fname in _FONT_FILES:
            assert f'url("fonts/{fname}")' in css, f"@font-face src missing for {fname}"
        # Cardo family declared; Noto declared + unicode-range scoped.
        assert css.count('font-family: "Cardo"') >= 3, "Cardo needs a @font-face per face"
        assert 'font-family: "Noto Serif Ethiopic"' in css
        assert f"unicode-range: {_ETHIOPIC_RANGE}" in css, "Noto @font-face must be Ethiopic-scoped"
        assert "font-display: swap" in css, "@font-face should use font-display: swap"

    def test_font_face_is_outside_managed_region(self):
        css = self._css()
        begin = css.find("BEGIN apply_style.py managed region")
        end = css.find("END apply_style.py managed region")
        assert begin != -1 and end != -1, "managed-region sentinels must exist"
        managed = css[begin:end]
        # The @font-face rules must NOT be inside the managed block (we did
        # not run apply_style.py; its region is stale).
        assert "@font-face" not in managed, "@font-face must be authored OUTSIDE the managed region"

    def test_hebrew_stack_starts_with_cardo(self):
        css = self._css()
        idx = css.find(".vnote-hebrew {")
        assert idx != -1
        block = css[idx : css.find("}", idx)]
        fam = block[block.find("font-family:") :]
        assert fam.split(":", 1)[1].lstrip().startswith('"Cardo"'), (
            f".vnote-hebrew font stack must START with Cardo; got: {fam.splitlines()[0]}"
        )

    def test_greek_stack_starts_with_cardo(self):
        css = self._css()
        idx = css.find(".vnote-greek {")
        assert idx != -1
        block = css[idx : css.find("}", idx)]
        fam = block[block.find("font-family:") :]
        assert fam.split(":", 1)[1].lstrip().startswith('"Cardo"'), (
            f".vnote-greek font stack must START with Cardo; got: {fam.splitlines()[0]}"
        )

    def test_body_stack_includes_noto_serif_ethiopic(self):
        """The standalone Ge'ez body text renders via the body/verse-p stack
        (it has no .vnote-geez class); Noto must lead there for fidel."""
        css = self._css()
        idx = css.find("body, body.bible-body, p, p.verse-p")
        assert idx != -1, "body typography stack rule must exist"
        block = css[idx : css.find("}", idx)]
        assert '"Noto Serif Ethiopic"' in block, (
            "body/verse-p stack must include Noto Serif Ethiopic for Ge'ez body text"
        )


class TestStandaloneFontWiring:
    """build_standalone must call patch_opf_fonts so the standalone OPF
    manifest declares the CSS-referenced fonts (otherwise epubcheck flags
    a resource referenced-but-not-declared)."""

    def test_build_standalone_calls_patch_opf_fonts(self):
        src = (REPO / "scripts" / "build_standalone.py").read_text(encoding="utf-8")
        assert "patch_opf_fonts" in src, (
            "build_standalone must register the embedded fonts in the standalone OPF "
            "(be.patch_opf_fonts) or epubcheck flags the @font-face url() as undeclared"
        )


class TestBuiltEpubContainsFonts:
    """End-to-end proof: a built EPUB actually carries the font BYTES, the
    OPF font <item> entries (correct media-type), and the @font-face — the
    exact shape epubcheck validates."""

    EDITION = "ethiopian-tewahedo"

    def test_fonts_ship_in_built_epub(self, tmp_path, monkeypatch):
        import scripts.build_edition as be
        from scripts.core import build_cache, config

        # Hermetic — never touch the persistent build cache (always rebuild).
        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)

        assert self.EDITION in config.editions_by_id()
        all_kinds = config.load_kinds()
        stats = be.build_one(self.EDITION, tmp_path, "font-test", all_kinds, force=True)

        epub = Path(stats["output_path"])
        assert epub.is_file(), "build_one reported success but no EPUB landed on disk"

        with zipfile.ZipFile(epub) as zf:
            assert zf.testzip() is None, "corrupt EPUB zip"
            names = zf.namelist()

            # (a) the font BYTES are in the zip (under a fonts/ path).
            for fname in _FONT_FILES:
                hits = [n for n in names if n.endswith(f"fonts/{fname}") or n.endswith(fname)]
                assert hits, f"font byte missing from built EPUB: {fname}"
                data = zf.read(hits[0])
                assert len(data) > 10_000, f"embedded {fname} truncated ({len(data)} B)"

            # (b) the OPF declares each font as a <item> with a font media-type.
            opf_name = next(n for n in names if n.endswith("content.opf"))
            opf = zf.read(opf_name).decode("utf-8")
            assert 'href="fonts/Cardo-Regular.ttf"' in opf and 'media-type="font/ttf"' in opf, (
                "OPF must declare Cardo-Regular.ttf as a font/ttf item"
            )
            assert 'href="fonts/Cardo-Italic.ttf"' in opf
            assert 'href="fonts/Cardo-Bold.ttf"' in opf
            # Pin the full item shape (href AND media-type on THIS item) — the
            # whole-OPF 'media-type="font/ttf"' check above is already satisfied
            # by the Cardo items, so it cannot vouch for the Noto entry.
            assert 'href="fonts/NotoSerifEthiopic-Regular.ttf" media-type="font/ttf"' in opf, (
                "OPF must declare NotoSerifEthiopic-Regular.ttf as a font/ttf item"
            )
            assert 'href="fonts/NotoSerifEthiopic-Regular.woff2"' not in opf, (
                "the woff2 embed must be fully retired (Kobo woff2-flaky)"
            )

            # (c) the @font-face for Cardo + the popup stacks are in the stylesheet.
            css_name = next(n for n in names if n.endswith("stylesheet.css"))
            css = zf.read(css_name).decode("utf-8")
            assert "@font-face" in css and 'font-family: "Cardo"' in css
            assert 'url("fonts/Cardo-Regular.ttf")' in css
            hidx = css.find(".vnote-hebrew {")
            gidx = css.find(".vnote-greek {")
            assert hidx != -1 and gidx != -1
            hblock = css[hidx : css.find("}", hidx)]
            gblock = css[gidx : css.find("}", gidx)]
            assert '"Cardo"' in hblock.split("font-family:", 1)[1].split("\n", 1)[0]
            assert '"Cardo"' in gblock.split("font-family:", 1)[1].split("\n", 1)[0]

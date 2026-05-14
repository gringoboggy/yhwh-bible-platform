# Embedded fonts for EPUB builds

Each font in this directory is embedded by `scripts/apply_style.py` and
referenced by the per-edition CSS via the legacy
`style_config.EMBED_FONT_PATH` knob and/or the Π.0 `EMBED_FONT_PATHS` list.

## Current state (post-Π.0, 2026-05-14)

This directory contains the **slot** for embedded fonts but does NOT
yet contain the Ethiopic font binary needed by the parallel-Bible
expansion (Π.1 / τ.6.x / Π.2). The font binary is staged but not
committed because:

1. The OFL font file is ~400 KB — committing it requires explicit
   publisher authorization (per `dev/CLAUDE_PROJECT_RULES.md` on
   binary asset additions).
2. The Π.0 phase ships infrastructure-only; no production EPUB
   currently surfaces Ge'ez or Amharic popup data, so the font is
   not yet load-bearing.
3. The Ethiopic CSS fallback chain in
   `scripts/apply_style.py::.vnote-geez / .vnote-amharic` falls
   through to reader-supplied Ethiopic fonts (Noto Sans Ethiopic
   on most modern OSes; Abyssinica SIL / Nyala / Kefa / Ethiopia
   Jiret as further fallbacks). This is acceptable for Π.0 testing.

## Adding the Ethiopic font binary (at τ.6.x or Π.2 ship time)

1. Download **Noto Sans Ethiopic** from
   https://fonts.google.com/noto/specimen/Noto+Sans+Ethiopic
   or directly from the Google Fonts GitHub mirror:
   https://github.com/notofonts/noto-fonts/tree/main/hinted/ttf/NotoSansEthiopic
2. Place the binary at:
   `content/assets/fonts/NotoSansEthiopic-Regular.ttf`
   (and optionally `NotoSansEthiopic-Bold.ttf`).
3. Verify the OFL license file at:
   `content/assets/fonts/LICENSES.md`
   includes the full OFL 1.1 text for Noto Sans Ethiopic.
4. Edit `scripts/style_config.py` to register the binary:
   ```python
   EMBED_FONT_PATHS = [
       {"path": "fonts/NotoSansEthiopic-Regular.ttf",
        "family": "Noto Sans Ethiopic",
        "unicode_range": "U+1200-137F, U+1380-139F, U+2D80-2DDF, U+AB00-AB2F"},
       # optionally bold:
       # {"path": "fonts/NotoSansEthiopic-Bold.ttf",
       #  "family": "Noto Sans Ethiopic",
       #  "weight": "bold"},
   ]
   ```
   The `unicode_range` knob (added at φ.1, 2026-05-14) is optional
   and scopes the font's activation to Ethiopic codepoints so non-
   Ethiopic text doesn't activate the embedded font. The path is
   relative to `epub_working/`; the operator drops the font file
   at `epub_working/fonts/<name>.ttf` before running
   `apply_style.py`. (At Π.0 ship time, the apply step does NOT
   yet auto-copy `content/assets/fonts/*.ttf` into
   `epub_working/fonts/*.ttf` — that step is still operator-
   driven; this is a known gap flagged for a future hygiene ship.)
5. Run `python scripts/apply_style.py` — this emits the
   `@font-face` rules in `stylesheet.css`. φ.1 (2026-05-14) added
   `font-display: swap` to every `@font-face` rule so the reader
   renders fallback text immediately rather than blocking on the
   embedded download.
6. Run the ethiopian-tewahedo SKU build:
   `python scripts/build_edition.py ethiopian-tewahedo`.
   The build's `patch_opf_fonts()` step (added at φ.1) registers
   each EMBED_FONT_PATHS entry — plus the legacy EMBED_FONT_PATH
   knob — in `content.opf` manifest with the correct media-type
   (`font/ttf` for .ttf; `application/vnd.ms-opentype` for .otf;
   `font/woff` / `font/woff2` for .woff / .woff2). The patch is
   idempotent (skips entries already registered) and is a no-op
   when both knobs are empty (preserves v1.0 byte-identical
   reproducibility).
7. Run epubcheck on the produced EPUB and verify the font item
   is registered correctly with no manifest warnings.
8. Visual-QA on Kindle Paperwhite / Apple Books / Calibre / Adobe
   Digital Editions / Kobo. Per φ.1 §3 exit criteria, Ethiopic
   must render correctly on all 5 platforms.

## φ.1 typography polish (2026-05-14)

The `.vnote-geez` and `.vnote-amharic` CSS classes were polished
at φ.1 with five Ethiopic-aware refinements:

- `text-rendering: optimizeLegibility` — fonts with full glyph
  coverage participate in proper kerning + ligatures (important
  for Ethiopic syllabaries where vowel-bearing fidel are pre-
  composed).
- `font-feature-settings: "kern", "liga"` — enables OpenType
  kerning + standard ligatures (no-op on fallback fonts without
  the features; necessary on Noto Sans Ethiopic for correct
  fidel spacing).
- `hyphens: none` — Ethiopic does not hyphenate word-breaks the
  way Latin does; explicitly disable browser auto-hyphenation
  guesses.
- `unicode-bidi: isolate` — defensive isolation for the rare cases
  when an Ethiopic line embeds Latin or Arabic-numeral content;
  prevents bidirectional reorderings from spilling outside the
  popup.
- `word-break: keep-all` — Ethiopic word-spacing relies on the
  wordspace ፡ (U+1361); browser-default break-anywhere can split
  syllables; keep-all forces breaks at explicit word boundaries
  only.

## License compliance

All embedded fonts MUST be redistributable. Default policy:
**SIL Open Font License 1.1 (OFL) only**. Other licenses require
explicit publisher review and `dev/CLAUDE_PROJECT_RULES.md`
documentation.

License texts live in `LICENSES.md` in this directory.

---

*This README is part of the Π.0 infrastructure scaffolding for
the parallel-Bible expansion, extended at φ.1 (2026-05-14) with
typography-polish + OPF-emission documentation.
CC0 1.0 Universal.*

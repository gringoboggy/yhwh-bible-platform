# Embedded fonts for EPUB builds

The fonts in this directory ship inside every built EPUB. They are
registered in `scripts/style_config.py::EMBED_FONT_PATHS`; the build's
`patch_opf_fonts()` step (added at φ.1) registers each entry in the
`content.opf` manifest with the correct media-type (`font/ttf` for .ttf;
`application/vnd.ms-opentype` for .otf; `font/woff` for .woff), and the
build's copytree of `epub_working/` ships the bytes (a twin copy of each
binary lives at `epub_working/fonts/`). The matching `@font-face` rules
are hand-authored in `epub_working/stylesheet.css` — **outside** the
`apply_style.py` managed region. Do NOT run `apply_style.py`; its managed
region is stale (see the warning in `style_config.py`).

## Current state (2026-06-09, post device-QA K②)

This directory contains the SHIPPED embed set:

- **Cardo** (David Perry, OFL 1.1) — Latin + Greek + Hebrew; three faces
  (`Cardo-Regular.ttf` / `Cardo-Italic.ttf` / `Cardo-Bold.ttf`). Leads the
  `.vnote-hebrew` / `.vnote-greek` popup stacks; no unicode-range, so it
  is a general serif available to any stack that names it.
- **Noto Serif Ethiopic** (Google, OFL 1.1) —
  `NotoSerifEthiopic-Regular.ttf`, the notofonts ethiopic release
  v2.102 full/ttf static build (384 KB, hinted). Embedded as **ttf, not
  woff2**: device-QA 2026-06-09 (colour Kobo) showed Ge'ez tofu with the
  earlier woff2 embed — the root cause is the CONTAINER (Kobo supports
  TTF/OTF/WOFF 1.0, not woff2; the woff2 carried the same full face,
  cmap-verified). Scoped via the `unicode_range` knob (added at φ.1) to
  all five Ethiopic blocks — base + Supplement + Extended + Extended-A +
  Extended-B (`U+1200-137F, U+1380-139F, U+2D80-2DDF, U+AB00-AB2F,
  U+1E7E0-1E7FF`; the font is glyph-backed in every one) — so it only
  activates for Ge'ez/Amharic codepoints and never overrides
  Latin/Hebrew/Greek text.

Every `@font-face` rule carries `font-display: swap` (φ.1) so readers
render fallback text immediately rather than blocking on the embedded
font. Full (un-subset) binaries are embedded deliberately — subsetting
would add a `fonttools` dependency for ~1.4 MB of savings against a
~25 MB Bible.

## Changing the embed set

1. The binary must be OFL-licensed (see License compliance below); add
   its license text to `LICENSES.md` and the provenance line to the
   repo-root `ATTRIBUTIONS.md`.
2. Drop the file BOTH here and at `epub_working/fonts/<name>.ttf`
   (byte-identical copies — `tests/test_font_embed.py` guards presence).
3. Register it in `style_config.py::EMBED_FONT_PATHS` (path relative to
   `epub_working/`; optional `weight`/`style`/`unicode_range` knobs).
4. Hand-author the `@font-face` rule in `epub_working/stylesheet.css`
   (outside the managed region), mirroring the EMBED_FONT_PATHS entry.
5. Build any edition and run epubcheck — `patch_opf_fonts()` is
   idempotent (skips already-registered hrefs) and a no-op when the list
   is empty; a CSS-referenced font missing from the zip or manifest is
   an epubcheck error, and `tests/test_font_embed.py` proves the full
   chain end-to-end inside a real built EPUB.

## φ.1 typography polish (2026-05-14)

The `.vnote-geez` and `.vnote-amharic` CSS classes were polished
at φ.1 with five Ethiopic-aware refinements:

- `text-rendering: optimizeLegibility` — fonts with full glyph
  coverage participate in proper kerning + ligatures (important
  for Ethiopic syllabaries where vowel-bearing fidel are pre-
  composed).
- `font-feature-settings: "kern", "liga"` — enables OpenType
  kerning + standard ligatures (no-op on fallback fonts without
  the features; necessary for correct fidel spacing).
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

*Scaffolded at Π.0 for the parallel-Bible expansion; extended at φ.1
(2026-05-14) with typography polish + OPF emission; re-trued 2026-06-09
when the Ethiopic embed shipped for real (device-QA K② ttf swap).
CC0 1.0 Universal.*

# Font licenses

All fonts embedded by the EPUB build pipeline must be re-
distributable. This file is the project's font-license register.

## Current state (post-RX-Phase-3, 2026-06-05)

The EPUB build now embeds two OFL 1.1 font families in every edition
(full, un-subset — `fonttools` is not installed and the size cost is
negligible against the ~99 MB baseline). The committed binaries and
their license declarations:

- **Cardo** (David J. Perry, OFL 1.1) — `Cardo-Regular.ttf`,
  `Cardo-Italic.ttf`, `Cardo-Bold.ttf`. Latin + Greek + Hebrew; powers
  the `.vnote-hebrew` / `.vnote-greek` original-language popups.
- **Noto Serif Ethiopic** (Google, OFL 1.1) —
  `NotoSerifEthiopic-Regular.woff2`. Ethiopic syllabary; `@font-face`
  is `unicode-range`-scoped to U+1200–137F (Ge'ez/Amharic only).

These are registered in `style_config.EMBED_FONT_PATHS`, copied into
`epub_working/fonts/`, declared in each EPUB's OPF manifest by
`build_edition.patch_opf_fonts()`, and referenced by hand-authored
`@font-face` rules in `epub_working/stylesheet.css`.

---

## Cardo — SIL Open Font License 1.1 (OFL)

**Files:**
- `Cardo-Regular.ttf`
- `Cardo-Italic.ttf`
- `Cardo-Bold.ttf`

**Source:** https://software.sil.org/cardo/ (also on Google Fonts)
**Designer:** David J. Perry
**License:** SIL Open Font License (OFL) 1.1

Cardo is a scholarly serif designed for classical, biblical, and
medieval studies. It covers Latin, polytonic Greek, and Hebrew
(including vowel-pointing), making it the single embedded face that
guarantees a legible glyph for the Hebrew/Greek original-language
popups on readers (e.g. Kobo) that lack SBL Hebrew / SBL Greek.

**Full OFL 1.1 text:** see https://scripts.sil.org/OFL_web

---

## Noto Serif Ethiopic — SIL Open Font License 1.1 (OFL)

**Files:**
- `NotoSerifEthiopic-Regular.woff2`
- `NotoSerifEthiopic-Regular.ttf` — the SAME font (v2.102, full, 589
  glyphs / 528 codepoints), produced by losslessly decompressing the
  woff2 container (`fontTools.ttLib` flavor strip; cmap verified
  identical). Added 2026-06-09 for the EPUB embed: Kobo's renderers
  support TTF/OTF/WOFF 1.0 but NOT woff2 (Ge'ez popups rendered tofu
  on the colour-Kobo device test).

**Source:** https://fonts.google.com/noto/specimen/Noto+Serif+Ethiopic
**Designer/Publisher:** Google Inc., Noto Project
**License:** SIL Open Font License (OFL) 1.1

Replaces the earlier intended *Noto Sans Ethiopic* (the serif form
matches the project's serif body stack). Its `@font-face` is
`unicode-range`-scoped to U+1200–137F so it activates only for
Ge'ez/Amharic fidel and never overrides Latin/Hebrew/Greek text.

**Full OFL 1.1 text:** see https://scripts.sil.org/OFL_web

---

## Noto Sans Ethiopic — SIL Open Font License 1.1 (OFL)

**Files (to be added at τ.6.x / Π.2):**
- `NotoSansEthiopic-Regular.ttf`
- `NotoSansEthiopic-Bold.ttf` (optional)

**Source:** https://fonts.google.com/noto/specimen/Noto+Sans+Ethiopic
**Designer/Publisher:** Google Inc., Noto Project
**License:** SIL Open Font License (OFL) 1.1

The OFL license permits embedding the font in document containers
(including EPUB) without restriction and grants the right to
modify the font provided the modified version is renamed and
distributed under the same OFL terms.

**Full OFL 1.1 text:** see https://scripts.sil.org/OFL_web

The OFL is verified compatible with EPUB 3.0 and 3.2 packaging,
Kindle KFX, and Apple Books. No additional notice or attribution
is required inside the EPUB itself; this register satisfies the
OFL's "all parties of this Font Software" attribution requirement
for the project's own use.

---

## IM Fell English (currently embedded if EMBED_FONT_PATH is set)

**Files (currently optional, EMBED_FONT_PATH default is None):**
- `fonts/IMFellEnglish.otf`

**License:** Public Domain (IM Fell type, original ~1670, revived
by Igino Marini)

---

*License register compiled 2026-05-14 (Π.0 infrastructure
scaffolding). New fonts added at τ.6.x / Π.2 must add their
full license declaration to this file before the binary is
committed. CC0 1.0 Universal on this register file itself.*

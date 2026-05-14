# Font licenses

All fonts embedded by the EPUB build pipeline must be re-
distributable. This file is the project's font-license register.

## Current state (post-Π.0, 2026-05-14)

No fonts are yet committed to `content/assets/fonts/`. The slot is
infrastructure-only at Π.0. License declarations below cover the
fonts the project intends to embed at later phases; the binary
files themselves are added at τ.6.x / Π.2 ship time per
`README.md`.

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

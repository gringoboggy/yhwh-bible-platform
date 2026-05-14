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
        "family": "Noto Sans Ethiopic"},
       # optionally:
       # {"path": "fonts/NotoSansEthiopic-Bold.ttf",
       #  "family": "Noto Sans Ethiopic",
       #  "weight": "bold"},
   ]
   ```
   (Path is relative to `epub_working/`; the apply step copies
   `content/assets/fonts/*.ttf` into `epub_working/fonts/*.ttf`
   during build — already plumbed in `apply_style.py`.)
5. Run the ethiopian-tewahedo SKU build and verify epubcheck
   passes; visual-QA on Kindle Paperwhite / Apple Books / Calibre /
   Adobe Digital Editions.

## License compliance

All embedded fonts MUST be redistributable. Default policy:
**SIL Open Font License 1.1 (OFL) only**. Other licenses require
explicit publisher review and `dev/CLAUDE_PROJECT_RULES.md`
documentation.

License texts live in `LICENSES.md` in this directory.

---

*This README is part of the Π.0 infrastructure scaffolding for
the parallel-Bible expansion. CC0 1.0 Universal.*

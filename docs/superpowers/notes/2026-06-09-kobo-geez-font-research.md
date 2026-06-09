# Kobo Ge'ez tofu (device-QA K②, crops kobo3/kobo5) — woff2 vs ttf research + the ready-to-swap ttf

_Mac, turn 56, 2026-06-09. Laundry #4 of the turn-54 board: the colour-Kobo device test showed
tofu for Ge'ez in the note popups while the same EPUB's Cardo (Latin/Greek/Hebrew, ttf) rendered
fine. The EPUB embeds Noto Serif Ethiopic as **woff2** with `unicode-range: U+1200-137F`. Two
suspects: the container format and the range. Verdict below; WIN's swap is prepped first-try._

## TL;DR for WIN

**Root cause = the woff2 container, full stop.** Kobo does not support woff2 in either renderer.
The unicode-range is NOT the tofu cause (every Ge'ez codepoint the EPUB ships is inside
U+1200-137F), but widen it anyway while you're in the file (future-proofs the standalone
Ge'ez/Amharic Bibles; exact value below, already device-format-tested).

**The ttf is ready and committed: `content/assets/fonts/NotoSerifEthiopic-Regular.ttf`** (240 KB).
It is NOT a download — it is the shipped woff2 losslessly decompressed (fontTools flavor-strip),
so the glyph data is provenance-identical to what every other surface already QA'd:
**v2.102 = the current upstream release** (notofonts/ethiopic `NotoSerifEthiopic-v2.102`),
**589 glyphs / 528 mapped codepoints, cmap verified identical to the woff2**, valid TrueType
(18 tables). All 74 Ge'ez chars the EPUB uses render 74 distinct non-blank glyphs (Pillow
bitmap-hash proof — no tofu, no blanks).

### The swap (3 file edits + 1 copy, then rebuild + kepubify)

1. `cp content/assets/fonts/NotoSerifEthiopic-Regular.ttf epub_working/fonts/` and
   `git rm epub_working/fonts/NotoSerifEthiopic-Regular.woff2` (an unreferenced leftover would
   ship unmanifested → epubcheck noise).
2. `scripts/style_config.py` `EMBED_FONT_PATHS` (≈:101): `"path": "fonts/NotoSerifEthiopic-Regular.ttf"`
   and `"unicode_range": "U+1200-139F, U+2D80-2DDF, U+AB00-AB2F, U+1E7E0-1E7FF"`.
3. `epub_working/stylesheet.css` :41 `src: url("fonts/NotoSerifEthiopic-Regular.ttf");` and
   :45 `unicode-range: U+1200-139F, U+2D80-2DDF, U+AB00-AB2F, U+1E7E0-1E7FF;`.
4. Stale-comment sweep (same class as your 5508207a fix): `epub_working/stylesheet.css` :351
   ("unicode-range-scoped to U+1200-137F") + the style_config block comment ≈:80 ("scoped via
   unicode_range to U+1200–137F") + content/assets/fonts/LICENSES.md (already updated by Mac).
   `patch_opf_fonts()` keys off the url() target, so the OPF `media-type="font/ttf"` follows
   automatically — verified below.

`content/assets/fonts/LICENSES.md` + the README provenance are already updated (Mac, this turn).
The **website keeps its woff2** (`website/fonts/noto-serif-ethiopic-…woff2`) — browsers prefer
woff2; this swap is EPUB-only.

## Evidence

### 1. Kobo font-format support (the authoritative source)

[kobolabs/epub-spec](https://github.com/kobolabs/epub-spec) (Kobo's own platform spec):
**"TTF, OTF, and WOFF (v. 1.0) fonts are supported by all Kobo platforms."** woff2 is absent —
across all five platforms (eInk / Desktop / Android / iOS / Web Reader), with no kepub-vs-epub
carve-out. Corroborating: the device itself is the experiment — Cardo (**ttf**, identical
`@font-face` mechanism, same stylesheet) renders perfectly on the same colour Kobo where the
woff2 Ethiopic face tofus; and Kobo's user-font sideload path documents ttf/otf only
([Kobo help](https://help.kobo.com/hc/en-us/articles/13009477876631-Load-fonts-onto-your-Kobo-eReader)).
The kepub WebKit renderer is the relevant one for our `.kepub.epub` artifact; RMSDK (plain epub)
is stricter still — ttf/otf is the only embed format safe for both.

### 2. The shipped woff2 was already the FULL font (subsetting theory dead)

`epub_working/fonts/NotoSerifEthiopic-Regular.woff2` (49,732 B — small because woff2 compresses
hard, not because it's subset): name table = "Noto Serif Ethiopic" **Version 2.102**;
589 glyphs; 528 mapped codepoints spanning Ethiopic (358), Supplement (26), Extended (79),
Extended-A (32), Extended-B (28) + minimal Latin. The `style_config.py` "Full (un-subset) fonts
are embedded deliberately" comment is **correct**. Upstream latest release is the same v2.102 —
no version bump available or needed.

### 3. unicode-range: sufficient today, widened for tomorrow

Scan of the actual device-QA EPUB (`build/m2/…155343Z.epub`, every html/css/opf/ncx):
**74 distinct Ethiopic codepoints, ALL inside U+1200-137F** (min U+1201, max U+1365 ፥).
So the narrow range did not cause the tofu. Widening to
`U+1200-139F, U+2D80-2DDF, U+AB00-AB2F, U+1E7E0-1E7FF` costs nothing (a unicode-range only
activates when content hits it), matches the font's real coverage (it HAS glyphs in all five
blocks), and pre-clears the standalone Ge'ez/Amharic Bibles (gemination marks U+135D-135F and
Ethiopic punctuation U+1360-1368 were already in-range; the Supplement/Extended blocks cover
Sebatbeit/Me'en/Bilen extensions and archaic labialized series).

### 4. The full swap was test-built end-to-end (this is why it's "first-try")

On a COPY of the device-QA EPUB (`/tmp/kobo-font-test/`, repo untouched), Mac performed exactly
the swap above, repackaged, and converted:

- **kepubify v4.0.4: `1 converted, 0 errored`** → `eth-ttf-test.kepub.epub`.
- The kepub ships `fonts/NotoSerifEthiopic-Regular.ttf`, OPF
  `<item id="font-notoserifethiopic-regular" href="fonts/NotoSerifEthiopic-Regular.ttf"
  media-type="font/ttf"/>`, and the @font-face with the widened range — all survive the
  koboSpan transform.
- **Note wiring unchanged**: `epub:type="footnote"` 66,683 + `noteref` 66,498 — byte-equal
  counts across original epub → swapped epub → kepub (single counting method). (The "66,684"
  in earlier notes was a counting-variant artifact, not a real delta.)
- **epubcheck 3.3 on the swapped EPUB: 0 fatals / 0 errors / 0 warnings / 0 infos.**
- **Glyph proof**: all 74 used chars render distinct, non-blank bitmaps from the ttf; sample
  render `/tmp/kobo-font-test/geez-ttf-render.png` (መቃብያንን) eyeballed = real fidel.

### What this does NOT prove

Only the real device proves the popup renders fidel on Kobo (firmware quirks). But every
self-serviceable link in the chain — format support per Kobo's spec, the Cardo control
experiment, font integrity, the swap mechanics, kepub survival, package validity — is green.
Re-test on the colour Kobo lands in WIN's one-rebuild batch (K① gap + K② this + K③ title-bleed).

Sources:
- https://github.com/kobolabs/epub-spec (TTF/OTF/WOFF-1.0 list)
- https://help.kobo.com/hc/en-us/articles/13009477876631-Load-fonts-onto-your-Kobo-eReader
- https://github.com/notofonts/ethiopic/releases (NotoSerifEthiopic-v2.102 = current)
- https://www.kobo.com/kobo-writing-life/blog/embedding-fonts-in-your-ebooks

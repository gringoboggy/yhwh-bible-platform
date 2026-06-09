#!/usr/bin/env python3
"""
style_config.py — Single source of truth for EPUB-wide style knobs.

Edit this file, then run ``scripts/apply_style.py`` to regenerate the EPUB
stylesheet, navigation, and visible Table of Contents to match. The settings
here intentionally cover only the things a non-developer would care about
(margins, font, page-flow, TOC layout); fine-grained CSS lives in
``epub_working/stylesheet.css`` and is preserved by the apply script.
"""

# ---------------------------------------------------------------------------
# Body / typography
# ---------------------------------------------------------------------------

# Side margin between text and screen edge. CSS unit (em is recommended).
# 1em ≈ default reader margin; 0.4em ≈ a study-Bible feel; 0.2em is almost
# edge-to-edge. Some readers (e.g. Apple Books) override this with their own term-ref-ok
# slider; we set the default the EPUB ships with.
MARGIN_SIDE = "0.4em"

# Font stack. The reader picks the first font it can find. Most readers do
# NOT have these fonts installed — they fall through to the system serif.
# Picking the stack above lets readers that DO have these (Calibre, KOReader
# with packs) render with the desired aesthetic. To force the look, set
# EMBED_FONT_PATH below.
FONT_STACK = (
    '"IM Fell English", "Goudy Bookletter 1911", "Sorts Mill Goudy", '
    '"Cardo", "EB Garamond", "Crimson Text", "Palatino Linotype", '
    'Palatino, Georgia, "Times New Roman", serif'
)

# Optional font embedding. If set to a relative path inside ``epub_working/``
# (e.g. ``"fonts/IMFellEnglish.otf"``), the apply script registers the file
# in content.opf and emits a matching ``@font-face`` rule. Leave None to
# rely on system fonts only.
#
# Legacy single-font knobs (preserved for back-compat with v1.0 builds):
EMBED_FONT_PATH = None
EMBED_FONT_FAMILY = "IM Fell English"  # used as @font-face family name

# Π.0 (2026-05-14) — multi-font embed list for parallel-Bible support.
#
# Each entry is a dict: {"path": "fonts/<file>.ttf", "family": "<Family Name>"}
# - "path" is relative to ``epub_working/``.
# - "family" is the CSS font-family name used in @font-face.
#
# At build time apply_style.py concatenates the legacy single-font knob
# (if set) with EMBED_FONT_PATHS. Both code paths emit @font-face rules
# and register the files in content.opf. v1.0-tagged builds use only the
# legacy single-font knob — EMBED_FONT_PATHS defaults to [] so existing
# behavior is unchanged.
#
# Recommended use at τ.6.x / Π.1 / Π.2 ship time, when Ethiopic font
# binary lands at content/themes/<theme>/fonts/NotoSansEthiopic-Regular.ttf:
#
#     EMBED_FONT_PATHS = [
#         {"path": "fonts/NotoSansEthiopic-Regular.ttf",
#          "family": "Noto Sans Ethiopic"},
#     ]
#
# Π.0 itself did NOT enable embedding (font binaries were staged for
# download but not committed).
#
# Phase 3 (RX overhaul, 2026-06-05) — original-language font embedding.
# Fixes device issue #7 (Hebrew/Greek render tiny/tofu on Kobo and any
# reader lacking those scripts). The OFL fonts now live committed under
# ``content/assets/fonts/`` AND are copied into ``epub_working/fonts/``
# (the build's ``shutil.copytree(EPUB_DIR, tmp)`` ships everything under
# epub_working/, and patch_opf_fonts registers each href in the OPF
# manifest, so the bytes + the manifest <item> + the @font-face all line
# up — no epubcheck RSC-008/OPF dangling-resource error).
#
#   - **Cardo** (David Perry, OFL 1.1) covers Latin + Greek + **Hebrew**;
#     embedded in 3 weights/styles (Regular / Italic / Bold) so the
#     ``.vnote-hebrew`` / ``.vnote-greek`` original-language popups have a
#     guaranteed glyph everywhere. No unicode-range → Cardo is a general
#     serif available to every stack that names it.
#   - **Noto Serif Ethiopic** (Google, OFL 1.1) covers the Ethiopic
#     syllabary; scoped via ``unicode_range`` to U+1200–137F so it only
#     activates for Ge'ez/Amharic codepoints. Safe to ship in every
#     edition (it never overrides Latin/Hebrew/Greek text); the standalone
#     Ge'ez Bibles get legible fidel without any per-edition wiring.
#
# Full (un-subset) fonts are embedded deliberately — ``fonttools`` is not
# installed, and +~1.4 MB is negligible against the ~99 MB baseline while
# avoiding an undeclared dependency install.
#
# The matching @font-face rules live in epub_working/stylesheet.css
# (hand-authored OUTSIDE the apply_style.py managed region — do NOT run
# apply_style.py; its managed region is stale). The font *bytes* must be
# present under epub_working/fonts/ for the build's copytree to ship them.
EMBED_FONT_PATHS: list[dict] = [
    # Cardo — Latin + Greek + Hebrew (OFL 1.1, David Perry). Three faces.
    {"path": "fonts/Cardo-Regular.ttf", "family": "Cardo", "weight": "normal", "style": "normal"},
    {"path": "fonts/Cardo-Italic.ttf", "family": "Cardo", "weight": "normal", "style": "italic"},
    {"path": "fonts/Cardo-Bold.ttf", "family": "Cardo", "weight": "bold", "style": "normal"},
    # Noto Serif Ethiopic — scoped to the Ethiopic blocks so it only ever
    # activates for Ge'ez/Amharic glyphs (OFL 1.1, Google). Embedded as ttf:
    # device-QA 2026-06-09 (colour Kobo) showed Ge'ez tofu with the previous
    # woff2 embed — root cause is the CONTAINER, not coverage (Kobo supports
    # TTF/OTF/WOFF 1.0, NOT woff2; the woff2 carried the same full v2.102
    # face, Mac-lane cmap-verified). This is the notofonts ethiopic release
    # NotoSerifEthiopic-v2.102 full/ttf static build (384 KB).
    {
        "path": "fonts/NotoSerifEthiopic-Regular.ttf",
        "family": "Noto Serif Ethiopic",
        "weight": "normal",
        "style": "normal",
        "unicode_range": "U+1200-137F, U+1380-139F, U+2D80-2DDF, U+AB00-AB2F",
    },
]


# ---------------------------------------------------------------------------
# Chapter flow
# ---------------------------------------------------------------------------

# How chapter headings interact with page breaks.
#   "page-break"  legacy: every chapter starts a fresh page (forces a break).
#   "smart"       chapters flow into the same page when room exists, but
#                 the heading + its first paragraph are kept together so the
#                 reader never sees an orphan chapter number alone at page end.
CHAPTER_FLOW = "smart"


# ---------------------------------------------------------------------------
# Reader's Table of Contents (nav.xhtml + visible TOC page)
# ---------------------------------------------------------------------------

# Format used for chapter labels under each book.
#   "num-only"    just "1", "2", "3"  (matches the existing visible TOC)
#   "code-num"    "Gen 1", "Gen 2"     (book code + chapter)
#   "title-num"   "Genesis 1"          (full title + chapter)
#   "chapter-num" "Chapter 1"          (legacy nav.xhtml style)
TOC_CHAPTER_FORMAT = "num-only"

# Collapsible book sections in the visible TOC page. When True, each book is
# wrapped in an HTML5 <details>/<summary> element so the reader can collapse
# the chapter list per book. Modern readers (Apple Books, Calibre, KOReader) term-ref-ok
# render <details> correctly; older / very-strict readers may show a flat
# tree (graceful degradation — chapters remain visible and clickable).
TOC_COLLAPSIBLE = True

# When TOC_COLLAPSIBLE is True, should books default to expanded ("open"
# attribute) or collapsed (no attribute)?
TOC_COLLAPSIBLE_DEFAULT_OPEN = False

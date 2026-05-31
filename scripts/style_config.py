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
# Π.0 itself does NOT enable Ethiopic embedding (font binary is staged
# for download but not committed; the .vnote-geez and .vnote-amharic
# CSS fall through to reader-supplied Ethiopic fonts via the font-family
# fallback chain in apply_style.py).
EMBED_FONT_PATHS: list[dict] = []


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

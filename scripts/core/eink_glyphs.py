"""Cardo-safe e-ink category faces — the single source of truth for the substitute
glyphs an edition uses when it targets Kobo / e-ink.

K-R13b — in-margin study badge faces that render on Kobo e-ink. Cardo (the default
reading font) lacks ✧ ⌂ ⌇ ◇ ⚖ ⊛ ❑ ❖ ✦ … (empirically cmap-checked against
content/assets/fonts/Cardo-Regular.ttf, 2026-06-23); Kobo renders ◊ † * and letters
everywhere. For an eink target EVERY category face — the inline badge chip, the
glossary cascade header, the per-note ``note-sym`` link, AND the symbol-legend page —
resolves through this one map, so the legend always matches what the body shows and
nothing renders as a blank box under the user's reading font. Non-eink targets keep
the full categories.yaml symbols (their fonts cover them).

Shared by ``scripts/build_edition.py`` (emitters) and ``scripts/matter_pages.py``
(the legend page) so the two can never drift.
"""

EINK_CATEGORY_BADGE_GLYPHS = {
    "lang": "⌘",
    "text": "†",
    "xref": "‖",
    "hist": "H",
    "lit": "L",
    "comm": "◊",
    "compare": "☩",
    "dev": "✶",
    "liturgy": "☧",
    "apol": "A",
    "modern": "M",
    "ped": "◯",
    "vis": "V",
    "dist": "D",
    "topic": "*",
}


def eink_category_badge_glyph(cat: str, glyph: str) -> str:
    """Kobo-safe face for a study category (K-R13b): the curated substitute when one
    exists, else the passed-in categories.yaml glyph, else the category's initial."""
    return EINK_CATEGORY_BADGE_GLYPHS.get(cat) or glyph or cat[0].upper()

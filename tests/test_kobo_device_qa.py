"""Kobo device-QA fixes (2026-06-23) — the user QA'd the ethiopian-tewahedo eink
kepub on his colour Kobo under his Cardo reading font and surfaced three defects:

* B-1 — the ``comm`` category badge ``◇`` (U+25C7) is absent from Cardo, so ~750
  inline study badges rendered as blank boxes; the glossary cascade headers used
  the full categories.yaml symbols (✧ ⌂ ◇ ✦ …), several also absent from Cardo.
* C   — dict-*/topic- note bodies opened with a redundant ``<strong>Dictionary
  (Easton's).</strong>`` / ``<strong>Topics.</strong>`` lead-in restating the
  category heading + byline.
* D   — the Vulgate/Arabic translation-popup blocks + the Kobo dot-rule separator
  had no CSS, so they ran together in the footnote preview.

These pins lock the fixes. Tracker: dev/audit/kobo-device-qa-2026-06-23.md.
"""

from scripts.build_edition import (
    _eink_category_badge_glyph,
    _eink_safe_note_sym,
    _strip_redundant_body_boilerplate,
    apply_eink_reader_css,
)
from scripts.core.eink_glyphs import EINK_CATEGORY_BADGE_GLYPHS

# Empirically cmap-checked against content/assets/fonts/Cardo-Regular.ttf (2026-06-23):
# these category symbols are NOT in Cardo, so no eink badge/header glyph may be one.
_CARDO_MISSING = {"✧", "⌂", "⌇", "◇", "⚖", "⊛", "❑", "❖", "✦"}


# --- B-1: every eink category face is Cardo-safe ----------------------------
def test_comm_badge_glyph_is_lozenge_not_diamond():
    # ◇ (U+25C7) is missing from Cardo; ◊ (U+25CA) is present and near-identical.
    assert EINK_CATEGORY_BADGE_GLYPHS["comm"] == "◊"
    assert _eink_category_badge_glyph("comm", "◇") == "◊"


def test_no_eink_badge_glyph_is_cardo_missing():
    for cat, glyph in EINK_CATEGORY_BADGE_GLYPHS.items():
        assert glyph not in _CARDO_MISSING, f"{cat} badge glyph {glyph!r} is absent from Cardo"


def test_eink_glyph_resolver_substitutes_missing_header_symbol():
    # The cascade headers route the full categories.yaml symbol through the resolver
    # for eink; the substitute must be Cardo-safe even when the raw symbol is not.
    for cat, raw in (("comm", "◇"), ("hist", "⌂"), ("topic", "✦"), ("text", "✧")):
        assert _eink_category_badge_glyph(cat, raw) not in _CARDO_MISSING


def test_eink_note_sym_glyph_substituted():
    # The baked per-note note-sym carries the categories.yaml glyph; on eink it must
    # become the Cardo-safe face (topic ✦→*, comm ◇→◊, hist ⌂→H) while Cardo-safe
    # glyphs (lang ⌘, xref ‖) pass through unchanged.
    base = '<a class="note-sym" href="legend.xhtml#legend-{c}" title="t">{g}</a>'
    assert _eink_safe_note_sym(base.format(c="topic", g="✦")) == base.format(c="topic", g="*")
    assert _eink_safe_note_sym(base.format(c="comm", g="◇")) == base.format(c="comm", g="◊")
    assert _eink_safe_note_sym(base.format(c="hist", g="⌂")) == base.format(c="hist", g="H")
    assert _eink_safe_note_sym(base.format(c="lang", g="⌘")) == base.format(c="lang", g="⌘")


def test_eink_note_sym_leaves_non_note_sym_untouched():
    # Only note-sym links are rewritten — verse text + other anchors are inviolate.
    row = '<div class="vn-item">◇ in body <a class="vn-link" href="#x">◇</a></div>'
    assert _eink_safe_note_sym(row) == row


# --- C: redundant body boilerplate stripped, losslessly ---------------------
def test_dict_body_boiler_stripped_keeps_headword():
    row = '<a class="note-sym">H</a> <strong>Dictionary (Easton\'s).</strong> <strong>CREATION</strong> The act.'
    out, changed = _strip_redundant_body_boilerplate(row, "dict-easton")
    assert changed
    assert "Dictionary (Easton" not in out
    assert "<strong>CREATION</strong> The act." in out


def test_topic_body_boiler_stripped_keeps_term_list():
    row = "<strong>Topics.</strong> This verse appears under: CREATION, EARTH, GOD."
    out, changed = _strip_redundant_body_boilerplate(row, "topic-nave")
    assert changed
    assert "<strong>Topics.</strong>" not in out
    assert out.startswith("This verse appears under:")


def test_body_boiler_no_false_positive():
    # Non dict-/topic- kinds and boiler-free dict bodies are untouched.
    comm = "<strong>CREATION</strong> A patristic reading."
    assert _strip_redundant_body_boilerplate(comm, "comm-patristic") == (comm, False)
    clean_dict = "<strong>CREATION</strong> headword body."
    assert _strip_redundant_body_boilerplate(clean_dict, "dict-easton") == (clean_dict, False)


# --- D: popup CSS ships for eink, byte-neutral elsewhere --------------------
_POPUP_CLASSES = (".vnote-kobo-sep", "br.kobo-vnote-br", ".vnote-vulgate", ".vnote-arabic")


def test_eink_css_adds_translation_popup_classes():
    css = apply_eink_reader_css("/* base */\n", {"target_reader": "eink"})
    for cls in _POPUP_CLASSES:
        assert cls in css, f"{cls} missing from eink stylesheet"


def test_non_eink_css_unchanged():
    base = "/* base */\n"
    assert apply_eink_reader_css(base, {"target_reader": "tablet"}) == base
    for cls in _POPUP_CLASSES:
        assert cls not in apply_eink_reader_css(base, {"target_reader": "tablet"})


def test_eink_css_has_no_forbidden_direction_property():
    # EPUB 3.3 forbids the CSS `direction` property (epubcheck CSS-001) — RTL is set
    # via the inline dir="rtl" attribute (as the base sheet does for .vnote-hebrew).
    css = apply_eink_reader_css("/* base */\n", {"target_reader": "eink"})
    assert "direction:" not in css


# --- shared module: legend matches the body (one source of truth) ------------
def test_eink_glyphs_is_single_source():
    # The badge/header/note-sym emitters and the legend page resolve through the SAME
    # function object — build_edition's resolver IS the shared module's (no drift).
    from scripts.core.eink_glyphs import eink_category_badge_glyph

    assert _eink_category_badge_glyph is eink_category_badge_glyph


def test_legend_page_eink_uses_cardo_safe_symbols():
    from scripts.matter_pages import render_symbol_legend_page

    cats = [
        {"id": "comm", "symbol": "◇", "label": "Commentary", "count": 5, "description": "x"},
        {"id": "topic", "symbol": "✦", "label": "Topical", "count": 9, "description": "y"},
    ]
    eink = render_symbol_legend_page({"id": "e", "target_reader": "eink"}, cats)
    assert 'legend-sym">◊' in eink and 'legend-sym">◇' not in eink
    assert 'legend-sym">*' in eink and 'legend-sym">✦' not in eink
    # non-eink keeps the full categories.yaml symbols (its fonts cover them).
    web = render_symbol_legend_page({"id": "e", "target_reader": "everywhere"}, cats)
    assert 'legend-sym">◇' in web and 'legend-sym">✦' in web


# --- D-adjacent: book-page ornament Cardo-safe on eink ----------------------
def test_bookpage_ornament_eink_substitution():
    from scripts.build_edition import apply_eink_bookpage_ornament

    pre = {"a.html": '<div class="bookpage-rule">❖</div>', "b.html": "no rule"}
    assert apply_eink_bookpage_ornament({"target_reader": "eink"}, pre) == 1
    assert pre["a.html"] == '<div class="bookpage-rule">❦</div>'
    # non-eink leaves the base ornament byte-identical.
    pre2 = {"a.html": '<div class="bookpage-rule">❖</div>'}
    assert apply_eink_bookpage_ornament({"target_reader": "tablet"}, pre2) == 0
    assert pre2["a.html"] == '<div class="bookpage-rule">❖</div>'

"""Device-QA round-2 CSS pins (clusters D, E-Apple, G).

These lock the declarative base-stylesheet + CSS-generator changes so a future edit can't
silently revert them. The on-device behaviour is confirmed by the Wave-6 rebuild + user
re-QA; these are byte-level regression guards.
"""

import re
from pathlib import Path

import scripts.build_edition as be

REPO = Path(__file__).resolve().parent.parent
BASE_CSS = (REPO / "epub_working" / "stylesheet.css").read_text(encoding="utf-8")


class TestTitlePageOnePage:
    """D + E-Play: the book title heading must not force a mid-frame page break."""

    def test_bookpage_title_in_page_break_before_auto_override(self):
        # .bookpage-title is the last selector in the override block, so one of its `{`
        # occurrences is immediately followed by `page-break-before: auto` (the <h1> that
        # would otherwise inherit the global forced break and split the title page in two).
        # The other occurrence is its typography rule, so match position-agnostically.
        assert re.search(r"\.bookpage-title \{\s*page-break-before: auto", BASE_CSS)


class TestNoDoubleCoverBreak:
    """E-Apple: drop the redundant body-level page-break-after that doubled the wrap break."""

    def test_cover_body_has_no_page_break_after(self):
        line = next(ln for ln in BASE_CSS.splitlines() if ln.strip().startswith(".cover-body, .intro-body"))
        assert "page-break-after" not in line


class TestNoteTypographyG:
    """G (user decision, hardcoded): header BOLD+UPPERCASE; special-info italic+underline."""

    def test_note_label_header_is_uppercase_not_smallcaps(self):
        line = next(ln for ln in BASE_CSS.splitlines() if ln.strip().startswith(".note-label {"))
        assert "text-transform: uppercase" in line
        assert "font-weight: 700" in line
        assert "small-caps" not in line

    def test_special_info_em_and_tradition_label_underlined(self):
        assert (
            ".note em, .vn-item em, .note-tradition-label { font-style: italic; text-decoration: underline; }"
            in BASE_CSS
        )

    def test_cascade_header_css_is_uppercase(self):
        # the generated S2 cascade + popup category-color CSS no longer emit small-caps headers
        assert "text-transform: uppercase" in be._NOTE_CASCADE_CSS
        assert "font-variant-caps: small-caps" not in be._NOTE_CASCADE_CSS
        assert "font-variant-caps: small-caps" not in be._NOTE_POPUP_CATEGORY_COLOR_CSS

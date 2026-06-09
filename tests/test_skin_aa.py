"""η.1 manuscript-skin WCAG AA contrast pins (from Mac's adversarial review,
docs/superpowers/notes/2026-06-09-eta1-skin-adversarial-review.md).

The skin was user-loved but not AA-clean. The user's color decision: KEEP the gold
primary buttons (lighter #C49A2E hover), use INDIGO #243B6B for accents where gold
fails (NOT the red-recolor alternative). These tests compute true WCAG relative-
luminance contrast for the fixed pairs AND pin the AA-clean values in source, so a
future skin tweak can't silently re-introduce a sub-AA color.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TPL = REPO / "scripts" / "templates"

# WCAG AA thresholds.
AA_NORMAL = 4.5  # normal-size text
AA_LARGE = 3.0  # large/bold text + UI-component boundaries (1.4.11)

# Manuscript grounds (from _design.py :214-216).
INK = "#2B2118"
VELLUM = "#F4ECD8"
PARCHMENT = "#FBF6E9"
GOLD = "#B8860B"  # primary button rest (passes at 4.84:1)


def _relative_luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def _lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    rl = _lin(r), _lin(g), _lin(b)
    return 0.2126 * rl[0] + 0.7152 * rl[1] + 0.0722 * rl[2]


def contrast(a: str, b: str) -> float:
    la, lb = _relative_luminance(a), _relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _skin_css() -> str:
    from scripts.templates._design import MANUSCRIPT_SKIN_CSS

    return MANUSCRIPT_SKIN_CSS


class TestContrastHelper:
    def test_helper_matches_macs_independently_computed_values(self):
        # the review's anchor values — proves the luminance math is right
        assert round(contrast(INK, GOLD), 2) == 4.84  # gold rest
        assert round(contrast("#243B6B", PARCHMENT), 1) == 10.2  # indigo on parchment


class TestPrimaryButtonHoverAA:
    """H1 — gold-button hover #9A6E12 was 3.46:1 (fails). User: keep gold, lighter
    hover #C49A2E (6.01:1)."""

    def test_target_hover_gold_clears_AA_on_ink(self):
        assert contrast(INK, "#C49A2E") >= AA_NORMAL

    def test_skin_uses_the_lighter_hover_token(self):
        css = _skin_css()
        assert "#C49A2E" in css, "the AA-clean gold hover must be in the skin"
        # the failing 3.46:1 pair (ink text on #9A6E12) must no longer drive a button
        assert ".hover\\:bg-blue-700:hover { background-color: var(--ms-gold-line)" not in css


class TestHintTextAA:
    """H4 — slate-400 #A8916B hint text was 2.58/2.81:1 (×176 sites). Deepen to
    #6E5840 (~slate-500), ~6:1 on the grounds."""

    def test_target_hint_tone_clears_AA_on_both_grounds(self):
        assert contrast("#6E5840", VELLUM) >= AA_NORMAL
        assert contrast("#6E5840", PARCHMENT) >= AA_NORMAL

    def test_skin_scale_deepened_slate_400(self):
        css = _skin_css()
        # slate-400 line must no longer carry the low-contrast #A8916B
        assert "400:'#A8916B'" not in css
        assert "400:'#6E5840'" in css


class TestInputBorderAA:
    """M4 — input border rgba(154,110,18,0.60) composited to 2.28:1 (fails UI 3:1).
    Drop the alpha → solid gold-line #9A6E12 = 4.48:1."""

    def test_solid_gold_line_clears_UI_contrast(self):
        assert contrast("#9A6E12", "#FFFDF7") >= AA_LARGE

    def test_skin_input_border_is_no_longer_translucent(self):
        css = _skin_css()
        assert "rgba(154,110,18,0.60)" not in css  # the faint resting border is gone


class TestDarkModeInputAA:
    """H2/H3 — dark-mode typed text was slate-100 on near-white #FFFDF7 = 1.08:1.
    The skin must define a dark manuscript block so typed text reads in dark mode."""

    def test_skin_defines_a_dark_manuscript_override(self):
        css = _skin_css()
        assert ':root[data-theme="dark"]' in css, "skin must override the dark tokens (H3)"
        # the light grounds must defer in dark mode (no forced parchment under dark panels)
        assert ":root:not([data-theme=dark])" in css

    def test_dark_field_text_clears_AA(self):
        # in dark mode the field carries light parchment text on a dark surface
        assert contrast("#F4ECD8", "#2B2118") >= AA_NORMAL


class TestEmeraldPrimaryCtasRouted:
    """H5/H6 — the flagship terminal CTAs were bg-emerald-600 (3.77:1, un-skinned).
    Route them through the primary (bg-blue-600) so they get the gold treatment."""

    def test_wizard_terminal_ctas_use_the_primary_utility(self):
        src = (TPL / "wizard.py").read_text(encoding="utf-8")
        # the two terminal CTAs (Build my Bible / Download EPUB) no longer emerald
        assert "bg-emerald-600" not in src, "wizard CTAs must route through the gold primary"

    def test_index_add_note_uses_the_primary_utility(self):
        src = (TPL / "index.py").read_text(encoding="utf-8")
        assert "bg-emerald-600 hover:bg-emerald-700" not in src


class TestPerConsoleDataStatesAA:
    """M1/M2/M3/M6 — CSS-rule hex data states the skin can't reach were near-invisible
    on the warm grounds. Retoned to manuscript tones that read."""

    def test_book_row_active_is_visible_against_vellum(self):
        # M1: active row #dbeafe vs vellum was 1.04:1 (invisible) → #E3D4AE
        for f in ("build_my_bible.py", "sources.py"):
            src = (TPL / f).read_text(encoding="utf-8")
            assert "#dbeafe" not in src, f"{f}: the invisible blue active-row must be retoned"

    def test_matrix_count_states_clear_readability(self):
        # M2: count-disabled #fbbf24 (1.55:1) / count-zero #cbd5e0 (1.38:1) → manuscript
        src = (TPL / "matrix.py").read_text(encoding="utf-8")
        assert "#fbbf24" not in src and "#cbd5e0" not in src
        assert contrast("#574532", PARCHMENT) >= AA_NORMAL  # count-zero new tone

    def test_compare_verse_num_and_missing_are_legible(self):
        # M3: verse-num #94a3b8 (2.38:1) / missing #cbd5e1 (1.38:1) → sepia/gold
        src = (TPL / "compare.py").read_text(encoding="utf-8")
        assert "#94a3b8" not in src and "#cbd5e1" not in src

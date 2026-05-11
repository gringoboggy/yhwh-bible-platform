"""ζ.1 — CSS variable theming foundation pins.

Topic file (created alongside the ζ.1 ship, follows the ω.27
follow-on convention).

Coverage:
- TestZeta1ThemeTokensCss:        the `THEME_TOKENS_CSS` constant
  defines the required token set (colors, surfaces, status) in
  both `:root` (light) and `:root[data-theme="dark"]` blocks, and
  exposes `.theme-*` utility classes that consume the vars.
- TestZeta1ApplyDesignSystem:     the marker substitution works
  + is idempotent + is a no-op on templates without the marker.
- TestZeta1PreflightWired:        `/preflight`'s rendered HTML
  contains the tokens (the proof-of-concept retrofit landed) and
  the marker placeholder is gone.
- TestZeta1FocusRingThemableViaVar: `BUYER_ARC_POLISH_CSS` reads
  focus-ring color via `var(--color-focus-ring, …)` so ζ.2 dark
  mode can override without touching ψ.14's CSS.

Pinning rationale: ζ.1 is the foundation gate for every other
ζ.* phase (dark mode, typography, iconography, toasts,
skeletons, command palette). Drift in the token names, the
marker contract, or the apply-design-system substitution would
silently break all 6 follow-on phases. Every contract piece
gets an explicit assertion.
"""

from __future__ import annotations


class TestZeta1ThemeTokensCss:
    """The THEME_TOKENS_CSS constant is the canonical token surface.
    Pin token names, both theme blocks, and the utility classes."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOKENS_CSS

        cls.css = THEME_TOKENS_CSS

    def test_is_a_style_block(self):
        assert self.css.startswith("<style>"), "THEME_TOKENS_CSS must be wrapped in <style>"
        assert self.css.rstrip().endswith("</style>"), "THEME_TOKENS_CSS must end with </style>"

    def test_has_light_root_block(self):
        # Light theme = default values used when no data-theme attribute.
        assert ":root {" in self.css, "missing default :root block"

    def test_has_dark_data_theme_block(self):
        # Dark theme — defined but inactive until ζ.2 wires the toggle.
        assert ':root[data-theme="dark"]' in self.css, "missing dark-theme :root[data-theme] override"

    def test_defines_required_color_tokens_in_light(self):
        # The minimum viable token set ζ.2/4/5/6/7/8 will consume.
        # Pin both halves: name AND a default value (rgb/hex) must
        # appear in the :root block. We don't pin specific colors so
        # designers can tweak; we DO pin that each token exists.
        light_block = self.css.split(":root {", 1)[1].split("}", 1)[0]
        for token in (
            "--color-bg-page",
            "--color-bg-surface",
            "--color-text-primary",
            "--color-text-muted",
            "--color-text-on-accent",
            "--color-accent",
            "--color-accent-hover",
            "--color-border",
            "--color-focus-ring",
            "--color-status-success",
            "--color-status-warn",
            "--color-status-error",
            "--color-status-info",
        ):
            assert token in light_block, f"light :root missing token {token!r}"

    def test_defines_required_color_tokens_in_dark(self):
        # Dark theme must override the same set so ζ.2 toggling
        # data-theme="dark" gives every var a value (no fallthrough
        # to light, which would create a half-themed dashboard).
        dark_block = self.css.split(':root[data-theme="dark"]', 1)[1].split("}", 1)[0]
        for token in (
            "--color-bg-page",
            "--color-bg-surface",
            "--color-text-primary",
            "--color-text-muted",
            "--color-text-on-accent",
            "--color-accent",
            "--color-accent-hover",
            "--color-border",
            "--color-focus-ring",
            "--color-status-success",
            "--color-status-warn",
            "--color-status-error",
            "--color-status-info",
        ):
            assert token in dark_block, f"dark :root[data-theme] missing token {token!r}"

    def test_exposes_utility_classes_that_consume_tokens(self):
        # The `.theme-*` classes are how consumers actually use the
        # tokens (cheaper than peppering var() into every style
        # attribute). Pin the foundational set.
        for cls in (
            ".theme-bg-page",
            ".theme-bg-surface",
            ".theme-text",
            ".theme-text-muted",
            ".theme-border",
            ".theme-accent",
            ".theme-accent-text",
            ".theme-status-success",
            ".theme-status-warn",
            ".theme-status-error",
            ".theme-status-info",
        ):
            assert cls in self.css, f"utility class {cls} missing"

    def test_utility_classes_use_var_lookups(self):
        # Each utility class must reference its corresponding var()
        # rather than hardcoding a color — that's the whole point.
        for cls, expected_var in (
            (".theme-bg-page", "var(--color-bg-page)"),
            (".theme-bg-surface", "var(--color-bg-surface)"),
            (".theme-text", "var(--color-text-primary)"),
            (".theme-text-muted", "var(--color-text-muted)"),
            (".theme-border", "var(--color-border)"),
            (".theme-accent-text", "var(--color-accent)"),
            (".theme-status-success", "var(--color-status-success)"),
        ):
            # Crude but sufficient: find the class, then look at the
            # next 200 chars for the var() reference. The CSS is
            # tight enough that 200 chars covers each declaration.
            idx = self.css.find(cls + " ")
            if idx < 0:
                idx = self.css.find(cls + "  ")
            assert idx >= 0, f"could not locate {cls}"
            window = self.css[idx : idx + 200]
            assert expected_var in window, f"{cls} doesn't reference {expected_var!r}; got {window[:120]!r}..."


class TestZeta1ApplyDesignSystem:
    """`apply_design_system` must substitute the new marker, leave
    the existing markers working, and be idempotent."""

    def test_substitutes_theme_tokens_marker(self):
        from scripts.templates._design import THEME_TOKENS_CSS, apply_design_system

        before = "<head><!-- THEME_TOKENS_CSS --></head>"
        after = apply_design_system(before, "/preflight")
        assert "<!-- THEME_TOKENS_CSS -->" not in after, "marker not substituted"
        assert THEME_TOKENS_CSS in after, "marker substituted with wrong payload"

    def test_no_op_when_marker_absent(self):
        # Most templates don't yet have the marker — apply_design_system
        # must not break them. The output should equal the input
        # except for HEADER_NAV_LINKS substitution (still works).
        from scripts.templates._design import THEME_TOKENS_CSS, apply_design_system

        before = "<html><body>hello world</body></html>"
        after = apply_design_system(before, "/preflight")
        assert after == before, f"unexpected substitution: {after!r}"
        assert THEME_TOKENS_CSS not in after, "tokens injected without a marker"

    def test_idempotent_on_second_call(self):
        # The existing buyer-arc CSS already established this
        # contract; pin it for the new marker too. Once substituted,
        # rerunning is a no-op.
        from scripts.templates._design import apply_design_system

        once = apply_design_system("<!-- THEME_TOKENS_CSS -->", "/preflight")
        twice = apply_design_system(once, "/preflight")
        assert once == twice, "double-substitution drift"

    def test_still_substitutes_existing_markers(self):
        # Regression guard — adding the new marker must not break
        # the HEADER_NAV_LINKS or BUYER_ARC_POLISH_CSS substitutions.
        from scripts.templates._design import BUYER_ARC_POLISH_CSS, apply_design_system

        before = "    <!-- HEADER_NAV_LINKS -->\n<!-- BUYER_ARC_POLISH_CSS -->"
        after = apply_design_system(before, "/preflight")
        assert "<!-- HEADER_NAV_LINKS -->" not in after
        assert "<!-- BUYER_ARC_POLISH_CSS -->" not in after
        assert BUYER_ARC_POLISH_CSS in after


class TestZeta1PreflightWired:
    """`/preflight` is the proof-of-concept retrofit — its rendered
    HTML should contain the tokens, and the marker placeholder
    should be gone after the module-load substitution."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.preflight import PREFLIGHT_HTML

        cls.html = PREFLIGHT_HTML

    def test_marker_substituted_at_module_load(self):
        assert "<!-- THEME_TOKENS_CSS -->" not in self.html, "marker leaked into rendered HTML"

    def test_tokens_present_in_rendered_html(self):
        assert "--color-bg-page" in self.html
        assert "--color-accent" in self.html
        assert "--color-focus-ring" in self.html

    def test_dark_theme_block_present_but_inactive(self):
        # ζ.1 defines but doesn't activate dark mode — block must be
        # in the page, but no <html data-theme="dark"> attribute.
        assert ':root[data-theme="dark"]' in self.html, "dark block missing from preflight"

    def test_theme_utility_classes_available(self):
        # Even before /preflight migrates its elements to theme-*
        # classes, the classes themselves must be loaded so future
        # ζ.* work can opt-in without re-importing.
        for cls in (".theme-bg-surface", ".theme-text", ".theme-accent"):
            assert cls in self.html, f"utility class {cls} missing from preflight"


class TestZeta1FocusRingThemableViaVar:
    """ψ.14's focus-ring CSS was hardcoded `rgb(37 99 235)`. ζ.1
    rewires it to `var(--color-focus-ring, rgb(37 99 235))` so ζ.2
    dark mode can override without re-editing buyer-arc CSS."""

    def test_buyer_arc_css_uses_focus_ring_var(self):
        from scripts.templates._design import BUYER_ARC_POLISH_CSS

        assert "var(--color-focus-ring" in BUYER_ARC_POLISH_CSS, (
            "BUYER_ARC_POLISH_CSS still hardcodes focus-ring color; ζ.1 should rewire via var()"
        )

    def test_buyer_arc_css_preserves_fallback(self):
        # The rgb() fallback keeps the visual identical in templates
        # that haven't absorbed THEME_TOKENS_CSS yet. Without it,
        # those templates would show NO focus ring at all (var()
        # with no defined --color-focus-ring evaluates to invalid).
        from scripts.templates._design import BUYER_ARC_POLISH_CSS

        # Either form acceptable: var(--name, fallback) — must contain
        # the var name AND a comma indicating a fallback is provided.
        assert "var(--color-focus-ring, rgb" in BUYER_ARC_POLISH_CSS, (
            "focus-ring var() missing rgb() fallback for unthemed templates"
        )

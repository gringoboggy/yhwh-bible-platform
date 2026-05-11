"""ζ.2 — dark-mode toggle pins.

Topic file (created alongside the ζ.2 ship, follows the ω.27
follow-on convention).

Coverage:
- TestZeta2DarkModeJs:           the `DARK_MODE_JS` constant
  contains the init script (no-FOAUC: synchronous data-theme
  resolution) + toggle button creation + persistence + the
  `ebibleTheme` JS API surface.
- TestZeta2ApplyDesignSystem:    the `<!-- DARK_MODE_JS -->`
  marker substitution works + is idempotent + is a no-op on
  templates without the marker.
- TestZeta2PreflightWired:       `/preflight`'s rendered HTML
  contains the dark-mode JS, the marker placeholder is gone,
  and the visible surfaces (body + header) use `.theme-*`
  classes so toggling has actual visible effect.

Pinning rationale: ζ.2 is the first user-visible payoff of
the Month 2 modernization arc. Drift in the toggle contract,
the persistence key, the no-FOAUC guarantee, or the
visible-surface migration would silently regress to either
"toggle does nothing" or "flash of light on load" — both
visible bugs hard to catch without an explicit pin.
"""

from __future__ import annotations


class TestZeta2DarkModeJs:
    """The DARK_MODE_JS constant is the canonical toggle behavior.
    Pin the init contract, toggle insertion, persistence, and the
    public API surface (`window.ebibleTheme`)."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import DARK_MODE_JS

        cls.js = DARK_MODE_JS

    def test_is_a_script_block(self):
        assert self.js.startswith("<script>"), "DARK_MODE_JS must be wrapped in <script>"
        assert self.js.rstrip().endswith("</script>"), "DARK_MODE_JS must end with </script>"

    def test_uses_namespaced_localstorage_key(self):
        # `ebible_theme` — namespace-prefixed to avoid collision with
        # future per-feature toggles. Pin the exact key so external
        # tooling (e.g., a future preferences-export feature) can
        # rely on the name.
        assert "ebible_theme" in self.js, "localStorage key drift"

    def test_respects_prefers_color_scheme_media_query(self):
        # Without this, dark-mode users who haven't toggled get
        # light mode by default — bad UX.
        assert "prefers-color-scheme: dark" in self.js, "DARK_MODE_JS missing prefers-color-scheme media query check"

    def test_sets_data_theme_attribute_synchronously(self):
        # FOAUC guard: the init must call setAttribute('data-theme')
        # BEFORE DOMContentLoaded. We pin the synchronous call.
        assert "setAttribute('data-theme', 'dark')" in self.js, (
            "data-theme attribute not set synchronously — FOAUC risk"
        )

    def test_removes_data_theme_in_light_mode(self):
        # Light is the absence of the attribute; pin that we don't
        # set `data-theme="light"` (which would also work but is
        # semantically noisier and could surprise CSS selectors
        # that match on the attribute existence).
        assert "removeAttribute('data-theme')" in self.js

    def test_exposes_window_ebible_theme_api(self):
        # Public API surface for tests + future ζ.* components.
        # Pin the three methods that future toast/skeleton/etc.
        # code may rely on.
        for member in ("window.ebibleTheme", "get:", "set:", "toggle:"):
            assert member in self.js, f"ebibleTheme API missing {member!r}"

    def test_dispatches_themechange_event(self):
        # Custom event lets future ζ.* components react to theme
        # toggles (e.g., recolor charts). Pin the event name +
        # detail shape.
        assert "themechange" in self.js
        assert "CustomEvent" in self.js
        assert "detail" in self.js, "themechange event missing detail payload"

    def test_inserts_toggle_button_with_known_id(self):
        # The button id is the hook a future test/skill might use
        # to find + click the toggle. Pin it.
        assert "ebible-theme-toggle" in self.js, "toggle button id drift"

    def test_toggle_button_is_idempotent(self):
        # `insertToggle` should be safe to call twice (e.g., if
        # something else listens for DOMContentLoaded too).
        assert "getElementById('ebible-theme-toggle')" in self.js, (
            "toggle insertion not idempotent — re-running would inject duplicate buttons"
        )

    def test_button_has_accessible_label(self):
        # Screen-reader accessibility — the button is icon-only,
        # so aria-label carries the semantic meaning.
        assert "aria-label" in self.js, "toggle button missing aria-label"

    def test_localstorage_access_is_guarded(self):
        # Some browsers / private modes disable localStorage; the
        # init must degrade to media-query-only rather than throwing.
        assert "try" in self.js and "catch" in self.js, (
            "localStorage access not wrapped in try/catch — would throw in private-mode browsers"
        )


class TestZeta2ApplyDesignSystem:
    """`apply_design_system` must substitute the new DARK_MODE_JS
    marker, be idempotent, no-op on templates without it, and not
    regress the prior markers."""

    def test_substitutes_dark_mode_marker(self):
        from scripts.templates._design import DARK_MODE_JS, apply_design_system

        before = "<head><!-- DARK_MODE_JS --></head>"
        after = apply_design_system(before, "/preflight")
        assert "<!-- DARK_MODE_JS -->" not in after, "marker not substituted"
        assert DARK_MODE_JS in after

    def test_no_op_when_marker_absent(self):
        from scripts.templates._design import DARK_MODE_JS, apply_design_system

        before = "<html><body>hello</body></html>"
        after = apply_design_system(before, "/preflight")
        assert after == before
        assert DARK_MODE_JS not in after, "dark-mode JS injected without a marker"

    def test_idempotent_on_second_call(self):
        from scripts.templates._design import apply_design_system

        once = apply_design_system("<!-- DARK_MODE_JS -->", "/preflight")
        twice = apply_design_system(once, "/preflight")
        assert once == twice

    def test_still_substitutes_prior_markers(self):
        # Regression guard — adding the new marker must not break
        # the older HEADER_NAV_LINKS / BUYER_ARC_POLISH_CSS /
        # THEME_TOKENS_CSS substitutions.
        from scripts.templates._design import (
            BUYER_ARC_POLISH_CSS,
            DARK_MODE_JS,
            THEME_TOKENS_CSS,
            apply_design_system,
        )

        before = (
            "    <!-- HEADER_NAV_LINKS -->\n"
            "<!-- THEME_TOKENS_CSS -->\n"
            "<!-- DARK_MODE_JS -->\n"
            "<!-- BUYER_ARC_POLISH_CSS -->"
        )
        after = apply_design_system(before, "/preflight")
        for marker in (
            "<!-- HEADER_NAV_LINKS -->",
            "<!-- THEME_TOKENS_CSS -->",
            "<!-- DARK_MODE_JS -->",
            "<!-- BUYER_ARC_POLISH_CSS -->",
        ):
            assert marker not in after, f"prior marker {marker!r} no longer substituted"
        for payload in (THEME_TOKENS_CSS, DARK_MODE_JS, BUYER_ARC_POLISH_CSS):
            assert payload in after


class TestZeta2PreflightWired:
    """`/preflight` is the proof-of-concept retrofit — its rendered
    HTML should contain the dark-mode JS in `<head>` (so init runs
    before paint), the marker placeholder is gone, and the visible
    surfaces (body + header) use `.theme-*` classes."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.preflight import PREFLIGHT_HTML

        cls.html = PREFLIGHT_HTML

    def test_marker_substituted_at_module_load(self):
        assert "<!-- DARK_MODE_JS -->" not in self.html, "DARK_MODE_JS marker leaked"

    def test_dark_mode_js_lives_in_head(self):
        # FOAUC guard: the dark-mode init script must appear before
        # `</head>` so it runs synchronously before body paint.
        head_end = self.html.find("</head>")
        assert head_end > 0, "preflight has no </head>?"
        head_section = self.html[:head_end]
        assert "ebible_theme" in head_section, "DARK_MODE_JS appears after </head> — FOAUC risk for dark-mode users"

    def test_body_uses_theme_bg_page(self):
        # Visible-surface migration: body background is themable.
        assert 'class="theme-bg-page theme-text"' in self.html or (
            "theme-bg-page" in self.html and "theme-text" in self.html
        ), "body not migrated to theme classes"

    def test_header_uses_theme_bg_surface(self):
        # Header has a distinct surface color (card-like) so it's
        # readable against the page background in both themes.
        assert "theme-bg-surface" in self.html
        assert "theme-border" in self.html

    def test_no_residual_hardcoded_body_background(self):
        # Pin that we removed the conflicting `bg-slate-50` from
        # `<body>` — Tailwind CDN's JIT-injected utility would
        # otherwise win the cascade and dark mode wouldn't show.
        # Other elements may still legitimately use Tailwind
        # colors; we only check the body opener line.
        body_open_idx = self.html.find("<body")
        body_open_end = self.html.find(">", body_open_idx) + 1
        body_open_line = self.html[body_open_idx:body_open_end]
        assert "bg-slate-50" not in body_open_line, (
            "<body> still has Tailwind bg-slate-50 alongside theme-bg-page — cascade conflict"
        )

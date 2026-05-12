"""δ.1 — reading-streak pins.

NOTE on phase notation: this is **lowercase δ** (the reader-track
family), distinct from **uppercase Δ** (the database-evolution
track e.g. Δ.10, Δ.12). Same Greek letter shape; the Greek capital
delta is a triangle (Δ) and the lowercase is a curved form (δ).

Topic file (created alongside the δ.1 ship). Reader-track features
are localStorage-only with no backend; the test surface is the JS
shape + the CSS contract + the marker substitution + the icon
registration.

Coverage:
- TestDelta1ReaderStreakJs:           the `THEME_STREAK_JS` constant
  exposes the `window.ebibleStreak.{mark, getStreak, getReadDates,
  reset}` API, dispatches `streakchange`, uses namespaced
  localStorage key, guards localStorage with try/catch, computes
  streak with today-or-yesterday tolerance.
- TestDelta1FlameIcon:                ζ.5's ICONS_REGISTRY now
  includes the `flame` icon used by the streak indicator.
- TestDelta1StreakCss:                `.theme-streak-indicator` +
  variants present in THEME_TOKENS_CSS; uses ζ.1 tokens.
- TestDelta1ApplyDesignSystem:        `<!-- THEME_STREAK_JS -->`
  marker substitution works + idempotent + no-op without marker.
- TestDelta1PreflightWired:           /preflight absorbs the marker
  and `window.ebibleStreak` is present in the rendered HTML.

Pinning rationale: δ.1 is the first lowercase-delta phase. δ.2
bookmarks, δ.3 memorization, δ.6 pace-tracker all build on this
API. Drift in the storage key, the streak math, or the event
shape would break the entire reader-track chain.
"""

from __future__ import annotations


class TestDelta1ReaderStreakJs:
    """The `THEME_STREAK_JS` script block — JS contract."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_STREAK_JS

        cls.js = THEME_STREAK_JS

    def test_is_a_script_block(self):
        assert self.js.startswith("<script>")
        assert self.js.rstrip().endswith("</script>")

    def test_exposes_ebible_streak_api(self):
        assert "window.ebibleStreak" in self.js

    def test_exposes_four_public_methods(self):
        # mark / getStreak / getReadDates / reset — the API the
        # downstream δ.2 bookmarks + δ.3 memorization will rely on.
        for method in ("mark:", "getStreak:", "getReadDates:", "reset:"):
            assert method in self.js, f"missing method binding {method!r}"

    def test_uses_namespaced_localstorage_key(self):
        # `ebible_streak` — pin so a future cleanup doesn't quietly
        # rename and orphan existing users' streak data.
        assert "'ebible_streak'" in self.js or "ebible_streak" in self.js

    def test_localstorage_access_is_guarded(self):
        # Private-mode / disabled-localStorage browsers degrade
        # silently rather than throwing.
        assert "try" in self.js
        assert "catch" in self.js

    def test_dispatches_streakchange_event(self):
        # CustomEvent lets δ.2/δ.3/δ.6 listen for streak updates.
        assert "streakchange" in self.js
        assert "CustomEvent" in self.js
        assert "detail" in self.js

    def test_streak_tolerates_today_or_yesterday(self):
        # Users who check the page after midnight (yesterday's
        # streak end) shouldn't immediately drop to 0. Pin the
        # today-or-yesterday rollover guard.
        assert "todayIso()" in self.js
        # The function name varies; check that the math handles
        # the gap-day case by looking for dateNDaysAgo with a
        # numeric arg.
        assert "dateNDaysAgo(1)" in self.js, "yesterday-tolerance not implemented — users lose streak overnight"

    def test_indicator_id_is_known(self):
        # `ebible-streak-indicator` is the hook tests + δ.2 can use.
        assert "ebible-streak-indicator" in self.js

    def test_caps_stored_history_at_400_days(self):
        # Unbounded history would grow localStorage forever. Cap
        # at ~14 months so a long-time user's history is preserved
        # but the array stays bounded.
        assert "slice(-400)" in self.js or "400" in self.js, (
            "no history cap — localStorage will grow unbounded over years"
        )


class TestDelta1FlameIcon:
    """ζ.5's ICONS_REGISTRY now ships a `flame` icon for the
    streak indicator's leading glyph."""

    def test_flame_in_registry(self):
        from scripts.templates._design import ICONS_REGISTRY

        assert "flame" in ICONS_REGISTRY, "flame icon missing from ζ.5 registry"

    def test_flame_is_valid_svg(self):
        from scripts.templates._design import ICONS_REGISTRY

        svg = ICONS_REGISTRY["flame"]
        assert svg.startswith("<svg ")
        assert svg.rstrip().endswith("</svg>")
        assert 'stroke="currentColor"' in svg
        assert 'viewBox="0 0 24 24"' in svg

    def test_flame_carries_theme_icon_class(self):
        # So it renders at 1em with the rest of the icon system.
        from scripts.templates._design import ICONS_REGISTRY

        assert 'class="theme-icon"' in ICONS_REGISTRY["flame"]


class TestDelta1StreakCss:
    """`.theme-streak-indicator` + variants in THEME_TOKENS_CSS."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOKENS_CSS

        cls.css = THEME_TOKENS_CSS

    def test_indicator_rule_present(self):
        assert ".theme-streak-indicator" in self.css

    def test_indicator_is_fixed_position(self):
        idx = self.css.find(".theme-streak-indicator {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "position: fixed" in block
        # Specifically bottom-right per the proposal spec
        # ("Quiet bottom-of-page indicator").
        assert "bottom" in block
        assert "right" in block

    def test_indicator_uses_theme_tokens(self):
        # Background / text / border all from ζ.1 so dark mode
        # adapts. Pin var() usage.
        idx = self.css.find(".theme-streak-indicator {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "var(--color-bg-surface)" in block
        assert "var(--color-text-primary)" in block
        assert "var(--color-border)" in block

    def test_visible_class_toggles_display(self):
        # `display: none` by default; `.theme-streak-visible`
        # flips it to `inline-flex`. Pin the toggle pattern.
        assert ".theme-streak-visible" in self.css


class TestDelta1ApplyDesignSystem:
    """`<!-- THEME_STREAK_JS -->` substitution."""

    def test_substitutes_marker(self):
        from scripts.templates._design import THEME_STREAK_JS, apply_design_system

        before = "<head><!-- THEME_STREAK_JS --></head>"
        after = apply_design_system(before, "/preflight")
        assert "<!-- THEME_STREAK_JS -->" not in after
        assert THEME_STREAK_JS in after

    def test_no_op_when_marker_absent(self):
        from scripts.templates._design import THEME_STREAK_JS, apply_design_system

        before = "<html><body>hi</body></html>"
        after = apply_design_system(before, "/preflight")
        assert after == before
        assert THEME_STREAK_JS not in after

    def test_idempotent_on_second_call(self):
        from scripts.templates._design import apply_design_system

        once = apply_design_system("<!-- THEME_STREAK_JS -->", "/preflight")
        twice = apply_design_system(once, "/preflight")
        assert once == twice


class TestDelta1PreflightWired:
    """/preflight absorbs the streak JS marker (proof-of-concept;
    semantically /preflight isn't a 'reader' but the wire-up is
    universal — any future reader page inherits the same module)."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.preflight import PREFLIGHT_HTML

        cls.html = PREFLIGHT_HTML

    def test_marker_substituted_at_module_load(self):
        assert "<!-- THEME_STREAK_JS -->" not in self.html

    def test_ebible_streak_api_present(self):
        assert "window.ebibleStreak" in self.html

    def test_streak_lives_in_head(self):
        # The init runs on DOMContentLoaded; ordering with the other
        # theme scripts doesn't strictly matter, but placing in <head>
        # mirrors the pattern and keeps load-time behavior
        # predictable.
        head_end = self.html.find("</head>")
        head_section = self.html[:head_end]
        assert "window.ebibleStreak" in head_section

"""ζ.4 — typography upgrade pins.

Topic file (created alongside the ζ.4 ship, follows the ω.27
follow-on convention).

Coverage:
- TestZeta4TypographyTokens:    the new font / size / leading /
  weight CSS vars are defined in `:root` and live alongside the
  color tokens from ζ.1.
- TestZeta4TypographyUtilities: `.theme-text-{xs..2xl}` /
  `.theme-font-mono` / `.theme-weight-*` classes exist and
  reference the appropriate `var()` lookups.
- TestZeta4BodyFontRule:        `THEME_TOKENS_CSS` includes a
  `body { font-family: var(--font-stack-body) }` rule so every
  console picks up the themable stack on absorbing the marker.
- TestZeta4PreflightRetrofit:   `/preflight` headings + body
  text + details-list use the new themable classes / vars.

Pinning rationale: ζ.4 sets the type scale that ζ.5 iconography
(icons sized relative to text), ζ.6 toasts (consistent body
sizing), and ζ.8 command palette (mono input field) consume.
Drift in token names or class signatures would silently
mis-render text in the follow-on phases.
"""

from __future__ import annotations


class TestZeta4TypographyTokens:
    """Typography tokens live in `:root` (theme-independent —
    font choice doesn't change between light/dark). Pin token
    names so ζ.5+ phases can rely on them."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOKENS_CSS

        cls.css = THEME_TOKENS_CSS
        cls.root_block = THEME_TOKENS_CSS.split(":root {", 1)[1].split("}", 1)[0]

    def test_font_stack_body_token_present(self):
        assert "--font-stack-body" in self.root_block
        # The default must be a system stack — no Google Fonts
        # dependency. `ui-sans-serif` is the modern-stack entry
        # point (Chromium 84+, Safari 17+, Firefox 109+).
        assert "ui-sans-serif" in self.root_block, "body stack missing the modern system entry point"
        assert "system-ui" in self.root_block, "body stack missing system-ui fallback"

    def test_font_stack_mono_token_present(self):
        assert "--font-stack-mono" in self.root_block
        # Same shape — modern-stack entry point first, then
        # platform-specific fallbacks.
        assert "ui-monospace" in self.root_block
        assert "monospace" in self.root_block, "mono stack missing generic monospace fallback"

    def test_size_scale_tokens_present(self):
        # Six-step scale covering xs..2xl. Matches Tailwind's
        # font-size scale at the same names so the migration is
        # obvious for anyone fluent in Tailwind.
        for size in (
            "--font-size-xs",
            "--font-size-sm",
            "--font-size-base",
            "--font-size-lg",
            "--font-size-xl",
            "--font-size-2xl",
        ):
            assert size in self.root_block, f"size token {size} missing"

    def test_base_size_is_one_rem(self):
        # The contract: --font-size-base equals 1rem (16px on the
        # browser default root). Anchoring at 1rem keeps the rest of
        # the scale predictable in terms of effective px.
        assert "--font-size-base:" in self.root_block
        # Find the line; it should contain `1rem`.
        for line in self.root_block.splitlines():
            if "--font-size-base:" in line:
                assert "1rem" in line, f"--font-size-base not 1rem: {line!r}"
                break
        else:
            raise AssertionError("--font-size-base line not found")

    def test_leading_tokens_present(self):
        for token in ("--leading-tight", "--leading-normal", "--leading-relaxed"):
            assert token in self.root_block, f"leading token {token} missing"

    def test_weight_tokens_present(self):
        for token in (
            "--font-weight-normal",
            "--font-weight-medium",
            "--font-weight-semibold",
            "--font-weight-bold",
        ):
            assert token in self.root_block, f"weight token {token} missing"


class TestZeta4TypographyUtilities:
    """`.theme-text-*` and `.theme-font-mono` and `.theme-weight-*`
    utility classes consume the typography tokens. Pin that they
    exist AND reference the var() lookups (not hardcoded sizes)."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOKENS_CSS

        cls.css = THEME_TOKENS_CSS

    def test_size_utility_classes_present(self):
        for cls in (
            ".theme-text-xs",
            ".theme-text-sm",
            ".theme-text-base",
            ".theme-text-lg",
            ".theme-text-xl",
            ".theme-text-2xl",
        ):
            assert cls in self.css, f"utility class {cls} missing"

    def test_size_classes_reference_var_lookups(self):
        # Sample a few — if these miss the var() reference, the
        # whole scale probably broke. Each utility's body should
        # contain `font-size: var(--font-size-<name>)`.
        for size_class, var_name in (
            (".theme-text-xs", "var(--font-size-xs)"),
            (".theme-text-sm", "var(--font-size-sm)"),
            (".theme-text-base", "var(--font-size-base)"),
            (".theme-text-2xl", "var(--font-size-2xl)"),
        ):
            idx = self.css.find(size_class + " ")
            if idx < 0:
                idx = self.css.find(size_class + "  ")
            assert idx >= 0, f"could not locate {size_class}"
            window = self.css[idx : idx + 200]
            assert var_name in window, f"{size_class} doesn't reference {var_name!r}; got {window[:120]!r}..."

    def test_size_classes_also_set_line_height(self):
        # Sizes without paired line-height are a footgun (sets
        # font-size but inherits parent's leading). Pin that each
        # size utility ALSO sets line-height.
        for size_class in (".theme-text-base", ".theme-text-2xl"):
            idx = self.css.find(size_class + " ")
            window = self.css[idx : idx + 200]
            assert "line-height" in window, f"{size_class} missing line-height — sizing without leading is incomplete"

    def test_font_mono_utility_present(self):
        assert ".theme-font-mono" in self.css
        # Find the actual rule definition (followed by ` {`),
        # not a passing mention in a doc comment.
        idx = self.css.find(".theme-font-mono {")
        if idx < 0:
            idx = self.css.find(".theme-font-mono  {")
        assert idx >= 0, "could not locate .theme-font-mono rule definition"
        window = self.css[idx : idx + 200]
        assert "var(--font-stack-mono)" in window, f".theme-font-mono rule body: {window!r}"

    def test_weight_utility_classes_present(self):
        for cls in (".theme-weight-normal", ".theme-weight-medium", ".theme-weight-semibold", ".theme-weight-bold"):
            assert cls in self.css, f"weight utility {cls} missing"


class TestZeta4BodyFontRule:
    """`THEME_TOKENS_CSS` must set `body { font-family: var(...) }`
    so every console that absorbs the marker inherits the themable
    font stack via the DOM cascade — no per-element retrofit
    required for the basic body-text experience."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOKENS_CSS

        cls.css = THEME_TOKENS_CSS

    def test_body_rule_present(self):
        # The rule must target `body` (not `html` or `*`). Tailwind
        # CDN's preflight sets `html { font-family: ... }`; we set
        # `body { font-family: ... }` to win the cascade for
        # descendants without an explicit class.
        assert "body {" in self.css, "missing `body { ... }` rule"

    def test_body_rule_references_font_stack_var(self):
        body_idx = self.css.find("body {")
        body_end = self.css.find("}", body_idx)
        body_block = self.css[body_idx:body_end]
        assert "var(--font-stack-body)" in body_block, (
            "body rule doesn't reference --font-stack-body — typography isn't themable"
        )

    def test_body_rule_sets_base_size_and_leading(self):
        # The base experience for unstyled text: 1rem at
        # leading-normal. Without this, every console would need to
        # set its own body sizing.
        body_idx = self.css.find("body {")
        body_end = self.css.find("}", body_idx)
        body_block = self.css[body_idx:body_end]
        assert "var(--font-size-base)" in body_block
        assert "var(--leading-normal)" in body_block


class TestZeta4PreflightRetrofit:
    """`/preflight` is the proof-of-concept retrofit — its
    headings + body text + details-list use the new themable
    typography vocabulary."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.preflight import PREFLIGHT_HTML

        cls.html = PREFLIGHT_HTML

    def test_h1_uses_theme_text_2xl(self):
        # Pre-ζ.4 the h1 was `text-2xl font-semibold` (Tailwind
        # utility). Now it's the themable equivalent.
        assert "theme-text-2xl" in self.html, "h1 not migrated to theme-text-2xl"
        assert "theme-weight-semibold" in self.html, "h1 not migrated to theme-weight-semibold"

    def test_body_paragraph_uses_theme_text_sm(self):
        assert "theme-text-sm" in self.html, "body paragraphs not migrated to theme-text-sm"

    def test_details_list_uses_themable_mono_var(self):
        # The dense data list uses --font-stack-mono via fallback
        # chain so a console that hasn't absorbed THEME_TOKENS_CSS
        # still gets the original ui-monospace stack.
        assert "var(--font-stack-mono" in self.html, "details-list font-family not migrated to themable var"

    def test_no_residual_tailwind_text_2xl_on_h1(self):
        # Same cascade-collision concern as ζ.2 body: leaving
        # `text-2xl` alongside `theme-text-2xl` would let Tailwind's
        # JIT-injected utility win the cascade and make the new
        # token un-overridable.
        # Find the h1 line and confirm it doesn't have the old class.
        for line in self.html.splitlines():
            if "Pre-flight checklist" in line and "<h1" in line:
                assert "text-2xl" not in line.replace("theme-text-2xl", ""), (
                    f"h1 still carries Tailwind text-2xl alongside theme-text-2xl: {line!r}"
                )
                break
        else:
            raise AssertionError("could not find h1 line containing 'Pre-flight checklist'")

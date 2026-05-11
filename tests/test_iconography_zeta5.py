"""ζ.5 — iconography pass pins.

Topic file (created alongside the ζ.5 ship, follows the ω.27
follow-on convention).

Coverage:
- TestZeta5IconsRegistry:       `ICONS_REGISTRY` includes the
  status icons the /preflight banner + per-check rows need
  (check, alert-triangle, x-circle), plus the utility icons
  ζ.6+ phases will draw on (info, chevron-right, external-link).
  Each entry is a valid SVG with the standard shape attributes.
- TestZeta5ThemeIconHelper:     `theme_icon(name)` returns the
  SVG string for known names, empty for unknown.
- TestZeta5ThemeIconsJs:        `THEME_ICONS_JS` exposes the
  registry via `window.ebibleIcons` as JSON; payload parses;
  every registry key is present.
- TestZeta5ThemeIconUtilityClass: `.theme-icon` CSS rule exists
  in THEME_TOKENS_CSS with the contract (1em sizing,
  currentColor stroke, fill none).
- TestZeta5ApplyDesignSystem:   `<!-- THEME_ICONS_JS -->` marker
  substitution works + idempotent + no-op without marker.
- TestZeta5PreflightWired:      /preflight absorbs the marker,
  exposes window.ebibleIcons, and the JS uses
  `statusIconHtml()` instead of unicode glyphs for banner +
  per-check status icons.

Pinning rationale: icons are visual contract — drift between
the SVG library and the JS that consumes it surfaces as
"broken images" or missing-content boxes in production.
Pinning the registry shape + JS exposure + /preflight wire-up
catches every class of icon drift at test time.
"""

from __future__ import annotations

import json
import re


class TestZeta5IconsRegistry:
    """`ICONS_REGISTRY` is the canonical icon source. Pin its
    shape (24x24 viewBox, currentColor stroke, aria-hidden) for
    every entry — that's the contract every consumer relies on."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import ICONS_REGISTRY

        cls.registry = ICONS_REGISTRY

    def test_required_status_icons_present(self):
        # /preflight banner + per-check rows map pass → check,
        # warn → alert-triangle, fail → x-circle.
        for required in ("check", "alert-triangle", "x-circle"):
            assert required in self.registry, f"required status icon missing: {required!r}"

    def test_utility_icons_present(self):
        # The ζ.6+ phases will draw on these (info banners,
        # disclosure indicators, external-link visual hint).
        for utility in ("info", "chevron-right", "external-link"):
            assert utility in self.registry, f"utility icon missing: {utility!r}"

    def test_every_entry_is_an_svg_element(self):
        for name, svg in self.registry.items():
            assert svg.startswith("<svg "), f"{name!r}: not wrapped in <svg ...>"
            assert svg.rstrip().endswith("</svg>"), f"{name!r}: no closing </svg>"

    def test_every_entry_uses_currentColor_stroke(self):
        # The whole point of inline SVG over <img>: stroke inherits
        # the parent's text color, so icons theme automatically with
        # ζ.1's color tokens.
        for name, svg in self.registry.items():
            assert 'stroke="currentColor"' in svg, f"{name!r}: not stroke=currentColor"
            assert 'fill="none"' in svg, f"{name!r}: not fill=none"

    def test_every_entry_uses_24x24_viewbox(self):
        # Lucide convention — all icons share the same coordinate
        # space so they look uniform when sized identically.
        for name, svg in self.registry.items():
            assert 'viewBox="0 0 24 24"' in svg, f"{name!r}: viewBox drift"

    def test_every_entry_is_aria_hidden(self):
        # Icons that accompany text don't need screen-reader
        # announcement (the text carries the meaning). Standalone
        # icon buttons must provide aria-label on the button
        # element instead.
        for name, svg in self.registry.items():
            assert 'aria-hidden="true"' in svg, f"{name!r}: missing aria-hidden"

    def test_every_entry_has_theme_icon_class(self):
        # `.theme-icon` provides the 1em sizing + currentColor
        # cascade. If the class is missing, the icon renders at
        # the SVG's intrinsic 24x24 px size.
        for name, svg in self.registry.items():
            assert 'class="theme-icon"' in svg, f"{name!r}: missing theme-icon class"

    def test_every_entry_records_its_name_via_data_attr(self):
        # `data-icon="<name>"` lets the DOM inspector identify
        # which icon was rendered without parsing the path data.
        for name, svg in self.registry.items():
            assert f'data-icon="{name}"' in svg, f"{name!r}: data-icon attribute drift"


class TestZeta5ThemeIconHelper:
    """`theme_icon(name)` is the Python-side helper for embedding
    icons in template f-strings."""

    def test_returns_svg_for_known_icon(self):
        from scripts.templates._design import theme_icon

        markup = theme_icon("check")
        assert markup.startswith("<svg ")
        assert markup.rstrip().endswith("</svg>")
        assert 'data-icon="check"' in markup

    def test_returns_empty_string_for_unknown_icon(self):
        # Graceful degradation — a typo doesn't crash the page.
        # Worth pinning so a future "raise" change is intentional.
        from scripts.templates._design import theme_icon

        assert theme_icon("nonexistent-icon") == ""


class TestZeta5ThemeIconsJs:
    """`THEME_ICONS_JS` exposes the registry to client-side code.
    Pin that the payload is valid JSON, parses to a dict, and
    contains every registry key."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import ICONS_REGISTRY, THEME_ICONS_JS

        cls.js = THEME_ICONS_JS
        cls.registry = ICONS_REGISTRY

    def test_is_a_script_block(self):
        assert self.js.startswith("<script>")
        assert self.js.rstrip().endswith("</script>")

    def test_exposes_window_ebible_icons(self):
        assert "window.ebibleIcons" in self.js

    def test_payload_is_valid_json(self):
        # Extract the JSON object after `window.ebibleIcons = ` up
        # to the trailing semicolon. Parse to confirm it's
        # well-formed (no broken-quote bug from un-encoded SVG).
        match = re.search(r"window\.ebibleIcons\s*=\s*(\{.*?\});", self.js, re.DOTALL)
        assert match is not None, "could not extract window.ebibleIcons JSON literal"
        data = json.loads(match.group(1))
        assert isinstance(data, dict)
        for name in self.registry:
            assert name in data, f"JS payload missing icon {name!r}"
            assert data[name] == self.registry[name], f"JS payload diverged for {name!r}"


class TestZeta5ThemeIconUtilityClass:
    """The `.theme-icon` CSS rule sizes the SVG to 1em of its
    parent's font-size and inherits stroke/fill via currentColor."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOKENS_CSS

        cls.css = THEME_TOKENS_CSS

    def test_theme_icon_rule_present(self):
        # Match the rule definition (followed by `{`), not a
        # passing mention in a doc comment.
        assert ".theme-icon {" in self.css

    def test_theme_icon_sizes_to_one_em(self):
        idx = self.css.find(".theme-icon {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "width: 1em" in block, "icon not sized to 1em"
        assert "height: 1em" in block

    def test_theme_icon_uses_currentColor(self):
        idx = self.css.find(".theme-icon {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "stroke: currentColor" in block, "icon doesn't inherit stroke color"
        assert "fill: none" in block, "icon should default to outline-style (fill: none)"

    def test_theme_icon_is_inline_block_for_baseline_alignment(self):
        # Inline-block + vertical-align tweak so an icon sits next
        # to text on the baseline without weird offsets.
        idx = self.css.find(".theme-icon {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "display: inline-block" in block
        assert "vertical-align" in block


class TestZeta5ApplyDesignSystem:
    """The new marker `<!-- THEME_ICONS_JS -->` substitutes
    correctly, is idempotent, and is a no-op on templates without
    the marker."""

    def test_substitutes_theme_icons_marker(self):
        from scripts.templates._design import THEME_ICONS_JS, apply_design_system

        before = "<head><!-- THEME_ICONS_JS --></head>"
        after = apply_design_system(before, "/preflight")
        assert "<!-- THEME_ICONS_JS -->" not in after
        assert THEME_ICONS_JS in after

    def test_no_op_when_marker_absent(self):
        from scripts.templates._design import THEME_ICONS_JS, apply_design_system

        before = "<html><body>hi</body></html>"
        after = apply_design_system(before, "/preflight")
        assert after == before
        assert THEME_ICONS_JS not in after

    def test_idempotent_on_second_call(self):
        from scripts.templates._design import apply_design_system

        once = apply_design_system("<!-- THEME_ICONS_JS -->", "/preflight")
        twice = apply_design_system(once, "/preflight")
        assert once == twice


class TestZeta5PreflightWired:
    """/preflight absorbs the icons JS marker and migrates its
    banner + per-check status icons from unicode glyphs to SVGs
    fetched from `window.ebibleIcons`."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.preflight import PREFLIGHT_HTML

        cls.html = PREFLIGHT_HTML

    def test_marker_substituted_at_module_load(self):
        assert "<!-- THEME_ICONS_JS -->" not in self.html

    def test_window_ebible_icons_present(self):
        assert "window.ebibleIcons" in self.html

    def test_uses_statusIconHtml_helper(self):
        # The JS-side lookup that pulls the SVG by status name.
        # Pin it so a refactor doesn't silently revert to the
        # unicode-glyph branch.
        assert "statusIconHtml" in self.html

    def test_no_residual_unicode_status_glyphs(self):
        # Pre-ζ.5 the banner JS contained `icon.textContent = '✓'`
        # / '⚠' / '✗'. Pin that those literal assignments are
        # gone — they'd still work but would defeat the whole
        # SVG-icon migration.
        # Allow the glyphs to appear elsewhere in the file (e.g.,
        # comments about the pre-ζ.5 behavior) — only flag the
        # actual `textContent = '<glyph>'` JS pattern.
        for glyph in ("'✓'", "'⚠'", "'✗'"):
            assert f"textContent = {glyph}" not in self.html, (
                f"unicode glyph {glyph} still being assigned via textContent — ζ.5 not fully migrated"
            )

    def test_banner_status_dispatch_maps_to_icon_names(self):
        # Pin the {pass: 'check', warn: 'alert-triangle',
        # fail: 'x-circle'} dispatch table that statusIconHtml
        # uses. If the names drift the icons disappear without
        # any test failure unless we pin this directly.
        assert "'check'" in self.html
        assert "'alert-triangle'" in self.html
        assert "'x-circle'" in self.html

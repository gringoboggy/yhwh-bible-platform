"""ζ.6 — toast notification pins.

Topic file (created alongside the ζ.6 ship, follows the ω.27
follow-on convention).

Coverage:
- TestZeta6ToastJs:              the `THEME_TOAST_JS` constant
  defines the `window.ebibleToast(message, kind)` API with the
  expected kind dispatch, auto-dismiss timer, ARIA contract
  (error → assertive; others → polite), and XSS-safe message
  insertion via textContent.
- TestZeta6ToastCss:             toast container + per-kind +
  dismiss + leaving + keyframe rules all present in
  THEME_TOKENS_CSS. Colors pull from ζ.1's --color-status-*;
  sizing pulls from ζ.4's --font-size-sm; icons assumed to
  live on .theme-icon (ζ.5).
- TestZeta6ApplyDesignSystem:    `<!-- THEME_TOAST_JS -->`
  marker substitution works + idempotent + no-op without marker.
- TestZeta6PreflightWired:       /preflight absorbs the marker,
  the loadPreflight error path uses `window.ebibleToast` instead
  of the inline fail-bg div (with graceful fallback if the toast
  API isn't yet loaded).

Pinning rationale: toasts are the project's first centralized
notification primitive. Drift in the kind dispatch, the ARIA
contract, the textContent escaping, or the auto-dismiss timer
would silently surface as accessibility regressions or unsafe
HTML rendering. Pin each contract piece explicitly.
"""

from __future__ import annotations


class TestZeta6ToastJs:
    """The `THEME_TOAST_JS` constant is the canonical toast API.
    Pin the public surface (`window.ebibleToast`), the kind →
    icon dispatch table, the ARIA contract, and the XSS-safe
    message handling."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOAST_JS

        cls.js = THEME_TOAST_JS

    def test_is_a_script_block(self):
        assert self.js.startswith("<script>")
        assert self.js.rstrip().endswith("</script>")

    def test_exposes_window_ebible_toast(self):
        assert "window.ebibleToast" in self.js, "ebibleToast API not exposed on window"

    def test_kind_dispatch_table_present(self):
        # Pin the four supported kinds + their icon names. A future
        # refactor renaming the icons (e.g., "x-circle" → "circle-x")
        # would silently produce empty toast leading icons unless
        # this dispatch + ICONS_REGISTRY stay in sync.
        for kind, icon_name in (
            ("info", "info"),
            ("success", "check"),
            ("warn", "alert-triangle"),
            ("error", "x-circle"),
        ):
            assert kind in self.js, f"kind {kind!r} missing from dispatch"
            assert icon_name in self.js, f"icon name {icon_name!r} for kind {kind!r} missing"

    def test_auto_dismiss_after_4_seconds(self):
        # The 4000ms duration matches material-design + ARIA toast
        # convention. Shorter feels rushed; longer blocks the
        # screen. Pin so a "make toasts dismiss faster" change is
        # intentional.
        assert "AUTO_DISMISS_MS = 4000" in self.js, "auto-dismiss timer drift"

    def test_error_uses_aria_alert_assertive(self):
        # Errors should interrupt screen readers immediately —
        # role=alert + aria-live=assertive. Other kinds get the
        # gentler role=status + aria-live=polite.
        # Pin the exact ternary so a future refactor can't quietly
        # promote everything to assertive (annoying) or demote
        # errors to polite (missed by users).
        assert "'alert' : 'status'" in self.js, "ARIA role dispatch drift"
        assert "'assertive' : 'polite'" in self.js, "aria-live dispatch drift"

    def test_message_inserted_via_textcontent_not_innerhtml(self):
        # XSS guard: if a caller passes user-controlled text, we
        # must not interpret it as HTML. textContent gives us that
        # automatically. Pin the call site.
        assert ".textContent = String(message)" in self.js, (
            "message inserted via something other than textContent — XSS risk"
        )

    def test_container_id_is_known(self):
        # `ebible-toast-container` is the hook for tests + future
        # ζ.* (e.g., a future system-status banner that wants to
        # render below the toast stack). Pin the id.
        assert "ebible-toast-container" in self.js

    def test_container_is_idempotent(self):
        # Calling ebibleToast twice in quick succession must reuse
        # the existing container, not stack a new one each call.
        assert "getElementById('ebible-toast-container')" in self.js, (
            "container creation not guarded — duplicates on repeated calls"
        )

    def test_dismiss_button_has_accessible_label(self):
        # The × button is icon-only; aria-label carries the meaning.
        assert "aria-label" in self.js
        # The label text matters too — "Dismiss notification" is
        # explicit about WHICH dismissable thing.
        assert "Dismiss notification" in self.js, "dismiss aria-label too vague"

    def test_unknown_kind_falls_back_to_info(self):
        # Defensive default: a caller passing a typo (e.g., 'sucess')
        # should still produce a usable toast, not break.
        # Pin the hasOwnProperty guard.
        assert "hasOwnProperty(kind)" in self.js, (
            "kind validation missing — unknown kinds would silently produce malformed toasts"
        )

    def test_hover_pauses_auto_dismiss(self):
        # Long messages need time to read; pausing on mouseenter is
        # a small but expected UX touch. Pin it so a future refactor
        # doesn't silently drop the listener.
        assert "mouseenter" in self.js, "auto-dismiss doesn't pause on hover"
        assert "clearTimeout" in self.js, "auto-dismiss timer not cancellable"


class TestZeta6ToastCss:
    """Toast CSS rules live in THEME_TOKENS_CSS (so they ship to
    every console that absorbs the marker). Pin the contract:
    container + per-kind + dismiss + leaving + keyframes."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOKENS_CSS

        cls.css = THEME_TOKENS_CSS

    def test_container_rule_present(self):
        # Container positions the stack and provides
        # pointer-events: none so click-through works on the
        # transparent surrounding area.
        assert ".theme-toast-container" in self.css
        idx = self.css.find(".theme-toast-container {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "position: fixed" in block
        assert "pointer-events: none" in block, (
            "container should be click-through; each toast re-enables pointer-events"
        )

    def test_base_toast_rule_present(self):
        assert ".theme-toast {" in self.css
        idx = self.css.find(".theme-toast {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        # Uses ζ.1 colors
        assert "var(--color-bg-surface)" in block
        assert "var(--color-text-primary)" in block
        # Uses ζ.4 typography
        assert "var(--font-size-sm)" in block

    def test_per_kind_rules_present(self):
        for kind in ("info", "success", "warn", "error"):
            assert f".theme-toast-{kind}" in self.css, f"kind rule {kind} missing"

    def test_per_kind_uses_status_color_vars(self):
        # Each kind's border + icon color pulls from
        # --color-status-* (ζ.1) so dark mode automatically
        # adjusts both.
        for kind, var_suffix in (
            ("info", "info"),
            ("success", "success"),
            ("warn", "warn"),
            ("error", "error"),
        ):
            expected_var = f"var(--color-status-{var_suffix})"
            # We just check that the var appears at least twice
            # near the kind class (once for border, once for icon).
            count = self.css.count(expected_var)
            assert count >= 2, (
                f"color-status-{var_suffix} referenced only {count}× — "
                f"toast-{kind} should reference it for border + icon"
            )

    def test_dismiss_button_rule_present(self):
        assert ".theme-toast-dismiss" in self.css
        # The button shouldn't grow when its parent flexes.
        idx = self.css.find(".theme-toast-dismiss {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "flex-shrink: 0" in block

    def test_leaving_animation_rule_present(self):
        assert ".theme-toast-leaving" in self.css
        assert "@keyframes theme-toast-out" in self.css

    def test_entering_animation_rule_present(self):
        assert "@keyframes theme-toast-in" in self.css


class TestZeta6ApplyDesignSystem:
    """The new marker `<!-- THEME_TOAST_JS -->` substitutes
    correctly, is idempotent, and is a no-op on templates without
    the marker."""

    def test_substitutes_theme_toast_marker(self):
        from scripts.templates._design import THEME_TOAST_JS, apply_design_system

        before = "<head><!-- THEME_TOAST_JS --></head>"
        after = apply_design_system(before, "/preflight")
        assert "<!-- THEME_TOAST_JS -->" not in after
        assert THEME_TOAST_JS in after

    def test_no_op_when_marker_absent(self):
        from scripts.templates._design import THEME_TOAST_JS, apply_design_system

        before = "<html><body>hi</body></html>"
        after = apply_design_system(before, "/preflight")
        assert after == before
        assert THEME_TOAST_JS not in after

    def test_idempotent_on_second_call(self):
        from scripts.templates._design import apply_design_system

        once = apply_design_system("<!-- THEME_TOAST_JS -->", "/preflight")
        twice = apply_design_system(once, "/preflight")
        assert once == twice


class TestZeta6PreflightWired:
    """/preflight absorbs the toast JS marker and migrates the
    loadPreflight error path from the ad-hoc `fail-bg` div to a
    `window.ebibleToast(..., 'error')` call."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.preflight import PREFLIGHT_HTML

        cls.html = PREFLIGHT_HTML

    def test_marker_substituted_at_module_load(self):
        assert "<!-- THEME_TOAST_JS -->" not in self.html

    def test_window_ebible_toast_present(self):
        assert "window.ebibleToast" in self.html

    def test_error_path_calls_ebible_toast(self):
        # The migrated loadPreflight catch block must call
        # ebibleToast with the 'error' kind so the user sees the
        # failure prominently.
        assert "window.ebibleToast('Failed to load preflight" in self.html, (
            "loadPreflight error path doesn't call ebibleToast"
        )
        assert "'error'" in self.html, "error kind not passed to ebibleToast"

    def test_graceful_fallback_preserved(self):
        # If THEME_TOAST_JS somehow hasn't loaded yet, the original
        # fail-bg div still appears (so the user isn't left staring
        # at a blank screen with no error indication).
        # Pin both branches exist in the source.
        assert "if (window.ebibleToast)" in self.html, (
            "missing window.ebibleToast presence check — would crash if toast JS hadn't loaded"
        )
        # Fallback path still renders the fail-bg div.
        assert "fail-bg" in self.html

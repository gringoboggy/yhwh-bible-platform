"""ν.7 — inline editing standardization pins.

Topic file (created alongside the ν.7 ship). Last Month 4
non-money phase before the Month 4 → Month 5 boundary pause.

Coverage:
- TestNu7EditableJs:           the `THEME_EDITABLE_JS` constant
  exposes `window.ebibleEditable.{bind, unbind}`, supports the
  full lifecycle (click → input → blur/Enter saves, Esc cancels),
  composes ζ.6 toast on failure, XSS-safe via textContent.
- TestNu7EditableCss:          5 visual states present in
  THEME_TOKENS_CSS (idle, hover, active, pending, error) using
  ζ.1 tokens.
- TestNu7ApplyDesignSystem:    marker substitution works.
- TestNu7PreflightWired:       /preflight absorbs the marker.

Pinning rationale: ν.7 is the FOUNDATION library that future per-
console retrofits (ν.7.x) adopt. Drift in the API surface, the
lifecycle, or the visual states would force each retrofit to roll
its own variant — defeats the standardization goal.
"""

from __future__ import annotations


class TestNu7EditableJs:
    """`THEME_EDITABLE_JS` JS contract."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_EDITABLE_JS

        cls.js = THEME_EDITABLE_JS

    def test_is_a_script_block(self):
        assert self.js.startswith("<script>")
        assert self.js.rstrip().endswith("</script>")

    def test_exposes_ebible_editable_api(self):
        assert "window.ebibleEditable" in self.js

    def test_exposes_bind_and_unbind(self):
        assert "bind:" in self.js
        assert "unbind:" in self.js

    def test_bind_requires_on_save(self):
        # Without onSave, the binding is meaningless — pin that
        # it throws. Future retrofits can't accidentally bind a
        # display-only element with the editable styling.
        assert "onSave is required" in self.js

    def test_supports_format_callback(self):
        # `format(value) → str` lets callers display formatted
        # versions (e.g., dates, currency).
        assert "format:" in self.js or "options.format" in self.js
        assert "defaultFormat" in self.js

    def test_supports_validate_callback(self):
        # `validate(newValue) → bool` lets callers gate save.
        assert "validate:" in self.js or "options.validate" in self.js
        assert "defaultValidate" in self.js

    def test_enter_key_commits_save(self):
        # Enter triggers commit() — pin so future "use Tab to
        # save" changes are intentional (Tab default behavior
        # differs from Enter; both are reasonable).
        assert "'Enter'" in self.js

    def test_escape_key_cancels(self):
        # Esc reverts to original — pin the standard text-input
        # convention.
        assert "'Escape'" in self.js

    def test_blur_commits_save(self):
        # Blur (focus loss) saves — proposal says "blur saves".
        assert "input.addEventListener('blur'" in self.js or "addEventListener('blur'" in self.js

    def test_uses_textcontent_for_xss_safety(self):
        # Saved values rendered via textContent, not innerHTML.
        # Pin so a future "render some HTML for rich-text edit"
        # change is intentional.
        assert "textContent = format(" in self.js or ".textContent = " in self.js
        # And explicitly NOT innerHTML for the value display
        assert ".innerHTML = format(" not in self.js
        assert ".innerHTML = newValue" not in self.js

    def test_failure_path_uses_toast(self):
        # On onSave throwing, compose ζ.6's toast for error UI.
        assert "window.ebibleToast" in self.js
        assert "'error'" in self.js

    def test_pending_state_disables_pointer_events(self):
        # Multi-click protection: while saving, pointer events
        # are disabled. The CSS does this via the
        # .theme-editable-pending class.
        assert "theme-editable-pending" in self.js

    def test_no_change_skips_on_save(self):
        # If user opens the editor and blurs without changing,
        # don't call onSave (unnecessary network traffic +
        # unnecessary toast on save-failed-but-no-change-anyway).
        assert "newValue === " in self.js or "originalText" in self.js


class TestNu7EditableCss:
    """5 visual states + input styling in THEME_TOKENS_CSS."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOKENS_CSS

        cls.css = THEME_TOKENS_CSS

    def test_idle_state_present(self):
        # `.theme-editable` (no suffix) is the idle/hover-ready
        # state.
        assert ".theme-editable {" in self.css
        idx = self.css.find(".theme-editable {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        # Idle should have a visual affordance — dashed border-
        # bottom is the standard pattern.
        assert "border-bottom" in block

    def test_hover_state_uses_theme_token(self):
        assert ".theme-editable:hover" in self.css

    def test_active_state_present(self):
        # `.theme-editable-active` for when the input is showing.
        assert ".theme-editable-active" in self.css
        idx = self.css.find(".theme-editable-active {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        # Active should use accent color (matches focus rings).
        assert "var(--color-accent)" in block

    def test_pending_state_disables_pointer_events(self):
        # The CSS-level pointer-events disable prevents double-
        # save from a rapid second click during async commit.
        assert ".theme-editable-pending" in self.css
        idx = self.css.find(".theme-editable-pending {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "pointer-events: none" in block

    def test_error_state_uses_status_color(self):
        # `.theme-editable-error` uses ζ.1's --color-status-error
        # so dark mode adapts automatically.
        assert ".theme-editable-error" in self.css
        idx = self.css.find(".theme-editable-error {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "var(--color-status-error)" in block

    def test_input_class_inherits_styling(self):
        # `.theme-editable-input` should `font: inherit` so the
        # input visually matches the surrounding text.
        assert ".theme-editable-input" in self.css
        idx = self.css.find(".theme-editable-input {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "font: inherit" in block, "input must inherit font for seamless swap-in"


class TestNu7ApplyDesignSystem:
    """Marker substitution."""

    def test_substitutes_marker(self):
        from scripts.templates._design import THEME_EDITABLE_JS, apply_design_system

        before = "<head><!-- THEME_EDITABLE_JS --></head>"
        after = apply_design_system(before, "/preflight")
        assert "<!-- THEME_EDITABLE_JS -->" not in after
        assert THEME_EDITABLE_JS in after

    def test_no_op_when_marker_absent(self):
        from scripts.templates._design import THEME_EDITABLE_JS, apply_design_system

        before = "<html><body>hi</body></html>"
        after = apply_design_system(before, "/preflight")
        assert after == before
        assert THEME_EDITABLE_JS not in after

    def test_idempotent_on_second_call(self):
        from scripts.templates._design import apply_design_system

        once = apply_design_system("<!-- THEME_EDITABLE_JS -->", "/preflight")
        twice = apply_design_system(once, "/preflight")
        assert once == twice


class TestNu7PreflightWired:
    """/preflight absorbs the editable marker (infrastructure only;
    no actual editable elements in /preflight)."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.preflight import PREFLIGHT_HTML

        cls.html = PREFLIGHT_HTML

    def test_marker_substituted(self):
        assert "<!-- THEME_EDITABLE_JS -->" not in self.html

    def test_ebible_editable_api_present(self):
        assert "window.ebibleEditable" in self.html

    def test_lives_in_head(self):
        head_end = self.html.find("</head>")
        head = self.html[:head_end]
        assert "window.ebibleEditable" in head

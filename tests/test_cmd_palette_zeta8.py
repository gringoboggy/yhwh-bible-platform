"""ζ.8 — command palette (Cmd+K) pins.

Topic file (created alongside the ζ.8 ship, follows the ω.27
follow-on convention).

Coverage:
- TestZeta8CmdPaletteJs:        the `THEME_CMD_PALETTE_JS`
  constant exposes `window.ebibleCmdPalette.{open,close,toggle}`,
  listens for Cmd+K / Ctrl+K, supports arrow / enter / escape
  keyboard nav, restores focus on close, and is XSS-safe via
  textContent for label / route.
- TestZeta8CmdPaletteConsoles:  the CONSOLES list is JSON-embedded
  in the JS payload — every Python entry appears in the JS.
- TestZeta8CmdPaletteCss:       backdrop + modal + input + list +
  item + selected + footer + kbd + keyframes all present in
  THEME_TOKENS_CSS; colors compose ζ.1 tokens.
- TestZeta8ApplyDesignSystem:   `<!-- THEME_CMD_PALETTE_JS -->`
  marker substitution works + idempotent + no-op without marker.
- TestZeta8PreflightWired:      /preflight absorbs the marker
  and exposes `window.ebibleCmdPalette` in rendered HTML.

Pinning rationale: ζ.8 closes the Month 2 modernization arc.
Drift in the keyboard binding (Cmd+K), the keyboard navigation,
the focus management, the ARIA contract, or the CONSOLES-list
sync would break the project's first global power-user UI.
Every contract piece gets an explicit assertion.
"""

from __future__ import annotations

import json
import re


class TestZeta8CmdPaletteJs:
    """The `THEME_CMD_PALETTE_JS` constant is the canonical
    palette behavior. Pin the public API, keyboard contract,
    focus management, and a11y surface."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_CMD_PALETTE_JS

        cls.js = THEME_CMD_PALETTE_JS

    def test_is_a_script_block(self):
        assert self.js.startswith("<script>")
        assert self.js.rstrip().endswith("</script>")

    def test_exposes_window_ebible_cmd_palette(self):
        assert "window.ebibleCmdPalette" in self.js, "palette API not exposed on window"

    def test_exposes_open_close_toggle_methods(self):
        # Three-method public surface — pin them by name. A
        # future refactor renaming `toggle` to `flip` would
        # silently break any caller (e.g., a header icon button).
        for method in ("open:", "close:", "toggle:"):
            assert method in self.js, f"palette API missing method {method!r}"

    def test_cmd_k_keyboard_shortcut_present(self):
        # Cmd+K (macOS) / Ctrl+K (everywhere else) — pin both
        # modifier checks so a future "just use Cmd" change is
        # intentional.
        assert "metaKey" in self.js, "missing metaKey check (Cmd on macOS)"
        assert "ctrlKey" in self.js, "missing ctrlKey check (Ctrl on Windows/Linux)"
        # k key check
        assert "'k'" in self.js, "missing 'k' key check"

    def test_keyboard_navigation_arrow_keys(self):
        for key in ("ArrowDown", "ArrowUp", "Escape", "Enter"):
            assert key in self.js, f"keyboard nav key {key} missing"

    def test_aria_dialog_contract(self):
        # Modal must declare role=dialog + aria-modal=true so
        # screen readers know to trap focus.
        assert "setAttribute('role', 'dialog')" in self.js
        assert "setAttribute('aria-modal', 'true')" in self.js
        assert "aria-label" in self.js, "modal missing aria-label"

    def test_listbox_semantics_for_results(self):
        # Each result row is a listbox option.
        assert 'role="listbox"' in self.js or "role: 'listbox'" in self.js
        assert "'option'" in self.js or 'role="option"' in self.js
        assert "aria-selected" in self.js
        assert "aria-activedescendant" in self.js

    def test_restores_focus_on_close(self):
        # When opened from a focusable element (e.g., a header
        # button), Esc should return focus there — not to body —
        # so keyboard users don't lose context.
        assert "restoreFocusTo" in self.js, "no focus-restore variable — keyboard users lose context on Esc"
        assert "document.activeElement" in self.js, "doesn't snapshot focus on open"

    def test_message_inserted_via_textcontent(self):
        # XSS guard for label + route — even though they come from
        # the project's own CONSOLES list today, future contributors
        # might add user-controlled entries. Pin textContent usage.
        assert ".textContent = c.label" in self.js, "label not via textContent"
        assert ".textContent = c.route" in self.js, "route not via textContent"

    def test_backdrop_click_closes(self):
        # Standard modal pattern — clicking outside the modal
        # closes it. Pin the target check that distinguishes
        # backdrop-clicks from modal-content-clicks.
        assert "e.target === backdrop" in self.js, (
            "backdrop click handler missing target check — would close on modal-content click too"
        )

    def test_input_autofocus_on_open(self):
        assert "input.focus()" in self.js, "input not focused on open — keyboard users have to mouse to it"

    def test_empty_state_handled(self):
        # Filtering down to zero matches shouldn't leave a blank
        # listbox — pin the "No matches." fallback.
        assert "No matches" in self.js


class TestZeta8CmdPaletteConsoles:
    """The CONSOLES list is JSON-embedded into the JS payload at
    module load. Pin that every Python entry made it across."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import CONSOLES, THEME_CMD_PALETTE_JS

        cls.consoles = CONSOLES
        cls.js = THEME_CMD_PALETTE_JS

    def test_payload_is_extractable_json(self):
        # The JS payload contains `var CONSOLES = [...]` — extract
        # the JSON literal and parse it.
        match = re.search(r"var CONSOLES\s*=\s*(\[.*?\]);", self.js, re.DOTALL)
        assert match is not None, "could not extract var CONSOLES JSON literal"
        data = json.loads(match.group(1))
        assert isinstance(data, list)
        assert len(data) == len(self.consoles)

    def test_every_python_console_is_in_the_js_payload(self):
        match = re.search(r"var CONSOLES\s*=\s*(\[.*?\]);", self.js, re.DOTALL)
        data = json.loads(match.group(1))
        # Build a set of (route, label) tuples for both sides.
        py_set = set(self.consoles)
        js_set = {(item["route"], item["label"]) for item in data}
        assert py_set == js_set, (
            f"CONSOLES drift between Python and JS payload — "
            f"only in py: {py_set - js_set!r}, only in js: {js_set - py_set!r}"
        )

    def test_each_entry_has_route_and_label_keys(self):
        match = re.search(r"var CONSOLES\s*=\s*(\[.*?\]);", self.js, re.DOTALL)
        data = json.loads(match.group(1))
        for entry in data:
            assert "route" in entry, f"entry missing route: {entry!r}"
            assert "label" in entry, f"entry missing label: {entry!r}"


class TestZeta8CmdPaletteCss:
    """Palette CSS rules in THEME_TOKENS_CSS. Pin backdrop +
    modal + input + list + item + selected + footer + kbd +
    keyframes — every visible piece of the palette UI."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOKENS_CSS

        cls.css = THEME_TOKENS_CSS

    def test_backdrop_rule_present(self):
        assert ".theme-cmd-backdrop" in self.css
        idx = self.css.find(".theme-cmd-backdrop {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "position: fixed" in block, "backdrop not fixed-position"
        assert "z-index" in block, "backdrop missing z-index — could be hidden under other content"

    def test_modal_rule_present_and_uses_theme_tokens(self):
        assert ".theme-cmd-modal" in self.css
        idx = self.css.find(".theme-cmd-modal {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        # ζ.1 surface + text + border
        assert "var(--color-bg-surface)" in block
        assert "var(--color-text-primary)" in block
        assert "var(--color-border)" in block

    def test_input_rule_uses_font_stack_body(self):
        assert ".theme-cmd-input" in self.css
        idx = self.css.find(".theme-cmd-input {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        # ζ.4 typography
        assert "var(--font-stack-body)" in block, "input doesn't use themable font stack"
        assert "var(--font-size-base)" in block

    def test_item_rule_present(self):
        assert ".theme-cmd-item" in self.css

    def test_item_selected_rule_uses_accent_color(self):
        # The highlighted row should use --color-accent (ζ.1) +
        # --color-text-on-accent so it stays readable in both
        # themes.
        assert ".theme-cmd-item-selected" in self.css
        idx = self.css.find(".theme-cmd-item-selected {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "var(--color-accent)" in block, "selected row doesn't use accent color"
        assert "var(--color-text-on-accent)" in block

    def test_route_uses_mono_stack(self):
        # The route hint (e.g., `/preflight`) renders in mono for
        # the typewriter / code feel.
        assert ".theme-cmd-item-route" in self.css
        idx = self.css.find(".theme-cmd-item-route")
        end = self.css.find("}", idx + 1)
        block = self.css[idx:end]
        assert "var(--font-stack-mono)" in block

    def test_kbd_rule_uses_mono_stack(self):
        assert ".theme-cmd-kbd" in self.css
        idx = self.css.find(".theme-cmd-kbd {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "var(--font-stack-mono)" in block, "kbd hint not in mono"

    def test_fade_in_keyframes_present(self):
        assert "@keyframes theme-cmd-fade-in" in self.css


class TestZeta8ApplyDesignSystem:
    """The new marker `<!-- THEME_CMD_PALETTE_JS -->` substitutes
    correctly, is idempotent, and is a no-op without marker."""

    def test_substitutes_marker(self):
        from scripts.templates._design import THEME_CMD_PALETTE_JS, apply_design_system

        before = "<head><!-- THEME_CMD_PALETTE_JS --></head>"
        after = apply_design_system(before, "/preflight")
        assert "<!-- THEME_CMD_PALETTE_JS -->" not in after
        assert THEME_CMD_PALETTE_JS in after

    def test_no_op_when_marker_absent(self):
        from scripts.templates._design import THEME_CMD_PALETTE_JS, apply_design_system

        before = "<html><body>hi</body></html>"
        after = apply_design_system(before, "/preflight")
        assert after == before
        assert THEME_CMD_PALETTE_JS not in after

    def test_idempotent_on_second_call(self):
        from scripts.templates._design import apply_design_system

        once = apply_design_system("<!-- THEME_CMD_PALETTE_JS -->", "/preflight")
        twice = apply_design_system(once, "/preflight")
        assert once == twice


class TestZeta8PreflightWired:
    """/preflight absorbs the palette marker — Cmd+K now opens
    the palette on this console (and any future console that
    adds the marker)."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.preflight import PREFLIGHT_HTML

        cls.html = PREFLIGHT_HTML

    def test_marker_substituted_at_module_load(self):
        assert "<!-- THEME_CMD_PALETTE_JS -->" not in self.html

    def test_window_ebible_cmd_palette_present(self):
        assert "window.ebibleCmdPalette" in self.html

    def test_cmd_k_listener_present(self):
        # The global keyboard listener — pin both modifier checks
        # so Cmd+K + Ctrl+K both work after substitution.
        assert "metaKey" in self.html
        assert "ctrlKey" in self.html

    def test_palette_js_lives_in_head(self):
        # The palette's keyboard listener attaches to document on
        # script load — it doesn't need to be in <head>, but
        # placing it there matches the pattern of the other
        # theme JS blocks and keeps the head-block ordering
        # explicit for future authors.
        head_end = self.html.find("</head>")
        assert head_end > 0
        head_section = self.html[:head_end]
        assert "window.ebibleCmdPalette" in head_section, (
            "palette JS not in <head> — keyboard listener attaches later than the other theme scripts"
        )

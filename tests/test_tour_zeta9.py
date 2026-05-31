"""ζ.9 — first-run tour engine pins (2026-05-12).

Month 6 #3 (Month-6 non-money). In-house tour overlay engine
(no Shepherd.js / Driver.js CDN dependency — per invariant I.1
"no heavy framework creep"). Mirrors the public-API shape of
Shepherd/Driver/Intro so a future migration is cheap.

Coverage:
- TestZeta9JsConstantShape:        THEME_TOUR_JS exists, is a
  <script> block, exports window.ebibleTour.{start, skip, next,
  back, startIfFirstRun, reset}.
- TestZeta9MarkerSubstituted:      apply_design_system replaces
  the THEME_TOUR_JS marker (a template that uses the marker gets
  the script body in the final HTML).
- TestZeta9MarkerDocumented:       apply_design_system's
  docstring lists the marker.
- TestZeta9XssGuards:              the engine uses textContent
  for caller-supplied step strings (title + body) and progress
  text — no innerHTML on caller strings.
- TestZeta9StorageKey:             first-run gate uses
  localStorage; default key is 'ebible_tour_seen_v1'; per-call
  override accepted.
- TestZeta9Accessibility:          tooltip has role="dialog" +
  aria-modal + aria-labelledby; ESC key handler installed.

Pinning rationale: ζ.9 is invisible to test runners (DOM-only,
no Python side), so the test suite pins the *string contents* of
the engine. Behavioral tests would need a JS runner; the
contract pinning catches regression at the level that matters
(marker substitution + first-run gate + step selectors).
"""

from __future__ import annotations


class TestZeta9JsConstantShape:
    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOUR_JS

        cls.js = THEME_TOUR_JS

    def test_is_script_block(self):
        assert self.js.startswith("<script>")
        assert self.js.endswith("</script>")

    def test_exports_window_ebibletour(self):
        assert "window.ebibleTour" in self.js
        # Each public method must be assigned.
        for fn in ("start", "skip", "next", "back", "startIfFirstRun", "reset"):
            assert f"{fn}:" in self.js, f"window.ebibleTour.{fn} missing from THEME_TOUR_JS"


class TestZeta9MarkerSubstituted:
    def test_apply_design_system_replaces_marker(self):
        from scripts.templates._design import apply_design_system

        html_in = "<html><head><!-- THEME_TOUR_JS --></head><body></body></html>"
        out = apply_design_system(html_in, "/ops")
        assert "<!-- THEME_TOUR_JS -->" not in out, "marker not substituted"
        assert "window.ebibleTour" in out, "THEME_TOUR_JS body not injected"


class TestZeta9MarkerDocumented:
    def test_apply_design_system_docstring_lists_marker(self):
        # The substitution-map docstring lists every supported
        # marker so future contributors can see the catalog.
        from scripts.templates._design import apply_design_system

        doc = apply_design_system.__doc__ or ""
        assert "<!-- THEME_TOUR_JS -->" in doc
        assert "THEME_TOUR_JS" in doc


class TestZeta9XssGuards:
    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOUR_JS

        cls.js = THEME_TOUR_JS

    def test_step_title_uses_text_content(self):
        # The step's title is rendered into the tooltip via
        # textContent (XSS-safe). Pin so a future refactor to
        # innerHTML would be caught.
        assert "titleEl.textContent" in self.js

    def test_step_body_uses_text_content(self):
        assert "bodyEl.textContent" in self.js

    def test_progress_uses_text_content(self):
        # Step counter text is also caller-controlled (step count
        # comes from steps.length); use textContent.
        assert "progressEl.textContent" in self.js

    def test_no_inner_html_for_caller_strings(self):
        # innerHTML may legitimately be used for empty resets, but
        # not for caller-supplied step strings. Search for the
        # specific anti-pattern.
        bad_patterns = [
            "titleEl.innerHTML",
            "bodyEl.innerHTML",
        ]
        for pat in bad_patterns:
            assert pat not in self.js, f"engine uses {pat} — XSS risk"


class TestZeta9StorageKey:
    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOUR_JS

        cls.js = THEME_TOUR_JS

    def test_default_storage_key(self):
        # The default storage key is what consoles inherit when
        # they don't pass one. Pin the v1 suffix so a future
        # tour-content change can intentionally bump to v2.
        assert "'ebible_tour_seen_v1'" in self.js or '"ebible_tour_seen_v1"' in self.js

    def test_first_run_check_uses_localstorage(self):
        # The first-run gate must use localStorage.getItem (so it
        # persists across reloads). sessionStorage would re-show
        # on every browser restart.
        assert "localStorage.getItem" in self.js
        assert "localStorage.setItem" in self.js
        # reset() must use removeItem so /apihelp's restart link
        # works.
        assert "localStorage.removeItem" in self.js


class TestZeta9Accessibility:
    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOUR_JS

        cls.js = THEME_TOUR_JS

    def test_tooltip_has_dialog_role(self):
        assert "'role', 'dialog'" in self.js or '"role", "dialog"' in self.js

    def test_tooltip_has_aria_modal(self):
        assert "aria-modal" in self.js

    def test_tooltip_has_aria_labelledby(self):
        # The title gets id="ebible-tour-title" and the dialog
        # references it.
        assert "aria-labelledby" in self.js
        assert "ebible-tour-title" in self.js

    def test_esc_key_handler_installed(self):
        # Pressing Escape during the tour skips it (same as the
        # Skip button). Pin the keydown listener + the Escape
        # branch.
        assert "addEventListener('keydown'" in self.js or 'addEventListener("keydown"' in self.js
        assert "'Escape'" in self.js or '"Escape"' in self.js

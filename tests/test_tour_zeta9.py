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
  the THEME_TOUR_JS marker; the inverse holds (a template that
  uses the marker gets the script body in the final HTML).
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
- TestZeta9ExecWiring:             EXEC_HTML includes the
  THEME_TOUR_JS marker (now substituted), declares 6 steps,
  calls startIfFirstRun with the ebible_tour_exec_v1 key,
  references the right selectors (#kpi-grid,
  #sales-import-section, #distribution-section,
  #press-kit-section).

Pinning rationale: ζ.9 is invisible to test runners (DOM-only,
no Python side), so the test suite pins the *string contents* of
the engine + EXEC_HTML wiring. Behavioral tests would need a
JS runner; the contract pinning catches regression at the level
that matters (marker substitution + first-run gate + step
selectors).
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
        out = apply_design_system(html_in, "/exec")
        assert "<!-- THEME_TOUR_JS -->" not in out, "marker not substituted"
        assert "window.ebibleTour" in out, "THEME_TOUR_JS body not injected"

    def test_consoles_with_marker_get_engine(self):
        # Sanity: a console that opts into the tour (currently only
        # /exec) ends up with the engine present in its compiled HTML.
        from scripts.templates.exec import EXEC_HTML

        assert "window.ebibleTour" in EXEC_HTML
        # The marker itself must NOT survive the substitution.
        assert "<!-- THEME_TOUR_JS -->" not in EXEC_HTML


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


class TestZeta9ExecWiring:
    @classmethod
    def setup_class(cls):
        from scripts.templates.exec import EXEC_HTML

        cls.html = EXEC_HTML

    def test_tour_invoked_on_load(self):
        assert "ebibleTour.startIfFirstRun" in self.html

    def test_uses_per_exec_storage_key(self):
        # Per-console key so /exec's tour and any future console's
        # tour can be tracked independently.
        assert "'ebible_tour_exec_v1'" in self.html

    def test_has_six_steps(self):
        # Pin step count so a future content refactor that
        # accidentally drops a step (e.g. forgets the welcome
        # modal) is caught.
        # Count by 'title:' occurrences inside the steps array —
        # each step has exactly one title.
        # The IIFE block declares `var steps = [...]`; we scope
        # the search to that block.
        marker = "var steps = ["
        start = self.html.find(marker)
        assert start >= 0
        end = self.html.find("];", start)
        block = self.html[start:end]
        title_count = block.count("title:")
        assert title_count == 6, f"expected 6 steps, found {title_count}"

    def test_steps_reference_canonical_selectors(self):
        # Each tour step targets a real /exec section; if a future
        # refactor renames the section IDs without updating the
        # tour, the tour will silently render as a centred modal.
        # Pin the expected selectors.
        for selector in (
            "#kpi-grid",
            "#sales-import-section",
            "#distribution-section",
            "#press-kit-section",
        ):
            assert selector in self.html, f"tour step references missing selector {selector!r}"

    def test_welcome_and_closing_are_centered_modals(self):
        # First + last step have selector: null so they centre as
        # modals. Pin that the steps array starts and ends with a
        # `selector: null` entry.
        marker = "var steps = ["
        start = self.html.find(marker)
        end = self.html.find("];", start)
        block = self.html[start:end]
        # Crude but effective: the block contains at least 2
        # "selector: null" tokens.
        assert block.count("selector: null") >= 2

    def test_first_run_guard_present(self):
        # startIfFirstRun() short-circuits when localStorage flag
        # is set. Pin that the call wraps the steps array.
        assert "if (!window.ebibleTour) return" in self.html
        assert "startIfFirstRun" in self.html

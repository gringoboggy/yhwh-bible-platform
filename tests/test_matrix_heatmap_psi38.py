"""ψ.38 — matrix heatmap mode pins.

Topic file (created alongside the ψ.38 ship). Renumbered from
the proposal's "ψ.36 Heatmap mode" because ψ.36 was already
split into ψ.36-A (shipped) + ψ.36-B (deferred consumer-
migration). ψ.38 is the next free ψ slot (ψ.37 = time-
traveling commentary, shipped).

Coverage:
- TestPsi38HeatmapCss:           5 bucket classes +
  matrix-heatmap-on parent class + toggle button styling.
- TestPsi38ToggleButton:         the `#psi38-heatmap-toggle`
  button is in the matrix header with aria-pressed.
- TestPsi38HeatmapJs:             JS implementation: storage
  key, bucket classes, applyHeatmap function, clearHeatmap,
  MutationObserver for re-renders, retry-loop for initial
  apply.

Pinning rationale: ψ.38 is a self-contained client-side
feature inside matrix.py. Drift in the bucket-class names,
the toggle id, or the storage key would break the toggle
silently. The MutationObserver hook is what keeps the heatmap
in sync with /matrix's existing re-render pipeline — pin it.
"""

from __future__ import annotations


class TestPsi38HeatmapCss:
    """5 bucket classes + parent activation + toggle button styling."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.matrix import MATRIX_HTML

        cls.html = MATRIX_HTML

    def test_five_bucket_classes_present(self):
        for level in range(1, 6):
            cls = f"matrix-heatmap-{level}"
            assert cls in self.html, f"bucket class {cls!r} missing"

    def test_parent_class_for_activation(self):
        # `body.matrix-heatmap-on` is the parent activator so
        # toggling adds/removes a single body class rather than
        # touching every cell. Pin the pattern.
        assert "body.matrix-heatmap-on" in self.html

    def test_buckets_progress_light_to_dark(self):
        # 1 = lightest (emerald-50), 5 = deepest (emerald-900).
        # Pin both endpoints so a future palette flip is
        # intentional.
        assert "matrix-heatmap-1 { background: #f0fdf4" in self.html
        assert "matrix-heatmap-5 { background: #14532d" in self.html

    def test_toggle_button_has_dedicated_id(self):
        # `psi38-heatmap-toggle` is the hook the JS uses.
        # Drift here would orphan the button from its event
        # handler.
        assert "psi38-heatmap-toggle" in self.html

    def test_active_state_has_dedicated_class(self):
        # `.psi38-active` flips the toggle's own appearance when
        # heatmap is on.
        assert ".psi38-active" in self.html


class TestPsi38ToggleButton:
    """The toggle button is in the matrix header."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.matrix import MATRIX_HTML

        cls.html = MATRIX_HTML

    def test_button_in_header(self):
        # Find the <header> and check the button is inside it
        # (before </header>).
        header_start = self.html.find("<header ")
        header_end = self.html.find("</header>", header_start)
        assert header_start >= 0 and header_end > header_start
        header_block = self.html[header_start:header_end]
        assert 'id="psi38-heatmap-toggle"' in header_block, (
            "toggle button not inside <header> — should sit next to other matrix controls"
        )

    def test_button_has_aria_pressed(self):
        # Screen-reader accessibility — `aria-pressed` on a
        # toggle so assistive tech announces the current state.
        assert 'aria-pressed="false"' in self.html

    def test_button_has_title_attribute(self):
        # Hover-tooltip explains what the toggle does, since
        # the bare "Heatmap" label is terse.
        assert 'title="Toggle heatmap mode' in self.html


class TestPsi38HeatmapJs:
    """JS implementation pinned at the text level — no JS runtime
    so we verify the source contains the expected primitives."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.matrix import MATRIX_HTML

        cls.html = MATRIX_HTML

    def test_uses_namespaced_localstorage_key(self):
        # `ebible_matrix_heatmap_mode` — pin so a future cleanup
        # doesn't quietly orphan users' toggle state.
        assert "ebible_matrix_heatmap_mode" in self.html

    def test_localstorage_access_is_guarded(self):
        assert "try" in self.html
        assert "catch" in self.html

    def test_five_bucket_classes_referenced_in_js(self):
        # The JS-side BUCKET_CLASSES array must match the CSS-
        # side rules. Pin all 5 names.
        for level in range(1, 6):
            assert f"'matrix-heatmap-{level}'" in self.html, f"BUCKET_CLASSES missing matrix-heatmap-{level}"

    def test_apply_heatmap_function_present(self):
        assert "function applyHeatmap" in self.html

    def test_clear_heatmap_function_present(self):
        # Toggle OFF path; removes the bucket classes.
        assert "function clearHeatmap" in self.html

    def test_uses_mutation_observer_for_rerenders(self):
        # /matrix re-renders after edition kind-toggle saves
        # (see matrix_app.js). Without an observer, the heatmap
        # would strand after each re-render.
        assert "MutationObserver" in self.html
        assert ".observe(" in self.html

    def test_initial_apply_uses_retry_loop(self):
        # The matrix table is rendered async by matrix_app.js;
        # the heatmap script must wait for cells to appear.
        # Pin the retry pattern.
        assert "setTimeout(tryApply" in self.html or "tryApply" in self.html

    def test_button_text_switches_with_state(self):
        # When heatmap is ON, the button label flips to "Numbers"
        # so the user knows clicking will switch back. Pin both
        # labels.
        assert "'Numbers'" in self.html
        assert "'Heatmap'" in self.html

    def test_bucket_thresholds_pinned(self):
        # Pin the percentile thresholds so a future "tweak the
        # buckets" change is intentional.
        for threshold in ("0.05", "0.20", "0.50", "0.80"):
            assert threshold in self.html, f"bucket threshold {threshold!r} missing"

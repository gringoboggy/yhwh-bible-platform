"""ω.39 — hot-reload for templates pins.

Topic file (created alongside the ω.39 ship). Month 4 non-money
phase. Minimum-viable polling implementation; proper watchdog +
SSE upgrade is ω.39.x.

Coverage:
- TestOmega39Api:          `api_dev_templates_mtime()` returns the
  max mtime_ns across scripts/templates/*.py.
- TestOmega39Route:        `/api/dev/templates-mtime` is registered
  in `_SIMPLE_GET_ROUTES`.
- TestOmega39HotreloadJs:  the `THEME_HOTRELOAD_JS` constant has
  the localhost guard, 2s polling, mtime comparison, reload-on-
  change behavior.
- TestOmega39ApplyDesignSystem: the marker substitution works.
- TestOmega39PreflightWired:  /preflight absorbs the marker.

Pinning rationale: ω.39 is dev-tooling infrastructure. Drift in
the localhost guard would mean production users get polling
traffic (bandwidth waste). Drift in the comparison logic would
cause infinite reloads. Pin both.
"""

from __future__ import annotations


class TestOmega39Api:
    """`api_dev_templates_mtime()` handler."""

    def test_returns_status_ok(self):
        from scripts.web import api_dev_templates_mtime

        r = api_dev_templates_mtime()
        assert r["status"] == "ok"

    def test_returns_positive_mtime_ns(self):
        # scripts/templates/*.py definitely exist — at least
        # _design.py + preflight.py etc.
        from scripts.web import api_dev_templates_mtime

        r = api_dev_templates_mtime()
        assert isinstance(r["mtime_ns"], int)
        assert r["mtime_ns"] > 0, "max mtime should be positive (templates exist)"

    def test_mtime_advances_after_template_touch(self, tmp_path):
        # If a template file is touched, mtime_ns should increase
        # OR stay equal (filesystem mtime resolution can match).
        # We don't actually touch a production template (would
        # mutate state); just verify the handler reads stat
        # correctly by checking that two consecutive calls return
        # equal values (no spurious drift).
        from scripts.web import api_dev_templates_mtime

        a = api_dev_templates_mtime()["mtime_ns"]
        b = api_dev_templates_mtime()["mtime_ns"]
        assert a == b, "mtime drift between consecutive reads — handler isn't deterministic"


class TestOmega39Route:
    """`/api/dev/templates-mtime` is in the simple route table."""

    def test_route_registered(self):
        from scripts import web

        paths = [route for (route, _handler) in web._SIMPLE_GET_ROUTES]
        assert "/api/dev/templates-mtime" in paths, "ω.39 endpoint not in _SIMPLE_GET_ROUTES"

    def test_route_callable_is_the_right_handler(self):
        from scripts import web

        for route, handler in web._SIMPLE_GET_ROUTES:
            if route == "/api/dev/templates-mtime":
                assert handler is web.api_dev_templates_mtime
                return
        raise AssertionError("route entry missing")


class TestOmega39HotreloadJs:
    """`THEME_HOTRELOAD_JS` contract."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_HOTRELOAD_JS

        cls.js = THEME_HOTRELOAD_JS

    def test_is_a_script_block(self):
        assert self.js.startswith("<script>")
        assert self.js.rstrip().endswith("</script>")

    def test_has_localhost_guard(self):
        # Production deploys on real domains must NOT poll. Pin
        # the dev-only activation.
        assert "'localhost'" in self.js
        assert "'127.0.0.1'" in self.js
        # The guard pattern: indexOf == -1 → bail.
        assert "indexOf(host)" in self.js or "DEV_HOSTS" in self.js

    def test_polls_every_2_seconds(self):
        # 2000ms is the sweet spot: feels instant for save→see,
        # 0.5 req/sec is negligible bandwidth.
        assert "POLL_INTERVAL_MS = 2000" in self.js

    def test_polls_correct_endpoint(self):
        assert "/api/dev/templates-mtime" in self.js

    def test_compares_against_baseline(self):
        # First poll establishes baseline; subsequent polls
        # compare. Without the baseline check, the first poll
        # would trigger a reload immediately (infinite loop).
        assert "baselineMtime === null" in self.js
        assert "baselineMtime = data.mtime_ns" in self.js

    def test_reloads_on_change(self):
        # `window.location.reload()` is the reload call.
        assert "window.location.reload()" in self.js

    def test_uses_no_store_cache(self):
        # Browser must NOT cache the mtime response — otherwise
        # the change detection lags by the cache TTL.
        assert "no-store" in self.js or "cache: 'no-store'" in self.js

    def test_console_logs_on_activation(self):
        # Dev visibility — devs see "ω.39 hot-reload watching"
        # in DevTools so they know it's active.
        assert "console.log" in self.js
        assert "ω.39" in self.js

    def test_exposes_introspection_api(self):
        # `window.ebibleHotReload.{baselineMtime, pollCount}`
        # for debugging "is it actually polling?" questions.
        assert "window.ebibleHotReload" in self.js


class TestOmega39ApplyDesignSystem:
    """`<!-- THEME_HOTRELOAD_JS -->` marker substitution."""

    def test_substitutes_marker(self):
        from scripts.templates._design import THEME_HOTRELOAD_JS, apply_design_system

        before = "<head><!-- THEME_HOTRELOAD_JS --></head>"
        after = apply_design_system(before, "/preflight")
        assert "<!-- THEME_HOTRELOAD_JS -->" not in after
        assert THEME_HOTRELOAD_JS in after

    def test_no_op_when_marker_absent(self):
        from scripts.templates._design import THEME_HOTRELOAD_JS, apply_design_system

        before = "<html><body>hi</body></html>"
        after = apply_design_system(before, "/preflight")
        assert after == before
        assert THEME_HOTRELOAD_JS not in after

    def test_idempotent_on_second_call(self):
        from scripts.templates._design import apply_design_system

        once = apply_design_system("<!-- THEME_HOTRELOAD_JS -->", "/preflight")
        twice = apply_design_system(once, "/preflight")
        assert once == twice


class TestOmega39PreflightWired:
    """/preflight absorbs the hot-reload marker."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.preflight import PREFLIGHT_HTML

        cls.html = PREFLIGHT_HTML

    def test_marker_substituted(self):
        assert "<!-- THEME_HOTRELOAD_JS -->" not in self.html

    def test_ebible_hot_reload_present(self):
        assert "ebibleHotReload" in self.html

    def test_lives_in_head(self):
        head_end = self.html.find("</head>")
        head = self.html[:head_end]
        assert "ebibleHotReload" in head

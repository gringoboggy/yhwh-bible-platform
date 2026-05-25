"""Wave 4 W4.3 (slice 2a) — server-side onboarding/first-run state.

The desktop app shows a first-run welcome flow on a fresh install. Whether the
user has been through onboarding is persisted in the same frozen-aware,
writable user-data root as builds (so it survives app restarts and is a single
source of truth, not per-browser localStorage). ``scripts.core.onboarding``
reads/writes a small marker file; ``paths.state_dir()`` anchors it.

NOTE: distinct from ``launcher.should_run_first_run_migration`` — that copies
bundled content/ to the user-data dir on first frozen launch (data migration);
this tracks whether the USER has seen the welcome flow (UX state).
"""

from __future__ import annotations


class TestStateDir:
    def test_state_dir_is_under_the_data_root(self, monkeypatch, tmp_path):
        from scripts.core import paths

        monkeypatch.setenv("YHWH_DATA_DIR", str(tmp_path))
        assert paths.state_dir() == tmp_path / "state"

    def test_state_dir_tracks_data_dir_override(self, monkeypatch, tmp_path):
        from scripts.core import paths

        # state_dir() resolves live (not cached), so a data-dir change is seen.
        monkeypatch.setenv("YHWH_DATA_DIR", str(tmp_path / "a"))
        assert paths.state_dir() == tmp_path / "a" / "state"
        monkeypatch.setenv("YHWH_DATA_DIR", str(tmp_path / "b"))
        assert paths.state_dir() == tmp_path / "b" / "state"


class TestOnboardingState:
    def test_fresh_install_is_first_run(self, tmp_path):
        from scripts.core import onboarding

        p = tmp_path / "onboarding.json"
        st = onboarding.onboarding_state(path=p)
        assert st["first_run"] is True
        assert st["onboarded_at"] is None

    def test_mark_onboarded_clears_first_run_and_persists(self, tmp_path):
        from scripts.core import onboarding

        p = tmp_path / "onboarding.json"
        st = onboarding.mark_onboarded(path=p)
        assert st["first_run"] is False
        assert st["onboarded_at"]  # an ISO timestamp is set
        assert p.is_file()
        # A fresh read sees the persisted state (survives a "restart").
        again = onboarding.onboarding_state(path=p)
        assert again["first_run"] is False
        assert again["onboarded_at"] == st["onboarded_at"]

    def test_mark_onboarded_is_idempotent_and_preserves_timestamp(self, tmp_path):
        from scripts.core import onboarding

        p = tmp_path / "onboarding.json"
        first = onboarding.mark_onboarded(path=p)
        second = onboarding.mark_onboarded(path=p)
        # Re-marking must not move the original onboarding moment.
        assert second["onboarded_at"] == first["onboarded_at"]

    def test_corrupt_state_file_is_treated_as_first_run(self, tmp_path):
        from scripts.core import onboarding

        p = tmp_path / "onboarding.json"
        p.write_text("{ this is not valid json", encoding="utf-8")
        st = onboarding.onboarding_state(path=p)
        # Corrupt/unreadable marker → safe default: show onboarding again.
        assert st["first_run"] is True
        assert st["onboarded_at"] is None

    def test_default_path_resolves_under_state_dir(self, monkeypatch, tmp_path):
        from scripts.core import onboarding, paths

        monkeypatch.setenv("YHWH_DATA_DIR", str(tmp_path))
        assert onboarding.onboarding_state()["first_run"] is True
        onboarding.mark_onboarded()
        assert (paths.state_dir() / "onboarding.json").is_file()
        assert onboarding.onboarding_state()["first_run"] is False


class TestOnboardingEndpoints:
    """`GET /api/onboarding` (read state) + `POST /api/onboarding/complete`
    (mark done) — thin adapters over scripts.core.onboarding. Tests isolate
    via YHWH_DATA_DIR so they never write the real user-data marker."""

    def test_api_onboarding_state_reports_first_run(self, monkeypatch, tmp_path):
        import scripts.web as web

        monkeypatch.setenv("YHWH_DATA_DIR", str(tmp_path))
        st = web.api_onboarding_state()
        assert st["first_run"] is True
        assert st["onboarded_at"] is None

    def test_api_onboarding_complete_marks_onboarded(self, monkeypatch, tmp_path):
        import scripts.web as web

        monkeypatch.setenv("YHWH_DATA_DIR", str(tmp_path))
        done = web.api_onboarding_complete(None, {})
        assert done["first_run"] is False
        assert done["onboarded_at"]
        assert web.api_onboarding_state()["first_run"] is False

    def test_onboarding_routes_are_registered(self):
        import scripts.web as web

        get_paths = {p for p, _ in web._SIMPLE_GET_ROUTES}
        assert "/api/onboarding" in get_paths
        post_patterns = [r.pattern for r, _ in web._POST_ROUTES]
        assert any("/api/onboarding/complete" in p for p in post_patterns)

    def test_onboarding_round_trip_over_http(self, monkeypatch, tmp_path):
        import json
        import threading
        import urllib.request
        from http.server import ThreadingHTTPServer

        from scripts.web import Handler

        monkeypatch.setenv("YHWH_DATA_DIR", str(tmp_path))
        srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            r = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/onboarding", timeout=5)
            assert json.loads(r.read().decode())["first_run"] is True
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/onboarding/complete",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            done = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
            assert done["first_run"] is False
            r2 = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/onboarding", timeout=5)
            assert json.loads(r2.read().decode())["first_run"] is False
        finally:
            srv.shutdown()


class TestWelcomeOverlay:
    """The first-run welcome overlay is injected into the root editor console
    (what the launcher opens). It checks GET /api/onboarding on load, shows a
    one-time modal on first run, and POSTs /api/onboarding/complete on Start
    (→ /wizard) or Skip. Built with DOM nodes, never innerHTML."""

    def test_overlay_injected_into_index(self):
        from scripts.web import INDEX_HTML

        assert "yhwh-welcome-backdrop" in INDEX_HTML

    def test_overlay_checks_onboarding_state_and_completes(self):
        from scripts.web import INDEX_HTML

        assert "/api/onboarding" in INDEX_HTML
        # /api/onboarding/complete is unique to the overlay — proves the
        # Start/Skip actions persist onboarding server-side.
        assert "/api/onboarding/complete" in INDEX_HTML

    def test_overlay_routes_start_to_wizard(self):
        from scripts.web import INDEX_HTML

        assert "/wizard" in INDEX_HTML

    def test_overlay_marker_was_substituted(self):
        from scripts.web import INDEX_HTML

        # The injection marker must be consumed at module load (no stray
        # marker left in the served HTML).
        assert "<!-- WELCOME_OVERLAY_JS -->" not in INDEX_HTML

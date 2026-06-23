"""ω.27 follow-on (2026-05-11) — θ desktop-binary cluster test classes,
split out of the monolithic ``tests/test_scripts.py`` into a topic
file alongside the other ω.27 follow-on splits.

Eighth topic extraction. The θ cluster covers the desktop-binary
shipping arc:

- θ.1   Desktop launcher (Tkinter shell, free-port discovery,
        first-run migration, build url, bootstrap, browser open,
        server start, main entrypoint, PyInstaller spec)
- θ.4   Installer scripts (macOS .dmg, Windows Inno Setup,
        Linux AppImage; line-ending hygiene)
- θ.3   Auto-update (appcast parsing/fetching, version
        comparison, latest-version + release-url resolution,
        appcast generation)

The section also bundles ψ.14 (v1.0 polish — header nav
substitution, buyer-arc CSS, design-system helpers) and the
DesktopShell tests (the pywebview/Tkinter shell selection).

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# Phase θ.1 — Desktop launcher
# ============================================================


class TestLauncherIsFrozen:
    """θ.1: ``is_frozen`` reflects ``sys.frozen`` set by PyInstaller."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.mod = importlib.import_module("scripts.launcher")

    def test_is_frozen_false_in_pytest(self):
        # pytest is never run from a PyInstaller bundle; sys.frozen
        # should be unset.
        assert self.mod.is_frozen() is False

    def test_is_frozen_true_when_sys_frozen_set(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        assert self.mod.is_frozen() is True

    def test_is_frozen_false_when_sys_frozen_falsy(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", 0, raising=False)
        assert self.mod.is_frozen() is False


class TestLauncherFreePortDiscovery:
    """θ.1: ``find_free_port`` honors a free preferred port and falls
    back to an OS-assigned free port when the preferred one is bound."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.mod = importlib.import_module("scripts.launcher")

    def test_returns_preferred_when_free(self):
        # Port 0 means "let the OS choose" — guaranteed-free.
        port = self.mod.find_free_port(0, "127.0.0.1")
        assert port > 0
        assert port < 65536

    def test_falls_back_when_preferred_bound(self):
        import socket as _socket

        # Squat on a port; pass it as preferred and confirm the
        # launcher returns a *different* free port instead.
        squatter = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        squatter.bind(("127.0.0.1", 0))
        squatter.listen(1)
        try:
            taken = squatter.getsockname()[1]
            got = self.mod.find_free_port(taken, "127.0.0.1")
            assert got != taken
            assert got > 0
        finally:
            squatter.close()

    def test_returns_int(self):
        port = self.mod.find_free_port(0, "127.0.0.1")
        assert isinstance(port, int)


class TestLauncherShouldRunFirstRunMigration:
    """θ.1: first-run migration trigger only fires when frozen
    AND the user-data content/ lacks the editions.yaml marker."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.mod = importlib.import_module("scripts.launcher")

    def test_returns_false_in_dev(self, monkeypatch):
        # Not frozen → never migrate.
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        assert self.mod.should_run_first_run_migration() is False

    def test_returns_true_when_frozen_and_marker_missing(
        self,
        monkeypatch,
        tmp_path,
    ):
        from scripts.core import paths as paths_mod

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(paths_mod, "user_data_root", lambda: tmp_path)
        # No content/editions.yaml at tmp_path → should migrate.
        assert self.mod.should_run_first_run_migration() is True

    def test_returns_false_when_frozen_and_already_migrated(
        self,
        monkeypatch,
        tmp_path,
    ):
        from scripts.core import paths as paths_mod

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(paths_mod, "user_data_root", lambda: tmp_path)
        (tmp_path / "content").mkdir()
        (tmp_path / "content" / "editions.yaml").write_text(
            "editions: []\n",
            encoding="utf-8",
        )
        assert self.mod.should_run_first_run_migration() is False


class TestLauncherBuildUrl:
    @classmethod
    def setup_class(cls):
        import importlib

        cls.mod = importlib.import_module("scripts.launcher")

    def test_localhost_address(self):
        assert self.mod.build_url("127.0.0.1", 8765) == "http://127.0.0.1:8765/"

    def test_displays_localhost_for_zero(self):
        # 0.0.0.0 is a bind-spec, not a navigable address — display
        # as localhost so the browser can actually open it.
        assert self.mod.build_url("0.0.0.0", 8765) == "http://localhost:8765/"

    def test_arbitrary_port(self):
        assert self.mod.build_url("127.0.0.1", 9999) == "http://127.0.0.1:9999/"


class TestLauncherBootstrap:
    """θ.1: ``bootstrap_user_data`` calls injectable migrate_fn and
    relays its dict result. Production default composes
    scripts.migrate_to_user_data."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.mod = importlib.import_module("scripts.launcher")

    def test_uses_injected_migrate_fn(self):
        seen = {"called": 0}

        def fake_migrate():
            seen["called"] += 1
            return {"copied": 7, "skipped": 0, "errors": []}

        result = self.mod.bootstrap_user_data(migrate_fn=fake_migrate)
        assert seen["called"] == 1
        assert result["copied"] == 7

    def test_default_composes_migrate_module(self, monkeypatch):
        # Verify the default path goes through perform_migration —
        # mock at the module level so we don't actually copy files.
        import scripts.migrate_to_user_data as mm

        seen = {"called": 0}

        def fake_perform(src, dst, *, force=False):
            seen["called"] += 1
            return {"copied": 0, "skipped": 0, "errors": []}

        monkeypatch.setattr(mm, "perform_migration", fake_perform)
        monkeypatch.setattr(mm, "_src_content", lambda: Path("/nonexistent/src"))
        monkeypatch.setattr(mm, "_dst_content", lambda: Path("/nonexistent/dst"))
        result = self.mod.bootstrap_user_data()
        assert seen["called"] == 1
        assert "copied" in result


class TestLauncherScheduleBrowserOpen:
    """θ.1: ``schedule_browser_open`` schedules a daemon Timer that
    invokes the injected opener with the URL."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.mod = importlib.import_module("scripts.launcher")

    def test_calls_opener_after_delay(self):

        seen = []

        def fake_opener(url):
            seen.append(url)
            return True

        timer = self.mod.schedule_browser_open(
            "http://localhost:8765/",
            delay=0.01,
            opener=fake_opener,
        )
        # Wait for the timer to fire (small budget; deterministic on
        # all but the slowest CI hosts).
        timer.join(timeout=2.0)
        assert seen == ["http://localhost:8765/"]

    def test_returns_timer_already_started(self):
        timer = self.mod.schedule_browser_open(
            "http://localhost:8765/",
            delay=10.0,  # long enough to inspect before firing
            opener=lambda url: None,
        )
        try:
            assert timer.is_alive() is True
            assert timer.daemon is True
        finally:
            timer.cancel()


class TestLauncherStartServer:
    """θ.1: ``start_server`` returns whatever the injected
    server_factory returns; default path imports web.Handler and
    binds a ThreadingHTTPServer."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.mod = importlib.import_module("scripts.launcher")

    def test_uses_injected_factory(self):
        seen = {}

        class FakeServer:
            def __init__(self, host, port):
                self.host, self.port = host, port

        def fake_factory(host, port):
            seen["call"] = (host, port)
            return FakeServer(host, port)

        result = self.mod.start_server(
            "127.0.0.1",
            8765,
            server_factory=fake_factory,
        )
        assert isinstance(result, FakeServer)
        assert seen["call"] == ("127.0.0.1", 8765)

    def test_default_factory_returns_threading_http_server(self):
        # Bind to port 0 so we don't conflict with anything; close
        # immediately. This exercises the real production path
        # (imports scripts.web.Handler).
        from http.server import ThreadingHTTPServer

        server = self.mod.start_server("127.0.0.1", 0)
        try:
            assert isinstance(server, ThreadingHTTPServer)
            assert server.server_address[0] == "127.0.0.1"
            assert server.server_address[1] > 0
        finally:
            server.server_close()


class TestLauncherMain:
    """θ.1: ``main`` orchestrates bootstrap → port → server → browser →
    serve, and propagates dependency-injection through each stage."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.mod = importlib.import_module("scripts.launcher")

    def _fake_factory(self, *, captured=None):
        class FakeServer:
            def __init__(self, host, port):
                self.host, self.port = host, port
                self.shutdown_called = False
                if captured is not None:
                    captured["server"] = self

            def shutdown(self):
                self.shutdown_called = True

            def server_close(self):
                pass

        def factory(host, port):
            return FakeServer(host, port)

        return factory

    def test_no_browser_skips_opener(self, capsys):
        opener_calls = []
        rc = self.mod.main(
            ["--no-browser", "--port", "0"],
            server_factory=self._fake_factory(),
            opener=lambda url: opener_calls.append(url),
            serve_fn=lambda: None,
        )
        assert rc == 0
        assert opener_calls == []
        out = capsys.readouterr().out
        assert "serving at:" in out

    def test_opens_browser_by_default(self):
        opener_calls = []

        def fake_opener(url):
            opener_calls.append(url)

        # serve_fn is a no-op so main() returns immediately AFTER the
        # browser-open Timer has been scheduled. Use a short sleep
        # via a join-on-the-timer pattern is overkill — instead, the
        # timer fires on a background thread; we wait briefly.
        rc = self.mod.main(
            ["--port", "0"],
            server_factory=self._fake_factory(),
            opener=fake_opener,
            serve_fn=lambda: None,
        )
        assert rc == 0
        # Give the daemon Timer a moment to fire (delay default 0.5s).
        import time as _time

        for _ in range(40):
            if opener_calls:
                break
            _time.sleep(0.05)
        assert len(opener_calls) == 1
        assert opener_calls[0].startswith("http://")

    def test_skip_bootstrap_does_not_call_migrate(self, monkeypatch):
        called = {"n": 0}

        def fake_migrate():
            called["n"] += 1
            return {"copied": 0, "skipped": 0, "errors": []}

        # Even when we *would* migrate (frozen + missing marker),
        # --skip-bootstrap short-circuits.
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        rc = self.mod.main(
            # Force browser shell so the test pins migration behavior
            # independent of whether PyWebView is installed (frozen + auto
            # would pick native once pywebview is present — RULES §8).
            ["--shell", "browser", "--no-browser", "--port", "0", "--skip-bootstrap"],
            server_factory=self._fake_factory(),
            migrate_fn=fake_migrate,
            serve_fn=lambda: None,
        )
        assert rc == 0
        assert called["n"] == 0

    def test_runs_migration_when_frozen_and_marker_missing(
        self,
        monkeypatch,
        tmp_path,
        capsys,
    ):
        from scripts.core import paths as paths_mod

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(paths_mod, "user_data_root", lambda: tmp_path)
        called = {"n": 0}

        def fake_migrate():
            called["n"] += 1
            return {"copied": 5, "skipped": 0, "errors": []}

        rc = self.mod.main(
            # Force browser shell so the test pins migration behavior
            # independent of whether PyWebView is installed (frozen + auto
            # would pick native once pywebview is present — RULES §8).
            ["--shell", "browser", "--no-browser", "--port", "0"],
            server_factory=self._fake_factory(),
            migrate_fn=fake_migrate,
            serve_fn=lambda: None,
        )
        assert rc == 0
        assert called["n"] == 1
        out = capsys.readouterr().out
        assert "First run" in out
        assert "Copied 5 files" in out

    def test_skips_migration_in_dev(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        called = {"n": 0}

        def fake_migrate():
            called["n"] += 1
            return {"copied": 0, "skipped": 0, "errors": []}

        rc = self.mod.main(
            ["--no-browser", "--port", "0"],
            server_factory=self._fake_factory(),
            migrate_fn=fake_migrate,
            serve_fn=lambda: None,
        )
        assert rc == 0
        assert called["n"] == 0

    def test_keyboard_interrupt_triggers_shutdown(self, capsys):
        captured = {}
        factory = self._fake_factory(captured=captured)

        def boom():
            raise KeyboardInterrupt

        rc = self.mod.main(
            ["--no-browser", "--port", "0"],
            server_factory=factory,
            serve_fn=boom,
        )
        assert rc == 0
        assert captured["server"].shutdown_called is True
        out = capsys.readouterr().out
        assert "stopping" in out

    def test_reports_port_fallback(self, capsys, monkeypatch):
        # Force find_free_port to report a different port than
        # requested so the "Port X busy" message fires.
        monkeypatch.setattr(self.mod, "find_free_port", lambda port, host: port + 1)
        rc = self.mod.main(
            ["--no-browser", "--port", "8765"],
            server_factory=self._fake_factory(),
            serve_fn=lambda: None,
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "Port 8765 busy" in out
        assert "8766" in out


class TestLauncherSpecAndBuildScripts:
    """θ.1: shipping artifacts (PyInstaller spec + build wrappers)
    exist and reference the correct entry point."""

    def test_launcher_spec_exists(self):
        spec = REPO_ROOT / "dev" / "launcher.spec"
        assert spec.is_file(), "dev/launcher.spec missing"

    def test_launcher_spec_references_launcher_entry(self):
        spec = (REPO_ROOT / "dev" / "launcher.spec").read_text(
            encoding="utf-8",
        )
        assert "scripts" in spec and "launcher.py" in spec

    def test_launcher_spec_bundles_content_dir(self):
        spec = (REPO_ROOT / "dev" / "launcher.spec").read_text(
            encoding="utf-8",
        )
        # The content/ template must be in the datas list so the
        # first-run migrator can copy it to user_data_root.
        assert '"content"' in spec or "'content'" in spec

    def test_build_desktop_sh_exists_and_invokes_pyinstaller(self):
        sh = REPO_ROOT / "dev" / "build_desktop.sh"
        assert sh.is_file()
        body = sh.read_text(encoding="utf-8")
        assert "PyInstaller" in body or "pyinstaller" in body
        assert "launcher.spec" in body

    def test_build_desktop_cmd_exists_and_invokes_pyinstaller(self):
        cmd = REPO_ROOT / "dev" / "build_desktop.cmd"
        assert cmd.is_file()
        body = cmd.read_text(encoding="utf-8", errors="replace")
        assert "PyInstaller" in body or "pyinstaller" in body
        assert "launcher.spec" in body


# ============================================================
# Phase θ.2 — Native desktop shell (PyWebView wrapper)
# ============================================================


class TestDesktopShellAvailability:
    """θ.2: ``is_pywebview_available`` returns a bool, robustly."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.mod = importlib.import_module("scripts.desktop_shell")

    def setup_method(self):
        # Each test starts with a clean cache so we observe fresh
        # state — otherwise the first call's bool sticks for the
        # rest of the test session.
        self.mod.is_pywebview_available.cache_clear()

    def test_returns_bool(self):
        result = self.mod.is_pywebview_available()
        assert isinstance(result, bool)

    def test_returns_false_when_import_fails(self, monkeypatch):
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *a, **kw):
            if name == "webview":
                raise ImportError("no webview here")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        self.mod.is_pywebview_available.cache_clear()
        assert self.mod.is_pywebview_available() is False

    def test_returns_false_on_other_import_errors(self, monkeypatch):
        # Backend libraries can blow up at import time on partial
        # installs; we treat anything non-success as "unavailable".
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *a, **kw):
            if name == "webview":
                raise RuntimeError("backend missing")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        self.mod.is_pywebview_available.cache_clear()
        assert self.mod.is_pywebview_available() is False


class TestDesktopShellSelectShellMode:
    """θ.2: ``select_shell_mode`` precedence — explicit force >
    auto (frozen + available → native, else browser)."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.mod = importlib.import_module("scripts.desktop_shell")

    def test_force_native_overrides_everything(self):
        assert (
            self.mod.select_shell_mode(
                frozen=False,
                available=False,
                force="native",
            )
            == "native"
        )

    def test_force_browser_overrides_everything(self):
        assert (
            self.mod.select_shell_mode(
                frozen=True,
                available=True,
                force="browser",
            )
            == "browser"
        )

    def test_auto_dev_picks_browser(self):
        # Dev (not frozen) prefers browser even when pywebview is
        # available — devtools, copy/paste URL, etc.
        assert (
            self.mod.select_shell_mode(
                frozen=False,
                available=True,
            )
            == "browser"
        )

    def test_auto_frozen_with_pywebview_picks_native(self):
        assert (
            self.mod.select_shell_mode(
                frozen=True,
                available=True,
            )
            == "native"
        )

    def test_auto_frozen_without_pywebview_falls_back(self):
        # Frozen build that can't find pywebview → browser
        # rather than crashing.
        assert (
            self.mod.select_shell_mode(
                frozen=True,
                available=False,
            )
            == "browser"
        )

    def test_unknown_force_value_falls_through_to_auto(self):
        # Defensive: "auto" is a sentinel handled by the launcher
        # before calling select_shell_mode, but if anything else
        # leaks through, behave like auto rather than raising.
        assert (
            self.mod.select_shell_mode(
                frozen=False,
                available=True,
                force="auto",
            )
            == "browser"
        )


class TestDesktopShellWindowConfig:
    """θ.2: ``window_config`` returns the kwargs dict for
    ``webview.create_window`` with sensible defaults."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.mod = importlib.import_module("scripts.desktop_shell")

    def test_includes_url(self):
        cfg = self.mod.window_config("http://localhost:8765/")
        assert cfg["url"] == "http://localhost:8765/"

    def test_default_title_is_branded(self):
        cfg = self.mod.window_config("http://x/")
        assert "YHWH" in cfg["title"]

    def test_default_size_reasonable(self):
        cfg = self.mod.window_config("http://x/")
        # 1280x900 chosen to fit MacBook Air 1440x900 with chrome.
        assert cfg["width"] >= 1024
        assert cfg["height"] >= 600

    def test_min_size_is_tuple(self):
        cfg = self.mod.window_config("http://x/")
        assert isinstance(cfg["min_size"], tuple)
        assert len(cfg["min_size"]) == 2

    def test_resizable_default_true(self):
        cfg = self.mod.window_config("http://x/")
        assert cfg["resizable"] is True

    def test_overrides_apply(self):
        cfg = self.mod.window_config(
            "http://x/",
            title="Custom",
            width=800,
            height=600,
            min_size=(400, 300),
            resizable=False,
        )
        assert cfg["title"] == "Custom"
        assert cfg["width"] == 800
        assert cfg["height"] == 600
        assert cfg["min_size"] == (400, 300)
        assert cfg["resizable"] is False


class TestDesktopShellOpenInNativeShell:
    """θ.2: ``open_in_native_shell`` calls create_window + start
    on the injected webview module; raises when missing."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.mod = importlib.import_module("scripts.desktop_shell")

    def test_uses_injected_webview(self):
        seen = {"create": [], "start": []}

        class FakeWebview:
            @staticmethod
            def create_window(**kwargs):
                seen["create"].append(kwargs)

            @staticmethod
            def start(debug=False):
                seen["start"].append({"debug": debug})

        self.mod.open_in_native_shell(
            "http://localhost:8765/",
            webview_module=FakeWebview,
        )
        assert len(seen["create"]) == 1
        assert seen["create"][0]["url"] == "http://localhost:8765/"
        assert seen["create"][0]["title"]  # non-empty default
        assert len(seen["start"]) == 1
        assert seen["start"][0]["debug"] is False

    def test_passes_debug_flag(self):
        seen = {"start": []}

        class FakeWebview:
            @staticmethod
            def create_window(**kwargs):
                pass

            @staticmethod
            def start(debug=False):
                seen["start"].append(debug)

        self.mod.open_in_native_shell(
            "http://x/",
            webview_module=FakeWebview,
            debug=True,
        )
        assert seen["start"] == [True]

    def test_passes_title_through(self):
        seen = {}

        class FakeWebview:
            @staticmethod
            def create_window(**kwargs):
                seen.update(kwargs)

            @staticmethod
            def start(debug=False):
                pass

        self.mod.open_in_native_shell(
            "http://x/",
            title="Custom Title",
            webview_module=FakeWebview,
        )
        assert seen["title"] == "Custom Title"

    def test_raises_when_pywebview_missing(self, monkeypatch):
        # Production fallback path: no injection AND no webview
        # importable → RuntimeError with a helpful message.
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *a, **kw):
            if name == "webview":
                raise ImportError("not installed")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        with pytest.raises(RuntimeError) as exc:
            self.mod.open_in_native_shell("http://x/")
        # Error message points the user at the fix.
        assert "pywebview" in str(exc.value).lower() or "PyWebView" in str(exc.value)


class TestLauncherShellModeIntegration:
    """θ.2: launcher's --shell flag picks the right path. Native
    mode runs server in a thread; browser mode unchanged."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.mod = importlib.import_module("scripts.launcher")

    def _fake_factory(self, *, captured=None):
        class FakeServer:
            def __init__(self, host, port):
                self.host, self.port = host, port
                self.shutdown_called = False
                self.serve_called = 0
                if captured is not None:
                    captured["server"] = self

            def serve_forever(self):
                self.serve_called += 1
                # Block briefly so the daemon thread is "alive"
                # for any test that inspects it; the launcher's
                # shutdown call will clear this when wired right.
                import time as _time

                _time.sleep(0.05)

            def shutdown(self):
                self.shutdown_called = True

            def server_close(self):
                pass

        def factory(host, port):
            return FakeServer(host, port)

        return factory

    def test_force_browser_uses_browser_path(self, capsys):
        rc = self.mod.main(
            ["--shell", "browser", "--no-browser", "--port", "0"],
            server_factory=self._fake_factory(),
            serve_fn=lambda: None,
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "shell:      browser" in out

    def test_force_native_calls_shell_fn_and_shuts_down(
        self,
        capsys,
    ):
        captured = {}
        seen_url = []

        def fake_shell(url):
            seen_url.append(url)

        rc = self.mod.main(
            ["--shell", "native", "--port", "0"],
            server_factory=self._fake_factory(captured=captured),
            shell_fn=fake_shell,
        )
        assert rc == 0
        assert len(seen_url) == 1
        assert seen_url[0].startswith("http://")
        assert captured["server"].shutdown_called is True
        out = capsys.readouterr().out
        assert "shell:      native" in out

    def test_native_mode_server_serves_in_thread(self):
        # Server should have been called via serve_forever from
        # the daemon thread (count >= 1) before shell_fn returned.
        captured = {}

        def fake_shell(url):
            # Give the daemon thread a beat to reach serve_forever.
            import time as _time

            _time.sleep(0.1)

        rc = self.mod.main(
            ["--shell", "native", "--port", "0"],
            server_factory=self._fake_factory(captured=captured),
            shell_fn=fake_shell,
        )
        assert rc == 0
        # Our fake serve_forever increments serve_called once
        # before returning. If launcher had run it on the main
        # thread, this would still be 1; the assertion confirms
        # at least the call happened. Thread-vs-main is asserted
        # by the fact that shell_fn ran AND shutdown_called is
        # True (proving control flow continued past serve_forever
        # in another thread).
        assert captured["server"].serve_called >= 1
        assert captured["server"].shutdown_called is True

    def test_auto_in_dev_picks_browser(self, monkeypatch, capsys):
        # Dev (not frozen) → auto picks browser regardless of
        # pywebview availability.
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        rc = self.mod.main(
            ["--no-browser", "--port", "0"],  # default --shell auto
            server_factory=self._fake_factory(),
            serve_fn=lambda: None,
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "shell:      browser" in out

    def test_native_mode_propagates_shell_fn_exception(self):
        # If the shell raises, the launcher must still call
        # server.shutdown — a rude crash shouldn't leave the
        # background server alive in a tray-icon-less binary.
        captured = {}

        def bad_shell(url):
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            self.mod.main(
                ["--shell", "native", "--port", "0"],
                server_factory=self._fake_factory(captured=captured),
                shell_fn=bad_shell,
            )
        assert captured["server"].shutdown_called is True


class TestLauncherSpecPywebview:
    """θ.2: PyInstaller spec lists pywebview in hiddenimports so
    the bundled binary can find it at runtime."""

    def test_spec_lists_webview_hidden_import(self):
        spec = (REPO_ROOT / "dev" / "launcher.spec").read_text(
            encoding="utf-8",
        )
        assert '"webview"' in spec or "'webview'" in spec


# ============================================================
# Phase ψ.14 — Buyer-arc polish
# ============================================================


class TestPsi14HeaderNavSubstitution:
    """ψ.14: the cross-link nav in /wizard, /export, /compare is now
    sourced from `_design.HEADER_NAV_LINKS()` at module load. Verify
    the substitution actually fires and produces canonical labels."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.wizard import WIZARD_HTML
        from scripts.templates.export import EXPORT_HTML
        from scripts.templates.compare import COMPARE_HTML
        from scripts.templates._design import (
            HEADER_NAV_LINKS,
            BUYER_ARC_POLISH_CSS,
            CONSOLES,
        )

        cls.htmls = {
            "wizard": WIZARD_HTML,
            "export": EXPORT_HTML,
            "compare": COMPARE_HTML,
        }
        cls.HEADER_NAV_LINKS = HEADER_NAV_LINKS
        cls.BUYER_ARC_POLISH_CSS = BUYER_ARC_POLISH_CSS
        cls.CONSOLES = CONSOLES

    def test_marker_is_fully_replaced(self):
        # If the substitution failed for any reason, the literal HTML
        # comment marker would still be in the rendered string.
        for name, html in self.htmls.items():
            assert "<!-- HEADER_NAV_LINKS -->" not in html, f"{name}: HEADER_NAV_LINKS marker not substituted"

    def test_polish_css_marker_is_replaced(self):
        for name, html in self.htmls.items():
            assert "<!-- BUYER_ARC_POLISH_CSS -->" not in html, f"{name}: BUYER_ARC_POLISH_CSS marker not substituted"

    def test_canonical_label_apihelp_present(self):
        # Each console's nav lists every other route. "apihelp" was
        # already there pre-ψ.14; this test guards against a future
        # regression where the substitution silently emits an empty
        # link list (the marker is gone but no links were inserted).
        for name, html in self.htmls.items():
            assert 'href="/apihelp"' in html, f"{name}: missing apihelp link after substitution"

    def test_current_console_marked_font_semibold(self):
        # The console rendering its own page should mark its own link
        # with font-semibold (the "you are here" indicator).
        cases = {
            "wizard": '<a href="/wizard" class="font-semibold">',
            "export": '<a href="/export" class="font-semibold">',
            "compare": '<a href="/compare" class="font-semibold">',
        }
        for name, expected in cases.items():
            assert expected in self.htmls[name], f"{name}: missing self-link with font-semibold"

    def test_other_consoles_marked_text_blue_600(self):
        # Non-current links use the underline-on-hover style.
        # Wizard's nav should NOT mark /export with font-semibold
        # (only /wizard).
        wizard = self.htmls["wizard"]
        assert '<a href="/export" class="text-blue-600 hover:underline">' in wizard
        # Mirror check for compare.
        compare = self.htmls["compare"]
        assert '<a href="/wizard" class="text-blue-600 hover:underline">' in compare

    def test_substitution_includes_all_consoles(self):
        # Every console route in the canonical CONSOLES list should
        # appear as an href in each substituted template.
        for name, html in self.htmls.items():
            for route, _label in self.CONSOLES:
                assert f'href="{route}"' in html, f"{name}: missing href={route} after substitution"


class TestPsi14BuyerArcPolishCSS:
    """ψ.14: polish CSS layer (focus rings, transitions, click feedback,
    dirty-state pill) is injected into the 3 buyer-arc consoles."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.wizard import WIZARD_HTML
        from scripts.templates.export import EXPORT_HTML
        from scripts.templates.compare import COMPARE_HTML
        from scripts.templates._design import BUYER_ARC_POLISH_CSS

        cls.htmls = {
            "wizard": WIZARD_HTML,
            "export": EXPORT_HTML,
            "compare": COMPARE_HTML,
        }
        cls.css = BUYER_ARC_POLISH_CSS

    def test_polish_css_block_substituted(self):
        # The polish block opens with <style> — verify each console
        # contains the unique-to-polish keyframe name so we know the
        # actual polish CSS landed (not just any <style> block).
        for name, html in self.htmls.items():
            assert "psi14StepFadeIn" in html, f"{name}: BUYER_ARC_POLISH_CSS not present"

    def test_focus_visible_outline_present(self):
        for name, html in self.htmls.items():
            assert ":focus-visible" in html, f"{name}: missing :focus-visible focus-ring rule"

    def test_active_press_feedback_present(self):
        for name, html in self.htmls.items():
            assert "button:active" in html, f"{name}: missing :active press-feedback rule"

    def test_dirty_state_pill_class_available(self):
        # The .psi14-pending class doesn't have to be USED in any
        # console for ψ.14, but it must be defined in the CSS so
        # ψ.15 (editor-console polish) can hook into it without
        # re-declaring it.
        for name, html in self.htmls.items():
            assert ".psi14-pending" in html, f"{name}: missing .psi14-pending dirty-state rule"

    def test_polish_css_constant_has_style_tags(self):
        # The constant returns a complete <style>...</style> block —
        # templates substitute the marker with the whole thing.
        assert self.css.strip().startswith("<style>")
        assert self.css.strip().endswith("</style>")


class TestPsi14DesignSystemHelpers:
    """ψ.14: HEADER_NAV_LINKS / BUYER_ARC_POLISH_CSS are exposed
    helpers in `_design.py`."""

    @classmethod
    def setup_class(cls):
        from scripts.templates import _design

        cls.mod = _design

    def test_header_nav_links_returns_string_without_div(self):
        # HEADER_NAV_LINKS is the inner-content variant — no
        # wrapping <div>. Useful when a console wants to add
        # sibling elements (corpus-progress badge) inside its nav.
        out = self.mod.HEADER_NAV_LINKS("/wizard")
        assert "<a href=" in out
        assert not out.lstrip().startswith("<div")

    def test_header_nav_wraps_links_in_div(self):
        # HEADER_NAV is the full block, including the wrapping div.
        out = self.mod.HEADER_NAV("/export")
        assert out.lstrip().startswith("<div")
        assert "</div>" in out
        assert "<a href=" in out

    def test_header_nav_links_marks_current_console(self):
        out = self.mod.HEADER_NAV_LINKS("/compare")
        assert '<a href="/compare" class="font-semibold">' in out

    def test_header_nav_links_unknown_route_marks_no_current(self):
        # Defensive: passing a route that isn't in CONSOLES means
        # nothing is marked current. Should not raise.
        out = self.mod.HEADER_NAV_LINKS("/nonexistent")
        assert 'class="font-semibold"' not in out

    def test_buyer_arc_polish_css_exports(self):
        assert isinstance(self.mod.BUYER_ARC_POLISH_CSS, str)
        assert len(self.mod.BUYER_ARC_POLISH_CSS) > 100


# ============================================================
# Phase θ.4 — Cross-platform installer wrappers
# ============================================================


class TestTheta4InstallerScriptsExist:
    """θ.4: build_dmg.sh, build_msi.cmd, installer.iss,
    build_appimage.sh exist as the per-platform wrappers around
    PyInstaller's dist/ output."""

    def _read(self, rel: str) -> str:
        return (REPO_ROOT / rel).read_text(
            encoding="utf-8",
            errors="replace",
        )

    def test_build_dmg_sh_exists(self):
        assert (REPO_ROOT / "dev" / "build_dmg.sh").is_file()

    def test_installer_iss_exists(self):
        assert (REPO_ROOT / "dev" / "installer.iss").is_file()

    def test_build_msi_cmd_exists(self):
        assert (REPO_ROOT / "dev" / "build_msi.cmd").is_file()

    def test_build_appimage_sh_exists(self):
        assert (REPO_ROOT / "dev" / "build_appimage.sh").is_file()


class TestTheta4MacOSDmgWrapper:
    def _body(self) -> str:
        return (REPO_ROOT / "dev" / "build_dmg.sh").read_text(
            encoding="utf-8",
            errors="replace",
        )

    def test_uses_hdiutil_macos_native(self):
        # hdiutil is system-bundled on macOS — no third-party dep.
        assert "hdiutil" in self._body()

    def test_invokes_pyinstaller_when_app_missing(self):
        # If dist/YHWH.app doesn't exist yet, the wrapper runs the
        # PyInstaller build first rather than failing cryptically.
        body = self._body()
        assert "build_desktop.sh" in body

    def test_codesign_is_optional(self):
        # CODESIGN_IDENTITY env var is the gate — unset = unsigned
        # build (works for personal use); set = production sign.
        body = self._body()
        assert "CODESIGN_IDENTITY" in body
        assert "codesign" in body

    def test_notarization_is_optional(self):
        # Notarization requires both CODESIGN_IDENTITY AND a stored
        # keychain profile. Both unset = no notarize step (safe).
        body = self._body()
        assert "notarytool" in body
        assert "NOTARIZE_KEYCHAIN_PROFILE" in body

    def test_refuses_on_non_macos(self):
        # The script bails early if uname != Darwin, pointing at
        # the right script for the actual platform.
        body = self._body()
        assert "Darwin" in body
        assert "build_msi.cmd" in body or "build_appimage.sh" in body


class TestTheta4WindowsInnoSetupWrapper:
    def test_iss_references_yhwh_exe(self):
        body = (REPO_ROOT / "dev" / "installer.iss").read_text(
            encoding="utf-8",
            errors="replace",
        )
        assert "YHWH.exe" in body

    def test_iss_reads_version_from_VERSION_file(self):
        body = (REPO_ROOT / "dev" / "installer.iss").read_text(
            encoding="utf-8",
            errors="replace",
        )
        # The Inno Setup ifexist+FileRead pattern — version
        # propagates from the project's VERSION file rather than
        # hard-coded in the spec. build_msi.cmd passes /DMyAppVersion=
        # (first line only, build_dmg.sh parity).
        assert "VERSION" in body
        assert "FileRead" in body
        assert "#ifndef MyAppVersion" in body

    def test_msi_cmd_passes_first_line_version_define(self):
        body = (REPO_ROOT / "dev" / "build_msi.cmd").read_text(
            encoding="utf-8",
            errors="replace",
        )
        assert "/DMyAppVersion=" in body

    def test_iss_emits_to_dist(self):
        body = (REPO_ROOT / "dev" / "installer.iss").read_text(
            encoding="utf-8",
            errors="replace",
        )
        # OutputDir lands the installer in dist/ alongside the
        # PyInstaller output.
        assert "OutputDir=..\\dist" in body or "OutputDir=../dist" in body

    def test_iss_signtool_is_opt_in(self):
        # SignTool= is commented out by default — unsigned installer
        # works for personal use, signed installer needs a configured
        # signtool command.
        body = (REPO_ROOT / "dev" / "installer.iss").read_text(
            encoding="utf-8",
            errors="replace",
        )
        assert "SignTool" in body
        # The line is commented out (Inno Setup uses ; for comments)
        assert "; SignTool=" in body

    def test_msi_cmd_locates_iscc(self):
        body = (REPO_ROOT / "dev" / "build_msi.cmd").read_text(
            encoding="utf-8",
            errors="replace",
        )
        assert "ISCC" in body
        # Probes the standard install paths
        assert "Inno Setup 6" in body

    def test_msi_cmd_invokes_pyinstaller_when_exe_missing(self):
        body = (REPO_ROOT / "dev" / "build_msi.cmd").read_text(
            encoding="utf-8",
            errors="replace",
        )
        assert "build_desktop.cmd" in body


class TestTheta4LinuxAppImageWrapper:
    def _body(self) -> str:
        return (REPO_ROOT / "dev" / "build_appimage.sh").read_text(
            encoding="utf-8",
            errors="replace",
        )

    def test_uses_appimagetool(self):
        assert "appimagetool" in self._body()

    def test_invokes_pyinstaller_when_binary_missing(self):
        body = self._body()
        assert "build_desktop.sh" in body

    def test_creates_appdir_with_apprun(self):
        # AppImages have a specific layout — AppRun executable +
        # .desktop + icon at the AppDir root.
        body = self._body()
        assert "AppRun" in body
        assert ".desktop" in body

    def test_refuses_on_non_linux(self):
        body = self._body()
        assert "Linux" in body
        assert "build_dmg.sh" in body or "build_msi.cmd" in body


class TestTheta4InstallerLineEndings:
    """θ.4: shell scripts use LF; cmd files use CRLF (per ω.7
    lesson — cmd's parser chokes on parenthesized blocks with bare
    LF). Catches a category of regression that bit dev/install_hooks.cmd."""

    def test_build_dmg_sh_is_lf(self):
        raw = (REPO_ROOT / "dev" / "build_dmg.sh").read_bytes()
        # Shell scripts MUST be LF on every platform — bash on
        # Windows (Git Bash) accepts LF, but CRLF breaks the
        # shebang line and many shells.
        assert b"\r\n" not in raw, "build_dmg.sh has CRLF line endings — must be LF"

    def test_build_appimage_sh_is_lf(self):
        raw = (REPO_ROOT / "dev" / "build_appimage.sh").read_bytes()
        assert b"\r\n" not in raw, "build_appimage.sh has CRLF line endings — must be LF"


# ============================================================
# Phase θ.3 — Auto-update data plane (Sparkle/WinSparkle appcast)
# ============================================================


class TestTheta3UpdatesParseAppcast:
    """θ.3: parse_appcast handles valid Sparkle XML, raises on
    malformed input, defensive on missing fields."""

    @classmethod
    def setup_class(cls):
        from scripts.core import updates

        cls.mod = updates

    def _valid_xml(self, version="1.2.0", url="https://x/y.dmg") -> bytes:
        return (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<rss version="2.0" xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle">'
            "<channel>"
            "<title>YHWH</title>"
            "<description>Updates</description>"
            "<language>en</language>"
            "<item>"
            "<title>Version 1.2.0</title>"
            "<pubDate>Fri, 08 May 2026 12:00:00 GMT</pubDate>"
            f'<enclosure url="{url}" sparkle:version="{version}" length="12345" type="application/octet-stream" />'
            "</item>"
            "</channel></rss>"
        ).encode()

    def test_parses_valid_appcast(self):
        out = self.mod.parse_appcast(self._valid_xml())
        assert out["channel"]["title"] == "YHWH"
        assert len(out["items"]) == 1
        assert out["items"][0]["version"] == "1.2.0"
        assert out["items"][0]["url"] == "https://x/y.dmg"
        assert out["items"][0]["length"] == 12345

    def test_raises_on_unparseable_xml(self):
        with pytest.raises(self.mod.AppcastError):
            self.mod.parse_appcast(b"not <even> xml")

    def test_raises_on_wrong_root_element(self):
        with pytest.raises(self.mod.AppcastError):
            self.mod.parse_appcast(b'<?xml version="1.0"?><foo></foo>')

    def test_raises_on_missing_channel(self):
        with pytest.raises(self.mod.AppcastError):
            self.mod.parse_appcast(b'<?xml version="1.0"?><rss version="2.0"></rss>')

    def test_handles_missing_enclosure(self):
        # Defensive: an item with no enclosure parses to empty
        # version/url/length rather than raising.
        xml = (
            b'<?xml version="1.0"?>'
            b'<rss version="2.0"><channel>'
            b"<title>YHWH</title><description>x</description><language>en</language>"
            b"<item><title>broken</title></item>"
            b"</channel></rss>"
        )
        out = self.mod.parse_appcast(xml)
        assert out["items"][0]["version"] == ""
        assert out["items"][0]["url"] == ""
        assert out["items"][0]["length"] == 0

    def test_handles_non_integer_length(self):
        xml = self._valid_xml().replace(
            b'length="12345"',
            b'length="not-a-number"',
        )
        out = self.mod.parse_appcast(xml)
        assert out["items"][0]["length"] == 0


class TestTheta3UpdatesFetchAppcast:
    """θ.3: fetch_appcast composes http_fn with parse_appcast.
    Network failures propagate; XML parse failures raise
    AppcastError."""

    @classmethod
    def setup_class(cls):
        from scripts.core import updates

        cls.mod = updates

    def test_uses_injected_http_fn(self):
        called = {}

        def fake_http(url):
            called["url"] = url
            return (
                b'<?xml version="1.0"?>'
                b'<rss version="2.0"><channel>'
                b"<title>X</title><description>x</description><language>en</language>"
                b"</channel></rss>"
            )

        out = self.mod.fetch_appcast(
            "https://example.com/appcast.xml",
            http_fn=fake_http,
        )
        assert called["url"] == "https://example.com/appcast.xml"
        assert out["channel"]["title"] == "X"

    def test_propagates_network_errors(self):
        def boom(url):
            raise OSError("network down")

        with pytest.raises(OSError):
            self.mod.fetch_appcast("https://x/a.xml", http_fn=boom)


class TestTheta3VersionComparison:
    """θ.3: compare_versions / is_update_available. Semver-aware
    with defensive handling of pre-release suffixes and missing
    components."""

    @classmethod
    def setup_class(cls):
        from scripts.core import updates

        cls.mod = updates

    def test_simple_semver(self):
        assert self.mod.compare_versions("1.0.0", "1.0.1") == -1
        assert self.mod.compare_versions("1.0.1", "1.0.0") == 1
        assert self.mod.compare_versions("1.0.0", "1.0.0") == 0

    def test_different_lengths(self):
        # 1.0 < 1.0.1 (the .1 is a strict addition)
        assert self.mod.compare_versions("1.0", "1.0.1") == -1
        assert self.mod.compare_versions("2.0", "1.9.99") == 1

    def test_numeric_components_sort_numerically(self):
        # Lexical compare would say "10" < "9"; numeric > 9.
        assert self.mod.compare_versions("1.10.0", "1.9.0") == 1

    def test_v_prefix_compares_distinct(self):
        # Contract: the comparator is purely lexical/numeric on
        # chunks; "v" is treated as an alpha component. The "v"
        # prefix is stripped upstream by
        # `releases_from_version_and_tags` before this function
        # ever sees a tag. Don't widen the comparator to strip "v"
        # — that would silently mask data-ingestion bugs.
        assert self.mod.compare_versions("v1.0.0", "1.0.0") != 0

    def test_pre_release_suffix(self):
        # SemVer §11: a final release outranks its own pre-releases, and
        # pre-releases order among themselves (rc1 < rc2). _version_key keys
        # on (core, pre_marker) where final = (1,) sorts after pre = (0, …).
        assert self.mod.compare_versions("1.0.0", "1.0.0-rc1") == 1
        assert self.mod.compare_versions("1.0.0-rc1", "1.0.0") == -1
        assert self.mod.compare_versions("1.0.0-rc1", "1.0.0-rc2") == -1
        assert self.mod.compare_versions("1.0.0-rc2", "1.0.0-rc1") == 1
        assert self.mod.compare_versions("1.0.0-rc1", "1.0.0-rc1") == 0
        # a pre-release of a HIGHER core still beats a lower final release
        assert self.mod.compare_versions("1.0.1-rc1", "1.0.0") == 1

    def test_empty_versions(self):
        assert self.mod.compare_versions("", "") == 0
        assert self.mod.compare_versions("", "1.0.0") == -1
        assert self.mod.compare_versions("1.0.0", "") == 1

    def test_is_update_available_when_newer_advertised(self):
        appcast = {
            "items": [
                {"version": "1.5.0"},
                {"version": "1.4.0"},
            ],
        }
        assert self.mod.is_update_available("1.0.0", appcast) is True

    def test_is_update_available_when_already_latest(self):
        appcast = {"items": [{"version": "1.5.0"}]}
        assert self.mod.is_update_available("1.5.0", appcast) is False

    def test_is_update_available_when_running_ahead(self):
        # Dev versions can be newer than the public appcast; don't
        # prompt to "downgrade".
        appcast = {"items": [{"version": "1.5.0"}]}
        assert self.mod.is_update_available("2.0.0", appcast) is False

    def test_is_update_available_with_empty_appcast(self):
        assert self.mod.is_update_available("1.0.0", {"items": []}) is False


class TestTheta3LatestVersionAndReleaseUrl:
    @classmethod
    def setup_class(cls):
        from scripts.core import updates

        cls.mod = updates

    def test_latest_version_picks_highest(self):
        # Sparkle convention is newest-first, but the function
        # picks max regardless of order.
        appcast = {
            "items": [
                {"version": "1.2.0"},
                {"version": "1.5.0"},
                {"version": "1.3.0"},
            ],
        }
        assert self.mod.latest_version(appcast) == "1.5.0"

    def test_latest_version_with_no_items(self):
        assert self.mod.latest_version({"items": []}) == ""

    def test_release_url_returns_url_for_latest(self):
        appcast = {
            "items": [
                {"version": "1.5.0", "url": "https://x/v1.5.0.dmg"},
                {"version": "1.2.0", "url": "https://x/v1.2.0.dmg"},
            ],
        }
        assert self.mod.release_url(appcast) == "https://x/v1.5.0.dmg"

    def test_release_url_returns_none_when_no_items(self):
        assert self.mod.release_url({"items": []}) is None

    def test_release_url_returns_none_when_url_missing(self):
        appcast = {"items": [{"version": "1.0.0", "url": ""}]}
        assert self.mod.release_url(appcast) is None


class TestTheta3GenerateAppcast:
    """θ.3: dev/generate_appcast.py — pure-function pipeline that
    composes a Sparkle-compatible XML feed from VERSION + git tags."""

    @classmethod
    def setup_class(cls):
        import importlib.util as _u

        spec = _u.spec_from_file_location(
            "_test_gen_appcast",
            REPO_ROOT / "dev" / "generate_appcast.py",
        )
        cls.mod = _u.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)
        from scripts.core import updates as _updates

        cls.updates = _updates

    def test_build_appcast_round_trip(self):
        # build → parse → fields match
        xml = self.mod.build_appcast(
            channel_title="YHWH",
            channel_description="Updates",
            base_url="https://example.com/r/",
            releases=[
                {"version": "1.0.0", "filename": "YHWH-1.0.0.dmg"},
            ],
        )
        parsed = self.updates.parse_appcast(xml.encode("utf-8"))
        assert parsed["channel"]["title"] == "YHWH"
        assert len(parsed["items"]) == 1
        item = parsed["items"][0]
        assert item["version"] == "1.0.0"
        assert item["url"] == "https://example.com/r/YHWH-1.0.0.dmg"

    def test_build_appcast_with_no_releases(self):
        # Defensive: empty release list produces a valid (if
        # itemless) appcast.
        xml = self.mod.build_appcast(
            channel_title="YHWH",
            channel_description="Updates",
            base_url="https://x/",
            releases=[],
        )
        parsed = self.updates.parse_appcast(xml.encode("utf-8"))
        assert parsed["items"] == []

    def test_build_appcast_strips_trailing_slash_on_base(self):
        xml1 = self.mod.build_appcast(
            channel_title="YHWH",
            channel_description="x",
            base_url="https://x/r/",
            releases=[{"version": "1.0.0", "filename": "y.dmg"}],
        )
        xml2 = self.mod.build_appcast(
            channel_title="YHWH",
            channel_description="x",
            base_url="https://x/r",
            releases=[{"version": "1.0.0", "filename": "y.dmg"}],
        )
        # Both URLs land at the same canonical form.
        assert "https://x/r/y.dmg" in xml1
        assert "https://x/r/y.dmg" in xml2

    def test_build_appcast_escapes_xml_chars(self):
        # Filenames with & < > " need escaping (defensive — real
        # filenames shouldn't but URLs encoded by hand might).
        xml = self.mod.build_appcast(
            channel_title="YHWH & Co.",
            channel_description="<b>Updates</b>",
            base_url="https://x",
            releases=[{"version": "1.0.0", "filename": "y.dmg"}],
        )
        # These chars must NOT appear unescaped in the XML body.
        assert "<b>Updates</b>" not in xml
        assert "&amp;" in xml or "YHWH and Co." in xml

    def test_releases_from_version_and_tags_dedupes(self):
        # If VERSION matches a tag, only one release entry is
        # emitted (no duplicate item for the same version).
        out = self.mod.releases_from_version_and_tags(
            current_version="1.5.0",
            tags=["v1.5.0", "v1.4.0", "1.3.0"],
            filename_pattern="YHWH-{version}.dmg",
        )
        versions = [r["version"] for r in out]
        assert versions.count("1.5.0") == 1
        assert "1.4.0" in versions
        assert "1.3.0" in versions

    def test_releases_strips_v_prefix(self):
        out = self.mod.releases_from_version_and_tags(
            current_version="",
            tags=["v2.0.0", "v1.9.0"],
            filename_pattern="YHWH-{version}.dmg",
        )
        assert all(not r["version"].startswith("v") for r in out)

    def test_filename_pattern_substitution(self):
        out = self.mod.releases_from_version_and_tags(
            current_version="1.0.0",
            tags=[],
            filename_pattern="YHWH-Setup-{version}.exe",
        )
        assert out[0]["filename"] == "YHWH-Setup-1.0.0.exe"

    def test_discover_git_tags_with_injected_runner(self):
        # Inject the run_fn so the test doesn't depend on actual
        # git tags or a clean working tree.
        def fake_run(args):
            return "v1.2.0\nv1.1.0\nv1.0.0\n"

        out = self.mod.discover_git_tags(run_fn=fake_run)
        assert out == ["v1.2.0", "v1.1.0", "v1.0.0"]

    def test_discover_git_tags_empty_when_no_git(self):
        def boom(args):
            raise FileNotFoundError("git not installed")

        assert self.mod.discover_git_tags(run_fn=boom) == []

    def test_main_writes_to_stdout(self, tmp_path, capsys):
        # Set up an isolated VERSION file; pin tags via injected
        # run_fn... actually main uses _run_git directly, so use
        # the version-file CLI flag and accept the global git
        # state of the project (tags may or may not exist).
        vf = tmp_path / "VERSION"
        vf.write_text("9.9.9\n", encoding="utf-8")
        rc = self.mod.main(
            [
                "--base-url",
                "https://example.com/r",
                "--version-file",
                str(vf),
            ]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "<rss" in out
        assert "9.9.9" in out
        assert "https://example.com/r" in out


class TestBuildOutputRootResolution:
    """W4.1 — paths._build_output_root() (the writable root for exports/, builds/,
    backups) resolves: YHWH_DATA_DIR override > user_data_root when frozen >
    content_root().parent in dev. Frozen must NOT root build output under the
    read-only PyInstaller _MEIPASS extraction dir (it would vanish on exit)."""

    def test_dev_uses_content_root_parent(self, monkeypatch):
        from scripts.core import paths

        monkeypatch.delenv("YHWH_DATA_DIR", raising=False)
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        assert paths._build_output_root() == paths.content_root().parent

    def test_frozen_uses_user_data_root(self, monkeypatch, tmp_path):
        from scripts.core import paths

        monkeypatch.delenv("YHWH_DATA_DIR", raising=False)
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(paths, "user_data_root", lambda: tmp_path)
        assert paths._build_output_root() == tmp_path

    def test_yhwh_data_dir_env_overrides_even_when_frozen(self, monkeypatch, tmp_path):
        from scripts.core import paths

        target = tmp_path / "datadir"
        monkeypatch.setenv("YHWH_DATA_DIR", str(target))
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        assert paths._build_output_root() == target

    def test_exports_dir_follows_the_root(self, monkeypatch, tmp_path):
        from scripts.core import paths

        monkeypatch.setenv("YHWH_DATA_DIR", str(tmp_path))
        assert paths.exports_dir() == tmp_path / "exports"


# ============================================================
# Frozen-safe script loaders (web_helpers._load_*_helpers)
# ============================================================


class TestFrozenSafeScriptLoaders:
    """Regression (2026-06-08, M1 device-QA): the note-editor's lazy
    script loaders must import ``note_quality`` / ``new_note`` as *package
    modules*, never via ``spec_from_file_location`` on a REPO-relative
    path.

    A frozen PyInstaller build ships no loose ``scripts/*.py`` on disk
    (the source lives in the bundled PYZ archive), so the old file-path
    loader raised ``FileNotFoundError`` at request time in the desktop
    app — breaking every endpoint that funnels through ``_nq()``/``_nn()``:
    ``/api/kinds`` (book-list load → "failed to load" toast + the list
    stuck on "loading…"), ``/api/template`` (new-note scaffold), and
    ``quality_for`` via ``/api/notes`` (viewing any book). Surfaced via
    the native macOS window and the browser shell alike (a server-layer
    bug, shell-independent).

    Simulated here by pointing ``REPO`` at a path with no ``scripts/``
    tree: a disk-path loader would fail; a package import is unaffected.
    """

    def test_note_quality_loader_ignores_repo_disk_path(self, monkeypatch, tmp_path):
        from scripts import web_helpers

        monkeypatch.setattr(web_helpers, "REPO", tmp_path / "no-such-repo")
        mod = web_helpers._load_note_quality_helpers()
        assert hasattr(mod, "budget_for")
        assert hasattr(mod, "run_checks")

    def test_new_note_loader_ignores_repo_disk_path(self, monkeypatch, tmp_path):
        from scripts import web_helpers

        monkeypatch.setattr(web_helpers, "REPO", tmp_path / "no-such-repo")
        mod = web_helpers._load_new_note_helpers()
        assert hasattr(mod, "template_for")

    def test_api_kinds_works_without_loose_scripts_on_disk(self, monkeypatch, tmp_path):
        # End-to-end: /api/kinds is the call that failed in the frozen
        # desktop app. It must succeed even when no loose scripts/*.py
        # exists on the REPO-relative path.
        from scripts import web_helpers, web_notes

        monkeypatch.setattr(web_helpers, "REPO", tmp_path / "no-such-repo")
        # bust the lazy module-cache so the loader re-runs under the patch
        monkeypatch.setattr(web_helpers, "_note_quality", None, raising=False)
        out = web_notes.api_kinds()
        assert isinstance(out.get("kinds"), list)
        assert out["kinds"], "api_kinds returned no kinds"

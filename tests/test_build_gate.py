"""Wave 4 W4.2 — concurrent-build cap (local resource safety).

The desktop app serves builds on a ThreadingHTTPServer; a heavy in-process
build (the frozen path copies the ~122 MB base, filters, then zips) must not
run twice at once or it doubles peak memory + disk churn on the user's machine.
``scripts.core.build_gate`` is a process-wide admission gate: at most
``YHWH_MAX_CONCURRENT_BUILDS`` (default 1) build slots. A build request that
can't get a slot raises ``BuildBusyError`` instead of starting a second concurrent
build; the HTTP layer translates that to 409.

These are the gate-semantics unit tests (no HTTP). The route-translation
integration tests (BuildBusyError → 409 on the two build endpoints) live in
``TestBuildRoutesRejectConcurrentBuilds`` below.
"""

from __future__ import annotations

import threading

import pytest


class TestBuildGateSlots:
    def test_default_max_is_one(self, monkeypatch):
        from scripts.core import build_gate

        monkeypatch.delenv("YHWH_MAX_CONCURRENT_BUILDS", raising=False)
        build_gate.reset()
        assert build_gate.max_slots() == 1

    def test_second_concurrent_slot_raises_build_busy(self, monkeypatch):
        from scripts.core import build_gate

        monkeypatch.delenv("YHWH_MAX_CONCURRENT_BUILDS", raising=False)
        build_gate.reset()
        with build_gate.build_slot():
            with pytest.raises(build_gate.BuildBusyError):
                with build_gate.build_slot():
                    pass

    def test_slot_is_released_after_normal_use(self, monkeypatch):
        from scripts.core import build_gate

        monkeypatch.delenv("YHWH_MAX_CONCURRENT_BUILDS", raising=False)
        build_gate.reset()
        with build_gate.build_slot():
            pass
        # The single slot is free again — re-acquiring must not raise.
        with build_gate.build_slot():
            pass

    def test_slot_is_released_even_when_the_body_raises(self, monkeypatch):
        from scripts.core import build_gate

        monkeypatch.delenv("YHWH_MAX_CONCURRENT_BUILDS", raising=False)
        build_gate.reset()
        with pytest.raises(ValueError):
            with build_gate.build_slot():
                raise ValueError("boom")
        # A failed build must not leak its slot — the next build can proceed.
        with build_gate.build_slot():
            pass

    def test_busy_rejection_does_not_consume_a_slot(self, monkeypatch):
        from scripts.core import build_gate

        monkeypatch.delenv("YHWH_MAX_CONCURRENT_BUILDS", raising=False)
        build_gate.reset()
        with build_gate.build_slot():
            with pytest.raises(build_gate.BuildBusyError):
                with build_gate.build_slot():
                    pass
            # The rejected attempt must not have decremented the gate: still
            # exactly one slot held, none leaked.
            assert build_gate.active_count() == 1
        assert build_gate.active_count() == 0

    def test_env_override_allows_more_slots(self, monkeypatch):
        from scripts.core import build_gate

        monkeypatch.setenv("YHWH_MAX_CONCURRENT_BUILDS", "2")
        build_gate.reset()
        assert build_gate.max_slots() == 2
        with build_gate.build_slot():
            with build_gate.build_slot():
                with pytest.raises(build_gate.BuildBusyError):
                    with build_gate.build_slot():
                        pass

    def test_invalid_env_falls_back_to_default(self, monkeypatch):
        from scripts.core import build_gate

        monkeypatch.setenv("YHWH_MAX_CONCURRENT_BUILDS", "not-a-number")
        build_gate.reset()
        assert build_gate.max_slots() == 1

    def test_zero_or_negative_env_falls_back_to_default(self, monkeypatch):
        from scripts.core import build_gate

        monkeypatch.setenv("YHWH_MAX_CONCURRENT_BUILDS", "0")
        build_gate.reset()
        assert build_gate.max_slots() == 1

    def test_active_count_tracks_held_slots(self, monkeypatch):
        from scripts.core import build_gate

        monkeypatch.setenv("YHWH_MAX_CONCURRENT_BUILDS", "2")
        build_gate.reset()
        assert build_gate.active_count() == 0
        with build_gate.build_slot():
            assert build_gate.active_count() == 1
            with build_gate.build_slot():
                assert build_gate.active_count() == 2
            assert build_gate.active_count() == 1
        assert build_gate.active_count() == 0

    def test_gate_serializes_contending_threads(self, monkeypatch):
        """Two threads race for a single slot: the holder gets in and the
        contender is rejected with BuildBusyError (non-blocking — a second build
        request is rejected, never silently queued)."""
        from scripts.core import build_gate

        monkeypatch.delenv("YHWH_MAX_CONCURRENT_BUILDS", raising=False)
        build_gate.reset()

        started = threading.Event()
        release = threading.Event()
        outcomes: dict[str, str] = {}

        def hold():
            try:
                with build_gate.build_slot():
                    started.set()
                    release.wait(2)
                outcomes["holder"] = "ok"
            except build_gate.BuildBusyError:
                outcomes["holder"] = "busy"

        def contend():
            started.wait(2)
            try:
                with build_gate.build_slot():
                    outcomes["contender"] = "ok"
            except build_gate.BuildBusyError:
                outcomes["contender"] = "busy"

        t1 = threading.Thread(target=hold)
        t2 = threading.Thread(target=contend)
        t1.start()
        t2.start()
        t2.join(3)
        release.set()
        t1.join(3)

        assert outcomes["holder"] == "ok"
        assert outcomes["contender"] == "busy"


class TestBuildRoutesRejectConcurrentBuilds:
    """The two build endpoints must translate a full gate into HTTP 409 and
    must NOT start a build while another is already in progress. The real
    builder is mocked, so these prove admission control (not the build): when
    the gate is held, the route returns 409 and never calls the builder."""

    @staticmethod
    def _serve():
        from http.server import ThreadingHTTPServer

        from scripts.web import Handler

        srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        return srv, port

    def test_export_build_returns_409_and_skips_build_when_busy(self, monkeypatch):
        import json
        import urllib.error
        import urllib.request

        import scripts.web as web
        from scripts.core import build_gate

        called = {"n": 0}

        def _never(*a, **k):
            called["n"] += 1
            return {"ok": True, "filename": "should-not-build.epub"}

        monkeypatch.setattr(web, "api_export_build", _never)
        monkeypatch.delenv("YHWH_MAX_CONCURRENT_BUILDS", raising=False)
        build_gate.reset()

        srv, port = self._serve()
        try:
            with build_gate.build_slot():  # occupy the only slot
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/export/build/catholic-study",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with pytest.raises(urllib.error.HTTPError) as exc:
                    urllib.request.urlopen(req, timeout=5)
                assert exc.value.code == 409, f"expected 409, got {exc.value.code}"
                body = json.loads(exc.value.read().decode())
                assert body.get("error") == "build_in_progress"
            assert called["n"] == 0, "the builder must not run while the gate is full"
        finally:
            srv.shutdown()

    def test_build_all_returns_409_when_busy(self, monkeypatch):
        import json
        import urllib.error
        import urllib.request

        import scripts.web as web
        from scripts.core import build_gate

        called = {"n": 0}

        def _never(*a, **k):
            called["n"] += 1
            return {"ok": True, "success_count": 1}

        monkeypatch.setattr(web, "api_build_all_editions", _never)
        monkeypatch.delenv("YHWH_MAX_CONCURRENT_BUILDS", raising=False)
        build_gate.reset()

        srv, port = self._serve()
        try:
            with build_gate.build_slot():  # occupy the only slot
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/build-all",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with pytest.raises(urllib.error.HTTPError) as exc:
                    urllib.request.urlopen(req, timeout=5)
                assert exc.value.code == 409, f"expected 409, got {exc.value.code}"
                body = json.loads(exc.value.read().decode())
                assert body.get("error") == "build_in_progress"
            assert called["n"] == 0, "the builder must not run while the gate is full"
        finally:
            srv.shutdown()

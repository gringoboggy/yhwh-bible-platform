"""5.10 (2026-06-10 audit) — error payloads must not ship at HTTP 200.

Eight GET surfaces previously sent their error bodies with a silent 200:

Six legacy routes whose handlers return a top-level ``{"error": ...}``
dict (no ``status``/``http`` envelope) — the route adapter now owns the
HTTP translation (RULES §9 thin-route-adapter; handler return shapes are
pinned by other consumers and stay unchanged):

1. GET /api/scenarios/<name>            → 400 / 404 / 500 by shape
2. GET /api/sources/<book>              → 404 (unknown book)
3. GET /api/edition/<id>/disabled-notes → 404 (unknown edition)
4. GET /api/notes/<book>                → 404 (book not found)
5. GET /api/export/preview/<edition_id> → 404 (unknown edition)
6. GET /api/compare                     → 400 (input validation)

Two routes that already return the STANDARD ``{"status": "error",
"http": ...}`` envelope but bypassed the translating dispatch:

7. GET /api/sources/cache → now routed through _dispatch_table_result
8. GET /api/apihelp       → moved _SIMPLE_GET_ROUTES → _REGEX_GET_ROUTES
                            (the mint-6 api_distribution_rollup precedent)

Test mechanism mirrors the established suite patterns: a FakeHandler
capture for the dispatch helpers (tests/test_web_routetable.py) plus the
live ThreadingHTTPServer smoke for end-to-end route translation
(tests/test_scripts.py::test_apihelp_route_serves_html_and_data).
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request


class FakeHandler:
    """Capture shim matching the _send_json surface (routetable pattern)."""

    def __init__(self):
        self.sent = None
        self.status = None

    def _send_json(self, body, status=200):
        self.sent = body
        self.status = status


# ---------- unit: the 5.10 route-adapter helpers ----------------------


class TestSendJsonWithErrorStatus:
    def test_error_dict_gets_declared_status(self):
        from scripts.web import _send_json_with_error_status

        h = FakeHandler()
        _send_json_with_error_status(h, {"error": "unknown book: zzz"})
        assert h.status == 404
        # Body is passed through UNCHANGED — handler shapes are pinned.
        assert h.sent == {"error": "unknown book: zzz"}

    def test_error_status_override_for_invalid_input(self):
        from scripts.web import _send_json_with_error_status

        h = FakeHandler()
        _send_json_with_error_status(h, {"error": "chapter must be ≥ 1; got 0"}, error_status=400)
        assert h.status == 400
        assert h.sent == {"error": "chapter must be ≥ 1; got 0"}

    def test_success_dict_passes_through_at_200(self):
        from scripts.web import _send_json_with_error_status

        h = FakeHandler()
        _send_json_with_error_status(h, {"book": "gen", "notes": []})
        assert h.status == 200
        assert h.sent == {"book": "gen", "notes": []}

    def test_extra_keys_preserved_on_error(self):
        # api_notes' error shape carries {"error": ..., "book": ...}.
        from scripts.web import _send_json_with_error_status

        h = FakeHandler()
        _send_json_with_error_status(h, {"error": "book not found", "book": "zzz"})
        assert h.status == 404
        assert h.sent == {"error": "book not found", "book": "zzz"}


class TestScenarioErrorStatus:
    """api_get_scenario has THREE legacy error shapes with distinct HTTP
    semantics; the route classifies by message (shapes pinned upstream)."""

    def test_not_found_is_404(self):
        from scripts.web import _scenario_error_status

        assert _scenario_error_status("scenario 'nope' not found") == 404

    def test_corrupt_file_is_500(self):
        from scripts.web import _scenario_error_status

        assert _scenario_error_status("corrupt scenario file: bad yaml") == 500

    def test_invalid_name_is_400(self):
        from scripts.web import _scenario_error_status

        assert _scenario_error_status("invalid scenario name 'X' — use lowercase a-z, 0-9, -, _ (max 41 chars)") == 400


# ---------- unit: envelope-bypass surfaces (7 + 8) ---------------------


class TestSourcesCacheEnvelopeHonored:
    def test_do_GET_routes_cache_status_through_dispatch_helper(self):
        # Source pin (filesplit/routetable pattern): the call site must
        # translate the standard envelope, not send it raw.
        import inspect

        from scripts.web import Handler

        src = inspect.getsource(Handler.do_GET)
        assert "_dispatch_table_result(self, api_sources_cache_status())" in src, (
            "/api/sources/cache must route through _dispatch_table_result "
            "so its config_error http:500 envelope is honored"
        )
        assert "self._send_json(api_sources_cache_status())" not in src, (
            "/api/sources/cache still sends the raw envelope at 200"
        )

    def test_config_error_envelope_translates_to_500(self):
        # The handler's documented error shape (scripts/api/sources.py)
        # through the same dispatch the route now uses.
        from scripts.web import _dispatch_table_result

        h = FakeHandler()
        _dispatch_table_result(
            h,
            {"status": "error", "code": "config_error", "http": 500, "message": "bad fetchers", "sources": []},
        )
        assert h.status == 500
        assert h.sent["error"] == "config_error"
        assert h.sent["sources"] == []  # extras preserved (A.8 contract)


class TestApihelpEnvelopeHonored:
    def test_apihelp_moved_out_of_simple_table(self):
        from scripts import web

        simple_paths = {p for p, _ in web._SIMPLE_GET_ROUTES}
        assert "/api/apihelp" not in simple_paths, (
            "/api/apihelp must not be in the always-200 _SIMPLE_GET_ROUTES "
            "(its source_read_failed path returns an http:500 envelope)"
        )

    def test_apihelp_registered_in_regex_table(self):
        from scripts import web

        entry = next((h for rx, h in web._REGEX_GET_ROUTES if rx.pattern == r"^/api/apihelp$"), None)
        assert entry is not None, "/api/apihelp missing from _REGEX_GET_ROUTES"
        result = entry()
        assert result["status"] == "ok" and "api_routes" in result

    def test_apihelp_error_envelope_translates_to_500(self, monkeypatch):
        # The regex-table lambda resolves api_help_data from web's module
        # namespace at call time — monkeypatch it to the handler's
        # documented error envelope and run the REAL dispatch path.
        from scripts import web

        monkeypatch.setattr(
            web,
            "api_help_data",
            lambda: {"status": "error", "code": "source_read_failed", "http": 500, "message": "boom"},
        )
        entry = next(h for rx, h in web._REGEX_GET_ROUTES if rx.pattern == r"^/api/apihelp$")
        h = FakeHandler()
        web._dispatch_table_result(h, entry())
        assert h.status == 500
        assert h.sent == {"error": "source_read_failed", "message": "boom"}


class TestBuildMyBibleHttpStatus:
    """api_build_my_bible returns {"error": ..., "http": N} — must not ship at 200."""

    def test_dispatch_honors_error_http_envelope(self):
        from scripts.web import _dispatch_table_result

        h = FakeHandler()
        _dispatch_table_result(h, {"error": "unknown edition: xyz", "http": 404})
        assert h.status == 404
        assert h.sent == {"error": "unknown edition: xyz"}

    def test_unknown_edition_live_is_404(self):
        import threading
        import time
        from http.server import ThreadingHTTPServer

        from scripts.web import Handler

        srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        time.sleep(0.1)
        try:
            url = f"http://127.0.0.1:{port}/api/build-my-bible/nonexistent-edition-xyz"
            try:
                urllib.request.urlopen(url, timeout=10)
                raise AssertionError("expected HTTPError")
            except urllib.error.HTTPError as e:
                assert e.code == 404
                body = json.loads(e.read().decode("utf-8"))
                assert "error" in body
        finally:
            srv.shutdown()


# ---------- live HTTP: end-to-end route translation --------------------


class TestLiveErrorStatus:
    """One live server for the whole class (test_scripts live-smoke
    pattern); every request is a fast-fail error path or a cheap read."""

    @classmethod
    def setup_class(cls):
        import threading
        import time
        from http.server import ThreadingHTTPServer

        from scripts.web import Handler

        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.srv.server_address[1]
        t = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        t.start()
        time.sleep(0.1)

    @classmethod
    def teardown_class(cls):
        cls.srv.shutdown()

    def _get(self, path: str):
        url = f"http://127.0.0.1:{self.port}{path}"
        try:
            r = urllib.request.urlopen(url, timeout=10)
            return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    # -- the 6 legacy {"error": ...} routes --

    def test_scenario_not_found_is_404(self):
        status, body = self._get("/api/scenarios/zz-no-such-scenario")
        assert status == 404
        assert "not found" in body["error"]

    def test_scenario_invalid_name_is_400(self):
        # 50 chars passes the route regex but fails the handler's
        # 41-char name validation → input-validation 400.
        status, body = self._get("/api/scenarios/" + "a" * 50)
        assert status == 400
        assert "invalid scenario name" in body["error"]

    def test_sources_unknown_book_is_404(self):
        status, body = self._get("/api/sources/zzz")
        assert status == 404
        assert "unknown book" in body["error"]

    def test_disabled_notes_unknown_edition_is_404(self):
        status, body = self._get("/api/edition/zz-no-such-edition/disabled-notes")
        assert status == 404
        assert "unknown edition" in body["error"]

    def test_notes_unknown_book_is_404(self):
        status, body = self._get("/api/notes/zzz")
        assert status == 404
        assert body["error"] == "book not found"
        assert body["book"] == "zzz"  # legacy shape preserved

    def test_export_preview_unknown_edition_is_404(self):
        status, body = self._get("/api/export/preview/zz-no-such-edition")
        assert status == 404
        assert "unknown edition" in body["error"]

    def test_compare_chapter_below_one_is_400(self):
        status, body = self._get("/api/compare?book=gen&chapter=0")
        assert status == 400
        assert "chapter must be" in body["error"]

    # -- success paths still 200 (pin at least 2 of the routes) --

    def test_notes_success_still_200(self):
        status, body = self._get("/api/notes/gen")
        assert status == 200
        assert body["book"] == "gen"
        assert isinstance(body["notes"], list) and body["notes"]

    def test_sources_cache_success_still_200(self):
        status, body = self._get("/api/sources/cache")
        assert status == 200
        assert body["status"] == "ok"
        assert isinstance(body["sources"], list)

    def test_apihelp_success_still_200(self):
        status, body = self._get("/api/apihelp")
        assert status == 200
        assert body["status"] == "ok"
        assert "api_routes" in body and "consoles" in body

    def test_scenario_success_still_200(self):
        # Pick a real saved scenario dynamically (the list endpoint is
        # already a 200-stable simple route).
        status, listing = self._get("/api/scenarios")
        assert status == 200
        scenarios = listing.get("scenarios") or []
        if not scenarios:  # corpus without scenarios — nothing to pin
            return
        name = scenarios[0]["name"]
        assert re.fullmatch(r"[a-z0-9_-]+", name)
        status, body = self._get(f"/api/scenarios/{name}")
        assert status == 200
        assert body["ok"] is True
        assert body["scenario"]["name"] == name

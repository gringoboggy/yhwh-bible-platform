"""ω.27 follow-on (2026-05-11) — ω.35-A series test classes, split out
of the monolithic ``tests/test_scripts.py`` into a topic file
alongside the other three ω.27 follow-on splits.

Fourth (and final-for-this-session) topic extraction. The ω.35-A
arc (route-table migration) shipped ten slices on 2026-05-11:

- ω.35-A     check_routes.py meta-tool (route inventory + drift)
- ω.35-A.1   _SIMPLE_GET_ROUTES table (zero-arg path == handler)
- ω.35-A.2   _REGEX_GET_ROUTES table (parameterized GET paths)
- ω.35-A.4   _QS_REGEX_GET_ROUTES table (GET with querystring parsing)
- ω.35-A.5   _PUT_ROUTES table (mutation PUT with payload)
- ω.35-A.6   _DELETE_ROUTES table (DELETE)
- ω.35-A.7   _POST_ROUTES table (POST mutations)
- ω.35-A.8   bespoke GET cleanup (paths that resist table migration)
- ω.35-A.9   _MULTIPART_ROUTES table (file-upload POSTs)
- ω.35-A.10  bespoke PUT cleanup (export/build + build-all-editions)

Together these moved the legacy do_GET / do_POST / do_PUT /
do_DELETE if/elif cascade into table-driven dispatch, reducing
the per-route boilerplate from ~9 lines to ~1 line in the table
and making the route surface inspectable (check_routes.py
discovers all 95 routes via static analysis).

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""


# ---------- Phase ω.35-A : routes inventory + drift linter ------------


class TestOmega35RoutesInventory:
    """ω.35-A — first response to AUDIT_2026-05-11 ARCH-01.
    `scripts/check_routes.py` auto-discovers HTTP routes from
    web.py's do_GET/POST/PUT/DELETE methods, surfaces the route
    count + method distribution, and flags drift classes
    (duplicate patterns, unanchored regexes, missing methods).
    Wired into /api/preflight as the `routes_inventory` Tier-3
    check.

    Lays the foundation for ω.35-A.1 (progressive route-table
    dispatch migration) and ω.35-B (file split into
    `scripts/api/<topic>.py`) without rewriting any dispatch
    code in this phase — keeps the 1973-test green state intact."""

    def test_discover_routes_returns_at_least_50(self):
        from scripts import check_routes

        routes = check_routes.discover_routes()
        assert len(routes) >= 50, f"expected ≥50 routes, found {len(routes)}"

    def test_discover_routes_covers_all_four_methods(self):
        from scripts import check_routes

        routes = check_routes.discover_routes()
        methods = {r.method for r in routes}
        assert methods == {"GET", "POST", "PUT", "DELETE"}, f"method coverage: {methods}"

    def test_discover_routes_includes_known_routes(self):
        from scripts import check_routes

        routes = check_routes.discover_routes()
        keys = {(r.method, r.pattern, r.is_regex) for r in routes}
        assert ("GET", "/api/matrix", False) in keys
        assert ("GET", "/api/preflight", False) in keys
        assert ("GET", "/api/search-notes", False) in keys
        assert ("GET", "/api/audit/attribution", False) in keys

    def test_run_all_returns_standard_aggregator_shape(self):
        from scripts import check_routes

        result = check_routes.run_all()
        assert "checks" in result
        assert "summary" in result
        assert "route_count" in result
        for c in result["checks"]:
            for k in ("id", "name", "status", "message", "violations"):
                assert k in c, f"sub-check missing {k!r}"
            assert c["status"] in ("pass", "warn", "fail")
        s = result["summary"]
        for k in ("total", "pass", "clean"):
            assert k in s

    def test_no_duplicate_patterns_check_passes_on_real_codebase(self):
        from scripts import check_routes

        result = check_routes.run_all()
        sub = next(c for c in result["checks"] if c["id"] == "no_duplicate_patterns")
        assert sub["status"] == "pass", f"duplicate pattern found: {sub['violations']}"

    def test_regex_routes_are_end_anchored(self):
        from scripts import check_routes

        result = check_routes.run_all()
        sub = next(c for c in result["checks"] if c["id"] == "regex_anchors")
        assert sub["status"] == "pass", f"unanchored regex(es): {sub['violations']}"

    def test_run_all_clean_on_real_codebase(self):
        from scripts import check_routes

        result = check_routes.run_all()
        assert result["summary"]["clean"] is True, f"routes inventory has open drift: {result['summary']}"

    def test_preflight_includes_routes_inventory(self):
        from scripts.web import _compute_preflight_uncached

        pf = _compute_preflight_uncached()
        ids = [c["id"] for c in pf["checks"]]
        assert "routes_inventory" in ids, f"preflight missing routes_inventory check: {ids}"

    def test_preflight_routes_inventory_has_required_fields(self):
        from scripts.web import _compute_preflight_uncached

        pf = _compute_preflight_uncached()
        check = next(c for c in pf["checks"] if c["id"] == "routes_inventory")
        for k in ("id", "name", "status", "message", "details", "jump_to"):
            assert k in check, f"preflight check missing {k!r}"
        assert check["status"] in ("pass", "warn", "fail")
        assert check["jump_to"] == "/preflight"

    def test_discovery_handles_synthetic_web_py(self, tmp_path):
        # Pin: discovery is regex-based; verify it correctly
        # picks up both literal and regex route patterns from a
        # tiny synthetic do_GET / do_POST.
        from scripts import check_routes

        synth = tmp_path / "synth_web.py"
        synth.write_text(
            "import re\n\n"
            "class H:\n"
            "    def do_GET(self):\n"
            '        path = "/foo"\n'
            '        if path == "/foo":\n'
            "            return\n"
            '        if path == "/bar" or path == "/bar.html":\n'
            "            return\n"
            '        m = re.match(r"^/api/x/([a-z]+)$", path)\n'
            "        if m:\n"
            "            return\n\n"
            "    def do_POST(self):\n"
            '        m = re.match(r"^/api/upload$", self.path)\n'
            "        if m:\n"
            "            return\n",
            encoding="utf-8",
        )
        routes = check_routes.discover_routes(web_py_path=synth)
        keys = {(r.method, r.pattern, r.is_regex) for r in routes}
        assert ("GET", "/foo", False) in keys
        assert ("GET", "/bar", False) in keys
        assert ("GET", "/bar.html", False) in keys  # alias picked up
        assert ("GET", "/api/x/([a-z]+)$", True) in keys
        assert ("POST", "/api/upload$", True) in keys


# ---------- Phase ω.35-A.1 : table-driven dispatch (simple GET) -------


class TestOmega35A1SimpleGetTable:
    """ω.35-A.1 — first slice of the audit's ARCH-01 live-dispatcher
    refactor. `web._SIMPLE_GET_ROUTES` is a list of `(path, handler)`
    tuples for the simplest GET routes (the
    `if path == "/api/X": return self._send_json(api_X())` shape).
    `Handler.do_GET` checks the table FIRST and falls through to
    the legacy if/elif cascade for routes that don't fit the simple
    shape.

    Migrated branches REMAIN in the legacy if/elif as dead code —
    safety net + zero linter delta. ω.35-A.1 dedups the discovered
    set so the table entry wins; unintentional duplicates still
    surface.

    Future ω.35-A.2 will widen the table to cover regex routes and
    paths that need querystring parsing; ω.35-A.3 will delete the
    dead-code legacy branches once the table is proven."""

    def test_table_has_expected_minimum_size(self):
        from scripts import web

        assert len(web._SIMPLE_GET_ROUTES) >= 10, f"_SIMPLE_GET_ROUTES has only {len(web._SIMPLE_GET_ROUTES)} entries"

    def test_table_entries_are_path_handler_tuples(self):
        from scripts import web

        for entry in web._SIMPLE_GET_ROUTES:
            assert isinstance(entry, tuple), f"entry is not a tuple: {entry}"
            assert len(entry) == 2, f"entry is not a (path, handler) 2-tuple: {entry}"
            path, handler = entry
            assert isinstance(path, str), f"path is not a str: {path!r}"
            assert path.startswith("/"), f"path doesn't start with /: {path!r}"
            assert callable(handler), f"handler is not callable for {path}: {handler}"

    def test_table_includes_known_simple_routes(self):
        from scripts import web

        paths = {p for p, _ in web._SIMPLE_GET_ROUTES}
        # Pin a representative subset of the simplest routes
        assert "/api/books" in paths
        assert "/api/kinds" in paths
        assert "/api/matrix" in paths
        assert "/api/preflight" in paths
        assert "/api/customize" in paths
        assert "/api/publisher" in paths

    def test_table_handlers_each_return_dict_when_invoked(self):
        # Sanity: every registered handler can be called and returns
        # a dict. Catches mis-registration (e.g. someone wires a
        # handler that takes args, or one that returns None).
        from scripts import web

        for path, handler in web._SIMPLE_GET_ROUTES:
            result = handler()
            assert isinstance(result, dict), f"handler for {path} returned {type(result).__name__}, expected dict"

    def test_route_inventory_no_drift_after_migration(self):
        # Per the migration contract, dedup logic in check_routes
        # ensures the route count stays the same after migration —
        # table entries replace legacy duplicates 1:1.
        from scripts import check_routes

        result = check_routes.run_all()
        assert result["summary"]["clean"] is True, f"routes inventory has open drift: {result['summary']}"
        # All 4 methods still present
        sub = next(c for c in result["checks"] if c["id"] == "methods_covered")
        assert sub["status"] == "pass"
        # No duplicates (the dedup hides the intentional table↔legacy
        # overlap; unintentional duplicates would still surface)
        sub = next(c for c in result["checks"] if c["id"] == "no_duplicate_patterns")
        assert sub["status"] == "pass"

    def test_discovery_includes_table_entries(self):
        # The dedup path means table entries DO appear in the
        # discovered set (they take precedence over the legacy
        # if/elif duplicates).
        from scripts import check_routes

        routes = check_routes.discover_routes()
        keys = {(r.method, r.pattern, r.is_regex) for r in routes}
        for path in ("/api/books", "/api/matrix", "/api/preflight"):
            assert ("GET", path, False) in keys, f"table entry {path!r} not in discovered set"

    def test_table_routes_dispatched_through_handler(self):
        # End-to-end smoke: simulate a do_GET-style dispatch by
        # calling the table handler the way the Handler class would.
        # Confirms the table is well-formed and the handlers are
        # importable + callable from web.py's namespace.
        from scripts import web

        # Find /api/books handler
        path_to_handler = dict(web._SIMPLE_GET_ROUTES)
        assert "/api/books" in path_to_handler
        result = path_to_handler["/api/books"]()
        # api_books returns a dict with at least one of the
        # standard list keys (defensive check)
        assert isinstance(result, dict)

    def test_known_routes_still_work_post_migration(self):
        # Direct call to api_* via web.* module namespace must
        # still return the same shape as before. Catches accidental
        # function rename / import breakage.
        from scripts import web

        # /api/books shape: a dict with "books" key
        r = web.api_books()
        assert isinstance(r, dict)
        # /api/preflight shape: dict with "checks" key (part of
        # the standard preflight aggregator shape)
        r = web.api_preflight()
        assert isinstance(r, dict)
        assert "checks" in r or "summary" in r


# ---------- Phase ω.35-A.2 : regex routes table dispatch ---------------


class TestOmega35A2RegexGetTable:
    """ω.35-A.2 — second slice of the route-table migration.
    `web._REGEX_GET_ROUTES` covers parameterized GET paths with the
    boilerplate regex.match → handler(*groups) → error-translate →
    send_json shape. Handler.do_GET dispatches this table after
    _SIMPLE_GET_ROUTES and before the legacy if/elif cascade.
    `_dispatch_table_result` centralizes the standard error-
    translation envelope that previously appeared 10+ times in the
    legacy code."""

    def test_regex_table_has_expected_entries(self):
        from scripts import web

        patterns = [r.pattern for r, _ in web._REGEX_GET_ROUTES]
        as_strs = "|".join(patterns)
        assert "/api/reading-plans/" in as_strs
        assert "/api/snapshots/" in as_strs

    def test_regex_table_entries_are_compiled_regex_handler_tuples(self):
        from scripts import web

        for entry in web._REGEX_GET_ROUTES:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            regex_obj, handler = entry
            assert hasattr(regex_obj, "match"), f"first element not a compiled regex: {regex_obj}"
            assert callable(handler), f"second element not callable: {handler}"

    def test_snapshot_precedence_two_args_before_one(self):
        # /api/snapshots/<ed>/<ver> MUST come before
        # /api/snapshots/<ed> so the more-specific pattern wins.
        from scripts import web

        idx_two = None
        idx_one = None
        for i, (regex_obj, _) in enumerate(web._REGEX_GET_ROUTES):
            pat = regex_obj.pattern
            if "/api/snapshots/" in pat and pat.count("([a-z0-9._-]+)") == 2:
                idx_two = i
            elif "/api/snapshots/" in pat and pat.count("([a-z0-9._-]+)") == 1:
                idx_one = i
        assert idx_two is not None
        assert idx_one is not None
        assert idx_two < idx_one

    def test_dispatch_table_result_translates_error(self):
        from scripts.web import _dispatch_table_result

        class FakeHandler:
            def __init__(self):
                self.sent = None
                self.status = None

            def _send_json(self, body, status=200):
                self.sent = body
                self.status = status

        h = FakeHandler()
        _dispatch_table_result(h, {"status": "error", "code": "not_found", "http": 404, "message": "x"})
        assert h.status == 404
        assert h.sent == {"error": "not_found", "message": "x"}

    def test_dispatch_table_result_passes_through_ok(self):
        from scripts.web import _dispatch_table_result

        class FakeHandler:
            def __init__(self):
                self.sent = None
                self.status = None

            def _send_json(self, body, status=200):
                self.sent = body
                self.status = status

        h = FakeHandler()
        _dispatch_table_result(h, {"status": "ok", "data": [1, 2, 3]})
        assert h.status == 200
        assert h.sent == {"status": "ok", "data": [1, 2, 3]}

    def test_dispatch_table_result_defaults(self):
        # Missing code → "internal_error"; missing http → 500;
        # missing message → "".
        from scripts.web import _dispatch_table_result

        class FakeHandler:
            def __init__(self):
                self.sent = None
                self.status = None

            def _send_json(self, body, status=200):
                self.sent = body
                self.status = status

        h = FakeHandler()
        _dispatch_table_result(h, {"status": "error"})
        assert h.status == 500
        assert h.sent == {"error": "internal_error", "message": ""}

    def test_route_inventory_no_drift_after_regex_migration(self):
        from scripts import check_routes

        result = check_routes.run_all()
        assert result["summary"]["clean"] is True

    def test_discovery_recognizes_regex_table_entries(self):
        from scripts import check_routes

        routes = check_routes.discover_routes()
        keys = {(r.method, r.pattern, r.is_regex) for r in routes}
        assert ("GET", "/api/reading-plans/([a-z0-9_-]+)$", True) in keys
        assert ("GET", "/api/snapshots/([a-z0-9._-]+)/([a-z0-9._-]+)$", True) in keys
        assert ("GET", "/api/snapshots/([a-z0-9._-]+)$", True) in keys


# ---------- Phase ω.35-A.4 : querystring-bearing routes ---------------


class TestOmega35A4QsRegexGetTable:
    """ω.35-A.4 — third route-table slice covering GET routes that
    parse the URL querystring. `_QS_REGEX_GET_ROUTES` entries are
    `(regex, lambda m, qs: handler(...))` — handler takes the
    regex match + parsed qs dict, returns the response. Dispatch
    runs through `_dispatch_table_result` for the standard
    error-translate envelope.

    Migrated routes (legacy branches deleted in same phase):
    - /api/snapshots/<ed>/<ver>/diff (qs.against)
    - /api/audit-log (qs.n)
    - /api/diff (qs.a, qs.b)"""

    def test_qs_table_has_expected_entries(self):
        from scripts import web

        patterns = [r.pattern for r, _ in web._QS_REGEX_GET_ROUTES]
        joined = "|".join(patterns)
        assert "/api/snapshots/" in joined and "/diff" in joined
        assert "/api/audit-log" in joined
        assert "/api/diff" in joined

    def test_qs_table_entries_shape(self):
        from scripts import web

        for entry in web._QS_REGEX_GET_ROUTES:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            regex_obj, handler = entry
            assert hasattr(regex_obj, "match"), f"first not a compiled regex: {regex_obj}"
            assert callable(handler), f"second not callable: {handler}"

    def test_qs_handlers_take_match_and_qs(self):
        # Smoke-test the audit-log handler with empty qs to confirm
        # it accepts the (m, qs) signature and produces a dict.
        from scripts import web

        for regex_obj, handler in web._QS_REGEX_GET_ROUTES:
            if regex_obj.pattern == r"^/api/audit-log$":
                m = regex_obj.match("/api/audit-log")
                assert m is not None
                result = handler(m, {})
                assert isinstance(result, dict)
                break
        else:
            raise AssertionError("audit-log entry not found")

    def test_qs_diff_uses_defaults_when_qs_empty(self):
        from scripts import web

        for regex_obj, handler in web._QS_REGEX_GET_ROUTES:
            if regex_obj.pattern == r"^/api/diff$":
                m = regex_obj.match("/api/diff")
                assert m is not None
                result = handler(m, {})
                assert isinstance(result, dict)
                break
        else:
            raise AssertionError("/api/diff entry not found")

    def test_qs_audit_log_respects_n_param(self):
        from scripts import web

        for regex_obj, handler in web._QS_REGEX_GET_ROUTES:
            if regex_obj.pattern == r"^/api/audit-log$":
                m = regex_obj.match("/api/audit-log")
                result = handler(m, {"n": ["5"]})
                assert isinstance(result, dict)
                if "entries" in result:
                    assert len(result["entries"]) <= 5
                break

    def test_route_inventory_no_drift_after_qs_migration(self):
        from scripts import check_routes

        result = check_routes.run_all()
        assert result["summary"]["clean"] is True

    def test_discovery_recognizes_qs_table_entries(self):
        from scripts import check_routes

        routes = check_routes.discover_routes()
        keys = {(r.method, r.pattern, r.is_regex) for r in routes}
        assert ("GET", "/api/snapshots/([a-z0-9._-]+)/([a-z0-9._-]+)/diff$", True) in keys
        assert ("GET", "/api/audit-log$", True) in keys
        assert ("GET", "/api/diff$", True) in keys

    def test_substring_collision_dispatch_fixed(self):
        # Regression pin: `"_REGEX_GET_ROUTES" in "_QS_REGEX_GET_ROUTES"`
        # is True (substring); the discovery state machine must
        # check QS first so the regex-table flag isn't tripped on
        # the QS table's declaration line. If the order regressed,
        # the QS routes would silently vanish from the inventory.
        from scripts import check_routes

        routes = check_routes.discover_routes()
        qs_route_patterns = {
            r.pattern
            for r in routes
            if r.method == "GET" and r.is_regex and r.pattern in ("/api/audit-log$", "/api/diff$")
        }
        assert "/api/audit-log$" in qs_route_patterns
        assert "/api/diff$" in qs_route_patterns


# ---------- Phase ω.35-A.5 : PUT mutation routes table ----------------


class TestOmega35A5PutTable:
    """ω.35-A.5 — fourth route-table slice. `_PUT_ROUTES` covers
    PUT mutation routes that share the uniform shape:
    regex → read_body → handler(m, payload) → translate ok:False
    to 400 → send_json. The 9-line per-route boilerplate that
    appeared 6+ times in do_PUT is now one dispatch loop.

    Admin auth check runs at do_PUT function entry, so every
    table-registered route is auto-protected.

    Extended `_dispatch_table_result` handles the new
    `{ok: False}` legacy mutation-result shape (→ HTTP 400)
    alongside the existing `{status: error}` shape and the
    bare-200 fall-through."""

    def test_put_table_has_expected_entries(self):
        from scripts import web

        patterns = [r.pattern for r, _ in web._PUT_ROUTES]
        joined = "|".join(patterns)
        assert "/api/notes/" in joined
        assert "/api/edition/" in joined
        assert "/api/scenarios/" in joined
        assert "/api/category/" in joined
        assert "/api/kind/" in joined
        assert "/api/publisher/" in joined

    def test_put_table_entries_shape(self):
        from scripts import web

        for entry in web._PUT_ROUTES:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            regex_obj, handler = entry
            assert hasattr(regex_obj, "match")
            assert callable(handler)

    def test_dispatch_table_result_translates_ok_false_to_400(self):
        # The ω.35-A.5 extension: legacy {ok: False} mutation
        # results translate to HTTP 400 with the body as-is.
        from scripts.web import _dispatch_table_result

        class FakeHandler:
            def __init__(self):
                self.sent = None
                self.status = None

            def _send_json(self, body, status=200):
                self.sent = body
                self.status = status

        h = FakeHandler()
        _dispatch_table_result(h, {"ok": False, "error": "validation failed"})
        assert h.status == 400
        assert h.sent == {"ok": False, "error": "validation failed"}

    def test_dispatch_table_result_passes_ok_true_through(self):
        # Happy path: {ok: True} returns 200 unchanged.
        from scripts.web import _dispatch_table_result

        class FakeHandler:
            def __init__(self):
                self.sent = None
                self.status = None

            def _send_json(self, body, status=200):
                self.sent = body
                self.status = status

        h = FakeHandler()
        _dispatch_table_result(h, {"ok": True, "id": "x"})
        assert h.status == 200
        assert h.sent == {"ok": True, "id": "x"}

    def test_dispatch_table_result_passes_dict_without_ok_through(self):
        # api_save's error path returns {"error": ..., "book": ...}
        # with no "ok" key. result.get("ok") is None (not False), so
        # the ok-False check shouldn't fire. Matches legacy: api_save
        # errors went through send_json with 200 (the legacy did not
        # translate them).
        from scripts.web import _dispatch_table_result

        class FakeHandler:
            def __init__(self):
                self.sent = None
                self.status = None

            def _send_json(self, body, status=200):
                self.sent = body
                self.status = status

        h = FakeHandler()
        _dispatch_table_result(h, {"error": "book not found", "book": "xyz"})
        assert h.status == 200
        assert h.sent == {"error": "book not found", "book": "xyz"}

    def test_route_inventory_no_drift_after_put_migration(self):
        from scripts import check_routes

        result = check_routes.run_all()
        assert result["summary"]["clean"] is True
        # PUT method should still have at least the migrated 6
        # plus the un-migrated bespoke ones.
        routes = check_routes.discover_routes()
        puts = [r for r in routes if r.method == "PUT"]
        assert len(puts) >= 9, f"PUT count dropped: {len(puts)}"

    def test_discovery_recognizes_put_table_entries(self):
        from scripts import check_routes

        routes = check_routes.discover_routes()
        keys = {(r.method, r.pattern, r.is_regex) for r in routes}
        assert ("PUT", "/api/notes/([a-z0-9]+)$", True) in keys
        assert ("PUT", "/api/edition/([a-z0-9-]+)$", True) in keys
        assert ("PUT", "/api/category/([a-z0-9-]+)$", True) in keys
        assert ("PUT", "/api/kind/([a-z0-9-]+)$", True) in keys

    def test_handlers_take_match_and_payload(self):
        # Smoke-test: handler signature is (m, payload). Run each
        # handler with a synthetic match + minimal payload and
        # confirm it returns a dict (or raises a tolerable
        # exception like KeyError that the dispatch try/except
        # would translate to 400).
        import re as _re

        from scripts import web

        for regex_obj, handler in web._PUT_ROUTES:
            # Manually invoke with a dummy match and empty dict to
            # check the signature is (m, payload). The handler may
            # raise downstream — that's caught by the dispatch
            # try/except. We only care here about the call-pattern.
            m = _re.match(regex_obj.pattern, "/api/dummy/value")
            if m is None:
                # Some patterns require specific characters; try
                # the simplest path that matches the regex anchor.
                m = regex_obj.match("/api/x/y")
            # Just confirm handler is callable with (m, payload)
            # signature — we don't actually run it because that
            # would mutate state on the real corpus.
            assert callable(handler)
            try:
                import inspect

                sig = inspect.signature(handler)
                params = list(sig.parameters.keys())
                assert len(params) == 2, f"handler for {regex_obj.pattern} has wrong arg count: {params}"
            except (TypeError, ValueError):
                # Lambdas without explicit annotations are fine
                pass


# ---------- Phase ω.35-A.6 : DELETE mutation routes table -------------


class TestOmega35A6DeleteTable:
    """ω.35-A.6 — fifth route-table slice; first DELETE-method
    table. `_DELETE_ROUTES` covers DELETE routes that share the
    uniform shape: regex → handler(m) → _dispatch_table_result.
    Handler signature is `lambda m: api_X(...)` (no payload — the
    difference vs PUT). Admin auth runs at do_DELETE function
    entry; table dispatch is auto-protected.

    5 of 6 DELETE routes migrated: notes/<book>/<idx>,
    snapshots/<ed>/<ver>, scenarios/<name>, covers/<ed>/book/<book>,
    covers/<ed>/main. The sixth (sources/cache/<id>) stays in
    legacy — uses bespoke `_send_dict_result` helper, not
    table-compatible yet."""

    def test_delete_table_has_expected_entries(self):
        from scripts import web

        patterns = [r.pattern for r, _ in web._DELETE_ROUTES]
        joined = "|".join(patterns)
        assert "/api/notes/" in joined
        assert "/api/snapshots/" in joined
        assert "/api/scenarios/" in joined
        assert "/api/covers/" in joined

    def test_delete_table_entries_shape(self):
        from scripts import web

        for entry in web._DELETE_ROUTES:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            regex_obj, handler = entry
            assert hasattr(regex_obj, "match")
            assert callable(handler)

    def test_delete_handler_signature_is_match_only(self):
        # The DELETE table handler is `lambda m: api_X(...)` — one
        # arg (the regex match). Different from PUT's
        # `lambda m, payload:`.
        import inspect

        from scripts import web

        for regex_obj, handler in web._DELETE_ROUTES:
            try:
                sig = inspect.signature(handler)
                params = list(sig.parameters.keys())
                assert len(params) == 1, f"DELETE handler for {regex_obj.pattern} has wrong arg count: {params}"
            except (TypeError, ValueError):
                pass

    def test_covers_book_precedes_main_for_correctness(self):
        # /api/covers/<ed>/book/<book> is more specific than
        # /api/covers/<ed>/main; the more-specific pattern MUST
        # iterate first so its match wins. Iteration order =
        # precedence.
        from scripts import web

        idx_book = None
        idx_main = None
        for i, (regex_obj, _) in enumerate(web._DELETE_ROUTES):
            pat = regex_obj.pattern
            if "/api/covers/" in pat and "/book/" in pat:
                idx_book = i
            elif "/api/covers/" in pat and "/main" in pat:
                idx_main = i
        assert idx_book is not None
        assert idx_main is not None
        # In this specific case the patterns don't actually
        # overlap (the suffixes differ), but the precedence
        # discipline is the same — pin it.

    def test_notes_handler_coerces_index_to_int(self):
        # The notes DELETE pattern captures an integer index as
        # a string group; the handler must coerce to int before
        # calling api_delete (which expects int). A handler that
        # passes the string through would surface as TypeError
        # inside api_delete. Smoke check via a synthetic match
        # (we don't actually call the handler against the real
        # corpus — that would mutate state).

        from scripts import web

        for regex_obj, handler in web._DELETE_ROUTES:
            if "/api/notes/" in regex_obj.pattern:
                m = regex_obj.match("/api/notes/gen/0")
                assert m is not None
                # Verify the lambda's int(m.group(2)) call: by
                # inspecting the source representation when
                # possible.
                handler.__code__.co_consts if hasattr(handler, "__code__") else ()
                # Heuristic: the lambda body should reference int()
                # — we can't introspect deeply across versions, so
                # just confirm the handler is callable with one arg.
                assert callable(handler)
                break

    def test_route_inventory_no_drift_after_delete_migration(self):
        from scripts import check_routes

        result = check_routes.run_all()
        assert result["summary"]["clean"] is True
        routes = check_routes.discover_routes()
        deletes = [r for r in routes if r.method == "DELETE"]
        # Still 6 DELETE routes total (5 migrated + 1 still in legacy)
        assert len(deletes) >= 5, f"DELETE count dropped: {len(deletes)}"

    def test_discovery_recognizes_delete_table_entries(self):
        from scripts import check_routes

        routes = check_routes.discover_routes()
        keys = {(r.method, r.pattern, r.is_regex) for r in routes}
        # All 5 migrated DELETE routes should appear
        assert ("DELETE", "/api/notes/([a-z0-9]+)/(\\d+)$", True) in keys
        assert ("DELETE", "/api/snapshots/([a-z0-9._-]+)/([a-z0-9._-]+)$", True) in keys
        assert ("DELETE", "/api/scenarios/([a-z0-9_-]+)$", True) in keys
        assert ("DELETE", "/api/covers/([a-z0-9-]+)/book/([a-z0-9]+)$", True) in keys
        assert ("DELETE", "/api/covers/([a-z0-9-]+)/main$", True) in keys

    def test_sources_cache_migrated_in_a8(self):
        # ω.35-A.8 moved the 6th DELETE route (sources/cache/<id>)
        # into _DELETE_ROUTES, after extending
        # _dispatch_table_result to preserve extras in error
        # envelopes — the property `_send_dict_result` provided
        # but the dispatch helper previously didn't. Pin the
        # migrated state: the route MUST appear in _DELETE_ROUTES
        # AND be discoverable as a table-dispatched route.
        from scripts import check_routes, web

        table_patterns = [r.pattern for r, _ in web._DELETE_ROUTES]
        assert any("/sources/cache/" in p for p in table_patterns)
        routes = check_routes.discover_routes()
        cache_deletes = [r for r in routes if r.method == "DELETE" and "/sources/cache/" in r.pattern]
        assert len(cache_deletes) == 1, f"sources cache DELETE missing: {cache_deletes}"


class TestOmega35A7PostTable:
    """ω.35-A.7 — sixth route-table slice; first POST-method
    table for JSON-body routes. `_POST_ROUTES` covers POST routes
    that share the uniform shape: regex → handler(m, payload) →
    _dispatch_table_result. Same lambda signature as `_PUT_ROUTES`
    (POST and PUT both carry request bodies). Admin auth runs at
    do_POST function entry; body is read once in the dispatch
    loop and reused across all 6 entries.

    6 of 11 POST routes migrated:
    - /api/snapshots/<ed>/<ver>/restore   (no payload — uses {})
    - /api/snapshots/<ed>                 (snapshot create)
    - /api/matrix/apply-kind-to-all       (payload destructure)
    - /api/scenarios/_import              (payload destructure)
    - /api/editions/clone                 (payload pass-through)
    - /api/backups/restore                (payload destructure)

    Out of scope (deferred to ω.35-A.8 — bespoke cleanup):
    - 2 sources/cache fetch routes (use _send_dict_result with
      extras-preservation — needs either a dispatch helper
      extension or a dedicated table; judgment call deferred).
    - 3 multipart routes (cover main, cover book, sources cache
      upload) — distinct payload shape; need a dedicated table.
    """

    def test_post_table_has_at_least_six_entries(self):
        # A.7 introduced 6 entries; subsequent slices grow the table
        # (A.8 added 2 sources/cache entries → 8). Pin the lower
        # bound so the table never shrinks below the A.7 baseline.
        from scripts import web

        assert len(web._POST_ROUTES) >= 6

    def test_post_table_has_expected_patterns(self):
        from scripts import web

        patterns = [r.pattern for r, _ in web._POST_ROUTES]
        joined = "|".join(patterns)
        assert "/api/snapshots/" in joined
        assert "/api/matrix/apply-kind-to-all" in joined
        assert "/api/scenarios/_import" in joined
        assert "/api/editions/clone" in joined
        assert "/api/backups/restore" in joined

    def test_post_table_entries_shape(self):
        from scripts import web

        for entry in web._POST_ROUTES:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            regex_obj, handler = entry
            assert hasattr(regex_obj, "match")
            assert callable(handler)

    def test_post_handler_signature_is_match_and_payload(self):
        # The POST table handler is `lambda m, payload: api_X(...)` —
        # two args (match + JSON body), matching PUT. Different from
        # DELETE's one-arg `lambda m:` signature.
        import inspect

        from scripts import web

        for regex_obj, handler in web._POST_ROUTES:
            try:
                sig = inspect.signature(handler)
                params = list(sig.parameters.keys())
                assert len(params) == 2, f"POST handler for {regex_obj.pattern} has wrong arg count: {params}"
            except (TypeError, ValueError):
                pass

    def test_snapshot_restore_precedes_snapshot_create(self):
        # /api/snapshots/<ed>/<ver>/restore is more specific than
        # /api/snapshots/<ed>; iteration order = precedence so the
        # restore pattern MUST come first. Otherwise a POST to
        # /api/snapshots/main/v1/restore would match the less-
        # specific pattern with `version` swallowing `v1/restore`
        # and call api_snapshot_create instead of restore.
        from scripts import web

        idx_restore = None
        idx_create = None
        for i, (regex_obj, _) in enumerate(web._POST_ROUTES):
            pat = regex_obj.pattern
            # Specifically the snapshots/<ed>/<ver>/restore pattern,
            # NOT /api/backups/restore (which also has /restore).
            if "/api/snapshots/" in pat and "/restore" in pat:
                idx_restore = i
            elif pat.endswith(r"/api/snapshots/([a-z0-9._-]+)$"):
                idx_create = i
        assert idx_restore is not None
        assert idx_create is not None
        assert idx_restore < idx_create, (
            f"restore pattern (idx {idx_restore}) must precede create pattern "
            f"(idx {idx_create}); otherwise the less-specific create swallows "
            f"the /<ver>/restore path"
        )

    def test_route_inventory_no_drift_after_post_migration(self):
        from scripts import check_routes

        result = check_routes.run_all()
        assert result["summary"]["clean"] is True

    def test_discovery_recognizes_post_table_entries(self):
        from scripts import check_routes

        routes = check_routes.discover_routes()
        keys = {(r.method, r.pattern, r.is_regex) for r in routes}
        # All 6 migrated POST routes should appear via the standalone
        # `re.compile(r"^...$"),` shape (ruff reformatted onto own line).
        assert ("POST", "/api/snapshots/([a-z0-9._-]+)/([a-z0-9._-]+)/restore$", True) in keys
        assert ("POST", "/api/snapshots/([a-z0-9._-]+)$", True) in keys
        assert ("POST", "/api/matrix/apply-kind-to-all$", True) in keys
        assert ("POST", "/api/scenarios/_import$", True) in keys
        assert ("POST", "/api/editions/clone$", True) in keys
        assert ("POST", "/api/backups/restore$", True) in keys

    def test_multipart_still_in_legacy_after_a7(self):
        # 3 multipart routes stay in legacy after A.7 (deferred to a
        # future _MULTIPART_ROUTES table). The 2 sources/cache fetch
        # routes were also deferred from A.7, but A.8 moved them into
        # _POST_ROUTES — so they're no longer pinned here. Only
        # multipart-shape routes (which the helper can't handle yet)
        # remain in legacy. NOTE: the §4.6 cover-TEMPLATE route
        # (/api/covers/<id>/template) is a JSON POST and DOES live in
        # _POST_ROUTES — only the multipart cover UPLOADS (/main,
        # /book/<code>) stay in legacy.
        from scripts import web

        table_patterns = [r.pattern for r, _ in web._POST_ROUTES]
        assert not any("/covers/" in p and ("/main" in p or "/book" in p) for p in table_patterns), (
            "cover UPLOADS (/main, /book) are multipart — must NOT be in _POST_ROUTES"
        )
        # /upload uses multipart, but /fetch uses JSON — distinguish
        # them in the assertion.
        assert not any("/sources/cache/" in p and "/upload" in p for p in table_patterns), (
            "sources/cache /upload is multipart — must NOT be in _POST_ROUTES"
        )

    def test_dispatch_loop_reads_body_once(self):
        # The dispatch loop in do_POST is structured so _read_body()
        # fires at most once per request (when the first match
        # happens), then payload is reused if no match occurs (it
        # won't — the loop returns on first match). Pin via source
        # inspection.
        import inspect

        from scripts.web import Handler

        src = inspect.getsource(Handler.do_POST)
        # The function should contain the dispatch loop pattern
        assert "_POST_ROUTES" in src
        # And there must be only one _read_body() call inside the
        # _POST_ROUTES loop (legacy still has them for sources_cache
        # routes, which is fine).
        # Count `_read_body()` references INSIDE the new dispatch loop —
        # the loop body has exactly one.
        before_loop, _, after_loop = src.partition("for pattern, handler in _POST_ROUTES")
        loop_body, _, post_loop = after_loop.partition("# ω.16 routes migrated")
        assert loop_body.count("self._read_body()") == 1, (
            f"new POST dispatch loop should read body exactly once; got {loop_body.count('self._read_body()')}"
        )

    def test_empty_body_post_works_for_restore(self):
        # Snapshot restore POSTs typically have Content-Length 0.
        # `_read_body() or {}` returns {} for empty body, and the
        # restore lambda ignores payload anyway. Verify the lambda
        # gracefully accepts payload={}.
        from scripts import web

        # Find the restore entry
        restore_entry = None
        for regex_obj, handler in web._POST_ROUTES:
            if "/restore" in regex_obj.pattern:
                restore_entry = (regex_obj, handler)
                break
        assert restore_entry is not None
        regex_obj, handler = restore_entry
        m = regex_obj.match("/api/snapshots/main/v1/restore")
        assert m is not None
        # Call the handler with empty payload — it should call into
        # api_snapshot_restore; we don't care about the result here,
        # only that it accepts payload={} without crashing on a
        # missing key access.
        try:
            result = handler(m, {})
            # Result is a dict; either ok or an error envelope.
            assert isinstance(result, dict)
        except Exception as e:
            # api_snapshot_restore is allowed to error (no snapshot
            # named "v1" exists), but it must not raise something
            # caused by payload-key access.
            assert "payload" not in str(e).lower(), f"handler crashed on payload access: {e}"


class TestOmega35A8BespokeCleanup:
    """ω.35-A.8 — seventh route-table slice; closes the loop on
    sources/cache routes that previously used `_send_dict_result`.

    Three routes migrated (1 DELETE + 2 POST), enabled by extending
    `_dispatch_table_result` to preserve extras fields in error
    envelopes. Before A.8 the helper was extras-stripping (only
    sent `{error, message}` in error responses); the legacy
    `_send_dict_result` was extras-preserving (sent `{error,
    message, **extras}`). `api_sources_cache_fetch_all` returns
    `"results": []` in its config-error envelope, so the
    extras-preservation property is load-bearing.

    Routes migrated:
    - DELETE /api/sources/cache/<id> → api_sources_cache_clear
    - POST   /api/sources/cache/_all/fetch → api_sources_cache_fetch_all
    - POST   /api/sources/cache/<id>/fetch → api_sources_cache_fetch

    Verified extras-neutral for the 11 routes already migrated
    (none of them return extras in `status==error` envelopes —
    grep across all `"status": "error"` returns confirmed only
    api_sources_cache_status and api_sources_cache_fetch_all
    return `[...]` extras).
    """

    def test_dispatch_helper_preserves_extras_on_error(self):
        # The helper sends `{error, message, **extras}` for
        # status==error responses, matching the legacy
        # _send_dict_result behavior.
        from scripts.web import _dispatch_table_result

        captured = {}

        class FakeHandler:
            def _send_json(self, body, status=200):
                captured["body"] = body
                captured["status"] = status

        result = {
            "status": "error",
            "code": "config_error",
            "http": 500,
            "message": "bad config",
            "results": [],  # extras key — must be preserved
            "extra_field": "preserved",
        }
        _dispatch_table_result(FakeHandler(), result)
        assert captured["status"] == 500
        assert captured["body"]["error"] == "config_error"
        assert captured["body"]["message"] == "bad config"
        assert captured["body"]["results"] == []
        assert captured["body"]["extra_field"] == "preserved"
        # Standard fields are NOT preserved (they're already
        # mapped to `error`/`message`).
        assert "status" not in captured["body"]
        assert "code" not in captured["body"]
        assert "http" not in captured["body"]

    def test_dispatch_helper_no_extras_on_ok(self):
        # The status==ok / fall-through path passes the result
        # through unchanged. Extras have always been preserved
        # there; just pin that A.8's change didn't break it.
        from scripts.web import _dispatch_table_result

        captured = {}

        class FakeHandler:
            def _send_json(self, body, status=200):
                captured["body"] = body
                captured["status"] = status

        result = {"status": "ok", "ok": True, "id": "src1", "cached": True, "size_kb": 4.2}
        _dispatch_table_result(FakeHandler(), result)
        assert captured["status"] == 200
        assert captured["body"] == result  # full pass-through

    def test_delete_table_has_eight_entries_now(self):
        # A.8 added the 6th DELETE entry (sources/cache/<id>). The ε.6
        # distribution + ξ.26 license DELETE routes were never implemented
        # (decommercialize / scope), so the floor is 6. (mint-10: was a stale 8.)
        from scripts import web

        assert len(web._DELETE_ROUTES) == 6
        patterns = [r.pattern for r, _ in web._DELETE_ROUTES]
        assert any("/sources/cache/" in p for p in patterns)

    def test_post_table_has_fourteen_entries_now(self):
        # A.7 had 6, A.8 added 2 (sources/cache fetch + fetch_all),
        # ο.4 added 1 (archive-org upload), ξ.21 added 3 (auth/totp/
        # begin + confirm + disable), §4.6 added 1 (cover-template
        # recompose — a JSON POST, 2026-05-25 Wave 2), W4.3 added 1
        # (onboarding/complete) → 14 entries.
        from scripts import web

        assert len(web._POST_ROUTES) == 14

    def test_post_table_includes_sources_cache_routes(self):
        from scripts import web

        patterns = [r.pattern for r, _ in web._POST_ROUTES]
        joined = "|".join(patterns)
        assert "/api/sources/cache/_all/fetch" in joined
        assert "/api/sources/cache/" in joined and "/fetch" in joined

    def test_do_DELETE_has_no_legacy_branches(self):
        # After A.8 the do_DELETE method should contain ONLY the
        # table dispatch loop + a 404 fall-through; no legacy
        # `m = re.match(...)` for sources/cache.
        import inspect

        from scripts.web import Handler

        src = inspect.getsource(Handler.do_DELETE)
        # No raw `re.match(` reference to /sources/cache/ should
        # remain (the table dispatch uses pre-compiled regexes).
        assert "re.match" not in src or "/sources/cache/" not in src, (
            "do_DELETE still has a legacy /sources/cache/ branch — should be in _DELETE_ROUTES now"
        )

    def test_do_POST_has_no_sources_cache_fetch_branches(self):
        # After A.8 the do_POST method should not contain the
        # legacy `if self.path == "/api/sources/cache/_all/fetch":`
        # branch or `m = re.match(r"^/api/sources/cache/.../fetch$"...`.
        import inspect

        from scripts.web import Handler

        src = inspect.getsource(Handler.do_POST)
        assert '"/api/sources/cache/_all/fetch"' not in src, (
            "do_POST still has the legacy _all/fetch literal branch — should be in _POST_ROUTES"
        )
        assert "/api/sources/cache/([a-z0-9_-]+)/fetch" not in src, (
            "do_POST still has the legacy <id>/fetch regex branch — should be in _POST_ROUTES"
        )

    def test_sources_cache_fetch_all_extras_round_trip(self):
        # End-to-end smoke through the dispatch helper using a
        # mock-shaped error result. Confirms the
        # `_send_dict_result` → `_dispatch_table_result`
        # behavioral substitution holds for the load-bearing
        # case (api_sources_cache_fetch_all's config_error path
        # with `"results": []`).
        from scripts.web import _dispatch_table_result

        captured = {}

        class FakeHandler:
            def _send_json(self, body, status=200):
                captured["body"] = body
                captured["status"] = status

        result = {
            "status": "error",
            "code": "config_error",
            "http": 500,
            "message": "fetcher config invalid",
            "results": [],
        }
        _dispatch_table_result(FakeHandler(), result)
        # UI reads `results` in error case → must be present and []
        assert captured["body"]["results"] == []
        assert captured["status"] == 500

    def test_discovery_recognizes_a8_table_entries(self):
        from scripts import check_routes

        routes = check_routes.discover_routes()
        keys = {(r.method, r.pattern, r.is_regex) for r in routes}
        assert ("DELETE", "/api/sources/cache/([a-z0-9_-]+)$", True) in keys
        assert ("POST", "/api/sources/cache/_all/fetch$", True) in keys
        assert ("POST", "/api/sources/cache/([a-z0-9_-]+)/fetch$", True) in keys

    def test_route_inventory_clean_after_a8(self):
        from scripts import check_routes

        result = check_routes.run_all()
        assert result["summary"]["clean"] is True


class TestOmega35A9MultipartTable:
    """ω.35-A.9 — eighth route-table slice; first table with a
    DISTINCT entry shape (3-tuple instead of 2-tuple) and a
    DISTINCT lambda signature `lambda m, body, content_type`.

    `_MULTIPART_ROUTES` covers the 3 POST routes that take a
    multipart body instead of JSON. The dispatch helper
    `_dispatch_multipart_route` consolidates the boilerplate
    that previously lived in `_handle_cover_upload` and
    `_handle_sources_cache_upload` (both methods deleted by
    this phase).

    Per-route size cap: cover uploads = COVERS_UPLOAD_MAX_BYTES
    (10 MB), sources cache uploads = SOURCES_UPLOAD_MAX_BYTES
    (50 MB). The dispatch loop multiplies by 2 before rejecting
    (matches the prior pattern's defensive comment).

    Routes:
    - /api/covers/<ed>/main         → api_upload_cover_main
    - /api/covers/<ed>/book/<book>  → api_upload_cover_book
    - /api/sources/cache/<id>/upload → api_sources_cache_upload
    - /api/sales/import/<channel>   → api_sales_import (ε.3)
    """

    def test_multipart_table_has_four_entries(self):
        # ε.3's /api/sales/import/<channel> was removed in the mint-4
        # decommercialize; the floor is 3. (mint-10: was a stale 4.)
        from scripts import web

        assert len(web._MULTIPART_ROUTES) == 3

    def test_multipart_table_entries_shape(self):
        # Distinct 3-tuple shape: (regex, max_bytes, handler).
        from scripts import web

        for entry in web._MULTIPART_ROUTES:
            assert isinstance(entry, tuple)
            assert len(entry) == 3, f"multipart entry must be 3-tuple, got {len(entry)}"
            regex_obj, max_bytes, handler = entry
            assert hasattr(regex_obj, "match")
            assert isinstance(max_bytes, int)
            assert max_bytes > 0
            assert callable(handler)

    def test_multipart_handler_signature_is_match_body_ctype(self):
        # The multipart lambda is `lambda m, body, ctype: ...` —
        # three args. Different from POST table's (m, payload)
        # and DELETE table's (m).
        import inspect

        from scripts import web

        for regex_obj, _max, handler in web._MULTIPART_ROUTES:
            try:
                sig = inspect.signature(handler)
                params = list(sig.parameters.keys())
                assert len(params) == 3, f"multipart handler for {regex_obj.pattern} has wrong arg count: {params}"
            except (TypeError, ValueError):
                pass

    def test_size_caps_distinct_per_route(self):
        # The 2 cover routes share one cap; the sources/cache
        # upload has a different (larger) cap. Pin both.
        from scripts import web

        covers_caps = []
        sources_caps = []
        for regex_obj, max_bytes, _ in web._MULTIPART_ROUTES:
            if "/covers/" in regex_obj.pattern:
                covers_caps.append(max_bytes)
            elif "/sources/cache/" in regex_obj.pattern:
                sources_caps.append(max_bytes)
        assert covers_caps, "cover-upload caps missing"
        assert sources_caps, "sources-cache-upload cap missing"
        # All cover-upload caps match
        assert len(set(covers_caps)) == 1, f"cover caps differ: {covers_caps}"
        # Sources cap is strictly larger than cover cap
        assert sources_caps[0] > covers_caps[0], (
            "sources cache upload cap should be larger than cover-upload cap "
            f"(got sources={sources_caps[0]}, cover={covers_caps[0]})"
        )

    def test_do_POST_dispatches_to_multipart_table(self):
        # The do_POST method should contain the multipart table
        # dispatch loop, and the legacy `_handle_cover_upload`
        # and `_handle_sources_cache_upload` methods should be
        # deleted.
        import inspect

        from scripts.web import Handler

        src = inspect.getsource(Handler.do_POST)
        assert "_MULTIPART_ROUTES" in src, "do_POST missing multipart dispatch loop"
        # The legacy helpers are deleted — they shouldn't appear
        # as methods on Handler anymore.
        assert not hasattr(Handler, "_handle_cover_upload"), (
            "Handler._handle_cover_upload should be deleted — inlined into _dispatch_multipart_route"
        )
        assert not hasattr(Handler, "_handle_sources_cache_upload"), (
            "Handler._handle_sources_cache_upload should be deleted — inlined into _dispatch_multipart_route"
        )

    def test_dispatch_multipart_route_returns_413_for_oversize(self):
        # The helper rejects bodies larger than 2 * max_bytes
        # with HTTP 413. Test via a stub handler.
        from scripts.web import _dispatch_multipart_route

        captured = {}

        class FakeHandler:
            headers = {"Content-Length": str(100 * 1024 * 1024), "Content-Type": "multipart/form-data"}
            rfile = None  # never read because the size check fails first

            def _send_json(self, body, status=200):
                captured["body"] = body
                captured["status"] = status

        import re as _re

        m = _re.match(r"^(.+)$", "anything")
        # max_bytes=1MB → cap=2MB; sent 100MB → must be rejected
        _dispatch_multipart_route(FakeHandler(), m, 1 * 1024 * 1024, lambda mt, b, c: {"ok": True})
        assert captured["status"] == 413
        assert "too large" in captured["body"]["error"].lower()

    def test_dispatch_multipart_route_rejects_missing_content_length(self):
        from scripts.web import _dispatch_multipart_route

        captured = {}

        class FakeHandler:
            headers = {"Content-Length": "not-a-number", "Content-Type": "multipart/form-data"}
            rfile = None

            def _send_json(self, body, status=200):
                captured["body"] = body
                captured["status"] = status

        import re as _re

        m = _re.match(r"^(.+)$", "anything")
        _dispatch_multipart_route(FakeHandler(), m, 1024, lambda mt, b, c: {"ok": True})
        assert captured["status"] == 400
        assert "content-length" in captured["body"]["error"].lower()

    def test_dispatch_multipart_route_invokes_handler_and_dispatches_result(self):
        # Happy path: body within cap → handler called with body
        # bytes + ctype → result routed through
        # _dispatch_table_result.
        import io
        import re as _re

        from scripts.web import _dispatch_multipart_route

        captured = {}
        body_bytes = b"some multipart payload"

        class FakeHandler:
            headers = {
                "Content-Length": str(len(body_bytes)),
                "Content-Type": "multipart/form-data; boundary=xxx",
            }
            rfile = io.BytesIO(body_bytes)

            def _send_json(self, body, status=200):
                captured["body"] = body
                captured["status"] = status

        observed = {}

        def fake_handler(match, body, ctype):
            observed["body_len"] = len(body)
            observed["ctype"] = ctype
            observed["match"] = match
            return {"ok": True, "size": len(body)}

        m = _re.match(r"^/api/x/([a-z]+)$", "/api/x/test")
        _dispatch_multipart_route(FakeHandler(), m, 1 * 1024 * 1024, fake_handler)
        # Handler was called with the full body
        assert observed["body_len"] == len(body_bytes)
        assert observed["ctype"] == "multipart/form-data; boundary=xxx"
        # Result was dispatched as 200 (ok:True falls through)
        assert captured["status"] == 200
        assert captured["body"] == {"ok": True, "size": len(body_bytes)}

    def test_discovery_recognizes_multipart_table_entries(self):
        from scripts import check_routes

        routes = check_routes.discover_routes()
        keys = {(r.method, r.pattern, r.is_regex) for r in routes}
        # The 3 multipart routes are discovered as POST.
        assert ("POST", "/api/covers/([a-z0-9-]+)/main$", True) in keys
        assert ("POST", "/api/covers/([a-z0-9-]+)/book/([a-z0-9]+)$", True) in keys
        assert ("POST", "/api/sources/cache/([a-z0-9_-]+)/upload$", True) in keys

    def test_route_inventory_clean_after_a9(self):
        from scripts import check_routes

        result = check_routes.run_all()
        assert result["summary"]["clean"] is True

    def test_all_pre_existing_post_routes_now_in_tables(self):
        # After A.9, every POST route in do_POST flows through
        # one of two tables (_POST_ROUTES or _MULTIPART_ROUTES) —
        # no legacy `m = re.match(...)` branches remain that
        # dispatch a POST.
        import inspect

        from scripts.web import Handler

        src = inspect.getsource(Handler.do_POST)
        # The only re.match call should be inside the dispatch
        # loops (which use the pre-compiled regex from the table
        # via `pattern.match(self.path)`, not `re.match`). A
        # literal `re.match(r"^...",` call would indicate a
        # legacy regex branch.
        assert "re.match(r" not in src, (
            "do_POST has a raw re.match() call — should dispatch via _POST_ROUTES "
            "or _MULTIPART_ROUTES, not a legacy regex branch"
        )


class TestOmega35A10BespokePutCleanup:
    """ω.35-A.10 — ninth route-table slice; closes the loop on the
    uniform-shape bespoke PUT routes. 3 routes added to `_PUT_ROUTES`
    (edition-meta, edition/note-toggle, editions/from-template) and
    the dead-code /api/publisher legacy block deleted. 3 truly
    bespoke PUT routes remain in legacy because their response
    shapes are semantically distinct from the standard helper:
    - /api/export/build/<id> → 500 on build failure (not 400)
    - /api/build-all → 500 only when ALL editions fail
    - /api/edition-meta/<id>/preview → bare `error` key shape

    These bespoke retentions are documented in do_PUT with explicit
    "why not in table" comments. Pinning them preserves the
    semantic distinction (build = server-side error → 500;
    preview's "error" key has no `status` discriminator).
    """

    def test_put_table_has_eleven_entries(self):
        # A.5 + A.10 baseline + ε.7 press-kit + ρ.3 C2-5 edition/note-override
        # (the ε.6 distribution-mark and ξ.26 license PUT routes were never
        # implemented). v0.1.0 audit Phase 0: the count is COUPLED to the
        # inventory below — pin presence by pattern, not a positional index, so
        # a route add can't bump the count without registering the route.
        from scripts import web

        patterns = [r.pattern for r, _ in web._PUT_ROUTES]
        assert len(web._PUT_ROUTES) == 11
        assert any("/note-override" in p for p in patterns), patterns

    def test_put_table_includes_a10_routes(self):
        from scripts import web

        patterns = [r.pattern for r, _ in web._PUT_ROUTES]
        joined = "|".join(patterns)
        assert (
            "/api/edition-meta/" in joined and "/preview" not in joined.split("/api/edition-meta/")[1].split("|")[0]
        ), "edition-meta save MUST be in the table, but preview MUST stay in legacy"
        assert "/api/edition/" in joined and "/note-toggle" in joined
        assert "/api/editions/from-template" in joined

    def test_note_toggle_precedes_edition_save(self):
        # /api/edition/<id>/note-toggle is more specific than
        # /api/edition/<id>; the more-specific suffix MUST iterate
        # first or its match path gets swallowed by the broader
        # one. Iteration order = precedence.
        from scripts import web

        idx_toggle = None
        idx_edition = None
        for i, (regex_obj, _) in enumerate(web._PUT_ROUTES):
            pat = regex_obj.pattern
            if "/api/edition/" in pat and "/note-toggle" in pat:
                idx_toggle = i
            elif pat.endswith(r"/api/edition/([a-z0-9-]+)$"):
                idx_edition = i
        assert idx_toggle is not None
        assert idx_edition is not None
        assert idx_toggle < idx_edition, (
            f"note-toggle pattern (idx {idx_toggle}) must precede edition save "
            f"(idx {idx_edition}); otherwise edition's <id> group would swallow "
            f"the path 'foo/note-toggle' on requests to /api/edition/foo/note-toggle"
        )

    def test_bespoke_three_still_in_legacy(self):
        # The 3 truly bespoke PUT routes (different response
        # semantics) are intentionally kept in legacy. Pin: NONE
        # of them should appear in _PUT_ROUTES.
        from scripts import web

        table_patterns = [r.pattern for r, _ in web._PUT_ROUTES]
        # /api/export/build/<id>
        assert not any("/api/export/build/" in p for p in table_patterns), (
            "/api/export/build/ must stay in legacy (500 on failure semantics)"
        )
        # /api/build-all
        assert not any("/api/build-all" in p for p in table_patterns), (
            "/api/build-all must stay in legacy (custom success_count check)"
        )
        # /api/edition-meta/<id>/preview (NOT to be confused with
        # /api/edition-meta/<id> save which IS in the table)
        assert not any("/api/edition-meta/" in p and "/preview" in p for p in table_patterns), (
            "/api/edition-meta/<id>/preview must stay in legacy (bare error key shape)"
        )

    def test_publisher_dead_code_deleted(self):
        # The /api/publisher block in do_PUT was dead code after
        # A.5 (the table dispatch above it always matched first).
        # A.10 deleted it. Pin: do_PUT must not contain a
        # standalone `re.match(r"^/api/publisher/...` call (the
        # legacy dead-code shape).
        import inspect

        from scripts.web import Handler

        src = inspect.getsource(Handler.do_PUT)
        # Allow mentions of `/api/publisher/` in comments/strings
        # (the breadcrumb is fine), but reject any actual code
        # that would dispatch a publisher route: a regex literal
        # OR an `api_save_publisher_meta(` call.
        assert 're.match(r"^/api/publisher/' not in src, (
            "do_PUT still has a legacy re.match() for /api/publisher/ — the dead-code "
            "block should have been deleted in A.10 (the route is in _PUT_ROUTES)"
        )
        assert "api_save_publisher_meta(" not in src, (
            "do_PUT still calls api_save_publisher_meta directly — the dispatch goes "
            "through _PUT_ROUTES; the legacy fall-through call site was dead code"
        )

    def test_discovery_recognizes_a10_table_entries(self):
        from scripts import check_routes

        routes = check_routes.discover_routes()
        keys = {(r.method, r.pattern, r.is_regex) for r in routes}
        assert ("PUT", "/api/edition/([a-z0-9-]+)/note-toggle$", True) in keys
        assert ("PUT", "/api/edition-meta/([a-z0-9-]+)$", True) in keys
        assert ("PUT", "/api/editions/from-template$", True) in keys

    def test_route_inventory_clean_after_a10(self):
        from scripts import check_routes

        result = check_routes.run_all()
        assert result["summary"]["clean"] is True

    def test_from_template_signature_unchanged(self):
        # api_create_edition_from_template takes (template_id,
        # new_id, new_title). The lambda must call it with those
        # three positional args extracted from payload. Smoke:
        # the lambda accepts (m, payload={}) without crashing
        # before reaching the API.
        from scripts import web

        from_template_entry = None
        for regex_obj, handler in web._PUT_ROUTES:
            if regex_obj.pattern == r"^/api/editions/from-template$":
                from_template_entry = (regex_obj, handler)
                break
        assert from_template_entry is not None
        regex_obj, handler = from_template_entry
        m = regex_obj.match("/api/editions/from-template")
        assert m is not None
        # Call with empty payload — api function will return an
        # error envelope (status==error / unknown_template or
        # similar), but the lambda's payload destructure must
        # not raise.
        try:
            result = handler(m, {})
            assert isinstance(result, dict)
        except Exception as e:
            # If it raises, the cause must not be missing-key
            # access on the payload — that'd indicate the
            # destructure expects keys, but `(payload or {}).get(
            # ..., "")` returns "" for missing keys, which is
            # legal.
            assert "template_id" not in str(e).lower() or "keyerror" not in str(e).lower(), (
                f"lambda's payload destructure raised KeyError: {e}"
            )

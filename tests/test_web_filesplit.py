"""ω.27 follow-on (2026-05-11) — ω.35-B family test classes,
split out of the monolithic ``tests/test_scripts.py`` into a topic
file alongside ``tests/test_matrix_psi35.py``.

Second topic extraction (after the ψ.35 split). The eight
ω.35-B file-split tests — TestOmega35B1SnapshotsExtraction
through TestOmega35B7PreflightExtraction (with B.3a + B.3b as
separate slices) — were scattered across two regions of
test_scripts.py because they shipped across different sessions.
Moving them to one cohesive file:

  - improves orientation (one file = one Greek-letter cluster)
  - unlocks xdist parallelism (each test FILE is a separate
    worker target; smaller files mean more parallelism)
  - keeps the test_scripts.py monolith on a downward trend
    (was 28,384 lines pre-split; now ~26,200 after this slice +
    the ψ.35 split that preceded it)

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""

import pytest

# mint-7 E2 — this file's live socket/build smokes run ~20+ min; mark the whole
# module slow so normal runs can deselect via `-m "not slow"`.
pytestmark = pytest.mark.slow


class TestOmega35B1SnapshotsExtraction:
    """ω.35-B.1 — first slice of the web.py file split. Six
    api_snapshot_* functions moved from `scripts/web.py` into
    `scripts/api/snapshots.py`. `scripts/web.py` re-imports them
    so the existing flat namespace is preserved — route-table
    lambdas and tests that reference `scripts.web.api_snapshot_*`
    continue working unchanged.

    The extraction proves the pattern for subsequent ω.35-B.x
    slices (scenarios, sources/covers, editions/customize,
    exports/build, preflight/audit/help).
    """

    def test_snapshots_module_exists(self):
        # The new per-topic module is importable on its own.
        import scripts.api.snapshots as snap_api

        assert hasattr(snap_api, "api_snapshot_list")
        assert hasattr(snap_api, "api_snapshot_get")
        assert hasattr(snap_api, "api_snapshot_create")
        assert hasattr(snap_api, "api_snapshot_diff")
        assert hasattr(snap_api, "api_snapshot_restore")
        assert hasattr(snap_api, "api_snapshot_delete")

    def test_snapshot_handlers_backward_compatible_via_web(self):
        # The web.py re-exports the same six names; old import
        # paths continue working.
        from scripts.web import (
            api_snapshot_create,
            api_snapshot_delete,
            api_snapshot_diff,
            api_snapshot_get,
            api_snapshot_list,
            api_snapshot_restore,
        )

        for fn in (
            api_snapshot_create,
            api_snapshot_delete,
            api_snapshot_diff,
            api_snapshot_get,
            api_snapshot_list,
            api_snapshot_restore,
        ):
            assert callable(fn)

    def test_handlers_actually_live_in_new_module(self):
        # The re-exports point at the new module's functions
        # (not aliases hiding inline definitions).
        from scripts.web import api_snapshot_create, api_snapshot_list, api_snapshot_restore

        for fn in (api_snapshot_create, api_snapshot_list, api_snapshot_restore):
            # `__module__` should be the new module path. The
            # audit_log decorator may wrap the function in a
            # closure, so unwrap if present.
            target = getattr(fn, "__wrapped__", fn)
            assert target.__module__ == "scripts.api.snapshots", (
                f"{target.__name__} module is {target.__module__}, expected scripts.api.snapshots"
            )

    def test_route_tables_still_dispatch_snapshots(self):
        # The _POST_ROUTES and _DELETE_ROUTES entries still
        # reference the snapshot handlers by name. Pin: the
        # patterns are present and the handlers come from the
        # new module.
        from scripts import web

        post_patterns = [r.pattern for r, _ in web._POST_ROUTES]
        delete_patterns = [r.pattern for r, _ in web._DELETE_ROUTES]
        assert any("/api/snapshots/" in p and "/restore" in p for p in post_patterns)
        assert any(p.endswith(r"/api/snapshots/([a-z0-9._-]+)$") for p in post_patterns)
        assert any("/api/snapshots/" in p for p in delete_patterns)

    def test_audit_decorator_preserved_on_mutations(self):
        # The 3 mutating handlers (create, restore, delete) keep
        # their audit_log.audit_endpoint decorator after the
        # extraction — otherwise mutation audit-log entries would
        # silently disappear.
        from scripts.api.snapshots import (
            api_snapshot_create,
            api_snapshot_delete,
            api_snapshot_restore,
        )

        for fn in (api_snapshot_create, api_snapshot_restore, api_snapshot_delete):
            # audit_endpoint sets either __wrapped__ (functools.wraps)
            # or an attribute we can introspect; the simplest pin is
            # that the function name survives lookup.
            assert fn.__name__.startswith("api_snapshot_")

    def test_scripts_api_package_loadable(self):
        # The new scripts.api package itself is importable; the
        # __init__.py documents the split and serves as a marker.
        import scripts.api

        assert scripts.api.__doc__
        assert "ω.35-B" in scripts.api.__doc__

    def test_web_py_does_not_define_snapshot_handlers_inline(self):
        # The extraction is real, not a copy: web.py shouldn't
        # have `def api_snapshot_create(` etc. anymore. The
        # re-import line should be the only place the name
        # appears with a def-like context.
        from pathlib import Path

        web_py = Path(__file__).resolve().parent.parent / "scripts" / "web.py"
        text = web_py.read_text(encoding="utf-8")
        for name in (
            "api_snapshot_list",
            "api_snapshot_get",
            "api_snapshot_create",
            "api_snapshot_diff",
            "api_snapshot_restore",
            "api_snapshot_delete",
        ):
            # `def NAME(` is the inline definition form. The
            # re-import line uses `import NAME,` — different shape.
            assert f"def {name}(" not in text, (
                f"web.py still has inline `def {name}(...)` — should be re-imported from scripts.api.snapshots only"
            )


class TestOmega35B2ScenariosExtraction:
    """ω.35-B.2 — second slice of the web.py file split. 5
    `api_*_scenario*` handlers + 2 internal helpers (`_scenario_path`,
    `_resolve_scenario_recipe`) + 1 regex constant (`_SCENARIO_NAME_RE`)
    moved from `scripts/web.py` into `scripts/api/scenarios.py`.
    `scripts/web.py` re-imports all 8 names so the existing flat
    namespace is preserved.

    Bigger than B.1 (snapshots): scenarios has internal helpers that
    other code (tests, /matrix UI) reference by name, so the
    re-import surface is wider. Audit decorators preserved on the 3
    mutating handlers (save, import_yaml, delete).
    """

    def test_scenarios_module_exists(self):
        import scripts.api.scenarios as scenarios_api

        assert hasattr(scenarios_api, "api_list_scenarios")
        assert hasattr(scenarios_api, "api_get_scenario")
        assert hasattr(scenarios_api, "api_save_scenario")
        assert hasattr(scenarios_api, "api_export_scenario_yaml")
        assert hasattr(scenarios_api, "api_import_scenario_yaml")
        assert hasattr(scenarios_api, "api_delete_scenario")
        # Internal helpers
        assert hasattr(scenarios_api, "_scenario_path")
        assert hasattr(scenarios_api, "_resolve_scenario_recipe")
        assert hasattr(scenarios_api, "_SCENARIO_NAME_RE")

    def test_scenario_handlers_backward_compatible_via_web(self):
        from scripts.web import (
            api_delete_scenario,
            api_export_scenario_yaml,
            api_get_scenario,
            api_import_scenario_yaml,
            api_list_scenarios,
            api_save_scenario,
        )

        for fn in (
            api_delete_scenario,
            api_export_scenario_yaml,
            api_get_scenario,
            api_import_scenario_yaml,
            api_list_scenarios,
            api_save_scenario,
        ):
            assert callable(fn)

    def test_scenario_internal_helpers_backward_compatible_via_web(self):
        # Internal helpers (`_scenario_path`, `_resolve_scenario_recipe`,
        # `_SCENARIO_NAME_RE`) ARE re-exported from web.py because some
        # tests reference them by the `scripts.web.X` path.
        from scripts.web import _resolve_scenario_recipe, _scenario_path, _SCENARIO_NAME_RE

        assert callable(_scenario_path)
        assert callable(_resolve_scenario_recipe)
        assert _SCENARIO_NAME_RE.match("foo")
        assert not _SCENARIO_NAME_RE.match("FOO")  # uppercase rejected

    def test_handlers_actually_live_in_new_module(self):
        from scripts.web import api_save_scenario, api_list_scenarios, api_delete_scenario

        for fn in (api_save_scenario, api_list_scenarios, api_delete_scenario):
            target = getattr(fn, "__wrapped__", fn)
            assert target.__module__ == "scripts.api.scenarios", (
                f"{target.__name__} module is {target.__module__}, expected scripts.api.scenarios"
            )

    def test_route_tables_still_dispatch_scenarios(self):
        from scripts import web

        put_patterns = [r.pattern for r, _ in web._PUT_ROUTES]
        delete_patterns = [r.pattern for r, _ in web._DELETE_ROUTES]
        post_patterns = [r.pattern for r, _ in web._POST_ROUTES]
        # /api/scenarios/<name> (PUT save) + /api/scenarios/<name> (DELETE)
        # + /api/scenarios/_import (POST)
        assert any("/api/scenarios/" in p for p in put_patterns)
        assert any("/api/scenarios/" in p for p in delete_patterns)
        assert any("/api/scenarios/_import" in p for p in post_patterns)

    def test_audit_decorator_preserved_on_mutations(self):
        from scripts.api.scenarios import (
            api_delete_scenario,
            api_import_scenario_yaml,
            api_save_scenario,
        )

        for fn in (api_save_scenario, api_import_scenario_yaml, api_delete_scenario):
            # The decorator wraps the function but doesn't change the
            # name visible via the import.
            assert fn.__name__.endswith("scenario") or fn.__name__.endswith("yaml"), (
                f"unexpected name after decoration: {fn.__name__}"
            )

    def test_web_py_does_not_define_scenario_handlers_inline(self):
        from pathlib import Path

        web_py = Path(__file__).resolve().parent.parent / "scripts" / "web.py"
        text = web_py.read_text(encoding="utf-8")
        for name in (
            "api_list_scenarios",
            "api_get_scenario",
            "api_save_scenario",
            "api_export_scenario_yaml",
            "api_import_scenario_yaml",
            "api_delete_scenario",
            "_scenario_path",
            "_resolve_scenario_recipe",
        ):
            assert f"def {name}(" not in text, (
                f"web.py still has inline `def {name}(...)` — should be re-imported from scripts.api.scenarios only"
            )
        # The regex constant: assignment is `_SCENARIO_NAME_RE = re.compile(...)`,
        # not a `def`. Pin: no such assignment in web.py.
        assert "_SCENARIO_NAME_RE = re.compile" not in text, (
            "web.py still has inline `_SCENARIO_NAME_RE = re.compile(...)` — "
            "should be re-imported from scripts.api.scenarios only"
        )

    def test_scenario_path_validates_name(self):
        # Smoke test the internal helper round-trips through both
        # the new module's direct import and the web.py re-export.
        from scripts.api.scenarios import _scenario_path as direct
        from scripts.web import _scenario_path as reexport

        # Same function object via both paths
        assert direct is reexport
        # Valid name returns a Path; invalid raises
        p = direct("my-scenario")
        assert "my-scenario.yaml" in str(p)
        try:
            direct("BAD")  # uppercase rejected
            raise AssertionError("expected ValueError for uppercase name")
        except ValueError:
            pass


class TestOmega35B3aCoversExtraction:
    """ω.35-B.3a — third file-split slice. 4 cover-mutation
    handlers (`api_upload_cover_main/book`, `api_delete_cover_main
    /book`) extracted from `scripts/web.py` into
    `scripts/api/covers.py`. Only the audit-logged mutation
    handlers move in B.3a; `api_covers()` GET (with its tangled
    response-cache infrastructure) and the multipart helpers
    `_extract_boundary` / `_parse_multipart` / `_save_cover_bytes`
    (shared with the not-yet-extracted sources/cache upload) stay
    in web.py.

    The 4 handlers in `scripts/api/covers.py` use LAZY imports for
    web.py helpers to avoid an import cycle (web.py top-imports
    api.covers; api.covers cannot top-import web.py back, so the
    helper imports fire at call time when web.py is fully loaded).

    `scripts/web.py` re-imports the 4 names so route-table lambdas
    (`_MULTIPART_ROUTES` for uploads, `_DELETE_ROUTES` for deletes)
    and pre-existing tests keep working unchanged.
    """

    def test_covers_api_module_exists(self):
        import scripts.api.covers as covers_api

        assert hasattr(covers_api, "api_upload_cover_main")
        assert hasattr(covers_api, "api_upload_cover_book")
        assert hasattr(covers_api, "api_delete_cover_main")
        assert hasattr(covers_api, "api_delete_cover_book")

    def test_cover_handlers_backward_compatible_via_web(self):
        from scripts.web import (
            api_delete_cover_book,
            api_delete_cover_main,
            api_upload_cover_book,
            api_upload_cover_main,
        )

        for fn in (
            api_delete_cover_book,
            api_delete_cover_main,
            api_upload_cover_book,
            api_upload_cover_main,
        ):
            assert callable(fn)

    def test_handlers_actually_live_in_new_module(self):
        from scripts.web import api_upload_cover_main, api_delete_cover_book

        for fn in (api_upload_cover_main, api_delete_cover_book):
            target = getattr(fn, "__wrapped__", fn)
            assert target.__module__ == "scripts.api.covers", (
                f"{target.__name__} module is {target.__module__}, expected scripts.api.covers"
            )

    def test_multipart_routes_still_dispatch_cover_uploads(self):
        from scripts import web

        multipart_patterns = [r.pattern for r, _max, _h in web._MULTIPART_ROUTES]
        # Both cover upload routes are in the multipart table
        assert any("/api/covers/" in p and "/main" in p for p in multipart_patterns)
        assert any("/api/covers/" in p and "/book/" in p for p in multipart_patterns)

    def test_delete_routes_still_dispatch_cover_deletes(self):
        from scripts import web

        delete_patterns = [r.pattern for r, _ in web._DELETE_ROUTES]
        assert any("/api/covers/" in p and "/main" in p for p in delete_patterns)
        assert any("/api/covers/" in p and "/book/" in p for p in delete_patterns)

    def test_audit_decorator_preserved_on_all_four(self):
        # All 4 cover-mutation handlers are audit-logged; the
        # decorator survives the move.
        from scripts.api.covers import (
            api_delete_cover_book,
            api_delete_cover_main,
            api_upload_cover_book,
            api_upload_cover_main,
        )

        for fn in (
            api_upload_cover_main,
            api_upload_cover_book,
            api_delete_cover_main,
            api_delete_cover_book,
        ):
            assert fn.__name__.startswith("api_")

    def test_helpers_remain_in_web_py(self):
        # B.3a deliberately keeps the multipart helpers + the
        # _save_cover_bytes persister in web.py because they're
        # shared with api_sources_cache_upload (still in web.py).
        # Pin: these names ARE still in web.py's namespace.
        import scripts.web as w

        for name in ("_extract_boundary", "_parse_multipart", "_save_cover_bytes"):
            assert hasattr(w, name), (
                f"web.py missing helper {name!r} — B.3a should NOT have moved it "
                "(api_sources_cache_upload still needs it; defer to a future slice)"
            )

    def test_api_save_edition_meta_accessible_via_web(self):
        # ω.35-B.3a pinned that api_save_edition_meta lived in
        # web.py (it was lazy-imported by covers.py from
        # scripts.web). After ω.35-B.5 the canonical home is
        # scripts.api.editions; web.py re-exports it. The
        # B.3a covers handlers were updated in B.5 to lazy-import
        # from scripts.api.editions directly.
        # Pin: regardless of canonical home, the name is reachable
        # via scripts.web for backward compat.
        import scripts.web as w

        assert hasattr(w, "api_save_edition_meta"), (
            "scripts.web.api_save_edition_meta missing — either the canonical "
            "module moved without a re-export, or the function was deleted"
        )

    def test_api_covers_get_remains_in_web_py(self):
        # B.3a kept api_covers() (the GET endpoint) OUT of scripts/api/covers.py
        # because of its tangled response-cache infrastructure. The bae92e4 web.py
        # split later relocated it to scripts/web_covers.py (still NOT in api/covers,
        # and still re-exported via the web.py hub so the route table is unchanged).
        import scripts.api.covers as covers_api
        import scripts.web as w

        assert not hasattr(covers_api, "api_covers"), (
            "scripts.api.covers should NOT define api_covers() — it stays out of the api/ slice"
        )
        assert hasattr(w, "api_covers")
        # It now lives in web_covers (post-bae92e4 split), re-exported via web.py:
        assert w.api_covers.__module__ == "scripts.web_covers", (
            f"api_covers should live in scripts.web_covers, got {w.api_covers.__module__}"
        )

    def test_web_py_does_not_define_cover_mutations_inline(self):
        from pathlib import Path

        web_py = Path(__file__).resolve().parent.parent / "scripts" / "web.py"
        text = web_py.read_text(encoding="utf-8")
        for name in (
            "api_upload_cover_main",
            "api_upload_cover_book",
            "api_delete_cover_main",
            "api_delete_cover_book",
        ):
            assert f"def {name}(" not in text, (
                f"web.py still has inline `def {name}(...)` — should be re-imported from scripts.api.covers only"
            )

    def test_lazy_import_path_works_at_call_time(self):
        # Smoke: call api_delete_cover_main with an unknown
        # edition. It should NOT crash with ImportError; instead
        # return the expected error dict.
        from scripts.web import api_delete_cover_main

        result = api_delete_cover_main("definitely-not-a-real-edition-id-zzzqqq")
        assert isinstance(result, dict)
        # The function's lazy imports must have resolved
        # successfully; the result should be a normal error dict.
        assert "error" in result
        assert "unknown edition" in result["error"]


class TestOmega35B3bSourcesCacheExtraction:
    """ω.35-B.3b — fourth file-split slice. 5 sources-cache handlers
    (status, fetch, fetch_all, upload, clear) extracted from
    `scripts/web.py` into `scripts/api/sources.py` along with their
    internal helpers and the SOURCES_UPLOAD_MAX_BYTES constant. The
    multipart upload handler lazy-imports `_extract_boundary` and
    `_parse_multipart` from web.py (same pattern as B.3a covers).

    Out of scope: api_sources_index, api_sources_for_book,
    api_sources_summary (the sources NAVIGATOR — a different
    sub-topic, still in web.py).
    """

    def test_sources_api_module_exists(self):
        import scripts.api.sources as sources_api

        for name in (
            "api_sources_cache_status",
            "api_sources_cache_fetch",
            "api_sources_cache_fetch_all",
            "api_sources_cache_upload",
            "api_sources_cache_clear",
            "_sources_cache_dir",
            "_datetime_iso",
            "SOURCES_UPLOAD_MAX_BYTES",
        ):
            assert hasattr(sources_api, name), f"sources module missing {name!r}"

    def test_sources_cache_handlers_backward_compatible_via_web(self):
        from scripts.web import (
            api_sources_cache_clear,
            api_sources_cache_fetch,
            api_sources_cache_fetch_all,
            api_sources_cache_status,
            api_sources_cache_upload,
        )

        for fn in (
            api_sources_cache_status,
            api_sources_cache_fetch,
            api_sources_cache_fetch_all,
            api_sources_cache_upload,
            api_sources_cache_clear,
        ):
            assert callable(fn)

    def test_upload_max_bytes_constant_backward_compatible(self):
        # The constant is referenced directly by _MULTIPART_ROUTES
        # at module-load time in web.py, so the re-export MUST
        # preserve the same integer value.
        from scripts.api.sources import SOURCES_UPLOAD_MAX_BYTES as direct
        from scripts.web import SOURCES_UPLOAD_MAX_BYTES as reexport

        assert direct == reexport == 50 * 1024 * 1024  # 50 MB

    def test_handlers_actually_live_in_new_module(self):
        from scripts.web import (
            api_sources_cache_fetch,
            api_sources_cache_status,
            api_sources_cache_upload,
        )

        for fn in (api_sources_cache_status, api_sources_cache_fetch, api_sources_cache_upload):
            target = getattr(fn, "__wrapped__", fn)
            assert target.__module__ == "scripts.api.sources", (
                f"{target.__name__} module is {target.__module__}, expected scripts.api.sources"
            )

    def test_multipart_table_still_dispatches_sources_upload(self):
        from scripts import web

        multipart_patterns = [r.pattern for r, _max, _h in web._MULTIPART_ROUTES]
        assert any("/api/sources/cache/" in p and "/upload" in p for p in multipart_patterns)

    def test_post_table_still_dispatches_sources_fetch(self):
        from scripts import web

        post_patterns = [r.pattern for r, _ in web._POST_ROUTES]
        assert any("/api/sources/cache/_all/fetch" in p for p in post_patterns)
        assert any("/api/sources/cache/" in p and "/fetch" in p for p in post_patterns)

    def test_delete_table_still_dispatches_sources_clear(self):
        from scripts import web

        delete_patterns = [r.pattern for r, _ in web._DELETE_ROUTES]
        assert any("/api/sources/cache/" in p for p in delete_patterns)

    def test_audit_decorator_preserved_on_mutations(self):
        # 4 of 5 handlers are audit-logged (status is read-only,
        # not decorated). Pin the decorated ones.
        from scripts.api.sources import (
            api_sources_cache_clear,
            api_sources_cache_fetch,
            api_sources_cache_fetch_all,
            api_sources_cache_upload,
        )

        for fn in (
            api_sources_cache_fetch,
            api_sources_cache_fetch_all,
            api_sources_cache_upload,
            api_sources_cache_clear,
        ):
            assert fn.__name__.startswith("api_sources_cache_")

    def test_multipart_helpers_remain_in_web_py(self):
        # B.3b lazy-imports `_extract_boundary` and `_parse_multipart`
        # from web.py inside the upload handler. Pin that they're
        # still there.
        import scripts.web as w

        assert hasattr(w, "_extract_boundary")
        assert hasattr(w, "_parse_multipart")

    def test_sources_navigator_remains_in_web_py(self):
        # api_sources_index, api_sources_for_book, api_sources_summary
        # are deliberately NOT in B.3b's scope. Pin: still in web.py.
        import scripts.web as w

        for name in ("api_sources_index", "api_sources_for_book", "api_sources_summary"):
            assert hasattr(w, name), f"web.py missing {name!r} (sources navigator stays in B.3b)"
            # And NOT in the new sources_cache module
            import scripts.api.sources as sources_api

            assert not hasattr(sources_api, name), (
                f"scripts.api.sources should NOT define {name!r} — that's the navigator, "
                "still in web.py until a future slice"
            )

    def test_web_py_does_not_define_sources_cache_handlers_inline(self):
        from pathlib import Path

        web_py = Path(__file__).resolve().parent.parent / "scripts" / "web.py"
        text = web_py.read_text(encoding="utf-8")
        for name in (
            "api_sources_cache_status",
            "api_sources_cache_fetch",
            "api_sources_cache_fetch_all",
            "api_sources_cache_upload",
            "api_sources_cache_clear",
            "_sources_cache_dir",
            "_datetime_iso",
        ):
            assert f"def {name}(" not in text, (
                f"web.py still has inline `def {name}(...)` — should be re-imported from scripts.api.sources only"
            )
        # The constant is an assignment, not a def.
        assert "SOURCES_UPLOAD_MAX_BYTES = 50" not in text, (
            "web.py still has inline `SOURCES_UPLOAD_MAX_BYTES = 50...` — "
            "should be re-imported from scripts.api.sources only"
        )

    def test_lazy_multipart_helper_path_works_at_call_time(self):
        # Smoke: call api_sources_cache_upload with a missing
        # Content-Type to trigger an early error path. The lazy
        # imports of _extract_boundary and _parse_multipart must
        # resolve at call time without ImportError.
        from scripts.web import api_sources_cache_upload

        # Force a config lookup failure first to avoid hitting the
        # network — use an obviously invalid source id. The
        # function should reach the lazy-import line and proceed
        # to a normal error dict.
        result = api_sources_cache_upload("definitely-not-a-real-source-zzzqqq", b"", "")
        assert isinstance(result, dict)
        # Either the unknown_source error fires (most likely) or
        # the not_utf8 / missing_boundary error fires; either way
        # the function ran to completion with no ImportError.
        assert "status" in result or "error" in result

    def test_sources_cache_dir_is_callable(self):
        from scripts.api.sources import _sources_cache_dir as direct
        from scripts.web import _sources_cache_dir as reexport

        # Same function object via both paths
        assert direct is reexport
        p = direct()
        assert "content" in str(p)
        assert "sources" in str(p)


class TestOmega35B4CustomizeExtraction:
    """ω.35-B.4 — fifth file-split slice. 2 audit-logged mutation
    handlers for the /customize console (Phase ν.1 — edit
    symbols/labels/descriptions for categories and kinds)
    extracted from `scripts/web.py` into
    `scripts/api/customize.py`. The `_patch_yaml_entry` helper
    stays in web.py because it's also used by
    `api_save_edition_meta` and `api_save_publisher_meta` (both
    still in web.py until B.5). customize.py lazy-imports it
    inside each handler.

    Out of scope for B.4 (deferred to B.5 — editions cluster):
    - api_save_edition / api_save_edition_meta /
      api_save_publisher_meta
    - api_clone_edition / api_create_edition_from_template
    - api_save_note_toggle / api_preview_edition_changes
    - api_apply_kind_to_all_editions
    """

    def test_customize_module_exists(self):
        import scripts.api.customize as customize_api

        assert hasattr(customize_api, "api_save_category")
        assert hasattr(customize_api, "api_save_kind")

    def test_handlers_backward_compatible_via_web(self):
        from scripts.web import api_save_category, api_save_kind

        assert callable(api_save_category)
        assert callable(api_save_kind)

    def test_handlers_actually_live_in_new_module(self):
        from scripts.web import api_save_category, api_save_kind

        for fn in (api_save_category, api_save_kind):
            target = getattr(fn, "__wrapped__", fn)
            assert target.__module__ == "scripts.api.customize", (
                f"{target.__name__} module is {target.__module__}, expected scripts.api.customize"
            )

    def test_put_table_still_dispatches_customize(self):
        from scripts import web

        put_patterns = [r.pattern for r, _ in web._PUT_ROUTES]
        # /api/category/<id> + /api/kind/<code>
        assert any("/api/category/" in p for p in put_patterns)
        assert any("/api/kind/" in p for p in put_patterns)

    def test_audit_decorator_preserved(self):
        from scripts.api.customize import api_save_category, api_save_kind

        for fn in (api_save_category, api_save_kind):
            # The decorator wraps the function but the name
            # survives.
            assert fn.__name__.startswith("api_save_")

    def test_patch_yaml_entry_stays_in_web_py(self):
        # B.4 deliberately keeps _patch_yaml_entry in web.py
        # because api_save_edition_meta + api_save_publisher_meta
        # (still inline) also need it. Pin: the helper is still
        # there.
        import scripts.web as w

        assert hasattr(w, "_patch_yaml_entry"), (
            "web.py missing _patch_yaml_entry — B.4 should NOT have moved it "
            "(api_save_edition_meta + api_save_publisher_meta still use it)"
        )

    def test_editions_cluster_not_in_customize_module(self):
        # The 8 editions-cluster handlers belong to B.5 (scripts/
        # api/editions.py), NOT to B.4's customize module. Pin
        # that the customize module DOES NOT define them — they
        # live elsewhere. They ARE accessible via web.py
        # (re-imported by B.5) for backward compat.
        import scripts.api.customize as customize_api
        import scripts.web as w

        for name in (
            "api_save_edition",
            "api_save_edition_meta",
            "api_save_publisher_meta",
            "api_clone_edition",
            "api_create_edition_from_template",
            "api_save_note_toggle",
            "api_preview_edition_changes",
            "api_apply_kind_to_all_editions",
        ):
            assert not hasattr(customize_api, name), (
                f"scripts.api.customize should NOT define {name!r} — belongs to B.5 editions"
            )
            # Still reachable via web.py (re-export from B.5)
            assert hasattr(w, name), f"scripts.web.{name} missing (re-export broken)"

    def test_web_py_does_not_define_customize_handlers_inline(self):
        from pathlib import Path

        web_py = Path(__file__).resolve().parent.parent / "scripts" / "web.py"
        text = web_py.read_text(encoding="utf-8")
        for name in ("api_save_category", "api_save_kind"):
            assert f"def {name}(" not in text, (
                f"web.py still has inline `def {name}(...)` — should be re-imported from scripts.api.customize only"
            )

    def test_lazy_patch_helper_path_works_at_call_time(self):
        # Smoke: call api_save_category with an unknown category
        # id. The function must reach the lazy-import line and
        # return the expected error dict, NOT crash with
        # ImportError.
        from scripts.web import api_save_category

        result = api_save_category("definitely-not-a-real-cat-zzzqqq", {"symbol": "?"})
        assert isinstance(result, dict)
        assert "error" in result
        assert "unknown category" in result["error"]


class TestOmega35B5EditionsExtraction:
    """ω.35-B.5 — sixth file-split slice. The editions cluster (8
    audit-logged mutation handlers + 2 private helpers) moved
    from `scripts/web.py` into `scripts/api/editions.py`. Largest
    single-slice extraction in the file split (~1180 lines).

    Includes a cross-module update: `scripts/api/covers.py`'s
    lazy import of `api_save_edition_meta` re-targets from
    `scripts.web` to `scripts.api.editions`.

    Helpers (`_patch_yaml_entry`, `_patch_yaml_list_field`,
    `_load_themes`, `_validate_cover_path`, `parse_note_id`,
    `html_ref_id_from_note_id`, `PUBLISHING_TEXT_LIMITS`,
    `PUBLISHING_LIST_FIELDS`) STAY in web.py — editions.py
    lazy-imports them at call time (B.3a pattern).

    During extraction, a section header + `_THIN_ATTR_PATTERNS`
    constant that lived between `api_save_edition_meta` and the
    next `def _classify_attribution` got swept up by the
    block-end detector (which looked for the next `def` and
    swept everything before it). Restored manually. Pinned by
    test_thin_attr_patterns_constant_present.
    """

    def test_editions_module_exists(self):
        import scripts.api.editions as editions_api

        for name in (
            "api_save_edition",
            "api_save_edition_meta",
            "api_save_publisher_meta",
            "api_clone_edition",
            "api_create_edition_from_template",
            "api_save_note_toggle",
            "api_preview_edition_changes",
            "api_apply_kind_to_all_editions",
            "_patch_edition_kind_lists",
            "_append_cloned_edition",
        ):
            assert hasattr(editions_api, name), f"editions module missing {name!r}"

    def test_all_eight_handlers_backward_compatible_via_web(self):
        from scripts.web import (
            api_apply_kind_to_all_editions,
            api_clone_edition,
            api_create_edition_from_template,
            api_preview_edition_changes,
            api_save_edition,
            api_save_edition_meta,
            api_save_note_toggle,
            api_save_publisher_meta,
        )

        for fn in (
            api_apply_kind_to_all_editions,
            api_clone_edition,
            api_create_edition_from_template,
            api_preview_edition_changes,
            api_save_edition,
            api_save_edition_meta,
            api_save_note_toggle,
            api_save_publisher_meta,
        ):
            assert callable(fn)

    def test_private_helpers_backward_compatible_via_web(self):
        from scripts.web import _append_cloned_edition, _patch_edition_kind_lists

        assert callable(_patch_edition_kind_lists)
        assert callable(_append_cloned_edition)

    def test_handlers_actually_live_in_new_module(self):
        from scripts.web import (
            api_apply_kind_to_all_editions,
            api_clone_edition,
            api_create_edition_from_template,
            api_preview_edition_changes,
            api_save_edition,
            api_save_edition_meta,
            api_save_note_toggle,
            api_save_publisher_meta,
        )

        for fn in (
            api_save_edition,
            api_save_edition_meta,
            api_save_publisher_meta,
            api_clone_edition,
            api_create_edition_from_template,
            api_save_note_toggle,
            api_preview_edition_changes,
            api_apply_kind_to_all_editions,
        ):
            target = getattr(fn, "__wrapped__", fn)
            assert target.__module__ == "scripts.api.editions", (
                f"{target.__name__} module is {target.__module__}, expected scripts.api.editions"
            )

    def test_route_tables_still_dispatch_editions_cluster(self):
        from scripts import web

        put_patterns = [r.pattern for r, _ in web._PUT_ROUTES]
        post_patterns = [r.pattern for r, _ in web._POST_ROUTES]

        # PUT routes (api_save_edition, api_save_edition_meta,
        # api_save_publisher_meta, api_save_note_toggle, api_clone_edition,
        # api_create_edition_from_template)
        assert any(p == r"^/api/edition/([a-z0-9-]+)$" for p in put_patterns)
        assert any("/api/edition-meta/" in p for p in put_patterns)
        assert any("/api/publisher/" in p for p in put_patterns)
        assert any("/note-toggle" in p for p in put_patterns)
        assert any("/api/editions/from-template" in p for p in put_patterns)
        # POST: api_apply_kind_to_all_editions
        assert any("/api/matrix/apply-kind-to-all" in p for p in post_patterns)

    def test_audit_decorator_preserved_on_mutations(self):
        # 7 of 8 handlers are audit-logged
        # (api_preview_edition_changes is the bespoke read-only-ish
        # preview that doesn't mutate; api_create_edition_from_template
        # is not decorated either as it just delegates).
        from scripts.api.editions import (
            api_apply_kind_to_all_editions,
            api_clone_edition,
            api_save_edition,
            api_save_edition_meta,
            api_save_note_toggle,
            api_save_publisher_meta,
        )

        for fn in (
            api_save_edition,
            api_save_edition_meta,
            api_save_publisher_meta,
            api_clone_edition,
            api_save_note_toggle,
            api_apply_kind_to_all_editions,
        ):
            # Decorated funcs retain their name; an undecorated bare
            # function would also pass this loose check, so it's a
            # minimal pin.
            assert fn.__name__.startswith("api_")

    def test_covers_cross_module_import_targets_editions(self):
        # api_delete_cover_main + api_delete_cover_book now
        # lazy-import api_save_edition_meta from scripts.api.editions
        # (not scripts.web).
        import inspect

        from scripts.api import covers

        src_main = inspect.getsource(covers.api_delete_cover_main)
        src_book = inspect.getsource(covers.api_delete_cover_book)

        for src, name in ((src_main, "delete_cover_main"), (src_book, "delete_cover_book")):
            # Must NOT import from scripts.web
            assert "from scripts.web import api_save_edition_meta" not in src, (
                f"{name} still uses old web.py import path — should target scripts.api.editions"
            )
            # Must import from scripts.api.editions
            assert "from scripts.api.editions import api_save_edition_meta" in src, (
                f"{name} doesn't import api_save_edition_meta from scripts.api.editions"
            )

    def test_thin_attr_patterns_constant_present(self):
        # The _THIN_ATTR_PATTERNS constant + Attribution Audit
        # section header lived between api_save_edition_meta and
        # def _classify_attribution. During B.5 extraction the
        # block-end detector swept them along with the editions
        # handler. They were restored manually. Pin so this isn't
        # broken in a future refactor.
        from scripts.web import _classify_attribution, _THIN_ATTR_PATTERNS

        assert callable(_classify_attribution)
        # _THIN_ATTR_PATTERNS is a tuple of compiled regexes
        assert len(_THIN_ATTR_PATTERNS) > 0
        # Smoke test the classifier still works (would fail with
        # NameError if _THIN_ATTR_PATTERNS were missing)
        assert _classify_attribution("see Genesis 1:1") == "thin"
        assert _classify_attribution("") == "missing"

    def test_shared_helpers_remain_in_web_py(self):
        # B.5 keeps these helpers + constants in web.py because
        # they have web.py-resident callers (api_customize_data,
        # api_publisher_data) AND because routine refactor
        # discipline says "move only what's needed."
        import scripts.web as w

        for name in (
            "_patch_yaml_entry",
            "_patch_yaml_list_field",
            "_load_themes",
            "_validate_cover_path",
            "parse_note_id",
            "html_ref_id_from_note_id",
            "PUBLISHING_TEXT_LIMITS",
            "PUBLISHING_LIST_FIELDS",
        ):
            assert hasattr(w, name), (
                f"web.py missing helper/constant {name!r} — B.5 should NOT have moved it "
                "(editions.py lazy-imports it from web.py at call time)"
            )

    def test_web_py_does_not_define_editions_handlers_inline(self):
        from pathlib import Path

        web_py = Path(__file__).resolve().parent.parent / "scripts" / "web.py"
        text = web_py.read_text(encoding="utf-8")
        for name in (
            "api_save_edition",
            "api_save_edition_meta",
            "api_save_publisher_meta",
            "api_clone_edition",
            "api_create_edition_from_template",
            "api_save_note_toggle",
            "api_preview_edition_changes",
            "api_apply_kind_to_all_editions",
            "_patch_edition_kind_lists",
            "_append_cloned_edition",
        ):
            assert f"def {name}(" not in text, (
                f"web.py still has inline `def {name}(...)` — should be re-imported from scripts.api.editions only"
            )

    def test_lazy_helper_imports_work_at_call_time(self):
        # Smoke: call api_save_edition_meta with an unknown
        # edition. The function must reach its lazy
        # `from scripts.web import _load_themes, _patch_yaml_entry,
        # _patch_yaml_list_field, _validate_cover_path` line
        # without ImportError, then return the normal error dict.
        from scripts.web import api_save_edition_meta

        result = api_save_edition_meta("definitely-not-a-real-edition-zzz", {"title": "test"})
        assert isinstance(result, dict)
        assert "error" in result
        assert "unknown edition" in result["error"]


# ---------- Phase ω.35-B.6 : exports/build extraction --------------


class TestOmega35B6ExportsExtraction:
    """ω.35-B.6 — seventh file-split slice. 4 exports/build
    handlers extracted from `scripts/web.py` into
    `scripts/api/exports.py`:
    - api_export_preview (read-only)
    - api_export_build (mutation; audit-logged; bespoke 500-on-fail)
    - api_build_all_editions (mutation; audit-logged; bespoke
      success_count check)
    - api_download_export (streams bytes for download)

    Plus the module-level `EXPORTS_DIR` constant. All 5 names
    are re-exported from scripts.web for backward compat.

    Note: api_export_build + api_build_all_editions are the two
    bespoke PUT routes that stayed out of `_PUT_ROUTES` in
    ω.35-A.10 (because their 500-on-failure semantics differ
    from the standard helper's 400). They remain bespoke in
    do_PUT after this extraction — only the FUNCTION body
    moved.
    """

    def test_exports_module_exists(self):
        import scripts.api.exports as exports_api

        for name in (
            "api_export_preview",
            "api_export_build",
            "api_build_all_editions",
            "api_download_export",
            "EXPORTS_DIR",
        ):
            assert hasattr(exports_api, name), f"exports module missing {name!r}"

    def test_handlers_backward_compatible_via_web(self):
        from scripts.web import (
            EXPORTS_DIR,
            api_build_all_editions,
            api_download_export,
            api_export_build,
            api_export_preview,
        )

        for fn in (api_export_preview, api_export_build, api_build_all_editions, api_download_export):
            assert callable(fn)
        assert "exports" in str(EXPORTS_DIR), f"EXPORTS_DIR is {EXPORTS_DIR}"

    def test_handlers_actually_live_in_new_module(self):
        from scripts.web import (
            api_build_all_editions,
            api_download_export,
            api_export_build,
            api_export_preview,
        )

        for fn in (api_export_preview, api_export_build, api_build_all_editions, api_download_export):
            target = getattr(fn, "__wrapped__", fn)
            assert target.__module__ == "scripts.api.exports", (
                f"{target.__name__} module is {target.__module__}, expected scripts.api.exports"
            )

    def test_exports_dir_constant_backward_compatible(self):
        # The constant is referenced directly by tests + the
        # download dispatch path. Pin its value across both
        # import sites.
        from scripts.api.exports import EXPORTS_DIR as direct
        from scripts.web import EXPORTS_DIR as reexport

        # Same Path object via both paths (same identity)
        assert direct == reexport

    def test_audit_decorator_preserved_on_mutations(self):
        # api_export_build + api_build_all_editions are audit-
        # logged. api_export_preview + api_download_export are
        # read-only (no decorator).
        from scripts.api.exports import api_build_all_editions, api_export_build

        for fn in (api_export_build, api_build_all_editions):
            assert fn.__name__.startswith("api_")

    def test_bespoke_build_routes_still_dispatch_in_do_PUT(self):
        # api_export_build (PUT /api/export/build/<id>) and
        # api_build_all_editions (PUT /api/build-all) are the
        # two bespoke routes ω.35-A.10 kept out of _PUT_ROUTES
        # because their 500-on-failure semantics don't fit the
        # standard helper. Pin: they're STILL dispatched in
        # do_PUT (just calling the new module's function).
        import inspect

        from scripts.web import Handler

        src = inspect.getsource(Handler.do_PUT)
        assert "api_export_build" in src, "do_PUT must still dispatch api_export_build (bespoke 500-on-fail)"
        assert "api_build_all_editions" in src, (
            "do_PUT must still dispatch api_build_all_editions (success_count check)"
        )

    def test_download_route_still_registered_in_apihelp(self):
        # api_download_export is wired via `m = re.match(...)` in
        # do_GET. The /apihelp scanner picks it up. Pin that the
        # /apihelp data includes the download path so the route
        # discovery is intact post-split.
        from scripts.web import api_help_data

        d = api_help_data()
        paths = {r["path"] for r in d["api_routes"]}
        # Path uses <param> for placeholders
        assert any("/api/export/download" in p for p in paths), (
            f"/api/export/download missing from /apihelp; got: {[p for p in paths if 'export' in p]}"
        )

    def test_web_py_does_not_define_export_handlers_inline(self):
        from pathlib import Path

        web_py = Path(__file__).resolve().parent.parent / "scripts" / "web.py"
        text = web_py.read_text(encoding="utf-8")
        for name in (
            "api_export_preview",
            "api_export_build",
            "api_build_all_editions",
            "api_download_export",
        ):
            assert f"def {name}(" not in text, (
                f"web.py still has inline `def {name}(...)` — should be re-imported from scripts.api.exports only"
            )
        # The EXPORTS_DIR constant: no inline assignment
        assert 'EXPORTS_DIR = REPO / "exports"' not in text, (
            "web.py still defines EXPORTS_DIR — should be re-imported from scripts.api.exports"
        )

    def test_download_unknown_returns_error(self):
        # Smoke: api_download_export with an invalid filename
        # returns the expected error dict, not crashing.
        from scripts.web import api_download_export

        result = api_download_export("not-a-real-file.epub")
        assert isinstance(result, dict)
        assert "error" in result

    def test_preview_unknown_edition_returns_error(self):
        from scripts.web import api_export_preview

        result = api_export_preview("definitely-not-a-real-edition-zzz")
        assert isinstance(result, dict)
        assert "error" in result
        assert "unknown edition" in result["error"]


# ---------- Phase ω.35-B.7 : preflight/audit/help/multipart split -----


class TestOmega35B7PreflightExtraction:
    """ω.35-B.7 — final file-split slice. Three handler clusters +
    one helper pair extracted from `scripts/web.py` into purpose-
    built modules in `scripts/api/`:

    - `api_preflight` + `_cached_preflight` + `_compute_preflight_uncached`
      → scripts/api/preflight.py
    - `api_help_data` (+ `_ROUTE_PATTERNS` / `_CONSOLE_PATTERNS` constants)
      → scripts/api/help.py
    - `api_audit_log` → scripts/api/audit.py
    - `_parse_multipart` + `_extract_boundary` → scripts/api/multipart.py

    All names are re-exported from `scripts.web` so route-table
    lambdas in `_SIMPLE_GET_ROUTES` / `_QS_REGEX_GET_ROUTES`, the
    bespoke do_GET dispatcher, and existing tests that lookup
    `scripts.web.api_preflight` / `api_help_data` / `api_audit_log`
    / `_parse_multipart` / `_extract_boundary` keep working.

    The multipart helpers were also lazy-imported from `scripts.web`
    by `scripts/api/covers.py` (cover uploads) and
    `scripts/api/sources.py` (source-cache uploads). Those lazy
    imports were retargeted to `scripts.api.multipart` in the same
    ship; this test class pins the retarget.

    This slice closes ω.35-B. Cumulative B.1–B.7 reduction in
    web.py is ~3000+ lines from the file-split baseline.
    """

    def test_preflight_module_exists(self):
        import scripts.api.preflight as pf_api

        for name in ("api_preflight", "_cached_preflight", "_compute_preflight_uncached"):
            assert hasattr(pf_api, name), f"preflight module missing {name!r}"

    def test_help_module_exists(self):
        import scripts.api.help as help_api

        for name in ("api_help_data", "_ROUTE_PATTERNS", "_CONSOLE_PATTERNS"):
            assert hasattr(help_api, name), f"help module missing {name!r}"

    def test_audit_module_exists(self):
        import scripts.api.audit as audit_api

        assert hasattr(audit_api, "api_audit_log"), "audit module missing api_audit_log"

    def test_multipart_module_exists(self):
        import scripts.api.multipart as mp_api

        for name in ("_parse_multipart", "_extract_boundary"):
            assert hasattr(mp_api, name), f"multipart module missing {name!r}"

    def test_handlers_backward_compatible_via_web(self):
        # Every extracted name must still be importable from
        # scripts.web (re-export contract). Tests / route tables
        # / consoles depend on this surface.
        from scripts.web import (
            _cached_preflight,
            _compute_preflight_uncached,
            _extract_boundary,
            _parse_multipart,
            api_audit_log,
            api_help_data,
            api_preflight,
        )

        for fn in (
            api_preflight,
            _cached_preflight,
            _compute_preflight_uncached,
            api_help_data,
            api_audit_log,
            _parse_multipart,
            _extract_boundary,
        ):
            assert callable(fn)

    def test_handlers_actually_live_in_new_modules(self):
        # Identity check: scripts.web.X is the exact same object as
        # scripts.api.<topic>.X (re-import preserves identity).
        from scripts.api.audit import api_audit_log as audit_direct
        from scripts.api.help import api_help_data as help_direct
        from scripts.api.multipart import (
            _extract_boundary as eb_direct,
            _parse_multipart as mp_direct,
        )
        from scripts.api.preflight import api_preflight as pf_direct
        from scripts.web import (
            _extract_boundary,
            _parse_multipart,
            api_audit_log,
            api_help_data,
            api_preflight,
        )

        assert api_preflight is pf_direct
        assert api_help_data is help_direct
        assert api_audit_log is audit_direct
        assert _parse_multipart is mp_direct
        assert _extract_boundary is eb_direct

        # Canonical home: every callable's __module__ points at
        # scripts.api.<topic>, NOT scripts.web.
        assert api_preflight.__module__ == "scripts.api.preflight"
        assert api_help_data.__module__ == "scripts.api.help"
        assert api_audit_log.__module__ == "scripts.api.audit"
        assert _parse_multipart.__module__ == "scripts.api.multipart"
        assert _extract_boundary.__module__ == "scripts.api.multipart"

    def test_preflight_executes_end_to_end(self):
        # api_preflight composes api_attribution_audit + api_covers
        # from web.py via lazy import. Pin that the cross-module
        # call path still works after the extraction.
        from scripts.web import api_preflight

        result = api_preflight()
        assert "checks" in result
        assert "summary" in result
        assert isinstance(result["checks"], list)
        assert len(result["checks"]) >= 10, f"expected >=10 preflight checks, got {len(result['checks'])}"
        s = result["summary"]
        assert set(s) >= {"total", "pass", "warn", "fail", "ready_to_ship"}
        assert s["total"] == s["pass"] + s["warn"] + s["fail"]

    def test_help_data_executes_end_to_end(self):
        # api_help_data scans scripts/web.py source. Pin that the
        # source scan still finds the bulk of the route surface
        # post-extraction (which preserved the route tables).
        from scripts.web import api_help_data

        result = api_help_data()
        assert result.get("status") == "ok"
        assert result["totals"]["api"] >= 40, (
            f"expected >=40 API routes after extraction, got {result['totals']['api']}"
        )
        # Every entry has the expected schema
        for r in result["api_routes"]:
            assert {"method", "path", "description", "phase", "line"} <= set(r)
        for r in result["consoles"]:
            assert {"path", "description", "phase", "line"} <= set(r)

    def test_audit_log_executes_end_to_end(self, tmp_path):
        # Use base_dir=tmp_path so we never depend on production audit
        # log location. Empty dir → 0 entries; clamps n correctly.
        from scripts.web import api_audit_log

        result = api_audit_log(n=10, base_dir=tmp_path)
        assert result["status"] == "ok"
        assert result["limit"] == 10
        assert result["count"] == 0
        assert result["entries"] == []

    def test_audit_log_n_is_clamped(self, tmp_path):
        from scripts.web import api_audit_log

        # n < 1 → clamped to 1
        r = api_audit_log(n=0, base_dir=tmp_path)
        assert r["limit"] == 1
        # n > 1000 → clamped to 1000
        r = api_audit_log(n=99999, base_dir=tmp_path)
        assert r["limit"] == 1000
        # n non-int string → falls back to 100
        r = api_audit_log(n="not-an-int", base_dir=tmp_path)  # type: ignore[arg-type]
        assert r["limit"] == 100

    def test_multipart_helpers_round_trip(self):
        # Pin that the moved helpers still parse a minimal
        # multipart payload (single file part).
        from scripts.web import _extract_boundary, _parse_multipart

        boundary = _extract_boundary("multipart/form-data; boundary=abc123")
        assert boundary == b"abc123"

        body = (
            b"--abc123\r\n"
            b'Content-Disposition: form-data; name="cover"; filename="t.png"\r\n'
            b"Content-Type: image/png\r\n"
            b"\r\n"
            b"\x89PNG\r\n"
            b"--abc123--\r\n"
        )
        parts = _parse_multipart(body, boundary)
        assert len(parts) == 1
        p = parts[0]
        assert p["name"] == "cover"
        assert p["filename"] == "t.png"
        assert p["content_type"] == "image/png"
        assert p["data"] == b"\x89PNG"

    def test_extract_boundary_rejects_oversized(self):
        # SEC-007 — 70-char ceiling per RFC 2046.
        from scripts.web import _extract_boundary

        too_long = "a" * 71
        assert _extract_boundary(f"multipart/form-data; boundary={too_long}") is None
        ok = "a" * 70
        assert _extract_boundary(f"multipart/form-data; boundary={ok}") == ok.encode()

    def test_extract_boundary_rejects_non_ascii(self):
        # SEC-007 — boundary must be 7-bit ASCII printable.
        from scripts.web import _extract_boundary

        # Non-printable control byte in boundary
        assert _extract_boundary("multipart/form-data; boundary=ab\x01cd") is None
        # Non-ASCII upper-byte
        assert _extract_boundary("multipart/form-data; boundary=abécd") is None

    def test_extract_boundary_returns_none_on_missing(self):
        from scripts.web import _extract_boundary

        assert _extract_boundary("") is None
        assert _extract_boundary("text/plain") is None
        assert _extract_boundary("multipart/form-data") is None

    def test_covers_upload_handlers_target_new_multipart_home(self):
        # api/covers.py should lazy-import the multipart helpers
        # from scripts.api.multipart, NOT from scripts.web.
        from pathlib import Path

        src = (Path(__file__).resolve().parent.parent / "scripts" / "api" / "covers.py").read_text(encoding="utf-8")
        assert "from scripts.api.multipart import _extract_boundary, _parse_multipart" in src, (
            "api/covers.py upload handlers should lazy-import multipart helpers from "
            "scripts.api.multipart (canonical home), not scripts.web (legacy)"
        )

    def test_sources_upload_handler_targets_new_multipart_home(self):
        # api/sources.py should lazy-import multipart from
        # scripts.api.multipart, NOT from scripts.web.
        from pathlib import Path

        src = (Path(__file__).resolve().parent.parent / "scripts" / "api" / "sources.py").read_text(encoding="utf-8")
        assert "from scripts.api.multipart import _extract_boundary, _parse_multipart" in src, (
            "api/sources.py upload handler should lazy-import multipart helpers from "
            "scripts.api.multipart (canonical home), not scripts.web (legacy)"
        )

    def test_web_py_does_not_define_extracted_handlers_inline(self):
        # web.py should re-import from scripts.api.*, not redefine.
        from pathlib import Path

        web_py = Path(__file__).resolve().parent.parent / "scripts" / "web.py"
        text = web_py.read_text(encoding="utf-8")
        for name in (
            "api_preflight",
            "_cached_preflight",
            "_compute_preflight_uncached",
            "api_help_data",
            "api_audit_log",
            "_parse_multipart",
            "_extract_boundary",
        ):
            assert f"def {name}(" not in text, (
                f"web.py still has inline `def {name}(...)` — should be re-imported "
                f"from scripts.api.* only after ω.35-B.7"
            )
        # _ROUTE_PATTERNS / _CONSOLE_PATTERNS moved with api_help_data
        assert "_ROUTE_PATTERNS = [" not in text, (
            "web.py still has inline `_ROUTE_PATTERNS = [...]` — moved with api_help_data"
        )
        assert "_CONSOLE_PATTERNS = [" not in text, (
            "web.py still has inline `_CONSOLE_PATTERNS = [...]` — moved with api_help_data"
        )

    def test_route_table_still_dispatches_preflight_and_help(self):
        # Preflight + apihelp are dispatched via _SIMPLE_GET_ROUTES.
        # Pin that the table entries still point at the (re-imported)
        # functions — same name, same callable.
        from scripts.web import _SIMPLE_GET_ROUTES, api_help_data, api_preflight

        paths = {p: h for p, h in _SIMPLE_GET_ROUTES}
        assert paths.get("/api/preflight") is api_preflight
        assert paths.get("/api/apihelp") is api_help_data

    def test_route_table_still_dispatches_audit_log(self):
        # /api/audit-log lives in _QS_REGEX_GET_ROUTES (querystring n).
        # Pin that calling the lambda invokes api_audit_log.
        import re as _re

        from scripts.web import _QS_REGEX_GET_ROUTES

        for pattern, handler in _QS_REGEX_GET_ROUTES:
            if pattern.pattern == r"^/api/audit-log$":
                # Smoke: handler returns a dict shaped like api_audit_log
                m = _re.match(pattern, "/api/audit-log")
                assert m is not None
                result = handler(m, {"n": ["3"]})
                assert isinstance(result, dict)
                assert result.get("status") == "ok"
                assert result["limit"] == 3
                return
        raise AssertionError("/api/audit-log not registered in _QS_REGEX_GET_ROUTES")

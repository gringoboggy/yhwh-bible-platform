#!/usr/bin/env python3
"""
web.py — Local web UI for editing the YHWH Ya' Way note corpus.

Lightweight HTTP server (stdlib only — no Flask, no install) that exposes
content/notes/<code>.py as a browsable, editable list. Per-note edits go
through atomic_write + ensure_backup, so the UI is just a thin layer over
the same primitives the CLI uses.

Run:
    ebible web                       # default localhost:8765
    ebible web --port 9000
    ebible web --host 0.0.0.0        # bind LAN-wide (use carefully)

Then open http://localhost:8765/ in a browser.

Capabilities:
  * Browse books — counts per kind shown.
  * List + filter notes within a book (by kind, by quality status).
  * Edit one note at a time with live HTML preview + word-count budget
    feedback against the per-kind budget from note_quality.py.
  * Add new notes via the per-kind templates from new_note.py.
  * Delete a note (creates a .backup before mutating).
  * Per-edit feedback: opener detection, presentational-tag warnings,
    word-count vs kind budget.

Architecture:
  - JSON API at /api/* for all data operations.
  - Single-page HTML at / (no build step, vanilla JS, Tailwind via CDN).
  - File mutations always go through scripts.core.notes_io helpers.

Concurrency:
  - ThreadingHTTPServer; each request is independent.
  - File writes are atomic (rename) so partial-write corruption is impossible.
  - Last-write-wins for concurrent edits in different tabs.

This server intentionally binds to localhost by default so the corpus is
not exposed without conscious opt-in via --host.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.core.covers import UPLOAD_MAX_BYTES as COVERS_UPLOAD_MAX_BYTES  # noqa: E402  # ω.35-A.9

# REPO + NOTES_DIR are defined once in web_helpers (bottom of the import
# DAG) and re-exported here so `scripts.web.REPO` / `scripts.web.NOTES_DIR`
# keep resolving for external callers + tests.
from scripts.web_helpers import NOTES_DIR, REPO  # noqa: E402, F401

SCENARIOS_DIR = REPO / "content" / "scenarios"


# ============================================================
# Module-level route functions + helpers — moved into focused
# scripts/web_*.py modules in the god-module split (2026-05-26).
# Re-exported here (noqa: F401) so (a) the route-table data
# structures below resolve the api_* names in this module's
# namespace, and (b) external importers + tests keep working
# unchanged (both `from scripts import web; web.X` and
# `from scripts.web import X`). web_helpers sits at the bottom of
# the import DAG; the domain modules import from it one-directionally.
# ============================================================
from scripts.web_helpers import (  # noqa: E402, F401
    _canons_index,
    _files_signature,
    _load_new_note_helpers,
    _load_note_quality_helpers,
    _nn,
    _notes_dir_signature,
    _nq,
    _patch_yaml_entry,
    _patch_yaml_list_field,
    _yaml_escape,
    dict_to_tuple,
    html_ref_id_from_note_id,
    note_id_from_tuple,
    parse_note_id,
    quality_for,
    tuple_to_dict,
    write_book,
)
from scripts.web_notes import (  # noqa: E402, F401
    api_books,
    api_delete,
    api_kinds,
    api_notes,
    api_preview,
    api_save,
    api_search_notes,
    api_template,
)
from scripts.web_matrix import (  # noqa: E402, F401
    _api_matrix_per_edition,
    _cached_edition_diff,
    _compute_edition_diff_uncached,
    _diff_books_section,
    _diff_categories_section,
    _diff_edition_summary,
    _diff_headline,
    _diff_kinds_section,
    api_edition_diff,
    api_matrix,
    api_matrix_for_edition,
)
from scripts.web_editions import (  # noqa: E402, F401
    _decode_traditions_per_book_for_api,
    _filter_traditions_default,
    _load_themes,
    _reading_plans_summary_for_api,
    _traditions_canonical_for_api,
    api_build_my_bible,
    api_build_tracker,
    api_build_tracker_book,
    api_customize_data,
    api_disabled_notes_for_edition,
    api_edition_templates_list,
    api_reading_plan_get,
    api_reading_plans_list,
)
from scripts.web_covers import (  # noqa: E402, F401
    _cached_covers,
    _compute_covers_uncached,
    _save_cover_bytes,
    _validate_cover_path,
    api_covers,
)
from scripts.web_sources import (  # noqa: E402, F401
    PUBLISHING_DEFAULTS,
    PUBLISHING_LIST_FIELDS,
    PUBLISHING_TEXT_LIMITS,
    _cached_attribution_audit,
    _cached_publisher_data,
    _classify_attribution,
    _compute_attribution_audit_uncached,
    _compute_publisher_data_uncached,
    _THIN_ATTR_PATTERNS,
    api_attribution_audit,
    api_publisher_data,
    api_sources_for_book,
    api_sources_index,
    api_sources_summary,
)
from scripts.web_content import (  # noqa: E402, F401
    CORPUS_TARGET,
    _BACKUP_FILENAME_RE,
    _PROCESS_START_TIME,
    _render_sample_html,
    _resolve_content_path,
    api_compare,
    api_corpus_progress,
    api_dev_templates_mtime,
    api_list_backups,
    api_ops_dashboard,
    api_restore_backup,
    api_sample_html,
)
from scripts.web_misc import (  # noqa: E402, F401
    _safe_rss_base_url,
    api_onboarding_complete,
    api_onboarding_state,
    api_verse_of_day,
    api_verse_of_day_rss,
)


# ============================================================
# API handlers extracted to scripts/api/<topic>.py — re-imported here
# so route-table lambdas + tests that reference scripts.web.api_X (and
# the upload-size constants) keep working unchanged. These are the
# pre-existing ω.35-B / earlier splits; the names land in this module's
# namespace exactly as before.
# ============================================================
from scripts.api.editions import (  # noqa: E402, F401
    _append_cloned_edition as _append_cloned_edition,
    _patch_edition_kind_lists as _patch_edition_kind_lists,
    api_apply_kind_to_all_editions,
    api_clone_edition,
    api_create_edition_from_template,
    api_preview_edition_changes,
    api_save_edition,
    api_save_edition_meta,
    api_save_note_override,
    api_save_note_toggle,
    api_save_publisher_meta,
)
from scripts.api.snapshots import (  # noqa: E402, F401
    api_snapshot_create,
    api_snapshot_delete,
    api_snapshot_diff,
    api_snapshot_get,
    api_snapshot_list,
    api_snapshot_restore,
)
from scripts.api.scenarios import (  # noqa: E402, F401
    _resolve_scenario_recipe as _resolve_scenario_recipe,  # internal helper, used by some tests
    _scenario_path as _scenario_path,  # internal helper, used by some tests
    _SCENARIO_NAME_RE as _SCENARIO_NAME_RE,  # constant, used by some tests
    api_delete_scenario,
    api_export_scenario_yaml,
    api_get_scenario,
    api_import_scenario_yaml,
    api_list_scenarios,
    api_save_scenario,
)
from scripts.api.sources import (  # noqa: E402, F401
    _datetime_iso as _datetime_iso,
    _sources_cache_dir as _sources_cache_dir,
    api_sources_cache_clear,
    api_sources_cache_fetch,
    api_sources_cache_fetch_all,
    api_sources_cache_status,
    api_sources_cache_upload,
    SOURCES_UPLOAD_MAX_BYTES,
)
from scripts.api.exports import (  # noqa: E402, F401
    EXPORTS_DIR as EXPORTS_DIR,
    api_build_all_editions,
    api_download_export,
    api_export_build,
    api_export_preview,
)
from scripts.core import build_gate  # noqa: E402 — W4.2 build cap
from scripts.api.customize import (  # noqa: E402, F401
    api_save_category,
    api_save_kind,
)
from scripts.api.preflight import (  # noqa: E402, F401
    _cached_preflight as _cached_preflight,
    _compute_preflight_uncached as _compute_preflight_uncached,
    api_preflight,
)
from scripts.api.multipart import (  # noqa: E402, F401
    _extract_boundary as _extract_boundary,
    _parse_multipart as _parse_multipart,
)
from scripts.api.covers import (  # noqa: E402, F401
    api_apply_cover_template,
    api_delete_cover_book,
    api_delete_cover_main,
    api_upload_cover_book,
    api_upload_cover_main,
)
from scripts.api.help import api_help_data  # noqa: E402, F401
from scripts.api.audit import api_audit_log  # noqa: E402, F401


# Phase ψ.3 — corpus progress widget. Tunable goal in one place; the
# /api/corpus-progress endpoint returns the structured payload that
# the every-console widget renders. Driven off the existing
# attribution-audit total (which already counts every note across
# every per-book file), so no new computation is introduced.
# Phase ω.0.6 — UI defense prelude. Four tiers of frontend
# robustness, mirroring the backend §15 chain-of-command. Injected
# into every console's <body> close so it runs once after page
# load. Order of definition is intentional: Tier 4 (global error
# backstop) installs first so it can catch any failures from
# Tier 2 / 3 themselves; Tier 2 (safeFetch) and Tier 3 (safe$/$$)
# are available to console-specific code that imports the page.
#
# Why a single shared constant: all 10 consoles need identical
# defensive scaffolding. Inlining the same ~80 lines into each
# template would drift; one constant + bulk-inject = one source
# of truth. Same pattern as the corpus-progress widget (ψ.3).
UI_DEFENSE_PRELUDE = r"""
<!-- ω.0.6 — UI defense prelude — START -->
<!-- Re-injecting / refreshing this block uses
     scripts/bulk_inject.py replace --open-marker "ω.0.6 — UI defense prelude — START"
     ...                          --close-marker "ω.0.6 — UI defense prelude — END"
     The markers are stable contracts; do not change without a coordinated migration. -->
<script>
(function () {
  'use strict';

  // -------------------------------------------------------------------
  // Tier 4 — Global error backstop. Catches anything that escapes
  // the other tiers (null-pointer accesses, unhandled rejections,
  // syntax errors in inline scripts) and shows a soft red banner
  // instead of leaving the page frozen.
  // -------------------------------------------------------------------

  function ensureErrorBanner() {
    var banner = document.getElementById('ebible-error-banner');
    if (banner) return banner;
    banner = document.createElement('div');
    banner.id = 'ebible-error-banner';
    banner.setAttribute('role', 'alert');
    banner.setAttribute('aria-live', 'polite');
    banner.style.cssText =
      'position:fixed;top:0;left:0;right:0;z-index:9999;' +
      'background:#dc2626;color:#fff;padding:8px 16px;font-size:13px;' +
      'font-family:system-ui,sans-serif;display:none;' +
      'box-shadow:0 2px 4px rgba(0,0,0,0.1)';
    banner.innerHTML =
      '<div style="max-width:72rem;margin:0 auto;display:flex;' +
      'align-items:center;justify-content:space-between;gap:12px">' +
      '<span class="ebible-error-text" style="flex:1;min-width:0;' +
      'overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span>' +
      '<button type="button" class="ebible-error-dismiss" ' +
      'style="background:none;border:1px solid rgba(255,255,255,0.4);' +
      'color:#fff;padding:2px 10px;border-radius:4px;cursor:pointer;' +
      'font-size:12px">Dismiss</button></div>';
    if (document.body) {
      document.body.appendChild(banner);
    } else {
      document.addEventListener('DOMContentLoaded', function () {
        document.body.appendChild(banner);
      });
    }
    banner.querySelector('.ebible-error-dismiss')
      .addEventListener('click', function () { banner.style.display = 'none'; });
    return banner;
  }

  function showErrorBanner(message) {
    try {
      var banner = ensureErrorBanner();
      var text = banner.querySelector('.ebible-error-text');
      if (text) text.textContent = message;
      banner.style.display = 'block';
    } catch (e) {
      // If even the banner fails, log to console as last resort
      try { console.error('[ebible] error banner failed:', e, message); }
      catch (_) {}
    }
  }

  // Install global error handlers
  window.addEventListener('error', function (ev) {
    var msg = (ev && ev.message) ? ev.message : 'Script error';
    // Filter out "Script error." with no info — usually cross-origin
    // loaded resources, nothing actionable for us
    if (msg === 'Script error.') return;
    showErrorBanner('Something went wrong: ' + msg);
    try { console.error('[ebible global error]', ev.error || msg); }
    catch (_) {}
  });
  window.addEventListener('unhandledrejection', function (ev) {
    var reason = ev && ev.reason;
    var msg = (reason && reason.message) ? reason.message : String(reason);
    showErrorBanner('Background task failed: ' + msg);
    try { console.error('[ebible unhandled rejection]', reason); }
    catch (_) {}
  });

  // -------------------------------------------------------------------
  // Tier 2 — safeFetch wrapper. Standard helper for every API call.
  // Throws on non-OK status, parses JSON safely, surfaces failures
  // via the banner. Re-throws so callers can do feature-specific
  // handling on top.
  // -------------------------------------------------------------------

  async function safeFetch(url, opts) {
    opts = opts || {};
    let response;
    try {
      response = await fetch(url, opts);
    } catch (netErr) {
      // Network drop, DNS fail, fetch aborted, etc.
      const msg = (netErr && netErr.message) ? netErr.message : 'network error';
      showErrorBanner('Network error: ' + msg + ' (' + url + ')');
      throw netErr;
    }
    if (!response.ok) {
      let errMsg = response.status + ' ' + response.statusText;
      try {
        const text = await response.text();
        if (text) {
          try {
            const parsed = JSON.parse(text);
            if (parsed && parsed.error) errMsg = parsed.error;
          } catch (_) {
            // Not JSON; use text snippet
            errMsg = text.slice(0, 200);
          }
        }
      } catch (_) {}
      showErrorBanner('API ' + response.status + ': ' + errMsg);
      const err = new Error(errMsg);
      err.status = response.status;
      throw err;
    }
    // Parse response. If empty body, return null (DELETE often is).
    const text = await response.text();
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch (parseErr) {
      showErrorBanner('Server returned invalid JSON from ' + url);
      throw parseErr;
    }
  }

  // -------------------------------------------------------------------
  // Tier 3 — DOM null-safe helpers. querySelector / querySelectorAll
  // wrappers that don't throw on missing elements. Opt-in: existing
  // code keeps working; new code can adopt these.
  // -------------------------------------------------------------------

  function safe$(selector, parent) {
    try {
      return (parent || document).querySelector(selector);
    } catch (e) {
      // Invalid selector syntax → log and return null instead of crash
      try { console.warn('[safe$] invalid selector:', selector, e); }
      catch (_) {}
      return null;
    }
  }

  function safe$$(selector, parent) {
    try {
      return Array.from((parent || document).querySelectorAll(selector));
    } catch (e) {
      try { console.warn('[safe$$] invalid selector:', selector, e); }
      catch (_) {}
      return [];
    }
  }

  // -------------------------------------------------------------------
  // ω.0.7 — Shared escape helpers. Eleven separate definitions of
  // essentially the same HTML-escaping logic existed across the
  // consoles before this consolidation. New code should use
  // window.ebible.escapeHtml (or the bare alias). Existing call
  // sites can migrate incrementally.
  // -------------------------------------------------------------------

  var ESCAPE_HTML_MAP = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  };

  function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, function (c) {
      return ESCAPE_HTML_MAP[c] || c;
    });
  }

  // -------------------------------------------------------------------
  // Public surface — attach to window.ebible namespace
  // -------------------------------------------------------------------

  window.ebible = window.ebible || {};
  window.ebible.showErrorBanner = showErrorBanner;
  window.ebible.safeFetch = safeFetch;
  window.ebible.safe$ = safe$;
  window.ebible.safe$$ = safe$$;
  window.ebible.escapeHtml = escapeHtml;
  // Convenience aliases for less typing in inline scripts
  window.safeFetch = safeFetch;
  window.safe$ = safe$;
  window.safe$$ = safe$$;
  window.escapeHtml = escapeHtml;
})();
</script>
<!-- ω.0.6 — UI defense prelude — END -->
"""


# ω.0.8 — web.py split refactor: HTML constants moved to
# scripts/templates/<name>.py during the 2026-05-07 split.
# These imports preserve back-compat with existing
# `from scripts.web import <NAME>_HTML` callers.
from scripts.templates.apihelp import APIHELP_HTML
from scripts.templates.audit import AUDIT_HTML
from scripts.templates.audit_log import AUDIT_LOG_HTML
from scripts.templates.compare import COMPARE_HTML
from scripts.templates.covers import COVERS_HTML
from scripts.templates.customize import CUSTOMIZE_HTML
from scripts.templates.diff import DIFF_HTML
from scripts.templates.distribution import DISTRIBUTION_HTML
from scripts.templates.export import EXPORT_HTML
from scripts.templates.greek import GREEK_HTML
from scripts.templates.hebrew import HEBREW_HTML
from scripts.templates.index import INDEX_HTML
from scripts.templates.matrix import MATRIX_HTML
from scripts.templates.build_tracker import BUILD_TRACKER_HTML
from scripts.templates.build_my_bible import BUILD_MY_BIBLE_HTML
from scripts.templates.ops import OPS_HTML
from scripts.templates.preflight import PREFLIGHT_HTML
from scripts.templates.publisher import PUBLISHER_HTML
from scripts.templates.sources import SOURCES_HTML
from scripts.templates.wizard import WIZARD_HTML

# γ.1 / γ.2 — interlinear lookup APIs.
from scripts.api.greek import api_greek_lookup
from scripts.api.hebrew import api_hebrew_lookup

from scripts.api.press_kit import (
    api_press_kit_get,
    api_press_kit_save,
    build_press_kit_zip,
)
from scripts.api.archive_org import (
    api_archive_org_status,
    api_archive_org_upload,
)
from scripts.api.distribution import api_distribution_rollup
from scripts.api.auth import (
    api_auth_status,
    api_auth_totp_begin,
    api_auth_totp_confirm,
    api_auth_totp_disable,
)
# ============================================================
# HTTP handler
# ============================================================


def _safe_request(method):
    """Phase ω.8 — top-level error boundary for do_* request methods.
    Any uncaught Exception becomes a 500 JSON response instead of a
    stack trace dumped to the response stream. Per-endpoint handlers
    still catch their own expected errors with appropriate 4xx codes;
    this wrapper is the safety net for genuinely unexpected
    conditions (Python bugs, OS errors, etc.).

    Used as a decorator on Handler.do_GET / do_POST / do_PUT /
    do_DELETE."""

    def wrapper(self):
        try:
            return method(self)
        except Exception as e:
            return self._send_unhandled_error(e, method.__name__)

    wrapper.__name__ = method.__name__
    wrapper.__wrapped__ = method
    return wrapper


# ω.35-A.1 (2026-05-11) — table-driven dispatch for the simplest GET
# routes (the `if path == "/api/X": return self._send_json(api_X())`
# shape that dominated the do_GET cascade). The Handler.do_GET method
# checks this table FIRST; falls through to the legacy if/elif
# cascade for routes that don't fit the simple shape (auth-gated,
# payload-reading, multipart parsing, custom error translation).
#
# **Migration strategy:** the migrated branches REMAIN in the legacy
# if/elif as dead code. The table dispatch returns first, so those
# branches are unreachable but still picked up by the ω.35-A
# `check_routes.py` drift linter (which discovers routes by regex-
# scanning do_GET). Future ω.35-A.2 cleanup will delete the dead
# branches once the table dispatch is proven across a full release
# cycle. For now, dead-code preservation = safety net + zero linter
# delta.
#
# **What qualifies for the table:** routes that are (a) GET, (b) no
# admin auth, (c) no payload reading, (d) no querystring parsing
# beyond what the handler does internally, (e) the response is a
# bare `_send_json(api_X())` with no error-translation logic. Any
# route that needs more inline logic stays in the legacy cascade.
#
# Routes are migrated as `(path, handler_callable)` tuples. The
# handlers are the existing pure-function `api_*` helpers — no
# changes to handler signatures or call patterns.


_SIMPLE_GET_ROUTES: list[tuple[str, object]] = [
    # W4.3 — onboarding state (read-only first-run check for the welcome flow).
    ("/api/onboarding", api_onboarding_state),
    ("/api/books", api_books),
    ("/api/kinds", api_kinds),
    ("/api/matrix", api_matrix),
    ("/api/reading-plans", api_reading_plans_list),
    ("/api/scenarios", api_list_scenarios),
    ("/api/sources", api_sources_index),
    ("/api/customize", api_customize_data),
    ("/api/publisher", api_publisher_data),
    ("/api/covers", api_covers),
    ("/api/preflight", api_preflight),
    ("/api/ops", api_ops_dashboard),
    ("/api/apihelp", api_help_data),
    ("/api/corpus-progress", api_corpus_progress),
    ("/api/edition-templates", api_edition_templates_list),
    # ω.39 — dev-side template mtime probe for THEME_HOTRELOAD_JS.
    ("/api/dev/templates-mtime", api_dev_templates_mtime),
    # ο.4 — archive.org configuration status (does the publisher have
    # credentials set yet?). Never touches the network.
    ("/api/archive-org/status", api_archive_org_status),
    # ξ.21 — admin-auth + 2FA enrollment status (read-only; never
    # reveals the secret).
    ("/api/auth/status", api_auth_status),
]


# ω.35-A.2 (2026-05-11) — second slice of the route-table migration.
# `_REGEX_GET_ROUTES` covers the next-simplest GET shape: parameterized
# paths with the boilerplate "regex.match → handler(*groups) →
# if result.get('status') == 'error': error-translate → else
# send_json(result)" pattern that appears 10+ times in the legacy
# cascade. Order matters here — table iteration is sequential and
# more-specific patterns MUST precede less-specific ones (e.g.
# `/api/snapshots/<ed>/<ver>` before `/api/snapshots/<ed>`). Same
# migration contract as ω.35-A.1: dispatch loop in do_GET checks
# this table after `_SIMPLE_GET_ROUTES` and before the legacy
# if/elif; migrated branches stay in legacy as dead code; the drift
# linter dedups so the route count is preserved.
#
# Qualifying criteria for this table:
#   - GET method
#   - No admin auth gate
#   - No querystring parsing (paths that need querystring stay in
#     legacy until ω.35-A.4 adds a query-aware table)
#   - Handler takes the regex capture groups as positional args
#   - Response is `_send_json(result)` with the standard
#     "if status == 'error', translate to HTTP error" dance
_REGEX_GET_ROUTES: list[tuple[re.Pattern, object]] = [
    (re.compile(r"^/api/reading-plans/([a-z0-9_-]+)$"), api_reading_plan_get),
    # Snapshots: order matters — /<ed>/<ver> must precede /<ed>
    (re.compile(r"^/api/snapshots/([a-z0-9._-]+)/([a-z0-9._-]+)$"), api_snapshot_get),
    (re.compile(r"^/api/snapshots/([a-z0-9._-]+)$"), api_snapshot_list),
    # ψ.36-A: per-edition matrix slice (lazy-load endpoint).
    (re.compile(r"^/api/matrix/edition/([a-z0-9_-]+)$"), api_matrix_for_edition),
    # Ω.0 (2026-05-14): /build-tracker feed. Two endpoints — counts
    # only (fast) and per-book note titles (lazy on details open).
    # Order matters — the more-specific 2-group pattern precedes the
    # 1-group pattern (regex table is sequential).
    (re.compile(r"^/api/build-tracker/([a-z0-9_-]+)/([a-z0-9_-]+)$"), api_build_tracker_book),
    (re.compile(r"^/api/build-tracker/([a-z0-9_-]+)$"), api_build_tracker),
    # ρ.3 Phase C2-1 — /api/build-my-bible/<ed>[/<book>[/<ch>]]:
    # 3-level lazy drill-down API for the /build-my-bible navigator.
    # One combined regex; the lambda receives all 3 groups from
    # `handler(*m.groups())` (optional groups return None when absent)
    # and calls api_build_my_bible with the appropriate optional args.
    (
        re.compile(r"^/api/build-my-bible/([a-z0-9-]+)(?:/([a-z0-9]+))?(?:/(\d+))?$"),
        lambda ed, bk, ch: api_build_my_bible(ed, book=bk or None, chapter=int(ch) if ch else None),
    ),
    # γ.1: Strong's Hebrew lookup. Accepts 'H1' / 'h1' / '1' /
    # 'H0001' — the handler normalizes.
    (re.compile(r"^/api/hebrew/([Hh]?\d+)$"), api_hebrew_lookup),
    # γ.2: Strong's Greek lookup. Parallel to γ.1; G-prefix.
    (re.compile(r"^/api/greek/([Gg]?\d+)$"), api_greek_lookup),
    # ε.7 — /api/press-kit/<edition> — per-edition blurbs + cover-
    # present flag + field limits. The /download companion lives in
    # the legacy cascade because it returns binary (ZIP) bytes.
    (re.compile(r"^/api/press-kit/([a-z0-9-]+)$"), api_press_kit_get),
    # mint-6 — distribution rollup. In the REGEX table (not _SIMPLE_GET_ROUTES)
    # so its {status:error, http} envelope is translated by _dispatch_table_result
    # (the simple table always sends 200). No capture groups → lambda *_ absorbs.
    (re.compile(r"^/api/distribution/rollup$"), lambda *_: api_distribution_rollup()),
]


# ω.35-A.4 (2026-05-11) — third slice of the route-table migration.
# `_QS_REGEX_GET_ROUTES` covers GET routes that need to parse the
# URL's querystring before calling their handler. The legacy
# cascade had this shape inlined 6+ times:
#
#   qs = urllib.parse.parse_qs(url.query or "")
#   arg = (qs.get("name") or ["default"])[0]
#   ...
#   result = api_X(group1, group2, kwarg=arg)
#   return self._send_json(result)   # or with error-translate
#
# The table represents each route as `(regex, handler_with_qs)`
# where `handler_with_qs` is `Callable[[Match, dict[str, list[str]]], dict]`
# — takes the regex match and the parsed qs dict, returns the
# response dict. Most entries use a small `lambda m, qs: api_X(...)`
# to keep the per-route boilerplate visible.
#
# Same dispatch contract as `_REGEX_GET_ROUTES`: order = precedence
# (more-specific patterns first), runs through
# `_dispatch_table_result` for the standard error-translation
# envelope, migrated branches deleted from legacy via ω.35-A.3-style
# cleanup once the table is proven.
_QS_REGEX_GET_ROUTES: list[tuple[re.Pattern, object]] = [
    # /api/snapshots/<ed>/<ver>/diff?against=<ver>
    (
        re.compile(r"^/api/snapshots/([a-z0-9._-]+)/([a-z0-9._-]+)/diff$"),
        lambda m, qs: api_snapshot_diff(
            m.group(1),
            m.group(2),
            against_version=(qs.get("against") or [""])[0] or None,
        ),
    ),
    # /api/audit-log?n=<int>
    (
        re.compile(r"^/api/audit-log$"),
        lambda m, qs: api_audit_log(n=(qs.get("n") or ["100"])[0]),
    ),
    # /api/diff?a=<ed>&b=<ed> — sensible defaults baked in
    (
        re.compile(r"^/api/diff$"),
        lambda m, qs: api_edition_diff(
            (qs.get("a") or ["catholic-study"])[0] or "catholic-study",
            (qs.get("b") or ["evangelical-reformed"])[0] or "evangelical-reformed",
        ),
    ),
]


# ω.35-A.5 (2026-05-11) — fourth slice of the route-table migration.
# `_PUT_ROUTES` covers PUT mutation routes that share the
# uniform shape: regex match → `payload = self._read_body()` →
# `result = api_X(group(1), payload)` → translate `ok: False`
# to HTTP 400 → send_json. Dispatch is wrapped in try/except so
# any handler exception becomes a 400 with the exception message
# (mirrors the legacy 9-line boilerplate inlined 6+ times).
#
# Admin auth happens at do_PUT function entry (one
# `_check_admin_auth()` call); table dispatch runs AFTER that
# check, so every table-registered route is auto-protected.
#
# Entries are `(regex, handler)` where handler is
# `Callable[[Match, dict], dict]` — takes the regex match and
# the parsed JSON payload, returns the response dict.
# `_dispatch_table_result` was extended in ω.35-A.5 to handle
# the `{ok: False}` legacy mutation-result shape (→ HTTP 400).
_PUT_ROUTES: list[tuple[re.Pattern, object]] = [
    (re.compile(r"^/api/notes/([a-z0-9]+)$"), lambda m, payload: api_save(m.group(1), payload)),
    # ω.35-A.10 — /api/edition/<id>/note-toggle MUST precede the
    # broader /api/edition/<id> below; both regex match on the same
    # prefix but the more-specific suffix-bearing pattern needs to
    # iterate first.
    (
        re.compile(r"^/api/edition/([a-z0-9-]+)/note-toggle$"),
        lambda m, payload: api_save_note_toggle(m.group(1), payload),
    ),
    # ρ.3 Phase C2-5 — /api/edition/<id>/note-override — atomic three-state
    # per-note override (enabled_note_ids force-on / disabled_note_ids force-off,
    # mutually exclusive). Distinct suffix from note-toggle above; both must
    # precede the broader /api/edition/<id> pattern below.
    (
        re.compile(r"^/api/edition/([a-z0-9-]+)/note-override$"),
        lambda m, payload: api_save_note_override(m.group(1), payload),
    ),
    (re.compile(r"^/api/edition/([a-z0-9-]+)$"), lambda m, payload: api_save_edition(m.group(1), payload)),
    (re.compile(r"^/api/scenarios/([a-z0-9_-]+)$"), lambda m, payload: api_save_scenario(m.group(1), payload)),
    (re.compile(r"^/api/category/([a-z0-9-]+)$"), lambda m, payload: api_save_category(m.group(1), payload)),
    (re.compile(r"^/api/kind/([a-z0-9-]+)$"), lambda m, payload: api_save_kind(m.group(1), payload)),
    (re.compile(r"^/api/publisher/([a-z0-9-]+)$"), lambda m, payload: api_save_publisher_meta(m.group(1), payload)),
    # ω.35-A.10 — /api/edition-meta/<id> — uses standard ok:True|False
    # shape (200 / 400). Standard helper covers it.
    (
        re.compile(r"^/api/edition-meta/([a-z0-9-]+)$"),
        lambda m, payload: api_save_edition_meta(m.group(1), payload),
    ),
    # ε.7 — /api/press-kit/<edition> — save per-edition blurbs.
    # Payload: {blurb_150?, blurb_500?, sample_chapter_html?}.
    (
        re.compile(r"^/api/press-kit/([a-z0-9-]+)$"),
        lambda m, payload: api_press_kit_save(m.group(1), payload),
    ),
    # ω.35-A.10 — /api/editions/from-template — uses status==ok|error
    # shape. Standard helper covers it via status==error → http
    # envelope and fall-through 200.
    (
        re.compile(r"^/api/editions/from-template$"),
        lambda m, payload: api_create_edition_from_template(
            (payload or {}).get("template_id", ""),
            (payload or {}).get("new_id", ""),
            (payload or {}).get("new_title", ""),
        ),
    ),
]


# ω.35-A.6 (2026-05-11) — fifth slice of the route-table migration.
# `_DELETE_ROUTES` covers DELETE routes (no payload) that go through
# the standard `_dispatch_table_result` helper. Same shape as
# `_PUT_ROUTES` but the handler signature is `lambda m: api_X(...)`
# — no payload, no read_body() call. Admin auth runs at do_DELETE
# function entry (one `_check_admin_auth()` call).
#
# Order matters: more-specific patterns precede less-specific ones
# (e.g. `/api/covers/<ed>/book/<book>` before `/api/covers/<ed>/main`
# isn't needed because the suffixes differ, but the principle holds).
_DELETE_ROUTES: list[tuple[re.Pattern, object]] = [
    # /api/notes/<book>/<idx> — note delete by 0-based index
    (re.compile(r"^/api/notes/([a-z0-9]+)/(\d+)$"), lambda m: api_delete(m.group(1), int(m.group(2)))),
    # /api/snapshots/<ed>/<ver> — uses status==error envelope (Δ-shape)
    (
        re.compile(r"^/api/snapshots/([a-z0-9._-]+)/([a-z0-9._-]+)$"),
        lambda m: api_snapshot_delete(m.group(1), m.group(2)),
    ),
    # /api/scenarios/<name> — uses ok:False envelope
    (re.compile(r"^/api/scenarios/([a-z0-9_-]+)$"), lambda m: api_delete_scenario(m.group(1))),
    # /api/covers/<ed>/book/<book> — more specific; MUST precede /<ed>/main
    (
        re.compile(r"^/api/covers/([a-z0-9-]+)/book/([a-z0-9]+)$"),
        lambda m: api_delete_cover_book(m.group(1), m.group(2)),
    ),
    # /api/covers/<ed>/main
    (re.compile(r"^/api/covers/([a-z0-9-]+)/main$"), lambda m: api_delete_cover_main(m.group(1))),
    # ω.35-A.8 — /api/sources/cache/<id> — clear a source cache.
    # Previously used `_send_dict_result` (which preserved extras in
    # error envelopes); now table-compatible because A.8 extended
    # `_dispatch_table_result` to preserve extras too.
    # api_sources_cache_clear's error envelopes don't include extras
    # but the discipline is uniform now.
    (
        re.compile(r"^/api/sources/cache/([a-z0-9_-]+)$"),
        lambda m: api_sources_cache_clear(m.group(1)),
    ),
]


# ω.35-A.7 (2026-05-11) — sixth slice of the route-table migration.
# `_POST_ROUTES` covers POST routes whose result-shape goes through
# the standard `_dispatch_table_result` helper. Same lambda signature
# as `_PUT_ROUTES`: `lambda m, payload`. Admin auth runs at do_POST
# function entry. Body read happens once in the dispatch loop (matches
# the PUT loop), and `_read_body() or {}` makes empty-body POSTs
# (e.g. snapshot restore) work transparently.
#
# Out of scope for A.7 (deferred to A.8 — bespoke cleanup):
# - /api/sources/cache/_all/fetch and /api/sources/cache/<id>/fetch
#   (use `_send_dict_result` which preserves extras in error envelopes
#   — they need either an extension to `_dispatch_table_result` or a
#   dedicated `_POST_DICT_RESULT_ROUTES` table, both judgment calls
#   best deferred).
# - 3 multipart routes (cover main, cover book, sources cache upload)
#   — these read the raw body, not JSON; they need a `_MULTIPART_ROUTES`
#   table with a distinct lambda signature `lambda m, body, ctype` and
#   their own dispatch loop. Separate slice.
_POST_ROUTES: list[tuple[re.Pattern, object]] = [
    # W4.3 — mark the first-run welcome flow complete (idempotent).
    (re.compile(r"^/api/onboarding/complete$"), api_onboarding_complete),
    # §4.6 — /api/covers/<ed>/template — recompose the edition's main cover
    # from one of the 25 design templates + the edition title. JSON body
    # {"cover_template": "<stem>"}. Distinct suffix from the /main multipart
    # upload and the DELETE cover routes, so there's no ordering hazard.
    (
        re.compile(r"^/api/covers/([a-z0-9-]+)/template$"),
        lambda m, payload: api_apply_cover_template(m.group(1), (payload.get("cover_template") or "")),
    ),
    # /api/snapshots/<ed>/<ver>/restore — no payload; status==error
    # envelope. MUST precede /api/snapshots/<ed> (more specific).
    (
        re.compile(r"^/api/snapshots/([a-z0-9._-]+)/([a-z0-9._-]+)/restore$"),
        lambda m, payload: api_snapshot_restore(m.group(1), m.group(2)),
    ),
    # /api/snapshots/<ed> — create; payload pass-through; status==error
    (
        re.compile(r"^/api/snapshots/([a-z0-9._-]+)$"),
        lambda m, payload: api_snapshot_create(m.group(1), payload),
    ),
    # /api/matrix/apply-kind-to-all — payload destructure; status==error
    (
        re.compile(r"^/api/matrix/apply-kind-to-all$"),
        lambda m, payload: api_apply_kind_to_all_editions(
            payload.get("kind") or "",
            enable=bool(payload.get("enable")),
        ),
    ),
    # /api/scenarios/_import — payload destructure; status==error
    (
        re.compile(r"^/api/scenarios/_import$"),
        lambda m, payload: api_import_scenario_yaml(
            payload.get("yaml") or "",
            name=payload.get("name") or None,
            overwrite=bool(payload.get("overwrite")),
        ),
    ),
    # /api/editions/clone — payload pass-through; uses ok:False envelope
    (
        re.compile(r"^/api/editions/clone$"),
        lambda m, payload: api_clone_edition(payload),
    ),
    # /api/backups/restore — payload destructure; status==ok|error
    (
        re.compile(r"^/api/backups/restore$"),
        lambda m, payload: api_restore_backup(
            payload.get("file") or "",
            payload.get("snapshot_id") or "",
        ),
    ),
    # ο.4 — /api/archive-org/upload/<edition> — compose press-kit
    # ZIP + S3-style PUT to archive.org + auto-mark distribution
    # cell. Payload reserved for future options (currently {}).
    # Returns ok:True on success (200/2xx from archive.org) or
    # standard {status:error, code, http, message} envelope on
    # missing credentials / unknown edition / upload failure.
    (
        re.compile(r"^/api/archive-org/upload/([a-z0-9-]+)$"),
        lambda m, payload: api_archive_org_upload(m.group(1), payload),
    ),
    # ξ.21 — 2FA enrollment flow (begin → confirm → disable).
    (
        re.compile(r"^/api/auth/totp/begin$"),
        lambda m, payload: api_auth_totp_begin(payload),
    ),
    (
        re.compile(r"^/api/auth/totp/confirm$"),
        lambda m, payload: api_auth_totp_confirm(payload),
    ),
    (
        re.compile(r"^/api/auth/totp/disable$"),
        lambda m, payload: api_auth_totp_disable(payload),
    ),
    # ω.35-A.8 — sources/cache fetch routes. Previously used
    # `_send_dict_result` (which preserved extras in error
    # envelopes). Now table-compatible because A.8 extended
    # `_dispatch_table_result` to preserve extras too. MORE-
    # SPECIFIC /<id>/fetch must precede the broader _all/fetch
    # match isn't a concern here (paths are distinct), but
    # convention pinned.
    # /api/sources/cache/_all/fetch — payload "force"; status==ok|error
    (
        re.compile(r"^/api/sources/cache/_all/fetch$"),
        lambda m, payload: api_sources_cache_fetch_all(
            force=bool(payload.get("force")),
        ),
    ),
    # /api/sources/cache/<id>/fetch — payload force/url_override/parser_override
    (
        re.compile(r"^/api/sources/cache/([a-z0-9_-]+)/fetch$"),
        lambda m, payload: api_sources_cache_fetch(
            m.group(1),
            force=bool(payload.get("force")),
            url_override=payload.get("url_override") or None,
            parser_override=payload.get("parser_override") or None,
        ),
    ),
]


# ω.35-A.9 (2026-05-11) — eighth slice of the route-table migration.
# `_MULTIPART_ROUTES` covers POST routes that take a multipart body
# instead of JSON. Distinct entry shape: 3-tuple
# `(regex, max_bytes, lambda m, body, content_type)` because the
# body is bytes (not parsed dict) and the per-route size cap differs
# (cover uploads = 10 MB; source cache uploads = 50 MB).
#
# The hard cap stored here is the per-file limit; the dispatch loop
# multiplies by 2 before rejecting (matches the legacy pattern's
# "twice the per-file limit so a hostile client can't tie up the
# server with an unbounded read" comment).
#
# Handlers return the standard `{ok, ...}` or `{status, ...}` dict
# shape and route through `_dispatch_table_result` like the other
# tables — uniform on the response side.
_MULTIPART_ROUTES: list[tuple[re.Pattern, int, object]] = [
    # /api/covers/<ed>/main — cover upload (main hero cover)
    (
        re.compile(r"^/api/covers/([a-z0-9-]+)/main$"),
        COVERS_UPLOAD_MAX_BYTES,
        lambda m, body, ctype: api_upload_cover_main(m.group(1), body, ctype),
    ),
    # /api/covers/<ed>/book/<book> — cover upload (per-book cover).
    # MUST precede /api/covers/<ed>/main if both could match — they
    # don't here (different suffixes) but the discipline is pinned.
    (
        re.compile(r"^/api/covers/([a-z0-9-]+)/book/([a-z0-9]+)$"),
        COVERS_UPLOAD_MAX_BYTES,
        lambda m, body, ctype: api_upload_cover_book(m.group(1), m.group(2), body, ctype),
    ),
    # /api/sources/cache/<id>/upload — drag-drop JSON cache upload
    (
        re.compile(r"^/api/sources/cache/([a-z0-9_-]+)/upload$"),
        SOURCES_UPLOAD_MAX_BYTES,
        lambda m, body, ctype: api_sources_cache_upload(m.group(1), body, ctype),
    ),
]


def _dispatch_multipart_route(
    handler_self,
    match: re.Match,
    max_bytes: int,
    handler: object,
) -> None:
    """ω.35-A.9 helper — read a multipart body within a per-route
    size cap and route the result through the standard dispatch
    helper. Consolidates the boilerplate that was duplicated in
    `_handle_cover_upload` and `_handle_sources_cache_upload`:
    parse Content-Length → validate int → reject > 2 * max_bytes
    → read body → call handler(match, body, content_type) →
    `_dispatch_table_result`. Any error path returns 400 with
    `{error: str}` (matches legacy)."""
    try:
        length_header = handler_self.headers.get("Content-Length", "")
        try:
            length = int(length_header)
        except ValueError:
            return handler_self._send_json(
                {"error": "missing or invalid Content-Length"},
                status=400,
            )
        # Hard cap at twice the per-file limit (defensive against a
        # hostile client streaming an unbounded body).
        cap = max_bytes * 2
        if length > cap:
            return handler_self._send_json(
                {"error": f"request too large: {length} bytes (max {cap})"},
                status=413,
            )
        body = handler_self.rfile.read(length) if length > 0 else b""
        content_type = handler_self.headers.get("Content-Type", "")
        result = handler(match, body, content_type)
        return _dispatch_table_result(handler_self, result)
    except Exception as e:
        return handler_self._send_json({"error": str(e)}, status=400)


def _dispatch_table_result(handler_self, result: dict) -> None:
    """ω.35-A.2 helper — translate a handler dict result to an HTTP
    response, mirroring the boilerplate that appeared 10+ times in
    the legacy cascade.

    Three response shapes handled:
    1. `{"status": "error", "code": ..., "http": ..., "message": ...,
       <extras>}` — translated to JSON error envelope with appropriate
       HTTP status. (ω.35-A.2 introduced this for the GET tables.
       ω.35-A.8 added extras-preservation so handlers that include
       additional fields in their error envelope — e.g.
       `api_sources_cache_fetch_all` returning `"results": []` on
       config error — match the legacy `_send_dict_result` behavior.)
    2. `{"ok": False, ...}` — legacy mutation-result shape used by
       api_save_edition / api_save_scenario / api_save_kind etc.
       Sends the raw result with HTTP 400. (ω.35-A.5 added this for
       the PUT/DELETE tables; preserves the legacy
       `status = 200 if result.get("ok") else 400` pattern.)
    3. Any other dict — sent as 200. Covers the `{"ok": True, ...}`
       success shape AND handlers that return bare result dicts
       without the ok-or-status discriminator (e.g. api_save's
       happy path returns `{"ok": True, ...}`; its error path
       returns `{"error": ..., "book": ...}` with no `ok` key —
       both go through as 200, matching legacy behavior).
    """
    if result.get("status") == "error":
        envelope = {
            "error": result.get("code") or "internal_error",
            "message": result.get("message") or "",
        }
        # ω.35-A.8 — preserve any extras (fields beyond the standard
        # status/code/http/message) so behavior matches the legacy
        # `_send_dict_result` helper. None of the routes migrated
        # before A.8 return extras in error envelopes (verified via
        # grep across all `"status": "error"` returns), so this
        # extension is behavior-neutral for them.
        for k, v in result.items():
            if k not in ("status", "code", "http", "message", "error"):
                envelope[k] = v
        handler_self._send_json(envelope, status=result.get("http") or 500)
        return
    if result.get("ok") is False:
        handler_self._send_json(result, status=400)
        return
    handler_self._send_json(result)


class Handler(BaseHTTPRequestHandler):
    # ξ.3 — security response headers. Applied to every HTML + JSON
    # response via _send_security_headers below.
    #
    # CSP rationale:
    #   default-src 'self'         — only same-origin loads
    #   script-src ... 'unsafe-inline' https://cdn.tailwindcss.com
    #                              — inline <script> blocks + the
    #                                Tailwind Play CDN are intentional
    #                                (CLAUDE_PROJECT_RULES §6.3 — no
    #                                build step). Tighten in a future
    #                                ξ phase if we move to bundled JS.
    #   style-src ... 'unsafe-inline' https://cdn.tailwindcss.com
    #                              — Tailwind injects styles at runtime
    #                                from the CDN; inline <style> blocks
    #                                are also intentional.
    #   img-src 'self' data:       — uploaded covers + data: URLs for
    #                                small icons.
    #   frame-ancestors 'none'     — forbid embedding /matrix etc. in
    #                                iframes (prevents clickjacking).
    #   base-uri 'self'            — block <base> tag injection.
    #   form-action 'self'         — submissions stay same-origin.
    _CSP_POLICY = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
        "img-src 'self' data:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    # ξ.18 (2026-05-12) — per-request nonce regex. Inserts
    # `nonce="<value>"` into every `<script` tag that doesn't already
    # carry one. Anchored on `<script` followed by a tag-attribute
    # boundary character (space, slash, or `>`); `<scripts>` and
    # `<scripting>` deliberately don't match.
    _SCRIPT_TAG_RE = re.compile(r"<script(?![a-zA-Z0-9-_])")

    @staticmethod
    def _generate_nonce() -> str:
        """Fresh CSP nonce per request. 16 bytes of os.urandom → base64
        url-safe encoding → 22-char string. RFC 8941 recommends ≥128
        bits of entropy for CSP nonces; 16 bytes (128 bits) satisfies."""
        return secrets.token_urlsafe(16)

    @classmethod
    def _csp_with_nonce(cls, nonce: str) -> str:
        """Return the strict CSP for an HTML response with this nonce.
        Drops `'unsafe-inline'` from `script-src` and adds the per-
        request `'nonce-<value>'` so every inline `<script>` block in
        the rendered HTML must carry the matching nonce attribute.

        `style-src` keeps `'unsafe-inline'` for now — Tailwind's Play
        CDN injects styles at runtime; tightening style-src is a
        separate ξ phase (style-src nonces require a Tailwind-build
        migration, which conflicts with §6.3 'no build step').
        """
        return (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    @classmethod
    def _inject_script_nonces(cls, html: str, nonce: str) -> str:
        """Add `nonce="<value>"` to every `<script` tag in `html` that
        doesn't already carry one. Pure function — html and nonce
        passed in, transformed html returned.

        Variant coverage:
            <script>            → <script nonce="X">
            <script src="...">  → <script nonce="X" src="...">
            <script async>      → <script nonce="X" async>
            <script\\nsrc="...">  → <script nonce="X"\\nsrc="..."> (preserves
                                                            internal whitespace)

        Idempotent: the regex adds `nonce="<value>"` to every `<script`
        tag, then a post-process pass collapses any resulting duplicate
        `nonce=` attribute (see below), so re-running on already-noncified
        HTML is a no-op. (An earlier lookahead-based "skip tags that
        already carry a nonce" design was dropped in favour of this simpler
        sub-then-dedupe.)"""

        def add_nonce(match: re.Match) -> str:
            return f'<script nonce="{nonce}"'

        # Skip tags that already have nonce="" (idempotent).
        # We accomplish this by limiting the regex to <script tags
        # without `nonce=` in the next 200 chars — but that requires
        # lookahead. Simpler: post-process to dedupe nonce attrs.
        result = cls._SCRIPT_TAG_RE.sub(add_nonce, html)
        # Collapse duplicate nonce attrs (defensive against caller
        # re-noncifying already-noncified HTML).
        if "nonce=" in html:
            result = re.sub(
                rf'<script nonce="{re.escape(nonce)}" nonce="[^"]+"',
                f'<script nonce="{nonce}"',
                result,
            )
        return result

    def _send_security_headers(self, *, nonce: str | None = None):
        """ξ.3 + ξ.18 — add CSP + nosniff + Referrer-Policy headers.

        Called by every response helper (_send_html, _send_json,
        _send_file, plus inline routes that build their own header
        block). Tailwind CDN is allow-listed; everything else is
        same-origin. Frame-ancestors blocks clickjacking.

        ξ.18 (2026-05-12): when `nonce` is provided, emit the strict
        CSP that requires `nonce-<value>` on every inline script
        instead of `'unsafe-inline'`. JSON / file / zip responses
        pass nonce=None (no inline scripts in those responses) and
        keep the legacy policy as defense-in-depth.
        """
        policy = self._csp_with_nonce(nonce) if nonce else self._CSP_POLICY
        self.send_header("Content-Security-Policy", policy)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_unhandled_error(self, exc: Exception, method_name: str = "?"):
        """ω.8 — last-resort error path. Logs the traceback to stderr
        for the operator (the existing log_message convention) and
        returns a structured 500 JSON to the client. Critically, the
        client never sees a Python stack trace — that's both an
        information-disclosure concern and an unfriendly UX."""
        import traceback

        # Log full detail to stderr — useful for operators tailing
        # the dev server; the existing log_message format is short
        # so we drop straight to stderr for tracebacks.
        sys.stderr.write(f"  [unhandled {method_name}] {type(exc).__name__}: {exc}\n")
        traceback.print_exc(file=sys.stderr)
        try:
            return self._send_json(
                {
                    "error": "internal_error",
                    "message": (f"unhandled {type(exc).__name__} in {method_name}; see server log for details"),
                },
                status=500,
            )
        except Exception:
            # If even the JSON send fails (broken pipe, etc.), there's
            # nothing else to do — the request is gone.
            pass

    def _send_html(self, html: str):
        # η.1 — re-tone every Tailwind console to the public website's manuscript
        # palette (no-op on non-console pages / if already skinned). Runs BEFORE
        # nonce injection so the skin's inline <script> picks up the CSP nonce.
        from scripts.templates._design import apply_manuscript_skin

        html = apply_manuscript_skin(html)
        # ξ.18 — fresh per-request nonce + noncified body + strict CSP.
        nonce = self._generate_nonce()
        noncified = self._inject_script_nonces(html, nonce)
        body = noncified.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_security_headers(nonce=nonce)  # ξ.3 + ξ.18
        self.end_headers()
        self.wfile.write(body)

    def _send_zip(self, filename: str, data: bytes):
        """ε.7 — serve a ZIP as an attachment download. Filename is
        sanitized to ASCII-safe characters via the standard simple
        filter (alphanumerics + dash + underscore + dot); anything
        else collapses to underscore so the Content-Disposition header
        stays well-formed across browsers."""
        safe_name = "".join(c if (c.isalnum() or c in "._-") else "_" for c in filename) or "download.zip"
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition", f'attachment; filename="{safe_name}"')
        self.send_header("Cache-Control", "no-store")
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path: Path, content_type: str | None = None):
        """Serve a binary file (cover images etc.). Path must already
        be confirmed safe by the caller — this helper does NOT
        re-validate path traversal, since the route is responsible
        for sandboxing to a known-safe directory."""
        try:
            data = path.read_bytes()
        except OSError:
            return self._send_json({"error": "file not found"}, status=404)
        if content_type is None:
            # ξ.16 SEC-001 — restrict served images to the same
            # allowlist the upload validator accepts (png/jpeg/webp).
            # Critically, drop SVG and GIF: SVG is XML and renders
            # inline `<script>` / `on*` handlers when navigated to
            # directly, which would XSS the localhost origin from the
            # /content/covers/ same-origin route. Verify magic bytes
            # match the extension — a hostile file dropped under
            # content/covers/ (via backup restore, scenario import,
            # or hand placement) cannot be served as an image.
            from scripts.core.covers import UPLOAD_ALLOWED_FORMATS, _detect_format

            ext = path.suffix.lower().lstrip(".")
            ext_norm = "jpeg" if ext == "jpg" else ext
            fmt = _detect_format(data[:32], ext)
            if fmt not in UPLOAD_ALLOWED_FORMATS or ext_norm not in UPLOAD_ALLOWED_FORMATS:
                return self._send_json({"error": "unsupported media type"}, status=415)
            if fmt != ext_norm:
                # Magic bytes disagree with extension — refuse to
                # serve. The route is read-only so we can't fix the
                # disk state from here; the upload pipeline is
                # responsible for never letting this combination land.
                return self._send_json({"error": "format/extension mismatch"}, status=415)
            content_type = {
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }[fmt]
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        # ξ.16 SEC-010 — `private` not `public`: the localhost app has
        # no shared cache, but if a user binds --host 0.0.0.0 with a
        # corporate proxy on path, public would let the proxy cache
        # private editorial content.
        self.send_header("Cache-Control", "private, max-age=60")
        self._send_security_headers()  # ξ.3
        # ξ.16 SEC-001 — extra defense: even with the magic-byte
        # check above, sandbox the response. `default-src 'none'`
        # blocks every subresource fetch the image-as-document
        # would attempt; `sandbox` blocks scripts/forms/popups in
        # browsers that respect it.
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; sandbox; img-src 'self'",
        )
        self.end_headers()
        self.wfile.write(data)

    # ξ.16 SEC-002 — generous cap on JSON body size. Every legitimate
    # JSON payload on this server is well under 1 MB (kind toggles,
    # edition meta, scenarios, audit reads). 32 MB gives 30× headroom
    # for the largest plausible legit payload while still rejecting a
    # 2 GB Content-Length attack BEFORE allocation. The size check
    # comes BEFORE self.rfile.read() — no allocation happens for an
    # over-cap request.
    JSON_BODY_MAX_BYTES = 32 * 1024 * 1024

    def _read_body(self) -> dict:
        length_header = self.headers.get("Content-Length") or "0"
        try:
            length = int(length_header)
        except ValueError:
            raise ValueError("invalid Content-Length") from None
        if length < 0:
            raise ValueError("negative Content-Length")
        if not length:
            return {}
        if length > self.JSON_BODY_MAX_BYTES:
            # ξ.16 SEC-002 — reject the request BEFORE allocating
            # `length` bytes. Existing per-route `except Exception
            # as e: return self._send_json({"error": str(e)},
            # status=400)` translates this to a 400 with the
            # message; importantly, no buffer allocation, no DoS.
            raise ValueError(f"request body too large: {length} bytes (max {self.JSON_BODY_MAX_BYTES})")
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _check_admin_auth(self) -> bool:
        """Phase ω.4 + ξ.21 — auth gate for mutation endpoints.

        Two factors compose:

          - **Factor 1 — admin token** (``EBIBLE_ADMIN_TOKEN`` env
            var). Unset → factor 1 not required. Set → caller must
            present a matching token.
          - **Factor 2 — TOTP** (enrolled via ξ.21's `/api/auth/totp/*`
            endpoints). Disabled → factor 2 not required. Enabled →
            caller must present a current 6-digit code.

        ``Authorization`` header formats accepted (per active factors):

            Both factors enabled →  ``Authorization: Bearer <token>:<code>``
            Token only            →  ``Authorization: Bearer <token>``
            TOTP only             →  ``Authorization: Bearer :<code>``
                                     (token slot is empty)
            Neither               →  no header required (back-compat)

        GET / HEAD bypass this gate (read-only stays open even when
        the rest is locked down).

        Returns True when allowed; on False the 401 response has
        already been sent and the caller should return immediately.
        """
        token = os.environ.get("EBIBLE_ADMIN_TOKEN", "").strip()
        from scripts.core import auth as auth_core

        totp_enabled = auth_core.is_totp_enabled()
        if not token and not totp_enabled:
            return True  # auth disabled, back-compat default
        header = self.headers.get("Authorization", "")
        prefix = "Bearer "
        if not header.startswith(prefix):
            self._send_json(
                {"error": "missing Authorization: Bearer <token>[:<totp-code>] header"},
                status=401,
            )
            return False
        supplied = header[len(prefix) :].strip()
        # Parse "<token>:<code>" — split on the FIRST colon only so
        # tokens that themselves contain colons (e.g. base64-encoded
        # secrets) round-trip correctly.
        supplied_token, _, supplied_code = supplied.partition(":")
        import hmac

        if token:
            if not hmac.compare_digest(supplied_token, token):
                self._send_json({"error": "invalid admin token"}, status=401)
                return False
        # ξ.21 — if TOTP is enabled, require a matching code in addition
        # to (or instead of) the token.
        if totp_enabled:
            secret = auth_core.get_totp_secret()
            from scripts.core import totp as totp_mod

            if not secret or not totp_mod.verify_code(secret, supplied_code):
                self._send_json(
                    {"error": "invalid or missing TOTP code"},
                    status=401,
                )
                return False
        return True

    def log_message(self, fmt, *args):
        # Quieter than the default
        sys.stderr.write(f"  {self.address_string()} - {fmt % args}\n")

    # -------- routes --------

    @_safe_request
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        # ω.35-A.1 — table-driven dispatch for the simplest JSON GET
        # routes. Falls through to the legacy if/elif cascade for
        # routes that don't fit (auth-gated, payload-reading, etc.).
        # See `_SIMPLE_GET_ROUTES` near the top of the file for
        # the migration contract and the drift-tolerance strategy.
        for route_path, handler in _SIMPLE_GET_ROUTES:
            if path == route_path:
                return self._send_json(handler())

        # ω.35-A.2 — regex routes with the standard
        # "handler(*groups) + error-translate" boilerplate.
        # Table order = precedence (more-specific before less).
        for regex, handler in _REGEX_GET_ROUTES:
            m = regex.match(path)
            if m:
                result = handler(*m.groups())
                return _dispatch_table_result(self, result)

        # ω.35-A.4 — regex routes with querystring parsing. Each
        # handler is `lambda m, qs: api_X(...)` — takes the match
        # and the parsed querystring dict, returns the response.
        # Routes through the same `_dispatch_table_result` helper
        # so the standard error-translate envelope still applies
        # uniformly.
        for regex, handler in _QS_REGEX_GET_ROUTES:
            m = regex.match(path)
            if m:
                qs = urllib.parse.parse_qs(url.query or "")
                result = handler(m, qs)
                return _dispatch_table_result(self, result)

        if path == "/" or path == "/index.html":
            return self._send_html(INDEX_HTML)
        if path == "/matrix" or path == "/matrix.html":
            return self._send_html(MATRIX_HTML)
        # ω.35-A.3 (2026-05-11) — deleted dead-code legacy branches
        # for the 14 simple + 3 regex routes migrated to
        # `_SIMPLE_GET_ROUTES` / `_REGEX_GET_ROUTES`. The table
        # dispatch loops at the top of this method handle them now.
        # The /api/snapshots/<ed>/<ver>/diff route stays here — it
        # needs querystring parsing (`?against=<ver>`) which the
        # current tables don't support; ω.35-A.4 will widen the
        # regex table to cover query-bearing routes.

        # ω.35-A.4 — /api/snapshots/<ed>/<ver>/diff migrated to
        # _QS_REGEX_GET_ROUTES.

        # ψ.27 — YAML export route. Place BEFORE the generic
        # /api/scenarios/<name> matcher so the .yaml suffix is matched
        # specifically (the suffix puts it outside the generic regex).
        m = re.match(r"^/api/scenarios/([a-z0-9_-]+)/export\.yaml$", path)
        if m:
            result = api_export_scenario_yaml(m.group(1))
            if result.get("status") == "error":
                return self._send_json(
                    {"error": result.get("code") or "internal_error", "message": result.get("message") or ""},
                    status=result.get("http") or 500,
                )
            yaml_text = result["yaml"]
            body = yaml_text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/x-yaml; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{m.group(1)}.yaml"',
            )
            self._send_security_headers()  # ξ.3
            self.end_headers()
            self.wfile.write(body)
            return

        m = re.match(r"^/api/scenarios/([a-z0-9_-]+)$", path)
        if m:
            return self._send_json(api_get_scenario(m.group(1)))

        # Sources Navigator (Phase μ.3)
        if path == "/sources" or path == "/sources.html":
            return self._send_html(SOURCES_HTML)
        # PD source-cache management (Phase υ.1) — distinct from
        # /api/sources below, which navigates note attribution
        if path == "/api/sources/cache":
            return self._send_json(api_sources_cache_status())
        # ω.35-A.3 — /api/sources migrated to _SIMPLE_GET_ROUTES.
        if path == "/api/sources/summary":
            return self._send_json(api_sources_summary())
        # υ.3 — cross-edition note search. Read query + filters from
        # the URL query string; thin route adapter over api_search_notes.
        if path == "/api/search-notes":
            qs = urllib.parse.parse_qs(url.query or "")
            q = (qs.get("q") or [""])[0]
            ed = (qs.get("edition_id") or [""])[0] or None
            kf = (qs.get("kind") or [""])[0] or None
            bk = (qs.get("book") or [""])[0] or None
            try:
                lim = int((qs.get("limit") or ["100"])[0])
            except ValueError:
                lim = 100
            result = api_search_notes(
                q,
                edition_id=ed,
                kind=kf,
                book=bk,
                limit=lim,
            )
            if result.get("status") == "error":
                return self._send_json(
                    {"error": result.get("code") or "internal_error", "message": result.get("message") or ""},
                    status=result.get("http") or 500,
                )
            return self._send_json(result)
        m = re.match(r"^/api/sources/([a-z0-9]+)$", path)
        if m:
            return self._send_json(api_sources_for_book(m.group(1)))
        # υ.8 — verse-of-the-day feeds. JSON + RSS share the same
        # underlying picker. ?date=YYYY-MM-DD pins a specific day;
        # ?edition_id=<id> restricts to that edition's enabled kinds.
        if path == "/api/verse-of-day.json":
            qs = urllib.parse.parse_qs(url.query or "")
            d = (qs.get("date") or [""])[0] or None
            ed = (qs.get("edition_id") or [""])[0] or None
            result = api_verse_of_day(d, edition_id=ed)
            if result.get("status") == "error":
                return self._send_json(
                    {"error": result.get("code") or "internal_error", "message": result.get("message") or ""},
                    status=result.get("http") or 500,
                )
            return self._send_json(result)
        if path == "/api/verse-of-day.rss":
            qs = urllib.parse.parse_qs(url.query or "")
            ed = (qs.get("edition_id") or [""])[0] or None
            try:
                days = int((qs.get("days") or ["7"])[0])
            except ValueError:
                days = 7
            # ξ.16 SEC-003 — never reflect Host / X-Forwarded-Proto
            # verbatim into RSS link URLs. An attacker (LAN peer in
            # --host 0.0.0.0 mode, or a tab that gets the RSS reader
            # to fetch with crafted headers) can otherwise pin
            # `javascript://attacker.tld/...` or `https://evil.tld/...`
            # into syndicated feeds. Trust order:
            #   1. YHWH_PUBLIC_BASE_URL (operator-set, authoritative)
            #   2. Host header IFF it matches the localhost allowlist
            #   3. hardcoded fallback http://localhost
            base = _safe_rss_base_url(
                self.headers.get("X-Forwarded-Proto", "http"),
                self.headers.get("Host") or "",
            )
            xml, mime = api_verse_of_day_rss(
                days=days,
                base_url=base,
                edition_id=ed,
            )
            body = xml.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            # 1-hour cache (dates roll over once a day; 1h is conservative)
            self.send_header("Cache-Control", "public, max-age=3600")
            self._send_security_headers()  # ξ.3
            self.end_headers()
            self.wfile.write(body)
            return

        # Export (Phase σ.1 + σ.2)
        if path == "/export" or path == "/export.html":
            return self._send_html(EXPORT_HTML)
        m = re.match(r"^/api/export/preview/([a-z0-9-]+)$", path)
        if m:
            return self._send_json(api_export_preview(m.group(1)))
        m = re.match(r"^/api/export/download/([\w.-]+)$", path)
        if m:
            result = api_download_export(m.group(1))
            if isinstance(result, dict):
                return self._send_json(result, status=404)
            data, mime = result
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{m.group(1)}"',
            )
            self._send_security_headers()  # ξ.3
            self.end_headers()
            self.wfile.write(data)
            return

        # Customize (Phase ν.1)
        if path == "/customize" or path == "/customize.html":
            return self._send_html(CUSTOMIZE_HTML)
        # ω.35-A.3 — /api/customize migrated to _SIMPLE_GET_ROUTES.

        # Attribution Audit (Phase ξ.4)
        if path == "/audit" or path == "/audit.html":
            return self._send_html(AUDIT_HTML)
        if path == "/api/audit/attribution":
            return self._send_json(api_attribution_audit())

        # Mutation Audit Log (Phase ξ.13)
        if path == "/audit-log" or path == "/audit-log.html":
            return self._send_html(AUDIT_LOG_HTML)
        # ω.35-A.4 — /api/audit-log migrated to _QS_REGEX_GET_ROUTES.

        # Per-note disable list for one edition (Phase ρ.1)
        m = re.match(r"^/api/edition/([a-z0-9-]+)/disabled-notes$", path)
        if m:
            return self._send_json(api_disabled_notes_for_edition(m.group(1)))

        # Publisher console (Phase π.1)
        if path == "/publisher" or path == "/publisher.html":
            return self._send_html(PUBLISHER_HTML)
        # ω.35-A.3 — /api/publisher migrated to _SIMPLE_GET_ROUTES.

        # Bible Builder Wizard (Phase π.5)
        if path == "/wizard" or path == "/wizard.html":
            return self._send_html(WIZARD_HTML)

        # Edition Diff View (Phase ξ.5) — read-only sales/demo tool
        if path == "/diff" or path == "/diff.html":
            return self._send_html(DIFF_HTML)
        # ω.35-A.4 — /api/diff migrated to _QS_REGEX_GET_ROUTES.

        # Translation comparison view (Phase ψ.4) — read-only side-
        # by-side renderer. Buyer demo without needing a full EPUB.
        if path == "/compare" or path == "/compare.html":
            return self._send_html(COMPARE_HTML)
        if path == "/api/compare":
            qs = urllib.parse.parse_qs(url.query or "")
            book = (qs.get("book") or ["gen"])[0]
            chapter_str = (qs.get("chapter") or ["1"])[0]
            try:
                chapter = int(chapter_str)
            except ValueError:
                chapter = 1
            # translations may come as repeated ?translations=kjv params
            # OR as a single comma-separated value
            translations: list = []
            for raw in qs.get("translations") or []:
                for piece in raw.split(","):
                    piece = piece.strip()
                    if piece:
                        translations.append(piece)
            # Sensible default: just KJV (the only translation we ship today)
            if not translations:
                translations = ["kjv"]
            return self._send_json(api_compare(book, chapter, translations))

        # Sample-chapter HTML export (Phase ψ.5) — buyer demo
        # without committing to a full EPUB build. URL pattern:
        #   /api/sample/<edition_id>?book=gen&from=1&to=3
        # Returns either text/html (200) or JSON error (404/400).
        # Spec discusses POST but GET is more idiomatic for a
        # read operation driven entirely by query params.
        if path.startswith("/api/sample/"):
            edition_id = path[len("/api/sample/") :].split("/", 1)[0]
            qs = urllib.parse.parse_qs(url.query or "")
            book = (qs.get("book") or [""])[0]
            from_str = (qs.get("from") or ["1"])[0]
            to_str = (qs.get("to") or [from_str])[0]
            try:
                from_n = int(from_str)
                to_n = int(to_str)
            except ValueError:
                # api_sample_html will surface its own error; pass
                # the originals through (it does its own int coercion)
                from_n, to_n = from_str, to_str
            translation = (qs.get("translation") or ["kjv"])[0]
            result = api_sample_html(
                edition_id,
                book,
                from_n,
                to_n,
                translation=translation,
            )
            if result.get("status") == "ok":
                return self._send_html(result["html"])
            # Error path — return JSON with the spec'd HTTP status (mint-7 D2:
            # via _send_json so Content-Length + Cache-Control + security headers
            # are set, like every other JSON route).
            http_code = result.get("http") or 500
            return self._send_json(
                {
                    "error": result.get("code") or "internal_error",
                    "message": result.get("message") or "",
                },
                status=http_code,
            )

        # Backup listing (Phase ω.1) — surface the .backups/
        # snapshots that already exist. Path-traversal-safe; only
        # files inside content/ are addressable. Restore is POST
        # (see do_POST), this is GET-only.
        if path == "/api/backups":
            qs = urllib.parse.parse_qs(url.query or "")
            file_arg = (qs.get("file") or [""])[0]
            result = api_list_backups(file_arg)
            if result.get("status") == "ok":
                return self._send_json(result)
            # mint-7 D2: via _send_json for Content-Length + security headers.
            http_code = result.get("http") or 500
            return self._send_json(
                {
                    "error": result.get("code") or "internal_error",
                    "message": result.get("message") or "",
                },
                status=http_code,
            )

        # Per-book cover status (Phase π.4-A) — read-only feed for
        # the upcoming /covers UI. Returns each edition's main + per-book
        # cover slots, filtered by canon and sorted in canonical order.
        # ω.35-A.3 — /api/covers migrated to _SIMPLE_GET_ROUTES.

        # Pre-flight checklist (Phase ψ.2) — aggregator dashboard
        if path == "/preflight" or path == "/preflight.html":
            return self._send_html(PREFLIGHT_HTML)

        # Ω.0 (2026-05-14) — /build-tracker: per-edition enabled-
        # notes visualizer. The companion JSON endpoints live in
        # _REGEX_GET_ROUTES (/api/build-tracker/<ed>[/<book>]).
        if path == "/build-tracker" or path == "/build-tracker.html":
            return self._send_html(BUILD_TRACKER_HTML)

        # ρ.3 Phase C2 — /build-my-bible: the hierarchical-customization
        # Navigator Console. Builders walk an edition like a Bible
        # (book → chapter → verse) and tune note symbols + popup
        # languages at every level. The lazy 3-level JSON feed lives in
        # _REGEX_GET_ROUTES (/api/build-my-bible/<ed>[/<book>[/<ch>]]).
        if path == "/build-my-bible" or path == "/build-my-bible.html":
            return self._send_html(BUILD_MY_BIBLE_HTML)
        # ω.35-A.3 — /api/preflight migrated to _SIMPLE_GET_ROUTES.

        # Corpus progress widget (Phase ψ.3) — read-only feed for
        # the every-console progress bar. Cheap; composes the
        # already-cached api_attribution_audit.

        # Phase ω.0.2 — scaffolded route for /ops
        if path == "/ops" or path == "/ops.html":
            return self._send_html(OPS_HTML)
        # Phase ψ.6 — operator dashboard data feed
        # ω.35-A.3 — /api/ops migrated to _SIMPLE_GET_ROUTES.

        # Phase ω.0.2 — scaffolded route for /apihelp
        if path == "/apihelp" or path == "/apihelp.html":
            return self._send_html(APIHELP_HTML)

        # γ.1 — Hebrew interlinear console (Strong's Hebrew lookup).
        # The JSON endpoint /api/hebrew/<num> is in _REGEX_GET_ROUTES.
        if path == "/hebrew" or path == "/hebrew.html":
            return self._send_html(HEBREW_HTML)

        # γ.2 — Greek interlinear console (Strong's Greek lookup).
        # The JSON endpoint /api/greek/<num> is in _REGEX_GET_ROUTES.
        if path == "/greek" or path == "/greek.html":
            return self._send_html(GREEK_HTML)
        # Phase ω.3 — API reference data feed (auto-generated)
        # ω.35-A.3 — /api/apihelp + /api/corpus-progress migrated to _SIMPLE_GET_ROUTES.

        # Cover console (Phase π.4-B UI). The image-upload flow lives
        # in do_POST; this route just serves the page shell.
        if path == "/covers" or path == "/covers.html":
            return self._send_html(COVERS_HTML)

        # mint-6 — /distribution console: re-surfaces the free-distribution UI
        # (archive.org upload + press kits) the deleted /exec console once hosted.
        if path == "/distribution" or path == "/distribution.html":
            return self._send_html(DISTRIBUTION_HTML)

        # Web favicon — serves the multi-resolution program icon
        # (.ico embedding 16/32/48/64/128/256 sizes) for browser
        # tabs + bookmarks. Sourced from assets/icons/ (publisher's
        # icon pack, ingested 2026-05-11). 24-hour public cache so
        # the browser doesn't re-fetch on every console nav.
        # See assets/icons/README.md for the full icon catalog.
        if path == "/favicon.ico":
            ico_path = REPO / "assets" / "icons" / "program_icon.ico"
            if not ico_path.is_file():
                return self._send_json({"error": "favicon missing"}, status=404)
            try:
                data = ico_path.read_bytes()
            except OSError:
                return self._send_json({"error": "favicon unreadable"}, status=404)
            self.send_response(200)
            self.send_header("Content-Type", "image/x-icon")
            self.send_header("Content-Length", str(len(data)))
            # Public cache OK — favicon is static + non-sensitive.
            self.send_header("Cache-Control", "public, max-age=86400")
            self._send_security_headers()
            self.end_headers()
            self.wfile.write(data)
            return

        # ψ.34 — static-asset route for the matrix console JS bundle.
        # Lives at scripts/templates/matrix_app.js after extraction
        # from the inline <script> block of MATRIX_HTML. Read-only;
        # served with `application/javascript`, the project security
        # headers, and a 5-minute private cache so navigations
        # between consoles don't re-fetch.
        if path == "/static/matrix.js":
            js_path = REPO / "scripts" / "templates" / "matrix_app.js"
            if not js_path.is_file():
                return self._send_json({"error": "not found"}, status=404)
            try:
                data = js_path.read_bytes()
            except OSError:
                return self._send_json({"error": "not found"}, status=404)
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "private, max-age=300")
            self._send_security_headers()
            self.end_headers()
            self.wfile.write(data)
            return

        # Static cover-image serving so the /covers UI can render
        # thumbnails. Sandboxed to content/covers/ ; any path that
        # tries to escape (.., absolute, hidden) is rejected with 404.
        # Read-only — uploads go through POST /api/covers/...
        if path.startswith("/content/covers/"):
            # ξ.2 — sandbox via shared safe_path helper. The string
            # after the route prefix is treated as a path RELATIVE
            # TO content/covers/.
            rel = path[len("/content/covers/") :]
            from scripts.core.safe_path import (
                SafePathError,
                resolve_under,
            )

            covers_root = REPO / "content" / "covers"
            try:
                file_path = resolve_under(covers_root, rel)
            except SafePathError:
                # 403/404-equivalent — don't disclose which check
                # failed. The §9 route-recipe convention.
                return self._send_json({"error": "forbidden"}, status=403)
            if not file_path.is_file():
                return self._send_json({"error": "not found"}, status=404)
            return self._send_file(file_path)

        # ε.7 — press-kit ZIP download. Returns binary (zipfile bytes)
        # so it can't go through the JSON-shaped route tables. Lives in
        # the legacy cascade by design.
        m = re.match(r"^/api/press-kit/([a-z0-9-]+)/download$", path)
        if m:
            result = build_press_kit_zip(m.group(1))
            if isinstance(result, tuple):
                filename, body = result
                return self._send_zip(filename, body)
            # Error envelope dict — JSON-translate via the standard helper.
            return _dispatch_table_result(self, result)

        m = re.match(r"^/api/notes/([a-z0-9]+)$", path)
        if m:
            return self._send_json(api_notes(m.group(1)))

        m = re.match(r"^/api/template/([\w-]+)$", path)
        if m:
            return self._send_json(api_template(m.group(1)))

        # ψ.7-B — list edition starter-pack templates
        # ω.35-A.3 — /api/edition-templates migrated to _SIMPLE_GET_ROUTES.

        # ψ.1.0 — live one-chapter preview
        # /api/preview/<edition>/<book>/<chapter>?translation=<id>
        m = re.match(
            r"^/api/preview/([a-z0-9-]+)/([a-z0-9]+)/(\d+)$",
            path,
        )
        if m:
            from urllib.parse import parse_qs, urlparse

            edition_id = m.group(1)
            book_code = m.group(2)
            try:
                chapter_int = int(m.group(3))
            except ValueError:
                return self._send_json(
                    {"error": "invalid_chapter"},
                    status=400,
                )
            qs = parse_qs(urlparse(self.path).query)
            translation_id = (qs.get("translation") or ["kjv"])[0]
            result = api_preview(
                edition_id,
                book_code,
                chapter_int,
                translation_id=translation_id,
            )
            if result.get("status") == "ok":
                return self._send_json(result)
            http_code = result.get("http") or 500
            return self._send_json(
                {
                    "error": result.get("code") or "internal_error",
                    "message": result.get("message") or "",
                },
                status=http_code,
            )

        self._send_json({"error": "not found", "path": path}, status=404)

    @_safe_request
    def do_PUT(self):
        if not self._check_admin_auth():
            return
        # ω.35-A.5/A.10 — table-driven dispatch for uniform-shape
        # PUT routes (regex → read body → call handler →
        # _dispatch_table_result → send_json). After A.10 the table
        # covers 9 of 10 PUT routes; the 3 remaining bespoke routes
        # below have semantically-distinct response shapes that
        # don't fit the standard helper:
        #   - /api/export/build/<id> uses HTTP 500 on build failure
        #     (server-side build error, not bad input)
        #   - /api/build-all uses HTTP 500 only when ALL editions
        #     fail (custom `success_count > 0` check; partial-ok
        #     is a real 200 outcome)
        #   - /api/edition-meta/<id>/preview uses a bare `"error"`
        #     key (no status/ok discriminator) — the helper can't
        #     distinguish error from success without additional
        #     introspection
        # Adapting them would require either modifying the API
        # functions' return shape (risky — UI may depend on the
        # current shape) or a wrapper helper per route (adds a
        # layer without saving meaningful code). Pinned bespoke.
        for regex, handler in _PUT_ROUTES:
            m = regex.match(self.path)
            if m:
                try:
                    payload = self._read_body()
                    result = handler(m, payload)
                    return _dispatch_table_result(self, result)
                except Exception as e:
                    return self._send_json({"error": str(e)}, status=400)
        # Bespoke #1 — Build edition (Phase σ.2). 500 on build
        # failure (not 400 — build is a server-side operation).
        m = re.match(r"^/api/export/build/([a-z0-9-]+)$", self.path)
        if m:
            try:
                payload = self._read_body()
                version = (payload or {}).get("version", "v28a")
                # W4.2 — hard concurrent-build cap: reject (409) rather than
                # start a second heavy in-process build on this single-user
                # desktop app. The internal per-edition builds inside
                # build-all don't re-enter the gate (it's request-scoped).
                try:
                    with build_gate.build_slot():
                        result = api_export_build(m.group(1), version=version)
                except build_gate.BuildBusyError:
                    return self._send_json(
                        {
                            "error": "build_in_progress",
                            "message": "A build is already running. Wait for it to finish before starting another.",
                        },
                        status=409,
                    )
                status = 200 if result.get("ok") else 500
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Bespoke #2 — Build all editions (Phase ω.2). 500 only
        # when ALL editions fail; partial success is a real 200.
        if self.path == "/api/build-all":
            try:
                payload = self._read_body() or {}
                version = payload.get("version", "v28a")
                # W4.2 — one gate slot for the whole batch (build-all builds
                # editions sequentially internally), so a concurrent single
                # build or a second build-all is rejected with 409.
                try:
                    with build_gate.build_slot():
                        result = api_build_all_editions(version=version)
                except build_gate.BuildBusyError:
                    return self._send_json(
                        {
                            "error": "build_in_progress",
                            "message": "A build is already running. Wait for it to finish before starting another.",
                        },
                        status=409,
                    )
                status = 200 if result.get("success_count", 0) > 0 else 500
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Bespoke #3 — Edition metadata change-impact preview
        # (Phase ν.5). Returns either a bare diff dict (success)
        # or `{"error": "..."}` (failure) — no status/ok marker.
        m = re.match(r"^/api/edition-meta/([a-z0-9-]+)/preview$", self.path)
        if m:
            try:
                payload = self._read_body()
                result = api_preview_edition_changes(m.group(1), payload)
                status = 200 if "error" not in result else 400
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # ω.35-A.10 — /api/edition-meta/<id>, /api/edition/<id>/
        # note-toggle, /api/editions/from-template migrated to
        # _PUT_ROUTES (above). /api/publisher/<id> was migrated
        # in A.5; the dead-code block previously kept for diff-
        # cleanliness has been deleted in A.10.
        return self._send_json({"error": "not found"}, status=404)

    @_safe_request
    def do_DELETE(self):
        if not self._check_admin_auth():
            return
        # ω.35-A.6/A.8 — table-driven dispatch for ALL 6 DELETE routes
        # (regex → handler(m) → _dispatch_table_result → send_json).
        # /api/sources/cache/<id> joined the table in A.8 once
        # _dispatch_table_result was extended to preserve extras in
        # error envelopes.
        for regex, handler in _DELETE_ROUTES:
            m = regex.match(self.path)
            if m:
                try:
                    result = handler(m)
                    return _dispatch_table_result(self, result)
                except Exception as e:
                    return self._send_json({"error": str(e)}, status=400)
        return self._send_json({"error": "not found"}, status=404)

    @_safe_request
    def do_POST(self):
        if not self._check_admin_auth():
            return
        # ω.35-A.7 — POST route-table dispatch. Covers:
        #   /api/snapshots/<ed>/<ver>/restore (no payload)
        #   /api/snapshots/<ed>               (create)
        #   /api/matrix/apply-kind-to-all
        #   /api/scenarios/_import
        #   /api/editions/clone
        #   /api/backups/restore
        # Body is read once here; routes that don't need a payload
        # (snapshot restore) accept the {} default. Any read failure
        # before pattern-match is a 400.
        payload: dict | None = None
        for pattern, handler in _POST_ROUTES:
            m = pattern.match(self.path)
            if not m:
                continue
            if payload is None:
                try:
                    payload = self._read_body() or {}
                except Exception as e:
                    return self._send_json({"error": str(e)}, status=400)
            return _dispatch_table_result(self, handler(m, payload))
        # ω.16 routes migrated to _POST_ROUTES (ω.35-A.7).
        # ψ.26 + ψ.27 routes migrated to _POST_ROUTES (ω.35-A.7).
        # ν.4 + ω.1 routes migrated to _POST_ROUTES (ω.35-A.7).
        # Source cache fetch routes (Phase υ.1) migrated to
        # _POST_ROUTES (ω.35-A.8) — `_dispatch_table_result` now
        # preserves extras in error envelopes, so the legacy
        # `_send_dict_result` behavior is preserved.
        # ω.35-A.9 — multipart POST routes (covers main, covers
        # book, sources cache upload) dispatched via
        # `_MULTIPART_ROUTES` with a per-route size cap.
        for pattern, max_bytes, handler in _MULTIPART_ROUTES:
            m = pattern.match(self.path)
            if m:
                return _dispatch_multipart_route(self, m, max_bytes, handler)
        # Everything else: same as PUT — front-end uses POST for create
        return self.do_PUT()


def _warm_corpus_index() -> dict:
    """Δ.9 — pre-build the derived corpus_index before the server
    starts handling requests so the first call doesn't pay the
    ~5s rebuild cost (51K notes × per-file parse). When the
    fingerprint already matches an existing on-disk index this is
    a fast no-op (sub-50ms — just a stat-walk + cached fingerprint
    compare).

    Best-effort: any failure logs a warning and returns a sentinel
    dict but does NOT propagate. The server should still start
    even if the index can't be built — first-request callers will
    fall back to file-walk paths and the next operator run can
    diagnose.

    Returns the rebuild() result dict (or `{"rebuilt": False,
    "error": str}` on failure) for callers that want to log the
    outcome themselves.
    """
    try:
        from scripts.core import corpus_index

        t0 = time.perf_counter()
        result = corpus_index.rebuild()
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        note_count = result.get("note_count", 0)
        if result.get("rebuilt"):
            print(f"  corpus_index: warmed ({note_count} notes, {elapsed_ms}ms)")
        else:
            print(f"  corpus_index: already fresh ({note_count} notes, {elapsed_ms}ms)")
        return result
    except Exception as exc:  # noqa: BLE001 — best-effort hook; never block server start
        print(f"  corpus_index: warm-up failed, will rebuild on first request: {exc}")
        return {"rebuilt": False, "error": str(exc)}


def main() -> int:
    p = argparse.ArgumentParser(description="Local web UI for the YHWH Ya' Way note corpus.")
    p.add_argument("--host", default="127.0.0.1", help="bind address (default: 127.0.0.1, localhost-only)")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-browser", action="store_true", help="don't auto-open the browser")
    args = p.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}/"
    print("\n  YHWH Ya' Way web — note editor")
    print(f"  serving at: {url}")
    print("  Ctrl-C to stop\n")

    # Δ.9 — pre-build the corpus_index BEFORE the first request
    # so cold-cache cost is paid here, not in a user-visible
    # 5s pause on the first /matrix or /api/search call.
    _warm_corpus_index()

    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopping…")
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())

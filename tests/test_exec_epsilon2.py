"""ε.2 — /exec dashboard MVP pins.

Topic file (created alongside the ε.2 ship). Month 5 #3.
Opens with Δ.15 event log + ε.1 metrics collector as foundation.

Coverage:
- TestEpsilon2ApiDashboard:        `api_exec_dashboard` returns the
  canonical 5-tile payload shape, composes existing aggregators,
  filters AI spend to the current month, sums cost fields correctly,
  surfaces perf budget counts + violations, derives error-rate from
  metrics.summary_kpis().
- TestEpsilon2ExecTemplate:        EXEC_HTML composes the full ζ
  foundation (theme tokens + dark mode + icons + toasts + cmd
  palette markers all substituted at module load), defines five
  KPI tiles with stable data-tile/data-field selectors, recent-
  events table uses textContent (XSS-safe).
- TestEpsilon2RouteRegistration:   /exec HTML route + /api/exec JSON
  route both registered in scripts/web.py's route tables.
- TestEpsilon2CrossLinkPropagated: every existing console's nav now
  includes the /exec link (via the CONSOLES list + HEADER_NAV_LINKS
  substitution).
- TestEpsilon2LintRulesMapped:     `route_for_constant` extended so
  §6.2 cross-link invariant treats /exec like every other console.

Pinning rationale: ε.2 is the first executive-track surface and
the first dashboard to *read* the event log + ε.1 rollups. Drift
in the payload shape would silently break ε.3 (sales import composes
into a 6th tile), ε.4 (per-edition cost rollup expands the AI tile),
and ε.5 (quarterly auto-report consumes this exact dict). Pin each
contract piece explicitly so future changes are intentional.

All tests that touch the event log use monkeypatch isolation in
tmp_path so production events.jsonl stays untouched.
"""

from __future__ import annotations

from datetime import datetime, timezone


def _isolate_event_log(monkeypatch, tmp_path):
    """Redirect the event_log module to a tmp file."""
    from scripts.core import event_log

    log_path = tmp_path / "events.jsonl"
    monkeypatch.setattr(event_log, "_event_log_path", lambda: log_path)
    return log_path


class TestEpsilon2ApiDashboard:
    """`api_exec_dashboard` payload shape + composition."""

    def test_payload_shape(self, monkeypatch, tmp_path):
        from scripts.api.exec import api_exec_dashboard

        _isolate_event_log(monkeypatch, tmp_path)
        result = api_exec_dashboard()
        assert result["status"] == "ok"
        tiles = result["tiles"]
        # Five tiles, all keys stable for downstream consumers.
        assert set(tiles.keys()) == {
            "editions",
            "notes_corpus",
            "ai_spend_mtd",
            "perf_budget_health",
            "error_rate",
        }
        assert "events_total" in result
        assert "recent_events" in result
        assert isinstance(result["recent_events"], list)

    def test_editions_tile_counts_editions(self, monkeypatch, tmp_path):
        from scripts.api.exec import api_exec_dashboard
        from scripts.core import config

        _isolate_event_log(monkeypatch, tmp_path)
        expected = len(config.load_editions())
        result = api_exec_dashboard()
        assert result["tiles"]["editions"]["count"] == expected
        # Sanity: at least one edition shipped in the repo.
        assert expected >= 1

    def test_notes_corpus_tile_composes_audit(self, monkeypatch, tmp_path):
        # Per §9 "compose, don't recompute" — this tile must match
        # api_attribution_audit's count exactly.
        from scripts import web
        from scripts.api.exec import api_exec_dashboard

        _isolate_event_log(monkeypatch, tmp_path)
        audit = web.api_attribution_audit()
        expected = int(audit["counts"]["total"])
        tile = api_exec_dashboard()["tiles"]["notes_corpus"]
        assert tile["current"] == expected
        assert tile["target"] == web.CORPUS_TARGET
        # Percent is current/target * 100, rounded to 2 places.
        assert tile["percent"] == round(expected / web.CORPUS_TARGET * 100.0, 2)

    def test_ai_spend_mtd_zero_when_no_events(self, monkeypatch, tmp_path):
        from scripts.api.exec import api_exec_dashboard

        _isolate_event_log(monkeypatch, tmp_path)
        tile = api_exec_dashboard()["tiles"]["ai_spend_mtd"]
        assert tile["events"] == 0
        assert tile["total_usd"] == 0.0
        assert tile["window_start_iso"].endswith("+00:00")

    def test_ai_spend_mtd_sums_cost_in_window(self, monkeypatch, tmp_path):
        from scripts.core import event_log
        from scripts.api.exec import api_exec_dashboard

        _isolate_event_log(monkeypatch, tmp_path)
        # Force "now" to a deterministic point so the month-start
        # window is predictable.
        now = datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Three AI events this month, one before, one non-AI.
        event_log.emit("ai_xref_run", cost=0.10)
        event_log.emit("ai_cover_generate", cost=2.50)
        event_log.emit("ai_xref_run")  # missing cost — counted but $0
        event_log.emit("edition_save", cost=99.0)  # not AI — ignored

        tile = api_exec_dashboard(now=now)["tiles"]["ai_spend_mtd"]
        # All four events were emitted "now" (after month-start);
        # only three are ai_*. The non-AI edition_save is excluded.
        assert tile["events"] == 3
        assert tile["total_usd"] == 2.60

    def test_ai_spend_excludes_events_before_window(self, monkeypatch, tmp_path):
        # Patch _now_iso on event_log so an emit lands in a past
        # month, and confirm the dashboard filters it out.
        from scripts.core import event_log
        from scripts.api.exec import api_exec_dashboard

        _isolate_event_log(monkeypatch, tmp_path)

        # Emit a "past" event by patching the timestamp generator.
        monkeypatch.setattr(event_log, "_now_iso", lambda: "2026-04-15T10:00:00+00:00")
        event_log.emit("ai_xref_run", cost=5.0)
        # Restore real time for the dashboard call.
        monkeypatch.undo()
        _isolate_event_log(monkeypatch, tmp_path)

        now = datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc)
        tile = api_exec_dashboard(now=now)["tiles"]["ai_spend_mtd"]
        # The April event is before May's window-start. Excluded.
        assert tile["events"] == 0
        assert tile["total_usd"] == 0.0

    def test_perf_budget_health_counts_budgets(self, monkeypatch, tmp_path):
        from scripts import perf_budgets
        from scripts.api.exec import api_exec_dashboard

        _isolate_event_log(monkeypatch, tmp_path)
        tile = api_exec_dashboard()["tiles"]["perf_budget_health"]
        assert tile["budgets_defined"] == len(perf_budgets.BUDGETS)
        assert tile["budgets_defined"] >= 1  # sanity
        assert tile["recent_violations"] == 0  # empty log

    def test_perf_budget_violations_count(self, monkeypatch, tmp_path):
        from scripts.core import event_log
        from scripts.api.exec import api_exec_dashboard

        _isolate_event_log(monkeypatch, tmp_path)
        event_log.emit("perf_violation", name="api_matrix.cold", ms=4500)
        event_log.emit("perf_violation", name="api_search", ms=3200)
        event_log.emit("edition_save")  # not a violation
        tile = api_exec_dashboard()["tiles"]["perf_budget_health"]
        assert tile["recent_violations"] == 2

    def test_error_rate_from_build_outcomes(self, monkeypatch, tmp_path):
        from scripts.core import event_log
        from scripts.api.exec import api_exec_dashboard

        _isolate_event_log(monkeypatch, tmp_path)
        # 3 complete, 1 failure → success_rate = 0.75
        for _ in range(3):
            event_log.emit("build_complete", edition_id="catholic-study")
        event_log.emit("build_failure", edition_id="catholic-study")
        tile = api_exec_dashboard()["tiles"]["error_rate"]
        assert tile["failure_count"] == 1
        assert tile["total_terminal"] == 4
        assert tile["success_rate"] == 0.75

    def test_error_rate_zero_with_no_builds(self, monkeypatch, tmp_path):
        from scripts.api.exec import api_exec_dashboard

        _isolate_event_log(monkeypatch, tmp_path)
        tile = api_exec_dashboard()["tiles"]["error_rate"]
        assert tile["failure_count"] == 0
        assert tile["total_terminal"] == 0
        assert tile["success_rate"] == 0.0

    def test_recent_events_capped(self, monkeypatch, tmp_path):
        from scripts.core import event_log
        from scripts.api.exec import api_exec_dashboard

        _isolate_event_log(monkeypatch, tmp_path)
        for i in range(25):
            event_log.emit("test_kind", i=i)
        result = api_exec_dashboard()
        assert len(result["recent_events"]) == 10  # MVP cap
        assert result["events_total"] == 25

    def test_recent_events_newest_last(self, monkeypatch, tmp_path):
        # Pass-through to event_log.tail(); newest at end. The
        # template flips for display, but the API contract is
        # newest-last (matches the file's append order).
        from scripts.core import event_log
        from scripts.api.exec import api_exec_dashboard

        _isolate_event_log(monkeypatch, tmp_path)
        for label in ("first", "second", "third"):
            event_log.emit(label)
        events = api_exec_dashboard()["recent_events"]
        assert events[0]["kind"] == "first"
        assert events[-1]["kind"] == "third"


class TestEpsilon2ExecTemplate:
    """The /exec console template composes the full ζ foundation."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.exec import EXEC_HTML

        cls.html = EXEC_HTML

    def test_is_a_valid_html_doc(self):
        assert self.html.startswith("<!DOCTYPE html>")
        assert "</html>" in self.html

    def test_theme_markers_substituted(self):
        # Every ζ marker is gone — substituted at module load.
        for marker in (
            "<!-- THEME_TOKENS_CSS -->",
            "<!-- DARK_MODE_JS -->",
            "<!-- THEME_ICONS_JS -->",
            "<!-- THEME_TOAST_JS -->",
            "<!-- THEME_CMD_PALETTE_JS -->",
            "<!-- BUYER_ARC_POLISH_CSS -->",
            "<!-- HEADER_NAV_LINKS -->",
        ):
            assert marker not in self.html, f"marker {marker!r} leaked"

    def test_composes_zeta_foundation(self):
        # Pin that the ζ foundation is actually in the rendered HTML
        # (not just substituted into nothing — that would be silent
        # failure mode).
        assert "--color-bg-page" in self.html, "ζ.1 tokens missing"
        assert "window.ebibleTheme" in self.html, "ζ.2 dark-mode API missing"
        assert "window.ebibleIcons" in self.html, "ζ.5 icons API missing"
        assert "window.ebibleToast" in self.html, "ζ.6 toast API missing"
        assert "window.ebibleCmdPalette" in self.html, "ζ.8 palette API missing"
        assert "theme-text-2xl" in self.html, "ζ.4 typography missing"

    def test_five_kpi_tiles_present(self):
        for tile in (
            "editions",
            "notes_corpus",
            "ai_spend_mtd",
            "perf_budget_health",
            "error_rate",
        ):
            assert f'data-tile="{tile}"' in self.html, f"tile {tile} missing"

    def test_calls_api_exec_endpoint(self):
        assert "/api/exec" in self.html, "JS doesn't reference the JSON endpoint"

    def test_events_table_uses_textcontent(self):
        # XSS guard — event payloads inserted via textContent so any
        # future event field containing a malicious sequence stays
        # safe by construction.
        assert "tdKind.textContent" in self.html
        assert "tdDetail.textContent" in self.html
        assert "tdWhen.textContent" in self.html

    def test_corpus_progress_widget_present(self):
        # Every console has the corpus-progress chip; pin it.
        assert 'id="corpus-progress"' in self.html
        assert "/api/corpus-progress" in self.html


class TestEpsilon2RouteRegistration:
    """Both routes registered correctly in scripts/web.py."""

    def test_html_route_returns_exec_html(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        src = (repo / "scripts" / "web.py").read_text(encoding="utf-8")
        assert 'if path == "/exec"' in src, "/exec HTML route not in web.py"
        assert "self._send_html(EXEC_HTML)" in src, "/exec route doesn't dispatch EXEC_HTML"

    def test_json_route_in_simple_table(self):
        from scripts import web

        # _SIMPLE_GET_ROUTES is a list of (path_str, callable);
        # confirm api_exec_dashboard is registered at /api/exec.
        routes = {p: h for (p, h) in web._SIMPLE_GET_ROUTES}
        assert "/api/exec" in routes, "/api/exec not in _SIMPLE_GET_ROUTES"
        assert routes["/api/exec"] is web.api_exec_dashboard, "/api/exec route doesn't point at api_exec_dashboard"


class TestEpsilon2CrossLinkPropagated:
    """Adding /exec to CONSOLES must propagate to every console's
    nav via the design-system substitution. The §6.2 cross-link
    invariant linter check enforces this in CI; we pin a sample
    of consoles here as belt-and-braces."""

    def test_exec_in_consoles_list(self):
        from scripts.templates._design import CONSOLES

        routes = {r for (r, _label) in CONSOLES}
        assert "/exec" in routes, "/exec not added to CONSOLES"

    def test_preflight_nav_includes_exec(self):
        from scripts.templates.preflight import PREFLIGHT_HTML

        assert 'href="/exec"' in PREFLIGHT_HTML, (
            "/preflight nav missing /exec link — HEADER_NAV_LINKS substitution didn't propagate"
        )

    def test_apihelp_nav_includes_exec(self):
        from scripts.templates.apihelp import APIHELP_HTML

        assert 'href="/exec"' in APIHELP_HTML

    def test_hebrew_nav_includes_exec(self):
        from scripts.templates.hebrew import HEBREW_HTML

        assert 'href="/exec"' in HEBREW_HTML

    def test_greek_nav_includes_exec(self):
        from scripts.templates.greek import GREEK_HTML

        assert 'href="/exec"' in GREEK_HTML

    def test_exec_self_includes_all_other_consoles(self):
        # The reverse direction: /exec's own nav must include every
        # other console (cross-link invariant).
        from scripts.templates._design import CONSOLES
        from scripts.templates.exec import EXEC_HTML

        for route, _label in CONSOLES:
            if route == "/exec":
                continue  # self-link styled differently
            # /matrix is aliased to / per the §6.2 pre-existing
            # exception — accept either.
            if route == "/matrix":
                assert ('href="/matrix"' in EXEC_HTML) or ('href="/"' in EXEC_HTML), (
                    "/exec nav missing matrix-cluster link"
                )
                continue
            assert f'href="{route}"' in EXEC_HTML, f"/exec nav missing link to {route}"


class TestEpsilon2LintRulesMapped:
    """`route_for_constant` in scripts/lint_rules.py knows about
    EXEC_HTML so the §6.2 cross-link invariant check treats it
    like every other console."""

    def test_exec_html_in_route_table(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        src = (repo / "scripts" / "lint_rules.py").read_text(encoding="utf-8")
        assert '"EXEC_HTML": "/exec"' in src, "lint_rules.route_for_constant missing EXEC_HTML mapping"

"""mint-6 — /distribution console tests.

The /distribution console re-surfaces the free-distribution UI (archive.org
upload + press-kit editing/download + the per-edition channel rollup) that the
deleted /exec console once hosted. The archive.org / press-kit endpoints were
already wired; this adds the rollup API + the console page + cross-links.

Run with PYTHONUTF8=1 + PYTHONPATH=<repo>.
"""

from scripts.api.distribution import api_distribution_rollup


class TestApiDistributionRollup:
    def test_rollup_ok_shape(self):
        r = api_distribution_rollup()
        assert r["status"] == "ok"
        for k in ("channels", "editions", "by_channel_coverage", "overall"):
            assert k in r

    def test_rollup_channels_are_free_only(self):
        r = api_distribution_rollup()
        ids = {c["id"] for c in r["channels"]}
        # Phase 4 dropped every commercial channel — only the free surfaces remain.
        assert ids <= {"archive_org", "own_site"}, ids

    def test_rollup_lists_every_edition(self):
        from scripts.core import config

        r = api_distribution_rollup()
        assert len(r["editions"]) == len(config.load_editions())

    def test_rollup_error_path_returns_error_dict(self, monkeypatch):
        from scripts.core import distribution

        def boom(*a, **k):
            raise RuntimeError("boom")

        monkeypatch.setattr(distribution, "rollup", boom)
        r = api_distribution_rollup()
        assert r["status"] == "error"
        assert r["http"] == 500
        assert "boom" in r["message"]


class TestDistributionConsoleTemplate:
    def test_html_renders_with_markers(self):
        from scripts.templates.distribution import DISTRIBUTION_HTML

        assert isinstance(DISTRIBUTION_HTML, str)
        assert len(DISTRIBUTION_HTML) > 1000
        assert "<title>" in DISTRIBUTION_HTML
        for needle in (
            '"/distribution"',  # self-link in nav
            '"/covers"',  # cross-link
            '"/sources"',  # cross-link
            "/api/distribution/rollup",  # rollup JS call
            "/api/archive-org/status",  # status JS call
            "/api/archive-org/upload/",  # upload JS call
            "/api/press-kit/",  # press-kit JS calls
            "ebible-error-banner",  # ω.0.6 defense prelude present
        ):
            assert needle in DISTRIBUTION_HTML, needle

    def test_no_commercial_surfaces(self):
        from scripts.templates.distribution import DISTRIBUTION_HTML

        low = DISTRIBUTION_HTML.lower()
        for banned in ("isbn", "onix", "license_key", "print_cover", "kdp", "royalty", "apple books", "google play"):
            assert banned not in low, banned

    def test_design_markers_substituted(self):
        # apply_design_system ran at module load — no raw placeholders left.
        from scripts.templates.distribution import DISTRIBUTION_HTML

        assert "<!-- HEADER_NAV_LINKS -->" not in DISTRIBUTION_HTML
        assert "OMEGA_PRELUDE_PLACEHOLDER" not in DISTRIBUTION_HTML


class TestDistributionWiring:
    def test_rollup_wired_for_error_translation(self):
        # In _REGEX_GET_ROUTES (dispatched via _dispatch_table_result) so the
        # adapter's {status:error, http:500} envelope maps to a real HTTP 500
        # — unlike the always-200 _SIMPLE_GET_ROUTES handlers.
        from scripts.web import _REGEX_GET_ROUTES

        assert any(p.pattern == r"^/api/distribution/rollup$" for p, _ in _REGEX_GET_ROUTES)

    def test_distribution_html_on_web_module(self):
        from scripts import web

        assert isinstance(web.DISTRIBUTION_HTML, str)

    def test_distribution_registered_in_consoles(self):
        from scripts.templates._design import CONSOLES

        assert ("/distribution", "distribution") in CONSOLES

    def test_distribution_in_route_for_constant(self):
        import inspect

        from scripts import lint_rules

        src = inspect.getsource(lint_rules.check_cross_link_invariant)
        assert "DISTRIBUTION_HTML" in src
        assert '"/distribution"' in src

    def test_cross_link_invariant_passes(self):
        from scripts import lint_rules

        r = lint_rules.check_cross_link_invariant()
        assert r["status"] == "pass", r["violations"]

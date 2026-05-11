"""ω.47 — SonarCloud preflight gate pins.

Topic file (created alongside the ω.47 ship, follows the ω.27
follow-on convention).

Coverage:
- TestOmega47SonarProjectProperties:  sonar-project.properties shape.
- TestOmega47CheckQualityGateUnit:    pure-function status mapping
  (each `projectStatus.status` branch + every error path).
- TestOmega47CheckQualityGateCli:     argparse main() exit-code map.
- TestOmega47PreflightWired:          /preflight surface includes the
  new check + degrades gracefully when sonar CLI unavailable.

Pinning rationale: the SonarCloud gate is the project's only
external-quality signal. Drift in the wire-up is silent (the
dashboard keeps rendering, but the new check would just disappear)
— pin each contract piece explicitly so a future refactor surfaces
the loss at test time, not at the next ω-cluster audit.
"""

from __future__ import annotations

import json


class TestOmega47SonarProjectProperties:
    """sonar-project.properties is the only authoritative source
    for projectKey + organization. Pin its shape so a future tweak
    can't silently break the preflight check or a SonarScanner run."""

    @classmethod
    def setup_class(cls):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        cls.path = repo / "sonar-project.properties"
        cls.text = cls.path.read_text(encoding="utf-8")
        # Parse the same way scripts/check_sonarqube.py does (simple
        # key=value, # comments, backslash-newline continuations).
        cls.cfg = {}
        folded = cls.text.replace("\\\n", "")
        for raw in folded.splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            cls.cfg[key.strip()] = value.strip()

    def test_file_exists(self):
        assert self.path.is_file()

    def test_has_organization(self):
        assert self.cfg.get("sonar.organization") == "bridge4kaladin-collab"

    def test_has_project_key(self):
        # SonarCloud convention: <org>_<github-repo-name>.
        assert self.cfg.get("sonar.projectKey") == "bridge4kaladin-collab_yhwh-bible-platform"

    def test_has_project_name(self):
        assert self.cfg.get("sonar.projectName")

    def test_sources_is_scripts(self):
        # Only the Python production tree is analyzed —
        # content/notes/*.py is data, kings_session/ is legacy.
        assert self.cfg.get("sonar.sources") == "scripts"

    def test_tests_is_tests(self):
        assert self.cfg.get("sonar.tests") == "tests"

    def test_exclusions_cover_regenerables_and_legacy(self):
        excl = self.cfg.get("sonar.exclusions", "")
        for required in (
            "__pycache__",
            "content/notes",  # data files
            "kings_session",  # legacy
            "source_archive",  # legacy
            "epub_working",
            "exports",
            "builds",
            ".backups",
        ):
            assert required in excl, f"exclusions missing {required!r}: {excl!r}"

    def test_python_version_covers_matrix_floor(self):
        # CI matrix tests 3.10–3.14; the properties file must declare
        # those so SonarCloud's analyzer chooses the right grammar.
        versions = self.cfg.get("sonar.python.version", "")
        assert "3.10" in versions, f"sonar.python.version missing 3.10: {versions!r}"

    def test_scm_provider_is_git(self):
        assert self.cfg.get("sonar.scm.provider") == "git"

    def test_source_encoding_is_utf8(self):
        # Pin UTF-8 because the project memory pin (PYTHONUTF8=1)
        # only covers the Python runtime — SonarCloud's analyzer
        # needs its own encoding hint.
        assert self.cfg.get("sonar.sourceEncoding") == "UTF-8"


class TestOmega47CheckQualityGateUnit:
    """check_quality_gate() returns a dict whose `status` reflects
    every branch of the upstream SonarCloud API contract.
    Mock-based: doesn't touch the network."""

    def test_returns_skip_when_props_missing(self, monkeypatch, tmp_path):
        from scripts import check_sonarqube

        # Point the module at a non-existent path.
        monkeypatch.setattr(check_sonarqube, "PROPS_PATH", tmp_path / "missing.properties")
        result = check_sonarqube.check_quality_gate()
        assert result["status"] == "skip"
        assert "missing" in result["message"].lower() or "no sonar.projectKey" in result["message"]

    def test_returns_skip_when_props_lacks_project_key(self, monkeypatch, tmp_path):
        from scripts import check_sonarqube

        props = tmp_path / "sonar-project.properties"
        props.write_text("sonar.organization=foo\n", encoding="utf-8")
        monkeypatch.setattr(check_sonarqube, "PROPS_PATH", props)
        result = check_sonarqube.check_quality_gate()
        assert result["status"] == "skip"

    def test_returns_skip_when_sonar_cli_missing(self, monkeypatch, tmp_path):
        from scripts import check_sonarqube

        props = tmp_path / "sonar-project.properties"
        props.write_text(
            "sonar.organization=org\nsonar.projectKey=org_repo\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(check_sonarqube, "PROPS_PATH", props)
        monkeypatch.setattr(check_sonarqube, "_sonar_cli_available", lambda: False)
        result = check_sonarqube.check_quality_gate()
        assert result["status"] == "skip"
        assert "sonar CLI" in result["message"] or "sonar cli" in result["message"].lower()

    def _patch_fetch(self, monkeypatch, outcome, payload=None, err=None):
        from scripts import check_sonarqube

        # Force config + CLI to "available" for the fetch path.
        monkeypatch.setattr(check_sonarqube, "_sonar_cli_available", lambda: True)

        def fake_load_config():
            return {"sonar.projectKey": "org_repo", "sonar.organization": "org"}

        monkeypatch.setattr(check_sonarqube, "_load_project_config", fake_load_config)
        monkeypatch.setattr(
            check_sonarqube,
            "_fetch_quality_gate",
            lambda *a, **kw: (outcome, payload, err),
        )

    def test_pass_on_ok_gate(self, monkeypatch):
        from scripts import check_sonarqube

        self._patch_fetch(
            monkeypatch,
            "ok",
            payload={
                "projectStatus": {
                    "status": "OK",
                    "conditions": [{"metricKey": "coverage", "status": "OK"}],
                }
            },
        )
        result = check_sonarqube.check_quality_gate()
        assert result["status"] == "pass"
        assert "OK" in result["message"]

    def test_fail_on_error_gate(self, monkeypatch):
        from scripts import check_sonarqube

        self._patch_fetch(
            monkeypatch,
            "ok",
            payload={
                "projectStatus": {
                    "status": "ERROR",
                    "conditions": [
                        {"metricKey": "coverage", "status": "ERROR"},
                        {"metricKey": "bugs", "status": "OK"},
                    ],
                }
            },
        )
        result = check_sonarqube.check_quality_gate()
        assert result["status"] == "fail"
        assert "coverage" in result["details"]["failed_conditions"]

    def test_warn_on_warn_gate(self, monkeypatch):
        from scripts import check_sonarqube

        self._patch_fetch(
            monkeypatch,
            "ok",
            payload={"projectStatus": {"status": "WARN", "conditions": []}},
        )
        result = check_sonarqube.check_quality_gate()
        assert result["status"] == "warn"

    def test_warn_on_none_gate(self, monkeypatch):
        # NONE = project exists but never scanned. Graceful warn so
        # the dashboard tells the operator what to do next instead of
        # failing the gate before any scan has run.
        from scripts import check_sonarqube

        self._patch_fetch(
            monkeypatch,
            "ok",
            payload={"projectStatus": {"status": "NONE"}},
        )
        result = check_sonarqube.check_quality_gate()
        assert result["status"] == "warn"
        assert "no SonarCloud analysis" in result["message"] or "sonar-scanner" in result["message"]

    def test_warn_on_404_unknown_project(self, monkeypatch):
        # SonarCloud returns 404 for unknown projects — operator
        # hasn't created it on the SonarCloud side yet.
        from scripts import check_sonarqube

        self._patch_fetch(monkeypatch, "api-error", err="404 Not Found: project does not exist")
        result = check_sonarqube.check_quality_gate()
        assert result["status"] == "warn"
        assert "not yet created" in result["message"]

    def test_fail_on_other_api_error(self, monkeypatch):
        from scripts import check_sonarqube

        self._patch_fetch(monkeypatch, "api-error", err="500 Internal Server Error")
        result = check_sonarqube.check_quality_gate()
        assert result["status"] == "fail"

    def test_warn_on_timeout(self, monkeypatch):
        from scripts import check_sonarqube

        self._patch_fetch(monkeypatch, "timeout", err="request timed out after 30s")
        result = check_sonarqube.check_quality_gate()
        assert result["status"] == "warn"

    def test_warn_on_parse_error(self, monkeypatch):
        from scripts import check_sonarqube

        self._patch_fetch(monkeypatch, "parse-error", err="<html>...</html>")
        result = check_sonarqube.check_quality_gate()
        assert result["status"] == "warn"


class TestOmega47CheckQualityGateCli:
    """main() returns exit codes that match the other audit scripts'
    conventions (audit_deps.py, audit_dead_code.py, etc.):
        pass → 0, fail → 1, warn / skip → 2."""

    def test_main_returns_0_on_pass(self, monkeypatch, capsys):
        from scripts import check_sonarqube

        monkeypatch.setattr(
            check_sonarqube,
            "check_quality_gate",
            lambda: {"status": "pass", "message": "OK", "details": {}},
        )
        assert check_sonarqube.main([]) == 0

    def test_main_returns_1_on_fail(self, monkeypatch, capsys):
        from scripts import check_sonarqube

        monkeypatch.setattr(
            check_sonarqube,
            "check_quality_gate",
            lambda: {"status": "fail", "message": "ERROR", "details": {}},
        )
        assert check_sonarqube.main([]) == 1

    def test_main_returns_2_on_warn(self, monkeypatch, capsys):
        from scripts import check_sonarqube

        monkeypatch.setattr(
            check_sonarqube,
            "check_quality_gate",
            lambda: {"status": "warn", "message": "NONE", "details": {}},
        )
        assert check_sonarqube.main([]) == 2

    def test_main_returns_2_on_skip(self, monkeypatch, capsys):
        from scripts import check_sonarqube

        monkeypatch.setattr(
            check_sonarqube,
            "check_quality_gate",
            lambda: {"status": "skip", "message": "no config", "details": {}},
        )
        assert check_sonarqube.main([]) == 2

    def test_main_json_flag_emits_valid_json(self, monkeypatch, capsys):
        from scripts import check_sonarqube

        monkeypatch.setattr(
            check_sonarqube,
            "check_quality_gate",
            lambda: {"status": "pass", "message": "OK", "details": {"x": 1}},
        )
        check_sonarqube.main(["--json"])
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["status"] == "pass"
        assert parsed["details"] == {"x": 1}


class TestOmega47PreflightWired:
    """/preflight aggregator must include the SonarCloud check and
    handle every status the upstream check can return — without
    breaking the dashboard when sonar isn't installed."""

    def test_preflight_includes_sonarqube_check(self):
        from scripts.api.preflight import api_preflight

        data = api_preflight()
        ids = {c["id"] for c in data["checks"]}
        assert "sonarqube_quality_gate" in ids, f"preflight missing sonarqube_quality_gate; got {sorted(ids)}"

    def test_sonarqube_check_has_required_shape(self):
        from scripts.api.preflight import api_preflight

        data = api_preflight()
        check = next(c for c in data["checks"] if c["id"] == "sonarqube_quality_gate")
        for required in ("id", "name", "status", "message", "details", "jump_to"):
            assert required in check, f"sonarqube check missing field: {required}"
        # Preflight contract (pinned by TestEditionMeta::
        # test_preflight_returns_structured_checks) requires status
        # to be one of pass/warn/fail (no `skip` — that maps to warn
        # at the wire-up boundary) and details to be a list.
        assert check["status"] in {"pass", "warn", "fail"}, (
            f"preflight `status` must be pass/warn/fail (not skip); got {check['status']!r}"
        )
        assert isinstance(check["details"], list), (
            f"preflight `details` must be a list per the existing contract; got {type(check['details']).__name__}"
        )
        assert isinstance(check["message"], str) and check["message"]

    def test_sonarqube_failure_does_not_break_dashboard(self, monkeypatch):
        # Even if check_sonarqube blows up entirely, the dashboard
        # must keep rendering — that's the contract every meta-tool
        # in scripts/api/preflight.py shares.
        # Pre-bust the lru_cache so our exception-raising stub runs.
        from scripts.api.preflight import _cached_preflight, api_preflight
        from scripts import check_sonarqube

        def raise_oops():
            raise RuntimeError("oops")

        monkeypatch.setattr(check_sonarqube, "check_quality_gate", raise_oops)
        _cached_preflight.cache_clear()
        try:
            data = api_preflight()
            check = next(c for c in data["checks"] if c["id"] == "sonarqube_quality_gate")
            assert check["status"] == "warn"
            assert "failed to run" in check["message"]
        finally:
            _cached_preflight.cache_clear()

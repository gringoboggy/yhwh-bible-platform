"""W4.5 — tests for the local CI gate orchestrator (scripts/ci.py).

The subprocess runner is injected, so these exercise the composition + verdict
logic (which gates block, which only warn) without spawning real gates."""

from __future__ import annotations


def _all_ok(cmd):
    return (0, "ok")


class TestCIGate:
    def test_standard_aggregator_shape(self):
        from scripts import ci

        r = ci.run_all(runner=_all_ok, coverage_installed=False)
        assert "checks" in r and "summary" in r
        for c in r["checks"]:
            assert set(c) >= {"id", "name", "status", "blocking", "message"}
            assert c["status"] in ("pass", "warn", "fail")
        assert set(r["summary"]) >= {"total", "pass", "warn", "fail", "clean"}

    def test_all_pass_is_clean(self):
        from scripts import ci

        r = ci.run_all(runner=_all_ok, coverage_installed=False)
        assert r["summary"]["clean"] is True
        # coverage absent → non-blocking warn, doesn't spoil clean
        cov = next(c for c in r["checks"] if c["id"] == "coverage")
        assert cov["status"] == "warn" and cov["blocking"] is False

    def test_blocking_failure_makes_it_unclean(self):
        from scripts import ci

        def runner(cmd):
            return (1, "FAIL") if "lint_rules.py" in " ".join(cmd) else (0, "ok")

        r = ci.run_all(runner=runner, coverage_installed=False)
        rules = next(c for c in r["checks"] if c["id"] == "rules")
        assert rules["status"] == "fail" and rules["blocking"] is True
        assert r["summary"]["clean"] is False

    def test_ruff_check_backlog_is_non_blocking(self):
        from scripts import ci

        def runner(cmd):
            # `ruff check .` reports backlog (rc=1) but must NOT block the gate.
            return (1, "backlog") if cmd[-2:] == ["check", "."] else (0, "ok")

        r = ci.run_all(runner=runner, coverage_installed=False)
        lint = next(c for c in r["checks"] if c["id"] == "lint")
        assert lint["status"] == "warn" and lint["blocking"] is False
        assert r["summary"]["clean"] is True

    def test_coverage_floor_enforced_when_installed(self):
        from scripts import ci

        def runner(cmd):
            # coverage report below the floor → rc=1
            return (1, "TOTAL 42%") if ("coverage" in cmd and "report" in cmd) else (0, "ok")

        r = ci.run_all(runner=runner, coverage_installed=True, coverage_floor=60)
        cov = next(c for c in r["checks"] if c["id"] == "coverage")
        assert cov["status"] == "fail" and cov["blocking"] is True
        assert r["summary"]["clean"] is False

    def test_no_tests_skips_tests_and_coverage(self):
        from scripts import ci

        r = ci.run_all(runner=_all_ok, run_tests=False, coverage_installed=True)
        ids = {c["id"] for c in r["checks"]}
        assert "tests" not in ids and "coverage" not in ids
        assert {"format", "lint", "rules", "types"} <= ids

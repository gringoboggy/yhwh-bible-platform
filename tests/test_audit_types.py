"""Tests for scripts/audit_types.py (ω.31 mypy wrapper).

Same shape as `tests/test_audit_dead_code.py` for ω.26 — a meta-tool
that subprocesses mypy + parses output + returns a structured verdict.
"""

from __future__ import annotations


class TestOmega31AuditTypes:
    """ω.31 — type-checking audit wrapper around mypy. Focuses on
    the parser + CLI shape; the live `audit()` call is exercised
    once to verify scripts/core/ + scripts/build_edition.py stay
    type-clean."""

    def setup_method(self, method):
        from scripts.audit_types import mypy_available
        import pytest

        if not mypy_available():
            pytest.skip("mypy not installed; run `pip install mypy` to enforce the type-check audit")

    # ---- parser ----

    def test_parse_standard_error_line(self):
        from scripts.audit_types import _parse_mypy_output

        out = "scripts/web.py:42: error: Some message  [arg-type]\n"
        errors = _parse_mypy_output(out)
        assert len(errors) == 1
        e = errors[0]
        assert e["file"] == "scripts/web.py"
        assert e["line"] == 42
        assert "Some message" in e["message"]
        assert e["code"] == "arg-type"

    def test_parse_error_line_without_code(self):
        from scripts.audit_types import _parse_mypy_output

        out = "scripts/web.py:42: error: A bare error message\n"
        errors = _parse_mypy_output(out)
        assert len(errors) == 1
        assert errors[0]["code"] == ""

    def test_parse_skips_notes(self):
        # Mypy `note:` lines are informational; only `error:` lines
        # surface as findings.
        from scripts.audit_types import _parse_mypy_output

        out = "scripts/x.py:1: note: by default ...\nscripts/x.py:2: error: real error  [misc]\n"
        errors = _parse_mypy_output(out)
        assert len(errors) == 1
        assert errors[0]["line"] == 2

    def test_parse_handles_windows_paths(self):
        from scripts.audit_types import _parse_mypy_output

        out = "scripts\\web.py:42: error: msg  [code]\n"
        assert len(_parse_mypy_output(out)) == 1

    def test_parse_empty_output_returns_empty_list(self):
        from scripts.audit_types import _parse_mypy_output

        assert _parse_mypy_output("") == []
        assert _parse_mypy_output("Success: no issues found in 26 source files\n") == []

    # ---- audit() ----

    def test_audit_clean_state_on_real_tree(self):
        # Pin: scripts/core/ + scripts/build_edition.py stay
        # type-clean. ω.31 v1 ships at this scope; future ω.31.x
        # widens it.
        from scripts.audit_types import audit

        result = audit()
        assert result["ok"] is True, (
            f"unexpected type errors:\nstdout:\n{result['stdout']}\nstderr:\n{result['stderr']}"
        )
        assert result["errors"] == []

    def test_audit_returns_structured_shape(self):
        from scripts.audit_types import audit

        result = audit()
        for key in ("ok", "errors", "stdout", "stderr", "returncode"):
            assert key in result

    # ---- mypy config ----

    def test_pyproject_has_mypy_config(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        text = (repo / "pyproject.toml").read_text(encoding="utf-8")
        assert "[tool.mypy]" in text
        assert "ignore_missing_imports" in text
        # Pin the surface scope so a future contributor doesn't drop
        # scripts/core/ from the check.
        assert "scripts/core" in text

    # ---- CLI ----

    def test_main_clean_returns_0(self, capsys):
        from scripts.audit_types import main

        rc = main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "no type errors" in out

    def test_main_json_output(self, capsys):
        from scripts.audit_types import main
        import json as _json

        rc = main(["--json"])
        out = capsys.readouterr().out
        assert rc == 0
        data = _json.loads(out)
        assert data["ok"] is True
        assert data["errors"] == []

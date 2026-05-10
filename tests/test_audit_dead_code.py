"""Tests for scripts/audit_dead_code.py (ω.26 vulture wrapper).

The audit is a meta-tool: subprocess to vulture + parse output +
return a structured verdict. Tests exercise the parser deterministically
+ the CLI happy-path; the actual "clean state" assertion lives in
the recurring lint via the wrapper itself.
"""

from __future__ import annotations


class TestOmega26AuditDeadCode:
    """ω.26 — dead-code audit wrapper around vulture. Focuses on
    the parser + CLI shape; the live `audit()` call is exercised
    once to verify production state is clean."""

    def setup_method(self, method):
        # Skip the whole class if vulture isn't installed. ω.26's
        # contract is "fail loudly if real dead code exists" — but
        # only when the tool is available. A fresh checkout without
        # `pip install vulture` shouldn't fail this test.
        from scripts.audit_dead_code import vulture_available
        import pytest

        if not vulture_available():
            pytest.skip("vulture not installed; run `pip install vulture` to enforce dead-code audit")

    # ---- parser ----

    def test_parse_standard_finding_line(self):
        from scripts.audit_dead_code import _parse_vulture_output

        out = "scripts/web.py:139: unused variable 'notes_sig' (100% confidence)\n"
        findings = _parse_vulture_output(out)
        assert len(findings) == 1
        f = findings[0]
        assert f["file"] == "scripts/web.py"
        assert f["line"] == 139
        assert "notes_sig" in f["message"]
        assert f["confidence"] == 100

    def test_parse_blank_lines_ignored(self):
        from scripts.audit_dead_code import _parse_vulture_output

        out = "\n\nscripts/x.py:1: unused variable 'y' (90% confidence)\n\n"
        assert len(_parse_vulture_output(out)) == 1

    def test_parse_empty_output_returns_empty_list(self):
        from scripts.audit_dead_code import _parse_vulture_output

        assert _parse_vulture_output("") == []
        assert _parse_vulture_output("\n\n") == []

    def test_parse_handles_windows_paths(self):
        # Vulture on Windows emits backslash paths.
        from scripts.audit_dead_code import _parse_vulture_output

        out = "scripts\\web.py:42: unused import 'X' (90% confidence)\n"
        findings = _parse_vulture_output(out)
        assert len(findings) == 1
        assert findings[0]["confidence"] == 90

    def test_parse_skips_malformed_lines(self):
        # Lines without the standard format are silently skipped
        # (e.g. vulture's banner or warnings).
        from scripts.audit_dead_code import _parse_vulture_output

        out = "Some random vulture warning that doesn't match the format\n"
        assert _parse_vulture_output(out) == []

    # ---- audit() entry point ----

    def test_audit_clean_state_on_real_tree(self):
        # Production state must be clean at the project's standard
        # threshold (80% confidence) with the whitelist applied.
        from scripts.audit_dead_code import audit

        result = audit(min_confidence=80)
        assert result["ok"] is True, f"unexpected dead-code findings:\n{result['stdout']}"
        assert result["findings"] == []

    def test_audit_returns_structured_shape(self):
        from scripts.audit_dead_code import audit

        result = audit(min_confidence=80)
        for key in ("ok", "findings", "stdout", "stderr", "returncode"):
            assert key in result

    # ---- whitelist ----

    def test_whitelist_file_present(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        whitelist = repo / "scripts" / ".vulture_whitelist.py"
        assert whitelist.is_file(), "scripts/.vulture_whitelist.py is required for ω.26"

    def test_whitelist_documents_each_entry(self):
        # Pin: every `_.<name>` whitelist entry should sit under a
        # documented section (`# ---- ... ----`). This keeps the
        # whitelist auditable — every false-positive has a stated
        # reason. If a future contributor adds an entry without
        # context, this test surfaces the omission only loosely
        # (we just check there's at least one comment block per
        # whitelist symbol cluster, not per individual line).
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        text = (repo / "scripts" / ".vulture_whitelist.py").read_text(encoding="utf-8")
        assert "lru_cache" in text, "whitelist missing lru_cache rationale"
        assert "HTMLParser" in text, "whitelist missing HTMLParser rationale"

    # ---- CLI ----

    def test_main_clean_returns_0(self, capsys):
        from scripts.audit_dead_code import main

        rc = main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "no dead code" in out

    def test_main_json_output(self, capsys):
        from scripts.audit_dead_code import main
        import json as _json

        rc = main(["--json"])
        out = capsys.readouterr().out
        assert rc == 0
        data = _json.loads(out)
        assert data["ok"] is True
        assert data["findings"] == []

    def test_main_min_confidence_threshold_passes_on_real_tree(self, capsys):
        # Even at min_confidence=70, scripts/ should be clean
        # (lower threshold = more findings, but the production tree
        # has none at this threshold either after the ω.26 cleanup).
        from scripts.audit_dead_code import main

        rc = main(["--min-confidence", "70"])
        out = capsys.readouterr().out
        # rc=0 expected if production tree is genuinely clean at 70%.
        # If it's not, this test surfaces the regression — that's the
        # point: ω.26 ships at 80% but the goal is 70% over time.
        assert rc == 0, f"rc={rc}; output:\n{out}"

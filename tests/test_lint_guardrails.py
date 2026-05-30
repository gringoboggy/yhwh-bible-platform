"""Tests for the 2026-05-29 mint-audit anti-bloat guardrails in lint_rules.py.

Each guard slots into ``lint_rules.ALL_CHECKS`` so it runs in the pre-commit
gate AND surfaces in /preflight. Guards that are currently *breached* ship at
WARN tier (so they can be committed without blocking) and get promoted to FAIL
in the cleanup phase that makes them satisfiable.
"""

from scripts import lint_rules


class TestTruthRecordBudget:
    def test_warns_when_oversize(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        (tmp_path / "dev" / "SESSION_STATE.md").write_text("➤➤➤\n" * 5 + "x" * 130_000, encoding="utf-8")
        r = lint_rules.check_truth_record_budget()
        assert r["id"] == "truth_record_budget"
        # WARN-tier until Phase 1 rotation promotes the hard ceiling to FAIL.
        assert r["status"] == "warn"
        assert any("SESSION_STATE" in str(v) for v in r["violations"])

    def test_passes_when_within_budget(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        for name in ("SESSION_STATE.md", "IN_FLIGHT.md", "CLAUDE_PROJECT_RULES.md"):
            (tmp_path / "dev" / name).write_text("➤➤➤ current\n" + "x" * 100, encoding="utf-8")
        r = lint_rules.check_truth_record_budget()
        assert r["status"] == "pass"
        assert r["violations"] == []

    def test_registered_in_all_checks(self):
        assert "truth_record_budget" in lint_rules.ALL_CHECKS

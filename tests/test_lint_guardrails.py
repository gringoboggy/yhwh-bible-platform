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


class TestCommercialOrphans:
    def test_warns_when_module_present(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "scripts" / "core").mkdir(parents=True)
        (tmp_path / "scripts" / "core" / "sales.py").write_text("x = 1\n", encoding="utf-8")
        r = lint_rules.check_commercial_orphans()
        assert r["status"] == "warn"
        assert any("sales.py" in v.get("path", "") for v in r["violations"])

    def test_warns_on_import(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "web.py").write_text("from scripts.core.license_key import verify\n", encoding="utf-8")
        r = lint_rules.check_commercial_orphans()
        assert r["status"] == "warn"
        assert any(v.get("kind") == "import" for v in r["violations"])

    def test_passes_when_clean(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "ok.py").write_text("import json\n", encoding="utf-8")
        assert lint_rules.check_commercial_orphans()["status"] == "pass"

    def test_registered(self):
        assert "commercial_orphans" in lint_rules.ALL_CHECKS


class TestChangelogSize:
    def test_warns_when_huge(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        (tmp_path / "dev" / "CHANGELOG.md").write_text("x" * 1_600_000, encoding="utf-8")
        assert lint_rules.check_changelog_size()["status"] == "warn"

    def test_passes_when_small(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        (tmp_path / "dev" / "CHANGELOG.md").write_text("small\n", encoding="utf-8")
        assert lint_rules.check_changelog_size()["status"] == "pass"

    def test_registered(self):
        assert "changelog_size" in lint_rules.ALL_CHECKS


class TestDevDocSprawl:
    def test_warns_when_sprawled(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        dev = tmp_path / "dev"
        dev.mkdir()
        for i in range(45):
            (dev / f"doc{i:02d}.md").write_text("x", encoding="utf-8")
        (dev / "AUDIT_2026-05-10.md").write_text("x", encoding="utf-8")
        r = lint_rules.check_dev_doc_sprawl()
        assert r["status"] == "warn"
        assert any("AUDIT_2026-05-10" in v.get("archive_candidate", "") for v in r["violations"])

    def test_passes_when_lean(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        (tmp_path / "dev" / "RULES.md").write_text("x", encoding="utf-8")
        assert lint_rules.check_dev_doc_sprawl()["status"] == "pass"

    def test_registered(self):
        assert "dev_doc_sprawl" in lint_rules.ALL_CHECKS


class TestRulesNoFrozenStats:
    def test_warns_on_arc_stats(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        (tmp_path / "dev" / "CLAUDE_PROJECT_RULES.md").write_text(
            "γ.4.9 Cyril 48.86% Jubilees 14.63%\nω.41 Ephrem 11.49%\n", encoding="utf-8"
        )
        assert lint_rules.check_rules_no_frozen_stats()["status"] == "warn"

    def test_passes_when_clean(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        (tmp_path / "dev" / "CLAUDE_PROJECT_RULES.md").write_text("Durable rules only.\n", encoding="utf-8")
        assert lint_rules.check_rules_no_frozen_stats()["status"] == "pass"

    def test_registered(self):
        assert "rules_no_frozen_stats" in lint_rules.ALL_CHECKS

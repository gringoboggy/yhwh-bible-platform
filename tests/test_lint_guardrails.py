"""Tests for the 2026-05-29 mint-audit anti-bloat guardrails in lint_rules.py.

Each guard slots into ``lint_rules.ALL_CHECKS`` so it runs in the pre-commit
gate AND surfaces in /preflight. Guards that are currently *breached* ship at
WARN tier (so they can be committed without blocking) and get promoted to FAIL
in the cleanup phase that makes them satisfiable.
"""

from scripts import lint_rules


class TestTruthRecordBudget:
    def test_fails_when_over_hard_ceiling(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        (tmp_path / "dev" / "SESSION_STATE.md").write_text("➤➤➤\n" * 5 + "x" * 130_000, encoding="utf-8")
        r = lint_rules.check_truth_record_budget()
        assert r["id"] == "truth_record_budget"
        # Hard ceiling promoted to FAIL once standing rotation landed (mint 3.1).
        assert r["status"] == "fail"
        assert any("SESSION_STATE" in str(v) for v in r["violations"])

    def test_passes_when_within_budget(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        for name in ("SESSION_STATE.md", "IN_FLIGHT.md", "CLAUDE_PROJECT_RULES.md"):
            (tmp_path / "dev" / name).write_text("➤➤➤ current\n" + "x" * 100, encoding="utf-8")
        r = lint_rules.check_truth_record_budget()
        assert r["status"] == "pass"
        assert r["violations"] == []

    def test_warns_when_too_many_entries(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        # 3 entry-START lines (> max_entries=2), small file. Entry counting must be
        # by entry-start line, not the bare glyph: an entry whose prose mentions
        # the `> **➤➤➤` marker (escaped below) must still count as ONE entry.
        body = "> **➤➤➤ 2026-05-29 — newest, splits on the `> **➤➤➤` marker**\n>\n"
        body += "> **➤➤➤ 2026-05-28 — mid**\n>\n> **➤➤➤ 2026-05-27 — old**\n>\n"
        (tmp_path / "dev" / "SESSION_STATE.md").write_text("# T\n\n" + body, encoding="utf-8")
        r = lint_rules.check_truth_record_budget()
        assert r["status"] == "warn"
        ev = next(v for v in r["violations"] if v.get("tier") == "entries")
        assert ev["entries"] == 3  # not 4 — the prose mention is not double-counted

    def test_inflight_arrow_entries_counted(self, tmp_path, monkeypatch):
        # IN_FLIGHT's entries use the `> **▶` marker (not `> **➤➤➤`) — the lint's
        # entry counter shares the rotator's resolver, so they MUST be visible.
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        body = "".join(f"> **▶ ✅ DONE 2026-06-{d:02d} (🪟 Windows) — e**\n>\n" for d in (10, 9, 8))
        (tmp_path / "dev" / "IN_FLIGHT.md").write_text("# T\n\n" + body, encoding="utf-8")
        r = lint_rules.check_truth_record_budget()
        assert r["status"] == "warn"
        ev = next(v for v in r["violations"] if v.get("tier") == "entries")
        assert ev["entries"] == 3

    def test_lane_handoff_budgeted(self, tmp_path, monkeypatch):
        # LANE_HANDOFF.md is a budgeted truth record (mint 3.3): hard size FAILs,
        # and its `## ` turn sections count as entries (protected sections don't).
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        secs = "".join(f"## ▶ Windows → Mac (turn {t}, 2026-06-10) — h\n\nbody.\n\n" for t in (70, 69, 68))
        secs += "## ⚠ STANDING — both lanes (do NOT rotate this section out of the file)\n\nx\n"
        (tmp_path / "dev" / "LANE_HANDOFF.md").write_text("---\nmode: parallel\n---\n\n" + secs, encoding="utf-8")
        r = lint_rules.check_truth_record_budget()
        ev = next(v for v in r["violations"] if v.get("tier") == "entries" and "LANE_HANDOFF" in str(v))
        assert ev["entries"] == 3  # the protected STANDING section is not an entry
        # Oversize board → hard FAIL.
        (tmp_path / "dev" / "LANE_HANDOFF.md").write_text(
            "---\nmode: parallel\n---\n\n## ▶ t (turn 70, 2026-06-10)\n\n" + "x" * 130_000, encoding="utf-8"
        )
        assert lint_rules.check_truth_record_budget()["status"] == "fail"

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


# ---------------------------------------------------------------------------
# Phase 0 tail (2026-05-29 mint) — commercial_terms / retired_terms /
# triad_plan_consistency / stray_artifacts + the two upgrades.
# ---------------------------------------------------------------------------


class TestCommercialTerms:
    def test_flags_term_in_curated_doc(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        (tmp_path / "dev" / "SESSION_PLAYBOOK.md").write_text("Set the ISBN before upload.\n", encoding="utf-8")
        r = lint_rules.check_commercial_terms()
        # State-aware (RULES §8): FAIL once _ENFORCE_COMMERCIAL is flipped (Phase 4), else WARN.
        assert r["status"] == ("fail" if lint_rules._ENFORCE_COMMERCIAL else "warn")
        assert any(v["term"] == "ISBN" for v in r["violations"])

    def test_waiver_marker_exempts_line(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        (tmp_path / "dev" / "CLAUDE_PROJECT_RULES.md").write_text(
            "No ISBN / ONIX / retail — pivot dropped them. term-ref-ok\n", encoding="utf-8"
        )
        assert lint_rules.check_commercial_terms()["status"] == "pass"

    def test_passes_when_clean(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        (tmp_path / "dev" / "MATRIX_MAP.md").write_text("Durable data-flow only.\n", encoding="utf-8")
        assert lint_rules.check_commercial_terms()["status"] == "pass"

    def test_registered(self):
        assert "commercial_terms" in lint_rules.ALL_CHECKS


class TestRetiredTerms:
    def test_flags_deadline_and_sonar(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        (tmp_path / "dev" / "SESSION_PLAYBOOK.md").write_text(
            "Deadline: 2026-06-07 (hard deadline). Run sonar before ship.\n", encoding="utf-8"
        )
        r = lint_rules.check_retired_terms()
        # FAIL-tier once Phase 2 flipped _ENFORCE_RETIRED_TERMS; WARN before (state-aware, RULES §8).
        assert r["status"] == ("fail" if lint_rules._ENFORCE_RETIRED_TERMS else "warn")
        # The date-rolled "2026-06-07" was retired from _RETIRED_TERMS (it was a
        # one-time roll); only the durable terms remain flaggable.
        assert {v["term"] for v in r["violations"]} >= {"hard deadline", "sonar"}

    def test_passes_when_clean(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        (tmp_path / "dev" / "CLAUDE_PROJECT_RULES.md").write_text("Completeness over speed.\n", encoding="utf-8")
        assert lint_rules.check_retired_terms()["status"] == "pass"

    def test_registered(self):
        assert "retired_terms" in lint_rules.ALL_CHECKS

    def test_retired_edition_skus_registered(self):
        assert "retired_edition_skus" in lint_rules.ALL_CHECKS
        r = lint_rules.check_retired_edition_skus()
        assert r["status"] == "pass"


class TestTriadPlanConsistency:
    def _scaffold(self, root, *, plan_in_rules, plan_in_playbook, plan_live):
        dev = root / "dev"
        (dev / "cc-hooks").mkdir(parents=True)
        plan = "PLAN_2026-05-29-roadmap.md"
        (dev / "cc-hooks" / "bootstrap-triad.ps1").write_text(f"3. dev/{plan} (master sequence)\n", encoding="utf-8")
        (dev / "CLAUDE_PROJECT_RULES.md").write_text(
            f"§0 read dev/{plan}\n" if plan_in_rules else "§0 read the plan\n", encoding="utf-8"
        )
        (dev / "SESSION_PLAYBOOK.md").write_text(
            f"triad: dev/{plan}\n" if plan_in_playbook else "triad: the plan\n", encoding="utf-8"
        )
        if plan_live:
            (dev / plan).write_text("# roadmap\n", encoding="utf-8")

    def test_passes_when_consistent_and_live(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        self._scaffold(tmp_path, plan_in_rules=True, plan_in_playbook=True, plan_live=True)
        assert lint_rules.check_triad_plan_consistency()["status"] == "pass"

    def test_flags_when_playbook_diverges(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        self._scaffold(tmp_path, plan_in_rules=True, plan_in_playbook=False, plan_live=True)
        r = lint_rules.check_triad_plan_consistency()
        # FAIL-tier once Phase 2 flipped _ENFORCE_TRIAD_PLAN; WARN before (state-aware, RULES §8).
        assert r["status"] == ("fail" if lint_rules._ENFORCE_TRIAD_PLAN else "warn")
        assert any("SESSION_PLAYBOOK" in v.get("issue", "") for v in r["violations"])

    def test_flags_when_plan_archived(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        self._scaffold(tmp_path, plan_in_rules=True, plan_in_playbook=True, plan_live=False)
        r = lint_rules.check_triad_plan_consistency()
        assert r["status"] == ("fail" if lint_rules._ENFORCE_TRIAD_PLAN else "warn")
        assert any("not live" in v.get("issue", "") for v in r["violations"])

    def test_registered(self):
        assert "triad_plan_consistency" in lint_rules.ALL_CHECKS


class TestStrayArtifacts:
    def test_flags_junk(self, monkeypatch):
        monkeypatch.setattr(
            lint_rules, "_git_candidate_files", lambda: ["scripts/x.py", "scratch.tmp", "dev/notes.bak"]
        )
        r = lint_rules.check_no_stray_artifacts()
        # State-aware (RULES §8): FAIL once the tree is verified clean
        # (_ENFORCE_STRAY_ARTIFACTS truthy), WARN beforehand — matches the
        # sibling guards at 148/178/216. (mint-10: was a lax `in {warn, fail}`.)
        assert r["status"] == ("fail" if lint_rules._ENFORCE_STRAY_ARTIFACTS else "warn")
        assert {v["stray"] for v in r["violations"]} == {"scratch.tmp", "dev/notes.bak"}

    def test_passes_when_clean(self, monkeypatch):
        monkeypatch.setattr(lint_rules, "_git_candidate_files", lambda: ["scripts/x.py", "dev/RULES.md"])
        assert lint_rules.check_no_stray_artifacts()["status"] == "pass"

    def test_skipped_when_git_unavailable(self, monkeypatch):
        monkeypatch.setattr(lint_rules, "_git_candidate_files", lambda: None)
        r = lint_rules.check_no_stray_artifacts()
        assert r["status"] == "warn"
        assert "git unavailable" in r["message"]

    def test_registered(self):
        assert "stray_artifacts" in lint_rules.ALL_CHECKS


class TestDocCrossRefArchiveAware:
    def test_archived_scope_satisfies_reference(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        dev = tmp_path / "dev"
        (dev / "archive" / "scope").mkdir(parents=True)
        (dev / "PLAN_2026-05-29-roadmap.md").write_text("see dev/SCOPE_pivot.md\n", encoding="utf-8")
        (dev / "SESSION_STATE.md").write_text("snapshot\n", encoding="utf-8")
        # The SCOPE lives ONLY in archive — must NOT be flagged as missing.
        (dev / "archive" / "scope" / "SCOPE_pivot.md").write_text("scope\n", encoding="utf-8")
        r = lint_rules.check_doc_cross_references()
        assert not any("missing" in v["issue"] for v in r["violations"])

    def test_dangling_link_flagged(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        dev = tmp_path / "dev"
        dev.mkdir()
        (dev / "PLAN_2026-05-29-roadmap.md").write_text("pointer dev/GHOST_DOC.md\n", encoding="utf-8")
        (dev / "SESSION_STATE.md").write_text("x\n", encoding="utf-8")
        r = lint_rules.check_doc_cross_references()
        assert any(v["issue"] == "dangling dev/ link" for v in r["violations"])


class TestRepoMapReversePath:
    def test_dangling_cited_path_flagged(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        dev = tmp_path / "dev"
        dev.mkdir()
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "real.py").write_text("x\n", encoding="utf-8")
        (dev / "REPO_MAP.md").write_text(
            "`scripts/` holds `scripts/real.py` and `scripts/gone.py`. Ignore `core/x.py`.\n",
            encoding="utf-8",
        )
        r = lint_rules.check_repo_map_complete()
        dangling = {v.get("dangling_path") for v in r["violations"] if "dangling_path" in v}
        assert "scripts/gone.py" in dangling
        assert "scripts/real.py" not in dangling
        assert "core/x.py" not in dangling  # section-relative → not validated

    def test_clean_map_passes(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        dev = tmp_path / "dev"
        dev.mkdir()
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "real.py").write_text("x\n", encoding="utf-8")
        (dev / "REPO_MAP.md").write_text("`dev/` and `scripts/` — see `scripts/real.py`.\n", encoding="utf-8")
        assert lint_rules.check_repo_map_complete()["status"] == "pass"


class TestSuperpowersCoherence:
    """mint-6 — every docs/superpowers/{plans,specs}/*.md carries a Status header
    and is listed in INDEX.md (anti-rot for the strategic-docs corpus)."""

    def _scaffold(self, root, *, plans=(), specs=(), index=None):
        base = root / "docs" / "superpowers"
        (base / "plans").mkdir(parents=True)
        (base / "specs").mkdir(parents=True)
        for name, body in plans:
            (base / "plans" / name).write_text(body, encoding="utf-8")
        for name, body in specs:
            (base / "specs" / name).write_text(body, encoding="utf-8")
        if index is not None:
            (base / "INDEX.md").write_text(index, encoding="utf-8")

    def test_flags_missing_status_header(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        self._scaffold(
            tmp_path,
            plans=[("2026-05-16-x.md", "# X\n\nno status here\n")],
            index="# Index\n\n`plans/2026-05-16-x.md`\n",
        )
        r = lint_rules.check_superpowers_coherence()
        assert r["id"] == "superpowers_coherence"
        assert r["status"] == "fail"  # _ENFORCE_SUPERPOWERS_COHERENCE ships True
        assert any("Status" in v.get("issue", "") for v in r["violations"])

    def test_flags_file_not_in_index(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        self._scaffold(
            tmp_path,
            plans=[("2026-05-16-x.md", "# X\n**Status:** shipped\n")],
            index="# Index\n\n(nothing listed)\n",
        )
        r = lint_rules.check_superpowers_coherence()
        assert r["status"] == "fail"
        assert any("not listed" in v.get("issue", "") for v in r["violations"])

    def test_flags_missing_index(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        self._scaffold(
            tmp_path,
            plans=[("2026-05-16-x.md", "# X\n**Status:** shipped\n")],
            index=None,
        )
        r = lint_rules.check_superpowers_coherence()
        assert r["status"] == "fail"
        assert any("INDEX" in str(v) for v in r["violations"])

    def test_flags_stale_index_entry(self, tmp_path, monkeypatch):
        # INDEX lists a plan that no longer exists on disk -> reverse-pass violation.
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        self._scaffold(
            tmp_path,
            plans=[("2026-05-16-x.md", "# X\n**Status:** shipped\n")],
            index="# Index\n\n`plans/2026-05-16-x.md` `plans/2026-05-16-deleted.md`\n",
        )
        r = lint_rules.check_superpowers_coherence()
        assert r["status"] == "fail"
        assert any("not found on disk" in v.get("issue", "") for v in r["violations"])

    def test_passes_when_coherent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        self._scaffold(
            tmp_path,
            plans=[("2026-05-16-x.md", "# X\n**Status:** shipped\n")],
            specs=[("2026-05-16-y.md", "# Y\n**Created:** d. **Status:** design\n")],
            index="# Index\n\n`plans/2026-05-16-x.md` `specs/2026-05-16-y.md`\n",
        )
        r = lint_rules.check_superpowers_coherence()
        assert r["status"] == "pass"
        assert r["violations"] == []

    def test_warn_tier_when_enforcement_off(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        monkeypatch.setattr(lint_rules, "_ENFORCE_SUPERPOWERS_COHERENCE", False)
        self._scaffold(
            tmp_path,
            plans=[("2026-05-16-x.md", "# X\n\nno status\n")],
            index="# Index\n\n`plans/2026-05-16-x.md`\n",
        )
        assert lint_rules.check_superpowers_coherence()["status"] == "warn"

    def test_no_files_passes(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lint_rules, "REPO", tmp_path)
        (tmp_path / "docs" / "superpowers" / "plans").mkdir(parents=True)
        (tmp_path / "docs" / "superpowers" / "specs").mkdir(parents=True)
        assert lint_rules.check_superpowers_coherence()["status"] == "pass"

    def test_registered_in_all_checks(self):
        assert "superpowers_coherence" in lint_rules.ALL_CHECKS

    def test_real_repo_is_coherent(self):
        # Integration: the live docs/superpowers corpus must stay coherent.
        r = lint_rules.check_superpowers_coherence()
        assert r["status"] == "pass", r["violations"]

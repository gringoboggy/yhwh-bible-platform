"""Tests for lint_rules — extracted from test_scripts.py in ω.27.

Originally lived in tests/test_scripts.py as part of a 22,000-line
monolithic test file; moved here so each test target sits next to a
single source-of-truth scripts/ module. Future tests for the same
target should land in this file rather than test_scripts.py.
"""

from __future__ import annotations


class TestAllChecksMetaContract:
    """mint-7 E1 — every registered lint check must run on the committed tree
    without raising and return the standard {status, message, ...} shape, so a
    check can never rot silently (8 of 28 ALL_CHECKS had no unit test before)."""

    @classmethod
    def setup_class(cls):
        from scripts import lint_rules

        cls.mod = lint_rules

    def test_every_check_runs_returns_valid_shape_and_does_not_fail(self):
        failing = {}
        for cid, fn in self.mod.ALL_CHECKS.items():
            assert callable(fn), f"{cid} is not callable"
            r = fn()
            assert isinstance(r, dict), f"{cid} returned {type(r).__name__}, not dict"
            assert r.get("status") in {"pass", "warn", "fail"}, f"{cid} bad status {r.get('status')!r}"
            assert "message" in r, f"{cid} missing 'message'"
            if r.get("status") == "fail":
                failing[cid] = r.get("message")
        assert not failing, f"lint check(s) failing on the committed tree: {failing}"

    def test_registry_not_silently_shrunk(self):
        # Pin the registry size EXACTLY (28 at mint-8: +bookcode_canonical mint-7,
        # +subprocess_stdin mint-8) so a check can't be dropped from ALL_CHECKS —
        # or quietly added without updating this pin — without a test noticing.
        assert len(self.mod.ALL_CHECKS) == 28, f"ALL_CHECKS is {len(self.mod.ALL_CHECKS)}, expected 28"
        # A duplicate key in the dict literal would silently collapse two checks
        # into one; pin that the keys are unique.
        assert len(self.mod.ALL_CHECKS) == len(set(self.mod.ALL_CHECKS))


class TestOmega15PlanLinter:
    """ω.15 — plan-coherence linter. Verifies the active PLAN_*.md
    stays coherent with CHANGELOG and Depends references."""

    @classmethod
    def setup_class(cls):
        from scripts import lint_plan

        cls.mod = lint_plan

    def test_phase_id_re_matches_greek_letters(self):
        # Spot-check the regex: Greek-letter phases match.
        text = "ψ.18 ψ.18.1 χ.7 ω.0.1 ν.2.7-A"
        ids = self.mod.PHASE_ID_RE.findall(text)
        for expected in ("ψ.18", "ψ.18.1", "χ.7", "ω.0.1", "ν.2.7-A"):
            assert expected in ids, f"missed {expected}"

    def test_phase_id_re_matches_named_composites(self):
        text = "the χ-AI-xrefs detector"
        ids = self.mod.PHASE_ID_RE.findall(text)
        assert "χ-AI-xrefs" in ids

    def test_phase_id_re_matches_release_tags(self):
        text = "ship v1.0.0 then v1.1.0"
        ids = self.mod.PHASE_ID_RE.findall(text)
        assert "v1.0.0" in ids
        assert "v1.1.0" in ids

    def test_phase_id_re_rejects_two_part_versions(self):
        # "v1.0" appears in prose like "v1.0 candidate criteria" —
        # not a release tag, shouldn't match. Three-part required.
        text = "the v1.0 candidate criteria are met"
        ids = self.mod.PHASE_ID_RE.findall(text)
        assert "v1.0" not in ids

    def test_active_plan_picks_latest(self):
        # Picks lexicographically latest PLAN_*.md.
        plan = self.mod._active_plan()
        assert plan is not None
        assert plan.name.startswith("PLAN_")
        assert plan.suffix == ".md"

    def test_changelog_shipped_phases_uses_phases_shipped_lines(self):
        # The shipped set must come from `**Phases shipped:**` lines
        # only — not arbitrary mentions. Spot-check a known shipped
        # phase from this session is recognized.
        shipped = self.mod._changelog_shipped_phases()
        assert "ψ.18" in shipped, "ψ.18 missing from shipped set"
        assert "ψ.15" in shipped, "ψ.15 missing from shipped set"

    def test_changelog_shipped_excludes_scope_only_mentions(self):
        # ρ.1 was added to the plan in a 2026-05-08 scope-expansion
        # session but never shipped. The shipped set must NOT
        # include it (regression for the false-positive that the
        # session-header heuristic produced).
        shipped = self.mod._changelog_shipped_phases()
        assert "ρ.1" not in shipped, "ρ.1 incorrectly classified as shipped (was scope-only)"

    def test_check_plan_singular_passes(self):
        # On the current repo, exactly one active PLAN_*.md should
        # be in dev/ (others archived).
        result = self.mod.check_plan_singular()
        assert result["status"] == "pass", result["message"]

    def test_check_plan_status_shipped_passes(self):
        # Every PLAN-claimed-shipped phase backs to CHANGELOG.
        result = self.mod.check_plan_status_shipped()
        assert result["status"] == "pass", f"{result['message']}: {result.get('violations')}"

    def test_check_plan_status_open_passes(self):
        # No PLAN-open phase has shipped yet.
        result = self.mod.check_plan_status_open()
        assert result["status"] == "pass", f"{result['message']}: {result.get('violations')}"

    def test_check_plan_depends_valid_passes(self):
        # All Depends: refs resolve to known phase ids.
        result = self.mod.check_plan_depends_valid()
        assert result["status"] == "pass", f"{result['message']}: {result.get('violations')}"

    def test_run_all_returns_clean(self):
        out = self.mod.run_all()
        assert out["summary"]["clean"] is True, out["summary"]
        assert out["summary"]["fail"] == 0
        assert out["summary"]["total"] == 4

    def test_lint_rules_composes_plan_check(self):
        # ω.15 wires lint_plan into lint_rules.run_all() as
        # `plan_coherence`. Verify the master linter sees it.
        from scripts.lint_rules import run_all

        out = run_all()
        ids = {c["id"] for c in out["checks"]}
        assert "plan_coherence" in ids, "plan_coherence sub-check not surfaced in lint_rules"
        plan_check = next(c for c in out["checks"] if c["id"] == "plan_coherence")
        assert plan_check["status"] == "pass", plan_check["message"]


class TestOmega23LintProfile:
    """ω.23 — `lint_rules.py --profile` flag for per-check timing.
    Helps notice when a new check (e.g. atomic_writes' AST scan)
    becomes the bottleneck as the suite grows.

    Additive: every check result gains `duration_ms`; aggregate
    summary gains `total_ms`. Default text/JSON output unchanged
    structurally — back-compat preserved.
    """

    # ---- run_all surfaces duration_ms ----

    def test_every_check_has_duration_ms(self):
        from scripts.lint_rules import run_all

        out = run_all()
        for c in out["checks"]:
            assert "duration_ms" in c, f"check {c['id']!r} missing duration_ms: {c}"
            assert isinstance(c["duration_ms"], float)
            assert c["duration_ms"] >= 0.0

    def test_summary_has_total_ms(self):
        from scripts.lint_rules import run_all

        out = run_all()
        assert "total_ms" in out["summary"]
        s = out["summary"]
        assert isinstance(s["total_ms"], float)
        # total_ms equals the sum of per-check durations (rounded).
        per_check_sum = sum(c.get("duration_ms", 0.0) for c in out["checks"])
        assert abs(s["total_ms"] - round(per_check_sum, 3)) < 0.01

    def test_unknown_check_id_still_carries_duration(self):
        from scripts.lint_rules import run_all

        out = run_all(check_ids=["this-id-does-not-exist"])
        assert len(out["checks"]) == 1
        assert "duration_ms" in out["checks"][0]
        # Unknown checks short-circuit; duration is 0.0.
        assert out["checks"][0]["duration_ms"] == 0.0

    def test_check_that_raises_still_carries_duration(self, monkeypatch):
        # If a check function explodes, run_all wraps it in a fail
        # result — the duration_ms field must still be set on that
        # synthesized result so consumers (api_preflight, --profile
        # output) don't trip on KeyError.
        from scripts import lint_rules

        def boom():
            raise RuntimeError("synthetic explosion")

        monkeypatch.setitem(
            lint_rules.ALL_CHECKS,
            "_test_boom",
            boom,
        )
        out = lint_rules.run_all(check_ids=["_test_boom"])
        assert len(out["checks"]) == 1
        assert "duration_ms" in out["checks"][0]
        assert out["checks"][0]["status"] == "fail"

    # ---- back-compat: existing consumers ignore the new fields ----

    def test_existing_check_keys_preserved(self):
        from scripts.lint_rules import run_all

        out = run_all()
        # The api_preflight composer reads c["status"], c["message"],
        # c["name"], c["id"]. Pin them so a future refactor of run_all
        # doesn't accidentally drop any.
        for c in out["checks"]:
            for key in ("id", "name", "status", "message", "violations"):
                assert key in c, f"check missing legacy key {key!r}: {c}"

    # ---- --profile CLI flag ----

    def test_main_profile_prints_per_check_timing(self, capsys):
        from scripts.lint_rules import main

        rc = main(["--profile"])
        out = capsys.readouterr().out
        assert rc == 0
        # Format pin: "[  XXX.X ms]" appears for each check.
        assert "ms]" in out, f"timing column missing in: {out!r}"
        # Aggregate total appears in the verdict line.
        assert "ms total" in out

    def test_main_profile_sorts_descending(self, capsys, monkeypatch):
        # Stub run_all to inject known durations and confirm the
        # printed order is descending.
        from scripts import lint_rules

        def fake_run_all(check_ids=None):
            return {
                "checks": [
                    {
                        "id": "fast",
                        "name": "FAST CHECK",
                        "status": "pass",
                        "message": "ok",
                        "violations": [],
                        "duration_ms": 1.0,
                    },
                    {
                        "id": "slow",
                        "name": "SLOW CHECK",
                        "status": "pass",
                        "message": "ok",
                        "violations": [],
                        "duration_ms": 999.0,
                    },
                    {
                        "id": "mid",
                        "name": "MID CHECK",
                        "status": "pass",
                        "message": "ok",
                        "violations": [],
                        "duration_ms": 50.0,
                    },
                ],
                "summary": {
                    "total": 3,
                    "pass": 3,
                    "warn": 0,
                    "fail": 0,
                    "clean": True,
                    "total_ms": 1050.0,
                },
            }

        monkeypatch.setattr(lint_rules, "run_all", fake_run_all)
        rc = lint_rules.main(["--profile"])
        out = capsys.readouterr().out
        assert rc == 0
        slow_pos = out.find("SLOW CHECK")
        mid_pos = out.find("MID CHECK")
        fast_pos = out.find("FAST CHECK")
        assert slow_pos < mid_pos < fast_pos, (
            f"expected SLOW < MID < FAST ordering, got slow={slow_pos}, mid={mid_pos}, fast={fast_pos}\noutput:\n{out}"
        )

    def test_main_default_mode_unchanged(self, capsys):
        # Without --profile, the per-line format must NOT include
        # the "[  XX ms]" timing column. Pin the back-compat
        # contract so a future refactor doesn't drift.
        from scripts.lint_rules import main

        rc = main([])
        out = capsys.readouterr().out
        assert rc == 0
        # The "ms]" suffix is the timing-column tell. It must not
        # appear in default mode.
        assert "ms]" not in out

    def test_main_json_includes_duration_ms(self, capsys):
        # JSON consumers (preflight aggregator, future webhook) get
        # the new field too — pin it so a future contributor doesn't
        # accidentally strip it.
        from scripts.lint_rules import main

        rc = main(["--json"])
        out = capsys.readouterr().out
        assert rc == 0
        import json as _json

        data = _json.loads(out)
        assert "summary" in data
        assert "total_ms" in data["summary"]
        for c in data["checks"]:
            assert "duration_ms" in c

    def test_profile_and_json_compose(self, capsys):
        # --profile is a presentation flag for text mode; --json
        # output should still be JSON. The two flags don't conflict —
        # JSON wins (it always carries duration_ms).
        from scripts.lint_rules import main

        rc = main(["--profile", "--json"])
        out = capsys.readouterr().out
        assert rc == 0
        import json as _json

        # JSON-parseable, not text format with timing brackets.
        data = _json.loads(out)
        assert "checks" in data


class TestOmega231AstCacheReuse:
    """ω.23.1 — read+parse cache shared between `check_atomic_writes`
    and `check_external_http`. Both AST-walk the same scripts/ tree;
    profile (ω.23) showed ~87% of total lint wall time was the
    duplicated parse work. Cache halves it.

    Tests pin: cache lookup behaviour, cleared-between-calls
    invariant, behavioural equivalence (the two checks still produce
    the SAME violations they would have without the cache), and a
    populated cache after run_all().
    """

    def setup_method(self, method):
        # Each test gets a clean cache so prior tests don't pollute.
        from scripts.lint_rules import _clear_parse_cache

        _clear_parse_cache()

    # ---- cache hit / miss behaviour ----

    def test_first_call_parses_second_call_hits_cache(self):
        from scripts import lint_rules
        from pathlib import Path

        path = Path(lint_rules.__file__)

        # Cache empty.
        assert not lint_rules._PARSE_CACHE

        tree1, lines1 = lint_rules._load_parsed_python(path)
        assert tree1 is not None
        assert len(lines1) > 0
        # Cache populated by exactly one entry.
        assert len(lint_rules._PARSE_CACHE) == 1

        tree2, lines2 = lint_rules._load_parsed_python(path)
        # Same object reference — proves we returned the cached
        # tuple, not a freshly-parsed one.
        assert tree2 is tree1
        assert lines2 is lines1

    def test_cache_keys_normalise_path(self, tmp_path):
        # Two Path objects pointing at the same file (one absolute,
        # one via a different routing) must hit the same cache slot.
        from scripts import lint_rules

        f = tmp_path / "demo.py"
        f.write_text("x = 1\n", encoding="utf-8")

        a = lint_rules._load_parsed_python(f)
        b = lint_rules._load_parsed_python(f.resolve())
        # Same cached object on both routes.
        assert a[0] is b[0]
        assert len(lint_rules._PARSE_CACHE) == 1

    def test_unreadable_file_caches_failure(self, tmp_path):
        # A file that doesn't parse must NOT be re-attempted on
        # the second call; the failure is cached as (None, []).
        from scripts import lint_rules

        f = tmp_path / "broken.py"
        f.write_text("def(\n", encoding="utf-8")  # SyntaxError

        a = lint_rules._load_parsed_python(f)
        assert a == (None, [])
        # Cached.
        assert str(f.resolve()) in lint_rules._PARSE_CACHE

        b = lint_rules._load_parsed_python(f)
        # Same tuple, same identity.
        assert a is b or a == b

    def test_missing_file_caches_failure(self, tmp_path):
        from scripts import lint_rules

        a = lint_rules._load_parsed_python(tmp_path / "no-such.py")
        assert a == (None, [])

    # ---- run_all clears cache between invocations ----

    def test_run_all_clears_cache_at_entry(self, tmp_path):
        # Pre-populate the cache with a synthetic entry; run_all()
        # must drop it before doing its own work.
        from scripts import lint_rules

        lint_rules._PARSE_CACHE["fake-key"] = (None, [])
        assert "fake-key" in lint_rules._PARSE_CACHE

        lint_rules.run_all()
        # The synthetic entry is gone (cache was cleared at entry).
        # The new entries are the real scripts/ files the checks
        # walked.
        assert "fake-key" not in lint_rules._PARSE_CACHE
        assert len(lint_rules._PARSE_CACHE) > 0

    def test_run_all_populates_cache(self):
        from scripts import lint_rules

        lint_rules.run_all()
        # After a run, the cache holds entries for every .py file
        # under scripts/ that the AST-walk checks touched.
        assert len(lint_rules._PARSE_CACHE) > 10
        # Every cached value is the (tree | None, lines) shape.
        for _key, val in lint_rules._PARSE_CACHE.items():
            assert isinstance(val, tuple)
            assert len(val) == 2

    # ---- behavioural equivalence ----

    def test_atomic_writes_check_unchanged_with_cache(self):
        from scripts.lint_rules import check_atomic_writes

        # The check passes on the production tree (no raw write-mode
        # open() outside notes_io.py). Sanity-check that's still true
        # — i.e., the cache refactor didn't accidentally change which
        # files get scanned.
        result = check_atomic_writes()
        assert result["status"] == "pass"
        assert result["violations"] == []

    def test_external_http_check_unchanged_with_cache(self):
        from scripts.lint_rules import check_external_http

        result = check_external_http()
        assert result["status"] == "pass"
        assert result["violations"] == []

    def test_two_back_to_back_runs_equivalent(self):
        # ω.23.1 ships a cache; consumers (api_preflight, tests)
        # call run_all() repeatedly. Pin that two back-to-back
        # invocations produce equivalent results — i.e., the cache
        # doesn't accidentally cause stale data to leak across
        # invocations.
        from scripts.lint_rules import run_all

        a = run_all()
        b = run_all()

        # Strip duration_ms (it varies per call by definition).
        def strip(out):
            return [{k: v for k, v in c.items() if k != "duration_ms"} for c in out["checks"]]

        assert strip(a) == strip(b)
        assert a["summary"]["clean"] == b["summary"]["clean"]
        assert a["summary"]["pass"] == b["summary"]["pass"]
        assert a["summary"]["fail"] == b["summary"]["fail"]

    # ---- cache clearing API ----

    def test_clear_parse_cache_empties_dict(self):
        from scripts import lint_rules
        from pathlib import Path

        # Populate.
        lint_rules._load_parsed_python(Path(lint_rules.__file__))
        assert lint_rules._PARSE_CACHE
        lint_rules._clear_parse_cache()
        assert not lint_rules._PARSE_CACHE


class TestOmega18LintFix:
    """ω.18 — `lint_rules.py --fix` for safe drift correction.
    Most checks need human review and produce a "no auto-fix
    available" refusal; only `freshness` ships an auto-fixer in
    v1 (touch SESSION_STATE.md mtime to match CHANGELOG.md).
    Future ω.18.x add more fixers as they're vetted.
    """

    # Restore mtimes after each test so the production tree's
    # freshness check stays clean for subsequent tests/runs.

    def setup_method(self, method):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        cl = repo / "dev" / "CHANGELOG.md"
        ss = repo / "dev" / "SESSION_STATE.md"
        self._cl_mtime = cl.stat().st_mtime if cl.is_file() else None
        self._ss_mtime = ss.stat().st_mtime if ss.is_file() else None
        self._cl = cl
        self._ss = ss

    def teardown_method(self, method):
        import os as _os

        if self._cl_mtime is not None:
            _os.utime(self._cl, (self._cl_mtime, self._cl_mtime))
        if self._ss_mtime is not None:
            _os.utime(self._ss, (self._ss_mtime, self._ss_mtime))

    # ---- FIXERS registry ----

    def test_fixers_registry_shape(self):
        from scripts.lint_rules import FIXERS

        assert isinstance(FIXERS, dict)
        # Every registered fixer must be callable.
        for cid, fn in FIXERS.items():
            assert callable(fn), f"fixer for {cid!r} is not callable"

    def test_freshness_fixer_registered(self):
        from scripts.lint_rules import FIXERS, _fix_freshness

        assert FIXERS.get("freshness") is _fix_freshness

    def test_unsafe_checks_have_no_fixer(self):
        # The PLAN spec for ω.18 explicitly excludes structurally
        # ambiguous checks (atomic_writes, untracked_phases, etc.).
        # Pin the safety bar so a future contributor doesn't quietly
        # land a risky fixer.
        from scripts.lint_rules import FIXERS

        for unsafe in (
            "atomic_writes",
            "external_http",
            "untracked_phases",
            "code_doc_sync",
            "encode_decode",
            "6.1",
            "6.2",
            "plan_coherence",
        ):
            assert unsafe not in FIXERS, (
                f"check {unsafe!r} should NOT have an auto-fixer without explicit safety review"
            )

    # ---- _fix_freshness behaviour ----

    def test_fix_freshness_already_in_sync_is_noop(self):
        import os as _os
        from scripts.lint_rules import _fix_freshness

        # Force the two files to identical mtimes.
        cl_mtime = self._cl.stat().st_mtime
        _os.utime(self._ss, (cl_mtime, cl_mtime))
        result = _fix_freshness({}, dry_run=False)
        assert result["ok"] is True
        assert result["applied"] is False
        assert "already in sync" in result["message"]

    def test_fix_freshness_dry_run_reports_no_apply(self):
        import os as _os
        from scripts.lint_rules import _fix_freshness

        # Force drift: bump CHANGELOG mtime 8h ahead.
        cl_mtime = self._cl.stat().st_mtime + 8 * 3600
        _os.utime(self._cl, (cl_mtime, cl_mtime))
        # Capture pre-fix SESSION_STATE mtime so we can verify it's
        # unchanged after dry-run.
        pre_ss = self._ss.stat().st_mtime
        result = _fix_freshness({}, dry_run=True)
        post_ss = self._ss.stat().st_mtime
        assert result["ok"] is True
        assert result["applied"] is False
        assert post_ss == pre_ss, "dry-run mutated the file mtime"
        assert "would sync" in result["message"]
        # Caveat about content drift surfaced.
        assert "content" in result["message"].lower()

    def test_fix_freshness_applies_when_drifted(self):
        import os as _os
        from scripts.lint_rules import _fix_freshness

        cl_mtime = self._cl.stat().st_mtime + 8 * 3600
        _os.utime(self._cl, (cl_mtime, cl_mtime))
        result = _fix_freshness({}, dry_run=False)
        assert result["ok"] is True
        assert result["applied"] is True
        # SESSION_STATE mtime is now within 6h of CHANGELOG.
        delta = abs(self._cl.stat().st_mtime - self._ss.stat().st_mtime)
        assert delta <= 6 * 3600
        # Caveat about content drift is in the applied message too.
        assert "content" in result["message"].lower()

    def test_fix_freshness_records_change_diff(self):
        import os as _os
        from scripts.lint_rules import _fix_freshness

        cl_mtime = self._cl.stat().st_mtime + 8 * 3600
        _os.utime(self._cl, (cl_mtime, cl_mtime))
        pre_ss = self._ss.stat().st_mtime
        result = _fix_freshness({}, dry_run=False)
        assert len(result["changes"]) == 1
        change = result["changes"][0]
        assert change["file"] == "dev/SESSION_STATE.md"
        assert change["field"] == "mtime"
        assert change["from"] == pre_ss

    # ---- run_fixers dispatcher ----

    def test_run_fixers_skips_passing_checks(self):
        # Passing checks never produce fixer entries (regardless of
        # whether other checks are warning/failing). Pin the contract
        # that run_fixers ONLY acts on non-pass results.
        from scripts.lint_rules import run_fixers

        result = run_fixers(dry_run=True)
        assert result["summary"]["skipped_clean"] > 0
        # Every entry in checks is non-passing (ready/refused/failed).
        for c in result["checks"]:
            assert c["status"] != "pass"
        # No fixes applied in dry-run regardless.
        assert result["summary"]["applied"] == 0
        assert result["summary"]["dry_run"] is True

    def test_run_fixers_refuses_unregistered_check(self, monkeypatch):
        # Stub run_all to surface a fail for a check that has no
        # fixer; run_fixers must surface "refused" with the original
        # message in tow rather than silently ignoring.
        from scripts import lint_rules

        def fake_run_all(check_ids=None):
            return {
                "checks": [
                    {
                        "id": "atomic_writes",
                        "name": "Atomic writes (no raw open('w') outside notes_io)",
                        "status": "fail",
                        "message": "1 violation",
                        "violations": [{"file": "x.py"}],
                        "duration_ms": 10.0,
                    }
                ],
                "summary": {"total": 1, "pass": 0, "warn": 0, "fail": 1, "clean": False},
            }

        monkeypatch.setattr(lint_rules, "run_all", fake_run_all)
        result = lint_rules.run_fixers(dry_run=False)
        assert len(result["checks"]) == 1
        c = result["checks"][0]
        assert c["status"] == "refused"
        assert c["id"] == "atomic_writes"
        assert "no auto-fix" in c["message"]
        assert "1 violation" in c["message"]
        assert result["summary"]["refused"] == 1
        assert result["summary"]["applied"] == 0

    def test_run_fixers_dispatches_to_registered_fixer(
        self,
        monkeypatch,
    ):
        import os as _os
        from scripts.lint_rules import run_fixers

        # Force drift so freshness check fires.
        cl_mtime = self._cl.stat().st_mtime + 8 * 3600
        _os.utime(self._cl, (cl_mtime, cl_mtime))
        result = run_fixers(check_ids=["freshness"], dry_run=False)
        assert len(result["checks"]) == 1
        c = result["checks"][0]
        assert c["status"] == "fixed"
        assert c["id"] == "freshness"
        assert result["summary"]["applied"] == 1

    def test_run_fixers_dry_run_preserves_state(self):
        import os as _os
        from scripts.lint_rules import run_fixers

        cl_mtime = self._cl.stat().st_mtime + 8 * 3600
        _os.utime(self._cl, (cl_mtime, cl_mtime))
        pre_ss = self._ss.stat().st_mtime
        result = run_fixers(check_ids=["freshness"], dry_run=True)
        # Dry-run reported a "ready" preview but didn't write.
        assert result["checks"][0]["status"] == "ready"
        assert self._ss.stat().st_mtime == pre_ss
        assert result["summary"]["applied"] == 0
        assert result["summary"]["dry_run"] is True

    # ---- CLI integration ----

    def test_main_fix_dry_run_clean_state(self, capsys):
        from scripts.lint_rules import main

        rc = main(["--fix", "--dry-run"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "DRY-RUN" in out

    def test_main_fix_json_output(self, capsys):
        from scripts.lint_rules import main

        rc = main(["--fix", "--json", "--dry-run"])
        out = capsys.readouterr().out
        import json as _json

        data = _json.loads(out)
        assert "summary" in data
        assert "checks" in data
        assert data["summary"]["dry_run"] is True
        assert rc == 0

    def test_main_default_mode_does_not_fix(self, capsys):
        # Without --fix, the linter behaves exactly as before
        # (production tree is clean → exit 0; profile / json
        # already pinned). Pin: --fix is OFF by default and
        # touching nothing.
        import os as _os
        from scripts.lint_rules import main

        # Force drift so a fix would matter; default mode must
        # still NOT fix it.
        cl_mtime = self._cl.stat().st_mtime + 8 * 3600
        _os.utime(self._cl, (cl_mtime, cl_mtime))
        pre_ss = self._ss.stat().st_mtime
        main([])
        post_ss = self._ss.stat().st_mtime
        # Default mode might exit 0 or 1 depending on warnings;
        # what matters is it did NOT touch SESSION_STATE.
        assert post_ss == pre_ss


class TestOmega33RuffFormat:
    """ω.33 — ruff format pass. The codebase was formatted in one
    one-shot diff (253 files); this test ensures it stays
    formatted by running `ruff format --check` and asserting
    return code 0.

    Skipped silently when ruff isn't installed — ruff is a dev-
    only tool, not a runtime dep, so a fresh checkout without
    `pip install ruff` shouldn't fail this test.
    """

    def test_codebase_stays_ruff_formatted(self):
        import shutil
        import subprocess
        import pytest

        if shutil.which("ruff") is None:
            try:
                # Some installations expose ruff as a Python module
                # rather than a shell executable.
                import ruff  # noqa: F401
            except ImportError:
                pytest.skip("ruff not installed; install with `pip install ruff` to enforce format consistency")

        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        proc = subprocess.run(
            ["python", "-m", "ruff", "format", "--check", "."],
            cwd=str(repo),
            stdin=subprocess.DEVNULL,  # W-W1 mitigation (τ.6.x.1)
            capture_output=True,
            text=True,
        )
        # Exit 0 = all formatted; exit 1 = files would reformat.
        # Exit 2 = misuse / config error — surface that too.
        assert proc.returncode == 0, (
            f"ruff format drift detected. Run "
            f"`python -m ruff format .` to fix.\n"
            f"stdout tail:\n{proc.stdout[-500:]}\n"
            f"stderr tail:\n{proc.stderr[-500:]}"
        )

    def test_pyproject_has_ruff_config(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        text = (repo / "pyproject.toml").read_text(encoding="utf-8")
        assert "[tool.ruff]" in text
        # Pin specific config knobs the format pass relied on.
        assert "line-length" in text
        assert 'target-version = "py310"' in text

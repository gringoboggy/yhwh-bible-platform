"""ω.38 — GitHub Actions CI workflow pins.

Topic file (created alongside the ω.38 ship, follows the ω.27
follow-on convention).

Coverage:
- TestOmega38CiWorkflowExists:     file is present, parseable YAML.
- TestOmega38CiWorkflowTriggers:   push + PR + manual dispatch.
- TestOmega38CiWorkflowEnv:        PYTHONUTF8=1 set workflow-wide.
- TestOmega38CiLintChain:          lint job mirrors the local
  pre-commit chain (ruff format/check + lint_rules + 4 audits).
- TestOmega38CiTestMatrix:         cross-OS × multi-Python matrix
  covers the pyproject py310 floor through 3.14.
- TestOmega38CiObsoleteRemoved:    the GitHub-default
  python-package.yml is gone (replaced by ci.yml).

Pinning rationale: this workflow is the only enforcement gate
on `main` for the audit chain a fresh clone might not have
locally activated. Drift here is silent (the maintainer keeps
seeing green checks while the actual coverage degrades), so
each requirement gets an explicit assertion.

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""

from __future__ import annotations


class TestOmega38CiWorkflowExists:
    """ci.yml must be present at the canonical GitHub Actions
    location and parse as YAML."""

    @classmethod
    def setup_class(cls):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        cls.path = repo / ".github" / "workflows" / "ci.yml"
        cls.text = cls.path.read_text(encoding="utf-8")
        cls.data = yaml.safe_load(cls.text)

    def test_workflow_file_exists(self):
        assert self.path.is_file(), f"ω.38 ci.yml missing at {self.path}"

    def test_workflow_yaml_parses(self):
        assert isinstance(self.data, dict), "ci.yml must parse to a top-level mapping"

    def test_workflow_has_a_name(self):
        assert self.data.get("name"), "ci.yml missing top-level `name:`"


class TestOmega38CiWorkflowTriggers:
    """Workflow must fire on push to main, on PRs to main, and
    accept a manual dispatch (handy for re-running after a
    transient runner failure)."""

    @classmethod
    def setup_class(cls):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        cls.data = yaml.safe_load((repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
        # YAML parses bare `on:` as the Python bool True. Accept both
        # spellings so future quoting-style changes don't break the pin.
        cls.on = cls.data.get("on") or cls.data.get(True)

    def test_triggers_on_push_to_main(self):
        push = self.on.get("push") or {}
        branches = push.get("branches") or []
        assert "main" in branches, f"ci.yml push branches missing main: {branches}"

    def test_triggers_on_pr_to_main(self):
        pr = self.on.get("pull_request") or {}
        branches = pr.get("branches") or []
        assert "main" in branches, f"ci.yml PR branches missing main: {branches}"

    def test_supports_workflow_dispatch(self):
        assert "workflow_dispatch" in self.on, "ci.yml must allow manual re-runs via workflow_dispatch"


class TestOmega38CiWorkflowEnv:
    """Top-level env block must set PYTHONUTF8=1. Project memory:
    without it, 72 tests fail on Windows runners with cp1252
    decoding errors at byte 0x9d. Setting it workflow-wide (not
    per-job) keeps the contract single-sourced."""

    @classmethod
    def setup_class(cls):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        cls.data = yaml.safe_load((repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))

    def test_pythonutf8_set_workflow_wide(self):
        env = self.data.get("env") or {}
        # YAML may load "1" as int 1 — accept both spellings.
        assert str(env.get("PYTHONUTF8")) == "1", (
            f"PYTHONUTF8 must be 1 (got {env.get('PYTHONUTF8')!r}); memory: required on Windows or 72 tests fail."
        )

    def test_pythonioencoding_set_workflow_wide(self):
        env = self.data.get("env") or {}
        assert env.get("PYTHONIOENCODING") == "utf-8", (
            f"PYTHONIOENCODING must be utf-8 (got {env.get('PYTHONIOENCODING')!r})"
        )


class TestOmega38CiLintChain:
    """The lint job must invoke every audit script the local
    pre-commit chain invokes (dev/git-hooks/pre-commit) PLUS the
    style+lint gates from .githooks/pre-commit. A future
    contributor removing one of these is the regression this
    test catches."""

    @classmethod
    def setup_class(cls):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        cls.data = yaml.safe_load((repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
        cls.lint_job = cls.data["jobs"]["lint"]
        cls.run_commands = " \n ".join(
            step.get("run", "") for step in cls.lint_job.get("steps", []) if isinstance(step, dict) and step.get("run")
        )

    def test_lint_job_runs_ruff_format_check(self):
        assert "ruff format --check" in self.run_commands, "lint job missing `ruff format --check` step"

    def test_lint_job_does_not_run_ruff_check_yet(self):
        # `ruff check` is deliberately NOT in CI yet — the codebase
        # has ~22.8K pre-existing violations from rules the local
        # pre-commit hook never enforced. Promoting it to a CI gate
        # is its own future cleanup phase. Pin the deliberate absence
        # so a future "let's add lint" sweep doesn't reintroduce the
        # day-one CI failure that would create.
        import re

        # Match `ruff check` as a CLI invocation (not appearing
        # inside `ruff format --check`).
        invocations = re.findall(r"\bruff\s+check\b", self.run_commands)
        assert not invocations, (
            "lint job re-introduced `ruff check`; codebase isn't clean yet — "
            "ship a ruff-cleanup phase first before promoting this to a gate"
        )

    def test_lint_job_runs_lint_rules(self):
        assert "scripts/lint_rules.py" in self.run_commands

    def test_lint_job_runs_audit_chain(self):
        # Match dev/git-hooks/pre-commit's chain — ξ.11.1.
        for required in (
            "scripts/audit_deps.py",
            "scripts/audit_dead_code.py",
            "scripts/audit_types.py",
            "scripts/audit_caches.py",
        ):
            assert required in self.run_commands, f"lint job missing audit step: {required}"

    def test_lint_job_installs_dev_tools(self):
        # Without these, the audit chain returns rc=2 (graceful
        # skip) and the gate becomes a no-op. Pin the install
        # step so a future "trim CI dependencies" sweep can't
        # silently neuter coverage.
        for tool in ("ruff", "mypy", "vulture", "pip-audit"):
            assert tool in self.run_commands, f"lint job not installing dev tool: {tool}"


class TestOmega38CiTestMatrix:
    """The pytest job must run on cross-OS × multi-Python matrix
    and use the project's parallel-test invocation."""

    @classmethod
    def setup_class(cls):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        cls.data = yaml.safe_load((repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
        cls.test_job = cls.data["jobs"]["test"]
        cls.matrix = cls.test_job["strategy"]["matrix"]

    def test_matrix_covers_three_oses(self):
        oses = set(self.matrix["os"])
        assert {"ubuntu-latest", "windows-latest", "macos-latest"} <= oses, f"test matrix missing OSes: got {oses}"

    def test_matrix_covers_pyproject_target_floor(self):
        # pyproject.toml's target-version = "py310" — that floor
        # MUST appear in the matrix or we stop catching the
        # py310-specific regressions ruff would tolerate.
        versions = {str(v) for v in self.matrix["python-version"]}
        assert "3.10" in versions, f"test matrix missing 3.10 (pyproject floor): got {versions}"

    def test_matrix_covers_modern_python(self):
        versions = {str(v) for v in self.matrix["python-version"]}
        # At least one 3.12+ entry — language-level changes after
        # 3.10 (PEP 695 type params, etc.) need coverage.
        modern = {v for v in versions if v >= "3.12"}
        assert modern, f"test matrix lacks modern Python (3.12+): got {versions}"

    def test_test_job_runs_pytest_in_parallel(self):
        runs = [
            step.get("run", "") for step in self.test_job.get("steps", []) if isinstance(step, dict) and step.get("run")
        ]
        run_text = " \n ".join(runs)
        # Parallel via xdist + loadfile distribution (per
        # pyproject.toml comments on the YAML-mutator monolith).
        assert "pytest" in run_text, "test job must run pytest"
        assert "-n auto" in run_text, "test job missing xdist parallel flag `-n auto`"
        assert "--dist=loadfile" in run_text, (
            "test job missing `--dist=loadfile` (required for the YAML-mutator monolith)"
        )

    def test_test_job_does_not_fail_fast(self):
        # When one matrix cell fails we want the others to keep
        # running so the cross-OS picture is visible.
        assert self.test_job["strategy"].get("fail-fast") is False, "test matrix must set fail-fast: false"


class TestOmega38CiObsoleteRemoved:
    """The GitHub-default python-package.yml (Python 3.9-3.11 +
    flake8) is misaligned with this project. ω.38 supersedes it
    with ci.yml; pin that it stays removed so a future `gh repo
    fork`-style re-init doesn't quietly resurrect it."""

    def test_obsolete_workflow_file_removed(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        obsolete = repo / ".github" / "workflows" / "python-package.yml"
        assert not obsolete.exists(), (
            "GitHub-default python-package.yml is back — it's superseded "
            "by ci.yml (ω.38). Delete it to restore the contract."
        )

    def test_ci_workflow_is_canonical(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        # ci.yml is the only workflow that runs the audit chain.
        # python-publish.yml stays for the PyPI release flow.
        canonical = repo / ".github" / "workflows" / "ci.yml"
        assert canonical.is_file()

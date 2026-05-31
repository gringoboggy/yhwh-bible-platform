"""Tests for the mint-8 ``subprocess_stdin`` lint check.

The check (``scripts.lint_rules.check_subprocess_stdin``) is a commit-time guard
that every ``subprocess`` spawn call under scripts/ + dev/ passes an explicit
``stdin=`` keyword — the Windows WinError 6 / W-W1 mitigation (memory
``feedback_w_w1_subprocess_devnull``). These tests pin: (a) the check is
registered in ALL_CHECKS and returns the standard dict shape, (b) it passes on
the current (fixed) tree, and (c) the underlying AST detector actually FLAGS a
synthetic ``subprocess.run([...])`` lacking ``stdin=`` — so the guard is real,
not vacuously green.
"""

from __future__ import annotations

import ast

import pytest


class TestSubprocessStdinCheck:
    @classmethod
    def setup_class(cls):
        from scripts import lint_rules

        cls.mod = lint_rules

    def test_check_registered_in_all_checks(self):
        assert "subprocess_stdin" in self.mod.ALL_CHECKS
        assert self.mod.ALL_CHECKS["subprocess_stdin"] is self.mod.check_subprocess_stdin

    def test_check_returns_standard_dict_shape(self):
        r = self.mod.check_subprocess_stdin()
        assert isinstance(r, dict)
        for key in ("id", "name", "status", "message", "violations"):
            assert key in r, f"missing key {key!r}: {r}"
        assert r["id"] == "subprocess_stdin"
        assert r["status"] in {"pass", "warn", "fail"}
        assert isinstance(r["violations"], list)

    def test_check_does_not_fail_on_current_tree(self):
        # The guard ships WARN-tier (``_ENFORCE_SUBPROCESS_STDIN=False``) while
        # the remaining call sites are being fixed, then flips to a hard FAIL.
        # Pin that it never FAILs on the committed tree (would brick commits +
        # the ALL_CHECKS meta-contract); pass once clean, warn while in flight.
        r = self.mod.check_subprocess_stdin()
        assert r["status"] in {"pass", "warn"}, f"{r['message']}: {r['violations']}"
        # Each surfaced violation carries the standard {file,line,snippet} shape.
        for v in r["violations"]:
            assert {"file", "line", "snippet"} <= set(v), v


class TestSubprocessStdinDetector:
    """Unit-level: the AST detector must FLAG a missing-stdin spawn call and
    NOT flag one that supplies stdin (or a **kwargs splat)."""

    @classmethod
    def setup_class(cls):
        from scripts import lint_rules

        cls.detect = staticmethod(lint_rules._find_subprocess_calls_missing_stdin)

    @pytest.mark.parametrize(
        "snippet",
        [
            'subprocess.run(["ls"])',
            'subprocess.Popen(["x"], capture_output=True)',
            'subprocess.call(["x"])',
            'subprocess.check_call(["x"])',
            'subprocess.check_output(["x"])',
            'from subprocess import run\nrun(["x"])',  # bare name bound via from-import
        ],
    )
    def test_flags_missing_stdin(self, snippet):
        tree = ast.parse(snippet)
        assert self.detect(tree), f"detector failed to flag: {snippet!r}"

    def test_does_not_flag_local_run_helper(self):
        # Import-aware (mint-8 FP fix): a LOCAL run() with NO
        # `from subprocess import run` must NOT be mistaken for subprocess.run.
        # The project has several such helpers (ci.py, ship-check.py, run.py …).
        tree = ast.parse("def run(cmd):\n    return cmd\nrun(['x'])")
        assert not self.detect(tree)

    def test_does_not_flag_attr_run_on_non_subprocess(self):
        tree = ast.parse("pool.run(['x'])")
        assert not self.detect(tree)

    @pytest.mark.parametrize(
        "snippet",
        [
            'subprocess.run(["x"], stdin=subprocess.DEVNULL)',
            'subprocess.Popen(["x"], stdin=subprocess.PIPE)',
            'subprocess.run(["x"], **kw)',  # splat could carry stdin — don't false-flag
            'run(["x"], stdin=None)',
        ],
    )
    def test_does_not_flag_when_stdin_present(self, snippet):
        tree = ast.parse(snippet)
        assert not self.detect(tree), f"detector falsely flagged: {snippet!r}"

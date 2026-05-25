#!/usr/bin/env python3
"""W4.5 — local CI gate. Composes the project's gates into one command
(`make ci` / `python scripts/ci.py`):

  - ruff format --check        (BLOCKING — same as the pre-commit hook)
  - ruff check                 (report-only — the project keeps a visible
                                lint backlog; never blocks)
  - scripts/lint_rules.py      (BLOCKING — the 16 project-rule checks)
  - scripts/audit_types.py     (BLOCKING — mypy on the typed surface)
  - pytest                     (BLOCKING — the test suite)
  - coverage floor             (BLOCKING **iff** `coverage` is installed;
                                otherwise skipped with a hint)

Solo-maintainability: there is no git remote yet (history is bundle-backed-up
to E:/F:), so "CI" runs locally via `make ci`. The process exits 0 only when
every BLOCKING step passes. Dev/CI tools are declared in `requirements-dev.txt`;
`coverage` is optional — the floor activates after
`pip install -r requirements-dev.txt`.

The standard meta-tool shape (RULES §9): pure ``run_all() -> dict`` + a thin
``main()``. The subprocess runner is injectable so tests exercise the
composition logic without spawning real gates.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_PY = sys.executable

# A runner maps a command (argv list) -> (returncode, combined_output).
Runner = Callable[[list[str]], "tuple[int, str]"]


def _subprocess_runner(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(_REPO),
        stdin=subprocess.DEVNULL,  # W-W1: Windows pytest-from-PowerShell guard
        capture_output=True,
        text=True,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _coverage_available() -> bool:
    return importlib.util.find_spec("coverage") is not None


def run_all(
    *,
    runner: Runner | None = None,
    run_tests: bool = True,
    coverage_floor: int | None = None,
    coverage_installed: bool | None = None,
) -> dict:
    """Run the gates and return ``{"checks": [...], "summary": {...}}``.

    Each check is ``{id, name, status: pass|warn|fail, blocking: bool,
    message}``. ``summary.clean`` is True iff no BLOCKING check failed.

    ``runner`` / ``coverage_installed`` are injectable for tests."""
    run = runner or _subprocess_runner
    if coverage_floor is None:
        # Baseline measured 2026-05-25: scripts/ line coverage = 62% over the full
        # serial suite (`coverage run --source=scripts -m pytest`). The floor is 60
        # — a ~2-point ratchet just below measured, so coverage can't silently
        # regress while leaving headroom for run-to-run drift. Raise it as coverage
        # improves; override per-run via the COVERAGE_FLOOR env var.
        try:
            coverage_floor = int(os.environ.get("COVERAGE_FLOOR") or "60")
        except ValueError:
            coverage_floor = 60
    if coverage_installed is None:
        coverage_installed = _coverage_available()

    checks: list[dict] = []

    def add(cid: str, name: str, ok: bool, *, blocking: bool, message: str, skipped: bool = False) -> None:
        status = "warn" if skipped or (not ok and not blocking) else ("pass" if ok else "fail")
        checks.append({"id": cid, "name": name, "status": status, "blocking": blocking, "message": message})

    rc, out = run([_PY, "-m", "ruff", "format", "--check", "."])
    add(
        "format",
        "ruff format --check",
        rc == 0,
        blocking=True,
        message="all formatted" if rc == 0 else out.strip()[-300:],
    )

    rc, out = run([_PY, "-m", "ruff", "check", "."])
    add(
        "lint",
        "ruff check (report)",
        rc == 0,
        blocking=False,
        message="clean" if rc == 0 else "lint backlog (non-blocking)",
    )

    rc, out = run([_PY, "scripts/lint_rules.py"])
    add(
        "rules",
        "lint_rules",
        rc == 0,
        blocking=True,
        message=out.strip().splitlines()[-1][-200:] if out.strip() else "",
    )

    rc, out = run([_PY, "scripts/audit_types.py"])
    add(
        "types",
        "mypy (typed surface)",
        rc == 0,
        blocking=True,
        message=out.strip().splitlines()[-1][-200:] if out.strip() else "",
    )

    if run_tests:
        rc, out = run([_PY, "-m", "pytest", "-q"])
        add(
            "tests",
            "pytest",
            rc == 0,
            blocking=True,
            message=out.strip().splitlines()[-1][-200:] if out.strip() else "",
        )

        if coverage_installed:
            run([_PY, "-m", "coverage", "run", "--source=scripts", "-m", "pytest", "-q"])
            rc, out = run([_PY, "-m", "coverage", "report", f"--fail-under={coverage_floor}"])
            add(
                "coverage",
                f"coverage >= {coverage_floor}%",
                rc == 0,
                blocking=True,
                message=out.strip().splitlines()[-1][-120:] if out.strip() else "",
            )
        else:
            add(
                "coverage",
                "coverage floor",
                False,
                blocking=False,
                skipped=True,
                message="coverage not installed — pip install -r requirements-dev.txt",
            )

    blocking_fail = any(c["status"] == "fail" and c["blocking"] for c in checks)
    summary = {
        "total": len(checks),
        "pass": sum(1 for c in checks if c["status"] == "pass"),
        "warn": sum(1 for c in checks if c["status"] == "warn"),
        "fail": sum(1 for c in checks if c["status"] == "fail"),
        "clean": not blocking_fail,
    }
    return {"checks": checks, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="ci", description="W4.5 — local CI gate (format · lint · rules · mypy · tests · coverage)."
    )
    ap.add_argument(
        "--no-tests",
        action="store_true",
        help="skip the test + coverage steps (fast gate: format · lint · rules · mypy)",
    )
    args = ap.parse_args(argv)

    result = run_all(run_tests=not args.no_tests)
    marks = {"pass": "✓", "warn": "!", "fail": "✗"}
    for c in result["checks"]:
        print(f"  {marks[c['status']]} {c['name']:28} {c['message'][:90]}")
    s = result["summary"]
    verdict = "CLEAN" if s["clean"] else "FAIL"
    print(f"\n  {verdict}: {s['pass']} pass · {s['warn']} warn · {s['fail']} fail (blocking)")
    return 0 if s["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())

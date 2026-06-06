#!/usr/bin/env python3
"""ω.31 — type-checking audit wrapper around `mypy`.

Runs mypy against the project's typed surface (currently
`scripts/core/`, `scripts/build_edition.py`, and `scripts/validate_schemas.py`
— the exact set is the pyproject `[tool.mypy] files` list; expanded outward in
future ω.31.x phases as call-site annotations land). Returns 0 when no
type errors, 1 when real type errors remain. Suitable as a
recurring lint check + a pre-commit gate.

Per CLAUDE_PROJECT_RULES §10 "Standard library only on the
backend" — mypy is a dev-only tool, NOT a runtime dep. This
wrapper degrades gracefully when mypy isn't installed (returns
exit code 2 with a clear install hint), mirroring
`scripts/audit_dead_code.py` and `scripts/audit_deps.py`.

Usage::

    python scripts/audit_types.py
    python scripts/audit_types.py --json
    python scripts/audit_types.py --strict   # future stricter mode

The configured surface lives in `pyproject.toml` under
`[tool.mypy]` (`files = [...]`).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parent.parent


def mypy_available() -> bool:
    """Return True iff mypy is invocable on this machine."""
    if shutil.which("mypy") is not None:
        return True
    try:
        import mypy  # noqa: F401

        return True
    except ImportError:
        return False


def run_mypy(*, extra_args: list[str] | None = None) -> dict:
    """Invoke `python -m mypy` as a subprocess; return a structured
    result. Reads the project's `[tool.mypy]` config from
    pyproject.toml — no path arguments are passed because the config
    sets `files = [...]` already.

    Returns ``{ok, errors: [...], stdout, stderr, returncode}``.
    Each error is a parsed line: ``{file, line, message, code}``.
    Mypy exit codes: 0 = clean; 1 = type errors; 2 = invocation /
    config error.
    """
    if not mypy_available():
        return {
            "ok": False,
            "errors": [],
            "stdout": "",
            "stderr": "mypy not installed; run `pip install mypy`",
            "returncode": 127,
            "missing_tool": True,
        }
    args = [sys.executable, "-m", "mypy"]
    if extra_args:
        args.extend(extra_args)
    proc = subprocess.run(
        args,
        cwd=str(_REPO),
        stdin=subprocess.DEVNULL,  # W-W1 mitigation (τ.6.x.1)
        capture_output=True,
        text=True,
    )
    errors = _parse_mypy_output(proc.stdout)
    return {
        "ok": proc.returncode == 0 and not errors,
        "errors": errors,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "returncode": proc.returncode,
    }


_MYPY_LINE_RE = re.compile(
    r"^(?P<file>[^\s:]+(?::[^\s:]+)?):(?P<line>\d+):\s*"
    r"error:\s*(?P<message>.*?)(?:\s+\[(?P<code>[a-z0-9-]+)\])?\s*$"
)


def _parse_mypy_output(text: str) -> list[dict]:
    """Parse mypy's `<file>:<line>: error: <msg>  [code]` lines into
    structured records. Notes / warnings / summary lines are skipped."""
    errors: list[dict] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        m = _MYPY_LINE_RE.match(line)
        if not m:
            continue
        errors.append(
            {
                "file": m.group("file"),
                "line": int(m.group("line")),
                "message": m.group("message").strip(),
                "code": m.group("code") or "",
            }
        )
    return errors


def audit() -> dict:
    """High-level entry point. Wraps `run_mypy()` with the project's
    default config (sourced from `pyproject.toml`)."""
    return run_mypy()


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="audit_types",
        description=(
            "ω.31 — mypy type-checking audit. Wraps `mypy` with the project's [tool.mypy] config in pyproject.toml."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="machine-readable JSON output",
    )
    args = parser.parse_args(argv)

    result = audit()

    if result.get("missing_tool"):
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(
                "  ! mypy not installed.  Run `pip install mypy` to enable the audit.",
                file=sys.stderr,
            )
        return 2

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return 0 if result["ok"] else 1

    errors = result["errors"]
    if not errors:
        print("  ✓ no type errors (mypy, per pyproject [tool.mypy] files)")
        return 0
    print(f"  ✗ {len(errors)} type error(s):")
    for e in errors:
        suffix = f"  [{e['code']}]" if e["code"] else ""
        print(f"    {e['file']}:{e['line']}: {e['message']}{suffix}")
    print(
        "\n  Triage:\n"
        "    real type bug → fix the code\n"
        "    intentional pattern mypy can't see → "
        "add a justified `# type: ignore[<code>]` comment\n"
        "    third-party stubs missing → "
        "add to pyproject.toml [[tool.mypy.overrides]]\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

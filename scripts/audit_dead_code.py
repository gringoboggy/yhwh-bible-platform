#!/usr/bin/env python3
"""ω.26 — dead-code audit wrapper around `vulture`.

Runs vulture against `scripts/` plus the false-positive whitelist
at `scripts/.vulture_whitelist.py`. Returns 0 when no findings,
1 when real dead code remains. Suitable as a recurring lint check
+ a pre-commit gate.

Per CLAUDE_PROJECT_RULES §10 "Standard library only on the
backend" — vulture is a dev-only tool, NOT a runtime dep. This
wrapper degrades gracefully when vulture isn't installed (returns
exit code 2 with a clear install hint, the same shape as
`scripts/audit_deps.py` for pip-audit).

Usage::

    python scripts/audit_dead_code.py
    python scripts/audit_dead_code.py --json
    python scripts/audit_dead_code.py --min-confidence 70
    python scripts/audit_dead_code.py --include-tests   # off by default

Conventions:

  - Default min-confidence is 80 (high-signal findings only).
  - Default scope is `scripts/` only — tests/ has many fixture-
    style false positives (unused param names that pytest fills,
    defensive imports). Pass `--include-tests` to scan tests too.
  - The whitelist file lives alongside `scripts/` so vulture's
    "any name in this file is used" semantics cover the false
    positives uniformly.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parent.parent
_WHITELIST = _REPO / "scripts" / ".vulture_whitelist.py"


def vulture_available() -> bool:
    """Return True iff vulture is invocable on this machine."""
    if shutil.which("vulture") is not None:
        return True
    try:
        import vulture  # noqa: F401

        return True
    except ImportError:
        return False


def run_vulture(
    *,
    paths: list[Path],
    min_confidence: int = 80,
    whitelist: Path | None = None,
) -> dict:
    """Invoke vulture as a subprocess; return a structured result.

    Returns ``{ok, findings: [...], stdout, stderr, returncode}``.
    Each finding is the parsed line: ``{file, line, message,
    confidence}``. Vulture exit codes:

      - 0 = no findings
      - 1 = only low-confidence findings (rare with our threshold)
      - 3 = at least one high-confidence finding
      - other = invocation error
    """
    if not vulture_available():
        return {
            "ok": False,
            "findings": [],
            "stdout": "",
            "stderr": ("vulture not installed; run `pip install vulture`"),
            "returncode": 127,
            "missing_tool": True,
        }
    # All positional path args (including the whitelist file) MUST
    # come before the `--min-confidence` flag — vulture's argparse
    # rejects trailing positionals after options. Arrangement:
    # `vulture <scan_paths> <whitelist> --min-confidence N`.
    args = [
        sys.executable,
        "-m",
        "vulture",
        *(str(p) for p in paths),
    ]
    if whitelist is not None and whitelist.is_file():
        args.append(str(whitelist))
    args += ["--min-confidence", str(min_confidence)]
    proc = subprocess.run(
        args,
        cwd=str(_REPO),
        stdin=subprocess.DEVNULL,  # W-W1 mitigation (τ.6.x.1)
        capture_output=True,
        text=True,
    )
    findings = _parse_vulture_output(proc.stdout)
    return {
        "ok": proc.returncode in (0, 1) and not findings,
        "findings": findings,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "returncode": proc.returncode,
    }


def _parse_vulture_output(text: str) -> list[dict]:
    """Parse vulture's `<file>:<line>: <message> (NN% confidence)`
    lines into structured records."""
    findings: list[dict] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Format: <file>:<lineno>: <message> (NN% confidence)
        try:
            head, _, tail = line.rpartition("(")
            confidence_str = tail.rstrip(")")
            if not confidence_str.endswith(" confidence"):
                continue
            pct = int(confidence_str.split("%", 1)[0])
            file_part, _, message = head.strip().rstrip(":").partition(": ")
            file_path, _, lineno = file_part.rpartition(":")
        except (ValueError, IndexError):
            continue
        if not file_path or not lineno.isdigit():
            continue
        findings.append(
            {
                "file": file_path,
                "line": int(lineno),
                "message": message.strip().rstrip(":"),
                "confidence": pct,
            }
        )
    return findings


def audit(
    *,
    min_confidence: int = 80,
    include_tests: bool = False,
) -> dict:
    """High-level audit entry point. Picks the path set, calls
    vulture, returns a structured envelope ready for either CLI
    rendering or JSON consumption."""
    paths: list[Path] = [_REPO / "scripts"]
    if include_tests:
        paths.append(_REPO / "tests")
    return run_vulture(
        paths=paths,
        min_confidence=min_confidence,
        whitelist=_WHITELIST,
    )


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="audit_dead_code",
        description=(
            "ω.26 — vulture dead-code audit. Wraps `vulture` against scripts/ plus the false-positive whitelist."
        ),
    )
    parser.add_argument(
        "--min-confidence",
        type=int,
        default=80,
        help=("vulture confidence floor (default: 80; high-signal findings only)"),
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help=("also scan tests/ (default: scripts/ only — tests have many fixture-style false positives)"),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="machine-readable JSON output",
    )
    args = parser.parse_args(argv)

    result = audit(
        min_confidence=args.min_confidence,
        include_tests=args.include_tests,
    )

    if result.get("missing_tool"):
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(
                "  ! vulture not installed.  Run `pip install vulture` to enable the audit.",
                file=sys.stderr,
            )
        return 2

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return 0 if result["ok"] else 1

    findings = result["findings"]
    if not findings:
        print(f"  ✓ no dead code (vulture, --min-confidence {args.min_confidence})")
        return 0
    print(f"  ✗ {len(findings)} finding(s) at --min-confidence {args.min_confidence}:")
    for f in findings:
        print(f"    {f['file']}:{f['line']}: {f['message']}  ({f['confidence']}%)")
    print(
        "\n  Triage:\n"
        "    real dead code → delete\n"
        "    intentional but unused → "
        "add a justified entry to scripts/.vulture_whitelist.py\n"
        "    legitimately used → file an issue against vulture\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

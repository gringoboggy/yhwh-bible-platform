#!/usr/bin/env python3
"""ξ.11 — pip-audit wrapper.

Runs ``pip-audit`` against the project's ``requirements.txt`` (ξ.5)
and surfaces any HIGH / CRITICAL CVEs in transitive dependencies.

Usage::

    python scripts/audit_deps.py
    python scripts/audit_deps.py --json          # machine-readable
    python scripts/audit_deps.py --strict        # fail on any vuln
    python scripts/audit_deps.py --severity HIGH # min severity gate

Exit codes:
    0 — no vulnerabilities at the configured min-severity
    1 — at least one vulnerability found at the gate
    2 — pip-audit not installed (graceful — operator gets clear
        install instructions rather than an opaque ImportError)
    3 — requirements.txt missing or unreadable

pip-audit itself is NOT bundled as a project dependency (it's an
operator tool, not a runtime dep). Install via::

    pipx install pip-audit

Composes ξ.5's requirements.txt as the input. A future
ξ.11.1 could wire this into a pre-commit hook + CI gate.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parent.parent
_REQUIREMENTS = _REPO / "requirements.txt"

_SEVERITY_RANK = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
    "UNKNOWN": 0,
}


def _which_pip_audit() -> str | None:
    """Locate the pip-audit executable on PATH. Returns None if
    not installed."""
    return shutil.which("pip-audit")


def _severity_at_or_above(severity: str, threshold: str) -> bool:
    """True iff ``severity`` (CVE rating) is >= ``threshold``."""
    return _SEVERITY_RANK.get((severity or "").upper(), 0) >= _SEVERITY_RANK.get(
        (threshold or "").upper(),
        0,
    )


def run_pip_audit(
    *,
    requirements_path: Path | None = None,
    pip_audit_runner=None,
) -> dict:
    """Pure-function wrapper around ``pip-audit``.

    Returns a structured result envelope:
        {"status": "ok"|"error",
         "code": <error code>?,
         "message": <error message>?,
         "vulnerabilities": [{...}, ...],   # raw pip-audit output
         "tool_path": <pip-audit executable path>?,
        }

    ``pip_audit_runner`` is injectable for tests — defaults to a
    real subprocess call. The runner takes ``(executable, args)``
    and returns ``(returncode, stdout, stderr)``.
    """
    if requirements_path is None:
        requirements_path = _REQUIREMENTS
    requirements_path = Path(requirements_path)
    if not requirements_path.is_file():
        return {
            "status": "error",
            "code": "no_requirements_txt",
            "exit_code": 3,
            "message": (
                f"requirements.txt not found at {requirements_path}; "
                f"ξ.5 (dependency hygiene) creates it. Run "
                f"`python scripts/audit_deps.py --help` for setup."
            ),
        }

    tool = _which_pip_audit()
    if tool is None:
        return {
            "status": "error",
            "code": "pip_audit_missing",
            "exit_code": 2,
            "message": (
                "pip-audit is not on PATH. Install with "
                "`pipx install pip-audit` (preferred) or "
                "`pip install --user pip-audit`. Then re-run this "
                "command."
            ),
        }

    if pip_audit_runner is None:
        pip_audit_runner = _real_pip_audit_runner

    args = [
        "-r",
        str(requirements_path),
        "--format",
        "json",
        # `--disable-pip` skips the "now-checking-environment" pass
        # so we audit ONLY what's pinned in requirements.txt.
        "--disable-pip",
    ]
    rc, stdout, stderr = pip_audit_runner(tool, args)
    if rc != 0 and rc != 1:
        # 0 = clean, 1 = vulnerabilities found — both are "ran
        # successfully". Anything else is a tool-level failure.
        return {
            "status": "error",
            "code": "pip_audit_failed",
            "exit_code": rc,
            "message": (f"pip-audit exited with rc={rc}; stderr (last 500): {stderr[-500:] if stderr else '<empty>'}"),
        }
    try:
        parsed = json.loads(stdout) if stdout.strip() else {"dependencies": []}
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "code": "parse_failed",
            "exit_code": rc,
            "message": f"pip-audit JSON parse failed: {e}",
        }

    vulnerabilities: list[dict] = []
    for dep in parsed.get("dependencies", []) or []:
        for vuln in dep.get("vulns") or []:
            vulnerabilities.append(
                {
                    "package": dep.get("name") or "?",
                    "installed_version": dep.get("version") or "?",
                    "id": vuln.get("id") or "?",
                    "fix_versions": vuln.get("fix_versions") or [],
                    "description": (vuln.get("description") or "")[:300],
                    "severity": (vuln.get("severity") or "UNKNOWN").upper(),
                }
            )

    return {
        "status": "ok",
        "tool_path": tool,
        "requirements_path": str(requirements_path),
        "vulnerability_count": len(vulnerabilities),
        "vulnerabilities": vulnerabilities,
    }


def _real_pip_audit_runner(executable: str, args: list[str]):
    """Production subprocess runner. Tests inject a fake."""
    proc = subprocess.run(
        [executable, *args],
        capture_output=True,
        text=True,
        cwd=str(_REPO),
        timeout=120,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _filter_by_severity(vulns: list[dict], min_severity: str) -> list[dict]:
    """Drop vulnerabilities below ``min_severity``."""
    return [v for v in vulns if _severity_at_or_above(v.get("severity", ""), min_severity)]


def _summary_line(vuln: dict) -> str:
    return f"  {vuln['severity']:>8}  {vuln['package']} {vuln['installed_version']}  {vuln['id']}" + (
        f"  → fix in {', '.join(vuln['fix_versions'])}" if vuln["fix_versions"] else ""
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="audit_deps",
        description="ξ.11 — pip-audit wrapper for the YHWH platform.",
        epilog=(
            "Install pip-audit first: `pipx install pip-audit`. "
            "Then re-run. Exits 0 on clean, 1 on vulnerabilities at "
            "the configured severity, 2 if pip-audit is missing, "
            "3 if requirements.txt is missing."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of human summary",
    )
    parser.add_argument(
        "--severity",
        default="HIGH",
        choices=("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"),
        help="minimum CVE severity that fails the gate (default: HIGH)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="alias for --severity LOW: any vuln fails the gate",
    )
    parser.add_argument(
        "--requirements",
        default=str(_REQUIREMENTS),
        help=f"path to requirements.txt (default: {_REQUIREMENTS})",
    )
    args = parser.parse_args(argv)
    severity = "LOW" if args.strict else args.severity

    result = run_pip_audit(requirements_path=Path(args.requirements))
    if result["status"] == "error":
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(
                f"audit_deps: {result['code']}: {result['message']}",
                file=sys.stderr,
            )
        return result.get("exit_code") or 1

    vulns = result["vulnerabilities"]
    gating = _filter_by_severity(vulns, severity)

    if args.json:
        print(
            json.dumps(
                {
                    "status": "ok",
                    "vulnerability_count": len(vulns),
                    "gate_severity": severity,
                    "gating_vulnerability_count": len(gating),
                    "vulnerabilities": vulns,
                },
                indent=2,
            )
        )
    else:
        if not vulns:
            print("✓ no known vulnerabilities in requirements.txt")
        else:
            print(f"{len(vulns)} vulnerability(ies) found ({len(gating)} ≥ {severity} severity):")
            for v in sorted(
                vulns,
                key=lambda x: -_SEVERITY_RANK.get(x.get("severity") or "UNKNOWN", 0),
            ):
                print(_summary_line(v))
        if gating:
            print(
                f"\nfix or waive the {len(gating)} ≥ {severity} entries before shipping",
                file=sys.stderr,
            )
    return 1 if gating else 0


if __name__ == "__main__":
    sys.exit(main())

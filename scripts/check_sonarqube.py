#!/usr/bin/env python3
"""ω.47 — SonarCloud quality-gate preflight check.

Reads `sonar-project.properties` for the project key + organization,
then queries SonarCloud's REST API via the locally-installed
`sonar` CLI (sonar-cli, NOT the heavyweight SonarScanner that runs
the actual analysis). Returns a structured status dict the
/preflight dashboard renders alongside the other Tier-3 meta-tools
(rules_compliance, schema_compliance, etc.).

Usage::

    python scripts/check_sonarqube.py
    python scripts/check_sonarqube.py --json    # machine-readable

Exit codes (same conventions as the other audit scripts —
audit_deps.py, audit_dead_code.py, etc.):
    0 — quality gate OK
    1 — quality gate ERROR (real findings to address)
    2 — graceful skip: sonar CLI missing, sonar-project.properties
        missing, SonarCloud project not yet created, or no
        analysis run yet. Operator gets clear next-step hints
        rather than an opaque failure.

Composes:
    - `sonar-project.properties` (ω.47) as the project-key source
    - `sonar` CLI (installed via /sonarqube:sonar-integrate) as
      the authenticated transport

Wires into:
    - `scripts/api/preflight.py` as a new `sonarqube_quality_gate`
      check (in-process call to `check_quality_gate()` below)
    - The CI workflow can call this script directly in a future
      ω.47.1 follow-on once the SonarCloud project exists
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROPS_PATH = REPO_ROOT / "sonar-project.properties"


def _load_project_config() -> dict[str, str]:
    """Parse sonar-project.properties (simple key=value, # comments,
    backslash-continuation). Returns an empty dict if the file is
    missing — graceful degradation per the project's other meta-
    tools."""
    if not PROPS_PATH.is_file():
        return {}
    cfg: dict[str, str] = {}
    text = PROPS_PATH.read_text(encoding="utf-8")
    # Fold backslash-newline continuations before line-splitting.
    text = text.replace("\\\n", "")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        cfg[key.strip()] = value.strip()
    return cfg


def _sonar_cli_available() -> bool:
    """True if the `sonar` CLI is on PATH. The CLI must be installed
    AND authenticated (`sonar auth login`) for the API call to
    succeed; we let the API attempt surface auth issues rather than
    pre-flighting them (one less branch to maintain)."""
    return shutil.which("sonar") is not None


def _fetch_quality_gate(project_key: str, organization: str | None) -> tuple[str, dict | None, str | None]:
    """Call `sonar api get /api/qualitygates/project_status`.

    Returns (outcome, payload, err) where outcome is one of:
        "ok"          → payload is the parsed JSON response
        "api-error"   → err is the CLI's stderr/stdout
        "parse-error" → err is the first 200 chars of stdout
        "timeout"     → err is "request timed out"
    """
    endpoint = f"/api/qualitygates/project_status?projectKey={project_key}"
    if organization:
        endpoint += f"&organization={organization}"
    try:
        result = subprocess.run(
            ["sonar", "api", "get", endpoint],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return "timeout", None, "request timed out after 30s"
    if result.returncode != 0:
        return "api-error", None, (result.stderr or result.stdout or "").strip()
    try:
        return "ok", json.loads(result.stdout), None
    except json.JSONDecodeError:
        return "parse-error", None, result.stdout[:200]


def check_quality_gate() -> dict:
    """Run the check and return a status dict.

    Shape::

        {
            "status": "pass" | "warn" | "fail" | "skip",
            "message": "<one-line human-readable>",
            "details": {<machine fields — gate response, conditions, etc.>}
        }

    Status semantics:
        pass — SonarCloud reports `OK` on the gate
        fail — SonarCloud reports `ERROR` on the gate
        warn — SonarCloud reports `WARN`, OR the project exists but
               has never been scanned (`NONE`)
        skip — config or tool missing; nothing to evaluate yet

    Exit-code mapping (used by `main()`):
        pass → 0
        fail → 1
        warn / skip → 2
    """
    cfg = _load_project_config()
    project_key = cfg.get("sonar.projectKey")
    organization = cfg.get("sonar.organization")

    if not project_key:
        return {
            "status": "skip",
            "message": "sonar-project.properties missing or has no sonar.projectKey",
            "details": {"config_path": str(PROPS_PATH), "config_present": PROPS_PATH.is_file()},
        }

    if not _sonar_cli_available():
        return {
            "status": "skip",
            "message": "sonar CLI not installed (run /sonarqube:sonar-integrate)",
            "details": {"project_key": project_key},
        }

    outcome, payload, err = _fetch_quality_gate(project_key, organization)

    if outcome == "timeout":
        return {
            "status": "warn",
            "message": f"SonarCloud request timed out: {err}",
            "details": {"project_key": project_key},
        }

    if outcome == "api-error":
        # SonarCloud returns 404 for unknown projects. Treat as warn
        # so the dashboard surfaces "project not yet created" rather
        # than failing the gate hard before the operator has had a
        # chance to set up the SonarCloud side.
        if err and ("404" in err or "not found" in err.lower() or "no project" in err.lower()):
            return {
                "status": "warn",
                "message": f"SonarCloud project not yet created ({project_key})",
                "details": {"project_key": project_key, "hint": "visit sonarcloud.io/projects/create"},
            }
        return {
            "status": "fail",
            "message": f"sonar API error: {(err or '')[:200]}",
            "details": {"project_key": project_key, "raw_error": err},
        }

    if outcome == "parse-error":
        return {
            "status": "warn",
            "message": "sonar API returned non-JSON response",
            "details": {"project_key": project_key, "raw_excerpt": err},
        }

    # outcome == "ok"; payload is the parsed response.
    assert payload is not None  # for type-checkers
    project_status = payload.get("projectStatus") or {}
    gate_status = project_status.get("status")  # OK / WARN / ERROR / NONE
    conditions = project_status.get("conditions") or []
    failed_conditions = [c.get("metricKey") for c in conditions if c.get("status") == "ERROR"]

    if gate_status == "OK":
        return {
            "status": "pass",
            "message": f"quality gate: OK ({len(conditions)} conditions, all passing)",
            "details": {"project_key": project_key, "conditions_total": len(conditions)},
        }

    if gate_status == "ERROR":
        return {
            "status": "fail",
            "message": f"quality gate: ERROR ({len(failed_conditions)} failed condition(s))",
            "details": {
                "project_key": project_key,
                "failed_conditions": failed_conditions,
                "all_conditions": conditions,
            },
        }

    if gate_status == "WARN":
        return {
            "status": "warn",
            "message": f"quality gate: WARN ({len(failed_conditions)} marginal condition(s))",
            "details": {
                "project_key": project_key,
                "failed_conditions": failed_conditions,
            },
        }

    if gate_status == "NONE":
        # Project exists on SonarCloud but no analysis has been
        # uploaded yet. Two paths populate it:
        #   - Automatic Analysis (default on SonarCloud Cloud): push
        #     to the linked GitHub repo triggers a scan automatically.
        #   - SonarScanner CLI (only valid when Auto Analysis is
        #     disabled in the project's Administration > Analysis
        #     Method settings — otherwise manual scans are rejected
        #     as a duplicate path).
        return {
            "status": "warn",
            "message": (
                "no SonarCloud analysis run yet (push to GitHub triggers Auto Analysis, "
                "or run `sonar-scanner` when Auto is off)"
            ),
            "details": {"project_key": project_key},
        }

    # Unknown status string — treat conservatively as warn.
    return {
        "status": "warn",
        "message": f"unknown quality-gate status: {gate_status!r}",
        "details": {"project_key": project_key, "raw_status": gate_status},
    }


def _status_to_rc(status: str) -> int:
    return {"pass": 0, "fail": 1, "warn": 2, "skip": 2}.get(status, 2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report the SonarCloud quality-gate status for this project.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human-readable line.",
    )
    args = parser.parse_args(argv)

    result = check_quality_gate()

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        glyph = {"pass": "✓", "fail": "✗", "warn": "⚠", "skip": "○"}.get(result["status"], "?")
        print(f"  {glyph} {result['status'].upper():<5}  {result['message']}")

    return _status_to_rc(result["status"])


if __name__ == "__main__":
    sys.exit(main())

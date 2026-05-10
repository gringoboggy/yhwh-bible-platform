"""
epubcheck.py — Thin Python wrapper around the W3C/IDPF epubcheck Java
tool (Phase ω.14).

The PyPI package ``epubcheck`` bundles the official JAR; this module
wraps it as a pure function for the preflight readiness dashboard
without taking on the package's Python internals (which import at
class-construction time and run synchronously).

Public API::

    run_epubcheck(epub_path)  ->  dict

    {
      "status":  "pass" | "fail" | "warn" | "unavailable",
      "epub":    str (path basename),
      "errors":  int,
      "warnings": int,
      "messages": [
        {"id": "OPF-014", "severity": "ERROR",
         "message": "...", "locations": [...]},
        ...
      ],
      "version": str | None,
      "explanation": str (only set when status is 'unavailable'),
    }

The function never raises for expected failure modes (missing Java,
absent JAR, malformed EPUB, subprocess hang). Reserved for raising:
genuinely unexpected bugs.

§9 mental model: "Pure function + thin route adapter". Tests construct
the call directly; preflight composes via dict result.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


# Probe for Java + JAR at module import time so subsequent calls are
# fast. The probe is cheap (one subprocess) and the result is stable
# across a process lifetime.
_JAVA_PROBE: Optional[bool] = None
_JAR_PATH: Optional[Path] = None


def _locate_jar() -> Optional[Path]:
    """Find the epubcheck JAR. Prefers the env override
    ``EPUBCHECK_JAR``, falls back to the bundled JAR from the
    ``epubcheck`` PyPI package. Returns None if neither is present.
    """
    env_jar = os.environ.get("EPUBCHECK_JAR")
    if env_jar and Path(env_jar).is_file():
        return Path(env_jar)
    try:
        from epubcheck.const import EPUBCHECK as bundled
    except ImportError:
        return None
    p = Path(bundled)
    return p if p.is_file() else None


def _probe_java() -> bool:
    """True iff a working ``java`` executable is on PATH.

    The probe runs ``java -version``; epubcheck needs Java 8+, but the
    JAR itself raises a clear error if the version is too old. We
    don't enforce a version here — let the JAR's own check carry that
    failure message back.
    """
    if shutil.which("java") is None:
        return False
    try:
        # ``java -version`` writes to stderr; we don't care about the
        # text, only that the process completes successfully.
        subprocess.run(
            ["java", "-version"],
            capture_output=True,
            timeout=10,
            check=True,
        )
        return True
    except (subprocess.SubprocessError, OSError):
        return False


def _ensure_probed() -> None:
    """Memoize the Java + JAR probes for the process lifetime."""
    global _JAVA_PROBE, _JAR_PATH
    if _JAVA_PROBE is None:
        _JAVA_PROBE = _probe_java()
    if _JAR_PATH is None:
        _JAR_PATH = _locate_jar()


def reset_probe_cache() -> None:
    """Drop the Java + JAR probe cache. Tests use this to re-probe
    after monkey-patching shutil.which / the JAR locator."""
    global _JAVA_PROBE, _JAR_PATH
    _JAVA_PROBE = None
    _JAR_PATH = None


def is_available() -> tuple[bool, str]:
    """True iff both Java and the epubcheck JAR are reachable.

    Returns ``(available, explanation)``. The explanation is a short
    human-readable reason when the tool is NOT available, suitable
    for surfacing in the preflight dashboard. Empty string when
    available.
    """
    _ensure_probed()
    if not _JAVA_PROBE:
        return False, (
            "Java runtime not found on PATH. Install OpenJDK 8+ to "
            "enable EPUB validation; the rest of the platform stays "
            "usable without it."
        )
    if _JAR_PATH is None:
        return False, (
            "epubcheck JAR not found. Reinstall the `epubcheck` PyPI package or set EPUBCHECK_JAR to a JAR path."
        )
    return True, ""


def _classify_status(errors: int, warnings: int) -> str:
    """Derive an overall status from message counts."""
    if errors:
        return "fail"
    if warnings:
        return "warn"
    return "pass"


def _parse_epubcheck_json(text: str) -> dict:
    """Parse epubcheck's JSON output and return a normalised dict.

    Tolerant: missing keys are defaulted; malformed JSON returns a
    ``{"messages": [], "checker": {}}`` empty shape so the caller's
    accounting still works."""
    try:
        raw = json.loads(text) if text.strip() else {}
    except json.JSONDecodeError:
        raw = {}
    msgs_raw = raw.get("messages") or []
    messages = []
    for m in msgs_raw:
        if not isinstance(m, dict):
            continue
        messages.append(
            {
                "id": m.get("ID", "") or m.get("id", ""),
                "severity": m.get("severity", "INFO"),
                "message": m.get("message", ""),
                "locations": m.get("locations") or [],
            }
        )
    return {
        "messages": messages,
        "version": (raw.get("checker") or {}).get("checkerVersion"),
    }


def run_epubcheck(
    epub_path: str | Path,
    *,
    timeout: int = 60,
) -> dict:
    """Validate an EPUB at *epub_path* and return a normalised dict.

    See module docstring for the result shape. Never raises for the
    expected failure paths (missing Java, missing JAR, malformed EPUB);
    those become structured ``status`` values instead.
    """
    epub = Path(epub_path)
    epub_name = epub.name

    avail, why = is_available()
    if not avail:
        return {
            "status": "unavailable",
            "epub": epub_name,
            "errors": 0,
            "warnings": 0,
            "messages": [],
            "version": None,
            "explanation": why,
        }

    if not epub.is_file():
        return {
            "status": "fail",
            "epub": epub_name,
            "errors": 1,
            "warnings": 0,
            "messages": [
                {
                    "id": "RSC-001",
                    "severity": "ERROR",
                    "message": f"EPUB file not found: {epub}",
                    "locations": [],
                }
            ],
            "version": None,
        }

    _ensure_probed()
    cmd = [
        "java",
        "-jar",
        str(_JAR_PATH),
        str(epub),
        "--json",
        "-",  # JSON to stdout
        "--quiet",
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            text=True,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "fail",
            "epub": epub_name,
            "errors": 1,
            "warnings": 0,
            "messages": [
                {
                    "id": "TIMEOUT",
                    "severity": "ERROR",
                    "message": f"epubcheck timed out after {timeout}s",
                    "locations": [],
                }
            ],
            "version": None,
        }
    except OSError as e:
        # Should be unreachable after the is_available() probe, but
        # cover it defensively rather than letting an OSError crash
        # the preflight aggregator.
        return {
            "status": "unavailable",
            "epub": epub_name,
            "errors": 0,
            "warnings": 0,
            "messages": [],
            "version": None,
            "explanation": f"Failed to launch epubcheck: {e}",
        }

    parsed = _parse_epubcheck_json(proc.stdout)
    errors = sum(1 for m in parsed["messages"] if m["severity"] in ("ERROR", "FATAL"))
    warnings = sum(1 for m in parsed["messages"] if m["severity"] == "WARNING")
    return {
        "status": _classify_status(errors, warnings),
        "epub": epub_name,
        "errors": errors,
        "warnings": warnings,
        "messages": parsed["messages"],
        "version": parsed["version"],
    }


def run_epubcheck_on_dir(
    directory: str | Path,
    *,
    timeout_per_file: int = 60,
) -> dict:
    """Validate every ``*.epub`` in *directory*. Returns an aggregate
    dict suitable for direct surfacing in the preflight dashboard.

    Result shape::

        {
          "status":   "pass" | "fail" | "warn" | "unavailable" | "empty",
          "n_epubs":  int,
          "results":  [<run_epubcheck output>, ...],
          "totals":   {"errors": int, "warnings": int},
          "explanation": str (set when status is 'unavailable' or 'empty'),
        }

    Empty directory → status='empty'. Tooling unavailable → status
    propagates from is_available() (without scanning files).
    """
    d = Path(directory)
    if not d.is_dir():
        return {
            "status": "empty",
            "n_epubs": 0,
            "results": [],
            "totals": {"errors": 0, "warnings": 0},
            "explanation": (
                f"Directory not found: {d}. Build at least one EPUB "
                f"via `python scripts/build_edition.py <id>` to populate."
            ),
        }
    epubs = sorted(d.glob("*.epub"))
    if not epubs:
        return {
            "status": "empty",
            "n_epubs": 0,
            "results": [],
            "totals": {"errors": 0, "warnings": 0},
            "explanation": (f"No *.epub files in {d}. Build at least one edition to enable EPUB validation."),
        }
    avail, why = is_available()
    if not avail:
        return {
            "status": "unavailable",
            "n_epubs": len(epubs),
            "results": [],
            "totals": {"errors": 0, "warnings": 0},
            "explanation": why,
        }

    results = []
    total_errors = 0
    total_warnings = 0
    overall = "pass"
    for ep in epubs:
        r = run_epubcheck(ep, timeout=timeout_per_file)
        results.append(r)
        total_errors += r.get("errors", 0)
        total_warnings += r.get("warnings", 0)
        if r["status"] == "fail":
            overall = "fail"
        elif r["status"] == "warn" and overall != "fail":
            overall = "warn"

    return {
        "status": overall,
        "n_epubs": len(epubs),
        "results": results,
        "totals": {"errors": total_errors, "warnings": total_warnings},
    }

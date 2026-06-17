#!/usr/bin/env python3
"""Run the pytest gate one test FILE at a time (WIN overnight shard runner).

Avoids a single multi-hour pytest process that session harnesses may kill.
Writes ``dev/.pytest-gate-report.txt`` with per-file results.

Usage::

    py -3 scripts/pytest_gate_shard.py
    py -3 scripts/pytest_gate_shard.py --from tests/test_scripts.py
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REPORT = REPO / "dev" / ".pytest-gate-report.txt"
MARKER = "not slow and not done_gate"


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line)
    with REPORT.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def test_files(start_from: str | None) -> list[Path]:
    files = sorted((REPO / "tests").glob("test_*.py"))
    if start_from:
        p = Path(start_from)
        if p not in files:
            raise SystemExit(f"--from not found: {start_from}")
        files = files[files.index(p) :]
    return files


def _pending_timeout_files(report_text: str) -> list[Path]:
    """Files whose latest report line is TIMEOUT (skip already-passed retries)."""
    last: dict[str, str] = {}
    for line in report_text.splitlines():
        if "] " not in line:
            continue
        body = line.split("] ", 1)[1]
        for kind in ("PASS", "FAIL", "TIMEOUT", "SKIP"):
            prefix = f"{kind} "
            if not body.startswith(prefix):
                continue
            rest = body[len(prefix) :]
            rel = rest.split(":", 1)[0].strip() if kind == "PASS" else rest.strip()
            last[rel] = kind
            break
    return [REPO / rel for rel, kind in sorted(last.items()) if kind == "TIMEOUT"]


def run_file(path: Path, *, timeout_sec: int) -> tuple[int, str]:
    env = {**os.environ, "PYTHONUTF8": "1"}
    bt = Path(os.environ.get("LOCALAPPDATA", "/tmp")) / "Temp" / "yhwh-pytest" / "shard"
    bt.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(path),
        "-q",
        "--tb=line",
        "-p",
        "no:cacheprovider",
        "-m",
        MARKER,
        f"--basetemp={bt}",
    ]
    p = subprocess.run(
        cmd,
        cwd=str(REPO),
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    tail = (p.stdout or "") + (p.stderr or "")
    summary = tail.strip().splitlines()[-1] if tail.strip() else f"exit {p.returncode}"
    # pytest exit 5 = nothing collected; with -m filter that means all tests deselected (expected).
    if p.returncode == 5 and "deselected" in summary.lower():
        return 0, f"SKIP (marker) {summary}"
    return p.returncode, summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Shard pytest gate by test file.")
    ap.add_argument("--from", dest="start_from", default=None, help="resume from this test file")
    ap.add_argument(
        "--retry-timeouts",
        action="store_true",
        help="re-run files whose latest report line is TIMEOUT",
    )
    ap.add_argument(
        "--timeout-sec",
        type=int,
        default=1200,
        help="per-file subprocess timeout (default 1200; use 2400+ for slow build tests)",
    )
    args = ap.parse_args(argv)

    if not REPORT.exists():
        REPORT.write_text(f"# pytest gate shard report marker={MARKER}\n", encoding="utf-8")

    timeout_sec = args.timeout_sec
    files = test_files(args.start_from)
    if args.retry_timeouts and REPORT.exists():
        files = _pending_timeout_files(REPORT.read_text(encoding="utf-8")) or files
        if timeout_sec == 1200:
            timeout_sec = 4800
        _log(f"retry-timeouts: {len(files)} file(s) timeout_sec={timeout_sec}")

    fails = 0
    for path in files:
        rel = path.relative_to(REPO).as_posix()
        _log(f"START {rel}")
        try:
            rc, summary = run_file(path, timeout_sec=timeout_sec)
        except subprocess.TimeoutExpired:
            _log(f"TIMEOUT {rel}")
            fails += 1
            continue
        if rc == 0:
            _log(f"PASS {rel}: {summary}")
        else:
            _log(f"FAIL {rel}: {summary}")
            fails += 1

    _log(f"DONE fails={fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

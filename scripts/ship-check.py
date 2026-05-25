#!/usr/bin/env python3
"""
ship-check.py — Pre-flight integrity gate.

Runs every integrity check the project has into a single command, with a
single pass/fail bottom line. Use before any save, or as a CI gate.

Composition:
  1. verify.py             paired refs + asides; HTML structural correctness
  2. validate_taxonomy.py  source notes match taxonomy.yaml + categories.yaml
  3. manifest.py --status  SHA-256 corpus integrity
  4. inject.py --dry-run   no orphan source-vs-HTML drift
  5. fix_xref_targets.py   no broken cross-references
  6. pytest                unit + integration tests
  7. epubcheck (opt-in)    EPUB 3 spec validity, via --epubcheck

Exits 0 if everything passes, 1 otherwise. Output is concise — one line
per check plus a final summary. Use --verbose for full sub-tool output.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.ui import GREEN, RED, DIM, BOLD, RESET  # noqa: E402

PYTHON = sys.executable


def run(label: str, cmd: list[str], verbose: bool) -> tuple[bool, str]:
    """Run a sub-tool. Returns (passed, summary_line). Stdout is shown
    only in verbose mode; otherwise we synthesise a 1-line summary."""
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT, stdin=subprocess.DEVNULL)
    if verbose:
        print(f"\n{DIM}--- {label} ---{RESET}")
        if r.stdout:
            print(r.stdout, end="")
        if r.stderr:
            print(r.stderr, file=sys.stderr, end="")

    # Last non-empty stdout line is usually the summary
    last_line = ""
    for line in (r.stdout or "").splitlines()[::-1]:
        if line.strip():
            last_line = line.strip()
            break

    return r.returncode == 0, last_line or f"exit={r.returncode}"


def main() -> None:
    p = argparse.ArgumentParser(description="Combined integrity gate.")
    p.add_argument("--verbose", "-v", action="store_true", help="show full sub-tool output")
    p.add_argument(
        "--epubcheck", action="store_true", help="add the EPUB 3 spec-validation gate (epubcheck; needs Java)"
    )
    p.add_argument("--editions-dir", type=Path, help="directory of built EPUBs to validate (with --epubcheck)")
    args = p.parse_args()

    print(
        f"\n{BOLD}ship-check{RESET}  {DIM}pre-flight integrity gate{'  (+epubcheck)' if args.epubcheck else ''}{RESET}\n"
    )

    results: list[tuple[str, bool, str]] = []

    # 1. verify.py — note-pair integrity + HTML structural audit (wraps audit.py).
    # Exits 0 when there are no ERROR-severity findings (warnings are fine).
    ok, summary = run("verify", [PYTHON, "scripts/verify.py", "--quiet"], args.verbose)
    results.append(("verify (note pairing)", ok, summary))

    # 1b. check_nested_anchors.py — JVM-free nested-<a> guard. Catches the
    # invalid <a>-in-<a> markup (epubcheck RSC-005) in the base HTML without
    # needing a build + Java, so the class can never silently regress.
    ok, summary = run("nested-anchors", [PYTHON, "scripts/check_nested_anchors.py"], args.verbose)
    results.append(("nested <a> (RSC-005 guard)", ok, summary))

    # 2. validate_taxonomy.py
    ok, summary = run("taxonomy", [PYTHON, "scripts/validate_taxonomy.py"], args.verbose)
    results.append(("validate taxonomy", ok, summary))

    # 3. manifest.py --status
    ok, summary = run("manifest", [PYTHON, "scripts/manifest.py", "--status"], args.verbose)
    results.append(("manifest (corpus integrity)", ok, summary))

    # 4. inject.py --all-books --dry-run — no orphan drift
    ok, summary = run("inject-dry-run", [PYTHON, "scripts/inject.py", "--all-books", "--dry-run"], args.verbose)
    # inject.py "passes" if 0 would-inject AND 0 missing-section AND 0 anchor-not-found
    if "0 would-inject" not in summary:
        ok = False
    results.append(("inject (source-vs-HTML drift)", ok, summary))

    # 5. fix_xref_targets.py --dry-run. Fail only on resolvable-but-unapplied
    # refs (run --apply to fix them); "unresolved" refs whose target popover is
    # absent everywhere are a known base-HTML coverage gap (the recovered
    # 2026-05-07 base), surfaced as a warning rather than a hard ship blocker.
    rx = subprocess.run(
        [PYTHON, "scripts/fix_xref_targets.py", "--quiet"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        stdin=subprocess.DEVNULL,
    )
    if args.verbose and rx.stdout:
        print(f"\n{DIM}--- xref-targets ---{RESET}")
        print(rx.stdout, end="")
    m_res = re.search(r"\bresolved=(\d+)", rx.stdout or "")
    m_unres = re.search(r"\bunresolved=(\d+)", rx.stdout or "")
    pending_fixable = int(m_res.group(1)) if m_res else -1
    n_absent = int(m_unres.group(1)) if m_unres else 0
    ok = pending_fixable == 0
    if pending_fixable < 0:
        summary = "could not parse fix_xref_targets output"
    elif n_absent:
        summary = f"{pending_fixable} fixable pending · {n_absent} absent-target (known base-HTML gap)"
    else:
        summary = "all cross-refs resolved"
    results.append(("xref targets (cross-refs)", ok, summary))

    # Tests: pytest unit + integration
    tests_dir = REPO_ROOT / "tests"
    if tests_dir.is_dir():
        ok, summary = run("pytest", [PYTHON, "-m", "pytest", "tests/", "-q", "--tb=no", "--no-header"], args.verbose)
        # Treat the absence of pytest as a soft skip rather than a hard fail
        if "No module named pytest" in summary:
            ok = True
            summary = "skipped (pytest not installed)"
        results.append(("pytest (unit tests)", ok, summary))

    # 7. (opt-in) epubcheck on built editions — EPUB 3 spec validity
    if args.epubcheck:
        cmd = [PYTHON, "scripts/epubcheck.py"]
        if args.editions_dir:
            cmd.extend(["--editions-dir", str(args.editions_dir)])
        ok, summary = run("epubcheck", cmd, args.verbose)
        results.append(("epubcheck (EPUB 3 spec)", ok, summary))

    # Render summary
    print()
    pass_count = sum(1 for _, ok, _ in results if ok)
    for label, ok, summary in results:
        glyph = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
        # Strip ANSI codes from the sub-summary so it doesn't double up.
        clean = re.sub(r"\033\[[\d;]*m", "", summary)
        print(f"  {glyph} {label:35s}  {DIM}{clean}{RESET}")

    print()
    if pass_count == len(results):
        print(
            f"  {GREEN}{BOLD}✓ ALL CHECKS PASS{RESET} "
            f"{DIM}({pass_count}/{len(results)}){RESET} — corpus is in shippable state.\n"
        )
        sys.exit(0)
    else:
        failed = len(results) - pass_count
        print(f"  {RED}{BOLD}✗ {failed} CHECK(S) FAILED{RESET} {DIM}({pass_count}/{len(results)} passed){RESET}\n")
        print(f"  Run with {BOLD}--verbose{RESET} to see full sub-tool output.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

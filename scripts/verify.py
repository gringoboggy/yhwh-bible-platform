#!/usr/bin/env python3
"""
verify.py — friendly wrapper around audit.py.

Runs the full audit and prints a compact summary suitable for daily use.
Exits non-zero if any ERROR-severity issues are found, so it can be used
as a pre-build check or in scripts.

Examples:
  python3 scripts/verify.py              # full audit
  python3 scripts/verify.py --category B # one category
  python3 scripts/verify.py --quiet      # only print summary line
  python3 scripts/verify.py --strict     # also fail on WARN
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main():
    p = argparse.ArgumentParser(description="Friendly audit wrapper.")
    p.add_argument("--category", choices=["A", "B", "C"], help="run only one audit category")
    p.add_argument("--quiet", action="store_true", help="only print the summary line")
    p.add_argument("--strict", action="store_true", help="exit non-zero on WARN as well as ERROR")
    args = p.parse_args()

    cmd = ["python3", "audit.py"]
    if args.category:
        cmd += ["--category", args.category]
    if args.quiet:
        cmd += ["--quiet"]

    result = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    out = result.stdout

    # Strip ANSI codes for parsing
    plain = re.sub(r"\x1b\[[0-9;]*m", "", out)
    n_err = sum(1 for ln in plain.splitlines() if "[ERROR]" in ln)
    n_warn = sum(1 for ln in plain.splitlines() if "[WARN]" in ln)
    n_info = sum(1 for ln in plain.splitlines() if "[INFO]" in ln)
    paired_match = re.search(r"(\d+)/(\d+)\s+paired", plain)
    paired_str = paired_match.group(0) if paired_match else "paired-count not reported"

    if not args.quiet:
        print(out, end="")
    else:
        # In quiet mode, audit.py still prints lots; replace with minimal.
        pass

    # Compact summary line
    status_color = "\033[92m" if n_err == 0 and (not args.strict or n_warn == 0) else "\033[91m"
    reset = "\033[0m"
    sym = "✓" if n_err == 0 and (not args.strict or n_warn == 0) else "✗"
    print(f"\n{status_color}{sym} verify: errors={n_err}  warnings={n_warn}  info={n_info}  {paired_str}{reset}")

    if n_err > 0:
        sys.exit(1)
    if args.strict and n_warn > 0:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()

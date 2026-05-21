#!/usr/bin/env python3
"""
run.py — orchestrator for the daily workflow.

Sequence:
  1. Run the audit (initial state).
  2. For each book that has notes in content/notes/<code>.py, run its injector
     in dry-run mode to detect pending notes (notes in the file but not yet
     injected into HTML).
  3. If any book has pending injections, prompt before applying them
     (or skip prompt if --yes).
  4. Apply pending injections.
  5. Re-run the audit. If anything regressed, exit non-zero.

This script never builds the EPUB — that remains a manual step (`bash build.sh`)
per the project's explicit safety rule.

Examples:
  python3 scripts/run.py             # interactive: prompt before injecting
  python3 scripts/run.py --yes       # auto-apply all pending injections
  python3 scripts/run.py --check     # dry-run only, never modifies HTML
  python3 scripts/run.py --book gen  # operate on one book
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config
from content.notes import load_notes


def info(msg, color=""):
    reset = "\033[0m" if color else ""
    print(f"{color}{msg}{reset}")


def run(cmd, cwd=None, capture=True):
    return subprocess.run(cmd, cwd=cwd or str(REPO_ROOT), capture_output=capture, text=True)


def parse_inject_summary(stdout, _code):
    """Parse scripts/inject.py's TOTAL line — '… N scanned · M would-inject ·
    K already in HTML' — into (inserted, already, miss). 'would-inject' is the
    pending count; miss = the 'anchor text not found' tail."""
    clean = re.sub(r"\x1b\[[0-9;]*m", "", stdout)
    m = re.search(
        r"(\d+)\s+scanned\s*·\s*(\d+)\s+(?:would[- ]inject|injected)\s*·\s*(\d+)\s+already",
        clean,
    )
    if not m:
        return None
    mm = re.search(r"(\d+)\s+note\(s\) had anchor", clean)
    return int(m.group(2)), int(m.group(3)), (int(mm.group(1)) if mm else 0)


def injector_cmd(book, dry_run):
    # The unified scripts/inject.py replaces the lost source_archive/add_commentary.py
    # (Strategy A) + kings_session/strategy_b_inject.py (Strategy B) — it dispatches
    # by the book's strategy internally and uses epub_working/ as the target.
    code = book["code"]
    cmd = [sys.executable, "scripts/inject.py", "--book", code]
    if dry_run:
        cmd.append("--dry-run")
    return cmd


def find_pending(books_to_check):
    """Return list of (book, inserted, already, miss) for books with
    pending injections (inserted > 0 in dry-run)."""
    pending = []
    print(f"\nScanning {len(books_to_check)} books for pending injections...")
    for book in books_to_check:
        code = book["code"]
        try:
            notes = load_notes(code)
        except Exception:
            notes = []
        if not notes:
            continue
        result = run(injector_cmd(book, dry_run=True))
        summary = parse_inject_summary(result.stdout, code)
        if summary is None:
            print(f"  {code:5}  ⚠ couldn't parse injector output")
            continue
        ins, alr, mis = summary
        flag = ""
        if ins > 0:
            flag += f"  → \033[93m{ins} pending\033[0m"
        if mis > 0:
            flag += f"  → \033[91m{mis} anchor-miss\033[0m"
        print(f"  {code:5}  notes={len(notes):>3}  injected={alr:>3}  pending={ins:>2}  miss={mis}{flag}")
        if ins > 0 or mis > 0:
            pending.append((book, ins, alr, mis))
    return pending


def main():  # noqa: C901  (legacy; refactor risk > benefit)
    p = argparse.ArgumentParser(description="Orchestrate audit + pending injections.")
    p.add_argument("--yes", "-y", action="store_true", help="auto-apply pending injections without prompting")
    p.add_argument("--check", action="store_true", help="dry-run only — never modify HTML")
    p.add_argument("--book", help="operate on a single book code")
    p.add_argument(
        "--skip-initial-audit",
        action="store_true",
        help="skip the initial audit (faster if you just ran it)",
    )
    args = p.parse_args()

    # 1. Initial audit
    if not args.skip_initial_audit:
        info("\n=== Initial audit ===", "\033[1m")
        result = run([sys.executable, "scripts/verify.py", "--quiet"])
        print(result.stdout, end="")
        if result.returncode != 0:
            info("\nInitial audit reports errors — investigate before proceeding.", "\033[91m")
            sys.exit(1)

    # 2. Scan for pending injections
    info("\n=== Pending injections ===", "\033[1m")
    books = [config.get_book(args.book)] if args.book else list(config.load_books())
    pending = find_pending(books)

    if not pending:
        info("\n✓ No pending injections — system is in sync.", "\033[92m")
        sys.exit(0)

    # 3. Decide: apply or stop
    n_ins = sum(p[1] for p in pending)
    n_mis = sum(p[3] for p in pending)
    info(
        f"\n{len(pending)} book(s) have pending changes: {n_ins} note(s) to insert, {n_mis} anchor-miss(es).",
        "\033[93m",
    )

    if args.check:
        info("--check given: not applying.", "\033[94m")
        sys.exit(0 if n_mis == 0 else 1)

    if not args.yes:
        try:
            ans = input("\nApply pending injections? [y/N]: ").strip().lower()
        except EOFError:
            ans = "n"
        if ans not in ("y", "yes"):
            info("Aborted.", "\033[94m")
            sys.exit(0)

    # 4. Apply
    info("\n=== Applying injections ===", "\033[1m")
    for book, ins, _, mis in pending:
        if mis > 0:
            info(f"  {book['code']}: skipping (has anchor misses — fix them first)", "\033[91m")
            continue
        if ins == 0:
            continue
        result = run(injector_cmd(book, dry_run=False))
        # Show only the summary line
        for line in result.stdout.splitlines():
            if "summary" in line or "inserted=" in line.lower():
                info(f"  {book['code']}: {line.strip()}")

    # 5. Re-audit
    info("\n=== Final audit ===", "\033[1m")
    result = run([sys.executable, "scripts/verify.py"])
    print(result.stdout, end="")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

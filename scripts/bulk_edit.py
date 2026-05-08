#!/usr/bin/env python3
"""
bulk_edit.py — Find/replace across ``content/notes/*.py`` with safety rails.

Apply a substring or regex substitution to all (or filtered) notes files.
Dry-run by default; shows a unified diff of every change. With ``--apply``,
writes the changes and immediately runs ``scripts/verify.py`` so you see
the audit consequences in the same command.

Operates at the **text level** — fast, formatting-preserving, and works
on any string in the file. Because the replacement is not AST-scoped,
review the dry-run diff before applying. To be conservative, prefer
patterns that only appear inside note bodies (HTML phrases, transliterations,
typos in prose).

Examples:
    python3 scripts/bulk_edit.py "vinyard" "vineyard"
        # dry-run substring replace across all notes files

    python3 scripts/bulk_edit.py "vinyard" "vineyard" --apply
        # write changes, then run verify.py

    python3 scripts/bulk_edit.py --regex "shma[ʿ']" "shema" --apply
        # regex mode (case-sensitive by default)

    python3 scripts/bulk_edit.py "Yahweh" "YHWH" --book gen
        # filter to one book

    python3 scripts/bulk_edit.py "<i>" "<em>" --regex
        # presentational → semantic (regex False so literal angle brackets are fine)

Exit codes:
    0  no changes (or applied cleanly with verify passing)
    1  changes pending (dry-run had matches; rerun with --apply)
    2  setup error, or verify.py reported errors after --apply
"""

import argparse
import difflib
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTES_DIR = REPO_ROOT / "content" / "notes"
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.notes_io import atomic_write, ensure_backup  # noqa: E402

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BLUE = "\033[94m"
RESET = "\033[0m"


def apply_replace(
    text: str,
    pattern: str,
    replacement: str,
    regex: bool,
    case_insensitive: bool,
) -> tuple[str, int]:
    """Return (new_text, n_replacements)."""
    if regex:
        flags = re.IGNORECASE if case_insensitive else 0
        try:
            new_text, n = re.subn(pattern, replacement, text, flags=flags)
            return new_text, n
        except re.error as e:
            print(f"{RED}ERROR: bad regex {pattern!r}: {e}{RESET}", file=sys.stderr)
            sys.exit(2)
    if case_insensitive:
        # Use a case-insensitive regex on the escaped literal.
        rx = re.compile(re.escape(pattern), re.IGNORECASE)
        new_text, n = rx.subn(replacement, text)
        return new_text, n
    n = text.count(pattern)
    if n == 0:
        return text, 0
    return text.replace(pattern, replacement), n


def show_diff(filename: str, old: str, new: str, context_lines: int = 1) -> None:
    """Print a colorized unified diff. Skips file headers."""
    diff = difflib.unified_diff(
        old.splitlines(keepends=False),
        new.splitlines(keepends=False),
        fromfile=f"{filename} (before)",
        tofile=f"{filename} (after)",
        n=context_lines,
        lineterm="",
    )
    for line in diff:
        if line.startswith("+++") or line.startswith("---"):
            print(f"  {DIM}{line}{RESET}")
        elif line.startswith("@@"):
            print(f"  {BLUE}{line}{RESET}")
        elif line.startswith("+"):
            print(f"  {GREEN}{line}{RESET}")
        elif line.startswith("-"):
            print(f"  {RED}{line}{RESET}")
        else:
            print(f"  {DIM}{line}{RESET}")


def main() -> None:
    p = argparse.ArgumentParser(
        description="Find/replace across content/notes/*.py with safety rails.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("pattern", help="substring (or regex with --regex) to find")
    p.add_argument("replacement", help="replacement string")
    p.add_argument("--regex", action="store_true", help="treat pattern as regex")
    p.add_argument(
        "-i",
        "--case-insensitive",
        action="store_true",
        help="case-insensitive matching",
    )
    p.add_argument("--book", help="restrict to one book code")
    p.add_argument("--apply", action="store_true", help="write changes (default is dry-run)")
    p.add_argument(
        "--no-verify",
        action="store_true",
        help="skip the post-apply verify.py run",
    )
    p.add_argument(
        "--context",
        type=int,
        default=1,
        help="lines of context per diff hunk (default 1)",
    )
    p.add_argument("--quiet", action="store_true", help="only print the summary line")
    args = p.parse_args()

    if not NOTES_DIR.is_dir():
        print(f"{RED}ERROR: not a directory: {NOTES_DIR}{RESET}", file=sys.stderr)
        sys.exit(2)

    # File set
    files = sorted(NOTES_DIR.glob("*.py"))
    files = [f for f in files if f.name != "__init__.py"]
    if args.book:
        files = [f for f in files if f.stem == args.book]
        if not files:
            print(f"{RED}ERROR: no notes file for book {args.book!r}{RESET}", file=sys.stderr)
            sys.exit(2)

    total_repls = 0
    files_changed = []  # (path, old, new, n)

    for f in files:
        old = f.read_text(encoding="utf-8")
        new, n = apply_replace(
            old, args.pattern, args.replacement, args.regex, args.case_insensitive
        )
        if n > 0 and new != old:
            files_changed.append((f, old, new, n))
            total_repls += n

    # Display
    if not args.quiet:
        for f, old, new, n in files_changed:
            verb = "would change" if not args.apply else "changed"
            print(
                f"\n{YELLOW}{f.relative_to(REPO_ROOT)}{RESET}: "
                f"{verb} {n} occurrence{'s' if n != 1 else ''}"
            )
            show_diff(f.name, old, new, args.context)

    # Apply
    if args.apply:
        for f, _old, new, _n in files_changed:
            ensure_backup(f)
            atomic_write(f, new)

    # Summary
    if total_repls == 0:
        print(f"\n{GREEN}○ bulk_edit: no matches.{RESET}")
        sys.exit(0)

    color, sym = (GREEN, "✓") if args.apply else (YELLOW, "⚠")
    action = "applied" if args.apply else "dry-run"
    print(
        f"\n{color}{sym} bulk_edit ({action}): {total_repls} replacement(s) "
        f"across {len(files_changed)} file(s){RESET}"
    )

    # Auto-verify after apply
    if args.apply and not args.no_verify:
        print(f"\n{DIM}running verify.py …{RESET}")
        result = subprocess.run(
            ["python3", str(REPO_ROOT / "scripts" / "verify.py"), "--quiet"],
            cwd=str(REPO_ROOT),
        )
        if result.returncode != 0:
            print(f"{RED}✗ verify.py reported errors — review the changes{RESET}", file=sys.stderr)
            sys.exit(2)
        sys.exit(0)

    if not args.apply:
        print(f"\n  re-run with --apply to write changes")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()

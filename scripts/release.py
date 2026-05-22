#!/usr/bin/env python3
"""
release.py — Stamp a versioned save atomically.

Mechanizes the manual save flow:

  1. Compute current state (paired count, EPUB-to-be size, …) via verify.py.
  2. Bump the HANDOFF "Last updated" + "Status" lines.
  3. Insert a row into the compact ledger and a stub into the detailed appendix.
  4. Run audit + epubcheck (advisory; doesn't block release if they fail).
  5. Build the EPUB into the repo root with the canonical naming.
  6. Print the path of the new EPUB.

Dry-run by default; ``--apply`` performs the writes/build. The generated
appendix stub is intended as a starting point — flesh it out by hand
afterwards.

Examples:
    python3 scripts/release.py --version v26 --summary "Backlog tooling complete"
        # dry-run: print the planned ledger row + appendix stub

    python3 scripts/release.py --version v26 --summary "..." --apply
        # do it for real

    python3 scripts/release.py --version v26 --summary "..." --apply --no-epubcheck
        # skip the epubcheck step (e.g., JAR not installed)

    python3 scripts/release.py --version v26 --summary "..." --apply --no-build
        # update HANDOFF only, don't build the EPUB

Exit codes:
    0  success (or dry-run completed)
    1  audit reported errors (release proceeds; warning printed)
    2  setup error (couldn't parse HANDOFF, build failed, …)
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HANDOFF_PATH = REPO_ROOT / "HANDOFF_README_v7.md"
SCRIPTS = REPO_ROOT / "scripts"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ----------------------------------------------------------------------
# Probe current state
# ----------------------------------------------------------------------


def run_verify() -> tuple[int, int, int, int]:
    """Return (errors, warnings, info, paired). Paired is 0 if not parsed."""
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "verify.py"), "--quiet"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    out = (r.stdout or "") + (r.stderr or "")
    plain = re.sub(r"\x1b\[[0-9;]*m", "", out)
    m = re.search(r"errors=(\d+)\s+warnings=(\d+)\s+info=(\d+)\s+(\d+)/", plain)
    if not m:
        return (0, 0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))


def run_epubcheck(epub_path: Path) -> tuple[int, int] | None:
    """Return (errors, warnings) or None if epubcheck unavailable."""
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "epubcheck.py"), str(epub_path), "--quiet"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    out = (r.stdout or "") + (r.stderr or "")
    plain = re.sub(r"\x1b\[[0-9;]*m", "", out)
    m = re.search(r"errors=(\d+)\s+warnings=(\d+)", plain)
    if not m:
        return None
    if "skipped" in plain:
        return None
    return (int(m.group(1)), int(m.group(2)))


def parse_last_paired_from_ledger(handoff_text: str) -> tuple[str | None, int]:
    """Return (last_version_str, last_paired_count) from the compact ledger."""
    lines = handoff_text.splitlines()
    in_ledger = False
    for ln in lines:
        if "Compact ledger" in ln:
            in_ledger = True
            continue
        if not in_ledger:
            continue
        # Stop at the next h3 (### Detailed appendix)
        if ln.startswith("###"):
            break
        m = re.match(
            r"^\|\s*(v\d+)\s*\|\s*[^|]+\|\s*[^|]+\|\s*[+-]?\d+\s*\|\s*(\d+)",
            ln,
        )
        if m:
            return (m.group(1), int(m.group(2)))
    return (None, 0)


def count_source_notes() -> int:
    """Walk content/notes/*.py and count total tuples (AST, no exec)."""
    import ast as _ast

    total = 0
    notes_dir = REPO_ROOT / "content" / "notes"
    for f in sorted(notes_dir.glob("*.py")):
        if f.name == "__init__.py":
            continue
        try:
            tree = _ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, _ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, _ast.Name) and tgt.id == "NOTES":
                        try:
                            value = _ast.literal_eval(node.value)
                            if isinstance(value, list):
                                total += len(value)
                        except (ValueError, SyntaxError):
                            pass
    return total


# ----------------------------------------------------------------------
# HANDOFF rewriting
# ----------------------------------------------------------------------


def render_status_line(paired: int, errors: int, epubcheck_errors: int | None, epub_size_mb: float) -> str:
    parts = [f"{paired}/{paired} paired refs", f"{errors} audit errors"]
    if epubcheck_errors is not None:
        parts.append(f"{epubcheck_errors} epubcheck errors")
    parts.append(f"{epub_size_mb:.2f} MB EPUB")
    return " · ".join(parts)


def render_ledger_row(version: str, date: str, summary: str, delta: int, paired: int, epub_mb: float) -> str:
    delta_str = f"+{delta}" if delta > 0 else str(delta)
    return f"| {version} | {date} | {summary} | {delta_str} | {paired} | {epub_mb:.2f} MB |"


def render_appendix_stub(
    version: str, date: str, summary: str, paired: int, epubcheck_errors: int | None, epub_mb: float
) -> str:
    epubcheck_line = f"`epubcheck`: {epubcheck_errors} errors  " if epubcheck_errors is not None else ""
    return (
        f"\n#### {version} — {summary} ({date})\n"
        "\n"
        "_Stub — flesh out by hand. Suggested headings: Tools / Fixes / "
        "Content amplifications / State._\n"
        "\n"
        f"**State:** {paired}/{paired} paired · {epubcheck_line}{epub_mb:.2f} MB EPUB.\n"
    )


def insert_ledger_row(handoff_text: str, new_row: str) -> str:
    """Insert ``new_row`` directly under the compact-ledger header row."""
    pattern = re.compile(
        r"(\| Save \| Date \| Batch \| Δ notes \| Total paired \| EPUB \|\n"
        r"\|---\|---\|---\|---\|---\|---\|\n)",
        re.MULTILINE,
    )
    new_text, n = pattern.subn(lambda m: m.group(1) + new_row + "\n", handoff_text, count=1)
    if n != 1:
        raise ValueError("could not locate compact-ledger header row")
    return new_text


def insert_appendix_stub(handoff_text: str, stub: str) -> str:
    """Insert ``stub`` directly under the appendix header."""
    pattern = re.compile(
        r"(### Detailed appendix \(chronological — newest at top\)\n)",
        re.MULTILINE,
    )
    new_text, n = pattern.subn(lambda m: m.group(1) + stub, handoff_text, count=1)
    if n != 1:
        raise ValueError("could not locate detailed-appendix header")
    return new_text


def update_status_block(handoff_text: str, version: str, date: str, summary: str, status: str) -> str:
    """Rewrite the top 'Last updated:' and 'Status:' lines."""
    new_text = re.sub(
        r"^\*\*Last updated:\*\*[^\n]*",
        f"**Last updated:** {version} save · {date} ({summary}).",
        handoff_text,
        count=1,
        flags=re.MULTILINE,
    )
    new_text = re.sub(
        r"^\*\*Status:\*\*[^\n]*",
        f"**Status:** {status}.",
        new_text,
        count=1,
        flags=re.MULTILINE,
    )
    return new_text


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Stamp a versioned save atomically.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", required=True, help="version label, e.g. v26")
    p.add_argument("--summary", required=True, help="one-line description for the ledger")
    p.add_argument("--apply", action="store_true", help="actually write changes (default is dry-run)")
    p.add_argument("--no-build", action="store_true", help="skip the EPUB build step")
    p.add_argument("--no-epubcheck", action="store_true", help="skip the epubcheck step")
    args = p.parse_args()

    if not re.match(r"^v\d+$", args.version):
        print(f"{RED}ERROR: --version must look like 'v26'{RESET}", file=sys.stderr)
        sys.exit(2)

    if not HANDOFF_PATH.is_file():
        print(f"{RED}ERROR: HANDOFF not found at {HANDOFF_PATH}{RESET}", file=sys.stderr)
        sys.exit(2)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")

    # ---- Probe state
    print(f"  {DIM}probing project state …{RESET}")
    errors, warns, info, paired = run_verify()
    if paired == 0:
        print(f"{YELLOW}WARNING: could not parse paired count from verify.py{RESET}", file=sys.stderr)

    handoff_text = HANDOFF_PATH.read_text(encoding="utf-8")
    last_version, last_paired = parse_last_paired_from_ledger(handoff_text)
    delta_paired = paired - last_paired

    n_source = count_source_notes()

    # ---- EPUB build (compute name; do work only on --apply)
    epub_path = REPO_ROOT / f"Ethiopian_Bible_{args.version}_{timestamp}.epub"
    epub_size_mb = 0.0
    epubcheck_errors: int | None = None

    if args.apply and not args.no_build:
        print(f"  {DIM}building EPUB → {epub_path.name} …{RESET}")
        r = subprocess.run(
            [sys.executable, str(SCRIPTS / "build_epub.py"), str(epub_path)],
            cwd=str(REPO_ROOT),
        )
        if r.returncode != 0:
            print(f"{RED}ERROR: build_epub.py failed (rc={r.returncode}){RESET}", file=sys.stderr)
            sys.exit(2)
        epub_size_mb = epub_path.stat().st_size / (1024 * 1024)

        if not args.no_epubcheck:
            print(f"  {DIM}running epubcheck …{RESET}")
            res = run_epubcheck(epub_path)
            if res is not None:
                epubcheck_errors = res[0]
            else:
                print(f"  {DIM}(epubcheck unavailable — skipped){RESET}")
    else:
        # Dry-run estimate from previously-built EPUBs
        existing = sorted(REPO_ROOT.glob("Ethiopian_Bible_*.epub"), key=lambda p: p.stat().st_mtime, reverse=True)
        if existing:
            epub_size_mb = existing[0].stat().st_size / (1024 * 1024)

    # ---- Compose new HANDOFF text
    status = render_status_line(paired, errors, epubcheck_errors, epub_size_mb)
    ledger_row = render_ledger_row(args.version, today, args.summary, delta_paired, paired, epub_size_mb)
    appendix_stub = render_appendix_stub(args.version, today, args.summary, paired, epubcheck_errors, epub_size_mb)

    try:
        new_text = update_status_block(handoff_text, args.version, today, args.summary, status)
        new_text = insert_ledger_row(new_text, ledger_row)
        new_text = insert_appendix_stub(new_text, appendix_stub)
    except ValueError as e:
        print(f"{RED}ERROR: HANDOFF rewrite failed: {e}{RESET}", file=sys.stderr)
        sys.exit(2)

    # ---- Output
    print(f"\n  {BOLD}{args.version} · {today}{RESET}")
    print(f"  {DIM}previous save: {last_version} (paired={last_paired}){RESET}\n")
    print("  ledger row:")
    print(f"    {GREEN}{ledger_row}{RESET}\n")
    print("  status line:")
    print(f"    {DIM}{status}{RESET}\n")
    print(f"  source notes: {n_source:,}    Δ paired: {delta_paired:+d}")

    if args.apply:
        HANDOFF_PATH.write_text(new_text, encoding="utf-8")
        print(f"\n  {GREEN}✓ wrote {HANDOFF_PATH.name}{RESET}")
        if not args.no_build:
            print(f"  {GREEN}✓ built {epub_path.name} ({epub_size_mb:.2f} MB){RESET}")
        print(f"\n  {DIM}flesh out the appendix stub by hand, then save the zip.{RESET}")
    else:
        print(f"\n  {YELLOW}⚠ dry-run — re-run with --apply to write changes{RESET}")

    if errors > 0:
        print(f"\n  {YELLOW}note: verify.py reported {errors} audit errors{RESET}")
    if epubcheck_errors:
        print(f"  {YELLOW}note: epubcheck reported {epubcheck_errors} errors{RESET}")

    sys.exit(0 if errors == 0 else 1)


if __name__ == "__main__":
    main()

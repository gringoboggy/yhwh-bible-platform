#!/usr/bin/env python3
"""
check_xrefs.py — Verify every internal href in the EPUB resolves to a real id.

``link_xrefs.py`` *creates* cross-reference links inside note bodies. Once
amplification is mature there are hundreds (Genesis alone will easily reach
200+ NT-quotes-OT, parallel-passage, and ANE-comparison links). Currently
nothing catches a typo in the target id — a broken ``href="#v-jhn-1-1"``
silently does nothing and no test fails.

This script is the inverse of ``link_xrefs.py``: it scans every internal
``href`` in ``epub_working/*.html`` and confirms each target id (or target
file) actually exists. Pure Python, no external dependencies.

Three failure modes are reported:

  * **broken-id**     ``href="...#X"`` — the file is fine, but ``id="X"`` does not exist.
  * **broken-file**   ``href="file.html..."`` — the referenced file is not in the EPUB at all.
  * **broken-empty**  ``href=""`` or ``href="#"`` — no target.

External hrefs (``http://``, ``mailto:``, ``data:``, ``javascript:``, ...) are skipped.

Examples:
    python3 scripts/check_xrefs.py
        # check every internal href; default mode

    python3 scripts/check_xrefs.py --asides-only
        # roadmap's strict scope: only links inside <aside> blocks
        # (commentary notes + verse popovers)

    python3 scripts/check_xrefs.py --verbose
        # show all broken links instead of just the first 20

    python3 scripts/check_xrefs.py --quiet
        # only print the summary line (suitable for CI)

Exit codes:
    0  no broken links
    1  broken links found
    2  setup error (epub_working/ missing or empty)
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EPUB_DIR = REPO_ROOT / "epub_working"

ID_RE = re.compile(r'\bid="([^"]+)"')
HREF_RE = re.compile(r'\bhref="([^"]*)"')

# Same aside pattern as link_xrefs.py — keeps the two scripts in lockstep.
ASIDE_PAT = re.compile(
    r'<aside class="(?:note (?:note-comm|note-word|note-source|note-variant)'
    r'|vnote)[^"]*"[^>]*>'
    r"(?:.*?)"
    r"</aside>",
    re.DOTALL,
)

EXTERNAL_PREFIXES = (
    "http://",
    "https://",
    "mailto:",
    "ftp://",
    "data:",
    "tel:",
    "javascript:",
)

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


# ----------------------------------------------------------------------
# Indexing
# ----------------------------------------------------------------------


def build_id_index(files: list[Path]) -> dict[str, set[str]]:
    """{filename: set(ids)} for each HTML file."""
    return {f.name: set(ID_RE.findall(f.read_text(encoding="utf-8"))) for f in files}


def line_starts(text: str) -> list[int]:
    """Return cumulative byte-offsets for the start of each line."""
    starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            starts.append(i + 1)
    return starts


def line_of(starts: list[int], pos: int) -> int:
    """1-indexed line number for a character position."""
    # Binary search would be faster, but linear is fast enough at our scale.
    lo, hi = 0, len(starts) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if starts[mid] <= pos:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1


# ----------------------------------------------------------------------
# Href collection
# ----------------------------------------------------------------------


def is_external(href: str) -> bool:
    return href.startswith(EXTERNAL_PREFIXES)


def collect_hrefs(text: str, asides_only: bool):
    """Yield (pos, href, context_snippet) for each href in scope."""
    if asides_only:
        for m in ASIDE_PAT.finditer(text):
            block = m.group(0)
            block_start = m.start()
            for hm in HREF_RE.finditer(block):
                pos = block_start + hm.start()
                href = hm.group(1)
                # Link text: <a href="…">TEXT</a>
                tail = block[hm.end() : hm.end() + 200]
                ctx_m = re.match(r"[^>]*>([^<]{0,80})</a>", tail)
                ctx = ctx_m.group(1).strip() if ctx_m else ""
                yield (pos, href, ctx)
    else:
        for hm in HREF_RE.finditer(text):
            pos = hm.start()
            href = hm.group(1)
            tail = text[hm.end() : hm.end() + 200]
            ctx_m = re.match(r"[^>]*>([^<]{0,80})</a>", tail)
            ctx = ctx_m.group(1).strip() if ctx_m else ""
            yield (pos, href, ctx)


# ----------------------------------------------------------------------
# Resolution
# ----------------------------------------------------------------------


def resolve(
    href: str,
    source_file: str,
    id_index: dict[str, set[str]],
    file_set: set[str],
) -> tuple[str, str]:
    """Return (status, detail). status ∈ {ok, skip, broken_id, broken_file, broken_empty}."""
    if not href:
        return ("broken_empty", "empty href")
    if href == "#":
        return ("broken_empty", "bare '#'")
    if is_external(href):
        return ("skip", "external")

    # Same-file fragment
    if href.startswith("#"):
        target_id = href[1:]
        if target_id in id_index.get(source_file, set()):
            return ("ok", f"{source_file}#{target_id}")
        return ("broken_id", f"#{target_id}")

    # Cross-file (with or without fragment)
    if "#" in href:
        file_part, id_part = href.split("#", 1)
    else:
        file_part, id_part = href, None

    # Normalize: strip leading "./" if any
    if file_part.startswith("./"):
        file_part = file_part[2:]

    if file_part not in file_set:
        return ("broken_file", f"{file_part}")

    if id_part is None or id_part == "":
        return ("ok", file_part)

    if id_part in id_index.get(file_part, set()):
        return ("ok", f"{file_part}#{id_part}")
    return ("broken_id", f"{file_part}#{id_part}")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Verify every internal href in the EPUB resolves to a real target.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--asides-only",
        action="store_true",
        help="restrict to hrefs inside <aside> blocks (the roadmap's strict scope)",
    )
    p.add_argument(
        "--epub-dir",
        type=Path,
        default=EPUB_DIR,
        help="directory of unpacked EPUB (default: epub_working/)",
    )
    p.add_argument("--quiet", action="store_true", help="only print the summary line")
    p.add_argument(
        "--verbose",
        action="store_true",
        help="show all broken refs (default: cap at --max-show)",
    )
    p.add_argument(
        "--max-show",
        type=int,
        default=20,
        help="how many broken refs to display in non-verbose mode (default 20)",
    )
    args = p.parse_args()

    if not args.epub_dir.is_dir():
        print(f"{RED}ERROR: not a directory: {args.epub_dir}{RESET}", file=sys.stderr)
        sys.exit(2)

    files = sorted(args.epub_dir.glob("*.html")) + sorted(args.epub_dir.glob("*.xhtml"))
    if not files:
        print(f"{RED}ERROR: no HTML files in {args.epub_dir}{RESET}", file=sys.stderr)
        sys.exit(2)

    if not args.quiet:
        scope = "asides only" if args.asides_only else "all internal"
        print(f"scanning {len(files)} files for {scope} hrefs …")

    # Build indexes. We extract ids only from (X)HTML, but the file_set must
    # include every shipped file (CSS, fonts, images, etc.) so that
    # ``href="stylesheet.css"`` resolves rather than being flagged as missing.
    id_index = build_id_index(files)
    file_set: set[str] = set()
    for path in args.epub_dir.rglob("*"):
        if path.is_file():
            rel = path.relative_to(args.epub_dir).as_posix()
            file_set.add(rel)
            # Also register the basename for files in subdirs, since hrefs
            # are written relative to the referencing file's directory and
            # most refs in this EPUB live in the root.
            file_set.add(path.name)

    # Scan
    total = 0
    skipped = 0
    ok = 0
    broken = []  # (source_file, line_no, href, context, reason)
    by_reason: Counter[str] = Counter()

    for f in files:
        text = f.read_text(encoding="utf-8")
        starts = line_starts(text)
        for pos, href, ctx in collect_hrefs(text, asides_only=args.asides_only):
            total += 1
            status, _detail = resolve(href, f.name, id_index, file_set)
            if status == "skip":
                skipped += 1
            elif status == "ok":
                ok += 1
            else:
                broken.append((f.name, line_of(starts, pos), href, ctx, status))
                by_reason[status] += 1

    # Output broken refs
    if broken and not args.quiet:
        limit = None if args.verbose else args.max_show
        shown = broken if limit is None else broken[:limit]
        for src, ln, href, ctx, reason in shown:
            ctx_str = f"  ⟶ {ctx[:60]!r}" if ctx else ""
            label = reason.replace("_", "-")
            print(f"  {RED}{src}:{ln}: {label}: {href}{RESET}{ctx_str}")
        if limit is not None and len(broken) > limit:
            print(f"  … {len(broken) - limit} more (re-run with --verbose)")

    # Summary
    bad = bool(broken)
    color = RED if bad else GREEN
    sym = "✗" if bad else "✓"
    scope_label = "asides" if args.asides_only else "all"
    print(
        f"\n{color}{sym} check_xrefs ({scope_label}): "
        f"refs={total}  ok={ok}  broken={len(broken)}  skipped={skipped}{RESET}"
    )
    if broken:
        # Per-reason breakdown
        parts = []
        for reason in ("broken_id", "broken_file", "broken_empty"):
            if by_reason[reason]:
                parts.append(f"{reason.replace('_', '-')}: {by_reason[reason]}")
        if parts:
            print("  " + "  ".join(parts))
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()

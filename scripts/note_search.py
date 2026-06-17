#!/usr/bin/env python3
"""
note_search.py — Tuple-aware search across every note in ``content/notes/``.

Like ``grep``, but understands the note tuple shape: search by body text,
anchor substring, title, kind, or book/chapter range, and combine filters
freely (all conditions are AND-ed).

Notes are loaded via ``ast.literal_eval`` — no code execution.

Examples:
    python3 scripts/note_search.py --body "Augustine"
    python3 scripts/note_search.py --anchor "image of God"
    python3 scripts/note_search.py --kind parallel
    python3 scripts/note_search.py --book gen --ch 1-11
    python3 scripts/note_search.py --body "deconstruction" --book gen
    python3 scripts/note_search.py --regex --body "[Bb]ereshit"
    python3 scripts/note_search.py --title "Hebrew" --kind word
    python3 scripts/note_search.py --count               # only print summary

Filters
-------

  --book CODE          one book (e.g. gen, 1en)
  --ch N or N-M        chapter, or range
  --kind CODE          one kind (word / comm / source / parallel / …)
  --body TEXT          substring in body_html (or regex with --regex)
  --anchor TEXT        substring in anchor (or regex with --regex)
  --title TEXT         substring in title (or regex with --regex)
  --regex              treat --body / --anchor / --title as regex (case-sens)
  --case-sensitive     by default, text searches are case-insensitive

Exit codes:
    0  matches found (or --count printed)
    1  no matches
    2  setup error (bad book code, malformed range, …)
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402
from scripts.core.notes_io import load_notes_from_text
from scripts.core.html_utils import strip_tags

NOTES_DIR = REPO_ROOT / "content" / "notes"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ----------------------------------------------------------------------
# Note loading
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# Filters
# ----------------------------------------------------------------------


def parse_chapter_range(spec: str) -> tuple[int, int]:
    """Accept '5' or '5-10'."""
    if "-" in spec:
        lo, hi = spec.split("-", 1)
        return (int(lo), int(hi))
    n = int(spec)
    return (n, n)


def make_text_matcher(pattern: str | None, regex: bool, case_sensitive: bool):
    """Return a callable str→bool, or None if pattern is None."""
    if pattern is None:
        return None
    if regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        rx = re.compile(pattern, flags)
        return lambda s: bool(rx.search(s or ""))
    needle = pattern if case_sensitive else pattern.lower()
    if case_sensitive:
        return lambda s: needle in (s or "")
    return lambda s: needle in (s or "").lower()


# ----------------------------------------------------------------------
# Highlighting
# ----------------------------------------------------------------------


def highlight(text: str, pattern: str | None, regex: bool, case_sensitive: bool) -> str:
    """Insert ANSI yellow background around pattern matches in text."""
    if not pattern:
        return text
    if regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            rx = re.compile(pattern, flags)
        except re.error:
            return text
    else:
        flags = 0 if case_sensitive else re.IGNORECASE
        rx = re.compile(re.escape(pattern), flags)
    return rx.sub(lambda m: f"\033[1;43;30m{m.group(0)}\033[0m", text)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Tuple-aware search across content/notes/.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--book", help="book code (e.g. gen)")
    p.add_argument("--ch", help="chapter or range (e.g. 5 or 1-11)")
    p.add_argument("--v", type=int, help="verse number")
    p.add_argument("--kind", help="kind code (word / comm / source / parallel / …)")
    p.add_argument("--body", help="body_html substring (or regex with --regex)")
    p.add_argument("--anchor", help="anchor substring (or regex with --regex)")
    p.add_argument("--title", help="title substring (or regex with --regex)")
    p.add_argument("--regex", action="store_true", help="treat text patterns as regex")
    p.add_argument("--case-sensitive", action="store_true", help="case-sensitive text matching")
    p.add_argument("--count", action="store_true", help="only print the count, no per-note output")
    p.add_argument(
        "--max-show",
        type=int,
        default=50,
        help="cap on results displayed (default 50; use 0 for no cap)",
    )
    p.add_argument(
        "--snippet",
        type=int,
        default=120,
        help="characters of plain-text body to show per result (default 120; 0 to suppress)",
    )
    args = p.parse_args()

    if args.book:
        args.book = config.resolve_book_code(args.book)

    # Validate book
    books_map = config.books_by_code()
    if args.book and args.book not in books_map:
        print(f"{RED}ERROR: unknown book code {args.book!r}{RESET}", file=sys.stderr)
        sys.exit(2)

    # Validate kind
    kinds_map = config.kinds_by_code()
    if args.kind and args.kind not in kinds_map:
        print(
            f"{RED}ERROR: unknown kind {args.kind!r}. Known: {sorted(kinds_map)}{RESET}",
            file=sys.stderr,
        )
        sys.exit(2)

    # Parse chapter range
    ch_lo = ch_hi = None
    if args.ch:
        try:
            ch_lo, ch_hi = parse_chapter_range(args.ch)
        except ValueError:
            print(f"{RED}ERROR: bad --ch spec {args.ch!r}; use N or N-M{RESET}", file=sys.stderr)
            sys.exit(2)

    # Build matchers
    body_match = make_text_matcher(args.body, args.regex, args.case_sensitive)
    anchor_match = make_text_matcher(args.anchor, args.regex, args.case_sensitive)
    title_match = make_text_matcher(args.title, args.regex, args.case_sensitive)

    # Iterate
    book_codes = [args.book] if args.book else [b["code"] for b in config.load_books()]
    matches = []  # (book, ch, v, suffix, anchor, kind, title, body)

    for code in book_codes:
        path = NOTES_DIR / f"{code}.py"
        if not path.is_file():
            continue
        notes = load_notes_from_text(path.read_text(encoding="utf-8"))
        if not notes:
            continue
        for tup in notes:
            if not isinstance(tup, tuple) or len(tup) < 8:
                continue
            ch, v, suffix, anchor, kind, title, _label, body = tup[:8]

            if ch_lo is not None and not (ch_lo <= ch <= ch_hi):
                continue
            if args.v is not None and v != args.v:
                continue
            if args.kind and kind != args.kind:
                continue
            if body_match and not body_match(body):
                continue
            if anchor_match and not anchor_match(anchor):
                continue
            if title_match and not title_match(title):
                continue

            matches.append((code, ch, v, suffix, anchor, kind, title, body))

    # Output
    if not matches:
        print(f"{DIM}no matches{RESET}")
        sys.exit(1)

    if args.count:
        print(f"{GREEN}{len(matches)}{RESET} match{'es' if len(matches) != 1 else ''}")
        sys.exit(0)

    limit = None if args.max_show == 0 else args.max_show
    shown = matches if limit is None else matches[:limit]

    for code, ch, v, suffix, anchor, kind, title, body in shown:
        loc = f"{BOLD}{code} {ch}:{v}{suffix or ''}{RESET}"
        kind_str = f"{DIM}[{kind}]{RESET}"
        anchor_str = repr(anchor) if anchor else f"{DIM}(start){RESET}"
        title_str = repr(title)
        # Highlight matches in the displayed body snippet (plain text)
        snippet_text = strip_tags(body)
        if args.snippet > 0 and len(snippet_text) > args.snippet:
            snippet_text = snippet_text[: args.snippet].rstrip() + "…"
        snippet_text = highlight(snippet_text, args.body, args.regex, args.case_sensitive)
        anchor_str = highlight(anchor_str, args.anchor, args.regex, args.case_sensitive)
        title_str = highlight(title_str, args.title, args.regex, args.case_sensitive)

        print(f"  {loc} {kind_str}  anchor={anchor_str}  title={title_str}")
        if args.snippet > 0:
            print(f"    {DIM}⟶{RESET} {snippet_text}")

    if limit is not None and len(matches) > limit:
        print(f"\n  {DIM}… {len(matches) - limit} more (use --max-show 0 for all){RESET}")

    print(f"\n{GREEN}{len(matches)}{RESET} match{'es' if len(matches) != 1 else ''}")
    sys.exit(0)


if __name__ == "__main__":
    main()

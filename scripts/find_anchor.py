#!/usr/bin/env python3
"""
find_anchor.py — Propose anchor candidates for a verse.

When adding a note via ``scripts/add_note.py``, the ``--anchor`` argument must be an
exact substring of the WEB-English verse text **and** must not collide with anchors
already used by other notes on the same verse. Hitting an anchor collision is the
most common round-trip in a batch session — this tool eliminates it by listing all
viable candidate substrings up front, with status against existing notes.

Usage:
    python3 scripts/find_anchor.py gen 1 26
        # show free 2–5-word substrings for Genesis 1:26

    python3 scripts/find_anchor.py gen 1 26 --all
        # also show taken / overlapping candidates with the colliding existing note

    python3 scripts/find_anchor.py gen 1 26 --max-words 7
        # widen the window

    python3 scripts/find_anchor.py 1en 6 1 --min-words 1
        # include single words

Exit codes:
    0  ok
    2  unknown book / verse not found in EPUB
"""

import argparse
import ast
import re
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402

EPUB_DIR = REPO_ROOT / "epub_working"
NOTES_DIR = REPO_ROOT / "content" / "notes"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
RESET = "\033[0m"


# ----------------------------------------------------------------------
# Verse text extraction
# ----------------------------------------------------------------------


VERSE_ANCHOR_RE = re.compile(r'<a[^>]*\bid="v-[a-z0-9]+-\d+-\d+[a-z]?"', re.IGNORECASE)
NOTEREF_RE = re.compile(r'<a class="note-ref[^"]*"[^>]*>.*?</a>', re.DOTALL)


def find_verse_text(epub_dir: Path, code: str, ch: int, v: int):
    """Return (plain_text, source_filename) or (None, None) if not found."""
    target_id = f"v-{code}-{ch}-{v}"
    target_pat = re.compile(
        rf'<a[^>]*\bid="{re.escape(target_id)}"[^>]*>.*?</a>',
        re.DOTALL,
    )
    for f in sorted(epub_dir.glob("*.html")):
        text = f.read_text(encoding="utf-8")
        m = target_pat.search(text)
        if not m:
            continue
        start = m.end()
        # Find next verse anchor (any verse, not just CH:V+1 — handles Strategy A
        # files where verses can cross paragraph boundaries).
        nxt = VERSE_ANCHOR_RE.search(text, start)
        end = nxt.start() if nxt else min(len(text), start + 4000)
        verse_html = text[start:end]
        # Strip injected note-refs (these aren't part of the verse text).
        cleaned = NOTEREF_RE.sub("", verse_html)
        # Strip remaining markup.
        plain = re.sub(r"<[^>]+>", "", cleaned)
        plain = re.sub(r"\s+", " ", plain).strip()
        return plain, f.name
    return None, None


# ----------------------------------------------------------------------
# Existing-note anchor lookup (AST, no exec)
# ----------------------------------------------------------------------


def load_existing_anchors(notes_path: Path, ch: int, v: int):
    """Return [(suffix, anchor, kind, title), …] for notes on this verse."""
    if not notes_path.is_file():
        return []
    try:
        tree = ast.parse(notes_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    notes = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "NOTES":
                    try:
                        notes = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return []
                    break
    out = []
    for tup in notes:
        if isinstance(tup, tuple) and len(tup) >= 8:
            tch, tv, tsuffix, tanchor, tkind, ttitle = tup[:6]
            if tch == ch and tv == v:
                out.append((tsuffix, tanchor, tkind, ttitle))
    return out


# ----------------------------------------------------------------------
# Candidate generation + classification
# ----------------------------------------------------------------------


def generate_candidates(verse_text: str, min_words: int, max_words: int):
    """Yield (n_words, start_word_index, substring) — distinct sliding windows."""
    words = verse_text.split()
    seen: set[str] = set()
    for length in range(min_words, max_words + 1):
        for start in range(len(words) - length + 1):
            sub = " ".join(words[start : start + length])
            if sub not in seen:
                seen.add(sub)
                yield (length, start, sub)


def classify(candidate: str, existing):
    """Return (status, detail). status ∈ {free, taken, overlap}."""
    for suffix, anchor, kind, _title in existing:
        if not anchor:
            continue
        if candidate == anchor:
            tag = f"{suffix or '—'} [{kind}]"
            return ("taken", f"used by {tag}")
        # Substring overlap either direction = ambiguous if injector matches by find()
        if anchor in candidate or candidate in anchor:
            tag = f"{suffix or '—'} [{kind}]"
            return ("overlap", f"overlaps anchor {anchor!r} ({tag})")
    return ("free", "")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Propose anchor candidates for a verse.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("book", help="book code (e.g. gen, exo, 1en)")
    p.add_argument("ch", type=int, help="chapter number")
    p.add_argument("v", type=int, help="verse number")
    p.add_argument("--min-words", type=int, default=2, help="min candidate length (default 2)")
    p.add_argument("--max-words", type=int, default=5, help="max candidate length (default 5)")
    p.add_argument("--all", action="store_true", help="also show taken / overlapping candidates")
    p.add_argument("--quiet", action="store_true", help="only print candidates, no preamble")
    args = p.parse_args()

    try:
        book = config.get_book(args.book)
    except KeyError as e:
        print(f"{RED}ERROR: {e}{RESET}", file=sys.stderr)
        sys.exit(2)

    if not (1 <= args.ch <= book["ch_count"]):
        print(
            f"{RED}ERROR: chapter {args.ch} out of range for {args.book} (1–{book['ch_count']}){RESET}",
            file=sys.stderr,
        )
        sys.exit(2)

    verse_text, filename = find_verse_text(EPUB_DIR, args.book, args.ch, args.v)
    if not verse_text:
        print(
            f"{RED}ERROR: verse {args.book} {args.ch}:{args.v} not found in EPUB{RESET}",
            file=sys.stderr,
        )
        sys.exit(2)

    existing = load_existing_anchors(NOTES_DIR / f"{args.book}.py", args.ch, args.v)

    # --- Header
    if not args.quiet:
        print(f"\n  {book['title']}")
        print(f"  {DIM}{args.book.upper()} {args.ch}:{args.v} · {filename}{RESET}\n")
        print(f"  Verse text:")
        for line in textwrap.wrap(verse_text, width=72, initial_indent="    ", subsequent_indent="    "):
            print(line)
        print()

        if existing:
            print(f"  {DIM}Existing notes on this verse ({len(existing)}):{RESET}")
            for suffix, anchor, kind, title in existing:
                anchor_str = repr(anchor) if anchor else "(empty: start of verse)"
                tag = (suffix or "—").ljust(2)
                print(f"    {DIM}{tag} [{kind}]{RESET}  anchor={anchor_str}  title={title!r}")
            print()
        else:
            print(f"  {DIM}No existing notes on this verse.{RESET}\n")

    # --- Generate + classify
    free, taken, overlap = [], [], []
    for length, _start, cand in generate_candidates(verse_text, args.min_words, args.max_words):
        status, detail = classify(cand, existing)
        item = (length, cand, detail)
        if status == "free":
            free.append(item)
        elif status == "taken":
            taken.append(item)
        else:
            overlap.append(item)

    # --- Output
    if free:
        print(f"  {GREEN}Free candidates ({len(free)}):{RESET}")
        for length, cand, _ in free:
            print(f"    [{length}] {cand!r}")
    else:
        print(f"  {YELLOW}No free candidates in {args.min_words}–{args.max_words} word range.{RESET}")
        print(
            f"  Try --min-words 1 or --max-words {args.max_words + 3}, "
            f"or use --suffix on add_note.py to add another note at an existing anchor."
        )

    if args.all:
        if taken:
            print(f"\n  {RED}Already taken ({len(taken)}):{RESET}")
            for length, cand, detail in taken:
                print(f"    [{length}] {cand!r}  — {detail}")
        if overlap:
            print(f"\n  {YELLOW}Overlapping with existing anchors ({len(overlap)}):{RESET}")
            for length, cand, detail in overlap:
                print(f"    [{length}] {cand!r}  — {detail}")

    print()


if __name__ == "__main__":
    main()

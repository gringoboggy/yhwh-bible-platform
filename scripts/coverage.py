#!/usr/bin/env python3
"""
coverage.py — track which books are fully amplified.

For each book in content/books.yaml, this script reports:
  - total chapters
  - chapters with ≥2 notes (heavy-pass standard)
  - chapters with exactly 1 note ("thin")
  - chapters with 0 notes ("empty")
  - total notes
  - injected count from epub_working/ HTML (paired refs in body)
  - status: ✅ complete / 🟡 in-progress / ⚪ untouched

A book is "complete" when every chapter has ≥2 notes AND the injected count
matches the notes count (i.e., all notes are live in the EPUB).

Examples:
  python3 scripts/coverage.py                    # full project dashboard
  python3 scripts/coverage.py --book 1en         # one book, per-chapter
  python3 scripts/coverage.py --thin             # only show in-progress books
  python3 scripts/coverage.py --json             # machine-readable
  python3 scripts/coverage.py --priority         # ordered by README §5.2 priority
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config
from content.notes import load_notes

EPUB_DIR = REPO_ROOT / "epub_working"

# Priority order from HANDOFF_README §5.2
PRIORITY_ORDER = [
    # Already amplified (heavy-pass)
    "gen",
    "exo",
    "lev",
    "num",
    "deu",
    "jos",
    "jdg",
    "rut",
    "1sa",
    "2sa",
    "1ki",
    "2ki",
    "1en",
    # Priority list
    "1ch",
    "2ch",
    "isa",
    "jer",
    "eze",
    "dan",
    "sus",
    "paz",
    "bel",
    "hos",
    "joe",
    "amo",
    "oba",
    "jon",
    "mic",
    "nah",
    "hab",
    "zep",
    "hag",
    "zec",
    "mal",
    "job",
    "ecc",
    "sng",
    "psa",
    "jub",
    "mq1",
    "mq2",
    "mq3",
    "4ba",
    "1es",
    # NT
    "mat",
    "mrk",
    "luk",
    "jhn",
    "act",
    "rom",
    "1co",
    "2co",
    "gal",
    "eph",
    "phi",
    "col",
    "1th",
    "2th",
    "1ti",
    "2ti",
    "tit",
    "phm",
    "heb",
    "jam",
    "1pe",
    "2pe",
    "1jn",
    "2jn",
    "3jn",
    "jud",
    "rev",
    # Other deuterocanon / extras
    "2en",
    "tob",
    "jdt",
    "est",
    "aes",
    "ezr",
    "neh",
    "2es",
    "man",
    "bar",
    "lje",
    "lam",
    "pro",
    "sir",
    "wis",
    "1cl",
]


def _compile_injected_id_re(id_prefix: str) -> "re.Pattern[str]":
    """Compile the injected-aside id regex for a book's id-prefix.

    Chapter group is ``\\d+`` (not fixed-width) so chapters >=100 are counted,
    e.g. 1En 100-108: id "note-1e10001" -> ch=100, v=01. Trailing ``\\d{2}``
    still anchors exactly 2 verse digits. (Mirrors ``inject._aside_existing_re``;
    see findings H3/M13.) Exposed as a named helper so tests exercise the SAME
    pattern ``count_injected`` uses rather than a drift-prone copy."""
    return re.compile(rf'id="note-{re.escape(id_prefix)}(\d+)(\d{{2}})([a-z]?)"')


def count_injected(book):
    """Count `note-<idprefix>NNNN[suf]` ids in the book's HTML files.
    Returns (total_count, by_chapter_dict) so callers can analyze per-chapter."""
    files = book.get("files") or []
    if not files:
        return 0, {}
    code = book["code"]
    id_prefix = book.get("id_prefix") or code
    pat = _compile_injected_id_re(id_prefix)
    seen = set()
    by_chapter = Counter()
    for fname in files:
        path = EPUB_DIR / fname
        if not path.exists():
            continue
        for m in pat.finditer(path.read_text()):
            key = (m.group(1), m.group(2), m.group(3))
            if key in seen:
                continue
            seen.add(key)
            by_chapter[int(m.group(1))] += 1
    return len(seen), dict(by_chapter)


def book_stats(book):
    """Return a dict of stats for one book."""
    code = book["code"]
    ch_count = book.get("ch_count", 0)
    try:
        notes = load_notes(code)
    except Exception:
        notes = []
    notes_total = len(notes)

    # Notes per chapter from content/notes/
    by_chapter_pending = Counter(n[0] for n in notes)
    # Notes per chapter from HTML (the authoritative reality)
    injected_total, by_chapter_injected = count_injected(book)

    # Combined per-chapter coverage = max(pending, injected). Pending notes are
    # tuples not yet injected (so they count as "scheduled"); injected notes are
    # what the EPUB actually has right now.
    chapters_full = []
    chapters_thin = []
    chapters_empty = []
    if ch_count > 0:
        for c in range(1, ch_count + 1):
            n = max(by_chapter_pending.get(c, 0), by_chapter_injected.get(c, 0))
            if n >= 2:
                chapters_full.append(c)
            elif n == 1:
                chapters_thin.append(c)
            else:
                chapters_empty.append(c)

    # Status logic — judged on COMBINED coverage:
    if notes_total == 0 and injected_total == 0:
        status = "untouched"
    elif ch_count > 0 and len(chapters_full) == ch_count:
        status = "complete"
    else:
        status = "in_progress"

    return {
        "code": code,
        "title": book["title"],
        "bxx": book.get("bxx"),
        "ch_count": ch_count,
        "notes_total": notes_total,
        "injected": injected_total,
        "pending_inject": max(0, notes_total - injected_total),
        "chapters_full": chapters_full,
        "chapters_thin": chapters_thin,
        "chapters_empty": chapters_empty,
        "status": status,
        "strategy": book["strategy"],
    }


STATUS_GLYPH = {"complete": "✅", "in_progress": "🟡", "untouched": "⚪"}


def print_dashboard(rows, show_only=None, ordered=None):
    """Print a project-wide dashboard."""
    rows = list(rows)
    if show_only:
        rows = [r for r in rows if r["status"] in show_only]
    if ordered:
        order_index = {c: i for i, c in enumerate(ordered)}
        rows.sort(key=lambda r: order_index.get(r["code"], 999))

    # Header
    print(f"  {'':2}  {'CODE':6}  {'CH':>4}  {'NOTES':>5}  {'INJ':>4}  {'FULL':>4}  {'THIN':>4}  {'EMPTY':>5}  TITLE")
    print("  " + "─" * 90)
    counts = Counter()
    for r in rows:
        glyph = STATUS_GLYPH[r["status"]]
        n_full = len(r["chapters_full"])
        n_thin = len(r["chapters_thin"])
        n_empty = len(r["chapters_empty"])
        title_short = r["title"][:55]
        print(
            f"  {glyph:2}  {r['code']:6}  {r['ch_count']:>4}  "
            f"{r['notes_total']:>5}  {r['injected']:>4}  "
            f"{n_full:>4}  {n_thin:>4}  {n_empty:>5}  {title_short}"
        )
        counts[r["status"]] += 1

    print("  " + "─" * 90)
    total = sum(counts.values())
    print(
        f"  Totals: {counts['complete']} complete · {counts['in_progress']} in-progress · "
        f"{counts['untouched']} untouched ({total} books shown)"
    )


def print_book_detail(stats):
    """Per-chapter breakdown for one book."""
    print(f"\n  {STATUS_GLYPH[stats['status']]} {stats['code']}  ({stats['title']})")
    print(
        f"     bxx={stats['bxx']}  strategy={stats['strategy']}  "
        f"chapters={stats['ch_count']}  notes={stats['notes_total']}  injected={stats['injected']}"
    )

    if stats["chapters_thin"]:
        print("\n  Thin chapters (exactly 1 note — need ≥2 for heavy-pass):")
        print(f"    {stats['chapters_thin']}")
    if stats["chapters_empty"]:
        print("\n  Empty chapters (0 notes):")
        print(f"    {stats['chapters_empty']}")
    if stats["status"] == "complete":
        print(f"\n  ✅ all {stats['ch_count']} chapters have ≥2 notes; injected matches notes count.")
    if stats["notes_total"] > stats["injected"]:
        print(
            f"\n  ⚠ {stats['notes_total'] - stats['injected']} note(s) in content/notes/{stats['code']}.py "
            f"are not yet injected. Run scripts/run.py."
        )


def main():
    p = argparse.ArgumentParser(description="Track per-book amplification status.")
    p.add_argument("--book", help="show per-chapter detail for one book")
    p.add_argument("--thin", action="store_true", help="only show in-progress books")
    p.add_argument("--complete", action="store_true", help="only show complete books")
    p.add_argument("--untouched", action="store_true", help="only show untouched books")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--priority", action="store_true", help="sort by HANDOFF_README §5.2 priority order")
    args = p.parse_args()

    if args.book:
        try:
            book = config.get_book(args.book)
        except KeyError as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)
        stats = book_stats(book)
        if args.json:
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            print_book_detail(stats)
        return

    rows = [book_stats(b) for b in config.load_books()]

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    show_only = None
    if args.thin:
        show_only = {"in_progress"}
    if args.complete:
        show_only = {"complete"}
    if args.untouched:
        show_only = {"untouched"}

    ordered = PRIORITY_ORDER if args.priority else None
    print()
    print_dashboard(rows, show_only=show_only, ordered=ordered)


if __name__ == "__main__":
    main()

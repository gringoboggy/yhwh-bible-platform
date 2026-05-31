#!/usr/bin/env python3
"""
set_reader_toc.py — Toggle the EPUB reader's built-in Table of Contents
between "books-only" mode (87 entries: just the book titles) and "full" mode
(every chapter listed under every book, ~1790 entries).

Why this script exists
----------------------
Reader apps (Apple Books, Calibre, Thorium, Kindle, etc.) render the EPUB's term-ref-ok
nav.xhtml and toc.ncx into their own UI sheet. Most of them DO NOT support
collapsible/foldable nesting — they show the navigation as a flat or lightly-
indented list. For an 87-book Bible with ~1700 chapter entries, this is
overwhelming. "Books-only" mode produces a clean reader-TOC sheet showing
just the 87 books; the in-book HTML TOC (which IS collapsible) is unaffected.

Behaviour
---------
- `set_reader_toc.py --mode books-only` (default):
    Strips every chapter `<li>` (in nav.xhtml) and every nested `navPoint`
    (in toc.ncx). The reader-TOC will show only the 87 book titles plus the
    Table-of-Contents entry.
    On first run, the current full state is saved to the repo-relative
    ``.toc_state/`` directory so the operation is fully reversible.

- `set_reader_toc.py --mode full`:
    Restores chapters from the backup. Errors if no backup exists.

- The script is idempotent in either mode.

- The in-book visible HTML TOC (managed by apply_style.py) is left alone.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAV = ROOT / "epub_working" / "nav.xhtml"
NCX = ROOT / "epub_working" / "toc.ncx"
BACKUP_DIR = ROOT / ".toc_state"
NAV_BACKUP = BACKUP_DIR / "nav_full.xhtml"
NCX_BACKUP = BACKUP_DIR / "toc_full.ncx"


def count_entries(nav_text: str, ncx_text: str) -> tuple[int, int]:
    """Return (nav_li_count, ncx_navpoint_count)."""
    return nav_text.count("<li>"), ncx_text.count("<navPoint")


def is_books_only(nav_text: str) -> bool:
    """Heuristic: in books-only mode, no `<li>` lives inside a nested `<ol>`
    that lives inside another `<li>`. The simple test: in books-only, every
    `<ol>` is the top-level one, so there's exactly one `<ol>` containing
    all `<li>`s. In full mode, each book's `<li>` contains a child `<ol>`.
    """
    # Count nested <ol> tags inside <li> blocks.
    # In full mode, ~87 nested <ol>s. In books-only, 0.
    return _nested_ol_count(nav_text) == 0


def _nested_ol_count(nav_text: str) -> int:
    """Count `<ol>` tags that are nested inside a `<li>` (i.e., chapter lists)."""
    # The pattern `<li>...something...<ol>` where there's no closing </li>
    # before the <ol>. We use a non-greedy regex.
    return len(re.findall(r"<li>[^<]*<a [^>]*>[^<]+</a>\s*\n\s*<ol>", nav_text))


def save_backup(nav_text: str, ncx_text: str) -> None:
    """Save the current state as the canonical 'full' backup."""
    BACKUP_DIR.mkdir(exist_ok=True)
    NAV_BACKUP.write_text(nav_text, encoding="utf-8")
    NCX_BACKUP.write_text(ncx_text, encoding="utf-8")


def has_backup() -> bool:
    return NAV_BACKUP.exists() and NCX_BACKUP.exists()


def strip_chapters_from_nav(nav_text: str) -> str:
    """Remove every nested `<ol>...</ol>` (chapter list) from nav.xhtml.

    Pattern: a book entry is `<li>\\s*<a ...>...</a>\\n<ol>...</ol>\\s*</li>`.
    We replace the inner `<ol>...</ol>` block with nothing, leaving the book
    entry collapsed: `<li><a ...>...</a></li>`.
    """
    # Match: `<a ...>BookTitle</a>` followed by optional whitespace, then
    # `<ol>...</ol>` (possibly multi-line), then optional whitespace, then `</li>`.
    # Be careful: the inner <ol> can span hundreds of lines and contain many <li>.
    # We use a non-greedy match constrained to NOT cross another book's <li>.
    # The safest delimiter: a chapter <ol> always immediately precedes `</li>`
    # of the parent book.
    pat = re.compile(
        r"(<li>\s*<a [^>]+>[^<]+</a>)\s*\n\s*<ol>.*?</ol>\s*(</li>)",
        re.DOTALL,
    )
    return pat.sub(r"\1\2", nav_text)


def strip_chapters_from_ncx(ncx_text: str) -> str:
    """Remove nested `<navPoint>` children from each book's `<navPoint>`.

    Each book navPoint looks like:
      <navPoint id="..." playOrder="...">
        <navLabel><text>Genesis</text></navLabel>
        <content src="..."/>
        <navPoint ...>     <!-- chapter (depth 2) -->
          <navLabel><text>1</text></navLabel>
          <content src="..."/>
        </navPoint>
        <navPoint ...>     <!-- chapter -->
        ...
      </navPoint>          <!-- book close -->

    Strategy: track navPoint nesting depth across lines. Keep lines whose
    nesting never reaches depth >= 2 — i.e., book-level entries are kept,
    chapter-level (and deeper) are dropped. The book's own `<navPoint>`
    open and close lines stay at depth 1 (max), so they survive.
    """
    out = []
    depth = 0  # nesting level of currently-open navPoints, BEFORE this line
    for line in ncx_text.split("\n"):
        opens = len(re.findall(r"<navPoint\b", line))
        closes = line.count("</navPoint>")
        # If, at any point during this line, depth would be >= 2, drop the line.
        # That covers:
        #   - chapter <navPoint> openings (depth 1 → 2)
        #   - chapter <navLabel>/<content> contents (still depth 2)
        #   - chapter </navPoint> closings (depth 2 → 1; depth_at_start = 2)
        peak_depth = depth + opens  # highest depth this line sees
        keep = (peak_depth < 2) and (depth < 2)
        if keep:
            out.append(line)
        depth += opens - closes
    rebuilt = "\n".join(out)
    # Renumber playOrder for surviving (top-level) navPoints
    play_order = [1]

    def renumber(_m):
        n = play_order[0]
        play_order[0] += 1
        return f'playOrder="{n}"'

    rebuilt = re.sub(r'playOrder="\d+"', renumber, rebuilt)
    return rebuilt


def main():
    ap = argparse.ArgumentParser(description="Toggle the reader-TOC between books-only and full modes.")
    ap.add_argument(
        "--mode",
        choices=["books-only", "full"],
        default="books-only",
        help="books-only (default): strip chapters; full: restore chapters from backup.",
    )
    ap.add_argument(
        "--status",
        action="store_true",
        help="Print current TOC state and exit.",
    )
    args = ap.parse_args()

    if not NAV.exists() or not NCX.exists():
        print(f"ERROR: nav.xhtml or toc.ncx not found in {NAV.parent}", file=sys.stderr)
        return 1

    nav_text = NAV.read_text(encoding="utf-8")
    ncx_text = NCX.read_text(encoding="utf-8")
    nav_li, ncx_np = count_entries(nav_text, ncx_text)
    current_mode = "books-only" if is_books_only(nav_text) else "full"

    if args.status:
        print("Reader-TOC state:")
        print(f"  nav.xhtml: {nav_li} <li> entries  (mode: {current_mode})")
        print(f"  toc.ncx:   {ncx_np} <navPoint> entries")
        print(f"  backup present: {has_backup()}")
        return 0

    if args.mode == "books-only":
        if current_mode == "books-only":
            print(f"Already in books-only mode ({nav_li} <li> entries). No-op.")
            return 0
        # Save backup if not present
        if not has_backup():
            save_backup(nav_text, ncx_text)
            print(f"  Saved backup: {NAV_BACKUP.relative_to(ROOT)}, {NCX_BACKUP.relative_to(ROOT)}")
        new_nav = strip_chapters_from_nav(nav_text)
        new_ncx = strip_chapters_from_ncx(ncx_text)
        NAV.write_text(new_nav, encoding="utf-8")
        NCX.write_text(new_ncx, encoding="utf-8")
        new_li, new_np = count_entries(new_nav, new_ncx)
        print(f"  nav.xhtml: {nav_li} → {new_li} entries")
        print(f"  toc.ncx:   {ncx_np} → {new_np} entries")
        print("Reader-TOC now in BOOKS-ONLY mode.")
        return 0

    # mode == "full"
    if not has_backup():
        print(
            "ERROR: no backup available; cannot restore full mode.\n"
            "       Restore epub_working/nav.xhtml from git history (the build_toc.py\n"
            "       regenerator was retired with source_archive/).",
            file=sys.stderr,
        )
        return 2
    if current_mode == "full":
        print(f"Already in full mode ({nav_li} <li> entries). No-op.")
        return 0
    new_nav = NAV_BACKUP.read_text(encoding="utf-8")
    new_ncx = NCX_BACKUP.read_text(encoding="utf-8")
    NAV.write_text(new_nav, encoding="utf-8")
    NCX.write_text(new_ncx, encoding="utf-8")
    new_li, new_np = count_entries(new_nav, new_ncx)
    print("  Restored from backup.")
    print(f"  nav.xhtml: {nav_li} → {new_li} entries")
    print(f"  toc.ncx:   {ncx_np} → {new_np} entries")
    print("Reader-TOC now in FULL mode.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

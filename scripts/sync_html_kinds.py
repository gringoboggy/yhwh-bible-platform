#!/usr/bin/env python3
"""
sync_html_kinds.py — Sync rendered HTML note classes to match source kinds.

When a source note's kind changes (e.g. via retag.py: comm → comm-patristic),
the rendered HTML in epub_working/ keeps its ORIGINAL class names because
the rendered HTML was baked at injection time. This breaks edition
filtering: build_edition.py filters by the HTML class, not the source.

This tool walks each book's source notes, computes the expected HTML
``note-<kind>`` / ``marker-<kind>`` classes, and rewrites the matching
HTML elements (the marker <a>, its inner <sup>, and the aside <aside>).

Operates on three element families per note:

    <a  class="note-ref note-XXX"  id="ref-{prefix}{cc}{vv}{s}" ...>
      <sup class="marker-XXX">…</sup>
    </a>
    <aside class="note note-XXX"  id="note-{prefix}{cc}{vv}{s}" ...>

(prefix from book.id_prefix; cc/vv zero-padded; s optional suffix letter)

This is NOT an injector — it does not insert new notes, only updates the
classes of notes already present in the HTML. For inserting brand-new
notes into the HTML (Strategy-A injection proper), a separate tool is
needed.

Usage:
    python3 scripts/sync_html_kinds.py --book gen --dry-run
    python3 scripts/sync_html_kinds.py --book gen
    python3 scripts/sync_html_kinds.py --all-books

Crash-safe: ensure_backup() + atomic_write() per modified HTML file.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402
from scripts.core.notes_io import atomic_write, ensure_backup  # noqa: E402

EPUB_DIR = REPO_ROOT / "epub_working"
NOTES_DIR = REPO_ROOT / "content" / "notes"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def load_source_notes(book_code: str) -> list[tuple]:
    path = NOTES_DIR / f"{book_code}.py"
    if not path.is_file():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "NOTES":
                    return ast.literal_eval(node.value)
    return []


def build_id(prefix: str, ch: int, v: int, suffix: str) -> str:
    return f"{prefix}{ch:02d}{v:02d}{suffix}"


def sync_book(book: dict, dry_run: bool) -> dict:
    """Sync one book's HTML files to match source kinds.

    Strategy A books (early canon) use deep-link anchors
    `id="ref-{prefix}{cc}{vv}{s}"` and are fully supported here.

    Strategy B books (late canon) use plain `<span class="vn">N</span>`
    chapter-scoped markers and need a different note-locating algorithm.
    For now this tool returns a clean "skip" stat for Strategy B books
    that have no notes (the 99% case for late canon currently); books
    with notes but no `id_prefix` get a clear "needs Strategy B
    implementation" warning instead of a generic metadata error.

    Returns:
        {
            scanned: int,        # source notes examined
            already_ok: int,     # HTML class already matched source
            updated: int,        # HTML class rewritten
            not_found: int,      # source note's id not located in HTML
            skipped_reason: str (optional),
            files_changed: list[str],
            error: str (optional),
        }
    """
    code = book["code"]
    prefix = book.get("id_prefix")
    files = book.get("files", [])
    strategy = book.get("strategy", "A")

    notes = load_source_notes(code)

    # Strategy B (no id_prefix by design)
    if not prefix:
        if not notes:
            return {
                "scanned": 0,
                "already_ok": 0,
                "updated": 0,
                "not_found": [],
                "files_changed": [],
                "skipped_reason": f"strategy {strategy} (no id_prefix)",
            }
        return {
            "error": (
                f"book {code} is strategy {strategy} (no id_prefix) but has "
                f"{len(notes)} note(s); Strategy-B HTML sync is not yet "
                f"implemented. Notes will not appear in edition-filtered EPUBs "
                f"until this is added."
            ),
        }

    if not files:
        return {"error": f"book {code} missing files in metadata"}

    notes = load_source_notes(code)

    # Build a map of full_id → expected_kind
    expected: dict[str, str] = {}
    for tup in notes:
        if not isinstance(tup, tuple) or len(tup) < 5:
            continue
        ch, v, suffix, _anchor, kind = tup[:5]
        full_id = build_id(prefix, ch, v, suffix or "")
        expected[full_id] = kind

    stats = {
        "scanned": len(expected),
        "already_ok": 0,
        "updated": 0,
        "not_found": set(expected.keys()),
        "files_changed": [],
    }

    # Walk each HTML file for this book
    for fname in files:
        fpath = EPUB_DIR / fname
        if not fpath.is_file():
            continue
        text = fpath.read_text(encoding="utf-8")
        original = text

        # For every expected id present in this file, check + update
        for full_id, new_kind in expected.items():
            new_note_class = f"note-{new_kind}"
            new_marker_class = f"marker-{new_kind}"

            # Locate the <a class="note-ref note-K…" ... id="ref-FULLID" ...>...<sup class="marker-K…">...</sup></a>
            # The ref pattern handles attribute ordering: class first, id appears later.
            ref_re = re.compile(
                r'(<a\s+class="note-ref\s+)(note-[a-z0-9-]+)(")([^>]*\bid="ref-'
                + re.escape(full_id)
                + r'"[^>]*>\s*<sup\s+class=")(marker-[a-z0-9-]+)(">)'
            )
            m = ref_re.search(text)
            if m:
                stats["not_found"].discard(full_id)
                old_note = m.group(2)
                old_marker = m.group(5)
                if old_note == new_note_class and old_marker == new_marker_class:
                    stats["already_ok"] += 1
                else:
                    text = ref_re.sub(
                        lambda mm, new_note_class=new_note_class, new_marker_class=new_marker_class: (
                            f"{mm.group(1)}{new_note_class}{mm.group(3)}{mm.group(4)}{new_marker_class}{mm.group(6)}"
                        ),
                        text,
                        count=1,
                    )
                    stats["updated"] += 1

            # Same for the corresponding <aside>
            aside_re = re.compile(
                r'(<aside\s+class="note\s+)(note-[a-z0-9-]+)(")([^>]*\bid="note-' + re.escape(full_id) + r'")'
            )
            ma = aside_re.search(text)
            if ma:
                stats["not_found"].discard(full_id)
                old = ma.group(2)
                if old != new_note_class:
                    text = aside_re.sub(
                        lambda mm, new_note_class=new_note_class: (
                            f"{mm.group(1)}{new_note_class}{mm.group(3)}{mm.group(4)}"
                        ),
                        text,
                        count=1,
                    )
                    # already counted under "updated" (rare to update aside without ref)

        if text != original:
            stats["files_changed"].append(fname)
            if not dry_run:
                ensure_backup(fpath)
                atomic_write(fpath, text)

    stats["not_found"] = sorted(stats["not_found"])
    return stats


def main() -> None:
    p = argparse.ArgumentParser(description="Sync HTML note classes to source kinds.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--book", help="single book code (e.g. 'gen')")
    g.add_argument("--all-books", action="store_true", help="every book in canon")
    p.add_argument("--dry-run", action="store_true", help="show what would change, don't write")
    args = p.parse_args()

    books = [config.get_book(args.book)] if args.book else config.load_books()

    print(f"\n{BOLD}sync-html-kinds{RESET} {DIM}{len(books)} book(s){'  (dry-run)' if args.dry_run else ''}{RESET}\n")

    grand = {"scanned": 0, "already_ok": 0, "updated": 0, "not_found": 0}
    files_changed: set = set()
    failed = []

    for book in books:
        code = book["code"]
        if not (NOTES_DIR / f"{code}.py").is_file():
            continue
        stats = sync_book(book, dry_run=args.dry_run)
        if "error" in stats:
            print(f"  {RED}✗ {code:6}{RESET}  {stats['error']}")
            failed.append(code)
            continue
        if stats.get("skipped_reason"):
            print(f"  {DIM}○ {code:6}  skipped — {stats['skipped_reason']}{RESET}")
            continue

        verb = "would update" if args.dry_run else "updated"
        s = stats["scanned"]
        u = stats["updated"]
        ok = stats["already_ok"]
        nf = len(stats["not_found"])
        if s == 0:
            continue
        flag = GREEN + "✓" if not nf else YELLOW + "⚠"
        print(
            f"  {flag}{RESET} {code:6}  "
            f"{s:>4} src · "
            f"{u:>4} {verb} · "
            f"{ok:>4} already ok" + (f" · {RED}{nf} not found in HTML{RESET}" if nf else "")
        )
        grand["scanned"] += s
        grand["updated"] += u
        grand["already_ok"] += ok
        grand["not_found"] += nf
        files_changed.update(stats["files_changed"])

    print(
        f"\n  {BOLD}TOTAL{RESET}: "
        f"{grand['scanned']} src · "
        f"{grand['updated']} {'would-update' if args.dry_run else 'updated'} · "
        f"{grand['already_ok']} already ok · "
        f"{grand['not_found']} not found"
    )
    if files_changed:
        print(f"  files {'would be' if args.dry_run else ''} modified: {len(files_changed)}")
    print()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

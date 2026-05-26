#!/usr/bin/env python3
"""Phase χ.6 — Batch-promote all candidate files in one process.

Avoids the per-file subprocess overhead of looping
`promote.py --promote-top N`. Calls promote_candidate() in-process.

Usage:
    python3 scripts/batch_promote_xrefs.py
    python3 scripts/batch_promote_xrefs.py --kind xref-citation
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.promote import promote_candidate, batch_insert_notes, NOTES_DIR  # noqa: E402
from scripts.core.matrix import AI_DRAFTED_KINDS  # noqa: E402
from scripts.core.html_sandbox import sandbox_ai_html  # noqa: E402

CANDIDATES_DIR = REPO_ROOT / "content" / "candidates"


def _candidate_to_note(c: dict, chapter: int) -> dict:
    """Convert a candidate dict to the note-dict ``batch_insert_notes`` expects,
    replicating ``promote_candidate``'s transforms (attribution compose + the AI
    sandbox pass for AI-drafted kinds)."""
    body = c["draft_body"]
    if c["kind"] in AI_DRAFTED_KINDS:
        body = sandbox_ai_html(body)
    attribution = (c.get("source_attribution") or "").strip() or None
    if not attribution and c.get("source_name"):
        attribution = c["source_name"]
    return {
        "chapter": chapter,
        "verse": c["verse"],
        "kind": c["kind"],
        "body": body,
        "anchor": c.get("anchor", ""),
        "title": c.get("draft_title", "Note"),
        "label": c.get("draft_label", "Note"),
        "attribution": attribution,
    }


def promote_by_book(files: list[Path], kind: str | None, max_per_file: int | None) -> tuple[int, int, int]:
    """Fast path: group all pending (kind-filtered) candidates by book and insert
    them with ONE read+write per book via ``batch_insert_notes``, instead of one
    full file rewrite per candidate. Same result, O(books) writes instead of
    O(candidates) (the per-candidate loop is O(candidates × filesize)). Returns
    (attempted, promoted, books_changed)."""
    by_book: dict[str, list[dict]] = {}
    attempted = 0
    for fp in files:
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ✗ {fp.name}: parse error: {e}")
            continue
        cands = data["candidates"]
        if kind:
            cands = [c for c in cands if c.get("kind") == kind]
        cands = [c for c in cands if c.get("status") == "pending"]
        if max_per_file:
            cands = cands[:max_per_file]
        for c in cands:
            attempted += 1
            by_book.setdefault(data["book"], []).append(_candidate_to_note(c, data["chapter"]))
    promoted = 0
    books_changed = 0
    for book, notes in sorted(by_book.items()):
        book_path = NOTES_DIR / f"{book}.py"
        if not book_path.is_file():
            print(f"  ⚠ {book}: no notes file ({book}.py) — skipping {len(notes)} candidate(s)")
            continue
        n = batch_insert_notes(book_path, notes, skip_existing=True)
        if n:
            promoted += n
            books_changed += 1
            print(f"  ✓ {book}: {n} inserted ({len(notes)} candidates seen)")
    return attempted, promoted, books_changed


def main() -> int:
    p = argparse.ArgumentParser(description="Batch-promote candidate notes.")
    p.add_argument("--kind", default=None, help="only promote candidates of this kind (e.g. xref-citation)")
    p.add_argument(
        "--max-per-file", type=int, default=None, help="cap how many candidates to promote per file (default: no cap)"
    )
    p.add_argument(
        "--by-book",
        action="store_true",
        help="fast path: batch-insert per book (one file write per book, not one per candidate)",
    )
    args = p.parse_args()

    files = sorted(CANDIDATES_DIR.glob("*.json"))
    print(f"Found {len(files)} candidate files. Filter: kind={args.kind!r}")

    if args.by_book:
        attempted, promoted, books_changed = promote_by_book(files, args.kind, args.max_per_file)
        print()
        print(f"Attempted: {attempted}")
        print(f"Promoted:  {promoted}")
        print(f"Skipped:   {attempted - promoted} (already exists, or coord-guarded)")
        print(f"Books affected: {books_changed}")
        return 0

    total_attempted = 0
    total_promoted = 0
    total_skipped = 0
    total_errors = 0
    files_with_change = 0

    for fp in files:
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ✗ {fp.name}: parse error: {e}")
            total_errors += 1
            continue
        book = data["book"]
        chapter = data["chapter"]
        cands = data["candidates"]
        # Filter by kind if specified
        if args.kind:
            cands = [c for c in cands if c.get("kind") == args.kind]
        # Filter to pending only
        cands = [c for c in cands if c.get("status") == "pending"]
        if args.max_per_file:
            cands = cands[: args.max_per_file]
        if not cands:
            continue
        promoted_in_file = 0
        for c in cands:
            # promote_candidate expects chapter on the candidate dict
            c["chapter"] = chapter
            total_attempted += 1
            try:
                ok, suffix = promote_candidate(book, c)
                if ok:
                    total_promoted += 1
                    promoted_in_file += 1
                else:
                    total_skipped += 1
            except Exception as e:
                print(f"    ✗ {c.get('id', '?')}: {type(e).__name__}: {e}")
                total_errors += 1
        if promoted_in_file > 0:
            files_with_change += 1
            print(f"  ✓ {fp.name}: {promoted_in_file}/{len(cands)} promoted")

    print()
    print(f"Attempted: {total_attempted}")
    print(f"Promoted:  {total_promoted}")
    print(f"Skipped:   {total_skipped} (already exists, or rejected)")
    print(f"Errors:    {total_errors}")
    print(f"Files affected: {files_with_change}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

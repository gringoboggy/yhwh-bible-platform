#!/usr/bin/env python3
"""Phase χ.6 — Batch-promote all candidate files in one process.

Avoids the per-file subprocess overhead of looping
`promote.py --promote-top N`. Calls promote_candidate() in-process.

By default uses the by-book fast path (one file write per book via
``batch_insert_notes``); pass ``--per-candidate`` to fall back to the slow
``promote_candidate`` loop (one full file rewrite per candidate).

Usage:
    python3 scripts/batch_promote_xrefs.py
    python3 scripts/batch_promote_xrefs.py --kind xref-citation
    python3 scripts/batch_promote_xrefs.py --per-candidate
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.promote import (  # noqa: E402
    NOTES_DIR,
    _REVIEWER_SCAFFOLD_RE,
    batch_insert_notes,
    promote_candidate,
    update_queue_status,
)
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
    # mint-11 audit HIGH-2: strip the editorial [Reviewer: …] scaffold exactly as
    # the slow promote_candidate() path does — otherwise the fast by-book path would
    # write that instruction text verbatim into content/notes/<book>.py and every EPUB.
    body = _REVIEWER_SCAFFOLD_RE.sub("", body)
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
    file_meta: dict[Path, tuple[dict, list[dict], int]] = {}
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
        if not cands:
            continue
        file_meta[fp] = (data, cands, data["chapter"])
        for c in cands:
            attempted += 1
            by_book.setdefault(data["book"], []).append(_candidate_to_note(c, data["chapter"]))
    promoted = 0
    books_changed = 0
    # mint-11 audit HIGH-1: track which books were actually processed (notes file
    # present) so the status-marking loop below never marks candidates "promoted"
    # for a book we skipped. 1ma/2ma have no notes file — marking their pending
    # candidates would silently drop them from the pipeline with no error.
    successful_books: set[str] = set()
    for book, notes in sorted(by_book.items()):
        book_path = NOTES_DIR / f"{book}.py"
        if not book_path.is_file():
            print(f"  ⚠ {book}: no notes file ({book}.py) — skipping {len(notes)} candidate(s)")
            continue
        successful_books.add(book)
        satisfied: set[tuple[int, int, str, str]] = set()
        n = batch_insert_notes(book_path, notes, skip_existing=True, satisfied_out=satisfied)
        if n:
            promoted += n
            books_changed += 1
            print(f"  ✓ {book}: {n} inserted ({len(notes)} candidates seen)")
        # mint-11 HIGH-1: only mark candidates whose note landed (inserted or
        # skip_existing match). Out-of-extent / parse-failure drops stay pending.
        from scripts.core.notes_io import atomic_write

        for fp, (data, to_mark, ch) in file_meta.items():
            if data.get("book") != book:
                continue
            changed = False
            for c in to_mark:
                note = _candidate_to_note(c, ch)
                key = (note["chapter"], note["verse"], note["kind"], note["body"])
                if key in satisfied:
                    c["status"] = "promoted"
                    changed = True
            if changed:
                atomic_write(fp, json.dumps(data, indent=2, ensure_ascii=False))
    return attempted, promoted, books_changed


def main() -> int:
    p = argparse.ArgumentParser(description="Batch-promote candidate notes.")
    p.add_argument("--kind", default=None, help="only promote candidates of this kind (e.g. xref-citation)")
    p.add_argument(
        "--max-per-file", type=int, default=None, help="cap how many candidates to promote per file (default: no cap)"
    )
    p.add_argument(
        "--per-candidate",
        action="store_true",
        help="slow path: one file-rewrite per candidate (default: by-book, one write per book)",
    )
    args = p.parse_args()

    files = sorted(CANDIDATES_DIR.glob("*.json"))
    print(f"Found {len(files)} candidate files. Filter: kind={args.kind!r}")

    if not args.per_candidate:
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
                    cid = c.get("id")
                    if cid:
                        update_queue_status(fp, cid, "promoted")
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

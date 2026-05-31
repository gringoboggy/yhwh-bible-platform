#!/usr/bin/env python3
"""Phase ω.40 — Ethiopian Tewahedo commentary at-scale driver
(N-C1 closure per AUDIT_2026-05-13).

Mirrors the established χ-cluster pattern (run_xref_at_scale.py /
run_naves_at_scale.py / run_hebrew_at_scale.py): bypasses
prospect.py's EPUB-build dependency by iterating the cached
ethiopian_commentaries.json source corpus directly.
EthiopianCommentaryDetector ignores verse text — it only needs
(book, chapter, verse) tuples — so this composition is faithful
to the existing pipeline, just with a different iteration source.

Output: writes candidates JSON files in the same prospect.py format
to ``content/candidates/<book>_ch_<NNN>.json``. ``scripts/promote.py``
and ``scripts/batch_promote_xrefs.py --kind comm-ethiopian`` work
unchanged.

Append-not-overwrite per chapter — coexists with the other χ-cluster
drivers' candidate files (xref / hebrew / greek / naves) on the
same chapter file. New candidates get fresh ids; existing
candidates are kept as-is (their ``status`` field carries any prior
promotion record).

Usage:
    python3 scripts/run_ethiopian_at_scale.py                # all 9 books
    python3 scripts/run_ethiopian_at_scale.py --books jhn,luk
    python3 scripts/run_ethiopian_at_scale.py --dry-run      # report only
"""

from __future__ import annotations
import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.detectors import EthiopianCommentaryDetector  # noqa: E402
from scripts.core.sources import EthiopianCommentaries, _normalize_book_code  # noqa: E402
from scripts.core.at_scale_base import DIM, GREEN, RESET, candidate_to_dict  # noqa: E402
from scripts.core.notes_io import atomic_write  # noqa: E402

CANDIDATES_DIR = REPO_ROOT / "content" / "candidates"


def write_queue(book: str, chapter: int, candidates: list) -> Path | None:
    """Append-not-overwrite per chapter — same pattern as
    run_naves_at_scale.write_queue. Lets multiple at-scale drivers
    coexist on the same chapter file. New candidates get fresh ids
    after the existing tail; existing entries are kept as-is.
    """
    if not candidates:
        return None
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CANDIDATES_DIR / f"{book}_ch_{chapter:03d}.json"

    existing: list[dict] = []
    if out_path.is_file():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8")).get("candidates", [])
        except (json.JSONDecodeError, OSError):
            existing = []

    # ids continue from the existing tail to avoid collisions
    start_idx = len(existing) + 1
    new_dicts = [candidate_to_dict(c, start_idx + i) for i, c in enumerate(candidates)]
    payload = {
        "book": book,
        "chapter": chapter,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_candidates": len(existing) + len(new_dicts),
        "candidates": existing + new_dicts,
    }
    atomic_write(out_path, json.dumps(payload, indent=2, ensure_ascii=False))
    return out_path


def run_ethiopian_for_book(book: str, *, dry_run: bool = False) -> dict:
    """Iterate the ethiopian_commentaries source corpus for one book,
    run EthiopianCommentaryDetector per verse, write per-chapter
    candidates JSON. Returns stats.

    The book parameter accepts either canonical (jhn / psa) or legacy
    (joh / ps) codes — `_normalize_book_code` aliases via ω.36."""
    ec = EthiopianCommentaries()
    detector = EthiopianCommentaryDetector()
    canon_book = _normalize_book_code(book)

    # Collect entries for this book and group by chapter
    by_chapter: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for (b, chapter, verse), entries in ec._by_verse.items():
        if b != canon_book:
            continue
        # The detector calls for_verse internally, so we just need to
        # iterate the unique (chapter, verse) pairs once.
        by_chapter[chapter].append((verse, len(entries)))

    chapters_processed = 0
    candidates_written = 0
    files_written = 0

    for chapter in sorted(by_chapter):
        chapters_processed += 1
        chapter_candidates = []
        # detect() reads from the corpus directly — we just iterate verses
        seen_verses: set[int] = set()
        for verse, _entry_count in sorted(by_chapter[chapter]):
            if verse in seen_verses:
                continue
            seen_verses.add(verse)
            cands = detector.detect(canon_book, chapter, verse, "")
            chapter_candidates.extend(cands)
        if chapter_candidates:
            if dry_run:
                files_written += 1
                candidates_written += len(chapter_candidates)
            else:
                out = write_queue(canon_book, chapter, chapter_candidates)
                if out:
                    files_written += 1
                    candidates_written += len(chapter_candidates)
    return {
        "book": canon_book,
        "chapters_processed": chapters_processed,
        "candidates_written": candidates_written,
        "files_written": files_written,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Run EthiopianCommentaryDetector at scale via direct source iteration.")
    p.add_argument("--books", help="comma-separated list of books (default: all 9 in the source corpus)")
    p.add_argument("--dry-run", action="store_true", help="report counts without writing candidate files")
    args = p.parse_args()

    # Determine book list — default to every book the corpus actually covers
    ec = EthiopianCommentaries()
    covered_books: set[str] = set()
    for b, _c, _v in ec._by_verse:
        covered_books.add(b)

    if args.books:
        books = [_normalize_book_code(b.strip()) for b in args.books.split(",")]
    else:
        books = sorted(covered_books)

    mode = "DRY-RUN " if args.dry_run else ""
    print(
        f"{mode}Running EthiopianCommentaryDetector across {len(books)} books ({len(covered_books)} covered in source corpus)"
    )
    print()

    total_chapters = 0
    total_candidates = 0
    total_files = 0
    for book in books:
        stats = run_ethiopian_for_book(book, dry_run=args.dry_run)
        if stats["candidates_written"]:
            print(
                f"  {GREEN}✓{RESET} {book:5s} "
                f"{stats['chapters_processed']:3d} chapters "
                f"→ {stats['candidates_written']:5d} candidates "
                f"({stats['files_written']} files)"
            )
        else:
            print(f"  {DIM}-{RESET} {book:5s} {stats['chapters_processed']:3d} chapters → 0 candidates")
        total_chapters += stats["chapters_processed"]
        total_candidates += stats["candidates_written"]
        total_files += stats["files_written"]

    print()
    print(
        f"TOTAL: {len(books)} books · {total_chapters} chapters · "
        f"{total_candidates} candidates · {total_files} candidate files"
    )
    if not args.dry_run:
        print(f"Files written under: {CANDIDATES_DIR}")
        print()
        print("Next step: python3 scripts/batch_promote_xrefs.py --kind comm-ethiopian")
    return 0


if __name__ == "__main__":
    sys.exit(main())

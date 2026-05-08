#!/usr/bin/env python3
"""GreekWord at scale — driver script (χ.1).

Mirrors scripts/run_hebrew_at_scale.py but for GreekWordDetector.
Bypasses prospect.py's EPUB-build dependency by reading verse
text directly from the KJV translation data.

Output: writes candidates JSON files in the same format as
prospect.py to content/candidates/. From there, scripts/promote.py
or scripts/batch_promote_xrefs.py works unchanged.

Usage:
    python3 scripts/run_greek_at_scale.py
    python3 scripts/run_greek_at_scale.py --books jhn,rom
    python3 scripts/run_greek_at_scale.py --min-confidence 0.85
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.detectors import GreekWordDetector  # noqa: E402
from scripts.core import translations  # noqa: E402
from scripts.core import config  # noqa: E402

CANDIDATES_DIR = REPO_ROOT / "content" / "candidates"

GREEN = "\033[92m"
DIM = "\033[2m"
RESET = "\033[0m"

# NT books — only set the detector emits candidates for. Mirror of the
# detector's NT_BOOKS so the driver can fast-skip OT books before any
# detector instantiation.
NT_BOOKS = {
    "mat", "mrk", "luk", "jhn", "act", "rom", "1co", "2co", "gal",
    "eph", "php", "col", "1th", "2th", "1ti", "2ti", "tit", "phm",
    "heb", "jas", "1pe", "2pe", "1jn", "2jn", "3jn", "jud", "rev",
}


def candidate_to_dict(c, idx: int) -> dict:
    """Mirror prospect.py's candidate_to_dict — promote.py works unchanged."""
    return {
        "id": f"{c.book}-{c.chapter}-{c.verse}-{idx:03d}",
        "verse": c.verse,
        "kind": c.kind,
        "anchor": c.anchor,
        "confidence": round(c.confidence, 3),
        "source_name": c.source_name,
        "source_attribution": c.source_attribution,
        "draft_title": c.draft_title,
        "draft_label": c.draft_label,
        "draft_body": c.draft_body,
        "detector": c.detector,
        "reviewer_notes": c.reviewer_notes,
        "status": "pending",
    }


def write_queue(book: str, chapter: int, candidates: list) -> Path | None:
    if not candidates:
        return None
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CANDIDATES_DIR / f"{book}_ch_{chapter:03d}.json"
    # Read existing file if present (could have xref-citation /
    # lang-hebrew / topic-nave candidates from prior at-scale runs);
    # merge by appending lang-greek candidates rather than overwriting.
    existing_candidates = []
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            existing_candidates = [c for c in existing.get("candidates", [])
                                    if c.get("kind") != "lang-greek"]
        except Exception:
            pass
    new_dicts = [candidate_to_dict(c, i)
                 for i, c in enumerate(candidates,
                                        start=len(existing_candidates) + 1)]
    all_candidates = existing_candidates + new_dicts
    payload = {
        "book": book,
        "chapter": chapter,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_candidates": len(all_candidates),
        "candidates": all_candidates,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    return out_path


def run_greek_for_book(book: str, *, min_confidence: float = 0.7) -> dict:
    """Iterate KJV verses for one NT book, run GreekWordDetector,
    write candidates JSON per chapter. Returns stats."""
    if book not in NT_BOOKS:
        return {"book": book, "skipped": True, "reason": "OT (no NT Greek)",
                "chapters_processed": 0, "candidates_written": 0,
                "files_written": 0}

    if not translations.has_book("kjv", book):
        return {"book": book, "skipped": True, "reason": "no KJV data",
                "chapters_processed": 0, "candidates_written": 0,
                "files_written": 0}

    detector = GreekWordDetector()

    # Discover chapter count from the books.yaml metadata; fall back
    # to a generous upper bound if absent (matches Hebrew driver).
    try:
        book_meta = config.get_book(book)
        n_chapters = book_meta.get("chapters", 50) if book_meta else 50
    except KeyError:
        n_chapters = 50

    chapters_processed = 0
    candidates_written = 0
    files_written = 0

    for chapter in range(1, n_chapters + 1):
        verses = translations.get_chapter("kjv", book, chapter)
        if not verses:
            continue
        chapters_processed += 1
        chapter_candidates = []
        for verse_num, verse_text in verses:
            cands = detector.detect(book, chapter, verse_num, verse_text)
            for c in cands:
                if c.confidence >= min_confidence:
                    chapter_candidates.append(c)
        if chapter_candidates:
            out = write_queue(book, chapter, chapter_candidates)
            if out:
                files_written += 1
                candidates_written += len(chapter_candidates)
    return {
        "book": book,
        "skipped": False,
        "chapters_processed": chapters_processed,
        "candidates_written": candidates_written,
        "files_written": files_written,
    }


def main() -> int:
    p = argparse.ArgumentParser(
        description="Run GreekWordDetector at scale via direct KJV iteration.",
    )
    p.add_argument("--books",
                    help="comma-separated list of NT books (default: all)")
    p.add_argument("--min-confidence", type=float, default=0.7)
    args = p.parse_args()

    if args.books:
        books = args.books.split(",")
    else:
        # All books we have KJV data for; filter to NT.
        all_books = [Path(p).stem
                     for p in (REPO_ROOT / "content/translations/kjv").glob("*.py")]
        books = sorted(b for b in all_books if b in NT_BOOKS)

    print(f"Running GreekWordDetector across {len(books)} NT books "
          f"(min-conf={args.min_confidence})")
    print()

    total_chapters = 0
    total_candidates = 0
    total_files = 0
    skipped_count = 0
    for book in books:
        stats = run_greek_for_book(
            book, min_confidence=args.min_confidence,
        )
        if stats.get("skipped"):
            skipped_count += 1
            print(f"  {DIM}-{RESET} {book:5s} "
                  f"skipped ({stats.get('reason', '?')})")
            continue
        if stats["candidates_written"]:
            print(f"  {GREEN}✓{RESET} {book:5s} "
                  f"{stats['chapters_processed']:3d} chapters "
                  f"→ {stats['candidates_written']:5d} candidates "
                  f"({stats['files_written']} files)")
        else:
            print(f"  {DIM}-{RESET} {book:5s} "
                  f"{stats['chapters_processed']:3d} chapters → 0 candidates")
        total_chapters += stats["chapters_processed"]
        total_candidates += stats["candidates_written"]
        total_files += stats["files_written"]

    print()
    print(f"TOTAL: {len(books) - skipped_count} books processed · "
          f"{total_chapters} chapters · "
          f"{total_candidates} candidates · {total_files} candidate files")
    print(f"({skipped_count} books skipped — OT or no KJV data)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Phase χ.6 — TSK xref at-scale driver.

Bypasses prospect.py's EPUB-build dependency (which calls
`discover_chapters()` that reads epub_working/) by iterating the
already-cached TSK xref data directly. The CrossRefDetector
ignores verse text anyway — it just needs (book, chapter, verse)
tuples — so this composition is faithful to the existing pipeline,
just with a different iteration source.

Output: writes candidates JSON files in the same format as
prospect.py to content/candidates/<book>_ch_<NNN>.json. From there,
scripts/promote.py works unchanged.

Usage:
    python3 scripts/run_xref_at_scale.py                # all books
    python3 scripts/run_xref_at_scale.py --books gen,exo,lev
    python3 scripts/run_xref_at_scale.py --min-confidence 0.7
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.detectors import CrossRefDetector  # noqa: E402
from scripts.core import sources  # noqa: E402

CANDIDATES_DIR = REPO_ROOT / "content" / "candidates"
TSK_PATH = REPO_ROOT / "content" / "sources" / "tsk_xrefs.json"

GREEN = "\033[92m"
DIM = "\033[2m"
RESET = "\033[0m"


def candidate_to_dict(c, idx: int) -> dict:
    """Mirror of prospect.py's candidate_to_dict — same shape so
    promote.py works unchanged."""
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
    """Same output format as prospect.write_queue — promote.py works on these
    unchanged. APPENDS rather than overwrites: multiple at-scale drivers (xref,
    hebrew, naves, …) coexist on the same chapter file, so existing candidates
    are preserved and new ones get fresh ids continuing from the existing tail.
    (mint-7 B2 — this driver was the lone one of 9 that clobbered the file,
    silently deleting other drivers' pending candidates and resetting ids.)"""
    if not candidates:
        return None
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CANDIDATES_DIR / f"{book}_ch_{chapter:03d}.json"

    existing: list[dict] = []
    if out_path.is_file():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8")).get("candidates", [])
        except Exception:
            existing = []

    new_dicts = [candidate_to_dict(c, len(existing) + i) for i, c in enumerate(candidates, start=1)]
    payload = {
        "book": book,
        "chapter": chapter,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_candidates": len(existing) + len(new_dicts),
        "candidates": existing + new_dicts,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def run_xref_for_book(book: str, *, min_confidence: float = 0.6, min_votes: int = 30, top_n: int = 3) -> dict:
    """Iterate the TSK cache for one book, run CrossRefDetector per
    verse, write per-chapter candidates JSON. Returns stats."""
    tsk = sources.tsk()
    detector = CrossRefDetector(min_votes=min_votes, top_n=top_n)
    raw = tsk._raw if hasattr(tsk, "_raw") else None
    if raw is None:
        # Fall back to direct cache load
        with open(TSK_PATH) as f:
            raw = json.load(f)

    book_data = raw.get(book, {})
    chapters_processed = 0
    candidates_written = 0
    files_written = 0

    for chapter_str, verses in book_data.items():
        try:
            chapter = int(chapter_str)
        except ValueError:
            continue
        chapters_processed += 1
        chapter_candidates = []
        for verse_str in verses:
            try:
                verse = int(verse_str)
            except ValueError:
                continue
            # CrossRefDetector ignores verse_text (param underscored)
            cands = detector.detect(book, chapter, verse, _verse_text="")
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
        "chapters_processed": chapters_processed,
        "candidates_written": candidates_written,
        "files_written": files_written,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Run CrossRefDetector at scale via direct TSK iteration.")
    p.add_argument("--books", help="comma-separated list of books (default: all in TSK)")
    p.add_argument("--min-confidence", type=float, default=0.6)
    p.add_argument("--min-votes", type=int, default=30, help="TSK community-vote threshold (default 30)")
    p.add_argument("--top-n", type=int, default=3, help="top N references per verse (default 3)")
    args = p.parse_args()

    # Determine book list
    with open(TSK_PATH) as f:
        tsk_raw = json.load(f)
    if args.books:
        books = args.books.split(",")
    else:
        books = sorted(tsk_raw.keys())
    # Defense-in-depth: canonicalize legacy codes so a re-run is self-correcting
    # even if a source JSON is ever rebuilt with legacy keys (mint-7 ★BUGCLUSTER).
    books = [sources._normalize_book_code(b) for b in books]

    print(
        f"Running CrossRefDetector across {len(books)} books "
        f"(min-conf={args.min_confidence}, min-votes={args.min_votes}, "
        f"top-n={args.top_n})"
    )
    print()

    total_chapters = 0
    total_candidates = 0
    total_files = 0
    for book in books:
        stats = run_xref_for_book(
            book,
            min_confidence=args.min_confidence,
            min_votes=args.min_votes,
            top_n=args.top_n,
        )
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
    print(f"Files written under: {CANDIDATES_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

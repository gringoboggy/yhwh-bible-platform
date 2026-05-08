#!/usr/bin/env python3
"""Phase χ.7 — Nave's Topical at-scale driver.

Mirrors ``scripts/run_xref_at_scale.py``: bypasses prospect.py's
EPUB-build dependency by iterating the cached Nave's index directly.
NaveTopicalDetector ignores verse text — it only needs (book, chapter,
verse) tuples — so this composition is faithful to the existing pipeline,
just with a different iteration source.

Output: writes candidates JSON files in the same prospect.py format to
``content/candidates/<book>_ch_<NNN>.json``. ``scripts/promote.py`` and
``scripts/batch_promote_xrefs.py --kind topic-nave`` work unchanged.

Usage:
    python3 scripts/run_naves_at_scale.py                # all books
    python3 scripts/run_naves_at_scale.py --books gen,exo
    python3 scripts/run_naves_at_scale.py --top-n 3      # tighter cap
    python3 scripts/run_naves_at_scale.py --min-topics 2 # only multi-topic
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.detectors import NaveTopicalDetector  # noqa: E402
from scripts.core import sources  # noqa: E402

CANDIDATES_DIR = REPO_ROOT / "content" / "candidates"
NAVES_PATH = REPO_ROOT / "content" / "sources" / "naves_topical.json"

GREEN = "\033[92m"
DIM = "\033[2m"
RESET = "\033[0m"


def candidate_to_dict(c, idx: int) -> dict:
    """Mirror of prospect.py's candidate_to_dict — same shape so
    promote.py / batch_promote_xrefs.py work unchanged."""
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
    """Same output format as prospect.write_queue — promote.py works
    on these unchanged. If a candidates file already exists for this
    chapter, we *append* rather than overwrite — multiple at-scale
    drivers (xref, hebrew, naves) need to coexist on the same chapter
    file. New candidates get fresh ids; existing candidates are kept
    as-is (their `status` field carries any prior promotion record).
    """
    if not candidates:
        return None
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CANDIDATES_DIR / f"{book}_ch_{chapter:03d}.json"

    existing: list[dict] = []
    if out_path.is_file():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8")).get(
                "candidates", []
            )
        except Exception:
            existing = []

    new_dicts = [candidate_to_dict(c, len(existing) + i)
                 for i, c in enumerate(candidates, start=1)]
    payload = {
        "book": book,
        "chapter": chapter,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_candidates": len(existing) + len(new_dicts),
        "candidates": existing + new_dicts,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    return out_path


def run_naves_for_book(book: str, *, min_confidence: float = 0.5,
                        top_n: int = 5, min_topics: int = 1) -> dict:
    """Iterate the Nave's reverse index for one book, run
    NaveTopicalDetector per verse, write per-chapter candidates JSON.
    Returns stats."""
    naves = sources.naves_topical()
    detector = NaveTopicalDetector(top_n=top_n, min_topics=min_topics)
    book_data = naves._verses.get(book, {})

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
    p = argparse.ArgumentParser(
        description="Run NaveTopicalDetector at scale via direct Nave's iteration."
    )
    p.add_argument("--books",
                    help="comma-separated list of books (default: all in Nave's)")
    p.add_argument("--min-confidence", type=float, default=0.5)
    p.add_argument("--top-n", type=int, default=5,
                    help="top N topics per verse (default 5)")
    p.add_argument("--min-topics", type=int, default=1,
                    help="skip verses with fewer than N topics (default 1)")
    args = p.parse_args()

    if not NAVES_PATH.is_file():
        print(
            f"Nave's Topical not cached at {NAVES_PATH.relative_to(REPO_ROOT)}.\n"
            f"Run: python3 scripts/fetch_sources.py\n"
            f"(Or drop a pre-built JSON of the documented shape into\n"
            f" {NAVES_PATH.relative_to(REPO_ROOT)}.)",
            file=sys.stderr,
        )
        return 2

    naves = sources.naves_topical()
    if args.books:
        books = args.books.split(",")
    else:
        books = sorted(naves._verses.keys())

    print(f"Running NaveTopicalDetector across {len(books)} books "
          f"(min-conf={args.min_confidence}, top-n={args.top_n}, "
          f"min-topics={args.min_topics})")
    print(f"Source: {naves.n_topics:,} topics · {naves.n_refs:,} refs")
    print()

    total_chapters = 0
    total_candidates = 0
    total_files = 0
    for book in books:
        stats = run_naves_for_book(
            book,
            min_confidence=args.min_confidence,
            top_n=args.top_n,
            min_topics=args.min_topics,
        )
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
    print(f"TOTAL: {len(books)} books · {total_chapters} chapters · "
          f"{total_candidates} candidates · {total_files} candidate files")
    print(f"Files written under: {CANDIDATES_DIR}")
    print(f"Next step:  python3 scripts/batch_promote_xrefs.py "
          f"--kind topic-nave")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Track C — Torrey's New Topical Textbook at-scale driver.

Mirrors ``scripts/run_naves_at_scale.py``: bypasses prospect.py's EPUB-build
dependency by iterating the cached Torrey index directly. TorreyTopicalDetector
ignores verse text — it only needs (book, chapter, verse) tuples — so this
composition is faithful to the existing pipeline, just with a different
iteration source.

Output: writes candidates JSON files in the same prospect.py format to
``content/candidates/<book>_ch_<NNN>.json``. ``scripts/promote.py`` and
``scripts/batch_promote_xrefs.py --kind topic-torrey`` work unchanged.

Usage:
    python3 scripts/run_torrey_at_scale.py                # write all candidates
    python3 scripts/run_torrey_at_scale.py --dry-run      # count only, no writes
    python3 scripts/run_torrey_at_scale.py --books gen,exo
    python3 scripts/run_torrey_at_scale.py --top-n 3      # tighter cap
    python3 scripts/run_torrey_at_scale.py --min-topics 2 # only multi-topic verses
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import sources  # noqa: E402
from scripts.core.detectors import TorreyTopicalDetector  # noqa: E402
from scripts.core.at_scale_base import DIM, GREEN, RESET, candidate_to_dict  # noqa: E402

CANDIDATES_DIR = REPO_ROOT / "content" / "candidates"
TORREY_PATH = REPO_ROOT / "content" / "sources" / "torrey_topical.json"


def write_queue(book: str, chapter: int, candidates: list) -> Path | None:
    """Same output format as prospect.write_queue — promote.py works on these
    unchanged. Appends to any existing chapter file so multiple at-scale drivers
    (xref, hebrew, naves, torrey) coexist on the same chapter; new candidates get
    fresh ids, existing ones keep their prior `status`."""
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


def naves_covered_verses() -> set[tuple[str, str, str]]:
    """(book, chapter_str, verse_str) keys already carrying a Nave's topical
    note — used by --net-new to keep Torrey to the verses Nave's leaves
    uncovered (the user's 'capped' scope; ~88% of Torrey overlaps Nave's)."""
    naves = sources.naves_topical()
    return {
        (book, ch, vs) for book, chapters in naves._verses.items() for ch, verses in chapters.items() for vs in verses
    }


def run_torrey_for_book(
    book: str,
    *,
    min_confidence: float = 0.5,
    top_n: int = 5,
    min_topics: int = 1,
    dry_run: bool = False,
    net_new: bool = False,
    overlap_only: bool = False,
    naves_keys: set[tuple[str, str, str]] | None = None,
) -> dict:
    """Iterate the Torrey reverse index for one book, run TorreyTopicalDetector
    per verse, write per-chapter candidates JSON (skipped when dry_run).
    ``net_new`` skips verses Nave's already covers; ``overlap_only`` keeps only
    those (the exact complement — the two partition the full set). Returns stats."""
    torrey = sources.torrey_topical()
    detector = TorreyTopicalDetector(top_n=top_n, min_topics=min_topics)
    book_data = torrey._verses.get(book, {})
    if (net_new or overlap_only) and naves_keys is None:
        naves_keys = naves_covered_verses()

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
            if naves_keys is not None:
                covered = (book, chapter_str, verse_str) in naves_keys
                if net_new and covered:
                    continue
                if overlap_only and not covered:
                    continue
            cands = detector.detect(book, chapter, verse, _verse_text="")
            for c in cands:
                if c.confidence >= min_confidence:
                    chapter_candidates.append(c)
        if chapter_candidates:
            candidates_written += len(chapter_candidates)
            if dry_run:
                files_written += 1
            else:
                out = write_queue(book, chapter, chapter_candidates)
                if out:
                    files_written += 1
    return {
        "book": book,
        "chapters_processed": chapters_processed,
        "candidates_written": candidates_written,
        "files_written": files_written,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Run TorreyTopicalDetector at scale via direct Torrey iteration.")
    p.add_argument("--books", help="comma-separated list of books (default: all in Torrey)")
    p.add_argument("--min-confidence", type=float, default=0.5)
    p.add_argument("--top-n", type=int, default=5, help="top N topics per verse (default 5)")
    p.add_argument("--min-topics", type=int, default=1, help="skip verses with fewer than N topics (default 1)")
    p.add_argument("--dry-run", action="store_true", help="count candidates, write nothing")
    p.add_argument(
        "--net-new",
        action="store_true",
        help="only emit candidates for verses Nave's Topical does NOT already cover",
    )
    p.add_argument(
        "--overlap-only",
        action="store_true",
        help="only emit candidates for verses Nave's Topical DOES cover (exact complement of --net-new)",
    )
    args = p.parse_args()
    if args.net_new and args.overlap_only:
        p.error("--net-new and --overlap-only are mutually exclusive")

    if not TORREY_PATH.is_file():
        print(
            f"Torrey's New Topical not cached at {TORREY_PATH.relative_to(REPO_ROOT)}.\n"
            f"Run: python3 scripts/extract_torrey_ccel.py",
            file=sys.stderr,
        )
        return 2

    torrey = sources.torrey_topical()
    books = args.books.split(",") if args.books else sorted(torrey._verses.keys())
    # Defense-in-depth: canonicalize legacy codes (mint-7 ★BUGCLUSTER).
    books = [sources._normalize_book_code(b) for b in books]
    naves_keys = naves_covered_verses() if (args.net_new or args.overlap_only) else None

    mode = "DRY-RUN (no writes)" if args.dry_run else "writing candidates"
    scope = " · NET-NEW vs Nave's" if args.net_new else (" · OVERLAP-ONLY vs Nave's" if args.overlap_only else "")
    print(
        f"Running TorreyTopicalDetector across {len(books)} books — {mode}{scope} "
        f"(min-conf={args.min_confidence}, top-n={args.top_n}, min-topics={args.min_topics})"
    )
    print(f"Source: {torrey.n_topics:,} topics · {torrey.n_refs:,} refs")
    print()

    total_chapters = 0
    total_candidates = 0
    total_files = 0
    for book in books:
        stats = run_torrey_for_book(
            book,
            min_confidence=args.min_confidence,
            top_n=args.top_n,
            min_topics=args.min_topics,
            dry_run=args.dry_run,
            net_new=args.net_new,
            overlap_only=args.overlap_only,
            naves_keys=naves_keys,
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
    if not args.dry_run:
        print(f"Files written under: {CANDIDATES_DIR}")
        print("Next step:  python3 scripts/batch_promote_xrefs.py --kind topic-torrey")
    return 0


if __name__ == "__main__":
    sys.exit(main())

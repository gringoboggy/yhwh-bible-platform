#!/usr/bin/env python3
"""Phase χ.0 — Kenyon textual-criticism at-scale driver.

Walks the local PD-source ``content/sources/kenyon_textcrit.txt``
(F.G. Kenyon, *Our Bible and the Ancient Manuscripts*, 1895) once,
extracts every verse reference the regex resolves to a known canonical
book code, and writes per-chapter candidate JSON files in the same
format as ``prospect.py`` produces. From there, ``scripts/promote.py``
and ``scripts/batch_promote_xrefs.py --kind text-witness`` work
unchanged.

Mirrors ``scripts/run_xref_at_scale.py`` (χ.6) and
``scripts/run_naves_at_scale.py`` (χ.7) — same output format, same
bypass of ``prospect.py``'s EPUB-build dependency, same idempotent
re-run semantics.

Usage:
    python3 scripts/run_kenyon_at_scale.py                 # all books
    python3 scripts/run_kenyon_at_scale.py --books mat,gen
    python3 scripts/run_kenyon_at_scale.py --max-per-verse 1

Output:
    content/candidates/<book>_ch_<NNN>.json  (per-chapter, appended
    when an existing file is present; merged on (id) with the
    existing entries to keep idempotency).
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.detectors import KenyonReferenceDetector  # noqa: E402
from scripts.core.at_scale_base import DIM, GREEN, RESET, candidate_to_dict  # noqa: E402
from scripts.core.notes_io import atomic_write  # noqa: E402

CANDIDATES_DIR = REPO_ROOT / "content" / "candidates"


def write_queue(book: str, chapter: int, candidates: list) -> Path | None:
    """Append the χ.0 candidates to any existing per-chapter file
    rather than overwriting — preserves prior detector output (TSK,
    Hebrew, Greek, Nave's). The merge is dedup'd on (verse, kind,
    body-hash) so re-running is idempotent."""
    if not candidates:
        return None
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CANDIDATES_DIR / f"{book}_ch_{chapter:03d}.json"

    existing: list[dict] = []
    if out_path.is_file():
        try:
            with out_path.open(encoding="utf-8") as f:
                payload = json.load(f)
            existing = payload.get("candidates", [])
        except (OSError, json.JSONDecodeError):
            existing = []

    seen = {(c.get("verse"), c.get("kind"), c.get("draft_body")) for c in existing}
    new_dicts = []
    # Continue ID numbering from where existing left off; the NNN
    # suffix in candidate IDs is chapter-file-wide sequential, not
    # per-verse scoped, so a fresh start at 1 would collide with
    # already-promoted entries.
    next_idx = len(existing) + 1
    for c in candidates:
        d = candidate_to_dict(c, next_idx)
        key = (d["verse"], d["kind"], d["draft_body"])
        if key in seen:
            continue
        seen.add(key)
        new_dicts.append(d)
        next_idx += 1

    if not new_dicts:
        return None  # idempotent: nothing new to add

    # Re-index ALL candidates so the chapter-wide id NNN stays unique.
    # This also repairs any prior collision a too-naive merge might
    # have produced — id is opaque from promote.py's perspective.
    all_cands = existing + new_dicts
    for i, d in enumerate(all_cands, start=1):
        d["id"] = f"{book}-{chapter}-{d.get('verse', 0)}-{i:03d}"
    payload = {
        "book": book,
        "chapter": chapter,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_candidates": len(all_cands),
        "candidates": all_cands,
    }
    atomic_write(out_path, json.dumps(payload, indent=2, ensure_ascii=False))
    return out_path


def main() -> int:
    p = argparse.ArgumentParser(
        description=("Run KenyonReferenceDetector at scale via direct iteration of the cached Kenyon source text."),
    )
    p.add_argument("--books", help="comma-separated list of books to keep (default: all books found in Kenyon)")
    p.add_argument(
        "--max-per-verse",
        type=int,
        default=1,
        help="cap candidates per verse (default 1; raise to see every Kenyon mention)",
    )
    args = p.parse_args()

    book_filter = None
    if args.books:
        book_filter = {b.strip() for b in args.books.split(",") if b.strip()}

    detector = KenyonReferenceDetector(
        max_candidates_per_verse=args.max_per_verse,
    )
    print(
        f"Running KenyonReferenceDetector "
        f"(max-per-verse={args.max_per_verse}"
        f"{', books=' + ','.join(sorted(book_filter)) if book_filter else ''})"
    )
    print()

    # Group by (book, chapter)
    by_chapter: dict[tuple[str, int], list] = {}
    for c in detector.iter_all_candidates():
        if book_filter and c.book not in book_filter:
            continue
        by_chapter.setdefault((c.book, c.chapter), []).append(c)

    total_candidates = 0
    total_files = 0
    by_book: dict[str, int] = {}
    for (book, chapter), cands in sorted(by_chapter.items()):
        out = write_queue(book, chapter, cands)
        if out:
            total_files += 1
            total_candidates += len(cands)
            by_book[book] = by_book.get(book, 0) + len(cands)

    for book in sorted(by_book.keys()):
        n = by_book[book]
        print(f"  {GREEN}✓{RESET} {book:5s} {n:3d} candidates")

    print()
    print(f"TOTAL: {len(by_book)} books · {total_candidates} new candidates · {total_files} candidate files updated")
    print(f"Files written under: {CANDIDATES_DIR}")
    print()
    print(f"{DIM}Next: python3 scripts/batch_promote_xrefs.py --kind text-witness{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

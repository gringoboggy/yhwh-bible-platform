#!/usr/bin/env python3
"""
prospect.py — Generate candidate notes for a book / chapter.

Runs every detector in ``scripts/core/detectors.py`` against every verse
in the target range, collects the candidates, filters against existing
notes, and writes a review queue to ``content/candidates/<book>_ch_<n>.json``.

Pair with ``scripts/promote.py`` to walk the queue and convert candidates
into real notes in ``content/notes/<book>.py``.

The detectors are pluggable — extending the system means adding a
detector class to ``detectors.py`` and registering it in
``ALL_DETECTORS``. No prospect.py changes required.

Examples:
    python3 scripts/prospect.py gen 3
        # candidates for Genesis chapter 3
    python3 scripts/prospect.py gen --all-chapters
        # all 50 chapters of Genesis
    python3 scripts/prospect.py gen 3 --only lang-hebrew
        # only Hebrew-word candidates
    python3 scripts/prospect.py gen 3 --min-confidence 0.7
        # higher-confidence candidates only
    python3 scripts/prospect.py gen 3 --no-dedupe
        # don't filter against existing notes (re-suggest already-noted anchors)

Exit codes:
    0  candidates written (or queue already complete)
    1  no verses found in the target range
    2  setup error (unknown book, missing sources)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402
from scripts.core.detectors import ALL_DETECTORS, Candidate  # noqa: E402
from scripts.core.sources import SourceMissingError  # noqa: E402
from scripts.find_anchor import find_verse_text, load_existing_anchors  # noqa: E402

EPUB_DIR = REPO_ROOT / "epub_working"
NOTES_DIR = REPO_ROOT / "content" / "notes"
CANDIDATES_DIR = REPO_ROOT / "content" / "candidates"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ----------------------------------------------------------------------
# Verse iteration
# ----------------------------------------------------------------------


def discover_verses(book: str, chapter: int) -> list[tuple[int, str]]:
    """Return [(verse_num, verse_text), ...] for a chapter, in order."""
    out = []
    # Chapters cap at ~150 verses (Psalm 119); cheap to scan upper bound.
    for v in range(1, 200):
        text, _ = find_verse_text(EPUB_DIR, book, chapter, v)
        if text is None:
            # Stop scanning at first missing verse — verse numbering is
            # contiguous within a chapter.
            break
        out.append((v, text))
    return out


def discover_chapters(book: str) -> list[int]:
    """Return list of chapter numbers found in the EPUB for this book."""
    pat = re.compile(rf'\bid="v-{re.escape(book)}-(\d+)-1"')
    found = set()
    for f in sorted(EPUB_DIR.glob("*.html")):
        text = f.read_text(encoding="utf-8")
        for m in pat.finditer(text):
            found.add(int(m.group(1)))
    return sorted(found)


# ----------------------------------------------------------------------
# Dedupe against existing notes
# ----------------------------------------------------------------------


# Map kind families: a `word`-kind legacy note covers the same ground as
# a `lang-hebrew` candidate, etc. Used for dedupe.
LEGACY_TO_CATEGORY = {
    "word": "lang",
    "comm": "comm",
    "source": "text",
    "parallel": "xref",
}


def _category_of(kind_code: str, kinds_index: dict) -> str | None:
    """Return the category for a kind code, looking through legacy and new."""
    if kind_code in LEGACY_TO_CATEGORY:
        return LEGACY_TO_CATEGORY[kind_code]
    k = kinds_index.get(kind_code)
    return k.get("category") if k else None


def is_duplicate(c: Candidate, existing: list, kinds_index: dict) -> bool:
    """Return True if a candidate is likely already covered by an existing note.

    Heuristics (any of these triggers a dedupe):
      * same anchor + same kind-category on the same verse
      * empty anchor + same kind-category on the same verse (no good
        signal to differentiate; assume the existing note covers it)
    """
    cand_cat = _category_of(c.kind, kinds_index)
    if not cand_cat:
        return False
    cand_anchor_l = (c.anchor or "").strip().lower()

    for _tsuffix, tanchor, tkind, _ttitle in existing:
        ex_cat = _category_of(tkind, kinds_index)
        if ex_cat != cand_cat:
            continue
        ex_anchor_l = (tanchor or "").strip().lower()
        # Same anchor (case-insensitive)
        if cand_anchor_l and ex_anchor_l and cand_anchor_l == ex_anchor_l:
            return True
        # Both empty anchors + same category → likely duplicate
        if not cand_anchor_l and not ex_anchor_l:
            return True
    return False


# ----------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------


def candidate_to_dict(c: Candidate, idx: int) -> dict:
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


def write_queue(book: str, chapter: int, candidates: list[Candidate]) -> Path:
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CANDIDATES_DIR / f"{book}_ch_{chapter:03d}.json"
    payload = {
        "book": book,
        "chapter": chapter,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_candidates": len(candidates),
        "candidates": [candidate_to_dict(c, i) for i, c in enumerate(candidates, start=1)],
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


# ----------------------------------------------------------------------
# Per-chapter pipeline
# ----------------------------------------------------------------------


def prospect_chapter(
    book: str,
    chapter: int,
    *,
    only_kinds: set | None,
    min_confidence: float,
    dedupe: bool,
    kinds_index: dict,
) -> dict:
    """Generate, filter, and write candidates for one chapter. Returns stats."""
    verses = discover_verses(book, chapter)
    if not verses:
        return {"verses": 0, "candidates": 0, "deduped": 0, "out_path": None}

    # Instantiate detectors; tolerate ones whose source data isn't cached
    # yet (e.g. Nave's Topical before fetch_sources.py has run). The
    # detector framework expects all-or-nothing instantiation; this
    # softens that so `prospect.py` keeps working when newer detectors'
    # sources are absent. Phase χ.7.
    detectors = []
    for d in ALL_DETECTORS:
        try:
            detectors.append(d())
        except SourceMissingError as e:
            print(
                f"  {YELLOW}! detector {d.__name__} skipped — source not cached: {e}{RESET}",
                file=sys.stderr,
            )

    notes_path = NOTES_DIR / f"{book}.py"
    raw_candidates: list[Candidate] = []

    for v, vtext in verses:
        for det in detectors:
            if only_kinds and det.kind not in only_kinds:
                continue
            try:
                cands = det.detect(book, chapter, v, vtext)
            except Exception as e:
                print(
                    f"  {YELLOW}! detector {det.name} crashed on {book} {chapter}:{v}: {e}{RESET}",
                    file=sys.stderr,
                )
                cands = []
            for c in cands:
                if c.confidence < min_confidence:
                    continue
                raw_candidates.append(c)

    # Dedupe against existing notes (per verse, since existing-note loading
    # is verse-scoped).
    final: list[Candidate] = []
    deduped = 0
    if dedupe:
        # Group by verse to limit existing-note lookups
        per_verse: dict[int, list] = {}
        for c in raw_candidates:
            per_verse.setdefault(c.verse, []).append(c)
        for v, cs in per_verse.items():
            existing = load_existing_anchors(notes_path, chapter, v)
            for c in cs:
                if is_duplicate(c, existing, kinds_index):
                    deduped += 1
                    continue
                final.append(c)
    else:
        final = raw_candidates

    # Stable sort by (verse, -confidence) so highest-conf appears first per verse.
    final.sort(key=lambda c: (c.verse, -c.confidence))

    out_path = write_queue(book, chapter, final)
    return {
        "verses": len(verses),
        "candidates": len(final),
        "deduped": deduped,
        "out_path": out_path,
    }


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Generate candidate notes from PD reference corpora.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("book", help="book code (gen, exo, ...)")
    p.add_argument("chapter", nargs="?", type=int, help="chapter number")
    p.add_argument(
        "--all-chapters",
        action="store_true",
        help="run on every chapter found in the book",
    )
    p.add_argument(
        "--only",
        help="comma-separated kind codes to include (e.g. lang-hebrew,xref-citation)",
    )
    p.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="confidence floor (0.0–1.0; default 0.0)",
    )
    p.add_argument(
        "--no-dedupe",
        action="store_true",
        help="skip filtering against existing notes",
    )
    args = p.parse_args()

    if not args.all_chapters and args.chapter is None:
        p.error("specify chapter, or pass --all-chapters")

    # Validate book (raises KeyError on unknown book)
    try:
        config.get_book(args.book)
    except KeyError:
        print(f"{RED}✗ unknown book {args.book!r}{RESET}", file=sys.stderr)
        sys.exit(2)

    # Sources available?
    try:
        # Touch loaders early — fail fast with a clean message
        from scripts.core import sources

        sources.strongs_hebrew()
        sources.tsk()
    except SourceMissingError as e:
        print(f"{RED}✗ {e}{RESET}", file=sys.stderr)
        sys.exit(2)

    only_kinds = set(args.only.split(",")) if args.only else None
    kinds_index = config.kinds_by_code()

    if args.all_chapters:
        chapters = discover_chapters(args.book)
        if not chapters:
            print(
                f"{RED}✗ no chapters found for {args.book!r} in {EPUB_DIR}{RESET}",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        chapters = [args.chapter]

    print(f"\n{BOLD}prospect{RESET} {DIM}book={args.book} chapters={len(chapters)}{RESET}")

    total_candidates = 0
    total_deduped = 0
    for ch in chapters:
        stats = prospect_chapter(
            args.book,
            ch,
            only_kinds=only_kinds,
            min_confidence=args.min_confidence,
            dedupe=not args.no_dedupe,
            kinds_index=kinds_index,
        )
        if stats["verses"] == 0:
            print(f"  {YELLOW}–{RESET} ch {ch}: no verses found")
            continue
        rel = stats["out_path"].relative_to(REPO_ROOT)
        print(
            f"  {GREEN}✓{RESET} ch {ch:>3}: "
            f"{stats['candidates']:>3} candidates "
            f"({stats['verses']} verses, {stats['deduped']} deduped) "
            f"{DIM}→ {rel}{RESET}"
        )
        total_candidates += stats["candidates"]
        total_deduped += stats["deduped"]

    print(
        f"\n  {BOLD}{total_candidates}{RESET} candidates queued · "
        f"{DIM}{total_deduped} deduped against existing notes{RESET}\n"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()

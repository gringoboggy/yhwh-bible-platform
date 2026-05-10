#!/usr/bin/env python3
"""Phase χ-AI-notes — LLM-backed first-draft note generator driver.

Walks KJV verses (in canonical book order), invokes
``AINoteDetector`` per verse, writes per-chapter candidate JSON in
the same format ``prospect.py`` produces. From there,
``scripts/promote.py`` and
``scripts/batch_promote_xrefs.py --kind comm-ai`` work unchanged.

Mirrors ``scripts/run_ai_xrefs_at_scale.py`` (χ-AI-xrefs); same
cost guards (``--dry-run``, ``--max-verses``, ``--confirm-cost``)
because this is the second χ phase backed by a paid API rather
than a free cached source.

Usage:
    python3 scripts/run_ai_notes_at_scale.py --dry-run             # cost estimate
    python3 scripts/run_ai_notes_at_scale.py --books jhn --max-verses 50
    python3 scripts/run_ai_notes_at_scale.py --max-verses 5000 --confirm-cost
    python3 scripts/run_ai_notes_at_scale.py --books rom,gal,heb --max-verses 500

Cost model (``claude-haiku-4-5``, prompt-cached system prompt at
1h TTL). The system prompt is ~5800 tokens (estimated via
chars/4) — well over Haiku 4.5's 4096-token minimum cacheable
prefix. Output averages ~250 tokens for an emitted draft, ~80
tokens for a `{"note": null}` skip.

    Per verse with cache hit: 5800 read tokens × $0.10/1M
                              + ~80 user tokens × $1.00/1M
                              + ~250 output tokens × $5.00/1M
                              ≈ $0.002 per verse.
    First call pays cache-write premium (5800 × $2.00/1M ≈ $0.012).
    1h TTL refreshes mid-run; budget ~$0.012 per cache rewrite.

    ~$0.20 per 100 verses → $10 per 5K verses → $62 per full
    31K-verse pass.

Re-baseline by running 50-100 verses with --dry-run-after-first to
confirm cache_read_input_tokens > 0; ``client.last_usage`` exposes
the per-call telemetry.

Output:
    content/candidates/<book>_ch_<NNN>.json — per-chapter,
    merge-not-clobber against prior detector output (TSK / Hebrew /
    Greek / Nave / Kenyon / xref-thematic).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.detectors import AINoteDetector  # noqa: E402
from scripts.core.sources import (  # noqa: E402
    DEFAULT_AI_NOTE_MODEL,
    AnthropicNoteClient,
    SourceMissingError,
)
from scripts.core import translations  # noqa: E402
from scripts.core import config  # noqa: E402

CANDIDATES_DIR = REPO_ROOT / "content" / "candidates"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
RESET = "\033[0m"

# Cost per verse, in USD. Derived from the χ-AI-notes spec's cost
# model (5800-token cached system prompt at 1h TTL + ~80 user tokens
# + ~250 output tokens). Lighter output schema than χ-AI-xrefs
# (single note instead of up to 3 proposals), so per-verse cost is
# ~10% lower.
COST_PER_VERSE_USD = 0.0020

# Above this, the driver requires --confirm-cost to proceed. Same
# threshold as χ-AI-xrefs — keeps an accidental full-corpus pass
# from costing $62 by surprise.
CONFIRM_COST_THRESHOLD = 200


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
    """Append ``comm-ai`` candidates to any existing per-chapter file
    (merge-not-clobber). Existing non-``comm-ai`` candidates (TSK /
    Hebrew / Greek / Nave / Kenyon / xref-thematic) are preserved
    verbatim. Same merge contract as ``run_ai_xrefs_at_scale.py``."""
    if not candidates:
        return None
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CANDIDATES_DIR / f"{book}_ch_{chapter:03d}.json"
    existing_candidates = []
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            existing_candidates = [c for c in existing.get("candidates", []) if c.get("kind") != "comm-ai"]
        except Exception:
            pass
    new_dicts = [candidate_to_dict(c, i) for i, c in enumerate(candidates, start=len(existing_candidates) + 1)]
    all_candidates = existing_candidates + new_dicts
    payload = {
        "book": book,
        "chapter": chapter,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_candidates": len(all_candidates),
        "candidates": all_candidates,
    }
    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return out_path


def iter_target_verses(books: list[str], max_verses: int):
    """Yield ``(book, chapter, verse, verse_text)`` tuples in
    canonical book order, capped at ``max_verses`` total. Skips
    books that aren't present in the KJV translation data. Mirrors
    ``run_ai_xrefs_at_scale.iter_target_verses`` — kept separate to
    allow per-driver targeting filters in the future (e.g. "only
    verses with < N existing notes")."""
    yielded = 0
    for book in books:
        if yielded >= max_verses:
            return
        if not translations.has_book("kjv", book):
            continue
        try:
            book_meta = config.get_book(book)
            n_chapters = book_meta.get("chapters", 50) if book_meta else 50
        except KeyError:
            n_chapters = 50
        for chapter in range(1, n_chapters + 1):
            if yielded >= max_verses:
                return
            verses = translations.get_chapter("kjv", book, chapter)
            if not verses:
                continue
            for verse_num, verse_text in verses:
                if yielded >= max_verses:
                    return
                yield (book, chapter, verse_num, verse_text)
                yielded += 1


def run_ai_notes(
    books: list[str],
    *,
    max_verses: int,
    min_confidence: float,
    model: str,
    tradition: str | None = None,
    detector_factory=None,
) -> dict:
    """Pure-function core of the driver. ``detector_factory`` is
    injectable for tests (default constructs a real
    ``AINoteDetector(client=AnthropicNoteClient(model=...))``).

    Returns a stats dict with:
        verses_processed, candidates_written, files_written,
        per_book{book: {verses, candidates}}.
    """
    if detector_factory is None:

        def detector_factory():  # noqa: E306
            return AINoteDetector(
                client=AnthropicNoteClient(model=model),
                min_confidence=min_confidence,
                tradition=tradition,
            )

    detector = detector_factory()

    # Group candidates by (book, chapter) for one merge-and-write pass
    # per chapter. Same shape as run_ai_xrefs_at_scale.run_ai_xrefs.
    verses_processed = 0
    by_chapter: dict[tuple[str, int], list] = {}
    per_book: dict[str, dict] = {}

    for book, chapter, verse_num, verse_text in iter_target_verses(
        books,
        max_verses,
    ):
        verses_processed += 1
        per_book.setdefault(book, {"verses": 0, "candidates": 0})
        per_book[book]["verses"] += 1
        cands = detector.detect(book, chapter, verse_num, verse_text)
        if cands:
            by_chapter.setdefault((book, chapter), []).extend(cands)
            per_book[book]["candidates"] += len(cands)

    candidates_written = 0
    files_written = 0
    for (book, chapter), cands in sorted(by_chapter.items()):
        out = write_queue(book, chapter, cands)
        if out:
            files_written += 1
            candidates_written += len(cands)

    return {
        "verses_processed": verses_processed,
        "candidates_written": candidates_written,
        "files_written": files_written,
        "per_book": per_book,
    }


def estimate_cost(n_verses: int) -> float:
    return n_verses * COST_PER_VERSE_USD


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=("Run AINoteDetector at scale via direct KJV iteration with cost guards."),
    )
    p.add_argument(
        "--books",
        help=("comma-separated list of canonical 3-letter book codes (default: all books with KJV data)"),
    )
    p.add_argument(
        "--max-verses",
        type=int,
        default=100,
        help=(
            "hard cap on API calls per run (default 100). The "
            "driver refuses to run more than "
            f"{CONFIRM_COST_THRESHOLD} verses without "
            "--confirm-cost."
        ),
    )
    p.add_argument(
        "--min-confidence",
        type=float,
        default=0.65,
        help=("drop AI drafts below this confidence (default 0.65)"),
    )
    p.add_argument(
        "--model",
        default=DEFAULT_AI_NOTE_MODEL,
        help=(f"Anthropic model id (default: {DEFAULT_AI_NOTE_MODEL})"),
    )
    p.add_argument(
        "--tradition",
        default=None,
        help=(
            "optional edition tradition tag (e.g. eastern-orthodox, "
            "lutheran-confessional) — passed to the model so drafts "
            "are written in that tradition's idiom and concerns. "
            "Default: no tradition tag (general)."
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help=("print projected verse count and cost, then exit. No API calls made."),
    )
    p.add_argument(
        "--confirm-cost",
        action="store_true",
        help=(f"explicit acknowledgement of cost; required when --max-verses > {CONFIRM_COST_THRESHOLD}."),
    )
    return p.parse_args(argv)


def resolve_books(books_arg: str | None) -> list[str]:
    if books_arg:
        return [b.strip() for b in books_arg.split(",") if b.strip()]
    # Default: every KJV book in canonical order from books.yaml.
    canonical = list(config.books_by_code().keys())
    kjv_dir = REPO_ROOT / "content" / "translations" / "kjv"
    available = {p.stem for p in kjv_dir.glob("*.py")}
    return [b for b in canonical if b in available]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    books = resolve_books(args.books)

    # Pre-count target verses so the cost estimate is accurate (and
    # the confirm-cost guard fires before any API call).
    n_verses = sum(1 for _ in iter_target_verses(books, args.max_verses))
    cost_usd = estimate_cost(n_verses)

    tradition_str = f", tradition={args.tradition}" if args.tradition else ""
    print(
        f"Target: {n_verses} verses across {len(books)} books "
        f"(model={args.model}, min-conf={args.min_confidence}{tradition_str})."
    )
    print(f"Projected cost: ~${cost_usd:.2f} USD (@ ${COST_PER_VERSE_USD:.5f}/verse).")
    print()

    if args.dry_run:
        print(f"{DIM}--dry-run: nothing written; no API calls made.{RESET}")
        return 0

    if args.max_verses > CONFIRM_COST_THRESHOLD and not args.confirm_cost:
        print(
            f"{RED}REFUSING:{RESET} --max-verses ({args.max_verses}) "
            f"exceeds the {CONFIRM_COST_THRESHOLD}-verse "
            f"confirm-cost threshold."
        )
        print(f"  Re-run with {YELLOW}--confirm-cost{RESET} to proceed, or lower --max-verses.")
        print(f"  Projected spend: ${cost_usd:.2f} USD.")
        return 1

    # Construct the client once (validates the SDK + key); fail
    # cleanly if the source is missing.
    try:
        client = AnthropicNoteClient(model=args.model)
    except SourceMissingError as e:
        print(f"{RED}REFUSING:{RESET} {e}")
        return 1

    def detector_factory():
        return AINoteDetector(
            client=client,
            min_confidence=args.min_confidence,
            tradition=args.tradition,
        )

    stats = run_ai_notes(
        books,
        max_verses=args.max_verses,
        min_confidence=args.min_confidence,
        model=args.model,
        tradition=args.tradition,
        detector_factory=detector_factory,
    )

    print()
    for book in sorted(stats["per_book"].keys()):
        s = stats["per_book"][book]
        marker = GREEN + "✓" + RESET if s["candidates"] else DIM + "-" + RESET
        print(f"  {marker} {book:5s} {s['verses']:4d} verses → {s['candidates']:3d} candidates")

    print()
    print(
        f"TOTAL: {stats['verses_processed']} verses processed · "
        f"{stats['candidates_written']} candidates · "
        f"{stats['files_written']} candidate files updated"
    )
    print(f"Files written under: {CANDIDATES_DIR}")
    print()
    print(f"{DIM}Next: python3 scripts/batch_promote_xrefs.py --kind comm-ai{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

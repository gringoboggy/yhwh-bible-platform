#!/usr/bin/env python3
"""Phase χ-AI-xrefs — LLM-backed thematic cross-reference driver.

Walks KJV verses (in canonical book order), invokes
``AIXrefDetector`` per verse, writes per-chapter candidate JSON in
the same format ``prospect.py`` produces. From there,
``scripts/promote.py`` and
``scripts/batch_promote_xrefs.py --kind xref-thematic`` work
unchanged.

Mirrors ``scripts/run_greek_at_scale.py`` (χ.1) and
``scripts/run_kenyon_at_scale.py`` (χ.0); adds cost guards because
this is the first χ phase backed by a paid API rather than a free
cached source.

Usage:
    python3 scripts/run_ai_xrefs_at_scale.py --dry-run             # cost estimate
    python3 scripts/run_ai_xrefs_at_scale.py --books jhn --max-verses 50
    python3 scripts/run_ai_xrefs_at_scale.py --max-verses 5000 --confirm-cost
    python3 scripts/run_ai_xrefs_at_scale.py --books rom,gal,heb --max-verses 500

Cost model (``claude-haiku-4-5``, prompt-cached system prompt at 1h TTL).
The system prompt was expanded 2026-05-08 to ≥4096 tokens (Haiku 4.5's
minimum cacheable prefix — under that, ``cache_control`` silently does
nothing). Padded prompt is ~5000 tokens; output averages ~350 tokens
across 3 proposals.

    Per verse with cache hit: 5000 read tokens × $0.10/1M
                              + ~50 user tokens × $1.00/1M
                              + ~350 output tokens × $5.00/1M
                              ≈ $0.0023 per verse.
    First call pays cache-write premium (5000 × $2.00/1M ≈ $0.01).
    1h TTL refreshes mid-run; budget ~$0.01 per cache rewrite.

    ~$0.23 per 100 verses → $11.50 per 5K verses → $72 per full
    31K-verse pass (vs the broken-cache state which would have been
    ~$37 — caching wasn't actually engaging on the prior 700-token
    prompt despite the cache_control marker).

Re-baseline by running 50-100 verses with --dry-run-after-first to
confirm cache_read_input_tokens > 0; ``client.last_usage`` exposes
the per-call telemetry.

Output:
    content/candidates/<book>_ch_<NNN>.json — per-chapter, merge-not-
    clobber against prior detector output (TSK / Hebrew / Greek /
    Nave / Kenyon).
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.detectors import AIXrefDetector  # noqa: E402
from scripts.core.sources import (  # noqa: E402
    DEFAULT_AI_XREF_MODEL,
    SourceMissingError,
    AnthropicXrefClient,
)
from scripts.core.parallel import parallel_map  # noqa: E402
from scripts.core.work_cache import WorkCache  # noqa: E402
from scripts.core.at_scale_base import (  # noqa: E402
    DIM,
    GREEN,
    RED,
    RESET,
    YELLOW,
    candidate_to_dict,
    iter_target_verses,
    resolve_books,
)
from scripts.core.notes_io import atomic_write  # noqa: E402

CANDIDATES_DIR = REPO_ROOT / "content" / "candidates"

# Cost per verse, in USD. Re-baselined 2026-05-08 after the
# system-prompt padding fix (5000 cached tokens at 1h TTL +
# ~50 user tokens + ~350 output tokens). The prior 0.00092
# estimate assumed caching worked on a 700-token prompt — it
# didn't (Haiku 4.5 minimum cacheable prefix is 4096 tokens).
# Real cost on a full 31K-verse pass is ~$72; under a strict
# budget, dial back top_n in propose_xrefs() or use --max-verses.
COST_PER_VERSE_USD = 0.0023

# Above this, the driver requires --confirm-cost to proceed. Keeps an
# accidental full-corpus pass from costing $28 by surprise.
CONFIRM_COST_THRESHOLD = 200


def write_queue(book: str, chapter: int, candidates: list) -> Path | None:
    """Append ``xref-thematic`` candidates to any existing per-chapter
    file (merge-not-clobber). Existing non-``xref-thematic`` candidates
    (TSK / Hebrew / Greek / Nave / Kenyon) are preserved verbatim."""
    if not candidates:
        return None
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CANDIDATES_DIR / f"{book}_ch_{chapter:03d}.json"
    existing_candidates = []
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            existing_candidates = [c for c in existing.get("candidates", []) if c.get("kind") != "xref-thematic"]
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
    atomic_write(out_path, json.dumps(payload, indent=2, ensure_ascii=False))
    return out_path


def run_ai_xrefs(
    books: list[str],
    *,
    max_verses: int,
    min_confidence: float,
    top_n: int,
    model: str,
    detector_factory=None,
    workers: int = 1,
) -> dict:
    """Pure-function core of the driver. ``detector_factory`` is
    injectable for tests (default constructs a real
    ``AIXrefDetector(client=AnthropicXrefClient(model=...))``).

    Returns a stats dict with:
        verses_processed, candidates_written, files_written,
        per_book{book: {verses, candidates}}.
    """
    if detector_factory is None:

        def detector_factory():  # noqa: E306
            return AIXrefDetector(
                client=AnthropicXrefClient(model=model),
                top_n=top_n,
                min_confidence=min_confidence,
            )

    detector = detector_factory()

    # Gather targets up front so the per-verse API calls can run in parallel
    # (they're I/O-bound). `parallel_map` returns results in INPUT order, so
    # the aggregation below is deterministic and byte-identical to the serial
    # path regardless of `workers`. workers<=1 keeps the original behavior.
    targets = list(iter_target_verses(books, max_verses))
    verses_processed = len(targets)

    def _work(t):
        book, chapter, verse_num, verse_text = t
        return (book, chapter, detector.detect(book, chapter, verse_num, verse_text))

    if workers and workers > 1:
        processed = parallel_map(_work, targets, workers=workers)
    else:
        processed = [_work(t) for t in targets]

    # Group candidates by (book, chapter) for one merge-and-write pass
    # per chapter.
    by_chapter: dict[tuple[str, int], list] = {}
    per_book: dict[str, dict] = {}
    for book, chapter, cands in processed:
        per_book.setdefault(book, {"verses": 0, "candidates": 0})
        per_book[book]["verses"] += 1
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
        description=("Run AIXrefDetector at scale via direct KJV iteration with cost guards."),
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
        default=0.7,
        help=("drop AI proposals below this confidence (default 0.7)"),
    )
    p.add_argument(
        "--top-n",
        type=int,
        default=3,
        help=("ask the model for up to N proposals per verse (default 3)"),
    )
    p.add_argument(
        "--model",
        default=DEFAULT_AI_XREF_MODEL,
        help=(f"Anthropic model id (default: {DEFAULT_AI_XREF_MODEL})"),
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
    p.add_argument(
        "--workers",
        type=int,
        default=1,
        help=(
            "parallel API workers (default 1 = serial). The calls are "
            "I/O-bound; 4-8 gives a large wall-clock speedup. Keep modest to "
            "respect rate limits (the SDK retries 429s)."
        ),
    )
    p.add_argument(
        "--cache",
        default=None,
        help=(
            "path to a SQLite response cache. Re-runs skip verses whose text "
            "(and model/prompt) are unchanged, paying only for what changed."
        ),
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    books = resolve_books(args.books)

    # Pre-count target verses so the cost estimate is accurate (and
    # the confirm-cost guard fires before any API call).
    n_verses = sum(1 for _ in iter_target_verses(books, args.max_verses))
    cost_usd = estimate_cost(n_verses)

    print(
        f"Target: {n_verses} verses across {len(books)} books "
        f"(model={args.model}, top-n={args.top_n}, "
        f"min-conf={args.min_confidence})."
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

    # Construct the detector once (validates the SDK + key); fail
    # cleanly if the source is missing. Opt-in response cache is shared
    # across all workers (thread-safe).
    cache = WorkCache(args.cache) if args.cache else None
    try:
        client = AnthropicXrefClient(model=args.model, cache=cache)
    except SourceMissingError as e:
        print(f"{RED}REFUSING:{RESET} {e}")
        return 1

    def detector_factory():
        return AIXrefDetector(
            client=client,
            top_n=args.top_n,
            min_confidence=args.min_confidence,
        )

    stats = run_ai_xrefs(
        books,
        max_verses=args.max_verses,
        min_confidence=args.min_confidence,
        top_n=args.top_n,
        model=args.model,
        detector_factory=detector_factory,
        workers=args.workers,
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
    print(f"{DIM}Next: python3 scripts/batch_promote_xrefs.py --kind xref-thematic{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

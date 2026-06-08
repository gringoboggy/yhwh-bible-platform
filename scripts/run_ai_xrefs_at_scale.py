#!/usr/bin/env python3
"""Phase χ-AI-xrefs — LLM-backed thematic cross-reference driver.

Walks KJV verses (in canonical book order), invokes
``AIXrefDetector`` per verse, writes per-chapter candidate JSON in
the same format ``prospect.py`` produces. From there,
``scripts/promote.py`` and
``scripts/batch_promote_xrefs.py --kind xref-thematic`` work
unchanged.

Thin CLI over ``at_scale_base.run_ai_detector`` / ``build_ai_arg_parser`` /
``run_ai_driver_main`` (v0.1.0 STAGE A): the shared aggregation core + parser +
cost-guarded ``main()`` live in ``scripts/core/at_scale_base.py``; this file
supplies the AIXrefDetector / AnthropicXrefClient classes + the xref-thematic
labels.

Usage:
    python3 scripts/run_ai_xrefs_at_scale.py --dry-run             # cost estimate
    python3 scripts/run_ai_xrefs_at_scale.py --books jhn --max-verses 50
    python3 scripts/run_ai_xrefs_at_scale.py --max-verses 5000 --confirm-cost
    python3 scripts/run_ai_xrefs_at_scale.py --books rom,gal,heb --max-verses 500

Cost model (``claude-haiku-4-5``, prompt-cached system prompt at 1h TTL): the
~5000-token padded prompt is ≥ Haiku 4.5's 4096-token minimum cacheable prefix;
~$0.0023 per verse with a cache hit → ~$0.23 per 100 verses → $72 per full
31K-verse pass. Under a strict budget, dial back ``--top-n`` or ``--max-verses``.
``client.last_usage`` exposes the per-call telemetry for re-baselining.

Output:
    content/candidates/<book>_ch_<NNN>.json — per-chapter, merge-not-
    clobber against prior detector output (TSK / Hebrew / Greek /
    Nave / Kenyon).
"""

from __future__ import annotations
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.detectors import AIXrefDetector  # noqa: E402
from scripts.core.sources import (  # noqa: E402
    DEFAULT_AI_XREF_MODEL,
    AnthropicXrefClient,
)
from scripts.core.at_scale_base import (  # noqa: E402
    append_candidates,
    build_ai_arg_parser,
    run_ai_detector,
    run_ai_driver_main,
)

CANDIDATES_DIR = REPO_ROOT / "content" / "candidates"

# Cost per verse, in USD. Re-baselined 2026-05-08 after the system-prompt padding
# fix (5000 cached tokens at 1h TTL + ~50 user + ~350 output tokens). Real cost on
# a full 31K-verse pass is ~$72; under a strict budget, dial back top_n or
# --max-verses.
COST_PER_VERSE_USD = 0.0023

# Above this, the driver requires --confirm-cost to proceed (keeps an accidental
# full-corpus pass from costing $72 by surprise).
CONFIRM_COST_THRESHOLD = 200


def write_queue(book: str, chapter: int, candidates: list) -> Path | None:
    """Append candidates to the per-chapter JSON via the shared
    ``at_scale_base.append_candidates`` (status-preserving dedup; mint-10)."""
    return append_candidates(CANDIDATES_DIR / f"{book}_ch_{chapter:03d}.json", book, chapter, candidates)


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
    """Pure-function core of the driver. ``detector_factory`` is injectable for
    tests (default constructs a real ``AIXrefDetector(client=AnthropicXrefClient
    (model=...))``). Delegates aggregation to ``at_scale_base.run_ai_detector``;
    reads ``CANDIDATES_DIR`` at call time so tests can monkeypatch it."""
    if detector_factory is None:

        def detector_factory():  # noqa: E306
            return AIXrefDetector(
                client=AnthropicXrefClient(model=model),
                top_n=top_n,
                min_confidence=min_confidence,
            )

    return run_ai_detector(
        books,
        max_verses=max_verses,
        detector_factory=detector_factory,
        candidates_dir=CANDIDATES_DIR,
        workers=workers,
    )


def estimate_cost(n_verses: int) -> float:
    return n_verses * COST_PER_VERSE_USD


def main(argv: list[str] | None = None) -> int:
    parser = build_ai_arg_parser(
        detector_label="AIXrefDetector",
        min_confidence_default=0.7,
        confirm_threshold=CONFIRM_COST_THRESHOLD,
        model_default=DEFAULT_AI_XREF_MODEL,
        extra_args=(
            (
                ("--top-n",),
                {
                    "type": int,
                    "default": 3,
                    "help": "ask the model for up to N proposals per verse (default 3)",
                },
            ),
        ),
    )
    args = parser.parse_args(argv)

    def make_client(model, cache):
        return AnthropicXrefClient(model=model, cache=cache)

    def make_detector_factory(client, args):
        def detector_factory():
            return AIXrefDetector(
                client=client,
                top_n=args.top_n,
                min_confidence=args.min_confidence,
            )

        return detector_factory

    def format_target_line(args, n_verses, n_books):
        return (
            f"Target: {n_verses} verses across {n_books} books "
            f"(model={args.model}, top-n={args.top_n}, min-conf={args.min_confidence})."
        )

    return run_ai_driver_main(
        args,
        cost_per_verse=COST_PER_VERSE_USD,
        confirm_threshold=CONFIRM_COST_THRESHOLD,
        candidates_dir=CANDIDATES_DIR,
        kind_hint="xref-thematic",
        make_client=make_client,
        make_detector_factory=make_detector_factory,
        format_target_line=format_target_line,
    )


if __name__ == "__main__":
    sys.exit(main())

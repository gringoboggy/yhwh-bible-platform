#!/usr/bin/env python3
"""Phase χ-AI-notes — LLM-backed first-draft note generator driver.

Walks KJV verses (in canonical book order), invokes
``AINoteDetector`` per verse, writes per-chapter candidate JSON in
the same format ``prospect.py`` produces. From there,
``scripts/promote.py`` and
``scripts/batch_promote_xrefs.py --kind comm-ai`` work unchanged.

Thin CLI over ``at_scale_base.run_ai_detector`` / ``build_ai_arg_parser`` /
``run_ai_driver_main`` (v0.1.0 STAGE A): this and ``run_ai_xrefs_at_scale.py``
were near-clones, differing only by the detector/client classes, the per-driver
extra arg (``--tradition`` vs ``--top-n``), ``COST_PER_VERSE`` (0.0020/0.0023),
the ``--min-confidence`` default (0.65/0.7), and the ``--kind`` promote hint. The
shared aggregation core + parser + cost-guarded ``main()`` live in
``scripts/core/at_scale_base.py``; this file supplies the AINoteDetector /
AnthropicNoteClient classes + the comm-ai labels.

Usage:
    python3 scripts/run_ai_notes_at_scale.py --dry-run             # cost estimate
    python3 scripts/run_ai_notes_at_scale.py --books jhn --max-verses 50
    python3 scripts/run_ai_notes_at_scale.py --max-verses 5000 --confirm-cost
    python3 scripts/run_ai_notes_at_scale.py --books rom,gal,heb --max-verses 500

Cost model (``claude-haiku-4-5``, prompt-cached system prompt at
1h TTL): ~$0.002 per verse with a cache hit → ~$0.20 per 100 verses
→ $62 per full 31K-verse pass. ``client.last_usage`` exposes the
per-call telemetry for re-baselining.

Output:
    content/candidates/<book>_ch_<NNN>.json — per-chapter,
    merge-not-clobber against prior detector output (TSK / Hebrew /
    Greek / Nave / Kenyon / xref-thematic).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.detectors import AINoteDetector  # noqa: E402
from scripts.core.sources import (  # noqa: E402
    DEFAULT_AI_NOTE_MODEL,
    AnthropicNoteClient,
)
from scripts.core.at_scale_base import (  # noqa: E402
    append_candidates,
    build_ai_arg_parser,
    run_ai_detector,
    run_ai_driver_main,
)

CANDIDATES_DIR = REPO_ROOT / "content" / "candidates"

# Cost per verse, in USD. Derived from the χ-AI-notes spec's cost model
# (5800-token cached system prompt at 1h TTL + ~80 user + ~250 output tokens).
# Lighter output schema than χ-AI-xrefs (single note, not up to 3 proposals).
COST_PER_VERSE_USD = 0.0020

# Above this, the driver requires --confirm-cost to proceed (keeps an accidental
# full-corpus pass from costing $62 by surprise).
CONFIRM_COST_THRESHOLD = 200


def write_queue(book: str, chapter: int, candidates: list) -> Path | None:
    """Append candidates to the per-chapter JSON via the shared
    ``at_scale_base.append_candidates`` (status-preserving dedup; mint-10)."""
    return append_candidates(CANDIDATES_DIR / f"{book}_ch_{chapter:03d}.json", book, chapter, candidates)


def run_ai_notes(
    books: list[str],
    *,
    max_verses: int,
    min_confidence: float,
    model: str,
    tradition: str | None = None,
    detector_factory=None,
    workers: int = 1,
) -> dict:
    """Pure-function core of the driver. ``detector_factory`` is injectable for
    tests (default constructs a real ``AINoteDetector(client=AnthropicNoteClient
    (model=...))``). Delegates aggregation to ``at_scale_base.run_ai_detector``;
    reads ``CANDIDATES_DIR`` at call time so tests can monkeypatch it."""
    if detector_factory is None:

        def detector_factory():  # noqa: E306
            return AINoteDetector(
                client=AnthropicNoteClient(model=model),
                min_confidence=min_confidence,
                tradition=tradition,
            )

    return run_ai_detector(
        books,
        max_verses=max_verses,
        detector_factory=detector_factory,
        candidates_dir=CANDIDATES_DIR,
        workers=workers,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_ai_arg_parser(
        detector_label="AINoteDetector",
        min_confidence_default=0.65,
        confirm_threshold=CONFIRM_COST_THRESHOLD,
        model_default=DEFAULT_AI_NOTE_MODEL,
        extra_args=(
            (
                ("--tradition",),
                {
                    "default": None,
                    "help": (
                        "optional edition tradition tag (e.g. eastern-orthodox, "
                        "evangelical-reformed) — passed to the model so drafts "
                        "are written in that tradition's idiom and concerns. "
                        "Default: no tradition tag (general)."
                    ),
                },
            ),
        ),
    )
    args = parser.parse_args(argv)

    def make_client(model, cache):
        return AnthropicNoteClient(model=model, cache=cache)

    def make_detector_factory(client, args):
        def detector_factory():
            return AINoteDetector(
                client=client,
                min_confidence=args.min_confidence,
                tradition=args.tradition,
            )

        return detector_factory

    def format_target_line(args, n_verses, n_books):
        tradition_str = f", tradition={args.tradition}" if args.tradition else ""
        return (
            f"Target: {n_verses} verses across {n_books} books "
            f"(model={args.model}, min-conf={args.min_confidence}{tradition_str})."
        )

    return run_ai_driver_main(
        args,
        cost_per_verse=COST_PER_VERSE_USD,
        confirm_threshold=CONFIRM_COST_THRESHOLD,
        candidates_dir=CANDIDATES_DIR,
        kind_hint="comm-ai",
        make_client=make_client,
        make_detector_factory=make_detector_factory,
        format_target_line=format_target_line,
    )


if __name__ == "__main__":
    sys.exit(main())

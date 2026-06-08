#!/usr/bin/env python3
"""HebrewWord at scale — driver script.

Mirrors scripts/run_greek_at_scale.py but for HebrewWordDetector.
Bypasses prospect.py's EPUB-build dependency by reading verse
text directly from the KJV translation data (which ships with
the project via τ.1).

Output: writes candidates JSON files in the same format as
prospect.py to content/candidates/. From there, scripts/promote.py
or scripts/batch_promote_xrefs.py works unchanged.

Thin CLI over ``at_scale_base.run_word_detector_*`` (v0.1.0 STAGE A): this and
``run_greek_at_scale.py`` were ~95% clones, differing only by the detector
instance, the OT/NT scope predicate, and three label strings. The shared loop +
``main()`` live in ``scripts/core/at_scale_base.py``; this file supplies the
HebrewWordDetector instance + the OT-scope labels.

Usage:
    python3 scripts/run_hebrew_at_scale.py
    python3 scripts/run_hebrew_at_scale.py --books gen,exo
    python3 scripts/run_hebrew_at_scale.py --min-confidence 0.85
"""

from __future__ import annotations
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.detectors import HebrewWordDetector  # noqa: E402
from scripts.core.at_scale_base import (  # noqa: E402
    NT_BOOKS,
    append_candidates,
    run_word_detector_for_book,
    run_word_detector_main,
)

CANDIDATES_DIR = REPO_ROOT / "content" / "candidates"

# Hebrew lexicon is OT-only: a book is in scope iff it's NOT a NT book.
_OUT_OF_SCOPE_REASON = "NT (no Hebrew)"


def _in_scope(book: str) -> bool:
    return book not in NT_BOOKS


def write_queue(book: str, chapter: int, candidates: list) -> Path | None:
    """Append candidates to the per-chapter JSON via the shared
    ``at_scale_base.append_candidates`` (status-preserving dedup; mint-10)."""
    return append_candidates(CANDIDATES_DIR / f"{book}_ch_{chapter:03d}.json", book, chapter, candidates)


def run_hebrew_for_book(book: str, *, min_confidence: float = 0.7) -> dict:
    """Iterate KJV verses for one OT book, run HebrewWordDetector,
    write candidates JSON per chapter. Returns stats. Delegates to the shared
    ``at_scale_base.run_word_detector_for_book``."""
    return run_word_detector_for_book(
        book,
        HebrewWordDetector(),
        in_scope=_in_scope(book),
        out_of_scope_reason=_OUT_OF_SCOPE_REASON,
        min_confidence=min_confidence,
        candidates_dir=CANDIDATES_DIR,
    )


def main() -> int:
    return run_word_detector_main(
        detector=HebrewWordDetector(),
        detector_label="HebrewWordDetector",
        scope_label="OT",
        skipped_scope_label="NT",
        in_scope_predicate=_in_scope,
        out_of_scope_reason=_OUT_OF_SCOPE_REASON,
        candidates_dir=CANDIDATES_DIR,
        repo_root=REPO_ROOT,
    )


if __name__ == "__main__":
    sys.exit(main())

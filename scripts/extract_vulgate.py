"""Clementine Vulgate (latVUC) ingest — shared Vulgate->KJV adapter.
PD: Clementine Vulgate (1592/1598), public domain by age."""

from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from scripts.core.versification import vulgate_to_kjv  # noqa: E402
from scripts.extract_translation import extract  # noqa: E402

TRANSLATION_ID = "vulgate-clementine"


def main() -> int:
    stats = extract(TRANSLATION_ID, remap=vulgate_to_kjv, report=True)
    print(f"{TRANSLATION_ID}: {stats['project_books_emitted']} books, {stats['total_verses']:,} verses")
    return 0


if __name__ == "__main__":
    sys.exit(main())

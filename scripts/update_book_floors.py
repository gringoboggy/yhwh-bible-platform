#!/usr/bin/env python3
"""Regenerate dev/BOOK_FLOORS.json from current corpus counts.

Phase ω.34.1 — companion to TestOmega341BookFloors. Per-book floors
are pinned at 75% of the snapshot count to catch mass-deletion
regressions while leaving slack for legitimate edits. When intended
reductions ship (a publisher removes a kind class, a book gets
restructured into separate files), regenerate the snapshot:

    python scripts/update_book_floors.py

The test enforces ``current >= floor`` for every book; this script
is the only sanctioned way to lower a floor.
"""

from __future__ import annotations

import datetime
import json
import sys
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.core.notes_io import load_notes  # noqa: E402

NOTES_DIR = REPO / "content" / "notes"
FLOOR_PATH = REPO / "dev" / "BOOK_FLOORS.json"
FLOOR_RATIO = 0.75


def compute_floors() -> dict[str, int]:
    floors: dict[str, int] = {}
    for p in sorted(NOTES_DIR.glob("*.py")):
        if p.stem == "__init__":
            continue
        raw = load_notes(p)
        if raw is None:
            # mint-11 #3a: load_notes returns None on a parse failure; len(None)
            # crashed here. Warn + skip so one bad notes file doesn't abort the
            # whole floor recompute (and the failure is visible, not silent).
            warnings.warn(f"update_book_floors: {p.stem} failed to parse — skipping its floor", stacklevel=2)
            continue
        n = len(raw)
        if n == 0:
            floors[p.stem] = 0
        elif n < 20:
            floors[p.stem] = max(1, n - 5)
        else:
            floors[p.stem] = int(n * FLOOR_RATIO)
    return floors


def main() -> int:
    floors = compute_floors()
    payload = {
        "_doc": (
            "Per-book minimum note counts. Pinned at 75% of the "
            "snapshot count for books with >=20 notes; small books get "
            "a -5 cushion; placeholder books with 0 notes carry a 0 "
            "floor. The test in TestOmega341BookFloors enforces "
            "current >= floor for every book. Regenerate via "
            "scripts/update_book_floors.py when planned reductions ship."
        ),
        "_snapshot_date": datetime.date.today().isoformat(),
        "floors": floors,
    }
    FLOOR_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    total = sum(floors.values())
    print(f"wrote {FLOOR_PATH.relative_to(REPO)} — {len(floors)} books; sum_floors={total:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

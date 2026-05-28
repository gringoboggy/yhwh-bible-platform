"""recollate_base_structured.py — Phase A4 driver.

Re-collate the 10 already-transcribed chapters into the new base-structured
format (``*_collation_v2.json``), writing ONLY to the ``collation/`` output
directory. The immutable calibration witnesses + hand goldens are NEVER touched.

Usage (module form — preferred):
    python -m scripts.recollate_base_structured

Usage (import):
    from scripts.recollate_base_structured import run
    result = run()   # -> {"written": [...], "failed": [...]}
"""

from __future__ import annotations

import json
import os
import sys

from scripts.core.manuscript_collation import collate_base_structured
from scripts.core.notes_io import atomic_write

# ── target chapters (A4 spec) ─────────────────────────────────────────────────
DONE_CHAPTERS: list[tuple[str, int]] = [
    ("1ki", 1),
    ("1ki", 2),
    ("1ki", 3),
    ("1ki", 4),
    ("1ki", 5),
    ("1ki", 6),
    ("1sa", 1),
    ("1sa", 3),
    ("1sa", 17),
    ("2sa", 11),
]


def _track(book: str) -> str:
    """Return the manuscript track name for a given book code."""
    return "kings" if book in {"1ki", "2ki"} else "samuel"


def recollate(book: str, chapter: int) -> str:
    """Load witnesses, collate, write atomically; return the output path."""
    track = _track(book)
    cal_dir = os.path.join("content", "manuscript", track, "calibration")
    out_dir = os.path.join("content", "manuscript", track, "collation")

    # Create collation/ dir if missing (samuel/collation/ is new in A4)
    os.makedirs(out_dir, exist_ok=True)

    gg_path = os.path.join(cal_dir, f"{book}{chapter}_witnessGG.json")
    cam_path = os.path.join(cal_dir, f"{book}{chapter}_witnessCAM_hires.json")

    with open(gg_path, encoding="utf-8") as fh:
        gg = json.load(fh)
    with open(cam_path, encoding="utf-8") as fh:
        cam = json.load(fh)

    out = collate_base_structured(gg, cam, book=book, chapter=chapter)

    final_path = os.path.join(out_dir, f"{book}{chapter}_collation_v2.json")
    text = json.dumps(out, ensure_ascii=False, indent=2)
    atomic_write(final_path, text)

    return final_path


def run(targets: list[tuple[str, int]] = DONE_CHAPTERS) -> dict:
    """Re-collate all target chapters; fail-soft per chapter.

    Returns ``{"written": [paths], "failed": [{"ref": str, "error": str}]}``.
    """
    written: list[str] = []
    failed: list[dict] = []

    for book, chapter in targets:
        ref = f"{book}{chapter}"
        try:
            path = recollate(book, chapter)
            written.append(path)
        except Exception as exc:
            failed.append({"ref": ref, "error": str(exc)})

    return {"written": written, "failed": failed}


def main() -> None:
    result = run()
    print(f"Written ({len(result['written'])}):")
    for p in result["written"]:
        print(f"  {p}")
    if result["failed"]:
        print(f"Failed ({len(result['failed'])}):")
        for f in result["failed"]:
            print(f"  {f['ref']}: {f['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

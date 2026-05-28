"""apply_kjv_xref.py — Phase B5 driver.

Fold the KJV cross-reference layer into the 10 already-collated v2 files,
adding a top-level ``kjv_xref`` key and filling ``metrics["kjv_coverage"]``.
The immutable calibration witnesses are NEVER touched.

Usage (module form — preferred):
    python -m scripts.apply_kjv_xref

Usage (import):
    from scripts.apply_kjv_xref import run
    result = run()   # -> {"written": [...], "skipped": [...], "failed": [...]}
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

from scripts.core import geez_kjv_xref
from scripts.core.manuscript_collation import load_kjv_skeleton

# ── target chapters (B5 spec) ─────────────────────────────────────────────────
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


def apply_one(book: str, chapter: int) -> str:
    """Load v2 JSON, inject kjv_xref + kjv_coverage, atomic-rewrite; return path."""
    track = _track(book)
    col_path = os.path.join("content", "manuscript", track, "collation", f"{book}{chapter}_collation_v2.json")

    with open(col_path, encoding="utf-8") as fh:
        col = json.load(fh)

    # Guard: if KJV skeleton is unavailable (Ethiopian-only book), skip gracefully.
    try:
        kjv_rows = load_kjv_skeleton(book, chapter)
    except FileNotFoundError:
        return None  # caller records as skipped

    xref = geez_kjv_xref.build_kjv_xref(col, kjv_rows, book)

    # Augment in-place: add kjv_xref at top level (added last) + fill kjv_coverage.
    col["metrics"]["kjv_coverage"] = geez_kjv_xref.kjv_coverage(xref)
    col["kjv_xref"] = xref

    # Atomic rewrite: write to a temp file in the same directory, then os.replace.
    out_dir = os.path.dirname(os.path.abspath(col_path))
    fd, tmp_path = tempfile.mkstemp(dir=out_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(col, fh, ensure_ascii=False, indent=2)
        os.replace(tmp_path, col_path)
    except Exception:
        # Clean up the temp file if something goes wrong.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    return col_path


def run(targets: list[tuple[str, int]] = DONE_CHAPTERS) -> dict:
    """Apply kjv_xref to all target chapters; fail-soft per chapter.

    Returns ``{"written": [paths], "skipped": [refs], "failed": [{"ref", "error"}]}``.
    """
    written: list[str] = []
    skipped: list[str] = []
    failed: list[dict] = []

    for book, chapter in targets:
        ref = f"{book}{chapter}"
        try:
            path = apply_one(book, chapter)
            if path is None:
                skipped.append(ref)
            else:
                written.append(path)
        except Exception as exc:
            failed.append({"ref": ref, "error": str(exc)})

    return {"written": written, "skipped": skipped, "failed": failed}


def main() -> None:
    result = run()
    print(f"Written ({len(result['written'])}):")
    for p in result["written"]:
        print(f"  {p}")
    if result["skipped"]:
        print(f"Skipped ({len(result['skipped'])}):")
        for s in result["skipped"]:
            print(f"  {s}")
    if result["failed"]:
        print(f"Failed ({len(result['failed'])}):")
        for f in result["failed"]:
            print(f"  {f['ref']}: {f['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

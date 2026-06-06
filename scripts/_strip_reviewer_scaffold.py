#!/usr/bin/env python3
r"""_strip_reviewer_scaffold.py — one-shot RX Phase 1 scaffold remover.

Removes the trailing ``<em>[Reviewer:…]</em>`` editorial-scaffold span that
leaked into 96.8% of shipped note bodies. The scaffold was reviewer guidance
meant for the promote queue, not the reader; its correct home is each
detector's ``reviewer_notes=`` field (fixed separately in detectors.py).

Two passes, both driven by the SAME regex:

  (default) ``content/notes/*.py``  — the note SOURCE. Safe to regex the raw
            ``.py`` because that exact HTML substring occurs only inside body
            string literals (verified: every one of the 88,773 bare
            ``[Reviewer:`` tokens is wrapped in exactly one
            ``<em>[Reviewer:…]</em>`` span with no ``<`` inside).

  --base    ``epub_working/index_split_*.html`` — the built BASE, stripped in
            lockstep so source and base stay byte-consistent.

The reviewer text never contains a ``<`` before its closing ``</em>``, so
``[^<]*`` is a safe, greedy-free body. A leading ``\s*`` swallows the space
that separated the scaffold from the preceding sentence so we don't leave a
trailing space.

Usage::

    python scripts/_strip_reviewer_scaffold.py          # strip content/notes/*.py
    python scripts/_strip_reviewer_scaffold.py --base    # strip epub_working/*.html
    python scripts/_strip_reviewer_scaffold.py --both     # both passes

Idempotent: re-running finds nothing to remove. Writes a file back only if it
changed.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.core import notes_io  # noqa: E402  — crash-safe canonical writes

# The one strip pattern, shared by every consumer (the promote.py defensive
# strip and the lint guard reference this same shape). A leading \s* eats the
# separating whitespace; [^<]* is safe because the reviewer prose has no '<'
# before its own closing </em>.
SCAFFOLD_RE = re.compile(r"\s*<em>\[Reviewer:[^<]*</em>")


def _strip_dir(paths: list[Path], label: str) -> tuple[int, int]:
    """Strip the scaffold from every file in ``paths``. Returns
    ``(files_changed, total_removed)`` and prints per-file counts."""
    files_changed = 0
    total_removed = 0
    for p in sorted(paths):
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            print(f"  SKIP (unreadable): {p.name}")
            continue
        new_text, n = SCAFFOLD_RE.subn("", text)
        if n:
            notes_io.ensure_backup(p)
            notes_io.atomic_write(p, new_text)
            files_changed += 1
            total_removed += n
            print(f"  {p.name}: -{n}")
    print(f"[{label}] files changed: {files_changed}  removed: {total_removed}")
    return files_changed, total_removed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", action="store_true", help="strip epub_working/index_split_*.html")
    ap.add_argument("--both", action="store_true", help="strip both notes source AND base")
    args = ap.parse_args(argv)

    do_notes = args.both or not args.base
    do_base = args.both or args.base

    grand = 0
    if do_notes:
        notes = [p for p in (REPO / "content" / "notes").glob("*.py") if p.name != "__init__.py"]
        print(f"=== content/notes/*.py ({len(notes)} files) ===")
        _, removed = _strip_dir(notes, "notes")
        grand += removed
    if do_base:
        base = list((REPO / "epub_working").glob("index_split_*.html"))
        print(f"=== epub_working/index_split_*.html ({len(base)} files) ===")
        _, removed = _strip_dir(base, "base")
        grand += removed

    print(f"GRAND TOTAL removed: {grand}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

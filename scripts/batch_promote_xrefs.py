#!/usr/bin/env python3
"""Phase χ.6 — Batch-promote all candidate files in one process.

Avoids the per-file subprocess overhead of looping
`promote.py --promote-top N`. Calls promote_candidate() in-process.

Usage:
    python3 scripts/batch_promote_xrefs.py
    python3 scripts/batch_promote_xrefs.py --kind xref-citation
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.promote import promote_candidate  # noqa: E402

CANDIDATES_DIR = REPO_ROOT / "content" / "candidates"


def main() -> int:
    p = argparse.ArgumentParser(description="Batch-promote candidate notes.")
    p.add_argument("--kind", default=None, help="only promote candidates of this kind (e.g. xref-citation)")
    p.add_argument(
        "--max-per-file", type=int, default=None, help="cap how many candidates to promote per file (default: no cap)"
    )
    args = p.parse_args()

    files = sorted(CANDIDATES_DIR.glob("*.json"))
    print(f"Found {len(files)} candidate files. Filter: kind={args.kind!r}")

    total_attempted = 0
    total_promoted = 0
    total_skipped = 0
    total_errors = 0
    files_with_change = 0

    for fp in files:
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ✗ {fp.name}: parse error: {e}")
            total_errors += 1
            continue
        book = data["book"]
        chapter = data["chapter"]
        cands = data["candidates"]
        # Filter by kind if specified
        if args.kind:
            cands = [c for c in cands if c.get("kind") == args.kind]
        # Filter to pending only
        cands = [c for c in cands if c.get("status") == "pending"]
        if args.max_per_file:
            cands = cands[: args.max_per_file]
        if not cands:
            continue
        promoted_in_file = 0
        for c in cands:
            # promote_candidate expects chapter on the candidate dict
            c["chapter"] = chapter
            total_attempted += 1
            try:
                ok, suffix = promote_candidate(book, c)
                if ok:
                    total_promoted += 1
                    promoted_in_file += 1
                else:
                    total_skipped += 1
            except Exception as e:
                print(f"    ✗ {c.get('id', '?')}: {type(e).__name__}: {e}")
                total_errors += 1
        if promoted_in_file > 0:
            files_with_change += 1
            print(f"  ✓ {fp.name}: {promoted_in_file}/{len(cands)} promoted")

    print()
    print(f"Attempted: {total_attempted}")
    print(f"Promoted:  {total_promoted}")
    print(f"Skipped:   {total_skipped} (already exists, or rejected)")
    print(f"Errors:    {total_errors}")
    print(f"Files affected: {files_with_change}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

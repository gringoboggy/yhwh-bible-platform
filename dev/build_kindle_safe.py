#!/usr/bin/env python3
"""Build the Send-to-Kindle-safe catholic-study artifact (K-KIN rounds).

Passes ``target_reader="kindle"`` straight into ``build_one`` (the M1
``--target-reader`` override path: the override folds into a COPY of the
edition record through the one resolver, the cache key hashes the RESOLVED
target, and editions.yaml is never touched — the old byte-backup/flip/restore
dance is retired). The artifact lands on the Desktop with the round's UTC
timestamp:

    .venv/bin/python dev/build_kindle_safe.py [--edition catholic-study]
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--edition", default="catholic-study")
    ap.add_argument("--out-dir", default=str(Path.home() / "Desktop"))
    args = ap.parse_args()

    from scripts.core import config

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out_dir = REPO / "build" / f"kindle_{stamp}"

    from scripts import build_edition as be

    out_dir.mkdir(parents=True, exist_ok=True)
    be.build_one(
        args.edition,
        out_dir,
        f"kindle-{stamp}",
        config.load_kinds(),
        dry_run=False,
        target_reader="kindle",
    )

    built = sorted(out_dir.glob("*.epub"))
    if not built:
        print("no artifact produced", file=sys.stderr)
        return 1
    dest = Path(args.out_dir) / f"Ethiopian_Bible_{args.edition}_kindle-safe_{stamp}.epub"
    dest.write_bytes(built[0].read_bytes())
    print(f"STAGED: {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

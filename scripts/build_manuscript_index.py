#!/usr/bin/env python3
"""Build + query the derived manuscript index (scripts/core/manuscript_index).

A one-shot marathon tool: instead of grepping ~20 witness JSONs, this
builds the in-memory SQLite index over content/manuscript/**/*_witness*.json
and answers cross-chapter questions in one pass.

Usage:
    # Headline + every open marker + per-witness coverage:
    py scripts/build_manuscript_index.py

    # Just one marker class across all chapters:
    py scripts/build_manuscript_index.py --marker damaged

    # Where does a Ge'ez token occur across every witness?
    py scripts/build_manuscript_index.py --token ኪራም

    # Persist the DB for ad-hoc SQL (sqlite3 manuscript.sqlite):
    py scripts/build_manuscript_index.py --db dev/manuscript.sqlite
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import manuscript_index as mi  # noqa: E402

GREEN = "\033[92m"
YELLOW = "\033[93m"
DIM = "\033[2m"
RESET = "\033[0m"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--root", default=None, help="Manuscript root (default: content/manuscript)")
    p.add_argument("--db", default=None, help="Persist the index to this path (default: in-memory)")
    p.add_argument("--marker", default=None, choices=["uncertain", "damaged", "illegible"])
    p.add_argument("--token", default=None, help="Find every exact occurrence of this Ge'ez token")
    p.add_argument("--top", type=int, default=0, help="Show the N most frequent tokens")
    args = p.parse_args(argv)

    root = Path(args.root) if args.root else REPO_ROOT / "content" / "manuscript"
    if not root.exists():
        print(f"manuscript root not found: {root}", file=sys.stderr)
        return 1

    conn = mi.build_from_tree(root, db_path=args.db)

    s = mi.summary(conn)
    print(
        f"{GREEN}Manuscript index{RESET}: {s['witnesses']} witnesses · "
        f"{s['verses']} verses · {s['tokens']} tokens · "
        f"{s['open_markers']} open markers"
    )
    mc = ", ".join(f"{k}={v}" for k, v in sorted(s["marker_counts"].items()))
    print(f"  markers: {mc or '(none)'}")
    print()

    if args.token:
        hits = mi.find_token(conn, args.token)
        print(f"{YELLOW}'{args.token}'{RESET}: {len(hits)} occurrence(s)")
        for h in hits:
            print(f"  {h['witness']} {h['book']}{h['chapter']} v{h['v']} tok#{h['idx']}")
        return 0

    if args.top:
        print(f"Top {args.top} tokens:")
        for r in mi.token_counts(conn, limit=args.top):
            print(f"  {r['n']:4d}  {r['token']}")
        return 0

    print("Per-witness coverage:")
    for r in mi.witness_coverage(conn):
        print(f"  {r['witness']:3s} {r['book']}{r['chapter']:<3} · {r['n_verses']:3d} verses")
    print()

    rows = mi.open_markers(conn, marker=args.marker)
    label = args.marker or "all"
    print(f"Open markers ({label}): {len(rows)}")
    for r in rows:
        note = (r["note"] or "")[:80]
        print(f"  {DIM}{r['witness']} {r['book']}{r['chapter']} v{r['v']} [{r['marker']}]{RESET} {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

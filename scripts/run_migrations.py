#!/usr/bin/env python3
"""Δ.10 — apply pending schema migrations to the corpus_index DB.

Default behavior: opens the cached corpus_index SQLite file (via
`scripts.core.paths.user_data_root() / 'corpus_index.sqlite'`),
ensures the `schema_migrations` table, and applies every migration
whose version is greater than the current HEAD.

Usage::

    python scripts/run_migrations.py             # apply pending
    python scripts/run_migrations.py --dry-run   # show what would apply
    python scripts/run_migrations.py --current   # print current version
    python scripts/run_migrations.py --db <path> # operate on a specific file

Exit codes (match the other audit-script conventions):
    0 — migrations applied (or already at HEAD)
    1 — a migration failed; DB is at the version printed in the error
    2 — invalid args / DB path doesn't exist

The runner is idempotent — running twice in a row applies nothing
the second time. Future Δ-cluster work (Δ.12 FTS5, Δ.13 sqlite-vec)
adds entries to `scripts/core/migrations.MIGRATIONS`; this CLI picks
them up automatically.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import migrate  # noqa: E402
from scripts.core.paths import user_data_root  # noqa: E402


def _default_db_path() -> Path:
    return user_data_root() / "corpus_index.sqlite"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply pending schema migrations to a SQLite DB.")
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Path to the SQLite DB. Defaults to the corpus_index file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print pending migrations without applying them.",
    )
    parser.add_argument(
        "--current",
        action="store_true",
        help="Print the current HEAD version and exit.",
    )
    args = parser.parse_args(argv)

    db_path = args.db if args.db is not None else _default_db_path()
    if not db_path.exists():
        if args.current or args.dry_run:
            # Read-only intent on a non-existent DB → friendly "0".
            print(f"  (no DB at {db_path}; HEAD=0)")
            return 0
        # Apply intent on a non-existent DB → create it.
        db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        if args.current:
            print(f"HEAD={migrate.current_version(conn)} ({db_path})")
            return 0

        pending = migrate.pending(conn)
        if args.dry_run:
            if not pending:
                print(f"  ✓  at HEAD ({db_path})")
                return 0
            print(f"  pending ({len(pending)}) at {db_path}:")
            for version, name in pending:
                print(f"    {version:>4d}  {name}")
            return 0

        if not pending:
            print(f"  ✓  at HEAD ({migrate.current_version(conn)}); nothing to apply")
            return 0

        try:
            applied = migrate.apply_pending(conn)
        except sqlite3.Error as e:
            print(f"  ✗  migration failed: {e}", file=sys.stderr)
            return 1

        print(f"  ✓  applied {len(applied)} migration(s):")
        for version, name in applied:
            print(f"    {version:>4d}  {name}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

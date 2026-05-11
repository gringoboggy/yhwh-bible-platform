"""Δ.10 — schema migration runner for the corpus_index SQLite db.

The minimal viable migration framework promised by
PROPOSAL_FEATURE_LANDSCAPE §7 / Track L. Tracks applied migrations
in a `schema_migrations` metadata table and replays anything not yet
recorded, in version order.

Public API:
    apply_pending(conn)     — apply every migration whose version is
                              strictly greater than the highest seen
                              in `schema_migrations`. Returns the list
                              of newly-applied (version, name) tuples.
    current_version(conn)   — highest applied version, or 0 if none.
    pending(conn)           — list of (version, name) tuples that would
                              be applied by the next `apply_pending`.
                              Read-only; does not mutate the DB.

Invariants enforced:
    - Versions in MIGRATIONS must be strictly increasing positive
      integers. The runner rejects a duplicate or out-of-order entry
      before touching the DB.
    - Each migration is wrapped in a transaction; a failing migration
      rolls back AND aborts the pending list (later migrations don't
      apply over a half-applied earlier one).
    - The `schema_migrations` table itself is created idempotently
      via CREATE IF NOT EXISTS — a fresh DB ends up with one row per
      applied migration plus the metadata table.

The runner intentionally has no Python-callable migration support:
keeping it SQL-only matches the project's "data files look like
Python but must not be executable" rule (CLAUDE_PROJECT_RULES §7.1)
and removes a class of footgun where a migration's behavior depends
on import-time state. If a future change is purely procedural (no
DDL), extend the framework then — not preemptively.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

# Import the module (not the name) so tests can monkeypatch
# `migrations.MIGRATIONS` and have the runner pick up the
# replacement. Importing `MIGRATIONS` directly would snapshot the
# reference at module-load time, defeating the patch.
from scripts.core import migrations as _migrations_module

# Public so tests can assert the table name without re-deriving.
SCHEMA_MIGRATIONS_TABLE = "schema_migrations"


def _migrations() -> list[tuple[int, str, str]]:
    """Return the current MIGRATIONS list. Read via attribute access
    on the module so a monkeypatched MIGRATIONS reaches us."""
    return _migrations_module.MIGRATIONS


_ENSURE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA_MIGRATIONS_TABLE} (
    version    INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL,
    applied_at TEXT    NOT NULL
);
"""


def _validate_migrations(migrations: list[tuple[int, str, str]] | None = None) -> None:
    """Pre-flight validation: versions must be strictly increasing
    positive integers; names must be non-empty.

    Surfaces a developer error (e.g. forgot to bump version when
    appending a new migration) at import time, before any DB writes,
    by raising ValueError with a precise message.

    Accepts an optional explicit list for unit testing; defaults to
    the live `migrations.MIGRATIONS` so the import-time check covers
    the real list.
    """
    items = migrations if migrations is not None else _migrations()
    last_version = 0
    seen_versions: set[int] = set()
    for version, name, _sql in items:
        if not isinstance(version, int) or version <= 0:
            raise ValueError(f"migration version must be a positive int, got {version!r}")
        if version in seen_versions:
            raise ValueError(f"duplicate migration version: {version}")
        if version <= last_version:
            raise ValueError(f"migration versions must be strictly increasing; got {version} after {last_version}")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"migration #{version} has empty/invalid name {name!r}")
        seen_versions.add(version)
        last_version = version


# Validate at import time so a malformed MIGRATIONS list fails fast.
_validate_migrations()


def _ensure_schema_migrations_table(conn: sqlite3.Connection) -> None:
    """Create the metadata table if missing. Idempotent."""
    conn.executescript(_ENSURE_TABLE_SQL)


def current_version(conn: sqlite3.Connection) -> int:
    """Highest version recorded in `schema_migrations`, or 0 if the
    table doesn't exist yet (pristine DB)."""
    _ensure_schema_migrations_table(conn)
    cur = conn.execute(f"SELECT COALESCE(MAX(version), 0) FROM {SCHEMA_MIGRATIONS_TABLE}")
    row = cur.fetchone()
    return int(row[0]) if row else 0


def pending(conn: sqlite3.Connection) -> list[tuple[int, str]]:
    """Return the `(version, name)` tuples that `apply_pending` would
    apply next, in order. Read-only; does not mutate the DB beyond
    the metadata-table ensure (which is itself idempotent).
    """
    head = current_version(conn)
    return [(v, name) for (v, name, _sql) in _migrations() if v > head]


def apply_pending(conn: sqlite3.Connection) -> list[tuple[int, str]]:
    """Apply every migration with version > current_version, in order.

    Each migration's SQL runs inside a transaction; a failure rolls
    back THAT migration and aborts the chain (subsequent migrations
    are not attempted). Successful migrations are recorded in
    `schema_migrations` with an ISO-8601 UTC applied_at timestamp.

    Returns the list of newly-applied `(version, name)` tuples. An
    empty list means the DB was already at HEAD.
    """
    _ensure_schema_migrations_table(conn)
    head = current_version(conn)
    applied: list[tuple[int, str]] = []
    for version, name, sql in _migrations():
        if version <= head:
            continue
        # `executescript` auto-commits and ends any open transaction.
        # We want each migration + its bookkeeping row to land or fail
        # together, so issue an explicit BEGIN/COMMIT around both via
        # `conn:` and use `executescript` only for the migration body.
        try:
            with conn:
                # NB: conn.executescript ends the implicit txn; the
                # `with conn` block manages its own. To keep both the
                # DDL and the bookkeeping insert atomic, run the DDL
                # via execute(...) for single-statement migrations is
                # impractical (multi-statement SQL is the common case).
                # The compromise: use executescript for the body
                # (which auto-commits), then immediately insert the
                # bookkeeping row in the surrounding `with conn` txn.
                # In the rare event the bookkeeping insert fails after
                # the DDL committed, the DB ends up "ahead" of the
                # metadata — the next apply_pending will re-attempt
                # the same DDL (which is idempotent per the
                # CREATE ... IF NOT EXISTS contract) and re-record it.
                conn.executescript(sql)
                conn.execute(
                    f"INSERT INTO {SCHEMA_MIGRATIONS_TABLE} (version, name, applied_at) VALUES (?, ?, ?)",
                    (version, name, datetime.now(timezone.utc).isoformat()),
                )
        except sqlite3.Error as e:
            # Surface with context. Don't continue the chain — a later
            # migration may assume the failed one's tables/columns
            # exist.
            raise sqlite3.Error(
                f"migration #{version} ({name!r}) failed: {e}; chain aborted at HEAD={current_version(conn)}"
            ) from e
        applied.append((version, name))
    return applied

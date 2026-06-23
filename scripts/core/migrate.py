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
from collections.abc import Iterator
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


def _iter_sql_statements(sql: str) -> Iterator[str]:
    """Yield individual executable statements from a migration's SQL.

    ``conn.execute`` runs ONE statement at a time, so a multi-statement
    migration body is split on the statement terminator. Migration SQL
    is project-controlled DDL (``CREATE TABLE/INDEX ... IF NOT EXISTS``,
    ``CREATE VIRTUAL TABLE ... USING fts5(...)``) with no semicolons
    inside string literals, so a plain split is safe; blank chunks and
    comment-only chunks are skipped. (Round-11 gap-7 — replaces the
    auto-committing ``executescript`` so DDL + bookkeeping stay atomic.)
    """
    for chunk in sql.split(";"):
        stripped = chunk.strip()
        if not stripped:
            continue
        non_comment = "\n".join(line for line in stripped.splitlines() if not line.strip().startswith("--")).strip()
        if not non_comment:
            continue
        yield stripped


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
        # Run the migration body AND its bookkeeping INSERT inside ONE
        # explicit transaction so they commit or roll back together.
        # `executescript()` is deliberately avoided: it issues an
        # implicit COMMIT before running, which would leave the DDL
        # committed "ahead" of the ledger if the bookkeeping INSERT (or
        # a later statement) failed. Statements run individually within
        # the BEGIN/COMMIT, so a mid-migration failure rolls the whole
        # migration back — no "DB ahead of ledger" window. (gap-7.)
        try:
            conn.execute("BEGIN")
            for statement in _iter_sql_statements(sql):
                conn.execute(statement)
            conn.execute(
                f"INSERT INTO {SCHEMA_MIGRATIONS_TABLE} (version, name, applied_at) VALUES (?, ?, ?)",
                (version, name, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
        except sqlite3.Error as e:
            # Roll the partial migration back, then surface with
            # context. Don't continue the chain — a later migration may
            # assume the failed one's tables/columns exist.
            conn.rollback()
            raise sqlite3.Error(
                f"migration #{version} ({name!r}) failed: {e}; chain aborted at HEAD={current_version(conn)}"
            ) from e
        applied.append((version, name))
    return applied

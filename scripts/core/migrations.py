"""Δ.10 — schema migration declarations for the corpus_index SQLite db.

Each migration is a `(version, name, sql)` tuple. Versions are strictly
increasing positive integers; the runner (`scripts/core/migrate.py`)
applies any whose version is greater than the highest recorded in the
`schema_migrations` metadata table.

Migrations MUST be idempotent: every `CREATE TABLE` uses
`IF NOT EXISTS`, every `CREATE INDEX` uses `IF NOT EXISTS`. The
corpus_index DB is fully derivable (rebuilt from `content/notes/*.py`
on fingerprint mismatch), so a clean rebuild applies the same
migrations as an incremental upgrade — both must converge.

Adding a new migration:
    1. Append a `(version, name, sql)` tuple to `MIGRATIONS`.
    2. Version must be strictly greater than the previous one
       (the runner enforces this and refuses to apply otherwise).
    3. Name is a short snake_case slug (used in logs +
       `schema_migrations.name`).
    4. SQL can be one statement or many — the runner uses
       `executescript()`. If the change is purely procedural
       (no DDL), use a SQL comment + a callable in a future
       extension; today the runner is SQL-only.

Future migrations sketched in PROPOSAL_FEATURE_LANDSCAPE.md §7
(Track L — database evolution):
    Δ.11 — `PRAGMA journal_mode=WAL` (pragma, not DDL — runner-level
           handling, not a migration entry)
    Δ.12 — FTS5 virtual table for full-text note search
    Δ.13 — sqlite-vec extension + vector-similarity table
    Δ.15 — separate event-log file (`events.jsonl`), not in SQLite
    Δ.16 — encrypted backups (file-level, not SQLite)

The baseline (#1) preserves the schema that lived inline in
`corpus_index._SCHEMA` before Δ.10 — every `CREATE` uses the same
text, so a pre-Δ.10 corpus_index DB upgrades cleanly the first time
the new runner opens it.
"""

from __future__ import annotations

# Migration #1 — baseline `notes` table + 4 indexes (the schema that
# lived inline in scripts/core/corpus_index._SCHEMA pre-Δ.10).
_M1_NOTES_BASELINE = """
CREATE TABLE IF NOT EXISTS notes (
    book_code   TEXT    NOT NULL,
    chapter     INTEGER NOT NULL,
    verse       INTEGER NOT NULL,
    suffix      TEXT    NOT NULL DEFAULT '',
    anchor      TEXT    NOT NULL DEFAULT '',
    kind        TEXT    NOT NULL,
    title       TEXT    NOT NULL DEFAULT '',
    label       TEXT    NOT NULL DEFAULT '',
    body        TEXT    NOT NULL DEFAULT '',
    body_plain  TEXT    NOT NULL DEFAULT '',
    attribution TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_notes_book          ON notes(book_code);
CREATE INDEX IF NOT EXISTS ix_notes_kind          ON notes(kind);
CREATE INDEX IF NOT EXISTS ix_notes_book_chapter  ON notes(book_code, chapter);
CREATE INDEX IF NOT EXISTS ix_notes_book_kind     ON notes(book_code, kind);
"""


# The canonical migration list. Order = application order. Versions
# MUST be strictly increasing; the runner enforces this at apply time.
MIGRATIONS: list[tuple[int, str, str]] = [
    (1, "notes_baseline", _M1_NOTES_BASELINE),
]

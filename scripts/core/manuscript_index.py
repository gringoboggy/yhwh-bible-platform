"""Derived SQLite query layer over the manuscript witness JSONs.

The project already has a mature derived index for the *notes* corpus
(``scripts/core/corpus_index.py`` — FTS5, migrations, rebuild-lock,
xdist-namespaced, 51K rows). This module is the manuscript counterpart:
it indexes ``content/manuscript/**/*_witness*.json`` so the marathon can
ask cross-chapter questions in one query instead of grepping JSON:

  - every OPEN uncertain/damaged/illegible marker across all chapters;
  - marker frequency by class;
  - per-witness verse coverage;
  - where a Ge'ez token occurs across every witness.

Deliberately *lighter* than ``corpus_index``: the witness corpus is ~20
files, so this builds on-demand into an in-memory DB (default) — the
lock / fingerprint-cache / per-worker-namespacing machinery that the
51K-note index needs would be pure over-engineering at this cardinality.
The witness JSONs stay canonical; this index is purely derived.

Stdlib only (``sqlite3``), per CLAUDE_PROJECT_RULES §10.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from collections.abc import Iterable

_SCHEMA = """
CREATE TABLE witness (
    id          INTEGER PRIMARY KEY,
    witness     TEXT NOT NULL,
    book        TEXT NOT NULL,
    chapter     INTEGER NOT NULL,
    source_path TEXT NOT NULL DEFAULT '',
    n_verses    INTEGER NOT NULL DEFAULT 0,
    transcription_notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE verse (
    id          INTEGER PRIMARY KEY,
    witness_id  INTEGER NOT NULL,
    book        TEXT NOT NULL,
    chapter     INTEGER NOT NULL,
    v           INTEGER,
    col         TEXT NOT NULL DEFAULT '',
    line_start  INTEGER NOT NULL DEFAULT 0,
    geez        TEXT NOT NULL DEFAULT '',
    n_tokens    INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE token (
    id          INTEGER PRIMARY KEY,
    verse_id    INTEGER NOT NULL,
    witness     TEXT NOT NULL,
    book        TEXT NOT NULL,
    chapter     INTEGER NOT NULL,
    v           INTEGER,
    idx         INTEGER NOT NULL,
    token       TEXT NOT NULL
);
CREATE TABLE uncertain (
    id          INTEGER PRIMARY KEY,
    verse_id    INTEGER NOT NULL,
    witness     TEXT NOT NULL,
    book        TEXT NOT NULL,
    chapter     INTEGER NOT NULL,
    v           INTEGER,
    token_index INTEGER,
    marker      TEXT NOT NULL,
    note        TEXT NOT NULL DEFAULT ''
);
CREATE INDEX ix_uncertain_marker ON uncertain(marker);
CREATE INDEX ix_token_token ON token(token);
CREATE INDEX ix_verse_loc ON verse(book, chapter, v);
"""


def _is_witness(d: object) -> bool:
    return (
        isinstance(d, dict)
        and isinstance(d.get("verses"), list)
        and d.get("witness") in ("GG", "CAM")
        and "book" in d
        and "chapter" in d
    )


def dedupe_witnesses(witnesses: Iterable[dict], *, prefer_hires: bool = True) -> list[dict]:
    """Keep one record per (book, chapter, witness).

    A chapter sometimes has both a calibrated ``_hires`` transcription and an
    older non-hires one (e.g. ``1sa1_witnessCAM.json`` + ``…_hires.json``);
    indexing both double-counts that chapter. Prefer the hires file (the
    calibrated master). Order-preserving on the kept records.
    """
    best: dict[tuple, dict] = {}
    order: list[tuple] = []
    for d in witnesses:
        if not _is_witness(d):
            continue
        key = (str(d.get("book")), d.get("chapter"), str(d.get("witness")))
        is_hires = "hires" in str(d.get("source_path", "")).lower()
        if key not in best:
            best[key] = d
            order.append(key)
        elif prefer_hires and is_hires and "hires" not in str(best[key].get("source_path", "")).lower():
            best[key] = d  # upgrade the kept record to the hires variant
    return [best[k] for k in order]


def build_index(conn: sqlite3.Connection, witnesses: Iterable[dict]) -> dict:
    """Create the schema and populate it from *witnesses*.

    Each item is a witness dict (optionally carrying a ``source_path`` key
    the file loader attaches). Malformed / non-witness records are skipped
    silently — corruption resilience over strictness, since the JSON files
    remain the trust boundary. Returns a small stats dict.
    """
    conn.executescript(_SCHEMA)
    n_w = n_v = n_t = n_u = 0
    with conn:
        for d in witnesses:
            if not _is_witness(d):
                continue
            book = str(d.get("book"))
            chapter = int(d.get("chapter")) if str(d.get("chapter")).lstrip("-").isdigit() else d.get("chapter")
            witness = str(d.get("witness"))
            verses = d.get("verses") or []
            cur = conn.execute(
                "INSERT INTO witness (witness, book, chapter, source_path, n_verses, transcription_notes) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    witness,
                    book,
                    chapter,
                    str(d.get("source_path", "")),
                    len(verses),
                    str(d.get("transcription_notes", "")),
                ),
            )
            witness_id = cur.lastrowid
            n_w += 1
            for ve in verses:
                if not isinstance(ve, dict):
                    continue
                geez = str(ve.get("geez", "") or "")
                tokens = ve.get("tokens") or []
                v_num = ve.get("v")
                vcur = conn.execute(
                    "INSERT INTO verse (witness_id, book, chapter, v, col, line_start, geez, n_tokens) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        witness_id,
                        book,
                        chapter,
                        v_num,
                        str(ve.get("column", "") or ""),
                        int(ve.get("line_start", 0) or 0),
                        geez,
                        len(tokens),
                    ),
                )
                verse_id = vcur.lastrowid
                n_v += 1
                for i, tok in enumerate(tokens):
                    conn.execute(
                        "INSERT INTO token (verse_id, witness, book, chapter, v, idx, token) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (verse_id, witness, book, chapter, v_num, i, str(tok)),
                    )
                    n_t += 1
                for u in ve.get("uncertain") or []:
                    if not isinstance(u, dict):
                        continue
                    conn.execute(
                        "INSERT INTO uncertain (verse_id, witness, book, chapter, v, token_index, marker, note) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            verse_id,
                            witness,
                            book,
                            chapter,
                            v_num,
                            u.get("token_index"),
                            str(u.get("marker", "") or ""),
                            str(u.get("note", "") or ""),
                        ),
                    )
                    n_u += 1
    return {"witnesses": n_w, "verses": n_v, "tokens": n_t, "uncertain": n_u}


# ----------------------------------------------------------------------
# File loading
# ----------------------------------------------------------------------


def iter_witness_files(root: Path) -> list[Path]:
    """Return every ``*_witness*.json`` under *root* (sorted)."""
    return sorted(root.glob("**/*_witness*.json"))


def load_witnesses(root: Path) -> list[dict]:
    """Load + tag every witness JSON under *root* with its ``source_path``.

    Files that fail to parse or aren't witness-shaped are skipped.
    """
    out: list[dict] = []
    for p in iter_witness_files(root):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if _is_witness(d):
            d["source_path"] = str(p)
            out.append(d)
    return dedupe_witnesses(out)


def build_from_tree(root: Path, *, db_path: str | None = None) -> sqlite3.Connection:
    """Build the index from every witness JSON under *root*.

    Returns an open connection (``:memory:`` unless *db_path* is given).
    """
    conn = sqlite3.connect(db_path or ":memory:")
    conn.row_factory = sqlite3.Row
    build_index(conn, load_witnesses(root))
    return conn


# ----------------------------------------------------------------------
# Queries
# ----------------------------------------------------------------------


def open_markers(conn: sqlite3.Connection, marker: str | None = None) -> list[sqlite3.Row]:
    """Every uncertain/damaged/illegible marker, across all chapters.

    Optional *marker* filters to one class. Ordered for triage:
    book, chapter, verse.
    """
    sql = "SELECT witness, book, chapter, v, token_index, marker, note FROM uncertain"
    args: list = []
    if marker:
        sql += " WHERE marker = ?"
        args.append(marker)
    sql += " ORDER BY book, chapter, v, marker"
    return conn.execute(sql, args).fetchall()


def marker_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """``{marker: count}`` across the whole manuscript corpus."""
    rows = conn.execute("SELECT marker, COUNT(*) FROM uncertain GROUP BY marker").fetchall()
    return {r[0]: r[1] for r in rows}


def witness_coverage(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """One row per witness: witness, book, chapter, n_verses. Ordered."""
    return conn.execute(
        "SELECT witness, book, chapter, n_verses, source_path FROM witness ORDER BY book, chapter, witness"
    ).fetchall()


def find_token(conn: sqlite3.Connection, token: str) -> list[sqlite3.Row]:
    """Every exact occurrence of *token* across all witnesses."""
    return conn.execute(
        "SELECT witness, book, chapter, v, idx, token FROM token WHERE token = ? ORDER BY book, chapter, v, idx",
        (token,),
    ).fetchall()


def token_counts(conn: sqlite3.Connection, *, limit: int = 50) -> list[sqlite3.Row]:
    """Most frequent tokens corpus-wide (collation-variant spotting)."""
    return conn.execute(
        "SELECT token, COUNT(*) AS n FROM token GROUP BY token ORDER BY n DESC, token LIMIT ?",
        (limit,),
    ).fetchall()


def summary(conn: sqlite3.Connection) -> dict:
    """Headline stats for the CLI report."""

    def one(sql):
        return conn.execute(sql).fetchone()[0]

    return {
        "witnesses": one("SELECT COUNT(*) FROM witness"),
        "verses": one("SELECT COUNT(*) FROM verse"),
        "tokens": one("SELECT COUNT(*) FROM token"),
        "open_markers": one("SELECT COUNT(*) FROM uncertain"),
        "marker_counts": marker_counts(conn),
    }

"""
corpus_index.py — derived SQLite index over `content/notes/*.py`.

Phase Δ.1 (2026-05-10) — bold-proposal companion to
`dev/AUDIT_2026-05-10.md` §2. The pre-Δ.1 architecture answered every
aggregate question (matrix, citation index, glossary, attribution
audit, search, coverage, dashboard) by re-walking 87 books × N notes
through 7+ separate `lru_cache` wrappers, each with its own
signature scheme. The matrix endpoint alone composes 5 of these
wrappers. Architectural cost grows with every new aggregate.

Δ.1 introduces a derived SQLite index. The `.py` files stay
canonical (no behavior change to the corpus on disk;
`ast.literal_eval` remains the trust boundary). The index is purely
derived: rebuilt automatically when any `notes/*.py` mtime changes,
sub-second to query, and lives under `<user_data>/cache/`. Every
existing test stays green because the canonical `.py` files don't
change.

This module is **additive**: the existing `lru_cache` aggregates
keep working unchanged. New aggregates use the index. Migration of
existing aggregates is a future phase per consumer.

Schema:

    CREATE TABLE notes (
        book_code   TEXT NOT NULL,
        chapter     INTEGER NOT NULL,
        verse       INTEGER NOT NULL,
        suffix      TEXT NOT NULL DEFAULT '',
        anchor      TEXT NOT NULL DEFAULT '',
        kind        TEXT NOT NULL,
        title       TEXT NOT NULL DEFAULT '',
        label       TEXT NOT NULL DEFAULT '',
        body        TEXT NOT NULL DEFAULT '',
        attribution TEXT NOT NULL DEFAULT ''
    );
    CREATE INDEX ix_notes_book ON notes(book_code);
    CREATE INDEX ix_notes_kind ON notes(kind);
    CREATE INDEX ix_notes_book_chapter ON notes(book_code, chapter);
    CREATE INDEX ix_notes_book_kind ON notes(book_code, kind);

Public API:
    rebuild(*, force=False) -> dict
        Rebuild the index if the corpus fingerprint has changed (or
        always if `force=True`). Returns
        `{rebuilt: bool, fingerprint: str, note_count: int,
        elapsed_ms: float}`.

    connection() -> sqlite3.Connection
        Return a connection to the index. Triggers `rebuild()` on
        first call; thereafter returns the same connection.

    count_by_kind(*, book=None, kinds=None) -> dict[str, int]
    count_by_book(*, kinds=None) -> dict[str, int]
    count_by_kind_and_book(*, kinds=None, books=None) ->
        dict[(book, kind), int]
    fingerprint() -> str
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import html
import os
import re
import sqlite3
import sys
import threading
import time
from pathlib import Path

from . import paths


# Regex helpers for body-text normalization. Defined at module scope
# so they're compiled once across many notes during the build.
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _strip_tags(html_text: str) -> str:
    """Strip HTML tags + decode entities for index search.

    Mirrors `note_search._strip_tags` so search results between the
    file-walk and index-backed paths produce identical excerpts.
    """
    if not html_text:
        return ""
    plain = _TAG_RE.sub(" ", html_text)
    plain = html.unescape(plain)
    return _WS_RE.sub(" ", plain).strip()


# ----------------------------------------------------------------------
# Storage layout
# ----------------------------------------------------------------------
#
# Δ.8 (2026-05-11) — index files are per-process under pytest-xdist.
# Each worker reads `PYTEST_XDIST_WORKER` (a string like "gw0", "gw1",
# ..., or "master" for the controller process) and namespaces its
# corpus.sqlite / corpus.fingerprint / corpus.lock filenames so workers
# never share state on disk.
#
# This eliminates the cross-worker file contention class that
# defeated Δ.4.1 attempts #1-3 — Windows file locks during cached-
# connection swap-out + short-window rebuilds produced widespread
# `PermissionError` failures when 8 workers all hammered the same
# `corpus.sqlite`.  With per-worker storage the contention surface
# vanishes at its root: each worker has its own file, its own lock,
# its own fingerprint cell.
#
# In production (no PYTEST_XDIST_WORKER set), paths revert to the
# canonical names — `corpus.sqlite`, `corpus.fingerprint`,
# `corpus.lock`. Single-process, no namespacing, full
# cross-process-sharing benefit when multiple production callers
# reuse the same on-disk index.


def _xdist_suffix() -> str:
    """Δ.8 — return ``.<worker>`` when running under pytest-xdist,
    empty string otherwise. Each worker subprocess sets
    PYTEST_XDIST_WORKER (e.g. ``gw0``) so we can give each worker
    its own index file. The xdist controller (the test session
    itself) does NOT set the env var, so master-only test runs use
    the canonical names — same as production."""
    worker = os.environ.get("PYTEST_XDIST_WORKER", "")
    return f".{worker}" if worker else ""


def _index_dir() -> Path:
    return paths.user_data_root() / "cache"


def _index_path() -> Path:
    return _index_dir() / f"corpus{_xdist_suffix()}.sqlite"


def _fingerprint_path() -> Path:
    return _index_dir() / f"corpus{_xdist_suffix()}.fingerprint"


def _notes_dir() -> Path:
    # paths.notes_dir() resolves to content/notes; wrap so we can be
    # explicit about which directory the index walks.
    return paths.notes_dir()


# ----------------------------------------------------------------------
# Δ.0 — cross-platform rebuild lock
# ----------------------------------------------------------------------
#
# When multiple processes (xdist workers, dev shell + web server,
# etc.) all want to rebuild the index, they MUST serialize. Without
# the lock they race on `_build_to`'s atomic rename + unlink, and a
# slow reader can find a partial file.
#
# Implementation:
#   POSIX → fcntl.flock(LOCK_EX) on a sentinel file next to the
#           index. Blocks until the lock is acquired.
#   Windows → msvcrt.locking(LK_LOCK) on the same sentinel. The
#             stdlib API requires the file to be opened binary
#             read/write and locks a byte range, but a 1-byte file
#             + 1-byte range works fine.


def _lock_path() -> Path:
    """Path to the rebuild sentinel lockfile. Lives next to the
    index so all index-touching processes converge on the same
    file regardless of how `paths.user_data_root()` is resolved.

    Δ.8 — per-worker namespace under pytest-xdist (one lock per
    worker, since each worker now has its own corpus.sqlite). In
    production (no env var) reverts to the canonical
    ``corpus.lock`` filename so concurrent production processes
    serialize correctly."""
    return _index_dir() / f"corpus{_xdist_suffix()}.lock"


@contextlib.contextmanager
def _acquire_rebuild_lock(*, timeout: float = 30.0):
    """Cross-platform exclusive lock. Blocks until acquired (up to
    `timeout` seconds, then raises TimeoutError). Releases on exit
    even if the wrapped block raises.

    The lockfile is created on first acquire and persists; only the
    OS-level lock state changes per acquire/release cycle. So
    concurrent processes contend on the same kernel object.
    """
    lock_path = _lock_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    # 'a+b' creates if missing, opens at end for both read+write.
    fh = open(lock_path, "a+b")
    try:
        if sys.platform == "win32":
            import msvcrt

            # Loop on LK_NBLCK + sleep; LK_LOCK blocks for ~10s
            # cycles which is awkward to bound by timeout.
            deadline = time.monotonic() + timeout
            while True:
                try:
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            f"timed out acquiring rebuild lock at {lock_path} after {timeout}s"
                        ) from None
                    time.sleep(0.05)
        else:
            import fcntl

            # POSIX flock supports LOCK_NB but no built-in timeout;
            # mirror the busy-wait loop to keep behavior identical.
            deadline = time.monotonic() + timeout
            while True:
                try:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except (BlockingIOError, OSError):
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            f"timed out acquiring rebuild lock at {lock_path} after {timeout}s"
                        ) from None
                    time.sleep(0.05)
        try:
            yield
        finally:
            if sys.platform == "win32":
                import msvcrt

                try:
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            else:
                import fcntl

                try:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
    finally:
        try:
            fh.close()
        except OSError:
            pass


# ----------------------------------------------------------------------
# Fingerprint
# ----------------------------------------------------------------------


def _compute_fingerprint() -> str:
    """SHA-256 over each notes/*.py file's `(stem, size, mtime_ns)`.

    Cheaper than reading every byte; sufficient for change detection
    because mtime + size both flipping without content changing is
    vanishingly unlikely in practice. Distinct from
    `snapshots._corpus_fingerprint` (which IS content-hashed
    post-ω.34) — that's the snapshot integrity hash; this is the
    cache invalidation key. Different cost / different correctness
    target.
    """
    notes_dir = _notes_dir()
    if not notes_dir.is_dir():
        return ""
    h = hashlib.sha256()
    for p in sorted(notes_dir.glob("*.py")):
        try:
            stat = p.stat()
        except OSError:
            h.update(f"{p.stem}:missing\n".encode())
            continue
        h.update(f"{p.stem}:{stat.st_size}:{stat.st_mtime_ns}\n".encode())
    return h.hexdigest()


# Δ.6 — TTL-memoized fingerprint. Without this layer, every
# `connection()` call (and therefore every indexed query) triggered
# `_compute_fingerprint()` which `os.stat()`s every notes/*.py file.
# 87 stat calls per query is fine in cold-cache isolation but defeats
# the parent-level lru_cache on `matrix.compute_matrix()` and
# hammers the test suite under xdist. The TTL bounds staleness:
# in production the worst case is one TTL of stale data after a
# corpus edit (default 1s — acceptable for editorial workflows).
# Tests override to 0 (always recompute) via monkeypatch when they
# care about freshness; the equivalence pins call `invalidate()`
# (which also clears this cache) for the same effect. After Δ.6,
# `connection()` in steady state is a dict lookup + a sqlite query.
_FINGERPRINT_TTL_SEC: float = 1.0
# ω.36 (2026-05-11) — cache cell now carries the notes_dir path it
# was computed against. Tests routinely monkeypatch
# `paths.notes_dir` to a tmp_path; without the path tag, a cached
# fingerprint from a real-corpus test would leak into a synthetic-
# corpus test and return wrong results. Tagging the path lets the
# cache survive across tests within a worker (faster) while still
# auto-invalidating when the resolved path changes (correct).
_FINGERPRINT_CACHE: tuple[float, str, str] | None = None


def _compute_fingerprint_cached() -> str:
    """TTL-memoized variant of `_compute_fingerprint()`.

    When the TTL is non-positive, bypasses the cache (test-friendly
    "never trust the cache" mode). Otherwise returns the cached
    value if it was computed within `_FINGERPRINT_TTL_SEC` of now
    AND the resolved `notes_dir` path matches; recomputes and
    refreshes the cache otherwise.

    The cache is process-local module state; cross-process workers
    each maintain their own. `invalidate()` clears the cache so
    callers that need a guaranteed fresh fingerprint (e.g. after
    explicitly mutating the corpus) can force the next call to
    recompute.

    ω.36 (2026-05-11) — path-tagged cache. The cache cell now
    stores ``(monotonic_at, fingerprint, notes_dir_str)``. A
    cached value is reused only when the resolved notes_dir
    matches the cell's tag, which lets the cache safely survive
    across tests within a worker (the autouse conftest fixture no
    longer needs to clear it per-test). Eliminates the per-test
    87-file stat-walk that had pushed the perf-budget multiplier
    from 1.4 → 3.0 under xdist load.
    """
    global _FINGERPRINT_CACHE
    if _FINGERPRINT_TTL_SEC <= 0:
        return _compute_fingerprint()
    now = time.monotonic()
    notes_dir_str = str(_notes_dir())
    cached = _FINGERPRINT_CACHE
    if cached is not None:
        cached_at, fp, cached_path = cached
        if cached_path == notes_dir_str and now - cached_at < _FINGERPRINT_TTL_SEC:
            return fp
    fp = _compute_fingerprint()
    _FINGERPRINT_CACHE = (now, fp, notes_dir_str)
    return fp


def fingerprint() -> str:
    """Public alias of `_compute_fingerprint_cached()` — the cached
    variant since 2026-05-11 (Δ.6). Callers wanting a guaranteed
    cache miss should call `invalidate()` first."""
    return _compute_fingerprint_cached()


# ----------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------


# Δ.10 — schema now lives in scripts/core/migrations.MIGRATIONS and
# is applied via scripts/core/migrate.apply_pending(). The previous
# inline _SCHEMA constant became migration #1 ("notes_baseline").
# `_SCHEMA` is retained as a back-compat alias for any external
# import that referenced it directly; future schema changes append
# to MIGRATIONS rather than editing this string.
from scripts.core.migrations import MIGRATIONS as _MIGRATIONS

_SCHEMA = _MIGRATIONS[0][2]  # migration #1 sql — notes_baseline


def _read_notes_tuples(path: Path) -> list[tuple]:
    """Parse the NOTES = (...) tuple from a notes file via
    `ast.literal_eval` — same primitive the project uses everywhere
    for note files. Returns a list of tuples (one per note).

    Returns an empty list if the file is missing, empty, or has no
    NOTES binding.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return []
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "NOTES"
        ):
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                return []
            if isinstance(value, (list, tuple)):
                return list(value)
            return []
    return []


def _populate_from_book(conn: sqlite3.Connection, book_code: str, path: Path) -> int:
    """Insert every note from `path` into the index. Returns the
    count inserted. The note-tuple shape is the project's
    canonical 8 or 9-element form:

        (chapter, verse, suffix, anchor, kind, title, label, body)
        (chapter, verse, suffix, anchor, kind, title, label, body, attribution)

    Anything else is skipped silently — corruption resilience over
    correctness for the index (the canonical `.py` file remains the
    trust boundary).
    """
    rows = _read_notes_tuples(path)
    inserted = 0
    insert_sql = (
        "INSERT INTO notes "
        "(book_code, chapter, verse, suffix, anchor, kind, title, label, body, body_plain, attribution) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < 8:
            continue
        try:
            chapter = int(row[0])
            verse = int(row[1])
            suffix = str(row[2] or "")
            anchor = str(row[3] or "")
            kind = str(row[4] or "")
            title = str(row[5] or "")
            label = str(row[6] or "")
            body = str(row[7] or "")
        except (ValueError, TypeError):
            continue
        attribution = str(row[8]) if len(row) >= 9 and row[8] is not None else ""
        if not kind:
            continue
        # Δ.2: precompute body_plain at index build time. The
        # alternative — strip on every search query — would defeat
        # the index's whole point. ~50K notes × ~500 bytes = 25 MB
        # of plain text per build; acceptable.
        body_plain = _strip_tags(body)
        conn.execute(
            insert_sql,
            (book_code, chapter, verse, suffix, anchor, kind, title, label, body, body_plain, attribution),
        )
        inserted += 1
    return inserted


def _build_to(path: Path) -> tuple[int, str]:
    """Build a fresh index at `path`. Atomic: writes to
    `<path>.tmp` first, renames on success.

    Returns `(note_count, fingerprint)`.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    # ξ.4 Windows-lock fix: close any cached connection BEFORE
    # attempting to unlink the old file. On POSIX this is a no-op;
    # on Windows the old file stays locked while a connection is
    # open, so `path.unlink()` would PermissionError.
    global _CACHED_CONN, _CACHED_CONN_PATH
    # mint-11 audit MED: make the cached-conn close atomic w.r.t. connection()'s
    # check-and-return by taking _CONN_LOCK (mirrors invalidate()/rebuild()).
    with _CONN_LOCK:
        if _CACHED_CONN is not None:
            try:
                _CACHED_CONN.close()
            except sqlite3.Error:
                pass
            _CACHED_CONN = None
            _CACHED_CONN_PATH = None
    tmp = path.with_suffix(path.suffix + ".tmp")
    if tmp.is_file():
        tmp.unlink()
    conn = sqlite3.connect(str(tmp))
    try:
        # Performance pragmas for build-time bulk insert.
        conn.executescript("PRAGMA journal_mode=MEMORY; PRAGMA synchronous=OFF;")
        # Δ.10 — apply schema via the migration runner instead of an
        # inline executescript. On a freshly-rebuilt DB this applies
        # every migration in order (currently just #1 notes_baseline,
        # equivalent to the previous _SCHEMA).
        from scripts.core import migrate

        migrate.apply_pending(conn)
        notes_dir = _notes_dir()
        total = 0
        if notes_dir.is_dir():
            with conn:
                for nb in sorted(notes_dir.glob("*.py")):
                    if nb.stem == "__init__":
                        continue
                    total += _populate_from_book(conn, nb.stem, nb)
        # Δ.12 — populate the FTS5 external-content index from `notes`.
        # The 'rebuild' command reads every row from the source table
        # and re-indexes it. Cheap (one pass after the bulk insert);
        # idempotent (rebuild always produces the same index).
        try:
            conn.execute("INSERT INTO notes_fts(notes_fts) VALUES('rebuild')")
        except sqlite3.OperationalError:
            # Migration #2 might not have applied (e.g. very old DB
            # on disk between Δ.10 and Δ.12). Skip silently — search
            # falls back to the LIKE-based path until the next
            # fingerprint mismatch triggers a full rebuild.
            pass
        # Switch back to safer pragmas for query-time use.
        conn.executescript("PRAGMA journal_mode=DELETE; PRAGMA synchronous=NORMAL;")
        conn.close()
        # Atomic swap. Δ.4.1 attempt #5 (2026-05-11) — switched from
        # `unlink + rename` to `tmp.replace(path)` because on Windows
        # the discrete unlink can race with a sibling worker's still-
        # closing sqlite handle. `Path.replace()` calls `os.replace()`,
        # which is atomic on POSIX and, on Windows, MoveFileEx with
        # REPLACE_EXISTING.
        # ⚠ CORRECTION (round-5 audit): the swap is NOT self-healing.
        # MoveFileEx still FAILS with PermissionError (WinError 5) if ANY
        # handle on the destination `path` is open — atomicity only
        # guarantees a reader sees either the old or the new file, never a
        # half-written one; it does NOT tolerate an open dest handle. What
        # actually prevents the PermissionError here is closing every
        # cached connection to `path` (the `_CACHED_CONN.close()` guards
        # under `_CONN_LOCK`, mint-11) BEFORE this swap, so no open dest
        # handle remains. That close-guarding — not `os.replace` — is what
        # eliminated the PermissionError class on Δ.1 equivalence tests
        # under 8-worker xdist load.
        # mint-11 #14: compute the fingerprint BEFORE the swap so it reflects the
        # notes state the index was just built from. After tmp.replace, a notes
        # edit landing in the gap would be recorded as a MATCH — masking the
        # staleness so the index never rebuilds.
        fp = _compute_fingerprint()
        tmp.replace(path)
        return total, fp
    except Exception:
        conn.close()
        if tmp.is_file():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def rebuild(*, force: bool = False) -> dict:
    """Build the index if the corpus fingerprint has changed.

    Δ.0 — under the rebuild lock, so concurrent processes serialize
    on the actual write. The fast-path (fingerprint matches) does
    NOT take the lock — it's a pure read.

    Δ.6 — fingerprint reads go through `_compute_fingerprint_cached`
    so back-to-back calls (e.g. every `connection()` call from a
    web request) don't re-stat 87 files. The post-lock re-check
    deliberately bypasses the cache by clearing it first — once
    we've waited on the lock the cached value is potentially stale
    relative to other processes' writes.

    Returns:
        ``{rebuilt: bool, fingerprint: str, note_count: int,
        elapsed_ms: float}``
    """
    global _FINGERPRINT_CACHE, _CACHED_CONN, _CACHED_CONN_PATH
    t0 = time.perf_counter()
    fp = _compute_fingerprint_cached()
    fp_path = _fingerprint_path()
    idx_path = _index_path()

    if not force and idx_path.is_file() and fp_path.is_file():
        try:
            existing_fp = fp_path.read_text(encoding="utf-8").strip()
        except OSError:
            existing_fp = ""
        if existing_fp == fp:
            return {
                "rebuilt": False,
                "fingerprint": fp,
                "note_count": _count_notes(idx_path),
                "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
            }

    # Δ.0 — serialize concurrent writers. After acquiring the
    # lock, re-check the fingerprint: another process may have
    # rebuilt while we were waiting, in which case our work is
    # already done.
    with _acquire_rebuild_lock():
        if not force and idx_path.is_file() and fp_path.is_file():
            try:
                existing_fp_post = fp_path.read_text(encoding="utf-8").strip()
            except OSError:
                existing_fp_post = ""
            # Recompute fingerprint inside the lock — corpus might
            # have changed between our pre-lock check and acquire,
            # OR another process may have rebuilt while we waited.
            # Clear the cache first so the post-lock check is fresh.
            _FINGERPRINT_CACHE = None
            fp_post = _compute_fingerprint_cached()
            if existing_fp_post == fp_post:
                # Another process rebuilt while we waited (or no
                # rebuild was actually needed); skip our build.
                return {
                    "rebuilt": False,
                    "fingerprint": fp_post,
                    "note_count": _count_notes(idx_path),
                    "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
                }
            fp = fp_post

        note_count, fp = _build_to(idx_path)
        fp_path.parent.mkdir(parents=True, exist_ok=True)
        fp_path.write_text(fp, encoding="utf-8")
        # Refresh the fingerprint cache to the just-written value
        # so the next caller sees the post-build fingerprint
        # without a fresh stat-walk. ω.36 — include notes_dir path
        # tag so the cache survives the rebuild correctly even
        # when the resolved path is monkeypatched by tests.
        _FINGERPRINT_CACHE = (time.monotonic(), fp, str(_notes_dir()))

        # Reset any cached connection — it points at the old file now.
        # mint-9 #20: this MUST be inside the rebuild lock. Under the
        # ThreadingHTTPServer a worker thread can be inside connection()
        # between its `_CACHED_CONN is not None` check and its `.execute()`;
        # closing the conn here without the lock raced that read and could
        # surface a sqlite3.ProgrammingError on a closed connection. The lock
        # serialises the reset against connection()'s own rebuild() call.
        # mint-11 audit MED: ALSO take _CONN_LOCK — the rebuild lock alone does not
        # serialise against connection()'s post-rebuild _CONN_LOCK section. Safe
        # (no re-entrancy): connection() releases the rebuild lock before taking
        # _CONN_LOCK, so the ordering is one-way (rebuild-lock → _CONN_LOCK).
        with _CONN_LOCK:
            if _CACHED_CONN is not None:
                try:
                    _CACHED_CONN.close()
                except sqlite3.Error:
                    pass
                _CACHED_CONN = None
                _CACHED_CONN_PATH = None

    return {
        "rebuilt": True,
        "fingerprint": fp,
        "note_count": note_count,
        "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
    }


def _count_notes(path: Path) -> int:
    """Quick row-count helper for the rebuild() response shape."""
    try:
        c = sqlite3.connect(str(path))
        try:
            return int(c.execute("SELECT COUNT(*) FROM notes").fetchone()[0])
        finally:
            c.close()
    except sqlite3.Error:
        return 0


# ----------------------------------------------------------------------
# Connection (cached)
# ----------------------------------------------------------------------


_CACHED_CONN: sqlite3.Connection | None = None
# ω.34 / Δ.4.1 — track which path `_CACHED_CONN` was opened against
# so test fixtures that monkeypatch `paths.user_data_root` don't
# leave a stale connection pointing at a deleted tmp_path file.
_CACHED_CONN_PATH: str | None = None
# mint-10: a plain threading.Lock guarding the check-then-create in connection()
# so a ThreadingHTTPServer race can't have two worker threads each open a
# connection and leak one fd. NOT _acquire_rebuild_lock — that's the file lock
# for the cross-process index rebuild; this guards only the in-process cache.
_CONN_LOCK = threading.Lock()


def connection() -> sqlite3.Connection:
    """Return a (cached) connection to the index. Triggers rebuild()
    on first call. The connection is read-only-by-convention; do
    not write through it (the index is fully derived).

    The cache invalidates itself if the resolved index path changes
    (i.e. tests monkeypatched `paths.user_data_root`) — without that
    check, a synthetic test leaves the conn pointing at a tmp file
    that the next real test's call would reuse and find empty.
    """
    global _CACHED_CONN, _CACHED_CONN_PATH
    rebuild()  # Idempotent fast-path when fingerprint matches.
    current_path = str(_index_path())
    # mint-10: guard the check-then-create with _CONN_LOCK so two worker threads
    # can't both observe `_CACHED_CONN is None` and each open a connection, leaking
    # one fd. rebuild() stays OUTSIDE the lock (it has its own cross-process file
    # lock); this lock is purely for the in-process cached connection.
    with _CONN_LOCK:
        if _CACHED_CONN is not None and current_path != _CACHED_CONN_PATH:
            try:
                _CACHED_CONN.close()
            except sqlite3.Error:
                pass
            _CACHED_CONN = None
            _CACHED_CONN_PATH = None
        if _CACHED_CONN is None:
            # check_same_thread=False: the web server is a ThreadingHTTPServer and
            # _warm_corpus_index() opens this connection in the main thread, while
            # requests are served on worker threads — without this, every
            # /customize + /matrix request 500'd with a cross-thread
            # sqlite3.ProgrammingError. Safe because the index is read-only by
            # convention (all writes go through a separate connection in rebuild()),
            # Python's sqlite3 serializes access in its default threadsafety mode,
            # and _CONN_LOCK serializes the open itself.
            _CACHED_CONN = sqlite3.connect(current_path, check_same_thread=False)
            _CACHED_CONN.row_factory = sqlite3.Row
            _CACHED_CONN_PATH = current_path
        return _CACHED_CONN


def invalidate() -> None:
    """Force the next call to rebuild. Useful after explicit corpus
    edits that the mtime check might miss (e.g. a future API that
    writes through `notes_io` followed immediately by a query).

    Δ.6 — also clears the in-memory fingerprint cache so the next
    `_compute_fingerprint_cached()` call recomputes from scratch.
    Without this clear, an `invalidate()` call inside the TTL
    window would still return a stale fingerprint and incorrectly
    skip the rebuild on the next `connection()` call.
    """
    global _CACHED_CONN, _CACHED_CONN_PATH, _FINGERPRINT_CACHE
    _FINGERPRINT_CACHE = None
    # mint-11 audit MED: take _CONN_LOCK so the close is atomic w.r.t. connection().
    with _CONN_LOCK:
        if _CACHED_CONN is not None:
            try:
                _CACHED_CONN.close()
            except sqlite3.Error:
                pass
            _CACHED_CONN = None
            _CACHED_CONN_PATH = None
    fp_path = _fingerprint_path()
    if fp_path.is_file():
        try:
            fp_path.unlink()
        except OSError:
            pass


# ----------------------------------------------------------------------
# Query helpers
# ----------------------------------------------------------------------


def count_by_kind(*, book: str | None = None, kinds: list[str] | None = None) -> dict[str, int]:
    """Return ``{kind: count}`` aggregated across the corpus (or a
    single book if `book` is given). Optional ``kinds`` filter
    restricts the result; empty filter means "all kinds in corpus."
    """
    conn = connection()
    sql = "SELECT kind, COUNT(*) FROM notes WHERE 1=1"
    args: list = []
    if book:
        sql += " AND book_code = ?"
        args.append(book)
    if kinds:
        placeholders = ",".join("?" * len(kinds))
        sql += f" AND kind IN ({placeholders})"
        args.extend(kinds)
    sql += " GROUP BY kind"
    return {row[0]: row[1] for row in conn.execute(sql, args)}


def count_by_book(*, kinds: list[str] | None = None) -> dict[str, int]:
    """Return ``{book_code: count}``. Optional `kinds` filter."""
    conn = connection()
    sql = "SELECT book_code, COUNT(*) FROM notes WHERE 1=1"
    args: list = []
    if kinds:
        placeholders = ",".join("?" * len(kinds))
        sql += f" AND kind IN ({placeholders})"
        args.extend(kinds)
    sql += " GROUP BY book_code"
    return {row[0]: row[1] for row in conn.execute(sql, args)}


def count_by_kind_and_book(
    *,
    kinds: list[str] | None = None,
    books: list[str] | None = None,
) -> dict[tuple[str, str], int]:
    """Return ``{(book_code, kind): count}``. Optional filters."""
    conn = connection()
    sql = "SELECT book_code, kind, COUNT(*) FROM notes WHERE 1=1"
    args: list = []
    if kinds:
        placeholders = ",".join("?" * len(kinds))
        sql += f" AND kind IN ({placeholders})"
        args.extend(kinds)
    if books:
        placeholders = ",".join("?" * len(books))
        sql += f" AND book_code IN ({placeholders})"
        args.extend(books)
    sql += " GROUP BY book_code, kind"
    return {(row[0], row[1]): row[2] for row in conn.execute(sql, args)}


def total_note_count() -> int:
    """Total notes in the corpus."""
    conn = connection()
    row = conn.execute("SELECT COUNT(*) FROM notes").fetchone()
    return int(row[0]) if row else 0


def kinds_present() -> list[str]:
    """All distinct kinds present in the corpus, sorted."""
    conn = connection()
    return [row[0] for row in conn.execute("SELECT DISTINCT kind FROM notes ORDER BY kind")]


# ----------------------------------------------------------------------
# Δ.3 — attribution audit
# ----------------------------------------------------------------------


# Mirror of web.py's `_THIN_ATTR_PATTERNS`. Kept duplicated rather
# than imported because web.py is a heavy module (it pulls every
# `api_*` helper at import time). The duplication is the price of
# keeping `corpus_index` lightweight; an equivalence test pins the
# two paths return the same classification for every input.
_THIN_ATTR_PATTERNS = (
    re.compile(r"^see\s", re.I),
    re.compile(r"^cf\.?\s", re.I),
    re.compile(r"^ibid", re.I),
    re.compile(r"^author$", re.I),
)


def _classify_attribution(attr: str) -> str:
    """Bucket an attribution string into one of:
    'missing'  — empty/whitespace, no attribution at all
    'thin'     — present but suspiciously short or vague
    'user'     — user-original / user-paraphrase (legitimate but flag)
    'sourced'  — references a real outside source (best case)

    Mirror of `web._classify_attribution` — equivalence pin in tests.
    """
    s = (attr or "").strip()
    if not s:
        return "missing"
    if any(p.match(s) for p in _THIN_ATTR_PATTERNS):
        return "thin"
    if len(s) < 12:
        return "thin"
    s_low = s.lower()
    if s_low.startswith("user original") or s_low.startswith("user paraphrase"):
        return "user"
    return "sourced"


def audit_attribution() -> dict:
    """Δ.3 — attribution audit via the index.

    Returns the same shape as `web.api_attribution_audit()`:

        {
            "counts": {"total": N, "missing": ..., "thin": ...,
                       "user": ..., "sourced": ...},
            "needs_attention": [{book, book_title, section, chapter,
                                 verse, suffix, kind, kind_label,
                                 category, category_symbol, title,
                                 body_preview, attribution,
                                 classification}, ...],
            "by_book": [{code, title, section, missing, thin}, ...],
            "by_kind": [(kind, count), ...],
        }

    The book / kind / category metadata is looked up via the
    existing `config.*_by_*` caches; only the per-note data comes
    from the index. Equivalence pin in tests.
    """
    from . import config

    books_idx = config.books_by_code()
    kinds_idx = config.kinds_by_code()
    cats_idx = config.categories_by_id()

    # Canonical book order for per-book sorting
    books = config.load_books()
    canonical_order = {b["code"]: i for i, b in enumerate(books)}

    counts = {"total": 0, "missing": 0, "thin": 0, "user": 0, "sourced": 0}
    needs_attention: list[dict] = []

    conn = connection()
    rows = conn.execute(
        "SELECT book_code, chapter, verse, suffix, kind, title, body, attribution "
        "FROM notes "
        "ORDER BY book_code, chapter, verse, suffix"
    ).fetchall()

    for r in rows:
        book_code = r["book_code"]
        chapter = int(r["chapter"])
        verse = int(r["verse"])
        suffix = r["suffix"] or ""
        kind = r["kind"]
        title = r["title"] or ""
        body = r["body"] or ""
        attribution = r["attribution"] or ""

        counts["total"] += 1
        cls = _classify_attribution(attribution)
        counts[cls] = counts.get(cls, 0) + 1
        if cls in ("missing", "thin"):
            book_def = books_idx.get(book_code, {})
            kind_def = kinds_idx.get(kind, {})
            cat_id = kind_def.get("category", "?")
            cat_def = cats_idx.get(cat_id, {})
            needs_attention.append(
                {
                    "book": book_code,
                    "book_title": book_def.get("title", book_code),
                    "section": book_def.get("section", ""),
                    "chapter": chapter,
                    "verse": verse,
                    "suffix": suffix,
                    "kind": kind,
                    "kind_label": kind_def.get("label", kind),
                    "category": cat_id,
                    "category_symbol": cat_def.get("symbol", "?"),
                    "title": title,
                    "body_preview": body[:120],
                    "attribution": attribution.strip(),
                    "classification": cls,
                }
            )

    # ORDER BY book_code in SQL gives alphabetical, not canonical;
    # re-sort needs_attention into canonical book order.
    needs_attention.sort(
        key=lambda item: (
            canonical_order.get(item["book"], 9999),
            item["chapter"],
            item["verse"],
            item["suffix"],
        )
    )

    # Per-book counts (left rail)
    by_book: dict[str, dict] = {}
    for item in needs_attention:
        b = item["book"]
        if b not in by_book:
            by_book[b] = {
                "code": b,
                "title": item["book_title"],
                "section": item["section"],
                "missing": 0,
                "thin": 0,
            }
        by_book[b][item["classification"]] += 1
    by_book_list = sorted(by_book.values(), key=lambda x: -(x["missing"] + x["thin"]))

    # Per-kind counts
    by_kind: dict[str, int] = {}
    for item in needs_attention:
        by_kind[item["kind"]] = by_kind.get(item["kind"], 0) + 1
    by_kind_list = sorted(by_kind.items(), key=lambda x: -x[1])

    return {
        "counts": counts,
        "needs_attention": needs_attention,
        "by_book": by_book_list,
        "by_kind": by_kind_list,
    }


# ----------------------------------------------------------------------
# Δ.4 — index-backed compute_matrix
# ----------------------------------------------------------------------


def compute_matrix_indexed():
    """Δ.4 — build the matrix data structure entirely from the index.

    Returns a `scripts.core.matrix.Matrix` dataclass with all five
    projections populated:

      - ``enabled``               ed → kind → count (filtered)
      - ``potential``             ed → kind → count (canon-only)
      - ``edition_canon_books``   ed → set[book_code]
      - ``edition_enabled_kinds`` ed → set[kind_code]
      - ``per_book``              ed → kind → book → count
      - ``per_chapter``           ed → kind → book → chapter → count

    The shape exactly matches `matrix.compute_matrix()` so an
    eventual wire flip is a one-line change. Equivalence pin in
    tests confirms identical output for every edition.

    Strategy: ONE pass over the index produces a (book, kind,
    chapter, count) grid. Editions then filter+sum that grid into
    their projections in Python — bounded by `O(books × kinds ×
    editions)` not `O(notes × editions)`.
    """
    # Lazy import to avoid circulars (matrix imports from this
    # package at module level for `_enabled_kinds_for_edition`).
    from . import config
    from .matrix import Matrix, _canon_books_for_edition, _enabled_kinds_for_edition, _load_canons

    # Single SQL roll-up: (book, kind, chapter, count). Groups
    # the 51K-row notes table down to ~5K aggregate rows.
    conn = connection()
    rows = conn.execute(
        "SELECT book_code, kind, chapter, COUNT(*) as cnt FROM notes GROUP BY book_code, kind, chapter"
    ).fetchall()

    # Pivot into nested dicts keyed by book → kind → chapter
    # for fast per-edition filtering below.
    grid: dict[str, dict[str, dict[int, int]]] = {}
    book_kind_totals: dict[str, dict[str, int]] = {}
    for r in rows:
        book = r["book_code"]
        kind = r["kind"]
        chapter = int(r["chapter"])
        cnt = int(r["cnt"])
        grid.setdefault(book, {}).setdefault(kind, {})[chapter] = cnt
        book_kind_totals.setdefault(book, {})[kind] = book_kind_totals.setdefault(book, {}).get(kind, 0) + cnt

    # Pre-compute per-edition canon and enabled-kinds sets — same
    # logic the file-walk path uses, so editions filter identically.
    editions = config.load_editions()
    kinds_def = config.load_kinds()
    canons = _load_canons()

    edition_canon: dict[str, set[str]] = {}
    edition_enabled: dict[str, set[str]] = {}
    for ed in editions:
        ed_id = ed["id"]
        edition_canon[ed_id] = _canon_books_for_edition(ed, canons)
        edition_enabled[ed_id] = _enabled_kinds_for_edition(ed, kinds_def)

    # ψ.35-Final: only `per_chapter` is built here. The three
    # derived projections (`enabled`, `potential`, `per_book`) are
    # computed in Matrix.__post_init__ from per_chapter +
    # edition_enabled_kinds. Same simplification applied to the
    # file-walk reference path in `scripts/core/matrix.py`.
    per_chapter: dict[str, dict[str, dict[str, dict[int, int]]]] = {ed["id"]: {} for ed in editions}

    # For each book in each edition's canon, distribute that book's
    # per-chapter counts into per_chapter.
    for book in book_kind_totals:
        for ed in editions:
            ed_id = ed["id"]
            if book not in edition_canon[ed_id]:
                continue
            chapter_grid = grid.get(book, {})
            for kind_code, chap_counts in chapter_grid.items():
                if chap_counts:
                    # Copy to detach from grid (matches file-walk's
                    # `dict(chap_counts)` defensive-copy contract).
                    per_chapter[ed_id].setdefault(kind_code, {})[book] = dict(chap_counts)

    return Matrix(
        edition_canon_books=edition_canon,
        edition_enabled_kinds=edition_enabled,
        per_chapter=per_chapter,
    )


# ----------------------------------------------------------------------
# Δ.2 — index-backed search
# ----------------------------------------------------------------------


# Field weights mirror `scripts.core.note_search._FIELD_WEIGHTS` so an
# index-backed search returns the same ordering as the file-walk.
# Drift here would break the equivalence pin that lets future phases
# flip `api_search_notes` to call this implementation.
_SEARCH_FIELD_WEIGHTS = (
    ("label", 5),
    ("title", 4),
    ("kind", 3),
    ("attribution", 2),
    ("body_plain", 1),
)


def _make_excerpt(text: str, query: str, *, radius: int = 60) -> str:
    """Mirror of `note_search._make_excerpt`. Returns a window of
    ``text`` around the first occurrence of ``query``.
    """
    if not text:
        return ""
    if not query:
        if len(text) <= radius * 2:
            return text
        return text[: radius * 2] + "…"
    lower = text.lower()
    q_lc = query.lower()
    idx = lower.find(q_lc)
    if idx < 0:
        if len(text) <= radius * 2:
            return text
        return text[: radius * 2] + "…"
    start = max(0, idx - radius)
    end = min(len(text), idx + len(query) + radius)
    out = text[start:end]
    if start > 0:
        out = "…" + out
    if end < len(text):
        out = out + "…"
    return out


def search(
    query: str,
    *,
    kind: str | None = None,
    book: str | None = None,
    edition_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Δ.2 — index-backed substring search across the corpus.

    Returns a list of dicts (matching the existing `SearchHit.to_dict`
    shape from `note_search`) sorted by score descending then by
    canonical book order, chapter, verse.

    Empty / whitespace-only ``query`` returns an empty list.

    The scoring exactly mirrors `note_search._FIELD_WEIGHTS` —
    label=5, title=4, kind=3, attribution=2, body=1 — so the
    equivalence pin in tests can hold.

    `edition_id` filters to kinds enabled in that edition's profile
    (using the same `_enabled_kinds_for_edition` precedence as the
    file-walk implementation).
    """
    q = (query or "").strip()
    if not q:
        return []
    q_lc = q.lower()

    # Resolve edition filter to (canon_book_set, enabled_kind_set)
    canon_book_set: set[str] | None = None
    enabled_kind_set: set[str] | None = None
    if edition_id:
        # Local imports to avoid a circular: matrix imports config,
        # config is fine here. We import lazily so this module stays
        # importable even before matrix's load chain settles.
        from . import config
        from .matrix import _enabled_kinds_for_edition, _load_canons

        editions = config.load_editions()
        ed = next(
            (e for e in editions if isinstance(e, dict) and e.get("id") == edition_id),
            None,
        )
        if ed is not None:
            all_kinds = config.load_kinds()
            enabled_kind_set = _enabled_kinds_for_edition(ed, all_kinds)
            canon_id = ed.get("canon")
            if canon_id:
                canons = _load_canons()
                canon_def = canons.get(canon_id) if isinstance(canons, dict) else None
                if isinstance(canon_def, dict):
                    canon_book_set = set(canon_def.get("books") or [])

    conn = connection()
    # Build SQL with the LIKE filter against any of the 5 fields.
    # Score is a SUM(CASE WHEN field LIKE ? THEN weight ELSE 0 END)
    # computed in the SELECT so we can ORDER BY it directly.
    pattern = f"%{q_lc}%"
    sql_parts: list[str] = []
    score_parts: list[str] = []
    args: list = []
    for field, weight in _SEARCH_FIELD_WEIGHTS:
        # SQLite's LIKE is case-insensitive for ASCII by default.
        # For non-ASCII (Hebrew / Greek), users tend to paste the
        # exact glyph so case-folding isn't critical there.
        score_parts.append(f"(CASE WHEN LOWER({field}) LIKE ? THEN {weight} ELSE 0 END)")
        args.append(pattern)
    score_sql = " + ".join(score_parts)
    where_or = " OR ".join(f"LOWER({field}) LIKE ?" for field, _ in _SEARCH_FIELD_WEIGHTS)
    args.extend([pattern] * len(_SEARCH_FIELD_WEIGHTS))

    sql = (
        "SELECT book_code, chapter, verse, suffix, anchor, kind, title, label, "
        f"body_plain, attribution, ({score_sql}) AS score "
        f"FROM notes WHERE ({where_or})"
    )

    if kind:
        sql += " AND kind = ?"
        args.append(kind)
    if book:
        sql += " AND book_code = ?"
        args.append(book)
    if enabled_kind_set is not None:
        if not enabled_kind_set:
            return []
        placeholders = ",".join("?" * len(enabled_kind_set))
        sql += f" AND kind IN ({placeholders})"
        args.extend(sorted(enabled_kind_set))
    if canon_book_set is not None:
        if not canon_book_set:
            return []
        placeholders = ",".join("?" * len(canon_book_set))
        sql += f" AND book_code IN ({placeholders})"
        args.extend(sorted(canon_book_set))

    # Cap before sort/order — the score order needs all candidates,
    # so we apply LIMIT after. SQLite handles this efficiently.
    sql_parts.append(sql)
    rows = conn.execute(sql, args).fetchall()

    # Order: -score, canonical_book_order, chapter, verse, suffix
    # Canonical book order comes from books.yaml. Build the lookup.
    from . import config

    books = config.load_books()
    canonical_order = {b["code"]: i for i, b in enumerate(books)}

    def sort_key(r):
        return (
            -int(r["score"]),
            canonical_order.get(r["book_code"], 9999),
            int(r["chapter"]),
            int(r["verse"]),
            r["suffix"] or "",
        )

    sorted_rows = sorted(rows, key=sort_key)
    cap = max(0, int(limit)) if limit is not None else len(sorted_rows)
    sorted_rows = sorted_rows[:cap]

    # Build the dict-shaped output. Excerpt sourcing mirrors the
    # file-walk: prefer body_plain when the query hits there, fall
    # back to label, then title, then any of the three.
    out: list[dict] = []
    for r in sorted_rows:
        body_plain = r["body_plain"] or ""
        label = r["label"] or ""
        title = r["title"] or ""
        if q_lc in body_plain.lower() and body_plain:
            excerpt_src = body_plain
        elif q_lc in label.lower() and label:
            excerpt_src = label
        elif q_lc in title.lower() and title:
            excerpt_src = title
        else:
            excerpt_src = body_plain or label or title
        excerpt = _make_excerpt(excerpt_src, q)
        out.append(
            {
                "book_code": r["book_code"],
                "chapter": int(r["chapter"]),
                "verse": int(r["verse"]),
                "suffix": r["suffix"] or "",
                "anchor": r["anchor"] or "",
                "kind": r["kind"],
                "title": title,
                "label": label,
                "excerpt": excerpt,
                "attribution": r["attribution"] or None,
                "score": int(r["score"]),
            }
        )
    return out


# ----------------------------------------------------------------------
# Δ.12 — FTS5 full-text search (2026-05-11)
# ----------------------------------------------------------------------


def fts5_search(
    query: str,
    *,
    kind: str | None = None,
    book: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Δ.12 — FTS5-backed search across notes.

    Same return shape as `search()` so consumers can swap call sites.
    Uses SQLite FTS5 MATCH with the `bm25()` ranking function and the
    `snippet()` builtin for context-window excerpts (~30 token window
    around the first match, wrapped in `‹›` markers).

    Query syntax: FTS5 standard. Bare words are AND-combined; quoted
    phrases match exactly; `OR`, `NOT`, `*` (prefix), and `NEAR()` all
    supported. Bare-word queries are auto-prefixed (`word*`) for
    substring-ish matching that matches the LIKE-based search's UX.

    Returns:
        list[dict] — same shape as `search()`: book_code, chapter,
        verse, suffix, anchor, kind, title, label, excerpt,
        attribution, score (lower is better in FTS5 bm25; flipped
        to a positive integer for consistency with the LIKE search).

    Empty / whitespace-only query → []. Queries that FTS5 rejects
    as malformed (e.g., unbalanced quotes) raise `ValueError`.
    """
    q = (query or "").strip()
    if not q:
        return []

    # Bare-word queries → prefix-matching by default. Single-word
    # queries get `word*`; multi-word bare queries become `w1* w2*`.
    # Power users using FTS5 syntax (quotes, OR, NOT, NEAR) get their
    # literal query through unchanged.
    has_syntax = any(c in q for c in ('"', "(", ")")) or any(
        kw in q.upper().split() for kw in ("AND", "OR", "NOT", "NEAR")
    )
    if has_syntax:
        match_q = q
    else:
        # Sanitize bare words: split on whitespace, append `*` to each
        # token that doesn't already end with one. Strip non-alphanum
        # punctuation that FTS5 would reject (commas, parens, etc.).
        tokens = []
        for tok in q.split():
            cleaned = "".join(c for c in tok if c.isalnum() or c in "*'-")
            if not cleaned:
                continue
            if not cleaned.endswith("*"):
                cleaned = cleaned + "*"
            tokens.append(cleaned)
        if not tokens:
            return []
        match_q = " ".join(tokens)

    conn = connection()
    sql_parts = [
        "SELECT n.book_code, n.chapter, n.verse, n.suffix, n.anchor, n.kind, n.title, n.label, n.attribution,",
        "snippet(notes_fts, -1, '‹', '›', '…', 30) AS excerpt,",
        "bm25(notes_fts) AS bm25_score",
        "FROM notes_fts JOIN notes n ON n.rowid = notes_fts.rowid",
        "WHERE notes_fts MATCH ?",
    ]
    args: list = [match_q]

    if kind:
        sql_parts.append("AND n.kind = ?")
        args.append(kind)
    if book:
        sql_parts.append("AND n.book_code = ?")
        args.append(book)

    sql_parts.append("ORDER BY bm25_score")  # ascending — lower bm25 = better match
    cap = max(1, int(limit)) if limit else 100
    sql_parts.append("LIMIT ?")
    args.append(cap)

    sql = " ".join(sql_parts)
    try:
        rows = conn.execute(sql, args).fetchall()
    except sqlite3.OperationalError as e:
        # FTS5 rejects malformed queries (e.g., unbalanced quotes).
        # Re-raise as ValueError so callers can distinguish from
        # generic DB errors.
        raise ValueError(f"malformed FTS5 query {query!r}: {e}") from e

    out: list[dict] = []
    for r in rows:
        # bm25 is negative-ish; lower magnitude = better. Flip to a
        # positive integer for consistency with the LIKE search's
        # "higher score = better" convention.
        bm25 = float(r["bm25_score"])
        # bm25 typically ranges 0 to -10; map to integer score where
        # 100 = perfect match, decreasing for weaker.
        positive_score = max(1, int(100 - bm25 * -10))
        out.append(
            {
                "book_code": r["book_code"],
                "chapter": int(r["chapter"]),
                "verse": int(r["verse"]),
                "suffix": r["suffix"] or "",
                "anchor": r["anchor"] or "",
                "kind": r["kind"],
                "title": r["title"] or "",
                "label": r["label"] or "",
                "excerpt": r["excerpt"] or "",
                "attribution": r["attribution"] or None,
                "score": positive_score,
            }
        )
    return out


# ----------------------------------------------------------------------
# Δ.5 — index-backed dashboard_stats
# ----------------------------------------------------------------------


def dashboard_stats(books: list[dict]) -> dict:
    """Δ.5 — gather the project-wide stats `dashboard.gather_stats()`
    produces, but via a single index pass instead of an 87-book walk.

    Mirrors `dashboard.gather_stats(books, kinds)`'s output shape on
    every aggregate field (total_notes, per_kind, per_book.note_count,
    per_book.attributed, per_book.kinds, per_book.chapters_touched,
    per_book.pct_covered, chapter_density). Equivalence pin in tests.

    Pass-through fields the file-walk includes for downstream rendering
    (`books`, `kinds`, `parse_failures`, `generated_at`) are NOT
    returned here — consumers either pass them through themselves or
    use the dedicated `dashboard.gather_stats()` for a full report.
    The index has no notion of "parse failure" because malformed
    entries are silently skipped at build time.

    Args:
        books: list of book dicts from `config.load_books()` (each has
            `code`, `title`, `ch_count`). Iteration order matches the
            file-walk path so per_book key order is identical.

    Returns:
        ``{total_notes, per_book, per_kind, chapter_density}`` —
        equivalent to the corresponding fields of
        `dashboard.gather_stats()`.
    """
    book_codes = [b["code"] for b in books if isinstance(b, dict) and b.get("code")]

    per_book: dict[str, dict] = {}
    per_kind: dict[str, int] = {}
    chapter_density: dict[str, dict[int, int]] = {}
    total_notes = 0

    if not book_codes:
        for b in books:
            if not isinstance(b, dict):
                continue
            code = b.get("code")
            if not code:
                continue
            ch_count = b.get("ch_count", 0)
            per_book[code] = {
                "code": code,
                "title": b.get("title", code),
                "ch_count": ch_count,
                "note_count": 0,
                "attributed": 0,
                "kinds": {},
                "chapters_touched": 0,
                "pct_covered": 0.0,
            }
        return {
            "total_notes": 0,
            "per_book": per_book,
            "per_kind": per_kind,
            "chapter_density": chapter_density,
        }

    conn = connection()
    placeholders = ",".join("?" * len(book_codes))

    # Per (book, kind): count + attributed-count. The attribution
    # presence test mirrors `dashboard.gather_stats`: tuple index 8
    # exists, is a string, and stripped non-empty. The index stores
    # attribution as a TEXT column (default ''); the file-walk's
    # `len(tup) >= 9` branch is automatic here because non-9-element
    # rows insert '' for attribution at build time.
    rows = conn.execute(
        f"SELECT book_code, kind, COUNT(*) AS cnt, "
        f"SUM(CASE WHEN TRIM(attribution) != '' THEN 1 ELSE 0 END) AS attr_cnt "
        f"FROM notes WHERE book_code IN ({placeholders}) "
        f"GROUP BY book_code, kind",
        book_codes,
    ).fetchall()

    book_kind_counts: dict[str, dict[str, int]] = {}
    book_attr_counts: dict[str, int] = {}
    for r in rows:
        bc = r["book_code"]
        kind = r["kind"]
        cnt = int(r["cnt"])
        attr_cnt = int(r["attr_cnt"] or 0)
        book_kind_counts.setdefault(bc, {})[kind] = cnt
        book_attr_counts[bc] = book_attr_counts.get(bc, 0) + attr_cnt
        per_kind[kind] = per_kind.get(kind, 0) + cnt

    # Per (book, chapter): count, fed into chapter_density. Same
    # filter on book_codes.
    chap_rows = conn.execute(
        f"SELECT book_code, chapter, COUNT(*) AS cnt "
        f"FROM notes WHERE book_code IN ({placeholders}) "
        f"GROUP BY book_code, chapter",
        book_codes,
    ).fetchall()

    book_chapters: dict[str, set[int]] = {}
    for r in chap_rows:
        bc = r["book_code"]
        chapter = int(r["chapter"])
        cnt = int(r["cnt"])
        chapter_density.setdefault(bc, {})[chapter] = cnt
        book_chapters.setdefault(bc, set()).add(chapter)

    # Now stitch the per_book output in book-list iteration order
    # so the dict's key sequence matches dashboard.gather_stats.
    for b in books:
        if not isinstance(b, dict):
            continue
        code = b.get("code")
        if not code:
            continue
        ch_count = b.get("ch_count", 0)
        kinds_count = book_kind_counts.get(code, {})
        n = sum(kinds_count.values())
        chapters_touched = len(book_chapters.get(code, set()))
        per_book[code] = {
            "code": code,
            "title": b.get("title", code),
            "ch_count": ch_count,
            "note_count": n,
            "attributed": book_attr_counts.get(code, 0),
            "kinds": kinds_count,
            "chapters_touched": chapters_touched,
            "pct_covered": (chapters_touched / ch_count * 100) if ch_count else 0.0,
        }
        total_notes += n
        # Ensure book has a chapter_density entry even when zero notes
        # (file-walk uses defaultdict so absent keys silently return
        # empty; an absent key in a regular dict would diverge).
        chapter_density.setdefault(code, {})

    return {
        "total_notes": total_notes,
        "per_book": per_book,
        "per_kind": per_kind,
        "chapter_density": chapter_density,
    }

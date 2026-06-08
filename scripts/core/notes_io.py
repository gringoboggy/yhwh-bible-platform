"""
notes_io.py — Crash-safe write primitives for the notes corpus.

Two helpers:

    atomic_write(path, text)      # write-then-rename; POSIX-atomic
    ensure_backup(path)           # copy file to .backups/ before mutating

Plus shared note-reading helpers (consolidated from 5+ duplicates in
v28a-11 / Phase β.2):

    load_notes_from_text(text)    # parse a notes-module source string
    load_notes(path)               # parse a notes-module file

Use atomic_write everywhere a note file, candidate JSON, or any other
content artifact is rewritten. Use ensure_backup before any *bulk* or
*destructive* operation (whole-file rewrite, mass find-replace, etc.) so
that even a regex bug can be reverted from disk in one step.

Why these matter (Phase β audit, finding S1 / S3):
  - Direct path.write_text(...) is NOT atomic. A crash mid-write leaves
    the file half-written and unparseable. attribute.py --all-books
    walks 87 files in sequence; without atomic writes, any interruption
    is potentially corrupting.
  - The save-zip workflow is the only fallback otherwise, which can be
    hours stale.
"""

from __future__ import annotations

import ast
import functools
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

__all__ = [
    "atomic_write",
    "ensure_backup",
    "load_notes_from_text",
    "load_notes",
    "clear_load_notes_cache",
]


def atomic_write(path: Path | str, text: str, *, encoding: str = "utf-8") -> Path:
    """Replace *path* with *text* atomically (write to .tmp, then rename).

    On POSIX, ``os.replace`` is guaranteed atomic — the destination is
    either fully the old content or fully the new content; there is no
    half-written state observable to other readers.

    Δ.7 — when the written path is a `.py` file under
    `content/notes/`, the corpus_index fingerprint cache is
    invalidated so the next indexed query sees the write
    immediately. Without this hook the Δ.6 TTL (1s in production)
    would let a freshly-written note return stale aggregates for
    up to one TTL after the write — visible in the editor's
    save → re-render-matrix loop after Δ.4.1 wired
    `compute_matrix()` to the indexed path.

    Returns the resolved Path that was written.
    """
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        # ω.48 / F-DEEP3-2: newline="" disables the platform newline
        # translation Path.write_text does by default (newline=None →
        # `\n`→os.linesep, i.e. CRLF on Windows). The repo is
        # LF-canonical (.gitattributes `* text=auto`); without this
        # every atomic_write on Windows produced CRLF, which git
        # normalizes on add (so commits stay clean) but which shows
        # files as spuriously modified in mid-test-run `git status`
        # — the editions.yaml false-alarm AUDIT_2026-05-15-DEEP-3
        # root-caused (F-DEEP3-2). Writing the string verbatim keeps
        # on-disk == in-memory == repo (LF) on every platform.
        tmp.write_text(text, encoding=encoding, newline="")
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    _invalidate_corpus_index_if_notes_file(path)
    return path


def atomic_write_bytes(path: Path | str, data: bytes) -> Path:
    """Binary counterpart of atomic_write — same atomicity guarantee.

    Used by the cover-upload endpoint (Phase π.4-B) and any other
    binary writer. Same .tmp + os.replace dance. Δ.7 hook fires
    here too — defense in depth against a future writer choosing
    the wrong primitive.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    _invalidate_corpus_index_if_notes_file(path)
    return path


def _invalidate_corpus_index_if_notes_file(path: Path) -> None:
    """Δ.7 — if `path` is a `.py` file under `content/notes/`,
    clear the corpus_index fingerprint cache so the next indexed
    query picks up the write without waiting for the Δ.6 TTL to
    expire. Lazy-import to avoid startup-order circular. Best-
    effort: failure is silently swallowed (1s of stale data is
    graceful degradation; failing the editor save is not). Path
    discrimination via `path.parent.name == "notes"` rejects
    lookalike directories like `notes_backup/`.
    """
    try:
        if path.suffix == ".py" and path.parent.name == "notes":
            from scripts.core import corpus_index

            corpus_index.invalidate()
            # Also drop the load_notes parse cache: a rewrite within the
            # same 1s mtime-resolution window keeps (path, mtime_ns)
            # unchanged, so _load_notes_cached would otherwise serve the
            # stale parse despite the corpus_index invalidation above.
            clear_load_notes_cache()
            # mint-9 #10: compute_matrix is a maxsize=1 singleton derived from
            # the notes corpus; a notes-file write must also drop it or the
            # /matrix + /customize count grids serve stale numbers until the
            # web process restarts (api/editions + api/customize already clear
            # it after their own edits — this covers the editor save path too).
            from scripts.core import matrix as _matrix

            _matrix.compute_matrix.cache_clear()
            # v0.1.0 audit Phase 2 (the mint-9 #10 twin): edition_stats's
            # resolved_note_counts is an lru_cache keyed on an edition signature
            # that does NOT include the notes-corpus mtime, so a runtime notes
            # write leaves the baked front-matter counts (copyright / legend /
            # "Your Edition" pages) stale until restart. Drop it here too —
            # edition_stats never imports notes_io, so this is DAG-safe.
            from scripts.core import edition_stats as _edition_stats

            _edition_stats.cache_clear()
    except Exception:  # noqa: BLE001
        pass


def ensure_backup(
    path: Path | str,
    *,
    backup_dir: Path | None = None,
    max_keep: int = 50,
) -> Path | None:
    """Snapshot *path* into a .backups/ subdirectory before it is mutated.

    Returns the path of the backup, or ``None`` if the source file does
    not exist (nothing to back up). Default backup directory is
    ``<path.parent>/.backups/``.

    Backup filenames embed an ISO-8601 UTC timestamp so multiple backups
    of the same file sort lexicographically. With ``max_keep`` set, only
    the most recent N backups for each file stem are retained.
    """
    path = Path(path)
    if not path.exists():
        return None
    backup_dir = Path(backup_dir) if backup_dir else (path.parent / ".backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"{path.stem}.{timestamp}{path.suffix}.bak"
    shutil.copy2(path, backup_path)

    if max_keep is not None and max_keep > 0:
        existing = sorted(backup_dir.glob(f"{path.stem}.*{path.suffix}.bak"))
        for old in existing[:-max_keep]:
            try:
                old.unlink()
            except OSError:
                pass

    return backup_path


def load_notes_from_text(text: str):
    """Parse a notes-module source string and return the ``NOTES`` list.

    Returns ``None`` on syntax error, or ``[]`` if no NOTES assignment
    is found. Uses ``ast.literal_eval`` so only literal data passes
    through — code in the module is never executed.

    Consolidated from 5 byte-identical duplicates (Phase β.2).
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "NOTES":
                    try:
                        return ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return None
    return []


@functools.lru_cache(maxsize=256)
def _load_notes_cached(path_str: str, mtime_ns: int):
    """Cached parse of a notes file. The cache key includes mtime_ns, so
    if the file is rewritten the cache automatically invalidates."""
    try:
        text = Path(path_str).read_text(encoding="utf-8")
    except OSError:
        return None
    return load_notes_from_text(text)


def load_notes(path: Path | str):
    """Read a notes-module from disk and return the ``NOTES`` list.

    Convenience wrapper over ``load_notes_from_text``. Returns ``None``
    on read failure, ``[]`` if no NOTES assignment found.

    Cached by (path, mtime). Repeat calls in a single process avoid
    re-reading and re-parsing — substantial speedup for tools that
    sweep all 87 books (dashboard, citation_index, glossary, etc.).
    Cache invalidates automatically when the file is rewritten because
    mtime changes.
    """
    path = Path(path)
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        return None
    return _load_notes_cached(str(path), mtime_ns)


def clear_load_notes_cache() -> None:
    """Drop the entire load_notes cache. Useful in tests or after bulk
    rewrites if mtime resolution proves insufficient."""
    _load_notes_cached.cache_clear()

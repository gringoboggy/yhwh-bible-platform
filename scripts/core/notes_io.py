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

    Returns the resolved Path that was written.
    """
    path = Path(path)
    # Sibling tempfile in the same directory so os.replace stays on the
    # same filesystem (cross-fs renames are not atomic).
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(text, encoding=encoding)
        os.replace(tmp, path)
    except Exception:
        # Best-effort cleanup; never leave a stray .tmp behind.
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    return path


def atomic_write_bytes(path: Path | str, data: bytes) -> Path:
    """Binary counterpart of atomic_write — same atomicity guarantee.

    Used by the cover-upload endpoint (Phase π.4-B) and any other
    binary writer. Same .tmp + os.replace dance.
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
    return path


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

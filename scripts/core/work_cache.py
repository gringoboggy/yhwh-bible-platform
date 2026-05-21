"""Content-hash result cache for the at-scale / vision passes.

Keyed by ``sha256`` of the inputs (model + system prompt + per-item text +
image hashes), so a re-run skips every input that hasn't changed and only
pays the API for what actually changed. Makes iterative marathon re-runs
near-free.

Stdlib only (``hashlib`` + ``sqlite3``), per CLAUDE_PROJECT_RULES §10.
In-memory by default; pass a path to persist across runs.

Typical use in a driver::

    cache = WorkCache("dev/cache/vision.sqlite")
    key = key_for(model, system_prompt, verse_text, *image_hashes)
    result_json, hit = cache.get_or_compute(key, lambda: client.analyze(...))
"""

from __future__ import annotations

import hashlib
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Callable, Optional


def key_for(*parts: object) -> str:
    """Stable sha256 hex over *parts*.

    A NUL separator after each part keeps ``("a", "b")`` distinct from
    ``("ab",)``. ``repr`` is used so ints/bytes/strings all hash
    deterministically; pass an image's own digest (not raw bytes) for
    large binary inputs.
    """
    h = hashlib.sha256()
    for p in parts:
        h.update(repr(p).encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


class WorkCache:
    """A tiny key→value SQLite cache."""

    def __init__(self, db_path: str = ":memory:") -> None:
        # check_same_thread=False + a mutex makes one shared connection safe
        # to use from parallel_map's worker threads (access is serialized by
        # the lock; writes are short). Without this, a cache-wrapped
        # completion_fn called from a worker thread would raise
        # "SQLite objects created in a thread can only be used in that thread".
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT NOT NULL, created_at TEXT NOT NULL)"
            )
            self._conn.commit()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            row = self._conn.execute("SELECT value FROM cache WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    def put(self, key: str, value: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, created_at) VALUES (?, ?, ?)",
                (key, value, datetime.now(timezone.utc).isoformat(timespec="seconds")),
            )
            self._conn.commit()

    def get_or_compute(self, key: str, compute_fn: Callable[[], str]) -> tuple[str, bool]:
        """Return ``(value, hit)``. On miss, run *compute_fn*, store, return
        ``(value, False)``. On hit, return ``(cached, True)`` without calling
        *compute_fn*."""
        cached = self.get(key)
        if cached is not None:
            return cached, True
        value = compute_fn()
        self.put(key, value)
        return value, False

    def close(self) -> None:
        self._conn.close()

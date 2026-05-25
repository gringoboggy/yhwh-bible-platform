"""Wave 4 W4.2 — process-wide concurrent-build admission gate.

The desktop app serves builds on a ThreadingHTTPServer. A heavy in-process
build (the frozen path copies the ~122 MB base, filters, then zips) must not
run twice concurrently or it doubles peak memory + disk churn on the user's
machine. This gate caps concurrent builds at ``YHWH_MAX_CONCURRENT_BUILDS``
(default 1). A build request that can't get a slot raises ``BuildBusyError``; the
HTTP layer translates that to 409 so a second BUILD click gets a clean
"already building" response instead of starting a second build.

Stdlib only (threading / contextlib / os), per CLAUDE_PROJECT_RULES §10.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Iterator
from contextlib import contextmanager

_DEFAULT_MAX = 1
_ENV_VAR = "YHWH_MAX_CONCURRENT_BUILDS"

_lock = threading.Lock()
_semaphore: threading.BoundedSemaphore | None = None
_max = 0
_active = 0


class BuildBusyError(Exception):
    """All build slots are occupied — do not start another build right now.

    The HTTP layer catches this and returns 409 so a second concurrent build
    request is rejected cleanly rather than starting a second heavy build."""


def _read_max_from_env() -> int:
    raw = os.environ.get(_ENV_VAR)
    if raw is None:
        return _DEFAULT_MAX
    try:
        value = int(raw)
    except ValueError:
        return _DEFAULT_MAX
    return value if value >= 1 else _DEFAULT_MAX


def reset(max_slots: int | None = None) -> None:
    """(Re)initialize the gate. ``max_slots=None`` reads the env var (default
    1). Production calls this lazily on first use; tests call it after setting
    the env to rebuild the gate deterministically."""
    global _semaphore, _max, _active
    with _lock:
        _max = max_slots if max_slots is not None else _read_max_from_env()
        _semaphore = threading.BoundedSemaphore(_max)
        _active = 0


def _ensure() -> threading.BoundedSemaphore:
    if _semaphore is None:
        reset()
    assert _semaphore is not None
    return _semaphore


def max_slots() -> int:
    """The configured concurrent-build limit."""
    _ensure()
    return _max


def active_count() -> int:
    """How many build slots are currently held."""
    _ensure()
    with _lock:
        return _active


@contextmanager
def build_slot() -> Iterator[None]:
    """Hold a build slot for the duration of the block, or raise ``BuildBusyError``
    immediately if none is free.

    Non-blocking by design: a second concurrent build request is rejected (so
    the UI can say "already building"), never silently queued behind a
    minutes-long build."""
    sem = _ensure()
    if not sem.acquire(blocking=False):
        raise BuildBusyError("a build is already running")
    global _active
    with _lock:
        _active += 1
    try:
        yield
    finally:
        with _lock:
            _active -= 1
        sem.release()

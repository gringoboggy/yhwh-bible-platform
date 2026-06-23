"""gap-4 (round-11) — corpus_index reader/closer use-after-close race.

The shared process-global ``_CACHED_CONN`` was read + ``execute()``'d OUTSIDE
``_CONN_LOCK`` by every query helper, while ``invalidate()`` / ``rebuild()`` /
``_build_to()`` close that same handle under the lock — a use-after-close
window under the ThreadingHTTPServer + the build ``ThreadPoolExecutor``. The
fix routes every reader through ``_read_cursor()``, which holds ``_CONN_LOCK``
for the WHOLE read (open/swap + execute + fetch), so a close can never overlap
an in-flight execute.
"""

from __future__ import annotations

import threading

import scripts.core.corpus_index as ci


def test_read_cursor_holds_conn_lock_for_the_whole_read():
    # Deterministic invariant (no timing): the lock is held for the entire
    # read and released on exit.
    assert not ci._CONN_LOCK.locked()
    with ci._read_cursor() as conn:
        assert ci._CONN_LOCK.locked(), "reader must hold _CONN_LOCK during the read"
        conn.execute("SELECT COUNT(*) FROM notes").fetchone()
    assert not ci._CONN_LOCK.locked(), "lock must release after the read"


def test_close_blocks_until_reader_releases_the_lock():
    # invalidate() closes _CACHED_CONN under _CONN_LOCK. While a reader holds
    # the lock via _read_cursor(), a concurrent close MUST block until the
    # reader exits — that is exactly the window the gap-4 fix closes.
    started = threading.Event()
    closed = threading.Event()

    def closer():
        started.wait(2)
        ci.invalidate()  # blocks on _CONN_LOCK until the reader releases it
        closed.set()

    t = threading.Thread(target=closer, daemon=True)
    t.start()
    with ci._read_cursor() as conn:
        started.set()
        # the closer must NOT be able to finish its close while we hold the read
        assert not closed.wait(0.25), "invalidate() closed the conn mid-read (gap-4 race)"
        conn.execute("SELECT COUNT(*) FROM notes").fetchone()
    t.join(2)
    assert closed.is_set(), "invalidate() should complete once the reader releases the lock"

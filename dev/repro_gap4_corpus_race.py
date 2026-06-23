#!/usr/bin/env python3
"""Empirical reproduction harness for the gap-4 ``corpus_index`` SQLite
use-after-close race (round-11 / round-12 seed #1).

The round-11 sweep found 18 sites where a process-global
``_CACHED_CONN = sqlite3.connect(..., check_same_thread=False)`` was ``.execute()``-ed
*outside* ``_CONN_LOCK`` while ``invalidate()`` / ``rebuild()`` / ``_build_to()`` could
close that same handle under the lock. WIN's fix routes every reader through
``_read_cursor()`` (a context manager that holds ``_CONN_LOCK`` for the WHOLE read —
open/swap + ``execute`` + ``fetch``), so a concurrent close can no longer pull the
handle out from under an in-flight ``execute()``. Two deterministic unit tests guard
it, but it was never reproduced under real concurrent load.

This harness drives that load. It models the build's ``ThreadPoolExecutor(max_workers=5)``
matrix-read fan-out (``compute_matrix_indexed`` + ``count_by_kind`` both go through
``_read_cursor()``) running concurrently with a writer thread that repeatedly calls
``invalidate()`` (which closes the cached connection under ``_CONN_LOCK``).

  --mode fixed  : readers use the real query helpers (``_read_cursor()``)  → expect 0 errors.
  --mode legacy : readers use the unguarded ``connection().execute()`` path, with a
                  widened window between handle-fetch and execute → expect the race to
                  fire (sqlite3.ProgrammingError "Cannot operate on a closed database").
                  This shows the bug is real and the fix is load-bearing.
  --mode both   : run both and contrast (default).

It is READ-ONLY w.r.t. the corpus: ``invalidate()`` only drops the cached connection +
the derived-index fingerprint, forcing a rebuild from the SAME ``content/notes`` — it
never edits content. Findings-only; not a pytest (WIN promotes any durable assertion
into ``tests/``).

Usage:
    python dev/repro_gap4_corpus_race.py [--readers 5] [--seconds 6]
                                         [--invalidate-ms 80] [--mode both]
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import threading
import time
import traceback
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.core import corpus_index  # noqa: E402


class _Counters:
    def __init__(self) -> None:
        self.reads = 0
        self.invalidations = 0
        self.errors: list[str] = []
        self.lock = threading.Lock()

    def add_reads(self, n: int) -> None:
        with self.lock:
            self.reads += n

    def add_invalidation(self) -> None:
        with self.lock:
            self.invalidations += 1

    def add_error(self, e: BaseException) -> None:
        with self.lock:
            self.errors.append(f"{type(e).__name__}: {e}")


def _fixed_reader(stop: threading.Event, c: _Counters) -> None:
    """The real read path: every helper goes through ``_read_cursor()``."""
    local = 0
    while not stop.is_set():
        try:
            corpus_index.compute_matrix_indexed()
            corpus_index.count_by_kind()
            local += 1
        except Exception as e:  # noqa: BLE001 — we WANT to catch the race here
            c.add_error(e)
    c.add_reads(local)


def _legacy_reader(stop: threading.Event, c: _Counters) -> None:
    """The unguarded path the fix replaced: fetch the shared handle, then
    ``.execute()`` on it OUTSIDE ``_CONN_LOCK``. A micro-pause widens the
    use-after-close window so the race is observable in a short run."""
    local = 0
    while not stop.is_set():
        try:
            conn = corpus_index.connection()
            # The window the fix closes: a concurrent invalidate()/rebuild() can
            # close `conn` between here and the execute() below.
            time.sleep(0)  # yield the GIL — widen the window without a real sleep
            conn.execute("SELECT COUNT(*) FROM notes").fetchall()
            local += 1
        except Exception as e:  # noqa: BLE001
            c.add_error(e)
    c.add_reads(local)


def _invalidator(stop: threading.Event, c: _Counters, period_s: float) -> None:
    """Writer: close the cached connection under ``_CONN_LOCK`` on a cadence,
    forcing every reader's next call to reopen — the close-vs-read pressure."""
    while not stop.is_set():
        try:
            corpus_index.invalidate()
            c.add_invalidation()
        except Exception as e:  # noqa: BLE001
            c.add_error(e)
        stop.wait(period_s)


def _run(mode: str, readers: int, seconds: float, invalidate_ms: float) -> _Counters:
    c = _Counters()
    stop = threading.Event()
    reader_fn = _legacy_reader if mode == "legacy" else _fixed_reader

    # Warm the index once (first call triggers the full rebuild) before timing.
    corpus_index.compute_matrix_indexed()

    threads = [threading.Thread(target=reader_fn, args=(stop, c), name=f"reader-{i}") for i in range(readers)]
    threads.append(threading.Thread(target=_invalidator, args=(stop, c, invalidate_ms / 1000.0), name="invalidator"))
    for t in threads:
        t.start()
    time.sleep(seconds)
    stop.set()
    for t in threads:
        t.join(timeout=10)
    return c


def _report(mode: str, c: _Counters, *, expect_clean: bool) -> bool:
    print(f"\n── mode={mode} ──")
    print(f"  reads completed : {c.reads}")
    print(f"  invalidations   : {c.invalidations}")
    print(f"  errors          : {len(c.errors)}")
    for msg in c.errors[:6]:
        print(f"    • {msg}")
    if len(c.errors) > 6:
        print(f"    … +{len(c.errors) - 6} more")
    if expect_clean:
        ok = len(c.errors) == 0
        print(
            f"  VERDICT: {'PASS — _read_cursor() held under load (0 use-after-close)' if ok else 'FAIL — the fixed path raised; investigate'}"
        )
        return ok
    # legacy: errors here are EXPECTED (they demonstrate the race the fix prevents)
    race = sum(1 for m in c.errors if "closed database" in m or "ProgrammingError" in m)
    print(f"  use-after-close errors (race fired): {race}")
    print("  NOTE: errors on the legacy path are EXPECTED — they show the bug the fix closes.")
    return True


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Empirical gap-4 corpus_index race repro")
    ap.add_argument("--readers", type=int, default=5, help="reader threads (default 5 = the build pool size)")
    ap.add_argument("--seconds", type=float, default=6.0, help="duration per mode")
    ap.add_argument("--invalidate-ms", type=float, default=80.0, help="writer invalidate() cadence (ms)")
    ap.add_argument("--mode", choices=["fixed", "legacy", "both"], default="both")
    args = ap.parse_args(argv)

    print(f"gap-4 race repro · readers={args.readers} · {args.seconds}s/mode · invalidate every {args.invalidate_ms}ms")
    print(f"sqlite3 {sqlite3.sqlite_version} · index = {corpus_index._index_path()}")

    ok = True
    if args.mode in ("fixed", "both"):
        ok &= _report("fixed", _run("fixed", args.readers, args.seconds, args.invalidate_ms), expect_clean=True)
    if args.mode in ("legacy", "both"):
        _report("legacy", _run("legacy", args.readers, args.seconds, args.invalidate_ms), expect_clean=False)

    print("\nDONE." + ("" if ok else "  (fixed path raised — see above)"))
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(2)

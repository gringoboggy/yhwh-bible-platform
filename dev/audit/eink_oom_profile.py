#!/usr/bin/env python3
"""P1 — tracemalloc + RSS profiler for the eink build OOM.

Runs ``build_one`` IN-PROCESS (the peak lives there — `build_epub.py`'s zip step is a
subprocess that streams per-file, so it is not the hog) under tracemalloc, with a sampler
thread that keeps the tracemalloc snapshot taken at the highest observed memory. On
MemoryError it captures the snapshot at the crash point. Prints: peak traced bytes, peak
RSS, top allocators by file:line at peak, and the single largest resident structure.

Findings-only — does NOT edit source; build output goes to a throwaway dir. Usage:
    .venv/bin/python dev/audit/eink_oom_profile.py ethiopian-tewahedo --target-reader eink
    .venv/bin/python dev/audit/eink_oom_profile.py catholic-study --target-reader eink   # smaller fallback
"""

from __future__ import annotations

import argparse
import resource
import sys
import threading
import time
import tracemalloc
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# macOS ru_maxrss is BYTES; Linux is KiB. Normalize to bytes.
_RSS_UNIT = 1 if sys.platform == "darwin" else 1024


def _rss_bytes() -> int:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * _RSS_UNIT


class _Sampler(threading.Thread):
    """Poll memory; keep the tracemalloc snapshot from the highest point seen."""

    def __init__(self, interval: float = 0.25) -> None:
        super().__init__(daemon=True)
        self.interval = interval
        self.stop = threading.Event()
        self.peak_current = 0
        self.peak_rss = 0
        self.peak_snapshot: tracemalloc.Snapshot | None = None
        self._last_snap = 0.0

    def run(self) -> None:
        while not self.stop.is_set():
            cur, _ = tracemalloc.get_traced_memory()
            self.peak_rss = max(self.peak_rss, _rss_bytes())
            now = time.monotonic()
            # snapshot on a new high (>40 MB jump), throttled to >=0.8s apart
            if cur > self.peak_current + 40 * 1024 * 1024 and now - self._last_snap > 0.8:
                self.peak_current = cur
                self.peak_snapshot = tracemalloc.take_snapshot()
                self._last_snap = now
            elif cur > self.peak_current:
                self.peak_current = cur
            self.stop.wait(self.interval)


def _report(sampler: _Sampler, where: str) -> None:
    cur, peak = tracemalloc.get_traced_memory()
    mb = 1024 * 1024
    print(f"\n===== eink OOM profile ({where}) =====")
    print(f"tracemalloc peak (this process): {peak / mb:.0f} MB")
    print(f"sampler peak current           : {sampler.peak_current / mb:.0f} MB")
    print(f"peak RSS (ru_maxrss)           : {sampler.peak_rss / mb:.0f} MB")
    snap = sampler.peak_snapshot or tracemalloc.take_snapshot()
    print("\n-- top 25 allocators by file:line at peak --")
    for i, stat in enumerate(snap.statistics("lineno")[:25], 1):
        fr = stat.traceback[0]
        f = fr.filename.replace(str(REPO) + "/", "")
        print(f"{i:2}. {stat.size / mb:8.1f} MB  {stat.count:>9,} blocks  {f}:{fr.lineno}")
    print("\n-- top 10 by traceback (largest resident structures, with call path) --")
    for i, stat in enumerate(snap.statistics("traceback")[:10], 1):
        f = stat.traceback[0].filename.replace(str(REPO) + "/", "")
        print(f"{i:2}. {stat.size / mb:8.1f} MB  {f}:{stat.traceback[0].lineno}")
        for line in stat.traceback.format()[-4:]:
            print(f"        {line}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("edition_id", nargs="?", default="ethiopian-tewahedo")
    ap.add_argument("--target-reader", default="eink")
    ap.add_argument("--frames", type=int, default=25)
    args = ap.parse_args()

    from scripts import build_edition
    from scripts.core import config

    all_kinds = config.load_kinds()
    out = REPO / "tmp" / "oom-profile-out"
    out.mkdir(parents=True, exist_ok=True)

    tracemalloc.start(args.frames)
    sampler = _Sampler()
    sampler.start()
    print(f"profiling build_one({args.edition_id!r}, target_reader={args.target_reader!r}, force=True) ...")
    t0 = time.perf_counter()
    try:
        build_edition.build_one(
            args.edition_id,
            out,
            "v27",
            all_kinds,
            dry_run=False,
            force=True,
            target_reader=args.target_reader,
        )
        sampler.stop.set()
        sampler.join(timeout=2)
        print(f"build completed in {time.perf_counter() - t0:.0f}s")
        _report(sampler, "completed")
        return 0
    except MemoryError:
        sampler.stop.set()
        # capture the allocation state at the crash
        sampler.peak_snapshot = tracemalloc.take_snapshot()
        print(f"\n!!! MemoryError after {time.perf_counter() - t0:.0f}s — capturing crash snapshot")
        _report(sampler, "CRASHED (MemoryError)")
        return 2
    except Exception as e:  # noqa: BLE001 — profiler must report any failure
        sampler.stop.set()
        print(f"\n!!! build raised {type(e).__name__}: {e}")
        _report(sampler, f"raised {type(e).__name__}")
        return 3


if __name__ == "__main__":
    sys.exit(main())

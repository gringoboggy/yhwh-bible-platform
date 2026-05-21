"""Tests for scripts/core/parallel.py — bounded parallel map.

The at-scale passes are I/O-bound (API calls), so a thread pool gives
5-10x wall-clock with the GIL released during network waits. This is the
reusable primitive; drivers adopt it for the 31K-verse runs.
"""

import threading

import pytest


def test_parallel_map_preserves_order():
    from scripts.core.parallel import parallel_map

    out = parallel_map(lambda x: x * 2, list(range(20)), workers=5)
    assert out == [x * 2 for x in range(20)]


def test_parallel_map_runs_concurrently():
    from scripts.core.parallel import parallel_map

    # A Barrier of N only releases when N threads reach it. If parallel_map
    # ran serially, the first task would wait alone and the barrier would
    # time out (BrokenBarrierError). Completing proves true concurrency.
    n = 4
    barrier = threading.Barrier(n, timeout=5)

    def fn(x):
        barrier.wait()
        return x

    out = parallel_map(fn, list(range(n)), workers=n)
    assert sorted(out) == list(range(n))


def test_parallel_map_single_worker():
    from scripts.core.parallel import parallel_map

    assert parallel_map(lambda x: x + 1, [1, 2, 3], workers=1) == [2, 3, 4]


def test_parallel_map_empty():
    from scripts.core.parallel import parallel_map

    assert parallel_map(lambda x: x, [], workers=4) == []


def test_parallel_map_propagates_exceptions():
    from scripts.core.parallel import parallel_map

    def boom(x):
        if x == 2:
            raise ValueError("boom")
        return x

    with pytest.raises(ValueError, match="boom"):
        parallel_map(boom, [1, 2, 3], workers=3)

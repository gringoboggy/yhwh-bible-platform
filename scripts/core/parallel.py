"""Bounded parallel map for I/O-bound at-scale passes.

The ``run_*_at_scale.py`` drivers issue thousands of independent API calls.
Those are I/O-bound — the GIL is released during the network wait — so a
``ThreadPoolExecutor`` gives near-linear wall-clock speedup (5-10x on the
31K-verse passes) with no process overhead. The Anthropic SDK client is
thread-safe and its connection pool is shared.

This is the reusable primitive. A driver adopts it by replacing its
per-item loop:

    results = parallel_map(lambda v: detector.detect(*v), verses, workers=8)

Cost guards stay in the driver (the work is the same; only the scheduling
changes). Keep ``workers`` modest (4-8) to respect API rate limits — the
SDK's built-in retry handles the occasional 429.

Stdlib only (``concurrent.futures``), per CLAUDE_PROJECT_RULES §10.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def parallel_map(
    fn: Callable[[T], R],
    items: Iterable[T],
    *,
    workers: int = 4,
) -> list[R]:
    """Apply *fn* to each item across up to *workers* threads.

    Results are returned in **input order** regardless of completion order.
    The first exception raised by any item propagates (after the pool drains
    on context exit) — wrap *fn* to degrade gracefully if you'd rather
    collect partial results, mirroring the at-scale clients that already
    return ``[]`` on per-item failure.

    ``workers <= 1`` runs serially (no pool overhead). Empty input returns
    ``[]``.
    """
    materialized = list(items)
    if not materialized:
        return []
    if workers <= 1:
        return [fn(x) for x in materialized]

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(fn, x) for x in materialized]
        # .result() in submission order preserves input order and re-raises
        # the first failing item's exception.
        return [f.result() for f in futures]

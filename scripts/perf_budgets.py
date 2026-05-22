"""ω.13 — performance budgets for hot paths.

Defines a mapping of named hot-path operations to their target
elapsed-time budget and exposes a tiny `measure()` / `assert_under_budget()`
pair the test suite uses to enforce them. The shape mirrors the
§15 Tier-3 contract: continuous structural enforcement runs on
every test pass; if any hot path exceeds its budget the test
fails, surfacing the regression before it ships.

Budgets here are CALIBRATED HEADROOM, not aspiration. Measured
2026-05-09 against the 51K-note corpus on a developer machine:

- `notes_io.load_notes(gen)` ≈ 115 ms cold (Genesis is the
  largest book), 0.2 ms warm. Budget: 250 ms (~2× headroom).
- `notes_io.load_notes(jud)` ≈ 4 ms cold (one-chapter book).
  Same 250 ms budget covers both.
- `api_matrix()` cold ≈ 2400 ms (walks every note in every
  edition × kind permutation), 0.4 ms warm. Budget: 3000 ms
  cold (~25 % headroom; the underlying work is unavoidable
  unless we add a per-book index), 50 ms cached.
- `api_search_notes("Hebrew")` ≈ 2500 ms (full 51K-corpus
  walk). Budget: 3000 ms — same shape as api_matrix.cold.
- `api_customize_data()` ≈ 35 ms. Budget: 500 ms.
- `_parse_yaml_records(editions.yaml)` ≈ 6 ms. Budget: 50 ms.
- `verse_of_day()` ≈ 12 ms. Budget: 200 ms.

Treat budget violations as bugs, not "needs more headroom" —
double-check the lru_cache invalidation, the file_signature
fingerprint, and the mtime-cache miss patterns before bumping
the budget.

Per CLAUDE_PROJECT_RULES §10 ("Standard library only"): no
external profiling library. `time.perf_counter()` is the only
clock we need.
"""

from __future__ import annotations

import time
from typing import Any
from collections.abc import Callable


# ----------------------------------------------------------------------
# Budget table — named hot paths → seconds.
#
# Add a new entry here (alongside the matching test in tests/test_perf.py)
# when shipping a new feature whose latency the user can perceive.
# Cold + cached pairs share a stem to keep them visually grouped.
# ----------------------------------------------------------------------

BUDGETS: dict[str, float] = {
    # Core data loaders — single source of truth for everything else
    "notes_io.load_notes(book)": 0.250,  # 250 ms
    "config._parse_yaml_records(editions)": 0.050,  # 50 ms
    # Aggregate / multi-file loaders
    "config.load_editions": 0.050,  # 50 ms
    "config.load_kinds": 0.050,  # 50 ms
    # API endpoints — operator-perceptible
    # `api_matrix.cold` walks every note in every edition × kind
    # permutation. The underlying work is unavoidable until a
    # per-book index ships; budget reflects measured + headroom.
    "api_matrix.cold": 3.000,  # 3 s
    "api_matrix.cached": 0.050,  # 50 ms
    "api_customize_data": 0.500,  # 500 ms
    # Same shape as api_matrix.cold — full-corpus walk.
    "api_search_notes": 3.000,  # 3 s
    "verse_of_day": 0.200,  # 200 ms
    # Build-pipeline reading-plans inject (ψ.19.1)
    "inject_reading_plans_page": 0.100,  # 100 ms
    # Recovery CLI
    "recover.list_backups": 0.050,  # 50 ms
    "recover.verify_yaml": 0.100,  # 100 ms
}


# ----------------------------------------------------------------------
# Public API — measure + enforce
# ----------------------------------------------------------------------


def measure(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, float]:
    """Run `fn(*args, **kwargs)` and return ``(result, elapsed_seconds)``.

    Uses ``time.perf_counter`` for the highest-resolution clock the
    stdlib offers. Pure helper; no logging side-effects.
    """
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return result, elapsed


def assert_under_budget(name: str, elapsed_s: float, *, multiplier: float = 1.0) -> None:
    """Raise ``AssertionError`` if `elapsed_s` exceeds
    ``BUDGETS[name] * multiplier``.

    `multiplier` lets tests opt for a tighter or more-relaxed gate
    around the canonical budget — for example, the cached path can
    run with ``multiplier=0.1`` to catch unexpected cache misses.
    """
    budget = BUDGETS.get(name)
    if budget is None:
        raise KeyError(f"unknown budget name {name!r}; add it to scripts/perf_budgets.py:BUDGETS")
    threshold = budget * multiplier
    if elapsed_s > threshold:
        raise AssertionError(
            f"perf budget violation: {name} took "
            f"{elapsed_s * 1000:.1f} ms (budget {threshold * 1000:.1f} ms; "
            f"multiplier {multiplier}× of base {budget * 1000:.1f} ms)"
        )


def check_budget(name: str, elapsed_s: float, *, multiplier: float = 1.0) -> dict:
    """Non-raising variant of `assert_under_budget` for the linter
    composition path. Returns a dict envelope with `pass` /
    `elapsed_ms` / `budget_ms` / `over_by_ms` for easy reporting.
    """
    budget = BUDGETS.get(name)
    if budget is None:
        return {
            "name": name,
            "status": "unknown_name",
            "elapsed_ms": elapsed_s * 1000,
        }
    threshold = budget * multiplier
    return {
        "name": name,
        "status": "pass" if elapsed_s <= threshold else "fail",
        "elapsed_ms": round(elapsed_s * 1000, 2),
        "budget_ms": round(threshold * 1000, 2),
        "over_by_ms": round((elapsed_s - threshold) * 1000, 2) if elapsed_s > threshold else 0,
    }


def list_budgets() -> list[dict]:
    """Return every named budget as a list of
    ``{name, budget_ms}`` dicts. Used by the operator-facing
    PERF_BUDGETS.md and the optional preflight integration."""
    return [{"name": name, "budget_ms": round(budget_s * 1000, 2)} for name, budget_s in sorted(BUDGETS.items())]

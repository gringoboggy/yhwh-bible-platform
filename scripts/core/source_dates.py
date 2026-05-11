"""ψ.37-A — circa-year lookup for note attributions.

Powers the time-traveling commentary filter: every note's `attribution`
string is mapped to a circa-year via prefix-match against
`content/source_dates.yaml`. The build pipeline uses the returned year
to filter notes against an edition's `time_filter_ceiling`.

Public API:
- ``lookup_year(attribution: str) -> int | None``
  Returns the source's circa-year for the longest matching prefix,
  or ``None`` for empty / unmatched attributions ("User original",
  "User paraphrase", and any source not yet catalogued).

- ``load_source_dates() -> list[dict]``
  Returns the raw list of {prefix, year, label, note?} entries from
  `content/source_dates.yaml`, sorted longest-prefix first for
  longest-prefix-wins matching.

Match semantics: longest prefix wins. The YAML lists entries in
longest-first order, but ``load_source_dates`` re-sorts defensively
in case a future edit adds entries in a different order.

Empty / unmatched attribution → ``None``. Callers interpret ``None``
as "contemporary / no fixed historical year" — the build pipeline's
filter pass treats those as failing any historical ceiling
(they ship only when no ceiling is set).
"""

from __future__ import annotations

import functools
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent.parent
SOURCE_DATES_PATH = REPO / "content" / "source_dates.yaml"


@functools.lru_cache(maxsize=1)
def load_source_dates() -> list[dict]:
    """Read `content/source_dates.yaml` and return the source list
    sorted longest-prefix-first.

    Cached for the life of the process. Call
    ``load_source_dates.cache_clear()`` after editing the YAML."""
    if not SOURCE_DATES_PATH.is_file():
        return []
    raw = yaml.safe_load(SOURCE_DATES_PATH.read_text(encoding="utf-8")) or {}
    sources = raw.get("sources", []) or []
    return sorted(sources, key=lambda s: -len(s.get("prefix", "")))


def lookup_year(attribution: str) -> int | None:
    """Map an attribution string to its source's circa-year.

    Returns the year as int, or ``None`` if the attribution is empty
    or doesn't match any catalogued prefix. Longest-prefix wins so
    catalogue entries can be ordered for clarity rather than
    correctness.
    """
    if not attribution:
        return None
    for entry in load_source_dates():
        prefix = entry.get("prefix") or ""
        if prefix and attribution.startswith(prefix):
            return entry.get("year")
    return None

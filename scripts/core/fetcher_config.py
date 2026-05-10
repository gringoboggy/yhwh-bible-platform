"""
fetcher_config.py — Load and validate `content/sources/_fetchers.json`.

This is the declarative source list consumed by ``scripts/fetch_sources.py``.
Phase υ.7 moved the previously-hard-coded URL + parser-kind constants out
of Python and into a JSON config so future PD sources can be added without
editing code (and so the `/sources` console — υ.1 — has a real schema to
read/write against).

Schema (version 1)::

    {
      "version": 1,
      "sources": [
        {
          "id":          "strongs_hebrew",        # unique stable identifier
          "name":        "Strong's Hebrew …",     # human label for UI / logs
          "cache_path":  "strongs_hebrew.json",   # relative to content/sources/
          "required":    true,                    # if true, fetch failure
                                                  # is fatal (non-zero exit)
          "license":     "...",                   # PD/CC notice (one paragraph)
          "candidates": [                         # tried in order; first
            {                                     # success wins
              "url":    "https://...",
              "parser": "strongs-hebrew-js"       # must be in KNOWN_PARSERS
            }
          ]
        },
        ...
      ]
    }

Public API:
    KNOWN_PARSERS                           — frozenset of valid parser names
    Candidate, Source, FetcherConfig        — frozen dataclasses
    FetcherConfigError                      — raised on validation failure
    load_fetcher_config(path=None)          — read + validate; returns FetcherConfig
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_FETCHER_CONFIG_PATH = _REPO_ROOT / "content" / "sources" / "_fetchers.json"

CONFIG_VERSION = 1

# Parser kinds the fetch flow knows how to dispatch. Must match the keys
# registered in scripts.fetch_sources.PARSERS. Keep this list and that
# registry in sync — the linter could enforce it as a follow-up if drift
# becomes an issue.
KNOWN_PARSERS: frozenset[str] = frozenset(
    {
        "strongs-hebrew-js",
        "strongs-greek-js",
        "tsk-zip-tsv",
        "json-topic-to-refs",
        "openbible-topics-tsv",
        "ccel-text",
    }
)


class FetcherConfigError(ValueError):
    """Raised when _fetchers.json is malformed, missing, or references
    an unknown parser kind."""


@dataclass(frozen=True)
class Candidate:
    """One upstream URL and the parser kind that knows how to ingest it."""

    url: str
    parser: str


@dataclass(frozen=True)
class Source:
    """One PD/CC reference corpus the platform caches under content/sources/.

    A source has 1+ candidate URLs; the fetcher tries them in order and
    keeps the first that succeeds. ``required=False`` means the platform
    stays usable without this source (Nave's Topical is the existing
    instance — its absence just disables NaveTopicalDetector)."""

    id: str
    name: str
    cache_path: str  # filename under content/sources/, not absolute
    required: bool
    license: str
    candidates: tuple[Candidate, ...]


@dataclass(frozen=True)
class FetcherConfig:
    version: int
    sources: tuple[Source, ...]

    def find(self, source_id: str) -> Source | None:
        """Look up a source by its `id`. Returns None if absent."""
        for s in self.sources:
            if s.id == source_id:
                return s
        return None


def load_fetcher_config(path: Path | None = None) -> FetcherConfig:
    """Read and validate `_fetchers.json`.

    Pass `path` to point at a different file (used by tests). Raises
    `FetcherConfigError` for any validation failure (missing file,
    malformed JSON, unknown parser, duplicate id, etc.)."""
    p = path or DEFAULT_FETCHER_CONFIG_PATH
    if not p.is_file():
        raise FetcherConfigError(
            f"_fetchers.json not found at {p}. Add it (see scripts/core/fetcher_config.py for the schema)."
        )
    try:
        with p.open(encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        raise FetcherConfigError(f"_fetchers.json is not valid JSON: {e}") from e

    return _validate_and_build(raw)


def _validate_and_build(raw: object) -> FetcherConfig:
    if not isinstance(raw, dict):
        raise FetcherConfigError("top level must be a JSON object")

    version = raw.get("version")
    if version != CONFIG_VERSION:
        raise FetcherConfigError(f"unsupported version {version!r} (this loader supports {CONFIG_VERSION})")

    sources_raw = raw.get("sources")
    if not isinstance(sources_raw, list):
        raise FetcherConfigError('"sources" must be a list')
    if not sources_raw:
        raise FetcherConfigError('"sources" must not be empty')

    seen_ids: set[str] = set()
    sources: list[Source] = []
    for i, s in enumerate(sources_raw):
        ctx = f"sources[{i}]"
        if not isinstance(s, dict):
            raise FetcherConfigError(f"{ctx}: must be an object")

        for field in ("id", "name", "cache_path", "license"):
            val = s.get(field)
            if not isinstance(val, str) or not val:
                raise FetcherConfigError(f"{ctx}: missing or empty string field {field!r}")

        # ξ.17 SEC-004 — `cache_path` flows into write paths
        # (`api_sources_cache_upload`, `api_sources_cache_clear`). A
        # tampered `_fetchers.json` (delivered via scenario bundle,
        # restore from backup, hand-edit) could otherwise direct
        # writes anywhere reachable from the cache dir. Validate
        # that the cache_path is a plain relative filename — no
        # path separators, no `..`, no absolute prefix, no
        # drive-letter prefix, no leading `~`. The same rule
        # `safe_path._check_string_safety` applies. Empty strings
        # already rejected above.
        cp = s["cache_path"]
        if "/" in cp or "\\" in cp:
            raise FetcherConfigError(f"{ctx}: cache_path must be a bare filename (got {cp!r})")
        if cp.startswith("~") or cp == "." or cp == "..":
            raise FetcherConfigError(f"{ctx}: cache_path may not be {cp!r}")
        if len(cp) >= 2 and cp[1] == ":" and cp[0].isalpha():
            raise FetcherConfigError(f"{ctx}: cache_path may not have a drive-letter prefix")
        if any(ord(c) < 0x20 for c in cp):
            raise FetcherConfigError(f"{ctx}: cache_path may not contain control characters")

        sid: str = s["id"]
        if sid in seen_ids:
            raise FetcherConfigError(f"{ctx}: duplicate source id {sid!r}")
        seen_ids.add(sid)

        if not isinstance(s.get("required"), bool):
            raise FetcherConfigError(f"{ctx}: 'required' must be a bool")

        cands_raw = s.get("candidates")
        if not isinstance(cands_raw, list) or not cands_raw:
            raise FetcherConfigError(f'{ctx}: "candidates" must be a non-empty list')

        cands: list[Candidate] = []
        for j, c in enumerate(cands_raw):
            cctx = f"{ctx}.candidates[{j}]"
            if not isinstance(c, dict):
                raise FetcherConfigError(f"{cctx}: must be an object")
            for field in ("url", "parser"):
                val = c.get(field)
                if not isinstance(val, str) or not val:
                    raise FetcherConfigError(f"{cctx}: missing or empty string field {field!r}")
            if c["parser"] not in KNOWN_PARSERS:
                raise FetcherConfigError(f"{cctx}: unknown parser {c['parser']!r}; known: {sorted(KNOWN_PARSERS)}")
            cands.append(Candidate(url=c["url"], parser=c["parser"]))

        sources.append(
            Source(
                id=sid,
                name=s["name"],
                cache_path=s["cache_path"],
                required=s["required"],
                license=s["license"],
                candidates=tuple(cands),
            )
        )

    return FetcherConfig(version=version, sources=tuple(sources))

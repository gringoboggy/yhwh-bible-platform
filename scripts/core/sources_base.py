"""
sources_base.py — shared foundation for the ``sources`` god-module split.

Holds the repo-root / sources-dir resolution, the ``SourceMissingError``
raised by every loader, and the legacy book-code alias normalization
used across the commentary loaders. Imported by every other ``sources_*``
module; depends on none of them (acyclic foundation).

Extracted verbatim from ``sources.py`` (module split 2026-05-26).
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SOURCES = _REPO_ROOT / "content" / "sources"


def _sources_dir() -> Path:
    """Resolve the sources/ directory through the ω.5 paths resolver
    (in-tree wins for dev; user_data_dir for installed builds; honors
    YHWH_CONTENT_ROOT and the testing override).

    Existing loader classes keep their PATH class attribute pointing
    at ``_SOURCES / "<file>.json"`` for back-compat with tests that
    monkeypatch PATH; ω.5.1+ rolling migration switches each loader
    to call ``_sources_dir()`` lazily so the resolver flows through.
    """
    from . import paths

    return paths.sources_dir()


class SourceMissingError(RuntimeError):
    """Raised when a source file is not cached. Hint: run fetch_sources.py."""


from .book_codes import BOOK_CODE_ALIASES as _BOOK_CODE_ALIASES
from .book_codes import canonical_book_code as _normalize_book_code

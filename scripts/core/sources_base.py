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


# ω.36 — Book-code aliases for legacy commentary JSONs.
#
# Historical commentary corpora (ethiopian / catholic / protestant /
# reformation / rabbinic JSONs) use 1990s-SBL short codes `joh` (John)
# and `ps` (Psalms). The canonical `content/books.yaml` registry uses
# OSIS-style `jhn` / `psa`. Without normalization, calls like
# `for_verse("jhn", 1, 1)` against an entry stored under `joh` return
# `[]` — silently dropping 119 Cyril-on-John + 2 Ephrem-on-Psalm-1
# entries from any reader that uses the canonical books.yaml code.
# Audit-C (2026-05-12) flagged this as CRITICAL-2.
#
# The alias map is applied SYMMETRICALLY — both at index-build time
# (stored keys are normalized to canonical codes) and at for_verse
# lookup time (query codes are normalized too). Either input form
# resolves to the canonical bucket.
_BOOK_CODE_ALIASES: dict[str, str] = {
    "joh": "jhn",  # John (legacy SBL short → OSIS canonical)
    "ps": "psa",  # Psalms (legacy SBL short → OSIS canonical)
    # ω.42 hygiene (γ.4.8 ship 2026-05-14) — resolves AUDIT_2026-05-13-DEEP
    # D-W2 / γ.4.9.D pre-existing project-level inconsistency: the
    # _BOOK_CODE_ALIASES_LONGFORM dict (further down this file) maps
    # "james" → "jas", but content/notes/jam.py is the actual notes-file
    # (no jas.py exists). Symmetric normalization here makes "jas"-typed
    # source-JSON entries resolve to "jam" at both index-build and lookup
    # time, matching the notes-file convention.
    "jas": "jam",  # James (SBL alias → notes-file canonical)
}


def _normalize_book_code(book: str) -> str:
    """Map legacy book codes to canonical books.yaml codes.
    Unknown codes pass through unchanged."""
    return _BOOK_CODE_ALIASES.get(book, book)

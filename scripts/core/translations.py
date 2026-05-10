"""scripts.core.translations — runtime query API for parallel-translation
data (Phase τ.1).

The on-disk store is laid out by ``scripts/extract_translation.py``:

    content/translations/
        <translation_id>/
            _meta.yaml           # license + source provenance
            <book_code>.py       # one module per book; defines VERSES list

This module provides the lookup surface that everything else in the
project uses. Today's only consumer is the verse-popup feature
(Phase ν.2.5-B), which on each clicked verse asks:

    get_verse(translation, book_code, ch, vs) → "In the beginning…"

But the API is general — diff views, alignment tools, and any future
"Strong's links into KJV" feature can use the same loader.

Loading is lazy (per-book) and cached (lru_cache on path + mtime),
mirroring ``scripts.core.notes_io`` so we get the same auto-
invalidation guarantees.

Parsing is via ``ast.literal_eval`` only — translation modules are
never executed as code, so a corrupted or hostile translation file
cannot run anything.
"""

from __future__ import annotations

import ast
import functools
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
TRANSLATIONS_DIR = REPO / "content" / "translations"


def _translations_dir() -> Path:
    """ω.5 paths-resolver entrypoint. Existing ``TRANSLATIONS_DIR``
    constant is preserved for back-compat; new call sites should
    prefer this function so they pick up dev/installed/test-override
    resolution automatically."""
    from . import paths

    return paths.translations_dir()


# ----------------------------------------------------------------------
# Per-book loading
# ----------------------------------------------------------------------


def _book_path(translation: str, book_code: str) -> Path:
    return TRANSLATIONS_DIR / translation / f"{book_code}.py"


def load_book_verses_from_text(text: str) -> list[tuple[int, int, str]] | None:
    """Parse a translation-module source string and return its VERSES list.

    Returns ``None`` on syntax error, ``[]`` if no VERSES assignment is
    present. Uses ``ast.literal_eval`` — never executes module code.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "VERSES":
                    try:
                        return ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return None
    return []


@functools.lru_cache(maxsize=256)
def _load_book_cached(path_str: str, mtime_ns: int):
    try:
        text = Path(path_str).read_text(encoding="utf-8")
    except OSError:
        return None
    return load_book_verses_from_text(text)


def _load_book(translation: str, book_code: str) -> list[tuple[int, int, str]] | None:
    """Read one translation book's VERSES list. ``None`` if no such
    file; ``[]`` if the file exists but is empty or malformed."""
    path = _book_path(translation, book_code)
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        return None
    return _load_book_cached(str(path), mtime_ns)


@functools.lru_cache(maxsize=256)
def _book_index(translation: str, book_code: str) -> dict[tuple[int, int], str] | None:
    """Build a (chapter, verse) → text dict for one book. Cached so
    every popup lookup after the first is a single dict access.
    """
    verses = _load_book(translation, book_code)
    if verses is None:
        return None
    return {(c, v): t for (c, v, t) in verses}


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def has_translation(translation: str) -> bool:
    """True if ``content/translations/<translation>/`` exists with at
    least one book module."""
    d = TRANSLATIONS_DIR / translation
    if not d.is_dir():
        return False
    return any(p.suffix == ".py" and p.name != "__init__.py" for p in d.iterdir())


def list_translations() -> list[str]:
    """Translation ids available on disk, sorted alphabetically."""
    if not TRANSLATIONS_DIR.is_dir():
        return []
    out = []
    for child in TRANSLATIONS_DIR.iterdir():
        if child.is_dir() and child.name != "sources" and has_translation(child.name):
            out.append(child.name)
    return sorted(out)


def has_book(translation: str, book_code: str) -> bool:
    """True if the per-book module file exists for this translation."""
    return _book_path(translation, book_code).is_file()


def get_verse(translation: str, book_code: str, chapter: int, verse: int) -> str | None:
    """Return the verse text, or ``None`` if missing.

    No partial matches; chapter and verse must match exactly. The
    one-translation-per-call shape is deliberate — the popup feature
    queries one translation per click, and a plural API would just
    push the choice back to the caller.
    """
    idx = _book_index(translation, book_code)
    if idx is None:
        return None
    return idx.get((chapter, verse))


def get_chapter(translation: str, book_code: str, chapter: int) -> list[tuple[int, str]]:
    """Return ``[(verse_number, text), …]`` for one chapter, in verse
    order. Empty list if the chapter is missing or the book is absent.
    """
    verses = _load_book(translation, book_code)
    if not verses:
        return []
    out = [(v, t) for (c, v, t) in verses if c == chapter]
    out.sort(key=lambda p: p[0])
    return out


def book_verse_count(translation: str, book_code: str) -> int:
    """Total verses in one book of one translation. 0 if missing."""
    verses = _load_book(translation, book_code)
    return len(verses) if verses else 0


def translation_meta(translation: str) -> dict | None:
    """Read the translation's _meta.yaml — title, license, provenance.

    Uses PyYAML if available, otherwise returns ``None`` (callers
    treat missing meta as "we have the data but no extra metadata").
    """
    p = TRANSLATIONS_DIR / translation / "_meta.yaml"
    if not p.is_file():
        return None
    try:
        import yaml
    except ImportError:
        return None
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8")) or None
    except yaml.YAMLError:
        return None


def clear_cache() -> None:
    """Drop loader caches. Useful in tests or after bulk re-extraction."""
    _load_book_cached.cache_clear()
    _book_index.cache_clear()

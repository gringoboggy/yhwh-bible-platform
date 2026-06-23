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

# Canonical book code → on-disk module stem when stores use legacy 2-letter
# filenames (geez-tewahedo-en/ex.py, amharic-en/ex.py). Additive only:
# if ``{code}.py`` exists it wins; alias applies only when the canonical
# file is absent (byte-stable for editions that already use exo.py).
_BOOK_FILE_ALIASES: dict[str, str] = {
    "exo": "ex",
}


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


def _resolve_book_stem(translation: str, book_code: str) -> str:
    """Return the ``.py`` stem for a book, applying legacy aliases when needed."""
    d = TRANSLATIONS_DIR / translation
    canonical = d / f"{book_code}.py"
    if canonical.is_file():
        return book_code
    alias = _BOOK_FILE_ALIASES.get(book_code)
    if alias and (d / f"{alias}.py").is_file():
        return alias
    return book_code


def _book_path(translation: str, book_code: str) -> Path:
    return TRANSLATIONS_DIR / translation / f"{_resolve_book_stem(translation, book_code)}.py"


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


def _load_book_attr_from_text(text: str, attr: str) -> str | None:
    """Parse a module-level string assignment (e.g. ``VERSIFICATION = "own"``)
    and return its value. ``None`` if absent, on syntax error, or if the value
    is not a string. Uses ``ast.literal_eval`` — never executes module code.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == attr:
                    try:
                        val = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return None
                    return val if isinstance(val, str) else None
    return None


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
def _book_index_cached(translation: str, book_code: str, mtime_ns: int) -> dict[tuple[int, int], str] | None:
    """Build a (chapter, verse) → text dict for one book. Cached so
    every popup lookup after the first is a single dict access.

    The cache key includes ``mtime_ns`` (mirroring ``_load_book_cached``),
    so a rewritten book file auto-invalidates this dict too — without it
    the index froze for the process lifetime and ``_load_book``'s own
    mtime freshness was defeated (a verse edited in the editor showed
    stale popup text until restart).
    """
    verses = _load_book(translation, book_code)
    if verses is None:
        return None
    return {(c, v): t for (c, v, t) in verses}


def _book_index(translation: str, book_code: str) -> dict[tuple[int, int], str] | None:
    """Resolve the book file's mtime and delegate to the cached builder."""
    try:
        mtime_ns = _book_path(translation, book_code).stat().st_mtime_ns
    except OSError:
        return None
    return _book_index_cached(translation, book_code, mtime_ns)


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


def verse_sort_key(v: object) -> tuple:
    """Order key for a verse coordinate that may be an ``int`` (canonical
    store) OR a string label. A ``VERSIFICATION == "own"`` store (the Geʽez
    Patrologia / Psalter lane) can emit lettered or Addition labels like
    ``"2a"`` or ``"B1"`` — calling ``max()`` / ``range()`` / ``int()`` on those
    raises. This comparator sorts numbered verses by ``(numeric prefix,
    suffix)`` (so ``1, 2, "2a", 3`` order correctly and a pure-int chapter is
    byte-identical to the old int sort), and any non-numbered label after, by
    text. Use this anywhere a verse value originates from ``get_chapter()`` /
    ``get_verse()`` / ``_load_book()`` instead of raw int arithmetic.
    """
    s = str(v)
    i = 0
    while i < len(s) and s[i].isdigit():
        i += 1
    if i:
        return (0, int(s[:i]), s[i:])
    return (1, 0, s)


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


def versification_of(translation: str, book_code: str) -> str:
    """Return the book's versification scheme: ``"own"`` or ``"canonical"``.

    Defaults to ``"canonical"`` when the per-book ``VERSIFICATION`` attribute
    is absent, so every existing translation/book (and the 9 KJV editions)
    is unchanged. ``"own"`` marks a store whose ``(chapter, verse)`` keys are
    the source's own numbering (e.g. the Ge'ez/LXX recension), NOT KJV-renumbered.
    """
    path = _book_path(translation, book_code)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return "canonical"
    val = _load_book_attr_from_text(text, "VERSIFICATION")
    return val if val in ("own", "canonical") else "canonical"


def clear_cache() -> None:
    """Drop loader caches. Useful in tests or after bulk re-extraction."""
    _load_book_cached.cache_clear()
    _book_index_cached.cache_clear()

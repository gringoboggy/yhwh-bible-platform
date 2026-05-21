"""Canonical (KJV/Masoretic) verse-count helper for ALL canonical books.

Single source of truth for "how many verses per chapter does this book
have in the canonical (KJV) enumeration." Derives from the KJV skeleton
at module-load — does NOT duplicate the data into hand-typed dicts.

Why this exists in addition to the per-book ``BOOK_VERSE_COUNTS`` dicts
in ``scripts/extract_parallel_pdf.py``:

- The ``extract_parallel_pdf.py`` dicts are OCR floors (used by
  ``renumber_against_floor`` for parallel-PDF ingest; sometimes
  tradition-specific so they're hand-typed).
- This module is the Phase-3 RENDER scaffolding (the test pin "rendered
  count <= canonical count" pattern; the canonical-ceiling reference).
  Derived from the KJV skeleton because that's the published canonical
  source.

Use ``canonical_count(book, chapter) -> int`` for a single chapter
count, ``canonical_total(book) -> int`` for the book-wide sum, and
``canonical_book_shape(book) -> dict[int, int]`` for the full mapping.
All three are cached.
"""

from __future__ import annotations

from functools import lru_cache

from .manuscript_collation import load_kjv_skeleton

# Every canonical book code in the Tewahedo 82-book superset (matches
# ``scripts.render_coverage._CANONICAL_BOOKS``). Books in this list
# MUST have a ``content/translations/kjv/<book>.py`` skeleton (the lint
# rule ``check_canonical_skeleton_coverage`` pins this).
# Books WITH a KJV / LXX skeleton in content/translations/kjv/. These
# are the canonical-anchored books — use ``canonical_count()`` for them.
# Tewahedo-distinctive books WITHOUT a KJV skeleton (mq1, mq2, mq3, 1en,
# jub, 4ba) have hand-typed VERSE_COUNTS in scripts/extract_parallel_pdf.py
# — see ``TEWAHEDO_DISTINCTIVE_NO_KJV`` below.
#
# Note: NT Mark uses code "mrk" (not "mar"); Letter-of-Jeremiah "lje";
# Susanna "sus"; Prayer-of-Manasseh "man"; Additions-to-Esther "aes" —
# matches the kjv/ directory's filenames.
CANONICAL_BOOKS = (
    # Pentateuch
    "gen",
    "exo",
    "lev",
    "num",
    "deu",
    # Historical
    "jos",
    "jdg",
    "rut",
    "1sa",
    "2sa",
    "1ki",
    "2ki",
    "1ch",
    "2ch",
    "ezr",
    "neh",
    "est",
    "tob",
    "jdt",
    # Wisdom + Poetry
    "job",
    "psa",
    "pro",
    "ecc",
    "sng",
    "wis",
    "sir",
    # Major + Minor Prophets
    "isa",
    "jer",
    "lam",
    "bar",
    "lje",
    "eze",
    "dan",
    "sus",
    "bel",
    "hos",
    "joe",
    "amo",
    "oba",
    "jon",
    "mic",
    "nah",
    "hab",
    "zep",
    "hag",
    "zec",
    "mal",
    # Apocryphal additions + Maccabees + LXX additions
    "1ma",
    "2ma",
    "1es",
    "2es",
    "paz",
    "aes",
    "man",
    # New Testament (Mark = "mrk")
    "mat",
    "mrk",
    "luk",
    "jhn",
    "act",
    "rom",
    "1co",
    "2co",
    "gal",
    "eph",
    "phi",
    "col",
    "1th",
    "2th",
    "1ti",
    "2ti",
    "tit",
    "phm",
    "heb",
    "jam",
    "1pe",
    "2pe",
    "1jn",
    "2jn",
    "3jn",
    "jud",
    "rev",
)

# Tewahedo-distinctive books without a KJV skeleton — verse counts live
# in scripts/extract_parallel_pdf.py's hand-typed dicts.
TEWAHEDO_DISTINCTIVE_NO_KJV = ("mq1", "mq2", "mq3", "1en", "jub", "4ba")


@lru_cache(maxsize=1024)
def _book_shape_cached(book: str) -> tuple:
    """Cached body for ``canonical_book_shape``. Returns tuple for hashability."""
    out: list[tuple[int, int]] = []
    ch = 1
    while True:
        skel = load_kjv_skeleton(book, ch)
        if not skel:
            break
        out.append((ch, len(skel)))
        ch += 1
        if ch > 200:  # defensive bound
            break
    return tuple(out)


def canonical_book_shape(book: str) -> dict[int, int]:
    """Return ``{chapter: verse_count}`` for *book*. Reads from the KJV
    skeleton; cached after first call."""
    return dict(_book_shape_cached(book))


def coord_in_canonical_extent(book: str, chapter: int, verse: int) -> bool:
    """True if ``(book, chapter, verse)`` is within the book's canonical extent —
    or the book has no known canonical shape (Tewahedo distinctives etc.), in
    which case it can't be validated and is kept. The single boundary guard that
    keeps impossible coordinates (e.g. Genesis 87:12, from OCR/parse noise) out
    of the corpus, regardless of which source or detector produced them."""
    try:
        shape = canonical_book_shape(book)
    except Exception:
        return True  # unknown book code — can't validate, keep
    if not shape:
        return True
    return chapter in shape and 1 <= verse <= shape[chapter]


def canonical_count(book: str, chapter: int) -> int:
    """Per-chapter verse count for *(book, chapter)*. Raises ``KeyError``
    if the chapter is not in the canonical skeleton."""
    shape = canonical_book_shape(book)
    if chapter not in shape:
        raise KeyError(f"{book} ch{chapter} not in canonical skeleton")
    return shape[chapter]


def canonical_total(book: str) -> int:
    """Total verse count for *book* (sum across all chapters)."""
    return sum(canonical_book_shape(book).values())


def canonical_chapters(book: str) -> int:
    """Total chapter count for *book*."""
    return len(canonical_book_shape(book))

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
# jub, 4ba; + 1cl, 2en) — the first six have hand-typed VERSE_COUNTS in
# scripts/extract_parallel_pdf.py; see ``TEWAHEDO_DISTINCTIVE_NO_KJV`` below.
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
TEWAHEDO_DISTINCTIVE_NO_KJV = ("mq1", "mq2", "mq3", "1en", "jub", "4ba", "1cl", "2en")


@lru_cache(maxsize=1024)
def _book_verse_sets_cached(book: str) -> tuple:
    """Cached ``((chapter, (verse, …)), …)`` of the ACTUAL verse numbers per chapter
    from the KJV skeleton (not just the count). Returns a tuple for hashability.

    Scans chapters 1..200 and SKIPS empty chapters (``continue``, not ``break``)
    so a book whose KJV skeleton does NOT start at chapter 1 — or has an internal
    chapter gap — is captured in full. The old break-on-first-empty truncated such
    a book to ``{}`` (``aes``'s skeleton runs 10..16 → ch 1 empty → break → empty
    shape), which silently made ``coord_in_canonical_extent`` a NO-OP for it (the
    ``if not shape: return True`` keep-all path).

    Capturing verse NUMBERS (not just ``len``) lets ``coord_in_canonical_extent``
    test true membership, so a non-1-start chapter — the sole one in the whole
    skeleton is ``aes`` ch10, numbered 4..13 (it continues canonical Esther 10:3) —
    validates against its real numbering rather than ``1..count`` (which wrongly
    rejected 11-13 and accepted 1-3). Round-13 data-validity finding DV2."""
    out: list[tuple[int, tuple[int, ...]]] = []
    for ch in range(1, 201):
        skel = load_kjv_skeleton(book, ch)
        if skel:
            out.append((ch, tuple(v for (_c, v, *_t) in skel)))
    return tuple(out)


@lru_cache(maxsize=1024)
def _book_shape_cached(book: str) -> tuple:
    """Cached ``{chapter: verse_count}`` body for ``canonical_book_shape``, derived
    from the per-chapter verse sets. Byte-identical to the historical count scan."""
    return tuple((ch, len(verses)) for ch, verses in _book_verse_sets_cached(book))


def canonical_book_shape(book: str) -> dict[int, int]:
    """Return ``{chapter: verse_count}`` for *book*. Reads from the KJV
    skeleton; cached after first call."""
    return dict(_book_shape_cached(book))


def coord_in_canonical_extent(book: str, chapter: int, verse: int) -> bool:
    """True if ``(book, chapter, verse)`` is within the book's canonical extent —
    or the book has no known canonical shape (Tewahedo distinctives etc.), in
    which case it can't be validated and is kept. The single boundary guard that
    keeps impossible coordinates (e.g. Genesis 87:12, from OCR/parse noise) out
    of the corpus, regardless of which source or detector produced them.

    Tests true verse-number MEMBERSHIP (not ``1..count``), so a non-1-start chapter
    (``aes`` ch10, verses 4..13) validates against its real numbering — byte-identical
    for every contiguous 1-start chapter (1361 of the 1362 skeleton chapters).
    Round-13 data-validity finding DV2."""
    try:
        sets = dict(_book_verse_sets_cached(book))
    except Exception:
        return True  # unknown book code — can't validate, keep
    if not sets:
        return True  # no canonical shape (Tewahedo distinctives etc.) — keep
    verses = sets.get(chapter)
    if not verses:
        return False  # chapter not in this book's skeleton — impossible coordinate
    return verse in verses


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


def html_chapter_count(book: str) -> int:
    """Number of chapters the BASE HTML actually renders for *book* — the
    promote-time ceiling for note chapter coordinates.

    Notes whose chapter exceeds this count are uninjectable: the base HTML
    has no chapter anchor to place them against (e.g. the ``aes`` ch 11-16
    notes — a known, PARKED residual — where the base HTML only renders the
    first 10 chapters). This helper backs a secondary promote guard that
    rejects FUTURE above-extent notes; it does not touch the existing parked
    residual (no corpus scan).

    Source / limitation: this module has no base-HTML chapter-extent table
    distinct from the canonical (KJV/LXX) skeleton, so the ceiling is the
    HIGHEST chapter number in that skeleton (``max`` of the shape keys), NOT the
    chapter COUNT. For a contiguous 1-start book the two are equal; for a book
    whose skeleton does not start at 1 / has a gap (``aes``: chapters 10..16) the
    max (16) is the true ceiling, whereas the count (7) would wrongly reject the
    real aes 10..16 coords. A conservative upper bound that rejects clearly
    out-of-canon chapters (aes ch 17+) but does not, by itself, reject the parked
    aes 11-16 coords — their injectability is the inject pipeline's concern, not
    this guard's. Books with no known skeleton (Tewahedo distinctives, or an
    unknown/test book code) have no derivable extent and return 0, which the
    guards treat as "unknown — do not reject" (mirroring ``coord_in_canonical_extent``).
    """
    try:
        shape = canonical_book_shape(book)
        return max(shape) if shape else 0
    except Exception:
        return 0  # unknown book code — no derivable extent; guards keep

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


# ── Tewahedo-distinctive extent (R14 data-validity fix) ──────────────────────
# The 8 books in ``TEWAHEDO_DISTINCTIVE_NO_KJV`` have no KJV/LXX skeleton, so the
# skeleton-derived guards above cannot validate them — historically that made
# ``coord_in_canonical_extent``/``html_chapter_count`` a silent NO-OP for them
# (any coordinate kept). Six DO have an authoritative hand-typed per-chapter
# verse table (in the dependency-free leaf ``distinctive_verse_counts``); the
# other two (``1cl``/``2en``) have only a ``books.yaml`` ``ch_count``. Consulting
# these closes the one boundary where an impossible coordinate (e.g. ``1en``
# 999:99) could otherwise reach ``content/notes`` and be silently dropped at
# inject. Additive: current on-disk data is clean (0 over-extent coords) so the
# Ethiopian build stays byte-identical and the 9 KJV editions are unaffected.

# Distinctive books WITHOUT a verse table — ch_count-ceiling-only (``1cl``/``2en``).
_DISTINCTIVE_NO_VERSE_TABLE = tuple(
    b for b in TEWAHEDO_DISTINCTIVE_NO_KJV if b not in ("mq1", "mq2", "mq3", "4ba", "jub", "1en")
)


@lru_cache(maxsize=1)
def _distinctive_extent_map() -> dict[str, dict[int, int]]:
    """``{book: {chapter: max_verse}}`` for the six distinctive books that have a
    hand-typed verse table. The tables are ``{chapter: verse_count}``; for a
    1-start contiguous book the count IS the highest verse number, so it doubles
    as the per-chapter verse CEILING. Lazy import keeps the leaf
    ``distinctive_verse_counts`` (and this module) free of import-time deps."""
    from .distinctive_verse_counts import (
        FOUR_BARUCH_VERSE_COUNTS,
        JUBILEES_VERSE_COUNTS,
        MQ1_VERSE_COUNTS,
        MQ2_VERSE_COUNTS,
        MQ3_VERSE_COUNTS,
        ONE_ENOCH_VERSE_COUNTS,
    )

    return {
        "mq1": dict(MQ1_VERSE_COUNTS),
        "mq2": dict(MQ2_VERSE_COUNTS),
        "mq3": dict(MQ3_VERSE_COUNTS),
        "4ba": dict(FOUR_BARUCH_VERSE_COUNTS),
        "jub": dict(JUBILEES_VERSE_COUNTS),
        "1en": dict(ONE_ENOCH_VERSE_COUNTS),
    }


def _distinctive_ch_count(book: str) -> int | None:
    """``books.yaml`` ``ch_count`` chapter ceiling for a distinctive book that has
    NO verse table (``1cl``/``2en``). Returns ``None`` for any other code so that
    genuinely unknown/test codes still reach the keep-all path. Lazy-loads
    ``books.yaml`` (cached by ``config.load_books``)."""
    if book not in _DISTINCTIVE_NO_VERSE_TABLE:
        return None
    try:
        from .config import books_by_code

        meta = books_by_code().get(book)
        if meta is None:
            return None
        return int(meta["ch_count"])
    except Exception:
        return None


def coord_in_canonical_extent(book: str, chapter: int, verse: int) -> bool:
    """True if ``(book, chapter, verse)`` is within the book's canonical extent.
    The single boundary guard that keeps impossible coordinates (e.g. Genesis
    87:12, from OCR/parse noise) out of the corpus, regardless of which source or
    detector produced them.

    Canonical-skeleton books test true verse-number MEMBERSHIP (not ``1..count``),
    so a non-1-start chapter (``aes`` ch10, verses 4..13) validates against its
    real numbering — byte-identical for every contiguous 1-start chapter (1361 of
    the 1362 skeleton chapters). Round-13 data-validity finding DV2.

    The 8 Tewahedo-distinctive books have no KJV/LXX skeleton. Six are validated
    against their hand-typed per-chapter verse table as a CEILING + chapter
    membership; ``1cl``/``2en`` (no verse table) are validated against the
    ``books.yaml`` ``ch_count`` chapter ceiling only. ``True`` (keep-all) is
    reserved for genuinely unknown/test book codes. Round-14 data-validity fix
    (was a silent no-op that kept ANY coordinate for these 8 shipping books)."""
    try:
        sets = dict(_book_verse_sets_cached(book))
    except Exception:
        sets = {}  # no KJV/LXX skeleton on disk — try the distinctive fallback
    if sets:
        verses = sets.get(chapter)
        if not verses:
            return False  # chapter not in this book's skeleton — impossible coordinate
        return verse in verses
    # No KJV/LXX skeleton — Tewahedo distinctive. Six have a hand-typed
    # {chapter: count} table → per-chapter verse CEILING + chapter membership.
    # verse 0 is the project's chapter-level note convention (e.g. the two real
    # on-disk 1en 91:0 / 94:0 chapter-intro comm notes) so the floor is 0, not 1.
    extent = _distinctive_extent_map().get(book)
    if extent is not None:
        return chapter in extent and 0 <= verse <= extent[chapter]
    # 1cl/2en have no verse table → enforce only the books.yaml chapter ceiling.
    ch_count = _distinctive_ch_count(book)
    if ch_count is not None:
        return 1 <= chapter <= ch_count and verse >= 0
    return True  # genuinely unknown / test book code — can't validate, keep


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
    this guard's. The 8 Tewahedo-distinctive books have no KJV/LXX skeleton: the
    six with a hand-typed verse table return ``max(chapter keys)`` of that table,
    and ``1cl``/``2en`` return the ``books.yaml`` ``ch_count`` (R14 data-validity
    fix; was 0 = "unknown, do not reject"). Only a genuinely unknown/test book
    code returns 0, which the guards treat as "unknown — do not reject" (mirroring
    ``coord_in_canonical_extent``).
    """
    try:
        shape = canonical_book_shape(book)
    except Exception:
        shape = {}  # no KJV/LXX skeleton on disk — try the distinctive fallback
    if shape:
        return max(shape)
    # No KJV/LXX skeleton — Tewahedo distinctive (R14 fix).
    extent = _distinctive_extent_map().get(book)
    if extent:
        return max(extent)
    ch_count = _distinctive_ch_count(book)
    if ch_count is not None:
        return ch_count
    return 0  # no derivable extent — guards treat 0 as "unknown — do not reject"

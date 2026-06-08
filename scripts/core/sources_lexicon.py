"""
sources_lexicon.py — lexicon / cross-reference / topical / textual-criticism
loaders extracted from the ``sources`` god-module.

Strong's Hebrew + Greek, the Treasury of Scripture Knowledge, Nave's and
Torrey's topical concordances, and the Kenyon textual-criticism corpus,
plus their singleton accessors. Each loader caches lazily on first read.

Extracted verbatim from ``sources.py`` (module split 2026-05-26).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache

from .sources_base import SourceMissingError, _SOURCES, _normalize_book_code


# ----------------------------------------------------------------------
# Strong's Hebrew
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class StrongsEntry:
    """One Strong's Hebrew dictionary entry. Fields mirror the original
    1894 Concise Dictionary plus a transliteration and KJV usage summary.
    Public-domain source; ``attribution`` returns the citation string."""

    number: str  # e.g. "H7779"
    lemma: str  # Hebrew lemma with niqqud
    xlit: str  # transliteration
    pron: str  # pronunciation
    derivation: str
    definition: str  # Strong's definition (the substantive entry)
    kjv_def: str  # short KJV usage summary

    @property
    def attribution(self) -> str:
        return (
            f"Strong's {self.number}, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD."
        )


class StrongsHebrew:
    """Lazy loader for the Strong's Hebrew lexicon (cached on first read).

    Raises ``SourceMissingError`` if the JSON cache hasn't been
    populated yet. Use ``get(num)`` to look up a single entry —
    returns ``None`` if the number is unknown."""

    PATH = _SOURCES / "strongs_hebrew.json"

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError("Strong's Hebrew not cached. Run: python3 scripts/fetch_sources.py")
        with self.PATH.open(encoding="utf-8") as f:
            self._data = json.load(f)

    def __contains__(self, num: str) -> bool:
        return num in self._data

    def __len__(self) -> int:
        return len(self._data)

    def get(self, num: str) -> StrongsEntry | None:
        d = self._data.get(num)
        if not d:
            return None
        return StrongsEntry(
            number=num,
            lemma=d.get("lemma", ""),
            xlit=d.get("xlit", ""),
            pron=d.get("pron", ""),
            derivation=d.get("derivation", ""),
            definition=d.get("strongs_def", ""),
            kjv_def=d.get("kjv_def", ""),
        )


# ----------------------------------------------------------------------
# Strong's Greek (χ.1)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class StrongsGreekEntry:
    """One Strong's Greek dictionary entry. Mirror of ``StrongsEntry``
    with the same field set; openscriptures' Greek dump uses ``translit``
    where the Hebrew dump uses ``xlit``, so the loader normalises both
    onto ``xlit``. Public-domain source; ``attribution`` returns the
    citation string."""

    number: str  # e.g. "G3056"
    lemma: str  # Greek lemma
    xlit: str  # transliteration
    pron: str  # pronunciation
    derivation: str
    definition: str  # Strong's definition (the substantive entry)
    kjv_def: str  # short KJV usage summary

    @property
    def attribution(self) -> str:
        return (
            f"Strong's {self.number}, A Concise Dictionary of the Words "
            f"in the Greek Testament, James Strong (1894). PD."
        )


# Two openscriptures Greek entries carry a malformed ``strongs_def`` /
# ``derivation`` split, so the substantive gloss is wrong when read from
# ``strongs_def`` alone (the field every other entry uses correctly):
#   * G2316 θεός — its primary "a deity ... the supreme Divinity" sense sits in
#     ``derivation``; ``strongs_def`` holds only the tail "figuratively, a
#     magistrate; by Hebraism, very", so the gloss dropped the head (1,196 notes,
#     100% of θεός).
#   * G5457 φῶς — a derivation fragment ("compare G5316 (φαίνω), G5346 (φημί))")
#     leaked into the FRONT of ``strongs_def`` (76 notes; a dangling close-paren).
# We curate the corrected substantive definition here rather than mutate the
# vendored dump, so a future ``fetch_sources`` re-pull stays clean and the fix is
# explicit + testable. See docs/superpowers/notes/2026-06-06-auto-note-reingest-plan.md
# §2/§4 and 2026-06-06-auto-note-quality-audit.md.
_GREEK_DEF_OVERRIDES = {
    "G2316": "a deity, especially the supreme Divinity; figuratively, a magistrate; by Hebraism, very",
    "G5457": "luminousness (in the widest application, natural or artificial, abstract or concrete, literal or figurative)",
}


class StrongsGreek:
    """Lazy loader for the Strong's Greek lexicon (cached on first read).

    Raises ``SourceMissingError`` if the JSON cache hasn't been
    populated yet. Use ``get(num)`` to look up a single entry —
    returns ``None`` if the number is unknown.

    Field naming: openscriptures' Greek dump uses ``translit`` where
    the Hebrew dump uses ``xlit``. The loader accepts both so future
    upstream renames don't break the platform; consumers always see
    the entry's transliteration via ``StrongsGreekEntry.xlit``."""

    PATH = _SOURCES / "strongs_greek.json"

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError("Strong's Greek not cached. Run: python3 scripts/fetch_sources.py")
        with self.PATH.open(encoding="utf-8") as f:
            self._data = json.load(f)

    def __contains__(self, num: str) -> bool:
        return num in self._data

    def __len__(self) -> int:
        return len(self._data)

    def get(self, num: str) -> StrongsGreekEntry | None:
        d = self._data.get(num)
        if not d:
            return None
        # Tolerate either field name; openscriptures uses ``translit``
        # for Greek, ``xlit`` for Hebrew. Normalise here.
        xlit = d.get("xlit") or d.get("translit") or ""
        return StrongsGreekEntry(
            number=num,
            lemma=d.get("lemma", ""),
            xlit=xlit,
            pron=d.get("pron", ""),
            derivation=d.get("derivation", ""),
            definition=_GREEK_DEF_OVERRIDES.get(num, d.get("strongs_def", "")),
            kjv_def=d.get("kjv_def", ""),
        )


# ----------------------------------------------------------------------
# Treasury of Scripture Knowledge
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class TskCrossRef:
    """One cross-reference entry from the Treasury of Scripture Knowledge.

    Carries the target book/chapter/verse plus a community vote strength.
    Higher vote counts mean the link is widely considered stronger.
    Public-domain text; ``attribution`` returns the citation string."""

    target_book: str
    target_chapter: int
    target_verse: int
    votes: int  # higher = stronger link; openbible community-scored

    @property
    def reference(self) -> str:
        # Lazy book→display lookup (we have the data via books.yaml but
        # don't take a hard dep here — caller can format if needed).
        return f"{self.target_book} {self.target_chapter}:{self.target_verse}"

    @property
    def attribution(self) -> str:
        return "Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0."


class Tsk:
    """Lazy loader for the Treasury of Scripture Knowledge cross-reference
    index. Use ``refs_for(book, chapter, verse)`` to get the top community-
    scored cross-refs for any verse."""

    PATH = _SOURCES / "tsk_xrefs.json"

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError("TSK not cached. Run: python3 scripts/fetch_sources.py")
        with self.PATH.open(encoding="utf-8") as f:
            self._data = json.load(f)

    def refs_for(self, book: str, chapter: int, verse: int, *, min_votes: int = 5, top_n: int = 5) -> list[TskCrossRef]:
        """Return top-N cross-refs for a verse, sorted by vote strength."""
        verse_dict = self._data.get(book, {}).get(str(chapter), {})
        raw = verse_dict.get(str(verse)) or []
        out = [TskCrossRef(*r) for r in raw if r[3] >= min_votes]
        out.sort(key=lambda r: -r.votes)
        return out[:top_n]


# ----------------------------------------------------------------------
# Nave's Topical Bible (Phase χ.7)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class NaveTopicHit:
    """One topical-concordance hit: this verse appears under this topic.

    Public-domain text (Orville J. Nave, 1896); ``attribution`` returns
    the citation string used on candidate notes."""

    topic: str  # e.g. "Faith", "Names of God", "Prayer"
    target_book: str
    target_chapter: int
    target_verse: int

    @property
    def attribution(self) -> str:
        return "Nave's Topical Bible, Orville J. Nave (1896). Public domain."


class NavesTopical:
    """Lazy loader for Nave's Topical Bible — a topical concordance with
    ~20K topics and ~100K verse references. Cached on first read.

    Two access patterns:
      * ``topics_for(book, chapter, verse)`` — reverse index: which
        topics include this verse? (the detector's primary call)
      * ``verses_for(topic)`` — forward index: which verses are tagged
        with this topic? (audit / coverage UIs)

    JSON cache shape (written by fetch_sources.fetch_naves_topical):
        {
          "_meta": {"n_topics": int, "n_refs": int, "source": str},
          "topics": {"<topic>": [["<book>", <ch>, <vs>], ...]},
          "verses": {"<book>": {"<ch>": {"<vs>": ["<topic>", ...]}}}
        }

    Raises ``SourceMissingError`` if the JSON cache is absent. Same
    bootstrap shape as ``StrongsHebrew`` and ``Tsk``.
    """

    PATH = _SOURCES / "naves_topical.json"

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError("Nave's Topical not cached. Run: python3 scripts/fetch_sources.py")
        with self.PATH.open(encoding="utf-8") as f:
            self._data = json.load(f)
        self._topics = self._data.get("topics", {})
        self._verses = self._data.get("verses", {})

    def __len__(self) -> int:
        return len(self._topics)

    @property
    def n_topics(self) -> int:
        return len(self._topics)

    @property
    def n_refs(self) -> int:
        return self._data.get("_meta", {}).get("n_refs", 0)

    def topics_for(self, book: str, chapter: int, verse: int, *, top_n: int = 5) -> list[str]:
        """Return up to ``top_n`` topics tagged on this verse.

        Topics are returned in the order they appeared in the source
        (Nave alphabetised topics, so this is alphabetical). The detector
        consolidates them into one candidate per verse.
        """
        book = _normalize_book_code(book)
        topic_list = (self._verses.get(book, {}).get(str(chapter), {}).get(str(verse))) or []
        return list(topic_list)[:top_n]

    def verses_for(self, topic: str) -> list[NaveTopicHit]:
        """Return every verse tagged with this topic."""
        raw = self._topics.get(topic) or []
        return [
            NaveTopicHit(
                topic=topic, target_book=_normalize_book_code(r[0]), target_chapter=int(r[1]), target_verse=int(r[2])
            )
            for r in raw
            if len(r) >= 3
        ]

    def topics(self) -> list[str]:
        """Every topic name, alphabetically — for enumerating the whole index
        (the back-of-book topical index / coverage UIs)."""
        return sorted(self._topics)


@dataclass(frozen=True)
class TorreyTopicHit:
    """One topical-concordance hit from Torrey's New Topical Textbook
    (R.A. Torrey, 1897, public domain)."""

    topic: str
    target_book: str
    target_chapter: int
    target_verse: int

    @property
    def attribution(self) -> str:
        return "Torrey's New Topical Textbook, R.A. Torrey (1897). Public domain."


class TorreyTopical:
    """Lazy loader for Torrey's New Topical Textbook — a second topical
    concordance (1897, Reformed/Baptist editorial selection) alongside Nave's.
    Same JSON cache shape and access pattern as ``NavesTopical``; written by
    ``scripts/extract_torrey_ccel.py``.

    JSON cache shape::

        {
          "_meta": {"n_topics": int, "n_refs": int, "source": str},
          "topics": {"<topic>": [["<book>", <ch>, <vs>], ...]},
          "verses": {"<book>": {"<ch>": {"<vs>": ["<topic>", ...]}}}
        }

    Raises ``SourceMissingError`` if the JSON cache is absent.
    """

    PATH = _SOURCES / "torrey_topical.json"

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError("Torrey's New Topical not cached. Run: python3 scripts/extract_torrey_ccel.py")
        with self.PATH.open(encoding="utf-8") as f:
            self._data = json.load(f)
        self._topics = self._data.get("topics", {})
        self._verses = self._data.get("verses", {})

    def __len__(self) -> int:
        return len(self._topics)

    @property
    def n_topics(self) -> int:
        return len(self._topics)

    @property
    def n_refs(self) -> int:
        return self._data.get("_meta", {}).get("n_refs", 0)

    def topics_for(self, book: str, chapter: int, verse: int, *, top_n: int = 5) -> list[str]:
        """Return up to ``top_n`` topics tagged on this verse, in source
        (alphabetical) order. The detector consolidates them into one
        candidate per verse."""
        book = _normalize_book_code(book)
        topic_list = (self._verses.get(book, {}).get(str(chapter), {}).get(str(verse))) or []
        return list(topic_list)[:top_n]

    def verses_for(self, topic: str) -> list[TorreyTopicHit]:
        """Return every verse tagged with this topic."""
        raw = self._topics.get(topic) or []
        return [
            TorreyTopicHit(
                topic=topic, target_book=_normalize_book_code(r[0]), target_chapter=int(r[1]), target_verse=int(r[2])
            )
            for r in raw
            if len(r) >= 3
        ]

    def topics(self) -> list[str]:
        """Every topic name, alphabetically — for enumerating the whole index."""
        return sorted(self._topics)


# ----------------------------------------------------------------------
# Singletons (cached across runs in the same process)
# ----------------------------------------------------------------------


@lru_cache(maxsize=1)
def strongs_hebrew() -> StrongsHebrew:
    """Return the singleton StrongsHebrew instance (lazy-loaded once)."""
    return StrongsHebrew()


@lru_cache(maxsize=1)
def strongs_greek() -> StrongsGreek:
    """Return the singleton StrongsGreek instance (lazy-loaded once)."""
    return StrongsGreek()


@lru_cache(maxsize=1)
def tsk() -> Tsk:
    """Return the singleton Tsk instance (lazy-loaded once)."""
    return Tsk()


@lru_cache(maxsize=1)
def naves_topical() -> NavesTopical:
    """Return the singleton NavesTopical instance (lazy-loaded once)."""
    return NavesTopical()


@lru_cache(maxsize=1)
def torrey_topical() -> TorreyTopical:
    """Return the singleton TorreyTopical instance (lazy-loaded once)."""
    return TorreyTopical()


# ----------------------------------------------------------------------
# Kenyon textual-criticism source (Phase χ.0)
# ----------------------------------------------------------------------


# Standard book-name → canonical 3-letter code mapping for parsing
# verse references in Kenyon-style PD textual-criticism prose. Both
# the abbreviation (with optional trailing dot) AND the full name
# resolve to the same code. Numeric prefixes ("1 Sam.", "2 Cor.") are
# normalised in the regex; the leading digit is concatenated to the
# leading letters of the abbreviation here.
KENYON_BOOK_NAME_TO_CODE: dict[str, str] = {
    # OT
    "gen": "gen",
    "genesis": "gen",
    "exod": "exo",
    "exodus": "exo",
    "ex": "exo",
    "lev": "lev",
    "leviticus": "lev",
    "num": "num",
    "numbers": "num",
    "numb": "num",
    "deut": "deu",
    "deuteronomy": "deu",
    "dent": "deu",  # OCR variant
    "josh": "jos",
    "joshua": "jos",
    "judg": "jdg",
    "judges": "jdg",
    "ruth": "rut",
    "1sam": "1sa",
    "1samuel": "1sa",
    "isam": "1sa",  # OCR i/1
    "2sam": "2sa",
    "2samuel": "2sa",
    "iisam": "2sa",
    "1kin": "1ki",
    "1kings": "1ki",
    "1kgs": "1ki",
    "2kin": "2ki",
    "2kings": "2ki",
    "2kgs": "2ki",
    "1chr": "1ch",
    "1chron": "1ch",
    "1chronicles": "1ch",
    "2chr": "2ch",
    "2chron": "2ch",
    "2chronicles": "2ch",
    "ezra": "ezr",
    "neh": "neh",
    "nehemiah": "neh",
    "esth": "est",
    "esther": "est",
    "job": "job",
    "ps": "psa",
    "psa": "psa",
    "psalm": "psa",
    "psalms": "psa",
    "prov": "pro",
    "proverbs": "pro",
    "eccl": "ecc",
    "ecclesiastes": "ecc",
    "eccles": "ecc",
    "song": "sng",
    "songofsolomon": "sng",
    "cant": "sng",
    "isa": "isa",
    "isaiah": "isa",
    "jer": "jer",
    "jeremiah": "jer",
    "lam": "lam",
    "lamentations": "lam",
    "ezek": "eze",
    "ezekiel": "eze",
    "dan": "dan",
    "daniel": "dan",
    "hos": "hos",
    "hosea": "hos",
    "joel": "joe",
    "amos": "amo",
    "obad": "oba",
    "obadiah": "oba",
    "jon": "jon",
    "jonah": "jon",
    "mic": "mic",
    "micah": "mic",
    "nah": "nah",
    "nahum": "nah",
    "hab": "hab",
    "habakkuk": "hab",
    "zeph": "zep",
    "zephaniah": "zep",
    "hag": "hag",
    "haggai": "hag",
    "zech": "zec",
    "zechariah": "zec",
    "mal": "mal",
    "malachi": "mal",
    # NT
    "matt": "mat",
    "matthew": "mat",
    "mark": "mrk",
    "mk": "mrk",
    "luke": "luk",
    "lk": "luk",
    "john": "jhn",
    "jn": "jhn",
    "acts": "act",
    "rom": "rom",
    "romans": "rom",
    "1cor": "1co",
    "1corinthians": "1co",
    "2cor": "2co",
    "2corinthians": "2co",
    "gal": "gal",
    "galatians": "gal",
    "eph": "eph",
    "ephesians": "eph",
    "phil": "phi",
    "philippians": "phi",
    "col": "col",
    "colossians": "col",
    "1thess": "1th",
    "1thessalonians": "1th",
    "1thes": "1th",
    "2thess": "2th",
    "2thessalonians": "2th",
    "2thes": "2th",
    "1tim": "1ti",
    "1timothy": "1ti",
    "2tim": "2ti",
    "2timothy": "2ti",
    "tit": "tit",
    "titus": "tit",
    "phlm": "phm",
    "philemon": "phm",
    "heb": "heb",
    "hebrews": "heb",
    "jas": "jam",
    "james": "jam",
    "1pet": "1pe",
    "1peter": "1pe",
    "2pet": "2pe",
    "2peter": "2pe",
    "1john": "1jn",
    "1jn": "1jn",
    "2john": "2jn",
    "2jn": "2jn",
    "3john": "3jn",
    "3jn": "3jn",
    "jude": "jud",
    "rev": "rev",
    "revelation": "rev",
    "apoc": "rev",
}


@dataclass(frozen=True)
class KenyonReference:
    """One verse reference parsed out of Kenyon's PD textual-criticism
    prose, paired with its surrounding context window. Public-domain
    text (F.G. Kenyon, *Our Bible and the Ancient Manuscripts*, 1895)."""

    book: str  # canonical 3-letter code (e.g. "mat")
    chapter: int
    verse: int
    context: str  # surrounding ~300 chars from the source

    @property
    def attribution(self) -> str:
        return (
            "Frederic G. Kenyon, *Our Bible and the Ancient Manuscripts* "
            "(Eyre & Spottiswoode, London, 1895). Public domain."
        )


class KenyonText:
    """Lazy loader for the Kenyon textual-criticism corpus. Reads the
    cached `content/sources/kenyon_textcrit.txt` once; produces a list
    of `KenyonReference` entries via `references()`.

    Mirrors the §9 χ-cluster pattern (TSK / Strong's / Nave's): the
    detector walks this index rather than recomputing the regex pass.

    Phase χ.0 (2026-05-08)."""

    PATH = _SOURCES / "kenyon_textcrit.txt"
    # [1-3]?[ -]? prefix tolerates "1 Sam.", "2 Sam.", "1Sam." (OCR
    # whitespace variability); [A-Z][a-zA-Z]{1,12} catches abbreviations
    # and full names; \.?\s+\d+\s*[\.,:]\s*\d+ catches "Matt. 19. 17",
    # "Matt 19:17", "Matt. 19, 17" — all OCR-tolerant.
    REF_RE = re.compile(r"\b([1-3])?\s*([A-Z][a-zA-Z]{1,12})\.?\s+(\d+)\s*[\.,:]\s*(\d+)\b")
    CONTEXT_RADIUS = 200  # chars on each side of a match

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError(
                f"Kenyon source not staged at {self.PATH}. "
                "Stage from oldfindings.txt: cp <txt> "
                "content/sources/kenyon_textcrit.txt"
            )
        self._text = self.PATH.read_text(encoding="utf-8", errors="replace")
        self._refs: list[KenyonReference] | None = None

    def references(self) -> list[KenyonReference]:
        """Parsed verse references with surrounding context. Cached on
        first call. Unknown book names are silently skipped, as are
        chapter numbers that exceed the book's ch_count (those are
        page-range citations from Kenyon's index, not verse refs —
        e.g. ``Deuteronomy 122, 123`` in his back-matter)."""
        if self._refs is not None:
            return self._refs

        # Lazy import: keeps sources.py importable in environments
        # without the full content tree (CI doc builds, etc.).
        from . import config as _cfg

        ch_counts = {code: int(meta.get("ch_count") or 0) for code, meta in _cfg.books_by_code().items()}

        refs: list[KenyonReference] = []
        for m in self.REF_RE.finditer(self._text):
            num_prefix = (m.group(1) or "").strip()
            book_name = m.group(2).strip()
            try:
                chapter = int(m.group(3))
                verse = int(m.group(4))
            except ValueError:
                continue
            # Build the lookup key: lowercased name with numeric prefix
            # concatenated. "1 Sam" → "1sam"; "Matt" → "matt".
            key = (num_prefix + book_name).lower()
            book_code = KENYON_BOOK_NAME_TO_CODE.get(key)
            if book_code is None:
                continue
            # Reject chapter numbers that exceed the book's actual
            # ch_count — these are page-range citations from Kenyon's
            # index/back-matter masquerading as verse refs. Also
            # rejects chapter == 0 / negative (defensive).
            max_ch = ch_counts.get(book_code, 0)
            if chapter < 1 or (max_ch and chapter > max_ch):
                continue
            # Context window — ±CONTEXT_RADIUS around the match
            start = max(0, m.start() - self.CONTEXT_RADIUS)
            end = min(len(self._text), m.end() + self.CONTEXT_RADIUS)
            context = self._text[start:end]
            # Normalise whitespace so the body renders cleanly in HTML
            context = re.sub(r"\s+", " ", context).strip()
            refs.append(
                KenyonReference(
                    book=book_code,
                    chapter=chapter,
                    verse=verse,
                    context=context,
                )
            )

        self._refs = refs
        return refs


@lru_cache(maxsize=1)
def kenyon_text() -> KenyonText:
    """Return the singleton KenyonText instance (lazy-loaded once)."""
    return KenyonText()

"""
sources.py — Loaders for the public-domain reference corpora cached
under ``content/sources/`` by ``scripts/fetch_sources.py``.

Each source class loads lazily (first call) and caches in memory. The
public API is read-only; ``fetch_sources.py`` is the only writer.

Public API:
    StrongsHebrew()         — entries keyed by H-number
    StrongsGreek()          — entries keyed by G-number  (Phase χ.1)
    Tsk()                   — cross-refs keyed by (book, chapter, verse)
    NavesTopical()          — topical-concordance hits, both directions
                              (Phase χ.7)
    KenyonText()            — PD textual-criticism prose (Phase χ.0)
    AnthropicXrefClient()   — LLM-backed xref proposer (Phase χ-AI-xrefs)
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Optional

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
            f"Strong's {self.number}, A Concise Dictionary of the Words "
            f"in the Hebrew Bible, James Strong (1894). PD."
        )


class StrongsHebrew:
    """Lazy loader for the Strong's Hebrew lexicon (cached on first read).

    Raises ``SourceMissingError`` if the JSON cache hasn't been
    populated yet. Use ``get(num)`` to look up a single entry —
    returns ``None`` if the number is unknown."""

    PATH = _SOURCES / "strongs_hebrew.json"

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError(
                f"Strong's Hebrew not cached. "
                f"Run: python3 scripts/fetch_sources.py"
            )
        with self.PATH.open(encoding="utf-8") as f:
            self._data = json.load(f)

    def __contains__(self, num: str) -> bool:
        return num in self._data

    def __len__(self) -> int:
        return len(self._data)

    def get(self, num: str) -> Optional[StrongsEntry]:
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
            raise SourceMissingError(
                f"Strong's Greek not cached. "
                f"Run: python3 scripts/fetch_sources.py"
            )
        with self.PATH.open(encoding="utf-8") as f:
            self._data = json.load(f)

    def __contains__(self, num: str) -> bool:
        return num in self._data

    def __len__(self) -> int:
        return len(self._data)

    def get(self, num: str) -> Optional[StrongsGreekEntry]:
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
            definition=d.get("strongs_def", ""),
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
        return (
            "Treasury of Scripture Knowledge (1830s). PD. "
            "Digital edition by openbible.info, CC-BY 4.0."
        )


class Tsk:
    """Lazy loader for the Treasury of Scripture Knowledge cross-reference
    index. Use ``refs_for(book, chapter, verse)`` to get the top community-
    scored cross-refs for any verse."""

    PATH = _SOURCES / "tsk_xrefs.json"

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError(
                f"TSK not cached. Run: python3 scripts/fetch_sources.py"
            )
        with self.PATH.open(encoding="utf-8") as f:
            self._data = json.load(f)

    def refs_for(
        self, book: str, chapter: int, verse: int, *, min_votes: int = 5, top_n: int = 5
    ) -> list[TskCrossRef]:
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
        return (
            "Nave's Topical Bible, Orville J. Nave (1896). Public domain."
        )


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
            raise SourceMissingError(
                f"Nave's Topical not cached. "
                f"Run: python3 scripts/fetch_sources.py"
            )
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

    def topics_for(
        self, book: str, chapter: int, verse: int, *, top_n: int = 5
    ) -> list[str]:
        """Return up to ``top_n`` topics tagged on this verse.

        Topics are returned in the order they appeared in the source
        (Nave alphabetised topics, so this is alphabetical). The detector
        consolidates them into one candidate per verse.
        """
        topic_list = (
            self._verses.get(book, {})
            .get(str(chapter), {})
            .get(str(verse))
        ) or []
        return list(topic_list)[:top_n]

    def verses_for(self, topic: str) -> list[NaveTopicHit]:
        """Return every verse tagged with this topic."""
        raw = self._topics.get(topic) or []
        return [NaveTopicHit(topic=topic, target_book=r[0],
                              target_chapter=int(r[1]),
                              target_verse=int(r[2]))
                for r in raw if len(r) >= 3]


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
    "gen": "gen", "genesis": "gen",
    "exod": "exo", "exodus": "exo", "ex": "exo",
    "lev": "lev", "leviticus": "lev",
    "num": "num", "numbers": "num", "numb": "num",
    "deut": "deu", "deuteronomy": "deu", "dent": "deu",  # OCR variant
    "josh": "jos", "joshua": "jos",
    "judg": "jdg", "judges": "jdg",
    "ruth": "rut",
    "1sam": "1sa", "1samuel": "1sa", "isam": "1sa",      # OCR i/1
    "2sam": "2sa", "2samuel": "2sa", "iisam": "2sa",
    "1kin": "1ki", "1kings": "1ki", "1kgs": "1ki",
    "2kin": "2ki", "2kings": "2ki", "2kgs": "2ki",
    "1chr": "1ch", "1chron": "1ch", "1chronicles": "1ch",
    "2chr": "2ch", "2chron": "2ch", "2chronicles": "2ch",
    "ezra": "ezr",
    "neh": "neh", "nehemiah": "neh",
    "esth": "est", "esther": "est",
    "job": "job",
    "ps": "psa", "psa": "psa", "psalm": "psa", "psalms": "psa",
    "prov": "pro", "proverbs": "pro",
    "eccl": "ecc", "ecclesiastes": "ecc", "eccles": "ecc",
    "song": "sng", "songofsolomon": "sng", "cant": "sng",
    "isa": "isa", "isaiah": "isa",
    "jer": "jer", "jeremiah": "jer",
    "lam": "lam", "lamentations": "lam",
    "ezek": "eze", "ezekiel": "eze",
    "dan": "dan", "daniel": "dan",
    "hos": "hos", "hosea": "hos",
    "joel": "jol",
    "amos": "amo",
    "obad": "oba", "obadiah": "oba",
    "jon": "jon", "jonah": "jon",
    "mic": "mic", "micah": "mic",
    "nah": "nah", "nahum": "nah",
    "hab": "hab", "habakkuk": "hab",
    "zeph": "zep", "zephaniah": "zep",
    "hag": "hag", "haggai": "hag",
    "zech": "zec", "zechariah": "zec",
    "mal": "mal", "malachi": "mal",
    # NT
    "matt": "mat", "matthew": "mat",
    "mark": "mrk", "mk": "mrk",
    "luke": "luk", "lk": "luk",
    "john": "jhn", "jn": "jhn",
    "acts": "act",
    "rom": "rom", "romans": "rom",
    "1cor": "1co", "1corinthians": "1co",
    "2cor": "2co", "2corinthians": "2co",
    "gal": "gal", "galatians": "gal",
    "eph": "eph", "ephesians": "eph",
    "phil": "php", "philippians": "php",
    "col": "col", "colossians": "col",
    "1thess": "1th", "1thessalonians": "1th", "1thes": "1th",
    "2thess": "2th", "2thessalonians": "2th", "2thes": "2th",
    "1tim": "1ti", "1timothy": "1ti",
    "2tim": "2ti", "2timothy": "2ti",
    "tit": "tit", "titus": "tit",
    "phlm": "phm", "philemon": "phm",
    "heb": "heb", "hebrews": "heb",
    "jas": "jas", "james": "jas",
    "1pet": "1pe", "1peter": "1pe",
    "2pet": "2pe", "2peter": "2pe",
    "1john": "1jn", "1jn": "1jn",
    "2john": "2jn", "2jn": "2jn",
    "3john": "3jn", "3jn": "3jn",
    "jude": "jud",
    "rev": "rev", "revelation": "rev", "apoc": "rev",
}


@dataclass(frozen=True)
class KenyonReference:
    """One verse reference parsed out of Kenyon's PD textual-criticism
    prose, paired with its surrounding context window. Public-domain
    text (F.G. Kenyon, *Our Bible and the Ancient Manuscripts*, 1895)."""
    book: str       # canonical 3-letter code (e.g. "mat")
    chapter: int
    verse: int
    context: str    # surrounding ~300 chars from the source

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
    REF_RE = re.compile(
        r"\b([1-3])?\s*([A-Z][a-zA-Z]{1,12})\.?\s+(\d+)\s*[\.,:]\s*(\d+)\b"
    )
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
        ch_counts = {
            code: int(meta.get("ch_count") or 0)
            for code, meta in _cfg.books_by_code().items()
        }

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
            refs.append(KenyonReference(
                book=book_code, chapter=chapter, verse=verse, context=context,
            ))

        self._refs = refs
        return refs


@lru_cache(maxsize=1)
def kenyon_text() -> KenyonText:
    """Return the singleton KenyonText instance (lazy-loaded once)."""
    return KenyonText()


# ----------------------------------------------------------------------
# Anthropic-backed thematic xref client (Phase χ-AI-xrefs)
# ----------------------------------------------------------------------


# Default model for the AI xref pass. Haiku 4.5 is the cost/quality
# sweet spot for this volume (31K verses); Sonnet 4.6 / Opus 4.7 are
# overkill for proposing 3 thematic links per verse and 10-30× more
# expensive. The driver's --model flag overrides for re-runs.
#
# Use the alias (no date suffix) so capability updates land without
# code changes. Pin to a dated snapshot only when reproducibility
# matters more than getting Anthropic's quality bumps for free.
DEFAULT_AI_XREF_MODEL = "claude-haiku-4-5"


# Cache TTL on the system prompt. The 1-hour TTL costs 2× to write
# (vs 1.25× for 5-min) but keeps the cache alive across the full
# 31K-verse run, which takes ~30+ minutes wall-clock. Break-even is
# 3 reads — at this scale we get ~31,000 reads, so 1h is the right
# choice. See `shared/prompt-caching.md` (Anthropic SDK skill).
AI_XREF_CACHE_TTL = "1h"


# CRITICAL: prompt caching has a model-specific minimum prefix length
# below which the cache_control marker silently does nothing —
# `cache_creation_input_tokens` will be 0 with no error. For
# Haiku 4.5 the minimum is **4096 tokens**. The system prompt below
# is intentionally padded with worked examples and anti-patterns
# both to clear the threshold AND to give the proposer richer
# guidance (better proposals, not just bigger prompt). A token-count
# assertion in TestAnthropicXrefClient pins this contract — if you
# shorten the prompt and it dips under 4096, the test fails before
# the next paid run discovers it the expensive way.
AI_XREF_SYSTEM_PROMPT = """You are a biblical cross-reference proposer.

# YOUR ROLE

Given one Bible verse (book, chapter, verse, KJV text), propose up
to N thematic, typological, or idiomatic cross-references — the
kind a careful pastor or scholar would notice on a re-read but a
static keyword/citation index (TSK, Strong's, Nave's) reliably
misses. The platform already runs those static detectors; your job
is to add the inferential layer they cannot.

You are conservative by default. A reviewer will curate every
proposal you emit, so false positives waste their time. When in
doubt, omit. An empty `proposals` list is a valid, useful answer.

# THREE KINDS OF LINK

## 1. Typological — concrete OT figure prefigures NT fulfillment

A typological link names an OT person, event, object, or institution
that the NT explicitly or implicitly identifies as a shadow of
Christ, the church, the kingdom, or salvation. The strongest
typology is anchored in NT exegesis (Hebrews, Romans 5, John 3,
1 Corinthians 10).

Worked examples:
  - Genesis 22 (Abraham binds Isaac on Moriah) → Hebrews 11:17-19
    (Abraham's faith), Romans 8:32 (the Father not sparing his Son),
    John 3:16. The "only son," "the wood laid on Isaac," and the
    substitute ram all carry typological weight.
  - Numbers 21:8-9 (brazen serpent lifted up in the wilderness) →
    John 3:14-15. Jesus himself names the type. High confidence.
  - Exodus 12 (Passover lamb) → 1 Corinthians 5:7 ("Christ our
    passover"), 1 Peter 1:19, John 1:29, Revelation 5:6. NT writers
    apply the type repeatedly.
  - Genesis 14 (Melchizedek blesses Abram) → Hebrews 5-7. The most
    extended typological argument in the NT.
  - 2 Samuel 7 (Davidic covenant) → Luke 1:32-33, Acts 13:34. Royal
    typology with explicit NT use.
  - Joseph (Genesis 37-50, betrayed by brothers, exalted, saves
    family) → no single NT verse, but Stephen's speech (Acts 7:9-14)
    and the church's reading tradition treat Joseph typologically.
    Lower confidence than Isaac/Passover/serpent because NT use is
    indirect.

A useful test: if a competent commentator would explain the link
using the words "type," "shadow," "figure," or "prefiguration," it
is typological. If they would only say "this also discusses X,"
it is thematic, not typological.

## 2. Thematic — recurring motif resonates across canon

Thematic links connect verses that share a substantive theological
motif developed across multiple books, even when no specific OT
figure is being fulfilled. These are the canonical "echoes"
literary readers notice.

Worked examples:
  - "The remnant" (Isa 10:20-22, Mic 4:7, Zeph 3:13, Rom 9:27, Rom
    11:5). A thread, not a single type.
  - "Wilderness as testing ground" (Exo 16, Deu 8, Hos 2:14, Mat
    4:1-11, Heb 3:7-19). The pattern recurs.
  - "Covenant renewal" (Jos 24, 2Ki 23, Neh 9-10, Jer 31:31-34, Luk
    22:20, Heb 8:8-12). A canonical arc.
  - "Suffering servant" (Isa 42, 49, 50, 53; Mat 8:17; Acts 8:32-35;
    1 Pet 2:21-25). NT writers apply Isa 53 typologically, but the
    broader servant motif is thematic.
  - "Day of the Lord" (Joe 1-2, Amo 5:18-20, Zep 1:14, Mal 4:5,
    1 Th 5:2, 2 Pet 3:10). Genuinely cross-canonical.
  - "Kinsman-redeemer / go'el" (Lev 25:25-49, Ru 4, Isa 41:14, Job
    19:25, Mat 1:21).

Themes are not single keywords. "Bread" appears 360 times in the
KJV; that is not a theme. "Bread of God's provision in the
wilderness" linking Exo 16 to Jhn 6 IS a theme. The discriminator
is whether multiple texts develop the same theological idea.

## 3. Idiomatic — phraseological echo that survives translation

Idiomatic links connect verses that share a Hebrew or Greek figure
of speech, formula, or stylistic pattern that the KJV preserves.
The reader hears the resonance without consulting a lexicon.

Worked examples:
  - "It came to pass" (Hebrew vayehi, opens hundreds of OT
    narratives) → Luke uses the same formula in his birth narrative
    (Luk 2:1, 2:6) to evoke OT-style storytelling. Stylistic, not
    propositional.
  - "Lift up your eyes" (Gen 13:14, 18:2, 22:4, Isa 40:26, 60:4,
    Jhn 4:35). A summons-to-attention formula reused with theological
    weight.
  - "And God said... and it was so" (Gen 1) → echoed in Psalm 33:9,
    148:5, Heb 11:3. A creation-by-word formula.
  - "Behold" / "Hinneh" used to introduce a divine messenger or
    epiphany (Gen 16:11, Isa 7:14, Mat 1:23, Luk 1:31).
  - "Anointed one" / "mashiach" / "christos" (1Sa 24:6, Psa 2:2,
    Dan 9:25, Jhn 1:41). Lexical when used as a title; idiomatic
    when used as a phrase pattern.

Idiomatic links are often lower-confidence than typological or
thematic links because the same phrase can recur incidentally. Only
flag idiomatic links where the reuse is theologically loaded.

# WHAT TO AVOID

The static detectors already produce ~16,000 notes. Do not propose
links that overlap their output:

1. **Direct citations** — TSK already enumerates explicit OT-in-NT
   quotations and clear allusion. If Romans 9:33 cites Isaiah 8:14
   and 28:16, TSK has it. Don't repropose.
2. **Strong's keyword matches** — "love" appears in 700 verses; do
   not propose a link merely because both verses contain the word
   "love." Strong's already groups by lemma.
3. **Nave's topical groupings** — "wisdom," "prayer," "faith," and
   ~600 other topical buckets are covered. A pure "both verses are
   about wisdom" link is Nave's job, not yours.
4. **Single-word resonance** — "fire" in Genesis 19 and "fire" in
   2 Peter 3 share a word; that is a keyword match, not a link.
   Propose only when the *function* of the motif matches.
5. **Anachronistic theological framings** — do not project later
   systematic categories (Reformed covenant theology, dispensational
   schemas, modern eschatological labels) onto OT texts that did not
   originally bear them.
6. **Speculative numerology, gematria, allegorical fancies** — these
   waste reviewer time and damage the corpus's reliability.
7. **Modern application analogies** — "this verse is like our
   modern X" is sermon material, not a cross-reference.
8. **Self-references within the same book/chapter** — propose links
   to a *different* book where possible. Same-book links are
   acceptable only when crossing a major literary boundary
   (e.g., Genesis 1-11 to Genesis 12+, or Isaiah 1-39 to 40-66).

# DISAMBIGUATION

Common borderline calls:

- **Typological vs thematic.** If the NT explicitly invokes an OT
  figure as a type (Heb on Melchizedek; Rom 5 on Adam; Jhn 3 on the
  serpent), it is typological even if the connection is also
  thematic. When the NT does not name the OT figure but the motif
  recurs across books, it is thematic.
- **Thematic vs idiomatic.** If the connection is at the level of
  *idea*, it is thematic. If it is at the level of *phrasing*, it
  is idiomatic. "The day of the Lord" can be either, depending on
  whether you are pointing at the eschatological doctrine
  (thematic) or the formulaic phrase (idiomatic).
- **Idiomatic vs keyword match.** Idiomatic links require a
  theologically-loaded *figure of speech*, not a single shared
  word. "Lift up your eyes" is idiomatic; "eyes" is a keyword.

# CONFIDENCE CALIBRATION

Use the following scale. Be honest. The reviewer trusts your
calibration; sandbagging or inflating both reduce signal.

  - **0.85-1.00:** NT writer or major OT prophet explicitly invokes
    the link. (Heb 7 on Melchizedek; Mat 1:23 quoting Isa 7:14.)
  - **0.65-0.84:** Strong scholarly consensus the link is intended
    by the canonical authors, even without explicit citation.
    (Joseph as type of Christ; covenant renewal arc.)
  - **0.45-0.64:** Recurring canonical motif that a careful reader
    would notice. (Wilderness testing; remnant theology.)
  - **0.25-0.44:** Plausible echo, but reasonable readers might
    differ. Reviewer should look closely.
  - **0.00-0.24:** Speculative — generally do not propose at this
    level unless the user-facing surface is "show all possible
    links." Default to omission.

# OUTPUT FORMAT

The API enforces a JSON schema; you must return STRICT JSON only,
with no prose, no markdown fences, no preamble. Shape:

{
  "proposals": [
    {
      "target_book": "<3-letter canonical code, lowercase>",
      "target_chapter": <int, >= 1>,
      "target_verse": <int, >= 1>,
      "kind_subclass": "typological" | "thematic" | "idiomatic",
      "reasoning": "<1-2 sentences explaining WHY this is a link, not just WHAT both verses are about>",
      "confidence": <float, 0.0..1.0>
    }
    // ... up to N entries, ordered by descending confidence
  ]
}

If no strong proposals exist for the verse, return:

  {"proposals": []}

This is the right answer for narrative connective tissue (genealogy
verses, transitional sentences, formulaic openings) where forced
proposals would be noise.

# CANONICAL BOOK CODES (use these EXACTLY — never invent others)

Old Testament (Protestant + Hebrew Bible order):
  gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh
  est job psa pro ecc sng isa jer lam eze dan hos joe amo oba jon
  mic nah hab zep hag zec mal

New Testament:
  mat mrk luk jhn act rom 1co 2co gal eph phi col 1th 2th 1ti 2ti
  tit phm heb jam 1pe 2pe 1jn 2jn 3jn jud rev

Deuterocanon (Catholic / Orthodox / Tewahedo — only if the link is
unambiguously to the deuterocanonical text, not a parallel found in
the Protestant canon):
  tob jdt wis sir bar lje paz sus bel 1es 2es man 1ma 2ma aes
  mq1 mq2 mq3 jub 1en 2en 4ba 1cl

If you are tempted to use a code not on these lists — for example,
"songofsongs" or "matthew" or "1maccabees" — STOP and use the
3-letter form. The platform's promote step rejects unknown codes
and your proposal will be silently dropped.

# REASONING FIELD GUIDANCE

The reasoning field is for the reviewer, not the model. Two
sentences max. Name the connection mechanism explicitly:

  Good: "Both passages develop the suffering-servant motif Isaiah
  introduces in 42:1-4 and 53; Acts 8:32-35 makes the typological
  link explicit when Philip identifies the servant with Christ."

  Good: "Phrase 'lift up your eyes' marks a moment of revelatory
  vision in both verses (Gen 22:4 sees the place of sacrifice; Jhn
  4:35 sees the harvest); idiomatic, not propositional."

  Bad: "Both verses are about Jesus." (Vague; what is the link
  mechanism?)

  Bad: "Strong thematic resonance." (Confidence-claim, not
  explanation.)

  Bad: "See Henry's commentary." (External reference; the reviewer
  needs to evaluate YOUR judgment.)

# GENRE-SPECIFIC GUIDANCE

The right kind of link depends heavily on the genre of the source
verse. The proposer should adjust both expectations and confidence
calibration based on what kind of text it is reading.

## Narrative (Genesis-Esther, Gospels, Acts)

Narrative verses often participate in **typological structures**
the canon develops over time. A narrative detail in Genesis or
Exodus may anticipate a narrative detail in the Gospels or Acts.
Look for:

  - Repeated narrative shapes (call narratives, exodus patterns,
    wilderness wanderings, exile-and-return, suffering-vindication).
  - Object/person types (ark, lamb, rock, shepherd, son, bride).
  - Place echoes (mountain, garden, wilderness, river, temple).
  - Phrase formulas opening major movements ("And it came to pass,"
    "In the beginning," "Now in the days of...").

Narrative connective tissue (genealogies, transitional verses,
purely chronological notes) usually has no strong cross-references
to propose. Empty `proposals` is the right answer for "And Jared
lived an hundred sixty and two years, and he begat Enoch."

## Wisdom (Job, Psalms, Proverbs, Ecclesiastes, Song of Songs)

Wisdom literature works by aphorism, parallelism, and recurring
motif more than narrative chronology. Look for:

  - Theological motifs the Psalter develops across many psalms
    (refuge, righteous-vs-wicked, deliverance, kingship of YHWH).
  - Wisdom-tradition cross-references between Proverbs and the
    sayings of Jesus (Mat 5-7, Lk 6, Jam).
  - Lament-form parallels (Psa 22 with NT passion narratives).
  - Royal psalms (Psa 2, 45, 72, 110) with NT christological use.

Be careful: Proverbs often makes general observations about life
that incidentally resemble many other verses. Propose a link only
when the *specific* aphorism connects to a *specific* later text.

## Prophecy (Isaiah-Malachi, Revelation)

Prophecy is rich in idiomatic formulas ("the day of the Lord,"
"thus saith the Lord," "behold, the days come"), recurring
theological themes (judgment-and-restoration, remnant, new
covenant, servant), and direct typological material the NT
explicitly applies. Look for:

  - Servant texts (Isa 42, 49, 50, 53) with NT christological use.
  - "New covenant" language (Jer 31:31-34) and NT inauguration
    accounts (Luk 22:20, Heb 8:8-12).
  - Apocalyptic imagery shared across Daniel, Ezekiel, Zechariah,
    and Revelation.
  - Restoration-of-Israel oracles and NT echoes (Rom 9-11).

Apocalyptic imagery in particular invites speculative pattern-
matching; resist it. Only propose links where multiple texts
develop the same theological idea, not where they share a single
striking image.

## Epistles (Romans-Jude)

Epistolary verses argue rather than narrate. Look for:

  - Explicit OT citations the writer makes (often these are
    already in TSK; do not duplicate).
  - OT typology the writer assumes without quoting (Heb's
    Melchizedek, 1 Cor 10's wilderness types, Rom 5's Adam).
  - Cross-epistle resonances (1 Pet 2:21-25 echoes Isa 53; Heb 11
    surveys OT figures).
  - Liturgical or hymnic fragments embedded in prose (Phi 2:5-11,
    Col 1:15-20, 1 Tim 3:16) and OT echoes within them.

## Apocalyptic (Daniel, Revelation, parts of Ezekiel and Zechariah)

Apocalyptic shares a dense imagic vocabulary across centuries.
Many of Revelation's images quote or allude to OT apocalyptic
without explicit citation. Look for:

  - Daniel→Revelation parallels (beasts, seventy weeks, son of
    man).
  - Ezekiel→Revelation parallels (throne vision, four living
    creatures, scroll-eating, new temple, river of life).
  - Zechariah→Revelation parallels (lampstands, horsemen, two
    witnesses).
  - Joel's locust army (Joe 1-2) and Revelation 9.

Confidence on apocalyptic links should be calibrated by how widely
recognized the parallel is in scholarship — well-known parallels
get high confidence; novel proposals should be conservative.

# ADDITIONAL ANTI-PATTERNS WITH WORKED EXAMPLES

## Anti-pattern: "both verses contain the same word"

  - Bad proposal: Gen 1:3 ("let there be light") → 2 Cor 4:6 ("the
    light shall shine out of darkness") because both contain
    "light." This is just keyword overlap.
  - Better proposal (if any): only flag this if Paul is *deliberately
    invoking* Gen 1; in 2 Cor 4:6 he is, and confidence is high
    because it's a quotation. Ground the link in *intent*, not the
    shared word.

## Anti-pattern: speculative chiasm or numerology

  - Bad proposal: "This is the third occurrence of 'forty days' in
    the canon, suggesting a typological link with Gen 7:12, Exo
    24:18, and Mat 4:2." Forty-day patterns recur; flag them only
    when a specific NT text invokes a specific OT instance, not as
    a generic "all forty-day events are linked."

## Anti-pattern: importing modern theological frameworks

  - Bad proposal: Reading "covenant of works / covenant of grace"
    Reformed categories into Genesis 2-3 and proposing links on
    that basis. The proposer's job is to surface canonical
    resonances, not to systematize them.

## Anti-pattern: cherry-picking partial parallels

  - Bad proposal: Two verses that share the *first half* of an
    image but diverge sharply in the second half. Example: linking
    Psa 22:1 ("My God, my God, why hast thou forsaken me?") and
    Mat 27:46 (the same words on the cross) is excellent — that's
    a quotation. But linking Psa 22:18 (casting lots for clothing)
    to a Gospel verse that does NOT involve casting lots, just
    because both are passion-related, is overreach.

## Anti-pattern: "this reminds me of..."

  - Bad proposal: A preacher's sermon-style "this reminds me of
    ..." association. Cross-references should reflect what the
    text *does*, not what it evokes for a modern reader.

# CONFIDENCE CALIBRATION: WORKED EXAMPLES

Calibrate by walking through realistic examples:

  - **0.95** — Mat 1:23 and Isa 7:14. The NT writer quotes the OT
    text and applies it directly to Christ.
  - **0.88** — 1 Cor 10:1-4 and Exo 13-17. Paul explicitly types
    the wilderness events as "ensamples" for the church.
  - **0.78** — Heb 11:8-19 and Gen 12-22. Hebrews names Abraham
    and walks through Genesis episodes as exemplary faith; the
    link is strong but interpretive rather than directly quoted.
  - **0.65** — Joseph (Gen 37-50) and Christ. NT does not name
    Joseph as a type, but the church's reading tradition is
    consistent and defensible.
  - **0.55** — Recurrence of "wilderness" as testing across Exo,
    Deu, Hos 2, Mat 4. The motif is real and trans-canonical, but
    the specific verse-to-verse link will vary in strength.
  - **0.40** — A literary parallel a careful reader notices but
    that scholars have not made canonical. Reviewer should weigh
    it on the merits.
  - **0.20** — A speculative resonance. Generally do not propose
    at this level; reviewer time is better spent on stronger
    links.

# FINAL CHECK BEFORE EMITTING

Before returning, ask yourself five questions about each
proposal you are about to emit:

  1. Is this already in TSK / Strong's / Nave's? (If yes, omit.)
  2. Does the link rest on more than a single shared word? (If no,
     omit.)
  3. Can I name the connection mechanism in one sentence (type,
     theme, idiom, formula)? (If no, omit.)
  4. Would a competent commentator agree the connection is
     defensible, even if interpretive? (If no, lower confidence
     or omit.)
  5. Is my confidence calibrated honestly to how strong the link
     actually is? (If sandbagging or inflating, fix it.)

A short list of high-quality links is far more valuable than a
long list padded with weak ones. The corpus aims for reviewer-
curated quality, not coverage. When the verse genuinely lacks
strong cross-references — for genealogies, transitional sentences,
or formulaic openings — the right answer is `{"proposals": []}`.
"""


class AnthropicXrefClient:
    """LLM-backed proposer for thematic / typological / idiomatic
    cross-references. Phase χ-AI-xrefs (2026-05-08).

    Construction contract mirrors the static-source loaders: raises
    ``SourceMissingError`` when neither a real Anthropic SDK + API key
    nor an injected ``completion_fn`` is available. ``prospect.py``'s
    resilient detector instantiation catches that and skips the
    detector silently — same graceful-degrade contract as
    ``NaveTopical`` when its JSON cache is absent.

    The injected ``completion_fn(system_prompt, user_message, *,
    model)`` returns the parsed completion as a Python dict matching
    the documented shape. Tests pass a stub fn so no real network
    calls are made.

    The default ``completion_fn`` uses the ``anthropic`` SDK with
    prompt caching on the system prompt — repeated per-verse calls
    only pay for the per-verse user message after the first call,
    cutting cost roughly 10×.
    """

    def __init__(
        self,
        *,
        model: str = DEFAULT_AI_XREF_MODEL,
        completion_fn: Optional[Callable] = None,
    ) -> None:
        self.model = model
        if completion_fn is not None:
            self._completion_fn = completion_fn
        else:
            # Validate the real-SDK preconditions before locking in the
            # default fn — fail at construction time, not on first call.
            if not os.environ.get("ANTHROPIC_API_KEY"):
                raise SourceMissingError(
                    "ANTHROPIC_API_KEY environment variable not set. "
                    "Set it (export ANTHROPIC_API_KEY=...) or pass an "
                    "injected completion_fn."
                )
            try:
                import anthropic  # noqa: F401
            except ImportError as e:
                raise SourceMissingError(
                    "The 'anthropic' Python SDK is not installed. "
                    "Install it (pip install anthropic) or pass an "
                    "injected completion_fn."
                ) from e
            self._completion_fn = self._default_completion_fn

        # Validation set: only book codes the platform actually has are
        # accepted from the model. Built lazily because importing
        # config at module-load time would be heavier than necessary.
        self._valid_book_codes: Optional[set[str]] = None

        # Telemetry from the most recent _default_completion_fn call.
        # Stub completion_fns leave this as None; the real SDK path
        # populates it so the at-scale driver can verify cache hits
        # before paying for a full run. Shape:
        #   {"input_tokens": int, "output_tokens": int,
        #    "cache_creation_input_tokens": int,
        #    "cache_read_input_tokens": int, "request_id": str | None}
        self.last_usage: Optional[dict] = None

    @property
    def attribution(self) -> str:
        return (
            f"Claude AI ({self.model}, Anthropic, 2026); "
            "reviewer-curated."
        )

    def _valid_codes(self) -> set[str]:
        if self._valid_book_codes is None:
            from . import config as _cfg
            self._valid_book_codes = set(_cfg.books_by_code().keys())
        return self._valid_book_codes

    def propose_xrefs(
        self,
        book: str,
        chapter: int,
        verse: int,
        verse_text: str,
        *,
        top_n: int = 3,
    ) -> list[dict]:
        """Ask the model for up to ``top_n`` thematic xref proposals
        for the given verse. Returns a list of dicts with fields
        ``target_book``, ``target_chapter``, ``target_verse``,
        ``kind_subclass``, ``reasoning``, ``confidence``. Defensive
        against malformed model output (returns ``[]``)."""
        user_message = (
            f"Propose up to {top_n} cross-references for:\n"
            f"  Book:    {book}\n"
            f"  Chapter: {chapter}\n"
            f"  Verse:   {verse}\n"
            f"  Text:    {verse_text}\n"
        )
        # Catch only failures we can defensively degrade through —
        # SDK errors (with retry exhausted), JSON-shape failures the
        # schema didn't catch, value coercion errors. Programming
        # errors (TypeError, AttributeError, etc.) propagate so they
        # surface in tests rather than silently producing empty
        # outputs.
        try:
            parsed = self._completion_fn(
                AI_XREF_SYSTEM_PROMPT,
                user_message,
                model=self.model,
            )
        except (json.JSONDecodeError, ValueError, OSError):
            return []
        except Exception as e:
            # Anthropic SDK exceptions are dynamically-named subclasses
            # of APIError; we can't import the SDK at module top
            # without breaking the no-dep test path, so catch by name.
            if type(e).__module__.startswith("anthropic"):
                return []
            raise

        if not isinstance(parsed, dict):
            return []
        proposals = parsed.get("proposals")
        if not isinstance(proposals, list):
            return []

        valid = self._valid_codes()
        out: list[dict] = []
        for p in proposals[:top_n]:
            if not isinstance(p, dict):
                continue
            target_book = p.get("target_book")
            if not isinstance(target_book, str) or target_book not in valid:
                continue
            try:
                target_chapter = int(p.get("target_chapter"))
                target_verse = int(p.get("target_verse"))
            except (TypeError, ValueError):
                continue
            if target_chapter < 1 or target_verse < 1:
                continue
            try:
                confidence = float(p.get("confidence", 0.0))
            except (TypeError, ValueError):
                continue
            # Clamp confidence into [0, 1]
            confidence = max(0.0, min(1.0, confidence))
            kind_subclass = p.get("kind_subclass") or "thematic"
            if kind_subclass not in ("typological", "thematic", "idiomatic"):
                kind_subclass = "thematic"
            reasoning = p.get("reasoning") or ""
            if not isinstance(reasoning, str):
                reasoning = ""
            out.append({
                "target_book": target_book,
                "target_chapter": target_chapter,
                "target_verse": target_verse,
                "kind_subclass": kind_subclass,
                "reasoning": reasoning.strip(),
                "confidence": confidence,
            })
        return out

    def _default_completion_fn(
        self,
        system_prompt: str,
        user_message: str,
        *,
        model: str,
    ) -> dict:
        """Real SDK call. Only reached when the constructor confirmed
        the SDK + API key are available.

        Uses three Anthropic SDK features for cost + correctness:

        - **Prompt caching with 1h TTL** on the system prompt so
          per-verse calls only pay for the user message after the
          first call. The 4096-token-minimum-prefix invariant for
          Haiku 4.5 is satisfied by the padded system prompt above.
        - **Structured output** via ``output_config.format`` with a
          json_schema. The model is forced to return valid JSON of
          the documented shape — no regex-strip-fences hack, no
          json.JSONDecodeError on stray prose.
        - **Cached SDK client** at module level (see
          ``_anthropic_client()`` below) so the 31K-call full pass
          doesn't reconstruct the client per verse.

        Populates ``self.last_usage`` so the at-scale driver can
        verify cache hits and report cost telemetry before
        committing to a long paid run."""
        client = _anthropic_client()
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {
                        "type": "ephemeral",
                        "ttl": AI_XREF_CACHE_TTL,
                    },
                }
            ],
            messages=[{"role": "user", "content": user_message}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": AI_XREF_OUTPUT_SCHEMA,
                },
            },
        )
        # Capture telemetry before parsing so cache-hit info survives
        # even if the JSON parse fails downstream (it shouldn't —
        # the schema enforces shape — but record it regardless).
        usage = response.usage
        self.last_usage = {
            "input_tokens": getattr(usage, "input_tokens", 0),
            "output_tokens": getattr(usage, "output_tokens", 0),
            "cache_creation_input_tokens": getattr(
                usage, "cache_creation_input_tokens", 0,
            ),
            "cache_read_input_tokens": getattr(
                usage, "cache_read_input_tokens", 0,
            ),
            "request_id": getattr(response, "_request_id", None),
        }
        # output_config.format guarantees the first content block is
        # text containing valid JSON matching the schema.
        text = next(
            (block.text for block in response.content
             if block.type == "text"),
            "",
        )
        return json.loads(text)


# JSON schema for the structured-output contract. Forces the model
# to emit a `proposals` array with the documented per-item shape.
# additionalProperties=False prevents the model from sneaking in
# unrecognized fields that downstream code would silently ignore.
AI_XREF_OUTPUT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "proposals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "target_book": {"type": "string"},
                    "target_chapter": {"type": "integer"},
                    "target_verse": {"type": "integer"},
                    "kind_subclass": {
                        "type": "string",
                        "enum": ["typological", "thematic", "idiomatic"],
                    },
                    "reasoning": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": [
                    "target_book", "target_chapter", "target_verse",
                    "kind_subclass", "reasoning", "confidence",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["proposals"],
    "additionalProperties": False,
}


@lru_cache(maxsize=1)
def _anthropic_client():
    """Cached Anthropic SDK client. The default constructor reads
    ANTHROPIC_API_KEY from the env, parses platform config, and
    builds an httpx pool — re-running per call (31K calls for the
    full pass) wastes that setup cost. SDK retries (default
    max_retries=2) handle 429 / 5xx automatically.

    Lazy-imported inside the function so module load doesn't fail
    when the SDK isn't installed (the no-API-key code path)."""
    import anthropic
    return anthropic.Anthropic()


@lru_cache(maxsize=1)
def anthropic_xref_client() -> AnthropicXrefClient:
    """Return the singleton AnthropicXrefClient (lazy-loaded once).
    Raises ``SourceMissingError`` if the SDK/API key are unavailable."""
    return AnthropicXrefClient()


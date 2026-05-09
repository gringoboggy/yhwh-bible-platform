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
DEFAULT_AI_XREF_MODEL = "claude-haiku-4-5-20251001"


# System prompt for the xref proposer. Tightly templated so the model
# returns a strict JSON shape; prompt-cached so repeated per-verse calls
# only pay for the per-verse user message after the first call.
AI_XREF_SYSTEM_PROMPT = """You are a biblical cross-reference proposer.

Given one Bible verse (book, chapter, verse, KJV text), propose up to
N thematic, typological, or idiomatic cross-references — the kind a
careful pastor or scholar would notice on a re-read but a static
keyword/citation index (TSK, Strong's, Nave's) misses.

Focus on:
- Typology (Adam→Christ; Joseph→Christ; brazen serpent→Jn 3:14)
- Thematic resonance across canon (remnant theology; wilderness trope;
  covenant renewal; suffering servant)
- Idiomatic / phraseological echoes (Hebrew/Greek figures of speech
  that survive translation)

Avoid:
- Direct citations already obvious (TSK has them).
- Single-keyword matches (Strong's has them).
- Topical groupings (Nave's has them).
- Speculative or fanciful links — be conservative.

Return STRICT JSON only, no prose. Shape:

{
  "proposals": [
    {
      "target_book": "<3-letter canonical code>",
      "target_chapter": <int>,
      "target_verse": <int>,
      "kind_subclass": "typological" | "thematic" | "idiomatic",
      "reasoning": "<1-2 sentences explaining the link>",
      "confidence": <float 0.0..1.0>
    },
    ...
  ]
}

If no strong proposals exist, return {"proposals": []}.

Canonical 3-letter book codes (use exactly these — do not invent
others): gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr
neh est job psa pro ecc sng isa jer lam eze dan hos joe amo oba jon
mic nah hab zep hag zec mal mat mrk luk jhn act rom 1co 2co gal eph
phi col 1th 2th 1ti 2ti tit phm heb jam 1pe 2pe 1jn 2jn 3jn jud rev

Deuterocanon (only if relevant): tob jdt wis sir bar lje paz sus bel
1es 2es man 1ma 2ma aes mq1 mq2 mq3 jub 1en 2en 4ba 1cl
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
        try:
            parsed = self._completion_fn(
                AI_XREF_SYSTEM_PROMPT,
                user_message,
                model=self.model,
            )
        except Exception:
            # Network blip / SDK exception / parse fail — defensively
            # degrade to no proposals rather than abort the driver.
            return []

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
        the SDK + API key are available. Uses prompt caching on the
        system prompt so repeated per-verse calls only pay for the
        per-verse user message after the first call."""
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=model,
            max_tokens=512,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        # Concatenate text blocks; the model is instructed to return
        # strict JSON, but it occasionally wraps with code fences.
        text = "".join(
            getattr(block, "text", "") for block in msg.content
        ).strip()
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE)
        return json.loads(text)


@lru_cache(maxsize=1)
def anthropic_xref_client() -> AnthropicXrefClient:
    """Return the singleton AnthropicXrefClient (lazy-loaded once).
    Raises ``SourceMissingError`` if the SDK/API key are unavailable."""
    return AnthropicXrefClient()


"""
sources.py — Loaders for the public-domain reference corpora cached
under ``content/sources/`` by ``scripts/fetch_sources.py``.

Each source class loads lazily (first call) and caches in memory. The
public API is read-only; ``fetch_sources.py`` is the only writer.

Public API:
    StrongsHebrew()         — entries keyed by H-number
    Tsk()                   — cross-refs keyed by (book, chapter, verse)
    NavesTopical()          — topical-concordance hits, both directions
                              (Phase χ.7)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SOURCES = _REPO_ROOT / "content" / "sources"


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
def tsk() -> Tsk:
    """Return the singleton Tsk instance (lazy-loaded once)."""
    return Tsk()


@lru_cache(maxsize=1)
def naves_topical() -> NavesTopical:
    """Return the singleton NavesTopical instance (lazy-loaded once)."""
    return NavesTopical()


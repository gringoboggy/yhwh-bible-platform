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
from collections.abc import Callable

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
        topic_list = (self._verses.get(book, {}).get(str(chapter), {}).get(str(verse))) or []
        return list(topic_list)[:top_n]

    def verses_for(self, topic: str) -> list[NaveTopicHit]:
        """Return every verse tagged with this topic."""
        raw = self._topics.get(topic) or []
        return [
            NaveTopicHit(topic=topic, target_book=r[0], target_chapter=int(r[1]), target_verse=int(r[2]))
            for r in raw
            if len(r) >= 3
        ]


# ----------------------------------------------------------------------
# Patristic commentary corpus (γ.3 — 2026-05-11)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class PatristicCommentary:
    """One verse-keyed Church Father commentary entry.

    Each entry summarizes a Father's interpretation of a specific verse;
    the source `attribution` field embeds the precise translation
    citation (NPNF series + volume) so promoted notes carry their
    provenance into the YAML.

    See `content/sources/patristic_commentaries.json` for the live
    dataset; future γ.3.x will expand from the current ~8-entry
    Augustine-on-Genesis seed into a fuller corpus drawn from the
    NPNF dump.
    """

    book: str
    chapter: int
    verse: int
    father: str
    work: str
    year: int
    summary: str
    attribution: str


class PatristicCommentaries:
    """Lazy loader for the Patristic commentary corpus. Cached on
    first read. Raises ``SourceMissingError`` if the JSON cache file
    is absent.

    Two access patterns:
      * ``for_verse(book, chapter, verse)`` — every commentary entry
        targeting one specific verse (used by the detector).
      * ``by_father(name)`` — every entry by a given Church Father
        (e.g. ``"Augustine"``), for audit / coverage UIs.
    """

    PATH = _SOURCES / "patristic_commentaries.json"

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError(
                f"Patristic commentaries cache not present at {self.PATH}. "
                "The seed corpus shipped with γ.3 (2026-05-11) — restore from git."
            )
        with self.PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        # Index by (book, chapter, verse) for O(1) per-verse lookup.
        self._by_verse: dict[tuple[str, int, int], list[PatristicCommentary]] = {}
        # Also index by father name for the audit case.
        self._by_father: dict[str, list[PatristicCommentary]] = {}
        for entry in data.get("entries", []):
            try:
                pc = PatristicCommentary(
                    book=str(entry["book"]),
                    chapter=int(entry["chapter"]),
                    verse=int(entry["verse"]),
                    father=str(entry["father"]),
                    work=str(entry.get("work", "")),
                    year=int(entry.get("year", 0)),
                    summary=str(entry["summary"]),
                    attribution=str(entry["attribution"]),
                )
            except (KeyError, ValueError, TypeError):
                # Malformed entry — skip silently. The schema is
                # documented in the JSON's _meta block; this is
                # defensive against hand-edit typos.
                continue
            key = (_normalize_book_code(pc.book), pc.chapter, pc.verse)
            self._by_verse.setdefault(key, []).append(pc)
            self._by_father.setdefault(pc.father, []).append(pc)

    def __len__(self) -> int:
        return sum(len(v) for v in self._by_verse.values())

    def for_verse(self, book: str, chapter: int, verse: int) -> list[PatristicCommentary]:
        """Return every commentary entry attached to a specific verse,
        in insertion order (which the JSON keeps as chronological per
        father since most Fathers wrote sequentially). Returns an
        empty list for verses with no commentary."""
        return list(self._by_verse.get((_normalize_book_code(book), int(chapter), int(verse)), ()))

    def by_father(self, name: str) -> list[PatristicCommentary]:
        """Return every entry by a given Church Father (case-sensitive).
        Useful for coverage audits or a future per-Father console."""
        return list(self._by_father.get(name, ()))


# ----------------------------------------------------------------------
# Ethiopian commentary corpus (γ.4 — 2026-05-11)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class EthiopianCommentary:
    """One verse-keyed entry in the Ethiopian Tewahedo commentary corpus.

    Shape mirrors `PatristicCommentary` so the detector layer can stay
    structurally parallel to γ.3. The semantic distinction is the
    *tradition*: these entries come from the Syriac fathers (Ephrem),
    the non-Chalcedonian Alexandrian school (Cyril), the Tewahedo-
    canonical 1 Enoch (R.H. Charles' PD 1912 translation), and the
    Ethiopian Andəmta / Synaxarium / Fetha Nagast tradition — the
    sources distinctively received by the Ethiopian Tewahedo communion.

    See `content/sources/ethiopian_commentaries.json` for the live
    dataset; γ.4 ships a ~12-entry seed across Genesis / Psalms / John,
    and future γ.4.x will expand from the NPNF + Charles ETLs.
    """

    book: str
    chapter: int
    verse: int
    father: str
    work: str
    year: int
    summary: str
    attribution: str


class EthiopianCommentaries:
    """Lazy loader for the Ethiopian commentary corpus. Cached on
    first read. Raises ``SourceMissingError`` if the JSON cache file
    is absent.

    Two access patterns mirror `PatristicCommentaries`:
      * ``for_verse(book, chapter, verse)`` — every entry attached to
        the verse (used by the detector).
      * ``by_father(name)`` — every entry by a given source (e.g.
        ``"Ephrem the Syrian"``), for audit / coverage UIs.
    """

    PATH = _SOURCES / "ethiopian_commentaries.json"

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError(
                f"Ethiopian commentaries cache not present at {self.PATH}. "
                "The seed corpus shipped with γ.4 (2026-05-11) — restore from git."
            )
        with self.PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        self._by_verse: dict[tuple[str, int, int], list[EthiopianCommentary]] = {}
        self._by_father: dict[str, list[EthiopianCommentary]] = {}
        for entry in data.get("entries", []):
            try:
                ec = EthiopianCommentary(
                    book=str(entry["book"]),
                    chapter=int(entry["chapter"]),
                    verse=int(entry["verse"]),
                    father=str(entry["father"]),
                    work=str(entry.get("work", "")),
                    year=int(entry.get("year", 0)),
                    summary=str(entry["summary"]),
                    attribution=str(entry["attribution"]),
                )
            except (KeyError, ValueError, TypeError):
                continue
            key = (_normalize_book_code(ec.book), ec.chapter, ec.verse)
            self._by_verse.setdefault(key, []).append(ec)
            self._by_father.setdefault(ec.father, []).append(ec)

    def __len__(self) -> int:
        return sum(len(v) for v in self._by_verse.values())

    def for_verse(self, book: str, chapter: int, verse: int) -> list[EthiopianCommentary]:
        """Return every entry attached to a specific verse, in insertion
        order. Empty list when nothing matches."""
        return list(self._by_verse.get((_normalize_book_code(book), int(chapter), int(verse)), ()))

    def by_father(self, name: str) -> list[EthiopianCommentary]:
        """Return every entry by a given source (case-sensitive). The
        'father' field is sometimes a tradition rather than a person
        (e.g. '1 Enoch (Ethiopian tradition)') — that's deliberate;
        the audit UI groups by it identically."""
        return list(self._by_father.get(name, ()))


# ----------------------------------------------------------------------
# Protestant commentary corpus (χ.2 — 2026-05-12)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class ProtestantCommentary:
    """One verse-keyed entry in the post-Reformation Protestant corpus.

    Shape parallels `PatristicCommentary` and `EthiopianCommentary` so the
    detector layer stays structurally uniform across the comm-* cluster.
    The semantic distinction is twofold: (a) the *tradition* — these are
    post-Reformation English Nonconformist / Puritan / Evangelical
    expositors rather than Church Fathers or magisterial Reformers; and
    (b) the *field name* — `commentator` rather than `father`, since
    Matthew Henry / Spurgeon / Edwards / Hodge are not Fathers in any
    historical sense.

    See `content/sources/protestant_commentaries.json` for the live
    dataset; χ.2 ships a ~12-entry Matthew Henry seed across Genesis /
    Psalms / John, and future χ.2.x will expand from the CCEL /
    Project Gutenberg dump via per-pericope summarization.
    """

    book: str
    chapter: int
    verse: int
    commentator: str
    work: str
    year: int
    summary: str
    attribution: str


class ProtestantCommentaries:
    """Lazy loader for the Protestant commentary corpus. Cached on
    first read. Raises ``SourceMissingError`` if the JSON cache file
    is absent.

    Two access patterns mirror the γ.3/γ.4 loaders:
      * ``for_verse(book, chapter, verse)`` — every entry attached to
        the verse (used by the detector).
      * ``by_commentator(name)`` — every entry by a given expositor
        (e.g. ``"Matthew Henry"``), for audit / coverage UIs.
    """

    PATH = _SOURCES / "protestant_commentaries.json"

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError(
                f"Protestant commentaries cache not present at {self.PATH}. "
                "The seed corpus shipped with χ.2 (2026-05-12) — restore from git."
            )
        with self.PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        self._by_verse: dict[tuple[str, int, int], list[ProtestantCommentary]] = {}
        self._by_commentator: dict[str, list[ProtestantCommentary]] = {}
        for entry in data.get("entries", []):
            try:
                pc = ProtestantCommentary(
                    book=str(entry["book"]),
                    chapter=int(entry["chapter"]),
                    verse=int(entry["verse"]),
                    commentator=str(entry["commentator"]),
                    work=str(entry.get("work", "")),
                    year=int(entry.get("year", 0)),
                    summary=str(entry["summary"]),
                    attribution=str(entry["attribution"]),
                )
            except (KeyError, ValueError, TypeError):
                continue
            key = (_normalize_book_code(pc.book), pc.chapter, pc.verse)
            self._by_verse.setdefault(key, []).append(pc)
            self._by_commentator.setdefault(pc.commentator, []).append(pc)

    def __len__(self) -> int:
        return sum(len(v) for v in self._by_verse.values())

    def for_verse(self, book: str, chapter: int, verse: int) -> list[ProtestantCommentary]:
        """Return every entry attached to a specific verse, in insertion
        order. Empty list when nothing matches."""
        return list(self._by_verse.get((_normalize_book_code(book), int(chapter), int(verse)), ()))

    def by_commentator(self, name: str) -> list[ProtestantCommentary]:
        """Return every entry by a given expositor (case-sensitive)."""
        return list(self._by_commentator.get(name, ()))


# ----------------------------------------------------------------------
# Catholic commentary corpus (χ.4 — 2026-05-12)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class CatholicCommentary:
    """One verse-keyed entry in the medieval Catholic exegetical corpus.

    Shape parallels `PatristicCommentary` and `EthiopianCommentary` —
    field name `father` is preserved because every voice surfaced
    through Aquinas's Catena Aurea is itself a Church Father (Augustine,
    Chrysostom, Jerome, Origen, Cyril, Bede, Gregory the Great,
    Theophylact, etc.). The semantic distinction from γ.3 is the
    *framing tradition*: these are Father voices selected and stitched
    by Aquinas's medieval Catholic editorial hand — the same Father may
    appear in both γ.3 (Augustine on Genesis, e.g.) and χ.4 (Augustine
    on the Gospels via the Catena), tagged with different kinds
    according to which tradition's reception apparatus surfaces them.

    Coverage is Gospels-only per the Catena's original scope: Matthew,
    Mark, Luke, John.

    See `content/sources/catholic_commentaries.json` for the live
    dataset; χ.4 ships a ~12-entry seed across all four Gospels, and
    future χ.4.x will expand from the Newman/Pusey 1841-1845 Oxford
    edition (CCEL hosts the full PD text).
    """

    book: str
    chapter: int
    verse: int
    father: str
    work: str
    year: int
    summary: str
    attribution: str


class CatholicCommentaries:
    """Lazy loader for the Catholic (Catena Aurea) commentary corpus.
    Cached on first read. Raises ``SourceMissingError`` if the JSON
    cache file is absent.

    Two access patterns mirror γ.3/γ.4:
      * ``for_verse(book, chapter, verse)`` — every entry attached to
        the verse (used by the detector).
      * ``by_father(name)`` — every entry by a given Church Father as
        surfaced via the Catena (e.g. ``"Augustine"``), for audit /
        coverage UIs.
    """

    PATH = _SOURCES / "catholic_commentaries.json"

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError(
                f"Catholic commentaries cache not present at {self.PATH}. "
                "The seed corpus shipped with χ.4 (2026-05-12) — restore from git."
            )
        with self.PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        self._by_verse: dict[tuple[str, int, int], list[CatholicCommentary]] = {}
        self._by_father: dict[str, list[CatholicCommentary]] = {}
        for entry in data.get("entries", []):
            try:
                cc = CatholicCommentary(
                    book=str(entry["book"]),
                    chapter=int(entry["chapter"]),
                    verse=int(entry["verse"]),
                    father=str(entry["father"]),
                    work=str(entry.get("work", "")),
                    year=int(entry.get("year", 0)),
                    summary=str(entry["summary"]),
                    attribution=str(entry["attribution"]),
                )
            except (KeyError, ValueError, TypeError):
                continue
            key = (_normalize_book_code(cc.book), cc.chapter, cc.verse)
            self._by_verse.setdefault(key, []).append(cc)
            self._by_father.setdefault(cc.father, []).append(cc)

    def __len__(self) -> int:
        return sum(len(v) for v in self._by_verse.values())

    def for_verse(self, book: str, chapter: int, verse: int) -> list[CatholicCommentary]:
        """Return every entry attached to a specific verse, in insertion
        order. Empty list when nothing matches."""
        return list(self._by_verse.get((_normalize_book_code(book), int(chapter), int(verse)), ()))

    def by_father(self, name: str) -> list[CatholicCommentary]:
        """Return every entry by a given Church Father (case-sensitive),
        as surfaced through Aquinas's Catena Aurea."""
        return list(self._by_father.get(name, ()))


# ----------------------------------------------------------------------
# Reformation commentary corpus (χ.3 — 2026-05-12)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class ReformationCommentary:
    """One verse-keyed entry in the 16th c. magisterial Reformation corpus.

    Shape parallels `ProtestantCommentary` — field name `commentator`
    rather than `father` because the magisterial Reformers (Calvin,
    Luther, Zwingli, Anabaptist expositors) are not Fathers in the
    patristic sense; they are 16th c. confessional theologians. The
    semantic distinction from χ.2 (`comm-protestant`) is *period*:
    χ.3 covers the 16th c. magisterial Reformation narrowly (1517-
    1564 endpoints — Luther's 95 Theses through Calvin's death);
    χ.2 covers the broader post-Reformation English Nonconformist /
    Puritan / Evangelical tradition (Henry, Spurgeon, Edwards, Hodge,
    all post-1700). Together with `comm-patristic` (γ.3) and
    `comm-catholic` (χ.4) they fan out the historical Western
    Christian commentary spectrum.

    Calvin wrote commentaries on most of the OT (Genesis through
    Joshua, Psalms, Isaiah, Jeremiah-Lamentations, Daniel, the
    Twelve Minor Prophets) and on every NT book EXCEPT 2-3 John,
    Jude, and Revelation. The χ.3 seed pulls 12 entries covering
    Calvin's distinctively Reformed pins (sola fide, sola gratia,
    accommodation, covenant theology, providence).

    See `content/sources/reformation_commentaries.json` for the live
    dataset; χ.3 ships a ~12-entry Calvin-only seed, and future
    χ.3.x will expand from the Calvin Translation Society Edinburgh
    1843-1855 edition (CCEL hosts the full PD text).
    """

    book: str
    chapter: int
    verse: int
    commentator: str
    work: str
    year: int
    summary: str
    attribution: str


class ReformationCommentaries:
    """Lazy loader for the Reformation commentary corpus. Cached on
    first read. Raises ``SourceMissingError`` if the JSON cache file
    is absent.

    Two access patterns mirror χ.2 ProtestantCommentaries:
      * ``for_verse(book, chapter, verse)`` — every entry attached to
        the verse (used by the detector).
      * ``by_commentator(name)`` — every entry by a given Reformer
        (e.g. ``"John Calvin"``), for audit / coverage UIs.
    """

    PATH = _SOURCES / "reformation_commentaries.json"

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError(
                f"Reformation commentaries cache not present at {self.PATH}. "
                "The seed corpus shipped with χ.3 (2026-05-12) — restore from git."
            )
        with self.PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        self._by_verse: dict[tuple[str, int, int], list[ReformationCommentary]] = {}
        self._by_commentator: dict[str, list[ReformationCommentary]] = {}
        for entry in data.get("entries", []):
            try:
                rc = ReformationCommentary(
                    book=str(entry["book"]),
                    chapter=int(entry["chapter"]),
                    verse=int(entry["verse"]),
                    commentator=str(entry["commentator"]),
                    work=str(entry.get("work", "")),
                    year=int(entry.get("year", 0)),
                    summary=str(entry["summary"]),
                    attribution=str(entry["attribution"]),
                )
            except (KeyError, ValueError, TypeError):
                continue
            key = (_normalize_book_code(rc.book), rc.chapter, rc.verse)
            self._by_verse.setdefault(key, []).append(rc)
            self._by_commentator.setdefault(rc.commentator, []).append(rc)

    def __len__(self) -> int:
        return sum(len(v) for v in self._by_verse.values())

    def for_verse(self, book: str, chapter: int, verse: int) -> list[ReformationCommentary]:
        """Return every entry attached to a specific verse, in insertion
        order. Empty list when nothing matches."""
        return list(self._by_verse.get((_normalize_book_code(book), int(chapter), int(verse)), ()))

    def by_commentator(self, name: str) -> list[ReformationCommentary]:
        """Return every entry by a given Reformer (case-sensitive)."""
        return list(self._by_commentator.get(name, ()))


# ----------------------------------------------------------------------
# Rabbinic commentary corpus (χ.5 — 2026-05-12)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class RabbinicCommentary:
    """One verse-keyed entry in the rabbinic-tradition commentary corpus.

    Shape parallels `ProtestantCommentary` / `ReformationCommentary` —
    field name `commentator` (not `father`) since rabbinic-tradition
    exegetes (Rashi, Maimonides, Ibn Ezra, Ramban, Sforno, etc.) are
    not Christian Fathers. The semantic distinction from the Christian
    comm-* siblings is *tradition*: these are voices in the Jewish
    medieval / classical exegetical chain — what the kinds.yaml
    description calls 'Talmud, Midrash Rabbah, Rashi, Maimonides,
    Targumim'.

    Rashi (Rabbi Shlomo ben Yitzhak, 1040-1105) is THE foundational
    Jewish commentator — the indispensable companion to every page of
    the Tanakh and Talmud in subsequent Jewish learning. χ.5 ships a
    Rashi-only seed; future χ.5.x adds Maimonides / Ibn Ezra /
    Ramban / Targum entries.

    See `content/sources/rabbinic_commentaries.json` for the live
    dataset; χ.5 ships a ~12-entry Pentateuch-heavy seed covering
    Rashi's signature pins (Bereshit, Akedah, Shema, etc.) + key
    Jewish-distinctive readings of contested verses (Isa 53, Ps 22).
    """

    book: str
    chapter: int
    verse: int
    commentator: str
    work: str
    year: int
    summary: str
    attribution: str


class RabbinicCommentaries:
    """Lazy loader for the rabbinic commentary corpus. Cached on first
    read. Raises ``SourceMissingError`` if the JSON cache file is absent.

    Two access patterns mirror χ.2 / χ.3:
      * ``for_verse(book, chapter, verse)`` — every entry attached to
        the verse (used by the detector).
      * ``by_commentator(name)`` — every entry by a given exegete
        (e.g. ``"Rashi"``), for audit / coverage UIs.
    """

    PATH = _SOURCES / "rabbinic_commentaries.json"

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError(
                f"Rabbinic commentaries cache not present at {self.PATH}. "
                "The seed corpus shipped with χ.5 (2026-05-12) — restore from git."
            )
        with self.PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        self._by_verse: dict[tuple[str, int, int], list[RabbinicCommentary]] = {}
        self._by_commentator: dict[str, list[RabbinicCommentary]] = {}
        for entry in data.get("entries", []):
            try:
                rb = RabbinicCommentary(
                    book=str(entry["book"]),
                    chapter=int(entry["chapter"]),
                    verse=int(entry["verse"]),
                    commentator=str(entry["commentator"]),
                    work=str(entry.get("work", "")),
                    year=int(entry.get("year", 0)),
                    summary=str(entry["summary"]),
                    attribution=str(entry["attribution"]),
                )
            except (KeyError, ValueError, TypeError):
                continue
            key = (_normalize_book_code(rb.book), rb.chapter, rb.verse)
            self._by_verse.setdefault(key, []).append(rb)
            self._by_commentator.setdefault(rb.commentator, []).append(rb)

    def __len__(self) -> int:
        return sum(len(v) for v in self._by_verse.values())

    def for_verse(self, book: str, chapter: int, verse: int) -> list[RabbinicCommentary]:
        """Return every entry attached to a specific verse, in insertion
        order. Empty list when nothing matches."""
        return list(self._by_verse.get((_normalize_book_code(book), int(chapter), int(verse)), ()))

    def by_commentator(self, name: str) -> list[RabbinicCommentary]:
        """Return every entry by a given exegete (case-sensitive)."""
        return list(self._by_commentator.get(name, ()))


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
def patristic_commentaries() -> PatristicCommentaries:
    """Return the singleton PatristicCommentaries instance (γ.3 — 2026-05-11)."""
    return PatristicCommentaries()


@lru_cache(maxsize=1)
def ethiopian_commentaries() -> EthiopianCommentaries:
    """Return the singleton EthiopianCommentaries instance (γ.4 — 2026-05-11)."""
    return EthiopianCommentaries()


@lru_cache(maxsize=1)
def protestant_commentaries() -> ProtestantCommentaries:
    """Return the singleton ProtestantCommentaries instance (χ.2 — 2026-05-12)."""
    return ProtestantCommentaries()


@lru_cache(maxsize=1)
def catholic_commentaries() -> CatholicCommentaries:
    """Return the singleton CatholicCommentaries instance (χ.4 — 2026-05-12)."""
    return CatholicCommentaries()


@lru_cache(maxsize=1)
def reformation_commentaries() -> ReformationCommentaries:
    """Return the singleton ReformationCommentaries instance (χ.3 — 2026-05-12)."""
    return ReformationCommentaries()


@lru_cache(maxsize=1)
def rabbinic_commentaries() -> RabbinicCommentaries:
    """Return the singleton RabbinicCommentaries instance (χ.5 — 2026-05-12)."""
    return RabbinicCommentaries()


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
    "joel": "jol",
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
    "phil": "php",
    "philippians": "php",
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
    "jas": "jas",
    "james": "jas",
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


def _with_cache(inner: Callable, cache) -> Callable:
    """Wrap a ``completion_fn`` so identical (model, system, user) inputs are
    served from *cache* instead of re-calling the API.

    Opt-in: only applied when an at-scale driver constructs a client with
    ``cache=...``. The cached unit is the model's JSON response — the
    expensive part — keyed by a content hash, so a re-run pays only for
    verses whose text (or the model/prompt) changed. The default
    construction path is byte-identical to before (no cache → no wrap).
    """
    from . import work_cache as _wc

    def wrapped(system_prompt, user_message, *, model):
        key = _wc.key_for(model, system_prompt, user_message)
        hit = cache.get(key)
        if hit is not None:
            return json.loads(hit)
        result = inner(system_prompt, user_message, model=model)
        cache.put(key, json.dumps(result, ensure_ascii=False))
        return result

    return wrapped


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
        completion_fn: Callable | None = None,
        cache=None,
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
        self._valid_book_codes: set[str] | None = None

        # Telemetry from the most recent _default_completion_fn call.
        # Stub completion_fns leave this as None; the real SDK path
        # populates it so the at-scale driver can verify cache hits
        # before paying for a full run. Shape:
        #   {"input_tokens": int, "output_tokens": int,
        #    "cache_creation_input_tokens": int,
        #    "cache_read_input_tokens": int, "request_id": str | None}
        self.last_usage: dict | None = None

        # Opt-in response cache (at-scale --cache). Wrap last so it decorates
        # whichever completion_fn was selected above.
        if cache is not None:
            self._completion_fn = _with_cache(self._completion_fn, cache)

    @property
    def attribution(self) -> str:
        return f"Claude AI ({self.model}, Anthropic, 2026); reviewer-curated."

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
                # `dict.get()` may return None; the surrounding
                # try/except catches `int(None)` as TypeError. Mypy
                # treats `p.get(...)` as `Any` since `p` is untyped,
                # so no ignore is needed at the callsite.
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
            out.append(
                {
                    "target_book": target_book,
                    "target_chapter": target_chapter,
                    "target_verse": target_verse,
                    "kind_subclass": kind_subclass,
                    "reasoning": reasoning.strip(),
                    "confidence": confidence,
                }
            )
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
                usage,
                "cache_creation_input_tokens",
                0,
            ),
            "cache_read_input_tokens": getattr(
                usage,
                "cache_read_input_tokens",
                0,
            ),
            "request_id": getattr(response, "_request_id", None),
        }
        # output_config.format guarantees the first content block is
        # text containing valid JSON matching the schema.
        text = next(
            (block.text for block in response.content if block.type == "text"),
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
                    "target_book",
                    "target_chapter",
                    "target_verse",
                    "kind_subclass",
                    "reasoning",
                    "confidence",
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


# ----------------------------------------------------------------------
# AI-augmented note generator — Phase χ-AI-notes (2026-05-10)
#
# Sibling of AnthropicXrefClient. Same SDK plumbing, same caching
# discipline, same defensive degradation contract. Different prompt
# (proposes new note prose for a verse, not links between verses) and
# different output schema.
#
# See dev/SCOPE_2026-05-09-addendum-ai-notes.md for the full spec.
# ----------------------------------------------------------------------


# Use the alias so capability updates land for free; pin to a dated
# snapshot only when reproducibility outweighs Anthropic's quality
# bumps. χ-AI-xrefs uses Haiku 4.5; χ-AI-notes mirrors that choice
# for cost parity (the cost model in the SCOPE addendum projects
# ~$0.002/verse → $62 full-corpus pass at this model tier).
DEFAULT_AI_NOTE_MODEL = "claude-haiku-4-5"


# 1-hour TTL on the system prompt cache. Same trade as χ-AI-xrefs:
# 2× write premium amortizes after a few thousand reads, and a
# multi-thousand-verse run takes long enough that a 5-minute TTL
# would invalidate mid-pass.
AI_NOTE_CACHE_TTL = "1h"


# CRITICAL: Haiku 4.5's minimum cacheable prefix is 4096 tokens. A
# system prompt under that threshold gets `cache_creation_input_tokens
# = 0` with no error and the at-scale driver's cost projection is
# wrong by 5-10×. The padded prompt below clears the threshold AND
# (more importantly) gives the generator richer guidance — better
# first drafts, not just a bigger prompt.
#
# Sibling test (TestAnthropicNoteClient.test_system_prompt_meets_haiku_4_5_cache_minimum)
# pins this contract — if you shorten the prompt and it dips under
# 4096 estimated tokens, the test fails before the next paid run
# discovers it the expensive way.
AI_NOTE_SYSTEM_PROMPT = """You are a biblical commentary note drafter.

# YOUR ROLE

Given one Bible verse (book, chapter, verse, KJV text) and a small
amount of context (genre, neighboring verses if useful, the
edition's tradition tag if set), draft a single first-draft note
suitable for inclusion in a study Bible's editorial apparatus. A
human editor will review every draft you emit, edit freely, and
either approve or discard. Your job is to make the editor's job
faster, not to ship final copy.

You are conservative by default. False starts and weak drafts cost
the reviewer time; an empty answer (a brief flag that this verse
does not warrant a note) is a valid, useful response when the verse
is genealogical filler, narrative connective tissue, or formulaic
opening with no live theological or interpretive question.

# WHAT KIND OF NOTE TO WRITE

Three note classes, distinguished by what they explain:

## 1. Explanatory — historical, geographic, philological background

An explanatory note unpacks something a modern reader would miss
without specialist knowledge: a place name's geography, a coin's
purchasing power, a Levitical ritual's mechanics, an idiom's
literal sense, a manuscript variant's significance, an OT
intertext the NT writer assumes but does not quote.

Worked examples:

  - **Mark 5:1, "the country of the Gadarenes."** Note: "Across the
    Sea of Galilee in the Decapolis — Gentile territory, signaled
    by the herd of swine. Variant readings 'Gerasenes' (older
    manuscripts) and 'Gergesenes' (Origen) reflect uncertainty
    about which Decapolis town; the geographic point is that Jesus
    crosses into pagan country."
  - **Acts 16:14, "a seller of purple."** Note: "Lydia trades in
    luxury textiles dyed with murex purple — a high-margin
    commodity associated with imperial and aristocratic clientele.
    Her presence at the riverside prayer meeting and her
    subsequent hospitality (16:15) suggest a woman of substantial
    means heading a household of her own."
  - **Genesis 15:6, 'and he counted it to him for righteousness.'**
    Note: "The Hebrew verb hashav ('reckon, impute') is forensic
    rather than transformative — Abraham's faith is treated AS
    righteousness, not made into it. Paul's use of this verse in
    Rom 4 turns on exactly this nuance."

Explanatory notes are the safest class for AI drafts. They draw on
well-attested factual material — geography, philology, manuscript
history — rather than interpretive judgment. The reviewer's job is
mostly fact-checking and trimming.

## 2. Study — verse-anchored devotional + canonical bridge

A study note treats the verse as a lens onto a broader theological
or pastoral concern: what this verse is asking the reader to do,
believe, or notice; how it connects to the larger argument of the
book; what the canonical resonance is.

Worked examples:

  - **Romans 8:28, 'all things work together for good.'** Note:
    "Paul does not promise that all events ARE good — he says that
    God works in all things FOR good toward those who love him.
    The grammar is causal, not optimistic; 8:28 belongs with the
    chain that runs through 8:35-39, where 'all things' is glossed
    as tribulation, distress, persecution, famine, peril, sword."
  - **Psalm 23:4, 'Yea, though I walk through the valley of the
    shadow of death.'** Note: "Hebrew tsalmaveth means 'deep
    darkness' more than 'death's shadow' — the KJV's translation
    shapes the verse's pastoral use in funerary settings. The
    psalm's flow shifts here from third-person ('he leadeth me')
    to second-person ('thou art with me') — at the lowest point,
    the speaker addresses God directly."
  - **Matthew 5:3, 'blessed are the poor in spirit.'** Note: "Luke
    6:20 has 'blessed are ye poor' — the canonical Beatitudes
    resist a simple choice between material and spiritual poverty.
    'Poor in spirit' (ptochoi to pneumati) names those who know
    their need before God, whatever their material situation;
    Luke's 'poor' names the materially destitute as Jesus's named
    audience."

Study notes are interpretive and require more reviewer judgment
than explanatory notes. Stay close to the text's own concerns;
avoid reading later theological frameworks back into earlier
material; flag where scholarly consensus is contested rather than
choosing a side.

## 3. Translation — idiom, cultural-context unpacking

A translation note explains what the underlying Hebrew or Greek is
doing that the English translation flattens or that a careful
reader should know about. This includes idioms (literal vs
intended sense), cultural conventions (forms of address, rhetorical
patterns), and lexical fields the translator had to choose
between.

Worked examples:

  - **Genesis 4:1, 'I have gotten a man from the LORD.'** Note:
    "Hebrew qaniti ish et-YHWH — Eve's wordplay on Cain's name
    (qayin / qaniti, 'I have gotten / I have produced'). The 'et'
    particle is ambiguous: 'with the help of the LORD' (most
    versions) or 'I have produced a man, [namely] the LORD'
    (older Jewish reading hinting at messianic hope). The
    grammatical ambiguity is real; modern translations choose
    'with the help of' for clarity."
  - **Mark 10:18, 'Why callest thou me good?'** Note: "Greek
    agathos. Jesus is not denying his own goodness; the phrase
    'good teacher' (didaskale agathe) was an unusual rabbinic
    address that Jesus redirects toward God to expose what 'good'
    really means. The retort is rhetorical — Jesus's response
    invites the rich young ruler to think about what he is
    actually claiming with the address."
  - **John 3:3, 'born again.'** Note: "Greek anothen — 'from above'
    or 'again,' deliberately ambiguous. Jesus uses it in the 'from
    above' sense (3:31, 19:11); Nicodemus hears it in the 'again'
    sense and asks the literal-minded follow-up. The pun is the
    point of the dialogue."

Translation notes are the most technically demanding. The reviewer
will check the lexical claims; do not invent etymologies, do not
exaggerate ambiguity that does not exist, and do not import
specialized vocabulary the average reader cannot follow.

# CONFIDENCE CALIBRATION

The reviewer trusts your calibration. Sandbagging or inflating
both reduce signal.

  - **0.85-1.00:** Well-attested factual or philological material
    that any standard commentary or lexicon will confirm. Place
    names, dates, lexical glosses, manuscript variants. Reviewer
    will fact-check briefly and approve quickly.
  - **0.65-0.84:** Interpretive judgment that has scholarly
    consensus. The note states a reading the major commentaries
    converge on, in the project's voice rather than quoting any
    one source. Reviewer will check the reading is fairly stated.
  - **0.45-0.64:** Defensible interpretation where reasonable
    readers differ. The note acknowledges the contested character
    rather than pretending consensus. Reviewer will weigh whether
    to ship the note as is, hedge it further, or replace.
  - **0.25-0.44:** Speculative or genuinely uncertain. The note
    surfaces a possibility worth flagging but not asserting.
    Reviewer should look closely; many will not survive review.
  - **0.00-0.24:** Drop and emit no note. Better to leave the
    verse without an AI draft than to waste reviewer time on a
    weak suggestion.

# WHAT TO AVOID

The corpus's quality is the platform's reputation. The following
patterns will be rejected at review and should not appear in your
drafts:

1. **Fabricated citations.** Do not invent author names, page
   numbers, journal references, or quoted passages. If you do not
   have the citation, write the substance without the citation.
   The reviewer will add references where appropriate.

2. **Theological advocacy.** This is an editorial apparatus, not
   a sermon. Explain what the text is doing, what scholars
   discuss, what the historical context is — do not exhort the
   reader, do not preach, do not pronounce on contested doctrinal
   matters as if they were settled.

3. **Anachronistic categories.** Do not project Reformation
   covenant theology, dispensational schemas, modern psychological
   categories, or contemporary political frames onto OT or NT
   texts that did not originally bear them.

4. **Speculative numerology, gematria, allegorical fancies.**
   These waste reviewer time and damage the corpus's reliability.
   "The number 7 in this verse symbolizes..." — no.

5. **Generic devotional padding.** "This verse reminds us of God's
   faithfulness" applies to half the Bible. If your draft would
   work for any verse with the same general topic, it is too
   generic — either say something specific to THIS verse or emit
   no note.

6. **Long quotations of the verse itself.** The verse is already
   on the page. Do not paste it back; reference it briefly and
   move to your point.

7. **Citation of secondary works in the body.** Inline references
   like "(Wright, p. 142)" do not match the project's house style.
   Attribution is set on the note record; the body should read as
   project-voice prose. The reviewer will phrase any in-text
   credit if needed.

8. **Modern application analogies as the substance of the note.**
   "This is like our modern X" is sermon material. The note may
   end with one sentence of application if it follows naturally
   from the exegesis, but the substance should be exegetical.

9. **Length inflation.** The label is 1-3 words; the body is 1-3
   sentences. A long body is almost always worse than a tight
   one. Cut everything that does not earn its place.

10. **Tradition partisanship.** When the edition has a tradition
    tag (e.g. eastern-orthodox, lutheran-confessional, ethiopian),
    write the note in that tradition's idiom and concerns; do not
    polemicize against other traditions or import contested
    distinctives. Stay descriptive.

# WORKED EXAMPLE WALKTHROUGH

Verse: Romans 12:1, "I beseech you therefore, brethren, by the
mercies of God, that ye present your bodies a living sacrifice,
holy, acceptable unto God, which is your reasonable service."

Bad draft (do not emit):

  Label: "Living sacrifice."
  Body: "Romans 12:1 reminds us that as believers, our entire
  lives should be offered as a sacrifice to God. This is a
  beautiful picture of total devotion. Are we presenting our
  bodies as living sacrifices today? May we be challenged to
  greater commitment as we meditate on this powerful verse."
  Reasoning: Generic devotional padding; no exegetical content;
  exhortation tone; padding phrase 'as we meditate on this
  powerful verse.'

Better draft (acceptable for first pass):

  Label: "Reasonable service."
  Body: "Greek logikēn latreian — both adjective and noun are
  unusual. Latreia is cultic service (the OT sacrificial system
  in LXX usage); logikē is 'rational' or 'pertaining to logos.'
  Paul reframes Levitical worship around the rational/spiritual
  offering of the whole self, completing the ethical pivot from
  Rom 1-11 (what God has done) to Rom 12-15 (what response
  follows). Translations vary: 'reasonable service' (KJV),
  'spiritual worship' (RSV), 'true and proper worship' (NIV)."
  Reasoning: Exegetical substance, lexical content, structural
  observation about the letter's pivot, fair handling of
  translation choices without polemic. Confidence ~0.78.

# OUTPUT FORMAT

The API enforces a JSON schema; you must return STRICT JSON only,
with no prose, no markdown fences, no preamble. Shape:

{
  "verse_anchor": {
    "book": "<3-letter canonical code, lowercase>",
    "chapter": <int>,
    "verse": <int>
  },
  "note": {
    "kind_class": "explanatory" | "study" | "translation",
    "label": "<1-3 words, capitalized — appears as the bold lead-in on the rendered note>",
    "body_html": "<the note text, plain prose with at most these tags: <em>, <strong>, <a href=\"#vnote-<book>-<ch>-<vs>\"> — 1-3 sentences>",
    "confidence": <float, 0.0..1.0>,
    "sources_consulted": ["<short-form reference>", ...],
    "reviewer_flags": ["<concise flag>", ...]
  }
}

If the verse does not warrant an AI draft (genealogy, transitional
narrative, formulaic opening, or the verse simply does not have
strong enough material to produce a useful first draft at >=0.40
confidence), return:

  {"verse_anchor": {"book": "<...>", "chapter": <...>, "verse": <...>},
   "note": null}

A `null` note is a valid, useful answer. The reviewer's queue is
better with 200 strong drafts than 1000 thin ones.

# CANONICAL BOOK CODES (use these EXACTLY — never invent others)

Old Testament (Protestant + Hebrew Bible order):
  gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh
  est job psa pro ecc sng isa jer lam eze dan hos joe amo oba jon
  mic nah hab zep hag zec mal

New Testament:
  mat mrk luk jhn act rom 1co 2co gal eph phi col 1th 2th 1ti 2ti
  tit phm heb jam 1pe 2pe 1jn 2jn 3jn jud rev

Deuterocanon (Catholic / Orthodox / Tewahedo — only when the verse
itself is in the deuterocanon):
  tob jdt wis sir bar lje paz sus bel 1es 2es man 1ma 2ma aes
  mq1 mq2 mq3 jub 1en 2en 4ba 1cl

If you are tempted to use a code not on these lists — for example,
"songofsongs" or "matthew" or "1maccabees" — STOP and use the
3-letter form. The platform's promote step rejects unknown codes
and your draft will be silently dropped.

# LABEL FIELD GUIDANCE

The label is a 1-3 word phrase that renders as the bold lead-in to
the note body. It should name what the note is about — the term
being explained, the place being identified, the idiom being
unpacked, the theological motif being bridged.

  Good labels: "Living sacrifice." / "Decapolis." / "Anothen." /
  "Tsalmaveth." / "Reasonable service." / "Imputed righteousness."

  Bad labels: "Note." / "Commentary." / "Romans 12:1." (generic
  or redundant with the verse anchor). "This important verse..."
  (sentence fragment, not a label).

End the label with a period. The renderer pairs the label with the
body as: <strong>{label}</strong> {body}.

# BODY HTML GUIDANCE

The body is 1-3 sentences of plain prose. Allowed tags:
  - <em> for foreign-language terms (Greek, Hebrew, Latin), OT
    book titles, work titles, and emphasis
  - <strong> for terms being defined or genuinely emphasized
  - <a href="#vnote-<book>-<chapter>-<verse>"> for cross-canonical
    references that should link to another verse note

Do NOT include:
  - <p>, <div>, <ul>, <ol>, <li>, <h1>-<h6>, <br>, <hr>, <img>,
    <script>, <style>, or any structural / multimedia / executable
    tags. The renderer wraps the body itself; you supply prose.
  - Inline citations like "(Wright, p. 142)" or "according to
    Brown 1993" — attribution lives on the note record, not in
    the body. The reviewer adds in-text credit if needed.
  - Asterisks, bullet points, numbered lists, or pseudo-markdown.
    The body is plain prose.

# REASONING NOTES — the reviewer_flags field

The `reviewer_flags` array is a short list of concise English
strings telling the reviewer what specifically to check or
consider. Common flags:

  - "Verify the lexical claim against BDAG / HALOT."
  - "The Greek/Hebrew transliteration is approximate; verify
    spelling and macrons."
  - "Contested reading; major commentaries split between A and B.
    The note picks A — switch to B if the edition's tradition
    favors it."
  - "The cross-reference link assumes vnote anchors exist for the
    target verse; verify that target verse has a note."
  - "Generic study-Bible language — replace with project voice."
  - "Cuts close to theological advocacy at the end; trim if it
    reads as exhortation."

Aim for 0-3 flags. An empty array is correct when the draft is
unflagged. The flags are part of the reviewer's queue — make them
specific and actionable, not general disclaimers.

# SOURCES_CONSULTED FIELD GUIDANCE

A short list of short-form references identifying the kinds of
sources the draft draws on, when relevant. Examples:

  - ["BDAG", "Cranfield Romans", "NA28 apparatus"]
  - ["Wenham Genesis", "HALOT", "Westermann commentary tradition"]
  - ["TLG search on logikē latreian"]
  - ["Standard study-Bible apparatus, no specialist source"]

This field is for the reviewer's verification step — it tells them
where to look to confirm the substance. Do not invent sources you
did not actually draw on. An empty array is acceptable when the
draft is general enough to need no specific source.

# GENRE-SPECIFIC GUIDANCE

The right kind of note depends on the genre of the verse. Adjust
expectations and confidence accordingly.

## Narrative (Genesis-Esther, Gospels, Acts)

Narrative verses often warrant explanatory notes (geography,
political context, character background) and translation notes
(Hebrew or Greek narrative formulas). Study notes are appropriate
when the verse is doing significant theological work within the
larger story.

Narrative connective tissue (genealogies, transitional verses,
purely chronological notes) usually warrants no note. Empty answer
is the right answer for "And Jared lived an hundred sixty and two
years, and he begat Enoch."

## Wisdom (Job, Psalms, Proverbs, Ecclesiastes, Song of Songs)

Wisdom literature works by aphorism and parallelism. Look for:

  - Translation notes on Hebrew poetry (parallelism patterns,
    untranslatable wordplay).
  - Study notes on the place of the verse in its larger psalm or
    proverbial unit.
  - Cultural-context notes (ANE wisdom parallels, where useful).

Be careful: Proverbs often makes general observations that
incidentally resemble many other verses. Draft a note only when
something specific to THIS verse warrants explanation.

## Prophecy (Isaiah-Malachi, Revelation)

Prophecy is rich in idiomatic formulas, recurring theological
themes, and direct OT/NT material. Look for:

  - Explanatory notes on the historical setting (which king, what
    crisis).
  - Translation notes on prophetic formulas ('thus saith the
    LORD,' 'behold, the days come').
  - Study notes on canonical use (e.g. NT use of an OT prophecy).

Apocalyptic imagery in particular invites speculative pattern-
matching; resist it. Stay descriptive.

## Epistles (Romans-Jude)

Epistles argue rather than narrate. Look for:

  - Translation notes on key Greek terms (logikē, hilastērion,
    dikaiosynē, pistis).
  - Study notes on the verse's place in the letter's argument
    (this verse pivots from indicative to imperative; this verse
    completes a chain begun in 8:1).
  - Explanatory notes on first-century context (Roman household,
    synagogue practice, patron-client relations).

## Apocalyptic (Daniel, Revelation, parts of Ezekiel and Zechariah)

Apocalyptic shares a dense imagic vocabulary across centuries.
Many of Revelation's images quote OT apocalyptic without explicit
citation. Look for:

  - Explanatory notes on imagery the modern reader will not
    recognize (Daniel's beasts, the bowls/seals/trumpets
    structure).
  - Cross-references to the OT source for an image (with a brief
    note on what the OT context contributed).
  - Study notes on the letter's pastoral situation (which
    Anatolian church, which crisis).

Confidence on apocalyptic interpretation should be conservative.
Many readings are contested.

# ADDITIONAL ANTI-PATTERNS WITH WORKED EXAMPLES

## Anti-pattern: starting with a question

  - Bad: "Have you ever wondered what 'reasonable service' really
    means? Paul uses an unusual Greek phrase here..."
  - Better: "Greek logikēn latreian — both adjective and noun are
    unusual..."

## Anti-pattern: applause for the verse

  - Bad: "This beautiful verse reminds us of God's wonderful
    faithfulness."
  - Better: simply make the substantive observation. The verse
    does not need your endorsement.

## Anti-pattern: parading specialist vocabulary

  - Bad: "The sitz im leben of this pericope problematizes a naive
    redaction-critical approach to the source-critical seam at
    v. 7."
  - Better: name the issue in plain English. If specialist terms
    are needed, gloss them inline. Notes are for the educated lay
    reader, not the seminar room.

## Anti-pattern: fabricating a quoted source

  - Bad: "As Brueggemann observes in his Theology of the Old
    Testament (1997, p. 412), the suffering servant motif..."
  - Better: state the substance without the citation. If the
    observation is general scholarly consensus, say so. If it
    needs a citation, leave it for the reviewer.

## Anti-pattern: hedging into uselessness

  - Bad: "Some scholars suggest that this verse may possibly,
    though uncertainly, perhaps refer to..."
  - Better: state the reading you find best, calibrate confidence
    honestly, and use a single hedge ('contested,' 'one reading,'
    'likely') if needed. Empty hedges read as cowardice.

# CONFIDENCE CALIBRATION: WORKED EXAMPLES

Calibrate by walking through realistic examples:

  - **0.92** — A geographic identification of a clear place name
    with well-attested ancient sources. "Decapolis is the league
    of ten Greek cities east of the Jordan." Standard reference
    material; reviewer fact-checks briefly.
  - **0.85** — A lexical gloss on a technical term where the
    major lexica converge. "logikē in Greek philosophical and
    Stoic usage means 'rational' or 'pertaining to logos.'"
  - **0.75** — An interpretive observation with broad scholarly
    consensus. "Romans 12:1 marks the pivot from doctrinal
    exposition (Rom 1-11) to ethical exhortation (Rom 12-15)."
  - **0.62** — A reading the commentaries discuss but where there
    is real disagreement. "The 'man of sin' in 2 Thess 2 has been
    read as a specific historical figure (Nero, Caligula),
    institutional Rome, the antichrist, or the larger pattern of
    eschatological lawlessness; the immediate context favors..."
  - **0.45** — A defensible reading among several. Worth flagging
    for the reviewer to weigh.
  - **0.30** — Speculative; mention only with explicit hedge and
    only when the verse is otherwise hard to draft for.
  - **0.20** — Drop the draft. Reviewer time is better spent on
    stronger material.

# FINAL CHECK BEFORE EMITTING

Before returning, ask yourself five questions about the draft you
are about to emit:

  1. Is the substance specific to THIS verse, or could the same
     prose apply to many verses? (If generic, drop or rewrite.)
  2. Have I named what is being explained — the place, the term,
     the idiom, the structural observation, the canonical
     resonance? (If not, the note has no thesis.)
  3. Is every claim either obvious from the text, well-attested in
     standard reference works, or fairly stated as one
     interpretation among several? (If shaky, lower confidence or
     drop.)
  4. Have I avoided fabricated citations, theological advocacy,
     anachronistic categories, and devotional padding? (If any
     present, rewrite.)
  5. Is the body 1-3 sentences? Is the label 1-3 words ending in
     a period? (If oversize, trim.)

A short list of high-quality drafts is far more valuable than a
long list padded with weak ones. The corpus aims for reviewer-
curated quality, not coverage. When the verse genuinely lacks
strong material — for genealogies, transitional sentences, or
formulaic openings — the right answer is `{"note": null}`.
"""


# JSON schema for the structured-output contract. Forces the model
# to emit a `verse_anchor` + (`note` | null) shape — no
# regex-strip-fences hack, no JSONDecodeError on stray prose.
# additionalProperties=False prevents the model from sneaking in
# unrecognized fields downstream code would silently ignore.
AI_NOTE_OUTPUT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "verse_anchor": {
            "type": "object",
            "properties": {
                "book": {"type": "string"},
                "chapter": {"type": "integer"},
                "verse": {"type": "integer"},
            },
            "required": ["book", "chapter", "verse"],
            "additionalProperties": False,
        },
        "note": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "properties": {
                        "kind_class": {
                            "type": "string",
                            "enum": ["explanatory", "study", "translation"],
                        },
                        "label": {"type": "string"},
                        "body_html": {"type": "string"},
                        "confidence": {"type": "number"},
                        "sources_consulted": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "reviewer_flags": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "kind_class",
                        "label",
                        "body_html",
                        "confidence",
                        "sources_consulted",
                        "reviewer_flags",
                    ],
                    "additionalProperties": False,
                },
            ],
        },
    },
    "required": ["verse_anchor", "note"],
    "additionalProperties": False,
}


class AnthropicNoteClient:
    """LLM-backed first-draft note generator. Phase χ-AI-notes (2026-05-10).

    Sibling of :class:`AnthropicXrefClient`. Same construction
    contract: raises :class:`SourceMissingError` when neither a
    real Anthropic SDK + API key nor an injected ``completion_fn``
    is available. ``prospect.py``'s resilient detector
    instantiation catches that and skips the detector silently —
    same graceful-degrade contract as :class:`NaveTopical` when
    its JSON cache is absent.

    The injected ``completion_fn(system_prompt, user_message, *,
    model)`` returns the parsed completion as a Python dict
    matching the documented shape. Tests pass a stub fn so no
    real network calls are made.

    The default ``completion_fn`` uses the ``anthropic`` SDK with
    prompt caching on the system prompt — repeated per-verse calls
    only pay for the per-verse user message after the first call,
    cutting cost roughly 10×. Distinct from
    :class:`AnthropicXrefClient` only in prompt + schema; the
    SDK plumbing, cache TTL, telemetry shape, and exception-
    handling contract are identical.
    """

    def __init__(
        self,
        *,
        model: str = DEFAULT_AI_NOTE_MODEL,
        completion_fn: Callable | None = None,
        cache=None,
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
        self._valid_book_codes: set[str] | None = None

        # Telemetry from the most recent _default_completion_fn call.
        # Stub completion_fns leave this as None; the real SDK path
        # populates it so the at-scale driver can verify cache hits
        # before paying for a full run. Same shape as
        # AnthropicXrefClient.last_usage.
        self.last_usage: dict | None = None

        # Opt-in response cache (at-scale --cache). Wrap last so it decorates
        # whichever completion_fn was selected above.
        if cache is not None:
            self._completion_fn = _with_cache(self._completion_fn, cache)

    @property
    def attribution(self) -> str:
        return f"Claude AI ({self.model}, Anthropic, 2026); reviewer-curated. AI-generated first draft, edited and approved by a human reviewer before publication."

    def _valid_codes(self) -> set[str]:
        if self._valid_book_codes is None:
            from . import config as _cfg

            self._valid_book_codes = set(_cfg.books_by_code().keys())
        return self._valid_book_codes

    def draft_note(
        self,
        book: str,
        chapter: int,
        verse: int,
        verse_text: str,
        *,
        tradition: str | None = None,
    ) -> dict | None:
        """Ask the model for a first-draft note for the given verse.

        Returns a dict with fields ``kind_class``, ``label``,
        ``body_html``, ``confidence``, ``sources_consulted``,
        ``reviewer_flags`` — OR ``None`` when the model judges the
        verse not to warrant a draft (genealogy, transitional
        narrative, formulaic opening, etc.).

        Defensive against malformed model output: returns ``None``
        on schema violation, parse failure, or SDK error rather
        than raising. Programming errors (TypeError,
        AttributeError) propagate so they surface in tests.

        ``tradition`` is an optional edition-level tradition tag
        (e.g. ``"eastern-orthodox"``) that gets passed into the
        user message so the model can write in that tradition's
        idiom. Defaults to None (general/non-tradition-tagged).
        """
        anchor_line = f"  Book:    {book}\n  Chapter: {chapter}\n  Verse:   {verse}\n  Text:    {verse_text}\n"
        if tradition:
            user_message = f"Draft a first-draft note for the verse below. The edition's tradition tag is '{tradition}' — write in that tradition's idiom and concerns where appropriate.\n\n{anchor_line}"
        else:
            user_message = f"Draft a first-draft note for the verse below.\n\n{anchor_line}"

        # Catch only failures we can defensively degrade through —
        # SDK errors (with retry exhausted), JSON-shape failures the
        # schema didn't catch, value coercion errors. Programming
        # errors (TypeError, AttributeError, etc.) propagate so they
        # surface in tests rather than silently producing empty
        # outputs. Identical contract to AnthropicXrefClient.
        try:
            parsed = self._completion_fn(
                AI_NOTE_SYSTEM_PROMPT,
                user_message,
                model=self.model,
            )
        except (json.JSONDecodeError, ValueError, OSError):
            return None
        except Exception as e:
            if type(e).__module__.startswith("anthropic"):
                return None
            raise

        if not isinstance(parsed, dict):
            return None

        # Verify the verse_anchor matches what we asked for. A model
        # that returns a draft for a different verse is misbehaving;
        # drop the draft rather than write it under the wrong anchor.
        anchor = parsed.get("verse_anchor")
        if not isinstance(anchor, dict):
            return None
        if anchor.get("book") != book:
            return None
        try:
            if int(anchor.get("chapter", 0)) != chapter:
                return None
            if int(anchor.get("verse", 0)) != verse:
                return None
        except (TypeError, ValueError):
            return None

        note = parsed.get("note")
        if note is None:
            return None
        if not isinstance(note, dict):
            return None

        kind_class = note.get("kind_class")
        if kind_class not in ("explanatory", "study", "translation"):
            return None

        label = note.get("label")
        if not isinstance(label, str) or not label.strip():
            return None

        body_html = note.get("body_html")
        if not isinstance(body_html, str) or not body_html.strip():
            return None

        try:
            confidence = float(note.get("confidence", 0.0))
        except (TypeError, ValueError):
            return None
        # Clamp confidence into [0, 1]
        confidence = max(0.0, min(1.0, confidence))

        sources_consulted = note.get("sources_consulted") or []
        if not isinstance(sources_consulted, list):
            sources_consulted = []
        sources_consulted = [s for s in sources_consulted if isinstance(s, str)]

        reviewer_flags = note.get("reviewer_flags") or []
        if not isinstance(reviewer_flags, list):
            reviewer_flags = []
        reviewer_flags = [s for s in reviewer_flags if isinstance(s, str)]

        return {
            "kind_class": kind_class,
            "label": label.strip(),
            "body_html": body_html.strip(),
            "confidence": confidence,
            "sources_consulted": sources_consulted,
            "reviewer_flags": reviewer_flags,
        }

    def _default_completion_fn(
        self,
        system_prompt: str,
        user_message: str,
        *,
        model: str,
    ) -> dict:
        """Real SDK call. Only reached when the constructor confirmed
        the SDK + API key are available.

        Mirrors :meth:`AnthropicXrefClient._default_completion_fn`:

        - **Prompt caching with 1h TTL** on the system prompt so
          per-verse calls only pay for the user message after the
          first call. The 4096-token-minimum-prefix invariant for
          Haiku 4.5 is satisfied by the padded system prompt above.
        - **Structured output** via ``output_config.format`` with a
          json_schema. The model is forced to return valid JSON of
          the documented shape — no regex-strip-fences hack, no
          json.JSONDecodeError on stray prose.
        - **Cached SDK client** at module level (see
          ``_anthropic_client()``).

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
                        "ttl": AI_NOTE_CACHE_TTL,
                    },
                }
            ],
            messages=[{"role": "user", "content": user_message}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": AI_NOTE_OUTPUT_SCHEMA,
                },
            },
        )
        # Capture telemetry before parsing so cache-hit info survives
        # even if the JSON parse fails downstream.
        usage = response.usage
        self.last_usage = {
            "input_tokens": getattr(usage, "input_tokens", 0),
            "output_tokens": getattr(usage, "output_tokens", 0),
            "cache_creation_input_tokens": getattr(
                usage,
                "cache_creation_input_tokens",
                0,
            ),
            "cache_read_input_tokens": getattr(
                usage,
                "cache_read_input_tokens",
                0,
            ),
            "request_id": getattr(response, "_request_id", None),
        }
        text = next(
            (block.text for block in response.content if block.type == "text"),
            "",
        )
        return json.loads(text)


@lru_cache(maxsize=1)
def anthropic_note_client() -> AnthropicNoteClient:
    """Return the singleton AnthropicNoteClient (lazy-loaded once).
    Raises ``SourceMissingError`` if the SDK/API key are unavailable."""
    return AnthropicNoteClient()

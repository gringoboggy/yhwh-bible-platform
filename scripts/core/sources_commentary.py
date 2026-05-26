"""
sources_commentary.py — verse-keyed commentary corpora extracted from the
``sources`` god-module.

The six historical commentary traditions (patristic, Ethiopian, Protestant,
Catholic, Reformation, rabbinic), each a frozen dataclass entry plus a lazy
loader indexing by (book, chapter, verse) and by author, with their singleton
accessors.

Extracted verbatim from ``sources.py`` (module split 2026-05-26).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from .sources_base import SourceMissingError, _SOURCES, _normalize_book_code


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

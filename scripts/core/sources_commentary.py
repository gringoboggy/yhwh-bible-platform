"""
sources_commentary.py — verse-keyed commentary corpora extracted from the
``sources`` god-module.

The six historical commentary traditions (patristic, Ethiopian, Protestant,
Catholic, Reformation, rabbinic), each a frozen dataclass entry plus a lazy
loader indexing by (book, chapter, verse) and by author, with their singleton
accessors.

Extracted verbatim from ``sources.py`` (module split 2026-05-26). The six
loaders — which differed only in their JSON path, their "person" field name
(``father`` vs ``commentator``), the missing-cache message, and the
``by_father``/``by_commentator`` accessor name — share one
:class:`_CommentaryCorpus` base (de-dup B1.9, 2026-05-26). The six frozen
dataclasses are kept distinct so each tradition keeps its own field name,
provenance docstring, and ``isinstance`` identity.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

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


# ----------------------------------------------------------------------
# Shared loader (de-dup B1.9 — 2026-05-26)
# ----------------------------------------------------------------------


class _CommentaryCorpus:
    """Lazy loader shared by the six verse-keyed commentary corpora.

    Cached on first read by its singleton accessor. Raises
    ``SourceMissingError`` if the JSON cache file is absent — the
    graceful-degrade contract ``prospect.py``'s detector instantiation
    relies on.

    Each subclass declares four class attributes:

      * ``ENTRY``        — the frozen dataclass for one entry.
      * ``PATH``         — the JSON cache file under ``content/sources/``.
      * ``PERSON_FIELD`` — ``"father"`` or ``"commentator"``; the one
                           field whose name differs between traditions.
      * ``_MISSING``     — a ``str.format(path=...)`` template for the
                           SourceMissingError raised when ``PATH`` is absent.

    and expose the tradition-appropriate ``by_father`` / ``by_commentator``
    delegating to :meth:`by_person`. Two access patterns are shared:

      * :meth:`for_verse` — every entry attached to one verse (the detector
        path).
      * the by-person accessor — every entry by a given author (audit /
        coverage UIs).

    Extracted from six ~90-line near-clones that differed only in the four
    attributes above.
    """

    ENTRY: type
    PATH: Path
    PERSON_FIELD: str
    _MISSING: str

    def __init__(self) -> None:
        if not self.PATH.is_file():
            raise SourceMissingError(self._MISSING.format(path=self.PATH))
        with self.PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        pf = self.PERSON_FIELD
        # Index by (book, chapter, verse) for O(1) per-verse lookup, and
        # by author name for the audit case. Insertion order is preserved
        # (the JSON keeps entries chronological per author).
        self._by_verse: dict[tuple[str, int, int], list] = {}
        self._by_person: dict[str, list] = {}
        for entry in data.get("entries", []):
            try:
                obj = self.ENTRY(
                    book=str(entry["book"]),
                    chapter=int(entry["chapter"]),
                    verse=int(entry["verse"]),
                    work=str(entry.get("work", "")),
                    year=int(entry.get("year", 0)),
                    summary=str(entry["summary"]),
                    attribution=str(entry["attribution"]),
                    **{pf: str(entry[pf])},
                )
            except (KeyError, ValueError, TypeError):
                # Malformed entry — skip silently. The schema is documented
                # in the JSON's _meta block; this is defensive against
                # hand-edit typos.
                continue
            key = (_normalize_book_code(obj.book), obj.chapter, obj.verse)
            self._by_verse.setdefault(key, []).append(obj)
            self._by_person.setdefault(getattr(obj, pf), []).append(obj)

    def __len__(self) -> int:
        return sum(len(v) for v in self._by_verse.values())

    def for_verse(self, book: str, chapter: int, verse: int) -> list:
        """Return every commentary entry attached to a specific verse, in
        insertion order. Empty list when nothing matches."""
        return list(self._by_verse.get((_normalize_book_code(book), int(chapter), int(verse)), ()))

    def by_person(self, name: str) -> list:
        """Return every entry by a given author (case-sensitive). Subclasses
        expose this under the tradition-appropriate name (``by_father`` for
        the Father corpora, ``by_commentator`` for the rest)."""
        return list(self._by_person.get(name, ()))


class PatristicCommentaries(_CommentaryCorpus):
    """Patristic commentary corpus (γ.3 — 2026-05-11)."""

    ENTRY = PatristicCommentary
    PATH = _SOURCES / "patristic_commentaries.json"
    PERSON_FIELD = "father"
    _MISSING = (
        "Patristic commentaries cache not present at {path}. "
        "The seed corpus shipped with γ.3 (2026-05-11) — restore from git."
    )

    def by_father(self, name: str) -> list[PatristicCommentary]:
        """Return every entry by a given Church Father (case-sensitive).
        Useful for coverage audits or a future per-Father console."""
        return self.by_person(name)


class EthiopianCommentaries(_CommentaryCorpus):
    """Ethiopian Tewahedo commentary corpus (γ.4 — 2026-05-11)."""

    ENTRY = EthiopianCommentary
    PATH = _SOURCES / "ethiopian_commentaries.json"
    PERSON_FIELD = "father"
    _MISSING = (
        "Ethiopian commentaries cache not present at {path}. "
        "The seed corpus shipped with γ.4 (2026-05-11) — restore from git."
    )

    def by_father(self, name: str) -> list[EthiopianCommentary]:
        """Return every entry by a given source (case-sensitive). The
        'father' field is sometimes a tradition rather than a person
        (e.g. '1 Enoch (Ethiopian tradition)') — that's deliberate; the
        audit UI groups by it identically."""
        return self.by_person(name)


class ProtestantCommentaries(_CommentaryCorpus):
    """Post-Reformation Protestant commentary corpus (χ.2 — 2026-05-12)."""

    ENTRY = ProtestantCommentary
    PATH = _SOURCES / "protestant_commentaries.json"
    PERSON_FIELD = "commentator"
    _MISSING = (
        "Protestant commentaries cache not present at {path}. "
        "The seed corpus shipped with χ.2 (2026-05-12) — restore from git."
    )

    def by_commentator(self, name: str) -> list[ProtestantCommentary]:
        """Return every entry by a given expositor (case-sensitive)."""
        return self.by_person(name)


class CatholicCommentaries(_CommentaryCorpus):
    """Catholic (Catena Aurea) commentary corpus (χ.4 — 2026-05-12)."""

    ENTRY = CatholicCommentary
    PATH = _SOURCES / "catholic_commentaries.json"
    PERSON_FIELD = "father"
    _MISSING = (
        "Catholic commentaries cache not present at {path}. "
        "The seed corpus shipped with χ.4 (2026-05-12) — restore from git."
    )

    def by_father(self, name: str) -> list[CatholicCommentary]:
        """Return every entry by a given Church Father (case-sensitive),
        as surfaced through Aquinas's Catena Aurea."""
        return self.by_person(name)


class ReformationCommentaries(_CommentaryCorpus):
    """16th c. magisterial Reformation commentary corpus (χ.3 — 2026-05-12)."""

    ENTRY = ReformationCommentary
    PATH = _SOURCES / "reformation_commentaries.json"
    PERSON_FIELD = "commentator"
    _MISSING = (
        "Reformation commentaries cache not present at {path}. "
        "The seed corpus shipped with χ.3 (2026-05-12) — restore from git."
    )

    def by_commentator(self, name: str) -> list[ReformationCommentary]:
        """Return every entry by a given Reformer (case-sensitive)."""
        return self.by_person(name)


class RabbinicCommentaries(_CommentaryCorpus):
    """Rabbinic-tradition commentary corpus (χ.5 — 2026-05-12)."""

    ENTRY = RabbinicCommentary
    PATH = _SOURCES / "rabbinic_commentaries.json"
    PERSON_FIELD = "commentator"
    _MISSING = (
        "Rabbinic commentaries cache not present at {path}. "
        "The seed corpus shipped with χ.5 (2026-05-12) — restore from git."
    )

    def by_commentator(self, name: str) -> list[RabbinicCommentary]:
        """Return every entry by a given exegete (case-sensitive)."""
        return self.by_person(name)


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

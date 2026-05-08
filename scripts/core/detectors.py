"""
detectors.py — Detectors generate candidate notes from a verse + source corpora.

Each detector:
  * declares the kind it produces (matched against kinds.yaml)
  * takes a (book, chapter, verse, verse_text) tuple
  * returns a list of Candidate instances (possibly empty)

Detectors are pure: same input → same output. They never write to disk;
``prospect.py`` collects, dedupes, and serialises their output.

Detectors registered in this module are auto-discovered by ``prospect.py``
via ``ALL_DETECTORS``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import sources


# ----------------------------------------------------------------------
# Candidate dataclass
# ----------------------------------------------------------------------


@dataclass
class Candidate:
    """A draft note proposed by a detector. Becomes a real note iff the
    user promotes it via ``promote.py``."""

    book: str  # e.g. "gen"
    chapter: int
    verse: int
    kind: str  # must be a registered kind in kinds.yaml
    anchor: str  # text in the verse to anchor on (or "")
    confidence: float  # 0.0..1.0
    source_name: str  # e.g. "Strong's H1254"
    source_attribution: str  # PD/CC notice for the YAML
    draft_title: str  # the note's title field
    draft_label: str  # the note's label field
    draft_body: str  # HTML body
    detector: str = ""  # which detector produced this (for debug)
    reviewer_notes: str = ""  # optional, for the review CLI


# ----------------------------------------------------------------------
# Hebrew word detector
# ----------------------------------------------------------------------

# Curated map of theologically-loaded biblical Hebrew terms.
# Format: english_keyword → (strongs_number, ...)
# We use a small, curated set for the MVP. Extending this map widens
# the detector's coverage without changing any code.
#
# Each English keyword is matched case-insensitively, whole-word, in the
# verse text. When a match fires, the detector produces a candidate with
# the Strong's data as the draft body.

HEBREW_KEYWORD_MAP: dict[str, str] = {
    # Genesis 1 vocabulary
    "created": "H1254",  # bara — distinctive: only God is subject in OT
    "create": "H1254",
    "earth": "H776",  # erets
    "land": "H776",
    "heavens": "H8064",  # shamayim
    "heaven": "H8064",
    "sky": "H8064",
    "spirit": "H7307",  # ruach — spirit/wind/breath
    "wind": "H7307",
    "breath": "H7307",
    "formless": "H8414",  # tohu — chaos/wasteland
    "waste": "H8414",
    "void": "H922",  # bohu
    "empty": "H922",
    "darkness": "H2822",  # choshek
    "light": "H216",  # or
    "deep": "H8415",  # tehom — cognate with Akkadian Tiamat
    "waters": "H4325",  # mayim
    "water": "H4325",
    "good": "H2896",  # tov
    # The divine names
    "god": "H430",  # elohim — plural form, singular meaning
    "yahweh": "H3068",  # YHWH — the tetragrammaton
    "lord": "H136",  # adonai — used in place of YHWH
    # Anthropology
    "man": "H120",  # adam — humanity
    "adam": "H120",
    "woman": "H802",  # ishshah
    "soul": "H5315",  # nephesh — life/soul/self
    "image": "H6754",  # tselem — divine image
    "likeness": "H1823",  # demut
    "dust": "H6083",  # aphar — humans formed from dust
    "ground": "H127",  # adamah — wordplay with adam
    # Genesis 3 vocabulary
    "serpent": "H5175",  # nachash
    "naked": "H6174",  # arom — wordplay with arum (subtle, v.1)
    "subtle": "H6175",  # arum
    "bruise": "H7779",  # shuph — Gen 3:15 protevangelium
    "eve": "H2332",  # chavvah — "living"
    # Common biblical theological terms
    "covenant": "H1285",  # berit
    "blood": "H1818",  # dam
    "soul": "H5315",  # nephesh
    "heart": "H3820",  # leb / lebab
    "righteousness": "H6664",  # tsedeq
    "righteous": "H6664",
    "holy": "H6918",  # qadosh
    "glory": "H3519",  # kavod
    "peace": "H7965",  # shalom
    "love": "H157",  # ahab
    "lovingkindness": "H2617",  # chesed
    "mercy": "H2617",
    "wisdom": "H2451",  # chokmah
    "fear": "H3374",  # yir'ah (fear of the LORD)
    "sin": "H2403",  # chatta'ah
    "atonement": "H3722",  # kaphar
    "redeem": "H1350",  # ga'al
    "messiah": "H4899",  # mashiach — anointed one
    "anointed": "H4899",
    "salvation": "H3444",  # yeshu'ah
}


# Words for which we already have a `word`-kind note in the corpus tend
# to be in early Genesis. We don't filter that here — prospect.py
# de-duplicates against existing notes.


class HebrewWordDetector:
    """Generate `lang-hebrew` candidates from theologically-loaded English
    keywords backed by Strong's lexical data."""

    name = "HebrewWordDetector"
    kind = "lang-hebrew"

    # Verses in OT only — Hebrew lexicon doesn't apply to NT.
    NT_BOOKS = {
        "mat", "mrk", "luk", "jhn", "act", "rom", "1co", "2co", "gal",
        "eph", "php", "col", "1th", "2th", "1ti", "2ti", "tit", "phm",
        "heb", "jas", "1pe", "2pe", "1jn", "2jn", "3jn", "jud", "rev",
    }

    def __init__(self) -> None:
        self.lex = sources.strongs_hebrew()

    def detect(
        self, book: str, chapter: int, verse: int, verse_text: str
    ) -> list[Candidate]:
        if book in self.NT_BOOKS:
            return []
        out = []
        text = verse_text.lower()
        seen_strongs = set()
        for kw, strongs_num in HEBREW_KEYWORD_MAP.items():
            if strongs_num in seen_strongs:
                continue
            # Whole-word match, case-insensitive
            if not re.search(rf"\b{re.escape(kw)}\b", text):
                continue
            entry = self.lex.get(strongs_num)
            if not entry:
                continue
            seen_strongs.add(strongs_num)
            # Confidence: weight Genesis 1–3 vocabulary highly (it's the
            # most theologically loaded), then drop off.
            conf = 0.85 if (book == "gen" and chapter <= 3) else 0.65

            body = self._format_body(kw, entry, verse_text)
            out.append(
                Candidate(
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    kind=self.kind,
                    anchor=self._find_anchor(kw, verse_text),
                    confidence=conf,
                    source_name=entry.number,
                    source_attribution=entry.attribution,
                    draft_title="Hebrew",
                    draft_label="Hebrew.",
                    draft_body=body,
                    detector=self.name,
                    reviewer_notes=(
                        "Strong's gives the lexical baseline. Add the "
                        "interpretive substance — context, theological "
                        "stakes, parallels — before promoting."
                    ),
                )
            )
        return out

    @staticmethod
    def _find_anchor(keyword: str, verse_text: str) -> str:
        """Locate the keyword in the verse to use as the anchor.
        Returns the actual cased substring from the verse."""
        m = re.search(rf"\b{re.escape(keyword)}\b", verse_text, re.IGNORECASE)
        return m.group(0) if m else ""

    @staticmethod
    def _format_body(_keyword: str, entry, _verse_text: str) -> str:
        """Compose the draft note body — a stub the user fleshes out.
        ``_keyword`` and ``_verse_text`` are kept for signature parity with
        sibling detector formatters; they're unused in this implementation."""
        lemma_part = (
            f" (<em>{entry.lemma}</em>)" if entry.lemma else ""
        )
        xlit_part = entry.xlit or "—"
        return (
            f"<strong>{xlit_part.capitalize()}{lemma_part}.</strong> "
            f"{entry.definition.strip().rstrip('.')}. "
            f"<em>[Reviewer: extend this with context, theological "
            f"reading, and any cross-canon resonance before promoting.]</em>"
        )


# ----------------------------------------------------------------------
# TSK cross-reference detector
# ----------------------------------------------------------------------


class CrossRefDetector:
    """Generate `xref-citation` candidates from Treasury of Scripture
    Knowledge — the strongest community-scored cross-references per verse."""

    name = "CrossRefDetector"
    kind = "xref-citation"

    def __init__(self, *, min_votes: int = 30, top_n: int = 3) -> None:
        self.tsk = sources.tsk()
        self.min_votes = min_votes
        self.top_n = top_n

    def detect(
        self, book: str, chapter: int, verse: int, _verse_text: str
    ) -> list[Candidate]:
        refs = self.tsk.refs_for(
            book, chapter, verse, min_votes=self.min_votes, top_n=self.top_n
        )
        if not refs:
            return []

        # One aggregated candidate per verse, with all top refs in the body.
        target_lines = []
        for r in refs:
            target_lines.append(
                f"<a href=\"#vnote-{r.target_book}-{r.target_chapter}-"
                f"{r.target_verse}\">{r.target_book.title()} "
                f"{r.target_chapter}:{r.target_verse}</a>"
            )
        targets_str = " · ".join(target_lines)
        confidence = min(0.5 + (refs[0].votes / 200), 0.95)

        body = (
            f"<strong>Cross-references.</strong> {targets_str}. "
            f"<em>[Reviewer: select 1–3 most relevant; rewrite as a "
            f"thematic note rather than a list before promoting.]</em>"
        )

        return [
            Candidate(
                book=book,
                chapter=chapter,
                verse=verse,
                kind=self.kind,
                anchor="",
                confidence=confidence,
                source_name=f"TSK ({len(refs)} refs)",
                source_attribution=refs[0].attribution,
                draft_title="Cross-ref",
                draft_label="Cite.",
                draft_body=body,
                detector=self.name,
                reviewer_notes=(
                    f"TSK community-scored. Top vote count: {refs[0].votes}. "
                    f"Don't paste the link list as the final note — "
                    f"explain the thematic connection."
                ),
            )
        ]


# ----------------------------------------------------------------------
# Nave's Topical detector (Phase χ.7)
# ----------------------------------------------------------------------


class NaveTopicalDetector:
    """Generate ``topic-nave`` candidates from Nave's Topical Bible —
    the topical-concordance entries that name a verse under one or
    more topical headings.

    Like ``CrossRefDetector``, this detector is verse-text-agnostic:
    it operates purely on (book, chapter, verse) tuples, looking up
    the reverse index in ``sources.naves_topical()``. One consolidated
    candidate is produced per verse, with the top-N topics rendered
    as a comma-separated list in the body — the reviewer's job is to
    pick one or two, write a thematic note, and discard the rest.

    Construction is lazy in two senses: the underlying source is
    lazy-loaded on first access, and a verse with zero topics yields
    an empty list (not a candidate).
    """

    name = "NaveTopicalDetector"
    kind = "topic-nave"

    def __init__(self, *, top_n: int = 5, min_topics: int = 1) -> None:
        self.naves = sources.naves_topical()
        self.top_n = top_n
        self.min_topics = min_topics

    def detect(
        self, book: str, chapter: int, verse: int, _verse_text: str
    ) -> list[Candidate]:
        topics = self.naves.topics_for(book, chapter, verse, top_n=self.top_n)
        if len(topics) < self.min_topics:
            return []

        # Confidence: more topics = stronger thematic anchoring. The
        # ceiling is conservative because Nave's tags some verses with
        # marginal topics; the reviewer's filter does the final cut.
        confidence = min(0.55 + 0.07 * len(topics), 0.85)

        topics_str = ", ".join(topics)
        primary = topics[0]
        attribution = (
            "Nave's Topical Bible, Orville J. Nave (1896). Public domain."
        )
        body = (
            f"<strong>Topics.</strong> This verse appears under: "
            f"{topics_str}. "
            f"<em>[Reviewer: pick one topic (typically the first or "
            f"most theologically loaded), write a 2–3 sentence thematic "
            f"note, and discard the rest.]</em>"
        )

        return [
            Candidate(
                book=book,
                chapter=chapter,
                verse=verse,
                kind=self.kind,
                anchor="",
                confidence=confidence,
                source_name=f"Nave: {primary}"
                + (f" (+{len(topics)-1} more)" if len(topics) > 1 else ""),
                source_attribution=attribution,
                draft_title="Topic",
                draft_label="Topic.",
                draft_body=body,
                detector=self.name,
                reviewer_notes=(
                    f"Nave's Topical lists {len(topics)} topic(s) for this "
                    f"verse. Don't paste the comma-list as the final note — "
                    f"pick the strongest theme and write a paragraph."
                ),
            )
        ]


# ----------------------------------------------------------------------
# Registry
# ----------------------------------------------------------------------

# Order matters: prospect.py runs in this order, and ties on (verse, kind)
# are broken by detector order.
ALL_DETECTORS = [
    HebrewWordDetector,
    CrossRefDetector,
    NaveTopicalDetector,
]

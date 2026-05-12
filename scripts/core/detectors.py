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
from .html_sandbox import sandbox_ai_html


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
        "php",
        "col",
        "1th",
        "2th",
        "1ti",
        "2ti",
        "tit",
        "phm",
        "heb",
        "jas",
        "1pe",
        "2pe",
        "1jn",
        "2jn",
        "3jn",
        "jud",
        "rev",
    }

    def __init__(self) -> None:
        self.lex = sources.strongs_hebrew()

    def detect(self, book: str, chapter: int, verse: int, verse_text: str) -> list[Candidate]:
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
        lemma_part = f" (<em>{entry.lemma}</em>)" if entry.lemma else ""
        xlit_part = entry.xlit or "—"
        return (
            f"<strong>{xlit_part.capitalize()}{lemma_part}.</strong> "
            f"{entry.definition.strip().rstrip('.')}. "
            f"<em>[Reviewer: extend this with context, theological "
            f"reading, and any cross-canon resonance before promoting.]</em>"
        )


# ----------------------------------------------------------------------
# Greek word detector (χ.1)
# ----------------------------------------------------------------------

# Curated map of theologically-loaded biblical Greek (NT) terms.
# Format: english_keyword → strongs_number (G-prefixed).
# Same shape and rationale as ``HEBREW_KEYWORD_MAP`` above — a small
# curated set for the MVP; extending the map widens detector coverage
# without code changes.

GREEK_KEYWORD_MAP: dict[str, str] = {
    # Johannine + Pauline core vocabulary
    "word": "G3056",  # logos — Word; the Logos in John 1
    "love": "G26",  # agape — distinctive NT love (vs philia, eros)
    "loved": "G25",  # agapao
    "faith": "G4102",  # pistis — covenantal trust
    "believe": "G4100",  # pisteuo
    "believed": "G4100",
    "lord": "G2962",  # kyrios — Lord (also LXX rendering of YHWH)
    "christ": "G5547",  # christos — anointed; LXX/NT rendering of mashiach
    "god": "G2316",  # theos
    "spirit": "G4151",  # pneuma — spirit/wind/breath
    "holy spirit": "G4151",
    "flesh": "G4561",  # sarx — Pauline anthropology
    "body": "G4983",  # soma
    "soul": "G5590",  # psyche
    "life": "G2222",  # zoe — esp. eternal life in John
    # Soteriological core
    "glory": "G1391",  # doxa
    "grace": "G5485",  # charis
    "peace": "G1515",  # eirene — LXX rendering of shalom
    "hope": "G1680",  # elpis
    "righteousness": "G1343",  # dikaiosyne
    "righteous": "G1342",  # dikaios
    "salvation": "G4991",  # soteria
    "saved": "G4982",  # sozo
    "save": "G4982",
    "resurrection": "G386",  # anastasis
    "judgment": "G2920",  # krisis
    "kingdom": "G932",  # basileia
    "church": "G1577",  # ekklesia — assembly / called-out
    "assembly": "G1577",
    "gospel": "G2098",  # evangelion — good news
    "mystery": "G3466",  # musterion
    "covenant": "G1242",  # diatheke — also "testament"
    "testament": "G1242",
    # Christological + relational
    "son": "G5207",  # huios
    "father": "G3962",  # pater
    "sin": "G266",  # hamartia
    "ransom": "G3083",  # lutron
    "redemption": "G629",  # apolytrosis
    "eternal": "G166",  # aionios — age-long / eternal
    "everlasting": "G166",
    "coming": "G3952",  # parousia — Christ's return
    "season": "G2540",  # kairos — appointed time
    "name": "G3686",  # onoma
    "truth": "G225",  # aletheia
    "true": "G228",  # alethinos
    "way": "G3598",  # hodos
    "light": "G5457",  # phos — NT counterpart of Hebrew or
    "darkness": "G4655",  # skotos
    "blood": "G129",  # haima — NT counterpart of Hebrew dam
    "blessed": "G3107",  # makarios — Beatitudes vocabulary
    "heart": "G2588",  # kardia
    "mind": "G3563",  # nous
    "knowledge": "G1108",  # gnosis
    "wisdom": "G4678",  # sophia
    "fear": "G5401",  # phobos
    "perfect": "G5046",  # teleios — completeness, maturity
    "holy": "G40",  # hagios
    # Christ-incarnation specific
    "lamb": "G721",  # arnion — esp. Revelation
    "sheep": "G4263",  # probaton
    "shepherd": "G4166",  # poimen
    "vine": "G288",  # ampelos
    "bread": "G740",  # artos
    "rock": "G4073",  # petra — Matt 16
    "stone": "G3037",  # lithos
    "temple": "G3485",  # naos — inner sanctuary
}


class GreekWordDetector:
    """Generate ``lang-greek`` candidates from theologically-loaded
    English keywords backed by Strong's Greek lexical data.

    Mirror of :class:`HebrewWordDetector` for NT verses. Returns ``[]``
    for OT books — the LXX is also Greek, but tagging LXX/Apocrypha is
    out of scope for χ.1 (the KJV translation data ships only the
    Reformed canon, and the Apocrypha translation set is sparse). A
    future χ.* phase can extend this to LXX/Apocrypha by removing the
    ``not in NT_BOOKS`` filter and expanding the keyword map."""

    name = "GreekWordDetector"
    kind = "lang-greek"

    # Verses in NT only — Greek lexicon applies to NT (and LXX, deferred).
    NT_BOOKS = {
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
        "php",
        "col",
        "1th",
        "2th",
        "1ti",
        "2ti",
        "tit",
        "phm",
        "heb",
        "jas",
        "1pe",
        "2pe",
        "1jn",
        "2jn",
        "3jn",
        "jud",
        "rev",
    }

    def __init__(self) -> None:
        self.lex = sources.strongs_greek()

    def detect(self, book: str, chapter: int, verse: int, verse_text: str) -> list[Candidate]:
        if book not in self.NT_BOOKS:
            return []
        out = []
        text = verse_text.lower()
        seen_strongs = set()
        for kw, strongs_num in GREEK_KEYWORD_MAP.items():
            if strongs_num in seen_strongs:
                continue
            # Whole-word match, case-insensitive
            if not re.search(rf"\b{re.escape(kw)}\b", text):
                continue
            entry = self.lex.get(strongs_num)
            if not entry:
                continue
            seen_strongs.add(strongs_num)
            # Confidence: weight Johannine + Pauline core terms in their
            # most theologically loaded contexts. Conservative ceiling
            # because keyword matching is necessarily lossy (English
            # ambiguity around "word", "love", "lord" etc.).
            conf = 0.85 if (book in {"jhn", "rom"} and chapter <= 8) else 0.65

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
                    draft_title="Greek",
                    draft_label="Greek.",
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
        ``_keyword`` and ``_verse_text`` are kept for signature parity
        with ``HebrewWordDetector._format_body``; unused here."""
        lemma_part = f" (<em>{entry.lemma}</em>)" if entry.lemma else ""
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

    def detect(self, book: str, chapter: int, verse: int, _verse_text: str) -> list[Candidate]:
        refs = self.tsk.refs_for(book, chapter, verse, min_votes=self.min_votes, top_n=self.top_n)
        if not refs:
            return []

        # One aggregated candidate per verse, with all top refs in the body.
        target_lines = []
        for r in refs:
            target_lines.append(
                f'<a href="#vnote-{r.target_book}-{r.target_chapter}-'
                f'{r.target_verse}">{r.target_book.title()} '
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

    def detect(self, book: str, chapter: int, verse: int, _verse_text: str) -> list[Candidate]:
        topics = self.naves.topics_for(book, chapter, verse, top_n=self.top_n)
        if len(topics) < self.min_topics:
            return []

        # Confidence: more topics = stronger thematic anchoring. The
        # ceiling is conservative because Nave's tags some verses with
        # marginal topics; the reviewer's filter does the final cut.
        confidence = min(0.55 + 0.07 * len(topics), 0.85)

        topics_str = ", ".join(topics)
        primary = topics[0]
        attribution = "Nave's Topical Bible, Orville J. Nave (1896). Public domain."
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
                source_name=f"Nave: {primary}" + (f" (+{len(topics) - 1} more)" if len(topics) > 1 else ""),
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
# Kenyon textual-criticism detector (Phase χ.0)
# ----------------------------------------------------------------------


# OCR artifacts in the 1914-stamped Kenyon scan show up as caret runs
# (`^^^`), stray `^TM`, isolated punctuation tokens, and stray
# backslashes. We strip the worst of these from the context window
# before emitting a candidate; what remains is still draft prose for a
# reviewer, not finished copy. Backslashes specifically must go because
# a stored literal `\<space>` triggers a SyntaxWarning when notes are
# parsed via ast.literal_eval (e.g. `li\ Luke 6. 48` from p.124 of the
# scan).
_KENYON_OCR_ARTIFACT_RE = re.compile(r"\^+|[`~|\\]")
_KENYON_MULTI_PUNCT_RE = re.compile(r"([.,;:!?]){3,}")


def _clean_kenyon_context(s: str) -> str:
    """Strip the loudest OCR artifacts from one Kenyon context window.
    Conservative — only removes characters that are unambiguously
    scanner noise; legitimate punctuation is preserved."""
    s = _KENYON_OCR_ARTIFACT_RE.sub(" ", s)
    s = _KENYON_MULTI_PUNCT_RE.sub(r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


class KenyonReferenceDetector:
    """Generate ``text-witness`` candidates from Kenyon's PD textual-
    criticism prose (*Our Bible and the Ancient Manuscripts*, 1895).

    Unlike the per-verse detectors above, this one walks the cached
    source text once via ``KenyonText.references()`` and yields all
    candidates flat — the driver then groups by (book, chapter) before
    writing per-chapter candidate JSON.

    Per-verse interface is preserved for parity with the χ-cluster
    pattern (so this can be used as a drop-in via
    ``ALL_DETECTORS`` if a future caller needs verse-keyed access).
    Implementation: an in-memory index built once on first ``detect()``
    call.
    """

    name = "KenyonReferenceDetector"
    kind = "text-witness"

    def __init__(self, *, max_candidates_per_verse: int = 1) -> None:
        self.max_candidates_per_verse = max_candidates_per_verse
        # Lazy index: built on first detect() / iter_candidates() call
        self._index: dict[tuple[str, int, int], list[str]] | None = None

    def _build_index(self) -> dict[tuple[str, int, int], list[str]]:
        kenyon = sources.kenyon_text()
        idx: dict[tuple[str, int, int], list[str]] = {}
        for ref in kenyon.references():
            key = (ref.book, ref.chapter, ref.verse)
            idx.setdefault(key, []).append(_clean_kenyon_context(ref.context))
        return idx

    def detect(self, book: str, chapter: int, verse: int, _verse_text: str) -> list[Candidate]:
        if self._index is None:
            self._index = self._build_index()
        contexts = self._index.get((book, chapter, verse), [])
        if not contexts:
            return []
        out: list[Candidate] = []
        for context in contexts[: self.max_candidates_per_verse]:
            attribution = (
                "Frederic G. Kenyon, *Our Bible and the Ancient "
                "Manuscripts* (Eyre & Spottiswoode, London, 1895). "
                "Public domain."
            )
            body = (
                f"<strong>Manuscript witness.</strong> "
                f"{_xml_escape_text_for_kenyon(context)} "
                f"<em>[Reviewer: trim to the relevant clause; the "
                f"surrounding context is provided so you can judge "
                f"which version / witness Kenyon is discussing.]</em>"
            )
            out.append(
                Candidate(
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    kind=self.kind,
                    anchor="",
                    confidence=0.55,  # draft-quality; reviewer trims
                    source_name="Kenyon 1895",
                    source_attribution=attribution,
                    draft_title="Witness",
                    draft_label="MS.",
                    draft_body=body,
                    detector=self.name,
                    reviewer_notes=(
                        "Kenyon's textual-criticism prose. Don't paste the "
                        "raw context — pick the clause that names the "
                        "witness (Codex, Old Latin, LXX, Peshitto, etc.) "
                        "and write a 1-2 sentence note on what that "
                        "witness does for this verse."
                    ),
                )
            )
        return out

    def iter_all_candidates(self):
        """Bulk iteration — yields every candidate the detector would
        emit across the entire Kenyon corpus, in (book, chapter, verse)
        order. Used by ``run_kenyon_at_scale.py`` to avoid the per-verse
        loop overhead and to expose a stable order for testing."""
        if self._index is None:
            self._index = self._build_index()
        for key in sorted(self._index.keys()):
            book, chapter, verse = key
            for c in self.detect(book, chapter, verse, _verse_text=""):
                yield c


def _xml_escape_text_for_kenyon(s: str) -> str:
    """Escape `&`, `<`, `>` for safe inclusion in HTML body text. Local
    helper (mirror of the same-named one in build_edition); kept here
    so detectors.py doesn't need a cross-module import for one trivial
    string transform."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ----------------------------------------------------------------------
# AI-backed thematic xref detector (Phase χ-AI-xrefs)
# ----------------------------------------------------------------------


# Display labels for the kind_subclass field on the rendered note body.
# Kept here (not on the model side) so the body's prose stays consistent
# regardless of the model's exact wording.
_AI_XREF_SUBCLASS_LABEL = {
    "typological": "Typological",
    "thematic": "Thematic",
    "idiomatic": "Idiomatic",
}


class AIXrefDetector:
    """Generate ``xref-thematic`` candidates from an LLM proposer
    (``sources.AnthropicXrefClient``).

    Phase χ-AI-xrefs (2026-05-08). The first χ-cluster detector backed
    by an API rather than a static cached source; otherwise mirrors the
    existing pattern (verse-text-driven, lazy source via the singleton,
    SourceMissingError on construction propagates to ``prospect.py``'s
    resilient instantiation handler — same graceful-degrade contract
    as ``NaveTopicalDetector`` when its JSON cache is absent).

    The detector caps proposals at ``top_n`` per verse and filters
    below ``min_confidence`` before returning. Cost-conscious by
    design: the cap + floor + the driver's ``--max-verses`` together
    bound the API spend.
    """

    name = "AIXrefDetector"
    kind = "xref-thematic"

    def __init__(
        self,
        *,
        client=None,
        top_n: int = 3,
        min_confidence: float = 0.7,
    ) -> None:
        if client is None:
            client = sources.anthropic_xref_client()
        self.client = client
        self.top_n = top_n
        self.min_confidence = min_confidence

    def detect(self, book: str, chapter: int, verse: int, verse_text: str) -> list[Candidate]:
        proposals = self.client.propose_xrefs(
            book,
            chapter,
            verse,
            verse_text,
            top_n=self.top_n,
        )
        out: list[Candidate] = []
        for p in proposals:
            confidence = float(p.get("confidence", 0.0))
            if confidence < self.min_confidence:
                continue
            target_book = p["target_book"]
            target_chapter = p["target_chapter"]
            target_verse = p["target_verse"]
            subclass = p.get("kind_subclass", "thematic")
            subclass_label = _AI_XREF_SUBCLASS_LABEL.get(subclass, "Thematic")
            reasoning = p.get("reasoning", "")

            target_link = (
                f'<a href="#vnote-{target_book}-{target_chapter}-'
                f'{target_verse}">{target_book.title()} '
                f"{target_chapter}:{target_verse}</a>"
            )
            body = (
                f"<strong>{subclass_label} cross-reference.</strong> "
                f"{target_link}. {_xml_escape_text_for_kenyon(reasoning)} "
                f"<em>[Reviewer: AI-proposed; verify the link is sound, "
                f"trim the reasoning, and decide whether to keep before "
                f"promoting.]</em>"
            )

            out.append(
                Candidate(
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    kind=self.kind,
                    anchor="",
                    confidence=confidence,
                    source_name=(f"AI: {target_book} {target_chapter}:{target_verse} ({subclass})"),
                    source_attribution=self.client.attribution,
                    draft_title="Thematic",
                    draft_label=f"{subclass_label[:5]}.",
                    draft_body=body,
                    detector=self.name,
                    reviewer_notes=(
                        f"AI-proposed {subclass} link with confidence "
                        f"{confidence:.2f}. The model's reasoning is a draft, "
                        f"not the final note — rewrite in the project's voice "
                        f"and discard if the connection is too thin."
                    ),
                )
            )
        return out


# ----------------------------------------------------------------------
# AI-backed first-draft note generator (Phase χ-AI-notes)
# ----------------------------------------------------------------------


# Display labels for the kind_class field on the rendered note body.
# Mirrors AIXrefDetector's _AI_XREF_SUBCLASS_LABEL pattern: kept here
# (not on the model side) so the rendered prose stays consistent
# regardless of the model's exact wording.
_AI_NOTE_CLASS_LABEL = {
    "explanatory": "Background",
    "study": "Study",
    "translation": "Translation",
}


class AINoteDetector:
    """Generate ``comm-ai`` candidates from an LLM note drafter
    (``sources.AnthropicNoteClient``).

    Phase χ-AI-notes (2026-05-10). Sibling of ``AIXrefDetector``;
    same lazy-source-via-singleton pattern, same SourceMissingError
    propagation contract, same min_confidence floor. Distinct from
    AIXrefDetector in what it emits — first-draft *note prose* for
    a verse, not links between verses.

    Reviewer-flag invariant: every emitted candidate carries an
    explicit ``[Reviewer: AI-generated, requires human approval]``
    flag in the body so a draft can never be confused with a
    reviewed note in the editor / preview surface.

    ξ.15 sandbox: every model-emitted ``body_html`` and ``label`` is
    run through ``html_sandbox.sandbox_ai_html`` before being woven
    into the candidate body. The sandbox is a strict subset of
    publisher-grade ``sanitize_html`` — only ``em``, ``strong``,
    ``b``, ``i``, ``sup``, ``sub``, ``code``, ``br``, ``span``, ``p``
    and in-document anchors on ``<a>`` survive. Anything else is
    stripped (inner text preserved). A second sandbox pass also
    fires in ``promote.promote_candidate`` for kinds in
    ``matrix.AI_DRAFTED_KINDS`` — defense in depth.
    """

    name = "AINoteDetector"
    kind = "comm-ai"

    def __init__(
        self,
        *,
        client=None,
        min_confidence: float = 0.65,
        tradition: str | None = None,
    ) -> None:
        if client is None:
            client = sources.anthropic_note_client()
        self.client = client
        self.min_confidence = min_confidence
        self.tradition = tradition

    def detect(self, book: str, chapter: int, verse: int, verse_text: str) -> list[Candidate]:
        draft = self.client.draft_note(
            book,
            chapter,
            verse,
            verse_text,
            tradition=self.tradition,
        )
        if draft is None:
            return []
        confidence = float(draft.get("confidence", 0.0))
        if confidence < self.min_confidence:
            return []

        kind_class = draft.get("kind_class", "explanatory")
        class_label = _AI_NOTE_CLASS_LABEL.get(kind_class, "Note")
        label = (draft.get("label") or "").strip()
        body_html = (draft.get("body_html") or "").strip()
        flags = draft.get("reviewer_flags") or []

        # ξ.15 sandbox: pass every model-emitted string through the
        # AI-strict allowlist BEFORE composition into the final body.
        # Drops <script>, <iframe>, javascript: URLs, on* handlers,
        # and any tag outside the strict AI allowlist. Idempotent;
        # safe to re-apply. If the sandbox empties the body, we still
        # emit the candidate with the reviewer flag so the queue
        # surfaces the empty draft for human attention rather than
        # silently swallowing it.
        label = sandbox_ai_html(label)
        body_html = sandbox_ai_html(body_html)

        # Reviewer-flag invariant: every AI note draft carries an
        # explicit AI-generated flag so the editor / preview cannot
        # mistake it for a reviewed note. The label is bolded by the
        # renderer so we don't bold it again here — match the
        # existing AIXrefDetector body shape.
        body = (
            f"<strong>{label}</strong> {body_html} "
            f"<em>[Reviewer: AI-generated, requires human approval. "
            f"Edit freely; discard if the draft does not earn its "
            f"place. Class: {class_label}.]</em>"
        )

        # Reviewer notes — separate from the body, surfaced in the
        # candidate JSON for the queue. Includes the model's
        # self-flagged concerns + sources_consulted + the standing
        # AI-draft warning. The reviewer reads this BEFORE looking at
        # the body, so it tells them what to focus on.
        reviewer_lines = [
            f"AI-generated first-draft note (class: {class_label}, "
            f"confidence {confidence:.2f}). Reviewer must verify the "
            f"substance, edit the prose into the project's voice, "
            f"and discard if the draft does not warrant a note.",
        ]
        if draft.get("sources_consulted"):
            sources_list = ", ".join(draft["sources_consulted"])
            reviewer_lines.append(f"Sources consulted by drafter: {sources_list}.")
        for flag in flags:
            if isinstance(flag, str) and flag.strip():
                reviewer_lines.append(f"AI-flagged: {flag.strip()}")
        reviewer_notes = " ".join(reviewer_lines)

        return [
            Candidate(
                book=book,
                chapter=chapter,
                verse=verse,
                kind=self.kind,
                anchor="",
                confidence=confidence,
                source_name=f"AI: {class_label} draft for {book} {chapter}:{verse}",
                source_attribution=self.client.attribution,
                draft_title=class_label,
                draft_label=label,
                draft_body=body,
                detector=self.name,
                reviewer_notes=reviewer_notes,
            )
        ]


# ----------------------------------------------------------------------
# Patristic commentary detector (γ.3 — 2026-05-11)
# ----------------------------------------------------------------------


class PatristicCommentaryDetector:
    """Emit `comm-patristic` candidates from the curated Patristic
    corpus (`content/sources/patristic_commentaries.json`).

    Unlike the keyword-matching language detectors, this is a
    *direct-lookup* detector: each entry in the JSON has an exact
    `(book, chapter, verse)` target, and the detector emits one
    candidate per matching entry. Confidence is high (0.95)
    because the data is hand-curated from public-domain Church
    Father commentaries, not heuristic.

    Body shape: an `<aside>` block carrying the Father's name +
    work + circa-year + the summary paragraph. Promoted notes
    carry the NPNF attribution into the YAML.

    Build-pipeline considerations: the resulting `comm-patristic`
    notes participate in the existing tradition filter (ψ.8)
    when an edition's `traditions_default` includes `patristic`.
    Editions that don't tag the patristic tradition simply omit
    these notes from the EPUB.
    """

    name = "PatristicCommentaryDetector"
    kind = "comm-patristic"

    def __init__(self) -> None:
        self.corpus = sources.patristic_commentaries()

    def detect(self, book: str, chapter: int, verse: int, verse_text: str) -> list[Candidate]:
        # verse_text is unused — direct lookup by (book, chapter, verse).
        entries = self.corpus.for_verse(book, chapter, verse)
        if not entries:
            return []
        out: list[Candidate] = []
        for entry in entries:
            body = self._format_body(entry)
            out.append(
                Candidate(
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    kind=self.kind,
                    anchor="",  # whole-verse anchor (Patristic comment on the entire verse)
                    confidence=0.95,
                    source_name=f"{entry.father} / {entry.work}",
                    source_attribution=entry.attribution,
                    draft_title=f"Patristic — {entry.father}",
                    draft_label=f"{entry.father} ({entry.year}).",
                    draft_body=body,
                    detector=self.name,
                    reviewer_notes=(
                        "Curated PD interpretive summary from "
                        f"{entry.father}, {entry.work}. Verify the "
                        "summary still reflects the source's argument "
                        "before promoting; substitute a verbatim quote "
                        "from the NPNF dump where available."
                    ),
                )
            )
        return out

    @staticmethod
    def _format_body(entry: "sources.PatristicCommentary") -> str:
        """Render the entry's HTML body. Mirrors the other detectors'
        HTML shape: header line with the Father + work + year, then
        the summary paragraph."""
        # The summary text is already HTML-safe by construction (no
        # user-controlled content) but escape defensively to keep the
        # XSS-by-design contract honest.
        import html as _html

        father = _html.escape(entry.father)
        work = _html.escape(entry.work)
        summary = _html.escape(entry.summary)
        return (
            f'<aside class="note-comm-patristic">'
            f"<strong>{father}</strong> "
            f"<em>{work}</em> "
            f"<small>(c. {int(entry.year)} AD)</small>"
            f"<p>{summary}</p>"
            f"</aside>"
        )


# ----------------------------------------------------------------------
# Ethiopian commentary detector (γ.4 — 2026-05-11) — flagship payload
# ----------------------------------------------------------------------


class EthiopianCommentaryDetector:
    """Emit `comm-ethiopian` candidates from the curated Ethiopian
    Tewahedo corpus (`content/sources/ethiopian_commentaries.json`).

    Structurally parallel to γ.3's PatristicCommentaryDetector — a
    direct-lookup detector keyed on (book, chapter, verse) emitting
    one Candidate per matching entry. The semantic difference is
    *tradition*: this detector surfaces the Syriac / non-Chalcedonian
    / Tewahedo-canon (1 Enoch) / Andəmta sources the Ethiopian
    Tewahedo communion distinctively receives.

    The proposal calls γ.4 "the flagship payload — the Tewahedo
    Bible's primary differentiator". The eventual goal is a
    full Andəmta corpus from PD Ge'ez ETLs; γ.4 ships a ~12-entry
    seed across Genesis / Psalms / John to prove the pipeline, with
    γ.4.x to expand.

    Build-pipeline considerations: the resulting `comm-ethiopian`
    notes participate in the existing tradition filter (ψ.8) when
    an edition's `traditions_default` includes `tewahedo`. The
    Ethiopian Tewahedo edition (`ethiopian-tewahedo`) consumes
    them directly; other editions can opt in per their own
    traditions config.
    """

    name = "EthiopianCommentaryDetector"
    kind = "comm-ethiopian"

    def __init__(self) -> None:
        self.corpus = sources.ethiopian_commentaries()

    def detect(self, book: str, chapter: int, verse: int, verse_text: str) -> list[Candidate]:
        # verse_text is unused — direct lookup by (book, chapter, verse).
        entries = self.corpus.for_verse(book, chapter, verse)
        if not entries:
            return []
        out: list[Candidate] = []
        for entry in entries:
            body = self._format_body(entry)
            out.append(
                Candidate(
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    kind=self.kind,
                    anchor="",  # whole-verse anchor
                    confidence=0.95,
                    source_name=f"{entry.father} / {entry.work}",
                    source_attribution=entry.attribution,
                    draft_title=f"Tewahedo — {entry.father}",
                    draft_label=f"{entry.father} ({entry.year}).",
                    draft_body=body,
                    detector=self.name,
                    reviewer_notes=(
                        "Curated PD interpretive summary representing the "
                        f"Ethiopian Tewahedo tradition's reading via "
                        f"{entry.father}, {entry.work}. Verify the summary "
                        "still reflects the source's argument before "
                        "promoting; substitute a verbatim quote from the "
                        "NPNF / Charles dump where available, and where "
                        "applicable cross-check the Andəmta homiletic "
                        "tradition for resonance."
                    ),
                )
            )
        return out

    @staticmethod
    def _format_body(entry: "sources.EthiopianCommentary") -> str:
        """Render the entry's HTML body. Mirrors γ.3's pattern.

        The summary text is already escape-safe by construction (no
        user-controlled content) but escape defensively to keep the
        XSS-by-design contract honest.
        """
        import html as _html

        father = _html.escape(entry.father)
        work = _html.escape(entry.work)
        summary = _html.escape(entry.summary)
        # Year may be negative (e.g. 1 Enoch c. 200 BC). Render "BC"
        # for negative, "AD" for positive so the chip stays correct
        # across the canonical span.
        year = int(entry.year)
        era = "BC" if year < 0 else "AD"
        year_display = abs(year)
        return (
            f'<aside class="note-comm-ethiopian">'
            f"<strong>{father}</strong> "
            f"<em>{work}</em> "
            f"<small>(c. {year_display} {era})</small>"
            f"<p>{summary}</p>"
            f"</aside>"
        )


class ProtestantCommentaryDetector:
    """Emit `comm-protestant` candidates from the curated post-Reformation
    Protestant corpus (`content/sources/protestant_commentaries.json`).

    Structurally parallel to γ.3's PatristicCommentaryDetector and γ.4's
    EthiopianCommentaryDetector — a direct-lookup detector keyed on
    (book, chapter, verse) emitting one Candidate per matching entry.
    The semantic difference is *tradition*: this detector surfaces the
    post-Reformation English Nonconformist / Puritan / Evangelical
    exposition (Matthew Henry, Spurgeon, Edwards, Hodge) — distinct from
    the magisterial Reformers covered by comm-reformation.

    Build-pipeline considerations: the resulting `comm-protestant`
    notes participate in the existing tradition filter (ψ.8) when an
    edition's `traditions_default` includes `protestant`. The
    `evangelical-reformed` edition consumes them directly; other
    editions can opt in per their own traditions config.

    χ.2 ships a ~12-entry Matthew Henry seed across Genesis / Psalms /
    John to prove the pipeline; χ.2.x will expand from CCEL / Project
    Gutenberg dumps via per-pericope summarization.
    """

    name = "ProtestantCommentaryDetector"
    kind = "comm-protestant"

    def __init__(self) -> None:
        self.corpus = sources.protestant_commentaries()

    def detect(self, book: str, chapter: int, verse: int, verse_text: str) -> list[Candidate]:
        # verse_text is unused — direct lookup by (book, chapter, verse).
        entries = self.corpus.for_verse(book, chapter, verse)
        if not entries:
            return []
        out: list[Candidate] = []
        for entry in entries:
            body = self._format_body(entry)
            out.append(
                Candidate(
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    kind=self.kind,
                    anchor="",  # whole-verse anchor
                    confidence=0.95,
                    source_name=f"{entry.commentator} / {entry.work}",
                    source_attribution=entry.attribution,
                    draft_title=f"Protestant — {entry.commentator}",
                    draft_label=f"{entry.commentator} ({entry.year}).",
                    draft_body=body,
                    detector=self.name,
                    reviewer_notes=(
                        "Curated PD interpretive summary representing the "
                        f"post-Reformation English Protestant tradition's "
                        f"reading via {entry.commentator}, {entry.work}. "
                        "Verify the summary still reflects the expositor's "
                        "argument before promoting; substitute a verbatim "
                        "quote from the CCEL / Project Gutenberg dump where "
                        "available."
                    ),
                )
            )
        return out

    @staticmethod
    def _format_body(entry: "sources.ProtestantCommentary") -> str:
        """Render the entry's HTML body. Mirrors γ.3 / γ.4 pattern.

        The summary text is escape-safe by construction (no user-
        controlled content) but escape defensively to keep the
        XSS-by-design contract honest.
        """
        import html as _html

        commentator = _html.escape(entry.commentator)
        work = _html.escape(entry.work)
        summary = _html.escape(entry.summary)
        # All Protestant expositors in the corpus are post-Reformation
        # (1500+) so plain year display suffices — no BC/AD branching
        # needed (γ.4's BC handling was required for 1 Enoch's c. 200 BC).
        year = int(entry.year)
        return (
            f'<aside class="note-comm-protestant">'
            f"<strong>{commentator}</strong> "
            f"<em>{work}</em> "
            f"<small>({year})</small>"
            f"<p>{summary}</p>"
            f"</aside>"
        )


class CatholicCommentaryDetector:
    """Emit `comm-catholic` candidates from Aquinas's Catena Aurea
    (`content/sources/catholic_commentaries.json`).

    Structurally parallel to γ.3 / γ.4 / χ.2 — a direct-lookup detector
    keyed on (book, chapter, verse) emitting one Candidate per matching
    entry. The semantic distinction from γ.3 is the *framing tradition*:
    every Father voice surfaced here is Aquinas-selected and Aquinas-
    sequenced, representing the medieval Catholic reception of the
    Fathers via the Catena. The same Church Father (Augustine, Origen,
    Chrysostom) may legitimately appear in both γ.3's patristic corpus
    and χ.4's Catholic corpus — the two readings are tagged with
    different kinds to surface in different denominational lenses
    (catholic-study edition opts into comm-catholic; eastern-orthodox
    edition consumes comm-patristic).

    Body rendering uses **BC/AD-aware year display** because Origen
    (d. 254 AD) and other early Fathers in the Catena cross the AD
    transition — mirrors γ.4's pattern. Coverage is Gospels-only per
    the Catena's original scope.

    Build-pipeline considerations: comm-catholic notes participate in
    the existing tradition filter (ψ.8) when an edition's
    `traditions_default` includes `catholic`. The catholic-study and
    anglican-bcp editions consume them directly.

    χ.4 ships a ~12-entry seed across all four Gospels to prove the
    pipeline; χ.4.x will expand from the Newman/Pusey 1841-1845
    Oxford edition (CCEL hosts the full PD text).
    """

    name = "CatholicCommentaryDetector"
    kind = "comm-catholic"

    def __init__(self) -> None:
        self.corpus = sources.catholic_commentaries()

    def detect(self, book: str, chapter: int, verse: int, verse_text: str) -> list[Candidate]:
        # verse_text is unused — direct lookup by (book, chapter, verse).
        entries = self.corpus.for_verse(book, chapter, verse)
        if not entries:
            return []
        out: list[Candidate] = []
        for entry in entries:
            body = self._format_body(entry)
            out.append(
                Candidate(
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    kind=self.kind,
                    anchor="",  # whole-verse anchor
                    confidence=0.95,
                    source_name=f"{entry.father} / {entry.work}",
                    source_attribution=entry.attribution,
                    draft_title=f"Catholic (Catena Aurea) — {entry.father}",
                    draft_label=f"{entry.father} ({entry.year}), via Catena Aurea.",
                    draft_body=body,
                    detector=self.name,
                    reviewer_notes=(
                        "Curated PD interpretive summary representing the "
                        f"medieval Catholic reception of {entry.father} "
                        f"via Aquinas's Catena Aurea. Verify the summary "
                        "still reflects the Father's argument as Aquinas "
                        "framed it before promoting; substitute a verbatim "
                        "quote from the Newman/Pusey Oxford 1841-1845 "
                        "edition (CCEL) where available."
                    ),
                )
            )
        return out

    @staticmethod
    def _format_body(entry: "sources.CatholicCommentary") -> str:
        """Render the entry's HTML body. Mirrors γ.4's BC/AD pattern
        since some Catena Fathers (Origen d. 254 AD, Tertullian, etc.)
        sit near the AD transition.

        The summary text is escape-safe by construction (no user-
        controlled content) but escape defensively to keep the
        XSS-by-design contract honest.
        """
        import html as _html

        father = _html.escape(entry.father)
        work = _html.escape(entry.work)
        summary = _html.escape(entry.summary)
        year = int(entry.year)
        era = "BC" if year < 0 else "AD"
        year_display = abs(year)
        return (
            f'<aside class="note-comm-catholic">'
            f"<strong>{father}</strong> "
            f"<em>{work}</em> "
            f"<small>(c. {year_display} {era})</small>"
            f"<p>{summary}</p>"
            f"</aside>"
        )


class ReformationCommentaryDetector:
    """Emit `comm-reformation` candidates from the 16th c. magisterial
    Reformation corpus (`content/sources/reformation_commentaries.json`).

    Structurally parallel to γ.3 / γ.4 / χ.2 / χ.4 — a direct-lookup
    detector keyed on (book, chapter, verse) emitting one Candidate
    per matching entry. The semantic distinction from χ.2 is *period*:
    χ.3 covers the 16th c. magisterial Reformation narrowly (Calvin,
    Luther, Zwingli, Anabaptist expositors — years 1517-1564); χ.2
    covers the broader post-Reformation English tradition (Henry,
    Spurgeon, Edwards, Hodge — post-1700).

    Body rendering uses **plain year display** (mirrors χ.2) — all
    magisterial Reformers are post-1500, no BC/AD branching needed.

    Build-pipeline considerations: comm-reformation notes participate
    in the existing tradition filter (ψ.8). The lutheran-confessional
    edition's `traditions_default` declares `protestant`, which
    surfaces both comm-protestant (broader) AND comm-reformation
    (narrower 16th c.) — the edition itself doesn't need to know the
    period distinction; downstream UIs can chip them differently.

    χ.3 ships a ~12-entry Calvin-only seed across both Testaments;
    χ.3.x will expand from the Calvin Translation Society Edinburgh
    1843-1855 edition (CCEL hosts the full PD text).
    """

    name = "ReformationCommentaryDetector"
    kind = "comm-reformation"

    def __init__(self) -> None:
        self.corpus = sources.reformation_commentaries()

    def detect(self, book: str, chapter: int, verse: int, verse_text: str) -> list[Candidate]:
        # verse_text is unused — direct lookup by (book, chapter, verse).
        entries = self.corpus.for_verse(book, chapter, verse)
        if not entries:
            return []
        out: list[Candidate] = []
        for entry in entries:
            body = self._format_body(entry)
            out.append(
                Candidate(
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    kind=self.kind,
                    anchor="",  # whole-verse anchor
                    confidence=0.95,
                    source_name=f"{entry.commentator} / {entry.work}",
                    source_attribution=entry.attribution,
                    draft_title=f"Reformation — {entry.commentator}",
                    draft_label=f"{entry.commentator} ({entry.year}).",
                    draft_body=body,
                    detector=self.name,
                    reviewer_notes=(
                        "Curated PD interpretive summary representing the "
                        f"16th c. magisterial Reformation reading via "
                        f"{entry.commentator}, {entry.work}. Verify the "
                        "summary still reflects the Reformer's argument "
                        "before promoting; substitute a verbatim quote "
                        "from the Calvin Translation Society Edinburgh "
                        "1843-1855 edition (CCEL) where available."
                    ),
                )
            )
        return out

    @staticmethod
    def _format_body(entry: "sources.ReformationCommentary") -> str:
        """Render the entry's HTML body. Mirrors χ.2 (plain year
        display, no BC/AD branching) — all magisterial Reformers are
        post-1500.

        The summary text is escape-safe by construction (no user-
        controlled content) but escape defensively to keep the
        XSS-by-design contract honest.
        """
        import html as _html

        commentator = _html.escape(entry.commentator)
        work = _html.escape(entry.work)
        summary = _html.escape(entry.summary)
        year = int(entry.year)
        return (
            f'<aside class="note-comm-reformation">'
            f"<strong>{commentator}</strong> "
            f"<em>{work}</em> "
            f"<small>({year})</small>"
            f"<p>{summary}</p>"
            f"</aside>"
        )


class RabbinicCommentaryDetector:
    """Emit `comm-rabbinic` candidates from the rabbinic-tradition corpus
    (`content/sources/rabbinic_commentaries.json`).

    Structurally parallel to γ.3 / γ.4 / χ.2 / χ.4 / χ.3 — a direct-
    lookup detector keyed on (book, chapter, verse) emitting one
    Candidate per matching entry. The semantic distinction from the
    Christian comm-* siblings is *tradition*: the kind comm-rabbinic
    surfaces voices from the Jewish medieval-classical exegetical
    chain (Rashi, Maimonides, Ibn Ezra, Ramban, Targumim, etc.).

    Body rendering uses **plain year display** (mirrors χ.2 / χ.3) —
    Rashi died 1105 AD; all rabbinic-tradition voices in the χ.5 seed
    are post-AD, no BC/AD branching needed.

    Build-pipeline considerations: comm-rabbinic notes participate in
    the existing tradition filter (ψ.8) when an edition's
    `traditions_default` includes `jewish`. The jewish-study edition
    consumes them directly per traditions.yaml.

    χ.5 ships a ~12-entry Rashi-only seed weighted toward Pentateuch;
    χ.5.x will expand from primary Hebrew sources (Rashi medieval
    Hebrew is PD) + add Maimonides / Ibn Ezra / Ramban / Targum entries.
    """

    name = "RabbinicCommentaryDetector"
    kind = "comm-rabbinic"

    def __init__(self) -> None:
        self.corpus = sources.rabbinic_commentaries()

    def detect(self, book: str, chapter: int, verse: int, verse_text: str) -> list[Candidate]:
        # verse_text is unused — direct lookup by (book, chapter, verse).
        entries = self.corpus.for_verse(book, chapter, verse)
        if not entries:
            return []
        out: list[Candidate] = []
        for entry in entries:
            body = self._format_body(entry)
            out.append(
                Candidate(
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    kind=self.kind,
                    anchor="",  # whole-verse anchor
                    confidence=0.95,
                    source_name=f"{entry.commentator} / {entry.work}",
                    source_attribution=entry.attribution,
                    draft_title=f"Rabbinic — {entry.commentator}",
                    draft_label=f"{entry.commentator} ({entry.year}).",
                    draft_body=body,
                    detector=self.name,
                    reviewer_notes=(
                        "Curated PD interpretive summary representing the "
                        f"Jewish medieval-classical exegetical tradition's "
                        f"reading via {entry.commentator}, {entry.work}. "
                        "The medieval Hebrew text is PD by age; verify the "
                        "summary still reflects the exegete's argument "
                        "before promoting; for direct quotation, use a "
                        "confirmed-PD English edition (most modern Rashi "
                        "translations are still in copyright)."
                    ),
                )
            )
        return out

    @staticmethod
    def _format_body(entry: "sources.RabbinicCommentary") -> str:
        """Render the entry's HTML body. Mirrors χ.2 / χ.3 (plain year
        display, no BC/AD branching — all χ.5 seed voices are
        post-AD).

        The summary text is escape-safe by construction (no user-
        controlled content) but escape defensively to keep the
        XSS-by-design contract honest.
        """
        import html as _html

        commentator = _html.escape(entry.commentator)
        work = _html.escape(entry.work)
        summary = _html.escape(entry.summary)
        year = int(entry.year)
        return (
            f'<aside class="note-comm-rabbinic">'
            f"<strong>{commentator}</strong> "
            f"<em>{work}</em> "
            f"<small>({year})</small>"
            f"<p>{summary}</p>"
            f"</aside>"
        )


# ----------------------------------------------------------------------
# Registry
# ----------------------------------------------------------------------

# Order matters: prospect.py runs in this order, and ties on (verse, kind)
# are broken by detector order.
ALL_DETECTORS = [
    HebrewWordDetector,
    GreekWordDetector,
    CrossRefDetector,
    NaveTopicalDetector,
    KenyonReferenceDetector,
    AIXrefDetector,
    AINoteDetector,
    PatristicCommentaryDetector,  # γ.3
    EthiopianCommentaryDetector,  # γ.4 — flagship payload
    ProtestantCommentaryDetector,  # χ.2 — Matthew Henry seed
    CatholicCommentaryDetector,  # χ.4 — Catena Aurea seed
    ReformationCommentaryDetector,  # χ.3 — Calvin seed
    RabbinicCommentaryDetector,  # χ.5 — Rashi seed (CLOSES χ.2-5 cluster)
]

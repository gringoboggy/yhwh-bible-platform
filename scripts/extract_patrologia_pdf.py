"""scripts/extract_patrologia_pdf.py — extract Ge'ez verse text from
Patrologia Orientalis bilingual critical-edition PDFs (PO 2/9/13/23).

τ.6.x.5.a (2026-05-20) — built per
``docs/superpowers/specs/2026-05-20-patrologia-ingest-design.md``.

INPUT
=====

The four PO volumes hold the Ge'ez (Ethiopic) text + French translation
of five canonical Tewahedo OT books that are NOT in the parallel-Bible
EOTC PDF's render path (or, in Esther's case, that the PO editor cleans
up to a higher tier):

    Job        — PO 2 fasc 5, Pereira 1907
    Esther     — PO 9 fasc 1, Pereira 1913
    Ezra+Neh   — PO 13 fasc 5, Pereira 1919
    Chronicles — PO 23 fasc 4, Grébaut 1932

The PO layout (verified by inspection 2026-05-20 on the Job volume):

- Single-column page.
- TOP ~60% of page: Ge'ez body text + small French chapter/verse
  banner like ``LE LIVRE DE JOB, I, 6-12`` at the top edge.
- BOTTOM ~30-40%: French translation of the same Ge'ez verses,
  with the editor's apparatus footnotes interleaved.
- Ge'ez verses are marked with Ethiopic numerals (``፩፪፫…``) in the
  margin, NOT inline. Tesseract's column-aware OCR loses the margin
  numerals so we rely on paragraph-mode parsing (`።`-split) + sequential
  renumbering against the KJV skeleton (per τ.7.x.a methodology in
  ``scripts.extract_parallel_pdf.renumber_against_floor``).

The French apparatus footnotes are NOT scripture — they're the editor's
manuscript-variant notes. They get extracted alongside the body as
``gloss`` text in the optional ``fra`` target, but they are NOT
verse-aligned and the spec D1 puts them out of scope for the first pass.

OUTPUT
======

Per-book Python modules in:
    content/translations/geez-tewahedo/<book>.py

Each module exposes:
    TRANSLATION = "geez-tewahedo"
    BOOK = "<book_code>"
    VERSES = [(chapter, verse, text), ...]
    SOURCE_QUALITY = "patrologia-printed-tier1"
    SOURCE_PROVENANCE = "patrologia-orientalis-<vol>-fasc-<f>-<editor>-<year>"
    EXTRACTION_DATE = "YYYY-MM-DD"

ENGINE
======

Only ``tesseract`` is supported (the PO PDFs have no text layer; the
embedded text is empty, as verified at ingest spec-design time). The
``script/Ethiopic`` language pack OCRs the body text; ``fra`` OCRs the
French translation/apparatus when ``--target fra`` is selected.

USAGE
=====

    # Ingest Job at default page range:
    python scripts/extract_patrologia_pdf.py --book job \\
        --pdf GAPS/6_Job/Job__PO-2-fasc-5_Pereira_1907.pdf \\
        --target geez --engine tesseract --language ethi

    # Diagnostic dry-run:
    python scripts/extract_patrologia_pdf.py --book job \\
        --pdf GAPS/6_Job/Job__PO-2-fasc-5_Pereira_1907.pdf \\
        --target geez --dry-run

    # Override page range:
    python scripts/extract_patrologia_pdf.py --book job \\
        --pdf <pdf> --target geez --page-start 584 --page-end 697

QUALITY POLICY
==============

Output is tagged ``SOURCE_QUALITY = "patrologia-printed-tier1"`` per
``scripts.core.provenance_tiers.TIERS``. Higher quality than ocr-tier3
because the PO editor has pre-done the philological collation work; our
OCR pass only has to recover the editor's printed Ge'ez (not a raw
manuscript hand).
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TRANSLATIONS_DIR = REPO / "content" / "translations"

# Bootstrap: when this script is invoked as ``python scripts/
# extract_patrologia_pdf.py …`` from the repo root, the repo isn't on
# sys.path so the ``from scripts.extract_parallel_pdf import …``
# imports below fail. Ensuring REPO is on sys.path is idempotent and
# safe when the script is invoked as ``python -m scripts.extract_
# patrologia_pdf`` (the repo is already on sys.path from the -m
# launcher).
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# τ.6.x.5.a — Tesseract engine constants. Mirrors
# scripts.extract_parallel_pdf for the GEEZ_LANG/AMH_LANG/OCR_DPI
# values (both scripts share the same rasterize-then-OCR pipeline).
OCR_DPI = 350
GEEZ_LANG = "script/Ethiopic"
FRA_LANG = "fra"
ENGINE_TESSERACT = "tesseract"
ENGINE_TEXT_LAYER = "text-layer"
ENGINE_CHOICES = (ENGINE_TESSERACT, ENGINE_TEXT_LAYER)
ENGINE_DEFAULT = ENGINE_TESSERACT

TARGET_GEEZ = "geez"
TARGET_FRA = "fra"
TARGET_CHOICES = (TARGET_GEEZ, TARGET_FRA)

# Source quality tier (registered in scripts.core.provenance_tiers.TIERS).
SOURCE_QUALITY = "patrologia-printed-tier1"

# PO layout split fractions. The Ge'ez body occupies the top of the
# page; the French translation + apparatus is at the bottom. The split
# is around 60/40 (verified on Job p585: top 60% = pure Ge'ez +
# top-strip French banner; bottom 40% = French translation).
GEEZ_TOP_FRACTION = 0.60
FRA_BOTTOM_FRACTION = 0.40

# Top-banner strip (chapter/verse heading like "LE LIVRE DE JOB, I, 6-12")
# — used to detect chapter boundaries when present.
BANNER_TOP_FRACTION = 0.06


# ───────────────────────────────────────────────────────────────────
# Per-book PO source metadata
# ───────────────────────────────────────────────────────────────────


class POSource:
    """Per-book PO source metadata (volume / fascicle / editor / year /
    archive.org URL / default PDF-page range / canonical book code).

    ``banner_top_fraction`` (added at τ.6.x.5.c): the vertical strip
    fraction used to OCR the chapter/verse banner. The PO 2/9 volumes
    fit cleanly in the default 0.06 (top 6% of page); the PO 13 volume
    (Ezra-Nehemiah) lays the banner a bit lower and needs ~0.10 to
    capture it. Per-source override avoids a global change that could
    regress Job/Esther.
    """

    def __init__(
        self,
        *,
        book: str,
        volume: int,
        fascicle: int,
        editor: str,
        year: int,
        archive_url: str,
        default_page_range: tuple[int, int],
        banner_top_fraction: float = BANNER_TOP_FRACTION,
    ) -> None:
        self.book = book
        self.volume = volume
        self.fascicle = fascicle
        self.editor = editor
        self.year = year
        self.archive_url = archive_url
        self.default_page_range = default_page_range
        self.banner_top_fraction = banner_top_fraction

    @property
    def provenance(self) -> str:
        """Canonical SOURCE_PROVENANCE string."""
        return f"patrologia-orientalis-vol{self.volume}-fasc{self.fascicle}-{self.editor.lower()}-{self.year}"

    @property
    def citation(self) -> str:
        """Human-readable PO citation (used in module docstring)."""
        return f"PO {self.volume} fasc {self.fascicle}, {self.editor} {self.year}"


# Registry of the 4 PO sources from the spec, keyed by the canonical
# book code. Page ranges are 0-indexed inclusive PDF pages.
PO_SOURCES: dict[str, POSource] = {
    "job": POSource(
        book="job",
        volume=2,
        fascicle=5,
        editor="Pereira",
        year=1907,
        archive_url="https://archive.org/details/patrologiaorient02pariuoft",
        # Verified by OCR-probe 2026-05-20: Job content starts at PDF
        # p584 (chapter I, verse 1 in Ge'ez) and ends at p697 (chapter
        # XLII, end). Page 698+ is the volume Table of Contents.
        default_page_range=(584, 697),
    ),
    "est": POSource(
        book="est",
        volume=9,
        fascicle=1,
        editor="Pereira",
        year=1913,
        archive_url="https://archive.org/details/patrologiaorient09pariuoft",
        # Calibrated by OCR-probe 2026-05-20 (τ.6.x.5.b): Esther body
        # starts at PDF p24 ("ዘአስ'ቱር" / chapter I, v1) and ends at p65
        # (chapter X / Greek Addition F tail). Pages 0-23 are the volume
        # frontmatter + French INTRODUCTION; pages 66+ are the next PO
        # work ("Acta Pilati"). The Esther body interleaves canonical
        # chapters I-X with the Greek Additions A-F (banners show e.g.
        # "III, 9 — B, 1" + "IV, 17 — C, 7" + "C, 29 — D, 6"); the
        # renumber-against-canonical step folds the extra Additions back
        # into the KJV 10-chapter / 167-verse skeleton.
        default_page_range=(24, 65),
    ),
    "ezr": POSource(
        book="ezr",
        volume=13,
        fascicle=5,
        editor="Pereira",
        year=1919,
        archive_url="https://archive.org/details/patrologiaorient13pariuoft",
        # Calibrated by OCR-probe 2026-05-20 (τ.6.x.5.c): the PO 13 fasc
        # 5 volume contains a SINGLE Ethiopian work titled "TROISIÈME
        # LIVRE DE 'EZRA / (ESDRAS ET NÉHÉMIE CANONIQUES)" — i.e. the
        # combined canonical Ezra + canonical Nehemiah folded into one
        # 23-chapter Ge'ez book per Ethiopian convention. Volume
        # chapters I-X correspond to canonical Ezra 1-10; volume
        # chapters XI-XXIII correspond to canonical Nehemiah 1-13.
        # The ingest splits the single volume into two output modules
        # by page-boundary:
        #   ezr ← pages 13-47 (volume ch I-X = canonical Ezra, 10ch)
        #   neh ← pages 48-97 (volume ch XI-XXIII = canonical Neh, 13ch)
        # Pages 0-12 are PO frontmatter (title, license, INTRODUCTION);
        # pages 98+ are the volume Table of Contents + advertising.
        # The Ezra→Nehemiah transition spans p47 (volume ch X tail +
        # ch XI 1-3); p47 is assigned to ezr (X is the larger share of
        # body text). The neh extract starts at p48; the ~3 lost neh
        # 1:1-3 verses on p47 are tolerated by the merge variant.
        default_page_range=(13, 47),
        # PO 13 layout sits the banner ~10% down (vs PO 2/9's 6%); see
        # POSource.banner_top_fraction docstring.
        banner_top_fraction=0.10,
    ),
    "neh": POSource(
        book="neh",
        volume=13,
        fascicle=5,
        editor="Pereira",
        year=1919,
        archive_url="https://archive.org/details/patrologiaorient13pariuoft",
        # Calibrated by OCR-probe 2026-05-20 (τ.6.x.5.c): pages 48-97
        # are the canonical-Nehemiah half of the PO 13 fasc 5 volume's
        # "TROISIÈME LIVRE DE 'EZRA" (volume chapters XI-XXIII =
        # canonical Nehemiah 1-13). See the ezr entry above for the
        # full volume layout + boundary rationale.
        default_page_range=(48, 97),
        banner_top_fraction=0.10,
    ),
    "1ch": POSource(
        book="1ch",
        volume=23,
        fascicle=4,
        editor="Grebaut",
        year=1932,
        archive_url="https://archive.org/details/patrologiaorient23pariuoft",
        # Calibrated by OCR-probe 2026-05-20 (τ.6.x.5.d): the PO 23 fasc
        # 4 volume contains a SINGLE Ethiopian "Paralipomènes I-II"
        # composite work split into LIVRE PREMIER (1 Chronicles) and
        # LIVRE SECOND (2 Chronicles) per Grébaut's bilingual edition.
        #   1ch ← PDF pages 542-647 (LIVRE PREMIER, ch I-XXIX = 29 ch)
        #   2ch ← PDF pages 648-776 (LIVRE SECOND, ch I-XXXVI = 36 ch)
        # Pages 0-541 are 4 OTHER PO 23 works (Severus Homilies in
        # Syriac, Heresies Compendium, Yahya-ibn-Sa'id History in Arabic
        # — none of them Ge'ez or canonical OT) + a 15-page Chronicles
        # INTRODUCTION (pp 522-541). Pages 777+ are the volume APPENDICE
        # (manuscript-margin titles) + the volume Table of Contents.
        # The 1ch→2ch transition is at p647→p648: p647 ends LIVRE
        # PREMIER ch XXIX (banner "VINGT-NEUVIEME"); p648 starts LIVRE
        # SECOND ch I (banner OCR'd as garbled "D"/"EE" — likely the
        # ornate chapter-heading hides a clean banner — but the body
        # OCR begins with "ጺንዐ ፡ ሰለሞን ፡ ወልደ ፡ ዳዊት" / "Strong was
        # Solomon son of David", the unambiguous 2 Chr 1:1 incipit).
        default_page_range=(542, 647),
        # PO 23 lays its banner ~10% down (vs PO 2/9's 6%); same as PO 13.
        banner_top_fraction=0.10,
    ),
    "2ch": POSource(
        book="2ch",
        volume=23,
        fascicle=4,
        editor="Grebaut",
        year=1932,
        archive_url="https://archive.org/details/patrologiaorient23pariuoft",
        # Calibrated by OCR-probe 2026-05-20 (τ.6.x.5.d): pages 648-776
        # are the canonical 2-Chronicles half of the PO 23 fasc 4 volume
        # (LIVRE SECOND, ch I-XXXVI = 36 ch). Last body page is p776
        # (CHAPITRE TRENTE-SIXIEME); p777 begins the APPENDICE
        # (manuscript-margin titles, not scripture). See the 1ch entry
        # above for the full volume layout + boundary rationale.
        default_page_range=(648, 776),
        banner_top_fraction=0.10,
    ),
}


# ───────────────────────────────────────────────────────────────────
# Page-layout helpers (TOP / BOTTOM split — PO-specific)
# ───────────────────────────────────────────────────────────────────


def _render_strip_to_png(
    pdf_page,
    strip: str,
    dpi: int,
    out_path: Path,
    *,
    geez_top_fraction: float = GEEZ_TOP_FRACTION,
    banner_top_fraction: float = BANNER_TOP_FRACTION,
) -> Path:
    """Render one horizontal strip of a PDF page to a PNG.

    ``strip`` is one of:
        - "geez"   → top ``geez_top_fraction`` of the page (the Ge'ez body).
        - "fra"    → remaining bottom of the page (French translation +
                     apparatus footnotes).
        - "banner" → top ``banner_top_fraction`` only (small French
                     chapter/verse banner — used for chapter detection).

    Returns ``out_path`` for chaining.
    """
    import fitz

    if strip not in ("geez", "fra", "banner"):
        raise ValueError(f"strip must be 'geez', 'fra', or 'banner'; got {strip!r}")

    rect = pdf_page.rect
    height = rect.height
    if strip == "banner":
        clip = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + height * banner_top_fraction)
    elif strip == "geez":
        # Skip the banner strip (it's French) and include the rest of
        # the top fraction as Ge'ez body. The boundary between Ge'ez
        # body and French translation is at ``geez_top_fraction``.
        clip = fitz.Rect(rect.x0, rect.y0 + height * banner_top_fraction, rect.x1, rect.y0 + height * geez_top_fraction)
    else:  # fra
        clip = fitz.Rect(rect.x0, rect.y0 + height * geez_top_fraction, rect.x1, rect.y1)

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = pdf_page.get_pixmap(matrix=matrix, clip=clip)
    pix.save(str(out_path))
    return out_path


def render_body_for_vision(
    pdf_page,
    out_path: Path,
    *,
    dpi: int = 230,
    geez_top_fraction: float = 0.45,
    banner_top_fraction: float = 0.0,
) -> Path:
    """Render the banner+Ge'ez-body region of a PO page to a PNG for an Opus
    VISION agent — EXCLUDING the apparatus band + the French translation (the
    bottom of the page).

    The D1b vision lane reads the printed Ge'ez body + recovers the source margin
    verse-numerals (and the interleaved LXX Addition letters), which the Tesseract
    OCR path loses. Unlike ``_render_strip_to_png(strip="geez")`` this KEEPS the
    top banner (the French chapter/verse cross-check) and the right margin (the
    verse numerals), and clips at ``geez_top_fraction`` of the page height
    (default 0.45 — banner + body + margins; the apparatus band starts below it,
    per the PO 9 Esther calibration 2026-05-28). ``dpi`` defaults to 230 so a
    full-width strip lands ~1518 px — under the 1568 px vision downsample cap, so
    no resolution is wasted. Pure render-to-PNG; no OCR.
    """
    import fitz

    rect = pdf_page.rect
    clip = fitz.Rect(
        rect.x0,
        rect.y0 + rect.height * banner_top_fraction,
        rect.x1,
        rect.y0 + rect.height * geez_top_fraction,
    )
    zoom = dpi / 72.0
    pix = pdf_page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip)
    pix.save(str(out_path))
    return out_path


def tesseract_extract_strips(
    pdf_page,
    binary: Path,
    *,
    dpi: int = OCR_DPI,
    geez_lang: str = GEEZ_LANG,
    fra_lang: str = FRA_LANG,
    targets: tuple[str, ...] = (TARGET_GEEZ, TARGET_FRA),
    tmp_dir: Path | None = None,
    banner_top_fraction: float = BANNER_TOP_FRACTION,
) -> dict[str, str]:
    """OCR each requested strip of a PDF page.

    Returns a dict keyed by target name:
        {
            "geez": <Ge'ez body OCR text>,
            "fra":  <French translation OCR text>,
            "banner": <French chapter/verse banner text>,
        }

    ``targets`` selects which strips to OCR. The ``banner`` strip is
    always extracted (it's small + tells us which chapter we're on) when
    "geez" is in targets.

    ``banner_top_fraction`` (added at τ.6.x.5.c) overrides the default
    banner strip thickness for sources that lay the banner lower than
    PO 2/9 (e.g. PO 13's ezr/neh need ~0.10).

    ``tmp_dir`` shares one ``tempfile.TemporaryDirectory`` across many
    pages instead of paying the create/teardown cost per page. When
    ``None``, a local TemporaryDirectory is created and torn down.
    """
    # Reuse the parallel-PDF extractor's _run_tesseract_on_png helper for
    # the actual subprocess invocation (W-W1-safe; stdin=DEVNULL).
    from scripts.extract_parallel_pdf import _run_tesseract_on_png

    if tmp_dir is None:
        with tempfile.TemporaryDirectory() as tmp:
            return tesseract_extract_strips(
                pdf_page,
                binary,
                dpi=dpi,
                geez_lang=geez_lang,
                fra_lang=fra_lang,
                targets=targets,
                tmp_dir=Path(tmp),
                banner_top_fraction=banner_top_fraction,
            )

    out: dict[str, str] = {}
    if TARGET_GEEZ in targets:
        geez_png = tmp_dir / "geez.png"
        _render_strip_to_png(pdf_page, "geez", dpi, geez_png, banner_top_fraction=banner_top_fraction)
        out[TARGET_GEEZ] = _run_tesseract_on_png(binary, geez_png, geez_lang)

        banner_png = tmp_dir / "banner.png"
        _render_strip_to_png(pdf_page, "banner", dpi, banner_png, banner_top_fraction=banner_top_fraction)
        out["banner"] = _run_tesseract_on_png(binary, banner_png, fra_lang)

    if TARGET_FRA in targets:
        fra_png = tmp_dir / "fra.png"
        _render_strip_to_png(pdf_page, "fra", dpi, fra_png, banner_top_fraction=banner_top_fraction)
        out[TARGET_FRA] = _run_tesseract_on_png(binary, fra_png, fra_lang)

    return out


# ───────────────────────────────────────────────────────────────────
# French banner → (chapter, verse-start, verse-end) parser
# ───────────────────────────────────────────────────────────────────


# PO chapter/verse banner shape: "LE LIVRE DE JOB, I, 6-12" or
# "LE LIVRE DE JOB, II, 4-9" or "LE LIVRE DE JOB, I, 22 — II, 5"
# (cross-chapter banner). Roman numerals + comma + verse range.
#
# τ.6.x.5.b extension: matches the apostrophe form
# ``LE LIVRE D'ESDRAS`` / ``LE LIVRE D'ESTHER`` and the accented form
# ``LE LIVRE DE NÉHÉMIE``. The ``D[E']?`` allows DE or D'; the
# ``[\s\.']*`` between the connector and the book name absorbs the
# apostrophe + optional whitespace; ``\w+`` is Unicode-aware under
# ``re.UNICODE`` (Python 3 default) so accented letters like É match.
#
# τ.6.x.5.c extension: also matches the PO 13 fasc 5 banner shape
# ``TROISIÈME (LIVRE) DE 'EZRA, I, 5-11`` — the Ezra-Nehemiah volume
# uses "TROISIÈME LIVRE DE" (no "LE" leader; the OCR puts parens around
# LIVRE and prepends an apostrophe before the book name). The leading
# ``(?:LE\s+|\w+\s+)?`` allows either "LE" or the ordinal qualifier
# (PREMIER/DEUXIÈME/TROISIÈME). The ``\(?LIVRE\)?`` accepts the OCR's
# parenthesized variant. The ``[\s'`'`]*`` between DE and the book name
# absorbs the apostrophe family.
BANNER_RE = re.compile(
    r"(?:LE\s+|\w+\s+)?\(?LIVRE\)?\s+D[E']?[\s\.'`‘’\(\)]*\w+[\.,]?\s*([IVXL]+)[\.,\s]+(\d+)",
    re.IGNORECASE | re.UNICODE,
)

# τ.6.x.5.d extension: PO 23 fasc 4 (Grébaut 1932, Chronicles) uses a
# DIFFERENT banner shape — no book name, and BOTH the volume-book
# ordinal AND the chapter ordinal are spelled out as French ordinal
# words (no Roman numerals):
#
#     LIVRE PREMIER, CHAPITRE PREMIER.
#     LIVRE PREMIER, CHAPITRE DEUXIÈME.
#     LIVRE PREMIER, CHAPITRE VINGT-NEUVIÈME.
#     LIVRE SECOND, CHAPITRE PREMIER.
#     LIVRE SECOND, CHAPITRE TRENTE-SIXIÈME.
#
# This pattern picks the word(s) AFTER "CHAPITRE" and feeds them to
# ``french_ordinal_to_int`` which knows the 1-36 ordinals. The "LIVRE
# PREMIER/SECOND" prefix only tells us which canonical book the page
# belongs to — and we already split the PDF page-range by book before
# this regex runs, so we don't need to capture that.
PO23_BANNER_RE = re.compile(
    # CHAPITRE — OCR mangles include CHÄPITRE / CHAPITKE / CHAP1TRE / CIIAPITRE.
    # Accept any leading C, optional H/I, ‘A’-‘Ä’, P, optional I/L/1, T, R/K,
    # optional E. The ordinal word allows digit-1 in place of letter-I so the
    # mangled "CINQU1EME" / "QUATR1EME" / "DEUX1EME" still match (we normalize
    # 1↔I in ``french_ordinal_to_int`` before dictionary lookup).
    r"C[HI]+[ÄA]P[IiLl1]?T[RKr][Ee]?\s+([A-ZÉÈÊÀÔÛŒ\-0-9]+(?:\s+ET\s+[A-ZÉÈÊÀÔÛŒ\-0-9]+)?(?:\s*[\-]\s*[A-ZÉÈÊÀÔÛŒ0-9]+)?)",
    re.IGNORECASE | re.UNICODE,
)

# Roman numeral table (Roman → int) for the PO banners.
ROMAN_NUMERALS = {
    "I": 1,
    "V": 5,
    "X": 10,
    "L": 50,
    "C": 100,
    "D": 500,
    "M": 1000,
}

# τ.6.x.5.d — French ordinal words (1-36) for the PO 23 Chronicles
# banner. Accents tolerant (DEUXIÈME / DEUXIEME) — the matcher first
# strips accents + uppercases before lookup.
FRENCH_ORDINALS: dict[str, int] = {
    "PREMIER": 1,
    "PREMIERE": 1,  # feminine form, just in case
    "DEUXIEME": 2,
    "TROISIEME": 3,
    "QUATRIEME": 4,
    "CINQUIEME": 5,
    "SIXIEME": 6,
    "SEPTIEME": 7,
    "HUITIEME": 8,
    "NEUVIEME": 9,
    "DIXIEME": 10,
    "ONZIEME": 11,
    "DOUZIEME": 12,
    "TREIZIEME": 13,
    "QUATORZIEME": 14,
    "QUINZIEME": 15,
    "SEIZIEME": 16,
    "DIX-SEPTIEME": 17,
    "DIX-HUITIEME": 18,
    "DIX-NEUVIEME": 19,
    "VINGTIEME": 20,
    "VINGT-ET-UNIEME": 21,
    "VINGT-DEUXIEME": 22,
    "VINGT-TROISIEME": 23,
    "VINGT-QUATRIEME": 24,
    "VINGT-CINQUIEME": 25,
    "VINGT-SIXIEME": 26,
    "VINGT-SEPTIEME": 27,
    "VINGT-HUITIEME": 28,
    "VINGT-NEUVIEME": 29,
    "TRENTIEME": 30,
    "TRENTE-ET-UNIEME": 31,
    "TRENTE-DEUXIEME": 32,
    "TRENTE-TROISIEME": 33,
    "TRENTE-QUATRIEME": 34,
    "TRENTE-CINQUIEME": 35,
    "TRENTE-SIXIEME": 36,
}


def _strip_accents_upper(s: str) -> str:
    """Normalize a French word: strip accents + uppercase. Used for
    FRENCH_ORDINALS lookup (tolerates DEUXIÈME / DEUXIEME / deuxième)."""
    import unicodedata

    nfkd = unicodedata.normalize("NFKD", s)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return no_accents.upper().strip()


def french_ordinal_to_int(word: str) -> int | None:
    """Convert a French ordinal word to int, e.g.:
        "PREMIER"        → 1
        "deuxième"       → 2
        "VINGT-NEUVIÈME" → 29
        "TRENTE-SIXIÈME" → 36
    Returns None on miss.

    Handles common OCR mangles:
        - missing trailing E (DEUXIEM, CINQUIEM)
        - digit-1 substituted for letter-I (CINQU1EME, QUATR1EME)
    """
    if not word:
        return None
    key = _strip_accents_upper(word)
    # OCR mangle: digit '1' sometimes substituted for letter 'I' mid-word
    # (CINQU1EME, QUATR1EME, DEUX1EME). Normalize before lookup.
    key_iletter = key.replace("1", "I")
    if key_iletter in FRENCH_ORDINALS:
        return FRENCH_ORDINALS[key_iletter]
    # OCR mangle: missing trailing E.
    if (key_iletter + "E") in FRENCH_ORDINALS:
        return FRENCH_ORDINALS[key_iletter + "E"]
    return None


def roman_to_int(s: str) -> int | None:
    """Convert a Roman numeral string (e.g. 'XLII') to int (42).
    Returns None on parse failure. Subtractive notation supported.
    """
    s = s.upper().strip()
    if not s:
        return None
    total = 0
    prev = 0
    for ch in reversed(s):
        if ch not in ROMAN_NUMERALS:
            return None
        val = ROMAN_NUMERALS[ch]
        if val < prev:
            total -= val
        else:
            total += val
            prev = val
    return total if total > 0 else None


def parse_banner_chapter(banner_text: str) -> int | None:
    """Extract the chapter number from a PO French banner string.

    Examples:
        "LE LIVRE DE JOB, I, 6-12"      → 1
        "LE LIVRE DE JOB, II, 4-9"      → 2
        "576 LE LIVRE DE JOB, I, 6-12." → 1
        "[15] LE LIVRE DE JOB, XLII, 1" → 42
        no banner / garbled OCR         → None

    τ.6.x.5.d — also handles the PO 23 ordinal-word format:
        "LIVRE PREMIER, CHAPITRE PREMIER."         → 1
        "LIVRE PREMIER, CHAPITRE VINGT-NEUVIÈME."  → 29
        "LIVRE SECOND, CHAPITRE TRENTE-SIXIÈME."   → 36
    """
    if not banner_text:
        return None
    # OCR sometimes mangles "LE LIVRE" to "LE LINRE" or "LE LIVRE-DE";
    # be liberal in the keyword match. Also allow Esther/Job/etc.
    m = BANNER_RE.search(banner_text)
    if m is None:
        # Looser fallback: any "LIVRE DE/D' <BOOK> ROMAN" sequence.
        # τ.6.x.5.b: accept D' (apostrophe) form for D'ESDRAS, D'ESTHER
        # + Unicode-aware \w to match NÉHÉMIE.
        # τ.6.x.5.c: accept the parenthesized OCR variant ``(LIVRE)``
        # used by the PO 13 fasc 5 ``TROISIÈME (LIVRE) DE 'EZRA`` banner
        # + the apostrophe family before the book name.
        m = re.search(
            r"\(?LI[NV]RE\)?\s*[\.\-,]?\s*D[E']?[\s\.'`‘’\(\)]*\w+[\.,]?\s*([IVXL]+)",
            banner_text,
            re.IGNORECASE | re.UNICODE,
        )
        if m is None:
            # τ.6.x.5.d — try the PO 23 ordinal-word banner shape
            # ``LIVRE PREMIER, CHAPITRE <ORDINAL_WORD>.``
            m23 = PO23_BANNER_RE.search(banner_text)
            if m23 is not None:
                word = m23.group(1).strip()
                got = french_ordinal_to_int(word)
                if got is not None:
                    return got
            return None
    roman = m.group(1)
    return roman_to_int(roman)


# ───────────────────────────────────────────────────────────────────
# Ge'ez body text → verse-list parser
# ───────────────────────────────────────────────────────────────────


def split_geez_body_into_fragments(text: str) -> list[str]:
    """Split a chunk of Ge'ez body text into verse-candidate fragments.

    The PO Ge'ez body uses ``።`` (Ethiopic full stop) AND ``፡`` (word
    separator that often doubles as verse boundary in PO printing) as
    sentence-terminators. We follow the τ.6.x.1.C paragraph-mode
    discipline: split by ``።`` to get candidate verses, drop empty/very-
    short fragments, drop the OCR ASCII noise that the French banner
    sometimes leaves at the top.

    Returns the list of non-empty fragments WITH the trailing ``።``
    preserved (downstream consumers expect verse-text to end in the
    Ethiopic terminator).
    """
    # Drop pure-ASCII lines (page headers, French banners that leaked
    # into the Ge'ez strip OCR — e.g. "576 LE LIVRE DE JOB, I, 6-12.").
    kept_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        has_ethiopic = any(0x1200 <= ord(c) <= 0x137F for c in line)
        if not has_ethiopic and re.search(r"[a-zA-Z]{4,}", line):
            continue
        kept_lines.append(line)

    if not kept_lines:
        return []

    flat = " ".join(kept_lines)
    # Collapse multiple whitespace into single space.
    flat = re.sub(r"\s+", " ", flat).strip()
    if not flat:
        return []

    fragments = flat.split("።")
    out: list[str] = []
    for frag in fragments:
        s = frag.strip().rstrip("=;|").rstrip()
        if not s:
            continue
        # Drop fragments that have no Ethiopic content (pure-numeral or
        # pure-punctuation OCR noise).
        if not any(0x1200 <= ord(c) <= 0x137F for c in s):
            continue
        # Drop fragments shorter than 10 chars — likely OCR noise.
        if len(s) < 10:
            continue
        out.append(s + "።")
    return out


def parse_patrologia_pages(
    page_strips: list[dict[str, str]],
) -> list[tuple[int, int, str]]:
    """Parse a list of per-page strip-OCR results into (ch, v, text)
    tuples.

    Strategy:
    1. Walk pages in order. For each page, look at the ``banner`` strip
       to detect the chapter number (Roman numeral in the French banner).
    2. Within each chapter, accumulate Ge'ez body fragments (split by
       ``።``). Number them sequentially starting from 1 in each chapter.
    3. Pages without a recognizable banner inherit the previous page's
       chapter.

    Returns:
        list of (chapter, verse, text) in source order. The chapter
        labels here are the PARSER'S BEST GUESS; downstream may
        renumber against a canonical floor (KJV skeleton).
    """
    out: list[tuple[int, int, str]] = []
    current_chapter = 0  # 0 = none seen yet; bumps to 1 at first banner
    verse_in_chapter = 0

    for _page_idx, strips in enumerate(page_strips):
        banner = strips.get("banner", "")
        body = strips.get(TARGET_GEEZ, "")

        detected = parse_banner_chapter(banner)
        if detected is not None and detected != current_chapter:
            current_chapter = detected
            verse_in_chapter = 0
        elif current_chapter == 0:
            # No banner detected on the FIRST page — default to ch 1.
            current_chapter = 1

        fragments = split_geez_body_into_fragments(body)
        for frag in fragments:
            verse_in_chapter += 1
            out.append((current_chapter, verse_in_chapter, frag))

    return out


# ───────────────────────────────────────────────────────────────────
# Renumber-against-canonical helper
# ───────────────────────────────────────────────────────────────────


def renumber_against_canonical(
    verses: list[tuple[int, int, str]],
    book: str,
) -> list[tuple[int, int, str]]:
    """Reassign chapter/verse labels by sequentially filling canonical
    chapters per the KJV skeleton.

    Wrapper around
    ``scripts.extract_parallel_pdf.renumber_against_floor`` that
    sources the per-chapter verse-count floor from
    ``scripts.core.canonical_verse_counts.canonical_book_shape``.
    """
    from scripts.core.canonical_verse_counts import canonical_book_shape
    from scripts.extract_parallel_pdf import renumber_against_floor

    floor = canonical_book_shape(book)
    return renumber_against_floor(verses, floor)


def renumber_against_canonical_with_merge(
    verses: list[tuple[int, int, str]],
    book: str,
) -> list[tuple[int, int, str]]:
    """Like ``renumber_against_canonical`` but PRE-MERGES adjacent
    fragments when the raw parser produced more fragments than the
    canonical total — fitting OCR output into the canonical shape by
    joining short Ge'ez sentences (the PO `።`-per-colometric-pause
    over-segmentation pattern documented at τ.7.x.v).

    Strategy:
        1. If raw fragment count <= canonical total: use the plain
           ``renumber_against_canonical`` (sparse output is fine).
        2. If raw fragment count > canonical total: distribute the
           fragments across canonical chapters proportionally. Each
           canonical chapter ``ch`` gets ``ratio * canonical_count(ch)``
           fragments where ``ratio = total_raw / total_canonical``.
           Within each chapter, the assigned fragments are then
           re-grouped into exactly ``canonical_count(ch)`` verses by
           concatenating adjacent fragments (the typical PO `።`-per-
           colometric pause means 2-3 adjacent fragments form one
           canonical verse).

    The chapter labels of the input ``verses`` are DISCARDED — only
    source order is preserved. This matches
    ``renumber_against_floor``'s contract.
    """
    from scripts.core.canonical_verse_counts import canonical_book_shape

    floor = canonical_book_shape(book)
    n_in = len(verses)
    n_floor = sum(floor.values())
    if n_in <= n_floor:
        return renumber_against_canonical(verses, book)

    # Over-segmentation path. Distribute proportionally.
    chapters = sorted(floor.keys())
    ratio = n_in / n_floor
    out: list[tuple[int, int, str]] = []
    cursor = 0
    for ch in chapters:
        target_verses = floor[ch]
        # Number of raw fragments allocated to this chapter.
        allocated = int(round(ratio * target_verses))
        if ch == chapters[-1]:
            # Last chapter: take whatever's left so we don't drop tails.
            allocated = n_in - cursor
        chapter_frags = [v[2] for v in verses[cursor : cursor + allocated]]
        cursor += allocated
        if not chapter_frags:
            continue
        # Merge chapter_frags down to exactly target_verses by joining
        # adjacent fragments. Compute group size = ceil(N / target).
        n_frags = len(chapter_frags)
        if n_frags <= target_verses:
            # Few fragments — produce sparse output for this chapter
            # (no merge needed).
            for i, frag in enumerate(chapter_frags, start=1):
                out.append((ch, i, frag))
            continue
        # group_size = how many fragments to merge into each canonical
        # verse. Use integer division + spread the remainder across
        # the first ``remainder`` verses (each gets +1 fragment).
        base_size = n_frags // target_verses
        remainder = n_frags - base_size * target_verses
        idx = 0
        for v in range(1, target_verses + 1):
            take = base_size + (1 if v <= remainder else 0)
            merged = " ".join(chapter_frags[idx : idx + take])
            idx += take
            out.append((ch, v, merged))
    return out


# ───────────────────────────────────────────────────────────────────
# Top-level extract + write
# ───────────────────────────────────────────────────────────────────


def _resolve_tesseract_or_exit() -> Path:
    """Resolve the Tesseract binary; SystemExit if not installed.

    Thin wrapper that delegates to the parallel-PDF extractor's
    resolver (same install-pointer message for both pipelines).
    """
    from scripts.extract_parallel_pdf import _resolve_tesseract_or_exit as _resolve

    return _resolve()


def _verify_tesseract_languages_or_exit(binary: Path, langs: tuple[str, ...]) -> None:
    """Pre-flight ``tesseract --list-langs`` for the requested language
    packs and SystemExit if any are missing.

    Reuses ``scripts.extract_parallel_pdf._check_tesseract_languages``
    (which handles Windows ``script\\X`` ↔ POSIX ``script/X``
    normalization + the W-W1-safe stdin=DEVNULL invocation).
    """
    from scripts.extract_parallel_pdf import _check_tesseract_languages

    missing = _check_tesseract_languages(binary, langs)
    if not missing:
        return
    raise SystemExit(
        "FATAL: --engine tesseract requires these language packs which "
        "are NOT present in this Tesseract install:\n"
        + "\n".join(f"  - {ln}" for ln in missing)
        + "\n\nInstall via the Tesseract installer's optional-languages "
        "step, or drop the corresponding .traineddata file into the "
        "tessdata directory of the install (typically "
        "``C:\\Program Files\\Tesseract-OCR\\tessdata\\``).\n"
        "Sources:\n"
        "  - https://github.com/tesseract-ocr/tessdata_fast\n"
        "  - https://github.com/tesseract-ocr/tessdata_best\n"
    )


def extract_patrologia(
    *,
    book: str,
    pdf_path: Path,
    targets: tuple[str, ...] = (TARGET_GEEZ,),
    engine: str = ENGINE_DEFAULT,
    page_start: int | None = None,
    page_end: int | None = None,
    dpi: int = OCR_DPI,
) -> tuple[list[tuple[int, int, str]], dict]:
    """OCR-extract a Patrologia Orientalis PDF for one book.

    Returns ``(verses, meta)`` where:
        - verses: list of (chapter, verse, text) tuples in source order,
          renumbered against the KJV skeleton via
          ``renumber_against_canonical``.
        - meta: dict with extraction metadata (pages processed, raw verse
          count before renumber, banner-detected chapter set, etc.).
    """
    if engine != ENGINE_TESSERACT:
        # The PO PDFs have no text layer. text-layer engine is a
        # placeholder for the CLI surface; it would produce empty output.
        raise SystemExit(
            f"FATAL: --engine {engine!r} is not supported for PO PDFs. "
            "The PO volumes have no embedded text layer; use "
            "--engine tesseract."
        )
    if book not in PO_SOURCES:
        raise SystemExit(f"FATAL: book {book!r} is not a known Patrologia source. Known: {sorted(PO_SOURCES.keys())}")
    if not pdf_path.is_file():
        raise SystemExit(f"FATAL: PDF not found at {pdf_path}")

    src = PO_SOURCES[book]
    p_start = page_start if page_start is not None else src.default_page_range[0]
    p_end = page_end if page_end is not None else src.default_page_range[1]
    if p_start <= 0 or p_end < p_start:
        raise SystemExit(
            f"FATAL: page range invalid for {book!r}: --page-start={p_start} "
            f"--page-end={p_end}. The PO_SOURCES default for {book!r} is "
            f"{src.default_page_range}; if it's (0, 0) the range hasn't "
            f"been calibrated yet and must be passed via CLI flags."
        )

    binary = _resolve_tesseract_or_exit()
    needed_langs: list[str] = []
    if TARGET_GEEZ in targets:
        needed_langs.append(GEEZ_LANG)
    if TARGET_FRA in targets or TARGET_GEEZ in targets:
        # The banner OCR needs `fra` too (top-strip chapter detection).
        needed_langs.append(FRA_LANG)
    _verify_tesseract_languages_or_exit(binary, tuple(set(needed_langs)))

    import fitz

    doc = fitz.open(str(pdf_path))
    try:
        if p_end >= len(doc):
            raise SystemExit(f"FATAL: page_end={p_end} beyond PDF length {len(doc)} for {pdf_path}")
        print(f"  source PDF: {pdf_path}")
        print(f"  book: {book}  ({src.citation})")
        print(f"  pages: {p_start}-{p_end} ({p_end - p_start + 1} pages)")
        print(f"  engine: {engine}  ocr_dpi: {dpi}")
        print(f"  targets: {targets}")
        print(f"  tesseract: {binary}")

        all_strips: list[dict[str, str]] = []
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            n_pages = p_end - p_start + 1
            for i, scan_page in enumerate(range(p_start, p_end + 1)):
                page = doc[scan_page]
                strips = tesseract_extract_strips(
                    page,
                    binary,
                    dpi=dpi,
                    targets=targets,
                    tmp_dir=tmp_dir,
                    banner_top_fraction=src.banner_top_fraction,
                )
                all_strips.append(strips)
                if i % 10 == 0 or i == n_pages - 1:
                    print(f"  [{i + 1}/{n_pages}] page {scan_page}")
    finally:
        doc.close()

    raw_verses = parse_patrologia_pages(all_strips)
    banner_chapters = sorted({c for (c, _, _) in raw_verses})
    print(
        f"  banner-detected chapters: {len(banner_chapters)} ({banner_chapters[:10]}{'...' if len(banner_chapters) > 10 else ''})"
    )
    print(f"  raw verses parsed: {len(raw_verses)}")

    # Renumber against the canonical KJV skeleton. The Ge'ez `።` full-
    # stop punctuates more granularly than verse boundaries (PO Pereira's
    # print includes mid-verse colometric pauses ≈ 2.5x oversplit vs
    # canonical verse count). Use ``renumber_against_canonical_with_
    # merge`` which proactively merges adjacent fragments to fit the
    # canonical chapter shape, avoiding the τ.7.x.v gross-over-
    # segmentation hard-fail. Sparse output (fewer raw fragments than
    # canonical total) still works — the merge variant falls back to
    # plain renumber in that case.
    renumber_succeeded = False
    renumber_merge_applied = False
    if TARGET_GEEZ in targets:
        n_raw = len(raw_verses)
        from scripts.core.canonical_verse_counts import canonical_total

        n_floor = canonical_total(book)
        try:
            if n_raw <= n_floor:
                verses = renumber_against_canonical(raw_verses, book)
            else:
                verses = renumber_against_canonical_with_merge(raw_verses, book)
                renumber_merge_applied = True
            renumber_succeeded = True
        except ValueError as exc:
            msg = str(exc)[:140]
            print(f"  renumber FAILED: {msg}...")
            print("  falling back to banner-anchored chapter labels + sentence-level verse numbering.")
            verses = raw_verses
    else:
        verses = raw_verses

    meta = {
        "pages_start": p_start,
        "pages_end": p_end,
        "raw_verse_count": len(raw_verses),
        "renumbered_verse_count": len(verses),
        "banner_detected_chapters": banner_chapters,
        "renumber_succeeded": renumber_succeeded,
        "renumber_merge_applied": renumber_merge_applied,
    }
    return verses, meta


def write_book_module_patrologia(
    *,
    book: str,
    verses: list[tuple[int, int, str]],
    ingest_phase: str = "τ.6.x.5.a",
    extraction_date: str | None = None,
    meta: dict | None = None,
) -> Path:
    """Write ``content/translations/geez-tewahedo/<book>.py`` with the
    PO ingest's verse data + provenance metadata.

    Mirrors ``scripts.extract_parallel_pdf.write_book_module`` but:
        - Sets ``SOURCE_QUALITY = "patrologia-printed-tier1"``.
        - Sets ``SOURCE_PROVENANCE`` from the PO_SOURCES registry
          (volume / fascicle / editor / year).
        - References the PO archive.org URL in the docstring (the
          honesty contract for the public-domain attribution).
    """
    from scripts.extract_parallel_pdf import write_book_module

    if book not in PO_SOURCES:
        raise SystemExit(f"FATAL: book {book!r} not in PO_SOURCES")
    src = PO_SOURCES[book]
    ext_date = extraction_date or date.today().isoformat()

    doc_extra_lines = [
        f"Source: {src.citation}",
        f"Archive: {src.archive_url}",
        f"Editor: {src.editor} ({src.year}); public-domain bilingual critical edition.",
    ]
    if meta:
        doc_extra_lines.extend(
            [
                "",
                f"PDF pages: {meta.get('pages_start')}-{meta.get('pages_end')}.",
                f"Raw OCR verse count: {meta.get('raw_verse_count')}.",
                f"Renumbered verse count: {meta.get('renumbered_verse_count')}.",
            ]
        )
        if meta.get("renumber_succeeded"):
            if meta.get("renumber_merge_applied"):
                doc_extra_lines.append(
                    "Renumbering: COLOMETRIC-MERGE variant of the sequential "
                    f"KJV-skeleton renumber for {book!r}. Raw OCR fragment "
                    "count exceeded the canonical verse total (PO Pereira's "
                    "Ge'ez print uses 2-3 `።` colometric pauses per verse, "
                    "vs the parallel-Bible-EOTC's 1-2). Adjacent fragments "
                    "were merged proportionally per chapter so the output "
                    "fits the canonical chapter shape. Per-verse text spans "
                    "multiple printed `።` pauses joined by spaces. "
                    "τ.6.x.5.b detail-wave can refine the merge boundaries "
                    "using the editor's French translation as a guide."
                )
            else:
                doc_extra_lines.append(
                    "Renumbering: sequentially against the KJV canonical "
                    f"skeleton for {book!r} (see scripts.core.canonical_verse_counts)."
                )
        else:
            doc_extra_lines.append(
                "Renumbering: ATTEMPTED + FELL BACK. The KJV canonical-floor "
                "renumber raised the τ.7.x.v gross-over-segmentation guard. "
                "Output below uses banner-anchored chapter labels + sentence-"
                "level verse numbering — neither chapter nor verse labels "
                "match canonical Job; this is raw OCR. τ.6.x.5.b detail-wave "
                "will refine."
            )
        if meta.get("banner_detected_chapters"):
            chapters = meta["banner_detected_chapters"]
            doc_extra_lines.append(f"Banner-detected chapters ({len(chapters)}): {chapters}.")

    return write_book_module(
        translation="geez-tewahedo",
        book=book,
        verses=verses,
        source_quality=SOURCE_QUALITY,
        extraction_date=ext_date,
        ingest_phase=ingest_phase,
        docstring_extra="\n".join(doc_extra_lines),
        source_provenance=src.provenance,
        source_yaml_ref=src.archive_url,
        tool="scripts/extract_patrologia_pdf.py",
    )


# ───────────────────────────────────────────────────────────────────
# CLI
# ───────────────────────────────────────────────────────────────────


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Extract Ge'ez verse text from Patrologia Orientalis "
        "bilingual critical-edition PDFs (PO 2/9/13/23). τ.6.x.5.a — see "
        "docs/superpowers/specs/2026-05-20-patrologia-ingest-design.md."
    )
    p.add_argument(
        "--book",
        required=True,
        choices=sorted(PO_SOURCES.keys()),
        help="canonical book code (job, est, ezr, neh, 1ch, 2ch)",
    )
    p.add_argument(
        "--pdf",
        required=True,
        help="path to the PO PDF file (absolute or relative to repo root)",
    )
    p.add_argument(
        "--target",
        default=TARGET_GEEZ,
        choices=list(TARGET_CHOICES),
        help="extract Ge'ez body (default) or the French translation",
    )
    p.add_argument(
        "--engine",
        default=ENGINE_DEFAULT,
        choices=list(ENGINE_CHOICES),
        help=(
            "OCR engine. 'tesseract' (default) renders each PDF page "
            "strip to PNG at 350 dpi and OCRs with the appropriate "
            "language pack. 'text-layer' is a placeholder; PO PDFs "
            "have no text layer so it errors out."
        ),
    )
    p.add_argument(
        "--language",
        default=None,
        help=(
            "Tesseract language pack. Default derived from --target: "
            "'ethi' (alias for script/Ethiopic) for --target geez; "
            "'fra' for --target fra. Pass through unchanged otherwise."
        ),
    )
    p.add_argument(
        "--page-start",
        type=int,
        default=None,
        help="override start PDF page (0-indexed, inclusive)",
    )
    p.add_argument(
        "--page-end",
        type=int,
        default=None,
        help="override end PDF page (0-indexed, inclusive)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="extract + report; do not write the output module",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite the output module if it already exists",
    )
    p.add_argument(
        "--ingest-phase",
        default="τ.6.x.5.a",
        help="phase tag recorded in the output module (default τ.6.x.5.a)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_argparser()
    args = p.parse_args(argv)

    # Resolve the --language alias.
    # The spec asks for `--language ethi` and `--language fra`. The
    # underlying Tesseract pack for Ge'ez is `script/Ethiopic`, so
    # 'ethi' is an alias the CLI accepts to keep the surface short.
    requested_lang = args.language
    if requested_lang is None:
        requested_lang = "ethi" if args.target == TARGET_GEEZ else FRA_LANG
    # Normalize 'ethi' alias to the actual Tesseract pack name.
    if requested_lang.lower() in ("ethi", "ethiopic", "geez", "ge'ez"):
        # GEEZ_LANG is used internally as `script/Ethiopic`.
        pass  # No change to args; we already drive GEEZ_LANG through internals.
    elif requested_lang.lower() not in (FRA_LANG, GEEZ_LANG):
        print(
            f"warning: --language {requested_lang!r} is unusual for a PO PDF; expected 'ethi' or 'fra'.",
            file=sys.stderr,
        )

    pdf_path = Path(args.pdf)
    if not pdf_path.is_absolute():
        pdf_path = REPO / pdf_path
    pdf_path = pdf_path.resolve()

    targets: tuple[str, ...] = (args.target,)

    print(f"extract_patrologia_pdf — book={args.book!r} target={args.target!r}")
    verses, meta = extract_patrologia(
        book=args.book,
        pdf_path=pdf_path,
        targets=targets,
        engine=args.engine,
        page_start=args.page_start,
        page_end=args.page_end,
    )

    print()
    print("=" * 72)
    print("EXTRACTION RESULTS")
    print("=" * 72)
    print(f"  book: {args.book}")
    print(f"  verses: {len(verses)}")
    if verses:
        from collections import Counter

        counts = Counter(c for (c, _, _) in verses)
        chapters_with_verses = sorted(counts.keys())
        print(f"  chapters covered: {len(chapters_with_verses)} ({chapters_with_verses[:10]}...)")
        for ch, v, txt in verses[:3]:
            print(f"  {ch}:{v}  {txt[:70]}")
        if len(verses) > 3:
            print(f"  ... +{len(verses) - 3} more")

    if args.dry_run:
        print()
        print("  --dry-run: skipping write.")
        return 0

    out_path = TRANSLATIONS_DIR / "geez-tewahedo" / f"{args.book}.py"
    if out_path.exists() and not args.overwrite:
        print(f"  SKIP (exists; use --overwrite to replace): {out_path}")
        return 0

    written = write_book_module_patrologia(
        book=args.book,
        verses=verses,
        ingest_phase=args.ingest_phase,
        meta=meta,
    )
    print(f"  wrote {written}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

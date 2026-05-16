"""scripts/extract_parallel_pdf.py — extract Geʽez + Amharic verse
text from the parallel-Bible EOTC PDF.

τ.6.x.0a (2026-05-14) — built after the τ.6.x.0 pivot finding that
eBible.org's gez-Geez slot is no longer available; the parallel-
Bible PDF (`Bible_Amharic_and_Geez.pdf`, 2,539 pages) is the
PRIMARY Geʽez + Amharic source.

Π.1 (2026-05-14) — extended for the 6 Tewahedo-distinctive books.
`_source.yaml::structural_map` gains `jubilees` (jub), `one_enoch`
(1en), and `laodiceans` (lao) sections alongside the original
`meqabyan` section. The `meqabyan.subsections` map is hoisted from
this file's heuristic dict into declarative YAML. The `laodiceans`
slot is declared with `present_in_pdf: false` and triggers a clean
SystemExit when extraction is attempted (operator must supply an
alternate source). `tewahedo_distinctive_inventory` is added as a
metadata sibling of the real sections — filtered out by
`_extraction_sections()` so it does not appear in `--list-sections`
output or pilot-book resolution.

τ.6.x.1 (2026-05-14) — Tesseract OCR engine wired in. The tool now
supports two extraction engines:

- ``--engine tesseract`` (default per τ.6.x.0b Option-D-Hybrid
  authorization): each PDF page is rendered to a PNG at 350 dpi via
  pymupdf, then Tesseract is invoked once per column with the
  language pack appropriate to that column — ``script/Ethiopic``
  for the Geʽez left column (Tewahedo's upstream-blessed Ethiopic-
  script recognizer adopted at τ.6.x.0c) and ``amh`` for the
  Amharic right column. The Tesseract binary is resolved through
  ``scripts.core.paths.tesseract_binary()`` (PATH → known platform
  install paths → ``TESSERACT_BIN`` env-override). Required
  languages are pre-flight-checked via ``tesseract --list-langs``;
  missing languages cause an early clean SystemExit before any
  PDF page is opened.

- ``--engine text-layer`` (legacy fallback, τ.6.x.0a-original
  behavior): the PDF's embedded OCR text layer is consumed
  directly. This is faster but emits the "garbage Geʽez" the
  publisher's OCR pipeline produced; retained for diagnostic
  comparison and for cases where Tesseract is unavailable.

Both engines feed the same ``parse_verses_from_text()`` /
``write_book_module()`` downstream pipeline; the SOURCE_QUALITY tag
remains ``ocr-tier3`` for either engine until operator cross-check
upgrades a book to ``ocr-tier2`` per the τ.6.x.0b honesty contract.

τ.6.x.1 is wiring-only — no actual bulk-ingest runs at this phase.
The ``geez-tewahedo`` and ``amharic-tewahedo`` translation slots
REMAIN at their Π.0 seed state (3 verses Genesis only). Bulk-ingest
of the 66 standard-canon books unblocks at τ.6.x.2+ after publisher
direction on cadence, target-tier ramp, and per-book audit plan.

INPUTS
======

Source PDF: resolved through `content/translations/sources/
parallel-bible-eotc/_source.yaml::resolution_paths` (env-var,
publisher-supplied path, in-repo location — in priority order).

Structural map: declared in the same _source.yaml; the extractor
reads `structural_map.<book_section>.scan_page_range` to know
which page range corresponds to which book(s) and the
`pdf_index_offset` to convert scan-pages to PDF page indices.

OUTPUTS
=======

Per-book Python modules in:
    content/translations/geez-tewahedo/<book>.py
    content/translations/amharic-tewahedo/<book>.py

Each module exposes:
    TRANSLATION = "geez-tewahedo" | "amharic-tewahedo"
    BOOK = "<book_code>"
    VERSES = [(chapter, verse, text), ...]
    SOURCE_QUALITY = "ocr-tier3" | "ocr-tier2" | "page-image-tier1"

The SOURCE_QUALITY tag flows downstream so verse-popups + audits
can flag the provenance to readers.

EXTRACTION MODE
===============

The tool offers two engines, selected via ``--engine``:

1. ``tesseract`` (default, τ.6.x.1+): each PDF column is rendered to
   a 350-dpi PNG and OCR'd by Tesseract using ``script/Ethiopic``
   for the Geʽez column and ``amh`` for the Amharic column. This is
   the project's authorized path per the τ.6.x.0b Option-D-Hybrid
   strategy + τ.6.x.0c ``script/Ethiopic`` adoption.

2. ``text-layer`` (legacy fallback): reads the PDF's embedded OCR
   text layer directly. Per the Phase-4 methodology in
   ``project_maccabees_expansion/02_METHODOLOGY.md §2``, that text
   layer is GARBLED for Geʽez (e.g. clean ወገብረ → garbage like
   ወንዳረ ቘልፌኤቱ). Retained for diagnostic comparison and for
   environments where Tesseract is not installed.

Either way:

- For NON-Meqabyan books, extracted text is tagged ``SOURCE_QUALITY =
  "ocr-tier3"`` — the per-entry reader-facing caveat
  ("OCR-derived; awaiting operator cross-check") is preserved
  alongside the text so readers know to expect OCR errors in Geʽez
  until later passes upgrade the data. Operator cross-check upgrades
  a book to ``ocr-tier2``.
- For Meqabyan (the highest-priority book per
  project_maccabees_expansion/), this tool is NOT the long-term
  source — Phase 4 (δ.1.x) will produce page-image-tier1 text via
  the careful per-chapter methodology. This tool's Meqabyan output
  is ``ocr-tier3`` and explicitly REPLACEABLE by δ.1.x output.

USAGE
=====

    # Pilot mode (extract a small specific range, useful for testing):
    python scripts/extract_parallel_pdf.py --pilot mq1-ch1

    # Book-section mode (extract by structural_map key):
    python scripts/extract_parallel_pdf.py --section meqabyan

    # Diagnostic mode (do not write; just report):
    python scripts/extract_parallel_pdf.py --section meqabyan --dry-run

    # Force-fresh extraction (re-run even if files exist):
    python scripts/extract_parallel_pdf.py --section meqabyan --overwrite

QUALITY POLICY
==============

Every per-book .py the tool writes carries:
    SOURCE_QUALITY = "ocr-tier3"
    SOURCE_PROVENANCE = "parallel-bible-eotc"
    EXTRACTION_DATE = "YYYY-MM-DD"

These flow downstream into:
- The translation-popup display (the verse-popup widget can show
  a "OCR-flagged" indicator when SOURCE_QUALITY is tier-3).
- The audit tools (`scripts/lint_rules.py` can add a rule
  requiring tier-3 entries to be flagged in production EPUB
  delivery via the popup_languages config).
- The δ.1.x divergence-apparatus tool (compares OCR-tier-3 text
  against Phase-4 page-image-tier-1 text and produces divergence
  notes).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
import yaml
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc"
TRANSLATIONS_DIR = REPO / "content" / "translations"

# τ.6.x.1 — Tesseract engine constants. The 350-dpi render rate
# matches the project_maccabees_expansion/02_METHODOLOGY.md §2
# Phase-4 page-image cadence; higher dpi has diminishing OCR-accuracy
# returns and inflates temp-PNG size. The language pair below is the
# τ.6.x.0c-authorized invocation (`-l script/Ethiopic+amh` per the
# SCOPE doc §7.5) split into per-column invocations because the two
# columns are recognized SEPARATELY (left=Geʽez fidel, right=Amharic
# fidel) for cleaner verse-keyed output.
OCR_DPI = 350
GEEZ_LANG = "script/Ethiopic"
AMH_LANG = "amh"
ENGINE_TESSERACT = "tesseract"
ENGINE_TEXT_LAYER = "text-layer"
ENGINE_CHOICES = (ENGINE_TESSERACT, ENGINE_TEXT_LAYER)
ENGINE_DEFAULT = ENGINE_TESSERACT


# ───────────────────────────────────────────────────────────────────
# Source resolution
# ───────────────────────────────────────────────────────────────────


def load_source_config() -> dict:
    """Load `_source.yaml` describing the parallel-Bible PDF source."""
    path = SOURCE_DIR / "_source.yaml"
    if not path.is_file():
        raise SystemExit(f"FATAL: missing source config at {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def resolve_pdf_path(cfg: dict) -> Path:
    """Iterate the cfg's resolution_paths in order, returning the
    first one that exists. Raises SystemExit if none resolve."""
    paths = cfg.get("resolution_paths") or []
    if not paths:
        raise SystemExit("FATAL: no resolution_paths configured in _source.yaml")

    for raw in paths:
        # Substitute env vars (${VAR}); also handle ~ expansion.
        expanded = os.path.expandvars(os.path.expanduser(raw))
        if not expanded or "${" in expanded:
            continue  # env var unset
        p = Path(expanded)
        if not p.is_absolute():
            p = REPO / p
        if p.is_file():
            return p.resolve()

    msg = [
        "FATAL: parallel-Bible PDF not found at any of the configured paths.",
        "",
        "Tried (in order):",
    ]
    for raw in paths:
        expanded = os.path.expandvars(os.path.expanduser(raw))
        msg.append(f"  - {raw!r}  →  {expanded!r}")
    msg.append("")
    msg.append("Options to resolve:")
    msg.append("  1. Set PARALLEL_BIBLE_PDF env var to the absolute path.")
    msg.append("  2. Place the PDF at one of the resolution_paths.")
    msg.append("  3. Edit content/translations/sources/parallel-bible-eotc/_source.yaml to add a new resolution path.")
    raise SystemExit("\n".join(msg))


# ───────────────────────────────────────────────────────────────────
# PDF page → verse extraction
# ───────────────────────────────────────────────────────────────────

# Geʽez numeral table — chars used for chapter/verse numbering.
# U+1369-U+137C maps numeric values 1-10000.
GEEZ_NUMERAL_TO_INT = {
    "፩": 1,
    "፪": 2,
    "፫": 3,
    "፬": 4,
    "፭": 5,
    "፮": 6,
    "፯": 7,
    "፰": 8,
    "፱": 9,
    "፲": 10,
    "፳": 20,
    "፴": 30,
    "፵": 40,
    "፶": 50,
    "፷": 60,
    "፸": 70,
    "፹": 80,
    "፺": 90,
    "፻": 100,
    "፼": 10000,
}


def geez_numeral_to_int(s: str) -> int | None:
    """Convert a Geʽez numeral string (e.g. '፴፮') to int (36).
    Returns None on parse failure. Compounds are additive."""
    s = s.strip()
    if not s:
        return None
    total = 0
    for ch in s:
        if ch not in GEEZ_NUMERAL_TO_INT:
            return None
        total += GEEZ_NUMERAL_TO_INT[ch]
    return total


# Regex: match a verse-number marker (Arabic digits, possibly with
# trailing punctuation like ., :, ).
VERSE_NUM_RE = re.compile(r"^\s*(\d+)[.:\)\s]")

# Regex: match a chapter header. The parallel PDF uses ምዕራፍ + Geʽez
# numeral. τ.6.x.1.B extension: also tolerate Ethiopic word-space `፡`
# (U+1361) and Ethiopic comma `፣` (U+1363) as separators between the
# `ምዕራፍ` keyword and the chapter numeral — Tesseract OCR routinely
# emits these as separators in the parallel-Bible PDF where the
# text-layer engine sees only ASCII whitespace.
CHAPTER_HEADER_RE = re.compile(r"ምዕራፍ[\s፡፣]*([፩-፼]+)")


# τ.6.x.1.D — Chapter-marker recovery for OCR-garbled numerals.
#
# The τ.6.x.1.C known residual: when OCR garbles the chapter numeral
# (e.g. text-layer emits `ምዕራፍ B ።` for what should be `ምዕራፍ ፩ ።`;
# Tesseract emits `ምዕራፍ ል፳።`), the strict CHAPTER_HEADER_RE above
# doesn't match because the captured group requires `[፩-፼]+`. The
# chapter marker is silently missed and all verses in subsequent
# chapters get attributed to the previous chapter — for Genesis
# paragraph-mode ingest, this collapses all 50 chapters into chapter 1.
#
# The fix: a LENIENT regex that matches `ምዕራፍ` + separators + ANY
# short non-whitespace token + the closing Ethiopic-punct terminator.
# The captured token is then passed to `_resolve_chapter_marker()`
# which tries (1) clean Geʽez-numeral parsing, (2) Arabic-digit
# extraction, then (3) sequential fallback (current_chapter + 1).
# Sequential fallback assumes chapters are encountered in order —
# always true for sequential PDF page reading.
#
# Why a SEPARATE regex (vs replacing CHAPTER_HEADER_RE):
# - The strict regex is correct for Tewahedo-distinctive sections
#   (Meqabyan/Jubilees/1 Enoch) where Tesseract recognizes the
#   Ethiopic numerals cleanly. Loosening that path would risk
#   false-positives (e.g. matching cross-references shaped like
#   `ምዕራፍ <something>`).
# - The lenient regex is only used in paragraph_mode (τ.6.x.1.C)
#   for standard-canon books where OCR garbles the numerals.

CHAPTER_HEADER_RE_LENIENT = re.compile(
    r"ም[ዕፅ]ራፍ"  # keyword with ዕ-or-ፅ tolerance (text-layer engine
    # occasionally emits ፅ for ዕ — both are Ethiopic
    # syllabic glyphs with similar shape)
    r"[\s፡፣]+"  # at least one separator
    r"(\S{1,5})"  # 1-5 non-whitespace chars (numeral token, possibly garbled)
    r"\s*"
    r"[።፡፣=!|]"  # MUST be followed by Ethiopic punctuation OR `=`/`!`/`|`
    # (OCR substitutes `=` for `።` at chapter-marker ends — confirmed
    # on Genesis 1 p5; the text-layer engine ALSO emits `!` and `|`
    # for `።` — the real Matthew-1 marker `ምዕራፍ 8 !` was silently
    # dropped pre-τ.6.x.1.E, which discarded Mt 1-2 as pre-marker
    # noise and was the true cause of the τ.7.x.v "NT-overflow")
)


def _resolve_chapter_marker(numeral_token: str, current_chapter: int, *, max_jump: int = 5) -> int:
    """Resolve a chapter-marker numeral token to an integer chapter
    number, tolerating OCR garbling per τ.6.x.1.D.

    Strategy (in priority order):
    1. Clean Geʽez numeral — `geez_numeral_to_int()` returns int.
    2. Arabic-digit extraction — strip non-digits, parse remaining as
       int (covers OCR mistakes that drop in a digit like '፬' → '4').
    3. Sequential fallback — return current_chapter + 1, assuming
       chapters are encountered in order during sequential PDF reading.

    Sanity-check: parsed values that JUMP more than `max_jump` chapters
    forward of the current chapter are treated as OCR-garbled (Ethiopic
    numerals are visually similar — `፬` (4) vs `፱` (9) confusion is
    plausible). Sequential fallback fires for big jumps. The default
    `max_jump=5` is a heuristic — chapters are encountered in order in
    sequential PDF reading, so a jump of more than 5 is unlikely
    legitimate. Set max_jump=None to disable the check (use only when
    chapter-marker fidelity is verified upstream).

    Returns an int chapter number in [1, 200]. The 200 upper bound is
    a sanity-check guard against runaway values (Genesis has 50,
    Psalms has 150 — 200 leaves headroom for any biblical book).
    """
    if numeral_token:
        # Strategy 1: clean Geʽez numeral
        n = geez_numeral_to_int(numeral_token)
        if n is not None and 1 <= n <= 200:
            if max_jump is None or current_chapter == 0 or n <= current_chapter + max_jump:
                return n
            # Big jump — likely OCR garble; fall through to sequential.
        # Strategy 2: Arabic digits embedded in the token
        digits = "".join(c for c in numeral_token if c.isdigit())
        if digits:
            try:
                n = int(digits)
                if 1 <= n <= 200:
                    if max_jump is None or current_chapter == 0 or n <= current_chapter + max_jump:
                        return n
                    # Big jump — fall through to sequential.
            except ValueError:
                pass
    # Strategy 3: sequential fallback
    return current_chapter + 1


# τ.6.x.1.B — Ethiopic-numeral verse-marker normalization.
#
# The τ.6.x.1.A pilot empirical finding: the parallel-Bible PDF's
# verse markers in Tesseract OCR output are ETHIOPIC NUMERALS
# (e.g. `፪፤ ስመ ...` = "verse 2: name ..."), not Arabic digits. The
# existing `VERSE_NUM_RE` keys off `\d+` which under Python's default
# Unicode-decimal semantics matches the `Nd` (Decimal_Number) category
# only; Ethiopic numerals are categorized as `No` (Other Number) and
# therefore do NOT match `\d+`. Without normalization, τ.6.x.2.x bulk-
# ingest would produce ZERO verses from valid OCR output.
#
# The fix: pre-process the OCR text line-by-line. Where a line begins
# with one-or-more Ethiopic numerals followed by an Ethiopic punctuation
# mark (the verse-number/text separator in the PDF's layout), replace
# the Ethiopic numeral with its Arabic equivalent + an ASCII colon.
# The downstream `parse_verses_from_text()` then keys off the Arabic
# digits via the existing `VERSE_NUM_RE` regex unchanged.
#
# Why this approach (vs extending VERSE_NUM_RE itself):
# - Single-responsibility: the normalizer handles numeral systems;
#   the parser handles verse-line structure. Each function stays
#   simple.
# - Backward-compatible: text-layer-engine output (which contains
#   Arabic digits, not Ethiopic numerals) passes through unchanged.
# - Round-trippable: the helper is a pure-function transform on
#   strings, easy to test in isolation.
#
# Ethiopic punctuation set: ።፣፤፥፦፧፨ (Ethiopic full stop, comma,
# semicolon, preface colon, colon, question mark, paragraph
# separator — Unicode U+1361 through U+1368).

ETHIOPIC_PUNCT = "።፣፤፥፦፧፨"
ETHIOPIC_LINE_START_NUMERAL_RE = re.compile(r"^(\s*)([፩-፼]+)\s*([" + ETHIOPIC_PUNCT + r"])")


# τ.6.x.1.C — Paragraph-mode parser extension.
#
# The τ.7.x.a.0 PILOT empirical finding: standard-canon books (Genesis,
# Exodus, etc.) in the parallel-Bible PDF use PARAGRAPH-FLOWING verse
# layout — verses are NOT prefixed by leading verse numbers (Arabic or
# Ethiopic). Instead, verses are sentences terminated by `።` (Ethiopic
# full stop, U+1362). Tesseract OCR output preserves `።` boundaries
# cleanly; cross-references between verses appear as additional
# fragments after `።` containing biblical-citation patterns
# (e.g. `መዝ ፳፻፤5` = "Ps 215", `ዮሐ.ይ፤፳-፲፻` = "John ?:?").
#
# Contrast with Tewahedo-distinctive books (Meqabyan, Jubilees, 1 Enoch)
# where the PDF carries explicit Ethiopic-numeral verse prefixes
# (`፪፤ ስመ ...` = "verse 2: name ..."). These continue to use the
# single-line mode (τ.6.x.1 + τ.6.x.1.B).
#
# The extension adds a `paragraph_mode=True` kwarg to
# `parse_verses_from_text()` that:
#   1. Walks chapter markers same as today.
#   2. Within each chapter, splits the text by `።` to obtain verse
#      fragments.
#   3. Filters out cross-reference fragments via `CROSS_REF_FRAGMENT_RE`
#      (short strings with mostly numerals + biblical-citation
#      patterns).
#   4. Numbers verses sequentially within each chapter starting from 1.
#
# Callers in `extract_section()` pass `paragraph_mode=True` for
# standard-canon sections (genesis, exodus, ...) and `paragraph_mode=
# False` (the default) for Tewahedo-distinctive sections (meqabyan,
# jubilees, one_enoch).

# CROSS_REF_FRAGMENT_RE matches a verse-fragment that is a cross-
# reference, not body text. Cross-refs in this PDF carry biblical-
# citation shape: optionally a 1-5-character Ethiopic book-abbreviation
# + `.` or whitespace + chapter:verse numerals (Arabic or Ethiopic) +
# optional verse range, possibly with `፤` `፡` `፣` separators. They're
# short (≤30 chars) and CONTAIN A NUMERAL.
#
# Examples that should match:
#   `መዝ ፳፻፤5`          (book abbrev + Ethiopic numerals + Arabic digit)
#   `ዮሐ.ይ፤፳-፲፻`        (book abbrev + period + numerals + range)
#   `፻9፪፤፳`            (pure numerals - chapter:verse standalone)
#   `ቀ. ፲፫`            (book abbrev + period + Ethiopic numeral)
#
# Examples that should NOT match (real verse text):
#   `በመጀመሪያው ቀን እግዚአብሔር ሰማይንና ምድርን ፈጠረ` (Gen 1:1)
#   `እግዚአብሔርም ብርሃን ይሁን አለ` (Gen 1:3)
#
# Heuristic: short Ethiopic strings (≤30 chars) whose digit+numeral
# coverage exceeds ~25% of the non-whitespace characters are likely
# cross-references rather than body text.

CROSS_REF_FRAGMENT_RE = re.compile(
    r"^\s*"
    r"(?:[ሀ-ፗ]{1,5}[\.,]?\s*)?"  # optional 1-5-char book abbreviation
    r"[፩-፼\d]+"  # required numeral run
    r"(?:[፡:፣፤፥፦፧፨\-,\./\s]+[፩-፼\d]+)*"  # optional more numeral runs + separators
    r"[፡:፣፤፥፦፧፨]?\s*"  # optional trailing separator
    r"$"
)


def is_cross_ref_fragment(frag: str) -> bool:
    """Heuristic: is this verse-fragment a biblical cross-reference
    rather than body text?

    Returns True if the fragment is SHORT (≤30 chars, post-strip) AND
    matches CROSS_REF_FRAGMENT_RE (book-abbrev + numerals shape) OR
    has high digit/numeral coverage (>25% of non-whitespace
    characters are Arabic digits or Ethiopic numerals).
    """
    s = frag.strip()
    if not s:
        return False
    if len(s) > 30:
        return False  # body-text length; not a cross-ref
    if CROSS_REF_FRAGMENT_RE.match(s):
        return True
    # Fallback: numeral-coverage heuristic
    non_ws = [c for c in s if not c.isspace()]
    if not non_ws:
        return False
    numerals = [c for c in non_ws if c.isdigit() or "፩" <= c <= "፼"]
    return len(numerals) / len(non_ws) > 0.25


# τ.6.x.1.E — NT pericope/section-header rejection.
#
# The Amharic NT carries `ክፍል N፡ ስለ …` ("Section N: concerning …")
# pericope headers between verses. They are long Ethiopic prose with a
# single leading numeral, so is_cross_ref_fragment() (which keys off
# numeral-DOMINATED short strings) does NOT catch them — pre-τ.6.x.1.E
# each one survived the `።`-split as a spurious verse, inflating the
# count (the true mechanism behind the τ.7.x.v "NT-renumber-overflow"
# blocker, alongside the dropped `!`-terminated Mt-1 chapter marker).
# They are highly regular: the literal keyword `ክፍል`, a separator,
# then a section numeral. Matching that exact shape (NOT a bare
# leading "ክፍል", which can legitimately open a verse) keeps the
# false-positive risk ~zero.

PERICOPE_HEADER_RE = re.compile(r"^\s*ክፍል[\s፡፣]+[፩-፼0-9]")


def is_pericope_header(frag: str) -> bool:
    """Is this fragment an NT `ክፍል N፡ …` section header (not scripture)?

    True only for the numbered-section shape `ክፍል <sep> <numeral> …`.
    A verse that merely *contains* the word ክፍል mid-text, or that
    starts with ክፍል but is not followed by a section numeral, is NOT
    a header and is preserved.
    """
    return PERICOPE_HEADER_RE.match(frag or "") is not None


# Per-book expected verse-count floor for sanity-checking paragraph-mode
# output. Source: Masoretic Text + LXX agreement (modern Bible verse-
# count standard). Used by callers to validate τ.7.x.x ingest output;
# the parser itself does NOT enforce floors (the parser is single-
# responsibility — extract whatever's in the text + let callers gate
# on quality).
GENESIS_VERSE_COUNTS = {
    1: 31,
    2: 25,
    3: 24,
    4: 26,
    5: 32,
    6: 22,
    7: 24,
    8: 22,
    9: 29,
    10: 32,
    11: 32,
    12: 20,
    13: 18,
    14: 24,
    15: 21,
    16: 16,
    17: 27,
    18: 33,
    19: 38,
    20: 18,
    21: 34,
    22: 24,
    23: 20,
    24: 67,
    25: 34,
    26: 35,
    27: 46,
    28: 22,
    29: 35,
    30: 43,
    31: 55,
    32: 33,
    33: 20,
    34: 31,
    35: 29,
    36: 43,
    37: 36,
    38: 30,
    39: 23,
    40: 23,
    41: 57,
    42: 38,
    43: 34,
    44: 34,
    45: 28,
    46: 34,
    47: 31,
    48: 22,
    49: 33,
    50: 26,
}
# Total Genesis verses = 1534 (Masoretic-tradition Genesis 31:55
# treated as its own verse; Christian/Protestant tradition that
# renumbers 31:55 as 32:1 yields the alternative 1533 total).


# τ.7.x.b — Canonical Exodus verse counts (40 chapters, 1213 verses).
# Added at τ.7.x.b ship-time as the second renumber-floor for the
# parallel-Bible Amharic-stream ingest under D1-a per-book cadence.
# Masoretic + LXX + Vulgate + Tewahedo enumerations agree on the
# per-chapter counts.
EXODUS_VERSE_COUNTS = {
    1: 22,
    2: 25,
    3: 22,
    4: 31,
    5: 23,
    6: 30,
    7: 25,
    8: 32,
    9: 35,
    10: 29,
    11: 10,
    12: 51,
    13: 22,
    14: 31,
    15: 27,
    16: 36,
    17: 16,
    18: 27,
    19: 25,
    20: 26,
    21: 36,
    22: 31,
    23: 33,
    24: 18,
    25: 40,
    26: 37,
    27: 21,
    28: 43,
    29: 46,
    30: 38,
    31: 18,
    32: 35,
    33: 23,
    34: 35,
    35: 35,
    36: 38,
    37: 29,
    38: 31,
    39: 43,
    40: 38,
}
# Total Exodus verses = 1213 (Masoretic + LXX + Vulgate agreement).


# τ.7.x.c — Canonical Leviticus verse counts (27 chapters, 859 verses).
# Third renumber-floor for the parallel-Bible Amharic-stream ingest
# under D1-a per-book cadence. Masoretic + LXX + Vulgate + Tewahedo
# enumerations agree on the per-chapter counts.
LEVITICUS_VERSE_COUNTS = {
    1: 17,
    2: 16,
    3: 17,
    4: 35,
    5: 19,
    6: 30,
    7: 38,
    8: 36,
    9: 24,
    10: 20,
    11: 47,
    12: 8,
    13: 59,
    14: 57,
    15: 33,
    16: 34,
    17: 16,
    18: 30,
    19: 37,
    20: 27,
    21: 24,
    22: 33,
    23: 44,
    24: 23,
    25: 55,
    26: 46,
    27: 34,
}
# Total Leviticus verses = 859 (Masoretic + LXX + Vulgate agreement).


# τ.7.x.d — Canonical Numbers verse counts (36 chapters, 1288 verses).
# Fourth renumber-floor for the parallel-Bible Amharic-stream ingest
# under D1-a per-book cadence. Masoretic + LXX + Vulgate + Tewahedo
# enumerations agree on the per-chapter counts (the Vulgate
# 16:36-50 → 17:1-15 boundary repartitioning is NOT followed in the
# Tewahedo Amharic edition per parallel-Bible-EOTC source inspection;
# the floor here is the Hebrew/Masoretic enumeration which yields the
# canonical 1288 total).
NUMBERS_VERSE_COUNTS = {
    1: 54,
    2: 34,
    3: 51,
    4: 49,
    5: 31,
    6: 27,
    7: 89,
    8: 26,
    9: 23,
    10: 36,
    11: 35,
    12: 16,
    13: 33,
    14: 45,
    15: 41,
    16: 50,
    17: 13,
    18: 32,
    19: 22,
    20: 29,
    21: 35,
    22: 41,
    23: 30,
    24: 25,
    25: 18,
    26: 65,
    27: 23,
    28: 31,
    29: 40,
    30: 16,
    31: 54,
    32: 42,
    33: 56,
    34: 29,
    35: 34,
    36: 13,
}
# Total Numbers verses = 1288 (Masoretic + LXX + Tewahedo agreement).


# τ.7.x.e — Canonical Deuteronomy verse counts (34 chapters, 959 verses).
# Fifth renumber-floor for the parallel-Bible Amharic-stream ingest
# under D1-a per-book cadence. CLOSES the §8.1 Pentateuch arc under
# Amharic-first sequencing (gen + ex + lev + num + deut = all 5 books
# of Torah). The 959-verse total reflects the KJV/Vulgate/LXX-aligned
# enumeration; the Hebrew/Masoretic enumeration redistributes some
# verses at the 5/6 + 12/13 + 22/23 + 28/29 chapter boundaries but
# yields the same 959 total. The parallel-Bible-EOTC source uses the
# Christian/Vulgate enumeration consistent with the Ge'ez liturgical
# tradition.
DEUTERONOMY_VERSE_COUNTS = {
    1: 46,
    2: 37,
    3: 29,
    4: 49,
    5: 33,
    6: 25,
    7: 26,
    8: 20,
    9: 29,
    10: 22,
    11: 32,
    12: 32,
    13: 18,
    14: 29,
    15: 23,
    16: 22,
    17: 20,
    18: 22,
    19: 21,
    20: 20,
    21: 23,
    22: 30,
    23: 25,
    24: 22,
    25: 19,
    26: 19,
    27: 26,
    28: 68,
    29: 29,
    30: 20,
    31: 30,
    32: 52,
    33: 29,
    34: 12,
}
# Total Deuteronomy verses = 959 (KJV/LXX/Vulgate-aligned; Hebrew
# Masoretic redistributes some boundaries but yields the same total).


# τ.7.x.f — Canonical Joshua verse counts (24 chapters, 658 verses).
# Sixth renumber-floor for the parallel-Bible Amharic-stream ingest
# under D1-a per-book cadence. OPENS the post-Pentateuch historical-
# books arc under Amharic-first sequencing (the §8.1 Pentateuch arc-
# close at τ.7.x.e marked the canonical Pentateuch boundary; τ.7.x.f
# starts the next canonical unit — the historical-books cluster:
# Joshua → Judges → Ruth → 1-2 Samuel → 1-2 Kings → 1-2 Chronicles
# → Ezra → Nehemiah → Esther under the Protestant ordering, or
# Joshua → Judges → Ruth → 1-4 Kingdoms → 1-2 Paralipomena → Ezra/
# Nehemiah → Esther in the LXX ordering followed by the Tewahedo
# tradition). The 658-verse total matches KJV/standard Christian
# enumeration; Hebrew/Masoretic agrees.
JOSHUA_VERSE_COUNTS = {
    1: 18,
    2: 24,
    3: 17,
    4: 24,
    5: 15,
    6: 27,
    7: 26,
    8: 35,
    9: 27,
    10: 43,
    11: 23,
    12: 24,
    13: 33,
    14: 15,
    15: 63,
    16: 10,
    17: 18,
    18: 28,
    19: 51,
    20: 9,
    21: 45,
    22: 34,
    23: 16,
    24: 33,
}
# Total Joshua verses = 658 (KJV/Hebrew Masoretic + LXX agreement).


# τ.7.x.g — Canonical Judges verse counts (21 chapters, 618 verses).
# Seventh renumber-floor for the parallel-Bible Amharic-stream ingest
# under D1-a per-book cadence. CONTINUES the post-Pentateuch historical-
# books arc opened at τ.7.x.f (Joshua → Judges → Ruth → 1-4 Kingdoms →
# 1-2 Paralipomena → Ezra/Nehemiah → Esther under the LXX/Tewahedo
# ordering). The 618-verse total matches KJV/standard Christian
# enumeration; Hebrew Masoretic + LXX agree (no chapter-boundary
# repartitioning between traditions).
JUDGES_VERSE_COUNTS = {
    1: 36,
    2: 23,
    3: 31,
    4: 24,
    5: 31,
    6: 40,
    7: 25,
    8: 35,
    9: 57,
    10: 18,
    11: 40,
    12: 15,
    13: 25,
    14: 20,
    15: 20,
    16: 31,
    17: 13,
    18: 31,
    19: 30,
    20: 48,
    21: 25,
}
# Total Judges verses = 618 (KJV/Hebrew Masoretic + LXX agreement).


# τ.7.x.h — Canonical Ruth verse counts (4 chapters, 85 verses).
# Eighth renumber-floor for the parallel-Bible Amharic-stream ingest
# under D1-a per-book cadence. CONTINUES the post-Pentateuch historical-
# books arc (Joshua → Judges → Ruth → 1-4 Kingdoms → ...). Ruth is the
# SHORTEST canonical book in the Old Testament (4 chapters, 85 verses)
# and is the smallest τ.7.x.* per-book ingest to date — only ~6 PDF
# pages of content. The 85-verse total matches KJV/standard Christian
# enumeration; Hebrew Masoretic + LXX agree (no chapter-boundary
# repartitioning between traditions).
RUTH_VERSE_COUNTS = {
    1: 22,
    2: 23,
    3: 18,
    4: 22,
}
# Total Ruth verses = 85 (KJV/Hebrew Masoretic + LXX agreement).


# τ.7.x.i — Canonical Psalter verse counts under LXX/Tewahedo
# enumeration (151 Psalms, ~2551 total verses). The Tewahedo Psalter
# inherits the LXX numbering (so LXX Psalm 9 = Hebrew Psalms 9+10
# merged; LXX Psalm 17 = Hebrew Psalm 18 with title counted as v1;
# etc.) and adds Psalm 151 — the David-vs-Goliath psalm preserved
# only in the LXX/Tewahedo/Syriac canon (deuterocanonical from a
# Protestant perspective; fully canonical in Tewahedo).
#
# Ninth renumber-floor for the parallel-Bible Amharic-stream ingest
# under D1-a per-book cadence. **SKIPS the 438-802 dzamaragna gap**
# (1 Samuel → Job, 10 books in Amharic-only format) and RESUMES the
# parallel-Bible-EOTC scan at page 803 (second EOTC-parallel block
# discovered at τ.7.x.h structural inspection).
#
# Verse counts below follow the standard LXX/Tewahedo Psalter as
# documented in Brenton's LXX + the Ethiopian Orthodox liturgical
# psalter. Counts include title verses where the LXX/Tewahedo
# tradition treats them as numbered (e.g., LXX Psalm 50:1-2 are the
# David-after-Bathsheba superscription; the body begins at v3).
PSALMS_VERSE_COUNTS = {
    1: 6,
    2: 12,
    3: 9,
    4: 9,
    5: 13,
    6: 11,
    7: 18,
    8: 10,
    9: 39,
    10: 7,
    11: 9,
    12: 6,
    13: 7,
    14: 5,
    15: 11,
    16: 15,
    17: 51,
    18: 15,
    19: 10,
    20: 14,
    21: 32,
    22: 6,
    23: 10,
    24: 22,
    25: 12,
    26: 14,
    27: 9,
    28: 11,
    29: 13,
    30: 25,
    31: 11,
    32: 22,
    33: 23,
    34: 28,
    35: 13,
    36: 40,
    37: 22,
    38: 14,
    39: 18,
    40: 14,
    41: 12,
    42: 5,
    43: 26,
    44: 18,
    45: 12,
    46: 10,
    47: 15,
    48: 21,
    49: 23,
    50: 21,
    51: 9,
    52: 7,
    53: 9,
    54: 24,
    55: 14,
    56: 12,
    57: 12,
    58: 18,
    59: 14,
    60: 9,
    61: 13,
    62: 12,
    63: 11,
    64: 14,
    65: 20,
    66: 8,
    67: 36,
    68: 36,
    69: 6,
    70: 24,
    71: 19,
    72: 28,
    73: 23,
    74: 10,
    75: 13,
    76: 21,
    77: 72,
    78: 13,
    79: 20,
    80: 17,
    81: 8,
    82: 19,
    83: 13,
    84: 14,
    85: 17,
    86: 7,
    87: 19,
    88: 53,
    89: 17,
    90: 16,
    91: 16,
    92: 5,
    93: 23,
    94: 11,
    95: 13,
    96: 12,
    97: 9,
    98: 9,
    99: 5,
    100: 8,
    101: 29,
    102: 22,
    103: 35,
    104: 45,
    105: 48,
    106: 43,
    107: 14,
    108: 31,
    109: 7,
    110: 10,
    111: 10,
    112: 9,
    113: 26,
    114: 9,
    115: 10,
    116: 2,
    117: 29,
    118: 176,
    119: 7,
    120: 8,
    121: 9,
    122: 4,
    123: 8,
    124: 5,
    125: 6,
    126: 5,
    127: 6,
    128: 8,
    129: 8,
    130: 4,
    131: 18,
    132: 3,
    133: 3,
    134: 21,
    135: 26,
    136: 9,
    137: 8,
    138: 24,
    139: 14,
    140: 13,
    141: 8,
    142: 12,
    143: 15,
    144: 21,
    145: 10,
    146: 11,
    147: 9,
    148: 14,
    149: 9,
    150: 6,
    151: 7,
}
# Total Psalter verses = 2551 (LXX/Tewahedo enumeration, including
# Psalm 151 David-vs-Goliath). Hebrew/Protestant Psalter (150 Psalms)
# yields ~2461 verses with different chapter boundaries.


# τ.7.x.j — Ezra Sutuʼel (2 Esdras / 4 Ezra) verse counts. The
# Ethiopian Tewahedo `መጽሐፈ ዕዝራ ሱቱኤል` is the Ezra-apocalypse — the
# text the Latin tradition calls 4 Esdras and the KJV/NRSV Apocrypha
# calls 2 Esdras. Unlike the Latin (which lost the long "missing
# fragment" 7:36-105), the Ethiopic/Syriac/Arabic witnesses PRESERVE
# it, so the Tewahedo ch 7 is the full 140-verse form. content/
# books.yaml fixes `2es` at ch_count: 16 (the full 5-Ezra + 4-Ezra +
# 6-Ezra Vulgate-appendix span); this floor uses the NRSV 16-chapter
# enumeration WITH the restored 7:36-105 fragment that survives in
# the Ethiopic. Tenth renumber-floor for the parallel-Bible Amharic-
# stream ingest under D1-a per-book cadence; FIRST deuterocanonical
# (non-protocanonical) τ.7.x.* floor. Exact Ethiopic Ezra-Sutuʼel
# chapter boundaries (the EOTC printing's treatment of the Christian
# 5/6-Ezra additions) are reconciled at the τ.6.x.3 batched audit
# per the τ.6.x.0b honesty contract — same as every prior ship.
EZRA_SUTUEL_VERSE_COUNTS = {
    1: 40,
    2: 48,
    3: 36,
    4: 52,
    5: 56,
    6: 59,
    7: 140,
    8: 63,
    9: 47,
    10: 60,
    11: 46,
    12: 51,
    13: 58,
    14: 48,
    15: 63,
    16: 78,
}
# Total Ezra Sutuʼel (2 Esdras) verses = 945 (NRSV 16-chapter
# enumeration including the restored 7:36-105 Ethiopic fragment).
# KJV Apocrypha (without the fragment) yields ~875.


# τ.7.x.k — Tobit verse counts. The Tewahedo `መጽሐፈ ጦቢት` follows the
# LXX 14-chapter Tobit (content/books.yaml fixes `tob` at ch_count:
# 14). Verse counts use the NRSV enumeration (GII / Codex Sinaiticus
# long recension, the form closest to the Ethiopic). The GI
# (Vaticanus) short recension + the Vulgate differ by ±1-2 verses in
# several chapters; per the τ.6.x.0b honesty contract the renumber-
# floor is a canonical ceiling and the τ.6.x.3 batched audit
# reconciles the exact Ethiopic recension boundaries — identical
# treatment to the Psalms LXX/Tewahedo-vs-Hebrew enumeration variance
# at τ.7.x.i. Eleventh renumber-floor under D1-a per-book cadence.
TOBIT_VERSE_COUNTS = {
    1: 22,
    2: 14,
    3: 17,
    4: 21,
    5: 22,
    6: 18,
    7: 17,
    8: 21,
    9: 6,
    10: 14,
    11: 19,
    12: 22,
    13: 18,
    14: 15,
}
# Total Tobit verses = 246 (NRSV/GII 14-chapter enumeration).


# τ.7.x.l — Judith verse counts. The Tewahedo `መጽሐፈ ዮዲት` follows
# the LXX 16-chapter Judith (content/books.yaml fixes `jdt` at
# ch_count: 16). Verse counts use the NRSV enumeration. Twelfth
# renumber-floor under D1-a per-book cadence; third deuterocanonical
# τ.7.x.* floor (after 2es Ezra Sutuʼel + tob Tobit). The Vulgate
# Judith differs substantially in verse division from the LXX/NRSV
# (Jerome worked from an Aramaic text); per the τ.6.x.0b honesty
# contract the floor is the canonical ceiling and the τ.6.x.3
# batched audit reconciles the exact Ethiopic recension boundaries.
JUDITH_VERSE_COUNTS = {
    1: 16,
    2: 28,
    3: 10,
    4: 15,
    5: 24,
    6: 21,
    7: 32,
    8: 36,
    9: 14,
    10: 23,
    11: 23,
    12: 20,
    13: 20,
    14: 19,
    15: 13,
    16: 25,
}
# Total Judith verses = 339 (NRSV/LXX 16-chapter enumeration).


# τ.7.x.m — Esther verse counts. content/books.yaml fixes `est` at
# ch_count: 10 — the Hebrew/Masoretic protocanonical Esther core.
# The Greek "Additions to Esther" (Additions A-F) are a SEPARATE
# Tewahedo book code (b25 in books.yaml), NOT part of this floor.
# Verse counts use the standard KJV/Hebrew Masoretic enumeration.
# Esther is sourced here from the EOTC-parallel block p1308-1317 —
# the documented alternative to the τ.7.x.i dzamaragna-gap Esther
# (τ.7.x.i recorded `est` SKIPPED-via-dzamaragna but flagged this
# parallel block as the preferred source "if/when that ship
# happens"; τ.7.x.m IS that ship — see the τ.7.x.i est skip-pin
# conversion). The EOTC-parallel text likely interleaves the Greek
# additions; the renumber-against-floor + τ.6.x.3 audit reconcile
# that (same treatment as 2es's 5/6-Ezra + tob's recension variance).
# Thirteenth renumber-floor under D1-a per-book cadence.
ESTHER_VERSE_COUNTS = {
    1: 22,
    2: 23,
    3: 15,
    4: 17,
    5: 14,
    6: 14,
    7: 10,
    8: 17,
    9: 32,
    10: 3,
}
# Total Esther verses = 167 (KJV/Hebrew Masoretic 10-chapter
# enumeration; the Greek Additions are the separate `b25` book).


# τ.7.x.n — Mäqabyan trilogy verse counts (mq1 / mq2 / mq3). The
# FIRST Tewahedo-distinctive book(s) in the τ.7.x.* stream and the
# FIRST multi-book EOTC-parallel block (p1318-1378). Mäqabyan has NO
# Western canonical enumeration — it is uniquely Tewahedo-canonical
# (distinct from the Greek LXX 1-4 Maccabees: shared title only).
#
# COORDINATION (per PLAN τ.7.x.n NEXT-UP note — coordinate with the
# γ.4.8 patristic arc + the δ.1.x Meqabyan-revision track):
#   The floors are derived as the per-chapter MAX verse number across
#   content/candidates/mq{N}_ch_*.json — the IDENTICAL derivation the
#   δ.1.x divergence JSON documents for its mq1 ch1-9
#   per_chapter_verse_count_floor ("max-verse-with-note ... Wright
#   1877 + Cowley 1974b apparatus (γ.4.8.F sources) is the canonical
#   reference"). mq1 ch1-9 below {1:14,2:28,3:38,4:5,5:14,6:23,7:1,
#   8:22,9:3} EXACTLY matches content/divergence/
#   meqabyan_geez_divergence.json::_meta.batch_prep.
#   per_chapter_verse_count_floor — so the parallel-Bible ingest, the
#   δ.1.x revision, and the γ.4.8 apparatus all align on ONE verse
#   structure. ch_counts match content/books.yaml (mq1:36 b26 /
#   mq2:21 b27 / mq3:10 b28) + build_meqabyan_revision.py BOOKS.
#
# Per the extract_parallel_pdf.py QUALITY POLICY, Mäqabyan output is
# `ocr-tier3` and EXPLICITLY δ.1.x-REPLACEABLE — this is the OCR
# witness the δ.1.x page-image-tier1 divergence apparatus diverges
# FROM, NOT the long-term authoritative text. Fourteenth/fifteenth/
# sixteenth renumber-floors under D1-a per-book cadence.
MQ1_VERSE_COUNTS = {
    1: 14,
    2: 28,
    3: 38,
    4: 5,
    5: 14,
    6: 23,
    7: 1,
    8: 22,
    9: 3,
    10: 5,
    11: 3,
    12: 1,
    13: 20,
    14: 15,
    15: 8,
    16: 1,
    17: 14,
    18: 2,
    19: 1,
    20: 14,
    21: 14,
    22: 14,
    23: 14,
    24: 14,
    25: 9,
    26: 14,
    27: 14,
    28: 38,
    29: 5,
    30: 21,
    31: 14,
    32: 14,
    33: 8,
    34: 14,
    35: 14,
    36: 49,
}
# Total 1 Mäqabyan verses = 502 (36 ch; Maqabis-of-Benjamin
# martyrology vs Ṣiruṣaydan).

MQ2_VERSE_COUNTS = {
    1: 14,
    2: 9,
    3: 11,
    4: 17,
    5: 14,
    6: 8,
    7: 9,
    8: 14,
    9: 11,
    10: 14,
    11: 9,
    12: 18,
    13: 7,
    14: 29,
    15: 11,
    16: 8,
    17: 5,
    18: 14,
    19: 10,
    20: 13,
    21: 11,
}
# Total 2 Mäqabyan verses = 256 (21 ch; Maqabis-of-Moab conversion
# + sons' martyrdom + Ṣiruṣaydan's death).

MQ3_VERSE_COUNTS = {
    1: 28,
    2: 24,
    3: 15,
    4: 34,
    5: 14,
    6: 14,
    7: 14,
    8: 10,
    9: 5,
    10: 30,
}
# Total 3 Mäqabyan verses = 188 (10 ch; homiletic + angelological
# dialogue + Satan-refused-Adam tradition + resurrection-doctrine).
# Trilogy total = 502 + 256 + 188 = 946 verses / 67 chapters.


# τ.7.x.o — Sirach (sir / Ecclesiasticus / The Wisdom of Jesus the
# Son of Sirach). content/books.yaml fixes `sir` at ch_count: 51
# (b36). Verse counts use the standard NRSV Apocrypha / Göttingen-
# Ziegler LXX Sirach enumeration — continuing the deuterocanon-NRSV
# pattern of 2es/tob/jdt. Sirach has well-known recension variance
# (the Greek GI vs the longer GII; the Hebrew Masada/Geniza
# fragments; the Vulgate chapter-30/36 displacement). Per the
# τ.6.x.0b honesty contract the floor is the canonical CEILING and
# the τ.6.x.3 batched audit reconciles the exact Ethiopic recension
# boundaries (identical caveat to the JUDITH floor). Seventeenth
# renumber-floor under D1-a per-book cadence; FIRST τ.7.x.* book in
# the sixth EOTC-parallel block (p1379+).
SIRACH_VERSE_COUNTS = {
    1: 30,
    2: 18,
    3: 31,
    4: 31,
    5: 15,
    6: 37,
    7: 36,
    8: 19,
    9: 18,
    10: 31,
    11: 34,
    12: 18,
    13: 26,
    14: 27,
    15: 20,
    16: 30,
    17: 32,
    18: 33,
    19: 30,
    20: 32,
    21: 28,
    22: 27,
    23: 27,
    24: 34,
    25: 26,
    26: 29,
    27: 30,
    28: 26,
    29: 28,
    30: 25,
    31: 31,
    32: 24,
    33: 33,
    34: 31,
    35: 26,
    36: 31,
    37: 31,
    38: 34,
    39: 35,
    40: 30,
    41: 27,
    42: 25,
    43: 33,
    44: 23,
    45: 26,
    46: 20,
    47: 25,
    48: 25,
    49: 16,
    50: 29,
    51: 30,
}
# Total Sirach verses = 1413 (51 ch; NRSV/Göttingen-Ziegler LXX
# enumeration; the unnumbered translator's Prologue is excluded —
# the EOTC-parallel text may interleave it, reconciled at τ.6.x.3).


# τ.7.x.p — Paralipomena of Jeremiah / 4 Baruch (4ba). content/
# books.yaml fixes `4ba` at ch_count: 9 (b42). Verse counts use the
# Kraft-Purintun 1972 (SBL Texts & Translations 1) critical-edition
# 9-chapter division, cross-checked against Harris 1889. The
# Ethiopic recension (Dillmann; the EOTC broader canon) is KNOWN to
# differ from the Greek — it carries an extended Christian conclusion
# in ch 9 (the Jeremiah-martyrdom + resurrection-preaching cycle).
# Per the τ.6.x.0b honesty contract the floor is the canonical
# CEILING; the τ.6.x.3 audit reconciles the Ethiopic recension
# (identical caveat to TOBIT's GII recension variance). Eighteenth
# renumber-floor; SECOND τ.7.x.* book in the sixth EOTC-parallel
# block; drains it (Wisdom of Solomon opens the seventh block after).
FOUR_BARUCH_VERSE_COUNTS = {
    1: 11,
    2: 10,
    3: 22,
    4: 11,
    5: 34,
    6: 25,
    7: 37,
    8: 9,
    9: 32,
}
# Total 4 Baruch verses = 191 (9 ch; Kraft-Purintun 1972; the
# Ethiopic ch-9 Christian expansion is reconciled at τ.6.x.3).


# τ.7.x.q — The Book of Baruch (bar). content/books.yaml fixes `bar`
# at ch_count: 5 (b40). Verse counts use the standard NRSV/LXX
# Baruch enumeration (the deuterocanon-NRSV pattern of 2es/tob/jdt/
# sir). NOTE: the Letter of Jeremiah (lje, books.yaml b41) is the
# LXX/Vulgate "Baruch ch 6" but content/books.yaml treats it as a
# SEPARATE book (ch_count: 1); this floor is the 5-chapter Baruch
# proper. Per the τ.6.x.0b honesty contract the floor is the
# canonical CEILING and the τ.6.x.3 batched audit reconciles the
# exact Ethiopic recension + the lje-as-Baruch-6 ambiguity
# (identical caveat to the JUDITH + SIRACH floors). Nineteenth
# renumber-floor; FIRST book of the seventh EOTC-parallel block.
BARUCH_VERSE_COUNTS = {
    1: 22,
    2: 35,
    3: 38,
    4: 37,
    5: 9,
}
# Total Baruch verses = 141 (5 ch; NRSV/LXX enumeration; the Letter
# of Jeremiah is the SEPARATE `lje` book, NOT this floor).


# τ.7.x.r — The Wisdom of Solomon (wis). content/books.yaml fixes
# `wis` at ch_count: 19 (b33). Verse counts use the standard NRSV/
# Göttingen-Ziegler LXX Wisdom-of-Solomon enumeration (continuing
# the deuterocanon-NRSV pattern). Per the τ.6.x.0b honesty contract
# the floor is the canonical CEILING; the τ.6.x.3 batched audit
# reconciles the exact Ethiopic recension boundaries (identical
# caveat to the SIRACH floor). Twentieth renumber-floor; SECOND
# (major) book of the seventh EOTC-parallel block; drains the
# bar+wis major-book pair before the Daniel-additions cluster.
WISDOM_OF_SOLOMON_VERSE_COUNTS = {
    1: 16,
    2: 24,
    3: 19,
    4: 20,
    5: 23,
    6: 25,
    7: 30,
    8: 21,
    9: 18,
    10: 21,
    11: 26,
    12: 27,
    13: 19,
    14: 31,
    15: 19,
    16: 29,
    17: 21,
    18: 25,
    19: 22,
}
# Total Wisdom of Solomon verses = 436 (19 ch; NRSV/Göttingen-
# Ziegler LXX enumeration).


# τ.7.x.s — The Prayer of Azariah and the Song of the Three Holy
# Children (paz). content/books.yaml fixes `paz` at ch_count: 1
# (b45) — the EOTC "ተረፈ ዳንኤል" (Rest of Daniel) appendix opens with
# this combined unit (Prayer of Azariah + the Benedicite Song of
# the Three). Verse counts use the standard NRSV "The Prayer of
# Azariah and the Song of the Three Jews" enumeration (1 ch / 68 v;
# continuing the deuterocanon-NRSV pattern of 2es/tob/jdt/sir/bar/
# wis). Per the τ.6.x.0b honesty contract the floor is the canonical
# CEILING; the τ.6.x.3 batched audit reconciles the exact Ethiopic
# ተረፈ-ዳንኤል recension (the Theodotion Dan-3:24-90 insertion vs the
# standalone-appendix placement). Twenty-first renumber-floor; FIRST
# book of the Daniel-additions cluster (eighth EOTC-parallel block).
PRAYER_OF_AZARIAH_VERSE_COUNTS = {
    1: 68,
}
# Total Prayer of Azariah + Song of the Three verses = 68 (1 ch;
# NRSV enumeration; combined unit per books.yaml `paz` ch_count: 1).


# τ.7.x.s — The History of Susanna (sus). content/books.yaml fixes
# `sus` at ch_count: 1 (b46). Verse counts use the standard NRSV
# (Theodotion) Susanna enumeration (1 ch / 64 v). NOTE: the τ.7.x.s
# structural-discovery scan (deep band p1440-1455, the τ.7.x.n/o/q
# content-boundary method) found Susanna is NOT distinctly present
# in this parallel-Bible PDF's "ተረፈ ዳንኤል" cluster (p1449-1453 =
# Prayer of Azariah/Song of the Three p1449-1451 + Bel & the Dragon
# p1452-1453 ONLY; zero Susanna/elders/garden/Joachim markers in the
# band). Susanna in the EOTC tradition is commonly embedded inside
# the Book of Daniel proper (the not-yet-ingested `dan` block, b44)
# as a Daniel-13-class chapter rather than in the standalone
# appendix. This floor is therefore PRE-STAGED (infra-ready) but
# Susanna ingest is DEFERRED to the τ.6.x.3 batched audit / the
# future `dan` τ.7.x.* ship — exactly the τ.7.x.q `lje`-deferral
# precedent + the `laodiceans` present_in_pdf:false pattern. Twenty-
# second renumber-floor (infra-ready, content-deferred at τ.7.x.s).
SUSANNA_VERSE_COUNTS = {
    1: 64,
}
# Total Susanna verses = 64 (1 ch; NRSV/Theodotion enumeration).
# DEFERRED at τ.7.x.s — not distinctly present in the parallel-Bible
# PDF ተረፈ-ዳንኤል cluster (Susanna-as-embedded-Daniel-13 ambiguity;
# reconciled at τ.6.x.3 / the future `dan` ingest).


# τ.7.x.s — Bel and the Dragon (bel). content/books.yaml fixes `bel`
# at ch_count: 1 (b47). Verse counts use the standard NRSV Bel and
# the Dragon enumeration (1 ch / 42 v). Empirically the SECOND (and
# closing) book of the EOTC "ተረፈ ዳንኤል" cluster (PDF p1452-1453;
# GEZ banner "ተረፈ ዳንኤል ምፅራፍ ፲፫"; Bel idol-food / clay-and-bronze
# / 70-priests + the ዘንዶ dragon narrative; the p1453 colophon
# "…ዳንኤል የተናገረው … ተፈጸመ" closes the whole appendix; p1454 opens
# Jubilees ።ኩፉሌ።, EXACTLY matching the pre-existing Π.1 structural_
# map.jubilees [1454,1514] — decisive cross-validation that the
# τ.7.x.s scan indexing is correct). Per the τ.6.x.0b honesty
# contract the floor is the canonical CEILING; τ.6.x.3 reconciles
# the exact Ethiopic recension. Twenty-third renumber-floor; DRAINS
# the Daniel-additions cluster (paz shipped + bel shipped; sus
# deferred per SUSANNA_VERSE_COUNTS above).
BEL_AND_THE_DRAGON_VERSE_COUNTS = {
    1: 42,
}
# Total Bel and the Dragon verses = 42 (1 ch; NRSV enumeration).


# τ.7.x.t — The Book of Jubilees / Mäṣḥafä Kufāle (jub). content/
# books.yaml fixes `jub` at ch_count: 50 (b15; "The Book of
# Jubilees, or The Little Genesis" — R.H. Charles's exact title).
# A uniquely-Tewahedo-canonical OT text; the FIRST of the two
# LARGE Π.1-mapped Tewahedo-distinctive books (1 Enoch τ.7.x.u
# follows). Verse counts use the standard R.H. Charles 1913 /
# VanderKam 1989 (CSCO 510-511) Jubilees enumeration — the
# universally-cited critical versification (Charles + VanderKam
# concordant on the 50-ch / ~1306-1307-v division). Per the
# τ.6.x.0b honesty contract the floor is the canonical CEILING;
# the τ.6.x.3 batched audit reconciles the exact Ethiopic Mäṣḥafä
# Kufāle recension (identical caveat to the SIRACH / one_enoch
# floors). FLOOR-COORDINATION CROSS-VALIDATION (the τ.7.x.n
# δ.1.x-proof discipline): the project's existing γ.4.5 Mäṣḥafä
# Kufāle annotation maxima in content/notes/jub.py never EXCEED
# this ceiling and match it exactly at the distinctive chapters
# (ch6=38, ch7=39, ch9=15) — the parallel-Bible OCR layer + the
# v1 γ.4.5 apparatus align on ONE Jubilees verse structure.
# Twenty-fourth renumber-floor; FIRST of the two LARGE Tewahedo-
# distinctive books; the structural_map.jubilees section
# (Π.1-discovered [1454,1514], cross-validated 3× at τ.7.x.q/r/s)
# is UPGRADED verified:tentative→true / Π.1→τ.7.x.t by this ship.
JUBILEES_VERSE_COUNTS = {
    1: 29,
    2: 33,
    3: 35,
    4: 33,
    5: 32,
    6: 38,
    7: 39,
    8: 30,
    9: 15,
    10: 35,
    11: 24,
    12: 31,
    13: 29,
    14: 24,
    15: 34,
    16: 31,
    17: 18,
    18: 19,
    19: 31,
    20: 13,
    21: 26,
    22: 30,
    23: 32,
    24: 33,
    25: 23,
    26: 35,
    27: 27,
    28: 30,
    29: 20,
    30: 26,
    31: 32,
    32: 34,
    33: 23,
    34: 21,
    35: 27,
    36: 24,
    37: 25,
    38: 24,
    39: 18,
    40: 13,
    41: 28,
    42: 25,
    43: 24,
    44: 34,
    45: 16,
    46: 16,
    47: 12,
    48: 19,
    49: 23,
    50: 13,
}
# Total Jubilees verses = 1306 (50 ch; R.H. Charles 1913 /
# VanderKam 1989 CSCO enumeration; canonical CEILING — τ.6.x.3
# reconciles the exact Ethiopic Mäṣḥafä Kufāle recension).


# τ.7.x.u — The Book of Enoch / Mäṣḥafä Hēnok / 1 Enoch (1en).
# content/books.yaml fixes `1en` at ch_count: 108 (b16). The
# SECOND of the two LARGE Π.1-mapped Tewahedo-distinctive books
# (Jubilees τ.7.x.t was the first); uniquely-Tewahedo-canonical.
# Verse counts use the standard R.H. Charles 1912 "The Book of
# Enoch" enumeration — the project's stated 1 Enoch standard (cf.
# structural_map.one_enoch.chapter_count_expected "# R.H. Charles
# 1912 chapter count" + the γ.4.4 Mäṣḥafä Hēnok arc). Five
# sections: Watchers (1-36), Parables (37-71), Astronomical
# (72-82), Dream-Visions (83-90), Epistle (91-108). Per the
# τ.6.x.0b honesty contract the floor is the canonical CEILING;
# the τ.6.x.3 batched audit reconciles the exact Ethiopic Mäṣḥafä
# Hēnok recension (identical caveat to the SIRACH / JUBILEES
# floors). FLOOR-COORDINATION CROSS-VALIDATION (the τ.7.x.n/t
# δ.1.x-proof discipline, here STRONGER than τ.7.x.t): every one
# of the 108 chapters was hard-validated ≥ the project's existing
# γ.4.4 Mäṣḥafä Hēnok per-chapter annotation maxima in content/
# notes/1en.py (ALL 108 cross-validated, not a 3-chapter sample);
# the γ.4.4 maxima never exceed this Charles ceiling, with exact
# matches at the distinctive long chapters (14=25, 60=25, 90=42)
# confirming the shared Charles enumeration. Twenty-fifth
# renumber-floor; the structural_map.one_enoch section
# (Π.1-discovered [1515,1566], cross-validated at τ.7.x.s/t as the
# post-Jubilees boundary) is UPGRADED verified:tentative→true /
# Π.1→τ.7.x.u by this ship.
ONE_ENOCH_VERSE_COUNTS = {
    1: 9,
    2: 3,
    3: 1,
    4: 1,
    5: 9,
    6: 8,
    7: 6,
    8: 4,
    9: 11,
    10: 22,
    11: 2,
    12: 6,
    13: 10,
    14: 25,
    15: 12,
    16: 4,
    17: 8,
    18: 16,
    19: 3,
    20: 8,
    21: 10,
    22: 14,
    23: 4,
    24: 6,
    25: 7,
    26: 6,
    27: 5,
    28: 3,
    29: 2,
    30: 3,
    31: 3,
    32: 6,
    33: 4,
    34: 3,
    35: 1,
    36: 4,
    37: 5,
    38: 6,
    39: 14,
    40: 10,
    41: 9,
    42: 3,
    43: 4,
    44: 1,
    45: 6,
    46: 8,
    47: 4,
    48: 10,
    49: 4,
    50: 5,
    51: 5,
    52: 9,
    53: 7,
    54: 10,
    55: 4,
    56: 8,
    57: 3,
    58: 6,
    59: 3,
    60: 25,
    61: 13,
    62: 16,
    63: 12,
    64: 2,
    65: 12,
    66: 3,
    67: 13,
    68: 5,
    69: 29,
    70: 4,
    71: 17,
    72: 37,
    73: 8,
    74: 17,
    75: 9,
    76: 14,
    77: 9,
    78: 17,
    79: 6,
    80: 8,
    81: 10,
    82: 20,
    83: 11,
    84: 6,
    85: 10,
    86: 6,
    87: 4,
    88: 3,
    89: 77,
    90: 42,
    91: 19,
    92: 5,
    93: 14,
    94: 11,
    95: 7,
    96: 8,
    97: 10,
    98: 16,
    99: 16,
    100: 13,
    101: 9,
    102: 11,
    103: 15,
    104: 13,
    105: 2,
    106: 19,
    107: 3,
    108: 15,
}
# Total 1 Enoch verses = 1064 (108 ch; R.H. Charles 1912
# enumeration; canonical CEILING ≥ the γ.4.4 notes/1en.py maxima
# at all 108 ch — τ.6.x.3 reconciles the exact Ethiopic Mäṣḥafä
# Hēnok recension).


# τ.7.x.v — The Gospel of Matthew (mat). content/books.yaml fixes
# `mat` at ch_count: 28 (b60, "The Good News According to
# Matthew"). FIRST New Testament book — OPENS the 4-Gospels block
# (Matthew → Mark → Luke → John, p1567-1832 region per the PLAN).
# Verse counts use the standard KJV / UBS-NA Matthew enumeration
# (28 ch / 1071 v). **METHODOLOGY NOTE — NT differs from the OT
# pseudepigrapha:** unlike JUBILEES / ONE_ENOCH (whose floors were
# γ-cross-validated against content/notes/{jub,1en}.py because the
# OT-pseudepigrapha versification is recension-variable), the NT
# chapter/verse division is HIGHLY STANDARDIZED (KJV/NA/UBS/EOTC
# all agree on 28-ch Matthew) so the KJV/UBS floor is authoritative
# DIRECTLY. content/notes/mat.py is deliberately NOT used for
# floor-coordination here: its (int,int) per-chapter maxima are
# implausible as verse numbers (ch6=83, ch20=75 vs KJV 34/34) —
# the legacy original-Ethiopian-Bible-build NT notes evidently use
# a different second-int semantic, so the τ.7.x.t/u γ-cross-
# validation method does NOT transfer to the NT sub-arc (future NT
# ships — Mark/Luke/John… — likewise use the standard NT
# enumeration directly, not notes-cross-validation). Per the
# τ.6.x.0b honesty contract the floor is the canonical CEILING;
# τ.6.x.3 reconciles the exact Ethiopic recension (identical
# caveat to every prior book). The pre-existing
# content/notes/mat.py backslash SyntaxWarning is the same
# legacy-prior-data backslash residual flagged for τ.6.x.3 at
# τ.7.x.t — out of render-cadence scope, not τ.7.x.v-introduced.
# Twenty-sixth renumber-floor; structural_map.matthew is a NEW
# section [1567,1635] (the τ.7.x.q new-section pattern, NOT a Π.1
# upgrade — Matthew was never Π.1-mapped; no prior-pin
# conversion); contiguous after one_enoch [1515,1566], Mark opens
# p1636 (discovery-scan cross-validated).
MATTHEW_VERSE_COUNTS = {
    1: 25,
    2: 23,
    3: 17,
    4: 25,
    5: 48,
    6: 34,
    7: 29,
    8: 34,
    9: 38,
    10: 42,
    11: 30,
    12: 50,
    13: 58,
    14: 36,
    15: 39,
    16: 28,
    17: 27,
    18: 35,
    19: 30,
    20: 34,
    21: 46,
    22: 46,
    23: 39,
    24: 51,
    25: 46,
    26: 75,
    27: 66,
    28: 20,
}
# Total Matthew verses = 1071 (28 ch; standard KJV / UBS-NA NT
# enumeration; canonical CEILING — τ.6.x.3 reconciles the exact
# Ethiopic recension; NT versification is standardized so no
# γ-notes cross-validation, unlike the OT pseudepigrapha).


def _parse_paragraph_mode(text: str) -> list[tuple[int, int, str]]:
    """τ.6.x.1.C paragraph-mode parser + τ.6.x.1.D chapter-marker recovery.

    Walks chapter markers (lenient regex tolerates OCR-garbled
    numerals per τ.6.x.1.D); within each chapter splits the body text
    by `።` sentence-terminator; filters cross-reference fragments;
    numbers verses sequentially. See module-level τ.6.x.1.C +
    τ.6.x.1.D blocks for the full design rationale.
    """
    # First pass: filter lines for ASCII page-header garbage. Keep
    # blank lines so paragraph structure (if any) is preserved for
    # downstream use; the splitter operates on full joined text.
    filtered_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            filtered_lines.append("")
            continue
        has_ethiopic = any(0x1200 <= ord(c) <= 0x137F for c in line)
        if not has_ethiopic and re.search(r"[a-zA-Z]{4,}", line):
            continue  # ASCII page header — drop
        filtered_lines.append(line)
    filtered_text = "\n".join(filtered_lines)

    # Walk chapter markers using the τ.6.x.1.D lenient regex which
    # tolerates OCR-garbled keywords (ምፅራፍ for ምዕራፍ), numerals
    # (e.g. text-layer 'ምዕራፍ B ።', Tesseract 'ምዕራፍ ል፳።'), and
    # terminators (`=` substituted for `።`). CHAPTER_HEADER_RE_
    # LENIENT.split gives [pre, ch_num_token_1, mid_1,
    # ch_num_token_2, mid_2, ...].
    parts = CHAPTER_HEADER_RE_LENIENT.split(filtered_text)
    chapters: list[tuple[int, str]] = []
    if len(parts) > 1:
        # We have at least one chapter marker; the text BEFORE the
        # first marker is typically title-page header noise (publisher
        # banner + book title) and should NOT be credited to chapter 1.
        # The first marker itself establishes chapter 1.
        pre_marker_discarded = True  # noqa: F841 (kept for documentation)
    elif parts and parts[0].strip():
        # No markers at all — credit everything to chapter 1 by
        # default (works for single-chapter sections OR when ALL
        # markers were garbled past recognition).
        chapters.append((1, parts[0]))
    for i in range(1, len(parts), 2):
        ch_num_token = parts[i]
        ch_text = parts[i + 1] if i + 1 < len(parts) else ""
        # τ.6.x.1.D: resolve the chapter number with OCR-tolerance.
        # Sequential fallback uses (chapters[-1][0] if any else 0)
        # so the FIRST marker (when chapters is empty) resolves to 1
        # via 0+1; subsequent markers advance from the previous chapter.
        seed = chapters[-1][0] if chapters else 0
        ch_num = _resolve_chapter_marker(ch_num_token, seed)
        if ch_text.strip():
            chapters.append((ch_num, ch_text))

    out: list[tuple[int, int, str]] = []
    for chapter, chapter_text in chapters:
        # Collapse all whitespace + newlines into single spaces.
        flat = re.sub(r"\s+", " ", chapter_text).strip()
        if not flat:
            continue
        # Split by `።` Ethiopic full stop.
        fragments = flat.split("።")
        verse_num = 0
        for frag in fragments:
            frag = frag.strip()
            # Strip trailing OCR-noise punctuation.
            frag = frag.rstrip("=;|").rstrip()
            if not frag:
                continue
            # Filter cross-reference fragments.
            if is_cross_ref_fragment(frag):
                continue
            # τ.6.x.1.E: filter NT `ክፍል N፡ …` pericope/section headers
            # (long Ethiopic prose the numeral-keyed cross-ref filter
            # misses) so they do not parse as spurious verses.
            if is_pericope_header(frag):
                continue
            # Filter very-short fragments (likely OCR noise — orphan
            # punctuation, single characters, etc.). Body-text verses
            # are typically ≥15 chars even at OCR quality.
            if len(frag) < 10:
                continue
            verse_num += 1
            # Add back the `።` terminator for verse integrity.
            out.append((chapter, verse_num, frag + "።"))
    return out


def normalize_verse_numerals(text: str) -> str:
    """Convert Ethiopic-numeral verse markers at line starts into the
    Arabic-digit+colon form ``parse_verses_from_text()`` expects.

    Operates line-by-line. A line is considered to start with a verse
    marker if it matches `ETHIOPIC_LINE_START_NUMERAL_RE` — leading
    whitespace, one or more Ethiopic numerals (U+1369 … U+137C),
    optional whitespace, then an Ethiopic punctuation mark. The
    matched prefix is replaced with `<arabic_digit>:` so the existing
    `VERSE_NUM_RE` (`^\\s*(\\d+)[.:\\)\\s]`) keys off it unchanged.

    Lines that do NOT match (no Ethiopic numerals; non-verse-marker
    leading content like chapter headers `ምዕራፍ ፡ ፫`) pass through
    unchanged. Text-layer-engine output (Arabic digits) is therefore
    a no-op for this function.

    Returns a new string with the same line count as the input.
    """
    out_lines: list[str] = []
    for line in text.splitlines():
        m = ETHIOPIC_LINE_START_NUMERAL_RE.match(line)
        if m is None:
            out_lines.append(line)
            continue
        ws, ethio, _sep = m.group(1), m.group(2), m.group(3)
        arabic = geez_numeral_to_int(ethio)
        if arabic is None:
            out_lines.append(line)
            continue
        # Replace the matched prefix with `<arabic>:` so VERSE_NUM_RE
        # matches via its `[.:\\)\\s]` separator class. Everything
        # after the matched prefix is preserved.
        out_lines.append(f"{ws}{arabic}:{line[m.end() :]}")
    return "\n".join(out_lines)


def extract_text_by_column(pdf_page) -> tuple[str, str]:
    """Extract the Geʽez (left) and Amharic (right) column text from
    one PDF page via the text-layer engine.

    Uses pymupdf's page.get_text() with bbox-restriction. The split
    point is at 50% of page width.

    Per the source PDF's caveat (``_source.yaml::ocr_caveats``) the
    embedded OCR text layer is BADLY GARBLED for Geʽez; this engine
    is retained for diagnostic comparison and for cases where
    Tesseract is unavailable. The Tesseract engine (τ.6.x.1+) is the
    project's authorized default.

    Returns: (geez_text, amharic_text). Each may be empty.
    """
    rect = pdf_page.rect
    mid_x = rect.x0 + rect.width * 0.50

    left_rect = (rect.x0, rect.y0, mid_x, rect.y1)
    right_rect = (mid_x, rect.y0, rect.x1, rect.y1)

    geez = pdf_page.get_text("text", clip=left_rect)
    amharic = pdf_page.get_text("text", clip=right_rect)
    return geez, amharic


# ───────────────────────────────────────────────────────────────────
# τ.6.x.1 — Tesseract engine helpers
# ───────────────────────────────────────────────────────────────────


def _required_tesseract_languages() -> tuple[str, ...]:
    """The language packs the tesseract engine needs available before
    extraction can run. Pre-flight-checked once per ``extract_section``
    invocation; missing packs short-circuit before any PDF page is
    rendered.
    """
    return (AMH_LANG, GEEZ_LANG)


def _check_tesseract_languages(
    binary: Path,
    required: tuple[str, ...] = (),
) -> list[str]:
    """Run ``tesseract --list-langs`` and return the list of required
    languages that are missing. Empty list means all required packs
    are present.

    ``--list-langs`` formats script-level models as ``script/<name>``
    on POSIX and ``script\\<name>`` on Windows (mirrors the on-disk
    layout). This helper normalizes both forms.

    The subprocess is invoked with ``stdin=subprocess.DEVNULL`` to
    avoid the LIGHT-1 W-W1 Windows-handle-invalid failure mode when
    pytest runs from a stdin-less shell. ``capture_output=True``
    plus ``text=True`` keeps the API simple for the caller.
    """
    result = subprocess.run(
        [str(binary), "--list-langs"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
    )
    combined = (result.stdout or "") + (result.stderr or "")
    raw_langs = {line.strip() for line in combined.splitlines()}
    # Normalize Windows-style backslashes to forward-slashes so callers
    # can compare against the canonical ``script/Ethiopic`` form.
    normalized = {ln.replace("\\", "/") for ln in raw_langs}
    missing: list[str] = []
    for want in required:
        if want.replace("\\", "/") not in normalized:
            missing.append(want)
    return missing


def _render_column_to_png(
    pdf_page,
    side: str,
    dpi: int,
    out_path: Path,
) -> Path:
    """Render either the left (``side='left'``) or right (``side='right'``)
    half of a PDF page to a PNG at ``dpi``. Returns ``out_path``.

    Uses pymupdf's ``page.get_pixmap(matrix=..., clip=...)`` to
    rasterize only the chosen column at the requested resolution.
    The matrix scales the 72-dpi PDF user-space to the target dpi.
    """
    import fitz

    if side not in ("left", "right"):
        raise ValueError(f"side must be 'left' or 'right'; got {side!r}")

    rect = pdf_page.rect
    mid_x = rect.x0 + rect.width * 0.50
    if side == "left":
        clip = fitz.Rect(rect.x0, rect.y0, mid_x, rect.y1)
    else:
        clip = fitz.Rect(mid_x, rect.y0, rect.x1, rect.y1)

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = pdf_page.get_pixmap(matrix=matrix, clip=clip)
    pix.save(str(out_path))
    return out_path


def _run_tesseract_on_png(
    binary: Path,
    png_path: Path,
    lang: str,
    psm: int = 6,
) -> str:
    """Invoke Tesseract on a PNG file with the given language pack and
    return the recognized text from stdout.

    ``psm=6`` ("assume a single uniform block of text") matches the
    column layout of the parallel-Bible PDF — each column is a
    vertical block of verses with consistent baseline orientation.

    Per LIGHT-1 W-W1 mitigation, the subprocess inherits no stdin
    handle (``stdin=subprocess.DEVNULL``). Tesseract is asked to
    write its output to ``stdout`` so no temp output-file dance is
    needed.
    """
    args = [str(binary), str(png_path), "stdout", "-l", lang, "--psm", str(psm)]
    result = subprocess.run(
        args,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    return result.stdout or ""


def tesseract_extract_columns(
    pdf_page,
    binary: Path,
    *,
    dpi: int = OCR_DPI,
    geez_lang: str = GEEZ_LANG,
    amh_lang: str = AMH_LANG,
    tmp_dir: Path | None = None,
) -> tuple[str, str]:
    """Extract the Geʽez (left) and Amharic (right) column text from
    one PDF page via the Tesseract OCR engine.

    Renders each column to a PNG at ``dpi`` (default 350 — per the
    Phase-4 methodology), invokes Tesseract with the appropriate
    per-column language pack, and returns the recognized text.

    ``tmp_dir`` lets the caller share a single ``tempfile.
    TemporaryDirectory()`` across many pages instead of paying the
    create/teardown cost per page. When ``tmp_dir`` is ``None`` a
    local TemporaryDirectory is created and torn down inside the
    function.

    Returns: (geez_text, amharic_text). Each may be empty (e.g. if
    the page is a blank publisher front-matter spread).
    """
    if tmp_dir is None:
        with tempfile.TemporaryDirectory() as tmp:
            return tesseract_extract_columns(
                pdf_page,
                binary,
                dpi=dpi,
                geez_lang=geez_lang,
                amh_lang=amh_lang,
                tmp_dir=Path(tmp),
            )

    left_png = tmp_dir / "left.png"
    right_png = tmp_dir / "right.png"
    _render_column_to_png(pdf_page, "left", dpi, left_png)
    _render_column_to_png(pdf_page, "right", dpi, right_png)

    geez = _run_tesseract_on_png(binary, left_png, geez_lang)
    amharic = _run_tesseract_on_png(binary, right_png, amh_lang)
    return geez, amharic


def parse_verses_from_text(text: str, *, paragraph_mode: bool = False) -> list[tuple[int, int, str]]:
    """Parse one column's text into (chapter, verse, text) tuples.

    Strategy (single-line mode; ``paragraph_mode=False``, the default):
    - τ.6.x.1.B: pre-normalize Ethiopic-numeral verse markers at line
      starts (e.g. `፪፤ …` → `2: …`) so the Arabic-digit regex below
      keys off either numeral system. No-op for text-layer-engine
      output (Arabic-digit-only).
    - Track current chapter (starts at 1 if no ምዕራፍ marker seen).
    - When we see ምዕራፍ ፪, switch to chapter 2, etc.
    - When we see a line starting with a digit (e.g. "1 በመጀመሪያ..."
      OR "1፣ በመጀመሪያ..."), start a new verse.
    - Accumulate text lines into the current verse until the next
      verse marker.

    Strategy (paragraph mode; ``paragraph_mode=True``, τ.6.x.1.C):
    - τ.6.x.1.B pre-normalization still applies but is typically a
      no-op since paragraph-mode is used for standard-canon books
      that have no leading verse markers at all.
    - Split chapter content by `።` Ethiopic full-stop; each non-
      empty fragment is a candidate verse.
    - Filter out cross-reference fragments via `is_cross_ref_fragment`
      (short numeral-dominated strings matching biblical-citation
      patterns).
    - Number candidate verses sequentially within each chapter.

    Use paragraph_mode for standard-canon books (Genesis, Exodus, ...)
    per the τ.7.x.a.0 PILOT empirical finding; use the default mode
    for Tewahedo-distinctive books (Meqabyan, Jubilees, 1 Enoch) where
    verse-number prefixes are present in the source.
    """
    text = normalize_verse_numerals(text)

    if paragraph_mode:
        return _parse_paragraph_mode(text)

    chapter = 1
    verse = 0
    current_text: list[str] = []
    out: list[tuple[int, int, str]] = []

    def _flush() -> None:
        if verse > 0 and current_text:
            txt = " ".join(current_text).strip()
            txt = re.sub(r"\s+", " ", txt)
            if txt:
                out.append((chapter, verse, txt))

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Skip page-header garbage (English page headers in margins
        # like "www.ethiopianorthodox.org" or "The Ethiopian Orthodox
        # Tewahido Church"). These are PURE ASCII with no Ethiopic
        # characters. Verse-text lines mix Ethiopic + numerals so are
        # not filtered out here.
        has_ethiopic = any(0x1200 <= ord(c) <= 0x137F for c in line)
        if not has_ethiopic and re.search(r"[a-zA-Z]{4,}", line):
            continue

        # Check for chapter header.
        m_ch = CHAPTER_HEADER_RE.search(line)
        if m_ch:
            _flush()
            new_ch = geez_numeral_to_int(m_ch.group(1))
            if new_ch is not None:
                chapter = new_ch
                verse = 0
                current_text = []
                continue

        # Check for verse number.
        m_v = VERSE_NUM_RE.match(line)
        if m_v:
            _flush()
            verse = int(m_v.group(1))
            # Remainder of the line is the start of the verse text.
            remainder = line[m_v.end() :].strip()
            current_text = [remainder] if remainder else []
            continue

        # Continuation of current verse.
        if verse > 0:
            current_text.append(line)

    _flush()
    return out


# τ.7.x.a — Post-process renumbering against a known verse-count floor.
#
# The τ.6.x.1.D residual: when the lenient chapter-marker regex still
# misses a marker (because OCR garbled the keyword past `ም[ዕፅ]ራፍ`
# tolerance — e.g. `ራፍ` alone or substituted glyphs), the parser
# bundles verses from multiple actual chapters into a single parser
# bucket. For long books (Genesis: 50 chapters, 1534 verses) the
# parser detects ~16-22 chapter markers, leaving 28-34 chapter
# boundaries collapsed.
#
# The fix: post-process the parser's output by discarding its chapter
# labels and assigning verses sequentially into canonical chapters
# whose verse-counts are known. `GENESIS_VERSE_COUNTS` provides the
# floor for Genesis; the same pattern works for any book once its
# canonical verse-count dict is provided.
#
# Trade-off: individual verse content may misalign by 1-3 verses
# per chapter (because the parser merged some verses past `።` or
# dropped fragments below the 10-char filter). The chapter+verse
# INDEX, however, is canonical — popup lookups for (gen, 1, 1) get
# the FIRST verse in source order, which is reader-expected. Cross-
# checking against an independent reference (KJV, BHS, LXX) at
# τ.6.x.3 batched audit will surface and correct the residual.
def renumber_against_floor(
    verses: list[tuple[int, int, str]],
    verse_counts: dict[int, int],
) -> list[tuple[int, int, str]]:
    """Re-assign (chapter, verse) labels by sequentially filling chapters
    per ``verse_counts`` (e.g. ``GENESIS_VERSE_COUNTS``).

    The input ``verses`` are expected in SOURCE ORDER (parser's natural
    page-by-page output). Their existing chapter labels are DISCARDED.
    Each input verse becomes the next sequential verse in the next
    canonical chapter — chapter 1 receives ``verse_counts[1]`` verses,
    then chapter 2 receives ``verse_counts[2]``, etc.

    If the input has FEWER verses than ``sum(verse_counts.values())``,
    later chapters end up with PARTIAL or zero coverage. If the input
    has MORE verses, excess verses overflow into a synthesized "ch_max+1"
    bucket (still in the returned list; downstream consumers can choose
    to drop, log, or keep them).

    Chapters with zero received verses are omitted from the output (no
    placeholders). The returned list is in canonical (ch, v) order.

    Parameters
    ----------
    verses : list of (chapter, verse, text)
        Parser output (chapter labels treated as untrusted). Source
        order is preserved during redistribution.
    verse_counts : dict[int, int]
        Canonical chapter → expected verse count mapping (e.g.
        ``GENESIS_VERSE_COUNTS``). Chapters processed in
        ``sorted(verse_counts.keys())`` order.

    Returns
    -------
    list of (chapter, verse, text)
        Renumbered verses; the text is unchanged, only labels are
        reassigned.
    """
    if not verses:
        return []
    out: list[tuple[int, int, str]] = []
    flat = [(c, v, t) for (c, v, t) in verses]  # local copy to iterate
    idx = 0
    n_in = len(flat)
    for ch in sorted(verse_counts.keys()):
        target = verse_counts[ch]
        for v in range(1, target + 1):
            if idx >= n_in:
                break
            _, _, text = flat[idx]
            out.append((ch, v, text))
            idx += 1
        if idx >= n_in:
            break
    # Overflow handling. A clean parse is always ≤ the canonical floor
    # (the floor is the per-chapter MAXIMUM verse count), so a few
    # residual fragments past the floor are tolerable ocr-tier3 noise
    # and keep the historical ch_max+1 bucketing. GROSS overflow,
    # however, means the parse produced structurally-wrong segments
    # (NT pericope/cross-ref apparatus, or Ge'ez colometric `።`-per-
    # colon poetry). Silently bucketing that into ch_max+1 ships
    # distorted scripture behind a false "all chapters full" signal —
    # the τ.6.x.0b honesty contract requires a HARD failure instead
    # (τ.6.x.1.E). Threshold: max(10, 2% of the floor total).
    if idx < n_in:
        overflow = n_in - idx
        total_expected = sum(verse_counts.values())
        tolerance = max(10, int(0.02 * total_expected))
        if overflow > tolerance:
            raise ValueError(
                "renumber_against_floor: GROSS over-segmentation — "
                f"{n_in} parsed verses vs a {total_expected}-verse "
                f"floor ({overflow} overflow > {tolerance} tolerance). "
                "This is the τ.7.x.v / τ.6.x.2.i bug class: the OT-"
                "narrative-tuned `።`/paragraph parser hit structurally-"
                "different scripture (NT pericope/cross-ref apparatus, "
                "or the Ge'ez colometric Psalter). Refusing to ship "
                "distorted scripture behind a false 'all chapters full' "
                "signal (τ.6.x.0b honesty contract). Apply the "
                "structure-aware pre-pass / colometric merge before "
                "renumbering this book."
            )
        ch_overflow = max(verse_counts.keys()) + 1
        v_overflow = 0
        while idx < n_in:
            _, _, text = flat[idx]
            v_overflow += 1
            out.append((ch_overflow, v_overflow, text))
            idx += 1
    return out


# ───────────────────────────────────────────────────────────────────
# Section extraction
# ───────────────────────────────────────────────────────────────────


# Π.1 introduced metadata keys at the same dict level as real section
# entries (e.g. `tewahedo_distinctive_inventory`). A real section has a
# `book_codes` list; metadata keys do not. This helper filters the
# structural_map dict down to the real extraction sections so the CLI
# can list them, iterate them, and look-up pilot-book → section without
# stumbling over metadata.
_METADATA_KEYS = frozenset({"tewahedo_distinctive_inventory"})


def _extraction_sections(cfg: dict) -> list[str]:
    """Return the names of structural_map entries that represent real
    extractable book sections (each has a `book_codes` list). Filters
    out Π.1+ inventory/metadata keys that share the namespace."""
    out: list[str] = []
    for name, sec in (cfg.get("structural_map") or {}).items():
        if name in _METADATA_KEYS:
            continue
        if not isinstance(sec, dict):
            continue
        if not sec.get("book_codes"):
            continue
        out.append(name)
    return out


def _resolve_section(cfg: dict, section_name: str) -> dict:
    """Look up a section in structural_map; SystemExit with a helpful
    list if missing, and SystemExit with the alternate-source guidance
    if it's a present_in_pdf=False slot like `laodiceans`."""
    sec = (cfg.get("structural_map") or {}).get(section_name)
    if not sec:
        raise SystemExit(
            f"FATAL: section {section_name!r} not in _source.yaml::structural_map. "
            f"Available: {sorted(_extraction_sections(cfg))}"
        )
    if sec.get("present_in_pdf") is False or sec.get("pdf_page_range") is None:
        raise SystemExit(
            f"FATAL: section {section_name!r} declares present_in_pdf=False "
            f"or has no pdf_page_range. Per the _source.yaml::structural_map "
            f"{section_name}.notes, this book requires an ALTERNATE SOURCE "
            f"(not the parallel-Bible PDF). Do not run extract_parallel_pdf "
            f"against it; consult content/translations/sources/parallel-bible-eotc/"
            f"_source.yaml for acquisition options."
        )
    return sec


def _section_page_range(sec: dict) -> tuple[int, int, int]:
    """Resolve a section's (page_start, page_end, offset). Supports
    both the canonical `pdf_page_range` (0-indexed; offset 0) and the
    legacy τ.6.x.0 `scan_page_range` (archive.org scan-page numbers;
    requires `pdf_index_offset`)."""
    if "pdf_page_range" in sec:
        page_start, page_end = sec["pdf_page_range"]
        return page_start, page_end, 0
    page_start, page_end = sec["scan_page_range"]
    return page_start, page_end, sec.get("pdf_index_offset", 0)


def _resolve_tesseract_or_exit() -> Path:
    """Resolve the Tesseract binary via ``scripts.core.paths.
    tesseract_binary()`` and SystemExit with a clear install-pointer
    if the resolver returns ``None``.
    """
    from scripts.core.paths import tesseract_binary

    binary = tesseract_binary()
    if binary is None:
        raise SystemExit(
            "FATAL: --engine tesseract requires Tesseract OCR to be installed.\n"
            "\n"
            "The scripts.core.paths.tesseract_binary() resolver could not find it on:\n"
            "  - TESSERACT_BIN env-var override\n"
            "  - PATH (shutil.which)\n"
            "  - Windows: C:\\Program Files\\Tesseract-OCR\\tesseract.exe\n"
            "  - macOS:   /opt/homebrew/bin/tesseract, /usr/local/bin/tesseract\n"
            "  - Linux:   /usr/bin/tesseract, /usr/local/bin/tesseract\n"
            "\n"
            "Install options:\n"
            "  Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "  macOS:   brew install tesseract tesseract-lang\n"
            "  Linux:   apt-get install tesseract-ocr tesseract-ocr-amh\n"
            "\n"
            "Or pass --engine text-layer to use the PDF's embedded text layer\n"
            "(garbled for Geʽez but functional for diagnostic comparison)."
        )
    return binary


def _verify_tesseract_languages_or_exit(binary: Path) -> None:
    """Pre-flight ``tesseract --list-langs`` and SystemExit if any
    required language pack is missing. Empty list means all required
    packs are present.
    """
    missing = _check_tesseract_languages(binary, _required_tesseract_languages())
    if not missing:
        return
    raise SystemExit(
        "FATAL: --engine tesseract requires the following language packs "
        "which are NOT present in this Tesseract install:\n" + "\n".join(f"  - {ln}" for ln in missing) + "\n\n"
        "Install via the Tesseract installer's optional-languages step, "
        "or manually drop the corresponding .traineddata file into the "
        "tessdata directory of the install. For the UB-Mannheim Windows\n"
        "build, that path is "
        "``C:\\Program Files\\Tesseract-OCR\\tessdata\\``.\n\n"
        "Sources for traineddata files:\n"
        "  - https://github.com/tesseract-ocr/tessdata_fast\n"
        "  - https://github.com/tesseract-ocr/tessdata_best\n"
    )


def extract_section(
    cfg: dict,
    section_name: str,
    pilot_filter: str | None = None,
    engine: str = ENGINE_DEFAULT,
    paragraph_mode: bool = False,
    renumber_floor: dict[int, int] | None = None,
) -> dict[str, dict[str, list[tuple[int, int, str]]]]:
    """Extract one structural_map section from the PDF.

    Returns:
        {
            "<book_code>": {
                "geez":    [(ch, v, text), ...],
                "amharic": [(ch, v, text), ...],
            },
            ...
        }

    `pilot_filter` is a string like "mq1-ch1" that restricts output
    to a single book + chapter for testing.

    `engine` is one of:
        - "tesseract" (default per τ.6.x.0b Option-D-Hybrid
          authorization) — render columns at 350 dpi via pymupdf,
          invoke Tesseract once per column with the per-column
          language pack (script/Ethiopic + amh).
        - "text-layer" — consume the PDF's embedded OCR text layer
          directly (legacy τ.6.x.0a behavior).
    """
    if engine not in ENGINE_CHOICES:
        raise ValueError(f"engine must be one of {ENGINE_CHOICES!r}; got {engine!r}")

    import fitz

    sec = _resolve_section(cfg, section_name)
    page_start, page_end, offset = _section_page_range(sec)
    book_codes = sec["book_codes"]

    # Tesseract engine: resolve the binary and verify required language
    # packs UPFRONT, before opening the (large) PDF. This fails fast
    # with a clean install pointer rather than a mid-extract crash.
    tesseract_bin: Path | None = None
    if engine == ENGINE_TESSERACT:
        tesseract_bin = _resolve_tesseract_or_exit()
        _verify_tesseract_languages_or_exit(tesseract_bin)

    pdf_path = resolve_pdf_path(cfg)
    print(f"  source PDF: {pdf_path}")
    print(f"  section: {section_name} (PDF pages {page_start}-{page_end})")
    print(f"  books: {', '.join(book_codes)}")
    print(f"  engine: {engine}")
    if engine == ENGINE_TESSERACT:
        print(f"  tesseract: {tesseract_bin}")
        print(f"  ocr_dpi: {OCR_DPI}")

    # For pilot mode, restrict the page range to just the pilot book's
    # sub-range if a `subsections` map is present in the section.
    # This is essential because parsing 60+ pages of multi-book text
    # without book-boundary detection produces tangled output.
    if pilot_filter:
        pilot_book = pilot_filter.split("-ch")[0] if "-ch" in pilot_filter else pilot_filter
        # Π.1 hoisted the meqabyan subsections into the declarative
        # _source.yaml; jubilees + one_enoch are single-book sections
        # so subsections doesn't apply. Prefer the declarative form;
        # the heuristic remains as a safety net for back-compat.
        subs = sec.get("subsections") or {}
        if pilot_book in subs:
            page_start, page_end = subs[pilot_book]
            print(f"  pilot narrowing: book {pilot_book} → pages {page_start}-{page_end}")
        elif len(book_codes) == 1 and pilot_book == book_codes[0]:
            # Single-book section — the section page range IS the book
            # page range. No narrowing needed.
            print(f"  pilot narrowing: book {pilot_book} = section {section_name} (single-book)")
        else:
            # Heuristic fallback for the meqabyan section based on
            # τ.6.x.0a verified ranges. Retained as a safety net even
            # though Π.1 hoisted them into the declarative subsections
            # map above; this fires only if subsections is removed or
            # malformed in _source.yaml.
            # τ.7.x.n-corrected (was mq1[1318,1365]/mq2[1366,1372]/
            # mq3[1373,1378] — the coarse τ.6.x.0a approximate scan;
            # corrected by τ.7.x.n content-boundary inspection, see
            # _source.yaml::structural_map.meqabyan.subsections).
            heuristic = {
                ("meqabyan", "mq1"): (1318, 1350),
                ("meqabyan", "mq2"): (1351, 1368),
                ("meqabyan", "mq3"): (1369, 1378),
            }
            key = (section_name, pilot_book)
            if key in heuristic:
                page_start, page_end = heuristic[key]
                print(f"  pilot narrowing (heuristic): book {pilot_book} → pages {page_start}-{page_end}")

    doc = fitz.open(str(pdf_path))
    try:
        all_geez = []
        all_amh = []
        # Share one TemporaryDirectory across pages so we don't pay
        # per-page mkdir/rmdir cost for the Tesseract path.
        if engine == ENGINE_TESSERACT:
            tmp_ctx = tempfile.TemporaryDirectory()
            tmp_dir: Path | None = Path(tmp_ctx.name)
        else:
            tmp_ctx = None
            tmp_dir = None
        try:
            for scan_page in range(page_start, page_end + 1):
                idx = scan_page - offset
                if idx < 0 or idx >= len(doc):
                    continue
                page = doc[idx]
                if engine == ENGINE_TESSERACT:
                    assert tesseract_bin is not None  # narrowed by engine check above
                    g, a = tesseract_extract_columns(
                        page,
                        tesseract_bin,
                        dpi=OCR_DPI,
                        geez_lang=GEEZ_LANG,
                        amh_lang=AMH_LANG,
                        tmp_dir=tmp_dir,
                    )
                else:
                    g, a = extract_text_by_column(page)
                all_geez.append(g)
                all_amh.append(a)
        finally:
            if tmp_ctx is not None:
                tmp_ctx.cleanup()
        full_geez = "\n".join(all_geez)
        full_amh = "\n".join(all_amh)
    finally:
        doc.close()

    geez_verses = parse_verses_from_text(full_geez, paragraph_mode=paragraph_mode)
    amh_verses = parse_verses_from_text(full_amh, paragraph_mode=paragraph_mode)

    # τ.7.x.a — Optional post-process renumbering against a known
    # verse-count floor. When the parser misses chapter markers (the
    # τ.6.x.1.D residual), bundle verses into canonical chapters by
    # filling each per its expected count in source order.
    if renumber_floor is not None:
        geez_verses = renumber_against_floor(geez_verses, renumber_floor)
        amh_verses = renumber_against_floor(amh_verses, renumber_floor)

    # NOTE: this naive parse does not yet know book-boundaries
    # within a multi-book section (e.g. Meqabyan spans 3 books).
    # For the τ.6.x.0b pilot we extract per-book by RESTRICTING the
    # scan range to a single book's pages. The full multi-book
    # within-section split is a τ.6.x.0c task.
    by_book: dict[str, dict[str, list]] = {}

    # Pilot mode: single book + single chapter
    if pilot_filter:
        if "-ch" in pilot_filter:
            bc, chpart = pilot_filter.split("-ch")
            ch = int(chpart)
            if bc in book_codes:
                by_book[bc] = {
                    "geez": [(c, v, t) for (c, v, t) in geez_verses if c == ch],
                    "amharic": [(c, v, t) for (c, v, t) in amh_verses if c == ch],
                }
    else:
        # All in the section get bundled into the first book code
        # — this is the τ.6.x.0a-tier naive split; τ.6.x.0c will add
        # multi-book within-section partitioning by detecting the
        # መቃብያን ፪ / መቃብያን ፫ dividers.
        by_book[book_codes[0]] = {
            "geez": geez_verses,
            "amharic": amh_verses,
        }

    return by_book


# ───────────────────────────────────────────────────────────────────
# Output writing
# ───────────────────────────────────────────────────────────────────


def write_book_module(
    translation: str,
    book: str,
    verses: list[tuple[int, int, str]],
    source_quality: str,
    extraction_date: str,
    *,
    ingest_phase: str | None = None,
    docstring_extra: str | None = None,
) -> Path:
    """Write content/translations/<translation>/<book>.py with the
    verse data + provenance metadata.

    Parameters
    ----------
    translation, book, verses, source_quality, extraction_date
        Core fields (as before).
    ingest_phase
        Optional phase tag to record alongside extraction_date (e.g.
        ``"τ.7.x.a"``). When set, written into the file as
        ``INGEST_PHASE`` constant + referenced in the docstring.
    docstring_extra
        Optional additional docstring text appended after the generic
        provenance lines (book-specific quality notes, renumbering
        provenance, residual-issue documentation). Use for τ.7.x.a-
        style ingests that have non-generic quality residue worth
        flagging in-line.
    """
    out = TRANSLATIONS_DIR / translation / f"{book}.py"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f'"""Translation: {translation} · Book: {book}',
        "",
        "Extracted from the parallel-Bible EOTC PDF (",
        "content/translations/sources/parallel-bible-eotc/_source.yaml).",
        "",
        f"Source quality: {source_quality}",
        f"Extraction date: {extraction_date}",
    ]
    if ingest_phase:
        lines.append(f"Ingest phase: {ingest_phase}")
    lines.append("Tool: scripts/extract_parallel_pdf.py")
    if docstring_extra:
        lines.append("")
        for ln in docstring_extra.splitlines():
            lines.append(ln.rstrip())
    lines.extend(['"""', ""])
    lines.append(f"TRANSLATION = {translation!r}")
    lines.append(f"BOOK = {book!r}")
    lines.append(f"SOURCE_QUALITY = {source_quality!r}")
    lines.append("SOURCE_PROVENANCE = 'parallel-bible-eotc'")
    lines.append(f"EXTRACTION_DATE = {extraction_date!r}")
    if ingest_phase:
        lines.append(f"INGEST_PHASE = {ingest_phase!r}")
    lines.append("VERSES = [")
    for ch, v, text in verses:
        # τ.7.x.t fix: serialize via repr() so backslashes, quotes,
        # and control chars in ocr-tier3 OCR text are escaped
        # canonically. The prior manual `'...'.replace("'", "\\'")`
        # only escaped single-quotes — a literal OCR backslash
        # produced an invalid escape sequence (SyntaxWarning for
        # `\ `; silent data corruption for `\n`/`\t`/`\x...`). For
        # text without backslashes/quotes/control chars the post-
        # generation ruff-format normalizes repr() output to the
        # identical double-quoted form prior books already carry, so
        # this is forward-correct with no churn on clean text.
        lines.append(f"    ({ch}, {v}, {text!r}),")
    lines.append("]")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


# ───────────────────────────────────────────────────────────────────
# CLI
# ───────────────────────────────────────────────────────────────────


def _build_docstring_extra(
    *,
    book: str,
    lang: str,
    verses: list[tuple[int, int, str]],
    paragraph_mode: bool,
    renumber: str | None,
) -> str | None:
    """Compose a book-specific docstring extension for ``write_book_module``.

    Returns None when no extension is warranted (default-mode + no
    renumber path, where the generic provenance lines suffice).

    For τ.7.x.a Genesis (paragraph_mode + renumber=genesis) the returned
    string summarizes per-chapter coverage + flags missing chapters.
    """
    if not paragraph_mode and not renumber:
        return None

    lines: list[str] = []
    if paragraph_mode:
        lines.append("Parser mode: paragraph (τ.6.x.1.C — splits verses by `።` Ethiopic full-stop")
        lines.append("and τ.6.x.1.D lenient chapter-marker regex tolerating OCR-garbled keywords).")
    if renumber:
        lines.append(f"Renumbering: post-process renumbered against {renumber!r} verse-count floor (τ.7.x.a+).")
        lines.append("Parser chapter labels discarded; verses assigned sequentially to canonical chapters.")

    floor_dict = None
    if renumber == "genesis":
        floor_dict = GENESIS_VERSE_COUNTS
    elif renumber == "exodus":
        floor_dict = EXODUS_VERSE_COUNTS
    elif renumber == "leviticus":
        floor_dict = LEVITICUS_VERSE_COUNTS
    elif renumber == "numbers":
        floor_dict = NUMBERS_VERSE_COUNTS
    elif renumber == "deuteronomy":
        floor_dict = DEUTERONOMY_VERSE_COUNTS
    elif renumber == "joshua":
        floor_dict = JOSHUA_VERSE_COUNTS
    elif renumber == "judges":
        floor_dict = JUDGES_VERSE_COUNTS
    elif renumber == "ruth":
        floor_dict = RUTH_VERSE_COUNTS
    elif renumber == "psalms":
        floor_dict = PSALMS_VERSE_COUNTS
    elif renumber == "ezra_sutuel":
        floor_dict = EZRA_SUTUEL_VERSE_COUNTS
    elif renumber == "tobit":
        floor_dict = TOBIT_VERSE_COUNTS
    elif renumber == "judith":
        floor_dict = JUDITH_VERSE_COUNTS
    elif renumber == "esther":
        floor_dict = ESTHER_VERSE_COUNTS
    elif renumber == "meqabyan_i":
        floor_dict = MQ1_VERSE_COUNTS
    elif renumber == "meqabyan_ii":
        floor_dict = MQ2_VERSE_COUNTS
    elif renumber == "meqabyan_iii":
        floor_dict = MQ3_VERSE_COUNTS
    elif renumber == "sirach":
        floor_dict = SIRACH_VERSE_COUNTS
    elif renumber == "four_baruch":
        floor_dict = FOUR_BARUCH_VERSE_COUNTS
    elif renumber == "baruch":
        floor_dict = BARUCH_VERSE_COUNTS
    elif renumber == "wisdom_of_solomon":
        floor_dict = WISDOM_OF_SOLOMON_VERSE_COUNTS
    elif renumber == "prayer_of_azariah":
        floor_dict = PRAYER_OF_AZARIAH_VERSE_COUNTS
    elif renumber == "susanna":
        floor_dict = SUSANNA_VERSE_COUNTS
    elif renumber == "bel_and_the_dragon":
        floor_dict = BEL_AND_THE_DRAGON_VERSE_COUNTS
    elif renumber == "jubilees":
        floor_dict = JUBILEES_VERSE_COUNTS
    elif renumber == "one_enoch":
        floor_dict = ONE_ENOCH_VERSE_COUNTS
    elif renumber == "matthew":
        floor_dict = MATTHEW_VERSE_COUNTS

    if floor_dict is not None and verses:
        # Per-chapter coverage summary
        from collections import Counter

        counts = Counter(c for (c, _, _) in verses)
        floor = floor_dict
        total_actual = sum(counts.values())
        total_expected = sum(floor.values())
        pct = 100.0 * total_actual / total_expected if total_expected else 0.0
        full = sorted(c for c in floor if counts.get(c, 0) >= floor[c])
        partial = sorted(c for c in floor if 0 < counts.get(c, 0) < floor[c])
        missing = sorted(c for c in floor if counts.get(c, 0) == 0)
        lines.append("")
        lines.append(f"Coverage: {total_actual}/{total_expected} verses ({pct:.1f}%) at ocr-tier3 quality.")
        if full:
            lines.append(f"Chapters fully populated ({len(full)}): {_pretty_range(full)}.")
        if partial:
            partial_detail = ", ".join(f"{c}:{counts[c]}/{floor[c]}" for c in partial)
            lines.append(f"Chapters partial: {partial_detail}.")
        if missing:
            lines.append(f"Chapters missing ({len(missing)}): {_pretty_range(missing)} — at ocr-tier3 the parser ran")
            lines.append("out of recovered verses before reaching these; τ.6.x.3 batched audit cross-checks.")
    return "\n".join(lines) if lines else None


def _pretty_range(nums: list[int]) -> str:
    """Render a sorted list of ints as a compact range string.

    e.g. [1,2,3,5,6] → "1-3, 5-6"; [44,45,46,47,48,49,50] → "44-50".
    """
    if not nums:
        return ""
    parts: list[str] = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        parts.append(f"{start}" if start == prev else f"{start}-{prev}")
        start = prev = n
    parts.append(f"{start}" if start == prev else f"{start}-{prev}")
    return ", ".join(parts)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--section", help="structural_map section name (e.g. 'meqabyan')")
    p.add_argument("--pilot", help="pilot mode: <book>-ch<N> (e.g. 'mq1-ch1')")
    p.add_argument("--dry-run", action="store_true", help="extract + report; do not write")
    p.add_argument("--overwrite", action="store_true", help="overwrite existing output files")
    p.add_argument("--quality", default="ocr-tier3", help="SOURCE_QUALITY tier (default: ocr-tier3)")
    p.add_argument(
        "--engine",
        default=ENGINE_DEFAULT,
        choices=list(ENGINE_CHOICES),
        help=(
            "extraction engine (default: tesseract per τ.6.x.0b Option-D-Hybrid). "
            "'tesseract' renders each PDF column to PNG at 350 dpi and OCRs with "
            "script/Ethiopic + amh language packs. 'text-layer' reads the PDF's "
            "embedded OCR text (legacy τ.6.x.0a behavior; garbled for Geʽez)."
        ),
    )
    p.add_argument(
        "--paragraph-mode",
        action="store_true",
        help=(
            "Use paragraph-mode parser (τ.6.x.1.C) — split verses by `።` "
            "Ethiopic full-stop and number sequentially within each chapter. "
            "Required for standard-canon books (Genesis, etc.) per the "
            "τ.7.x.a.0 PILOT empirical finding; leave OFF for Tewahedo-"
            "distinctive sections (Meqabyan, Jubilees, 1 Enoch) that carry "
            "explicit Ethiopic-numeral verse prefixes in the source."
        ),
    )
    p.add_argument(
        "--renumber",
        default=None,
        choices=[
            "genesis",
            "exodus",
            "leviticus",
            "numbers",
            "deuteronomy",
            "joshua",
            "judges",
            "ruth",
            "psalms",
            "ezra_sutuel",
            "tobit",
            "judith",
            "esther",
            "meqabyan_i",
            "meqabyan_ii",
            "meqabyan_iii",
            "sirach",
            "four_baruch",
            "baruch",
            "wisdom_of_solomon",
            "prayer_of_azariah",
            "susanna",
            "bel_and_the_dragon",
            "jubilees",
            "one_enoch",
            "matthew",
        ],
        help=(
            "Post-process renumber verses against a canonical chapter "
            "verse-count floor (τ.7.x.a writer-side residual handler). "
            "Supports 'genesis' (GENESIS_VERSE_COUNTS, 50 ch / 1534 v), "
            "'exodus' (EXODUS_VERSE_COUNTS, 40 ch / 1213 v; τ.7.x.b), "
            "'leviticus' (LEVITICUS_VERSE_COUNTS, 27 ch / 859 v; τ.7.x.c), "
            "'numbers' (NUMBERS_VERSE_COUNTS, 36 ch / 1288 v; τ.7.x.d), "
            "'deuteronomy' (DEUTERONOMY_VERSE_COUNTS, 34 ch / 959 v; "
            "τ.7.x.e — CLOSED the §8.1 Pentateuch arc), 'joshua' "
            "(JOSHUA_VERSE_COUNTS, 24 ch / 658 v; τ.7.x.f — OPENS the "
            "post-Pentateuch historical-books arc), 'judges' "
            "(JUDGES_VERSE_COUNTS, 21 ch / 618 v; τ.7.x.g — CONTINUES "
            "the post-Pentateuch historical-books arc), 'ruth' "
            "(RUTH_VERSE_COUNTS, 4 ch / 85 v; τ.7.x.h — CONTINUES the "
            "post-Pentateuch historical-books arc; SHORTEST canonical "
            "OT book), and 'psalms' (PSALMS_VERSE_COUNTS, 151 ch / "
            "2551 v under LXX/Tewahedo enumeration; τ.7.x.i — SKIPS "
            "the 438-802 dzamaragna gap and resumes the parallel-"
            "Bible-EOTC scan at p803; LARGEST canonical OT book + "
            "biggest τ.7.x.* per-book ingest to date), 'ezra_sutuel' "
            "(EZRA_SUTUEL_VERSE_COUNTS, 16 ch / 945 v; 2 Esdras / "
            "4 Ezra / መጽሐፈ ዕዝራ ሱቱኤል; τ.7.x.j — FIRST deuterocanonical "
            "τ.7.x.* floor; drains the p1239-1293 EOTC-parallel block), "
            "'tobit' (TOBIT_VERSE_COUNTS, 14 ch / 246 v; "
            "መጽሐፈ ጦቢት; τ.7.x.k — second deuterocanonical book in the "
            "p1239-1293 block), 'judith' (JUDITH_VERSE_COUNTS, 16 ch "
            "/ 339 v; መጽሐፈ ዮዲት; τ.7.x.l — third deuterocanonical "
            "τ.7.x.* floor; drains the p1294-1317 EOTC-parallel block), "
            "and 'esther' (ESTHER_VERSE_COUNTS, 10 ch / 167 v; "
            "መጽሐፈ አስቴር; τ.7.x.m — Hebrew Esther core sourced from the "
            "EOTC-parallel block p1308-1317, the documented alternative "
            "to the τ.7.x.i dzamaragna-gap Esther), and the Mäqabyan "
            "trilogy 'meqabyan_i' (MQ1_VERSE_COUNTS, 36 ch / 502 v), "
            "'meqabyan_ii' (MQ2_VERSE_COUNTS, 21 ch / 256 v), "
            "'meqabyan_iii' (MQ3_VERSE_COUNTS, 10 ch / 188 v) — "
            "τ.7.x.n; FIRST Tewahedo-distinctive + FIRST multi-book "
            "EOTC-parallel block (p1318-1378); floors derived by the "
            "δ.1.x per-chapter-max-verse method (γ.4.8.F Wright 1877 + "
            "Cowley 1974b apparatus); ocr-tier3 + EXPLICITLY δ.1.x-"
            "replaceable per the QUALITY POLICY. Also 'sirach' "
            "(SIRACH_VERSE_COUNTS, 51 ch / 1413 v; NRSV/Göttingen-"
            "Ziegler LXX Ecclesiasticus; τ.7.x.o — FIRST book of the "
            "sixth EOTC-parallel block p1379+) and 'four_baruch' "
            "(FOUR_BARUCH_VERSE_COUNTS, 9 ch / 191 v; Kraft-Purintun "
            "1972 Paralipomena Jeremiou / 4 Baruch; τ.7.x.p — drains "
            "the sixth block before Wisdom of Solomon). Also 'baruch' "
            "(BARUCH_VERSE_COUNTS, 5 ch / 141 v; NRSV/LXX The Book of "
            "Baruch; τ.7.x.q — FIRST book of the seventh EOTC-parallel "
            "block; the Letter of Jeremiah is the SEPARATE `lje` book) "
            "and 'wisdom_of_solomon' (WISDOM_OF_SOLOMON_VERSE_COUNTS, "
            "19 ch / 436 v; NRSV/Göttingen-Ziegler LXX; τ.7.x.r — "
            "drains the bar+wis major-book pair before the Daniel-"
            "additions cluster paz/sus/bel). Also the Daniel-additions "
            "'prayer_of_azariah' (PRAYER_OF_AZARIAH_VERSE_COUNTS, 1 ch "
            "/ 68 v; NRSV Prayer of Azariah + Song of the Three; "
            "τ.7.x.s — OPENS the ተረፈ-ዳንኤል cluster p1449-1451), "
            "'bel_and_the_dragon' (BEL_AND_THE_DRAGON_VERSE_COUNTS, "
            "1 ch / 42 v; NRSV; τ.7.x.s — DRAINS the cluster p1452-"
            "1453; p1454 opens Jubilees, Π.1-cross-validated), and "
            "'susanna' (SUSANNA_VERSE_COUNTS, 1 ch / 64 v; NRSV/"
            "Theodotion — infra-ready but DEFERRED at τ.7.x.s: the "
            "structural-discovery scan found Susanna NOT distinctly "
            "present in this PDF's ተረፈ-ዳንኤል cluster, the τ.7.x.q "
            "`lje` + `laodiceans` present_in_pdf:false precedent; "
            "reconciled at τ.6.x.3 / the future `dan` ingest). Also "
            "the Tewahedo-distinctive 'jubilees' (JUBILEES_VERSE_"
            "COUNTS, 50 ch / 1306 v; R.H. Charles 1913 / VanderKam "
            "1989 CSCO — Mäṣḥafä Kufāle / The Little Genesis; "
            "τ.7.x.t — FIRST of the two LARGE Π.1-mapped Tewahedo-"
            "distinctive books, p1454-1514; upgrades structural_map."
            "jubilees verified:tentative→true Π.1→τ.7.x.t; 1 Enoch "
            "[1515,1566] follows as τ.7.x.u). Also the Tewahedo-"
            "distinctive 'one_enoch' (ONE_ENOCH_VERSE_COUNTS, 108 ch "
            "/ 1064 v; R.H. Charles 1912 — Mäṣḥafä Hēnok / 1 Enoch; "
            "τ.7.x.u — SECOND of the two LARGE Π.1-mapped Tewahedo-"
            "distinctive books, p1515-1566; upgrades structural_map."
            "one_enoch verified:tentative→true Π.1→τ.7.x.u; floor "
            "hard-validated ≥ the γ.4.4 notes/1en.py maxima at all "
            "108 ch). Also the NT-opener 'matthew' "
            "(MATTHEW_VERSE_COUNTS, 28 ch / 1071 v; standard KJV / "
            "UBS-NA enumeration — NT versification is standardized, "
            "so NO γ-notes cross-validation, unlike the OT "
            "pseudepigrapha jub/1en; τ.7.x.v — OPENS the 4-Gospels "
            "block, structural_map.matthew is a NEW section "
            "[1567,1635], the τ.7.x.q new-section pattern, NOT a "
            "Π.1 upgrade; Mark opens p1636, discovery-scan cross-"
            "validated). "
            "Renumbering discards parser chapter labels and assigns verses "
            "sequentially to canonical chapters; trade-off documented in "
            "renumber_against_floor() docstring."
        ),
    )
    p.add_argument(
        "--lang",
        default="both",
        choices=["geez", "amharic", "both"],
        help=(
            "Which translation slot(s) to write. 'both' (default) writes "
            "both geez-tewahedo and amharic-tewahedo (Π.1 + Meqabyan-pilot "
            "behavior). 'amharic' writes only amharic-tewahedo (τ.7.x.a per "
            "D4-c Amharic-first sequencing; leaves geez-tewahedo at its "
            "current state). 'geez' writes only geez-tewahedo (τ.6.x.2.a "
            "Geʽez-stream per-book ingests under D1-a cadence)."
        ),
    )
    p.add_argument(
        "--ingest-phase",
        default=None,
        help=(
            "Phase tag recorded in the output module (e.g. 'τ.7.x.a'). "
            "Written as INGEST_PHASE constant + referenced in the file "
            "docstring. Useful for downstream-consumer audit traceback."
        ),
    )
    args = p.parse_args()

    cfg = load_source_config()

    renumber_floor: dict[int, int] | None = None
    if args.renumber == "genesis":
        renumber_floor = GENESIS_VERSE_COUNTS
    elif args.renumber == "exodus":
        renumber_floor = EXODUS_VERSE_COUNTS
    elif args.renumber == "leviticus":
        renumber_floor = LEVITICUS_VERSE_COUNTS
    elif args.renumber == "numbers":
        renumber_floor = NUMBERS_VERSE_COUNTS
    elif args.renumber == "deuteronomy":
        renumber_floor = DEUTERONOMY_VERSE_COUNTS
    elif args.renumber == "joshua":
        renumber_floor = JOSHUA_VERSE_COUNTS
    elif args.renumber == "judges":
        renumber_floor = JUDGES_VERSE_COUNTS
    elif args.renumber == "ruth":
        renumber_floor = RUTH_VERSE_COUNTS
    elif args.renumber == "psalms":
        renumber_floor = PSALMS_VERSE_COUNTS
    elif args.renumber == "ezra_sutuel":
        renumber_floor = EZRA_SUTUEL_VERSE_COUNTS
    elif args.renumber == "tobit":
        renumber_floor = TOBIT_VERSE_COUNTS
    elif args.renumber == "judith":
        renumber_floor = JUDITH_VERSE_COUNTS
    elif args.renumber == "esther":
        renumber_floor = ESTHER_VERSE_COUNTS
    elif args.renumber == "meqabyan_i":
        renumber_floor = MQ1_VERSE_COUNTS
    elif args.renumber == "meqabyan_ii":
        renumber_floor = MQ2_VERSE_COUNTS
    elif args.renumber == "meqabyan_iii":
        renumber_floor = MQ3_VERSE_COUNTS
    elif args.renumber == "sirach":
        renumber_floor = SIRACH_VERSE_COUNTS
    elif args.renumber == "four_baruch":
        renumber_floor = FOUR_BARUCH_VERSE_COUNTS
    elif args.renumber == "baruch":
        renumber_floor = BARUCH_VERSE_COUNTS
    elif args.renumber == "wisdom_of_solomon":
        renumber_floor = WISDOM_OF_SOLOMON_VERSE_COUNTS
    elif args.renumber == "prayer_of_azariah":
        renumber_floor = PRAYER_OF_AZARIAH_VERSE_COUNTS
    elif args.renumber == "susanna":
        renumber_floor = SUSANNA_VERSE_COUNTS
    elif args.renumber == "bel_and_the_dragon":
        renumber_floor = BEL_AND_THE_DRAGON_VERSE_COUNTS
    elif args.renumber == "jubilees":
        renumber_floor = JUBILEES_VERSE_COUNTS
    elif args.renumber == "one_enoch":
        renumber_floor = ONE_ENOCH_VERSE_COUNTS
    elif args.renumber == "matthew":
        renumber_floor = MATTHEW_VERSE_COUNTS

    if args.pilot:
        # Derive section from pilot filter. Π.1 introduced metadata
        # keys (e.g. tewahedo_distinctive_inventory) at the same level
        # as real sections; we filter those out via _extraction_sections.
        pilot_book = args.pilot.split("-ch")[0]
        section = None
        sm = cfg["structural_map"]
        for name in _extraction_sections(cfg):
            sec = sm[name]
            if pilot_book in (sec.get("book_codes") or []):
                section = name
                break
        if not section:
            raise SystemExit(
                f"FATAL: pilot book {pilot_book!r} not in any extractable section. "
                f"Available: {sorted(_extraction_sections(cfg))}"
            )
        print(f"extract_parallel_pdf — PILOT mode: {args.pilot} (section={section})")
        by_book = extract_section(
            cfg,
            section,
            pilot_filter=args.pilot,
            engine=args.engine,
            paragraph_mode=args.paragraph_mode,
            renumber_floor=renumber_floor,
        )
    elif args.section:
        print(f"extract_parallel_pdf — SECTION mode: {args.section}")
        by_book = extract_section(
            cfg,
            args.section,
            engine=args.engine,
            paragraph_mode=args.paragraph_mode,
            renumber_floor=renumber_floor,
        )
    else:
        p.error("must pass --section or --pilot")

    extraction_date = date.today().isoformat()
    print()
    print("=" * 72)
    print("EXTRACTION RESULTS")
    print("=" * 72)

    lang_filter: set[str] = {"geez", "amharic"} if args.lang == "both" else {args.lang}

    for book, langs in by_book.items():
        print()
        print(f"book: {book}")
        for lang, verses in langs.items():
            translation = f"{lang}-tewahedo"
            n = len(verses)
            if lang not in lang_filter:
                print(f"  {translation}: {n} verses (SKIPPED — --lang={args.lang})")
                continue
            print(f"  {translation}: {n} verses")
            if args.dry_run:
                for ch, v, t in verses[:3]:
                    print(f"    {ch}:{v}  {t[:60]}...")
                if len(verses) > 3:
                    print(f"    ... +{len(verses) - 3} more")
            else:
                out = TRANSLATIONS_DIR / translation / f"{book}.py"
                if out.exists() and not args.overwrite:
                    print(f"    SKIP (exists; use --overwrite to replace): {out}")
                    continue
                doc_extra = _build_docstring_extra(
                    book=book,
                    lang=lang,
                    verses=verses,
                    paragraph_mode=args.paragraph_mode,
                    renumber=args.renumber,
                )
                written = write_book_module(
                    translation,
                    book,
                    verses,
                    args.quality,
                    extraction_date,
                    ingest_phase=args.ingest_phase,
                    docstring_extra=doc_extra,
                )
                print(f"    wrote {written}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

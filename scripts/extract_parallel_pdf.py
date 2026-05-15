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
    r"[።፡፣=]"  # MUST be followed by Ethiopic punctuation OR `=` (OCR
    # occasionally substitutes `=` for `።` at the end of
    # chapter markers — confirmed empirically on page 5
    # of Genesis 1)
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
    # Overflow: any input verses beyond the floor end up in ch_max+1.
    if idx < n_in:
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
            heuristic = {
                ("meqabyan", "mq1"): (1318, 1365),
                ("meqabyan", "mq2"): (1366, 1372),
                ("meqabyan", "mq3"): (1373, 1378),
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
        text_repr = text.replace("'", "\\'")
        lines.append(f"    ({ch}, {v}, '{text_repr}'),")
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
        choices=["genesis", "exodus"],
        help=(
            "Post-process renumber verses against a canonical chapter "
            "verse-count floor (τ.7.x.a writer-side residual handler). "
            "Supports 'genesis' (GENESIS_VERSE_COUNTS, 50 ch / 1534 v) and "
            "'exodus' (EXODUS_VERSE_COUNTS, 40 ch / 1213 v; τ.7.x.b). "
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

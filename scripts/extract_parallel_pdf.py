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


def parse_verses_from_text(text: str) -> list[tuple[int, int, str]]:
    """Parse one column's text into (chapter, verse, text) tuples.

    Strategy:
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
    """
    text = normalize_verse_numerals(text)
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

    geez_verses = parse_verses_from_text(full_geez)
    amh_verses = parse_verses_from_text(full_amh)

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
) -> Path:
    """Write content/translations/<translation>/<book>.py with the
    verse data + provenance metadata."""
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
        "Tool: scripts/extract_parallel_pdf.py (τ.6.x.0a, 2026-05-14)",
        "",
        "Per the source PDF's caveat: the OCR text layer is unreliable",
        "for Geʽez (vowel-order scrambling, invented fidel). Amharic OCR",
        "is more reliable but still has errors. Production-grade text",
        "for Meqabyan flows through δ.1.x (Phase-4 page-image methodology).",
        '"""',
        "",
        f"TRANSLATION = {translation!r}",
        f"BOOK = {book!r}",
        f"SOURCE_QUALITY = {source_quality!r}",
        "SOURCE_PROVENANCE = 'parallel-bible-eotc'",
        f"EXTRACTION_DATE = {extraction_date!r}",
        "VERSES = [",
    ]
    for ch, v, text in verses:
        text_repr = text.replace("'", "\\'")
        lines.append(f"    ({ch}, {v}, '{text_repr}'),")
    lines.append("]")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


# ───────────────────────────────────────────────────────────────────
# CLI
# ───────────────────────────────────────────────────────────────────


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
    args = p.parse_args()

    cfg = load_source_config()

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
        by_book = extract_section(cfg, section, pilot_filter=args.pilot, engine=args.engine)
    elif args.section:
        print(f"extract_parallel_pdf — SECTION mode: {args.section}")
        by_book = extract_section(cfg, args.section, engine=args.engine)
    else:
        p.error("must pass --section or --pilot")

    extraction_date = date.today().isoformat()
    print()
    print("=" * 72)
    print("EXTRACTION RESULTS")
    print("=" * 72)

    for book, langs in by_book.items():
        print()
        print(f"book: {book}")
        for lang, verses in langs.items():
            translation = f"{lang}-tewahedo"
            print(f"  {translation}: {len(verses)} verses")
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
                written = write_book_module(translation, book, verses, args.quality, extraction_date)
                print(f"    wrote {written}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

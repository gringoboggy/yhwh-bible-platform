"""scripts/extract_parallel_pdf.py — extract Geʽez + Amharic verse
text from the parallel-Bible EOTC PDF.

τ.6.x.0a (2026-05-14) — built after the τ.6.x.0 pivot finding that
eBible.org's gez-Geez slot is no longer available; the parallel-
Bible PDF (`Bible_Amharic_and_Geez.pdf`, 2,539 pages) is the
PRIMARY Geʽez + Amharic source.

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

This tool reads the PDF's OCR text layer. Per the Phase-4
methodology in `project_maccabees_expansion/02_METHODOLOGY.md §2`,
the OCR is GARBLED for Geʽez (e.g. clean ወገብረ → garbage like
ወንዳረ ቘልፌኤቱ). Therefore:

- For NON-Meqabyan books, extracted text is tagged `SOURCE_QUALITY =
  "ocr-tier3"` — the publisher's caveat is preserved alongside the
  text so readers know to expect OCR errors in Geʽez until later
  passes upgrade the data.
- For Meqabyan (the highest-priority book per
  project_maccabees_expansion/), this tool is NOT the long-term
  source — Phase 4 (δ.1.x) will produce page-image-tier1 text via
  the careful per-chapter methodology. This tool's Meqabyan output
  is `ocr-tier3` and explicitly REPLACEABLE by δ.1.x output.

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
import sys
import yaml
from collections import OrderedDict
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc"
TRANSLATIONS_DIR = REPO / "content" / "translations"


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

# Regex: match a chapter header. The parallel PDF uses ምዕራፍ + Geʽez numeral.
CHAPTER_HEADER_RE = re.compile(r"ምዕራፍ\s*([፩-፼]+)")


def extract_text_by_column(pdf_page) -> tuple[str, str]:
    """Extract the Geʽez (left) and Amharic (right) column text from
    one PDF page.

    Uses pymupdf's page.get_text() with bbox-restriction. The split
    point is at 50% of page width.

    Returns: (geez_text, amharic_text). Each may be empty.
    """
    rect = pdf_page.rect
    mid_x = rect.x0 + rect.width * 0.50

    left_rect = (rect.x0, rect.y0, mid_x, rect.y1)
    right_rect = (mid_x, rect.y0, rect.x1, rect.y1)

    geez = pdf_page.get_text("text", clip=left_rect)
    amharic = pdf_page.get_text("text", clip=right_rect)
    return geez, amharic


def parse_verses_from_text(text: str) -> list[tuple[int, int, str]]:
    """Parse one column's text into (chapter, verse, text) tuples.

    Strategy:
    - Track current chapter (starts at 1 if no ምዕራፍ marker seen).
    - When we see ምዕራፍ ፪, switch to chapter 2, etc.
    - When we see a line starting with a digit (e.g. "1 በመጀመሪያ..."
      OR "1፣ በመጀመሪያ..."), start a new verse.
    - Accumulate text lines into the current verse until the next
      verse marker.
    """
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


def extract_section(
    cfg: dict,
    section_name: str,
    pilot_filter: str | None = None,
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
    """
    import fitz

    sec = cfg["structural_map"].get(section_name)
    if not sec:
        raise SystemExit(
            f"FATAL: section {section_name!r} not in _source.yaml::structural_map. "
            f"Available: {sorted(cfg['structural_map'].keys())}"
        )
    # Support both the new pdf_page_range key and the legacy
    # scan_page_range key for back-compat. pdf_page_range is the
    # canonical post-τ.6.x.0a format (0-indexed full-PDF page
    # numbers); scan_page_range was the τ.6.x.0 placeholder format
    # (archive.org scan-page numbers, requires pdf_index_offset).
    if "pdf_page_range" in sec:
        page_start, page_end = sec["pdf_page_range"]
        offset = 0
    else:
        page_start, page_end = sec["scan_page_range"]
        offset = sec.get("pdf_index_offset", 0)
    book_codes = sec["book_codes"]

    pdf_path = resolve_pdf_path(cfg)
    print(f"  source PDF: {pdf_path}")
    print(f"  section: {section_name} (PDF pages {page_start}-{page_end})")
    print(f"  books: {', '.join(book_codes)}")

    # For pilot mode, restrict the page range to just the pilot book's
    # sub-range if a `subsections` map is present in the section.
    # This is essential because parsing 60+ pages of multi-book text
    # without book-boundary detection produces tangled output.
    if pilot_filter:
        pilot_book = pilot_filter.split("-ch")[0] if "-ch" in pilot_filter else pilot_filter
        # Look for a sub-page-range hint in the notes field — we'll
        # parse the notes more cleverly post-pilot. For now, accept
        # a `subsections` map if present.
        subs = sec.get("subsections") or {}
        if pilot_book in subs:
            page_start, page_end = subs[pilot_book]
            print(f"  pilot narrowing: book {pilot_book} → pages {page_start}-{page_end}")
        else:
            # Heuristic fallback for the meqabyan section based on
            # τ.6.x.0a verified ranges (notes documented these even
            # if subsections isn't filled in):
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
        for scan_page in range(page_start, page_end + 1):
            idx = scan_page - offset
            if idx < 0 or idx >= len(doc):
                continue
            page = doc[idx]
            g, a = extract_text_by_column(page)
            all_geez.append(g)
            all_amh.append(a)
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
    args = p.parse_args()

    cfg = load_source_config()

    if args.pilot:
        # Derive section from pilot filter.
        pilot_book = args.pilot.split("-ch")[0]
        section = None
        for name, sec in cfg["structural_map"].items():
            if pilot_book in sec["book_codes"]:
                section = name
                break
        if not section:
            raise SystemExit(f"FATAL: pilot book {pilot_book!r} not in any section")
        print(f"τ.6.x.0a extraction — PILOT mode: {args.pilot} (section={section})")
        by_book = extract_section(cfg, section, pilot_filter=args.pilot)
    elif args.section:
        print(f"τ.6.x.0a extraction — SECTION mode: {args.section}")
        by_book = extract_section(cfg, args.section)
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

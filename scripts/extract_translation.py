"""scripts/extract_translation.py — parse a public-domain Bible into the
project's translation store (Phase τ.1).

Input:  content/translations/sources/<id>/eng-<id>_vpl.txt
        eBible.org's "Verse Per Line" text format. One verse per line,
        prefixed with a 3-letter SIL/UBS book code:

            GEN 1:1 In the beginning God created the heaven and the earth.

Output: content/translations/<id>/<book_code>.py
        One Python module per project book code, each exposing:

            TRANSLATION = "<id>"
            BOOK = "<book_code>"
            VERSES = [(chapter, verse, text), ...]

        Plus content/translations/<id>/_meta.yaml — translation
        metadata (license, source, fetched-date, totals).

Why .py and not .yaml/.json:
        Matches the project's existing per-book notes format (which
        also uses .py with tuple data). Loads via ``import`` with no
        parser overhead — important for runtime popups across 36k+
        verses. lru_cache-friendly.

Usage:
    python scripts/extract_translation.py kjv
    python scripts/extract_translation.py kjv --dry-run
    python scripts/extract_translation.py kjv --report

Standalone — does not import any of the project's other modules so it
remains usable as a one-shot ingestion tool even before τ.1.5 wires
the runtime query API.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TRANSLATIONS_DIR = REPO / "content" / "translations"

# eBible VPL → project book code mapping.
#
# eBible.org's VPL files use older 3-letter codes (mostly matching
# UBS Paratext but with a few deviations from the modern SIL standard
# now used in their navigation). The project uses lowercase 3-letter
# codes mostly aligned with eBible's VPL — only the cells below differ.
EBIBLE_VPL_TO_PROJECT: dict[str, str] = {
    # Old Testament — 39 books, all just lowercased
    "GEN": "gen", "EXO": "exo", "LEV": "lev", "NUM": "num", "DEU": "deu",
    "JOS": "jos", "JDG": "jdg", "RUT": "rut",
    "1SA": "1sa", "2SA": "2sa", "1KI": "1ki", "2KI": "2ki",
    "1CH": "1ch", "2CH": "2ch",
    "EZR": "ezr", "NEH": "neh", "EST": "est",
    "JOB": "job", "PSA": "psa", "PRO": "pro", "ECC": "ecc",
    "SOL": "sng",        # Song of Solomon → Song of Songs
    "ISA": "isa", "JER": "jer", "LAM": "lam",
    "EZE": "eze", "DAN": "dan",
    "HOS": "hos", "JOE": "joe", "AMO": "amo", "OBA": "oba", "JON": "jon",
    "MIC": "mic", "NAH": "nah", "HAB": "hab", "ZEP": "zep",
    "HAG": "hag", "ZEC": "zec", "MAL": "mal",

    # Apocrypha / Deuterocanon
    "TOB": "tob", "JDT": "jdt",
    "ESG": "aes",        # Esther Greek additions → project's `aes`
    "WIS": "wis", "SIR": "sir",
    "BAR": "bar",        # SPECIAL: ch 6 is split out below into `lje`
    "PRA": "paz",        # Prayer of Azariah / Song of 3 Holy Children
    "SUS": "sus", "BEL": "bel",
    "1MA": "1ma", "2MA": "2ma",   # forward-compat: project lacks books.yaml
                                    # entries for these yet but the data
                                    # lands here for when they're added
    "1ES": "1es",
    "PRM": "man",        # Prayer of Manasses
    "4ES": "2es",        # 4 Esdras (Latin) = project's `2es`

    # New Testament
    "MAT": "mat", "MAR": "mrk", "LUK": "luk", "JOH": "jhn",
    "ACT": "act",
    "ROM": "rom", "1CO": "1co", "2CO": "2co",
    "GAL": "gal", "EPH": "eph", "PHI": "phi", "COL": "col",
    "1TH": "1th", "2TH": "2th", "1TI": "1ti", "2TI": "2ti",
    "TIT": "tit", "PHM": "phm", "HEB": "heb",
    "JAM": "jam", "1PE": "1pe", "2PE": "2pe",
    "1JO": "1jn", "2JO": "2jn", "3JO": "3jn",
    "JUD": "jud", "REV": "rev",
}

# Books in the project canon for which KJV+Apocrypha provides no text
# (these are Ethiopian-canon-only or simply absent from the standard
# Apocrypha): jub, 1en, 2en, mq1-3, 4ba, 1cl. Recorded for reporting
# only; the absence is expected and not an error.
PROJECT_BOOKS_OUTSIDE_KJV = {
    "jub", "1en", "2en", "mq1", "mq2", "mq3", "4ba", "1cl",
}


# ----------------------------------------------------------------------
# VPL parsing
# ----------------------------------------------------------------------

# Lines look like:    GEN 1:1 In the beginning God created…
# (book code; space; chapter:verse; space; text to end of line)
_VPL_LINE_RE = re.compile(r"^([0-9A-Z]{3})\s+(\d+):(\d+)\s+(.*)$")


def parse_vpl(vpl_path: Path) -> dict[str, list[tuple[int, int, str]]]:
    """Read a VPL .txt file and return {book_code: [(ch, vs, text), …]}.

    Book codes are returned **as-is from the file** (ALL CAPS eBible
    codes); mapping to project codes happens in a later pass.
    """
    out: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    skipped_blank = 0
    skipped_malformed = 0
    with vpl_path.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip():
                skipped_blank += 1
                continue
            m = _VPL_LINE_RE.match(line)
            if not m:
                skipped_malformed += 1
                continue
            book, ch, vs, text = m.groups()
            out[book].append((int(ch), int(vs), text.strip()))
    if skipped_malformed:
        sys.stderr.write(
            f"  warning: {skipped_malformed} malformed VPL line(s) skipped\n"
        )
    return dict(out)


def split_baruch_letter_of_jeremiah(
    bar_verses: list[tuple[int, int, str]],
) -> tuple[list[tuple[int, int, str]], list[tuple[int, int, str]]]:
    """eBible's KJV+Apocrypha keeps the Letter of Jeremiah inside Baruch
    as chapter 6 (the traditional KJV layout). The project treats it
    as a separate book ``lje``.

    Returns (baruch_chapters_1_to_5, lje_as_chapter_1).
    """
    bar_keep: list[tuple[int, int, str]] = []
    lje_renumbered: list[tuple[int, int, str]] = []
    for c, v, t in bar_verses:
        if c == 6:
            lje_renumbered.append((1, v, t))
        else:
            bar_keep.append((c, v, t))
    return bar_keep, lje_renumbered


# ----------------------------------------------------------------------
# Per-book Python file emission
# ----------------------------------------------------------------------


def _py_repr_text(s: str) -> str:
    """Render a verse text as a Python string literal — double-quoted
    when possible, falling back to repr() for awkward content. Output
    is one line per verse for grep-ability."""
    if "\\" not in s and '"' not in s:
        return f'"{s}"'
    return repr(s)


def write_book_module(out_path: Path, translation: str, book_code: str,
                       verses: list[tuple[int, int, str]]) -> None:
    """Emit one ``content/translations/<id>/<book>.py`` module.

    The file is regenerable — a header banner notes that hand edits
    will be lost on the next extraction run. Verses are written as a
    flat list of tuples for fastest possible import-time loading.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f'"""Translation: {translation} · Book: {book_code}',
        '',
        'AUTO-GENERATED by scripts/extract_translation.py.',
        'Do not edit by hand — re-run extraction to regenerate.',
        '"""',
        f'TRANSLATION = "{translation}"',
        f'BOOK = "{book_code}"',
        'VERSES = [',
    ]
    # Verses sorted by (chapter, verse) for deterministic output
    for c, v, t in sorted(verses, key=lambda r: (r[0], r[1])):
        lines.append(f'    ({c}, {v}, {_py_repr_text(t)}),')
    lines.append(']')
    lines.append('')
    out_path.write_text("\n".join(lines), encoding="utf-8")


# ----------------------------------------------------------------------
# Metadata YAML
# ----------------------------------------------------------------------


def write_meta_yaml(meta_path: Path, info: dict) -> None:
    """Write the translation _meta.yaml. Hand-rolled writer to avoid
    a runtime PyYAML dependency on the small set of fields we use."""

    def _q(s: str) -> str:
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

    lines = [
        "# Translation metadata — generated by scripts/extract_translation.py",
        "# (the source archive in ./sources/ is the canonical record;",
        "# this file is a convenience summary)",
        "",
        f'id: {info["id"]}',
        f'title: {_q(info["title"])}',
        f'short_title: {_q(info["short_title"])}',
        f'license: {_q(info["license"])}',
        "source:",
        f'  publisher: {_q(info["source"]["publisher"])}',
        f'  url: {_q(info["source"]["url"])}',
        f'  package: {_q(info["source"]["package"])}',
        f'  fetched: {info["source"]["fetched"]}',
        f'  source_date: {info["source"]["source_date"]}',
        "stats:",
        f'  books: {info["stats"]["books"]}',
        f'  verses: {info["stats"]["verses"]}',
        f'  books_outside_kjv: {info["stats"]["books_outside_kjv"]}',
    ]
    if info.get("notes"):
        lines.extend(["notes: |"] + ["  " + ln for ln in info["notes"].split("\n")])
    meta_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------


def extract(translation_id: str, dry_run: bool = False, report: bool = False) -> dict:
    """Top-level extraction entry point.

    For ``translation_id`` it expects the source files to be at
    ``content/translations/sources/<id>/`` already (use a separate
    fetcher to download). Returns a stats dict.
    """
    src_dir = TRANSLATIONS_DIR / "sources" / translation_id
    if not src_dir.is_dir():
        raise SystemExit(f"missing source dir: {src_dir}")

    vpl_candidates = list(src_dir.glob("*_vpl.txt"))
    if not vpl_candidates:
        raise SystemExit(f"no *_vpl.txt found in {src_dir}")
    vpl_path = vpl_candidates[0]

    by_ebible_book = parse_vpl(vpl_path)

    # Map eBible codes → project codes, applying the BAR-split rule.
    by_project_book: dict[str, list[tuple[int, int, str]]] = {}
    unmapped_codes: list[str] = []
    for ebook, verses in by_ebible_book.items():
        if ebook == "BAR":
            bar_keep, lje_part = split_baruch_letter_of_jeremiah(verses)
            by_project_book["bar"] = bar_keep
            if lje_part:
                by_project_book["lje"] = lje_part
            continue
        proj = EBIBLE_VPL_TO_PROJECT.get(ebook)
        if proj is None:
            unmapped_codes.append(ebook)
            continue
        by_project_book[proj] = verses

    total_verses = sum(len(v) for v in by_project_book.values())
    stats = {
        "translation": translation_id,
        "ebible_books_seen": len(by_ebible_book),
        "project_books_emitted": len(by_project_book),
        "total_verses": total_verses,
        "unmapped_codes": unmapped_codes,
        "books_outside_kjv": sorted(PROJECT_BOOKS_OUTSIDE_KJV),
    }

    if report:
        print(f"VPL source: {vpl_path}")
        print(f"  eBible books seen:       {stats['ebible_books_seen']}")
        print(f"  Project books emitted:   {stats['project_books_emitted']}")
        print(f"  Total verses:            {stats['total_verses']}")
        if unmapped_codes:
            print(f"  Unmapped eBible codes:   {unmapped_codes}")
        print(f"  Project books w/o coverage: {stats['books_outside_kjv']}")

    if dry_run:
        return stats

    # Write per-book .py files
    out_dir = TRANSLATIONS_DIR / translation_id
    out_dir.mkdir(parents=True, exist_ok=True)
    for proj_code, verses in sorted(by_project_book.items()):
        write_book_module(out_dir / f"{proj_code}.py",
                          translation_id, proj_code, verses)

    # Write _meta.yaml — KJV-specific defaults; tweak when extending
    # this script to other translations later.
    if translation_id == "kjv":
        meta = {
            "id": "kjv",
            "title": "King James Version + Apocrypha",
            "short_title": "KJV",
            "license": "Public Domain",
            "source": {
                "publisher": "eBible.org",
                "url": "https://eBible.org/eng-kjv/",
                "package": "eng-kjv_vpl.zip",
                "fetched": _dt.date.today().isoformat(),
                "source_date": "2025-11-27",
            },
            "stats": {
                "books": stats["project_books_emitted"],
                "verses": stats["total_verses"],
                "books_outside_kjv": len(PROJECT_BOOKS_OUTSIDE_KJV),
            },
            "notes": (
                "King James Version (1769 Blayney standardized text) "
                "with Apocrypha. Letter of Jeremiah (project book "
                "'lje') is split out of eBible's BAR chapter 6, "
                "matching the project's separate-book convention. "
                "1 Maccabees and 2 Maccabees are emitted at "
                "content/translations/kjv/{1ma,2ma}.py for "
                "forward-compatibility, even though books.yaml "
                "doesn't list them yet."
            ),
        }
        write_meta_yaml(out_dir / "_meta.yaml", meta)

    return stats


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("translation_id",
                   help="translation slug; expects sources/<id>/*_vpl.txt")
    p.add_argument("--dry-run", action="store_true",
                   help="parse and report, but do not write output files")
    p.add_argument("--report", action="store_true",
                   help="print a coverage report after extraction")
    args = p.parse_args()
    stats = extract(args.translation_id, dry_run=args.dry_run, report=args.report)
    if not args.report:
        print(
            f"{stats['translation']}: "
            f"{stats['project_books_emitted']} books, "
            f"{stats['total_verses']:,} verses"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Build Easton's Bible Dictionary notes (kind ``dict-easton``) from the clean
CCEL edition text (``content/sources/eastons_ccel_source.txt``, extracted from
the CCEL PDF).

Easton's entries are headword-prefixed with ``•`` (``•AMASA burden. ...``) and
use FULL book names in references (``1 Chronicles 2:17``, not abbreviations).
Each entry's definition is attached as one note to the entry's PRIMARY (first)
``chapter:verse`` reference — giving a per-verse dictionary gloss for the people,
places, and terms a verse mentions. Promotion uses the batched insert
(``promote.batch_insert_notes``).

Usage:
    python3 scripts/extract_eastons_ccel.py            # parse + promote
    python3 scripts/extract_eastons_ccel.py --dry-run  # report counts, no write
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.promote import batch_insert_notes  # noqa: E402

SOURCE = REPO_ROOT / "content" / "sources" / "eastons_ccel_source.txt"
NOTES_DIR = REPO_ROOT / "content" / "notes"
ATTRIBUTION = "Easton's Illustrated Bible Dictionary, M. G. Easton (1897). Public domain."
MAX_BODY = 480

# Full book names → project 3-letter codes (the CORRECT codes: eze/joe/nah/jam/phi).
EASTON_BOOK = {
    "Genesis": "gen",
    "Exodus": "exo",
    "Leviticus": "lev",
    "Numbers": "num",
    "Deuteronomy": "deu",
    "Joshua": "jos",
    "Judges": "jdg",
    "Ruth": "rut",
    "1 Samuel": "1sa",
    "2 Samuel": "2sa",
    "1 Kings": "1ki",
    "2 Kings": "2ki",
    "1 Chronicles": "1ch",
    "2 Chronicles": "2ch",
    "Ezra": "ezr",
    "Nehemiah": "neh",
    "Esther": "est",
    "Job": "job",
    "Psalms": "psa",
    "Psalm": "psa",
    "Proverbs": "pro",
    "Ecclesiastes": "ecc",
    "Song of Solomon": "sng",
    "Song of Songs": "sng",
    "Canticles": "sng",
    "Isaiah": "isa",
    "Jeremiah": "jer",
    "Lamentations": "lam",
    "Ezekiel": "eze",
    "Daniel": "dan",
    "Hosea": "hos",
    "Joel": "joe",
    "Amos": "amo",
    "Obadiah": "oba",
    "Jonah": "jon",
    "Micah": "mic",
    "Nahum": "nah",
    "Habakkuk": "hab",
    "Zephaniah": "zep",
    "Haggai": "hag",
    "Zechariah": "zec",
    "Malachi": "mal",
    "Matthew": "mat",
    "Mark": "mrk",
    "Luke": "luk",
    "John": "jhn",
    "Acts": "act",
    "Romans": "rom",
    "1 Corinthians": "1co",
    "2 Corinthians": "2co",
    "Galatians": "gal",
    "Ephesians": "eph",
    "Philippians": "phi",
    "Colossians": "col",
    "1 Thessalonians": "1th",
    "2 Thessalonians": "2th",
    "1 Timothy": "1ti",
    "2 Timothy": "2ti",
    "Titus": "tit",
    "Philemon": "phm",
    "Hebrews": "heb",
    "James": "jam",
    "1 Peter": "1pe",
    "2 Peter": "2pe",
    "1 John": "1jn",
    "2 John": "2jn",
    "3 John": "3jn",
    "Jude": "jud",
    "Revelation": "rev",
}

_REF = re.compile(r"(?P<book>(?:[123]\s)?[A-Z][a-z]+(?:\sof\s[A-Z][a-z]+)?)\s(?P<ch>\d+):(?P<v>\d+)")
_HEAD = re.compile(r"^([A-Z][A-Z0-9'’\-]*(?:\s+[A-Z0-9'’\-]+)*)")


def first_ref(text: str) -> tuple[str, int, int] | None:
    """First ``chapter:verse`` reference in an entry, mapped to a book code.
    Chapter-only references (``Genesis 17``) are skipped — a per-verse note
    needs a verse."""
    for m in _REF.finditer(text):
        code = EASTON_BOOK.get(m.group("book"))
        if code:
            return code, int(m.group("ch")), int(m.group("v"))
    return None


def parse_entries(text: str) -> list[tuple[str, str]]:
    """Split the dictionary into (headword, full-entry-text) pairs on ``•``."""
    entries = []
    for chunk in text.split("•")[1:]:  # [0] is front matter before the first entry
        chunk = chunk.strip()
        m = _HEAD.match(chunk)
        if not m:
            continue
        head = m.group(1).strip()
        if len(head) >= 2:
            entries.append((head, chunk))
    return entries


def build_notes(entries: list[tuple[str, str]]) -> list[dict]:
    notes = []
    for head, chunk in entries:
        ref = first_ref(chunk)
        if not ref:
            continue
        code, c, v = ref
        rest = re.sub(r"\s+", " ", chunk[len(head) :]).strip()
        rest = rest.replace("\\", "").replace('"', "'")  # keep the tuple literal valid
        if len(rest) > MAX_BODY:
            rest = rest[:MAX_BODY].rsplit(" ", 1)[0] + "…"
        # No reviewer scaffold in the reader-facing body — RX Phase 1. (These
        # dict-easton notes promote straight via batch_insert_notes, which has
        # no reviewer_notes slot; the "condense as needed" guidance was trivial
        # reviewer chatter and is simply dropped.)
        body = f"<strong>Dictionary (Easton's).</strong> <strong>{head}</strong> {rest}"
        notes.append(
            {
                "code": code,
                "ch": c,
                "v": v,
                "kind": "dict-easton",
                "anchor": "",
                "title": "Dictionary",
                "label": "Easton.",
                "body": body,
                "attribution": ATTRIBUTION,
            }
        )
    return notes


def main() -> int:
    p = argparse.ArgumentParser(description="Build Easton's dict-easton notes from the clean CCEL text.")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    if not SOURCE.is_file():
        print(f"missing source: {SOURCE.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 2
    entries = parse_entries(SOURCE.read_text(encoding="utf-8"))
    notes = build_notes(entries)
    by_book: dict[str, list] = {}
    for n in notes:
        by_book.setdefault(n["code"], []).append(n)
    added = books = 0
    if not args.dry_run:
        for code, ns in by_book.items():
            bp = NOTES_DIR / f"{code}.py"
            if not bp.is_file():
                continue
            n = batch_insert_notes(bp, ns, skip_existing=True)
            added += n
            books += 1
    print(f"entries={len(entries):,}  notes_built={len(notes):,}  books={len(by_book)}  added={added:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build naves_topical.json from the clean CCEL Nave's Topical Bible text.

The previous index was built from an OCR-noisy source (garbled topic names like
``ORVILLE J`` / ``SFECIAJ`` and impossible coordinates like Genesis 87:12). This
parser reads the clean, proofread CCEL edition text
(``content/sources/naves_ccel_source.txt``, extracted from the CCEL PDF) and
rebuilds the topic→reference index, expanding Nave's compressed reference syntax
(``Ex 6:18; 20; Nu 26:58,59; 1Ch 6:3,18; 23:12,13``) into individual
``(book, chapter, verse)`` triples with book/chapter carry-forward.

Coordinate validation (out-of-range drop) happens in
``fetch_sources._build_naves_indices``; this module only parses + expands.

Usage:
    python3 scripts/extract_naves_ccel.py            # rebuild naves_topical.json
    python3 scripts/extract_naves_ccel.py --dry-run  # report counts, no write
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.notes_io import atomic_write, ensure_backup  # noqa: E402
from scripts.fetch_sources import NAVES_BOOK_REMAP, _build_naves_indices  # noqa: E402

SOURCE_TXT = REPO_ROOT / "content" / "sources" / "naves_ccel_source.txt"
OUT_JSON = REPO_ROOT / "content" / "sources" / "naves_topical.json"

# CCEL Nave's uses its own abbreviation scheme (Mr/Lu/Joh/1Pe/1Jo; "Jud" = Judges,
# NOT Jude). Complete 66-book map; falls back to NAVES_BOOK_REMAP for full names.
CCEL_ABBREV = {
    "Ge": "gen",
    "Ex": "exo",
    "Le": "lev",
    "Nu": "num",
    "De": "deu",
    "Jos": "jos",
    "Jud": "jdg",
    "Ru": "rut",
    "1Sa": "1sa",
    "2Sa": "2sa",
    "1Ki": "1ki",
    "2Ki": "2ki",
    "1Ch": "1ch",
    "2Ch": "2ch",
    "Ezr": "ezr",
    "Ne": "neh",
    "Es": "est",
    "Job": "job",
    "Ps": "psa",
    "Pr": "pro",
    "Ec": "ecc",
    "So": "sng",
    "Isa": "isa",
    "Jer": "jer",
    "La": "lam",
    "Eze": "eze",
    "Da": "dan",
    "Ho": "hos",
    "Joe": "joe",
    "Am": "amo",
    "Ob": "oba",
    "Jon": "jon",
    "Mic": "mic",
    "Na": "nah",
    "Hab": "hab",
    "Zep": "zep",
    "Hag": "hag",
    "Zec": "zec",
    "Mal": "mal",
    "Mt": "mat",
    "Mr": "mrk",
    "Lu": "luk",
    "Joh": "jhn",
    "Ac": "act",
    "Ro": "rom",
    "1Co": "1co",
    "2Co": "2co",
    "Ga": "gal",
    "Eph": "eph",
    "Php": "phi",
    "Col": "col",
    "1Th": "1th",
    "2Th": "2th",
    "1Ti": "1ti",
    "2Ti": "2ti",
    "Tit": "tit",
    "Phm": "phm",
    "Heb": "heb",
    "Jas": "jam",
    "1Pe": "1pe",
    "2Pe": "2pe",
    "1Jo": "1jn",
    "2Jo": "2jn",
    "3Jo": "3jn",
    "Jude": "jud",
    "Re": "rev",
}

_BOOK = r"(?:[1-3]\s?)?[A-Z][a-z]{1,3}"
_FIRST_REF = re.compile(_BOOK + r"\s+\d+:\d+")
_CIT = re.compile(
    r"(?P<book>" + _BOOK + r")\s+(?P<bch>\d+):(?P<bv>\d+)(?:-(?P<bv2>\d+))?"
    r"|(?P<bookch>" + _BOOK + r")\s+(?P<bcho>\d+)(?![:\d])"
    r"|(?P<ch>\d+):(?P<cv>\d+)(?:-(?P<cv2>\d+))?"
    r"|(?P<v>\d+)(?:-(?P<v2>\d+))?"
)
_TOPIC = re.compile(r"^[A-Z][A-Z0-9 '\-,()]+$")


def remap(abbr: str) -> str | None:
    a = re.sub(r"\s+", "", abbr)
    return CCEL_ABBREV.get(a) or NAVES_BOOK_REMAP.get(a) or NAVES_BOOK_REMAP.get(a.title())


def expand_refs(line: str) -> list[list]:
    """Expand a Nave's reference line into ``[book, chapter, verse]`` triples.

    Handles book/chapter carry-forward (``Ex 6:18; 20`` → Ex 6:18 + Ex 6:20),
    comma verse-lists (``Nu 26:58,59``), ranges (``Ge 5:1-5``), and new-chapter
    same-book (``1Ch 6:3,18; 23:12``). Chapter-only refs (``Ge 14``) update state
    but emit no verse (a per-verse index can't anchor a whole-chapter ref).
    "See X" lines and prose without references yield no triples.
    """
    m0 = _FIRST_REF.search(line)
    if not m0:
        return []
    out: list[list] = []
    book: str | None = None
    ch: int | None = None
    for m in _CIT.finditer(line, m0.start()):
        if m.group("book"):
            bk = remap(m.group("book"))
            if not bk:
                continue
            book, ch = bk, int(m.group("bch"))
            v1 = int(m.group("bv"))
            v2 = int(m.group("bv2")) if m.group("bv2") else v1
            out.extend([book, ch, v] for v in range(v1, v2 + 1))
        elif m.group("bookch"):
            bk = remap(m.group("bookch"))
            if not bk:
                continue
            book, ch = bk, int(m.group("bcho"))  # chapter-only: update state, no verse
        elif m.group("ch"):
            if book is None:
                continue
            ch = int(m.group("ch"))
            v1 = int(m.group("cv"))
            v2 = int(m.group("cv2")) if m.group("cv2") else v1
            out.extend([book, ch, v] for v in range(v1, v2 + 1))
        elif m.group("v"):
            if book is None or ch is None:
                continue
            v1 = int(m.group("v"))
            v2 = int(m.group("v2")) if m.group("v2") else v1
            out.extend([book, ch, v] for v in range(v1, v2 + 1))
    return out


def parse_text(text: str) -> dict[str, list]:
    """Parse the CCEL Nave's text into a forward index {topic: [[book,ch,v],...]}."""
    forward: dict[str, list] = {}
    current: str | None = None
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        if _TOPIC.match(s) and len(s) >= 2 and "." not in s and any(c.isalpha() for c in s):
            current = s
            forward.setdefault(current, [])
        elif current and s[0] in "-–—.":
            forward[current].extend(expand_refs(s))
    return {t: r for t, r in forward.items() if r}


def build(dry_run: bool = False) -> dict:
    text = SOURCE_TXT.read_text(encoding="utf-8")
    forward = parse_text(text)
    idx = _build_naves_indices(forward)
    print(f"topics={idx['_meta']['n_topics']:,}  refs={idx['_meta']['n_refs']:,}")
    if not dry_run:
        if OUT_JSON.is_file():
            ensure_backup(OUT_JSON)
        atomic_write(OUT_JSON, json.dumps(idx, ensure_ascii=False, indent=2) + "\n")
        print(f"wrote {OUT_JSON.relative_to(REPO_ROOT)}")
    return idx


def main() -> int:
    p = argparse.ArgumentParser(description="Rebuild naves_topical.json from the clean CCEL Nave's text.")
    p.add_argument("--dry-run", action="store_true", help="report counts, do not write")
    args = p.parse_args()
    if not SOURCE_TXT.is_file():
        print(f"missing source: {SOURCE_TXT.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 2
    build(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

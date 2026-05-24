#!/usr/bin/env python3
"""
link_xrefs.py — Auto-link cross-references inside commentary notes.

Hand-typed phrases like ``cf. Genesis 1:1``, ``See Matt 3:16``, ``cf. 1 Cor 12:4``
appear unwrapped in note bodies (and the originals popovers we generate). This
script wraps them in ``<a href="...">`` so readers can tap to navigate.

The script is conservative on purpose:

  * Only modifies content inside ``<aside class="note …">`` and ``<aside class="vnote">``
    blocks — i.e., commentary we wrote, not PDF-derived verse text.
  * Never touches a ref that is already inside an ``<a>`` element.
  * Does not modify the source files unless ``--apply`` is passed.

Examples:
    python3 scripts/link_xrefs.py --dry-run        # report what would change
    python3 scripts/link_xrefs.py --apply          # actually wrap refs
    python3 scripts/link_xrefs.py --book gen --apply

Exit codes: 0 success / no work, 1 if any error.
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402

EPUB_DIR = REPO_ROOT / "epub_working"

# Common abbreviations for biblical books. Maps lowercased name → canonical code.
# Codes must match the ``code`` field in books.yaml.
ABBREV = {
    # Pentateuch
    "gen": "gen",
    "ge": "gen",
    "genesis": "gen",
    "exo": "exo",
    "ex": "exo",
    "exod": "exo",
    "exodus": "exo",
    "lev": "lev",
    "le": "lev",
    "leviticus": "lev",
    "num": "num",
    "nu": "num",
    "numb": "num",
    "numbers": "num",
    "deu": "deu",
    "dt": "deu",
    "deut": "deu",
    "deuteronomy": "deu",
    # History
    "jos": "jos",
    "josh": "jos",
    "joshua": "jos",
    "jdg": "jdg",
    "judg": "jdg",
    "judges": "jdg",
    "rut": "rut",
    "ru": "rut",
    "ruth": "rut",
    "1sa": "1sa",
    "1 sam": "1sa",
    "1 samuel": "1sa",
    "1sam": "1sa",
    "2sa": "2sa",
    "2 sam": "2sa",
    "2 samuel": "2sa",
    "2sam": "2sa",
    "1ki": "1ki",
    "1 kgs": "1ki",
    "1 kings": "1ki",
    "1kgs": "1ki",
    "2ki": "2ki",
    "2 kgs": "2ki",
    "2 kings": "2ki",
    "2kgs": "2ki",
    "1ch": "1ch",
    "1 chr": "1ch",
    "1 chronicles": "1ch",
    "2ch": "2ch",
    "2 chr": "2ch",
    "2 chronicles": "2ch",
    "ezr": "ezr",
    "ezra": "ezr",
    "neh": "neh",
    "nehemiah": "neh",
    "est": "est",
    "esther": "est",
    # Wisdom
    "job": "job",
    "psa": "psa",
    "ps": "psa",
    "pss": "psa",
    "psalm": "psa",
    "psalms": "psa",
    "pro": "pro",
    "prov": "pro",
    "proverbs": "pro",
    "ecc": "ecc",
    "eccl": "ecc",
    "ecclesiastes": "ecc",
    "sng": "sng",
    "song": "sng",
    "cant": "sng",
    # Major prophets
    "isa": "isa",
    "is": "isa",
    "isaiah": "isa",
    "jer": "jer",
    "jeremiah": "jer",
    "lam": "lam",
    "lamentations": "lam",
    "eze": "eze",
    "ezek": "eze",
    "ezekiel": "eze",
    "dan": "dan",
    "daniel": "dan",
    # Minor prophets
    "hos": "hos",
    "hosea": "hos",
    "jol": "joe",
    "joel": "joe",
    "amo": "amo",
    "am": "amo",
    "amos": "amo",
    "oba": "oba",
    "obadiah": "oba",
    "jon": "jon",
    "jonah": "jon",
    "mic": "mic",
    "micah": "mic",
    "nah": "nah",
    "nahum": "nah",
    "hab": "hab",
    "habakkuk": "hab",
    "zep": "zep",
    "zeph": "zep",
    "zephaniah": "zep",
    "hag": "hag",
    "haggai": "hag",
    "zec": "zec",
    "zech": "zec",
    "zechariah": "zec",
    "mal": "mal",
    "malachi": "mal",
    # NT
    "mat": "mat",
    "mt": "mat",
    "matt": "mat",
    "matthew": "mat",
    "mar": "mrk",
    "mk": "mrk",
    "mark": "mrk",
    "luk": "luk",
    "lk": "luk",
    "luke": "luk",
    "joh": "jhn",
    "jn": "jhn",
    "john": "jhn",
    "act": "act",
    "acts": "act",
    "rom": "rom",
    "romans": "rom",
    "1co": "1co",
    "1 cor": "1co",
    "1 corinthians": "1co",
    "1cor": "1co",
    "2co": "2co",
    "2 cor": "2co",
    "2 corinthians": "2co",
    "2cor": "2co",
    "gal": "gal",
    "galatians": "gal",
    "eph": "eph",
    "ephesians": "eph",
    "php": "phi",
    "phil": "phi",
    "philippians": "phi",
    "col": "col",
    "colossians": "col",
    "1th": "1th",
    "1 thess": "1th",
    "1 thessalonians": "1th",
    "2th": "2th",
    "2 thess": "2th",
    "2 thessalonians": "2th",
    "1ti": "1ti",
    "1 tim": "1ti",
    "1 timothy": "1ti",
    "2ti": "2ti",
    "2 tim": "2ti",
    "2 timothy": "2ti",
    "tit": "tit",
    "titus": "tit",
    "phm": "phm",
    "phlm": "phm",
    "philemon": "phm",
    "heb": "heb",
    "hebrews": "heb",
    "jas": "jam",
    "james": "jam",
    "1pe": "1pe",
    "1 pet": "1pe",
    "1 peter": "1pe",
    "2pe": "2pe",
    "2 pet": "2pe",
    "2 peter": "2pe",
    "1jn": "1jn",
    "1 john": "1jn",
    "2jn": "2jn",
    "2 john": "2jn",
    "3jn": "3jn",
    "3 john": "3jn",
    "jud": "jud",
    "jude": "jud",
    "rev": "rev",
    "revelation": "rev",
    # Apocrypha used in this canon
    "tob": "tob",
    "tobit": "tob",
    "jdt": "jdt",
    "judith": "jdt",
    "wis": "wis",
    "wisdom": "wis",
    "sir": "sir",
    "sirach": "sir",
    "ecclus": "sir",
    "bar": "bar",
    "baruch": "bar",
    "1ma": "1ma",
    "1 macc": "1ma",
    "1 maccabees": "1ma",
    "2ma": "2ma",
    "2 macc": "2ma",
    "2 maccabees": "2ma",
    "1en": "1en",
    "1 enoch": "1en",
    "enoch": "1en",
    "jub": "jub",
    "jubilees": "jub",
}

# Reference pattern. Captures: (intro, book, ch, v).
# intro:   see / cf / Cf. / compare etc.
# book:    optional ordinal (1, 2, 3) + book name (one or two words like "Song of")
# ch:v:    digits with : or . separator
REF_PAT = re.compile(
    r"\b(see|cf\.?|See|Cf\.?|compare|Compare)\s+"
    r"(?:also\s+)?"
    r"((?:[123]\s+)?(?:[A-Z][a-z]+)\.?)\s+"
    r"(\d+)[:.\u2013\u2010-](\d+)\b",
    re.UNICODE,
)


def build_anchor_index(epub_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Scan all HTML files for v-* and ch-* ids; return two file-maps.

    Returns:
        (verse_anchors, chapter_anchors) — each maps anchor id → filename.
        verse_anchors:   v-{code}-{ch}-{v}[a-z]?
        chapter_anchors: ch-{bxx}-c{ch}
    """
    verse_anchors: dict[str, str] = {}
    chapter_anchors: dict[str, str] = {}
    v_pat = re.compile(r'id="(v-[a-z0-9]+-\d+-\d+[a-z]?)"')
    ch_pat = re.compile(r'id="(ch-b\d+-c\d+)"')
    for f in sorted(epub_dir.glob("index_split_*.html")):
        text = f.read_text(encoding="utf-8")
        for m in v_pat.finditer(text):
            verse_anchors.setdefault(m.group(1), f.name)
        for m in ch_pat.finditer(text):
            chapter_anchors.setdefault(m.group(1), f.name)
    return verse_anchors, chapter_anchors


def resolve_book(name_raw: str) -> str | None:
    """Map a free-form book reference (e.g. '1 Cor', 'Gen', 'Psalms') to its code."""
    name = name_raw.strip().rstrip(".").lower()
    return ABBREV.get(name) or ABBREV.get(name.replace(" ", ""))


def wrap_refs_in_block(
    block: str,
    verse_anchors: dict[str, str],
    chapter_anchors: dict[str, str],
    code_to_bxx: dict[str, str],
    counters: Counter,
) -> str:
    """Wrap eligible refs inside one aside block. Skips refs already inside <a>."""

    def replace(m: re.Match) -> str:
        full = m.group(0)
        book_raw, ch, v = m.group(2), m.group(3), m.group(4)
        # Already linked? Look at preceding 60 chars in the block.
        before = block[max(0, m.start() - 60) : m.start()]
        last_open = before.rfind("<a ")
        last_close = before.rfind("</a>")
        if last_open > last_close:
            counters["skip_already_linked"] += 1
            return full

        code = resolve_book(book_raw)
        if not code:
            counters["skip_unknown_book"] += 1
            counters[f"unknown:{book_raw.strip().lower()}"] += 1
            return full

        # Try most-specific anchor first.
        v_anchor = f"v-{code}-{ch}-{v}"
        if v_anchor in verse_anchors:
            counters["wrapped_verse"] += 1
            return f'<a href="{verse_anchors[v_anchor]}#{v_anchor}">{full}</a>'

        # Fall back to chapter-level anchor (Strategy-B books and verse-out-of-range).
        bxx = code_to_bxx.get(code)
        if bxx:
            ch_anchor = f"ch-{bxx}-c{ch}"
            if ch_anchor in chapter_anchors:
                counters["wrapped_chapter"] += 1
                return f'<a href="{chapter_anchors[ch_anchor]}#{ch_anchor}">{full}</a>'

        counters["skip_no_anchor"] += 1
        return full

    return REF_PAT.sub(replace, block)


# Match either commentary notes OR verse-popover asides (both are Claude-authored).
ASIDE_PAT = re.compile(
    r'(<aside class="(?:note (?:note-comm|note-word|note-source|note-variant)|vnote)[^"]*"[^>]*>)'
    r"(.*?)"
    r"(</aside>)",
    re.DOTALL,
)


def process_file(
    path: Path,
    verse_anchors: dict[str, str],
    chapter_anchors: dict[str, str],
    code_to_bxx: dict[str, str],
    counters: Counter,
) -> str:
    """Return the rewritten HTML for one file."""
    text = path.read_text(encoding="utf-8")

    def on_aside(m: re.Match) -> str:
        open_tag, body, close_tag = m.group(1), m.group(2), m.group(3)
        new_body = wrap_refs_in_block(body, verse_anchors, chapter_anchors, code_to_bxx, counters)
        return open_tag + new_body + close_tag

    return ASIDE_PAT.sub(on_aside, text)


def main() -> None:
    p = argparse.ArgumentParser(description="Auto-link cross-refs in commentary notes.")
    p.add_argument("--epub-dir", type=Path, default=EPUB_DIR)
    p.add_argument("--book", help="restrict to this book code (e.g. 'gen')")
    p.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    p.add_argument("--dry-run", action="store_true", help="preview only (default behaviour)")
    args = p.parse_args()

    if not args.epub_dir.is_dir():
        print(f"ERROR: epub dir not found: {args.epub_dir}", file=sys.stderr)
        sys.exit(1)

    print("Indexing v- and ch- anchors…")
    verse_anchors, chapter_anchors = build_anchor_index(args.epub_dir)
    print(f"  {len(verse_anchors)} verse anchors, {len(chapter_anchors)} chapter anchors")

    # Build code → bxx map for chapter-fallback links.
    code_to_bxx = {b["code"]: b["bxx"] for b in config.load_books()}

    if args.book:
        try:
            book = config.get_book(args.book)
        except KeyError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
        files = [args.epub_dir / f for f in book["files"]]
    else:
        files = sorted(args.epub_dir.glob("index_split_*.html"))

    counters: Counter = Counter()
    files_changed = 0
    for path in files:
        original = path.read_text(encoding="utf-8")
        new_text = process_file(path, verse_anchors, chapter_anchors, code_to_bxx, counters)
        if new_text != original:
            files_changed += 1
            if args.apply:
                path.write_text(new_text, encoding="utf-8")

    mode = "applied" if args.apply else "(dry-run)"
    print(f"\nResult {mode}:")
    print(f"  Files affected: {files_changed} / {len(files)}")
    print(f"  Refs wrapped (verse-precision):   {counters['wrapped_verse']}")
    print(f"  Refs wrapped (chapter fallback):  {counters['wrapped_chapter']}")
    print(f"  Skipped (already linked):         {counters['skip_already_linked']}")
    print(f"  Skipped (book not in canon):      {counters['skip_unknown_book']}")
    print(f"  Skipped (no matching anchor):     {counters['skip_no_anchor']}")

    unknowns = sorted(
        ((k.split(":", 1)[1], v) for k, v in counters.items() if k.startswith("unknown:")),
        key=lambda kv: -kv[1],
    )
    if unknowns:
        print("\n  Unknown book names encountered (could be added to ABBREV):")
        for name, n in unknowns[:10]:
            print(f"    {n:>4}  {name!r}")

    if not args.apply:
        print("\n(Dry-run only. Re-run with --apply to write changes.)")


if __name__ == "__main__":
    main()

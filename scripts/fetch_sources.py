#!/usr/bin/env python3
"""
fetch_sources.py — Build the local public-domain reference corpus used
by ``prospect.py`` to draft candidate notes.

The data we cache lives under ``content/sources/`` and is loaded by
``scripts/core/sources.py``. All sources here are explicitly PD or CC-BY,
and each cached file carries an attribution header in its companion
``ATTRIBUTIONS.md``.

Currently fetched:

  1. Strong's Hebrew Dictionary (1894, PD; openscriptures CC-BY-SA derivation)
     ~2 MB — keyed by Strong's number (H1..H8674), each entry has lemma,
     transliteration, derivation, and definition.

  2. Treasury of Scripture Knowledge (1830s, PD; openbible.info CC-BY)
     ~1.9 MB compressed — tab-separated cross-reference index, ~340K
     directional links, scored by community-vote intensity.

  3. Nave's Topical Bible (1896, PD; phase χ.7) — topical concordance
     by Orville J. Nave with ~20K topics and ~100K verse references.
     Best-effort fetch from a list of upstream mirrors; if all fail,
     the platform remains usable and the user can drop a pre-built
     ``naves_topical.json`` of the documented shape into
     ``content/sources/`` directly.

Run once after first checkout, or whenever the upstream sources publish
a new version. Idempotent; existing files are kept unless ``--force``.

Examples:
    python3 scripts/fetch_sources.py            # fetch missing only
    python3 scripts/fetch_sources.py --force    # re-fetch everything
    python3 scripts/fetch_sources.py --list     # list what's available

Exit codes:
    0  all sources present (or fetched ok)
    1  one or more fetches failed
    2  setup error
"""

import argparse
import json
import re
import sys
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO_ROOT / "content" / "sources"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ----------------------------------------------------------------------
# Strong's Hebrew Dictionary
# ----------------------------------------------------------------------

STRONGS_HEBREW_URL = (
    "https://raw.githubusercontent.com/openscriptures/strongs/master/"
    "hebrew/strongs-hebrew-dictionary.js"
)

STRONGS_HEBREW_PATH = SOURCES_DIR / "strongs_hebrew.json"
STRONGS_HEBREW_LICENCE = (
    "Strong's Exhaustive Concordance of the Bible, James Strong (1894). "
    "Public domain. Digital edition by Open Scriptures, CC-BY-SA."
)


def fetch_strongs_hebrew(force: bool = False) -> bool:
    if STRONGS_HEBREW_PATH.is_file() and not force:
        print(f"  {DIM}strongs_hebrew.json already present{RESET}")
        return True
    print(f"  {DIM}fetching Strong's Hebrew dictionary…{RESET}")
    try:
        with urllib.request.urlopen(STRONGS_HEBREW_URL, timeout=30) as r:
            text = r.read().decode("utf-8")
    except Exception as e:
        print(f"  {RED}✗ download failed: {e}{RESET}", file=sys.stderr)
        return False

    # Strip JS wrapper: `var strongsHebrewDictionary = {...};`
    m = re.search(r"strongsHebrewDictionary\s*=\s*(\{.*\})", text, re.DOTALL)
    if not m:
        print(f"  {RED}✗ unexpected format — no dictionary object found{RESET}", file=sys.stderr)
        return False
    raw_json = m.group(1).rstrip().rstrip(";")
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"  {RED}✗ JSON parse failed: {e}{RESET}", file=sys.stderr)
        return False

    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    STRONGS_HEBREW_PATH.write_text(
        json.dumps(data, indent=None, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"  {GREEN}✓{RESET} strongs_hebrew.json  {DIM}({len(data):,} entries, "
          f"{STRONGS_HEBREW_PATH.stat().st_size / 1024:.0f} KB){RESET}")
    return True


# ----------------------------------------------------------------------
# Treasury of Scripture Knowledge
# ----------------------------------------------------------------------

TSK_URL = "https://a.openbible.info/data/cross-references.zip"
TSK_PATH = SOURCES_DIR / "tsk_xrefs.json"
TSK_LICENCE = (
    "Treasury of Scripture Knowledge (Canne, Browne, Blayney, Scott et al., "
    "1830s). Public domain. Digital edition by openbible.info, CC-BY 4.0."
)

# Map openbible.info book codes to our internal codes (mostly identical
# but a few differ; we keep the canonical-3-letter form).
TSK_BOOK_REMAP = {
    "Gen": "gen", "Exod": "exo", "Lev": "lev", "Num": "num", "Deut": "deu",
    "Josh": "jos", "Judg": "jdg", "Ruth": "rut",
    "1Sam": "1sa", "2Sam": "2sa", "1Kgs": "1ki", "2Kgs": "2ki",
    "1Chr": "1ch", "2Chr": "2ch", "Ezra": "ezr", "Neh": "neh", "Esth": "est",
    "Job": "job", "Ps": "psa", "Prov": "pro", "Eccl": "ecc", "Song": "sng",
    "Isa": "isa", "Jer": "jer", "Lam": "lam", "Ezek": "ezk", "Dan": "dan",
    "Hos": "hos", "Joel": "jol", "Amos": "amo", "Obad": "oba", "Jonah": "jon",
    "Mic": "mic", "Nah": "nam", "Hab": "hab", "Zeph": "zep", "Hag": "hag",
    "Zech": "zec", "Mal": "mal",
    "Matt": "mat", "Mark": "mrk", "Luke": "luk", "John": "jhn",
    "Acts": "act",
    "Rom": "rom", "1Cor": "1co", "2Cor": "2co", "Gal": "gal", "Eph": "eph",
    "Phil": "php", "Col": "col", "1Thess": "1th", "2Thess": "2th",
    "1Tim": "1ti", "2Tim": "2ti", "Titus": "tit", "Phlm": "phm",
    "Heb": "heb", "Jas": "jas", "1Pet": "1pe", "2Pet": "2pe",
    "1John": "1jn", "2John": "2jn", "3John": "3jn",
    "Jude": "jud", "Rev": "rev",
}


def _parse_tsk_ref(s: str) -> tuple | None:
    """Parse 'Gen.1.1' or 'Gen.1.1-Gen.1.3' → ('gen', 1, 1) (start of range)."""
    s = s.split("-")[0]  # range start
    parts = s.split(".")
    if len(parts) != 3:
        return None
    book, ch, vs = parts
    book = TSK_BOOK_REMAP.get(book)
    if not book:
        return None
    try:
        return (book, int(ch), int(vs))
    except ValueError:
        return None


def fetch_tsk(force: bool = False) -> bool:
    if TSK_PATH.is_file() and not force:
        print(f"  {DIM}tsk_xrefs.json already present{RESET}")
        return True
    print(f"  {DIM}fetching Treasury of Scripture Knowledge…{RESET}")
    try:
        with urllib.request.urlopen(TSK_URL, timeout=30) as r:
            zip_bytes = r.read()
    except Exception as e:
        print(f"  {RED}✗ download failed: {e}{RESET}", file=sys.stderr)
        return False

    try:
        with zipfile.ZipFile(BytesIO(zip_bytes)) as z:
            text = z.read("cross_references.txt").decode("utf-8")
    except Exception as e:
        print(f"  {RED}✗ unzip failed: {e}{RESET}", file=sys.stderr)
        return False

    # Build {book: {chapter: {verse: [(target_book, ch, vs, votes), ...]}}}
    index: dict = {}
    n_links = 0
    n_skipped = 0
    for line in text.splitlines():
        if not line or line.startswith("#") or line.startswith("From"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        src = _parse_tsk_ref(parts[0])
        dst = _parse_tsk_ref(parts[1])
        if not src or not dst:
            n_skipped += 1
            continue
        try:
            votes = int(parts[2])
        except ValueError:
            votes = 0
        sb, sc, sv = src
        db, dc, dv = dst
        index.setdefault(sb, {}).setdefault(sc, {}).setdefault(sv, []).append(
            [db, dc, dv, votes]
        )
        n_links += 1

    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    TSK_PATH.write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"  {GREEN}✓{RESET} tsk_xrefs.json  {DIM}({n_links:,} links across "
          f"{sum(len(c) for c in index.values()):,} chapters, "
          f"{TSK_PATH.stat().st_size / 1024:.0f} KB; skipped {n_skipped} unparseable){RESET}")
    return True


# ----------------------------------------------------------------------
# Nave's Topical Bible (Phase χ.7)
# ----------------------------------------------------------------------

# Nave's Topical Bible (Orville J. Nave, 1896) is firmly in the public
# domain. The challenge is finding a clean structured digital edition.
# We try a list of candidate URLs in order; the user can prepend their
# own (e.g., a local mirror, a curated GitHub fork) by editing this list.
#
# Expected upstream shape (whichever URL succeeds, the parser detects
# the format and normalises to the JSON cache structure documented on
# ``scripts/core/sources.py:NavesTopical``).

NAVES_PATH = SOURCES_DIR / "naves_topical.json"
NAVES_LICENCE = (
    "Nave's Topical Bible, Orville J. Nave (1896). Public domain "
    "(US copyright lapsed; author died 1917, work first published 1896)."
)

# Best-effort mirror list. Each entry is (url, parser_kind). Parsers:
#   "openbible-topics-tsv" — openbible.info-style topic-votes.txt format
#   "json-topic-to-verses" — direct {"Topic": [["book", ch, vs], ...]}
#   "json-topic-to-refs"   — {"Topic": ["Gen 1:1", "Heb 11:3", ...]}
#   "ccel-text"            — ccel.org plain-text dump (most fragile)
NAVES_CANDIDATE_SOURCES: list[tuple[str, str]] = [
    # GitHub mirrors (most stable when they exist):
    (
        "https://raw.githubusercontent.com/scrollmapper/bible_databases_extras/"
        "main/naves/naves.json",
        "json-topic-to-refs",
    ),
    (
        "https://raw.githubusercontent.com/openbibleinfo/Topical-Bible/"
        "main/naves.json",
        "json-topic-to-refs",
    ),
    # openbible.info zipped TSV (their topic-votes data, when reachable):
    (
        "https://a.openbible.info/data/topic-votes.txt.zip",
        "openbible-topics-tsv",
    ),
    # CCEL fallback (HTML; the plain-text dump path isn't always present):
    (
        "https://www.ccel.org/n/nave/topical/topical.txt",
        "ccel-text",
    ),
]


# Reuse the openbible-style 3-letter book codes already mapped for TSK.
# A few new ones may appear in Nave's reference notation (e.g. "Mt", "Mk",
# "Lk", "Jn", "Ac", "Ro", "1Co", "2Co", "1Pt", "2Pt", "Jas", "Re").
NAVES_BOOK_REMAP = dict(TSK_BOOK_REMAP)
NAVES_BOOK_REMAP.update({
    # Common abbreviations Nave's editions use that aren't in TSK_BOOK_REMAP
    "Mt": "mat", "Mk": "mrk", "Lk": "luk", "Jn": "jhn",
    "Ac": "act", "Ro": "rom", "1Pt": "1pe", "2Pt": "2pe",
    "Re": "rev", "Sg": "sng",
    "1Co": "1co", "2Co": "2co",
    "1Th": "1th", "2Th": "2th",
    "1Ti": "1ti", "2Ti": "2ti",
    "1Jn": "1jn", "2Jn": "2jn", "3Jn": "3jn",
    "Phm": "phm", "Phlm": "phm", "Phil": "php", "Php": "php",
    # Lower-case variants seen in some mirrors
    "gen": "gen", "exod": "exo", "lev": "lev", "num": "num", "deut": "deu",
    # Full English book names (Nave's plain-text dump uses these)
    "Genesis": "gen", "Exodus": "exo", "Leviticus": "lev",
    "Numbers": "num", "Deuteronomy": "deu", "Joshua": "jos",
    "Judges": "jdg", "Ruth": "rut",
    "1Samuel": "1sa", "2Samuel": "2sa", "1Kings": "1ki", "2Kings": "2ki",
    "1Chronicles": "1ch", "2Chronicles": "2ch",
    "Ezra": "ezr", "Nehemiah": "neh", "Esther": "est",
    "Job": "job", "Psalms": "psa", "Psalm": "psa",
    "Proverbs": "pro", "Ecclesiastes": "ecc",
    "Song": "sng", "SongofSolomon": "sng", "Songs": "sng",
    "Isaiah": "isa", "Jeremiah": "jer", "Lamentations": "lam",
    "Ezekiel": "ezk", "Daniel": "dan",
    "Hosea": "hos", "Joel": "jol", "Amos": "amo", "Obadiah": "oba",
    "Jonah": "jon", "Micah": "mic", "Nahum": "nam", "Habakkuk": "hab",
    "Zephaniah": "zep", "Haggai": "hag", "Zechariah": "zec", "Malachi": "mal",
    "Matthew": "mat", "Mark": "mrk", "Luke": "luk", "John": "jhn",
    "Acts": "act", "Romans": "rom",
    "1Corinthians": "1co", "2Corinthians": "2co",
    "Galatians": "gal", "Ephesians": "eph", "Philippians": "php",
    "Colossians": "col",
    "1Thessalonians": "1th", "2Thessalonians": "2th",
    "1Timothy": "1ti", "2Timothy": "2ti",
    "Titus": "tit", "Philemon": "phm",
    "Hebrews": "heb", "James": "jas",
    "1Peter": "1pe", "2Peter": "2pe",
    "1John": "1jn", "2John": "2jn", "3John": "3jn",
    "Jude": "jud", "Revelation": "rev",
})


_REF_RE = re.compile(
    r"^([1-3]?\s?[A-Za-z]+)\s*\.?\s*(\d+)\s*[:.]\s*(\d+)"
)


def _parse_naves_ref(s: str) -> tuple[str, int, int] | None:
    """Parse 'Genesis 1:1' / 'Gen.1.1' / '1 Cor 15:45' → ('gen', 1, 1)."""
    s = s.strip()
    if not s:
        return None
    m = _REF_RE.match(s)
    if not m:
        return None
    raw_book = re.sub(r"\s+", "", m.group(1))
    book = NAVES_BOOK_REMAP.get(raw_book)
    if not book:
        # Try title-case fallback (e.g. "GENESIS" → "Genesis" → "gen")
        book = NAVES_BOOK_REMAP.get(raw_book.title())
    if not book:
        return None
    try:
        return (book, int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _build_naves_indices(forward: dict[str, list]) -> dict:
    """Build the canonical cache shape from a forward index of
    {topic: [(book, ch, vs), ...]}. Builds the reverse index (verses)
    and the meta block.

    Tolerates ref tuples or list-of-3 elements.
    """
    topics = {}
    verses: dict = {}
    n_refs = 0
    for topic, raw_refs in forward.items():
        cleaned = []
        for r in raw_refs:
            if isinstance(r, (list, tuple)) and len(r) >= 3:
                book = r[0]
                try:
                    ch = int(r[1]); vs = int(r[2])
                except (TypeError, ValueError):
                    continue
            elif isinstance(r, str):
                parsed = _parse_naves_ref(r)
                if not parsed:
                    continue
                book, ch, vs = parsed
            else:
                continue
            cleaned.append([book, ch, vs])
            verses.setdefault(book, {}).setdefault(str(ch), {}) \
                  .setdefault(str(vs), []).append(topic)
            n_refs += 1
        if cleaned:
            topics[topic] = cleaned
    return {
        "_meta": {
            "n_topics": len(topics),
            "n_refs": n_refs,
            "source": "Nave's Topical Bible (1896, PD)",
        },
        "topics": topics,
        "verses": verses,
    }


def _fetch_naves_json_topic_to_refs(url: str) -> dict | None:
    """Fetcher for {"Topic": ["Gen 1:1", ...] | [["gen",1,1], ...]} JSON."""
    with urllib.request.urlopen(url, timeout=30) as r:
        raw = r.read().decode("utf-8")
    forward = json.loads(raw)
    if not isinstance(forward, dict):
        return None
    return _build_naves_indices(forward)


def _fetch_naves_openbible_tsv(url: str) -> dict | None:
    """Fetcher for openbible.info topic-votes zipped TSV (topic\tref\tvotes).
    Uses only the topic+ref columns; votes are not stored (Nave's model
    is unweighted)."""
    with urllib.request.urlopen(url, timeout=30) as r:
        zip_bytes = r.read()
    forward: dict[str, list] = {}
    with zipfile.ZipFile(BytesIO(zip_bytes)) as z:
        # Take the first .txt member
        names = [n for n in z.namelist() if n.lower().endswith(".txt")]
        if not names:
            return None
        text = z.read(names[0]).decode("utf-8", errors="replace")
    for line in text.splitlines():
        if not line or line.startswith("#") or line.startswith("Topic"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        topic = parts[0].strip()
        ref = parts[1].strip()
        parsed = _parse_naves_ref(ref)
        if not parsed:
            continue
        forward.setdefault(topic, []).append(list(parsed))
    if not forward:
        return None
    return _build_naves_indices(forward)


def fetch_naves_topical(force: bool = False) -> bool:
    """Try each NAVES_CANDIDATE_SOURCES URL in order; first success wins.

    On success, writes ``content/sources/naves_topical.json`` in the
    canonical shape consumed by ``scripts.core.sources.NavesTopical``.

    On total failure, prints a clear next-step (the user can drop a
    pre-built ``naves_topical.json`` of the documented shape into
    ``content/sources/`` manually).
    """
    if NAVES_PATH.is_file() and not force:
        print(f"  {DIM}naves_topical.json already present{RESET}")
        return True
    print(f"  {DIM}fetching Nave's Topical Bible…{RESET}")

    for url, kind in NAVES_CANDIDATE_SOURCES:
        try:
            if kind == "json-topic-to-refs":
                idx = _fetch_naves_json_topic_to_refs(url)
            elif kind == "openbible-topics-tsv":
                idx = _fetch_naves_openbible_tsv(url)
            elif kind == "ccel-text":
                # The CCEL plain-text path is fragile and parser-heavy;
                # left as a known-not-quite-implemented fallback. Skip
                # gracefully so we move to the next candidate.
                continue
            else:
                continue
        except Exception as e:
            print(f"  {DIM}  · {url[:60]}… → {type(e).__name__}: "
                  f"{str(e)[:50]}{RESET}", file=sys.stderr)
            continue
        if idx and idx.get("topics"):
            SOURCES_DIR.mkdir(parents=True, exist_ok=True)
            NAVES_PATH.write_text(
                json.dumps(idx, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            meta = idx["_meta"]
            kb = NAVES_PATH.stat().st_size / 1024
            print(f"  {GREEN}✓{RESET} naves_topical.json  "
                  f"{DIM}({meta['n_topics']:,} topics, "
                  f"{meta['n_refs']:,} refs, {kb:.0f} KB){RESET}")
            return True

    # Everything failed.
    print(f"  {YELLOW}–{RESET} naves_topical.json  "
          f"{DIM}(no upstream reachable; place a pre-built file at "
          f"{NAVES_PATH.relative_to(REPO_ROOT)} matching the shape "
          f"documented in scripts/core/sources.py:NavesTopical){RESET}",
          file=sys.stderr)
    return False


# ----------------------------------------------------------------------
# Attribution file
# ----------------------------------------------------------------------


def write_attributions() -> None:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    attr_path = SOURCES_DIR / "ATTRIBUTIONS.md"
    attr_path.write_text(
        "# Source attributions\n\n"
        "This directory caches public-domain reference works used by "
        "`scripts/prospect.py` to draft candidate notes. Every fetched "
        "source is named below with its licence; the cached files are "
        "redistributable under those terms.\n\n"
        "## Strong's Hebrew Dictionary\n\n"
        f"{STRONGS_HEBREW_LICENCE}\n\n"
        "Source: <https://github.com/openscriptures/strongs>\n\n"
        "## Treasury of Scripture Knowledge\n\n"
        f"{TSK_LICENCE}\n\n"
        "Source: <https://www.openbible.info/labs/cross-references/>\n\n"
        "## Nave's Topical Bible\n\n"
        f"{NAVES_LICENCE}\n\n"
        "Source: see `scripts/fetch_sources.py:NAVES_CANDIDATE_SOURCES` "
        "for the upstream URL list tried at fetch time. The original 1896 "
        "edition is hosted on the Internet Archive "
        "(<https://archive.org/details/topicalbibledige00naveuoft>); "
        "structured digital editions are aggregated from CCEL and "
        "openbible.info topic data.\n",
        encoding="utf-8",
    )


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def cmd_list() -> None:
    sources = [
        ("Strong's Hebrew", STRONGS_HEBREW_PATH),
        ("TSK Cross-references", TSK_PATH),
        ("Nave's Topical Bible", NAVES_PATH),
    ]
    for name, path in sources:
        if path.is_file():
            kb = path.stat().st_size / 1024
            print(f"  {GREEN}✓{RESET} {name:30s} {DIM}{kb:.0f} KB{RESET}")
        else:
            print(f"  {YELLOW}–{RESET} {name:30s} {DIM}not fetched{RESET}")


def main() -> None:
    p = argparse.ArgumentParser(
        description="Fetch / cache PD reference corpora used by prospect.py.",
    )
    p.add_argument("--force", action="store_true", help="re-fetch even if cached")
    p.add_argument("--list", action="store_true", help="list source status and exit")
    args = p.parse_args()

    if args.list:
        cmd_list()
        sys.exit(0)

    print(f"\n{BOLD}fetch_sources{RESET}")
    ok = fetch_strongs_hebrew(force=args.force)
    ok &= fetch_tsk(force=args.force)
    # Nave's is best-effort: a failed fetch doesn't cause a non-zero exit
    # because the platform stays usable (NaveTopicalDetector skips
    # gracefully when the source is missing — see prospect.py and §χ.7).
    fetch_naves_topical(force=args.force)
    write_attributions()

    print()
    cmd_list()
    print()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

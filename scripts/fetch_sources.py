#!/usr/bin/env python3
"""
fetch_sources.py — Build the local public-domain reference corpus used
by ``prospect.py`` to draft candidate notes.

Phase υ.7 (2026-05-08): the source list — URLs, parser kinds, license
strings, "required vs best-effort" — is now declarative in
``content/sources/_fetchers.json`` and loaded by
``scripts.core.fetcher_config``. To add a new source: drop a parser
into ``PARSERS`` below, register its name in
``scripts.core.fetcher_config.KNOWN_PARSERS``, and add a `sources[]`
entry to ``_fetchers.json``. No constants need touching here.

The cache files live under ``content/sources/`` and are loaded by
``scripts/core/sources.py``. All sources are explicitly PD or CC-BY,
with attribution recorded in the companion ``ATTRIBUTIONS.md``.

Run once after first checkout, or whenever the upstream sources publish
a new version. Idempotent; existing files are kept unless ``--force``.

Examples:
    python3 scripts/fetch_sources.py            # fetch missing only
    python3 scripts/fetch_sources.py --force    # re-fetch everything
    python3 scripts/fetch_sources.py --list     # list what's available

Exit codes:
    0  all required sources present (or fetched ok)
    1  one or more REQUIRED fetches failed (best-effort sources don't
       affect exit code; the platform stays usable without them)
    2  setup error (e.g. _fetchers.json missing or malformed)
"""

import argparse
import json
import re
import sys
import zipfile
from io import BytesIO
from pathlib import Path

# sys.path bootstrap so this script runs both as `python3 scripts/fetch_sources.py`
# and as `python3 -m scripts.fetch_sources`.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.core.fetcher_config import (  # noqa: E402
    FetcherConfig,
    FetcherConfigError,
    Source,
    load_fetcher_config,
)
from scripts.core.notes_io import atomic_write  # noqa: E402  (ω.9)
from scripts.core import http as _http  # noqa: E402  (ω.10)
from scripts.core.http import DEFAULT_PD_SOURCES_ALLOWLIST  # noqa: E402  (ξ.10.1)
from scripts.core.canonical_verse_counts import canonical_book_shape  # noqa: E402  (Nave's coord guard)

SOURCES_DIR = REPO_ROOT / "content" / "sources"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ======================================================================
# PARSERS — each takes a URL, returns a JSON-ready dict or None on
# failure. The dict is the cache shape the corresponding loader in
# scripts/core/sources.py expects.
# ======================================================================


# ----------------------------------------------------------------------
# Strong's Hebrew Dictionary
# ----------------------------------------------------------------------


def _parse_strongs_hebrew_js(url: str) -> dict | None:
    """Strip the JS wrapper around openscriptures' Strong's Hebrew dump
    and return the dictionary keyed by H-number."""
    text = _http.get(url, allowlist=DEFAULT_PD_SOURCES_ALLOWLIST).decode("utf-8")  # ω.10 + ξ.10.1
    m = re.search(r"strongsHebrewDictionary\s*=\s*(\{.*\})", text, re.DOTALL)
    if not m:
        return None
    raw_json = m.group(1).rstrip().rstrip(";")
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


# ----------------------------------------------------------------------
# Strong's Greek Dictionary (χ.1)
# ----------------------------------------------------------------------


def _parse_strongs_greek_js(url: str) -> dict | None:
    """Strip the JS wrapper around openscriptures' Strong's Greek dump
    and return the dictionary keyed by G-number.

    Mirror of ``_parse_strongs_hebrew_js`` — same upstream repo, same
    JS-variable shape, just a different variable name
    (``strongsGreekDictionary``). The cached JSON is consumed by
    ``scripts.core.sources.StrongsGreek``."""
    text = _http.get(url, allowlist=DEFAULT_PD_SOURCES_ALLOWLIST).decode("utf-8")  # ω.10 + ξ.10.1
    m = re.search(r"strongsGreekDictionary\s*=\s*(\{.*\})", text, re.DOTALL)
    if not m:
        return None
    raw_json = m.group(1).rstrip().rstrip(";")
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


# ----------------------------------------------------------------------
# Treasury of Scripture Knowledge
# ----------------------------------------------------------------------


# Map openbible.info book codes to our internal codes (mostly identical
# but a few differ; we keep the canonical-3-letter form).
TSK_BOOK_REMAP = {
    "Gen": "gen",
    "Exod": "exo",
    "Lev": "lev",
    "Num": "num",
    "Deut": "deu",
    "Josh": "jos",
    "Judg": "jdg",
    "Ruth": "rut",
    "1Sam": "1sa",
    "2Sam": "2sa",
    "1Kgs": "1ki",
    "2Kgs": "2ki",
    "1Chr": "1ch",
    "2Chr": "2ch",
    "Ezra": "ezr",
    "Neh": "neh",
    "Esth": "est",
    "Job": "job",
    "Ps": "psa",
    "Prov": "pro",
    "Eccl": "ecc",
    "Song": "sng",
    "Isa": "isa",
    "Jer": "jer",
    "Lam": "lam",
    "Ezek": "eze",
    "Dan": "dan",
    "Hos": "hos",
    "Joel": "joe",
    "Amos": "amo",
    "Obad": "oba",
    "Jonah": "jon",
    "Mic": "mic",
    "Nah": "nah",
    "Hab": "hab",
    "Zeph": "zep",
    "Hag": "hag",
    "Zech": "zec",
    "Mal": "mal",
    "Matt": "mat",
    "Mark": "mrk",
    "Luke": "luk",
    "John": "jhn",
    "Acts": "act",
    "Rom": "rom",
    "1Cor": "1co",
    "2Cor": "2co",
    "Gal": "gal",
    "Eph": "eph",
    "Phil": "phi",
    "Col": "col",
    "1Thess": "1th",
    "2Thess": "2th",
    "1Tim": "1ti",
    "2Tim": "2ti",
    "Titus": "tit",
    "Phlm": "phm",
    "Heb": "heb",
    "Jas": "jam",
    "1Pet": "1pe",
    "2Pet": "2pe",
    "1John": "1jn",
    "2John": "2jn",
    "3John": "3jn",
    "Jude": "jud",
    "Rev": "rev",
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


def _parse_tsk_zip_tsv(url: str) -> dict | None:
    """Download openbible.info's cross-references ZIP and build the
    nested {book: {chapter: {verse: [(target_book, ch, vs, votes), ...]}}}
    cache structure consumed by scripts.core.sources.Tsk."""
    zip_bytes = _http.get(url, allowlist=DEFAULT_PD_SOURCES_ALLOWLIST)  # ω.10 + ξ.10.1
    with zipfile.ZipFile(BytesIO(zip_bytes)) as z:
        text = z.read("cross_references.txt").decode("utf-8")
    index: dict = {}
    for line in text.splitlines():
        if not line or line.startswith("#") or line.startswith("From"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        src = _parse_tsk_ref(parts[0])
        dst = _parse_tsk_ref(parts[1])
        if not src or not dst:
            continue
        try:
            votes = int(parts[2])
        except ValueError:
            votes = 0
        sb, sc, sv = src
        db, dc, dv = dst
        index.setdefault(sb, {}).setdefault(sc, {}).setdefault(sv, []).append([db, dc, dv, votes])
    return index if index else None


# ----------------------------------------------------------------------
# Nave's Topical Bible (Phase χ.7)
# ----------------------------------------------------------------------


# Reuse the openbible-style 3-letter book codes already mapped for TSK.
# A few new ones may appear in Nave's reference notation (e.g. "Mt", "Mk",
# "Lk", "Jn", "Ac", "Ro", "1Co", "2Co", "1Pt", "2Pt", "Jas", "Re").
NAVES_BOOK_REMAP = dict(TSK_BOOK_REMAP)
NAVES_BOOK_REMAP.update(
    {
        # Common abbreviations Nave's editions use that aren't in TSK_BOOK_REMAP
        "Mt": "mat",
        "Mk": "mrk",
        "Lk": "luk",
        "Jn": "jhn",
        "Ac": "act",
        "Ro": "rom",
        "1Pt": "1pe",
        "2Pt": "2pe",
        "Re": "rev",
        "Sg": "sng",
        "1Co": "1co",
        "2Co": "2co",
        "1Th": "1th",
        "2Th": "2th",
        "1Ti": "1ti",
        "2Ti": "2ti",
        "1Jn": "1jn",
        "2Jn": "2jn",
        "3Jn": "3jn",
        "Phm": "phm",
        "Phlm": "phm",
        "Phil": "phi",
        "Php": "phi",
        # Lower-case variants seen in some mirrors
        "gen": "gen",
        "exod": "exo",
        "lev": "lev",
        "num": "num",
        "deut": "deu",
        # Full English book names (Nave's plain-text dump uses these)
        "Genesis": "gen",
        "Exodus": "exo",
        "Leviticus": "lev",
        "Numbers": "num",
        "Deuteronomy": "deu",
        "Joshua": "jos",
        "Judges": "jdg",
        "Ruth": "rut",
        "1Samuel": "1sa",
        "2Samuel": "2sa",
        "1Kings": "1ki",
        "2Kings": "2ki",
        "1Chronicles": "1ch",
        "2Chronicles": "2ch",
        "Ezra": "ezr",
        "Nehemiah": "neh",
        "Esther": "est",
        "Job": "job",
        "Psalms": "psa",
        "Psalm": "psa",
        "Proverbs": "pro",
        "Ecclesiastes": "ecc",
        "Song": "sng",
        "SongofSolomon": "sng",
        "Songs": "sng",
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
        "1Corinthians": "1co",
        "2Corinthians": "2co",
        "Galatians": "gal",
        "Ephesians": "eph",
        "Philippians": "phi",
        "Colossians": "col",
        "1Thessalonians": "1th",
        "2Thessalonians": "2th",
        "1Timothy": "1ti",
        "2Timothy": "2ti",
        "Titus": "tit",
        "Philemon": "phm",
        "Hebrews": "heb",
        "James": "jam",
        "1Peter": "1pe",
        "2Peter": "2pe",
        "1John": "1jn",
        "2John": "2jn",
        "3John": "3jn",
        "Jude": "jud",
        "Revelation": "rev",
    }
)


_REF_RE = re.compile(r"^([1-3]?\s?[A-Za-z]+)\s*\.?\s*(\d+)\s*[:.]\s*(\d+)")


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


def _naves_coord_in_extent(book: str, ch: int, vs: int) -> bool:
    """True if (book, ch, vs) is within the book's canonical extent — or the
    book has no known canonical shape (Tewahedo distinctives etc.), in which
    case we can't validate and keep the ref. The upstream Nave's dump is
    OCR-noisy and emits impossible coordinates (e.g. Genesis 87:12, Deut 81:7);
    rejecting them here, at the boundary where external data enters the
    pipeline, stops them becoming notes that can never inject."""
    try:
        shape = canonical_book_shape(book)
    except Exception:
        return True
    if not shape:
        return True
    return ch in shape and 1 <= vs <= shape[ch]


def _build_naves_indices(forward: dict[str, list], *, source: str = "Nave's Topical Bible (1896, PD)") -> dict:
    """Build the canonical cache shape from a forward index of
    {topic: [(book, ch, vs), ...]}. Builds the reverse index (verses)
    and the meta block.

    ``source`` labels ``_meta.source``; it defaults to Nave's so every existing
    caller stays byte-identical. The Torrey's New Topical Textbook ingest (same
    index shape) passes its own label.

    Tolerates ref tuples or list-of-3 elements."""
    topics = {}
    verses: dict = {}
    n_refs = 0
    for topic, raw_refs in forward.items():
        cleaned = []
        for r in raw_refs:
            if isinstance(r, (list, tuple)) and len(r) >= 3:
                book = r[0]
                try:
                    ch = int(r[1])
                    vs = int(r[2])
                except (TypeError, ValueError):
                    continue
            elif isinstance(r, str):
                parsed = _parse_naves_ref(r)
                if not parsed:
                    continue
                book, ch, vs = parsed
            else:
                continue
            if not _naves_coord_in_extent(book, ch, vs):
                continue
            cleaned.append([book, ch, vs])
            verses.setdefault(book, {}).setdefault(str(ch), {}).setdefault(str(vs), []).append(topic)
            n_refs += 1
        if cleaned:
            topics[topic] = cleaned
    return {
        "_meta": {
            "n_topics": len(topics),
            "n_refs": n_refs,
            "source": source,
        },
        "topics": topics,
        "verses": verses,
    }


def _parse_naves_json_topic_to_refs(url: str) -> dict | None:
    """Parser for {"Topic": ["Gen 1:1", ...] | [["gen",1,1], ...]} JSON."""
    raw = _http.get(url, allowlist=DEFAULT_PD_SOURCES_ALLOWLIST).decode("utf-8")  # ω.10 + ξ.10.1
    forward = json.loads(raw)
    if not isinstance(forward, dict):
        return None
    return _build_naves_indices(forward)


def _parse_naves_openbible_tsv(url: str) -> dict | None:
    """Parser for openbible.info topic-votes zipped TSV (topic\tref\tvotes).
    Uses only the topic+ref columns; votes are not stored (Nave's model
    is unweighted)."""
    zip_bytes = _http.get(url, allowlist=DEFAULT_PD_SOURCES_ALLOWLIST)  # ω.10 + ξ.10.1
    forward: dict[str, list] = {}
    with zipfile.ZipFile(BytesIO(zip_bytes)) as z:
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


def _parse_ccel_text(url: str) -> dict | None:
    """Placeholder for the CCEL plain-text dump. The path is fragile and
    parser-heavy; left as a known-not-quite-implemented fallback. Returns
    None so the dispatcher tries the next candidate."""
    return None


# ----------------------------------------------------------------------
# Parser registry — names must match scripts.core.fetcher_config.KNOWN_PARSERS
# ----------------------------------------------------------------------


PARSERS: dict[str, callable] = {
    "strongs-hebrew-js": _parse_strongs_hebrew_js,
    "strongs-greek-js": _parse_strongs_greek_js,
    "tsk-zip-tsv": _parse_tsk_zip_tsv,
    "json-topic-to-refs": _parse_naves_json_topic_to_refs,
    "openbible-topics-tsv": _parse_naves_openbible_tsv,
    "ccel-text": _parse_ccel_text,
}


# ======================================================================
# Generic fetch flow — iterates a Source's candidates, writes the cache
# ======================================================================


def fetch_source(source: Source, force: bool = False) -> bool:
    """Fetch one configured source. Returns True on success (file present
    or freshly written), False on failure.

    Caller's responsibility to translate False → exit code based on
    ``source.required``."""
    cache_path = SOURCES_DIR / source.cache_path
    if cache_path.is_file() and not force:
        print(f"  {DIM}{source.cache_path} already present{RESET}")
        return True

    print(f"  {DIM}fetching {source.name}…{RESET}")

    for c in source.candidates:
        parser = PARSERS.get(c.parser)
        if parser is None:
            # The config validator should reject this; defensive skip.
            continue
        try:
            data = parser(c.url)
        except Exception as e:
            print(f"  {DIM}  · {c.url[:60]}… → {type(e).__name__}: {str(e)[:50]}{RESET}", file=sys.stderr)
            continue
        if not data:
            continue
        SOURCES_DIR.mkdir(parents=True, exist_ok=True)
        # ω.9 — atomic write; a crash mid-fetch leaves the previous
        # cache (or no file at all), never a partial JSON.
        atomic_write(
            cache_path,
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        )
        kb = cache_path.stat().st_size / 1024
        # Pull a meta-line if the parser returned one (Nave's format has
        # _meta with n_topics/n_refs); otherwise just file size.
        meta_extra = ""
        if isinstance(data, dict):
            meta = data.get("_meta") if isinstance(data.get("_meta"), dict) else None
            if meta:
                bits = []
                if "n_topics" in meta:
                    bits.append(f"{meta['n_topics']:,} topics")
                if "n_refs" in meta:
                    bits.append(f"{meta['n_refs']:,} refs")
                if bits:
                    meta_extra = ", ".join(bits) + ", "
            elif data and not meta:
                # Strong's: top-level dict of entries
                meta_extra = f"{len(data):,} entries, "
        print(f"  {GREEN}✓{RESET} {source.cache_path}  {DIM}({meta_extra}{kb:.0f} KB){RESET}")
        return True

    # All candidates exhausted.
    if source.required:
        print(
            f"  {RED}✗{RESET} {source.cache_path}  {DIM}(no upstream reachable; required source missing){RESET}",
            file=sys.stderr,
        )
    else:
        print(
            f"  {YELLOW}–{RESET} {source.cache_path}  "
            f"{DIM}(no upstream reachable; optional, platform stays usable){RESET}",
            file=sys.stderr,
        )
    return False


# ----------------------------------------------------------------------
# Attribution file — assembled from the loaded config so adding a new
# source automatically gets its license recorded.
# ----------------------------------------------------------------------


def write_attributions(config: FetcherConfig) -> None:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    attr_path = SOURCES_DIR / "ATTRIBUTIONS.md"
    # ω.9 — atomic write so a crash mid-write leaves the prior
    # ATTRIBUTIONS.md intact (or absent), never half-rendered.
    parts = [
        "# Source attributions\n\n"
        "This directory caches public-domain reference works used by "
        "`scripts/prospect.py` to draft candidate notes. Every fetched "
        "source is named below with its licence; the cached files are "
        "redistributable under those terms.\n\n"
        "The source list is declarative — see "
        "`content/sources/_fetchers.json` for the URL + parser-kind table "
        "and `scripts/core/fetcher_config.py` for the loader/schema.\n\n"
    ]
    for s in config.sources:
        parts.append(f"## {s.name}\n\n{s.license}\n\n")
        if len(s.candidates) == 1:
            parts.append(f"Source URL: <{s.candidates[0].url}>\n\n")
        else:
            parts.append("Source URLs (tried in order):\n\n")
            for c in s.candidates:
                parts.append(f"- <{c.url}> *(parser: `{c.parser}`)*\n")
            parts.append("\n")
    atomic_write(attr_path, "".join(parts))


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def cmd_list(config: FetcherConfig) -> None:
    for s in config.sources:
        path = SOURCES_DIR / s.cache_path
        suffix = "" if s.required else f" {DIM}(optional){RESET}"
        if path.is_file():
            kb = path.stat().st_size / 1024
            print(f"  {GREEN}✓{RESET} {s.name:30s} {DIM}{kb:.0f} KB{RESET}{suffix}")
        else:
            print(f"  {YELLOW}–{RESET} {s.name:30s} {DIM}not fetched{RESET}{suffix}")


def main() -> None:
    p = argparse.ArgumentParser(
        description="Fetch / cache PD reference corpora used by prospect.py.",
    )
    p.add_argument("--force", action="store_true", help="re-fetch even if cached")
    p.add_argument("--list", action="store_true", help="list source status and exit")
    args = p.parse_args()

    try:
        config = load_fetcher_config()
    except FetcherConfigError as e:
        print(f"  {RED}✗ fetcher config error:{RESET} {e}", file=sys.stderr)
        sys.exit(2)

    if args.list:
        cmd_list(config)
        sys.exit(0)

    print(f"\n{BOLD}fetch_sources{RESET}")

    overall_ok = True
    for src in config.sources:
        ok = fetch_source(src, force=args.force)
        if src.required and not ok:
            overall_ok = False
        # Best-effort sources don't affect overall_ok — by design (e.g.
        # NaveTopicalDetector skips gracefully when its source is absent
        # per prospect.py's resilient instantiation, χ.7).

    write_attributions(config)

    print()
    cmd_list(config)
    print()
    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()

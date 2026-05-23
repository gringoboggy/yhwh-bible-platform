"""scripts/extract_translation.py — parse a public-domain Bible into the
project's translation store (τ cluster).

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
    python scripts/extract_translation.py --list   # show registered τ ids
    python scripts/extract_translation.py kjv
    python scripts/extract_translation.py kjv --dry-run
    python scripts/extract_translation.py kjv --report
    python scripts/extract_translation.py web                # τ.1 (PD)

Adding a new translation: add an entry to ``TRANSLATIONS`` below; then
the user runs::

    1. Download eng-<id>_vpl.zip from the configured source URL
    2. unzip into content/translations/sources/<id>/
    3. python3 scripts/extract_translation.py <id> --report

Standalone — does not import any of the project's other modules so it
remains usable as a one-shot ingestion tool.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from collections import defaultdict
from collections.abc import Callable
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
    "GEN": "gen",
    "EXO": "exo",
    "LEV": "lev",
    "NUM": "num",
    "DEU": "deu",
    "JOS": "jos",
    "JDG": "jdg",
    "RUT": "rut",
    "1SA": "1sa",
    "2SA": "2sa",
    "1KI": "1ki",
    "2KI": "2ki",
    "1CH": "1ch",
    "2CH": "2ch",
    "EZR": "ezr",
    "NEH": "neh",
    "EST": "est",
    "JOB": "job",
    "PSA": "psa",
    "PRO": "pro",
    "ECC": "ecc",
    "SOL": "sng",  # Song of Solomon → Song of Songs
    "ISA": "isa",
    "JER": "jer",
    "LAM": "lam",
    "EZE": "eze",
    "DAN": "dan",
    "HOS": "hos",
    "JOE": "joe",
    "AMO": "amo",
    "OBA": "oba",
    "JON": "jon",
    "MIC": "mic",
    "NAH": "nah",
    "HAB": "hab",
    "ZEP": "zep",
    "HAG": "hag",
    "ZEC": "zec",
    "MAL": "mal",
    # Apocrypha / Deuterocanon
    "TOB": "tob",
    "JDT": "jdt",
    "ESG": "aes",  # Esther Greek additions → project's `aes`
    "WIS": "wis",
    "SIR": "sir",
    "BAR": "bar",  # SPECIAL: ch 6 is split out below into `lje`
    "PRA": "paz",  # Prayer of Azariah / Song of 3 Holy Children
    "SUS": "sus",
    "BEL": "bel",
    "1MA": "1ma",
    "2MA": "2ma",  # forward-compat: project lacks books.yaml
    # entries for these yet but the data
    # lands here for when they're added
    "1ES": "1es",
    "PRM": "man",  # Prayer of Manasses
    "4ES": "2es",  # 4 Esdras (Latin) = project's `2es`
    # New Testament
    "MAT": "mat",
    "MAR": "mrk",
    "LUK": "luk",
    "JOH": "jhn",
    "ACT": "act",
    "ROM": "rom",
    "1CO": "1co",
    "2CO": "2co",
    "GAL": "gal",
    "EPH": "eph",
    "PHI": "phi",
    "COL": "col",
    "1TH": "1th",
    "2TH": "2th",
    "1TI": "1ti",
    "2TI": "2ti",
    "TIT": "tit",
    "PHM": "phm",
    "HEB": "heb",
    "JAM": "jam",
    "1PE": "1pe",
    "2PE": "2pe",
    "1JO": "1jn",
    "2JO": "2jn",
    "3JO": "3jn",
    "JUD": "jud",
    "REV": "rev",
}

# Books in the project canon for which KJV+Apocrypha provides no text
# (these are Ethiopian-canon-only or simply absent from the standard
# Apocrypha): jub, 1en, 2en, mq1-3, 4ba, 1cl. Recorded for reporting
# only; the absence is expected and not an error.
PROJECT_BOOKS_OUTSIDE_KJV = {
    "jub",
    "1en",
    "2en",
    "mq1",
    "mq2",
    "mq3",
    "4ba",
    "1cl",
}


# ----------------------------------------------------------------------
# Translation registry — one entry per τ-cluster phase
# ----------------------------------------------------------------------
#
# Each entry carries the metadata that gets written to
# content/translations/<id>/_meta.yaml after extraction. The
# `source.fetched` field is filled at extract time (not stored here),
# so the same entry is reusable across re-fetches of the same source.
#
# Adding a new τ phase:
#   1. Pick the project's translation slug (lowercase id like "web")
#   2. Add a TRANSLATIONS[id] = {...} entry below
#   3. Document the user-side fetch step in the entry's `notes` field
#   4. The user downloads the source ZIP, unpacks to
#      content/translations/sources/<id>/, then runs this script.
#
# Translations not in the registry can still extract — they get a
# stub _meta.yaml with placeholder license/source fields. The
# registry is the right place to document license + provenance for
# the τ-cluster phases we ship infrastructure for.

TRANSLATIONS: dict[str, dict] = {
    "kjv": {
        "title": "King James Version + Apocrypha",
        "short_title": "KJV",
        "license": "Public Domain",
        "source": {
            "publisher": "eBible.org",
            "url": "https://eBible.org/eng-kjv/",
            "package": "eng-kjv_vpl.zip",
            "source_date": "2025-11-27",
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
    },
    "web": {
        "title": "World English Bible (with Apocrypha)",
        "short_title": "WEB",
        "license": "Public Domain",
        "source": {
            "publisher": "eBible.org",
            "url": "https://eBible.org/eng-web/",
            "package": "eng-web_vpl.zip",
            "source_date": None,  # filled at extract time
        },
        "notes": (
            "World English Bible — modern Public Domain English "
            "translation derived from the 1901 ASV. Phase τ.1 "
            "primary-translation alternative to the KJV's archaic "
            "register. Synergy with ρ.1 (LibriVox audio): WEB "
            "recordings are widely available for the audio-EPUB "
            "build pass. Letter of Jeremiah split rule (BAR ch 6 "
            "→ lje ch 1) applies if the WEB-with-Apocrypha "
            "package is the source; the WEB-66 package skips "
            "Apocrypha entirely."
        ),
    },
    "jps": {
        "title": "Jewish Publication Society Tanakh (1917)",
        "short_title": "JPS",
        "license": "Public Domain",
        "source": {
            "publisher": "eBible.org",
            "url": "https://eBible.org/eng-jps/",
            "package": "eng-jps_vpl.zip",
            "source_date": None,  # filled at extract time
        },
        "notes": (
            "Jewish Publication Society 1917 Tanakh — Public-Domain "
            "English translation of the Hebrew Bible. Closes the "
            "Hebrew column for the 6 of 9 editions that declare "
            "`hebrew` in popup_languages_default (ethiopian-tewahedo, "
            "catholic-study, jewish-study, scholarly-academic, "
            "anglican-bcp, lutheran-confessional). Pairs with "
            "the `wlc` (Westminster Leningrad Codex) consonantal "
            "Hebrew text — JPS provides the English-language "
            "channel; WLC provides the Hebrew-text channel. Phase "
            "τ.5-A ships infrastructure + Gen 1:1-3 seed; τ.5-A.x "
            "is the user-side full ingest (download eng-jps_vpl.zip, "
            "unzip into content/translations/sources/jps/, run "
            "this script). OT only — JPS is the Hebrew Bible, 39 "
            "books / ~23,000 verses."
        ),
    },
    "wlc": {
        "title": "Westminster Leningrad Codex (Hebrew)",
        "short_title": "WLC",
        "license": "Public Domain",
        "source": {
            "publisher": "Westminster Theological Seminary / tanach.us",
            "url": "https://tanach.us/Tanach.xml",
            "package": "WLC consonantal text — transcribed from Leningrad Codex (B19A, 1008 CE)",
            "source_date": None,  # filled at extract time
        },
        "notes": (
            "Westminster Leningrad Codex — consonantal Hebrew text "
            "of the Tanakh, transcribed from the Leningrad Codex "
            "(B19A, 1008 CE) by Christopher V. Kimball at WLC. "
            "Public Domain. Pairs with `jps` (JPS 1917 English). "
            "The Leningrad Codex is the oldest complete Masoretic "
            "text manuscript and is the base text for nearly every "
            "modern critical Hebrew Bible. τ.5-A ships seed (Gen "
            "1:1-3); τ.5-A.x is user-side full ingest. OT only — "
            "Hebrew canon (39 books / ~23,000 verses)."
        ),
    },
    "lxx-brenton-english": {
        "title": "Septuagint (Brenton 1844, English translation)",
        "short_title": "LXX-Eng",
        "license": "Public Domain",
        "source": {
            "publisher": "Samuel Bagster & Sons (London, 1844)",
            "url": "https://eBible.org/eng-Brenton/",
            "package": "eng-Brenton_vpl.zip",
            "source_date": 1844,
        },
        "notes": (
            "Brenton's 1844 English translation of the Septuagint, "
            "printed alongside the Greek text (which ships as "
            "`lxx-brenton-greek` from γ.5). Both halves are "
            "unambiguously Public Domain — Brenton died 1862; the "
            "1844 edition predates the 1929 PD cutoff in every "
            "jurisdiction. This is the English-side companion "
            "translation called for by SESSION_END_2026-05-12 §4 "
            "N+2. Closes the Greek-translation-content column for "
            "the 8 of 9 editions declaring `greek` in "
            "popup_languages_default (Orthodox primary; useful for "
            "any edition exploring LXX vs MT divergences). τ.4 "
            "ships infrastructure + Gen 1:1-3 seed; τ.4.x is "
            "user-side full ingest. OT only — Septuagint canon "
            "(~30 books / ~25,000 verses)."
        ),
    },
    "vulgate-clementine": {
        "title": "Clementine Vulgate (Latin, 1592)",
        "short_title": "Vulgate",
        "license": "Public Domain",
        "source": {
            "publisher": "Vatican Press (Rome, 1592 Clementine edition)",
            "url": "https://eBible.org/lat-clemvulg/",
            "package": "lat-clemvulg_vpl.zip",
            "source_date": 1592,
        },
        "notes": (
            "Clementine Vulgate — Pope Clement VIII's 1592 "
            "authorized edition of Jerome's 4th-century Latin "
            "translation. Public Domain by age (Jerome died 420 "
            "AD; Clementine edition 1592). Closes the Latin "
            "column called for by the anglican-bcp edition in "
            "popup_languages_default. The Stuttgart Vulgate "
            "(Weber-Gryson, 1969+) is the modern critical "
            "alternative but is NOT public domain; the "
            "Clementine remains the canonical PD Latin Bible. "
            "τ.3 ships Gen 1:1-3 seed; τ.3.x is user-side full "
            "ingest. Both Testaments — full Catholic canon "
            "(~73 books, the Latin Vulgate covers slightly more "
            "than the Hebrew MT)."
        ),
    },
    "geez-tewahedo": {
        "title": "Ge'ez Bible (Classical Ethiopian, Tewahedo tradition)",
        "short_title": "Ge'ez",
        "license": "Public Domain",
        "source": {
            "publisher": "Pell-Platt British and Foreign Bible Society (London, 1830 NT) + classical Tewahedo manuscript tradition",
            "url": "https://eBible.org/gez-Geez/",
            "package": "gez-Geez_vpl.zip",
            "source_date": 1830,
        },
        "notes": (
            "Ge'ez (ግዕዝ) is the Classical Ethiopian liturgical "
            "language — the scriptural and liturgical tongue of "
            "the Ethiopian Orthodox Tewahedo Church (and Eritrean "
            "Orthodox Tewahedo). The Tewahedo Bible has been "
            "preserved in Ge'ez manuscript form since the 4th-6th "
            "centuries CE (the Ge'ez translation pre-dates and "
            "preserves textual readings sometimes lost in other "
            "language traditions — most famously 1 Enoch, which "
            "Tewahedo is the only major Christian communion to "
            "canonize). PD basis: pre-1929 printed Ge'ez Bibles "
            "(Pell-Platt's 1830 BFBS Ge'ez NT, the 1853 BFBS Old "
            "Testament, Dillmann's 1865 Lexicon Linguae "
            "Aethiopicae); all underlying manuscripts are PD by "
            "age (4th-15th century CE). Directly reinforces the "
            "v1.x uniqueness angle (the ethiopian-tewahedo "
            "flagship edition has Ge'ez as its native scriptural "
            "language). τ.6 ships Gen 1:1-3 seed; τ.6.x is "
            "user-side full ingest. Unicode handling: Ethiopic "
            "block U+1200-U+137F covers the main syllabary; "
            "U+1380-U+139F Ethiopic Supplement; U+2D80-U+2DDF "
            "Ethiopic Extended; U+AB00-U+AB2F Ethiopic Extended-A. "
            "The script is read left-to-right (unlike Hebrew + "
            "Arabic). Tewahedo numerals (፩ ፪ ፫ ...) live at "
            "U+1369-U+137C; standard Hindu-Arabic numerals also "
            "acceptable for verse numbering."
        ),
    },
    "arabic-vandyke": {
        "title": "Van Dyck–Boustani Arabic Bible (1865)",
        "short_title": "AVD",
        "license": "Public Domain",
        "source": {
            "publisher": "American Bible Society / Syrian Mission (Beirut, 1865)",
            "url": "https://eBible.org/arb-vandyke/",
            "package": "arb-vandyke_vpl.zip",
            "source_date": 1865,
        },
        "notes": (
            "Van Dyck–Boustani 1865 Arabic Bible — the standard "
            "Arabic Protestant Bible, produced over 16 years by "
            "Eli Smith (d. 1857), Cornelius Van Dyck (d. 1895), "
            "Butrus al-Bustani (d. 1883), Nasif al-Yaziji (d. "
            "1871), and Yusuf al-Asir (d. 1889) — all dead before "
            "the 1929 PD cutoff in every jurisdiction. The 1865 "
            "Beirut edition itself is unambiguously PD by age. "
            "Closes the Arabic column for the coptic-orthodox "
            "edition — the last popup-language gap after τ.5-A + "
            "γ.5 + τ.4 + τ.3 closed Hebrew + Greek + Latin. "
            "τ.10-A ships Gen 1:1-3 seed; τ.10-A.x is user-side "
            "full ingest. Right-to-left rendering handled by "
            "ν.2.7's popup-languages machinery (same as `wlc` "
            "Hebrew). Both Testaments — Protestant 66-book canon "
            "(the Van Dyck does NOT include the deuterocanonical "
            "books; for Coptic Orthodox use a future τ-phase "
            "could add the 19th-century Bagster Catholic Arabic "
            "Bible which has the deuterocanon)."
        ),
    },
    "douay-rheims": {
        "title": "Douay-Rheims Bible (Challoner revision, 1899)",
        "short_title": "DRA",
        "license": "Public Domain",
        "source": {
            "publisher": "John Murphy Company (Baltimore, 1899)",
            "url": "https://eBible.org/eng-DRA/",
            "package": "eng-DRA_vpl.zip",
            "source_date": 1899,
        },
        "notes": (
            "Douay-Rheims-Challoner — English Catholic translation "
            "of the Latin Vulgate. The original Douay-Rheims OT "
            "(1610) + NT (1582) was revised by Bishop Richard "
            "Challoner in three rounds (1749 NT, 1750 OT, 1752 NT). "
            "The 1899 John Murphy edition is the canonical "
            "Challoner-text reprint, Public Domain by age. "
            "Pairs with `vulgate-clementine` (Latin) as the "
            "Catholic-tradition translation pair (the way KJV + "
            "WLC pair for Reformation Protestants, and JPS + WLC "
            "pair for Jewish-tradition readers). Strengthens the "
            "catholic-study + anglican-bcp editions in particular. "
            "Famously archaic phrasings like 'Be light made. And "
            "light was made.' for Genesis 1:3 — a direct calque "
            "of the Vulgate's 'Fiat lux. Et facta est lux.' τ.2 "
            "ships Gen 1:1-3 seed; τ.2.x is user-side full ingest. "
            "Both Testaments — full Catholic canon."
        ),
    },
}


def list_registered() -> list[str]:
    """Return the registered translation ids, in registration order."""
    return list(TRANSLATIONS.keys())


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
        sys.stderr.write(f"  warning: {skipped_malformed} malformed VPL line(s) skipped\n")
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
# Optional versification remap (for sources whose numbering != KJV)
# ----------------------------------------------------------------------

RemapFn = Callable[[str, int, int], tuple[str, int, int] | None]


def apply_remap(
    by_project_book: dict[str, list[tuple[int, int, str]]],
    remap: RemapFn,
) -> dict[str, list[tuple[int, int, str]]]:
    """Remap every verse via ``remap(code, ch, vs) -> (code, ch, vs) | None``,
    regroup by the (possibly new) book code, and CONCATENATE — in source-coordinate
    order — any verses that land on the same canonical coordinate. This mirrors
    ``scripts/extract_lxx_swete.build_verses``: when a source splits one canonical
    verse across two adjacent source verses, the popup shows the WHOLE verse, never a
    truncated half. ``None`` drops a verse (out-of-extent / unmapped); books left
    empty are omitted.

    Only called for the versification-divergent VPL ingests (Arabic tail-merges, JPS
    Masoretic remap, Douay/Vulgate). With no remap (the kjv/web identity sources),
    ``extract`` skips this entirely, so those extractions stay byte-identical."""
    regrouped: dict[str, dict[tuple[int, int], str]] = {}
    for code, verses in by_project_book.items():
        for ch, vs, text in sorted(verses):
            mapped = remap(code, ch, vs)
            if mapped is None:
                continue
            ncode, nch, nvs = mapped
            slot = regrouped.setdefault(ncode, {})
            key = (nch, nvs)
            slot[key] = (slot[key] + " " + text).strip() if key in slot else text
    return {code: sorted((c, v, t) for (c, v), t in d.items()) for code, d in regrouped.items()}


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


def write_book_module(out_path: Path, translation: str, book_code: str, verses: list[tuple[int, int, str]]) -> None:
    """Emit one ``content/translations/<id>/<book>.py`` module.

    The file is regenerable — a header banner notes that hand edits
    will be lost on the next extraction run. Verses are written as a
    flat list of tuples for fastest possible import-time loading.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f'"""Translation: {translation} · Book: {book_code}',
        "",
        "AUTO-GENERATED by scripts/extract_translation.py.",
        "Do not edit by hand — re-run extraction to regenerate.",
        '"""',
        f'TRANSLATION = "{translation}"',
        f'BOOK = "{book_code}"',
        "VERSES = [",
    ]
    # Verses sorted by (chapter, verse) for deterministic output
    for c, v, t in sorted(verses, key=lambda r: (r[0], r[1])):
        lines.append(f"    ({c}, {v}, {_py_repr_text(t)}),")
    lines.append("]")
    lines.append("")
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
        f"id: {info['id']}",
        f"title: {_q(info['title'])}",
        f"short_title: {_q(info['short_title'])}",
        f"license: {_q(info['license'])}",
        "source:",
        f"  publisher: {_q(info['source']['publisher'])}",
        f"  url: {_q(info['source']['url'])}",
        f"  package: {_q(info['source']['package'])}",
        f"  fetched: {info['source']['fetched']}",
        f"  source_date: {info['source']['source_date']}",
        "stats:",
        f"  books: {info['stats']['books']}",
        f"  verses: {info['stats']['verses']}",
        f"  books_outside_kjv: {info['stats']['books_outside_kjv']}",
    ]
    if info.get("notes"):
        lines.extend(["notes: |"] + ["  " + ln for ln in info["notes"].split("\n")])
    meta_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------


def extract(translation_id: str, dry_run: bool = False, report: bool = False, remap: RemapFn | None = None) -> dict:
    """Top-level extraction entry point.

    For ``translation_id`` it expects the source files to be at
    ``content/translations/sources/<id>/`` already (use a separate
    fetcher to download). Returns a stats dict.

    ``remap`` (optional): a ``(code, ch, vs) -> (code, ch, vs) | None`` adapter for
    sources whose own numbering differs from the canonical KJV scheme. When given,
    every verse is remapped to canonical coords and same-coord collisions are
    concatenated (see ``apply_remap``). When omitted, verses are stored at the
    source's own coordinates (identity — kjv/web)."""
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

    # Versification remap (sources whose numbering != KJV); identity-store otherwise.
    if remap is not None:
        by_project_book = apply_remap(by_project_book, remap)

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
        write_book_module(out_dir / f"{proj_code}.py", translation_id, proj_code, verses)

    # Write _meta.yaml — driven by the TRANSLATIONS registry. Falls
    # back to a minimal stub when the translation is not yet
    # registered (allows ad-hoc extraction of new sources before
    # promoting them to a full τ phase).
    write_meta_yaml(
        out_dir / "_meta.yaml",
        meta_for(translation_id, stats),
    )

    return stats


def meta_for(translation_id: str, stats: dict) -> dict:
    """Compose the _meta.yaml dict for ``translation_id``, filling in
    ``stats`` and the live ``fetched`` date. Looks up ``TRANSLATIONS``
    and falls back to a placeholder stub for unregistered ids."""
    today = _dt.date.today().isoformat()
    entry = TRANSLATIONS.get(translation_id)
    if entry is None:
        # Unregistered translation — write a stub so the customize
        # console doesn't error on missing _meta.yaml. Author can
        # promote it to a full TRANSLATIONS entry later.
        return {
            "id": translation_id,
            "title": translation_id.upper(),
            "short_title": translation_id.upper(),
            "license": "Unknown — review before publishing",
            "source": {
                "publisher": "",
                "url": "",
                "package": "",
                "fetched": today,
                "source_date": today,
            },
            "stats": {
                "books": stats["project_books_emitted"],
                "verses": stats["total_verses"],
                "books_outside_kjv": len(PROJECT_BOOKS_OUTSIDE_KJV),
            },
            "notes": (
                f"Ad-hoc extraction; not in TRANSLATIONS registry. "
                f"Add a TRANSLATIONS['{translation_id}'] entry to "
                f"scripts/extract_translation.py before publishing."
            ),
        }
    src = entry["source"]
    return {
        "id": translation_id,
        "title": entry["title"],
        "short_title": entry["short_title"],
        "license": entry["license"],
        "source": {
            "publisher": src.get("publisher", ""),
            "url": src.get("url", ""),
            "package": src.get("package", ""),
            "fetched": today,
            "source_date": src.get("source_date") or today,
        },
        "stats": {
            "books": stats["project_books_emitted"],
            "verses": stats["total_verses"],
            "books_outside_kjv": len(PROJECT_BOOKS_OUTSIDE_KJV),
        },
        "notes": entry.get("notes", ""),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("translation_id", nargs="?", help="translation slug; expects sources/<id>/*_vpl.txt")
    p.add_argument("--dry-run", action="store_true", help="parse and report, but do not write output files")
    p.add_argument("--report", action="store_true", help="print a coverage report after extraction")
    p.add_argument("--list", action="store_true", help="list registered translation ids and exit")
    args = p.parse_args()
    if args.list:
        for tid in list_registered():
            entry = TRANSLATIONS[tid]
            print(f"  {tid:8s} {entry['short_title']:5s} {entry['title']}")
            print(f"  {'':8s} {'':5s} → {entry['source'].get('url', '')}")
            print(f"  {'':8s} {'':5s} fetch: {entry['source'].get('package', '')}")
        return 0
    if not args.translation_id:
        p.error("translation_id is required (or pass --list)")
    stats = extract(args.translation_id, dry_run=args.dry_run, report=args.report)
    if not args.report:
        print(f"{stats['translation']}: {stats['project_books_emitted']} books, {stats['total_verses']:,} verses")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Build torrey_topical.json from the clean CCEL Torrey's New Topical Textbook.

Torrey's New Topical Textbook (R.A. Torrey, 1897, public domain) is a topical
concordance structurally like Nave's Topical Bible — topic heading followed by
scripture-reference sub-entries — so it reuses Nave's CCEL reference-expansion
grammar (``extract_naves_ccel.expand_refs``: same ``;``/``,``/``-`` compression
with book/chapter carry-forward).

It needs its OWN parser, though, because the CCEL text dump of Torrey differs
from Nave's in three ways, each of which (left unhandled) both loses real
references AND fabricates junk topics:

  1. **Title-Case topics, nested sub-labels.** Torrey topics are Title-Case
     ("Access to God"), not Nave's ALL-CAPS, and Torrey nests recurring
     structural sub-labels ("Exemplified", "Should produce") plus unique
     grouping headers ("Implements of") that look like topics but aren't.
     Two complementary filters separate topics from sub-labels:
       * a **section-letter gate** — the dump prints a clean A–Z running header
         on every page, so a no-reference heading whose initial letter differs
         from the current section's letter is a sub-label, not a topic;
       * a **frequency filter** — a recurring no-reference heading (seen
         ``>= _MIN_SUBLABEL_OCCURRENCES`` times) is structural; a real topic
         appears once in the alphabetical index.

  2. **Wrapped reference lines.** A long citation wraps so the book token ends
     one line and the ``chapter:verse`` tail starts the next ("…; Heb" / then
     "12:5-11."). The tail is rejoined to its book; a leftover numeric line
     could never be a topic anyway (topics start with a letter).

  3. **A divergent abbreviation.** Torrey renders Judges as "Jdj" (447x), which
     is absent from Nave's CCEL scheme; it is normalised before expansion.

Coordinate validation (out-of-canonical-extent drop) happens in
``fetch_sources._build_naves_indices``; this module only parses + expands.

Usage:
    python3 scripts/extract_torrey_ccel.py            # rebuild torrey_topical.json
    python3 scripts/extract_torrey_ccel.py --dry-run  # report counts, no write
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.notes_io import atomic_write, ensure_backup  # noqa: E402
from scripts.extract_naves_ccel import expand_refs as _naves_expand_refs  # noqa: E402
from scripts.fetch_sources import _build_naves_indices  # noqa: E402

SOURCE_TXT = REPO_ROOT / "content" / "sources" / "torrey_ccel_source.txt"
OUT_JSON = REPO_ROOT / "content" / "sources" / "torrey_topical.json"
TORREY_SOURCE_LABEL = "Torrey's New Topical Textbook (1897, PD)"

# A no-reference heading seen at least this many times is a recurring structural
# sub-label (Exemplified / Illustrated / Typified / …), never a topic.
_MIN_SUBLABEL_OCCURRENCES = 2

# Torrey-specific abbreviations that differ from Nave's CCEL scheme. "Jdj" is
# Torrey's rendering of Judges; "Jud" maps to Judges in the shared scheme and
# never appears in Torrey (it uses the full "Jude" for Jude), so the rewrite is
# safe.
_TORREY_ABBREV_FIXUPS = ((re.compile(r"\bJdj\b"), "Jud"),)

# CCEL front/back-matter boilerplate markers (matched case-insensitively).
_CCEL_BOILERPLATE_MARKERS = (
    "ccel",
    "christian classics",
    "calvin college",
    "copyrighted",
    "developing countr",
    "@",
    "http",
)

# The running title printed atop every page of the CCEL edition.
_NOISE_EXACT = {"Torrey's New Topical Textbook"}

# A wrapped citation tail: a line that opens with "<chapter>:" or "<verses>,"
# whose book token was left at the end of the previous line.
_WRAP_CONTINUATION = re.compile(r"\d+[:,]")
# A line whose prose/citation wrapped FORWARD: it ends with a dangling em-dash
# (the citation continues next line) or a hyphenated word split across the break.
_FORWARD_WRAP_DASH = re.compile(r"[—–]$")
_FORWARD_WRAP_HYPHEN = re.compile(r"[A-Za-z]-$")
_HEADER = re.compile(r"[A-Z]")  # single-letter A–Z running section header


# The shared CCEL ref-grammar yields LEGACY book codes when a ref uses a full
# book name that falls through to the old TSK alias map (e.g. "Joel" → "jol").
# The notes files use canonical codes (joe/eze/nah/phi/mrk/jhn/jam/psa), so
# normalize — else those notes land nowhere (the ★BUGCLUSTER class; the central
# _normalize_book_code covers only joh/ps/jas, so cover the full set here).
_LEGACY_TO_CANON = {
    "jol": "joe",
    "ezk": "eze",
    "nam": "nah",
    "php": "phi",
    "mar": "mrk",
    "joh": "jhn",
    "jas": "jam",
    "ps": "psa",
}


def expand_refs(line: str) -> list[list]:
    """Nave's CCEL reference expansion + Torrey abbreviation fix-ups + canonical
    book-code normalization."""
    for pattern, replacement in _TORREY_ABBREV_FIXUPS:
        line = pattern.sub(replacement, line)
    return [[_LEGACY_TO_CANON.get(b, b), ch, v] for b, ch, v in _naves_expand_refs(line)]


def _is_header(s: str) -> bool:
    return bool(_HEADER.fullmatch(s))


def _is_page_noise(s: str) -> bool:
    """True for page artifacts to drop — page numbers, roman-numeral front-matter
    markers, the running title, CCEL boilerplate. Single-letter running headers
    are NOT page noise: they drive the section-letter gate."""
    if s in _NOISE_EXACT:
        return True
    if re.fullmatch(r"\d+", s):  # page number
        return True
    if re.fullmatch(r"[ivxlcdm]+", s):  # lowercase roman-numeral page marker
        return True
    low = s.lower()
    return any(marker in low for marker in _CCEL_BOILERPLATE_MARKERS)


def _logical_lines(text: str) -> list[str]:
    """Strip blank/page-noise lines (keeping section headers) and rejoin wrapped
    reference tails to the line that carries their book token. Dropping the
    interleaved page artifacts first makes a continuation adjacent to its book
    even across a page break."""
    out: list[str] = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or _is_page_noise(s):
            continue
        prev = out[-1] if out else None
        if prev is not None and not _is_header(prev):
            if _WRAP_CONTINUATION.match(s):  # backward: "…; Heb" + "12:5-11."
                out[-1] = f"{prev} {s}"
                continue
            if _FORWARD_WRAP_DASH.search(prev):  # forward: "description —" + "Ex 1:1"
                out[-1] = f"{prev} {s}"
                continue
            if _FORWARD_WRAP_HYPHEN.search(prev):  # forward: "destruc-" + "tion …"
                out[-1] = prev[:-1] + s
                continue
        out.append(s)
    return out


def parse_text(text: str) -> dict[str, list]:
    """Parse the CCEL Torrey text into a forward index {topic: [[book,ch,v],...]}.

    A line carrying references is attributed to the current main topic. A
    no-reference heading becomes a new main topic only if it starts with a
    letter, is not a recurring structural sub-label, and (once a section is
    known from the running header) starts with the current section's letter.
    Topics that end up with zero in-range references are dropped.
    """
    lines = _logical_lines(text)

    freq: Counter = Counter()
    for s in lines:
        if not _is_header(s) and s[:1].isalpha() and not expand_refs(s):
            freq[s] += 1
    sublabels = {s for s, n in freq.items() if n >= _MIN_SUBLABEL_OCCURRENCES}

    forward: dict[str, list] = {}
    section: str | None = None
    current: str | None = None
    prev_was_header = False
    for s in lines:
        if _is_header(s):
            # A running section header is preceded by content; the front-matter
            # Contents A–Z list is a run of consecutive header lines. Honor only
            # the first of a run, so the Contents collapses to "A" (aligned with
            # the body's section A) instead of leaving section stuck at "Z".
            if not prev_was_header:
                section = s
            prev_was_header = True
            continue
        prev_was_header = False
        refs = expand_refs(s)
        if refs:
            if current is not None:
                forward[current].extend(refs)
            continue
        # No-reference heading candidate.
        if not s[:1].isalpha():
            continue  # leftover wrapped-citation fragment, never a topic
        if s in sublabels:
            continue  # recurring structural sub-label
        if section is not None and s[0].upper() != section:
            continue  # wrong-section grouping header
        current = s
        forward.setdefault(current, [])
    return {topic: refs for topic, refs in forward.items() if refs}


def build(dry_run: bool = False) -> dict:
    text = SOURCE_TXT.read_text(encoding="utf-8")
    forward = parse_text(text)
    idx = _build_naves_indices(forward, source=TORREY_SOURCE_LABEL)
    print(f"topics={idx['_meta']['n_topics']:,}  refs={idx['_meta']['n_refs']:,}")
    if not dry_run:
        if OUT_JSON.is_file():
            ensure_backup(OUT_JSON)
        atomic_write(OUT_JSON, json.dumps(idx, ensure_ascii=False, indent=2) + "\n")
        print(f"wrote {OUT_JSON.relative_to(REPO_ROOT)}")
    return idx


def main() -> int:
    p = argparse.ArgumentParser(description="Rebuild torrey_topical.json from the clean CCEL Torrey text.")
    p.add_argument("--dry-run", action="store_true", help="report counts, do not write")
    args = p.parse_args()
    if not SOURCE_TXT.is_file():
        print(f"missing source: {SOURCE_TXT.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 2
    build(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

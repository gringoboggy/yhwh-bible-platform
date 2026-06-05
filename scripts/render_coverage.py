#!/usr/bin/env python3
"""Render-coverage inventory (audit 2026-05-20 — broadened from
Samuel/Kings to whole-project).

Reports which books of the canonical 87-book Tewahedo set are rendered
under each ``content/translations/<edition>/`` directory and which are
pending — sorted by source track so the project can see at a glance:

- **manuscript-collation track** (τ.6.x.4.b/c): 1sa, 2sa, 1ki, 2ki
  rendered post-marathon; today they show up as ``marathon_pending``
  with a calibration_count showing partial progress.
- **Patrologia Orientalis track** (PO 2/9/13/23 PDFs): 1ch, 2ch, ezr,
  neh, job rendered from printed bilingual Ge'ez+French critical
  editions. Ingest complete (τ.6.x.5.x): the per-book ``.py`` stores
  exist under ``content/translations/geez-tewahedo/`` so ``_list_rendered``
  returns them and the inventory shows them as **rendered**. (The
  separate Phase-D *own-versification* re-ingest of these books — the
  roadmap's D1b-batch — is a distinct lane and is still pending.)
- **Parallel-PDF EOTC track** (τ.6.x.2 / τ.7.x): the bulk of OT +
  Apocrypha — already substantially rendered (geez 16 books, amharic
  24 books as of 2026-05-20).
- **KJV skeleton**: complete reference; missing implies a book the
  Tewahedo canon has but the protestant KJV doesn't (e.g. mq1-3,
  jub, 1en, paz, etc.).

Intended to compose into ``api_preflight`` via the standard
``run_all()`` shape (rules §9) — ``run_all()`` already returns that
shape, but the preflight wiring is not yet implemented (no check in
``scripts/api/preflight.py`` calls it today; this tool is CLI-only).

CLI:

    py scripts/render_coverage.py            # JSON report
    py scripts/render_coverage.py --pretty   # human-readable summary
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Canonical Tewahedo 87-book set, sourced from content/books.yaml. The
# protestant subset is 66 books; LXX/Catholic add deuterocanonical;
# Tewahedo additionally includes 1 Enoch, Jubilees, Meqabyan, etc.
# This is the SUPERSET — every edition is a filter on this list.
#
# NOTE: This list is intentionally STATIC — books.yaml is the runtime
# source of truth; this static copy survives if books.yaml is missing
# or being edited mid-run. The lint check ``render_coverage_no_regression``
# (lint_rules.py) pins that this list does not shrink.
# Some editions use legacy 2-letter codes; map to canonical 3-letter.
_BOOK_ALIASES = {"ex": "exo", "1k": "1ki", "2k": "2ki"}

# Order + codes mirror content/books.yaml (the runtime source of truth)
# exactly — all 87 codes in canonical sequence.
_CANONICAL_BOOKS = [
    # Pentateuch
    "gen",
    "exo",
    "lev",
    "num",
    "deu",
    # Historical
    "jos",
    "jdg",
    "rut",
    "1sa",
    "2sa",
    "1ki",
    "2ki",
    "1ch",
    "2ch",
    "man",  # The Prayer of Manasses
    # Tewahedo distinctives (interleaved per books.yaml order)
    "jub",
    "1en",
    "2en",  # Slavonic Enoch / Secrets of Enoch
    "ezr",
    "neh",
    "1es",  # First Esdras / Ezra Kali
    "2es",
    "tob",
    "jdt",
    "est",
    "aes",  # Additions to Esther (Greek Septuagint)
    "mq1",
    "mq2",
    "mq3",
    # Wisdom + Poetry
    "job",
    "psa",
    "pro",
    "wis",
    "ecc",
    "sng",
    "sir",
    # Major + Minor Prophets
    "isa",
    "jer",
    "lam",
    "bar",
    "lje",  # The Letter of Jeremiah
    "4ba",
    "eze",
    "dan",
    "paz",
    "sus",  # The History of Susanna
    "bel",
    "hos",
    "joe",
    "amo",
    "oba",
    "jon",
    "mic",
    "nah",
    "hab",
    "zep",
    "hag",
    "zec",
    "mal",
    # New Testament
    "mat",
    "mrk",  # mint-7 ★BUGCLUSTER: was "mar" (legacy) — canonical Mark is "mrk"
    "luk",
    "jhn",
    "act",
    "rom",
    "1co",
    "2co",
    "gal",
    "eph",
    "phi",
    "col",
    "1th",
    "2th",
    "1ti",
    "2ti",
    "tit",
    "phm",
    "heb",
    "jam",
    "1pe",
    "2pe",
    "1jn",
    "2jn",
    "3jn",
    "jud",
    "rev",
    "1cl",  # First Epistle of Clement to the Corinthians
]

# Books with manuscript-collation track (τ.6.x.4.b/c) — render is
# post-marathon, currently in flight.
_MANUSCRIPT_TRACK_BOOKS = {"1sa", "2sa", "1ki", "2ki"}

# Books with Patrologia Orientalis source PDFs (under GAPS/3..6/*.pdf).
# Render COMPLETE (τ.6.x.5.x) — printed bilingual Ge'ez+French critical
# edition; the per-book stores exist so these appear as rendered. (The
# Phase-D own-versification re-ingest of the same books is a separate lane.)
_PATROLOGIA_TRACK_BOOKS = {"1ch", "2ch", "ezr", "neh", "job"}


def _list_rendered(edition_dir: Path) -> set[str]:
    """Return the set of book codes that have a .py file in this edition.

    Applies ``_BOOK_ALIASES`` so legacy 2-letter filenames (`ex.py`) map
    to canonical 3-letter codes (`exo`)."""
    if not edition_dir.is_dir():
        return set()
    out: set[str] = set()
    for p in edition_dir.glob("*.py"):
        if p.stem.startswith("_"):
            continue
        out.add(_BOOK_ALIASES.get(p.stem, p.stem))
    return out


def _calibration_count(book: str) -> int:
    """Count calibrated chapters for a manuscript-track book."""
    # Read the per-track manifest if present
    for track in ("samuel", "kings"):
        manifest = REPO / "content" / "manuscript" / track / "manifest.yaml"
        if not manifest.is_file():
            continue
        try:
            import yaml

            data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
            if book in data:
                return sum(
                    1
                    for ch_data in data[book].values()
                    if isinstance(ch_data, dict) and ch_data.get("status") == "calibrated"
                )
        except Exception:
            continue
    return 0


def _per_edition_report(edition_dir_name: str) -> dict:
    """Per-edition coverage: rendered, marathon_pending, patrologia_pending, missing."""
    edition_dir = REPO / "content" / "translations" / edition_dir_name
    rendered = _list_rendered(edition_dir)

    marathon_pending: list[str] = []
    patrologia_pending: list[str] = []
    missing: list[str] = []
    for book in _CANONICAL_BOOKS:
        if book in rendered:
            continue
        if book in _MANUSCRIPT_TRACK_BOOKS:
            marathon_pending.append(book)
        elif book in _PATROLOGIA_TRACK_BOOKS:
            patrologia_pending.append(book)
        else:
            missing.append(book)

    return {
        "edition": edition_dir_name,
        "rendered_count": len(rendered & set(_CANONICAL_BOOKS)),
        "rendered_books": sorted(rendered & set(_CANONICAL_BOOKS)),
        "marathon_pending": marathon_pending,
        "patrologia_pending": patrologia_pending,
        "missing": missing,
        "manuscript_calibration_counts": {book: _calibration_count(book) for book in marathon_pending}
        if marathon_pending
        else {},
    }


def run_all() -> dict:
    """Run the inventory across every translation edition.

    Returns the standard §9 meta-tool shape (``summary`` + per-edition
    blocks) so api_preflight + lint_rules composers can fold it in.
    """
    editions = {}
    for ed_name in (
        "kjv",
        "geez-tewahedo",
        "amharic-tewahedo",
        # EN back-translation stores feeding the two standalone Bibles
        # (RULES §1 north-star). Enumerated here so the inventory surfaces
        # their render progress too.
        "geez-tewahedo-en",
        "amharic-tewahedo-en",
    ):
        editions[ed_name] = _per_edition_report(ed_name)

    summary = {
        "canonical_books": len(_CANONICAL_BOOKS),
        "geez_tewahedo_rendered": editions["geez-tewahedo"]["rendered_count"],
        "amharic_tewahedo_rendered": editions["amharic-tewahedo"]["rendered_count"],
        "geez_tewahedo_pending": (
            len(editions["geez-tewahedo"]["marathon_pending"])
            + len(editions["geez-tewahedo"]["patrologia_pending"])
            + len(editions["geez-tewahedo"]["missing"])
        ),
        "manuscript_track_chapters_calibrated": sum(
            editions["geez-tewahedo"]["manuscript_calibration_counts"].values()
        ),
        "patrologia_track_books_pdf_available": len(_PATROLOGIA_TRACK_BOOKS),
        "geez_tewahedo_en_rendered": editions["geez-tewahedo-en"]["rendered_count"],
        "amharic_tewahedo_en_rendered": editions["amharic-tewahedo-en"]["rendered_count"],
    }

    return {"summary": summary, "editions": editions}


def _pretty(rep: dict) -> str:
    """Human-readable summary."""
    lines = []
    s = rep["summary"]
    lines.append(f"Canonical books: {s['canonical_books']}")
    lines.append(f"geez-tewahedo:   {s['geez_tewahedo_rendered']}/{s['canonical_books']} rendered")
    lines.append(f"amharic-tewahedo: {s['amharic_tewahedo_rendered']}/{s['canonical_books']} rendered")
    lines.append(
        f"geez-tewahedo-en (back-translation): {s['geez_tewahedo_en_rendered']}/{s['canonical_books']} rendered"
    )
    lines.append(
        f"amharic-tewahedo-en (back-translation): {s['amharic_tewahedo_en_rendered']}/{s['canonical_books']} rendered"
    )
    lines.append(
        f"geez-tewahedo-en (back-translation): {s['geez_tewahedo_en_rendered']}/{s['canonical_books']} rendered"
    )
    lines.append(
        f"amharic-tewahedo-en (back-translation): {s['amharic_tewahedo_en_rendered']}/{s['canonical_books']} rendered"
    )
    lines.append(
        f"manuscript track: {s['manuscript_track_chapters_calibrated']} chapters calibrated (4 books in flight)"
    )
    lines.append(
        f"patrologia track: {s['patrologia_track_books_pdf_available']} books with PDFs ready (ingest pending)"
    )
    lines.append("")

    ge = rep["editions"]["geez-tewahedo"]
    lines.append(f"=== geez-tewahedo ({ge['rendered_count']} rendered) ===")
    lines.append(f"  Rendered: {', '.join(ge['rendered_books'])}")
    if ge["marathon_pending"]:
        cal = ge["manuscript_calibration_counts"]
        m = ", ".join(f"{b}({cal[b]}ch)" for b in ge["marathon_pending"])
        lines.append(f"  Marathon-pending: {m}")
    if ge["patrologia_pending"]:
        lines.append(f"  Patrologia-pending: {', '.join(ge['patrologia_pending'])}")
    if ge["missing"]:
        lines.append(
            f"  Other missing ({len(ge['missing'])}): {', '.join(ge['missing'][:10])}"
            + ("…" if len(ge["missing"]) > 10 else "")
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--pretty", action="store_true", help="human-readable summary")
    p.add_argument("--json", action="store_true", help="raw JSON")
    args = p.parse_args(argv)

    rep = run_all()
    if args.pretty:
        print(_pretty(rep))
    else:
        print(json.dumps(rep, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

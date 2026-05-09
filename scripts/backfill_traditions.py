#!/usr/bin/env python3
"""backfill_traditions.py — Audit + rewrite the corpus to stamp the
ψ.8 tradition field on note tuples that resolve to a non-default
tradition.

Why this is mostly an audit today
---------------------------------
The current 15,925-note corpus is sourced from PD reference works
(TSK xrefs, Strong's Hebrew, Strong's Greek, Nave's Topical) plus a
handful of hand-authored seeds. ALL of those resolve to the
denominationally-neutral ``cross`` tradition under the
``note_tradition()`` derivation rules. So the backfill **has nothing
to rewrite right now**: the resolver already returns the correct
tradition for every existing note, and per CLAUDE_PROJECT_RULES §7.2
"no-op when the field is unset", we don't write the explicit field
where the derived value is already ``cross`` (would produce a noisy
diff with no behavioral change).

When future χ.2-χ.5 commentary phases ship tradition-tagged content
(Henry → protestant; Calvin → protestant; Catena Aurea → orthodox;
Rashi → jewish), THIS script becomes the migration tool: re-run it
after the new notes land and it will stamp explicit tradition values
on each one whose derived tradition differs from ``cross``.

Idempotency
-----------
Re-running this script never produces a different result for
unchanged input — the resolver is a pure function and the rewrite
condition (``target != cross AND explicit != target``) is stable.

Usage
-----
::

    python3 scripts/backfill_traditions.py            # dry-run audit
    python3 scripts/backfill_traditions.py --apply    # write changes

Exit codes
----------
``0``  audit clean (or apply succeeded). ``1``  apply would have
written but ``--apply`` not given (CI-friendly drift detection).
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.core.traditions import (  # noqa: E402
    DEFAULT_TRADITION,
    TRADITION_IDS,
    note_tradition,
    valid_tradition,
)
from scripts.core.notes_io import load_notes  # noqa: E402

NOTES_DIR = REPO_ROOT / "content" / "notes"

GREEN = "\033[92m"
YELLOW = "\033[93m"
DIM = "\033[2m"
RESET = "\033[0m"


def _explicit_tradition(tup: tuple) -> str | None:
    """Return the explicit tradition field on a note tuple (10th
    position), or ``None`` if absent / invalid."""
    if not isinstance(tup, tuple) or len(tup) < 10:
        return None
    val = tup[9]
    return val if valid_tradition(val) else None


def audit_book(book_code: str) -> dict:
    """Audit every note in one book; never mutates disk.

    Returns a stats dict with:
        n_total          — notes scanned
        n_default        — derived = cross (no rewrite needed)
        n_explicit_match — explicit field present and matches derived
        n_would_rewrite  — derived ≠ cross AND explicit ≠ derived
        by_tradition     — Counter of derived tradition values
    """
    path = NOTES_DIR / f"{book_code}.py"
    if not path.is_file():
        return {"book": book_code, "missing": True, "n_total": 0,
                "n_default": 0, "n_explicit_match": 0,
                "n_would_rewrite": 0, "by_tradition": Counter()}

    notes = load_notes(path) or []
    by_tradition: Counter = Counter()
    n_default = 0
    n_explicit_match = 0
    n_would_rewrite = 0
    for tup in notes:
        if not isinstance(tup, tuple) or len(tup) < 8:
            continue
        derived = note_tradition(tup)
        by_tradition[derived] += 1
        explicit = _explicit_tradition(tup)
        if derived == DEFAULT_TRADITION and explicit is None:
            n_default += 1
        elif explicit == derived:
            n_explicit_match += 1
        elif derived != DEFAULT_TRADITION:
            # The note resolves to a non-default tradition, but the
            # explicit field is missing (or stale) — this is the case
            # the rewrite path handles.
            n_would_rewrite += 1
        else:
            # derived = cross, explicit = something else. Today this
            # can't happen (cross is the default fallthrough), but
            # we count it defensively.
            n_default += 1

    return {
        "book": book_code,
        "missing": False,
        "n_total": len(notes),
        "n_default": n_default,
        "n_explicit_match": n_explicit_match,
        "n_would_rewrite": n_would_rewrite,
        "by_tradition": by_tradition,
    }


def discover_books() -> list[str]:
    """Sorted list of all book codes that have a notes module."""
    return sorted(
        p.stem for p in NOTES_DIR.glob("*.py")
        if p.stem != "__init__" and not p.stem.startswith("_")
    )


def run_audit(books: Iterable[str]) -> dict:
    """Audit every book in *books*. Returns aggregated stats."""
    by_book: list[dict] = []
    totals = Counter()
    n_total = 0
    n_default = 0
    n_explicit_match = 0
    n_would_rewrite = 0
    for code in books:
        stats = audit_book(code)
        by_book.append(stats)
        if stats["missing"]:
            continue
        n_total += stats["n_total"]
        n_default += stats["n_default"]
        n_explicit_match += stats["n_explicit_match"]
        n_would_rewrite += stats["n_would_rewrite"]
        totals.update(stats["by_tradition"])
    return {
        "by_book": by_book,
        "n_total": n_total,
        "n_default": n_default,
        "n_explicit_match": n_explicit_match,
        "n_would_rewrite": n_would_rewrite,
        "by_tradition": totals,
    }


def _print_audit(report: dict) -> None:
    """Print a compact human-readable audit summary."""
    print(f"\n{DIM}─── ψ.8 tradition backfill audit ───{RESET}\n")
    print(f"  notes scanned:           {report['n_total']:6d}")
    print(f"  default-resolving:       {report['n_default']:6d} "
          f"{DIM}(no rewrite needed){RESET}")
    print(f"  explicit field matches:  {report['n_explicit_match']:6d} "
          f"{DIM}(already stamped, idempotent){RESET}")
    print(f"  would rewrite:           {report['n_would_rewrite']:6d} "
          f"{DIM}(derived ≠ cross AND not yet stamped){RESET}")
    print()
    print(f"  by tradition:")
    for tid in sorted(report["by_tradition"]):
        n = report["by_tradition"][tid]
        marker = GREEN if tid != DEFAULT_TRADITION else DIM
        print(f"    {marker}{tid:14s}{RESET} {n:6d}")
    print()


def main() -> int:
    p = argparse.ArgumentParser(
        description="Audit + (optionally) backfill the ψ.8 tradition "
                     "field on every note in content/notes/.",
    )
    p.add_argument("--apply", action="store_true",
                    help="rewrite notes whose derived tradition differs "
                         "from the explicit field. Default is dry-run.")
    p.add_argument("--books",
                    help="comma-separated subset of book codes to audit "
                         "(default: every book in content/notes/)")
    args = p.parse_args()

    books = (args.books.split(",") if args.books else discover_books())

    report = run_audit(books)
    _print_audit(report)

    if report["n_would_rewrite"] == 0:
        print(f"  {GREEN}✓{RESET} no rewrites needed — every note "
              f"already resolves correctly.")
        return 0

    if not args.apply:
        print(f"  {YELLOW}!{RESET} {report['n_would_rewrite']} note(s) "
              f"would be rewritten — re-run with --apply to commit.")
        return 1

    # Rewrite path. Reaching here means at least one note has a
    # non-default derived tradition that isn't yet stamped explicitly.
    # That can happen once χ.2-χ.5 (commentary ingestors) ship — the
    # derived tradition will then come from the attribution string of
    # tagged commentaries (e.g. "Henry's Commentary, Matthew Henry
    # (1714). PD." → protestant). The actual file-rewrite pass is
    # deferred to ψ.8.0.1 — it requires an AST-aware writer that
    # preserves the surrounding NOTES module's comments and ordering,
    # mirroring scripts/attribute.py. ψ.8.0 ships the schema +
    # resolver + audit; the writer lands once there's actual content
    # to migrate.
    print(f"  {YELLOW}!{RESET} --apply is reserved for ψ.8.0.1 "
          f"(AST-aware rewriter); see CHANGELOG ψ.8.0 entry for "
          f"context. Audit-only ship.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

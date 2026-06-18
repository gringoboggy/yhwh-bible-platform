#!/usr/bin/env python3
"""Surgically remove orphaned note markers + asides from epub_working/.

Removes:
  - any note whose kind was dropped from the project (REMOVED_KINDS), and
  - optionally, baked ids absent from the live corpus for edited Strategy-A
    books (those with ``id_prefix`` in books.yaml).

Never touches Strategy-B ``bxx``-scoped ids (no ``id_prefix``) or verse popups.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.core import config, notes_io  # noqa: E402

REMOVED_KINDS = frozenset(
    {
        "comm-rabbinic",
        "compare-quran",
        "compare-nag-hammadi",
        "liturgy-torah-portion",
    }
)

# Books whose source corpus changed in the Christian-scope scrub arc.
SYNC_BOOK_CODES = frozenset(
    {
        "gen",
        "exo",
        "lev",
        "num",
        "deu",
        "jos",
        "rut",
        "1sa",
        "2sa",
        "1ki",
        "2ki",
        "1en",
        "ezr",
    }
)

MARKER_RE = re.compile(
    r'<a class="note-ref note-(?P<kind>[a-z0-9-]+)" id="ref-(?P<fid>[^"]+)"[^>]*>.*?</a>',
    re.DOTALL,
)
ASIDE_OPEN_RE = re.compile(
    r'<aside class="note note-(?P<kind>[a-z0-9-]+)" id="note-(?P<fid>[^"]+)"[^>]*>',
)


def _prefix_entries() -> tuple[list[str], dict[str, str]]:
    """Longest-first id_prefix list + prefix → book code."""
    pairs: list[tuple[str, str]] = []
    for code, book in config.books_by_code().items():
        prefix = book.get("id_prefix")
        if prefix:
            pairs.append((prefix, code))
    pairs.sort(key=lambda x: len(x[0]), reverse=True)
    return [p for p, _ in pairs], {p: c for p, c in pairs}


def load_valid_ids(sync_codes: frozenset[str]) -> dict[str, set[str]]:
    valid_by_prefix: dict[str, set[str]] = {}
    for code, book in config.books_by_code().items():
        if code not in sync_codes:
            continue
        prefix = book.get("id_prefix")
        if not prefix:
            continue
        notes_path = REPO / "content" / "notes" / f"{code}.py"
        if not notes_path.is_file():
            continue
        loaded = notes_io.load_notes_checked(notes_path, book=code)
        if isinstance(loaded, dict):
            continue
        bucket = valid_by_prefix.setdefault(prefix, set())
        for ch, v, suffix, *_ in loaded:
            bucket.add(f"{prefix}{ch:02d}{v:02d}{suffix or ''}")
    return valid_by_prefix


def fid_prefix(fid: str, prefixes: list[str]) -> str | None:
    for p in prefixes:
        if fid.startswith(p):
            return p
    return None


def should_remove(
    *,
    kind: str,
    fid: str,
    prefixes: list[str],
    sync_prefixes: frozenset[str],
    valid_by_prefix: dict[str, set[str]],
) -> bool:
    if kind in REMOVED_KINDS:
        return True
    pfx = fid_prefix(fid, prefixes)
    if not pfx or pfx not in sync_prefixes:
        return False
    return fid not in valid_by_prefix.get(pfx, set())


def _remove_balanced_aside(text: str, start: int) -> tuple[str, bool]:
    depth = 0
    pos = start
    while pos < len(text):
        no = text.find("<aside", pos)
        nc = text.find("</aside>", pos)
        if nc == -1:
            return text, False
        if no != -1 and no < nc:
            depth += 1
            pos = no + len("<aside")
        else:
            depth -= 1
            if depth == 0:
                end = nc + len("</aside>")
                return text[:start] + text[end:], True
            pos = nc + len("</aside>")
    return text, False


def prune_text(
    text: str,
    *,
    prefixes: list[str],
    sync_prefixes: frozenset[str],
    valid_by_prefix: dict[str, set[str]],
) -> tuple[str, dict[str, int]]:
    remove_ids: set[str] = set()
    for m in ASIDE_OPEN_RE.finditer(text):
        if should_remove(
            kind=m.group("kind"),
            fid=m.group("fid"),
            prefixes=prefixes,
            sync_prefixes=sync_prefixes,
            valid_by_prefix=valid_by_prefix,
        ):
            remove_ids.add(m.group("fid"))
    for m in MARKER_RE.finditer(text):
        if should_remove(
            kind=m.group("kind"),
            fid=m.group("fid"),
            prefixes=prefixes,
            sync_prefixes=sync_prefixes,
            valid_by_prefix=valid_by_prefix,
        ):
            remove_ids.add(m.group("fid"))

    stats = {"markers": 0, "asides": 0, "ids": len(remove_ids)}
    if not remove_ids:
        return text, stats

    for m in sorted(MARKER_RE.finditer(text), key=lambda x: x.start(), reverse=True):
        if m.group("fid") in remove_ids:
            text = text[: m.start()] + text[m.end() :]
            stats["markers"] += 1

    for m in sorted(ASIDE_OPEN_RE.finditer(text), key=lambda x: x.start(), reverse=True):
        if m.group("fid") in remove_ids:
            text, ok = _remove_balanced_aside(text, m.start())
            if ok:
                stats["asides"] += 1

    return text, stats


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--kinds-only",
        action="store_true",
        help="Only strip REMOVED_KINDS (skip corpus orphan sync).",
    )
    args = p.parse_args()

    prefixes, prefix_to_code = _prefix_entries()
    sync_codes = frozenset() if args.kinds_only else SYNC_BOOK_CODES
    sync_prefixes = frozenset(p for p in prefixes if prefix_to_code[p] in sync_codes)
    valid_by_prefix = load_valid_ids(sync_codes) if sync_codes else {}

    work = REPO / "epub_working"
    totals = {"files": 0, "markers": 0, "asides": 0, "ids": 0}

    for path in sorted(work.glob("index_split_*.html")):
        text = path.read_text(encoding="utf-8")
        new_text, stats = prune_text(
            text,
            prefixes=prefixes,
            sync_prefixes=sync_prefixes,
            valid_by_prefix=valid_by_prefix,
        )
        if stats["ids"]:
            totals["files"] += 1
            totals["markers"] += stats["markers"]
            totals["asides"] += stats["asides"]
            totals["ids"] += stats["ids"]
            print(f"{path.name}: remove {stats['ids']} ids ({stats['markers']} markers, {stats['asides']} asides)")
            if not args.dry_run:
                path.write_text(new_text, encoding="utf-8")

    print(
        f"{'DRY-RUN ' if args.dry_run else ''}done: "
        f"{totals['files']} files, {totals['ids']} ids, "
        f"{totals['markers']} markers, {totals['asides']} asides"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

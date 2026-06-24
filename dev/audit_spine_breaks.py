#!/usr/bin/env python3
"""Spine-break auditor — finds spurious page breaks in a built EPUB/KEPUB.

THE PROBLEM THIS CATCHES (and why earlier structural audits missed it for weeks):
On a Kobo e-ink kepub (and every EPUB renderer to some degree) **each spine file
starts on a new page**. CSS page-break rules are ignored at the depth kepubify
nests content, so the ONLY thing that forces a page break is a spine-file boundary.
The build's file-split packer (`apply_file_split`) slices each book into ~400 KB
pieces and, for a heavily-noted chapter, cuts BETWEEN VERSES — so a reader gets a
half-empty page in the middle of a chapter. The defect is invisible to a
per-file HTML audit: no single file is malformed; the bug is in WHERE one file
ends and the next begins. You only see it by reconstructing the spine→verse map.

THE EXPECTED MODEL (per the user, 2026-06-23): a book is
    [title page] -> ch1 header -> ch1 verses -> ch2 header -> ... -> last chapter
flowing continuously; the ONLY forced new page is a book's title page. So:
    * a spine boundary at a BOOK start   = intended      (severity OK)
    * a spine boundary at a CHAPTER start = mid-book break (severity WARN — policy)
    * a spine boundary MID-CHAPTER        = always a BUG   (severity ERROR)

USAGE:
    py -3 dev/audit_spine_breaks.py <built.epub | built.kepub.epub | dir> [...]
    py -3 dev/audit_spine_breaks.py --max-chapter-breaks 0 <epub>   # also fail WARNs

Exit code 1 if any ERROR (mid-chapter) break is found, or if chapter-boundary
breaks exceed --max-chapter-breaks (default: unlimited → chapter breaks are WARN).
Edition/canon-agnostic: it reads the verse anchors the build emits, so it works on
every canonical Bible and every platform artifact.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from dataclasses import dataclass, field

# The build's emitted anchors (build_edition.py): every verse carries a
# `v-{book}-{chapter}-{verse}` id; a book title page is `class="book-title-page"`.
_VERSE_RE = re.compile(r'id="v-([a-z0-9]+)-(\d+)-(\d+)"')
_BOOKPAGE_RE = re.compile(r'class="book-title-page"|class="bookpage-title"')
_ITEM_RE = re.compile(r'<item\s+[^>]*\bid="([^"]+)"[^>]*\bhref="([^"]+)"')
_ITEMREF_RE = re.compile(r'<itemref\s+[^>]*\bidref="([^"]+)"')
_OPF_CANDIDATES = ("content.opf", "OEBPS/content.opf", "EPUB/content.opf")


@dataclass
class Piece:
    """One spine file's identity for boundary classification."""

    name: str
    is_bookpage: bool
    first: tuple[str, int, int] | None  # (book, chapter, verse) of the first verse
    last: tuple[str, int, int] | None  # ... of the last verse


@dataclass
class Report:
    edition: str
    pieces: int = 0
    backmatter: int = 0
    book_breaks: int = 0
    chapter_breaks: list[tuple[str, str, str]] = field(default_factory=list)
    midchapter_breaks: list[tuple[str, str, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.midchapter_breaks


def _read_opf(zf: zipfile.ZipFile) -> str | None:
    names = set(zf.namelist())
    for cand in _OPF_CANDIDATES:
        if cand in names:
            return zf.read(cand).decode("utf-8", "replace")
    # fall back: any *.opf in the archive
    for n in names:
        if n.endswith(".opf"):
            return zf.read(n).decode("utf-8", "replace")
    return None


def _spine_pieces(zf: zipfile.ZipFile) -> list[Piece]:
    opf = _read_opf(zf)
    if opf is None:
        raise ValueError("no .opf found in archive")
    manifest = dict(_ITEM_RE.findall(opf))
    # hrefs in the OPF are relative to the OPF's own folder
    opf_name = next((c for c in _OPF_CANDIDATES if c in set(zf.namelist())), None)
    base = (opf_name.rsplit("/", 1)[0] + "/") if opf_name and "/" in opf_name else ""
    names = set(zf.namelist())
    pieces: list[Piece] = []
    for idref in _ITEMREF_RE.findall(opf):
        href = manifest.get(idref, "")
        if not href.endswith((".html", ".xhtml")):
            continue
        path = base + href
        if path not in names:
            path = href if href in names else path
        try:
            txt = zf.read(path).decode("utf-8", "replace")
        except KeyError:
            continue
        verses = [(b, int(c), int(v)) for b, c, v in _VERSE_RE.findall(txt)]
        pieces.append(
            Piece(
                name=href,
                is_bookpage=bool(_BOOKPAGE_RE.search(txt)),
                first=verses[0] if verses else None,
                last=verses[-1] if verses else None,
            )
        )
    return pieces


def audit_epub(path: str) -> Report:
    """Classify every spine boundary in one built EPUB/KEPUB."""
    rep = Report(edition=path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1])
    with zipfile.ZipFile(path) as zf:
        pieces = _spine_pieces(zf)
    prev_last: tuple[str, int, int] | None = None
    for pc in pieces:
        # backmatter glossary pieces (index_split_900*) are a separate section,
        # not part of the scripture flow — count but don't classify as a break.
        if "index_split_900" in pc.name or "_900" in pc.name:
            rep.backmatter += 1
            prev_last = None
            continue
        if pc.first is None:
            # a pure title-page / front-matter piece — the next content starts a book
            if prev_last is not None:
                rep.book_breaks += 1
            prev_last = None
            continue
        rep.pieces += 1
        if prev_last is not None:
            pb, pc_, pv = prev_last
            nb, nc, nv = pc.first
            a = f"{pb} {pc_}:{pv}"
            b = f"{nb} {nc}:{nv}"
            if nb != pb:
                rep.book_breaks += 1
            elif nc == pc_:
                rep.midchapter_breaks.append((pc.name, a, b))
            else:
                rep.chapter_breaks.append((pc.name, a, b))
        prev_last = pc.last
    return rep


def _print(rep: Report, max_chapter_breaks: int | None) -> bool:
    mc, cb = len(rep.midchapter_breaks), len(rep.chapter_breaks)
    print(f"\n=== {rep.edition} ===")
    print(f"  scripture spine pieces: {rep.pieces}  backmatter pieces: {rep.backmatter}")
    print(f"  OK    book-title breaks (intended)      : {rep.book_breaks}")
    print(f"  WARN  chapter-boundary breaks (mid-book) : {cb}")
    print(f"  ERROR mid-chapter breaks (between verses): {mc}")
    for name, a, b in rep.midchapter_breaks:
        print(f"        ERROR mid-chapter: {a:>14s} -> {b:<14s} ({name})")
    failed = mc > 0
    if max_chapter_breaks is not None and cb > max_chapter_breaks:
        print(f"  -> chapter breaks {cb} exceed --max-chapter-breaks {max_chapter_breaks}")
        failed = True
    print(f"  RESULT: {'FAIL' if failed else 'PASS'}")
    return failed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Find spurious page breaks (spine boundaries) in a built EPUB/KEPUB.")
    ap.add_argument("paths", nargs="+", help="built .epub / .kepub.epub files")
    ap.add_argument(
        "--max-chapter-breaks",
        type=int,
        default=None,
        help="fail if chapter-boundary (mid-book) breaks exceed this; omit to treat them as WARN only",
    )
    args = ap.parse_args(argv)
    any_fail = False
    for p in args.paths:
        try:
            rep = audit_epub(p)
        except (zipfile.BadZipFile, ValueError) as e:
            print(f"\n=== {p} ===\n  SKIP: {e}")
            any_fail = True
            continue
        any_fail |= _print(rep, args.max_chapter_breaks)
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""check_nested_anchors.py — JVM-free nested-<a> gate + one-time repair.

An ``<a>`` nested inside another ``<a>`` is invalid XHTML and is the sole
cause of the EPUB epubcheck RSC-005 errors in this corpus. The recovered
base (v28a-50 snapshot) shipped 746 such verses across 8 files where a
``note-ref`` word-study marker sits INSIDE the ``vn-link`` verse-number
anchor:

    <a class="vn-link" …><a class="note-ref …">…<sup>⌘</sup></a><span class="vn">6</span></a>

The repair relocates the note-ref to a sibling immediately *before* the
vn-link — preserving the exact rendered glyph order (⌘ then 6) and every
other byte — so the vn-link wraps only its span:

    <a class="note-ref …">…<sup>⌘</sup></a><a class="vn-link" …><span class="vn">6</span></a>

Detection uses an open-tag stack (robust against attribute order / whitespace);
repair uses a raw-byte regex substitution (moves an open tag without
reformatting, so it cannot perturb other bytes). The two cross-check each
other: after a regex repair the parser must report zero nesting.

Usage:
    check_nested_anchors.py [paths…]     # gate: exit 1 if any nesting (default: epub_working/*.html)
    check_nested_anchors.py --fix [paths…]  # one-time in-place repair (backup + atomic write)
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

EPUB_DIR = REPO / "epub_working"


class _AnchorNesting(HTMLParser):
    """Collects every ``<a>`` opened while another ``<a>`` is still open."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._open: list[dict] = []
        self.nested: list[tuple[dict, dict]] = []  # (inner_attrs, outer_attrs)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            d = dict(attrs)
            if self._open:
                self.nested.append((d, self._open[-1]))
            self._open.append(d)

    def handle_endtag(self, tag):
        if tag == "a" and self._open:
            self._open.pop()


def find_nested_anchors(html: str) -> list[tuple[dict, dict]]:
    """Return ``[(inner_attrs, outer_attrs), …]`` for each nested ``<a>``."""
    p = _AnchorNesting()
    p.feed(html)
    return p.nested


# A vn-link open tag, then one-or-more *complete* note-ref anchor elements,
# then the verse-number span, then the vn-link close. ``note-ref`` content is
# only ``<sup>…</sup>`` so ``.*?</a>`` never over-runs. A correct wrapper (span
# immediately after the open) has no note-ref here and so never matches.
_BROKEN_RE = re.compile(
    r'(<a class="vn-link"[^>]*>)'  # 1: vn-link open tag
    r'((?:<a class="note-ref[^>]*>.*?</a>)+)'  # 2: leading note-ref element(s)
    r'(<span class="vn">\d+</span>)'  # 3: the verse-number span
    r"</a>",  # vn-link close
    re.DOTALL,
)


def repair_html(html: str) -> tuple[str, int]:
    """Relocate note-ref markers out of vn-link wrappers. Byte-exact: only
    moves the vn-link open tag past the leading note-ref(s). Returns
    ``(new_html, num_wrappers_fixed)``; idempotent on already-correct HTML."""
    count = 0

    def _repl(m: re.Match) -> str:
        nonlocal count
        count += 1
        return m.group(2) + m.group(1) + m.group(3) + "</a>"

    return _BROKEN_RE.sub(_repl, html), count


def _default_files() -> list[Path]:
    return sorted(EPUB_DIR.glob("*.html"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Detect/repair nested <a> (epubcheck RSC-005) in base HTML.")
    ap.add_argument("--fix", action="store_true", help="relocate note-refs out of vn-link wrappers in place")
    ap.add_argument("paths", nargs="*", type=Path, help="files to scan (default: epub_working/*.html)")
    args = ap.parse_args(argv)
    files = args.paths or _default_files()

    if args.fix:
        from scripts.core import notes_io  # lazy: keep the gate path dependency-light

        total = 0
        changed: list[str] = []
        for f in files:
            new, n = repair_html(f.read_text(encoding="utf-8"))
            if n:
                notes_io.ensure_backup(f)
                notes_io.atomic_write(f, new)
                changed.append(f"{f.name}:{n}")
                total += n
        print(f"fixed {total} nested <a> across {len(changed)} file(s): {', '.join(changed) or 'none'}")
        return 0

    total = 0
    offenders: list[str] = []
    for f in files:
        n = len(find_nested_anchors(f.read_text(encoding="utf-8")))
        if n:
            offenders.append(f"{f.name}:{n}")
            total += n
    if total:
        for o in offenders:
            print(f"  {o}")
        print(f"FAIL: {total} nested <a> in {len(offenders)} file(s) — invalid XHTML (epubcheck RSC-005)")
        return 1
    print(f"OK: 0 nested <a> across {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

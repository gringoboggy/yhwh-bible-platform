#!/usr/bin/env python3
"""resync_marker_glyphs.py — bring the note-marker glyphs already rendered in the
base HTML (epub_working/) into agreement with inject.glyph_for.

Historically inject.glyph_for was a hardcoded 5-symbol prefix map that defaulted
unmatched kinds to ◇, so kinds like topic-nave (✦), hist-* (⌂), dist-* (❖), and
the other category symbols rendered as ◇. Now that glyph_for is data-driven
(reads the kind's symbol from kinds.yaml), this pass rewrites the already-injected
glyphs in place — both the inline marker ``<sup class="marker-{kind}">`` and the
note-back link inside each ``<aside class="note note-{kind}">`` — to match.

Re-runnable + idempotent. Run as a module so scripts.* imports resolve:
    python -m scripts.resync_marker_glyphs --dry-run
    python -m scripts.resync_marker_glyphs
"""

from __future__ import annotations

import argparse
import re

from scripts.core import notes_io
from scripts.inject import EPUB_DIR, glyph_for, html_title_for

# Inline marker: <sup class="marker-{kind}">{glyph}</sup> — kind is in the class.
_MARKER_RE = re.compile(r'(<sup class="marker-)([a-z0-9-]+)(">)(.*?)(</sup>)', re.DOTALL)
# Aside declaration maps a note id -> its kind: <aside class="note note-{kind}" id="note-{id}".
_ASIDE_KIND_RE = re.compile(r'<aside class="note note-([a-z0-9-]+)" id="note-([^"]+)"')
# Note-back link: <a href="#ref-{id}" class="note-back" title="Back">{glyph}</a>.
# Keyed on the id (not surrounding structure) so it is robust to layout variation.
_NOTEBACK_RE = re.compile(r'(<a href="#ref-)([^"]+)(" class="note-back" title="Back">)(.*?)(</a>)', re.DOTALL)


def resync_glyphs(text: str) -> tuple[str, int]:
    """Rewrite every inline marker glyph and note-back glyph in ``text`` to the
    current ``glyph_for(kind)``. Returns ``(new_text, n_changed)``. Idempotent:
    glyphs already correct are left byte-identical."""
    changed = 0

    def _fix_marker(m: re.Match) -> str:
        nonlocal changed
        correct = glyph_for(m.group(2))
        if m.group(4) != correct:
            changed += 1
        return f"{m.group(1)}{m.group(2)}{m.group(3)}{correct}{m.group(5)}"

    text = _MARKER_RE.sub(_fix_marker, text)

    # Map each note id -> kind from the aside declarations, then rewrite each
    # note-back link by its id (decoupled from the aside's internal layout).
    id_to_kind = {nid: kind for kind, nid in _ASIDE_KIND_RE.findall(text)}

    def _fix_back(m: re.Match) -> str:
        nonlocal changed
        kind = id_to_kind.get(m.group(2))
        if kind is None:
            return m.group(0)
        correct = glyph_for(kind)
        if m.group(4) != correct:
            changed += 1
        return f"{m.group(1)}{m.group(2)}{m.group(3)}{correct}{m.group(5)}"

    text = _NOTEBACK_RE.sub(_fix_back, text)
    return text, changed


# Marker open tag: <a class="note-ref note-{kind}" ... title="{tooltip}"><sup...
_MARKER_TITLE_RE = re.compile(r'(<a class="note-ref note-)([a-z0-9-]+)("[^>]*\stitle=")([^"]*)(">)')


def resync_titles(text: str) -> tuple[str, int]:
    """Rewrite the ``title="…"`` tooltip on every note-ref marker in ``text`` to
    the current ``html_title_for(kind)`` (kind read from the marker's class).
    Returns ``(new_text, n_changed)``. Idempotent."""
    changed = 0

    def _fix(m: re.Match) -> str:
        nonlocal changed
        correct = html_title_for(m.group(2))
        if m.group(4) != correct:
            changed += 1
        return f"{m.group(1)}{m.group(2)}{m.group(3)}{correct}{m.group(5)}"

    return _MARKER_TITLE_RE.sub(_fix, text), changed


def resync_file(path, *, dry_run: bool) -> int:
    text = path.read_text(encoding="utf-8")
    new_text, n_glyph = resync_glyphs(text)
    new_text, n_title = resync_titles(new_text)
    n = n_glyph + n_title
    if n and not dry_run:
        notes_io.ensure_backup(path)
        notes_io.atomic_write(path, new_text)
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description="Resync note-marker glyphs in epub_working/ to glyph_for.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    total = 0
    for f in sorted(EPUB_DIR.glob("index_split_*.html")):
        n = resync_file(f, dry_run=args.dry_run)
        if n:
            print(f"  {f.name}: {n} glyph(s)")
            total += n
    print(f"TOTAL glyphs resynced: {total}{' (dry-run)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

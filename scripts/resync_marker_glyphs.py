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
        # Wave-3 numbered markers (class marker-num) hold a footnote number, not
        # a category glyph — leave them alone (glyph_for("num") would be the ◇
        # default and would overwrite the number).
        if m.group(2) == "num":
            return m.group(0)
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
        # Wave-3 back-links are a fixed ↩ (the category symbol moved into a
        # sibling note-sym); never revert ↩ to the kind glyph.
        if m.group(4) == "↩":
            return m.group(0)
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


# ----------------------------------------------------------------------
# Wave-3 re-bake: marker_style=numbers + symbols-into-notes (spec §4.1/§4.4/§12.4)
#
# A DISTINCT, one-time transform from the glyph/title resync above. ``inject.py``
# runs base-wide, so the markers already baked carry the OLD presentation (inline
# category glyph in the <sup>; the category glyph reused as the aside back-link —
# the stray ‖). These functions rewrite the base in place to:
#   marker:  <sup class="marker-{kind}">{glyph}</sup> → <sup class="marker-num">{N}</sup>
#            (N = per-chapter sequential footnote number; inline glyph dropped → no tofu)
#   aside :  ...title="Back">{glyph}</a> → ...title="Back">↩</a>
#              <a class="note-sym" href="legend.xhtml#legend-{cat}" title="{label}">{glyph}</a>
#            (fixed ↩ back-link; the category symbol moves INTO the note as a
#            clickable link to its "A Guide to the Notes" legend row)
# ----------------------------------------------------------------------

# A chapter-heading anchor — the numbering reset boundary. Only ``id="ch-…"``
# headings match; an aside cross-ref href ("…#ch-b73-c1") does NOT (it lacks the
# ``id="`` prefix), so a mid-chapter cross-reference can never restart the count.
_CH_ANCHOR_RE = re.compile(r'id="ch-b\d+-c\d+"')

# A full inline marker. The <a> head (through its closing '>'), the kind, and the
# <sup> glyph are captured; only the <sup> is rewritten so every attribute on the
# anchor (id / href / epub:type / title / note-{kind}) survives byte-for-byte.
_NUM_MARKER_RE = re.compile(
    r'(?P<head><a class="note-ref note-(?P<kind>[^"]+)" id="ref-(?P<id>[^"]+)"[^>]*>)'
    r'<sup class="marker-[^"]*">(?P<glyph>[^<]*)</sup>'
    r"(?P<tail></a>)"
)

# An aside's back-link (the first child of the note body). The negative lookahead
# keeps the rewrite idempotent: once a ``note-sym`` has been appended the back-link
# is skipped on subsequent runs.
_ASIDE_BACK_RE = re.compile(
    r'(?P<pre><aside class="note note-(?P<kind>[^"]+)" id="note-(?P<id>[^"]+)" '
    r'epub:type="footnote">\s*<(?:p|div)>'
    r'<a href="#ref-(?P=id)" class="note-back" title="Back">)'
    r"(?P<glyph>[^<]*)"
    r'(?P<post></a>)(?! <a class="note-sym")'
)


def renumber_markers(text: str) -> tuple[str, int]:
    """Replace each inline marker's category ``<sup>`` glyph with a sequential
    footnote number, resetting the counter at every chapter heading. Returns
    ``(new_text, markers_renumbered)``. Idempotent (numbers are stable)."""
    chapter_pos = [m.start() for m in _CH_ANCHOR_RE.finditer(text)]
    n_ch = len(chapter_pos)
    out: list[str] = []
    last = 0
    counter = 0
    ch_idx = 0
    count = 0
    for m in _NUM_MARKER_RE.finditer(text):
        while ch_idx < n_ch and chapter_pos[ch_idx] <= m.start():
            counter = 0  # crossed into a new chapter
            ch_idx += 1
        counter += 1
        count += 1
        out.append(text[last : m.start()])
        out.append(f'{m.group("head")}<sup class="marker-num">{counter}</sup>{m.group("tail")}')
        last = m.end()
    out.append(text[last:])
    return "".join(out), count


def rewrite_asides(text: str, *, kind_to_cat: dict, cat_label: dict) -> tuple[str, int]:
    """Rewrite each aside's back-link to a fixed ↩ and move the category symbol
    into the note as a clickable ``legend.xhtml#legend-{cat}`` link. Returns
    ``(new_text, asides_rewritten)``. Idempotent (the note-sym lookahead guards
    a second pass)."""
    count = 0

    def _sub(m: re.Match) -> str:
        nonlocal count
        count += 1
        kind = m.group("kind")
        cat = kind_to_cat.get(kind, "?")
        glyph = m.group("glyph")
        label = cat_label.get(cat, cat)
        return (
            m.group("pre")
            + "↩"
            + m.group("post")
            + f' <a class="note-sym" href="legend.xhtml#legend-{cat}" title="{label}">{glyph}</a>'
        )

    return _ASIDE_BACK_RE.sub(_sub, text), count


def resync_html(text: str, *, kind_to_cat: dict, cat_label: dict) -> tuple[str, dict]:
    """Apply both Wave-3 transforms (renumber markers, then rewrite asides)."""
    text, m = renumber_markers(text)
    text, a = rewrite_asides(text, kind_to_cat=kind_to_cat, cat_label=cat_label)
    return text, {"markers": m, "asides": a}


def default_kind_to_cat() -> dict:
    """kind code → category id, from kinds.yaml (production default)."""
    from scripts.core import config

    return {k["code"]: k.get("category", "?") for k in config.load_kinds()}


def default_cat_label() -> dict:
    """category id → human label, from categories.yaml (production default)."""
    from scripts.core import config

    return {c["id"]: c["label"] for c in config.load_categories()}


def _rebake_numbers_main(*, write: bool) -> int:
    """One-time Wave-3 re-bake across the base, self-verified per file."""
    from scripts.categorize_diff import prove_marker_rebake

    kind_to_cat = default_kind_to_cat()
    cat_label = default_cat_label()
    tot_m = tot_a = changed = 0
    for f in sorted(EPUB_DIR.glob("index_split_*.html")):
        before = f.read_text(encoding="utf-8")
        after, stats = resync_html(before, kind_to_cat=kind_to_cat, cat_label=cat_label)
        if after == before:
            continue
        report = prove_marker_rebake(before, after)
        if not report["ok"]:
            print(f"REFUSED {f.name}: {report['reason']}")
            return 1
        tot_m += stats["markers"]
        tot_a += stats["asides"]
        changed += 1
        print(f"  {f.name}: {stats['markers']} markers, {stats['asides']} asides")
        if write:
            notes_io.ensure_backup(f)
            notes_io.atomic_write(f, after)
    mode = "WROTE" if write else "DRY RUN"
    print(f"{mode}: {changed} files, {tot_m} markers renumbered, {tot_a} asides rewritten")
    if not write and changed:
        print("re-run with --rebake-numbers --write to apply.")
    return 0


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
    ap.add_argument(
        "--rebake-numbers",
        action="store_true",
        help="Wave-3 one-time: renumber markers + move category symbols into notes (distinct from glyph resync)",
    )
    ap.add_argument("--write", action="store_true", help="with --rebake-numbers: actually write (default is a dry run)")
    args = ap.parse_args()
    if args.rebake_numbers:
        return _rebake_numbers_main(write=args.write)
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

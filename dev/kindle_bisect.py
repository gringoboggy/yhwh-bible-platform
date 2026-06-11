#!/usr/bin/env python3
"""Kindle STK failure bisect ladder — one-variable probe artifacts.

Round-2 STK failure (~46 min, rung-1 UNHIDE already in-build) killed the
hidden-text hypothesis; the live suspect is the ~112k-link anchor/popup
graph (ranked cause #2 in notes/2026-06-11-kindle-stk-failure-forensics.md).
Each rung rewrites the STAGED artifact's zip — never a rebuild — so exactly
one variable changes versus the file the user uploaded.

Rung 2 DELINK: the four note-graph anchor classes (vn-link,
verse-notes-badge, vnote-back, note-back) become spans and asides become
divs. Text is byte-constant, ids stay, all other links (note-sym, nav,
ch-anchor, plain) are untouched. Output is a DIAGNOSTIC probe — popups are
intentionally dead. If STK passes it, the link graph chokes the converter
and we sub-bisect; if it fails, fall through to rung 3 HALF-SPINE.

    .venv/bin/python dev/kindle_bisect.py --rung delink \\
        --src ~/Desktop/Ethiopian_Bible_..._kindle-safe_<stamp>.epub
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

# The note-graph anchor classes (census 2026-06-11 on the round-2 artifact:
# 33,969 + 9,047 noterefs and 33,969 + 9,047 back-links = 86,032 of 112,760
# total <a>; the surviving ~26.7k are note-sym/nav/ch-anchor/plain links).
_NOTE_GRAPH_CLASSES = frozenset({"vn-link", "verse-notes-badge", "vnote-back", "note-back"})

_A_TAG_RE = re.compile(r"<a\b[^>]*>.*?</a>", re.S)
_CLASS_RE = re.compile(r'class="([^"]*)"')
_HREF_ATTR_RE = re.compile(r'\s+href="[^"]*"')
_EPUB_TYPE_ATTR_RE = re.compile(r'\s+epub:type="[^"]*"')
_ASIDE_OPEN_RE = re.compile(r"<aside\b([^>]*)>")


def _is_note_graph_anchor(open_tag: str) -> bool:
    m = _CLASS_RE.search(open_tag)
    if not m:
        return False
    return bool(_NOTE_GRAPH_CLASSES & set(m.group(1).split()))


def _delink_anchor(match: re.Match[str]) -> str:
    whole = match.group(0)
    open_end = whole.index(">") + 1
    open_tag, rest = whole[:open_end], whole[open_end:]
    if not _is_note_graph_anchor(open_tag):
        return whole
    span_open = _HREF_ATTR_RE.sub("", open_tag)
    span_open = _EPUB_TYPE_ATTR_RE.sub("", span_open)
    span_open = "<span" + span_open[len("<a") :]
    assert rest.endswith("</a>")
    return span_open + rest[: -len("</a>")] + "</span>"


def _aside_to_div(match: re.Match[str]) -> str:
    attrs = _EPUB_TYPE_ATTR_RE.sub("", match.group(1))
    return f"<div{attrs}>"


def delink_html(text: str) -> str:
    """Rung-2 transform: note-graph anchors -> spans, asides -> divs.

    Stripped text is byte-constant; ids survive; every anchor whose class is
    outside the note graph is returned untouched.
    """
    text = _A_TAG_RE.sub(_delink_anchor, text)
    text = _ASIDE_OPEN_RE.sub(_aside_to_div, text)
    text = text.replace("</aside>", "</div>")
    return text


_STRIP_TAGS_RE = re.compile(r"<[^>]+>")


def build_delink(src_epub: Path, out_epub: Path) -> dict[str, int]:
    """Zip-rewrite src_epub with delink_html over every content document.

    Hard-fails (AssertionError) if any piece's stripped text changes or any
    note-graph markup survives — the probe's invariants run on every build.
    """
    stats = {"pieces": 0, "links_before": 0, "links_after": 0, "asides_before": 0}
    with zipfile.ZipFile(src_epub) as zin, zipfile.ZipFile(out_epub, "w", zipfile.ZIP_DEFLATED) as zout:
        names = zin.namelist()
        assert names[0] == "mimetype", "mimetype must be the first zip entry"
        for name in names:
            data = zin.read(name)
            if name == "mimetype":
                zout.writestr(zipfile.ZipInfo("mimetype"), data, zipfile.ZIP_STORED)
                continue
            if name.endswith((".html", ".xhtml")):
                text = data.decode("utf-8")
                out = delink_html(text)
                assert _STRIP_TAGS_RE.sub("", out) == _STRIP_TAGS_RE.sub("", text), f"stripped text changed in {name}"
                assert 'epub:type="noteref"' not in out, name
                assert "<aside" not in out, name
                stats["pieces"] += 1
                stats["links_before"] += len(re.findall(r"<a\b", text))
                stats["links_after"] += len(re.findall(r"<a\b", out))
                stats["asides_before"] += len(re.findall(r"<aside\b", text))
                data = out.encode("utf-8")
            zout.writestr(name, data)
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rung", choices=["delink"], required=True)
    ap.add_argument("--src", required=True, help="staged kindle-safe epub")
    ap.add_argument("--out", help="output path (default: src + rung tag)")
    args = ap.parse_args()

    src = Path(args.src).expanduser()
    if not src.is_file():
        print(f"missing src: {src}", file=sys.stderr)
        return 1
    out = Path(args.out).expanduser() if args.out else src.with_name(src.stem + f"_rung2-{args.rung}" + src.suffix)
    stats = build_delink(src, out)
    print(f"{out}")
    print(
        f"pieces={stats['pieces']} links {stats['links_before']:,} -> "
        f"{stats['links_after']:,} | asides converted: "
        f"{stats['asides_before']:,}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

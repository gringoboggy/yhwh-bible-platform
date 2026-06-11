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

Rung TOCHUSK (2026-06-11, the local-oracle finding): Kindle Previewer 3
reproduced the STK failure locally in ~15 min and NAMED it — E24010
"Hyperlink not resolved in toc" on bp-45/46/47 → E24001 "TOC could not be
built". Those anchors live in EMPTY HUSK title pages (Prayer of Azariah /
Susanna / Bel & the Dragon — the Daniel additions): the canon-splice moved
their text into Daniel but left a standalone appendix-section title frame
(~750 bytes, no art, no verses) that the KFX preprocessor refuses to keep
as a TOC target. Same canon-splice-residue class as the orphan-vnote
asides. This rung removes each husk piece + its manifest/spine/nav/ncx
entries, one-variable; the converter verdict on the probe proves/refutes
the husk as THE failure cause.

    .venv/bin/python dev/kindle_bisect.py --rung delink|tochusk \\
        --src ~/Desktop/Ethiopian_Bible_..._kindle-safe_<stamp>.epub
"""

from __future__ import annotations

import argparse
import itertools
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


# ── rung TOCHUSK ────────────────────────────────────────────────────────

_BODY_RE = re.compile(r"<body[^>]*>(.*?)</body>", re.S)


def is_husk_doc(text: str) -> bool:
    """True iff a content doc is a canon-splice HUSK: an appendix-section
    title frame with NO art and NO verse content (the body the splice left
    behind). The healthy tiny title pieces differ on class (book-title-page)
    and carry their bookpage-art illustration — they must NOT match."""
    m = _BODY_RE.search(text)
    if not m:
        return False
    body = m.group(1)
    if "<img" in body or 'id="v-' in body or 'class="verse"' in body:
        return False
    if 'class="appendix-section"' not in body or 'class="book-title-frame"' not in body:
        return False
    return len(_STRIP_TAGS_RE.sub("", body).strip()) < 300


def _strip_husk_refs(name: str, text: str, base: str, stats: dict[str, int]) -> str:
    """Remove every OPF/ncx/nav reference to one husk file from one document."""
    b = re.escape(base)
    if name.endswith(".opf"):
        item_m = re.search(rf'[ \t]*<item\b[^>]*href="(?:[^"]*/)?{b}"[^>]*/>\s*\n?', text)
        if not item_m:
            return text
        idref_m = re.search(r'id="([^"]+)"', item_m.group(0))
        text = text.replace(item_m.group(0), "")
        stats["opf_items_removed"] += 1
        if idref_m:
            text = re.sub(rf'[ \t]*<itemref\b[^>]*idref="{re.escape(idref_m.group(1))}"[^>]*/>\s*\n?', "", text)
        return text
    if name.endswith(".ncx"):
        # tempered: never scan across a navPoint boundary (a bare .*? swallowed
        # every navPoint from the navMap top down to the husk's — epubcheck
        # "first playOrder value is not 1" caught it on the real artifact).
        # Fragment OPTIONAL: back-matter navPoints (Sources/Colophon…) carry
        # a bare file src — the halfspine rung must drop those whole too.
        text, n_ncx = re.subn(
            rf"[ \t]*<navPoint\b[^>]*>(?:(?!</?navPoint).)*?"
            rf'<content src="(?:[^"]*/)?{b}(?:#[^"]*)?"\s*/>(?:(?!</?navPoint).)*?</navPoint>\s*\n?',
            "",
            text,
            flags=re.S,
        )
        stats["ncx_points_removed"] += n_ncx
        return text
    # nav.xhtml <li> entries AND the in-book HTML TOC page's whole
    # <li class="toc-book"> blocks (label + chapter rows): drop the smallest
    # <li>…</li> that references the husk. Fragment OPTIONAL ([#"]): the
    # back-matter lis (Sources & Acknowledgments / Reference Tables / Topical
    # Index / Colophon) href the bare file — leaving them to the anchor→span
    # neutralizer mints `<li><span>` = invalid nav markup (li needs a, or
    # span + nested ol; epubcheck RSC-005 ×4 on the real half-first probe).
    text, n_nav = re.subn(
        rf'[ \t]*<li[^>]*>(?:(?!</li>).)*?href="(?:[^"]*/)?{b}[#"](?:(?!</li>).)*?</li>\s*\n?',
        "",
        text,
        flags=re.S,
    )
    stats["nav_entries_removed"] += n_nav
    return text


def build_tochusk(src_epub: Path, out_epub: Path) -> dict[str, int]:
    """Zip-rewrite src_epub dropping every husk piece + its OPF manifest item,
    spine itemref, nav.xhtml <li>, and toc.ncx <navPoint>.

    Hard-fails if any reference to a removed husk survives anywhere, or if a
    kept content doc changed by even one byte (only opf/nav/ncx may change).
    """
    stats = {"husks_removed": 0, "opf_items_removed": 0, "nav_entries_removed": 0, "ncx_points_removed": 0}
    with zipfile.ZipFile(src_epub) as zin:
        names = zin.namelist()
        assert names[0] == "mimetype", "mimetype must be the first zip entry"
        raw = {name: zin.read(name) for name in names}

    husks = [n for n in names if n.endswith((".html", ".xhtml")) and is_husk_doc(raw[n].decode("utf-8"))]
    stats["husks_removed"] = len(husks)
    husk_bases = [h.rsplit("/", 1)[-1] for h in husks]

    rewritten: dict[str, bytes] = {}
    for name in names:
        if name in husks or not name.endswith((".opf", ".ncx", ".xhtml", ".html")):
            continue
        text = raw[name].decode("utf-8")
        orig = text
        for base in husk_bases:
            text = _strip_husk_refs(name, text, base, stats)
        if text != orig:
            if name.endswith(".ncx"):
                counter = itertools.count(1)
                text = re.sub(r'playOrder="\d+"', lambda m, c=counter: f'playOrder="{next(c)}"', text)
            rewritten[name] = text.encode("utf-8")

    with zipfile.ZipFile(out_epub, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in names:
            if name in husks:
                continue
            data = rewritten.get(name, raw[name])
            if name == "mimetype":
                zout.writestr(zipfile.ZipInfo("mimetype"), data, zipfile.ZIP_STORED)
                continue
            if name not in rewritten:
                assert data == raw[name]  # kept docs byte-identical
            for base in husk_bases:
                assert base.encode("utf-8") not in data, f"{name} still references removed husk {base}"
            zout.writestr(name, data)
    return stats


# ── rung 3 HALF-SPINE ───────────────────────────────────────────────────
# Blocker #2 (the generic no-E-code internal error) survived BOTH tochusk and
# the chained delink-on-tochusk probe — the TOC husks and the note graph are
# each exonerated, so the remaining trigger is localized by binary content
# search: keep a contiguous spine range, drop the rest, strip every
# opf/nav/ncx/guide entry for the dropped docs, neutralize leftover
# cross-file links INTO dropped docs (anchor → span, the delink transform's
# targeted cousin), retarget any unstrippable ncx <content src> to the first
# kept doc, and renumber playOrder. The probe must stay epubcheck-error-free
# so the Previewer verdict reflects content, not validity.

_OPF_ITEM_RE = re.compile(r"<item\b[^>]*/>")
_OPF_ITEMREF_RE = re.compile(r"<itemref\b[^>]*/>")


def _spine_doc_bases(opf_text: str) -> list[str]:
    """The spine's content-doc href basenames, in spine order."""
    items: dict[str, str] = {}
    for m in _OPF_ITEM_RE.finditer(opf_text):
        tag = m.group(0)
        idm = re.search(r'\bid="([^"]+)"', tag)
        hm = re.search(r'\bhref="([^"]+)"', tag)
        if idm and hm and "nav" not in (re.search(r'properties="([^"]*)"', tag) or [None, ""])[1]:
            items[idm.group(1)] = hm.group(1).rsplit("/", 1)[-1]
    out: list[str] = []
    for m in _OPF_ITEMREF_RE.finditer(opf_text):
        idm = re.search(r'\bidref="([^"]+)"', m.group(0))
        if idm and idm.group(1) in items:
            out.append(items[idm.group(1)])
    return out


def _parse_keep(keep: str, n: int) -> tuple[int, int]:
    if keep == "first":
        return 0, (n + 1) // 2
    if keep == "second":
        return (n + 1) // 2, n
    lo_s, hi_s = keep.split(":", 1)
    lo, hi = int(lo_s), int(hi_s)
    assert 0 <= lo < hi <= n, f"--keep {keep} out of range for a {n}-doc spine"
    return lo, hi


def build_halfspine(src_epub: Path, out_epub: Path, keep: str = "first") -> dict[str, int]:
    """Zip-rewrite src_epub keeping only the ``keep`` slice of the spine
    ("first" | "second" | "lo:hi" doc indices). Non-spine entries (css,
    fonts, images, nav doc, ncx, opf) always survive.

    Hard-fails if any kept entry still references a dropped doc."""
    stats = {
        "docs_kept": 0,
        "docs_dropped": 0,
        "opf_items_removed": 0,
        "nav_entries_removed": 0,
        "ncx_points_removed": 0,
        "links_neutralized": 0,
        "ncx_retargeted": 0,
    }
    with zipfile.ZipFile(src_epub) as zin:
        names = zin.namelist()
        assert names[0] == "mimetype", "mimetype must be the first zip entry"
        raw = {name: zin.read(name) for name in names}

    opf_name = next(n for n in names if n.endswith(".opf"))
    spine = _spine_doc_bases(raw[opf_name].decode("utf-8"))
    lo, hi = _parse_keep(keep, len(spine))
    kept_bases = set(spine[lo:hi])
    dropped_bases = [b for b in spine if b not in kept_bases]
    assert kept_bases and dropped_bases, "halfspine needs a non-trivial split"
    stats["docs_kept"], stats["docs_dropped"] = len(kept_bases), len(dropped_bases)
    dropped_names = {n for n in names if n.rsplit("/", 1)[-1] in dropped_bases}
    first_kept = spine[lo]

    dropped_set = set(dropped_bases)

    def _neutralize_anchor(match: re.Match[str]) -> str:
        whole = match.group(0)
        open_end = whole.index(">") + 1
        open_tag, rest = whole[:open_end], whole[open_end:]
        hm = re.search(r'href="([^"#]*)(?:#[^"]*)?"', open_tag)
        if not hm or hm.group(1).rsplit("/", 1)[-1] not in dropped_set:
            return whole
        stats["links_neutralized"] += 1
        span_open = _HREF_ATTR_RE.sub("", open_tag)
        span_open = _EPUB_TYPE_ATTR_RE.sub("", span_open)
        span_open = "<span" + span_open[len("<a") :]
        return span_open + rest[: -len("</a>")] + "</span>"

    rewritten: dict[str, bytes] = {}
    for name in names:
        if name in dropped_names or not name.endswith((".opf", ".ncx", ".xhtml", ".html")):
            continue
        text = raw[name].decode("utf-8")
        orig = text
        for base in dropped_bases:
            text = _strip_husk_refs(name, text, base, stats)
        if name.endswith(".opf"):
            # guide <reference> entries into dropped docs
            for base in dropped_bases:
                text = re.sub(rf'[ \t]*<reference\b[^>]*href="(?:[^"]*/)?{re.escape(base)}[#"][^>]*/>\s*\n?', "", text)
        elif name.endswith(".ncx"):
            # an unstrippable leftover (e.g. a parent navPoint with nested
            # children) — retarget at the first kept doc so the ncx stays valid
            for base in dropped_bases:
                text, n_re = re.subn(
                    rf'(<content src=")(?:[^"]*/)?{re.escape(base)}(?:#[^"]*)?(")', rf"\g<1>{first_kept}\g<2>", text
                )
                stats["ncx_retargeted"] += n_re
        else:
            text = _A_TAG_RE.sub(_neutralize_anchor, text)
        if text != orig:
            if name.endswith(".ncx"):
                counter = itertools.count(1)
                text = re.sub(r'playOrder="\d+"', lambda m, c=counter: f'playOrder="{next(c)}"', text)
            rewritten[name] = text.encode("utf-8")

    with zipfile.ZipFile(out_epub, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in names:
            if name in dropped_names:
                continue
            data = rewritten.get(name, raw[name])
            if name == "mimetype":
                zout.writestr(zipfile.ZipInfo("mimetype"), data, zipfile.ZIP_STORED)
                continue
            if name.endswith((".opf", ".ncx", ".xhtml", ".html")):
                for base in dropped_bases:
                    assert base.encode("utf-8") not in data, f"{name} still references dropped {base}"
            zout.writestr(name, data)
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rung", choices=["delink", "tochusk", "halfspine"], required=True)
    ap.add_argument("--src", required=True, help="staged kindle-safe epub")
    ap.add_argument("--out", help="output path (default: src + rung tag)")
    ap.add_argument("--keep", default="first", help='halfspine slice: "first" | "second" | "lo:hi" (spine doc indices)')
    args = ap.parse_args()

    src = Path(args.src).expanduser()
    if not src.is_file():
        print(f"missing src: {src}", file=sys.stderr)
        return 1
    tag = {
        "delink": "_rung2-delink",
        "tochusk": "_rung-tochusk",
        "halfspine": f"_rung3-half-{args.keep.replace(':', '-')}",
    }[args.rung]
    out = Path(args.out).expanduser() if args.out else src.with_name(src.stem + tag + src.suffix)
    if args.rung == "delink":
        stats = build_delink(src, out)
        print(f"{out}")
        print(
            f"pieces={stats['pieces']} links {stats['links_before']:,} -> "
            f"{stats['links_after']:,} | asides converted: "
            f"{stats['asides_before']:,}"
        )
    elif args.rung == "tochusk":
        stats = build_tochusk(src, out)
        print(f"{out}")
        print(
            f"husks removed: {stats['husks_removed']} | opf items: "
            f"{stats['opf_items_removed']} | nav entries: "
            f"{stats['nav_entries_removed']} | ncx points: {stats['ncx_points_removed']}"
        )
    else:
        stats = build_halfspine(src, out, keep=args.keep)
        print(f"{out}")
        print(
            f"docs kept {stats['docs_kept']} / dropped {stats['docs_dropped']} | "
            f"nav entries: {stats['nav_entries_removed']} | ncx points: "
            f"{stats['ncx_points_removed']} (+{stats['ncx_retargeted']} retargeted) | "
            f"links neutralized: {stats['links_neutralized']:,}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

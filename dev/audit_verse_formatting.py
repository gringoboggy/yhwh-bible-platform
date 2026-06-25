#!/usr/bin/env python3
"""Scripture-body formatting auditor — WS1 of the Kobo deep-audit program (2026-06-24).

THE PROBLEMS THIS CATCHES (device-QA of the flagship eink kepub, root-caused vs the built epub):

1. **Mid-verse line breaks.** A single verse is split across multiple ``<p class="verse-p">``
   blocks — the continuation paragraph has NO ``id="v-{book}-{ch}-{v}"`` verse anchor (it carries
   only the verse's ``vbadge-…`` study badge, or nothing). On a Kobo kepub every ``<p>`` is
   block-level, so the reader sees a line break in the middle of a verse. (gen 19:1's
   "Lot saw them…" is a 2nd paragraph still tagged ``vbadge-gen-19-1-comm``.)

2. **Stray pilcrows ¶** in the verse text — the "weird symbol after the verse marker"
   (gen 46:13, gen 49:14). A KJV paragraph mark that leaked into the rendered text.

3. **Mixed / inconsistent base translation.** ¶ and ``[bracketed]`` supplied words are KJV-isms;
   they appear on a few verses (gen 46:13, 49:14) whose neighbours are modern WEB text
   ("When he finished talking with him, God went up from Abraham") → the English base is mixed.
   The auditor flags EVERY such verse so the fix covers the whole class, not just the two seen.

4. **badge-trail / leading-space** counts after verse badges (a presentation metric, WARN-only).

USAGE:
    py -3 dev/audit_verse_formatting.py <built.epub | built.kepub.epub | *.html> [...]

Exit code 1 if any mid-verse break or stray pilcrow is found (the device-visible defects).
Edition/canon/platform-agnostic: it reads the verse anchors the build emits.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from dataclasses import dataclass, field

# A scripture verse paragraph (build_edition emits `<p class="verse-p">…`).
_VERSE_P_RE = re.compile(r'<p\b[^>]*class="[^"]*\bverse-p\b[^"]*"[^>]*>(.*?)</p>', re.DOTALL)
# A verse START carries the canonical anchor; a continuation paragraph does NOT.
_VSTART_RE = re.compile(r'id="v-([a-z0-9]+)-(\d+)-(\d+)"')
# A continuation paragraph still carries the verse's study badge id.
_VBADGE_RE = re.compile(r'id="vbadge-([a-z0-9]+)-(\d+)-(\d+)-')
# KJV supplied-word italics rendered as [lowercase …] — NOT [1] footnote markers.
_KJV_BRACKET_RE = re.compile(r"\[[a-z][^\]]{0,40}\]")
_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class Finding:
    kind: str
    verse: str
    detail: str = ""


@dataclass
class Report:
    edition: str
    verses: int = 0
    multi_paragraph: list[Finding] = field(default_factory=list)
    pilcrow: list[Finding] = field(default_factory=list)
    kjv_bracket: list[Finding] = field(default_factory=list)
    badge_trail: int = 0

    @property
    def failed(self) -> bool:
        # The device-visible defects: a mid-verse line break or a stray pilcrow.
        return bool(self.multi_paragraph or self.pilcrow)


def _fmt(owner: tuple[str, int, int] | None) -> str:
    if owner is None:
        return "unknown"
    b, c, v = owner
    return f"{b} {c}:{v}"


def _text(inner: str) -> str:
    return _TAG_RE.sub("", inner)


def _scan_into(html: str, rep: Report) -> Report:
    current: tuple[str, int, int] | None = None
    for m in _VERSE_P_RE.finditer(html):
        inner = m.group(1)
        vs = _VSTART_RE.search(inner)
        if vs:
            current = (vs.group(1), int(vs.group(2)), int(vs.group(3)))
            rep.verses += 1
            owner = current
        else:
            vb = _VBADGE_RE.search(inner)
            owner = (vb.group(1), int(vb.group(2)), int(vb.group(3))) if vb else current
            rep.multi_paragraph.append(Finding("multi_paragraph", _fmt(owner), _text(inner)[:60].strip()))
        text = _text(inner)
        if "¶" in text:
            rep.pilcrow.append(Finding("pilcrow", _fmt(owner)))
        if _KJV_BRACKET_RE.search(text):
            rep.kjv_bracket.append(Finding("kjv_bracket", _fmt(owner), _KJV_BRACKET_RE.search(text).group(0)))
        rep.badge_trail += inner.count('class="badge-trail"')
    return rep


def scan_html(html: str, edition: str = "(html)") -> Report:
    """Scan one HTML chunk and return a fresh Report."""
    return _scan_into(html, Report(edition=edition))


def audit_epub(path: str) -> Report:
    """Aggregate the scan across every content document in a built EPUB/KEPUB."""
    rep = Report(edition=path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1])
    with zipfile.ZipFile(path) as zf:
        for n in zf.namelist():
            if n.endswith((".html", ".xhtml")):
                _scan_into(zf.read(n).decode("utf-8", "replace"), rep)
    return rep


def _print(rep: Report, sample: int) -> bool:
    print(f"\n=== {rep.edition} ===")
    print(f"  verses scanned: {rep.verses}")
    print(f"  ERROR mid-verse line breaks (multi-<p> verses): {len(rep.multi_paragraph)}")
    print(f"  ERROR stray pilcrows ¶ in verse text          : {len(rep.pilcrow)}")
    print(f"  WARN  mixed-translation [bracket] verses       : {len(rep.kjv_bracket)}")
    print(f"  INFO  badge-trail spans                        : {rep.badge_trail}")
    for f in rep.multi_paragraph[:sample]:
        print(f"        break  {f.verse:>14s}  …{f.detail}")
    for f in rep.pilcrow[:sample]:
        print(f"        pilcrow {f.verse:>13s}")
    for f in rep.kjv_bracket[:sample]:
        print(f"        bracket {f.verse:>13s}  {f.detail}")
    print(f"  RESULT: {'FAIL' if rep.failed else 'PASS'}")
    return rep.failed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Find scripture-body formatting defects in a built EPUB/KEPUB.")
    ap.add_argument("paths", nargs="+", help="built .epub / .kepub.epub / .html files")
    ap.add_argument("--sample", type=int, default=15, help="how many example findings to print per class")
    args = ap.parse_args(argv)
    any_fail = False
    for p in args.paths:
        try:
            if p.endswith((".html", ".xhtml")):
                with open(p, encoding="utf-8") as fh:
                    rep = scan_html(fh.read(), p)
            else:
                rep = audit_epub(p)
        except (zipfile.BadZipFile, OSError) as e:
            print(f"\n=== {p} ===\n  SKIP: {e}")
            any_fail = True
            continue
        any_fail |= _print(rep, args.sample)
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())

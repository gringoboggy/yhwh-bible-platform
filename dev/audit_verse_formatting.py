#!/usr/bin/env python3
"""Scripture-body formatting auditor — WS1 of the Kobo deep-audit program (2026-06-24).

Re-architected 2026-06-24 after the first cut measured the WRONG thing. Proven against
the built flagship eink kepub AND the base HTML (`epub_working/`); the build preserves
paragraph structure, so the base is both where the defect lives and where it is fixed.

THE DEFECTS THIS CATCHES (device-QA of the flagship eink kepub, color Kobo):

1. **Mid-verse line break** (ERROR) — a single verse's TEXT spans a ``<p class="verse-p">``
   boundary. The signature is a verse-p paragraph that begins with ALPHABETIC PROSE
   *before* its first verse marker: that leading prose is the previous verse's tail, and
   the ``</p><p>`` boundary fell inside the verse. On a Kobo kepub every ``<p>`` is
   block-level, so the reader sees a line break mid-verse.
   Example (gen 19:1): paragraph A ends "...Lot sat in the gate of Sodom."; paragraph B
   *opens* "Lot saw them, and rose up to meet them. He bowed himself..." then the verse-2
   marker — so verse 1 is split across A and B.

   This is NOT the same as the original "paragraph with no v- anchor" heuristic, which
   counted 1 Clement (strategy-B plain ``<span class="vn">`` chapters), psalm
   superscriptions, Song-of-Songs speaker rubrics and apocrypha section headings — none of
   which are mid-verse breaks — while MISSING the real gen/exo narrative breaks (whose
   continuation paragraph still carries the *next* verse's anchor).

2. **Stray pilcrow ¶** (ERROR) in verse text — the "weird symbol after the verse marker"
   (gen 46:13 / 49:14): a KJV paragraph mark that leaked into the rendered WEB text.

3. **Mixed / inconsistent base translation** (WARN) — ``[bracketed]`` supplied words are a
   KJV-ism; they appear on a few verses whose neighbours are modern WEB text → the English
   base is mixed. The auditor flags every such verse so the fix covers the whole class.

4. **badge-trail / leading-space** counts after verse badges (presentation metric, INFO).

Pilcrow / bracket are attributed to the nearest PRECEDING verse marker in the same
paragraph (so gen 46:13 reads as 46:13, not the paragraph's first verse 46:1).

The apocrypha books with a documented irregular layout (1 Enoch dual-witness columns,
Jubilees/Manasses section headings, strategy-B chapters) are split into a WARN bucket so
the ERROR gate stays trustworthy for the regular-layout canon, where a mid-verse break is
an unambiguous, fixable defect. Pass ``--all`` to gate on every book.

USAGE:
    py -3 dev/audit_verse_formatting.py <built.epub | built.kepub.epub | base/*.html> [...]

Exit code 1 if any ERROR (regular-book mid-verse break, or a stray pilcrow) is found.
Edition / canon / platform-agnostic: it reads the verse anchors the build emits.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from dataclasses import dataclass, field

# A scripture verse paragraph (build_edition emits `<p class="verse-p">` / `verse-p-flush`).
_VERSE_P_RE = re.compile(r'<p\b[^>]*class="[^"]*\bverse-p\b[^"]*"[^>]*>(.*?)</p>', re.DOTALL)
# A verse marker: the deep-link anchor (strategy A) OR a bare verse-number span (strategy B).
_FIRST_MARKER_RE = re.compile(r'<a\b[^>]*id="v-[a-z0-9]+-\d+-\d+"|<span class="vn">')
# The canonical verse anchor carries book/chapter/verse.
_VANCHOR_RE = re.compile(r'id="v-([a-z0-9]+)-(\d+)-(\d+)"')
_VN_SPAN_RE = re.compile(r'<span class="vn">')
# KJV supplied-word italics rendered as [lowercase …] — NOT [1] footnote markers.
_KJV_BRACKET_RE = re.compile(r"\[[a-z][^\]]{0,40}\]")
# Prose = a real word (≥2 letters); excludes note-marker digits and single-glyph badges.
_PROSE_RE = re.compile(r"[A-Za-z]{2,}")
_TAG_RE = re.compile(r"<[^>]+>")

# Books with a documented irregular layout (roadmap "irregular-layout residual" +
# strategy-B apocrypha): dual-witness columns, section headings, plain-vn chapters.
# A mid-verse break here is editorial/known-residual, not a regular-canon defect → WARN.
IRREGULAR_BOOKS = frozenset({"aes", "1en", "2en", "jub", "mq1", "mq2", "mq3", "sir", "man", "4ba", "1cl", "1es", "2es"})

# Poetry / wisdom / lament / poetic-prophet books: a verse split across poetic LINES is
# intentional typography, not the device defect (user decision 2026-06-25 "keep" poetry,
# dev/HUMAN_DECISIONS.md) → WARN, never the ERROR gate. Kept in sync with the build's
# `_MIDVERSE_BREAK_KEEP_BOOKS` (scripts/build_edition.py). Daniel/Ezekiel/Jonah are
# prose-dominant → they stay in the narrative (ERROR) gate.
POETRY_BOOKS = frozenset(
    {
        "psa",
        "sng",
        "job",
        "pro",
        "ecc",
        "lam",
        "bar",
        "isa",
        "jer",
        "hos",
        "joe",
        "amo",
        "oba",
        "mic",
        "nah",
        "hab",
        "zep",
        "hag",
        "zec",
        "mal",
    }
)


@dataclass
class Finding:
    kind: str
    verse: str
    detail: str = ""


@dataclass
class Report:
    edition: str
    verses: int = 0  # deep-linked scripture verses (v- anchors)
    strategy_b_verses: int = 0  # plain-vn verses (1cl etc.)
    mid_verse_break: list[Finding] = field(default_factory=list)  # ERROR, narrative/prose books
    irregular_break: list[Finding] = field(default_factory=list)  # WARN, irregular books
    poetry_break: list[Finding] = field(default_factory=list)  # WARN, poetry/wisdom/prophet (kept)
    strategy_b_continuation: list[Finding] = field(default_factory=list)  # WARN
    superscription: list[Finding] = field(default_factory=list)  # INFO (psalm titles, rubrics, headings)
    pilcrow: list[Finding] = field(default_factory=list)  # ERROR
    kjv_bracket: list[Finding] = field(default_factory=list)  # WARN (mixed translation)
    badge_trail: int = 0

    @property
    def failed(self) -> bool:
        # Device-visible defects in the regular-layout canon: a mid-verse break or a stray ¶.
        return bool(self.mid_verse_break or self.pilcrow)


def _fmt(owner: tuple[str, int, int] | None) -> str:
    if owner is None:
        return "unknown"
    b, c, v = owner
    return f"{b} {c}:{v}"


def _text(inner: str) -> str:
    return _TAG_RE.sub("", inner)


def _owner_at(pos: int, anchors: list[tuple[int, tuple[str, int, int]]], current: tuple[str, int, int] | None):
    """The verse whose anchor most recently precedes `pos` within the paragraph, else carried `current`."""
    best = current
    for apos, ident in anchors:
        if apos <= pos:
            best = ident
        else:
            break
    return best


def _scan_into(html: str, rep: Report, gate_all: bool = False) -> Report:
    current: tuple[str, int, int] | None = None  # last verse anchor seen (carries across paragraphs)
    for m in _VERSE_P_RE.finditer(html):
        inner = m.group(1)
        anchors = [
            (am.start(), (am.group(1), int(am.group(2)), int(am.group(3)))) for am in _VANCHOR_RE.finditer(inner)
        ]
        n_vn = len(_VN_SPAN_RE.findall(inner))
        rep.verses += len(anchors)
        rep.strategy_b_verses += max(0, n_vn - len(anchors))

        mk = _FIRST_MARKER_RE.search(inner)
        lead = _text(inner[: mk.start()]) if mk else _text(inner)
        has_prose = bool(_PROSE_RE.search(lead))
        has_vanchor = bool(anchors)

        if has_prose:
            if mk and has_vanchor:
                # Real mid-verse break: prose tail of `current`, then the next verse marker.
                owner = current  # the verse whose tail spilled = the previous paragraph's last anchor
                if owner is None:
                    # No preceding verse to continue → this is a section heading / book intro
                    # sharing a paragraph with the first following verse (e.g. Jubilees'
                    # editorial headings), not a mid-verse break.
                    rep.superscription.append(Finding("superscription", _fmt(owner), lead.strip()[:60]))
                else:
                    f = Finding("mid_verse_break", _fmt(owner), lead.strip()[:60])
                    book = owner[0]
                    if not gate_all and book in IRREGULAR_BOOKS:
                        rep.irregular_break.append(f)
                    elif not gate_all and book in POETRY_BOOKS:
                        rep.poetry_break.append(f)
                    else:
                        rep.mid_verse_break.append(f)
            elif mk:  # has_vn but no v- anchor → strategy-B chapter split mid-verse
                rep.strategy_b_continuation.append(Finding("strategy_b_continuation", _fmt(current), lead.strip()[:60]))
            else:  # prose-only paragraph, no verse marker → psalm title / Song rubric / section heading
                rep.superscription.append(Finding("superscription", _fmt(current), lead.strip()[:60]))

        text = _text(inner)
        for pm in re.finditer("¶", inner):
            rep.pilcrow.append(Finding("pilcrow", _fmt(_owner_at(pm.start(), anchors, current))))
        for bm in _KJV_BRACKET_RE.finditer(inner):
            rep.kjv_bracket.append(Finding("kjv_bracket", _fmt(_owner_at(bm.start(), anchors, current)), bm.group(0)))
        rep.badge_trail += inner.count('class="badge-trail"')

        if anchors:
            current = anchors[-1][1]
    return rep


def scan_html(html: str, edition: str = "(html)", gate_all: bool = False) -> Report:
    """Scan one HTML chunk and return a fresh Report."""
    return _scan_into(html, Report(edition=edition), gate_all)


def audit_epub(path: str, gate_all: bool = False) -> Report:
    """Aggregate the scan across every content document in a built EPUB/KEPUB."""
    rep = Report(edition=path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1])
    with zipfile.ZipFile(path) as zf:
        for n in zf.namelist():
            if n.endswith((".html", ".xhtml")):
                _scan_into(zf.read(n).decode("utf-8", "replace"), rep, gate_all)
    return rep


def _print(rep: Report, sample: int) -> bool:
    print(f"\n=== {rep.edition} ===")
    print(f"  verses scanned: {rep.verses} deep-linked + {rep.strategy_b_verses} plain-vn (strategy-B)")
    print(f"  ERROR mid-verse line breaks (regular canon)    : {len(rep.mid_verse_break)}")
    print(f"  ERROR stray pilcrows ¶ in verse text           : {len(rep.pilcrow)}")
    print(f"  WARN  mid-verse breaks in poetry (kept)         : {len(rep.poetry_break)}")
    print(f"  WARN  mid-verse breaks in irregular apocrypha   : {len(rep.irregular_break)}")
    print(f"  WARN  strategy-B chapter splits                 : {len(rep.strategy_b_continuation)}")
    print(f"  WARN  mixed-translation [bracket] verses        : {len(rep.kjv_bracket)}")
    print(f"  INFO  superscriptions / rubrics / headings      : {len(rep.superscription)}")
    print(f"  INFO  badge-trail spans                         : {rep.badge_trail}")
    for f in rep.mid_verse_break[:sample]:
        print(f"        break   {f.verse:>14s}  …{f.detail}")
    for f in rep.pilcrow[:sample]:
        print(f"        pilcrow {f.verse:>14s}")
    for f in rep.kjv_bracket[:sample]:
        print(f"        bracket {f.verse:>14s}  {f.detail}")
    print(f"  RESULT: {'FAIL' if rep.failed else 'PASS'}")
    return rep.failed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Find scripture-body formatting defects in a built EPUB/KEPUB.")
    ap.add_argument("paths", nargs="+", help="built .epub / .kepub.epub / base .html files")
    ap.add_argument("--sample", type=int, default=15, help="how many example findings to print per class")
    ap.add_argument("--all", action="store_true", help="gate on every book (irregular apocrypha included)")
    args = ap.parse_args(argv)
    any_fail = False
    for p in args.paths:
        try:
            if p.endswith((".html", ".xhtml")):
                with open(p, encoding="utf-8") as fh:
                    rep = scan_html(fh.read(), p, args.all)
            else:
                rep = audit_epub(p, args.all)
        except (zipfile.BadZipFile, OSError) as e:
            print(f"\n=== {p} ===\n  SKIP: {e}")
            any_fail = True
            continue
        any_fail |= _print(rep, args.sample)
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())

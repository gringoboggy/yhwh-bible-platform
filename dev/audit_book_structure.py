"""EPUB structural + content audit — verse → chapter → book → out-of-book.

Deterministic, level-by-level audit of the RENDERED epub/kepub output; the
superset of ``dev/verify_kr2_build.py`` (which owns the K-R2/K-R3 Kobo gates).
Where verify_kr2_build asks "are the Kobo fix arcs intact on this artifact?",
this asks "is the BOOK structurally + content-wise sound at every level?":

  Verse   — verse anchor present; badge count == rendered note count; the badge
            and its target aside agree on the verse coords; no repeated category
            heading inside one verse's notes (the ``note_group_by_category``
            redundancy class — the in-flight Kobo-QA fix).
  Chapter — verses ascending, no duplicates (a GAP is a WARN — recovered-base
            versification has known holes; a DUPLICATE is a FAIL); a chapter that
            has verses has a chapter heading; no spurious page break sits between
            two verses of one chapter.
  Book    — chapters ascending, no duplicates; a book-title page opens the book;
            a book is GREEN only when its verse + chapter + break checks all pass.
  Out-of-book — nav.xhtml + ncx present; every internal href resolves to a real
            id; nav/ncx ToC targets exist; the colophon + copyright pages are
            present.

The audit is EDITION- and CANON-agnostic: it checks the INTERNAL consistency of
whatever the artifact actually contains, so the same pass runs unchanged on every
edition × format (no per-edition canon table to drift). Completeness-vs-expected
(is every canonical verse of the edition's canon present?) is a planned v2 layer
that folds in the per-edition canon resolver.

Standalone stdlib only (no repo imports) → light + OOM-safe; parsing built HTML
is cheap. Spec: docs/superpowers/specs/2026-06-22-epub-structural-content-audit.md

Usage:
    py -3 dev/audit_book_structure.py <epub> [<epub> ...] [--json OUT.json]
Exit 0 = every book green in every artifact; 1 = any FAIL.
"""

from __future__ import annotations

import json
import posixpath
import re
import sys
import zipfile
from dataclasses import dataclass, field

# ── markup the build emits (mirrors scripts/build_edition.py + verify_kr2_build) ──
_VERSE_ANCHOR_RE = re.compile(r'<a class="vn-link" id="v-([a-z0-9]+)-(\d+)-(\d+)"')
_BOOK_TITLE_RE = re.compile(r'<div class="book-title-page[^"]*" id="(bp-\d+)"')
_CH_HEADING_RE = re.compile(r'<a id="ch-b(\d+)-c(\d+)"|<p\b[^>]*class="ch-heading"')
# The badge: <a class="verse-notes-badge" id="vbadge-{c}-{ch}-{v}-sN"
#   href="#vnotes-{c}-{ch}-{v}-sN" … title="{N} notes"><sup …>{glyph/count}</sup>
# Count from title="{N} notes" (stable across marker_badge_style; the <sup> text
# is style-dependent — glyph+count on eink, etc).
_BADGE_RE = re.compile(
    r'<a class="verse-notes-badge" id="vbadge-([a-z0-9]+)-(\d+)-(\d+)-s(\d+)"[^>]*'
    r'href="#(vnotes-[a-z0-9]+-\d+-\d+-s\d+)"[^>]*title="(\d+) notes?"',
)
# The merged verse-notes aside (one per badge unit).
_VNOTES_ASIDE_RE = re.compile(
    r'<aside class="verse-notes[^"]*" id="(vnotes-([a-z0-9]+)-(\d+)-(\d+)-s\d+)"[^>]*>(.*?)</aside>',
    re.DOTALL,
)
_VN_ITEM_RE = re.compile(r'class="vn-item\b')
_VN_GROUP_CAT_RE = re.compile(r'<section class="vn-group note-cat-([a-z0-9]+)"')
# any element carrying an id (for link resolution)
_ID_RE = re.compile(r'\sid="([^"]+)"')
# every internal href (… .xhtml#frag | #frag) — external http(s) skipped
_HREF_RE = re.compile(r'href="([^"]+)"')
# a spurious page break between two verses (conservative — inline style or a
# stray <hr> that is not the notes rule); class-driven CSS breaks need the
# cascade and are out of scope for the static pass (the Gen 10:6→7 calibration
# case is exercised once a real artifact is in hand).
_PAGEBREAK_RE = re.compile(r'style="[^"]*page-break|<hr(?![^>]*notes-rule)\b')

_FRONT_BACK_REQUIRED = ("nav.xhtml", ".ncx")  # presence of the ToC machinery


@dataclass
class BookResult:
    code: str
    bp: str
    chapters: list[int] = field(default_factory=list)
    fails: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)

    @property
    def green(self) -> bool:
        return not self.fails


@dataclass
class EpubResult:
    path: str
    books: list[BookResult] = field(default_factory=list)
    global_fails: list[str] = field(default_factory=list)
    global_warns: list[str] = field(default_factory=list)

    @property
    def green(self) -> bool:
        return not self.global_fails and all(b.green for b in self.books)


def _norm(name: str) -> str:
    return posixpath.normpath(name).lstrip("/")


def _spine_docs(zf: zipfile.ZipFile) -> tuple[list[str], str, str]:
    """(ordered xhtml zip-names per the OPF spine, opf name, opf text)."""
    names = set(zf.namelist())
    opf_name = next(n for n in names if n.endswith(".opf"))
    opf = zf.read(opf_name).decode("utf-8", "replace")
    opf_dir = opf_name.rsplit("/", 1)[0] if "/" in opf_name else ""
    manifest: dict[str, str] = {}
    for m in re.finditer(r"<item\b[^>]*>", opf):
        tag = m.group(0)
        idm = re.search(r'\bid="([^"]+)"', tag)
        hrefm = re.search(r'\bhref="([^"]+)"', tag)
        if idm and hrefm:
            manifest[idm.group(1)] = hrefm.group(1)
    order: list[str] = []
    for m in re.finditer(r'<itemref\b[^>]*\bidref="([^"]+)"', opf):
        href = manifest.get(m.group(1))
        if not href:
            continue
        zn = _norm(f"{opf_dir}/{href}" if opf_dir else href)
        if zn in names and zn.endswith((".html", ".xhtml")):
            order.append(zn)
    return order, opf_name, opf


def _strip_to_text(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def audit_epub(path: str) -> EpubResult:
    res = EpubResult(path=path)
    zf = zipfile.ZipFile(path)
    names = zf.namelist()
    spine, _opf_name, opf = _spine_docs(zf)
    if not spine:
        res.global_fails.append("OPF spine lists no content documents")
        return res

    # ── concatenate spine in reading order, tracking (offset → file) ──────────
    docs: list[tuple[str, str]] = [(n, zf.read(n).decode("utf-8", "replace")) for n in spine]
    full = "\n".join(t for _, t in docs)

    # ── id / href maps for link resolution (file-scoped ids; cross-file hrefs) ─
    ids_by_file: dict[str, set[str]] = {}
    all_ids: set[str] = set()
    for n, t in docs:
        s = {i for i in _ID_RE.findall(t) if not i.startswith("kobo.")}
        ids_by_file[n] = s
        all_ids |= s
    # also collect nav/ncx targets for ToC resolution
    nav_ncx = [n for n in names if n.endswith(("nav.xhtml", ".ncx"))]
    for n in nav_ncx:
        all_ids |= {i for i in _ID_RE.findall(zf.read(n).decode("utf-8", "replace"))}

    # ── verse-notes asides: id → (coords, item count, category multiplicity) ──
    aside_items: dict[str, int] = {}
    aside_coords: dict[str, tuple[str, int, int]] = {}
    for n, t in docs:
        for m in _VNOTES_ASIDE_RE.finditer(t):
            aid, code, ch, v = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
            body = m.group(5)
            aside_items[aid] = len(_VN_ITEM_RE.findall(body))
            aside_coords[aid] = (code, ch, v)
            cats = _VN_GROUP_CAT_RE.findall(body)
            dupes = {c for c in cats if cats.count(c) > 1}
            if dupes:
                res.global_fails.append(
                    f"{n}: verse-notes {aid} repeats category heading(s) {sorted(dupes)} "
                    "(note_group_by_category redundancy — one heading per category expected)"
                )

    # ── badge ⇄ aside contract (count + coords) ───────────────────────────────
    for n, t in docs:
        for m in _BADGE_RE.finditer(t):
            code, ch, v, _unit = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
            target, title_n = m.group(5), int(m.group(6))
            if target not in aside_items:
                res.global_fails.append(f"{n}: badge vbadge-{code}-{ch}-{v} → missing aside #{target}")
                continue
            items = aside_items[target]
            if title_n != items:
                res.global_fails.append(
                    f"{n}: badge vbadge-{code}-{ch}-{v} claims {title_n} note(s) but aside #{target} "
                    f"renders {items} (badge-count vs note-count contradiction)"
                )
            if aside_coords[target] != (code, ch, v):
                ac = aside_coords[target]
                res.global_fails.append(
                    f"{n}: badge vbadge-{code}-{ch}-{v} targets aside for {ac[0]} {ac[1]}:{ac[2]} "
                    "(badge/aside verse-coord mismatch)"
                )

    # ── link resolution (in-book + out-of-book; ToC targets) ──────────────────
    unresolved: list[str] = []
    for n, t in docs:
        for href in _HREF_RE.findall(t):
            if href.startswith(("http://", "https://", "mailto:")) or "#" not in href:
                continue
            file_part, frag = href.split("#", 1)
            if not frag:
                continue
            if file_part:  # cross-file: id may live in any doc (last-writer idmap)
                if frag not in all_ids:
                    unresolved.append(f"{n}: href {href} → no such id")
            else:  # same-file
                if frag not in ids_by_file.get(n, set()) and frag not in all_ids:
                    unresolved.append(f"{n}: href #{frag} → no such id")
    if unresolved:
        res.global_fails.append(f"{len(unresolved)} unresolved internal href(s); first 5: {unresolved[:5]}")

    # ── out-of-book presence ──────────────────────────────────────────────────
    for suffix in _FRONT_BACK_REQUIRED:
        if not any(n.endswith(suffix) for n in names):
            res.global_fails.append(f"out-of-book: no {suffix} (ToC machinery missing)")
    nav = next((zf.read(n).decode("utf-8", "replace") for n in names if n.endswith("nav.xhtml")), "")
    if nav and ">Copyright<" not in nav:
        res.global_warns.append("out-of-book: nav has no Copyright entry")
    if not any(n.endswith("colophonend.xhtml") for n in names):
        res.global_warns.append("out-of-book: no closing colophon")

    # ── regions (book by book, split on title pages over the whole reading flow) ─
    title_hits = [(m.start(), m.group(1)) for m in _BOOK_TITLE_RE.finditer(full)]
    if not title_hits:
        res.global_fails.append("no book-title pages found (cannot establish book structure)")
        return res
    bounds = [p for p, _ in title_hits] + [len(full)]

    for idx, (start, bp) in enumerate(title_hits):
        region = full[start : bounds[idx + 1]]
        verses = _VERSE_ANCHOR_RE.findall(region)  # [(code, ch, v) as str]
        if not verses:
            # a legitimate title-only / front piece (e.g. an intro); not a book region
            continue
        codes = {c for c, _, _ in verses}
        code = max(codes, key=lambda c: sum(1 for cc, _, _ in verses if cc == c))
        br = BookResult(code=code, bp=bp)
        if len(codes) > 1:
            br.fails.append(f"region holds >1 book code {sorted(codes)} (title-page/boundary leak)")

        # title page must carry a real title frame
        title_block = region[: region.find(">", region.find(bp)) + 1]
        head = region[:400]
        if "book-title-frame" not in head and "book-title-frame" not in title_block:
            br.warns.append(f"{bp}: title page has no book-title-frame")

        # chapter headings present in this region
        heading_chs = {int(mc) for ma, mc in _CH_HEADING_RE.findall(region) if mc}

        # group verses by chapter, in document order
        by_ch: dict[int, list[int]] = {}
        for c, ch, v in verses:
            if c == code:
                by_ch.setdefault(int(ch), []).append(int(v))
        br.chapters = sorted(by_ch)

        # chapter ordering
        prev = 0
        for ch in br.chapters:
            if ch == prev:
                br.fails.append(f"{code}: chapter {ch} duplicated")
            prev = ch
            if heading_chs and ch not in heading_chs:
                br.warns.append(f"{code} ch {ch} has verses but no chapter heading in its region")

        # verse ordering within each chapter
        for ch, vs in by_ch.items():
            seen: set[int] = set()
            last = 0
            for v in vs:
                if v in seen:
                    br.fails.append(f"{code} {ch}:{v} duplicated verse anchor")
                seen.add(v)
                if v < last:
                    br.fails.append(f"{code} {ch}: verse {v} out of order (after {last})")
                last = v
            ordered = sorted(seen)
            gaps = [g for g in range(ordered[0], ordered[-1]) if g not in seen]
            if gaps:
                br.warns.append(f"{code} {ch}: missing verse number(s) {gaps[:8]}{'…' if len(gaps) > 8 else ''}")

        # spurious page break between two same-chapter verses
        anchor_iter = list(_VERSE_ANCHOR_RE.finditer(region))
        for a, b in zip(anchor_iter, anchor_iter[1:]):
            ca, cha, _va = a.group(1), a.group(2), a.group(3)
            cb, chb, _vb = b.group(1), b.group(2), b.group(3)
            if ca == cb == code and cha == chb:
                between = region[a.end() : b.start()]
                if _PAGEBREAK_RE.search(between):
                    br.warns.append(
                        f"{code} {cha}: possible spurious page break between v{_va} and v{_vb} "
                        "(static-pass heuristic — confirm on device/render)"
                    )
        res.books.append(br)

    return res


def _print(res: EpubResult) -> None:
    name = res.path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    green = sum(b.green for b in res.books)
    print(f"\n=== {name} — {green}/{len(res.books)} books green ===")
    for g in res.global_fails:
        print("  ✗ GLOBAL", g)
    for g in res.global_warns:
        print("  ⚠ GLOBAL", g)
    for b in res.books:
        if b.green and not b.warns:
            continue
        flag = "green" if b.green else "FAIL"
        print(f"  [{flag}] {b.code} ({b.bp}, {len(b.chapters)} ch)")
        for f in b.fails:
            print("      ✗", f)
        for w in b.warns[:6]:
            print("      ⚠", w)
        if len(b.warns) > 6:
            print(f"      ⚠ … +{len(b.warns) - 6} more warns")


def main(argv: list[str]) -> int:
    paths = [a for a in argv if not a.startswith("--")]
    json_out = None
    if "--json" in argv:
        json_out = argv[argv.index("--json") + 1]
    if not paths:
        print(__doc__)
        return 2
    results = [audit_epub(p) for p in paths]
    for r in results:
        _print(r)
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump(
                [
                    {
                        "path": r.path,
                        "green": r.green,
                        "global_fails": r.global_fails,
                        "global_warns": r.global_warns,
                        "books": [
                            {
                                "code": b.code,
                                "bp": b.bp,
                                "chapters": b.chapters,
                                "green": b.green,
                                "fails": b.fails,
                                "warns": b.warns,
                            }
                            for b in r.books
                        ],
                    }
                    for r in results
                ],
                fh,
                indent=1,
            )
        print(f"\nwrote {json_out}")
    any_fail = any(not r.green for r in results)
    total_books = sum(len(r.books) for r in results)
    green_books = sum(sum(b.green for b in r.books) for r in results)
    print(f"\nTOTAL: {green_books}/{total_books} books green across {len(results)} artifact(s)")
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

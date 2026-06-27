#!/usr/bin/env python3
"""Gate G3 — idmap / cross-file-link integrity of a built EPUB (no rebuild).

The eink build splits the one big scripture document into hundreds of
``index_split_NNN_MM.html`` pieces, then runs ``rewrite_links`` over an *idmap*
(``id`` -> the piece that now holds it) to repoint every former same-file
``#frag`` link at ``piece#frag``. A bug in that idmap (a stale/missing entry, a
bare/full-href fallback on a miss, a split that duplicates an element) ships an
EPUB that is structurally valid yet has **dead or wrong cross-file links** — a
defect invisible to a static same-file check and only felt when a real e-reader
follows the link to the wrong piece (program dims A3 / B6 / propagation P4).

This gate closes the specific gap the two existing finders leave:
  * ``audit_book_structure.py`` resolves a cross-file ``file#frag`` against the
    GLOBAL union of all ids — so ``A.html#frag`` "passes" whenever ``frag`` lives
    in ANY piece, even when piece ``A`` does not hold it (the wrong-piece miss).
  * ``audit_popup_formula.py`` only ever checks SAME-FILE popup hrefs.
G3 instead resolves each ``file#frag`` against the ids of the *named* piece, and
adds the split-only invariants (cross-piece id-uniqueness, no orphaned piece).

Checks (all per spec gate G3):
  1. CROSS/SAME-FILE FRAG — every ``href="file#frag"`` resolves to a piece that
     actually holds ``id="frag"`` (or ``<a name="frag">``); every bare
     ``href="#frag"`` resolves within its own file.
  2. NOTEREF/BADGE TARGET — every noteref / badge / vn-link / backlink anchor's
     target resolves (the verse-badge -> aside link and the aside back-link),
     reported under a noteref label even when check 1 also covers it.
  3. ID UNIQUENESS — no ``id``/``name`` value occurs in more than one spine piece
     (a duplicated id makes the idmap ambiguous and silently misroutes #frag nav).
  4. ORPHAN / TOC — every xhtml manifest item is in the spine (except the nav
     doc); every spine itemref's piece exists; nav + ncx targets resolve.

Standalone stdlib only (mirrors ``audit_book_structure.py``) -> light + OOM-safe.

Round-15 D2 adds an **xref-class breakout**: scripture cross-references (a NON-noteref
``<a>`` whose target frag is a ``v-`` verse or ``ch-`` chapter anchor) are counted +
failure-bucketed separately from the noteref popup/badge bulk, and guardable by their own
``--min-xrefs`` floor — so a wholesale scripture-xref loss (a canon-filter that drops the
target book, an idmap miss) FAILS instead of hiding behind the ~45k noteref count that keeps
``--min-links`` satisfied.

Usage:
    py -3 dev/audit_idmap_frags.py <epub> [<epub> ...] [--json OUT.json] [--max-show N]
        [--min-links N] [--min-xrefs N]
Exit 0 = every internal link resolves + ids unique + no orphan (+ ≥ --min-links frag/noteref
anchors and ≥ --min-xrefs scripture v-/ch- xrefs survive, if given); 1 = any FAIL.
"""

from __future__ import annotations

import json
import posixpath
import re
import sys
import zipfile
from dataclasses import dataclass, field

# Any element carrying an id, and the legacy ``<a name="…">`` anchor form (both are
# valid #frag targets). ``kobo.*`` ids are kepubify's injected per-segment spans —
# they are synthetic, never link targets, and excluded (mirrors audit_book_structure).
_ID_RE = re.compile(r'\sid="([^"]+)"')
_NAME_RE = re.compile(r'<a\b[^>]*\sname="([^"]+)"')
# An opening <a …> tag (captures its attribute blob so href/class/epub:type can be
# read together -> one pass classifies a plain link vs a noteref/badge/backlink).
_ANCHOR_RE = re.compile(r"<a\b([^>]*)>", re.I)
_HREF_ATTR_RE = re.compile(r'\bhref="([^"]+)"')
# ncx targets live in <content src="…">; nav targets are ordinary <a href> anchors.
_NCX_SRC_RE = re.compile(r'<content\b[^>]*\bsrc="([^"]+)"')
# Classes / epub:type that mark a note-navigation anchor (badge -> aside, aside
# back-link, inline marker). Used only to LABEL a finding, never to skip resolution.
_NOTEREF_CLASS_RE = re.compile(
    r'class="[^"]*\b(?:verse-notes-badge|vn-link|note-ref|note-backref|study-glossary-jump)\b'
)
# A scripture CROSS-REFERENCE target: the verse (``v-…``) or chapter (``ch-…``) anchor a
# NON-noteref <a> points at — i.e. a verse→verse / verse→chapter / nav→scripture link, as
# opposed to a note popup/badge (noteref) or a front/back-matter link. Broken out (round-15
# D2) so a WHOLESALE xref loss (a canon-filter that drops the target book, an idmap miss that
# bares every link) is VISIBLE in the stats + guardable by ``--min-xrefs``, instead of hiding
# inside the ~45k-strong noteref bulk that keeps ``--min-links`` satisfied on its own. ``vnote-``
# starts ``v`` but not ``v-``, so note targets never match.
_XREF_FRAG_RE = re.compile(r"^(?:v-|ch-)")
_EXTERNAL = ("http://", "https://", "mailto:", "tel:", "data:", "javascript:")


@dataclass
class IdmapResult:
    path: str
    fails: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    @property
    def green(self) -> bool:
        return not self.fails


def _norm(name: str) -> str:
    return posixpath.normpath(name).lstrip("/")


def _join(basedir: str, rel: str) -> str:
    """Resolve a member-relative href to its zip name (hrefs resolve against the
    directory of the document that contains them, not the OPF dir)."""
    return _norm(f"{basedir}/{rel}" if basedir else rel)


def _dir(name: str) -> str:
    return name.rsplit("/", 1)[0] if "/" in name else ""


def _base(name: str) -> str:
    return name.rsplit("/", 1)[-1]


def _manifest_spine(zf: zipfile.ZipFile) -> tuple[dict[str, tuple[str, str, str]], list[str], list[str]]:
    """Parse the OPF. Returns (manifest{id:(zipname, media_type, properties)},
    ordered spine zipnames, ordered spine idrefs)."""
    names = set(zf.namelist())
    opf_name = next(n for n in names if n.endswith(".opf"))
    opf = zf.read(opf_name).decode("utf-8", "replace")
    opf_dir = _dir(opf_name)
    manifest: dict[str, tuple[str, str, str]] = {}
    for m in re.finditer(r"<item\b[^>]*>", opf):
        tag = m.group(0)
        idm = re.search(r'\bid="([^"]+)"', tag)
        hrefm = re.search(r'\bhref="([^"]+)"', tag)
        mtm = re.search(r'\bmedia-type="([^"]+)"', tag)
        propm = re.search(r'\bproperties="([^"]+)"', tag)
        if idm and hrefm:
            zn = _norm(f"{opf_dir}/{hrefm.group(1)}" if opf_dir else hrefm.group(1))
            manifest[idm.group(1)] = (zn, mtm.group(1) if mtm else "", propm.group(1) if propm else "")
    spine_idrefs = [m.group(1) for m in re.finditer(r'<itemref\b[^>]*\bidref="([^"]+)"', opf)]
    spine_zipnames = [manifest[i][0] for i in spine_idrefs if i in manifest]
    return manifest, spine_zipnames, spine_idrefs


def _ids_of(text: str) -> set[str]:
    s = {i for i in _ID_RE.findall(text)}
    s |= set(_NAME_RE.findall(text))
    return {i for i in s if not i.startswith("kobo.")}


def _anchor_targets(text: str):
    """Yield (href, kind) for every <a …> opening tag that carries an href, where
    ``kind`` ∈ {``"noteref"``, ``"xref"``, ``"plain"``}: noteref = a note popup/badge/backlink
    anchor; xref = a NON-noteref link to a scripture ``v-``/``ch-`` anchor (the D2 breakout);
    plain = anything else (front/back-matter, stylesheet-relative, etc.)."""
    for m in _ANCHOR_RE.finditer(text):
        attrs = m.group(1)
        hm = _HREF_ATTR_RE.search(attrs)
        if not hm:
            continue
        href = hm.group(1)
        is_note = (
            'epub:type="noteref"' in attrs
            or 'epub:type="backlink"' in attrs
            or _NOTEREF_CLASS_RE.search(attrs) is not None
        )
        if is_note:
            kind = "noteref"
        else:
            frag = href.split("#", 1)[1] if "#" in href else ""
            kind = "xref" if _XREF_FRAG_RE.match(frag) else "plain"
        yield href, kind


def _resolve(href: str, refname: str, basedir: str, names: set[str], ids_by_file: dict[str, set[str]]) -> str | None:
    """Return a reason string if ``href`` is a dead/wrong internal frag link, else
    None (external / no-frag / resolved)."""
    if href.startswith(_EXTERNAL) or "#" not in href:
        return None
    file_part, frag = href.split("#", 1)
    if not frag:
        return None
    if file_part:
        tgt = _join(basedir, file_part)
        if tgt not in names:
            return "target file not in epub"
        if tgt not in ids_by_file:  # exists but not an (x)html piece -> no id namespace to check
            return None
        if frag not in ids_by_file[tgt]:
            return f'no id "{frag}" in target piece {_base(tgt)}'
    else:  # bare #frag -> same file
        if frag not in ids_by_file.get(refname, set()):
            return f'no id "{frag}" in same file'
    return None


def _dup_id_fails(spine_html: list[str], ids_by_file: dict[str, set[str]]) -> tuple[list[str], int]:
    """Check 3 — no id/name occurs in more than one spine piece. Returns
    (fail strings, total distinct id count)."""
    id_to_pieces: dict[str, list[str]] = {}
    for n in spine_html:
        for i in ids_by_file[n]:
            id_to_pieces.setdefault(i, []).append(n)
    fails = [
        f'duplicate id "{i}" in {len(ps)} spine pieces {[_base(p) for p in ps][:4]} (idmap is ambiguous)'
        for i, ps in id_to_pieces.items()
        if len(ps) > 1
    ]
    return fails, len(id_to_pieces)


def _link_fails(
    zf: zipfile.ZipFile, html_members: list[str], names: set[str], ids_by_file: dict[str, set[str]]
) -> tuple[list[str], list[str], list[str], int, int, int]:
    """Checks 1 + 2 — every anchor frag link resolves to its NAMED piece. Returns
    (plain-link fails, noteref fails, xref fails, plain count, noteref count, xref count).
    The xref class (scripture ``v-``/``ch-`` cross-references) is broken out from plain links
    so a wholesale xref loss is visible + floor-guardable (round-15 D2)."""
    plain_fails: list[str] = []
    note_fails: list[str] = []
    xref_fails: list[str] = []
    n_plain = n_notes = n_xrefs = 0
    bucket = {"plain": plain_fails, "noteref": note_fails, "xref": xref_fails}
    for n in html_members:
        text = zf.read(n).decode("utf-8", "replace")
        base = _dir(n)
        for href, kind in _anchor_targets(text):
            if href.startswith(_EXTERNAL) or "#" not in href or not href.split("#", 1)[1]:
                continue
            if kind == "noteref":
                n_notes += 1
            elif kind == "xref":
                n_xrefs += 1
            else:
                n_plain += 1
            reason = _resolve(href, n, base, names, ids_by_file)
            if reason:
                bucket[kind].append(f"{_base(n)} -> {href} -> {reason}")
    return plain_fails, note_fails, xref_fails, n_plain, n_notes, n_xrefs


def _ncx_fails(zf: zipfile.ZipFile, names: set[str], ids_by_file: dict[str, set[str]]) -> tuple[list[str], int]:
    """Check 4 (ncx half) — every ncx <content src> file/frag resolves."""
    fails: list[str] = []
    n_toc = 0
    for n in (m for m in names if m.endswith(".ncx")):
        text = zf.read(n).decode("utf-8", "replace")
        base = _dir(n)
        for src in _NCX_SRC_RE.findall(text):
            if src.startswith(_EXTERNAL) or "#" not in src or not src.split("#", 1)[1]:
                fp = src.split("#", 1)[0]  # no-frag ncx target -> just verify the file exists
                if fp and _join(base, fp) not in names:
                    fails.append(f"{_base(n)} -> {src} -> target file not in epub")
                continue
            n_toc += 1
            reason = _resolve(src, n, base, names, ids_by_file)
            if reason:
                fails.append(f"{_base(n)} -> {src} -> {reason}")
    return fails, n_toc


def _orphan_fails(manifest: dict[str, tuple[str, str, str]], spine_idrefs: list[str], names: set[str]) -> list[str]:
    """Check 4 (spine half) — no xhtml manifest item is unreachable; every spine
    itemref resolves to a real manifest piece present in the zip."""
    fails: list[str] = []
    spine_idref_set = set(spine_idrefs)
    for iid, (zn, mt, props) in manifest.items():
        if mt != "application/xhtml+xml" or "nav" in props.split():
            continue  # the nav doc is referenced via properties, not the linear spine
        if iid not in spine_idref_set:
            fails.append(f"orphan: xhtml manifest item {_base(zn)} is not referenced by the spine")
    for iid in spine_idrefs:
        if iid not in manifest:
            fails.append(f"spine itemref {iid} has no manifest item")
        elif manifest[iid][0] not in names:
            fails.append(f"spine piece {_base(manifest[iid][0])} ({iid}) is missing from the epub")
    return fails


def audit_epub(path: str, min_links: int = 0, min_xrefs: int = 0) -> IdmapResult:
    res = IdmapResult(path=path)
    zf = zipfile.ZipFile(path)
    names = set(zf.namelist())
    manifest, spine, spine_idrefs = _manifest_spine(zf)
    if not spine:
        res.fails.append("OPF spine lists no content documents")
        return res

    # id namespace for EVERY (x)html member (cross-file links may target front/back
    # matter that is not a split piece, e.g. copyright.xhtml / the glossary).
    html_members = [n for n in names if n.endswith((".html", ".xhtml"))]
    ids_by_file: dict[str, set[str]] = {n: _ids_of(zf.read(n).decode("utf-8", "replace")) for n in html_members}
    spine_html = [n for n in spine if n.endswith((".html", ".xhtml"))]

    dup_fails, n_ids = _dup_id_fails(spine_html, ids_by_file)
    plain_fails, note_fails, xref_fails, n_plain, n_notes, n_xrefs = _link_fails(zf, html_members, names, ids_by_file)
    ncx_fails, n_toc = _ncx_fails(zf, names, ids_by_file)
    orphan_fails = _orphan_fails(manifest, spine_idrefs, names)

    res.fails.extend(dup_fails)
    res.fails.extend(plain_fails)
    res.fails.extend(xref_fails)
    res.fails.extend(note_fails)
    res.fails.extend(ncx_fails)
    res.fails.extend(orphan_fails)
    res.stats = {
        "spine_pieces": len(spine_html),
        "html_members": len(html_members),
        "frag_links": n_plain + n_xrefs,  # all NON-noteref frag links (unchanged total)
        "xref_links": n_xrefs,  # D2 breakout: scripture v-/ch- cross-references (subset of frag_links)
        "noteref_links": n_notes,
        "ncx_targets": n_toc,
        "unique_ids": n_ids,
        "duplicate_ids": len(dup_fails),
        "link_fails": len(plain_fails) + len(xref_fails) + len(ncx_fails),
        "xref_fails": len(xref_fails),  # D2 breakout: dead scripture cross-references (subset of link_fails)
        "noteref_fails": len(note_fails),
        "orphan_fails": len(orphan_fails),
    }
    # Presence floor (round-15 D2): every check above only ever reports a link that
    # FAILS to resolve — so a build that silently dropped ALL its xref/noteref anchors
    # (a canon-filter or idmap that emitted ZERO) would pass G3 vacuously (0 links → 0
    # fails → green). Require a minimum surviving frag+noteref count so wholesale xref
    # loss FAILS the gate instead of passing. Off (0) by default; the per-build gate
    # passes a real floor calibrated well under the edition's true count.
    if min_links and (n_plain + n_xrefs + n_notes) < min_links:
        res.fails.append(
            f"presence floor: only {n_plain + n_xrefs + n_notes} frag+noteref links resolve-checked "
            f"(< {min_links}) — the build may have dropped its cross-references wholesale"
        )
    # Dedicated xref floor (round-15 D2): the ~45k-strong noteref bulk keeps ``--min-links``
    # satisfied even if EVERY scripture cross-reference were dropped, so guard the xref class
    # on its own. Off (0) by default; the per-build gate calibrates it under the edition's
    # true xref count.
    if min_xrefs and n_xrefs < min_xrefs:
        res.fails.append(
            f"xref floor: only {n_xrefs} scripture xref (v-/ch-) links resolve-checked "
            f"(< {min_xrefs}) — the build may have dropped its scripture cross-references wholesale"
        )
    return res


def _print(res: IdmapResult, max_show: int) -> None:
    name = _base(res.path.replace("\\", "/"))
    s = res.stats
    status = "PASS" if res.green else "FAIL"
    print(f"\n=== {name} — G3 idmap/cross-file-link {status} ===")
    if s:
        print(
            f"  pieces={s['spine_pieces']} html_members={s['html_members']} "
            f"frag_links={s['frag_links']} (xref={s['xref_links']}) noteref_links={s['noteref_links']} "
            f"ncx_targets={s['ncx_targets']} unique_ids={s['unique_ids']} "
            f"xref_fails={s['xref_fails']}"
        )
    for f in res.fails[:max_show]:
        print("  ✗", f)
    if len(res.fails) > max_show:
        print(f"  ✗ … +{len(res.fails) - max_show} more FAIL(s)")
    for w in res.warns[:max_show]:
        print("  ⚠", w)


def main(argv: list[str]) -> int:
    # Exclude both the flags AND the value that immediately follows each value-flag,
    # so a flag value (e.g. the N after --min-links) is never mistaken for an epub path.
    _value_flags = ("--json", "--max-show", "--min-links", "--min-xrefs")
    _skip = {argv.index(f) + 1 for f in _value_flags if f in argv}
    paths = [a for i, a in enumerate(argv) if not a.startswith("--") and i not in _skip]
    json_out = argv[argv.index("--json") + 1] if "--json" in argv else None
    max_show = int(argv[argv.index("--max-show") + 1]) if "--max-show" in argv else 50
    min_links = int(argv[argv.index("--min-links") + 1]) if "--min-links" in argv else 0
    min_xrefs = int(argv[argv.index("--min-xrefs") + 1]) if "--min-xrefs" in argv else 0
    if not paths:
        print(__doc__)
        return 2
    results = [audit_epub(p, min_links=min_links, min_xrefs=min_xrefs) for p in paths]
    for r in results:
        _print(r, max_show)
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump(
                [
                    {"path": r.path, "green": r.green, "stats": r.stats, "fails": r.fails, "warns": r.warns}
                    for r in results
                ],
                fh,
                indent=1,
            )
        print(f"\nwrote {json_out}")
    any_fail = any(not r.green for r in results)
    print(f"\nTOTAL: {sum(r.green for r in results)}/{len(results)} artifact(s) idmap-clean")
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

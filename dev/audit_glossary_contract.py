#!/usr/bin/env python3
"""Gate G5 — study-glossary format-contract validator of a built EPUB (no rebuild).

The eink build streams the one huge study-notes backmatter monolith (the
``index_split_900`` document — the pooled per-verse study asides, ~tens of MB for a
study edition) into ~400 KB pieces so Kobo's e-ink Footnote *navigate* path resolves
a study-badge jump. The split cuts at ``h2.study-book-head`` boundaries and, when one
book exceeds the target, between ``div.study-glossary-entry`` atoms
(``_iter_study_glossary_pieces`` / ``_iter_study_glossary_pieces_from_file`` in
``scripts/build_edition.py``). A bug in that streaming split (an over-packed group, a
piece that straddles two book heads, a duplicated/untargetable atom) ships a
structurally-valid EPUB whose glossary **busts the Kobo navigate cap** — the badge tap
silently lands at the piece top instead of the note (program dims A5 / propagation P3).

The navigate-target cap is ``FILE_SPLIT_TARGET_DEFAULT`` (``build_edition.py``): the
glossary backmatter is split with ``gtarget = min(target, FILE_SPLIT_TARGET_DEFAULT)``
and every real edition has ``target >= default``, so ``gtarget == 400_000``. The build
groups *codepoint* lengths of the joined atoms (``_group_glossary_atoms`` uses
``len(atom)``), measured over the ``section.study-notes-index`` INNER content — NOT the
file's byte size (the head/section wrappers + multi-byte Hebrew/Greek/Geʽez inflate
bytes well past the codepoint count). This gate therefore measures the inner codepoint
length, exactly the quantity the build caps.

Checks (all per spec gate G5):
  1. CAP — every glossary piece's ``study-notes-index`` inner <= the navigate-target
     cap (400_000 codepoints). A piece over cap is the Kobo footnote/nav failure.
  2. ONE BOOK PER PIECE — no split piece (``index_split_900_NN.html``) packs two
     ``h2.study-book-head`` markers; a piece is one book's glossary section max (a
     ``#study-paz`` fragment jump must land on the book head, not mid-book residue).
  3. ATOM CONSERVATION — every ``div.study-glossary-entry`` atom carries an id; no
     entry id (and no book-head id) is duplicated across pieces (a streaming split
     that re-scans a book span duplicates atoms / makes #frag nav ambiguous). Total
     atoms == distinct atom ids is the conservation invariant; a mismatch fails.
  4. REFERENCE PARTITION (opt-in ``--reference-split``; memory-heavy) — reconstruct the
     monolith from the pieces and re-run the in-memory reference splitter
     ``split_study_glossary_document``; assert the built pieces are the byte-identical
     partition the reference produces. SOUND ONLY on pieces that have NOT been through the
     build's ``rewrite_links`` pass (e.g. the raw reference-splitter output the synthetic
     tests feed it). A REAL built epub's glossary pieces are POST-rewrite (cross-file hrefs
     carry the ``index_split_<n>_<m>.html`` piece infix), and the build splits the monolith
     PRE-rewrite reserving ``_atom_rewrite_headroom`` per link — so a post-rewrite
     reconstruction CANNOT reproduce the build's cut points (atom lengths AND reserved
     headroom both differ). Check 4 therefore detects rewritten pieces and SKIPS with a WARN
     rather than false-FAIL. OFF by default (it re-materializes the ~tens-of-MB monolith the
     streaming build exists to avoid). The str==from-file partition equality is verified
     soundly, on the PRE-rewrite flagship monolith, by
     ``tests/test_file_split::TestStreamGlossaryFromFile`` (D5).

Standalone stdlib only for checks 1-3 (mirrors ``audit_idmap_frags.py``) -> light +
OOM-safe; ``--reference-split`` lazily imports ``scripts.build_edition``.

Usage:
    py -3 dev/audit_glossary_contract.py <epub> [<epub> ...]
        [--json OUT.json] [--max-show N] [--cap N] [--stem S] [--reference-split]
Exit 0 = every glossary piece is under cap + one-book-per-piece + atoms conserved;
1 = any FAIL.
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from dataclasses import dataclass, field

# = scripts.build_edition.FILE_SPLIT_TARGET_DEFAULT (build_edition.py ~L4599). The study
# backmatter splits with gtarget = min(target, FILE_SPLIT_TARGET_DEFAULT) (~L5725) and every
# real edition has target >= default, so the effective glossary cap is this value.
NAVIGATE_TARGET_CAP = 400_000
# = scripts.build_edition.EINK_STUDY_BACKMATTER_STEM (build_edition.py ~L2296). Glossary
# pieces are ``<stem>.html`` (unsplit) or ``<stem>_NN.html`` (the streamed pieces).
GLOSSARY_STEM = "index_split_900"

_SECTION_OPEN_RE = re.compile(r'<section class="study-notes-index"[^>]*>')
_SECTION_TOKEN_RE = re.compile(r"</?section\b")
_BOOK_HEAD_RE = re.compile(r'<h2 class="study-book-head"')
_BOOK_HEAD_ID_RE = re.compile(r'<h2 class="study-book-head"\s+id="([^"]+)"')
_ENTRY_RE = re.compile(r'<div class="study-glossary-entry"')
_ENTRY_ID_RE = re.compile(r'<div class="study-glossary-entry"\s+id="([^"]+)"')
# kepubify wraps text in <span class="koboSpan" id="kobo.N.M">; its presence inflates the
# measured inner past the build's codepoint count (the cap was applied pre-kepubify).
_KOBO_SPAN_RE = re.compile(r'<span class="koboSpan"')
# Built glossary pieces that have been through apply_file_split's ``rewrite_links`` carry
# cross-file hrefs with the piece infix (``index_split_<n>_<m>.html``). The PRE-split monolith
# the build actually split never has this form, so its presence marks a POST-rewrite
# reconstruction that check 4 (--reference-split) cannot soundly re-split (the build reserves
# per-link ``_atom_rewrite_headroom`` PRE-rewrite). See ``_reference_split_via_raw``.
_REWRITTEN_HREF_RE = re.compile(r'(?:href|src)="index_split_\d+_\d+\.html')


@dataclass
class GlossaryPiece:
    name: str
    order: int  # the _NN index; -1 for the bare unsplit ``<stem>.html``
    is_split: bool  # True for ``<stem>_NN.html`` (a streamed piece subject to the 1-book rule)
    inner: str | None  # study-notes-index inner content, or None when the section is missing


@dataclass
class GlossaryContractResult:
    path: str
    fails: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    @property
    def green(self) -> bool:
        return not self.fails


def _base(name: str) -> str:
    return name.replace("\\", "/").rsplit("/", 1)[-1]


def _section_inner(text: str) -> str | None:
    """Depth-aware extraction of the ``section.study-notes-index`` INNER content.

    The glossary nests ``section.vn-group`` inside each entry, so a naive non-greedy
    ``</section>`` would close on the first nested group (mirrors
    ``build_edition._study_index_section_parts``). Returns the inner string, or None
    when the section open/close cannot be located."""
    om = _SECTION_OPEN_RE.search(text)
    if not om:
        return None
    depth = 1
    for tok in _SECTION_TOKEN_RE.finditer(text, om.end()):
        if tok.group(0) == "</section":
            depth -= 1
            if depth == 0:
                return text[om.end() : tok.start()]
        else:
            depth += 1
    return None


def _glossary_pieces(zf: zipfile.ZipFile, stem: str) -> list[GlossaryPiece]:
    """Locate + order every glossary piece in the EPUB by the build's naming scheme."""
    pat = re.compile(rf"(?:.*/)?{re.escape(stem)}(?:_(\d+))?\.html$")
    pieces: list[GlossaryPiece] = []
    for name in zf.namelist():
        m = pat.match(name)
        if not m:
            continue
        suffix = m.group(1)
        text = zf.read(name).decode("utf-8", "replace")
        pieces.append(
            GlossaryPiece(
                name=name,
                order=int(suffix) if suffix is not None else -1,
                is_split=suffix is not None,
                inner=_section_inner(text),
            )
        )
    pieces.sort(key=lambda p: p.order)
    return pieces


def _cap_fails(pieces: list[GlossaryPiece], cap: int) -> tuple[list[str], int]:
    """Check 1 — every piece's inner codepoint length <= cap. Returns (fails, max_cp)."""
    fails: list[str] = []
    max_cp = 0
    for p in pieces:
        if p.inner is None:
            continue
        cp = len(p.inner)
        max_cp = max(max_cp, cp)
        if cp > cap:
            fails.append(f"{_base(p.name)} inner {cp} cp > cap {cap} (+{cp - cap}) — busts the Kobo navigate cap")
    return fails, max_cp


def _bookhead_fails(pieces: list[GlossaryPiece]) -> tuple[list[str], int]:
    """Check 2 — no SPLIT piece packs >1 book-head. Returns (fails, total_book_heads).

    The bare unsplit ``<stem>.html`` is exempt: a glossary that fit in one piece legitimately
    holds every book head; the one-book-per-piece contract only governs the streamed pieces."""
    fails: list[str] = []
    total = 0
    for p in pieces:
        if p.inner is None:
            continue
        n = len(_BOOK_HEAD_RE.findall(p.inner))
        total += n
        if p.is_split and n > 1:
            ids = _BOOK_HEAD_ID_RE.findall(p.inner)
            fails.append(f"{_base(p.name)} packs {n} book-heads {ids[:4]} — a glossary piece holds one book max")
    return fails, total


def _atom_fails(pieces: list[GlossaryPiece]) -> tuple[list[str], dict[str, int]]:
    """Check 3 — atom conservation: every entry has an id; no entry/book-head id is
    duplicated across pieces. Returns (fails, stat-deltas)."""
    fails: list[str] = []
    total_atoms = 0
    missing_id = 0
    entry_pieces: dict[str, list[str]] = {}
    bookhead_pieces: dict[str, list[str]] = {}
    for p in pieces:
        if p.inner is None:
            fails.append(f"{_base(p.name)} has no study-notes-index section (malformed glossary piece)")
            continue
        n_entries = len(_ENTRY_RE.findall(p.inner))
        total_atoms += n_entries
        ids = _ENTRY_ID_RE.findall(p.inner)
        if len(ids) < n_entries:
            missing_id += n_entries - len(ids)
            fails.append(
                f"{_base(p.name)} has {n_entries - len(ids)} study-glossary-entry div(s) "
                f"without an id (untargetable — dropped from navigation)"
            )
        for i in ids:
            entry_pieces.setdefault(i, []).append(p.name)
        for i in _BOOK_HEAD_ID_RE.findall(p.inner):
            bookhead_pieces.setdefault(i, []).append(p.name)
    for i, ps in entry_pieces.items():
        if len(ps) > 1:
            fails.append(
                f'duplicate glossary entry id "{i}" in {len(ps)} pieces '
                f"{[_base(x) for x in ps][:4]} (streaming split duplicated an atom)"
            )
    for i, ps in bookhead_pieces.items():
        if len(ps) > 1:
            fails.append(
                f'duplicate book-head id "{i}" in {len(ps)} pieces '
                f"{[_base(x) for x in ps][:4]} (a book was split across pieces with its head duplicated)"
            )
    stats = {
        "total_atoms": total_atoms,
        "distinct_atom_ids": len(entry_pieces),
        "duplicate_atom_ids": sum(1 for ps in entry_pieces.values() if len(ps) > 1),
        "missing_atom_ids": missing_id,
        "duplicate_bookhead_ids": sum(1 for ps in bookhead_pieces.values() if len(ps) > 1),
    }
    return fails, stats


def audit_epub(
    path: str,
    *,
    cap: int = NAVIGATE_TARGET_CAP,
    stem: str = GLOSSARY_STEM,
    reference_split: bool = False,
) -> GlossaryContractResult:
    res = GlossaryContractResult(path=path)
    with zipfile.ZipFile(path) as zf:
        pieces = _glossary_pieces(zf, stem)
        kepub = any(_KOBO_SPAN_RE.search(p.inner) for p in pieces if p.inner is not None)
        raw_by_name = {p.name: zf.read(p.name).decode("utf-8", "replace") for p in pieces} if reference_split else {}
    if not pieces:
        res.fails.append(f'no glossary pieces ("{stem}*.html") found in the EPUB')
        return res
    if kepub:
        res.warns.append(
            "kepub koboSpan markup detected — the cap is measured on the post-kepubify inner, "
            "which is inflated vs the build's pre-kepubify codepoint count; run on the source .epub "
            "for an exact cap figure"
        )

    cap_fails, max_cp = _cap_fails(pieces, cap)
    bookhead_fails, total_heads = _bookhead_fails(pieces)
    atom_fails, atom_stats = _atom_fails(pieces)
    res.fails.extend(cap_fails)
    res.fails.extend(bookhead_fails)
    res.fails.extend(atom_fails)

    if reference_split:
        ref_fails, ref_warns = _reference_split_via_raw(raw_by_name, pieces, stem, cap)
        res.fails.extend(ref_fails)
        res.warns.extend(ref_warns)

    res.stats = {
        "pieces": len(pieces),
        "split_pieces": sum(1 for p in pieces if p.is_split),
        "malformed_pieces": sum(1 for p in pieces if p.inner is None),
        "cap": cap,
        "max_inner_cp": max_cp,
        "over_cap": len(cap_fails),
        "total_book_heads": total_heads,
        "multi_bookhead_pieces": len(bookhead_fails),
        "is_kepub": int(kepub),
        **atom_stats,
    }
    return res


def _reference_split_via_raw(
    raw_by_name: dict[str, str], pieces: list[GlossaryPiece], stem: str, cap: int
) -> tuple[list[str], list[str]]:
    """Check 4 — reconstruct the monolith from the raw piece bytes and compare the built
    partition to the reference splitter's output (the standing str==from-file proof)."""
    try:
        from scripts.build_edition import split_study_glossary_document
    except Exception as exc:  # pragma: no cover - import-env dependent
        return [], [f"--reference-split skipped: cannot import scripts.build_edition ({exc})"]
    ordered = [p for p in pieces if p.inner is not None]
    if any(p.inner is None for p in pieces):
        return ["--reference-split: a piece has no study-notes-index section; cannot reconstruct"], []
    if not ordered:
        return [], ["--reference-split: no glossary pieces to reconstruct"]
    first_text = raw_by_name[ordered[0].name]
    wrap = _doc_wrappers(first_text)
    if wrap is None:
        return [], ["--reference-split: could not recover the document wrapper from the first piece"]
    head, body_prefix_open, body_suffix, tail = wrap
    full_inner = "".join(p.inner or "" for p in ordered)
    if _REWRITTEN_HREF_RE.search(full_inner):
        # The pieces are a REAL built epub (post rewrite_links): re-splitting this
        # reconstruction cannot reproduce the build's PRE-rewrite, headroom-reserved cut
        # points (atom lengths + reserved _atom_rewrite_headroom both differ), so a byte
        # comparison here is a guaranteed false-FAIL, not a real divergence. Skip with a WARN;
        # the sound str==from-file proof is tests/test_file_split::TestStreamGlossaryFromFile.
        return [], [
            "--reference-split skipped: the built glossary pieces are POST-rewrite_links "
            "(cross-file hrefs carry the index_split_<n>_<m>.html piece infix). The build splits "
            "the monolith PRE-rewrite, reserving _atom_rewrite_headroom per link, so re-splitting "
            "the post-rewrite reconstruction cannot reproduce the build's cut points. The sound "
            "str==from-file partition proof runs on the PRE-rewrite monolith in "
            "tests/test_file_split::TestStreamGlossaryFromFile (D5)."
        ]
    doc = head + body_prefix_open + full_inner + "</section>" + body_suffix + tail
    ref = split_study_glossary_document(doc, stem, cap)
    ref_inners = [(_base(n), _section_inner(t)) for n, t in ref]
    epub_inners = [(_base(p.name), p.inner) for p in ordered]
    fails: list[str] = []
    if len(ref_inners) != len(epub_inners):
        fails.append(
            f"reference partition has {len(ref_inners)} pieces but the EPUB has {len(epub_inners)} "
            f"(streaming split diverges from the str-path reference)"
        )
    for i, ((rn, ri), (en, ei)) in enumerate(zip(ref_inners, epub_inners, strict=False)):
        if ri != ei:
            fails.append(
                f"piece #{i} ({en}) inner diverges from reference ({rn}): "
                f"{len(ei) if ei else 0} vs {len(ri) if ri else 0} cp (atom mis-cut/drop/dup)"
            )
    return fails, []


def _doc_wrappers(text: str) -> tuple[str, str, str, str] | None:
    """Split a piece into (head, body_prefix+section_open, body_suffix, tail) so the monolith
    can be reconstructed as head + body_prefix+section_open + <all inners> + </section> +
    body_suffix + tail (mirrors the build's piece_body assembly)."""
    bm = re.search(r"<body\b[^>]*>", text)
    if not bm:
        return None
    body_start = bm.end()
    body_close = text.rfind("</body>")
    if body_close == -1 or body_close < body_start:
        return None
    head, body, tail = text[:body_start], text[body_start:body_close], text[body_close:]
    om = _SECTION_OPEN_RE.search(body)
    if not om:
        return None
    depth = 1
    close_start = -1
    for tok in _SECTION_TOKEN_RE.finditer(body, om.end()):
        if tok.group(0) == "</section":
            depth -= 1
            if depth == 0:
                close_start = tok.start()
                break
        else:
            depth += 1
    if close_start == -1:
        return None
    close_end = body.find(">", close_start) + 1
    return head, body[: om.end()], body[close_end:], tail


def _print(res: GlossaryContractResult, max_show: int) -> None:
    name = _base(res.path)
    s = res.stats
    status = "PASS" if res.green else "FAIL"
    print(f"\n=== {name} — G5 study-glossary contract {status} ===")
    if s:
        print(
            f"  pieces={s['pieces']} split={s['split_pieces']} cap={s['cap']} "
            f"max_inner_cp={s['max_inner_cp']} over_cap={s['over_cap']} "
            f"book_heads={s['total_book_heads']} multi_bookhead={s['multi_bookhead_pieces']} "
            f"atoms={s['total_atoms']} distinct_atom_ids={s['distinct_atom_ids']}"
        )
    for f in res.fails[:max_show]:
        print("  ✗", f)
    if len(res.fails) > max_show:
        print(f"  ✗ … +{len(res.fails) - max_show} more FAIL(s)")
    for w in res.warns[:max_show]:
        print("  ⚠", w)


def _arg(argv: list[str], flag: str, default: str | None = None) -> str | None:
    return argv[argv.index(flag) + 1] if flag in argv else default


def main(argv: list[str]) -> int:
    paths = [a for a in argv if not a.startswith("--")]
    # skip the value tokens that follow valued flags so they are not read as epub paths
    for flag in ("--json", "--max-show", "--cap", "--stem"):
        if flag in argv:
            val = argv[argv.index(flag) + 1]
            if val in paths:
                paths.remove(val)
    json_out = _arg(argv, "--json")
    max_show = int(_arg(argv, "--max-show", "50"))
    cap = int(_arg(argv, "--cap", str(NAVIGATE_TARGET_CAP)))
    stem = _arg(argv, "--stem", GLOSSARY_STEM)
    reference_split = "--reference-split" in argv
    if not paths:
        print(__doc__)
        return 2
    results = [audit_epub(p, cap=cap, stem=stem, reference_split=reference_split) for p in paths]
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
    print(f"\nTOTAL: {sum(r.green for r in results)}/{len(results)} artifact(s) glossary-contract-clean")
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

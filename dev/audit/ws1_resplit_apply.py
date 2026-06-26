#!/usr/bin/env python3
"""Apply the WS1 158-verse empty-verse re-split to the base HTML.

User-ratified 2026-06-25. For each group, the terminal verse's body currently holds the
empties' WEB prose AS A LEADING PREFIX (proven by ws1_resplit_verify.py). We RELOCATE that
leading prose substring back under each empty verse's own anchor — a pure substring move:
zero characters added or removed, apparatus (note-refs/sups) stays with its verse, every
#frag id is preserved. Byte-reversible by construction.

Dry-run by default (verifies every move). --apply writes. --base DIR targets a sandbox.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from html import unescape
from pathlib import Path

REPO = Path(__file__).resolve().parents[2] if (Path(__file__).resolve().parents[2] / "epub_working").exists() else None
DATA_DEFAULT = "dev/audit/ws1-empty-verse-resplit-data.json"

_ANCHOR_RE = re.compile(r'<a\s+class="vn-link"\s+id="v-([a-z0-9]+)-(\d+)-(\d+)"[^>]*>.*?</a>', re.DOTALL)
_NOTEREF_RE = re.compile(r'<a\b[^>]*class="[^"]*note-ref[^"]*"[^>]*>.*?</a>', re.DOTALL)
_SUP_RE = re.compile(r"<sup\b[^>]*>.*?</sup>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_CHHEAD = 'class="ch-heading"'


def _prose(fragment: str) -> str:
    s = _NOTEREF_RE.sub("", fragment)
    s = _SUP_RE.sub("", s)
    s = _TAG_RE.sub(" ", s)
    s = unescape(s)
    s = unicodedata.normalize("NFC", s)
    return _WS_RE.sub(" ", s).strip()


def _norm(s: str) -> str:
    return _WS_RE.sub(" ", unicodedata.normalize("NFC", unescape(s))).strip()


def _coord(c: str) -> tuple[str, int, int]:
    bk, rest = c.split(" ", 1)
    ch, vs = rest.split(":")
    return bk, int(ch), int(vs)


def _anchors(html: str):
    return [(m.group(1), int(m.group(2)), int(m.group(3)), m.start(), m.end()) for m in _ANCHOR_RE.finditer(html)]


def _body_end(html: str, anchor_end: int, next_start: int) -> int:
    seg = html[anchor_end:next_start]
    chpos = seg.find(_CHHEAD)
    if chpos != -1:
        pstart = seg.rfind("<p", 0, chpos)
        if pstart != -1:
            return anchor_end + pstart
    return next_start


def _safe_cuts(fragment: str) -> list[int]:
    """Offsets at which we may split without bisecting an apparatus element or a tag.
    A cut strictly INSIDE a note-ref/sup/tag would make _prose see a partial element
    (garbage), so only offsets outside every such span (boundaries included) are valid."""
    spans = []
    for rx in (_NOTEREF_RE, _SUP_RE, _TAG_RE):
        spans += [(m.start(), m.end()) for m in rx.finditer(fragment)]
    return [k for k in range(len(fragment) + 1) if not any(s < k < e for s, e in spans)]


def _find_seam(fragment: str, target: str) -> int:
    """Smallest SAFE offset k with _prose(fragment[:k]) == _norm(target) — i.e. right after
    target's last prose char, never inside an apparatus element/tag. -1 if not a clean
    prose-prefix. (Binary search is invalid here: a cut mid-element makes _prose length
    non-monotonic, so scan the safe offsets in order — verse bodies are small.)"""
    tgt = _norm(target)
    n = len(tgt)
    for k in _safe_cuts(fragment):
        p = _prose(fragment[:k])
        if len(p) < n:
            continue
        if p == tgt:
            return k
        if len(p) > n:
            break  # passed the length at a safe boundary without matching → no clean seam
    return -1


def apply_group(html: str, g: dict) -> tuple[str | None, str | None]:
    empties = [_coord(c) for c in g["empties"]]
    term = _coord(g["terminal"])
    web = g["web_per_verse"]
    anchors = _anchors(html)
    idx = {(a[0], a[1], a[2]): i for i, a in enumerate(anchors)}
    seq = empties + [term]
    pos = [idx.get(c) for c in seq]
    if any(p is None for p in pos):
        return None, f"missing anchor(s) in {g['empties']}+{g['terminal']}"
    if pos != list(range(pos[0], pos[0] + len(seq))):
        return None, f"empties+terminal not consecutive anchors (pos={pos})"
    ti = idx[term]
    next_start = anchors[ti + 1][3] if ti + 1 < len(anchors) else len(html)
    t_body_end = _body_end(html, anchors[ti][4], next_start)
    t_body = html[anchors[ti][4] : t_body_end]
    expect = _norm(" ".join(web[f"{c[1]}:{c[2]}"] for c in seq))
    if _prose(t_body) != expect:
        return None, f"terminal body prose != expected join ({g['terminal']})"
    # Peel each empty's WEB prose off the front of the terminal body, in order.
    segs: list[str] = []
    rest = t_body
    for c in empties:
        k = _find_seam(rest, web[f"{c[1]}:{c[2]}"])
        if k == -1:
            return None, f"seam not found for {c[0]} {c[1]}:{c[2]}"
        # Carry the trailing inter-clause whitespace with the relocated clause so the moved
        # verse ends with a space before the next verse's number badge (which otherwise abuts
        # it — `.vn-link` gets no left margin after plain text). The next verse's leading gap
        # comes from `.vn{margin-right}`. Pure relocation either way (no char added/removed).
        while k < len(rest) and rest[k].isspace():
            k += 1
        segs.append(rest[:k])
        rest = rest[k:]
    if _prose(rest) != _norm(web[f"{term[1]}:{term[2]}"]):
        return None, f"terminal residual prose != web[terminal] ({g['terminal']})"
    # Reconstruct the region [first-empty anchor start .. anchor after terminal).
    parts: list[str] = []
    for i, c in enumerate(empties):
        ai = anchors[idx[c]]
        nb_start = anchors[idx[c] + 1][3]
        a_html = html[ai[3] : ai[4]]
        old_body = html[ai[4] : nb_start]  # the empty verse's apparatus (no prose)
        parts.append(a_html + old_body + segs[i])
    parts.append(html[anchors[ti][3] : anchors[ti][4]] + rest)  # terminal anchor + residual
    parts.append(html[t_body_end:next_start])  # preserve any ch-heading tail
    region_start = anchors[idx[empties[0]]][3]
    new_html = html[:region_start] + "".join(parts) + html[next_start:]
    # Invariant: pure relocation — the region's character multiset is unchanged.
    if sorted(new_html[region_start : region_start + (next_start - region_start)]) != sorted(
        html[region_start:next_start]
    ):
        return None, f"char-multiset changed (NOT pure relocation) at {g['terminal']}"
    return new_html, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=None, help="base HTML dir (default: <repo>/epub_working)")
    ap.add_argument("--data", default=None)
    ap.add_argument("--apply", action="store_true", help="write the files (default: dry-run)")
    args = ap.parse_args()
    base = Path(args.base) if args.base else (REPO / "epub_working")
    data = json.loads(Path(args.data or (REPO / DATA_DEFAULT)).read_text(encoding="utf-8"))
    groups = data["resplit_groups"]

    by_file: dict[str, list[dict]] = {}
    for g in groups:
        by_file.setdefault(g["file"], []).append(g)

    total, ok, flags = 0, 0, []
    for fname, gs in sorted(by_file.items()):
        fp = base / fname
        if not fp.is_file():
            flags.append(f"{fname}: file missing")
            continue
        html = fp.read_text(encoding="utf-8")
        # Apply groups bottom-up (descending terminal position) so earlier offsets stay valid.
        gs_sorted = sorted(gs, key=lambda g: _coord(g["terminal"]), reverse=True)
        for g in gs_sorted:
            total += 1
            new_html, err = apply_group(html, g)
            if err:
                flags.append(f"{fname} {g['empties']}->{g['terminal']}: {err}")
            else:
                html = new_html
                ok += 1
        # post-file verification: re-extract each touched verse's prose == web
        for g in gs:
            anchors = _anchors(html)
            bodies = {}
            for i, a in enumerate(anchors):
                e = anchors[i + 1][3] if i + 1 < len(anchors) else len(html)
                be = _body_end(html, a[4], e)
                bodies[(a[0], a[1], a[2])] = _prose(html[a[4] : be])
            for c in g["empties"] + [g["terminal"]]:
                co = _coord(c)
                want = _norm(g["web_per_verse"][f"{co[1]}:{co[2]}"])
                got = bodies.get(co, "<absent>")
                if got != want:
                    flags.append(f"VERIFY FAIL {fname} {c}: prose != web (got={got[:50]!r} want={want[:50]!r})")
        if args.apply and not any(fname in f for f in flags):
            fp.write_text(html, encoding="utf-8")

    print(f"groups: {total}  applied-clean: {ok}  flagged: {len(flags)}")
    for f in flags[:60]:
        print("  -", f)
    if args.apply and not flags:
        print("APPLIED to", base)
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main())

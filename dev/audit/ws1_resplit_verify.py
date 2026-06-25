#!/usr/bin/env python3
"""P2 — independently re-verify the WS1 empty-verse re-split package vs the REAL base HTML.

Mac-lane ratification-hardening check (2026-06-25). For every resplit group, confirm:
  (a) each ``empties`` coord is a TRULY EMPTY verse anchor in the base (no scripture prose
      between its ``vn-link`` and the next verse anchor — apparatus markers don't count);
  (b) the terminal verse's full base prose == " ".join(web[empties...] + [web[terminal]])
      AND each web[empty] is a CLEAN LEADING PREFIX peelable in order (seam unambiguous);
  (c) the split is BYTE-REVERSIBLE: peeling the empties back off the terminal reconstructs
      exactly the per-verse WEB texts with single-space seams (no wording change).
Plus a COMPLETENESS scan: every empty-body verse anchor in the base must be classified
(resplit / deutero_defer / legit_omission) — no unclassified empties may exist.

Findings-only. Reads ``epub_working/`` (never writes). Run:
    .venv/bin/python dev/audit/ws1_resplit_verify.py
"""

from __future__ import annotations

import glob
import json
import re
import sys
import unicodedata
from html import unescape
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "epub_working"
DATA = REPO / "dev/audit/ws1-empty-verse-resplit-data.json"

_ANCHOR_RE = re.compile(r'<a\s+class="vn-link"\s+id="v-([a-z0-9]+)-(\d+)-(\d+)"[^>]*>.*?</a>', re.DOTALL)
_NOTEREF_RE = re.compile(r'<a\b[^>]*class="[^"]*note-ref[^"]*"[^>]*>.*?</a>', re.DOTALL)
_SUP_RE = re.compile(r"<sup\b[^>]*>.*?</sup>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _prose(fragment: str) -> str:
    s = _NOTEREF_RE.sub("", fragment)
    s = _SUP_RE.sub("", s)
    s = _TAG_RE.sub(" ", s)
    s = unescape(s)
    s = unicodedata.normalize("NFC", s)
    return _WS_RE.sub(" ", s).strip()


def _norm(s: str) -> str:
    return _WS_RE.sub(" ", unicodedata.normalize("NFC", unescape(s))).strip()


_file_cache: dict[str, dict] = {}


def _verse_bodies(fname: str) -> dict:
    if fname in _file_cache:
        return _file_cache[fname]
    html = (BASE / fname).read_text(encoding="utf-8")
    anchors = [(m.group(1), int(m.group(2)), int(m.group(3)), m.start(), m.end()) for m in _ANCHOR_RE.finditer(html)]
    bodies: dict[tuple[str, int, int], str] = {}
    for i, (bk, ch, vs, _s, e) in enumerate(anchors):
        nxt = anchors[i + 1][3] if i + 1 < len(anchors) else len(html)
        seg = html[e:nxt]
        # a chapter heading (<p class="ch-heading">...N...</p>) is a real boundary,
        # not verse prose — cut there so the next chapter's number doesn't bleed in.
        chpos = seg.find('class="ch-heading"')
        if chpos != -1:
            pstart = seg.rfind("<p", 0, chpos)
            if pstart != -1:
                seg = seg[:pstart]
        bodies[(bk, ch, vs)] = _prose(seg)
    _file_cache[fname] = bodies
    return bodies


def _coord(c: str) -> tuple[str, int, int]:
    bk, rest = c.split(" ", 1)
    ch, vs = rest.split(":")
    return bk, int(ch), int(vs)


def _peel(empties: list[str], web: dict, terminal: str, terminal_full: str) -> list[str]:
    """(b)+(c): peel each web[empty] off the terminal body in order; the residual must
    equal web[terminal] and the rejoin must reproduce the base body byte-for-byte."""
    problems: list[str] = []
    remaining, peeled = terminal_full, []
    for ec in empties:
        eb = _coord(ec)
        wtext = _norm(web.get(f"{eb[1]}:{eb[2]}", ""))
        if not wtext:
            problems.append(f"{ec}: no web text in data")
            continue
        if remaining.startswith(wtext):
            peeled.append(wtext)
            remaining = remaining[len(wtext) :].lstrip()
        else:
            problems.append(
                f"{ec}: web text NOT a clean leading prefix (web={wtext[:50]!r} | base-head={remaining[:50]!r})"
            )
            return problems
    tb = _coord(terminal)
    wterm = _norm(web.get(f"{tb[1]}:{tb[2]}", ""))
    if remaining != wterm:
        problems.append(f"{terminal}: residual!=web (resid={remaining[:50]!r} | web={wterm[:50]!r})")
    if _norm(" ".join(peeled + [wterm])) != _norm(terminal_full):
        problems.append(f"{terminal}: rejoin!=base body (NOT byte-reversible)")
    return problems


def _check_group(g: dict, samples: dict, want: set) -> tuple[list[str], str, list[str]]:
    empties, terminal, web = g["empties"], g["terminal"], g["web_per_verse"]
    try:
        bodies = _verse_bodies(g["file"])
    except FileNotFoundError:
        return empties, terminal, [f"base file {g['file']} not found"]
    tb = _coord(terminal)
    if tb not in bodies:
        return empties, terminal, [f"terminal anchor v-{tb[0]}-{tb[1]}-{tb[2]} absent"]
    terminal_full = bodies[tb]
    problems = [
        (
            f"{ec}: verse anchor MISSING in base"
            if _coord(ec) not in bodies
            else f"{ec}: anchor NOT empty (prose={bodies[_coord(ec)][:60]!r})"
        )
        for ec in empties
        if _coord(ec) not in bodies or bodies[_coord(ec)] != ""
    ]
    problems += _peel(empties, web, terminal, terminal_full)
    for ec in empties:
        if ec in want:
            eb = _coord(ec)
            samples[ec] = (
                f"v{eb[2]}=(empty) | v{tb[2]}={terminal_full[:130]!r}",
                f"v{eb[2]}={_norm(web.get(f'{eb[1]}:{eb[2]}', ''))[:110]!r} | "
                f"v{tb[2]}={_norm(web.get(f'{tb[1]}:{tb[2]}', ''))[:110]!r}",
            )
    return empties, terminal, problems


def _completeness(groups: list, data: dict) -> tuple[int, list, int]:
    """Every empty-body verse anchor in the base must be classified."""
    classified: set = set()
    for g in groups:
        classified.update(_coord(e) for e in g["empties"])
    classified.update(_coord(e["coord"]) for e in data["deutero_defer"])
    classified.update(_coord(e["coord"]) for e in data["legit_omission"])
    empty_in_base, unclassified = [], []
    for f in sorted(glob.glob(str(BASE / "*.html"))):
        try:
            bodies = _verse_bodies(Path(f).name)
        except Exception:
            continue
        for coord, body in bodies.items():
            if body == "":
                empty_in_base.append(coord)
                if coord not in classified:
                    unclassified.append((coord, Path(f).name))
    return len(empty_in_base), unclassified, len(classified)


def verify() -> dict:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    groups = data["resplit_groups"]
    safe: list = []
    flagged: list = []
    samples: dict = {}
    want = {"gen 8:15", "mat 5:4", "psa 10:12"}
    for g in groups:
        empties, terminal, problems = _check_group(g, samples, want)
        if problems:
            flagged.append((empties, terminal, problems))
        else:
            safe.append((empties, terminal))
    empty_in_base, unclassified, n_classified = _completeness(groups, data)
    return {
        "groups": len(groups),
        "safe_empties": sum(len(e) for e, _ in safe),
        "flagged": flagged,
        "samples": samples,
        "empty_in_base": empty_in_base,
        "classified": n_classified,
        "unclassified": unclassified,
        "deutero_defer": len(data["deutero_defer"]),
        "legit_omission": len(data["legit_omission"]),
    }


def main() -> int:
    r = verify()
    print(f"resplit groups={r['groups']}  SAFE empties={r['safe_empties']}  FLAGGED groups={len(r['flagged'])}")
    print(
        f"completeness: empty-in-base={r['empty_in_base']}  classified={r['classified']}  "
        f"UNCLASSIFIED={len(r['unclassified'])}"
    )
    print(f"deutero_defer={r['deutero_defer']}  legit_omission={r['legit_omission']}")
    if r["flagged"]:
        print("FLAGGED:")
        for empties, terminal, probs in r["flagged"]:
            print(f"  {empties} -> {terminal}")
            for p in probs:
                print(f"    - {p}")
    else:
        print("NO FLAGS — every resplit group mechanically safe & byte-reversible.")
    for c, (b, a) in r["samples"].items():
        print(f"[{c}] BEFORE {b}\n        AFTER  {a}")
    return 1 if (r["flagged"] or r["unclassified"]) else 0


if __name__ == "__main__":
    sys.exit(main())

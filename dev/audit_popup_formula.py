#!/usr/bin/env python3
"""Audit ONE kepub against the popup-footnote formula (no rebuild).

Compares every noteref type to the canonical contract from
docs/superpowers/notes/2026-06-05-eink-epub-compat-research.md §1:
  - same-file forward href
  - ASCII id on aside
  - target 9..5000 stripped chars (Kobo)
  - visible backlink in aside
  - structural parity: working vn-link vs failing vbadge

Usage: py -3 dev/audit_popup_formula.py <path-to.kepub.epub>
       py -3 dev/audit_popup_formula.py <path> --pin gen-1-12 gen-1-1-s7
"""

from __future__ import annotations

import re
import sys
import zipfile
from html import unescape
from pathlib import Path

_ASCII_ID = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]*$")
_NOTEREF_RE = re.compile(
    r'<a\b([^>]*)\bepub:type="noteref"([^>]*)>',
    re.I,
)
_ID_RE = re.compile(r'\bid="([^"]+)"')
_HREF_RE = re.compile(r'\bhref="([^"]*)"')
_CLASS_RE = re.compile(r'\bclass="([^"]*)"')
_ASIDE_RE = re.compile(
    r'<aside\b([^>]*)\bid="([^"]+)"([^>]*)>(.*?)</aside>',
    re.I | re.DOTALL,
)
_BACKLINK_RE = re.compile(r'<a\b[^>]*href="#([^"]+)"', re.I)


def _attrs(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r'(\w+)="([^"]*)"', blob):
        out[m.group(1)] = m.group(2)
    return out


def _strip_len(html: str) -> int:
    t = unescape(re.sub(r"<[^>]+>", "", html))
    return len(re.sub(r"\s+", " ", t).strip())


def _load_pieces(zf: zipfile.ZipFile, pins: list[str] | None = None) -> dict[str, str]:
    """Load split pieces. With pins, only pieces whose raw bytes mention a pin."""
    names = [n for n in zf.namelist() if re.search(r"index_split_\d+(?:_\d+)?\.html$", n)]
    if pins:
        keep: list[str] = []
        for name in names:
            raw = zf.read(name)
            if any(p.encode() in raw for p in pins):
                keep.append(name)
        names = keep or names[:3]  # fallback: first 3 pieces only
    out: dict[str, str] = {}
    for name in names:
        out[name] = zf.read(name).decode("utf-8", "replace")
    return out


def _noterefs(text: str, fname: str) -> list[dict]:
    rows: list[dict] = []
    for m in _NOTEREF_RE.finditer(text):
        blob = m.group(1) + m.group(2)
        a = _attrs(blob)
        rid = a.get("id", "")
        href = a.get("href", "")
        cls = a.get("class", "")
        kind = (
            "vbadge"
            if "verse-notes-badge" in cls
            else "vn-link"
            if "vn-link" in cls
            else "note-ref"
            if "note-ref" in cls
            else "other"
        )
        rows.append({"file": fname, "offset": m.start(), "id": rid, "href": href, "class": cls, "kind": kind})
    return rows


def _aside_index(pieces: dict[str, str]) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for fname, text in pieces.items():
        ids = set(_ID_RE.findall(text))
        for m in _ASIDE_RE.finditer(text):
            blob = m.group(1) + m.group(3)
            a = _attrs(blob)
            if a.get("epub:type") != "footnote":
                continue
            aid = m.group(2)
            inner = m.group(4)
            backs = _BACKLINK_RE.findall(inner)
            idx[aid] = {
                "file": fname,
                "offset": m.start(),
                "class": a.get("class", ""),
                "stripped": _strip_len(inner),
                "serialized": len(m.group(0).encode("utf-8")),
                "backlinks": backs,
                "has_epub_backlink": 'epub:type="backlink"' in inner or "epub:type='backlink'" in inner,
            }
    return idx


def _context(text: str, pos: int, width: int = 120) -> str:
    return re.sub(r"\s+", " ", text[max(0, pos - width) : pos + width])


def _next_vn_link_after(text: str, pos: int) -> str | None:
    m = re.search(r'<a class="vn-link" id="([^"]+)"', text[pos : pos + 400])
    return m.group(1) if m else None


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    path = Path(argv[1])
    pins = [p for p in argv[2:] if p != "--pin"]
    if not path.is_file():
        print(f"missing: {path}")
        return 1

    with zipfile.ZipFile(path) as zf:
        pieces = _load_pieces(zf, pins or None)
    aside_idx = _aside_index(pieces)
    all_refs: list[dict] = []
    for fname, text in pieces.items():
        all_refs.extend(_noterefs(text, fname))

    violations: list[str] = []
    for ref in all_refs:
        href = ref["href"]
        if not href.startswith("#"):
            violations.append(f"PROMOTED {ref['kind']} {ref['id']} → {href} ({ref['file']})")
            continue
        tid = href[1:]
        aside = aside_idx.get(tid)
        file_ids = set(_ID_RE.findall(pieces[ref["file"]]))
        if tid not in file_ids:
            violations.append(f"UNRESOLVED {ref['kind']} {ref['id']} → #{tid} ({ref['file']})")
            continue
        if aside is None:
            violations.append(f"NO_ASIDE {ref['kind']} {ref['id']} → #{tid}")
            continue
        if ref["file"] != aside["file"]:
            violations.append(f"CROSS_FILE {ref['kind']} {ref['id']} in {ref['file']} aside in {aside['file']}")
        if aside["offset"] <= ref["offset"]:
            violations.append(f"BACKWARD {ref['kind']} {ref['id']} @{ref['offset']} aside @{aside['offset']}")
        if not _ASCII_ID.match(tid):
            violations.append(f"NON_ASCII_ID #{tid}")
        if aside["stripped"] < 9:
            violations.append(f"SHORT_TARGET #{tid} stripped={aside['stripped']}")
        if aside["stripped"] > 5000:
            violations.append(f"LONG_TARGET #{tid} stripped={aside['stripped']}")
        if ref["id"] not in aside["backlinks"]:
            violations.append(f"NO_BACKLINK #{tid} ← {ref['id']} (backs={aside['backlinks'][:3]})")

    # Terminal geometry: vbadge immediately before next vn-link (device failure class)
    terminal: list[str] = []
    for fname, text in pieces.items():
        for m in re.finditer(
            r'<a class="verse-notes-badge"[^>]*id="(vbadge-[^"]+)"[^>]*>.*?</a>\s*(?:<span class="badge-trail"[^>]*>.*?</span>\s*)?<a class="vn-link"',
            text,
            re.DOTALL,
        ):
            terminal.append(f"{fname}: {m.group(1)} → next {_next_vn_link_after(text, m.end())}")

    print(f"=== {path.name} ===")
    print(f"pieces={len(pieces)} noterefs={len(all_refs)} footnote_asides={len(aside_idx)}")
    vn = [r for r in all_refs if r["kind"] == "vn-link"]
    vb = [r for r in all_refs if r["kind"] == "vbadge"]
    print(f"vn-link={len(vn)} vbadge={len(vb)} violations={len(violations)} terminal_vbadge={len(terminal)}")

    if violations:
        print("\n-- formula violations (first 20) --")
        for v in violations[:20]:
            print(v)
        if len(violations) > 20:
            print(f"... +{len(violations) - 20} more")

    if terminal:
        print("\n-- terminal vbadge (badge then next vn-link) --")
        for t in terminal[:15]:
            print(t)
        if len(terminal) > 15:
            print(f"... +{len(terminal) - 15} more")

    if pins:
        print("\n-- pinned refs --")
        for pin in pins:
            for ref in all_refs:
                if pin in ref["id"] or pin in ref["href"]:
                    text = pieces[ref["file"]]
                    aside = aside_idx.get(ref["href"].lstrip("#"), {})
                    print(f"\n{pin}:")
                    print(f"  ref: {ref['kind']} id={ref['id']} href={ref['href']} @{ref['offset']}")
                    print(f"  ctx: {_context(text, ref['offset'])}")
                    if aside:
                        print(
                            f"  aside: {aside['file']} @{aside['offset']} stripped={aside['stripped']} B={aside['serialized']} class={aside['class']}"
                        )
                        print(f"  back: {aside['backlinks']}")
                    nxt = _next_vn_link_after(text, ref["offset"])
                    if nxt:
                        print(f"  next_vn-link: {nxt}")

    # Parity: do ALL vn-links pass while failing vbadge shares terminal geometry?
    vn_bad = sum(1 for r in vn if any(r["id"] in v or r["href"] in v for v in violations))
    vb_bad = sum(1 for r in vb if any(r["id"] in v or r["href"] in v for v in violations))
    print(f"\nparity: vn-link violations={vn_bad}/{len(vn)} vbadge violations={vb_bad}/{len(vb)}")
    print(f"terminal vbadge rate: {len(terminal)}/{len(vb) or 1}")

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

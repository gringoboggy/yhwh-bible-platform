#!/usr/bin/env python3
"""Round-15 D8 — canonical book/chapter ORDER of a built EPUB (no rebuild).

The emitted reading flow (OPF spine document order) is never asserted against the
canonical config today. ``enrich_nav_chapters`` (build_edition.py:6656) ``chs.sort()``s
the nav/ncx chapter entries ascending-by-number REGARDLESS of the actual spine document
order, so a reading-flow chapter SWAP (a rewrite pass that reorders pieces) is invisible
in the native ToC AND to ``audit_book_structure`` (which also sorts before checking).
This gate reads the chapter anchors in DOCUMENT order (spine order, then file order) and
asserts the real reading flow is canonical — defeating the sort-masking.

Checks:
  A. CHAPTER ORDER — within each book, the ``ch-bNN-cMM`` anchors appear in strictly
     ascending chapter order in the spine reading flow (a swap → non-ascending → FAIL).
  B. BOOK ORDER — the distinct books, in first-appearance (reading-flow) order, equal the
     books present sorted by canonical ``bp`` index. The appendix books (paz/sus/bel) ship
     at their natural ``bp`` slot after Daniel — the "nav 83 vs spine 86" demotion is a
     NAV-only concept; the spine carries every book in bp order. A reorder → FAIL.
  C. NCX PLAYORDER — the ncx ``playOrder`` values are gapless 1..N (no skipped/duplicated
     step), so the device's linear "next" never jumps.

Imports ``scripts.core.config`` for the canonical ``bp`` index; ``APPENDIX_BOOKS`` mirrors
``build_edition.APPENDIX_BOOKS`` (a drift guard pins the two equal in the test).

Usage:
    py -3 dev/audit_canonical_order.py <epub> [<epub> ...] [--json OUT.json] [--max-show N]
Exit 0 = reading flow is canonical (chapters ascending + books in canonical+demoted order
+ ncx gapless); 1 = any FAIL.
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from dataclasses import dataclass, field

# Mirror of build_edition.APPENDIX_BOOKS (paz=Prayer of Azariah, sus=Susanna, bel=Bel &
# the Dragon — the Greek additions demoted to an appendix after the main canon). Defined
# locally to keep the gate light (no build_edition import); test_audit_canonical_order
# pins it == build_edition.APPENDIX_BOOKS so the two can never drift.
APPENDIX_BOOKS = ("paz", "sus", "bel")

_CH_RE = re.compile(r'id="ch-b(\d+)-c(\d+)"')
_PLAYORDER_RE = re.compile(r'\bplayOrder="(\d+)"')


@dataclass
class OrderResult:
    path: str
    fails: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    @property
    def green(self) -> bool:
        return not self.fails


def _bp_to_code() -> dict[int, str]:
    """Canonical ``bp`` index → book code, from the single config source."""
    from scripts.core import config

    out: dict[int, str] = {}
    for b in config.load_books():
        bp = b.get("bp") or ""
        if bp.startswith("bp-"):
            out[int(bp[3:])] = b["code"]
    return out


def _spine_xhtml(zf: zipfile.ZipFile) -> list[str]:
    """OPF spine xhtml members, in spine (reading) order."""
    names = set(zf.namelist())
    opf_name = next(n for n in names if n.endswith(".opf"))
    opf = zf.read(opf_name).decode("utf-8", "replace")
    opf_dir = opf_name.rsplit("/", 1)[0] if "/" in opf_name else ""
    manifest: dict[str, str] = {}
    for m in re.finditer(r"<item\b[^>]*>", opf):
        idm = re.search(r'\bid="([^"]+)"', m.group(0))
        hrefm = re.search(r'\bhref="([^"]+)"', m.group(0))
        mtm = re.search(r'\bmedia-type="([^"]+)"', m.group(0))
        if idm and hrefm and mtm and mtm.group(1) == "application/xhtml+xml":
            zn = f"{opf_dir}/{hrefm.group(1)}" if opf_dir else hrefm.group(1)
            manifest[idm.group(1)] = zn.lstrip("/")
    spine = [m.group(1) for m in re.finditer(r'<itemref\b[^>]*\bidref="([^"]+)"', opf)]
    return [manifest[i] for i in spine if i in manifest]


def _reading_flow(zf: zipfile.ZipFile, spine: list[str]) -> list[tuple[int, int]]:
    """The (bp, chapter) tuples in DOCUMENT order — spine order, then in-file order.
    Each ``ch-bNN-cMM`` anchor counted ONCE at its first occurrence (a chapter start
    can be referenced again later in the same book without being a re-ordering)."""
    flow: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for n in spine:
        text = zf.read(n).decode("utf-8", "replace")
        for m in _CH_RE.finditer(text):
            key = (int(m.group(1)), int(m.group(2)))
            if key in seen:
                continue
            seen.add(key)
            flow.append(key)
    return flow


def _chapter_order_fails(flow: list[tuple[int, int]], bp2c: dict[int, str]) -> list[str]:
    """Check A — within each book, chapters ascend in document order."""
    fails: list[str] = []
    last_ch: dict[int, int] = {}
    for bp, ch in flow:
        prev = last_ch.get(bp)
        if prev is not None and ch <= prev:
            fails.append(
                f"chapter out of order in {bp2c.get(bp, f'bp-{bp:02d}')}: "
                f"chapter {ch} follows {prev} in the reading flow (a swap the sorted nav masks)"
            )
        last_ch[bp] = ch
    return fails


def _book_order_fails(flow: list[tuple[int, int]], bp2c: dict[int, str]) -> list[str]:
    """Check B — distinct books, in first-appearance (reading-flow) order, equal the books
    present sorted by canonical ``bp`` index. The appendix books (paz/sus/bel) are NOT
    spine-demoted — they ship at their natural ``bp`` slot after Daniel (the "nav 83 vs
    spine 86" demotion is a NAV-only concept; the spine carries every book in bp order).
    A reorder (a book out of bp sequence in the reading flow) → FAIL."""
    actual: list[int] = []
    for bp, _ch in flow:
        if bp not in actual:
            actual.append(bp)
    expected = sorted(set(actual))
    if actual == expected:
        return []
    # Pinpoint the first divergence for a readable failure (lengths can differ — the
    # length-mismatch line below covers that, so strict=False is intentional).
    for i, (a, e) in enumerate(zip(actual, expected, strict=False)):
        if a != e:
            return [
                f"book reading-flow order diverges at position {i}: "
                f"got {bp2c.get(a, f'bp-{a:02d}')} (bp-{a:02d}), "
                f"expected {bp2c.get(e, f'bp-{e:02d}')} (bp-{e:02d}) (books must read in bp order)"
            ]
    return [f"book reading-flow length mismatch: {len(actual)} vs expected {len(expected)}"]


def _ncx_playorder_fails(zf: zipfile.ZipFile) -> list[str]:
    """Check C — ncx playOrder is gapless 1..N (deduped: a target reached twice keeps one
    playOrder, so the DISTINCT sorted set must be a contiguous 1..N run)."""
    names = [n for n in zf.namelist() if n.endswith(".ncx")]
    if not names:
        return []
    text = zf.read(names[0]).decode("utf-8", "replace")
    orders = sorted({int(x) for x in _PLAYORDER_RE.findall(text)})
    if not orders:
        return []  # ncx without playOrder attributes — nothing to check
    expected = list(range(orders[0], orders[0] + len(orders)))
    if orders != expected or orders[0] != 1:
        missing = sorted(set(range(1, orders[-1] + 1)) - set(orders))
        return [f"ncx playOrder not gapless 1..{orders[-1]} (start={orders[0]}, missing={missing[:8]})"]
    return []


def audit_epub(path: str) -> OrderResult:
    res = OrderResult(path=path)
    bp2c = _bp_to_code()
    with zipfile.ZipFile(path) as zf:
        spine = _spine_xhtml(zf)
        if not spine:
            res.fails.append("OPF spine lists no xhtml content documents")
            return res
        flow = _reading_flow(zf, spine)
        if not flow:
            res.warns.append("no ch-bNN-cMM chapter anchors found — order not assertable")
            res.stats = {"spine_pieces": len(spine), "chapters": 0, "books": 0}
            return res
        res.fails.extend(_chapter_order_fails(flow, bp2c))
        res.fails.extend(_book_order_fails(flow, bp2c))
        res.fails.extend(_ncx_playorder_fails(zf))
        books = {bp for bp, _ in flow}
        res.stats = {
            "spine_pieces": len(spine),
            "chapters": len(flow),
            "books": len(books),
            "appendix_books": sum(1 for b in books if bp2c.get(b) in APPENDIX_BOOKS),
        }
    return res


def _print(res: OrderResult, max_show: int) -> None:
    name = res.path.replace("\\", "/").rsplit("/", 1)[-1]
    status = "PASS" if res.green else "FAIL"
    s = res.stats
    print(f"\n=== {name} — D8 canonical-order {status} ===")
    if s:
        print(
            f"  spine_pieces={s.get('spine_pieces', 0)} chapters={s.get('chapters', 0)} "
            f"books={s.get('books', 0)} appendix={s.get('appendix_books', 0)}"
        )
    for f in res.fails[:max_show]:
        print("  ✗", f)
    if len(res.fails) > max_show:
        print(f"  ✗ … +{len(res.fails) - max_show} more FAIL(s)")
    for w in res.warns[:max_show]:
        print("  ⚠", w)


def main(argv: list[str]) -> int:
    _value_flags = ("--json", "--max-show")
    _skip = {argv.index(f) + 1 for f in _value_flags if f in argv}
    paths = [a for i, a in enumerate(argv) if not a.startswith("--") and i not in _skip]
    json_out = argv[argv.index("--json") + 1] if "--json" in argv else None
    max_show = int(argv[argv.index("--max-show") + 1]) if "--max-show" in argv else 50
    if not paths:
        print(__doc__)
        return 2
    results = [audit_epub(p) for p in paths]
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
    print(f"\nTOTAL: {sum(r.green for r in results)}/{len(results)} artifact(s) canonical-order-clean")
    return 1 if any(not r.green for r in results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

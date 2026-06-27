"""Tests for dev/audit_canonical_order.py — gate D8 (canonical book/chapter order).

Synthetic in-memory epubs exercise the three checks the gate adds: a CHAPTER swap
(document order non-ascending within a book), a BOOK swap (reading flow out of bp
order), and an ncx playOrder gap — each of which the sorted nav / sorted
audit_book_structure mask. A drift guard pins APPENDIX_BOOKS == build_edition's.
The real-epub scan is the slow per-build gate (catholic-study eink) + the on-disk
build verification done during round-15 D8.
"""

import importlib.util
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("audit_canonical_order", REPO / "dev" / "audit_canonical_order.py")
aco = importlib.util.module_from_spec(_spec)
sys.modules["audit_canonical_order"] = aco
_spec.loader.exec_module(aco)

_CONTAINER = (
    '<?xml version="1.0"?><container version="1.0" '
    'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
    '<rootfiles><rootfile full-path="content.opf" '
    'media-type="application/oebps-package+xml"/></rootfiles></container>'
)


def _doc(anchors: list[tuple[int, int]]) -> str:
    body = "".join(f'<h2 id="ch-b{bp}-c{ch}">{bp}:{ch}</h2>' for bp, ch in anchors)
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<html xmlns="http://www.w3.org/1999/xhtml"><body>' + body + "</body></html>"
    )


def _make_epub(
    tmp_path: Path, pieces: list[tuple[str, list[tuple[int, int]]]], playorders: list[int] | None = None
) -> str:
    """``pieces`` = ordered [(filename, [(bp, ch), ...])] placed in the spine in that
    order. ``playorders`` = ncx playOrder ints (default a gapless 1..N over the pieces)."""
    manifest = "".join(
        f'<item id="{n.replace(".", "_")}" href="{n}" media-type="application/xhtml+xml"/>' for n, _ in pieces
    )
    manifest += '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
    spine = "".join(f'<itemref idref="{n.replace(".", "_")}"/>' for n, _ in pieces)
    opf = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bid">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bid">urn:x:1</dc:identifier>'
        "<dc:title>t</dc:title><dc:language>en</dc:language></metadata>"
        f'<manifest>{manifest}</manifest><spine toc="ncx">{spine}</spine></package>'
    )
    pos = playorders if playorders is not None else list(range(1, len(pieces) + 1))
    navpoints = "".join(
        f'<navPoint id="np{i}" playOrder="{p}"><navLabel><text>{pieces[i][0]}</text></navLabel>'
        f'<content src="{pieces[i][0]}"/></navPoint>'
        for i, p in enumerate(pos)
    )
    ncx = (
        '<?xml version="1.0"?><ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
        f"<navMap>{navpoints}</navMap></ncx>"
    )
    out = tmp_path / "t.epub"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", _CONTAINER)
        zf.writestr("content.opf", opf)
        zf.writestr("toc.ncx", ncx)
        for n, anchors in pieces:
            zf.writestr(n, _doc(anchors))
    return str(out)


def test_canonical_order_passes(tmp_path):
    """Books in bp order (gen=0, exo=1, lev=2), chapters ascending, ncx gapless → PASS."""
    epub = _make_epub(
        tmp_path,
        [("a.xhtml", [(0, 1), (0, 2), (0, 3)]), ("b.xhtml", [(1, 1), (1, 2)]), ("c.xhtml", [(2, 1)])],
    )
    res = aco.audit_epub(epub)
    assert res.green, res.fails
    assert res.stats["books"] == 3 and res.stats["chapters"] == 6
    assert aco.main([epub]) == 0


def test_chapter_swap_fails(tmp_path):
    """A chapter out of document order within a book (1, 3, 2) → CHECK A FAIL — the swap
    the sorted nav masks."""
    epub = _make_epub(tmp_path, [("a.xhtml", [(0, 1), (0, 3), (0, 2)])])
    res = aco.audit_epub(epub)
    assert not res.green
    assert any("chapter out of order" in f and "chapter 2 follows 3" in f for f in res.fails), res.fails
    assert aco.main([epub]) == 1


def test_book_swap_fails(tmp_path):
    """Books out of bp order in the reading flow (gen, lev, exo) → CHECK B FAIL."""
    epub = _make_epub(tmp_path, [("a.xhtml", [(0, 1)]), ("b.xhtml", [(2, 1)]), ("c.xhtml", [(1, 1)])])
    res = aco.audit_epub(epub)
    assert not res.green
    assert any("book reading-flow order diverges" in f for f in res.fails), res.fails


def test_ncx_playorder_gap_fails(tmp_path):
    """An ncx playOrder gap (1, 2, 4) → CHECK C FAIL (the device 'next' jumps)."""
    epub = _make_epub(
        tmp_path,
        [("a.xhtml", [(0, 1)]), ("b.xhtml", [(1, 1)]), ("c.xhtml", [(2, 1)])],
        playorders=[1, 2, 4],
    )
    res = aco.audit_epub(epub)
    assert not res.green
    assert any("playOrder not gapless" in f for f in res.fails), res.fails


def test_appendix_books_match_build_edition(tmp_path):
    """Drift guard: the gate's local APPENDIX_BOOKS must equal build_edition's (the
    single source) so the demotion model can never silently diverge."""
    from scripts.build_edition import APPENDIX_BOOKS as BE_APPENDIX

    assert aco.APPENDIX_BOOKS == BE_APPENDIX

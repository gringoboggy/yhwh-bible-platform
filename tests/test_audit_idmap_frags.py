"""Tests for dev/audit_idmap_frags.py — gate G3 (idmap / cross-file-link integrity).

Synthetic, in-memory tmp epubs (no real build) exercise the four checks the gate
adds beyond the existing finders:
  * cross-PIECE frag resolution (``A.html#frag`` must resolve against piece A, the
    gap ``audit_book_structure`` leaves by resolving against the GLOBAL id union),
  * noteref/badge/back-link target resolution,
  * cross-piece id-uniqueness,
  * orphaned-spine-piece detection.
The real-epub scan is covered by a ``slow`` test gated on the round-14 fixture.
"""

import importlib.util
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("audit_idmap_frags", REPO / "dev" / "audit_idmap_frags.py")
aif = importlib.util.module_from_spec(_spec)
# Register before exec so the module's @dataclass can resolve its own module (the
# loader leaves sys.modules unset otherwise -> AttributeError on 3.12+/3.14).
sys.modules["audit_idmap_frags"] = aif
_spec.loader.exec_module(aif)

_CONTAINER = (
    '<?xml version="1.0"?><container version="1.0" '
    'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
    '<rootfiles><rootfile full-path="content.opf" '
    'media-type="application/oebps-package+xml"/></rootfiles></container>'
)


def _doc(body: str) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops"><body>' + body + "</body></html>"
    )


def _make_epub(tmp_path: Path, pieces: dict[str, str], spine: list[str]) -> str:
    """Build a minimal valid-enough epub. ``pieces`` = {filename: <body html>}.
    ``spine`` = ordered filenames placed in the spine; the rest are manifest-only
    (to exercise the orphan check). A unique ``pg{i}`` anchor is injected into each
    spine piece so nav/ncx reference a per-piece id (never a shared one — sharing
    would itself trip the cross-piece id-uniqueness check)."""
    anchor = {n: f"pg{i}" for i, n in enumerate(spine)}
    pieces = {n: (f'<span id="{anchor[n]}"></span>{body}' if n in anchor else body) for n, body in pieces.items()}
    nav = _doc(
        '<nav epub:type="toc"><ol><li><a href="' + spine[0] + "#" + anchor[spine[0]] + '">Start</a></li></ol></nav>'
    )
    ncx_items = "".join(
        f'<navPoint id="np{i}"><navLabel><text>{n}</text></navLabel><content src="{n}#{anchor[n]}"/></navPoint>'
        for i, n in enumerate(spine)
    )
    ncx = (
        '<?xml version="1.0"?><ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
        f"<navMap>{ncx_items}</navMap></ncx>"
    )
    manifest_items = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>']
    manifest_items.append('<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
    for n in list(pieces):
        iid = n.replace(".", "_")
        manifest_items.append(f'<item id="{iid}" href="{n}" media-type="application/xhtml+xml"/>')
    spine_items = "".join(f'<itemref idref="{n.replace(".", "_")}"/>' for n in spine)
    opf = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bid">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bid">urn:x:1</dc:identifier>'
        "<dc:title>t</dc:title><dc:language>en</dc:language></metadata>"
        f"<manifest>{''.join(manifest_items)}</manifest>"
        f'<spine toc="ncx">{spine_items}</spine></package>'
    )
    out = tmp_path / "t.epub"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", _CONTAINER)
        zf.writestr("content.opf", opf)
        zf.writestr("nav.xhtml", nav)
        zf.writestr("toc.ncx", ncx)
        for n, body in pieces.items():
            zf.writestr(n, _doc(body))
    return str(out)


def test_two_piece_pass(tmp_path):
    """(a) A clean 2-piece split: cross-file links, a noteref->aside, and the aside
    back-link all resolve; ids unique; no orphan -> green / exit 0."""
    a = (
        '<p id="secA"></p>'
        '<a href="b.html#secB">to B</a>'
        '<a epub:type="noteref" class="vn-link" id="ref1" href="b.html#note1">*</a>'
    )
    b = (
        '<p id="secB"></p>'
        '<a href="a.html#secA">back to A</a>'
        '<aside epub:type="footnote" id="note1"><a epub:type="backlink" href="a.html#ref1">^</a> note</aside>'
    )
    epub = _make_epub(tmp_path, {"a.html": a, "b.html": b}, ["a.html", "b.html"])
    res = aif.audit_epub(epub)
    assert res.green, res.fails
    assert res.stats["duplicate_ids"] == 0
    assert aif.main([epub]) == 0


def test_dangling_cross_file_frag_fails(tmp_path):
    """(b) A cross-file href whose frag lives in NO piece (``ghost``) AND the
    wrong-piece case whose frag lives in a DIFFERENT piece than the one named
    (``secA`` is in a.html, but the link names b.html) must both FAIL — the exact
    gap audit_book_structure's global-union resolution misses."""
    a = (
        '<p id="secA"></p>'  # secA lives in piece a only
        '<a href="b.html#ghost">dead link</a>'  # ghost exists nowhere
        '<a href="b.html#secA">wrong piece</a>'  # named piece b does NOT hold secA
    )
    b = '<p id="secB"></p>'
    epub = _make_epub(tmp_path, {"a.html": a, "b.html": b}, ["a.html", "b.html"])
    res = aif.audit_epub(epub)
    assert not res.green
    joined = "\n".join(res.fails)
    assert "ghost" in joined and "no id" in joined, joined
    assert 'no id "secA" in target piece b.html' in joined, "wrong-piece cross-file link must fail: " + joined
    assert aif.main([epub]) == 1


def test_duplicate_id_across_pieces_fails(tmp_path):
    """(c) The same id in two spine pieces makes the idmap ambiguous -> FAIL."""
    a = '<p id="dup"></p>'
    b = '<p id="dup"></p>'  # same id in a second piece
    epub = _make_epub(tmp_path, {"a.html": a, "b.html": b}, ["a.html", "b.html"])
    res = aif.audit_epub(epub)
    assert not res.green
    assert any('duplicate id "dup"' in f for f in res.fails), res.fails
    assert res.stats["duplicate_ids"] == 1


def test_bare_same_file_frag_fails(tmp_path):
    """A bare ``#frag`` with no matching id in its own file must FAIL."""
    a = '<a href="#nope">bad</a>'
    epub = _make_epub(tmp_path, {"a.html": a}, ["a.html"])
    res = aif.audit_epub(epub)
    assert not res.green
    assert any("no id" in f and "same file" in f for f in res.fails), res.fails


def test_orphan_spine_piece_fails(tmp_path):
    """An xhtml manifest item not referenced by the spine is an orphan -> FAIL
    (the nav doc is exempt; that exemption is proven by the PASS test)."""
    a = "<p>a</p>"
    orphan = "<p>unreachable</p>"
    epub = _make_epub(tmp_path, {"a.html": a, "orphan.html": orphan}, ["a.html"])
    res = aif.audit_epub(epub)
    assert not res.green
    assert any("orphan" in f and "orphan.html" in f for f in res.fails), res.fails


def test_noteref_target_miss_labelled(tmp_path):
    """A noteref whose target is missing is counted as a noteref failure (check 2),
    distinct from a plain link failure."""
    a = '<a epub:type="noteref" class="vn-link" id="r1" href="b.html#gone">*</a>'
    b = "<p>b</p>"
    epub = _make_epub(tmp_path, {"a.html": a, "b.html": b}, ["a.html", "b.html"])
    res = aif.audit_epub(epub)
    assert not res.green
    assert res.stats["noteref_fails"] >= 1, res.stats


def test_presence_floor_guards_wholesale_xref_loss(tmp_path):
    """round-15 D2: every other check only flags a link that FAILS to resolve, so a
    build that dropped ALL its xref/noteref anchors would pass G3 vacuously (0 links →
    0 fails → green). ``--min-links`` requires a minimum surviving frag+noteref count
    so wholesale loss FAILS. Off (0) by default → backward-compatible."""
    a = (
        '<p id="secA"></p>'
        '<a href="b.html#secB">to B</a>'
        '<a epub:type="noteref" class="vn-link" id="ref1" href="b.html#note1">*</a>'
    )
    b = '<p id="secB"></p><aside epub:type="footnote" id="note1">n</aside>'
    epub = _make_epub(tmp_path, {"a.html": a, "b.html": b}, ["a.html", "b.html"])
    # All links resolve → green when the floor is OFF (default) ...
    assert aif.audit_epub(epub, min_links=0).green
    # ... but a floor above this epub's tiny (2) link count FAILS the gate.
    res = aif.audit_epub(epub, min_links=1000)
    assert not res.green
    assert any("presence floor" in f for f in res.fails), res.fails
    assert aif.main([epub, "--min-links", "1000"]) == 1


def test_xref_class_broken_out(tmp_path):
    """round-15 D2: a NON-noteref link whose target is a scripture ``v-``/``ch-`` anchor is
    counted in its own ``xref_links`` bucket (a subset of ``frag_links``), and a DEAD one is
    bucketed as an ``xref_fails`` finding — so scripture cross-references are visible, distinct
    from the noteref popup bulk and from plain front/back-matter links."""
    a = (
        '<a href="b.html#v-gen-2-1">cf 2:1</a>'  # xref (resolves)
        '<a href="b.html#ch-b00-c2">ch 2</a>'  # xref (resolves)
        '<a href="b.html#secB">plain</a>'  # plain (resolves, not v-/ch-)
        '<a epub:type="noteref" class="vn-link" id="r1" href="b.html#note1">*</a>'  # noteref
        '<a href="b.html#v-gen-9-9">cf 9:9</a>'  # DEAD xref (no target)
    )
    b = '<p id="v-gen-2-1"></p><a id="ch-b00-c2"></a><p id="secB"></p><aside epub:type="footnote" id="note1">n</aside>'
    epub = _make_epub(tmp_path, {"a.html": a, "b.html": b}, ["a.html", "b.html"])
    res = aif.audit_epub(epub)
    # three v-/ch- xref anchors counted (2 live + 1 dead); the noteref is NOT an xref.
    assert res.stats["xref_links"] == 3, res.stats
    assert res.stats["noteref_links"] == 1, res.stats
    assert res.stats["xref_links"] <= res.stats["frag_links"]  # xref is a subset of all non-noteref
    # the dead xref is bucketed as an xref failure (not a plain link / noteref failure)...
    assert res.stats["xref_fails"] == 1, res.stats
    assert res.stats["noteref_fails"] == 0, res.stats
    assert any("v-gen-9-9" in f for f in res.fails), res.fails
    assert not res.green


def test_xref_floor_catches_loss_hidden_by_noteref_bulk(tmp_path):
    """round-15 D2: the dedicated ``--min-xrefs`` floor catches a wholesale scripture-xref
    loss that the ``--min-links`` floor would miss, because the (here plentiful) noteref bulk
    keeps the frag+noteref total above ``--min-links`` even when zero scripture xrefs survive."""
    a = "".join(f'<a epub:type="noteref" class="vn-link" id="r{i}" href="b.html#n{i}">*</a>' for i in range(5))
    b = "".join(f'<aside epub:type="footnote" id="n{i}">x</aside>' for i in range(5))
    epub = _make_epub(tmp_path, {"a.html": a, "b.html": b}, ["a.html", "b.html"])
    base = aif.audit_epub(epub)
    assert base.stats["xref_links"] == 0 and base.stats["noteref_links"] == 5, base.stats
    # --min-links is satisfied (5 noterefs + nav link >> 2) → green despite ZERO scripture xrefs ...
    assert aif.audit_epub(epub, min_links=2).green
    # ... but the dedicated xref floor FAILS on the wholesale scripture-xref loss.
    res = aif.audit_epub(epub, min_links=2, min_xrefs=1)
    assert not res.green
    assert any("xref floor" in f for f in res.fails), res.fails
    assert aif.main([epub, "--min-xrefs", "1"]) == 1


# ── real-data fixture (round-14 catholic-study eink epub) — gated slow ──────────
_REAL_GLOBS = [
    Path(r"C:\Users\bogda\YHWH-builds\round14-postA1"),
    Path(r"C:\Users\bogda\YHWH-builds"),
]


def _find_real_epub() -> str | None:
    for root in _REAL_GLOBS:
        if root.is_dir():
            hits = sorted(root.glob("**/*catholic-study*eink*.epub"))
            if hits:
                return str(hits[0])
    return None


@pytest.mark.slow
def test_real_catholic_eink_epub_is_idmap_clean():
    epub = _find_real_epub()
    if not epub:
        pytest.skip("no round-14 catholic-study eink epub on disk")
    res = aif.audit_epub(epub)
    assert res.green, "\n".join(res.fails[:50])

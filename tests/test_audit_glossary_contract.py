"""Tests for gate G5 — the study-glossary format-contract validator (dev/audit_glossary_contract.py).

Fast synthetic cases build tiny in-memory EPUBs (a zip of glossary pieces) and run the gate
with a small ``cap`` so the contract logic is exercised without 400 KB of data or a real build:
  (a) PASS — pieces under cap, one book-head each, atoms conserved.
  (b) FAIL — a piece over the cap (the Kobo navigate-cap bust, dim A5 / P3).
  (c) FAIL — two book-heads in one split piece.
  (d) FAIL — atom-count mismatch (an entry id duplicated across pieces).
Plus the opt-in reference-split (str==from-file partition) proof on synthetic data, and a
``slow`` smoke against the real round14 study eink build.
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import pytest

import dev.audit_glossary_contract as g

STEM = g.GLOSSARY_STEM


# --------------------------------------------------------------------------- fixtures
def _entry(vid: str, body_chars: int = 200) -> str:
    return (
        f'<div class="study-glossary-entry" id="{vid}">\n'
        f'<aside epub:type="footnote" class="study-glossary-cat verse-notes" id="{vid}-comm">'
        f"<p>{'n' * body_chars}</p></aside>\n</div>\n"
    )


def _bookhead(bid: str, label: str = "Book") -> str:
    return f'<h2 class="study-book-head" id="{bid}">{label}</h2>\n'


def _piece(inner: str) -> str:
    """Wrap glossary inner exactly like a built piece (head + body + study-notes-index + tail)."""
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">\n'
        "<head><title>Study Notes</title></head>\n"
        '<body epub:type="backmatter">\n'
        '<section class="study-notes-index" epub:type="backmatter">'
        f"{inner}"
        "</section>\n</body>\n</html>\n"
    )


def _make_epub(tmp_path: Path, pieces: dict[str, str], name: str = "synthetic.epub") -> str:
    """Zip the named glossary pieces (each value is full piece HTML) into a minimal EPUB."""
    path = tmp_path / name
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", "<container/>")
        for piece_name, html in pieces.items():
            zf.writestr(f"OEBPS/{piece_name}", html)
    path.write_bytes(buf.getvalue())
    return str(path)


def _three_book_pieces() -> dict[str, str]:
    """An intro piece + three single-book pieces, each under a small cap, atoms unique."""
    intro = _piece('<h1>Study Notes</h1><p class="study-notes-lead">lead</p>')
    pieces = {f"{STEM}_00.html": intro}
    for i in range(1, 4):
        inner = _bookhead(f"study-b{i}", f"Book {i}") + "".join(_entry(f"study-entry-b{i}-1-{j}") for j in range(1, 4))
        pieces[f"{STEM}_0{i}.html"] = _piece(inner)
    return pieces


# --------------------------------------------------------------------------- cases
def test_pass_under_cap_one_bookhead_atoms_conserved(tmp_path):
    """(a) PASS — every piece under cap, one book-head each, no duplicate atoms."""
    path = _make_epub(tmp_path, _three_book_pieces())
    res = g.audit_epub(path, cap=5_000)
    assert res.green, res.fails
    assert res.stats["pieces"] == 4
    assert res.stats["over_cap"] == 0
    assert res.stats["multi_bookhead_pieces"] == 0
    assert res.stats["total_atoms"] == 9
    assert res.stats["distinct_atom_ids"] == 9


def test_fail_piece_over_cap(tmp_path):
    """(b) FAIL — one piece's inner exceeds the cap (Kobo navigate bust)."""
    pieces = _three_book_pieces()
    # bloat book-2's single entry well past a 5_000-cp cap
    big_inner = _bookhead("study-b2", "Book 2") + _entry("study-entry-b2-1-1", body_chars=6_000)
    pieces[f"{STEM}_02.html"] = _piece(big_inner)
    path = _make_epub(tmp_path, pieces)
    res = g.audit_epub(path, cap=5_000)
    assert not res.green
    assert res.stats["over_cap"] == 1
    assert any("busts the Kobo navigate cap" in f for f in res.fails)


def test_fail_two_bookheads_in_one_piece(tmp_path):
    """(c) FAIL — a split piece packs two book-heads."""
    pieces = _three_book_pieces()
    two_heads = (
        _bookhead("study-b2", "Book 2")
        + _entry("study-entry-b2-1-1")
        + _bookhead("study-b9", "Book 9")
        + _entry("study-entry-b9-1-1")
    )
    pieces[f"{STEM}_02.html"] = _piece(two_heads)
    path = _make_epub(tmp_path, pieces)
    res = g.audit_epub(path, cap=5_000)
    assert not res.green
    assert res.stats["multi_bookhead_pieces"] == 1
    assert any("holds one book max" in f for f in res.fails)


def test_fail_atom_count_mismatch_duplicate_id(tmp_path):
    """(d) FAIL — an entry id is duplicated across two pieces (streaming split dup'd an atom)."""
    pieces = _three_book_pieces()
    # piece _03 re-emits an atom id that already lives in piece _01
    dup_inner = _bookhead("study-b3", "Book 3") + _entry("study-entry-b1-1-1") + _entry("study-entry-b3-1-9")
    pieces[f"{STEM}_03.html"] = _piece(dup_inner)
    path = _make_epub(tmp_path, pieces)
    res = g.audit_epub(path, cap=5_000)
    assert not res.green
    assert res.stats["duplicate_atom_ids"] == 1
    # conservation invariant broken: more atom divs than distinct ids
    assert res.stats["total_atoms"] > res.stats["distinct_atom_ids"]
    assert any("duplicated an atom" in f for f in res.fails)


def test_fail_entry_without_id(tmp_path):
    """An entry div with no id is untargetable — flagged as a dropped-from-nav atom."""
    pieces = _three_book_pieces()
    no_id = _bookhead("study-b3", "Book 3") + '<div class="study-glossary-entry">\n<p>x</p>\n</div>\n'
    pieces[f"{STEM}_03.html"] = _piece(no_id)
    path = _make_epub(tmp_path, pieces)
    res = g.audit_epub(path, cap=5_000)
    assert not res.green
    assert res.stats["missing_atom_ids"] == 1
    assert any("without an id" in f for f in res.fails)


def test_no_glossary_pieces_fails(tmp_path):
    path = _make_epub(tmp_path, {"some_other.html": _piece("<p>not a glossary</p>")})
    res = g.audit_epub(path, cap=5_000)
    assert not res.green
    assert any("no glossary pieces" in f for f in res.fails)


def test_unsplit_single_piece_exempt_from_one_book_rule(tmp_path):
    """The bare ``<stem>.html`` (a glossary that fit in one piece) may hold every book head."""
    inner = (
        "<h1>Study Notes</h1>"
        + _bookhead("study-b1", "Book 1")
        + _entry("study-entry-b1-1-1")
        + _bookhead("study-b2", "Book 2")
        + _entry("study-entry-b2-1-1")
    )
    path = _make_epub(tmp_path, {f"{STEM}.html": _piece(inner)})
    res = g.audit_epub(path, cap=50_000)
    assert res.green, res.fails
    assert res.stats["split_pieces"] == 0
    assert res.stats["total_book_heads"] == 2


def _real_glossary_text(n_books: int = 6, asides_per_book: int = 40) -> str:
    """A glossary monolith whose entries carry UNIQUE ids (one per verse) so the real
    reference splitter output also satisfies the gate's atom-id-uniqueness invariant."""
    books = []
    for i in range(n_books):
        asides = "".join(
            f'<div class="study-glossary-entry" id="study-entry-b{i}-1-{j}">'
            '<aside epub:type="footnote" class="study-glossary-cat verse-notes" '
            f'id="study-entry-b{i}-1-{j}-comm"><p>note</p></aside></div>\n'
            for j in range(asides_per_book)
        )
        books.append(f'<h2 class="study-book-head" id="study-b{i}">Book {i}</h2>' + asides)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Study Notes</title></head>\n'
        '<body epub:type="backmatter">\n'
        '<section class="study-notes-index" epub:type="backmatter">\n'
        f'<h1>Study Notes</h1><p class="study-notes-lead">lead</p>\n{"".join(books)}\n</section>\n</body></html>'
    )


def test_reference_split_pass_on_real_splitter_output(tmp_path):
    """Opt-in check 4 — pieces produced by the real reference splitter pass reference-equality."""
    be = pytest.importorskip("scripts.build_edition")
    cap = 8_000
    pieces = be.split_study_glossary_document(_real_glossary_text(), STEM, cap)
    assert len(pieces) > 1
    path = _make_epub(tmp_path, dict(pieces))
    res = g.audit_epub(path, cap=cap, reference_split=True)
    assert res.green, res.fails
    # and the cheap checks agree the build is clean
    assert res.stats["over_cap"] == 0
    assert res.stats["multi_bookhead_pieces"] == 0
    assert res.stats["total_atoms"] == res.stats["distinct_atom_ids"]


def test_reference_split_detects_tampered_partition(tmp_path):
    """Opt-in check 4 catches a partition the reference splitter would NOT produce — here a
    single atom deleted from one piece, which the cheap checks (cap / book-head / dup-id)
    cannot see but which shifts every downstream reference boundary."""
    be = pytest.importorskip("scripts.build_edition")
    cap = 8_000
    # 80 asides/book pushes each book past the cap → a book spans several entry-split pieces,
    # so deleting one atom from a non-final piece of a book shifts every downstream boundary.
    pieces = dict(be.split_study_glossary_document(_real_glossary_text(n_books=3, asides_per_book=80), STEM, cap))
    assert len(pieces) > 3
    ordered = sorted(pieces, key=lambda n: int(re.search(r"_(\d+)\.html", n).group(1)))
    # delete ONE entry atom from an early content piece (not the intro) → reconstruction is
    # short one atom → the reference repartition diverges from that piece onward.
    victim = ordered[1]
    pieces[victim] = re.sub(r'<div class="study-glossary-entry".*?</div>\n', "", pieces[victim], count=1, flags=re.S)
    path = _make_epub(tmp_path, pieces)
    # the cheap checks alone do NOT catch a clean single-atom deletion...
    assert g.audit_epub(path, cap=cap).green
    # ...but the reference-partition proof does.
    res = g.audit_epub(path, cap=cap, reference_split=True)
    assert not res.green
    assert any("reference" in f.lower() or "diverges" in f.lower() for f in res.fails)


@pytest.mark.slow
def test_real_round14_study_eink_build(tmp_path):
    """Smoke against the real built catholic-study eink epub (no rebuild). Confirms the gate
    runs end-to-end and its stats are self-consistent; records the live cap-bust count."""
    candidates = sorted(Path("C:/Users/bogda/YHWH-builds").glob("**/*catholic-study*eink*.epub"))
    candidates = [c for c in candidates if "kepub" not in c.name.lower()]
    if not candidates:
        pytest.skip("no built study eink epub available")
    res = g.audit_epub(str(candidates[-1]))
    assert res.stats["pieces"] > 1
    # internal consistency: with no duplicate ids, atoms == distinct ids
    if res.stats["duplicate_atom_ids"] == 0 and res.stats["missing_atom_ids"] == 0:
        assert res.stats["total_atoms"] == res.stats["distinct_atom_ids"]
    # the gate either passes or reports concrete offending pieces — never crashes
    assert isinstance(res.green, bool)

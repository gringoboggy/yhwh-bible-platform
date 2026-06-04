"""Regression: canon book-splice must not orphan footnotes.

Each split file has ONE per-file notes-section (shared by every book in the
file) at its end, which falls inside the LAST book's `_BOOK_SEGMENT_RE`
segment (it runs to `</body>`). When the last book is dropped by a smaller
canon, that segment used to swallow the shared notes-section — taking KEPT
books' asides with it while their inline markers survived → orphaned
note-ref markers (`href="#note-X"` with no `id="note-X"`), which epubcheck
flags RSC-012. Conversely a dropped book's own aside, left behind, dangles.

Fix: segments stop at the shared notes/verse-refs sections (preserve kept
asides), then a reconciliation drops asides whose marker was spliced out.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts import build_edition  # noqa: E402

_DOC = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><body>'
    '<div class="book-title-page" id="bp-1">Book A</div>'
    '<p>A 1:1 <a class="note-ref note-comm" id="ref-a0101" href="#note-a0101" epub:type="noteref"><sup>x</sup></a></p>'
    '<div class="book-title-page" id="bp-2">Book B</div>'
    '<p>B 1:1 <a class="note-ref note-comm" id="ref-b0101" href="#note-b0101" epub:type="noteref"><sup>x</sup></a></p>'
    '<aside class="notes-section" epub:type="footnotes" hidden="">'
    '<aside class="note note-comm" id="note-a0101" epub:type="footnote"><p><a href="#ref-a0101" class="note-back">x</a> A note</p></aside>'
    '<aside class="note note-comm" id="note-b0101" epub:type="footnote"><p><a href="#ref-b0101" class="note-back">x</a> B note</p></aside>'
    "</aside>"
    "</body></html>"
)

_ALL_BOOKS = [
    {"code": "a", "bp": "bp-1", "files": ["index_split_000.html"]},
    {"code": "b", "bp": "bp-2", "files": ["index_split_000.html"]},
]


def test_canon_splice_preserves_kept_aside_and_drops_orphaned_one(tmp_path):
    (tmp_path / "index_split_000.html").write_text(_DOC, encoding="utf-8")
    # Drop the LAST book (B); keep A. A's aside lives in the shared trailing
    # notes-section that B's segment used to swallow.
    build_edition.filter_books_for_canon(tmp_path, {"a"}, _ALL_BOOKS)
    out = (tmp_path / "index_split_000.html").read_text(encoding="utf-8")

    # Kept book A: marker AND its aside both survive (no orphaned marker).
    assert 'href="#note-a0101"' in out, "kept book A's marker was lost"
    assert 'id="note-a0101"' in out, "kept book A's aside was swallowed by B's dropped segment"

    # Dropped book B: scripture/marker gone, and its now-orphaned aside removed.
    assert 'id="ref-b0101"' not in out, "dropped book B's marker should be spliced out"
    assert 'id="note-b0101"' not in out, "dropped book B's orphaned aside should be reconciled away"


# --- σ.1.2 leading-spillover guard (a multi-file book's continuation that
# precedes the first book-title-page in a split file). The original 2es/Tobit
# leak: 2es chapters 7-16 shared index_split_026.html with kept Tobit but had
# no title page there, so they shipped as orphan markers in canons that drop
# 2es. The guard strips that leading region ONLY when every chapter-anchor
# prefix in it maps to a dropped book. ---

_SPILL_DOC = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><body>'
    # Leading region: book A's continuation (no title page in THIS file)
    '<a id="ch-b00-c7" class="ch-anchor"></a>'
    '<p>A 7:1 <a class="note-ref note-comm" id="ref-a0701" href="#note-a0701" epub:type="noteref"><sup>x</sup></a></p>'
    # First title page in this file = book B
    '<div class="book-title-page" id="bp-2">Book B</div>'
    "<p>B 1:1 text</p>"
    '<aside class="notes-section" epub:type="footnotes" hidden="">'
    '<aside class="note note-comm" id="note-a0701" epub:type="footnote"><p><a href="#ref-a0701" class="note-back">x</a> A note</p></aside>'
    "</aside>"
    "</body></html>"
)

# Book A is multi-file (continues into this file); its prefix b00 maps to "a".
_SPILL_ALL_BOOKS = [
    {"code": "a", "bxx": "b00", "bp": "bp-1", "files": ["index_split_025.html", "index_split_026.html"]},
    {"code": "b", "bxx": "b01", "bp": "bp-2", "files": ["index_split_026.html"]},
]


def test_leading_spillover_stripped_when_all_lead_books_dropped(tmp_path):
    """Keep B, drop A → A's leading continuation (anchors + markers + orphaned
    aside) is stripped from the file even though no book-title-page precedes it."""
    (tmp_path / "index_split_026.html").write_text(_SPILL_DOC, encoding="utf-8")
    build_edition.filter_books_for_canon(tmp_path, {"b"}, _SPILL_ALL_BOOKS)
    out = (tmp_path / "index_split_026.html").read_text(encoding="utf-8")
    assert "ch-b00-c7" not in out, "dropped book A's leading chapter anchor should be stripped"
    assert 'id="ref-a0701"' not in out, "dropped book A's leading note-ref marker should be stripped"
    assert 'id="note-a0701"' not in out, "dropped book A's orphaned aside should be reconciled away"
    assert 'id="bp-2"' in out, "kept book B's title page must remain"


def test_leading_spillover_preserved_when_lead_book_is_kept(tmp_path):
    """Keep A, drop B → A's leading continuation must be preserved (the guard is
    conservative: it only strips a leading region whose books are ALL dropped)."""
    (tmp_path / "index_split_026.html").write_text(_SPILL_DOC, encoding="utf-8")
    build_edition.filter_books_for_canon(tmp_path, {"a"}, _SPILL_ALL_BOOKS)
    out = (tmp_path / "index_split_026.html").read_text(encoding="utf-8")
    assert "ch-b00-c7" in out, "kept book A's leading spillover must be preserved"
    assert 'id="ref-a0701"' in out, "kept book A's leading marker must be preserved"


def test_patch_opf_bisac_subject_pairs_authority_and_term():
    """epubcheck RSC-005: a BISAC ``dc:subject`` carrying ``property="authority"``
    must ALSO carry a paired ``property="term"`` refining the same id — else
    'A term property must be associated with a dc:subject when an authority is
    specified'. patch_opf emitted authority without term (catholic/anglican)."""
    opf = (
        "<?xml version='1.0'?>\n"
        '<package version="3.0">\n'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        '<dc:title>X</dc:title><dc:creator id="creator">Public Domain</dc:creator>\n'
        '<meta refines="#creator" property="role" scheme="marc:relators">aut</meta>\n'
        '<meta refines="#creator" property="file-as">Public Domain</meta>\n'
        "<dc:date>2020-01-01</dc:date><dc:language>en</dc:language>\n"
        "</metadata></package>"
    )
    edition = {"id": "cat", "title": "X", "bisac_codes": ["REL006150"]}
    out = build_edition.patch_opf(opf, edition, "v1")
    assert '<dc:subject id="bisac-REL006150">' in out
    assert '<meta refines="#bisac-REL006150" property="authority">BISAC</meta>' in out
    assert '<meta refines="#bisac-REL006150" property="term">REL006150</meta>' in out, (
        "BISAC subject is missing the paired property='term' meta (epubcheck RSC-005)"
    )

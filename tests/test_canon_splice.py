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

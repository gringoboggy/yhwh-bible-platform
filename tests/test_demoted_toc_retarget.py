"""K-KIN husk fix, organ #2 — retarget demoted-book TOC entries to content.

The Previewer oracle proved the E24010 target condition is the demoted
``appendix-section`` frame TAG itself, not just the empty husk piece: with
the frame merged into a content-bearing piece (the splitter fix), conversion
STILL failed E24010 ×1 + W14001 ×3 on ``#bp-45/46/47`` — KFX prunes/refuses
the frame div as a TOC link target in BOTH layouts (its leading children are
display:none). Every other anchor class in the book resolves (43k links), so
the fix is the design direction from the handoff: rewrite the nav.xhtml /
toc.ncx / in-book-TOC fragments for each demoted book from ``#bp-NN`` to the
book's FIRST CONTENT ANCHOR (chapter anchor / heading id / verse id — all
plainly visible). Runs pre-split; the splitter's link remap carries the new
fragments to the final pieces.
"""

from __future__ import annotations

import sys
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


PAZ_FILE = "index_split_047.html"  # registry: paz -> bp-45 in this file

PAZ_DOC = (
    "<?xml version='1.0' encoding='utf-8'?>\n"
    "<html><body>\n"
    '<p class="verse-p"><a class="vn-link" id="v-dan-12-13" href="#vnote-dan-12-13" '
    'epub:type="noteref"><span class="vn">13</span></a> Daniel tail.</p>\n'
    '<div class="appendix-section" id="bp-45"><div class="book-title-frame">'
    '<p class="bookpage-eyebrow">BOOK XLV</p>'
    '<h1 class="bookpage-title">The Prayer of Azariah</h1></div></div>\n'
    '<a id="ch-b45-c1" class="ch-anchor"></a>'
    '<p id="page_200" class="ch-heading"><span class="bold-num">1</span></p>\n'
    '<p class="verse-p"><a class="vn-link" id="v-paz-1-1" href="#vnote-paz-1-1" '
    'epub:type="noteref"><span class="vn">1</span></a> And they walked in the fire.</p>\n'
    "</body></html>"
)

NAV_DOC = (
    '<html xmlns:epub="http://www.idpf.org/2007/ops"><body><nav epub:type="toc"><ol>\n'
    f'<li><a href="{PAZ_FILE}#bp-45">The Prayer of Azariah</a></li>\n'
    '<li><a href="index_split_001.html#bp-07">Ruth</a></li>\n'
    "</ol></nav></body></html>"
)

NCX_DOC = (
    "<ncx><navMap>"
    '<navPoint id="n1" playOrder="1"><navLabel><text>Azariah</text></navLabel>'
    f'<content src="{PAZ_FILE}#bp-45"/></navPoint>'
    '<navPoint id="n2" playOrder="2"><navLabel><text>Ruth</text></navLabel>'
    '<content src="index_split_001.html#bp-07"/></navPoint>'
    "</navMap></ncx>"
)

TOC_PAGE = (
    "<html><body><ol>"
    '<li class="toc-book">'
    f'<p class="toc-book-label"><a href="{PAZ_FILE}#bp-45">The Prayer of Azariah</a></p>'
    "</li>"
    '<li class="toc-book">'
    '<p class="toc-book-label"><a href="index_split_001.html#bp-07">Ruth</a></p>'
    "</li>"
    "</ol></body></html>"
)


def _tree(tmp_path):
    tmp = tmp_path / "build"
    tmp.mkdir()
    (tmp / PAZ_FILE).write_text(PAZ_DOC, encoding="utf-8")
    (tmp / "index_split_000.html").write_text(TOC_PAGE, encoding="utf-8")
    (tmp / "nav.xhtml").write_text(NAV_DOC, encoding="utf-8")
    (tmp / "toc.ncx").write_text(NCX_DOC, encoding="utf-8")
    return tmp


class TestRetargetDemotedTocAnchors:
    def _run(self, tmp_path, canon=None):
        from scripts.build_edition import retarget_demoted_toc_anchors

        tmp = _tree(tmp_path)
        stats = retarget_demoted_toc_anchors(tmp, canon)
        return tmp, stats

    def test_all_three_toc_surfaces_point_at_first_content_anchor(self, tmp_path):
        tmp, stats = self._run(tmp_path)
        assert stats["retargeted_books"] == 1  # only paz is present in this tree
        for f in ("nav.xhtml", "toc.ncx", "index_split_000.html"):
            t = (tmp / f).read_text(encoding="utf-8")
            assert "#bp-45" not in t, f"{f} still targets the demoted frame (the E24010 class)"
            assert f"{PAZ_FILE}#ch-b45-c1" in t, f"{f} must target the first content anchor"

    def test_other_books_entries_untouched(self, tmp_path):
        tmp, _ = self._run(tmp_path)
        for f in ("nav.xhtml", "toc.ncx", "index_split_000.html"):
            t = (tmp / f).read_text(encoding="utf-8")
            assert "index_split_001.html#bp-07" in t, f"{f}: real book-title target must survive"

    def test_content_file_and_frame_ids_unchanged(self, tmp_path):
        # only TOC SURFACES are rewritten — the frame keeps its bp id (xref
        # coordinates stay canonical) and the content doc is untouched.
        tmp, _ = self._run(tmp_path)
        assert (tmp / PAZ_FILE).read_text(encoding="utf-8") == PAZ_DOC

    def test_canon_filter_excludes_absent_books(self, tmp_path):
        tmp, stats = self._run(tmp_path, canon={"gen", "rut"})  # paz filtered out
        assert stats["retargeted_books"] == 0
        assert "#bp-45" in (tmp / "nav.xhtml").read_text(encoding="utf-8")

"""K-R10 nav/ToC short titles — pin the `toc_title` data + the build step that applies it.

The Kobo native ToC truncates a long book label to a `[+]` expander. `build_edition.
apply_nav_toc_short_titles` shortens nav.xhtml + toc.ncx labels from a `toc_title` field in
books.yaml (the full `title` still shows on the book page). The device-QA on 2026-06-24 found
"The Prayer of Azariah and the Song of the Three Holy Children" had reverted to the long form
(→ `[+]`); the `paz` record had lost its `toc_title`. These pins keep it from reverting again.
"""

from pathlib import Path

from scripts import build_edition as be
from scripts.core import config

REPO = Path(__file__).resolve().parent.parent

_PAZ_FULL = "The Prayer of Azariah and the Song of the Three Holy Children"
_PAZ_SHORT = "Prayer of Azariah"


class TestTocTitleData:
    def test_paz_has_short_toc_title(self):
        books = {b["code"]: b for b in config.load_books()}
        paz = books["paz"]
        assert paz.get("toc_title") == _PAZ_SHORT
        assert paz["title"] == _PAZ_FULL  # full title still shows on the book page
        assert paz["toc_title"] != paz["title"]  # but the nav label is the short form


class TestApplyNavTocShortTitles:
    def test_shortens_paz_in_nav_and_ncx(self, tmp_path):
        (tmp_path / "nav.xhtml").write_text(
            f'<li><a href="index_split_047.html#bp-45">{_PAZ_FULL}</a></li>', encoding="utf-8"
        )
        (tmp_path / "toc.ncx").write_text(f"<navLabel><text>{_PAZ_FULL}</text></navLabel>", encoding="utf-8")

        stats = be.apply_nav_toc_short_titles(tmp_path)

        nav = (tmp_path / "nav.xhtml").read_text(encoding="utf-8")
        ncx = (tmp_path / "toc.ncx").read_text(encoding="utf-8")
        assert _PAZ_SHORT in nav and _PAZ_FULL not in nav
        assert _PAZ_SHORT in ncx and _PAZ_FULL not in ncx
        assert stats["labels_rewritten"] >= 2

    def test_no_short_title_leaves_label_untouched(self, tmp_path):
        # A book with no toc_title (e.g. "Genesis") must not be rewritten.
        (tmp_path / "nav.xhtml").write_text(
            '<li><a href="index_split_000.html#bp-1">Genesis</a></li>', encoding="utf-8"
        )
        (tmp_path / "toc.ncx").write_text("<navLabel><text>Genesis</text></navLabel>", encoding="utf-8")
        be.apply_nav_toc_short_titles(tmp_path)
        assert "Genesis" in (tmp_path / "nav.xhtml").read_text(encoding="utf-8")

"""§5.4 #4 — Nave's topical-index back-matter page.

Composed from the structured ``content/sources/naves_topical.json`` (4,604
topics → ~100k verse refs; loaded via ``sources.naves_topical()``). The build
filters refs to the edition's canon, dedupes, orders them canonically, and
renders an alphabetical topic→verses index — appended after the Reference
Tables and before the closing colophon (back-matter order Sources → Reference
tables → Topical index → Closing colophon).
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


class _Hit:
    def __init__(self, b, c, v):
        self.target_book, self.target_chapter, self.target_verse = b, c, v


class _FakeNaves:
    """Stub of sources.NavesTopical with just the index-building surface."""

    def __init__(self, topics):
        self._t = topics  # {topic: [(book, ch, vs), ...]}

    def topics(self):
        return sorted(self._t)

    def verses_for(self, topic):
        return [_Hit(*r) for r in self._t.get(topic, [])]


BOOK_ORDER = {"gen": 0, "exo": 1, "mat": 50, "tob": 80}


class TestBuildTopicIndex:
    def test_filters_canon_dedupes_and_orders_canonically(self):
        from scripts.matter_pages import build_topic_index

        naves = _FakeNaves(
            {
                # mat after gen canonically; the dup gen 15:6 collapses; tob is out of canon
                "FAITH": [("mat", 8, 10), ("gen", 15, 6), ("gen", 15, 6), ("tob", 2, 1)],
                "TOBIT-ONLY": [("tob", 1, 1)],  # entirely out of canon -> omitted
            }
        )
        idx = dict(build_topic_index(naves, canon_books={"gen", "exo", "mat"}, book_order=BOOK_ORDER))
        assert "TOBIT-ONLY" not in idx  # no in-canon ref
        assert idx["FAITH"] == [("gen", 15, 6), ("mat", 8, 10)]

    def test_none_canon_keeps_all_books(self):
        from scripts.matter_pages import build_topic_index

        naves = _FakeNaves({"FAITH": [("tob", 2, 1), ("gen", 15, 6)]})
        idx = dict(build_topic_index(naves, canon_books=None, book_order=BOOK_ORDER))
        assert idx["FAITH"] == [("gen", 15, 6), ("tob", 2, 1)]

    def test_topics_alphabetical(self):
        from scripts.matter_pages import build_topic_index

        naves = _FakeNaves({"ZEAL": [("gen", 1, 1)], "ABRAHAM": [("gen", 12, 1)]})
        idx = build_topic_index(naves, canon_books=None, book_order=BOOK_ORDER)
        assert [t for t, _ in idx] == ["ABRAHAM", "ZEAL"]


class TestRenderTopicalIndexPage:
    def test_renders_valid_xhtml_with_topics_and_refs(self):
        from scripts.matter_pages import render_topical_index_page

        idx = [("FAITH", [("gen", 15, 6), ("mat", 8, 10)])]
        out = render_topical_index_page(idx, book_abbrev=lambda c: c.title())
        ET.fromstring(out)  # well-formed XHTML
        assert "FAITH" in out
        assert "Gen 15:6" in out and "Mat 8:10" in out
        assert 'epub:type="backmatter"' in out

    def test_escapes_topic_names(self):
        from scripts.matter_pages import render_topical_index_page

        out = render_topical_index_page([("A &amp; B".replace("&amp;", "&"), [("gen", 1, 1)])], book_abbrev=str.title)
        assert "A &amp; B" in out
        ET.fromstring(out)

    def test_empty_index_still_valid(self):
        from scripts.matter_pages import render_topical_index_page

        out = render_topical_index_page([], book_abbrev=str.title)
        ET.fromstring(out)


class TestRealCorpusIndex:
    """Smoke against the real Nave's source — the page must build for the full
    87-book superset without error and cover a substantial topic set."""

    def test_full_index_builds_from_real_source(self):
        from scripts.core import sources
        from scripts.matter_pages import build_topic_index, render_topical_index_page

        naves = sources.naves_topical()
        book_order = {b["code"]: i for i, b in enumerate(config.load_books())}
        idx = build_topic_index(naves, canon_books=None, book_order=book_order)
        assert len(idx) > 3000  # ~4,604 topics
        out = render_topical_index_page(idx, book_abbrev=str.title)
        ET.fromstring(out)  # the whole real index is well-formed

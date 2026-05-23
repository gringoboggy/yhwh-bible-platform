import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


# NOTE: build_vnote_aside + harvest_existing_langs are now exercised in
# tests/test_popup_versions.py against the B1 list-of-versions API. The old
# english/hebrew/greek-keyword tests that lived here were orphaned by the B1
# refactor (pre-B1 signature) and have been removed as redundant.


class TestWrapVerseNumber:
    def test_wraps_bare_span(self):
        from scripts.generate_verse_popups import wrap_verse_number

        chunk = '<p class="verse-p"><span class="vn">1</span>And king David was old.'
        out, changed = wrap_verse_number(chunk, code="1ki", ch=1, vs=1, title="The First Book of Kings")
        assert changed is True
        assert (
            '<a class="vn-link" id="v-1ki-1-1" href="#vnote-1ki-1-1" '
            'epub:type="noteref" title="The First Book of Kings 1:1">'
            '<span class="vn">1</span></a>'
        ) in out

    def test_idempotent_when_already_wrapped(self):
        from scripts.generate_verse_popups import wrap_verse_number

        already = (
            '<a class="vn-link" id="v-1ki-1-1" href="#vnote-1ki-1-1" '
            'epub:type="noteref" title="The First Book of Kings 1:1">'
            '<span class="vn">1</span></a>And king David was old.'
        )
        out, changed = wrap_verse_number(already, code="1ki", ch=1, vs=1, title="The First Book of Kings")
        assert changed is False
        assert out == already

    def test_only_first_matching_span_in_chunk(self):
        from scripts.generate_verse_popups import wrap_verse_number

        chunk = '<span class="vn">2</span>text with a stray "2" inside.'
        out, changed = wrap_verse_number(chunk, code="1ki", ch=1, vs=2, title="The First Book of Kings")
        assert out.count('id="v-1ki-1-2"') == 1


class TestVerseSpansInChapter:
    HTML = (
        '<p id="ch-b10-c1" class="ch-heading"><span class="bold-num">1</span></p>'
        '<p class="verse-p"><span class="vn">1</span>First verse.</p>'
        '<p class="verse-p"><span class="vn">2</span>Second verse.</p>'
        '<p id="ch-b10-c2" class="ch-heading"><span class="bold-num">2</span></p>'
        '<p class="verse-p"><span class="vn">1</span>Next chapter v1.</p>'
        '<section class="verse-refs-section" epub:type="footnotes" hidden=""></section>'
    )

    def test_finds_chapter_1_region_bounds(self):
        from scripts.generate_verse_popups import chapter_region

        start, end = chapter_region(self.HTML, bxx="b10", ch=1)
        slice_ = self.HTML[start:end]
        assert "First verse." in slice_ and "Second verse." in slice_
        assert "Next chapter v1." not in slice_

    def test_lists_verse_numbers_in_order(self):
        from scripts.generate_verse_popups import chapter_region, verse_numbers_in_region

        start, end = chapter_region(self.HTML, bxx="b10", ch=1)
        assert verse_numbers_in_region(self.HTML[start:end]) == [1, 2]


class TestEnsureVerseRefsSection:
    def test_returns_existing_section_span(self):
        from scripts.generate_verse_popups import ensure_verse_refs_section

        text = 'x<section class="verse-refs-section" epub:type="footnotes" hidden=""></section></body>'
        new_text, insert_at = ensure_verse_refs_section(text)
        assert new_text == text  # already present, unchanged
        assert text[insert_at : insert_at + len("</section>")] == "</section>"

    def test_creates_section_before_body_close(self):
        from scripts.generate_verse_popups import ensure_verse_refs_section

        text = "<body><p>scripture</p></body></html>"
        new_text, insert_at = ensure_verse_refs_section(text)
        assert 'class="verse-refs-section"' in new_text
        assert new_text[insert_at : insert_at + len("</section>")] == "</section>"


def _make_unwrapped_work(tmp_path, monkeypatch, book_code: str = "1ki") -> "Path":
    """Copy epub_working to a tmp dir, strip existing verse-popup anchors for
    *book_code* so the generator has something to do, and monkeypatch EPUB_DIR."""
    import re
    import shutil

    import scripts.generate_verse_popups as g

    work = tmp_path / "epub_working"
    work.mkdir()
    for f in g.EPUB_DIR.glob("index_split_*.html"):
        shutil.copy(f, work / f.name)

    # Strip existing vn-link anchors so the generator can re-wrap them.
    anchor_re = re.compile(
        rf'<a class="vn-link" id="v-{re.escape(book_code)}-[^"]*"[^>]*>(<span class="vn">[^<]*</span>)</a>',
        re.DOTALL,
    )
    for f in work.glob("index_split_*.html"):
        text = f.read_text(encoding="utf-8")
        stripped = anchor_re.sub(r"\1", text)
        if stripped != text:
            f.write_text(stripped, encoding="utf-8")

    monkeypatch.setattr(g, "EPUB_DIR", work)
    return work


class TestGenerateBook:
    def test_1ki_gains_wrappers_and_asides_dry_run(self, tmp_path, monkeypatch):
        """After stripping existing wrappers, generate_book should re-wrap them."""
        import scripts.generate_verse_popups as g

        _make_unwrapped_work(tmp_path, monkeypatch, "1ki")
        stats = g.generate_book("1ki", dry_run=True)
        assert stats["verses_wrapped"] > 500, stats  # 1Ki has 816 verses
        assert stats["asides_built"] == stats["verses_wrapped"], stats
        assert stats["files_changed"], stats

    def test_genesis_is_idempotent_dry_run(self):
        from scripts.generate_verse_popups import generate_book

        stats = generate_book("gen", dry_run=True)
        assert stats["verses_wrapped"] == 0, stats  # already wrapped
        assert stats["asides_built"] > 0, stats  # but asides still rebuilt


class TestIdempotency:
    def test_second_run_changes_nothing(self, tmp_path, monkeypatch):
        import scripts.generate_verse_popups as g

        _make_unwrapped_work(tmp_path, monkeypatch, "1ki")

        first = g.generate_book("1ki", dry_run=False)
        assert first["files_changed"], first
        second = g.generate_book("1ki", dry_run=False)
        assert second["files_changed"] == [], second


class TestCoverageAfterGeneration:
    def test_1ki_now_has_popups_in_base(self):
        from scripts.generate_verse_popups import EPUB_DIR

        blob = "".join(p.read_text(encoding="utf-8") for p in EPUB_DIR.glob("index_split_*.html"))
        assert 'href="#vnote-1ki-1-1"' in blob
        assert 'id="vnote-1ki-1-1"' in blob

    def test_genesis_1_1_text_aligned(self):
        # The uniform regen fixes the old Gen 1:1/1:2 offset: 1:1's aside must
        # carry Genesis 1:1's KJV text, not be empty.
        import re as _re

        from scripts.core import translations as tx
        from scripts.generate_verse_popups import EPUB_DIR

        kjv_11 = tx.get_verse("kjv", "gen", 1, 1)
        gen_file = (EPUB_DIR / "index_split_000.html").read_text(encoding="utf-8")
        m = _re.search(r'<aside class="vnote" id="vnote-gen-1-1".*?</aside>', gen_file, _re.DOTALL)
        assert m and kjv_11 and kjv_11.split()[0] in m.group(0)

    def test_2sa_retains_greek_after_regen(self):
        # Harvest-and-merge safety: 2 Samuel had LXX-Greek popups before the
        # regen and the resolver has no 2sa Greek source, so the regen must have
        # preserved the existing Greek (not dropped it).
        import re as _re

        from scripts.generate_verse_popups import EPUB_DIR

        blob = "".join(p.read_text(encoding="utf-8") for p in EPUB_DIR.glob("index_split_*.html"))
        asides_2sa = _re.findall(r'<aside class="vnote" id="vnote-2sa-[^"]+".*?</aside>', blob, _re.DOTALL)
        assert asides_2sa, "no 2 Samuel vnote asides found"
        assert any("vnote-greek" in a for a in asides_2sa), "2 Samuel lost its Greek popups — harvest-merge failed"

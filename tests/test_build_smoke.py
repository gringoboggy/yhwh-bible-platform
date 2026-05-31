"""Build smoke test — regression guard for the 2026-05-21 base-HTML gap.

The EPUB build *source* (``epub_working/index_split_*.html`` — the World
English Bible scripture text that notes inject into) was lost in the
2026-05-08 repo re-init (never committed) and silently broke every build
until it was recovered + committed (5ee2ad1, 2026-05-21). The
"smoother-running" audit (P1) asked for a smoke test that builds one
edition and asserts a valid EPUB, so the gap can never recur silently.

Two tiers:
  - fast pins: the base scripture HTML is present + substantive on disk
    (these would have flagged the gap the instant it appeared);
  - integration: ``build_one()`` produces a structurally valid EPUB that
    actually *contains* that scripture HTML — exercising the real build
    path (filter -> zip) with no epubcheck/Java dependency.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EPUB_WORKING = REPO / "epub_working"


class TestBaseScriptureHtmlPresent:
    """The build source must exist on disk — the cheap pins that would
    have caught the lost-base-HTML gap immediately."""

    def test_split_html_files_present(self):
        splits = sorted(EPUB_WORKING.glob("index_split_*.html"))
        assert len(splits) >= 50, (
            f"base scripture HTML missing/incomplete: found {len(splits)} "
            "index_split_*.html files in epub_working/ (expected the full WEB text)"
        )

    def test_split_html_is_substantive(self):
        total = sum(p.stat().st_size for p in EPUB_WORKING.glob("index_split_*.html"))
        assert total > 1_000_000, (
            f"base scripture HTML present but tiny ({total} bytes) — likely stubs, "
            "not the real World English Bible text"
        )

    def test_opf_and_nav_present(self):
        assert (EPUB_WORKING / "content.opf").is_file(), "content.opf missing from build source"
        assert (EPUB_WORKING / "nav.xhtml").is_file(), "nav.xhtml missing from build source"


class TestEbibleBuildProducesValidEpub:
    """``ebible build`` for one edition must yield a structurally valid
    EPUB that contains the base scripture HTML. Exercises the real
    ``build_one()`` path; no epubcheck/Java required."""

    EDITION = "ethiopian-tewahedo"

    def test_build_one_yields_valid_epub(self, tmp_path, monkeypatch):
        import scripts.build_edition as be
        from scripts.core import build_cache, config

        # Hermetic: neither read from nor write to the persistent build cache.
        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)

        assert self.EDITION in config.editions_by_id(), f"flagship edition {self.EDITION!r} missing"
        all_kinds = config.load_kinds()

        stats = be.build_one(self.EDITION, tmp_path, "smoke-test", all_kinds, force=True)

        epub = Path(stats["output_path"])
        assert epub.is_file(), "build_one reported success but no EPUB landed on disk"
        assert not stats.get("skipped"), "build was skipped — force=True must always build"
        assert stats["size_mb"] > 0.5, f"EPUB suspiciously small ({stats['size_mb']:.2f} MB) — empty shell?"

        with zipfile.ZipFile(epub) as zf:
            assert zf.testzip() is None, "corrupt EPUB zip"
            names = zf.namelist()
            # OCF spec: 'mimetype' must be the first entry AND stored uncompressed.
            assert names[0] == "mimetype", f"first zip entry must be 'mimetype', got {names[0]!r}"
            assert zf.getinfo("mimetype").compress_type == zipfile.ZIP_STORED, "mimetype must be stored, not deflated"
            assert zf.read("mimetype") == b"application/epub+zip"
            assert "META-INF/container.xml" in names, "EPUB missing OCF container.xml"
            assert any(n.endswith("content.opf") for n in names), "no OPF package document in EPUB"
            # The regression pin: the scripture text actually made it into the book.
            splits = [n for n in names if "index_split_" in n and n.endswith(".html")]
            assert len(splits) >= 50, (
                f"EPUB contains only {len(splits)} scripture split files — the base-HTML gap is back"
            )
            # Ω.0: a CC0 give-away must not bundle commercial ONIX sales metadata.
            onix_entries = [n for n in names if "onix" in n.split("/")]
            assert not onix_entries, f"EPUB bundles commercial ONIX files: {onix_entries}"
            # Per-file <title> must be the edition title, not calibre's default.
            edition_title = config.editions_by_id()[self.EDITION]["title"]
            sample = zf.read(splits[0]).decode("utf-8")
            assert "<title>Converted Ebook</title>" not in sample, (
                "chapter XHTML still carries calibre's default <title>Converted Ebook</title>"
            )
            assert f"<title>{edition_title}</title>" in sample, (
                f"chapter <title> should be the edition title {edition_title!r}"
            )


class TestInjectAnchorFallback:
    """Inject-tail fix (2026-05-21): a note whose anchor word isn't in the
    rendered verse text — KJV-vs-WEB wording divergence ('LORD'->'Yahweh',
    'firmament'->'expanse', 'void'->'formless') or a base-HTML verse-merge
    that left this verse's slot empty — must NOT be silently dropped. It
    falls back to verse-end placement, the same position the injector
    already uses for verse-level (empty-anchor) notes. This recovers the
    ~7,800-note anchor tail that was being left out of every EPUB (corpus
    placement 83% -> ~98%)."""

    def test_exact_anchor_match_is_not_a_fallback(self):
        from scripts.inject import resolve_marker_insertion

        html = "In the beginning God created the heavens and the earth."
        offset, used_fallback = resolve_marker_insertion(html, "created")
        assert used_fallback is False
        assert html[:offset].endswith("created")  # marker sits right after the word

    def test_absent_anchor_falls_back_to_verse_end(self):
        from scripts.inject import resolve_marker_insertion

        # WEB renders "Yahweh"; a note anchored to the KJV word 'LORD' can't match.
        html = "Yahweh God formed man from the dust of the ground.   "
        offset, used_fallback = resolve_marker_insertion(html, "LORD")
        assert used_fallback is True
        # Lands at the end of the verse's real prose (before trailing space) —
        # a valid in-region offset, never None, the note is never dropped.
        assert 0 < offset <= len(html)
        assert html[offset:].strip() == ""

    def test_empty_merged_region_still_returns_offset(self):
        from scripts.inject import resolve_marker_insertion

        # Off-by-one verse-merge: this verse's slot holds only prior markers,
        # the prose having rendered under the next verse's anchor.
        html = '<sup class="marker-word">⌘</sup>   '
        offset, used_fallback = resolve_marker_insertion(html, "created")
        assert used_fallback is True
        assert isinstance(offset, int)
        assert 0 <= offset <= len(html)  # valid index — marker placed, note kept

    def test_empty_anchor_is_verse_level_not_fallback(self):
        from scripts.inject import resolve_marker_insertion

        # Verse-level notes (xref/topic/comm) carry no word-anchor; their
        # end-of-verse placement is intentional, not a degraded fallback.
        html = "God said, Let there be light, and there was light.  "
        offset, used_fallback = resolve_marker_insertion(html, "")
        assert used_fallback is False
        assert html[offset:].strip() == ""


class TestNotesSectionLocator:
    """Inject-tail fix #2 (2026-05-21): the base HTML renders chapter
    headings two ways — Genesis-style ``<a id="ch-b00-c2" class="ch-anchor">``
    and Deuteronomy-style ``<p id="ch-b04-c1" class="ch-heading">``. The
    notes-section locator only matched the ``<a>`` form, so every chapter
    whose heading is a ``<p>`` (deu/1sa/jdg/jos/num/lev/rut chapter 1s, etc.)
    failed to find its EXISTING notes-section and dropped ~900 notes as
    'no-notes-section'. The locator must match the chapter id on any tag,
    and scope to the book's bxx so a shared file's other-book ``cN`` can't
    capture it."""

    SECTION = (
        '<aside class="notes-section" epub:type="footnotes" hidden="">\n'
        '<hr class="notes-rule"/>\n<h3 class="notes-heading">Notes</h3>\n</aside>\n'
    )

    def _assert_points_inside_section(self, html, result):
        assert result is not None
        start, end = result
        assert start <= end
        assert html[end:].startswith("</aside>")  # end sits at the closing tag
        assert "notes-heading" in html[start:end]  # range covers the section body

    def test_p_heading_chapter_finds_its_section(self):
        from scripts.inject import find_notes_section_for_chapter

        # Deuteronomy-style: id on the <p>, no <a> anchor. This was the bug.
        html = '<p id="ch-b04-c1" class="ch-heading"><span>1</span></p>\n<p class="verse-p">words</p>\n' + self.SECTION
        self._assert_points_inside_section(html, find_notes_section_for_chapter(html, 1, "b04"))

    def test_a_anchor_chapter_still_finds_its_section(self):
        from scripts.inject import find_notes_section_for_chapter

        # Genesis-style: id on an <a class="ch-anchor"> — must keep working.
        heading = '<a id="ch-b00-c2" class="ch-anchor"></a><p class="ch-heading"><span>2</span></p>\n'
        html = heading + "<p>v</p>\n" + self.SECTION
        self._assert_points_inside_section(html, find_notes_section_for_chapter(html, 2, "b00"))

    def test_bxx_scopes_to_the_right_book(self):
        from scripts.inject import find_notes_section_for_chapter

        # A shared split file: Numbers c1 (+section A) precedes Deuteronomy
        # c1 (+section B). Scoping by bxx must return B, not the first c1.
        section_a = self.SECTION.replace("Notes", "NUMBERS-NOTES")
        section_b = self.SECTION.replace("Notes", "DEUT-NOTES")
        html = (
            '<p id="ch-b03-c1" class="ch-heading"></p>\n<p>num</p>\n'
            + section_a
            + '<p id="ch-b04-c1" class="ch-heading"></p>\n<p>deu</p>\n'
            + section_b
        )
        result = find_notes_section_for_chapter(html, 1, "b04")
        assert result is not None
        start, end = result
        assert "DEUT-NOTES" in html[start:end]
        assert "NUMBERS-NOTES" not in html[start:end]

    def test_chapter_number_is_not_a_prefix_match(self):
        from scripts.inject import find_notes_section_for_chapter

        # c1 must not match c12: a file with only c12 + a section must not
        # resolve when asked for c1.
        html = '<p id="ch-b04-c12" class="ch-heading"></p>\n<p>v</p>\n' + self.SECTION
        assert find_notes_section_for_chapter(html, 1, "b04") is None

    def test_missing_section_still_returns_none(self):
        from scripts.inject import find_notes_section_for_chapter

        html = '<p id="ch-b04-c1" class="ch-heading"></p>\n<p class="verse-p">words, no section here</p>\n'
        assert find_notes_section_for_chapter(html, 1, "b04") is None


class TestEnsureNotesSectionA:
    """Inject-tail fix #3 (2026-05-21): when a chapter's verses spill across
    a file-split boundary, the chapter heading sits in the PREVIOUS split
    file while the verses (and their markers) land at the start of the next
    file — which therefore has no `ch-<bxx>-c<ch>` heading and no section
    for that chapter (gen 27 is the live case: 45 notes). ensure_notes_
    section_a repairs the split-dropped chapter anchor + an empty notes-
    section in the verse's file, right after the chapter's verses, so the
    notes land in their own section instead of being dropped. Idempotent."""

    SECTION = (
        '<aside class="notes-section" epub:type="footnotes" hidden="">\n'
        '<hr class="notes-rule"/>\n<h3 class="notes-heading">Notes</h3>\n</aside>\n'
    )

    def test_returns_existing_section_unchanged(self):
        from scripts.inject import ensure_notes_section_a, find_notes_section_for_chapter

        html = '<p id="ch-b00-c27" class="ch-heading"></p>\n<p>v</p>\n' + self.SECTION
        new_text, rng = ensure_notes_section_a(html, 27, "b00", 0)
        assert new_text == html  # nothing created when a section already exists
        assert rng == find_notes_section_for_chapter(html, 27, "b00")

    def test_creates_section_at_split_boundary(self):
        from scripts.inject import ensure_notes_section_a, find_notes_section_for_chapter

        # ch27 verses begin the file; ch28 (with its own section) follows;
        # ch27's heading is absent (it's in the previous split file).
        ch27 = '<p class="verse-p"><a class="vn-link" id="v-gen-27-1"></a>Esau sold his birthright.</p>\n'
        ch28 = '<p id="ch-b00-c28" class="ch-heading"></p>\n<p>v28</p>\n' + self.SECTION
        html = ch27 + ch28
        assert find_notes_section_for_chapter(html, 27, "b00") is None  # the bug precondition

        new_text, rng = ensure_notes_section_a(html, 27, "b00", html.index('id="v-gen-27-1"'))
        assert rng is not None
        # the created section is now locatable for ch27 (idempotency hook)
        assert find_notes_section_for_chapter(new_text, 27, "b00") is not None
        # the synthesized section carries its OWN id, never a duplicate of the
        # real chapter anchor (which lives in the previous split file) — that
        # cross-file dup would fail `ebible verify`.
        assert 'id="notes-b00-c27"' in new_text
        assert 'id="ch-b00-c27"' not in new_text
        # placed after ch27's verses and before ch28
        assert new_text.index('id="notes-b00-c27"') > new_text.index('id="v-gen-27-1"')
        assert new_text.index('id="notes-b00-c27"') < new_text.index('id="ch-b00-c28"')

    def test_idempotent_no_duplicate_sections(self):
        from scripts.inject import ensure_notes_section_a

        html = '<p><a id="v-gen-27-1"></a>x</p>\n<p id="ch-b00-c28" class="ch-heading"></p>\n' + self.SECTION
        t1, _ = ensure_notes_section_a(html, 27, "b00", 0)
        t2, _ = ensure_notes_section_a(t1, 27, "b00", 0)
        assert t2 == t1  # the second call creates nothing
        assert t1.count('id="notes-b00-c27"') == 1


class TestAuditBaseHtml:
    """audit_base_html.classify_book reports, per book, whether every
    chapter's verse text is reachable from its chapter anchor (regular) or
    whether scripture and the chapter anchor are split across files
    (irregular). It must flag 1ch as irregular and gen as regular."""

    def test_gen_is_regular(self):
        from scripts.audit_base_html import classify_book

        report = classify_book("gen")
        assert report["irregular_chapters"] == [], report

    def test_1ch_flags_chapter_3_irregular(self):
        from scripts.audit_base_html import classify_book

        report = classify_book("1ch")
        # ch3's verse text is in a different split file than its ch anchor
        assert 3 in report["irregular_chapters"], report

    def test_verse_absent_report_lists_book_chapter_verse(self):
        from scripts.audit_base_html import verse_absent_report

        rows = verse_absent_report()
        # every row is a concrete (book, ch, v) the WEB base does not contain
        assert rows, "expected the Strategy-A versification gaps to be enumerated"
        assert all(len(r) == 3 for r in rows)
        assert all(isinstance(r[0], str) and isinstance(r[1], int) and isinstance(r[2], int) for r in rows)


class TestVerseRegionBSpill:
    """The real split-layout defect: a Strategy-B chapter whose ``ch-anchor``
    sits at the END of split file N while its verses open file N+1 (jer 25,
    1ch 3, isa 33, psa 73; psa 119 splits mid-chapter at v88/89). Split files
    are SHARED between books (e.g. 2 Kings + 1 Chronicles share index_split_015),
    so a full-document vn-walk would ingest the previous book's verses and
    mis-number chapters — instead, ``find_verse_region_b_spill`` looks only at
    the head of the NEXT file (start -> its first ``ch-{bxx}`` anchor), and
    only for the chapter whose anchor is physically LAST in file N (the one
    that actually spilled). That guard prevents a versification-miss on an
    earlier chapter from borrowing the spilled chapter's verse v."""

    # jer-like: CH24 (v1-10) then CH25 anchor at the very end of file A, no
    # verses after it; all of CH25's verses (1,30,38) open file B's head.
    FILE_A = (
        '<a id="ch-b38-c24" class="ch-anchor"></a><p class="verse-p">'
        '<span class="vn">1</span> word24a <span class="vn">10</span> word24j</p>'
        '<a id="ch-b38-c25" class="ch-anchor"></a>'
    )
    FILE_B = (
        '<body class="bible-body"><p class="verse-p">'
        '<span class="vn">1</span> cup of wrath <span class="vn">30</span> the nations '
        '<span class="vn">38</span> tail</p>'
        '<a id="ch-b38-c26" class="ch-anchor"></a><p class="verse-p">'
        '<span class="vn">1</span> ch26v1</p></body>'
    )

    def _texts(self):
        return {"a.html": self.FILE_A, "b.html": self.FILE_B}

    def test_full_spill_finds_verse_in_next_file_head(self):
        from scripts import inject

        hit = inject.find_verse_region_b_spill(["a.html", "b.html"], self._texts(), "a.html", "b38", 25, 30)
        assert hit is not None, "spilled verse 25:30 should resolve in the next file's head"
        fname, (s, e) = hit
        assert fname == "b.html"
        assert "the nations" in self.FILE_B[s:e]
        assert "tail" not in self.FILE_B[s:e]  # region stops before verse 38

    def test_guard_rejects_non_last_chapter(self):
        from scripts import inject

        # jer 24 has 10 verses; a note on a non-existent 24:30 must NOT borrow
        # 25:30's verse from the spilled head. ch 24 is not the last anchor.
        hit = inject.find_verse_region_b_spill(["a.html", "b.html"], self._texts(), "a.html", "b38", 24, 30)
        assert hit is None, "non-last (non-spilled) chapter must never borrow the next file's verses"

    def test_partial_mid_chapter_spill(self):
        from scripts import inject

        # psa 119-like: v1-88 sit under the anchor in file A; v89-176 open file B.
        file_a = (
            '<a id="ch-b30-c119" class="ch-anchor"></a><p class="verse-p">'
            '<span class="vn">1</span> aleph <span class="vn">88</span> v88</p>'
        )
        file_b = (
            '<body><p class="verse-p"><span class="vn">89</span> v89 '
            '<span class="vn">100</span> hundred <span class="vn">176</span> last</p>'
            '<a id="ch-b30-c120" class="ch-anchor"></a><p><span class="vn">1</span> psa120v1</p></body>'
        )
        texts = {"a.html": file_a, "b.html": file_b}
        hit = inject.find_verse_region_b_spill(["a.html", "b.html"], texts, "a.html", "b30", 119, 100)
        assert hit is not None
        fname, (s, e) = hit
        assert fname == "b.html" and "hundred" in file_b[s:e]
        # a verse that is NOT in the spilled head (it lives under the anchor in
        # file A) is not the spill resolver's job -> None, no false placement.
        assert inject.find_verse_region_b_spill(["a.html", "b.html"], texts, "a.html", "b30", 119, 50) is None

    def test_no_next_file_returns_none(self):
        from scripts import inject

        # host is the last file in the book -> nothing to spill into.
        hit = inject.find_verse_region_b_spill(["a.html", "b.html"], self._texts(), "b.html", "b38", 26, 1)
        assert hit is None


class TestInjectIrregularLayout:
    """End-to-end: a Strategy-B book whose chapter's ch-anchor ends one split
    file while its verses open the next must still inject that chapter's note
    — the marker into the verse's file, the aside into that file's notes-
    section — instead of dropping it as 'verse region not parseable'."""

    def test_spilled_chapter_note_injects(self, tmp_path, monkeypatch):
        from scripts import inject

        # file A: ch1 (anchor + verse) then ch2's anchor at the END, no verses.
        a = (
            '<html><body><a id="ch-b99-c1" class="ch-anchor"></a>'
            '<p class="verse-p"><span class="vn">1</span> alpha</p>'
            '<a id="ch-b99-c2" class="ch-anchor"></a></body></html>'
        )
        # file B: ch2's verse opens the file (the spill); ch3 follows; a per-file
        # notes-section exists so the aside has a home.
        b = (
            '<html><body class="bible-body">'
            '<p class="verse-p"><span class="vn">1</span> the deep word here</p>'
            '<a id="ch-b99-c3" class="ch-anchor"></a>'
            '<p class="verse-p"><span class="vn">1</span> gamma</p>'
            '<aside class="notes-section" epub:type="footnotes" hidden="">'
            '<hr class="notes-rule"/><h3 class="notes-heading">Notes</h3></aside>'
            "</body></html>"
        )
        epub = tmp_path / "epub_working"
        epub.mkdir()
        (epub / "a.html").write_text(a, encoding="utf-8")
        (epub / "b.html").write_text(b, encoding="utf-8")
        monkeypatch.setattr(inject, "EPUB_DIR", epub)
        book = {
            "code": "zz",
            "bxx": "b99",
            "strategy": "B",
            "ch_count": 3,
            "files": ["a.html", "b.html"],
            "id_prefix": "b99",
        }
        # one note on ch2 v1, anchored to a word that IS in the spilled verse
        monkeypatch.setattr(
            inject,
            "load_notes",
            lambda p: [(2, 1, "", "word", "lang-hebrew", "T", "L", "B")],
        )
        stats = inject.inject_book(book, dry_run=True)
        assert stats["injected"] == 1, stats
        assert len(stats["missing_anchor"]) == 0, stats


class TestOnixExcludedFromPackage:
    """Ω.0 free-public pivot: the EPUB is a CC0 give-away and must NOT carry
    the commercial ONIX sales-metadata files. Legacy ONIX artifacts may still
    linger under ``epub_working/onix/`` (gitignored, but present on disk), and
    ``build_one`` copies the whole working tree into its temp build dir — so the
    packaging walk (``build_epub.collect_files``) is the chokepoint that must
    drop them. Excluding the directory name covers BOTH the per-edition build
    (via ``build_one``) and a direct ``build_epub.py`` run."""

    def test_should_skip_excludes_onix_directory(self):
        from scripts.build_epub import should_skip

        # Every file under an onix/ directory is commercial metadata — skip it.
        assert should_skip(Path("onix/onix-ethiopian-tewahedo.xml")) is True
        # Regression guard: scripture + structural files must still be packaged.
        assert should_skip(Path("index_split_000.html")) is False
        assert should_skip(Path("content.opf")) is False

    def test_collect_files_omits_onix_xml(self, tmp_path):
        from scripts.build_epub import collect_files

        (tmp_path / "mimetype").write_text("application/epub+zip", encoding="utf-8")
        (tmp_path / "index_split_000.html").write_text("<html></html>", encoding="utf-8")
        onix_dir = tmp_path / "onix"
        onix_dir.mkdir()
        (onix_dir / "onix-ethiopian-tewahedo.xml").write_text("<ONIXMessage/>", encoding="utf-8")

        files, _total, skipped = collect_files(tmp_path)
        names = {p.name for p in files}
        assert "index_split_000.html" in names, "scripture file must be packaged"
        assert "onix-ethiopian-tewahedo.xml" not in names, "commercial ONIX must be excluded from the EPUB"
        assert skipped >= 1


class TestPerFilePageTitle:
    """The base scripture chunks (epub_working/index_split_*.html) carry the
    calibre-default ``<title>Converted Ebook</title>``. build_one must rewrite
    it to the edition's own title (per-edition, matching OPF dc:title), without
    clobbering the generated pages' already-correct titles, and XML-escaping
    the title so it stays well-formed XHTML."""

    def test_calibre_default_replaced_with_edition_title(self):
        from scripts.build_edition import _retitle_html_pages

        text = "<head>\n    <title>Converted Ebook</title>\n</head>"
        new_text, n = _retitle_html_pages(text, "The Ethiopian Tewahedo Study Bible")
        assert n == 1
        assert "<title>The Ethiopian Tewahedo Study Bible</title>" in new_text
        assert "Converted Ebook" not in new_text

    def test_leaves_other_titles_untouched(self):
        from scripts.build_edition import _retitle_html_pages

        # Generated pages already have correct titles — must not be rewritten.
        text = "<title>Copyright &amp; Credits</title>"
        new_text, n = _retitle_html_pages(text, "My Edition")
        assert n == 0
        assert new_text == text

    def test_title_is_xml_escaped(self):
        from scripts.build_edition import _retitle_html_pages

        # A title containing & / < must be escaped so the XHTML stays valid.
        new_text, n = _retitle_html_pages("<title>Converted Ebook</title>", "Faith & <Reason>")
        assert n == 1
        assert "<title>Faith &amp; &lt;Reason&gt;</title>" in new_text

    def test_idempotent(self):
        from scripts.build_edition import _retitle_html_pages

        once, _ = _retitle_html_pages("<title>Converted Ebook</title>", "Ed")
        twice, n = _retitle_html_pages(once, "Ed")
        assert twice == once
        assert n == 0

    def test_empty_title_is_noop(self):
        from scripts.build_edition import _retitle_html_pages

        text = "<title>Converted Ebook</title>"
        new_text, n = _retitle_html_pages(text, "")
        assert n == 0
        assert new_text == text

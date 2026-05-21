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

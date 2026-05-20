"""Tests for the chapter-complexity classifier (audit U4).

Codifies which Kings chapters have known failure classes that need extra
anti-failure screens in the C-2/C-5 transcriber prompt — derived from the
1Ki4 retrospective (LIST chapters fire `ለ`/`ስ`, `ይ`/`ደ`, `ያ`/`ደ`,
numeral-vs-letter, cross-glyph classes that NARRATIVE chapters don't).
"""


class TestClassify:
    def test_default_narrative(self):
        from scripts.core.manuscript_chapter_class import classify

        # Solomon accession / Adonijah / David's charge / Solomon's dream —
        # narrative prose, harmonization-to-printed-Bible is the dominant
        # failure mode (the matrix's pre-1Ki4 CARDINAL RULE).
        assert classify("1ki", 1) == "NARRATIVE"
        assert classify("1ki", 2) == "NARRATIVE"
        assert classify("1ki", 3) == "NARRATIVE"
        assert classify("2ki", 1) == "NARRATIVE"

    def test_1ki4_is_list(self):
        """The reason this classifier exists: 1Ki4's officer + wisdom-name
        registry was the first chapter where list-class failures fired and
        the matrix wasn't pre-screening for them."""
        from scripts.core.manuscript_chapter_class import classify

        assert classify("1ki", 4) == "LIST"

    def test_known_regnal_frames(self):
        from scripts.core.manuscript_chapter_class import classify

        # 1Ki15-16: Jeroboam/Nadab/Baasha/Elah/Zimri/Omri/Ahab succession.
        assert classify("1ki", 15) == "REGNAL_FRAME"
        assert classify("1ki", 16) == "REGNAL_FRAME"
        # 2Ki13-17: divided-kingdom synchronistic regnal frames + fall of
        # Samaria — heavy on year-of-king-X / mother / city patronymics.
        for c in (13, 14, 15, 16, 17):
            assert classify("2ki", c) == "REGNAL_FRAME"

    def test_unknown_book_defaults_narrative(self):
        from scripts.core.manuscript_chapter_class import classify

        # Conservative: a future caller asking about (1sa, 1) gets NARRATIVE,
        # not an exception — the classifier's role is risk-screening, not a
        # gate.
        assert classify("1sa", 1) == "NARRATIVE"


class TestChapterProfile:
    def test_list_profile_carries_class_specific_screens(self):
        from scripts.core.manuscript_chapter_class import chapter_profile

        p = chapter_profile("1ki", 4)
        assert p["class"] == "LIST"
        assert p["book"] == "1ki" and p["chapter"] == 4
        assert isinstance(p["screens"], list) and len(p["screens"]) >= 3

        joined = " ".join(p["screens"])
        # NARRATIVE-class screens inherit (harmonization + column-boundary).
        assert "harmonization" in joined.lower()
        assert "boundary" in joined.lower()
        # LIST-specific: name-fidel families documented in 1Ki4 retrospective.
        assert "ለ" in joined and "ስ" in joined
        assert "ይ" in joined and "ደ" in joined

    def test_narrative_profile_has_only_narrative_screens(self):
        from scripts.core.manuscript_chapter_class import chapter_profile

        p = chapter_profile("1ki", 1)
        assert p["class"] == "NARRATIVE"
        joined = " ".join(p["screens"])
        assert "harmonization" in joined.lower()
        # name-fidel family screens are LIST-specific, not present here
        assert "ያ" not in joined  # final-syllable name-fidel only fires on LIST

    def test_regnal_profile_inherits_list_screens(self):
        from scripts.core.manuscript_chapter_class import chapter_profile

        p = chapter_profile("2ki", 15)
        assert p["class"] == "REGNAL_FRAME"
        joined = " ".join(p["screens"])
        # REGNAL inherits NARRATIVE + LIST screens, plus regnal-year numerals
        assert "harmonization" in joined.lower()
        assert "ለ" in joined and "ስ" in joined
        assert "year" in joined.lower() or "numeral" in joined.lower()

    def test_expected_rounds_grow_with_complexity(self):
        from scripts.core.manuscript_chapter_class import chapter_profile

        # The honest expectation set by the 1Ki1 (3) → 1Ki4 (7) trajectory:
        # narrative converges fastest, regnal frames need more passes.
        n = chapter_profile("1ki", 1)["expected_rounds_max"]
        ls = chapter_profile("1ki", 4)["expected_rounds_max"]
        rf = chapter_profile("2ki", 15)["expected_rounds_max"]
        assert n <= ls <= rf
        # And the floor must be honest about even narrative chapters needing >1.
        assert chapter_profile("1ki", 1)["expected_rounds_min"] >= 2

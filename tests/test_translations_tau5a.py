"""τ.5-A — JPS 1917 + WLC Hebrew seed pins (2026-05-12).

Per SESSION_END_2026-05-12 §4 N+1 recommendation, this is the
session-N+1 ship: close the Hebrew column for the 6 of 9 editions
that declare `hebrew` in popup_languages_default. Mirrors the γ.5
LXX-seed pattern (3-verse Genesis seed + full ingest deferred to
τ.5-A.x user-side).

Coverage:
- TestTau5aRegistry:                 jps + wlc both registered in
  scripts.extract_translation.TRANSLATIONS with correct metadata
  (PD license, source URLs, notes documenting the user-side ingest
  path).
- TestTau5aDiscovery:                 list_translations() returns
  both new ids; has_translation() returns True; has_book(gen)
  returns True.
- TestTau5aJpsSeed:                   Gen 1:1-3 seed loads; verse
  text matches the JPS 1917 published English (literal text pin so
  a future swap is detected); meta short_title pinned to "JPS".
- TestTau5aWlcSeed:                   Gen 1:1-3 seed loads; verse
  text contains the canonical Hebrew opening "בְּרֵאשִׁית" (in the
  beginning); meta short_title pinned to "WLC"; verse text is in
  the Hebrew Unicode block.
- TestTau5aMetaShape:                 _meta.yaml for both follows
  the established pattern (id / title / short_title / license /
  source / stats / notes).

Pinning rationale: τ.5-A is the foundational shipping translation
work after the SESSION_END EPUB-scope reckoning. Getting the
registry + discovery + seed format right is what subsequent τ.*
ships build on. A future τ.5-A.x full ingest will replace the seed
with ~23,000 verses but the discovery/meta contract stays.
"""

from __future__ import annotations


class TestTau5aRegistry:
    """Both new translations registered in extract_translation.py."""

    def test_jps_registered(self):
        from scripts.extract_translation import TRANSLATIONS

        assert "jps" in TRANSLATIONS
        entry = TRANSLATIONS["jps"]
        assert entry["short_title"] == "JPS"
        assert entry["license"] == "Public Domain"
        # Source published 1917 — well before the PD cutoff.
        # Notes must mention the user-side ingest path.
        assert "user-side" in entry["notes"].lower() or "user" in entry["notes"].lower()

    def test_wlc_registered(self):
        from scripts.extract_translation import TRANSLATIONS

        assert "wlc" in TRANSLATIONS
        entry = TRANSLATIONS["wlc"]
        assert entry["short_title"] == "WLC"
        assert entry["license"] == "Public Domain"
        # Notes name the Leningrad Codex base manuscript.
        assert "Leningrad" in entry["notes"]

    def test_list_registered_includes_both(self):
        from scripts.extract_translation import list_registered

        ids = list_registered()
        assert "jps" in ids
        assert "wlc" in ids


class TestTau5aDiscovery:
    """Runtime discovery via scripts.core.translations finds both."""

    def test_both_in_list_translations(self):
        from scripts.core import translations

        ids = translations.list_translations()
        assert "jps" in ids
        assert "wlc" in ids

    def test_has_translation_returns_true(self):
        from scripts.core import translations

        assert translations.has_translation("jps") is True
        assert translations.has_translation("wlc") is True

    def test_has_book_gen(self):
        from scripts.core import translations

        assert translations.has_book("jps", "gen") is True
        assert translations.has_book("wlc", "gen") is True

    def test_has_book_unknown_returns_false(self):
        # Seed is Genesis only — other books shouldn't claim to exist.
        from scripts.core import translations

        assert translations.has_book("jps", "exo") is False
        assert translations.has_book("wlc", "exo") is False


class TestTau5aJpsSeed:
    """JPS 1917 Genesis 1:1-3 seed content + meta."""

    def test_three_verses_in_gen(self):
        from scripts.core import translations

        assert translations.book_verse_count("jps", "gen") == 3

    def test_gen_1_1(self):
        from scripts.core import translations

        v = translations.get_verse("jps", "gen", 1, 1)
        assert v == "In the beginning God created the heaven and the earth."

    def test_gen_1_2_canonical_jps_phrasing(self):
        # JPS 1917 says "unformed and void" (distinct from KJV's
        # "without form, and void"). Pin the JPS-specific phrasing
        # so a future swap to a different English translation is
        # caught as a deliberate change, not silent drift.
        from scripts.core import translations

        v = translations.get_verse("jps", "gen", 1, 2)
        assert "unformed and void" in v
        assert "hovered" in v  # JPS choice; KJV uses "moved"

    def test_gen_1_3_quoted_speech(self):
        # JPS uses single quotes for direct speech.
        from scripts.core import translations

        v = translations.get_verse("jps", "gen", 1, 3)
        assert "'Let there be light.'" in v

    def test_meta_shape(self):
        from scripts.core import translations

        meta = translations.translation_meta("jps")
        assert meta is not None
        assert meta["id"] == "jps"
        assert meta["short_title"] == "JPS"
        assert meta["license"] == "Public Domain"
        # Source-date 1917 pinned.
        assert int(meta["source"]["source_date"]) == 1917


class TestTau5aWlcSeed:
    """WLC Hebrew Genesis 1:1-3 seed content + meta."""

    def test_three_verses_in_gen(self):
        from scripts.core import translations

        assert translations.book_verse_count("wlc", "gen") == 3

    def test_gen_1_1_starts_with_bereshit(self):
        # בְּרֵאשִׁית = "In the beginning" — the canonical opening of
        # the Hebrew Bible. Pin its presence.
        from scripts.core import translations

        v = translations.get_verse("wlc", "gen", 1, 1)
        assert v is not None
        assert "בְּרֵאשִׁית" in v

    def test_gen_1_1_contains_elohim(self):
        # אֱלֹהִים = "God" — the second-most-anchored word in the verse.
        from scripts.core import translations

        v = translations.get_verse("wlc", "gen", 1, 1)
        assert "אֱלֹהִים" in v

    def test_gen_1_3_yehi_or(self):
        # יְהִי אוֹר = "Let there be light." Pin presence.
        from scripts.core import translations

        v = translations.get_verse("wlc", "gen", 1, 3)
        assert v is not None
        assert "יְהִי" in v
        assert "אוֹר" in v

    def test_text_is_hebrew_unicode(self):
        # Every character should be in the Hebrew Unicode block
        # (U+0590-U+05FF) or punctuation/whitespace.
        from scripts.core import translations

        for ch_num in (1, 2, 3):
            v = translations.get_verse("wlc", "gen", 1, ch_num)
            for c in v:
                cp = ord(c)
                # Hebrew block + ASCII whitespace/punctuation
                # (some WLC texts include the maqaf "־" U+05BE which
                # is in the Hebrew block).
                in_hebrew = 0x0590 <= cp <= 0x05FF
                in_ascii = cp <= 0x007F
                assert in_hebrew or in_ascii, f"non-Hebrew/non-ASCII char {c!r} (U+{cp:04X}) in verse {ch_num}"

    def test_meta_shape(self):
        from scripts.core import translations

        meta = translations.translation_meta("wlc")
        assert meta is not None
        assert meta["id"] == "wlc"
        assert meta["short_title"] == "WLC"
        assert meta["license"] == "Public Domain"

    def test_meta_documents_rtl_handling(self):
        # The WLC meta should reference the RTL rendering pattern
        # so future contributors know the popup pipeline handles it
        # correctly via ν.2.7.
        from scripts.core import translations

        meta = translations.translation_meta("wlc")
        assert meta is not None
        notes = (meta.get("notes") or "").lower()
        assert "right-to-left" in notes or "rtl" in notes


class TestTau5aPairing:
    """JPS + WLC ship together as the Hebrew-column pair."""

    def test_both_present_simultaneously(self):
        # Pin that the two halves of τ.5-A both ship — a future
        # contributor who ships only one and forgets the other gets
        # caught.
        from scripts.core import translations

        ids = translations.list_translations()
        assert "jps" in ids
        assert "wlc" in ids

    def test_both_have_genesis_seed(self):
        from scripts.core import translations

        # Same 3-verse coverage on both halves.
        assert translations.book_verse_count("jps", "gen") == 3
        assert translations.book_verse_count("wlc", "gen") == 3

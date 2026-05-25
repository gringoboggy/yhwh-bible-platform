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
- TestTau5aJpsFull:                   JPS 1917 full ingest (the
  f6d90c6 spine, superseding the seed); verse text matches the
  published English (literal text pin so a future swap is
  detected); meta short_title "JPS" + source_date 1917.
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

import re


def _consonants(s: str) -> str:
    """Bare Hebrew consonants only — drops <em> markup, niqqud, te'amim and
    punctuation, so a content pin matches the word regardless of vowel/accent
    Unicode encoding. Byte-exact niqqud/te'amim fidelity is pinned separately in
    tests/test_wlc_ingest.py (characterized against the recovered base)."""
    return re.sub(r"[^א-ת]", "", s)


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

    def test_has_book_coverage_full_ot_ingest(self):
        # Both JPS and WLC are now fully ingested (the f6d90c6 spine): each
        # claims the full OT (has Exodus). Earlier JPS was a Genesis-only seed.
        from scripts.core import translations

        assert translations.has_book("jps", "exo") is True  # jps: full OT ingest
        assert translations.has_book("wlc", "exo") is True  # wlc: full OT ingest


class TestTau5aJpsFull:
    """JPS 1917 — full ingest (the f6d90c6 spine: 39 books / 23,145 verses),
    superseding the τ.5-A 3-verse Genesis seed."""

    def test_full_genesis_matches_kjv_verse_count(self):
        # JPS aligns to the KJV Genesis verse count — proof the full ingest
        # replaced the 3-verse seed.
        from scripts.core import translations

        assert translations.book_verse_count("jps", "gen") == translations.book_verse_count("kjv", "gen")
        assert translations.book_verse_count("jps", "gen") > 1500

    def test_gen_1_1(self):
        # The eBible eng-jps source renders the opening words of Genesis in caps
        # ("IN THE beginning") — a typographic convention of the 1917 print
        # edition preserved by the ingest. Pin the actual text (swap-detector).
        from scripts.core import translations

        v = translations.get_verse("jps", "gen", 1, 1)
        assert v == "IN THE beginning God created the heaven and the earth."

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


class TestTau5aWlcFull:
    """WLC Hebrew — full 39-book ingest (Phase 2; supersedes the τ.5-A seed).

    The 3-verse Genesis seed was replaced by the full morphhb ingest, exactly as
    this file's module docstring anticipated. Verse text is now em-per-word with
    cantillation (te'amim), so content pins strip te'amim before matching the
    niqqud-level word. The discovery/meta contract is unchanged.
    """

    def test_full_genesis_matches_kjv_verse_count(self):
        # WLC Genesis aligns to the KJV Genesis verse count (the 31/32 boundary
        # shift preserves the total) — proof the full ingest replaced the seed.
        from scripts.core import translations

        wlc = translations.book_verse_count("wlc", "gen")
        assert wlc == translations.book_verse_count("kjv", "gen")
        assert wlc > 1500  # a full book, not a 3-verse seed

    def test_gen_1_1_starts_with_bereshit(self):
        # בראשית = "In the beginning" — the canonical opening of the Hebrew Bible.
        from scripts.core import translations

        v = translations.get_verse("wlc", "gen", 1, 1)
        assert v is not None
        assert "בראשית" in _consonants(v)

    def test_gen_1_1_contains_elohim(self):
        # אלהים = "God" — the second-most-anchored word in the verse.
        from scripts.core import translations

        assert "אלהים" in _consonants(translations.get_verse("wlc", "gen", 1, 1))

    def test_gen_1_3_yehi_or(self):
        # יהי אור = "Let there be light." Pin the consonants' presence.
        from scripts.core import translations

        v = _consonants(translations.get_verse("wlc", "gen", 1, 3))
        assert "יהי" in v
        assert "אור" in v

    def test_text_is_hebrew_block_or_markup(self):
        # Every char is the Hebrew block (U+0590-U+05FF) or ASCII (the <em>
        # word markup + spaces). Pins that no stray non-Hebrew text leaked in.
        from scripts.core import translations

        for vs in (1, 2, 3):
            v = translations.get_verse("wlc", "gen", 1, vs)
            for c in v:
                cp = ord(c)
                in_hebrew = 0x0590 <= cp <= 0x05FF
                in_ascii = cp <= 0x007F
                assert in_hebrew or in_ascii, f"non-Hebrew/non-ASCII char {c!r} (U+{cp:04X}) in verse {vs}"

    def test_meta_shape(self):
        from scripts.core import translations

        meta = translations.translation_meta("wlc")
        assert meta is not None
        assert meta["id"] == "wlc"
        assert meta["short_title"] == "WLC"
        assert meta["license"] == "Public Domain"

    def test_meta_documents_rtl_handling(self):
        # The WLC meta references the RTL rendering pattern so future
        # contributors know the popup pipeline handles it correctly.
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

    def test_genesis_coverage_both_full(self):
        from scripts.core import translations

        # Both halves of the Hebrew column are now full ingests (f6d90c6).
        assert translations.book_verse_count("jps", "gen") > 1500
        assert translations.book_verse_count("wlc", "gen") > 1500

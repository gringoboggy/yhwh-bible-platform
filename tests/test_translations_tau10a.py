"""τ.10-A — Arabic Van-Dyck 1865 seed (2026-05-12).

Closes the Arabic popup-language column for editions declaring
`arabic`. After this ship every language declared in
any edition's popup_languages_default has at least seed-level
coverage in content/translations/.

Coverage:
- TestTau10aRegistry:                 arabic-vandyke registered in
  scripts.extract_translation.TRANSLATIONS with correct metadata
  (Van Dyck team + 1865 + PD basis documented; eBible.org source).
- TestTau10aDiscovery:                 list_translations() returns
  the new id; has_translation / has_book(gen) both True.
- TestTau10aSeed:                      Gen 1:1-3 seed loads; verse
  text contains the canonical Arabic opening "فِي ٱلْبَدْءِ" (in the
  beginning); text is in Arabic Unicode block (U+0600-U+06FF);
  third verse contains "نُورٌ" (light).
- TestTau10aMetaShape:                 _meta.yaml id / short_title /
  license / source_date 1865 pinned.
- TestPopupLanguageCoverageClosed:    sanity check that every
  popup_languages_default language across all 9 editions now has
  at least one matching translation in content/translations/.
"""

from __future__ import annotations


class TestTau10aRegistry:
    def test_registered(self):
        from scripts.extract_translation import TRANSLATIONS

        assert "arabic-vandyke" in TRANSLATIONS
        entry = TRANSLATIONS["arabic-vandyke"]
        assert entry["short_title"] == "AVD"
        assert entry["license"] == "Public Domain"
        # 1865 Beirut edition, well before the 1929 PD cutoff.
        assert entry["source"]["source_date"] == 1865

    def test_notes_document_pd_basis(self):
        from scripts.extract_translation import TRANSLATIONS

        entry = TRANSLATIONS["arabic-vandyke"]
        # The Van Dyck team must be named in the notes so the PD
        # basis is auditable.
        for name in ("Van Dyck", "Bustani"):
            assert name in entry["notes"]


class TestTau10aDiscovery:
    def test_in_list_translations(self):
        from scripts.core import translations

        assert "arabic-vandyke" in translations.list_translations()

    def test_has_translation(self):
        from scripts.core import translations

        assert translations.has_translation("arabic-vandyke") is True

    def test_has_book_gen(self):
        from scripts.core import translations

        assert translations.has_book("arabic-vandyke", "gen") is True


class TestTau10aFull:
    """Arabic Van-Dyck — full ingest (the f6d90c6 translation spine: 66 books /
    31,102 verses), superseding the τ.10-A 3-verse seed. The Gen 1:1-3 content
    pins below still hold (the full text opens identically)."""

    def test_full_genesis(self):
        # A full book aligned to the KJV Genesis verse count — not a 3-verse seed.
        from scripts.core import translations

        assert translations.book_verse_count("arabic-vandyke", "gen") == translations.book_verse_count("kjv", "gen")
        assert translations.book_verse_count("arabic-vandyke", "gen") > 1500

    def test_gen_1_1_starts_with_fi_albadi(self):
        # فِي ٱلْبَدْءِ = "In the beginning" — the canonical Arabic
        # opening. Pin presence.
        from scripts.core import translations

        v = translations.get_verse("arabic-vandyke", "gen", 1, 1)
        assert v is not None
        assert "فِي" in v
        assert "ٱلْبَدْءِ" in v or "البدء" in v

    def test_gen_1_1_contains_allah(self):
        # ٱللهُ = "God" — pin presence in Arabic opening.
        from scripts.core import translations

        v = translations.get_verse("arabic-vandyke", "gen", 1, 1)
        assert "ٱللهُ" in v or "الله" in v

    def test_gen_1_3_contains_nur(self):
        # نُورٌ = "light" — pin presence in the let-there-be-light verse.
        from scripts.core import translations

        v = translations.get_verse("arabic-vandyke", "gen", 1, 3)
        assert v is not None
        assert "نُورٌ" in v or "نور" in v

    def test_text_is_arabic_unicode(self):
        # Every non-whitespace, non-ASCII-punctuation character should
        # be in the Arabic Unicode block (U+0600-U+06FF) or related
        # Arabic Presentation Forms (U+FB50-U+FDFF + U+FE70-U+FEFF).
        from scripts.core import translations

        for ch_num in (1, 2, 3):
            v = translations.get_verse("arabic-vandyke", "gen", 1, ch_num)
            for c in v:
                cp = ord(c)
                in_arabic = 0x0600 <= cp <= 0x06FF
                in_arabic_pres = 0xFB50 <= cp <= 0xFDFF or 0xFE70 <= cp <= 0xFEFF
                in_ascii = cp <= 0x007F
                # Punctuation like guillemets « » (U+00AB / U+00BB) is
                # also expected from the seed's quoted speech.
                is_quote = c in "«»"
                assert in_arabic or in_arabic_pres or in_ascii or is_quote, (
                    f"unexpected char {c!r} (U+{cp:04X}) in verse {ch_num}"
                )


class TestTau10aMetaShape:
    def test_meta_short_title(self):
        from scripts.core import translations

        meta = translations.translation_meta("arabic-vandyke")
        assert meta is not None
        assert meta["short_title"] == "AVD"
        assert meta["license"] == "Public Domain"
        assert int(meta["source"]["source_date"]) == 1865

    def test_meta_documents_rtl_handling(self):
        # Like WLC, the Arabic meta should reference the RTL
        # rendering pattern.
        from scripts.core import translations

        meta = translations.translation_meta("arabic-vandyke")
        assert meta is not None
        notes = (meta.get("notes") or "").lower()
        assert "right-to-left" in notes or "rtl" in notes


class TestPopupLanguageCoverageClosed:
    """Every popup_languages_default value resolves to a popup version.

    Originally (τ.10-A) this mapped language-family names to translation seeds.
    EPUB Wave 3 #6 redefined popup_languages_default to hold popup-VERSION ids
    directly (wlc/lxx-greek/greek-nt/vulgate/arabic), so the contract is now:
    every declared value resolves via popup_versions.resolve_version_id (which
    also honors the legacy aliases english→kjv, hebrew→wlc, greek→lxx-greek) —
    that resolver is what actually furnishes a verse popup.
    """

    def _all_popup_languages(self) -> set[str]:
        from scripts.core import config

        out = set()
        for ed in config.load_editions():
            for lang in ed.get("popup_languages_default") or []:
                out.add(str(lang).strip().lower())
        return out

    def test_every_popup_language_resolves_to_a_popup_version(self):
        # Wave 3 #6 contract: every declared popup_languages_default value must
        # resolve to a registered popup version — directly (wlc/lxx-greek/
        # greek-nt/vulgate/arabic) or via a legacy alias (english→kjv, etc.).
        # popup_versions.resolve_version_id is the single source of truth for
        # "this token furnishes a verse popup."
        from scripts.core import popup_versions

        gaps = [lang for lang in self._all_popup_languages() if popup_versions.resolve_version_id(lang) is None]
        assert not gaps, (
            f"popup-language gaps remain: {gaps}. Every declared "
            "popup_languages_default value must resolve to a registered popup "
            "version (popup_versions.resolve_version_id)."
        )

    def test_eight_translations_after_this_ship(self):
        # Pin the post-ship registered-translation count so future
        # additions are visible at the test-count layer.
        from scripts.core import translations

        ids = set(translations.list_translations())
        expected = {
            "kjv",
            "jps",
            "wlc",
            "lxx-brenton-greek",
            "lxx-brenton-english",
            "vulgate-clementine",
            "douay-rheims",
            "arabic-vandyke",
        }
        assert expected.issubset(ids), f"missing: {expected - ids}"

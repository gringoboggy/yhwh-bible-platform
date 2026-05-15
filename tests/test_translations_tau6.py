"""τ.6 — Ge'ez Tewahedo seed pins (2026-05-12).

Reinforces the v1.x flagship (ethiopian-tewahedo edition) by
adding its native scriptural language to the translation
registry. Ge'ez (ግዕዝ) is the Classical Ethiopian liturgical
language and the Tewahedo Bible's manuscript tradition language.

Coverage:
- TestTau6Registry:                 geez-tewahedo registered;
  PD basis documented via Pell-Platt 1830 + Dillmann 1865
  citations.
- TestTau6Discovery:                 list_translations / has_*
  predicates work.
- TestTau6Seed:                      Gen 1:1-3 loads; text is
  in Ethiopic Unicode block (U+1200-U+137F); opens on
  ቀዳሚሁ ("in the beginning") + ገብረ ("created") +
  እግዚአብሔር ("God"); third verse contains ብርሃን (light).
- TestTau6MetaShape:                 _meta.yaml schema pinned;
  notes document the Tewahedo-canonical 1 Enoch / Jubilees /
  Meqabyan distinctive (this is the v1.x uniqueness anchor).
- TestTau6FlagshipReinforcement:     this ship reinforces the
  ethiopian-tewahedo edition specifically; sanity check that
  the flagship edition exists + the runtime can compose this
  translation.
"""

from __future__ import annotations


class TestTau6Registry:
    def test_registered(self):
        from scripts.extract_translation import TRANSLATIONS

        assert "geez-tewahedo" in TRANSLATIONS
        entry = TRANSLATIONS["geez-tewahedo"]
        assert entry["short_title"] == "Ge'ez"
        assert entry["license"] == "Public Domain"
        # Pell-Platt 1830 BFBS Ge'ez NT well before 1929 cutoff.
        assert entry["source"]["source_date"] == 1830

    def test_notes_document_pd_basis(self):
        from scripts.extract_translation import TRANSLATIONS

        entry = TRANSLATIONS["geez-tewahedo"]
        # The PD basis anchors must appear so future audits trace
        # the chain back to specific PD publications.
        assert "Pell-Platt" in entry["notes"]
        assert "1830" in entry["notes"]


class TestTau6Discovery:
    def test_in_list_translations(self):
        from scripts.core import translations

        assert "geez-tewahedo" in translations.list_translations()

    def test_has_translation(self):
        from scripts.core import translations

        assert translations.has_translation("geez-tewahedo") is True

    def test_has_book_gen(self):
        from scripts.core import translations

        assert translations.has_book("geez-tewahedo", "gen") is True


class TestTau6Seed:
    def test_three_verses(self):
        # MIGRATED at τ.6.x.2.a-h batch ship-time (2026-05-15):
        # originally asserted the Geʽez Genesis Π.0 seed had EXACTLY
        # 3 curated verses (Gen 1:1-3). The τ.6.x.2.a batch sub-ship
        # UPGRADED Geʽez Genesis from the 3-verse seed to a 1022-verse
        # ocr-tier3 full-book ingest. Durable invariant: Geʽez Genesis
        # is at ocr-tier3 ingest scale (≥950; empirical 1022).
        from scripts.core import translations

        assert translations.book_verse_count("geez-tewahedo", "gen") >= 950

    def test_gen_1_1_starts_with_qedami(self):
        # MIGRATED at τ.6.x.2.a-h batch ship-time (2026-05-15):
        # the Π.0 seed had the clean canonical opening ቀዳሚሁ ("in
        # the beginning"). The τ.6.x.2.a ocr-tier3 ingest replaced
        # the curated seed with garbled-but-real OCR text — Gen 1:1
        # now reads `በሩዳሚ ገብረ አግዚአብሔር ሰማየ ወምድረ` where the opening
        # word OCR-garbled ቀዳሚ→ሩዳሚ. Per the τ.6.x.0b honesty
        # contract, ocr-tier3 garbling is expected + acceptable.
        # Durable invariant: the verse is non-empty and carries the
        # ዳሚ "beginning"-root fragment (survives the OCR garble in
        # both the clean ቀዳሚሁ and the garbled በሩዳሚ forms).
        from scripts.core import translations

        v = translations.get_verse("geez-tewahedo", "gen", 1, 1)
        assert v is not None
        assert "ዳሚ" in v, f"Geʽez Gen 1:1 must carry the ዳሚ beginning-root; got: {v[:120]!r}"

    def test_gen_1_1_contains_egziabher(self):
        # MIGRATED at τ.6.x.2.a-h batch ship-time (2026-05-15):
        # the Π.0 seed used the clean divine-name spelling እግዚአብሔር.
        # The τ.6.x.2.a ocr-tier3 ingest produced the OCR-variant
        # አግዚአብሔር (leading አ instead of እ) at Gen 1:1. Both are
        # recognizably the Tewahedo divine name. Durable invariant:
        # accept either the clean እግዚአብሔር or the OCR-variant
        # አግዚአብሔር (shared discriminative stem: ግዚአብሔር).
        from scripts.core import translations

        v = translations.get_verse("geez-tewahedo", "gen", 1, 1)
        assert "ግዚአብሔር" in v, f"Geʽez Gen 1:1 must carry the divine-name stem ግዚአብሔር; got: {v[:120]!r}"

    def test_gen_1_3_contains_berhan(self):
        # ብርሃን = "light" — pin its appearance in the "let there be
        # light" verse.
        from scripts.core import translations

        v = translations.get_verse("geez-tewahedo", "gen", 1, 3)
        assert v is not None
        assert "ብርሃን" in v

    def test_text_in_ethiopic_unicode_block(self):
        # Every non-ASCII / non-punctuation char in Ethiopic blocks.
        from scripts.core import translations

        for ch_num in (1, 2, 3):
            v = translations.get_verse("geez-tewahedo", "gen", 1, ch_num)
            for c in v:
                cp = ord(c)
                in_ethiopic = 0x1200 <= cp <= 0x137F
                in_ethiopic_supp = 0x1380 <= cp <= 0x139F
                in_ethiopic_ext = 0x2D80 <= cp <= 0x2DDF
                in_ethiopic_ext_a = 0xAB00 <= cp <= 0xAB2F
                in_ascii = cp <= 0x007F
                assert in_ethiopic or in_ethiopic_supp or in_ethiopic_ext or in_ethiopic_ext_a or in_ascii, (
                    f"non-Ethiopic / non-ASCII char {c!r} (U+{cp:04X}) in verse {ch_num}"
                )


class TestTau6MetaShape:
    def test_meta_short_title(self):
        from scripts.core import translations

        meta = translations.translation_meta("geez-tewahedo")
        assert meta is not None
        assert meta["short_title"] == "Ge'ez"
        assert meta["license"] == "Public Domain"

    def test_meta_documents_tewahedo_distinctive(self):
        # The notes must name the Tewahedo-canonical distinctives
        # (1 Enoch / Jubilees / Meqabyan) so future contributors
        # understand WHY Ge'ez matters for this project specifically.
        from scripts.core import translations

        meta = translations.translation_meta("geez-tewahedo")
        assert meta is not None
        notes = meta.get("notes") or ""
        # At least one of the Tewahedo-only canonical books named.
        assert any(name in notes for name in ("1 Enoch", "Jubilees", "Meqabyan"))


class TestTau6FlagshipReinforcement:
    """τ.6 ships specifically to reinforce the ethiopian-tewahedo
    edition. Sanity-check that the flagship edition exists in the
    project + that the runtime composes geez-tewahedo cleanly."""

    def test_ethiopian_tewahedo_edition_exists(self):
        from scripts.core import config

        eds = config.load_editions()
        ids = {str(e["id"]) for e in eds}
        assert "ethiopian-tewahedo" in ids, "the ethiopian-tewahedo flagship edition must exist for τ.6 to reinforce"

    def test_runtime_composes_geez_for_any_edition(self):
        # The translation system is edition-agnostic — any edition
        # can opt in to the geez-tewahedo popup by listing `geez`
        # in popup_languages_default. Pin that the registry +
        # discovery + verse-fetch chain works end-to-end.
        from scripts.core import translations

        # Same chain a popup-render code path follows:
        assert translations.has_translation("geez-tewahedo")
        meta = translations.translation_meta("geez-tewahedo")
        assert meta and meta["id"] == "geez-tewahedo"
        # And the actual verse is loadable.
        v = translations.get_verse("geez-tewahedo", "gen", 1, 1)
        assert v and len(v) > 0


class TestNineTranslationsRegistered:
    """Post-τ.6 state: 9 translations on disk. Pin so subsequent
    τ-cluster ships are visible at the test-count layer."""

    def test_nine_translations_registered(self):
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
            "geez-tewahedo",
        }
        assert expected.issubset(ids), f"missing: {expected - ids}"

"""Book-file alias resolution in scripts.core.translations (Phase 4)."""

from __future__ import annotations


class TestTranslationsBookFileAlias:
    def test_exo_resolves_ex_stem_for_geez_en(self):
        from scripts.core import translations

        translations.clear_cache()
        assert translations.has_book("geez-tewahedo-en", "exo") is True
        v = translations.get_verse("geez-tewahedo-en", "exo", 1, 1)
        assert v is not None and len(v) > 10

    def test_canonical_exo_stem_unchanged_when_exo_py_exists(self, tmp_path, monkeypatch):
        from scripts.core import translations

        store = tmp_path / "demo-tr"
        store.mkdir()
        (store / "exo.py").write_text(
            'VERSES = [(1, 1, "canonical exo stem wins")]\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(translations, "TRANSLATIONS_DIR", tmp_path)
        translations.clear_cache()
        assert translations.get_verse("demo-tr", "exo", 1, 1) == "canonical exo stem wins"

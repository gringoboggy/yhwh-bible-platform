"""Per-edition theme assignment — every edition declares a theme so its built
EPUB carries a distinct house style (build_edition appends
content/themes/<theme>.css at build time). See
docs/superpowers/specs/2026-05-22-themes-and-multitranslation-popups-design.md."""

from __future__ import annotations

import zipfile
from pathlib import Path

from scripts.core import config

EXPECTED_THEMES = {
    "ethiopian-tewahedo": "classic",
    "anglican-bcp": "classic",
    "standalone-geez": "classic",
    "standalone-amharic": "classic",
    "lutheran-confessional": "scholarly",
    "catholic-study": "devotional",
    "eastern-orthodox": "devotional",
    "coptic-orthodox": "devotional",
    "evangelical-reformed": "modern",
}


class TestPerEditionThemes:
    def test_every_edition_declares_expected_theme(self):
        eds = config.editions_by_id()
        for ed_id, theme in EXPECTED_THEMES.items():
            assert ed_id in eds, f"edition {ed_id!r} missing from editions.yaml"
            assert eds[ed_id].get("theme") == theme, (
                f"{ed_id}: expected theme {theme!r}, got {eds[ed_id].get('theme')!r}"
            )

    def test_theme_css_files_exist(self):
        repo = Path(config.__file__).resolve().parents[2]
        for theme in set(EXPECTED_THEMES.values()):
            assert (repo / "content" / "themes" / f"{theme}.css").is_file(), f"content/themes/{theme}.css missing"


class TestThemeReachesEpub:
    """The config change must actually reach the built EPUB: a `modern`-themed
    edition's stylesheet should carry the appended modern theme block."""

    def test_modern_themed_build_appends_modern_css(self, tmp_path, monkeypatch):
        import scripts.build_edition as be
        from scripts.core import build_cache

        # Hermetic: bypass the persistent build cache.
        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)

        all_kinds = config.load_kinds()
        stats = be.build_one("evangelical-reformed", tmp_path, "theme-test", all_kinds, force=True)
        epub = Path(stats["output_path"])
        assert epub.is_file()

        with zipfile.ZipFile(epub) as zf:
            css_name = next(n for n in zf.namelist() if n.endswith("stylesheet.css"))
            css = zf.read(css_name).decode("utf-8")

        assert "=== theme: modern ===" in css, "modern theme block not appended to the edition stylesheet"
        assert ("-apple-system" in css) or ("#2563eb" in css), "modern theme CSS rules missing from the stylesheet"

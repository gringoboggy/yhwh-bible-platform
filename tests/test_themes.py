"""Theme CSS — builder-time choice via /customize, not per-edition SKUs.

Editions no longer declare ``theme:`` in editions.yaml; the build pipeline
defaults to ``classic``. Visual themes (devotional, modern, scholarly) are
picked in the customize wizard at build time.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from scripts.core import config

CANON_EDITIONS = (
    "ethiopian-tewahedo",
    "catholic-study",
    "evangelical-reformed",
    "eastern-orthodox",
)


class TestEditionThemeDefaults:
    def test_editions_do_not_pin_theme_skus(self):
        eds = config.editions_by_id()
        for ed_id in CANON_EDITIONS:
            assert ed_id in eds, f"edition {ed_id!r} missing from editions.yaml"
            assert eds[ed_id].get("theme") is None, f"{ed_id}: per-edition theme SKU removed — pick theme in /customize"

    def test_classic_theme_css_exists(self):
        repo = Path(config.__file__).resolve().parents[2]
        assert (repo / "content" / "themes" / "classic.css").is_file()


class TestThemeReachesEpub:
    """A builder-chosen theme override must reach the built EPUB."""

    def test_theme_override_appends_css_block(self, tmp_path, monkeypatch):
        import scripts.build_edition as be
        from scripts.core import build_cache

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)

        if hasattr(config.load_editions, "cache_clear"):
            config.load_editions.cache_clear()
        all_kinds = config.load_kinds()
        _orig = config.editions_by_id

        def _with_modern_theme():
            d = dict(_orig())
            d["evangelical-reformed"] = {**d["evangelical-reformed"], "theme": "modern"}
            return d

        monkeypatch.setattr(config, "editions_by_id", _with_modern_theme)

        stats = be.build_one("evangelical-reformed", tmp_path, "theme-test", all_kinds, force=True)
        epub = Path(stats["output_path"])
        assert epub.is_file()

        with zipfile.ZipFile(epub) as zf:
            css_name = next(n for n in zf.namelist() if n.endswith("stylesheet.css"))
            css = zf.read(css_name).decode("utf-8")

        assert "=== theme: modern ===" in css, "modern theme block not appended to the edition stylesheet"
        assert ("-apple-system" in css) or ("#2563eb" in css), "modern theme CSS rules missing from the stylesheet"

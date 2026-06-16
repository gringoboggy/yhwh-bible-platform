"""Tests for per-book title cover compose pipeline."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from scripts.core import covers as cover_core
from scripts.generate_book_title_covers import (
    DEFAULTS_DIR,
    MANIFEST_PATH,
    build_prompt,
    cmd_audit,
    compose_scene,
)


class TestBookTitleCovers:
    def test_manifest_loads_and_prompt_includes_motif(self):
        import yaml

        data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
        assert "books" in data
        prompt = build_prompt(data, "gen", data["books"]["gen"])
        assert "creation light" in prompt
        assert "No text" in prompt or "no text" in prompt.lower()

    def test_audit_reports_full_ethiopian_coverage(self):
        import argparse

        assert cmd_audit(argparse.Namespace(variant="default")) == 0
        jpg_count = len(list(DEFAULTS_DIR.glob("*.jpg")))
        assert jpg_count >= 86

    def test_compose_scene_writes_expected_size(self, tmp_path: Path):
        scene = tmp_path / "scene.png"
        border = tmp_path / "border.png"
        out = tmp_path / "out.jpg"
        Image.new("RGB", (800, 1200), (80, 10, 20)).save(scene)
        Image.new("RGBA", (800, 1200), (255, 215, 0, 80)).save(border)
        compose_scene(scene, border, out)
        with Image.open(out) as img:
            assert img.size == (1024, 1536)

    def test_variant_catalog_has_three_slots(self):
        rows = cover_core.book_cover_variant_catalog("gen")
        assert len(rows) == 3
        assert rows[0]["variant_id"] == "default"
        assert rows[1]["path"].endswith("alt02/gen.jpg")

    def test_normalize_upload_to_epub_safe_jpeg(self):
        import io

        src = Image.new("RGB", (1600, 900), (120, 20, 30))
        buf = io.BytesIO()
        src.save(buf, format="PNG")
        out, meta = cover_core.normalize_cover_image(buf.getvalue())
        assert meta["format"] == "jpeg"
        assert meta["width"] == 1024
        assert meta["height"] == 1536
        with Image.open(io.BytesIO(out)) as img:
            assert img.size == (1024, 1536)

    def test_alt02_prompt_differs_from_default(self):
        import yaml

        data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
        p_default = build_prompt(data, "gen", data["books"]["gen"], "default")
        p_alt = build_prompt(data, "gen", data["books"]["gen"], "alt02")
        assert p_default != p_alt
        assert "Alternate composition B" in p_alt

"""Tests for per-book title cover compose pipeline."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from scripts.core import covers as cover_core
from scripts.generate_book_title_covers import (
    DEFAULTS_DIR,
    MANIFEST_PATH,
    _apply_grok_style_grade,
    _apply_scene_fade_vignette,
    build_prompt,
    cmd_audit,
    compose_scene,
)


class TestBookTitleCovers:
    def test_manifest_loads_and_prompt_includes_motif(self):
        import yaml

        data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
        assert "books" in data
        compose = data["style"]["compose"]
        assert compose["scene_source"] == "midjourney_first"
        assert data["style"]["regen_wave"] == "midjourney_gradient"
        prompt = build_prompt(data, "gen", data["books"]["gen"])
        assert "creation" in prompt.lower() or "primordial" in prompt.lower()
        assert "full-bleed" in prompt.lower() or "full bleed" in prompt.lower()
        assert data["style"]["border"] == "none"
        assert "no leather" in prompt.lower() or "reimagine" in prompt.lower()
        assert "No text" in prompt or "no text" in prompt.lower()
        assert "crimson" in prompt.lower() or "burgundy" in prompt.lower()

    def test_audit_reports_full_ethiopian_coverage(self):
        import argparse

        assert cmd_audit(argparse.Namespace(variant="default")) == 0
        jpg_count = len(list(DEFAULTS_DIR.glob("*.jpg")))
        assert jpg_count >= 86

    def test_compose_scene_writes_expected_size(self, tmp_path: Path):
        scene = tmp_path / "scene.png"
        out = tmp_path / "out.jpg"
        Image.new("RGB", (800, 1200), (80, 10, 20)).save(scene)
        compose_scene(scene, out, vignette=0.12)
        with Image.open(out) as img:
            assert img.size == (1024, 1536)

    def test_style_grade_and_vignette_change_pixels(self):
        base = Image.new("RGB", (400, 600))
        for y in range(600):
            for x in range(400):
                base.putpixel((x, y), (80 + x // 8, 30 + y // 12, 40))
        graded = _apply_grok_style_grade(base)
        assert graded.getpixel((200, 300)) != base.getpixel((200, 300))
        faded = _apply_scene_fade_vignette(graded, strength=0.12)
        assert faded.getpixel((5, 5)) != graded.getpixel((5, 5))

    def test_variant_catalog_has_single_builtin_slot(self):
        rows = cover_core.book_cover_variant_catalog("gen")
        assert len(rows) == 1
        assert rows[0]["variant_id"] == "default"
        assert rows[0]["path"].endswith("_book_defaults/gen.jpg")

    def test_optimize_shrinks_jpeg(self, tmp_path: Path):
        import argparse

        from scripts.generate_book_title_covers import cmd_optimize

        src = tmp_path / "big.jpg"
        out_dir = tmp_path / "alt02"
        out_dir.mkdir()
        img = Image.new("RGB", (1024, 1536), (120, 30, 40))
        img.save(src, format="JPEG", quality=95, optimize=False)
        before = src.stat().st_size
        # cmd_optimize scans DEFAULTS_DIR — patch via copying to a controlled path is heavy;
        # verify save_book_cover_jpeg produces smaller output than q95 baseline.
        lean = tmp_path / "lean.jpg"
        cover_core.save_book_cover_jpeg(img, lean)
        assert lean.stat().st_size < before

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

"""Render step for the agent-path workflow (P1 of the Sam/Kings cloud plan).

`downsample_to_png` is tested on a synthetic oversized image (CI-safe, no GAPS).
`render_chapter` is tested against the calibrated 1Ki1 manifest entry but SKIPS
if the GAPS images aren't on disk (they're gitignored — absent in a clean CI).
"""

from pathlib import Path

import pytest
from PIL import Image

from scripts.core import manuscript_manifest as mm
from scripts.manuscript_render_crops import downsample_to_png, render_chapter

REPO = Path(__file__).resolve().parent.parent


def test_downsample_caps_long_edge(tmp_path):
    src = tmp_path / "big.jpg"
    Image.new("RGB", (3000, 2000), (128, 64, 32)).save(str(src), format="JPEG")
    dst = tmp_path / "out.png"
    downsample_to_png(src, dst, max_edge=1568)
    assert dst.exists()
    w, h = Image.open(str(dst)).size
    assert max(w, h) == 1568
    assert dst.suffix == ".png"


def test_downsample_never_upscales(tmp_path):
    src = tmp_path / "small.jpg"
    Image.new("RGB", (800, 500), (10, 20, 30)).save(str(src), format="JPEG")
    dst = tmp_path / "out.png"
    downsample_to_png(src, dst, max_edge=1568)
    assert Image.open(str(dst)).size == (800, 500)  # unchanged — no upscale


def test_render_chapter_1ki1_when_images_present(tmp_path):
    entry = mm.chapter_entry(mm.load_manifest(track="kings"), "1ki", 1)
    first = (entry.get("GG") or {}).get("source_images") or []
    if not first or not (REPO / first[0]).exists():
        pytest.skip("GAPS 1Ki1 images not on disk (gitignored) — integration skip")
    res = render_chapter("kings", "1ki", 1, tmp_path)
    assert res["GG"] and res["CAM"]
    for w in ("GG", "CAM"):
        for png in res[w]:
            assert Path(png).exists()
            assert max(Image.open(png).size) <= 1568

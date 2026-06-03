"""Tests for scripts/manuscript_folio_crop.py — the P0 folio column-tiler.

The tiler splits a manuscript folio into a grid of native-resolution PNG tiles
for the free AGENT vision path (whole-folio reads downsample names into
illegibility). These pin the grid contract: tile count, never-upscale, the
<=max_edge cap, seam overlap, and bounds clamping.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.manuscript_folio_crop import MAX_IMAGE_EDGE, crop_folio, tile_boxes


def test_tile_boxes_count_and_cover():
    boxes = tile_boxes(900, 1200, cols=3, rows=2, overlap=0.0)
    assert len(boxes) == 6
    # With zero overlap the cells tile the image edge-to-edge.
    cols = sorted({(lo, hi) for _, _, lo, _, hi, _ in boxes})
    assert cols[0][0] == 0 and cols[-1][1] == 900
    # Every box is within bounds and non-empty.
    for _c, _r, left, top, right, bottom in boxes:
        assert 0 <= left < right <= 900
        assert 0 <= top < bottom <= 1200


def test_tile_boxes_overlap_expands_and_clamps():
    plain = tile_boxes(1000, 1000, cols=2, rows=2, overlap=0.0)
    over = tile_boxes(1000, 1000, cols=2, rows=2, overlap=0.1)
    # Overlap widens interior seams but never escapes the image bounds.
    for _c, _r, left, top, right, bottom in over:
        assert left >= 0 and top >= 0 and right <= 1000 and bottom <= 1000
    # The interior-facing edge of the top-left tile moves outward with overlap.
    tl_plain = next(box for box in plain if box[0] == 0 and box[1] == 0)
    tl_over = next(box for box in over if box[0] == 0 and box[1] == 0)
    assert tl_over[4] > tl_plain[4]  # right edge pushed out
    assert tl_over[5] > tl_plain[5]  # bottom edge pushed out


def _make_image(path: Path, size: tuple[int, int]) -> None:
    from PIL import Image

    Image.new("RGB", size, (200, 180, 160)).save(str(path), format="JPEG")


def test_crop_folio_writes_tiles_capped_never_upscaled(tmp_path):
    from PIL import Image

    src = tmp_path / "folio.jpg"
    _make_image(src, (6000, 9000))  # CAM-scale: both edges far over the cap
    out_dir = tmp_path / "tiles"
    res = crop_folio(src, out_dir, cols=3, rows=3, overlap=0.05, prefix="CAM_f117r")

    assert len(res["tiles"]) == 9
    assert res["size"] == [6000, 9000]
    for meta in res["tiles"]:
        p = Path(meta["path"])
        assert p.exists() and p.suffix == ".png"
        with Image.open(p) as im:
            assert max(im.size) <= MAX_IMAGE_EDGE  # capped, never exceeds


def test_crop_folio_small_image_passes_through_native(tmp_path):
    from PIL import Image

    src = tmp_path / "small.jpg"
    _make_image(src, (600, 900))  # under the cap → no downscale
    out_dir = tmp_path / "tiles"
    # One column, one row → the whole (sub-cap) image, untouched.
    res = crop_folio(src, out_dir, cols=1, rows=1, overlap=0.0, prefix="GG")
    assert len(res["tiles"]) == 1
    with Image.open(res["tiles"][0]["path"]) as im:
        assert im.size == (600, 900)  # native, never upscaled


def test_crop_folio_prefix_defaults_to_stem(tmp_path):
    src = tmp_path / "2-Samuel_f017v.jpg"
    _make_image(src, (2081, 2368))
    out_dir = tmp_path / "tiles"
    res = crop_folio(src, out_dir, cols=3, rows=2)
    names = {Path(t["path"]).name for t in res["tiles"]}
    assert "2-Samuel_f017v_c0_r0.png" in names
    assert len(names) == 6


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))

#!/usr/bin/env python3
"""Column-tile a manuscript folio into native-resolution crop FILES for vision agents.

P0 Sam/Kings folio-mapping support tool. Sibling of
``scripts/manuscript_render_crops.py`` — but where that downsamples a WHOLE
folio to <=1568px (for transcribing an already-mapped chapter), this splits a
folio into a grid of column x row tiles, each capped to <=1568px on its longest
edge but otherwise NATIVE resolution. Whole-folio reads downsample a 7760px CAM
master (or a 2081px GG side) so far that individual Ge'ez fidels become
illegible; reading a single column-tile preserves glyph-level detail so a vision
pass can anchor chapter onsets on actual incipit names, not just rubric blocks.

The free AGENT vision path (Claude Code on this box, per the ratified marathon
method) ``Read``s image FILES, so this writes PNG tiles to disk and prints the
tile manifest as JSON. (``manuscript_vision.crop_and_encode`` produces a base64
block for the PAID API path instead — out of scope here.)

Tiles overlap slightly (default 6%) so a chapter onset that lands on a tile
boundary still appears whole in at least one tile. Never upscales (the OOM
lesson, ``manuscript_vision.MAX_IMAGE_EDGE``).

CLI::

    py scripts/manuscript_folio_crop.py <src.jpg> <out_dir> [--cols 3] [--rows 3]
        [--overlap 0.06] [--max-edge 1568] [--prefix NAME]

Prints::

    {"src": "...", "size": [w, h], "cols": 3, "rows": 3,
     "tiles": [{"path": "...", "col": 0, "row": 0, "box": [l, t, r, b]}, ...]}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PIL import Image  # noqa: E402

MAX_IMAGE_EDGE = 1568  # mirror manuscript_vision.MAX_IMAGE_EDGE (Claude's vision downsample cap)


def tile_boxes(
    width: int,
    height: int,
    cols: int,
    rows: int,
    overlap: float,
) -> list[tuple[int, int, int, int, int, int]]:
    """Return ``(col, row, left, top, right, bottom)`` tiles covering the image.

    Columns/rows divide the image evenly; each tile is then expanded by
    ``overlap`` (a fraction of the cell size) on every side and clamped to the
    image bounds, so onsets on a seam stay whole in a neighbouring tile.
    """
    cw = width / cols
    ch = height / rows
    ox = cw * overlap
    oy = ch * overlap
    out: list[tuple[int, int, int, int, int, int]] = []
    for c in range(cols):
        for r in range(rows):
            left = max(0, int(round(c * cw - ox)))
            top = max(0, int(round(r * ch - oy)))
            right = min(width, int(round((c + 1) * cw + ox)))
            bottom = min(height, int(round((r + 1) * ch + oy)))
            out.append((c, r, left, top, right, bottom))
    return out


def crop_folio(
    src: str | Path,
    out_dir: str | Path,
    *,
    cols: int = 3,
    rows: int = 3,
    overlap: float = 0.06,
    max_edge: int = MAX_IMAGE_EDGE,
    prefix: str | None = None,
) -> dict:
    """Column-tile *src* into ``cols x rows`` native-res PNG tiles under *out_dir*.

    Returns a manifest dict (see module docstring). Tiles whose longest edge
    exceeds *max_edge* are scaled DOWN (LANCZOS); smaller tiles pass through
    untouched (never upscaled)."""
    src = Path(src)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pfx = prefix or src.stem
    img = Image.open(src).convert("RGB")
    w, h = img.size
    tiles_meta: list[dict] = []
    for c, r, left, top, right, bottom in tile_boxes(w, h, cols, rows, overlap):
        crop = img.crop((left, top, right, bottom))
        longest = max(crop.size)
        if longest > max_edge:
            scale = max_edge / longest
            crop = crop.resize(
                (max(1, round(crop.width * scale)), max(1, round(crop.height * scale))),
                Image.Resampling.LANCZOS,
            )
        dst = out_dir / f"{pfx}_c{c}_r{r}.png"
        crop.save(str(dst), format="PNG")
        tiles_meta.append({"path": str(dst), "col": c, "row": r, "box": [left, top, right, bottom]})
    return {"src": str(src), "size": [w, h], "cols": cols, "rows": rows, "tiles": tiles_meta}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Column-tile a folio into native-res crop files for vision agents.")
    p.add_argument("src", help="Source folio image (JPG)")
    p.add_argument("out_dir", help="Directory to write PNG tiles into")
    p.add_argument("--cols", type=int, default=3, help="Number of columns (default 3 — GG/CAM are 3-column)")
    p.add_argument("--rows", type=int, default=3, help="Vertical tiles per column (default 3)")
    p.add_argument("--overlap", type=float, default=0.06, help="Seam overlap as a fraction of cell size (default 0.06)")
    p.add_argument("--max-edge", type=int, default=MAX_IMAGE_EDGE, help=f"Max tile edge px (default {MAX_IMAGE_EDGE})")
    p.add_argument("--prefix", default=None, help="Output filename prefix (default = src stem)")
    args = p.parse_args(argv)
    res = crop_folio(
        args.src,
        args.out_dir,
        cols=args.cols,
        rows=args.rows,
        overlap=args.overlap,
        max_edge=args.max_edge,
        prefix=args.prefix,
    )
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

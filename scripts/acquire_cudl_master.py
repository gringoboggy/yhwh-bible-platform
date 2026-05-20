#!/usr/bin/env python3
"""CUDL IIIF master-image acquisition (audit U-belt 2026-05-20, U7).

Fetches a single CUDL IIIF master image by view-id, region-tiles past the
1503x2000 single-delivery cap, stitches with Pillow, and writes the
stitched JPG to disk. Used to pre-pull the Cambridge Add. 1570 Kings band
(f126r-f146v, ~42 folios) BEFORE the per-chapter C-4 step, so the
remaining 43 Kings chapters skip the IIIF fetch + tile-stitch overhead
(saves ~30 min per chapter).

Per memory ``cudl-iiif-access``:
- Manifest URL: ``https://cudl.lib.cam.ac.uk/iiif/MS-ADD-01570``
- Image base:   ``https://images.lib.cam.ac.uk/iiif/MS-ADD-01570-000-{view:05d}.jp2``
- Region tile:  ``{base}/{x},{y},{w},{h}/full/0/default.jpg``
- Cap:          single delivery up to 1503x2000; pass tile_size <= 1900px
- info.json:    ``{base}/info.json`` returns ``{width, height, ...}``

Folio anchor: 1 Sam 1 = view 215 = f106r. Kings (3-4 Reigns) follows
2 Samuel; CAM low-res ``Kings_f126r..f146v`` crops give the approximate
Kings folio band. View numbers for individual Kings folios are determined
by VISION against the low-res band (ToC mislabels Reigns — never trust
the manifest label).

Attribution: CC BY-NC, "Cambridge University Library" — record in
``_source.yaml`` provenance at Stage 2 (Phase-3 render).

CLI usage:

    py acquire_cudl_master.py 215 GAPS/2_Kings/Cambridge-Add-1570-hires/MS-ADD-01570_f106r_hires.jpg

Programmatic usage:

    from scripts.acquire_cudl_master import fetch_master
    fetch_master(view_id=215, output_path="path/to/output.jpg")

Bulk pre-pull recipe (run once, drops C-4 IIIF time to zero for the
remaining Kings chapters). View numbers below ESTIMATED from anchor
f106r=view215 assuming 2 views/folio (recto+verso) — VERIFY by vision
on the first few before bulk-running:

    # Smoke first folio to confirm view-number arithmetic:
    py scripts/acquire_cudl_master.py 255 GAPS/2_Kings/Cambridge-Add-1570-hires/MS-ADD-01570_f126r_hires.jpg

    # If smoke confirms f126r at view 255, bulk-pull views 255-296:
    for view in {255..296}; do
        folio_num=$(( 126 + (view - 255) / 2 ))
        side=$(( (view - 255) % 2 == 0 ? "r" : "v" ))
        py scripts/acquire_cudl_master.py $view \\
            GAPS/2_Kings/Cambridge-Add-1570-hires/MS-ADD-01570_f${folio_num}${side}_hires.jpg
    done

CC BY-NC requires not selling re-distributions of the images; the
project's free-public Bible build (memory ``project_free_public_pivot``)
complies. Provenance recorded in Stage-2 ``_source.yaml`` per spec §9.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

from PIL import Image

from scripts.core import http

CUDL_HOST = "images.lib.cam.ac.uk"
CUDL_BASE = f"https://{CUDL_HOST}/iiif/MS-ADD-01570-000"
ALLOWLIST = (CUDL_HOST, "cudl.lib.cam.ac.uk")
DEFAULT_TILE_SIZE = 1900  # below the 2000 single-delivery cap


def _image_url(view_id: int) -> str:
    return f"{CUDL_BASE}-{view_id:05d}.jp2"


def fetch_info(view_id: int) -> dict:
    """Fetch the IIIF info.json for *view_id* and return the parsed dict.

    Raises ``http.HttpError`` after retries exhausted.
    """
    url = f"{_image_url(view_id)}/info.json"
    body = http.get(url, allowlist=ALLOWLIST)
    return json.loads(body.decode("utf-8"))


def _tile_bounds(width: int, height: int, tile_size: int) -> list[tuple[int, int, int, int]]:
    """Compute the (x, y, w, h) tile rectangles covering (width, height).

    Tiles tile in row-major order, sized at most ``tile_size`` per side,
    with the right-most + bottom-most tiles trimmed to fit.
    """
    out: list[tuple[int, int, int, int]] = []
    y = 0
    while y < height:
        h = min(tile_size, height - y)
        x = 0
        while x < width:
            w = min(tile_size, width - x)
            out.append((x, y, w, h))
            x += tile_size
        y += tile_size
    return out


def fetch_tile(view_id: int, x: int, y: int, w: int, h: int) -> bytes:
    """Fetch a single IIIF region tile as JPG bytes.

    Uses the documented IIIF region+size syntax:
    ``{base}/{x},{y},{w},{h}/full/0/default.jpg``.
    """
    url = f"{_image_url(view_id)}/{x},{y},{w},{h}/full/0/default.jpg"
    return http.get(url, allowlist=ALLOWLIST)


def fetch_master(
    view_id: int,
    output_path,
    *,
    tile_size: int = DEFAULT_TILE_SIZE,
    quality: int = 90,
) -> dict:
    """Fetch and stitch the complete master image for *view_id*.

    Parameters
    ----------
    view_id
        IIIF view number (per memory ``cudl-iiif-access``; anchor
        f106r=view 215).
    output_path
        Destination path for the stitched JPG. Parent directories are
        created as needed.
    tile_size
        Maximum tile dimension in pixels. Must be < the IIIF single-
        delivery cap (~2000 for MS-ADD-01570); defaults to 1900.
    quality
        Final JPG quality (1-95). Default 90 mirrors the existing
        per-chapter pulls.

    Returns
    -------
    A dict ``{view_id, output_path, width, height, tile_count, bytes_written}``
    summarising the operation.

    Raises
    ------
    ``http.HttpError`` on persistent network failures.
    """
    info = fetch_info(view_id)
    width, height = info["width"], info["height"]
    tiles = _tile_bounds(width, height, tile_size)
    stitched = Image.new("RGB", (width, height))
    for x, y, w, h in tiles:
        tile_bytes = fetch_tile(view_id, x, y, w, h)
        tile_img = Image.open(io.BytesIO(tile_bytes))
        # IIIF returns the exact region pixels — paste at (x, y).
        stitched.paste(tile_img, (x, y))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    stitched.save(str(out), "JPEG", quality=quality)
    bytes_written = out.stat().st_size

    return {
        "view_id": view_id,
        "output_path": str(out),
        "width": width,
        "height": height,
        "tile_count": len(tiles),
        "bytes_written": bytes_written,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("view_id", type=int, help="IIIF view number")
    parser.add_argument("output_path", help="Destination JPG path")
    parser.add_argument(
        "--tile-size",
        type=int,
        default=DEFAULT_TILE_SIZE,
        help=f"Max tile dimension in px (default: {DEFAULT_TILE_SIZE})",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=90,
        help="JPG quality 1-95 (default: 90)",
    )
    args = parser.parse_args(argv)
    try:
        result = fetch_master(
            args.view_id,
            args.output_path,
            tile_size=args.tile_size,
            quality=args.quality,
        )
    except http.HttpError as e:
        print(f"FETCH FAILED: {e}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

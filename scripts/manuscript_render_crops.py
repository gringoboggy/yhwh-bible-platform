#!/usr/bin/env python3
"""Render a chapter's CAM + GG folio images to downsampled PNGs for vision agents.

P1 of the Sam/Kings cloud plan
(``plans/2026-06-02-samkings-cloud-agent-workflow-and-run-plan.md``). The batch
Workflow's vision sub-agents ``Read`` these PNGs. Reads the chapter's manifest
entry, downsamples each witness's folio image to ``<= MAX_IMAGE_EDGE`` (1568 px,
**never upscaled** — Claude's vision pipeline downsamples larger inputs, and a
bigger crop only burns harness memory, the OOM lesson), and writes
``<out_dir>/<book><chapter>/<witness>_<folio>.png``.

Emits the rendered-path map as JSON on stdout so the Workflow can hand each
witness's crop paths to its blind passes::

    {"GG": ["/…/GG_f028v.png", …], "CAM": [...],
     "folios": {"GG": ["f028v", …], "CAM": [...]},
     "source_images": {"GG": ["GAPS/…"], "CAM": [...]}}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from PIL import Image  # noqa: E402

from scripts.core import manuscript_manifest as mm  # noqa: E402
from scripts.core import manuscript_vision as mv  # noqa: E402


def downsample_to_png(src: Path, dst: Path, max_edge: int = mv.MAX_IMAGE_EDGE) -> None:
    """Load *src*, downsample so the longest edge is ``<= max_edge`` (never
    upscale), write *dst* as PNG. Mirrors ``manuscript_vision.crop_and_encode``'s
    cap (LANCZOS), but to a file rather than a base64 API block."""
    img = mv.load_image(str(src))  # RGB
    longest = max(img.size)
    if longest > max_edge:
        scale = max_edge / longest
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(dst), format="PNG")


def render_chapter(track: str, book: str, chapter: int, out_dir: Path, max_edge: int = mv.MAX_IMAGE_EDGE) -> dict:
    """Render both witnesses' folios for one chapter to PNGs under *out_dir*.

    Returns a dict of rendered PNG paths + folio sigla + source-image relpaths
    per witness (``GG``/``CAM``). Raises FileNotFoundError if a manifest-listed
    source image is absent on disk (the manifest must be folio-mapped first — P0)."""
    man = mm.load_manifest(track=track)
    entry = mm.chapter_entry(man, book, chapter)
    images = {
        "GG": (entry.get("GG") or {}).get("source_images") or [],
        "CAM": (entry.get("CAM") or {}).get("views") or [],
    }
    folio_lists = {
        "GG": (entry.get("GG") or {}).get("folios") or [],
        "CAM": (entry.get("CAM") or {}).get("folios") or [],
    }
    out: dict = {"GG": [], "CAM": [], "folios": {"GG": [], "CAM": []}, "source_images": images}
    for witness, rels in images.items():
        for i, rel in enumerate(rels):
            src = REPO_ROOT / rel
            if not src.exists():
                raise FileNotFoundError(f"{book} {chapter} {witness}: source image missing on disk: {rel}")
            folio = folio_lists[witness][i] if i < len(folio_lists[witness]) else src.stem
            dst = out_dir / f"{book}{chapter}" / f"{witness}_{folio}.png"
            downsample_to_png(src, dst, max_edge=max_edge)
            out[witness].append(str(dst))
            out["folios"][witness].append(folio)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render a chapter's CAM+GG folios to PNG crops for vision agents.")
    p.add_argument("--track", required=True, choices=["samuel", "kings"])
    p.add_argument("--book", required=True)
    p.add_argument("--chapter", type=int, required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--max-edge", type=int, default=mv.MAX_IMAGE_EDGE)
    args = p.parse_args(argv)
    res = render_chapter(args.track, args.book, args.chapter, Path(args.out_dir), max_edge=args.max_edge)
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

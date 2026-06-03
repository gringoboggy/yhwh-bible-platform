#!/usr/bin/env python3
"""Fill one chapter's folio entry in a dual-manuscript manifest (P0 folio-index).

Line-based splice (preserves the YAML's comments/blank-lines/order — PyYAML
round-trip would not). Locates the ``<book>:`` section, then the ``  <chapter>:``
block within it, and replaces that block's GG + CAM folios/images. ``status``
stays ``pending`` (P0 only maps folios; collation runs ``calibrated`` chapters).

Usage::

    py -3 scripts/fill_manifest_entry.py --manifest content/manuscript/samuel/manifest.yaml \\
        --book 1sa --chapter 7 \\
        --gg-folios f005v,f006r   --gg-images <csv of GG image relpaths> \\
        --cam-folios f108v,f109r  --cam-images <csv of CAM image relpaths>

(folios + images are comma-separated and positionally paired per witness.)
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_CHAP_RE = re.compile(r"^  (\d+):\s*$")


def _block(chapter: int, gg_folios, gg_images, cam_folios, cam_images) -> list[str]:
    out = [f"  {chapter}:", "    GG:"]
    out.append("      folios:")
    out += [f"        - {f}" for f in gg_folios]
    out.append("      source_images:")
    out += [f"        - {p}" for p in gg_images]
    out.append("    CAM:")
    out.append("      folios:")
    out += [f"        - {f}" for f in cam_folios]
    out.append("      views:")
    out += [f"        - {p}" for p in cam_images]
    out.append("    status: pending")
    out.append("")  # trailing blank line between chapters
    return out


def fill(manifest: Path, book: str, chapter: int, gg_folios, gg_images, cam_folios, cam_images) -> None:
    lines = manifest.read_text(encoding="utf-8").split("\n")
    book_re = re.compile(rf"^{re.escape(book)}:\s*$")
    bi = next((i for i, ln in enumerate(lines) if book_re.match(ln)), None)
    if bi is None:
        raise SystemExit(f"book '{book}' not found in {manifest}")
    # book section ends at the next top-level (column-0) key
    be = len(lines)
    for i in range(bi + 1, len(lines)):
        if lines[i] and not lines[i].startswith(" ") and lines[i].rstrip().endswith(":"):
            be = i
            break
    # locate the chapter block within the book section
    ci = None
    for i in range(bi + 1, be):
        m = _CHAP_RE.match(lines[i])
        if m and int(m.group(1)) == chapter:
            ci = i
            break
    if ci is None:
        raise SystemExit(f"chapter {chapter} not found in book '{book}'")
    # block runs until the next chapter header (inclusive of its trailing blank)
    ce = be
    for i in range(ci + 1, be):
        if _CHAP_RE.match(lines[i]):
            ce = i
            break
    new_lines = lines[:ci] + _block(chapter, gg_folios, gg_images, cam_folios, cam_images) + lines[ce:]
    manifest.write_text("\n".join(new_lines), encoding="utf-8", newline="\n")
    print(f"filled {book} {chapter}: GG={gg_folios} CAM={cam_folios}")


def _csv(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Fill one chapter's folio manifest entry")
    p.add_argument("--manifest", required=True)
    p.add_argument("--book", required=True)
    p.add_argument("--chapter", type=int, required=True)
    p.add_argument("--gg-folios", required=True)
    p.add_argument("--gg-images", required=True)
    p.add_argument("--cam-folios", required=True)
    p.add_argument("--cam-images", required=True)
    a = p.parse_args(argv)
    fill(
        Path(a.manifest),
        a.book,
        a.chapter,
        _csv(a.gg_folios),
        _csv(a.gg_images),
        _csv(a.cam_folios),
        _csv(a.cam_images),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Deterministic catalog cover-swap — matrix M1 (format-matrix spec §4.2).

Every Downloads-catalog cell is a base build (edition × target_reader) with
the cell's (edition × design × colour) composite swapped into the EPUB's
cover slot. The swap REWRITES the package under ``build_epub.py``'s writer
discipline — mimetype FIRST and STORED, every other entry DEFLATE-9, all
dates pinned to the 1980 zip epoch, 0o644 attrs — because a bare rezip
guarantees neither determinism nor zip discipline (the Mac review's
blocker-#2 trap). Every non-cover byte survives identically, which is what
licenses the light per-variant gates (zip integrity + cover presence) in
place of a full epubcheck per cell.

The replacement cover must be a real JPEG (magic bytes, never the
filename): the OPF cover slot is ``image/jpeg``, so PNG bytes in it are an
epubcheck failure.

Usage:  py -3 scripts/swap_epub_cover.py <base.epub> <cover.jpg> -o <out.epub>
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

# SOI marker — every JPEG stream starts FF D8.
_JPEG_MAGIC = b"\xff\xd8"

# The base master cover's in-package path (apply_edition_cover's slot).
DEFAULT_COVER_ENTRY = "cover.jpeg"

_ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def swap_cover(
    epub_path: Path,
    cover_path: Path,
    out_path: Path,
    *,
    cover_entry: str = DEFAULT_COVER_ENTRY,
) -> Path:
    """Rewrite ``epub_path`` to ``out_path`` with ``cover_entry``'s bytes
    replaced by ``cover_path``'s. Entry order is preserved; every other
    entry's bytes are copied verbatim; the writer discipline matches
    ``build_epub.build`` so the output is reproducible byte-for-byte.

    Raises ``ValueError`` when the package has no ``cover_entry`` (a base
    built without a cover must fail loudly, never ship coverless) or when
    the replacement is not a real JPEG."""
    cover_bytes = cover_path.read_bytes()
    if not cover_bytes.startswith(_JPEG_MAGIC):
        raise ValueError(f"replacement cover is not a JPEG (magic bytes): {cover_path}")

    with zipfile.ZipFile(epub_path) as src:
        names = src.namelist()
        if cover_entry not in names:
            raise ValueError(f"no {cover_entry!r} cover entry in {epub_path.name}; entries start: {names[:5]}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out_path, "w", allowZip64=False) as dst:
            for name in names:
                data = cover_bytes if name == cover_entry else src.read(name)
                zi = zipfile.ZipInfo(name)
                zi.date_time = _ZIP_EPOCH
                zi.external_attr = 0o644 << 16
                zi.create_system = 0  # round-13 #6: pin FAT so cross-OS re-zips match (Win default 0)
                if name == "mimetype":
                    zi.compress_type = zipfile.ZIP_STORED
                    dst.writestr(zi, data)
                else:
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    dst.writestr(zi, data, compresslevel=9)
    return out_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Swap a catalog cover composite into a built EPUB, deterministically.")
    p.add_argument("epub", type=Path, help="base .epub (or .kepub.epub)")
    p.add_argument("cover", type=Path, help="replacement cover JPEG")
    p.add_argument("-o", "--output", type=Path, required=True, help="output path")
    p.add_argument(
        "--entry",
        default=DEFAULT_COVER_ENTRY,
        help=f"in-package cover path (default: {DEFAULT_COVER_ENTRY})",
    )
    args = p.parse_args(argv)
    out = swap_cover(args.epub, args.cover, args.output, cover_entry=args.entry)
    print(f"swapped {args.cover.name} into {out}  ({out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

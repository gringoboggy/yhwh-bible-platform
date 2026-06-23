"""Reproducible-zip metadata helper (round-12 zipfile-byte-repro class).

A build over identical input should produce a byte-identical archive. By
default ``zipfile`` stamps each member's ``date_time`` with the current
wall-clock (``writestr``) or the source file's on-disk mtime (``write``), so
two runs differ byte-for-byte. This module centralizes the fix:

    ZIP_EPOCH                — the pinned 1980-01-01 date_time the shipping
                               EPUB writers (build_epub / kindle_post /
                               swap_epub_cover) already use.
    reproducible_zipinfo()   — a ZipInfo with that epoch + 0o644 perms, for
                               the two previously-UNPINNED shipping writers:
                               press_kit.build_zip and the api/exports
                               All-Editions bundle.

Usage: ``zf.writestr(reproducible_zipinfo(name), data)`` instead of
``zf.writestr(name, data)`` / ``zf.write(path, arcname=name)``.
"""

from __future__ import annotations

import zipfile

# The 1980-01-01 epoch zipfile uses as its minimum representable date_time —
# the same value build_epub.py / kindle_post.py / swap_epub_cover.py pin inline.
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def reproducible_zipinfo(name: str, *, stored: bool = False) -> zipfile.ZipInfo:
    """A ``ZipInfo`` with pinned ``date_time`` + perms for byte-reproducible
    output. ``stored=True`` selects ZIP_STORED (e.g. an EPUB ``mimetype``);
    otherwise ZIP_DEFLATED."""
    info = zipfile.ZipInfo(filename=name, date_time=ZIP_EPOCH)
    info.external_attr = 0o644 << 16
    info.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
    return info

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

# OCF members whose line endings must be normalized so the packaged EPUB is
# byte-identical regardless of the BUILD host OS (round-14 A1). The build's
# text I/O / a CRLF git checkout can leave ``\r\n`` in these text members on
# Windows, while macOS/Linux emit ``\n`` — diverging the bytes (and the
# SHA256SUMS / the KJV golden) cross-machine. Binaries (fonts, images) and the
# ``mimetype`` entry have no extension match and are never touched.
_OCF_TEXT_EXTENSIONS = (".html", ".xhtml", ".xml", ".opf", ".ncx", ".css", ".svg")


def ocf_member_bytes(name: str, data: bytes) -> bytes:
    """Normalize one OCF member's bytes for OS-independent EPUB output.

    For text members (matched by extension), collapse ``\\r\\n`` → ``\\n`` so a
    Windows build is byte-identical to a macOS/Linux build. Binary members and
    the ``mimetype`` entry are returned unchanged. The replace is a no-op on
    POSIX-produced LF bytes, so macOS/Linux output does NOT change — only the
    Windows bytes converge onto the POSIX baseline (a one-time, deliberate
    Windows CRLF→LF re-baseline). Only the exact ``\\r\\n`` pair is collapsed; a
    lone ``\\r`` inside content is left intact.

    Call at every OCF write chokepoint:
    ``zf.writestr(zi, ocf_member_bytes(arcname, raw), compresslevel=9)``.
    """
    if name.lower().endswith(_OCF_TEXT_EXTENSIONS):
        return data.replace(b"\r\n", b"\n")
    return data


def reproducible_zipinfo(name: str, *, stored: bool = False) -> zipfile.ZipInfo:
    """A ``ZipInfo`` with pinned ``date_time`` + perms for byte-reproducible
    output. ``stored=True`` selects ZIP_STORED (e.g. an EPUB ``mimetype``);
    otherwise ZIP_DEFLATED.

    ``create_system`` is pinned to 0 (FAT) so the archive is byte-identical
    regardless of the BUILD host OS (round-13 #6): ``ZipInfo`` otherwise
    defaults ``create_system`` to 0 on Windows but 3 (UNIX) on macOS/Linux,
    which diverges the central directory cross-machine (and the SHA256SUMS).
    Windows-built bytes are unchanged; macOS/Linux converge onto them.
    """
    info = zipfile.ZipInfo(filename=name, date_time=ZIP_EPOCH)
    info.external_attr = 0o644 << 16
    info.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
    info.create_system = 0
    return info

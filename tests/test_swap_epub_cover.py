"""Matrix M1 — the deterministic catalog cover-swap (spec §4.2).

Every Downloads-catalog cell is the format's base build with the cell's
(edition × design × colour) composite swapped into the EPUB's cover slot.
A bare rezip guarantees neither zip discipline nor determinism, so the swap
rewrites the package with ``build_epub.py``'s writer rules: mimetype FIRST
and STORED, every other entry DEFLATE-9, all dates pinned to the 1980 zip
epoch, 0o644 attrs. Every non-cover byte must survive identically — the
swap touches no markup (that's what licenses the per-design epubcheck spot
sample instead of 225 full runs).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

# A minimal-but-real JPEG header (SOI + APP0/JFIF) so magic-byte checks pass.
JPEG_BYTES = bytes.fromhex("ffd8ffe000104a46494600010100000100010000") + b"fake-jpeg-payload" + bytes.fromhex("ffd9")
NEW_JPEG_BYTES = (
    bytes.fromhex("ffd8ffe000104a46494600010100000100010000") + b"NEW-cover-payload" + bytes.fromhex("ffd9")
)
PNG_BYTES = bytes.fromhex("89504e470d0a1a0a") + b"fake-png-payload"


def _make_mini_epub(path: Path, *, with_cover: bool = True) -> None:
    """A tiny EPUB-shaped zip with the discipline the swap must preserve."""
    with zipfile.ZipFile(path, "w") as zf:
        mz = zipfile.ZipInfo("mimetype")
        mz.date_time = (1980, 1, 1, 0, 0, 0)
        mz.compress_type = zipfile.ZIP_STORED
        zf.writestr(mz, b"application/epub+zip")
        entries = [
            ("META-INF/container.xml", b"<container/>"),
            ("content.opf", b'<package><item href="cover.jpeg" media-type="image/jpeg"/></package>'),
            ("chapter1.xhtml", b"<html>In the beginning</html>"),
        ]
        if with_cover:
            entries.insert(2, ("cover.jpeg", JPEG_BYTES))
        for name, data in entries:
            zi = zipfile.ZipInfo(name)
            zi.date_time = (1980, 1, 1, 0, 0, 0)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zi, data)


def _swap(tmp_path: Path, **kwargs):
    from scripts.swap_epub_cover import swap_cover

    src = tmp_path / "base.epub"
    _make_mini_epub(src, with_cover=kwargs.pop("with_cover", True))
    cover = tmp_path / "new_cover.jpg"
    cover.write_bytes(kwargs.pop("cover_bytes", NEW_JPEG_BYTES))
    out = tmp_path / "swapped.epub"
    return swap_cover(src, cover, out, **kwargs), src, out


class TestSwapCover:
    def test_replaces_cover_bytes_and_nothing_else(self, tmp_path):
        _, src, out = _swap(tmp_path)
        with zipfile.ZipFile(src) as zs, zipfile.ZipFile(out) as zo:
            assert zo.namelist() == zs.namelist()  # order preserved
            for name in zs.namelist():
                if name == "cover.jpeg":
                    assert zo.read(name) == NEW_JPEG_BYTES
                else:
                    assert zo.read(name) == zs.read(name), name

    def test_mimetype_stays_first_and_stored(self, tmp_path):
        _, _, out = _swap(tmp_path)
        with zipfile.ZipFile(out) as zo:
            infos = zo.infolist()
            assert infos[0].filename == "mimetype"
            assert infos[0].compress_type == zipfile.ZIP_STORED
            assert all(i.compress_type == zipfile.ZIP_DEFLATED for i in infos[1:])

    def test_all_dates_pinned_to_zip_epoch(self, tmp_path):
        _, _, out = _swap(tmp_path)
        with zipfile.ZipFile(out) as zo:
            assert all(i.date_time == (1980, 1, 1, 0, 0, 0) for i in zo.infolist())

    def test_swap_is_deterministic(self, tmp_path):
        from scripts.swap_epub_cover import swap_cover

        _, src, out1 = _swap(tmp_path)
        out2 = tmp_path / "swapped2.epub"
        swap_cover(src, tmp_path / "new_cover.jpg", out2)
        assert out1.read_bytes() == out2.read_bytes()

    def test_output_passes_zip_integrity(self, tmp_path):
        _, _, out = _swap(tmp_path)
        with zipfile.ZipFile(out) as zo:
            assert zo.testzip() is None

    def test_missing_cover_entry_raises(self, tmp_path):
        import pytest

        with pytest.raises(ValueError, match="cover"):
            _swap(tmp_path, with_cover=False)

    def test_non_jpeg_cover_rejected_by_magic_bytes(self, tmp_path):
        # The OPF cover slot is image/jpeg — PNG bytes in it are an epubcheck
        # failure (review blocker #2's exact trap). Detect from magic bytes,
        # never the filename.
        import pytest

        with pytest.raises(ValueError, match="JPEG"):
            _swap(tmp_path, cover_bytes=PNG_BYTES)

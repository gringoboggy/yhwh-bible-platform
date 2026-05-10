"""Shared test fixtures.

Phase ω.0.3 — hoisted from `TestEditionMeta._make_png`, `_multipart_body`,
and `TestCovers._make_png` (which were duplicated near-byte-identical).
The duplication grows worse every time a new endpoint accepts binary
uploads; centralizing means one fix applies everywhere.

Use as plain functions, not bound methods:

    from tests.fixtures import make_png, multipart_body
    png = make_png(1200, 1800)
    body, ctype = multipart_body(png, "cover.png")

Existing test classes can keep their `self._make_png` wrappers as
thin delegates if migration is gradual:

    def _make_png(self, w, h):
        return make_png(w, h)
"""

from __future__ import annotations
import struct
import zlib


def make_png(width: int, height: int) -> bytes:
    """Build minimal valid PNG bytes with the requested dimensions.

    Solid red 24-bit RGB image. Useful for testing image-upload
    endpoints (covers, future thumbnails, etc.) without bringing in
    Pillow or a real image fixture file.

    Args:
        width: image width in pixels
        height: image height in pixels

    Returns:
        Complete PNG file as bytes (signature + IHDR + IDAT + IEND).
    """
    if width <= 0 or height <= 0:
        raise ValueError(f"width and height must be positive: {width}x{height}")

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">II", width, height) + b"\x08\x02\x00\x00\x00"
    ihdr = struct.pack(">I", 13) + b"IHDR" + ihdr_data + struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data))
    # Solid red row data, deflated
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * width for _ in range(height))
    compressed = zlib.compress(raw)
    idat = (
        struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", zlib.crc32(b"IDAT" + compressed))
    )
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND"))
    return sig + ihdr + idat + iend


def multipart_body(
    file_bytes: bytes,
    filename: str,
    *,
    content_type: str = "image/png",
    field_name: str = "file",
    boundary: str = "----testboundary12345",
) -> tuple[bytes, str]:
    """Build a multipart/form-data request body matching browser uploads.

    Returns:
        (body_bytes, content_type_header) — pass content_type_header
        as the request's Content-Type so the boundary is correct.

    Args:
        file_bytes: the file payload (e.g. PNG bytes from make_png)
        filename: filename to declare in Content-Disposition
        content_type: MIME type for the file part (default image/png)
        field_name: form field name (default "file" — matches the
            covers upload endpoint's expectation)
        boundary: multipart boundary string (default a stable one
            for predictable test assertions)
    """
    ctype = f"multipart/form-data; boundary={boundary}"
    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"; '
            f'filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8")
        + file_bytes
        + (f"\r\n--{boundary}--\r\n").encode("utf-8")
    )
    return body, ctype

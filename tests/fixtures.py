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
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The single durable record of shipped phases. dev/SESSION_STATE.md and
# dev/IN_FLIGHT.md are rolling snapshots that get trimmed for bootstrap-
# bandwidth + OOM hygiene (Rule §11), and dated dev/PLAN_*.md ledgers get
# moved under dev/archive/ when superseded — so NONE of them are safe to
# pin a phase tag against. dev/CHANGELOG.md is the permanent chronology
# (Rule §12). Route every "did phase X ship and get recorded" assertion
# through assert_phase_recorded() so a future CHANGELOG move/rename is a
# one-line fix instead of one-per-pin.
DURABLE_PHASE_RECORD = REPO_ROOT / "dev" / "CHANGELOG.md"


def assert_phase_recorded(*phase_tags: str) -> None:
    """Assert every given phase tag appears in the durable phase record
    (dev/CHANGELOG.md).

    Single chokepoint for phase-ship pins. Do NOT assert phase tags
    against dev/SESSION_STATE.md or dev/IN_FLIGHT.md — they are rolling
    snapshots that are trimmed regularly, so such pins break the moment
    the snapshot rolls (this helper exists because ~58 pins broke exactly
    that way when SESSION_STATE/IN_FLIGHT were trimmed and PLAN_2026-05-09
    was archived on 2026-05-21). The `no_ephemeral_doc_pins` check in
    scripts/lint_rules.py enforces the rule going forward.
    """
    if not phase_tags:
        raise AssertionError("assert_phase_recorded() requires at least one phase tag")
    text = DURABLE_PHASE_RECORD.read_text(encoding="utf-8")
    missing = [t for t in phase_tags if t not in text]
    assert not missing, (
        f"phase tag(s) {missing} not recorded in the durable phase record "
        f"dev/{DURABLE_PHASE_RECORD.name} — every shipped phase must be "
        f"journaled there (Rule §12). Add a CHANGELOG entry."
    )


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
        ).encode()
        + file_bytes
        + (f"\r\n--{boundary}--\r\n").encode()
    )
    return body, ctype

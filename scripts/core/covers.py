"""scripts.core.covers — per-book cover model + image metadata reader
(Phase π.4-A).

This module is the data layer that surfaces cover information to the
publisher console (π.4-B will add the upload UI on top). Today's
responsibilities:

  1. Encode/decode ``book_covers`` in editions.yaml — the project's
     custom YAML parser doesn't handle nested mappings, so per-book
     paths live as a flat list of ``"<book_code>=<path>"`` strings on
     disk and decode to a dict in the API/UI layer. Mirrors the
     ``popup_languages_per_book`` pattern; see
     ``CLAUDE_PROJECT_RULES.md`` §7 (Code conventions) and the
     "Add a new per-book asset" mental model in §9.

  2. Read minimal image metadata from disk — width, height, file size,
     format — without taking on a Pillow / image-library dependency.
     Header-only parsers for PNG and JPEG cover the formats we accept;
     unknown / unreadable files report ``None`` for dimensions but
     still report file size so the UI can show "broken cover".

The on-disk layout consumers should follow:

  content/covers/<edition_id>/main.<ext>
  content/covers/<edition_id>/books/<book_code>.<ext>

…but this module does not enforce that — paths can point anywhere
under ``content/`` to keep the door open for shared covers across
editions later.
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

REPO = Path(__file__).resolve().parent.parent.parent
CONTENT = REPO / "content"


def _covers_dir() -> Path:
    """ω.5 paths-resolver entrypoint for content/covers/. Existing
    ``CONTENT`` constant is preserved for back-compat; new call
    sites should prefer this function so they pick up
    dev/installed/test-override resolution automatically."""
    from . import paths

    return paths.covers_dir()


def _content_root() -> Path:
    """Resolve content/ via the ω.5 paths resolver (mirrors press_kit)."""
    from . import paths

    return paths.content_root()


def resolve_cover_path(edition: dict) -> Path | None:
    """Resolve ``edition["cover_image"]`` to an absolute Path under content/.
    Returns None when the field is empty or the resolved file doesn't exist on
    disk. The ``cover_image`` path is stored relative to content/ (see the module
    docstring + π.4-A). Relocated from press_kit in Phase 4 (decommercialize)."""
    raw = str((edition or {}).get("cover_image", "")).strip()
    if not raw:
        return None
    abs_path = _content_root() / raw
    return abs_path if abs_path.is_file() else None


# ----------------------------------------------------------------------
# Cover-template library (§4.6) — the 25-design picker source of truth
# ----------------------------------------------------------------------
# Five Midjourney design families × five colours = 25 PNG stems living in
# content/covers/templates/<stem>.png. The /customize picker renders them as
# clickable thumbnails; generate_edition_covers composes the edition title onto
# the chosen one to (re)build the main cover. Declared here (PIL-free) so the
# api_save_edition_meta enum validator can import COVER_TEMPLATES without
# pulling in Pillow via generate_edition_covers.

COVER_TEMPLATE_FAMILIES: list[tuple[str, str]] = [
    ("01_ornate_leafy", "Ornate leafy"),
    ("02_classical_corner", "Classical corner"),
    ("03_beadline", "Beadline"),
    ("04_minimal_lines", "Minimal lines"),
    ("05_missal_central", "Missal central"),
]
COVER_TEMPLATE_COLORS: list[str] = ["black", "brown", "forest", "navy", "red"]
COVER_TEMPLATES: frozenset[str] = frozenset(
    f"{family}_{color}" for family, _label in COVER_TEMPLATE_FAMILIES for color in COVER_TEMPLATE_COLORS
)


def cover_template_catalog() -> list[dict]:
    """The 25 templates as ordered picker rows (family-major, colour order
    within each family). Each row: ``{stem, family, family_label, color,
    thumb}`` where ``thumb`` is the same-origin static path the picker uses as
    an ``<img src>`` (served by the sandboxed /content/covers/ route)."""
    rows: list[dict] = []
    for family, label in COVER_TEMPLATE_FAMILIES:
        for color in COVER_TEMPLATE_COLORS:
            stem = f"{family}_{color}"
            rows.append(
                {
                    "stem": stem,
                    "family": family,
                    "family_label": label,
                    "color": color,
                    "thumb": f"/content/covers/templates/{stem}.png",
                }
            )
    return rows


# ----------------------------------------------------------------------
# encode / decode for book_covers (list-of-strings on disk → dict in API)
# ----------------------------------------------------------------------


def decode_book_covers(raw) -> dict[str, str]:
    """Decode the on-disk format for ``book_covers``.

    On-disk format is a flat list of ``"<book_code>=<path>"`` strings.
    Same indirection pattern as ``popup_languages_per_book`` — it
    keeps editions.yaml parseable without expanding the project's
    constrained YAML parser. See CLAUDE_PROJECT_RULES.md §7.

    Empty value (``"gen="``) means "the publisher explicitly cleared
    the book cover" — distinct from absence-of-key (which means "no
    cover ever set"). Both surface as no displayable image, but
    keeping them distinct preserves audit history through saves.

    Accepts:
      - None / empty list / empty dict → {}
      - list[str]                       → decoded
      - dict (from JSON API payload)    → returned as-is

    Returns ``{book_code: path_str}``.
    """
    if raw is None or raw == [] or raw == {}:
        return {}
    if isinstance(raw, dict):
        return {str(k): str(v or "") for k, v in raw.items()}
    out: dict[str, str] = {}
    for entry in raw:
        if not isinstance(entry, str):
            continue
        if "=" not in entry:
            # Bare code without a value: skip, same defensive policy as
            # the popup-languages decoder.
            continue
        code, path = entry.split("=", 1)
        code = code.strip()
        if not code:
            continue
        out[code] = path.strip()
    return out


def encode_book_covers(per_book: dict[str, str]) -> list[str]:
    """Inverse of decode_book_covers.

    Output is sorted by canonical book order (per CLAUDE_PROJECT_RULES.md
    §6.1) so editions.yaml diffs stay clean and predictable.
    """
    if not per_book:
        return []
    # Late import to avoid circular dependency at module load time.
    from scripts.core import config as _cfg

    book_order = list(_cfg.books_by_code().keys())
    rank = {code: i for i, code in enumerate(book_order)}

    def _sort_key(item):
        code = item[0]
        return (rank.get(code, len(book_order) + 1), code)

    out: list[str] = []
    for code, path in sorted(per_book.items(), key=_sort_key):
        out.append(f"{code}={path or ''}")
    return out


# ----------------------------------------------------------------------
# Image metadata — header-only parsers (no Pillow dependency)
# ----------------------------------------------------------------------


def _read_png_dimensions(data: bytes) -> tuple[int, int] | None:
    """Return (width, height) for PNG bytes, or None if unparseable.

    PNG signature is 8 bytes; the IHDR chunk follows immediately and
    contains width + height as big-endian 32-bit ints. We only need
    the first 24 bytes of the file.
    """
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    if data[12:16] != b"IHDR":
        return None
    try:
        width = struct.unpack(">I", data[16:20])[0]
        height = struct.unpack(">I", data[20:24])[0]
        return (width, height)
    except struct.error:
        return None


def _read_jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    """Return (width, height) for JPEG bytes, or None if unparseable.

    JPEGs are a stream of marker segments; we walk them looking for
    a Start-Of-Frame marker (SOF0..SOF15 except SOF4/SOF8/SOF12 which
    are reserved). The SOF segment carries height + width as big-endian
    16-bit ints right after a 1-byte sample-precision field.
    """
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return None
    i = 2
    n = len(data)
    while i + 4 < n:
        # Marker prefix
        if data[i] != 0xFF:
            return None
        # Skip filler 0xFF bytes
        while i < n and data[i] == 0xFF:
            i += 1
        if i >= n:
            return None
        marker = data[i]
        i += 1
        # Standalone markers (no length / payload)
        if marker in (0xD8, 0xD9):  # SOI / EOI
            continue
        if 0xD0 <= marker <= 0xD7:  # RST0..RST7
            continue
        # All other markers carry a 2-byte big-endian length
        if i + 2 > n:
            return None
        seg_len = struct.unpack(">H", data[i : i + 2])[0]
        # SOF markers — encode dimensions
        if (0xC0 <= marker <= 0xCF) and marker not in (0xC4, 0xC8, 0xCC):
            # Layout: length(2) + precision(1) + height(2) + width(2)
            if i + 7 > n:
                return None
            try:
                height = struct.unpack(">H", data[i + 3 : i + 5])[0]
                width = struct.unpack(">H", data[i + 5 : i + 7])[0]
                return (width, height)
            except struct.error:
                return None
        i += seg_len
    return None


def _detect_format(data: bytes, suffix: str) -> str:
    """Best-effort image-format detection.

    Magic bytes win; falls back to the file extension if unknown.
    """
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:2] == b"\xff\xd8":
        return "jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return suffix.lstrip(".").lower() or "unknown"


def _read_webp_dimensions(data: bytes) -> tuple[int, int] | None:
    """Return (width, height) for WebP bytes, or None if unparseable.

    WebP files start ``RIFF<size>WEBP``; what follows is one of three
    chunks that carry dimensions:

      VP8   — lossy. After the chunk header (8 bytes) and a 3-byte
              frame tag, three bytes 0x9D 0x01 0x2A mark the start of
              the keyframe; the next two pairs of bytes carry width
              and height (lower 14 bits each, little-endian).

      VP8L  — lossless. After the 8-byte chunk header and a 1-byte
              signature (0x2F), 28 bits encode (width-1, height-1)
              packed little-endian as 14+14 bits.

      VP8X  — extended. After the chunk header + 4 bytes of flags,
              two 24-bit little-endian fields carry (width-1, height-1).
    """
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None

    chunk = data[12:16]

    if chunk == b"VP8X":
        # canvas width-1 at offset 24 (3 bytes LE), height-1 at 27
        if len(data) < 30:
            return None
        w = data[24] | (data[25] << 8) | (data[26] << 16)
        h = data[27] | (data[28] << 8) | (data[29] << 16)
        return (w + 1, h + 1)

    if chunk == b"VP8 ":
        # Find the 0x9D 0x01 0x2A start-code; the spec says it sits
        # at offset 23 (12 RIFF + 8 chunk header + 3 frame tag), but
        # we scan defensively in the next 16 bytes for robustness.
        for i in range(20, min(40, len(data) - 7)):
            if data[i : i + 3] == b"\x9d\x01\x2a":
                if i + 7 > len(data):
                    return None
                w = (data[i + 3] | (data[i + 4] << 8)) & 0x3FFF
                h = (data[i + 5] | (data[i + 6] << 8)) & 0x3FFF
                return (w, h)
        return None

    if chunk == b"VP8L":
        # Signature byte at offset 20 must be 0x2F; then 28 bits of
        # (width-1, height-1) little-endian.
        if len(data) < 25 or data[20] != 0x2F:
            return None
        b1, b2, b3, b4 = data[21], data[22], data[23], data[24]
        w = (b1 | ((b2 & 0x3F) << 8)) + 1
        h = ((b2 >> 6) | (b3 << 2) | ((b4 & 0x0F) << 10)) + 1
        return (w, h)

    return None


def read_image_meta(path_str: str) -> dict | None:
    """Inspect the file at ``path_str`` and return a small metadata
    dict, or ``None`` if the file does not exist.

    Returned shape:
        {
            "exists":   True,
            "size_kb":  int,
            "format":   "png" | "jpeg" | "webp" | "<unknown>",
            "width":    int | None,    # None if format unparseable
            "height":   int | None,
        }

    Returning ``None`` for missing files (rather than a partial dict)
    lets the API caller distinguish "no cover set" from "cover set
    but file missing" — important for the publisher's audit view.
    """
    if not path_str:
        return None
    p = Path(path_str)
    if not p.is_absolute():
        # Cover paths in editions.yaml are relative to content/ so that
        # they survive moves of the repo on disk.
        p = CONTENT / p
    if not p.is_file():
        return None
    try:
        st = p.stat()
    except OSError:
        return None
    # Read just enough to detect format + dimensions for the supported
    # types. JPEGs may need more than 64KB to find SOF, but covers are
    # rarely that large; cap at 256KB for safety on huge files.
    try:
        with p.open("rb") as fh:
            head = fh.read(256 * 1024)
    except OSError:
        return None

    suffix = p.suffix
    fmt = _detect_format(head, suffix)
    dims: tuple[int, int] | None = None
    if fmt == "png":
        dims = _read_png_dimensions(head)
    elif fmt == "jpeg":
        dims = _read_jpeg_dimensions(head)
    elif fmt == "webp":
        dims = _read_webp_dimensions(head)

    return {
        "exists": True,
        "size_kb": int(round(st.st_size / 1024)),
        "format": fmt,
        "width": dims[0] if dims else None,
        "height": dims[1] if dims else None,
    }


# ----------------------------------------------------------------------
# Public-API helpers used by api_covers in scripts/web.py
# ----------------------------------------------------------------------


def cover_record_for_edition(edition: dict, canon_books: list[str], books_idx: dict) -> dict:
    """Build the cover-status record for one edition.

    `canon_books` is a list of book codes IN CANONICAL ORDER (caller
    is responsible for that — see books_canonical from
    api_customize_data). `books_idx` is the mapping {code: book-dict}
    for resolving titles.

    Returned shape mirrors what the publisher console will render:
        {
            "edition_id":    "catholic-study",
            "main_cover": {
                "path": "...",  "meta": {...} | None,
            },
            "book_covers": [
                {"book_code": "gen", "title": "Genesis",
                 "path": "covers/.../gen.jpg",
                 "meta": {...} | None},
                …  // ONLY books in canon, in canonical order
            ],
        }
    """
    main_path = edition.get("cover_image", "")
    main_meta = read_image_meta(main_path) if main_path else None

    per_book = decode_book_covers(edition.get("book_covers"))

    book_rows = []
    edition_id = edition.get("id", "")
    for code in canon_books:
        raw_path = per_book.get(code, "")
        path = resolve_effective_book_cover_path(edition_id, code, raw_path)
        meta = read_image_meta(path) if path else None
        variants = book_cover_variant_catalog(code)
        selected_variant = "default"
        if raw_path and is_custom_book_cover_path(edition_id, code, raw_path):
            selected_variant = "custom"
        else:
            for v in variants:
                if raw_path and v["path"] == raw_path:
                    selected_variant = v["variant_id"]
                    break
                if not raw_path and v["variant_id"] == "default":
                    selected_variant = v["variant_id"]
                    break
        book_rows.append(
            {
                "book_code": code,
                "title": books_idx.get(code, {}).get("title", code),
                "path": path,
                "selected_path": raw_path,
                "selected_variant": selected_variant,
                "is_custom": bool(raw_path and is_custom_book_cover_path(edition_id, code, raw_path)),
                "variants": variants,
                "meta": meta,
            }
        )

    return {
        "edition_id": edition["id"],
        "main_cover": {"path": main_path, "meta": main_meta},
        "book_covers": book_rows,
    }


# ----------------------------------------------------------------------
# Shared per-book cover catalog (3 built-in variants + edition upload)
# ----------------------------------------------------------------------

BOOK_COVER_OUTPUT_WIDTH = 1024
BOOK_COVER_OUTPUT_HEIGHT = 1536
# Lean JPEG for EPUB title plates — 1024×1536 @ q82 ≈ 250 KB vs ~390 KB @ q92.
BOOK_COVER_JPEG_QUALITY = 82
BOOK_COVER_JPEG_PROGRESSIVE = True
BOOK_COVER_JPEG_SUBSAMPLING = 2  # 4:2:0 chroma subsampling

# Built-in default only; upload + none are edition-level choices (see README).
BOOK_COVER_VARIANT_DEFS: tuple[tuple[str, str, str], ...] = (
    ("default", "built-in", "covers/_book_defaults/{code}.jpg"),
)


def default_book_cover_path(book_code: str) -> str:
    """Factory path for variant A — used when no per-edition override is set."""
    return BOOK_COVER_VARIANT_DEFS[0][2].format(code=book_code)


def book_cover_variant_catalog(book_code: str) -> list[dict]:
    """The shared built-in default for one book (may be missing on disk)."""
    rows: list[dict] = []
    for variant_id, label, tpl in BOOK_COVER_VARIANT_DEFS:
        path = tpl.format(code=book_code)
        rows.append(
            {
                "variant_id": variant_id,
                "label": label,
                "path": path,
                "meta": read_image_meta(path),
            }
        )
    return rows


def edition_book_upload_path(edition_id: str, book_code: str) -> str:
    """Canonical storage path for a publisher-uploaded per-book cover."""
    return f"covers/{edition_id}/books/{book_code}.jpg"


def is_custom_book_cover_path(edition_id: str, book_code: str, path: str) -> bool:
    return (path or "").strip().replace("\\", "/") == edition_book_upload_path(edition_id, book_code)


def is_allowed_book_cover_selection(edition_id: str, book_code: str, path: str) -> bool:
    """True when ``path`` is a catalog variant for ``book_code`` or that edition's upload."""
    norm = (path or "").strip().replace("\\", "/")
    if not norm:
        return False
    catalog_paths = {row["path"] for row in book_cover_variant_catalog(book_code)}
    if norm in catalog_paths:
        return True
    return norm == edition_book_upload_path(edition_id, book_code)


def resolve_effective_book_cover_path(edition_id: str, book_code: str, selected: str) -> str:
    """Pick the path build/UI should use: explicit selection, else first catalog hit."""
    sel = (selected or "").strip()
    if sel and read_image_meta(sel):
        return sel
    if sel and is_custom_book_cover_path(edition_id, book_code, sel):
        return sel
    for row in book_cover_variant_catalog(book_code):
        if row.get("meta"):
            return row["path"]
    return default_book_cover_path(book_code)


# ----------------------------------------------------------------------
# Upload-time validation (Phase π.4-B)
# ----------------------------------------------------------------------

# Limits per dev/SCOPE_2026-05-07-addendum-covers.md.
UPLOAD_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
UPLOAD_MIN_WIDTH = 600
UPLOAD_MIN_HEIGHT = 900
UPLOAD_MAX_WIDTH = 4000
UPLOAD_MAX_HEIGHT = 6000
UPLOAD_TARGET_ASPECT = 2 / 3  # portrait, 2:3 book jacket
UPLOAD_ASPECT_TOLERANCE = 0.20  # ±20%
UPLOAD_ALLOWED_FORMATS = ("png", "jpeg", "webp")


def validate_upload_image(data: bytes) -> tuple[bool, str, dict | None]:
    """Validate raw upload bytes against the cover-image policy.

    Returns ``(ok, error_message, meta)``:
      - ok is True if the bytes pass every check
      - error_message is empty when ok, else a human-readable reason
      - meta is the inspected metadata dict when ok (format, width,
        height, size_kb), else None

    All checks short-circuit; the caller doesn't need to inspect meta
    on failure. The order matches the user's perceived priority:
    size first (cheapest) → format → dimensions → aspect ratio.
    """
    # Size — cheapest check, do it first
    n = len(data)
    if n == 0:
        return False, "uploaded file is empty", None
    if n > UPLOAD_MAX_BYTES:
        mb = n / (1024 * 1024)
        return False, (f"file too large: {mb:.1f} MB (max {UPLOAD_MAX_BYTES // (1024 * 1024)} MB)"), None

    # Format — detect from magic bytes (don't trust the filename)
    fmt = _detect_format(data, "")
    if fmt not in UPLOAD_ALLOWED_FORMATS:
        return False, (f"unsupported image format: {fmt!r} (accept: {', '.join(UPLOAD_ALLOWED_FORMATS)})"), None

    # Dimensions — required; if we can't determine them we can't
    # safely accept the upload.
    if fmt == "png":
        dims = _read_png_dimensions(data)
    elif fmt == "jpeg":
        dims = _read_jpeg_dimensions(data)
    elif fmt == "webp":
        dims = _read_webp_dimensions(data)
    else:
        dims = None
    if dims is None:
        return (
            False,
            (f"could not determine image dimensions; the file may be corrupted or use an unsupported {fmt} variant"),
            None,
        )
    width, height = dims

    if width < UPLOAD_MIN_WIDTH or height < UPLOAD_MIN_HEIGHT:
        return False, (f"image too small: {width}×{height} px (minimum {UPLOAD_MIN_WIDTH}×{UPLOAD_MIN_HEIGHT})"), None
    if width > UPLOAD_MAX_WIDTH or height > UPLOAD_MAX_HEIGHT:
        return False, (f"image too large: {width}×{height} px (maximum {UPLOAD_MAX_WIDTH}×{UPLOAD_MAX_HEIGHT})"), None

    # Aspect ratio is NOT enforced here — ``normalize_cover_image`` center-crops
    # to the EPUB-safe 2:3 output so publishers can upload landscape or square
    # art without breaking the build.

    return (
        True,
        "",
        {
            "format": fmt,
            "width": width,
            "height": height,
            "size_kb": int(round(n / 1024)),
        },
    )


def storage_path_for_main(edition_id: str, fmt: str) -> str:
    """Return the project-relative storage path for a main cover.

    Centralized so the upload endpoint and any future migration tool
    use the same naming. Path is relative to ``content/``.
    """
    ext = {"jpeg": "jpg", "png": "png", "webp": "webp"}.get(fmt, "jpg")
    return f"covers/{edition_id}/main.{ext}"


def storage_path_for_book(edition_id: str, book_code: str, fmt: str) -> str:
    """Uploads are always normalized to JPEG — see ``normalize_cover_image``."""
    _ = fmt  # normalized output is always JPEG
    return edition_book_upload_path(edition_id, book_code)


def save_book_cover_jpeg(img: "Image.Image", dest: Path) -> dict:
    """Write a 1024×1536 lean JPEG suitable for EPUB title-page plates."""
    from PIL import ImageOps

    target = (BOOK_COVER_OUTPUT_WIDTH, BOOK_COVER_OUTPUT_HEIGHT)
    if img.size != target:
        rgb = img.convert("RGB")
        fitted = ImageOps.fit(rgb, target, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    else:
        fitted = img.convert("RGB")
    dest.parent.mkdir(parents=True, exist_ok=True)
    fitted.save(
        dest,
        format="JPEG",
        quality=BOOK_COVER_JPEG_QUALITY,
        optimize=True,
        progressive=BOOK_COVER_JPEG_PROGRESSIVE,
        subsampling=BOOK_COVER_JPEG_SUBSAMPLING,
    )
    size = dest.stat().st_size
    return {
        "format": "jpeg",
        "width": target[0],
        "height": target[1],
        "size_kb": int(round(size / 1024)),
    }


def normalize_cover_image(data: bytes) -> tuple[bytes, dict]:
    """Center-crop + resize to the EPUB-safe book-cover plate (1024×1536 JPEG).

    Converts PNG/WebP uploads to baseline JPEG (no progressive) so title-page
    art is consistent across e-readers. Requires Pillow (declared in
    requirements-dev.txt; cover tooling already depends on it).
    """
    import io

    ok, err, _meta = validate_upload_image(data)
    if not ok:
        raise ValueError(err)

    try:
        from PIL import Image, ImageOps
    except ImportError as e:
        raise ValueError("cover normalization requires Pillow; install requirements-dev.txt") from e

    opened = Image.open(io.BytesIO(data))
    transposed = ImageOps.exif_transpose(opened)
    rgb = transposed.convert("RGB")
    target = (BOOK_COVER_OUTPUT_WIDTH, BOOK_COVER_OUTPUT_HEIGHT)
    fitted = ImageOps.fit(rgb, target, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

    buf = io.BytesIO()
    fitted.save(buf, format="JPEG", quality=92, optimize=True, progressive=False)
    out = buf.getvalue()
    return (
        out,
        {
            "format": "jpeg",
            "width": target[0],
            "height": target[1],
            "size_kb": int(round(len(out) / 1024)),
        },
    )

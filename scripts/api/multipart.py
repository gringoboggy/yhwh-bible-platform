"""ω.35-B.7 — multipart/form-data helpers, extracted from scripts/web.py.

Two pure helpers shared by every upload route:
- `_parse_multipart(body, boundary)` — RFC 7578 multipart parser
- `_extract_boundary(content_type_header)` — pulls the boundary token

These were originally inlined in `scripts/web.py` and lazy-imported from
both `scripts/api/covers.py` (cover uploads) and `scripts/api/sources.py`
(source-cache uploads). After ω.35-B.7 they live in their canonical home
here; web.py re-exports them so tests that monkeypatch
`scripts.web._parse_multipart` keep working unchanged.

Both functions are pure (no module-level state, no I/O), so this module
imports nothing from the project.
"""

from __future__ import annotations


def _parse_multipart(body: bytes, boundary: bytes) -> list[dict]:
    """Minimal multipart/form-data parser — focused on the cover-upload
    use case (one file part per request, no nested multipart).

    Returns a list of part dicts:
        {name, filename, content_type, data}

    We use this instead of cgi.FieldStorage because cgi is deprecated
    in 3.13 and a focused 30-line parser is easier to reason about than
    a stdlib module that's on its way out. The format itself is RFC
    7578: ``--boundary\\r\\n`` separates parts; each part has headers,
    an empty line, then bytes. ``--boundary--\\r\\n`` ends the body.
    """
    # ξ.16 SEC-002 — bound the search for the headers/body separator
    # to a fixed prefix per part. RFC 7578 doesn't cap per-part
    # header size, but realistic uploads have headers well under 1 KB.
    # 8 KB is generous; anything larger is almost certainly an attack
    # trying to grow the headers dict unboundedly.
    PART_HEADER_MAX_BYTES = 8 * 1024
    PART_HEADER_LINE_MAX = 1024
    delim = b"--" + boundary
    chunks = body.split(delim)
    # First chunk is the prelude (often empty); last is the closing
    # "--\r\n" marker plus optional trailer.
    parts = []
    for chunk in chunks[1:-1]:
        # Strip the CRLF that follows the boundary line
        if chunk.startswith(b"\r\n"):
            chunk = chunk[2:]
        # Strip the CRLF that precedes the next boundary
        if chunk.endswith(b"\r\n"):
            chunk = chunk[:-2]
        # ξ.16 SEC-002 — search for the header/body delimiter in only
        # the first PART_HEADER_MAX_BYTES of the chunk. Past that
        # point, headers are not legitimate.
        header_search_window = chunk[:PART_HEADER_MAX_BYTES]
        sep = header_search_window.find(b"\r\n\r\n")
        if sep < 0:
            # Either the part is malformed, or the headers exceed
            # PART_HEADER_MAX_BYTES — treat as malformed and skip.
            continue
        header_blob = chunk[:sep].decode("utf-8", errors="replace")
        data = chunk[sep + 4 :]
        headers = {}
        for line in header_blob.split("\r\n"):
            # ξ.16 SEC-002 — also cap individual header line length to
            # blunt single-line dict-growth attacks (e.g. one massive
            # Content-Disposition).
            if len(line) > PART_HEADER_LINE_MAX:
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        cd = headers.get("content-disposition", "")
        name = ""
        filename = ""
        for piece in cd.split(";"):
            piece = piece.strip()
            if piece.startswith("name="):
                name = piece[5:].strip().strip('"')
            elif piece.startswith("filename="):
                filename = piece[9:].strip().strip('"')
        parts.append(
            {
                "name": name,
                "filename": filename,
                "content_type": headers.get("content-type", ""),
                "data": data,
            }
        )
    return parts


def _extract_boundary(content_type_header: str) -> bytes | None:
    """Pull the ``boundary=...`` token out of a Content-Type header.

    ξ.16 SEC-007 — reject empty or oversized boundaries before the
    parser ever sees them. RFC 2046 §5.1.1 caps the boundary at 70
    chars; an empty boundary makes ``b"--"`` the delimiter and
    fragments the body at every ``--`` substring (e.g. inside any
    base64-encoded chunk), widening the parser's interpretation
    surface unpredictably. The caller treats ``None`` as a malformed
    multipart header and returns 400.
    """
    if not content_type_header:
        return None
    for piece in content_type_header.split(";"):
        piece = piece.strip()
        if piece.lower().startswith("boundary="):
            v = piece[9:].strip()
            # Strip surrounding quotes if present
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            # ξ.16 SEC-007 — empty / oversized rejected. Length cap
            # is RFC 2046's 70-char ceiling; non-ASCII or control
            # chars are also rejected (boundary must be 7-bit).
            if not v or len(v) > 70:
                return None
            if any(ord(c) < 0x20 or ord(c) > 0x7E for c in v):
                return None
            return v.encode("ascii", errors="replace")
    return None

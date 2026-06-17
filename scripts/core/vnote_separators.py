"""K-R4-1 vnote plain-text preview separators (shared bake + build paths)."""

from __future__ import annotations

import re

_VN_SEP_CAT = '<span class="vn-sep">\u2028¶ </span>'
_VN_SEP_BYLINE = '<span class="vn-sep">\u2028◦ </span>'

_VNOTE_SEP_TEXT_RE = re.compile(r'(<p class="vnote-text(?:\s[^"]*)?">)(?!<span class="vn-sep">)(?!¶)')
_VNOTE_SEP_LABEL_RE = re.compile(r'(<p class="vnote-source-label">)(?!<span class="vn-sep">)')


def add_vnote_preview_separators(html: str) -> str:
    """Insert hidden `.vn-sep` plain-text separators into vnote asides (K-R4-1)."""
    html = _VNOTE_SEP_TEXT_RE.sub(lambda m: m.group(1) + _VN_SEP_CAT, html)
    return _VNOTE_SEP_LABEL_RE.sub(lambda m: m.group(1) + _VN_SEP_BYLINE, html)

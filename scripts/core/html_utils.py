"""
html_utils.py — Shared HTML manipulation helpers.

Consolidated from 4+ duplicates across editorial scripts (Phase β.2 / C2).
"""

from __future__ import annotations

import re

__all__ = ["strip_tags", "word_count"]

_TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(s: str) -> str:
    """Remove all HTML/XML tags from a string. Preserves text content."""
    return _TAG_RE.sub("", s or "")


def word_count(s: str) -> int:
    """Count whitespace-delimited words in a string after stripping tags."""
    if not s:
        return 0
    return len(strip_tags(s).split())

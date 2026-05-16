"""τ.6.x.5 — HaCohen external Ge'ez PD-source ingest.

Fetches Ran HaCohen's clean Unicode-Ge'ez critical editions
(tau.ac.il/~hacohen), caches HTML locally, parses per-verse text,
and writes a standard translation module. The source's own verse
numbering is authoritative — the canonical floor is used for
VALIDATION only, never to renumber (see the design spec
docs/superpowers/specs/2026-05-16-geez-external-source-ingest-design.md).
"""

from __future__ import annotations

import html as _html
import re
from pathlib import Path

_P_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
_VERSENUM_RE = re.compile(
    r"^\s*<span[^>]*font-size:\s*70%[^>]*>\s*(\d+)\s*</span>",
    re.IGNORECASE,
)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _clean_fragment(fragment_html: str) -> str:
    """Strip the optional leading verse-number span, all tags, and
    unescape HTML entities to real Unicode Ge'ez; collapse whitespace."""
    no_num = _VERSENUM_RE.sub("", fragment_html, count=1)
    no_tags = _TAG_RE.sub("", no_num)
    text = _html.unescape(no_tags)
    return _WS_RE.sub(" ", text).strip()


def parse_hacohen_psalter(page_html: str, psalm_number: int) -> list[tuple[int, int, str]]:
    """Parse one HaCohen Ludolf Psalm page into (psalm, verse, text).

    A new verse begins at a <p> whose leading element is
    <span style='font-size:70%'>N</span>. Subsequent number-less <p>
    blocks are continuation cola of the current verse. Title /
    "Nr. Vers." toggle / "Cap." caption paragraphs are skipped, as
    is any paragraph before the first numbered verse (superscription
    — not a Rahlfs-numbered verse on this view).
    """
    verses: list[tuple[int, int, str]] = []
    cur_v: int | None = None
    parts: list[str] = []

    def flush() -> None:
        nonlocal parts
        if cur_v is not None and parts:
            joined = " ".join(p for p in parts if p).strip()
            if joined:
                verses.append((psalm_number, cur_v, joined))
        parts = []

    for m in _P_RE.finditer(page_html):
        inner = m.group(1)
        if "Nr. Vers" in inner or "<!--Cap." in inner:
            continue
        vm = _VERSENUM_RE.match(inner.lstrip())
        text = _clean_fragment(inner)
        if not text:
            continue
        if vm:
            flush()
            cur_v = int(vm.group(1))
            parts = [text]
        elif cur_v is not None:
            parts.append(text)
        # else: pre-verse-1 superscription — skip
    flush()
    return verses

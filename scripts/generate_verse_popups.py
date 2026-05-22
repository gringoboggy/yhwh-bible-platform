"""Regenerate verse-popup wrappers + vnote asides in the base HTML
(epub_working/). Base-preprocessing, re-runnable, idempotent. See
docs/superpowers/specs/2026-05-22-verse-popup-regeneration-design.md."""

from __future__ import annotations

import html as _html
import re

_EMPTY_TEXT = '<p class="vnote-text vnote-empty"><em>[no text in this edition; verse marker only]</em></p>'


def build_vnote_aside(
    *, code: str, ch: int, vs: int, title: str, english: str | None, hebrew: str | None, greek: str | None
) -> str:
    """Build one ``<aside class="vnote">`` matching the recovered-base contract.
    ``english`` is plain text (escaped here); ``hebrew``/``greek`` are trusted
    pre-formatted HTML fragments (from the resolver or harvested asides)."""
    vid = f"vnote-{code}-{ch}-{vs}"
    parts = [
        f'<aside class="vnote" id="{vid}" epub:type="footnote"><p><strong>{_html.escape(title)} {ch}:{vs}.</strong></p>'
    ]
    if english:
        parts.append(f'<p class="vnote-text">{_html.escape(english)}</p>')
    else:
        parts.append(_EMPTY_TEXT)
    if hebrew:
        parts.append('\n  <p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>')
        parts.append(f'\n  <p class="vnote-hebrew" dir="rtl" lang="he">{hebrew}</p>')
    if greek:
        parts.append('\n  <p class="vnote-source-label">Greek (Septuagint / Brenton)</p>')
        parts.append(f'\n  <p class="vnote-greek" lang="grc">{greek}</p>')
    parts.append(f'\n<p><a href="#v-{code}-{ch}-{vs}" class="vnote-back" title="Back">↩</a></p></aside>')
    return "".join(parts)


def wrap_verse_number(chunk: str, *, code: str, ch: int, vs: int, title: str) -> tuple[str, bool]:
    """Wrap the first bare ``<span class="vn">{vs}</span>`` in ``chunk`` with the
    verse-popup noteref anchor. Idempotent: if a wrapper for this verse already
    exists, return unchanged. ``chunk`` MUST be scoped to one verse region so the
    head verse-number span is the right one. Returns ``(new_chunk, changed)``."""
    if f'id="v-{code}-{ch}-{vs}"' in chunk:
        return chunk, False
    needle = f'<span class="vn">{vs}</span>'
    idx = chunk.find(needle)
    if idx == -1:
        return chunk, False
    wrapper = (
        f'<a id="v-{code}-{ch}-{vs}" epub:type="noteref" '
        f'title="{_html.escape(title)} {ch}:{vs}" href="#vnote-{code}-{ch}-{vs}">'
        f"{needle}</a>"
    )
    return chunk[:idx] + wrapper + chunk[idx + len(needle) :], True


_ASIDE_RE = re.compile(r'<aside class="vnote" id="(vnote-[^"]+)".*?</aside>', re.DOTALL)
_HE_RE = re.compile(r'<p class="vnote-hebrew"[^>]*>(.*?)</p>', re.DOTALL)
_GR_RE = re.compile(r'<p class="vnote-greek"[^>]*>(.*?)</p>', re.DOTALL)


def harvest_existing_langs(text: str) -> dict[str, dict[str, str | None]]:
    """Parse every existing ``vnote`` aside in ``text`` -> ``{vnote_id:
    {"hebrew": html|None, "greek": html|None}}``. Used so a uniform regen never
    drops original-language content the resolver can no longer reproduce."""
    out: dict[str, dict[str, str | None]] = {}
    for m in _ASIDE_RE.finditer(text):
        block = m.group(0)
        he = _HE_RE.search(block)
        gr = _GR_RE.search(block)
        out[m.group(1)] = {
            "hebrew": he.group(1) if he else None,
            "greek": gr.group(1) if gr else None,
        }
    return out


def chapter_region(text: str, *, bxx: str, ch: int) -> tuple[int, int] | None:
    """Byte range of chapter ``ch`` of book ``bxx`` in ``text`` — from its
    heading anchor to the next chapter heading (any chapter), the verse-refs
    section, or end of text. Returns None if the chapter heading is absent."""
    anchor = f'id="ch-{bxx}-c{ch}"'
    start = text.find(anchor)
    if start == -1:
        return None
    after = start + len(anchor)
    nxt = re.search(rf'id="ch-{re.escape(bxx)}-c\d+"', text[after:])
    sect = text.find('<section class="verse-refs-section"', after)
    end = len(text)
    if nxt:
        end = min(end, after + nxt.start())
    if sect != -1:
        end = min(end, sect)
    return start, end


_VN_RE = re.compile(r'<span class="vn">(\d+)</span>')


def verse_numbers_in_region(region: str) -> list[int]:
    """Verse numbers (in document order) inside one chapter region."""
    return [int(m.group(1)) for m in _VN_RE.finditer(region)]


_SECTION_OPEN = '<section class="verse-refs-section" epub:type="footnotes" hidden="">'


def ensure_verse_refs_section(text: str) -> tuple[str, int]:
    """Return ``(text, insertion_index)`` where ``insertion_index`` points at the
    section's closing ``</section>`` (asides are inserted just before it). Creates
    an empty section before ``</body>`` if none exists."""
    pos = text.find(_SECTION_OPEN)
    if pos != -1:
        close = text.find("</section>", pos)
        return text, close
    body = text.rfind("</body>")
    if body == -1:
        body = len(text)
    new_text = text[:body] + f"\n{_SECTION_OPEN}</section>\n" + text[body:]
    pos = new_text.find(_SECTION_OPEN)
    return new_text, new_text.find("</section>", pos)

"""Regenerate verse-popup wrappers + vnote asides in the base HTML
(epub_working/). Base-preprocessing, re-runnable, idempotent. See
docs/superpowers/specs/2026-05-22-verse-popup-regeneration-design.md."""

from __future__ import annotations

import html as _html

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

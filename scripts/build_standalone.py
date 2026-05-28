"""scripts.build_standalone — Phase C3.

The standalone-Bible render path. Generates the Ge'ez body XHTML from the
own-versification store (there is no verse→HTML renderer in the rest of the
project — the 9 KJV editions inject into the pre-baked epub_working/ tree),
assembles a fresh OPF over a copied epub_working/ skeleton, and reuses the
shared build_epub.build / patch_opf / matter_pages machinery.

Popups carry the KJV cross-reference + the manuscript apparatus. English
back-translation is the NEXT lane and is intentionally absent here (never
faked from KJV).
"""

from __future__ import annotations

import html as _html
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GEEZ_STORE = REPO / "content" / "translations" / "geez-tewahedo"

# Display titles for popup headers. Extend as the standalone book set grows.
_BOOK_TITLES = {
    "1ki": "1 Kings",
    "2ki": "2 Kings",
    "1sa": "1 Samuel",
    "2sa": "2 Samuel",
    "psa": "Psalms",
}


def _esc(s: str) -> str:
    return _html.escape(s, quote=True)


def _fmt_kjv_ref(ref: list) -> str:
    bk, ch, vs = ref
    return f"{_BOOK_TITLES.get(bk, bk)} {ch}:{vs}"


def _render_vnote(book: str, chapter: int, gv: int, app: dict) -> str:
    nid = f"vnote-{book}-{chapter}-{gv}"
    title = f"{_BOOK_TITLES.get(book, book)} {chapter}:{gv}"
    parts = [
        f'<aside class="vnote" id="{nid}" epub:type="footnote">',
        f"<p><strong>{_esc(title)}</strong></p>",
    ]
    kjv = app.get("kjv") or []
    if kjv:
        refs = "; ".join(_fmt_kjv_ref(r) for r in kjv)
        conf = app.get("confidence") or ""
        conf_html = f' <span class="xref-confidence">({_esc(conf)})</span>' if conf else ""
        parts.append(f'<p class="vnote-xref">KJV cross-reference: {_esc(refs)}{conf_html}</p>')
    variants = [a for a in (app.get("apparatus") or []) if a.get("class") in ("disagree", "insertion", "lacuna")]
    if variants:
        items = []
        for a in variants:
            base = _esc(a.get("base") or "—")
            other = _esc(a.get("other") or "—")
            cls = _esc(a.get("class") or "")
            items.append(
                f'<li><span class="app-base">{base}</span> / '
                f'<span class="app-other">{other}</span> '
                f'<span class="app-class">[{cls}]</span></li>'
            )
        parts.append('<p class="vnote-apparatus">Manuscript variants (base / other witness):</p>')
        parts.append('<ul class="apparatus-list">' + "".join(items) + "</ul>")
    parts.append("</aside>")
    return "\n".join(parts)


def render_chapter_body(book: str, chapter: int, verses: list[tuple[int, str]], appmap: dict) -> str:
    """``verses``: ``[(geez_v, geez_text), …]``; ``appmap``: ``{str(geez_v): {...}}``.
    Returns the chapter body fragment (verse-p paragraphs + the hidden footnotes section)."""
    body = [
        f'<a id="ch-{book}-c{chapter}" class="ch-anchor"></a>',
        f'<p class="ch-heading"><span class="section-heading"><span class="bold-num">{chapter}</span></span></p>',
    ]
    asides = []
    for gv, text in verses:
        vid = f"v-{book}-{chapter}-{gv}"
        nid = f"vnote-{book}-{chapter}-{gv}"
        title = f"{_BOOK_TITLES.get(book, book)} {chapter}:{gv}"
        body.append(
            f'<p class="verse-p"><a class="vn-link" id="{vid}" href="#{nid}" '
            f'epub:type="noteref" title="{_esc(title)}"><span class="vn">{gv}</span></a> '
            f"{_esc(text)}</p>"
        )
        asides.append(_render_vnote(book, chapter, gv, appmap.get(str(gv), {})))
    body.append('<section class="verse-refs-section" epub:type="footnotes" hidden="">')
    body.extend(asides)
    body.append("</section>")
    return "\n".join(body)

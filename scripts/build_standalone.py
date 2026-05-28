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


# Captured from epub_working/index_split_001.html <head> (C3b skeleton recon):
# single-quoted XML decl, NO doctype, body class="bible-body", stylesheet.css.
# Ge'ez body → xml:lang/lang="gez".
_XHTML_HEAD = (
    "<?xml version='1.0' encoding='utf-8'?>\n"
    '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" '
    'xml:lang="gez" lang="gez">\n'
    "<head>\n"
    "<title>{title}</title>\n"
    '<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>\n'
    '<link rel="stylesheet" type="text/css" href="stylesheet.css"/>\n'
    "</head>\n"
    '<body class="bible-body">\n'
)
_XHTML_TAIL = "\n</body>\n</html>\n"


def wrap_xhtml_doc(title: str, body_fragment: str) -> str:
    """Wrap a chapter body fragment into a complete, well-formed XHTML document
    matching the epub_working skeleton's format."""
    return _XHTML_HEAD.format(title=_esc(title)) + body_fragment + _XHTML_TAIL


def build_manifest_and_spine(items: list[tuple[str, str]]) -> tuple[str, str]:
    """``items``: ``[(item_id, href), …]`` for the generated chapter files (spine order).
    Returns ``(manifest_items_xml, spine_itemrefs_xml)`` to splice into the skeleton OPF."""
    manifest = "\n".join(f'<item id="{i}" href="{h}" media-type="application/xhtml+xml"/>' for i, h in items)
    spine = "\n".join(f'<itemref idref="{i}"/>' for i, _ in items)
    return manifest, spine


def patch_standalone_opf(opf_text: str, chapter_items: list[tuple[str, str]]) -> str:
    """Replace the scripture-body portion of the skeleton manifest+spine with the
    generated chapter files, RETAINING non-body resources (css/nav/ncx/cover/titlepage/
    introduction). Body items are the ``index_split_*.html`` files; their spine itemrefs
    reference the body item ids (e.g. ``id161``), so we collect those ids and drop their
    itemrefs by id. Stdlib regex only (mirrors build_edition.patch_opf)."""
    import re

    # 1. collect the body manifest item ids (href matches index_split_NNN.html), both attr orders
    body_ids = set(re.findall(r'<item\b[^>]*\bid="([^"]+)"[^>]*\bhref="index_split_\d+\.html"', opf_text))
    body_ids |= set(re.findall(r'<item\b[^>]*\bhref="index_split_\d+\.html"[^>]*\bid="([^"]+)"', opf_text))
    # 2. drop the body manifest items
    opf_text = re.sub(r'\s*<item\b[^>]*href="index_split_\d+\.html"[^>]*/>', "", opf_text)
    # 3. drop their spine itemrefs (by collected id — itemrefs don't contain the href)
    for bid in body_ids:
        opf_text = re.sub(r'\s*<itemref\b[^>]*idref="' + re.escape(bid) + r'"[^>]*/>', "", opf_text)
    # 4. inject the generated manifest items + spine itemrefs
    manifest_items, spine_items = build_manifest_and_spine(chapter_items)
    opf_text = opf_text.replace("</manifest>", manifest_items + "\n</manifest>", 1)
    opf_text = opf_text.replace("</spine>", spine_items + "\n</spine>", 1)
    return opf_text

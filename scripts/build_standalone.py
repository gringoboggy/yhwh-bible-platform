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


def _render_vnote(nid: str, title: str, app: dict) -> str:
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
    Returns the chapter body fragment (verse-p paragraphs + the hidden footnotes
    section). Repeated verse numbers within a chapter get unique anchor ids
    (``…-N``, ``…-N-2``, …) while keeping the displayed number faithful to the source."""
    body = [
        f'<a id="ch-{book}-c{chapter}" class="ch-anchor"></a>',
        f'<p class="ch-heading"><span class="section-heading"><span class="bold-num">{chapter}</span></span></p>',
    ]
    asides = []
    seen: dict[int, int] = {}
    for gv, text in verses:
        seen[gv] = seen.get(gv, 0) + 1
        suffix = "" if seen[gv] == 1 else f"-{seen[gv]}"
        vid = f"v-{book}-{chapter}-{gv}{suffix}"
        nid = f"vnote-{book}-{chapter}-{gv}{suffix}"
        title = f"{_BOOK_TITLES.get(book, book)} {chapter}:{gv}"
        body.append(
            f'<p class="verse-p"><a class="vn-link" id="{vid}" href="#{nid}" '
            f'epub:type="noteref" title="{_esc(title)}"><span class="vn">{gv}</span></a> '
            f"{_esc(text)}</p>"
        )
        asides.append(_render_vnote(nid, title, appmap.get(str(gv), {})))
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


import shutil
import tempfile
import time

EPUB_DIR = REPO / "epub_working"

# Proof-EPUB book set: own-versification content only (Phase C scope).
# Psalms is added by Task C4 (after its xref sidecar exists).
_STANDALONE_BOOKS = ["1ki", "1sa", "2sa", "psa"]


def _skeleton_ignore(_d: object, names: list[str]) -> list[str]:
    """Replicate build_one's copytree ignore exactly:
    exclude dot-dirs/dot-files (e.g. .backups/, .sonar/) and *.bak editor cruft."""
    return [n for n in names if n.startswith(".") or n.endswith(".bak")]


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


def chapter_verses_in_source_order(translation: str, book: str) -> dict[int, list[tuple[int, str]]]:
    """Group a book's verses by chapter, PRESERVING the store's source order within
    each chapter. Unlike ``translations.get_chapter`` (which sorts by verse number),
    this keeps non-adjacent duplicate verse numbers in their authored reading order:
    the HaCohen Ge'ez Psalter stores Ps 36 as four distinct verses mis-numbered
    24,25,24,25, and sorting would scramble them to 24,24,25,25. Faithfulness to the
    source over tidy numbering. (The irregular psa numbering itself is a pre-existing
    ingest artifact for a Phase-D data pass — the render only reflects the store.)"""
    from scripts.core import translations as tx

    by_ch: dict[int, list[tuple[int, str]]] = {}
    for c, v, t in tx._load_book(translation, book) or []:
        by_ch.setdefault(c, []).append((v, t))
    return by_ch


def build_standalone(edition_id: str, output_dir: Path, version: str) -> dict:
    """Render a standalone Ge'ez Bible EPUB from the own-versification store.
    Returns {"status":"ok","output_path":str,"books":int,"chapters":int} or
    {"status":"error","message":str}."""
    from scripts import build_edition as be
    from scripts import build_epub
    from scripts.core import config
    from scripts.core import translations as tx

    edition = config.editions_by_id().get(edition_id)
    if edition is None or not edition.get("standalone"):
        return {"status": "error", "message": f"not a standalone edition: {edition_id}"}

    books = [b for b in _STANDALONE_BOOKS if tx.has_book("geez-tewahedo", b)]
    if not books:
        return {"status": "error", "message": "no own-versification books found in geez-tewahedo"}

    tmp = Path(tempfile.mkdtemp(prefix="standalone_"))
    try:
        # 1. copy the epub_working skeleton (same ignore as build_one)
        shutil.copytree(EPUB_DIR, tmp, ignore=_skeleton_ignore, dirs_exist_ok=True)

        # 2. remove the original scripture body files (we supply our own)
        for f in tmp.glob("index_split_*.html"):
            f.unlink()

        # 3. generate the Ge'ez body files (one per chapter), in book/chapter order
        chapter_items: list[tuple[str, str]] = []  # (item_id, href) in spine order
        toc_entries: list[tuple[str, str]] = []  # (href, label)
        for book in books:
            by_ch = chapter_verses_in_source_order("geez-tewahedo", book)
            appmap_path = GEEZ_STORE / f"{book}_apparatus.json"
            appmap_all = json.loads(appmap_path.read_text(encoding="utf-8")) if appmap_path.is_file() else {}
            for ch in sorted(by_ch):
                verses = by_ch[ch]  # source order — NOT re-sorted by verse number (faithful)
                frag = render_chapter_body(book, ch, verses, appmap_all.get(str(ch), {}))
                title = f"{_BOOK_TITLES.get(book, book)} {ch}"
                href = f"geez_{book}_{ch}.xhtml"
                (tmp / href).write_text(wrap_xhtml_doc(title, frag), encoding="utf-8")
                chapter_items.append((f"geez_{book}_{ch}", href))
                toc_entries.append((href, title))

        # 4. patch the OPF — metadata (best-effort) + body manifest/spine swap
        opf_path = tmp / _find_opf(tmp)
        opf_text = opf_path.read_text(encoding="utf-8")
        try:
            opf_text = be.patch_opf(opf_text, edition, version)
        except Exception:  # noqa: BLE001 — metadata patch is best-effort for the proof
            pass
        opf_text = patch_standalone_opf(opf_text, chapter_items)
        opf_path.write_text(opf_text, encoding="utf-8")

        # 5. rewrite the EPUB3 nav + the legacy NCX to the standalone toc
        _rewrite_nav(tmp, toc_entries)
        _rewrite_ncx(tmp, toc_entries)

        # 6. cover: standalone-geez sets cover_image="" → keep the master (no-op)
        be.apply_edition_cover(edition, tmp)

        # 7. package
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_path = output_dir / f"Geez_Standalone_{edition_id}_{version}_{ts}.epub"
        build_epub.build(tmp, out_path, bump=True)
        return {
            "status": "ok",
            "output_path": str(out_path),
            "books": len(books),
            "chapters": len(chapter_items),
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _find_opf(root: Path) -> str:
    import re

    container = (root / "META-INF" / "container.xml").read_text(encoding="utf-8")
    m = re.search(r'full-path="([^"]+)"', container)
    if not m:
        raise ValueError("no rootfile full-path in container.xml")
    return m.group(1)


def _find_nav(root: Path) -> Path:
    import re

    opf_path = root / _find_opf(root)
    opf_text = opf_path.read_text(encoding="utf-8")
    m = re.search(r'<item\b[^>]*properties="[^"]*\bnav\b[^"]*"[^>]*href="([^"]+)"', opf_text)
    if not m:
        m = re.search(r'<item\b[^>]*href="([^"]+)"[^>]*properties="[^"]*\bnav\b[^"]*"', opf_text)
    if not m:
        raise ValueError("no nav item in OPF manifest")
    return opf_path.parent / m.group(1)


def _rewrite_nav(root: Path, toc_entries: list[tuple[str, str]]) -> None:
    import re

    nav_path = _find_nav(root)
    nav_text = nav_path.read_text(encoding="utf-8")
    lis = "\n".join(f'<li><a href="{h}">{_esc(label)}</a></li>' for h, label in toc_entries)
    nav_text = re.sub(r"<ol>.*?</ol>", "<ol>\n" + lis + "\n</ol>", nav_text, count=1, flags=re.DOTALL)
    nav_path.write_text(nav_text, encoding="utf-8")


def _rewrite_ncx(root: Path, toc_entries: list[tuple[str, str]]) -> None:
    import re

    ncx_path = root / "toc.ncx"
    if not ncx_path.is_file():
        return
    ncx_text = ncx_path.read_text(encoding="utf-8")
    points = [
        f'<navPoint id="np-{i}" playOrder="{i}">'
        f"<navLabel><text>{_esc(label)}</text></navLabel>"
        f'<content src="{h}"/></navPoint>'
        for i, (h, label) in enumerate(toc_entries, start=1)
    ]
    ncx_text = re.sub(
        r"<navMap>.*?</navMap>",
        "<navMap>\n" + "\n".join(points) + "\n</navMap>",
        ncx_text,
        count=1,
        flags=re.DOTALL,
    )
    ncx_path.write_text(ncx_text, encoding="utf-8")

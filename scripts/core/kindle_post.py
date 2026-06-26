"""Productize the proven Send-to-Kindle ("june10") recipe as a deterministic
post-process over a STANDARD (everywhere) build.

Why this exists
---------------
The ``--target-reader kindle`` build variant (the 2026-06-10 kindle_safe arc)
tuned the EPUB against the **Kindle Previewer** oracle: CSS-unhide +
``apply_kindle_toc_rows`` + source-label compaction + a 2-language popup cap +
``apply_kindle_unhide`` + a 2 MB file-split. Turn-83/84 (Mac, 2026-06-14) proved
on the REAL channel that that artifact (``FIXED.epub``) **FAILS Send-to-Kindle**,
while a *minimal* recipe — a plain everywhere build with only the hidden content
physically stripped and the language collapsed — **DELIVERS** (user-confirmed).
The Previewer-oracle extras were exactly what broke Send-to-Kindle.

The proven recipe (turn-84, user-confirmed via Send-to-Kindle, catholic-study,
24.1 MB / 299 spine / epubcheck 0/0/0/0)::

    build_edition.py <id>            # STANDARD everywhere build — full apparatus
    -> physically strip every display:none / visibility:hidden  (CSS + inline)
    -> LEAVE the .vn-sep separator spans intact (Mac turn-85 correction: the
       measured june10recipe.epub KEPT all 132,949 — with their hide rule stripped
       they render as the visible language separators inside the footnote popups;
       dropping them is a FIXED.epub/FAIL-column behavior, NOT the proven recipe)
    -> collapse <dc:language> to a single en-US
    -> LEAVE hidden="" attributes intact
    -> OCF re-zip (mimetype first + stored)

This module is the post-process; ``scripts/build_kindle.py`` is the driver
(standard build -> ``make_kindle_safe``). Operating on the *zipped* everywhere
artifact (rather than re-running the in-pipeline kindle passes) keeps the result
byte-faithful to the device-proven shape and leaves the 9 KJV editions, the
everywhere build, and the dormant kindle target completely untouched.

The hidden-strip half intentionally mirrors
``scripts.build_edition.apply_kindle_strip_hidden`` and detects exactly what
``dev/verify_kr2_build.py``'s gate-5 measures
(``display:none`` / ``visibility:hidden``), so a post-processed artifact carries
ZERO hidden content by that gate's own ruler.
"""

from __future__ import annotations

import html
import re
import zipfile
from pathlib import Path

from scripts.core.zip_repro import ocf_member_bytes  # round-14 A1: OS-independent OCF bytes

# Mirrors scripts.build_edition.apply_kindle_strip_hidden (same regexes) so the
# productized recipe strips precisely what the in-pipeline pass — and gate-5 —
# key on. Kept local (not imported from the heavy build module) so the
# post-process stays a small, dependency-light core utility.
_CSS_HIDDEN_DECL_RE = re.compile(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)\s*;?", re.I)
_INLINE_HIDDEN_DECL_RE = re.compile(r'(style="[^"]*?)(?:display\s*:\s*none|visibility\s*:\s*hidden)\s*;?', re.I)
_DC_LANG_RE = re.compile(r"<dc:language>[^<]*</dc:language>")
_CSS_RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.S)
_BODY_SELECTOR_RE = re.compile(r"\bbody\b", re.I)
_BODY_BACKGROUND_DECL_RE = re.compile(r"\bbackground(?:-color)?\s*:[^;]+;?\s*", re.I)


def _flatten_toc_pills(html: str) -> str:
    """Rewrite every <ol class="...toc-chapters..."> (the visual chapter "pills" ToC)
    to a <p class="toc-chapter-row"> containing the original <a> elements space-joined.
    This guarantees horizontal flow of the pills on Amazon Kindle/KFX renderers
    (which drop list-item display semantics, causing the raw <li display:inline-block>
    pills to stack vertically one per line). Anchor hrefs, text, and the pill
    appearance styles (on the <a>) are preserved exactly. Safe no-op if no such
    blocks. Idempotent. Added for the production kindle_post path after the old
    in-pipeline K-KIN-2 rewrite was retired with the dead --target-reader variant."""

    def _repl(m: re.Match) -> str:
        ol = m.group(0)
        links = re.findall(r"(<a\b[^>]*>.*?</a>)", ol, flags=re.S | re.I)
        if not links:
            return ol
        return f'<p class="toc-chapter-row">{" ".join(links)}</p>'

    pat = re.compile(
        r'<ol\b[^>]*class=["\'][^"\']*toc-chapters[^"\']*["\'][^>]*>.*?</ol>',
        re.S | re.I,
    )
    return pat.sub(_repl, html)


#: The single language a Send-to-Kindle artifact may declare (Amazon's E999
#: trigger is a multi-valued ``dc:language``).
KINDLE_LANGUAGE = "en-US"

_DOC_SUFFIXES = (".html", ".xhtml")

# Reproducible-zip epoch (M14). A bare ``writestr(name, bytes)`` stamps the
# build wall-clock time into every member, so two builds of identical input
# differ → SHA256SUMS break across the v1.0.0 re-cut. Pin it, like the sibling
# OCF packagers ``swap_epub_cover.py`` / ``build_epub.py``.
_ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def _ocf_rezip(dst_epub: Path, data: dict[str, bytes], order: list[str]) -> None:
    """Repackage an OCF/EPUB zip *reproducibly*: ``mimetype`` first + STORED,
    every other member DEFLATED (``compresslevel=9``), each member carrying a
    pinned ``date_time`` (``_ZIP_EPOCH``) + ``0o644`` external attr — so two
    runs over identical ``data`` produce byte-identical output. Mirrors
    ``swap_epub_cover.py``; the single re-zip chokepoint for the Kindle post-
    process (``make_kindle_safe`` + ``apply_kindle_m4b``)."""
    dst_epub.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dst_epub, "w", zipfile.ZIP_DEFLATED) as zout:
        mt = zipfile.ZipInfo("mimetype")
        mt.date_time = _ZIP_EPOCH
        mt.external_attr = 0o644 << 16
        mt.compress_type = zipfile.ZIP_STORED
        mt.create_system = 0  # round-13 #6: pin FAT so cross-OS re-zips match (Win default 0)
        zout.writestr(mt, data["mimetype"])
        for name in order:
            if name == "mimetype":
                continue
            zi = zipfile.ZipInfo(name)
            zi.date_time = _ZIP_EPOCH
            zi.external_attr = 0o644 << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.create_system = 0  # round-13 #6: pin FAT (see mimetype above)
            # round-14 A1: LF-normalize text members so the re-zip is OS-independent.
            zout.writestr(zi, ocf_member_bytes(name, data[name]), compresslevel=9)


def strip_body_backgrounds(css: str) -> tuple[str, int]:
    """Remove ``background`` / ``background-color`` from rules whose selector
    targets ``body``. Theme files (e.g. devotional) set a page tint that Kindle
    KFX renders as an unwanted content-area panel. Idempotent."""
    stripped = 0

    def _repl(m: re.Match) -> str:
        nonlocal stripped
        selector, decls = m.group(1), m.group(2)
        if not _BODY_SELECTOR_RE.search(selector):
            return m.group(0)
        new_decls, n = _BODY_BACKGROUND_DECL_RE.subn("", decls)
        if n:
            stripped += n
            return f"{selector}{{{new_decls}}}"
        return m.group(0)

    return _CSS_RULE_RE.sub(_repl, css), stripped


def strip_hidden_css(css: str) -> tuple[str, int]:
    """Remove every ``display:none`` / ``visibility:hidden`` declaration from a
    stylesheet (sibling declarations and the rule itself survive). Returns the
    new text and the count removed. Idempotent."""
    return _CSS_HIDDEN_DECL_RE.subn("", css)


def strip_hidden_html(html: str) -> tuple[str, int]:
    """Strip inline ``display:none`` / ``visibility:hidden`` from ``style="…"``
    attributes. ``hidden=""`` attributes AND ``.vn-sep`` separator spans are
    deliberately LEFT in place — the measured june10recipe.epub kept all 132,949
    vn-sep spans (with their hide rule stripped they are the visible language
    separators in the footnote popups). Returns ``(text, inline_hidden_stripped)``.
    Idempotent."""
    return _INLINE_HIDDEN_DECL_RE.subn(r"\1", html)


def collapse_dc_language(opf: str, lang: str = KINDLE_LANGUAGE) -> tuple[str, int]:
    """Collapse every ``<dc:language>`` element to a single ``<dc:language>{lang}``
    (keeping the first position, dropping the rest). Returns ``(text, count)``
    where ``count`` is how many ``dc:language`` elements were present. No-op when
    none exist."""
    count = len(_DC_LANG_RE.findall(opf))
    if count == 0:
        return opf, 0
    seen = 0

    def _sub(_m: re.Match) -> str:
        nonlocal seen
        seen += 1
        return f"<dc:language>{lang}</dc:language>" if seen == 1 else ""

    return _DC_LANG_RE.sub(_sub, opf), count


def make_kindle_safe(src_epub: Path | str, dst_epub: Path | str) -> dict:
    """Write the Send-to-Kindle-safe artifact at ``dst_epub`` from the standard
    (everywhere) EPUB at ``src_epub``, applying the proven june10 recipe.

    Reads every member into memory, transforms CSS / HTML / the OPF, then re-zips
    in OCF order with ``mimetype`` first and stored. Returns a stats dict."""
    src_epub, dst_epub = Path(src_epub), Path(dst_epub)
    stats = {
        "css_hidden_stripped": 0,
        "body_backgrounds_stripped": 0,
        "inline_hidden_stripped": 0,
        "dc_language_collapsed": 0,
    }

    with zipfile.ZipFile(src_epub) as zin:
        order = [i.filename for i in zin.infolist()]
        data: dict[str, bytes] = {name: zin.read(name) for name in order}

    if "mimetype" not in data:
        raise ValueError(f"{src_epub} is not an OCF EPUB (no mimetype member)")

    opf_name = next((n for n in order if n.endswith(".opf")), None)
    if opf_name is None:
        raise ValueError(f"{src_epub} has no .opf member")

    for name in order:
        if name.endswith(".css"):
            text = data[name].decode("utf-8")
            text, n_hidden = strip_hidden_css(text)
            text, n_bg = strip_body_backgrounds(text)
            if n_hidden or n_bg:
                data[name] = text.encode("utf-8")
                stats["css_hidden_stripped"] += n_hidden
                stats["body_backgrounds_stripped"] += n_bg
        elif name.endswith(_DOC_SUFFIXES):
            text = data[name].decode("utf-8")
            text, n_inline = strip_hidden_html(text)
            text = _flatten_toc_pills(text)
            data[name] = text.encode("utf-8")
            if n_inline:
                stats["inline_hidden_stripped"] += n_inline

    opf_text, lang_count = collapse_dc_language(data[opf_name].decode("utf-8"))
    if lang_count:
        data[opf_name] = opf_text.encode("utf-8")
        stats["dc_language_collapsed"] = lang_count

    _ocf_rezip(dst_epub, data, order)
    return stats


def verify_kindle_safe(epub_path: Path | str) -> list[str]:
    """Assert a built artifact conforms to the proven june10 recipe.

    Returns a list of human-readable failures (empty list = conformant). Checks:
    ``mimetype`` is the first member and stored; ZERO ``display:none`` /
    ``visibility:hidden`` survives in any ``.css`` or inline ``style="…"``;
    exactly one ``<dc:language>``. ``.vn-sep`` spans and ``hidden=""`` attrs are
    PRESERVED (june10 kept both), so they are not checked. This is the new path's
    own gate — it does NOT touch the dormant kindle target's gate-5."""
    epub_path = Path(epub_path)
    fails: list[str] = []
    with zipfile.ZipFile(epub_path) as z:
        infos = z.infolist()
        if not infos or infos[0].filename != "mimetype":
            fails.append("mimetype is not the first zip member (OCF violation)")
        elif infos[0].compress_type != zipfile.ZIP_STORED:
            fails.append("mimetype member is not stored (OCF violation)")
        for info in infos:
            name = info.filename
            if name.endswith(".css"):
                css_text = z.read(name).decode("utf-8", "replace")
                if _CSS_HIDDEN_DECL_RE.search(css_text):
                    fails.append(f"{name}: display:none/visibility:hidden survives in CSS")
                for m in _CSS_RULE_RE.finditer(css_text):
                    if _BODY_SELECTOR_RE.search(m.group(1)) and _BODY_BACKGROUND_DECL_RE.search(m.group(2)):
                        fails.append(f"{name}: body background survives in CSS")
                        break
            elif name.endswith(_DOC_SUFFIXES):
                text = z.read(name).decode("utf-8", "replace")
                if _INLINE_HIDDEN_DECL_RE.search(text):
                    fails.append(f"{name}: inline display:none/visibility:hidden survives")
            elif name.endswith(".opf"):
                n = z.read(name).decode("utf-8", "replace").count("<dc:language>")
                if n != 1:
                    fails.append(f"{name}: {n} dc:language values (want exactly 1)")
    return fails


# --- M4b: study glossary backmatter (Kobo K-R9 mirror) + badge navigate ---

_VN_LINK_RE = re.compile(r'<a\s+class="vn-link"', re.I)
_VERSE_NOTES_BADGE_RE = re.compile(
    r'<a\s+class="verse-notes-badge"[^>]*\bhref="#(vnotes-[^"]+)"[^>]*>.*?</a>',
    re.DOTALL | re.I,
)
_VNOTES_ASIDE_RE = re.compile(
    r'<aside\b(?=[^>]*\bid="(vnotes-[^"]+)")(?=[^>]*\bclass="[^"]*\bverse-notes\b)[^>]*>.*?</aside>',
    re.DOTALL | re.I,
)
_VNOTES_COORD_RE = re.compile(r"^vnotes-([a-z0-9]+)-(\d+)-(\d+)")
_VNOTE_ASIDE_RE = re.compile(
    r'<aside\b(?=[^>]*\bid="(vnote-[^"]+)")(?=[^>]*\bclass="[^"]*\bvnote\b)[^>]*>.*?</aside>',
    re.DOTALL | re.I,
)
_VNOTE_COORD_RE = re.compile(r"^vnote-([a-z0-9]+)-(\d+)-(\d+)")
_EMPTY_NOTES_SECTION_RE = re.compile(r'<aside class="notes-section"[^>]*>\s*</aside>\s*', re.DOTALL)
_EMPTY_VERSE_REFS_RE = re.compile(
    r'<section class="verse-refs-section"[^>]*>\s*</section>\s*',
    re.DOTALL,
)
_HIDDEN_ATTR_RE = re.compile(r'\s+hidden(?:="[^"]*")?')
_CH_BOUNDARY_RE = re.compile(r'<a\s+id="ch-b\d+-c(\d+)"\s+class="ch-anchor"></a>', re.I)
_KINDLE_STUDY_START = "<!-- yhwh:kindle-study-start -->"
_KINDLE_STUDY_END = "<!-- yhwh:kindle-study-end -->"
_VNOTE_BLOCK_START = "<!-- yhwh:kindle-vnote-start -->"
_VNOTE_BLOCK_END = "<!-- yhwh:kindle-vnote-end -->"
_KINDLE_STUDY_BLOCK_RE = re.compile(
    re.escape(_KINDLE_STUDY_START) + r".*?" + re.escape(_KINDLE_STUDY_END),
    re.DOTALL,
)
_VNOTE_BLOCK_RE = re.compile(
    re.escape(_VNOTE_BLOCK_START) + r".*?" + re.escape(_VNOTE_BLOCK_END),
    re.DOTALL,
)
_KINDLE_M4B_CSS_MARKER = "/* yhwh:kindle-m4b */"
_KINDLE_M4B_CSS = """
/* yhwh:kindle-m4b — KFX pagination + ToC spacing (device QA 2026-06-18) */
.book-title-page {
  page-break-after: auto;
  break-after: auto;
  padding: 0.6em 0.8em;
  margin: 0 0 0.6em 0;
}
.book-title-frame {
  page-break-inside: auto;
  break-inside: auto;
  padding: 0.8em 0.6em 0.6em 0.6em;
}
.toc-chapter-row a {
  display: inline-block;
  margin: 0 0.35em;
}
"""


KINDLE_STUDY_GLOSSARY_STEM = "kindle_study_glossary"
KINDLE_GLOSSARY_SPLIT_TARGET = 400_000
_SCRIPTURE_HTML_RE = re.compile(r"^index_split_\d+", re.I)
_GLOSSARY_HTML_RE = re.compile(rf"^{re.escape(KINDLE_STUDY_GLOSSARY_STEM)}(?:_\d+)?\.html$", re.I)
_BACKMATTER_SPINE_MARKERS = ("backsources", "backreftables", "backtopical", "backcolophon", "studynotes")


def _strip_kindle_study_blocks(html: str) -> str:
    """Remove retired Option-A ``kindle-chapter-study`` blocks (idempotent re-run)."""
    return _KINDLE_STUDY_BLOCK_RE.sub("", html)


def _strip_kindle_vnote_blocks(html: str) -> str:
    """Remove retired translation tail blocks (idempotent re-run)."""
    return _VNOTE_BLOCK_RE.sub("", html)


def _is_scripture_html(name: str) -> bool:
    base = Path(name).name
    return bool(_SCRIPTURE_HTML_RE.match(base))


def _is_glossary_html(name: str) -> bool:
    return bool(_GLOSSARY_HTML_RE.match(Path(name).name))


def _orphan_vnotes_in_prose(html: str) -> list[str]:
    prose = _strip_kindle_study_blocks(html)
    return sorted(set(re.findall(r'<aside\b[^>]*\bid="(vnotes-[^"]+)"', prose, re.I)))


def _inline_vnotes_in_prose(html: str) -> list[str]:
    """Translation ``vnote-*`` asides spliced directly after a verse paragraph.

    Hidden tail popups (the proven STK-deliverable shape) are not matched."""
    prose = _strip_kindle_vnote_blocks(_strip_kindle_study_blocks(html))
    pat = re.compile(
        r'<p[^>]*\bclass="[^"]*\bverse-p[^"]*"[^>]*>.*?</p>\s*'
        r'<aside\b[^>]*\bid="(vnote-[^"]+)"',
        re.DOTALL | re.I,
    )
    return sorted(set(m.group(1) for m in pat.finditer(prose)))


_VN_BACK_VBADGE_RE = re.compile(
    r'<p class="vn-back">.*?href="#vbadge-[^"]*".*?</p>\s*',
    re.DOTALL | re.I,
)
_VBADGE_HREF_RE = re.compile(r'href="#(vbadge-[^"]+)"', re.I)
_BADGE_HREF_RE = re.compile(
    r'(<a\s+class="verse-notes-badge"[^>]*\bhref=")#(vnotes-[^"]+)(")',
    re.I,
)
_VN_LINK_ID_ANY_RE = re.compile(r'\bid="(v-[^"]+)"', re.I)
_V_HREF_BARE_RE = re.compile(r'href="#(v-[a-z0-9]+-\d+-\d+[a-z]?)"', re.I)


def apply_kindle_m4b_css(css: str) -> str:
    """Append Kindle M4b pagination/ToC overrides. Idempotent."""
    if _KINDLE_M4B_CSS_MARKER in css:
        return css
    return css.rstrip() + "\n" + _KINDLE_M4B_CSS


def _retarget_glossary_xrefs(html: str, v_anchor_files: dict[str, str]) -> str:
    """Rewrite same-document ``#v-…`` xrefs to cross-file scripture anchors."""

    def _repl(m: re.Match) -> str:
        vid = m.group(1)
        spine = v_anchor_files.get(vid)
        if spine:
            return f'href="{spine}#{vid}"'
        return m.group(0)

    return _V_HREF_BARE_RE.sub(_repl, html)


def _glossary_back_link(book: str, ch: str, verse: str, v_anchor_files: dict[str, str]) -> str:
    v_id = f"v-{book}-{ch}-{verse}"
    spine_file = v_anchor_files.get(v_id)
    if spine_file:
        href = f"{spine_file}#{v_id}"
    else:
        return f'<p class="vn-back"><strong>{ch}:{verse}</strong></p>'
    return f'<p class="vn-back"><a href="{href}" class="note-back">↩</a> <strong>{ch}:{verse}</strong></p>'


def _prepare_glossary_aside(
    aside_html: str,
    aid: str,
    *,
    v_anchor_files: dict[str, str],
) -> str:
    """Unhide a relocated study aside and wire a cross-file scripture back-link."""
    aside_html = _HIDDEN_ATTR_RE.sub("", aside_html)
    aside_html = _VN_BACK_VBADGE_RE.sub("", aside_html)
    aside_html = _retarget_glossary_xrefs(aside_html, v_anchor_files)
    cm = _VNOTES_COORD_RE.match(aid)
    if not cm:
        return aside_html
    back = _glossary_back_link(cm.group(1), cm.group(2), cm.group(3), v_anchor_files)
    open_aside = re.match(r"(<aside\b[^>]*>)", aside_html, re.I)
    if open_aside:
        return aside_html[: open_aside.end()] + back + aside_html[open_aside.end() :]
    return back + aside_html


def _extract_m4b_asides(html: str) -> tuple[str, dict[str, str]]:
    """Extract study ``vnotes-*`` asides. Translation ``vnote-*`` popups stay put."""
    asides: dict[str, str] = {}

    def _take_vnotes(m: re.Match) -> str:
        asides[m.group(1)] = m.group(0)
        return ""

    html = _VNOTES_ASIDE_RE.sub(_take_vnotes, html)
    return html, asides


def _vnotes_sort_key(aid: str) -> tuple:
    cm = _VNOTES_COORD_RE.match(aid)
    if not cm:
        return (9999, 0, 0, aid)
    from scripts.core import config as _config

    book_order = list(_config.books_by_code().keys())
    rank = {code: i for i, code in enumerate(book_order)}
    code = cm.group(1)
    return (rank.get(code, len(book_order) + 1), int(cm.group(2)), int(cm.group(3)), aid)


def _render_kindle_study_glossary(entries: list[tuple[str, str]], title: str = "Study Notes") -> str:
    from scripts.core import config as _config

    books_by_code = _config.books_by_code()
    body_parts = [
        '<section class="study-notes-index" epub:type="backmatter">',
        "<h1>Study Notes</h1>",
        '<p class="study-notes-lead">Coloured badges after each verse open study notes '
        "by category. Tap a badge to jump here. Tap the ↩ link or verse tag to return "
        "to scripture. Tap a verse number at the start of a line for translation text.</p>",
    ]
    current_code: str | None = None
    for aid, aside_html in entries:
        cm = _VNOTES_COORD_RE.match(aid)
        code = cm.group(1) if cm else "misc"
        if code != current_code:
            current_code = code
            rec = books_by_code.get(code) or {}
            book_title = html.escape((rec.get("toc_title") or rec.get("title") or code.upper()))
            body_parts.append(f'<h2 class="study-book-head" id="study-{code}">{book_title}</h2>')
        entry_id = f"study-entry-{aid.removeprefix('vnotes-')}"
        body_parts.append(f'<div class="study-glossary-entry" id="{entry_id}">\n{aside_html}\n</div>')
    body_parts.append("</section>")
    body = "\n".join(body_parts)
    safe_title = html.escape(title)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>{safe_title}</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="backmatter">
{body}
</body>
</html>
"""


def _split_kindle_glossary(text: str) -> list[tuple[str, str]]:
    from scripts.build_edition import split_study_glossary_document

    return split_study_glossary_document(text, KINDLE_STUDY_GLOSSARY_STEM, KINDLE_GLOSSARY_SPLIT_TARGET)


def _glossary_target_hrefs(pieces: list[tuple[str, str]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for piece_name, piece_text in pieces:
        for aid in re.findall(r'<aside\b[^>]*\bid="(vnotes-[^"]+)"', piece_text, re.I):
            out[aid] = f"{piece_name}#{aid}"
    return out


def _retarget_study_badges(html: str, id_to_href: dict[str, str]) -> tuple[str, int]:
    retargeted = 0

    def _repl(m: re.Match) -> str:
        nonlocal retargeted
        aid = m.group(2)
        target = id_to_href.get(aid)
        if not target:
            return m.group(0)
        retargeted += 1
        return f"{m.group(1)}{target}{m.group(3)}"

    return _BADGE_HREF_RE.sub(_repl, html), retargeted


def _clean_scripture_html(html: str) -> tuple[str, dict[str, str]]:
    html = _strip_kindle_study_blocks(html)
    html = _strip_kindle_vnote_blocks(html)
    html, asides = _extract_m4b_asides(html)
    html = _EMPTY_NOTES_SECTION_RE.sub("", html)
    return html, asides


def _glossary_already_present(data: dict[str, bytes]) -> bool:
    return any(_is_glossary_html(name) for name in data)


def _apply_kindle_m4b_members(data: dict[str, bytes], order: list[str]) -> dict:
    if _glossary_already_present(data):
        return {"glossary_skipped": 1}

    collected: dict[str, str] = {}
    v_anchor_files: dict[str, str] = {}
    vn_links_before = 0
    badges_before = 0

    for name in order:
        if not name.endswith(_DOC_SUFFIXES) or not _is_scripture_html(name):
            continue
        text = data[name].decode("utf-8")
        vn_links_before += len(_VN_LINK_RE.findall(text))
        badges_before += len(_VERSE_NOTES_BADGE_RE.findall(text))
        spine = Path(name).name
        for v_id in _VN_LINK_ID_ANY_RE.findall(text):
            if v_id.startswith("v-"):
                v_anchor_files[v_id] = spine
        cleaned, asides = _clean_scripture_html(text)
        collected.update(asides)
        data[name] = cleaned.encode("utf-8")

    if not collected:
        return {"asides_relocated": 0, "badges_retargeted": 0, "glossary_pieces": 0, "vn_links": vn_links_before}

    entries = sorted(
        ((aid, _prepare_glossary_aside(collected[aid], aid, v_anchor_files=v_anchor_files)) for aid in collected),
        key=lambda row: _vnotes_sort_key(row[0]),
    )
    glossary_html = _render_kindle_study_glossary(entries)
    pieces = _split_kindle_glossary(glossary_html)
    id_to_href = _glossary_target_hrefs(pieces)

    badges_retargeted = 0
    for name in order:
        if not name.endswith(_DOC_SUFFIXES) or not _is_scripture_html(name):
            continue
        text = data[name].decode("utf-8")
        text, n = _retarget_study_badges(text, id_to_href)
        badges_retargeted += n
        data[name] = text.encode("utf-8")

    glossary_names = [piece_name for piece_name, _ in pieces]
    insert_at = len(order)
    for idx, name in enumerate(order):
        base = Path(name).name
        if base in {"sources.xhtml", "reftables.xhtml", "topical.xhtml", "colophonend.xhtml"}:
            insert_at = idx
            break

    for offset, (piece_name, piece_text) in enumerate(pieces):
        data[piece_name] = piece_text.encode("utf-8")
        order.insert(insert_at + offset, piece_name)

    opf_name = next((n for n in order if n.endswith(".opf")), None)
    if opf_name:
        opf = data[opf_name].decode("utf-8")
        manifest_add: list[str] = []
        spine_add: list[str] = []
        for k, piece_name in enumerate(glossary_names):
            item_id = f"kindle-studynotes-{k:02d}"
            if piece_name not in opf:
                manifest_add.append(
                    f'    <item id="{item_id}" href="{piece_name}" media-type="application/xhtml+xml"/>'
                )
                spine_add.append(f'    <itemref idref="{item_id}"/>')
        if manifest_add:
            opf = opf.replace("</manifest>", "\n" + "\n".join(manifest_add) + "\n  </manifest>")
        if spine_add:
            inserted = False
            for marker in _BACKMATTER_SPINE_MARKERS:
                needle = f'<itemref idref="{marker}"'
                if needle in opf:
                    opf = opf.replace(needle, "\n".join(spine_add) + "\n    " + needle, 1)
                    inserted = True
                    break
            if not inserted:
                opf = opf.replace("</spine>", "\n" + "\n".join(spine_add) + "\n  </spine>")
        data[opf_name] = opf.encode("utf-8")

    first_piece = glossary_names[0]
    nav_name = next((n for n in order if Path(n).name == "nav.xhtml"), None)
    if nav_name and first_piece not in data[nav_name].decode("utf-8"):
        nav = data[nav_name].decode("utf-8")
        study_li = f'      <li><a href="{first_piece}">Study Notes</a></li>\n'
        sources_m = re.search(r"<li>\s*<a\s+href=\"sources\.xhtml\"", nav, re.I)
        if sources_m:
            nav = nav[: sources_m.start()] + study_li + nav[sources_m.start() :]
        else:
            nav = nav.replace("</ol>", "\n" + study_li + "    </ol>", 1)
        data[nav_name] = nav.encode("utf-8")

    ncx_name = next((n for n in order if Path(n).name == "toc.ncx"), None)
    if ncx_name and first_piece not in data[ncx_name].decode("utf-8"):
        ncx = data[ncx_name].decode("utf-8")
        study_np = (
            f'\n    <navPoint id="num-kindle-studynotes" playOrder="0">'
            f"<navLabel><text>Study Notes</text></navLabel>"
            f'<content src="{first_piece}"/></navPoint>'
        )
        ncx = ncx.replace("</navMap>", study_np + "\n  </navMap>")
        counter = [0]

        def _renum(_m: re.Match) -> str:
            counter[0] += 1
            return f'playOrder="{counter[0]}"'

        data[ncx_name] = re.sub(r'playOrder="\d+"', _renum, ncx).encode("utf-8")

    return {
        "asides_relocated": len(collected),
        "badges_retargeted": badges_retargeted,
        "glossary_pieces": len(pieces),
        "vn_links": vn_links_before,
        "badges_kept": badges_before,
    }


def apply_kindle_m4b_html(html: str) -> tuple[str, dict]:
    """Single-document shim — real M4b runs at EPUB scope in ``apply_kindle_m4b``."""
    cleaned, asides = _clean_scripture_html(html)
    stats = {
        "asides_relocated": len(asides),
        "vn_links": len(_VN_LINK_RE.findall(html)),
        "badges_kept": len(_VERSE_NOTES_BADGE_RE.findall(html)),
    }
    return cleaned, stats


def apply_kindle_m4b(epub_path: Path | str) -> dict:
    """Option B: study glossary backmatter + badge navigate; scripture stays intact."""
    epub_path = Path(epub_path)
    with zipfile.ZipFile(epub_path) as zin:
        order = [i.filename for i in zin.infolist()]
        data: dict[str, bytes] = {name: zin.read(name) for name in order}

    stats = _apply_kindle_m4b_members(data, order)
    for name in order:
        if name.endswith(".css"):
            text = data[name].decode("utf-8")
            new_text = apply_kindle_m4b_css(text)
            if new_text != text:
                data[name] = new_text.encode("utf-8")

    _ocf_rezip(Path(epub_path), data, order)
    return stats


def verify_kindle_m4b_scripture_html(html: str) -> list[str]:
    """Structural M4b checks on scripture HTML. Empty list = pass."""
    fails: list[str] = []
    if "kindle-chapter-study" in html:
        fails.append("m4b-6: retired kindle-chapter-study block survives in scripture")
    for aid in _orphan_vnotes_in_prose(html):
        fails.append(f"m4b-2: vnotes aside {aid!r} still in scripture prose")
    for m in _BADGE_HREF_RE.finditer(html):
        target = m.group(2)
        if not target.startswith(f"{KINDLE_STUDY_GLOSSARY_STEM}"):
            fails.append(f"m4b-1: study badge still targets same-file #{target}")
    for vid in _inline_vnotes_in_prose(html):
        fails.append(f"m4b-5: translation vnote {vid!r} inlined in scripture prose")
    return fails


def verify_kindle_m4b_glossary_html(html: str) -> list[str]:
    """Glossary backmatter must not keep same-document scripture verse xrefs."""
    fails: list[str] = []
    for m in _V_HREF_BARE_RE.finditer(html):
        fails.append(f"m4b-4: bare scripture verse href #{m.group(1)} in glossary")
    return fails


def verify_kindle_m4b_html(html: str, *, filename: str = "") -> list[str]:
    """Dispatch per-document M4b checks (scripture vs glossary)."""
    if filename and _is_glossary_html(filename):
        return verify_kindle_m4b_glossary_html(html)
    if "study-notes-index" in html:
        return verify_kindle_m4b_glossary_html(html)
    return verify_kindle_m4b_scripture_html(html)


def verify_kindle_m4b(epub_path: Path | str) -> list[str]:
    """Assert M4b structural contract + kindle_safe conformance."""
    epub_path = Path(epub_path)
    fails = list(verify_kindle_safe(epub_path))
    has_glossary = False
    has_study_badges = False
    with zipfile.ZipFile(epub_path) as z:
        names = z.namelist()
        has_glossary = any(_is_glossary_html(n) for n in names)
        for name in names:
            if not name.endswith(_DOC_SUFFIXES):
                continue
            if _is_glossary_html(name):
                text = z.read(name).decode("utf-8", "replace")
                fails.extend(f"{name}: {msg}" for msg in verify_kindle_m4b_glossary_html(text))
                continue
            if _is_scripture_html(name):
                text = z.read(name).decode("utf-8", "replace")
                if "verse-notes-badge" in text:
                    has_study_badges = True
                fails.extend(f"{name}: {msg}" for msg in verify_kindle_m4b_scripture_html(text))
    if has_study_badges and not has_glossary:
        fails.append("m4b-3: study badges present but no kindle_study_glossary spine file")
    return fails


def make_kindle_m4b(src_epub: Path | str, dst_epub: Path | str) -> dict:
    """Proven june10 recipe + M4b study glossary backmatter. Returns merged stats."""
    src_epub, dst_epub = Path(src_epub), Path(dst_epub)
    safe_stats = make_kindle_safe(src_epub, dst_epub)
    m4b_stats = apply_kindle_m4b(dst_epub)
    return {**safe_stats, **m4b_stats}

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

import re
import zipfile
from collections import defaultdict
from pathlib import Path

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

    dst_epub.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dst_epub, "w", zipfile.ZIP_DEFLATED) as zout:
        # OCF: mimetype first, stored (uncompressed), no extra field.
        zout.writestr(zipfile.ZipInfo("mimetype"), data["mimetype"], compress_type=zipfile.ZIP_STORED)
        for name in order:
            if name == "mimetype":
                continue
            zout.writestr(name, data[name])
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


# --- M4b: suppress inline study badges; chapter-tail visible study blocks ---

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
_KINDLE_STUDY_BLOCK_RE = re.compile(
    re.escape(_KINDLE_STUDY_START) + r".*?" + re.escape(_KINDLE_STUDY_END),
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


def _strip_kindle_study_blocks(html: str) -> str:
    """Remove M4b study blocks (comment-delimited — safe with nested ``<section>``)."""
    return _KINDLE_STUDY_BLOCK_RE.sub("", html)


def _orphan_vnotes_in_prose(html: str) -> list[str]:
    prose = _strip_kindle_study_blocks(html)
    return sorted(set(re.findall(r'<aside\b[^>]*\bid="(vnotes-[^"]+)"', prose, re.I)))


_VN_BACK_RE = re.compile(r'<p class="vn-back">.*?</p>\s*', re.DOTALL | re.I)
_VN_BACK_VBADGE_RE = re.compile(
    r'<p class="vn-back">.*?href="#vbadge-[^"]*".*?</p>\s*',
    re.DOTALL | re.I,
)
_VBADGE_HREF_RE = re.compile(r'href="#(vbadge-[^"]+)"', re.I)


def apply_kindle_m4b_css(css: str) -> str:
    """Append Kindle M4b pagination/ToC overrides. Idempotent."""
    if _KINDLE_M4B_CSS_MARKER in css:
        return css
    return css.rstrip() + "\n" + _KINDLE_M4B_CSS


def _study_back_link(book: str, ch: str, verse: str) -> str:
    return (
        f'<p class="vn-back"><a href="#v-{book}-{ch}-{verse}" class="note-back">↩</a> <strong>{ch}:{verse}</strong></p>'
    )


def _prepare_relocated_aside(aside_html: str, aid: str) -> str:
    """Unhide study aside; replace suppressed ``vbadge`` back-link with ``#v-`` anchor."""
    aside_html = _HIDDEN_ATTR_RE.sub("", aside_html, count=1)
    aside_html = _VN_BACK_VBADGE_RE.sub("", aside_html)
    cm = _VNOTES_COORD_RE.match(aid)
    if not cm:
        return aside_html
    back = _study_back_link(cm.group(1), cm.group(2), cm.group(3))
    open_aside = re.match(r"(<aside\b[^>]*>)", aside_html, re.I)
    if open_aside:
        return aside_html[: open_aside.end()] + back + aside_html[open_aside.end() :]
    return back + aside_html


def _prepare_vnote_aside(aside_html: str) -> str:
    """Unhide a translation ``vnote`` aside for KFX-visible popup targets."""
    return _HIDDEN_ATTR_RE.sub("", aside_html)


def _orphan_vbadge_back_links(html: str) -> list[str]:
    orphans: list[str] = []
    for m in _VBADGE_HREF_RE.finditer(html):
        vb_id = m.group(1)
        if f'id="{vb_id}"' not in html and f"id='{vb_id}'" not in html:
            orphans.append(vb_id)
    return sorted(set(orphans))


def _strip_vn_back_in_study_blocks(html: str) -> tuple[str, int]:
    """Remove legacy ``vbadge`` back-links inside existing M4b study blocks (idempotent)."""
    stripped = 0

    def _repl(m: re.Match) -> str:
        nonlocal stripped
        block = m.group(0)
        cleaned = _VN_BACK_VBADGE_RE.sub("", block)
        if cleaned != block:
            stripped += len(_VN_BACK_VBADGE_RE.findall(block))
        return cleaned

    return _KINDLE_STUDY_BLOCK_RE.sub(_repl, html), stripped


def _chapter_injection_points(html: str) -> dict[int, int]:
    """Map chapter number → byte offset where that chapter's study block belongs."""
    boundaries = [(m.start(), int(m.group(1))) for m in _CH_BOUNDARY_RE.finditer(html)]
    if not boundaries:
        return {}
    points: dict[int, int] = {}
    body_end = html.rfind("</body>")
    if body_end == -1:
        body_end = len(html)
    for idx, (pos, ch_num) in enumerate(boundaries):
        if idx + 1 < len(boundaries):
            points[ch_num] = boundaries[idx + 1][0]
            continue
        region = html[pos:body_end]
        tail_candidates = [
            pos + region.find(needle)
            for needle in ('<aside class="notes-section"', '<section class="verse-refs-section"')
            if region.find(needle) != -1
        ]
        points[ch_num] = min(tail_candidates) if tail_candidates else body_end
    return points


def _build_study_block(book: str, ch: str, aids: list[str], asides: dict[str, str]) -> str:
    inner = "\n".join(_prepare_relocated_aside(asides[aid], aid) for aid in aids)
    return (
        f"{_KINDLE_STUDY_START}\n"
        f'<div class="kindle-chapter-study" epub:type="footnotes">\n'
        f"<h3>Study Notes — {book} {ch}</h3>\n{inner}\n</div>\n"
        f"{_KINDLE_STUDY_END}"
    )


def _inline_vnote_popups(html: str, vnotes: dict[str, str]) -> tuple[str, int]:
    """Hoist translation ``vnote-*`` asides out of hidden tail sections — inline after verse."""
    inlined = 0
    jobs: list[tuple[int, str]] = []
    for vid, aside in vnotes.items():
        cm = _VNOTE_COORD_RE.match(vid)
        if not cm:
            continue
        book, ch, verse = cm.group(1), cm.group(2), cm.group(3)
        v_id = f"v-{book}-{ch}-{verse}"
        link_pat = re.compile(
            rf'<a\s+class="vn-link"\s+id="{re.escape(v_id)}"\s+href="#{re.escape(vid)}"',
            re.I,
        )
        m = link_pat.search(html)
        if not m:
            continue
        para_end = html.find("</p>", m.end())
        if para_end == -1:
            continue
        jobs.append((para_end + len("</p>"), _prepare_vnote_aside(aside)))
    for insert_at, aside in sorted(jobs, key=lambda t: t[0], reverse=True):
        html = html[:insert_at] + "\n" + aside + html[insert_at:]
        inlined += 1
    return html, inlined


def _hidden_vnotes_in_tail(html: str) -> list[str]:
    """Translation vnotes still trapped inside a hidden ``verse-refs-section``."""
    m = re.search(r'<section class="verse-refs-section"[^>]*\bhidden[^>]*>(.*)</section>', html, re.DOTALL | re.I)
    if not m:
        return []
    return sorted(set(re.findall(r'id="(vnote-[^"]+)"', m.group(1), re.I)))


def _m4b_already_applied(html: str, badges: list[tuple[int, int]]) -> bool:
    return bool(
        not badges
        and _KINDLE_STUDY_START in html
        and not _orphan_vnotes_in_prose(html)
        and not _orphan_vbadge_back_links(html)
        and not _hidden_vnotes_in_tail(html)
    )


def _extract_m4b_asides(html: str) -> tuple[str, dict[str, str], dict[str, str]]:
    asides: dict[str, str] = {}
    vnotes: dict[str, str] = {}

    def _take_vnotes(m: re.Match) -> str:
        asides[m.group(1)] = m.group(0)
        return ""

    def _take_vnote(m: re.Match) -> str:
        vnotes[m.group(1)] = m.group(0)
        return ""

    html = _VNOTES_ASIDE_RE.sub(_take_vnotes, html)
    html = _VNOTE_ASIDE_RE.sub(_take_vnote, html)
    return html, asides, vnotes


def _group_vnotes_by_chapter(asides: dict[str, str]) -> dict[tuple[str, str], list[str]]:
    by_chapter: dict[tuple[str, str], list[str]] = defaultdict(list)
    for aid in asides:
        cm = _VNOTES_COORD_RE.match(aid)
        if cm:
            by_chapter[(cm.group(1), cm.group(2))].append(aid)
    return by_chapter


def _inject_study_blocks_at_tail(
    html: str,
    by_chapter: dict[tuple[str, str], list[str]],
    asides: dict[str, str],
) -> tuple[str, int]:
    """Fallback when a file piece has study asides but no matching ``ch-anchor``."""
    blocks: list[str] = []
    for book, ch in sorted(by_chapter):
        aids = sorted(by_chapter[(book, ch)])
        blocks.append(_build_study_block(book, ch, aids, asides))
    injection = "\n".join(blocks) + "\n"
    ns = html.find('<aside class="notes-section"')
    if ns != -1:
        html = html[:ns] + injection + html[ns:]
    else:
        bc = html.rfind("</body>")
        html = html[:bc] + injection + html[bc:] if bc != -1 else html + injection
    return html, len(blocks)


def _inject_study_blocks(
    html: str,
    by_chapter: dict[tuple[str, str], list[str]],
    asides: dict[str, str],
) -> tuple[str, int]:
    emitted = 0
    injection_points = _chapter_injection_points(html)
    if not injection_points:
        return _inject_study_blocks_at_tail(html, by_chapter, asides)

    pending: dict[tuple[str, str], list[str]] = dict(by_chapter)
    for book, ch in sorted(by_chapter, key=lambda k: int(k[1]), reverse=True):
        ch_num = int(ch)
        if ch_num not in injection_points:
            continue
        aids = sorted(by_chapter[(book, ch)])
        block = _build_study_block(book, ch, aids, asides) + "\n"
        pos = injection_points[ch_num]
        html = html[:pos] + block + html[pos:]
        emitted += 1
        del pending[(book, ch)]

    if pending:
        html, tail_emitted = _inject_study_blocks_at_tail(html, pending, asides)
        emitted += tail_emitted
    return html, emitted


def apply_kindle_m4b_html(html: str) -> tuple[str, dict]:
    """Remove inline ``verse-notes-badge`` markers; relocate ``vnotes-*`` asides into
    per-chapter ``kindle-chapter-study`` sections (visible, same file). Hoist
    translation ``vnote-*`` popups inline after their verse for KFX. Idempotent."""
    stats: dict = {
        "badges_removed": 0,
        "asides_relocated": 0,
        "chapters_emitted": 0,
        "vnotes_inlined": 0,
        "vn_links": len(_VN_LINK_RE.findall(html)),
    }

    badges = [(m.start(), m.end()) for m in _VERSE_NOTES_BADGE_RE.finditer(html)]
    if _m4b_already_applied(html, badges):
        html, back_stripped = _strip_vn_back_in_study_blocks(html)
        stats["vn_back_stripped"] = back_stripped
        return html, stats

    stats["badges_removed"] = len(badges)
    for start, end in reversed(badges):
        html = html[:start] + html[end:]

    html, asides, vnotes = _extract_m4b_asides(html)
    stats["asides_relocated"] = len(asides)

    if vnotes:
        html, n_inlined = _inline_vnote_popups(html, vnotes)
        stats["vnotes_inlined"] = n_inlined

    html = _EMPTY_VERSE_REFS_RE.sub("", html)

    if not asides:
        return html, stats

    by_chapter = _group_vnotes_by_chapter(asides)
    html, emitted = _inject_study_blocks(html, by_chapter, asides)
    stats["chapters_emitted"] = emitted

    html = _EMPTY_NOTES_SECTION_RE.sub("", html)
    html, back_stripped = _strip_vn_back_in_study_blocks(html)
    stats["vn_back_stripped"] = stats.get("vn_back_stripped", 0) + back_stripped
    return html, stats


def _transform_epub_members(data: dict[str, bytes], order: list[str], transform) -> dict:
    """Apply ``transform(html)->(html, partial_stats)`` to every HTML/XHTML member."""
    merged: dict = {}
    for name in order:
        if not name.endswith(_DOC_SUFFIXES):
            continue
        text = data[name].decode("utf-8")
        new_text, partial = transform(text)
        if new_text != text:
            data[name] = new_text.encode("utf-8")
        for k, v in partial.items():
            merged[k] = merged.get(k, 0) + v
    return merged


def apply_kindle_m4b(epub_path: Path | str) -> dict:
    """Apply the M4b HTML fork in-place on a kindle-safe (or everywhere) EPUB zip."""
    epub_path = Path(epub_path)
    with zipfile.ZipFile(epub_path) as zin:
        order = [i.filename for i in zin.infolist()]
        data: dict[str, bytes] = {name: zin.read(name) for name in order}

    stats = _transform_epub_members(data, order, apply_kindle_m4b_html)
    for name in order:
        if name.endswith(".css"):
            text = data[name].decode("utf-8")
            new_text = apply_kindle_m4b_css(text)
            if new_text != text:
                data[name] = new_text.encode("utf-8")

    with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED) as zout:
        zout.writestr(zipfile.ZipInfo("mimetype"), data["mimetype"], compress_type=zipfile.ZIP_STORED)
        for name in order:
            if name == "mimetype":
                continue
            zout.writestr(name, data[name])
    return stats


def verify_kindle_m4b_html(html: str) -> list[str]:
    """Structural M4b checks on one content document. Empty list = pass."""
    fails: list[str] = []
    if _VERSE_NOTES_BADGE_RE.search(html):
        fails.append("m4b-1: verse-notes-badge survives in document")
    for m in re.finditer(r'<p[^>]*\bclass="[^"]*\bverse-p[^"]*"[^>]*>.*?</p>', html, re.DOTALL | re.I):
        if 'href="#vnotes-' in m.group(0):
            fails.append("m4b-1: scripture paragraph still links to vnotes-*")
    for aid in _orphan_vnotes_in_prose(html):
        fails.append(f"m4b-2: vnotes aside {aid!r} not inside kindle-chapter-study")
    for m in _VBADGE_HREF_RE.finditer(html):
        vb_id = m.group(1)
        if f'id="{vb_id}"' not in html and f"id='{vb_id}'" not in html:
            fails.append(f"m4b-3: vbadge back-link {vb_id!r} has no fragment target")
    for vid in _hidden_vnotes_in_tail(html):
        fails.append(f"m4b-4: translation vnote {vid!r} still in hidden verse-refs-section")
    return fails


def verify_kindle_m4b(epub_path: Path | str) -> list[str]:
    """Assert M4b structural contract + kindle_safe conformance."""
    epub_path = Path(epub_path)
    fails = list(verify_kindle_safe(epub_path))
    with zipfile.ZipFile(epub_path) as z:
        for name in z.namelist():
            if name.endswith(_DOC_SUFFIXES):
                fails.extend(
                    f"{name}: {msg}" for msg in verify_kindle_m4b_html(z.read(name).decode("utf-8", "replace"))
                )
    return fails


def make_kindle_m4b(src_epub: Path | str, dst_epub: Path | str) -> dict:
    """Proven june10 recipe + M4b study relocation. Returns merged stats."""
    src_epub, dst_epub = Path(src_epub), Path(dst_epub)
    safe_stats = make_kindle_safe(src_epub, dst_epub)
    m4b_stats = apply_kindle_m4b(dst_epub)
    return {**safe_stats, **m4b_stats}

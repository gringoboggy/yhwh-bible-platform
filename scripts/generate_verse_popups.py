"""Regenerate verse-popup wrappers + vnote asides in the base HTML
(epub_working/). Base-preprocessing, re-runnable, idempotent. See
docs/superpowers/specs/2026-05-22-verse-popup-regeneration-design.md."""

from __future__ import annotations

import argparse
import html as _html
import re
from pathlib import Path

from scripts.core import config, notes_io
from scripts.core import translations as tx

REPO = Path(__file__).resolve().parents[1]
EPUB_DIR = REPO / "epub_working"

_EMPTY_TEXT = '<p class="vnote-text vnote-empty"><em>[no text in this edition; verse marker only]</em></p>'


def build_vnote_aside(*, code: str, ch: int, vs: int, title: str, versions: list[dict]) -> str:
    """Build one ``<aside class="vnote">`` from an ordered list of version dicts
    ``{label, lang, dir, has_label_para, content_class, text}`` (list order =
    render order; see scripts/core/popup_versions.py).

    Byte-compatible with the recovered-base contract: a leading
    ``has_label_para=False`` version (KJV) renders as a bare
    ``<p class="vnote-text">`` glued directly to the citation; labeled versions
    render an indented source-label + a ``dir``/``lang``-tagged content
    paragraph. ``text`` is plain scripture text (escaped here — a no-op for the
    plain unicode of Hebrew/Greek/etc., so it matches the old raw passing)."""
    vid = f"vnote-{code}-{ch}-{vs}"
    parts = [
        f'<aside class="vnote" id="{vid}" epub:type="footnote"><p><strong>{_html.escape(title)} {ch}:{vs}.</strong></p>'
    ]
    rendered = False
    for v in versions:
        text = v.get("text")
        if not text:
            continue
        # Original-language sources (WLC/LXX) carry per-word <em> markup → pass
        # raw; plain-text translations are escaped (matches the recovered base).
        body = text if v.get("trusted_html") else _html.escape(text)
        if v.get("has_label_para"):
            dir_attr = f' dir="{v["dir"]}"' if v.get("dir") == "rtl" else ""
            lang_attr = f' lang="{v["lang"]}"' if v.get("lang") else ""
            parts.append(f'\n  <p class="vnote-source-label">{_html.escape(v["label"])}</p>')
            parts.append(f'\n  <p class="{v["content_class"]}"{dir_attr}{lang_attr}>{body}</p>')
        else:
            parts.append(f'<p class="{v["content_class"]}">{body}</p>')
        rendered = True
    if not rendered:
        parts.append(_EMPTY_TEXT)
    parts.append(f'\n<p><a href="#v-{code}-{ch}-{vs}" class="vnote-back" title="Back">↩</a></p></aside>')
    return "".join(parts)


def assemble_versions_for_verse(code: str, ch: int, vs: int, *, harvested: dict) -> list[dict]:
    """Ordered version list for one verse: every registered version that has
    text — live via ``translations.get_verse`` at the version's normalized
    coordinate, or harvested from the prior aside — in registry render order.
    A version with no text is simply omitted (graceful per-verse availability)."""
    from scripts.core import popup_versions as pv

    vid = f"vnote-{code}-{ch}-{vs}"
    h = harvested.get(vid, {})
    out: list[dict] = []
    for version_id in sorted(pv.ALL_VERSION_IDS, key=lambda i: pv.VERSION_REGISTRY[i]["order"]):
        if not pv.bakes_now(version_id):
            continue  # full data not yet ingested; Phase 2 flips this on
        spec = pv.VERSION_REGISTRY[version_id]
        nb, nc, nv = pv.normalize_coord(version_id, code, ch, vs)
        text = tx.get_verse(spec["translation_id"], nb, nc, nv) or h.get(version_id)
        if not text:
            continue
        out.append(
            {
                "id": version_id,
                "label": spec["label"],
                "lang": spec["lang"],
                "dir": spec["dir"],
                "has_label_para": spec["has_label_para"],
                "content_class": spec["content_class"],
                "trusted_html": pv.is_trusted_html(version_id),
                "text": text,
            }
        )
    return out


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
        f'<a class="vn-link" id="v-{code}-{ch}-{vs}" href="#vnote-{code}-{ch}-{vs}" '
        f'epub:type="noteref" title="{_html.escape(title)} {ch}:{vs}">'
        f"{needle}</a>"
    )
    return chunk[:idx] + wrapper + chunk[idx + len(needle) :], True


_ASIDE_RE = re.compile(r'<aside class="vnote" id="(vnote-[^"]+)".*?</aside>', re.DOTALL)


def harvest_existing_langs(text: str) -> dict[str, dict[str, str | None]]:
    """Parse every existing ``vnote`` aside -> ``{vnote_id: {version_id: text|None}}``
    for every registered version's content class, so a uniform regen never drops
    content the resolver can no longer reproduce (e.g. an original ingested
    before its translation file existed)."""
    from scripts.core import popup_versions as pv

    class_to_id = {spec["content_class"]: vid for vid, spec in pv.VERSION_REGISTRY.items()}
    out: dict[str, dict[str, str | None]] = {}
    for m in _ASIDE_RE.finditer(text):
        block = m.group(0)
        entry: dict[str, str | None] = {}
        for cls, vid in class_to_id.items():
            cm = re.search(rf'<p class="{re.escape(cls)}"[^>]*>(.*?)</p>', block, re.DOTALL)
            entry[vid] = cm.group(1) if cm else None
        out[m.group(1)] = entry
    return out


_ANY_CHAPTER_RE = re.compile(r'id="ch-b\d+-c\d+"')


def chapter_region(text: str, *, bxx: str, ch: int) -> tuple[int, int] | None:
    """Byte range of chapter ``ch`` of book ``bxx`` in ``text`` — from its
    heading anchor to the next chapter heading (any book/chapter), the
    verse-refs section, or end of text. Returns None if the chapter heading
    is absent.

    Using ANY next chapter anchor (not just same-book) prevents the last
    chapter of a book from bleeding into the following book's content when
    multiple books share a file."""
    anchor = f'id="ch-{bxx}-c{ch}"'
    start = text.find(anchor)
    if start == -1:
        return None
    after = start + len(anchor)
    nxt = _ANY_CHAPTER_RE.search(text, after)
    sect = text.find('<section class="verse-refs-section"', after)
    end = len(text)
    if nxt:
        end = min(end, nxt.start())
    if sect != -1:
        end = min(end, sect)
    return start, end


_VN_RE = re.compile(r'<span class="vn">(\d+)</span>')


def verse_numbers_in_region(region: str) -> list[int]:
    """Verse numbers (in document order) inside one chapter region."""
    return [int(m.group(1)) for m in _VN_RE.finditer(region)]


_SECTION_OPEN = '<section class="verse-refs-section" epub:type="footnotes" hidden="">'


def _v_anchor_maps(epub_dir: Path) -> tuple[dict[str, str], dict[str, set[str]], dict[str, str]]:
    """Visible ``#v-`` anchor index for retargeting note-body links (round-7 5.2)."""
    from scripts.fix_xref_targets import build_chapter_index, build_v_anchor_index

    v_index, file_v_ids = build_v_anchor_index(epub_dir)
    chapter_fallback = build_chapter_index(epub_dir, config.load_books())
    return v_index, file_v_ids, chapter_fallback


def retarget_hidden_vnote_body_links(
    text: str,
    fname: str,
    *,
    v_index: dict[str, str],
    file_v_ids: dict[str, set[str]],
    chapter_fallback: dict[str, str],
) -> tuple[str, int]:
    """Retarget note-BODY ``<a href="…#vnote-">`` links to visible ``#v-`` anchors.

    vnote asides live inside the hidden ``verse-refs-section`` (and the file
    splitter's ``notes-section``) — body links must never target them (Kobo
    teleports to file start). vn-link noterefs are untouched."""
    from scripts.fix_xref_targets import retarget_visible

    new_text, n_retargeted, _unresolved = retarget_visible(
        text, file_v_ids.get(fname, set()), v_index, chapter_fallback
    )
    return new_text, n_retargeted


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


def _strip_chapter_asides(text: str, code: str, ch: int) -> str:
    """Remove existing ``vnote`` asides for (code, ch) so a regen replaces rather
    than duplicates them."""
    pat = re.compile(rf'<aside class="vnote" id="vnote-{re.escape(code)}-{ch}-\d+".*?</aside>\s*', re.DOTALL)
    return pat.sub("", text)


def _wrap_and_build_asides(
    text: str,
    region_html: str,
    region_start: int,
    region_end: int,
    *,
    code: str,
    ch: int,
    title: str,
    harvested: dict,
    stats: dict,
) -> str:
    """Wrap verse numbers in ``region_html`` and insert/refresh asides in ``text``.

    Returns the updated full ``text``.  ``region_start``/``region_end`` are
    the byte offsets of ``region_html`` inside ``text`` so we can splice the
    wrapped region back in; pass ``region_start=0, region_end=len(region_html)``
    for a preamble region that occupies the very beginning of the file.
    """
    # Wrap verse numbers in reverse order so earlier offsets stay valid.
    # dict.fromkeys deduplicates while preserving order (multi-edition files
    # repeat each <span class="vn"> N times per edition).
    for vs in sorted(dict.fromkeys(verse_numbers_in_region(region_html)), reverse=True):
        needle = f'<span class="vn">{vs}</span>'
        vpos = region_html.find(needle)
        if vpos == -1:
            continue
        # Idempotency: look 300 chars before the span for an existing anchor.
        lookback = region_html[max(0, vpos - 300) : vpos]
        if f'id="v-{code}-{ch}-{vs}"' in lookback:
            continue
        nxt = _VN_RE.search(region_html, vpos + len(needle))
        vchunk = region_html[vpos : (nxt.start() if nxt else len(region_html))]
        wrapped, changed = wrap_verse_number(vchunk, code=code, ch=ch, vs=vs, title=title)
        if changed:
            region_html = region_html[:vpos] + wrapped + region_html[vpos + len(vchunk) :]
            stats["verses_wrapped"] += 1

    # Splice updated region back into full text.
    text = text[:region_start] + region_html + text[region_end:]

    # Build/refresh asides for every unique verse in the region.
    new_asides = []
    for vs in dict.fromkeys(verse_numbers_in_region(region_html)):
        versions = assemble_versions_for_verse(code, ch, vs, harvested=harvested)
        new_asides.append(build_vnote_aside(code=code, ch=ch, vs=vs, title=title, versions=versions))
        stats["asides_built"] += 1

    if new_asides:
        text = _strip_chapter_asides(text, code, ch)
        text, insert_at = ensure_verse_refs_section(text)
        text = text[:insert_at] + "\n".join(new_asides) + "\n" + text[insert_at:]

    return text


def generate_book(code: str, *, dry_run: bool) -> dict:
    book = config.books_by_code().get(code)
    if book is None:
        return {"error": f"unknown book {code!r}"}
    title = book["title"]
    bxx = book.get("bxx")
    ch_count = int(book.get("ch_count", 0) or 0)
    files = book.get("files", [])
    stats = {"code": code, "verses_wrapped": 0, "asides_built": 0, "files_changed": [], "skipped_reason": None}

    if not tx.has_book("kjv", code):
        stats["skipped_reason"] = "no KJV source (Ethiopic-only — deferred)"
        return stats
    if not bxx or not files:
        stats["skipped_reason"] = "missing bxx/files metadata"
        return stats

    last_ch: int | None = None  # chapter last seen in the preceding file
    v_index, file_v_ids, chapter_fallback = _v_anchor_maps(EPUB_DIR)

    for fname in files:
        fpath = EPUB_DIR / fname
        if not fpath.is_file():
            continue
        text = fpath.read_text(encoding="utf-8")
        harvested = harvest_existing_langs(text)
        original = text

        # Handle cross-file chapter spillage: verse text for the last chapter
        # of the previous file may continue at the start of this file without
        # a repeating chapter anchor.  Process that preamble region as last_ch.
        first_ch_anchor = _ANY_CHAPTER_RE.search(text)
        preamble_end = first_ch_anchor.start() if first_ch_anchor else len(text)
        if last_ch is not None and preamble_end > 0:
            preamble = text[:preamble_end]
            if _VN_RE.search(preamble):
                text = _wrap_and_build_asides(
                    text,
                    preamble,
                    0,
                    preamble_end,
                    code=code,
                    ch=last_ch,
                    title=title,
                    harvested=harvested,
                    stats=stats,
                )
                # Recalculate preamble_end since _strip_chapter_asides may
                # have changed the text length.
                new_first = _ANY_CHAPTER_RE.search(text)
                preamble_end = new_first.start() if new_first else len(text)

        for ch in range(1, ch_count + 1):
            region = chapter_region(text, bxx=bxx, ch=ch)
            if region is None:
                continue
            last_ch = ch  # track for next file's preamble handling
            r_start, r_end = region
            region_html = text[r_start:r_end]
            text = _wrap_and_build_asides(
                text,
                region_html,
                r_start,
                r_end,
                code=code,
                ch=ch,
                title=title,
                harvested=harvested,
                stats=stats,
            )

        if "#vnote-" in text:
            from scripts.fix_xref_targets import V_ID_RE

            # Wrapping may have just minted vn-link anchors in this file.
            file_v_ids[fname] = {m.group(1) for m in V_ID_RE.finditer(text)}
            text, _n_rt = retarget_hidden_vnote_body_links(
                text,
                fname,
                v_index=v_index,
                file_v_ids=file_v_ids,
                chapter_fallback=chapter_fallback,
            )

        if text != original:
            stats["files_changed"].append(fname)
            if not dry_run:
                notes_io.ensure_backup(fpath)
                notes_io.atomic_write(fpath, text)
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description="Regenerate verse popups in epub_working/.")
    ap.add_argument("--books", nargs="*", help="book codes; default = all KJV-covered")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    codes = args.books or list(config.books_by_code())
    total_w = total_a = 0
    for code in codes:
        s = generate_book(code, dry_run=args.dry_run)
        if s.get("skipped_reason"):
            print(f"  skip {code}: {s['skipped_reason']}")
            continue
        total_w += s["verses_wrapped"]
        total_a += s["asides_built"]
        print(f"  {code}: wrapped {s['verses_wrapped']}, asides {s['asides_built']}, files {len(s['files_changed'])}")
    print(f"TOTAL wrapped {total_w}, asides {total_a}{' (dry-run)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
